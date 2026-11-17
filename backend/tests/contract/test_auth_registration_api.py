from __future__ import annotations

from dataclasses import dataclass, field

from fastapi.testclient import TestClient

from sketch2life.application.ports.identity import (
    IdentityAccountConflict,
    IdentityAccountProvisioningUnavailable,
)
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.interfaces.http.app import create_app


@dataclass
class ProvisionerSpy:
    calls: list[tuple[str, str]] = field(default_factory=list)
    error: Exception | None = None

    def create_password_account(self, *, email: str, password: str) -> None:
        self.calls.append((email, password))
        if self.error is not None:
            raise self.error


def make_client(provisioner: ProvisionerSpy) -> tuple[TestClient, object]:
    app = create_app(
        identity_account_provisioner=provisioner,
        _composition_profile="classroom",
    )
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

    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_REGISTRATION_REQUEST"
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

    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_REGISTRATION_REQUEST"
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


def test_registration_is_disabled_outside_local_environment() -> None:
    provisioner = ProvisionerSpy()
    client, app = make_client(provisioner)
    app.state.settings = Settings(
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
