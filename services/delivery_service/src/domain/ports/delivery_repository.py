from typing import Protocol, List, Optional
from uuid import UUID

from src.domain.entities import Delivery
from src.domain.entities.delivery import DeliveryStatus


class DeliveryRepositoryPort(Protocol):

    async def save(self, delivery: Delivery) -> Delivery:
        ...

    async def get(self, delivery_id: UUID) -> Optional[Delivery]:
        ...

    async def get_by_shipment(self, shipment_id: UUID) -> List[Delivery]:
        ...

    async def get_by_courier(self, courier_id: UUID) -> List[Delivery]:
        ...

    async def get_by_status(self, status: DeliveryStatus) -> List[Delivery]:
        ...

    async def get_all(self, limit: int = 50, offset: int = 0) -> List[Delivery]:
        ...

    async def delete(self, delivery_id: UUID) -> None:
        ...
