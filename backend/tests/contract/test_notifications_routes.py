"""FEAT-066 T-8a: the notification inbox route contract (SRS l.812, l.1681, l.1697).

Offline: no database. The service is replaced by a fake, so the module checks the catalog, the
published OpenAPI, request validation (CONV-1 400 bodies), headers, the error mapping and that no
route accepts a recipient. Behaviour against PostgreSQL lives in
``tests/integration/test_t8a_notifications_postgres.py``.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.contracts.schemas.notifications import (
    NotificationPageV1,
    NotificationReadAllV1,
    NotificationV1,
)
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.notifications.inbox_repository import (
    InboxPage,
    NotificationError,
)
from sketch2life.interfaces.http.api_conventions import encode_cursor
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from sketch2life.interfaces.http.openapi_contract import (
    IDEMPOTENCY_MISMATCH_OPERATION_KEYS,
    MOUNTED_OPERATIONS,
)
from sketch2life.interfaces.http.openapi_srs_v22 import (
    SRS_V22_INCLUDED_OPERATIONS,
    SRS_V22_OPERATION_TAGS,
)
from sketch2life.interfaces.http.routers.notifications import get_notification_service

FLAG = "STORYRUN_LITE_MAIN_DEMO_ENABLED"
ACK = "STORYRUN_LITE_MAIN_DEMO_REPLACES_PARENT_ROUTER"
DATABASE_SENTINEL = "postgresql+psycopg://sentinel_user:sentinel_pw@localhost:9/sentinel_db"
LIST = ("get", "/v1/notifications")
READ_ONE = ("post", "/v1/notifications/{inbox_item_id}/read")
READ_ALL = ("post", "/v1/notifications/read-all")
PUSH_REGISTER = ("post", "/v1/notifications/push-endpoints")
PUSH_REVOKE = ("delete", "/v1/notifications/push-endpoints/{endpoint_id}")
OPERATIONS = (LIST, READ_ONE, READ_ALL, PUSH_REGISTER, PUSH_REVOKE)
NOW = datetime(2026, 11, 21, 7, 0, tzinfo=UTC)
ITEM: dict[str, Any] = {
    "contract": "NotificationV1",
    "inbox_item_id": "item-1",
    "notification_type": "CLASS_ARCHIVED",
    "template_version": 1,
    "safe_parameters": {"count": 3, "class_ref": "cls_1", "urgent": False},
    "created_at": NOW,
    "read_at": None,
    "expires_at": None,
}
HIDDEN_WORDS = (
    "recipient",
    "organization",
    "trigger",
    "dedupe",
    "command_sha256",
    "child_name",
    "email",
    "endpoint",
    "device",
)


@pytest.fixture(autouse=True)
def _environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", DATABASE_SENTINEL)
    monkeypatch.delenv(FLAG, raising=False)
    monkeypatch.delenv(ACK, raising=False)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    try:
        yield
    finally:
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


class FakeService:
    def __init__(self) -> None:
        self.error: Exception | None = None
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.page = InboxPage(
            items=[dict(ITEM)],
            has_more=True,
            unread_count=100,
            last_created_at=NOW,
            last_item_id="item-1",
        )

    def _maybe_fail(self) -> None:
        if self.error is not None:
            raise self.error

    def list_page(self, **kwargs: Any) -> InboxPage:
        self.calls.append(("list", kwargs))
        self._maybe_fail()
        return self.page

    def mark_read(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("read", kwargs))
        self._maybe_fail()
        return {**ITEM, "read_at": NOW + timedelta(minutes=1)}

    def mark_all_read(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("read-all", kwargs))
        self._maybe_fail()
        return {"contract": "NotificationReadAllV1", "marked_count": 4}


@pytest.fixture
def served() -> Iterator[tuple[TestClient, FakeService]]:
    application = create_app()
    service = FakeService()

    async def verified() -> VerifiedPrincipal:
        return VerifiedPrincipal(subject="subject-1", issuer="issuer", roles=frozenset())

    application.dependency_overrides[get_verified_adult] = verified
    application.dependency_overrides[get_notification_service] = lambda: service
    with TestClient(application) as client:
        yield client, service


def headers(key: str | None = "key-1") -> dict[str, str]:
    return {"Idempotency-Key": key} if key is not None else {}


# ----------------------------------------------------------------------------- catalog
def test_the_five_operations_are_catalogued_projected_and_tagged() -> None:
    for key in OPERATIONS:
        assert key in MOUNTED_OPERATIONS
        assert key in SRS_V22_INCLUDED_OPERATIONS
        assert SRS_V22_OPERATION_TAGS[key] == "Notifications"
        assert MOUNTED_OPERATIONS[key]["tag"] == "Notifications"
        assert MOUNTED_OPERATIONS[key]["authentication"] == "HTTPBearer (bearer)"
    assert READ_ONE in IDEMPOTENCY_MISMATCH_OPERATION_KEYS
    assert READ_ALL in IDEMPOTENCY_MISMATCH_OPERATION_KEYS
    assert PUSH_REGISTER in IDEMPOTENCY_MISMATCH_OPERATION_KEYS
    assert PUSH_REVOKE in IDEMPOTENCY_MISMATCH_OPERATION_KEYS
    assert LIST not in IDEMPOTENCY_MISMATCH_OPERATION_KEYS


def test_the_route_table_under_notifications_is_exactly_the_five_t8a_t8b_routes() -> None:
    application = create_app()
    application.openapi()
    runtime_paths = application.state.runtime_openapi_schema["paths"]
    routes = {
        (method.lower(), path)
        for path, item in runtime_paths.items()
        if path.startswith("/v1/notifications")
        for method in item
    }
    assert routes == set(OPERATIONS)


def test_no_push_list_or_delivery_route_is_published() -> None:
    published = create_app().openapi()["paths"]
    assert "/v1/notifications/push-endpoints" in published
    assert "post" in published["/v1/notifications/push-endpoints"]
    assert "get" not in published["/v1/notifications/push-endpoints"]
    assert "/v1/notifications/push-endpoints/{endpoint_id}" in published
    assert "delete" in published["/v1/notifications/push-endpoints/{endpoint_id}"]
    assert not any(
        "delivery" in path or "send" in path.removesuffix("/resend") for path in published
    )


def test_no_route_accepts_a_recipient_or_an_account() -> None:
    application = create_app()
    spec = application.openapi()
    declared: set[str] = set()
    for path, item in spec["paths"].items():
        if not path.startswith("/v1/notifications"):
            continue
        for operation in item.values():
            declared.update(parameter["name"].lower() for parameter in operation["parameters"])
            if path == "/v1/notifications/push-endpoints":
                body = operation["requestBody"]["content"]["application/json"]["schema"]
                assert body["$ref"] == "#/components/schemas/PushEndpointRegistrationV1"
            else:
                assert "requestBody" not in operation, path
    assert declared == {
        "limit", "cursor", "idempotency-key", "inbox_item_id", "endpoint_id", "if-match"
    }


def test_published_contract_documents_the_routes_and_leaks_nothing() -> None:
    spec = create_app().openapi()
    published = spec["paths"]
    listing = published["/v1/notifications"]["get"]
    assert listing["tags"] == ["Notifications"] and listing["security"]
    assert listing["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/NotificationPageV1"
    }
    assert "422" not in listing["responses"] and "404" in listing["responses"]
    query = {p["name"]: p for p in listing["parameters"] if p["in"] == "query"}
    assert set(query) == {"limit", "cursor"}
    assert query["limit"]["schema"]["maximum"] == 100 and query["limit"]["schema"]["default"] == 25
    one = published["/v1/notifications/{inbox_item_id}/read"]["post"]
    parameters = {(p["in"], p["name"]): p for p in one["parameters"]}
    assert parameters[("header", "Idempotency-Key")]["required"] is True
    assert "422" not in one["responses"]
    assert one["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/NotificationV1"
    }
    every = published["/v1/notifications/read-all"]["post"]
    assert every["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/NotificationReadAllV1"
    }
    register = published["/v1/notifications/push-endpoints"]["post"]
    assert register["responses"]["201"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/PushEndpointV1"
    }
    register_parameters = {(p["in"], p["name"]): p for p in register["parameters"]}
    assert register_parameters[("header", "Idempotency-Key")]["required"] is True
    revoke = published["/v1/notifications/push-endpoints/{endpoint_id}"]["delete"]
    revoke_parameters = {(p["in"], p["name"]): p for p in revoke["parameters"]}
    assert revoke_parameters[("header", "If-Match")]["required"] is True
    assert revoke_parameters[("header", "Idempotency-Key")]["required"] is True
    assert "content" not in revoke["responses"]["204"]
    assert "409" in revoke["responses"]
    schemas = spec["components"]["schemas"]
    for name in (
        "NotificationV1", "NotificationPageV1", "NotificationReadAllV1",
        "PushEndpointRegistrationV1", "PushEndpointV1",
    ):
        assert schemas[name]["additionalProperties"] is False, name
    assert set(schemas["NotificationV1"]["properties"]) == set(ITEM)
    assert set(schemas["NotificationPageV1"]["properties"]) == {
        "contract",
        "items",
        "next_cursor",
        "unread_count",
    }
    assert (
        "100 means 100 or more"
        in schemas["NotificationPageV1"]["properties"]["unread_count"]["description"]
    )
    scoped = json.dumps(
        {
            path: published[path]
            for path in published
            if "notifications" in path and "push-endpoints" not in path
        }
    ) + json.dumps({name: schemas[name] for name in schemas if name.startswith("Notification")})
    for word in HIDDEN_WORDS:
        assert word not in scoped.lower(), word
    names = {
        name
        for schema in ("NotificationV1", "NotificationPageV1")
        for name in schemas[schema]["properties"]
    }
    assert not [name for name in names if "playback" in name or "url" in name]


def test_srs_v22_description_limits_push_to_endpoint_management() -> None:
    from sketch2life.interfaces.http.openapi_srs_v22 import SRS_V22_OPENAPI_DESCRIPTION

    assert "push delivery are unavailable" in SRS_V22_OPENAPI_DESCRIPTION


def test_the_schemas_are_strict() -> None:
    for model in (NotificationV1, NotificationPageV1, NotificationReadAllV1):
        assert model.model_config["extra"] == "forbid"
    with pytest.raises(ValueError):
        NotificationV1.model_validate({**ITEM, "recipient_account_id": "x"})
    with pytest.raises(ValueError):
        NotificationV1.model_validate({**ITEM, "template_version": 0})
    with pytest.raises(ValueError):
        NotificationPageV1.model_validate({"items": [], "unread_count": 101})


# ----------------------------------------------------------------------------- validation
def test_list_parameters_are_validated(served: tuple[TestClient, FakeService]) -> None:
    client, service = served
    for query, field, code in (
        ("limit=101", "limit", "OUT_OF_RANGE"),
        ("limit=0", "limit", "OUT_OF_RANGE"),
        ("limit=abc", "limit", "INVALID_TYPE"),
    ):
        response = client.get(f"/v1/notifications?{query}")
        assert response.status_code == 400, query
        assert {"field": field, "code": code} in response.json()["field_errors"], query
    assert service.calls == []
    assert client.get("/v1/notifications?limit=100").status_code == 200


@pytest.mark.parametrize(
    "cursor",
    [
        "not-a-cursor",
        "e30",  # `{}`
        "x" * 1025,
    ],
)
def test_a_malformed_cursor_is_400(served: tuple[TestClient, FakeService], cursor: str) -> None:
    client, service = served
    response = client.get("/v1/notifications", params={"cursor": cursor})
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"
    assert service.calls == []


def test_a_cursor_of_another_scope_or_without_a_zone_is_400(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    other = encode_cursor(scope="lesson-occurrences", sort_key=NOW.isoformat(), item_id="x")
    naive = encode_cursor(scope="notifications", sort_key="2026-11-21T07:00:00", item_id="x")
    for cursor in (other, naive):
        response = client.get("/v1/notifications", params={"cursor": cursor})
        assert response.status_code == 400
        assert {"field": "cursor", "code": "INVALID_FORMAT"} in response.json()["field_errors"]
    assert service.calls == []


def test_missing_or_malformed_keys_are_400_with_a_field_error(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    for path in ("/v1/notifications/item-1/read", "/v1/notifications/read-all"):
        missing = client.post(path)
        assert missing.status_code == 400 and missing.json()["code"] == "INVALID_REQUEST"
        assert {"field": "Idempotency-Key", "code": "REQUIRED"} in missing.json()["field_errors"]
        for bad in ("has space", "x" * 129):
            response = client.post(path, headers=headers(bad))
            assert response.status_code == 400, (path, bad)
            assert response.json()["code"] == "INVALID_REQUEST"
    assert service.calls == []


def test_a_malformed_item_id_is_400_before_any_query(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    for bad in ("a b", "a%00b", "x" * 65, "a;b"):
        response = client.post(f"/v1/notifications/{bad}/read", headers=headers())
        assert response.status_code in {400, 404}, bad
        assert response.status_code != 200
    assert service.calls == []


# ----------------------------------------------------------------------------- behaviour
def test_list_returns_the_page_with_a_cursor_the_badge_and_private_headers(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    response = client.get("/v1/notifications?limit=10")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "private, no-cache"
    assert response.headers["Vary"] == "Authorization"
    body = response.json()
    assert body["contract"] == "NotificationPageV1" and body["unread_count"] == 100
    assert body["items"][0]["inbox_item_id"] == "item-1"
    assert body["next_cursor"] is not None
    ((name, kwargs),) = service.calls
    assert name == "list" and kwargs["limit"] == 10 and kwargs["after"] is None
    assert kwargs["principal"].subject == "subject-1"
    # The next request carries the cursor back as a decoded keyset.
    again = client.get("/v1/notifications", params={"cursor": body["next_cursor"]})
    assert again.status_code == 200
    assert service.calls[1][1]["after"] == (NOW, "item-1")
    assert "recipient" not in set(service.calls[1][1])


def test_the_last_page_has_no_cursor(served: tuple[TestClient, FakeService]) -> None:
    client, service = served
    service.page = InboxPage([dict(ITEM)], False, 1, NOW, "item-1")
    assert client.get("/v1/notifications").json()["next_cursor"] is None
    service.page = InboxPage([], False, 0, None, None)
    empty = client.get("/v1/notifications").json()
    assert empty["items"] == [] and empty["next_cursor"] is None and empty["unread_count"] == 0


def test_mark_read_and_read_all_forward_the_key_and_answer_200(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    one = client.post("/v1/notifications/item-1/read", headers=headers("k-1"))
    assert one.status_code == 200 and one.json()["read_at"] is not None
    assert one.json()["contract"] == "NotificationV1"
    every = client.post("/v1/notifications/read-all", headers=headers("k-2"))
    assert every.status_code == 200
    assert every.json() == {"contract": "NotificationReadAllV1", "marked_count": 4}
    (_, first), (_, second) = service.calls
    assert first["inbox_item_id"] == "item-1" and first["idempotency_key"] == "k-1"
    assert second["idempotency_key"] == "k-2" and "inbox_item_id" not in second


@pytest.mark.parametrize(
    ("error", "status", "code"),
    [
        (NotificationError(404, "RESOURCE_NOT_FOUND"), 404, "RESOURCE_NOT_FOUND"),
        (NotificationError(400, "INVALID_IDEMPOTENCY_KEY"), 400, "INVALID_IDEMPOTENCY_KEY"),
    ],
)
def test_service_errors_use_the_conv1_envelope(
    served: tuple[TestClient, FakeService], error: Exception, status: int, code: str
) -> None:
    client, service = served
    service.error = error
    for response in (
        client.get("/v1/notifications"),
        client.post("/v1/notifications/item-1/read", headers=headers()),
        client.post("/v1/notifications/read-all", headers=headers()),
    ):
        assert response.status_code == status
        body = response.json()
        assert body["code"] == code
        assert {"message", "correlation_id", "retryable", "field_errors"} <= set(body)
        assert "retry_after_seconds" in body
        assert body["request_id"] == body["correlation_id"]


def test_unauthenticated_calls_are_401_in_the_conv1_envelope() -> None:
    application = create_app()
    with TestClient(application) as client:
        for response in (
            client.get("/v1/notifications"),
            client.post("/v1/notifications/read-all", headers=headers()),
        ):
            assert response.status_code == 401
            assert response.json()["code"] == "AUTH_REQUIRED"
