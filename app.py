import streamlit as st
import pandas as pd
from src.moves import move_piece, is_check, is_checkmate, is_stalemate, submit_move, promote_pawn
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


logger.info("Starting DFChess")

#Session State Initialization
if "board" not in st.session_state:
    st.session_state.board = create_board()
if "turn" not in st.session_state:
    st.session_state.turn = "w"
if "move_history" not in st.session_state:
    st.session_state.move_history = []
if "board_history" not in st.session_state:
    st.session_state.board_history = [st.session_state.board.copy(deep=True)]
if "game_status" not in st.session_state:
    st.session_state.game_status = "ongoing"
if "promotion_pending" not in st.session_state:
    st.session_state.promotion_pending = False
if "promotion_pos" not in st.session_state:
    st.session_state.promotion_pos = None

#Sidebar
st.sidebar.title("Game Options")

#Move History
move_hist_str = "\n".join([f"{move[0]} -> {move[1]}" for move in st.session_state.move_history])
st.sidebar.text_area("Move History", value = move_hist_str, height = 200)

#Undo Move
if st.sidebar.button("Undo Move"):
    if len(st.session_state.move_history) > 1:
        st.session_state.board_history.pop() #Remove the last board state
        st.session_state.board = st.session_state.board_history[-1].copy(deep=True)
        st.session_state.move_history.pop() #Remove the last move
        st.sidebar.success("Move undone!")
        st.rerun()
    else:
        st.sidebar.error("Cannot undo further")

#Reset Game
if st.sidebar.button("Reset Game"):
    st.session_state.board = create_board()
    st.session_state.turn = "w"
    st.session_state.move_history = []
    st.session_state.board_history = [st.session_state.board.copy(deep=True)]
    st.session_state.game_status = "ongoing"
    st.session_state.promotion_pending = False
    st.session_state.promotion_pos = None
    st.sidebar.success("Game Reset!")
    st.rerun()


#Game Mode Selection
st.sidebar.title("Game Mode")
game_mode = st.sidebar.radio("Select game mode", ["Player vs Player", "Player vs AI (Coming soon)"])

#Main Game
st.title("DFChess")

#Render the board
html_board = render_board(st.session_state.board)
st.components.v1.html(html_board, height= 610)

#Promotion UI
if st.session_state.promotion_pending:
    st.info("Promotion! Choose a piece:")
    col1, col2, col3, col4 = st.columns(4)

    if st.session_state.turn == "w":
        queen_img = images["wQ"]
        rook_img = images["wR"]
        bishop_img = images["wB"]
        knight_img = images["wN"]
    else:
        queen_img = images["bQ"]
        rook_img = images["bR"]
        bishop_img = images["bB"]
        knight_img = images["bN"]

    with col1:
        st.image(queen_img, width = 50)
        if st.button("Queen", key = "promo_q"):
            st.session_state.board = promote_pawn(
                st.session_state.board, st.session_state.promotion_pos, "Q"
            )
            st.session_state.promotion_pending = False
            st.rerun()
    with col2:
        st.image(rook_img, width = 50)
        if st.button("Rook", key = "promo_r"):
            st.session_state.board = promote_pawn(
                st.session_state.board, st.session_state.promotion_pos, "R"
            )
            st.session_state.promotion_pending = False
            st.rerun()
    with col3:
        st.image(bishop_img, width = 50)
        if st.button("Bishop", key = "promo_b"):
            st.session_state.board = promote_pawn(
                st.session_state.board, st.session_state.promotion_pos, "B"
            )
            st.session_state.promotion_pending = False
            st.rerun()
    with col4:
        st.image(knight_img, width = 50)
        if st.button("Knight", key = "promo_n"):
            st.session_state.board = promote_pawn(
                st.session_state.board, st.session_state.promotion_pos, "N"
            )
            st.session_state.promotion_pending = False
            st.rerun()
            
        

#Move Input
st.subheader(f"Move ({'White' if st.session_state.turn == 'w' else 'Black'})")
StartCol, EndCol = st.columns(2)
with StartCol:
    start_pos = st.text_input("Start Position (e.g. A2):", value = "")
with EndCol:
    end_pos = st.text_input("End Position (e.g. A4):", value = "")

if st.button("Submit:"):
    if start_pos and end_pos:
        submit_move(start_pos, end_pos)
    else:
        st.error("Please enter both start and end positions")
