from typing import Protocol, List
from uuid import UUID
from services.shipment_service.domain.entities.shipment import Shipment

class ShipmentRepositoryPort(Protocol):
    async def save(self, shipment: Shipment) -> Shipment:
        ...

    async def get(self, shipment_id: UUID) -> Shipment:
        ...

    async def delete(self, shipment_id: UUID) -> None:
        ...

    async def get_all(self) -> List[Shipment]:
        ...
