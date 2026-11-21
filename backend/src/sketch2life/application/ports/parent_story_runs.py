"""Application-owned persistence contract for authenticated Parent StoryRuns."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.object_storage import ObjectStoragePort
from sketch2life.application.ports.parent_story_inputs import (
    DrawingAttachOutcome,
    IdeaOutcome,
    SpeechTranscriptionRequest,
    SubjectConfirmOutcome,
    TranscriptConfirmOutcome,
    TranscriptView,
    VoiceInput,
)
from sketch2life.application.ports.parent_story_profile_lookup import ParentStoryProfileReference


class ParentStoryRunError(RuntimeError):
    def __init__(
        self,
        status_code: int,
        code: str,
        *,
        current_version: int | None = None,
        field_errors: list[dict[str, str]] | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.current_version = current_version
        # Plain ``[{field, code}]`` items for a 400 ``INVALID_REQUEST`` (T-2c); never free text.
        self.field_errors = field_errors
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class ParentStoryRunRecord:
    run_id: str
    run_state: str
    run_revision: int
    parent_profile_id: UUID
    profile_revision_ref: UUID
    context_revision: int
    context_confirmed: bool
    context_snapshot: dict[str, Any]
    context_snapshot_sha256: str
    current_input_revision: int | None
    understanding_revision: int | None
    subject_label: str | None
    candidate: dict[str, Any] | None
    story_revision_id: str | None
    story_revision_no: int | None
    story_status: str | None
    story_sha256: str | None
    story_content: dict[str, Any] | None
    job_state: str | None
    retryable: bool
    error_code: str | None
    created_at: datetime
    updated_at: datetime
    lesson_pin_snapshot: dict[str, Any] | None = None
    # T-1c (StoryRunDetailV1, SRS l.1811): the names equal the response model fields, which is how
    # the seed tests rebuild the model from every dataclass field. ``video`` is None until a video
    # request was accepted or is waiting; ``timeline`` is derived from existing timestamps.
    video: dict[str, Any] | None = None
    timeline: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ParentStoryLifecycleRecord:
    """FR-C-08 content-free projection of a run in DELETE_PENDING or DELETED (DTR §6.5).

    It is read before any input or profile access, so it carries no profile, context, story,
    candidate, subject or asset field: a purged run has none of them to report.
    """

    run_id: str
    run_state: str
    revision: int
    version: int
    lifecycle_request_ref: str
    purge_state: str

    def as_body(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "run_state": self.run_state,
            "revision": self.revision,
            "version": self.version,
            "lifecycle_request_ref": self.lifecycle_request_ref,
            "purge_state": self.purge_state,
        }

    @classmethod
    def from_body(cls, body: dict[str, Any]) -> ParentStoryLifecycleRecord:
        return cls(
            run_id=str(body["run_id"]),
            run_state=str(body["run_state"]),
            revision=int(body["revision"]),
            version=int(body["version"]),
            lifecycle_request_ref=str(body["lifecycle_request_ref"]),
            purge_state=str(body["purge_state"]),
        )


# A live run is reported in full; from DELETE_PENDING on only the projection is reported.
ParentStoryRunView = ParentStoryRunRecord | ParentStoryLifecycleRecord


@dataclass(frozen=True, slots=True)
class ParentStoryInputRecord:
    run_input_id: str
    input_revision: int
    original_asset_ref: str | None
    original_sha256: str | None
    original_media_type: str | None
    original_size_bytes: int | None
    derived_asset_ref: str | None
    derived_sha256: str | None
    derived_size_bytes: int | None
    source_profile_revision_ref: UUID
    context_revision: int
    context_snapshot: dict[str, Any]
    context_snapshot_sha256: str
    context_confirmed_by: str | None
    context_confirmed_at: datetime | None


@dataclass(frozen=True, slots=True)
class ParentStoryRevisionReservation:
    run_id: str
    story_revision_id: str
    revision_no: int
    understanding_revision: int
    context_revision: int
    source_asset_sha256: str
    worker_input: dict[str, Any]
    request_sha256: str
    # ``None`` for the rewrite route (T-2d): its receipt is FINAL at reservation, so completing or
    # failing the generation touches no receipt.
    receipt_id: str | None
    replayed: bool = False
    replay_body: dict[str, Any] | None = None
    # FR-C-08: set only on the replay of a purged run; the route returns the projection.
    lifecycle: ParentStoryLifecycleRecord | None = None


@dataclass(frozen=True, slots=True)
class StoryRewriteOutcome:
    """The committed result of one ``story-rewrites`` command; also the stored receipt body.

    ``reservation`` is set only on a fresh command (the runner needs the worker input, which is
    never stored); ``lifecycle`` only on the replay of a purged run.
    """

    story_revision_no: int
    run_revision: int
    run_state: str
    replayed: bool = False
    reservation: ParentStoryRevisionReservation | None = None
    lifecycle: ParentStoryLifecycleRecord | None = None


@dataclass(frozen=True, slots=True)
class ParentStoryRunSummary:
    """FEAT-081 C3b: content-free history item (no story, context, topic, media or provider)."""

    run_id: str
    parent_profile_id: UUID | None
    run_state: str
    revision: int
    deleting: bool
    can_cancel: bool
    can_delete: bool
    created_at: datetime
    updated_at: datetime


class ParentStoryRunRepositoryPort(Protocol):
    def list_runs(
        self,
        *,
        principal: VerifiedPrincipal,
        profile_id: UUID | None,
        limit: int,
        after: tuple[datetime, str] | None,
    ) -> list[ParentStoryRunSummary]:
        """Owner-scoped runs, newest first; returns up to ``limit + 1`` rows."""
        ...

    def replay_create_run(
        self,
        *,
        principal: VerifiedPrincipal,
        account_id: str,
        parent_profile_id: UUID,
        idempotency_key: str,
        topic: str,
        adult_confirmed_idea: str,
        lesson_version_ref: dict[str, str] | None = None,
    ) -> ParentStoryRunView | None: ...

    def create_run(
        self,
        *,
        principal: VerifiedPrincipal,
        account_id: str,
        profile: ParentStoryProfileReference,
        idempotency_key: str,
        run_id: str,
        topic: str,
        adult_confirmed_idea: str,
        lesson_version_ref: dict[str, str] | None = None,
        lesson_pin_snapshot: dict[str, Any] | None = None,
    ) -> ParentStoryRunView: ...

    def get_run(self, *, principal: VerifiedPrincipal, run_id: str) -> ParentStoryRunView: ...

    def get_active_run(
        self, *, principal: VerifiedPrincipal, account_id: str
    ) -> ParentStoryRunView | None: ...

    def cancel_run(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_revision: int,
        idempotency_key: str,
    ) -> ParentStoryLifecycleRecord:
        """FR-C-08 cancel (DTR §6.1): the stored projection body, as accepted or replayed."""
        ...

    def delete_run(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        idempotency_key: str,
    ) -> ParentStoryLifecycleRecord:
        """FR-C-08 delete of a finished run (DTR §6.1); no expected revision."""
        ...

    def ensure_accepting_artwork(self, *, principal: VerifiedPrincipal, run_id: str) -> None:
        """State re-check immediately before the artwork route's first ``put_object``."""
        ...

    def confirm_context(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_context_revision: int,
        expected_context_snapshot_sha256: str,
        idempotency_key: str,
    ) -> ParentStoryRunView: ...

    def attach_artwork(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        original_asset_ref: str,
        original_sha256: str,
        original_media_type: str,
        original_size_bytes: int,
        derived_asset_ref: str,
        derived_sha256: str,
        derived_size_bytes: int,
        scanner_name: str,
        scanner_version: str,
    ) -> ParentStoryInputRecord: ...

    def read_current_input(
        self, *, principal: VerifiedPrincipal, run_id: str
    ) -> ParentStoryInputRecord: ...

    def record_understanding(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        result_snapshot: dict[str, Any],
        candidate_subject: str,
        confidence: float,
        expected_input_revision: int | None = None,
    ) -> int: ...

    def confirm_subject(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_understanding_revision: int,
        confirmed_subject: str,
        idempotency_key: str,
        rerun_on_edit: bool = False,
    ) -> SubjectConfirmOutcome | ParentStoryLifecycleRecord: ...

    def read_subject_rerun_hint(self, *, principal: VerifiedPrincipal, run_id: str) -> str | None:
        """The adult's edited subject while its VLM rerun is pending, else ``None`` (T-2d)."""
        ...

    def reserve_story_revision(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_understanding_revision: int,
        rewrite_instruction: str | None,
        idempotency_key: str,
        story_revision_id: str,
        model_id: str,
        model_revision: str,
        prompt_version: str,
    ) -> ParentStoryRevisionReservation: ...

    def reserve_story_rewrite(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        idempotency_key: str,
        expected_story_revision: int,
        expected_story_sha256: str | None,
        hint: str | None,
        story_revision_id: str,
        model_id: str,
        model_revision: str,
        prompt_version: str,
        instruction_version: str,
        instruction: str,
    ) -> StoryRewriteOutcome:
        """T-2d: accept one rewrite; the receipt is FINAL 202 in the same transaction."""
        ...

    def start_story_generation(
        self, *, principal: VerifiedPrincipal, run_id: str, story_revision_id: str
    ) -> bool:
        """QUEUED -> RUNNING for the reserved revision; ``False`` when the work is stale."""
        ...

    def complete_story_revision(
        self,
        *,
        reservation: ParentStoryRevisionReservation,
        principal: VerifiedPrincipal,
        story: dict[str, Any],
        story_sha256: str,
        provider_call_id: str,
        model_id: str,
        model_revision: str,
    ) -> ParentStoryRunView: ...

    def fail_story_revision(
        self,
        *,
        principal: VerifiedPrincipal,
        reservation: ParentStoryRevisionReservation,
        error_code: str,
        outcome_unknown: bool,
    ) -> None: ...

    def fail_drawing_analysis(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        error_code: str,
        outcome_unknown: bool,
        expected_input_revision: int | None = None,
    ) -> None: ...

    def fail_drawing_analysis_recoverable(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        error_code: str,
        expected_input_revision: int,
    ) -> bool:
        """T-2b: a failure a retake can fix; the run stays INPUT_PROCESSING (False when stale)."""
        ...

    def start_drawing_analysis(
        self, *, principal: VerifiedPrincipal, run_id: str, expected_input_revision: int
    ) -> bool: ...

    def prepare_drawing_attach(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        idempotency_key: str,
        fingerprint: str,
        expected_run_revision: int | None,
    ) -> DrawingAttachOutcome | ParentStoryLifecycleRecord | None: ...

    def attach_uploaded_drawing(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        idempotency_key: str,
        fingerprint: str,
        expected_run_revision: int | None,
        original_asset_ref: str,
        original_sha256: str,
        original_media_type: str,
        original_size_bytes: int,
        scanner_name: str,
        scanner_version: str,
        derived_png: bytes,
        derived_sha256: str,
        storage: ObjectStoragePort,
    ) -> DrawingAttachOutcome | ParentStoryLifecycleRecord: ...

    def confirm_story_revision(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_revision: int,
        expected_story_sha256: str,
        idempotency_key: str,
    ) -> ParentStoryRunView: ...

    # ------------------------------------------------------------------ T-2c: idea and transcript
    def ensure_accepting_audio(self, *, principal: VerifiedPrincipal, run_id: str) -> None:
        """State re-check immediately before the audio upload's first ``put_object``."""
        ...

    def prepare_idea(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        idempotency_key: str,
        fingerprint: str,
        expected_run_revision: int,
    ) -> IdeaOutcome | ParentStoryLifecycleRecord | None:
        """Replay or the cheap pre-checks that run before any audio byte is read."""
        ...

    def submit_idea(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        idempotency_key: str,
        fingerprint: str,
        expected_run_revision: int,
        text: str | None = None,
        voice: VoiceInput | None = None,
        correction_base_revision: int | None = None,
        correction_text: str | None = None,
    ) -> IdeaOutcome | ParentStoryLifecycleRecord:
        """Text and/or audio (new input revision) or a transcript correction (new revision)."""
        ...

    def get_transcript(self, *, principal: VerifiedPrincipal, run_id: str) -> TranscriptView: ...

    def confirm_transcript(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        idempotency_key: str,
        expected_transcript_revision: int,
        transcript_sha256: str,
    ) -> TranscriptConfirmOutcome | ParentStoryLifecycleRecord: ...

    def read_pending_transcription(
        self, *, principal: VerifiedPrincipal, run_id: str, transcript_revision_id: str
    ) -> SpeechTranscriptionRequest | None:
        """The request for a still-current ``PENDING`` transcript, else ``None`` (stale work)."""
        ...

    def complete_transcript(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        transcript_revision_id: str,
        text: str,
        language: str,
        model_revision: str,
        config_hash: str | None,
        asr_profile_ref: str | None,
        segment_timing: list[dict[str, int]] | None,
    ) -> bool: ...

    def fail_transcript(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        transcript_revision_id: str,
        error_code: str,
    ) -> bool: ...


__all__ = [
    "ParentStoryInputRecord",
    "ParentStoryLifecycleRecord",
    "ParentStoryRevisionReservation",
    "ParentStoryRunError",
    "ParentStoryRunRecord",
    "ParentStoryRunRepositoryPort",
    "ParentStoryRunSummary",
    "ParentStoryRunView",
    "StoryRewriteOutcome",
]
