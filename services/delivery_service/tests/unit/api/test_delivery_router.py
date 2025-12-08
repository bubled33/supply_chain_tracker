import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import date, datetime, timezone
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.deps.getters import get_delivery_service, get_courier_service, get_event_queue
from src.api.dto.delivery import DeliveryDTO
from src.domain.entities.delivery import DeliveryStatus
from src.api.handlers.delivery import delivery_router

app = FastAPI()
app.include_router(delivery_router)


@pytest.fixture
def mock_delivery_service():
    return AsyncMock()


@pytest.fixture
def mock_courier_service():
    return AsyncMock()


@pytest.fixture
def mock_event_queue():
    return AsyncMock()


@pytest.fixture
def client(mock_delivery_service, mock_courier_service, mock_event_queue):
    app.dependency_overrides[get_delivery_service] = lambda: mock_delivery_service
    app.dependency_overrides[get_courier_service] = lambda: mock_courier_service
    app.dependency_overrides[get_event_queue] = lambda: mock_event_queue

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def create_fake_courier_entity(courier_id=None, **kwargs):
    """Создает фейкового курьера"""
    courier = MagicMock()
    courier.courier_id = courier_id or uuid4()

    name_vo = MagicMock()
    name_vo.value = kwargs.get("name", "John Courier")
    courier.name = name_vo

    contact_vo = MagicMock()
    contact_vo.value = kwargs.get("contact_info", "+79001234567")
    courier.contact_info = contact_vo

    return courier


def create_fake_delivery_entity(delivery_id=None, **kwargs):
    """Создает фейковую Delivery Entity с Value Objects"""
    delivery = MagicMock()
    delivery.delivery_id = delivery_id or uuid4()
    delivery.shipment_id = kwargs.get("shipment_id", uuid4())

    delivery.courier = kwargs.get("courier", create_fake_courier_entity())

    status_vo = MagicMock()
    status_vo.value = kwargs.get("status", DeliveryStatus.ASSIGNED)
    delivery.status = status_vo

    delivery.estimated_arrival = kwargs.get("estimated_arrival")

    delivery.actual_arrival = kwargs.get("actual_arrival")

    created_at_vo = MagicMock()
    created_at_vo.value = kwargs.get("created_at", datetime.now(timezone.utc))
    delivery.created_at = created_at_vo

    updated_at_vo = MagicMock()
    updated_at_vo.value = kwargs.get("updated_at", datetime.now(timezone.utc))
    delivery.updated_at = updated_at_vo

    delivery.mark_delivered = MagicMock()

    return delivery


@patch("src.api.handlers.delivery.DeliveryMapper")
def test_create_delivery_success(mock_mapper, client, mock_delivery_service, mock_courier_service, mock_event_queue):
    """Тест успешного создания доставки"""
    delivery_id = uuid4()
    shipment_id = uuid4()
    courier_id = uuid4()
    estimated_arrival = date(2025, 12, 15)

    payload = {
        "shipment_id": str(shipment_id),
        "courier_id": str(courier_id),
        "estimated_arrival": str(estimated_arrival)
    }

    fake_courier = create_fake_courier_entity(courier_id=courier_id)
    fake_delivery = create_fake_delivery_entity(
        delivery_id=delivery_id,
        shipment_id=shipment_id,
        courier=fake_courier,
        estimated_arrival=estimated_arrival,
        status=DeliveryStatus.ASSIGNED
    )

    mock_courier_service.get.return_value = fake_courier
    mock_mapper.create_dto_to_entity.return_value = fake_delivery
    mock_delivery_service.create.return_value = fake_delivery
    mock_mapper.entity_to_dto.return_value = DeliveryDTO(
        delivery_id=delivery_id,
        shipment_id=shipment_id,
        courier_id=courier_id,
        status=DeliveryStatus.ASSIGNED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        estimated_arrival=estimated_arrival,
        actual_arrival=None
    )

    response = client.post("/deliveries", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["delivery_id"] == str(delivery_id)
    assert data["shipment_id"] == str(shipment_id)
    assert data["courier_id"] == str(courier_id)

    assert data["status"].lower() == "assigned"

    mock_courier_service.get.assert_awaited_once_with(courier_id)
    mock_mapper.create_dto_to_entity.assert_called_once()
    mock_delivery_service.create.assert_awaited_once_with(fake_delivery)
    mock_event_queue.publish_event.assert_called_once()


@patch("src.api.handlers.delivery.DeliveryMapper")
def test_create_delivery_courier_not_found(mock_mapper, client, mock_delivery_service, mock_courier_service,
                                           mock_event_queue):
    """Тест создания доставки с несуществующим курьером"""
    shipment_id = uuid4()
    courier_id = uuid4()

    payload = {
        "shipment_id": str(shipment_id),
        "courier_id": str(courier_id)
    }

    mock_courier_service.get.return_value = None

    response = client.post("/deliveries", json=payload)

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()

    mock_delivery_service.create.assert_not_awaited()
    mock_event_queue.publish_event.assert_not_called()


@patch("src.api.handlers.delivery.DeliveryMapper")
def test_get_delivery_success(mock_mapper, client, mock_delivery_service):
    """Тест получения доставки по ID"""
    delivery_id = uuid4()
    shipment_id = uuid4()
    courier_id = uuid4()

    fake_delivery = create_fake_delivery_entity(
        delivery_id=delivery_id,
        shipment_id=shipment_id
    )
    fake_delivery.courier.courier_id = courier_id

    mock_delivery_service.get.return_value = fake_delivery
    mock_mapper.entity_to_dto.return_value = DeliveryDTO(
        delivery_id=delivery_id,
        shipment_id=shipment_id,
        courier_id=courier_id,
        status=DeliveryStatus.ASSIGNED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        estimated_arrival=None,
        actual_arrival=None
    )

    response = client.get(f"/deliveries/{delivery_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["delivery_id"] == str(delivery_id)

    mock_delivery_service.get.assert_awaited_once_with(delivery_id)
    mock_mapper.entity_to_dto.assert_called_once()


@patch("src.api.handlers.delivery.DeliveryMapper")
def test_get_delivery_not_found(mock_mapper, client, mock_delivery_service):
    """Тест получения несуществующей доставки"""
    delivery_id = uuid4()
    mock_delivery_service.get.return_value = None

    response = client.get(f"/deliveries/{delivery_id}")

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()

    mock_mapper.entity_to_dto.assert_not_called()


@patch("src.api.handlers.delivery.DeliveryMapper")
def test_list_deliveries_empty(mock_mapper, client, mock_delivery_service):
    """Тест получения пустого списка доставок"""
    mock_delivery_service.get_all.return_value = []

    response = client.get("/deliveries")

    assert response.status_code == 200
    data = response.json()
    assert data == []

    mock_delivery_service.get_all.assert_awaited_once()


@patch("src.api.handlers.delivery.DeliveryMapper")
def test_list_deliveries_multiple(mock_mapper, client, mock_delivery_service):
    """Тест получения списка доставок"""
    delivery1 = create_fake_delivery_entity(delivery_id=uuid4())
    delivery2 = create_fake_delivery_entity(delivery_id=uuid4())

    mock_delivery_service.get_all.return_value = [delivery1, delivery2]
    mock_mapper.entity_to_dto.side_effect = [
        DeliveryDTO(
            delivery_id=delivery1.delivery_id,
            shipment_id=delivery1.shipment_id,
            courier_id=delivery1.courier.courier_id,
            status=DeliveryStatus.ASSIGNED,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ),
        DeliveryDTO(
            delivery_id=delivery2.delivery_id,
            shipment_id=delivery2.shipment_id,
            courier_id=delivery2.courier.courier_id,
            status=DeliveryStatus.ASSIGNED,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    ]

    response = client.get("/deliveries")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    mock_delivery_service.get_all.assert_awaited_once()
    assert mock_mapper.entity_to_dto.call_count == 2


@patch("src.api.handlers.delivery.DeliveryMapper")
def test_update_delivery_status(mock_mapper, client, mock_delivery_service, mock_courier_service, mock_event_queue):
    """Тест обновления статуса доставки"""
    delivery_id = uuid4()

    payload = {}

    existing_delivery = create_fake_delivery_entity(
        delivery_id=delivery_id,
        status=DeliveryStatus.ASSIGNED
    )

    updated_delivery = create_fake_delivery_entity(
        delivery_id=delivery_id,
        status=DeliveryStatus.IN_TRANSIT
    )

    mock_delivery_service.get.return_value = existing_delivery
    mock_mapper.update_entity_from_dto.return_value = updated_delivery
    mock_delivery_service.update.return_value = updated_delivery
    mock_mapper.entity_to_dto.return_value = DeliveryDTO(
        delivery_id=delivery_id,
        shipment_id=updated_delivery.shipment_id,
        courier_id=updated_delivery.courier.courier_id,
        status=DeliveryStatus.IN_TRANSIT,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    response = client.patch(f"/deliveries/{delivery_id}", json=payload)

    assert response.status_code == 200

    mock_delivery_service.update.assert_awaited_once()


@patch("src.api.handlers.delivery.DeliveryMapper")
def test_update_delivery_change_courier(mock_mapper, client, mock_delivery_service, mock_courier_service,
                                        mock_event_queue):
    """Тест переназначения курьера"""
    delivery_id = uuid4()
    old_courier_id = uuid4()
    new_courier_id = uuid4()

    payload = {
        "courier_id": str(new_courier_id)
    }

    old_courier = create_fake_courier_entity(courier_id=old_courier_id)
    new_courier = create_fake_courier_entity(courier_id=new_courier_id)

    existing_delivery = create_fake_delivery_entity(
        delivery_id=delivery_id,
        courier=old_courier
    )

    updated_delivery = create_fake_delivery_entity(
        delivery_id=delivery_id,
        courier=new_courier
    )

    mock_delivery_service.get.return_value = existing_delivery
    mock_courier_service.get.return_value = new_courier
    mock_mapper.update_entity_from_dto.return_value = updated_delivery
    mock_delivery_service.update.return_value = updated_delivery
    mock_mapper.entity_to_dto.return_value = DeliveryDTO(
        delivery_id=delivery_id,
        shipment_id=updated_delivery.shipment_id,
        courier_id=new_courier_id,
        status=DeliveryStatus.ASSIGNED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    response = client.patch(f"/deliveries/{delivery_id}", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["courier_id"] == str(new_courier_id)

    mock_courier_service.get.assert_awaited_once_with(new_courier_id)
    mock_delivery_service.update.assert_awaited_once()
    mock_event_queue.publish_event.assert_called_once()  # CourierAssigned event


@patch("src.api.handlers.delivery.DeliveryMapper")
def test_update_delivery_new_courier_not_found(mock_mapper, client, mock_delivery_service, mock_courier_service,
                                               mock_event_queue):
    """Тест переназначения на несуществующего курьера"""
    delivery_id = uuid4()
    new_courier_id = uuid4()

    payload = {
        "courier_id": str(new_courier_id)
    }

    existing_delivery = create_fake_delivery_entity(delivery_id=delivery_id)

    mock_delivery_service.get.return_value = existing_delivery
    mock_courier_service.get.return_value = None  # Курьер не найден

    response = client.patch(f"/deliveries/{delivery_id}", json=payload)

    assert response.status_code == 404
    data = response.json()
    assert "Courier" in data["detail"] and "not found" in data["detail"]

    mock_delivery_service.update.assert_not_awaited()


@patch("src.api.handlers.delivery.DeliveryMapper")
def test_mark_delivery_in_transit(mock_mapper, client, mock_delivery_service, mock_event_queue):
    """Тест перевода доставки в статус IN_TRANSIT"""
    delivery_id = uuid4()

    delivery = create_fake_delivery_entity(
        delivery_id=delivery_id,
        status=DeliveryStatus.ASSIGNED
    )

    updated_delivery = create_fake_delivery_entity(
        delivery_id=delivery_id,
        status=DeliveryStatus.IN_TRANSIT
    )

    mock_delivery_service.get.side_effect = [delivery, updated_delivery]  # Два вызова get

    mock_mapper.entity_to_dto.return_value = DeliveryDTO(
        delivery_id=delivery_id,
        shipment_id=updated_delivery.shipment_id,
        courier_id=updated_delivery.courier.courier_id,
        status=DeliveryStatus.IN_TRANSIT,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    response = client.post(f"/deliveries/{delivery_id}/start")

    assert response.status_code == 200
    data = response.json()
    assert data["status"].lower() == "in_transit"

    mock_delivery_service.mark_as_in_transit.assert_awaited_once_with(delivery_id)
    mock_event_queue.publish_event.assert_called_once()


@patch("src.api.handlers.delivery.DeliveryMapper")
def test_complete_delivery(mock_mapper, client, mock_delivery_service, mock_event_queue):
    """Тест завершения доставки"""
    delivery_id = uuid4()

    delivery = create_fake_delivery_entity(
        delivery_id=delivery_id,
        status=DeliveryStatus.IN_TRANSIT
    )

    completed_delivery = create_fake_delivery_entity(
        delivery_id=delivery_id,
        status=DeliveryStatus.DELIVERED,
        actual_arrival=date.today()
    )

    mock_delivery_service.get.return_value = delivery
    mock_delivery_service.update.return_value = completed_delivery

    mock_mapper.entity_to_dto.return_value = DeliveryDTO(
        delivery_id=delivery_id,
        shipment_id=completed_delivery.shipment_id,
        courier_id=completed_delivery.courier.courier_id,
        status=DeliveryStatus.DELIVERED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        actual_arrival=date.today()
    )

    response = client.post(f"/deliveries/{delivery_id}/complete")

    assert response.status_code == 200
    data = response.json()
    assert data["status"].lower() == "delivered"
    assert data["actual_arrival"] is not None

    delivery.mark_delivered.assert_called_once()
    mock_delivery_service.update.assert_awaited_once()
    mock_event_queue.publish_event.assert_called_once()


@patch("src.api.handlers.delivery.DeliveryMapper")
def test_complete_delivery_not_found(mock_mapper, client, mock_delivery_service, mock_event_queue):
    """Тест завершения несуществующей доставки"""
    delivery_id = uuid4()

    mock_delivery_service.get.return_value = None

    response = client.post(f"/deliveries/{delivery_id}/complete")

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()

    mock_delivery_service.update.assert_not_awaited()
    mock_event_queue.publish_event.assert_not_called()
