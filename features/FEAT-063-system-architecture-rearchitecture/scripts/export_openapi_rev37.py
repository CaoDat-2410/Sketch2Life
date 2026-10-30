"""Export and verify the FEAT-063 Rev37 local-Compose OpenAPI snapshot."""

# ruff: noqa: I001

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "backend" / "src"))

from sketch2life.interfaces.http.app import create_app  # noqa: E402
from sketch2life.interfaces.http.openapi_contract import (  # noqa: E402
    CONTRACT_REVISION,
    DECLARED_OPERATION_COUNT,
    MOUNTED_OPERATIONS,
    MOUNTED_OPERATION_COUNT,
    SOURCE_SHA256,
    TAG_DESCRIPTIONS,
    UNMOUNTED_OPERATIONS,
    UNMOUNTED_OPERATION_COUNT,
)


HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}
CONTRACT_PARAMETER = re.compile(r"\b(path|query|header|cookie)\s+`([^`]+)`:\s*([^;]+)")
CONTRACT_REQUEST_BODY = re.compile(
    r"([A-Za-z0-9.+_-]+/[A-Za-z0-9.+_-]+)(?:\s+\((required|optional)\))?:\s*"
    r"([A-Za-z][A-Za-z0-9_]*)"
)


def _operation_map(spec: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (method.lower(), path): operation
        for path, path_item in spec.get("paths", {}).items()
        for method, operation in path_item.items()
        if method.lower() in HTTP_METHODS
    }


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


def _verify(spec: dict[str, Any]) -> None:
    operations = _operation_map(spec)
    expected = set(MOUNTED_OPERATIONS)
    observed = set(operations)
    if observed != expected:
        missing = sorted(expected - observed)
        extra = sorted(observed - expected)
        raise SystemExit(
            f"OpenAPI operation mismatch; missing={missing}; extra={extra}"
        )
    if len(spec.get("paths", {})) != 111:
        raise SystemExit(
            f"Expected 111 OpenAPI paths; found {len(spec.get('paths', {}))}"
        )
    if spec.get("openapi") != "3.1.0":
        raise SystemExit(f"Expected OpenAPI 3.1.0; found {spec.get('openapi')!r}")
    expected_tags = [
        {"name": name, "description": description}
        for name, description in TAG_DESCRIPTIONS.items()
    ]
    if spec.get("tags") != expected_tags:
        raise SystemExit(
            "OpenAPI tag names/descriptions do not match the curated navigation groups"
        )
    contract_info = spec.get("info", {}).get("x-contract-catalog", {})
    expected_contract_info = {
        "revision": CONTRACT_REVISION,
        "source_sha256": SOURCE_SHA256,
        "declared_operations": DECLARED_OPERATION_COUNT,
        "mounted_in_default_compose": MOUNTED_OPERATION_COUNT,
        "unmounted_candidates": UNMOUNTED_OPERATION_COUNT,
        "runtime_operation_count": MOUNTED_OPERATION_COUNT,
    }
    if any(
        contract_info.get(key) != value for key, value in expected_contract_info.items()
    ):
        raise SystemExit(f"OpenAPI contract source metadata mismatch: {contract_info}")
    for key, contract in MOUNTED_OPERATIONS.items():
        operation = operations[key]
        if key in {
            ("post", "/v1/sessions"),
            ("post", "/v1/sessions/{session_id}/media/image"),
        }:
            if not operation.get("description", "").startswith(contract["purpose"]):
                raise SystemExit(f"Missing contract purpose for {key}")
        elif operation.get("description") != contract["purpose"]:
            raise SystemExit(f"Missing or mismatched contract purpose for {key}")
        if operation.get("tags") != [contract["tag"]]:
            raise SystemExit(f"Missing or mismatched surface tag for {key}")
        if operation.get("x-contract-request-inputs") != contract["request_inputs"]:
            raise SystemExit(f"Missing request-input contract metadata for {key}")
        if operation.get("x-contract-authentication") != contract["authentication"]:
            raise SystemExit(f"Missing authentication contract metadata for {key}")
        if contract["authentication"] == "HTTPBearer (bearer)":
            if operation.get("security") != [{"HTTPBearer": []}]:
                raise SystemExit(f"Authentication/security mismatch for {key}")
        elif "security" in operation:
            raise SystemExit(f"Undeclared OpenAPI security requirement for {key}")
        expected_parameters = {}
        for location, raw_name, _type in CONTRACT_PARAMETER.findall(
            contract["request_inputs"]
        ):
            required = raw_name.endswith("*")
            name = raw_name.removesuffix("*")
            expected_parameters[(location, name)] = required
        actual_parameters = {
            (parameter["in"], parameter["name"]): bool(parameter.get("required"))
            for parameter in operation.get("parameters", [])
        }
        if actual_parameters != expected_parameters:
            raise SystemExit(
                f"Request parameter mismatch for {key}; "
                f"expected={expected_parameters}; actual={actual_parameters}"
            )
        expected_bodies = CONTRACT_REQUEST_BODY.findall(contract["request_inputs"])
        request_body = operation.get("requestBody")
        if bool(request_body) != bool(expected_bodies):
            raise SystemExit(f"Request-body presence mismatch for {key}")
        for media_type, requiredness, schema_name in expected_bodies:
            if media_type not in request_body.get("content", {}):
                raise SystemExit(
                    f"Request-body media type mismatch for {key}: {media_type}"
                )
            if bool(request_body.get("required")) != (requiredness == "required"):
                raise SystemExit(f"Request-body requiredness mismatch for {key}")
            request_schema = request_body["content"][media_type]["schema"]
            if schema_name == "object" and request_schema.get("type") != "object":
                raise SystemExit(f"Generic request object schema missing for {key}")
            if schema_name != "object" and schema_name not in _schema_refs(
                request_schema
            ):
                raise SystemExit(
                    f"Request-body schema mismatch for {key}: {schema_name}"
                )
        declared_responses = {
            response["status"]: response for response in contract["responses"]
        }
        actual_responses = operation.get("responses", {})
        if set(actual_responses) != set(declared_responses):
            raise SystemExit(
                f"Response-code mismatch for {key}; "
                f"missing={sorted(set(declared_responses) - set(actual_responses))}; "
                f"extra={sorted(set(actual_responses) - set(declared_responses))}"
            )
        if operation.get("x-contract-declared-responses") != list(
            contract["responses"]
        ):
            raise SystemExit(f"Missing contract response metadata for {key}")
        for status, response_contract in declared_responses.items():
            if (
                actual_responses[status].get("description")
                != response_contract["description"]
            ):
                raise SystemExit(
                    f"Response description mismatch for {key} HTTP {status}"
                )
            response = actual_responses[status]
            media_type = response_contract["media_type"]
            content = response.get("content", {})
            if media_type:
                if set(content) != {media_type}:
                    raise SystemExit(
                        f"Response media type mismatch for {key} HTTP {status}"
                    )
                response_schema = content[media_type].get("schema", {})
                schema_name = response_contract["schema_name"]
                if schema_name == "object" and response_schema.get("type") != "object":
                    raise SystemExit(
                        f"Generic response object schema missing for {key} HTTP {status}"
                    )
                if schema_name and schema_name != "object":
                    list_schema = re.match(
                        r"^list\[([A-Za-z][A-Za-z0-9_]*)", schema_name
                    )
                    expected_schema = (
                        list_schema.group(1) if list_schema else schema_name
                    )
                    if expected_schema not in _schema_refs(response_schema):
                        raise SystemExit(
                            f"Response schema mismatch for {key} HTTP {status}: {schema_name}"
                        )
                    if list_schema and response_schema.get("type") != "array":
                        raise SystemExit(
                            f"Response array schema missing for {key} HTTP {status}"
                        )
            elif content:
                raise SystemExit(f"Unexpected response body for {key} HTTP {status}")
        if key in {
            ("post", "/v1/sessions/{session_id}/media/audio"),
            ("post", "/v1/sessions/{session_id}/media/image"),
        }:
            response_413 = actual_responses["413"]
            if "x-contract-runtime-mismatch" in response_413:
                raise SystemExit(f"Unexpected runtime/contract 413 discrepancy for {key}")
            response_schema = response_413["content"]["application/json"]["schema"]
            if response_schema != {"$ref": "#/components/schemas/MobileWorkflowResultV1"}:
                raise SystemExit(f"Mismatched Rev37 413 response schema for {key}")

    session_example = spec["paths"]["/v1/sessions"]["post"]["requestBody"]["content"][
        "application/json"
    ]["examples"].get("localSyntheticSession", {}).get("value", {})
    if session_example.get("payload") != {"operation": "CREATE_SESSION"}:
        raise SystemExit("Missing local synthetic session request example")
    image_operation = spec["paths"]["/v1/sessions/{session_id}/media/image"]["post"]
    image_example = image_operation["requestBody"]["content"]["multipart/form-data"][
        "examples"
    ].get("localSyntheticPng", {}).get("value", {})
    if image_example.get("image") != "synthetic-demo.png":
        raise SystemExit("Missing local synthetic image upload request example")
    unmounted = {(entry["method"], entry["path"]) for entry in UNMOUNTED_OPERATIONS}
    if len(unmounted) != 11 or observed.intersection(unmounted):
        raise SystemExit(
            "Candidate/fixture operations must remain outside active OpenAPI paths"
        )
    if spec.get("x-unmounted-operations") != list(UNMOUNTED_OPERATIONS):
        raise SystemExit(
            "OpenAPI must retain exact metadata for all 11 not-mounted operations"
        )
    operation_ids = [op.get("operationId") for op in operations.values()]
    if len(operation_ids) != len(set(operation_ids)):
        raise SystemExit("OpenAPI contains duplicate operationId values")
    json.dumps(spec, ensure_ascii=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT
        / "features/FEAT-063-system-architecture-rearchitecture/artifacts/OPENAPI_FEAT063_REV37_20261030.json",
        help="Output path for the OpenAPI JSON snapshot",
    )
    args = parser.parse_args()
    if os.getenv("SKETCH2LIFE_ENV", "").lower() != "local":
        raise SystemExit(
            "Set SKETCH2LIFE_ENV=local to export the local-Compose API profile"
        )
    if os.getenv("SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED", "").lower() not in {
        "1",
        "true",
        "yes",
        "on",
    }:
        raise SystemExit(
            "Set SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED=true to include the three local routes"
        )

    app = create_app()
    spec = app.openapi()
    _verify(spec)
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"OPENAPI_VALID: {len(MOUNTED_OPERATIONS)} mounted operations, "
        f"{len(spec['paths'])} paths, {len(UNMOUNTED_OPERATIONS)} unmounted candidates; wrote {output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
