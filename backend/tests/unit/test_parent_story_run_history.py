from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from sketch2life.application.services.parent_story_runs import (
    ParentStoryRunService,
    ParentStoryRunServiceError,
)


class _HistoryRepository:
    def __init__(self, rows):
        self.rows = rows
        self.kwargs = None

    def list_runs(self, **kwargs):
        self.kwargs = kwargs
        return self.rows[: kwargs["limit"]]


def _record(run_id: str, created_at: datetime):
    return SimpleNamespace(run_id=run_id, created_at=created_at)


def test_history_uses_owner_scoped_page_and_returns_opaque_next_cursor():
    now = datetime.now(UTC)
    rows = [
        _record("00000000-0000-0000-0000-000000000003", now),
        _record("00000000-0000-0000-0000-000000000002", now - timedelta(seconds=1)),
        _record("00000000-0000-0000-0000-000000000001", now - timedelta(seconds=2)),
    ]
    repository = _HistoryRepository(rows)
    service = ParentStoryRunService(repository)

    page, cursor = service.list_runs(
        owner_subject="parent-emulator-uid",
        policy_version="local-policy-v1",
        limit=2,
        profile_id="profile-owned-by-parent",
    )

    assert [row.run_id for row in page] == [rows[0].run_id, rows[1].run_id]
    assert cursor
    assert repository.kwargs["owner_subject"] == "parent-emulator-uid"
    assert repository.kwargs["profile_id"] == "profile-owned-by-parent"
    assert repository.kwargs["limit"] == 3
    cursor_time, cursor_run_id = service._decode_history_cursor(cursor)
    assert cursor_time == rows[1].created_at
    assert cursor_run_id == rows[1].run_id


def test_history_cursor_is_rejected_when_malformed():
    with pytest.raises(ParentStoryRunServiceError) as error:
        ParentStoryRunService._decode_history_cursor("not-a-valid-cursor")

    assert error.value.status_code == 422
    assert error.value.code == "PARENT_STORY_HISTORY_CURSOR_INVALID"


def test_history_page_has_no_cursor_when_results_fit_one_page():
    repository = _HistoryRepository(
        [_record("00000000-0000-0000-0000-000000000001", datetime.now(UTC))]
    )
    rows, cursor = ParentStoryRunService(repository).list_runs(
        owner_subject="parent-emulator-uid",
        policy_version="local-policy-v1",
        limit=20,
    )

    assert len(rows) == 1
    assert cursor is None
