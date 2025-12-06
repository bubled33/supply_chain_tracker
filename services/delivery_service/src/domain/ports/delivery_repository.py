from typing import Protocol, List, Optional
from uuid import UUID

from src.domain.entities import Delivery
from src.domain.entities.delivery import DeliveryStatus


class DeliveryRepositoryPort(Protocol):
    """Порт для работы с Delivery в репозитории"""

    async def save(self, delivery: Delivery) -> Delivery:
        """
        Сохранить доставку (создание или обновление).

        Args:
            delivery: Сущность delivery для сохранения

        Returns:
            Сохраненная delivery
        """
        ...

    async def get(self, delivery_id: UUID) -> Optional[Delivery]:
        """
        Получить доставку по ID.

        Args:
            delivery_id: Уникальный идентификатор доставки

        Returns:
            Delivery или None, если не найдена
        """
        ...

    async def get_by_shipment(self, shipment_id: UUID) -> List[Delivery]:
        """
        Получить историю доставок для конкретного отправления.

        Args:
            shipment_id: ID отправления

        Returns:
            Список доставок, связанных с этим отправлением
        """
        ...

    async def get_by_courier(self, courier_id: UUID) -> List[Delivery]:
        """
        Получить все доставки конкретного курьера.

        Args:
            courier_id: ID курьера

        Returns:
            Список доставок, назначенных на курьера
        """
        ...

    async def get_by_status(self, status: DeliveryStatus) -> List[Delivery]:
        """
        Получить доставки по конкретному статусу.
        Например, все активные (IN_TRANSIT) доставки.

        Args:
            status: Статус доставки

        Returns:
            Список доставок в этом статусе
        """
        ...

    async def get_all(self) -> List[Delivery]:
        """
        Получить все доставки.

        Returns:
            Список всех доставок
        """
        ...

    async def delete(self, delivery_id: UUID) -> None:
        """
        Удалить доставку по ID.

        Args:
            delivery_id: ID доставки для удаления
        """
        ...
