from dataclasses import dataclass
import uuid
from typing import List, Dict, Optional
from .base import Command

# --- Warehouse Commands ---

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

# --- Delivery Commands ---

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

# --- Shipment Commands ---

@dataclass
class CreateShipmentCommand(Command):
    """Команда для создания отправления"""
    @staticmethod
    def create(shipment_id: uuid.UUID, origin: str, destination: str, items: List[Dict], saga_id: uuid.UUID) -> "CreateShipmentCommand":
        return CreateShipmentCommand(
            command_type="shipment.create",
            aggregate_id=shipment_id,
            payload={
                "shipment_id": str(shipment_id),
                "origin": origin,
                "destination": destination,
                "items": items,
            },
            correlation_id=saga_id,
        )

@dataclass
class CancelShipmentCommand(Command):
    """Команда для отмены отправления (компенсация)"""
    @staticmethod
    def create(shipment_id: uuid.UUID, reason: str, saga_id: uuid.UUID) -> "CancelShipmentCommand":
        return CancelShipmentCommand(
            command_type="shipment.cancel",
            aggregate_id=shipment_id,
            payload={
                "shipment_id": str(shipment_id),
                "reason": reason,
            },
            correlation_id=saga_id,
        )

# --- Blockchain Commands ---

@dataclass
class RecordTransactionCommand(Command):
    """Команда для записи транзакции в блокчейн"""
    @staticmethod
    def create(record_id: uuid.UUID, shipment_id: uuid.UUID, data_hash: str, saga_id: uuid.UUID) -> "RecordTransactionCommand":
        return RecordTransactionCommand(
            command_type="blockchain.record",
            aggregate_id=record_id,
            payload={
                "record_id": str(record_id),
                "shipment_id": str(shipment_id),
                "data_hash": data_hash,
            },
            correlation_id=saga_id,
        )

@dataclass
class InvalidateBlockchainRecordCommand(Command):
    """Команда для пометки записи как невалидной (компенсация)"""
    # В блокчейне нельзя "удалить", но можно записать корректирующую транзакцию
    # или пометить запись статусом "Void/Invalid" в оффчейн базе
    @staticmethod
    def create(record_id: uuid.UUID, reason: str, saga_id: uuid.UUID) -> "InvalidateBlockchainRecordCommand":
        return InvalidateBlockchainRecordCommand(
            command_type="blockchain.invalidate",
            aggregate_id=record_id,
            payload={
                "record_id": str(record_id),
                "reason": reason,
            },
            correlation_id=saga_id,
        )
