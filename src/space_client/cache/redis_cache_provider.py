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
        raw = self._client.get(self._key(key))
        if raw is None:
            return None
        return json.loads(raw)

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        encoded = json.dumps(value)
        seconds = ttl if ttl is not None else self._default_ttl
        if seconds > 0:
            self._client.setex(self._key(key), seconds, encoded)
        else:
            self._client.set(self._key(key), encoded)

    def delete(self, key: str) -> None:
        self._client.delete(self._key(key))

    def clear(self) -> None:
        for key in self._client.scan_iter(match=f"{self._config.key_prefix}*"):
            self._client.delete(key)

    def has(self, key: str) -> bool:
        return bool(self._client.exists(self._key(key)))

    def keys(self, pattern: str | None = None) -> list[str]:
        redis_pattern = f"{self._config.key_prefix}{pattern or '*'}"
        prefix = self._config.key_prefix
        return [key.removeprefix(prefix) for key in self._client.keys(redis_pattern)]

    def close(self) -> None:
        self._client.close()
