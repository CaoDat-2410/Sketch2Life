"""FEAT-066 T-2a: the generic upload-session route contract and its mount exclusivity.

SRS l.1654-1658.

Offline: no database, no storage. Behaviour against PostgreSQL and S3Mock lives in
``tests/integration/uploads/test_upload_sessions_postgres.py``.
"""

from __future__ import annotations

import inspect
import json
from collections.abc import Iterator
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from sketch2life.application.ports.story_run_lite import CommandResult
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.story_run_lite import composition
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.openapi_contract import (
    IDEMPOTENCY_MISMATCH_OPERATION_KEYS,
    MOUNTED_OPERATIONS,
)
from sketch2life.interfaces.http.openapi_srs_v22 import (
    SRS_V22_INCLUDED_OPERATIONS,
    SRS_V22_OPERATION_TAGS,
)
from sketch2life.interfaces.http.router_composition import (
    mount_all_routers,
    story_demo_replaced_routers,
)
from sketch2life.interfaces.http.routers.upload_sessions import router as upload_sessions_router

FLAG = "STORYRUN_LITE_MAIN_DEMO_ENABLED"
ACK = "STORYRUN_LITE_MAIN_DEMO_REPLACES_PARENT_ROUTER"
DATABASE_SENTINEL = "postgresql+psycopg://sentinel_user:sentinel_pw@localhost:9/sentinel_db"
OPERATIONS = (
    ("post", "/v1/upload-sessions"),
    ("get", "/v1/upload-sessions/{upload_id}"),
    ("put", "/v1/upload-sessions/{upload_id}/parts/{part_no}"),
    ("post", "/v1/upload-sessions/{upload_id}/complete"),
    ("delete", "/v1/upload-sessions/{upload_id}"),
)
KEYED = (OPERATIONS[0], OPERATIONS[3], OPERATIONS[4])
STORAGE_WORDS = (
    "bucket", "object_key", "storage_object_ref", "presigned", "credential", "amazonaws", "minio",
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


def _paths(application) -> set[str]:
    return set(application.openapi()["paths"])


# ----------------------------------------------------------------------------- catalog
def test_the_five_operations_are_catalogued_projected_and_tagged() -> None:
    for key in OPERATIONS:
        assert key in MOUNTED_OPERATIONS
        assert key in SRS_V22_INCLUDED_OPERATIONS
        assert SRS_V22_OPERATION_TAGS[key] == "Upload Sessions"
        assert MOUNTED_OPERATIONS[key]["tag"] == "Upload Sessions"
    assert len(SRS_V22_INCLUDED_OPERATIONS & set(OPERATIONS)) == 5
    for key in KEYED:
        assert key in IDEMPOTENCY_MISMATCH_OPERATION_KEYS
    assert OPERATIONS[1] not in IDEMPOTENCY_MISMATCH_OPERATION_KEYS
    assert OPERATIONS[2] not in IDEMPOTENCY_MISMATCH_OPERATION_KEYS


def test_published_contract_has_the_five_operations_and_no_storage_words() -> None:
    spec = create_app().openapi()
    published = spec["paths"]
    assert {path for _method, path in OPERATIONS} <= set(published)
    for method, path in OPERATIONS:
        operation = published[path][method]
        assert operation["tags"] == ["Upload Sessions"]
        security = operation.get("security", [])
        assert security, (method, path)
        assert operation["responses"]
        assert "422" not in operation["responses"] or method in {"put", "post"}
    create = published["/v1/upload-sessions"]["post"]
    assert create["responses"]["201"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/GenericUploadSessionV1"
    }
    parameters = {(p["in"], p["name"]): p for p in create["parameters"]}
    assert parameters[("header", "Idempotency-Key")]["required"] is True
    assert parameters[("header", "Idempotency-Key")]["schema"]["maxLength"] == 128
    part = published["/v1/upload-sessions/{upload_id}/parts/{part_no}"]["put"]
    assert part["requestBody"]["content"]["application/octet-stream"]["schema"] == {
        "type": "string", "format": "binary",
    }
    part_parameters = {(p["in"], p["name"]): p for p in part["parameters"]}
    assert part_parameters[("header", "X-Part-SHA256")]["required"] is True
    assert part_parameters[("path", "part_no")]["schema"]["maximum"] == 7
    delete = published["/v1/upload-sessions/{upload_id}"]["delete"]
    delete_parameters = {(p["in"], p["name"]) for p in delete["parameters"]}
    assert {("header", "If-Match"), ("header", "Idempotency-Key")} <= delete_parameters
    assert delete["responses"]["202"]
    done = published["/v1/upload-sessions/{upload_id}/complete"]["post"]
    assert done["responses"]["202"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/GenericUploadCompletionV1"
    }
    assert "GenericUploadCompletionV1" in spec["components"]["schemas"]
    scoped = json.dumps({path: published[path] for path in published if "upload-sessions" in path})
    scoped += json.dumps(
        {
            name: schema
            for name, schema in spec["components"]["schemas"].items()
            if name.startswith("GenericUpload")
        }
    )
    for word in STORAGE_WORDS:
        assert word not in scoped.lower(), word
    # Lesson source sessions keep their own routes, tag and schemas.
    assert "/api/lesson-library/v1/upload-sessions/{upload_session_id}" in published


def test_response_models_expose_only_the_documented_fields() -> None:
    schemas = create_app().openapi()["components"]["schemas"]
    session = set(schemas["GenericUploadSessionV1"]["properties"])
    assert session == {
        "contract", "upload_id", "purpose", "target_ref", "state", "part_size_bytes",
        "expected_parts", "accepted_parts", "byte_count", "expires_at", "revision", "asset_ref",
        "asset_state", "error_code",
    }
    assert set(schemas["GenericUploadCompletionV1"]["properties"]) == session | {
        "scanner_name", "scanner_version",
    }
    create = schemas["CreateGenericUploadRequestV1"]
    assert create["additionalProperties"] is False
    assert set(create["properties"]) == {
        "purpose", "target_ref", "media_type", "expected_size_bytes", "expected_sha256",
        "file_name",
    }
    assert set(create["properties"]["purpose"]["enum"]) == {
        "RUN_ARTWORK", "RUN_AUDIO", "OCCURRENCE_DOCUMENT", "PRESENTATION_IMAGE",
    }


# ----------------------------------------------------------------------------- mounting
def test_flag_off_mounts_the_generic_routes_with_the_conv1_envelope() -> None:
    application = create_app()
    assert {path for _m, path in OPERATIONS} <= _paths(application)
    with TestClient(application) as client:
        response = client.get("/v1/upload-sessions/anything")
    body = response.json()
    assert response.status_code == 401 and body["code"] == "AUTH_REQUIRED"  # no bearer token
    assert set(body) >= {"code", "message", "correlation_id", "retryable", "request_id"}
    assert body["request_id"] == body["correlation_id"]


def test_mount_parameter_defaults_to_true_and_the_registry_lists_the_router() -> None:
    parameter = inspect.signature(mount_all_routers).parameters["include_upload_sessions"]
    assert parameter.default is True
    assert upload_sessions_router in story_demo_replaced_routers()


def test_the_unmounted_router_serves_nothing_in_a_composition_without_it() -> None:
    from fastapi import FastAPI

    application = FastAPI()
    application.state.be1_runtime = SimpleNamespace(
        settings=SimpleNamespace(env="test", synthetic_pilot_enabled=False)
    )
    mount_all_routers(application, include_upload_sessions=False)
    assert not [p for p in _paths(application) if p.startswith("/v1/upload-sessions")]
    application = FastAPI()
    application.state.be1_runtime = SimpleNamespace(
        settings=SimpleNamespace(env="test", synthetic_pilot_enabled=False)
    )
    mount_all_routers(application)
    assert {path for _m, path in OPERATIONS} <= _paths(application)


@pytest.fixture
def local_demo(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.setenv(ACK, "1")
    get_settings.cache_clear()
    service = Mock()
    service.get_upload.return_value = CommandResult(200, {"upload_ref": "synthetic"}, 1)
    runtime = SimpleNamespace(
        repository=Mock(), service=service, vision=None, engine=Mock(),
        ensure_ready=Mock(),
    )
    monkeypatch.setattr(composition, "build_runtime", Mock(return_value=runtime))
    yield
    get_settings.cache_clear()


def _demo_client() -> TestClient:
    return TestClient(
        create_app(), base_url="http://127.0.0.1", client=("127.0.0.1", 54321)
    )


def test_with_the_demo_on_the_generic_router_is_not_mounted_and_demo_bodies_are_unchanged(
    local_demo: None,
) -> None:
    application = create_app()
    mounted = {
        route.path
        for route in application.routes
        if getattr(route, "path", "").startswith("/v1/upload-sessions")
    }
    assert "/v1/upload-sessions/{upload_id}" not in mounted  # the demo names it {upload_ref}
    with _demo_client() as client:
        served = client.get("/v1/upload-sessions/synthetic")
        invalid = client.post(
            "/v1/upload-sessions", json={"purpose": "RUN_ARTWORK"},
            headers={"Idempotency-Key": "k1"},
        )
        unknown = client.get("/v1/upload-sessions/synthetic/no-such-route")
        sibling = client.get("/v1/upload-sessionsfoo")
    assert served.status_code == 200 and served.json() == {"upload_ref": "synthetic"}
    # The demo validation body: 422, no request_id, INVALID_FIELD items, no CONV-1 shape.
    assert invalid.status_code == 422
    assert invalid.headers["Cache-Control"] == "no-store"
    assert "request_id" not in invalid.json()
    assert {item["code"] for item in invalid.json()["field_errors"]} == {"INVALID_FIELD"}
    assert unknown.status_code == 404 and unknown.json() == {"detail": "Not Found"}
    assert sibling.status_code == 404 and sibling.json() == {"detail": "Not Found"}


def test_the_same_unknown_path_is_a_conv1_envelope_when_the_demo_is_off() -> None:
    with TestClient(create_app()) as client:
        unknown = client.get("/v1/upload-sessions/synthetic/no-such-route")
        sibling = client.get("/v1/upload-sessionsfoo")
    assert unknown.status_code == 404 and unknown.json()["code"] == "RESOURCE_NOT_FOUND"
    assert sibling.status_code == 404 and "code" not in sibling.json()  # not in the family
