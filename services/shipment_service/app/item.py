from uuid import UUID
from typing import List

from services.shipment_service.domain.entities.item import Item


class ItemService:
    def __init__(
        self,
    ):
        pass

    # ---- CRUD ----
    def create(self, item: Item) -> Item:
        pass

    def get(self, item_id: UUID) -> Item:
        pass

    def update(self, item: Item) -> Item:
        pass

    def delete(self, item_id: UUID) -> None:
        pass

    def get_all(self) -> List[Item]:
        pass

    def get_by_shipment(self, shipment_id: UUID) -> List[Item]:
        pass

    # ---- Бизнес методы ----
    def increase_quantity(self, item_id: UUID, quantity: int) -> Item:
        """Увеличить количество item"""
        pass

    def decrease_quantity(self, item_id: UUID, quantity: int) -> Item:
        """Уменьшить количество item"""
        pass

    def update_weight(self, item_id: UUID, weight: float) -> Item:
        """Обновить вес item"""
        pass
