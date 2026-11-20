"""FEAT-066 T-3d: occurrence plan revisions (SRS l.547-548, l.775, l.1659-1660, l.1699).

Offline: no database, no storage. The service is replaced by a fake, except for the request rules
that run the real service up to its first database access (a plan is validated before anything
else). The module checks the catalog (four operations; create and confirm are keyed), the published
OpenAPI, request validation in the CONV-1 envelope, headers and ETags, the stale 409
(``current_version``), the explicit refusal of Teacher-written activities while no safety checklist
exists, the request size guard and the 401. Behaviour against PostgreSQL lives in
``tests/integration/lesson_occurrences/test_plan_revisions_postgres.py``.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

import sketch2life
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.domain.lesson_occurrences.plan import plan_etag
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.lesson_occurrences.documents import DocumentError
from sketch2life.infrastructure.lesson_occurrences.plans import PlanResult, PlanRevisionService
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from sketch2life.interfaces.http.middleware.bounded_image_upload import (
    MAX_PLAN_CONFIRM_BODY_BYTES,
    MAX_PLAN_CREATE_BODY_BYTES,
)
from sketch2life.interfaces.http.openapi_contract import (
    IDEMPOTENCY_MISMATCH_OPERATION_KEYS,
    MOUNTED_OPERATIONS,
)
from sketch2life.interfaces.http.openapi_srs_v22 import SRS_V22_INCLUDED_OPERATIONS
from sketch2life.interfaces.http.routers.lesson_occurrences import get_plan_service

DATABASE_SENTINEL = "postgresql+psycopg://sentinel_user:sentinel_pw@localhost:9/sentinel_db"
BASE = "/v1/lesson-occurrences/{occurrence_id}/plan-revisions"
ONE = BASE + "/{revision_no}"
CONFIRM = ONE + "/confirm"
URL = "/v1/lesson-occurrences/occ-1/plan-revisions"
CONFIRM_URL = URL + "/3/confirm"
NOW = datetime(2026, 11, 20, 3, 0, tzinfo=UTC)
HASH = "a" * 64
STORAGE_WORDS = ("bucket", "object_key", "presigned", "amazonaws", "organization_ref", "scanner")


def plan_json(number: int = 3, state: str = "DRAFT") -> dict[str, Any]:
    return {
        "contract": "LessonPlanRevisionV1",
        "occurrence_id": "occ-1",
        "revision_no": number,
        "state": state,
        "content_hash": HASH,
        "document_revision_ref": {"document_id": "doc-1", "revision_no": 2},
        "objectives": ["Nhận biết hình tròn"],
        "teacher_direction": "Câu chuyện về chú mèo",
        "safety_notes": None,
        "lesson_version_ref": None,
        "lesson_version_no": None,
        "activities": [
            {
                "order": 1,
                "kind": "LESSON",
                "lesson_activity_id": "act-1",
                "title": "Vẽ cây",
                "description": "Vẽ thân rồi tán lá",
                "snapshot_hash": "b" * 64,
                "checklist_required": False,
                "checklist_version": None,
                "confirmed": False,
            }
        ],
        "created_at": NOW,
        "approved_at": NOW if state == "APPROVED" else None,
        "supersedes_revision_no": 2 if state == "APPROVED" else None,
    }


@pytest.fixture(autouse=True)
def _environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", DATABASE_SENTINEL)
    monkeypatch.delenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", raising=False)
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
        self.page: dict[str, Any] = {
            "contract": "LessonPlanRevisionPageV1",
            "items": [
                {
                    "revision_no": 3,
                    "state": "DRAFT",
                    "content_hash": HASH,
                    "activity_count": 1,
                    "created_at": NOW,
                    "approved_at": None,
                }
            ],
            "next_cursor": None,
        }

    def _answer(self, name: str, kwargs: dict[str, Any]) -> None:
        self.calls.append((name, kwargs))
        if self.error is not None:
            raise self.error

    def create_revision(self, **kwargs: Any) -> PlanResult:
        self._answer("create", kwargs)
        return PlanResult(plan_json(), 201, replayed=False)

    def confirm_revision(self, **kwargs: Any) -> PlanResult:
        self._answer("confirm", kwargs)
        return PlanResult(plan_json(state="APPROVED"), 200, replayed=False)

    def get_revision(self, **kwargs: Any) -> dict[str, Any]:
        self._answer("get", kwargs)
        return plan_json()

    def list_revisions(self, **kwargs: Any) -> dict[str, Any]:
        self._answer("list", kwargs)
        return self.page


class NoDatabase:
    def __getattr__(self, name: str) -> Any:
        raise AssertionError(f"the request rules must refuse before the database ({name})")


def principal() -> VerifiedPrincipal:
    return VerifiedPrincipal(subject="subject-1", issuer="issuer", roles=frozenset())


@pytest.fixture
def served() -> Iterator[tuple[TestClient, FakeService]]:
    application = create_app()
    service = FakeService()

    async def verified() -> VerifiedPrincipal:
        return principal()

    application.dependency_overrides[get_verified_adult] = verified
    application.dependency_overrides[get_plan_service] = lambda: service
    with TestClient(application) as client:
        yield client, service


@pytest.fixture
def served_real_rules() -> Iterator[TestClient]:
    """The real service (shipped empty checklist registry) with no database."""
    application = create_app()

    async def verified() -> VerifiedPrincipal:
        return principal()

    application.dependency_overrides[get_verified_adult] = verified
    application.dependency_overrides[get_plan_service] = lambda: PlanRevisionService(
        NoDatabase()  # type: ignore[arg-type]
    )
    with TestClient(application) as client:
        yield client


def headers(key: str | None = "key-1") -> dict[str, str]:
    return {"Idempotency-Key": key} if key is not None else {}


def good(**overrides: Any) -> dict[str, Any]:
    values: dict[str, Any] = {
        "expected_head_revision_no": 2,
        "objectives": ["Nhận biết hình tròn"],
        "teacher_direction": "Câu chuyện về chú mèo",
    }
    values.update(overrides)
    return values


def confirm_body(**overrides: Any) -> dict[str, Any]:
    return {"expected_plan_hash": HASH, **overrides}


# ----------------------------------------------------------------------------- catalog
def test_four_operations_two_of_them_keyed_and_none_in_the_fe_projection() -> None:
    expected = {
        ("post", BASE): "create_plan_revision",
        ("get", BASE): "list_plan_revisions",
        ("get", ONE): "get_plan_revision",
        ("post", CONFIRM): "confirm_plan_revision",
    }
    for key, handler in expected.items():
        contract = MOUNTED_OPERATIONS[key]
        assert contract["tag"] == "Lesson Occurrences"
        assert contract["authentication"] == "HTTPBearer (bearer)"
        assert contract["handler"] == f"lesson_occurrences.py::{handler}"
        assert key not in SRS_V22_INCLUDED_OPERATIONS
    assert {key for key in expected if key in IDEMPOTENCY_MISMATCH_OPERATION_KEYS} == {
        ("post", BASE),
        ("post", CONFIRM),
    }
    assert {r["status"] for r in MOUNTED_OPERATIONS[("post", BASE)]["responses"]} == {
        "201",
        "400",
        "401",
        "403",
        "404",
        "409",
        "413",
        "503",
    }
    assert {r["status"] for r in MOUNTED_OPERATIONS[("post", CONFIRM)]["responses"]} == {
        "200",
        "400",
        "401",
        "403",
        "404",
        "409",
        "413",
        "503",
    }
    assert {r["status"] for r in MOUNTED_OPERATIONS[("get", ONE)]["responses"]} >= {"200", "304"}


def test_no_latest_alias_and_no_plan_not_approved_code_in_the_plan_routes() -> None:
    application = create_app()
    application.openapi()
    paths = list(application.state.runtime_openapi_schema["paths"])
    assert not [path for path in paths if "plan-revisions" in path and "latest" in path.lower()]
    assert not [path for path in paths if path.rstrip("/").endswith("/plan-revisions/latest")]
    root = Path(sketch2life.__file__).resolve().parent
    for relative in (
        "interfaces/http/routers/lesson_occurrences.py",
        "infrastructure/lesson_occurrences/plans.py",
        "domain/lesson_occurrences/plan.py",
        "domain/lesson_occurrences/safety_checklist.py",
    ):
        assert "LESSON_PLAN_NOT_APPROVED" not in (root / relative).read_text(encoding="utf-8")
    assert "CLASS_CAPACITY_REACHED" not in (
        root / "infrastructure/lesson_occurrences/plans.py"
    ).read_text(encoding="utf-8")


def test_published_contract_documents_the_plan_and_leaks_nothing() -> None:
    application = create_app()
    projected = application.openapi()
    assert not [path for path in projected["paths"] if "plan-revisions" in path]
    spec = application.state.runtime_openapi_schema
    create = spec["paths"][BASE]["post"]
    assert create["tags"] == ["Lesson Occurrences"] and create["security"]
    assert create["responses"]["201"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/LessonPlanRevisionV1"
    }
    assert "422" not in create["responses"]
    parameters = {(p["in"], p["name"]): p for p in create["parameters"]}
    assert parameters[("header", "Idempotency-Key")]["required"] is True
    for needle in ("STALE_REVISION", "expected_head_revision_no", "NOT_SUPPORTED", "1 MiB"):
        assert needle in create["description"]
    confirm = spec["paths"][CONFIRM]["post"]
    assert confirm["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/LessonPlanRevisionV1"
    }
    for needle in ("STALE_REVISION", "head", "SUPERSEDED", "256 KiB", "checklist"):
        assert needle in confirm["description"]
    request = spec["components"]["schemas"]["CreatePlanRevisionRequestV1"]
    assert request["additionalProperties"] is False
    assert set(request["required"]) == {
        "expected_head_revision_no",
        "objectives",
        "teacher_direction",
    }
    assert request["properties"]["objectives"]["maxItems"] == 12
    assert request["properties"]["objectives"]["items"]["maxLength"] == 1000
    assert request["properties"]["activities"]["maxItems"] == 24
    assert request["properties"]["expected_head_revision_no"]["minimum"] == 0
    assert "lesson_version_ref" not in request["properties"]
    activity = spec["components"]["schemas"]["PlanActivityInputV1"]
    assert activity["properties"]["title"]["anyOf"][0]["maxLength"] == 160
    published = json.dumps([create, confirm, request, activity]).lower()
    for word in STORAGE_WORDS:
        assert word not in published, word
    body = json.dumps(spec["components"]["schemas"]["LessonPlanRevisionV1"]).lower()
    for word in STORAGE_WORDS:
        assert word not in body, word


# ----------------------------------------------------------------------------- validation
def test_a_missing_or_malformed_key_is_400_and_nothing_runs(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    for url, body in ((URL, good()), (CONFIRM_URL, confirm_body())):
        missing = client.post(url, json=body)
        assert missing.status_code == 400 and missing.json()["code"] == "INVALID_REQUEST"
        assert {"field": "Idempotency-Key", "code": "REQUIRED"} in missing.json()["field_errors"]
        for bad in ("has space", "x" * 129):
            assert client.post(url, json=body, headers=headers(bad)).status_code == 400
    assert service.calls == []


@pytest.mark.parametrize(
    ("body", "field", "code"),
    [
        ({"objectives": ["x"], "teacher_direction": "d"}, "expected_head_revision_no", "REQUIRED"),
        ({"expected_head_revision_no": 0, "teacher_direction": "d"}, "objectives", "REQUIRED"),
        ({"expected_head_revision_no": 0, "objectives": ["x"]}, "teacher_direction", "REQUIRED"),
        (good(objectives=[]), "objectives", "EMPTY"),
        (good(objectives=["x"] * 13), "objectives", "TOO_LONG"),
        (good(objectives=["x" * 1001]), "objectives", "TOO_LONG"),
        (good(objectives=[""]), "objectives", "EMPTY"),
        (good(objectives="x"), "objectives", "INVALID_TYPE"),
        (good(teacher_direction=""), "teacher_direction", "EMPTY"),
        (good(teacher_direction="d" * 2001), "teacher_direction", "TOO_LONG"),
        (good(safety_notes="n" * 2001), "safety_notes", "TOO_LONG"),
        (good(expected_head_revision_no=-1), "expected_head_revision_no", "OUT_OF_RANGE"),
        (good(expected_head_revision_no="2"), "expected_head_revision_no", "INVALID_TYPE"),
        (good(expected_head_revision_no=True), "expected_head_revision_no", "INVALID_TYPE"),
        (good(activities=[{"kind": "LESSON"}] * 25), "activities", "TOO_LONG"),
        (good(activities=[{"kind": "OTHER"}]), "activities.kind", "INVALID_FORMAT"),
        (
            good(activities=[{"kind": "CUSTOM", "title": "t" * 161, "description": "d"}]),
            "activities.title",
            "TOO_LONG",
        ),
        (
            good(activities=[{"kind": "CUSTOM", "title": "t", "description": "d" * 4001}]),
            "activities.description",
            "TOO_LONG",
        ),
        (
            good(document_revision_ref={"document_id": "d"}),
            "document_revision_ref.revision_no",
            "REQUIRED",
        ),
        (
            good(document_revision_ref={"document_id": "d", "revision_no": 0}),
            "document_revision_ref.revision_no",
            "OUT_OF_RANGE",
        ),
    ],
)
def test_invalid_create_bodies_are_400_with_field_errors_never_422(
    served: tuple[TestClient, FakeService], body: dict[str, Any], field: str, code: str
) -> None:
    client, service = served
    response = client.post(URL, json=body, headers=headers())
    assert response.status_code == 400, response.text
    payload = response.json()
    assert payload["code"] == "INVALID_REQUEST"
    assert {"field": field, "code": code} in payload["field_errors"]
    assert service.calls == []


def test_unknown_create_fields_are_refused_and_there_is_no_pin_field(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    for extra in (
        "lesson_version_ref",
        "lesson_id",
        "version_id",
        "latest",
        "state",
        "content_hash",
        "revision_no",
        "organization_id",
        "created_by",
        "approved_at",
    ):
        response = client.post(URL, json=good(**{extra: "x"}), headers=headers())
        assert response.status_code == 400, extra
        assert any(item["code"] == "UNKNOWN_FIELD" for item in response.json()["field_errors"])
    assert service.calls == []


@pytest.mark.parametrize(
    ("body", "field", "code"),
    [
        ({}, "expected_plan_hash", "REQUIRED"),
        (confirm_body(expected_plan_hash="A" * 64), "expected_plan_hash", "INVALID_FORMAT"),
        (confirm_body(expected_plan_hash="a" * 63), "expected_plan_hash", "INVALID_FORMAT"),
        (confirm_body(expected_plan_hash=5), "expected_plan_hash", "INVALID_TYPE"),
        (confirm_body(checklist="x"), "checklist", "INVALID_TYPE"),
        (
            confirm_body(checklist=[{"activity_order": 1}]),
            "checklist.checklist_version",
            "REQUIRED",
        ),
        (
            confirm_body(checklist=[{"activity_order": 0, "checklist_version": "v", "items": []}]),
            "checklist.activity_order",
            "OUT_OF_RANGE",
        ),
        (
            confirm_body(
                checklist=[
                    {
                        "activity_order": 1,
                        "checklist_version": "v",
                        "items": [{"item_id": "bad id", "checked": True}],
                    }
                ]
            ),
            "checklist.items.item_id",
            "INVALID_FORMAT",
        ),
        (
            confirm_body(
                checklist=[
                    {
                        "activity_order": 1,
                        "checklist_version": "v",
                        "items": [{"item_id": "a", "checked": "yes"}],
                    }
                ]
            ),
            "checklist.items.checked",
            "INVALID_TYPE",
        ),
        (confirm_body(extra=1), "<unknown>", "UNKNOWN_FIELD"),
    ],
)
def test_invalid_confirm_bodies_are_400_with_field_errors(
    served: tuple[TestClient, FakeService], body: dict[str, Any], field: str, code: str
) -> None:
    client, service = served
    response = client.post(CONFIRM_URL, json=body, headers=headers())
    assert response.status_code == 400, response.text
    assert {"field": field, "code": code} in response.json()["field_errors"]
    assert service.calls == []


def test_a_revision_number_in_the_path_must_be_positive(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    for number in ("0", "-1", "abc", "1000001"):
        response = client.post(
            f"/v1/lesson-occurrences/occ-1/plan-revisions/{number}/confirm",
            json=confirm_body(),
            headers=headers(),
        )
        assert response.status_code == 400, number
        assert client.get(f"{URL}/{number}").status_code in {400, 401}
    assert service.calls == []


# ----------------------------------------------------------------------------- request rules
def test_free_text_reaches_the_service_exactly_as_sent(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    response = client.post(
        URL,
        json=good(teacher_direction="  hướng \n truyện  ", objectives=[" a ", "b "]),
        headers=headers("k"),
    )
    assert response.status_code == 201
    ((name, kwargs),) = service.calls
    assert name == "create"
    assert kwargs["payload"].teacher_direction == "  hướng \n truyện  "
    assert kwargs["payload"].objectives == [" a ", "b "]
    assert kwargs["occurrence_id"] == "occ-1" and kwargs["idempotency_key"] == "k"
    assert kwargs["principal"].subject == "subject-1"


def test_a_custom_activity_is_refused_explicitly_while_no_checklist_exists(
    served_real_rules: TestClient,
) -> None:
    response = served_real_rules.post(
        URL,
        json=good(
            activities=[
                {"kind": "CUSTOM", "title": "Tự soạn", "description": "Mô tả"},
                {"kind": "CATALOG"},
            ]
        ),
        headers=headers(),
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "INVALID_REQUEST" and payload["message"]
    assert payload["field_errors"] == [
        {"field": "activities[0].kind", "code": "NOT_SUPPORTED"},
        {"field": "activities[1].kind", "code": "NOT_SUPPORTED"},
    ]


@pytest.mark.parametrize("text", ["co NUL \x00 giua", "   \n\t "])
def test_nul_and_blank_texts_answer_400_before_any_database_access(
    served_real_rules: TestClient, text: str
) -> None:
    response = served_real_rules.post(
        URL, json=good(objectives=[text], teacher_direction=text), headers=headers()
    )
    assert response.status_code == 400
    codes = {item["code"] for item in response.json()["field_errors"]}
    assert codes <= {"INVALID_FORMAT", "EMPTY"} and codes


def test_a_lone_surrogate_is_a_400_that_is_not_echoed(served_real_rules: TestClient) -> None:
    raw = (
        b'{"expected_head_revision_no":0,"objectives":["abc\\ud800def"],'
        b'"teacher_direction":"ok","safety_notes":"x\\udfffy"}'
    )
    response = served_real_rules.post(
        URL, content=raw, headers={**headers(), "Content-Type": "application/json"}
    )
    assert response.status_code == 400, response.text
    payload = response.json()
    assert payload["code"] == "INVALID_REQUEST"
    fields = {item["field"] for item in payload["field_errors"]}
    # the schema already refuses a lone surrogate (never echoed); the service guard is a backstop
    assert {"objectives", "safety_notes"} <= fields
    assert "abc" not in response.text and "ud800" not in response.text


# ----------------------------------------------------------------------------- behaviour
def test_create_is_201_with_location_and_a_strong_etag_of_hash_and_state(
    served: tuple[TestClient, FakeService],
) -> None:
    client, _service = served
    response = client.post(URL, json=good(), headers=headers())
    assert response.status_code == 201
    assert response.headers["Location"] == f"{URL}/3"
    assert response.headers["ETag"] == plan_etag(HASH, "DRAFT") == f'"{HASH}.DRAFT"'
    assert response.headers["Cache-Control"] == "private, no-cache"
    body = response.json()
    assert body["state"] == "DRAFT" and body["content_hash"] == HASH
    assert body["activities"][0]["checklist_required"] is False
    assert body["approved_at"] is None and body["supersedes_revision_no"] is None


def test_confirm_is_200_with_the_approved_etag_and_names_the_superseded_revision(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    response = client.post(CONFIRM_URL, json=confirm_body(), headers=headers("k2"))
    assert response.status_code == 200
    assert response.headers["ETag"] == f'"{HASH}.APPROVED"'
    assert response.headers["Content-Location"] == f"{URL}/3"
    body = response.json()
    assert body["state"] == "APPROVED" and body["supersedes_revision_no"] == 2
    ((name, kwargs),) = service.calls
    assert name == "confirm" and kwargs["revision_no"] == 3
    assert kwargs["payload"].expected_plan_hash == HASH and kwargs["idempotency_key"] == "k2"


def test_a_single_read_has_an_etag_and_answers_304_for_a_matching_validator(
    served: tuple[TestClient, FakeService],
) -> None:
    client, _service = served
    first = client.get(f"{URL}/3")
    assert first.status_code == 200 and first.headers["ETag"] == f'"{HASH}.DRAFT"'
    assert first.headers["Cache-Control"] == "private, no-cache"
    second = client.get(f"{URL}/3", headers={"If-None-Match": first.headers["ETag"]})
    assert second.status_code == 304 and second.content == b""
    other = client.get(f"{URL}/3", headers={"If-None-Match": f'"{HASH}.APPROVED"'})
    assert other.status_code == 200


def test_the_list_is_a_page_without_an_etag_and_limits_are_checked(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    response = client.get(URL, params={"limit": 25})
    assert response.status_code == 200
    assert response.json()["items"][0]["activity_count"] == 1
    assert "ETag" not in response.headers
    assert client.get(URL, params={"limit": 101}).status_code == 400
    assert client.get(URL, params={"limit": 0}).status_code == 400
    assert [name for name, _ in service.calls] == ["list"]


def test_the_stale_409_carries_current_version_as_an_integer_and_the_head_etag(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    service.error = DocumentError(409, "STALE_REVISION", current_version=4, etag=f"{HASH}.DRAFT")
    for url, body in ((URL, good()), (CONFIRM_URL, confirm_body())):
        response = client.post(url, json=body, headers=headers())
        assert response.status_code == 409
        payload = response.json()
        assert payload["code"] == "STALE_REVISION" and payload["message"]
        assert payload["current_version"] == 4 and type(payload["current_version"]) is int
        assert response.headers["ETag"] == f'"{HASH}.DRAFT"'


def test_a_stale_head_of_zero_still_reports_the_version(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    service.error = DocumentError(409, "STALE_REVISION", current_version=0)
    response = client.post(URL, json=good(), headers=headers())
    assert response.status_code == 409 and response.json()["current_version"] == 0
    assert "ETag" not in response.headers


def test_the_checklist_refusal_is_400_with_field_errors_in_the_envelope(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    service.error = DocumentError(
        400,
        "INVALID_REQUEST",
        field_errors=[
            {"field": "checklist[2].items.synthetic_b", "code": "REQUIRED"},
            {"field": "checklist[4]", "code": "UNKNOWN_FIELD"},
            {"field": "checklist[1]", "code": "NOT_SUPPORTED"},
        ],
    )
    response = client.post(CONFIRM_URL, json=confirm_body(), headers=headers())
    assert response.status_code == 400
    assert response.json()["field_errors"] == [
        {"field": "checklist[1]", "code": "NOT_SUPPORTED"},
        {"field": "checklist[2].items.synthetic_b", "code": "REQUIRED"},
        {"field": "checklist[4]", "code": "UNKNOWN_FIELD"},
    ]


@pytest.mark.parametrize(
    ("status", "code"),
    [
        (404, "RESOURCE_NOT_FOUND"),
        (403, "ACTION_NOT_ALLOWED"),
        (409, "INVALID_STATE_TRANSITION"),
        (400, "INVALID_IDEMPOTENCY_KEY"),
        (503, "PROVIDER_UNAVAILABLE"),
    ],
)
def test_refusals_use_the_conv1_envelope_and_never_name_plan_not_approved(
    served: tuple[TestClient, FakeService], status: int, code: str
) -> None:
    client, service = served
    service.error = DocumentError(status, code)
    for response in (
        client.post(URL, json=good(), headers=headers()),
        client.post(CONFIRM_URL, json=confirm_body(), headers=headers()),
        client.get(f"{URL}/3"),
        client.get(URL),
    ):
        assert response.status_code == status
        body = response.json()
        assert body["code"] == code and body["message"]
        assert body["request_id"] == body["correlation_id"]
        assert body["code"] != "LESSON_PLAN_NOT_APPROVED"


def test_the_routes_need_a_bearer_token() -> None:
    with TestClient(create_app()) as client:
        for response in (
            client.post(URL, json=good(), headers=headers()),
            client.post(CONFIRM_URL, json=confirm_body(), headers=headers()),
            client.get(URL),
            client.get(f"{URL}/1"),
        ):
            assert response.status_code == 401 and response.json()["code"] == "AUTH_REQUIRED"


# ----------------------------------------------------------------------------- request size guard
def test_an_oversize_create_body_is_413_before_parsing_authorisation_or_the_service(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    body = b'{"teacher_direction":"' + b"a" * MAX_PLAN_CREATE_BODY_BYTES + b'"}'
    response = client.post(
        URL, content=body, headers={**headers(), "Content-Type": "application/json"}
    )
    assert response.status_code == 413
    payload = response.json()
    assert payload["code"] == "MEDIA_TOO_LARGE" and payload["message"]
    assert payload["request_id"] == response.headers["X-Request-ID"]
    assert service.calls == []


def test_an_oversize_confirm_body_is_413_and_a_create_sized_one_is_not_a_413_for_create(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    body = b'{"expected_plan_hash":"' + b"a" * MAX_PLAN_CONFIRM_BODY_BYTES + b'"}'
    response = client.post(
        CONFIRM_URL, content=body, headers={**headers(), "Content-Type": "application/json"}
    )
    assert response.status_code == 413 and response.json()["code"] == "MEDIA_TOO_LARGE"
    assert service.calls == []
    same_size_for_create = client.post(
        URL, content=body, headers={**headers(), "Content-Type": "application/json"}
    )
    assert same_size_for_create.status_code == 400  # a bad body, not a 413


def test_an_oversize_chunked_create_body_is_413_too(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    chunk = b"a" * (256 * 1024)

    def stream() -> Iterator[bytes]:
        yield b'{"teacher_direction":"'
        for _ in range(5):
            yield chunk
        yield b'"}'

    response = client.post(
        URL, content=stream(), headers={**headers(), "Content-Type": "application/json"}
    )
    assert response.status_code == 413
    assert response.json()["code"] == "MEDIA_TOO_LARGE"
    assert service.calls == []


def test_a_full_size_create_request_fits_under_the_cap(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    body = json.dumps(
        good(
            objectives=["\u0001" * 1000] * 12,
            teacher_direction="\u0001" * 2000,
            safety_notes="\u0001" * 2000,
            activities=[{"kind": "LESSON", "lesson_activity_id": "a" * 36}] * 24,
        )
    ).encode()
    assert len(body) <= MAX_PLAN_CREATE_BODY_BYTES
    response = client.post(
        URL, content=body, headers={**headers(), "Content-Type": "application/json"}
    )
    assert response.status_code == 201
    assert len(service.calls) == 1


def test_a_nul_in_the_document_id_is_a_400_before_the_service(
    served: tuple[TestClient, FakeService],
) -> None:
    client, service = served
    response = client.post(
        URL,
        json=good(document_revision_ref={"document_id": "a\x00b", "revision_no": 1}),
        headers=headers(),
    )
    assert response.status_code == 400
    assert response.json()["field_errors"] == [
        {"field": "document_revision_ref.document_id", "code": "INVALID_FORMAT"}
    ]
    assert service.calls == []
    path = client.post(
        "/v1/lesson-occurrences/a%00b/plan-revisions", json=good(), headers=headers()
    )
    assert path.status_code == 400 and path.json()["code"] == "INVALID_REQUEST"
    assert service.calls == []
