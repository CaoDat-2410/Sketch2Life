from __future__ import annotations

from dataclasses import dataclass, field

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from sketch2life.application.ports.identity import (
    IdentityAccountConflict,
    IdentityAccountProvisioningUnavailable,
    ProvisionedIdentity,
    VerifiedPrincipal,
)
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.core_models import CorePersistenceBase
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult


@dataclass
class ProvisionerSpy:
    calls: list[tuple[str, str]] = field(default_factory=list)
    deleted_subjects: list[str] = field(default_factory=list)
    error: Exception | None = None

    def create_password_account(self, *, email: str, password: str) -> ProvisionedIdentity:
        self.calls.append((email, password))
        if self.error is not None:
            raise self.error
        return ProvisionedIdentity(
            subject=f"synthetic-firebase-subject-{len(self.calls)}",
            issuer="https://securetoken.google.com/synthetic-project",
        )

    def delete_account(self, subject: str) -> None:
        self.deleted_subjects.append(subject)
        return None


def make_client(provisioner: ProvisionerSpy) -> tuple[TestClient, object]:
    app = create_app(
        identity_account_provisioner=provisioner,
        _composition_profile="classroom",
    )
    app.state.be1_runtime.settings = Settings(
        _env_file=None,
        env="local",
        auth_provider="firebase",
        firebase_project_id="synthetic-project",
    )
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    CorePersistenceBase.metadata.create_all(engine, tables=[AdultIdentityModel.__table__])

    def override_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    return TestClient(app), app


def test_registration_creates_identity_without_returning_uid_or_password() -> None:
    provisioner = ProvisionerSpy()
    client, _ = make_client(provisioner)

    response = client.post(
        "/api/auth/v1/registrations",
        json={"email": " Parent@Example.com ", "password": "synthetic-pass"},
    )

    assert response.status_code == 201
    assert response.json() == {
        "status": "IDENTITY_CREATED",
        "role": "parent",
        "email_verified": False,
    }
    assert "X-Request-ID" in response.headers
    assert provisioner.calls == [("parent@example.com", "synthetic-pass")]
    assert "synthetic-pass" not in response.text
    assert "uid" not in response.json()


def test_registration_rejects_client_role_and_redacts_validation_input() -> None:
    provisioner = ProvisionerSpy()
    client, _ = make_client(provisioner)
    payload = {
        "email": "parent@example.com",
        "password": "secret-value-never-echo",
        "role": "PLATFORM_ADMIN",
    }

    response = client.post("/api/auth/v1/registrations", json=payload)

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"
    assert "secret-value-never-echo" not in response.text
    assert "parent@example.com" not in response.text
    assert provisioner.calls == []


def test_registration_rejects_invalid_email_and_short_password_safely() -> None:
    provisioner = ProvisionerSpy()
    client, _ = make_client(provisioner)

    response = client.post(
        "/api/auth/v1/registrations",
        json={"email": "not-an-email", "password": "short"},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"
    assert "not-an-email" not in response.text
    assert "short" not in response.text
    assert provisioner.calls == []


def test_duplicate_account_uses_generic_setup_conflict() -> None:
    provisioner = ProvisionerSpy(error=IdentityAccountConflict())
    client, _ = make_client(provisioner)

    response = client.post(
        "/api/auth/v1/registrations",
        json={"email": "parent@example.com", "password": "synthetic-pass"},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "ACCOUNT_SETUP_UNAVAILABLE"
    assert "parent@example.com" not in response.text
    assert "synthetic-pass" not in response.text


def test_provider_failure_is_generic_and_does_not_echo_identity_data() -> None:
    provisioner = ProvisionerSpy(
        error=IdentityAccountProvisioningUnavailable("private provider detail")
    )
    client, _ = make_client(provisioner)

    response = client.post(
        "/api/auth/v1/registrations",
        json={"email": "parent@example.com", "password": "synthetic-pass"},
    )

    assert response.status_code == 503
    assert response.json()["code"] == "IDENTITY_PROVIDER_UNAVAILABLE"
    assert "private provider detail" not in response.text
    assert "synthetic-pass" not in response.text


def test_unknown_commit_outcome_preserves_firebase_identity_for_later_reconciliation() -> None:
    provisioner = ProvisionerSpy()
    client, app = make_client(provisioner)

    class CommitOutcomeUnknownSession:
        def add(self, _identity: AdultIdentityModel) -> None:
            return None

        def commit(self) -> None:
            raise OperationalError("COMMIT", {}, RuntimeError("private connection detail"))

        def rollback(self) -> None:
            return None

    def override_db():
        yield CommitOutcomeUnknownSession()

    app.dependency_overrides[get_db] = override_db
    response = client.post(
        "/api/auth/v1/registrations",
        json={"email": "parent@example.com", "password": "synthetic-pass"},
    )

    assert response.status_code == 503
    assert response.json()["code"] == "ACCOUNT_SETUP_UNAVAILABLE"
    assert "private connection detail" not in response.text
    assert provisioner.deleted_subjects == []


def test_registration_is_disabled_outside_local_environment() -> None:
    provisioner = ProvisionerSpy()
    client, app = make_client(provisioner)
    app.state.be1_runtime.settings = Settings(
        _env_file=None,
        env="staging",
        auth_provider="firebase",
        firebase_project_id="synthetic-project",
    )

    response = client.post(
        "/api/auth/v1/registrations",
        json={"email": "parent@example.com", "password": "synthetic-pass"},
    )

    assert response.status_code == 404
    assert response.json()["code"] == "REGISTRATION_UNAVAILABLE"
    assert provisioner.calls == []


def test_authenticated_first_parent_registration_is_server_assigned_and_idempotent() -> None:
    client, app = make_client(ProvisionerSpy())
    principal = VerifiedPrincipal(
        subject="synthetic-google-subject",
        issuer="https://securetoken.google.com/synthetic-project",
        roles=frozenset(),
    )
    app.dependency_overrides[get_verified_adult] = lambda: principal

    first = client.post("/api/auth/v1/registrations/complete", json={"role": "platform_admin"})
    replay = client.post("/api/auth/v1/registrations/complete")

    assert first.status_code == 200
    assert first.json() == {"role": "parent", "state": "active", "role_revision": 1}
    assert replay.status_code == 200
    assert replay.json() == first.json()
    assert "synthetic-google-subject" not in first.text


def test_authenticated_parent_completion_does_not_reassign_other_scope() -> None:
    client, app = make_client(ProvisionerSpy())
    principal = VerifiedPrincipal(
        subject="synthetic-teacher-subject",
        issuer="https://securetoken.google.com/synthetic-project",
        roles=frozenset(),
    )
    app.dependency_overrides[get_verified_adult] = lambda: principal
    session_dependency = app.dependency_overrides[get_db]()
    session = next(session_dependency)
    try:
        session.add(
            AdultIdentityModel(
                account_id="550e8400-e29b-41d4-a716-446655440000",
                subject=principal.subject,
                issuer=principal.issuer,
                state="active",
                account_role="teacher",
                role_revision=1,
            )
        )
        session.commit()
    finally:
        session_dependency.close()

    response = client.post("/api/auth/v1/registrations/complete")

    assert response.status_code == 409
    assert response.json()["code"] == "ACCOUNT_SETUP_UNAVAILABLE"
    assert "teacher" not in response.text.lower()
    assert principal.subject not in response.text


def test_registration_limits_attempts_per_client_ip() -> None:
    provisioner = ProvisionerSpy()
    client, _ = make_client(provisioner)
    payload = {"email": "parent@example.com", "password": "synthetic-pass"}

    responses = [client.post("/api/auth/v1/registrations", json=payload) for _ in range(6)]

    assert [response.status_code for response in responses] == [201, 201, 201, 201, 201, 429]
    assert responses[-1].json()["code"] == "RATE_LIMITED"
    assert responses[-1].headers["Retry-After"] == "900"


def test_openapi_registration_contract_has_no_role_or_sensitive_response_fields() -> None:
    client, _ = make_client(ProvisionerSpy())
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    operation = schema["paths"]["/api/auth/v1/registrations"]["post"]
    request_schema = schema["components"]["schemas"]["RegistrationRequest"]["properties"]
    response_schema = schema["components"]["schemas"]["RegistrationCreated"]["properties"]
    assert set(request_schema) == {"email", "password"}
    assert "role" not in request_schema
    assert "password" not in response_schema
    assert "responses" in operation
