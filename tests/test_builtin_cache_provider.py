from __future__ import annotations

import time

from space_client.cache.builtin_cache_provider import BuiltinCacheProvider


def test_store_retrieve_delete_and_clear_values():
    cache = BuiltinCacheProvider(default_ttl=300)
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"

    cache.delete("key1")
    assert cache.get("key1") is None

    cache.set("a", "1")
    cache.set("b", "2")
    cache.clear()
    assert cache.get("a") is None
    assert cache.get("b") is None


def test_ttl_expiration_and_pattern_keys():
    cache = BuiltinCacheProvider(default_ttl=300)
    cache.set("user:1", "v1", ttl=1)
    cache.set("user:2", "v2", ttl=10)
    cache.set("org:1", "v3", ttl=10)

    assert cache.has("user:1")
    time.sleep(1.1)
    assert not cache.has("user:1")

    assert sorted(cache.keys("user:*")) == ["user:2"]
