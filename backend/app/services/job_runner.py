from __future__ import annotations

from typing import Any

from app.db.models import JobRecord
from app.models.forecast_models import ForecastRequest
from app.models.report_models import ReportRequest
from app.repositories import job_repository
from app.services.audit_service import record_event
from app.services.analysis_service import analyze_dataset
from app.services.forecast_service import forecast_dataset
from app.services.report_service import generate_report


class JobRunnerError(Exception):
    """Raised when a job cannot be executed."""


def run_job(record: JobRecord) -> JobRecord:
    try:
        record_event(
            "job.started",
            "run",
            "success",
            actor_user_id=record.created_by_user_id,
            workspace_id=record.workspace_id,
            dataset_id=record.dataset_id,
            job_id=record.job_id,
            target_type="job",
            target_id=record.job_id,
            metadata={"job_type": record.job_type},
        )
        job_repository.update_progress(record.job_id, 10)
        output = execute_job(record)
        succeeded = job_repository.mark_succeeded(record.job_id, output)
        if succeeded is None:
            raise JobRunnerError("Job disappeared while marking success.")
        record_event(
            "job.succeeded",
            "run",
            "success",
            actor_user_id=succeeded.created_by_user_id,
            workspace_id=succeeded.workspace_id,
            dataset_id=succeeded.dataset_id,
            job_id=succeeded.job_id,
            target_type="job",
            target_id=succeeded.job_id,
            metadata={"job_type": succeeded.job_type},
        )
        return succeeded
    except Exception as exc:
        failed = job_repository.mark_failed(record.job_id, str(exc))
        if failed is None:
            raise
        record_event(
            "job.failed",
            "run",
            "failure",
            actor_user_id=failed.created_by_user_id,
            workspace_id=failed.workspace_id,
            dataset_id=failed.dataset_id,
            job_id=failed.job_id,
            target_type="job",
            target_id=failed.job_id,
            metadata={"job_type": failed.job_type, "reason": str(exc)},
        )
        return failed


def execute_job(record: JobRecord) -> dict[str, Any]:
    payload = job_repository.load_input(record)
    dataset_id = payload.get("dataset_id") or record.dataset_id
    if not isinstance(dataset_id, str) or not dataset_id:
        raise JobRunnerError("Job is missing dataset_id.")

    if record.job_type == "analysis":
        job_repository.update_progress(record.job_id, 35)
        analysis = analyze_dataset(dataset_id)
        job_repository.update_progress(record.job_id, 85)
        return analysis.model_dump(mode="json")

    if record.job_type == "forecast":
        request_payload = payload.get("request")
        if not isinstance(request_payload, dict):
            raise JobRunnerError("Forecast job is missing request payload.")
        job_repository.update_progress(record.job_id, 35)
        forecast = forecast_dataset(dataset_id, ForecastRequest.model_validate(request_payload))
        job_repository.update_progress(record.job_id, 85)
        return forecast.model_dump(mode="json")

    if record.job_type == "report":
        request_payload = payload.get("request")
        if not isinstance(request_payload, dict):
            raise JobRunnerError("Report job is missing request payload.")
        job_repository.update_progress(record.job_id, 35)
        report = generate_report(dataset_id, ReportRequest.model_validate(request_payload))
        job_repository.update_progress(record.job_id, 85)
        return report.model_dump(mode="json")

    raise JobRunnerError(f"Unsupported job type '{record.job_type}'.")


def run_next_job_once() -> JobRecord | None:
    record = job_repository.claim_next_queued_job()
    if record is None:
        return None
    return run_job(record)
