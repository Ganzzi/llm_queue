"""Tests for the QueueManager class."""

import asyncio
import pytest

from llm_queue import (
    QueueManager,
    ModelConfig,
    QueueRequest,
    ModelNotRegistered,
)


class TestQueueManagerBasics:
    """Basic QueueManager functionality tests."""

    @pytest.mark.asyncio
    async def test_singleton_pattern(self):
        """Test that QueueManager is a singleton."""
        manager1 = QueueManager()
        manager2 = QueueManager()

        assert manager1 is manager2

        QueueManager.reset_instance()

    @pytest.mark.asyncio
    async def test_register_queue(self, queue_manager, sample_model_config, simple_processor):
        """Test registering a single queue."""
        await queue_manager.register_queue(sample_model_config, simple_processor)

        assert "test-model" in queue_manager.get_registered_models()

    @pytest.mark.asyncio
    async def test_register_duplicate_fails(
        self, queue_manager, sample_model_config, simple_processor
    ):
        """Test that registering duplicate model fails."""
        await queue_manager.register_queue(sample_model_config, simple_processor)

        with pytest.raises(ValueError, match="already registered"):
            await queue_manager.register_queue(sample_model_config, simple_processor)

    @pytest.mark.asyncio
    async def test_register_all_queues(
        self, queue_manager, multiple_model_configs, simple_processor
    ):
        """Test registering multiple queues at once."""
        await queue_manager.register_all_queues(multiple_model_configs, simple_processor)

        registered = queue_manager.get_registered_models()
        assert len(registered) == 3
        assert "model-1" in registered
        assert "model-2" in registered
        assert "model-3" in registered


class TestQueueManagerRequests:
    """Tests for request submission and processing."""

    @pytest.mark.asyncio
    async def test_submit_request(self, queue_manager, sample_model_config, simple_processor):
        """Test submitting a request."""
        await queue_manager.register_queue(sample_model_config, simple_processor)

        request = QueueRequest(model_id="test-model", params={"test": True})
        response = await queue_manager.submit_request(request)

        assert response.status == "completed"
        assert response.result["success"] is True

    @pytest.mark.asyncio
    async def test_submit_to_unregistered_model(self, queue_manager):
        """Test submitting to unregistered model fails."""
        request = QueueRequest(model_id="unknown-model", params={"test": True})

        with pytest.raises(ModelNotRegistered, match="not registered"):
            await queue_manager.submit_request(request)

    @pytest.mark.asyncio
    async def test_submit_to_multiple_models(
        self, queue_manager, multiple_model_configs, simple_processor
    ):
        """Test submitting requests to multiple models."""
        await queue_manager.register_all_queues(multiple_model_configs, simple_processor)

        # Submit to each model
        requests = [
            QueueRequest(model_id="model-1", params={"req": 1}),
            QueueRequest(model_id="model-2", params={"req": 2}),
            QueueRequest(model_id="model-3", params={"req": 3}),
        ]

        import asyncio

        responses = await asyncio.gather(*[queue_manager.submit_request(req) for req in requests])

        assert len(responses) == 3
        assert all(r.status == "completed" for r in responses)
        assert responses[0].model_id == "model-1"
        assert responses[1].model_id == "model-2"
        assert responses[2].model_id == "model-3"


class TestQueueManagerWaitForCompletion:
    """Tests for wait_for_completion feature in manager."""

    @pytest.mark.asyncio
    async def test_submit_request_wait_for_completion_false(
        self, queue_manager, sample_model_config, simple_processor
    ):
        """Test submitting request with wait_for_completion=False."""
        await queue_manager.register_queue(sample_model_config, simple_processor)

        request = QueueRequest(
            model_id="test-model", params={"test": True}, wait_for_completion=False
        )
        response = await queue_manager.submit_request(request)

        # Should return immediately with PENDING status
        assert response.status == "pending"
        assert response.result is None

        # Wait for completion and check status
        await asyncio.sleep(0.1)
        status = await queue_manager.get_status("test-model", response.request_id)
        # Completed requests are now stored in history
        assert status is not None
        assert status.status == "completed"


class TestQueueManagerStatus:
    """Tests for status tracking."""

    @pytest.mark.asyncio
    async def test_get_status(self, queue_manager, sample_model_config, simple_processor):
        """Test getting request status."""
        await queue_manager.register_queue(sample_model_config, simple_processor)

        request = QueueRequest(model_id="test-model", params={"test": True})
        response = await queue_manager.submit_request(request)

        # Status after completion should return status (request stored in history)
        status = await queue_manager.get_status("test-model", request.id)
        assert status is not None
        assert status.status == "completed"

    @pytest.mark.asyncio
    async def test_get_status_unregistered_model(self, queue_manager):
        """Test getting status for unregistered model fails."""
        with pytest.raises(ModelNotRegistered):
            await queue_manager.get_status("unknown-model", "some-id")

    @pytest.mark.asyncio
    async def test_get_queue_info(self, queue_manager, sample_model_config, simple_processor):
        """Test getting queue information."""
        await queue_manager.register_queue(sample_model_config, simple_processor)

        info = queue_manager.get_queue_info("test-model")

        assert info["model_id"] == "test-model"
        assert "rate_limiters" in info
        assert len(info["rate_limiters"]) > 0
        assert "queue_size" in info
        assert "rate_limiter_usage" in info

    @pytest.mark.asyncio
    async def test_get_all_queues_info(
        self, queue_manager, multiple_model_configs, simple_processor
    ):
        """Test getting information for all queues."""
        await queue_manager.register_all_queues(multiple_model_configs, simple_processor)

        all_info = queue_manager.get_all_queues_info()

        assert len(all_info) == 3
        assert "model-1" in all_info
        assert "model-2" in all_info
        assert "model-3" in all_info


class TestQueueManagerShutdown:
    """Tests for manager shutdown."""

    @pytest.mark.asyncio
    async def test_shutdown_all(self, queue_manager, multiple_model_configs, simple_processor):
        """Test shutting down all queues."""
        await queue_manager.register_all_queues(multiple_model_configs, simple_processor)

        assert len(queue_manager.get_registered_models()) == 3

        await queue_manager.shutdown_all()

        assert len(queue_manager.get_registered_models()) == 0

    @pytest.mark.asyncio
    async def test_reset_instance(self):
        """Test resetting the singleton instance."""
        manager1 = QueueManager()
        QueueManager.reset_instance()
        manager2 = QueueManager()

        # After reset, new instance should be created
        # (though they'll be the same singleton after reset)
        assert manager1 is not manager2 or not manager1._initialized

        QueueManager.reset_instance()
