from uuid import UUID, uuid4


class Item:
    def __init__(self, item_id: UUID = None, name: str = "", quantity: int = 0, weight: float = 0.0):
        self.item_id: UUID = item_id or uuid4()
        self.name: str = name
        self.quantity: int = quantity
        self.weight: float = weight

    def __repr__(self):
        return f"<Item {self.name} x {self.quantity}>"