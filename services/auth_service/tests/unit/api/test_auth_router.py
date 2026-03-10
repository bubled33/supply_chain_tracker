import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from fastapi import FastAPI
from fastapi.testclient import TestClient

from libs.auth.jwt import create_access_token
from libs.auth.models import UserInDB
from src.api.handlers.auth import auth_router
from src.api.deps.getters import get_auth_service, auth_provider
from src.domain.entities.user import User
from src.domain.errors.auth import UserAlreadyExistsError, InvalidCredentialsError, UserNotFoundError

TEST_SECRET = "test-secret-for-auth-service"
TEST_USERNAME = "alice"
TEST_EMAIL = "alice@test.com"
TEST_PASSWORD = "secret123"
TEST_USER_ID = uuid4()

test_app = FastAPI()
test_app.include_router(auth_router)


def _make_user(role: str = "operator") -> User:
    return User(
        user_id=TEST_USER_ID,
        username=TEST_USERNAME,
        email=TEST_EMAIL,
        hashed_password="hashed",
        role=role,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def _token(role: str = "operator") -> str:
    return create_access_token(
        data={"sub": TEST_USERNAME, "role": role},
        secret_key=TEST_SECRET,
        expires_minutes=60,
    )


@pytest.fixture(autouse=True)
def patch_auth_provider():
    original_secret = auth_provider._secret_key
    auth_provider._secret_key = TEST_SECRET
    yield
    auth_provider._secret_key = original_secret


@pytest.fixture
def mock_auth_service():
    return AsyncMock()


@pytest.fixture
def client(mock_auth_service):
    test_app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    with TestClient(test_app) as c:
        yield c
    test_app.dependency_overrides.clear()


def test_register_success(client, mock_auth_service):
    mock_auth_service.register = AsyncMock(return_value=_make_user())
    response = client.post("/auth/register", json={
        "username": TEST_USERNAME,
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == TEST_USERNAME
    assert data["role"] == "operator"


def test_register_duplicate(client, mock_auth_service):
    mock_auth_service.register = AsyncMock(side_effect=UserAlreadyExistsError("Username already exists"))
    response = client.post("/auth/register", json={
        "username": TEST_USERNAME,
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
    })
    assert response.status_code == 409


def test_login_success(client, mock_auth_service):
    user = _make_user()
    mock_auth_service.authenticate = AsyncMock(return_value=user)
    mock_auth_service.create_access_token = MagicMock(return_value="access-tok")
    mock_auth_service.create_refresh_token = AsyncMock(return_value="refresh-tok")

    response = client.post(
        "/auth/token",
        data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, mock_auth_service):
    mock_auth_service.authenticate = AsyncMock(side_effect=InvalidCredentialsError("Invalid"))
    response = client.post(
        "/auth/token",
        data={"username": TEST_USERNAME, "password": "wrong"},
    )
    assert response.status_code == 401


def test_refresh_success(client, mock_auth_service):
    mock_auth_service.refresh = AsyncMock(return_value=("new-access", "new-refresh"))
    response = client.post("/auth/refresh", json={"refresh_token": "some-raw-token"})
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == "new-access"
    assert data["refresh_token"] == "new-refresh"


def test_refresh_invalid(client, mock_auth_service):
    mock_auth_service.refresh = AsyncMock(side_effect=InvalidCredentialsError("Stale"))
    response = client.post("/auth/refresh", json={"refresh_token": "stale-token"})
    assert response.status_code == 401


def test_get_me_with_valid_token(client, mock_auth_service):
    mock_auth_service.get_me = AsyncMock(return_value=_make_user())
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {_token()}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == TEST_USERNAME


def test_get_me_without_token(client, mock_auth_service):
    response = client.get("/auth/me")
    assert response.status_code == 401
