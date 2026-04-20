from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class CacheProvider(ABC):
    @abstractmethod
    def get(self, key: str) -> Any:
        """Retrieve a value from cache.

        Args:
            key (str): Cache key.

        Returns:
            Any: Stored value, or None when key does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store a value in cache.

        Args:
            key (str): Cache key.
            value (Any): Value to store.
            ttl (int | None): Optional TTL in seconds.

        Returns:
            None: No value is returned.
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete a cache entry by key.

        Args:
            key (str): Cache key.

        Returns:
            None: No value is returned.
        """
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        """Delete all cache entries.

        Returns:
            None: No value is returned.
        """
        raise NotImplementedError

    @abstractmethod
    def has(self, key: str) -> bool:
        """Check whether a key exists.

        Args:
            key (str): Cache key.

        Returns:
            bool: True when key exists, otherwise False.
        """
        raise NotImplementedError

    @abstractmethod
    def keys(self, pattern: str | None = None) -> list[str]:
        """List cache keys.

        Args:
            pattern (str | None): Optional glob-style pattern.

        Returns:
            list[str]: Matching cache keys.
        """
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        """Close resources associated with the cache provider.

        Returns:
            None: No value is returned.
        """
        raise NotImplementedError
