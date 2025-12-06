from datetime import datetime

from libs.value_objects.timestamp import Timestamp
from src.domain.value_objects.shipment_status import ShipmentStatus
from src.domain.value_objects.location import Location
from src.api.dto.shipment import ShipmentDTO, ShipmentCreateDTO, ShipmentUpdateDTO, \
    LocationDTO

from ...domain.entities import Shipment


class ShipmentMapper:

    @staticmethod
    def create_dto_to_entity(dto: ShipmentCreateDTO) -> Shipment:
        return Shipment(
            origin=Location(**dto.origin) if isinstance(dto.origin, dict) else dto.origin,
            destination=Location(**dto.destination) if isinstance(dto.destination, dict) else dto.destination,
            departure_date=dto.departure_date,
        )

    @staticmethod
    def update_entity_from_dto(entity: Shipment, dto: ShipmentUpdateDTO) -> Shipment:
        if dto.origin is not None:
            entity.origin = Location(**dto.origin) if isinstance(dto.origin, dict) else dto.origin
        if dto.destination is not None:
            entity.destination = Location(**dto.destination) if isinstance(dto.destination, dict) else dto.destination
        if dto.departure_date is not None:
            entity.departure_date = dto.departure_date
        if dto.arrival_date is not None:
            entity.arrival_date = dto.arrival_date
        if dto.status is not None:
            entity.status = ShipmentStatus(dto.status)
        entity.updated_at = Timestamp(value=datetime.utcnow())
        return entity

    @staticmethod
    def entity_to_dto(entity: Shipment) -> ShipmentDTO:
        return ShipmentDTO(
            shipment_id=entity.shipment_id,
            origin=LocationDTO(
                country=entity.origin.country,
                city=entity.origin.city,
                address=entity.origin.address
            ),
            destination=LocationDTO(
                country=entity.destination.country,
                city=entity.destination.city,
                address=entity.destination.address
            ),
            departure_date=entity.departure_date,
            arrival_date=entity.arrival_date,
            status=entity.status.value,
            created_at=entity.created_at.isoformat(),
            updated_at=entity.updated_at.isoformat()
        )