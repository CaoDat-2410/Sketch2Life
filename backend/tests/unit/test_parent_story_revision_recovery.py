from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.infrastructure.persistence import parent_story_repository as repository_module
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)

_PRINCIPAL = VerifiedPrincipal("parent-user", "firebase", frozenset({"parent"}))
_RUN_ID = "22222222-2222-4222-8222-222222222222"
_ACCOUNT_ID = "parent-account-1"
_SOURCE_HASH = "a" * 64
_ACTIVITY_ID = "33333333-3333-4333-8333-333333333333"


class _Result:
    def __init__(self, *, rows: list[dict[str, Any]] | None = None, rowcount: int = 1) -> None:
        self._rows = rows or []
        self.rowcount = rowcount

    def mappings(self) -> _Result:
        return self

    def all(self) -> list[dict[str, Any]]:
        return self._rows


class _Session:
    def __init__(self, *, latest_story: dict[str, Any], active_run_id: str | None = None) -> None:
        self.latest_story = latest_story
        self.active_run_id = active_run_id
        self.statements: list[Any] = []
        self.scalar_queries: list[str] = []
        self.commits = 0
        self.rollbacks = 0
        self.raise_active_lock_conflict = False

    def execute(self, statement: Any, *_args: Any, **_kwargs: Any) -> _Result:
        self.statements.append(statement)
        if getattr(statement, "is_select", False):
            sql = str(statement.compile(dialect=postgresql.dialect()))
            if "story_revisions" in sql:
                return _Result(rows=[self.latest_story])
            raise AssertionError(f"unexpected read query: {sql}")
        table = getattr(getattr(statement, "table", None), "name", "")
        if (
            self.raise_active_lock_conflict
            and getattr(statement, "is_update", False)
            and table == "runs"
        ):
            original = SimpleNamespace(
                diag=SimpleNamespace(constraint_name="uq_story_run_active_parent")
            )
            raise IntegrityError("statement", {}, original)
        return _Result()

    def scalar(self, statement: Any, *_args: Any, **_kwargs: Any) -> Any:
        sql = str(statement.compile(dialect=postgresql.dialect()))
        self.scalar_queries.append(sql)
        if "active_owner_parent_account_id" in sql:
            return self.active_run_id
        if "review_decisions" in sql:
            return "confirmed-subject-decision"
        raise AssertionError(f"unexpected scalar query: {sql}")

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


def _run(**overrides: Any) -> dict[str, Any]:
    return {
        "run_id": _RUN_ID,
        "run_state": "FAILED",
        "error_code": "STORY_OUTPUT_INVALID",
        "job_state": "FAILED",
        "retryable": False,
        "understanding_revision": 1,
        "subject_label": "con rùa",
        "version": 8,
        "revision": 7,
        "current_input_revision": 2,
        "active_owner_parent_account_id": None,
        **overrides,
    }


def _latest_story(**overrides: Any) -> dict[str, Any]:
    return {
        "story_revision_id": "44444444-4444-4444-8444-444444444444",
        "revision_no": 1,
        "status": "FAILED",
        "source_asset_sha256": _SOURCE_HASH,
        "context_revision": 1,
        "understanding_revision": 1,
        "activity_selection_id": _ACTIVITY_ID,
        **overrides,
    }


def _repository(
    monkeypatch: pytest.MonkeyPatch,
    *,
    run: dict[str, Any] | None = None,
    latest_story: dict[str, Any] | None = None,
    active_run_id: str | None = None,
) -> tuple[SqlParentStoryRunRepository, _Session]:
    session = _Session(
        latest_story=latest_story or _latest_story(),
        active_run_id=active_run_id,
    )
    repository = SqlParentStoryRunRepository(session)  # type: ignore[arg-type]
    monkeypatch.setattr(repository, "_owned_run", lambda *_args, **_kwargs: dict(run or _run()))
    monkeypatch.setattr(repository, "_lock_idempotency", lambda **_kwargs: None)
    monkeypatch.setattr(repository, "_find_idempotency_receipt", lambda **_kwargs: None)
    monkeypatch.setattr(
        repository,
        "_store_pending_idempotency_receipt",
        lambda **_kwargs: "receipt-1",
    )
    monkeypatch.setattr(
        repository,
        "_latest_activity_selection",
        lambda **_kwargs: {
            "actor_scope_ref": repository_module._principal_scope_ref(_PRINCIPAL),
            "activity_selection_id": _ACTIVITY_ID,
            "activity_snapshot_sha256": "b" * 64,
            "activity_snapshot": {"title": "Quan sát mai rùa"},
        },
    )
    monkeypatch.setattr(
        repository,
        "_latest_understanding",
        lambda _run_id: {
            "revision_no": 1,
            "result_snapshot": {"result": {"visible_features": ["mai tròn", "bốn chân"]}},
        },
    )
    monkeypatch.setattr(
        repository,
        "_current_input",
        lambda _run: {
            "context_confirmed_by": "adult-1",
            "context_confirmed_at": datetime.now(UTC),
            "original_sha256": _SOURCE_HASH,
            "context_snapshot": {"age_months": 72, "topic": "Thiên nhiên"},
            "context_revision": 1,
            "typed_idea": "đi chậm trong vườn",
            "lesson_pin_snapshot": {
                "schema_version": "sketch2life.parent-lesson-pin.v1",
                "subject_learning_notes": "Rùa có mai bảo vệ cơ thể và di chuyển bằng bốn chân.",
                "script_direction": "Kể chuyện khám phá khu vườn.",
                "script_following_allowed": True,
            },
        },
    )
    return repository, session


def _reserve(repository: SqlParentStoryRunRepository, **overrides: Any) -> Any:
    args: dict[str, Any] = {
        "principal": _PRINCIPAL,
        "account_id": _ACCOUNT_ID,
        "run_id": _RUN_ID,
        "expected_understanding_revision": 1,
        "rewrite_instruction": "Viết câu ngắn và hoàn chỉnh.",
        "idempotency_key": "fresh-adult-rewrite-key",
        "story_revision_id": "55555555-5555-4555-8555-555555555555",
        "model_id": "qwen-test",
        "model_revision": "rev-test",
        "prompt_version": "prompt-test",
    }
    args.update(overrides)
    return repository.reserve_story_revision(**args)


def test_quality_rejected_story_rewrite_is_reserved_on_same_run_and_reacquires_owner_lock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, session = _repository(monkeypatch)

    reservation = _reserve(repository)

    assert reservation.run_id == _RUN_ID
    assert reservation.revision_no == 2
    assert reservation.worker_input["rewrite_instruction"] == "Viết câu ngắn và hoàn chỉnh."
    assert reservation.worker_input["schema_version"] == "sketch2life.story-generation-input.v3"
    assert reservation.worker_input["topic"] == "Thiên nhiên"
    assert reservation.worker_input["lesson_subject_learning_notes"].startswith("Rùa có mai")
    assert reservation.worker_input["lesson_direction"] == "Kể chuyện khám phá khu vườn."
    assert "interests_summary" not in reservation.worker_input
    assert session.commits == 1
    assert session.rollbacks == 0
    assert any("active_owner_parent_account_id" in query for query in session.scalar_queries)
    inserts = [
        statement
        for statement in session.statements
        if getattr(statement, "is_insert", False)
    ]
    assert len(inserts) == 1
    revision_values = inserts[0].compile(dialect=postgresql.dialect()).params
    assert revision_values["status"] == "GENERATING"
    assert revision_values["revision_no"] == 2
    run_updates = [
        statement for statement in session.statements
        if getattr(statement, "is_update", False)
        and getattr(getattr(statement, "table", None), "name", "") == "runs"
    ]
    assert len(run_updates) == 1
    update_values = run_updates[0].compile(dialect=postgresql.dialect()).params
    assert _ACCOUNT_ID in update_values.values()
    assert update_values["run_state"] == "SCRIPT_GENERATING"


def test_story_request_omits_pinned_script_direction_when_lesson_disallows_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, _session = _repository(monkeypatch)
    current_input = repository._current_input

    def _without_script_permission(run: dict[str, Any]) -> dict[str, Any]:
        result = current_input(run)
        result["lesson_pin_snapshot"]["script_following_allowed"] = False
        return result

    monkeypatch.setattr(repository, "_current_input", _without_script_permission)

    reservation = _reserve(repository)

    assert reservation.worker_input["lesson_subject_learning_notes"]
    assert reservation.worker_input["lesson_direction"] is None


@pytest.mark.parametrize(
    "overrides",
    (
        {"error_code": "MODAL_EXECUTION_FAILED"},
        {"job_state": "AWAITING_RECONCILIATION"},
        {"retryable": True},
        {"run_state": "SCRIPT_GENERATION_UNKNOWN"},
    ),
)
def test_other_failed_or_unknown_outcomes_remain_terminal(
    monkeypatch: pytest.MonkeyPatch, overrides: dict[str, Any]
) -> None:
    repository, session = _repository(monkeypatch, run=_run(**overrides))

    with pytest.raises(ParentStoryRunError) as error:
        _reserve(repository)

    assert error.value.code == "PARENT_STORY_RUN_NOT_READY_FOR_SCRIPT"
    assert not [
        statement
        for statement in session.statements
        if getattr(statement, "is_insert", False)
    ]


def test_recovery_requires_an_adult_instruction_and_matching_failed_revision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, session = _repository(monkeypatch)

    with pytest.raises(ParentStoryRunError) as missing_instruction:
        _reserve(repository, rewrite_instruction=None)
    assert missing_instruction.value.code == "PARENT_STORY_REWRITE_NOT_ALLOWED"

    repository, session = _repository(
        monkeypatch,
        latest_story=_latest_story(source_asset_sha256="c" * 64),
    )
    with pytest.raises(ParentStoryRunError) as stale_revision:
        _reserve(repository)
    assert stale_revision.value.code == "PARENT_STORY_REWRITE_NOT_ALLOWED"
    assert session.commits == 0


def test_recovery_refuses_when_another_run_holds_the_parent_lock_before_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, session = _repository(monkeypatch, active_run_id="other-active-run")

    with pytest.raises(ParentStoryRunError) as conflict:
        _reserve(repository)

    assert conflict.value.status_code == 409
    assert conflict.value.code == "ACTIVE_RUN_EXISTS"
    assert session.commits == 0
    assert not [
        statement
        for statement in session.statements
        if getattr(statement, "is_insert", False)
    ]


def test_partial_unique_index_race_maps_to_active_run_conflict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, session = _repository(monkeypatch)
    session.raise_active_lock_conflict = True

    with pytest.raises(ParentStoryRunError) as conflict:
        _reserve(repository)

    assert conflict.value.status_code == 409
    assert conflict.value.code == "ACTIVE_RUN_EXISTS"
    assert session.commits == 0
    assert session.rollbacks == 1
