"""FEAT-066 T-7c: the Teacher profile create contract (offline).

No database is reached: the app is built against a sentinel URL and only its OpenAPI, its route
table, the handler signature and the 401 of the bearer dependency are read. The behaviour on
PostgreSQL lives in ``tests/integration/test_t7c_profile_create_postgres.py``.
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
from sketch2life.interfaces.http.routers import be1_registry

DATABASE_SENTINEL = "postgresql+psycopg://sentinel_user:sentinel_pw@localhost:9/sentinel_db"
PATH = "/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles"
CREATE = ("post", PATH)


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


def test_the_catalog_row_is_keyed_and_carries_the_expected_class_revision() -> None:
    contract = MOUNTED_OPERATIONS[CREATE]
    assert CREATE in IDEMPOTENCY_MISMATCH_OPERATION_KEYS
    assert contract["handler"] == "be1_registry.py::create_profile"
    inputs = str(contract["request_inputs"])
    assert "`Idempotency-Key*`" in inputs and "`If-Match`" in inputs
    assert "class_id*:string" not in inputs and "CreateProfileRequest {" in inputs
    assert "consent_id:string" in inputs
    statuses = {row["status"] for row in contract["responses"]}
    assert {"201", "400", "403", "404", "409"} <= statuses
    for banned in ("capacity", "quota", "billing", "subscription", "payment"):
        assert banned not in str(contract["purpose"]).lower()


def test_the_example_is_the_new_201_body() -> None:
    example = SYNTHETIC_RESPONSE_EXAMPLES[CREATE]
    assert set(example) == {
        "contract",
        "child_id",
        "class_id",
        "enrollment_id",
        "display_name",
        "age_months",
        "data_origin",
        "class_revision",
    }
    assert example["data_origin"] == "SYNTHETIC_DEV"
    assert example["display_name"].startswith("Synthetic ")


def test_published_operation_has_the_headers_and_a_class_less_body(
    published: dict[str, Any],
) -> None:
    operation = published["paths"][PATH]["post"]
    parameters = {
        (item["in"], item["name"]): bool(item.get("required")) for item in operation["parameters"]
    }
    assert parameters[("path", "organization_id")] is True
    assert parameters[("path", "class_id")] is True
    assert parameters[("header", "Idempotency-Key")] is True
    assert ("header", "If-Match") in parameters
    body = operation["requestBody"]["content"]["application/json"]["schema"]
    name = body["$ref"].rsplit("/", 1)[-1]
    schema = published["components"]["schemas"][name]
    assert set(schema["properties"]) == {"display_name", "age_months", "consent_id"}
    assert set(schema["required"]) == {"display_name", "age_months"}
    assert schema["additionalProperties"] is False
    assert "201" in operation["responses"]


def test_the_route_table_has_no_second_create_route(
    published: dict[str, Any],
) -> None:
    posts = {path for path, item in published["paths"].items() if "post" in item}
    profile_posts = {
        path for path in posts if path.startswith("/api/be1/") and path.endswith("/profiles")
    }
    assert profile_posts == {PATH}
    assert "/api/be1/v1/classes/{class_id}/profiles" not in published["paths"]


def test_the_handler_declares_the_key_if_match_and_no_body_class_id() -> None:
    signature = inspect.signature(be1_registry.create_profile)
    assert list(signature.parameters)[:7] == [
        "organization_id",
        "class_id",
        "payload",
        "request",
        "response",
        "idempotency_key",
        "if_match",
    ]


def test_the_settings_gate_is_off_by_default() -> None:
    assert Settings.model_fields["real_profile_data_enabled"].default is False


def test_the_catalog_names_the_rate_limit_and_the_unavailable_key_answers() -> None:
    # T-7c-fix (O-1, O-2): 429 with Retry-After on the real-data gate, 503 without the secret.
    contract = MOUNTED_OPERATIONS[CREATE]
    purpose = str(contract["purpose"])
    assert "429 `RATE_LIMITED`" in purpose and "`Retry-After`" in purpose
    assert "not SRS values" in purpose and "503 `PROVIDER_UNAVAILABLE`" in purpose
    statuses = {row["status"] for row in contract["responses"]}
    assert {"429", "503"} <= statuses
    assert "T-7c-fix" in str(contract["verification"])


def test_the_receipt_key_and_gate_limit_settings_exist_with_their_defaults() -> None:
    fields = Settings.model_fields
    assert fields["profile_receipt_hmac_key"].default is None
    assert fields["profile_gate_account_limit"].default == 5
    assert fields["profile_gate_ip_limit"].default == 20
    assert fields["profile_gate_window_seconds"].default == 60


def test_the_route_requires_a_bearer_token() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.post(
            "/api/be1/v1/organizations/org-a/classes/class-a/profiles",
            json={"display_name": "Synthetic Learner", "age_months": 60},
            headers={"Idempotency-Key": "key-1", "If-Match": '"1"'},
        )
    assert response.status_code == 401
