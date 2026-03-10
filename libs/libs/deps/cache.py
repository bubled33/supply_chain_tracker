from typing import Optional
from libs.cache.ports import CachePort
from libs.cache.redis import RedisCacheAdapter
from libs.cache.memory import InMemoryCacheAdapter


class CacheProvider:

    def __init__(
            self,
            redis_url: str,
            service_prefix: str,
            use_redis: bool = True,
            default_ttl: int = 3600
    ):
        self._redis_url = redis_url
        self._prefix = service_prefix
        self._use_redis = use_redis
        self._default_ttl = default_ttl
        self._cache_instance: Optional[CachePort] = None

    async def __call__(self) -> CachePort:
        if not self._cache_instance:
            if self._use_redis:
                self._cache_instance = RedisCacheAdapter(
                    redis_url=self._redis_url,
                    service_prefix=self._prefix,
                    default_ttl=self._default_ttl
                )
            else:
                self._cache_instance = InMemoryCacheAdapter()

        return self._cache_instance
