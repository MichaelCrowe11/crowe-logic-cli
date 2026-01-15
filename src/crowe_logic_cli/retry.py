"""Retry logic with exponential backoff for API calls."""
from __future__ import annotations

import random
import time
from functools import wraps
from typing import Any, Callable, Optional, Sequence, Type, TypeVar

import httpx
from rich.console import Console

T = TypeVar("T")

# HTTP status codes that should trigger retry
RETRYABLE_STATUS_CODES = frozenset({
    408,  # Request Timeout
    429,  # Too Many Requests
    500,  # Internal Server Error
    502,  # Bad Gateway
    503,  # Service Unavailable
    504,  # Gateway Timeout
})

# Exception types that should trigger retry
RETRYABLE_EXCEPTIONS: tuple[Type[Exception], ...] = (
    httpx.TimeoutException,
    httpx.NetworkError,
    httpx.ConnectError,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.ConnectTimeout,
)


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_status_codes: Optional[frozenset[int]] = None,
        retryable_exceptions: Optional[tuple[Type[Exception], ...]] = None,
    ) -> None:
        """Initialize retry configuration.

        Args:
            max_retries: Maximum number of retry attempts (0 = no retries)
            initial_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            exponential_base: Base for exponential backoff calculation
            jitter: Whether to add random jitter to delays
            retryable_status_codes: HTTP status codes to retry on
            retryable_exceptions: Exception types to retry on
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_status_codes = retryable_status_codes or RETRYABLE_STATUS_CODES
        self.retryable_exceptions = retryable_exceptions or RETRYABLE_EXCEPTIONS

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a given retry attempt.

        Args:
            attempt: The current attempt number (0-based)

        Returns:
            Delay in seconds
        """
        delay = self.initial_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            # Add jitter: random value between 0 and delay
            delay = delay * (0.5 + random.random())

        return delay


# Default retry configuration
DEFAULT_RETRY_CONFIG = RetryConfig()


def is_retryable_error(error: Exception, config: RetryConfig) -> bool:
    """Check if an error should trigger a retry.

    Args:
        error: The exception that was raised
        config: Retry configuration

    Returns:
        True if the error is retryable
    """
    # Check for retryable exceptions
    if isinstance(error, config.retryable_exceptions):
        return True

    # Check for HTTP status code errors
    if isinstance(error, httpx.HTTPStatusError):
        return error.response.status_code in config.retryable_status_codes

    return False


def get_retry_after(error: Exception) -> Optional[float]:
    """Extract Retry-After header value if present.

    Args:
        error: The HTTP error

    Returns:
        Retry-After value in seconds, or None
    """
    if isinstance(error, httpx.HTTPStatusError):
        retry_after = error.response.headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
    return None


def with_retry(
    config: Optional[RetryConfig] = None,
    console: Optional[Console] = None,
    verbose: bool = True,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to add retry logic to a function.

    Args:
        config: Retry configuration (uses default if not provided)
        console: Rich console for status output
        verbose: Whether to print retry status messages

    Returns:
        Decorated function with retry logic
    """
    if config is None:
        config = DEFAULT_RETRY_CONFIG
    if console is None:
        console = Console()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_error: Optional[Exception] = None

            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e

                    if not is_retryable_error(e, config):
                        raise

                    if attempt >= config.max_retries:
                        raise

                    # Calculate delay (use Retry-After if available)
                    retry_after = get_retry_after(e)
                    delay = retry_after if retry_after else config.calculate_delay(attempt)

                    if verbose:
                        error_type = type(e).__name__
                        if isinstance(e, httpx.HTTPStatusError):
                            error_type = f"HTTP {e.response.status_code}"
                        console.print(
                            f"[yellow]⚠ {error_type} - Retrying in {delay:.1f}s "
                            f"(attempt {attempt + 1}/{config.max_retries})[/yellow]"
                        )

                    time.sleep(delay)

            # This should never be reached, but just in case
            if last_error:
                raise last_error
            raise RuntimeError("Retry logic error")

        return wrapper
    return decorator


class RetryableClient:
    """HTTP client wrapper with built-in retry logic."""

    def __init__(
        self,
        config: Optional[RetryConfig] = None,
        timeout: float = 120.0,
        console: Optional[Console] = None,
        verbose: bool = True,
    ) -> None:
        """Initialize retryable client.

        Args:
            config: Retry configuration
            timeout: Request timeout in seconds
            console: Rich console for output
            verbose: Whether to print retry messages
        """
        self.config = config or DEFAULT_RETRY_CONFIG
        self.timeout = timeout
        self.console = console or Console()
        self.verbose = verbose

    def request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make an HTTP request with retry logic.

        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional arguments for httpx

        Returns:
            HTTP response
        """
        kwargs.setdefault("timeout", self.timeout)
        last_error: Optional[Exception] = None

        for attempt in range(self.config.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.request(method, url, **kwargs)
                    response.raise_for_status()
                    return response
            except Exception as e:
                last_error = e

                if not is_retryable_error(e, self.config):
                    raise

                if attempt >= self.config.max_retries:
                    raise

                retry_after = get_retry_after(e)
                delay = retry_after if retry_after else self.config.calculate_delay(attempt)

                if self.verbose:
                    error_type = type(e).__name__
                    if isinstance(e, httpx.HTTPStatusError):
                        error_type = f"HTTP {e.response.status_code}"
                    self.console.print(
                        f"[yellow]⚠ {error_type} - Retrying in {delay:.1f}s "
                        f"(attempt {attempt + 1}/{self.config.max_retries})[/yellow]"
                    )

                time.sleep(delay)

        if last_error:
            raise last_error
        raise RuntimeError("Retry logic error")

    def post(self, url: str, **kwargs: Any) -> httpx.Response:
        """Make a POST request with retry logic."""
        return self.request("POST", url, **kwargs)

    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        """Make a GET request with retry logic."""
        return self.request("GET", url, **kwargs)
