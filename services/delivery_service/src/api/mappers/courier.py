from src.api.dto.courier import CourierCreateDTO, CourierUpdateDTO, CourierDTO
from src.domain.entities import Courier


class CourierMapper:
    @staticmethod
    def create_dto_to_entity(dto: CourierCreateDTO) -> Courier:
        return Courier(
            name=dto.name,
            contact_info=dto.contact_info
        )

    @staticmethod
    def update_entity_from_dto(entity: Courier, dto: CourierUpdateDTO) -> Courier:
        if dto.name is not None:
            entity.name = dto.name

        if dto.contact_info is not None:
            # Используем метод бизнес-логики для обновления контакта
            entity.update_contact(dto.contact_info)

        return entity

    @staticmethod
    def entity_to_dto(entity: Courier) -> CourierDTO:
        return CourierDTO(
            courier_id=entity.courier_id,
            name=entity.name,
            contact_info=entity.contact_info
        )
