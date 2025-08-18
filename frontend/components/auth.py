import streamlit as st
import time
from frontend.utils.api import api_request
from frontend.utils.logger import get_frontend_logger

# Initialize logger
logger = get_frontend_logger(__name__)

def check_authentication():
    """Check if user is still authenticated and restore session if needed"""
    logger.info("Checking user authentication")
    if st.session_state.user_token:
        # Verify token is still valid by making a test API call
        try:
            response = api_request("GET", "/auth/me")
            if "id" in response:
                st.session_state.authenticated = True
                st.session_state.user_info = response
                logger.info("Authentication restored successfully")
                return True
            else:
                # Token is invalid, clear session
                st.session_state.authenticated = False
                st.session_state.user_token = None
                st.session_state.user_info = None
                logger.warning("Authentication failed - no user ID in response")
                return False
        except Exception as e:
            # API call failed, clear session
            st.session_state.authenticated = False
            st.session_state.user_token = None
            st.session_state.user_info = None
            logger.error(f"Authentication check failed: {str(e)}")
            return False
    logger.info("No user token found")
    return False

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
                logger.info(f"Login attempt for email: {email}")
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
                    logger.info(f"Login successful for user: {email}")
                    
                    # Get user info
                    user_response = api_request("GET", "/auth/me")
                    if "id" in user_response:
                        st.session_state.user_info = user_response
                        st.success("Login successful! Redirecting...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        logger.error("Failed to get user information after login")
                        st.error("Failed to get user information")
                else:
                    logger.warning(f"Login failed for email: {email}")
                    st.error("Login failed. Please check your credentials.")
            else:
                logger.warning("Login attempt with missing credentials")
                st.error("Please enter both email and password.")
        
        if signup_button:
            if email and password:
                logger.info(f"Signup attempt for email: {email}")
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
                    logger.info(f"Signup successful for user: {email}")
                    st.success("Account created successfully! Please login.")
                else:
                    logger.error(f"Signup failed for email: {email} - {response.get('detail', 'Unknown error')}")
                    st.error(f"Signup failed: {response.get('detail', 'Unknown error')}")
            else:
                logger.warning("Signup attempt with missing credentials")
                st.error("Please enter both email and password.")
        
        st.markdown("---")
        st.markdown("""
        **Demo Credentials:**
        - Email: `user1@example.com`
        - Password: `password123`
        """)
