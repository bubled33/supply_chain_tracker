from uuid import UUID, uuid4
from datetime import date
from typing import List, Optional

from src.domain.entities import Delivery, Courier
from src.domain.entities.delivery import DeliveryStatus
from src.domain.errors.delivery import DeliveryNotFoundError, DeliveryStatusTransitionError
from src.domain.ports import DeliveryRepositoryPort


class DeliveryService:
    """Сервис для работы с Delivery"""

    def __init__(
            self,
            repository: DeliveryRepositoryPort,
    ):
        self._repository = repository

    async def create(self, delivery: Delivery) -> Delivery:
        """
        Создать новую доставку.
        """
        return await self._repository.save(delivery)

    async def get(self, delivery_id: UUID) -> Optional[Delivery]:
        """
        Получить доставку по ID.
        """
        return await self._repository.get(delivery_id)

    async def update(self, delivery: Delivery) -> Delivery:
        """
        Обновить существующую доставку.
        """
        existing = await self._repository.get(delivery.delivery_id)
        if existing is None:
            raise DeliveryNotFoundError(f"Delivery {delivery.delivery_id} not found")

        return await self._repository.save(delivery)

    async def delete(self, delivery_id: UUID) -> None:
        """
        Удалить доставку (например, при отмене заказа).
        """
        existing = await self._repository.get(delivery_id)
        if existing is None:
            raise DeliveryNotFoundError(f"Delivery {delivery_id} not found")

        await self._repository.delete(delivery_id)

    async def get_all(self) -> List[Delivery]:
        """Получить все доставки"""
        return await self._repository.get_all()

    async def get_by_shipment(self, shipment_id: UUID) -> List[Delivery]:
        return await self._repository.get_by_shipment(shipment_id)

    async def get_active_shipments(self) -> List[Delivery]:
        """Получить все доставки, которые еще не завершены (не DELIVERED/CONFIRMED)"""
        return await self._repository.get_by_status(DeliveryStatus.IN_TRANSIT)

    async def get_in_transit_shipments(self) -> List[Delivery]:
        return await self._repository.get_by_status(DeliveryStatus.IN_TRANSIT)

    async def mark_as_received(self, delivery_id: UUID) -> Delivery:
        """Перевести в статус RECEIVED (на складе)"""
        delivery = await self._get_or_raise(delivery_id)
        # Логика проверки допустимости перехода может быть здесь
        if delivery.status == DeliveryStatus.DELIVERED:
            raise DeliveryStatusTransitionError("Cannot move back from DELIVERED")

        return await self._repository.save(delivery)

    async def mark_as_ready_for_delivery(self, delivery_id: UUID) -> Delivery:
        """Перевести в статус готовности (если такой есть)"""
        delivery = await self._get_or_raise(delivery_id)
        return await self._repository.save(delivery)

    async def mark_as_in_transit(self, delivery_id: UUID) -> Delivery:
        """Перевести в статус IN_TRANSIT"""
        delivery = await self._get_or_raise(delivery_id)

        if delivery.status == DeliveryStatus.DELIVERED:
            raise DeliveryStatusTransitionError("Delivery is already finished")

        delivery.update_status(DeliveryStatus.IN_TRANSIT)
        return await self._repository.save(delivery)

    async def mark_as_delivered(self, delivery_id: UUID, arrival_date: date) -> Delivery:
        """
        Завершить доставку.
        Устанавливает статус DELIVERED и дату фактического прибытия.
        """
        delivery = await self._get_or_raise(delivery_id)

        delivery.mark_delivered(arrival_date)
        return await self._repository.save(delivery)

    async def mark_as_completed(self, delivery_id: UUID) -> Delivery:
        """Перевести в статус CONFIRMED (окончательное завершение)"""
        delivery = await self._get_or_raise(delivery_id)

        if delivery.status != DeliveryStatus.DELIVERED:
            raise DeliveryStatusTransitionError("Delivery must be DELIVERED before CONFIRMED")

        delivery.update_status(DeliveryStatus.CONFIRMED)
        return await self._repository.save(delivery)

    async def reassign_courier(self, delivery_id: UUID, new_courier: Courier) -> Delivery:
        """
        Переназначить курьера для доставки.
        Допустимо только если доставка еще не завершена.
        """
        delivery = await self._get_or_raise(delivery_id)

        if delivery.status in (DeliveryStatus.DELIVERED, DeliveryStatus.CONFIRMED):
            raise DeliveryStatusTransitionError("Cannot reassign courier for finished delivery")

        delivery.courier = new_courier
        from datetime import datetime
        delivery.updated_at = datetime.utcnow()

        return await self._repository.save(delivery)

    async def _get_or_raise(self, delivery_id: UUID) -> Delivery:
        delivery = await self._repository.get(delivery_id)
        if delivery is None:
            raise DeliveryNotFoundError(f"Delivery {delivery_id} not found")
        return delivery
