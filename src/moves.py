import src.logger as logger
import streamlit as st
import pandas as pd

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

    if piece[1] == "P":
        valid_move = is_valid_move_pawn(piece, start, end, board)
        direction = -1 if color == "w" else 1
        # If the pawn moves two squares forward, set en passant target.
        if abs(end[0] - start[0]) == 2:
            st.session_state.en_passant_target = (start[0] + direction, start[1])
        # En passant capture: pawn moves diagonally into an empty square.
        if abs(end[1] - start[1]) == 1 and board.iat[end[0], end[1]] == ".":
            if st.session_state.get("en_passant_target") == (end[0], end[1]):
                # Remove the opponent pawn that's being captured en passant.
                board.iat[start[0], end[1]] = "."
    elif piece_type == "R":
        valid_move = is_valid_move_rook(piece, start, end, board)
    elif piece_type == "B":
        valid_move = is_valid_move_bishop(piece, start, end, board)
    elif piece_type == "N":
        valid_move = is_valid_move_knight(piece, start, end, board)
    elif piece_type == "Q":
        valid_move = is_valid_move_queen(piece, start, end, board)
    elif piece_type == "K":
        valid_move = is_valid_move_king(piece, start, end, board)
    else:
        st.session_state.last_error = "Invalid piece!"
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
    st.session_state.move_history.append((start, end, piece))
    st.session_state.board_history.append(updated_board.copy(deep=True))

    #Check for promotion
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

    #Check for check
    if is_check(st.session_state.board, new_turn):
        st.session_state.last_error = f"Check! {'White' if new_turn == 'b' else 'Black'} is in check!"
        if is_checkmate(st.session_state.board, new_turn):
            st.session_state.last_error= f"Checkmate! {'White' if new_turn == 'b' else 'Black'} wins!"
            st.session_state.game_status = "game_over"
            return
        elif is_stalemate(st.session_state.board, new_turn):
            st.session_state.last_error= "Stalemate! It's a draw!"
            st.session_state.game_status = "game_over"
            return
        
    st.session_state.turn = new_turn
    st.rerun()

def find_king(board: pd.DataFrame, color: str) -> tuple:
    """
    Find the position of the king of the given color on the board

    Parameters:
        board (pd.DataFrame): The chess board
        color (str): The color of the king to find

    Returns:
        tuple: The row and column index
    """
    king_name = color + "K"
    for i in range(8):
        for j in range(8):
            if board.iat[i, j] == king_name:
                return i, j
    return None

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
    Checks if a player is in stalemate

    Parameters:
        board (pd.DataFrame): The chess board
        color (str): The color of the player

    Returns:
        bool: True if the player is in stalemate, False otherwise
    """

    if is_check(board, color):
        return False
    
    for i in range(8):
        for j in range(8):
            piece = board.iat[i, j]
            if piece != "." and piece[0] == color:
                for k in range(8):
                    for l in range(8):
                        if (i, j) == (k, l):
                            continue
                        if can_piece_attack_square(piece, (i, j), (k, l), board):
                            board_copy = board.copy(deep = True)
                            board_copy.iat[k, l] = piece
                            board_copy.iat[i, j] = "."
                            if not is_check(board_copy, color):
                                return False
    return True

def is_check(board: pd.DataFrame, color: str) -> bool:
    """
    Checks if a player is in check

    Parameters:
        board (pd.DataFrame): The chess board
        color (str): The color of the player

    Returns:
        bool: True if the player is in check, False otherwise
    """
    king_pos = find_king(board, color)
    if not king_pos:
        return True
    attacker_color = "b" if color == "w" else "w"
    return is_square_attacked(board, king_pos, attacker_color)

def is_checkmate(board: pd.DataFrame, color: str) -> bool:
    """
    Returns True if the player of color is in checkmate, False otherwise

    Parameters:
        board (pd.DataFrame): The chess board
        color (str): The color of the player

    Returns:
        bool: True if the player is in checkmate, False otherwise
    """

    if not is_check(board, color):
        return False
    
    for i in range(8):
        for j in range(8):
            piece = board.iat[i, j]
            if piece != "." and piece[0] == color:
                for k in range(8):
                    for l in range(8):
                        if (i, j) == (k, l):
                            continue
                        if can_piece_attack_square(piece, (i, j), (k, l), board):
                            board_copy = board.copy(deep = True)
                            board_copy.iat[k, l] = piece
                            board_copy.iat[i, j] = "."
                            if not is_check(board_copy, color):
                                return False
    return True

def is_valid_move_pawn(piece, start, end, board):
    """
    Checks if a move is valid for a pawn

    Parameters:
        piece (str): The piece being moved (e.g. "wP, bP")
        start (tuple): The starting position of the piece
        end (tuple): The ending position of the piece
        board (pd.DataFrame): The chess board

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
        if board.iat[re, ce] != "." and board.iat[re, ce][0] != color:
            return True
        #En passant
        if "en_passant_target" in st.session_state and st.session_state.en_passant_target == (re, ce):
            if board.iat[rs, ce] == color + "P":
                return True
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
    while current_row != re and current_col != ce:
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
    
    rs, cs = start
    re, ce = end

    if rs == re or cs == ce:
        if rs == re: #Horizontal
            step = 1 if ce > cs else -1
            for col in range(cs + step, ce, step):
                if board.iat[rs, col] != ".":
                    return False
        else: #Vertical move
            step = 1 if re > rs else -1
            for row in range(rs + step, re, step):
                if board.iat[row, cs] != ".":
                    return False
    
    elif abs(rs - re) == abs(cs - ce):
        row_step = 1 if re > rs else -1
        col_step = 1 if ce > cs else -1
        current_row, current_col = rs + row_step, cs + col_step
        while current_row != re and current_col != ce:
            if board.iat[current_row, current_col] != ".":
                return False
            current_row += row_step
            current_col += col_step
    else:
        return False
    
    target = board.iat[re, ce]

    if target == ".":
        return True
    elif target[0] != piece[0]:
        return True
    else: #Friendly piece
        return False

def is_valid_move_king(piece, start, end, board):
    """
    Checks if a move is valid for a king

    Parameters:
        piece (str): The piece being moved (e.g. "wK, bK")
        start (tuple): The starting position of the piece
        end (tuple): The ending position of the piece
        board (pd.DataFrame): The chess board
    
    Returns:
        bool: True if the move is valid, False otherwise
    """
    rs, cs = start
    re, ce = end

    if abs(re - rs) > 1 or abs(ce - cs) > 1:
        return False
    
    target = board.iat[re, ce]

    if target == ".":
        return True
    elif target[0] != piece[0]:
        return True
    else: #Friendly piece
        return False
    
    #Castling
    if rs == re and abso(ce-cs) == 2:
        if piece[0] == "w" and start == (7,4):
            if ce == 6: #Kingside
                if board.iat[7,5] != "." or board.iat[7,6] != ".":
                    return False
                if is_square_attacked(board, (7,4), "b") or is_square_attacked(board, (7,5), "b") or is_square_attacked(board, (7,6), "b"):
                    return False
                if not st.session_state.castling_rights("wK", True) or not st.session_state.castling_rights.get("wR_kingside", True):
                    return False
                return True
            elif ce == 2: #Queenside
                if board.iat[7,1] != "." or board.iat[7,2] != "." or board.iat[7,3] != ".":
                    return False
                if is_square_attacked(board, (7,4), "b") or is_square_attacked(board, (7,3), "b") or is_square_attacked(board, (7,2), "b"):
                    return False
                if not st.session_state.castling_rights("wK", True) or not st.session_state.castling_rights.get("wR_queenside", True):
                    return False
                return True
        elif piece[0] == "b" and start == (0,4):
            if ce == 6:
                if board.iat[0,5] != "." or board.iat[0,6] != ".":
                    return False
                if is_square_attacked(board, (0,4), "w") or is_square_attacked(board, (0,5), "w") or is_square_attacked(board, (0,6), "w"):
                    return False
                if not st.session_state.castling_rights("bK", True) or not st.session_state.castling_rights.get("bR_kingside", True):
                    return False
                return True
            if ce == 2:
                if board.iat[0,1] != "." or board.iat[0,2] != "." or board.iat[0,3] != ".":
                    return False
                if is_square_attacked(board, (0,4), "w") or is_square_attacked(board, (0,3), "w") or is_square_attacked(board, (0,2), "w"):
                    return False
                if not st.session_state.castling_rights("bK", True) or not st.session_state.castling_rights.get("bR_queenside", True):
                    return False
                return True
    return False
    
def promote_pawn(board: pd.DataFrame, pos: tuple, piece: str) -> pd.DataFrame:
    """
    Promotes a pawn to a new piece

    Parameters:
        board (pd.DataFrame): The chess board
        pos (tuple): The row and column index of the pawn
        piece (str): The piece to promote the pawn to

    Returns:
        pd.DataFrame: The updated chess board
    """
    row, col = pos
    pawn = board.iat[row, col]

    if pawn == "." or pawn[1] != "P":
        return board
    
    color = pawn[0]
    board.iat[row, col] = color + piece
    return board