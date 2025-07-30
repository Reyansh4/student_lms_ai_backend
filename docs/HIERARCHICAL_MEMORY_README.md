# Hierarchical Memory System

## Overview

The Hierarchical Memory System implements a sophisticated memory architecture that mimics human memory organization with multiple layers: Working Memory (fast, short-term), Long-Term Memory (durable, semantic search-based), and intelligent promotion logic between them.

## 🧠 Architecture

### Memory Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Hierarchical Memory                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────┐   │
│  │  Working Memory │    │     Long-Term Memory       │   │
│  │  (SlidingWindow)│    │     (Retrieval-based)      │   │
│  │                 │    │                             │   │
│  │ • Fast access   │    │ • Semantic search          │   │
│  │ • Recent convos │    │ • Embedding-based          │   │
│  │ • Limited size  │    │ • Durable storage          │   │
│  │ • Auto-eviction │    │ • Intelligent retrieval    │   │
│  └─────────────────┘    └─────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│              Promotion Logic & Keywords                   │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

1. **Working Memory** (`SlidingWindowMemory`)
   - Fast, short-term storage
   - Sliding window with configurable size
   - Automatic eviction of old messages
   - Recent conversation context

2. **Long-Term Memory** (`RetrievalMemory`)
   - Durable, semantic search-based storage
   - Embedding-based similarity search
   - Configurable retrieval count (k)
   - Intelligent context retrieval

3. **Promotion Logic**
   - Automatic promotion based on keywords
   - Pattern matching for personal information
   - Learning-specific content detection
   - Explicit promotion flags

## 📁 File Structure

```
app/memory/
├── __init__.py
├── base_memory.py              # Abstract base classes
├── sliding_window_memory.py    # Working memory implementation
├── retrieval_memory.py         # Long-term memory implementation
├── hierarchical_memory.py      # Main hierarchical system
├── enhanced_store.py           # Enhanced store integration
└── store.py                   # Original store (for compatibility)
```

## 🔧 Usage Examples

### Basic Hierarchical Memory

```python
from app.memory.hierarchical_memory import HierarchicalMemory

# Initialize hierarchical memory
hierarchical_memory = HierarchicalMemory(
    window_size=5,    # Working memory size
    k=5,              # Number of relevant memories to retrieve
    embedding_dim=1536 # Embedding dimension
)

# Add messages (automatically handles promotion)
hierarchical_memory.add_message(
    user_input="Please remember my User ID is AX-7890.",
    ai_response="I'll remember your User ID as AX-7890.",
    session_id="user_123"
)

# Get context (combines working and long-term memory)
context = hierarchical_memory.get_context("What's my User ID?", "user_123")
print(context)
```

### Enhanced Store Integration

```python
from app.memory.enhanced_store import enhanced_memory_store

# Create session
session = enhanced_memory_store.get_or_create_session("user_123")

# Add messages (automatically integrates with hierarchical memory)
enhanced_memory_store.add_message(session.session_id, "user", "I'm allergic to peanuts")
enhanced_memory_store.add_message(session.session_id, "assistant", "I'll remember your peanut allergy")

# Get hierarchical context
context = enhanced_memory_store.get_hierarchical_context(
    "What are my allergies?", 
    session.session_id
)
```

### Chat Agent Integration

```python
from app.agents.chat_agent import run_agent

# The chat agent automatically uses hierarchical memory
result = await run_agent({
    "prompt": "Please remember my User ID is AX-7890.",
    "details": {"token": "user_token"},
    "user_id": "user_123",
    "db": None
})
```

## 🎯 Promotion Keywords

### Default Promotion Keywords

**General Keywords:**
- `remember`, `rule`, `preference`, `always`, `never`, `allergic`
- `important`, `critical`, `save`, `store`, `keep`, `note`
- `user id`, `password`, `username`, `email`, `phone`, `address`
- `preference`, `setting`, `configuration`, `favorite`, `like`, `dislike`

**Learning-Specific Keywords:**
- `learn`, `study`, `practice`, `understand`, `explain`, `teach`
- `concept`, `topic`, `subject`, `lesson`, `course`, `assignment`
- `quiz`, `test`, `exam`, `homework`, `project`, `research`

### Custom Promotion Keywords

```python
# Add custom promotion keywords
hierarchical_memory.add_promotion_keyword("custom_keyword")

# Remove promotion keywords
hierarchical_memory.remove_promotion_keyword("custom_keyword")

# Get all promotion keywords
keywords = hierarchical_memory.get_promotion_keywords()
```

## 🔍 Memory Retrieval

### Working Memory Context

```python
# Get recent conversation context
working_context = hierarchical_memory.working_memory.get_context(query, session_id)
```

### Long-Term Memory Context

```python
# Get semantically relevant memories
long_term_context = hierarchical_memory.long_term_memory.get_context(query, session_id)
```

### Combined Context

```python
# Get combined context from both memory systems
combined_context = hierarchical_memory.get_context(query, session_id)
```

## 📊 Memory Statistics

```python
# Get comprehensive memory statistics
stats = hierarchical_memory.get_memory_stats(session_id)

print(f"Working Memory Messages: {stats['working_memory']['message_count']}")
print(f"Long-term Memory Messages: {stats['long_term_memory']['message_count']}")
print(f"Total Messages: {stats['total_messages']}")
print(f"Promotion Keywords: {stats['promotion_keywords_count']}")
```

## 🧪 Testing

### Run Memory Tests

```bash
# Test hierarchical memory system
python test_hierarchical_memory.py

# Test with chat agent integration
python test_restructured_system.py
```

### Test Scenarios

1. **User ID Memory Test**
   ```python
   # Add important information
   hierarchical_memory.add_message(
       "Please remember my User ID is AX-7890.",
       "I'll remember your User ID as AX-7890.",
       "test_session"
   )
   
   # Later retrieve it
   context = hierarchical_memory.get_context("What's my User ID?", "test_session")
   ```

2. **Learning Preference Test**
   ```python
   # Add learning preferences
   hierarchical_memory.add_message(
       "I prefer to learn through visual diagrams and examples.",
       "I'll remember your learning preference for visual aids.",
       "test_session"
   )
   ```

3. **Allergy Information Test**
   ```python
   # Add health information
   hierarchical_memory.add_message(
       "I'm allergic to peanuts, please remember this.",
       "I'll remember your peanut allergy.",
       "test_session"
   )
   ```

## ⚙️ Configuration

### Hierarchical Memory Configuration

```python
hierarchical_memory = HierarchicalMemory(
    window_size=5,        # Working memory window size
    k=5,                  # Number of relevant memories to retrieve
    embedding_dim=1536    # Embedding vector dimension
)
```

### Azure OpenAI Configuration

The system uses Azure OpenAI for embeddings:

```python
# From app/core/azure_config.py
azure_config = load_azure_config()

# Embedding model configuration
embedding_model = AzureOpenAIEmbeddings(
    openai_api_version=azure_config.api_version,
    azure_deployment=azure_config.embedding_deployment or "text-embedding-ada-002",
    azure_endpoint=azure_config.endpoint,
    api_key=azure_config.api_key
)
```

## 🔄 Memory Operations

### Adding Messages

```python
# Add message with metadata
hierarchical_memory.add_message(
    user_input="User message",
    ai_response="AI response",
    session_id="session_123",
    metadata={"intent": "learning", "topic": "math"}
)
```

### Clearing Memory

```python
# Clear all memory for a session
hierarchical_memory.clear_memory("session_123")

# Clear enhanced store memory
enhanced_memory_store.clear_session_memory("session_123")
```

### Memory Statistics

```python
# Get detailed statistics
stats = enhanced_memory_store.get_memory_stats(session_id)

print(f"Session Messages: {stats['session']['session_messages']}")
print(f"Working Memory: {stats['hierarchical']['working_memory']['message_count']}")
print(f"Long-term Memory: {stats['hierarchical']['long_term_memory']['message_count']}")
```

## 🎯 Use Cases

### 1. Educational Context

```python
# Student provides learning preferences
hierarchical_memory.add_message(
    "I learn best through visual diagrams and practical examples.",
    "I'll remember your learning preference for visual and practical methods.",
    "student_123"
)

# Later, when explaining concepts
context = hierarchical_memory.get_context("Explain calculus", "student_123")
# System will include visual and practical approaches
```

### 2. Personal Information Management

```python
# User provides important information
hierarchical_memory.add_message(
    "My User ID is AX-7890 and I'm allergic to peanuts.",
    "I'll remember your User ID and peanut allergy.",
    "user_123"
)

# Later retrieval
context = hierarchical_memory.get_context("What's my User ID?", "user_123")
# System will retrieve the stored information
```

### 3. Learning Progress Tracking

```python
# Track learning progress
hierarchical_memory.add_message(
    "I'm studying calculus and currently on derivatives.",
    "I'll remember you're studying calculus derivatives.",
    "student_123"
)

# Context-aware responses
context = hierarchical_memory.get_context("Help me with calculus", "student_123")
# System will focus on derivatives and related concepts
```

## 🔧 Advanced Features

### Custom Promotion Logic

```python
# Override promotion logic
def custom_promotion_check(user_input, ai_response, metadata):
    # Custom logic here
    return "custom_reason" if condition else ""

# Use in hierarchical memory
hierarchical_memory._should_promote_to_long_term = custom_promotion_check
```

### Memory Persistence

```python
# Save memory state (future enhancement)
memory_state = hierarchical_memory.get_memory_stats(session_id)

# Load memory state (future enhancement)
hierarchical_memory.load_memory_state(memory_state)
```

### Memory Analytics

```python
# Get memory analytics
analytics = {
    "promotion_rate": promoted_messages / total_messages,
    "retrieval_accuracy": relevant_retrievals / total_retrievals,
    "memory_efficiency": working_memory_usage / window_size
}
```

## 🚀 Performance Considerations

1. **Working Memory**: Fast access, limited size
2. **Long-Term Memory**: Slower but more comprehensive
3. **Embedding Generation**: Cached for efficiency
4. **Semantic Search**: Optimized similarity calculations
5. **Memory Eviction**: Automatic cleanup

## 🔮 Future Enhancements

1. **Memory Persistence**: Database storage for long-term memory
2. **Memory Compression**: Efficient storage of large memory sets
3. **Memory Analytics**: Detailed usage and performance metrics
4. **Memory Sharing**: Cross-session memory sharing
5. **Memory Privacy**: Encrypted memory storage
6. **Memory Optimization**: Automatic memory cleanup and optimization

## ✅ Benefits

- **Human-like Memory**: Mimics human memory organization
- **Intelligent Promotion**: Automatic important information detection
- **Semantic Retrieval**: Context-aware memory retrieval
- **Scalable Architecture**: Modular and extensible design
- **Educational Focus**: Learning-specific optimizations
- **Performance Optimized**: Efficient memory operations

This hierarchical memory system provides a sophisticated foundation for building AI agents with human-like memory capabilities, particularly well-suited for educational applications. 