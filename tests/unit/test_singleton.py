"""Tests for singleton manager behavior."""

import asyncio
import pytest
from llm_queue import QueueManager, ModelConfig, RateLimiterConfig, RateLimiterType


@pytest.mark.unit
class TestSingletonPattern:
    """Tests for singleton behavior of QueueManager."""

    def test_get_same_instance(self):
        """Test that multiple instantiations return same instance."""
        QueueManager.reset_instance()

        m1 = QueueManager()
        m2 = QueueManager()

        assert m1 is m2
        QueueManager.reset_instance()

    def test_reset_clears_instance(self):
        """Test that reset clears the singleton."""
        m1 = QueueManager()
        QueueManager.reset_instance()
        m2 = QueueManager()

        # After reset, new instance
        assert m1 is not m2
        QueueManager.reset_instance()

    @pytest.mark.asyncio
    async def test_state_is_shared(self):
        """Test that state is shared across references."""
        QueueManager.reset_instance()

        manager_ref1 = QueueManager()
        manager_ref2 = QueueManager()

        async def dummy_processor(request):
            return {"ok": True}

        config = ModelConfig(
            model_id="singleton-test",
            rate_limiters=[RateLimiterConfig(type=RateLimiterType.RPM, limit=10)]
        )

        await manager_ref1.register_queue(config, dummy_processor)

        # Should see the model registered through ref2
        assert "singleton-test" in manager_ref2.get_registered_models()

        await manager_ref1.shutdown_all()
        QueueManager.reset_instance()

    def test_initialized_flag(self):
        """Test _initialized flag prevents double initialization."""
        QueueManager.reset_instance()

        m = QueueManager()
        assert m._initialized is True

        # Second instantiation should be same object with same flag
        m2 = QueueManager()
        assert m2._initialized is True
        assert m is m2

        QueueManager.reset_instance()