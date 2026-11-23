"""FEAT-066 T-3a: the lesson occurrence route contract (SRS l.775, l.798, l.1652, l.1697).

Offline: no database, no storage. The service is replaced by a fake, so the module checks the
catalog, the published OpenAPI, request validation (CONV-1 400 bodies), headers, ETag handling and
the error mapping. Behaviour against PostgreSQL lives in
``tests/integration/lesson_occurrences/test_occurrence_postgres.py``.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.story_run_lite import CommandResult
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.lesson_occurrences.scope import LessonOccurrenceError
from sketch2life.infrastructure.lesson_occurrences.service import CreateResult
from sketch2life.infrastructure.story_run_lite import composition
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from sketch2life.interfaces.http.openapi_contract import (
    IDEMPOTENCY_MISMATCH_OPERATION_KEYS,
    MOUNTED_OPERATIONS,
)
from sketch2life.interfaces.http.openapi_srs_v22 import (
    SRS_V22_INCLUDED_OPERATIONS,
    SRS_V22_OPERATION_TAGS,
)
from sketch2life.interfaces.http.routers.lesson_occurrences import get_occurrence_service

FLAG = "STORYRUN_LITE_MAIN_DEMO_ENABLED"
ACK = "STORYRUN_LITE_MAIN_DEMO_REPLACES_PARENT_ROUTER"
DATABASE_SENTINEL = "postgresql+psycopg://sentinel_user:sentinel_pw@localhost:9/sentinel_db"
POST = ("post", "/v1/lesson-occurrences")
GET_ONE = ("get", "/v1/lesson-occurrences/{occurrence_id}")
GET_LIST = ("get", "/v1/lesson-occurrences")
OPERATIONS = (POST, GET_ONE, GET_LIST)
STORAGE_WORDS = (
    "bucket",
    "object_key",
    "storage_object_ref",
    "presigned",
    "credential",
    "amazonaws",
    "minio",
    "organization_ref",
    "organization_id",
)
NOW = datetime(2026, 11, 20, 3, 0, tzinfo=UTC)
HASH = "b" * 64
BODY: dict[str, Any] = {
    "contract": "LessonOccurrenceV1",
    "occurrence_id": "occ-1",
    "class_id": "class-1",
    "title": "Bài học vẽ",
    "scheduled_date": None,
    "state": "DRAFT",
    "revision": 4,
    "responsible_teacher_ref": "acct-1",
    "lesson_version_ref": None,
    "lesson_version_no": None,
    "approved_plan": None,
    "sample_video": {"slot_state": "AVAILABLE", "claimed_at": None, "run_ref": None},
    "created_at": NOW,
}


@pytest.fixture(autouse=True)
def _environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", DATABASE_SENTINEL)
    monkeypatch.delenv(FLAG, raising=False)
    monkeypatch.delenv(ACK, raising=False)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    try:
        yield
    finally:
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


class FakeService:
    def __init__(self) -> None:
        self.error: Exception | None = None
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def _maybe_fail(self) -> None:
        if self.error is not None:
            raise self.error

    def create(self, **kwargs: Any) -> CreateResult:
        self.calls.append(("create", kwargs))
        self._maybe_fail()
        return CreateResult(dict(BODY), replayed=False)

    def get(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("get", kwargs))
        self._maybe_fail()
        return dict(BODY)

    def list_page(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("list", kwargs))
        self._maybe_fail()
        return {"contract": "LessonOccurrencePageV1", "items": [dict(BODY)], "next_cursor": "n"}


@pytest.fixture
def served() -> Iterator[tuple[TestClient, FakeService]]:
    application = create_app()
    service = FakeService()

    async def verified() -> VerifiedPrincipal:
        return VerifiedPrincipal(subject="subject-1", issuer="issuer", roles=frozenset())

    application.dependency_overrides[get_verified_adult] = verified
    application.dependency_overrides[get_occurrence_service] = lambda: service
    with TestClient(application) as client:
        yield client, service


def headers(key: str | None = "key-1") -> dict[str, str]:
    return {"Idempotency-Key": key} if key is not None else {}


def valid_body(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"class_id": "class-1", "title": "Bài học vẽ"}
    body.update(overrides)
    return body


# ----------------------------------------------------------------------------- catalog
def test_the_three_operations_are_catalogued_projected_and_tagged() -> None:
    for key in OPERATIONS:
        assert key in MOUNTED_OPERATIONS
        assert key in SRS_V22_INCLUDED_OPERATIONS
        assert SRS_V22_OPERATION_TAGS[key] == "Lesson Occurrences"
        assert MOUNTED_OPERATIONS[key]["tag"] == "Lesson Occurrences"
        assert MOUNTED_OPERATIONS[key]["authentication"] == "HTTPBearer (bearer)"
    assert POST in IDEMPOTENCY_MISMATCH_OPERATION_KEYS
    assert GET_ONE not in IDEMPOTENCY_MISMATCH_OPERATION_KEYS
    assert GET_LIST not in IDEMPOTENCY_MISMATCH_OPERATION_KEYS


def test_published_contract_documents_the_routes_and_leaks_nothing() -> None:
    spec = create_app().openapi()
    published = spec["paths"]
    create = published["/v1/lesson-occurrences"]["post"]
    assert create["tags"] == ["Lesson Occurrences"] and create["security"]
    assert create["responses"]["201"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/LessonOccurrenceV1"
    }
    assert "422" not in create["responses"]
    parameters = {(p["in"], p["name"]): p for p in create["parameters"]}
    assert parameters[("header", "Idempotency-Key")]["required"] is True
    one = published["/v1/lesson-occurrences/{occurrence_id}"]["get"]
    assert "304" in one["responses"] and "404" in one["responses"]
    listing = published["/v1/lesson-occurrences"]["get"]
    query = {p["name"]: p for p in listing["parameters"] if p["in"] == "query"}
    assert query["class_id"]["required"] is True
    assert query["limit"]["schema"]["maximum"] == 100 and query["limit"]["schema"]["default"] == 25
    assert set(query) == {"class_id", "state", "limit", "cursor"}
    schemas = spec["components"]["schemas"]
    request = schemas["CreateLessonOccurrenceRequestV1"]
    assert request["additionalProperties"] is False
    assert set(request["properties"]) == {
        "class_id",
        "title",
        "scheduled_date",
        "lesson_version_ref",
    }
    assert set(schemas["LessonVersionRefV1"]["properties"]) == {
        "lesson_id",
        "version_id",
        "content_sha256",
    }
    assert set(schemas["LessonOccurrenceV1"]["properties"]) == set(BODY)
    scoped = json.dumps(
        {path: published[path] for path in published if "lesson-occurrences" in path}
    )
    scoped += json.dumps(
        {
            name: schema
            for name, schema in schemas.items()
            if name
            in {
                "CreateLessonOccurrenceRequestV1",
                "LessonOccurrenceV1",
                "LessonOccurrencePageV1",
                "LessonVersionRefV1",
                "ApprovedPlanSummaryV1",
                "SampleVideoStateV1",
            }
        }
    )
    for word in STORAGE_WORDS:
        assert word not in scoped.lower(), word
    assert "latest" not in scoped.lower()


# ----------------------------------------------------------------------------- validation
def test_missing_or_malformed_keys_are_400_with_a_field_error(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    missing = client.post("/v1/lesson-occurrences", json=valid_body())
    assert missing.status_code == 400 and missing.json()["code"] == "INVALID_REQUEST"
    assert {"field": "Idempotency-Key", "code": "REQUIRED"} in missing.json()["field_errors"]
    for bad in ("has space", "x" * 129):
        response = client.post("/v1/lesson-occurrences", json=valid_body(), headers=headers(bad))
        assert response.status_code == 400, bad
        assert response.json()["code"] == "INVALID_REQUEST"
    assert service.calls == []


@pytest.mark.parametrize(
    ("overrides", "field", "code"),
    [
        ({"title": ""}, "title", "EMPTY"),
        ({"title": "x" * 201}, "title", "TOO_LONG"),
        ({"class_id": ""}, "class_id", "EMPTY"),
        ({"scheduled_date": "20/11/2026"}, "scheduled_date", "INVALID_FORMAT"),
        ({"title": 5}, "title", "INVALID_TYPE"),
    ],
)
def test_invalid_bodies_are_400_never_422(
    served: tuple[TestClient, FakeService], overrides: dict[str, Any], field: str, code: str
) -> None:
    client, service = served
    response = client.post(
        "/v1/lesson-occurrences", json=valid_body(**overrides), headers=headers()
    )
    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "INVALID_REQUEST"
    assert {"field": field, "code": code} in body["field_errors"]
    assert service.calls == []


def test_unknown_body_fields_are_refused_so_a_client_cannot_name_an_organization(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    for extra in ("organization_id", "responsible_teacher_ref", "state", "revision"):
        response = client.post(
            "/v1/lesson-occurrences", json=valid_body(**{extra: "x"}), headers=headers()
        )
        assert response.status_code == 400, extra
        assert any(item["code"] == "UNKNOWN_FIELD" for item in response.json()["field_errors"])
    latest = client.post(
        "/v1/lesson-occurrences",
        json=valid_body(lesson_version_ref={"lesson_id": "l", "version": "latest"}),
        headers=headers(),
    )
    assert latest.status_code == 400
    assert service.calls == []


def test_list_parameters_are_validated(served: tuple[TestClient, FakeService]) -> None:
    client, service = served
    for query, field, code in (
        ("limit=101&class_id=c", "limit", "OUT_OF_RANGE"),
        ("limit=0&class_id=c", "limit", "OUT_OF_RANGE"),
        ("limit=abc&class_id=c", "limit", "INVALID_TYPE"),
        ("", "class_id", "REQUIRED"),
        ("class_id=c&state=DONE", "state", "INVALID_FORMAT"),
    ):
        response = client.get(f"/v1/lesson-occurrences?{query}")
        assert response.status_code == 400, query
        assert {"field": field, "code": code} in response.json()["field_errors"], query
    assert service.calls == []
    assert client.get("/v1/lesson-occurrences?class_id=c&limit=100").status_code == 200


# ----------------------------------------------------------------------------- behaviour
def test_create_returns_201_with_location_and_a_strong_etag(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    response = client.post(
        "/v1/lesson-occurrences", json=valid_body(scheduled_date="2026-11-21"), headers=headers("k")
    )
    assert response.status_code == 201
    assert response.headers["Location"] == "/v1/lesson-occurrences/occ-1"
    assert response.headers["ETag"] == '"4"'
    assert response.json()["occurrence_id"] == "occ-1"
    ((name, kwargs),) = service.calls
    assert name == "create" and kwargs["idempotency_key"] == "k"
    assert kwargs["payload"].class_id == "class-1" and kwargs["principal"].subject == "subject-1"


def test_get_sets_the_etag_and_answers_304_for_a_matching_validator(
    served: tuple[TestClient, FakeService],
) -> None:
    client, _service = served
    first = client.get("/v1/lesson-occurrences/occ-1")
    assert first.status_code == 200 and first.headers["ETag"] == '"4"'
    assert first.headers["Cache-Control"] == "private, no-cache"
    again = client.get("/v1/lesson-occurrences/occ-1", headers={"If-None-Match": '"4"'})
    assert again.status_code == 304 and again.content == b"" and again.headers["ETag"] == '"4"'
    stale = client.get("/v1/lesson-occurrences/occ-1", headers={"If-None-Match": '"3"'})
    assert stale.status_code == 200


def test_list_returns_a_page_without_an_etag(served: tuple[TestClient, FakeService]) -> None:
    client, service = served
    response = client.get("/v1/lesson-occurrences?class_id=class-1&state=DRAFT&limit=10")
    assert response.status_code == 200 and "ETag" not in response.headers
    assert response.json()["next_cursor"] == "n"
    ((_, kwargs),) = service.calls
    assert kwargs["limit"] == 10 and kwargs["state"] == "DRAFT" and kwargs["cursor"] is None


@pytest.mark.parametrize(
    ("error", "status", "code"),
    [
        (LessonOccurrenceError(404, "RESOURCE_NOT_FOUND"), 404, "RESOURCE_NOT_FOUND"),
        (LessonOccurrenceError(403, "ACTION_NOT_ALLOWED"), 403, "ACTION_NOT_ALLOWED"),
        (
            LessonOccurrenceError(409, "TEACHER_ASSIGNMENT_REQUIRED"),
            409,
            "TEACHER_ASSIGNMENT_REQUIRED",
        ),
        (LessonOccurrenceError(409, "INVALID_STATE_TRANSITION"), 409, "INVALID_STATE_TRANSITION"),
        (LessonOccurrenceError(409, "STALE_REVISION"), 409, "STALE_REVISION"),
        (LessonOccurrenceError(400, "INVALID_IDEMPOTENCY_KEY"), 400, "INVALID_IDEMPOTENCY_KEY"),
    ],
)
def test_service_refusals_use_the_conv1_envelope(
    served: tuple[TestClient, FakeService], error: Exception, status: int, code: str
) -> None:
    client, service = served
    service.error = error
    response = client.post("/v1/lesson-occurrences", json=valid_body(), headers=headers())
    assert response.status_code == status
    body = response.json()
    assert body["code"] == code and body["message"] and body["request_id"] == body["correlation_id"]
    assert set(body) >= {"retryable", "retry_after_seconds", "field_errors"}
    assert client.get("/v1/lesson-occurrences/occ-1").status_code == status


def test_a_malformed_cursor_is_400_on_the_cursor_field(
    served: tuple[TestClient, FakeService],
) -> None:
    from sketch2life.domain.lesson_occurrences.model import LessonOccurrenceRuleError

    client, service = served
    service.error = LessonOccurrenceRuleError("cursor", "INVALID_FORMAT")
    response = client.get("/v1/lesson-occurrences?class_id=c&cursor=zzz")
    assert response.status_code == 400
    assert response.json()["field_errors"] == [{"field": "cursor", "code": "INVALID_FORMAT"}]


def test_a_stale_pin_carries_no_current_version_but_the_envelope_code(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    service.error = LessonOccurrenceError(409, "STALE_REVISION", current_version=3)
    body = client.post("/v1/lesson-occurrences", json=valid_body(), headers=headers()).json()
    assert body["code"] == "STALE_REVISION" and body["current_version"] == 3


def test_the_routes_need_a_bearer_token() -> None:
    with TestClient(create_app()) as client:
        for response in (
            client.get("/v1/lesson-occurrences/occ-1"),
            client.get("/v1/lesson-occurrences?class_id=c"),
            client.post("/v1/lesson-occurrences", json=valid_body(), headers=headers()),
        ):
            assert response.status_code == 401 and response.json()["code"] == "AUTH_REQUIRED"


# ----------------------------------------------------------------------------- mounting
@pytest.fixture
def local_demo(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv(FLAG, "1")
    monkeypatch.setenv(ACK, "1")
    get_settings.cache_clear()
    service = Mock()
    service.get_upload.return_value = CommandResult(200, {"upload_ref": "synthetic"}, 1)
    runtime = Mock()
    runtime.service = service
    monkeypatch.setattr(composition, "build_runtime", Mock(return_value=runtime))
    yield
    get_settings.cache_clear()


def test_the_router_is_mounted_in_both_demo_modes_and_demo_bodies_stay_unchanged(
    local_demo: None,
) -> None:
    application = create_app()
    with TestClient(
        application, base_url="http://127.0.0.1", client=("127.0.0.1", 54321)
    ) as client:
        # Mounted (a bearer token is asked for) and in the CONV-1 envelope even with the demo on.
        mounted = client.get("/v1/lesson-occurrences/occ-1")
        assert mounted.status_code == 401 and mounted.json()["code"] == "AUTH_REQUIRED"
        listed = client.get("/v1/lesson-occurrences?class_id=c")
        assert listed.status_code == 401 and listed.json()["code"] == "AUTH_REQUIRED"
        demo = client.get("/v1/upload-sessions/synthetic")
        story = client.get("/v1/story-runs/synthetic/no-such-route")
        sibling = client.get("/v1/lesson-occurrencesfoo")
    assert demo.status_code == 200 and demo.json() == {"upload_ref": "synthetic"}
    assert "request_id" not in story.json()  # the demo family keeps its own body shape
    assert sibling.status_code == 404 and "code" not in sibling.json()
