from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from sketch2life.application.ports.story_task_reaper import ReapKind, ReapOutcome
from sketch2life.infrastructure.persistence import story_task_reaper_store
from sketch2life.infrastructure.persistence.story_task_reaper_store import (
    SqlStoryTaskReaperStore,
)


class _Result:
    def __init__(self, row: Any = None, *, rowcount: int = 1) -> None:
        self._row = row
        self.rowcount = rowcount

    def one_or_none(self) -> Any:
        return self._row


class _Session:
    def __init__(self, latest_revision: tuple[str, int, str]) -> None:
        self.latest_revision = latest_revision
        self.execute_calls: list[Any] = []
        self.scalar_calls: list[Any] = []

    def execute(self, statement: Any) -> _Result:
        self.execute_calls.append(statement)
        if len(self.execute_calls) == 1:
            return _Result(self.latest_revision)
        return _Result(rowcount=1)

    def scalar(self, statement: Any) -> str:
        self.scalar_calls.append(statement)
        return "FAILED"


@pytest.mark.parametrize(
    ("kind", "job_state", "revision_status"),
    [
        (ReapKind.STORY_LOST, "QUEUED", "GENERATING"),
        (
            ReapKind.STORY_UNKNOWN,
            "AWAITING_RECONCILIATION",
            "AWAITING_RECONCILIATION",
        ),
    ],
    ids=["lost-recovery", "unknown-recovery"],
)
def test_failed_first_story_recovery_uses_terminal_reaper_path(
    monkeypatch: pytest.MonkeyPatch,
    kind: ReapKind,
    job_state: str,
    revision_status: str,
) -> None:
    now = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
    session = _Session(("revision-2", 2, revision_status))
    store = SqlStoryTaskReaperStore(session)  # type: ignore[arg-type]
    store._audit = lambda *_args, **_kwargs: None  # type: ignore[method-assign]
    monkeypatch.setattr(
        story_task_reaper_store.SqlParentStoryRunRepository,
        "recover_failed_rewrite",
        lambda *_args, **_kwargs: pytest.fail(
            "a recovery whose first story failed must not return to review"
        ),
    )
    run = {
        "run_id": "run-ref",
        "actor_scope_kind": "PARENT_ACCOUNT",
        "actor_scope_ref": "owner-scope-ref",
        "run_state": (
            "SCRIPT_GENERATION_UNKNOWN"
            if kind is ReapKind.STORY_UNKNOWN
            else "SCRIPT_GENERATING"
        ),
        "job_state": job_state,
        "version": 10,
        "revision": 12,
        "updated_at": now - timedelta(hours=7),
    }

    outcome = store._reap_story(run, kind, now, now)

    assert outcome is ReapOutcome.STORY_FAILED
    assert len(session.scalar_calls) == 1
    assert len(session.execute_calls) == 4
