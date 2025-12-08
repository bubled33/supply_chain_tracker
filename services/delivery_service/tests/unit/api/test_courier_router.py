import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.deps.getters import get_courier_service
from src.api.dto.courier import CourierDTO
from src.api.handlers.courier import courier_router

app = FastAPI()
app.include_router(courier_router)


@pytest.fixture
def mock_courier_service():
    return AsyncMock()


@pytest.fixture
def client(mock_courier_service):
    app.dependency_overrides[get_courier_service] = lambda: mock_courier_service

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def create_fake_courier_entity(courier_id=None, **kwargs):
    """Создает фейковую Courier Entity с Value Objects"""
    courier = MagicMock()
    courier.courier_id = courier_id or uuid4()

    # Name VO
    name_vo = MagicMock()
    name_vo.value = kwargs.get("name", "John Doe")
    courier.name = name_vo

    # ContactInfo VO
    contact_vo = MagicMock()
    contact_vo.value = kwargs.get("contact_info", "Phone: +79001234567, Email: john@example.com")
    courier.contact_info = contact_vo

    return courier


@patch("src.api.handlers.courier.CourierMapper")
def test_create_courier_success(mock_mapper, client, mock_courier_service):
    """Тест успешной регистрации курьера"""
    courier_id = uuid4()

    payload = {
        "name": "John Doe",
        "contact_info": "Phone: +79001234567, Email: john@example.com"
    }

    fake_entity = create_fake_courier_entity(
        courier_id=courier_id,
        name="John Doe",
        contact_info="Phone: +79001234567, Email: john@example.com"
    )

    mock_mapper.create_dto_to_entity.return_value = fake_entity
    mock_courier_service.create.return_value = fake_entity
    mock_mapper.entity_to_dto.return_value = CourierDTO(
        courier_id=courier_id,
        name="John Doe",
        contact_info="Phone: +79001234567, Email: john@example.com"
    )

    response = client.post("/couriers", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["courier_id"] == str(courier_id)
    assert data["name"] == "John Doe"
    assert data["contact_info"] == "Phone: +79001234567, Email: john@example.com"

    mock_mapper.create_dto_to_entity.assert_called_once()
    mock_courier_service.create.assert_awaited_once_with(fake_entity)
    mock_mapper.entity_to_dto.assert_called_once()


@patch("src.api.handlers.courier.CourierMapper")
def test_create_courier_minimal_data(mock_mapper, client, mock_courier_service):
    """Тест создания курьера с минимальными данными"""
    courier_id = uuid4()

    payload = {
        "name": "Jane Smith",
        "contact_info": "+79009876543"
    }

    fake_entity = create_fake_courier_entity(
        courier_id=courier_id,
        name="Jane Smith",
        contact_info="+79009876543"
    )

    mock_mapper.create_dto_to_entity.return_value = fake_entity
    mock_courier_service.create.return_value = fake_entity
    mock_mapper.entity_to_dto.return_value = CourierDTO(
        courier_id=courier_id,
        name="Jane Smith",
        contact_info="+79009876543"
    )

    response = client.post("/couriers", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Jane Smith"
    assert data["contact_info"] == "+79009876543"


@patch("src.api.handlers.courier.CourierMapper")
def test_get_courier_success(mock_mapper, client, mock_courier_service):
    """Тест получения курьера по ID"""
    courier_id = uuid4()

    fake_entity = create_fake_courier_entity(
        courier_id=courier_id,
        name="John Doe",
        contact_info="+79001234567"
    )

    mock_courier_service.get.return_value = fake_entity
    mock_mapper.entity_to_dto.return_value = CourierDTO(
        courier_id=courier_id,
        name="John Doe",
        contact_info="+79001234567"
    )

    response = client.get(f"/couriers/{courier_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["courier_id"] == str(courier_id)
    assert data["name"] == "John Doe"
    assert data["contact_info"] == "+79001234567"

    mock_courier_service.get.assert_awaited_once_with(courier_id)
    mock_mapper.entity_to_dto.assert_called_once()


@patch("src.api.handlers.courier.CourierMapper")
def test_get_courier_not_found(mock_mapper, client, mock_courier_service):
    """Тест получения несуществующего курьера"""
    courier_id = uuid4()
    mock_courier_service.get.return_value = None

    response = client.get(f"/couriers/{courier_id}")

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()

    mock_mapper.entity_to_dto.assert_not_called()


@patch("src.api.handlers.courier.CourierMapper")
def test_list_couriers_empty(mock_mapper, client, mock_courier_service):
    """Тест получения пустого списка курьеров"""
    mock_courier_service.get_all.return_value = []

    response = client.get("/couriers")

    assert response.status_code == 200
    data = response.json()
    assert data == []

    mock_courier_service.get_all.assert_awaited_once()


@patch("src.api.handlers.courier.CourierMapper")
def test_list_couriers_multiple(mock_mapper, client, mock_courier_service):
    """Тест получения списка курьеров"""
    courier1 = create_fake_courier_entity(
        courier_id=uuid4(),
        name="John Doe",
        contact_info="+79001234567"
    )
    courier2 = create_fake_courier_entity(
        courier_id=uuid4(),
        name="Jane Smith",
        contact_info="+79009876543"
    )

    mock_courier_service.get_all.return_value = [courier1, courier2]
    mock_mapper.entity_to_dto.side_effect = [
        CourierDTO(
            courier_id=courier1.courier_id,
            name="John Doe",
            contact_info="+79001234567"
        ),
        CourierDTO(
            courier_id=courier2.courier_id,
            name="Jane Smith",
            contact_info="+79009876543"
        )
    ]

    response = client.get("/couriers")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "John Doe"
    assert data[1]["name"] == "Jane Smith"

    mock_courier_service.get_all.assert_awaited_once()
    assert mock_mapper.entity_to_dto.call_count == 2


@patch("src.api.handlers.courier.CourierMapper")
def test_update_courier_success(mock_mapper, client, mock_courier_service):
    """Тест обновления данных курьера"""
    courier_id = uuid4()

    payload = {
        "name": "John Doe Updated",
        "contact_info": "Phone: +79001111111, Email: newemail@example.com"
    }

    existing_entity = create_fake_courier_entity(
        courier_id=courier_id,
        name="John Doe",
        contact_info="+79001234567"
    )

    updated_entity = create_fake_courier_entity(
        courier_id=courier_id,
        name="John Doe Updated",
        contact_info="Phone: +79001111111, Email: newemail@example.com"
    )

    mock_courier_service.get.return_value = existing_entity
    mock_mapper.update_entity_from_dto.return_value = updated_entity
    mock_courier_service.update.return_value = updated_entity
    mock_mapper.entity_to_dto.return_value = CourierDTO(
        courier_id=courier_id,
        name="John Doe Updated",
        contact_info="Phone: +79001111111, Email: newemail@example.com"
    )

    response = client.patch(f"/couriers/{courier_id}", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "John Doe Updated"
    assert data["contact_info"] == "Phone: +79001111111, Email: newemail@example.com"

    mock_courier_service.get.assert_awaited_once_with(courier_id)
    mock_mapper.update_entity_from_dto.assert_called_once()
    mock_courier_service.update.assert_awaited_once_with(updated_entity)


@patch("src.api.handlers.courier.CourierMapper")
def test_update_courier_partial(mock_mapper, client, mock_courier_service):
    """Тест частичного обновления курьера (только некоторые поля)"""
    courier_id = uuid4()

    payload = {
        "contact_info": "New phone: +79005555555"
    }

    existing_entity = create_fake_courier_entity(
        courier_id=courier_id,
        name="John Doe",
        contact_info="+79001234567"
    )

    updated_entity = create_fake_courier_entity(
        courier_id=courier_id,
        name="John Doe",
        contact_info="New phone: +79005555555"
    )

    mock_courier_service.get.return_value = existing_entity
    mock_mapper.update_entity_from_dto.return_value = updated_entity
    mock_courier_service.update.return_value = updated_entity
    mock_mapper.entity_to_dto.return_value = CourierDTO(
        courier_id=courier_id,
        name="John Doe",
        contact_info="New phone: +79005555555"
    )

    response = client.patch(f"/couriers/{courier_id}", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["contact_info"] == "New phone: +79005555555"
    assert data["name"] == "John Doe"  # Не изменилось


@patch("src.api.handlers.courier.CourierMapper")
def test_update_courier_not_found(mock_mapper, client, mock_courier_service):
    """Тест обновления несуществующего курьера"""
    courier_id = uuid4()

    payload = {
        "name": "New Name"
    }

    mock_courier_service.get.return_value = None

    response = client.patch(f"/couriers/{courier_id}", json=payload)

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()

    mock_mapper.update_entity_from_dto.assert_not_called()
    mock_courier_service.update.assert_not_awaited()


@patch("src.api.handlers.courier.CourierMapper")
def test_delete_courier_success(mock_mapper, client, mock_courier_service):
    """Тест удаления курьера"""
    courier_id = uuid4()

    fake_entity = create_fake_courier_entity(courier_id=courier_id)
    mock_courier_service.get.return_value = fake_entity

    response = client.delete(f"/couriers/{courier_id}")

    assert response.status_code == 204
    assert response.content == b""

    mock_courier_service.get.assert_awaited_once_with(courier_id)
    mock_courier_service.delete.assert_awaited_once_with(courier_id)


@patch("src.api.handlers.courier.CourierMapper")
def test_delete_courier_not_found(mock_mapper, client, mock_courier_service):
    """Тест удаления несуществующего курьера"""
    courier_id = uuid4()

    mock_courier_service.get.return_value = None

    response = client.delete(f"/couriers/{courier_id}")

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()

    mock_courier_service.delete.assert_not_awaited()
