from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from sqlalchemy import text

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.models import ArtifactRecord, JobRecord
from app.db.session import new_session
from app.models.preflight_models import PreflightCheck, PreflightResponse, PreflightStatus
from app.services import storage_service
from app.services.artifact_service import audit_artifacts


logger = get_logger(__name__)


def run_preflight() -> PreflightResponse:
    checks = [
        check_database(),
        check_storage_root("datasets_storage", storage_service.get_datasets_dir),
        check_storage_root("reports_storage", lambda: Path(get_settings().reports_local_root)),
        check_backup_dir(),
        check_artifacts(),
        check_stale_jobs(),
        check_llm_config(),
        check_jwt_config(),
        check_cors_config(),
        check_rate_limit_config(),
    ]
    return PreflightResponse(
        status=overall_status(checks),
        checks=checks,
        created_at=datetime.now(timezone.utc),
    )


def run_startup_preflight() -> None:
    settings = get_settings()
    if not settings.startup_preflight_enabled:
        return
    result = run_preflight()
    if result.status == "ok":
        logger.info("startup preflight passed")
        return
    for check in result.checks:
        if check.status != "ok":
            logger.warning(
                "startup preflight issue",
                extra={
                    "preflight_check": check.name,
                    "preflight_status": check.status,
                    "preflight_message": check.message,
                },
            )
    if result.status == "error" and settings.fail_fast_on_preflight_error:
        raise RuntimeError("Startup preflight failed: " + "; ".join(c.message for c in result.checks if c.status == "error"))


def check_database() -> PreflightCheck:
    try:
        session = new_session()
        try:
            session.execute(text("SELECT 1")).scalar()
        finally:
            session.close()
        return ok("database", "Database reachable.")
    except Exception as exc:  # pragma: no cover - defensive around driver failures
        return error("database", f"Database is not reachable: {safe_message(exc)}")


def check_storage_root(name: str, path_factory: Callable[[], Path]) -> PreflightCheck:
    try:
        root = path_factory().expanduser()
        root.mkdir(parents=True, exist_ok=True)
        probe = root / ".aidssist_preflight"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return ok(name, f"{name} exists and is writable.")
    except Exception as exc:
        return error(name, f"{name} is not writable: {safe_message(exc)}")


def check_backup_dir() -> PreflightCheck:
    return check_storage_root("backup_dir", lambda: Path(get_settings().backup_dir))


def check_artifacts() -> PreflightCheck:
    try:
        audit = audit_artifacts()
        missing = len(audit["missing_storage_objects"])
        total = audit["total_artifacts"]
        if missing:
            return warning("artifacts", f"{missing} of {total} active artifact records point to missing storage objects.")
        return ok("artifacts", f"{total} active artifact records checked.")
    except Exception as exc:
        return warning("artifacts", f"Artifact audit could not complete: {safe_message(exc)}")


def check_stale_jobs() -> PreflightCheck:
    settings = get_settings()
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=settings.job_stale_after_minutes)
    session = new_session()
    try:
        stale_count = (
            session.query(JobRecord)
            .filter(JobRecord.status == "running", JobRecord.started_at < cutoff)
            .count()
        )
    finally:
        session.close()
    if stale_count:
        return warning("stale_jobs", f"{stale_count} running job(s) are older than the stale threshold.")
    return ok("stale_jobs", "No stale running jobs detected.")


def check_llm_config() -> PreflightCheck:
    settings = get_settings()
    if not settings.llm_enabled:
        return ok("llm_config", "LLM features are disabled.")
    if settings.llm_provider != "gemini":
        return error("llm_config", f"Unsupported LLM provider '{settings.llm_provider}'.")
    if not settings.gemini_api_key:
        return error("llm_config", "LLM is enabled but GEMINI_API_KEY is not configured.")
    return ok("llm_config", "LLM provider configuration is present.")


def check_jwt_config() -> PreflightCheck:
    settings = get_settings()
    if not settings.user_auth_enabled:
        return ok("jwt_config", "User auth is disabled.")
    if not settings.jwt_secret_key or settings.jwt_secret_key in {"change-me", "dev-secret", "secret", "dev-only"}:
        return error("jwt_config", "User auth is enabled but JWT secret is missing or unsafe.")
    if len(settings.jwt_secret_key) < 24:
        return warning("jwt_config", "JWT secret is configured but short; use a long random value.")
    return ok("jwt_config", "JWT configuration is present.")


def check_cors_config() -> PreflightCheck:
    settings = get_settings()
    if settings.auth_enabled and "*" in settings.cors_origins:
        return error("cors_config", "Wildcard CORS origins are not allowed when API-key auth is enabled.")
    return ok("cors_config", "CORS configuration is sane.")


def check_rate_limit_config() -> PreflightCheck:
    settings = get_settings()
    if not settings.rate_limit_enabled:
        return warning("rate_limit_config", "Rate limiting is disabled.")
    if settings.rate_limit_requests <= 0 or settings.rate_limit_window_seconds <= 0:
        return error("rate_limit_config", "Rate limit request and window values must be positive.")
    return ok("rate_limit_config", "Rate limiting configuration is sane.")


def artifact_missing_count(limit: int = 10000) -> int:
    session = new_session()
    try:
        return session.query(ArtifactRecord).filter(ArtifactRecord.deleted_at.is_(None)).limit(limit).count()
    finally:
        session.close()


def overall_status(checks: list[PreflightCheck]) -> PreflightStatus:
    if any(check.status == "error" for check in checks):
        return "error"
    if any(check.status == "warning" for check in checks):
        return "warning"
    return "ok"


def ok(name: str, message: str) -> PreflightCheck:
    return PreflightCheck(name=name, status="ok", message=message)


def warning(name: str, message: str) -> PreflightCheck:
    return PreflightCheck(name=name, status="warning", message=message)


def error(name: str, message: str) -> PreflightCheck:
    return PreflightCheck(name=name, status="error", message=message)


def safe_message(exc: Exception) -> str:
    return str(exc).splitlines()[0][:300]
