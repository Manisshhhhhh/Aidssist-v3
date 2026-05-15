import pytest
from fastapi.testclient import TestClient

from app.core import paths
from app.core.config import get_settings
from app.core.rate_limit import clear_rate_limit_state
from app.db.init_db import init_db
from app.db.session import reset_engine_cache
from app.main import app


@pytest.fixture(autouse=True)
def reset_security_settings(monkeypatch):
    for env_name in [
        "AIDSSIST_API_KEY",
        "AIDSSIST_AUTH_ENABLED",
        "AIDSSIST_MAX_UPLOAD_MB",
        "AIDSSIST_MAX_UPLOAD_SIZE_MB",
        "AIDSSIST_RATE_LIMIT_ENABLED",
        "AIDSSIST_RATE_LIMIT_REQUESTS",
        "AIDSSIST_RATE_LIMIT_WINDOW_SECONDS",
        "AIDSSIST_DATABASE_URL",
        "AIDSSIST_USER_AUTH_ENABLED",
        "AIDSSIST_JWT_SECRET_KEY",
        "AIDSSIST_JWT_ALGORITHM",
        "AIDSSIST_ACCESS_TOKEN_EXPIRE_MINUTES",
        "AIDSSIST_LOG_LEVEL",
        "AIDSSIST_LOG_FORMAT",
        "AIDSSIST_AUDIT_LOG_ENABLED",
        "AIDSSIST_REQUEST_LOGGING_ENABLED",
        "AIDSSIST_ERROR_DETAILS_ENABLED",
        "AIDSSIST_LLM_ENABLED",
        "AIDSSIST_LLM_PROVIDER",
        "GEMINI_API_KEY",
        "AIDSSIST_GEMINI_MODEL",
        "AIDSSIST_LLM_TIMEOUT_SECONDS",
        "AIDSSIST_LLM_MAX_INPUT_CHARS",
        "AIDSSIST_LLM_MAX_OUTPUT_TOKENS",
        "AIDSSIST_LLM_TEMPERATURE",
        "AIDSSIST_SAFE_MODE",
        "AIDSSIST_READ_ONLY_MODE",
        "AIDSSIST_BACKUP_DIR",
        "AIDSSIST_BACKUP_RETENTION_DAYS",
        "AIDSSIST_STARTUP_PREFLIGHT_ENABLED",
        "AIDSSIST_FAIL_FAST_ON_PREFLIGHT_ERROR",
        "AIDSSIST_AUTO_BACKUP_BEFORE_MIGRATION",
        "AIDSSIST_MAX_BACKUP_COUNT",
    ]:
        monkeypatch.delenv(env_name, raising=False)
    get_settings.cache_clear()
    reset_engine_cache()
    clear_rate_limit_state()
    yield
    get_settings.cache_clear()
    reset_engine_cache()
    clear_rate_limit_state()


@pytest.fixture()
def client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setattr(paths, "DATASETS_DIR", tmp_path / "datasets")
    monkeypatch.setenv("AIDSSIST_DATABASE_URL", f"sqlite:///{tmp_path / 'aidssist_test.db'}")
    get_settings.cache_clear()
    reset_engine_cache()
    init_db()
    return TestClient(app)
