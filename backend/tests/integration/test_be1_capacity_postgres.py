"""PostgreSQL acceptance coverage for the BE1/Billing capacity projection."""

from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.be1.capacity_adapter import Be1CapacityAdapter
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    Be1CommandReceiptModel,
    ClassroomModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.billing_models import (
    BillingReceiptModel,
    SubscriptionEventModel,
    SubscriptionModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult


@dataclass
class CapacityAcceptanceClient:
    app: FastAPI
    client: TestClient
    organization_id: str
    subject: str
    subscription_id: str


@pytest.fixture
def capacity_acceptance_client(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> Iterator[CapacityAcceptanceClient]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to run PostgreSQL-backed capacity tests")
    if "be1_acceptance" not in database_url.rsplit("/", 1)[-1]:
        pytest.fail("BE1_TEST_DATABASE_URL must point to a disposable *be1_acceptance database")

    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_BILLING_SANDBOX_ENABLED", "true")
    monkeypatch.setenv("SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED", "true")
    monkeypatch.setenv("SKETCH2LIFE_ROOM_CODE_HMAC_KEY", "synthetic-test-key-" + "x" * 40)
    monkeypatch.setenv("SKETCH2LIFE_BE1_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()

    app = create_app()
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("BE1 PostgreSQL runtime did not initialize")

    organization_id = f"synthetic-capacity-org-{uuid4()}"
    subject = f"synthetic-capacity-manager-{uuid4()}"
    subscription_id = str(uuid4())
    now = datetime.now(UTC)
    with runtime.session_factory.begin() as db:
        db.add(
            OrganizationModel(
                organization_id=organization_id,
                display_name="Synthetic Capacity Organization",
                state="active",
            )
        )
        db.add(
            AdultIdentityModel(
                subject=subject,
                issuer="synthetic-test-issuer",
                state="active",
                account_role="school_manager",
            )
        )
        db.flush()
        db.add(
            OrganizationAssignmentModel(
                assignment_id=str(uuid4()),
                organization_id=organization_id,
                subject=subject,
                class_id=None,
                role="school_admin",
                active=True,
            )
        )
        db.add(
            SubscriptionModel(
                subscription_id=subscription_id,
                organization_ref=organization_id,
                price_id=str(uuid4()),
                addon_slots=1,
                state="ACTIVE",
                period_start=now,
                period_end=now + timedelta(days=30),
                revision=1,
            )
        )

    principal = VerifiedPrincipal(
        subject=subject,
        issuer="synthetic-test-issuer",
        roles=frozenset(),
        token_id="synthetic-capacity-token",
    )

    async def verified_test_adult() -> VerifiedPrincipal:
        return principal

    app.dependency_overrides[get_verified_adult] = verified_test_adult
    random_ip = uuid4().int
    test_ip = f"10.{random_ip % 254 + 1}.{(random_ip >> 8) % 254 + 1}.{(random_ip >> 16) % 254 + 1}"
    with TestClient(app, client=(test_ip, 12345)) as client:
        yield CapacityAcceptanceClient(app, client, organization_id, subject, subscription_id)
    app.dependency_overrides.clear()
    runtime.engine.dispose()
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()


def test_scheduled_downgrade_is_effective_on_read_and_projected_with_class_create(
    capacity_acceptance_client: CapacityAcceptanceClient,
) -> None:
    accepted = capacity_acceptance_client
    client = accepted.client
    base = f"/api/be1/v1/organizations/{accepted.organization_id}"
    class_refs: list[str] = []
    for index in range(11):
        created = client.post(
            base + "/classes",
            json={"display_name": f"Scheduled Capacity Class {index}"},
            headers={"Idempotency-Key": f"scheduled-capacity-{uuid4().hex}"},
        )
        assert created.status_code == 201, created.text
        class_refs.append(created.json()["class_id"])

    config_key = f"schedule-downgrade-{uuid4().hex}"
    downgrade_request = {
        "action": "downgrade",
        "addon_slots": 0,
        "suspend_class_refs": [class_refs[0]],
    }
    configured = client.patch(
        base + "/capacity",
        json=downgrade_request,
        headers={"If-Match": '"1"', "Idempotency-Key": config_key},
    )
    assert configured.status_code == 200, configured.text
    assert configured.headers["ETag"] == '"2"'
    assert configured.json()["scheduled_change"]["capacity"] == 10
    assert configured.json()["scheduled_change"]["suspend_class_refs"] == [class_refs[0]]

    replay = client.patch(
        base + "/capacity",
        json=downgrade_request,
        headers={"If-Match": '"1"', "Idempotency-Key": config_key},
    )
    assert replay.status_code == 200, replay.text
    assert replay.json() == configured.json()
    assert replay.headers["ETag"] == '"2"'
    mismatch = client.patch(
        base + "/capacity",
        json={"action": "cancel_renewal"},
        headers={"If-Match": '"1"', "Idempotency-Key": config_key},
    )
    assert mismatch.status_code == 400
    assert mismatch.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    stale = client.patch(
        base + "/capacity",
        json={"action": "resume_renewal"},
        headers={"If-Match": '"1"', "Idempotency-Key": f"stale-capacity-{uuid4().hex}"},
    )
    assert stale.status_code == 409
    assert stale.json()["code"] == "STALE_REVISION"
    assert stale.json()["current_version"] == 2

    with accepted.app.state.be1_runtime.session_factory() as db:
        assert db.get(
            Be1CommandReceiptModel,
            (
                accepted.subject,
                f"PATCH /organizations/{accepted.organization_id}/capacity",
                config_key,
            ),
        ) is not None
        assert db.get(
            BillingReceiptModel,
            (accepted.subject, "subscription.configure:" + accepted.subscription_id, config_key),
        ) is not None
        assert db.scalar(
            select(CoreAuditEntryModel.audit_id).where(
                CoreAuditEntryModel.organization_id == accepted.organization_id,
                CoreAuditEntryModel.actor_ref == accepted.subject,
                CoreAuditEntryModel.action == "subscription.downgrade",
            )
        ) is not None

    runtime = accepted.app.state.be1_runtime
    effective_at = datetime.now(UTC) - timedelta(seconds=1)
    with runtime.session_factory.begin() as db:
        # Backdating a scheduled event is a test-only edit of an append-only Billing table.
        db.execute(text("set local session_replication_role = replica"))
        subscription = db.get(SubscriptionModel, accepted.subscription_id)
        assert subscription is not None
        subscription.period_end = effective_at
        scheduled_events = db.scalars(
            select(SubscriptionEventModel).where(
                SubscriptionEventModel.subscription_id == accepted.subscription_id,
                SubscriptionEventModel.group_ref.is_not(None),
            )
        ).all()
        assert scheduled_events
        for item in scheduled_events:
            item.effective_at = effective_at

    archived = client.post(
        f"/api/be1/v1/classes/{class_refs[1]}/archive",
        headers={"If-Match": '"1"', "Idempotency-Key": f"archive-capacity-{uuid4().hex}"},
    )
    assert archived.status_code == 200, archived.text

    class_read = client.get(base + "/classes?state=all")
    assert class_read.status_code == 200, class_read.text
    projected_item = next(
        item for item in class_read.json()["items"] if item["class_id"] == class_refs[0]
    )
    assert projected_item["state"] == "suspended"
    with runtime.session_factory() as db:
        projected_by_read = db.get(ClassroomModel, class_refs[0])
        assert projected_by_read is not None
        assert (projected_by_read.state, projected_by_read.revision) == ("suspended", 2)

    effective_view = client.get(base + "/capacity")
    assert effective_view.status_code == 200, effective_view.text
    assert effective_view.json()["capacity"] == 10
    assert effective_view.json()["active_class_count"] == 9
    assert effective_view.json()["available_slots"] == 1
    assert effective_view.json()["scheduled_change"] is None

    created_after_due = client.post(
        base + "/classes",
        json={"display_name": "Class After Effective Downgrade"},
        headers={"Idempotency-Key": f"create-after-downgrade-{uuid4().hex}"},
    )
    assert created_after_due.status_code == 201, created_after_due.text
    with runtime.session_factory() as db:
        projected = db.get(ClassroomModel, class_refs[0])
        assert projected is not None
        assert (projected.state, projected.revision) == ("suspended", 2)
        assert db.scalar(
            select(ClassroomModel.class_id).where(
                ClassroomModel.class_id == created_after_due.json()["class_id"],
                ClassroomModel.state == "active",
            )
        ) is not None

    final_view = client.get(base + "/capacity")
    assert final_view.status_code == 200, final_view.text
    assert final_view.json()["active_class_count"] == 10
    assert final_view.json()["available_slots"] == 0


def _create_classes(accepted: CapacityAcceptanceClient, count: int) -> list[str]:
    base = f"/api/be1/v1/organizations/{accepted.organization_id}"
    class_refs = []
    for index in range(count):
        created = accepted.client.post(
            base + "/classes",
            json={"display_name": f"Capacity Acceptance Class {index}"},
            headers={"Idempotency-Key": f"capacity-class-{uuid4().hex}"},
        )
        assert created.status_code == 201, created.text
        class_refs.append(created.json()["class_id"])
    return class_refs


def test_capacity_get_persists_due_downgrade_projection_atomically(
    capacity_acceptance_client: CapacityAcceptanceClient,
) -> None:
    accepted = capacity_acceptance_client
    base = f"/api/be1/v1/organizations/{accepted.organization_id}"
    class_refs = _create_classes(accepted, 11)
    scheduled = accepted.client.patch(
        base + "/capacity",
        json={
            "action": "downgrade",
            "addon_slots": 0,
            "suspend_class_refs": [class_refs[0]],
        },
        headers={"If-Match": '"1"', "Idempotency-Key": f"schedule-get-{uuid4().hex}"},
    )
    assert scheduled.status_code == 200, scheduled.text

    effective_at = datetime.now(UTC) - timedelta(seconds=1)
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        # Backdating a scheduled event is a test-only edit of an append-only Billing table.
        db.execute(text("set local session_replication_role = replica"))
        subscription = db.get(SubscriptionModel, accepted.subscription_id)
        assert subscription is not None
        subscription.period_end = effective_at
        events = db.scalars(
            select(SubscriptionEventModel).where(
                SubscriptionEventModel.subscription_id == accepted.subscription_id,
                SubscriptionEventModel.group_ref.is_not(None),
            )
        ).all()
        assert events
        for event_row in events:
            event_row.effective_at = effective_at

    capacity = accepted.client.get(base + "/capacity")
    assert capacity.status_code == 200, capacity.text
    assert capacity.json()["capacity"] == 10
    assert capacity.json()["active_class_count"] == 10
    assert capacity.json()["available_slots"] == 0
    assert capacity.json()["scheduled_change"] is None
    with accepted.app.state.be1_runtime.session_factory() as db:
        projected = db.get(ClassroomModel, class_refs[0])
        assert projected is not None
        assert (projected.state, projected.revision) == ("suspended", 2)
        assert db.scalar(
            select(CoreAuditEntryModel.audit_id).where(
                CoreAuditEntryModel.organization_id == accepted.organization_id,
                CoreAuditEntryModel.action == "class.suspend.capacity_downgrade",
                CoreAuditEntryModel.resource_id == class_refs[0],
            )
        ) is not None


def test_downgrade_rejections_cover_missing_duplicate_foreign_inactive_and_wrong_size(
    capacity_acceptance_client: CapacityAcceptanceClient,
) -> None:
    accepted = capacity_acceptance_client
    base = f"/api/be1/v1/organizations/{accepted.organization_id}"
    class_refs = _create_classes(accepted, 11)

    missing = accepted.client.patch(
        base + "/capacity",
        json={"action": "downgrade", "addon_slots": 0},
        headers={"If-Match": '"1"', "Idempotency-Key": f"missing-{uuid4().hex}"},
    )
    assert missing.status_code == 400
    assert missing.json()["code"] == "INVALID_REQUEST"

    duplicate = accepted.client.patch(
        base + "/capacity",
        json={
            "action": "downgrade",
            "addon_slots": 0,
            "suspend_class_refs": [class_refs[0], class_refs[0]],
        },
        headers={"If-Match": '"1"', "Idempotency-Key": f"duplicate-{uuid4().hex}"},
    )
    assert duplicate.status_code == 422
    assert duplicate.json()["code"] == "INVALID_CAPACITY_DOWNGRADE"

    wrong_size = accepted.client.patch(
        base + "/capacity",
        json={"action": "downgrade", "addon_slots": 0, "suspend_class_refs": []},
        headers={"If-Match": '"1"', "Idempotency-Key": f"wrong-size-{uuid4().hex}"},
    )
    assert wrong_size.status_code == 422
    assert wrong_size.json()["code"] == "CLASS_SELECTION_REQUIRED"

    foreign = accepted.client.patch(
        base + "/capacity",
        json={
            "action": "downgrade",
            "addon_slots": 0,
            "suspend_class_refs": [f"foreign-class-{uuid4()}"],
        },
        headers={"If-Match": '"1"', "Idempotency-Key": f"foreign-{uuid4().hex}"},
    )
    assert foreign.status_code == 422
    assert foreign.json()["code"] == "CLASS_SELECTION_REQUIRED"

    archived = accepted.client.post(
        f"/api/be1/v1/classes/{class_refs[0]}/archive",
        headers={"If-Match": '"1"', "Idempotency-Key": f"archive-{uuid4().hex}"},
    )
    assert archived.status_code == 200, archived.text
    inactive = accepted.client.patch(
        base + "/capacity",
        json={
            "action": "downgrade",
            "addon_slots": 0,
            "suspend_class_refs": [class_refs[0]],
        },
        headers={"If-Match": '"1"', "Idempotency-Key": f"inactive-{uuid4().hex}"},
    )
    assert inactive.status_code == 422
    assert inactive.json()["code"] == "CLASS_SELECTION_REQUIRED"


def test_suspended_and_archived_classes_do_not_count_toward_capacity(
    capacity_acceptance_client: CapacityAcceptanceClient,
) -> None:
    accepted = capacity_acceptance_client
    class_refs = _create_classes(accepted, 3)
    suspended = accepted.client.post(
        f"/api/be1/v1/classes/{class_refs[0]}/suspend",
        headers={"If-Match": '"1"', "Idempotency-Key": f"suspend-{uuid4().hex}"},
    )
    archived = accepted.client.post(
        f"/api/be1/v1/classes/{class_refs[1]}/archive",
        headers={"If-Match": '"1"', "Idempotency-Key": f"archive-{uuid4().hex}"},
    )
    assert suspended.status_code == 200, suspended.text
    assert archived.status_code == 200, archived.text

    capacity = accepted.client.get(
        f"/api/be1/v1/organizations/{accepted.organization_id}/capacity"
    )
    assert capacity.status_code == 200, capacity.text
    assert capacity.json()["capacity"] == 11
    assert capacity.json()["active_class_count"] == 1
    assert capacity.json()["available_slots"] == 10


def test_patch_fails_closed_when_billing_sandbox_is_disabled(
    capacity_acceptance_client: CapacityAcceptanceClient,
) -> None:
    accepted = capacity_acceptance_client
    runtime = accepted.app.state.be1_runtime
    idempotency_key = f"disabled-{uuid4().hex}"
    original_settings = runtime.settings
    runtime.settings = original_settings.model_copy(
        update={"billing_sandbox_enabled": False}
    )
    try:
        response = accepted.client.patch(
            f"/api/be1/v1/organizations/{accepted.organization_id}/capacity",
            json={"action": "cancel_renewal"},
            headers={"If-Match": '"1"', "Idempotency-Key": idempotency_key},
        )
    finally:
        runtime.settings = original_settings

    assert response.status_code == 503
    assert response.json()["code"] == "PROVIDER_UNAVAILABLE"
    with runtime.session_factory() as db:
        assert db.get(
            Be1CommandReceiptModel,
            (
                accepted.subject,
                f"PATCH /organizations/{accepted.organization_id}/capacity",
                idempotency_key,
            ),
        ) is None
        assert db.get(
            BillingReceiptModel,
            (
                accepted.subject,
                "subscription.configure:" + accepted.subscription_id,
                idempotency_key,
            ),
        ) is None
        subscription = db.get(SubscriptionModel, accepted.subscription_id)
        assert subscription is not None
        assert (subscription.state, subscription.revision) == ("ACTIVE", 1)


def test_patch_fails_closed_when_capacity_read_hits_a_database_error(
    capacity_acceptance_client: CapacityAcceptanceClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    accepted = capacity_acceptance_client
    runtime = accepted.app.state.be1_runtime
    idempotency_key = f"sql-error-{uuid4().hex}"

    def unavailable(_self, _organization_id: str, *, lock: bool = False):
        raise SQLAlchemyError("synthetic capacity read failure")

    monkeypatch.setattr(Be1CapacityAdapter, "view_for_organization", unavailable)
    response = accepted.client.patch(
        f"/api/be1/v1/organizations/{accepted.organization_id}/capacity",
        json={"action": "cancel_renewal"},
        headers={"If-Match": '"1"', "Idempotency-Key": idempotency_key},
    )

    assert response.status_code == 503
    assert response.json()["code"] == "PROVIDER_UNAVAILABLE"
    with runtime.session_factory() as db:
        assert db.get(
            Be1CommandReceiptModel,
            (
                accepted.subject,
                f"PATCH /organizations/{accepted.organization_id}/capacity",
                idempotency_key,
            ),
        ) is None
        assert db.get(
            BillingReceiptModel,
            (
                accepted.subject,
                "subscription.configure:" + accepted.subscription_id,
                idempotency_key,
            ),
        ) is None
        subscription = db.get(SubscriptionModel, accepted.subscription_id)
        assert subscription is not None
        assert (subscription.state, subscription.revision) == ("ACTIVE", 1)


def test_non_manager_capacity_get_is_hidden_as_not_found(
    capacity_acceptance_client: CapacityAcceptanceClient,
) -> None:
    accepted = capacity_acceptance_client
    teacher_subject = f"synthetic-capacity-teacher-{uuid4()}"
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        db.add(
            AdultIdentityModel(
                subject=teacher_subject,
                issuer="synthetic-test-issuer",
                state="active",
                account_role="teacher",
            )
        )
        db.add(
            OrganizationAssignmentModel(
                assignment_id=str(uuid4()),
                organization_id=accepted.organization_id,
                subject=teacher_subject,
                class_id=None,
                role="teacher",
                active=True,
            )
        )

    manager_verifier = accepted.app.dependency_overrides[get_verified_adult]
    teacher = VerifiedPrincipal(
        subject=teacher_subject,
        issuer="synthetic-test-issuer",
        roles=frozenset(),
        token_id="synthetic-capacity-teacher-token",
    )

    async def verified_teacher() -> VerifiedPrincipal:
        return teacher

    accepted.app.dependency_overrides[get_verified_adult] = verified_teacher
    try:
        response = accepted.client.get(
            f"/api/be1/v1/organizations/{accepted.organization_id}/capacity"
        )
    finally:
        accepted.app.dependency_overrides[get_verified_adult] = manager_verifier

    assert response.status_code == 404
    assert response.json()["code"] == "RESOURCE_NOT_FOUND"


def test_concurrent_same_key_patch_replays_one_committed_command(
    capacity_acceptance_client: CapacityAcceptanceClient,
) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    accepted = capacity_acceptance_client
    url = f"/api/be1/v1/organizations/{accepted.organization_id}/capacity"
    key = f"concurrent-patch-{uuid4().hex}"
    barrier = Barrier(2)

    def configure() -> tuple[int, dict[str, object]]:
        barrier.wait(timeout=10)
        response = accepted.client.patch(
            url,
            json={"action": "cancel_renewal"},
            headers={"If-Match": '"1"', "Idempotency-Key": key},
        )
        return response.status_code, response.json()

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _index: configure(), range(2)))

    assert [status for status, _body in outcomes] == [200, 200]
    assert outcomes[0][1] == outcomes[1][1]
    assert outcomes[0][1]["revision"] == 2
    with accepted.app.state.be1_runtime.session_factory() as db:
        assert db.get(
            Be1CommandReceiptModel,
            (accepted.subject, f"PATCH /organizations/{accepted.organization_id}/capacity", key),
        ) is not None
        assert db.get(
            BillingReceiptModel,
            (accepted.subject, "subscription.configure:" + accepted.subscription_id, key),
        ) is not None
        assert db.scalar(
            select(func.count()).select_from(SubscriptionEventModel).where(
                SubscriptionEventModel.subscription_id == accepted.subscription_id,
                SubscriptionEventModel.kind == "SUBSCRIPTION_CANCEL_RENEWAL",
            )
        ) == 1


def test_manager_can_cancel_and_resume_subscription_renewal(
    capacity_acceptance_client: CapacityAcceptanceClient,
) -> None:
    accepted = capacity_acceptance_client
    url = f"/api/be1/v1/organizations/{accepted.organization_id}/capacity"

    cancelled = accepted.client.patch(
        url,
        json={"action": "cancel_renewal"},
        headers={"If-Match": '"1"', "Idempotency-Key": f"cancel-{uuid4().hex}"},
    )
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["subscription_state"] == "CANCEL_AT_PERIOD_END"
    assert cancelled.json()["revision"] == 2

    resumed = accepted.client.patch(
        url,
        json={"action": "resume_renewal"},
        headers={"If-Match": '"2"', "Idempotency-Key": f"resume-{uuid4().hex}"},
    )
    assert resumed.status_code == 200, resumed.text
    assert resumed.json()["subscription_state"] == "ACTIVE"
    assert resumed.json()["revision"] == 3


def test_patch_rejects_a_subscription_after_its_period_ends(
    capacity_acceptance_client: CapacityAcceptanceClient,
) -> None:
    accepted = capacity_acceptance_client
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        subscription = db.get(SubscriptionModel, accepted.subscription_id)
        assert subscription is not None
        subscription.period_end = datetime.now(UTC) - timedelta(seconds=1)

    response = accepted.client.patch(
        f"/api/be1/v1/organizations/{accepted.organization_id}/capacity",
        json={"action": "cancel_renewal"},
        headers={"If-Match": '"1"', "Idempotency-Key": f"ended-{uuid4().hex}"},
    )
    assert response.status_code == 409
    assert response.json()["code"] == "SUBSCRIPTION_PERIOD_ENDED"


def test_manager_cannot_read_platform_admin_capacity_prices(
    capacity_acceptance_client: CapacityAcceptanceClient,
) -> None:
    response = capacity_acceptance_client.client.get(
        "/api/platform-admin/v1/billing/sandbox/capacity-prices"
    )
    assert response.status_code == 403
    assert response.json()["code"] == "ACTION_NOT_ALLOWED"
