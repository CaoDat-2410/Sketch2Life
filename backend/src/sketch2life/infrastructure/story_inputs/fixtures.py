"""Deterministic analyzer and transcriber for tests and local composition (goal v3; no provider).

``FixtureSpeechTranscriber`` (T-2c) answers only for an audio SHA-256 that was registered with an
explicit text; any other audio is a recoverable ``SpeechTranscriptionFailure``, never an invented
transcript. Nothing about the audio or the text is logged.

``FixtureDrawingAnalyzer`` answers only for a derived SHA-256 that was registered with an explicit
result. An input it does not know is a recoverable failure, never an invented answer, so a test (or
a local demo) can never mistake it for a real understanding of a real drawing. A result may be
registered for one adult subject hint (a rerun after a subject edit, T-2d); a request with a hint
that has no entry falls back to the entry without a hint. No network, no Modal import, no model
weights.

``FixtureStoryGenerator`` (T-2d) answers only for the SHA-256 of an exact worker input (the same
canonical hash the repository stores as ``request_sha256``); any other input is a recoverable
``StoryGenerationFailure``, never an invented story.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from sketch2life.application.ports.parent_story_inputs import (
    ASR_UNAVAILABLE,
    DRAWING_ANALYSIS_UNAVAILABLE,
    STORY_GENERATION_UNAVAILABLE,
    DrawingAnalysisFailure,
    DrawingAnalysisRequest,
    DrawingAnalysisResult,
    SpeechTranscriptionFailure,
    SpeechTranscriptionRequest,
    SpeechTranscriptionResult,
    StoryGenerationFailure,
    StoryGenerationResult,
)


class FixtureDrawingAnalyzer:
    def __init__(self, results: Mapping[str, DrawingAnalysisResult] | None = None) -> None:
        self._results: dict[tuple[str, str | None], DrawingAnalysisResult] = {
            (derived_sha256, None): result for derived_sha256, result in (results or {}).items()
        }
        self.calls: list[DrawingAnalysisRequest] = []

    def register(
        self,
        derived_sha256: str,
        result: DrawingAnalysisResult,
        *,
        subject_hint: str | None = None,
    ) -> None:
        self._results[(derived_sha256, subject_hint)] = result

    def analyze(self, request: DrawingAnalysisRequest) -> DrawingAnalysisResult:
        self.calls.append(request)
        result = self._results.get((request.derived_sha256, request.subject_hint))
        if result is None:
            result = self._results.get((request.derived_sha256, None))
        if result is None:
            raise DrawingAnalysisFailure(DRAWING_ANALYSIS_UNAVAILABLE)
        return result


class FixtureSpeechTranscriber:
    """Maps an explicit audio SHA-256 to a text (or a result); every other audio fails."""

    def __init__(
        self, results: Mapping[str, str | SpeechTranscriptionResult] | None = None
    ) -> None:
        self._results = dict(results or {})
        self.calls: list[SpeechTranscriptionRequest] = []

    def register(self, audio_sha256: str, result: str | SpeechTranscriptionResult) -> None:
        self._results[audio_sha256] = result

    def transcribe(self, request: SpeechTranscriptionRequest) -> SpeechTranscriptionResult:
        self.calls.append(request)
        result = self._results.get(request.audio_sha256)
        if result is None:
            raise SpeechTranscriptionFailure(ASR_UNAVAILABLE)
        if isinstance(result, str):
            return SpeechTranscriptionResult(
                text=result, model_revision="fixture-1", config_hash="0" * 64
            )
        return result


def worker_input_sha256(worker_input: Mapping[str, Any]) -> str:
    """The canonical hash of a story worker input (equal to the stored ``request_sha256``)."""
    canonical = json.dumps(worker_input, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class FixtureStoryGenerator:
    """Maps the hash of an exact worker input to a story result; every other input fails."""

    def __init__(self, results: Mapping[str, StoryGenerationResult] | None = None) -> None:
        self._results = dict(results or {})
        self.calls: list[dict[str, Any]] = []

    def register(self, request_sha256: str, result: StoryGenerationResult) -> None:
        self._results[request_sha256] = result

    def generate(self, worker_input: Mapping[str, Any]) -> StoryGenerationResult:
        self.calls.append(dict(worker_input))
        result = self._results.get(worker_input_sha256(worker_input))
        if result is None:
            raise StoryGenerationFailure(STORY_GENERATION_UNAVAILABLE)
        return result


__all__ = [
    "FixtureDrawingAnalyzer",
    "FixtureSpeechTranscriber",
    "FixtureStoryGenerator",
    "worker_input_sha256",
]
