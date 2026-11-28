"""Pure tests for the OpenAPI catalog mapper and for the catalog's source declarations."""

from __future__ import annotations

import ast
import copy
from pathlib import Path
from typing import Any

import pytest

from sketch2life.interfaces.http import openapi_contract
from sketch2life.interfaces.http.app import _apply_catalog_metadata
from sketch2life.interfaces.http.openapi_contract import MOUNTED_OPERATIONS
from sketch2life.interfaces.http.openapi_contract_amendments import (
    public_tag_name,
    published_responses,
)

CATALOG_NAME = "MOUNTED_OPERATIONS"
MUTATING_ATTRIBUTES = {
    "update",
    "setdefault",
    "pop",
    "popitem",
    "clear",
    "__setitem__",
    "__delitem__",
}
KEY = ("get", "/synthetic/items/{item_id}")
NEIGHBOR_PATH = "/synthetic/items/{item_id}/children"
CONTRACT: dict[str, Any] = {
    "purpose": "Read one synthetic item.",
    "tag": "Synthetic Items",
    "responses": (
        {
            "status": "200",
            "description": "The synthetic item",
            "media_type": "application/json",
            "schema_name": "object",
        },
        {
            "status": "404",
            "description": "The synthetic item was not found",
            "media_type": "application/json",
            "schema_name": "object",
        },
    ),
}


def _operation(operation_id: str) -> dict[str, Any]:
    return {
        "operationId": operation_id,
        "summary": "Generated summary",
        "description": "Generated description",
        "tags": ["Generated"],
        "security": [{"HTTPBearer": []}],
        "parameters": [{"name": "item_id", "in": "path", "required": True}],
        "requestBody": {"content": {"application/json": {"schema": {"type": "object"}}}},
        "responses": {"200": {"description": "Generated response"}},
    }


def _schema() -> dict[str, Any]:
    return {
        "openapi": "3.1.0",
        "info": {"title": "synthetic", "version": "0"},
        "paths": {
            KEY[1]: {
                "summary": "Path-level summary",
                "parameters": [{"name": "item_id", "in": "path", "required": True}],
                "get": _operation("read_item"),
                "post": _operation("write_item"),
            },
            NEIGHBOR_PATH: {"get": _operation("list_children")},
        },
        "components": {"schemas": {}},
    }


def _declared_catalog_keys(source: str, name: str = CATALOG_NAME) -> list[tuple[str, str]]:
    """Return every literal key declared for ``name``, in source order, or fail closed."""

    def literal_key(node: ast.expr | None) -> tuple[str, str]:
        if (
            isinstance(node, ast.Tuple)
            and len(node.elts) == 2
            and all(
                isinstance(element, ast.Constant) and isinstance(element.value, str)
                for element in node.elts
            )
        ):
            first, second = node.elts
            assert isinstance(first, ast.Constant) and isinstance(second, ast.Constant)
            return (first.value, second.value)
        raise ValueError("catalog key is not a literal (method, path) tuple")

    keys: list[tuple[str, str]] = []
    declared = False
    for statement in ast.parse(source).body:
        target: ast.expr | None = None
        value: ast.expr | None = None
        if isinstance(statement, ast.AnnAssign):
            target, value = statement.target, statement.value
        elif isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            target, value = statement.targets[0], statement.value
        if isinstance(target, ast.Name) and target.id == name:
            if declared or not isinstance(value, ast.Dict):
                raise ValueError("catalog must be declared once as a dictionary literal")
            declared = True
            keys.extend(literal_key(key) for key in value.keys)
            continue
        if (
            isinstance(statement, ast.Assign)
            and isinstance(target, ast.Subscript)
            and isinstance(target.value, ast.Name)
            and target.value.id == name
        ):
            if not declared:
                raise ValueError("catalog entry is assigned before the catalog is declared")
            keys.append(literal_key(target.slice))
            continue
        for node in ast.walk(statement):
            rebinds = isinstance(node, ast.Name) and node.id == name
            if rebinds and not isinstance(node.ctx, ast.Load):
                raise ValueError("unsupported catalog rebinding or deletion")
            if (
                isinstance(node, ast.Subscript)
                and isinstance(node.value, ast.Name)
                and node.value.id == name
                and not isinstance(node.ctx, ast.Load)
            ):
                raise ValueError("unsupported catalog item mutation")
            if (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == name
                and node.attr in MUTATING_ATTRIBUTES
            ):
                raise ValueError("unsupported catalog mutation call")
    if not declared:
        raise ValueError("catalog declaration was not found")
    return keys


def _key_differences(
    runtime_keys: set[tuple[str, str]],
    catalog_keys: set[tuple[str, str]],
    runtime_only_keys: set[tuple[str, str]],
) -> dict[str, set[tuple[str, str]]]:
    return {
        "missing_from_runtime": catalog_keys - runtime_keys,
        "unexpected_in_runtime": runtime_keys - catalog_keys - runtime_only_keys,
        "stale_runtime_only": runtime_only_keys - runtime_keys,
        "runtime_only_in_catalog": runtime_only_keys & catalog_keys,
    }


def test_exact_key_receives_catalog_metadata_and_keeps_unrelated_fields() -> None:
    schema = _schema()
    before = copy.deepcopy(schema["paths"][KEY[1]]["get"])

    _apply_catalog_metadata(schema, {KEY: CONTRACT})

    operation = schema["paths"][KEY[1]]["get"]
    declared = {row["status"]: row for row in published_responses(KEY, CONTRACT["responses"])}
    assert operation["description"] == CONTRACT["purpose"]
    assert operation["tags"] == [public_tag_name(CONTRACT["tag"])]
    assert set(operation["responses"]) == set(before["responses"]) | set(declared)
    for status, row in declared.items():
        assert operation["responses"][status]["description"] == row["description"]
    for field in ("operationId", "summary", "security", "parameters", "requestBody"):
        assert operation[field] == before[field]


def test_a_lifecycle_union_response_keeps_both_envelopes_after_mapping() -> None:
    """FR-C-08 (Contract Draft 11 §3.3): the catalog sets the description of the Parent GET
    and replay responses and keeps the union of the run envelope and the lifecycle envelope."""
    key = ("get", "/v1/story-runs/{run_id}")
    union = {
        "anyOf": [
            {"$ref": "#/components/schemas/ParentStoryRunEnvelopeV1"},
            {"$ref": "#/components/schemas/ParentStoryRunLifecycleEnvelopeV1"},
        ]
    }
    schema = {
        "openapi": "3.1.0",
        "info": {"title": "synthetic", "version": "0"},
        "paths": {
            key[1]: {
                "get": {
                    "operationId": "get_run",
                    "responses": {
                        "200": {
                            "description": "Generated",
                            "content": {"application/json": {"schema": copy.deepcopy(union)}},
                        }
                    },
                }
            }
        },
        "components": {
            "schemas": {
                "ParentStoryRunEnvelopeV1": {"type": "object"},
                "ParentStoryRunLifecycleEnvelopeV1": {"type": "object"},
            }
        },
    }
    contract = {
        "purpose": "Read one Parent StoryRun owned by the verified principal.",
        "tag": "Parent StoryRuns",
        "responses": (
            {
                "status": "200",
                "description": (
                    "StoryRun resource, including the selected AI_DRAFT activity with a "
                    "null activity reference, or the lifecycle projection from "
                    "DELETE_PENDING on"
                ),
                "media_type": "application/json",
                "schema_name": "ParentStoryRunEnvelopeV1",
            },
        ),
    }
    _apply_catalog_metadata(schema, {key: contract})
    response = schema["paths"][key[1]]["get"]["responses"]["200"]
    assert response["description"] == contract["responses"][0]["description"]
    assert response["content"]["application/json"]["schema"] == union
    catalogued = MOUNTED_OPERATIONS[key]["responses"][0]
    assert catalogued["description"] == contract["responses"][0]["description"]


def test_metadata_is_not_applied_to_neighbouring_keys() -> None:
    schema = _schema()
    before = copy.deepcopy(schema)

    _apply_catalog_metadata(schema, {KEY: CONTRACT})

    path_item = schema["paths"][KEY[1]]
    assert path_item["post"] == before["paths"][KEY[1]]["post"]
    assert path_item["summary"] == before["paths"][KEY[1]]["summary"]
    assert path_item["parameters"] == before["paths"][KEY[1]]["parameters"]
    assert schema["paths"][NEIGHBOR_PATH] == before["paths"][NEIGHBOR_PATH]
    assert schema["components"] == before["components"]
    assert schema["info"] == before["info"]


def test_uncatalogued_operations_are_left_unchanged() -> None:
    schema = _schema()
    before = copy.deepcopy(schema)

    _apply_catalog_metadata(schema, {})

    assert schema == before


def test_stale_catalog_key_does_not_create_or_change_operations() -> None:
    schema = _schema()
    before = copy.deepcopy(schema)

    _apply_catalog_metadata(schema, {("delete", "/synthetic/not-mounted"): CONTRACT})

    assert schema == before


def test_lookup_requires_the_exact_method_and_path() -> None:
    schema = _schema()
    before = copy.deepcopy(schema)
    near_misses = {
        ("post", NEIGHBOR_PATH): CONTRACT,
        ("get", KEY[1] + "/"): CONTRACT,
        ("GET", KEY[1]): CONTRACT,
        ("get", KEY[1].upper()): CONTRACT,
    }

    _apply_catalog_metadata(schema, near_misses)

    assert schema == before


def test_key_differences_name_missing_unexpected_and_stale_keys() -> None:
    catalog = {("get", "/a"), ("post", "/a"), ("get", "/b")}
    runtime_only = {("get", "/pilot"), ("get", "/gone")}
    runtime = {("get", "/a"), ("post", "/a"), ("get", "/pilot"), ("get", "/extra")}

    assert _key_differences(runtime, catalog, runtime_only) == {
        "missing_from_runtime": {("get", "/b")},
        "unexpected_in_runtime": {("get", "/extra")},
        "stale_runtime_only": {("get", "/gone")},
        "runtime_only_in_catalog": set(),
    }
    assert _key_differences(catalog | {("get", "/pilot")}, catalog, {("get", "/pilot")}) == {
        "missing_from_runtime": set(),
        "unexpected_in_runtime": set(),
        "stale_runtime_only": set(),
        "runtime_only_in_catalog": set(),
    }


def test_declaration_audit_reports_duplicate_literal_keys() -> None:
    source = (
        "MOUNTED_OPERATIONS = {('get', '/a'): 1, ('get', '/a'): 2, ('post', '/a'): 3}\n"
        "MOUNTED_OPERATIONS[('post', '/a')] = 4\n"
        "MOUNTED_OPERATIONS[('get', '/b')] = 5\n"
    )

    keys = _declared_catalog_keys(source)

    assert keys == [("get", "/a"), ("get", "/a"), ("post", "/a"), ("post", "/a"), ("get", "/b")]
    assert sorted({key for key in keys if keys.count(key) > 1}) == [("get", "/a"), ("post", "/a")]


@pytest.mark.parametrize(
    "source",
    [
        "KEY = ('get', '/a')\nMOUNTED_OPERATIONS = {KEY: 1}\n",
        "MOUNTED_OPERATIONS = {('get', '/a'): 1}\nMOUNTED_OPERATIONS[KEY] = 2\n",
        "MOUNTED_OPERATIONS = {('get', '/a'): 1}\nMOUNTED_OPERATIONS.update({('get', '/b'): 2})\n",
        "MOUNTED_OPERATIONS = {('get', '/a'): 1}\ndel MOUNTED_OPERATIONS[('get', '/a')]\n",
        "MOUNTED_OPERATIONS = {('get', '/a'): 1}\nMOUNTED_OPERATIONS = {('get', '/b'): 2}\n",
        "MOUNTED_OPERATIONS = dict(a=1)\n",
        "MOUNTED_OPERATIONS = {**OTHER}\n",
        "MOUNTED_OPERATIONS = {('get', '/a', 'x'): 1}\n",
        "OTHER = {('get', '/a'): 1}\n",
    ],
)
def test_declaration_audit_fails_closed_on_unrecognized_forms(source: str) -> None:
    with pytest.raises(ValueError):
        _declared_catalog_keys(source)


def test_catalog_source_declares_every_key_exactly_once() -> None:
    source_path = Path(openapi_contract.__file__)
    declared = _declared_catalog_keys(source_path.read_text(encoding="utf-8"))

    assert len(declared) == len(set(declared))
    assert set(declared) == set(MOUNTED_OPERATIONS)
    assert len(declared) == len(MOUNTED_OPERATIONS)
    assert all(method == method.lower() and path.startswith("/") for method, path in declared)
