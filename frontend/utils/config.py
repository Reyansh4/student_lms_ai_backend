"""
Configuration settings for the frontend application
"""

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

# Streamlit Page Configuration
STREAMLIT_CONFIG = {
    "page_title": "Student LMS AI",
    "page_icon": "🎓",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
    "menu_items": {
        "Get Help": "https://github.com/your-repo/issues",
        "Report a bug": "https://github.com/your-repo/issues",
        "About": "Student LMS AI - AI-powered Learning Management System"
    }
}

# CSS Styles
CSS_STYLES = """
<style>
/* Main Header - Removed large header */
.main-header {
    text-align: center;
    color: #1f77b4;
    margin-bottom: 1rem;
    font-size: 1.5rem;
    font-weight: bold;
}

/* Welcome Message */
.welcome-message-small {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 15px;
    text-align: center;
    margin: 2rem auto;
    max-width: 600px;
}

.welcome-message-small h4 {
    margin-bottom: 0.75rem;
    font-size: 1.2rem;
}

.welcome-message-small p {
    margin: 0.5rem 0;
    font-size: 0.9rem;
}

.welcome-message-small ul {
    text-align: left;
    display: inline-block;
    margin: 0.75rem 0;
    font-size: 0.85rem;
}

.welcome-message-small li {
    margin: 0.25rem 0;
}

/* Chat Messages - Full Width Horizontal Alignment */
.chat-message {
    padding: 1rem 1.5rem;
    margin: 1rem 0;
    border-radius: 20px;
    border: none;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    max-width: 70%;
    word-wrap: break-word;
    display: block;
    clear: both;
}

.chat-message.user {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    float: left;
    margin-left: 0;
    margin-right: auto;
    border-bottom-right-radius: 5px;
    text-align: left;
}

.chat-message.assistant {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
    float: right;
    margin-right: 0;
    margin-left: auto;
    border-bottom-left-radius: 5px;
    text-align: left;
}

.chat-message strong {
    font-size: 0.9rem;
    opacity: 0.9;
    margin-bottom: 0.5rem;
    display: block;
}

/* Clear float after messages */
.chat-message::after {
    content: "";
    display: table;
    clear: both;
}

/* Chat Input Area */
.stTextArea textarea {
    border-radius: 15px;
    border: 2px solid #e0e0e0;
    transition: all 0.3s ease;
    font-size: 1rem;
    padding: 1rem;
}

.stTextArea textarea:focus {
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    transform: translateY(-2px);
}

/* Send Button */
.stButton > button[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    border-radius: 15px;
    padding: 0.75rem 2rem;
    font-weight: 600;
    font-size: 1.1rem;
    transition: all 0.3s ease;
    margin-top: 1rem;
    position: relative;
    overflow: hidden;
}

.stButton > button[data-testid="baseButton-primary"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
}

.stButton > button[data-testid="baseButton-primary"]:active {
    transform: translateY(-1px);
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

/* Disabled Button State */
.stButton > button[disabled] {
    background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
    opacity: 0.7;
}

/* Loading Spinner Enhancements */
.stSpinner > div {
    border: 3px solid #f3f3f3;
    border-top: 3px solid #667eea;
    border-radius: 50%;
    width: 30px;
    height: 30px;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Success and Error Messages */
.stAlert[data-baseweb="notification"] {
    border-radius: 12px;
    border: none;
    font-weight: 500;
}

/* Info Message Styling */
.stAlert[data-baseweb="notification"] .stAlert {
    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
    color: #1565c0;
    border-left: 4px solid #2196f3;
}

/* Warning Message Styling */
.stAlert[data-baseweb="notification"] .stAlert[data-baseweb="notification"] {
    background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
    color: #ef6c00;
    border-left: 4px solid #ff9800;
}

/* Error Message Styling */
.stAlert[data-baseweb="notification"] .stAlert[data-baseweb="notification"] {
    background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
    color: #c62828;
    border-left: 4px solid #f44336;
}

/* Success Message Styling */
.stAlert[data-baseweb="notification"] .stAlert[data-baseweb="notification"] {
    background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
    color: #2e7d32;
    border-left: 4px solid #4caf50;
}

/* Quick Actions */
.stButton > button {
    border-radius: 12px;
    font-weight: 500;
    transition: all 0.3s ease;
    border: 2px solid #e0e0e0;
    background: white;
    color: #333;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    border-color: #667eea;
    background: #667eea;
    color: white;
}

/* Sidebar Styling */
.sidebar .sidebar-content {
    background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
}

/* Form Styling */
.stTextInput > div > div > input {
    border-radius: 12px;
    border: 2px solid #e0e0e0;
    transition: border-color 0.3s ease;
}

.stTextInput > div > div > input:focus {
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* Info Boxes */
.stAlert {
    border-radius: 12px;
    border: none;
}

/* Expander Styling */
.streamlit-expanderHeader {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border-radius: 12px;
    font-weight: 500;
}

/* Responsive Design */
@media (max-width: 768px) {
    .main-header {
        font-size: 1.3rem;
    }
    
    .chat-message {
        max-width: 90%;
        padding: 0.75rem 1rem;
    }
    
    .welcome-message-small {
        padding: 1rem;
        margin: 1rem auto;
        max-width: 90%;
    }
    
    .welcome-message-small h4 {
        font-size: 1.1rem;
    }
    
    .welcome-message-small ul {
        font-size: 0.8rem;
    }
    
    .chat-container-main {
        min-height: 70vh;
    }
    
    .chat-messages-scrollable {
        max-height: 50vh;
        min-height: 30vh;
        padding: 1rem;
    }
    
    .chat-input-fixed {
        padding: 1rem;
    }
}

/* Scrollbar Styling */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8;
}
</style>
"""
