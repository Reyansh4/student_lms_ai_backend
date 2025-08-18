import streamlit as st
from frontend.utils.config import STREAMLIT_CONFIG, CSS_STYLES
from frontend.utils.logger import get_frontend_logger
from frontend.components.auth import check_authentication, login_page
from frontend.components.navigation import vertical_sidebar, horizontal_top_bar
from frontend.components.chat import chat_interface

# Initialize logger
logger = get_frontend_logger(__name__)

def configure_page():
    """Configure Streamlit page settings"""
    logger.info("Configuring Streamlit page settings")
    st.set_page_config(**STREAMLIT_CONFIG)
    st.markdown(CSS_STYLES, unsafe_allow_html=True)
    logger.info("Page configuration completed")

def initialize_session_state():
    """Initialize session state variables"""
    logger.info("Initializing session state")
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_token' not in st.session_state:
        st.session_state.user_token = None
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'current_memory_session' not in st.session_state:
        st.session_state.current_memory_session = None
    
    # Clear invalid memory sessions
    if st.session_state.get('current_memory_session'):
        try:
            from frontend.utils.api import api_request
            test_response = api_request("GET", f"/memory/sessions/{st.session_state.current_memory_session}")
            if not test_response or 'error' in str(test_response) or 'Not Found' in str(test_response):
                logger.info(f"Clearing invalid memory session at startup: {st.session_state.current_memory_session}")
                st.session_state.current_memory_session = None
        except Exception as e:
            logger.info(f"Clearing invalid memory session at startup due to error: {str(e)}")
            st.session_state.current_memory_session = None
    
    logger.info("Session state initialized")

def main():
    """Main application function - Chat Only"""
    logger.info("Starting Student LMS AI Frontend application")
    
    # Configure page
    configure_page()
    
    # Initialize session state
    initialize_session_state()
    
    # Check and restore authentication if token exists
    if st.session_state.user_token and not st.session_state.authenticated:
        logger.info("Restoring authentication from existing token")
        check_authentication()
    
    # Check authentication
    if not st.session_state.authenticated:
        logger.info("User not authenticated, showing login page")
        login_page()
        return
    
    logger.info("User authenticated, displaying main interface")
    
    # Display vertical sidebar
    vertical_sidebar()
    
    # Display horizontal top bar
    horizontal_top_bar()
    
    # Main content area - Only chat functionality
    chat_interface()
    
    logger.info("Main interface displayed successfully")

if __name__ == "__main__":
    main()
