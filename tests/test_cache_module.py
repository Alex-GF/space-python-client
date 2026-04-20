from __future__ import annotations

from space_client.modules.cache_module import CacheModule
from space_client.types import CacheOptions


def test_cache_module_initialize_and_user_invalidation():
    cache = CacheModule()
    cache.initialize(CacheOptions(enabled=True))

    cache.set("contract:user1", {"id": 1})
    cache.set("feature:user1:a", {"eval": True})
    cache.set("pricing-token:user1", "token")
    cache.set("feature:user2:a", {"eval": False})

    cache.invalidate_user("user1")

    assert cache.get("contract:user1") is None
    assert cache.get("feature:user1:a") is None
    assert cache.get("pricing-token:user1") is None
    assert cache.get("feature:user2:a") == {"eval": False}
