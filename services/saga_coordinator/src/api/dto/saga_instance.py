from dataclasses import dataclass
from uuid import UUID
from datetime import datetime
from typing import Optional

from src.domain.entities.saga_instance import SagaStatus


@dataclass
class SagaCreateDTO:
    """
    DTO для создания новой саги.
    Обычно создается на основе стартового события (например, ShipmentCreated).
    """
    saga_id: UUID
    saga_type: str
    shipment_id: UUID
    warehouse_id: Optional[UUID] = None
    delivery_id: Optional[UUID] = None


@dataclass
class SagaDTO:
    """
    DTO для ответа API / представления SagaInstance.
    Содержит полную информацию о состоянии процесса.
    """
    saga_id: UUID
    saga_type: str
    shipment_id: UUID
    status: SagaStatus
    started_at: datetime
    updated_at: datetime

    warehouse_id: Optional[UUID] = None
    delivery_id: Optional[UUID] = None

    failed_step: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class SagaUpdateDTO:
    """
    DTO для обновления контекста саги.
    Используется воркерами для сохранения промежуточных данных (например, id доставки)
    или ручного вмешательства администратора (смена статуса).
    """
    warehouse_id: Optional[UUID] = None
    delivery_id: Optional[UUID] = None
    status: Optional[SagaStatus] = None
    failed_step: Optional[str] = None
    error_message: Optional[str] = None
