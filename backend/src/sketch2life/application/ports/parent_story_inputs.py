"""Ports for the Parent StoryRun input step: drawing analysis and speech transcription.

SRS l.394 puts the visual-understanding work after the 202 response (``INPUT_PROCESSING`` until a
result or a recoverable failure) and OD-13 owns the real worker. Until a worker is composed the
application holds no analyzer (``app.state.drawing_analyzer is None``) and the run waits. The
shape here is deliberately small: the analyzer receives hashes and sizes of the normalized drawing
and answers with a closed result, so no provider type or Modal import leaks into the application.

T-2c adds the same shape for the voice idea: ``SpeechTranscriberPort`` receives the hash and the
duration of the stored audio and answers with text. ``app.state.speech_transcriber`` is ``None``
by default and the transcript then stays ``PENDING`` (the run waits and can be cancelled). The
transcript text is untrusted: it reaches the story worker only after the adult confirmed that
exact revision (TD-04, l.1713).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Final, Protocol

MULTI_CHILD_NOT_SUPPORTED: Final = "MULTI_CHILD_NOT_SUPPORTED"  # SRS l.871
DRAWING_ANALYSIS_FAILED: Final = "DRAWING_ANALYSIS_FAILED"
DRAWING_ANALYSIS_UNAVAILABLE: Final = "DRAWING_ANALYSIS_UNAVAILABLE"
MAX_VISIBLE_FEATURES: Final = 4


class DrawingAnalysisFailure(RuntimeError):
    """The analyzer could not answer, and a retake or a later retry can fix it (recoverable)."""

    def __init__(self, code: str = DRAWING_ANALYSIS_UNAVAILABLE) -> None:
        self.code = code
        super().__init__(code)


class DrawingAnalysisOutcomeUnknown(RuntimeError):
    """The analyzer may have run but its outcome is unknown (reconciliation, never a retake)."""


@dataclass(frozen=True, slots=True)
class DrawingAnalysisRequest:
    """What an analyzer may see: the normalized drawing of one input revision of one run."""

    run_id: str
    input_revision: int
    derived_asset_ref: str
    derived_sha256: str
    derived_size_bytes: int
    # T-2d: set only on a rerun after the adult edited the subject (SRS l.394, l.1413): the
    # adult's text, at most 160 characters, untrusted data for the analyzer, never an instruction.
    subject_hint: str | None = None


@dataclass(frozen=True, slots=True)
class DrawingAnalysisResult:
    """Closed analyzer answer; ``child_count > 1`` is reported as MULTI_CHILD_NOT_SUPPORTED."""

    subject: str
    visible_features: tuple[str, ...]
    confidence: float
    child_count: int = 1
    topic_compatible: bool | None = None


class DrawingAnalyzerPort(Protocol):
    def analyze(self, request: DrawingAnalysisRequest) -> DrawingAnalysisResult:
        """Answer for the request, or raise ``DrawingAnalysisFailure`` / ``...OutcomeUnknown``."""
        ...


ASR_FAILED: Final = "ASR_FAILED"
ASR_UNAVAILABLE: Final = "ASR_UNAVAILABLE"
TRANSCRIPT_EMPTY: Final = "TRANSCRIPT_EMPTY"
TRANSCRIPT_TOO_LONG: Final = "TRANSCRIPT_TOO_LONG"
MAX_RAW_TRANSCRIPT_CHARS: Final = 20_000
MAX_TRANSCRIPT_TEXT: Final = 500  # the typed idea and the confirmed transcript share this bound
MAX_SEGMENT_TIMING_ITEMS: Final = 500


class SpeechTranscriptionFailure(RuntimeError):
    """The transcriber could not answer; the adult types the idea instead (recoverable)."""

    def __init__(self, code: str = ASR_UNAVAILABLE) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class SpeechTranscriptionRequest:
    """What a transcriber may see: the stored audio of one transcript revision, by hash."""

    run_id: str
    transcript_revision_id: str
    audio_asset_ref: str
    audio_sha256: str
    media_type: str
    # A header claim, not a fact: an MP4 duration comes from the client-controlled ``mvhd``
    # box. The real adapter (OD-13) must re-measure at decode and answer ``FAILED/ASR_*``
    # (or reject) when the decoded audio is longer than the 2-minute rule (l.982, l.1413).
    duration_ms: int


@dataclass(frozen=True, slots=True)
class SpeechTranscriptionResult:
    text: str
    language: str = "vi"
    model_revision: str = "unspecified"
    config_hash: str | None = None
    asr_profile_ref: str | None = None
    # Optional ``{"start_ms", "end_ms"}`` items; dropped when malformed or over the bound.
    segment_timing: tuple[dict[str, int], ...] | None = None


class SpeechTranscriberPort(Protocol):
    def transcribe(self, request: SpeechTranscriptionRequest) -> SpeechTranscriptionResult:
        """Answer for the request, or raise ``SpeechTranscriptionFailure``."""
        ...


STORY_GENERATION_FAILED: Final = "STORY_GENERATION_FAILED"
STORY_GENERATION_UNAVAILABLE: Final = "STORY_GENERATION_UNAVAILABLE"


class StoryGenerationFailure(RuntimeError):
    """The generator could not answer; the run fails and the outcome is known (T-2d)."""

    def __init__(self, code: str = STORY_GENERATION_UNAVAILABLE) -> None:
        self.code = code
        super().__init__(code)


class StoryGenerationOutcomeUnknown(RuntimeError):
    """The generator may have run but its outcome is unknown (reconciliation, never a retry)."""


@dataclass(frozen=True, slots=True)
class StoryGenerationResult:
    """The raw story draft (validated by ``story_output``) and the provenance to store."""

    story: Mapping[str, Any]
    call_id: str
    model_id: str
    model_revision: str


class StoryGeneratorPort(Protocol):
    def generate(self, worker_input: Mapping[str, Any]) -> StoryGenerationResult:
        """Answer for the worker input, or raise ``StoryGenerationFailure`` / ``...Unknown``.

        The worker input keeps the adult's rewrite hint in its own field
        (``adult_rewrite_hint``); the instruction is a server constant (FR-AI-12, BR-36).
        """
        ...


@dataclass(frozen=True, slots=True)
class SubjectConfirmOutcome:
    """The committed result of one subject confirmation; also the stored body of its receipt.

    ``decision`` is ``CONFIRMED`` (the subject was accepted as the revision named) or
    ``RERUN_REQUESTED`` (the adult edited the subject and the VLM runs again, SRS l.394).
    ``input_revision`` is set only on a fresh rerun: the input the runner starts for.
    """

    understanding_revision: int
    decision: str
    run_revision: int
    input_revision: int | None = None
    replayed: bool = False


@dataclass(frozen=True, slots=True)
class VoiceInput:
    """The completed, clean ``RUN_AUDIO`` upload that ``/idea`` attaches to the run."""

    asset_key: str
    sha256: str
    media_type: str
    size_bytes: int
    duration_ms: int


@dataclass(frozen=True, slots=True)
class IdeaOutcome:
    """The committed result of one ``/idea`` command; also the stored body of its receipt."""

    input_revision: int
    run_revision: int
    run_state: str
    idea_source: str | None
    transcript_revision: int | None
    transcript_state: str | None
    # Set only on a fresh audio submission: the PENDING row the runner completes. Not stored.
    new_transcript_id: str | None = None
    replayed: bool = False

    def as_body(self) -> dict[str, object]:
        return {
            "input_revision": self.input_revision,
            "run_revision": self.run_revision,
            "run_state": self.run_state,
            "idea_source": self.idea_source,
            "transcript_revision": self.transcript_revision,
            "transcript_state": self.transcript_state,
        }


@dataclass(frozen=True, slots=True)
class TranscriptView:
    """The adult's read of the current transcript (``GET .../transcript``)."""

    run_revision: int
    state: str  # NONE, PENDING, NEEDS_CONFIRMATION, CONFIRMED or FAILED
    transcript_revision: int | None = None
    origin: str | None = None
    text: str | None = None
    transcript_sha256: str | None = None
    language: str | None = None
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class TranscriptConfirmOutcome:
    transcript_revision: int
    run_revision: int
    run_state: str
    replayed: bool = False

    def as_body(self) -> dict[str, object]:
        return {
            "transcript_revision": self.transcript_revision,
            "run_revision": self.run_revision,
            "run_state": self.run_state,
        }


@dataclass(frozen=True, slots=True)
class DrawingAttachOutcome:
    """The committed result of one attach; also the stored body of its idempotency receipt."""

    input_revision: int
    run_revision: int
    run_state: str
    analysis_state: str
    replayed: bool = False

    def as_body(self) -> dict[str, object]:
        return {
            "input_revision": self.input_revision,
            "run_revision": self.run_revision,
            "run_state": self.run_state,
            "analysis_state": self.analysis_state,
        }


__all__ = [
    "ASR_FAILED",
    "ASR_UNAVAILABLE",
    "DRAWING_ANALYSIS_FAILED",
    "DRAWING_ANALYSIS_UNAVAILABLE",
    "MAX_RAW_TRANSCRIPT_CHARS",
    "MAX_SEGMENT_TIMING_ITEMS",
    "MAX_TRANSCRIPT_TEXT",
    "MAX_VISIBLE_FEATURES",
    "MULTI_CHILD_NOT_SUPPORTED",
    "TRANSCRIPT_EMPTY",
    "TRANSCRIPT_TOO_LONG",
    "DrawingAnalysisFailure",
    "DrawingAnalysisOutcomeUnknown",
    "DrawingAnalysisRequest",
    "DrawingAnalysisResult",
    "DrawingAnalyzerPort",
    "DrawingAttachOutcome",
    "IdeaOutcome",
    "STORY_GENERATION_FAILED",
    "STORY_GENERATION_UNAVAILABLE",
    "SpeechTranscriberPort",
    "SpeechTranscriptionFailure",
    "SpeechTranscriptionRequest",
    "SpeechTranscriptionResult",
    "StoryGenerationFailure",
    "StoryGenerationOutcomeUnknown",
    "StoryGenerationResult",
    "StoryGeneratorPort",
    "SubjectConfirmOutcome",
    "TranscriptConfirmOutcome",
    "TranscriptView",
    "VoiceInput",
]
