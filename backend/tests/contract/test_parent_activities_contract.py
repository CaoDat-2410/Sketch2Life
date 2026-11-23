"""FEAT-066 goal v4 T-2e-a: ``GET /v1/activities`` and ``POST .../activity-selection`` contracts.

Offline: the real app with its real exception handlers, a fake database and a fake service. The
behaviour against PostgreSQL lives in
``tests/integration/test_parent_activity_selection_postgres.py``.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

import sketch2life.interfaces.http.app as app_module
import sketch2life.interfaces.http.be1_runtime as runtime_module
import sketch2life.interfaces.http.routers.parent_story_activities as activity_routes
import sketch2life.interfaces.http.routers.parent_story_inputs as input_routes
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryLifecycleRecord,
    ParentStoryRevisionReservation,
    ParentStoryRunError,
    ParentStoryRunRecord,
)
from sketch2life.application.ports.story_run_lifecycle import lifecycle_projection_body
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.lesson_library.service import LessonLibraryError
from sketch2life.interfaces.http.be1_runtime import get_db, get_runtime, get_verified_adult
from sketch2life.interfaces.http.openapi_contract import MOUNTED_OPERATIONS
from sketch2life.interfaces.http.openapi_srs_v22 import (
    SRS_V22_INCLUDED_OPERATIONS,
    SRS_V22_OPERATION_TAGS,
)

ISSUER = "issuer-1"
PRINCIPAL = VerifiedPrincipal("adult-1", ISSUER, frozenset())
RUN_ID = "22222222-2222-4222-8222-222222222222"
UNKNOWN_ID = "00000000-0000-0000-0000-000000000000"
LIST_OPERATION = ("get", "/v1/activities")
SELECT_OPERATION = ("post", "/v1/story-runs/{run_id}/activity-selection")
HASH = "a" * 64
STORAGE_WORDS = ("bucket", "object_key", "presigned", "amazonaws", "s3mock", "parent/")
REF = {
    "lesson_id": "lesson-1",
    "version_id": "version-1",
    "content_sha256": HASH,
    "activity_index": 0,
}
ACTIVITY = {
    "activity_ref": REF,
    "title": "Tim la cay",
    "objective": "Quan sat la cay ngoai san",
    "materials_text": "",
    "preparation_text": "",
    "instructions_text": "Cung tre di tim la cay",
    "observation_notes": "",
    "safety_notes": "Di cung nguoi lon",
    "activity_kind": "outdoor",
    "source": "PUBLIC",
    "lesson_title": "Thien nhien",
    "lesson_topic": "la cay",
}


class _Db:
    def __init__(self, role: str | None, *, state: str = "active", issuer: str = ISSUER) -> None:
        self._identity = (
            None
            if role is None
            else SimpleNamespace(
                account_id="account-1", issuer=issuer, account_role=role, state=state
            )
        )

    def get(self, _model: object, _key: object) -> Any:
        return self._identity


def _record(**changes: Any) -> ParentStoryRunRecord:
    now = datetime(2026, 11, 22, tzinfo=UTC)
    values: dict[str, Any] = {
        "run_id": RUN_ID,
        "run_state": "PREPARATION_REVIEW",
        "run_revision": 6,
        "parent_profile_id": UUID("33333333-3333-4333-8333-333333333333"),
        "profile_revision_ref": UUID("44444444-4444-4444-8444-444444444444"),
        "context_revision": 1,
        "context_confirmed": False,
        "context_snapshot": {
            "schema_version": "sketch2life.parent-context.v1",
            "profile_revision_ref": "44444444-4444-4444-8444-444444444444",
            "age_months": 60,
            "interests_summary": "",
            "topic": "",
            "adult_confirmed_idea": "",
        },
        "context_snapshot_sha256": HASH,
        "current_input_revision": 1,
        "understanding_revision": 1,
        "subject_label": "rong",
        "candidate": None,
        "story_revision_id": None,
        "story_revision_no": None,
        "story_status": None,
        "story_sha256": None,
        "story_content": None,
        "job_state": "SUCCEEDED",
        "retryable": False,
        "error_code": None,
        "created_at": now,
        "updated_at": now,
        "main_activity": {
            "state": "SELECTED",
            "selected": ACTIVITY,
            "selected_at": "2026-11-22T10:00:00+00:00",
        },
    }
    values.update(changes)
    return ParentStoryRunRecord(**values)


def _reservation() -> ParentStoryRevisionReservation:
    return ParentStoryRevisionReservation(
        run_id=RUN_ID,
        story_revision_id="rev-1",
        revision_no=1,
        understanding_revision=1,
        context_revision=1,
        source_asset_sha256=HASH,
        worker_input={"confirmed_subject": "rong"},
        request_sha256=HASH,
        receipt_id=None,
    )


class _Service:
    list_result: Any = None
    select_result: Any = None
    start: ParentStoryRevisionReservation | None = None
    calls: list[tuple[str, dict[str, Any]]] = []

    def list_activities(self, **kwargs: Any) -> Any:
        type(self).calls.append(("list", kwargs))
        if isinstance(type(self).list_result, BaseException):
            raise type(self).list_result
        return type(self).list_result

    def select_activity(self, **kwargs: Any) -> Any:
        type(self).calls.append(("select", kwargs))
        if isinstance(type(self).select_result, BaseException):
            raise type(self).select_result
        if type(self).start is not None:
            kwargs["on_story_started"](type(self).start)
        return type(self).select_result


class _Runner:
    scheduled: list[tuple[Any, ...]] = []

    def __init__(self, session_factory: object, generator: object) -> None:
        self.generator = generator

    def run(self, *args: Any) -> None:
        type(self).scheduled.append(args)


@pytest.fixture(autouse=True)
def _reset() -> Iterator[None]:
    _Service.list_result = {
        "items": [ACTIVITY],
        "basis": {"age_band": "36-71", "pinned_lesson": False, "no_candidate": False},
    }
    _Service.select_result = _record()
    _Service.start = None
    _Service.calls = []
    _Runner.scheduled = []
    yield


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    settings = Settings(
        env="test",
        auth_provider="firebase",
        firebase_project_id="synthetic-t2ea-project",
        _env_file=None,  # type: ignore[call-arg]
    )
    monkeypatch.setattr(app_module, "get_settings", lambda: settings)
    monkeypatch.setattr(
        runtime_module, "get_core_database_settings", lambda: SimpleNamespace(database_url=None)
    )
    monkeypatch.setattr(activity_routes, "_selection_service", lambda _request, _db: _Service())
    monkeypatch.setattr(input_routes, "ParentStoryRewriteRunner", _Runner)
    application = app_module.create_app()
    application.dependency_overrides[get_verified_adult] = lambda: PRINCIPAL
    application.dependency_overrides[get_db] = lambda: _Db("parent")
    application.dependency_overrides[get_runtime] = lambda: SimpleNamespace(
        settings=SimpleNamespace(env="test", synthetic_pilot_enabled=True), session_factory=None
    )
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    try:
        with TestClient(application, raise_server_exceptions=False) as test_client:
            yield test_client
    finally:
        application.dependency_overrides.clear()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _use_db(client: TestClient, db: _Db) -> None:
    client.app.dependency_overrides[get_db] = lambda: db  # type: ignore[attr-defined]


def _list(client: TestClient, run: str = RUN_ID) -> Any:
    return client.get("/v1/activities", params={"story_run_id": run})


def _select(
    client: TestClient, body: Any = None, *, key: str | None = "t2ea-key-1", run: str = RUN_ID
) -> Any:
    headers = {} if key is None else {"Idempotency-Key": key}
    payload = {"expected_revision": 5, "activity": REF} if body is None else body
    return client.post(f"/v1/story-runs/{run}/activity-selection", json=payload, headers=headers)


def _compose(client: TestClient, **state: Any) -> None:
    for name, value in state.items():
        setattr(client.app.state, name, value)  # type: ignore[attr-defined]


# ------------------------------------------------------------------------- catalog
@pytest.mark.parametrize(
    ("operation", "handler", "success"),
    [
        (LIST_OPERATION, "parent_story_activities.py::list_parent_activities", "200"),
        (SELECT_OPERATION, "parent_story_activities.py::select_parent_story_activity", "200"),
    ],
)
def test_the_operations_are_catalogued_projected_and_tagged(
    operation: tuple[str, str], handler: str, success: str
) -> None:
    assert operation in MOUNTED_OPERATIONS
    assert operation in SRS_V22_INCLUDED_OPERATIONS
    assert SRS_V22_OPERATION_TAGS[operation] == "Parent StoryRuns"
    contract = MOUNTED_OPERATIONS[operation]
    assert contract["handler"] == handler
    assert {response["status"] for response in contract["responses"]} == {
        success,
        "400",
        "401",
        "404",
        "409",
        "422",
        "503",
        "500",
    }


def test_the_published_contract_has_the_shapes_and_no_storage_words(client: TestClient) -> None:
    spec = client.app.openapi()  # type: ignore[attr-defined]
    listing = spec["paths"]["/v1/activities"]["get"]
    assert listing["tags"] == ["Parent StoryRuns"]
    assert [p["name"] for p in listing["parameters"]] == ["story_run_id"]  # no cursor, no limit
    assert "404" in listing["responses"] and "403" not in listing["responses"]
    selection = spec["paths"]["/v1/story-runs/{run_id}/activity-selection"]["post"]
    key = next(p for p in selection["parameters"] if p["name"] == "Idempotency-Key")
    assert key["required"] is True and key["schema"]["maxLength"] == 128
    assert "200" in selection["responses"] and "202" not in selection["responses"]
    schemas = spec["components"]["schemas"]
    assert set(schemas["ParentActivityListV1"]["properties"]) == {"request_id", "items", "basis"}
    assert schemas["ParentActivityListV1"]["properties"]["items"]["maxItems"] == 12
    assert set(schemas["ParentActivitySelectionRequestV1"]["properties"]) == {
        "expected_revision",
        "activity",
    }
    assert schemas["ParentActivitySelectionRequestV1"]["additionalProperties"] is False
    assert set(schemas["ParentActivityRefV1"]["properties"]) == set(REF)
    assert {"main_activity", "post_video_activities"} <= set(
        schemas["ParentStoryRunResponseV1"]["properties"]
    )
    wire = json.dumps(
        {
            name: schemas[name]
            for name in (
                "ParentActivityListV1",
                "ParentActivityV1",
                "ParentActivityRefV1",
                "ParentActivitySelectionRequestV1",
                "ParentMainActivityV1",
                "ParentPostVideoActivityV1",
            )
        }
    ).lower()
    for word in STORAGE_WORDS:
        assert word not in wire, word


# ------------------------------------------------------------------------- the list
def test_the_list_is_the_bounded_recommendation_with_its_basis(client: TestClient) -> None:
    response = _list(client)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"request_id", "items", "basis"}
    assert body["items"] == [ACTIVITY]
    assert body["basis"] == {"age_band": "36-71", "pinned_lesson": False, "no_candidate": False}
    assert _Service.calls == [("list", {"principal": PRINCIPAL, "run_id": RUN_ID})]
    assert "X-Request-ID" in response.headers


def test_no_candidate_is_an_empty_list_not_an_error(client: TestClient) -> None:
    _Service.list_result = {
        "items": [],
        "basis": {"age_band": "72-107", "pinned_lesson": False, "no_candidate": True},
    }
    body = _list(client).json()
    assert body["items"] == [] and body["basis"]["no_candidate"] is True


@pytest.mark.parametrize(
    ("error", "status", "code"),
    [
        (ParentStoryRunError(409, "INVALID_STATE_TRANSITION"), 409, "INVALID_STATE_TRANSITION"),
        (ParentStoryRunError(422, "SUBJECT_NOT_CONFIRMED"), 422, "SUBJECT_NOT_CONFIRMED"),
        (ParentStoryRunError(404, "RESOURCE_NOT_FOUND"), 404, "RESOURCE_NOT_FOUND"),
        (
            ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE"),
            503,
            "PARENT_STORY_RUN_STORE_UNAVAILABLE",
        ),
        (LessonLibraryError(404, "LESSON_NOT_FOUND", "x"), 404, "RESOURCE_NOT_FOUND"),
    ],
)
def test_the_list_errors_use_the_story_envelope(
    client: TestClient, error: BaseException, status: int, code: str
) -> None:
    _Service.list_result = error
    response = _list(client)
    assert response.status_code == status
    body = response.json()
    assert body["code"] == code and "correlation_id" in body and "message" in body


def test_a_run_query_that_is_not_a_uuid_is_a_plain_400_in_the_story_envelope(
    client: TestClient,
) -> None:
    response = client.get("/v1/activities", params={"story_run_id": "not-a-uuid"})
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"
    assert client.get("/v1/activities").status_code == 400


@pytest.mark.parametrize("role", ["teacher", "school_manager", "platform_admin", "child", None])
def test_every_other_role_and_an_unknown_account_get_the_uniform_404(
    client: TestClient, role: str | None
) -> None:
    _use_db(client, _Db(role))
    for response in (_list(client), _select(client)):
        assert response.status_code == 404
        assert response.json()["code"] == "RESOURCE_NOT_FOUND"
    assert _Service.calls == []


@pytest.mark.parametrize("db", [_Db("parent", state="suspended"), _Db("parent", issuer="other")])
def test_an_inactive_parent_or_another_issuer_gets_the_uniform_404(
    client: TestClient, db: _Db
) -> None:
    _use_db(client, db)
    assert _list(client).status_code == 404
    assert _select(client).status_code == 404
    assert _Service.calls == []


# ------------------------------------------------------------------------- the selection
def test_a_selection_answers_200_with_the_run_envelope_and_main_activity(
    client: TestClient,
) -> None:
    response = _select(client)
    assert response.status_code == 200
    run = response.json()["story_run"]
    assert run["run_id"] == RUN_ID and run["run_revision"] == 6
    assert run["main_activity"]["state"] == "SELECTED"
    assert run["main_activity"]["selected"]["activity_ref"] == REF
    assert "story_run_id" not in run
    kind, call = _Service.calls[0]
    assert kind == "select"
    assert call["run_id"] == RUN_ID and call["expected_revision"] == 5
    assert call["idempotency_key"] == "t2ea-key-1"
    assert call["activity_ref"] == REF


def test_a_run_without_a_selection_reports_not_selected(client: TestClient) -> None:
    _Service.select_result = _record(
        main_activity={"state": "NOT_SELECTED", "selected": None, "selected_at": None}
    )
    run = _select(client).json()["story_run"]
    assert run["main_activity"] == {"state": "NOT_SELECTED", "selected": None, "selected_at": None}
    assert run["post_video_activities"] is None


def test_a_missing_or_invalid_key_is_a_plain_400_invalid_request(client: TestClient) -> None:
    for key in (None, "", "k" * 129, "bad key with spaces"):
        response = _select(client, key=key)
        assert response.status_code == 400, key
        body = response.json()
        assert body["code"] == "INVALID_REQUEST"
        assert not body.get("field_errors")
    assert _Service.calls == []


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"expected_revision": 0, "activity": REF},
        {"expected_revision": 5},
        {"expected_revision": 5, "activity": {**REF, "activity_index": -1}},
        {"expected_revision": 5, "activity": {**REF, "content_sha256": "zz"}},
        {"expected_revision": 5, "activity": {**REF, "extra": 1}},
        {"expected_revision": 5, "activity": REF, "extra": 1},
    ],
)
def test_a_bad_body_is_400_and_never_reaches_the_service(client: TestClient, body: Any) -> None:
    response = _select(client, body)
    assert response.status_code == 400 and response.json()["code"] == "INVALID_REQUEST"
    assert _Service.calls == []


def test_a_stale_revision_carries_current_version(client: TestClient) -> None:
    _Service.select_result = ParentStoryRunError(409, "STALE_REVISION", current_version=8)
    response = _select(client)
    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "STALE_REVISION" and body["current_version"] == 8


@pytest.mark.parametrize(
    ("error", "status", "code"),
    [
        (ParentStoryRunError(409, "INVALID_STATE_TRANSITION"), 409, "INVALID_STATE_TRANSITION"),
        (ParentStoryRunError(422, "SUBJECT_NOT_CONFIRMED"), 422, "SUBJECT_NOT_CONFIRMED"),
        (ParentStoryRunError(404, "RESOURCE_NOT_FOUND"), 404, "RESOURCE_NOT_FOUND"),
        (ParentStoryRunError(400, "INVALID_IDEMPOTENCY_KEY"), 400, "INVALID_IDEMPOTENCY_KEY"),
        (LessonLibraryError(404, "LESSON_NOT_FOUND", "x"), 404, "RESOURCE_NOT_FOUND"),
    ],
)
def test_the_selection_errors_use_the_story_envelope(
    client: TestClient, error: BaseException, status: int, code: str
) -> None:
    _Service.select_result = error
    response = _select(client)
    assert response.status_code == status and response.json()["code"] == code


def test_the_replay_of_a_purged_run_is_the_lifecycle_projection(client: TestClient) -> None:
    _Service.select_result = ParentStoryLifecycleRecord.from_body(
        {
            **lifecycle_projection_body(
                run_id=RUN_ID, run_state="DELETE_PENDING", revision=7, version=9
            ),
        }
    )
    response = _select(client)
    assert response.status_code == 200
    assert set(response.json()) == {"request_id", "lifecycle"}


def test_a_started_story_is_generated_after_the_response_when_a_generator_is_composed(
    client: TestClient,
) -> None:
    _Service.start = _reservation()
    _compose(client, story_generator=None)
    assert _select(client).status_code == 200
    assert _Runner.scheduled == []  # nothing composed: the run waits in SCRIPT_GENERATING
    _compose(
        client,
        story_generator=object(),
        be1_runtime=SimpleNamespace(session_factory=lambda: None),
    )
    assert _select(client).status_code == 200
    assert len(_Runner.scheduled) == 1
    assert _Runner.scheduled[0][0] == PRINCIPAL and len(_Runner.scheduled[0]) == 2
    assert _Runner.scheduled[0][1].worker_input == {"confirmed_subject": "rong"}
    _Service.start = None  # a replay or a start that is not ready collects nothing
    assert _select(client).status_code == 200
    assert len(_Runner.scheduled) == 1
