from uuid import UUID, uuid4

class Warehouse:
    def __init__(self, name: str, location: str, warehouse_id: UUID = None):
        self.warehouse_id: UUID = warehouse_id or uuid4()
        self.name: str = name
        self.location: str = location

    def update_location(self, new_location: str):
        self.location = new_location

    def __repr__(self):
        return f"<Warehouse {self.name} ({self.warehouse_id})>"
