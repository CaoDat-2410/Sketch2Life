from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.lesson_library.service import LessonLibraryError
from sketch2life.infrastructure.persistence.be1_models import OrganizationAssignmentModel
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.routers.lesson_library import get_lesson_library_service

_BASE = "/api/lesson-library/v1"
_ORG = "synthetic-parent-group-org"
_GROUP = "synthetic-parent-group-01"
_ISSUER = "synthetic-parent-group-issuer"


class _Rows:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def all(self) -> list[Any]:
        return self._rows


class _MembershipDb:
    def __init__(self, *, actor: str, role: str, assigned: bool) -> None:
        self.identity = SimpleNamespace(state="active", account_role=role, issuer=_ISSUER)
        self.assignment = OrganizationAssignmentModel(
            assignment_id="synthetic-parent-group-assignment",
            organization_id=_ORG,
            subject=actor,
            class_id=None,
            role="school_admin",
            active=True,
        )
        self.assigned = assigned

    def get(self, _model: Any, _subject: str) -> Any:
        return self.identity

    def scalars(self, _statement: Any) -> _Rows:
        return _Rows([self.assignment] if self.assigned else [])


class _MembershipService:
    def __init__(
        self,
        *,
        responses: dict[str, dict[str, Any]] | None = None,
        errors: dict[str, LessonLibraryError] | None = None,
    ) -> None:
        self.responses = responses or {}
        self.errors = errors or {}
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def _call(self, name: str, **kwargs: Any) -> dict[str, Any]:
        self.calls.append((name, kwargs))
        if name in self.errors:
            raise self.errors[name]
        return self.responses[name]

    def decline_parent_group_invitation(self, **kwargs: Any) -> dict[str, Any]:
        return self._call("decline_parent_group_invitation", **kwargs)

    def list_parent_group_memberships(self, **kwargs: Any) -> dict[str, Any]:
        return self._call("list_parent_group_memberships", **kwargs)

    def list_parent_group_members(self, **kwargs: Any) -> dict[str, Any]:
        return self._call("list_parent_group_members", **kwargs)

    def revoke_parent_group_membership(self, **kwargs: Any) -> dict[str, Any]:
        return self._call("revoke_parent_group_membership", **kwargs)


def _membership(*, state: str, revision: int = 2) -> dict[str, Any]:
    now = datetime.now(UTC)
    return {
        "contract": "ParentGroupMembershipV1",
        "membership_id": "synthetic-membership-01",
        "parent_group_id": _GROUP,
        "organization_id": _ORG,
        "state": state,
        "invited_at": now,
        "expires_at": now + timedelta(days=30),
        "accepted_at": now if state == "ACTIVE" else None,
        "revision": revision,
    }


@contextmanager
def _client(
    service: _MembershipService,
    *,
    actor: str = "synthetic-parent",
    role: str = "parent",
    assigned: bool = True,
) -> Iterator[TestClient]:
    application = create_app()
    principal = VerifiedPrincipal(
        subject=actor,
        issuer=_ISSUER,
        roles=frozenset(),
        token_id="synthetic-parent-group-token",
    )
    db = _MembershipDb(actor=actor, role=role, assigned=assigned)
    application.dependency_overrides[get_verified_adult] = lambda: principal
    application.dependency_overrides[get_db] = lambda: db
    application.dependency_overrides[get_lesson_library_service] = lambda: service
    try:
        with TestClient(application) as client:
            yield client
    finally:
        application.dependency_overrides.clear()


def test_parent_decline_and_own_active_membership_routes() -> None:
    membership = _membership(state="DECLINED")
    active_page = {
        "contract": "ParentGroupMembershipPageV1",
        "items": [_membership(state="ACTIVE")],
        "next_cursor": "scoped-cursor",
    }
    service = _MembershipService(
        responses={
            "decline_parent_group_invitation": membership,
            "list_parent_group_memberships": active_page,
        }
    )
    with _client(service) as client:
        declined = client.post(
            f"{_BASE}/me/parent-group-invitations/synthetic-membership-01/decline",
            headers={"Idempotency-Key": "decline-key-01"},
        )
        assert declined.status_code == 200, declined.text
        assert declined.json()["state"] == "DECLINED"
        assert declined.json()["organization_id"] == _ORG
        assert declined.headers["ETag"] == '"2"'
        page = client.get(
            f"{_BASE}/me/parent-group-memberships",
            params={"limit": 1, "cursor": "previous-page"},
        )
    assert page.status_code == 200, page.text
    assert page.headers["Cache-Control"] == "private, no-store"
    assert page.json()["items"][0]["state"] == "ACTIVE"
    assert page.json()["items"][0]["organization_id"] == _ORG
    assert service.calls == [
        (
            "decline_parent_group_invitation",
            {
                "membership_id": "synthetic-membership-01",
                "actor": "synthetic-parent",
                "actor_issuer": _ISSUER,
                "idempotency_key": "decline-key-01",
            },
        ),
        (
            "list_parent_group_memberships",
            {
                "parent_principal_ref": "synthetic-parent",
                "limit": 1,
                "cursor": "previous-page",
            },
        ),
    ]


def test_manager_member_read_passes_filter_and_exposes_only_safe_fields() -> None:
    safe_membership = {
        key: value
        for key, value in _membership(state="DECLINED").items()
        if key not in {"contract", "organization_id", "revision_source"}
    }
    response = {
        "contract": "ParentGroupMemberPageV1",
        "items": [safe_membership],
        "counts": {
            "invited": 1,
            "accepted": 2,
            "declined": 5,
            "revoked": 3,
            "expired": 4,
            "total": 15,
        },
        "next_cursor": None,
    }
    service = _MembershipService(responses={"list_parent_group_members": response})
    with _client(service, actor="synthetic-manager", role="school_manager") as client:
        result = client.get(
            f"{_BASE}/organizations/{_ORG}/parent-groups/{_GROUP}/members",
            params={"state": "DECLINED", "limit": 1, "cursor": "scoped-cursor"},
        )
    assert result.status_code == 200, result.text
    assert result.headers["Cache-Control"] == "private, no-store"
    body = result.json()
    assert body["counts"] == response["counts"]
    assert body["items"][0]["state"] == "DECLINED"
    assert "contract" not in body["items"][0]
    assert "revision_source" not in body["items"][0]
    assert not {
        "parent_principal_ref",
        "email",
        "phone",
        "child_id",
        "child_name",
    }.intersection(body["items"][0])
    assert service.calls == [
        (
            "list_parent_group_members",
            {
                "organization_id": _ORG,
                "group_id": _GROUP,
                "manager_principal_ref": "synthetic-manager",
                "state": "DECLINED",
                "limit": 1,
                "cursor": "scoped-cursor",
            },
        )
    ]


def test_manager_read_uses_the_same_404_for_absent_foreign_and_unassigned_groups() -> None:
    not_found = LessonLibraryError(404, "RESOURCE_NOT_FOUND", "Parent group was not found")
    assigned_service = _MembershipService(errors={"list_parent_group_members": not_found})
    with _client(assigned_service, actor="synthetic-manager", role="school_manager") as client:
        absent = client.get(f"{_BASE}/organizations/{_ORG}/parent-groups/missing/members")
        foreign = client.get(
            f"{_BASE}/organizations/synthetic-other-org/parent-groups/foreign-group/members"
        )
    unassigned_service = _MembershipService()
    with _client(
        unassigned_service,
        actor="synthetic-unassigned-manager",
        role="school_manager",
        assigned=False,
    ) as client:
        unassigned = client.get(f"{_BASE}/organizations/{_ORG}/parent-groups/{_GROUP}/members")
    results = [absent, foreign, unassigned]
    assert all(result.status_code == 404 for result in results)
    assert all(result.json().get("code") == "RESOURCE_NOT_FOUND" for result in results)
    assert all(result.status_code != 422 for result in results)
    bodies = {(result.json().get("code"), result.json().get("message")) for result in results}
    assert len(bodies) == 1
    # The foreign-organization request stops at the assignment check, before any service call.
    assert len(assigned_service.calls) == 1
    assert not unassigned_service.calls


def test_revoke_requires_if_match_and_returns_the_response_revision_as_etag() -> None:
    service = _MembershipService(
        responses={"revoke_parent_group_membership": _membership(state="REVOKED", revision=5)}
    )
    with _client(service, actor="synthetic-manager", role="school_manager") as client:
        missing = client.delete(
            f"{_BASE}/organizations/{_ORG}/parent-groups/{_GROUP}/members/synthetic-membership-01",
            headers={"Idempotency-Key": "revoke-key-01"},
        )
        revoked = client.delete(
            f"{_BASE}/organizations/{_ORG}/parent-groups/{_GROUP}/members/synthetic-membership-01",
            headers={"If-Match": '"4"', "Idempotency-Key": "revoke-key-01"},
        )
    assert missing.status_code == 428
    assert missing.json()["code"] == "PRECONDITION_REQUIRED"
    assert revoked.status_code == 200, revoked.text
    assert revoked.headers["ETag"] == '"5"'
    assert service.calls == [
        (
            "revoke_parent_group_membership",
            {
                "organization_id": _ORG,
                "group_id": _GROUP,
                "membership_id": "synthetic-membership-01",
                "actor": "synthetic-manager",
                "actor_issuer": _ISSUER,
                "manager": True,
                "expected_revision": 4,
                "idempotency_key": "revoke-key-01",
            },
        )
    ]


@pytest.mark.parametrize(
    "key",
    [None, "", " ", "x" * 129],
    ids=["missing", "empty", "non-visible-ascii", "over-128"],
)
def test_decline_rejects_invalid_idempotency_keys_as_flat_400(key: str | None) -> None:
    service = _MembershipService()
    headers = {} if key is None else {"Idempotency-Key": key}
    with _client(service) as client:
        result = client.post(
            f"{_BASE}/me/parent-group-invitations/synthetic-membership-01/decline",
            headers=headers,
        )
    assert result.status_code == 400, result.text
    assert result.json()["code"] == "INVALID_REQUEST"
    assert result.json()["field_errors"][0]["field"] == "Idempotency-Key"
    assert service.calls == []


def test_revoke_precondition_errors_precede_idempotency_key_validation() -> None:
    service = _MembershipService()
    path = f"{_BASE}/organizations/{_ORG}/parent-groups/{_GROUP}/members/synthetic-membership-01"
    with _client(service, actor="synthetic-manager", role="school_manager") as client:
        valid_key = {"Idempotency-Key": "revoke-key-02"}
        missing_match = client.delete(path, headers=valid_key)
        malformed_match = client.delete(
            path,
            headers={**valid_key, "If-Match": "not-an-etag"},
        )
    assert missing_match.status_code == 428
    assert missing_match.json()["code"] == "PRECONDITION_REQUIRED"
    assert malformed_match.status_code == 400
    assert malformed_match.json()["code"] == "INVALID_REQUEST"
    assert malformed_match.json()["field_errors"][0]["field"] == "If-Match"
    assert service.calls == []


def test_manager_member_read_rejects_invalid_state_and_oversized_cursor_as_flat_400() -> None:
    service = _MembershipService()
    path = f"{_BASE}/organizations/{_ORG}/parent-groups/{_GROUP}/members"
    with _client(service, actor="synthetic-manager", role="school_manager") as client:
        invalid_state = client.get(path, params={"state": "ACTIVE"})
        oversized_cursor = client.get(path, params={"cursor": "x" * 1025})
    assert invalid_state.status_code == 400, invalid_state.text
    assert invalid_state.json()["code"] == "INVALID_REQUEST"
    assert invalid_state.json()["field_errors"][0]["field"] == "state"
    assert oversized_cursor.status_code == 400, oversized_cursor.text
    assert oversized_cursor.json()["code"] == "INVALID_REQUEST"
    assert oversized_cursor.json()["field_errors"][0]["field"] == "cursor"
    assert service.calls == []
