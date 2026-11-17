"""Pure DATA-25 job/attempt lifecycle for BE2-01 Phase A (candidate, fixture scope).

No framework, storage, queue or provider imports. Every transition returns a new immutable
``AiJob``; invalid transitions raise ``InvalidJobTransition``. Numeric values live only in
named ``JobRetryPolicy``/``JobPollPolicy`` instances, never in transition code.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from enum import StrEnum


class JobState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED_RETRYABLE = "failed_retryable"
    FAILED_EXHAUSTED = "failed_exhausted"
    BLOCKED_UNSAFE = "blocked_unsafe"
    CANCELLED = "cancelled"


TERMINAL_STATES = frozenset(
    {
        JobState.SUCCEEDED,
        JobState.FAILED_EXHAUSTED,
        JobState.BLOCKED_UNSAFE,
        JobState.CANCELLED,
    }
)
CANCELLABLE_STATES = frozenset({JobState.QUEUED, JobState.RUNNING, JobState.FAILED_RETRYABLE})


class ResultDisposition(StrEnum):
    """Disposition axis; deliberately separate from ``JobState`` (stale is not a state)."""

    ACCEPTED = "accepted"
    STALE = "stale"
    REJECTED = "rejected"


class ProgressKind(StrEnum):
    UNKNOWN = "unknown"
    STAGES = "stages"
    PERCENTAGE = "percentage"


class InvalidJobTransition(ValueError):
    """A transition was requested from a state or attempt that does not allow it."""


class InvalidProgress(ValueError):
    """Progress report is malformed; it is rejected rather than coerced."""


_PUBLIC_CODE = re.compile(r"^[A-Z][A-Z0-9_]{1,79}$")


def _require_public_code(code: str) -> None:
    if not isinstance(code, str) or not _PUBLIC_CODE.match(code):
        raise ValueError("failure/cancel code must match ^[A-Z][A-Z0-9_]{1,79}$")


def require_aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


@dataclass(frozen=True, slots=True)
class JobProgress:
    kind: ProgressKind
    value: float | None = None
    stage_label: str | None = None

    def __post_init__(self) -> None:
        if self.value is not None and (
            isinstance(self.value, bool)
            or not isinstance(self.value, int | float)
            or not math.isfinite(self.value)
            or not 0 <= self.value <= 100
        ):
            raise InvalidProgress("progress value must be a finite number in [0, 100]")
        if self.stage_label is not None and not (0 < len(self.stage_label) <= 80):
            raise InvalidProgress("stage_label must be 1..80 characters")
        if self.kind is ProgressKind.UNKNOWN and (
            self.value is not None or self.stage_label is not None
        ):
            raise InvalidProgress("unknown progress must have value=null and stage_label=null")
        if self.kind is ProgressKind.PERCENTAGE and self.value is None:
            raise InvalidProgress("percentage progress requires a real value")
        if self.kind is ProgressKind.STAGES and self.stage_label is None:
            raise InvalidProgress("stages progress requires stage_label")


UNKNOWN_PROGRESS = JobProgress(ProgressKind.UNKNOWN)


@dataclass(frozen=True, slots=True)
class JobRetryPolicy:
    """Named fixture policy. Values are PROPOSED and never production defaults."""

    policy_id: str
    max_attempts: int
    backoff_base_ms: int
    backoff_multiplier: int
    backoff_max_ms: int
    attempt_timeout_ms: int
    status: str = "PROPOSED"

    def __post_init__(self) -> None:
        if self.max_attempts < 1 or self.backoff_base_ms < 0 or self.backoff_multiplier < 1:
            raise ValueError("retry policy bounds are invalid")
        if self.backoff_max_ms < self.backoff_base_ms or self.attempt_timeout_ms <= 0:
            raise ValueError("retry policy bounds are invalid")

    def backoff_after(self, attempt_number: int) -> timedelta:
        delay = self.backoff_base_ms * self.backoff_multiplier ** max(attempt_number - 1, 0)
        return timedelta(milliseconds=min(delay, self.backoff_max_ms))

    def attempts_remaining(self, attempt_number: int) -> int:
        return max(self.max_attempts - attempt_number, 0)


@dataclass(frozen=True, slots=True)
class JobPollPolicy:
    """Named fixture poll policy mapped to SRS ``JOB_POLL_MIN_INTERVAL`` (PROPOSED)."""

    policy_id: str
    min_interval_ms: int
    max_interval_ms: int
    backoff_step_seconds: int
    status: str = "PROPOSED"

    def __post_init__(self) -> None:
        if not 0 < self.min_interval_ms <= self.max_interval_ms or self.backoff_step_seconds < 1:
            raise ValueError("poll policy bounds are invalid")


@dataclass(frozen=True, slots=True)
class RequestRef:
    """Immutable pinned request identity; lineage of the source is never rewritten."""

    request_id: str
    request_revision: int
    input_hash: str
    context_revision: int

    def __post_init__(self) -> None:
        if not self.request_id or self.request_revision < 1 or self.context_revision < 0:
            raise ValueError("request reference is invalid")
        if len(self.input_hash) != 64 or any(c not in "0123456789abcdef" for c in self.input_hash):
            raise ValueError("input_hash must be lowercase sha256 hex")


@dataclass(frozen=True, slots=True)
class JobScope:
    """Ownership scope used for authorization, eligibility and cancellation notices."""

    organization_id: str
    session_id: str | None
    subject_refs: tuple[str, ...]
    purpose_code: str
    target_id: str


@dataclass(frozen=True, slots=True)
class JobFailure:
    code: str
    retryable: bool
    public_message: str
    attempts_remaining: int | None


@dataclass(frozen=True, slots=True)
class ResultRef:
    artifact_ref: str
    sha256: str
    provenance: str


@dataclass(frozen=True, slots=True)
class Attempt:
    attempt_id: str
    attempt_number: int
    request_ref: RequestRef
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    outcome: str | None = None


@dataclass(frozen=True, slots=True)
class AiJob:
    job_id: str
    job_type: str
    scope: JobScope
    job_revision: int
    request_ref: RequestRef
    attempts: tuple[Attempt, ...]
    state: JobState
    correlation_id: str
    created_at: datetime
    updated_at: datetime
    retry_policy: JobRetryPolicy
    progress: JobProgress = UNKNOWN_PROGRESS
    result_disposition: ResultDisposition | None = None
    result_refs: tuple[ResultRef, ...] = ()
    failure: JobFailure | None = None
    retry_not_before: datetime | None = None
    completed_at: datetime | None = None
    lineage_note: str | None = None
    history: tuple[str, ...] = field(default=())

    @property
    def organization_id(self) -> str:
        return self.scope.organization_id

    @property
    def active_attempt(self) -> Attempt:
        return self.attempts[-1]

    @property
    def is_terminal(self) -> bool:
        return self.state in TERMINAL_STATES

    @property
    def started_at(self) -> datetime | None:
        return self.active_attempt.started_at


def _advance(job: AiJob, now: datetime, event: str, **changes: object) -> AiJob:
    require_aware(now, "now")
    return replace(
        job,
        job_revision=job.job_revision + 1,
        updated_at=now,
        history=(*job.history, event),
        **changes,  # type: ignore[arg-type]
    )


def _replace_active(job: AiJob, attempt: Attempt) -> tuple[Attempt, ...]:
    return (*job.attempts[:-1], attempt)


def _require_active(job: AiJob, attempt_id: str) -> Attempt:
    if job.active_attempt.attempt_id != attempt_id:
        raise InvalidJobTransition("attempt is not the active attempt")
    return job.active_attempt


def create_job(
    *,
    job_id: str,
    attempt_id: str,
    job_type: str,
    scope: JobScope,
    request_ref: RequestRef,
    correlation_id: str,
    retry_policy: JobRetryPolicy,
    now: datetime,
) -> AiJob:
    require_aware(now, "now")
    if not job_id or not attempt_id or not job_type or not correlation_id:
        raise ValueError("job identity fields are required")
    attempt = Attempt(attempt_id, 1, request_ref, now)
    return AiJob(
        job_id=job_id,
        job_type=job_type,
        scope=scope,
        job_revision=1,
        request_ref=request_ref,
        attempts=(attempt,),
        state=JobState.QUEUED,
        correlation_id=correlation_id,
        created_at=now,
        updated_at=now,
        retry_policy=retry_policy,
        history=("created",),
    )


def start_attempt(job: AiJob, attempt_id: str, now: datetime) -> AiJob:
    attempt = _require_active(job, attempt_id)
    if job.state is not JobState.QUEUED:
        raise InvalidJobTransition(f"cannot start from {job.state}")
    started = replace(attempt, started_at=now)
    return _advance(
        job,
        now,
        "started",
        state=JobState.RUNNING,
        attempts=_replace_active(job, started),
        progress=UNKNOWN_PROGRESS,
    )


def report_progress(job: AiJob, attempt_id: str, progress: JobProgress, now: datetime) -> AiJob:
    _require_active(job, attempt_id)
    if job.state is not JobState.RUNNING:
        raise InvalidJobTransition(f"cannot report progress from {job.state}")
    if progress == job.progress:
        return job
    return _advance(job, now, "progress", progress=progress)


def record_failure(
    job: AiJob,
    attempt_id: str,
    *,
    code: str,
    retryable: bool,
    public_message: str,
    now: datetime,
) -> AiJob:
    attempt = _require_active(job, attempt_id)
    if job.state is not JobState.RUNNING:
        raise InvalidJobTransition(f"cannot fail from {job.state}")
    _require_public_code(code)
    remaining = job.retry_policy.attempts_remaining(attempt.attempt_number)
    finished = replace(attempt, finished_at=now, outcome=f"failure:{code}")
    if retryable and remaining > 0:
        return _advance(
            job,
            now,
            "failed_retryable",
            state=JobState.FAILED_RETRYABLE,
            attempts=_replace_active(job, finished),
            failure=JobFailure(code, True, public_message, remaining),
            retry_not_before=now + job.retry_policy.backoff_after(attempt.attempt_number),
        )
    return _advance(
        job,
        now,
        "failed_exhausted",
        state=JobState.FAILED_EXHAUSTED,
        attempts=_replace_active(job, finished),
        failure=JobFailure(code, False, public_message, 0),
        retry_not_before=None,
        completed_at=now,
    )


DISPATCH_LOST = "DISPATCH_LOST"


def record_dispatch_loss(
    job: AiJob, attempt_id: str, *, public_message: str, now: datetime
) -> AiJob:
    """The active queued attempt was published but never durably started within its bound.

    The attempt closes without inventing a start: ``started_at`` stays ``None`` and the pinned
    request is kept. Retry budget left gives ``failed_retryable`` with the existing backoff;
    otherwise ``failed_exhausted``. ``record_failure`` stays RUNNING-only.
    """

    attempt = _require_active(job, attempt_id)
    if job.state is not JobState.QUEUED:
        raise InvalidJobTransition(f"cannot record dispatch loss from {job.state}")
    if attempt.started_at is not None or attempt.finished_at is not None:
        raise InvalidJobTransition("dispatch loss needs an unstarted open attempt")
    remaining = job.retry_policy.attempts_remaining(attempt.attempt_number)
    closed = replace(attempt, finished_at=now, outcome="dispatch_lost")
    if remaining > 0:
        return _advance(
            job,
            now,
            "dispatch_lost",
            state=JobState.FAILED_RETRYABLE,
            attempts=_replace_active(job, closed),
            failure=JobFailure(DISPATCH_LOST, True, public_message, remaining),
            retry_not_before=now + job.retry_policy.backoff_after(attempt.attempt_number),
        )
    return _advance(
        job,
        now,
        "dispatch_lost",
        state=JobState.FAILED_EXHAUSTED,
        attempts=_replace_active(job, closed),
        failure=JobFailure(DISPATCH_LOST, False, public_message, 0),
        retry_not_before=None,
        completed_at=now,
    )


def requeue_for_retry(job: AiJob, *, new_attempt_id: str, now: datetime) -> AiJob:
    """Policy retry: same semantic job, next attempt, same pinned request lineage."""

    if job.state is not JobState.FAILED_RETRYABLE or job.retry_not_before is None:
        raise InvalidJobTransition(f"cannot retry from {job.state}")
    if now < job.retry_not_before:
        raise InvalidJobTransition("retry backoff has not elapsed")
    number = job.active_attempt.attempt_number + 1
    if number > job.retry_policy.max_attempts:
        raise InvalidJobTransition("retry policy attempts exhausted")
    attempt = Attempt(new_attempt_id, number, job.request_ref, now)
    return _advance(
        job,
        now,
        "requeued",
        state=JobState.QUEUED,
        attempts=(*job.attempts, attempt),
        retry_not_before=None,
        progress=UNKNOWN_PROGRESS,
    )


def cancel(job: AiJob, *, reason_code: str, public_message: str, now: datetime) -> AiJob:
    """Cancel queued/running/failed_retryable; invalidates any scheduled retry."""

    _require_public_code(reason_code)
    if job.state not in CANCELLABLE_STATES:
        raise InvalidJobTransition(f"cannot cancel from {job.state}")
    attempt = job.active_attempt
    closed = (
        attempt
        if attempt.finished_at
        else replace(attempt, finished_at=now, outcome="cancelled")
    )
    return _advance(
        job,
        now,
        f"cancelled:{reason_code}",
        state=JobState.CANCELLED,
        attempts=_replace_active(job, closed),
        retry_not_before=None,
        failure=JobFailure(reason_code, False, public_message, None),
        completed_at=now,
    )


def block_unsafe(job: AiJob, attempt_id: str, *, public_message: str, now: datetime) -> AiJob:
    attempt = _require_active(job, attempt_id)
    if job.state not in {JobState.QUEUED, JobState.RUNNING}:
        raise InvalidJobTransition(f"cannot block from {job.state}")
    finished = replace(attempt, finished_at=now, outcome="blocked_unsafe")
    return _advance(
        job,
        now,
        "blocked_unsafe",
        state=JobState.BLOCKED_UNSAFE,
        attempts=_replace_active(job, finished),
        failure=JobFailure("UNSAFE_CONTENT", False, public_message, None),
        result_disposition=ResultDisposition.REJECTED,
        completed_at=now,
    )


def succeed(
    job: AiJob,
    attempt_id: str,
    *,
    result_refs: tuple[ResultRef, ...],
    disposition: ResultDisposition,
    now: datetime,
    lineage_note: str | None = None,
) -> AiJob:
    """Provider/application success. Does not approve media or complete a session."""

    attempt = _require_active(job, attempt_id)
    if job.state is not JobState.RUNNING:
        raise InvalidJobTransition(f"cannot succeed from {job.state}")
    if disposition is ResultDisposition.REJECTED or not result_refs:
        raise InvalidJobTransition("success needs result refs and accepted/stale disposition")
    finished = replace(attempt, finished_at=now, outcome=f"succeeded:{disposition}")
    return _advance(
        job,
        now,
        f"succeeded:{disposition}",
        state=JobState.SUCCEEDED,
        attempts=_replace_active(job, finished),
        result_refs=result_refs,
        result_disposition=disposition,
        failure=None,
        completed_at=now,
        lineage_note=lineage_note,
    )


def poll_after_ms(job: AiJob, policy: JobPollPolicy, now: datetime) -> int | None:
    """Bounded poll hint; ``None`` tells clients to stop polling a terminal job."""

    if job.is_terminal:
        return None
    idle_seconds = max((now - job.updated_at).total_seconds(), 0.0)
    steps = int(idle_seconds // policy.backoff_step_seconds)
    interval: int = min(policy.min_interval_ms << min(steps, 16), policy.max_interval_ms)
    if job.state is JobState.FAILED_RETRYABLE and job.retry_not_before is not None:
        # Whole seconds, so the hint (and the ETag variant built from it) changes stepwise.
        until_retry = math.ceil((job.retry_not_before - now).total_seconds()) * 1000
        interval = max(interval, min(until_retry, policy.max_interval_ms))
    return max(interval, policy.min_interval_ms)


__all__ = [
    "CANCELLABLE_STATES",
    "DISPATCH_LOST",
    "TERMINAL_STATES",
    "UNKNOWN_PROGRESS",
    "AiJob",
    "Attempt",
    "InvalidJobTransition",
    "InvalidProgress",
    "JobFailure",
    "JobPollPolicy",
    "JobProgress",
    "JobRetryPolicy",
    "JobScope",
    "JobState",
    "ProgressKind",
    "RequestRef",
    "ResultDisposition",
    "ResultRef",
    "block_unsafe",
    "cancel",
    "create_job",
    "poll_after_ms",
    "record_dispatch_loss",
    "record_failure",
    "report_progress",
    "require_aware",
    "requeue_for_retry",
    "start_attempt",
    "succeed",
]
