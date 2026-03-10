from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from libs.auth.models import UserInDB

from src.api.deps.getters import get_auth_service, get_current_user
from src.api.dto.auth import RegisterRequest, TokenResponse, RefreshRequest, MeResponse
from src.app.services.auth import AuthService
from src.domain.errors.auth import UserAlreadyExistsError, InvalidCredentialsError, UserNotFoundError

auth_router = APIRouter(tags=["auth"])


@auth_router.post(
    "/auth/register",
    response_model=MeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
):
    try:
        user = await service.register(
            username=body.username,
            email=body.email,
            password=body.password,
            role=body.role,
        )
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return MeResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
    )


@auth_router.post("/auth/token", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
):
    try:
        user = await service.authenticate(form_data.username, form_data.password)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = service.create_access_token(user)
    refresh_token = await service.create_refresh_token(user)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@auth_router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_tokens(
    body: RefreshRequest,
    service: AuthService = Depends(get_auth_service),
):
    try:
        access_token, refresh_token = await service.refresh(body.refresh_token)
    except (InvalidCredentialsError, UserNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@auth_router.get("/auth/me", response_model=MeResponse)
async def get_me(
    current_user: UserInDB = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    try:
        user = await service.get_me(current_user.username)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return MeResponse(
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
    )
