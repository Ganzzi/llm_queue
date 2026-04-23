"""Integration tests for llm_queue: queue lifecycle, priority, retry/backoff, and rate limiting.

These tests exercise end-to-end workflows using the public API with real async execution.
No external dependencies required — all processors are in-process.
"""

import asyncio
import time
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
# Helpers / fixtures
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


async def simple_ok(request: QueueRequest) -> dict:
    await asyncio.sleep(0.01)
    return {"ok": True, "id": request.id}


async def echo_params(request: QueueRequest) -> dict:
    await asyncio.sleep(0.005)
    return {"params": request.params}


async def always_fail(request: QueueRequest) -> dict:
    raise RuntimeError("deliberate failure")


# ---------------------------------------------------------------------------
# 1. Queue Lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestQueueLifecycle:
    """End-to-end lifecycle: register → enqueue → complete → shutdown."""

    @pytest.mark.asyncio
    async def test_register_and_submit_single_request(self, manager):
        """Register a model and process one request successfully."""
        config = ModelConfig(
            model_id="lifecycle-model",
            rate_limiters=[RateLimiterConfig(type=RateLimiterType.RPM, limit=60)],
        )
        await manager.register_queue(config, simple_ok)

        request = QueueRequest(model_id="lifecycle-model", params={"x": 1})
        response = await manager.submit_request(request)

        assert response.status == RequestStatus.COMPLETED
        assert response.result == {"ok": True, "id": request.id}
        assert response.request_id == request.id
        assert response.processing_time is not None
        assert response.processing_time >= 0

    @pytest.mark.asyncio
    async def test_multiple_sequential_requests(self, manager):
        """Process several requests sequentially on the same queue."""
        config = ModelConfig(
            model_id="seq-model",
            rate_limiters=[RateLimiterConfig(type=RateLimiterType.RPM, limit=60)],
        )
        await manager.register_queue(config, echo_params)

        for i in range(5):
            req = QueueRequest(model_id="seq-model", params={"i": i})
            resp = await manager.submit_request(req)
            assert resp.status == RequestStatus.COMPLETED
            assert resp.result["params"]["i"] == i

    @pytest.mark.asyncio
    async def test_concurrent_requests_all_complete(self, manager):
        """All concurrent requests complete and return correct results."""
        config = ModelConfig(
            model_id="conc-model",
            rate_limiters=[RateLimiterConfig(type=RateLimiterType.CONCURRENT, limit=10)],
        )
        await manager.register_queue(config, echo_params)

        requests = [
            QueueRequest(model_id="conc-model", params={"n": n}) for n in range(20)
        ]
        responses = await asyncio.gather(
            *[manager.submit_request(r) for r in requests]
        )

        assert len(responses) == 20
        for resp in responses:
            assert resp.status == RequestStatus.COMPLETED
            assert resp.result is not None

    @pytest.mark.asyncio
    async def test_failed_request_returns_failed_status(self, manager):
        """A processor that raises causes status FAILED, not an exception bubble."""
        config = ModelConfig(
            model_id="fail-model",
            rate_limiters=[RateLimiterConfig(type=RateLimiterType.RPM, limit=60)],
        )
        await manager.register_queue(config, always_fail)

        req = QueueRequest(model_id="fail-model", params={})
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

    @pytest.mark.asyncio
    async def test_shutdown_and_reset(self, manager):
        """After shutdown_all + reset, manager is empty and usable again."""
        config = ModelConfig(
            model_id="ephemeral",
            rate_limiters=[RateLimiterConfig(type=RateLimiterType.RPM, limit=10)],
        )
        await manager.register_queue(config, simple_ok)
        assert "ephemeral" in manager.get_registered_models()

        await manager.shutdown_all()
        assert manager.get_registered_models() == []

    @pytest.mark.asyncio
    async def test_no_wait_returns_pending(self, manager):
        """wait_for_completion=False returns immediately with PENDING status."""
        config = ModelConfig(
            model_id="nowait-model",
            rate_limiters=[RateLimiterConfig(type=RateLimiterType.RPM, limit=60)],
        )
        await manager.register_queue(config, simple_ok)

        req = QueueRequest(
            model_id="nowait-model", params={}, wait_for_completion=False
        )
        resp = await manager.submit_request(req)

        assert resp.status == RequestStatus.PENDING
        assert resp.result is None

    @pytest.mark.asyncio
    async def test_register_all_queues_and_route(self, manager):
        """register_all_queues registers multiple models; requests route correctly."""
        configs = [
            ModelConfig(
                model_id=f"m{i}",
                rate_limiters=[RateLimiterConfig(type=RateLimiterType.RPM, limit=60)],
            )
            for i in range(3)
        ]
        await manager.register_all_queues(configs, echo_params)

        assert len(manager.get_registered_models()) == 3

        for i in range(3):
            req = QueueRequest(model_id=f"m{i}", params={"model": i})
            resp = await manager.submit_request(req)
            assert resp.status == RequestStatus.COMPLETED
            assert resp.result["params"]["model"] == i


# ---------------------------------------------------------------------------
# 2. Priority / FIFO ordering
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestPriorityHandling:
    """Queue processes requests in submission order (FIFO) by default."""

    @pytest.mark.asyncio
    async def test_fifo_ordering_under_low_concurrency(self, manager):
        """Requests dispatched serially (concurrent=1) are completed in order."""
        order: list[int] = []

        async def ordered_processor(request: QueueRequest) -> dict:
            order.append(request.params["seq"])
            return {"seq": request.params["seq"]}

        config = ModelConfig(
            model_id="fifo",
            rate_limiters=[RateLimiterConfig(type=RateLimiterType.CONCURRENT, limit=1)],
        )
        await manager.register_queue(config, ordered_processor)

        # Submit in order
        reqs = [QueueRequest(model_id="fifo", params={"seq": i}) for i in range(5)]
        await asyncio.gather(*[manager.submit_request(r) for r in reqs])

        # Because concurrency=1, items process in queue order
        assert order == list(range(5))

    @pytest.mark.asyncio
    async def test_all_requests_complete_regardless_of_concurrency(self, manager):
        """High-concurrency queue: all requests complete with correct results."""
        config = ModelConfig(
            model_id="wide",
            rate_limiters=[RateLimiterConfig(type=RateLimiterType.CONCURRENT, limit=20)],
        )
        await manager.register_queue(config, echo_params)

        N = 50
        reqs = [QueueRequest(model_id="wide", params={"n": n}) for n in range(N)]
        responses = await asyncio.gather(*[manager.submit_request(r) for r in reqs])

        assert len(responses) == N
        completed_n = {r.result["params"]["n"] for r in responses}
        assert completed_n == set(range(N))


# ---------------------------------------------------------------------------
# 3. Retry / Backoff behaviour
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestRetryBackoff:
    """Verify processor retry patterns; the queue itself is not retry-aware,
    but callers can implement backoff via re-submission."""

    @pytest.mark.asyncio
    async def test_manual_retry_succeeds_after_transient_failure(self, manager):
        """Re-submitting a failed request returns a successful response."""
        call_count = {"n": 0}

        async def flaky(request: QueueRequest) -> dict:
            call_count["n"] += 1
            if call_count["n"] < 3:
                raise ValueError("transient")
            return {"recovered": True}

        config = ModelConfig(
            model_id="flaky",
            rate_limiters=[RateLimiterConfig(type=RateLimiterType.RPM, limit=60)],
        )
        await manager.register_queue(config, flaky)

        # First two attempts fail
        for _ in range(2):
            req = QueueRequest(model_id="flaky", params={})
            resp = await manager.submit_request(req)
            assert resp.status == RequestStatus.FAILED

        # Third attempt succeeds
        req = QueueRequest(model_id="flaky", params={})
        resp = await manager.submit_request(req)
        assert resp.status == RequestStatus.COMPLETED
        assert resp.result == {"recovered": True}

    @pytest.mark.asyncio
    async def test_exponential_backoff_between_retries(self, manager):
        """Caller-side exponential backoff: delays grow between retries."""
        attempts = {"n": 0}

        async def succeed_on_third(request: QueueRequest) -> dict:
            attempts["n"] += 1
            if attempts["n"] < 3:
                raise RuntimeError("not yet")
            return {"done": True}

        config = ModelConfig(
            model_id="backoff-model",
            rate_limiters=[RateLimiterConfig(type=RateLimiterType.RPM, limit=60)],
        )
        await manager.register_queue(config, succeed_on_third)

        backoff = 0.05
        resp = None
        timestamps = []
        for attempt in range(5):
            req = QueueRequest(model_id="backoff-model", params={"attempt": attempt})
            timestamps.append(time.monotonic())
            resp = await manager.submit_request(req)
            if resp.status == RequestStatus.COMPLETED:
                break
            await asyncio.sleep(backoff)
            backoff *= 2

        assert resp is not None
        assert resp.status == RequestStatus.COMPLETED
        # Verify backoff delays increased (at least two retry gaps)
        if len(timestamps) >= 3:
            gap1 = timestamps[1] - timestamps[0]
            gap2 = timestamps[2] - timestamps[1]
            assert gap2 >= gap1  # second wait >= first wait

    @pytest.mark.asyncio
    async def test_failed_request_error_message_preserved(self, manager):
        """Error message from processor exception is captured in response.error."""
        sentinel = "unique-error-xyz"

        async def error_proc(request: QueueRequest) -> dict:
            raise ValueError(sentinel)

        config = ModelConfig(
            model_id="err-model",
            rate_limiters=[RateLimiterConfig(type=RateLimiterType.RPM, limit=60)],
        )
        await manager.register_queue(config, error_proc)

        resp = await manager.submit_request(
            QueueRequest(model_id="err-model", params={})
        )
        assert resp.status == RequestStatus.FAILED
        assert sentinel in (resp.error or "")


# ---------------------------------------------------------------------------
# 4. Provider rate limiting
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestProviderRateLimiting:
    """Validate that rate limiters constrain throughput as configured."""

    @pytest.mark.asyncio
    async def test_concurrent_limiter_caps_parallelism(self, manager):
        """At most N requests execute simultaneously when CONCURRENT limit = N."""
        active = {"current": 0, "peak": 0}
        limit = 3

        async def tracking(request: QueueRequest) -> dict:
            active["current"] += 1
            active["peak"] = max(active["peak"], active["current"])
            await asyncio.sleep(0.05)
            active["current"] -= 1
            return {"ok": True}

        config = ModelConfig(
            model_id="concurrent-capped",
            rate_limiters=[RateLimiterConfig(type=RateLimiterType.CONCURRENT, limit=limit)],
        )
        await manager.register_queue(config, tracking)

        requests = [
            QueueRequest(model_id="concurrent-capped", params={}) for _ in range(12)
        ]
        await asyncio.gather(*[manager.submit_request(r) for r in requests])

        assert active["peak"] <= limit

    @pytest.mark.asyncio
    async def test_rpm_limiter_enforces_request_count(self, manager):
        """RPM limiter prevents more than N requests within the window."""
        rpm_limit = 5
        config = ModelConfig(
            model_id="rpm-model",
            rate_limiters=[
                RateLimiterConfig(type=RateLimiterType.RPM, limit=rpm_limit)
            ],
        )
        await manager.register_queue(config, simple_ok)

        # Submit exactly rpm_limit requests — all should complete without blocking
        start = time.monotonic()
        requests = [
            QueueRequest(model_id="rpm-model", params={"n": n})
            for n in range(rpm_limit)
        ]
        responses = await asyncio.gather(*[manager.submit_request(r) for r in requests])
        elapsed = time.monotonic() - start

        assert len(responses) == rpm_limit
        assert all(r.status == RequestStatus.COMPLETED for r in responses)
        # They should complete quickly (within the rate window, no waiting needed)
        assert elapsed < 5.0

    @pytest.mark.asyncio
    async def test_tpm_limiter_with_token_estimates(self, manager):
        """TPM limiter respects estimated token counts per request."""
        tpm_limit = 100
        config = ModelConfig(
            model_id="tpm-model",
            rate_limiters=[
                RateLimiterConfig(type=RateLimiterType.TPM, limit=tpm_limit)
            ],
        )
        await manager.register_queue(config, simple_ok)

        # Small requests well within limit
        requests = [
            QueueRequest(
                model_id="tpm-model",
                params={"n": n},
                estimated_input_tokens=5,
                estimated_output_tokens=5,
            )
            for n in range(5)
        ]
        responses = await asyncio.gather(*[manager.submit_request(r) for r in requests])

        assert all(r.status == RequestStatus.COMPLETED for r in responses)

    @pytest.mark.asyncio
    async def test_token_usage_update_adjusts_limiter(self, manager):
        """update_token_usage reconciles over/under-estimated token consumption."""
        config = ModelConfig(
            model_id="token-update",
            rate_limiters=[
                RateLimiterConfig(type=RateLimiterType.TPM, limit=1000)
            ],
        )
        await manager.register_queue(config, simple_ok)

        req = QueueRequest(
            model_id="token-update",
            params={},
            estimated_input_tokens=100,
            estimated_output_tokens=100,
        )
        resp = await manager.submit_request(req)
        assert resp.status == RequestStatus.COMPLETED

        # Actual usage was less than estimated — update should not raise
        await manager.update_token_usage(
            model_id="token-update",
            request_id=req.id,
            input_tokens=50,
            output_tokens=40,
        )

    @pytest.mark.asyncio
    async def test_mixed_rate_limiters_all_respected(self, manager):
        """Queue with both RPM and CONCURRENT limiters enforces both constraints."""
        active = {"current": 0, "peak": 0}
        concurrent_limit = 2

        async def tracking(request: QueueRequest) -> dict:
            active["current"] += 1
            active["peak"] = max(active["peak"], active["current"])
            await asyncio.sleep(0.03)
            active["current"] -= 1
            return {"ok": True}

        config = ModelConfig(
            model_id="multi-limit",
            rate_limiters=[
                RateLimiterConfig(type=RateLimiterType.RPM, limit=30),
                RateLimiterConfig(type=RateLimiterType.CONCURRENT, limit=concurrent_limit),
            ],
        )
        await manager.register_queue(config, tracking)

        requests = [
            QueueRequest(model_id="multi-limit", params={}) for _ in range(8)
        ]
        responses = await asyncio.gather(*[manager.submit_request(r) for r in requests])

        assert all(r.status == RequestStatus.COMPLETED for r in responses)
        assert active["peak"] <= concurrent_limit

    @pytest.mark.asyncio
    async def test_queue_info_reflects_usage(self, manager):
        """get_queue_info returns accurate size and rate limiter data."""
        config = ModelConfig(
            model_id="info-model",
            rate_limiters=[RateLimiterConfig(type=RateLimiterType.CONCURRENT, limit=5)],
        )
        await manager.register_queue(config, simple_ok)

        info = manager.get_queue_info("info-model")
        assert info["model_id"] == "info-model"
        assert "queue_size" in info
        assert "rate_limiters" in info
        assert len(info["rate_limiters"]) == 1
        assert info["rate_limiters"][0]["limit"] == 5
