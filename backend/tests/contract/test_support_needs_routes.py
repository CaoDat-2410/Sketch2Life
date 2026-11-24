"""FEAT-066 goal v4 T-12c: the encrypted support-needs routes (offline).

The Parent routes run on service doubles, so ownership, role, key-source and error shapes are
checked without a database. The Teacher routes are checked through the published contract and the
bearer boundary here; their authorization, consent, permission and write behaviour is on
PostgreSQL in ``tests/integration/test_support_needs_postgres.py``. No value is ever echoed in an
error and no answer is cacheable.
"""

from __future__ import annotations

from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

import sketch2life.interfaces.http.app as app_module
import sketch2life.interfaces.http.be1_runtime as runtime_module
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.services.support_needs import ParentSupportNeedsService
from sketch2life.domain.parent_profiles import ParentProfileError
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.identity.firebase_token_verifier import FirebaseTokenVerifier
from sketch2life.interfaces.http.openapi_contract import (
    IDEMPOTENCY_MISMATCH_OPERATION_KEYS,
    MOUNTED_OPERATIONS,
)
from sketch2life.interfaces.http.openapi_srs_v22 import SRS_V22_INCLUDED_OPERATIONS
from sketch2life.interfaces.http.parent_runtime import (
    get_parent_principal,
    get_parent_role_reader,
    get_parent_support_needs_service,
)

SENTINEL = "SENTINEL-support-note-5d2e8b"
PROFILE_ID = "a3a878cf-7b93-4f25-a71d-6a3b09351a11"
FOREIGN_PROFILE_ID = "00000000-0000-0000-0000-000000000001"
PARENT_PATH = f"/v1/parent/profiles/{PROFILE_ID}/support-needs"
PARENT_KEY_GET = ("get", "/v1/parent/profiles/{profile_id}/support-needs")
PARENT_KEY_PUT = ("put", "/v1/parent/profiles/{profile_id}/support-needs")
BE1_BASE = "/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles/{child_id}"
BE1_KEY_GET = ("get", f"{BE1_BASE}/support-needs")
BE1_KEY_PUT = ("put", f"{BE1_BASE}/support-needs")
PRINCIPAL = VerifiedPrincipal("subject-1", "issuer-1", frozenset())
HEADERS = {"Authorization": "Bearer synthetic-token", "X-Request-ID": "parent-sn-1"}
BODY = {"expected_revision": 0, "category": "sensory", "note": SENTINEL}
DATABASE_SENTINEL = "postgresql+psycopg://sentinel_user:sentinel_pw@localhost:9/sentinel_db"


class _Repository:
    """Stands in for the Parent repository behind the real service (validation is the real one)."""

    def __init__(self) -> None:
        self.owned: list[UUID] = []
        self.puts: list[dict[str, Any]] = []
        self.gets: list[UUID] = []
        self.error: ParentProfileError | None = None

    def assert_profile_owned(self, *, principal: VerifiedPrincipal, profile_id: UUID) -> None:
        self.owned.append(profile_id)
        if principal.issuer != "issuer-1" or str(profile_id) == FOREIGN_PROFILE_ID:
            raise ParentProfileError(404, "PROFILE_NOT_FOUND", "Profile was not found")

    def get_support_needs(self, *, principal: Any, profile_id: UUID, crypto: Any) -> dict[str, Any]:
        self.gets.append(profile_id)
        if self.error:
            raise self.error
        return {
            "contract": "ParentSupportNeedsV1",
            "profile_id": str(profile_id),
            "revision": 2,
            "category": "sensory",
            "note": SENTINEL,
        }

    def put_support_needs(self, **kwargs: Any) -> dict[str, Any]:
        self.puts.append(kwargs)
        if self.error:
            raise self.error
        return {
            "contract": "ParentSupportNeedsWriteV1",
            "profile_id": str(kwargs["profile_id"]),
            "revision": kwargs["expected_revision"] + 1,
        }


class _Role:
    def __init__(self, active: bool = True) -> None:
        self.active = active

    def has_active_parent_role(self, *, principal: VerifiedPrincipal) -> bool:
        del principal
        return self.active


class _Crypto:
    fingerprint_key_id = "fp-1"


@pytest.fixture
def parent_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[TestClient, _Repository]]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    settings = Settings(
        env="test",
        auth_provider="firebase",
        firebase_project_id="synthetic-parent-project",
        _env_file=None,  # type: ignore[call-arg]
    )
    monkeypatch.setattr(app_module, "get_settings", lambda: settings)
    monkeypatch.setattr(
        runtime_module, "get_core_database_settings", lambda: SimpleNamespace(database_url=None)
    )
    application = app_module.create_app()
    application.state.be1_runtime.identity_verifier = FirebaseTokenVerifier(settings)
    repository = _Repository()
    state = {"crypto": _Crypto()}
    application.dependency_overrides[get_parent_support_needs_service] = lambda: (
        ParentSupportNeedsService(repository, state["crypto"])  # type: ignore[arg-type]
    )
    application.dependency_overrides[get_parent_role_reader] = lambda: _Role()
    application.dependency_overrides[get_parent_principal] = lambda: PRINCIPAL
    application.state.test_state = state
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    try:
        with TestClient(application, raise_server_exceptions=False) as client:
            yield client, repository
    finally:
        application.dependency_overrides.clear()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _error(response: Any, *, status: int, code: str) -> dict[str, Any]:
    assert response.status_code == status, response.text
    body = response.json()
    assert body["code"] == code
    assert body["request_id"] == body["correlation_id"] == response.headers["X-Request-ID"]
    assert SENTINEL not in response.text
    return body  # type: ignore[no-any-return]


def test_the_parent_get_and_put_return_exact_no_store_shapes(
    parent_client: tuple[TestClient, _Repository],
) -> None:
    client, repository = parent_client
    read = client.get(PARENT_PATH, headers=HEADERS)
    assert read.status_code == 200
    assert read.json() == {
        "contract": "ParentSupportNeedsV1",
        "profile_id": PROFILE_ID,
        "revision": 2,
        "category": "sensory",
        "note": SENTINEL,
    }
    assert read.headers["Cache-Control"] == "private, no-store"
    assert read.headers["X-Request-ID"] == "parent-sn-1"
    write = client.put(PARENT_PATH, headers={**HEADERS, "Idempotency-Key": "put-1"}, json=BODY)
    assert write.status_code == 200
    assert write.json() == {
        "contract": "ParentSupportNeedsWriteV1",
        "profile_id": PROFILE_ID,
        "revision": 1,
    }  # the revision only: no category, no note
    assert SENTINEL not in write.text and write.headers["Cache-Control"] == "private, no-store"
    (call,) = repository.puts
    assert (call["expected_revision"], call["idempotency_key"]) == (0, "put-1")
    assert call["payload"].category == "sensory" and call["payload"].note == SENTINEL


def test_the_put_keeps_unicode_and_whitespace_exactly(
    parent_client: tuple[TestClient, _Repository],
) -> None:
    client, repository = parent_client
    body = {"expected_revision": 3, "category": None, "note": "  Cần hỗ trợ\n\tgiác quan  "}
    response = client.put(PARENT_PATH, headers={**HEADERS, "Idempotency-Key": "put-2"}, json=body)
    assert response.status_code == 200
    assert repository.puts[0]["payload"].note == "  Cần hỗ trợ\n\tgiác quan  "
    assert repository.puts[0]["payload"].category is None


def test_the_put_refuses_bad_keys_and_bodies_without_echoing_a_value(
    parent_client: tuple[TestClient, _Repository],
) -> None:
    client, repository = parent_client
    no_key = client.put(PARENT_PATH, headers=HEADERS, json=BODY)
    body = _error(no_key, status=400, code="INVALID_REQUEST")
    assert {"field": "Idempotency-Key", "code": "REQUIRED"} in body["field_errors"]
    bad_key = client.put(PARENT_PATH, headers={**HEADERS, "Idempotency-Key": "bad key"}, json=BODY)
    _error(bad_key, status=400, code="INVALID_REQUEST")
    keyed = {**HEADERS, "Idempotency-Key": "put-3"}
    for payload, field, code in (
        ({**BODY, "extra": SENTINEL}, "<unknown>", "UNKNOWN_FIELD"),
        ({**BODY, "category": None, "note": None}, "body", "EMPTY"),
        ({**BODY, "note": SENTINEL + "\x00"}, "note", "INVALID_FORMAT"),
        ({**BODY, "note": "   "}, "note", "EMPTY"),
        ({**BODY, "note": SENTINEL * 100}, "note", "TOO_LONG"),
        ({**BODY, "category": "c" * 81}, "category", "TOO_LONG"),
        ({**BODY, "note": "ADHD " + SENTINEL}, "note", "DIAGNOSIS_LIKE"),
        ({**BODY, "category": "chẩn đoán " + SENTINEL}, "category", "DIAGNOSIS_LIKE"),
        ({**BODY, "expected_revision": -1}, "expected_revision", "OUT_OF_RANGE"),
        ({**BODY, "expected_revision": "0"}, "expected_revision", "INVALID_TYPE"),
        ({**BODY, "note": 5}, "note", "INVALID_TYPE"),
        ({"expected_revision": 0, "note": SENTINEL}, "category", "REQUIRED"),
    ):
        response = client.put(PARENT_PATH, headers=keyed, json=payload)
        body = _error(response, status=400, code="INVALID_REQUEST")
        assert {"field": field, "code": code} in body["field_errors"], payload
        assert SENTINEL not in response.text, payload
    broken = client.put(PARENT_PATH, headers=keyed, content=b"{" + SENTINEL.encode())
    _error(broken, status=400, code="INVALID_REQUEST")
    assert repository.puts == []  # no write for any refusal


def test_ownership_role_and_profile_id_come_before_the_body(
    parent_client: tuple[TestClient, _Repository],
) -> None:
    client, repository = parent_client
    keyed = {**HEADERS, "Idempotency-Key": "put-4"}
    foreign = f"/v1/parent/profiles/{FOREIGN_PROFILE_ID}/support-needs"
    for response in (
        client.get(foreign, headers=HEADERS),
        client.put(foreign, headers=keyed, json=BODY),
        client.put(foreign, headers=keyed, json={"x": SENTINEL}),
    ):
        _error(response, status=404, code="PROFILE_NOT_FOUND")
    client.app.dependency_overrides[get_parent_role_reader] = lambda: _Role(active=False)  # type: ignore[attr-defined]
    for response in (
        client.get(PARENT_PATH, headers=HEADERS),
        client.put(PARENT_PATH, headers=keyed, json=BODY),
    ):
        _error(response, status=404, code="PROFILE_NOT_FOUND")
    assert repository.puts == [] and repository.gets == []
    invalid = client.get("/v1/parent/profiles/not-a-uuid/support-needs", headers=HEADERS)
    body = _error(invalid, status=400, code="INVALID_REQUEST")
    assert {"field": "profile_id", "code": "INVALID_FORMAT"} in body["field_errors"]


def test_without_a_key_source_both_routes_answer_503_after_authorization(
    parent_client: tuple[TestClient, _Repository],
) -> None:
    client, repository = parent_client
    client.app.state.test_state["crypto"] = None  # type: ignore[attr-defined]
    keyed = {**HEADERS, "Idempotency-Key": "put-5"}
    for response in (
        client.get(PARENT_PATH, headers=HEADERS),
        client.put(PARENT_PATH, headers=keyed, json=BODY),
        client.put(PARENT_PATH, headers=keyed, json={"bad": 1}),  # before the body check
    ):
        body = _error(response, status=503, code="SUPPORT_NEEDS_UNAVAILABLE")
        assert body["retryable"] is True
        assert body["message"] == "Support needs are unavailable"
    foreign = f"/v1/parent/profiles/{FOREIGN_PROFILE_ID}/support-needs"
    _error(client.get(foreign, headers=HEADERS), status=404, code="PROFILE_NOT_FOUND")
    assert repository.puts == [] and repository.gets == []


@pytest.mark.parametrize(
    ("error", "status", "code"),
    [
        (
            ParentProfileError(409, "STALE_REVISION", "stale", current_version=4),
            409,
            "STALE_REVISION",
        ),
        (
            ParentProfileError(409, "INVALID_STATE_TRANSITION", "pending"),
            409,
            "INVALID_STATE_TRANSITION",
        ),
        (
            ParentProfileError(400, "INVALID_IDEMPOTENCY_KEY", "reused"),
            400,
            "INVALID_IDEMPOTENCY_KEY",
        ),
        (
            ParentProfileError(503, "SUPPORT_NEEDS_UNAVAILABLE", "x"),
            503,
            "SUPPORT_NEEDS_UNAVAILABLE",
        ),
    ],
)
def test_repository_refusals_use_the_parent_envelope_with_no_value(
    parent_client: tuple[TestClient, _Repository], error: ParentProfileError, status: int, code: str
) -> None:
    client, repository = parent_client
    repository.error = error
    for response in (
        client.get(PARENT_PATH, headers=HEADERS),
        client.put(PARENT_PATH, headers={**HEADERS, "Idempotency-Key": "put-6"}, json=BODY),
    ):
        body = _error(response, status=status, code=code)
        if code == "STALE_REVISION":
            assert body["current_version"] == 4


# --------------------------------------------------------------------- the published contract
@pytest.fixture
def published(monkeypatch: pytest.MonkeyPatch) -> Iterator[dict[str, Any]]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", DATABASE_SENTINEL)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    try:
        application = app_module.create_app()
        application.openapi()
        yield application.state.runtime_openapi_schema  # type: ignore[no-any-return]
    finally:
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def test_the_four_operations_are_catalogued_with_their_handlers() -> None:
    handlers = {
        key: MOUNTED_OPERATIONS[key]["handler"]
        for key in (PARENT_KEY_GET, PARENT_KEY_PUT, BE1_KEY_GET, BE1_KEY_PUT)
    }
    assert handlers == {
        PARENT_KEY_GET: "parent_profiles.py::get_parent_profile_support_needs",
        PARENT_KEY_PUT: "parent_profiles.py::put_parent_profile_support_needs",
        BE1_KEY_GET: "be1_registry.py::get_profile_support_needs",
        BE1_KEY_PUT: "be1_registry.py::put_profile_support_needs",
    }
    for key in handlers:
        text = str(MOUNTED_OPERATIONS[key]["purpose"])
        for banned in ("capacity", "quota", "billing", "subscription", "payment", "diagnos "):
            assert banned not in text.lower()
        assert "not a diagnosis" in text and "no-store" in text
    assert MOUNTED_OPERATIONS[PARENT_KEY_PUT]["tag"] == "Parent Profiles"
    assert MOUNTED_OPERATIONS[BE1_KEY_PUT]["tag"] == "BE1 — Organizations & Classes"
    # the keyed Teacher write is in the Be1Error mismatch set; the Parent family answers its own
    # envelope (like the Parent PATCH and the T-12a POST) and is in neither set.
    assert BE1_KEY_PUT in IDEMPOTENCY_MISMATCH_OPERATION_KEYS
    assert BE1_KEY_GET not in IDEMPOTENCY_MISMATCH_OPERATION_KEYS
    assert PARENT_KEY_PUT not in IDEMPOTENCY_MISMATCH_OPERATION_KEYS
    # the published SRS set: the two Parent operations, not the two BE1 ones
    assert {PARENT_KEY_GET, PARENT_KEY_PUT} <= SRS_V22_INCLUDED_OPERATIONS
    assert not {BE1_KEY_GET, BE1_KEY_PUT} & SRS_V22_INCLUDED_OPERATIONS


def test_the_runtime_spec_publishes_strict_bodies_and_closed_answers(
    published: dict[str, Any],
) -> None:
    schemas = published["components"]["schemas"]
    for name in ("SupportNeedsPutV1", "Be1SupportNeedsPutV1"):
        schema = schemas[name]
        assert set(schema["properties"]) == {"expected_revision", "category", "note"}
        assert set(schema["required"]) == {"expected_revision", "category", "note"}
        assert schema["additionalProperties"] is False
        assert schema["properties"]["expected_revision"]["minimum"] == 0
    assert set(schemas["ParentSupportNeedsV1"]["properties"]) == {
        "contract",
        "profile_id",
        "revision",
        "category",
        "note",
    }
    assert set(schemas["ParentSupportNeedsWriteV1"]["properties"]) == {
        "contract",
        "profile_id",
        "revision",
    }
    assert set(schemas["Be1SupportNeedsV1"]["properties"]) == {
        "contract",
        "child_id",
        "revision",
        "category",
        "note",
    }
    assert set(schemas["Be1SupportNeedsWriteV1"]["properties"]) == {
        "contract",
        "child_id",
        "revision",
    }
    for name in ("ParentSupportNeedsWriteV1", "Be1SupportNeedsWriteV1"):
        assert "note" not in schemas[name]["properties"]
        assert "category" not in schemas[name]["properties"]


def test_the_runtime_spec_lists_each_method_once_with_a_required_key_on_the_puts(
    published: dict[str, Any],
) -> None:
    parent = published["paths"]["/v1/parent/profiles/{profile_id}/support-needs"]
    be1 = published["paths"][f"{BE1_BASE}/support-needs"]
    assert set(parent) == {"get", "put"} and set(be1) == {"get", "put"}
    assert parent["get"]["operationId"] == "parentGetSupportNeedsV1"
    assert parent["put"]["operationId"] == "parentPutSupportNeedsV1"
    for operation in (parent["put"], be1["put"]):
        key = next(
            p
            for p in operation["parameters"]
            if p["in"] == "header" and p["name"] == "Idempotency-Key"
        )
        assert key["required"] is True and key["schema"]["maxLength"] == 128
        assert "200" in operation["responses"]
    body = be1["put"]["requestBody"]["content"]["application/json"]["schema"]
    assert body["$ref"].endswith("/Be1SupportNeedsPutV1")
    body = parent["put"]["requestBody"]["content"]["application/json"]["schema"]
    assert body["$ref"].endswith("/SupportNeedsPutV1")
    assert {"409", "503"} <= set(parent["get"]["responses"])
    # the catalog documents the Teacher family's 409 and 503 too (the runtime spec of a BE1
    # route lists the shared subset only, as for every BE1 operation)
    for key in (BE1_KEY_GET, BE1_KEY_PUT):
        assert {"409", "503"} <= {row["status"] for row in MOUNTED_OPERATIONS[key]["responses"]}


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/be1/v1/organizations/o/classes/c/profiles/k/support-needs"),
        ("put", "/api/be1/v1/organizations/o/classes/c/profiles/k/support-needs"),
        ("get", f"/v1/parent/profiles/{PROFILE_ID}/support-needs"),
        ("put", f"/v1/parent/profiles/{PROFILE_ID}/support-needs"),
    ],
)
def test_the_routes_need_a_bearer_credential(
    published: dict[str, Any], monkeypatch: pytest.MonkeyPatch, method: str, path: str
) -> None:
    del published
    with TestClient(app_module.create_app(), raise_server_exceptions=False) as client:
        response = client.request(
            method, path, json={"expected_revision": 0, "category": None, "note": SENTINEL}
        )
    assert response.status_code == 401
    assert SENTINEL not in response.text


def test_the_unavailable_code_has_a_safe_message_in_both_envelopes() -> None:
    from sketch2life.interfaces.http.error_envelope import STATUS_MESSAGE_ONLY, build_error_body

    assert "SUPPORT_NEEDS_UNAVAILABLE" in STATUS_MESSAGE_ONLY
    body = build_error_body(status=503, code="SUPPORT_NEEDS_UNAVAILABLE", request_id="r-1")
    assert body["retryable"] is True and "SUPPORT" not in body["message"]
