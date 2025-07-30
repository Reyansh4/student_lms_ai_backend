# Multi-Agent Learning System

## Overview

This implementation integrates a sophisticated multi-agent system with the existing LangGraph-based chat agent. The system provides comprehensive learning support through specialized AI agents that collaborate to deliver personalized educational experiences.

## Architecture

### Core Components

1. **MultiAgentSystem** (`app/agent/multi_agent_system.py`)
   - Manages specialized learning agents
   - Coordinates collaborative learning sessions
   - Handles single-agent consultations

2. **Enhanced Chat Agent** (`app/agent/chat.py`)
   - Improved intent classification
   - New routing for multi-agent capabilities
   - Integration with existing activity management

### Specialized Agents

#### 1. Lead Tutor (`tutor`)
- **Role**: Primary coordinator and learning guide
- **Capabilities**: 
  - Understands student learning needs
  - Breaks down complex topics
  - Coordinates with other specialists
  - Provides structured explanations

#### 2. Subject Expert (`subject_expert`)
- **Role**: Deep domain knowledge specialist
- **Capabilities**:
  - In-depth subject knowledge
  - Clear concept explanations
  - Real-world examples
  - Cross-topic connections

#### 3. Exercise Designer (`exercise_designer`)
- **Role**: Educational activity creator
- **Capabilities**:
  - Creates engaging practice activities
  - Designs varied question types
  - Matches learning levels
  - Considers different learning styles

#### 4. Learning Evaluator (`evaluator`)
- **Role**: Assessment and feedback specialist
- **Capabilities**:
  - Objective assessment
  - Specific, actionable feedback
  - Progress recognition
  - Improvement suggestions

#### 5. Learning Coach (`learning_coach`)
- **Role**: Motivation and strategy expert
- **Capabilities**:
  - Study techniques
  - Motivation strategies
  - Time management
  - Confidence building

#### 6. Visual Learning Specialist (`visual_learning_specialist`)
- **Role**: Visual representation expert
- **Capabilities**:
  - Mermaid diagram creation
  - Flowcharts and process diagrams
  - Concept maps
  - Visual learning aids

## Usage Examples

### Collaborative Learning
```
User: "Help me understand calculus derivatives with examples and practice problems"
```
**Response**: Multiple agents collaborate to provide:
- Lead Tutor: Overall guidance and structure
- Subject Expert: Mathematical explanations
- Exercise Designer: Practice problems
- Visual Learning Specialist: Diagrams if needed

### Single Agent Consultation
```
User: "Ask the subject expert about quantum physics"
```
**Response**: Subject Expert provides focused, in-depth explanation

### General Learning Support
```
User: "I need help studying for my biology exam"
```
**Response**: Collaborative session with relevant agents (tutor, subject expert, learning coach)

## Intent Classification

The system now recognizes these additional intents:

- `collaborative-learning`: Comprehensive multi-agent support
- `single-agent-consultation`: Specific agent consultation
- `learning-support`: General educational assistance

### Intent Detection Examples

| User Input | Detected Intent | Target Agents |
|------------|----------------|---------------|
| "Help me learn calculus" | `collaborative-learning` | tutor, subject_expert, exercise_designer |
| "Ask the subject expert about physics" | `single-agent-consultation` | subject_expert |
| "Create a practice quiz" | `collaborative-learning` | tutor, exercise_designer |
| "Show me a diagram" | `collaborative-learning` | tutor, visual_learning_specialist |
| "I need study tips" | `learning-support` | tutor, learning_coach |

## Integration with Existing System

### Enhanced Workflow

1. **Intent Classification**: Improved to detect multi-agent scenarios
2. **Routing**: New handlers for collaborative and single-agent sessions
3. **Response Generation**: Combines multiple agent responses intelligently
4. **Session Management**: Maintains conversation context across agents

### Backward Compatibility

- All existing functionality preserved
- Activity management unchanged
- Database operations unaffected
- API endpoints remain the same

## API Endpoints

The existing `/agent/chat` endpoint now supports:

```json
{
  "prompt": "Help me understand quantum physics",
  "details": {
    "token": "user_jwt_token",
    "session_id": "optional_session_id"
  }
}
```

**Response**:
```json
{
  "intent": "collaborative-learning",
  "result": {
    "message": "## Collaborative Learning Response\n\n**Lead Tutor's Guidance:**...",
    "session_type": "collaborative_learning"
  }
}
```

## Testing

Run the test script to verify functionality:

```bash
python test_multi_agent.py
```

This will test:
- Collaborative learning scenarios
- Single agent consultations
- Individual agent capabilities
- Error handling

## Configuration

### Azure OpenAI Setup

The system uses the existing Azure configuration:

```python
# From app/core/azure_config.py
azure_config = load_azure_config()
```

### Agent Configuration

Each agent can be customized with:
- Temperature settings
- Max tokens
- System messages
- Specialized prompts

## Error Handling

The system includes comprehensive error handling:

- Agent communication failures
- Azure API errors
- Intent classification fallbacks
- Graceful degradation

## Performance Considerations

- Async/await for all agent communications
- Intelligent agent selection to minimize API calls
- Response caching (future enhancement)
- Session memory management

## Future Enhancements

1. **Agent Memory**: Persistent agent-specific knowledge
2. **Learning Analytics**: Track student progress across agents
3. **Dynamic Agent Creation**: On-demand specialized agents
4. **Multi-modal Support**: Image, audio, and video processing
5. **Personalization**: Adaptive agent behavior based on student profile

## Troubleshooting

### Common Issues

1. **Agent Not Responding**
   - Check Azure OpenAI configuration
   - Verify API key and endpoint
   - Check network connectivity

2. **Intent Classification Issues**
   - Review classification prompts
   - Check for new intent patterns
   - Verify fallback logic

3. **Response Quality**
   - Adjust agent temperature settings
   - Review system messages
   - Check prompt engineering

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

To add new agents:

1. Create agent definition in `MultiAgentSystem`
2. Add intent classification patterns
3. Update routing logic
4. Add test cases
5. Update documentation

## License

This implementation extends the existing student LMS AI backend system. 