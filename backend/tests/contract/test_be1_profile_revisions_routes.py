"""FEAT-066 goal v4 T-12b: the Teacher profile revision contract (offline).

No database is reached: the app is built against a sentinel URL and only its OpenAPI, its route
table and the 401 of the bearer dependency are read. The behaviour on PostgreSQL lives in
``tests/integration/test_be1_profile_revisions_postgres.py``.
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

DATABASE_SENTINEL = "postgresql+psycopg://sentinel_user:sentinel_pw@localhost:9/sentinel_db"
BASE = "/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles/{child_id}"
HISTORY = ("get", f"{BASE}/revisions")
ONE = ("get", f"{BASE}/revisions/{{profile_revision_id}}")
EDIT = ("patch", BASE)


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


def _operation(published: dict[str, Any], key: tuple[str, str]) -> dict[str, Any]:
    method, path = key
    return published["paths"][path][method]  # type: ignore[no-any-return]


def test_the_three_operations_are_catalogued_with_their_handlers() -> None:
    assert {key: MOUNTED_OPERATIONS[key]["handler"] for key in (HISTORY, ONE, EDIT)} == {
        HISTORY: "be1_registry.py::list_profile_revisions",
        ONE: "be1_registry.py::get_profile_revision",
        EDIT: "be1_registry.py::edit_profile",
    }
    assert EDIT in IDEMPOTENCY_MISMATCH_OPERATION_KEYS
    assert HISTORY not in IDEMPOTENCY_MISMATCH_OPERATION_KEYS and ONE not in (
        IDEMPOTENCY_MISMATCH_OPERATION_KEYS
    )
    for key in (HISTORY, ONE, EDIT):
        text = str(MOUNTED_OPERATIONS[key]["purpose"])
        for banned in ("capacity", "quota", "billing", "subscription", "payment"):
            assert banned not in text.lower()
        assert MOUNTED_OPERATIONS[key]["tag"] == "BE1 — Organizations & Classes"


def test_the_edit_publishes_a_strict_body_and_a_required_key(published: dict[str, Any]) -> None:
    operation = _operation(published, EDIT)
    body = operation["requestBody"]["content"]["application/json"]["schema"]
    name = body["$ref"].rsplit("/", 1)[-1]
    schema = published["components"]["schemas"][name]
    assert name == "EditProfileRequest"
    assert set(schema["properties"]) == {
        "expected_revision",
        "display_name",
        "age_months",
        "structured_interests",
    }
    assert schema["required"] == ["expected_revision"]
    assert schema["additionalProperties"] is False
    key = next(
        p for p in operation["parameters"] if p["in"] == "header" and p["name"] == "Idempotency-Key"
    )
    assert key["required"] is True and key["schema"]["maxLength"] == 128
    assert "200" in operation["responses"]


def test_the_history_publishes_the_shared_page_limit(published: dict[str, Any]) -> None:
    limit = next(
        p
        for p in _operation(published, HISTORY)["parameters"]
        if p["in"] == "query" and p["name"] == "limit"
    )
    assert limit["schema"]["default"] == 25
    assert limit["schema"]["minimum"] == 1 and limit["schema"]["maximum"] == 100


def test_the_response_models_hold_no_author_and_no_secret(published: dict[str, Any]) -> None:
    schemas = published["components"]["schemas"]
    assert set(schemas["Be1ProfileRevisionV1"]["properties"]) == {
        "contract",
        "child_id",
        "profile_revision_id",
        "revision_no",
        "display_name",
        "age_months",
        "age_band",
        "structured_interests",
        "revision_hash",
        "created_at",
    }
    assert set(schemas["Be1ProfileEditResultV1"]["properties"]) == {
        "contract",
        "child_id",
        "profile_revision_id",
        "revision_no",
        "revision_hash",
    }
    assert set(schemas["Be1ProfileRevisionPageV1"]["properties"]) == {
        "contract",
        "items",
        "next_cursor",
    }
    for name in ("Be1ProfileRevisionV1", "Be1ProfileEditResultV1"):
        assert "authored_by" not in schemas[name]["properties"]


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/be1/v1/organizations/o/classes/c/profiles/k/revisions"),
        ("get", "/api/be1/v1/organizations/o/classes/c/profiles/k/revisions/r"),
        ("patch", "/api/be1/v1/organizations/o/classes/c/profiles/k"),
    ],
)
def test_the_routes_need_a_bearer_credential(method: str, path: str) -> None:
    with TestClient(create_app(), raise_server_exceptions=False) as client:
        response = client.request(method, path, json={"expected_revision": 1, "age_months": 60})
    assert response.status_code == 401


_SUPPORT_NEEDS = f"{BASE}/support-needs"
_TEACHER_409_OPERATIONS = (
    HISTORY,
    ONE,
    EDIT,
    ("get", _SUPPORT_NEEDS),
    ("put", _SUPPORT_NEEDS),
)


@pytest.mark.parametrize("key", _TEACHER_409_OPERATIONS)
def test_the_409_row_names_the_consent_code_and_the_purpose_says_when_404_replaces_it(
    key: tuple[str, str],
) -> None:
    """V4-B T-12b-fix (owner decision Q3): 409 only for an assigned Teacher; 404 when withdrawn."""
    rows = {row["status"]: row for row in MOUNTED_OPERATIONS[key]["responses"]}
    assert "CONSENT_NOT_EFFECTIVE" in rows["409"]["description"]
    assert "pending deletion" in rows["409"]["description"]
    purpose = str(MOUNTED_OPERATIONS[key]["purpose"])
    assert "CONSENT_NOT_EFFECTIVE" in purpose
    assert "pending deletion" in purpose and "revoked" in purpose


def test_the_support_needs_teacher_purpose_orders_permission_before_consent() -> None:
    for method in ("get", "put"):
        purpose = str(MOUNTED_OPERATIONS[(method, _SUPPORT_NEEDS)]["purpose"])
        assert "without the permission is the uniform 404" in purpose
        assert "no audit row is written" in purpose


def test_the_edit_documents_the_diagnosis_like_field_code() -> None:
    assert "DIAGNOSIS_LIKE" in str(MOUNTED_OPERATIONS[EDIT]["purpose"])
