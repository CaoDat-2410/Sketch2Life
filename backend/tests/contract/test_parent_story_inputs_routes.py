"""FEAT-066 T-2b: the Parent run drawing route contract (SRS l.1664) and its mount exclusivity.

Offline: the real app with its real exception handlers, a fake database and a fake attach service.
Behaviour against PostgreSQL and S3Mock lives in
``tests/integration/test_parent_story_inputs_postgres.py``.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

import sketch2life.interfaces.http.app as app_module
import sketch2life.interfaces.http.be1_runtime as runtime_module
import sketch2life.interfaces.http.routers.parent_story_inputs as input_routes
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_inputs import DrawingAttachOutcome
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryLifecycleRecord,
    ParentStoryRunError,
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
from sketch2life.interfaces.http.router_composition import story_demo_replaced_routers
from sketch2life.interfaces.http.story_demo_guard import route_labels

ISSUER = "issuer-1"
PRINCIPAL = VerifiedPrincipal("adult-1", ISSUER, frozenset())
RUN_ID = "22222222-2222-4222-8222-222222222222"
UNKNOWN_ID = "00000000-0000-0000-0000-000000000000"
HANDLE = "upl_11111111-1111-4111-8111-111111111111"
PATH = f"/v1/story-runs/{RUN_ID}/assets"
OPERATION = ("post", "/v1/story-runs/{run_id}/assets")
VOLATILE_KEYS = {"request_id", "correlation_id"}
STORAGE_WORDS = (
    "bucket",
    "object_key",
    "storage_object_ref",
    "presigned",
    "credential",
    "amazonaws",
    "minio",
    "normalized.png",
    "parent/",
    "s3mock",
)


class _Db:
    """Fake session: one identity row (or none)."""

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


class _Service:
    """Fake attach service: ``result`` is returned, or raised when it is an exception."""

    result: Any = None
    calls: list[dict[str, Any]] = []

    def __init__(self, db: object, *, storage: object, repository: object = None) -> None:
        self.storage = storage
        self.repository = repository

    def attach_drawing(self, **kwargs: Any) -> Any:
        type(self).calls.append(kwargs)
        if isinstance(type(self).result, BaseException):
            raise type(self).result
        return type(self).result


def _outcome(*, replayed: bool = False, state: str = "QUEUED") -> DrawingAttachOutcome:
    return DrawingAttachOutcome(
        input_revision=2,
        run_revision=5,
        run_state="INPUT_PROCESSING",
        analysis_state=state,
        replayed=replayed,
    )


@pytest.fixture(autouse=True)
def _reset_service() -> Iterator[None]:
    _Service.result = _outcome()
    _Service.calls = []
    yield


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    settings = Settings(
        env="test",
        auth_provider="firebase",
        firebase_project_id="synthetic-t2b-project",
        _env_file=None,  # type: ignore[call-arg]
    )
    monkeypatch.setattr(app_module, "get_settings", lambda: settings)
    monkeypatch.setattr(
        runtime_module, "get_core_database_settings", lambda: SimpleNamespace(database_url=None)
    )
    monkeypatch.setattr(input_routes, "ParentRunAssetService", _Service)
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


def _post(
    client: TestClient,
    body: Any = None,
    *,
    key: str | None = "t2b-key-1",
    run_id: str = RUN_ID,
) -> Any:
    headers = {} if key is None else {"Idempotency-Key": key}
    payload = {"asset_ref": HANDLE} if body is None else body
    return client.post(f"/v1/story-runs/{run_id}/assets", json=payload, headers=headers)


def _wire(response: Any) -> tuple[int, dict[str, Any]]:
    body = response.json()
    return response.status_code, {k: v for k, v in body.items() if k not in VOLATILE_KEYS}


# ----------------------------------------------------------------------------- catalog and mount
def test_the_operation_is_catalogued_projected_and_tagged() -> None:
    assert OPERATION in MOUNTED_OPERATIONS
    assert OPERATION in SRS_V22_INCLUDED_OPERATIONS
    assert SRS_V22_OPERATION_TAGS[OPERATION] == "Parent StoryRuns"
    contract = MOUNTED_OPERATIONS[OPERATION]
    assert contract["tag"] == "Parent StoryRuns"
    assert contract["handler"] == "parent_story_inputs.py::attach_parent_run_asset"
    statuses = {response["status"] for response in contract["responses"]}
    assert statuses == {"202", "400", "401", "404", "409", "413", "415", "422", "503", "500"}


def test_the_route_is_in_the_demo_registry_and_the_demo_replaces_it() -> None:
    registry = {
        label for router in story_demo_replaced_routers() for label in route_labels(router.routes)
    }
    assert ("POST", "/v1/story-runs/{run_id}/assets") in registry
    assert [getattr(route, "path", None) for route in input_routes.router.routes] == [
        "/v1/story-runs/{run_id}/assets",
        # FEAT-066 T-2c: the idea, the transcript read and its confirmation join the module.
        "/v1/story-runs/{run_id}/idea",
        "/v1/story-runs/{run_id}/transcript",
        "/v1/story-runs/{run_id}/transcript-confirmation",
        # FEAT-066 T-2d: the story rewrite joins the module.
        "/v1/story-runs/{run_id}/story-rewrites",
    ]


def test_published_contract_has_the_operation_and_no_storage_words(client: TestClient) -> None:
    spec = client.app.openapi()  # type: ignore[attr-defined]
    operation = spec["paths"]["/v1/story-runs/{run_id}/assets"]["post"]
    assert operation["tags"] == ["Parent StoryRuns"]
    assert operation["security"]
    parameters = {(p["in"], p["name"]): p for p in operation["parameters"]}
    assert parameters[("header", "Idempotency-Key")]["required"] is True
    assert parameters[("header", "Idempotency-Key")]["schema"]["maxLength"] == 128
    assert parameters[("path", "run_id")]["schema"]["format"] == "uuid"
    request_schema = spec["components"]["schemas"]["AttachRunAssetRequestV1"]
    assert request_schema["additionalProperties"] is False
    assert request_schema["required"] == ["asset_ref"]
    assert request_schema["properties"]["asset_ref"]["pattern"] == "^upl_[0-9a-f-]{36}$"
    accepted = spec["components"]["schemas"]["ParentRunAssetAcceptedV1"]
    assert "job" not in accepted["properties"]
    assert set(accepted["properties"]) == {
        "request_id",
        "story_run_id",
        "asset_ref",
        "asset_kind",
        "asset_state",
        "input_revision",
        "run_revision",
        "run_state",
        "analysis_state",
    }
    assert accepted["properties"]["analysis_state"]["enum"] == [
        "QUEUED",
        "RUNNING",
        "SUCCEEDED",
        "FAILED",
        "AWAITING_RECONCILIATION",
    ]
    success = operation["responses"]["202"]["content"]["application/json"]["schema"]
    assert {ref["$ref"].rsplit("/", 1)[-1] for ref in success["anyOf"]} == {
        "ParentRunAssetAcceptedV1",
        "ParentStoryRunLifecycleEnvelopeV1",
    }
    scoped = json.dumps(operation) + json.dumps(request_schema) + json.dumps(accepted)
    for word in STORAGE_WORDS:
        assert word not in scoped.lower(), word


# ----------------------------------------------------------------------------- success shape
def test_success_is_a_202_with_the_asset_ref_and_validation_state(client: TestClient) -> None:
    response = _post(client)
    assert response.status_code == 202, response.text
    body = response.json()
    assert UUID(body["request_id"])
    assert {k: v for k, v in body.items() if k != "request_id"} == {
        "story_run_id": RUN_ID,
        "asset_ref": HANDLE,
        "asset_kind": "DRAWING",
        "asset_state": "READY",
        "input_revision": 2,
        "run_revision": 5,
        "run_state": "INPUT_PROCESSING",
        "analysis_state": "QUEUED",
    }
    assert "job" not in body
    assert response.headers["Content-Location"] == f"/v1/story-runs/{RUN_ID}"
    call = _Service.calls[0]
    assert call["run_id"] == RUN_ID and call["asset_ref"] == HANDLE
    assert call["expected_run_revision"] is None and call["idempotency_key"] == "t2b-key-1"
    assert call["principal"] == PRINCIPAL
    lowered = response.text.lower()
    for word in STORAGE_WORDS:
        assert word not in lowered, word


def test_a_replay_of_a_purged_run_returns_the_lifecycle_envelope(client: TestClient) -> None:
    _Service.result = ParentStoryLifecycleRecord.from_body(
        lifecycle_projection_body(run_id=RUN_ID, run_state="DELETE_PENDING", revision=7, version=7)
    )
    response = _post(client)
    assert response.status_code == 202, response.text
    body = response.json()
    assert set(body) == {"request_id", "lifecycle"}
    assert body["lifecycle"]["run_state"] == "DELETE_PENDING"
    assert "asset_ref" not in body and "story_run_id" not in body


# ------------------------------------------------------------------------------ keys and bodies
@pytest.mark.parametrize("key", [None, "", " bad key ", "x" * 129, "with\ttab"])
def test_a_missing_or_invalid_key_is_a_plain_400(client: TestClient, key: str | None) -> None:
    response = _post(client, key=key)
    assert response.status_code == 400, response.text
    body = response.json()
    assert body["code"] == "INVALID_REQUEST"
    assert body["field_errors"] is None
    assert not _Service.calls


def test_the_key_is_checked_after_the_role_and_before_the_run(client: TestClient) -> None:
    # T-4b3a: a Teacher now passes the actor guard (it is covered in
    # ``test_teacher_run_inputs_contract.py``); a Manager stands for the wrong role here.
    _use_db(client, _Db("school_manager"))
    wrong_role_bad_key = _post(client, key=" ")
    assert wrong_role_bad_key.status_code == 404
    _use_db(client, _Db("parent"))
    parent_bad_key = _post(client, key=" ")
    assert parent_bad_key.status_code == 400
    assert not _Service.calls


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"asset_ref": ""},
        {"asset_ref": "up_11111111-1111-4111-8111-111111111111"},
        {"asset_ref": "parent/run/token/original"},
        {"asset_ref": "https://example.test/a.png"},
        {"asset_ref": HANDLE, "expected_run_revision": 0},
        {"asset_ref": HANDLE, "expected_run_revision": "3"},
        {"asset_ref": HANDLE, "expected_run_revision": 1.5},
        {"asset_ref": HANDLE, "owner_scope_ref": "x"},
        {"asset_ref": HANDLE, "asset_key": "parent/x/y/original"},
        {"asset_ref": HANDLE, "bucket": "b"},
        {"asset_ref": HANDLE, "url": "https://example.test"},
        {"asset_ref": HANDLE, "job": {}},
    ],
)
def test_the_body_is_strict(client: TestClient, body: dict[str, Any]) -> None:
    response = _post(client, body)
    assert response.status_code == 400, response.text
    assert response.json()["code"] == "INVALID_REQUEST"
    assert not _Service.calls


def test_an_expected_run_revision_is_passed_through(client: TestClient) -> None:
    assert _post(client, {"asset_ref": HANDLE, "expected_run_revision": 5}).status_code == 202
    assert _Service.calls[0]["expected_run_revision"] == 5


def test_a_malformed_run_id_is_400(client: TestClient) -> None:
    response = _post(client, run_id="not-a-uuid")
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST"


# ------------------------------------------------------------------------- uniform 404 (CV-5)
def test_wrong_role_unknown_run_foreign_asset_and_unknown_asset_look_the_same(
    client: TestClient,
) -> None:
    _Service.result = ParentStoryRunError(404, "RESOURCE_NOT_FOUND")
    _use_db(client, _Db("parent"))
    unknown_run = _post(client, run_id=UNKNOWN_ID)
    foreign_asset = _post(client, {"asset_ref": HANDLE.replace("1111", "2222")})
    unknown_asset = _post(client, {"asset_ref": "upl_" + "0" * 8 + "-0000-4000-8000-" + "0" * 12})
    assert unknown_run.status_code == 404
    reference = _wire(unknown_run)
    assert reference[1]["code"] == "RESOURCE_NOT_FOUND"
    for other in (foreign_asset, unknown_asset):
        assert _wire(other) == reference
    calls_before = len(_Service.calls)
    for role, state, issuer in (
        ("school_manager", "active", ISSUER),
        ("platform_admin", "active", ISSUER),
        ("parent", "suspended", ISSUER),
        ("parent", "active", "another-issuer"),
        (None, "active", ISSUER),
    ):
        _use_db(client, _Db(role, state=state, issuer=issuer))
        wrong = _post(client)
        assert _wire(wrong) == reference, (role, state, issuer)
    assert len(_Service.calls) == calls_before  # the guard stops before the service


def test_a_wrong_role_gets_404_even_for_a_run_the_service_would_accept(client: TestClient) -> None:
    _use_db(client, _Db("school_manager"))
    response = _post(client)
    assert response.status_code == 404
    assert response.json()["code"] == "RESOURCE_NOT_FOUND"
    assert not _Service.calls


# ----------------------------------------------------------------------- errors and the envelope
def test_a_stale_revision_carries_current_version(client: TestClient) -> None:
    _Service.result = ParentStoryRunError(409, "STALE_REVISION", current_version=9)
    response = _post(client, {"asset_ref": HANDLE, "expected_run_revision": 3})
    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "STALE_REVISION"
    assert body["current_version"] == 9
    assert body["retryable"] is False


def test_other_conflicts_do_not_carry_current_version(client: TestClient) -> None:
    _Service.result = ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
    response = _post(client)
    assert response.status_code == 409
    assert response.json()["code"] == "INVALID_STATE_TRANSITION"
    assert "current_version" not in response.json()


@pytest.mark.parametrize(
    ("status", "code", "retryable"),
    [
        (413, "MEDIA_TOO_LARGE", False),
        (415, "UNSUPPORTED_MEDIA_TYPE", False),
        (422, "IMAGE_DIMENSIONS_EXCEEDED", False),
        (422, "UPLOAD_INCOMPLETE", False),
        (422, "UPLOAD_CHECKSUM_MISMATCH", False),
        (422, "UPLOAD_CONTENT_MISMATCH", False),
        (503, "STORAGE_UNAVAILABLE", True),
    ],
)
def test_error_codes_reach_the_client_with_their_own_message(
    client: TestClient, status: int, code: str, retryable: bool
) -> None:
    _Service.result = ParentStoryRunError(status, code)
    response = _post(client)
    assert response.status_code == status
    body = response.json()
    assert body["code"] == code
    assert body["retryable"] is retryable
    assert body["message"] and body["message"] != "Không thể hoàn tất yêu cầu."
    assert set(body) == {
        "code",
        "message",
        "correlation_id",
        "retryable",
        "retry_after_seconds",
        "field_errors",
    }


# ----------------------------------------------------------------- background analysis hand-off
class _Runner:
    created: list[Any] = []
    scheduled: list[tuple[Any, ...]] = []

    def __init__(self, session_factory: Any, analyzer: Any) -> None:
        type(self).created.append((session_factory, analyzer))

    def run(self, principal: Any, run_id: str, input_revision: int) -> None:
        type(self).scheduled.append((principal, run_id, input_revision))


@pytest.fixture
def runner(monkeypatch: pytest.MonkeyPatch) -> type[_Runner]:
    _Runner.created = []
    _Runner.scheduled = []
    monkeypatch.setattr(input_routes, "ParentInputJobRunner", _Runner)
    return _Runner


def _compose(client: TestClient, analyzer: object | None) -> None:
    client.app.state.drawing_analyzer = analyzer  # type: ignore[attr-defined]
    client.app.state.be1_runtime = SimpleNamespace(  # type: ignore[attr-defined]
        session_factory=lambda: None
    )


def test_no_analyzer_means_no_background_task_by_default(
    client: TestClient, runner: type[_Runner]
) -> None:
    assert client.app.state.drawing_analyzer is None  # type: ignore[attr-defined]
    assert _post(client).status_code == 202
    assert runner.created == [] and runner.scheduled == []


def test_a_composed_analyzer_runs_after_the_response_for_the_new_input(
    client: TestClient, runner: type[_Runner]
) -> None:
    analyzer = object()
    _compose(client, analyzer)
    assert _post(client).status_code == 202
    assert runner.created[0][1] is analyzer
    assert runner.scheduled == [(PRINCIPAL, RUN_ID, 2)]


def test_a_replay_does_not_start_a_second_analysis(
    client: TestClient, runner: type[_Runner]
) -> None:
    _compose(client, object())
    _Service.result = _outcome(replayed=True)
    assert _post(client).status_code == 202
    assert runner.scheduled == []


def test_a_failed_attach_starts_no_analysis(client: TestClient, runner: type[_Runner]) -> None:
    _compose(client, object())
    _Service.result = ParentStoryRunError(409, "INVALID_STATE_TRANSITION")
    assert _post(client).status_code == 409
    assert runner.scheduled == []
