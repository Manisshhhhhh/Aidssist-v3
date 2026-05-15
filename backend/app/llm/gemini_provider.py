from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Any, Optional

from app.core.config import get_settings
from app.llm.base import LLMResult


class GeminiProviderError(Exception):
    """Raised when Gemini generation fails."""


class GeminiProvider:
    provider = "gemini"

    def __init__(self, api_key: str, model: Optional[str] = None, timeout_seconds: Optional[int] = None):
        try:
            from google import genai
        except Exception as exc:
            raise GeminiProviderError("google-genai is not installed.") from exc

        settings = get_settings()
        self.model = model or settings.gemini_model
        self.timeout_seconds = timeout_seconds or settings.llm_timeout_seconds
        self._genai = genai
        self._client = genai.Client(api_key=api_key)

    def generate_text(
        self,
        system_instruction: str,
        prompt: str,
        max_output_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> LLMResult:
        settings = get_settings()
        max_tokens = max_output_tokens or settings.llm_max_output_tokens
        temp = settings.llm_temperature if temperature is None else temperature

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._generate, system_instruction, prompt, max_tokens, temp)
            try:
                response = future.result(timeout=self.timeout_seconds)
            except TimeoutError as exc:
                raise GeminiProviderError("Gemini request timed out.") from exc
            except Exception as exc:
                raise GeminiProviderError(sanitize_error(str(exc))) from exc

        text = getattr(response, "text", None) or ""
        finish_reason = extract_finish_reason(response)
        return LLMResult(
            text=text.strip(),
            provider=self.provider,
            model=self.model,
            input_chars=len(system_instruction) + len(prompt),
            output_chars=len(text),
            finish_reason=finish_reason,
            raw_metadata={"finish_reason": finish_reason} if finish_reason else {},
        )

    def _generate(self, system_instruction: str, prompt: str, max_tokens: int, temperature: float):
        from google.genai import types

        return self._client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                max_output_tokens=max_tokens,
                temperature=temperature,
            ),
        )


def extract_finish_reason(response: Any) -> Optional[str]:
    try:
        candidates = getattr(response, "candidates", None) or []
        if not candidates:
            return None
        reason = getattr(candidates[0], "finish_reason", None)
        return str(reason) if reason is not None else None
    except Exception:
        return None


def sanitize_error(message: str) -> str:
    compact = " ".join(message.split())
    for marker in ["api key", "apikey", "authorization", "bearer", "token", "secret"]:
        if marker in compact.lower():
            return "Gemini request failed."
    return compact[:300] or "Gemini request failed."
