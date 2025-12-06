from uuid import UUID, uuid4


class Courier:
    def __init__(self, name: str, contact_info: str, courier_id: UUID = None):
        self.courier_id: UUID = courier_id or uuid4()
        self.name: str = name
        self.contact_info: str = contact_info

    def update_contact(self, new_contact: str):
        self.contact_info = new_contact

    def __repr__(self):
        return f"<Courier {self.name} ({self.courier_id})>"
