from __future__ import annotations

import fnmatch
from threading import Lock
from time import time
from typing import Any

from .cache_entry import CacheEntry
from .cache_provider import CacheProvider


class BuiltinCacheProvider(CacheProvider):
    def __init__(self, default_ttl: int) -> None:
        self._default_ttl = default_ttl
        self._cache: dict[str, CacheEntry] = {}
        self._lock = Lock()

    def _purge_if_expired(self, key: str) -> None:
        entry = self._cache.get(key)
        if entry is not None and entry.is_expired():
            self._cache.pop(key, None)

    def get(self, key: str) -> Any:
        with self._lock:
            self._purge_if_expired(key)
            entry = self._cache.get(key)
            return entry.value if entry is not None else None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        with self._lock:
            ttl_to_use = ttl if ttl is not None else self._default_ttl
            self._cache[key] = CacheEntry(value=value, ttl_seconds=ttl_to_use, created_at=time())

    def delete(self, key: str) -> None:
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def has(self, key: str) -> bool:
        with self._lock:
            self._purge_if_expired(key)
            return key in self._cache

    def keys(self, pattern: str | None = None) -> list[str]:
        with self._lock:
            for key in list(self._cache.keys()):
                self._purge_if_expired(key)
            if not pattern:
                return list(self._cache.keys())
            return [key for key in self._cache if fnmatch.fnmatch(key, pattern)]

    def close(self) -> None:
        self.clear()
