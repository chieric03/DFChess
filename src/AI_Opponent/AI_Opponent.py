import pandas as pd
import numpy as np
import tensorflow as tf
import chess # Need python-chess for board validation and FEN handling
import os
import math # Keep math for potential future use or if needed by helpers

# Import validation functions needed for checking move legality
from src.validation import is_check, find_king 


# Constants
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'Models', 'chess_model.keras')
NUM_CLASSES = 4096 # 64 start squares * 64 end squares

# Loading trained model
if os.path.exists(MODEL_PATH):
    try:
        model = tf.keras.models.load_model(MODEL_PATH)
        print("Successfully loaded trained model from:", MODEL_PATH)
    except Exception as e:
        print(f"Error loading model from {MODEL_PATH}: {e}")
        model = None # Set model to None if loading fails
else:
    print(f"Error: Model file not found at {MODEL_PATH}")
    model = None

# Helper functions

def dataframe_to_fen(board_df: pd.DataFrame, turn: str = 'w') -> str:
    """
    Converts a DataFrame representation of a chess board to a FEN string.
    Assumes standard chess setup for castling, en passant for simplicity in FEN.
    """
    fen_rows = []
    for i in range(8):
        empty_count = 0
        fen_row = ""
        for j in range(8):
            cell = board_df.iat[i, j]
            if cell == ".":
                empty_count += 1
            else:
                if empty_count > 0:
                    fen_row += str(empty_count)
                    empty_count = 0
                # DataFrame stores 'wP', 'bN' etc. Need to convert to FEN's P, n etc.
                piece_char = cell[1]
                fen_row += piece_char.upper() if cell[0] == 'w' else piece_char.lower()
        if empty_count > 0:
            fen_row += str(empty_count)
        fen_rows.append(fen_row)


    fen_board = "/".join(fen_rows)
    return f"{fen_board} {turn} - - 0 1" #Placeholder for castling and en passant


def fen_to_onehot(fen: str) -> np.ndarray | None:
    """
    Converts a FEN string to a numpy array of shape (8,8,12) representing the board state.
    Returns None if the FEN is invalid.
    (Same as in the training notebook)
    """
    try:
        board = chess.Board(fen)
    except ValueError:
        return None
        
    onehot = np.zeros((8,8,12), dtype=np.uint8)
    mapping = {
        chess.PAWN: 0, chess.KNIGHT: 1, chess.BISHOP: 2,
        chess.ROOK: 3, chess.QUEEN: 4, chess.KING: 5
    }

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            rank = chess.square_rank(square)
            file = chess.square_file(square)
            channel = mapping[piece.piece_type] + (0 if piece.color == chess.WHITE else 6)
            onehot[rank, file, channel] = 1

    return onehot

def index_to_uci(index: int) -> str | None:
    """
    Converts a move index (0-4095) back to a UCI string (e.g., 'e2e4').
    Returns None if the index is out of bounds.
    """
    if not 0 <= index < NUM_CLASSES:
        return None
        
    end_square_idx = index % 64
    start_square_idx = index // 64
    
    start_rank = start_square_idx // 8
    start_file = start_square_idx % 8
    end_rank = end_square_idx // 8
    end_file = end_square_idx % 8
    
    # Convert file/rank indices (0-7) to UCI notation (a-h, 1-8)
    uci = f"{chr(ord('a') + start_file)}{start_rank + 1}{chr(ord('a') + end_file)}{end_rank + 1}"
    return uci

def uci_to_coords(uci: str) -> tuple | None:
    """ Converts a UCI string to ((start_row, start_col), (end_row, end_col)) format. """
    if not uci or len(uci) < 4:
        return None
    try:
        start_col = ord(uci[0]) - ord('a')
        start_row = 8 - int(uci[1]) # Convert chess rank to DataFrame row index
        end_col = ord(uci[2]) - ord('a')
        end_row = 8 - int(uci[3])   # Convert chess rank to DataFrame row index
        
        # Basic bounds check
        if not (0 <= start_row <= 7 and 0 <= start_col <= 7 and \
                0 <= end_row <= 7 and 0 <= end_col <= 7):
            return None
            
        return ((start_row, start_col), (end_row, end_col))
    except (ValueError, IndexError):
        return None

# --- AI Move Function ---

def get_ai_move(board_df: pd.DataFrame, turn: str) -> tuple | None:
    """
    Determines the best move for the AI using the loaded ML model.
    Validates the predicted move before returning.

    Parameters:
        board_df (pd.DataFrame): The current board state.
        turn (str): The current player's turn ('w' or 'b').

    Returns:
        tuple | None: The best legal move found as ((start_row, start_col), (end_row, end_col)),
                      or None if no legal move is found or model failed.
    """
    from src.validation import get_all_valid_moves_for_ai

    if model is None:
        print("AI Error: Model not loaded.")
        return None

    # Convert DataFrame to FEN
    fen = dataframe_to_fen(board_df, turn)
    if not fen:
        print("AI Error: Could not convert board to FEN.")
        return None

    # Convert FEN to one-hot encoding
    onehot_board = fen_to_onehot(fen)
    if onehot_board is None:
        print("AI Error: Could not convert FEN to one-hot.")
        return None
        
    # Add batch dimension for prediction
    input_tensor = np.expand_dims(onehot_board, axis=0)

    # Get move probabilities from the model
    try:
        predictions = model.predict(input_tensor)[0] # Get probabilities for the single input
    except Exception as e:
        print(f"AI Error: Model prediction failed: {e}")
        return None

    # 4Get all currently legal moves for the position
    try:
        legal_moves_coords = get_all_valid_moves_for_ai(board_df, turn) 
    except NameError:
         print("AI Error: Need 'get_all_valid_moves_for_ai' function in validation.py")
         # Fallback: Generate moves using python-chess
         try:
             board_chess = chess.Board(fen)
             legal_moves_coords = []
             for move in board_chess.legal_moves:
                 coords = uci_to_coords(move.uci())
                 if coords:
                     legal_moves_coords.append(coords)
         except Exception as e_chess:
             print(f"AI Error: Fallback move generation failed: {e_chess}")
             return None

    if not legal_moves_coords:
        print("AI Info: No legal moves available.")
        return None # Checkmate or stalemate likely

    # Find the best *legal* move predicted by the model
    # Get indices sorted by probability (highest first)
    sorted_indices = np.argsort(predictions)[::-1]

    for predicted_index in sorted_indices:
        uci_move = index_to_uci(predicted_index)
        if uci_move:
            predicted_coords = uci_to_coords(uci_move)
            if predicted_coords and predicted_coords in legal_moves_coords:
                print(f"AI Move Selected: {uci_move} (Coords: {predicted_coords}) with probability {predictions[predicted_index]:.4f}")
                return predicted_coords # Return the first valid move found

    # 6. Fallback (if no predicted move is legal)
    print("AI Warning: No predicted move was legal. Choosing first available legal move.")
    if legal_moves_coords:
         # Maybe choose randomly instead? For now, just take the first.
        return legal_moves_coords[0] 
    else:
        # This case should have been caught earlier
        return None



def simulate_move(board: pd.DataFrame, move: tuple) -> pd.DataFrame:
    """
    Returns a new board after simulating the move.
    (Identical to the previous version)
    """
    board_copy = board.copy(deep=True)
    (i, j), (r, c) = move
    piece = board_copy.iat[i, j]
    board_copy.iat[r, c] = piece
    board_copy.iat[i, j] = "."
    return board_copy

