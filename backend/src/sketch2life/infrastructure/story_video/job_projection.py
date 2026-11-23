"""Read-only job projection of a Parent video generation (FEAT-066 T-1a, D10; SRS l.779, l.1675).

The generation row is the durable job record (D9: no ``ai_jobs`` row exists for a Parent before the
first real worker, plan Q2). ``SqlParentVideoJobs`` is the ``ParentJobScopePort`` that lets
``GET /v1/jobs/{job_id}`` read it for the Parent who owns the run (``SqlTeacherVideoJobs``, T-4b3b
D14, does the same for the Teacher of a Teacher run). It is one query by ``job_ref`` and it proves
ownership with the run's owner scope (``actor_scope_kind = PARENT_ACCOUNT AND
actor_scope_ref = ?``), so a run that is ``COMPLETED``, ``FAILED`` or ``ABANDONED`` (the lock column
is NULL there) stays readable. A purged run answers not found, and so does a row without a job
reference (an intent or a refused request). Nothing but ids, hashes, states and safe codes is
mapped: no storage key, no provider text, no result reference (playback is the playback route,
l.1692).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sqlalchemy import Engine, exists, literal, select

from sketch2life.application.job_kinds import VIDEO_GENERATION_JOB_TYPE, JobActor
from sketch2life.application.ports.story_run_actor import TEACHER_COMMAND_SCOPE_KIND
from sketch2life.application.ports.story_run_lifecycle import PURGE_STATES
from sketch2life.domain.ai_jobs.model import (
    UNKNOWN_PROGRESS,
    AiJob,
    Attempt,
    JobFailure,
    JobProgress,
    JobRetryPolicy,
    JobScope,
    JobState,
    ProgressKind,
    RequestRef,
    ResultDisposition,
)
from sketch2life.domain.story_video.model import (
    PUBLIC_JOB_STATE,
    GenerationState,
    public_failure_code,
)
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.teacher_run_access import occurrence_pin_select
from sketch2life.infrastructure.story_run_lite import tables as story_tables

# The job record has no organization (a Parent job has none); the reader needs a string, so a fixed
# non-identifying placeholder stands in. It is never serialized (``AiJobStatusV1`` has no such
# field).
PARENT_JOB_PLACEHOLDER_ORGANIZATION = "parent-video"
# One attempt, the 6-hour deadline of SRS l.395 (accepted_at + 6h) as the attempt bound.
_RETRY_POLICY = JobRetryPolicy(
    policy_id="srs.video_generation.v1",
    max_attempts=1,
    backoff_base_ms=0,
    backoff_multiplier=1,
    backoff_max_ms=0,
    attempt_timeout_ms=6 * 3600 * 1000,
    status="SRS_L395",
)
_PUBLIC_MESSAGES = {
    "RUN_CANCELLED": "Lượt kể chuyện đã bị hủy.",
    "SAFETY_BLOCKED": "Video không đạt kiểm tra an toàn.",
    # The SRS label of a failed attempt (l.1807); the deadline has no SRS code (T-1d1-fix OPEN Q3b).
    "VIDEO_DEADLINE_EXCEEDED": "Không tạo được lần này.",
}
_DEFAULT_MESSAGE = "Không thể tạo video."
_RUNNING_STAGES = {
    GenerationState.GENERATING: "generating",
    GenerationState.TECHNICAL_VALIDATING: "technical_validating",
    GenerationState.SAFETY_VALIDATING: "safety_validating",
}

_GENERATIONS = story_tables.video_generations
_RUNS = story_tables.story_runs
_REVISIONS = story_tables.story_revisions


class SqlParentVideoJobs:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def owned_job(self, actor: JobActor, job_id: str) -> AiJob | None:
        if actor.story_scope_ref is None:
            return None
        statement = (
            select(_GENERATIONS, _REVISIONS.c.revision_no)
            .join(_RUNS, _RUNS.c.run_id == _GENERATIONS.c.story_run_id)
            .join(
                _REVISIONS,
                _REVISIONS.c.story_revision_id == _GENERATIONS.c.story_revision_id,
            )
            .where(
                _GENERATIONS.c.job_ref == job_id,
                _RUNS.c.actor_scope_kind == "PARENT_ACCOUNT",
                _RUNS.c.actor_scope_ref == actor.story_scope_ref,
                _RUNS.c.run_state.not_in(sorted(PURGE_STATES)),
            )
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().one_or_none()
        return None if row is None else build_video_job(row)


class SqlTeacherVideoJobs:
    """The ``TeacherJobScopePort`` of the video generation of a Teacher run (T-4b3b D14).

    One query by ``job_ref``. The run must be an ``ORGANIZATION`` run with an occurrence pin and
    not purged, AND the asker must be the occurrence's CURRENT responsible Teacher, written once in
    ``occurrence_pin_select`` (the same predicate the run access port uses): not a Manager, a guide,
    an observer, another or a former Teacher, never ``created_by_actor_ref``. The row is read
    whatever the state of the run, so a completed run stays readable by its Teacher. Result refs
    stay empty and nothing but ids, hashes, states and safe codes is mapped.
    """

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def owned_job(self, actor: JobActor, job_id: str) -> AiJob | None:
        if actor.account_role != "teacher":
            return None
        pinned = exists(
            occurrence_pin_select(
                literal(1),
                occurrence_ref=_RUNS.c.occurrence_ref,
                organization_id=_RUNS.c.actor_scope_ref,
            ).where(AdultIdentityModel.account_id == actor.account_id)
        )
        statement = (
            select(_GENERATIONS, _REVISIONS.c.revision_no)
            .join(_RUNS, _RUNS.c.run_id == _GENERATIONS.c.story_run_id)
            .join(
                _REVISIONS,
                _REVISIONS.c.story_revision_id == _GENERATIONS.c.story_revision_id,
            )
            .where(
                _GENERATIONS.c.job_ref == job_id,
                _RUNS.c.actor_scope_kind == TEACHER_COMMAND_SCOPE_KIND,
                _RUNS.c.occurrence_ref.is_not(None),
                _RUNS.c.run_state.not_in(sorted(PURGE_STATES)),
                pinned,
            )
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().one_or_none()
        return None if row is None else build_video_job(row)


def build_video_job(values: Mapping[Any, Any]) -> AiJob | None:
    """Map one generation row to the job shape; a row without a job reference has none."""

    job_ref = values["job_ref"]
    accepted_at = values["accepted_at"]
    if job_ref is None or accepted_at is None:
        return None
    state = GenerationState(values["state"])
    public_state = PUBLIC_JOB_STATE.get(state)
    if public_state is None:
        return None
    request_ref = RequestRef(
        request_id=str(values["video_generation_id"]),
        request_revision=int(values["revision_no"]),
        input_hash=str(values["target_script_hash"]),
        context_revision=0,
    )
    started_at = values["started_at"]
    completed_at = values["completed_at"]
    attempt = Attempt(
        attempt_id=f"{job_ref}-1",
        attempt_number=1,
        request_ref=request_ref,
        created_at=accepted_at,
        started_at=started_at,
        finished_at=completed_at,
    )
    failure: JobFailure | None = None
    if state in {GenerationState.FAILED, GenerationState.SAFETY_BLOCKED}:
        stored = values["safe_failure_code"] or "VIDEO_GENERATION_FAILED"
        failure = JobFailure(
            # T-1c D8: only the closed public set leaves Story; the message keys on the stored code.
            code=public_failure_code(str(stored)),
            retryable=False,
            public_message=_PUBLIC_MESSAGES.get(str(stored), _DEFAULT_MESSAGE),
            attempts_remaining=0,
        )
    stage = _RUNNING_STAGES.get(state)
    progress = (
        UNKNOWN_PROGRESS if stage is None else JobProgress(ProgressKind.STAGES, stage_label=stage)
    )
    disposition = ResultDisposition.ACCEPTED if public_state == "succeeded" else None
    return AiJob(
        job_id=str(job_ref),
        job_type=VIDEO_GENERATION_JOB_TYPE,
        scope=JobScope(
            organization_id=PARENT_JOB_PLACEHOLDER_ORGANIZATION,
            session_id=None,
            subject_refs=(),
            purpose_code="STORY_VIDEO",
            target_id=str(values["video_generation_id"]),
        ),
        job_revision=int(values["generation_revision"]),
        request_ref=request_ref,
        attempts=(attempt,),
        state=JobState(public_state),
        correlation_id=str(job_ref),
        created_at=accepted_at,
        updated_at=values["updated_at"],
        retry_policy=_RETRY_POLICY,
        progress=progress,
        result_disposition=disposition,
        result_refs=(),
        failure=failure,
        completed_at=completed_at,
    )


__all__ = [
    "PARENT_JOB_PLACEHOLDER_ORGANIZATION",
    "SqlParentVideoJobs",
    "SqlTeacherVideoJobs",
    "build_video_job",
]
