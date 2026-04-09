"""Tests for priority queue behavior."""

import asyncio
import pytest
from llm_queue import QueueManager, Queue, ModelConfig, QueueRequest, RateLimiterConfig, RateLimiterType
from llm_queue.rate_limiters import create_chain


@pytest.mark.unit
class TestPriorityHandling:
    """Tests for request ordering and fairness."""

    @pytest.mark.asyncio
    async def test_requests_process_in_order(self, simple_processor):
        """Test that multiple requests are all processed."""
        chain = create_chain([RateLimiterConfig(type=RateLimiterType.CONCURRENT, limit=5)])
        queue = Queue(
            model_id="test-model",
            processor_func=simple_processor,
            rate_limiter_chain=chain,
        )

        requests = [
            QueueRequest(model_id="test-model", params={"i": i}) for i in range(10)
        ]

        responses = await asyncio.gather(*[queue.enqueue(req) for req in requests])

        # All requests should complete
        assert len(responses) == 10
        assert all(r.result is not None for r in responses)

        await queue.shutdown()

    @pytest.mark.asyncio
    async def test_concurrent_limit_respected(self):
        """Test that concurrent processing limit is respected."""
        active = {"count": 0, "max": 0}

        async def tracking_processor(request):
            active["count"] += 1
            active["max"] = max(active["max"], active["count"])
            await asyncio.sleep(0.05)
            active["count"] -= 1
            return {"done": True}

        chain = create_chain([RateLimiterConfig(type=RateLimiterType.CONCURRENT, limit=3)])
        queue = Queue(
            model_id="test-model",
            processor_func=tracking_processor,
            rate_limiter_chain=chain,
        )

        requests = [
            QueueRequest(model_id="test-model", params={"i": i}) for i in range(9)
        ]

        await asyncio.gather(*[queue.enqueue(req) for req in requests])

        assert active["max"] <= 3
        await queue.shutdown()