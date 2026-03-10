import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.testclient import TestClient

from libs.auth.models import UserInDB
from src.api.deps.getters import get_inventory_service, get_event_queue, get_current_user
from src.api.dto.inventory_record import InventoryRecordDTO
from src.api.handlers.inventory_record import inventory_router
from src.domain.entities.inventory_record import InventoryStatus

_ADMIN_USER = UserInDB(username="admin", hashed_password="", role="admin")

app = FastAPI()
app.include_router(inventory_router)


@pytest.fixture
def mock_inventory_service():
    return AsyncMock()


@pytest.fixture
def mock_event_queue():
    return AsyncMock()


@pytest.fixture
def client(mock_inventory_service, mock_event_queue):
    app.dependency_overrides[get_inventory_service] = lambda: mock_inventory_service
    app.dependency_overrides[get_event_queue] = lambda: mock_event_queue
    app.dependency_overrides[get_current_user] = lambda: MagicMock()

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def create_fake_record_entity(record_id=None, shipment_id=None, warehouse_id=None, **kwargs):
    record = MagicMock()
    record.record_id = record_id or uuid4()
    record.shipment_id = shipment_id or uuid4()
    record.warehouse_id = warehouse_id or uuid4()
    record.status = kwargs.get("status", InventoryStatus.RECEIVED)
    record.received_at = datetime.now(timezone.utc)
    record.updated_at = datetime.now(timezone.utc)
    return record


@patch("src.api.handlers.inventory_record.InventoryRecordMapper")
def test_create_inventory_record_success(mock_mapper, client, mock_inventory_service, mock_event_queue):
    warehouse_id = uuid4()
    shipment_id = uuid4()
    record_id = uuid4()
    now = datetime.now(timezone.utc)

    payload = {"shipment_id": str(shipment_id)}
    fake_entity = create_fake_record_entity(record_id=record_id, shipment_id=shipment_id, warehouse_id=warehouse_id)

    mock_mapper.create_dto_to_entity.return_value = fake_entity
    mock_inventory_service.create_record.return_value = fake_entity
    mock_mapper.entity_to_dto.return_value = InventoryRecordDTO(
        record_id=record_id,
        shipment_id=shipment_id,
        warehouse_id=warehouse_id,
        status=InventoryStatus.RECEIVED,
        received_at=now,
        updated_at=now,
    )

    response = client.post(f"/warehouses/{warehouse_id}/inventory", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["record_id"] == str(record_id)
    assert data["shipment_id"] == str(shipment_id)

    mock_inventory_service.create_record.assert_awaited_once()
    mock_event_queue.publish_event.assert_awaited_once()


@patch("src.api.handlers.inventory_record.InventoryRecordMapper")
def test_get_inventory_record_success(mock_mapper, client, mock_inventory_service):
    warehouse_id = uuid4()
    record_id = uuid4()
    now = datetime.now(timezone.utc)
    fake_entity = create_fake_record_entity(record_id=record_id, warehouse_id=warehouse_id)

    mock_inventory_service.get_record.return_value = fake_entity
    mock_mapper.entity_to_dto.return_value = InventoryRecordDTO(
        record_id=record_id,
        shipment_id=fake_entity.shipment_id,
        warehouse_id=warehouse_id,
        status=InventoryStatus.RECEIVED,
        received_at=now,
        updated_at=now,
    )

    response = client.get(f"/warehouses/{warehouse_id}/inventory/{record_id}")

    assert response.status_code == 200
    mock_inventory_service.get_record.assert_awaited_once_with(record_id)


@patch("src.api.handlers.inventory_record.InventoryRecordMapper")
def test_get_inventory_record_not_found(mock_mapper, client, mock_inventory_service):
    mock_inventory_service.get_record.return_value = None

    response = client.get(f"/warehouses/{uuid4()}/inventory/{uuid4()}")

    assert response.status_code == 404


@patch("src.api.handlers.inventory_record.InventoryRecordMapper")
def test_list_inventory_records_empty(mock_mapper, client, mock_inventory_service):
    warehouse_id = uuid4()
    shipment_id = uuid4()
    mock_inventory_service.list_records_by_shipment.return_value = []

    response = client.get(f"/warehouses/{warehouse_id}/inventory", params={"shipment_id": str(shipment_id)})

    assert response.status_code == 200
    assert response.json() == []


@patch("src.api.handlers.inventory_record.InventoryRecordMapper")
def test_update_inventory_record_status(mock_mapper, client, mock_inventory_service, mock_event_queue):
    warehouse_id = uuid4()
    record_id = uuid4()
    now = datetime.now(timezone.utc)
    existing = create_fake_record_entity(record_id=record_id, warehouse_id=warehouse_id)
    updated = create_fake_record_entity(record_id=record_id, warehouse_id=warehouse_id, status=InventoryStatus.STORED)

    mock_inventory_service.get_record.return_value = existing
    mock_inventory_service.update_status.return_value = updated
    mock_mapper.entity_to_dto.return_value = InventoryRecordDTO(
        record_id=record_id,
        shipment_id=existing.shipment_id,
        warehouse_id=warehouse_id,
        status=InventoryStatus.STORED,
        received_at=now,
        updated_at=now,
    )

    response = client.patch(
        f"/warehouses/{warehouse_id}/inventory/{record_id}",
        json={"status": "stored"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "stored"
    mock_event_queue.publish_event.assert_awaited_once()


@patch("src.api.handlers.inventory_record.InventoryRecordMapper")
def test_update_inventory_record_not_found(mock_mapper, client, mock_inventory_service):
    mock_inventory_service.get_record.return_value = None

    response = client.patch(
        f"/warehouses/{uuid4()}/inventory/{uuid4()}",
        json={"status": "stored"},
    )

    assert response.status_code == 404


@patch("src.api.handlers.inventory_record.InventoryRecordMapper")
def test_delete_inventory_record_success(mock_mapper, client, mock_inventory_service, mock_event_queue):
    warehouse_id = uuid4()
    record_id = uuid4()
    existing = create_fake_record_entity(record_id=record_id, warehouse_id=warehouse_id)
    mock_inventory_service.get_record.return_value = existing
    app.dependency_overrides[get_current_user] = lambda: _ADMIN_USER

    response = client.delete(f"/warehouses/{warehouse_id}/inventory/{record_id}")

    assert response.status_code == 204
    mock_inventory_service.delete_record.assert_awaited_once_with(record_id)
    mock_event_queue.publish_event.assert_awaited_once()


@patch("src.api.handlers.inventory_record.InventoryRecordMapper")
def test_delete_inventory_record_not_found(mock_mapper, client, mock_inventory_service):
    app.dependency_overrides[get_current_user] = lambda: _ADMIN_USER
    mock_inventory_service.get_record.return_value = None

    response = client.delete(f"/warehouses/{uuid4()}/inventory/{uuid4()}")

    assert response.status_code == 404
