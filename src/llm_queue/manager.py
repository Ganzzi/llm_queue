"""Queue manager for centralized multi-model queue management."""

from typing import Awaitable, Callable, Dict, Generic, List, Optional, TypeVar

from .exceptions import ModelNotRegistered
from .models import ModelConfig, QueueRequest, QueueResponse, RateLimiterType
from .queue import Queue
from .rate_limiters import create_chain

P = TypeVar("P")  # Generic for request parameters
T = TypeVar("T")  # Generic for response results


class QueueManager(Generic[P, T]):
    """Singleton manager for multiple model queues.

    Manages multiple queues for different LLM models, routing requests
    to the appropriate queue based on model_id.

    Generic Parameters:
        P: Type of the request parameters
        T: Type of the response results

    Attributes:
        queues: Dictionary mapping model_id to Queue instances
    """

    _instance: Optional["QueueManager"] = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(QueueManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the queue manager."""
        if self._initialized:
            return
        self.queues: Dict[str, Queue[P, T]] = {}
        self._initialized = True

    async def register_queue(
        self,
        model_config: ModelConfig,
        processor_func: Callable[[QueueRequest[P]], Awaitable[T]],
    ) -> None:
        """Register a new model with its queue.

        Args:
            model_config: Configuration for the model
            processor_func: Async function to process requests, takes QueueRequest[P] and returns T

        Raises:
            ValueError: If model is already registered
        """
        if model_config.model_id in self.queues:
            raise ValueError(f"Model '{model_config.model_id}' is already registered")

        chain = create_chain(model_config.rate_limiters)

        self.queues[model_config.model_id] = Queue(
            model_id=model_config.model_id,
            processor_func=processor_func,
            rate_limiter_chain=chain,
        )

    async def register_all_queues(
        self, models: List[ModelConfig], processor_func: Callable[[QueueRequest[P]], Awaitable[T]]
    ) -> None:
        """Register multiple models at once.

        Args:
            models: List of model configurations
            processor_func: Async function to process requests

        Note:
            Skips models that are already registered
        """
        for model in models:
            if model.model_id not in self.queues:
                await self.register_queue(
                    model_config=model,
                    processor_func=processor_func,
                )

    async def submit_request(self, request: QueueRequest[P]) -> QueueResponse[T]:
        """Submit a request to the appropriate queue.

        Args:
            request: The request to process

        Returns:
            QueueResponse with the result (if wait_for_completion=True),
            otherwise returns immediately with PENDING status

        Raises:
            ModelNotRegistered: If the model_id is not registered
        """
        model_id = request.model_id
        if model_id not in self.queues:
            raise ModelNotRegistered(f"Model '{model_id}' is not registered")

        return await self.queues[model_id].enqueue(request)

    async def update_token_usage(
        self, model_id: str, request_id: str, input_tokens: int, output_tokens: int
    ) -> None:
        """Update actual token usage for a request.

        Args:
            model_id: ID of the model
            request_id: ID of the request
            input_tokens: Actual input tokens used
            output_tokens: Actual output tokens used

        Raises:
            ModelNotRegistered: If the model_id is not registered
        """
        if model_id not in self.queues:
            raise ModelNotRegistered(f"Model '{model_id}' is not registered")

        await self.queues[model_id].update_token_usage(request_id, input_tokens, output_tokens)

    async def get_status(self, model_id: str, request_id: str) -> Optional[QueueResponse[T]]:
        """Get the status of a specific request.

        Args:
            model_id: ID of the model
            request_id: ID of the request

        Returns:
            QueueResponse if request exists, None otherwise

        Raises:
            ModelNotRegistered: If the model_id is not registered
        """
        if model_id not in self.queues:
            raise ModelNotRegistered(f"Model '{model_id}' is not registered")

        return await self.queues[model_id].get_status(request_id)

    def get_registered_models(self) -> List[str]:
        """Get list of registered model IDs.

        Returns:
            List of model IDs that are currently registered
        """
        return list(self.queues.keys())

    def get_queue_info(self, model_id: str) -> Dict[str, any]:
        """Get information about a specific queue.

        Args:
            model_id: ID of the model

        Returns:
            Dictionary with queue information

        Raises:
            ModelNotRegistered: If the model_id is not registered
        """
        if model_id not in self.queues:
            raise ModelNotRegistered(f"Model '{model_id}' is not registered")

        queue = self.queues[model_id]

        info = {
            "model_id": model_id,
            "queue_size": queue.get_queue_size(),
            "rate_limiter_usage": queue.get_rate_limiter_usage(),
        }

        # Add detailed limiter info
        limiters_info = []
        if queue.rate_limiter_chain:
            for limiter in queue.rate_limiter_chain.limiters:
                l_type = getattr(limiter, "rate_limiter_type", "unknown")
                limiters_info.append(
                    {
                        "type": l_type,
                        "usage": limiter.get_current_usage(),
                        "limit": getattr(limiter, "limit", 0),
                        "available": limiter.get_available_capacity(),
                    }
                )
        info["rate_limiters"] = limiters_info

        return info

    def get_all_queues_info(self) -> Dict[str, Dict[str, any]]:
        """Get information about all registered queues.

        Returns:
            Dictionary mapping model_id to queue information
        """
        return {model_id: self.get_queue_info(model_id) for model_id in self.queues.keys()}

    async def shutdown_all(self) -> None:
        """Gracefully shutdown all queues.

        Waits for all pending requests to complete before stopping.
        """
        for queue in self.queues.values():
            await queue.shutdown()
        self.queues.clear()

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (useful for testing).

        Warning:
            This should only be used in tests. In production, use shutdown_all() instead.
        """
        if cls._instance is not None:
            cls._instance._initialized = False
            cls._instance.queues.clear()
        cls._instance = None
