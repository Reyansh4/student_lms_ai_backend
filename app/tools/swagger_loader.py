import httpx
import threading
from functools import lru_cache
from app.core.config import settings

# URL to fetch your OpenAPI schema (configure in settings)
OPENAPI_URL = "http://localhost:8081/api/v1/openapi.json"

_lock = threading.Lock()

@lru_cache(maxsize=1)
def get_openapi_spec() -> dict:
    """
    Fetches and caches the OpenAPI spec on first call (cold start).
    """
    print(f"OPENAPI_URL: {OPENAPI_URL}")
    with _lock:
        resp = httpx.get(OPENAPI_URL, timeout=10.0)
        resp.raise_for_status()
        print(f"resp.json(): {resp.json()}")
        return resp.json()


def clear_openapi_spec_cache() -> None:
    """
    Clears the cached OpenAPI spec so the next call will re-fetch.
    """
    get_openapi_spec.cache_clear()
    print(f"Cleared cache")
