"""Custom exceptions for llm_queue package."""


class LLMQueueException(Exception):
    """Base exception for llm_queue package."""

    pass


class RateLimitExceeded(LLMQueueException):
    """Raised when rate limit is exceeded."""

    pass


class QueueTimeout(LLMQueueException):
    """Raised when a queue operation times out."""

    pass


class ModelNotRegistered(LLMQueueException):
    """Raised when trying to use a model that hasn't been registered."""

    pass


class InvalidConfiguration(LLMQueueException):
    """Raised when configuration is invalid."""

    pass


class ProcessingError(LLMQueueException):
    """Raised when request processing fails."""

    pass
