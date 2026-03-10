from uuid import UUID

from src.domain.entities import Item
from src.domain.value_objects.quantity import Quantity
from src.domain.value_objects.weight import Weight
from src.api.dto.item import ItemDTO, ItemCreateDTO, ItemUpdateDTO

class ItemMapper:
    @staticmethod
    def create_dto_to_entity(dto: ItemCreateDTO, shipment_id: UUID) -> Item:
        return Item(
            shipment_id = shipment_id,
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
            shipment_id=entity.shipment_id,
            item_id=entity.item_id,
            name=entity.name,
            quantity=entity.quantity.value,
            weight=entity.weight.value
        )
