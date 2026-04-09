"""Pytest configuration and fixtures."""

import asyncio
import pytest
from typing import AsyncGenerator

from llm_queue import QueueManager, ModelConfig, QueueRequest, RateLimiterConfig, RateLimiterType


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def queue_manager() -> AsyncGenerator[QueueManager, None]:
    """Provide a fresh QueueManager instance for each test."""
    # Reset singleton before test
    QueueManager.reset_instance()
    manager = QueueManager()
    yield manager
    # Cleanup after test
    await manager.shutdown_all()
    QueueManager.reset_instance()


@pytest.fixture
async def simple_processor():
    """Provide a simple processor function for testing."""

    async def processor(request: QueueRequest[dict]) -> dict:
        """Simple test processor that returns success."""
        await asyncio.sleep(0.01)  # Simulate processing
        return {"success": True, "request_id": request.id}

    return processor


@pytest.fixture
async def failing_processor():
    """Provide a processor that always fails."""

    async def processor(request: QueueRequest[dict]) -> dict:
        """Processor that raises an exception."""
        raise ValueError("Test error")

    return processor


@pytest.fixture
def sample_model_config() -> ModelConfig:
    """Provide a sample model configuration."""
    return ModelConfig(
        model_id="test-model",
        rate_limiters=[
            RateLimiterConfig(type=RateLimiterType.RPM, limit=10),
        ],
    )


@pytest.fixture
def concurrent_model_config() -> ModelConfig:
    """Provide a concurrent model configuration."""
    return ModelConfig(
        model_id="concurrent-model",
        rate_limiters=[
            RateLimiterConfig(type=RateLimiterType.CONCURRENT, limit=3),
        ],
    )


@pytest.fixture
def multiple_model_configs() -> list[ModelConfig]:
    """Provide multiple model configurations."""
    return [
        ModelConfig(
            model_id="model-1",
            rate_limiters=[
                RateLimiterConfig(type=RateLimiterType.RPM, limit=5),
            ],
        ),
        ModelConfig(
            model_id="model-2",
            rate_limiters=[
                RateLimiterConfig(type=RateLimiterType.CONCURRENT, limit=3),
            ],
        ),
        ModelConfig(
            model_id="model-3",
            rate_limiters=[
                RateLimiterConfig(type=RateLimiterType.RPM, limit=10),
            ],
        ),
    ]


@pytest.fixture
def sample_request() -> QueueRequest:
    """Provide a sample queue request."""
    return QueueRequest(model_id="test-model", params={"test": "data"})
