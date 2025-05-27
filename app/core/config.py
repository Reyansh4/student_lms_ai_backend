from typing import Any, Dict, Optional
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, validator, HttpUrl, Extra
import secrets
from pathlib import Path
<<<<<<< HEAD
import os
=======
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
>>>>>>> bc4b5af (added templates)

class Settings(BaseSettings):
    # Application settings
    PROJECT_NAME: str = "Student LMS"
    VERSION: str = "1.0.0" 
    API_PREFIX: str = "/api/v1"
    TITLE: str = "Create Chat Completions via Azure OpenAI"
    
    # Security settings
    SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
<<<<<<< HEAD
    ACCESS_TOKEN_EXPIRY_TIME: int = 60  # Default to 60 minutes
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
=======
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # Default to 60 minutes
>>>>>>> bc4b5af (added templates)
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database settings
    DB_HOST: str = "localhost"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "reyansh4"
    DB_NAME: str = "student_lms_ai"
    DB_PORT: int = 5432

<<<<<<< HEAD
    OPENAI_API_KEY: str

    HUGGINGFACE_API_KEY: str = os.getenv("HUGGINGFACE_API_KEY")
=======
    # Azure OpenAI settings
    AZURE_OPENAI_KEY: str
    AZURE_OPENAI_ENDPOINT: HttpUrl
    AZURE_OPENAI_DEPLOYMENT: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")  # Map to deployment name
    AZURE_OPENAI_API_VERSION: str = "2023-05-15"
>>>>>>> bc4b5af (added templates)

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Get database URI as string."""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DIR: Path = Path("logs")
    LOG_FILE: str = "app.log"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5

    class Config:
        case_sensitive = True
        env_file = ".env"
<<<<<<< HEAD
        extra = "allow"
=======
        extra = Extra.allow  # Allow extra fields from environment variables
>>>>>>> bc4b5af (added templates)

# Create settings instance
settings = Settings()