"""Provider-shaped Whisper adapter without a hard dependency on a model SDK.

The injected engine is the only place that may know faster-whisper. This module
maps its typed boundary output into the public contract and never returns SDK
objects or raw provider payloads.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sketch2life.contracts.schemas.understanding import (
    AdapterFailureV1,
    AsrQualityV1,
    AsrRequestV1,
    AsrResultV1,
    AsrSegmentV1,
    ModelProvenanceV1,
)


@dataclass(frozen=True, slots=True)
class WhisperSegment:
    start_seconds: float
    end_seconds: float
    text: str
    confidence: float | None = None


@dataclass(frozen=True, slots=True)
class WhisperEngineResult:
    transcript: str
    language: str | None
    language_confidence: float | None
    segments: tuple[WhisperSegment, ...]
    no_speech_probability: float | None = None
    average_log_probability: float | None = None


class WhisperEngine(Protocol):
    def transcribe(self, source_audio: object) -> object: ...


@dataclass(frozen=True, slots=True)
class WhisperAsrAdapter:
    engine: WhisperEngine
    provenance: ModelProvenanceV1
    max_retries: int = 1

    def transcribe(self, request: AsrRequestV1) -> AsrResultV1:
        attempts = min(max(self.max_retries, 0), 1) + 1
        for attempt in range(attempts):
            try:
                raw = self.engine.transcribe(request.source_audio)
                return _map_engine_result(raw, request, self.provenance)
            except TimeoutError:
                return _failed(request, self.provenance, "TIMEOUT", "ASR provider timed out", True)
            except Exception:
                if attempt + 1 < attempts:
                    continue
                return _failed(
                    request,
                    self.provenance,
                    "PROVIDER_ERROR",
                    "ASR provider request failed",
                    True,
                )
        return _failed(
            request, self.provenance, "PROVIDER_ERROR", "ASR provider request failed", True
        )


def _map_engine_result(
    raw: object, request: AsrRequestV1, provenance: ModelProvenanceV1
) -> AsrResultV1:
    if not isinstance(raw, WhisperEngineResult):
        return _failed(
            request, provenance, "MALFORMED_OUTPUT", "ASR output shape is invalid", False
        )
    try:
        segments = tuple(
            AsrSegmentV1(
                start_seconds=segment.start_seconds,
                end_seconds=segment.end_seconds,
                text=segment.text,
                confidence=segment.confidence,
            )
            for segment in raw.segments
        )
        return AsrResultV1(
            status="SUCCEEDED",
            source_audio=request.source_audio,
            transcript=raw.transcript,
            language=raw.language,
            language_confidence=raw.language_confidence,
            segments=segments,
            quality=AsrQualityV1(
                no_speech_probability=raw.no_speech_probability,
                average_log_probability=raw.average_log_probability,
                segment_count=len(segments),
            ),
            provenance=provenance,
        )
    except (TypeError, ValueError):
        return _failed(
            request,
            provenance,
            "MALFORMED_OUTPUT",
            "ASR output failed schema validation",
            False,
        )


def _failed(
    request: AsrRequestV1,
    provenance: ModelProvenanceV1,
    code: str,
    message: str,
    retryable: bool,
) -> AsrResultV1:
    return AsrResultV1(
        status="FAILED",
        source_audio=request.source_audio,
        provenance=provenance,
        failure=AdapterFailureV1(code=code, message=message, retryable=retryable),  # type: ignore[arg-type]
    )
