"""HTTP acceptance checks against an explicitly isolated PostgreSQL database.

Set BE1_TEST_DATABASE_URL to a disposable database whose name contains
``be1_acceptance``. The verifier override below substitutes only the external Firebase
token boundary; all BE1 routes, authorization queries, transactions, migrations, audit,
and outbox records still use the real application and PostgreSQL adapters.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    ClassroomSessionModel,
    ConsentRecordModel,
    DataLifecycleRequestModel,
    DeviceGrantModel,
    EnrollmentModel,
    ManagedProfileModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)
from sketch2life.infrastructure.persistence.be1_worker import run_retention_once
from sketch2life.infrastructure.persistence.core_models import (
    CoreAssetMetadataModel,
    CoreAuditEntryModel,
    CoreOutboxEventModel,
)
from sketch2life.infrastructure.storage.persistent_local_artifacts import LocalArtifactStore
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult


@dataclass
class AcceptanceClient:
    app: FastAPI
    client: TestClient
    organization_id: str
    subject: str


@pytest.fixture
def acceptance_client(monkeypatch: pytest.MonkeyPatch, tmp_path) -> Iterator[AcceptanceClient]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to run PostgreSQL-backed BE1 acceptance tests")
    if "be1_acceptance" not in database_url.rsplit("/", 1)[-1]:
        pytest.fail("BE1_TEST_DATABASE_URL must point to a disposable *be1_acceptance database")

    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_BE1_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()

    app = create_app()
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("BE1 PostgreSQL runtime did not initialize")
    with runtime.engine.connect() as connection:
        if not connection.dialect.has_table(connection, "be1_organizations"):
            pytest.fail("BE1_TEST_DATABASE_URL has not been migrated to Alembic head")

    organization_id = f"synthetic-org-{uuid4()}"
    subject = f"synthetic-adult-{uuid4()}"
    with runtime.session_factory.begin() as db:
        db.add(
            OrganizationModel(
                organization_id=organization_id,
                display_name="Synthetic Acceptance Organization",
                state="active",
            )
        )
        db.add(AdultIdentityModel(subject=subject, issuer="synthetic-test-issuer", state="active"))
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

    principal = VerifiedPrincipal(
        subject=subject,
        issuer="synthetic-test-issuer",
        roles=frozenset(),
        token_id="synthetic-test-token",
    )

    async def verified_test_adult() -> VerifiedPrincipal:
        return principal

    app.dependency_overrides[get_verified_adult] = verified_test_adult
    with TestClient(app) as client:
        yield AcceptanceClient(app, client, organization_id, subject)
    app.dependency_overrides.clear()
    runtime.engine.dispose()
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()


def _url(acceptance: AcceptanceClient, suffix: str) -> str:
    return f"/api/be1/v1/organizations/{acceptance.organization_id}{suffix}"


def test_real_http_writes_audits_outbox_and_enforces_assignment_scope(
    acceptance_client: AcceptanceClient,
) -> None:
    accepted = acceptance_client
    client = accepted.client

    organization = client.get(_url(accepted, ""))
    assert organization.status_code == 200
    assert organization.json() == {
        "contract": "Be1OrganizationV1",
        "organization_id": accepted.organization_id,
        "display_name": "Synthetic Acceptance Organization",
    }
    assert organization.headers["X-Request-ID"]

    created_class = client.post(
        _url(accepted, "/classes"), json={"display_name": "Synthetic Class"}
    )
    assert created_class.status_code == 201, created_class.text
    class_id = created_class.json()["class_id"]
    assert created_class.json()["contract"] == "Be1ClassV1"

    created_session = client.post(
        _url(accepted, "/sessions"),
        json={
            "class_id": class_id,
            "purpose_ref": "synthetic-purpose-pending",
            "configuration": {"activity_ref": "synthetic-activity"},
        },
    )
    assert created_session.status_code == 201, created_session.text
    session = created_session.json()
    session_id = session["session_id"]
    assert session["state"] == "configured"
    assert "join_code_sha256" not in session["configuration"]
    assert session["join_code"]

    lobby = client.post(
        _url(accepted, f"/sessions/{session_id}/lobby"), json={"expected_revision": 1}
    )
    assert lobby.status_code == 200, lobby.text
    assert (lobby.json()["state"], lobby.json()["revision"]) == ("lobby", 2)

    stale = client.post(
        _url(accepted, f"/sessions/{session_id}/lobby"), json={"expected_revision": 1}
    )
    assert stale.status_code == 409
    assert stale.json()["code"] == "STALE_SESSION_REVISION"
    assert stale.json()["request_id"] == stale.headers["X-Request-ID"]

    group = client.post(
        _url(accepted, f"/sessions/{session_id}/groups"),
        json={"display_name": "Synthetic Group"},
    )
    assert group.status_code == 201, group.text
    group_id = group.json()["group_id"]
    assert group.json()["session_revision"] == 3

    locked = client.post(
        _url(accepted, f"/sessions/{session_id}/groups/{group_id}/control"),
        json={"action": "lock", "expected_revision": 3},
    )
    assert locked.status_code == 200, locked.text
    assert (locked.json()["state"], locked.json()["session_revision"]) == ("locked", 4)

    idempotent_lock = client.post(
        _url(accepted, f"/sessions/{session_id}/groups/{group_id}/control"),
        json={"action": "lock", "expected_revision": 4},
    )
    assert idempotent_lock.status_code == 200
    assert idempotent_lock.json()["session_revision"] == 4

    unlocked = client.post(
        _url(accepted, f"/sessions/{session_id}/groups/{group_id}/control"),
        json={"action": "unlock", "expected_revision": 4},
    )
    assert unlocked.status_code == 200, unlocked.text
    assert (unlocked.json()["state"], unlocked.json()["session_revision"]) == ("active", 5)

    data_request = client.post(
        _url(accepted, "/data-requests"),
        json={"request_type": "delete", "target_ref": "synthetic-subject-ref"},
    )
    assert data_request.status_code == 202, data_request.text
    assert data_request.json()["state"] == "requested"
    assert data_request.json()["completion_claimed"] is False
    read_request = client.get(
        _url(accepted, f"/data-requests/{data_request.json()['request_id']}")
    )
    assert read_request.status_code == 200
    assert read_request.json()["state"] == "requested"
    assert read_request.json()["unresolved_items"] == 0
    assert read_request.json()["completion_claimed"] is False

    outsider_subject = f"synthetic-observer-{uuid4()}"
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        db.add(
            AdultIdentityModel(
                subject=outsider_subject, issuer="synthetic-test-issuer", state="active"
            )
        )
        db.flush()
        db.add(
            OrganizationAssignmentModel(
                assignment_id=str(uuid4()),
                organization_id=accepted.organization_id,
                subject=outsider_subject,
                class_id=None,
                role="observer",
                active=True,
            )
        )

    async def observer_principal() -> VerifiedPrincipal:
        return VerifiedPrincipal(
            subject=outsider_subject,
            issuer="synthetic-test-issuer",
            roles=frozenset(),
            token_id="synthetic-observer-token",
        )

    accepted.app.dependency_overrides[get_verified_adult] = observer_principal
    forbidden = client.post(
        _url(accepted, "/classes"), json={"display_name": "Forged role attempt"}
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["request_id"] == forbidden.headers["X-Request-ID"]
    forged_role = client.post(
        _url(accepted, "/classes"),
        json={"display_name": "Forged role attempt", "role": "school_admin"},
    )
    assert forged_role.status_code == 422
    assert forged_role.json()["code"] == "REQUEST_VALIDATION_FAILED"

    with accepted.app.state.be1_runtime.session_factory() as db:
        audit_count = db.scalar(
            select(func.count()).select_from(CoreAuditEntryModel).where(
                CoreAuditEntryModel.organization_id == accepted.organization_id
            )
        )
        outbox_count = db.scalar(
            select(func.count()).select_from(CoreOutboxEventModel).where(
                CoreOutboxEventModel.organization_id == accepted.organization_id
            )
        )
    assert audit_count == 7  # class, session, lobby, group, lock, unlock, data request
    assert outbox_count >= 7

    health = client.get("/api/be1/v1/health")
    assert health.status_code == 200, health.text
    assert health.json() == {
        "status": "ready",
        "database": "postgresql",
        "api": "be1-v1",
    }
    openapi_response = client.get("/openapi.json")
    assert openapi_response.status_code == 200
    openapi = openapi_response.json()
    be1_paths = [path for path in openapi["paths"] if path.startswith("/api/be1/v1/")]
    assert len(be1_paths) == 42
    be1_operations = sum(
        1
        for path in be1_paths
        for method in openapi["paths"][path]
        if method in {"get", "post", "put", "patch", "delete"}
    )
    assert be1_operations == 47
    assert "HTTPBearer" in openapi["components"]["securitySchemes"]
    error_schema = openapi["components"]["schemas"]["Be1Error"]
    assert set(error_schema["properties"]) == {"code", "message", "request_id"}
    upload_response = openapi["paths"][
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/artifacts"
    ]["post"]["responses"]
    assert {"413", "415", "503"}.issubset(upload_response)
    download_response = openapi["paths"][
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/artifacts/{asset_ref}"
    ]["get"]["responses"]
    assert "410" in download_response


def test_pending_consent_stays_pending_and_blocks_profile_admission_and_canvas(
    acceptance_client: AcceptanceClient,
) -> None:
    accepted = acceptance_client
    client = accepted.client
    class_response = client.post(
        _url(accepted, "/classes"), json={"display_name": "Consent Gate Class"}
    )
    assert class_response.status_code == 201, class_response.text
    class_id = class_response.json()["class_id"]

    child_id = f"synthetic-child-{uuid4()}"
    consent_response = client.post(
        _url(accepted, f"/classes/{class_id}/consents"),
        json={
            "class_id": class_id,
            "child_id": child_id,
            "purpose_ref": "synthetic-purpose-pending",
            "evidence_ref": "synthetic-evidence-reference",
        },
    )
    assert consent_response.status_code == 201, consent_response.text
    consent = consent_response.json()
    assert consent["state"] == "pending"
    assert consent["effective"] is False

    profile_response = client.post(
        _url(accepted, f"/classes/{class_id}/profiles"),
        json={
            "child_id": child_id,
            "class_id": class_id,
            "consent_id": consent["consent_id"],
            "purpose_ref": "synthetic-purpose-pending",
            "display_name": "Synthetic Child",
            "age_months": 36,
        },
    )
    assert profile_response.status_code == 409
    assert profile_response.json()["code"] == "CONSENT_NOT_EFFECTIVE"

    session_response = client.post(
        _url(accepted, "/sessions"),
        json={
            "class_id": class_id,
            "purpose_ref": "synthetic-purpose-pending",
            "configuration": {},
        },
    )
    assert session_response.status_code == 201, session_response.text
    session = session_response.json()
    session_id = session["session_id"]
    lobby = client.post(
        _url(accepted, f"/sessions/{session_id}/lobby"), json={"expected_revision": 1}
    )
    assert lobby.status_code == 200

    device_key = f"synthetic-device-key-{uuid4()}"
    join = client.post(
        _url(accepted, f"/sessions/{session_id}/join"),
        json={"join_code": session["join_code"], "device_key": device_key},
    )
    assert join.status_code == 202, join.text
    repeated_join = client.post(
        _url(accepted, f"/sessions/{session_id}/join"),
        json={"join_code": session["join_code"], "device_key": device_key},
    )
    assert repeated_join.status_code == 202
    assert repeated_join.json()["grant_id"] == join.json()["grant_id"]
    assert repeated_join.json().keys() == join.json().keys()

    grant_id = join.json()["grant_id"]
    # Seed a synthetic legacy/stale profile in the disposable database to reach the
    # admission consent check after the public profile-create path has already denied.
    with accepted.app.state.be1_runtime.session_factory.begin() as db:
        db.add(
            ManagedProfileModel(
                child_id=child_id,
                organization_id=accepted.organization_id,
                class_id=class_id,
                display_name="Synthetic Child",
                age_months=36,
                consent_id=consent["consent_id"],
                consent_purpose_ref="synthetic-purpose-pending",
                created_by=accepted.subject,
            )
        )
    admission = client.post(
        _url(accepted, f"/sessions/{session_id}/join-requests/{grant_id}/admit"),
        json={"child_id": child_id},
    )
    assert admission.status_code == 409
    assert admission.json()["code"] == "CONSENT_NOT_EFFECTIVE"

    device_canvas = client.get(
        _url(accepted, f"/sessions/{session_id}/canvas/operations"),
        headers={"X-Be1-Grant": grant_id, "X-Be1-Device-Key": device_key},
    )
    assert device_canvas.status_code == 401
    assert device_canvas.json()["code"] == "INVALID_DEVICE_CREDENTIAL"

    start = client.post(
        _url(accepted, f"/sessions/{session_id}/start"), json={"expected_revision": 3}
    )
    assert start.status_code == 409
    assert start.json()["code"] == "CONSENT_NOT_EFFECTIVE"

    with accepted.app.state.be1_runtime.session_factory() as db:
        stored_consent = db.get(ConsentRecordModel, consent["consent_id"])
        assert stored_consent is not None and stored_consent.state == "pending"
        assert db.get(ManagedProfileModel, child_id) is not None
        assert db.scalar(
            select(EnrollmentModel.enrollment_id).where(EnrollmentModel.child_id == child_id)
        ) is None
        stored_grant = db.get(DeviceGrantModel, grant_id)
        assert stored_grant is not None and stored_grant.state == "pending"
        assert stored_grant.device_key_hash != device_key
        assert db.scalar(
            select(CoreAuditEntryModel.audit_id).where(
                CoreAuditEntryModel.organization_id == accepted.organization_id,
                CoreAuditEntryModel.decision == "denied_consent_pending",
            )
        ) is not None
        assert db.scalar(
            select(CoreOutboxEventModel.event_id).where(
                CoreOutboxEventModel.organization_id == accepted.organization_id,
                CoreOutboxEventModel.event_type == "be1.consent.pending.v1",
            )
        ) is not None


def test_retention_worker_purges_local_bytes_once_but_keeps_external_purge_pending(
    acceptance_client: AcceptanceClient,
) -> None:
    accepted = acceptance_client
    client = accepted.client
    class_response = client.post(
        _url(accepted, "/classes"), json={"display_name": "Retention Acceptance Class"}
    )
    assert class_response.status_code == 201, class_response.text
    class_id = class_response.json()["class_id"]
    session_response = client.post(
        _url(accepted, "/sessions"),
        json={
            "class_id": class_id,
            "purpose_ref": "synthetic-purpose-pending",
            "configuration": {"synthetic": True},
        },
    )
    assert session_response.status_code == 201, session_response.text
    session_id = session_response.json()["session_id"]
    lobby = client.post(
        _url(accepted, f"/sessions/{session_id}/lobby"), json={"expected_revision": 1}
    )
    assert lobby.status_code == 200, lobby.text
    finish = client.post(
        _url(accepted, f"/sessions/{session_id}/finish"), json={"expected_revision": 2}
    )
    assert finish.status_code == 200, finish.text
    assert finish.json()["state"] == "finished"
    assert finish.json()["retain_until"] is not None

    runtime = accepted.app.state.be1_runtime
    content = b"synthetic retention artifact bytes"
    artifact_ref, digest = runtime.artifact_store.put(content)
    restarted_store = LocalArtifactStore(runtime.settings.be1_artifact_root)
    assert restarted_store.get(artifact_ref) == content
    now = datetime.now(UTC)
    with runtime.session_factory.begin() as db:
        session = db.get(ClassroomSessionModel, session_id)
        assert session is not None
        session.retain_until = now - timedelta(seconds=1)
        db.add(
            CoreAssetMetadataModel(
                asset_ref=artifact_ref,
                asset_version=1,
                organization_id=accepted.organization_id,
                content_sha256=digest,
                media_type="application/octet-stream",
                source_refs=[f"be1-session:{session_id}"],
                derived_from_ref=None,
            )
        )

    assert run_retention_once(runtime.session_factory, restarted_store, now=now) == 1
    assert restarted_store.get(artifact_ref) is None
    assert run_retention_once(runtime.session_factory, restarted_store, now=now) == 0
    with runtime.session_factory() as db:
        retained_session = db.get(ClassroomSessionModel, session_id)
        assert retained_session is not None
        assert retained_session.state == "finished"
        assert retained_session.configuration == {}
        assert retained_session.retention_enqueued_at == now
        assert db.get(CoreAssetMetadataModel, (artifact_ref, 1)) is None
        deletion = db.scalar(
            select(DataLifecycleRequestModel).where(
                DataLifecycleRequestModel.organization_id == accepted.organization_id,
                DataLifecycleRequestModel.target_ref == f"session:{session_id}",
            )
        )
        assert deletion is not None
        assert deletion.state == "awaiting_external_purge"
        assert deletion.unresolved_items >= 1
