"""Export and verify the FE-facing OpenAPI projection for SRS v2.2."""

# ruff: noqa: I001

from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "backend" / "src"))

from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.openapi_contract_amendments import (
    PORTFOLIO_OPERATION_KEY,
    RESTORE_CHECKPOINT_OPERATION_KEY,
    RESTORE_CHECKPOINT_RESPONSE_DESCRIPTIONS,
    published_responses,
    public_tag_name,
    public_tags,
)
from sketch2life.interfaces.http.openapi_contract import (
    MOUNTED_OPERATIONS,
    TAG_DESCRIPTIONS,
    UNMOUNTED_OPERATIONS,
)
from sketch2life.interfaces.http.openapi_srs_v22 import (
    SRS_V22_INCLUDED_OPERATIONS,
    SRS_V22_OPERATION_TAGS,
    SRS_V22_TAGS,
    publicize_openapi_terms,
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
    expected_tags = public_tags(TAG_DESCRIPTIONS)
    if spec.get("tags") != expected_tags:
        raise SystemExit(
            "OpenAPI tag names/descriptions do not match the curated navigation groups"
        )
    extensions = _extension_keys(spec)
    if extensions:
        raise SystemExit(f"Public OpenAPI must not contain custom extensions: {extensions}")
    for key, contract in MOUNTED_OPERATIONS.items():
        operation = operations[key]
        if key in {
            ("post", "/v1/sessions"),
            ("post", "/v1/sessions/{session_id}/media/image"),
            (
                "post",
                "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/restore",
            ),

            PORTFOLIO_OPERATION_KEY,
        }:
            if not operation.get("description", "").startswith(contract["purpose"]):
                raise SystemExit(f"Missing contract purpose for {key}")
        elif operation.get("description") != contract["purpose"]:
            raise SystemExit(f"Missing or mismatched contract purpose for {key}")
        if operation.get("tags") != [public_tag_name(contract["tag"])]:
            raise SystemExit(f"Missing or mismatched surface tag for {key}")
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
        effective_rows = published_responses(key, contract["responses"])
        declared_responses = {
            response["status"]: response for response in effective_rows
        }
        actual_responses = operation.get("responses", {})
        if set(actual_responses) != set(declared_responses):
            raise SystemExit(
                f"Response-code mismatch for {key}; "
                f"missing={sorted(set(declared_responses) - set(actual_responses))}; "
                f"extra={sorted(set(actual_responses) - set(declared_responses))}"
            )
        for status, response_contract in declared_responses.items():
            expected_description = (
                RESTORE_CHECKPOINT_RESPONSE_DESCRIPTIONS.get(
                    status, response_contract["description"]
                )
                if key == RESTORE_CHECKPOINT_OPERATION_KEY
                else response_contract["description"]
            )
            if actual_responses[status].get("description") != expected_description:
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
                if schema_name == "binary":
                    if response_schema != {"type": "string", "format": "binary"}:
                        raise SystemExit(f"Binary response schema mismatch for {key} HTTP {status}")
                elif schema_name and schema_name != "object":
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
        if key[1].startswith("/api/be1/v1/"):
            if key == PORTFOLIO_OPERATION_KEY:
                expected_statuses = {"401", "403", "409", "422", "default"}
                expected_default_codes = "404, 410, 413, 415, 429, 500, 503"
            elif key == RESTORE_CHECKPOINT_OPERATION_KEY:
                expected_statuses = {
                    "200", "401", "403", "404", "409", "410", "422", "500", "503"
                }
                expected_default_codes = None
            else:
                success_status = next(
                    row["status"]
                    for row in effective_rows
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
            if set(actual_responses) != expected_statuses:
                raise SystemExit(f"BE1 response list is not concise for {key}")
            if expected_default_codes is not None:
                default_response = actual_responses["default"]
                if expected_default_codes not in default_response.get(
                    "description", ""
                ):
                    raise SystemExit(f"BE1 default response omits known statuses for {key}")
                if default_response.get("content", {}).get("application/json", {}).get(
                    "schema"
                ) != {"$ref": "#/components/schemas/Be1Error"}:
                    raise SystemExit(f"BE1 default error schema mismatch for {key}")
        if key in {
            ("post", "/v1/sessions/{session_id}/media/audio"),
            ("post", "/v1/sessions/{session_id}/media/image"),
        }:
            response_413 = actual_responses["413"]
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
    operation_ids = [op.get("operationId") for op in operations.values()]
    if len(operation_ids) != len(set(operation_ids)):
        raise SystemExit("OpenAPI contains duplicate operationId values")
    json.dumps(spec, ensure_ascii=False)


def _verify_srs_v22(
    runtime_spec: dict[str, Any], published_spec: dict[str, Any]
) -> None:
    expected = set(SRS_V22_INCLUDED_OPERATIONS)
    runtime_operations = _operation_map(runtime_spec)
    published_operations = _operation_map(published_spec)
    if len(expected) != 24 or len(SRS_V22_OPERATION_TAGS) != len(expected):
        raise SystemExit("SRS v2.2 allowlist or tag mapping count is incorrect")
    if set(published_operations) != expected:
        raise SystemExit(
            "Published operations differ from the SRS v2.2 allowlist; "
            f"missing={sorted(expected - set(published_operations))}; "
            f"unexpected={sorted(set(published_operations) - expected)}"
        )
    if len(published_spec.get("paths", {})) != 17:
        raise SystemExit("SRS v2.2 OpenAPI must contain exactly 17 paths")
    if published_spec.get("tags") != SRS_V22_TAGS:
        raise SystemExit("SRS v2.2 public tags differ from the approved grouping")
    if len(published_spec.get("info", {}).get("description", "").split()) > 55:
        raise SystemExit("SRS v2.2 Swagger overview is longer than 55 words")
    if any(len(tag.get("description", "").split()) > 9 for tag in SRS_V22_TAGS):
        raise SystemExit("SRS v2.2 Swagger tag descriptions must stay concise")
    if published_spec.get("info", {}).get("title") != "Sketch2Life FE API":
        raise SystemExit("SRS v2.2 FE OpenAPI title is missing")
    if _extension_keys(published_spec):
        raise SystemExit("Published OpenAPI contains a non-standard x- extension")

    for key, operation in published_operations.items():
        if key not in runtime_operations:
            raise SystemExit(f"Published operation has no mounted runtime handler: {key}")
        expected_operation = deepcopy(runtime_operations[key])
        expected_operation["tags"] = [SRS_V22_OPERATION_TAGS[key]]
        expected_operation = publicize_openapi_terms(expected_operation)
        if operation != expected_operation:
            raise SystemExit(f"Published operation differs from runtime metadata: {key}")

    schemas = published_spec.get("components", {}).get("schemas", {})
    for name in _schema_refs(published_spec.get("paths", {})):
        if name not in schemas:
            raise SystemExit(f"Published OpenAPI references missing schema: {name}")
    if "BE1" in " ".join(tag["name"] for tag in published_spec.get("tags", [])):
        raise SystemExit("Technical BE1 acronym leaked into the FE-facing tag names")
    if "Be1Error" in schemas or "BE1" in json.dumps(published_spec, ensure_ascii=False):
        raise SystemExit("Internal BE1 naming leaked into the FE-facing OpenAPI values")
    json.dumps(published_spec, ensure_ascii=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT
        / "features/FEAT-063-system-architecture-rearchitecture/artifacts/OPENAPI_FEAT063_REV45_20261101.json",
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
    runtime_spec = app.state.runtime_openapi_schema
    _verify(runtime_spec)
    _verify_srs_v22(runtime_spec, spec)
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"OPENAPI_VALID: {len(spec['paths'])} FE paths / "
        f"{len(_operation_map(spec))} SRS v2.2 operations; "
        f"preserved {len(MOUNTED_OPERATIONS)} full runtime operations and excluded "
        f"{len(UNMOUNTED_OPERATIONS)} unmounted candidates; wrote {output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
