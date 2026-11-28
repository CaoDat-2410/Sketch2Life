"""T-8b HTTP contract checks with an in-memory command-service double (no database)."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.push_endpoints import PushEndpointStoreUnavailable
from sketch2life.application.services.push_endpoints import (
    PushEndpointError,
    PushEndpointRegistration,
    PushEndpointResult,
)
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from sketch2life.interfaces.http.openapi_contract import (
    IDEMPOTENCY_MISMATCH_OPERATION_KEYS,
    MOUNTED_OPERATIONS,
)
from sketch2life.interfaces.http.openapi_srs_v22 import SRS_V22_INCLUDED_OPERATIONS
from sketch2life.interfaces.http.routers.notifications import get_push_endpoint_service

DATABASE_SENTINEL = "postgresql+psycopg://sentinel_user:sentinel_pw@localhost:9/sentinel_db"
ENDPOINT_ID = "11111111-1111-4111-8111-111111111111"
FOREIGN_ID = "22222222-2222-4222-8222-222222222222"
PUSH_PATH = "/v1/notifications/push-endpoints"
DELETE_PATH = f"{PUSH_PATH}/{{endpoint_id}}"


class FakePushEndpointService:
    def __init__(self) -> None:
        self.identities = {
            "parent": ("parent", "active"),
            "other-parent": ("parent", "active"),
            "teacher": ("teacher", "active"),
            "disabled": ("parent", "disabled"),
        }
        self.calls: list[tuple[str, object]] = []
        self.by_key: dict[tuple[str, str], tuple[PushEndpointRegistration, PushEndpointResult]] = {}
        self.owner_by_endpoint: dict[str, str] = {}
        self.revocations: dict[tuple[str, str], tuple[str, int]] = {}
        self.store_unavailable = False

    def authorize_parent(self, principal: VerifiedPrincipal) -> None:
        identity = self.identities.get(principal.subject)
        if identity is None or identity != ("parent", "active") or principal.issuer != "issuer":
            raise PushEndpointError(404, "RESOURCE_NOT_FOUND")

    def register(
        self,
        *,
        principal: VerifiedPrincipal,
        command: PushEndpointRegistration,
        idempotency_key: str,
    ) -> PushEndpointResult:
        self.calls.append(("register", command))
        self.authorize_parent(principal)
        if self.store_unavailable:
            raise PushEndpointStoreUnavailable()
        if command.platform_kind == "ANDROID":
            raise PushEndpointError(422, "PUSH_PLATFORM_UNSUPPORTED")
        if command.encrypted_registration_proof.startswith("bad:"):
            raise PushEndpointError(400, "INVALID_REQUEST")
        scope_key = (principal.subject, idempotency_key)
        previous = self.by_key.get(scope_key)
        if previous is not None:
            if previous[0] != command:
                raise PushEndpointError(400, "INVALID_IDEMPOTENCY_KEY")
            return previous[1]
        result = PushEndpointResult(ENDPOINT_ID, 1)
        self.by_key[scope_key] = (command, result)
        self.owner_by_endpoint[ENDPOINT_ID] = principal.subject
        return result

    def revoke(
        self,
        *,
        principal: VerifiedPrincipal,
        endpoint_id: str,
        expected_version: int,
        idempotency_key: str,
    ) -> None:
        self.calls.append(("revoke", endpoint_id))
        self.authorize_parent(principal)
        if self.owner_by_endpoint.get(endpoint_id) != principal.subject:
            raise PushEndpointError(404, "RESOURCE_NOT_FOUND")
        receipt_key = (principal.subject, idempotency_key)
        previous = self.revocations.get(receipt_key)
        if previous is not None:
            if previous != (endpoint_id, expected_version):
                raise PushEndpointError(400, "INVALID_IDEMPOTENCY_KEY")
            return
        if expected_version != 1:
            raise PushEndpointError(409, "STALE_REVISION", current_version=1)
        self.revocations[receipt_key] = (endpoint_id, expected_version)


@pytest.fixture(autouse=True)
def _environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", DATABASE_SENTINEL)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    try:
        yield
    finally:
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


@pytest.fixture
def served() -> Iterator[tuple[TestClient, FakePushEndpointService]]:
    app = create_app()
    service = FakePushEndpointService()

    async def verified(request: Request) -> VerifiedPrincipal:
        return VerifiedPrincipal(
            subject=request.headers.get("X-Test-Principal", "parent"),
            issuer="issuer",
            roles=frozenset(),
        )

    app.dependency_overrides[get_verified_adult] = verified
    app.dependency_overrides[get_push_endpoint_service] = lambda: service
    with TestClient(app) as client:
        yield client, service


def body(**changes: Any) -> dict[str, Any]:
    value: dict[str, Any] = {
        "contract": "PushEndpointRegistrationV1",
        "platform_kind": "WEB",
        "provider_kind": "WEB_PUSH",
        "encrypted_registration_proof": "synthetic:proof-1",
        "app_version": "1.2.3",
    }
    value.update(changes)
    return value


def idempotency(key: str | bytes | None = "key") -> dict[str, str | bytes]:
    return {} if key is None else {"Idempotency-Key": key}


def test_push_catalog_register_and_delete_strict_schemas(served) -> None:
    app = create_app()
    spec = app.openapi()
    assert ("post", PUSH_PATH) in MOUNTED_OPERATIONS
    assert ("delete", DELETE_PATH) in MOUNTED_OPERATIONS
    assert {("post", PUSH_PATH), ("delete", DELETE_PATH)} <= SRS_V22_INCLUDED_OPERATIONS
    assert {("post", PUSH_PATH), ("delete", DELETE_PATH)} <= set(
        IDEMPOTENCY_MISMATCH_OPERATION_KEYS
    )
    assert PUSH_PATH in spec["paths"] and DELETE_PATH in spec["paths"]
    request_schema = spec["components"]["schemas"]["PushEndpointRegistrationV1"]
    assert request_schema["additionalProperties"] is False
    assert set(request_schema["properties"]) == {
        "contract", "platform_kind", "provider_kind", "encrypted_registration_proof", "app_version"
    }
    result_schema = spec["components"]["schemas"]["PushEndpointV1"]
    assert result_schema["additionalProperties"] is False
    assert set(result_schema["properties"]) == {"contract", "endpoint_id", "version"}


def test_register_201_and_replay_etag(served) -> None:
    client, service = served
    headers = idempotency("register-1")
    first = client.post(PUSH_PATH, json=body(), headers=headers)
    replay = client.post(PUSH_PATH, json=body(), headers=headers)
    assert first.status_code == replay.status_code == 201
    assert first.json() == replay.json() == {
        "contract": "PushEndpointV1", "endpoint_id": ENDPOINT_ID, "version": 1
    }
    assert first.headers["ETag"] == replay.headers["ETag"] == '"1"'
    assert first.headers["Cache-Control"] == replay.headers["Cache-Control"] == "no-store"
    assert len([call for call in service.calls if call[0] == "register"]) == 2


def test_revoke_204_empty_and_replay(served) -> None:
    client, service = served
    registered = client.post(PUSH_PATH, json=body(), headers=idempotency("register"))
    assert registered.status_code == 201
    headers = {**idempotency("revoke-1"), "If-Match": '"1"'}
    first = client.delete(f"{PUSH_PATH}/{ENDPOINT_ID}", headers=headers)
    replay = client.delete(f"{PUSH_PATH}/{ENDPOINT_ID}", headers=headers)
    assert first.status_code == replay.status_code == 204
    assert first.content == replay.content == b""
    assert first.headers["Cache-Control"] == "no-store"
    assert len([call for call in service.calls if call[0] == "revoke"]) == 2


def test_revoke_stale_409(served) -> None:
    client, _service = served
    registered = client.post(PUSH_PATH, json=body(), headers=idempotency("stale-register"))
    assert registered.status_code == 201
    response = client.delete(
        f"{PUSH_PATH}/{ENDPOINT_ID}",
        headers={**idempotency("stale-revoke"), "If-Match": '"2"'},
    )
    assert response.status_code == 409
    assert response.json()["code"] == "STALE_REVISION"
    assert response.json()["current_version"] == 1


def test_missing_or_invalid_key_and_if_match_400(served) -> None:
    client, _service = served
    assert client.post(PUSH_PATH, json=body()).status_code == 400
    for key in ("", "has space", "x" * 129, "é".encode()):
        response = client.post(PUSH_PATH, json=body(), headers=idempotency(key))
        assert response.status_code == 400
        assert response.json()["code"] == "INVALID_REQUEST"
    for etag in (None, "W/\"1\"", "1", '"0"', '"1", "2"'):
        headers = idempotency("delete-" + str(etag))
        if etag is not None:
            headers["If-Match"] = etag
        response = client.delete(f"{PUSH_PATH}/{ENDPOINT_ID}", headers=headers)
        assert response.status_code == 400
        assert response.json()["code"] == "INVALID_REQUEST"
    for key in ("a", "k" * 128):
        response = client.post(PUSH_PATH, json=body(), headers=idempotency(key))
        assert response.status_code == 201


def test_bad_proof_400_without_echo(served) -> None:
    client, _service = served
    proof = "bad:synthetic-secret-value"
    response = client.post(
        PUSH_PATH,
        json=body(encrypted_registration_proof=proof),
        headers=idempotency("bad-proof"),
    )
    assert response.status_code == 400
    assert proof not in response.text
    assert response.json()["code"] == "INVALID_REQUEST"


def test_android_unsupported_no_persist(served) -> None:
    client, service = served
    response = client.post(
        PUSH_PATH,
        json=body(platform_kind="ANDROID", provider_kind="ANDROID_PUSH"),
        headers=idempotency("android"),
    )
    assert response.status_code == 422
    assert response.json()["code"] == "PUSH_PLATFORM_UNSUPPORTED"
    assert service.by_key == {}


def test_dependency_unavailable_uses_provider_unavailable_wire_code(served) -> None:
    client, service = served
    service.store_unavailable = True
    response = client.post(PUSH_PATH, json=body(), headers=idempotency("store-down"))
    assert response.status_code == 503
    assert response.json()["code"] == "PROVIDER_UNAVAILABLE"
    assert response.json()["retryable"] is True


def test_wrong_role_unknown_and_foreign_endpoint_same_404(served) -> None:
    client, _service = served
    response = client.post(PUSH_PATH, json=body(), headers=idempotency("register"))
    assert response.status_code == 201
    foreign = client.delete(
        f"{PUSH_PATH}/{ENDPOINT_ID}",
        headers={**idempotency("foreign"), "If-Match": '"1"', "X-Test-Principal": "other-parent"},
    )
    unknown = client.delete(
        f"{PUSH_PATH}/{FOREIGN_ID}",
        headers={**idempotency("unknown"), "If-Match": '"1"'},
    )
    wrong_role = client.post(
        PUSH_PATH,
        json=body(),
        headers={**idempotency("wrong-role"), "X-Test-Principal": "teacher"},
    )
    assert (foreign.status_code, unknown.status_code, wrong_role.status_code) == (404, 404, 404)
    assert {
        (r.json()["code"], r.json()["message"])
        for r in (foreign, unknown, wrong_role)
    } == {("RESOURCE_NOT_FOUND", foreign.json()["message"])}


def test_changed_payload_under_same_key_is_400(served) -> None:
    client, _service = served
    assert client.post(PUSH_PATH, json=body(), headers=idempotency("same")).status_code == 201
    changed = client.post(
        PUSH_PATH,
        json=body(app_version="1.2.4"),
        headers=idempotency("same"),
    )
    assert changed.status_code == 400
    assert changed.json()["code"] == "INVALID_IDEMPOTENCY_KEY"


def test_no_push_list_or_delivery_route(served) -> None:
    _client, _service = served
    paths = create_app().openapi()["paths"]
    assert set(paths[PUSH_PATH]) == {"post"}
    assert set(paths[DELETE_PATH]) == {"delete"}
    assert not any("delivery" in path or "send" in path.removesuffix("/resend") for path in paths)


def test_existing_inbox_routes_unchanged(served) -> None:
    paths = create_app().openapi()["paths"]
    assert "get" in paths["/v1/notifications"]
    assert "post" in paths["/v1/notifications/read-all"]
    assert "post" in paths["/v1/notifications/{inbox_item_id}/read"]



def test_default_wiring_fails_closed_with_503_and_no_receipt() -> None:
    from sketch2life.application.services.push_endpoints import PushEndpointCommandService

    class Store:
        def __init__(self) -> None:
            self.receipts_added = 0

        def authorize_parent(self, principal: VerifiedPrincipal) -> str:
            return "acct"

        def rollback(self) -> None:
            return None

        def get_receipt(self, **_kw: object) -> None:
            return None

        def add_receipt(self, **_kw: object) -> None:
            self.receipts_added += 1

    store = Store()
    app = create_app()

    async def verified(request: Request) -> VerifiedPrincipal:
        return VerifiedPrincipal(subject="parent", issuer="issuer", roles=frozenset())

    app.dependency_overrides[get_verified_adult] = verified
    # No proof verifier, encryptor or key adapters: the production default.
    app.dependency_overrides[get_push_endpoint_service] = lambda: PushEndpointCommandService(
        store=store  # type: ignore[arg-type]
    )
    with TestClient(app) as client:
        response = client.post(
            PUSH_PATH,
            headers={"Authorization": "Bearer x", "Idempotency-Key": "key-1"},
            json={
                "contract": "PushEndpointRegistrationV1",
                "platform_kind": "WEB",
                "provider_kind": "WEB_PUSH",
                "encrypted_registration_proof": "proof-value",
                "app_version": None,
            },
        )
    assert response.status_code == 503
    assert response.json()["code"] == "PUSH_REGISTRATION_UNAVAILABLE"
    assert "proof-value" not in response.text
    assert store.receipts_added == 0
