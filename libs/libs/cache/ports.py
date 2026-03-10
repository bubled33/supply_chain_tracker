from typing import Protocol, Optional, Any, TypeVar, Union, Type
from datetime import timedelta

T = TypeVar("T")

class CachePort(Protocol):

    async def get(
        self,
        key: str,
        model: Optional[Type[T]] = None
    ) -> Optional[Union[dict, list, str, T]]:
        ...

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        ...

    async def delete(self, key: str) -> bool:
        ...

    async def exists(self, key: str) -> bool:
        ...

    async def close(self) -> None:
        ...
