import streamlit as st
from frontend.utils.api import api_request
from datetime import datetime
from frontend.utils.logger import get_frontend_logger

# Initialize logger
logger = get_frontend_logger(__name__)

def memory_page():
    """Display detailed memory sessions page"""
    logger.info("Displaying memory sessions page")
    st.markdown('<h1 class="main-header">🧠 Memory Sessions</h1>', unsafe_allow_html=True)
    
    try:
        # Fetch all chat sessions for the current user
        logger.info("Fetching memory sessions")
        sessions_response = api_request("GET", "/memory/sessions")
        
        if not sessions_response:
            logger.info("No chat sessions found")
            st.info("No chat sessions found. Start a conversation to create memories!")
            return
        
        # Display sessions
        st.markdown("### 📚 Chat Sessions")
        
        for session in sessions_response:
            with st.expander(f"💬 {session.get('name', 'Unnamed Session')} - {session.get('created_at', 'Unknown')}", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Session ID:** {session.get('session_id', 'N/A')}")
                    st.markdown(f"**Created:** {session.get('created_at', 'Unknown')}")
                    st.markdown(f"**Last Updated:** {session.get('updated_at', 'Unknown')}")
                
                with col2:
                    if st.button("💬 Load to Chat", key=f"load_{session['session_id']}"):
                        # Load this session's history to current chat
                        logger.info(f"Loading session {session['session_id']} to chat")
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
                
                # Fetch and display recent messages for this session
                try:
                    history_response = api_request("GET", f"/memory/sessions/{session['session_id']}/history")
                    if history_response:
                        st.markdown("**Recent Messages:**")
                        for msg in history_response[-3:]:  # Show last 3 messages
                            role_icon = "👤" if msg['role'] == 'user' else "🤖"
                            timestamp = msg.get('timestamp', 'Unknown')
                            st.markdown(f"{role_icon} **{msg['role'].title()}** ({timestamp}): {msg['content'][:100]}{'...' if len(msg['content']) > 100 else ''}")
                    else:
                        st.info("No messages in this session")
                except Exception as e:
                    st.error(f"Error fetching session history: {str(e)}")
        
        # Search functionality
        st.markdown("---")
        st.markdown("### 🔍 Search Across All Sessions")
        
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            search_query = st.text_input("Search term", placeholder="Enter search term...")
        with col2:
            search_type = st.selectbox("Search type", ["fuzzy", "semantic"])
        with col3:
            search_button = st.button("🔍 Search", use_container_width=True)
        
        if search_button and search_query:
            logger.info(f"Searching for '{search_query}' using {search_type} search")
            st.markdown("### 🔍 Search Results")
            
            # Search in each session
            for session in sessions_response:
                try:
                    search_response = api_request("GET", f"/memory/sessions/{session['session_id']}/search", 
                                               params={"q": search_query, "type": search_type, "top_k": 5})
                    if search_response:
                        logger.info(f"Found {len(search_response)} results in session {session['session_id']}")
                        st.markdown(f"**Results in session: {session.get('name', 'Unnamed')}**")
                        for msg in search_response:
                            role_icon = "👤" if msg['role'] == 'user' else "🤖"
                            timestamp = msg.get('timestamp', 'Unknown')
                            st.markdown(f"{role_icon} **{msg['role'].title()}** ({timestamp}): {msg['content']}")
                        st.markdown("---")
                    else:
                        logger.info(f"No search results found in session {session['session_id']}")
                except Exception as e:
                    logger.error(f"Error searching session {session['session_id']}: {str(e)}")
                    st.error(f"Error searching session {session['session_id']}: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error fetching memories: {str(e)}")
        st.error(f"Error fetching memories: {str(e)}")
        st.info("Make sure the backend is running and accessible.")
    
    # Back button
    if st.button("← Back to Chat", use_container_width=True):
        logger.info("User returning to main chat")
        st.switch_page("main.py")
