from pydantic import BaseModel
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class AzureConfig(BaseModel):
    endpoint: str
    api_key: str
    deployment: str = "gpt-4o-mini"
    api_version: str = "2024-02-15-preview"

    def validate_config(self) -> bool:
        if not self.endpoint.startswith("https://"): return False
        if not self.endpoint.endswith("/"): self.endpoint += "/"
        if not self.api_key or len(self.api_key) < 10: return False
        return True

def load_azure_config() -> AzureConfig:
    """Load and validate Azure OpenAI configuration from environment variables."""
    cfg = AzureConfig(
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        api_key=os.getenv("AZURE_OPENAI_KEY", ""),
        deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    )
    if not cfg.validate_config():
        logger.error("Invalid Azure configuration")
        raise ValueError("Invalid Azure configuration")
    return cfg 