import httpx
from app.core.config import settings

HUGGINGFACE_API_KEY = settings.HUGGINGFACE_API_KEY
MODEL_ID = "meta-llama/Meta-Llama-3-8B-Instruct"  # Or your chosen model

async def query_huggingface(prompt: str, temperature: float = 0.7) -> str:
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": prompt,
        "parameters": {"temperature": temperature}
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api-inference.huggingface.co/models/{MODEL_ID}",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        return result[0]["generated_text"] if isinstance(result, list) else result.get("generated_text", "")
