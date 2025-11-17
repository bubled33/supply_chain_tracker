from services.shipment_service.domain import Item
from services.shipment_service.domain.value_objects.quantity import Quantity
from services.shipment_service.domain.value_objects.weight import Weight
from services.shipment_service.api.dto.item import ItemDTO, ItemCreateDTO, ItemUpdateDTO

class ItemMapper:
    @staticmethod
    def create_dto_to_entity(dto: ItemCreateDTO) -> Item:
        return Item(
            name=dto.name,
            quantity=Quantity(dto.quantity),
            weight=Weight(dto.weight)
        )

    @staticmethod
    def update_entity_from_dto(entity: Item, dto: ItemUpdateDTO):
        if dto.name is not None:
            entity.name = dto.name
        if dto.quantity is not None:
            entity.quantity = Quantity(dto.quantity)
        if dto.weight is not None:
            entity.weight = Weight(dto.weight)
        return entity

    @staticmethod
    def entity_to_dto(entity: Item) -> ItemDTO:
        return ItemDTO(
            item_id=entity.item_id,
            name=entity.name,
            quantity=entity.quantity.value,
            weight=entity.weight.value
        )
