"""Standalone P2-T1 use case; it has no HTTP, queue, database, or model dependency."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Literal, Protocol

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

_HASH_CHUNK_BYTES = 1024 * 1024


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
        image = _source_reference(request.image_path, request.image_artifact_ref)
        audio = _source_reference(request.audio_path, request.audio_artifact_ref)
        assessment = assess_media(
            self._inspector.inspect_image(request.image_path),
            self._inspector.inspect_audio(request.audio_path),
            self._policy,
        )
        return media_validation_contract(assessment, image, audio)


def _source_reference(path: Path, artifact_ref: str) -> SourceMediaReferenceV1:
    try:
        digest = _file_digest(path)
    except OSError:
        status: Literal["MISSING", "UNREADABLE"] = (
            "MISSING" if not path.exists() else "UNREADABLE"
        )
        return SourceMediaReferenceV1(
            artifact_ref=artifact_ref,
            sha256=None,
            source_status=status,
        )
    return SourceMediaReferenceV1(
        artifact_ref=artifact_ref,
        sha256=digest,
        source_status="AVAILABLE",
    )


def _file_digest(path: Path) -> str:
    """Hash the complete source without holding it in memory."""

    digest = sha256()
    with path.open("rb") as source:
        while chunk := source.read(_HASH_CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()
