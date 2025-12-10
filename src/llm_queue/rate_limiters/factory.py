"""Factory for creating rate limiters."""

from typing import List

from ..models import RateLimiterConfig, RateLimiterType
from .base import BaseRateLimiter
from .chain import RateLimiterChain
from .concurrent_limiter import ConcurrentRateLimiter
from .request_limiter import RequestRateLimiter
from .token_limiter import TokenRateLimiter


def create_rate_limiter(config: RateLimiterConfig) -> BaseRateLimiter:
    """Create a rate limiter from configuration.

    Args:
        config: Rate limiter configuration

    Returns:
        Configured rate limiter instance
    """
    limiter: BaseRateLimiter

    if config.type in (RateLimiterType.RPM, RateLimiterType.RPD):
        # Default time periods if not specified
        time_period = config.time_period
        if time_period is None:
            time_period = 60 if config.type == RateLimiterType.RPM else 86400

        limiter = RequestRateLimiter(limit=config.limit, time_period=time_period)

    elif config.type == RateLimiterType.CONCURRENT:
        limiter = ConcurrentRateLimiter(limit=config.limit)

    elif config.type in (
        RateLimiterType.TPM,
        RateLimiterType.TPD,
        RateLimiterType.ITPM,
        RateLimiterType.OTPM,
    ):
        # Default time periods
        time_period = config.time_period
        if time_period is None:
            if config.type in (
                RateLimiterType.TPM,
                RateLimiterType.ITPM,
                RateLimiterType.OTPM,
            ):
                time_period = 60
            else:  # TPD
                time_period = 86400

        limiter = TokenRateLimiter(limit=config.limit, time_period=time_period)

    else:
        raise ValueError(f"Unsupported rate limiter type: {config.type}")

    # Attach type for chain logic
    # We use setattr because BaseRateLimiter doesn't define it in __init__
    setattr(limiter, "rate_limiter_type", config.type)
    return limiter


def create_chain(configs: List[RateLimiterConfig]) -> RateLimiterChain:
    """Create a rate limiter chain from configurations.

    Args:
        configs: List of rate limiter configurations

    Returns:
        Configured RateLimiterChain
    """
    limiters = [create_rate_limiter(config) for config in configs]
    return RateLimiterChain(limiters)
