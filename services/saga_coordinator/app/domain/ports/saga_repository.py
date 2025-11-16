from abc import ABC, abstractmethod
from uuid import UUID

from services.saga_coordinator.app.domain.entities.saga_event import SagaEvent
from services.saga_coordinator.app.domain.entities.saga_instance import SagaInstance


class SagaRepositoryPort(ABC):
    @abstractmethod
    def add_instance(self, saga: SagaInstance) -> SagaInstance:
        pass

    @abstractmethod
    def get_instance(self, saga_id: UUID) -> SagaInstance:
        pass

    @abstractmethod
    def update_instance(self, saga: SagaInstance) -> SagaInstance:
        pass

    @abstractmethod
    def add_event(self, event: SagaEvent) -> SagaEvent:
        pass

    @abstractmethod
    def list_events(self, saga_id: UUID) -> list[SagaEvent]:
        pass