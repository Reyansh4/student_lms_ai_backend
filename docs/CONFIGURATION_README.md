# Configuration Management

## Overview

All application configuration has been consolidated into the `app/config/` folder for better modularity and maintainability. This includes application settings, Azure OpenAI configuration, and agent-specific configurations.

## 📁 Configuration Structure

```
app/config/
├── __init__.py           # Exports all configuration
├── settings.py           # Main application settings
├── azure_config.py       # Azure OpenAI configuration
└── agent_config.py       # Agent-specific configurations
```

## 🔧 Configuration Components

### 1. **Main Settings** (`settings.py`)

Contains all application-level settings:

```python
from app.config import settings

# Application settings
settings.PROJECT_NAME          # "Student LMS"
settings.VERSION              # "1.0.0"
settings.API_PREFIX           # "/api/v1"

# Security settings
settings.SECRET_KEY           # JWT secret key
settings.JWT_SECRET_KEY       # JWT signing key
settings.ALGORITHM            # "HS256"
settings.ACCESS_TOKEN_EXPIRE_MINUTES  # 6000

# Database settings
settings.DB_HOST              # "localhost"
settings.DB_USER              # "postgres"
settings.DB_PASSWORD          # "reyansh4"
settings.DB_NAME              # "student_lms_ai"
settings.DB_PORT              # 5432
settings.SQLALCHEMY_DATABASE_URI  # Constructed URI

# API Keys
settings.OPENAI_API_KEY       # OpenAI API key
settings.HUGGINGFACE_API_KEY  # HuggingFace API key

# Service URLs
settings.ACTIVITY_SERVICE_URL # "http://localhost:8081/api/v1/activities"
settings.SERVER_HOST          # "http://localhost:8081"

# Logging settings
settings.LOG_LEVEL            # "INFO"
settings.LOG_FORMAT           # Log format string
settings.LOG_DIR              # Path("logs")
settings.LOG_FILE             # "app.log"
```

### 2. **Azure Configuration** (`azure_config.py`)

Manages Azure OpenAI settings:

```python
from app.config import load_azure_config, AzureConfig

# Load Azure configuration
azure_config = load_azure_config()

# Configuration properties
azure_config.endpoint              # Azure OpenAI endpoint
azure_config.api_key              # Azure OpenAI API key
azure_config.deployment           # "gpt-4o-mini"
azure_config.api_version          # "2024-02-15-preview"
azure_config.embedding_deployment # "text-embedding-ada-002"
```

### 3. **Agent Configuration** (`agent_config.py`)

Contains all agent-specific settings:

```python
from app.config import (
    get_agent_config,
    get_intent_classification_config,
    get_multi_agent_config,
    is_valid_intent,
    get_agent_selection_patterns
)

# Get agent configuration
tutor_config = get_agent_config("tutor")
# Returns: {"temperature": 0.7, "max_tokens": 1000, "role": "coordinator"}

# Get intent classification config
intent_config = get_intent_classification_config()
# Returns: {"temperature": 0.3, "max_tokens": 512, "json_mode": True}

# Check valid intents
is_valid = is_valid_intent("collaborative-learning")  # True
is_valid = is_valid_intent("invalid-intent")         # False

# Get agent selection patterns
patterns = get_agent_selection_patterns()
# Returns patterns for subject_specific, exercise_requests, etc.
```

## 🚀 Usage Examples

### 1. **Importing Configuration**

```python
# Import everything from config
from app.config import settings, load_azure_config, get_agent_config

# Use settings
database_uri = settings.SQLALCHEMY_DATABASE_URI
project_name = settings.PROJECT_NAME

# Use Azure config
azure_config = load_azure_config()
endpoint = azure_config.endpoint

# Use agent config
tutor_config = get_agent_config("tutor")
temperature = tutor_config["temperature"]
```

### 2. **Environment Variables**

The configuration system supports environment variables through `.env` files:

```bash
# .env file
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

OPENAI_API_KEY=your-openai-key
HUGGINGFACE_API_KEY=your-huggingface-key

DB_HOST=localhost
DB_USER=postgres
DB_PASSWORD=your-password
DB_NAME=student_lms_ai
DB_PORT=5432
```

### 3. **Configuration Validation**

```python
from app.config import load_azure_config

try:
    azure_config = load_azure_config()
    print("✅ Azure configuration is valid")
except ValueError as e:
    print(f"❌ Azure configuration error: {e}")
```

## 🔧 Configuration Categories

### **Application Settings**
- Project metadata (name, version, API prefix)
- Security settings (JWT, tokens, algorithms)
- Database connection settings
- Logging configuration
- Service URLs

### **Azure OpenAI Settings**
- Endpoint configuration
- API keys and authentication
- Model deployments
- API versions
- Embedding model settings

### **Agent Settings**
- Temperature and token limits per agent
- Intent classification parameters
- Activity extraction settings
- Multi-agent system configuration
- Valid intents and patterns
- Response templates

## 📝 Development Guidelines

### 1. **Adding New Settings**
```python
# In app/config/settings.py
class Settings(BaseSettings):
    # Add new setting
    NEW_SETTING: str = "default_value"
    
    # Add with environment variable support
    NEW_API_KEY: str = os.getenv("NEW_API_KEY", "")
```

### 2. **Adding New Agent Configurations**
```python
# In app/config/agent_config.py
AGENT_CONFIG = {
    "new_agent": {
        "temperature": 0.7,
        "max_tokens": 1000,
        "role": "new_role"
    }
}
```

### 3. **Adding New Azure Settings**
```python
# In app/config/azure_config.py
class AzureConfig(BaseModel):
    # Add new Azure setting
    new_setting: str = "default_value"
```

### 4. **Using Configuration in Code**
```python
# Import from consolidated config
from app.config import settings, get_agent_config

# Use in your code
def my_function():
    db_uri = settings.SQLALCHEMY_DATABASE_URI
    agent_config = get_agent_config("tutor")
    return f"Using {settings.PROJECT_NAME} with {agent_config['temperature']} temperature"
```

## 🎯 Benefits of Consolidated Configuration

### 1. **Single Source of Truth**
- All configuration in one place
- No scattered config files
- Easy to find and update settings

### 2. **Type Safety**
- Pydantic models for validation
- Automatic type checking
- Clear configuration schemas

### 3. **Environment Variable Support**
- Automatic `.env` file loading
- Environment variable overrides
- Secure credential management

### 4. **Modular Design**
- Separate concerns (app, Azure, agents)
- Easy to extend and maintain
- Clear import structure

### 5. **Validation**
- Automatic configuration validation
- Clear error messages
- Fail-fast on invalid config

## 🔄 Migration from Old Structure

### Old Import Pattern
```python
from app.core.config import settings
from app.core.azure_config import load_azure_config
```

### New Import Pattern
```python
from app.config import settings, load_azure_config
```

### Benefits
- ✅ Single import location
- ✅ Cleaner import statements
- ✅ Better organization
- ✅ Easier maintenance

This consolidated configuration system provides a clean, maintainable, and type-safe way to manage all application settings in one place. 