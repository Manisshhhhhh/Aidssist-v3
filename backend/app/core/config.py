from __future__ import annotations

import json
from functools import lru_cache
from typing import Optional

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://[::1]:5173",
    "http://[::1]:4173",
    "https://aidssist-v3.vercel.app",
]
DEFAULT_CORS_ORIGINS_RAW = ",".join(DEFAULT_CORS_ORIGINS)


class Settings(BaseSettings):
    app_name: str = "Aidssist V3 API"
    app_version: str = "0.1.0"
    environment: str = "development"
    max_upload_size_mb: int = Field(
        default=10,
        validation_alias=AliasChoices("AIDSSIST_MAX_UPLOAD_MB", "AIDSSIST_MAX_UPLOAD_SIZE_MB"),
    )
    auth_enabled: bool = False
    api_key: Optional[str] = None
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60
    async_jobs_enabled: bool = False
    job_poll_interval_seconds: int = 2
    job_max_attempts: int = 3
    job_stale_after_minutes: int = 30
    log_level: str = "INFO"
    log_format: str = "json"
    audit_log_enabled: bool = True
    request_logging_enabled: bool = True
    error_details_enabled: bool = False
    llm_enabled: bool = False
    llm_provider: str = "gemini"
    gemini_api_key: Optional[str] = Field(default=None, validation_alias="GEMINI_API_KEY")
    gemini_model: str = "gemini-2.5-flash"
    llm_timeout_seconds: int = 30
    llm_max_input_chars: int = 30000
    llm_max_output_tokens: int = 1200
    llm_temperature: float = 0.2
    safe_mode: bool = False
    read_only_mode: bool = False
    backup_dir: str = "./backups"
    backup_retention_days: int = 14
    startup_preflight_enabled: bool = True
    fail_fast_on_preflight_error: bool = False
    auto_backup_before_migration: bool = True
    max_backup_count: int = 20
    storage_backend: str = "local"
    storage_local_root: str = "./datasets"
    reports_local_root: str = "./reports"
    s3_bucket: Optional[str] = None
    s3_region: Optional[str] = None
    s3_endpoint_url: Optional[str] = None
    s3_access_key_id: Optional[str] = None
    s3_secret_access_key: Optional[str] = None
    s3_prefix: str = "aidssist"
    database_url: str = "sqlite:///./aidssist.db"
    user_auth_enabled: bool = False
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    cors_origins_raw: str = Field(
        default=DEFAULT_CORS_ORIGINS_RAW,
        validation_alias="AIDSSIST_CORS_ORIGINS",
    )
    cors_origin_regex: Optional[str] = (
        r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="AIDSSIST_",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return parse_cors_origins(self.cors_origins_raw) or DEFAULT_CORS_ORIGINS


def parse_cors_origins(value: str | list[str] | None) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [origin.strip().rstrip("/") for origin in value if origin and origin.strip()]

    text = value.strip()
    if not text:
        return []

    if text.startswith("["):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = []
        if isinstance(parsed, list):
            return parse_cors_origins(parsed)

    return [origin.strip().rstrip("/") for origin in text.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
