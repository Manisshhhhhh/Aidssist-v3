from __future__ import annotations

from app.core.auth import create_access_token, hash_password, normalize_email, verify_password
from app.db.models import User
from app.models.auth_models import AuthUser, LoginResponse, RegisterRequest
from app.repositories import user_repository
from app.repositories.workspace_repository import ensure_personal_workspace


class DuplicateUserError(Exception):
    """Raised when registering an email that already exists."""


class InvalidCredentialsError(Exception):
    """Raised when login credentials are invalid."""


class InactiveUserError(Exception):
    """Raised when an inactive user attempts to authenticate."""


def register_user(request: RegisterRequest) -> AuthUser:
    email = normalize_email(str(request.email))
    if user_repository.get_user_by_email(email) is not None:
        raise DuplicateUserError("A user with this email already exists.")

    user = user_repository.create_user(
        email=email,
        full_name=request.full_name,
        password_hash=hash_password(request.password),
    )
    ensure_personal_workspace(user)
    return auth_user_from_record(user)


def login_user(email: str, password: str) -> LoginResponse:
    normalized_email = normalize_email(email)
    user = user_repository.get_user_by_email(normalized_email)
    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError("Invalid email or password.")
    if not user.is_active:
        raise InactiveUserError("This user account is inactive.")

    ensure_personal_workspace(user)
    token, expires_in = create_access_token(user.id, user.email)
    return LoginResponse(
        access_token=token,
        expires_in=expires_in,
        user=auth_user_from_record(user),
    )


def auth_user_from_record(user: User) -> AuthUser:
    return AuthUser(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_admin=user.is_admin,
        created_at=user.created_at,
    )
