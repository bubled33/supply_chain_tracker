from typing import Optional, Any, Dict, Type, Union, TypeVar
from datetime import datetime, timedelta
from .ports import CachePort

T = TypeVar("T")


class InMemoryCacheAdapter(CachePort):
    def __init__(self):
        self._storage: Dict[str, Any] = {}
        self._expiry: Dict[str, datetime] = {}

    async def get(self, key: str, model: Optional[Type[T]] = None) -> Optional[Union[dict, T]]:
        if key in self._expiry and datetime.now() > self._expiry[key]:
            del self._storage[key]
            del self._expiry[key]
            return None

        data = self._storage.get(key)
        if data is None:
            return None

        if model and hasattr(model, "model_validate") and isinstance(data, dict):
            return model.model_validate(data)

        return data

    async def set(self, key: str, value: Any, ttl: Optional[Union[int, timedelta]] = None) -> bool:
        if hasattr(value, "model_dump"):
            self._storage[key] = value.model_dump()
        else:
            self._storage[key] = value

        if ttl:
            seconds = ttl if isinstance(ttl, int) else ttl.total_seconds()
            self._expiry[key] = datetime.now() + timedelta(seconds=seconds)
        return True

    async def delete(self, key: str) -> bool:
        if key in self._storage:
            del self._storage[key]
            if key in self._expiry:
                del self._expiry[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        if key in self._expiry and datetime.now() > self._expiry[key]:
            return False
        return key in self._storage

    async def close(self) -> None:
        self._storage.clear()
