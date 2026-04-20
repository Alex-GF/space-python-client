from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class CacheProvider(ABC):
    @abstractmethod
    def get(self, key: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def has(self, key: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def keys(self, pattern: str | None = None) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError
