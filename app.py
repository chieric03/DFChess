import streamlit as st
import pandas as pd
from src.moves import move_piece
from src.board import create_board
import base64

def get_base64_image(svg_path: str) -> str:
    """
    Reads an SVG file and returns a base64-encoded data URI string.
    
    Parameters:
        svg_path (str): Path to the SVG file.
    
    Returns:
        str: A data URI string that can be used in an <img> tag.
    """
    with open(svg_path, "rb") as svg_file:
        encoded = base64.b64encode(svg_file.read()).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"

images = {
    "wP": get_base64_image("images/white_pawn.svg"),
    "wR": get_base64_image("images/white_rook.svg"),
    "wN": get_base64_image("images/white_knight.svg"),
    "wB": get_base64_image("images/white_bishop.svg"),
    "wQ": get_base64_image("images/white_queen.svg"),
    "wK": get_base64_image("images/white_king.svg"),
    "bP": get_base64_image("images/black_pawn.svg"),
    "bR": get_base64_image("images/black_rook.svg"),
    "bN": get_base64_image("images/black_knight.svg"),
    "bB": get_base64_image("images/black_bishop.svg"),
    "bQ": get_base64_image("images/black_queen.svg"),
    "bK": get_base64_image("images/black_king.svg")
}

def render_board(board: pd.DataFrame) -> str:
    """
    Renders the chess board as HTML using images

    Parameters:
        board (pd.DataFrame): The chess board DataFrame
    """
    html = '<table style= "border-collapse: collapse; border: 1px solid black;">'
    for i in range(8):
        html += "<tr>"
        for j in range(8):
            square_color = '#789cac' if (i+j) % 2 == 0 else '#54616f'
            piece = board.iat[i,j]
            cell_html = f'<td style="width: 60px; height: 60px; background-color: {square_color}; text-align: center; vertical-align: middle;">'
            if piece != ".":
                img_url = images[piece]
                cell_html += f'<img src="{img_url}" style="max-width: 50px; max-height: 50px;">'
            cell_html += "</td>"
            html += cell_html
        html += "</tr>"
    html += "</table>"
    return html


#Session State Initialization
if "board" not in st.session_state:
    st.session_state.board = create_board()
if "turn" not in st.session_state:
    st.session_state.turn = "w"

#Game Mode Selection
st.sidebar.title("Game Mode")
game_mode = st.sidebar.radio("Select game mode", ["Player vs Player", "Player vs AI (Coming soon)"])

#Main Game
st.title("DFChess")
st.write(f"!!Current Turn: {'White' if st.session_state.turn == 'w' else 'Black'}!!")

#Render the board
st.markdown(render_board(st.session_state.board), unsafe_allow_html=True)

#Move Input
st.subheader("Move:")
StartCol, EndCol = st.columns(2)
with StartCol:
    start_pos = st.text_input("Start Position (e.g. A2):", value = "")
with EndCol:
    end_pos = st.text_input("End Position (e.g. A4):", value = "")

if st.button("Submit:"):
    if start_pos and end_pos:
        updated_board = move_piece(st.session_state.board, start_pos, end_pos)

        st.session_state.board = updated_board

        st.session_state.turn = "b" if st.session_state.turn == "w" else "w"

        st.rerun()

    else:
        st.error("Please enter both start and end positions")


    