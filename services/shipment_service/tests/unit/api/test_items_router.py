import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from src.api.deps.getters import get_item_service, get_event_queue
from src.api.dto.item import ItemDTO
from src.domain.errors import ItemNotFoundError
from src.api.handlers.item import shipment_items_router, items_router

app = FastAPI()


@app.exception_handler(ItemNotFoundError)
async def item_not_found_handler(request: Request, exc: ItemNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


app.include_router(shipment_items_router)
app.include_router(items_router)


@pytest.fixture
def mock_item_service():
    return AsyncMock()


@pytest.fixture
def mock_event_queue():
    return AsyncMock()


@pytest.fixture
def client(mock_item_service, mock_event_queue):
    app.dependency_overrides[get_item_service] = lambda: mock_item_service
    app.dependency_overrides[get_event_queue] = lambda: mock_event_queue

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def create_fake_item_entity(item_id=None, shipment_id=None, **kwargs):
    item = MagicMock()
    item.item_id = item_id or uuid4()
    item.shipment_id = shipment_id or uuid4()
    item.name = kwargs.get("name", "Test Item")

    quantity_vo = MagicMock()
    quantity_vo.value = kwargs.get("quantity", 1)
    item.quantity = quantity_vo

    weight_vo = MagicMock()
    weight_vo.value = kwargs.get("weight", 1.0)
    item.weight = weight_vo

    return item


# ✅ Патчим в модуле handlers.item, где используется
@patch("src.api.handlers.item.ItemMapper")
def test_create_item_success(mock_mapper, client, mock_item_service, mock_event_queue):
    shipment_id = uuid4()
    item_id = uuid4()

    payload = {"name": "Box", "quantity": 5, "weight": 2.5}

    fake_entity = create_fake_item_entity(item_id=item_id, shipment_id=shipment_id, **payload)
    mock_mapper.create_dto_to_entity.return_value = fake_entity
    mock_mapper.entity_to_dto.return_value = ItemDTO(
        item_id=item_id, shipment_id=shipment_id, name="Box", quantity=5, weight=2.5
    )
    mock_item_service.create.return_value = fake_entity

    response = client.post(f"/shipments/{shipment_id}/items", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["item_id"] == str(item_id)
    assert data["name"] == "Box"

    mock_mapper.create_dto_to_entity.assert_called_once()
    mock_item_service.create.assert_awaited_once_with(fake_entity)
    mock_event_queue.publish_event.assert_called_once()


@patch("src.api.handlers.item.ItemMapper")
def test_get_item_not_found(mock_mapper, client, mock_item_service):
    item_id = uuid4()
    mock_item_service.get.return_value = None

    response = client.get(f"/items/{item_id}")

    assert response.status_code == 404
    mock_mapper.entity_to_dto.assert_not_called()


@patch("src.api.handlers.item.ItemMapper")
def test_increase_quantity_success(mock_mapper, client, mock_item_service, mock_event_queue):
    item_id = uuid4()
    shipment_id = uuid4()
    amount = 3

    fake_item = create_fake_item_entity(item_id=item_id, shipment_id=shipment_id, quantity=13)
    mock_item_service.increase_quantity.return_value = fake_item
    mock_mapper.entity_to_dto.return_value = ItemDTO(
        item_id=item_id, shipment_id=shipment_id, name="Test", quantity=13, weight=1.0
    )

    response = client.post(f"/items/{item_id}/increase-quantity?amount={amount}")

    assert response.status_code == 200
    assert response.json()["quantity"] == 13

    mock_item_service.increase_quantity.assert_awaited_once_with(item_id, amount)
    mock_event_queue.publish_event.assert_called_once()


@patch("src.api.handlers.item.ItemMapper")
def test_delete_item_success(mock_mapper, client, mock_item_service, mock_event_queue):
    item_id = uuid4()
    shipment_id = uuid4()

    fake_item = create_fake_item_entity(item_id=item_id, shipment_id=shipment_id)
    mock_item_service.get.return_value = fake_item

    response = client.delete(f"/items/{item_id}")

    assert response.status_code == 204
    assert response.content == b""

    mock_item_service.delete.assert_awaited_once_with(item_id)
    mock_event_queue.publish_event.assert_called_once()


# Добавьте в test_items_router.py

@patch("src.api.handlers.item.ItemMapper")
def test_list_shipment_items(mock_mapper, client, mock_item_service):
    """Тест получения всех items для конкретного shipment"""
    shipment_id = uuid4()
    item1 = create_fake_item_entity(item_id=uuid4(), shipment_id=shipment_id, name="Item 1")
    item2 = create_fake_item_entity(item_id=uuid4(), shipment_id=shipment_id, name="Item 2")

    mock_item_service.get_by_shipment.return_value = [item1, item2]
    mock_mapper.entity_to_dto.side_effect = [
        ItemDTO(item_id=item1.item_id, shipment_id=shipment_id, name="Item 1", quantity=5, weight=2.5),
        ItemDTO(item_id=item2.item_id, shipment_id=shipment_id, name="Item 2", quantity=3, weight=1.5)
    ]

    response = client.get(f"/shipments/{shipment_id}/items")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Item 1"
    assert data[1]["name"] == "Item 2"

    mock_item_service.get_by_shipment.assert_awaited_once_with(shipment_id)


@patch("src.api.handlers.item.ItemMapper")
def test_update_item(mock_mapper, client, mock_item_service, mock_event_queue):
    """Тест обновления item"""
    item_id = uuid4()
    shipment_id = uuid4()

    payload = {"name": "Updated Item", "quantity": 10}

    existing_item = create_fake_item_entity(item_id=item_id, shipment_id=shipment_id)
    updated_item = create_fake_item_entity(item_id=item_id, shipment_id=shipment_id, name="Updated Item", quantity=10)

    mock_item_service.get.return_value = existing_item
    mock_mapper.update_entity_from_dto.return_value = updated_item
    mock_item_service.update.return_value = updated_item
    mock_mapper.entity_to_dto.return_value = ItemDTO(
        item_id=item_id, shipment_id=shipment_id, name="Updated Item", quantity=10, weight=2.5
    )

    response = client.patch(f"/items/{item_id}", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Item"
    assert data["quantity"] == 10

    mock_item_service.update.assert_awaited_once()
    mock_event_queue.publish_event.assert_called_once()


@patch("src.api.handlers.item.ItemMapper")
def test_decrease_quantity_success(mock_mapper, client, mock_item_service, mock_event_queue):
    """Тест уменьшения количества item"""
    item_id = uuid4()
    shipment_id = uuid4()
    amount = 2

    fake_item = create_fake_item_entity(item_id=item_id, shipment_id=shipment_id, quantity=8)
    mock_item_service.decrease_quantity.return_value = fake_item
    mock_mapper.entity_to_dto.return_value = ItemDTO(
        item_id=item_id, shipment_id=shipment_id, name="Test", quantity=8, weight=1.0
    )

    response = client.post(f"/items/{item_id}/decrease-quantity?amount={amount}")

    assert response.status_code == 200
    assert response.json()["quantity"] == 8

    mock_item_service.decrease_quantity.assert_awaited_once_with(item_id, amount)
    mock_event_queue.publish_event.assert_called_once()


@patch("src.api.handlers.item.ItemMapper")
def test_update_item_weight(mock_mapper, client, mock_item_service, mock_event_queue):
    """Тест обновления веса item"""
    item_id = uuid4()
    shipment_id = uuid4()
    new_weight = 5.5

    fake_item = create_fake_item_entity(item_id=item_id, shipment_id=shipment_id, weight=new_weight)
    mock_item_service.update_weight.return_value = fake_item
    mock_mapper.entity_to_dto.return_value = ItemDTO(
        item_id=item_id, shipment_id=shipment_id, name="Test", quantity=10, weight=new_weight
    )

    response = client.patch(f"/items/{item_id}/weight?new_weight={new_weight}")

    assert response.status_code == 200
    assert response.json()["weight"] == new_weight

    mock_item_service.update_weight.assert_awaited_once_with(item_id, new_weight)
    mock_event_queue.publish_event.assert_called_once()


@patch("src.api.handlers.item.ItemMapper")
def test_get_shipment_total_weight(mock_mapper, client, mock_item_service):
    """Тест получения общего веса items в shipment"""
    shipment_id = uuid4()
    total_weight = 15.5

    mock_item_service.calculate_total_weight.return_value = total_weight

    response = client.get(f"/shipments/{shipment_id}/items/total-weight")

    assert response.status_code == 200
    data = response.json()
    assert data["total_weight"] == total_weight
    assert data["shipment_id"] == str(shipment_id)
    assert data["unit"] == "kg"

    mock_item_service.calculate_total_weight.assert_awaited_once_with(shipment_id)


@patch("src.api.handlers.item.ItemMapper")
def test_get_shipment_items_count(mock_mapper, client, mock_item_service):
    """Тест получения количества items в shipment"""
    shipment_id = uuid4()
    items_count = 7

    mock_item_service.get_items_count.return_value = items_count

    response = client.get(f"/shipments/{shipment_id}/items/count")

    assert response.status_code == 200
    data = response.json()
    assert data["items_count"] == items_count
    assert data["shipment_id"] == str(shipment_id)

    mock_item_service.get_items_count.assert_awaited_once_with(shipment_id)
