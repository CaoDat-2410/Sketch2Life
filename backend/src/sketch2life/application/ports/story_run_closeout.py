"""Story-owned port of the adult-wait closeout sweep (FEAT-066 T-1d1; SRS l.394-395, l.503).

The sweep is a system job: it has no principal, no request key and no route. It reads run rows
only by owner scope kind, never a content column, and it returns counts and opaque ids.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from sketch2life.application.ports.story_video import ProgressEvent, ProgressResult


class CloseoutOutcome(StrEnum):
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"
    # Nothing was written: the row is locked by a live command, changed, or is no longer idle.
    SKIPPED = "SKIPPED"


@dataclass(frozen=True, slots=True)
class IdleCandidate:
    """A run that looked idle when it was listed; the store re-checks it under the run lock."""

    run_id: str
    run_state: str


@dataclass(frozen=True, slots=True)
class OverdueGeneration:
    """An accepted generation past ``accepted_at`` + 6 h that has not settled."""

    generation_id: str
    state: str


@dataclass(frozen=True, slots=True)
class CloseoutReport:
    completed: int = 0
    abandoned: int = 0
    deadline_failed: int = 0
    skipped: int = 0
    errors: int = 0


class StoryRunCloseoutStore(Protocol):
    def overdue_generations(self, now: datetime, limit: int) -> list[OverdueGeneration]: ...

    def idle_candidates(self, now: datetime, limit: int) -> list[IdleCandidate]: ...

    def close_idle(self, run_id: str, now: datetime) -> CloseoutOutcome:
        """One transaction: lock the run (``SKIP LOCKED``), re-check, compare-and-set the close."""
        ...


class GenerationProgress(Protocol):
    """The T-1a progress service seen from the sweep: one compare-and-set step plus the settle."""

    def apply(self, generation_id: str, event: ProgressEvent) -> ProgressResult: ...


__all__ = [
    "CloseoutOutcome",
    "CloseoutReport",
    "GenerationProgress",
    "IdleCandidate",
    "OverdueGeneration",
    "StoryRunCloseoutStore",
]
