"""School Manager opaque roster references: scope and response privacy (no database)."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.interfaces.http.routers import be1_registry
from sketch2life.interfaces.http.routers.be1_common import failure

ORG = "synthetic-org"
PRINCIPAL = VerifiedPrincipal(
    subject="synthetic-manager", issuer="synthetic-issuer", roles=frozenset(), token_id="t"
)


class _Rows:
    def __init__(self, rows: list[SimpleNamespace]) -> None:
        self._rows = rows

    def all(self) -> list[SimpleNamespace]:
        return self._rows


class _RefSession:
    def __init__(self, rows: list[SimpleNamespace]) -> None:
        self.rows = rows
        self.statement: object | None = None

    def scalar(self, _statement: object) -> SimpleNamespace:
        return SimpleNamespace(class_id="class-a", organization_id=ORG, state="active")

    def execute(self, statement: object) -> _Rows:
        self.statement = statement
        return _Rows(self.rows)


def _refs(
    db: _RefSession,
    *,
    organization_id: str = ORG,
    class_id: str = "class-a",
    limit: int = 25,
    cursor: str | None = None,
) -> dict[str, object]:
    return be1_registry.list_profile_refs(
        organization_id,
        class_id,
        limit,
        cursor,
        PRINCIPAL,
        cast(Session, db),
    )


def test_manager_ref_list_selects_only_active_enrolled_references(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authorization: dict[str, Any] = {}

    def allow_manager(
        _db: object,
        _principal: object,
        organization_id: str,
        *,
        roles: set[str],
        class_id: str,
    ) -> tuple[SimpleNamespace, ...]:
        authorization.update(organization_id=organization_id, roles=roles, class_id=class_id)
        return (SimpleNamespace(role="school_admin", class_id=None),)

    monkeypatch.setattr(be1_registry, "_require_m2_assignment", allow_manager)
    db = _RefSession(
        [
            SimpleNamespace(child_id="opaque-ref-1", created_at=datetime(2026, 1, 1, tzinfo=UTC)),
            SimpleNamespace(child_id="opaque-ref-2", created_at=datetime(2026, 1, 2, tzinfo=UTC)),
        ]
    )

    response = _refs(db, limit=1)

    assert authorization == {
        "organization_id": ORG,
        "roles": {"school_admin"},
        "class_id": "class-a",
    }
    assert response["contract"] == "Be1ClassProfileRefListV1"
    assert response["class_id"] == "class-a"
    assert response["items"] == [{"child_id": "opaque-ref-1"}]
    assert response["next_cursor"]
    assert set(cast("list[dict[str, object]]", response["items"])[0]) == {"child_id"}
    sql = str(db.statement)
    assert "be1_enrollments" in sql
    assert "be1_enrollments.state" in sql
    assert "be1_managed_profiles.state" in sql
    assert "display_name" not in sql and "age_months" not in sql


@pytest.mark.parametrize("status_code", [403, 404])
def test_ref_list_propagates_teacher_refusal_and_uniform_scope_not_found(
    monkeypatch: pytest.MonkeyPatch, status_code: int
) -> None:
    def refuse(*_args: object, **_kwargs: object) -> None:
        if status_code == 403:
            raise failure(403, "ACTION_NOT_ALLOWED", "The action is not allowed for this role")
        raise be1_registry._scope_denied()

    monkeypatch.setattr(be1_registry, "_require_m2_assignment", refuse)
    db = _RefSession([])

    with pytest.raises(HTTPException) as caught:
        _refs(db)

    assert caught.value.status_code == status_code
    if status_code == 403:
        assert caught.value.detail["code"] == "ACTION_NOT_ALLOWED"
    else:
        assert caught.value.detail == {
            "code": "RESOURCE_NOT_FOUND",
            "message": "The requested resource was not found",
        }
    assert db.statement is None


def test_profile_ref_cursor_is_decoded_with_organization_and_class_scope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scopes: list[tuple[str, str]] = []

    def decode(cursor: str, *, scope: str) -> tuple[datetime, str]:
        scopes.append((cursor, scope))
        return datetime(2026, 1, 1, tzinfo=UTC), "after-ref"

    monkeypatch.setattr(be1_registry, "_require_m2_assignment", lambda *_a, **_k: ())
    monkeypatch.setattr(be1_registry, "decode_time_cursor", decode)
    db = _RefSession(
        [SimpleNamespace(child_id="opaque-ref", created_at=datetime(2026, 1, 2, tzinfo=UTC))]
    )

    response = _refs(db, organization_id="org-two", class_id="class-two", cursor="next-page")

    assert scopes == [("next-page", "be1.profile-refs:org-two:class-two")]
    assert response["items"] == [{"child_id": "opaque-ref"}]
