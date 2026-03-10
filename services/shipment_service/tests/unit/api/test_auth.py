import pytest
from unittest.mock import MagicMock, AsyncMock
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from libs.auth.jwt import create_access_token
from src.api.handlers.shipment import shipments_router
from src.api.deps.getters import get_shipment_service, get_current_user, get_event_queue, auth_provider
from src.domain.errors import ShipmentNotFoundError

TEST_SECRET = "test-secret-for-auth-tests"
TEST_USERNAME = "testuser"

test_app = FastAPI()


@test_app.exception_handler(ShipmentNotFoundError)
async def shipment_not_found_handler(request: Request, exc: ShipmentNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


test_app.include_router(shipments_router)


@pytest.fixture(autouse=True)
def patch_auth_provider():
    original_secret = auth_provider._secret_key
    auth_provider._secret_key = TEST_SECRET
    yield
    auth_provider._secret_key = original_secret


@pytest.fixture
def client():
    mock_service = MagicMock()
    mock_service.get_all = AsyncMock(return_value=[])
    mock_service.get = AsyncMock(return_value=None)
    mock_service.delete = AsyncMock(return_value=None)
    mock_queue = AsyncMock()
    test_app.dependency_overrides[get_shipment_service] = lambda: mock_service
    test_app.dependency_overrides[get_event_queue] = lambda: mock_queue
    with TestClient(test_app) as c:
        yield c
    test_app.dependency_overrides.clear()


def _token(role: str = "operator") -> str:
    return create_access_token(
        data={"sub": TEST_USERNAME, "role": role},
        secret_key=TEST_SECRET,
        expires_minutes=60,
    )


def _expired_token() -> str:
    return create_access_token(
        data={"sub": TEST_USERNAME, "role": "operator"},
        secret_key=TEST_SECRET,
        expires_minutes=-1,
    )


def test_protected_route_without_token(client):
    response = client.get("/shipments")
    assert response.status_code == 401


def test_protected_route_with_valid_token(client):
    response = client.get("/shipments", headers={"Authorization": f"Bearer {_token()}"})
    assert response.status_code == 200


def test_protected_route_with_expired_token(client):
    response = client.get("/shipments", headers={"Authorization": f"Bearer {_expired_token()}"})
    assert response.status_code == 401


def test_protected_route_with_bad_signature(client):
    bad_token = create_access_token(
        data={"sub": TEST_USERNAME, "role": "operator"},
        secret_key="wrong-secret",
        expires_minutes=60,
    )
    response = client.get("/shipments", headers={"Authorization": f"Bearer {bad_token}"})
    assert response.status_code == 401


def test_delete_shipment_requires_admin(client):
    shipment_id = uuid4()
    response = client.delete(
        f"/shipments/{shipment_id}",
        headers={"Authorization": f"Bearer {_token(role='operator')}"},
    )
    assert response.status_code == 403


def test_delete_shipment_admin_succeeds(client):
    from datetime import date, datetime, timezone
    from unittest.mock import MagicMock

    shipment_id = uuid4()
    fake_entity = MagicMock()
    fake_entity.shipment_id = shipment_id

    status_vo = MagicMock()
    status_vo.value = "CREATED"
    fake_entity.status = status_vo

    updated_at_vo = MagicMock()
    updated_at_vo.value = datetime.now(timezone.utc)
    fake_entity.updated_at = updated_at_vo

    mock_service = MagicMock()
    mock_service.get = AsyncMock(return_value=fake_entity)
    mock_service.delete = AsyncMock(return_value=None)
    mock_queue = AsyncMock()

    test_app.dependency_overrides[get_shipment_service] = lambda: mock_service
    test_app.dependency_overrides[get_event_queue] = lambda: mock_queue

    response = client.delete(
        f"/shipments/{shipment_id}",
        headers={"Authorization": f"Bearer {_token(role='admin')}"},
    )
    assert response.status_code == 204
