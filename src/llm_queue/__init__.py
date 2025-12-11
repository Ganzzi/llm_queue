"""
LLM Queue - A high-performance Python package for managing LLM API calls with rate limiting.

This package provides:
- Async-first queue management for LLM requests
- Multiple rate limiting modes (requests per period, concurrent requests)
- Per-model queue configuration
- Type-safe operations with Pydantic models
- Request status tracking and monitoring

Example:
    >>> import asyncio
    >>> from llm_queue import QueueManager, ModelConfig, QueueRequest, RateLimiterConfig, RateLimiterType
    >>>
    >>> async def processor(request):
    ...     # Your LLM call logic here
    ...     return {"response": "Hello!"}
    >>>
    >>> async def main():
    ...     manager = QueueManager()
    ...
    ...     # Register a model with rate limiters
    ...     config = ModelConfig(
    ...         model_id="gpt-4",
    ...         rate_limiters=[
    ...             RateLimiterConfig(type=RateLimiterType.RPM, limit=500),
    ...             RateLimiterConfig(type=RateLimiterType.TPM, limit=30000),
    ...         ]
    ...     )
    ...     await manager.register_queue(config, processor)
    ...
    ...     # Submit a request
    ...     request = QueueRequest(model_id="gpt-4", params={"prompt": "Hello"})
    ...     response = await manager.submit_request(request)
    ...     print(response.result)
    >>>
    >>> asyncio.run(main())
"""

from .exceptions import (
    InvalidConfiguration,
    LLMQueueException,
    ModelNotRegistered,
    ProcessingError,
    QueueTimeout,
    RateLimitExceeded,
)
from .manager import QueueManager
from .models import (
    ModelConfig,
    QueueRequest,
    QueueResponse,
    RateLimiterConfig,
    RateLimiterType,
    RequestStatus,
)
from .queue import Queue
from .utils import Timer, get_logger, setup_logging, with_timeout
from .__version__ import __version__, __author__, __email__, __license__

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    # Main classes
    "QueueManager",
    "Queue",
    # Models
    "ModelConfig",
    "QueueRequest",
    "QueueResponse",
    "RateLimiterConfig",
    "RateLimiterType",
    "RequestStatus",
    # Exceptions
    "LLMQueueException",
    "RateLimitExceeded",
    "QueueTimeout",
    "ModelNotRegistered",
    "InvalidConfiguration",
    "ProcessingError",
    # Utils
    "setup_logging",
    "get_logger",
    "with_timeout",
    "Timer",
]
