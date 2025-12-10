"""Rate limiter for request counts (RPM, RPD)."""

import asyncio
import time
from typing import List

from .base import BaseRateLimiter


class RequestRateLimiter(BaseRateLimiter):
    """Rate limiter for request counts (RPM, RPD)."""

    def __init__(self, limit: int, time_period: int):
        """Initialize request rate limiter.

        Args:
            limit: Maximum number of requests
            time_period: Time period in seconds
        """
        if limit <= 0:
            raise ValueError("limit must be greater than 0")
        if time_period <= 0:
            raise ValueError("time_period must be greater than 0")

        self.limit = limit
        self.time_period = time_period
        self.timestamps: List[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> bool:
        """Try to acquire request slot(s).

        Args:
            tokens: Number of requests to acquire (usually 1)

        Returns:
            True if acquired, False otherwise
        """
        async with self._lock:
            now = time.time()
            self._cleanup(now)

            if len(self.timestamps) + tokens <= self.limit:
                for _ in range(tokens):
                    self.timestamps.append(now)
                return True
            return False

    async def release(self, tokens: int = 1) -> None:
        """Release request slot(s).

        Note: For time-window limiters, releasing usually doesn't make sense
        unless we want to "refund" a failed request.
        We implement it by removing the most recent timestamps.
        """
        async with self._lock:
            if not self.timestamps:
                return
            
            # Remove up to 'tokens' most recent timestamps
            # This effectively "refunds" the capacity
            for _ in range(min(tokens, len(self.timestamps))):
                self.timestamps.pop()

    async def wait_for_slot(self, tokens: int = 1) -> None:
        """Wait until request slot(s) are available."""
        while True:
            if await self.acquire(tokens):
                return
            await asyncio.sleep(0.1)

    def get_current_usage(self) -> int:
        """Get current request count in window."""
        now = time.time()
        # We don't lock here for reading, but we filter
        return len([t for t in self.timestamps if now - t < self.time_period])

    def get_available_capacity(self) -> int:
        """Get available request slots."""
        return max(0, self.limit - self.get_current_usage())

    def _cleanup(self, now: float) -> None:
        """Remove expired timestamps."""
        self.timestamps = [t for t in self.timestamps if now - t < self.time_period]
