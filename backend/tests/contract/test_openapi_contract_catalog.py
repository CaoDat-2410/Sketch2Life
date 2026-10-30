"""Contract-alignment checks for the published Swagger/OpenAPI surface."""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.openapi_contract import (
    CONTRACT_REVISION,
    DECLARED_OPERATION_COUNT,
    MOUNTED_OPERATION_COUNT,
    MOUNTED_OPERATIONS,
    SOURCE_SHA256,
    TAG_DESCRIPTIONS,
    UNMOUNTED_OPERATION_COUNT,
    UNMOUNTED_OPERATIONS,
)

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}
UPLOAD_TRANSPORT_TOO_LARGE_OPERATIONS = {
    ("post", "/v1/sessions/{session_id}/media/audio"),
    ("post", "/v1/sessions/{session_id}/media/image"),
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
        assert openapi_response.json()["openapi"] == "3.1.0"
    finally:
        if runtime is not None and runtime.engine is not None:
            runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


@pytest.fixture
def rev37_openapi(monkeypatch: pytest.MonkeyPatch) -> Iterator[dict[str, Any]]:
    monkeypatch.setenv("SKETCH2LIFE_ENV", "local")
    monkeypatch.setenv("SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED", "true")
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    app = create_app()
    runtime = getattr(app.state, "be1_runtime", None)
    try:
        yield app.openapi()
    finally:
        if runtime is not None and runtime.engine is not None:
            runtime.engine.dispose()
        monkeypatch.undo()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def test_swagger_matches_all_mounted_rev37_operations_and_records_unmounted_candidates(
    rev37_openapi: dict[str, Any],
) -> None:
    spec = rev37_openapi
    operations = {
        (method.lower(), path): operation
        for path, path_item in spec["paths"].items()
        for method, operation in path_item.items()
        if method.lower() in HTTP_METHODS
    }

    assert spec["openapi"] == "3.1.0"
    assert [tag["name"] for tag in spec["tags"]] == list(TAG_DESCRIPTIONS)
    assert {tag["name"]: tag["description"] for tag in spec["tags"]} == TAG_DESCRIPTIONS
    assert len(spec["paths"]) == 111
    assert len(operations) == MOUNTED_OPERATION_COUNT == 124
    assert set(operations) == set(MOUNTED_OPERATIONS)

    for key, contract in MOUNTED_OPERATIONS.items():
        operation = operations[key]
        if key in {
            ("post", "/v1/sessions"),
            ("post", "/v1/sessions/{session_id}/media/image"),
        }:
            assert operation["description"].startswith(contract["purpose"])
        else:
            assert operation["description"] == contract["purpose"]
        assert operation["tags"] == [contract["tag"]]
        assert contract["tag"] in TAG_DESCRIPTIONS
        assert operation["x-contract-request-inputs"] == contract["request_inputs"]
        assert operation["x-contract-authentication"] == contract["authentication"]
        if contract["authentication"] == "HTTPBearer (bearer)":
            assert operation["security"] == [{"HTTPBearer": []}]
        else:
            assert "security" not in operation
        assert operation["x-contract-surface"] == contract["surface"]
        assert operation["x-contract-handler"] == contract["handler"]
        assert operation["x-contract-verification"] == contract["verification"]
        assert operation.get("responses")
        assert operation.get("operationId")
        declared_responses = {response["status"]: response for response in contract["responses"]}
        assert set(operation["responses"]) == set(declared_responses)
        assert operation["x-contract-declared-responses"] == list(contract["responses"])
        for status, response_contract in declared_responses.items():
            runtime_response = operation["responses"][status]
            assert runtime_response["description"] == response_contract["description"]
            media_type = response_contract["media_type"]
            if media_type:
                assert set(runtime_response["content"]) == {media_type}
                response_schema = runtime_response["content"][media_type]["schema"]
                schema_name = response_contract["schema_name"]
                if schema_name == "object":
                    assert response_schema.get("type") == "object"
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

    candidate_keys = {(item["method"], item["path"]) for item in UNMOUNTED_OPERATIONS}
    assert len(candidate_keys) == UNMOUNTED_OPERATION_COUNT == 11
    assert not candidate_keys.intersection(operations)
    assert spec["x-unmounted-operations"] == list(UNMOUNTED_OPERATIONS)

    contract_info = spec["info"]["x-contract-catalog"]
    assert contract_info["revision"] == CONTRACT_REVISION
    assert contract_info["source_sha256"] == SOURCE_SHA256
    assert contract_info["declared_operations"] == DECLARED_OPERATION_COUNT == 135
    assert contract_info["mounted_in_default_compose"] == MOUNTED_OPERATION_COUNT == 124
    assert contract_info["unmounted_candidates"] == UNMOUNTED_OPERATION_COUNT == 11
    assert contract_info["runtime_operation_count"] == len(operations)

    session_example = spec["paths"]["/v1/sessions"]["post"]["requestBody"]["content"][
        "application/json"
    ]["examples"]["localSyntheticSession"]["value"]
    assert session_example["actor_ref"] == "demo:local"
    assert session_example["expected_session_version"] == 0
    assert session_example["payload"] == {"operation": "CREATE_SESSION"}

    image_operation = spec["paths"]["/v1/sessions/{session_id}/media/image"]["post"]
    image_example = image_operation["requestBody"]["content"]["multipart/form-data"]["examples"][
        "localSyntheticPng"
    ]["value"]
    assert image_example["image"] == "synthetic-demo.png"
    assert image_example["normalization_policy"] == "IDENTITY_V1"
    image_header_examples = {
        parameter["name"]: parameter["example"]
        for parameter in image_operation["parameters"]
        if parameter.get("in") == "header" and "example" in parameter
    }
    assert image_header_examples["X-Actor-Ref"] == "demo:local"
    assert image_header_examples["X-Synthetic-Non-Child-Confirmed"] is True
    assert "without invoking an AI provider" in image_operation["description"]

    assert len(spec["tags"]) == 18
    assert all(tag.get("description") for tag in spec["tags"])

    operation_ids = [operation["operationId"] for operation in operations.values()]
    assert len(operation_ids) == len(set(operation_ids))
    json.dumps(spec, ensure_ascii=False)
