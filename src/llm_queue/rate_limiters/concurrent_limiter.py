"""Rate limiter for concurrent requests."""

import asyncio

from .base import BaseRateLimiter


class ConcurrentRateLimiter(BaseRateLimiter):
    """Rate limiter for concurrent requests."""

    def __init__(self, limit: int):
        """Initialize concurrent rate limiter.

        Args:
            limit: Maximum number of concurrent requests
        """
        if limit <= 0:
            raise ValueError("limit must be greater than 0")

        self.limit = limit
        self._semaphore = asyncio.Semaphore(limit)

    async def acquire(self, tokens: int = 1) -> bool:
        """Try to acquire concurrent slot(s).

        Args:
            tokens: Number of slots (usually 1)

        Returns:
            True if acquired, False otherwise
        """
        # Check if enough tokens available
        # Accessing _value is an implementation detail but standard in asyncio
        if self._semaphore._value < tokens:
            return False

        # Acquire tokens
        # Since we checked _value, acquire() should not block or yield
        for _ in range(tokens):
            await self._semaphore.acquire()
        return True

    async def release(self, tokens: int = 1) -> None:
        """Release concurrent slot(s)."""
        for _ in range(tokens):
            self._semaphore.release()

    async def wait_for_slot(self, tokens: int = 1) -> None:
        """Wait until concurrent slot(s) are available."""
        for _ in range(tokens):
            await self._semaphore.acquire()

    def get_current_usage(self) -> int:
        """Get current concurrent usage."""
        return max(0, self.limit - self._semaphore._value)

    def get_available_capacity(self) -> int:
        """Get available concurrent slots."""
        return self._semaphore._value
