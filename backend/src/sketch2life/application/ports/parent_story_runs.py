"""Application-owned persistence contract for authenticated Parent StoryRuns."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_profile_lookup import ParentStoryProfileReference


class ParentStoryRunError(RuntimeError):
    def __init__(
        self, status_code: int, code: str, *, current_version: int | None = None
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.current_version = current_version
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
    receipt_id: str
    replayed: bool = False
    replay_body: dict[str, Any] | None = None
    # FR-C-08: set only on the replay of a purged run; the route returns the projection.
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


@dataclass(frozen=True, slots=True)
class ParentActivitySuggestionReservation:
    run_id: str
    suggestion_set_id: str
    set_revision: int
    understanding_revision: int
    input_revision: int
    context_revision: int
    context_snapshot: dict[str, Any]
    subject_label: str
    visible_features: tuple[str, ...]
    lesson_pin_snapshot: dict[str, Any] | None
    excluded_candidate_keys: tuple[str, ...]
    excluded_activities: tuple[dict[str, Any], ...]
    receipt_id: str | None = None
    replayed: bool = False
    replay_body: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class ParentActivitySelectionRecord:
    run_id: str
    activity_selection_id: str
    suggestion_set_id: str
    selection_revision: int
    understanding_revision: int
    activity_index: int
    activity_snapshot: dict[str, Any]
    activity_snapshot_sha256: str
    created_at: datetime


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
        intended_drawing_subject: str | None = None,
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
        intended_drawing_subject: str | None = None,
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

    def reserve_activity_suggestion_set(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_understanding_revision: int,
        idempotency_key: str,
    ) -> ParentActivitySuggestionReservation: ...

    def complete_activity_suggestion_set(
        self,
        *,
        principal: VerifiedPrincipal,
        reservation: ParentActivitySuggestionReservation,
        response: dict[str, Any],
        provider_call_id: str | None,
    ) -> dict[str, Any]: ...

    def fail_activity_suggestion_set(
        self,
        *,
        principal: VerifiedPrincipal,
        reservation: ParentActivitySuggestionReservation,
        error_code: str,
        response_status: int,
    ) -> None: ...

    def select_activity(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        suggestion_set_id: str,
        expected_understanding_revision: int,
        activity_index: int,
        idempotency_key: str,
        activity_selection_id: str,
    ) -> ParentActivitySelectionRecord: ...

    def record_understanding(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        result_snapshot: dict[str, Any],
        candidate_subject: str,
        confidence: float,
    ) -> int: ...

    def confirm_subject(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_understanding_revision: int,
        confirmed_subject: str,
        idempotency_key: str,
    ) -> int | ParentStoryLifecycleRecord: ...

    def reserve_story_revision(
        self,
        *,
        principal: VerifiedPrincipal,
        account_id: str,
        run_id: str,
        expected_understanding_revision: int,
        rewrite_instruction: str | None,
        idempotency_key: str,
        story_revision_id: str,
        model_id: str,
        model_revision: str,
        prompt_version: str,
    ) -> ParentStoryRevisionReservation: ...

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
        self, *, principal: VerifiedPrincipal, run_id: str, error_code: str, outcome_unknown: bool
    ) -> None: ...

    def confirm_story_revision(
        self,
        *,
        principal: VerifiedPrincipal,
        run_id: str,
        expected_revision: int,
        expected_story_sha256: str,
        idempotency_key: str,
    ) -> ParentStoryRunView: ...


__all__ = [
    "ParentStoryInputRecord",
    "ParentStoryLifecycleRecord",
    "ParentActivitySelectionRecord",
    "ParentActivitySuggestionReservation",
    "ParentStoryRevisionReservation",
    "ParentStoryRunError",
    "ParentStoryRunRecord",
    "ParentStoryRunRepositoryPort",
    "ParentStoryRunSummary",
    "ParentStoryRunView",
]
