import pandas as pd
import math
# Import necessary functions from validation.py (to break circular import)
from src.validation import (
    is_valid_move_pawn, is_valid_move_rook, is_valid_move_bishop, 
    is_valid_move_knight, is_valid_move_queen, is_valid_move_king, 
    is_check, find_king # Import is_check and find_king as well
)

def evaluate_board(board: pd.DataFrame) -> int:
    piece_values = {
        "P": 1,
        "N": 3,
        "B": 3,
        "R": 5,
        "Q": 9,
        "K": 1000
    }
    score = 0
    for i in range(8):
        for j in range(8):
            piece = board.iloc[i, j]
            if piece != "." and piece != "":
                # Use the second character as the piece type.
                score += piece_values.get(piece[1], 0) if piece[0] == "w" else -piece_values.get(piece[1], 0)
                # Optional: add bonus for central control.
                if (i, j) in [(3, 3), (3, 4), (4, 3), (4, 4)]:
                    score += 0.1 if piece[0] == "w" else -0.1
    return score

def get_all_valid_moves(board: pd.DataFrame, turn: str) -> list:
    valid_moves = []
    for i in range(8):
        for j in range(8):
            piece = board.iloc[i, j]
            if piece != '.' and piece[0] == turn:
                for r in range(8):
                    for c in range(8):
                        if (i, j) == (r, c):
                            continue
                        # Pass necessary state to validation functions from validation.py
                        # AI context doesn't have session state, so pass defaults/None.
                        en_passant_target = None # AI doesn't track this directly here
                        castling_rights = {}     # AI doesn't track this directly here

                        if piece[1] == "P":
                            valid = is_valid_move_pawn(piece, (i, j), (r, c), board, en_passant_target)
                        elif piece[1] == "R":
                            valid = is_valid_move_rook(piece, (i, j), (r, c), board)
                        elif piece[1] == "B":
                            valid = is_valid_move_bishop(piece, (i, j), (r, c), board)
                        elif piece[1] == "N":
                            valid = is_valid_move_knight(piece, (i, j), (r, c), board)
                        elif piece[1] == "Q":
                            valid = is_valid_move_queen(piece, (i, j), (r, c), board)
                        elif piece[1] == "K":
                            # Pass empty castling rights dict; AI doesn't castle yet based on this logic
                            valid = is_valid_move_king(piece, (i, j), (r, c), board, castling_rights) 
                        else:
                            valid = False

                        if valid:
                            # Simulate move and check if it leaves the king in check
                            board_copy = board.copy(deep=True)
                            board_copy.iat[r, c] = piece
                            board_copy.iat[i, j] = "."
                            if not is_check(board_copy, turn):
                                valid_moves.append(((i, j), (r, c)))
    return valid_moves

# Note: The is_valid_move_*, is_check functions are now imported from src.validation

def simulate_move(board: pd.DataFrame, move: tuple) -> pd.DataFrame:
    """
    Returns a new board after simulating the move
    """
    board_copy = board.copy(deep=True)
    (i, j), (r, c) = move
    piece = board_copy.iat[i, j]
    board_copy.iat[r, c] = piece
    board_copy.iat[i, j] = "."
    return board_copy

def minimax(board: pd.DataFrame, depth: int, alpha: int, beta: int, maximizing_player: bool, turn: str) -> int:
    moves = get_all_valid_moves(board, turn)
    if depth == 0 or not moves:
        return evaluate_board(board)
    
    # Toggle the turn for the next ply.
    next_turn = "b" if turn == "w" else "w"
    
    if maximizing_player:
        max_eval = -math.inf
        for move in moves:
            new_board = simulate_move(board, move)
            eval = minimax(new_board, depth-1, alpha, beta, False, next_turn)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        for move in moves:
            new_board = simulate_move(board, move)
            eval = minimax(new_board, depth-1, alpha, beta, True, next_turn)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval


def get_ai_move(board: pd.DataFrame, turn: str, depth: int) -> tuple | None:
    """
    Determines the best move for the AI using the minimax algorithm.

    Parameters:
        board (pd.DataFrame): The current board state.
        turn (str): The current player's turn ('w' or 'b').
        depth (int): The search depth for the minimax algorithm.

    Returns:
        tuple | None: The best move found as ((start_row, start_col), (end_row, end_col)),
                      or None if no valid moves are available.
    """
    best_move = None
    best_value = -math.inf if turn == "w" else math.inf
    alpha = -math.inf
    beta = math.inf
    
    maximizing_player = (turn == "w")
    next_turn = "b" if turn == "w" else "w"

    valid_moves = get_all_valid_moves(board, turn)
    if not valid_moves:
        return None # No legal moves

    for move in valid_moves:
        new_board = simulate_move(board, move)
        board_value = minimax(new_board, depth - 1, alpha, beta, not maximizing_player, next_turn)

        if maximizing_player:
            if board_value > best_value:
                best_value = board_value
                best_move = move
            alpha = max(alpha, board_value)
        else: # Minimizing player ('b')
            if board_value < best_value:
                best_value = board_value
                best_move = move
            beta = min(beta, board_value)
        
        # Alpha-beta pruning
        if beta <= alpha:
            break # Prune the branch

    return best_move
