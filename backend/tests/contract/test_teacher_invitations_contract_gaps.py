"""Additional HTTP contract tests for Teacher invitation gaps from cold review R1."""

from __future__ import annotations

from collections.abc import Iterator
from types import SimpleNamespace

import pytest

from sketch2life.application.ports.teacher_invitations import (
    TeacherInvitationIdentityUnavailable,
    TeacherInvitationNotFound,
    TeacherInvitationSetupUnavailable,
)
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.interfaces.http.app import create_app
from tests.contract.test_teacher_invitations_contract import (
    EMAIL_SENTINEL,
    INVITE_PATH,
    ISSUER,
    OPERATIONS,
    RESEND_PATH,
    FakeInvitationService,
    FakeScopeDatabase,
    _headers,
    _served,
)


@pytest.fixture(autouse=True)
def _offline_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv(
        "SKETCH2LIFE_DATABASE_URL",
        "postgresql+psycopg://sentinel_user:sentinel_pw@localhost:9/sentinel_db",
    )
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    try:
        yield
    finally:
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


class _OrgStateDatabase(FakeScopeDatabase):
    def __init__(self, *, org_state: str | None) -> None:
        super().__init__(scoped=True, manager=True, class_level_only=False)
        self.org_state = org_state

    def get(self, model: type, key: str):
        if model is AdultIdentityModel:
            return SimpleNamespace(
                subject=key,
                issuer=ISSUER,
                state="active",
                account_role="school_manager",
            )
        if self.org_state is None:
            return None
        return SimpleNamespace(organization_id=key, state=self.org_state)


def test_explicit_400_409_and_503_responses_published_in_openapi() -> None:
    """covers: IMPL_REVIEW_D_T-6A_R1_20261125.md P1-2"""
    spec = create_app(_composition_profile="classroom").openapi()
    for method, path in OPERATIONS:
        responses = spec["paths"][path][method]["responses"]
        assert "400" in responses
        assert "409" in responses
        assert "503" in responses


@pytest.mark.parametrize(
    ("path", "payload", "database", "service", "expected_status", "expected_code"),
    [
        (
            RESEND_PATH,
            None,
            None,
            FakeInvitationService(resend_error=TeacherInvitationNotFound()),
            404,
            "RESOURCE_NOT_FOUND",
        ),
        (
            INVITE_PATH,
            {"email": EMAIL_SENTINEL},
            FakeScopeDatabase(class_level_only=True),
            None,
            404,
            "RESOURCE_NOT_FOUND",
        ),
        (
            INVITE_PATH,
            {"email": EMAIL_SENTINEL},
            _OrgStateDatabase(org_state="suspended"),
            None,
            404,
            "RESOURCE_NOT_FOUND",
        ),
        (
            INVITE_PATH,
            {"email": EMAIL_SENTINEL},
            None,
            FakeInvitationService(invite_error=TeacherInvitationSetupUnavailable()),
            409,
            "ACCOUNT_SETUP_UNAVAILABLE",
        ),
        (
            INVITE_PATH,
            {"email": EMAIL_SENTINEL},
            None,
            FakeInvitationService(invite_error=TeacherInvitationIdentityUnavailable()),
            503,
            "IDENTITY_PROVIDER_UNAVAILABLE",
        ),
    ],
)
def test_error_envelopes_emit_private_no_store_cache_header(
    path: str,
    payload: dict[str, str] | None,
    database: FakeScopeDatabase | None,
    service: FakeInvitationService | None,
    expected_status: int,
    expected_code: str,
) -> None:
    """covers: IMPL_REVIEW_D_T-6A_R1_20261125.md P1-1"""
    with _served(database=database, service=service) as (client, _):
        response = client.post(path, json=payload, headers=_headers("error-cache-header"))

    assert response.status_code == expected_status
    assert response.json()["code"] == expected_code
    assert response.headers["Cache-Control"] == "private, no-store"


def test_foreign_organization_manager_on_resend_uses_uniform_404() -> None:
    """covers: IMPL_REVIEW_D_T-6A_R1_20261125.md Checked-Authz"""
    with _served(database=FakeScopeDatabase(scoped=False)) as (foreign_client, foreign_service):
        foreign = foreign_client.post(RESEND_PATH, headers=_headers("foreign-resend"))
    with _served(service=FakeInvitationService(resend_error=TeacherInvitationNotFound())) as (
        absent_client,
        _,
    ):
        absent = absent_client.post(RESEND_PATH, headers=_headers("absent-resend"))

    assert foreign.status_code == absent.status_code == 404
    assert foreign.json()["code"] == absent.json()["code"] == "RESOURCE_NOT_FOUND"
    assert foreign.json()["message"] == absent.json()["message"]
    assert foreign_service.calls == []


@pytest.mark.parametrize("org_state", [None, "suspended", "archived"])
@pytest.mark.parametrize(
    ("path", "payload"),
    [(INVITE_PATH, {"email": EMAIL_SENTINEL}), (RESEND_PATH, None)],
)
def test_inactive_or_missing_organization_returns_uniform_404(
    org_state: str | None, path: str, payload: dict[str, str] | None
) -> None:
    """covers: IMPL_REVIEW_D_T-6A_R1_20261125.md Checked-Authz"""
    with _served(database=_OrgStateDatabase(org_state=org_state)) as (client, service):
        response = client.post(path, json=payload, headers=_headers("inactive-org"))

    assert response.status_code == 404
    assert response.json()["code"] == "RESOURCE_NOT_FOUND"
    assert service.calls == []


@pytest.mark.parametrize(
    ("path", "payload"),
    [(INVITE_PATH, {"email": EMAIL_SENTINEL}), (RESEND_PATH, None)],
)
@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Idempotency-Key": ""},
        {"Idempotency-Key": "   "},
        {"Idempotency-Key": "bad key with spaces"},
        {"Idempotency-Key": "k" * 129},
    ],
)
def test_invalid_idempotency_key_headers_are_rejected_with_400(
    path: str, payload: dict[str, str] | None, headers: dict[str, str]
) -> None:
    """covers: D_T-6A_PROMPT.md §3"""
    with _served() as (client, service):
        response = client.post(path, json=payload, headers=headers)

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"
    assert service.calls == []
