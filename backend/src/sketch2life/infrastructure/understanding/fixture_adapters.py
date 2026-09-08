"""Deterministic fixture adapters used by tests and local contract development."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from sketch2life.contracts.schemas.understanding import (
    AdapterFailureV1,
    AsrRequestV1,
    AsrResultV1,
    ModelProvenanceV1,
    VisionRequestV1,
    VisionUnderstandingResultV1,
)

_FIXTURE_PROVENANCE = ModelProvenanceV1(
    provider="fixture",
    model="fixture-understanding-v1",
    adapter_version="1.0",
    config_version="fixture-config-v1",
)


def _missing_fixture_failure(kind: str) -> AdapterFailureV1:
    return AdapterFailureV1(
        code="PROVIDER_ERROR",
        message=f"No deterministic {kind} fixture is registered",
        retryable=False,
    )


@dataclass(frozen=True, slots=True)
class FixtureAsrAdapter:
    fixtures: Mapping[str, AsrResultV1]

    def __post_init__(self) -> None:
        object.__setattr__(self, "fixtures", MappingProxyType(dict(self.fixtures)))

    def transcribe(self, request: AsrRequestV1) -> AsrResultV1:
        result = self.fixtures.get(request.source_audio.artifact_ref)
        if result is None:
            return AsrResultV1(
                status="FAILED",
                source_audio=request.source_audio,
                provenance=_FIXTURE_PROVENANCE,
                failure=_missing_fixture_failure("ASR"),
            )
        if result.source_audio != request.source_audio:
            return result.model_copy(
                update={
                    "status": "FAILED",
                    "source_audio": request.source_audio,
                    "transcript": None,
                    "language": None,
                    "language_confidence": None,
                    "segments": (),
                    "quality": None,
                    "failure": AdapterFailureV1(
                        code="SOURCE_MISMATCH",
                        message="Fixture source reference does not match request",
                        retryable=False,
                    ),
                }
            )
        return result


@dataclass(frozen=True, slots=True)
class FixtureVisionAdapter:
    fixtures: Mapping[str, VisionUnderstandingResultV1]

    def __post_init__(self) -> None:
        object.__setattr__(self, "fixtures", MappingProxyType(dict(self.fixtures)))

    def understand(self, request: VisionRequestV1) -> VisionUnderstandingResultV1:
        result = self.fixtures.get(request.source_image.artifact_ref)
        if result is None:
            return VisionUnderstandingResultV1(
                status="FAILED",
                source_image=request.source_image,
                uncertainty=1,
                provenance=_FIXTURE_PROVENANCE,
                failure=_missing_fixture_failure("vision"),
            )
        if result.source_image != request.source_image:
            return result.model_copy(
                update={
                    "status": "FAILED",
                    "source_image": request.source_image,
                    "entities": (),
                    "actions": (),
                    "relations": (),
                    "themes": (),
                    "ambiguous_regions": (),
                    "uncertainty": 1,
                    "failure": AdapterFailureV1(
                        code="SOURCE_MISMATCH",
                        message="Fixture source reference does not match request",
                        retryable=False,
                    ),
                }
            )
        return result
