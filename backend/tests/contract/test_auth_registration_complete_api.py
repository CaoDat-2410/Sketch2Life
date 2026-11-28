from __future__ import annotations

import logging
from collections.abc import Iterator
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import (
    get_db,
    get_runtime,
    get_verified_adult,
)
from sketch2life.interfaces.http.routers.auth_registration import RegistrationRateLimiter

COMPLETION_PATH = "/api/auth/v1/registrations/complete"
PROJECT_ID = "synthetic-project"


class SyntheticDriverError(Exception):
    sqlstate = "08006"


class FakeSession:
    def __init__(
        self,
        identities: dict[str, AdultIdentityModel] | None = None,
        *,
        commit_error: SQLAlchemyError | None = None,
        race_identity: AdultIdentityModel | None = None,
    ) -> None:
        self.identities = identities or {}
        self.commit_error = commit_error
        self.race_identity = race_identity
        self.pending: AdultIdentityModel | None = None
        self.get_calls: list[str] = []
        self.commit_calls = 0

    def get(self, model: type[AdultIdentityModel], subject: str) -> AdultIdentityModel | None:
        assert model is AdultIdentityModel
        self.get_calls.append(subject)
        return self.identities.get(subject)

    def add(self, identity: AdultIdentityModel) -> None:
        self.pending = identity

    def commit(self) -> None:
        self.commit_calls += 1
        if self.race_identity is not None:
            self.identities[self.race_identity.subject] = self.race_identity
            self.race_identity = None
            raise IntegrityError("INSERT", {}, SyntheticDriverError("synthetic conflict"))
        if self.commit_error is not None:
            raise self.commit_error
        assert self.pending is not None
        self.identities[self.pending.subject] = self.pending
        self.pending = None

    def rollback(self) -> None:
        self.pending = None


class FakeTokenVerifier:
    def __init__(self, principal: VerifiedPrincipal) -> None:
        self.principal = principal
        self.tokens: list[str] = []

    async def verify(self, encoded_token: str) -> VerifiedPrincipal:
        self.tokens.append(encoded_token)
        return self.principal


@pytest.fixture(autouse=True)
def isolate_settings_from_dotenv(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[None]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.delenv("SKETCH2LIFE_DATABASE_URL", raising=False)
    monkeypatch.delenv("SKETCH2LIFE_PARENT_SELF_REGISTRATION_ENABLED", raising=False)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    try:
        yield
    finally:
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def verified_principal(
    *,
    subject: str = "synthetic-firebase-subject",
    issuer: str = f"https://securetoken.google.com/{PROJECT_ID}",
    email_verified: bool = True,
) -> VerifiedPrincipal:
    return VerifiedPrincipal(
        subject=subject,
        issuer=issuer,
        roles=frozenset({"platform_admin"}),
        token_id="synthetic-token-id",
        email="synthetic-parent@example.invalid",
        email_verified=email_verified,
    )


def identity_row(
    principal: VerifiedPrincipal,
    *,
    issuer: str | None = None,
    role: str = "parent",
    state: str = "active",
    role_revision: int = 1,
) -> AdultIdentityModel:
    return AdultIdentityModel(
        account_id=str(uuid4()),
        subject=principal.subject,
        issuer=issuer or principal.issuer,
        state=state,
        account_role=role,
        role_revision=role_revision,
    )


def make_client(
    *,
    enabled: bool = True,
    principal: VerifiedPrincipal | None = None,
    session: FakeSession | None = None,
    override_principal: bool = True,
) -> tuple[TestClient, FastAPI, FakeSession, VerifiedPrincipal]:
    principal = principal or verified_principal()
    session = session or FakeSession()
    application = create_app(_composition_profile="classroom")
    application.state.be1_runtime.settings = Settings(
        _env_file=None,
        env="test",
        firebase_project_id=PROJECT_ID,
        parent_self_registration_enabled=enabled,
    )
    application.dependency_overrides[get_db] = lambda: session
    if override_principal:
        application.dependency_overrides[get_verified_adult] = lambda: principal
    else:
        runtime = application.state.be1_runtime
        runtime.database_error = None
        runtime.session_factory = object()
        runtime.identity_verifier = FakeTokenVerifier(principal)
        application.dependency_overrides[get_runtime] = lambda: runtime
    return TestClient(application), application, session, principal


def test_complete_requires_a_verified_firebase_bearer() -> None:
    client, application, session, _ = make_client(override_principal=False)

    response = client.post(COMPLETION_PATH)

    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_REQUIRED"
    assert session.get_calls == []

    token = "synthetic-bearer-token"
    response = client.post(
        COMPLETION_PATH,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {"role": "parent", "state": "active", "role_revision": 1}
    assert application.state.be1_runtime.identity_verifier.tokens == [token]


def test_complete_is_refused_with_the_generic_code_when_the_setting_is_off() -> None:
    client, _, session, _ = make_client(enabled=False)

    response = client.post(COMPLETION_PATH)

    assert response.status_code == 403
    assert response.json()["code"] == "ACCOUNT_SETUP_UNAVAILABLE"
    assert session.get_calls == []


def test_complete_requires_a_verified_email() -> None:
    principal = verified_principal(email_verified=False)
    client, _, session, _ = make_client(principal=principal)

    response = client.post(COMPLETION_PATH)

    assert response.status_code == 403
    assert response.json()["code"] == "ACCOUNT_SETUP_UNAVAILABLE"
    assert session.get_calls == []


def test_complete_refuses_a_verified_principal_from_another_firebase_project() -> None:
    principal = verified_principal(
        issuer="https://securetoken.google.com/other-project",
    )
    client, _, session, _ = make_client(principal=principal)

    response = client.post(COMPLETION_PATH)

    assert response.status_code == 403
    assert response.json()["code"] == "ACCOUNT_SETUP_UNAVAILABLE"
    assert "other-project" not in response.text
    assert session.get_calls == []


def test_complete_ignores_any_client_supplied_role_or_scope() -> None:
    client, application, session, principal = make_client()

    response = client.post(
        COMPLETION_PATH,
        json={
            "role": "platform_admin",
            "uid": "client-supplied-uid",
            "account_scope": "organization:client-supplied",
            "account_id": "client-supplied-account-id",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"role": "parent", "state": "active", "role_revision": 1}
    created = session.identities[principal.subject]
    assert created.subject == principal.subject
    assert created.account_role == "parent"
    assert created.issuer == principal.issuer
    assert created.account_id != "client-supplied-account-id"
    assert "scope" not in response.json()
    assert "client-supplied-uid" not in response.text
    operation = application.openapi(fe_projected=False)["paths"][COMPLETION_PATH]["post"]
    assert "requestBody" not in operation


def test_complete_creates_a_parent_identity_with_a_server_assigned_account_id() -> None:
    client, _, session, principal = make_client()

    response = client.post(COMPLETION_PATH)

    assert response.status_code == 200
    assert response.json() == {"role": "parent", "state": "active", "role_revision": 1}
    created = session.identities[principal.subject]
    assert created.account_role == "parent"
    assert created.state == "active"
    assert created.role_revision == 1
    assert created.issuer == f"https://securetoken.google.com/{PROJECT_ID}"
    assert str(UUID(created.account_id)) == created.account_id


def test_complete_is_idempotent_for_the_exact_issuer_subject_and_role() -> None:
    principal = verified_principal()
    existing = identity_row(principal, role_revision=4)
    session = FakeSession({principal.subject: existing})
    client, _, _, _ = make_client(principal=principal, session=session)

    response = client.post(COMPLETION_PATH)

    assert response.status_code == 200
    assert response.json() == {"role": "parent", "state": "active", "role_revision": 4}
    assert session.commit_calls == 0
    assert session.identities[principal.subject] is existing


@pytest.mark.parametrize(
    ("issuer", "role", "state", "hidden_value"),
    [
        (None, "teacher", "active", "teacher"),
        ("https://securetoken.google.com/other-project", "parent", "active", "other-project"),
        (None, "parent", "disabled", "disabled"),
    ],
)
def test_complete_refuses_an_existing_row_of_another_role_or_issuer_without_disclosure(
    issuer: str | None,
    role: str,
    state: str,
    hidden_value: str,
) -> None:
    principal = verified_principal()
    existing = identity_row(principal, issuer=issuer, role=role, state=state)
    session = FakeSession({principal.subject: existing})
    client, _, _, _ = make_client(principal=principal, session=session)

    response = client.post(COMPLETION_PATH)

    assert response.status_code == 409
    assert response.json()["code"] == "ACCOUNT_SETUP_UNAVAILABLE"
    assert hidden_value not in response.text
    assert principal.subject not in response.text


def test_complete_accepts_an_exact_parent_identity_after_a_uniqueness_race() -> None:
    principal = verified_principal()
    raced_identity = identity_row(principal, role_revision=7)
    session = FakeSession(race_identity=raced_identity)
    client, _, _, _ = make_client(principal=principal, session=session)

    response = client.post(COMPLETION_PATH)

    assert response.status_code == 200
    assert response.json() == {"role": "parent", "state": "active", "role_revision": 7}
    assert session.get_calls == [principal.subject, principal.subject]


def test_complete_refuses_a_mismatched_identity_after_a_uniqueness_race() -> None:
    principal = verified_principal()
    raced_identity = identity_row(principal, role="teacher")
    session = FakeSession(race_identity=raced_identity)
    client, _, _, _ = make_client(principal=principal, session=session)

    response = client.post(COMPLETION_PATH)

    assert response.status_code == 409
    assert response.json()["code"] == "ACCOUNT_SETUP_UNAVAILABLE"
    assert "teacher" not in response.text.lower()


def test_complete_uses_the_shared_registration_rate_limit() -> None:
    client, application, _, _ = make_client()
    limiter = application.state.registration_rate_limiter

    assert isinstance(limiter, RegistrationRateLimiter)
    for _ in range(5):
        assert limiter.allow("testclient") is True

    response = client.post(COMPLETION_PATH)

    assert response.status_code == 429
    assert response.json()["code"] == "RATE_LIMITED"


def test_complete_checks_the_setting_before_verifying_the_token() -> None:
    client, application, session, principal = make_client(enabled=False, override_principal=False)

    response = client.post(COMPLETION_PATH, headers={"Authorization": "Bearer synthetic-token"})

    assert response.status_code == 403
    assert response.json()["code"] == "ACCOUNT_SETUP_UNAVAILABLE"
    assert application.state.be1_runtime.identity_verifier.tokens == []
    assert session.get_calls == []


def test_complete_counts_attempts_before_the_token_is_verified() -> None:
    client, application, _, _ = make_client(override_principal=False)
    limiter = application.state.registration_rate_limiter
    for _ in range(5):
        assert limiter.allow("testclient") is True

    response = client.post(COMPLETION_PATH, headers={"Authorization": "Bearer synthetic-token"})

    assert response.status_code == 429
    assert application.state.be1_runtime.identity_verifier.tokens == []


def test_complete_logs_contain_no_email_uid_or_claims(caplog: pytest.LogCaptureFixture) -> None:
    principal = verified_principal(subject="synthetic-firebase-uid-81")
    private_driver_error = SyntheticDriverError(
        "synthetic-parent@example.invalid private-claim-value synthetic-bearer-token"
    )
    session = FakeSession(commit_error=OperationalError("COMMIT", {}, private_driver_error))
    client, _, _, _ = make_client(principal=principal, session=session)
    caplog.set_level(
        logging.ERROR,
        logger="sketch2life.interfaces.http.routers.auth_registration",
    )

    response = client.post(
        COMPLETION_PATH,
        headers={"Authorization": "Bearer synthetic-bearer-token"},
    )

    assert response.status_code == 503
    assert response.json()["code"] == "ACCOUNT_SETUP_UNAVAILABLE"
    for private_value in (
        "synthetic-parent@example.invalid",
        "synthetic-firebase-uid-81",
        "synthetic-token-id",
        "synthetic-bearer-token",
        "private-claim-value",
        "platform_admin",
    ):
        assert private_value not in caplog.text
        assert private_value not in response.text
    assert "stage=completion_commit_failed" in caplog.text
    assert "sqlstate=08006" in caplog.text
