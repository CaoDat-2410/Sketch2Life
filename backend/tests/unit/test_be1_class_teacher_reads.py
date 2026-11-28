"""T-7a2 unit tests: child-profile reads need the class's own Teacher row (SRS l.541, l.2586).

The pilot-profiles list, the session roster and the portfolio read answer 403
``ACTION_NOT_ALLOWED`` to a caller who is in scope (its rows cover the class) but holds no active
``teacher`` row of exactly that class (an org-wide ``teacher`` row, a guide, an observer, a School
Manager). A caller whose rows do not cover the class gets the uniform 404 (SRS l.864-865, AC-27).
Uses a fake session keyed by table name, no database.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import pytest
from fastapi import HTTPException, Response
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.interfaces.http.routers import be1_records, be1_registry, be1_sessions
from sketch2life.interfaces.http.routers.be1_common import (
    is_class_teacher_row,
    require_assignment,
    require_class_teacher_row,
)

ISSUER = "https://issuer.example.test/synthetic"
PRINCIPAL = VerifiedPrincipal(subject="adult-1", issuer=ISSUER, roles=frozenset())
ORG = "org-1"
CLASS = "class-a"
SESSION = "session-1"
CHILD = "child-1"
Case = tuple[str, dict[str, Any], list[Any]]


class _Scalars:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def all(self) -> list[Any]:
        return self._rows


class _FakeSession:
    """Answers each query by the table it reads, so the call order of a route cannot matter."""

    def __init__(
        self,
        identity: Any,
        rows: list[Any],
        *,
        classroom: Any = None,
        session: Any = None,
        profile: Any = None,
    ) -> None:
        self._identity = identity
        self._rows = rows
        self._classroom = classroom
        self._session = session
        self._profile = profile
        self.added: list[Any] = []

    def get(self, _model: Any, _key: Any) -> Any:
        return self._identity

    def scalars(self, statement: Any) -> _Scalars:
        text = str(statement)
        return _Scalars(self._rows if "FROM be1_organization_assignments" in text else [])

    def scalar(self, statement: Any) -> Any:
        text = str(statement)
        if "FROM be1_classrooms" in text:
            return self._classroom
        if "FROM be1_sessions" in text:
            return self._session
        if "FROM be1_managed_profiles" in text:
            return self._profile
        return None

    def add(self, row: Any) -> None:
        self.added.append(row)

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass


def _identity(*, state: str = "active", role: str = "teacher", issuer: str = ISSUER) -> Any:
    return SimpleNamespace(state=state, account_role=role, issuer=issuer)


def _row(*, role: str = "teacher", class_id: str | None = CLASS, active: bool = True) -> Any:
    return SimpleNamespace(
        organization_id=ORG,
        subject=PRINCIPAL.subject,
        class_id=class_id,
        role=role,
        active=active,
        assignment_id=f"assign-{role}-{class_id}",
    )


def _classroom(state: str = "active") -> Any:
    return SimpleNamespace(organization_id=ORG, class_id=CLASS, state=state)


def _lobby_session() -> Any:
    return SimpleNamespace(
        organization_id=ORG,
        session_id=SESSION,
        class_id=CLASS,
        state="lobby",
        revision=1,
        configuration={},
    )


def _fake(identity: Any, rows: list[Any], **kwargs: Any) -> _FakeSession:
    kwargs.setdefault("classroom", _classroom())
    kwargs.setdefault("session", _lobby_session())
    return _FakeSession(identity, rows, **kwargs)


# --- the actors of plan section 3 -------------------------------------------------------------
# (id, identity kwargs, rows) -> the status of every route is the same for these callers.
ASSIGNED: Case = ("assigned", {}, [_row(class_id=CLASS)])
ASSIGNED_AND_ORGWIDE: Case = (
    "assigned_and_orgwide",
    {},
    [_row(class_id=None), _row(class_id=CLASS)],
)
ORGWIDE_TEACHER: Case = ("orgwide_teacher", {}, [_row(class_id=None)])
ORGWIDE_GUIDE: Case = ("orgwide_guide", {}, [_row(role="guide", class_id=None)])
ORGWIDE_OBSERVER: Case = ("orgwide_observer", {}, [_row(role="observer", class_id=None)])
CLASS_GUIDE: Case = ("class_guide", {}, [_row(role="guide", class_id=CLASS)])
CLASS_OBSERVER: Case = ("class_observer", {}, [_row(role="observer", class_id=CLASS)])
# Guide of this class plus a Teacher row of another class: `roles={"teacher"}` removes both.
GUIDE_PLUS_OTHER_TEACHER: Case = (
    "guide_plus_other_class_teacher",
    {},
    [_row(role="guide", class_id=CLASS), _row(class_id="class-b")],
)
MANAGER_ORGWIDE: Case = (
    "manager",
    {"role": "school_manager"},
    [_row(role="school_admin", class_id=None)],
)
MANAGER_CLASS: Case = (
    "manager_class_row",
    {"role": "school_manager"},
    [_row(role="school_admin", class_id=CLASS)],
)

FORBIDDEN_403: list[Case] = [
    ORGWIDE_TEACHER,
    ORGWIDE_GUIDE,
    ORGWIDE_OBSERVER,
    CLASS_GUIDE,
    CLASS_OBSERVER,
    GUIDE_PLUS_OTHER_TEACHER,
    MANAGER_ORGWIDE,
    MANAGER_CLASS,
]
NOT_FOUND_404: list[Case] = [
    ("other_class_teacher", {}, [_row(class_id="class-b")]),
    ("revoked_row", {}, []),  # require_assignment keeps only active rows; the query returns none
    ("no_rows", {}, []),
    ("parent_account", {"role": "parent"}, [_row(class_id=None)]),
    ("platform_admin", {"role": "platform_admin"}, [_row(role="school_admin", class_id=None)]),
    ("inactive_identity", {"state": "disabled"}, [_row(class_id=CLASS)]),
    ("issuer_mismatch", {"issuer": "https://other.example.test"}, [_row(class_id=CLASS)]),
    ("manager_without_rows", {"role": "school_manager"}, []),
]


def _ids(cases: list[Case]) -> list[str]:
    return [case[0] for case in cases]


def _session_for(case: Case, **kwargs: Any) -> _FakeSession:
    _name, identity_kwargs, rows = case
    return _fake(_identity(**identity_kwargs), rows, **kwargs)


# --- the helper alone -------------------------------------------------------------------------


def test_helper_passes_the_class_teacher_row_and_a_mixed_set() -> None:
    require_class_teacher_row(cast(Any, (_row(class_id=CLASS),)), CLASS)
    require_class_teacher_row(cast(Any, (_row(class_id=None), _row(class_id=CLASS))), CLASS)
    assert is_class_teacher_row(cast(Any, (_row(class_id=CLASS),)), CLASS) is True


@pytest.mark.parametrize(
    "rows",
    [
        [_row(class_id=None)],
        [_row(role="guide", class_id=CLASS)],
        [_row(role="observer", class_id=CLASS)],
        [_row(role="school_admin", class_id=None)],
        [_row(role="school_admin", class_id=CLASS)],
        [_row(class_id="class-b")],
        [],
    ],
)
def test_helper_refuses_every_other_row_with_403(rows: list[Any]) -> None:
    with pytest.raises(HTTPException) as caught:
        require_class_teacher_row(cast(Any, tuple(rows)), CLASS)
    _assert_forbidden(caught.value)
    assert is_class_teacher_row(cast(Any, tuple(rows)), CLASS) is False


# --- the three routes -------------------------------------------------------------------------


def _assert_forbidden(error: HTTPException) -> None:
    assert error.status_code == 403
    assert isinstance(error.detail, dict)
    assert error.detail == {
        "code": "ACTION_NOT_ALLOWED",
        "message": "The action is not allowed for this role",
    }


def _assert_not_found(error: HTTPException) -> None:
    assert error.status_code == 404
    assert isinstance(error.detail, dict)
    assert error.detail["code"] == "RESOURCE_NOT_FOUND"


def _pilot(session: _FakeSession, *, env: str = "staging") -> Any:
    runtime = SimpleNamespace(settings=SimpleNamespace(env=env, synthetic_pilot_enabled=True))
    return be1_registry.list_pilot_profiles(
        ORG,
        SESSION,
        principal=PRINCIPAL,
        runtime=cast(Any, runtime),
        db=cast(Session, session),
    )


def _roster(session: _FakeSession) -> Any:
    return be1_sessions.read_session_roster(
        ORG, SESSION, principal=PRINCIPAL, db=cast(Session, session)
    )


def _portfolio(session: _FakeSession) -> Any:
    return be1_records.read_portfolio(
        ORG, CLASS, CHILD, Response(), principal=PRINCIPAL, db=cast(Session, session)
    )


ROUTES = {"pilot_profiles": _pilot, "roster": _roster, "portfolio": _portfolio}


def _error(call: Any, session: _FakeSession) -> HTTPException:
    with pytest.raises(HTTPException) as caught:
        call(session)
    return caught.value


@pytest.mark.parametrize("route", sorted(ROUTES))
@pytest.mark.parametrize("case", FORBIDDEN_403, ids=_ids(FORBIDDEN_403))
def test_in_scope_caller_without_the_class_teacher_row_is_403(route: str, case: Any) -> None:
    _assert_forbidden(_error(ROUTES[route], _session_for(case)))


@pytest.mark.parametrize("route", sorted(ROUTES))
@pytest.mark.parametrize("case", NOT_FOUND_404, ids=_ids(NOT_FOUND_404))
def test_caller_with_no_covering_row_is_the_uniform_404(route: str, case: Any) -> None:
    _assert_not_found(_error(ROUTES[route], _session_for(case)))


_ASSIGNED_CASES: list[Case] = [ASSIGNED, ASSIGNED_AND_ORGWIDE]


@pytest.mark.parametrize("case", _ASSIGNED_CASES, ids=_ids(_ASSIGNED_CASES))
def test_assigned_teacher_passes_every_guard(case: Any) -> None:
    # Pilot profiles: past the guard, the staging environment answers the lookup-disabled 409.
    pilot = _error(_pilot, _session_for(case))
    assert pilot.status_code == 409
    assert isinstance(pilot.detail, dict)
    assert pilot.detail["code"] == "PILOT_PROFILE_LOOKUP_UNAVAILABLE"
    # Roster: the fake has no members, so the body is empty but present.
    body = _roster(_session_for(case))
    assert body["contract"] == "Be1SessionRosterV1"
    assert body["members"] == []
    # Portfolio: no profile row -> 404 PROFILE_NOT_FOUND; with a profile -> 409.
    missing = _error(_portfolio, _session_for(case))
    assert missing.status_code == 404
    assert isinstance(missing.detail, dict)
    assert missing.detail["code"] == "PROFILE_NOT_FOUND"
    present = _error(
        _portfolio,
        _session_for(
            case,
            profile=SimpleNamespace(
                child_id=CHILD,
                organization_id=ORG,
                class_id=CLASS,
                data_origin="LEGACY_UNCLASSIFIED",
                consent_purpose_ref=None,
            ),
        ),
    )
    assert present.status_code == 409
    assert isinstance(present.detail, dict)
    assert present.detail["code"] == "CONSENT_NOT_EFFECTIVE"


# --- order ------------------------------------------------------------------------------------


def test_pilot_profiles_403_comes_before_the_pilot_env_and_lobby_409s() -> None:
    session = _session_for(ORGWIDE_TEACHER)
    _assert_forbidden(_error(lambda s: _pilot(s, env="staging"), session))
    _assert_forbidden(_error(lambda s: _pilot(s, env="local"), session))
    started = SimpleNamespace(**{**vars(_lobby_session()), "state": "active"})
    _assert_forbidden(_error(_pilot, _session_for(ORGWIDE_TEACHER, session=started)))


def test_unknown_session_is_404_before_the_403_for_every_caller() -> None:
    for case in (ORGWIDE_TEACHER, MANAGER_ORGWIDE, ASSIGNED):
        for route in (_pilot, _roster):
            error = _error(route, _session_for(case, session=None))
            assert error.status_code == 404
            assert isinstance(error.detail, dict)
            assert error.detail["code"] == "SESSION_NOT_FOUND"


def test_portfolio_unknown_class_is_404_before_the_403() -> None:
    for case in (ORGWIDE_TEACHER, MANAGER_ORGWIDE, CLASS_GUIDE):
        error = _error(_portfolio, _session_for(case, classroom=None))
        assert error.status_code == 404
        assert isinstance(error.detail, dict)
        assert error.detail["code"] == "CLASS_NOT_FOUND"


def test_portfolio_403_comes_before_the_profile_lookup() -> None:
    # An unknown child and a known child give the same 403 to the Manager: no existence oracle.
    unknown = _error(_portfolio, _session_for(MANAGER_ORGWIDE, profile=None))
    known = _error(
        _portfolio, _session_for(MANAGER_ORGWIDE, profile=SimpleNamespace(child_id=CHILD))
    )
    _assert_forbidden(unknown)
    assert (unknown.status_code, unknown.detail) == (known.status_code, known.detail)


def test_portfolio_archived_class_is_404_for_a_teacher_and_403_for_the_manager() -> None:
    archived = _classroom("archived")
    _assert_not_found_class(_error(_portfolio, _session_for(ORGWIDE_TEACHER, classroom=archived)))
    _assert_not_found_class(_error(_portfolio, _session_for(ASSIGNED, classroom=archived)))
    _assert_forbidden(_error(_portfolio, _session_for(MANAGER_ORGWIDE, classroom=archived)))


def _assert_not_found_class(error: HTTPException) -> None:
    assert error.status_code == 404
    assert isinstance(error.detail, dict)
    assert error.detail["code"] == "CLASS_NOT_FOUND"


# --- require_assignment is unchanged (the helper only narrows its output) -----------------------


def test_require_assignment_still_lets_the_orgwide_teacher_row_through() -> None:
    session = _session_for(ORGWIDE_TEACHER)
    rows = require_assignment(
        cast(Session, session), PRINCIPAL, ORG, roles={"teacher"}, class_id=CLASS
    )
    assert len(rows) == 1 and rows[0].class_id is None
