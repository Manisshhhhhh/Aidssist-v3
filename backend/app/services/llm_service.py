from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import Request

from app.core.config import get_settings
from app.db.models import User
from app.llm.factory import LLMConfigurationError, LLMDisabledError, get_llm_provider
from app.llm.gemini_provider import GeminiProviderError
from app.models.llm_models import AiSummaryGrounding, AiSummaryRequest, AiSummaryResponse
from app.repositories.dataset_repository import get_dataset_record
from app.services import artifact_service, storage_service
from app.services.analysis_service import load_analysis
from app.services.audit_service import record_event
from app.services.llm_prompt_service import SYSTEM_INSTRUCTION, build_ai_summary_prompt


class AiSummaryDatasetNotFoundError(Exception):
    """Raised when a dataset does not exist."""


class AiSummaryValidationError(Exception):
    """Raised when summary preconditions are not met."""


class AiSummaryUnavailableError(Exception):
    """Raised when LLM features are disabled or unavailable."""


class AiSummaryProviderError(Exception):
    """Raised when the LLM provider fails."""


def create_ai_summary(
    dataset_id: str,
    request_payload: AiSummaryRequest,
    current_user: Optional[User] = None,
    request: Optional[Request] = None,
) -> AiSummaryResponse:
    metadata = storage_service.load_metadata(dataset_id)
    if metadata is None:
        raise AiSummaryDatasetNotFoundError(f"Dataset '{dataset_id}' was not found.")
    analysis = load_analysis(dataset_id)
    if analysis is None:
        raise AiSummaryValidationError("Run analysis before generating an AI summary.")

    dataset_record = get_dataset_record(dataset_id)
    workspace_id = dataset_record.workspace_id if dataset_record else None
    actor_id = current_user.id if current_user else None
    record_event(
        "llm.summary.requested",
        "generate",
        "success",
        actor_user_id=actor_id,
        workspace_id=workspace_id,
        dataset_id=dataset_id,
        metadata={"provider": get_settings().llm_provider, "model": get_settings().gemini_model},
        request=request,
    )

    try:
        provider = get_llm_provider()
    except LLMDisabledError as exc:
        record_event(
            "llm.summary.failed",
            "generate",
            "failure",
            actor_user_id=actor_id,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            metadata={"reason": "disabled"},
            request=request,
        )
        raise AiSummaryUnavailableError(str(exc)) from exc
    except LLMConfigurationError as exc:
        record_event(
            "llm.summary.failed",
            "generate",
            "failure",
            actor_user_id=actor_id,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            metadata={"reason": "configuration"},
            request=request,
        )
        raise AiSummaryUnavailableError(str(exc)) from exc

    prompt, grounding_flags = build_ai_summary_prompt(metadata, analysis, request_payload)
    try:
        result = provider.generate_text(
            system_instruction=SYSTEM_INSTRUCTION,
            prompt=prompt,
            max_output_tokens=get_settings().llm_max_output_tokens,
            temperature=get_settings().llm_temperature,
        )
    except GeminiProviderError as exc:
        record_event(
            "llm.summary.failed",
            "generate",
            "failure",
            actor_user_id=actor_id,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            metadata={"provider": get_settings().llm_provider, "model": get_settings().gemini_model, "reason": str(exc)},
            request=request,
        )
        raise AiSummaryProviderError("Gemini summary generation failed.") from exc

    if not result.text:
        record_event(
            "llm.summary.failed",
            "generate",
            "failure",
            actor_user_id=actor_id,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            metadata={"provider": result.provider, "model": result.model, "reason": "empty_response"},
            request=request,
        )
        raise AiSummaryProviderError("Gemini returned an empty summary.")

    created_at = datetime.now(timezone.utc)
    summary = AiSummaryResponse(
        dataset_id=dataset_id,
        summary_id=str(uuid4()),
        provider=result.provider,
        model=result.model,
        summary=result.text,
        grounding=AiSummaryGrounding(
            used_analysis=grounding_flags["used_analysis"],
            used_forecast=grounding_flags["used_forecast"],
            used_charts=grounding_flags["used_charts"],
            raw_rows_sent=False,
        ),
        warnings=[
            "This summary is generated from deterministic analysis outputs, not raw-data reasoning.",
            "Treat LLM wording as explanatory assistance; deterministic Aidssist metrics remain the source of truth.",
        ],
        created_at=created_at,
    )
    save_summary_artifact(summary, prompt, result.input_chars, result.output_chars)
    record_event(
        "llm.summary.succeeded",
        "generate",
        "success",
        actor_user_id=actor_id,
        workspace_id=workspace_id,
        dataset_id=dataset_id,
        target_type="ai_summary",
        target_id=summary.summary_id,
        metadata={
            "provider": result.provider,
            "model": result.model,
            "input_chars": result.input_chars,
            "output_chars": result.output_chars,
            "prompt_hash": prompt_hash(prompt),
        },
        request=request,
    )
    return summary


def save_summary_artifact(summary: AiSummaryResponse, prompt: str, input_chars: int, output_chars: int) -> None:
    storage_key = storage_service.dataset_key(summary.dataset_id, f"ai_summaries/{summary.summary_id}.json")
    stored = storage_service.get_provider().save_text(
        storage_key,
        json.dumps(summary.model_dump(mode="json"), indent=2, ensure_ascii=False),
        "application/json",
    )
    artifact_service.record_artifact(
        artifact_type="ai_summary_json",
        stored=stored,
        filename=f"ai_summary_{summary.summary_id}.json",
        dataset_id=summary.dataset_id,
        metadata={
            "summary_id": summary.summary_id,
            "provider": summary.provider,
            "model": summary.model,
            "prompt_hash": prompt_hash(prompt),
            "input_chars": input_chars,
            "output_chars": output_chars,
        },
    )


def latest_ai_summary(dataset_id: str) -> Optional[dict]:
    from app.repositories.artifact_repository import latest_dataset_artifact

    artifact = latest_dataset_artifact(dataset_id, "ai_summary_json")
    if artifact is None:
        return None
    provider = storage_service.get_provider()
    if not provider.exists(artifact.storage_key):
        return None
    try:
        return json.loads(provider.read_text(artifact.storage_key))
    except json.JSONDecodeError:
        return None


def prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()
