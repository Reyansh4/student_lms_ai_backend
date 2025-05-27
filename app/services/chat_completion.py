import httpx

from app.core.config import settings
from app.models.chat_models import (
    ChatCompletionRequest,
    ChatCompletionResponse
)

# Use settings instance for all config values
AZURE_OPENAI_ENDPOINT = settings.AZURE_OPENAI_ENDPOINT
AZURE_OPENAI_KEY = settings.AZURE_OPENAI_KEY
AZURE_OPENAI_DEPLOYMENT_NAME = settings.AZURE_OPENAI_DEPLOYMENT
AZURE_OPENAI_API_VERSION = settings.AZURE_OPENAI_API_VERSION
title = settings.TITLE

class ChatCompletion:
    def __init__(self):
        # Validate config
        if not all([AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, AZURE_OPENAI_DEPLOYMENT_NAME]):
            raise ValueError("Missing Azure OpenAI configuration in environment variables")

        self.url = (
            f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/"
            f"{AZURE_OPENAI_DEPLOYMENT_NAME}/chat/completions"
            f"?api-version={AZURE_OPENAI_API_VERSION}"
        )
        self.headers = {
            "Content-Type": "application/json",
            "api-key": AZURE_OPENAI_KEY
        }

    async def create(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """
        Send a chat completion request to Azure OpenAI and parse the response.
        """
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.url,
                headers=self.headers,
                json=request.dict(exclude_none=True)
            )
            resp.raise_for_status()
            return ChatCompletionResponse(**resp.json())