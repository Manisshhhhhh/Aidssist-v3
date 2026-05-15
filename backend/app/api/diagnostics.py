from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func

from app.core.config import get_settings
from app.core.security import require_api_key
from app.core.user_auth import get_current_user_required
from app.db.models import ArtifactRecord, AuditLogRecord, DatasetRecord, JobRecord, User, Workspace
from app.db.session import new_session
from app.models.diagnostic_models import (
    DiagnosticCounts,
    JobDiagnosticCounts,
    RecentErrorDiagnosticsResponse,
    RecentFailedJob,
    SystemDiagnosticsResponse,
)


router = APIRouter(prefix="/diagnostics", tags=["diagnostics"], dependencies=[Depends(require_api_key)])


@router.get("/system", response_model=SystemDiagnosticsResponse)
def system_diagnostics(current_user: Optional[User] = Depends(get_current_user_required)) -> SystemDiagnosticsResponse:
    ensure_admin_or_local(current_user)
    settings = get_settings()
    session = new_session()
    try:
        queued = count_jobs(session, "queued")
        running = count_jobs(session, "running")
        failed = count_jobs(session, "failed")
        return SystemDiagnosticsResponse(
            app_version=settings.app_version,
            environment=settings.environment,
            database_type=database_type(settings.database_url),
            storage_backend=settings.storage_backend,
            async_jobs_enabled=settings.async_jobs_enabled,
            user_auth_enabled=settings.user_auth_enabled,
            api_key_auth_enabled=settings.auth_enabled,
            rate_limit_enabled=settings.rate_limit_enabled,
            audit_log_enabled=settings.audit_log_enabled,
            request_logging_enabled=settings.request_logging_enabled,
            llm_enabled=settings.llm_enabled,
            llm_provider=settings.llm_provider,
            llm_model=settings.gemini_model if settings.llm_provider == "gemini" else "",
            llm_key_configured=bool(settings.gemini_api_key),
            counts=DiagnosticCounts(
                workspaces=session.query(func.count(Workspace.id)).scalar() or 0,
                datasets=session.query(func.count(DatasetRecord.id)).scalar() or 0,
                artifacts=session.query(func.count(ArtifactRecord.id)).scalar() or 0,
                jobs=JobDiagnosticCounts(queued=queued, running=running, failed=failed),
            ),
            created_at=datetime.now(timezone.utc),
        )
    finally:
        session.close()


@router.get("/errors/recent", response_model=RecentErrorDiagnosticsResponse)
def recent_errors(current_user: Optional[User] = Depends(get_current_user_required)) -> RecentErrorDiagnosticsResponse:
    ensure_admin_or_local(current_user)
    session = new_session()
    try:
        failed_jobs = (
            session.query(JobRecord)
            .filter(JobRecord.status == "failed")
            .order_by(JobRecord.finished_at.desc(), JobRecord.id.desc())
            .limit(20)
            .all()
        )
        failed_audit_count = (
            session.query(func.count(AuditLogRecord.id)).filter(AuditLogRecord.outcome == "failure").scalar() or 0
        )
        return RecentErrorDiagnosticsResponse(
            failed_jobs=[
                RecentFailedJob(
                    job_id=job.job_id,
                    job_type=job.job_type,
                    dataset_id=job.dataset_id,
                    error_message=job.error_message,
                    finished_at=job.finished_at,
                )
                for job in failed_jobs
            ],
            failed_audit_event_count=failed_audit_count,
            created_at=datetime.now(timezone.utc),
        )
    finally:
        session.close()


def ensure_admin_or_local(current_user: Optional[User]) -> None:
    if not get_settings().user_auth_enabled:
        return
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication is required.")
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access is required.")


def count_jobs(session, status_value: str) -> int:
    return session.query(func.count(JobRecord.id)).filter(JobRecord.status == status_value).scalar() or 0


def database_type(database_url: str) -> str:
    return database_url.split(":", 1)[0] if ":" in database_url else "unknown"
