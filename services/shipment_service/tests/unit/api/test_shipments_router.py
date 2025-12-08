import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import date, datetime, timezone
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from src.api.deps.getters import get_shipment_service, get_event_queue
from src.api.dto.shipment import ShipmentDTO, LocationDTO
from src.domain.errors import ShipmentNotFoundError
from src.api.handlers.shipment import shipments_router

app = FastAPI()


@app.exception_handler(ShipmentNotFoundError)
async def shipment_not_found_handler(request: Request, exc: ShipmentNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


app.include_router(shipments_router)


@pytest.fixture
def mock_shipment_service():
    return AsyncMock()


@pytest.fixture
def mock_event_queue():
    return AsyncMock()


@pytest.fixture
def client(mock_shipment_service, mock_event_queue):
    app.dependency_overrides[get_shipment_service] = lambda: mock_shipment_service
    app.dependency_overrides[get_event_queue] = lambda: mock_event_queue

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def create_fake_shipment_entity(shipment_id=None, **kwargs):
    """Создает фейковую Shipment Entity с Value Objects"""
    shipment = MagicMock()
    shipment.shipment_id = shipment_id or uuid4()

    # Origin VO
    origin_vo = MagicMock()
    origin_vo.city = kwargs.get("origin_city", "Moscow")
    origin_vo.country = kwargs.get("origin_country", "Russia")
    origin_vo.address = kwargs.get("origin_address", "")
    shipment.origin = origin_vo

    # Destination VO
    dest_vo = MagicMock()
    dest_vo.city = kwargs.get("dest_city", "London")
    dest_vo.country = kwargs.get("dest_country", "UK")
    dest_vo.address = kwargs.get("dest_address", "")
    shipment.destination = dest_vo

    # Departure date VO
    departure_vo = MagicMock()
    departure_vo.value = kwargs.get("departure_date", date(2025, 12, 10))
    shipment.departure_date = departure_vo

    # Arrival date VO (optional)
    arrival_date = kwargs.get("arrival_date")
    if arrival_date:
        arrival_vo = MagicMock()
        arrival_vo.value = arrival_date
        shipment.arrival_date = arrival_vo
    else:
        shipment.arrival_date = None

    # Status VO
    status_vo = MagicMock()
    status_vo.value = kwargs.get("status", "CREATED")
    shipment.status = status_vo

    # Timestamps VO
    created_at_vo = MagicMock()
    created_at_vo.value = kwargs.get("created_at", datetime.now(timezone.utc))
    shipment.created_at = created_at_vo

    updated_at_vo = MagicMock()
    updated_at_vo.value = kwargs.get("updated_at", datetime.now(timezone.utc))
    shipment.updated_at = updated_at_vo

    return shipment


@patch("src.api.handlers.shipment.ShipmentMapper")
def test_create_shipment_success(mock_mapper, client, mock_shipment_service, mock_event_queue):
    """Тест успешного создания shipment"""
    shipment_id = uuid4()

    payload = {
        "origin": {"country": "Russia", "city": "Moscow", "address": "Red Square"},
        "destination": {"country": "UK", "city": "London", "address": "Trafalgar Square"},
        "departure_date": "2025-12-10"
    }

    fake_entity = create_fake_shipment_entity(
        shipment_id=shipment_id,
        origin_city="Moscow",
        dest_city="London"
    )

    mock_mapper.create_dto_to_entity.return_value = fake_entity
    mock_shipment_service.create.return_value = fake_entity
    mock_mapper.entity_to_dto.return_value = ShipmentDTO(
        shipment_id=shipment_id,
        origin=LocationDTO(country="Russia", city="Moscow", address="Red Square"),
        destination=LocationDTO(country="UK", city="London", address="Trafalgar Square"),
        departure_date=date(2025, 12, 10),
        arrival_date=None,
        status="CREATED",
        created_at="2025-12-08T00:00:00Z",
        updated_at="2025-12-08T00:00:00Z"
    )

    response = client.post("/shipments", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["shipment_id"] == str(shipment_id)
    assert data["status"] == "CREATED"

    mock_mapper.create_dto_to_entity.assert_called_once()
    mock_shipment_service.create.assert_awaited_once_with(fake_entity)
    mock_event_queue.publish_event.assert_called_once()


@patch("src.api.handlers.shipment.ShipmentMapper")
def test_get_shipment_success(mock_mapper, client, mock_shipment_service):
    """Тест получения shipment по ID"""
    shipment_id = uuid4()

    fake_entity = create_fake_shipment_entity(shipment_id=shipment_id)
    mock_shipment_service.get.return_value = fake_entity
    mock_mapper.entity_to_dto.return_value = ShipmentDTO(
        shipment_id=shipment_id,
        origin=LocationDTO(country="Russia", city="Moscow"),
        destination=LocationDTO(country="UK", city="London"),
        departure_date=date(2025, 12, 10),
        arrival_date=None,
        status="CREATED",
        created_at="2025-12-08T00:00:00Z",
        updated_at="2025-12-08T00:00:00Z"
    )

    response = client.get(f"/shipments/{shipment_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["shipment_id"] == str(shipment_id)

    mock_shipment_service.get.assert_awaited_once_with(shipment_id)
    mock_mapper.entity_to_dto.assert_called_once()


@patch("src.api.handlers.shipment.ShipmentMapper")
def test_get_shipment_not_found(mock_mapper, client, mock_shipment_service):
    """Тест получения несуществующего shipment"""
    shipment_id = uuid4()
    mock_shipment_service.get.return_value = None

    response = client.get(f"/shipments/{shipment_id}")

    assert response.status_code == 404
    mock_mapper.entity_to_dto.assert_not_called()


@patch("src.api.handlers.shipment.ShipmentMapper")
def test_list_shipments(mock_mapper, client, mock_shipment_service):
    """Тест получения списка всех shipments"""
    shipment1 = create_fake_shipment_entity(shipment_id=uuid4())
    shipment2 = create_fake_shipment_entity(shipment_id=uuid4())

    mock_shipment_service.get_all.return_value = [shipment1, shipment2]
    mock_mapper.entity_to_dto.side_effect = [
        ShipmentDTO(
            shipment_id=shipment1.shipment_id,
            origin=LocationDTO(country="Russia", city="Moscow"),
            destination=LocationDTO(country="UK", city="London"),
            departure_date=date(2025, 12, 10),
            arrival_date=None,
            status="CREATED",
            created_at="2025-12-08T00:00:00Z",
            updated_at="2025-12-08T00:00:00Z"
        ),
        ShipmentDTO(
            shipment_id=shipment2.shipment_id,
            origin=LocationDTO(country="USA", city="New York"),
            destination=LocationDTO(country="France", city="Paris"),
            departure_date=date(2025, 12, 15),
            arrival_date=None,
            status="CREATED",
            created_at="2025-12-08T00:00:00Z",
            updated_at="2025-12-08T00:00:00Z"
        )
    ]

    response = client.get("/shipments")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    mock_shipment_service.get_all.assert_awaited_once()


@patch("src.api.handlers.shipment.ShipmentMapper")
def test_update_shipment_success(mock_mapper, client, mock_shipment_service, mock_event_queue):
    """Тест обновления shipment"""
    shipment_id = uuid4()

    payload = {
        "status": "RECEIVED"
    }

    fake_entity = create_fake_shipment_entity(shipment_id=shipment_id)
    updated_entity = create_fake_shipment_entity(shipment_id=shipment_id, status="RECEIVED")

    mock_shipment_service.get.return_value = fake_entity
    mock_mapper.update_entity_from_dto.return_value = updated_entity
    mock_shipment_service.update.return_value = updated_entity
    mock_mapper.entity_to_dto.return_value = ShipmentDTO(
        shipment_id=shipment_id,
        origin=LocationDTO(country="Russia", city="Moscow"),
        destination=LocationDTO(country="UK", city="London"),
        departure_date=date(2025, 12, 10),
        arrival_date=None,
        status="RECEIVED",
        created_at="2025-12-08T00:00:00Z",
        updated_at="2025-12-08T01:00:00Z"
    )

    response = client.patch(f"/shipments/{shipment_id}", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "RECEIVED"

    mock_shipment_service.update.assert_awaited_once()
    mock_event_queue.publish_event.assert_called_once()


@patch("src.api.handlers.shipment.ShipmentMapper")
def test_delete_shipment_success(mock_mapper, client, mock_shipment_service, mock_event_queue):
    """Тест удаления shipment"""
    shipment_id = uuid4()

    fake_entity = create_fake_shipment_entity(shipment_id=shipment_id)
    mock_shipment_service.get.return_value = fake_entity

    response = client.delete(f"/shipments/{shipment_id}")

    assert response.status_code == 204
    assert response.content == b""

    mock_shipment_service.delete.assert_awaited_once_with(shipment_id)
    mock_event_queue.publish_event.assert_called_once()


@patch("src.api.handlers.shipment.ShipmentMapper")
def test_mark_shipment_received(mock_mapper, client, mock_shipment_service, mock_event_queue):
    """Тест перевода shipment в статус RECEIVED"""
    shipment_id = uuid4()

    fake_entity = create_fake_shipment_entity(shipment_id=shipment_id, status="RECEIVED")
    mock_shipment_service.mark_as_received.return_value = fake_entity
    mock_mapper.entity_to_dto.return_value = ShipmentDTO(
        shipment_id=shipment_id,
        origin=LocationDTO(country="Russia", city="Moscow"),
        destination=LocationDTO(country="UK", city="London"),
        departure_date=date(2025, 12, 10),
        arrival_date=None,
        status="RECEIVED",
        created_at="2025-12-08T00:00:00Z",
        updated_at="2025-12-08T01:00:00Z"
    )

    response = client.post(f"/shipments/{shipment_id}/receive")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "RECEIVED"

    mock_shipment_service.mark_as_received.assert_awaited_once_with(shipment_id)
    mock_event_queue.publish_event.assert_called_once()


@patch("src.api.handlers.shipment.ShipmentMapper")
def test_list_active_shipments(mock_mapper, client, mock_shipment_service):
    """Тест получения активных shipments"""
    shipment1 = create_fake_shipment_entity(shipment_id=uuid4(), status="IN_TRANSIT")

    mock_shipment_service.get_active_shipments.return_value = [shipment1]
    mock_mapper.entity_to_dto.return_value = ShipmentDTO(
        shipment_id=shipment1.shipment_id,
        origin=LocationDTO(country="Russia", city="Moscow"),
        destination=LocationDTO(country="UK", city="London"),
        departure_date=date(2025, 12, 10),
        arrival_date=None,
        status="IN_TRANSIT",
        created_at="2025-12-08T00:00:00Z",
        updated_at="2025-12-08T01:00:00Z"
    )

    response = client.get("/shipments/status/active")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1

    mock_shipment_service.get_active_shipments.assert_awaited_once()


@patch("src.api.handlers.shipment.ShipmentMapper")
def test_mark_shipment_ready_for_delivery(mock_mapper, client, mock_shipment_service, mock_event_queue):
    """Тест перевода shipment в статус READY_FOR_DELIVERY"""
    shipment_id = uuid4()

    fake_entity = create_fake_shipment_entity(shipment_id=shipment_id, status="READY_FOR_DELIVERY")
    mock_shipment_service.mark_as_ready_for_delivery.return_value = fake_entity
    mock_mapper.entity_to_dto.return_value = ShipmentDTO(
        shipment_id=shipment_id,
        origin=LocationDTO(country="Russia", city="Moscow"),
        destination=LocationDTO(country="UK", city="London"),
        departure_date=date(2025, 12, 10),
        arrival_date=None,
        status="READY_FOR_DELIVERY",
        created_at="2025-12-08T00:00:00Z",
        updated_at="2025-12-08T01:00:00Z"
    )

    response = client.post(f"/shipments/{shipment_id}/ready-for-delivery")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "READY_FOR_DELIVERY"

    mock_shipment_service.mark_as_ready_for_delivery.assert_awaited_once_with(shipment_id)
    mock_event_queue.publish_event.assert_called_once()


@patch("src.api.handlers.shipment.ShipmentMapper")
def test_mark_shipment_in_transit(mock_mapper, client, mock_shipment_service, mock_event_queue):
    """Тест перевода shipment в статус IN_TRANSIT"""
    shipment_id = uuid4()

    fake_entity = create_fake_shipment_entity(shipment_id=shipment_id, status="IN_TRANSIT")
    mock_shipment_service.mark_as_in_transit.return_value = fake_entity
    mock_mapper.entity_to_dto.return_value = ShipmentDTO(
        shipment_id=shipment_id,
        origin=LocationDTO(country="Russia", city="Moscow"),
        destination=LocationDTO(country="UK", city="London"),
        departure_date=date(2025, 12, 10),
        arrival_date=None,
        status="IN_TRANSIT",
        created_at="2025-12-08T00:00:00Z",
        updated_at="2025-12-08T01:00:00Z"
    )

    response = client.post(f"/shipments/{shipment_id}/in-transit")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "IN_TRANSIT"

    mock_shipment_service.mark_as_in_transit.assert_awaited_once_with(shipment_id)
    mock_event_queue.publish_event.assert_called_once()


@patch("src.api.handlers.shipment.ShipmentMapper")
def test_mark_shipment_delivered(mock_mapper, client, mock_shipment_service, mock_event_queue):
    """Тест перевода shipment в статус DELIVERED"""
    shipment_id = uuid4()
    arrival_date = date.today()

    fake_entity = create_fake_shipment_entity(
        shipment_id=shipment_id,
        status="DELIVERED",
        arrival_date=arrival_date
    )
    mock_shipment_service.mark_as_delivered.return_value = fake_entity
    mock_mapper.entity_to_dto.return_value = ShipmentDTO(
        shipment_id=shipment_id,
        origin=LocationDTO(country="Russia", city="Moscow"),
        destination=LocationDTO(country="UK", city="London"),
        departure_date=date(2025, 12, 10),
        arrival_date=arrival_date,
        status="DELIVERED",
        created_at="2025-12-08T00:00:00Z",
        updated_at="2025-12-08T01:00:00Z"
    )

    response = client.post(f"/shipments/{shipment_id}/delivered")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "DELIVERED"
    assert data["arrival_date"] == str(arrival_date)

    mock_shipment_service.mark_as_delivered.assert_awaited_once()
    mock_event_queue.publish_event.assert_called_once()


@patch("src.api.handlers.shipment.ShipmentMapper")
def test_mark_shipment_completed(mock_mapper, client, mock_shipment_service, mock_event_queue):
    """Тест перевода shipment в статус COMPLETED"""
    shipment_id = uuid4()

    fake_entity = create_fake_shipment_entity(shipment_id=shipment_id, status="COMPLETED")
    mock_shipment_service.mark_as_completed.return_value = fake_entity
    mock_mapper.entity_to_dto.return_value = ShipmentDTO(
        shipment_id=shipment_id,
        origin=LocationDTO(country="Russia", city="Moscow"),
        destination=LocationDTO(country="UK", city="London"),
        departure_date=date(2025, 12, 10),
        arrival_date=date(2025, 12, 15),
        status="COMPLETED",
        created_at="2025-12-08T00:00:00Z",
        updated_at="2025-12-08T01:00:00Z"
    )

    response = client.post(f"/shipments/{shipment_id}/complete")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"

    mock_shipment_service.mark_as_completed.assert_awaited_once_with(shipment_id)
    mock_event_queue.publish_event.assert_called_once()


@patch("src.api.handlers.shipment.ShipmentMapper")
def test_list_in_transit_shipments(mock_mapper, client, mock_shipment_service):
    """Тест получения shipments в пути"""
    shipment1 = create_fake_shipment_entity(shipment_id=uuid4(), status="IN_TRANSIT")
    shipment2 = create_fake_shipment_entity(shipment_id=uuid4(), status="IN_TRANSIT")

    mock_shipment_service.get_in_transit_shipments.return_value = [shipment1, shipment2]
    mock_mapper.entity_to_dto.side_effect = [
        ShipmentDTO(
            shipment_id=shipment1.shipment_id,
            origin=LocationDTO(country="Russia", city="Moscow"),
            destination=LocationDTO(country="UK", city="London"),
            departure_date=date(2025, 12, 10),
            arrival_date=None,
            status="IN_TRANSIT",
            created_at="2025-12-08T00:00:00Z",
            updated_at="2025-12-08T01:00:00Z"
        ),
        ShipmentDTO(
            shipment_id=shipment2.shipment_id,
            origin=LocationDTO(country="USA", city="New York"),
            destination=LocationDTO(country="France", city="Paris"),
            departure_date=date(2025, 12, 11),
            arrival_date=None,
            status="IN_TRANSIT",
            created_at="2025-12-08T00:00:00Z",
            updated_at="2025-12-08T01:00:00Z"
        )
    ]

    response = client.get("/shipments/status/in-transit")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(s["status"] == "IN_TRANSIT" for s in data)

    mock_shipment_service.get_in_transit_shipments.assert_awaited_once()
