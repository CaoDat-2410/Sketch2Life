"""FEAT-066 T-4b3b: the five StoryRun video routes admit a Teacher; the Parent side is unchanged.

Plan D1, D8 to D11 and section 10 (SRS l.864-865, l.1664-1676, l.1691-1693). Three things are
pinned here, all offline (a fake session that knows only the identity row; no PostgreSQL):

* **the Parent byte-for-byte guard**: every answer that is given before a repository is touched
  (validation, key, token and role answers of the five routes) is compared with
  ``golden/story_run_video_head.json``, recorded at HEAD ``29949961`` (the T-4b3a commit) with
  ``story_run_video_matrix`` BEFORE the routes were edited;
* **the OpenAPI document**: the five operations and the schemas they reference are compared with
  ``golden/story_run_video_openapi_head.json``. The 404 and 409 texts name the Teacher; ONLY
  ``video-unsuitable`` and ``complete`` change their success response, by one added member in the
  ``anyOf`` (the Teacher run view, ``TeacherStoryRunEnvelopeV1``); no dangling ``$ref``;
* **the wiring**: a Teacher passes the actor guard and reaches the video repository; the two run
  commands answer a Teacher with the Teacher view and a Parent with the Parent view; the cancel of
  either actor meets the video saga.
"""

from __future__ import annotations

import inspect
import json
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import UUID

import pytest
import story_run_video_matrix as matrix  # type: ignore[import-not-found]
from fastapi import FastAPI
from fastapi.testclient import TestClient

import sketch2life.interfaces.http.app as app_module
import sketch2life.interfaces.http.be1_runtime as runtime_module
import sketch2life.interfaces.http.routers.parent_story_runs as story_routes
import sketch2life.interfaces.http.routers.story_run_video as video_routes
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.application.ports.story_run_actor import RunActor, RunActorKind
from sketch2life.application.ports.story_video import (
    GenerationRecord,
    PlaybackResolution,
    PlaybackStatus,
    PlaybackTarget,
    RunCommandResult,
)
from sketch2life.application.services.story_run_video import AdmissionOutcome
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.interfaces.http.openapi_contract import MOUNTED_OPERATIONS
from tests.unit.test_teacher_story_run_domain import _record as teacher_record

GOLDEN = Path(__file__).parent / "golden" / "story_run_video_head.json"
OPENAPI_GOLDEN = Path(__file__).parent / "golden" / "story_run_video_openapi_head.json"
RUN_ID = matrix.GOOD_UUID
GENERATION_ID = matrix.GENERATION_UUID
HASH = "a" * 64

OPERATIONS = {
    "post /v1/story-runs/{run_id}/video-generations",
    "post /v1/story-runs/{run_id}/video-unsuitable",
    "post /v1/story-runs/{run_id}/complete",
    "post /v1/story-runs/{run_id}/playback-token",
    "get /v1/story-runs/{run_id}/playback",
}
RUN_VIEW_OPERATIONS = {
    "post /v1/story-runs/{run_id}/video-unsuitable",
    "post /v1/story-runs/{run_id}/complete",
}


@pytest.fixture(scope="module")
def application() -> Iterator[FastAPI]:
    patcher = pytest.MonkeyPatch()
    patcher.setitem(Settings.model_config, "env_file", None)
    patcher.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    patcher.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    settings = Settings(
        env="test",
        auth_provider="firebase",
        firebase_project_id="synthetic-t4b3b-project",
        _env_file=None,  # type: ignore[call-arg]
    )
    patcher.setattr(app_module, "get_settings", lambda: settings)
    patcher.setattr(
        runtime_module, "get_core_database_settings", lambda: SimpleNamespace(database_url=None)
    )
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    try:
        built = app_module.create_app()
        matrix.install_overrides(built, runtime_module)
        yield built
    finally:
        patcher.undo()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


@pytest.fixture(scope="module")
def client(application: FastAPI) -> Iterator[TestClient]:
    with TestClient(application, raise_server_exceptions=False) as test_client:
        yield test_client


# ----------------------------------------------------------------------------- Parent golden
def test_every_answer_given_before_a_repository_equals_the_golden_recorded_at_head(
    client: TestClient,
) -> None:
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    current = matrix.run_matrix(client, include_teacher_branch=False)
    assert set(current) == set(golden)
    differing = [key for key in golden if current[key] != golden[key]]
    assert differing == [], differing[:5]
    assert len(golden) > 2000  # five routes x roles x bodies x keys x content types x tokens


def test_the_golden_matrix_covers_each_non_teacher_caller_of_every_route() -> None:
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    for route in matrix.ROUTES:
        for role in matrix.ROLES:
            if role in matrix.ACTIVE_ROLES and route in {"playback_token"}:
                continue  # an authorized call reaches the repository: PostgreSQL covers it
            assert any(key.startswith(f"{route}|run_ok|{role}|") for key in golden), (route, role)


def test_the_matrix_leaves_out_exactly_the_cases_that_reach_a_repository() -> None:
    assert matrix.reaches_repository(
        "video_generations", "parent", "valid", "key_ok", "json", "token_none"
    )
    assert matrix.reaches_repository(
        "video_generations", "teacher", "valid_regen", "key_ok", "json", "token_none"
    )
    assert matrix.reaches_repository("playback", "teacher", "none", "key_ok", "json", "token_valid")
    assert matrix.reaches_repository(
        "playback_token", "parent", "none", "key_ok", "json", "token_none"
    )
    assert not matrix.reaches_repository(
        "video_generations", "manager", "valid", "key_ok", "json", "token_none"
    )
    assert not matrix.reaches_repository(
        "video_generations", "parent", "valid", "key_bad", "json", "token_none"
    )
    assert not matrix.reaches_repository(
        "complete", "parent", "empty", "key_ok", "json", "token_none"
    )
    # a stream with no token or a malformed one is answered (401) before the role is read
    assert not matrix.reaches_repository(
        "playback", "parent", "none", "key_ok", "json", "token_garbage"
    )


# ----------------------------------------------------------------------------- the document
def _resolve(node: Any, components: dict[str, Any]) -> set[str]:
    """Every component a node references, transitively; a dangling ref raises ``KeyError``."""

    found: set[str] = set()

    def walk(item: Any) -> None:
        if isinstance(item, dict):
            ref = item.get("$ref")
            if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
                name = ref.rsplit("/", 1)[1]
                if name not in found:
                    found.add(name)
                    walk(components[name])
            for value in item.values():
                walk(value)
        elif isinstance(item, list):
            for value in item:
                walk(value)

    walk(node)
    return found


def _blank_texts(operation: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = json.loads(json.dumps(operation))
    for code in ("404", "409"):
        if code in cleaned.get("responses", {}):
            cleaned["responses"][code]["description"] = "<text>"
    return cleaned


def _success_schema(operation: dict[str, Any]) -> Any:
    return operation["responses"]["200"]["content"]["application/json"]["schema"]


def test_the_openapi_operations_change_only_in_the_texts_and_the_two_success_members(
    application: FastAPI,
) -> None:
    golden = json.loads(OPENAPI_GOLDEN.read_text(encoding="utf-8"))
    document = application.openapi()
    assert set(golden["operations"]) == OPERATIONS
    for name, before in golden["operations"].items():
        method, path = name.split(" ", 1)
        after = document["paths"][path][method]
        if name in RUN_VIEW_OPERATIONS:
            # the success schema gains the Teacher member and nothing else changes
            before_clean, after_clean = _blank_texts(before), _blank_texts(after)
            before_success = _success_schema(before_clean)
            after_success = _success_schema(after_clean)
            del before_clean["responses"]["200"]["content"]["application/json"]["schema"]
            del after_clean["responses"]["200"]["content"]["application/json"]["schema"]
            assert after_clean == before_clean, name
            before_refs = {item["$ref"] for item in before_success["anyOf"]}
            after_refs = {item["$ref"] for item in after_success["anyOf"]}
            assert after_refs - before_refs == {"#/components/schemas/TeacherStoryRunEnvelopeV1"}
            assert before_refs <= after_refs
        else:
            assert _blank_texts(after) == _blank_texts(before), name
        # the 404 row of the document names the Teacher (it is written by the catalog)
        assert "Teacher" in after["responses"]["404"]["description"], name
    components = document["components"]["schemas"]
    # the schemas the operations referenced at HEAD are untouched; the new member is a component
    # that already existed (T-4b2) and every reference resolves
    for schema_name, schema in golden["schemas"].items():
        assert components[schema_name] == schema, schema_name
    for name in OPERATIONS:
        method, path = name.split(" ", 1)
        _resolve(document["paths"][path][method], components)  # no dangling ref


def test_the_catalog_rows_of_the_five_routes_name_the_teacher() -> None:
    for method, path in (
        ("post", "/v1/story-runs/{run_id}/video-generations"),
        ("post", "/v1/story-runs/{run_id}/video-unsuitable"),
        ("post", "/v1/story-runs/{run_id}/complete"),
        ("post", "/v1/story-runs/{run_id}/playback-token"),
        ("get", "/v1/story-runs/{run_id}/playback"),
    ):
        responses = {row["status"]: row for row in MOUNTED_OPERATIONS[(method, path)]["responses"]}
        assert "Teacher" in responses["404"]["description"], path


# ----------------------------------------------------------------------------- the handlers
@pytest.mark.parametrize(
    "handler",
    [
        video_routes.create_parent_video_generation,
        video_routes.mark_parent_video_unsuitable,
        video_routes.complete_parent_story_run,
        video_routes.issue_parent_playback_token,
        video_routes.stream_parent_playback,
    ],
)
def test_each_video_handler_resolves_the_actor_and_builds_its_repository_from_it(
    handler: Any,
) -> None:
    source = inspect.getsource(handler)
    assert "require_story_run_actor(db, principal)" in source
    assert "_require_parent(" not in source
    assert "SqlStoryVideoRepository(" not in source
    assert "story_video_repository(db, actor)" in source


def test_the_role_check_runs_before_the_key_parse_in_every_post_handler() -> None:
    for handler in (
        video_routes.create_parent_video_generation,
        video_routes.mark_parent_video_unsuitable,
        video_routes.complete_parent_story_run,
    ):
        source = inspect.getsource(handler)
        assert source.index("require_story_run_actor(") < source.index("parse_idempotency_key(")


def test_the_stream_checks_the_token_before_the_actor_and_the_actor_inside_its_own_scope() -> None:
    source = inspect.getsource(video_routes.stream_parent_playback)
    assert source.index("check_playback_token(") < source.index("require_story_run_actor(")
    assert source.index("runtime.session_factory()") < source.index("require_story_run_actor(")
    assert source.index("require_story_run_actor(") < source.index("storage.get_object(")


def test_the_cancel_route_meets_the_video_saga_for_either_actor() -> None:
    source = inspect.getsource(story_routes.cancel_parent_story_run)
    assert "_meet_video_saga(request, db, str(run_id))" in source
    assert "is_teacher" not in source.split("_service_for(db, actor).cancel_run", 1)[1]


# ----------------------------------------------------------------------------- the wiring (fakes)
class _Db:
    def __init__(self, role: str) -> None:
        self._identity = SimpleNamespace(
            account_id=f"account-{role}",
            issuer=matrix.ISSUER,
            account_role=role,
            state="active",
        )

    def get(self, _model: object, _key: object) -> Any:
        return self._identity


class _VideoRepository:
    actors: list[RunActor] = []

    def __init__(self, actor: RunActor) -> None:
        type(self).actors.append(actor)


class _Admission:
    calls: list[dict[str, Any]] = []
    reply: Any = None
    repositories: list[Any] = []

    def __init__(self, repository: object, adapters: object, **_kwargs: Any) -> None:
        type(self).repositories.append(repository)

    def request(self, **kwargs: Any) -> Any:
        type(self).calls.append(kwargs)
        return type(self).reply


class _Commands:
    calls: list[tuple[str, dict[str, Any]]] = []
    repositories: list[Any] = []

    def __init__(self, repository: object) -> None:
        type(self).repositories.append(repository)

    def mark_unsuitable(self, **kwargs: Any) -> Any:
        type(self).calls.append(("mark_unsuitable", kwargs))
        return RunCommandResult(RUN_ID, False)

    def complete(self, **kwargs: Any) -> Any:
        type(self).calls.append(("complete", kwargs))
        return RunCommandResult(RUN_ID, False)


class _RunReader:
    actors: list[RunActor] = []
    view: Any = None

    def __init__(self, actor: RunActor) -> None:
        type(self).actors.append(actor)

    def get_run(self, **kwargs: Any) -> Any:
        return type(self).view


class _Playback:
    resolutions: list[dict[str, Any]] = []

    def __init__(self, actor: RunActor) -> None:
        self.actor = actor

    def resolve_playback(self, **kwargs: Any) -> PlaybackResolution:
        type(self).resolutions.append({"actor": self.actor, **kwargs})
        return PlaybackResolution(
            PlaybackStatus.PLAYABLE,
            PlaybackTarget(RUN_ID, GENERATION_ID, "digest-of-the-caller", "parent/run/out.mp4"),
        )


@pytest.fixture
def wired(monkeypatch: pytest.MonkeyPatch, application: FastAPI) -> Iterator[FastAPI]:
    _VideoRepository.actors = []
    _Admission.calls, _Admission.repositories, _Admission.reply = [], [], None
    _Commands.calls, _Commands.repositories = [], []
    _RunReader.actors, _RunReader.view = [], None
    _Playback.resolutions = []
    monkeypatch.setattr(
        video_routes, "story_video_repository", lambda _db, actor: _VideoRepository(actor)
    )
    monkeypatch.setattr(video_routes, "StoryVideoAdmissionService", _Admission)
    monkeypatch.setattr(video_routes, "StoryVideoCommandService", _Commands)
    monkeypatch.setattr(video_routes, "story_run_repository", lambda _db, actor: _RunReader(actor))
    original_db = application.dependency_overrides[runtime_module.get_db]
    try:
        yield application
    finally:
        application.dependency_overrides[runtime_module.get_db] = original_db


def _use(application: FastAPI, role: str) -> None:
    application.dependency_overrides[runtime_module.get_db] = lambda: _Db(role)


def _headers(role: str) -> dict[str, str]:
    return {"X-Test-Principal": role, "Idempotency-Key": "key-1"}


def _generation() -> GenerationRecord:
    return GenerationRecord(
        generation_id=GENERATION_ID,
        run_id=RUN_ID,
        scope_kind="ORGANIZATION",
        scope_ref="organization-1",
        state="ACCEPTED",
        kind="INITIAL",
        generation_no=1,
        job_ref="vjob_abc",
        key_hash="k" * 64,
        fingerprint="f" * 64,
        script_hash=HASH,
        story_revision_id="rev-1",
        review_id="review-1",
        quality_reason_code=None,
        compute_reservation_ref="res-1",
        compute_released_at=None,
        billing_quota_usage_ref="usage-1",
        safe_failure_code=None,
        started=False,
        generation_revision=2,
        run_state="VIDEO_QUEUED",
        run_revision=7,
    )


@pytest.mark.parametrize(
    "role, kind", [("teacher", RunActorKind.TEACHER), ("parent", RunActorKind.PARENT)]
)
def test_a_video_request_builds_the_repository_for_the_actor_of_either_role(
    client: TestClient, wired: FastAPI, role: str, kind: RunActorKind
) -> None:
    _use(wired, role)
    _Admission.reply = AdmissionOutcome(_generation())
    response = client.post(
        f"/v1/story-runs/{RUN_ID}/video-generations",
        json={"expected_revision": 6, "story_sha256": HASH},
        headers=_headers(role),
    )
    assert response.status_code == 202, response.text
    assert [actor.kind for actor in _VideoRepository.actors] == [kind]
    assert [type(repository) for repository in _Admission.repositories] == [_VideoRepository]
    (call,) = _Admission.calls
    assert call["run_id"] == RUN_ID and call["principal"].subject == role
    # the body of a Teacher request is the Parent's: ids, state and number only
    body = response.json()["video_generation"]
    assert set(body) == {
        "generation_id",
        "state",
        "generation_no",
        "kind",
        "job_id",
        "run_state",
        "run_revision",
    }
    assert "organization" not in response.text.lower()


@pytest.mark.parametrize(
    "path, body",
    [
        (
            "video-unsuitable",
            {"expected_revision": 6, "generation_id": GENERATION_ID, "reason_code": "OTHER"},
        ),
        ("complete", {"expected_revision": 6}),
    ],
)
def test_the_two_run_commands_answer_a_teacher_with_the_teacher_view(
    client: TestClient, wired: FastAPI, path: str, body: dict[str, Any]
) -> None:
    _use(wired, "teacher")
    _RunReader.view = teacher_record(run_id=RUN_ID, run_state="SCRIPT_REVIEW", run_revision=8)
    response = client.post(
        f"/v1/story-runs/{RUN_ID}/{path}", json=body, headers=_headers("teacher")
    )
    assert response.status_code == 200, response.text
    story_run = response.json()["story_run"]
    assert story_run["profile_ref"]["kind"] == "MANAGED_PROFILE"  # the Teacher view
    assert "parent_profile_id" not in story_run
    assert [actor.kind for actor in _VideoRepository.actors] == [RunActorKind.TEACHER]
    assert [actor.kind for actor in _RunReader.actors] == [RunActorKind.TEACHER]
    assert response.headers["Content-Location"] == f"/v1/story-runs/{RUN_ID}"


def test_a_purged_replay_is_the_content_free_projection_for_a_teacher_too(
    client: TestClient, wired: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sketch2life.application.ports.parent_story_runs import ParentStoryLifecycleRecord
    from sketch2life.application.ports.story_run_lifecycle import lifecycle_projection_body

    _use(wired, "teacher")
    projection = ParentStoryLifecycleRecord.from_body(
        lifecycle_projection_body(run_id=RUN_ID, run_state="DELETE_PENDING", revision=4, version=7)
    )

    class _Purged(_Commands):
        def complete(self, **kwargs: Any) -> Any:
            return RunCommandResult(RUN_ID, True, projection)

    monkeypatch.setattr(video_routes, "StoryVideoCommandService", _Purged)
    response = client.post(
        f"/v1/story-runs/{RUN_ID}/complete",
        json={"expected_revision": 6},
        headers=_headers("teacher"),
    )
    assert response.status_code == 200 and set(response.json()) == {"request_id", "lifecycle"}
    assert _RunReader.actors == []  # a purge projection never reads the run


def test_a_repository_refusal_is_the_uniform_http_error_for_a_teacher(
    client: TestClient, wired: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use(wired, "teacher")

    class _Refusing(_Commands):
        def complete(self, **kwargs: Any) -> Any:
            raise ParentStoryRunError(404, "RESOURCE_NOT_FOUND")

    monkeypatch.setattr(video_routes, "StoryVideoCommandService", _Refusing)
    response = client.post(
        f"/v1/story-runs/{RUN_ID}/complete",
        json={"expected_revision": 6},
        headers=_headers("teacher"),
    )
    assert response.status_code == 404 and response.json()["code"] == "RESOURCE_NOT_FOUND"


def test_the_playback_token_of_a_teacher_binds_the_digest_of_the_caller(
    client: TestClient, application: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    _Playback.resolutions = []
    monkeypatch.setattr(video_routes, "story_video_repository", lambda _db, actor: _Playback(actor))
    original = application.dependency_overrides[runtime_module.get_db]
    _use(application, "teacher")
    try:
        response = client.post(
            f"/v1/story-runs/{RUN_ID}/playback-token", headers={"X-Test-Principal": "teacher"}
        )
    finally:
        application.dependency_overrides[runtime_module.get_db] = original
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    (resolution,) = _Playback.resolutions
    assert resolution["actor"].is_teacher and resolution["generation_id"] is None
    grant = response.json()["playback"]
    assert set(grant) == {"token", "expires_at", "stream_path", "media_type", "asset_ref"}
    text = response.text.lower()
    for word in ("bucket", "object_key", "presigned", "parent/", "output.mp4", "digest"):
        assert word not in text
    assert grant["stream_path"] == f"/v1/story-runs/{UUID(RUN_ID)}/playback"
