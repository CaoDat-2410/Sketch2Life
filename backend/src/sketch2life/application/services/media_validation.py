"""Standalone P2-T1 use case; it has no HTTP, queue, database, or model dependency."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Protocol

from sketch2life.contracts.schemas.media_validation import (
    MediaValidationResultV1,
    SourceMediaReferenceV1,
    media_validation_contract,
)
from sketch2life.domain.understanding.media_quality import (
    AudioQualitySignals,
    ImageQualitySignals,
    MediaQualityPolicy,
    assess_media,
)


@dataclass(frozen=True, slots=True)
class MediaValidationRequest:
    image_path: Path
    audio_path: Path
    image_artifact_ref: str
    audio_artifact_ref: str


class MediaSignalInspector(Protocol):
    """Port for reading media at the standalone component boundary."""

    def inspect_image(self, path: Path) -> ImageQualitySignals: ...

    def inspect_audio(self, path: Path) -> AudioQualitySignals: ...


class DeterministicMediaValidator:
    def __init__(
        self, inspector: MediaSignalInspector, policy: MediaQualityPolicy | None = None
    ) -> None:
        self._inspector = inspector
        self._policy = policy or MediaQualityPolicy()

    def validate(self, request: MediaValidationRequest) -> MediaValidationResultV1:
        image = SourceMediaReferenceV1(
            artifact_ref=request.image_artifact_ref,
            sha256=_sha256_or_missing(request.image_path),
        )
        audio = SourceMediaReferenceV1(
            artifact_ref=request.audio_artifact_ref,
            sha256=_sha256_or_missing(request.audio_path),
        )
        assessment = assess_media(
            self._inspector.inspect_image(request.image_path),
            self._inspector.inspect_audio(request.audio_path),
            self._policy,
        )
        return media_validation_contract(assessment, image, audio)


def _sha256_or_missing(path: Path) -> str:
    try:
        return sha256(path.read_bytes()).hexdigest()
    except OSError:
        return sha256(f"missing:{path}".encode()).hexdigest()
