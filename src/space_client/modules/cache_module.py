from __future__ import annotations

from typing import Any, Callable, TypeVar

from ..cache.cache_provider import CacheProvider
from ..cache.cache_provider_factory import CacheProviderFactory
from ..types.cache_options import CacheOptions

T = TypeVar("T")


class CacheModule:
    def __init__(self) -> None:
        self._provider: CacheProvider | None = None
        self._enabled = False
        self._key_prefix = "space-client:"

    def initialize(self, options: CacheOptions) -> None:
        if not options.enabled:
            self._enabled = False
            self._provider = None
            return

        CacheProviderFactory.validate(options)
        self._provider = CacheProviderFactory.create(options)
        self._enabled = True

    def is_enabled(self) -> bool:
        return self._enabled and self._provider is not None

    def get(self, key: str, parser: Callable[[Any], T] | None = None) -> T | Any | None:
        if not self.is_enabled():
            return None
        assert self._provider is not None
        value = self._provider.get(self._full_key(key))
        if value is None:
            return None
        if parser is None:
            return value
        try:
            return parser(value)
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        if not self.is_enabled():
            return
        assert self._provider is not None
        self._provider.set(self._full_key(key), value, ttl)

    def delete(self, key: str) -> None:
        if not self.is_enabled():
            return
        assert self._provider is not None
        self._provider.delete(self._full_key(key))

    def has(self, key: str) -> bool:
        if not self.is_enabled():
            return False
        assert self._provider is not None
        return self._provider.has(self._full_key(key))

    def clear(self) -> None:
        if not self.is_enabled():
            return
        assert self._provider is not None
        self._provider.clear()

    def keys(self, pattern: str | None = None) -> list[str]:
        if not self.is_enabled():
            return []
        assert self._provider is not None
        full_pattern = f"{self._key_prefix}{pattern if pattern is not None else '*'}"
        keys = self._provider.keys(full_pattern)
        return [key.removeprefix(self._key_prefix) for key in keys]

    def get_contract_key(self, user_id: str) -> str:
        return f"contract:{user_id}"

    def get_feature_key(self, user_id: str, feature_name: str) -> str:
        return f"feature:{user_id}:{feature_name}"

    def get_subscription_key(self, user_id: str) -> str:
        return f"subscription:{user_id}"

    def get_pricing_token_key(self, user_id: str) -> str:
        return f"pricing-token:{user_id}"

    def invalidate_user(self, user_id: str) -> None:
        if not self.is_enabled():
            return
        patterns = [
            f"contract:{user_id}",
            f"feature:{user_id}:*",
            f"subscription:{user_id}",
            f"pricing-token:{user_id}",
        ]
        for pattern in patterns:
            for key in self.keys(pattern):
                self.delete(key)

    def close(self) -> None:
        if self._provider is not None:
            self._provider.close()
            self._provider = None
        self._enabled = False

    def _full_key(self, key: str) -> str:
        return f"{self._key_prefix}{key}"

    # Java compatibility aliases
    isEnabled = is_enabled
    getContractKey = get_contract_key
    getFeatureKey = get_feature_key
    getSubscriptionKey = get_subscription_key
    getPricingTokenKey = get_pricing_token_key
    invalidateUser = invalidate_user
