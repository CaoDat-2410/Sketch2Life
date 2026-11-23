"""T-7a unit tests: School Manager roster summary and class-scoped Teacher rule (no database).

SRS l.2586 (Profile row), l.864-865 (403 only inside a known scope), l.1640 (cursor lists);
D-066-75 CM-3, CM-4, CM-5, CM-11. A fake session answers each query by the table it reads.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any, cast

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.interfaces.http.api_conventions import decode_time_cursor, encode_cursor
from sketch2life.interfaces.http.routers import be1_registry

ISSUER = "https://issuer.example.test/synthetic"
PRINCIPAL = VerifiedPrincipal(subject="adult-1", issuer=ISSUER, roles=frozenset())
ORG = "org-1"
CLASS = "class-a"
CONSENT_SCOPE = f"be1.consents:{ORG}:{CLASS}"
BASE_TIME = datetime(2026, 11, 19, 8, 0, 0, tzinfo=UTC)


class _Scalars:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def all(self) -> list[Any]:
        return self._rows


class _RosterSession:
    def __init__(
        self,
        identity: Any,
        assignments: list[Any],
        *,
        classroom: Any = None,
        active_count: int = 0,
        profiles: list[Any] | None = None,
        consents: list[Any] | None = None,
    ) -> None:
        self._identity = identity
        self._assignments = assignments
        self._classroom = classroom
        self._active_count = active_count
        self._profiles = profiles or []
        self._consents = consents or []
        self.added: list[Any] = []

    def get(self, _model: Any, _key: Any) -> Any:
        return self._identity

    def scalars(self, statement: Any) -> _Scalars:
        text = str(statement)
        if "be1_organization_assignments" in text:
            return _Scalars(self._assignments)
        if "be1_consent_records" in text:
            return _Scalars(self._consents)
        if "be1_managed_profiles" in text:
            return _Scalars(self._profiles)
        return _Scalars([])

    def scalar(self, statement: Any) -> Any:
        return self._active_count if "count(" in str(statement).lower() else self._classroom

    def add(self, item: Any) -> None:
        self.added.append(item)

    def commit(self) -> None:  # pragma: no cover - a read must not reach it
        raise AssertionError("a roster read must not commit")


def _identity(role: str = "teacher") -> Any:
    return SimpleNamespace(state="active", account_role=role, issuer=ISSUER)


def _row(role: str, class_id: str | None) -> Any:
    return SimpleNamespace(
        organization_id=ORG,
        subject=PRINCIPAL.subject,
        class_id=class_id,
        role=role,
        active=True,
        assignment_id=f"assign-{role}-{class_id}",
    )


def _classroom() -> Any:
    return SimpleNamespace(organization_id=ORG, class_id=CLASS, state="active")


def _manager(class_id: str | None = None, **kwargs: Any) -> _RosterSession:
    return _RosterSession(
        _identity("school_manager"),
        [_row("school_admin", class_id)],
        classroom=kwargs.pop("classroom", _classroom()),
        **kwargs,
    )


def _teacher_side(role: str, class_id: str | None, **kwargs: Any) -> _RosterSession:
    classroom = kwargs.pop("classroom", _classroom())
    return _RosterSession(_identity(), [_row(role, class_id)], classroom=classroom, **kwargs)


def _profiles(session: _RosterSession, class_id: str = CLASS) -> Any:
    return be1_registry.list_profiles(
        ORG, class_id, principal=PRINCIPAL, db=cast(Session, session)
    )


def _consents(
    session: _RosterSession, *, limit: int = 25, cursor: str | None = None, class_id: str = CLASS
) -> Any:
    return be1_registry.list_consents(
        ORG,
        class_id,
        limit=limit,
        cursor=cursor,
        principal=PRINCIPAL,
        db=cast(Session, session),
    )


def _error(call: Any) -> HTTPException:
    with pytest.raises(HTTPException) as caught:
        call()
    return caught.value


def _assert_code(error: HTTPException, status: int, code: str) -> None:
    assert error.status_code == status
    assert isinstance(error.detail, dict)
    assert error.detail["code"] == code


def _consent_row(index: int, *, child_id: str = "child-1") -> Any:
    return SimpleNamespace(
        consent_id=f"consent-{index:03d}",
        child_id=child_id,
        purpose_ref="purpose-secret",
        state="pending",
        recorded_at=BASE_TIME - timedelta(minutes=index),
    )


# --- A09 -----------------------------------------------------------------------------------


@pytest.mark.parametrize("row_class_id", [None, CLASS])
def test_a09_manager_gets_exactly_the_three_key_summary(row_class_id: str | None) -> None:
    body = _profiles(_manager(row_class_id, active_count=4))
    assert body == {
        "contract": "Be1ClassRosterSummaryV1",
        "class_id": CLASS,
        "active_profile_count": 4,
    }
    assert set(body) == {"contract", "class_id", "active_profile_count"}


def test_a09_manager_summary_of_an_empty_class_is_zero_and_writes_nothing() -> None:
    session = _manager(active_count=0)
    assert _profiles(session)["active_profile_count"] == 0
    assert session.added == []


def test_a09_class_scoped_teacher_keeps_the_full_list_shape() -> None:
    body = _profiles(_teacher_side("teacher", CLASS))
    assert body == {"contract": "Be1ManagedProfileListV1", "items": []}
    assert "next_cursor" not in body


@pytest.mark.parametrize(
    ("role", "row_class_id"),
    [
        ("teacher", None),
        ("guide", None),
        ("guide", CLASS),
        ("observer", None),
        ("observer", CLASS),
    ],
)
def test_a09_other_teacher_side_rows_are_403(role: str, row_class_id: str | None) -> None:
    error = _error(lambda: _profiles(_teacher_side(role, row_class_id)))
    _assert_code(error, 403, "ACTION_NOT_ALLOWED")


def test_a09_out_of_scope_callers_get_the_uniform_404() -> None:
    other_class = _teacher_side("teacher", "class-b")
    no_row = _RosterSession(_identity("school_manager"), [], classroom=_classroom())
    parent = _RosterSession(
        _identity("parent"), [_row("school_admin", None)], classroom=_classroom()
    )
    errors = [_error(lambda s=s: _profiles(s)) for s in (other_class, no_row, parent)]
    for error in errors:
        _assert_code(error, 404, "RESOURCE_NOT_FOUND")
    assert len({str(error.detail) for error in errors}) == 1


@pytest.mark.parametrize(
    "make",
    [
        lambda: _manager(classroom=None),
        lambda: _teacher_side("guide", None, classroom=None),
    ],
)
def test_a09_missing_class_is_404_before_any_403(make: Any) -> None:
    _assert_code(_error(lambda: _profiles(make())), 404, "CLASS_NOT_FOUND")


# --- A10 -----------------------------------------------------------------------------------


def test_a10_manager_items_carry_no_child_or_purpose() -> None:
    session = _manager(consents=[_consent_row(1), _consent_row(2)])
    body = _consents(session)
    assert body["contract"] == "Be1ConsentListManagerV1"
    assert body["next_cursor"] is None
    assert body["items"] == [
        {"consent_id": "consent-001", "state": "pending", "effective": False},
        {"consent_id": "consent-002", "state": "pending", "effective": False},
    ]
    assert "child-1" not in str(body) and "purpose-secret" not in str(body)


def test_a10_class_scoped_teacher_keeps_todays_items_and_gains_next_cursor() -> None:
    body = _consents(_teacher_side("teacher", CLASS, consents=[_consent_row(1)]))
    assert body["contract"] == "Be1ConsentListV1"
    assert body["next_cursor"] is None
    assert body["items"] == [
        {
            "consent_id": "consent-001",
            "child_id": "child-1",
            "purpose_ref": "purpose-secret",
            "state": "pending",
            "effective": False,
        }
    ]


@pytest.mark.parametrize(
    ("role", "row_class_id"),
    [("teacher", None), ("guide", None), ("guide", CLASS), ("observer", None), ("observer", CLASS)],
)
def test_a10_other_teacher_side_rows_are_403(role: str, row_class_id: str | None) -> None:
    session = _teacher_side(role, row_class_id, consents=[_consent_row(1)])
    _assert_code(_error(lambda: _consents(session)), 403, "ACTION_NOT_ALLOWED")


def test_a10_out_of_scope_and_missing_class() -> None:
    other_class = _teacher_side("teacher", "class-b")
    _assert_code(_error(lambda: _consents(other_class)), 404, "RESOURCE_NOT_FOUND")
    _assert_code(
        _error(lambda: _consents(_manager(classroom=None))), 404, "CLASS_NOT_FOUND"
    )
    _assert_code(
        _error(lambda: _consents(_teacher_side("observer", None, classroom=None))),
        404,
        "CLASS_NOT_FOUND",
    )


def test_a10_next_cursor_is_built_from_the_last_returned_row() -> None:
    rows = [_consent_row(1), _consent_row(2), _consent_row(3)]
    body = _consents(_manager(consents=rows), limit=2)
    assert [item["consent_id"] for item in body["items"]] == ["consent-001", "consent-002"]
    assert body["next_cursor"] is not None
    moment, item_id = decode_time_cursor(body["next_cursor"], scope=CONSENT_SCOPE)
    assert (moment, item_id) == (rows[1].recorded_at, "consent-002")
    exact = _consents(_manager(consents=rows[:2]), limit=2)
    assert exact["next_cursor"] is None


def test_a10_cursor_is_rejected_after_the_scope_checks() -> None:
    wrong_scope = encode_cursor(
        scope="be1.classes:org-1", sort_key=BASE_TIME.isoformat(), item_id="x"
    )
    error = _error(lambda: _consents(_manager(), cursor=wrong_scope))
    detail: Any = error.detail
    assert error.status_code == 400
    assert detail == {
        "code": "INVALID_REQUEST",
        "field_errors": [{"field": "cursor", "code": "INVALID_FORMAT"}],
    }
    # An out-of-scope caller gets the uniform 404 whatever the cursor says.
    _assert_code(
        _error(lambda: _consents(_teacher_side("teacher", "class-b"), cursor="%%%")),
        404,
        "RESOURCE_NOT_FOUND",
    )
