"""HTTP contract for the Parent consent-policy read route (T-CONSENT1)."""

from __future__ import annotations

from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient

import sketch2life.interfaces.http.app as app_module
import sketch2life.interfaces.http.be1_runtime as runtime_module
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_roles import ParentRoleStoreUnavailable
from sketch2life.domain.parent_consent_policy import CURRENT_PARENT_CONSENT_POLICY
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.interfaces.http.be1_runtime import get_runtime, get_verified_adult
from sketch2life.interfaces.http.openapi_srs_v22 import (
    SRS_V22_INCLUDED_OPERATIONS,
    project_srs_v22_openapi,
)
from sketch2life.interfaces.http.routers.parent_consent_policy import get_consent_role_reader

PATH = "/v1/parent/consent-policy"
ISSUER = "synthetic-consent-issuer"
VALID_AUTHORIZATION = "Bearer synthetic-consent-token"
ERROR_FIELDS = {
    "code",
    "message",
    "correlation_id",
    "retryable",
    "retry_after_seconds",
    "field_errors",
    "request_id",
}
_IDENTITIES = {
    "parent": (ISSUER, "active", "parent"),
    "teacher": (ISSUER, "active", "teacher"),
    "inactive": (ISSUER, "disabled", "parent"),
    "issuer-mismatch": (ISSUER, "active", "parent"),
}


class _RoleReader:
    def __init__(self, state: dict[str, bool]) -> None:
        self._state = state

    def has_active_parent_role(self, *, principal: VerifiedPrincipal) -> bool:
        if self._state["store_unavailable"]:
            raise ParentRoleStoreUnavailable
        identity = _IDENTITIES.get(principal.subject)
        return identity == (principal.issuer, "active", "parent")


@pytest.fixture
def consent_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, FastAPI, dict[str, bool]]]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    settings = Settings(
        env="test",
        auth_provider="firebase",
        firebase_project_id="synthetic-consent-project",
        _env_file=None,  # type: ignore[call-arg]
    )
    monkeypatch.setattr(app_module, "get_settings", lambda: settings)
    monkeypatch.setattr(
        runtime_module,
        "get_core_database_settings",
        lambda: SimpleNamespace(database_url=None),
    )
    application = app_module.create_app()
    state = {"store_unavailable": False}

    async def verified_adult(request: Request) -> VerifiedPrincipal:
        authorization = request.headers.get("Authorization")
        if authorization is None:
            raise HTTPException(
                status_code=401,
                detail={"code": "AUTHENTICATION_REQUIRED"},
            )
        if authorization == "Bearer provider-down":
            raise HTTPException(
                status_code=503,
                detail={"code": "IDENTITY_PROVIDER_UNAVAILABLE"},
            )
        if authorization != VALID_AUTHORIZATION:
            raise HTTPException(
                status_code=401,
                detail={"code": "INVALID_IDENTITY_TOKEN"},
            )
        subject = request.headers.get("X-Test-Principal", "parent")
        issuer = request.headers.get("X-Test-Issuer", ISSUER)
        return VerifiedPrincipal(subject=subject, issuer=issuer, roles=frozenset())

    def runtime() -> Any:
        return SimpleNamespace(session_factory=None, database_error=None)

    application.dependency_overrides[get_verified_adult] = verified_adult
    application.dependency_overrides[get_runtime] = runtime
    application.dependency_overrides[get_consent_role_reader] = lambda: _RoleReader(state)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()

    try:
        with TestClient(application) as client:
            yield client, application, state
    finally:
        application.dependency_overrides.clear()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _headers(**values: str) -> dict[str, str]:
    return {
        "Authorization": VALID_AUTHORIZATION,
        "X-Request-ID": "consent-test-request",
        **values,
    }


def _assert_error(
    response: Any, *, status: int, code: str, retryable: bool
) -> dict[str, Any]:
    assert response.status_code == status
    body = response.json()
    assert set(body) == ERROR_FIELDS
    assert body["code"] == code
    assert body["retryable"] is retryable
    assert body["request_id"] == response.headers["X-Request-ID"]
    assert body["correlation_id"] == body["request_id"]
    return body


def test_active_parent_reads_placeholder_with_client_fields_and_private_headers(
    consent_client: tuple[TestClient, FastAPI, dict[str, bool]],
    caplog: pytest.LogCaptureFixture,
) -> None:
    client, _application, _state = consent_client
    response = client.get(f"{PATH}?ignored=anything", headers=_headers())

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"contract", "request_id", "policy"}
    assert body["contract"] == "ParentConsentPolicyV1"
    assert body["request_id"] == response.headers["X-Request-ID"]
    policy = body["policy"]
    assert set(policy) == {
        "purpose_code",
        "policy_version",
        "consent_text",
        "consent_text_sha256",
        "policy_state",
        "data_origin_scope",
        "effective_from",
        "purposes",
        "links",
        "acceptance_recording",
    }
    assert all(
        isinstance(policy[key], str) and policy[key]
        for key in (
            "purpose_code",
            "policy_version",
            "consent_text",
            "consent_text_sha256",
        )
    )
    assert policy["consent_text"] == CURRENT_PARENT_CONSENT_POLICY.consent_text
    assert policy["consent_text_sha256"] == CURRENT_PARENT_CONSENT_POLICY.consent_text_sha256
    assert policy["policy_version"] == "parent-consent-placeholder-v0"
    assert policy["policy_state"] == "PLACEHOLDER_NOT_APPROVED"
    assert policy["effective_from"] is None
    assert policy["purposes"] == [
        {
            "purpose_code": "SYNTHETIC_TEST_ONLY",
            "text_key": "parent.consent.placeholder.synthetic_test_only",
        }
    ]
    assert policy["links"] == []
    assert policy["acceptance_recording"] == "NOT_AVAILABLE"
    assert response.headers["Cache-Control"] == "private, no-cache"
    assert response.headers["Vary"] == "Authorization"
    assert CURRENT_PARENT_CONSENT_POLICY.consent_text not in caplog.text


@pytest.mark.parametrize(
    ("headers", "status", "code"),
    [
        ({"X-Request-ID": "missing-token"}, 401, "AUTH_REQUIRED"),
        ({"Authorization": "Bearer invalid", "X-Request-ID": "bad-token"}, 401, "INVALID_TOKEN"),
    ],
)
def test_authentication_errors_use_conv1_envelope(
    consent_client: tuple[TestClient, FastAPI, dict[str, bool]],
    headers: dict[str, str],
    status: int,
    code: str,
) -> None:
    client, _application, _state = consent_client

    response = client.get(PATH, headers=headers)

    _assert_error(response, status=status, code=code, retryable=False)


@pytest.mark.parametrize(
    ("subject", "issuer"),
    [
        ("teacher", ISSUER),
        ("inactive", ISSUER),
        ("issuer-mismatch", "synthetic-other-issuer"),
    ],
)
def test_non_parent_callers_are_forbidden(
    consent_client: tuple[TestClient, FastAPI, dict[str, bool]],
    subject: str,
    issuer: str,
) -> None:
    client, _application, _state = consent_client

    response = client.get(
        PATH,
        headers=_headers(**{"X-Test-Principal": subject, "X-Test-Issuer": issuer}),
    )

    _assert_error(response, status=403, code="ACTION_NOT_ALLOWED", retryable=False)


def test_parent_role_store_failure_is_retryable_database_error(
    consent_client: tuple[TestClient, FastAPI, dict[str, bool]],
) -> None:
    client, _application, state = consent_client
    state["store_unavailable"] = True

    response = client.get(PATH, headers=_headers())

    _assert_error(response, status=503, code="DATABASE_UNAVAILABLE", retryable=True)


def test_runtime_dependency_failure_is_a_retryable_conv1_error(
    consent_client: tuple[TestClient, FastAPI, dict[str, bool]],
) -> None:
    client, application, _state = consent_client
    application.dependency_overrides.pop(get_consent_role_reader)

    def unavailable_runtime() -> Any:
        raise HTTPException(status_code=503, detail={"code": "BE1_RUNTIME_UNAVAILABLE"})

    application.dependency_overrides[get_runtime] = unavailable_runtime
    response = client.get(PATH, headers=_headers())

    _assert_error(response, status=503, code="BE1_RUNTIME_UNAVAILABLE", retryable=True)


def test_identity_provider_failure_is_a_retryable_conv1_error(
    consent_client: tuple[TestClient, FastAPI, dict[str, bool]],
) -> None:
    client, _application, _state = consent_client

    response = client.get(
        PATH,
        headers={"Authorization": "Bearer provider-down", "X-Request-ID": "provider-down"},
    )

    _assert_error(response, status=503, code="IDENTITY_PROVIDER_UNAVAILABLE", retryable=True)


def test_post_is_rejected_with_action_not_allowed(
    consent_client: tuple[TestClient, FastAPI, dict[str, bool]],
) -> None:
    client, _application, _state = consent_client

    response = client.post(PATH, headers=_headers())

    _assert_error(response, status=405, code="ACTION_NOT_ALLOWED", retryable=False)


def test_runtime_and_srs_v22_openapi_publish_the_read_without_422(
    consent_client: tuple[TestClient, FastAPI, dict[str, bool]],
) -> None:
    _client, application, _state = consent_client
    runtime_spec = application.openapi()
    runtime_operation = runtime_spec["paths"][PATH]["get"]

    assert runtime_operation["operationId"] == "parentGetConsentPolicyV1"
    assert "requestBody" not in runtime_operation
    assert "422" not in runtime_operation["responses"]
    projected = project_srs_v22_openapi(runtime_spec)
    assert ("get", PATH) in SRS_V22_INCLUDED_OPERATIONS
    projected_operation = projected["paths"][PATH]["get"]
    assert projected_operation["operationId"] == "parentGetConsentPolicyV1"
    assert projected_operation["tags"] == ["Parent Profiles"]
