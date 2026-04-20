from __future__ import annotations

from dataclasses import dataclass

from .cache_options import CacheOptions


@dataclass
class SpaceConnectionOptions:
    url: str | None
    api_key: str | None
    timeout: int = 5000
    cache: CacheOptions | None = None
