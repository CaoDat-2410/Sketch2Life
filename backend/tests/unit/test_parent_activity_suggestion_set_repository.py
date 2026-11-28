from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy.sql.dml import Delete, Insert, Update

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_activity_suggestion_sets import (
    ActivitySuggestionSetReservation,
)
from sketch2life.application.ports.parent_story_runs import (
    ParentActivityContext,
    ParentStoryRunError,
)
from sketch2life.infrastructure.persistence.parent_activity_suggestion_set_repository import (
    PENDING_ACTIVITY_SET_RECEIPT_TIMEOUT,
    SqlParentActivitySuggestionSetRepository,
    _snapshot_hash,
)

_PRINCIPAL = VerifiedPrincipal("parent-subject", "test-issuer", frozenset())
_RUN_ID = "55555555-5555-4555-8555-555555555555"
_SET_ID = "66666666-6666-4666-8666-666666666666"
_RECEIPT_ID = "77777777-7777-4777-8777-777777777777"


class _Result:
    def __init__(
        self,
        *,
        row: dict[str, Any] | None = None,
        scalar_rows: list[Any] | None = None,
        rowcount: int = 1,
    ) -> None:
        self._row = row
        self._scalar_rows = scalar_rows or []
        self.rowcount = rowcount

    def mappings(self) -> _Result:
        return self

    def one_or_none(self) -> dict[str, Any] | None:
        return self._row

    def scalars(self) -> _Result:
        return self

    def all(self) -> list[Any]:
        return self._scalar_rows


class _Session:
    def __init__(self, *, set_row: dict[str, Any] | None = None) -> None:
        self.set_row = set_row
        self.statements: list[Any] = []
        self.commits = 0
        self.rollbacks = 0

    def execute(self, statement: Any) -> _Result:
        self.statements.append(statement)
        if isinstance(statement, (Update, Delete, Insert)):
            return _Result(rowcount=1)
        froms = statement.get_final_froms()
        table_name = froms[0].name if froms else ""
        if table_name == "activity_suggestion_sets":
            if len(statement.selected_columns) == 1:
                return _Result(scalar_rows=[])
            return _Result(row=self.set_row)
        return _Result()

    def scalar(self, _statement: Any) -> int:
        return 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


class _Repository(SqlParentActivitySuggestionSetRepository):
    def __init__(
        self,
        session: _Session,
        *,
        run: dict[str, Any] | None = None,
        receipt: dict[str, Any] | None = None,
        context: ParentActivityContext | None = None,
    ) -> None:
        super().__init__(session)  # type: ignore[arg-type]
        self.run = run or {
            "run_id": _RUN_ID,
            "run_state": "PREPARATION_REVIEW",
            "understanding_revision": 7,
            "version": 4,
            "revision": 4,
        }
        self.receipt = receipt
        self.context = context or ParentActivityContext(
            run_id=_RUN_ID,
            run_revision=4,
            understanding_revision=7,
            context_snapshot={"age_months": 84, "topic": "shapes"},
            subject_label="shapes",
            visible_features=["round outline"],
            lesson_pin_snapshot=None,
        )
        self.find_calls = 0
        self.stored_pending_calls = 0

    def _owned_run(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return self.run

    def _lock_idempotency(self, **_kwargs: Any) -> None:
        return None

    def _find_idempotency_receipt(self, **_kwargs: Any) -> dict[str, Any] | None:
        self.find_calls += 1
        return self.receipt

    def _activity_context(
        self, _principal: VerifiedPrincipal, _run: dict[str, Any]
    ) -> ParentActivityContext:
        return self.context

    def _current_input(self, _run: dict[str, Any]) -> dict[str, int]:
        return {"input_revision": 2, "context_revision": 3}

    def _store_pending_idempotency_receipt(self, **_kwargs: Any) -> str:
        self.stored_pending_calls += 1
        return "new-pending-receipt"


def _set_row(activities: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "suggestion_set_id": _SET_ID,
        "run_id": _RUN_ID,
        "set_revision": 2,
        "understanding_revision": 7,
        "selection_mode": "AI_GENERATED_FALLBACK",
        "catalog_candidate_count": 1,
        "activities_snapshot": activities,
        "activities_snapshot_sha256": _snapshot_hash(activities),
        "provider_call_id": "call-1",
    }


def _draft() -> dict[str, Any]:
    return {
        "title": "Observe a shape",
        "objective": "Notice one detail.",
        "materials_text": "Paper.",
        "preparation_text": "An adult prepares a clear space.",
        "instructions_text": (
            "Outside, the child chooses one shape to observe with an adult nearby."
        ),
        "observation_notes": "Record the detail the child notices.",
        "safety_notes": "Stay with an adult.",
        "activity_kind": "outdoor",
        "source": "AI_GENERATED_DRAFT",
        "source_lesson_id": None,
        "source_lesson_title": None,
        "source_lesson_version_id": None,
        "source_content_sha256": None,
        "source_activity_index": None,
        "match_reason": None,
    }


def test_repository_rebuilds_replay_body_from_set_row_and_hash() -> None:
    activities = [_draft()]
    row = _set_row(activities)
    receipt = {
        "receipt_id": _RECEIPT_ID,
        "state": "FINAL",
        "response_status": 200,
        "response_body": {
            "suggestion_set_id": _SET_ID,
            "set_revision": 2,
            "activities_snapshot_sha256": row["activities_snapshot_sha256"],
        },
    }
    session = _Session(set_row=row)
    repository = _Repository(session, receipt=receipt)

    reservation = repository.reserve_activity_suggestion_set(
        principal=_PRINCIPAL,
        run_id=_RUN_ID,
        expected_understanding_revision=7,
        idempotency_key="replay-key",
    )

    assert reservation.replayed
    assert reservation.replay_body is not None
    assert reservation.replay_body["activities"] == activities
    assert reservation.replay_body["activities_snapshot_sha256"] == row[
        "activities_snapshot_sha256"
    ]
    assert "request_id" not in reservation.replay_body
    assert "activities" not in receipt["response_body"]


def test_repository_refuses_a_purged_run_before_looking_up_replay() -> None:
    receipt = {
        "receipt_id": _RECEIPT_ID,
        "state": "FINAL",
        "response_status": 200,
        "response_body": {"suggestion_set_id": _SET_ID, "set_revision": 2},
    }
    repository = _Repository(
        _Session(),
        run={
            "run_id": _RUN_ID,
            "run_state": "DELETE_PENDING",
            "understanding_revision": 7,
            "version": 4,
            "revision": 4,
        },
        receipt=receipt,
    )

    with pytest.raises(ParentStoryRunError, match="INVALID_STATE_TRANSITION") as caught:
        repository.reserve_activity_suggestion_set(
            principal=_PRINCIPAL,
            run_id=_RUN_ID,
            expected_understanding_revision=7,
            idempotency_key="replay-key",
        )

    assert caught.value.status_code == 409
    assert repository.find_calls == 0


def test_repository_replay_preserves_current_version_for_stale_conflicts() -> None:
    repository = _Repository(
        _Session(),
        receipt={
            "receipt_id": _RECEIPT_ID,
            "state": "FINAL",
            "response_status": 409,
            "response_body": {
                "error_code": "STALE_REVISION",
                "request_id": "old-request",
                "current_version": 8,
            },
        },
    )

    with pytest.raises(ParentStoryRunError, match="STALE_REVISION") as caught:
        repository.reserve_activity_suggestion_set(
            principal=_PRINCIPAL,
            run_id=_RUN_ID,
            expected_understanding_revision=7,
            idempotency_key="stale-key",
        )

    assert caught.value.current_version == 8


def test_repository_retries_an_orphan_pending_receipt_after_fake_clock_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    now = datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
    receipt = {
        "receipt_id": _RECEIPT_ID,
        "state": "PENDING",
        "created_at": now - PENDING_ACTIVITY_SET_RECEIPT_TIMEOUT - timedelta(seconds=1),
        "response_body": None,
    }
    session = _Session()
    repository = _Repository(session, receipt=receipt)
    monkeypatch.setattr(repository, "_now", lambda: now)

    reservation = repository.reserve_activity_suggestion_set(
        principal=_PRINCIPAL,
        run_id=_RUN_ID,
        expected_understanding_revision=7,
        idempotency_key="orphan-key",
    )

    assert not reservation.replayed
    assert reservation.receipt_id == _RECEIPT_ID
    assert repository.stored_pending_calls == 0
    assert isinstance(session.statements[0], Update)
    reclaimed_values = session.statements[0].compile().params
    assert reclaimed_values["created_at"] == now
    assert session.commits == 1


def test_owner_scoped_repository_lookup_returns_uniform_404_for_unknown_or_foreign_run() -> None:
    repository = SqlParentActivitySuggestionSetRepository(_Session())  # type: ignore[arg-type]

    with pytest.raises(ParentStoryRunError, match="RESOURCE_NOT_FOUND") as caught:
        repository.reserve_activity_suggestion_set(
            principal=_PRINCIPAL,
            run_id=_RUN_ID,
            expected_understanding_revision=7,
            idempotency_key="owner-404-key",
        )

    assert caught.value.status_code == 404


def test_repository_complete_stores_only_set_reference_revision_and_hash_in_receipt() -> None:
    activity = _draft()
    context = ParentActivityContext(
        run_id=_RUN_ID,
        run_revision=4,
        understanding_revision=7,
        context_snapshot={"age_months": 84, "topic": "shapes"},
        subject_label="shapes",
        visible_features=["round outline"],
        lesson_pin_snapshot=None,
    )
    session = _Session()
    repository = _Repository(session, context=context)
    reservation = ActivitySuggestionSetReservation(
        receipt_id=_RECEIPT_ID,
        suggestion_set_id=_SET_ID,
        set_revision=2,
        context=context,
        input_revision=2,
        context_revision=3,
    )

    repository.complete_activity_suggestion_set(
        principal=_PRINCIPAL,
        reservation=reservation,
        response={
            "selection_mode": "AI_GENERATED_FALLBACK",
            "catalog_candidate_count": 0,
            "activities": [activity],
        },
        provider_call_id="call-1",
    )

    insert_statement = next(
        statement for statement in session.statements if isinstance(statement, Insert)
    )
    receipt_update = next(
        statement
        for statement in session.statements
        if isinstance(statement, Update) and statement.table.name == "command_receipts"
    )
    assert insert_statement.table.name == "activity_suggestion_sets"
    response_body = receipt_update.compile().params["response_body"]
    assert response_body == {
        "suggestion_set_id": _SET_ID,
        "set_revision": 1,
        "activities_snapshot_sha256": _snapshot_hash([activity]),
    }
    assert "activities" not in response_body


def test_transient_failure_deletes_pending_receipt_but_deterministic_conflict_is_cached() -> None:
    reservation = ActivitySuggestionSetReservation(
        receipt_id=_RECEIPT_ID,
        suggestion_set_id=_SET_ID,
        set_revision=1,
    )
    transient_session = _Session()
    transient_repo = SqlParentActivitySuggestionSetRepository(transient_session)  # type: ignore[arg-type]
    transient_repo.fail_activity_suggestion_set(
        principal=_PRINCIPAL,
        reservation=reservation,
        error_code="MODAL_AI_NOT_ENABLED",
        response_status=503,
        request_id="request-transient",
    )
    assert isinstance(transient_session.statements[0], Delete)

    conflict_session = _Session()
    conflict_repo = SqlParentActivitySuggestionSetRepository(conflict_session)  # type: ignore[arg-type]
    conflict_repo.fail_activity_suggestion_set(
        principal=_PRINCIPAL,
        reservation=reservation,
        error_code="STALE_REVISION",
        response_status=409,
        request_id="request-conflict",
        cache_failure=True,
        current_version=8,
    )
    assert isinstance(conflict_session.statements[0], Update)
    response_body = conflict_session.statements[0].compile().params["response_body"]
    assert response_body["error_code"] == "STALE_REVISION"
    assert response_body["current_version"] == 8

    gate_session = _Session()
    gate_repo = SqlParentActivitySuggestionSetRepository(gate_session)  # type: ignore[arg-type]
    gate_repo.fail_activity_suggestion_set(
        principal=_PRINCIPAL,
        reservation=reservation,
        error_code="MODAL_OUTPUT_CONTRACT_INVALID",
        response_status=502,
        request_id="request-gate",
        cache_failure=True,
    )
    assert isinstance(gate_session.statements[0], Update)
    gate_body = gate_session.statements[0].compile().params["response_body"]
    assert gate_body["error_code"] == "MODAL_OUTPUT_CONTRACT_INVALID"
