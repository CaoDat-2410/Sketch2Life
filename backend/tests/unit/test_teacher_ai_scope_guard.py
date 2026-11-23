"""FEAT-066 T0.9: the Teacher AI routes use the uniform BE1 scope guard (SRS l.864-865, C-D4).

An out-of-scope caller (no identity, inactive, issuer mismatch, wrong account role, no active
assignment in the organization) gets the uniform 404 RESOURCE_NOT_FOUND. A caller assigned in the
organization with a role other than Teacher gets 403 ACTION_NOT_ALLOWED. The guard runs before the
``modal_dev`` gate, so an out-of-scope caller never learns the provider configuration. Fake
session, no database.
"""

from __future__ import annotations

from collections.abc import Callable
from types import SimpleNamespace
from typing import Any, cast

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.interfaces.http.routers import teacher_ai

ISSUER = "https://issuer.example.test/synthetic"
PRINCIPAL = VerifiedPrincipal(subject="adult-1", issuer=ISSUER, roles=frozenset())
ORG = "org-1"


class _Scalars:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def all(self) -> list[Any]:
        return self._rows


class _FakeSession:
    def __init__(self, identity: Any, rows: list[Any]) -> None:
        self._identity = identity
        self._rows = rows

    def get(self, _model: Any, _key: Any) -> Any:
        return self._identity

    def scalars(self, _statement: Any) -> _Scalars:
        return _Scalars(self._rows)


def _identity(*, state: str = "active", role: str = "teacher", issuer: str = ISSUER) -> Any:
    return SimpleNamespace(state=state, account_role=role, issuer=issuer)


def _row(*, role: str = "teacher", class_id: str | None = None) -> Any:
    return SimpleNamespace(
        organization_id=ORG,
        subject=PRINCIPAL.subject,
        class_id=class_id,
        role=role,
        active=True,
        assignment_id=f"assign-{role}-{class_id}",
    )


HANDLERS = (
    teacher_ai.suggest_lesson_plan,
    teacher_ai.generate_sketch_deck,
    teacher_ai.generate_lesson_visual,
)


def _call(handler: Callable[..., Any], session: _FakeSession) -> HTTPException:
    # The guard runs before the payload is read, so a placeholder payload is enough here.
    with pytest.raises(HTTPException) as caught:
        handler(ORG, cast(Any, SimpleNamespace()), PRINCIPAL, cast(Session, session))
    return caught.value


def _code(error: HTTPException) -> object:
    assert isinstance(error.detail, dict)
    return error.detail["code"]


def _provider(monkeypatch: pytest.MonkeyPatch, *, ai_provider: str, env: str = "test") -> None:
    monkeypatch.setattr(
        teacher_ai, "get_settings", lambda: SimpleNamespace(ai_provider=ai_provider, env=env)
    )


@pytest.mark.parametrize("handler", HANDLERS)
@pytest.mark.parametrize(
    "session",
    [
        pytest.param(_FakeSession(None, [_row()]), id="no-identity"),
        pytest.param(_FakeSession(_identity(state="disabled"), [_row()]), id="inactive"),
        pytest.param(
            _FakeSession(_identity(issuer="https://other.example.test"), [_row()]),
            id="issuer-mismatch",
        ),
        pytest.param(_FakeSession(_identity(role="parent"), [_row()]), id="parent-account"),
        pytest.param(
            _FakeSession(_identity(role="platform_admin"), [_row()]), id="platform-admin-account"
        ),
        pytest.param(_FakeSession(_identity(), []), id="teacher-not-assigned"),
    ],
)
def test_out_of_scope_callers_get_the_uniform_404(
    monkeypatch: pytest.MonkeyPatch, handler: Callable[..., Any], session: _FakeSession
) -> None:
    # Provider configuration must not matter: the guard runs first.
    _provider(monkeypatch, ai_provider="modal_dev")
    error = _call(handler, session)
    assert error.status_code == 404
    assert _code(error) == "RESOURCE_NOT_FOUND"
    _provider(monkeypatch, ai_provider="none")
    again = _call(handler, session)
    assert (again.status_code, _code(again)) == (404, "RESOURCE_NOT_FOUND")


@pytest.mark.parametrize("handler", HANDLERS)
@pytest.mark.parametrize(
    "session",
    [
        pytest.param(
            _FakeSession(_identity(role="school_manager"), [_row(role="school_admin")]),
            id="manager-assigned-in-organization",
        ),
        pytest.param(_FakeSession(_identity(), [_row(role="guide")]), id="guide-only"),
        pytest.param(_FakeSession(_identity(), [_row(role="observer")]), id="observer-only"),
    ],
)
def test_role_refused_inside_the_organization_is_403(
    monkeypatch: pytest.MonkeyPatch, handler: Callable[..., Any], session: _FakeSession
) -> None:
    _provider(monkeypatch, ai_provider="none")
    error = _call(handler, session)
    assert error.status_code == 403
    assert _code(error) == "ACTION_NOT_ALLOWED"


@pytest.mark.parametrize("handler", HANDLERS)
@pytest.mark.parametrize(
    "rows",
    [
        pytest.param([_row(role="teacher", class_id=None)], id="organization-wide"),
        pytest.param([_row(role="teacher", class_id="class-a")], id="class-scoped"),
    ],
)
def test_assigned_teacher_passes_the_guard_and_reaches_the_provider_gate(
    monkeypatch: pytest.MonkeyPatch, handler: Callable[..., Any], rows: list[Any]
) -> None:
    _provider(monkeypatch, ai_provider="none")
    error = _call(handler, _FakeSession(_identity(), rows))
    assert error.status_code == 503
    assert _code(error) == "MODAL_AI_NOT_ENABLED"


def test_modal_gate_also_requires_local_or_test_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _provider(monkeypatch, ai_provider="modal_dev", env="production")
    error = _call(HANDLERS[0], _FakeSession(_identity(), [_row()]))
    assert (error.status_code, _code(error)) == (503, "MODAL_AI_NOT_ENABLED")
