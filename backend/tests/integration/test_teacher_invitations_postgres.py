"""PostgreSQL persistence checks for Teacher invitation transactions (written, not run)."""

from __future__ import annotations

import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from threading import Barrier, Lock
from uuid import uuid4

import pytest
from fastapi import FastAPI, Header
from fastapi.testclient import TestClient
from httpx import Response as HttpxResponse
from pydantic import SecretStr
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, sessionmaker

from sketch2life.application.ports.identity import (
    IdentityAccountConflict,
    IdentityAccountProfile,
    ProvisionedIdentity,
    VerifiedPrincipal,
)
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.infrastructure.persistence.platform_models import EmailDeliveryModel
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult

ISSUER = "synthetic-teacher-invitation-issuer"
RECEIPT_KEY = "teacher-invitation-postgres-key-with-more-than-32-bytes"


@dataclass
class FakeProvisioner:
    identities: dict[str, ProvisionedIdentity] = field(default_factory=dict)
    lock: Lock = field(default_factory=Lock)

    def create_password_account(self, *, email: str, password: str) -> ProvisionedIdentity:
        raise AssertionError("password account creation is not used")

    def create_account(self, *, email: str, display_name: str | None = None) -> ProvisionedIdentity:
        normalized = email.casefold()
        with self.lock:
            if normalized in self.identities:
                raise IdentityAccountConflict()
            identity = ProvisionedIdentity(f"synthetic-provider-uid-{uuid4()}", ISSUER)
            self.identities[normalized] = identity
            return identity

    def delete_account(self, subject: str) -> None:
        raise AssertionError("provider cleanup is not used")

    def set_account_disabled(self, subject: str, disabled: bool) -> None:
        raise AssertionError("account disabling is not used")

    def get_account_profiles(self, subjects: list[str]) -> dict[str, IdentityAccountProfile]:
        return {}

    def find_account_by_email(self, email: str) -> ProvisionedIdentity | None:
        with self.lock:
            return self.identities.get(email.casefold())


@dataclass
class InvitationApi:
    client: TestClient
    app: FastAPI
    provisioner: FakeProvisioner
    organization_id: str
    manager_subject: str
    session_factory: sessionmaker[Session]

    def manager_headers(self, key: str) -> dict[str, str]:
        return {
            "X-Test-Principal": self.manager_subject,
            "Idempotency-Key": key,
        }


@pytest.fixture
def invitation_api(monkeypatch: pytest.MonkeyPatch) -> Iterator[InvitationApi]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    if "be1_acceptance" not in database_url.rsplit("/", 1)[-1]:
        pytest.fail("BE1_TEST_DATABASE_URL must point to a disposable *be1_acceptance database")
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_AI_PROVIDER", "disabled")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()

    provisioner = FakeProvisioner()
    app = create_app(
        identity_account_provisioner=provisioner,
        _composition_profile="classroom",
    )
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("PostgreSQL runtime did not initialize")
    runtime.settings.profile_receipt_hmac_key = SecretStr(RECEIPT_KEY)

    suffix = uuid4().hex[:12]
    organization_id = f"synthetic-teacher-invite-org-{suffix}"
    manager_subject = f"synthetic-teacher-invite-manager-{suffix}"
    with runtime.session_factory.begin() as db:
        db.add(
            OrganizationModel(
                organization_id=organization_id,
                display_name=f"Synthetic invitation school {suffix}",
                state="active",
            )
        )
        db.add(
            AdultIdentityModel(
                subject=manager_subject,
                issuer=ISSUER,
                state="active",
                account_role="school_manager",
            )
        )
        db.flush()
        db.add(
            OrganizationAssignmentModel(
                assignment_id=str(uuid4()),
                organization_id=organization_id,
                subject=manager_subject,
                class_id=None,
                role="school_admin",
                active=True,
            )
        )

    async def verified(
        x_test_principal: str = Header(alias="X-Test-Principal"),
        x_test_email_verified: bool = Header(default=False, alias="X-Test-Email-Verified"),
    ) -> VerifiedPrincipal:
        return VerifiedPrincipal(
            subject=x_test_principal,
            issuer=ISSUER,
            roles=frozenset(),
            email_verified=x_test_email_verified,
        )

    app.dependency_overrides[get_verified_adult] = verified
    try:
        with TestClient(app) as client:
            yield InvitationApi(
                client=client,
                app=app,
                provisioner=provisioner,
                organization_id=organization_id,
                manager_subject=manager_subject,
                session_factory=runtime.session_factory,
            )
    finally:
        app.dependency_overrides.clear()
        subjects = [manager_subject, *(item.subject for item in provisioner.identities.values())]
        with runtime.session_factory.begin() as db:
            db.execute(
                delete(EmailDeliveryModel).where(
                    EmailDeliveryModel.recipient_ref.in_(subjects)
                )
            )
            db.execute(
                delete(CoreAuditEntryModel).where(
                    CoreAuditEntryModel.organization_id == organization_id
                )
            )
            db.execute(
                delete(Be1CommandReceiptModel).where(
                    Be1CommandReceiptModel.organization_id == organization_id
                )
            )
            db.execute(
                delete(OrganizationAssignmentModel).where(
                    OrganizationAssignmentModel.organization_id == organization_id
                )
            )
            db.execute(delete(AdultIdentityModel).where(AdultIdentityModel.subject.in_(subjects)))
            db.execute(
                delete(OrganizationModel).where(
                    OrganizationModel.organization_id == organization_id
                )
            )
        runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _invite(api: InvitationApi, *, email: str, key: str) -> HttpxResponse:
    return api.client.post(
        f"/api/be1/v1/organizations/{api.organization_id}/teacher-invitations",
        json={"email": email},
        headers=api.manager_headers(key),
    )


def test_invitation_repeat_and_receipt_audit_are_safe(invitation_api: InvitationApi) -> None:
    api = invitation_api
    email = f"teacher-{uuid4().hex[:8]}@example.test"

    created = _invite(api, email=email, key="invite-first")
    repeated = _invite(api, email=email, key="invite-repeat")
    replay = _invite(api, email=email, key="invite-first")

    assert created.status_code == repeated.status_code == replay.status_code == 202
    assert created.headers["Cache-Control"] == "private, no-store"
    assert created.json() == repeated.json() == replay.json()
    assert set(created.json()) == {"account_ref", "status"}
    account_ref = created.json()["account_ref"]
    provider_identity = api.provisioner.identities[email]
    with api.session_factory() as db:
        identity = db.scalar(
            select(AdultIdentityModel).where(AdultIdentityModel.account_id == account_ref)
        )
        assignments = db.scalars(
            select(OrganizationAssignmentModel).where(
                OrganizationAssignmentModel.organization_id == api.organization_id,
                OrganizationAssignmentModel.subject == provider_identity.subject,
                OrganizationAssignmentModel.role == "teacher",
                OrganizationAssignmentModel.class_id.is_(None),
            )
        ).all()
        deliveries = db.scalars(
            select(EmailDeliveryModel).where(
                EmailDeliveryModel.recipient_ref == provider_identity.subject,
                EmailDeliveryModel.template == "password_setup",
            )
        ).all()
        receipts = db.scalars(
            select(Be1CommandReceiptModel).where(
                Be1CommandReceiptModel.organization_id == api.organization_id
            )
        ).all()
        audits = db.scalars(
            select(CoreAuditEntryModel).where(
                CoreAuditEntryModel.organization_id == api.organization_id,
                CoreAuditEntryModel.resource_id == account_ref,
            )
        ).all()

    assert identity is not None and identity.state == "pending_verification"
    assert identity.email_verification_required is True
    assert identity.account_role == "teacher"
    assert len(assignments) == 1
    assert assignments[0].active is False and assignments[0].pending_activation is True
    assert len(deliveries) == 2
    assert len(receipts) == 2
    assert all(
        set(row.response_json) == {"account_ref", "status"}
        and row.response_json["account_ref"] == account_ref
        and provider_identity.subject not in repr(row)
        and email not in repr(row)
        for row in receipts
    )
    assert len(audits) == 2
    assert all(
        row.actor_ref != api.manager_subject
        and provider_identity.subject not in repr(row)
        and email not in repr(row)
        for row in audits
    )
    assert provider_identity.subject not in created.text
    assert email not in created.text


def test_verified_me_activates_invitee_for_teacher_candidates(
    invitation_api: InvitationApi,
) -> None:
    api = invitation_api
    email = f"activation-{uuid4().hex[:8]}@example.test"
    invitation = _invite(api, email=email, key="invite-activation")
    assert invitation.status_code == 202
    account_ref = invitation.json()["account_ref"]
    provider_subject = api.provisioner.identities[email].subject

    before_verification = api.client.get(
        "/api/auth/v1/me",
        headers={"X-Test-Principal": provider_subject},
    )
    assert before_verification.status_code == 403

    activated = api.client.get(
        "/api/auth/v1/me",
        headers={
            "X-Test-Principal": provider_subject,
            "X-Test-Email-Verified": "true",
        },
    )
    assert activated.status_code == 200
    candidates = api.client.get(
        f"/api/be1/v1/organizations/{api.organization_id}/teacher-candidates",
        headers={"X-Test-Principal": api.manager_subject},
    )
    assert candidates.status_code == 200
    assert any(item["candidate_ref"] == account_ref for item in candidates.json()["items"])


def test_concurrent_same_org_invites_create_one_identity_and_assignment(
    invitation_api: InvitationApi,
) -> None:
    api = invitation_api
    email = f"concurrent-{uuid4().hex[:8]}@example.test"
    barrier = Barrier(2)

    def invite(key: str):
        barrier.wait()
        return _invite(api, email=email, key=key)

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(invite, ("concurrent-one", "concurrent-two")))

    assert [response.status_code for response in responses] == [202, 202]
    assert responses[0].json() == responses[1].json()
    provider_identity = api.provisioner.identities[email]
    account_ref = responses[0].json()["account_ref"]
    with api.session_factory() as db:
        identity_count = db.scalar(
            select(func.count())
            .select_from(AdultIdentityModel)
            .where(AdultIdentityModel.subject == provider_identity.subject)
        )
        assignment_count = db.scalar(
            select(func.count())
            .select_from(OrganizationAssignmentModel)
            .where(
                OrganizationAssignmentModel.organization_id == api.organization_id,
                OrganizationAssignmentModel.subject == provider_identity.subject,
                OrganizationAssignmentModel.role == "teacher",
                OrganizationAssignmentModel.class_id.is_(None),
            )
        )
    assert identity_count == 1
    assert assignment_count == 1
    assert provider_identity.subject not in responses[0].text + responses[1].text
    assert account_ref not in provider_identity.subject
