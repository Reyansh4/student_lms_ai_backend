import streamlit as st
import uuid
import time
from datetime import datetime
from frontend.utils.api import api_request
from frontend.utils.logger import get_frontend_logger
from frontend.utils.langfuse import (
    track_chat_message, track_memory, track_api, track_error, 
    track_performance, set_chat_session, set_user_context
)

# Initialize logger
logger = get_frontend_logger(__name__)

def chat_interface():
    """Display improved chat interface with scrollable messages and fixed input"""
    logger.info("Displaying chat interface")
    
    # Set user context for tracking if available
    if st.session_state.get('user_info') and st.session_state.get('user_info', {}).get('id'):
        user_id = str(st.session_state.user_info['id'])
        session_id = str(st.session_state.get('current_memory_session', 'frontend_session'))
        set_user_context(user_id, session_id)
    
    # Clear invalid memory sessions at startup
    if st.session_state.get('current_memory_session'):
        try:
            # Test if the session still exists
            test_response = api_request("GET", f"/memory/sessions/{st.session_state.current_memory_session}")
            if not test_response or 'error' in str(test_response) or 'Not Found' in str(test_response):
                logger.info(f"Clearing invalid memory session: {st.session_state.current_memory_session}")
                st.session_state.current_memory_session = None
                track_error("memory_session_invalid", f"Session {st.session_state.current_memory_session} not found")
        except Exception as e:
            logger.info(f"Clearing invalid memory session due to error: {str(e)}")
            st.session_state.current_memory_session = None
            track_error("memory_session_error", str(e))
    
    # Single chat container using Streamlit's native container system
    with st.container():
        # Apply custom CSS to this container
        st.markdown("""
        <style>
        .stContainer {
            min-height: 80vh;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 20px;
            border: 2px solid #dee2e6;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            padding: 2rem;
            margin: 1rem 0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Add Start New Chat button at the top
        if st.button("🆕 Start New Chat", use_container_width=True, type="secondary", key="new_chat_btn"):
            logger.info("User started new chat")
            track_user_action("start_new_chat", {"previous_history_length": len(st.session_state.get('chat_history', []))})
            st.session_state.chat_history = []
            st.session_state.current_memory_session = None
            st.rerun()
        
        # Debug section (only show in development)
        with st.expander("🔧 Debug Info (Click to expand)"):
            st.write("**Current Session State:**")
            st.write(f"- Current Memory Session: {st.session_state.get('current_memory_session', 'None')}")
            st.write(f"- Chat History Length: {len(st.session_state.get('chat_history', []))}")
            st.write(f"- Authenticated: {st.session_state.get('authenticated', False)}")
            
            # Show Langfuse tracking summary
            from frontend.utils.langfuse import get_tracking_summary
            tracking_summary = get_tracking_summary()
            st.write("**Langfuse Tracking:**")
            st.write(f"- Total Interactions: {tracking_summary.get('total_interactions', 0)}")
            st.write(f"- User ID: {tracking_summary.get('user_id', 'None')}")
            st.write(f"- Session ID: {tracking_summary.get('session_id', 'None')}")
            
            if st.button("🔄 Reset All Sessions", key="reset_sessions"):
                logger.info("User reset all sessions")
                track_user_action("reset_all_sessions", {"chat_history_length": len(st.session_state.get('chat_history', []))})
                st.session_state.chat_history = []
                st.session_state.current_memory_session = None
                st.rerun()
        
        # Chat messages area - scrollable
        if st.session_state.chat_history:
            # Show chat history with full width horizontal alignment
            for i, message in enumerate(st.session_state.chat_history):
                if message["role"] == "user":
                    # User message on the LEFT side - full width
                    st.markdown(f"""
                    <div class="chat-message user">
                        <strong>👤 You:</strong><br>
                        {message["content"]}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Assistant message on the RIGHT side - full width
                    st.markdown(f"""
                    <div class="chat-message assistant">
                        <strong>🤖 Assistant:</strong><br>
                        {message["content"]}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            # Small welcome message when no chat history (centered)
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown("""
                <div class="welcome-message-small">
                    <h4>🎓 Welcome to your AI Learning Assistant!</h4>
                    <p>I'm here to help you with:</p>
                    <ul>
                        <li>📚 Learning new topics</li>
                        <li>💡 Study tips and strategies</li>
                        <li>❓ Answering questions</li>
                        <li>🔍 Finding learning resources</li>
                        <li>📝 Homework help</li>
                    </ul>
                    <p><strong>Just ask me anything below!</strong></p>
                </div>
                """, unsafe_allow_html=True)
        
        # Separator line
        st.markdown("---")
        
        # Fixed input area at the bottom of the same container
        # Large input area
        col1, col2, col3 = st.columns([1, 4, 1])
        
        with col2:
            # Use session state for chat input if quick action was triggered
            if hasattr(st.session_state, 'chat_input') and st.session_state.chat_input:
                user_input = st.text_area(
                    "💬 Ask me anything about learning or get help:", 
                    value=st.session_state.chat_input,
                    placeholder="e.g., 'Help me with math' or 'Give me study tips'",
                    height=100,
                    key="chat_input_area"
                )
                # Clear the chat input after using it
                st.session_state.chat_input = None
            else:
                user_input = st.text_area(
                    "💬 Ask me anything about learning or get help:", 
                    placeholder="e.g., 'Help me with math' or 'Give me study tips'",
                    height=100,
                    key="chat_input_area"
                )
            
            # Send button below input
            if st.button("🚀 Send Message", use_container_width=True, type="primary", key="send_button"):
                if user_input and user_input.strip():
                    # Track chat message
                    track_chat_message("user_input", user_input.strip())
                    
                    # Show loading state
                    with st.spinner("🤖 Thinking..."):
                        # Disable the button during processing
                        st.button("⏳ Processing...", use_container_width=True, disabled=True, key="processing_button")
                        
                        start_time = time.time()
                        
                        # Check if we have an existing memory session, if not create one
                        current_session_id = None
                        if not st.session_state.get('current_memory_session'):
                            try:
                                session_response = api_request("POST", "/memory/sessions", data={"name": f"Chat Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"})
                                if session_response and 'session_id' in session_response:
                                    current_session_id = session_response['session_id']
                                    st.session_state.current_memory_session = current_session_id
                                    logger.info(f"Created new memory session: {current_session_id}")
                                    
                                    # Track memory session creation
                                    track_memory("create_session", current_session_id, True, {"name": f"Chat Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"})
                                    set_chat_session(current_session_id)
                                else:
                                    logger.warning("Could not create memory session")
                                    track_memory("create_session", "unknown", False, {"error": "No session_id in response"})
                            except Exception as e:
                                logger.warning(f"Could not create memory session: {str(e)}")
                                track_memory("create_session", "unknown", False, {"error": str(e)})
                        else:
                            current_session_id = st.session_state.current_memory_session
                            logger.info(f"Using existing memory session: {current_session_id}")
                            
                            # Verify the session still exists by trying to access it
                            try:
                                test_response = api_request("GET", f"/memory/sessions/{current_session_id}")
                                if not test_response or 'error' in str(test_response):
                                    logger.warning(f"Memory session {current_session_id} no longer exists, creating new one")
                                    st.session_state.current_memory_session = None
                                    current_session_id = None
                                    track_memory("session_verification", current_session_id, False, {"error": "Session no longer exists"})
                                    
                                    # Create new session
                                    session_response = api_request("POST", "/memory/sessions", data={"name": f"Chat Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"})
                                    if session_response and 'session_id' in session_response:
                                        current_session_id = session_response['session_id']
                                        st.session_state.current_memory_session = current_session_id
                                        logger.info(f"Created new memory session after verification: {current_session_id}")
                                        track_memory("create_session", current_session_id, True, {"reason": "verification_failed"})
                                        set_chat_session(current_session_id)
                            except Exception as e:
                                logger.warning(f"Could not verify memory session: {str(e)}, creating new one")
                                st.session_state.current_memory_session = None
                                current_session_id = None
                                track_memory("session_verification", current_session_id, False, {"error": str(e)})
                                
                                # Create new session
                                try:
                                    session_response = api_request("POST", "/memory/sessions", data={"name": f"Chat Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"})
                                    if session_response and 'session_id' in session_response:
                                        current_session_id = session_response['session_id']
                                        st.session_state.current_memory_session = current_session_id
                                        logger.info(f"Created new memory session after verification error: {current_session_id}")
                                        track_memory("create_session", current_session_id, True, {"reason": "verification_error"})
                                        set_chat_session(current_session_id)
                                except Exception as e2:
                                    logger.error(f"Failed to create new session after verification: {str(e2)}")
                                    track_memory("create_session", "unknown", False, {"error": str(e2)})
                        
                        # Add user message to history
                        st.session_state.chat_history.append({
                            "role": "user",
                            "content": user_input.strip(),
                            "timestamp": datetime.now()
                        })
                        
                        # Store user message in memory if session exists
                        if current_session_id:
                            try:
                                api_request("POST", f"/memory/sessions/{current_session_id}/messages", 
                                           data={"role": "user", "content": user_input.strip()})
                                track_memory("store_message", current_session_id, True, {"role": "user", "content_length": len(user_input.strip())})
                            except Exception as e:
                                logger.warning(f"Could not store message in memory: {str(e)}")
                                track_memory("store_message", current_session_id, False, {"error": str(e)})
                                
                                # If session doesn't exist, create a new one
                                if "Session not found" in str(e) or "404" in str(e):
                                    logger.info("Session not found, creating new session")
                                    track_memory("session_recreation", current_session_id, False, {"reason": "message_store_failed"})
                                    
                                    try:
                                        session_response = api_request("POST", "/memory/sessions", data={"name": f"Chat Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"})
                                        if session_response and 'session_id' in session_response:
                                            current_session_id = session_response['session_id']
                                            st.session_state.current_memory_session = current_session_id
                                            logger.info(f"Created new memory session after error: {current_session_id}")
                                            track_memory("create_session", current_session_id, True, {"reason": "message_store_failed"})
                                            set_chat_session(current_session_id)
                                            
                                            # Try to store message again
                                            api_request("POST", f"/memory/sessions/{current_session_id}/messages", 
                                                       data={"role": "user", "content": user_input.strip()})
                                            track_memory("store_message", current_session_id, True, {"role": "user", "content_length": len(user_input.strip())})
                                    except Exception as e2:
                                        logger.error(f"Failed to create new session: {str(e2)}")
                                        track_memory("create_session", "unknown", False, {"error": str(e2)})
                        
                        # Prepare conversation history for agent context
                        conversation_history = []
                        if current_session_id:
                            try:
                                # Get conversation history from memory
                                history_response = api_request("GET", f"/memory/sessions/{current_session_id}/history")
                                if history_response and not isinstance(history_response, dict) or 'error' not in str(history_response):
                                    conversation_history = history_response
                                    logger.info(f"Loaded {len(conversation_history)} messages from memory for agent context")
                                    logger.info(f"Conversation history details: {conversation_history}")
                                    track_memory("get_history", current_session_id, True, {"message_count": len(conversation_history)})
                                else:
                                    logger.warning("No conversation history found or error in response")
                                    track_memory("get_history", current_session_id, False, {"error": "Invalid response format"})
                            except Exception as e:
                                logger.warning(f"Could not load conversation history: {str(e)}")
                                track_memory("get_history", current_session_id, False, {"error": str(e)})
                                
                                # If session doesn't exist, use local chat history instead
                                if "Session not found" in str(e) or "404" in str(e):
                                    logger.info("Using local chat history instead of memory")
                                    conversation_history = st.session_state.chat_history[:-1]  # Exclude current message
                        
                        # If we still don't have conversation history, use local chat history
                        if not conversation_history:
                            logger.info("Using local chat history as fallback")
                            conversation_history = st.session_state.chat_history[:-1]  # Exclude current message
                        
                        # Ensure conversation history is properly formatted
                        if conversation_history and isinstance(conversation_history, list):
                            # Filter out any error objects or invalid messages
                            clean_conversation_history = []
                            for msg in conversation_history:
                                if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                                    clean_conversation_history.append(msg)
                                elif isinstance(msg, str):
                                    # Handle string messages as user messages
                                    clean_conversation_history.append({
                                        "role": "user",
                                        "content": msg
                                    })
                            conversation_history = clean_conversation_history
                            logger.info(f"Cleaned conversation history: {len(clean_conversation_history)} valid messages")
                        else:
                            conversation_history = []
                            logger.info("No valid conversation history available")
                        
                        # Send to API with conversation context
                        chat_data = {
                            "prompt": user_input.strip(),
                            "details": {
                                "session_id": current_session_id or str(uuid.uuid4()),
                                "topic": "learning_assistance",
                                "conversation_history": conversation_history  # Pass conversation context
                            }
                        }
                        
                        logger.info(f"Sending chat data to agent: {chat_data}")
                        
                        # Show API processing spinner
                        with st.spinner("📡 Sending to AI..."):
                            api_start_time = time.time()
                            response = api_request("POST", "/agent/chat", data=chat_data)
                            api_response_time = time.time() - api_start_time
                            
                            # Track API performance
                            track_api("POST", "/agent/chat", True, api_response_time)
                        
                        # Debug the response structure
                        logger.info(f"API Response: {response}")
                        
                        # Handle different response structures
                        assistant_message = None
                        if "result" in response and "result" in response["result"] and "message" in response["result"]["result"]:
                            # Handle nested structure: response["result"]["result"]["message"]
                            assistant_message = response["result"]["result"]["message"]
                        elif "result" in response and "message" in response["result"]:
                            # Handle structure: response["result"]["message"]
                            assistant_message = response["result"]["message"]
                        elif "message" in response:
                            # Handle structure: response["message"]
                            assistant_message = response["message"]
                        elif "response" in response:
                            # Handle structure: response["response"]
                            assistant_message = response["response"]
                        elif "content" in response:
                            # Handle structure: response["content"]
                            assistant_message = response["content"]
                        elif "text" in response:
                            # Handle structure: response["text"]
                            assistant_message = response["text"]
                        elif isinstance(response, str):
                            # Handle direct string responses
                            assistant_message = response
                        
                        if assistant_message:
                            # Track successful response
                            track_chat_message("assistant_response", assistant_message[:100], metadata={"response_length": len(assistant_message)})
                            
                            # Show success message
                            st.success("✅ Response received!")
                            
                            # Add assistant response to history
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": assistant_message,
                                "timestamp": datetime.now()
                            })
                            
                            # Store assistant message in memory if session exists
                            if current_session_id:
                                try:
                                    api_request("POST", f"/memory/sessions/{current_session_id}/messages", 
                                               data={"role": "assistant", "content": assistant_message})
                                    track_memory("store_message", current_session_id, True, {"role": "assistant", "content_length": len(assistant_message)})
                                except Exception as e:
                                    logger.warning(f"Could not store assistant message in memory: {str(e)}")
                                    track_memory("store_message", current_session_id, False, {"error": str(e)})
                                    
                                    # If session doesn't exist, try to create a new one
                                    if "Session not found" in str(e) or "404" in str(e):
                                        logger.info("Session not found for assistant message, creating new session")
                                        track_memory("session_recreation", current_session_id, False, {"reason": "assistant_message_store_failed"})
                                        
                                        try:
                                            session_response = api_request("POST", "/memory/sessions", data={"name": f"Chat Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"})
                                            if session_response and 'session_id' in session_response:
                                                current_session_id = session_response['session_id']
                                                st.session_state.current_memory_session = current_session_id
                                                logger.info(f"Created new memory session for assistant: {current_session_id}")
                                                track_memory("create_session", current_session_id, True, {"reason": "assistant_message_store_failed"})
                                                set_chat_session(current_session_id)
                                                
                                                # Try to store message again
                                                api_request("POST", f"/memory/sessions/{current_session_id}/messages", 
                                                           data={"role": "assistant", "content": assistant_message})
                                                track_memory("store_message", current_session_id, True, {"role": "assistant", "content_length": len(assistant_message)})
                                        except Exception as e2:
                                            logger.error(f"Failed to create new session for assistant: {str(e2)}")
                                            track_memory("create_session", "unknown", False, {"error": str(e2)})
                            
                            # Track total processing time
                            total_time = time.time() - start_time
                            track_performance("chat_completion", total_time, {
                                "user_input_length": len(user_input.strip()),
                                "assistant_response_length": len(assistant_message),
                                "conversation_history_length": len(conversation_history),
                                "api_response_time": api_response_time
                            })
                            
                            # Small delay to show success message
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            # Track failed response
                            track_error("ai_response_failed", f"Failed to get response from AI assistant. Response: {response}")
                            st.error(f"❌ Failed to get response from AI assistant. Response: {response}")
                else:
                    st.warning("⚠️ Please enter a message before sending.")
            
            # Add Enter key support
            if user_input and user_input.strip():
                st.info("💡 Press Enter or click Send Message to send your message!")
