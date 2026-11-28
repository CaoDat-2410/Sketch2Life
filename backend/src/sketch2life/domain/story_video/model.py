"""Pure state machine of one Parent video request (``story.video_generations``).

FEAT-066 goal v3, T-1a (SRS l.395 VideoGeneration, l.394 StoryRun states, FR-AI-07 l.573). No
framework, storage or provider import. One row is one request: it starts as an intent
(``ADMISSION_PENDING``), becomes ``ACCEPTED`` only after the compute reservation and the quota
admission are both confirmed, and ends in one of the settled states. One constant maps a
generation state to the run state that goes with it, so the service and the tests share it.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final


class GenerationState(StrEnum):
    ADMISSION_PENDING = "ADMISSION_PENDING"
    ADMISSION_REJECTED = "ADMISSION_REJECTED"
    ACCEPTED = "ACCEPTED"
    QUEUED = "QUEUED"
    GENERATING = "GENERATING"
    TECHNICAL_VALIDATING = "TECHNICAL_VALIDATING"
    SAFETY_VALIDATING = "SAFETY_VALIDATING"
    READY = "READY"
    SAFETY_BLOCKED = "SAFETY_BLOCKED"
    FAILED = "FAILED"
    REJECTED_BY_ADULT = "REJECTED_BY_ADULT"
    SUPERSEDED = "SUPERSEDED"


class GenerationKind(StrEnum):
    INITIAL = "INITIAL"
    QUALITY_REGEN = "QUALITY_REGEN"


class ValidationState(StrEnum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"


S = GenerationState

# The intent and every state of an accepted request that has not reached a settled state. A purge
# waits for these (a worker or the reconciler still owns the row); one run holds at most one.
OPEN_STATES: Final = frozenset(
    {
        S.ADMISSION_PENDING,
        S.ACCEPTED,
        S.QUEUED,
        S.GENERATING,
        S.TECHNICAL_VALIDATING,
        S.SAFETY_VALIDATING,
    }
)
IN_FLIGHT_STATES: Final = OPEN_STATES - {S.ADMISSION_PENDING}
# States in which the provider work has started: the compute reservation is settled, not released.
STARTED_STATES: Final = frozenset({S.GENERATING, S.TECHNICAL_VALIDATING, S.SAFETY_VALIDATING})
SETTLED_STATES: Final = frozenset(GenerationState) - OPEN_STATES

TRANSITIONS: Final[dict[GenerationState, frozenset[GenerationState]]] = {
    S.ADMISSION_PENDING: frozenset({S.ACCEPTED, S.ADMISSION_REJECTED, S.FAILED}),
    S.ACCEPTED: frozenset({S.QUEUED, S.FAILED}),
    S.QUEUED: frozenset({S.GENERATING, S.FAILED}),
    S.GENERATING: frozenset({S.TECHNICAL_VALIDATING, S.FAILED}),
    S.TECHNICAL_VALIDATING: frozenset({S.SAFETY_VALIDATING, S.FAILED}),
    S.SAFETY_VALIDATING: frozenset({S.READY, S.SAFETY_BLOCKED, S.FAILED}),
    S.READY: frozenset({S.REJECTED_BY_ADULT, S.SUPERSEDED}),
    S.ADMISSION_REJECTED: frozenset(),
    S.SAFETY_BLOCKED: frozenset(),
    S.FAILED: frozenset(),
    S.REJECTED_BY_ADULT: frozenset(),
    S.SUPERSEDED: frozenset(),
}

# The run state that goes with a generation state (SRS l.394). ``SUPERSEDED`` has no run state of
# its own: a newer generation decides it (T-1b). V4-A SAFETY_BLOCKED exit (owner decision C11): a
# blocked output returns the adult to the script review, like a refused admission, so the run state
# ``SAFETY_BLOCKED`` is no longer written; it stays valid for rows written before (SRS l.420).
RUN_STATE_FOR_GENERATION: Final[dict[GenerationState, str]] = {
    S.ADMISSION_PENDING: "VIDEO_ADMISSION_PENDING",
    S.ADMISSION_REJECTED: "SCRIPT_REVIEW",
    S.ACCEPTED: "VIDEO_QUEUED",
    S.QUEUED: "VIDEO_QUEUED",
    S.GENERATING: "VIDEO_GENERATING",
    S.TECHNICAL_VALIDATING: "VIDEO_SAFETY_VALIDATING",
    S.SAFETY_VALIDATING: "VIDEO_SAFETY_VALIDATING",
    S.READY: "VIDEO_READY",
    S.SAFETY_BLOCKED: "SCRIPT_REVIEW",
    S.FAILED: "FAILED",
    S.REJECTED_BY_ADULT: "SCRIPT_REVIEW",
}
# The run states in which the adult may confirm the story again or rewrite it. ``SAFETY_BLOCKED`` is
# legacy-only: rows written before the exit stay accepted (D6); no new write produces it.
REVIEWABLE_RUN_STATES: Final = frozenset({"SCRIPT_REVIEW", "SAFETY_BLOCKED"})
# The run states the six new values of ``ck_story_run_state`` add; every video state of a run.
VIDEO_RUN_STATES: Final = frozenset(
    {
        "VIDEO_ADMISSION_PENDING",
        "VIDEO_QUEUED",
        "VIDEO_GENERATING",
        "VIDEO_SAFETY_VALIDATING",
        "VIDEO_READY",
        "SAFETY_BLOCKED",
    }
)

# The run-level ``job_state`` clients already read (``ParentStoryRunResponseV1.job_state``).
RUN_JOB_STATE_FOR_GENERATION: Final[dict[GenerationState, str]] = {
    S.ACCEPTED: "QUEUED",
    S.QUEUED: "QUEUED",
    S.GENERATING: "RUNNING",
    S.TECHNICAL_VALIDATING: "RUNNING",
    S.SAFETY_VALIDATING: "RUNNING",
    S.READY: "SUCCEEDED",
    S.SAFETY_BLOCKED: "FAILED",
    S.FAILED: "FAILED",
}

# ``GET /v1/jobs/{id}`` state of a generation that has a job (SRS l.779; D10 of the T-1a plan).
PUBLIC_JOB_STATE: Final[dict[GenerationState, str]] = {
    S.ACCEPTED: "queued",
    S.QUEUED: "queued",
    S.GENERATING: "running",
    S.TECHNICAL_VALIDATING: "running",
    S.SAFETY_VALIDATING: "running",
    S.READY: "succeeded",
    S.REJECTED_BY_ADULT: "succeeded",
    S.SUPERSEDED: "succeeded",
    S.FAILED: "failed_exhausted",
    S.SAFETY_BLOCKED: "blocked_unsafe",
}

# At most three accepted requests per run: the first one and two quality regenerations (l.573).
MAX_ACCEPTED_REQUESTS: Final = 3
# Candidate closed set of the quality-regeneration reason (the SRS names the field only).
QUALITY_REASON_CODES: Final = ("QUALITY_LOW", "NOT_MATCHING_STORY", "CONTENT_CONCERN", "OTHER")

# T-1b: the safe reason an adult gives when a ready video does not fit (SRS l.1671). It is the same
# closed set as the quality-regeneration reason: the adult's word is never free text.
UNSUITABLE_REASON_CODES: Final = QUALITY_REASON_CODES
# The only run state in which a ready video can be marked unsuitable or the run completed
# (SRS l.1671-1672: the run waits for the adult with the video in front of them).
VIDEO_READY_RUN_STATE: Final = "VIDEO_READY"
# V4-A T-1c-fix: a closed run keeps its ready video until the user deletes the run (owner decisions
# O-3 and C1(a)); the Complete command and the idle closeout end the run, not the playback.
COMPLETED_RUN_STATE: Final = "COMPLETED"
REPLAYABLE_RUN_STATES: Final = frozenset({VIDEO_READY_RUN_STATE, COMPLETED_RUN_STATE})

# T-1c (SRS l.875, l.1811): the closed set of failure codes a client may read about a video. Every
# other stored ``safe_failure_code`` is shown as ``VIDEO_TECHNICAL_FAILURE``; no provider text, no
# internal code and no cancellation reason ever leaves Story.
VIDEO_SAFETY_BLOCKED: Final = "VIDEO_SAFETY_BLOCKED"
VIDEO_DEADLINE_EXCEEDED: Final = "VIDEO_DEADLINE_EXCEEDED"
VIDEO_TECHNICAL_FAILURE: Final = "VIDEO_TECHNICAL_FAILURE"
PROVIDER_UNAVAILABLE: Final = "PROVIDER_UNAVAILABLE"
PUBLIC_FAILURE_CODES: Final = frozenset(
    {VIDEO_SAFETY_BLOCKED, VIDEO_DEADLINE_EXCEEDED, VIDEO_TECHNICAL_FAILURE, PROVIDER_UNAVAILABLE}
)
# The stored safety-block code of T-1a (``SAFETY_BLOCKED``) is the same fact as the public one.
_PUBLIC_FAILURE_ALIASES: Final = {"SAFETY_BLOCKED": VIDEO_SAFETY_BLOCKED}

RUN_CANCELLED: Final = "RUN_CANCELLED"
VIDEO_QUOTA_EXCEEDED: Final = "VIDEO_QUOTA_EXCEEDED"
QUOTA_ALLOCATION_NOT_FOUND: Final = "QUOTA_ALLOCATION_NOT_FOUND"
TEACHER_QUOTA_INSUFFICIENT: Final = "TEACHER_QUOTA_INSUFFICIENT"
SCHOOL_QUOTA_INSUFFICIENT: Final = "SCHOOL_QUOTA_INSUFFICIENT"
SUBSCRIPTION_RESTRICTED: Final = "SUBSCRIPTION_RESTRICTED"
AI_COST_LIMIT_REACHED: Final = "AI_COST_LIMIT_REACHED"
# Admission refusals: code to the HTTP status of the first answer and of every replay.
ADMISSION_REFUSALS: Final[dict[str, int]] = {
    VIDEO_QUOTA_EXCEEDED: 409,
    QUOTA_ALLOCATION_NOT_FOUND: 409,
    TEACHER_QUOTA_INSUFFICIENT: 409,
    SCHOOL_QUOTA_INSUFFICIENT: 409,
    SUBSCRIPTION_RESTRICTED: 409,
    AI_COST_LIMIT_REACHED: 503,
}


class InvalidGenerationTransition(ValueError):
    """A generation state change that the machine does not allow."""


def can_transition(current: GenerationState, target: GenerationState) -> bool:
    return target in TRANSITIONS[current]


def require_transition(current: GenerationState, target: GenerationState) -> None:
    if not can_transition(current, target):
        raise InvalidGenerationTransition(f"{current} -> {target} is not allowed")


def public_failure_code(stored: str | None) -> str:
    """The client-visible code of a stored ``safe_failure_code`` (always one of the closed set)."""

    code = _PUBLIC_FAILURE_ALIASES.get(stored or "", stored or "")
    return code if code in PUBLIC_FAILURE_CODES else VIDEO_TECHNICAL_FAILURE


def is_playable(
    *,
    run_state: str,
    generation_state: str | None,
    technical: str | None,
    consistency: str | None,
    safety: str | None,
    has_output: bool,
    allow_completed: bool = False,
) -> bool:
    """Playback needs the run at ``VIDEO_READY`` and the current generation ``READY`` with every
    validation ``PASSED`` and an output (SRS l.1676; the T-1b hand-over: both states together,
    never the generation pointer alone).

    V4-A T-1c-fix: with ``allow_completed`` a ``COMPLETED`` run also plays (owner decisions O-3 and
    C1(a): Complete and the idle closeout end the run, not the playback). The caller passes the
    flag; the predicate knows no role. The default stays strict.
    """

    allowed = REPLAYABLE_RUN_STATES if allow_completed else frozenset({VIDEO_READY_RUN_STATE})
    return (
        run_state in allowed
        and generation_state == str(GenerationState.READY)
        and has_output
        and {technical, consistency, safety} == {str(ValidationState.PASSED)}
    )


def has_ready_output(
    *,
    generation_state: str | None,
    technical: str | None,
    consistency: str | None,
    safety: str | None,
    has_output: bool,
) -> bool:
    """The run-state-agnostic variant of ``is_playable`` (T-4b2, OD-14 window): a ``READY``
    generation with every validation ``PASSED`` and an output. A run that was completed without
    being projected still holds such a sample, so the occurrence must not start another one."""

    return (
        generation_state == str(GenerationState.READY)
        and has_output
        and {technical, consistency, safety} == {str(ValidationState.PASSED)}
    )


def generation_kind_for(accepted_count: int) -> GenerationKind:
    """The first accepted request is ``INITIAL``; every later one is ``QUALITY_REGEN``."""

    return GenerationKind.INITIAL if accepted_count == 0 else GenerationKind.QUALITY_REGEN


__all__ = [
    "ADMISSION_REFUSALS",
    "AI_COST_LIMIT_REACHED",
    "COMPLETED_RUN_STATE",
    "IN_FLIGHT_STATES",
    "MAX_ACCEPTED_REQUESTS",
    "OPEN_STATES",
    "PROVIDER_UNAVAILABLE",
    "PUBLIC_FAILURE_CODES",
    "PUBLIC_JOB_STATE",
    "QUALITY_REASON_CODES",
    "REPLAYABLE_RUN_STATES",
    "REVIEWABLE_RUN_STATES",
    "RUN_CANCELLED",
    "RUN_JOB_STATE_FOR_GENERATION",
    "RUN_STATE_FOR_GENERATION",
    "QUOTA_ALLOCATION_NOT_FOUND",
    "SCHOOL_QUOTA_INSUFFICIENT",
    "SETTLED_STATES",
    "STARTED_STATES",
    "SUBSCRIPTION_RESTRICTED",
    "TEACHER_QUOTA_INSUFFICIENT",
    "TRANSITIONS",
    "UNSUITABLE_REASON_CODES",
    "VIDEO_DEADLINE_EXCEEDED",
    "VIDEO_QUOTA_EXCEEDED",
    "VIDEO_READY_RUN_STATE",
    "VIDEO_RUN_STATES",
    "VIDEO_SAFETY_BLOCKED",
    "VIDEO_TECHNICAL_FAILURE",
    "GenerationKind",
    "GenerationState",
    "InvalidGenerationTransition",
    "ValidationState",
    "can_transition",
    "generation_kind_for",
    "has_ready_output",
    "is_playable",
    "public_failure_code",
    "require_transition",
]
