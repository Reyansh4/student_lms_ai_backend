import streamlit as st
from frontend.utils.api import api_request
from frontend.utils.logger import get_frontend_logger
from datetime import datetime

# Initialize logger
logger = get_frontend_logger(__name__)

def vertical_sidebar():
    """Display simplified vertical sidebar with navigation"""
    logger.debug("Displaying vertical sidebar")
    with st.sidebar:
        st.markdown("## 🧭 Navigation")
        
        if st.session_state.authenticated and st.session_state.user_info:
            user = st.session_state.user_info
            st.markdown(f"**👤 {user.get('name', 'User')}**")
            st.markdown(f"**📧 {user.get('email', '')}**")
            
            if st.button("🚪 Logout", use_container_width=True):
                logger.info(f"User {user.get('email', '')} logged out")
                st.session_state.authenticated = False
                st.session_state.user_token = None
                st.session_state.user_info = None
                st.session_state.chat_history = []
                st.rerun()
        
        st.markdown("---")
        
        # New Chat Section
        st.markdown("### 🆕 New Chat")
        if st.button("🆕 Start New Chat", use_container_width=True):
            logger.info("User started new chat")
            st.session_state.chat_history = []
            st.session_state.current_memory_session = None
            st.rerun()
        
        st.markdown("---")
        
        # Memory Sessions Section
        st.markdown("### 🧠 Memory Sessions")
        if st.button("📋 View All Memories", use_container_width=True):
            st.switch_page("pages/memory.py")
        
        if st.session_state.authenticated:
            try:
                sessions_response = api_request("GET", "/memory/sessions")
                if sessions_response and len(sessions_response) > 0:
                    # Show last 5 sessions
                    recent_sessions = sessions_response[-5:]
                    for session in reversed(recent_sessions):
                        session_name = session.get('name', 'Unnamed Session')
                        session_date = session.get('created_at', 'Unknown')
                        if isinstance(session_date, str) and len(session_date) > 10:
                            session_date = session_date[:10]  # Show just the date part
                        
                        if st.button(f"💬 {session_name[:20]}{'...' if len(session_name) > 20 else ''} ({session_date})",
                                   key=f"recent_{session['session_id']}", use_container_width=True):
                            try:
                                history_response = api_request("GET", f"/memory/sessions/{session['session_id']}/history")
                                if history_response:
                                    st.session_state.chat_history = []
                                    for msg in history_response:
                                        st.session_state.chat_history.append({
                                            "role": msg['role'],
                                            "content": msg['content'],
                                            "timestamp": msg.get('timestamp', datetime.now())
                                        })
                                    # Set the current memory session
                                    st.session_state.current_memory_session = session['session_id']
                                    logger.info(f"Successfully loaded {len(history_response)} messages from session {session['session_id']}")
                                    st.success(f"Loaded {len(history_response)} messages from session!")
                                    st.rerun()
                                else:
                                    logger.warning(f"No messages to load from session {session['session_id']}")
                                    st.warning("No messages to load from this session")
                            except Exception as e:
                                logger.error(f"Error loading session {session['session_id']}: {str(e)}")
                                st.error(f"Error loading session: {str(e)}")
                else:
                    st.markdown("*No recent conversations*")
            except Exception as e:
                st.markdown("*Could not load recent conversations*")
        
        st.markdown("---")
        
        # System Info
        st.markdown("### ℹ️ System Info")
        from frontend.utils.config import API_BASE_URL
        st.markdown(f"**API:** {API_BASE_URL}")
        st.markdown(f"**Status:** {'🟢 Connected' if st.session_state.authenticated else '🔴 Disconnected'}")

def horizontal_top_bar():
    """Display horizontal top bar with quick actions"""
    logger.debug("Displaying horizontal top bar")
    
    # Quick Actions at the very top - fully horizontal
    st.markdown("## 🚀 Quick Actions")
    
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    
    with col1:
        if st.button("📚 My Activities", key="activities_btn", use_container_width=True):
            logger.info("User clicked 'My Activities' quick action")
            st.session_state.quick_action = "activities"
            st.rerun()
    
    with col2:
        if st.button("🧠 Memory", key="memory_btn", use_container_width=True):
            logger.info("User clicked 'Memory' quick action")
            st.switch_page("pages/memory.py")
    
    with col3:
        if st.button("❓ Get Help", key="help_btn", use_container_width=True):
            logger.info("User clicked 'Get Help' quick action")
            st.session_state.quick_action = "help"
            st.rerun()
    
    with col4:
        if st.button("👤 Profile", key="profile_btn", use_container_width=True):
            logger.info("User clicked 'Profile' quick action")
            st.session_state.quick_action = "profile"
            st.rerun()
    
    with col5:
        if st.session_state.authenticated and st.session_state.user_info:
            user = st.session_state.user_info
            if st.button(f"🚪 Logout ({user.get('name', 'User')[:10]})", key="logout_btn", use_container_width=True):
                logger.info(f"User {user.get('email', '')} logged out")
                st.session_state.authenticated = False
                st.session_state.user_token = None
                st.session_state.user_info = None
                st.session_state.chat_history = []
                st.session_state.current_memory_session = None
                st.rerun()
        else:
            if st.button("🔐 Login", key="login_btn", use_container_width=True):
                logger.info("User clicked 'Login' quick action")
                st.session_state.authenticated = False
                st.rerun()
    
    st.markdown("---")
    
    # Handle quick actions
    if hasattr(st.session_state, 'quick_action'):
        action = st.session_state.quick_action
        logger.info(f"Handling quick action: {action}")
        if action == "help":
            st.session_state.chat_input = "What can you help me with?"
            st.session_state.quick_action = None
        elif action == "activities":
            st.session_state.chat_input = "Show me my learning activities and progress"
            st.session_state.quick_action = None
        elif action == "profile":
            st.session_state.chat_input = "Show me my profile and learning statistics"
            st.session_state.quick_action = None
