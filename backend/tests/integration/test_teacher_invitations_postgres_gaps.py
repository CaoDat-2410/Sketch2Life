"""Additional PostgreSQL integration tests for Teacher invitation gaps."""

# ruff: noqa: F811

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import func, select

from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.infrastructure.persistence.platform_models import EmailDeliveryModel
from tests.integration.test_teacher_invitations_postgres import (
    InvitationApi,
    _invite,
    invitation_api,  # noqa: F401 - pytest fixture
)


def _resend(api: InvitationApi, *, account_ref: str, key: str, principal: str | None = None):
    return api.client.post(
        f"/api/be1/v1/organizations/{api.organization_id}/teacher-invitations/{account_ref}/resend",
        headers={
            "X-Test-Principal": principal or api.manager_subject,
            "Idempotency-Key": key,
        },
    )


@pytest.mark.integration
def test_resend_route_replays_audits_and_uniform_404_on_postgres(
    invitation_api: InvitationApi,
) -> None:
    """covers: D_T-6A_PROMPT.md §5"""
    api = invitation_api
    email = f"resend-{uuid4().hex[:8]}@example.test"
    invited = _invite(api, email=email, key="resend-init")
    assert invited.status_code == 202
    account_ref = invited.json()["account_ref"]
    provider_subject = api.provisioner.identities[email].subject

    resent = _resend(api, account_ref=account_ref, key="resend-once")
    replayed = _resend(api, account_ref=account_ref, key="resend-once")
    assert resent.status_code == replayed.status_code == 202
    assert resent.json() == replayed.json() == {"account_ref": account_ref, "status": "PENDING_VERIFICATION"}
    assert resent.headers["Cache-Control"] == "private, no-store"

    with api.session_factory() as db:
        deliveries = db.scalars(
            select(EmailDeliveryModel).where(
                EmailDeliveryModel.recipient_ref == provider_subject,
                EmailDeliveryModel.template == "password_setup",
            )
        ).all()
        resent_audits = db.scalars(
            select(CoreAuditEntryModel).where(
                CoreAuditEntryModel.organization_id == api.organization_id,
                CoreAuditEntryModel.resource_id == account_ref,
                CoreAuditEntryModel.action == "TEACHER_INVITATION_RESENT",
            )
        ).all()
    assert len(deliveries) == 2
    assert len(resent_audits) == 1
    assert provider_subject not in repr(resent_audits[0])
    assert email not in repr(resent_audits[0])

    unknown = _resend(api, account_ref=str(uuid4()), key="resend-unknown")
    assert (unknown.status_code, unknown.json()["code"]) == (404, "RESOURCE_NOT_FOUND")

    activated = api.client.get(
        "/api/auth/v1/me",
        headers={"X-Test-Principal": provider_subject, "X-Test-Email-Verified": "true"},
    )
    assert activated.status_code == 200
    after_activation = _resend(api, account_ref=account_ref, key="resend-after-activation")
    assert (after_activation.status_code, after_activation.json()["code"]) == (
        404,
        "RESOURCE_NOT_FOUND",
    )
    assert (after_activation.json()["message"]) == (unknown.json()["message"])


@pytest.mark.integration
def test_unverified_invitee_is_excluded_from_teacher_candidates_until_verified(
    invitation_api: InvitationApi,
) -> None:
    """covers: D_T-6A_PROMPT.md §5"""
    api = invitation_api
    email = f"candidate-{uuid4().hex[:8]}@example.test"
    invited = _invite(api, email=email, key="candidate-check")
    assert invited.status_code == 202
    account_ref = invited.json()["account_ref"]
    provider_subject = api.provisioner.identities[email].subject

    before = api.client.get(
        f"/api/be1/v1/organizations/{api.organization_id}/teacher-candidates",
        headers={"X-Test-Principal": api.manager_subject},
    )
    assert before.status_code == 200
    assert all(item["candidate_ref"] != account_ref for item in before.json()["items"])

    activated = api.client.get(
        "/api/auth/v1/me",
        headers={"X-Test-Principal": provider_subject, "X-Test-Email-Verified": "true"},
    )
    assert activated.status_code == 200

    after = api.client.get(
        f"/api/be1/v1/organizations/{api.organization_id}/teacher-candidates",
        headers={"X-Test-Principal": api.manager_subject},
    )
    assert after.status_code == 200
    assert any(item["candidate_ref"] == account_ref for item in after.json()["items"])


@pytest.mark.integration
def test_same_key_with_changed_email_returns_400_without_side_effects_on_postgres(
    invitation_api: InvitationApi,
) -> None:
    """covers: IMPL_REVIEW_D_T-6A_R1_20261125.md Checked-Idempotency"""
    api = invitation_api
    email_a = f"first-{uuid4().hex[:8]}@example.test"
    email_b = f"second-{uuid4().hex[:8]}@example.test"

    first = _invite(api, email=email_a, key="shared-invite-key")
    assert first.status_code == 202
    second = _invite(api, email=email_b, key="shared-invite-key")

    assert second.status_code == 400
    assert second.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    assert second.headers["Cache-Control"] == "private, no-store"
    assert email_b not in api.provisioner.identities


@pytest.mark.integration
def test_foreign_org_manager_cannot_invite_and_gets_uniform_404_on_postgres(
    invitation_api: InvitationApi,
) -> None:
    """covers: D_T-6A_PROMPT.md §5"""
    api = invitation_api
    other_org = f"synthetic-other-org-{uuid4().hex[:8]}"
    other_manager = f"synthetic-other-manager-{uuid4().hex[:8]}"
    with api.session_factory.begin() as db:
        db.add(OrganizationModel(organization_id=other_org, display_name="Other Org", state="active"))
        db.add(
            AdultIdentityModel(
                subject=other_manager,
                issuer="synthetic-teacher-invitation-issuer",
                state="active",
                account_role="school_manager",
            )
        )
        db.flush()
        db.add(
            OrganizationAssignmentModel(
                assignment_id=str(uuid4()),
                organization_id=other_org,
                subject=other_manager,
                class_id=None,
                role="school_admin",
                active=True,
            )
        )

    email = f"foreign-{uuid4().hex[:8]}@example.test"
    response = api.client.post(
        f"/api/be1/v1/organizations/{api.organization_id}/teacher-invitations",
        json={"email": email},
        headers={"X-Test-Principal": other_manager, "Idempotency-Key": "foreign-invite"},
    )
    assert response.status_code == 404
    assert response.json()["code"] == "RESOURCE_NOT_FOUND"
    assert email not in api.provisioner.identities
    with api.session_factory() as db:
        receipt_count = db.scalar(
            select(func.count())
            .select_from(Be1CommandReceiptModel)
            .where(Be1CommandReceiptModel.organization_id == api.organization_id)
        )
    assert receipt_count == 0
