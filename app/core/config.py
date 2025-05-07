from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Student LMS"
    VERSION: str = "1.0.0"
    API_PREFIX: str = ""
    
    # Database settings
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "reyansh4"
    POSTGRES_DB: str = "student_lms_ai"
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    # JWT Configuration
    JWT_SECRET_KEY: str = "JohnDoe"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


    @property
    def get_database_url(self) -> str:
        if self.SQLALCHEMY_DATABASE_URI:
            return self.SQLALCHEMY_DATABASE_URI
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

    class Config:
        case_sensitive = True

settings = Settings()
settings.SQLALCHEMY_DATABASE_URI = settings.get_database_url 