import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from libs.messaging.base import Event, Command
from libs.messaging.commands import (
    ReleaseInventoryCommand,
    UnassignCourierCommand,
    CancelShipmentCommand
)
from src.domain.entities.saga_instance import SagaInstance, SagaStatus
from src.app.workers.compensation_worker import SagaCompensationWorker


# --- Fixtures ---

@pytest.fixture
def mock_event_queue():
    queue = AsyncMock()
    # Мокаем итератор consume_event, чтобы он возвращал список, который мы передадим, а потом останавливался
    queue.consume_event.return_value = AsyncMock()
    return queue


@pytest.fixture
def mock_saga_service():
    service = AsyncMock()
    return service


@pytest.fixture
def worker(mock_event_queue, mock_saga_service):
    return SagaCompensationWorker(mock_event_queue, mock_saga_service)


@pytest.fixture
def sample_saga_id():
    return uuid4()


@pytest.fixture
def sample_saga(sample_saga_id):
    return SagaInstance(
        saga_id=sample_saga_id,
        saga_type="delivery_saga",
        shipment_id=uuid4(),
        warehouse_id=uuid4(),
        delivery_id=uuid4(),
        status=SagaStatus.STARTED
    )


# --- Tests ---

@pytest.mark.asyncio
async def test_handle_failure_event_delivery_failed(worker, mock_saga_service, mock_event_queue, sample_saga):
    """Тест полного цикла компенсации при ошибке доставки"""

    # 1. Подготовка данных
    event = Event(
        event_type="delivery.failed",
        aggregate_id=uuid4(),
        aggregate_type="delivery",
        payload={"reason": "Driver lost"},
        correlation_id=sample_saga.saga_id
    )

    # Настраиваем моки сервиса
    mock_saga_service.get.return_value = sample_saga
    # trigger_compensation возвращает обновленную сагу
    mock_saga_service.trigger_compensation.return_value = sample_saga

    # 2. Вызов тестируемого метода (напрямую, без run цикла)
    await worker._handle_failure_event(event)

    # 3. Проверки

    # Проверяем переходы состояний
    mock_saga_service.trigger_compensation.assert_called_once_with(
        saga_id=sample_saga.saga_id,
        failed_step="delivery.failed"
    )

    mock_saga_service.fail_saga.assert_called_once()

    # Проверяем, что команды были отправлены в очередь
    # Для delivery.failed должно быть 3 команды: UnassignCourier, ReleaseInventory, CancelShipment
    assert mock_event_queue.publish_command.call_count == 3

    # Проверим типы отправленных команд
    calls = mock_event_queue.publish_command.call_args_list

    # 1. UnassignCourier
    cmd1 = calls[0][0][0]
    assert isinstance(cmd1, UnassignCourierCommand)
    assert cmd1.payload['reason'] == "Driver lost"

    # 2. ReleaseInventory
    cmd2 = calls[1][0][0]
    assert isinstance(cmd2, ReleaseInventoryCommand)

    # 3. CancelShipment
    cmd3 = calls[2][0][0]
    assert isinstance(cmd3, CancelShipmentCommand)


@pytest.mark.asyncio
async def test_handle_event_without_correlation_id(worker, mock_saga_service, mock_event_queue):
    """Тест игнорирования событий без correlation_id"""
    event = Event(
        event_type="delivery.failed",
        aggregate_id=uuid4(),
        aggregate_type="delivery",
        payload={},
        correlation_id=None
    )

    await worker._handle_failure_event(event)

    mock_saga_service.get.assert_not_called()
    mock_event_queue.publish_command.assert_not_called()


@pytest.mark.asyncio
async def test_handle_event_saga_not_found(worker, mock_saga_service, mock_event_queue):
    """Тест случая, когда сага не найдена в БД"""
    event = Event(
        event_type="delivery.failed",
        aggregate_id=uuid4(),
        aggregate_type="delivery",
        payload={},
        correlation_id=uuid4()
    )

    mock_saga_service.get.return_value = None

    await worker._handle_failure_event(event)

    mock_saga_service.trigger_compensation.assert_not_called()
    mock_event_queue.publish_command.assert_not_called()


@pytest.mark.asyncio
async def test_handle_event_saga_already_completed(worker, mock_saga_service, mock_event_queue, sample_saga):
    """Тест игнорирования уже завершенной саги"""
    sample_saga.status = SagaStatus.COMPLETED
    mock_saga_service.get.return_value = sample_saga

    event = Event(
        event_type="delivery.failed",  # Пришло событие ошибки, но сага уже завершена (странно, но бывает)
        aggregate_id=uuid4(),
        aggregate_type="delivery",
        payload={},
        correlation_id=sample_saga.saga_id
    )

    await worker._handle_failure_event(event)

    mock_saga_service.trigger_compensation.assert_not_called()
    mock_event_queue.publish_command.assert_not_called()


@pytest.mark.asyncio
async def test_race_condition_on_trigger(worker, mock_saga_service, mock_event_queue, sample_saga):
    """Тест обработки гонки состояний (ValueError из сервиса)"""
    event = Event(
        event_type="delivery.failed",
        aggregate_id=uuid4(),
        aggregate_type="delivery",
        payload={},
        correlation_id=sample_saga.saga_id
    )

    mock_saga_service.get.return_value = sample_saga
    # Имитируем, что пока мы думали, кто-то другой изменил статус саги
    mock_saga_service.trigger_compensation.side_effect = ValueError("Saga status mismatch")

    await worker._handle_failure_event(event)

    # Проверяем, что мы попытались переключить статус
    mock_saga_service.trigger_compensation.assert_called_once()

    # Но так как упала ошибка, команды компенсации НЕ полетели
    mock_event_queue.publish_command.assert_not_called()

    # И статус fail не выставился (так как мы считаем, что сагу уже обработали)
    mock_saga_service.fail_saga.assert_not_called()


@pytest.mark.asyncio
async def test_inventory_insufficient_compensation(worker, mock_saga_service, mock_event_queue, sample_saga):
    """Тест частичной компенсации (только Shipment)"""
    event = Event(
        event_type="inventory.insufficient",
        aggregate_id=uuid4(),
        aggregate_type="warehouse",
        payload={},
        correlation_id=sample_saga.saga_id
    )

    mock_saga_service.get.return_value = sample_saga
    mock_saga_service.trigger_compensation.return_value = sample_saga

    await worker._handle_failure_event(event)

    # Должна быть только 1 команда - отмена Shipment
    assert mock_event_queue.publish_command.call_count == 1

    cmd = mock_event_queue.publish_command.call_args[0][0]
    assert isinstance(cmd, CancelShipmentCommand)
