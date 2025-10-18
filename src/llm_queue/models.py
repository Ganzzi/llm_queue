"""Data models for llm_queue package."""

import time
import uuid
from enum import Enum
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class RateLimiterMode(str, Enum):
    """Rate limiter operation modes."""

    REQUESTS_PER_PERIOD = "requests_per_period"  # Limit requests per time period
    CONCURRENT_REQUESTS = "concurrent_requests"  # Limit concurrent requests


class RequestStatus(str, Enum):
    """Status of a queue request."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ModelConfig(BaseModel):
    """Configuration for a specific LLM model.

    Attributes:
        model_id: Unique identifier for the model
        rate_limit: Maximum number of requests (per period or concurrent)
        rate_limiter_mode: Mode of rate limiting
        time_period: Time period in seconds for REQUESTS_PER_PERIOD mode
    """

    model_id: str = Field(..., description="Unique identifier for the model")
    rate_limit: int = Field(
        ..., gt=0, description="Maximum number of requests (per period or concurrent)"
    )
    rate_limiter_mode: RateLimiterMode = Field(
        default=RateLimiterMode.REQUESTS_PER_PERIOD, description="Mode of rate limiting"
    )
    time_period: int = Field(
        default=60, gt=0, description="Time period in seconds for REQUESTS_PER_PERIOD mode"
    )

    model_config = ConfigDict()


class QueueRequest(BaseModel, Generic[T]):
    """A request to be processed in the queue.

    Attributes:
        id: Unique request identifier
        model_id: ID of the model to use
        created_at: Timestamp when request was created
        status: Current status of the request
        result: Result of processing (if completed)
        error: Error message (if failed)
        metadata: Optional metadata for the request
    """

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique request identifier"
    )
    model_id: str = Field(..., description="ID of the model to use")
    created_at: float = Field(
        default_factory=time.time, description="Timestamp when request was created"
    )
    status: RequestStatus = Field(
        default=RequestStatus.PENDING, description="Current status of the request"
    )
    result: Optional[T] = Field(default=None, description="Result of processing (if completed)")
    error: Optional[str] = Field(default=None, description="Error message (if failed)")
    metadata: Optional[dict[str, Any]] = Field(
        default=None, description="Optional metadata for the request"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class QueueResponse(BaseModel, Generic[T]):
    """Response from a queue request.

    Attributes:
        request_id: ID of the original request
        model_id: ID of the model used
        status: Final status of the request
        result: Result of processing (if completed)
        error: Error message (if failed)
        processing_time: Time taken to process in seconds
    """

    request_id: str = Field(..., description="ID of the original request")
    model_id: str = Field(..., description="ID of the model used")
    status: RequestStatus = Field(..., description="Final status of the request")
    result: Optional[T] = Field(default=None, description="Result of processing (if completed)")
    error: Optional[str] = Field(default=None, description="Error message (if failed)")
    processing_time: Optional[float] = Field(
        default=None, description="Time taken to process in seconds"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)
