"""FEAT-066 T-7b: the class state machine, the read/write class guard and the command order.

No database: a small fake session stands in for the one the handlers use (the pattern of
``test_be1_scope_guard_404_403.py``). The PostgreSQL behaviour (locks, receipts, races, the cursor
scope) is in ``tests/integration/test_t7b_class_state_postgres.py``.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import pytest
from fastapi import HTTPException, Response
from sqlalchemy.dialects.postgresql.base import PGDialect
from sqlalchemy.orm import Session
from starlette.datastructures import Headers

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
)
from sketch2life.interfaces.http.routers import be1_registry
from sketch2life.interfaces.http.routers.be1_common import get_class, hide_archived_from_teacher

ISSUER = "https://issuer.example.test/synthetic"
PRINCIPAL = VerifiedPrincipal(subject="adult-1", issuer=ISSUER, roles=frozenset())
ORG = "org-1"
STATES = ("active", "suspended", "archived")


class _Scalars:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def all(self) -> list[Any]:
        return self._rows


class _FakeSession:
    def __init__(
        self,
        *,
        classroom: Any,
        role: str = "school_manager",
        rows: list[Any] | None = None,
        receipt: Any = None,
    ) -> None:
        self.classroom = classroom
        self.identity = SimpleNamespace(state="active", account_role=role, issuer=ISSUER)
        self.rows = rows if rows is not None else []
        self.receipt = receipt
        self.added: list[Any] = []
        self.commits = 0
        self.rollbacks = 0

    def get(self, model: Any, _key: Any) -> Any:
        if model is AdultIdentityModel:
            return self.identity
        if model is Be1CommandReceiptModel:
            return self.receipt
        return None

    def scalars(self, _statement: Any) -> _Scalars:
        return _Scalars(self.rows)

    def scalar(self, _statement: Any) -> Any:
        return self.classroom

    def add(self, row: Any) -> None:
        self.added.append(row)

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


def _classroom(state: str = "active", revision: int = 1) -> Any:
    return SimpleNamespace(
        class_id="class-a", organization_id=ORG, state=state, revision=revision
    )


def _row(*, role: str, class_id: str | None) -> Any:
    return SimpleNamespace(
        organization_id=ORG,
        subject=PRINCIPAL.subject,
        class_id=class_id,
        role=role,
        active=True,
        assignment_id=f"assign-{role}-{class_id}",
    )


def _call(
    command: str, session: _FakeSession, *, if_match: str | None = '"1"', key: str = "key-1"
) -> dict[str, object]:
    handler = be1_registry.suspend_class if command == "suspend" else be1_registry.archive_class
    request = cast(Any, SimpleNamespace(headers=Headers({"Idempotency-Key": key})))
    return handler(
        "class-a",
        request,
        Response(),
        key,
        if_match,
        PRINCIPAL,
        cast(Session, session),
    )


def _error(command: str, session: _FakeSession, **kwargs: Any) -> HTTPException:
    with pytest.raises(HTTPException) as caught:
        _call(command, session, **kwargs)
    return caught.value


# --- the state machine: every command from every state ------------------------------------------
_ALLOWED = {
    ("suspend", "active"),
    ("archive", "active"),
    ("archive", "suspended"),
}


@pytest.mark.parametrize("command", ["suspend", "archive"])
@pytest.mark.parametrize("state", STATES)
def test_transition_table_is_the_whole_machine(command: str, state: str) -> None:
    assert be1_registry.class_state_transition_allowed(command, state) is (
        (command, state) in _ALLOWED
    )


def test_there_is_no_reactivate_or_unarchive_command() -> None:
    assert set(be1_registry._STATE_COMMANDS) == {"suspend", "archive"}
    targets = {target for target, _sources in be1_registry._STATE_COMMANDS.values()}
    assert "active" not in targets


@pytest.mark.parametrize("command", ["suspend", "archive"])
@pytest.mark.parametrize("state", STATES)
def test_every_pair_through_the_handler(command: str, state: str) -> None:
    session = _FakeSession(
        classroom=_classroom(state, revision=4), rows=[_row(role="school_admin", class_id=None)]
    )
    if (command, state) in _ALLOWED:
        body = _call(command, session, if_match='"4"')
        target = "suspended" if command == "suspend" else "archived"
        assert body == {
            "contract": "Be1ClassStateV1",
            "class_id": "class-a",
            "state": target,
            "class_revision": 5,
        }
        assert session.classroom.state == target and session.classroom.revision == 5
        assert session.commits == 1
        kinds = sorted(type(row).__name__ for row in session.added)
        assert kinds == [
            "Be1CommandReceiptModel",
            "CoreAggregateRevisionModel",
            "CoreAuditEntryModel",
            "CoreOutboxEventModel",
        ]
        receipt = next(row for row in session.added if isinstance(row, Be1CommandReceiptModel))
        # The receipt keeps only the class id, the state and the revision (no name, no count).
        assert set(receipt.response_json) == {"contract", "class_id", "state", "class_revision"}
    else:
        error = _error(command, session, if_match='"4"')
        assert error.status_code == 409
        assert error.detail["code"] == "INVALID_STATE_TRANSITION"  # type: ignore[index]
        assert session.commits == 0 and session.classroom.state == state
        assert session.classroom.revision == 4


# --- the order of the checks --------------------------------------------------------------------
def test_unknown_class_is_the_uniform_404_before_any_role_check() -> None:
    error = _error("suspend", _FakeSession(classroom=None, role="teacher"))
    assert error.status_code == 404
    assert error.detail["code"] == "RESOURCE_NOT_FOUND"  # type: ignore[index]


def test_unassigned_manager_is_the_same_404_as_an_unknown_class() -> None:
    unknown = _error("suspend", _FakeSession(classroom=None))
    unassigned = _error("suspend", _FakeSession(classroom=_classroom(), rows=[]))
    assert (unassigned.status_code, unassigned.detail) == (unknown.status_code, unknown.detail)


@pytest.mark.parametrize("class_id", ["class-a", None])
def test_teacher_assigned_in_the_organization_is_403_after_the_404_check(
    class_id: str | None,
) -> None:
    session = _FakeSession(
        classroom=_classroom(),
        role="teacher",
        rows=[_row(role="teacher", class_id=class_id)],
    )
    error = _error("archive", session)
    assert error.status_code == 403
    assert error.detail["code"] == "ACTION_NOT_ALLOWED"  # type: ignore[index]


def test_teacher_of_another_class_gets_the_uniform_404() -> None:
    session = _FakeSession(
        classroom=_classroom(),
        role="teacher",
        rows=[_row(role="teacher", class_id="class-other")],
    )
    assert _error("suspend", session).status_code == 404


def test_if_match_is_required_and_strong() -> None:
    session = _FakeSession(classroom=_classroom(), rows=[_row(role="school_admin", class_id=None)])
    assert _error("suspend", session, if_match=None).status_code == 400
    assert _error("suspend", session, if_match="1").status_code == 400
    assert _error("suspend", session, if_match='W/"1"').status_code == 400
    assert session.commits == 0


def test_stale_revision_is_checked_before_the_transition() -> None:
    # An archived class cannot be suspended, but a stale request is told to reload first.
    session = _FakeSession(
        classroom=_classroom("archived", revision=3),
        rows=[_row(role="school_admin", class_id=None)],
    )
    error = _error("suspend", session, if_match='"1"')
    assert error.status_code == 409
    detail = cast(dict[str, Any], error.detail)
    assert detail["code"] == "STALE_REVISION"
    assert detail["current_version"] == 3
    assert session.commits == 0 and session.classroom.state == "archived"


def test_a_stored_receipt_with_another_fingerprint_is_400() -> None:
    receipt = SimpleNamespace(request_fingerprint="0" * 64, response_json={})
    session = _FakeSession(
        classroom=_classroom(),
        rows=[_row(role="school_admin", class_id=None)],
        receipt=receipt,
    )
    error = _error("suspend", session)
    assert error.status_code == 400
    assert error.detail["code"] == "INVALID_IDEMPOTENCY_KEY"  # type: ignore[index]


def test_a_stored_receipt_with_the_same_fingerprint_replays_without_a_write() -> None:
    stored = {
        "contract": "Be1ClassStateV1",
        "class_id": "class-a",
        "state": "suspended",
        "class_revision": 2,
    }
    receipt = SimpleNamespace(
        request_fingerprint=be1_registry._class_state_fingerprint("suspend", 1),
        response_json=stored,
    )
    # The class has moved on (revision 2, suspended): the replay still answers the first result.
    session = _FakeSession(
        classroom=_classroom("suspended", revision=2),
        rows=[_row(role="school_admin", class_id=None)],
        receipt=receipt,
    )
    response = Response()
    request = cast(Any, SimpleNamespace(headers=Headers({"Idempotency-Key": "key-1"})))
    body = be1_registry.suspend_class(
        "class-a", request, response, "key-1", '"1"', PRINCIPAL, cast(Session, session)
    )
    assert body == stored
    assert response.headers["ETag"] == '"2"'
    assert session.commits == 0 and session.added == []


# --- the read/write class guard -----------------------------------------------------------------
class _ClassOnly:
    def __init__(self, row: Any) -> None:
        self._row = row

    def scalar(self, _statement: Any) -> Any:
        return self._row


@pytest.mark.parametrize("write", [True, False])
def test_get_class_missing_is_404_for_a_read_and_a_write(write: bool) -> None:
    with pytest.raises(HTTPException) as caught:
        get_class(cast(Session, _ClassOnly(None)), ORG, "class-a", write=write)
    assert caught.value.status_code == 404


@pytest.mark.parametrize("state", STATES)
def test_get_class_read_sees_every_state(state: str) -> None:
    row = _classroom(state)
    assert get_class(cast(Session, _ClassOnly(row)), ORG, "class-a", write=False) is row


@pytest.mark.parametrize("state", ["suspended", "archived"])
def test_get_class_write_refuses_a_read_only_class_with_409(state: str) -> None:
    with pytest.raises(HTTPException) as caught:
        get_class(cast(Session, _ClassOnly(_classroom(state))), ORG, "class-a")
    assert caught.value.status_code == 409
    assert caught.value.detail["code"] == "INVALID_STATE_TRANSITION"  # type: ignore[index]


def test_get_class_write_is_the_default_and_accepts_an_active_class() -> None:
    row = _classroom("active")
    assert get_class(cast(Session, _ClassOnly(row)), ORG, "class-a") is row


class _Capture:
    def __init__(self) -> None:
        self.statement: Any = None

    def scalar(self, statement: Any) -> Any:
        self.statement = statement
        return _classroom("active")


@pytest.mark.parametrize(("write", "locked"), [(True, True), (False, False)])
def test_get_class_write_reads_the_class_row_for_share_and_a_read_does_not(
    write: bool, locked: bool
) -> None:
    capture = _Capture()
    get_class(cast(Session, capture), ORG, "class-a", write=write)
    sql = str(capture.statement.compile(dialect=cast(Any, PGDialect)()))
    assert ("FOR SHARE" in sql) is locked
    assert "FOR UPDATE" not in sql


def test_archived_class_is_hidden_from_a_teacher_but_not_from_a_manager() -> None:
    archived = _classroom("archived")
    manager = (_row(role="school_admin", class_id=None),)
    teacher = (_row(role="teacher", class_id="class-a"),)
    hide_archived_from_teacher(archived, cast(Any, manager))
    with pytest.raises(HTTPException) as caught:
        hide_archived_from_teacher(archived, cast(Any, teacher))
    assert caught.value.status_code == 404
    for state in ("active", "suspended"):
        hide_archived_from_teacher(_classroom(state), cast(Any, teacher))


# --- the list filter ----------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("requested", "manager", "expected"),
    [
        ("active", True, ("active",)),
        ("suspended", True, ("suspended",)),
        ("archived", True, ("archived",)),
        ("all", True, STATES),
        ("active", False, ("active",)),
        ("suspended", False, ("suspended",)),
        ("archived", False, ()),
        ("all", False, ("active", "suspended")),
    ],
)
def test_listed_states_per_role(requested: str, manager: bool, expected: tuple[str, ...]) -> None:
    assert be1_registry._listed_states(requested, manager=manager) == expected
