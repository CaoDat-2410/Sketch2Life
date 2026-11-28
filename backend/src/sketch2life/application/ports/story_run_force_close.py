"""Application boundary for the Manager StoryRun force-close command."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sketch2life.domain.teacher_run_force_close import StoryRunForceCloseReceiptIdentity


@dataclass(frozen=True, slots=True)
class ManagerStoryRunConflict:
    run_id: str
    run_state: str
    revision: int


@dataclass(frozen=True, slots=True)
class ManagerStoryRunForceClosed:
    run_id: str
    revision: int


class ManagerStoryRunForceCloseFailure(RuntimeError):
    def __init__(
        self,
        status_code: int,
        code: str,
        *,
        current_version: int | None = None,
    ) -> None:
        super().__init__(code)
        self.status_code = status_code
        self.code = code
        self.current_version = current_version


class StoryRunForceCloseRepository(Protocol):
    def find_active_conflict(
        self, *, organization_id: str, teacher_ref: str
    ) -> ManagerStoryRunConflict | None: ...

    def force_close(
        self,
        *,
        organization_id: str,
        run_id: str,
        expected_revision: int,
        identity: StoryRunForceCloseReceiptIdentity,
        audit_actor_ref: str,
    ) -> ManagerStoryRunForceClosed: ...


__all__ = [
    "ManagerStoryRunConflict",
    "ManagerStoryRunForceClosed",
    "ManagerStoryRunForceCloseFailure",
    "StoryRunForceCloseRepository",
]
