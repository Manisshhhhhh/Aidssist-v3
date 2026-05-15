from __future__ import annotations

from sqlalchemy import inspect, text

from app.core.config import get_settings
from app.db.base import Base
from app.db.models import Workspace
from app.db.session import get_engine, new_session


DEFAULT_WORKSPACE_NAME = "Default Workspace"
DEFAULT_WORKSPACE_SLUG = "default"


def init_db() -> None:
    Base.metadata.create_all(bind=get_engine())
    add_backward_compatible_columns()
    ensure_default_workspace()
    validate_auth_configuration()
    validate_storage_configuration()


def ensure_default_workspace() -> Workspace:
    session = new_session()
    try:
        workspace = session.query(Workspace).filter(Workspace.slug == DEFAULT_WORKSPACE_SLUG).one_or_none()
        if workspace is None:
            workspace = Workspace(name=DEFAULT_WORKSPACE_NAME, slug=DEFAULT_WORKSPACE_SLUG)
            session.add(workspace)
            session.commit()
            session.refresh(workspace)
        return workspace
    finally:
        session.close()


def add_backward_compatible_columns() -> None:
    engine = get_engine()
    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    with engine.begin() as connection:
        if "workspaces" in tables:
            columns = {column["name"] for column in inspector.get_columns("workspaces")}
            if "owner_user_id" not in columns:
                connection.execute(text("ALTER TABLE workspaces ADD COLUMN owner_user_id INTEGER"))
        if "datasets" in tables:
            columns = {column["name"] for column in inspector.get_columns("datasets")}
            if "owner_user_id" not in columns:
                connection.execute(text("ALTER TABLE datasets ADD COLUMN owner_user_id INTEGER"))
        if "workspace_members" in tables:
            return


def validate_auth_configuration() -> None:
    settings = get_settings()
    unsafe_values = {None, "", "change-me", "dev-secret", "secret", "dev-only"}
    if settings.user_auth_enabled and settings.jwt_secret_key in unsafe_values:
        raise RuntimeError(
            "AIDSSIST_JWT_SECRET_KEY must be set to a strong non-default value when user auth is enabled."
        )


def validate_storage_configuration() -> None:
    settings = get_settings()
    backend = settings.storage_backend.lower()
    if backend == "local":
        return
    if backend != "s3":
        raise RuntimeError(f"Unsupported AIDSSIST_STORAGE_BACKEND '{settings.storage_backend}'.")
    missing = [
        name
        for name, value in {
            "AIDSSIST_S3_BUCKET": settings.s3_bucket,
            "AIDSSIST_S3_REGION": settings.s3_region,
            "AIDSSIST_S3_ACCESS_KEY_ID": settings.s3_access_key_id,
            "AIDSSIST_S3_SECRET_ACCESS_KEY": settings.s3_secret_access_key,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(
            "S3 storage is configured but required settings are missing: " + ", ".join(missing)
        )
