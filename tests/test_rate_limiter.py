"""Tests for the RateLimiter class."""

import asyncio
import pytest
import time

from llm_queue import RateLimiter, RateLimiterMode


class TestRateLimiterRequestsPerPeriod:
    """Tests for REQUESTS_PER_PERIOD mode."""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(limit=10, mode=RateLimiterMode.REQUESTS_PER_PERIOD, time_period=60)

        assert limiter.limit == 10
        assert limiter.mode == RateLimiterMode.REQUESTS_PER_PERIOD
        assert limiter.time_period == 60
        assert len(limiter.timestamps) == 0

    @pytest.mark.asyncio
    async def test_invalid_limit(self):
        """Test initialization with invalid limit."""
        with pytest.raises(ValueError, match="limit must be greater than 0"):
            RateLimiter(limit=0)

    @pytest.mark.asyncio
    async def test_invalid_time_period(self):
        """Test initialization with invalid time period."""
        with pytest.raises(ValueError, match="time_period must be greater than 0"):
            RateLimiter(limit=10, time_period=0)

    @pytest.mark.asyncio
    async def test_acquire_within_limit(self):
        """Test acquiring slots within the limit."""
        limiter = RateLimiter(limit=5, time_period=10)

        # Should be able to acquire 5 slots
        for i in range(5):
            acquired = await limiter.acquire()
            assert acquired is True, f"Failed to acquire slot {i+1}"

        # 6th should fail
        acquired = await limiter.acquire()
        assert acquired is False

    @pytest.mark.asyncio
    async def test_acquire_after_window(self):
        """Test that slots are released after time window."""
        limiter = RateLimiter(limit=2, time_period=1)

        # Acquire 2 slots
        assert await limiter.acquire() is True
        assert await limiter.acquire() is True
        assert await limiter.acquire() is False

        # Wait for window to pass
        await asyncio.sleep(1.1)

        # Should be able to acquire again
        assert await limiter.acquire() is True

    @pytest.mark.asyncio
    async def test_wait_for_slot(self):
        """Test waiting for a slot to become available."""
        limiter = RateLimiter(limit=1, time_period=1)

        # Acquire the only slot
        await limiter.acquire()

        # Wait for slot should block briefly then succeed
        start = time.time()
        await limiter.wait_for_slot()
        elapsed = time.time() - start

        # Should have waited ~1 second
        assert 0.9 < elapsed < 1.5

    @pytest.mark.asyncio
    async def test_get_current_usage(self):
        """Test getting current usage."""
        limiter = RateLimiter(limit=5, time_period=10)

        assert limiter.get_current_usage() == 0

        await limiter.acquire()
        assert limiter.get_current_usage() == 1

        await limiter.acquire()
        await limiter.acquire()
        assert limiter.get_current_usage() == 3

    @pytest.mark.asyncio
    async def test_get_available_slots(self):
        """Test getting available slots."""
        limiter = RateLimiter(limit=5, time_period=10)

        assert limiter.get_available_slots() == 5

        await limiter.acquire()
        assert limiter.get_available_slots() == 4

        await limiter.acquire()
        await limiter.acquire()
        assert limiter.get_available_slots() == 2


class TestRateLimiterConcurrentRequests:
    """Tests for CONCURRENT_REQUESTS mode."""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test concurrent mode initialization."""
        limiter = RateLimiter(limit=5, mode=RateLimiterMode.CONCURRENT_REQUESTS)

        assert limiter.limit == 5
        assert limiter.mode == RateLimiterMode.CONCURRENT_REQUESTS
        assert hasattr(limiter, "_semaphore")

    @pytest.mark.asyncio
    async def test_acquire_within_limit(self):
        """Test acquiring within concurrent limit."""
        limiter = RateLimiter(limit=3, mode=RateLimiterMode.CONCURRENT_REQUESTS)

        # Acquire 3 slots
        assert await limiter.acquire() is True
        assert await limiter.acquire() is True
        assert await limiter.acquire() is True

        # 4th should fail
        assert await limiter.acquire() is False

    @pytest.mark.asyncio
    async def test_release(self):
        """Test releasing slots."""
        limiter = RateLimiter(limit=2, mode=RateLimiterMode.CONCURRENT_REQUESTS)

        # Acquire all slots
        assert await limiter.acquire() is True
        assert await limiter.acquire() is True
        assert await limiter.acquire() is False

        # Release one
        await limiter.release()

        # Should be able to acquire again
        assert await limiter.acquire() is True

    @pytest.mark.asyncio
    async def test_wait_for_slot(self):
        """Test waiting for a slot in concurrent mode."""
        limiter = RateLimiter(limit=1, mode=RateLimiterMode.CONCURRENT_REQUESTS)

        # Acquire the slot
        await limiter.acquire()

        # Start a task that releases after delay
        async def release_after_delay():
            await asyncio.sleep(0.5)
            await limiter.release()

        asyncio.create_task(release_after_delay())

        # Wait for slot should block until released
        start = time.time()
        await limiter.wait_for_slot()
        elapsed = time.time() - start

        # Should have waited ~0.5 seconds
        assert 0.4 < elapsed < 0.7

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test multiple concurrent operations."""
        limiter = RateLimiter(limit=2, mode=RateLimiterMode.CONCURRENT_REQUESTS)

        results = []

        async def worker(worker_id: int):
            await limiter.wait_for_slot()
            results.append(f"start-{worker_id}")
            await asyncio.sleep(0.1)
            results.append(f"end-{worker_id}")
            await limiter.release()

        # Start 4 workers, only 2 should run concurrently
        await asyncio.gather(*[worker(i) for i in range(4)])

        assert len(results) == 8


class TestRateLimiterComparison:
    """Comparison tests between modes."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_mode_performance_difference(self):
        """Test performance difference between modes."""
        # Per-period mode
        per_period = RateLimiter(limit=5, mode=RateLimiterMode.REQUESTS_PER_PERIOD, time_period=1)

        # Concurrent mode
        concurrent = RateLimiter(limit=5, mode=RateLimiterMode.CONCURRENT_REQUESTS)

        # Both should handle the same number of immediate requests
        for _ in range(5):
            assert await per_period.acquire() is True
            assert await concurrent.acquire() is True

        # Both should reject the next request
        assert await per_period.acquire() is False
        assert await concurrent.acquire() is False

        # After releasing, concurrent should allow more
        await concurrent.release()
        assert await concurrent.acquire() is True

        # Per-period needs to wait for time window
        assert await per_period.acquire() is False
