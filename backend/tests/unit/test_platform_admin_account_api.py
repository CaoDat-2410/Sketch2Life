"""Account lifecycle HTTP checks against an isolated database and identity double."""

from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from sketch2life.application.ports.identity import (
    IdentityAccountProfile,
    ProvisionedIdentity,
    VerifiedPrincipal,
)
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
    ClassroomModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.infrastructure.persistence.platform_models import PLATFORM_TABLES
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.routers.auth_registration import router as auth_router
from sketch2life.interfaces.http.routers.password_recovery import router as recovery_router
from sketch2life.interfaces.http.routers.platform_admin import router as admin_router
from sketch2life.interfaces.http.routers.platform_admin_accounts import router


class IdentityDouble:
    def __init__(self):
        self.profiles = {"admin": IdentityAccountProfile("admin", "admin@example.test", "Admin")}
        self.disabled = {}

    def create_account(self, *, email, display_name=None):
        subject = str(uuid4())
        self.profiles[subject] = IdentityAccountProfile(subject, email, display_name)
        return ProvisionedIdentity(subject, "test-issuer")

    def get_account_profiles(self, subjects):
        return {subject: self.profiles[subject] for subject in subjects if subject in self.profiles}

    def set_account_disabled(self, subject, disabled):
        self.disabled[subject] = disabled

    def delete_account(self, subject):
        self.profiles.pop(subject, None)

    def find_account_by_email(self, email):
        profile = next((p for p in self.profiles.values() if p.email == email), None)
        return ProvisionedIdentity(profile.subject, "test-issuer") if profile else None

    def get_user(self, subject):
        return SimpleNamespace(
            email=self.profiles[subject].email, disabled=self.disabled.get(subject, False)
        )

    def password_link(self, email):
        return "https://example.test/password?code=synthetic-secret"

    def verification_link(self, email):
        return "https://example.test/verify?code=synthetic-secret"


@pytest.fixture
def account_api():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    for model in [
        OrganizationModel,
        AdultIdentityModel,
        OrganizationAssignmentModel,
        CoreAuditEntryModel,
        Be1CommandReceiptModel,
        ClassroomModel,
    ]:
        model.__table__.create(engine)
    for table in PLATFORM_TABLES:
        table.create(engine)
    with Session(engine) as db:
        db.add(
            AdultIdentityModel(
                account_id="admin-account",
                subject="admin",
                issuer="test-issuer",
                state="active",
                account_role="platform_admin",
                role_revision=1,
            )
        )
        db.add(
            OrganizationModel(organization_id="school", display_name="Test School", state="active")
        )
        db.commit()
    app = FastAPI()
    identity = IdentityDouble()
    app.state.identity_account_provisioner = identity
    app.include_router(router)
    app.include_router(admin_router)
    app.include_router(auth_router)
    app.include_router(recovery_router)
    principal = SimpleNamespace(value=VerifiedPrincipal("admin", "test-issuer", frozenset()))

    def database():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = database
    app.dependency_overrides[get_verified_adult] = lambda: principal.value
    with TestClient(app) as client:
        yield client, engine, identity, principal
    engine.dispose()


@compiles(JSONB, "sqlite")
def _jsonb_as_json_on_sqlite(_type, _compiler, **_kw):  # noqa: ANN001, ANN003
    return "JSON"


BASE = "/api/platform-admin/v1/accounts"
ADMIN = "/api/platform-admin/v1"


def activate_account(api, account_id):
    client, engine, _, principal = api
    previous = principal.value
    with Session(engine) as db:
        subject = db.scalar(
            select(AdultIdentityModel.subject).where(AdultIdentityModel.account_id == account_id)
        )
    principal.value = VerifiedPrincipal(subject, "test-issuer", frozenset(), email_verified=False)
    assert client.get("/api/auth/v1/me").status_code == 403
    principal.value = VerifiedPrincipal(subject, "test-issuer", frozenset(), email_verified=True)
    assert client.get("/api/auth/v1/me").status_code == 200
    principal.value = previous


def test_organization_idempotency_and_permissions(account_api):
    client, _, _, _ = account_api
    headers = {"Idempotency-Key": "organization-once"}
    first = client.post(
        ADMIN + "/organizations", json={"display_name": "New School"}, headers=headers
    )
    replay = client.post(
        ADMIN + "/organizations", json={"display_name": "New School"}, headers=headers
    )
    assert first.status_code == 201 and first.json() == replay.json()
    assert (
        client.get(ADMIN + "/organizations", params={"search": "New School"}).json()["total"] == 1
    )
    assert (
        client.post(
            ADMIN + "/organizations", json={"display_name": "Other"}, headers=headers
        ).status_code
        == 400
    )
    reviewer = client.post(
        BASE,
        json={
            "email": "reviewer@example.test",
            "display_name": "Reviewer",
            "role": "platform_admin",
        },
        headers={"Idempotency-Key": "create-reviewer"},
    ).json()
    activate_account(account_api, reviewer["account_id"])
    path = BASE + "/" + reviewer["account_id"] + "/permissions/content-admin"
    payload = {"active": True, "expected_revision": 0, "reason": "Assign editorial reviewer"}
    headers = {"Idempotency-Key": "permission-once"}
    assert client.put(path, json=payload, headers=headers).status_code == 200
    assert client.put(path, json=payload, headers=headers).json()["revision"] == 1
    assert (
        client.put(path, json=payload, headers={"Idempotency-Key": "stale-permission"}).status_code
        == 409
    )
    assert (
        client.put(
            BASE + "/admin-account/permissions/content-admin", json=payload, headers=headers
        ).status_code
        == 403
    )
    revoke = {"active": False, "expected_revision": 1, "reason": "Revoke reviewer"}
    assert (
        client.put(path, json=revoke, headers={"Idempotency-Key": "revoke"}).json()["active"]
        is False
    )


def test_organization_summary_state_filter_and_code_search(account_api):
    client, engine, _, _ = account_api
    with Session(engine) as db:
        db.add_all(
            [
                OrganizationModel(
                    organization_id="school-paused-01",
                    display_name="Trường Tạm Dừng",
                    state="suspended",
                ),
                OrganizationModel(
                    organization_id="school-disabled-01",
                    display_name="Trường Ngừng Hoạt Động",
                    state="inactive",
                ),
            ]
        )
        db.commit()

    summary = client.get(ADMIN + "/organizations/summary")
    assert summary.status_code == 200
    assert summary.json() == {
        "total": 3,
        "active": 1,
        "paused": 1,
        "disabled": 1,
        "other": 0,
    }

    paused = client.get(ADMIN + "/organizations", params={"state": "paused"})
    assert paused.status_code == 200
    assert [item["organization_id"] for item in paused.json()["items"]] == ["school-paused-01"]

    disabled = client.get(ADMIN + "/organizations", params={"state": "disabled"})
    assert disabled.status_code == 200
    assert [item["organization_id"] for item in disabled.json()["items"]] == ["school-disabled-01"]

    by_code = client.get(ADMIN + "/organizations", params={"search": "paused-01"})
    assert by_code.status_code == 200
    assert by_code.json()["total"] == 1
    assert by_code.json()["items"][0]["display_name"] == "Trường Tạm Dừng"
    assert client.get(ADMIN + "/organizations", params={"state": "unknown"}).status_code == 422


def test_private_inbox_preferences_audit_and_email_outbox(account_api):
    client, engine, _, principal = account_api
    headers = {"Idempotency-Key": "preferences"}
    payload = {"locale": "vi-VN", "email_notifications": False, "expected_revision": 0}
    assert client.put(ADMIN + "/preferences", json=payload, headers=headers).json()["revision"] == 1
    assert client.get(ADMIN + "/preferences").json()["email_notifications"] is False
    first = client.post(BASE + "/admin-account/setup-email", headers={"Idempotency-Key": "email"})
    assert first.status_code == 202
    assert (
        client.post(
            BASE + "/admin-account/setup-email", headers={"Idempotency-Key": "email"}
        ).json()
        == first.json()
    )
    audit = client.get(ADMIN + "/audit").json()["items"]
    assert any(row["action"] == "ACCOUNT_SETUP_EMAIL_REQUESTED" for row in audit)
    from sketch2life.infrastructure.persistence.platform_models import InboxItemModel

    with Session(engine) as db:
        db.add(
            InboxItemModel(
                item_id="other-inbox",
                recipient_ref="other",
                kind="PERMISSION_CHANGED",
                resource_ref="other",
                is_read=False,
            )
        )
        db.commit()
    assert client.get(ADMIN + "/inbox").json()["items"] == []
    assert (
        client.post(
            ADMIN + "/inbox/other-inbox/read", headers={"Idempotency-Key": "read"}
        ).status_code
        == 404
    )
    principal.value = VerifiedPrincipal("outsider", "test-issuer", frozenset())
    assert client.get(ADMIN + "/audit").status_code == 403
    assert client.get(ADMIN + "/organizations").status_code == 403
    assert client.get(ADMIN + "/organizations/summary").status_code == 403


def test_account_lifecycle_filters_and_paging(account_api):
    client, engine, identity, _ = account_api
    response = client.post(
        BASE,
        json={"email": "teacher@example.test", "display_name": "Teacher", "role": "teacher"},
        headers={"Idempotency-Key": "create-lifecycle-teacher"},
    )
    assert response.status_code == 201
    account = response.json()
    assert account["state"] == "pending_verification"
    activate_account(account_api, account["account_id"])
    account_url = BASE + "/" + account["account_id"]
    role_response = client.patch(
        account_url,
        json={"role": "parent"},
        headers={"Idempotency-Key": "lifecycle-role", "If-Match": '"2"'},
    )
    assert role_response.json()["revision"] == 3
    disabled = client.patch(
        account_url,
        json={"state": "disabled"},
        headers={"Idempotency-Key": "lifecycle-disable", "If-Match": '"3"'},
    )
    assert disabled.json()["state"] == "disabled"
    assert client.get(BASE, params={"state": "disabled"}).json()["total"] == 1
    assert client.patch(
        account_url,
        json={"state": "active"},
        headers={"Idempotency-Key": "lifecycle-enable", "If-Match": '"4"'},
    ).status_code == 200
    assert (
        client.get(BASE, params={"role": "parent", "search": "teacher@example"}).json()["total"]
        == 1
    )
    first = client.get(BASE, params={"limit": 1}).json()
    # Keyset paging itself is asserted on PostgreSQL (test_platform_admin_accounts_postgres);
    # SQLite returns naive timestamps, which the timezone-aware cursor rightly refuses.
    assert len(first["items"]) == 1 and isinstance(first["next_cursor"], str)
    assert client.get(BASE, params={"cursor": "invalid"}).status_code == 400
    assert client.get(BASE, params={"cursor": "offset:99999999999999999999"}).status_code == 400
    with Session(engine) as db:
        assert len(list(db.scalars(select(CoreAuditEntryModel)))) == 5
        row = db.scalar(
            select(AdultIdentityModel).where(AdultIdentityModel.account_id == account["account_id"])
        )
        assert identity.disabled[row.subject] is False


def test_self_protection_and_server_authorization(account_api):
    client, _, _, principal = account_api
    assert client.patch(
        BASE + "/admin-account",
        json={"state": "disabled"},
        headers={"Idempotency-Key": "self-disable", "If-Match": '"1"'},
    ).status_code == 409
    assert client.patch(
        BASE + "/admin-account",
        json={"role": "teacher"},
        headers={"Idempotency-Key": "self-demote", "If-Match": '"1"'},
    ).status_code == 409
    principal.value = VerifiedPrincipal("outsider", "test-issuer", frozenset({"platform_admin"}))
    assert client.get(BASE).status_code == 403
    assert (
        client.post(
            BASE,
            json={"email": "other@example.test", "display_name": "Other", "role": "teacher"},
            headers={"Idempotency-Key": "unauthorized-create"},
        ).status_code
        == 403
    )


def test_manager_assignment_and_revoke(account_api):
    client, engine, _, _ = account_api
    payload = {"email": "manager@example.test", "display_name": "Manager", "role": "school_manager"}
    assert client.post(
        BASE, json=payload, headers={"Idempotency-Key": "manager-no-org"}
    ).status_code == 422
    assert client.post(
        BASE,
        json={**payload, "organization_id": "missing"},
        headers={"Idempotency-Key": "manager-missing-org"},
    ).status_code == 422
    response = client.post(
        BASE,
        json={**payload, "organization_id": "school"},
        headers={"Idempotency-Key": "create-manager"},
    )
    assert response.status_code == 201
    account_url = BASE + "/" + response.json()["account_id"]
    with Session(engine) as db:
        assignment = db.scalar(select(OrganizationAssignmentModel))
        assert not assignment.active and assignment.pending_activation
    activate_account(account_api, response.json()["account_id"])
    with Session(engine) as db:
        assignment = db.scalar(select(OrganizationAssignmentModel))
        assert assignment.role == "school_admin" and assignment.active
    assert client.patch(
        account_url,
        json={"role": "teacher"},
        headers={"Idempotency-Key": "revoke-manager", "If-Match": '"2"'},
    ).status_code == 200
    with Session(engine) as db:
        assert not db.scalar(select(OrganizationAssignmentModel)).active


def test_recovery_is_neutral_and_email_worker_does_not_persist_action_links(account_api):
    from sketch2life.infrastructure.persistence.platform_models import EmailDeliveryModel
    from sketch2life.infrastructure.platform_admin.email_worker import deliver_pending

    client, engine, provider, _ = account_api
    created = client.post(
        BASE,
        json={"email": "new@example.test", "display_name": "New user", "role": "teacher"},
        headers={"Idempotency-Key": "create-recovery-user"},
    )
    assert created.status_code == 201
    known = client.post("/api/auth/v1/password-recovery", json={"email": "new@example.test"})
    unknown = client.post("/api/auth/v1/password-recovery", json={"email": "missing@example.test"})
    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()
    assert (
        client.post("/api/auth/v1/password-recovery", json={"email": "bad-email"}).status_code
        == 422
    )
    delivered = []
    with Session(engine) as db:
        result = deliver_pending(
            db, SimpleNamespace(smtp_from="test@example.test"), provider, delivered.append
        )
        assert result == {"sent": 2, "failed": 0}
        assert all("synthetic-secret" in m.get_content() for m in delivered)
        assert all("/verify?" in m.get_content() for m in delivered)
        assert {m["Subject"] for m in delivered} == {
            "Thiết lập mật khẩu Sketch2Life", "Đặt lại mật khẩu Sketch2Life"
        }
        assert {r.template for r in db.scalars(select(EmailDeliveryModel))} == {
            "password_setup", "password_recovery"
        }
        assert all(
            r.state == "sent" and r.failure_code is None
            for r in db.scalars(select(EmailDeliveryModel))
        )
    response = client.post(
        BASE + "/" + created.json()["account_id"] + "/setup-email",
        headers={"Idempotency-Key": "retry-setup"},
    )
    assert response.status_code == 202

    def fail(_message):
        raise RuntimeError("sensitive transport details")

    with Session(engine) as db:
        assert deliver_pending(
            db, SimpleNamespace(smtp_from="test@example.test"), provider, fail
        ) == {"sent": 0, "failed": 1}
        row = db.scalar(select(EmailDeliveryModel).where(EmailDeliveryModel.state == "failed"))
        assert row.failure_code == "EMAIL_DELIVERY_UNAVAILABLE"
        assert deliver_pending(
            db, SimpleNamespace(smtp_from="test@example.test"), provider, fail
        ) == {"sent": 0, "failed": 0}


def test_account_mutation_replay_and_stale_revision(account_api):
    client, _, identity, _ = account_api
    payload = {"email": "once@example.test", "display_name": "Once", "role": "parent"}
    # FEAT-066 C5: a missing or malformed Idempotency-Key is 400 INVALID_REQUEST.
    assert client.post(BASE, json=payload).status_code == 400
    headers = {"Idempotency-Key": "create-account-once"}
    first = client.post(BASE, json=payload, headers=headers)
    assert first.status_code == 201, first.text
    assert client.post(BASE, json=payload, headers=headers).json() == first.json()
    assert len(identity.profiles) == 2
    assert (
        client.post(BASE, json={**payload, "display_name": "Other"}, headers=headers).status_code
        == 400
    )
    account = first.json()
    activate_account(account_api, account["account_id"])
    account = next(
        row
        for row in client.get(BASE).json()["items"]
        if row["account_id"] == account["account_id"]
    )
    path = BASE + "/" + account["account_id"]
    # FEAT-066 C5 CA-4: account role/state PATCH takes no If-Match; the key is mandatory.
    assert client.patch(path, json={"state": "disabled"}).status_code == 400
    headers = {"Idempotency-Key": "disable-once"}
    updated = client.patch(path, json={"state": "disabled"}, headers=headers)
    assert updated.status_code == 200, updated.text
    assert client.patch(path, json={"state": "disabled"}, headers=headers).json() == updated.json()
    assert (
        client.patch(path, json={"state": "active"}, headers=headers).status_code == 400
    )
