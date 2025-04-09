import streamlit as st
import pandas as pd
import base64
from src.moves import move_piece, is_check, is_checkmate, is_stalemate, submit_move, promote_pawn
from src.board import create_board
from src.logger import logger
from src.ui import get_base64_image, images, interactive_board, render_board, show_two_boards_side_by_side
# Removed unused imports: evaluate_board, get_all_valid_moves from AI_Opponent

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
if "game_started" not in st.session_state:
    st.session_state.game_started = False # Flag to track if PvAI game is active

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

#Reset Game - Also reset game_started flag
if st.sidebar.button("Reset Game"):
    st.session_state.board = create_board()
    st.session_state.turn = "w"
    st.session_state.move_history = []
    st.session_state.board_history = [st.session_state.board.copy(deep=True)]
    st.session_state.game_status = "ongoing"
    st.session_state.promotion_pending = False
    st.session_state.promotion_pos = None
    st.session_state.game_started = False # Reset flag
    st.session_state.ai_move_triggered_init = False # Reset initial AI move flag
    st.sidebar.success("Game Reset!")
    st.rerun()



#Game Mode Selection & Start Button
st.sidebar.title("Game Mode")

# Determine if widgets should be disabled (game started or not PvP)
disable_widgets = st.session_state.game_started and st.session_state.game_mode == "PvAI"

game_mode = st.sidebar.selectbox(
    "Select Game Mode", 
    ["PvP", "PvAI"], 
    index=["PvP", "PvAI"].index(st.session_state.game_mode), # Set current value
    disabled=disable_widgets 
)
# Update game mode only if changed and game not started
if game_mode != st.session_state.game_mode and not disable_widgets:
    st.session_state.game_mode = game_mode
    # Reset relevant states if mode changes? Maybe not needed if reset button is used.
    st.rerun() 

# PvAI specific options
if st.session_state.game_mode == "PvAI":
    player_side = st.sidebar.radio(
        "Select Side", 
        ["White", "Black"], 
        index=["White", "Black"].index(st.session_state.player_side), # Set current value
        disabled=disable_widgets
    )
    # Update player side only if changed and game not started
    if player_side != st.session_state.player_side and not disable_widgets:
         st.session_state.player_side = player_side
         st.rerun()

    # Show "Start Game" button only if PvAI mode is selected AND game hasn't started
    if not st.session_state.game_started:
        if st.sidebar.button("Start PvAI Game"):
            st.session_state.game_started = True
            st.session_state.ai_move_triggered_init = False # Ensure initial AI move flag is reset
            st.sidebar.success(f"PvAI Game Started! You are playing as {st.session_state.player_side}.")
            
            # --- Trigger initial AI move *after* Start Game is pressed if player chose Black ---
            if st.session_state.player_side == "Black" and st.session_state.turn == "w":
                st.session_state.ai_move_triggered_init = True # Set flag
                from src.moves import _handle_post_move_updates 
                # Need to ensure _handle_post_move_updates doesn't change turn back immediately
                # Let's modify _handle_post_move_updates slightly or call AI directly?
                # Calling _handle_post_move_updates might be okay if it handles the turn correctly.
                # Let's try calling it first.
                _handle_post_move_updates() 
                # No explicit rerun here, _handle_post_move_updates should handle it.
            else:
                 st.rerun() # Rerun to disable widgets even if AI doesn't move first
        
# --- Remove the old initial AI move trigger location ---
# if "ai_move_triggered_init" not in st.session_state:
#     st.session_state.ai_move_triggered_init = False 

# if st.session_state.game_mode == "PvAI" and \
#    st.session_state.player_side == "Black" and \
#    st.session_state.turn == "w" and \
#    not st.session_state.ai_move_triggered_init:
#     st.session_state.ai_move_triggered_init = True 
#     from src.moves import _handle_post_move_updates 
#     _handle_post_move_updates() 

#Main Game
st.title("DFChess")
st.subheader(f"Move ({'White' if st.session_state.turn == 'w' else 'Black'})")



#Render the board - Only allow input if game started or PvP
if st.session_state.game_mode == "PvP" or st.session_state.game_started:
    show_two_boards_side_by_side()
else:
    # Display board statically if PvAI game hasn't started
    st.subheader("Board")
    html_board = render_board(st.session_state.board)
    st.components.v1.html(html_board, height=610)
    st.info("Select your side and click 'Start PvAI Game' in the sidebar.")


#Error Message Display (Consider moving this inside the conditional rendering)
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
