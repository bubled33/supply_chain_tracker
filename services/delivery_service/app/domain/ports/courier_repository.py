from abc import ABC, abstractmethod
from uuid import UUID

from services.delivery_service.app.domain.entities import Courier


class CourierRepositoryPort(ABC):
    @abstractmethod
    def add_courier(self, courier: Courier) -> Courier:
        pass

    @abstractmethod
    def get_courier(self, courier_id: UUID) -> Courier:
        pass

    @abstractmethod
    def update_courier(self, courier: Courier) -> Courier:
        pass

    @abstractmethod
    def list_couriers(self) -> list[Courier]:
        pass
