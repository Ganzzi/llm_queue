"""Utility functions and helpers for llm_queue package."""

import asyncio
import logging
from typing import Any, Callable, Optional, TypeVar
import time

T = TypeVar("T")


def setup_logging(level: int = logging.INFO, format_string: Optional[str] = None) -> None:
    """Set up logging for the package.

    Args:
        level: Logging level (default: INFO)
        format_string: Custom format string for log messages
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(level=level, format=format_string)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Name for the logger

    Returns:
        Logger instance
    """
    return logging.getLogger(f"llm_queue.{name}")


async def with_timeout(coro: Callable[..., Any], timeout: float, *args, **kwargs) -> Any:
    """Execute a coroutine with a timeout.

    Args:
        coro: Coroutine function to execute
        timeout: Timeout in seconds
        *args: Positional arguments for the coroutine
        **kwargs: Keyword arguments for the coroutine

    Returns:
        Result of the coroutine

    Raises:
        asyncio.TimeoutError: If timeout is exceeded
    """
    return await asyncio.wait_for(coro(*args, **kwargs), timeout=timeout)


class Timer:
    """Simple timer context manager for measuring execution time."""

    def __init__(self):
        """Initialize the timer."""
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.elapsed: Optional[float] = None

    def __enter__(self):
        """Start the timer."""
        self.start_time = time.time()
        return self

    def __exit__(self, *args):
        """Stop the timer and calculate elapsed time."""
        self.end_time = time.time()
        self.elapsed = self.end_time - self.start_time

    async def __aenter__(self):
        """Start the timer (async context)."""
        self.start_time = time.time()
        return self

    async def __aexit__(self, *args):
        """Stop the timer (async context)."""
        self.end_time = time.time()
        self.elapsed = self.end_time - self.start_time


def validate_rate_limit(rate_limit: int) -> None:
    """Validate rate limit value.

    Args:
        rate_limit: Rate limit to validate

    Raises:
        ValueError: If rate limit is invalid
    """
    if not isinstance(rate_limit, int):
        raise ValueError("rate_limit must be an integer")
    if rate_limit <= 0:
        raise ValueError("rate_limit must be greater than 0")


def validate_time_period(time_period: int) -> None:
    """Validate time period value.

    Args:
        time_period: Time period to validate

    Raises:
        ValueError: If time period is invalid
    """
    if not isinstance(time_period, int):
        raise ValueError("time_period must be an integer")
    if time_period <= 0:
        raise ValueError("time_period must be greater than 0")
