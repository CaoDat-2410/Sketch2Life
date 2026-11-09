"""Contract-alignment checks for the published Swagger/OpenAPI surface."""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.openapi_contract import (
    MOUNTED_OPERATION_COUNT,
    MOUNTED_OPERATIONS,
    TAG_DESCRIPTIONS,
    UNMOUNTED_OPERATION_COUNT,
    UNMOUNTED_OPERATIONS,
)
from sketch2life.interfaces.http.openapi_contract_amendments import (
    PORTFOLIO_OPERATION_KEY,
    RESTORE_CHECKPOINT_OPERATION_KEY,
    RESTORE_CHECKPOINT_RESPONSE_DESCRIPTIONS,
    public_tag_name,
    public_tags,
    published_responses,
)
from sketch2life.interfaces.http.openapi_srs_v22 import (
    SRS_V22_INCLUDED_OPERATIONS,
    SRS_V22_TAGS,
)

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}


@pytest.fixture(autouse=True)
def _disable_dotenv_for_composition_tests(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    monkeypatch.setenv(
        "SKETCH2LIFE_DATABASE_URL", "postgresql+psycopg://localhost:9/s1at_closed"
    )
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    assert Settings.model_config.get("env_file") is None
    assert CoreDatabaseSettings.model_config.get("env_file") is None
    try:
        yield
    finally:
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


UPLOAD_TRANSPORT_TOO_LARGE_OPERATIONS = {
    ("post", "/v1/sessions/{session_id}/media/audio"),
    ("post", "/v1/sessions/{session_id}/media/image"),
}
# T9's local/test-only candidate lookup is intentionally outside the pinned Rev37 catalog.
PILOT_ONLY_OPERATIONS = {
    (
        "get",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/pilot-profiles",
    ),
    ("post", "/api/be1/v1/assistance-requests"),
    ("post", "/api/be1/v1/assistance-requests/{assistance_id}/cancel"),
    (
        "get",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/assistance-requests/{assistance_id}/status",
    ),
    (
        "get",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/teacher/assistance-requests/pending",
    ),
}
CONTRACT_PARAMETER = re.compile(r"\b(path|query|header|cookie)\s+`([^`]+)`:\s*([^;]+)")
CONTRACT_REQUEST_BODY = re.compile(
    r"([A-Za-z0-9.+_-]+/[A-Za-z0-9.+_-]+)(?:\s+\((required|optional)\))?:\s*"
    r"([A-Za-z][A-Za-z0-9_]*)"
)


def _schema_refs(value: Any) -> set[str]:
    if isinstance(value, dict):
        refs = {value["$ref"].rsplit("/", maxsplit=1)[-1]} if "$ref" in value else set()
        for child in value.values():
            refs.update(_schema_refs(child))
        return refs
    if isinstance(value, list):
        refs: set[str] = set()
        for child in value:
            refs.update(_schema_refs(child))
        return refs
    return set()


def _extension_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        keys = {key for key in value if key.startswith("x-")}
        for child in value.values():
            keys.update(_extension_keys(child))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for child in value:
            keys.update(_extension_keys(child))
        return keys
    return set()


def test_swagger_ui_and_openapi_json_are_published(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKETCH2LIFE_ENV", "local")
    monkeypatch.setenv("SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED", "true")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    app = create_app()
    runtime = getattr(app.state, "be1_runtime", None)
    try:
        client = TestClient(app)
        docs_response = client.get("/docs")
        openapi_response = client.get("/openapi.json")
        assert docs_response.status_code == 200
        assert "swagger-ui" in docs_response.text
        assert openapi_response.status_code == 200
        published_spec = openapi_response.json()
        assert published_spec["openapi"] == "3.1.0"
        assert published_spec["info"]["title"] == "Sketch2Life FE API"
        assert published_spec["tags"] == SRS_V22_TAGS
        assert len(published_spec["info"]["description"].split()) <= 55
        assert all(len(tag["description"].split()) <= 9 for tag in published_spec["tags"])
        assert "ApiError" in published_spec["components"]["schemas"]
        assert "Be1Error" not in published_spec["components"]["schemas"]
        assert all(
            "BE1" not in response.get("description", "")
            for path_item in published_spec["paths"].values()
            for operation in path_item.values()
            for response in operation.get("responses", {}).values()
        )
        published_operations = {
            (method.lower(), path)
            for path, path_item in published_spec["paths"].items()
            for method in path_item
            if method.lower() in HTTP_METHODS
        }
        assert published_operations == set(SRS_V22_INCLUDED_OPERATIONS)
    finally:
        if runtime is not None and runtime.engine is not None:
            runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


@pytest.fixture
def runtime_openapi(monkeypatch: pytest.MonkeyPatch) -> Iterator[dict[str, Any]]:
    monkeypatch.setenv("SKETCH2LIFE_ENV", "local")
    monkeypatch.setenv("SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED", "true")
    monkeypatch.setenv("SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED", "true")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    app = create_app()
    runtime = getattr(app.state, "be1_runtime", None)
    try:
        app.openapi()
        yield app.state.runtime_openapi_schema
    finally:
        if runtime is not None and runtime.engine is not None:
            runtime.engine.dispose()
        monkeypatch.undo()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def test_runtime_openapi_preserves_local_synthetic_examples(
    runtime_openapi: dict[str, Any],
) -> None:
    session_example = runtime_openapi["paths"]["/v1/sessions"]["post"]["requestBody"][
        "content"
    ]["application/json"]["examples"]["localSyntheticSession"]["value"]
    assert session_example["actor_ref"] == "demo:local"
    assert session_example["expected_session_version"] == 0
    assert session_example["payload"] == {"operation": "CREATE_SESSION"}

    image_operation = runtime_openapi["paths"]["/v1/sessions/{session_id}/media/image"]["post"]
    image_example = image_operation["requestBody"]["content"]["multipart/form-data"]["examples"][
        "localSyntheticPng"
    ]["value"]
    assert image_example["image"] == "synthetic-demo.png"
    assert image_example["normalization_policy"] == "IDENTITY_V1"
    image_headers = {
        parameter["name"]: parameter["example"]
        for parameter in image_operation["parameters"]
        if parameter.get("in") == "header" and "example" in parameter
    }
    assert image_headers["X-Actor-Ref"] == "demo:local"
    assert image_headers["X-Synthetic-Non-Child-Confirmed"] is True
    assert "without invoking an AI provider" in image_operation["description"]


def test_runtime_openapi_matches_all_mounted_rev37_operations_and_records_unmounted_candidates(
    runtime_openapi: dict[str, Any],
) -> None:
    spec = runtime_openapi
    operations = {
        (method.lower(), path): operation
        for path, path_item in spec["paths"].items()
        for method, operation in path_item.items()
        if method.lower() in HTTP_METHODS
    }

    assert spec["openapi"] == "3.1.0"
    assert spec["tags"] == public_tags(TAG_DESCRIPTIONS)
    assert len(operations) == 128
    catalog_operations = set(operations) - PILOT_ONLY_OPERATIONS
    catalog_paths = {path for _method, path in catalog_operations}
    assert len(catalog_paths) == 110
    assert len(catalog_operations) == MOUNTED_OPERATION_COUNT == 123
    assert catalog_operations == set(MOUNTED_OPERATIONS)
    assert set(operations) - set(MOUNTED_OPERATIONS) == PILOT_ONLY_OPERATIONS
    assert PILOT_ONLY_OPERATIONS.isdisjoint(MOUNTED_OPERATIONS)
    profile_lookup = operations[
        (
            "get",
            "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/pilot-profiles",
        )
    ]
    assert "x-contract-surface" not in profile_lookup
    assert len(PILOT_ONLY_OPERATIONS) == 5

    assert (
        "post",
        "/api/be1/v1/organizations/{organization_id}/assignments",
    ) not in operations
    assert (
        "delete",
        "/api/be1/v1/organizations/{organization_id}/assignments/{assignment_id}",
    ) not in operations
    assignment_key = ("post", "/api/be1/v1/classes/{class_id}/assignments")
    assert assignment_key in operations
    assignment_body = operations[assignment_key]["requestBody"]["content"][
        "application/json"
    ]
    assignment_schema_name = next(iter(_schema_refs(assignment_body["schema"])))
    assert set(spec["components"]["schemas"][assignment_schema_name]["properties"]) == {
        "subject"
    }

    profile_key = (
        "post",
        "/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles",
    )
    profile_body = operations[profile_key]["requestBody"]["content"][
        "application/json"
    ]
    profile_schema_name = next(iter(_schema_refs(profile_body["schema"])))
    profile_schema = spec["components"]["schemas"][profile_schema_name]
    assert set(profile_schema["properties"]) == {
        "class_id",
        "display_name",
        "age_months",
    }
    assert profile_schema["properties"]["age_months"]["minimum"] == 36
    assert profile_schema["properties"]["age_months"]["maximum"] == 120

    for key, contract in MOUNTED_OPERATIONS.items():
        operation = operations[key]
        if key in {
            ("post", "/v1/sessions"),
            ("post", "/v1/sessions/{session_id}/media/image"),
            RESTORE_CHECKPOINT_OPERATION_KEY,
            PORTFOLIO_OPERATION_KEY,
            (
                "get",
                "/api/be1/v1/organizations/{organization_id}/classes/"
                "{class_id}/profiles/{child_id}/portfolio",
            ),
        }:
            assert operation["description"].startswith(contract["purpose"])
        else:
            assert operation["description"] == contract["purpose"]
        assert operation["tags"] == [public_tag_name(contract["tag"])]
        assert contract["tag"] in TAG_DESCRIPTIONS
        if contract["authentication"] == "HTTPBearer (bearer)":
            assert operation["security"] == [{"HTTPBearer": []}]
        else:
            assert "security" not in operation
        assert operation.get("responses")
        assert operation.get("operationId")
        declared_responses = {
            response["status"]: response
            for response in published_responses(key, contract["responses"])
        }
        assert set(operation["responses"]) == set(declared_responses)
        for status, response_contract in declared_responses.items():
            runtime_response = operation["responses"][status]
            expected_response_description = (
                RESTORE_CHECKPOINT_RESPONSE_DESCRIPTIONS.get(
                    status, response_contract["description"]
                )
                if key == RESTORE_CHECKPOINT_OPERATION_KEY
                else response_contract["description"]
            )
            assert runtime_response["description"] == expected_response_description
            media_type = response_contract["media_type"]
            if media_type:
                assert set(runtime_response["content"]) == {media_type}
                response_schema = runtime_response["content"][media_type]["schema"]
                schema_name = response_contract["schema_name"]
                if schema_name == "object":
                    assert response_schema.get("type") == "object"
                elif schema_name == "binary":
                    assert response_schema == {"type": "string", "format": "binary"}
                elif schema_name:
                    list_schema = re.match(r"^list\[([A-Za-z][A-Za-z0-9_]*)", schema_name)
                    expected_schema = list_schema.group(1) if list_schema else schema_name
                    assert expected_schema in _schema_refs(response_schema)
                    if list_schema:
                        assert response_schema.get("type") == "array"
            else:
                assert not runtime_response.get("content")

        expected_parameters = {}
        for location, raw_name, _type in CONTRACT_PARAMETER.findall(contract["request_inputs"]):
            required = raw_name.endswith("*")
            name = raw_name.removesuffix("*")
            expected_parameters[(location, name)] = required
        actual_parameters = {
            (parameter["in"], parameter["name"]): bool(parameter.get("required"))
            for parameter in operation.get("parameters", [])
        }
        assert actual_parameters == expected_parameters

        expected_bodies = CONTRACT_REQUEST_BODY.findall(contract["request_inputs"])
        request_body = operation.get("requestBody")
        assert bool(request_body) == bool(expected_bodies)
        for media_type, requiredness, schema_name in expected_bodies:
            assert media_type in request_body["content"]
            assert bool(request_body.get("required")) == (requiredness == "required")
            if schema_name == "object":
                assert request_body["content"][media_type]["schema"].get("type") == "object"
            else:
                assert schema_name in _schema_refs(request_body["content"][media_type]["schema"])

        if key in UPLOAD_TRANSPORT_TOO_LARGE_OPERATIONS:
            response_413 = operation["responses"]["413"]
            assert "x-contract-runtime-mismatch" not in response_413
            schema = response_413["content"]["application/json"]["schema"]
            assert schema == {"$ref": "#/components/schemas/MobileWorkflowResultV1"}

        if key[1].startswith("/api/be1/v1/"):
            if key == RESTORE_CHECKPOINT_OPERATION_KEY:
                expected_statuses = {
                    "200", "401", "403", "404", "409", "410", "422", "500", "503"
                }
                expected_default_codes = None
            elif key == PORTFOLIO_OPERATION_KEY:
                expected_statuses = {"401", "403", "409", "422", "default"}
                expected_default_codes = "404, 410, 413, 415, 429, 500, 503"
            else:
                success_status = next(
                    row["status"]
                    for row in declared_responses.values()
                    if row["status"] not in {"401", "403", "422", "default"}
                )
                expected_statuses = {
                    success_status,
                    "401",
                    "403",
                    "422",
                    "default",
                }
                expected_default_codes = "404, 409, 410, 413, 415, 429, 500, 503"
            assert set(operation["responses"]) == expected_statuses
            if expected_default_codes is not None:
                default_response = operation["responses"]["default"]
                assert expected_default_codes in default_response["description"]
                assert default_response["content"]["application/json"]["schema"] == {
                    "$ref": "#/components/schemas/Be1Error"
                }

    candidate_keys = {(item["method"], item["path"]) for item in UNMOUNTED_OPERATIONS}
    assert len(candidate_keys) == UNMOUNTED_OPERATION_COUNT == 11
    assert not candidate_keys.intersection(operations)
    assert not _extension_keys(spec)

    assert len(spec["tags"]) == 18
    assert all(tag.get("description") for tag in spec["tags"])

    operation_ids = [operation["operationId"] for operation in operations.values()]
    assert len(operation_ids) == len(set(operation_ids))
    json.dumps(spec, ensure_ascii=False)
