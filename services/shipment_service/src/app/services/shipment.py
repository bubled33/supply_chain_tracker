from uuid import UUID
from typing import List, Optional
from datetime import date

from src.domain.entities.shipment import Shipment
from src.domain.ports import ShipmentRepositoryPort
from src.domain.value_objects.shipment_status import ShipmentStatus
from src.domain.errors import ShipmentNotFoundError


class ShipmentService:

    def __init__(
            self,
            repository: ShipmentRepositoryPort,
    ):
        self._repository = repository


    async def create(self, shipment: Shipment) -> Shipment:
        return await self._repository.save(shipment)

    async def get(self, shipment_id: UUID) -> Optional[Shipment]:
        return await self._repository.get(shipment_id)

    async def update(self, shipment: Shipment) -> Shipment:
        existing = await self._repository.get(shipment.shipment_id)
        if existing is None:
            raise ShipmentNotFoundError(f"Shipment {shipment.shipment_id} not found")

        return await self._repository.save(shipment)

    async def delete(self, shipment_id: UUID) -> None:
        await self._repository.delete(shipment_id)

    async def get_all(self, limit: int = 50, offset: int = 0) -> List[Shipment]:
        return await self._repository.get_all(limit=limit, offset=offset)


    async def update_status(
            self,
            shipment_id: UUID,
            new_status: ShipmentStatus
    ) -> Shipment:
        shipment = await self._repository.get(shipment_id)
        if shipment is None:
            raise ShipmentNotFoundError(f"Shipment {shipment_id} not found")

        shipment.update_status(new_status)
        return await self._repository.save(shipment)

    async def mark_as_received(self, shipment_id: UUID) -> Shipment:
        return await self.update_status(shipment_id, ShipmentStatus.RECEIVED)

    async def mark_as_ready_for_delivery(self, shipment_id: UUID) -> Shipment:
        return await self.update_status(shipment_id, ShipmentStatus.READY_FOR_DELIVERY)

    async def mark_as_in_transit(self, shipment_id: UUID) -> Shipment:
        return await self.update_status(shipment_id, ShipmentStatus.IN_TRANSIT)

    async def mark_as_delivered(
            self,
            shipment_id: UUID,
            arrival_date: date
    ) -> Shipment:
        shipment = await self._repository.get(shipment_id)
        if shipment is None:
            raise ShipmentNotFoundError(f"Shipment {shipment_id} not found")

        shipment.mark_delivered(arrival_date)
        return await self._repository.save(shipment)

    async def mark_as_completed(self, shipment_id: UUID) -> Shipment:
        return await self.update_status(shipment_id, ShipmentStatus.COMPLETED)


    async def get_by_status(self, status: ShipmentStatus) -> List[Shipment]:
        all_shipments = await self._repository.get_all()
        return [s for s in all_shipments if s.status == status]

    async def get_created_shipments(self) -> List[Shipment]:
        return await self.get_by_status(ShipmentStatus.CREATED)

    async def get_received_shipments(self) -> List[Shipment]:
        return await self.get_by_status(ShipmentStatus.RECEIVED)

    async def get_ready_for_delivery_shipments(self) -> List[Shipment]:
        return await self.get_by_status(ShipmentStatus.READY_FOR_DELIVERY)

    async def get_in_transit_shipments(self) -> List[Shipment]:
        return await self.get_by_status(ShipmentStatus.IN_TRANSIT)

    async def get_delivered_shipments(self) -> List[Shipment]:
        return await self.get_by_status(ShipmentStatus.DELIVERED)

    async def get_completed_shipments(self) -> List[Shipment]:
        return await self.get_by_status(ShipmentStatus.COMPLETED)

    async def get_active_shipments(self) -> List[Shipment]:
        all_shipments = await self._repository.get_all()
        return [
            s for s in all_shipments
            if s.status != ShipmentStatus.COMPLETED
        ]

    async def get_pending_shipments(self) -> List[Shipment]:
        all_shipments = await self._repository.get_all()
        return [
            s for s in all_shipments
            if s.status in [ShipmentStatus.CREATED, ShipmentStatus.RECEIVED]
        ]


    async def can_transition_to(
            self,
            shipment_id: UUID,
            target_status: ShipmentStatus
    ) -> bool:
        shipment = await self._repository.get(shipment_id)
        if shipment is None:
            raise ShipmentNotFoundError(f"Shipment {shipment_id} not found")

        valid_transitions = {
            ShipmentStatus.CREATED: [ShipmentStatus.RECEIVED],
            ShipmentStatus.RECEIVED: [ShipmentStatus.READY_FOR_DELIVERY],
            ShipmentStatus.READY_FOR_DELIVERY: [ShipmentStatus.IN_TRANSIT],
            ShipmentStatus.IN_TRANSIT: [ShipmentStatus.DELIVERED],
            ShipmentStatus.DELIVERED: [ShipmentStatus.COMPLETED],
            ShipmentStatus.COMPLETED: [],
        }

        current_status = shipment.status
        allowed_statuses = valid_transitions.get(current_status, [])

        return target_status in allowed_statuses

    async def get_shipment_lifecycle(self, shipment_id: UUID) -> dict:
        shipment = await self._repository.get(shipment_id)
        if shipment is None:
            raise ShipmentNotFoundError(f"Shipment {shipment_id} not found")

        return {
            "shipment_id": str(shipment.shipment_id),
            "current_status": shipment.status.value,
            "created_at": shipment.created_at.value.isoformat(),
            "updated_at": shipment.updated_at.value.isoformat(),
            "departure_date": str(shipment.departure_date),
            "arrival_date": str(shipment.arrival_date) if shipment.arrival_date else None,
            "is_completed": shipment.status == ShipmentStatus.COMPLETED,
            "is_in_progress": shipment.status in [
                ShipmentStatus.READY_FOR_DELIVERY,
                ShipmentStatus.IN_TRANSIT
            ],
        }
