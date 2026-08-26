"""Strict structured-output adapter for a future Qwen3-VL client."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from sketch2life.contracts.schemas.understanding import (
    AdapterFailureV1,
    ModelProvenanceV1,
    VisionCandidateV1,
    VisionRegionV1,
    VisionRelationV1,
    VisionRequestV1,
    VisionUnderstandingResultV1,
)


class VisionModelClient(Protocol):
    def understand(self, source_image: object, response_schema_version: str) -> object: ...


class _VisionProviderPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entities: tuple[VisionCandidateV1, ...] = ()
    actions: tuple[VisionCandidateV1, ...] = ()
    relations: tuple[VisionRelationV1, ...] = ()
    themes: tuple[VisionCandidateV1, ...] = ()
    ambiguous_regions: tuple[VisionRegionV1, ...] = ()
    uncertainty: float = Field(ge=0, le=1)


_PROHIBITED_KEYS = {
    "personality",
    "diagnosis",
    "mental_state",
    "psychological_profile",
    "psychological_inference",
    "emotion_inference",
}


@dataclass(frozen=True, slots=True)
class Qwen3VLStructuredAdapter:
    client: VisionModelClient
    provenance: ModelProvenanceV1
    max_retries: int = 1

    def understand(self, request: VisionRequestV1) -> VisionUnderstandingResultV1:
        attempts = min(max(self.max_retries, 0), 1) + 1
        for attempt in range(attempts):
            try:
                raw = self.client.understand(
                    request.source_image,
                    request.response_schema_version,
                )
                return _map_provider_payload(raw, request, self.provenance)
            except TimeoutError:
                return _failed(
                    request, self.provenance, "TIMEOUT", "Vision provider timed out", True
                )
            except Exception:
                if attempt + 1 < attempts:
                    continue
                return _failed(
                    request,
                    self.provenance,
                    "PROVIDER_ERROR",
                    "Vision provider request failed",
                    True,
                )
        return _failed(
            request, self.provenance, "PROVIDER_ERROR", "Vision provider request failed", True
        )


def _map_provider_payload(
    raw: object, request: VisionRequestV1, provenance: ModelProvenanceV1
) -> VisionUnderstandingResultV1:
    if not isinstance(raw, Mapping):
        return _failed(
            request,
            provenance,
            "MALFORMED_OUTPUT",
            "Vision output is not structured JSON",
            False,
        )
    if _contains_prohibited_key(raw):
        return _failed(
            request,
            provenance,
            "PROHIBITED_FIELD",
            "Vision output contains a prohibited inference field",
            False,
        )
    try:
        payload = _VisionProviderPayload.model_validate(raw)
    except ValidationError:
        return _failed(
            request,
            provenance,
            "MALFORMED_OUTPUT",
            "Vision output failed schema validation",
            False,
        )
    return VisionUnderstandingResultV1(
        status="SUCCEEDED",
        source_image=request.source_image,
        entities=payload.entities,
        actions=payload.actions,
        relations=payload.relations,
        themes=payload.themes,
        ambiguous_regions=payload.ambiguous_regions,
        uncertainty=payload.uncertainty,
        provenance=provenance,
    )


def _contains_prohibited_key(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(
            str(key).lower() in _PROHIBITED_KEYS or _contains_prohibited_key(item)
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple)):
        return any(_contains_prohibited_key(item) for item in value)
    return False


def _failed(
    request: VisionRequestV1,
    provenance: ModelProvenanceV1,
    code: str,
    message: str,
    retryable: bool,
) -> VisionUnderstandingResultV1:
    return VisionUnderstandingResultV1(
        status="FAILED",
        source_image=request.source_image,
        uncertainty=1,
        provenance=provenance,
        failure=AdapterFailureV1(code=code, message=message, retryable=retryable),  # type: ignore[arg-type]
    )
