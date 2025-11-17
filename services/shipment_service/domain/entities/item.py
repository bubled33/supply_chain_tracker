from dataclasses import dataclass, field
from uuid import UUID, uuid4

from ..value_objects.quantity import Quantity
from ..value_objects.weight import Weight

@dataclass
class Item:
    name: str
    quantity: Quantity
    weight: Weight
    item_id: UUID = field(default_factory=uuid4)

    def to_dict(self) -> dict:
        return {
            "item_id": str(self.item_id),
            "name": self.name,
            "quantity": self.quantity.value,
            "weight": self.weight.value,
        }

    def __repr__(self):
        return f"<Item {self.name} x {self.quantity.value}>"
