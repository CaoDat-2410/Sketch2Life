"""Application-owned persistence contract for authenticated Parent StoryRuns."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol


class ParentStoryRunError(RuntimeError):
    def __init__(self, status_code: int, code: str) -> None:
        self.status_code = status_code
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class ParentStoryRunRecord:
    run_id: str
    run_state: str
    parent_profile_id: str
    profile_revision_ref: str
    context_revision: int
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
    source_profile_revision_ref: str
    data_authorization_id: str
    context_revision: int
    context_snapshot: dict[str, Any]
    context_snapshot_sha256: str
    context_confirmed_by: str
    context_confirmed_at: datetime


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


class ParentStoryRunRepositoryPort(Protocol):
    def create_run(
        self,
        *,
        owner_subject: str,
        account_id: str,
        parent_profile_id: str,
        expected_profile_revision_ref: str,
        policy_version: str,
        run_id: str,
        topic: str,
        adult_confirmed_idea: str,
    ) -> ParentStoryRunRecord: ...

    def get_run(
        self, *, owner_subject: str, policy_version: str, run_id: str
    ) -> ParentStoryRunRecord: ...

    def get_active_run(
        self, *, owner_subject: str, account_id: str, policy_version: str
    ) -> ParentStoryRunRecord | None: ...

    def attach_artwork(
        self,
        *,
        owner_subject: str,
        policy_version: str,
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
        self, *, owner_subject: str, policy_version: str, run_id: str
    ) -> ParentStoryInputRecord: ...

    def record_understanding(
        self,
        *,
        owner_subject: str,
        policy_version: str,
        run_id: str,
        result_snapshot: dict[str, Any],
        candidate_subject: str,
        confidence: float,
    ) -> int: ...

    def confirm_subject(
        self,
        *,
        owner_subject: str,
        policy_version: str,
        run_id: str,
        expected_understanding_revision: int,
        confirmed_subject: str,
    ) -> int: ...

    def reserve_story_revision(
        self,
        *,
        owner_subject: str,
        policy_version: str,
        run_id: str,
        expected_understanding_revision: int,
        rewrite_instruction: str | None,
        story_revision_id: str,
        model_id: str,
        model_revision: str,
        prompt_version: str,
    ) -> ParentStoryRevisionReservation: ...

    def complete_story_revision(
        self,
        *,
        reservation: ParentStoryRevisionReservation,
        owner_subject: str,
        policy_version: str,
        story: dict[str, Any],
        story_sha256: str,
        provider_call_id: str,
        model_id: str,
        model_revision: str,
    ) -> ParentStoryRunRecord: ...

    def fail_story_revision(
        self,
        *,
        owner_subject: str,
        policy_version: str,
        reservation: ParentStoryRevisionReservation,
        error_code: str,
        outcome_unknown: bool,
    ) -> None: ...

    def fail_drawing_analysis(
        self, *, owner_subject: str, run_id: str, error_code: str, outcome_unknown: bool
    ) -> None: ...

    def confirm_story_revision(
        self,
        *,
        owner_subject: str,
        policy_version: str,
        run_id: str,
        expected_revision: int,
        expected_story_sha256: str,
    ) -> ParentStoryRunRecord: ...


__all__ = [
    "ParentStoryInputRecord",
    "ParentStoryRevisionReservation",
    "ParentStoryRunError",
    "ParentStoryRunRecord",
    "ParentStoryRunRepositoryPort",
]
