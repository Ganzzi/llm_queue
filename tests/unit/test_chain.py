"""Tests for rate limiter chain."""

import asyncio
import pytest
from llm_queue.rate_limiters import (
    RequestRateLimiter,
    TokenRateLimiter,
    RateLimiterChain,
)
from llm_queue.models import RateLimiterType, QueueRequest


@pytest.mark.unit
class TestRateLimiterChain:
    """Tests for rate limiter chain."""

    @pytest.mark.asyncio
    async def test_chain_all_must_pass(self):
        """Test that all limiters in chain must pass."""
        rpm = RequestRateLimiter(limit=5, time_period=60)
        setattr(rpm, "rate_limiter_type", RateLimiterType.RPM)
        tpm = TokenRateLimiter(limit=200, time_period=60)
        setattr(tpm, "rate_limiter_type", RateLimiterType.TPM)

        chain = RateLimiterChain([rpm, tpm])
        req = QueueRequest(
            model_id="test",
            params={},
            estimated_input_tokens=50,
            estimated_output_tokens=0
        )

        # Both should pass
        assert await chain.acquire_all(req) is True
        # RPM: 1 request consumed
        assert rpm.get_current_usage() == 1
        # TPM: 50 tokens consumed
        assert tpm.get_current_usage() == 50

        # Another request that should pass
        req2 = QueueRequest(
            model_id="test",
            params={},
            estimated_input_tokens=100,
            estimated_output_tokens=0
        )

        # Should still pass: RPM=2 (still < 5), TPM=150 (still < 200)
        assert await chain.acquire_all(req2) is True
        assert rpm.get_current_usage() == 2
        assert tpm.get_current_usage() == 150

        # Third request that should fail due to TPM
        req3 = QueueRequest(
            model_id="test",
            params={},
            estimated_input_tokens=60,  # Would make TPM usage 210 > 200
            estimated_output_tokens=0
        )

        # Should fail because TPM limit exceeded
        assert await chain.acquire_all(req3) is False
        # RPM usage should be rolled back, so still 2
        assert rpm.get_current_usage() == 2
        # TPM usage should be rolled back, so still 150
        assert tpm.get_current_usage() == 150

    @pytest.mark.asyncio
    async def test_chain_rollback_on_failure(self):
        """Test that chain rolls back acquisitions on failure."""
        rpm = RequestRateLimiter(limit=2, time_period=60)
        setattr(rpm, "rate_limiter_type", RateLimiterType.RPM)
        tpm = TokenRateLimiter(limit=200, time_period=60)
        setattr(tpm, "rate_limiter_type", RateLimiterType.TPM)

        chain = RateLimiterChain([rpm, tpm])
        req = QueueRequest(
            model_id="test",
            params={},
            estimated_input_tokens=100,
            estimated_output_tokens=0
        )

        # First request: should pass
        assert await chain.acquire_all(req) is True
        assert rpm.get_current_usage() == 1
        assert tpm.get_current_usage() == 100

        # Second request: exceeds TPM (100 + 150 = 250 > 200)
        req2 = QueueRequest(
            model_id="test",
            params={},
            estimated_input_tokens=150,
            estimated_output_tokens=0
        )

        # Should fail and rollback RPM
        assert await chain.acquire_all(req2) is False
        assert rpm.get_current_usage() == 1  # RPM should be rolled back to 1 (was 2)
        assert tpm.get_current_usage() == 100  # TPM unchanged from 100

    @pytest.mark.asyncio
    async def test_empty_chain(self):
        """Test chain with no limiters."""
        chain = RateLimiterChain([])
        req = QueueRequest(model_id="test", params={})

        # Empty chain should always allow
        assert await chain.acquire_all(req) is True