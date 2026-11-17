from __future__ import annotations

import hashlib
from types import SimpleNamespace
from typing import Any

import pytest

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryRevisionReservation,
    ParentStoryRunError,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)

_PRINCIPAL = VerifiedPrincipal("parent-1", "issuer-1", frozenset({"parent"}))
_RUN_ID = "22222222-2222-4222-8222-222222222222"


class _Mappings:
    def __init__(self, value: Any) -> None:
        self._value = value

    def one_or_none(self) -> Any:
        return self._value


class _Result:
    def __init__(self, value: Any = None) -> None:
        self._value = value

    def mappings(self) -> _Mappings:
        return _Mappings(self._value)


class _Session:
    def __init__(self, receipt: Any = None) -> None:
        self.receipt = receipt
        self.statements: list[Any] = []
        self.commits = 0
        self.rollbacks = 0

    def execute(self, statement: Any, *_args: Any, **_kwargs: Any) -> _Result:
        self.statements.append(statement)
        return _Result(self.receipt)

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


def _repository(monkeypatch: pytest.MonkeyPatch, *, run_state: str = "SCRIPT_GENERATING"):
    session = _Session()
    repository = SqlParentStoryRunRepository(session)  # type: ignore[arg-type]
    run = {
        "run_id": _RUN_ID,
        "run_state": run_state,
        "revision": 7,
        "version": 9,
        "active_owner_parent_account_id": "parent-account-1",
    }
    monkeypatch.setattr(
        repository,
        "_owned_run",
        lambda *_args, **_kwargs: dict(run),
    )
    monkeypatch.setattr(repository, "_lock_idempotency", lambda **_kwargs: None)
    record = SimpleNamespace(run_state="DELETE_PENDING", run_revision=8)
    monkeypatch.setattr(repository, "get_run", lambda **_kwargs: record)
    return repository, session, run


def test_cancel_persists_exact_202_body_and_releases_active_owner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, session, _run = _repository(monkeypatch)
    stored: dict[str, Any] = {}
    monkeypatch.setattr(repository, "_store_idempotency_receipt", lambda **kwargs: stored.update(kwargs))

    def build_response(record: Any, request_id: str) -> dict[str, Any]:
        return {
            "request_id": request_id,
            "story_run": {
                "run_state": record.run_state,
                "run_revision": record.run_revision,
            },
            "purge_state": "PENDING",
        }

    result = repository.cancel_run(
        principal=_PRINCIPAL,
        run_id=_RUN_ID,
        expected_revision=7,
        idempotency_key="cancel-1",
        request_id="request-uuid",
        response_builder=build_response,
    )

    assert result == {
        "request_id": "request-uuid",
        "story_run": {"run_state": "DELETE_PENDING", "run_revision": 8},
        "purge_state": "PENDING",
    }
    assert stored["operation"] == "CANCEL_RUN"
    assert stored["response_status"] == 202
    assert stored["response_body"] == result
    assert session.commits == 1
    update_values = session.statements[-1]._values
    assert update_values["run_state"].value == "DELETE_PENDING"
    assert update_values["active_owner_parent_account_id"].value is None


def test_cancel_replays_receipt_before_revision_precondition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = {
        "request_id": "original-request-id",
        "story_run": {"run_state": "DELETE_PENDING", "run_revision": 8},
        "purge_state": "PENDING",
    }
    receipt = {
        "idempotency_scope_kind": "STORY_RUN",
        "idempotency_scope_ref": _RUN_ID,
        "request_fingerprint_sha256": hashlib.sha256(
            b'{"expected_revision":7,"run_id":"22222222-2222-4222-8222-222222222222"}'
        ).hexdigest(),
        "state": "FINAL",
        "response_status": 202,
        "response_body": body,
    }
    session = _Session(receipt)
    repository = SqlParentStoryRunRepository(session)  # type: ignore[arg-type]
    monkeypatch.setattr(
        repository,
        "_owned_run",
        lambda *_args, **_kwargs: {"revision": 8, "version": 10},
    )
    monkeypatch.setattr(repository, "_lock_idempotency", lambda **_kwargs: None)

    result = repository.cancel_run(
        principal=_PRINCIPAL,
        run_id=_RUN_ID,
        expected_revision=7,
        idempotency_key="cancel-1",
        request_id="new-request-id",
        response_builder=lambda *_args: pytest.fail("replay must not rebuild response"),
    )

    assert result == body
    assert session.commits == 1
    assert len(session.statements) == 1


def test_cancel_rejects_stale_revision_and_cross_run_key_reuse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, session, _run = _repository(monkeypatch)
    with pytest.raises(ParentStoryRunError) as stale:
        repository.cancel_run(
            principal=_PRINCIPAL,
            run_id=_RUN_ID,
            expected_revision=6,
            idempotency_key="cancel-1",
            request_id="request-id",
            response_builder=lambda *_args: {},
        )
    assert stale.value.status_code == 409
    assert stale.value.code == "STALE_REVISION"
    assert stale.value.current_version == 7
    assert session.rollbacks == 1

    other_receipt = {
        "idempotency_scope_kind": "STORY_RUN",
        "idempotency_scope_ref": "33333333-3333-4333-8333-333333333333",
        "request_fingerprint_sha256": "f" * 64,
        "state": "FINAL",
        "response_status": 202,
        "response_body": {"not": "replayed"},
    }
    session.receipt = other_receipt
    with pytest.raises(ParentStoryRunError, match="INVALID_IDEMPOTENCY_KEY"):
        repository.cancel_run(
            principal=_PRINCIPAL,
            run_id=_RUN_ID,
            expected_revision=7,
            idempotency_key="cancel-1",
            request_id="request-id",
            response_builder=lambda *_args: {},
        )

    same_run_receipt = {
        "idempotency_scope_kind": "STORY_RUN",
        "idempotency_scope_ref": _RUN_ID,
        "request_fingerprint_sha256": "f" * 64,
        "state": "FINAL",
        "response_status": 202,
        "response_body": {"not": "replayed"},
    }
    session.receipt = same_run_receipt
    with pytest.raises(ParentStoryRunError, match="INVALID_IDEMPOTENCY_KEY"):
        repository.cancel_run(
            principal=_PRINCIPAL,
            run_id=_RUN_ID,
            expected_revision=7,
            idempotency_key="cancel-1",
            request_id="request-id",
            response_builder=lambda *_args: {},
        )


@pytest.mark.parametrize("run_state", ("COMPLETED", "FAILED", "DELETE_PENDING"))
def test_cancel_refuses_terminal_or_already_cancelled_states_without_update(
    monkeypatch: pytest.MonkeyPatch, run_state: str
) -> None:
    repository, session, _run = _repository(monkeypatch, run_state=run_state)
    with pytest.raises(ParentStoryRunError) as refused:
        repository.cancel_run(
            principal=_PRINCIPAL,
            run_id=_RUN_ID,
            expected_revision=7,
            idempotency_key="cancel-1",
            request_id="request-id",
            response_builder=lambda *_args: {},
        )
    assert refused.value.status_code == 409
    assert refused.value.code == "INVALID_STATE_TRANSITION"
    assert len(session.statements) == 1
    assert session.rollbacks == 1


def test_cancel_hides_non_owned_runs_before_receipt_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, session, _run = _repository(monkeypatch)

    def not_owned(*_args: Any, **_kwargs: Any) -> None:
        raise ParentStoryRunError(404, "RESOURCE_NOT_FOUND")

    monkeypatch.setattr(repository, "_owned_run", not_owned)
    with pytest.raises(ParentStoryRunError, match="RESOURCE_NOT_FOUND"):
        repository.cancel_run(
            principal=_PRINCIPAL,
            run_id=_RUN_ID,
            expected_revision=7,
            idempotency_key="cancel-1",
            request_id="request-id",
            response_builder=lambda *_args: {},
        )
    assert session.statements == []


@pytest.mark.parametrize("method", ("complete", "story-failure", "drawing-failure"))
def test_late_provider_result_paths_refuse_delete_pending_without_writes(
    monkeypatch: pytest.MonkeyPatch, method: str
) -> None:
    repository, session, _run = _repository(monkeypatch, run_state="DELETE_PENDING")
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
    assert blocked.value.status_code == 409
    assert blocked.value.code == "INVALID_STATE_TRANSITION"
    assert session.statements == []
