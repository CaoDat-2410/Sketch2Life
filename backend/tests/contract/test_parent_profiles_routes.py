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
from sketch2life.application.ports.parent_profiles import (
    ParentCommandResult,
    ParentProfileListResult,
)
from sketch2life.application.ports.parent_roles import ParentRoleStoreUnavailable
from sketch2life.domain.parent_profiles import ParentProfileError
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
    get_parent_role_reader,
)


class _ResponseLike(Protocol):
    status_code: int

    @property
    def headers(self) -> Any: ...

    @property
    def text(self) -> str: ...

    def json(self) -> dict[str, object]: ...


class _RouteService:
    def __init__(self) -> None:
        self.writes = 0
        self.lookups = 0
        self.list_calls: list[tuple[int, str | None]] = []

    def assert_profile_owned(self, **kwargs: object) -> None:
        self.lookups += 1
        profile_id = kwargs.get("profile_id")
        principal = cast(VerifiedPrincipal, kwargs["principal"])
        if (
            principal.issuer != "issuer-1"
            or str(profile_id)
            in {
                "00000000-0000-0000-0000-000000000000",
                "00000000-0000-0000-0000-000000000001",
            }
        ):
            raise ParentProfileError(404, "PROFILE_NOT_FOUND", "Profile was not found")

    def create_profile(self, **_kwargs: object) -> ParentCommandResult:
        self.writes += 1
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

    def list_profiles(self, **kwargs: object) -> ParentProfileListResult:
        self.list_calls.append(
            (cast(int, kwargs["limit"]), cast(str | None, kwargs["cursor"]))
        )
        return ParentProfileListResult(items=[], next_cursor=None)

    def patch_profile(self, **_kwargs: object) -> ParentCommandResult:
        self.writes += 1
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

    def delete_profile(self, **kwargs: object) -> ParentCommandResult:
        self.writes += 1
        return ParentCommandResult(
            202,
            {
                "profile_id": str(kwargs.get("profile_id")),
                "state": "DELETE_PENDING",
                "request_id": str(kwargs.get("request_id")),
            },
        )


class _FakeRoleReader:
    def __init__(self, *, active: bool = True, unavailable: bool = False) -> None:
        self.active = active
        self.unavailable = unavailable
        self.calls = 0

    def has_active_parent_role(self, *, principal: VerifiedPrincipal) -> bool:
        del principal
        self.calls += 1
        if self.unavailable:
            raise ParentRoleStoreUnavailable
        return self.active


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
    application.dependency_overrides[get_parent_role_reader] = lambda: _FakeRoleReader()
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
    assert response.json()["field_errors"] == [
        {"field": "profile_id", "code": "INVALID_FORMAT"}
    ]


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
    assert response.json()["field_errors"] == [
        {"field": "<unknown>", "code": "UNKNOWN_FIELD"}
    ]
    assert "must-not-echo" not in response.text


def test_collection_role_denial_precedes_malformed_body_and_missing_key(
    parent_client: tuple[TestClient, Be1Runtime],
) -> None:
    client, _runtime = parent_client
    application = cast(FastAPI, client.app)
    service = _RouteService()
    role_reader = _FakeRoleReader(active=False)
    application.dependency_overrides[get_parent_principal] = lambda: VerifiedPrincipal(
        "subject-1", "issuer-1", frozenset()
    )
    application.dependency_overrides[get_parent_profile_service] = lambda: service
    application.dependency_overrides[get_parent_role_reader] = lambda: role_reader

    for method, url in (
        ("POST", "/v1/parent/profiles"),
        ("GET", "/v1/parent/profiles?limit=not-an-integer"),
    ):
        response = client.request(
            method,
            url,
            content="{" if method == "POST" else None,
            headers={"X-Request-ID": f"parent-role-first-{method.lower()}"},
        )
        _assert_parent_error(
            response,
            status=403,
            code="ACTION_NOT_ALLOWED",
            request_id=f"parent-role-first-{method.lower()}",
        )
    assert role_reader.calls == 2
    assert service.writes == 0


def test_targeted_error_precedence_is_uuid_then_scope_then_role_then_body(
    parent_client: tuple[TestClient, Be1Runtime],
) -> None:
    client, _runtime = parent_client
    application = cast(FastAPI, client.app)
    principal = VerifiedPrincipal("subject-1", "issuer-1", frozenset())
    service = _RouteService()
    role_reader = _FakeRoleReader(active=False)
    application.dependency_overrides[get_parent_principal] = lambda: principal
    application.dependency_overrides[get_parent_profile_service] = lambda: service
    application.dependency_overrides[get_parent_role_reader] = lambda: role_reader

    for method in ("GET", "PATCH", "DELETE"):
        invalid_uuid = client.request(
            method,
            "/v1/parent/profiles/not-a-uuid",
            content="{" if method == "PATCH" else None,
            headers={"X-Request-ID": f"parent-path-before-role-{method.lower()}"},
        )
        _assert_parent_error(
            invalid_uuid,
            status=400,
            code="INVALID_REQUEST",
            request_id=f"parent-path-before-role-{method.lower()}",
        )
    assert role_reader.calls == 0
    assert service.lookups == 0

    for method in ("GET", "PATCH", "DELETE"):
        for label, target_id in (
            ("missing", "00000000-0000-0000-0000-000000000000"),
            ("foreign", "00000000-0000-0000-0000-000000000001"),
        ):
            non_owned_profile = client.request(
                method,
                f"/v1/parent/profiles/{target_id}",
                content="{" if method == "PATCH" else None,
                headers={
                    "X-Request-ID": f"parent-scope-before-role-{label}-{method.lower()}"
                },
            )
            _assert_parent_error(
                non_owned_profile,
                status=404,
                code="PROFILE_NOT_FOUND",
                request_id=f"parent-scope-before-role-{label}-{method.lower()}",
            )
    assert role_reader.calls == 0
    assert service.lookups == 6

    application.dependency_overrides[get_parent_principal] = lambda: VerifiedPrincipal(
        "subject-1", "issuer-2", frozenset()
    )
    for method in ("GET", "PATCH", "DELETE"):
        wrong_issuer = client.request(
            method,
            "/v1/parent/profiles/a3a878cf-7b93-4f25-a71d-6a3b09351a11",
            content="{" if method == "PATCH" else None,
            headers={"X-Request-ID": f"parent-scope-wrong-issuer-{method.lower()}"},
        )
        _assert_parent_error(
            wrong_issuer,
            status=404,
            code="PROFILE_NOT_FOUND",
            request_id=f"parent-scope-wrong-issuer-{method.lower()}",
        )
    assert role_reader.calls == 0
    assert service.lookups == 9

    application.dependency_overrides[get_parent_principal] = lambda: principal

    for method in ("GET", "PATCH", "DELETE"):
        denied_owner = client.request(
            method,
            "/v1/parent/profiles/a3a878cf-7b93-4f25-a71d-6a3b09351a11",
            content="{" if method == "PATCH" else None,
            headers={"X-Request-ID": f"parent-role-before-body-{method.lower()}"},
        )
        _assert_parent_error(
            denied_owner,
            status=403,
            code="ACTION_NOT_ALLOWED",
            request_id=f"parent-role-before-body-{method.lower()}",
        )
    assert role_reader.calls == 3
    assert service.writes == 0


def test_parent_role_adapter_failure_is_503_without_writes(
    parent_client: tuple[TestClient, Be1Runtime],
) -> None:
    client, _runtime = parent_client
    application = cast(FastAPI, client.app)
    service = _RouteService()
    role_reader = _FakeRoleReader(unavailable=True)
    application.dependency_overrides[get_parent_principal] = lambda: VerifiedPrincipal(
        "subject-1", "issuer-1", frozenset()
    )
    application.dependency_overrides[get_parent_profile_service] = lambda: service
    application.dependency_overrides[get_parent_role_reader] = lambda: role_reader

    response = client.post(
        "/v1/parent/profiles",
        headers={
            "Idempotency-Key": "role-store-failure",
            "X-Request-ID": "parent-role-store-failure",
        },
        json={"display_name": "Mina", "age_months": 72},
    )

    _assert_parent_error(
        response,
        status=503,
        code="PARENT_STORE_UNAVAILABLE",
        request_id="parent-role-store-failure",
    )
    assert role_reader.calls == 1
    assert service.writes == 0


def test_parent_list_and_delete_routes_expose_the_approved_shapes(
    parent_client: tuple[TestClient, Be1Runtime],
) -> None:
    client, _runtime = parent_client
    application = cast(FastAPI, client.app)
    service = _RouteService()
    application.dependency_overrides[get_parent_principal] = lambda: VerifiedPrincipal(
        "subject-1", "issuer-1", frozenset()
    )
    application.dependency_overrides[get_parent_profile_service] = lambda: service
    application.dependency_overrides[get_parent_role_reader] = lambda: _FakeRoleReader()

    listed = client.get("/v1/parent/profiles?limit=25", headers={"X-Request-ID": "parent-list"})
    assert listed.status_code == 200
    assert listed.json() == {"items": [], "next_cursor": None, "request_id": "parent-list"}
    assert service.list_calls[-1] == (25, None)

    default_limit = client.get("/v1/parent/profiles")
    assert default_limit.status_code == 200
    assert service.list_calls[-1] == (25, None)
    maximum_limit = client.get("/v1/parent/profiles?limit=100")
    assert maximum_limit.status_code == 200
    assert service.list_calls[-1] == (100, None)
    too_large = client.get("/v1/parent/profiles?limit=101")
    _assert_parent_error(
        too_large,
        status=400,
        code="INVALID_REQUEST",
        request_id=too_large.headers["X-Request-ID"],
    )
    assert too_large.json()["field_errors"] == [
        {"field": "limit", "code": "OUT_OF_RANGE"}
    ]
    assert service.list_calls[-1] == (100, None)
    unknown_query = client.get("/v1/parent/profiles?unexpected=value")
    assert unknown_query.status_code == 400
    assert unknown_query.json()["field_errors"] == [
        {"field": "<unknown>", "code": "UNKNOWN_FIELD"}
    ]
    assert "unexpected" not in unknown_query.text

    deleted = client.delete(
        "/v1/parent/profiles/a3a878cf-7b93-4f25-a71d-6a3b09351a11",
        headers={"Idempotency-Key": "delete-1", "X-Request-ID": "parent-delete"},
    )
    assert deleted.status_code == 202
    assert deleted.json() == {
        "profile_id": "a3a878cf-7b93-4f25-a71d-6a3b09351a11",
        "state": "DELETE_PENDING",
        "request_id": "parent-delete",
    }
    assert service.writes == 1


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
    application.dependency_overrides[get_parent_role_reader] = lambda: _FakeRoleReader()
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
    monkeypatch.setattr(verifier_module, "get_firebase_admin_app", lambda *_args: object())

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
    monkeypatch.setattr(verifier_module, "get_firebase_admin_app", lambda *_args: object())

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
