import pytest
from unittest.mock import AsyncMock, MagicMock, call
from uuid import uuid4

from src.infra.db.courier_repository import AsyncPostgresCourierRepository
from src.domain.entities import Courier


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
    return AsyncPostgresCourierRepository(mock_pool)


@pytest.fixture
def sample_courier():
    """Пример курьера для тестов"""
    return Courier(
        courier_id=uuid4(),
        name="John Doe",
        contact_info="+79001234567"
    )


class TestAsyncPostgresCourierRepository:
    """Тесты для AsyncPostgresCourierRepository"""

    @pytest.mark.asyncio
    async def test_save_new_courier(self, repository, mock_connection, sample_courier):
        """Тест сохранения нового курьера (INSERT)"""
        # Настройка мока
        mock_connection.fetchrow.return_value = {
            'courier_id': sample_courier.courier_id,
            'name': sample_courier.name,
            'contact_info': sample_courier.contact_info
        }

        # Вызов метода
        result = await repository.save(sample_courier)

        # Проверки
        assert result.courier_id == sample_courier.courier_id
        assert result.name == sample_courier.name
        assert result.contact_info == sample_courier.contact_info

        # Проверяем SQL запрос
        mock_connection.fetchrow.assert_awaited_once()
        call_args = mock_connection.fetchrow.call_args
        assert "INSERT INTO couriers" in call_args[0][0]
        assert "ON CONFLICT" in call_args[0][0]
        assert call_args[0][1] == sample_courier.courier_id
        assert call_args[0][2] == sample_courier.name
        assert call_args[0][3] == sample_courier.contact_info

    @pytest.mark.asyncio
    async def test_save_existing_courier(self, repository, mock_connection):
        """Тест обновления существующего курьера (UPDATE)"""
        courier_id = uuid4()
        courier = Courier(
            courier_id=courier_id,
            name="Updated Name",
            contact_info="New Contact"
        )

        mock_connection.fetchrow.return_value = {
            'courier_id': courier_id,
            'name': "Updated Name",
            'contact_info': "New Contact"
        }

        result = await repository.save(courier)

        assert result.courier_id == courier_id
        assert result.name == "Updated Name"
        assert result.contact_info == "New Contact"

        mock_connection.fetchrow.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_existing_courier(self, repository, mock_connection):
        """Тест получения существующего курьера"""
        courier_id = uuid4()

        mock_connection.fetchrow.return_value = {
            'courier_id': courier_id,
            'name': "John Doe",
            'contact_info': "+79001234567"
        }

        result = await repository.get(courier_id)

        assert result is not None
        assert result.courier_id == courier_id
        assert result.name == "John Doe"
        assert result.contact_info == "+79001234567"

        # Проверяем SQL запрос
        mock_connection.fetchrow.assert_awaited_once()
        call_args = mock_connection.fetchrow.call_args
        assert "SELECT courier_id, name, contact_info" in call_args[0][0]
        assert "FROM couriers" in call_args[0][0]
        assert "WHERE courier_id = $1" in call_args[0][0]
        assert call_args[0][1] == courier_id

    @pytest.mark.asyncio
    async def test_get_non_existing_courier(self, repository, mock_connection):
        """Тест получения несуществующего курьера"""
        courier_id = uuid4()

        mock_connection.fetchrow.return_value = None  # Курьер не найден

        result = await repository.get(courier_id)

        assert result is None
        mock_connection.fetchrow.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_all_empty(self, repository, mock_connection):
        """Тест получения пустого списка курьеров"""
        mock_connection.fetch.return_value = []

        result = await repository.get_all()

        assert result == []
        mock_connection.fetch.assert_awaited_once()
        call_args = mock_connection.fetch.call_args
        assert "SELECT courier_id, name, contact_info" in call_args[0][0]
        assert "ORDER BY name" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_all_multiple_couriers(self, repository, mock_connection):
        """Тест получения списка курьеров"""
        courier1_id = uuid4()
        courier2_id = uuid4()

        mock_connection.fetch.return_value = [
            {
                'courier_id': courier1_id,
                'name': "Alice",
                'contact_info': "+79001111111"
            },
            {
                'courier_id': courier2_id,
                'name': "Bob",
                'contact_info': "+79002222222"
            }
        ]

        result = await repository.get_all()

        assert len(result) == 2
        assert result[0].courier_id == courier1_id
        assert result[0].name == "Alice"
        assert result[1].courier_id == courier2_id
        assert result[1].name == "Bob"

        mock_connection.fetch.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_courier(self, repository, mock_connection):
        """Тест удаления курьера"""
        courier_id = uuid4()

        mock_connection.execute.return_value = "DELETE 1"

        await repository.delete(courier_id)

        # Проверяем SQL запрос
        mock_connection.execute.assert_awaited_once()
        call_args = mock_connection.execute.call_args
        assert "DELETE FROM couriers" in call_args[0][0]
        assert "WHERE courier_id = $1" in call_args[0][0]
        assert call_args[0][1] == courier_id

    @pytest.mark.asyncio
    async def test_delete_non_existing_courier(self, repository, mock_connection):
        """Тест удаления несуществующего курьера (не должно вызывать ошибку)"""
        courier_id = uuid4()

        mock_connection.execute.return_value = "DELETE 0"

        # Не должно вызывать исключение
        await repository.delete(courier_id)

        mock_connection.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_pool_acquire_context_manager(self, repository, mock_pool, mock_connection):
        """Тест корректного использования context manager для пула"""
        courier_id = uuid4()

        mock_connection.fetchrow.return_value = None

        await repository.get(courier_id)

        # Проверяем, что пул был корректно использован
        mock_pool.acquire.assert_called_once()
        mock_pool.acquire.return_value.__aenter__.assert_awaited_once()
        mock_pool.acquire.return_value.__aexit__.assert_awaited_once()

    def test_row_to_entity(self, repository):
        """Тест преобразования row в entity"""
        courier_id = uuid4()
        row = {
            'courier_id': courier_id,
            'name': "Test Courier",
            'contact_info': "test@example.com"
        }

        courier = repository._row_to_entity(row)

        assert isinstance(courier, Courier)
        assert courier.courier_id == courier_id
        assert courier.name == "Test Courier"
        assert courier.contact_info == "test@example.com"

    @pytest.mark.asyncio
    async def test_save_with_special_characters(self, repository, mock_connection):
        """Тест сохранения курьера со спецсимволами в данных"""
        courier = Courier(
            courier_id=uuid4(),
            name="O'Brien",
            contact_info="Phone: +7(900)123-45-67, Email: test@example.com"
        )

        mock_connection.fetchrow.return_value = {
            'courier_id': courier.courier_id,
            'name': courier.name,
            'contact_info': courier.contact_info
        }

        result = await repository.save(courier)

        assert result.name == "O'Brien"
        assert "test@example.com" in result.contact_info

    @pytest.mark.asyncio
    async def test_connection_error_handling(self, mock_pool):
        """Тест обработки ошибки подключения"""
        courier_id = uuid4()

        # Симулируем ошибку при входе в context manager
        error_context = MagicMock()
        error_context.__aenter__ = AsyncMock(side_effect=Exception("Connection failed"))
        error_context.__aexit__ = AsyncMock()

        mock_pool.acquire.return_value = error_context

        repository = AsyncPostgresCourierRepository(mock_pool)

        with pytest.raises(Exception, match="Connection failed"):
            await repository.get(courier_id)
