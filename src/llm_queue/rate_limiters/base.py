"""Base class for rate limiters."""

from abc import ABC, abstractmethod


class BaseRateLimiter(ABC):
    """Abstract base class for rate limiters."""

    @abstractmethod
    async def acquire(self, tokens: int = 1) -> bool:
        """Try to acquire capacity.

        Args:
            tokens: Amount of capacity to acquire (default 1 for requests, N for tokens)

        Returns:
            True if acquired, False otherwise
        """
        pass

    @abstractmethod
    async def release(self, tokens: int = 1) -> None:
        """Release capacity (if applicable).

        Args:
            tokens: Amount of capacity to release
        """
        pass

    @abstractmethod
    async def wait_for_slot(self, tokens: int = 1) -> None:
        """Wait until capacity is available.

        Args:
            tokens: Amount of capacity needed
        """
        pass

    @abstractmethod
    def get_current_usage(self) -> int:
        """Get current usage count.

        Returns:
            Current usage (requests or tokens)
        """
        pass

    @abstractmethod
    def get_available_capacity(self) -> int:
        """Get available capacity.

        Returns:
            Available capacity (limit - usage)
        """
        pass
