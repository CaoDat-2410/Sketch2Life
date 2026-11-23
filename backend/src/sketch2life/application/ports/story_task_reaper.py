"""Story-owned port of the lost-background-task reaper (FEAT-066 T-2d-fix; SRS l.394, l.615).

The Parent story work (the drawing analysis, the speech transcription and the story rewrite) runs
in ``BackgroundTasks`` runners, not in ``ai_jobs``: a worker that dies leaves the run in
``INPUT_PROCESSING``/``SCRIPT_GENERATING`` for ever. The reaper is a system job: it has no
principal, no request key and no route. Its listings select run ids and clocks only (no content
column); the locked read of one run loads its row but nothing from it reaches a log or an audit
row; the report holds counts. Nothing schedules it yet (the periodic runner slice owns that).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Final, Protocol

# SRS l.394, l.615 (FR-O-10): the one AI job deadline the SRS licenses (l.988 and l.503 are the
# separate video generation deadline). A shorter lease for a
# QUEUED/RUNNING job has no SRS number (FR-O-06 l.611: per stage, needs a benchmark), so the caller
# of the reaper chooses it and this is the upper bound.
AI_JOB_DEADLINE: Final = timedelta(hours=6)

# Technical attempts of one rewrite slot (T-2d-fix D2, OPEN Q1 reading B): a failed attempt does not
# consume a slot, at most this many attempts per slot, so at most 9 rewrite generations per run.
REWRITE_ATTEMPTS_PER_SLOT: Final = 3

# The existing safe code for a step that took too long (``ai_jobs``, ``learning_media``). It is not
# in the synchronous SRS table l.847-873 (asynchronous codes are safe codes on the job, l.875).
TASK_TIMEOUT_CODE: Final = "PROVIDER_TIMEOUT"

# Metadata audit rows (BR-34 l.278: actor, action, resource, result; no child data, no text).
REAPER_ACTOR_REF: Final = "system:story-task-reaper"
AUDIT_REWRITE_ATTEMPT_FAILED: Final = "STORY_REWRITE_ATTEMPT_FAILED"
AUDIT_TIMED_OUT_DRAWING: Final = "STORY_TASK_TIMED_OUT_DRAWING"
AUDIT_TIMED_OUT_TRANSCRIPT: Final = "STORY_TASK_TIMED_OUT_TRANSCRIPT"
AUDIT_TIMED_OUT_STORY: Final = "STORY_TASK_TIMED_OUT_STORY"


class ReapKind(StrEnum):
    DRAWING_LOST = "DRAWING_LOST"  # K1: INPUT_PROCESSING, drawing job QUEUED/RUNNING
    DRAWING_UNKNOWN = "DRAWING_UNKNOWN"  # K2: the same, job AWAITING_RECONCILIATION
    TRANSCRIPT_LOST = "TRANSCRIPT_LOST"  # K3: a transcript PENDING in INPUT_PROCESSING
    STORY_LOST = "STORY_LOST"  # K4: SCRIPT_GENERATING, QUEUED/RUNNING
    STORY_UNKNOWN = "STORY_UNKNOWN"  # K5: SCRIPT_GENERATION_UNKNOWN


class ReapOutcome(StrEnum):
    DRAWING_TIMED_OUT = "DRAWING_TIMED_OUT"
    TRANSCRIPT_TIMED_OUT = "TRANSCRIPT_TIMED_OUT"
    REWRITE_RECOVERED = "REWRITE_RECOVERED"
    STORY_FAILED = "STORY_FAILED"
    # Nothing was written: locked by a live command, changed, a lite-lane run, or not yet due.
    SKIPPED = "SKIPPED"


@dataclass(frozen=True, slots=True)
class ReapCandidate:
    """A run that looked stuck when it was listed; the store re-checks it under the run lock."""

    run_id: str
    kind: ReapKind


@dataclass(frozen=True, slots=True)
class ReapReport:
    drawing_timed_out: int = 0
    transcript_timed_out: int = 0
    rewrite_recovered: int = 0
    story_failed: int = 0
    skipped: int = 0
    errors: int = 0


class StoryTaskReaperStore(Protocol):
    def list_candidates(self, kind: ReapKind, cutoff: datetime, limit: int) -> list[ReapCandidate]:
        """Bounded, ordered, read-only prefilter: opaque ids, no content column."""
        ...

    def reap(self, candidate: ReapCandidate, now: datetime, cutoff: datetime) -> ReapOutcome:
        """One transaction: lock the run (``SKIP LOCKED``), re-check, compare-and-set the effect."""
        ...


__all__ = [
    "AI_JOB_DEADLINE",
    "AUDIT_REWRITE_ATTEMPT_FAILED",
    "AUDIT_TIMED_OUT_DRAWING",
    "AUDIT_TIMED_OUT_STORY",
    "AUDIT_TIMED_OUT_TRANSCRIPT",
    "REAPER_ACTOR_REF",
    "REWRITE_ATTEMPTS_PER_SLOT",
    "TASK_TIMEOUT_CODE",
    "ReapCandidate",
    "ReapKind",
    "ReapOutcome",
    "ReapReport",
    "StoryTaskReaperStore",
]
