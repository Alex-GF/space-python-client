from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CacheType(str, Enum):
    BUILTIN = "builtin"
    REDIS = "redis"


@dataclass
class RedisConfig:
    host: str | None = None
    port: int = 6379
    password: str | None = None
    db: int = 0
    connect_timeout: int = 5000
    key_prefix: str = "space-client:"


@dataclass
class ExternalCacheConfig:
    redis: RedisConfig | None = None


@dataclass
class CacheOptions:
    enabled: bool = False
    type: CacheType = CacheType.BUILTIN
    external: ExternalCacheConfig | None = None
    ttl: int = 300
