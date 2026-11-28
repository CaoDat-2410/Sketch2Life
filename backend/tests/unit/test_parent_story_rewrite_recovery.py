from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy.sql.dml import Insert, Update

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryRevisionReservation,
    ParentStoryRunError,
)
from sketch2life.infrastructure.persistence import parent_story_repository
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
    _parent_first_story_request_sha256,
    _sha256_json,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables


class _MappingsResult:
    def __init__(self, rows: list[dict[str, Any]], *, rowcount: int = 1) -> None:
        self._rows = rows
        self.rowcount = rowcount

    def mappings(self) -> _MappingsResult:
        return self

    def all(self) -> list[dict[str, Any]]:
        return self._rows


class _FakeSession:
    def __init__(self, revisions: list[dict[str, Any]]) -> None:
        self.revisions = revisions
        self.statements: list[Any] = []
        self.scalar_result: Any = None
        self.scalar_results: list[Any] = []
        self.commit_count = 0
        self.rollback_count = 0

    def execute(self, statement: Any) -> _MappingsResult:
        self.statements.append(statement)
        if statement.__class__.__name__ == "Select":
            tables = {table.name for table in statement.get_final_froms()}
            if "story_revisions" in tables:
                return _MappingsResult(self.revisions)
            raise AssertionError(f"Unexpected unit-test query against {tables}")
        return _MappingsResult([])

    def scalar(self, statement: Any) -> Any:
        del statement
        if self.scalar_results:
            return self.scalar_results.pop(0)
        return self.scalar_result

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1


def _recovery_fixtures() -> tuple[
    VerifiedPrincipal,
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    now = datetime.now(UTC)
    principal = VerifiedPrincipal(
        subject="verified-provider-subject",
        issuer="https://identity.example.test/issuer",
        roles=frozenset({"PARENT"}),
    )
    context = {
        "schema_version": "sketch2life.parent-context.v1",
        "profile_revision_ref": "profile-revision",
        "age_months": 60,
        "interests_summary": "plants",
        "topic": "garden",
        "adult_confirmed_idea": "A garden adventure",
    }
    understanding_snapshot = {"result": {"visible_features": ["green leaves"]}}
    understanding_hash = _sha256_json(understanding_snapshot)
    input_row = {
        "context_snapshot": context,
        "context_snapshot_sha256": _sha256_json(context),
        "context_revision": 3,
        "original_sha256": "a" * 64,
    }
    selection_snapshot = {
        "title": "Plant activity",
        "objective": "Notice leaves",
        "instructions_text": "Look closely",
        "safety_notes": "Adult supervision",
        "activity_kind": "OBSERVATION",
        "source": "LESSON_ACTIVITY",
        "selected_at": (now - timedelta(minutes=1)).isoformat(),
    }
    selection = {
        "activity_snapshot": selection_snapshot,
        "activity_snapshot_sha256": _sha256_json(selection_snapshot),
        "created_at": now - timedelta(seconds=1),
        "lesson_id": "lesson-ref",
        "version_id": "lesson-version-ref",
        "content_sha256": "b" * 64,
        "target_understanding_revision": 1,
    }
    run = {
        "run_id": "run-ref",
        "actor_scope_kind": "PARENT_ACCOUNT",
        "actor_scope_ref": "owner-scope-ref",
        "run_state": "FAILED",
        "job_state": "FAILED",
        "error_code": "STORY_OUTPUT_INVALID",
        "active_owner_parent_account_id": None,
        "understanding_revision": 1,
        "subject_label": "confirmed subject",
        "result_sha256": understanding_hash,
        "version": 7,
        "revision": 9,
    }
    understanding = {
        "revision_no": 1,
        "canonical_result_sha256": understanding_hash,
        "result_snapshot": understanding_snapshot,
    }
    revision = {
        "story_revision_id": "failed-first-story",
        "revision_no": 1,
        "status": "FAILED",
        "story_sha256": None,
        "source_asset_sha256": input_row["original_sha256"],
        "understanding_revision": 1,
        "context_revision": 3,
        "request_sha256": "",
        "created_at": now,
    }
    revision["request_sha256"] = _parent_first_story_request_sha256(
        run=run,
        input_row=input_row,
        understanding_revision=1,
        idea_text="A garden adventure",
        visible_features=["green leaves"],
        selection=selection,
    )
    return principal, run, revision, input_row, understanding, selection


def _repository(
    monkeypatch: pytest.MonkeyPatch,
    *,
    revisions: list[dict[str, Any]] | None = None,
) -> tuple[
    SqlParentStoryRunRepository,
    _FakeSession,
    list[dict[str, Any]],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    VerifiedPrincipal,
]:
    principal, run, revision, input_row, understanding, selection = _recovery_fixtures()
    session = _FakeSession(revisions or [revision])
    repository = SqlParentStoryRunRepository(session)  # type: ignore[arg-type]
    receipt_calls: list[dict[str, Any]] = []

    monkeypatch.setattr(repository, "_owned_run_access", lambda *args, **kwargs: (run, None))
    monkeypatch.setattr(repository, "_lock_idempotency", lambda **kwargs: None)
    monkeypatch.setattr(repository, "_find_idempotency_receipt", lambda **kwargs: None)
    monkeypatch.setattr(repository, "_rewrite_attempts_used", lambda *args, **kwargs: 0)
    monkeypatch.setattr(
        repository,
        "_store_idempotency_receipt",
        lambda **kwargs: receipt_calls.append(kwargs) or "new-receipt",
    )
    monkeypatch.setattr(
        repository,
        "_story_generation_basis",
        lambda **kwargs: (
            understanding,
            input_row,
            "A garden adventure",
            list(understanding["result_snapshot"]["result"]["visible_features"]),
        ),
    )
    monkeypatch.setattr(
        parent_story_repository,
        "latest_selection_row",
        lambda *args: selection,
    )
    repository._test_selection = selection  # type: ignore[attr-defined]
    return repository, session, receipt_calls, run, revision, input_row, understanding, principal


def _reserve(repository: SqlParentStoryRunRepository, principal: VerifiedPrincipal, **kwargs: Any):
    params = {
        "principal": principal,
        "account_id": "parent-account-ref",
        "run_id": "run-ref",
        "idempotency_key": "new-recovery-key",
        "expected_story_revision": 1,
        "expected_story_sha256": None,
        "hint": None,
        "story_revision_id": "recovery-revision",
        "model_id": "story-model",
        "model_revision": "model-revision",
        "prompt_version": "prompt-version",
        "instruction_version": "instruction-version",
        "instruction": "Rewrite the story safely.",
    }
    params.update(kwargs)
    return repository.reserve_story_rewrite(**params)


def _statement_values(statement: Insert | Update) -> dict[str, Any]:
    return {
        column.name if hasattr(column, "name") else str(column): getattr(value, "value", value)
        for column, value in statement._values.items()
    }


def test_eligible_failed_first_story_reserves_revision_and_reacquires_parent_lock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, session, receipt_calls, _, _, _, _, principal = _repository(monkeypatch)

    outcome = _reserve(repository, principal)

    assert outcome.story_revision_no == 2
    assert outcome.run_state == "SCRIPT_GENERATING"
    assert outcome.reservation is not None
    assert len(receipt_calls) == 1
    revision_insert = next(
        statement
        for statement in session.statements
        if isinstance(statement, Insert) and statement.table is story_tables.story_revisions
    )
    assert _statement_values(revision_insert)["revision_no"] == 2
    run_update = next(
        statement
        for statement in session.statements
        if isinstance(statement, Update) and statement.table is story_tables.story_runs
    )
    values = _statement_values(run_update)
    assert values["active_owner_parent_account_id"] == "parent-account-ref"
    assert values["finished_at"] is None
    assert values["run_state"] == "SCRIPT_GENERATING"
    assert not any(
        isinstance(statement, Update) and statement.table is story_tables.story_revisions
        for statement in session.statements
    )
    assert session.commit_count == 1


def test_completing_recovery_keeps_failed_first_revision_immutable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    principal, _, _, _, _, _ = _recovery_fixtures()
    session = _FakeSession([])
    session.scalar_results = ["recovery-revision", "FAILED"]
    repository = SqlParentStoryRunRepository(session)  # type: ignore[arg-type]
    run = {"run_id": "run-ref", "run_state": "SCRIPT_GENERATING", "version": 10}
    monkeypatch.setattr(repository, "_owned_run", lambda *args, **kwargs: run)
    monkeypatch.setattr(repository, "get_run", lambda **kwargs: None)
    reservation = ParentStoryRevisionReservation(
        run_id="run-ref",
        story_revision_id="recovery-revision",
        revision_no=2,
        understanding_revision=1,
        context_revision=3,
        source_asset_sha256="a" * 64,
        worker_input={},
        request_sha256="e" * 64,
        receipt_id=None,
    )

    repository.complete_story_revision(
        reservation=reservation,
        principal=principal,
        story={
            "story": {},
            "language": "vi",
            "title": "Recovered story",
            "duration_ms": 30_000,
            "scenes": [],
        },
        story_sha256="f" * 64,
        provider_call_id="fixture-call",
        model_id="fixture-model",
        model_revision="1",
    )

    revision_status_updates = [
        _statement_values(statement).get("status")
        for statement in session.statements
        if isinstance(statement, Update) and statement.table is story_tables.story_revisions
    ]
    assert revision_status_updates == ["DRAFT"]
    assert session.commit_count == 1


def test_existing_recovery_key_replays_receipt_without_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, session, receipt_calls, _, _, _, _, principal = _repository(monkeypatch)
    monkeypatch.setattr(
        repository,
        "_find_idempotency_receipt",
        lambda **kwargs: {
            "response_body": {
                "story_revision_no": 2,
                "run_revision": 10,
                "run_state": "SCRIPT_GENERATING",
            }
        },
    )

    outcome = _reserve(repository, principal)

    assert outcome.replayed is True
    assert outcome.story_revision_no == 2
    assert outcome.run_revision == 10
    assert receipt_calls == []
    assert session.statements == []


@pytest.mark.parametrize(
    ("run_state", "job_state", "error_code", "expected_code"),
    [
        ("FAILED", "FAILED", "STORY_PROVIDER_FAILED", "PARENT_STORY_REWRITE_NOT_ALLOWED"),
        (
            "FAILED",
            "AWAITING_RECONCILIATION",
            "STORY_OUTPUT_INVALID",
            "PARENT_STORY_REWRITE_NOT_ALLOWED",
        ),
        ("FAILED", "FAILED", "SAFETY_BLOCKED", "PARENT_STORY_REWRITE_NOT_ALLOWED"),
        ("FAILED", "FAILED", "CONSENT_REVOKED", "PARENT_STORY_REWRITE_NOT_ALLOWED"),
        (
            "SCRIPT_GENERATION_UNKNOWN",
            "AWAITING_RECONCILIATION",
            "STORY_OUTPUT_INVALID",
            "INVALID_STATE_TRANSITION",
        ),
        ("ABANDONED", "FAILED", "STORY_OUTPUT_INVALID", "INVALID_STATE_TRANSITION"),
    ],
)
def test_other_failed_or_unknown_run_states_stay_terminal(
    monkeypatch: pytest.MonkeyPatch,
    run_state: str,
    job_state: str,
    error_code: str,
    expected_code: str,
) -> None:
    repository, _, _, run, _, _, _, principal = _repository(monkeypatch)
    run.update(run_state=run_state, job_state=job_state, error_code=error_code)

    with pytest.raises(ParentStoryRunError) as raised:
        _reserve(repository, principal)

    assert raised.value.code == expected_code


@pytest.mark.parametrize(
    "stale_field",
    ["context", "subject", "understanding", "drawing", "activity", "activity_hash"],
)
def test_recovery_refuses_stale_generation_basis(
    monkeypatch: pytest.MonkeyPatch,
    stale_field: str,
) -> None:
    repository, _, _, run, _, input_row, understanding, principal = _repository(monkeypatch)
    current_selection = repository._test_selection  # type: ignore[attr-defined]
    if stale_field == "context":
        input_row["context_snapshot"] = {**input_row["context_snapshot"], "age_months": 61}
        input_row["context_snapshot_sha256"] = _sha256_json(input_row["context_snapshot"])
    elif stale_field == "subject":
        run["subject_label"] = "changed subject"
    elif stale_field == "understanding":
        understanding["result_snapshot"] = {
            "result": {"visible_features": ["changed feature"]}
        }
        understanding["canonical_result_sha256"] = _sha256_json(understanding["result_snapshot"])
        run["result_sha256"] = understanding["canonical_result_sha256"]
    elif stale_field == "drawing":
        input_row["original_sha256"] = "c" * 64
    elif stale_field == "activity":
        current_selection["activity_snapshot"] = {
            **current_selection["activity_snapshot"],
            "title": "Changed activity",
        }
        current_selection["activity_snapshot_sha256"] = _sha256_json(
            current_selection["activity_snapshot"]
        )
        monkeypatch.setattr(
            parent_story_repository,
            "latest_selection_row",
            lambda *args: current_selection,
        )
    else:
        current_selection["activity_snapshot_sha256"] = "d" * 64
        monkeypatch.setattr(
            parent_story_repository,
            "latest_selection_row",
            lambda *args: current_selection,
        )

    with pytest.raises(ParentStoryRunError) as raised:
        _reserve(repository, principal)

    assert raised.value.code == "PARENT_STORY_REWRITE_NOT_ALLOWED"


def test_another_active_parent_run_rejects_before_revision_or_receipt_insert(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, session, receipt_calls, _, _, _, _, principal = _repository(monkeypatch)
    session.scalar_result = "other-active-run"

    with pytest.raises(ParentStoryRunError) as raised:
        _reserve(repository, principal)

    assert raised.value.code == "ACTIVE_RUN_EXISTS"
    assert receipt_calls == []
    assert not any(isinstance(statement, Insert) for statement in session.statements)
    assert session.rollback_count == 1


def test_an_in_flight_recovery_uses_the_ordinary_invalid_state_transition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, _, _, run, _, _, _, principal = _repository(
        monkeypatch,
        revisions=[
            {"revision_no": 2, "status": "GENERATING"},
            {"revision_no": 1, "status": "FAILED"},
        ],
    )
    run.update(
        run_state="SCRIPT_GENERATING",
        job_state="QUEUED",
        active_owner_parent_account_id="parent-account-ref",
    )

    with pytest.raises(ParentStoryRunError) as raised:
        _reserve(repository, principal)

    assert raised.value.code == "INVALID_STATE_TRANSITION"


@pytest.mark.parametrize("instruction", ["", "   "])
def test_empty_rewrite_instruction_is_refused(
    monkeypatch: pytest.MonkeyPatch,
    instruction: str,
) -> None:
    repository, _, _, _, _, _, _, principal = _repository(monkeypatch)

    with pytest.raises(ParentStoryRunError) as raised:
        _reserve(repository, principal, instruction=instruction)

    assert raised.value.status_code == 422
    assert raised.value.code == "PARENT_REWRITE_INSTRUCTION_INVALID"


def test_failed_recovery_uses_terminal_failure_path_and_preserves_regular_rewrite_recovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, session, _, run, _, _, _, principal = _repository(monkeypatch)
    run.update(run_state="SCRIPT_GENERATING", job_state="RUNNING")
    monkeypatch.setattr(repository, "_owned_run", lambda *args, **kwargs: run)
    session.scalar_result = "FAILED"
    terminal_calls: list[dict[str, Any]] = []
    monkeypatch.setattr(
        repository,
        "_fail_generating_revision",
        lambda **kwargs: terminal_calls.append(kwargs),
    )
    monkeypatch.setattr(
        repository,
        "recover_failed_rewrite",
        lambda **kwargs: pytest.fail("recovery failure must remain terminal"),
    )
    reservation = ParentStoryRevisionReservation(
        run_id="run-ref",
        story_revision_id="recovery-revision",
        revision_no=2,
        understanding_revision=1,
        context_revision=3,
        source_asset_sha256="a" * 64,
        worker_input={},
        request_sha256="e" * 64,
        receipt_id=None,
    )

    repository.fail_story_revision(
        principal=principal,
        reservation=reservation,
        error_code="STORY_OUTPUT_INVALID",
        outcome_unknown=False,
    )

    assert len(terminal_calls) == 1
    assert terminal_calls[0]["error_code"] == "STORY_OUTPUT_INVALID"
    assert session.commit_count == 1

    session.scalar_result = "DRAFT"
    recovered_calls: list[dict[str, Any]] = []
    monkeypatch.setattr(
        repository,
        "_fail_generating_revision",
        lambda **kwargs: pytest.fail("ordinary rewrite should be recoverable"),
    )
    monkeypatch.setattr(
        repository,
        "recover_failed_rewrite",
        lambda **kwargs: recovered_calls.append(kwargs),
    )
    repository.fail_story_revision(
        principal=principal,
        reservation=reservation,
        error_code="STORY_PROVIDER_FAILED",
        outcome_unknown=False,
    )
    assert len(recovered_calls) == 1


def test_recover_failed_rewrite_refuses_a_failed_previous_revision() -> None:
    session = _FakeSession([])
    session.scalar_result = "FAILED"
    repository = SqlParentStoryRunRepository(session)  # type: ignore[arg-type]

    with pytest.raises(ParentStoryRunError) as raised:
        repository.recover_failed_rewrite(
            run={
                "run_id": "run-ref",
                "actor_scope_ref": "owner-scope-ref",
                "version": 10,
                "revision": 12,
            },
            story_revision_id="recovery-revision",
            revision_no=2,
            error_code="PROVIDER_TIMEOUT",
            now=datetime.now(UTC),
            actor_ref="reaper",
        )

    assert raised.value.code == "INVALID_STATE_TRANSITION"
    assert session.statements == []


def test_deleted_run_cannot_enter_recovery(monkeypatch: pytest.MonkeyPatch) -> None:
    repository, _, _, run, _, _, _, principal = _repository(monkeypatch)
    run["run_state"] = "DELETED"

    with pytest.raises(ParentStoryRunError):
        _reserve(repository, principal)
