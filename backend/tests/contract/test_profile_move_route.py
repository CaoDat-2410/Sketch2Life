"""FEAT-066 T-7d: the Teacher enrollment move contract (offline).

No database is reached: the app is built against a sentinel URL and only its OpenAPI, its route
table, the handler signature and the 401 of the bearer dependency are read. The behaviour on
PostgreSQL lives in ``tests/integration/test_t7d_profile_move_postgres.py``.
"""

from __future__ import annotations

import inspect
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
    IDEMPOTENCY_MISMATCH_OPERATION_KEYS,
    MOUNTED_OPERATIONS,
)
from sketch2life.interfaces.http.openapi_contract_amendments import SYNTHETIC_RESPONSE_EXAMPLES
from sketch2life.interfaces.http.openapi_srs_v22 import SRS_V22_INCLUDED_OPERATIONS
from sketch2life.interfaces.http.routers import be1_registry

DATABASE_SENTINEL = "postgresql+psycopg://sentinel_user:sentinel_pw@localhost:9/sentinel_db"
PATH = "/api/be1/v1/classes/{class_id}/profiles/{child_id}/move"
MOVE = ("post", PATH)


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
def published() -> Iterator[dict[str, Any]]:
    app = create_app()
    app.openapi()
    yield app.state.runtime_openapi_schema


def test_the_catalog_row_is_keyed_and_names_both_revisions() -> None:
    contract = MOUNTED_OPERATIONS[MOVE]
    assert MOVE in IDEMPOTENCY_MISMATCH_OPERATION_KEYS
    assert MOVE in SRS_V22_INCLUDED_OPERATIONS
    assert contract["handler"] == "be1_registry.py::move_profile"
    inputs = str(contract["request_inputs"])
    assert "`Idempotency-Key*`" in inputs and "`If-Match`" in inputs
    assert "path `child_id*`" in inputs
    assert "MoveProfileRequest {target_class_id*:string, target_class_revision*:integer}" in inputs
    statuses = {row["status"] for row in contract["responses"]}
    assert {"400", "403", "404", "409"} <= statuses
    purpose = str(contract["purpose"])
    for needed in ("STALE_REVISION", "INVALID_STATE_TRANSITION", "403", "uniform 404"):
        assert needed in purpose
    # Owner scope rule: no capacity, quota, billing, subscription or payment wording.
    for banned in ("capacity", "quota", "billing", "subscription", "payment"):
        assert banned not in purpose.lower().replace("no capacity, quota or billing", "")


def test_the_example_holds_references_and_revisions_only() -> None:
    example = SYNTHETIC_RESPONSE_EXAMPLES[MOVE]
    assert set(example) == {
        "contract",
        "child_id",
        "from_class_id",
        "to_class_id",
        "enrollment_id",
        "from_class_revision",
        "to_class_revision",
    }
    assert example["contract"] == "Be1ProfileMoveV1"


def test_published_operation_has_the_headers_and_the_two_revisions(
    published: dict[str, Any],
) -> None:
    operation = published["paths"][PATH]["post"]
    parameters = {
        (item["in"], item["name"]): bool(item.get("required")) for item in operation["parameters"]
    }
    assert parameters[("path", "class_id")] is True
    assert parameters[("path", "child_id")] is True
    assert parameters[("header", "Idempotency-Key")] is True
    assert ("header", "If-Match") in parameters
    body = operation["requestBody"]["content"]["application/json"]["schema"]
    schema = published["components"]["schemas"][body["$ref"].rsplit("/", 1)[-1]]
    assert set(schema["properties"]) == {"target_class_id", "target_class_revision"}
    assert set(schema["required"]) == {"target_class_id", "target_class_revision"}
    assert schema["additionalProperties"] is False
    assert schema["properties"]["target_class_revision"]["minimum"] == 1
    assert "200" in operation["responses"]


def test_the_route_table_has_one_move_route_and_no_bulk_or_manager_variant(
    published: dict[str, Any],
) -> None:
    move_paths = {path for path in published["paths"] if path.endswith("/move")}
    assert move_paths == {PATH}
    assert set(published["paths"][PATH]) == {"post"}


def test_the_handler_declares_the_key_and_if_match_after_the_body() -> None:
    signature = inspect.signature(be1_registry.move_profile)
    assert list(signature.parameters) == [
        "class_id",
        "child_id",
        "payload",
        "request",
        "idempotency_key",
        "if_match",
        "principal",
        "db",
    ]


def test_the_route_requires_a_bearer_token() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.post(
            "/api/be1/v1/classes/class-a/profiles/child-a/move",
            json={"target_class_id": "class-b", "target_class_revision": 1},
            headers={"Idempotency-Key": "key-1", "If-Match": '"1"'},
        )
    assert response.status_code == 401
