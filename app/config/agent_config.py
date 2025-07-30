"""
Centralized agent configuration settings
"""

from typing import Dict, Any

# Agent Configuration Settings
AGENT_CONFIG = {
    "tutor": {
        "temperature": 0.7,
        "max_tokens": 1000,
        "role": "coordinator"
    },
    "subject_expert": {
        "temperature": 0.7,
        "max_tokens": 1000,
        "role": "content_expert"
    },
    "exercise_designer": {
        "temperature": 0.8,
        "max_tokens": 1000,
        "role": "exercise_creator"
    },
    "evaluator": {
        "temperature": 0.6,
        "max_tokens": 1000,
        "role": "assessor"
    },
    "learning_coach": {
        "temperature": 0.8,
        "max_tokens": 1000,
        "role": "motivator"
    },
    "visual_learning_specialist": {
        "temperature": 0.7,
        "max_tokens": 1000,
        "role": "visual_creator"
    }
}

# Intent Classification Settings
INTENT_CLASSIFICATION_CONFIG = {
    "temperature": 0.3,
    "max_tokens": 512,
    "json_mode": True
}

# Activity Extraction Settings
ACTIVITY_EXTRACTION_CONFIG = {
    "temperature": 0.1,
    "max_tokens": 512,
    "json_mode": True
}

# Chat Completion Settings
CHAT_COMPLETION_CONFIG = {
    "default_temperature": 0.7,
    "default_max_tokens": 512,
    "json_mode": False
}

# Multi-Agent System Settings
MULTI_AGENT_CONFIG = {
    "max_concurrent_agents": 6,
    "response_timeout": 30,
    "enable_caching": False,
    "cache_ttl": 3600
}

# Valid Intents
VALID_INTENTS = {
    "create-activity",
    "edit-activity", 
    "delete-activity",
    "list-activities",
    "start-activity",
    "generate-activity",
    "collaborative-learning",
    "single-agent-consultation",
    "greetings",
    "capabilities",
    "learning-support"
}

# Agent Selection Patterns
AGENT_SELECTION_PATTERNS = {
    "subject_specific": ["math", "science", "physics", "chemistry", "biology", "history", "literature", "language"],
    "exercise_requests": ["exercise", "practice", "quiz", "test", "problem", "question", "assignment"],
    "evaluation_requests": ["evaluate", "assess", "feedback", "grade", "review", "check"],
    "learning_strategy": ["how to study", "learning strategy", "study tips", "motivation", "confidence"],
    "visual_requests": ["diagram", "visual", "chart", "graph", "flowchart", "mind map", "visualize"],
    "complex_requests": ["comprehensive", "detailed", "thorough"]
}

# Response Templates
RESPONSE_TEMPLATES = {
    "error": "I'm sorry, I encountered an error while processing your request.",
    "unknown_intent": "Could not determine intent, please rephrase.",
    "no_response": "I'm sorry, I couldn't process your request properly.",
    "agent_error": "Error: Unable to get response from {agent_name}"
}

def get_agent_config(agent_name: str) -> Dict[str, Any]:
    """Get configuration for a specific agent"""
    return AGENT_CONFIG.get(agent_name, AGENT_CONFIG["tutor"])

def get_intent_classification_config() -> Dict[str, Any]:
    """Get intent classification configuration"""
    return INTENT_CLASSIFICATION_CONFIG

def get_activity_extraction_config() -> Dict[str, Any]:
    """Get activity extraction configuration"""
    return ACTIVITY_EXTRACTION_CONFIG

def get_chat_completion_config() -> Dict[str, Any]:
    """Get chat completion configuration"""
    return CHAT_COMPLETION_CONFIG

def get_multi_agent_config() -> Dict[str, Any]:
    """Get multi-agent system configuration"""
    return MULTI_AGENT_CONFIG

def is_valid_intent(intent: str) -> bool:
    """Check if intent is valid"""
    return intent in VALID_INTENTS

def get_agent_selection_patterns() -> Dict[str, list]:
    """Get agent selection patterns"""
    return AGENT_SELECTION_PATTERNS

def get_response_template(template_name: str, **kwargs) -> str:
    """Get response template with optional formatting"""
    template = RESPONSE_TEMPLATES.get(template_name, "")
    return template.format(**kwargs) if kwargs else template 