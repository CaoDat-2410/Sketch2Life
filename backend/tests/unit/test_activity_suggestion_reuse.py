"""FEAT-094: an app that was reopened asks for the suggestions it already has instead of a second set."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest

from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.contracts.schemas.parent_activity_selection import ParentActivitySuggestionsRequestV1
from sketch2life.infrastructure.persistence.parent_story_repository import SqlParentStoryRunRepository

NOW = datetime.now(UTC)
BODY = {"suggestion_set_id": "set-1", "set_revision": 1}


def _receipt(state: str, body: Any, age: timedelta = timedelta(seconds=20)) -> dict[str, Any]:
    return {"receipt_id": "receipt-1", "state": state, "response_body": body, "created_at": NOW - age}


class _Repository(SqlParentStoryRunRepository):
    """The reservation flow with the database reads replaced; ``stored`` is newest first."""

    def __init__(self, stored: list[dict[str, Any]]) -> None:
        super().__init__(SimpleNamespace(commit=lambda: None))
        self.stored = stored

    def _owned_run(self, *_args: Any, **_options: Any) -> dict[str, Any]:
        return {"current_input_revision": 1, "run_state": "PREPARATION_REVIEW"}

    def _require_activity_state(self, _run: Any) -> None:
        return None

    def _activity_context(self, *_args: Any) -> Any:
        return SimpleNamespace(
            understanding_revision=2, context_snapshot={}, subject_label="con gà", visible_features=[],
            lesson_pin_snapshot=None,
        )

    def _current_input(self, _run: Any) -> dict[str, Any]:
        return {"original_sha256": "a" * 64, "context_revision": 1}

    def _lock_idempotency(self, **_options: Any) -> None:
        return None

    def _find_idempotency_receipt(self, **_options: Any) -> None:
        return None

    def _suggestion_receipts(self, **_options: Any) -> list[dict[str, Any]]:
        return self.stored


def _reserve(stored: list[dict[str, Any]], **options: Any) -> Any:
    return _Repository(stored).reserve_activity_suggestion_set(
        principal=SimpleNamespace(subject="adult"), run_id="run-1", expected_understanding_revision=2,
        idempotency_key="a-new-key", **options,
    )


def test_the_reuse_flag_is_optional_and_off() -> None:
    assert ParentActivitySuggestionsRequestV1(expected_understanding_revision=1).reuse_latest is False


def test_a_reopened_app_gets_the_newest_finished_set() -> None:
    failed = _receipt("COMPLETED", {"error_code": "PARENT_ACTIVITY_RESPONSE_INVALID"})

    reservation = _reserve([failed, _receipt("COMPLETED", BODY)], reuse_latest=True)

    assert reservation.replayed and reservation.replay_body == BODY and reservation.suggestion_set_id == "set-1"


def test_a_reopened_app_waits_for_the_set_still_being_written() -> None:
    with pytest.raises(ParentStoryRunError) as error:
        _reserve([_receipt("PENDING", None), _receipt("COMPLETED", BODY)], reuse_latest=True)

    assert error.value.code == "PARENT_ACTIVITY_SUGGESTION_IN_PROGRESS"


def test_an_abandoned_request_does_not_block_the_run_forever() -> None:
    stale = _receipt("PENDING", None, timedelta(hours=2))

    reservation = _reserve([stale, _receipt("COMPLETED", BODY)], reuse_latest=True)

    assert reservation.replay_body == BODY
