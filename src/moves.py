import streamlit as st
import src.logger as logger
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

    if piece == ".":
        st.error("No piece at starting position!")
        return board, False
    
    current_turn = st.session_state.turn
    if piece[0] != current_turn:
        st.error("It's not your turn!")
        return board, False


    valid_move = False

    if piece[1] == "P":
        valid_move = is_valid_move_pawn(piece, start, end, board)
    elif piece[1] == "R":
        valid_move = is_valid_move_rook(piece, start, end, board)
    elif piece[1] == "B":
        valid_move = is_valid_move_bishop(piece, start, end, board)
    elif piece[1] == "N":
        valid_move = is_valid_move_knight(piece, start, end, board)
    elif piece[1] == "Q":
        valid_move = is_valid_move_queen(piece, start, end, board)
    elif piece[1] == "K":
        valid_move = is_valid_move_king(piece, start, end, board)
    else:
        st.error("Invalid piece!")
        return board, False
    
    if not valid_move:
        st.error("Invalid move!")
        return board, False
    
    board.iat[end[0], end[1]] = piece
    board.iat[start[0], start[1]] = "."
    
    return board, True



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
    direction = -1 if piece[0] == "w" else 1

    #One square forward
    if cs == ce and re == rs + direction and board.iat[re, ce] == ".":
        return True
    
    #Two squares forward
    if ((piece[0] == "w" and rs == 6) or (piece[0] == "b" and rs == 1)) and cs == ce:
        if (re == rs + 2 * direction and
            board.iat[rs + direction, cs] == "." and
            board.iat[re, ce] == "."):
            return True
        
    #Capture
    if abs(cs - ce) == 1 and re == rs + direction:
        if board.iat[re, ce] != "." and board.iat[re, ce][0] != piece[0]:
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
    