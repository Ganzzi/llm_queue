"""Tests for new rate limiters and chain."""

import asyncio
import time
import pytest
from llm_queue.rate_limiters import (
    RequestRateLimiter,
    TokenRateLimiter,
    ConcurrentRateLimiter,
    RateLimiterChain,
)
from llm_queue.models import RateLimiterType, QueueRequest


class TestTokenRateLimiter:
    """Tests for TokenRateLimiter."""

    @pytest.mark.asyncio
    async def test_acquire_release(self):
        """Test acquiring and releasing tokens."""
        limiter = TokenRateLimiter(limit=100, time_period=60)
        
        # Acquire 50
        assert await limiter.acquire(50) is True
        assert limiter.get_current_usage() == 50
        
        # Acquire another 50
        assert await limiter.acquire(50) is True
        assert limiter.get_current_usage() == 100
        
        # Fail to acquire 1
        assert await limiter.acquire(1) is False
        
        # Release (refund) 50
        await limiter.release(50)
        assert limiter.get_current_usage() == 50
        
        # Acquire 50 again
        assert await limiter.acquire(50) is True
        assert limiter.get_current_usage() == 100


class TestRateLimiterChain:
    """Tests for RateLimiterChain."""

    @pytest.mark.asyncio
    async def test_chain_acquire_rollback(self):
        """Test that chain rolls back if one limiter fails."""
        # RPM limit 10
        rpm = RequestRateLimiter(limit=10, time_period=60)
        setattr(rpm, "rate_limiter_type", RateLimiterType.RPM)
        
        # TPM limit 60
        tpm = TokenRateLimiter(limit=60, time_period=60)
        setattr(tpm, "rate_limiter_type", RateLimiterType.TPM)
        
        chain = RateLimiterChain([rpm, tpm])
        
        req = QueueRequest(
            model_id="test", 
            params={}, 
            estimated_input_tokens=50, 
            estimated_output_tokens=0
        )
        
        # 1st request: 1 RPM, 50 TPM -> Success
        assert await chain.acquire_all(req) is True
        assert rpm.get_current_usage() == 1
        assert tpm.get_current_usage() == 50
        
        # 2nd request: 1 RPM, 50 TPM -> Fails TPM (limit 60)
        # Should rollback RPM
        assert await chain.acquire_all(req) is False
        
        # RPM usage should still be 1 (rollback successful)
        assert rpm.get_current_usage() == 1
        # TPM usage should still be 50
        assert tpm.get_current_usage() == 50

    @pytest.mark.asyncio
    async def test_update_token_usage_refund(self):
        """Test refunding tokens when actual < estimated."""
        tpm = TokenRateLimiter(limit=100, time_period=60)
        setattr(tpm, "rate_limiter_type", RateLimiterType.TPM)
        chain = RateLimiterChain([tpm])
        
        req = QueueRequest(
            model_id="test", 
            params={}, 
            estimated_input_tokens=80, 
            estimated_output_tokens=0
        )
        
        await chain.acquire_all(req)
        assert tpm.get_current_usage() == 80
        
        # Actual usage 50. Refund 30.
        await chain.update_token_usage(req, 50, 0)
        assert tpm.get_current_usage() == 50

    @pytest.mark.asyncio
    async def test_update_token_usage_overage(self):
        """Test recording overage when actual > estimated."""
        tpm = TokenRateLimiter(limit=100, time_period=60)
        setattr(tpm, "rate_limiter_type", RateLimiterType.TPM)
        chain = RateLimiterChain([tpm])
        
        req = QueueRequest(
            model_id="test", 
            params={}, 
            estimated_input_tokens=80, 
            estimated_output_tokens=0
        )
        
        await chain.acquire_all(req)
        assert tpm.get_current_usage() == 80
        
        # Actual usage 90. Overage 10.
        await chain.update_token_usage(req, 90, 0)
        assert tpm.get_current_usage() == 90

    @pytest.mark.asyncio
    async def test_wait_for_all(self):
        """Test blocking wait."""
        # Limit 1 request
        rpm = RequestRateLimiter(limit=1, time_period=1) # 1 sec period
        setattr(rpm, "rate_limiter_type", RateLimiterType.RPM)
        chain = RateLimiterChain([rpm])
        
        req = QueueRequest(model_id="test", params={})
        
        # 1st acquire
        await chain.wait_for_all(req)
        assert rpm.get_current_usage() == 1
        
        # 2nd wait - should block until 1st expires (approx 1s)
        start = time.time()
        await chain.wait_for_all(req)
        elapsed = time.time() - start
        
        assert elapsed >= 0.9 # Should wait approx 1s
        assert rpm.get_current_usage() == 1 # New usage (old expired)
