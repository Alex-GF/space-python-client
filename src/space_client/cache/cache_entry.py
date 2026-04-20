from __future__ import annotations

from dataclasses import dataclass
from time import time
from typing import Any


@dataclass
class CacheEntry:
    value: Any
    ttl_seconds: int
    created_at: float

    def is_expired(self) -> bool:
        if self.ttl_seconds <= 0:
            return False
        return (time() - self.created_at) >= self.ttl_seconds
