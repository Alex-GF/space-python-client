"""Running an :class:`~space_client._operations.Operation`, either way.

This is the seam between the two clients. A module's methods say *what* to do by
building an operation; these two runners are the only code that knows whether
sending it blocks or is awaited.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

from .._operations import Operation

if TYPE_CHECKING:
    from .cache_module import CacheModule

T = TypeVar("T")


class ModuleBase:
    """State and cache handling shared by every module, sync or async."""

    def __init__(self, space_client: Any) -> None:
        """Create an operations module.

        Args:
            space_client: Parent client used for transport and cache.

        Returns:
            None: Constructor only stores references.
        """
        self._space_client = space_client

    @property
    def _cache(self) -> "CacheModule":
        return self._space_client.cache

    def _cached(self, operation: Operation[T]) -> T | None:
        """What the cache can answer on its own, if anything.

        Kept out of both runners because deciding whether to look is the same
        decision in both, and getting it wrong in one of them would be a
        difference nobody would see until a stale entitlement was served.
        """
        if operation.cache_hit is None or not self._cache.is_enabled():
            return None
        return operation.cache_hit(self._cache)


class SyncRunner(ModuleBase):
    def _run(self, operation: Operation[T]) -> T:
        cached = self._cached(operation)
        if cached is not None:
            return cached

        if operation.no_content:
            accepted = self._space_client._request_no_content(
                operation.method, operation.path, json=operation.json
            )
            return operation.parse(self._cache, accepted)

        payload = self._space_client._request_json(
            operation.method, operation.path, json=operation.json
        )
        return operation.parse(self._cache, payload)


class AsyncRunner(ModuleBase):
    async def _run(self, operation: Operation[T]) -> T:
        cached = self._cached(operation)
        if cached is not None:
            return cached

        if operation.no_content:
            accepted = await self._space_client._request_no_content(
                operation.method, operation.path, json=operation.json
            )
            return operation.parse(self._cache, accepted)

        payload = await self._space_client._request_json(
            operation.method, operation.path, json=operation.json
        )
        return operation.parse(self._cache, payload)
