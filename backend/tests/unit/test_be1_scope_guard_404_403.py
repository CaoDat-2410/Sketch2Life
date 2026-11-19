"""CONV-1 unit tests for the BE1 scope guard 404/403 rule (D-066-68 C-D4, D-066-71 CV-5).

Out-of-scope access gives one uniform 404 RESOURCE_NOT_FOUND; only a role refusal inside an
assigned organization and class gives 403 ACTION_NOT_ALLOWED. Uses a fake session, no database.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import pytest
from fastapi import HTTPException, Response
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.interfaces.http.routers import be1_registry
from sketch2life.interfaces.http.routers.be1_common import require_assignment

ISSUER = "https://issuer.example.test/synthetic"
PRINCIPAL = VerifiedPrincipal(subject="adult-1", issuer=ISSUER, roles=frozenset())
ORG = "org-1"


class _Scalars:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def all(self) -> list[Any]:
        return self._rows


class _FakeSession:
    def __init__(self, identity: Any, rows: list[Any], classroom: Any = None) -> None:
        self._identity = identity
        self._rows = rows
        self._classroom = classroom

    def get(self, _model: Any, _key: Any) -> Any:
        return self._identity

    def scalars(self, _statement: Any) -> _Scalars:
        return _Scalars(self._rows)

    def scalar(self, _statement: Any) -> Any:
        return self._classroom


def _identity(*, state: str = "active", role: str = "teacher", issuer: str = ISSUER) -> Any:
    return SimpleNamespace(state=state, account_role=role, issuer=issuer)


def _row(*, role: str = "teacher", class_id: str | None = "class-a", active: bool = True) -> Any:
    return SimpleNamespace(
        organization_id=ORG,
        subject=PRINCIPAL.subject,
        class_id=class_id,
        role=role,
        active=active,
        assignment_id=f"assign-{role}-{class_id}",
    )


def _guard(session: _FakeSession, **kwargs: Any) -> HTTPException:
    with pytest.raises(HTTPException) as caught:
        require_assignment(cast(Session, session), PRINCIPAL, ORG, **kwargs)
    return caught.value


def _assert_not_found(error: HTTPException) -> None:
    assert error.status_code == 404
    assert isinstance(error.detail, dict)
    assert error.detail["code"] == "RESOURCE_NOT_FOUND"


def test_missing_identity_is_404() -> None:
    _assert_not_found(_guard(_FakeSession(None, [_row()])))


def test_inactive_identity_is_404() -> None:
    _assert_not_found(_guard(_FakeSession(_identity(state="disabled"), [_row()])))


def test_wrong_account_role_is_404() -> None:
    _assert_not_found(_guard(_FakeSession(_identity(role="parent"), [_row()])))


def test_organization_not_covered_is_404() -> None:
    _assert_not_found(_guard(_FakeSession(_identity(), [])))


def test_class_not_covered_is_404() -> None:
    session = _FakeSession(_identity(), [_row(class_id="class-a")])
    _assert_not_found(_guard(session, class_id="class-b"))


def test_issuer_mismatch_is_404() -> None:
    session = _FakeSession(_identity(issuer="https://other.example.test"), [_row()])
    _assert_not_found(_guard(session, class_id="class-a"))


def test_role_refused_in_scope_is_403() -> None:
    session = _FakeSession(_identity(), [_row(role="observer", class_id="class-a")])
    error = _guard(session, roles={"teacher"}, class_id="class-a")
    assert error.status_code == 403
    assert isinstance(error.detail, dict)
    assert error.detail["code"] == "ACTION_NOT_ALLOWED"


def test_in_scope_teacher_is_allowed() -> None:
    session = _FakeSession(_identity(), [_row(class_id="class-a")])
    allowed = require_assignment(
        cast(Session, session), PRINCIPAL, ORG, roles={"teacher"}, class_id="class-a"
    )
    assert len(allowed) == 1


def _registry_error(call: Any) -> HTTPException:
    with pytest.raises(HTTPException) as caught:
        call()
    return caught.value


def test_assign_class_teacher_missing_and_unassigned_class_look_the_same() -> None:
    missing = _registry_error(
        lambda: be1_registry.assign_class_teacher(
            "class-x",
            cast(Any, SimpleNamespace()),
            # FEAT-066 M9-B: the command now takes the response, key and If-Match too.
            response=Response(),
            idempotency_key="synthetic-key",
            if_match='"1"',
            principal=PRINCIPAL,
            db=cast(Session, _FakeSession(_identity(role="school_manager"), [], classroom=None)),
        )
    )
    unassigned = _registry_error(
        lambda: be1_registry.assign_class_teacher(
            "class-x",
            cast(Any, SimpleNamespace()),
            # FEAT-066 M9-B: the command now takes the response, key and If-Match too.
            response=Response(),
            idempotency_key="synthetic-key",
            if_match='"1"',
            principal=PRINCIPAL,
            db=cast(
                Session,
                _FakeSession(
                    _identity(role="school_manager"),
                    [],
                    classroom=SimpleNamespace(organization_id=ORG),
                ),
            ),
        )
    )
    assert (missing.status_code, missing.detail) == (unassigned.status_code, unassigned.detail)
    _assert_not_found(missing)


def test_create_profile_missing_and_unassigned_class_look_the_same() -> None:
    runtime = SimpleNamespace(settings=SimpleNamespace(env="test", synthetic_pilot_enabled=True))
    payload = SimpleNamespace(class_id="class-x")

    def call(classroom: Any) -> HTTPException:
        return _registry_error(
            lambda: be1_registry.create_profile(
                ORG,
                "class-x",
                cast(Any, payload),
                principal=PRINCIPAL,
                runtime=cast(Any, runtime),
                db=cast(Session, _FakeSession(_identity(), [], classroom=classroom)),
            )
        )

    missing = call(None)
    unassigned = call(SimpleNamespace(organization_id=ORG, class_id="class-x"))
    assert (missing.status_code, missing.detail) == (unassigned.status_code, unassigned.detail)
    _assert_not_found(missing)


def test_registry_wrapper_passes_role_refusal_through() -> None:
    session = _FakeSession(_identity(), [_row(role="observer", class_id="class-a")])
    with pytest.raises(HTTPException) as caught:
        be1_registry._require_m2_assignment(
            cast(Session, session), PRINCIPAL, ORG, roles={"teacher"}, class_id="class-a"
        )
    assert caught.value.status_code == 403
