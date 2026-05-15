from __future__ import annotations

from app.core.config import get_settings
from app.llm.base import LLMProvider
from app.llm.gemini_provider import GeminiProvider


class LLMDisabledError(Exception):
    """Raised when LLM features are disabled."""


class LLMConfigurationError(Exception):
    """Raised when an enabled provider is not configured."""


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if not settings.llm_enabled:
        raise LLMDisabledError("LLM features are disabled.")
    if settings.llm_provider != "gemini":
        raise LLMConfigurationError(f"Unsupported LLM provider '{settings.llm_provider}'.")
    if not settings.gemini_api_key:
        raise LLMConfigurationError("Gemini API key is not configured.")
    return GeminiProvider(api_key=settings.gemini_api_key, model=settings.gemini_model)
