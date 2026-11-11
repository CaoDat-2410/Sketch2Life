"""Parent route contracts and the Parent-only Firebase error classification."""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any, Protocol, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from firebase_admin import auth
from firebase_admin.auth import ExpiredIdTokenError, InvalidIdTokenError

import sketch2life.infrastructure.identity.firebase_token_verifier as verifier_module
import sketch2life.interfaces.http.be1_runtime as runtime_module
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_profiles import ParentCommandResult
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.identity.firebase_token_verifier import (
    FirebaseTokenVerifier,
    IdentityVerificationUnavailable,
)
from sketch2life.interfaces.http.be1_runtime import Be1Runtime
from sketch2life.interfaces.http.parent_runtime import (
    get_parent_principal,
    get_parent_profile_service,
)


class _ResponseLike(Protocol):
    status_code: int

    @property
    def headers(self) -> Any: ...

    @property
    def text(self) -> str: ...

    def json(self) -> dict[str, object]: ...


class _RouteService:
    def create_profile(self, **_kwargs: object) -> ParentCommandResult:
        return ParentCommandResult(
            201,
            {
                "profile_id": "a3a878cf-7b93-4f25-a71d-6a3b09351a11",
                "revision_no": 1,
                "revision_hash": "a" * 64,
            },
        )

    def get_profile(self, **_kwargs: object) -> dict[str, object]:
        return {
            "profile_id": "a3a878cf-7b93-4f25-a71d-6a3b09351a11",
            "revision_no": 1,
            "revision_hash": "a" * 64,
            "display_name": "Mina",
            "age_months": 72,
            "age_band_ref": None,
            "age_band_version": None,
            "interests_summary": None,
            "state": "ACTIVE",
            "data_origin": "SYNTHETIC_DEV",
        }

    def patch_profile(self, **_kwargs: object) -> ParentCommandResult:
        return ParentCommandResult(
            200,
            {
                "profile_id": "a3a878cf-7b93-4f25-a71d-6a3b09351a11",
                "revision_no": 2,
                "revision_hash": "b" * 64,
                "display_name": "Mina",
                "age_months": 72,
                "age_band_ref": None,
                "age_band_version": None,
                "interests_summary": None,
                "state": "ACTIVE",
                "data_origin": "SYNTHETIC_DEV",
            },
        )


class _ReplayedStaleRouteService(_RouteService):
    def patch_profile(self, **_kwargs: object) -> ParentCommandResult:
        return ParentCommandResult(
            409,
            {
                "code": "STALE_REVISION",
                "message": "The profile revision is stale",
                "correlation_id": "parent-stale-first",
                "retryable": False,
                "request_id": "parent-stale-first",
                "current_version": 2,
            },
        )


class _BrokenRouteService(_RouteService):
    def get_profile(self, **_kwargs: object) -> dict[str, object]:
        raise RuntimeError("synthetic internal failure")


@pytest.fixture
def parent_client(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, Be1Runtime]]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    settings = Settings(
        env="test",
        auth_provider="firebase",
        firebase_project_id="synthetic-parent-project",
        _env_file=None,  # type: ignore[call-arg]
    )
    import sketch2life.interfaces.http.app as app_module
    from sketch2life.interfaces.http.app import create_app

    monkeypatch.setattr(app_module, "get_settings", lambda: settings)
    monkeypatch.setattr(
        runtime_module,
        "get_core_database_settings",
        lambda: SimpleNamespace(database_url=None),
    )
    application = create_app()
    runtime = application.state.be1_runtime
    runtime.identity_verifier = FirebaseTokenVerifier(settings)
    application.dependency_overrides[get_parent_profile_service] = _RouteService
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    try:
        with TestClient(application) as client:
            yield client, runtime
    finally:
        application.dependency_overrides.clear()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _assert_parent_error(
    response: _ResponseLike, *, status: int, code: str, request_id: str
) -> None:
    assert response.status_code == status
    body = response.json()
    assert body["code"] == code
    assert body["request_id"] == request_id
    assert body["correlation_id"] == request_id
    assert response.headers["X-Request-ID"] == request_id


def test_parent_routes_return_contract_shapes(
    parent_client: tuple[TestClient, Be1Runtime],
) -> None:
    client, _runtime = parent_client
    headers = {"Authorization": "Bearer synthetic-token", "X-Request-ID": "parent-route-1"}
    cast(FastAPI, client.app).dependency_overrides[get_parent_principal] = (
        lambda: VerifiedPrincipal("subject-1", "issuer-1", frozenset())
    )

    created = client.post(
        "/v1/parent/profiles",
        headers={**headers, "Idempotency-Key": "create-1"},
        json={"display_name": "Mina", "age_months": 72},
    )
    assert created.status_code == 201
    assert created.json()["revision_no"] == 1
    assert created.headers["X-Request-ID"] == "parent-route-1"

    profile_id = "a3a878cf-7b93-4f25-a71d-6a3b09351a11"
    read = client.get(f"/v1/parent/profiles/{profile_id}", headers=headers)
    assert read.status_code == 200
    assert read.json()["data_origin"] == "SYNTHETIC_DEV"

    patched = client.patch(
        f"/v1/parent/profiles/{profile_id}",
        headers={**headers, "Idempotency-Key": "patch-1"},
        json={"expected_revision": 1, "display_name": "Mina", "age_months": 72},
    )
    assert patched.status_code == 200
    patched_body = patched.json()
    assert set(patched_body) == {
        "profile_id",
        "revision_no",
        "revision_hash",
        "display_name",
        "age_months",
        "age_band_ref",
        "age_band_version",
        "interests_summary",
        "state",
        "data_origin",
    }
    assert patched_body == {
        "profile_id": profile_id,
        "revision_no": 2,
        "revision_hash": "b" * 64,
        "display_name": "Mina",
        "age_months": 72,
        "age_band_ref": None,
        "age_band_version": None,
        "interests_summary": None,
        "state": "ACTIVE",
        "data_origin": "SYNTHETIC_DEV",
    }


def test_parent_invalid_profile_uuid_is_documented_error_response(
    parent_client: tuple[TestClient, Be1Runtime],
) -> None:
    client, _runtime = parent_client
    cast(FastAPI, client.app).dependency_overrides[get_parent_principal] = (
        lambda: VerifiedPrincipal("subject-1", "issuer-1", frozenset())
    )
    response = client.get(
        "/v1/parent/profiles/not-a-uuid",
        headers={"X-Request-ID": "parent-invalid-profile-id"},
    )

    _assert_parent_error(
        response,
        status=400,
        code="INVALID_REQUEST",
        request_id="parent-invalid-profile-id",
    )


def test_replayed_error_response_header_uses_stored_request_id(
    parent_client: tuple[TestClient, Be1Runtime],
) -> None:
    client, _runtime = parent_client
    application = cast(FastAPI, client.app)
    application.dependency_overrides[get_parent_principal] = (
        lambda: VerifiedPrincipal("subject-1", "issuer-1", frozenset())
    )
    application.dependency_overrides[get_parent_profile_service] = (
        _ReplayedStaleRouteService
    )
    response = client.patch(
        "/v1/parent/profiles/a3a878cf-7b93-4f25-a71d-6a3b09351a11",
        headers={
            "Authorization": "Bearer synthetic-token",
            "Idempotency-Key": "stale-replay-key",
            "X-Request-ID": "parent-stale-retry",
        },
        json={"expected_revision": 1, "display_name": "Mina", "age_months": 72},
    )

    _assert_parent_error(
        response,
        status=409,
        code="STALE_REVISION",
        request_id="parent-stale-first",
    )


def test_parent_validation_uses_safe_request_id_envelope(
    parent_client: tuple[TestClient, Be1Runtime],
) -> None:
    client, _runtime = parent_client
    cast(FastAPI, client.app).dependency_overrides[get_parent_principal] = (
        lambda: VerifiedPrincipal("subject-1", "issuer-1", frozenset())
    )
    response = client.post(
        "/v1/parent/profiles",
        headers={
            "Authorization": "Bearer synthetic-token",
            "Idempotency-Key": "create-1",
            "X-Request-ID": "parent-invalid-1",
        },
        json={"display_name": "Mina", "age_months": 72, "secret_field": "must-not-echo"},
    )

    _assert_parent_error(
        response,
        status=400,
        code="INVALID_REQUEST",
        request_id="parent-invalid-1",
    )
    assert "must-not-echo" not in response.text


def test_parent_unhandled_errors_keep_the_safe_error_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    settings = Settings(
        env="test",
        auth_provider="firebase",
        firebase_project_id="synthetic-parent-project",
        _env_file=None,  # type: ignore[call-arg]
    )
    import sketch2life.interfaces.http.app as app_module
    from sketch2life.interfaces.http.app import create_app

    monkeypatch.setattr(app_module, "get_settings", lambda: settings)
    monkeypatch.setattr(
        runtime_module,
        "get_core_database_settings",
        lambda: SimpleNamespace(database_url=None),
    )
    application = create_app()
    application.dependency_overrides[get_parent_principal] = lambda: VerifiedPrincipal(
        "subject-1", "issuer-1", frozenset()
    )
    application.dependency_overrides[get_parent_profile_service] = _BrokenRouteService
    try:
        with TestClient(application, raise_server_exceptions=False) as client:
            response = client.get(
                "/v1/parent/profiles/a3a878cf-7b93-4f25-a71d-6a3b09351a11",
                headers={"X-Request-ID": "parent-internal-1"},
            )
    finally:
        application.dependency_overrides.clear()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()

    _assert_parent_error(
        response,
        status=500,
        code="INTERNAL_SERVER_ERROR",
        request_id="parent-internal-1",
    )
    assert response.json()["message"] == "The server could not complete the request"
    assert "synthetic internal failure" not in response.text


def test_expired_firebase_sdk_type_is_preserved_and_maps_to_token_expired(
    parent_client: tuple[TestClient, Be1Runtime], monkeypatch: pytest.MonkeyPatch
) -> None:
    client, runtime = parent_client
    monkeypatch.setattr(verifier_module, "_firebase_app", lambda *_args: object())

    def raise_expired(*_args: object, **_kwargs: object) -> None:
        raise ExpiredIdTokenError("synthetic expiry fixture", None)  # type: ignore[no-untyped-call]

    monkeypatch.setattr(auth, "verify_id_token", raise_expired)
    with pytest.raises(IdentityVerificationUnavailable) as rejected:
        asyncio.run(runtime.identity_verifier.verify("synthetic-token"))
    assert isinstance(rejected.value.__cause__, ExpiredIdTokenError)

    response = client.get(
        "/v1/parent/profiles/a3a878cf-7b93-4f25-a71d-6a3b09351a11",
        headers={"Authorization": "Bearer synthetic-token", "X-Request-ID": "parent-expired-1"},
    )
    _assert_parent_error(
        response,
        status=401,
        code="TOKEN_EXPIRED",
        request_id="parent-expired-1",
    )


def test_invalid_firebase_token_maps_separately_from_expired(
    parent_client: tuple[TestClient, Be1Runtime], monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _runtime = parent_client
    monkeypatch.setattr(verifier_module, "_firebase_app", lambda *_args: object())

    def raise_invalid(*_args: object, **_kwargs: object) -> None:
        raise InvalidIdTokenError("synthetic invalid fixture", None)  # type: ignore[no-untyped-call]

    monkeypatch.setattr(auth, "verify_id_token", raise_invalid)
    response = client.get(
        "/v1/parent/profiles/a3a878cf-7b93-4f25-a71d-6a3b09351a11",
        headers={
            "Authorization": "Bearer synthetic-token",
            "X-Request-ID": "parent-invalid-token-1",
        },
    )
    _assert_parent_error(
        response,
        status=401,
        code="INVALID_TOKEN",
        request_id="parent-invalid-token-1",
    )


def test_missing_bearer_and_verifier_unavailability_are_distinct(
    parent_client: tuple[TestClient, Be1Runtime], monkeypatch: pytest.MonkeyPatch
) -> None:
    client, runtime = parent_client
    missing = client.get(
        "/v1/parent/profiles/a3a878cf-7b93-4f25-a71d-6a3b09351a11",
        headers={"X-Request-ID": "parent-missing-bearer-1"},
    )
    _assert_parent_error(
        missing,
        status=401,
        code="AUTH_REQUIRED",
        request_id="parent-missing-bearer-1",
    )

    async def unavailable(_token: str) -> VerifiedPrincipal:
        cause = ImportError("synthetic SDK unavailable fixture")
        raise IdentityVerificationUnavailable("verifier unavailable") from cause

    monkeypatch.setattr(runtime.identity_verifier, "verify", unavailable)
    response = client.get(
        "/v1/parent/profiles/a3a878cf-7b93-4f25-a71d-6a3b09351a11",
        headers={"Authorization": "Bearer synthetic-token", "X-Request-ID": "parent-unavailable-1"},
    )
    _assert_parent_error(
        response,
        status=503,
        code="IDENTITY_PROVIDER_UNAVAILABLE",
        request_id="parent-unavailable-1",
    )
