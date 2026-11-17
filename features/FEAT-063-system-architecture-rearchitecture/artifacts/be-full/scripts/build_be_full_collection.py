"""Generate a full-BE Bruno inventory from the mounted FastAPI contracts.

This generator creates documentation artifacts only. It never starts the ASGI
lifespan, opens a database connection, or calls a provider.
"""

from __future__ import annotations

import copy
import csv
import json
import os
import re
import sys
import unicodedata
from collections.abc import Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
BACKEND_SRC = ROOT / "backend" / "src"
OUTPUT = Path(__file__).resolve().parents[1]
COLLECTION = OUTPUT / "bruno"
METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}
PLACEHOLDER_UUID = "00000000-0000-4000-8000-000000000001"


def configure_factory_environment(*, story: bool, storage: bool) -> None:
    """Make schema generation deterministic and prevent local dotenv loading."""
    os.environ["SKETCH2LIFE_ENV"] = "local"
    os.environ["SKETCH2LIFE_AI_PROVIDER"] = "disabled"
    os.environ["SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED"] = str(storage).lower()
    os.environ["STORYRUN_LITE_MAIN_DEMO_ENABLED"] = "1" if story else "0"
    os.environ["AWS_EC2_METADATA_DISABLED"] = "true"
    for name in ("SKETCH2LIFE_DATABASE_URL", "STORYRUN_LITE_DATABASE_URL"):
        os.environ.pop(name, None)

    sys.path.insert(0, str(BACKEND_SRC))
    from sketch2life.infrastructure.config.settings import (
        CoreDatabaseSettings,
        Settings,
        get_core_database_settings,
        get_settings,
    )

    # Settings normally read the developer's ignored backend/.env. Collection
    # generation must be independent of local credentials and infrastructure.
    Settings.model_config["env_file"] = None
    Settings.model_config["extra"] = "ignore"
    CoreDatabaseSettings.model_config["env_file"] = None
    CoreDatabaseSettings.model_config["extra"] = "ignore"
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()


def build_runtime_schema(profile: str, *, story: bool, storage: bool) -> dict[str, Any]:
    configure_factory_environment(story=story, storage=storage)
    from sketch2life.interfaces.http.app import create_app

    application = create_app(_composition_profile=profile)
    # Calling the public schema builder populates state.runtime_openapi_schema;
    # this is the full internal mounted schema, not the public SRS projection.
    application.openapi()
    schema = getattr(application.state, "runtime_openapi_schema", None)
    if not isinstance(schema, dict):
        raise TypeError("application factory did not expose its runtime OpenAPI schema")
    return copy.deepcopy(schema)


def operations(schema: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    result: dict[tuple[str, str], dict[str, Any]] = {}
    paths = schema.get("paths", {})
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() not in METHODS or not isinstance(operation, dict):
                continue
            key = (method.upper(), path)
            if key in result:
                raise RuntimeError(f"duplicate method/path in runtime schema: {key}")
            result[key] = operation
    return result


def resolve_ref(value: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    ref = value.get("$ref")
    if not isinstance(ref, str) or not ref.startswith("#/components/schemas/"):
        return value
    key = ref.rsplit("/", 1)[-1].replace("~1", "/").replace("~0", "~")
    target = schema.get("components", {}).get("schemas", {}).get(key)
    if not isinstance(target, dict):
        return value
    siblings = {name: item for name, item in value.items() if name != "$ref"}
    return {**target, **siblings}


def effective_schema(value: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    resolved = resolve_ref(value, schema)
    if isinstance(resolved.get("allOf"), list):
        properties: dict[str, Any] = {}
        required: set[str] = set()
        merged: dict[str, Any] = {}
        for item in resolved["allOf"]:
            part = effective_schema(item, schema)
            properties.update(part.get("properties", {}))
            required.update(part.get("required", []))
            merged.update(
                {k: v for k, v in part.items() if k not in {"properties", "required"}}
            )
        merged.update(
            {
                k: v
                for k, v in resolved.items()
                if k not in {"allOf", "properties", "required"}
            }
        )
        properties.update(resolved.get("properties", {}))
        required.update(resolved.get("required", []))
        if properties:
            merged["properties"] = properties
        if required:
            merged["required"] = sorted(required)
        return merged
    return resolved


def is_binary(value: dict[str, Any], schema: dict[str, Any]) -> bool:
    item = effective_schema(value, schema)
    if item.get("contentMediaType") or item.get("format") == "binary":
        return True
    return any(
        isinstance(branch, dict) and is_binary(branch, schema)
        for union_key in ("anyOf", "oneOf")
        for branch in item.get(union_key, [])
    )


def sample_value(value: dict[str, Any], schema: dict[str, Any], depth: int = 0) -> Any:
    """Create type-shaped, obviously synthetic placeholders from JSON Schema."""
    if depth > 7:
        return "REPLACE_WITH_SYNTHETIC_VALUE"
    item = effective_schema(value, schema)
    for union_key in ("oneOf", "anyOf"):
        branches = item.get(union_key)
        if isinstance(branches, list) and branches:
            non_null = [branch for branch in branches if branch.get("type") != "null"]
            return sample_value(
                non_null[0] if non_null else branches[0], schema, depth + 1
            )
    if "const" in item:
        return item["const"]
    if isinstance(item.get("enum"), list) and item["enum"]:
        return item["enum"][0]

    kind = item.get("type")
    if isinstance(kind, list):
        kind = next((candidate for candidate in kind if candidate != "null"), "string")
    if kind == "object" or "properties" in item:
        properties = item.get("properties", {})
        required = item.get("required", [])
        if not isinstance(properties, dict):
            return {}
        return {
            name: sample_value(properties[name], schema, depth + 1)
            for name in required
            if name in properties and not is_binary(properties[name], schema)
        }
    if kind == "array":
        item_schema = item.get("items", {})
        minimum = item.get("minItems", 0)
        return [sample_value(item_schema, schema, depth + 1)] if minimum > 0 else []
    if kind == "boolean":
        return False
    if kind == "integer":
        minimum = item.get("minimum", 0)
        if "exclusiveMinimum" in item:
            minimum = max(minimum, item["exclusiveMinimum"] + 1)
        return int(minimum)
    if kind == "number":
        minimum = item.get("minimum", 0)
        if "exclusiveMinimum" in item:
            minimum = max(minimum, item["exclusiveMinimum"] + 0.1)
        return minimum
    if kind == "string":
        if item.get("format") == "uuid":
            return PLACEHOLDER_UUID
        if item.get("format") == "email":
            return "synthetic@example.invalid"
        if item.get("format") == "date":
            return "2000-01-01"
        if item.get("format") == "date-time":
            return "2000-01-01T00:00:00Z"
        if item.get("contentMediaType"):
            return None
        minimum = item.get("minLength", 0)
        return "x" * min(max(minimum, 1), 32) if item.get("pattern") else "REPLACE_ME"
    if kind == "null":
        return None
    return "REPLACE_ME"


def get_parameters(
    path_item: dict[str, Any], operation: dict[str, Any], schema: dict[str, Any]
) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for parameter in [
        *path_item.get("parameters", []),
        *operation.get("parameters", []),
    ]:
        if not isinstance(parameter, dict):
            continue
        resolved = resolve_ref(parameter, schema)
        if resolved.get("in") and resolved.get("name"):
            by_key[(resolved["in"], resolved["name"])] = resolved
    return list(by_key.values())


def variable_name(name: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_]", "_", name)
    if not value or value[0].isdigit():
        value = f"value_{value}"
    return value.lower()


def tag_folder(operation: dict[str, Any], path: str) -> str:
    if path.startswith("/api/dev/v1/storage-examples/"):
        return "local-storage-examples"
    if path.startswith(("/v1/story-runs", "/v1/upload-sessions")):
        return "storyrun-lite"
    tags = operation.get("tags", [])
    label = tags[0] if tags else "StoryRun-lite" if path.startswith("/v1/") else "Other"
    normalized = (
        unicodedata.normalize("NFKD", label).encode("ascii", "ignore").decode("ascii")
    )
    return (
        re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", normalized.lower())).strip("-")
        or "other"
    )


def request_kind(
    method: str, path: str, operation: dict[str, Any]
) -> tuple[str, str, str]:
    operation_id = str(operation.get("operationId", "")).lower()
    text = f"{path} {operation_id} {operation.get('summary', '')}".lower()
    provider_markers = (
        "understanding",
        "vision",
        "story-video",
        "story_video",
        "whiteboard",
        "classify",
        "segment",
        "generate",
        "generation",
        "attach_asset",
    )
    if any(marker in text for marker in provider_markers):
        return (
            "provider-capable",
            "[PROVIDER-CAPABLE - REVIEW BEFORE RUN]",
            (
                "Manual review; this operation may invoke AI or media generation. "
                "Do not run as part of a full collection sweep."
            ),
        )
    if method in {"GET", "HEAD", "OPTIONS"}:
        return (
            "read-only",
            "[READ ONLY]",
            "Local API must be running; use existing synthetic resource IDs where required.",
        )
    handler_name = operation_id.split("_api_", maxsplit=1)[0]
    query_prefixes = (
        "read_",
        "list_",
        "get_",
        "check_",
        "preview_",
        "resolve_",
        "probe_",
    )
    if method == "POST" and handler_name.startswith(query_prefixes):
        return (
            "query-style-post",
            "[QUERY-STYLE POST - VERIFY HANDLER]",
            (
                "POST request whose handler name indicates a query; "
                "confirm it is safe before execution."
            ),
        )
    if method in {"PUT", "PATCH", "DELETE"}:
        return (
            "state-changing",
            "[STATE CHANGE - DISPOSABLE DATA ONLY]",
            "Local/test only; this operation may create, change, or delete state.",
        )
    return (
        "post-action",
        "[POST/ACTION - LOCAL TEST ONLY]",
        "Local/test only; inspect the handler and use disposable synthetic data before execution.",
    )


def expected_success(operation: dict[str, Any]) -> str:
    statuses = sorted(
        (
            status
            for status in operation.get("responses", {})
            if str(status).startswith("2")
        ),
        key=lambda value: (len(str(value)), str(value)),
    )
    return ",".join(str(value) for value in statuses)


def expected_responses(operation: dict[str, Any]) -> str:
    return ",".join(
        sorted((str(status) for status in operation.get("responses", {})), key=str)
    )


def param_placeholder(parameter: dict[str, Any], schema: dict[str, Any]) -> str:
    item = effective_schema(parameter.get("schema", {}), schema)
    if parameter.get("in") == "path":
        return "REPLACE_WITH_SYNTHETIC_ID"
    if isinstance(item.get("enum"), list) and item["enum"]:
        return str(item["enum"][0])
    if item.get("type") in {"integer", "number"}:
        return str(sample_value(item, schema))
    if item.get("type") == "boolean":
        return str(sample_value(item, schema)).lower()
    return "REPLACE_WITH_SYNTHETIC_VALUE"


def response_media(operation: dict[str, Any]) -> str | None:
    for response in operation.get("responses", {}).values():
        content = response.get("content", {}) if isinstance(response, dict) else {}
        for media_type in content:
            if media_type == "application/json":
                return media_type
    return None


def render_request(
    seq: int,
    method: str,
    path: str,
    operation_id: str,
    operation: dict[str, Any],
    path_item: dict[str, Any],
    schema: dict[str, Any],
    request_path: str,
    profile_operations: dict[str, dict[tuple[str, str], dict[str, Any]]],
) -> tuple[str, dict[str, Any]]:
    params = get_parameters(path_item, operation, schema)
    path_params = [item for item in params if item.get("in") == "path"]
    query_params = [item for item in params if item.get("in") == "query"]
    header_params = [item for item in params if item.get("in") == "header"]
    cookie_params = [item for item in params if item.get("in") == "cookie"]
    env_vars: dict[str, str] = {}

    request_url = path
    for parameter in path_params:
        name = parameter["name"]
        variable = variable_name(name)
        env_vars.setdefault(variable, "REPLACE_WITH_SYNTHETIC_ID")
        request_url = request_url.replace("{" + name + "}", "{{" + variable + "}}")
    included_query = [p for p in query_params if p.get("required") or "example" in p]
    query_parts: list[str] = []
    for parameter in included_query:
        name = parameter["name"]
        variable = variable_name(name)
        value = param_placeholder(parameter, schema)
        env_vars.setdefault(variable, value)
        query_parts.append(f"{name}={{{{{variable}}}}}")
    if query_parts:
        request_url += "?" + "&".join(query_parts)

    request_body = operation.get("requestBody", {})
    content = request_body.get("content", {}) if isinstance(request_body, dict) else {}
    content_type = next(iter(content), None)
    media_schema = (
        content.get(content_type, {}).get("schema", {}) if content_type else {}
    )
    body_schema = (
        effective_schema(media_schema, schema) if isinstance(media_schema, dict) else {}
    )
    body_json: dict[str, Any] | None = None
    body_multipart: dict[str, tuple[Any, str | None]] | None = None
    if content_type == "application/json":
        body_json = sample_value(body_schema, schema)
        if not isinstance(body_json, dict):
            body_json = {"value": body_json}
        if operation_id == "create_session_v1_sessions_post":
            env_vars.setdefault("request_id", "REPLACE_WITH_SYNTHETIC_ID")
            env_vars.setdefault("idempotency_key", "REPLACE_WITH_SYNTHETIC_ID")
            env_vars.setdefault("session_id", "REPLACE_WITH_SYNTHETIC_UUID4")
            env_vars.setdefault("demo_actor_ref", "REPLACE_WITH_SYNTHETIC_VALUE")
            body_json.update(
                {
                    "request_id": "{{request_id}}",
                    "idempotency_key": "{{idempotency_key}}",
                    "session_id": "{{session_id}}",
                    "actor_ref": "{{demo_actor_ref}}",
                    "payload": {"operation": "CREATE_SESSION"},
                }
            )
    elif content_type == "multipart/form-data":
        body_multipart = {}
        properties = body_schema.get("properties", {})
        required = body_schema.get("required", [])
        for name in required:
            property_schema = properties.get(name)
            if not isinstance(property_schema, dict):
                continue
            if is_binary(property_schema, schema):
                file_hint = "REPLACE_WITH_SYNTHETIC_FILE"
                body_multipart[name] = (file_hint, "application/octet-stream")
            else:
                body_multipart[name] = (sample_value(property_schema, schema), None)

    security = operation.get("security", schema.get("security", []))
    auth_required = bool(security)
    kind, marker, safety = request_kind(method, path, operation)
    summary = re.sub(r"\s+", " ", str(operation.get("summary") or operation_id)).strip()
    summary = summary.replace("{", "[").replace("}", "]")
    request_name = f"{seq:03d} {marker} {summary}"
    body_type = (
        "json"
        if body_json is not None
        else "multipart-form"
        if body_multipart is not None
        else "none"
    )
    lines = [
        "meta {",
        f"  name: {request_name}",
        "  type: http",
        f"  seq: {seq}",
        "}",
        "",
        f"{method.lower()} {{",
        f"  url: {{{{baseUrl}}}}{request_url}",
        f"  body: {body_type}",
        f"  auth: {'bearer' if auth_required else 'none'}",
        "}",
    ]
    if auth_required:
        lines.extend(["", "auth:bearer {", "  token: {{bearerToken}}", "}"])

    headers: list[tuple[str, str]] = []
    media_type = response_media(operation)
    if media_type:
        headers.append(("Accept", media_type))
    if content_type == "application/json":
        headers.append(("Content-Type", "application/json"))
    for parameter in header_params:
        name = parameter["name"]
        if name.lower() == "authorization":
            continue
        value = parameter.get("example")
        if value is None:
            value = param_placeholder(parameter, schema)
        if operation_id == "get_session_v1_sessions__session_id__get":
            header_variables = {
                "x-request-id": "request_id",
                "idempotency-key": "idempotency_key",
                "x-actor-ref": "demo_actor_ref",
            }
            variable = header_variables.get(name.lower())
            if variable is not None:
                env_vars.setdefault(variable, "REPLACE_WITH_SYNTHETIC_ID")
                value = "{{" + variable + "}}"
        headers.append(
            (name, str(value).lower() if isinstance(value, bool) else str(value))
        )
    if cookie_params:
        cookie = "; ".join(
            f"{item['name']}={param_placeholder(item, schema)}"
            for item in cookie_params
        )
        headers.append(("Cookie", cookie))
    if headers:
        lines.extend(["", "headers {"])
        lines.extend(f"  {name}: {value}" for name, value in headers)
        lines.append("}")

    if body_json is not None:
        lines.extend(
            [
                "",
                "body:json {",
                "  "
                + json.dumps(body_json, ensure_ascii=False, indent=2).replace(
                    "\n", "\n  "
                ),
                "}",
            ]
        )
    elif body_multipart is not None:
        lines.extend(["", "body:multipart-form {"])
        for name, (value, file_media) in body_multipart.items():
            if isinstance(value, str) and value == "REPLACE_WITH_SYNTHETIC_FILE":
                lines.append(
                    f"  {name}: @file(./fixtures/{value}) @contentType({file_media})"
                )
            else:
                rendered = (
                    json.dumps(value, ensure_ascii=False)
                    if isinstance(value, (dict, list, bool))
                    else str(value)
                )
                lines.append(f"  {name}: {rendered}")
        lines.append("}")
    lines.append("")
    preconditions = [safety]
    if auth_required:
        preconditions.append(
            "valid local bearer token required; the environment value is a placeholder"
        )
    if path_params:
        preconditions.append(
            "provide real synthetic IDs for: "
            + ", ".join(p["name"] for p in path_params)
        )
    if request_body:
        preconditions.append(
            "replace schema-shaped body placeholders with valid synthetic data"
        )
    if body_multipart:
        preconditions.append(
            "provide a synthetic file matching this endpoint's accepted media and size"
        )
    if operation_id in {
        "create_session_v1_sessions_post",
        "get_session_v1_sessions__session_id__get",
    }:
        preconditions.append(
            "process-local synthetic demo only; use demo_actor_ref=demo:local; "
            "session state resets when the API process exits"
        )

    row = {
        "status": "mounted",
        "operation_id": operation_id,
        "method": method,
        "path": path,
        "tag": "; ".join(operation.get("tags", [])) or tag_folder(operation, path),
        "profiles": "|".join(
            key for key, items in profile_operations.items() if (method, path) in items
        ),
        "mount_mode": mount_mode(path),
        "auth_required": str(auth_required).lower(),
        "request_content_types": ";".join(content),
        "request_body_required": str(bool(request_body.get("required", False))).lower()
        if request_body
        else "false",
        "path_parameters": ";".join(p["name"] for p in path_params),
        "query_parameters": ";".join(p["name"] for p in query_params),
        "required_headers": ";".join(
            p["name"] for p in header_params if p.get("required")
        ),
        "expected_success_statuses": expected_success(operation),
        "expected_response_statuses": expected_responses(operation),
        "side_effect_class": kind,
        "preconditions": " | ".join(preconditions),
        "request_file": request_path.replace("\\", "/"),
        "source_reference": operation_id,
    }
    return "\n".join(lines), row


def mount_mode(path: str) -> str:
    if path.startswith("/api/dev/v1/storage-examples/"):
        return "optional-local-storage-flag"
    if path.startswith(("/v1/story-runs", "/v1/upload-sessions")):
        return "opt-in-main-demo-loopback"
    return "default-mounted"


def slug(value: str) -> str:
    normalized = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
    result = re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()
    return result or "operation"


def remove_examples(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: remove_examples(child)
            for key, child in value.items()
            if key not in {"example", "examples"}
        }
    if isinstance(value, list):
        return [remove_examples(child) for child in value]
    return value


def build_collection(unmounted: Sequence[dict[str, Any]]) -> dict[str, Any]:
    full_schema = build_runtime_schema("combined", story=True, storage=True)
    profile_configs = {
        "combined-default": ("combined", False, False),
        "combined-main-demo-storyrun": ("combined", True, False),
        "combined-local-storage": ("combined", False, True),
        "classroom": ("classroom", False, False),
        "demo": ("demo", False, False),
    }
    profile_operations = {
        key: operations(build_runtime_schema(profile, story=story, storage=storage))
        for key, (profile, story, storage) in profile_configs.items()
    }

    full_operations = operations(full_schema)
    schema_pairs = set(full_operations)
    union_pairs = set().union(*(set(items) for items in profile_operations.values()))
    if schema_pairs != union_pairs:
        missing = sorted(union_pairs - schema_pairs)
        extra = sorted(schema_pairs - union_pairs)
        raise RuntimeError(
            f"profile union does not match full runtime schema; missing={missing}; extra={extra}"
        )

    unmounted_rows = [dict(item) for item in unmounted]
    if len(unmounted_rows) != 11:
        raise RuntimeError(
            f"expected 11 historical unmounted declarations, found {len(unmounted_rows)}"
        )
    if len(full_operations) != 136:
        raise RuntimeError(
            f"expected discovered runtime union of 136 operations, found {len(full_operations)}"
        )

    COLLECTION.mkdir(parents=True, exist_ok=True)

    request_rows: list[dict[str, Any]] = []
    environment: dict[str, str] = {
        "baseUrl": "http://127.0.0.1:8000",
        "bearerToken": "REPLACE_WITH_LOCAL_TEST_BEARER_TOKEN",
        "demo_actor_ref": "REPLACE_WITH_SYNTHETIC_VALUE",
        "idempotency_key": "REPLACE_WITH_SYNTHETIC_ID",
        "request_id": "REPLACE_WITH_SYNTHETIC_ID",
        "session_id": "REPLACE_WITH_SYNTHETIC_UUID4",
    }
    for seq, ((method, path), operation) in enumerate(
        sorted(full_operations.items(), key=lambda item: (item[0][1], item[0][0])),
        start=1,
    ):
        folder = tag_folder(operation, path)
        operation_id = str(operation["operationId"])
        request_file = (
            Path("requests") / folder / f"{seq:03d}-{slug(operation_id)[:58]}.bru"
        )
        request_text, row = render_request(
            seq,
            method,
            path,
            operation_id,
            operation,
            full_schema["paths"][path],
            full_schema,
            str(request_file),
            profile_operations,
        )
        destination = COLLECTION / request_file
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(request_text, encoding="utf-8", newline="\n")
        request_rows.append(row)

        for parameter in get_parameters(
            full_schema["paths"][path], operation, full_schema
        ):
            if parameter.get("in") not in {"path", "query"}:
                continue
            name = variable_name(parameter["name"])
            value = (
                "REPLACE_WITH_SYNTHETIC_ID"
                if parameter.get("in") == "path"
                else "REPLACE_WITH_QUERY_VALUE"
            )
            environment.setdefault(name, value)

    candidate_rows: list[dict[str, Any]] = []
    for index, item in enumerate(unmounted_rows, start=1):
        method = str(item.get("method", "")).upper()
        path = str(item.get("path", ""))
        candidate_rows.append(
            {
                "status": "unmounted-candidate",
                "operation_id": f"candidate-{index:02d}-{slug(method + '-' + path)}",
                "method": method,
                "path": path,
                "tag": "historical unmounted/candidate declaration",
                "profiles": "none",
                "mount_mode": "not-mounted",
                "auth_required": "unknown",
                "request_content_types": "",
                "request_body_required": "unknown",
                "path_parameters": "",
                "query_parameters": "",
                "required_headers": "",
                "expected_success_statuses": "",
                "expected_response_statuses": "",
                "side_effect_class": "not-runnable; no mounted contract",
                "preconditions": (
                    "Not mounted in the current combined/classroom/demo runtime; "
                    "no Bruno request generated."
                ),
                "request_file": "",
                "source_reference": "UNMOUNTED_OPERATIONS",
            }
        )

    coverage_path = OUTPUT / "API_COVERAGE.csv"
    fieldnames = list(request_rows[0])
    with coverage_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(request_rows)
        writer.writerows(candidate_rows)

    safe_schema = remove_examples(full_schema)
    (OUTPUT / "openapi.runtime.json").write_text(
        json.dumps(safe_schema, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (COLLECTION / "bruno.json").write_text(
        json.dumps(
            {
                "version": "1",
                "name": "Sketch2Life full BE runtime API (local/test)",
                "type": "collection",
                "ignore": ["node_modules", ".git"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    env_path = COLLECTION / "environments" / "local.bru"
    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_lines = [
        "vars {",
        *[f"  {key}: {value}" for key, value in sorted(environment.items())],
        "}",
        "",
    ]
    env_path.write_text("\n".join(env_lines), encoding="utf-8", newline="\n")

    return {
        "full_schema": full_schema,
        "full_operations": full_operations,
        "requests": request_rows,
        "candidates": candidate_rows,
        "profile_counts": {
            name: len(items) for name, items in profile_operations.items()
        },
    }


def main() -> None:
    from sketch2life.interfaces.http.openapi_contract import UNMOUNTED_OPERATIONS

    result = build_collection(UNMOUNTED_OPERATIONS)
    print(
        json.dumps(
            {
                "runtime_operations": len(result["requests"]),
                "paths": len(result["full_schema"].get("paths", {})),
                "unmounted_candidates": len(result["candidates"]),
                "profile_counts": result["profile_counts"],
                "coverage_csv": str(OUTPUT / "API_COVERAGE.csv"),
                "collection": str(COLLECTION),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    sys.path.insert(0, str(BACKEND_SRC))
    main()
