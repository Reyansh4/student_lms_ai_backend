"""
Configuration package for the application
"""

from .settings import settings
from .azure_config import AzureConfig, load_azure_config
from .agent_config import (
    AGENT_CONFIG,
    INTENT_CLASSIFICATION_CONFIG,
    ACTIVITY_EXTRACTION_CONFIG,
    CHAT_COMPLETION_CONFIG,
    MULTI_AGENT_CONFIG,
    VALID_INTENTS,
    AGENT_SELECTION_PATTERNS,
    RESPONSE_TEMPLATES,
    get_agent_config,
    get_intent_classification_config,
    get_activity_extraction_config,
    get_chat_completion_config,
    get_multi_agent_config,
    is_valid_intent,
    get_agent_selection_patterns,
    get_response_template
)

__all__ = [
    # Main settings
    "settings",
    
    # Azure configuration
    "AzureConfig",
    "load_azure_config",
    
    # Agent configuration
    "AGENT_CONFIG",
    "INTENT_CLASSIFICATION_CONFIG",
    "ACTIVITY_EXTRACTION_CONFIG",
    "CHAT_COMPLETION_CONFIG",
    "MULTI_AGENT_CONFIG",
    "VALID_INTENTS",
    "AGENT_SELECTION_PATTERNS",
    "RESPONSE_TEMPLATES",
    "get_agent_config",
    "get_intent_classification_config",
    "get_activity_extraction_config",
    "get_chat_completion_config",
    "get_multi_agent_config",
    "is_valid_intent",
    "get_agent_selection_patterns",
    "get_response_template"
] 