import streamlit as st
import requests
import json
import uuid
from datetime import datetime
import time
from typing import Dict, List, Any
import os

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
STREAMLIT_CONFIG = {
    "page_title": "Student LMS AI - Learning Assistant",
    "page_icon": "🎓",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Initialize session state
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

def check_authentication():
    """Check if user is still authenticated and restore session if needed"""
    if st.session_state.user_token:
        # Verify token is still valid by making a test API call
        try:
            response = api_request("GET", "/auth/me")
            if "id" in response:
                st.session_state.authenticated = True
                st.session_state.user_info = response
                return True
            else:
                # Token is invalid, clear session
                st.session_state.authenticated = False
                st.session_state.user_token = None
                st.session_state.user_info = None
                return False
        except:
            # API call failed, clear session
            st.session_state.authenticated = False
            st.session_state.user_token = None
            st.session_state.user_info = None
            return False
    return False

def configure_page():
    """Configure Streamlit page settings"""
    st.set_page_config(**STREAMLIT_CONFIG)
    st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 2rem;
        }
        .chat-message {
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            display: flex;
            align-items: flex-start;
        }
        .chat-message.user {
            background-color: #e3f2fd;
            border-left: 4px solid #2196f3;
        }
        .chat-message.assistant {
            background-color: #f3e5f5;
            border-left: 4px solid #9c27b0;
        }
        .sidebar-section {
            margin-bottom: 2rem;
        }
        .error-message {
            color: #d32f2f;
            background-color: #ffebee;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        .success-message {
            color: #2e7d32;
            background-color: #e8f5e8;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        </style>
    """, unsafe_allow_html=True)

def api_request(method: str, endpoint: str, data: Dict = None, headers: Dict = None, params: Dict = None, is_form: bool = False) -> Dict:
    """Make API request to backend"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        
        if headers is None:
            headers = {}
        
        if st.session_state.user_token:
            headers["Authorization"] = f"Bearer {st.session_state.user_token}"
        
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=30)
        elif method.upper() == "POST":
            if is_form:
                # For form data (like login), send as form-encoded
                response = requests.post(url, headers=headers, data=data, timeout=30)
            else:
                # For JSON data, send as JSON
                response = requests.post(url, headers=headers, json=data, timeout=30)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=30)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, timeout=30)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        
        if response.status_code == 204:  # No content
            return {"success": True}
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                st.error(f"Response details: {error_detail}")
            except:
                st.error(f"Response text: {e.response.text}")
        return {"error": str(e)}
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return {"error": str(e)}

def login_page():
    """Display login page"""
    st.markdown('<h1 class="main-header">🎓 Student LMS AI</h1>', unsafe_allow_html=True)
    st.markdown("### Welcome to your AI-powered Learning Assistant!")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("---")
        
        # Login form
        with st.form("login_form"):
            st.markdown("#### 🔐 Login")
            email = st.text_input("Email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            col1, col2 = st.columns(2)
            with col1:
                login_button = st.form_submit_button("Login", use_container_width=True)
            with col2:
                signup_button = st.form_submit_button("Sign Up", use_container_width=True)
        
        if login_button:
            if email and password:
                # Attempt login - backend expects OAuth2 form data
                login_data = {
                    "username": email,  # OAuth2PasswordRequestForm expects 'username' field
                    "password": password
                }
                
                # Use form data for login endpoint (OAuth2PasswordRequestForm format)
                response = api_request("POST", "/auth/login", data=login_data, is_form=True)
                
                if "access_token" in response:
                    st.session_state.user_token = response["access_token"]
                    st.session_state.authenticated = True
                    
                    # Get user info
                    user_response = api_request("GET", "/auth/me")
                    if "id" in user_response:
                        st.session_state.user_info = user_response
                        st.success("Login successful! Redirecting...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to get user information")
                else:
                    st.error("Login failed. Please check your credentials.")
            else:
                st.error("Please enter both email and password.")
        
        if signup_button:
            if email and password:
                # Attempt signup
                signup_data = {
                    "email": email,
                    "password": password,
                    "name": email.split("@")[0],  # Use email prefix as name
                    "phone": "",
                    "city": "",
                    "country": ""
                }
                
                response = api_request("POST", "/auth/signup", data=signup_data)
                
                if "id" in response:
                    st.success("Account created successfully! Please login.")
                else:
                    st.error(f"Signup failed: {response.get('detail', 'Unknown error')}")
            else:
                st.error("Please enter both email and password.")
        
        st.markdown("---")
        st.markdown("""
        **Demo Credentials:**
        - Email: `user1@example.com`
        - Password: `password123`
        """)

def sidebar():
    """Display sidebar with navigation and user info - Chat Only"""
    with st.sidebar:
        st.markdown("## 🧭 Navigation")
        
        if st.session_state.authenticated and st.session_state.user_info:
            user = st.session_state.user_info
            st.markdown(f"**👤 {user.get('name', 'User')}**")
            st.markdown(f"**📧 {user.get('email', '')}**")
            
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.user_token = None
                st.session_state.user_info = None
                st.session_state.chat_history = []
                st.session_state.current_memory_session = None
                st.rerun()
        
        st.markdown("---")
        
        # Quick Actions
        st.markdown("### ⚡ Quick Actions")
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.current_memory_session = None
            st.rerun()
        
        if st.button("🆕 New Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.current_memory_session = None
            st.rerun()
        
        # Show memory count
        if st.session_state.authenticated:
            try:
                sessions_response = api_request("GET", "/memory/sessions")
                memory_count = len(sessions_response) if sessions_response else 0
                st.markdown(f"*📊 {memory_count} total memories*")
                
                # Show current session info if active
                if hasattr(st.session_state, 'current_memory_session') and st.session_state.current_memory_session is not None:
                    current_session = next((s for s in sessions_response if s['session_id'] == st.session_state.current_memory_session), None)
                    if current_session:
                        session_name = current_session.get('name', 'Unnamed Session')
                        st.markdown(f"*💾 Active: {session_name[:15]}{'...' if len(session_name) > 15 else ''}*")
            except:
                st.markdown("*📊 Could not load memory count*")
        
        st.markdown("---")
        
        # Chat & Conversations
        st.markdown("### 💬 Chat & Conversations")
        if st.button("🤖 Current Chat", use_container_width=True):
            st.session_state.current_memory_session = None
            st.rerun()
        
        if st.button("🆕 New Conversation", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.current_memory_session = None
            st.rerun()
        
        st.markdown("---")
        
        # System Info
        st.markdown("### ℹ️ System Info")
        st.markdown(f"**API:** {API_BASE_URL}")
        st.markdown(f"**Status:** {'🟢 Connected' if st.session_state.authenticated else '🔴 Disconnected'}")

        st.markdown("---")
        
        # Recent Conversations
        if st.session_state.authenticated:
            st.markdown("### 🕒 Recent Conversations")
            try:
                sessions_response = api_request("GET", "/memory/sessions")
                if sessions_response and len(sessions_response) > 0:
                    # Show last 3 sessions
                    recent_sessions = sessions_response[-3:]
                    for session in reversed(recent_sessions):
                        session_name = session.get('name', 'Unnamed Session')
                        session_date = session.get('created_at', 'Unknown')
                        if isinstance(session_date, str) and len(session_date) > 10:
                            session_date = session_date[:10]  # Show just the date part
                        
                        if st.button(f"💬 {session_name[:20]}{'...' if len(session_name) > 20 else ''} ({session_date})", 
                                   key=f"recent_{session['session_id']}", use_container_width=True):
                            st.session_state.current_memory_session = session['session_id']
                            st.rerun()
                else:
                    st.markdown("*No recent conversations*")
            except:
                st.markdown("*Could not load recent conversations*")
        
        st.markdown("---")

def chat_interface():
    """Display main chat interface"""
    st.markdown('<h1 class="main-header">🤖 AI Learning Assistant</h1>', unsafe_allow_html=True)
    
    # Display current memory session info
    if hasattr(st.session_state, 'current_memory_session') and st.session_state.current_memory_session is not None:
        try:
            # Try to get session details to show the name
            sessions_response = api_request("GET", "/memory/sessions")
            current_session = next((s for s in sessions_response if s['session_id'] == st.session_state.current_memory_session), None)
            session_name = current_session.get('name', 'Unnamed Session') if current_session else 'Unknown Session'
            
            # Get message count for current session
            try:
                history_response = api_request("GET", f"/memory/sessions/{st.session_state.current_memory_session}/history")
                message_count = len(history_response) if history_response else 0
                st.info(f"💾 **Current Memory Session:** {session_name} ({st.session_state.current_memory_session[:8]}...) - 📝 {message_count} messages")
            except:
                st.info(f"💾 **Current Memory Session:** {session_name} ({st.session_state.current_memory_session[:8]}...)")
        except:
            st.info(f"💾 **Current Memory Session:** {st.session_state.current_memory_session[:8]}...")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🆕 Start New Session", use_container_width=True):
                st.session_state.current_memory_session = None
                st.rerun()
        with col2:
            if st.button("💾 Save & Continue", use_container_width=True):
                st.success("Session saved! Continue chatting to add more messages.")
    else:
        # No active session - show option to start one
        st.info("💾 **No active memory session** - Start chatting to create a new session")
        if st.button("🆕 Start New Session", use_container_width=True):
            try:
                session_response = api_request("POST", "/memory/sessions", data={"name": f"Chat Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"})
                if session_response and 'session_id' in session_response:
                    st.session_state.current_memory_session = session_response['session_id']
                    st.rerun()
                else:
                    st.warning("Could not create memory session")
            except Exception as e:
                st.warning(f"Could not create memory session: {str(e)}")
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Display chat history
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user">
                    <strong>👤 You:</strong> {message["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant">
                    <strong>🤖 Assistant:</strong> {message["content"]}
                </div>
                """, unsafe_allow_html=True)
    
    # Chat input
    st.markdown("---")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        user_input = st.text_input("💬 Ask me anything about learning or get help:", 
                                  placeholder="e.g., 'Help me with math' or 'Give me study tips'")
    with col2:
        send_button = st.button("🚀 Send", use_container_width=True)
    
    # Quick action buttons
    st.markdown("### 💡 Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("❓ Get Help", use_container_width=True):
            user_input = "What can you help me with?"
            send_button = True
    
    with col2:
        if st.button("📚 Learning Topics", use_container_width=True):
            user_input = "What learning topics can you help me with?"
            send_button = True
    
    with col3:
        if st.button("💡 Study Tips", use_container_width=True):
            user_input = "Give me some study tips"
            send_button = True
    
    # Handle chat
    if send_button and user_input:
        # Create or get memory session if not exists
        if not hasattr(st.session_state, 'current_memory_session') or st.session_state.current_memory_session is None:
            try:
                session_response = api_request("POST", "/memory/sessions", data={"name": f"Chat Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"})
                if session_response and 'session_id' in session_response:
                    st.session_state.current_memory_session = session_response['session_id']
                else:
                    st.warning("Could not create memory session, but chat will continue")
            except Exception as e:
                st.warning(f"Could not create memory session: {str(e)}")
        
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now()
        })
        
        # Store user message in memory if session exists and is not None
        if hasattr(st.session_state, 'current_memory_session') and st.session_state.current_memory_session is not None:
            try:
                api_request("POST", f"/memory/sessions/{st.session_state.current_memory_session}/messages", 
                           data={"role": "user", "content": user_input})
            except Exception as e:
                st.warning(f"Could not store message in memory: {str(e)}")
        
        # Send to API
        chat_data = {
            "prompt": user_input,
            "details": {
                "session_id": str(uuid.uuid4()),
                "topic": "learning_assistance"
            }
        }
        
        with st.spinner("🤖 Thinking..."):
            response = api_request("POST", "/agent/chat", data=chat_data)
        
        if "result" in response and "message" in response["result"]:
            assistant_message = response["result"]["message"]
            
            # Add assistant response to history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": assistant_message,
                "timestamp": datetime.now()
            })
            
            # Store assistant message in memory if session exists and is not None
            if hasattr(st.session_state, 'current_memory_session') and st.session_state.current_memory_session is not None:
                try:
                    api_request("POST", f"/memory/sessions/{st.session_state.current_memory_session}/messages", 
                               data={"role": "assistant", "content": assistant_message})
                except Exception as e:
                    st.warning(f"Could not store assistant message in memory: {str(e)}")
            
            st.rerun()
        else:
            st.error("Failed to get response from AI assistant")

def main():
    """Main application function - Chat Only"""
    configure_page()
    
    # Check and restore authentication if token exists
    if st.session_state.user_token and not st.session_state.authenticated:
        check_authentication()
    
    # Check authentication
    if not st.session_state.authenticated:
        login_page()
        return
    
    # Display sidebar
    sidebar()
    
    # Main content area - Only chat functionality
    chat_interface()

if __name__ == "__main__":
    main()
