"""Tests for the Queue class."""

import asyncio
import pytest

from llm_queue import Queue, QueueRequest, RateLimiterMode, RequestStatus


class TestQueueBasics:
    """Basic queue functionality tests."""

    @pytest.mark.asyncio
    async def test_initialization(self, simple_processor):
        """Test queue initialization."""
        queue = Queue(
            model_id="test-model",
            rate_limit=10,
            processor_func=simple_processor,
            rate_limiter_mode=RateLimiterMode.REQUESTS_PER_PERIOD,
            time_period=60,
        )

        assert queue.model_id == "test-model"
        # Updated for V2: access chain
        assert queue.rate_limiter_chain.limiters[0].limit == 10
        assert queue.get_queue_size() == 0

        await queue.shutdown()

    @pytest.mark.asyncio
    async def test_update_token_usage(self, simple_processor):
        """Test updating token usage."""
        queue = Queue(
            model_id="test-model", rate_limit=10, processor_func=simple_processor, time_period=60
        )

        request = QueueRequest(
            model_id="test-model",
            params={"test": True},
            estimated_input_tokens=100,
            estimated_output_tokens=0,
        )
        await queue.enqueue(request)

        # Update usage
        await queue.update_token_usage(request.id, 50, 10)

        # Check status has updated tokens
        status = await queue.get_status(request.id)
        assert status.input_tokens_used == 50
        assert status.output_tokens_used == 10

        await queue.shutdown()

    @pytest.mark.asyncio
    async def test_enqueue_and_process(self, simple_processor):
        """Test enqueuing and processing a request."""
        queue = Queue(
            model_id="test-model", rate_limit=10, processor_func=simple_processor, time_period=60
        )

        request = QueueRequest(model_id="test-model", params={"test": True})
        response = await queue.enqueue(request)

        assert response.status == RequestStatus.COMPLETED
        assert response.result["success"] is True
        assert response.request_id == request.id
        assert response.processing_time is not None

        await queue.shutdown()

    @pytest.mark.asyncio
    async def test_multiple_requests(self, simple_processor):
        """Test processing multiple requests."""
        queue = Queue(
            model_id="test-model", rate_limit=10, processor_func=simple_processor, time_period=60
        )

        requests = [
            QueueRequest(model_id="test-model", params={"request_num": i}) for i in range(5)
        ]

        responses = await asyncio.gather(*[queue.enqueue(req) for req in requests])

        assert len(responses) == 5
        assert all(r.status == RequestStatus.COMPLETED for r in responses)

        await queue.shutdown()

    @pytest.mark.asyncio
    async def test_failed_request(self, failing_processor):
        """Test handling of failed requests."""
        queue = Queue(
            model_id="test-model", rate_limit=10, processor_func=failing_processor, time_period=60
        )

        request = QueueRequest(model_id="test-model", params={"test": "fail"})
        response = await queue.enqueue(request)

        assert response.status == RequestStatus.FAILED
        assert response.error is not None
        assert "Test error" in response.error

        await queue.shutdown()


class TestQueueRateLimiting:
    """Tests for rate limiting behavior."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_requests_per_period_limiting(self):
        """Test that requests per period is enforced."""

        async def slow_processor(request: QueueRequest[dict]) -> dict:
            await asyncio.sleep(0.05)
            return {"done": True}

        queue = Queue(
            model_id="test-model",
            rate_limit=3,
            processor_func=slow_processor,
            rate_limiter_mode=RateLimiterMode.REQUESTS_PER_PERIOD,
            time_period=1,
        )

        # Submit 5 requests
        requests = [QueueRequest(model_id="test-model", params={"req_id": i}) for i in range(5)]

        import time

        start = time.time()
        responses = await asyncio.gather(*[queue.enqueue(req) for req in requests])
        elapsed = time.time() - start

        # All should complete
        assert all(r.status == RequestStatus.COMPLETED for r in responses)

        # Should take at least 1 second (rate limit window)
        # First 3 go immediately, next 2 wait for window
        assert elapsed >= 1.0

        await queue.shutdown()

    @pytest.mark.asyncio
    async def test_concurrent_limiting(self):
        """Test concurrent request limiting."""
        processing_count = {"value": 0, "max": 0}

        async def tracking_processor(request: QueueRequest[dict]) -> dict:
            processing_count["value"] += 1
            processing_count["max"] = max(processing_count["max"], processing_count["value"])
            await asyncio.sleep(0.1)
            processing_count["value"] -= 1
            return {"done": True}

        queue = Queue(
            model_id="test-model",
            rate_limit=2,
            processor_func=tracking_processor,
            rate_limiter_mode=RateLimiterMode.CONCURRENT_REQUESTS,
        )

        # Submit 5 requests
        requests = [QueueRequest(model_id="test-model", params={"req_id": i}) for i in range(5)]
        responses = await asyncio.gather(*[queue.enqueue(req) for req in requests])

        # All should complete
        assert all(r.status == RequestStatus.COMPLETED for r in responses)

        # Max concurrent should not exceed limit
        assert processing_count["max"] <= 2

        await queue.shutdown()


class TestQueueWaitForCompletion:
    """Tests for wait_for_completion feature."""

    @pytest.mark.asyncio
    async def test_wait_for_completion_false(self, simple_processor):
        """Test that wait_for_completion=False returns immediately with PENDING status."""
        queue = Queue(
            model_id="test-model", rate_limit=10, processor_func=simple_processor, time_period=60
        )

        request = QueueRequest(
            model_id="test-model", params={"test": True}, wait_for_completion=False
        )
        response = await queue.enqueue(request)

        # Should return immediately with PENDING status
        assert response.status == RequestStatus.PENDING
        assert response.result is None  # No result yet
        assert response.request_id == request.id

        # Wait a bit for processing to complete
        await asyncio.sleep(0.1)

        # For fire-and-forget requests, status IS available after completion (history)
        status = await queue.get_status(request.id)
        assert status is not None
        assert status.status == RequestStatus.COMPLETED

        await queue.shutdown()

    @pytest.mark.asyncio
    async def test_wait_for_completion_true_default(self, simple_processor):
        """Test that wait_for_completion=True (default) waits for completion."""
        queue = Queue(
            model_id="test-model", rate_limit=10, processor_func=simple_processor, time_period=60
        )

        request = QueueRequest(
            model_id="test-model", params={"test": True}
        )  # wait_for_completion defaults to True
        response = await queue.enqueue(request)

        # Should wait and return completed status
        assert response.status == RequestStatus.COMPLETED
        assert response.result["success"] is True
        assert response.request_id == request.id

        await queue.shutdown()


class TestQueueStatus:
    """Tests for queue status tracking."""

    @pytest.mark.asyncio
    async def test_get_status_pending(self):
        """Test getting status of a pending request."""

        async def slow_processor(request: QueueRequest[dict]) -> dict:
            await asyncio.sleep(1)
            return {"done": True}

        queue = Queue(
            model_id="test-model", rate_limit=1, processor_func=slow_processor, time_period=60
        )

        request = QueueRequest(model_id="test-model", params={"slow": True})

        # Submit but don't await
        task = asyncio.create_task(queue.enqueue(request))

        # Give it a moment to be queued
        await asyncio.sleep(0.05)

        # Check status
        status = await queue.get_status(request.id)
        assert status is not None
        assert status.status in [RequestStatus.PENDING, RequestStatus.PROCESSING]

        # Wait for completion
        await task

        await queue.shutdown()

    @pytest.mark.asyncio
    async def test_get_status_nonexistent(self, simple_processor):
        """Test getting status of non-existent request."""
        queue = Queue(
            model_id="test-model", rate_limit=10, processor_func=simple_processor, time_period=60
        )

        status = await queue.get_status("nonexistent-id")
        assert status is None

        await queue.shutdown()

    @pytest.mark.asyncio
    async def test_queue_metrics(self, simple_processor):
        """Test queue size and usage metrics."""
        queue = Queue(
            model_id="test-model", rate_limit=10, processor_func=simple_processor, time_period=60
        )

        assert queue.get_queue_size() == 0
        assert queue.get_rate_limiter_usage() == 0

        # Process a request
        request = QueueRequest(model_id="test-model", params={"test": True})
        await queue.enqueue(request)

        # After processing, queue should be empty again
        assert queue.get_queue_size() == 0

        await queue.shutdown()


class TestQueueShutdown:
    """Tests for queue shutdown."""

    @pytest.mark.asyncio
    async def test_graceful_shutdown(self):
        """Test graceful shutdown waits for pending requests."""
        completed = []

        async def processor(request: QueueRequest[dict]) -> dict:
            await asyncio.sleep(0.1)
            completed.append(request.id)
            return {"done": True}

        queue = Queue(
            model_id="test-model", rate_limit=10, processor_func=processor, time_period=60
        )

        # Submit requests
        requests = [QueueRequest(model_id="test-model", params={"req_id": i}) for i in range(3)]
        tasks = [asyncio.create_task(queue.enqueue(req)) for req in requests]

        # Give them a moment to start
        await asyncio.sleep(0.05)

        # Shutdown should wait for completion
        await queue.shutdown()

        # All tasks should complete
        responses = await asyncio.gather(*tasks)
        assert all(r.status == RequestStatus.COMPLETED for r in responses)
        assert len(completed) == 3
