from datetime import datetime, timezone

from src.api.dto.saga_instance import SagaCreateDTO, SagaUpdateDTO, SagaDTO
from src.domain.entities import SagaInstance


class SagaMapper:
    @staticmethod
    def create_dto_to_entity(dto: SagaCreateDTO) -> SagaInstance:
        """
        Преобразует DTO создания в сущность SagaInstance.
        При создании устанавливаются дефолтные значения (status=STARTED, даты).
        """
        return SagaInstance(
            saga_id=dto.saga_id,
            saga_type=dto.saga_type,
            shipment_id=dto.shipment_id,
            warehouse_id=dto.warehouse_id,
            delivery_id=dto.delivery_id,
        )

    @staticmethod
    def update_entity_from_dto(entity: SagaInstance, dto: SagaUpdateDTO) -> SagaInstance:
        """
        Обновляет сущность данными из DTO.
        Используется для обогащения контекста саги (привязка ресурсов)
        или ручного вмешательства (admin override).
        """
        if dto.warehouse_id is not None:
            entity.warehouse_id = dto.warehouse_id

        if dto.delivery_id is not None:
            entity.delivery_id = dto.delivery_id

        if dto.status is not None:
            entity.status = dto.status

        if dto.failed_step is not None:
            entity.failed_step = dto.failed_step

        if dto.error_message is not None:
            entity.error_message = dto.error_message

        entity.updated_at = datetime.now(timezone.utc)

        return entity

    @staticmethod
    def entity_to_dto(entity: SagaInstance) -> SagaDTO:
        """
        Преобразует сущность обратно в DTO для ответа API.
        """
        return SagaDTO(
            saga_id=entity.saga_id,
            saga_type=entity.saga_type,
            shipment_id=entity.shipment_id,
            status=entity.status,
            started_at=entity.started_at,
            updated_at=entity.updated_at,
            warehouse_id=entity.warehouse_id,
            delivery_id=entity.delivery_id,
            failed_step=entity.failed_step,
            error_message=entity.error_message
        )
