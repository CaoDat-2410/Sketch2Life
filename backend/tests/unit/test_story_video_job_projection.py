"""FEAT-066 T-1a: the Parent video job registry entry and the generation-to-job mapping (D10).

The route, the ownership query and the read counts are in
``tests/integration/story_video/test_video_generations_postgres.py``; this module pins the pure
mapping (state, ids, hashes, failure, empty results) and the fail-closed registry entry.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from sketch2life.application.job_kinds import (
    VIDEO_GENERATION_JOB_TYPE,
    ActorMembership,
    FirstOwnedParentJobs,
    JobActor,
    JobKindSpec,
    JobTargetKind,
    NoParentJobs,
    build_job_kind_registry,
    deny_organization_actors,
    deny_scope,
    video_generation_spec,
    withhold_results,
    withhold_video_results,
)
from sketch2life.domain.ai_jobs.model import JobState, ProgressKind
from sketch2life.domain.story_video.model import PUBLIC_JOB_STATE, GenerationState
from sketch2life.infrastructure.story_video.job_projection import (
    PARENT_JOB_PLACEHOLDER_ORGANIZATION,
    build_video_job,
)

NOW = datetime(2026, 11, 20, 12, 0, tzinfo=UTC)
HASH = "a" * 64


def _row(state: str = "QUEUED", **changes: Any) -> dict[str, Any]:
    values: dict[str, Any] = {
        "video_generation_id": "33333333-3333-4333-8333-333333333333",
        "job_ref": "vjob_" + "1" * 32,
        "state": state,
        "target_script_hash": HASH,
        "revision_no": 2,
        "generation_revision": 4,
        "accepted_at": NOW,
        "started_at": None,
        "completed_at": None,
        "updated_at": NOW + timedelta(seconds=5),
        "safe_failure_code": None,
    }
    values.update(changes)
    return values


@pytest.mark.parametrize("state", sorted(PUBLIC_JOB_STATE, key=str))
def test_every_job_bearing_state_maps_to_a_public_state(state: GenerationState) -> None:
    job = build_video_job(_row(state=str(state), safe_failure_code="X_CODE"))
    assert job is not None
    assert job.state is JobState(PUBLIC_JOB_STATE[state])
    assert job.job_type == VIDEO_GENERATION_JOB_TYPE


def test_the_mapping_follows_the_plan_field_by_field() -> None:
    job = build_video_job(_row("GENERATING", started_at=NOW + timedelta(seconds=1)))
    assert job is not None
    assert job.job_id == "vjob_" + "1" * 32 and job.correlation_id == job.job_id
    assert job.scope.target_id == "33333333-3333-4333-8333-333333333333"
    assert job.scope.organization_id == PARENT_JOB_PLACEHOLDER_ORGANIZATION
    assert job.scope.session_id is None and job.scope.subject_refs == ()
    assert job.job_revision == 4  # the generation revision
    assert job.request_ref.request_revision == 2  # the story revision number
    assert job.request_ref.input_hash == HASH  # the target script hash
    assert job.request_ref.request_id == "33333333-3333-4333-8333-333333333333"
    assert job.active_attempt.attempt_number == 1
    assert job.created_at == NOW and job.updated_at == NOW + timedelta(seconds=5)
    assert job.result_refs == ()  # playback is the playback route, never a job result (l.1692)
    assert job.progress.kind is ProgressKind.STAGES and job.progress.stage_label == "generating"
    assert job.failure is None and job.result_disposition is None


def test_a_queued_job_has_no_progress_and_a_succeeded_one_is_accepted_without_results() -> None:
    queued = build_video_job(_row("ACCEPTED"))
    assert queued is not None and queued.progress.kind is ProgressKind.UNKNOWN
    done = build_video_job(_row("READY", completed_at=NOW + timedelta(minutes=2)))
    assert done is not None and done.state is JobState.SUCCEEDED
    assert done.result_disposition is not None and done.result_disposition.value == "accepted"
    assert done.result_refs == () and done.completed_at == NOW + timedelta(minutes=2)


@pytest.mark.parametrize(
    ("state", "state_value"),
    [("FAILED", JobState.FAILED_EXHAUSTED), ("SAFETY_BLOCKED", JobState.BLOCKED_UNSAFE)],
)
def test_a_failure_carries_a_safe_code_and_never_retries(state: str, state_value: JobState) -> None:
    job = build_video_job(_row(state, safe_failure_code="RUN_CANCELLED"))
    assert job is not None and job.state is state_value
    assert job.failure is not None and job.failure.code == "VIDEO_TECHNICAL_FAILURE"
    assert job.failure.retryable is False and job.failure.attempts_remaining == 0
    assert job.failure.public_message and "provider" not in job.failure.public_message.lower()
    fallback = build_video_job(_row(state, safe_failure_code=None))
    assert fallback is not None and fallback.failure is not None
    assert fallback.failure.code == "VIDEO_TECHNICAL_FAILURE"


def test_the_deadline_failure_has_its_public_code_and_the_srs_label() -> None:
    job = build_video_job(_row("FAILED", safe_failure_code="VIDEO_DEADLINE_EXCEEDED"))
    assert job is not None and job.state is JobState.FAILED_EXHAUSTED
    assert job.failure is not None and job.failure.code == "VIDEO_DEADLINE_EXCEEDED"
    assert job.failure.public_message == "Không tạo được lần này."  # SRS l.1807
    assert job.failure.retryable is False


def test_an_intent_and_a_refused_request_are_not_jobs() -> None:
    assert build_video_job(_row("ADMISSION_PENDING", job_ref=None, accepted_at=None)) is None
    assert build_video_job(_row("ADMISSION_REJECTED", job_ref=None, accepted_at=None)) is None
    assert build_video_job(_row("QUEUED", job_ref=None)) is None


def test_the_registry_entry_is_fail_closed_and_denies_every_organization_actor() -> None:
    spec = video_generation_spec()
    assert spec.target_kind is JobTargetKind.VIDEO_GENERATION
    assert spec.job_types == (VIDEO_GENERATION_JOB_TYPE,)
    # an explicit rule and eligibility, never the module defaults (JobKindSpec refuses those)
    assert spec.scope_rule is deny_organization_actors and spec.scope_rule is not deny_scope
    assert spec.eligibility is withhold_video_results and spec.eligibility is not withhold_results
    assert spec.rule_grants_teacher_role is False
    membership = ActorMembership(
        "org-1",
        frozenset({"teacher", "school_admin"}),
        frozenset({"c1"}),
        {"c1": frozenset({"teacher"})},
    )
    job = build_video_job(_row("READY"))
    assert job is not None
    assert spec.scope_rule(membership, job) is False
    assert spec.eligibility(job) is False
    with pytest.raises(ValueError):
        JobKindSpec(JobTargetKind.VIDEO_GENERATION, ("x",))  # the defaults are refused


def test_the_production_registry_knows_the_video_job_type() -> None:
    class _Classes:
        def class_for(self, organization_id: str, source_document_id: str) -> str | None:
            return None

    registry = build_job_kind_registry(_Classes())
    assert registry.for_job_type(VIDEO_GENERATION_JOB_TYPE) is not None
    assert registry.for_job_type(VIDEO_GENERATION_JOB_TYPE).target_kind is (  # type: ignore[union-attr]
        JobTargetKind.VIDEO_GENERATION
    )


def _actor(ref: str | None = "s" * 64) -> JobActor:
    return JobActor("account-1", "parent", lambda _org: None, story_scope_ref=ref)


def test_the_composite_parent_port_returns_the_first_owner_and_none_when_nobody_owns() -> None:
    job = build_video_job(_row("QUEUED"))
    assert job is not None
    asked: list[str] = []

    class _Owns:
        def owned_job(self, actor: JobActor, job_id: str) -> Any:
            asked.append("owns")
            return job

    class _Never:
        def owned_job(self, actor: JobActor, job_id: str) -> Any:
            asked.append("never")
            return None

    assert FirstOwnedParentJobs(_Never(), _Owns()).owned_job(_actor(), "j") is job
    assert asked == ["never", "owns"]
    asked.clear()
    assert FirstOwnedParentJobs(_Owns(), _Never()).owned_job(_actor(), "j") is job
    assert asked == ["owns"]  # the first owner wins, the rest are not asked
    assert FirstOwnedParentJobs(_Never()).owned_job(_actor(), "j") is None
    assert FirstOwnedParentJobs().owned_job(_actor(), "j") is None
    assert NoParentJobs().owned_job(_actor(), "j") is None


def test_the_actor_scope_ref_defaults_to_none_so_older_callers_keep_working() -> None:
    assert JobActor("a", "teacher", lambda _org: None).story_scope_ref is None
