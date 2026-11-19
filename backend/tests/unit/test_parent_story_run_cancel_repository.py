"""FR-C-08 cancel and delete command transaction (DTR Draft 6 §6.1, Contract Draft 11 §3.1-§3.2).

The repository is driven with a statement-recording session; no database is used. The tests
check the error order, the five writes of one accepted command, replays and the access fence
of the three late-result writers (DTR §7).
"""

from __future__ import annotations

import hashlib
import json
from types import SimpleNamespace
from typing import Any

import pytest
from sqlalchemy.dialects import postgresql

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryLifecycleRecord,
    ParentStoryRevisionReservation,
    ParentStoryRunError,
)
from sketch2life.application.ports.story_run_lifecycle import (
    CANCEL_EVENT_TYPE,
    DELETE_EVENT_TYPE,
    lifecycle_audit_id,
    lifecycle_event_id,
    lifecycle_request_id,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)

_PRINCIPAL = VerifiedPrincipal("parent-1", "issuer-1", frozenset({"parent"}))
_RUN_ID = "22222222-2222-4222-8222-222222222222"
_REQUEST_ID = lifecycle_request_id(_RUN_ID)


def _fingerprint(value: dict[str, Any]) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class _Mappings:
    def __init__(self, value: Any) -> None:
        self._value = value

    def one_or_none(self) -> Any:
        return self._value


class _Result:
    def __init__(self, value: Any = None, rowcount: int = 1) -> None:
        self._value = value
        self.rowcount = rowcount

    def mappings(self) -> _Mappings:
        return _Mappings(self._value)


class _Session:
    def __init__(self, receipt: Any = None, *, run_rowcount: int = 1) -> None:
        self.receipt = receipt
        self.run_rowcount = run_rowcount
        self.statements: list[Any] = []
        self.commits = 0
        self.rollbacks = 0

    def execute(self, statement: Any, *_args: Any, **_kwargs: Any) -> _Result:
        self.statements.append(statement)
        table = getattr(getattr(statement, "table", None), "name", "")
        if table == "runs":
            return _Result(rowcount=self.run_rowcount)
        return _Result(self.receipt)

    def scalar(self, *_args: Any, **_kwargs: Any) -> Any:
        return None

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1

    def writes_to(self, table: str) -> list[Any]:
        return [
            statement
            for statement in self.statements
            if getattr(getattr(statement, "table", None), "name", "") == table
        ]


def _params(statement: Any) -> dict[str, Any]:
    dialect: Any = postgresql.dialect  # the dialect class has no type annotations
    return dict(statement.compile(dialect=dialect()).params)


def _repository(
    monkeypatch: pytest.MonkeyPatch,
    *,
    run_state: str = "SCRIPT_GENERATING",
    receipt: Any = None,
    run_rowcount: int = 1,
) -> tuple[SqlParentStoryRunRepository, _Session, dict[str, Any]]:
    session = _Session(receipt, run_rowcount=run_rowcount)
    repository = SqlParentStoryRunRepository(session)  # type: ignore[arg-type]
    stored: dict[str, Any] = {}
    run = {
        "run_id": _RUN_ID,
        "run_state": run_state,
        "revision": 7,
        "version": 9,
        "active_owner_parent_account_id": "parent-account-1",
    }
    monkeypatch.setattr(repository, "_owned_run", lambda *_args, **_kwargs: dict(run))
    monkeypatch.setattr(repository, "_lock_idempotency", lambda **_kwargs: None)
    monkeypatch.setattr(
        repository, "_store_idempotency_receipt", lambda **kwargs: stored.update(kwargs)
    )
    return repository, session, stored


def _cancel(repository: SqlParentStoryRunRepository, **overrides: Any) -> Any:
    values: dict[str, Any] = {
        "principal": _PRINCIPAL,
        "run_id": _RUN_ID,
        "expected_revision": 7,
        "idempotency_key": "cancel-1",
    }
    values.update(overrides)
    return repository.cancel_run(**values)


def _delete(repository: SqlParentStoryRunRepository, **overrides: Any) -> Any:
    values: dict[str, Any] = {
        "principal": _PRINCIPAL,
        "run_id": _RUN_ID,
        "idempotency_key": "delete-1",
    }
    values.update(overrides)
    return repository.delete_run(**values)


def test_cancel_writes_the_five_rows_in_one_transaction_and_returns_the_projection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, session, stored = _repository(monkeypatch)
    record = _cancel(repository)

    expected = {
        "run_id": _RUN_ID,
        "run_state": "DELETE_PENDING",
        "revision": 8,
        "version": 10,
        "lifecycle_request_ref": _REQUEST_ID,
        "purge_state": "PENDING",
    }
    assert isinstance(record, ParentStoryLifecycleRecord)
    assert record.as_body() == expected
    assert stored["operation"] == "CANCEL_RUN"
    assert stored["response_status"] == 202
    assert stored["response_body"] == expected
    assert stored["fingerprint"] == _fingerprint({"run_id": _RUN_ID, "expected_revision": 7})
    assert session.commits == 1 and session.rollbacks == 0

    (run_update,) = session.writes_to("runs")
    run_values = run_update._values
    assert run_values["run_state"].value == "DELETE_PENDING"
    assert run_values["active_owner_parent_account_id"].value is None
    assert run_values["revision"].value == 8 and run_values["version"].value == 10
    assert "NOT IN" in str(run_update.compile(dialect=postgresql.dialect()))  # type: ignore[no-untyped-call]

    (aggregate,) = session.writes_to("core_aggregate_revisions")
    aggregate_params = _params(aggregate)
    assert aggregate_params["aggregate_id"] == _RUN_ID
    assert aggregate_params["organization_id"] is None
    assert aggregate_params["owner_scope_kind"] == "PARENT_ACCOUNT"
    assert aggregate_params["revision"] == 8

    (event,) = session.writes_to("core_outbox_events")
    event_params = _params(event)
    assert event_params["event_id"] == lifecycle_event_id(_REQUEST_ID, CANCEL_EVENT_TYPE)
    assert event_params["event_type"] == CANCEL_EVENT_TYPE
    assert event_params["organization_id"] is None
    assert event_params["payload"] == {
        "run_ref": _RUN_ID,
        "lifecycle_request_ref": _REQUEST_ID,
        "actor_ref": event_params["owner_scope_ref"],
        "reason_code": "PARENT_CANCEL_REQUESTED",
        "expected_revision": "7",
    }
    assert "ON CONFLICT" in str(event.compile(dialect=postgresql.dialect()))  # type: ignore[no-untyped-call]

    (audit,) = session.writes_to("core_audit_entries")
    audit_params = _params(audit)
    assert audit_params["audit_id"] == lifecycle_audit_id(_REQUEST_ID, "lifecycle.cancel_accepted")
    assert audit_params["decision"] == "accepted:" + _REQUEST_ID
    assert len(audit_params["decision"]) <= 46
    assert audit_params["organization_id"] is None
    assert audit_params["resource_type"] == "story_run"
    assert set(audit_params) == {
        "audit_id",
        "organization_id",
        "owner_scope_kind",
        "owner_scope_ref",
        "actor_ref",
        "action",
        "resource_type",
        "resource_id",
        "decision",
        "created_at",
    }


def test_delete_needs_no_revision_and_emits_the_delete_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, session, stored = _repository(monkeypatch, run_state="COMPLETED")
    record = _delete(repository)
    assert record.run_state == "DELETE_PENDING" and record.purge_state == "PENDING"
    assert stored["operation"] == "DELETE_RUN"
    assert stored["fingerprint"] == _fingerprint({"run_id": _RUN_ID})
    (event,) = session.writes_to("core_outbox_events")
    params = _params(event)
    assert params["event_type"] == DELETE_EVENT_TYPE
    assert params["event_id"] == lifecycle_event_id(_REQUEST_ID, DELETE_EVENT_TYPE)
    assert "expected_revision" not in params["payload"]
    (audit,) = session.writes_to("core_audit_entries")
    assert _params(audit)["action"] == "lifecycle.delete_accepted"


@pytest.mark.parametrize("run_state", ("COMPLETED", "FAILED", "ABANDONED"))
def test_delete_accepts_the_three_finished_states(
    monkeypatch: pytest.MonkeyPatch, run_state: str
) -> None:
    repository, session, _stored = _repository(monkeypatch, run_state=run_state)
    assert _delete(repository).run_state == "DELETE_PENDING"
    assert session.commits == 1


@pytest.mark.parametrize(
    "run_state",
    ("INPUT_PROCESSING", "SCRIPT_REVIEW", "SCRIPT_GENERATING", "DELETE_PENDING", "DELETED"),
)
def test_delete_refuses_every_other_state_without_a_write(
    monkeypatch: pytest.MonkeyPatch, run_state: str
) -> None:
    repository, session, stored = _repository(monkeypatch, run_state=run_state)
    with pytest.raises(ParentStoryRunError) as refused:
        _delete(repository)
    assert (refused.value.status_code, refused.value.code) == (409, "INVALID_STATE_TRANSITION")
    assert refused.value.current_version is None
    assert len(session.statements) == 1  # the receipt lookup only
    assert stored == {} and session.rollbacks == 1


@pytest.mark.parametrize(
    "run_state",
    (
        "INPUT_PROCESSING",
        "SUBJECT_REVIEW",
        "PREPARATION_REVIEW",
        "SCRIPT_GENERATING",
        "SCRIPT_GENERATION_UNKNOWN",
        "SCRIPT_REVIEW",
        "VIDEO_ADMISSION_PENDING",
        "DRAFT",
        "INPUT_REVIEW",
        "STORY_GENERATING",
        "VIDEO_QUEUED",
        "VIDEO_GENERATING",
        "VIDEO_SAFETY_VALIDATING",
        "VIDEO_READY",
        "SAFETY_BLOCKED",
    ),
)
def test_cancel_accepts_the_thirteen_srs_states_and_the_two_extensions(
    monkeypatch: pytest.MonkeyPatch, run_state: str
) -> None:
    repository, session, _stored = _repository(monkeypatch, run_state=run_state)
    assert _cancel(repository).run_state == "DELETE_PENDING"
    assert session.commits == 1


@pytest.mark.parametrize("run_state", ("COMPLETED", "FAILED", "ABANDONED", "DELETE_PENDING", "DELETED"))
def test_cancel_refuses_terminal_and_purge_states_without_a_write(
    monkeypatch: pytest.MonkeyPatch, run_state: str
) -> None:
    repository, session, stored = _repository(monkeypatch, run_state=run_state)
    with pytest.raises(ParentStoryRunError) as refused:
        _cancel(repository)
    assert (refused.value.status_code, refused.value.code) == (409, "INVALID_STATE_TRANSITION")
    assert len(session.statements) == 1
    assert stored == {} and session.rollbacks == 1


def test_cancel_error_order_puts_the_revision_before_the_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, session, _stored = _repository(monkeypatch, run_state="DELETE_PENDING")
    with pytest.raises(ParentStoryRunError) as stale:
        _cancel(repository, expected_revision=6, idempotency_key="new-key")
    assert (stale.value.status_code, stale.value.code) == (409, "STALE_REVISION")
    assert stale.value.current_version == 7
    assert session.rollbacks == 1


def test_cancel_replay_returns_the_stored_projection_before_the_revision_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = {
        "run_id": _RUN_ID,
        "run_state": "DELETE_PENDING",
        "revision": 8,
        "version": 10,
        "lifecycle_request_ref": _REQUEST_ID,
        "purge_state": "PENDING",
    }
    receipt = {
        "idempotency_scope_kind": "STORY_RUN",
        "idempotency_scope_ref": _RUN_ID,
        "request_fingerprint_sha256": _fingerprint({"run_id": _RUN_ID, "expected_revision": 7}),
        "state": "FINAL",
        "response_status": 202,
        "response_body": body,
    }
    repository, session, stored = _repository(
        monkeypatch, run_state="DELETED", receipt=receipt
    )
    record = _cancel(repository)
    assert record.as_body() == body  # the stored body, not the current DELETED state
    assert session.commits == 1 and stored == {}
    assert len(session.statements) == 1


def test_replay_of_a_pre_existing_m2_cancel_body_returns_the_current_projection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = {
        "idempotency_scope_kind": "STORY_RUN",
        "idempotency_scope_ref": _RUN_ID,
        "request_fingerprint_sha256": _fingerprint({"run_id": _RUN_ID, "expected_revision": 7}),
        "state": "FINAL",
        "response_status": 202,
        "response_body": {
            "request_id": "old",
            "story_run": {"subject_label": "private"},
            "purge_state": "PENDING",
        },
    }
    repository, _session, _stored = _repository(
        monkeypatch, run_state="DELETE_PENDING", receipt=receipt
    )
    record = _cancel(repository)
    assert record.as_body()["revision"] == 7
    assert "story_run" not in record.as_body()


@pytest.mark.parametrize(
    ("scope_ref", "fingerprint"),
    (
        ("33333333-3333-4333-8333-333333333333", "f" * 64),
        (_RUN_ID, "f" * 64),
    ),
)
def test_a_changed_payload_or_another_run_under_the_same_key_is_refused(
    monkeypatch: pytest.MonkeyPatch, scope_ref: str, fingerprint: str
) -> None:
    receipt = {
        "idempotency_scope_kind": "STORY_RUN",
        "idempotency_scope_ref": scope_ref,
        "request_fingerprint_sha256": fingerprint,
        "state": "FINAL",
        "response_status": 202,
        "response_body": {"not": "replayed"},
    }
    repository, session, _stored = _repository(monkeypatch, receipt=receipt)
    with pytest.raises(ParentStoryRunError, match="INVALID_IDEMPOTENCY_KEY"):
        _cancel(repository)
    assert session.rollbacks == 1


def test_a_lost_run_update_is_refused_and_rolled_back(monkeypatch: pytest.MonkeyPatch) -> None:
    repository, session, stored = _repository(monkeypatch, run_rowcount=0)
    with pytest.raises(ParentStoryRunError, match="INVALID_STATE_TRANSITION"):
        _cancel(repository)
    assert stored == {} and session.commits == 0 and session.rollbacks == 1
    assert session.writes_to("core_outbox_events") == []


def test_non_owned_runs_are_hidden_before_any_statement(monkeypatch: pytest.MonkeyPatch) -> None:
    repository, session, _stored = _repository(monkeypatch)

    def not_owned(*_args: Any, **_kwargs: Any) -> None:
        raise ParentStoryRunError(404, "RESOURCE_NOT_FOUND")

    monkeypatch.setattr(repository, "_owned_run", not_owned)
    for command in (_cancel, _delete):
        with pytest.raises(ParentStoryRunError, match="RESOURCE_NOT_FOUND"):
            command(repository)
    assert session.statements == []


@pytest.mark.parametrize("run_state", ("DELETE_PENDING", "DELETED"))
@pytest.mark.parametrize("method", ("complete", "story-failure", "drawing-failure"))
def test_late_provider_results_cannot_change_a_purged_run(
    monkeypatch: pytest.MonkeyPatch, method: str, run_state: str
) -> None:
    repository, session, _stored = _repository(monkeypatch, run_state=run_state)
    reservation = ParentStoryRevisionReservation(
        run_id=_RUN_ID,
        story_revision_id="44444444-4444-4444-8444-444444444444",
        revision_no=1,
        understanding_revision=1,
        context_revision=1,
        source_asset_sha256="a" * 64,
        worker_input={},
        request_sha256="b" * 64,
        receipt_id="55555555-5555-4555-8555-555555555555",
    )
    with pytest.raises(ParentStoryRunError) as blocked:
        if method == "complete":
            repository.complete_story_revision(
                principal=_PRINCIPAL,
                reservation=reservation,
                story={},
                story_sha256="c" * 64,
                provider_call_id="call-id",
                model_id="model",
                model_revision="revision",
            )
        elif method == "story-failure":
            repository.fail_story_revision(
                principal=_PRINCIPAL,
                reservation=reservation,
                error_code="provider-error",
                outcome_unknown=True,
            )
        else:
            repository.fail_drawing_analysis(
                principal=_PRINCIPAL,
                run_id=_RUN_ID,
                error_code="provider-error",
                outcome_unknown=True,
            )
    assert (blocked.value.status_code, blocked.value.code) == (409, "INVALID_STATE_TRANSITION")
    assert session.statements == []


def test_the_drawing_failure_update_is_fenced_and_a_lost_update_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, session, _stored = _repository(
        monkeypatch, run_state="INPUT_PROCESSING", run_rowcount=0
    )
    with pytest.raises(ParentStoryRunError, match="INVALID_STATE_TRANSITION"):
        repository.fail_drawing_analysis(
            principal=_PRINCIPAL, run_id=_RUN_ID, error_code="x", outcome_unknown=False
        )
    (update_statement,) = session.writes_to("runs")
    sql = str(update_statement.compile(dialect=postgresql.dialect()))  # type: ignore[no-untyped-call]
    assert "run_state NOT IN" in sql
    assert session.commits == 0


@pytest.mark.parametrize("run_state", ("DELETE_PENDING", "DELETED"))
def test_read_current_input_and_the_artwork_recheck_refuse_a_purged_run(
    monkeypatch: pytest.MonkeyPatch, run_state: str
) -> None:
    repository, _session, _stored = _repository(monkeypatch, run_state=run_state)
    monkeypatch.setattr(
        repository, "_current_input", lambda _run: pytest.fail("input must not be read")
    )
    for call in (repository.read_current_input, repository.ensure_accepting_artwork):
        with pytest.raises(ParentStoryRunError) as refused:
            call(principal=_PRINCIPAL, run_id=_RUN_ID)
        assert (refused.value.status_code, refused.value.code) == (
            409,
            "INVALID_STATE_TRANSITION",
        )


def test_get_run_returns_the_projection_before_any_input_or_profile_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, _session, _stored = _repository(monkeypatch, run_state="DELETED")
    monkeypatch.setattr(
        repository, "_current_input", lambda _run: pytest.fail("input must not be read")
    )
    view = repository.get_run(principal=_PRINCIPAL, run_id=_RUN_ID)
    assert isinstance(view, ParentStoryLifecycleRecord)
    assert view.as_body() == {
        "run_id": _RUN_ID,
        "run_state": "DELETED",
        "revision": 7,
        "version": 9,
        "lifecycle_request_ref": _REQUEST_ID,
        "purge_state": "COMPLETED",
    }


def test_a_replayed_story_revision_of_a_purged_run_returns_the_projection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, _session, _stored = _repository(monkeypatch, run_state="DELETE_PENDING")
    monkeypatch.setattr(
        repository,
        "_find_idempotency_receipt",
        lambda **_kwargs: {"receipt_id": "66666666-6666-4666-8666-666666666666"},
    )
    reservation = repository.reserve_story_revision(
        principal=_PRINCIPAL,
        run_id=_RUN_ID,
        expected_understanding_revision=1,
        rewrite_instruction=None,
        idempotency_key="story-1",
        story_revision_id="77777777-7777-4777-8777-777777777777",
        model_id="m",
        model_revision="r",
        prompt_version="p",
    )
    assert reservation.replayed and reservation.lifecycle is not None
    assert reservation.lifecycle.run_state == "DELETE_PENDING"
    assert reservation.worker_input == {}


def test_a_new_story_revision_on_a_purged_run_is_a_lifecycle_conflict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, _session, _stored = _repository(monkeypatch, run_state="DELETED")
    monkeypatch.setattr(repository, "_find_idempotency_receipt", lambda **_kwargs: None)
    with pytest.raises(ParentStoryRunError) as refused:
        repository.reserve_story_revision(
            principal=_PRINCIPAL,
            run_id=_RUN_ID,
            expected_understanding_revision=1,
            rewrite_instruction=None,
            idempotency_key="story-2",
            story_revision_id="77777777-7777-4777-8777-777777777777",
            model_id="m",
            model_revision="r",
            prompt_version="p",
        )
    assert (refused.value.status_code, refused.value.code) == (409, "INVALID_STATE_TRANSITION")


def test_a_replayed_subject_confirmation_of_a_purged_run_returns_the_projection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, _session, _stored = _repository(monkeypatch, run_state="DELETED")
    monkeypatch.setattr(
        repository,
        "_find_idempotency_receipt",
        lambda **_kwargs: SimpleNamespace(),
    )
    result = repository.confirm_subject(
        principal=_PRINCIPAL,
        run_id=_RUN_ID,
        expected_understanding_revision=1,
        confirmed_subject="butterfly",
        idempotency_key="subject-1",
    )
    assert isinstance(result, ParentStoryLifecycleRecord)
    assert result.purge_state == "COMPLETED"
