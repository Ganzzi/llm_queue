"""Rate limiter implementation for controlling request rates."""

import asyncio
import time
from typing import List

from .models import RateLimiterMode


class RateLimiter:
    """Rate limiter for controlling request execution rates.

    Supports two modes:
    1. REQUESTS_PER_PERIOD: Limit number of requests in a time window
    2. CONCURRENT_REQUESTS: Limit number of concurrent requests

    Attributes:
        limit: Maximum number of requests (per period or concurrent)
        mode: Rate limiting mode
        time_period: Time period in seconds (for REQUESTS_PER_PERIOD mode)
    """

    def __init__(
        self,
        limit: int,
        mode: RateLimiterMode = RateLimiterMode.REQUESTS_PER_PERIOD,
        time_period: int = 60,
    ):
        """Initialize rate limiter.

        Args:
            limit: For REQUESTS_PER_PERIOD: number of requests per time_period.
                   For CONCURRENT_REQUESTS: max concurrent requests.
            mode: The rate limiter mode
            time_period: Time period in seconds (default: 60) - REQUESTS_PER_PERIOD only

        Raises:
            ValueError: If limit <= 0 or time_period <= 0
        """
        if limit <= 0:
            raise ValueError("limit must be greater than 0")
        if time_period <= 0:
            raise ValueError("time_period must be greater than 0")

        self.limit = limit
        self.mode = mode
        self.time_period = time_period
        self.timestamps: List[float] = []
        self._lock = asyncio.Lock()

        # For concurrent request limiting
        if mode == RateLimiterMode.CONCURRENT_REQUESTS:
            self._semaphore = asyncio.Semaphore(limit)

    async def acquire(self) -> bool:
        """Try to acquire a slot for execution.

        Returns:
            True if slot acquired, False otherwise.
        """
        if self.mode == RateLimiterMode.CONCURRENT_REQUESTS:
            # For concurrent requests mode, try to acquire the semaphore
            if self._semaphore.locked():
                return False

            # Try to acquire the semaphore (non-blocking)
            acquired = self._semaphore._value > 0
            if acquired:
                await self._semaphore.acquire()
            return acquired
        else:
            # REQUESTS_PER_PERIOD mode
            async with self._lock:
                now = time.time()
                # Remove timestamps older than time_period
                self.timestamps = [t for t in self.timestamps if now - t < self.time_period]

                if len(self.timestamps) < self.limit:
                    self.timestamps.append(now)
                    return True
                return False

    async def release(self) -> None:
        """Release a slot (only used in CONCURRENT_REQUESTS mode)."""
        if self.mode == RateLimiterMode.CONCURRENT_REQUESTS:
            self._semaphore.release()

    async def wait_for_slot(self) -> None:
        """Wait until a slot is available."""
        if self.mode == RateLimiterMode.CONCURRENT_REQUESTS:
            await self._semaphore.acquire()
            return
        else:
            # REQUESTS_PER_PERIOD mode
            while True:
                if await self.acquire():
                    return
                await asyncio.sleep(0.1)  # Avoid tight loop

    def get_current_usage(self) -> int:
        """Get current number of active/recent requests.

        Returns:
            For REQUESTS_PER_PERIOD: number of requests in current window
            For CONCURRENT_REQUESTS: number of concurrent requests
        """
        if self.mode == RateLimiterMode.CONCURRENT_REQUESTS:
            return self.limit - self._semaphore._value
        else:
            now = time.time()
            return len([t for t in self.timestamps if now - t < self.time_period])

    def get_available_slots(self) -> int:
        """Get number of available slots.

        Returns:
            Number of slots available for immediate execution
        """
        return self.limit - self.get_current_usage()
