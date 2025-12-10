"""Rate limiter chain for managing multiple limiters."""

import asyncio
from typing import List, Tuple

from ..models import QueueRequest, RateLimiterType
from .base import BaseRateLimiter
from .concurrent_limiter import ConcurrentRateLimiter
from .token_limiter import TokenRateLimiter


class RateLimiterChain:
    """Manages multiple rate limiters for a single model."""

    def __init__(self, limiters: List[BaseRateLimiter]):
        """Initialize chain.

        Args:
            limiters: List of rate limiters. Each limiter must have a
                     'rate_limiter_type' attribute set.
        """
        self.limiters = limiters

    async def acquire_all(self, request: QueueRequest) -> bool:
        """Try to acquire capacity from all limiters.

        If any fails, rollback acquired ones.

        Args:
            request: The request to acquire for

        Returns:
            True if all acquired, False otherwise
        """
        acquired_limiters: List[Tuple[BaseRateLimiter, int]] = []

        try:
            for limiter in self.limiters:
                tokens = self._get_tokens_for_limiter(limiter, request)
                if await limiter.acquire(tokens):
                    acquired_limiters.append((limiter, tokens))
                else:
                    # Failed to acquire, rollback
                    await self._rollback(acquired_limiters)
                    return False
            return True
        except Exception:
            await self._rollback(acquired_limiters)
            raise

    async def release_all(self, request: QueueRequest) -> None:
        """Release capacity (mainly for concurrent limiters).

        Args:
            request: The request to release for
        """
        for limiter in self.limiters:
            if isinstance(limiter, ConcurrentRateLimiter):
                tokens = self._get_tokens_for_limiter(limiter, request)
                await limiter.release(tokens)

    async def wait_for_all(self, request: QueueRequest) -> None:
        """Wait until all limiters have capacity AND acquire them.

        This method blocks until all limiters are acquired.
        We acquire in order to prevent deadlocks.

        Args:
            request: The request to wait for
        """
        for limiter in self.limiters:
            tokens = self._get_tokens_for_limiter(limiter, request)
            # wait_for_slot will block until capacity is available AND acquire it
            await limiter.wait_for_slot(tokens)

    async def update_token_usage(
        self, request: QueueRequest, actual_input: int, actual_output: int
    ) -> None:
        """Update actual token usage and adjust limiters.

        Args:
            request: The original request
            actual_input: Actual input tokens used
            actual_output: Actual output tokens used
        """
        est_input = request.estimated_input_tokens or 0
        est_output = request.estimated_output_tokens or 0

        for limiter in self.limiters:
            if isinstance(limiter, TokenRateLimiter):
                limiter_type = getattr(limiter, "rate_limiter_type", None)
                if not limiter_type:
                    continue

                estimated = 0
                actual = 0

                if limiter_type in (RateLimiterType.TPM, RateLimiterType.TPD):
                    estimated = est_input + est_output
                    actual = actual_input + actual_output
                elif limiter_type == RateLimiterType.ITPM:
                    estimated = est_input
                    actual = actual_input
                elif limiter_type == RateLimiterType.OTPM:
                    estimated = est_output
                    actual = actual_output
                else:
                    continue

                diff = estimated - actual
                if diff > 0:
                    # We overestimated, release the difference
                    await limiter.release(diff)
                elif diff < 0:
                    # We underestimated, record the overage
                    # acquire(abs(diff))
                    await limiter.acquire(abs(diff))

    async def _rollback(self, acquired: List[Tuple[BaseRateLimiter, int]]) -> None:
        """Rollback acquired limiters."""
        for limiter, tokens in reversed(acquired):
            await limiter.release(tokens)

    def _get_tokens_for_limiter(self, limiter: BaseRateLimiter, request: QueueRequest) -> int:
        """Calculate required tokens for a specific limiter."""
        limiter_type = getattr(limiter, "rate_limiter_type", None)
        
        if not limiter_type:
            # Default to 1 if type not set (safe fallback for request/concurrent)
            return 1

        if limiter_type in (RateLimiterType.RPM, RateLimiterType.RPD, RateLimiterType.CONCURRENT):
            return 1
        
        est_input = request.estimated_input_tokens or 0
        est_output = request.estimated_output_tokens or 0

        if limiter_type in (RateLimiterType.TPM, RateLimiterType.TPD):
            return est_input + est_output
        elif limiter_type == RateLimiterType.ITPM:
            return est_input
        elif limiter_type == RateLimiterType.OTPM:
            return est_output
            
        return 1
