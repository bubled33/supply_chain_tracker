import json
import logging
from typing import Optional, Any, Union, Type, TypeVar
from datetime import timedelta

import redis.asyncio as redis
from .ports import CachePort

logger = logging.getLogger(__name__)
T = TypeVar("T")


class RedisCacheAdapter(CachePort):
    def __init__(
            self,
            redis_url: str,
            service_prefix: str = "",
            default_ttl: int = 3600,
            encoding: str = "utf-8"
    ):
        self._redis = redis.from_url(redis_url, encoding=encoding, decode_responses=True)
        self._prefix = service_prefix
        self._default_ttl = default_ttl
        logger.info(f"RedisCacheAdapter initialized for prefix: '{service_prefix}'")

    async def close(self) -> None:
        await self._redis.close()

    def _make_key(self, key: str) -> str:
        if self._prefix:
            return f"{self._prefix}:{key}"
        return key

    async def get(self, key: str, model: Optional[Type[T]] = None) -> Optional[Union[dict, list, str, T]]:
        full_key = self._make_key(key)
        try:
            value = await self._redis.get(full_key)
            if value is None:
                return None

            try:
                data = json.loads(value)
            except json.JSONDecodeError:
                return value

            if model and hasattr(model, "model_validate"):
                return model.model_validate(data)

            return data

        except Exception as e:
            logger.error(f"Redis GET error for key {full_key}: {e}", exc_info=True)
            return None

    async def set(self, key: str, value: Any, ttl: Optional[Union[int, timedelta]] = None) -> bool:
        full_key = self._make_key(key)
        expiry = ttl if ttl is not None else self._default_ttl

        try:
            if hasattr(value, "model_dump"):
                serialized_value = json.dumps(value.model_dump(), default=str)
            elif hasattr(value, "dict"):
                serialized_value = json.dumps(value.dict(), default=str)
            elif isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, default=str)
            else:
                serialized_value = str(value)

            await self._redis.set(full_key, serialized_value, ex=expiry)
            return True

        except Exception as e:
            logger.error(f"Redis SET error for key {full_key}: {e}", exc_info=True)
            return False

    async def delete(self, key: str) -> bool:
        full_key = self._make_key(key)
        try:
            await self._redis.delete(full_key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}", exc_info=True)
            return False

    async def exists(self, key: str) -> bool:
        full_key = self._make_key(key)
        try:
            return await self._redis.exists(full_key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}", exc_info=True)
            return False
