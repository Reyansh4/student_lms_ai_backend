import streamlit as st
import requests
from typing import Dict, Any
from frontend.utils.logger import get_frontend_logger

# Initialize logger
logger = get_frontend_logger(__name__)

def api_request(method: str, endpoint: str, data: Dict = None, headers: Dict = None, params: Dict = None, is_form: bool = False) -> Dict:
    """Make API request to backend"""
    from frontend.utils.config import API_BASE_URL
    
    url = f"{API_BASE_URL}{endpoint}"
    logger.info(f"API {method.upper()} request to: {endpoint}")
    
    try:
        if headers is None:
            headers = {}
        
        if st.session_state.user_token:
            headers["Authorization"] = f"Bearer {st.session_state.user_token}"
            logger.debug(f"Request with auth token: {st.session_state.user_token[:20]}...")
        
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
        logger.info(f"API {method.upper()} request successful: {response.status_code}")
        
        if response.status_code == 204:  # No content
            return {"success": True}
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API {method.upper()} request failed: {str(e)}")
        st.error(f"API request failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                logger.error(f"API error response: {error_detail}")
                st.error(f"Response details: {error_detail}")
            except:
                logger.error(f"API error response text: {e.response.text}")
                st.error(f"Response text: {e.response.text}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in API request: {str(e)}")
        st.error(f"Unexpected error: {str(e)}")
        return {"error": str(e)}
