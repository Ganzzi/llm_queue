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
    >>> from llm_queue import QueueManager, ModelConfig, QueueRequest, RateLimiterMode
    >>>
    >>> async def processor(request):
    ...     # Your LLM call logic here
    ...     return {"response": "Hello!"}
    >>>
    >>> async def main():
    ...     manager = QueueManager()
    ...
    ...     # Register a model
    ...     config = ModelConfig(
    ...         model_id="gpt-4",
    ...         rate_limit=10,
    ...         rate_limiter_mode=RateLimiterMode.REQUESTS_PER_PERIOD,
    ...         time_period=60
    ...     )
    ...     await manager.register_queue(config, processor)
    ...
    ...     # Submit a request
    ...     request = QueueRequest(model_id="gpt-4")
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
    RateLimiterMode,
    RateLimiterType,
    RequestStatus,
)
from .queue import Queue
from .rate_limiter import RateLimiter
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
    "RateLimiter",
    # Models
    "ModelConfig",
    "QueueRequest",
    "QueueResponse",
    "RateLimiterConfig",
    "RateLimiterMode",
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
