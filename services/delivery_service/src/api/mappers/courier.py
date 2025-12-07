from src.api.dto.courier import CourierCreateDTO, CourierUpdateDTO, CourierDTO
from src.domain.entities import Courier
from src.domain.value_objects import FullName, ContactInfo


class CourierMapper:
    @staticmethod
    def create_dto_to_entity(dto: CourierCreateDTO) -> Courier:
        """
        Преобразует DTO создания в сущность, создавая необходимые Value Objects.
        """
        return Courier(
            name=FullName(dto.name),
            contact_info=ContactInfo(dto.contact_info)
        )

    @staticmethod
    def update_entity_from_dto(entity: Courier, dto: CourierUpdateDTO) -> Courier:
        """
        Обновляет сущность данными из DTO.
        """
        if dto.name is not None:
            entity.name = FullName(dto.name)

        if dto.contact_info is not None:
            new_contact = ContactInfo(dto.contact_info)
            entity.update_contact(new_contact)

        return entity

    @staticmethod
    def entity_to_dto(entity: Courier) -> CourierDTO:
        """
        Преобразует сущность обратно в DTO, извлекая примитивные значения из VO.
        """
        return CourierDTO(
            courier_id=entity.courier_id,
            name=entity.name.value,
            contact_info=entity.contact_info.value
        )
