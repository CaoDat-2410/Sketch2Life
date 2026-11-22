"""FEAT-066 T-4b3a: the five StoryRun input routes admit a Teacher; the Parent side is unchanged.

Plan D1 to D7 and section 10 (SRS l.864-865, l.1664-1668, l.1676). Three things are pinned here, all
offline (a fake session that knows only the identity row; no PostgreSQL):

* **the Parent byte-for-byte guard**: every answer that is given before a repository is touched
  (the validation, the key and the role answers of the five routes) is compared with
  ``golden/story_run_inputs_head.json``, recorded at HEAD ``8d0fd2ed`` (the T-4b2 commit) with
  ``story_run_inputs_matrix`` BEFORE the routes were edited;
* **the OpenAPI document**: the six operations of the input family (the five routes and the subject
  confirmation) and the schemas they reference are compared with
  ``golden/story_run_inputs_openapi_head.json``; the only difference is the text of the 404 and 409
  rows (a Teacher is named), no schema member, header, status or media type changes;
* **the wiring**: a Teacher passes the actor guard and reaches a repository, the background runner
  of a Teacher run gets the actor and the organization the route saw, and the runner call of a
  Parent is exactly what it was.
"""

from __future__ import annotations

import inspect
import json
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import story_run_inputs_matrix as matrix  # type: ignore[import-not-found]
from fastapi import FastAPI
from fastapi.testclient import TestClient

import sketch2life.interfaces.http.app as app_module
import sketch2life.interfaces.http.be1_runtime as runtime_module
import sketch2life.interfaces.http.routers.parent_story_inputs as input_routes
import sketch2life.interfaces.http.routers.parent_story_runs as story_routes
from sketch2life.application.ports.parent_story_inputs import (
    DrawingAttachOutcome,
    IdeaOutcome,
    SubjectConfirmOutcome,
    TranscriptConfirmOutcome,
    TranscriptView,
)
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryRevisionReservation,
    StoryRewriteOutcome,
)
from sketch2life.application.ports.story_run_actor import RunActor, RunActorKind
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.interfaces.http.openapi_contract import MOUNTED_OPERATIONS

GOLDEN = Path(__file__).parent / "golden" / "story_run_inputs_head.json"
OPENAPI_GOLDEN = Path(__file__).parent / "golden" / "story_run_inputs_openapi_head.json"
RUN_ID = matrix.GOOD_UUID
HASH = "a" * 64
ORG = "organization-1"

OPERATIONS = {
    "post /v1/story-runs/{run_id}/assets",
    "post /v1/story-runs/{run_id}/idea",
    "get /v1/story-runs/{run_id}/transcript",
    "post /v1/story-runs/{run_id}/transcript-confirmation",
    "post /v1/story-runs/{run_id}/story-rewrites",
    "post /v1/story-runs/{run_id}/subject-confirmation",
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
        firebase_project_id="synthetic-t4b3a-project",
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
    assert len(golden) > 2000  # five routes x roles x bodies x keys x content types


def test_the_golden_matrix_covers_each_non_teacher_caller_of_every_route() -> None:
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    for route in matrix.ROUTES:
        for role in matrix.ROLES:
            if route == "transcript" and role in matrix.ACTIVE_ROLES:
                continue  # an authorized GET reaches the repository: PostgreSQL covers it
            assert any(key.startswith(f"{route}|run_ok|{role}|") for key in golden), (route, role)


def test_the_matrix_leaves_out_exactly_the_cases_that_reach_a_repository() -> None:
    # a Parent or a Teacher with a valid body, a good key and JSON reaches the database; so does
    # an authorized GET. Every other combination is answered before a repository is touched.
    assert matrix.reaches_repository("POST", "parent", "valid", "key_ok", "json")
    assert matrix.reaches_repository("POST", "teacher", "valid_hint", "key_ok", "json")
    assert matrix.reaches_repository("GET", "parent", "none", "key_ok", "json")
    assert not matrix.reaches_repository("POST", "manager", "valid", "key_ok", "json")
    assert not matrix.reaches_repository("POST", "parent", "valid", "key_bad", "json")
    assert not matrix.reaches_repository("POST", "parent", "empty", "key_ok", "json")


# ----------------------------------------------------------------------------- the document
def _operations(document: dict[str, Any]) -> dict[str, Any]:
    return dict(document["operations"])


def _blank_error_texts(operation: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = json.loads(json.dumps(operation))
    for code in ("404", "409"):
        if code in cleaned.get("responses", {}):
            cleaned["responses"][code]["description"] = "<text>"
    return cleaned


def test_the_openapi_operations_change_only_in_the_404_and_409_texts(application: FastAPI) -> None:
    golden = json.loads(OPENAPI_GOLDEN.read_text(encoding="utf-8"))
    document = application.openapi()
    assert set(_operations(golden)) == OPERATIONS
    for name, before in _operations(golden).items():
        method, path = name.split(" ", 1)
        after = document["paths"][path][method]
        assert _blank_error_texts(after) == _blank_error_texts(before), name
        assert "Teacher" in after["responses"]["404"]["description"] or name.endswith(
            "subject-confirmation"
        ), name
    # the schemas the operations reference are untouched: no new member for a Teacher
    components = document["components"]["schemas"]
    for schema_name, schema in golden["schemas"].items():
        assert components[schema_name] == schema, schema_name


def test_the_404_rows_of_the_catalog_name_the_teacher() -> None:
    for method, path in (
        ("post", "/v1/story-runs/{run_id}/assets"),
        ("post", "/v1/story-runs/{run_id}/idea"),
        ("get", "/v1/story-runs/{run_id}/transcript"),
        ("post", "/v1/story-runs/{run_id}/transcript-confirmation"),
        ("post", "/v1/story-runs/{run_id}/story-rewrites"),
    ):
        responses = {row["status"]: row for row in MOUNTED_OPERATIONS[(method, path)]["responses"]}
        assert "Teacher" in responses["404"]["description"], path
        assert "Teacher" in responses["409"]["description"], path


# ----------------------------------------------------------------------------- the handlers
@pytest.mark.parametrize(
    "handler",
    [
        input_routes.attach_parent_run_asset,
        input_routes.add_parent_run_idea,
        input_routes.get_parent_run_transcript,
        input_routes.confirm_parent_run_transcript,
        input_routes.rewrite_parent_run_story,
    ],
)
def test_each_input_handler_resolves_the_actor_and_builds_its_repository_from_it(
    handler: Any,
) -> None:
    source = inspect.getsource(handler)
    assert "require_story_run_actor(db, principal)" in source
    assert "_require_parent(" not in source
    assert "SqlParentStoryRunRepository(" not in source
    assert "story_run_repository(db, actor)" in source


def test_the_role_check_runs_before_the_key_parse_in_every_post_handler() -> None:
    for handler in (
        input_routes.attach_parent_run_asset,
        input_routes.add_parent_run_idea,
        input_routes.confirm_parent_run_transcript,
        input_routes.rewrite_parent_run_story,
    ):
        source = inspect.getsource(handler)
        assert source.index("require_story_run_actor(") < source.index("parse_idempotency_key(")


def test_the_subject_confirmation_no_longer_excludes_a_teacher_from_the_rerun() -> None:
    source = inspect.getsource(story_routes.confirm_parent_story_subject)
    assert "not actor.is_teacher" not in source
    assert "job_arguments" in source


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


class _Repository:
    calls: list[tuple[str, dict[str, Any]]] = []
    actors: list[RunActor] = []
    reply: Any = None

    def __init__(self, actor: RunActor) -> None:
        type(self).actors.append(actor)

    def _record(self, name: str, kwargs: dict[str, Any]) -> Any:
        type(self).calls.append((name, kwargs))
        return type(self).reply

    def get_transcript(self, **kwargs: Any) -> Any:
        return self._record("get_transcript", kwargs)

    def confirm_transcript(self, **kwargs: Any) -> Any:
        return self._record("confirm_transcript", kwargs)

    def reserve_story_rewrite(self, **kwargs: Any) -> Any:
        return self._record("reserve_story_rewrite", kwargs)


class _Service:
    calls: list[dict[str, Any]] = []
    reply: Any = None
    repositories: list[Any] = []

    def __init__(self, db: object, *, storage: object, repository: object = None) -> None:
        type(self).repositories.append(repository)

    def attach_drawing(self, **kwargs: Any) -> Any:
        type(self).calls.append(kwargs)
        return type(self).reply

    def submit(self, **kwargs: Any) -> Any:
        type(self).calls.append(kwargs)
        return type(self).reply


class _Runner:
    scheduled: list[tuple[str, tuple[Any, ...]]] = []

    def __init__(self, session_factory: object, work: object) -> None:
        pass

    def run(self, *args: Any) -> None:
        type(self).scheduled.append(("run", args))


@pytest.fixture
def wired(monkeypatch: pytest.MonkeyPatch, application: FastAPI) -> Iterator[Any]:
    _Repository.calls, _Repository.actors, _Repository.reply = [], [], None
    _Service.calls, _Service.repositories, _Service.reply = [], [], None
    _Runner.scheduled = []
    monkeypatch.setattr(input_routes, "story_run_repository", lambda _db, actor: _Repository(actor))
    monkeypatch.setattr(input_routes, "ParentRunAssetService", _Service)
    monkeypatch.setattr(input_routes, "ParentRunIdeaService", _Service)
    monkeypatch.setattr(input_routes, "ParentInputJobRunner", _Runner)
    monkeypatch.setattr(input_routes, "ParentSpeechJobRunner", _Runner)
    monkeypatch.setattr(input_routes, "ParentStoryRewriteRunner", _Runner)
    monkeypatch.setattr(story_routes, "ParentInputJobRunner", _Runner)
    state = application.state
    saved = {
        name: getattr(state, name, None)
        for name in ("drawing_analyzer", "speech_transcriber", "story_generator", "be1_runtime")
    }
    state.drawing_analyzer = state.speech_transcriber = state.story_generator = object()
    state.be1_runtime = SimpleNamespace(session_factory=lambda: None)
    original_db = application.dependency_overrides[runtime_module.get_db]
    try:
        yield application
    finally:
        for name, value in saved.items():
            setattr(state, name, value)
        application.dependency_overrides[runtime_module.get_db] = original_db


def _use(application: FastAPI, role: str) -> None:
    application.dependency_overrides[runtime_module.get_db] = lambda: _Db(role)


def _teacher_headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    return {"X-Test-Principal": "teacher", "Idempotency-Key": "key-1", **(extra or {})}


def _reservation(organization: str | None) -> ParentStoryRevisionReservation:
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
        organization_id=organization,
    )


def test_a_teacher_rewrite_reaches_the_repository_and_the_runner_gets_the_actor(
    client: TestClient, wired: FastAPI
) -> None:
    _use(wired, "teacher")
    _Repository.reply = StoryRewriteOutcome(
        story_revision_no=2,
        run_revision=9,
        run_state="SCRIPT_GENERATING",
        reservation=_reservation(ORG),
    )
    response = client.post(
        f"/v1/story-runs/{RUN_ID}/story-rewrites",
        json={"expected_story_revision": 1},
        headers=_teacher_headers(),
    )
    assert response.status_code == 202, response.text
    assert [actor.kind for actor in _Repository.actors] == [RunActorKind.TEACHER]
    ((name, kwargs),) = _Repository.calls
    assert name == "reserve_story_rewrite" and kwargs["run_id"] == RUN_ID
    ((_, args),) = _Runner.scheduled
    assert args[1].organization_id == ORG
    assert isinstance(args[2], RunActor) and args[2].is_teacher and len(args) == 3
    assert "organization" not in response.text.lower()  # the id never reaches the body


def test_a_parent_rewrite_schedules_the_runner_exactly_as_before(
    client: TestClient, wired: FastAPI
) -> None:
    _use(wired, "parent")
    _Repository.reply = StoryRewriteOutcome(
        story_revision_no=2,
        run_revision=9,
        run_state="SCRIPT_GENERATING",
        reservation=_reservation(None),
    )
    response = client.post(
        f"/v1/story-runs/{RUN_ID}/story-rewrites",
        json={"expected_story_revision": 1},
        headers={**_teacher_headers(), "X-Test-Principal": "parent"},
    )
    assert response.status_code == 202, response.text
    assert [actor.kind for actor in _Repository.actors] == [RunActorKind.PARENT]
    ((_, args),) = _Runner.scheduled
    assert len(args) == 2  # the principal and the reservation: no actor, no organization


def test_a_teacher_drawing_attach_schedules_the_analysis_with_the_actor_and_the_organization(
    client: TestClient, wired: FastAPI
) -> None:
    _use(wired, "teacher")
    _Service.reply = DrawingAttachOutcome(
        input_revision=2,
        run_revision=5,
        run_state="INPUT_PROCESSING",
        analysis_state="QUEUED",
        organization_id=ORG,
    )
    response = client.post(
        f"/v1/story-runs/{RUN_ID}/assets",
        json={"asset_ref": matrix.UPLOAD_REF},
        headers=_teacher_headers(),
    )
    assert response.status_code == 202, response.text
    assert [type(r) for r in _Service.repositories] == [_Repository]
    ((_, args),) = _Runner.scheduled
    assert args[0].subject == "teacher" and args[1] == RUN_ID and args[2] == 2
    assert isinstance(args[3], RunActor) and args[3].is_teacher and args[4] == ORG
    assert ORG not in response.text


def test_a_parent_drawing_attach_schedules_the_analysis_exactly_as_before(
    client: TestClient, wired: FastAPI
) -> None:
    _use(wired, "parent")
    _Service.reply = DrawingAttachOutcome(
        input_revision=2, run_revision=5, run_state="INPUT_PROCESSING", analysis_state="QUEUED"
    )
    response = client.post(
        f"/v1/story-runs/{RUN_ID}/assets",
        json={"asset_ref": matrix.UPLOAD_REF},
        headers={**_teacher_headers(), "X-Test-Principal": "parent"},
    )
    assert response.status_code == 202, response.text
    ((_, args),) = _Runner.scheduled
    assert len(args) == 3  # principal, run id, input revision


def test_a_teacher_voice_idea_schedules_the_asr_with_the_actor_and_the_organization(
    client: TestClient, wired: FastAPI
) -> None:
    _use(wired, "teacher")
    _Service.reply = IdeaOutcome(
        input_revision=3,
        run_revision=6,
        run_state="INPUT_PROCESSING",
        idea_source="VOICE",
        transcript_revision=1,
        transcript_state="PENDING",
        new_transcript_id="transcript-1",
        organization_id=ORG,
    )
    response = client.post(
        f"/v1/story-runs/{RUN_ID}/idea",
        json={"expected_run_revision": 5, "audio_ref": matrix.UPLOAD_REF},
        headers=_teacher_headers(),
    )
    assert response.status_code == 202, response.text
    ((_, args),) = _Runner.scheduled
    assert args[1:3] == (RUN_ID, "transcript-1")
    assert isinstance(args[3], RunActor) and args[3].is_teacher and args[4] == ORG


def test_a_teacher_reads_and_confirms_the_transcript_with_the_no_store_header(
    client: TestClient, wired: FastAPI
) -> None:
    _use(wired, "teacher")
    _Repository.reply = TranscriptView(run_revision=4, state="NONE")
    read = client.get(
        f"/v1/story-runs/{RUN_ID}/transcript", headers={"X-Test-Principal": "teacher"}
    )
    assert read.status_code == 200, read.text
    assert read.headers["Cache-Control"] == "private, no-store"
    _Repository.reply = TranscriptConfirmOutcome(
        transcript_revision=1, run_revision=7, run_state="INPUT_REVIEW"
    )
    confirmed = client.post(
        f"/v1/story-runs/{RUN_ID}/transcript-confirmation",
        json={"expected_transcript_revision": 1, "transcript_sha256": HASH, "confirmed": True},
        headers=_teacher_headers(),
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.headers["Cache-Control"] == "private, no-store"
    assert [name for name, _ in _Repository.calls] == ["get_transcript", "confirm_transcript"]


def test_a_teacher_subject_edit_schedules_the_rerun_with_the_actor_and_the_organization(
    client: TestClient, wired: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    class _SubjectService:
        calls: list[dict[str, Any]] = []

        def confirm_subject(self, **kwargs: Any) -> Any:
            type(self).calls.append(kwargs)
            return SubjectConfirmOutcome(
                understanding_revision=1,
                decision="RERUN_REQUESTED",
                run_revision=8,
                input_revision=2,
                organization_id=ORG,
            )

    monkeypatch.setattr(story_routes, "_service_for", lambda _db, _actor: _SubjectService())
    _use(wired, "teacher")
    response = client.post(
        f"/v1/story-runs/{RUN_ID}/subject-confirmation",
        json={"expected_understanding_revision": 1, "confirmed_subject": "green dragon"},
        headers=_teacher_headers(),
    )
    assert response.status_code == 202, response.text
    # the Teacher exclusion is gone: the route asks for the rerun like it does for a Parent
    assert _SubjectService.calls[0]["rerun_on_edit"] is True
    ((_, args),) = _Runner.scheduled
    assert args[1:3] == (RUN_ID, 2)
    assert isinstance(args[3], RunActor) and args[3].is_teacher and args[4] == ORG
