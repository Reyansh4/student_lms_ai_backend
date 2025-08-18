"""
Frontend Langfuse utilities for tracking user interactions and frontend operations
"""
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime

# Initialize logger
logger = logging.getLogger(__name__)

class FrontendLangfuseTracker:
    """Frontend-specific Langfuse tracking for user interactions"""
    
    def __init__(self):
        self.enabled = self._check_langfuse_config()
        self.user_id = None
        self.session_id = None
        self.chat_session_id = None
        
        if self.enabled:
            logger.info("✅ Frontend Langfuse tracking enabled")
        else:
            logger.warning("⚠️ Frontend Langfuse tracking disabled")
    
    def _check_langfuse_config(self) -> bool:
        """Check if Langfuse is configured for frontend"""
        # Check if we're in a browser environment
        try:
            # This will work in Streamlit/React but not in pure Python
            import streamlit as st
            return True
        except ImportError:
            return False
    
    def set_user_context(self, user_id: str, session_id: str):
        """Set user context for tracking"""
        self.user_id = user_id
        self.session_id = session_id
        logger.info(f"Set user context: {user_id}, session: {session_id}")
    
    def set_chat_session(self, chat_session_id: str):
        """Set current chat session for tracking"""
        self.chat_session_id = chat_session_id
        logger.info(f"Set chat session: {chat_session_id}")
    
    def track_user_interaction(self, action: str, details: Dict[str, Any], 
                             success: bool = True, error_message: Optional[str] = None):
        """Track user interactions"""
        if not self.enabled:
            return
        
        try:
            import streamlit as st
            
            # Create interaction data
            interaction_data = {
                "action": action,
                "details": details,
                "success": success,
                "error_message": error_message,
                "user_id": self.user_id,
                "session_id": self.session_id,
                "chat_session_id": self.chat_session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "user_agent": "streamlit_frontend"
            }
            
            # Store in session state for backend processing
            if 'langfuse_interactions' not in st.session_state:
                st.session_state.langfuse_interactions = []
            
            st.session_state.langfuse_interactions.append(interaction_data)
            
            # Log the interaction
            if success:
                logger.info(f"Tracked user interaction: {action}")
            else:
                logger.warning(f"Tracked failed user interaction: {action} - {error_message}")
                
        except Exception as e:
            logger.error(f"Failed to track user interaction: {str(e)}")
    
    def track_chat_message(self, message_type: str, content: str, 
                          message_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """Track chat messages"""
        self.track_user_interaction(
            action="chat_message",
            details={
                "message_type": message_type,
                "content_length": len(content),
                "message_id": message_id,
                "metadata": metadata or {}
            }
        )
    
    def track_navigation(self, page: str, action: str, metadata: Optional[Dict[str, Any]] = None):
        """Track navigation actions"""
        self.track_user_interaction(
            action="navigation",
            details={
                "page": page,
                "action": action,
                "metadata": metadata or {}
            }
        )
    
    def track_authentication(self, action: str, success: bool, user_id: Optional[str] = None, 
                           error_message: Optional[str] = None):
        """Track authentication actions"""
        if user_id:
            self.set_user_context(user_id, str(datetime.utcnow().timestamp()))
        
        self.track_user_interaction(
            action=f"auth_{action}",
            details={"user_id": user_id},
            success=success,
            error_message=error_message
        )
    
    def track_memory_operation(self, operation: str, session_id: str, 
                             success: bool, metadata: Optional[Dict[str, Any]] = None):
        """Track memory operations"""
        self.track_user_interaction(
            action=f"memory_{operation}",
            details={
                "session_id": session_id,
                "metadata": metadata or {}
            },
            success=success
        )
    
    def track_api_request(self, endpoint: str, method: str, success: bool, 
                         response_time: Optional[float] = None, error_message: Optional[str] = None):
        """Track API requests"""
        self.track_user_interaction(
            action="api_request",
            details={
                "endpoint": endpoint,
                "method": method,
                "response_time": response_time,
                "error_message": error_message
            },
            success=success,
            error_message=error_message
        )
    
    def track_error(self, error_type: str, error_message: str, 
                   context: Optional[Dict[str, Any]] = None):
        """Track errors"""
        self.track_user_interaction(
            action="error",
            details={
                "error_type": error_type,
                "context": context or {}
            },
            success=False,
            error_message=error_message
        )
    
    def track_performance(self, operation: str, duration: float, 
                         metadata: Optional[Dict[str, Any]] = None):
        """Track performance metrics"""
        self.track_user_interaction(
            action="performance",
            details={
                "operation": operation,
                "duration": duration,
                "metadata": metadata or {}
            }
        )
    
    def get_tracking_summary(self) -> Dict[str, Any]:
        """Get summary of tracked interactions"""
        try:
            import streamlit as st
            
            if 'langfuse_interactions' not in st.session_state:
                return {"total_interactions": 0, "interactions": []}
            
            interactions = st.session_state.langfuse_interactions
            return {
                "total_interactions": len(interactions),
                "interactions": interactions[-10:],  # Last 10 interactions
                "user_id": self.user_id,
                "session_id": self.session_id,
                "chat_session_id": self.chat_session_id
            }
            
        except Exception as e:
            logger.error(f"Failed to get tracking summary: {str(e)}")
            return {"error": str(e)}
    
    def clear_tracking_data(self):
        """Clear tracked interactions"""
        try:
            import streamlit as st
            
            if 'langfuse_interactions' in st.session_state:
                del st.session_state.langfuse_interactions
            
            logger.info("Cleared tracking data")
            
        except Exception as e:
            logger.error(f"Failed to clear tracking data: {str(e)}")

# Global frontend tracker instance
frontend_tracker = FrontendLangfuseTracker()

# Utility functions for easy tracking
def track_user_action(action: str, details: Dict[str, Any], **kwargs):
    """Track a user action"""
    frontend_tracker.track_user_interaction(action, details, **kwargs)

def track_chat_message(message_type: str, content: str, **kwargs):
    """Track a chat message"""
    frontend_tracker.track_chat_message(message_type, content, **kwargs)

def track_navigation(page: str, action: str, **kwargs):
    """Track navigation"""
    frontend_tracker.track_navigation(page, action, **kwargs)

def track_auth(action: str, success: bool, **kwargs):
    """Track authentication"""
    frontend_tracker.track_authentication(action, success, **kwargs)

def track_memory(operation: str, session_id: str, **kwargs):
    """Track memory operation"""
    frontend_tracker.track_memory_operation(operation, session_id, **kwargs)

def track_api(endpoint: str, method: str, **kwargs):
    """Track API request"""
    frontend_tracker.track_api_request(endpoint, method, **kwargs)

def track_error(error_type: str, error_message: str, **kwargs):
    """Track error"""
    frontend_tracker.track_error(error_type, error_message, **kwargs)

def track_performance(operation: str, duration: float, **kwargs):
    """Track performance"""
    frontend_tracker.track_performance(operation, duration, **kwargs)

def set_user_context(user_id: str, session_id: str):
    """Set user context"""
    frontend_tracker.set_user_context(user_id, session_id)

def set_chat_session(chat_session_id: str):
    """Set chat session"""
    frontend_tracker.set_chat_session(chat_session_id)

def get_tracking_summary():
    """Get tracking summary"""
    return frontend_tracker.get_tracking_summary()

def clear_tracking():
    """Clear tracking data"""
    frontend_tracker.clear_tracking_data()
