import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import date, datetime, timezone

from src.infra.db.delivery_repository import AsyncPostgresDeliveryRepository
from src.domain.entities import Delivery, Courier
from src.domain.entities.delivery import DeliveryStatus


@pytest.fixture
def mock_connection():
    """Мок для asyncpg.Connection"""
    return AsyncMock()


@pytest.fixture
def mock_pool(mock_connection):
    """Мок для asyncpg.Pool с правильной настройкой context manager"""
    pool = MagicMock()

    # Настраиваем acquire() как async context manager
    acquire_context = MagicMock()
    acquire_context.__aenter__ = AsyncMock(return_value=mock_connection)
    acquire_context.__aexit__ = AsyncMock(return_value=None)

    pool.acquire.return_value = acquire_context

    return pool


@pytest.fixture
def repository(mock_pool):
    """Фикстура для репозитория"""
    return AsyncPostgresDeliveryRepository(mock_pool)


@pytest.fixture
def sample_courier():
    """Пример курьера"""
    return Courier(
        courier_id=uuid4(),
        name="John Courier",
        contact_info="+79001234567"
    )


@pytest.fixture
def sample_delivery(sample_courier):
    """Пример доставки для тестов"""
    return Delivery(
        delivery_id=uuid4(),
        shipment_id=uuid4(),
        courier=sample_courier,
        status=DeliveryStatus.ASSIGNED,
        estimated_arrival=date(2025, 12, 15),
        actual_arrival=None
    )


class TestAsyncPostgresDeliveryRepository:
    """Тесты для AsyncPostgresDeliveryRepository"""

    @pytest.mark.asyncio
    async def test_save_new_delivery(self, repository, mock_connection, sample_delivery):
        """Тест сохранения новой доставки (INSERT)"""
        # Настройка мока
        mock_connection.fetchrow.return_value = {
            'delivery_id': sample_delivery.delivery_id,
            'shipment_id': sample_delivery.shipment_id,
            'courier_id': sample_delivery.courier.courier_id,
            'status': sample_delivery.status.value,
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'estimated_arrival': sample_delivery.estimated_arrival,
            'actual_arrival': sample_delivery.actual_arrival,
            # Courier fields
            'courier_name': sample_delivery.courier.name,
            'courier_contact_info': sample_delivery.courier.contact_info
        }

        # Вызов метода
        result = await repository.save(sample_delivery)

        # Проверки
        assert result.delivery_id == sample_delivery.delivery_id
        assert result.shipment_id == sample_delivery.shipment_id
        assert result.courier.courier_id == sample_delivery.courier.courier_id
        assert result.status == sample_delivery.status

        # Проверяем SQL запрос
        mock_connection.fetchrow.assert_awaited_once()
        call_args = mock_connection.fetchrow.call_args
        assert "INSERT INTO deliveries" in call_args[0][0]
        assert "ON CONFLICT" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_save_existing_delivery(self, repository, mock_connection, sample_courier):
        """Тест обновления существующей доставки (UPDATE)"""
        delivery_id = uuid4()
        shipment_id = uuid4()

        delivery = Delivery(
            delivery_id=delivery_id,
            shipment_id=shipment_id,
            courier=sample_courier,
            status=DeliveryStatus.IN_TRANSIT
        )

        mock_connection.fetchrow.return_value = {
            'delivery_id': delivery_id,
            'shipment_id': shipment_id,
            'courier_id': sample_courier.courier_id,
            'status': DeliveryStatus.IN_TRANSIT.value,
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'estimated_arrival': None,
            'actual_arrival': None,
            'courier_name': sample_courier.name,
            'courier_contact_info': sample_courier.contact_info
        }

        result = await repository.save(delivery)

        assert result.delivery_id == delivery_id
        assert result.status == DeliveryStatus.IN_TRANSIT
        mock_connection.fetchrow.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_existing_delivery(self, repository, mock_connection):
        """Тест получения существующей доставки"""
        delivery_id = uuid4()
        shipment_id = uuid4()
        courier_id = uuid4()

        mock_connection.fetchrow.return_value = {
            'delivery_id': delivery_id,
            'shipment_id': shipment_id,
            'courier_id': courier_id,
            'status': DeliveryStatus.ASSIGNED.value,
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'estimated_arrival': date(2025, 12, 15),
            'actual_arrival': None,
            'courier_name': "John Courier",
            'courier_contact_info': "+79001234567"
        }

        result = await repository.get(delivery_id)

        assert result is not None
        assert result.delivery_id == delivery_id
        assert result.shipment_id == shipment_id
        assert result.courier.courier_id == courier_id
        assert result.status == DeliveryStatus.ASSIGNED

        # Проверяем SQL запрос
        mock_connection.fetchrow.assert_awaited_once()
        call_args = mock_connection.fetchrow.call_args
        assert "SELECT" in call_args[0][0]
        assert "WHERE" in call_args[0][0]
        assert call_args[0][1] == delivery_id

    @pytest.mark.asyncio
    async def test_get_non_existing_delivery(self, repository, mock_connection):
        """Тест получения несуществующей доставки"""
        delivery_id = uuid4()

        mock_connection.fetchrow.return_value = None

        result = await repository.get(delivery_id)

        assert result is None
        mock_connection.fetchrow.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_by_shipment_empty(self, repository, mock_connection):
        """Тест получения пустого списка доставок для отправления"""
        shipment_id = uuid4()

        mock_connection.fetch.return_value = []

        result = await repository.get_by_shipment(shipment_id)

        assert result == []
        mock_connection.fetch.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_by_shipment_multiple(self, repository, mock_connection):
        """Тест получения нескольких доставок для одного отправления"""
        shipment_id = uuid4()
        delivery1_id = uuid4()
        delivery2_id = uuid4()
        courier_id = uuid4()

        mock_connection.fetch.return_value = [
            {
                'delivery_id': delivery1_id,
                'shipment_id': shipment_id,
                'courier_id': courier_id,
                'status': DeliveryStatus.ASSIGNED.value,
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
                'estimated_arrival': None,
                'actual_arrival': None,
                'courier_name': "Courier 1",
                'courier_contact_info': "+79001111111"
            },
            {
                'delivery_id': delivery2_id,
                'shipment_id': shipment_id,
                'courier_id': courier_id,
                'status': DeliveryStatus.DELIVERED.value,
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
                'estimated_arrival': None,
                'actual_arrival': date.today(),
                'courier_name': "Courier 1",
                'courier_contact_info': "+79001111111"
            }
        ]

        result = await repository.get_by_shipment(shipment_id)

        assert len(result) == 2
        assert result[0].shipment_id == shipment_id
        assert result[1].shipment_id == shipment_id
        assert result[0].status == DeliveryStatus.ASSIGNED
        assert result[1].status == DeliveryStatus.DELIVERED

    @pytest.mark.asyncio
    async def test_get_by_courier_empty(self, repository, mock_connection):
        """Тест получения пустого списка доставок для курьера"""
        courier_id = uuid4()

        mock_connection.fetch.return_value = []

        result = await repository.get_by_courier(courier_id)

        assert result == []
        mock_connection.fetch.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_by_courier_multiple(self, repository, mock_connection):
        """Тест получения всех доставок курьера"""
        courier_id = uuid4()
        delivery1_id = uuid4()
        delivery2_id = uuid4()

        mock_connection.fetch.return_value = [
            {
                'delivery_id': delivery1_id,
                'shipment_id': uuid4(),
                'courier_id': courier_id,
                'status': DeliveryStatus.ASSIGNED.value,
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
                'estimated_arrival': None,
                'actual_arrival': None,
                'courier_name': "John Courier",
                'courier_contact_info': "+79001234567"
            },
            {
                'delivery_id': delivery2_id,
                'shipment_id': uuid4(),
                'courier_id': courier_id,
                'status': DeliveryStatus.IN_TRANSIT.value,
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
                'estimated_arrival': None,
                'actual_arrival': None,
                'courier_name': "John Courier",
                'courier_contact_info': "+79001234567"
            }
        ]

        result = await repository.get_by_courier(courier_id)

        assert len(result) == 2
        assert result[0].courier.courier_id == courier_id
        assert result[1].courier.courier_id == courier_id

    @pytest.mark.asyncio
    async def test_get_by_status_empty(self, repository, mock_connection):
        """Тест получения пустого списка доставок по статусу"""
        mock_connection.fetch.return_value = []

        result = await repository.get_by_status(DeliveryStatus.IN_TRANSIT)

        assert result == []
        mock_connection.fetch.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_by_status_multiple(self, repository, mock_connection):
        """Тест получения доставок по статусу"""
        delivery1_id = uuid4()
        delivery2_id = uuid4()

        mock_connection.fetch.return_value = [
            {
                'delivery_id': delivery1_id,
                'shipment_id': uuid4(),
                'courier_id': uuid4(),
                'status': DeliveryStatus.IN_TRANSIT.value,
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
                'estimated_arrival': None,
                'actual_arrival': None,
                'courier_name': "Courier 1",
                'courier_contact_info': "+79001111111"
            },
            {
                'delivery_id': delivery2_id,
                'shipment_id': uuid4(),
                'courier_id': uuid4(),
                'status': DeliveryStatus.IN_TRANSIT.value,
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
                'estimated_arrival': None,
                'actual_arrival': None,
                'courier_name': "Courier 2",
                'courier_contact_info': "+79002222222"
            }
        ]

        result = await repository.get_by_status(DeliveryStatus.IN_TRANSIT)

        assert len(result) == 2
        assert all(d.status == DeliveryStatus.IN_TRANSIT for d in result)

    @pytest.mark.asyncio
    async def test_get_all_empty(self, repository, mock_connection):
        """Тест получения пустого списка всех доставок"""
        mock_connection.fetch.return_value = []

        result = await repository.get_all()

        assert result == []
        mock_connection.fetch.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_all_multiple(self, repository, mock_connection):
        """Тест получения всех доставок"""
        mock_connection.fetch.return_value = [
            {
                'delivery_id': uuid4(),
                'shipment_id': uuid4(),
                'courier_id': uuid4(),
                'status': DeliveryStatus.ASSIGNED.value,
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
                'estimated_arrival': None,
                'actual_arrival': None,
                'courier_name': "Courier 1",
                'courier_contact_info': "+79001111111"
            },
            {
                'delivery_id': uuid4(),
                'shipment_id': uuid4(),
                'courier_id': uuid4(),
                'status': DeliveryStatus.DELIVERED.value,
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
                'estimated_arrival': None,
                'actual_arrival': date.today(),
                'courier_name': "Courier 2",
                'courier_contact_info': "+79002222222"
            }
        ]

        result = await repository.get_all()

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_delete_delivery(self, repository, mock_connection):
        """Тест удаления доставки"""
        delivery_id = uuid4()

        mock_connection.execute.return_value = "DELETE 1"

        await repository.delete(delivery_id)

        # Проверяем SQL запрос
        mock_connection.execute.assert_awaited_once()
        call_args = mock_connection.execute.call_args
        assert "DELETE FROM deliveries" in call_args[0][0]
        assert "WHERE delivery_id = $1" in call_args[0][0]
        assert call_args[0][1] == delivery_id

    @pytest.mark.asyncio
    async def test_delete_non_existing_delivery(self, repository, mock_connection):
        """Тест удаления несуществующей доставки (не должно вызывать ошибку)"""
        delivery_id = uuid4()

        mock_connection.execute.return_value = "DELETE 0"

        # Не должно вызывать исключение
        await repository.delete(delivery_id)

        mock_connection.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_pool_acquire_context_manager(self, repository, mock_pool, mock_connection):
        """Тест корректного использования context manager для пула"""
        delivery_id = uuid4()

        mock_connection.fetchrow.return_value = None

        await repository.get(delivery_id)

        # Проверяем, что пул был корректно использован
        mock_pool.acquire.assert_called_once()
        mock_pool.acquire.return_value.__aenter__.assert_awaited_once()
        mock_pool.acquire.return_value.__aexit__.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_connection_error_handling(self, mock_pool):
        """Тест обработки ошибки подключения"""
        delivery_id = uuid4()

        # Симулируем ошибку при входе в context manager
        error_context = MagicMock()
        error_context.__aenter__ = AsyncMock(side_effect=Exception("Connection failed"))
        error_context.__aexit__ = AsyncMock()

        mock_pool.acquire.return_value = error_context

        repository = AsyncPostgresDeliveryRepository(mock_pool)

        with pytest.raises(Exception, match="Connection failed"):
            await repository.get(delivery_id)

    @pytest.mark.asyncio
    async def test_save_delivery_with_dates(self, repository, mock_connection, sample_courier):
        """Тест сохранения доставки с датами прибытия"""
        delivery = Delivery(
            delivery_id=uuid4(),
            shipment_id=uuid4(),
            courier=sample_courier,
            status=DeliveryStatus.DELIVERED,
            estimated_arrival=date(2025, 12, 15),
            actual_arrival=date(2025, 12, 14)
        )

        mock_connection.fetchrow.return_value = {
            'delivery_id': delivery.delivery_id,
            'shipment_id': delivery.shipment_id,
            'courier_id': delivery.courier.courier_id,
            'status': delivery.status.value,
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc),
            'estimated_arrival': delivery.estimated_arrival,
            'actual_arrival': delivery.actual_arrival,
            'courier_name': delivery.courier.name,
            'courier_contact_info': delivery.courier.contact_info
        }

        result = await repository.save(delivery)

        assert result.estimated_arrival == date(2025, 12, 15)
        assert result.actual_arrival == date(2025, 12, 14)
        assert result.status == DeliveryStatus.DELIVERED
