from src.api.dto.inventory_record import InventoryRecordCreateDTO, InventoryRecordUpdateDTO, InventoryRecordDTO
from src.domain.entities.inventory_record import InventoryStatus, InventoryRecord


class InventoryRecordMapper:
    @staticmethod
    def create_dto_to_entity(dto: InventoryRecordCreateDTO) -> InventoryRecord:
        return InventoryRecord(
            shipment_id=dto.shipment_id,
            warehouse_id=dto.warehouse_id,
            status=dto.status or InventoryStatus.RECEIVED,
        )

    @staticmethod
    def update_entity_from_dto(entity: InventoryRecord, dto: InventoryRecordUpdateDTO) -> InventoryRecord:
        if dto.status is not None:
            entity.update_status(dto.status)
        return entity

    @staticmethod
    def entity_to_dto(entity: InventoryRecord) -> InventoryRecordDTO:
        return InventoryRecordDTO(
            record_id=entity.record_id,
            shipment_id=entity.shipment_id,
            warehouse_id=entity.warehouse_id,
            status=entity.status,
            received_at=entity.received_at,
            updated_at=entity.updated_at,
        )
