import pandas as pd
import math



def evaluate_board(board: pd.DataFrame) -> int:
    """
    Evaluate the board state using a simple heuristic
    """
    # Piece values
    piece_values = {
        "P": 1,
        "N": 3,
        "B": 3,
        "R": 5,
        "Q": 9,
        "K": 1000
    }
    # Initialize score
    score = 0
    # Iterate over the board
    for i in range(8):
        for j in range(8):
            piece = board.iloc[i, j]
            if piece != "":
                # Add the piece value to the score
                score += piece_values[piece]
                # Add a bonus for the center
                if (i, j) in [(3, 3), (3, 4), (4, 3), (4, 4)]:
                    score += 0.1
    return score

def get_all_valid_moves(board:pd.DataFrame, turn:str) -> list:
    """
    Returns a list of valid mvoes for the player of turn
    """
    valid_moves = []
    # Iterate over the board
    for i in range(8):
        for j in range(8):
            piece = board.iloc[i, j]
            # Check if the piece belongs to the current player
            if piece != '.' and piece[0] == turn:
                for r in range(8):
                    for c in range(8):
                        if (i,j) == (r,c):
                            continue

                        if piece[1] == "P":
                            valid = is_valid_move_pawn(piece, (i, j), (r, c), board)
                        elif piece[1] == "R":
                            valid = is_valid_move_rook(piece, (i, j), (r, c), board)
                        elif piece[1] == "B":
                            valid = is_valid_move_bishop(piece, (i, j), (r, c), board)
                        elif piece[1] == "N":
                            valid = is_valid_move_knight(piece, (i, j), (r, c), board)
                        elif piece[1] == "Q":
                            valid = is_valid_move_queen(piece, (i, j), (r, c), board)
                        elif piece[1] == "K":
                            valid = is_valid_move_king(piece, (i, j), (r, c), board)
                        else:
                            valid = False

                        if valid:
                            board_copy = board.copy(deep=True)
                            board_copy.iat[r,c] = piece
                            board_copy.iat[i,j] = "."
                            if not is_check(board_copy, turn):
                                valid_moves.append(((i, j), (r, c)))
    return valid_moves

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
    """
    Returns eval score for the board using minimax algorithm with alpha-beta pruning
    
    Parameters: 
    board (pd.DataFrame): The current board state
    depth (int): The depth of the search tree
    alpha (int): The alpha value for alpha-beta pruning
    beta (int): The beta value for alpha-beta pruning
    maximizing_player (bool): True if the current player is maximizing
    turn (str): The current player's turn
    """

    moves = get_all_valid_moves(board, turn)
    if depth == 0 or not moves:
        return evaluate_board(board)
    
    if maximizing_player:
        max_eval = -math.inf
        for move in moves:
            new_board = simulate_move(board, move)
            eval = minimax(new_board, depth-1, alpha, beta, False, "b")
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        for move in moves:
            new_board = simulate_move(board, move)
            eval = minimax(new_board, depth-1, alpha, beta, True, "w")
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval
    
def get_ai_move(board: pd.DataFrame, turn: str, depth: int = 2) -> tuple:
    """
    Returns the best move for the current player using minimax algorithm

    Parameters:
    board (pd.DataFrame): The current board state
    depth (int): The depth of the search tree
    turn (str): The current player's turn

    Returns:
    tuple: The best move
    """
    
    best_move = None
    if turn == 'w':
        best_eval = -math.inf
    else: 
        best_eval = math.inf

    moves = get_all_valid_moves(board, turn)
    for move in moves:
        new_board = simulate_move(board, move)
        eval = minimax(new_board, depth-1, -math.inf, math.inf, turn == 'b', 'b' if turn == 'w' else 'w')
        if turn == 'w' and eval > best_eval:
            best_eval = eval
            best_move = move
        elif turn == 'b' and eval < best_eval:
            best_eval = eval
            best_move = move
    return best_move
