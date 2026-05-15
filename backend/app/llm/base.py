from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Protocol


@dataclass(frozen=True)
class LLMResult:
    text: str
    provider: str
    model: str
    input_chars: int
    output_chars: int
    finish_reason: Optional[str] = None
    raw_metadata: Optional[dict[str, Any]] = None


class LLMProvider(Protocol):
    def generate_text(
        self,
        system_instruction: str,
        prompt: str,
        max_output_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> LLMResult:
        ...
