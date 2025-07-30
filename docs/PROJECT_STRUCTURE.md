# Project Structure

## Overview

This project has been reorganized for better modularity and maintainability. The structure follows a clear separation of concerns with dedicated folders for different components.

## 📁 Directory Structure

```
stident_lms_ai_backend/
├── app/                          # Main application code
│   ├── agents/                   # Multi-agent system
│   │   ├── __init__.py
│   │   ├── chat_agent.py         # Main LangGraph chat agent
│   │   ├── multi_agent_system.py # Collaborative learning system
│   │   ├── routers.py            # API routes for agents
│   │   └── templates/            # Agent templates
│   │       └── activity/
│   │           ├── clarification_questions.md
│   │           └── final_description.md
│   ├── api/                      # API dependencies and utilities
│   ├── config/                   # Configuration management
│   │   ├── __init__.py
│   │   └── agent_config.py       # Centralized agent configurations
│   ├── core/                     # Core utilities (logger, security, decorators)
│   ├── db/                       # Database models and sessions
│   ├── memory/                   # Hierarchical memory system
│   │   ├── __init__.py
│   │   ├── base_memory.py        # Abstract memory base classes
│   │   ├── sliding_window_memory.py # Working memory implementation
│   │   ├── retrieval_memory.py   # Long-term memory implementation
│   │   ├── hierarchical_memory.py # Main hierarchical system
│   │   ├── enhanced_store.py     # Enhanced store integration
│   │   └── store.py              # Original store (for compatibility)
│   ├── embeddings/               # Unified embedding system
│   │   ├── __init__.py
│   │   ├── models.py             # EmbeddingStore database model
│   │   ├── extractors.py         # Content extractors for each model type
│   │   ├── service.py            # Main embedding service
│   │   └── retrievers.py         # Semantic retrievers for different use cases
│   ├── models/                   # Database models
│   ├── prompts/                  # Centralized prompt management
│   │   ├── __init__.py
│   │   └── agent_prompts.py      # All agent prompts
│   ├── routes/                   # API routes
│   ├── schemas/                  # Pydantic schemas
│   ├── services/                 # External service integrations
│   ├── tools/                    # Functional tools and utilities
│   │   ├── __init__.py
│   │   └── agent_tools.py        # Centralized agent tools
│   ├── utils/                    # Utility functions
│   └── main.py                   # FastAPI application entry point
├── tests/                        # All test files
│   ├── __init__.py
│   ├── test_hierarchical_memory.py
│   ├── test_integration.py
│   ├── test_multi_agent.py
│   └── test_restructured_system.py
├── docs/                         # Documentation
│   ├── HIERARCHICAL_MEMORY_README.md
│   ├── PROJECT_STRUCTURE.md
│   └── RESTRUCTURED_SYSTEM_README.md
├── alembic/                      # Database migrations
├── assets/                       # Static assets
├── logs/                         # Application logs
├── requirements.txt               # Python dependencies
├── pyproject.toml               # Project configuration
└── README.md                     # Main project README
```

## 🔧 Key Components

### 1. Agents (`app/agents/`)
- **chat_agent.py**: Main LangGraph workflow for chat interactions
- **multi_agent_system.py**: Collaborative learning with multiple specialized agents
- **routers.py**: API endpoints for agent interactions
- **templates/**: Agent-specific templates and prompts

### 2. Memory System (`app/memory/`)
- **hierarchical_memory.py**: Main hierarchical memory system
- **sliding_window_memory.py**: Working memory (short-term)
- **retrieval_memory.py**: Long-term memory with semantic search
- **enhanced_store.py**: Session management with hierarchical memory

### 3. Embedding System (`app/embeddings/`)
- **models.py**: Unified embedding storage model
- **extractors.py**: Content extractors for each model type
- **service.py**: Main embedding service with Azure OpenAI integration
- **retrievers.py**: Semantic retrievers for different use cases

### 4. Configuration (`app/config/`)
- **settings.py**: Main application settings (database, security, logging, etc.)
- **azure_config.py**: Azure OpenAI configuration
- **agent_config.py**: Agent-specific configurations (temperature, tokens, etc.)
- **__init__.py**: Exports all configuration for easy imports

### 5. Prompts (`app/prompts/`)
- **agent_prompts.py**: All system prompts and templates
- Centralized prompt management for easy updates

### 6. Tools (`app/tools/`)
- **agent_tools.py**: Functional tools for agent operations
- Intent classification, activity extraction, etc.

## 🧪 Testing Structure

### Test Files (`tests/`)
- **test_hierarchical_memory.py**: Memory system tests
- **test_integration.py**: End-to-end integration tests
- **test_multi_agent.py**: Multi-agent system tests
- **test_restructured_system.py**: Complete system tests

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run specific test
python tests/test_hierarchical_memory.py
```

## 📚 Documentation (`docs/`)

### Documentation Files
- **HIERARCHICAL_MEMORY_README.md**: Complete memory system documentation
- **RESTRUCTURED_SYSTEM_README.md**: System architecture documentation
- **PROJECT_STRUCTURE.md**: This file - project organization

## 🔄 Migration from Old Structure

### Changes Made
1. **Consolidated Agent Folders**: Removed duplicate `app/agent/` folder
2. **Organized Tests**: Moved all test files to `tests/` folder
3. **Centralized Documentation**: Moved all `.md` files to `docs/` folder
4. **Consolidated Configuration**: Moved all config from `app/core/` to `app/config/`
5. **Updated Imports**: Fixed all import paths to use new structure

### Import Updates
```python
# Old imports
from app.agent.chat import run_agent
from app.agent.multi_agent_system import multi_agent_system
from app.core.config import settings
from app.core.azure_config import load_azure_config

# New imports
from app.agents.chat_agent import run_agent
from app.agents.multi_agent_system import multi_agent_system
from app.config import settings, load_azure_config
```

## 🎯 Benefits of New Structure

### 1. **Clear Separation of Concerns**
- Agents, memory, configuration, and tools are clearly separated
- Each component has its own dedicated folder

### 2. **Improved Maintainability**
- Centralized configuration and prompts
- Easy to locate and update specific components

### 3. **Better Testing Organization**
- All tests in one location
- Clear test categorization

### 4. **Enhanced Documentation**
- Organized documentation structure
- Easy to find relevant information

### 5. **Scalable Architecture**
- Modular design allows easy extension
- New components can be added without affecting existing code

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Tests
```bash
python tests/test_hierarchical_memory.py
```

### 3. Start Application
```bash
python -m uvicorn app.main:app --reload
```

## 📝 Development Guidelines

### 1. **Adding New Agents**
- Place new agent files in `app/agents/`
- Update `app/config/agent_config.py` for agent-specific configurations
- Add prompts to `app/prompts/agent_prompts.py`

### 2. **Adding New Memory Types**
- Extend `app/memory/base_memory.py`
- Implement new memory strategy
- Update `app/memory/hierarchical_memory.py` if needed

### 3. **Adding New Entity Types for Embeddings**
- Create new extractor in `app/embeddings/extractors.py`
- Add to `EXTRACTOR_REGISTRY`
- Update `app/embeddings/retrievers.py` for specialized search

### 4. **Adding New Tests**
- Place test files in `tests/` folder
- Follow naming convention: `test_*.py`
- Update import paths to use new structure

### 5. **Adding Documentation**
- Place documentation in `docs/` folder
- Use clear, descriptive filenames
- Include usage examples and API references

This organized structure provides a solid foundation for the multi-agent learning platform with hierarchical memory capabilities. 