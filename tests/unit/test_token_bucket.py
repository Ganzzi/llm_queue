"""Tests for token bucket rate limiter algorithm."""

import asyncio
import pytest
from llm_queue.rate_limiters import TokenRateLimiter


@pytest.mark.unit
class TestTokenBucket:
    """Tests for token bucket algorithm."""

    @pytest.mark.asyncio
    async def test_token_acquire_release(self):
        """Test that tokens can be acquired and released."""
        limiter = TokenRateLimiter(limit=10, time_period=60)

        # Acquire tokens
        assert await limiter.acquire(5) is True
        assert limiter.get_current_usage() == 5

        # Should still have capacity
        assert await limiter.acquire(3) is True
        assert limiter.get_current_usage() == 8

        # Exhaust capacity
        assert await limiter.acquire(2) is True
        assert limiter.get_current_usage() == 10

        # Should be exhausted
        assert await limiter.acquire(1) is False
        assert limiter.get_available_capacity() == 0

    @pytest.mark.asyncio
    async def test_token_refund(self):
        """Test token refund via release."""
        limiter = TokenRateLimiter(limit=20, time_period=60)

        assert await limiter.acquire(15) is True
        assert limiter.get_current_usage() == 15

        # Refund some tokens
        await limiter.release(5)
        # Usage should go down by 5
        assert limiter.get_current_usage() == 10
        assert limiter.get_available_capacity() == 10

    @pytest.mark.asyncio
    async def test_burst_capacity(self):
        """Test burst capacity handling."""
        limiter = TokenRateLimiter(limit=5, time_period=10)

        # Should allow burst up to limit
        assert await limiter.acquire(5) is True
        assert limiter.get_current_usage() == 5
        assert await limiter.acquire(1) is False

    @pytest.mark.asyncio
    async def test_partial_consumption(self):
        """Test partial consumption and release."""
        limiter = TokenRateLimiter(limit=20, time_period=60)

        assert await limiter.acquire(7) is True
        assert limiter.get_current_usage() == 7
        assert await limiter.acquire(3) is True
        assert limiter.get_current_usage() == 10

        # Release tokens
        await limiter.release(5)
        assert limiter.get_current_usage() == 5