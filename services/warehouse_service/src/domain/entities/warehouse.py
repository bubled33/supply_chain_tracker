from uuid import UUID, uuid4
from libs.value_objects.location import Location


class Warehouse:
    def __init__(
        self,
        name: str,
        location: Location,
        warehouse_id: UUID | None = None,
    ):
        self.warehouse_id: UUID = warehouse_id or uuid4()
        self.name: str = name
        self.location: Location = location

    def update_location(self, new_location: Location) -> None:
        self.location = new_location

    def __repr__(self) -> str:
        return f"<Warehouse {self.name} ({self.warehouse_id}) @ {self.location.value}>"
