"""FEAT-066 T-7b: class suspend and archive commands and the list state filter (offline).

No database is reached: the app is built against a sentinel URL and only its OpenAPI, its route
table and the 401 of the bearer dependency are read. The behaviour on PostgreSQL lives in
``tests/integration/test_t7b_class_state_postgres.py``.
"""

from __future__ import annotations

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

DATABASE_SENTINEL = "postgresql+psycopg://sentinel_user:sentinel_pw@localhost:9/sentinel_db"
SUSPEND = ("post", "/api/be1/v1/classes/{class_id}/suspend")
ARCHIVE = ("post", "/api/be1/v1/classes/{class_id}/archive")
LIST = ("get", "/api/be1/v1/organizations/{organization_id}/classes")


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


def test_catalog_declares_both_commands_as_keyed_and_in_the_fe_projection() -> None:
    for key in (SUSPEND, ARCHIVE):
        assert key in MOUNTED_OPERATIONS
        assert key in IDEMPOTENCY_MISMATCH_OPERATION_KEYS
        assert key in SRS_V22_INCLUDED_OPERATIONS
        assert key in SYNTHETIC_RESPONSE_EXAMPLES
        assert "capacity" not in str(MOUNTED_OPERATIONS[key]["purpose"]).lower()
    assert MOUNTED_OPERATIONS[SUSPEND]["handler"] == "be1_registry.py::suspend_class"
    assert MOUNTED_OPERATIONS[ARCHIVE]["handler"] == "be1_registry.py::archive_class"
    assert SYNTHETIC_RESPONSE_EXAMPLES[SUSPEND]["contract"] == "Be1ClassStateV1"
    assert SYNTHETIC_RESPONSE_EXAMPLES[ARCHIVE]["state"] == "archived"


def test_published_commands_have_the_key_the_revision_and_no_body(
    published: dict[str, Any],
) -> None:
    for _method, path in (SUSPEND, ARCHIVE):
        operation = published["paths"][path]["post"]
        assert "requestBody" not in operation
        parameters = {
            (item["in"], item["name"]): bool(item.get("required"))
            for item in operation["parameters"]
        }
        assert parameters[("path", "class_id")] is True
        assert parameters[("header", "Idempotency-Key")] is True
        assert ("header", "If-Match") in parameters
        assert "200" in operation["responses"]


def test_published_list_has_the_state_filter_with_the_default_active(
    published: dict[str, Any],
) -> None:
    operation = published["paths"][LIST[1]]["get"]
    state = next(item for item in operation["parameters"] if item["name"] == "state")
    assert state["in"] == "query" and state.get("required") is not True
    schema = state["schema"]
    assert schema["default"] == "active"
    assert schema["enum"] == ["active", "suspended", "archived", "all"]
    assert SYNTHETIC_RESPONSE_EXAMPLES[LIST]["items"][0]["class_revision"] == 1


def test_route_table_has_the_two_commands_and_no_way_back(published: dict[str, Any]) -> None:
    posts = {path for path, item in published["paths"].items() if "post" in item}
    assert "/api/be1/v1/classes/{class_id}/suspend" in posts
    assert "/api/be1/v1/classes/{class_id}/archive" in posts
    words = ("reactivate", "unarchive", "activate", "restore", "unsuspend", "resume")
    class_paths = [path for path in published["paths"] if path.startswith("/api/be1/v1/classes/")]
    assert sorted(class_paths) == [
        "/api/be1/v1/classes/{class_id}/archive",
        "/api/be1/v1/classes/{class_id}/assignments",
        # FEAT-066 T-7d: the Teacher enrollment move (a roster command, not a state command).
        "/api/be1/v1/classes/{class_id}/profiles/{child_id}/move",
        "/api/be1/v1/classes/{class_id}/suspend",
    ]
    assert all(not any(word in path for word in words) for path in class_paths)


@pytest.mark.parametrize("command", ["suspend", "archive"])
def test_commands_require_a_bearer_token(command: str) -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.post(
            f"/api/be1/v1/classes/class-a/{command}",
            headers={"Idempotency-Key": "key-1", "If-Match": '"1"'},
        )
    assert response.status_code == 401
