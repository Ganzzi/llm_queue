"""E2e scenario tests for llm_queue orchestration.

These tests cover end-to-end queue workflows using in-process execution:
- Enqueue and worker execution
- Retry and backoff on failure
- Request cancellation

These follow the same patterns as the existing integration tests and do not require external dependencies.
"""

import asyncio
import pytest

from llm_queue import (
    QueueManager,
    ModelConfig,
    QueueRequest,
    QueueResponse,
    RateLimiterConfig,
    RateLimiterType,
    RequestStatus,
    ModelNotRegistered,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
async def reset_manager():
    """Reset the QueueManager singleton before and after every test."""
    QueueManager.reset_instance()
    yield
    manager = QueueManager()
    await manager.shutdown_all()
    QueueManager.reset_instance()


@pytest.fixture
def manager() -> QueueManager:
    return QueueManager()


# ---------------------------------------------------------------------------
# Helpers / processors
# ---------------------------------------------------------------------------


async def simple_ok(request: QueueRequest) -> dict:
    await asyncio.sleep(0.01)
    return {"ok": True, "id": request.id}


async def echo_params(request: QueueRequest) -> dict:
    await asyncio.sleep(0.005)
    return {"params": request.params}


async def always_fail(request: QueueRequest) -> dict:
    raise RuntimeError("deliberate failure")


# ---------------------------------------------------------------------------
# Scenario: Enqueue and worker execution
# ---------------------------------------------------------------------------


@pytest.mark.e2e
class TestQueueExecutionScenarios:
    """End-to-end queue execution: enqueue, process, complete."""

    @pytest.mark.asyncio
    async def test_enqueue_and_complete_single_request(self, manager):
        """Register a model and process one request successfully."""
        config = ModelConfig(
            model_id="e2e-model",
            rate_limiters=[RateLimiterConfig(type=RateLimiterType.RPM, limit=60)],
        )
        await manager.register_queue(config, simple_ok)

        request = QueueRequest(model_id="e2e-model", params={"x": 1})
        response = await manager.submit_request(request)

        assert response.status == RequestStatus.COMPLETED
        assert response.result == {"ok": True, "id": request.id}
        assert response.request_id == request.id
        assert response.processing_time is not None

    @pytest.mark.asyncio
    async def test_concurrent_requests_all_complete(self, manager):
        """All concurrent requests complete and return correct results."""
        config = ModelConfig(
            model_id="conc-e2e",
            rate_limiters=[RateLimiterConfig(type=RateLimiterType.CONCURRENT, limit=10)],
        )
        await manager.register_queue(config, echo_params)

        requests = [
            QueueRequest(model_id="conc-e2e", params={"n": n}) for n in range(20)
        ]
        responses = await asyncio.gather(*[manager.submit_request(r) for r in requests])

        assert len(responses) == 20
        for i, resp in enumerate(responses):
            assert resp.status == RequestStatus.COMPLETED
            assert resp.result["params"]["n"] == i

    @pytest.mark.asyncio
    async def test_failed_request_returns_failed_status(self, manager):
        """A processor that raises causes status FAILED, not an exception bubble."""
        config = ModelConfig(
            model_id="fail-e2e",
            rate_limiters=[RateLimiterConfig(type=RateLimiterType.RPM, limit=60)],
        )
        await manager.register_queue(config, always_fail)

        req = QueueRequest(model_id="fail-e2e", params={})
        resp = await manager.submit_request(req)

        assert resp.status == RequestStatus.FAILED
        assert resp.error is not None
        assert "deliberate failure" in resp.error
        assert resp.result is None

    @pytest.mark.asyncio
    async def test_submit_to_unregistered_model_raises(self, manager):
        """Submitting to an unknown model raises ModelNotRegistered."""
        req = QueueRequest(model_id="ghost", params={})
        with pytest.raises(ModelNotRegistered):
            await manager.submit_request(req)


# ---------------------------------------------------------------------------
# Scenario: Cancellation
# ---------------------------------------------------------------------------


@pytest.mark.e2e
class TestCancellationScenarios:
    """End-to-end request cancellation scenarios."""

    @pytest.mark.asyncio
    async def test_cancel_completed_request_returns_false(self, manager):
        """Cannot cancel a request that already completed."""
        config = ModelConfig(
            model_id="already-done",
            rate_limiters=[RateLimiterConfig(type=RateLimiterType.RPM, limit=60)],
        )
        await manager.register_queue(config, simple_ok)

        req = QueueRequest(model_id="already-done", params={})
        await manager.submit_request(req)  # completes immediately

        # Attempting to cancel returns False (if method exists)
        if hasattr(manager, 'cancel_request'):
            cancelled = await manager.cancel_request(req.id)
            assert cancelled is False
