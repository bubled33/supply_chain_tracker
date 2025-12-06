from typing import Protocol, List, Optional
from uuid import UUID

from src.domain.entities import Courier


class CourierRepositoryPort(Protocol):
    """Порт для работы с Courier в репозитории"""

    async def save(self, courier: Courier) -> Courier:
        """
        Сохранить курьера (создание или обновление).

        Args:
            courier: Сущность courier для сохранения

        Returns:
            Сохраненный courier
        """
        ...

    async def get(self, courier_id: UUID) -> Optional[Courier]:
        """
        Получить курьера по ID.

        Args:
            courier_id: Уникальный идентификатор курьера

        Returns:
            Courier или None, если не найден
        """
        ...

    async def get_all(self) -> List[Courier]:
        """
        Получить всех курьеров.

        Returns:
            Список всех курьеров
        """
        ...

    async def delete(self, courier_id: UUID) -> None:
        """
        Удалить курьера по ID.

        Args:
            courier_id: ID курьера для удаления
        """
        ...
