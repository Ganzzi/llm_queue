"""Queue implementation for processing requests with rate limiting."""

import asyncio
import time
from typing import Awaitable, Callable, Dict, Generic, Optional, TypeVar

from .models import QueueRequest, QueueResponse, RateLimiterMode, RequestStatus
from .rate_limiter import RateLimiter

T = TypeVar("T")


class Queue(Generic[T]):
    """Queue for managing and processing requests with rate limiting.

    Processes requests asynchronously while respecting rate limits.
    Each queue is associated with a specific model and rate limiter.

    Attributes:
        model_id: Identifier for the LLM model
        rate_limiter: Rate limiter instance
        processor_func: Async function to process requests
    """

    def __init__(
        self,
        model_id: str,
        rate_limit: int,
        processor_func: Callable[[QueueRequest[T]], Awaitable[T]],
        rate_limiter_mode: RateLimiterMode = RateLimiterMode.REQUESTS_PER_PERIOD,
        time_period: int = 60,
    ):
        """Initialize a queue for a specific LLM.

        Args:
            model_id: Identifier for the LLM
            rate_limit: For REQUESTS_PER_PERIOD: requests per time_period
                        For CONCURRENT_REQUESTS: max concurrent requests
            processor_func: Async function to process requests
            rate_limiter_mode: Mode of rate limiting
            time_period: Time period in seconds (default: 60) - REQUESTS_PER_PERIOD only
        """
        self.model_id = model_id
        self.queue: asyncio.Queue = asyncio.Queue()
        self.rate_limiter = RateLimiter(
            limit=rate_limit, mode=rate_limiter_mode, time_period=time_period
        )
        self.requests: Dict[str, QueueRequest[T]] = {}
        self.processor_func = processor_func
        self._running = True
        self.task = asyncio.create_task(self._process_queue())

    async def enqueue(self, request: QueueRequest[T]) -> QueueResponse[T]:
        """Add a request to the queue and wait for result.

        Args:
            request: The LLM request to process

        Returns:
            QueueResponse with the result of processing
        """
        self.requests[request.id] = request
        # Create a future to wait for the result
        future: asyncio.Future[QueueResponse[T]] = asyncio.Future()
        await self.queue.put((request, future))

        # Wait for the result
        result = await future
        return result

    async def _process_queue(self) -> None:
        """Process items in the queue respecting rate limits.

        This is the main worker loop that processes queued requests.
        """
        while self._running or not self.queue.empty():
            try:
                # Get next item from queue with timeout to allow checking _running
                try:
                    item = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                request: QueueRequest[T]
                future: asyncio.Future[QueueResponse[T]]
                request, future = item

                # Wait for a slot according to rate limits
                await self.rate_limiter.wait_for_slot()

                # Process the request
                start_time = time.time()
                try:
                    request.status = RequestStatus.PROCESSING
                    result = await self.processor_func(request)
                    request.result = result
                    request.status = RequestStatus.COMPLETED
                except Exception as e:
                    request.error = str(e)
                    request.result = None
                    request.status = RequestStatus.FAILED
                finally:
                    # Release the slot if using concurrent request mode
                    if self.rate_limiter.mode == RateLimiterMode.CONCURRENT_REQUESTS:
                        await self.rate_limiter.release()

                processing_time = time.time() - start_time

                response = QueueResponse(
                    request_id=request.id,
                    model_id=request.model_id,
                    status=request.status,
                    error=request.error,
                    result=request.result,
                    processing_time=processing_time,
                )

                # Set the future result if not cancelled
                if not future.cancelled():
                    future.set_result(response)

                # Clean up the request from self.requests after processing
                if request.id in self.requests:
                    del self.requests[request.id]

                self.queue.task_done()

            except Exception as e:
                # Log unexpected errors but keep processing
                print(f"Unexpected error in queue processing: {e}")
                continue

    async def get_status(self, request_id: str) -> Optional[QueueResponse[T]]:
        """Get the current status of a request.

        Args:
            request_id: ID of the request to check

        Returns:
            QueueResponse if request exists, None otherwise
        """
        if request_id not in self.requests:
            return None

        request = self.requests[request_id]
        return QueueResponse(
            request_id=request.id,
            model_id=request.model_id,
            status=request.status,
            result=request.result,
            error=request.error,
        )

    def get_queue_size(self) -> int:
        """Get the current number of pending requests in the queue.

        Returns:
            Number of requests waiting to be processed
        """
        return self.queue.qsize()

    def get_rate_limiter_usage(self) -> int:
        """Get current rate limiter usage.

        Returns:
            Current number of active/recent requests
        """
        return self.rate_limiter.get_current_usage()

    async def shutdown(self) -> None:
        """Gracefully shutdown the queue.

        Waits for pending requests to complete before stopping.
        """
        self._running = False

        # Wait for the processing task to finish processing all items
        await self.task
