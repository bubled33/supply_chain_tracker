from uuid import UUID, uuid4
from ..value_objects.contact_info import ContactInfo
from ..value_objects.full_name import FullName

class Courier:
    def __init__(
        self,
        name: FullName,
        contact_info: ContactInfo,
        courier_id: UUID = None
    ):
        self.courier_id: UUID = courier_id or uuid4()
        self.name: FullName = name
        self.contact_info: ContactInfo = contact_info

    def update_contact(self, new_contact: ContactInfo):
        self.contact_info = new_contact

    def __repr__(self):
        # .value нужен, так как это теперь объект
        return f"<Courier {self.name.value} ({self.courier_id})>"
