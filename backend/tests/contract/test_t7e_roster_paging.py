"""FEAT-066 T-7e (D-066-100): the Teacher class roster is paged and carries a count (offline).

No database is reached: the app is built against a sentinel URL and only its OpenAPI and its
route table are read. The behaviour on PostgreSQL lives in
``tests/integration/test_t7e_roster_paging_postgres.py``.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest

from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.openapi_contract import MOUNTED_OPERATIONS
from sketch2life.interfaces.http.openapi_contract_amendments import (
    ALTERNATE_RESPONSE_EXAMPLES,
    SYNTHETIC_RESPONSE_EXAMPLES,
)

DATABASE_SENTINEL = "postgresql+psycopg://sentinel_user:sentinel_pw@localhost:9/sentinel_db"
ROSTER = (
    "get",
    "/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles",
)


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


def test_catalog_lists_limit_and_cursor_and_the_same_handler() -> None:
    contract = MOUNTED_OPERATIONS[ROSTER]
    assert contract["handler"] == "be1_registry.py::list_profiles"
    assert "query `limit`: integer" in contract["request_inputs"]
    assert "query `cursor`: string" in contract["request_inputs"]


def test_teacher_example_has_the_new_fields_and_the_manager_example_is_unchanged() -> None:
    teacher = SYNTHETIC_RESPONSE_EXAMPLES[ROSTER]
    assert teacher["contract"] == "Be1ManagedProfileListV1"
    assert set(teacher) == {"contract", "items", "next_cursor", "active_profile_count"}
    assert teacher["next_cursor"] is None
    assert teacher["active_profile_count"] == 1
    # The item fields are unchanged: the roster adds fields, it never adds a child field.
    assert set(teacher["items"][0]) == {"child_id", "class_id", "display_name", "age_months"}
    ((_name, manager),) = ALTERNATE_RESPONSE_EXAMPLES[ROSTER]
    assert set(manager) == {"contract", "class_id", "active_profile_count"}


def test_published_roster_has_limit_cursor_and_both_bodies(published: dict[str, Any]) -> None:
    operation = published["paths"][ROSTER[1]][ROSTER[0]]
    names = {parameter["name"]: parameter for parameter in operation["parameters"]}
    assert names["limit"]["in"] == "query"
    assert names["limit"]["schema"]["default"] == 25
    assert names["limit"]["schema"]["minimum"] == 1
    assert names["limit"]["schema"]["maximum"] == 100
    assert names["cursor"]["in"] == "query" and not names["cursor"].get("required")
    assert "400" in operation["responses"]
    media = operation["responses"]["200"]["content"]["application/json"]
    teacher, manager = media["schema"]["oneOf"]
    assert teacher["properties"]["contract"]["enum"] == ["Be1ManagedProfileListV1"]
    assert teacher["properties"]["next_cursor"]["type"] == ["string", "null"]
    assert teacher["properties"]["active_profile_count"]["type"] == "integer"
    assert {"next_cursor", "active_profile_count"} <= set(teacher["required"])
    assert manager["properties"]["contract"]["enum"] == ["Be1ClassRosterSummaryV1"]
    assert set(manager["properties"]) == {"contract", "class_id", "active_profile_count"}
    assert "next_cursor" not in manager["properties"]


def test_no_new_path_or_operation_for_the_roster(published: dict[str, Any]) -> None:
    roster_paths = [
        path for path in published["paths"] if path.endswith("/classes/{class_id}/profiles")
    ]
    assert roster_paths == [ROSTER[1]]
    assert sorted(published["paths"][ROSTER[1]]) == ["get", "post"]
