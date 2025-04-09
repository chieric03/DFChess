import pandas as pd


def find_king(board: pd.DataFrame, color: str) -> tuple | None:
    """
    Find the position of the king of the given color on the board

    Parameters:
        board (pd.DataFrame): The chess board
        color (str): The color of the king to find

    Returns:
        tuple | None: The row and column index, or None if not found.
    """
    king_name = color + "K"
    for i in range(8):
        for j in range(8):
            if board.iat[i, j] == king_name:
                return i, j
    return None

def is_valid_move_pawn(piece, start, end, board, en_passant_target: tuple | None):
    """
    Checks if a move is valid for a pawn

    Parameters:
        piece (str): The piece being moved (e.g. "wP, bP")
        start (tuple): The starting position of the piece
        end (tuple): The ending position of the piece
        board (pd.DataFrame): The chess board
        en_passant_target (tuple | None): The current en passant target square, if any.

    Returns:
        bool: True if the move is valid, False otherwise
    """
    rs, cs = start
    re, ce = end
    color = piece[0]
    direction = -1 if color == "w" else 1
    start_row = 6 if color == "w" else 1

    #Moving forward
    if cs == ce:
        #single step
        if re == rs + direction and board.iat[re, ce] == ".":
            return True
        #double step
        if rs == start_row and re == rs + 2 * direction:
            if board.iat[re, ce] == "." and board.iat[re - direction, ce] == ".":
                return True

    #Capture
    if abs(cs - ce) == 1 and re == rs + direction:
        target_piece = board.iat[re, ce]
        if target_piece != "." and target_piece[0] != color:
            return True
        #En passant
        if en_passant_target == (re, ce) and target_piece == ".":
             # Check the square being passed over contains the opponent's pawn that just moved two squares
             passed_square_piece = board.iat[rs, ce]
             opponent_pawn = ('b' if color == 'w' else 'w') + 'P'
             # Simple check: is the piece being captured en passant the correct opponent pawn?
             # A more robust check would involve move history, but this covers basic cases.
             if passed_square_piece == opponent_pawn:
                 return True

    return False

def is_valid_move_rook(piece, start, end, board):
    """
    Checks if a move is valid for a rook

    Parameters:
        piece (str): The piece being moved (e.g. "wR, bR")
        start (tuple): The starting position of the piece
        end (tuple): The ending position of the piece
        board (pd.DataFrame): The chess board
    """
    rs, cs = start
    re, ce = end

    if rs != re and cs != ce:
        return False

    if rs == re: #Horizontal move
        step = 1 if ce > cs else -1
        for col in range(cs + step, ce, step):
            if board.iat[rs, col] != ".":
                return False

    else: #Vertical move
        step = 1 if re > rs else -1
        for row in range(rs + step, re, step):
            if board.iat[row, cs] != ".":
                return False

    target = board.iat[re, ce]

    if target == ".":
        return True

    elif target[0] != piece[0]:
        return True

    else: #Friendly piece
        return False

def is_valid_move_bishop(piece, start, end, board):
    """
    Checks if a move is valid for a bishop

    Parameters:
        piece (str): The piece being moved (e.g. "wB, bB")
        start (tuple): The starting position of the piece
        end (tuple): The ending position of the piece
        board (pd.DataFrame): The chess board

    Returns:
        bool: True if the move is valid, False otherwise
    """

    rs, cs = start
    re, ce = end

    #checking if move is diagonal
    if abs(rs - re) != abs(cs - ce):
        return False

    #getting direction
    row_step = 1 if re > rs else -1
    col_step = 1 if ce > cs else -1

    #checking for pieces in the way
    current_row, current_col = rs + row_step, cs + col_step
    while current_row != re or current_col != ce: # Check until destination square
        if board.iat[current_row, current_col] != ".":
            return False
        current_row += row_step
        current_col += col_step

    target = board.iat[re, ce]

    if target == ".":
        return True
    elif target[0] != piece[0]:
        return True
    else: #Friendly piece
        return False

def is_valid_move_knight(piece, start, end, board):
    """
    checks if a move is valid for a knight

    Parameters:
        piece (str): The piece being moved (e.g. "wN, bN")
        start (tuple): The starting position of the piece
        end (tuple): The ending position of the piece
        board (pd.DataFrame): The chess board

    Returns:
        bool: True if the move is valid, False otherwise
    """

    rs, cs = start
    re, ce = end

    row_diff = abs(rs - re)
    col_diff = abs(cs - ce)

    if (row_diff,col_diff) not in [(1,2),(2,1)]:
        return False

    target = board.iat[re, ce]

    if target == ".":
        return True
    elif target[0] != piece[0]:
        return True
    else: #Friendly piece
        return False

def is_valid_move_queen(piece, start, end, board):
    """
    Checks if a move is valid for a queen

    Parameters:
        piece (str): The piece being moved (e.g. "wQ, bQ")
        start (tuple): The starting position of the piece
        end (tuple): The ending position of the piece
        board (pd.DataFrame): The chess board

    Returns:
        bool: True if the move is valid, False otherwise
    """
    # Queen moves like a rook or a bishop
    return is_valid_move_rook(piece, start, end, board) or \
           is_valid_move_bishop(piece, start, end, board)


def is_valid_move_king(piece, start, end, board, castling_rights: dict):
    """
    Checks if a move is valid for a king

    Parameters:
        piece (str): The piece being moved (e.g. "wK, bK")
        start (tuple): The starting position of the piece
        end (tuple): The ending position of the piece
        board (pd.DataFrame): The chess board
        castling_rights (dict): Dictionary containing castling availability (e.g., {'wK': True, 'wQ': True, ...})

    Returns:
        bool: True if the move is valid, False otherwise
    """
    rs, cs = start
    re, ce = end
    color = piece[0]
    opponent_color = 'b' if color == 'w' else 'w'

    # Standard 1-square move
    if abs(re - rs) <= 1 and abs(ce - cs) <= 1:
        target = board.iat[re, ce]
        if target == "." or target[0] != color:
             # Check if the destination square is attacked by the opponent
             # Need to simulate the move temporarily to check for checks is handled *after* this validation
             # but we must ensure the king doesn't move *into* an attacked square
             if not is_square_attacked(board, (re, ce), opponent_color):
                 return True
        return False # Moving onto friendly piece or into check

    # Castling
    if abs(ce - cs) == 2 and rs == re: # King moves two squares horizontally
        # Check if king or relevant rook has moved (using castling_rights)
        king_moved_key = f"{color}K"
        if castling_rights.get(king_moved_key, False): # If king has moved, cannot castle
             return False

        if ce > cs: # Kingside castling
            rook_key = f"{color}R_kingside" # Assuming keys like 'wR_kingside', 'bR_kingside'
            rook_col = 7
            path_cols = [5, 6]
        else: # Queenside castling
            rook_key = f"{color}R_queenside" # Assuming keys like 'wR_queenside', 'bR_queenside'
            rook_col = 0
            path_cols = [1, 2, 3]

        # Check if rook has moved
        if castling_rights.get(rook_key, False):
            return False

        # Check if path is clear
        for col in path_cols:
            if board.iat[rs, col] != ".":
                return False

        # Check if king is in check, passes through check, or lands in check
        if is_square_attacked(board, (rs, cs), opponent_color): # King currently in check
            return False
        for col in [cs + (1 if ce > cs else -1), ce]: # Squares king moves over/to
             if is_square_attacked(board, (rs, col), opponent_color):
                 return False

        # If all checks pass, castling is valid
        return True

    return False # Not a standard move or valid castling


def can_piece_attack_square(piece: str, start: tuple, end: tuple, board: pd.DataFrame) -> bool:
    """
    Checks if a piece *could* attack a square, ignoring intervening pieces for sliding pieces.
    Used primarily for check detection. Note the difference from is_valid_move_* which checks for obstructions.

    Parameters:
        piece (str): The piece attacking (e.g. "wP, bP")
        start (tuple): The starting position of the piece
        end (tuple): The square being attacked
        board (pd.DataFrame): The chess board (used mainly for pawn attacks)

    Returns:
        bool: True if the piece type can attack the square from its position, False otherwise
    """
    rs, cs = start
    re, ce = end
    color = piece[0]
    piece_type = piece[1]

    if piece_type == "P":
        direction = -1 if color == "w" else 1
        return re == rs + direction and abs(ce - cs) == 1
    elif piece_type == "N":
        row_diff = abs(rs - re)
        col_diff = abs(cs - ce)
        return (row_diff == 1 and col_diff == 2) or (row_diff == 2 and col_diff == 1)
    elif piece_type == "B":
        return abs(rs - re) == abs(cs - ce)
    elif piece_type == "R":
        return rs == re or cs == ce
    elif piece_type == "Q":
        return abs(rs - re) == abs(cs - ce) or rs == re or cs == ce
    elif piece_type == "K":
        return abs(rs - re) <= 1 and abs(cs - ce) <= 1
    else:
        return False


def is_square_attacked(board: pd.DataFrame, square: tuple, attacker_color: str) -> bool:
    """
    Checks if a square on the board is attacked by any of the opponent's pieces.

    Parameters:
        board (pd.DataFrame): The chess board
        square (tuple): The row and column index of the square being checked
        attacker_color (str): The color of the pieces potentially attacking

    Returns:
        bool: True if the square is attacked, False otherwise
    """
    for i in range(8):
        for j in range(8):
            piece = board.iat[i, j]
            if piece != "." and piece[0] == attacker_color:
                # Check if this piece type can attack the target square
                if can_piece_attack_square(piece, (i, j), square, board):
                    # For sliding pieces (Rook, Bishop, Queen), check for obstructions
                    if piece[1] in ['R', 'B', 'Q']:
                        obstructed = False
                        if i == square[0]: # Horizontal attack
                            step = 1 if square[1] > j else -1
                            for col in range(j + step, square[1], step):
                                if board.iat[i, col] != ".":
                                    obstructed = True
                                    break
                        elif j == square[1]: # Vertical attack
                            step = 1 if square[0] > i else -1
                            for row in range(i + step, square[0], step):
                                if board.iat[row, j] != ".":
                                    obstructed = True
                                    break
                        elif abs(i - square[0]) == abs(j - square[1]): # Diagonal attack
                            row_step = 1 if square[0] > i else -1
                            col_step = 1 if square[1] > j else -1
                            curr_r, curr_c = i + row_step, j + col_step
                            while curr_r != square[0]: # Check until the target square
                                if board.iat[curr_r, curr_c] != ".":
                                    obstructed = True
                                    break
                                curr_r += row_step
                                curr_c += col_step
                        if not obstructed:
                            return True # Sliding piece has clear path
                    else: # Pawn, Knight, King - obstruction check not needed here
                        return True
    return False

def is_check(board: pd.DataFrame, color: str) -> bool:
    """
    Checks if a player is in check.

    Parameters:
        board (pd.DataFrame): The chess board
        color (str): The color of the player potentially in check

    Returns:
        bool: True if the player is in check, False otherwise
    """
    king_pos = find_king(board, color)
    if not king_pos:
        # This case should ideally not happen in a valid game state
        print(f"Warning: King of color {color} not found on board.")
        return False # Or handle as an error state
    attacker_color = "b" if color == "w" else "w"
    return is_square_attacked(board, king_pos, attacker_color)


# AI OPPONENT IMPLEMENTATION

def get_all_valid_moves_for_ai(board: pd.DataFrame, turn: str) -> list:
    """
    Generates all valid moves for the given player's turn.
    This version is intended for use by the AI and does not rely on session state.
    It assumes default castling rights and no en passant target for simplicity,
    as the AI currently doesn't track these states explicitly.
    A more robust AI would need to receive this state information.
    """
    valid_moves = []
    # Assume default state for AI context (no castling, no en passant)
    en_passant_target = None 
    castling_rights = {} # Empty dict implies no castling rights available

    for i in range(8):
        for j in range(8):
            piece = board.iat[i, j]
            if piece != '.' and piece[0] == turn:
                for r in range(8):
                    for c in range(8):
                        if (i, j) == (r, c):
                            continue
                        
                        pseudo_legal = False
                        if piece[1] == "P":
                            pseudo_legal = is_valid_move_pawn(piece, (i, j), (r, c), board, en_passant_target)
                        elif piece[1] == "R":
                            pseudo_legal = is_valid_move_rook(piece, (i, j), (r, c), board)
                        elif piece[1] == "B":
                            pseudo_legal = is_valid_move_bishop(piece, (i, j), (r, c), board)
                        elif piece[1] == "N":
                            pseudo_legal = is_valid_move_knight(piece, (i, j), (r, c), board)
                        elif piece[1] == "Q":
                            pseudo_legal = is_valid_move_queen(piece, (i, j), (r, c), board)
                        elif piece[1] == "K":
                            pseudo_legal = is_valid_move_king(piece, (i, j), (r, c), board, castling_rights)
                        
                        if pseudo_legal:
                            # Simulate the move to check if it leaves the king in check
                            board_copy = board.copy(deep=True)
                            board_copy.iat[r, c] = piece
                            board_copy.iat[i, j] = "."
                            # Check if the current player's king is NOT in check after the move
                            if not is_check(board_copy, turn):
                                valid_moves.append(((i, j), (r, c)))
                                
    return valid_moves
