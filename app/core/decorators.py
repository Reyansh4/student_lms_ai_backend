import functools
import logging
import time
from typing import Callable, Type, Tuple, Optional
import asyncio

logger = logging.getLogger(__name__)

def retry_on_transient_error(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
    transient_errors: Tuple[Type[Exception], ...] = (ValueError, ConnectionError, TimeoutError),
    retry_on_status_codes: Tuple[int, ...] = (429, 500, 502, 503, 504)
):
    """
    Decorator that retries a function on transient errors with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Factor to increase delay between retries
        transient_errors: Tuple of exception types to retry on
        retry_on_status_codes: Tuple of HTTP status codes to retry on
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            delay = initial_delay

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Check if we should retry
                    should_retry = (
                        isinstance(e, transient_errors) or
                        (hasattr(e, 'status_code') and e.status_code in retry_on_status_codes) or
                        (hasattr(e, 'response') and hasattr(e.response, 'status_code') and 
                         e.response.status_code in retry_on_status_codes)
                    )

                    if not should_retry or attempt == max_retries:
                        raise last_exception

                    # Log retry attempt
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}. "
                        f"Error: {str(e)}. Retrying in {delay:.2f} seconds..."
                    )

                    # Wait before retrying
                    await asyncio.sleep(delay)
                    
                    # Calculate next delay with exponential backoff
                    delay = min(delay * backoff_factor, max_delay)

            # This should never be reached due to the raise in the loop
            raise last_exception

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            delay = initial_delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Check if we should retry
                    should_retry = (
                        isinstance(e, transient_errors) or
                        (hasattr(e, 'status_code') and e.status_code in retry_on_status_codes) or
                        (hasattr(e, 'response') and hasattr(e.response, 'status_code') and 
                         e.response.status_code in retry_on_status_codes)
                    )

                    if not should_retry or attempt == max_retries:
                        raise last_exception

                    # Log retry attempt
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}. "
                        f"Error: {str(e)}. Retrying in {delay:.2f} seconds..."
                    )

                    # Wait before retrying
                    time.sleep(delay)
                    
                    # Calculate next delay with exponential backoff
                    delay = min(delay * backoff_factor, max_delay)

            # This should never be reached due to the raise in the loop
            raise last_exception

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator 