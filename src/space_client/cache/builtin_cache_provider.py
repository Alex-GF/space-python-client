from __future__ import annotations

import fnmatch
from threading import Lock
from time import time
from typing import Any

from .cache_entry import CacheEntry
from .cache_provider import CacheProvider


class BuiltinCacheProvider(CacheProvider):
    def __init__(self, default_ttl: int) -> None:
        """Create in-memory cache provider.

        Args:
            default_ttl (int): Default TTL in seconds for entries without explicit TTL.

        Returns:
            None: Constructor initializes provider state.
        """
        self._default_ttl = default_ttl
        self._cache: dict[str, CacheEntry] = {}
        self._lock = Lock()

    def _purge_if_expired(self, key: str) -> None:
        entry = self._cache.get(key)
        if entry is not None and entry.is_expired():
            self._cache.pop(key, None)

    def get(self, key: str) -> Any:
        """Get cached value by key.

        Args:
            key (str): Cache key.

        Returns:
            Any: Stored value, or None if key is missing/expired.
        """
        with self._lock:
            self._purge_if_expired(key)
            entry = self._cache.get(key)
            return entry.value if entry is not None else None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set cache value.

        Args:
            key (str): Cache key.
            value (Any): Value to store.
            ttl (int | None): Optional TTL in seconds.

        Returns:
            None: No value is returned.
        """
        with self._lock:
            ttl_to_use = ttl if ttl is not None else self._default_ttl
            self._cache[key] = CacheEntry(value=value, ttl_seconds=ttl_to_use, created_at=time())

    def delete(self, key: str) -> None:
        """Delete one cache key.

        Args:
            key (str): Cache key.

        Returns:
            None: No value is returned.
        """
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        """Delete all cache entries.

        Returns:
            None: No value is returned.
        """
        with self._lock:
            self._cache.clear()

    def has(self, key: str) -> bool:
        """Check key existence.

        Args:
            key (str): Cache key.

        Returns:
            bool: True if key exists and is not expired.
        """
        with self._lock:
            self._purge_if_expired(key)
            return key in self._cache

    def keys(self, pattern: str | None = None) -> list[str]:
        """List cache keys.

        Args:
            pattern (str | None): Optional glob-style pattern.

        Returns:
            list[str]: Matching keys.
        """
        with self._lock:
            for key in list(self._cache.keys()):
                self._purge_if_expired(key)
            if not pattern:
                return list(self._cache.keys())
            return [key for key in self._cache if fnmatch.fnmatch(key, pattern)]

    def close(self) -> None:
        """Release provider resources.

        Returns:
            None: No value is returned.
        """
        self.clear()
