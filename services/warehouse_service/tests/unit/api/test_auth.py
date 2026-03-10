import pytest
from unittest.mock import MagicMock, AsyncMock
from uuid import uuid4
from fastapi import FastAPI
from fastapi.testclient import TestClient

from libs.auth.jwt import create_access_token
from src.api.handlers.warehouse import warehouse_router
from src.api.deps.getters import get_warehouse_service, get_current_user, auth_provider

TEST_SECRET = "test-secret-for-auth-tests"
TEST_USERNAME = "testuser"

test_app = FastAPI()
test_app.include_router(warehouse_router)


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
    test_app.dependency_overrides[get_warehouse_service] = lambda: mock_service
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
    response = client.get("/warehouses")
    assert response.status_code == 401


def test_protected_route_with_valid_token(client):
    response = client.get("/warehouses", headers={"Authorization": f"Bearer {_token()}"})
    assert response.status_code == 200


def test_protected_route_with_expired_token(client):
    response = client.get("/warehouses", headers={"Authorization": f"Bearer {_expired_token()}"})
    assert response.status_code == 401


def test_protected_route_with_bad_signature(client):
    bad_token = create_access_token(
        data={"sub": TEST_USERNAME, "role": "operator"},
        secret_key="wrong-secret",
        expires_minutes=60,
    )
    response = client.get("/warehouses", headers={"Authorization": f"Bearer {bad_token}"})
    assert response.status_code == 401


def test_delete_warehouse_requires_admin(client):
    warehouse_id = uuid4()
    response = client.delete(
        f"/warehouses/{warehouse_id}",
        headers={"Authorization": f"Bearer {_token(role='operator')}"},
    )
    assert response.status_code == 403


def test_delete_warehouse_admin_succeeds(client):
    warehouse_id = uuid4()
    mock_service = MagicMock()
    mock_service.get = AsyncMock(return_value=MagicMock(warehouse_id=warehouse_id))
    mock_service.delete = AsyncMock(return_value=None)
    test_app.dependency_overrides[get_warehouse_service] = lambda: mock_service

    response = client.delete(
        f"/warehouses/{warehouse_id}",
        headers={"Authorization": f"Bearer {_token(role='admin')}"},
    )
    assert response.status_code == 204
