import json
from app.core.logger import get_logger
from typing import Any, Dict
import httpx
from openai import AsyncAzureOpenAI
from app.core.azure_config import load_azure_config
from app.core.config import settings

# Configure logging
logger = get_logger(__name__)

# Load Azure configuration and create OpenAI client
azure_config = load_azure_config()
client = AsyncAzureOpenAI(
    api_key=azure_config.api_key,
    azure_endpoint=azure_config.endpoint,
    api_version=azure_config.api_version
)

# Base URL for your Activity service
ACTIVITY_SERVICE_URL = settings.ACTIVITY_SERVICE_URL

async def chat_completion(
    state: dict,
    config: dict,
    temperature: float = 0.7,
    max_tokens: int = 512,
    json_mode: bool = False
) -> dict:
    logger.debug(f"=== CHAT_COMPLETION START ===")
    logger.debug(f"Input state: {state}")
    logger.debug(f"Config: {config}")
    logger.debug(f"Temperature: {temperature}, Max tokens: {max_tokens}, JSON mode: {json_mode}")
    
    try:
        prompt = state.get("prompt", "")
        messages = state.get("messages", [{"role": "user", "content": prompt}])
        logger.debug(f"Prompt: {prompt}")
        logger.debug(f"Messages: {messages}")
        
        if json_mode:
            system_msg = {"role": "system", "content": "You MUST respond with valid JSON ONLY."}
            messages = [system_msg] + messages
            logger.debug(f"JSON mode enabled, updated messages: {messages}")
        
        params = {
            "model": azure_config.deployment,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        logger.debug(f"OpenAI params: {params}")
        
        response = await client.chat.completions.create(**params)
        content = response.choices[0].message.content.strip()
        logger.debug(f"OpenAI response content: {content}")
        
        try:
            result = {"response": json.loads(content)}
            logger.debug(f"Parsed JSON response: {result}")
            logger.debug(f"=== CHAT_COMPLETION SUCCESS (JSON) ===")
            return result
        except json.JSONDecodeError:
            result = {"response": {"text": content}}
            logger.debug(f"JSON decode failed, using text response: {result}")
            logger.debug(f"=== CHAT_COMPLETION SUCCESS (TEXT) ===")
            return result
    except Exception as e:
        logger.error(f"=== CHAT_COMPLETION ERROR ===")
        logger.error(f"Error details: {e}")
        logger.error(f"Chat completion failed: {e}")
        raise

async def activity_crud(
    state: dict,
    config: dict
) -> dict:
    logger.debug(f"=== ACTIVITY_CRUD START ===")
    logger.debug(f"Input state: {state}")
    logger.debug(f"Config: {config}")
    
    try:
        operation = state.get("operation")
        payload = state.get("payload", {})
        logger.debug(f"Operation: {operation}")
        logger.debug(f"Payload: {payload}")
        
        method_map = {
            "create": ("post", ""),
            "list":   ("get",  ""),
            "list-activities": ("get", ""),
            "edit":   ("put",  f"/{payload.get('id')}"),
            "delete": ("delete", f"/{payload.get('id')}")
        }
        method, path = method_map[operation]
        url = f"{ACTIVITY_SERVICE_URL}{path}/" if path == "" else f"{ACTIVITY_SERVICE_URL}{path}"
        logger.debug(f"HTTP method: {method}")
        logger.debug(f"Path: {path}")
        logger.debug(f"Full URL: {url}")

        # Prepare headers
        headers = {}
        if payload.get("token"):
            headers["Authorization"] = f"Bearer {payload['token']}"

        # For GET, use query params; for others, use JSON body
        if method == "get":
            # Only include valid query params
            query_params = {k: v for k, v in payload.items() if k in {"category_name", "subcategory_name", "activity_name", "skip", "limit"} and v is not None}
            async with httpx.AsyncClient() as client_http:
                resp = await client_http.request(method, url, params=query_params, headers=headers, timeout=10)
        else:
            async with httpx.AsyncClient() as client_http:
                resp = await client_http.request(method, url, json=payload, headers=headers, timeout=10)

        logger.debug(f"HTTP response status: {resp.status_code}")
        logger.debug(f"HTTP response headers: {dict(resp.headers)}")
        resp.raise_for_status()
        result = resp.json()
        logger.debug(f"HTTP response body: {result}")
        logger.debug(f"=== ACTIVITY_CRUD SUCCESS ===")
        return {"result": result}
    except Exception as e:
        logger.error(f"=== ACTIVITY_CRUD ERROR ===")
        logger.error(f"Error details: {e}")
        logger.error(f"Activity CRUD failed: {e}")
        raise 