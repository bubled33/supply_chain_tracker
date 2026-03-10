from typing import Protocol, List, Optional
from uuid import UUID

from src.domain.entities import Courier


class CourierRepositoryPort(Protocol):

    async def save(self, courier: Courier) -> Courier:
        ...

    async def get(self, courier_id: UUID) -> Optional[Courier]:
        ...

    async def get_all(self, limit: int = 50, offset: int = 0) -> List[Courier]:
        ...

    async def delete(self, courier_id: UUID) -> None:
        ...
