"""FEAT-066 T-1b: the ``video-unsuitable`` and ``complete`` route contracts (SRS l.1671-1672).

Offline: the real app with its real exception handlers, a fake database, a fake command service
and a fake run reader. Behaviour against PostgreSQL lives in
``tests/integration/story_video/test_video_commands_postgres.py``.
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
import sketch2life.interfaces.http.routers.story_run_video as video_routes
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryLifecycleRecord,
    ParentStoryRunError,
    ParentStoryRunRecord,
)
from sketch2life.application.ports.story_run_lifecycle import lifecycle_projection_body
from sketch2life.application.ports.story_video import RunCommandResult
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.interfaces.http.be1_runtime import get_db, get_runtime, get_verified_adult
from sketch2life.interfaces.http.openapi_contract import MOUNTED_OPERATIONS
from sketch2life.interfaces.http.openapi_srs_v22 import (
    SRS_V22_INCLUDED_OPERATIONS,
    SRS_V22_OPERATION_TAGS,
)

ISSUER = "issuer-1"
PRINCIPAL = VerifiedPrincipal("adult-1", ISSUER, frozenset())
RUN_ID = "22222222-2222-4222-8222-222222222222"
GEN_ID = "33333333-3333-4333-8333-333333333333"
UNSUITABLE = ("post", "/v1/story-runs/{run_id}/video-unsuitable")
COMPLETE = ("post", "/v1/story-runs/{run_id}/complete")
VOLATILE_KEYS = {"request_id", "correlation_id"}
STORAGE_WORDS = ("bucket", "object_key", "presigned", "amazonaws", "s3mock", "parent/", "output")
BODY = {"expected_revision": 6, "generation_id": GEN_ID, "reason_code": "QUALITY_LOW"}


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


def _run_record(run_state: str = "SCRIPT_REVIEW", revision: int = 8) -> ParentStoryRunRecord:
    now = datetime.now(UTC)
    return ParentStoryRunRecord(
        run_id=RUN_ID,
        run_state=run_state,
        run_revision=revision,
        parent_profile_id=UUID("11111111-1111-4111-8111-111111111111"),
        profile_revision_ref=UUID("44444444-4444-4444-8444-444444444444"),
        context_revision=1,
        context_confirmed=True,
        context_snapshot={
            "schema_version": "sketch2life.parent-context.v1",
            "profile_revision_ref": "44444444-4444-4444-8444-444444444444",
            "age_months": 72,
            "interests_summary": "",
            "topic": "",
            "adult_confirmed_idea": "",
        },
        context_snapshot_sha256="a" * 64,
        current_input_revision=1,
        understanding_revision=1,
        subject_label="dragon",
        candidate=None,
        story_revision_id=None,
        story_revision_no=None,
        story_status=None,
        story_sha256=None,
        story_content=None,
        job_state="SUCCEEDED",
        retryable=False,
        error_code=None,
        created_at=now,
        updated_at=now,
    )


class _Commands:
    outcome: Any = None
    calls: list[tuple[str, dict[str, Any]]] = []

    def __init__(self, repository: object) -> None:
        self.repository = repository

    def mark_unsuitable(self, **kwargs: Any) -> Any:
        return self._answer("mark_unsuitable", kwargs)

    def complete(self, **kwargs: Any) -> Any:
        return self._answer("complete", kwargs)

    def _answer(self, name: str, kwargs: dict[str, Any]) -> Any:
        type(self).calls.append((name, kwargs))
        if isinstance(type(self).outcome, BaseException):
            raise type(self).outcome
        return type(self).outcome


class _Reader:
    view: Any = None
    calls: list[dict[str, Any]] = []

    def __init__(self, db: object) -> None:
        self.db = db

    def get_run(self, **kwargs: Any) -> Any:
        type(self).calls.append(kwargs)
        if isinstance(type(self).view, BaseException):
            raise type(self).view
        return type(self).view


@pytest.fixture(autouse=True)
def _reset() -> None:
    _Commands.outcome = RunCommandResult(RUN_ID, False)
    _Commands.calls = []
    _Reader.view = _run_record()
    _Reader.calls = []


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    settings = Settings(
        env="test",
        auth_provider="firebase",
        firebase_project_id="synthetic-t1b-project",
        _env_file=None,  # type: ignore[call-arg]
    )
    monkeypatch.setattr(app_module, "get_settings", lambda: settings)
    monkeypatch.setattr(
        runtime_module, "get_core_database_settings", lambda: SimpleNamespace(database_url=None)
    )
    monkeypatch.setattr(video_routes, "StoryVideoCommandService", _Commands)
    monkeypatch.setattr(
        video_routes, "story_video_repository", lambda db, _actor: SimpleNamespace(db=db)
    )
    monkeypatch.setattr(video_routes, "story_run_repository", lambda db, _actor: _Reader(db))
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


def _unsuitable(
    client: TestClient, body: Any = None, *, key: str | None = "t1b-key-1", run: str = RUN_ID
) -> Any:
    headers = {} if key is None else {"Idempotency-Key": key}
    return client.post(
        f"/v1/story-runs/{run}/video-unsuitable",
        json=BODY if body is None else body,
        headers=headers,
    )


def _complete(
    client: TestClient, body: Any = None, *, key: str | None = "t1b-key-2", run: str = RUN_ID
) -> Any:
    headers = {} if key is None else {"Idempotency-Key": key}
    return client.post(
        f"/v1/story-runs/{run}/complete",
        json={"expected_revision": 6} if body is None else body,
        headers=headers,
    )


def _wire(response: Any) -> tuple[int, dict[str, Any]]:
    body = response.json()
    return response.status_code, {k: v for k, v in body.items() if k not in VOLATILE_KEYS}


# ------------------------------------------------------------------------- catalog
@pytest.mark.parametrize(
    ("operation", "handler"),
    [
        (UNSUITABLE, "story_run_video.py::mark_parent_video_unsuitable"),
        (COMPLETE, "story_run_video.py::complete_parent_story_run"),
    ],
)
def test_each_operation_is_catalogued_projected_and_tagged(
    operation: tuple[str, str], handler: str
) -> None:
    assert operation in MOUNTED_OPERATIONS
    assert operation in SRS_V22_INCLUDED_OPERATIONS
    assert SRS_V22_OPERATION_TAGS[operation] == "Parent StoryRuns"
    contract = MOUNTED_OPERATIONS[operation]
    assert contract["handler"] == handler
    assert {response["status"] for response in contract["responses"]} == {
        "200",
        "400",
        "401",
        "404",
        "409",
        "422",
        "503",
        "500",
    }
    assert "Idempotency-Key" in contract["request_inputs"]
    assert contract["authentication"] == "HTTPBearer (bearer)"


def test_the_published_requests_are_closed_and_name_no_owner_or_storage(
    client: TestClient,
) -> None:
    spec = client.app.openapi()  # type: ignore[attr-defined]
    schemas = spec["components"]["schemas"]
    unsuitable = schemas["ParentVideoUnsuitableRequestV1"]
    assert set(unsuitable["properties"]) == {"expected_revision", "generation_id", "reason_code"}
    assert set(unsuitable["required"]) == set(unsuitable["properties"])
    assert unsuitable["additionalProperties"] is False
    assert set(unsuitable["properties"]["reason_code"]["enum"]) == {
        "QUALITY_LOW",
        "NOT_MATCHING_STORY",
        "CONTENT_CONCERN",
        "OTHER",
    }
    complete = schemas["ParentStoryRunCompleteRequestV1"]
    assert set(complete["properties"]) == {"expected_revision"}
    assert complete["additionalProperties"] is False
    wire = json.dumps(
        {
            name: schemas[name]
            for name in (
                "ParentVideoUnsuitableRequestV1",
                "ParentStoryRunCompleteRequestV1",
            )
        }
    ).lower()
    for word in (*STORAGE_WORDS, "owner", "scope", "organization", "account", "url", "provider"):
        assert word not in wire, word
    for path in ("video-unsuitable", "complete"):
        operation = spec["paths"][f"/v1/story-runs/{{run_id}}/{path}"]["post"]
        assert operation["tags"] == ["Parent StoryRuns"]
        assert "200" in operation["responses"] and "202" not in operation["responses"]


# ------------------------------------------------------------------------- 200 shapes
def test_video_unsuitable_answers_200_with_the_run_back_in_script_review(
    client: TestClient,
) -> None:
    response = _unsuitable(client)
    status, body = _wire(response)
    assert status == 200 and set(body) == {"story_run"}
    assert body["story_run"]["run_state"] == "SCRIPT_REVIEW"
    assert body["story_run"]["run_revision"] == 8 and body["story_run"]["run_id"] == RUN_ID
    assert response.headers["Content-Location"] == f"/v1/story-runs/{RUN_ID}"
    assert _Commands.calls == [
        (
            "mark_unsuitable",
            {
                "principal": PRINCIPAL,
                "run_id": RUN_ID,
                "expected_revision": 6,
                "generation_id": GEN_ID,
                "reason_code": "QUALITY_LOW",
                "idempotency_key": "t1b-key-1",
            },
        )
    ]
    assert _Reader.calls == [{"principal": PRINCIPAL, "run_id": RUN_ID}]


def test_a_generation_id_in_capitals_reaches_the_service_normalised(client: TestClient) -> None:
    body = {**BODY, "generation_id": GEN_ID.upper()}
    assert _unsuitable(client, body).status_code == 200
    assert _Commands.calls[0][1]["generation_id"] == GEN_ID


def test_complete_answers_200_with_the_completed_run(client: TestClient) -> None:
    _Reader.view = _run_record("COMPLETED", 9)
    response = _complete(client)
    status, body = _wire(response)
    assert status == 200 and set(body) == {"story_run"}
    assert body["story_run"]["run_state"] == "COMPLETED" and body["story_run"]["run_revision"] == 9
    assert response.headers["Content-Location"] == f"/v1/story-runs/{RUN_ID}"
    assert _Commands.calls == [
        (
            "complete",
            {
                "principal": PRINCIPAL,
                "run_id": RUN_ID,
                "expected_revision": 6,
                "idempotency_key": "t1b-key-2",
            },
        )
    ]


@pytest.mark.parametrize("send", [_unsuitable, _complete])
def test_a_replay_on_a_run_being_deleted_is_the_content_free_projection(
    client: TestClient, send: Any
) -> None:
    projection = ParentStoryLifecycleRecord.from_body(
        lifecycle_projection_body(run_id=RUN_ID, run_state="DELETE_PENDING", revision=9, version=9)
    )
    _Commands.outcome = RunCommandResult(RUN_ID, True, projection)
    status, body = _wire(send(client))
    assert status == 200 and set(body) == {"lifecycle"}
    assert body["lifecycle"]["run_state"] == "DELETE_PENDING"
    assert _Reader.calls == []  # a purge replay never reads the run content
    assert "story_run" not in json.dumps(body)


@pytest.mark.parametrize("send", [_unsuitable, _complete])
def test_a_run_read_that_fails_after_the_commit_is_a_safe_story_error(
    client: TestClient, send: Any
) -> None:
    _Reader.view = ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE")
    response = send(client)
    assert response.status_code == 503
    assert response.json()["code"] == "PARENT_STORY_RUN_STORE_UNAVAILABLE"
    assert response.json()["retryable"] is True


def test_the_answers_carry_no_storage_word_or_url(client: TestClient) -> None:
    for send in (_unsuitable, _complete):
        text_body = send(client).text.lower()
        for word in (*STORAGE_WORDS, "http", "playback", "token"):
            assert word not in text_body, word


# ------------------------------------------------------------------------- errors
_ERRORS = [
    (ParentStoryRunError(404, "RESOURCE_NOT_FOUND"), 404, "RESOURCE_NOT_FOUND", False),
    (
        ParentStoryRunError(409, "INVALID_STATE_TRANSITION"),
        409,
        "INVALID_STATE_TRANSITION",
        False,
    ),
    (
        ParentStoryRunError(409, "VIDEO_REGENERATION_LIMIT_REACHED"),
        409,
        "VIDEO_REGENERATION_LIMIT_REACHED",
        False,
    ),
    (ParentStoryRunError(400, "INVALID_IDEMPOTENCY_KEY"), 400, "INVALID_IDEMPOTENCY_KEY", False),
]


@pytest.mark.parametrize("send", [_unsuitable, _complete])
@pytest.mark.parametrize(("error", "status", "code", "retryable"), _ERRORS)
def test_each_refusal_has_a_stable_code_a_safe_message_and_no_internals(
    client: TestClient,
    send: Any,
    error: ParentStoryRunError,
    status: int,
    code: str,
    retryable: bool,
) -> None:
    _Commands.outcome = error
    response = send(client)
    body = response.json()
    assert response.status_code == status
    assert body["code"] == code and body["retryable"] is retryable
    assert body["message"] and body["message"] != "Không thể hoàn tất yêu cầu."
    assert response.headers["X-Request-ID"] == body["correlation_id"]
    text = json.dumps(body).lower()
    for word in (*STORAGE_WORDS, "traceback", "reservation", "balance"):
        assert word not in text
    assert _Reader.calls == []


@pytest.mark.parametrize("send", [_unsuitable, _complete])
def test_a_stale_request_carries_the_current_version(client: TestClient, send: Any) -> None:
    _Commands.outcome = ParentStoryRunError(409, "STALE_REVISION", current_version=8)
    status, body = _wire(send(client))
    assert status == 409 and body["code"] == "STALE_REVISION" and body["current_version"] == 8


def test_an_unexpected_failure_is_a_plain_500_without_internals(client: TestClient) -> None:
    _Commands.outcome = RuntimeError("secret internal detail")
    response = _unsuitable(client)
    assert response.status_code == 500
    assert response.json()["code"] == "INTERNAL_SERVER_ERROR"
    assert "secret" not in response.text


# ------------------------------------------------------------------------- request checks
@pytest.mark.parametrize("send", [_unsuitable, _complete])
def test_a_missing_key_is_a_plain_400_without_a_service_call(client: TestClient, send: Any) -> None:
    status, body = _wire(send(client, key=None))
    assert status == 400 and body["code"] == "INVALID_REQUEST" and not body.get("field_errors")
    assert _Commands.calls == []


@pytest.mark.parametrize("path", ["video-unsuitable", "complete"])
@pytest.mark.parametrize("key", [" ", "k" * 129, "bad key", "kéy"])
def test_an_invalid_key_is_a_400_before_the_run_lookup(
    client: TestClient, path: str, key: str
) -> None:
    response = client.post(
        f"/v1/story-runs/{RUN_ID}/{path}",
        json=BODY if path == "video-unsuitable" else {"expected_revision": 6},
        headers={"Idempotency-Key": key.encode("utf-8")},  # type: ignore[arg-type]
    )
    assert response.status_code == 400 and response.json()["code"] == "INVALID_REQUEST"
    assert _Commands.calls == []


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"expected_revision": 6, "generation_id": GEN_ID},
        {"expected_revision": 6, "reason_code": "QUALITY_LOW"},
        {"generation_id": GEN_ID, "reason_code": "QUALITY_LOW"},
        {**BODY, "expected_revision": 0},
        {**BODY, "expected_revision": "6"},
        {**BODY, "generation_id": "not-a-uuid"},
        {**BODY, "generation_id": 7},
        {**BODY, "reason_code": "TOO_BAD"},
        {**BODY, "reason_code": "quality_low"},
        {**BODY, "reason_code": "free text about the child"},
        {**BODY, "extra": True},
        {**BODY, "owner": "someone-else"},
        {**BODY, "scope": "ORGANIZATION"},
    ],
)
def test_an_invalid_unsuitable_body_is_a_400_in_the_story_envelope(
    client: TestClient, body: Any
) -> None:
    status, payload = _wire(_unsuitable(client, body))
    assert status == 400 and payload["code"] == "INVALID_REQUEST"
    assert _Commands.calls == []


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"expected_revision": 0},
        {"expected_revision": "6"},
        {"expected_revision": 6, "extra": True},
        {"expected_revision": 6, "generation_id": GEN_ID},
        {"expected_revision": 6, "owner": "someone-else"},
    ],
)
def test_an_invalid_complete_body_is_a_400_in_the_story_envelope(
    client: TestClient, body: Any
) -> None:
    status, payload = _wire(_complete(client, body))
    assert status == 400 and payload["code"] == "INVALID_REQUEST"
    assert _Commands.calls == []


@pytest.mark.parametrize("send", [_unsuitable, _complete])
def test_a_malformed_run_id_is_a_400(client: TestClient, send: Any) -> None:
    status, body = _wire(send(client, run="not-a-uuid"))
    assert status == 400 and body["code"] == "INVALID_REQUEST"
    assert _Commands.calls == []


# ------------------------------------------------------------------------- roles and methods
@pytest.mark.parametrize("send", [_unsuitable, _complete])
@pytest.mark.parametrize("role", ["school_manager", "platform_admin", None])
def test_a_role_that_is_neither_an_active_parent_nor_teacher_gets_the_uniform_404(
    client: TestClient, send: Any, role: str | None
) -> None:
    client.app.dependency_overrides[get_db] = lambda: _Db(role)  # type: ignore[attr-defined]
    response = send(client)
    assert response.status_code == 404 and response.json()["code"] == "RESOURCE_NOT_FOUND"
    assert _Commands.calls == [] and _Reader.calls == []


@pytest.mark.parametrize("send", [_unsuitable, _complete])
def test_a_disabled_parent_or_another_issuer_gets_the_uniform_404(
    client: TestClient, send: Any
) -> None:
    for db in (
        _Db("parent", state="disabled"),
        _Db("parent", issuer="other-issuer"),
        _Db("teacher", state="disabled"),
        _Db("teacher", issuer="other-issuer"),
    ):
        client.app.dependency_overrides[get_db] = lambda db=db: db  # type: ignore[attr-defined]
        response = send(client)
        assert response.status_code == 404 and response.json()["code"] == "RESOURCE_NOT_FOUND"
    assert _Commands.calls == []


@pytest.mark.parametrize("path", ["video-unsuitable", "complete"])
def test_the_only_method_on_each_path_is_post(client: TestClient, path: str) -> None:
    for method in ("get", "put", "patch", "delete"):
        response = getattr(client, method)(f"/v1/story-runs/{RUN_ID}/{path}")
        assert response.status_code in {404, 405}, method
