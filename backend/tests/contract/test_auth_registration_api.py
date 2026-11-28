from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError, OperationalError

from sketch2life.application.ports.identity import (
    IdentityAccountConflict,
    IdentityAccountProvisioningUnavailable,
    VerifiedPrincipal,
)
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult


@dataclass
class ProvisionerSpy:
    calls: list[tuple[str, str]] = field(default_factory=list)
    error: Exception | None = None

    def create_password_account(self, *, email: str, password: str) -> SimpleNamespace:
        self.calls.append((email, password))
        if self.error is not None:
            raise self.error
        return SimpleNamespace(
            subject="synthetic-test-subject",
            issuer="https://securetoken.google.com/synthetic-project",
        )


class _RegistrationSession:
    def __init__(self) -> None:
        self.identities: list[object] = []
        self.identities_by_subject: dict[str, object] = {}

    def add(self, identity: object) -> None:
        self.identities.append(identity)
        self.identities_by_subject[str(getattr(identity, "subject"))] = identity

    def get(self, _model: type, subject: str) -> object | None:
        return self.identities_by_subject.get(subject)

    def commit(self) -> None:
        return None


def make_client(provisioner: ProvisionerSpy) -> tuple[TestClient, object]:
    app = create_app(
        identity_account_provisioner=provisioner,
        _composition_profile="classroom",
    )
    session = _RegistrationSession()
    app.state.test_registration_session = session
    app.dependency_overrides[get_db] = lambda: session
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
        "email_verified": False,
        "role": "parent",
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


def test_registration_is_available_outside_local_environment() -> None:
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

    assert response.status_code == 201
    assert response.json() == {
        "status": "IDENTITY_CREATED",
        "email_verified": False,
        "role": "parent",
    }
    assert provisioner.calls == [("parent@example.com", "synthetic-pass")]
    assert "uid" not in response.json()
    assert "synthetic-pass" not in response.text


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


def _make_authenticated_completion_client(
    *, existing_identity: object | None = None
) -> tuple[TestClient, object, VerifiedPrincipal]:
    client, app = make_client(ProvisionerSpy())
    app.state.be1_runtime.settings = Settings(
        _env_file=None,
        env="local",
        auth_provider="firebase",
        firebase_project_id="synthetic-project",
        parent_self_registration_enabled=True,
    )
    principal = VerifiedPrincipal(
        subject="synthetic-google-subject",
        issuer="https://securetoken.google.com/synthetic-project",
        roles=frozenset(),
        email_verified=True,
    )
    app.dependency_overrides[get_verified_adult] = lambda: principal
    if existing_identity is not None:
        app.state.test_registration_session.identities_by_subject[principal.subject] = (
            existing_identity
        )
    return client, app, principal


def test_authenticated_first_parent_registration_is_server_assigned_and_idempotent() -> None:
    client, app, principal = _make_authenticated_completion_client()

    first = client.post("/api/auth/v1/registrations/complete", json={"role": "platform_admin"})
    replay = client.post("/api/auth/v1/registrations/complete")

    assert first.status_code == 200
    assert first.json() == {"role": "parent", "state": "active", "role_revision": 1}
    assert replay.status_code == 200
    assert replay.json() == first.json()
    identity = app.state.test_registration_session.identities_by_subject[principal.subject]
    assert identity.account_role == "parent"
    assert principal.subject not in first.text


def test_authenticated_parent_completion_does_not_reassign_other_scope() -> None:
    existing_teacher = SimpleNamespace(
        issuer="https://securetoken.google.com/synthetic-project",
        state="active",
        account_role="teacher",
        role_revision=1,
    )
    client, _app, principal = _make_authenticated_completion_client(
        existing_identity=existing_teacher
    )

    response = client.post("/api/auth/v1/registrations/complete")

    assert response.status_code == 409
    assert response.json()["code"] == "ACCOUNT_SETUP_UNAVAILABLE"
    assert "teacher" not in response.text.lower()
    assert principal.subject not in response.text


class _DiagnosticProvisioner:
    def __init__(self, delete_error: Exception | None = None) -> None:
        self.deleted_subjects: list[str] = []
        self.delete_error = delete_error

    def create_password_account(self, *, email: str, password: str) -> SimpleNamespace:
        return SimpleNamespace(
            subject="private-firebase-uid",
            issuer="https://securetoken.google.com/synthetic-project",
        )

    def delete_account(self, subject: str) -> None:
        self.deleted_subjects.append(subject)
        if self.delete_error is not None:
            raise self.delete_error


def _make_database_failure_client(
    commit_error: Exception, *, delete_error: Exception | None = None
) -> tuple[TestClient, _DiagnosticProvisioner, object]:
    provisioner = _DiagnosticProvisioner(delete_error=delete_error)
    app = create_app(
        identity_account_provisioner=provisioner,
        _composition_profile="classroom",
    )

    class FailingSession:
        rollback_count = 0

        def add(self, _identity: object) -> None:
            return None

        def commit(self) -> None:
            raise commit_error

        def rollback(self) -> None:
            self.rollback_count += 1

    session = FailingSession()

    def override_db():
        yield session

    app.dependency_overrides[get_db] = override_db
    return TestClient(app), provisioner, session


def test_auth_registration_logs_validated_sqlstate_without_database_message(caplog) -> None:
    email = "private-parent@example.invalid"
    password = "private-password-value"
    authorization = "Bearer private-authorization-value"
    uid = "private-firebase-uid"
    claim = "private-token-claim-value"
    child_data = "private-child-name"
    database_message = (
        "private database detail INSERT INTO adult_identity "
        f"{email} {password} {uid} {claim} {child_data}"
    )

    class DriverFailure(Exception):
        sqlstate = "23A01"

    driver_error = DriverFailure(database_message)
    commit_error = IntegrityError("private raw SQL", {}, driver_error)
    client, provisioner, session = _make_database_failure_client(commit_error)

    response = client.post(
        "/api/auth/v1/registrations",
        json={"email": email, "password": password},
        headers={"Authorization": authorization},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "ACCOUNT_SETUP_UNAVAILABLE"
    assert "sqlstate=23A01" in caplog.text
    assert "IntegrityError" in caplog.text
    assert "DriverFailure" in caplog.text
    assert "compensation_ok=True" in caplog.text
    assert session.rollback_count == 1
    assert provisioner.deleted_subjects == [uid]
    for sensitive_value in (
        database_message,
        "private raw SQL",
        authorization,
        email,
        password,
        uid,
        claim,
        child_data,
    ):
        assert sensitive_value not in caplog.text


def test_auth_registration_database_failure_keeps_existing_error_envelope(caplog) -> None:
    email = "private-parent@example.invalid"
    password = "private-password-value"
    authorization = "Bearer private-authorization-value"
    uid = "private-firebase-uid"
    claim = "private-token-claim-value"
    child_data = "private-child-name"
    database_message = f"private database detail {email} {uid} {claim} {child_data}"

    class DriverFailure(Exception):
        sqlstate = "23*01"
        pgcode = "also-invalid"

    commit_error = OperationalError("private raw SQL", {}, DriverFailure(database_message))
    client, provisioner, session = _make_database_failure_client(
        commit_error,
        delete_error=IdentityAccountProvisioningUnavailable("private compensation detail"),
    )

    response = client.post(
        "/api/auth/v1/registrations",
        json={"email": email, "password": password},
        headers={"Authorization": authorization},
    )

    assert response.status_code == 503
    assert response.json()["code"] == "ACCOUNT_SETUP_UNAVAILABLE"
    assert set(response.json()) == {
        "code",
        "message",
        "correlation_id",
        "retryable",
        "retry_after_seconds",
        "field_errors",
        "request_id",
    }
    assert response.json()["retryable"] is True
    assert response.json()["correlation_id"] == response.headers["X-Request-ID"]
    assert response.json()["request_id"] == response.headers["X-Request-ID"]
    assert "sqlstate=" not in caplog.text
    assert "compensation_ok=None" in caplog.text
    assert session.rollback_count == 1
    assert provisioner.deleted_subjects == []
    for sensitive_value in (
        database_message,
        "private raw SQL",
        "private compensation detail",
        authorization,
        email,
        password,
        uid,
        claim,
        child_data,
    ):
        assert sensitive_value not in caplog.text


def test_unknown_commit_outcome_preserves_firebase_identity_for_later_reconciliation() -> None:
    class DriverFailure(Exception):
        pass

    commit_error = OperationalError(
        "private raw SQL",
        {},
        DriverFailure("private connection detail"),
    )
    client, provisioner, _session = _make_database_failure_client(commit_error)

    response = client.post(
        "/api/auth/v1/registrations",
        json={"email": "parent@example.com", "password": "synthetic-pass"},
    )

    assert response.status_code == 503
    assert response.json()["code"] == "ACCOUNT_SETUP_UNAVAILABLE"
    assert provisioner.deleted_subjects == []
    assert "private connection detail" not in response.text
