from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.config import get_settings
from app.core.user_auth import get_current_user_required
from app.db.models import User
from app.models.auth_models import AuthStatusResponse, AuthUser, LoginRequest, LoginResponse, RegisterRequest
from app.services.user_service import (
    DuplicateUserError,
    InactiveUserError,
    InvalidCredentialsError,
    auth_user_from_record,
    login_user,
    register_user,
)
from app.services.audit_service import record_event


router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/status", response_model=AuthStatusResponse)
def auth_status() -> AuthStatusResponse:
    settings = get_settings()
    return AuthStatusResponse(
        user_auth_enabled=settings.user_auth_enabled,
        api_key_auth_enabled=settings.auth_enabled,
    )


@router.post("/register", response_model=AuthUser, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request) -> AuthUser:
    try:
        user = register_user(payload)
        record_event(
            "auth.register",
            "register",
            "success",
            actor_user_id=user.id,
            metadata={"email": str(user.email)},
            request=request,
        )
        return user
    except DuplicateUserError as exc:
        record_event(
            "auth.register",
            "register",
            "failure",
            metadata={"email": str(payload.email), "reason": "duplicate"},
            request=request,
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request) -> LoginResponse:
    try:
        response = login_user(str(payload.email), payload.password)
        record_event(
            "auth.login",
            "login",
            "success",
            actor_user_id=response.user.id,
            metadata={"email": str(response.user.email)},
            request=request,
        )
        return response
    except InvalidCredentialsError as exc:
        record_event(
            "auth.login",
            "login",
            "failure",
            metadata={"email": str(payload.email), "reason": "invalid_credentials"},
            request=request,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except InactiveUserError as exc:
        record_event(
            "auth.login",
            "login",
            "failure",
            metadata={"email": str(payload.email), "reason": "inactive"},
            request=request,
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get("/me", response_model=AuthUser)
def me(current_user: User = Depends(get_current_user_required)) -> AuthUser:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication is required.")
    return auth_user_from_record(current_user)
