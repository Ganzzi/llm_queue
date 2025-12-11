"""Test package initialization."""


def test_imports():
    """Test that all public APIs are importable."""
    from llm_queue import (
        __version__,
        QueueManager,
        Queue,
        ModelConfig,
        QueueRequest,
        QueueResponse,
        RateLimiterConfig,
        RateLimiterType,
        RequestStatus,
        LLMQueueException,
        RateLimitExceeded,
        QueueTimeout,
        ModelNotRegistered,
        InvalidConfiguration,
        ProcessingError,
        setup_logging,
        get_logger,
        with_timeout,
        Timer,
    )

    assert __version__ is not None
    assert QueueManager is not None
    assert Queue is not None


def test_version():
    """Test version string."""
    from llm_queue import __version__

    assert isinstance(__version__, str)
    assert len(__version__) > 0
