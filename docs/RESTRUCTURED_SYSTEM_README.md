# Restructured Multi-Agent Learning System

## Overview

This is a completely restructured and reorganized multi-agent learning system with proper separation of concerns, centralized configuration, and functional tools. The system provides comprehensive learning support through specialized AI agents that collaborate to deliver personalized educational experiences.

## 🏗️ New Architecture

### Directory Structure

```
app/
├── agents/                    # Agent implementations
│   ├── __init__.py
│   ├── chat_agent.py         # Main chat agent with LangGraph
│   └── multi_agent_system.py # Multi-agent coordination
├── config/                   # Centralized configuration
│   ├── __init__.py
│   └── agent_config.py       # Agent settings and parameters
├── prompts/                  # Centralized prompts
│   ├── __init__.py
│   └── agent_prompts.py      # All agent prompts and templates
├── tools/                    # Functional tools
│   ├── __init__.py
│   └── agent_tools.py        # Core agent operations
├── core/                     # Core utilities (existing)
├── models/                   # Database models (existing)
├── routes/                   # API routes (existing)
├── services/                 # Business logic (existing)
└── utils/                    # Utilities (existing)
```

### Key Improvements

1. **Centralized Prompts** (`app/prompts/`)
   - All agent prompts in one place
   - Easy to modify and maintain
   - Consistent prompt engineering

2. **Centralized Configuration** (`app/config/`)
   - Agent temperature settings
   - Token limits and parameters
   - Intent classification patterns
   - Response templates

3. **Functional Tools** (`app/tools/`)
   - Reusable agent operations
   - Intent classification
   - Activity extraction
   - Agent response generation

4. **Clean Agent Implementation** (`app/agents/`)
   - Separated concerns
   - Modular design
   - Easy to extend

## 🔧 Configuration Management

### Agent Configuration

```python
# app/config/agent_config.py
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
    }
    # ... more agents
}
```

### Intent Classification Settings

```python
INTENT_CLASSIFICATION_CONFIG = {
    "temperature": 0.3,
    "max_tokens": 512,
    "json_mode": True
}
```

### Multi-Agent System Settings

```python
MULTI_AGENT_CONFIG = {
    "max_concurrent_agents": 6,
    "response_timeout": 30,
    "enable_caching": False,
    "cache_ttl": 3600
}
```

## 📝 Prompt Management

### Centralized Prompts

All prompts are now centralized in `app/prompts/agent_prompts.py`:

```python
# Lead Tutor System Prompt
LEAD_TUTOR_SYSTEM_PROMPT = """You are an expert lead tutor with deep knowledge across various subjects. 
You coordinate the learning experience, teach core concepts, and decide when to involve 
specialized agents for specific tasks..."""

# Intent Classification Prompt
INTENT_CLASSIFICATION_PROMPT = """Classify the user's intent into one of these categories:
- create-activity
- edit-activity
- collaborative-learning
- single-agent-consultation
..."""
```

### Response Templates

```python
# Capabilities Response
CAPABILITIES_RESPONSE = """I'm **Leena AI**, your comprehensive learning assistant! Here's what I can do:

**🎯 Learning Activities:**
- Create and manage educational activities
- Start existing activities (quizzes, lessons, assignments)
- Generate custom learning materials

**🤝 Multi-Agent Learning Support:**
- **Lead Tutor**: Coordinate comprehensive learning experiences
- **Subject Expert**: Deep knowledge in specific subjects
..."""
```

## 🛠️ Functional Tools

### Agent Tools Class

The `AgentTools` class provides all core functionality:

```python
# Intent Classification
result = await agent_tools.classify_intent("Help me learn calculus")

# Activity Extraction
details = await agent_tools.extract_activity_details("Start math quiz")

# Agent Response
response = await agent_tools.get_agent_response("subject_expert", "Explain quantum physics")

# Agent Selection
agents = agent_tools.determine_involved_agents("Help me understand calculus with practice problems")

# Response Combination
combined = agent_tools.combine_agent_responses(responses, original_input)
```

### Key Features

1. **Async Operations**: All tools are async for better performance
2. **Error Handling**: Comprehensive error handling with fallbacks
3. **Configuration Integration**: Uses centralized configuration
4. **Prompt Integration**: Uses centralized prompts
5. **Logging**: Detailed logging for debugging

## 🤖 Agent Implementation

### Multi-Agent System

```python
# Collaborative Learning Session
result = await multi_agent_system.collaborative_learning_session(
    "Help me understand calculus derivatives with examples and practice problems"
)

# Single Agent Consultation
result = await multi_agent_system.single_agent_consultation(
    "subject_expert", 
    "What are the key principles of thermodynamics?"
)

# Learning Support
result = await multi_agent_system.process_learning_request(
    "I need help studying for my biology exam"
)
```

### Chat Agent

The chat agent uses LangGraph for workflow management:

```python
# Run the agent
result = await run_agent({
    "prompt": "Help me learn calculus",
    "details": {"token": "user_jwt_token"},
    "user_id": "user_123",
    "db": database_session
})
```

## 🧪 Testing

### Test Structure

```python
# Test agent tools
await agent_tools.classify_intent("Help me learn calculus")

# Test multi-agent system
await multi_agent_system.collaborative_learning_session("Explain photosynthesis")

# Test chat agent
await run_agent(test_input)
```

### Running Tests

```bash
# Test restructured system
python test_restructured_system.py

# Test original system (for comparison)
python test_multi_agent.py
```

## 🔄 Migration Guide

### From Old to New Structure

1. **Update Imports**:
   ```python
   # Old
   from app.agent.chat import run_agent
   
   # New
   from app.agents.chat_agent import run_agent
   ```

2. **Configuration Access**:
   ```python
   # Old
   temperature = 0.7
   
   # New
   from app.config.agent_config import get_agent_config
   config = get_agent_config("tutor")
   temperature = config["temperature"]
   ```

3. **Prompt Access**:
   ```python
   # Old
   system_prompt = "You are an expert tutor..."
   
   # New
   from app.prompts.agent_prompts import LEAD_TUTOR_SYSTEM_PROMPT
   system_prompt = LEAD_TUTOR_SYSTEM_PROMPT
   ```

## 📊 Performance Improvements

1. **Concurrent Agent Execution**: Multiple agents run concurrently
2. **Timeout Management**: Configurable timeouts for agent responses
3. **Caching Support**: Framework for response caching (future)
4. **Async/Await**: All operations are async for better performance

## 🔧 Configuration Options

### Agent Settings

```python
# Temperature and token settings per agent
AGENT_CONFIG = {
    "tutor": {"temperature": 0.7, "max_tokens": 1000},
    "subject_expert": {"temperature": 0.7, "max_tokens": 1000},
    "exercise_designer": {"temperature": 0.8, "max_tokens": 1000},
    "evaluator": {"temperature": 0.6, "max_tokens": 1000},
    "learning_coach": {"temperature": 0.8, "max_tokens": 1000},
    "visual_learning_specialist": {"temperature": 0.7, "max_tokens": 1000}
}
```

### Intent Classification Patterns

```python
AGENT_SELECTION_PATTERNS = {
    "subject_specific": ["math", "science", "physics", "chemistry", "biology"],
    "exercise_requests": ["exercise", "practice", "quiz", "test", "problem"],
    "evaluation_requests": ["evaluate", "assess", "feedback", "grade"],
    "learning_strategy": ["how to study", "learning strategy", "study tips"],
    "visual_requests": ["diagram", "visual", "chart", "graph", "flowchart"],
    "complex_requests": ["comprehensive", "detailed", "thorough"]
}
```

## 🚀 Usage Examples

### Basic Usage

```python
from app.agents.chat_agent import run_agent

# Simple chat
result = await run_agent({
    "prompt": "Hello!",
    "details": {"token": "user_token"},
    "user_id": "user_123",
    "db": None
})
```

### Advanced Usage

```python
from app.agents.multi_agent_system import multi_agent_system

# Collaborative learning
result = await multi_agent_system.collaborative_learning_session(
    "Help me understand quantum physics with examples and diagrams"
)

# Single agent consultation
result = await multi_agent_system.single_agent_consultation(
    "subject_expert",
    "Explain the principles of thermodynamics"
)
```

### Tool Usage

```python
from app.tools.agent_tools import agent_tools

# Intent classification
intent = await agent_tools.classify_intent("Help me learn calculus")

# Activity extraction
details = await agent_tools.extract_activity_details("Start math quiz")

# Agent response
response = await agent_tools.get_agent_response("tutor", "Explain derivatives")
```

## 🔍 Monitoring and Debugging

### Logging

The system includes comprehensive logging:

```python
logger.debug(f"=== CLASSIFY_INTENT START ===")
logger.debug(f"Input state: {state}")
logger.debug(f"Final intent: {intent}")
logger.debug(f"=== CLASSIFY_INTENT SUCCESS ===")
```

### Error Handling

```python
try:
    result = await agent_tools.classify_intent(user_input)
except Exception as e:
    logger.error(f"Intent classification failed: {e}")
    return {"intent": "unknown", "confidence": 0.0}
```

## 🔮 Future Enhancements

1. **Response Caching**: Implement caching for faster responses
2. **Agent Memory**: Persistent agent-specific knowledge
3. **Learning Analytics**: Track student progress across agents
4. **Dynamic Agent Creation**: On-demand specialized agents
5. **Multi-modal Support**: Image, audio, and video processing
6. **Personalization**: Adaptive agent behavior based on student profile

## 📋 Maintenance

### Adding New Agents

1. Add agent configuration to `app/config/agent_config.py`
2. Add agent prompt to `app/prompts/agent_prompts.py`
3. Add agent system prompt to `AgentTools._get_agent_system_prompt()`
4. Update agent selection patterns in `app/config/agent_config.py`
5. Add tests to `test_restructured_system.py`

### Modifying Prompts

1. Edit prompts in `app/prompts/agent_prompts.py`
2. Test with `test_restructured_system.py`
3. Update documentation if needed

### Changing Configuration

1. Modify settings in `app/config/agent_config.py`
2. Test configuration with `test_restructured_system.py`
3. Update this README if needed

## ✅ Benefits of Restructuring

1. **Maintainability**: Centralized prompts and configuration
2. **Testability**: Modular design with clear interfaces
3. **Extensibility**: Easy to add new agents and features
4. **Performance**: Async operations and concurrent execution
5. **Debugging**: Comprehensive logging and error handling
6. **Documentation**: Clear structure and examples

## 🎯 Key Features

- ✅ Centralized prompt management
- ✅ Centralized configuration
- ✅ Functional tools architecture
- ✅ Async/await throughout
- ✅ Comprehensive error handling
- ✅ Detailed logging
- ✅ Easy testing
- ✅ Modular design
- ✅ Backward compatibility
- ✅ Performance optimizations

This restructured system provides a solid foundation for a scalable, maintainable, and extensible multi-agent learning platform. 