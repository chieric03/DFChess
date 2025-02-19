import pandas as pd

def create_board():
    """
    Creates a new chess board
    """
    columns = list("ABCDEFGH")
    rows = list(range(8,0,-1))
    board = pd.DataFrame([
        ["bR","bN","bB","bQ","bK","bB","bN","bR"],
        ["bP","bP","bP","bP","bP","bP","bP","bP"],
        [".",".",".",".",".",".",".","."],
        [".",".",".",".",".",".",".","."],
        [".",".",".",".",".",".",".","."],
        [".",".",".",".",".",".",".","."],
        ["wP","wP","wP","wP","wP","wP","wP","wP"],
        ["wR","wN","wB","wQ","wK","wB","wN","wR"]
    ],index=rows, columns=columns)
    return board

    