from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.contracts.schemas.profile_sharing import (
    Be1ParentSharedProfileV1,
    ParentShareDeliveryListV1,
    ParentShareGrantListV1,
    ParentShareGrantV1,
)
from sketch2life.domain.profile_sharing import (
    ProfileShareInvalidRequest,
    ProfileShareNotFound,
    ProfileShareStaleRevision,
)
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.interfaces.http.api_conventions import encode_cursor
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_db, get_verified_adult
from sketch2life.interfaces.http.error_envelope import is_conv1_path
from sketch2life.interfaces.http.openapi_contract import MOUNTED_OPERATIONS
from sketch2life.interfaces.http.routers import be1_registry, parent_share_grants
from sketch2life.interfaces.http.routers.parent_share_grants import (
    get_share_grant_role_reader,
)


class _ActiveParent:
    @staticmethod
    def has_active_parent_role(*, principal: VerifiedPrincipal) -> bool:
        return True


@pytest.fixture
def application(monkeypatch: pytest.MonkeyPatch) -> Iterator[FastAPI]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", "postgresql+psycopg://localhost:9/s1at_closed")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    app = create_app()
    app.dependency_overrides[get_verified_adult] = lambda: VerifiedPrincipal(
        subject=str(UUID(int=1)), issuer="contract-test", roles=frozenset()
    )
    app.dependency_overrides[get_share_grant_role_reader] = lambda: _ActiveParent()
    app.dependency_overrides[get_db] = lambda: object()
    try:
        yield app
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def test_parent_share_routes_are_conv1_and_get_schemas_never_expose_the_code() -> None:
    assert is_conv1_path("/v1/parent/share-grants")
    assert is_conv1_path("/v1/parent/share-grants/00000000-0000-0000-0000-000000000001/deliveries")
    assert not is_conv1_path("/v1/parent/share-grantsfoo")
    for schema in (
        ParentShareGrantV1.model_json_schema(),
        ParentShareGrantListV1.model_json_schema(),
        ParentShareDeliveryListV1.model_json_schema(),
        Be1ParentSharedProfileV1.model_json_schema(),
    ):
        assert "invitation_code" not in str(schema)
    shared_profile_schema = Be1ParentSharedProfileV1.model_json_schema()
    assert shared_profile_schema["properties"]["fields"]["$ref"].endswith(
        "/Be1ParentSharedFieldsV1"
    )


def test_catalog_contains_each_share_operation_and_keyed_command() -> None:
    paths = {
        ("post", "/v1/parent/share-grants"),
        ("get", "/v1/parent/share-grants"),
        ("get", "/v1/parent/share-grants/{share_grant_id}"),
        ("post", "/v1/parent/share-grants/{share_grant_id}/revoke"),
        ("get", "/v1/parent/share-grants/{share_grant_id}/deliveries"),
        (
            "post",
            "/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles/{child_id}/parent-share/accept",
        ),
        (
            "get",
            "/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles/{child_id}/parent-share",
        ),
    }
    assert paths <= set(MOUNTED_OPERATIONS)
    teacher_read = MOUNTED_OPERATIONS[
        (
            "get",
            "/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles/{child_id}/parent-share",
        )
    ]
    statuses = {response["status"] for response in teacher_read["responses"]}
    assert "404" in statuses and "409" not in statuses
    assert "Withdrawn or not released profiles return the uniform 404" in teacher_read[
        "verification"
    ]


def test_invalid_body_query_and_if_match_are_400_not_422(application: FastAPI) -> None:
    client = TestClient(application)
    headers = {"Idempotency-Key": "share-contract-key-1"}
    refused = client.post(
        "/v1/parent/share-grants",
        json={
            "profile_id": "00000000-0000-0000-0000-000000000001",
            "granted_fields": ["SUPPORT_NEEDS"],
        },
        headers=headers,
    )
    assert refused.status_code == 400
    assert refused.json()["field_errors"] == [
        {"field": "granted_fields", "code": "NOT_SUPPORTED"}
    ]

    extra = client.post(
        "/v1/parent/share-grants",
        json={
            "profile_id": "00000000-0000-0000-0000-000000000001",
            "granted_fields": ["DISPLAY_NAME"],
            "unknown": True,
        },
        headers=headers,
    )
    assert extra.status_code == 400

    missing_query = client.get("/v1/parent/share-grants")
    assert missing_query.status_code == 400

    missing_key = client.post(
        "/v1/parent/share-grants",
        json={
            "profile_id": "00000000-0000-0000-0000-000000000001",
            "granted_fields": ["DISPLAY_NAME"],
        },
    )
    assert missing_key.status_code == 400
    assert {"field": "Idempotency-Key", "code": "REQUIRED"} in missing_key.json()[
        "field_errors"
    ]

    missing_match = client.post(
        "/v1/parent/share-grants/00000000-0000-0000-0000-000000000001/revoke",
        headers={"Idempotency-Key": "share-contract-key-2"},
    )
    assert missing_match.status_code == 400
    assert {"field": "If-Match", "code": "REQUIRED"} in missing_match.json()["field_errors"]

    invalid_match = client.post(
        "/v1/parent/share-grants/00000000-0000-0000-0000-000000000001/revoke",
        headers={"If-Match": "*", "Idempotency-Key": "share-contract-key-3"},
    )
    assert invalid_match.status_code == 400


def test_parent_share_create_headers_and_idempotency_mismatch(
    application: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = TestClient(application)
    profile_id = uuid4()
    grant_id = uuid4()
    now = datetime.now(UTC)
    body = {
        "contract": "ParentShareGrantV1",
        "share_grant_id": grant_id,
        "profile_id": profile_id,
        "state": "INVITED",
        "granted_fields": ["DISPLAY_NAME"],
        "created_at": now,
        "invitation_expires_at": now + timedelta(days=90),
        "accepted_at": None,
        "expires_at": None,
        "revoked_at": None,
        "revision": 1,
        "invitation_code": "SyntheticShareCode0123456789",
    }
    monkeypatch.setattr(parent_share_grants, "create_grant", lambda *args, **kwargs: (body, '"1"'))
    created = client.post(
        "/v1/parent/share-grants",
        json={"profile_id": str(profile_id), "granted_fields": ["DISPLAY_NAME"]},
        headers={"Idempotency-Key": "share-contract-create-1"},
    )
    assert created.status_code == 201
    assert created.headers["location"] == f"/v1/parent/share-grants/{grant_id}"
    assert created.headers["etag"] == '"1"'
    assert created.headers["vary"] == "Authorization"

    def mismatch(*args: object, **kwargs: object) -> None:
        raise ProfileShareInvalidRequest("INVALID_IDEMPOTENCY_KEY")

    monkeypatch.setattr(parent_share_grants, "create_grant", mismatch)
    replay_mismatch = client.post(
        "/v1/parent/share-grants",
        json={"profile_id": str(profile_id), "granted_fields": ["AGE_BAND"]},
        headers={"Idempotency-Key": "share-contract-create-1"},
    )
    assert replay_mismatch.status_code == 400
    assert replay_mismatch.json()["code"] == "INVALID_IDEMPOTENCY_KEY"


def test_parent_share_read_headers_cursor_fault_and_uniform_404(
    application: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = TestClient(application)
    grant_id = UUID(int=5)

    def missing(*args: object, **kwargs: object) -> None:
        raise ProfileShareNotFound()

    monkeypatch.setattr(parent_share_grants, "get_grant", missing)
    parent_missing = client.get(
        f"/v1/parent/share-grants/{grant_id}", headers={"X-Request-ID": "same-share-404"}
    )

    monkeypatch.setattr(parent_share_grants, "list_deliveries", missing)
    delivery_missing = client.get(
        f"/v1/parent/share-grants/{grant_id}/deliveries",
        headers={"X-Request-ID": "same-share-404"},
    )
    assert parent_missing.status_code == delivery_missing.status_code == 404
    assert parent_missing.json() == delivery_missing.json()
    assert parent_missing.json()["code"] == "RESOURCE_NOT_FOUND"

    monkeypatch.setattr(
        parent_share_grants,
        "list_grants",
        lambda *args, **kwargs: ({"contract": "ParentShareGrantListV1", "items": []}, None),
    )
    profile_id = UUID(int=7)
    listed = client.get(f"/v1/parent/share-grants?profile_id={profile_id}")
    assert listed.status_code == 200
    assert listed.headers["cache-control"] == "private, no-cache"
    assert listed.headers["vary"] == "Authorization"

    malformed_cursor = client.get(
        f"/v1/parent/share-grants?profile_id={profile_id}&cursor=not-a-cursor"
    )
    assert malformed_cursor.status_code == 400
    assert {"field": "cursor", "code": "INVALID_FORMAT"} in malformed_cursor.json()[
        "field_errors"
    ]
    scoped_invalid_item = encode_cursor(
        scope=f"parent-share-deliveries:{grant_id}",
        sort_key=datetime.now(UTC).isoformat(),
        item_id="not-a-uuid",
    )
    malformed_item_cursor = client.get(
        f"/v1/parent/share-grants/{grant_id}/deliveries?cursor={scoped_invalid_item}"
    )
    assert malformed_item_cursor.status_code == 400
    assert {"field": "cursor", "code": "INVALID_FORMAT"} in malformed_item_cursor.json()[
        "field_errors"
    ]


def test_stale_if_match_includes_current_version(
    application: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = TestClient(application)

    def stale(*args: object, **kwargs: object) -> None:
        raise ProfileShareStaleRevision(4)

    monkeypatch.setattr(parent_share_grants, "revoke_grant", stale)
    response = client.post(
        "/v1/parent/share-grants/00000000-0000-0000-0000-000000000001/revoke",
        headers={"If-Match": '"3"', "Idempotency-Key": "share-contract-stale-1"},
    )
    assert response.status_code == 409
    assert response.json()["code"] == "STALE_REVISION"
    assert response.json()["current_version"] == 4
    assert response.headers["etag"] == '"4"'


def test_teacher_missing_profile_uses_conv1_404_body_and_shared_read_cache_headers(
    application: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = TestClient(application)
    organization_id, class_id, child_id = "org-1", "class-1", "child-1"
    teacher_path = (
        f"/api/be1/v1/organizations/{organization_id}/classes/{class_id}"
        f"/profiles/{child_id}/parent-share"
    )
    monkeypatch.setattr(be1_registry, "_require_profile_teacher", lambda *args, **kwargs: None)
    monkeypatch.setattr(be1_registry, "require_assignment", lambda *args, **kwargs: [])
    monkeypatch.setattr(be1_registry, "get_class", lambda *args, **kwargs: SimpleNamespace())
    monkeypatch.setattr(be1_registry, "hide_archived_from_teacher", lambda *args, **kwargs: None)
    application.dependency_overrides[get_db] = lambda: SimpleNamespace(
        scalar=lambda *args: None, rollback=lambda: None, commit=lambda: None
    )
    teacher_missing = client.get(teacher_path, headers={"X-Request-ID": "same-share-404"})

    def parent_missing(*args: object, **kwargs: object) -> None:
        raise ProfileShareNotFound()

    monkeypatch.setattr(parent_share_grants, "get_grant", parent_missing)
    parent_missing_response = client.get(
        "/v1/parent/share-grants/00000000-0000-0000-0000-000000000001",
        headers={"X-Request-ID": "same-share-404"},
    )
    assert teacher_missing.status_code == parent_missing_response.status_code == 404
    assert teacher_missing.json() == parent_missing_response.json()
    assert teacher_missing.json()["code"] == "RESOURCE_NOT_FOUND"

    profile = SimpleNamespace(data_origin="SYNTHETIC_DEV")
    application.dependency_overrides[get_db] = lambda: SimpleNamespace(
        scalar=lambda *args: profile, rollback=lambda: None, commit=lambda: None
    )
    monkeypatch.setattr(be1_registry, "_profile_withdrawn", lambda *args, **kwargs: False)
    monkeypatch.setattr(be1_registry, "_profile_released", lambda *args, **kwargs: True)
    grant_id = UUID(int=8)
    expires_at = datetime.now(UTC) + timedelta(days=90)
    monkeypatch.setattr(
        be1_registry,
        "read_teacher_shared_profile",
        lambda *args, **kwargs: {
            "contract": "Be1ParentSharedProfileV1",
            "share_grant_id": grant_id,
            "child_id": child_id,
            "granted_fields": ["DISPLAY_NAME"],
            "expires_at": expires_at,
            "fields": {"display_name": "Synthetic profile"},
        },
    )
    teacher_read = client.get(teacher_path)
    assert teacher_read.status_code == 200
    assert teacher_read.headers["cache-control"] == "private, no-store"
    assert teacher_read.headers["vary"] == "Authorization"
    assert set(teacher_read.json()["fields"]) == {"display_name"}
