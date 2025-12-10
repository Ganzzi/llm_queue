"""Rate limiter for tokens (TPM, TPD, ITPM, OTPM)."""

import asyncio
import time
from typing import List, Tuple

from .base import BaseRateLimiter


class TokenRateLimiter(BaseRateLimiter):
    """Rate limiter for tokens (TPM, TPD, ITPM, OTPM)."""

    def __init__(self, limit: int, time_period: int):
        """Initialize token rate limiter.

        Args:
            limit: Maximum number of tokens
            time_period: Time period in seconds
        """
        if limit <= 0:
            raise ValueError("limit must be greater than 0")
        if time_period <= 0:
            raise ValueError("time_period must be greater than 0")

        self.limit = limit
        self.time_period = time_period
        # History of (timestamp, token_count)
        self.usage_history: List[Tuple[float, int]] = []
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> bool:
        """Try to acquire token capacity.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if acquired, False otherwise
        """
        async with self._lock:
            now = time.time()
            self._cleanup(now)

            current_usage = sum(count for _, count in self.usage_history)
            if current_usage + tokens <= self.limit:
                self.usage_history.append((now, tokens))
                return True
            return False

    async def release(self, tokens: int = 1) -> None:
        """Release token capacity.

        Used to refund over-estimated tokens.
        Adds a negative entry to history to offset usage.
        """
        async with self._lock:
            now = time.time()
            # Add negative entry to refund
            # We use current time so it expires in time_period from NOW
            self.usage_history.append((now, -tokens))

    async def wait_for_slot(self, tokens: int = 1) -> None:
        """Wait until token capacity is available."""
        while True:
            if await self.acquire(tokens):
                return
            await asyncio.sleep(0.1)

    def get_current_usage(self) -> int:
        """Get current token usage in window."""
        now = time.time()
        # Filter and sum
        valid_entries = [count for t, count in self.usage_history if now - t < self.time_period]
        return max(0, sum(valid_entries))

    def get_available_capacity(self) -> int:
        """Get available token capacity."""
        return max(0, self.limit - self.get_current_usage())

    def _cleanup(self, now: float) -> None:
        """Remove expired entries."""
        self.usage_history = [
            (t, count) for t, count in self.usage_history if now - t < self.time_period
        ]
