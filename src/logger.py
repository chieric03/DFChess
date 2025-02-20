import logging
import streamlit as st

class StreamlitLogger(logging.Handler):
    """
    Custom logging handler for Streamlit.
    """
    def __init__(self, session_state_key= "logs"):
        super().__init__()
        self.session_state_key = session_state_key

        if self.session_state_key not in st.session_state:
            st.session_state[self.session_state_key] = []

    def emit(self, record):
        """
        Emit a log record to Streamlit.
        """
        log_entry = self.format(record)
        st.session_state[self.session_state_key].append(log_entry)


logger = logging.getLogger("DFChess")
logger.setLevel(logging.DEBUG)

if logger.hasHandlers():
    logger.handlers.clear()

handler = StreamlitLogger()
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
