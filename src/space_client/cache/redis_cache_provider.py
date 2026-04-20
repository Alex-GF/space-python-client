from __future__ import annotations

import json
from typing import Any

from .cache_provider import CacheProvider
from ..types.cache_options import RedisConfig

try:
    from redis import Redis
except ImportError:  # pragma: no cover - optional dependency
    Redis = None  # type: ignore[assignment]


class RedisCacheProvider(CacheProvider):
    def __init__(self, config: RedisConfig, default_ttl: int) -> None:
        """Create Redis-backed cache provider.

        Args:
            config (RedisConfig): Redis connection and key-prefix settings.
            default_ttl (int): Default TTL in seconds for entries without explicit TTL.

        Returns:
            None: Constructor initializes Redis client.

        Raises:
            RuntimeError: If Redis dependency is not installed.
        """
        if Redis is None:
            raise RuntimeError(
                "Redis support requires installing extra dependency: pip install space-python-client[redis]"
            )
        self._config = config
        self._default_ttl = default_ttl
        self._client = Redis(
            host=config.host,
            port=config.port,
            password=config.password,
            db=config.db,
            socket_connect_timeout=config.connect_timeout / 1000,
            decode_responses=True,
        )
        self._client.ping()

    def _key(self, key: str) -> str:
        return f"{self._config.key_prefix}{key}"

    def get(self, key: str) -> Any:
        """Get a value from Redis.

        Args:
            key (str): Cache key without prefix.

        Returns:
            Any: Decoded JSON value, or None when key does not exist.
        """
        raw = self._client.get(self._key(key))
        if raw is None:
            return None
        return json.loads(raw)

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a value in Redis.

        Args:
            key (str): Cache key without prefix.
            value (Any): JSON-serializable value to store.
            ttl (int | None): Optional TTL in seconds.

        Returns:
            None: No value is returned.
        """
        encoded = json.dumps(value)
        seconds = ttl if ttl is not None else self._default_ttl
        if seconds > 0:
            self._client.setex(self._key(key), seconds, encoded)
        else:
            self._client.set(self._key(key), encoded)

    def delete(self, key: str) -> None:
        """Delete one Redis key.

        Args:
            key (str): Cache key without prefix.

        Returns:
            None: No value is returned.
        """
        self._client.delete(self._key(key))

    def clear(self) -> None:
        """Delete all keys with configured prefix.

        Returns:
            None: No value is returned.
        """
        for key in self._client.scan_iter(match=f"{self._config.key_prefix}*"):
            self._client.delete(key)

    def has(self, key: str) -> bool:
        """Check whether a key exists in Redis.

        Args:
            key (str): Cache key without prefix.

        Returns:
            bool: True if key exists, otherwise False.
        """
        return bool(self._client.exists(self._key(key)))

    def keys(self, pattern: str | None = None) -> list[str]:
        """List keys that match a pattern.

        Args:
            pattern (str | None): Optional glob-style pattern without prefix.

        Returns:
            list[str]: Matching keys with prefix removed.
        """
        redis_pattern = f"{self._config.key_prefix}{pattern or '*'}"
        prefix = self._config.key_prefix
        return [key.removeprefix(prefix) for key in self._client.keys(redis_pattern)]

    def close(self) -> None:
        """Close Redis client resources.

        Returns:
            None: No value is returned.
        """
        self._client.close()
