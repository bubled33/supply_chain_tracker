import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from fastapi import FastAPI
from fastapi.testclient import TestClient

from libs.auth.models import UserInDB
from src.api.deps.getters import get_warehouse_service, get_current_user
from src.api.dto.warehouse import WarehouseDTO
from src.api.handlers.warehouse import warehouse_router

_ADMIN_USER = UserInDB(username="admin", hashed_password="", role="admin")

app = FastAPI()
app.include_router(warehouse_router)


@pytest.fixture
def mock_warehouse_service():
    return AsyncMock()


@pytest.fixture
def client(mock_warehouse_service):
    app.dependency_overrides[get_warehouse_service] = lambda: mock_warehouse_service
    app.dependency_overrides[get_current_user] = lambda: MagicMock()

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def create_fake_warehouse_entity(warehouse_id=None, **kwargs):
    warehouse = MagicMock()
    warehouse.warehouse_id = warehouse_id or uuid4()
    warehouse.name = kwargs.get("name", "Main Warehouse")

    location_vo = MagicMock()
    location_vo.country = kwargs.get("country", "Russia")
    location_vo.city = kwargs.get("city", "Moscow")
    location_vo.address = kwargs.get("address", "Red Square 1")
    warehouse.location = location_vo

    return warehouse


@patch("src.api.handlers.warehouse.WarehouseMapper")
def test_create_warehouse_success(mock_mapper, client, mock_warehouse_service):
    warehouse_id = uuid4()
    payload = {"name": "Main Warehouse", "country": "Russia", "city": "Moscow", "address": "Red Square 1"}

    fake_entity = create_fake_warehouse_entity(warehouse_id=warehouse_id, **payload)
    mock_mapper.create_dto_to_entity.return_value = fake_entity
    mock_warehouse_service.create.return_value = fake_entity
    mock_mapper.entity_to_dto.return_value = WarehouseDTO(
        warehouse_id=warehouse_id,
        name="Main Warehouse",
        country="Russia",
        city="Moscow",
        address="Red Square 1",
    )

    response = client.post("/warehouses", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["warehouse_id"] == str(warehouse_id)
    assert data["name"] == "Main Warehouse"
    assert data["city"] == "Moscow"

    mock_warehouse_service.create.assert_awaited_once()


@patch("src.api.handlers.warehouse.WarehouseMapper")
def test_get_warehouse_success(mock_mapper, client, mock_warehouse_service):
    warehouse_id = uuid4()
    fake_entity = create_fake_warehouse_entity(warehouse_id=warehouse_id)
    mock_warehouse_service.get.return_value = fake_entity
    mock_mapper.entity_to_dto.return_value = WarehouseDTO(
        warehouse_id=warehouse_id, name="WH", country="RU", city="SPb", address=""
    )

    response = client.get(f"/warehouses/{warehouse_id}")

    assert response.status_code == 200
    mock_warehouse_service.get.assert_awaited_once_with(warehouse_id)


@patch("src.api.handlers.warehouse.WarehouseMapper")
def test_get_warehouse_not_found(mock_mapper, client, mock_warehouse_service):
    mock_warehouse_service.get.return_value = None

    response = client.get(f"/warehouses/{uuid4()}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@patch("src.api.handlers.warehouse.WarehouseMapper")
def test_list_warehouses_empty(mock_mapper, client, mock_warehouse_service):
    mock_warehouse_service.get_all.return_value = []

    response = client.get("/warehouses")

    assert response.status_code == 200
    assert response.json() == []
    mock_warehouse_service.get_all.assert_awaited_once()


@patch("src.api.handlers.warehouse.WarehouseMapper")
def test_list_warehouses_multiple(mock_mapper, client, mock_warehouse_service):
    wh1 = create_fake_warehouse_entity(warehouse_id=uuid4(), name="WH1")
    wh2 = create_fake_warehouse_entity(warehouse_id=uuid4(), name="WH2")
    mock_warehouse_service.get_all.return_value = [wh1, wh2]
    mock_mapper.entity_to_dto.side_effect = [
        WarehouseDTO(warehouse_id=wh1.warehouse_id, name="WH1", country="RU", city="Moscow", address=""),
        WarehouseDTO(warehouse_id=wh2.warehouse_id, name="WH2", country="RU", city="SPb", address=""),
    ]

    response = client.get("/warehouses")

    assert response.status_code == 200
    assert len(response.json()) == 2


@patch("src.api.handlers.warehouse.WarehouseMapper")
def test_update_warehouse_success(mock_mapper, client, mock_warehouse_service):
    warehouse_id = uuid4()
    existing = create_fake_warehouse_entity(warehouse_id=warehouse_id)
    updated = create_fake_warehouse_entity(warehouse_id=warehouse_id, name="Updated WH")

    mock_warehouse_service.get.return_value = existing
    mock_mapper.update_entity_from_dto.return_value = updated
    mock_warehouse_service.update.return_value = updated
    mock_mapper.entity_to_dto.return_value = WarehouseDTO(
        warehouse_id=warehouse_id, name="Updated WH", country="RU", city="Moscow", address=""
    )

    response = client.patch(f"/warehouses/{warehouse_id}", json={"name": "Updated WH"})

    assert response.status_code == 200
    assert response.json()["name"] == "Updated WH"
    mock_warehouse_service.update.assert_awaited_once_with(updated)


@patch("src.api.handlers.warehouse.WarehouseMapper")
def test_update_warehouse_not_found(mock_mapper, client, mock_warehouse_service):
    mock_warehouse_service.get.return_value = None

    response = client.patch(f"/warehouses/{uuid4()}", json={"name": "X"})

    assert response.status_code == 404


@patch("src.api.handlers.warehouse.WarehouseMapper")
def test_delete_warehouse_success(mock_mapper, client, mock_warehouse_service):
    warehouse_id = uuid4()
    app.dependency_overrides[get_current_user] = lambda: _ADMIN_USER
    mock_warehouse_service.get.return_value = create_fake_warehouse_entity(warehouse_id=warehouse_id)

    response = client.delete(f"/warehouses/{warehouse_id}")

    assert response.status_code == 204
    mock_warehouse_service.delete.assert_awaited_once_with(warehouse_id)


@patch("src.api.handlers.warehouse.WarehouseMapper")
def test_delete_warehouse_not_found(mock_mapper, client, mock_warehouse_service):
    app.dependency_overrides[get_current_user] = lambda: _ADMIN_USER
    mock_warehouse_service.get.return_value = None

    response = client.delete(f"/warehouses/{uuid4()}")

    assert response.status_code == 404
