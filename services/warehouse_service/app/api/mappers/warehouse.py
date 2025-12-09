from libs.value_objects.location import Location

from app.api.dto.warehouse import WarehouseCreateDTO, WarehouseUpdateDTO, WarehouseDTO
from app.domain.entities import Warehouse


class WarehouseMapper:
    @staticmethod
    def create_dto_to_entity(dto: WarehouseCreateDTO) -> Warehouse:
        location = Location(
            country=dto.country,
            city=dto.city,
            address=dto.address or "",
        )
        return Warehouse(
            name=dto.name,
            location=location,
        )

    @staticmethod
    def update_entity_from_dto(entity: Warehouse, dto: WarehouseUpdateDTO) -> Warehouse:
        if dto.name is not None:
            entity.name = dto.name

        # если пришли любые поля локации — пересобираем VO
        if dto.country is not None or dto.city is not None or dto.address is not None:
            new_country = dto.country if dto.country is not None else entity.location.country
            new_city = dto.city if dto.city is not None else entity.location.city
            new_address = dto.address if dto.address is not None else entity.location.address

            entity.update_location(
                Location(
                    country=new_country,
                    city=new_city,
                    address=new_address or "",
                )
            )

        return entity

    @staticmethod
    def entity_to_dto(entity: Warehouse) -> WarehouseDTO:
        return WarehouseDTO(
            warehouse_id=entity.warehouse_id,
            name=entity.name,
            country=entity.location.country,
            city=entity.location.city,
            address=entity.location.address,
        )
