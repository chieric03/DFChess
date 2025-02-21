import streamlit as st
import pandas as pd
from src.moves import move_piece, is_check, is_checkmate, is_stalemate, submit_move, promote_pawn
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

"""
def interactive_board():

    Displays the current board as an interactive one,
    When a cell is clicked, it sets the selected cell. The next cell clicked will be the destination cell.
    
    board = st.session_state.board
    selected = st.session_state.get("selected", None)

    for i in range(8):
        col = st.columns(8)
        for j in range(8):
            cell_value = board.iat[i,j]
            label = cell_value if cell_value != "." else ""
            if selected == (i,j):
                label = f"[{label}]"

            if col[j].button(label, key=f"cell_{i}_{j}"):
                if selected is None: #marking first selected sell
                    st.session_state.selected = (i,j)
                else: #if same selected cell is selected then deselect
                    if selected == {i,j}:
                        st.session_state.selected = None
                    else: #Destination click
                        start = st.session_state.selected
                        end = (i,j)
                        st.session_state.selected = None
                        submit_move_with_index(start, end)
                        st.rerun()
"""

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

def interactive_board():
    """
    Displays an 8×8 grid of Streamlit buttons with row/column labels on the left/right
    and top/bottom. Clicking a square either selects it or, if one is selected, submits a move.
    """
    board = st.session_state.board
    selected = st.session_state.get("selected_square", None)

    col_labels = [chr(ord('A') + c) for c in range(8)]  # A–H
    row_labels = [str(8 - r) for r in range(8)]         # 8..1

    # Top row: corner + A–H + corner
    top_row = st.columns(10)
    top_row[0].write("")
    for c in range(8):
        top_row[c+1].write(f"**{col_labels[c]}**")
    top_row[9].write("")

    # Main board rows
    for i in range(8):
        row_cols = st.columns(10)
        # Left label
        row_cols[0].write(f"**{row_labels[i]}**")

        for j in range(8):
            piece = board.iat[i, j]
            label = piece if piece != "." else " "
            if selected == (i, j):
                label = f"[{label}]"
            if row_cols[j+1].button(label, key=f"cell_{i}_{j}"):
                if selected is None:
                    st.session_state.selected_square = (i, j)
                    st.rerun()
                else:
                    if selected == (i, j):
                        st.session_state.selected_square = None
                        st.rerun()
                    else:
                        start_idx = selected
                        end_idx = (i, j)
                        st.session_state.selected_square = None
                        submit_move_with_index(start_idx, end_idx)
                        st.rerun()

        # Right label
        row_cols[9].write(f"**{row_labels[i]}**")

    # Bottom row: corner + A–H + corner
    bottom_row = st.columns(10)
    bottom_row[0].write("")
    for c in range(8):
        bottom_row[c+1].write(f"**{col_labels[c]}**")
    bottom_row[9].write("")


def show_two_boards_side_by_side():
    col1, col2 = st.columns([3,2])

    # Board 1 (HTML images + text input) in col1
    with col1:
        st.subheader("")
        html_board = render_board(st.session_state.board)
        st.components.v1.html(html_board, height=610)

        # Text input for moves
        if st.session_state.get("last_error"):
            st.error(st.session_state.last_error)
            st.session_state.last_error = None
        start_move = st.text_input("Start Position (e.g. E2):", value="")
        end_move = st.text_input("End Position (e.g. E4):", value="")
        if st.button("Submit Move (Text Input)", key="text_move"):
            if start_move and end_move:
                submit_move(start_move, end_move)  # Your existing text-based move function
            else:
                st.session_state.last_error = "Please enter both start and end positions."

    # Board 2 (interactive text-based grid) in col2
    with col2:
        st.subheader("Interactive Board")
        # Inject custom CSS for square buttons in the interactive board container
        st.markdown(
            """
            <style>
            .interactive-board-container div.stButton > button {
                width: 60px;
                height: 60px;
                min-width: 60px !important;
                min-height: 60px !important;
                padding: 0px;
                font-size: 1em;
                line-height: 60px;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        # Wrap the interactive board in a div with the custom class.
        st.markdown('<div class="interactive-board-container">', unsafe_allow_html=True)
        interactive_board()
        st.markdown('</div>', unsafe_allow_html=True)



def submit_move_with_index(start_index, end_index):
    """
    Moves the piece from start_index to end_index
    """
    updated_board, valid = move_piece(st.session_state.board, start_index, end_index)
    if not valid:
        return
    
    st.session_state.board = updated_board
    st.session_state.move_history.append((start_index, end_index))
    st.session_state.board_history.append(updated_board.copy(deep = True))

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
        st.warning("Pawn promotion pending!")
        st.rerun()
        return
    
    #Change turn
    new_turn = "b" if st.session_state.turn == "w" else "w"

    #Check for check
    if is_check(st.session_state.board, new_turn):
        st.warning(f"Check! {'White' if new_turn == 'b' else 'Black'} is in check!")
        if is_checkmate(st.session_state.board, new_turn):
            st.session_state.last_error =f"Checkmate! {'White' if new_turn == 'b' else 'Black'} wins!"
            st.session_state.game_status = "game_over"
            return
        elif is_stalemate(st.session_state.board, new_turn):
            st.session_state.last_error ="Stalemate! It's a draw!"
            st.session_state.game_status = "game_over"
            return
        
    st.session_state.turn = new_turn
    st.rerun()
