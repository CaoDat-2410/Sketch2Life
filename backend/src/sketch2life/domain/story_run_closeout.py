"""Pure rules of the adult-wait closeout and the generation deadline (FEAT-066 T-1d1).

SRS l.394 (which states wait for the adult, what starts and resets the clock), l.395 (the six-hour
generation deadline from ``accepted_at``) and l.503 FR-C-11 (``VIDEO_READY`` becomes ``COMPLETED``
and every other adult-wait state becomes ``ABANDONED`` at +168 hours; the owner lock is released and
the content is kept). No framework, storage or provider import: the store and the service read their
decisions from here, and the tests pin them over every state.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Final

from sketch2life.domain.story_video.model import VIDEO_DEADLINE_EXCEEDED

IDLE_CLOSEOUT: Final = timedelta(hours=168)
GENERATION_DEADLINE: Final = timedelta(hours=6)

# A job in these states is AI work in progress: the run is never idle (SRS l.394, "xu ly AI dang
# chay khong phai adult-wait"; the closeout never touches a QUEUED, RUNNING, RETRY_WAIT or
# reconciling job). ``RETRY_WAIT`` is listed by l.394; the run-level ``ck_story_run_job_state`` has
# no such value today, so it protects the day a retrying job is mirrored onto the run.
ACTIVE_JOB_STATES: Final = frozenset({"QUEUED", "RUNNING", "RETRY_WAIT", "AWAITING_RECONCILIATION"})

# ``VIDEO_READY`` is the one wait that ends as ``COMPLETED`` (SRS l.503).
COMPLETING_WAIT_STATES: Final = frozenset({"VIDEO_READY"})
# The other states in which the run only needs an adult command (SRS l.394). ``DRAFT`` is in the
# SRS catalogue; no code writes it yet, so it is listed for the day it is. ``SAFETY_BLOCKED`` is
# an adult-wait state of l.394 and closes ``ABANDONED`` at +168 h from the block (T-1d1-fix-DEC-3).
ABANDONING_WAIT_STATES: Final = frozenset(
    {
        "DRAFT",
        "INPUT_REVIEW",
        "SUBJECT_REVIEW",
        "PREPARATION_REVIEW",
        "SCRIPT_REVIEW",
        "SAFETY_BLOCKED",
    }
)
# ``INPUT_PROCESSING`` waits for the adult only while nothing was ever attached: a Parent run starts
# there with no job (the draft of the SRS). Once a drawing job exists, the state belongs to the AI.
DRAFT_LIKE_STATE: Final = "INPUT_PROCESSING"
ADULT_WAIT_STATES: Final = COMPLETING_WAIT_STATES | ABANDONING_WAIT_STATES | {DRAFT_LIKE_STATE}

# The two terminal states the closeout writes, shared with the tests.
IDLE_COMPLETED: Final = "COMPLETED"
IDLE_ABANDONED: Final = "ABANDONED"
CLOSEOUT_TRANSITIONS: Final[dict[str, str]] = {
    **dict.fromkeys(COMPLETING_WAIT_STATES, IDLE_COMPLETED),
    **dict.fromkeys(ABANDONING_WAIT_STATES | {DRAFT_LIKE_STATE}, IDLE_ABANDONED),
}


def idle_target(
    run_state: str, job_state: str | None, *, transcript_pending: bool = False
) -> str | None:
    """The state a run ends in when its idle time is over, or ``None`` when it is not waiting.

    ``job_state`` is the run-level job state; ``transcript_pending`` says that a voice transcript
    of the run is still being produced (an ASR job the run row does not mirror).
    """

    target = CLOSEOUT_TRANSITIONS.get(run_state)
    if target is None:
        return None
    if job_state in ACTIVE_JOB_STATES:
        return None
    if run_state == DRAFT_LIKE_STATE and (job_state is not None or transcript_pending):
        return None
    return target


def idle_since(
    updated_at: datetime,
    adult_wait_started_at: datetime | None,
    last_meaningful_activity_at: datetime | None,
) -> datetime:
    """The instant the idle time counts from: the latest of the three markers of the run.

    ``adult_wait_started_at`` (SRS l.394: the job ended and the adult is needed) and
    ``last_meaningful_activity_at`` (the last adult command that took effect) are written by the
    video path; the Parent run repository bumps ``updated_at`` on every effective write and never
    the other two, so ``updated_at`` is the clock of the earlier steps. Polling, reads, push
    receipts and playback tokens write no run row and therefore never move it.
    """

    return max(
        value
        for value in (updated_at, adult_wait_started_at, last_meaningful_activity_at)
        if value is not None
    )


def idle_closeout_due(since: datetime, now: datetime) -> bool:
    return now - since >= IDLE_CLOSEOUT


def generation_deadline_at(accepted_at: datetime) -> datetime:
    return accepted_at + GENERATION_DEADLINE


def generation_deadline_due(accepted_at: datetime, now: datetime) -> bool:
    return now >= generation_deadline_at(accepted_at)


__all__ = [
    "ABANDONING_WAIT_STATES",
    "ACTIVE_JOB_STATES",
    "ADULT_WAIT_STATES",
    "CLOSEOUT_TRANSITIONS",
    "COMPLETING_WAIT_STATES",
    "DRAFT_LIKE_STATE",
    "GENERATION_DEADLINE",
    "IDLE_ABANDONED",
    "IDLE_CLOSEOUT",
    "IDLE_COMPLETED",
    "VIDEO_DEADLINE_EXCEEDED",
    "generation_deadline_at",
    "generation_deadline_due",
    "idle_closeout_due",
    "idle_since",
    "idle_target",
]
