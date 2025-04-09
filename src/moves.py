import src.logger as logger # Keep logger if used
import streamlit as st
import pandas as pd
from src.AI_Opponent.AI_Opponent import get_ai_move, simulate_move 
from src.validation import (
    is_valid_move_pawn, is_valid_move_rook, is_valid_move_bishop, 
    is_valid_move_knight, is_valid_move_queen, is_valid_move_king, 
    is_check, find_king, is_square_attacked, can_piece_attack_square
)
def parse_notation(coord: str) -> tuple:
    """
    Takes a user imput that is in chess notation and splits it into board coordinates
    """
    coord = coord.strip().upper()
    col_letter = coord[0]
    row_number = int(coord[1:])

    col_index = ord(col_letter) - ord("A")
    row_index = 8 - row_number
    return row_index, col_index

def coords_to_notation(coords: tuple) -> str | None:
    """ Converts ((start_row, start_col), (end_row, end_col)) to standard notation like 'a1h8'. """
    try:
        (start_row, start_col), (end_row, end_col) = coords
        
        # Basic bounds check
        if not (0 <= start_row <= 7 and 0 <= start_col <= 7 and \
                0 <= end_row <= 7 and 0 <= end_col <= 7):
            return None
            
        start_file_char = chr(ord('a') + start_col)
        start_rank_char = str(8 - start_row) # Convert DataFrame row index back to chess rank
        end_file_char = chr(ord('a') + end_col)
        end_rank_char = str(8 - end_row)   # Convert DataFrame row index back to chess rank
        
        return f"{start_file_char}{start_rank_char}{end_file_char}{end_rank_char}"
    except Exception: # Catch potential unpacking errors or other issues
        return None

def move_piece(board,start,end):
    """
    Moves a piece on the board
    """

    if isinstance(start,str):
        start = parse_notation(start)
    if isinstance(end,str):
        end = parse_notation(end)
    
    
    piece = board.iat[start[0], start[1]]
    color = piece[0]
    st.session_state.passant_target = None
    if piece == ".":
        st.session_state.last_error = "No piece at starting position!"
        return board, False
    
    current_turn = st.session_state.turn
    if piece[0] != current_turn:
        st.session_state.last_error = "It's not your turn!"
        return board, False


    piece_type = piece[1]
    valid_move = False
    
    # Get necessary state from session_state to pass to validation functions
    en_passant_target = st.session_state.get("en_passant_target", None)
    castling_rights = st.session_state.get("castling_rights", {}) 

    if piece[1] == "P":
        valid_move = is_valid_move_pawn(piece, start, end, board, en_passant_target)
        # Handle en passant capture side effect (removing captured pawn)
        if valid_move and abs(start[1] - end[1]) == 1 and board.iat[end[0], end[1]] == ".":
             # This indicates a valid en passant capture based on validation logic
             board.iat[start[0], end[1]] = "." # Remove the captured pawn
        # Set en passant target *after* validating the move
        direction = -1 if color == "w" else 1
        if abs(end[0] - start[0]) == 2 and valid_move: # Check if it was a valid two-square push
            st.session_state.en_passant_target = (start[0] + direction, start[1]) # Target square behind the pawn
        else:
             st.session_state.en_passant_target = None # Reset if not a two-square push
    elif piece_type == "R":
        valid_move = is_valid_move_rook(piece, start, end, board)
    elif piece_type == "B":
        valid_move = is_valid_move_bishop(piece, start, end, board)
    elif piece_type == "N":
        valid_move = is_valid_move_knight(piece, start, end, board)
    elif piece_type == "Q":
        valid_move = is_valid_move_queen(piece, start, end, board)
    elif piece_type == "K":
        valid_move = is_valid_move_king(piece, start, end, board, castling_rights)
        # Handle castling side effect (moving the rook)
        if valid_move and abs(start[1] - end[1]) == 2:
             # Kingside castling
             if end[1] > start[1]:
                 rook_start_col = 7
                 rook_end_col = 5
             # Queenside castling
             else:
                 rook_start_col = 0
                 rook_end_col = 3
             rook_piece = board.iat[start[0], rook_start_col]
             board.iat[start[0], rook_end_col] = rook_piece
             board.iat[start[0], rook_start_col] = "."
             # Update castling rights (king and relevant rook can no longer castle)
             st.session_state.castling_rights[f"{color}K"] = False
             rook_side = "kingside" if end[1] > start[1] else "queenside"
             st.session_state.castling_rights[f"{color}R_{rook_side}"] = False

    else:
        st.session_state.last_error = "Invalid piece type!" # More specific error
        return board, False
    
    if not valid_move:
        st.session_state.last_error = "Invalid move!"
        return board, False
    
    board_copy = board.copy(deep = True)
    board_copy.iat[end[0], end[1]] = piece
    board_copy.iat[start[0], start[1]] = "."
    if is_check(board_copy, current_turn):
        st.session_state.last_error = "Illegal Move! This leaves you in Check!"
        return board, False

    board.iat[end[0], end[1]] = piece
    board.iat[start[0], start[1]] = "."
    
    return board, True

def submit_move(start, end):
    """
    Attempts to submit a move
    Updates the board, turn, and move history

    Parameters:
        start (str): The starting position of the piece
        end (str): The ending position of the piece
    """
    piece_parse = parse_notation(start)
    piece = st.session_state.board.iat[piece_parse[0], piece_parse[1]]

    #If game is over, do nothing
    if st.session_state.game_status != "ongoing":
        st.session_state.last_error= "Game is over! Please restart"
        return
    
    #Attempt to move the piece
    updated_board, valid = move_piece(st.session_state.board, start, end)
    if not valid:
        return
    
    #Simulate and update gamestate
    st.session_state.board = updated_board
    # Record move with original notation
    st.session_state.move_history.append((start, end, piece)) 
    st.session_state.board_history.append(updated_board.copy(deep=True))

    # Call the consolidated post-move handler
    _handle_post_move_updates()


def _handle_post_move_updates():
    """
    Handles updates after a valid move is made: promotion check, turn change,
    AI move trigger (if applicable), and game status checks (check, mate, stalemate).
    """
    # Check for promotion
    promotion_triggered = False
    if st.session_state.turn == 'w':
        for col in range(8):
            cell = st.session_state.board.iat[0, col]
            if cell != "." and cell[1] == "P":
                st.session_state.promotion_pending = True
                st.session_state.promotion_pos = (0, col)
                promotion_triggered = True
                break
    else:
        for col in range(8):
            cell = st.session_state.board.iat[7, col]
            if cell != "." and cell[1] == "P":
                st.session_state.promotion_pending = True
                st.session_state.promotion_pos = (7, col)
                promotion_triggered = True
                break
            
    if promotion_triggered:
        st.session_state.last_error = "Pawn promotion pending!"
        st.rerun()
        return
    
    #Change turn
    new_turn = "b" if st.session_state.turn == "w" else "w"
    st.session_state.turn = new_turn # Update turn immediately after player move

    # Check game status before AI move
    if is_check(st.session_state.board, new_turn):
        st.session_state.last_error = f"Check! {'White' if new_turn == 'w' else 'Black'} is in check!" # Corrected color logic
        if is_checkmate(st.session_state.board, new_turn):
            st.session_state.last_error= f"Checkmate! {'White' if st.session_state.turn == 'b' else 'Black'} wins!" # Corrected winner logic
            st.session_state.game_status = "game_over"
            st.rerun()
            return
    elif is_stalemate(st.session_state.board, new_turn):
        st.session_state.last_error= "Stalemate! It's a draw!"
        st.session_state.game_status = "game_over"
        st.rerun()
        return
    else:
        st.session_state.last_error = "" # Clear previous error if no check/mate/stalemate

    # AI Move Logic (if applicable)
    if st.session_state.game_mode == "PvAI":
        human_side = st.session_state.player_side[0].lower()  # e.g. "w" or "b"
        # It's AI's turn if the current turn is not the human side
        if st.session_state.turn != human_side:
            st.write("AI is thinking...") # Indicate AI is processing
            # Call get_ai_move without the depth argument (ML model doesn't use it)
            ai_move = get_ai_move(st.session_state.board, st.session_state.turn) 
            st.write(f"AI Move: {ai_move}")  # Debug output
            if ai_move:
                start_coord, end_coord = ai_move
                
                # Get piece *before* simulating the move
                piece_moved_by_ai = st.session_state.board.iat[start_coord[0], start_coord[1]]
                
                # Simulate the move on the board
                st.session_state.board = simulate_move(st.session_state.board, ai_move)
                
                # Convert AI move coordinates to notation for history
                ai_move_notation = coords_to_notation(ai_move)
                
                # Record history in the consistent (start_notation, end_notation, piece) format
                if ai_move_notation:
                    st.session_state.move_history.append((ai_move_notation[:2], ai_move_notation[2:], piece_moved_by_ai))
                else:
                    # Fallback: store raw coordinates if conversion fails
                    st.session_state.move_history.append((str(start_coord), str(end_coord), piece_moved_by_ai)) # Still record the piece
                    
                st.session_state.board_history.append(st.session_state.board.copy(deep=True))
                
                # Check for check/mate/stalemate *after* AI move
                if is_check(st.session_state.board, human_side):
                     st.session_state.last_error = f"Check! {'White' if human_side == 'w' else 'Black'} is in check!"
                     if is_checkmate(st.session_state.board, human_side):
                         st.session_state.last_error= f"Checkmate! {'White' if st.session_state.turn == 'w' else 'Black'} wins!" # AI wins
                         st.session_state.game_status = "game_over"
                elif is_stalemate(st.session_state.board, human_side): # Check if AI caused stalemate
                    st.session_state.last_error= "Stalemate! It's a draw!"
                    st.session_state.game_status = "game_over"
                else:
                    st.session_state.last_error = "" # Clear previous error if AI move didn't result in check/mate

                st.session_state.turn = human_side 
            else:
                # This case should ideally not happen if checkmate/stalemate is handled correctly
                st.write("AI has no valid moves, but it's not checkmate/stalemate?") 
                # Potentially declare draw or handle error
                st.session_state.game_status = "game_over" # Or some error state

            st.rerun() # Rerun after AI move completes
            return # Exit after AI move sequence

    # If not PvAI or it was the human's turn in PvAI and AI didn't move/game didn't end, rerun.
    # The AI move logic already includes a rerun and return if it executes.
    st.rerun()






def can_piece_attack_square(piece: str, start: tuple, end: tuple, board: pd.DataFrame) -> bool:
    """
    Checks if a piece can attack a square on the board

    Parameters:
        piece (str): The piece being moved (e.g. "wP, bP")
        start (tuple): The starting position of the piece
        end (tuple): The ending position of the piece
        board (pd.DataFrame): The chess board

    Returns:
        bool: True if the piece can attack the square, False otherwise
    """    

    piece_type = piece[1]
    if piece_type == "P":
        return is_valid_move_pawn(piece, start, end, board)
    elif piece_type == "R":
        return is_valid_move_rook(piece, start, end, board)
    elif piece_type == "B":
        return is_valid_move_bishop(piece, start, end, board)
    elif piece_type == "N":
        return is_valid_move_knight(piece, start, end, board)
    elif piece_type == "Q":
        return is_valid_move_queen(piece, start, end, board)
    elif piece_type == "K":
        return is_valid_move_king(piece, start, end, board)
    else:
        return False

def is_square_attacked(board: pd.DataFrame, square: tuple, attacker_color: str) -> bool:
    """
    Checks if a square on the board is attacked by any of the opponent's pieces

    Parameters:
        board (pd.DataFrame): The chess board
        square (tuple): The row and column index of the square
        color (str): The color of the attacker

    Returns:
        bool: True if the square is attacked, False otherwise
    """
    for i in range(8):
        for j in range(8):
            piece = board.iat[i, j]
            if piece != "." and piece[0] == attacker_color:
                if can_piece_attack_square(piece, (i, j), square, board):
                    return True
    return False

def is_stalemate(board: pd.DataFrame, color: str) -> bool:
    """
    Checks if a player is in stalemate. Requires generating all valid moves.

    Parameters:
        board (pd.DataFrame): The chess board
        color (str): The color of the player to check for stalemate

    Returns:
        bool: True if the player is in stalemate, False otherwise
    """
    # NOTE: This now needs get_all_valid_moves_for_ai from validation.py
    from src.validation import get_all_valid_moves_for_ai 

    if is_check(board, color): # Use is_check from validation.py
        return False # Cannot be stalemate if in check

    # Check if any valid moves exist for the player
    valid_moves = get_all_valid_moves_for_ai(board, color) # Use the AI-safe version
    
    return not valid_moves # Stalemate if not in check and no valid moves


def is_checkmate(board: pd.DataFrame, color: str) -> bool:
    """
    Checks if the player of the given color is in checkmate.

    Parameters:
        board (pd.DataFrame): The chess board
        color (str): The color of the player to check for checkmate

    Returns:
        bool: True if the player is in checkmate, False otherwise
    """
    # Import locally to avoid circular dependency at module level
    # NOTE: This now needs get_all_valid_moves_for_ai from validation.py
    from src.validation import get_all_valid_moves_for_ai

    if not is_check(board, color): # Use is_check from validation.py
        return False # Cannot be checkmate if not in check

    # Check if any valid moves exist for the player
    valid_moves = get_all_valid_moves_for_ai(board, color) # Use the AI-safe version

    return not valid_moves # Checkmate if in check and no valid moves



def promote_pawn(board: pd.DataFrame, pos: tuple, piece: str) -> pd.DataFrame:
    """
    Promotes a pawn to a new piece

    Parameters:
        board (pd.DataFrame): The chess board
        pos (tuple): The row and column index of the pawn
        piece (str): The piece to promote the pawn to (e.g., 'Q', 'R', 'B', 'N')

    Returns:
        pd.DataFrame: The updated chess board
    """
    row, col = pos
    pawn = board.iat[row, col]

    # Basic check: is it a pawn
    if pawn == "." or pawn[1] != "P":
        st.session_state.last_error = "Cannot promote non-pawn piece."
        return board # Return original board if not a pawn

    color = pawn[0]
    # Check if pawn is on the promotion rank
    promotion_rank = 0 if color == 'w' else 7
    if row != promotion_rank:
        st.session_state.last_error = "Pawn not on promotion rank."
        return board # Return original board if not on correct rank

    # Check if the chosen piece is valid
    if piece not in ['Q', 'R', 'B', 'N']:
         st.session_state.last_error = f"Invalid promotion piece: {piece}"
         return board

    board.iat[row, col] = color + piece
    st.session_state.promotion_pending = False # Promotion complete
    st.session_state.promotion_pos = None
    st.session_state.last_error = f"Pawn promoted to {color}{piece}." # Confirmation message
    
    # After promotion, check for check/mate/stalemate against the opponent
    opponent_color = 'b' if color == 'w' else 'w'
    if is_check(board, opponent_color):
        st.session_state.last_error += f" Check!"
        if is_checkmate(board, opponent_color):
             st.session_state.last_error = f"Checkmate! {'White' if color == 'w' else 'Black'} wins by promotion!"
             st.session_state.game_status = "game_over"
        # No stalemate check needed here as the opponent will have a turn
    elif is_stalemate(board, opponent_color): # Check if promotion caused stalemate
        st.session_state.last_error = "Stalemate by promotion! It's a draw!"
        st.session_state.game_status = "game_over"

    return board
