"""Tests for sliding window rate limiter."""

import asyncio
import pytest
from llm_queue.rate_limiters import RequestRateLimiter


@pytest.mark.unit
class TestSlidingWindow:
    """Tests for sliding window algorithm."""

    @pytest.mark.asyncio
    async def test_request_counting(self):
        """Test that requests are counted correctly."""
        limiter = RequestRateLimiter(limit=5, time_period=60)  # 5 requests per minute

        for i in range(5):
            assert await limiter.acquire(1) is True

        # Should be exhausted
        assert await limiter.acquire(1) is False
        assert limiter.get_current_usage() == 5

    @pytest.mark.asyncio
    async def test_window_expiry(self):
        """Test that requests expire after time period."""
        limiter = RequestRateLimiter(limit=3, time_period=1)  # 3 requests per second

        # Use all 3
        for _ in range(3):
            assert await limiter.acquire(1) is True

        # Exhausted
        assert await limiter.acquire(1) is False

        # Wait for window to pass
        await asyncio.sleep(1.1)

        # Should be available again
        assert await limiter.acquire(1) is True

    @pytest.mark.asyncio
    async def test_usage_tracking(self):
        """Test usage counter accuracy."""
        limiter = RequestRateLimiter(limit=10, time_period=60)

        assert limiter.get_current_usage() == 0

        await limiter.acquire(1)
        assert limiter.get_current_usage() == 1

        await limiter.acquire(3)
        assert limiter.get_current_usage() == 4

        await limiter.acquire(6)
        assert limiter.get_current_usage() == 10