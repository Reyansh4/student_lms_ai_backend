from typing import Any, Dict, Optional
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, validator
import secrets
from pathlib import Path
import os

class Settings(BaseSettings):
    # Application settings
    PROJECT_NAME: str = "Student LMS"
    VERSION: str = "1.0.0" 
    API_PREFIX: str = "/api/v1"
    
    # Security settings
    SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRY_TIME: int = 60000  # Default to 60 minutes
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 6000
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database settings
    DB_HOST: str = "localhost"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "reyansh4"
    DB_NAME: str = "student_lms_ai"
    DB_PORT: int = 5432

    OPENAI_API_KEY: str

    HUGGINGFACE_API_KEY: str = os.getenv("HUGGINGFACE_API_KEY")

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
    ACTIVITY_SERVICE_URL: str="http://localhost:8000/api/v1/activities"
    SERVER_HOST: str = "http://localhost:8000"
    RUNNING_PORT: int = 8081
    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "allow"

# Create settings instance
settings = Settings()