from uuid import UUID
from typing import List, Optional

from src.domain.entities import Courier
from src.domain.errors.courier import CourierNotFoundError
from src.domain.ports.courier_repository import CourierRepositoryPort


class CourierService:
    """Сервис для работы с Courier"""

    def __init__(
            self,
            repository: CourierRepositoryPort,
    ):
        self._repository = repository

    # ---- CRUD ----

    async def create(self, courier: Courier) -> Courier:
        """
        Создать нового курьера.
        """
        return await self._repository.save(courier)

    async def get(self, courier_id: UUID) -> Optional[Courier]:
        """
        Получить курьера по ID.
        """
        return await self._repository.get(courier_id)

    async def update(self, courier: Courier) -> Courier:
        """
        Обновить существующего курьера.
        """
        existing = await self._repository.get(courier.courier_id)
        if existing is None:
            raise CourierNotFoundError(f"Courier {courier.courier_id} not found")

        return await self._repository.save(courier)

    async def delete(self, courier_id: UUID) -> None:
        """
        Удалить курьера по ID.
        """
        # Сначала проверяем существование, чтобы выбросить понятную ошибку
        existing = await self._repository.get(courier_id)
        if existing is None:
            raise CourierNotFoundError(f"Courier {courier_id} not found")

        await self._repository.delete(courier_id)

    async def get_all(self) -> List[Courier]:
        """
        Получить всех курьеров.
        """
        return await self._repository.get_all()

    # ---- Бизнес методы ----

    async def update_contact_info(self, courier_id: UUID, new_contact_info: str) -> Courier:
        """
        Обновить контактную информацию курьера.
        """
        courier = await self._repository.get(courier_id)
        if courier is None:
            raise CourierNotFoundError(f"Courier {courier_id} not found")

        courier.update_contact(new_contact_info)
        return await self._repository.save(courier)
