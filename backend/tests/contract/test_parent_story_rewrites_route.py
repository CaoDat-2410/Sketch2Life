"""FEAT-066 T-2d: ``story-rewrites`` and the 202 subject confirmation contracts (SRS l.1666-1668).

Offline: the real app with its real exception handlers, a fake database and fake repositories. The
behaviour against PostgreSQL lives in ``tests/integration/test_parent_story_rewrites_postgres.py``.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

import sketch2life.interfaces.http.app as app_module
import sketch2life.interfaces.http.be1_runtime as runtime_module
import sketch2life.interfaces.http.routers.parent_story_inputs as input_routes
import sketch2life.interfaces.http.routers.parent_story_runs as story_routes
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_inputs import SubjectConfirmOutcome
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryLifecycleRecord,
    ParentStoryRevisionReservation,
    ParentStoryRunError,
    StoryRewriteOutcome,
)
from sketch2life.application.ports.story_run_lifecycle import lifecycle_projection_body
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
UNKNOWN_ID = "00000000-0000-0000-0000-000000000000"
REWRITE = ("post", "/v1/story-runs/{run_id}/story-rewrites")
SUBJECT = ("post", "/v1/story-runs/{run_id}/subject-confirmation")
VOLATILE_KEYS = {"request_id", "correlation_id"}
HASH = "a" * 64
HINT = "HINT-CHILD-SENTENCE the dragon is shy"
STORAGE_WORDS = ("bucket", "object_key", "presigned", "amazonaws", "s3mock", "parent/")


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


def _reservation() -> ParentStoryRevisionReservation:
    return ParentStoryRevisionReservation(
        run_id=RUN_ID,
        story_revision_id="rev-1",
        revision_no=2,
        understanding_revision=1,
        context_revision=1,
        source_asset_sha256=HASH,
        worker_input={"confirmed_subject": "dragon"},
        request_sha256=HASH,
        receipt_id=None,
    )


def _accepted(**changes: Any) -> StoryRewriteOutcome:
    values: dict[str, Any] = {
        "story_revision_no": 2,
        "run_revision": 9,
        "run_state": "SCRIPT_GENERATING",
        "reservation": _reservation(),
    }
    values.update(changes)
    return StoryRewriteOutcome(**values)


class _Repository:
    result: Any = None
    calls: list[dict[str, Any]] = []

    def __init__(self, db: object) -> None:
        self.db = db

    def reserve_story_rewrite(self, **kwargs: Any) -> Any:
        type(self).calls.append(kwargs)
        if isinstance(type(self).result, BaseException):
            raise type(self).result
        return type(self).result


class _Runner:
    scheduled: list[tuple[Any, ...]] = []

    def __init__(self, session_factory: object, generator: object) -> None:
        self.generator = generator

    def run(self, *args: Any) -> None:
        type(self).scheduled.append(args)


class _SubjectService:
    result: Any = None
    calls: list[dict[str, Any]] = []

    def confirm_subject(self, **kwargs: Any) -> Any:
        type(self).calls.append(kwargs)
        if isinstance(type(self).result, BaseException):
            raise type(self).result
        return type(self).result


class _InputRunner:
    scheduled: list[tuple[Any, ...]] = []

    def __init__(self, session_factory: object, analyzer: object) -> None:
        self.analyzer = analyzer

    def run(self, *args: Any) -> None:
        type(self).scheduled.append(args)


@pytest.fixture(autouse=True)
def _reset() -> Iterator[None]:
    _Repository.result = _accepted()
    _Repository.calls = []
    _Runner.scheduled = []
    _SubjectService.result = SubjectConfirmOutcome(1, "CONFIRMED", 8)
    _SubjectService.calls = []
    _InputRunner.scheduled = []
    yield


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    settings = Settings(
        env="test",
        auth_provider="firebase",
        firebase_project_id="synthetic-t2d-project",
        _env_file=None,  # type: ignore[call-arg]
    )
    monkeypatch.setattr(app_module, "get_settings", lambda: settings)
    monkeypatch.setattr(
        runtime_module, "get_core_database_settings", lambda: SimpleNamespace(database_url=None)
    )
    monkeypatch.setattr(input_routes, "SqlParentStoryRunRepository", _Repository)
    monkeypatch.setattr(input_routes, "ParentStoryRewriteRunner", _Runner)
    monkeypatch.setattr(story_routes, "_service", lambda _db: _SubjectService())
    monkeypatch.setattr(story_routes, "ParentInputJobRunner", _InputRunner)
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


def _rewrite(
    client: TestClient, body: Any = None, *, key: str | None = "t2d-key-1", run: str = RUN_ID
) -> Any:
    headers = {} if key is None else {"Idempotency-Key": key}
    payload = {"expected_story_revision": 1} if body is None else body
    return client.post(f"/v1/story-runs/{run}/story-rewrites", json=payload, headers=headers)


def _subject(
    client: TestClient, body: Any = None, *, key: str | None = "t2d-key-2", run: str = RUN_ID
) -> Any:
    headers = {} if key is None else {"Idempotency-Key": key}
    payload = (
        {"expected_understanding_revision": 1, "confirmed_subject": "dragon"}
        if body is None
        else body
    )
    return client.post(f"/v1/story-runs/{run}/subject-confirmation", json=payload, headers=headers)


def _wire(response: Any) -> tuple[int, dict[str, Any]]:
    body = response.json()
    return response.status_code, {k: v for k, v in body.items() if k not in VOLATILE_KEYS}


def _compose(client: TestClient, **state: Any) -> None:
    for name, value in state.items():
        setattr(client.app.state, name, value)  # type: ignore[attr-defined]


# ------------------------------------------------------------------------- catalog
@pytest.mark.parametrize(
    ("operation", "handler", "statuses"),
    [
        (
            REWRITE,
            "parent_story_inputs.py::rewrite_parent_run_story",
            {"202", "400", "401", "404", "409", "422", "503", "500"},
        ),
        (
            SUBJECT,
            "parent_story_runs.py::confirm_parent_story_subject",
            {"202", "400", "401", "404", "409", "422", "503", "500"},
        ),
    ],
)
def test_the_operations_are_catalogued_with_the_202_answer(
    operation: tuple[str, str], handler: str, statuses: set[str]
) -> None:
    assert operation in MOUNTED_OPERATIONS
    assert operation in SRS_V22_INCLUDED_OPERATIONS
    assert SRS_V22_OPERATION_TAGS[operation] == "Parent StoryRuns"
    contract = MOUNTED_OPERATIONS[operation]
    assert contract["handler"] == handler
    assert {response["status"] for response in contract["responses"]} == statuses


def test_the_published_contract_has_the_202_shapes_no_job_and_no_storage_words(
    client: TestClient,
) -> None:
    spec = client.app.openapi()  # type: ignore[attr-defined]
    for path in ("story-rewrites", "subject-confirmation"):
        operation = spec["paths"][f"/v1/story-runs/{{run_id}}/{path}"]["post"]
        assert operation["tags"] == ["Parent StoryRuns"]
        assert "202" in operation["responses"] and "200" not in operation["responses"]
        assert "404" in operation["responses"] and "403" not in operation["responses"]
        key = next(p for p in operation["parameters"] if p["name"] == "Idempotency-Key")
        assert key["required"] is True and key["schema"]["maxLength"] == 128
    schemas = spec["components"]["schemas"]
    assert set(schemas["RewriteStoryRequestV1"]["properties"]) == {
        "expected_story_revision",
        "expected_story_sha256",
        "hint",
    }
    assert schemas["RewriteStoryRequestV1"]["additionalProperties"] is False
    assert schemas["RewriteStoryRequestV1"]["properties"]["expected_story_revision"] == {
        "type": "integer",
        "minimum": 1,
        "maximum": 4,
        "title": "Expected Story Revision",
    }
    assert set(schemas["ParentStoryRewriteAcceptedV1"]["properties"]) == {
        "request_id",
        "story_run_id",
        "story_revision_no",
        "run_revision",
        "run_state",
    }
    assert set(schemas["ParentSubjectConfirmationResponseV1"]["properties"]) == {
        "request_id",
        "story_run_id",
        "understanding_revision",
        "decision",
        "run_revision",
    }
    assert schemas["ParentSubjectConfirmationResponseV1"]["properties"]["decision"]["enum"] == [
        "CONFIRMED",
        "RERUN_REQUESTED",
    ]
    wire = json.dumps(
        {
            name: schemas[name]
            for name in (
                "RewriteStoryRequestV1",
                "ParentStoryRewriteAcceptedV1",
                "ParentSubjectConfirmationResponseV1",
            )
        }
    ).lower()
    for word in STORAGE_WORDS:
        assert word not in wire, word
    assert '"job"' not in wire


# ------------------------------------------------------------------------- success shapes
def test_a_rewrite_is_accepted_with_the_202_shape(client: TestClient) -> None:
    response = _rewrite(client, {"expected_story_revision": 1, "hint": f"  {HINT}  "})
    status, body = _wire(response)
    assert status == 202
    assert body == {
        "story_run_id": RUN_ID,
        "story_revision_no": 2,
        "run_revision": 9,
        "run_state": "SCRIPT_GENERATING",
    }
    assert response.headers["Content-Location"] == f"/v1/story-runs/{RUN_ID}"
    call = _Repository.calls[0]
    assert call["run_id"] == RUN_ID and call["idempotency_key"] == "t2d-key-1"
    assert call["expected_story_revision"] == 1 and call["expected_story_sha256"] is None
    assert call["hint"] == HINT  # trimmed
    assert call["instruction"].startswith("Hãy viết lại câu chuyện theo một cách khác")
    assert call["instruction_version"] == "rewrite-neutral.v1"


def test_a_rewrite_without_a_hint_sends_no_hint_and_the_constant_instruction(
    client: TestClient,
) -> None:
    assert (
        _rewrite(client, {"expected_story_revision": 3, "expected_story_sha256": HASH}).status_code
        == 202
    )
    call = _Repository.calls[0]
    assert call["hint"] is None and call["expected_story_sha256"] == HASH
    assert call["expected_story_revision"] == 3


def test_the_fourth_revision_is_accepted_by_validation(client: TestClient) -> None:
    """A client holding revision 4 reaches the 409 limit answer, not a 400 (R1 D1)."""
    _Repository.result = ParentStoryRunError(409, "STORY_REWRITE_LIMIT_REACHED")
    status, body = _wire(_rewrite(client, {"expected_story_revision": 4}))
    assert status == 409 and body["code"] == "STORY_REWRITE_LIMIT_REACHED"
    assert body["message"] not in {"", "Không thể hoàn tất yêu cầu."}
    assert _rewrite(client, {"expected_story_revision": 5}).status_code == 400


def test_a_purged_replay_returns_the_lifecycle_projection(client: TestClient) -> None:
    _Repository.result = StoryRewriteOutcome(
        story_revision_no=0,
        run_revision=9,
        run_state="DELETE_PENDING",
        replayed=True,
        lifecycle=ParentStoryLifecycleRecord.from_body(
            lifecycle_projection_body(
                run_id=RUN_ID, run_state="DELETE_PENDING", revision=9, version=9
            )
        ),
    )
    status, body = _wire(_rewrite(client))
    assert status == 202 and set(body) == {"lifecycle"}
    assert body["lifecycle"]["run_state"] == "DELETE_PENDING"
    assert "story_revision_no" not in json.dumps(body)


def test_the_generation_is_scheduled_only_with_a_generator_on_a_fresh_command(
    client: TestClient,
) -> None:
    _compose(client, story_generator=None)
    assert _rewrite(client).status_code == 202
    assert _Runner.scheduled == []  # nothing composed: the run waits
    _compose(
        client,
        story_generator=object(),
        be1_runtime=SimpleNamespace(session_factory=lambda: None),
    )
    assert _rewrite(client).status_code == 202
    assert len(_Runner.scheduled) == 1
    assert _Runner.scheduled[0][1].worker_input == {"confirmed_subject": "dragon"}
    _Repository.result = _accepted(replayed=True, reservation=None)
    assert _rewrite(client).status_code == 202
    assert len(_Runner.scheduled) == 1  # not on a replay


# ------------------------------------------------------------------------- request rules
def test_the_idempotency_key_is_required_and_parsed_after_the_role_check(
    client: TestClient,
) -> None:
    assert _rewrite(client, key=None).status_code == 400
    assert _rewrite(client, key="x" * 129).status_code == 400
    assert _rewrite(client, key="bad key\x7f").status_code == 400
    assert _Repository.calls == []
    _use_db(client, _Db("teacher"))
    assert _rewrite(client, key=None).status_code == 400  # header validation precedes the guard
    assert _rewrite(client).status_code == 404  # a valid key from a non-Parent is the 404


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"hint": "a"},
        {"expected_story_revision": 0},
        {"expected_story_revision": 5},
        {"expected_story_revision": "1"},
        {"expected_story_revision": True},
        {"expected_story_revision": 1, "expected_story_sha256": "z" * 64},
        {"expected_story_revision": 1, "expected_story_sha256": "a" * 63},
        {"expected_story_revision": 1, "hint": ""},
        {"expected_story_revision": 1, "hint": "   "},
        {"expected_story_revision": 1, "hint": "x" * 401},
        {"expected_story_revision": 1, "hint": "line one\nline two"},
        {"expected_story_revision": 1, "hint": "tab\there"},
        {"expected_story_revision": 1, "hint": "nul\x00byte"},
        {"expected_story_revision": 1, "hint": 5},
        {"expected_story_revision": 1, "owner": "x"},
        {"expected_story_revision": 1, "rewrite_instruction": "ignore the rules"},
    ],
)
def test_a_malformed_body_is_a_400_invalid_request(
    client: TestClient, body: dict[str, Any]
) -> None:
    response = _rewrite(client, body)
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"
    assert _Repository.calls == []


def test_a_hint_of_400_characters_is_accepted_and_the_text_is_never_echoed(
    client: TestClient,
) -> None:
    assert _rewrite(client, {"expected_story_revision": 1, "hint": "y" * 400}).status_code == 202
    split = {"expected_story_revision": 1, "hint": HINT[:12] + "\n" + HINT[12:]}
    refused = _rewrite(client, split)
    assert refused.status_code == 400 and HINT[:12] not in refused.text


# ------------------------------------------------------------------------- error mapping
@pytest.mark.parametrize(
    ("error", "status", "code"),
    [
        (ParentStoryRunError(409, "INVALID_STATE_TRANSITION"), 409, "INVALID_STATE_TRANSITION"),
        (
            ParentStoryRunError(409, "STORY_REWRITE_LIMIT_REACHED"),
            409,
            "STORY_REWRITE_LIMIT_REACHED",
        ),
        (ParentStoryRunError(422, "SUBJECT_NOT_CONFIRMED"), 422, "SUBJECT_NOT_CONFIRMED"),
        (
            ParentStoryRunError(422, "PROFILE_CONTEXT_NOT_CONFIRMED"),
            422,
            "PROFILE_CONTEXT_NOT_CONFIRMED",
        ),
        (ParentStoryRunError(422, "TRANSCRIPT_NOT_CONFIRMED"), 422, "TRANSCRIPT_NOT_CONFIRMED"),
        (ParentStoryRunError(400, "INVALID_IDEMPOTENCY_KEY"), 400, "INVALID_IDEMPOTENCY_KEY"),
        (ParentStoryRunError(404, "RESOURCE_NOT_FOUND"), 404, "RESOURCE_NOT_FOUND"),
        (
            ParentStoryRunError(503, "PARENT_STORY_RUN_STORE_UNAVAILABLE"),
            503,
            "PARENT_STORY_RUN_STORE_UNAVAILABLE",
        ),
        # the legacy repository codes reach the client under a published code
        (
            ParentStoryRunError(409, "PARENT_STORY_RUN_NOT_READY_FOR_SCRIPT"),
            409,
            "INVALID_STATE_TRANSITION",
        ),
        (
            ParentStoryRunError(409, "PARENT_STORY_REWRITE_NOT_ALLOWED"),
            409,
            "INVALID_STATE_TRANSITION",
        ),
        (
            ParentStoryRunError(409, "PARENT_UNDERSTANDING_REVISION_STALE"),
            409,
            "INVALID_STATE_TRANSITION",
        ),
        (
            ParentStoryRunError(409, "PARENT_STORY_ARTWORK_REQUIRED"),
            409,
            "INVALID_STATE_TRANSITION",
        ),
        (
            ParentStoryRunError(409, "PARENT_VISIBLE_FEATURES_UNAVAILABLE"),
            409,
            "INVALID_STATE_TRANSITION",
        ),
    ],
)
def test_each_error_has_its_status_code_and_a_specific_message(
    client: TestClient, error: ParentStoryRunError, status: int, code: str
) -> None:
    _Repository.result = error
    response = _rewrite(client)
    assert response.status_code == status
    body = response.json()
    assert body["code"] == code
    assert body["retryable"] is (status == 503)
    if code in {
        "STORY_REWRITE_LIMIT_REACHED",
        "SUBJECT_NOT_CONFIRMED",
        "PROFILE_CONTEXT_NOT_CONFIRMED",
        "TRANSCRIPT_NOT_CONFIRMED",
        "INVALID_STATE_TRANSITION",
    }:
        assert body["message"] not in {"", "Không thể hoàn tất yêu cầu."}


def test_a_stale_revision_carries_current_version_and_other_conflicts_do_not(
    client: TestClient,
) -> None:
    _Repository.result = ParentStoryRunError(409, "STALE_REVISION", current_version=3)
    status, body = _wire(_rewrite(client))
    assert status == 409 and body["code"] == "STALE_REVISION" and body["current_version"] == 3
    _Repository.result = ParentStoryRunError(409, "STORY_REWRITE_LIMIT_REACHED", current_version=4)
    status, body = _wire(_rewrite(client))
    assert status == 409 and "current_version" not in body


# ------------------------------------------------------------------------- uniform 404
@pytest.mark.parametrize(
    "db",
    [
        _Db(None),
        _Db("teacher"),
        _Db("school_manager"),
        _Db("platform_admin"),
        _Db("parent", state="suspended"),
        _Db("parent", issuer="another-issuer"),
    ],
    ids=["no-identity", "teacher", "manager", "admin", "inactive", "other-issuer"],
)
def test_a_non_parent_or_inactive_caller_gets_the_same_404_as_an_unknown_run(
    client: TestClient, db: _Db
) -> None:
    _Repository.result = ParentStoryRunError(404, "RESOURCE_NOT_FOUND")
    _use_db(client, _Db("parent"))
    unknown_run = _wire(_rewrite(client, run=UNKNOWN_ID))
    assert unknown_run[0] == 404 and unknown_run[1]["code"] == "RESOURCE_NOT_FOUND"
    _Repository.calls = []
    _use_db(client, db)
    assert _wire(_rewrite(client)) == unknown_run
    assert _Repository.calls == []  # the guard ran first
    _SubjectService.result = ParentStoryRunError(404, "RESOURCE_NOT_FOUND")
    assert _wire(_subject(client)) == unknown_run
    assert _SubjectService.calls == []


# ------------------------------------------------------------------------- subject confirmation
def test_a_plain_subject_confirmation_is_202_and_schedules_nothing(client: TestClient) -> None:
    _compose(
        client,
        drawing_analyzer=object(),
        be1_runtime=SimpleNamespace(session_factory=lambda: None),
    )
    response = _subject(client)
    status, body = _wire(response)
    assert status == 202
    assert body == {
        "story_run_id": RUN_ID,
        "understanding_revision": 1,
        "decision": "CONFIRMED",
        "run_revision": 8,
    }
    assert response.headers["Content-Location"] == f"/v1/story-runs/{RUN_ID}"
    assert _InputRunner.scheduled == []


def test_an_edit_schedules_the_rerun_only_for_a_fresh_command(client: TestClient) -> None:
    _compose(
        client,
        drawing_analyzer=object(),
        be1_runtime=SimpleNamespace(session_factory=lambda: None),
    )
    _SubjectService.result = SubjectConfirmOutcome(1, "RERUN_REQUESTED", 9, input_revision=2)
    status, body = _wire(_subject(client))
    assert status == 202 and body["decision"] == "RERUN_REQUESTED"
    assert body["understanding_revision"] == 1 and body["run_revision"] == 9
    assert len(_InputRunner.scheduled) == 1
    assert _InputRunner.scheduled[0][1:] == (RUN_ID, 2)
    _SubjectService.result = SubjectConfirmOutcome(
        1, "RERUN_REQUESTED", 9, input_revision=None, replayed=True
    )
    assert _subject(client).status_code == 202
    assert len(_InputRunner.scheduled) == 1  # the replay starts nothing


def test_the_rerun_needs_an_analyzer_and_the_switch(client: TestClient) -> None:
    """With no analyzer, or the switch off, the repository is told to confirm the edit at once."""
    _compose(client, drawing_analyzer=None)
    assert _subject(client).status_code == 202
    assert _SubjectService.calls[-1]["rerun_on_edit"] is False
    _compose(client, drawing_analyzer=object(), subject_edit_reruns_vlm=False)
    assert _subject(client).status_code == 202
    assert _SubjectService.calls[-1]["rerun_on_edit"] is False
    _compose(client, drawing_analyzer=object(), subject_edit_reruns_vlm=True)
    assert _subject(client).status_code == 202
    assert _SubjectService.calls[-1]["rerun_on_edit"] is True


def test_the_defaults_are_no_story_generator_and_the_rerun_switch_on(client: TestClient) -> None:
    state = client.app.state  # type: ignore[attr-defined]
    assert state.story_generator is None
    assert state.subject_edit_reruns_vlm is True
    assert state.drawing_analyzer is None


def test_a_stale_subject_answer_carries_current_version(client: TestClient) -> None:
    _SubjectService.result = ParentStoryRunError(409, "STALE_REVISION", current_version=2)
    status, body = _wire(_subject(client))
    assert status == 409 and body["code"] == "STALE_REVISION" and body["current_version"] == 2
    _SubjectService.result = ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
    status, body = _wire(_subject(client))
    assert status == 409 and body["code"] == "INVALID_STATE_TRANSITION"
    assert "current_version" not in body


def test_a_purged_subject_replay_is_the_lifecycle_projection_under_202(client: TestClient) -> None:
    _SubjectService.result = ParentStoryLifecycleRecord.from_body(
        lifecycle_projection_body(run_id=RUN_ID, run_state="DELETED", revision=9, version=9)
    )
    status, body = _wire(_subject(client))
    assert status == 202 and set(body) == {"lifecycle"}


def test_the_legacy_story_revisions_route_is_still_mounted(client: TestClient) -> None:
    paths = client.app.openapi(fe_projected=False)["paths"]  # type: ignore[attr-defined]
    assert "/api/parent/v1/ai/story-runs/{run_id}/story-revisions" in paths
    assert "/api/parent/v1/ai/drawing-understandings" in paths
