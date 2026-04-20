from __future__ import annotations

from ..types.cache_options import CacheOptions, CacheType
from .builtin_cache_provider import BuiltinCacheProvider
from .cache_provider import CacheProvider
from .redis_cache_provider import RedisCacheProvider


class CacheProviderFactory:
    @staticmethod
    def create(options: CacheOptions) -> CacheProvider:
        """Create a concrete cache provider.

        Args:
            options (CacheOptions): Cache configuration.

        Returns:
            CacheProvider: Built-in or Redis provider depending on configuration.

        Raises:
            ValueError: If Redis is selected but configuration is incomplete.
        """
        if options.type == CacheType.REDIS:
            if options.external is None or options.external.redis is None:
                raise ValueError("Redis configuration is required when using Redis cache type")
            return RedisCacheProvider(options.external.redis, options.ttl)
        return BuiltinCacheProvider(options.ttl)

    @staticmethod
    def validate(options: CacheOptions) -> None:
        """Validate cache configuration values.

        Args:
            options (CacheOptions): Cache configuration.

        Returns:
            None: No value is returned.

        Raises:
            ValueError: If any cache option value is invalid.
        """
        if not options.enabled:
            return

        if options.type == CacheType.REDIS:
            if options.external is None or options.external.redis is None:
                raise ValueError("Redis configuration is required when using Redis cache type")

            redis = options.external.redis
            if not redis.host:
                raise ValueError("Redis host is required")
            if redis.port < 1 or redis.port > 65535:
                raise ValueError("Redis port must be between 1 and 65535")
            if redis.db < 0 or redis.db > 15:
                raise ValueError("Redis database number must be between 0 and 15")
            if redis.connect_timeout <= 0:
                raise ValueError("Redis connect timeout must be a positive number")

        if options.ttl <= 0:
            raise ValueError("TTL must be a positive number")
