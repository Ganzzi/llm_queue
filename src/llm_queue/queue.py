"""Queue implementation for processing requests with rate limiting."""

import asyncio
import time
from typing import Awaitable, Callable, Dict, Generic, Optional, TypeVar

from .models import (
    QueueRequest,
    QueueResponse,
    RateLimiterMode,
    RateLimiterType,
    RequestStatus,
)
from .rate_limiters import RateLimiterChain, RequestRateLimiter, ConcurrentRateLimiter

P = TypeVar("P")  # Generic for request parameters
T = TypeVar("T")  # Generic for response results


class Queue(Generic[P, T]):
    """Queue for managing and processing requests with rate limiting.

    Processes requests asynchronously while respecting rate limits.
    Each queue is associated with a specific model and rate limiter chain.
    """

    def __init__(
        self,
        model_id: str,
        processor_func: Callable[[QueueRequest[P]], Awaitable[T]],
        rate_limit: Optional[int] = None,
        rate_limiter_mode: RateLimiterMode = RateLimiterMode.REQUESTS_PER_PERIOD,
        time_period: int = 60,
        rate_limiter_chain: Optional[RateLimiterChain] = None,
    ):
        """Initialize a queue for a specific LLM.

        Args:
            model_id: Identifier for the LLM
            processor_func: Async function to process requests
            rate_limit: Legacy: requests per period or max concurrent
            rate_limiter_mode: Legacy: Mode of rate limiting
            time_period: Legacy: Time period in seconds
            rate_limiter_chain: V2: Configured rate limiter chain
        """
        self.model_id = model_id
        self.queue: asyncio.Queue = asyncio.Queue()
        self.processor_func = processor_func
        self.requests: Dict[str, QueueRequest[P]] = {}
        # Store completed requests for token usage updates (limit size)
        self.completed_requests: Dict[str, QueueRequest[P]] = {}
        self._max_completed_history = 1000
        
        self._running = True

        if rate_limiter_chain:
            self.rate_limiter_chain = rate_limiter_chain
        else:
            # Legacy initialization
            if rate_limit is None:
                raise ValueError("rate_limit must be provided if rate_limiter_chain is not set")

            if rate_limiter_mode == RateLimiterMode.CONCURRENT_REQUESTS:
                limiter = ConcurrentRateLimiter(limit=rate_limit)
                # Set type for chain logic
                setattr(limiter, "rate_limiter_type", RateLimiterType.CONCURRENT)
            else:
                limiter = RequestRateLimiter(limit=rate_limit, time_period=time_period)
                setattr(limiter, "rate_limiter_type", RateLimiterType.RPM)

            self.rate_limiter_chain = RateLimiterChain([limiter])

        self.task = asyncio.create_task(self._process_queue())

    async def enqueue(self, request: QueueRequest[P]) -> QueueResponse[T]:
        """Add a request to the queue and optionally wait for result."""
        self.requests[request.id] = request

        # Create a future to wait for the result
        future: asyncio.Future[QueueResponse[T]] = asyncio.Future()
        await self.queue.put((request, future))

        # If not waiting for completion, return immediately with PENDING status
        if not request.wait_for_completion:
            return QueueResponse(
                request_id=request.id,
                model_id=request.model_id,
                status=RequestStatus.PENDING,
                result=None,
                error=None,
                processing_time=None,
                created_at=request.created_at,
            )

        # Wait for the result
        result = await future
        return result

    async def _process_queue(self) -> None:
        """Process items in the queue respecting rate limits."""
        while self._running or not self.queue.empty():
            try:
                try:
                    item = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                request: QueueRequest[P]
                future: asyncio.Future[QueueResponse[T]]
                request, future = item

                # Wait for slots (and acquire them)
                await self.rate_limiter_chain.wait_for_all(request)

                # Process the request
                start_time = time.time()
                try:
                    request.status = RequestStatus.PROCESSING
                    result = await self.processor_func(request)
                    request.status = RequestStatus.COMPLETED
                except Exception as e:
                    request.error = str(e)
                    result = None
                    request.status = RequestStatus.FAILED
                finally:
                    # Release concurrent slots
                    await self.rate_limiter_chain.release_all(request)

                processing_time = time.time() - start_time
                
                # Update request with actual tokens if user didn't set them yet
                # (User might have set them inside processor_func, but we don't know)
                # We don't overwrite if set?
                # Actually, we don't touch them here unless we want to auto-capture.
                
                response = QueueResponse(
                    request_id=request.id,
                    model_id=request.model_id,
                    status=request.status,
                    error=request.error,
                    result=result,
                    processing_time=processing_time,
                    created_at=request.created_at,
                    input_tokens_used=request.actual_input_tokens,
                    output_tokens_used=request.actual_output_tokens,
                )

                # Set the future result if not cancelled
                if not future.cancelled():
                    future.set_result(response)

                # Move to completed history
                if request.id in self.requests:
                    del self.requests[request.id]
                
                self.completed_requests[request.id] = request
                self._cleanup_history()

                self.queue.task_done()

            except Exception as e:
                print(f"Unexpected error in queue processing: {e}")
                continue

    async def update_token_usage(
        self, request_id: str, input_tokens: int, output_tokens: int
    ) -> None:
        """Update actual token usage for a request.

        Args:
            request_id: ID of the request
            input_tokens: Actual input tokens used
            output_tokens: Actual output tokens used
        """
        request = self.requests.get(request_id) or self.completed_requests.get(request_id)
        if not request:
            # Request not found or expired from history
            return

        request.actual_input_tokens = input_tokens
        request.actual_output_tokens = output_tokens

        await self.rate_limiter_chain.update_token_usage(
            request, input_tokens, output_tokens
        )

    async def get_status(self, request_id: str) -> Optional[QueueResponse[T]]:
        """Get the current status of a request."""
        request = self.requests.get(request_id) or self.completed_requests.get(request_id)
        if not request:
            return None

        return QueueResponse(
            request_id=request.id,
            model_id=request.model_id,
            status=request.status,
            result=None,  # Result not available here (only in future result)
            error=request.error,
            created_at=request.created_at,
            input_tokens_used=request.actual_input_tokens,
            output_tokens_used=request.actual_output_tokens,
        )

    def get_queue_size(self) -> int:
        """Get the current number of pending requests in the queue."""
        return self.queue.qsize()

    def get_rate_limiter_usage(self) -> int:
        """Get current rate limiter usage.
        
        Note: With multiple limiters, this returns usage of the first limiter
        or a summary. For backward compatibility, we try to return something meaningful.
        """
        if self.rate_limiter_chain.limiters:
            return self.rate_limiter_chain.limiters[0].get_current_usage()
        return 0

    async def shutdown(self) -> None:
        """Gracefully shutdown the queue."""
        self._running = False
        await self.task

    def _cleanup_history(self) -> None:
        """Cleanup old completed requests."""
        if len(self.completed_requests) > self._max_completed_history:
            # Remove oldest (approximate since dict is ordered by insertion in recent Python)
            # Remove 10% oldest
            keys_to_remove = list(self.completed_requests.keys())[: self._max_completed_history // 10]
            for key in keys_to_remove:
                del self.completed_requests[key]
