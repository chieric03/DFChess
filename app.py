import streamlit as st
import pandas as pd
import base64
from src.moves import move_piece, is_check, is_checkmate, is_stalemate, submit_move, promote_pawn
from src.board import create_board
from src.logger import logger
from src.ui import get_base64_image, images, interactive_board, render_board, show_two_boards_side_by_side
from src.AI_Opponent import evaluate_board, get_all_valid_moves

st.set_page_config(layout="wide")


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
if "last_error" not in st.session_state:
    st.session_state.last_error = None

if "game_mode" not in st.session_state:
    st.session_state.game_mode = "PvP"
if "player_side" not in st.session_state:
    st.session_state.player_side = "White"

if "castling_rights" not in st.session_state:
    st.session_state.castling_rights = {
        "wK": True,
        "wR_kingside": True,
        "wR_queenside": True,
        "bK": True,
        "bR_kingside": True,
        "bR_queenside": True
    }
if "en_passant_target" not in st.session_state:
    st.session_state.en_passant_target = None


#Sidebar
st.sidebar.title("Game Options")

#Move History
move_hist_str = "\n".join([f"{move[0]} -> {move[1]}" for move in st.session_state.move_history])
st.sidebar.text_area("Move History", value = move_hist_str, height = 200)

#Undo Move
if st.sidebar.button("Undo Move"):
    if len(st.session_state.board_history) > 1:
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
game_mode = st.sidebar.selectbox("Select Game Mode", ["PvP", "PvAI"])
st.session_state.game_mode = game_mode

if game_mode == "PvAI":
    player_side = st.sidebar.radio("Select Side", ["White", "Black"])
    st.session_state.player_side = player_side


#Main Game
st.title("DFChess")
st.subheader(f"Move ({'White' if st.session_state.turn == 'w' else 'Black'})")



#Render the board

show_two_boards_side_by_side()


#Error Message
#if st.session_state.get("last_error"):
#    st.error(st.session_state.last_error)
#    st.session_state.last_error = None

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

        
