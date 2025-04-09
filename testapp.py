import streamlit as st
import pandas as pd
import math

# --- Dummy / Minimal Chess Functions for Testing AI Move ---

def create_board():
    """Creates a standard chess board initial state as an 8x8 DataFrame."""
    board = pd.DataFrame([
        ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
        ["bP"] * 8,
        ["."] * 8,
        ["."] * 8,
        ["."] * 8,
        ["."] * 8,
        ["wP"] * 8,
        ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
    ])
    return board

def evaluate_board(board: pd.DataFrame) -> int:
    """A simple evaluation function that sums piece values."""
    piece_values = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 1000}
    score = 0
    for i in range(8):
        for j in range(8):
            piece = board.iloc[i, j]
            if piece != ".":
                value = piece_values.get(piece[1], 0)
                if piece[0] == "w":
                    score += value
                else:
                    score -= value
    return score

# For testing purposes, we assume every move is legal as long as destination is empty.
def get_all_valid_moves(board: pd.DataFrame, turn: str) -> list:
    moves = []
    for i in range(8):
        for j in range(8):
            piece = board.iloc[i, j]
            if piece != "." and piece[0] == turn:
                for r in range(8):
                    for c in range(8):
                        if (i, j) == (r, c):
                            continue
                        if board.iloc[r, c] == ".":  # For testing, only allow moves to empty squares.
                            moves.append(((i, j), (r, c)))
    return moves

def simulate_move(board: pd.DataFrame, move: tuple) -> pd.DataFrame:
    """Simulates a move and returns a new board state."""
    board_copy = board.copy(deep=True)
    (i, j), (r, c) = move
    piece = board_copy.iat[i, j]
    board_copy.iat[r, c] = piece
    board_copy.iat[i, j] = "."
    return board_copy

def minimax(board: pd.DataFrame, depth: int, alpha: float, beta: float, maximizing_player: bool, turn: str) -> int:
    moves = get_all_valid_moves(board, turn)
    if depth == 0 or not moves:
        return evaluate_board(board)
    
    next_turn = "b" if turn == "w" else "w"
    
    if maximizing_player:
        max_eval = -math.inf
        for move in moves:
            new_board = simulate_move(board, move)
            eval_value = minimax(new_board, depth-1, alpha, beta, False, next_turn)
            max_eval = max(max_eval, eval_value)
            alpha = max(alpha, eval_value)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        for move in moves:
            new_board = simulate_move(board, move)
            eval_value = minimax(new_board, depth-1, alpha, beta, True, next_turn)
            min_eval = min(min_eval, eval_value)
            beta = min(beta, eval_value)
            if beta <= alpha:
                break
        return min_eval

def get_ai_move(board: pd.DataFrame, turn: str, depth: int = 2) -> tuple:
    best_move = None
    if turn == "w":
        best_eval = -math.inf
    else:
        best_eval = math.inf
    moves = get_all_valid_moves(board, turn)
    st.write("DEBUG: Valid moves for turn", turn, ":", moves)  # Debug output
    for move in moves:
        new_board = simulate_move(board, move)
        next_turn = "b" if turn == "w" else "w"
        eval_value = minimax(new_board, depth-1, -math.inf, math.inf, turn=="w", next_turn)
        st.write("DEBUG: Evaluating move", move, "with eval", eval_value)  # Debug output
        if turn == "w" and eval_value > best_eval:
            best_eval = eval_value
            best_move = move
        elif turn == "b" and eval_value < best_eval:
            best_eval = eval_value
            best_move = move
    st.write("DEBUG: Chosen AI move:", best_move)  # Debug output
    return best_move

# --- Test App Code ---

# Initialize session state if not already set.
if "board" not in st.session_state:
    st.session_state.board = create_board()
if "turn" not in st.session_state:
    # For testing, set turn to Black so the AI will move.
    st.session_state.turn = "b"
if "move_history" not in st.session_state:
    st.session_state.move_history = []
if "board_history" not in st.session_state:
    st.session_state.board_history = [st.session_state.board.copy(deep=True)]

st.title("Chess AI Test App")
st.write("Current board state:")
st.write(st.session_state.board)

st.write("Current turn (AI should move):", st.session_state.turn)

if st.button("Force AI Move"):
    ai_move = get_ai_move(st.session_state.board, st.session_state.turn, depth=2)
    if ai_move:
        new_board = simulate_move(st.session_state.board, ai_move)
        st.session_state.board = new_board
        st.session_state.move_history.append(ai_move)
        st.session_state.board_history.append(new_board.copy(deep=True))
        # Toggle turn: if AI moved, switch back to White.
        st.session_state.turn = "w" if st.session_state.turn == "b" else "b"
    else:
        st.write("No valid AI move found.")
    st.experimental_rerun()

st.write("Board after AI move:")
st.write(st.session_state.board)