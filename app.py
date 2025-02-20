import streamlit as st
import pandas as pd
from src.moves import move_piece
from src.board import create_board
from src.logger import logger
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
     #Initializing Board
    html = """
    <style>
      .chess-board {
        border-collapse: collapse;
        margin: auto;
      }
      .chess-board td {
        width: 60px;
        height: 60px;
        text-align: center;
        vertical-align: middle;
        border: 1px solid black;
        padding: 0;
      }
      .label-cell {
        background-color: #e1e1e1;
        font-weight: bold;
      }
      .light-square {
        background-color: #789cac;
      }
      .dark-square {
        background-color: #54616f;
      }
      .chess-board img {
        max-width: 50px;
        max-height: 50px;
      }
    </style>
    <div>
        <table class="chess-board">
    """

    #A-H columns
    html += '<tr>'
    html += '<td class="label-cell"></td>'
    for col in range(8):
        col_label = chr(ord("A") + col)
        html += f'<td class="label-cell">{col_label}</td>'
    html += '<td class="label-cell"></td>'
    html += '</tr>'

    #For each following row, row label and cells
    for i in range(8):
        row_label = 8-i
        html += '<tr>'
        html += f'<td class="label-cell">{row_label}</td>'

        for j in range(8):
            square_color = 'light-square' if (i+j) % 2 == 0 else 'dark-square'
            piece = board.iat[i,j]
            cell_html = f'<td class="{square_color}">'
            if piece != ".":
                img_url = images[piece]
                cell_html += f'<img src="{img_url}">'
            cell_html += "</td>"
            html += cell_html
        html += f'<td class="label-cell">{row_label}</td>'
        html += "</tr>"

    #bottom row labels
    html += "<tr>"
    html += '<td class="label-cell"></td>'
    for j in range(8):
        col_letter = chr(ord('A') + j)
        html += f'<td class="label-cell">{col_letter}</td>'
    html += '<td class="label-cell"></td>'
    html += "</tr>"


    html += """
        </table>
    </div>
    """
    return html

    """
    #A-H columns
    html += "<tr><td style= 'width: 60px; height: 60px; background-color: #e1e1e1; text-align: center; vertical-align: middle;'></td>"
    for col in range(8):
        col_label = chr(ord("A") + col)
        html += f'<td style= "width: 60px; height: 60px; background-color: #e1e1e1; text-align: center; vertical-align: middle;">{col_label}</td>'
    html += "</tr>"



    for i in range(8):
        row_label = 8-i
        html += f'<td style= "width: 60px; height: 60px; background-color: #e1e1e1; text-align: center; vertical-align: middle;">{row_label}</td>'
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
"""

logger.info("Starting DFChess")

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


#Render the board
#st.markdown(render_board(st.session_state.board), unsafe_allow_html=True)
html_board = render_board(st.session_state.board)
st.components.v1.html(html_board, height= 600)

#Move Input
st.subheader(f"Move ({'White' if st.session_state.turn == 'w' else 'Black'})")
StartCol, EndCol = st.columns(2)
with StartCol:
    start_pos = st.text_input("Start Position (e.g. A2):", value = "")
with EndCol:
    end_pos = st.text_input("End Position (e.g. A4):", value = "")

if st.button("Submit:"):
    if start_pos and end_pos:
        new_board, valid = move_piece(st.session_state.board, start_pos, end_pos)
        if valid:
            st.session_state.board = new_board
            st.session_state.turn = "b" if st.session_state.turn == "w" else "w"
            st.rerun()
    else:
        st.error("Please enter both start and end positions")
