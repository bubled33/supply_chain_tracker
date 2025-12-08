from datetime import datetime

from src.api.dto.delivery import DeliveryCreateDTO, DeliveryUpdateDTO, DeliveryDTO
from src.domain.entities import Courier, Delivery
from src.domain.entities.delivery import DeliveryStatus


class DeliveryMapper:
    @staticmethod
    def create_dto_to_entity(dto: DeliveryCreateDTO, courier: Courier) -> Delivery:
        """
        Принимает объект courier, который сервис должен предварительно найти
        по dto.courier_id.
        """
        return Delivery(
            shipment_id=dto.shipment_id,
            courier=courier,
            status=dto.status if dto.status else DeliveryStatus.ASSIGNED,
            estimated_arrival=dto.estimated_arrival
        )

    @staticmethod
    def update_entity_from_dto(
        entity: Delivery,
        dto: DeliveryUpdateDTO,
        new_courier: Courier = None
    ) -> Delivery:
        """
        Если dto подразумевает смену курьера, сервис должен передать new_courier.
        """
        if dto.courier_id is not None and new_courier is not None:
            if new_courier.courier_id == dto.courier_id:
                entity.courier = new_courier
                entity.updated_at = datetime.utcnow()

        if dto.actual_arrival is not None:
            entity.mark_delivered(dto.actual_arrival)

        elif dto.status is not None:
            entity.update_status(dto.status)

        if dto.estimated_arrival is not None:
            entity.estimated_arrival = dto.estimated_arrival
            entity.updated_at = datetime.utcnow()

        return entity

    @staticmethod
    def entity_to_dto(entity: Delivery) -> DeliveryDTO:
        return DeliveryDTO(
            delivery_id=entity.delivery_id,
            shipment_id=entity.shipment_id,
            courier_id=entity.courier.courier_id,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            estimated_arrival=entity.estimated_arrival,
            actual_arrival=entity.actual_arrival
        )
