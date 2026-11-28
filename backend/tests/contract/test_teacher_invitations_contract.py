"""HTTP contract checks for Teacher invitation and resend routes with local fakes."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.teacher_invitations import (
    TeacherInvitationIdempotencyMismatch,
    TeacherInvitationIdentityUnavailable,
    TeacherInvitationKeyUnavailable,
    TeacherInvitationNotFound,
    TeacherInvitationResult,
    TeacherInvitationSetupUnavailable,
    TeacherInvitationStoreUnavailable,
)
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.openapi_contract import (
    IDEMPOTENCY_MISMATCH_OPERATION_KEYS,
    MOUNTED_OPERATIONS,
    TEACHER_INVITATION_OPERATIONS,
)
from sketch2life.interfaces.http.routers.teacher_invitations import (
    get_teacher_invitation_service,
)

ORG = "school-contract"
ACTOR = "manager-uid-contract"
ISSUER = "synthetic-issuer"
ACCOUNT_REF = "12345678-1234-4234-8234-123456789abc"
EMAIL_SENTINEL = "teacher.sentinel@example.test"
UID_SENTINEL = "provider-uid-sentinel"
LINK_SENTINEL = "https://example.test/action?token=private-action-token"
INVITE_PATH = f"/api/be1/v1/organizations/{ORG}/teacher-invitations"
RESEND_PATH = f"{INVITE_PATH}/{ACCOUNT_REF}/resend"
OPERATIONS = {
    ("post", "/api/be1/v1/organizations/{organization_id}/teacher-invitations"),
    (
        "post",
        "/api/be1/v1/organizations/{organization_id}/teacher-invitations/{account_ref}/resend",
    ),
}


@pytest.fixture(autouse=True)
def _environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", "postgresql+psycopg://user:pw@localhost:9/db")
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    try:
        yield
    finally:
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


class FakeScopeDatabase:
    def __init__(
        self,
        *,
        scoped: bool = True,
        manager: bool = True,
        class_level_only: bool = False,
    ) -> None:
        self.scoped = scoped
        self.manager = manager
        self.class_level_only = class_level_only

    def get(self, model: type, key: str):
        if model is AdultIdentityModel:
            role = "school_manager" if self.manager else "teacher"
            return SimpleNamespace(
                subject=key,
                issuer=ISSUER,
                state="active",
                account_role=role,
            )
        return SimpleNamespace(organization_id=key, state="active")

    def scalars(self, _statement):
        rows = (
            [
                SimpleNamespace(
                    organization_id=ORG,
                    subject=ACTOR,
                    class_id="class-contract" if self.class_level_only else None,
                    role="school_admin" if self.manager else "teacher",
                    active=True,
                    assignment_id="assignment-contract",
                )
            ]
            if self.scoped
            else []
        )
        return SimpleNamespace(all=lambda: rows)


class FakeInvitationService:
    def __init__(
        self,
        *,
        invite_error: Exception | None = None,
        resend_error: Exception | None = None,
    ):
        self.invite_error = invite_error
        self.resend_error = resend_error
        self.calls: list[tuple[str, dict[str, object]]] = []

    def invite_teacher(self, **kwargs: object) -> TeacherInvitationResult:
        self.calls.append(("invite", kwargs))
        if self.invite_error is not None:
            raise self.invite_error
        return TeacherInvitationResult(account_ref=ACCOUNT_REF)

    def resend_teacher_invitation(self, **kwargs: object) -> TeacherInvitationResult:
        self.calls.append(("resend", kwargs))
        if self.resend_error is not None:
            raise self.resend_error
        return TeacherInvitationResult(account_ref=ACCOUNT_REF)


@contextmanager
def _served(
    *,
    database: FakeScopeDatabase | None = None,
    service: FakeInvitationService | None = None,
    authenticate: bool = True,
) -> Iterator[tuple[TestClient, FakeInvitationService]]:
    application = create_app(_composition_profile="classroom")
    service = service or FakeInvitationService()
    application.dependency_overrides[get_db] = lambda: database or FakeScopeDatabase()
    application.dependency_overrides[get_teacher_invitation_service] = lambda: service
    if authenticate:
        application.dependency_overrides[get_verified_adult] = lambda: VerifiedPrincipal(
            subject=ACTOR,
            issuer=ISSUER,
            roles=frozenset(),
        )
    else:
        def unauthenticated() -> VerifiedPrincipal:
            raise HTTPException(
                status_code=401,
                detail={"code": "AUTH_REQUIRED", "message": "Sign in is required"},
            )

        application.dependency_overrides[get_verified_adult] = unauthenticated
    with TestClient(application) as client:
        yield client, service


def _headers(key: str = "invitation-contract-key") -> dict[str, str]:
    return {"Idempotency-Key": key}


def test_both_routes_are_catalogued_and_publish_required_headers() -> None:
    application = create_app(_composition_profile="classroom")
    spec = application.openapi()

    assert set(TEACHER_INVITATION_OPERATIONS) == OPERATIONS
    assert set(MOUNTED_OPERATIONS) >= OPERATIONS
    assert set(IDEMPOTENCY_MISMATCH_OPERATION_KEYS) >= OPERATIONS
    for method, path in OPERATIONS:
        operation = spec["paths"][path][method]
        parameters = {
            parameter["name"]: parameter for parameter in operation["parameters"]
        }
        assert parameters["Idempotency-Key"]["required"] is True
        assert "202" in operation["responses"]
        assert "400" in operation["responses"]
        default_description = operation["responses"]["default"]["description"]
        for failure_status in ("409", "503"):
            # Published explicitly or grouped in the default response, depending on the amendment.
            assert failure_status in operation["responses"] or failure_status in default_description
        assert "private, no-store" in MOUNTED_OPERATIONS[(method, path)]["responses"][0][
            "description"
        ]


@pytest.mark.parametrize(
    ("path", "payload", "kind"),
    [
        (INVITE_PATH, {"email": EMAIL_SENTINEL}, "invite"),
        (RESEND_PATH, None, "resend"),
    ],
)
def test_success_responses_are_private_safe_and_do_not_echo_identity_data(
    path: str, payload: dict[str, str] | None, kind: str
) -> None:
    with _served() as (client, service):
        request = client.post(path, json=payload, headers=_headers())

    assert request.status_code == 202
    assert request.headers["Cache-Control"] == "private, no-store"
    assert request.json() == {"account_ref": ACCOUNT_REF, "status": "PENDING_VERIFICATION"}
    assert service.calls[0][0] == kind
    for sentinel in (EMAIL_SENTINEL, UID_SENTINEL, LINK_SENTINEL, "private-action-token"):
        assert sentinel not in request.text


@pytest.mark.parametrize(
    ("path", "payload"),
    [(INVITE_PATH, {"email": EMAIL_SENTINEL}), (RESEND_PATH, None)],
)
def test_authentication_guard_runs_for_both_routes(
    path: str, payload: dict[str, str] | None
) -> None:
    with _served(authenticate=False) as (client, service):
        response = client.post(path, json=payload, headers=_headers())

    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_REQUIRED"
    assert service.calls == []


def test_foreign_organization_and_absent_resend_share_the_uniform_404() -> None:
    with _served(database=FakeScopeDatabase(scoped=False)) as (foreign_client, _):
        foreign = foreign_client.post(
            INVITE_PATH,
            json={"email": EMAIL_SENTINEL},
            headers=_headers("foreign-org"),
        )
    with _served(
        service=FakeInvitationService(resend_error=TeacherInvitationNotFound())
    ) as (absent_client, _):
        absent = absent_client.post(RESEND_PATH, headers=_headers("absent-account"))

    assert foreign.status_code == absent.status_code == 404
    assert foreign.json()["code"] == absent.json()["code"] == "RESOURCE_NOT_FOUND"
    assert foreign.json()["message"] == absent.json()["message"]
    assert EMAIL_SENTINEL not in foreign.text + absent.text
    assert ACCOUNT_REF not in foreign.text + absent.text


def test_class_only_assignment_does_not_grant_organization_invitation_scope() -> None:
    with _served(database=FakeScopeDatabase(class_level_only=True)) as (client, service):
        response = client.post(
            INVITE_PATH,
            json={"email": EMAIL_SENTINEL},
            headers=_headers("class-only-manager"),
        )

    assert response.status_code == 404
    assert response.json()["code"] == "RESOURCE_NOT_FOUND"
    assert service.calls == []


def test_in_scope_non_manager_gets_action_not_allowed() -> None:
    with _served(database=FakeScopeDatabase(manager=False)) as (client, service):
        response = client.post(
            INVITE_PATH,
            json={"email": EMAIL_SENTINEL},
            headers=_headers("teacher-role"),
        )

    assert response.status_code == 403
    assert response.json()["code"] == "ACTION_NOT_ALLOWED"
    assert EMAIL_SENTINEL not in response.text
    assert service.calls == []


@pytest.mark.parametrize(
    "path,payload",
    [(INVITE_PATH, {"email": EMAIL_SENTINEL}), (RESEND_PATH, None)],
)
def test_existing_identity_refusals_use_generic_409_envelope(
    path: str, payload: dict[str, str] | None
) -> None:
    with _served(
        service=FakeInvitationService(
            invite_error=TeacherInvitationSetupUnavailable(),
            resend_error=TeacherInvitationSetupUnavailable(),
        )
    ) as (client, _):
        response = client.post(path, json=payload, headers=_headers("matrix-refusal"))

    assert response.status_code == 409
    assert response.json()["code"] == "ACCOUNT_SETUP_UNAVAILABLE"
    for sentinel in (EMAIL_SENTINEL, UID_SENTINEL, LINK_SENTINEL, ACCOUNT_REF):
        assert sentinel not in response.text


def test_provider_unavailable_is_generic_and_does_not_echo_request_email() -> None:
    with _served(
        service=FakeInvitationService(
            invite_error=TeacherInvitationIdentityUnavailable(),
        )
    ) as (client, _):
        response = client.post(
            INVITE_PATH,
            json={"email": EMAIL_SENTINEL},
            headers=_headers("provider-down"),
        )

    assert response.status_code == 503
    assert response.json()["code"] == "IDENTITY_PROVIDER_UNAVAILABLE"
    assert EMAIL_SENTINEL not in response.text


@pytest.mark.parametrize(
    ("path", "payload", "kind"),
    [
        (INVITE_PATH, {"email": EMAIL_SENTINEL}, "invite"),
        (RESEND_PATH, None, "resend"),
    ],
)
def test_idempotency_mismatch_uses_safe_400_envelope(
    path: str, payload: dict[str, str] | None, kind: str
) -> None:
    with _served(
        service=FakeInvitationService(
            invite_error=TeacherInvitationIdempotencyMismatch(),
            resend_error=TeacherInvitationIdempotencyMismatch(),
        )
    ) as (client, service):
        response = client.post(path, json=payload, headers=_headers("mismatched-key"))

    assert response.status_code == 400
    assert response.headers["Cache-Control"] == "private, no-store"
    assert response.json()["code"] == "INVALID_IDEMPOTENCY_KEY"
    assert EMAIL_SENTINEL not in response.text
    assert ACCOUNT_REF not in response.text
    assert service.calls[0][0] == kind


@pytest.mark.parametrize(
    ("path", "payload"),
    [(INVITE_PATH, {"email": EMAIL_SENTINEL}), (RESEND_PATH, None)],
)
def test_store_unavailable_uses_safe_database_error_envelope(
    path: str, payload: dict[str, str] | None
) -> None:
    with _served(
        service=FakeInvitationService(
            invite_error=TeacherInvitationStoreUnavailable(),
            resend_error=TeacherInvitationStoreUnavailable(),
        )
    ) as (client, _):
        response = client.post(path, json=payload, headers=_headers("store-unavailable"))

    assert response.status_code == 503
    assert response.headers["Cache-Control"] == "private, no-store"
    assert response.json()["code"] == "DATABASE_UNAVAILABLE"
    assert EMAIL_SENTINEL not in response.text
    assert UID_SENTINEL not in response.text
    assert LINK_SENTINEL not in response.text


def test_missing_fingerprint_key_fails_closed_with_safe_service_error() -> None:
    with _served(
        service=FakeInvitationService(invite_error=TeacherInvitationKeyUnavailable())
    ) as (client, _):
        response = client.post(
            INVITE_PATH,
            json={"email": EMAIL_SENTINEL},
            headers=_headers("missing-key"),
        )

    assert response.status_code == 503
    assert response.headers["Cache-Control"] == "private, no-store"
    assert response.json()["code"] == "PROVIDER_UNAVAILABLE"
    assert EMAIL_SENTINEL not in response.text


def test_invalid_email_contract_redacts_validation_input() -> None:
    with _served() as (client, service):
        response = client.post(
            INVITE_PATH,
            json={"email": "invalid-email-sentinel"},
            headers=_headers("invalid-email"),
        )

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"
    assert "invalid-email-sentinel" not in response.text
    assert service.calls == []
