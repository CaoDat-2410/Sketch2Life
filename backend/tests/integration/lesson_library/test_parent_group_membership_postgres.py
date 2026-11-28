"""PostgreSQL acceptance coverage for T-10c parent-group membership commands and reads."""

from __future__ import annotations

import importlib.util
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import delete, event, func, select, update
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.orm import Session
from test_lesson_library_api import (
    LessonApiAcceptance,
    _create_lesson,
    _headers,
)
from test_lesson_library_api import (
    lesson_api_acceptance as lesson_api_acceptance,
)

from sketch2life.infrastructure.lesson_library.tables import (
    ACCESS_GRANTS,
    COMMAND_RECEIPTS,
    PARENT_GROUP_MEMBERS,
    PARENT_GROUPS,
)
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel

_BASE = "/api/lesson-library/v1"
_DECLINE_SCOPE = "POST /lesson-library/v1/me/parent-group-invitations/decline"
_REVOKE_SCOPE = "DELETE /lesson-library/v1/organizations/parent-groups/members"
_MIGRATION = (
    Path(__file__).resolve().parents[3]
    / "alembic"
    / "versions"
    / "20261121_pg_0001_declined_membership.py"
)


def _create_group(
    accepted: LessonApiAcceptance, label: str, *, organization_id: str | None = None,
) -> str:
    target_organization = organization_id or accepted.organization_id
    response = accepted.client.post(
        f"{_BASE}/organizations/{target_organization}/parent-groups",
        json={"contract": "CreateParentGroupRequestV1", "display_name": f"{label} {uuid4()}"},
        headers=_headers(accepted.manager, **{"Idempotency-Key": f"{label}-group-{uuid4()}"}),
    )
    assert response.status_code == 201, response.text
    return response.json()["parent_group_id"]


def _invite_parent(
    accepted: LessonApiAcceptance,
    group_id: str,
    parent: str,
    label: str,
    *,
    organization_id: str | None = None,
) -> str:
    target_organization = organization_id or accepted.organization_id
    response = accepted.client.post(
        f"{_BASE}/organizations/{target_organization}/parent-groups/{group_id}/invitations",
        json={
            "contract": "InviteParentToGroupRequestV1",
            "parent_principal_ref": parent,
        },
        headers=_headers(accepted.manager, **{"Idempotency-Key": f"{label}-invite-{uuid4()}"}),
    )
    assert response.status_code == 201, response.text
    return response.json()["membership_id"]


def _load_migration():
    spec = importlib.util.spec_from_file_location("pg_0001_declined_membership", _MIGRATION)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _add_parent(accepted: LessonApiAcceptance, label: str) -> str:
    subject = f"synthetic-parent-group-{label}-{uuid4()}"
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        db.add(
            AdultIdentityModel(
                subject=subject,
                issuer="synthetic-lesson-test-issuer",
                state="active",
                account_role="parent",
            )
        )
    return subject


def _accept_parent(
    accepted: LessonApiAcceptance, membership_id: str, parent: str,
) -> dict[str, Any]:
    response = accepted.client.post(
        f"{_BASE}/me/parent-group-invitations/{membership_id}/accept",
        headers=_headers(parent, **{"Idempotency-Key": f"accept-{uuid4()}"}),
    )
    assert response.status_code == 200, response.text
    return response.json()


def _parent_receipt_count(
    accepted: LessonApiAcceptance,
    *,
    actor: str,
    key: str,
    scope_prefix: str,
) -> int:
    with accepted.app.state.be1_runtime.session_factory() as db:
        return int(
            db.scalar(
                select(func.count()).select_from(Be1CommandReceiptModel).where(
                    Be1CommandReceiptModel.principal_ref == actor,
                    Be1CommandReceiptModel.idempotency_key == key,
                    Be1CommandReceiptModel.operation_scope.like(f"{scope_prefix}:%"),
                )
            )
            or 0
        )


def _parent_group_audit_count(
    accepted: LessonApiAcceptance, *, membership_id: str, actions: tuple[str, ...],
) -> int:
    with accepted.app.state.be1_runtime.session_factory() as db:
        return int(
            db.scalar(
                select(func.count()).select_from(CoreAuditEntryModel).where(
                    CoreAuditEntryModel.resource_type == "parent_group_membership",
                    CoreAuditEntryModel.resource_id == membership_id,
                    CoreAuditEntryModel.action.in_(actions),
                )
            )
            or 0
        )


def test_declining_an_expired_invitation_does_not_change_state_or_save_a_receipt(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    group_id = _create_group(accepted, "t10c-expired")
    membership_id = _invite_parent(accepted, group_id, accepted.parent, "t10c-expired")
    key = f"expired-decline-{uuid4()}"
    scope = f"POST /me/parent-group-invitations/{membership_id}/decline"
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        db.execute(
            update(PARENT_GROUP_MEMBERS)
            .where(PARENT_GROUP_MEMBERS.c.membership_id == membership_id)
            .values(expires_at=datetime.now(UTC) - timedelta(seconds=1))
        )

    response = accepted.client.post(
        f"{_BASE}/me/parent-group-invitations/{membership_id}/decline",
        headers=_headers(accepted.parent, **{"Idempotency-Key": key}),
    )
    assert response.status_code == 409, response.text
    assert response.json()["code"] == "INVITATION_EXPIRED"
    with accepted.app.state.be1_runtime.session_factory() as db:
        membership = db.execute(
            select(PARENT_GROUP_MEMBERS.c.state, PARENT_GROUP_MEMBERS.c.revision)
            .where(PARENT_GROUP_MEMBERS.c.membership_id == membership_id)
        ).one()
        receipt_count = db.execute(
            select(func.count()).select_from(COMMAND_RECEIPTS).where(
                COMMAND_RECEIPTS.c.organization_id == accepted.organization_id,
                COMMAND_RECEIPTS.c.principal_ref == accepted.parent,
                COMMAND_RECEIPTS.c.operation_scope == scope,
                COMMAND_RECEIPTS.c.idempotency_key == key,
            )
        ).scalar_one()
    assert membership.state == "invited"
    assert membership.revision == 1
    assert receipt_count == 0
    assert _parent_receipt_count(
        accepted, actor=accepted.parent, key=key, scope_prefix=_DECLINE_SCOPE
    ) == 0

    stored_expired_key = f"stored-expired-decline-{uuid4()}"
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        db.execute(
            update(PARENT_GROUP_MEMBERS)
            .where(PARENT_GROUP_MEMBERS.c.membership_id == membership_id)
            .values(state="expired")
        )
    stored_expired = accepted.client.post(
        f"{_BASE}/me/parent-group-invitations/{membership_id}/decline",
        headers=_headers(accepted.parent, **{"Idempotency-Key": stored_expired_key}),
    )
    assert stored_expired.status_code == 409, stored_expired.text
    assert stored_expired.json()["code"] == "INVITATION_EXPIRED"
    assert _parent_receipt_count(
        accepted,
        actor=accepted.parent,
        key=stored_expired_key,
        scope_prefix=_DECLINE_SCOPE,
    ) == 0


def test_parent_memberships_and_manager_roster_are_scoped_paged_and_private(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    group_id = _create_group(accepted, "t10c-members")
    other_parent = _add_parent(accepted, "member")
    active_id = _invite_parent(accepted, group_id, accepted.parent, "t10c-active")
    _accept_parent(accepted, active_id, accepted.parent)
    declined_id = _invite_parent(accepted, group_id, other_parent, "t10c-declined")
    decline_key = f"decline-{uuid4()}"
    decline_path = f"{_BASE}/me/parent-group-invitations/{declined_id}/decline"
    declined = accepted.client.post(
        decline_path,
        headers=_headers(other_parent, **{"Idempotency-Key": decline_key}),
    )
    assert declined.status_code == 200, declined.text
    assert declined.json()["state"] == "DECLINED"
    with accepted.app.state.be1_runtime.session_factory() as db:
        group_organization_id = db.scalar(
            select(PARENT_GROUPS.c.organization_id).where(
                PARENT_GROUPS.c.parent_group_id == group_id
            )
        )
    assert declined.json()["organization_id"] == group_organization_id
    assert declined.headers["ETag"] == f'"{declined.json()["revision"]}"'
    replay = accepted.client.post(
        decline_path,
        headers=_headers(other_parent, **{"Idempotency-Key": decline_key}),
    )
    assert replay.status_code == 200, replay.text
    assert replay.json() == declined.json()
    assert replay.headers["ETag"] == declined.headers["ETag"]
    assert _parent_receipt_count(
        accepted, actor=other_parent, key=decline_key, scope_prefix=_DECLINE_SCOPE
    ) == 1
    assert _parent_group_audit_count(
        accepted,
        membership_id=declined_id,
        actions=("parent_group.invitation.decline",),
    ) == 1

    pending_group = _create_group(accepted, "t10c-pending")
    pending_id = _invite_parent(accepted, pending_group, accepted.parent, "t10c-pending")
    other_active_id = _invite_parent(
        accepted, pending_group, other_parent, "t10c-other-active"
    )
    _accept_parent(accepted, other_active_id, other_parent)
    own_page = accepted.client.get(
        f"{_BASE}/me/parent-group-memberships",
        headers=_headers(accepted.parent),
    )
    assert own_page.status_code == 200, own_page.text
    assert own_page.headers["Cache-Control"] == "private, no-store"
    assert [item["membership_id"] for item in own_page.json()["items"]] == [active_id]
    assert own_page.json()["items"][0]["organization_id"] == group_organization_id
    assert other_active_id not in {item["membership_id"] for item in own_page.json()["items"]}
    assert pending_id not in {item["membership_id"] for item in own_page.json()["items"]}

    manager_path = (
        f"{_BASE}/organizations/{accepted.organization_id}/parent-groups/{group_id}/members"
    )
    filtered = accepted.client.get(
        manager_path,
        params={"state": "DECLINED", "limit": 1},
        headers=_headers(accepted.manager),
    )
    assert filtered.status_code == 200, filtered.text
    assert filtered.headers["Cache-Control"] == "private, no-store"
    assert [item["membership_id"] for item in filtered.json()["items"]] == [declined_id]
    assert filtered.json()["counts"] == {
        "invited": 0,
        "accepted": 1,
        "declined": 1,
        "revoked": 0,
        "expired": 0,
        "total": 2,
    }
    safe_fields = {
        "membership_id",
        "parent_group_id",
        "state",
        "invited_at",
        "expires_at",
        "accepted_at",
        "revision",
    }
    assert set(filtered.json()["items"][0]) == safe_fields
    assert "parent_principal_ref" not in filtered.text
    assert other_parent not in filtered.text

    first_page = accepted.client.get(
        manager_path,
        params={"limit": 1},
        headers=_headers(accepted.manager),
    )
    assert first_page.status_code == 200, first_page.text
    assert first_page.json()["counts"] == filtered.json()["counts"]
    cursor = first_page.json()["next_cursor"]
    assert cursor
    second_page = accepted.client.get(
        manager_path,
        params={"limit": 1, "cursor": cursor},
        headers=_headers(accepted.manager),
    )
    assert second_page.status_code == 200, second_page.text
    assert second_page.json()["counts"] == first_page.json()["counts"]
    ids = {
        first_page.json()["items"][0]["membership_id"],
        second_page.json()["items"][0]["membership_id"],
    }
    assert ids == {active_id, declined_id}
    assert first_page.json()["counts"]["total"] == sum(
        first_page.json()["counts"][state]
        for state in ("invited", "accepted", "declined", "revoked", "expired")
    )
    mismatched_cursor = accepted.client.get(
        manager_path,
        params={"state": "DECLINED", "limit": 1, "cursor": cursor},
        headers=_headers(accepted.manager),
    )
    assert mismatched_cursor.status_code == 400, mismatched_cursor.text
    assert mismatched_cursor.json()["code"] == "INVALID_REQUEST"

    accepted_filter = accepted.client.get(
        manager_path,
        params={"state": "ACCEPTED"},
        headers=_headers(accepted.manager),
    )
    assert accepted_filter.status_code == 200, accepted_filter.text
    assert [item["membership_id"] for item in accepted_filter.json()["items"]] == [active_id]
    assert accepted_filter.json()["items"][0]["state"] == "ACCEPTED"

    absent_group = accepted.client.get(
        f"{_BASE}/organizations/{accepted.organization_id}/parent-groups/missing/members",
        headers=_headers(accepted.manager),
    )
    other_organization = accepted.client.get(
        f"{_BASE}/organizations/synthetic-other-org/parent-groups/{group_id}/members",
        headers=_headers(accepted.manager),
    )
    unassigned_parent = accepted.client.get(
        manager_path,
        headers=_headers(accepted.parent),
    )
    hidden_group_responses = [absent_group, other_organization, unassigned_parent]
    assert all(response.status_code == 404 for response in hidden_group_responses)
    assert all(
        response.json()["code"] == "RESOURCE_NOT_FOUND" for response in hidden_group_responses
    )
    assert len({
        (response.json()["code"], response.json()["message"])
        for response in hidden_group_responses
    }) == 1


def test_same_key_concurrent_declines_replay_one_be1_receipt_and_audit(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    parent = _add_parent(accepted, "concurrent-decline")
    group_id = _create_group(accepted, "t10c-concurrent-decline")
    membership_id = _invite_parent(accepted, group_id, parent, "t10c-concurrent-decline")
    key = f"same-decline-{uuid4()}"
    barrier = threading.Barrier(2)
    url = f"{_BASE}/me/parent-group-invitations/{membership_id}/decline"

    def send_decline():
        barrier.wait(timeout=10)
        return accepted.client.post(
            url, headers=_headers(parent, **{"Idempotency-Key": key})
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _index: send_decline(), range(2)))

    assert [response.status_code for response in responses] == [200, 200]
    assert responses[0].json() == responses[1].json()
    assert responses[0].headers["ETag"] == responses[1].headers["ETag"] == '"2"'
    assert _parent_receipt_count(
        accepted, actor=parent, key=key, scope_prefix=_DECLINE_SCOPE
    ) == 1
    assert _parent_group_audit_count(
        accepted,
        membership_id=membership_id,
        actions=("parent_group.invitation.decline",),
    ) == 1
    with accepted.app.state.be1_runtime.session_factory() as db:
        legacy_receipts = db.scalar(
            select(func.count()).select_from(COMMAND_RECEIPTS).where(
                COMMAND_RECEIPTS.c.principal_ref == parent,
                COMMAND_RECEIPTS.c.idempotency_key == key,
            )
        )
    assert legacy_receipts == 0


def test_decline_and_accept_race_has_one_successful_transition(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    group_id = _create_group(accepted, "t10c-accept-decline-race")
    membership_id = _invite_parent(accepted, group_id, accepted.parent, "t10c-race")
    barrier = threading.Barrier(2)

    def decline():
        barrier.wait(timeout=10)
        return accepted.client.post(
            f"{_BASE}/me/parent-group-invitations/{membership_id}/decline",
            headers=_headers(accepted.parent, **{"Idempotency-Key": f"race-decline-{uuid4()}"}),
        )

    def accept():
        barrier.wait(timeout=10)
        return accepted.client.post(
            f"{_BASE}/me/parent-group-invitations/{membership_id}/accept",
            headers=_headers(accepted.parent, **{"Idempotency-Key": f"race-accept-{uuid4()}"}),
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        decline_future = executor.submit(decline)
        accept_future = executor.submit(accept)
        responses = [decline_future.result(), accept_future.result()]

    assert sorted(response.status_code for response in responses) == [200, 409]
    winner = next(response for response in responses if response.status_code == 200)
    loser = next(response for response in responses if response.status_code == 409)
    assert loser.json()["code"] == "INVALID_STATE_TRANSITION"
    assert winner.json()["state"] in {"DECLINED", "ACTIVE"}
    with accepted.app.state.be1_runtime.session_factory() as db:
        row = db.execute(
            select(PARENT_GROUP_MEMBERS.c.state, PARENT_GROUP_MEMBERS.c.revision).where(
                PARENT_GROUP_MEMBERS.c.membership_id == membership_id
            )
        ).one()
    assert row.revision == 2
    assert row.state == winner.json()["state"].lower()
    assert _parent_group_audit_count(
        accepted,
        membership_id=membership_id,
        actions=("parent_group.invitation.decline", "parent_group.invitation.accept"),
    ) == 1


def test_decline_receipt_flush_failure_rolls_back_transition_and_audit(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    group_id = _create_group(accepted, "t10c-receipt-failure")
    membership_id = _invite_parent(accepted, group_id, accepted.parent, "t10c-receipt-failure")
    key = f"receipt-failure-{uuid4()}"

    def fail_parent_group_receipt(session, _flush_context, _instances):
        if any(
            isinstance(instance, Be1CommandReceiptModel)
            and instance.operation_scope.startswith(f"{_DECLINE_SCOPE}:")
            for instance in session.new
        ):
            raise SQLAlchemyError("synthetic parent-group receipt flush failure")

    event.listen(Session, "before_flush", fail_parent_group_receipt)
    try:
        response = accepted.client.post(
            f"{_BASE}/me/parent-group-invitations/{membership_id}/decline",
            headers=_headers(accepted.parent, **{"Idempotency-Key": key}),
        )
    finally:
        event.remove(Session, "before_flush", fail_parent_group_receipt)

    assert response.status_code == 503, response.text
    assert response.json()["code"] == "PROVIDER_UNAVAILABLE"
    with accepted.app.state.be1_runtime.session_factory() as db:
        membership = db.execute(
            select(PARENT_GROUP_MEMBERS.c.state, PARENT_GROUP_MEMBERS.c.revision).where(
                PARENT_GROUP_MEMBERS.c.membership_id == membership_id
            )
        ).one()
    assert (membership.state, membership.revision) == ("invited", 1)
    assert _parent_receipt_count(
        accepted, actor=accepted.parent, key=key, scope_prefix=_DECLINE_SCOPE
    ) == 0
    assert _parent_group_audit_count(
        accepted,
        membership_id=membership_id,
        actions=("parent_group.invitation.decline",),
    ) == 0


def test_stale_revoke_with_fresh_key_writes_no_receipt_or_audit(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    group_id = _create_group(accepted, "t10c-stale-revoke")
    membership_id = _invite_parent(accepted, group_id, accepted.parent, "t10c-stale-revoke")
    _accept_parent(accepted, membership_id, accepted.parent)
    key = f"stale-revoke-{uuid4()}"
    response = accepted.client.delete(
        f"{_BASE}/organizations/{accepted.organization_id}/parent-groups/{group_id}/members/{membership_id}",
        headers=_headers(
            accepted.manager,
            **{"If-Match": '"1"', "Idempotency-Key": key},
        ),
    )
    assert response.status_code == 409, response.text
    assert response.json()["code"] == "STALE_REVISION"
    assert response.headers["ETag"] == '"2"'
    assert _parent_receipt_count(
        accepted, actor=accepted.manager, key=key, scope_prefix=_REVOKE_SCOPE
    ) == 0
    assert _parent_group_audit_count(
        accepted,
        membership_id=membership_id,
        actions=("parent_group.membership.revoke",),
    ) == 0


def test_revoke_same_key_with_changed_if_match_is_invalid_idempotency_key(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    group_id = _create_group(accepted, "t10c-revoke-fingerprint")
    membership_id = _invite_parent(accepted, group_id, accepted.parent, "t10c-revoke-fingerprint")
    key = f"revoke-fingerprint-{uuid4()}"
    path = (
        f"{_BASE}/organizations/{accepted.organization_id}/parent-groups/{group_id}"
        f"/members/{membership_id}"
    )
    first = accepted.client.delete(
        path,
        headers=_headers(accepted.manager, **{"If-Match": '"1"', "Idempotency-Key": key}),
    )
    changed = accepted.client.delete(
        path,
        headers=_headers(accepted.manager, **{"If-Match": '"2"', "Idempotency-Key": key}),
    )
    assert first.status_code == 200, first.text
    assert first.json()["revision"] == 2
    assert changed.status_code == 400, changed.text
    assert changed.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    assert _parent_receipt_count(
        accepted, actor=accepted.manager, key=key, scope_prefix=_REVOKE_SCOPE
    ) == 1
    assert _parent_group_audit_count(
        accepted,
        membership_id=membership_id,
        actions=("parent_group.membership.revoke",),
    ) == 1


def test_revoke_same_key_concurrent_requests_replay_original_etag(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    group_id = _create_group(accepted, "t10c-concurrent-revoke")
    membership_id = _invite_parent(accepted, group_id, accepted.parent, "t10c-concurrent-revoke")
    _accept_parent(accepted, membership_id, accepted.parent)
    key = f"same-revoke-{uuid4()}"
    barrier = threading.Barrier(2)
    path = (
        f"{_BASE}/organizations/{accepted.organization_id}/parent-groups/{group_id}"
        f"/members/{membership_id}"
    )

    def send_revoke():
        barrier.wait(timeout=10)
        return accepted.client.delete(
            path,
            headers=_headers(
                accepted.manager,
                **{"If-Match": '"2"', "Idempotency-Key": key},
            ),
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _index: send_revoke(), range(2)))

    assert [response.status_code for response in responses] == [200, 200]
    assert responses[0].json() == responses[1].json()
    assert responses[0].headers["ETag"] == responses[1].headers["ETag"] == '"3"'
    assert _parent_receipt_count(
        accepted, actor=accepted.manager, key=key, scope_prefix=_REVOKE_SCOPE
    ) == 1
    assert _parent_group_audit_count(
        accepted,
        membership_id=membership_id,
        actions=("parent_group.membership.revoke",),
    ) == 1


def test_revoke_replay_after_manager_assignment_loss_is_not_found(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    group_id = _create_group(accepted, "t10c-assignment-loss")
    membership_id = _invite_parent(accepted, group_id, accepted.parent, "t10c-assignment-loss")
    key = f"assignment-loss-{uuid4()}"
    path = (
        f"{_BASE}/organizations/{accepted.organization_id}/parent-groups/{group_id}"
        f"/members/{membership_id}"
    )
    first = accepted.client.delete(
        path,
        headers=_headers(accepted.manager, **{"If-Match": '"1"', "Idempotency-Key": key}),
    )
    assert first.status_code == 200, first.text
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        db.execute(
            update(OrganizationAssignmentModel)
            .where(
                OrganizationAssignmentModel.organization_id == accepted.organization_id,
                OrganizationAssignmentModel.subject == accepted.manager,
                OrganizationAssignmentModel.role == "school_admin",
            )
            .values(active=False)
        )
    replay_without_assignment = accepted.client.delete(
        path,
        headers=_headers(accepted.manager, **{"If-Match": '"1"', "Idempotency-Key": key}),
    )
    assert replay_without_assignment.status_code == 404, replay_without_assignment.text
    assert replay_without_assignment.json()["code"] == "RESOURCE_NOT_FOUND"
    assert replay_without_assignment.status_code != 422


def test_decline_by_another_parent_matches_missing_membership_404(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    other_parent = _add_parent(accepted, "not-owner")
    group_id = _create_group(accepted, "t10c-other-parent")
    membership_id = _invite_parent(accepted, group_id, accepted.parent, "t10c-other-parent")
    foreign = accepted.client.post(
        f"{_BASE}/me/parent-group-invitations/{membership_id}/decline",
        headers=_headers(other_parent, **{"Idempotency-Key": f"other-parent-{uuid4()}"}),
    )
    missing = accepted.client.post(
        f"{_BASE}/me/parent-group-invitations/missing-membership/decline",
        headers=_headers(other_parent, **{"Idempotency-Key": f"missing-parent-{uuid4()}"}),
    )
    assert foreign.status_code == missing.status_code == 404
    assert foreign.json()["code"] == missing.json()["code"] == "RESOURCE_NOT_FOUND"
    assert foreign.json()["message"] == missing.json()["message"]
    assert foreign.status_code != 422


def test_revoke_by_another_parent_matches_missing_membership_404(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    other_parent = _add_parent(accepted, "revoke-not-owner")
    group_id = _create_group(accepted, "t10c-revoke-other-parent")
    membership_id = _invite_parent(
        accepted, group_id, accepted.parent, "t10c-revoke-other-parent"
    )
    foreign = accepted.client.delete(
        f"{_BASE}/organizations/{accepted.organization_id}/parent-groups/"
        f"{group_id}/members/{membership_id}",
        headers=_headers(
            other_parent,
            **{"If-Match": '"1"', "Idempotency-Key": f"other-revoke-{uuid4()}"},
        ),
    )
    missing = accepted.client.delete(
        f"{_BASE}/organizations/{accepted.organization_id}/parent-groups/"
        f"{group_id}/members/missing-membership",
        headers=_headers(
            other_parent,
            **{"If-Match": '"1"', "Idempotency-Key": f"missing-revoke-{uuid4()}"},
        ),
    )
    assert foreign.status_code == missing.status_code == 404
    assert foreign.json()["code"] == missing.json()["code"] == "RESOURCE_NOT_FOUND"
    assert foreign.json()["message"] == missing.json()["message"]
    assert foreign.status_code != 422


def test_revoke_absent_group_matches_absent_membership_404(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    group_id = _create_group(accepted, "t10c-revoke-not-found")
    membership_id = _invite_parent(
        accepted, group_id, accepted.parent, "t10c-revoke-not-found"
    )
    headers = {"If-Match": '"1"'}
    missing_group = accepted.client.delete(
        f"{_BASE}/organizations/{accepted.organization_id}/parent-groups/"
        f"missing-group/members/{membership_id}",
        headers=_headers(accepted.manager, **{
            **headers,
            "Idempotency-Key": f"missing-group-{uuid4()}",
        }),
    )
    missing_member = accepted.client.delete(
        f"{_BASE}/organizations/{accepted.organization_id}/parent-groups/"
        f"{group_id}/members/missing-membership",
        headers=_headers(accepted.manager, **{
            **headers,
            "Idempotency-Key": f"missing-member-{uuid4()}",
        }),
    )
    assert missing_group.status_code == missing_member.status_code == 404
    assert missing_group.json()["code"] == missing_member.json()["code"] == "RESOURCE_NOT_FOUND"
    assert missing_group.json()["message"] == missing_member.json()["message"]
    assert missing_group.status_code != 422


def test_revoke_removes_group_scoped_access_and_preserves_separate_direct_access(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    group_id = _create_group(accepted, "t10c-grant-access")
    membership_id = _invite_parent(accepted, group_id, accepted.parent, "t10c-grant-access")
    _accept_parent(accepted, membership_id, accepted.parent)
    group_lesson = _create_lesson(
        accepted, title=f"Synthetic group {uuid4()}", visibility="PRIVATE"
    )
    direct_lesson = _create_lesson(
        accepted, title=f"Synthetic direct {uuid4()}", visibility="PRIVATE"
    )

    def create_grant(lesson: dict[str, Any], audience_kind: str, audience_ref: str) -> str:
        result = accepted.client.post(
            f"{_BASE}/organizations/{accepted.organization_id}/lessons/"
            f"{lesson['lesson_id']}/access-grants",
            json={
                "contract": "CreateLessonAccessGrantRequestV1",
                "version_id": lesson["current_version"]["version_id"],
                "audience_kind": audience_kind,
                "audience_ref": audience_ref,
                "capability": "VIEW",
                "expires_at": None,
            },
            headers=_headers(accepted.teacher, **{"Idempotency-Key": f"grant-{uuid4()}"}),
        )
        assert result.status_code == 201, result.text
        return result.json()["access_grant_id"]

    group_grant_id = create_grant(group_lesson, "PARENT_GROUP", group_id)
    direct_grant_id = create_grant(direct_lesson, "PRINCIPAL", accepted.parent)
    direct_accept = accepted.client.post(
        f"{_BASE}/me/lesson-invitations/{direct_grant_id}/accept",
        headers=_headers(accepted.parent, **{"Idempotency-Key": f"direct-accept-{uuid4()}"}),
    )
    assert direct_accept.status_code == 200, direct_accept.text
    before = accepted.client.get(
        f"{_BASE}/me/lessons?source=SHARED", headers=_headers(accepted.parent)
    )
    assert before.status_code == 200, before.text
    before_ids = {item["lesson_id"] for item in before.json()["items"]}
    assert {group_lesson["lesson_id"], direct_lesson["lesson_id"]} <= before_ids

    revoked = accepted.client.delete(
        f"{_BASE}/organizations/{accepted.organization_id}/parent-groups/{group_id}/members/{membership_id}",
        headers=_headers(
            accepted.manager,
            **{"If-Match": '"2"', "Idempotency-Key": f"group-revoke-{uuid4()}"},
        ),
    )
    assert revoked.status_code == 200, revoked.text
    after = accepted.client.get(
        f"{_BASE}/me/lessons?source=SHARED", headers=_headers(accepted.parent)
    )
    assert after.status_code == 200, after.text
    after_ids = {item["lesson_id"] for item in after.json()["items"]}
    assert group_lesson["lesson_id"] not in after_ids
    assert direct_lesson["lesson_id"] in after_ids
    with accepted.app.state.be1_runtime.session_factory() as db:
        grant_states = db.execute(
            select(ACCESS_GRANTS.c.access_grant_id, ACCESS_GRANTS.c.state).where(
                ACCESS_GRANTS.c.access_grant_id.in_((group_grant_id, direct_grant_id))
            )
        ).all()
    assert {grant.access_grant_id: grant.state for grant in grant_states} == {
        group_grant_id: "ACTIVE",
        direct_grant_id: "ACTIVE",
    }


def test_parent_self_revokes_using_organization_id_from_own_memberships_list(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    group_id = _create_group(accepted, "fix1-self-revoke")
    membership_id = _invite_parent(accepted, group_id, accepted.parent, "fix1-self-revoke")
    _accept_parent(accepted, membership_id, accepted.parent)
    own_page = accepted.client.get(
        f"{_BASE}/me/parent-group-memberships", headers=_headers(accepted.parent)
    )
    assert own_page.status_code == 200, own_page.text
    item = next(i for i in own_page.json()["items"] if i["membership_id"] == membership_id)
    assert item["organization_id"] == accepted.organization_id
    key = f"fix1-self-revoke-{uuid4()}"
    path = (
        f"{_BASE}/organizations/{item['organization_id']}/parent-groups/"
        f"{item['parent_group_id']}/members/{item['membership_id']}"
    )
    headers = _headers(
        accepted.parent, **{"If-Match": f'"{item["revision"]}"', "Idempotency-Key": key}
    )
    revoked = accepted.client.delete(path, headers=headers)
    assert revoked.status_code == 200, revoked.text
    assert revoked.json()["state"] == "REVOKED"
    assert revoked.json()["organization_id"] == item["organization_id"]
    replay = accepted.client.delete(path, headers=headers)
    assert replay.status_code == 200, replay.text
    assert replay.json()["organization_id"] == item["organization_id"]


def test_equal_timestamp_membership_pages_use_membership_id_as_tiebreaker(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    group_id = _create_group(accepted, "t10c-equal-timestamp")
    membership_ids = []
    for index in range(3):
        parent = _add_parent(accepted, f"equal-{index}")
        membership_ids.append(_invite_parent(accepted, group_id, parent, f"equal-{index}"))
    same_time = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        db.execute(
            update(PARENT_GROUP_MEMBERS)
            .where(PARENT_GROUP_MEMBERS.c.membership_id.in_(membership_ids))
            .values(invited_at=same_time)
        )
    url = f"{_BASE}/organizations/{accepted.organization_id}/parent-groups/{group_id}/members"
    cursor = None
    actual_ids: list[str] = []
    page_counts: list[dict[str, int]] = []
    while True:
        params: dict[str, Any] = {"limit": 1}
        if cursor is not None:
            params["cursor"] = cursor
        page = accepted.client.get(url, params=params, headers=_headers(accepted.manager))
        assert page.status_code == 200, page.text
        actual_ids.extend(item["membership_id"] for item in page.json()["items"])
        page_counts.append(page.json()["counts"])
        cursor = page.json()["next_cursor"]
        if cursor is None:
            break
    assert actual_ids == sorted(membership_ids, reverse=True)
    assert len(actual_ids) == len(set(actual_ids)) == 3
    assert all(counts == page_counts[0] for counts in page_counts)
    assert page_counts[0] == {
        "invited": 3,
        "accepted": 0,
        "declined": 0,
        "revoked": 0,
        "expired": 0,
        "total": 3,
    }


def test_parent_group_cursor_is_bound_to_group_and_organization(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    group_a = _create_group(accepted, "t10c-cursor-a")
    group_b = _create_group(accepted, "t10c-cursor-b")
    for index in range(2):
        parent = _add_parent(accepted, f"cursor-{index}")
        _invite_parent(accepted, group_a, parent, f"cursor-a-{index}")
    path_a = f"{_BASE}/organizations/{accepted.organization_id}/parent-groups/{group_a}/members"
    first = accepted.client.get(path_a, params={"limit": 1}, headers=_headers(accepted.manager))
    assert first.status_code == 200, first.text
    cursor = first.json()["next_cursor"]
    assert cursor

    same_org_other_group = accepted.client.get(
        f"{_BASE}/organizations/{accepted.organization_id}/parent-groups/{group_b}/members",
        params={"cursor": cursor},
        headers=_headers(accepted.manager),
    )
    assert same_org_other_group.status_code == 400, same_org_other_group.text
    assert same_org_other_group.json()["code"] == "INVALID_REQUEST"

    other_organization_id = f"synthetic-parent-group-cursor-org-{uuid4()}"
    other_assignment_id = str(uuid4())
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        db.add(
            OrganizationModel(
                organization_id=other_organization_id,
                display_name=f"Synthetic cursor organization {uuid4()}",
                state="active",
            )
        )
        db.flush()
        db.add(
            OrganizationAssignmentModel(
                assignment_id=other_assignment_id,
                organization_id=other_organization_id,
                subject=accepted.manager,
                class_id=None,
                role="school_admin",
                active=True,
            )
        )
    try:
        other_group = _create_group(
            accepted, "t10c-cursor-other-org", organization_id=other_organization_id
        )
        with accepted.app.state.be1_runtime.session_factory() as db:
            assert db.scalar(
                select(PARENT_GROUPS.c.organization_id).where(
                    PARENT_GROUPS.c.parent_group_id == other_group
                )
            ) == other_organization_id
        foreign_group = accepted.client.get(
            f"{_BASE}/organizations/{accepted.organization_id}/parent-groups/{other_group}/members",
            headers=_headers(accepted.manager),
        )
        absent_group = accepted.client.get(
            f"{_BASE}/organizations/{accepted.organization_id}/parent-groups/missing/members",
            headers=_headers(accepted.manager),
        )
        assert foreign_group.status_code == absent_group.status_code == 404
        assert foreign_group.json()["code"] == absent_group.json()["code"] == "RESOURCE_NOT_FOUND"
        assert foreign_group.json()["message"] == absent_group.json()["message"]
        other_org_page = accepted.client.get(
            f"{_BASE}/organizations/{other_organization_id}/parent-groups/{other_group}/members",
            params={"cursor": cursor},
            headers=_headers(accepted.manager),
        )
        assert other_org_page.status_code == 400, other_org_page.text
        assert other_org_page.json()["code"] == "INVALID_REQUEST"
    finally:
        # The fixture removes the Manager identity; the extra assignment must go first.
        with accepted.app.state.be1_runtime.session_factory.begin() as db:
            db.execute(
                delete(OrganizationAssignmentModel).where(
                    OrganizationAssignmentModel.assignment_id == other_assignment_id
                )
            )


def test_parent_group_accept_still_replays_its_legacy_receipt(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    group_id = _create_group(accepted, "t10c-legacy-accept")
    membership_id = _invite_parent(accepted, group_id, accepted.parent, "t10c-legacy-accept")
    key = f"legacy-accept-{uuid4()}"
    url = f"{_BASE}/me/parent-group-invitations/{membership_id}/accept"
    first = accepted.client.post(
        url, headers=_headers(accepted.parent, **{"Idempotency-Key": key})
    )
    replay = accepted.client.post(
        url, headers=_headers(accepted.parent, **{"Idempotency-Key": key})
    )
    assert first.status_code == replay.status_code == 200
    assert first.json() == replay.json()
    scope = f"POST /me/parent-group-invitations/{membership_id}/accept"
    with accepted.app.state.be1_runtime.session_factory() as db:
        legacy_count = db.scalar(
            select(func.count()).select_from(COMMAND_RECEIPTS).where(
                COMMAND_RECEIPTS.c.organization_id == accepted.organization_id,
                COMMAND_RECEIPTS.c.principal_ref == accepted.parent,
                COMMAND_RECEIPTS.c.operation_scope == scope,
                COMMAND_RECEIPTS.c.idempotency_key == key,
            )
        )
        be1_count = db.scalar(
            select(func.count()).select_from(Be1CommandReceiptModel).where(
                Be1CommandReceiptModel.principal_ref == accepted.parent,
                Be1CommandReceiptModel.idempotency_key == key,
            )
        )
    assert legacy_count == 1
    assert be1_count == 0
    assert _parent_group_audit_count(
        accepted,
        membership_id=membership_id,
        actions=("parent_group.invitation.accept",),
    ) == 1


def test_runtime_migration_downgrade_refuses_declined_membership_rows(
    lesson_api_acceptance: LessonApiAcceptance,
) -> None:
    accepted = lesson_api_acceptance
    group_id = _create_group(accepted, "t10c-runtime-downgrade")
    parent = _add_parent(accepted, "runtime-downgrade")
    membership_id = _invite_parent(accepted, group_id, parent, "t10c-runtime-downgrade")
    declined = accepted.client.post(
        f"{_BASE}/me/parent-group-invitations/{membership_id}/decline",
        headers=_headers(parent, **{"Idempotency-Key": f"downgrade-{uuid4()}"}),
    )
    assert declined.status_code == 200, declined.text

    migration = _load_migration()
    connection = accepted.app.state.be1_runtime.engine.connect()
    transaction = connection.begin()
    try:
        migration.op = Operations(MigrationContext.configure(connection))
        with pytest.raises(DBAPIError, match="downgrade refused: declined parent-group"):
            migration.downgrade()
    finally:
        transaction.rollback()
        connection.close()
    with accepted.app.state.be1_runtime.session_factory() as db:
        row = db.execute(
            select(PARENT_GROUP_MEMBERS.c.state).where(
                PARENT_GROUP_MEMBERS.c.membership_id == membership_id
            )
        ).one()
    assert row.state == "declined"
