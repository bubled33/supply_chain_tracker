from dataclasses import dataclass
import uuid

from .base import Command


@dataclass
class ReserveInventoryCommand(Command):
    """Команда для резервирования инвентаря"""
    @staticmethod
    def create(shipment_id: uuid.UUID, warehouse_id: uuid.UUID, items: list[dict], saga_id: uuid.UUID) -> "ReserveInventoryCommand":
        return ReserveInventoryCommand(
            command_type="inventory.reserve",
            aggregate_id=warehouse_id,
            payload={
                "shipment_id": str(shipment_id),
                "warehouse_id": str(warehouse_id),
                "items": items,
            },
            correlation_id=saga_id,
        )


@dataclass
class ReleaseInventoryCommand(Command):
    """Команда для освобождения инвентаря (компенсация)"""
    @staticmethod
    def create(shipment_id: uuid.UUID, warehouse_id: uuid.UUID, items: list[dict], saga_id: uuid.UUID, reason: str) -> "ReleaseInventoryCommand":
        return ReleaseInventoryCommand(
            command_type="inventory.release",
            aggregate_id=warehouse_id,
            payload={
                "shipment_id": str(shipment_id),
                "warehouse_id": str(warehouse_id),
                "items": items,
                "reason": reason,
            },
            correlation_id=saga_id,
        )


@dataclass
class AssignCourierCommand(Command):
    """Команда для назначения курьера"""
    @staticmethod
    def create(shipment_id: uuid.UUID, delivery_id: uuid.UUID, saga_id: uuid.UUID) -> "AssignCourierCommand":
        return AssignCourierCommand(
            command_type="courier.assign",
            aggregate_id=delivery_id,
            payload={
                "delivery_id": str(delivery_id),
                "shipment_id": str(shipment_id),
            },
            correlation_id=saga_id,
        )


@dataclass
class UnassignCourierCommand(Command):
    """Команда для снятия курьера (компенсация)"""
    @staticmethod
    def create(delivery_id: uuid.UUID, saga_id: uuid.UUID, reason: str) -> "UnassignCourierCommand":
        return UnassignCourierCommand(
            command_type="courier.unassign",
            aggregate_id=delivery_id,
            payload={
                "delivery_id": str(delivery_id),
                "reason": reason,
            },
            correlation_id=saga_id,
        )
