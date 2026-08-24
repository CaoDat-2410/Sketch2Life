"""Provider-neutral AI inference boundary owned by the application layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class AiInferenceRequest:
    """A reference-only request; raw media is resolved by trusted infrastructure."""

    request_id: str
    operation: str
    input_artifact_ids: tuple[str, ...]
    expected_session_version: int
    model_profile: str


@dataclass(frozen=True, slots=True)
class AiInferenceResult:
    """Untrusted provider output metadata awaiting contract validation."""

    request_id: str
    output_artifact_ids: tuple[str, ...]
    provider_trace_id: str
    model_profile: str


class AiGateway(Protocol):
    """Implemented only by infrastructure behind the private network boundary."""

    async def infer(self, request: AiInferenceRequest) -> AiInferenceResult:
        """Submit one idempotent inference request and return artifact references."""
        ...
