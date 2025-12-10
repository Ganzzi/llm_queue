"""Data models for llm_queue package."""

import time
import uuid
from enum import Enum
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

P = TypeVar("P")  # Generic for request parameters
T = TypeVar("T")  # Generic for response results


class RateLimiterType(str, Enum):
    """Rate limiter types for v2."""

    RPM = "rpm"  # Requests per Minute
    RPD = "rpd"  # Requests per Day
    TPM = "tpm"  # Tokens per Minute
    TPD = "tpd"  # Tokens per Day
    ITPM = "itpm"  # Input Tokens per Minute
    OTPM = "otpm"  # Output Tokens per Minute
    CONCURRENT = "concurrent"  # Concurrent Requests


class RateLimiterMode(str, Enum):
    """Rate limiter operation modes (Legacy v1)."""

    REQUESTS_PER_PERIOD = "requests_per_period"  # Limit requests per time period
    CONCURRENT_REQUESTS = "concurrent_requests"  # Limit concurrent requests


class RequestStatus(str, Enum):
    """Status of a queue request."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RateLimiterConfig(BaseModel):
    """Configuration for a single rate limiter."""

    type: RateLimiterType = Field(..., description="Type of rate limiter")
    limit: int = Field(..., gt=0, description="Limit value")
    time_period: Optional[int] = Field(
        default=None, gt=0, description="Time period in seconds (optional, overrides default)"
    )

    model_config = ConfigDict()


class ModelConfig(BaseModel):
    """Configuration for a specific LLM model.

    Supports both v2 multi-rate limiter configuration and v1 legacy configuration.
    """

    model_id: str = Field(..., description="Unique identifier for the model")
    
    # V2 Configuration
    rate_limiters: List[RateLimiterConfig] = Field(
        default_factory=list, description="List of rate limiters for this model"
    )

    # V1 Legacy Configuration (Deprecated)
    rate_limit: Optional[int] = Field(
        default=None, gt=0, description="Legacy: Maximum number of requests"
    )
    rate_limiter_mode: Optional[RateLimiterMode] = Field(
        default=None, description="Legacy: Mode of rate limiting"
    )
    time_period: int = Field(
        default=60, gt=0, description="Legacy: Time period in seconds"
    )

    model_config = ConfigDict()

    @model_validator(mode="after")
    def validate_config(self) -> "ModelConfig":
        """Validate that either v1 or v2 config is provided."""
        if not self.rate_limiters and self.rate_limit is None:
            raise ValueError("Either rate_limiters (v2) or rate_limit (v1) must be provided")
        
        # If v1 config is provided but no v2 config, we could auto-convert here
        # but for now we just ensure valid state.
        # The Manager will handle conversion or support both.
        
        return self


class QueueRequest(BaseModel, Generic[P]):
    """A request to be processed in the queue.

    Generic Parameters:
        P: Type of the parameters/payload for this request

    Attributes:
        id: Unique request identifier
        model_id: ID of the model to use
        params: User-defined parameters/payload for the request
        wait_for_completion: Whether to wait for processing to complete (default: True)
        created_at: Timestamp when request was created
        status: Current status of the request
        error: Error message (if failed)
        metadata: Optional metadata for the request
        estimated_input_tokens: Estimated input tokens for rate limiting
        estimated_output_tokens: Estimated output tokens for rate limiting
        actual_input_tokens: Actual input tokens used (set after processing)
        actual_output_tokens: Actual output tokens used (set after processing)
    """

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique request identifier"
    )
    model_id: str = Field(..., description="ID of the model to use")
    params: P = Field(..., description="User-defined parameters/payload for the request")
    wait_for_completion: bool = Field(
        default=True, description="Whether to wait for processing to complete"
    )
    created_at: float = Field(
        default_factory=time.time, description="Timestamp when request was created"
    )
    status: RequestStatus = Field(
        default=RequestStatus.PENDING, description="Current status of the request"
    )
    error: Optional[str] = Field(default=None, description="Error message (if failed)")
    metadata: Optional[dict[str, Any]] = Field(
        default=None, description="Optional metadata for the request"
    )
    
    # Token Tracking Fields
    estimated_input_tokens: Optional[int] = Field(
        default=None, ge=0, description="Estimated input tokens"
    )
    estimated_output_tokens: Optional[int] = Field(
        default=None, ge=0, description="Estimated output tokens"
    )
    actual_input_tokens: Optional[int] = Field(
        default=None, ge=0, description="Actual input tokens used"
    )
    actual_output_tokens: Optional[int] = Field(
        default=None, ge=0, description="Actual output tokens used"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class QueueResponse(BaseModel, Generic[T]):
    """Response from a queue request.

    Generic Parameters:
        T: Type of the result returned from processing

    Attributes:
        request_id: ID of the original request
        model_id: ID of the model used
        status: Final status of the request
        result: Result of processing (if completed)
        error: Error message (if failed)
        processing_time: Time taken to process in seconds
        created_at: Timestamp when request was created
        input_tokens_used: Actual input tokens used
        output_tokens_used: Actual output tokens used
    """

    request_id: str = Field(..., description="ID of the original request")
    model_id: str = Field(..., description="ID of the model used")
    status: RequestStatus = Field(..., description="Final status of the request")
    result: Optional[T] = Field(default=None, description="Result of processing (if completed)")
    error: Optional[str] = Field(default=None, description="Error message (if failed)")
    processing_time: Optional[float] = Field(
        default=None, description="Time taken to process in seconds"
    )
    created_at: float = Field(
        default_factory=time.time, description="Timestamp when request was created"
    )
    
    # Token Usage Fields
    input_tokens_used: Optional[int] = Field(
        default=None, ge=0, description="Actual input tokens used"
    )
    output_tokens_used: Optional[int] = Field(
        default=None, ge=0, description="Actual output tokens used"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)
