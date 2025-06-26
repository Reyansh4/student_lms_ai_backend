import os
import httpx
from typing import Any, Dict

HUGGINGFACE_API_URL = os.getenv("HUGGINGFACE_API_URL")  # e.g. https://api-inference.huggingface.co/models/your-model
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")

class HuggingFaceClient:
    def __init__(self, api_url: str = HUGGINGFACE_API_URL, token: str = HUGGINGFACE_API_TOKEN):
        self.api_url = api_url
        self.headers = {"Authorization": f"Bearer {token}"}

    async def generate(self, inputs: Any, parameters: Dict[str, Any] = {}) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.api_url,
                headers=self.headers,
                json={"inputs": inputs, "parameters": parameters},
                timeout=30
            )
            resp.raise_for_status()
            return resp.json()
