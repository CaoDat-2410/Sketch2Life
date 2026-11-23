"""FEAT-066 T-1c: the playback-token, stream and run-detail route contracts (SRS l.575-576, l.1676,
l.1691-1693, l.1811).

Offline: the real app with its real exception handlers, a fake database session, a fake Story
repository and an in-memory object store. Behaviour against PostgreSQL (real ownership rechecks,
no pooled connection during a download, the detail read) lives in
``tests/integration/story_video/test_playback_and_detail_postgres.py``.
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
from collections.abc import Iterator
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

import sketch2life.interfaces.http.app as app_module
import sketch2life.interfaces.http.be1_runtime as runtime_module
import sketch2life.interfaces.http.routers.parent_story_runs as run_routes
import sketch2life.interfaces.http.routers.story_run_video as video_routes
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.object_storage import ObjectStorageFailure, StoredObject
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryLifecycleRecord,
    ParentStoryRunError,
    ParentStoryRunRecord,
)
from sketch2life.application.ports.story_run_lifecycle import lifecycle_projection_body
from sketch2life.application.ports.story_video import (
    PlaybackResolution,
    PlaybackStatus,
    PlaybackTarget,
)
from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.infrastructure.story_video.playback_tokens import (
    PlaybackTokenCodec,
    actor_digest,
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
OWNER_SCOPE = "owner-scope-ref"
KEY = "parent/22222222/video/33333333/output.mp4"
CONTENT = bytes(range(256)) * 4
GRANT_POST = ("post", "/v1/story-runs/{run_id}/playback-token")
STREAM_GET = ("get", "/v1/story-runs/{run_id}/playback")
DETAIL_GET = ("get", "/v1/story-runs/{run_id}")
STORAGE_WORDS = (
    "bucket",
    "object_key",
    "presigned",
    "amazonaws",
    "s3mock",
    "parent/",
    "output.mp4",
)
VOLATILE = {"request_id", "correlation_id"}


class Clock:
    now = 1_900_000_000.0

    def __call__(self) -> float:
        return self.now


class _Session:
    """A fake database session: the identity lookup, and a record of when it was closed."""

    instances: list[_Session] = []
    role = "parent"
    fail = False

    def __init__(self) -> None:
        self.closed = False
        type(self).instances.append(self)

    def get(self, _model: object, _key: object) -> Any:
        if type(self).fail:
            from sqlalchemy.exc import OperationalError

            raise OperationalError("select", {}, Exception("down"))
        if type(self).role == "none":
            return None
        return SimpleNamespace(
            account_id="account-1", issuer=ISSUER, account_role=type(self).role, state="active"
        )

    def __enter__(self) -> _Session:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.closed = True

    def close(self) -> None:
        self.closed = True


class _Repo:
    resolution: PlaybackResolution = PlaybackResolution(PlaybackStatus.NOT_FOUND)
    calls: list[dict[str, Any]] = []

    def __init__(self, db: object) -> None:
        self.db = db

    def resolve_playback(self, **kwargs: Any) -> PlaybackResolution:
        type(self).calls.append(kwargs)
        return type(self).resolution


class _Body:
    def __init__(self, content: bytes, session_log: list[bool]) -> None:
        self._io = io.BytesIO(content)
        self._log = session_log
        self.closed = False

    def read(self, size: int = -1) -> bytes:
        self._log.append(all(session.closed for session in _Session.instances))
        return self._io.read(size)

    def close(self) -> None:
        self.closed = True


class _Storage:
    def __init__(self) -> None:
        self.reads: list[bool] = []
        self.bodies: list[_Body] = []
        self.content: bytes | None = CONTENT
        self.fail = False
        self.keys: list[str] = []

    def get_object(self, key: str) -> StoredObject | None:
        self.keys.append(key)
        if self.fail:
            raise ObjectStorageFailure("down")
        if self.content is None:
            return None
        body = _Body(self.content, self.reads)
        self.bodies.append(body)
        return StoredObject(body, len(self.content), "application/octet-stream", {})


def _playable() -> PlaybackResolution:
    return PlaybackResolution(
        PlaybackStatus.PLAYABLE, PlaybackTarget(RUN_ID, GEN_ID, OWNER_SCOPE, KEY)
    )


@pytest.fixture(autouse=True)
def _reset() -> None:
    _Session.instances = []
    _Session.role = "parent"
    _Session.fail = False
    _Repo.resolution = _playable()
    _Repo.calls = []


@pytest.fixture
def clock() -> Clock:
    clock = Clock()
    clock.now = 1_900_000_000.0
    return clock


@pytest.fixture
def storage() -> _Storage:
    return _Storage()


@pytest.fixture
def client(
    monkeypatch: pytest.MonkeyPatch, clock: Clock, storage: _Storage
) -> Iterator[TestClient]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    settings = Settings(
        env="test",
        auth_provider="firebase",
        firebase_project_id="synthetic-t1c-project",
        _env_file=None,  # type: ignore[call-arg]
    )
    monkeypatch.setattr(app_module, "get_settings", lambda: settings)
    monkeypatch.setattr(
        runtime_module, "get_core_database_settings", lambda: SimpleNamespace(database_url=None)
    )
    monkeypatch.setattr(video_routes, "story_video_repository", lambda db, _actor: _Repo(db))
    application = app_module.create_app()
    application.state.story_playback_tokens = PlaybackTokenCodec(
        active_key_id="k1", keys={"k1": b"synthetic-secret-0123456789abcdef-0123"}, clock=clock
    )
    application.state.lesson_library_storage = storage
    application.dependency_overrides[get_verified_adult] = lambda: PRINCIPAL
    application.dependency_overrides[get_db] = lambda: _Session()
    application.dependency_overrides[get_runtime] = lambda: SimpleNamespace(
        settings=SimpleNamespace(env="test", synthetic_pilot_enabled=True),
        session_factory=_Session,
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


def _token(client: TestClient) -> str:
    response = client.post(f"/v1/story-runs/{RUN_ID}/playback-token")
    assert response.status_code == 200, response.text
    return str(response.json()["playback"]["token"])


def _stream(client: TestClient, token: str | None, **headers: str) -> Any:
    if token is not None:
        headers["X-Playback-Token"] = token
    return client.get(f"/v1/story-runs/{RUN_ID}/playback", headers=headers)


def _property_names(schema: Any) -> set[str]:
    """Every property name below a schema (descriptions are prose and are not inspected)."""

    names: set[str] = set()
    if isinstance(schema, dict):
        properties = schema.get("properties")
        if isinstance(properties, dict):
            names.update(str(name).lower() for name in properties)
        for value in schema.values():
            names |= _property_names(value)
    elif isinstance(schema, list):
        for item in schema:
            names |= _property_names(item)
    return names


def _wire(response: Any) -> tuple[int, dict[str, Any]]:
    return response.status_code, {k: v for k, v in response.json().items() if k not in VOLATILE}


# ----------------------------------------------------------------------------- catalog
@pytest.mark.parametrize(
    ("operation", "handler", "statuses"),
    [
        (
            GRANT_POST,
            "story_run_video.py::issue_parent_playback_token",
            {"200", "401", "404", "409", "422", "500", "503"},
        ),
        (
            STREAM_GET,
            "story_run_video.py::stream_parent_playback",
            {"200", "206", "401", "404", "416", "422", "500", "503"},
        ),
    ],
)
def test_the_two_new_operations_are_catalogued_projected_and_tagged(
    operation: tuple[str, str], handler: str, statuses: set[str]
) -> None:
    assert operation in MOUNTED_OPERATIONS and operation in SRS_V22_INCLUDED_OPERATIONS
    assert SRS_V22_OPERATION_TAGS[operation] == "Parent StoryRuns"
    contract = MOUNTED_OPERATIONS[operation]
    assert contract["handler"] == handler
    assert {row["status"] for row in contract["responses"]} == statuses
    assert contract["authentication"] == "HTTPBearer (bearer)"
    assert "Idempotency-Key" not in contract["request_inputs"]  # a grant, not a state change


def test_the_stream_publishes_a_binary_video_and_the_token_header_only(client: TestClient) -> None:
    spec = client.app.openapi()  # type: ignore[attr-defined]
    stream = spec["paths"]["/v1/story-runs/{run_id}/playback"]["get"]
    parameters = {(p["in"], p["name"]): p.get("required", False) for p in stream["parameters"]}
    assert parameters == {
        ("path", "run_id"): True,
        ("header", "X-Playback-Token"): False,
        ("header", "Range"): False,
    }
    for status in ("200", "206"):
        assert stream["responses"][status]["content"] == {
            "video/mp4": {"schema": {"type": "string", "format": "binary"}}
        }
    assert not any(p["in"] == "query" for p in stream["parameters"])  # never in a URL (l.1693)
    issue = spec["paths"]["/v1/story-runs/{run_id}/playback-token"]["post"]
    assert "requestBody" not in issue
    assert [p["name"] for p in issue["parameters"]] == ["run_id"]
    schemas = spec["components"]["schemas"]
    grant = schemas["ParentPlaybackGrantV1"]
    assert set(grant["properties"]) == {
        "token",
        "expires_at",
        "stream_path",
        "media_type",
        "asset_ref",
    }
    assert grant["additionalProperties"] is False
    names = _property_names(
        {n: schemas[n] for n in ("ParentPlaybackGrantV1", "ParentPlaybackTokenResponseV1")}
    )
    for word in ("bucket", "object_key", "presigned", "s3", "storage_key", "url"):
        assert not any(word in name for name in names), word


def test_the_run_detail_model_is_additive_and_publishes_the_304_and_the_quota_marker(
    client: TestClient,
) -> None:
    spec = client.app.openapi()  # type: ignore[attr-defined]
    operation = spec["paths"]["/v1/story-runs/{run_id}"]["get"]
    assert "304" in operation["responses"] and "200" in operation["responses"]
    run = spec["components"]["schemas"]["ParentStoryRunResponseV1"]
    assert {"video", "quota", "timeline"} <= set(run["properties"])
    assert {"video", "quota", "timeline"}.isdisjoint(run["required"])
    quota = spec["components"]["schemas"]["ParentStoryQuotaSummaryV1"]
    assert quota["properties"]["state"]["const"] == "UNAVAILABLE" or quota["properties"]["state"][
        "enum"
    ] == ["UNAVAILABLE"]
    video = spec["components"]["schemas"]["ParentStoryRunVideoV1"]
    assert "video_requests_used" in video["properties"] and "quota" not in video["properties"]
    names = _property_names(video) | _property_names(
        {
            n: spec["components"]["schemas"][n]
            for n in (
                "ParentVideoJobSummaryV1",
                "ParentVideoPlaybackV1",
                "ParentVideoHistoryItemV1",
                "ParentVideoSceneStateV1",
            )
        }
    )
    for word in ("prompt", "transcript", "output_asset", "storage", "bucket", "provider", "key"):
        assert not any(word in name for name in names), word


# ----------------------------------------------------------------------------- issue
def test_the_grant_is_200_with_no_store_and_no_storage_location(client: TestClient) -> None:
    response = client.post(f"/v1/story-runs/{RUN_ID}/playback-token")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"request_id", "playback"}
    playback = body["playback"]
    assert playback["media_type"] == "video/mp4"
    assert playback["asset_ref"] == f"vid_{GEN_ID}"
    assert playback["stream_path"] == f"/v1/story-runs/{RUN_ID}/playback"
    assert response.headers["Cache-Control"] == "no-store"
    expires = datetime.fromisoformat(playback["expires_at"].replace("Z", "+00:00"))
    assert expires == datetime.fromtimestamp(1_900_000_000 + 300, UTC)
    text = (
        json.dumps({k: v for k, v in playback.items() if k != "token"})
        + str(dict(response.headers))
    ).lower()
    for word in STORAGE_WORDS:
        assert word not in text, word
    assert _Repo.calls == [{"principal": PRINCIPAL, "run_id": RUN_ID, "generation_id": None}]


def test_an_unplayable_run_is_409_a_foreign_one_404_and_neither_leaks(client: TestClient) -> None:
    _Repo.resolution = PlaybackResolution(PlaybackStatus.NOT_PLAYABLE)
    status, body = _wire(client.post(f"/v1/story-runs/{RUN_ID}/playback-token"))
    assert (status, body["code"]) == (409, "INVALID_STATE_TRANSITION")
    _Repo.resolution = PlaybackResolution(PlaybackStatus.NOT_FOUND)
    status, body = _wire(client.post(f"/v1/story-runs/{RUN_ID}/playback-token"))
    assert (status, body["code"]) == (404, "RESOURCE_NOT_FOUND")
    _Session.role = "school_manager"
    status, other = _wire(client.post(f"/v1/story-runs/{RUN_ID}/playback-token"))
    assert (status, other) == (404, body)  # a wrong role answers the same uniform 404
    assert len(_Repo.calls) == 2  # the wrong role never reached the repository


def test_without_a_signing_secret_both_routes_answer_503_and_the_app_still_starts(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    client.app.state.story_playback_tokens = None  # type: ignore[attr-defined]
    issued = client.post(f"/v1/story-runs/{RUN_ID}/playback-token")
    assert _wire(issued)[0] == 503 and issued.json()["code"] == "PROVIDER_UNAVAILABLE"
    streamed = _stream(client, "ptk1.a.b.c")
    assert streamed.status_code == 503 and streamed.json()["code"] == "PROVIDER_UNAVAILABLE"
    # a foreign or unplayable run still sees 404 / 409 first on the issue route
    _Repo.resolution = PlaybackResolution(PlaybackStatus.NOT_FOUND)
    assert client.post(f"/v1/story-runs/{RUN_ID}/playback-token").status_code == 404
    # the factory composes no codec when the builder returns none: the app object still exists
    monkeypatch.setattr(app_module, "build_playback_codec", lambda _settings: None)
    application = app_module.create_app()
    assert application.state.story_playback_tokens is None


# ----------------------------------------------------------------------------- stream
def test_the_stream_sends_the_whole_object_with_the_safe_header_set(
    client: TestClient, storage: _Storage
) -> None:
    token = _token(client)
    response = _stream(client, token)
    assert response.status_code == 200 and response.content == CONTENT
    headers = response.headers
    assert headers["content-type"] == "video/mp4"
    assert headers["accept-ranges"] == "bytes"
    assert headers["content-length"] == str(len(CONTENT))
    assert headers["content-disposition"] == "inline"  # no file name, no download
    assert "filename" not in headers["content-disposition"]
    assert headers["cache-control"] == "private, no-store"
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["referrer-policy"] == "no-referrer"
    assert token not in str(dict(headers))
    assert storage.keys == [KEY]  # the key is used inside Story only
    text = (str(dict(headers)) + response.url.path).lower()
    for word in ("bucket", "presigned", "s3mock", "amazonaws", "output.mp4"):
        assert word not in text
    assert all(body.closed for body in storage.bodies)
    assert _Repo.calls[-1] == {"principal": PRINCIPAL, "run_id": RUN_ID, "generation_id": GEN_ID}


def test_a_range_is_206_and_a_bad_range_is_416_with_the_size(
    client: TestClient, storage: _Storage
) -> None:
    token = _token(client)
    part = _stream(client, token, Range="bytes=10-19")
    assert part.status_code == 206 and part.content == CONTENT[10:20]
    assert part.headers["content-range"] == f"bytes 10-19/{len(CONTENT)}"
    assert part.headers["content-length"] == "10"
    assert _stream(client, token, Range="bytes=-4").content == CONTENT[-4:]
    for bad in ("bytes=0-1,5-6", "bytes=5-2", f"bytes={len(CONTENT)}-", "chunks=0-1"):
        refused = _stream(client, token, Range=bad)
        assert refused.status_code == 416
        assert refused.headers["content-range"] == f"bytes */{len(CONTENT)}"
        assert refused.json()["code"] == "RANGE_NOT_SATISFIABLE"
    assert all(body.closed for body in storage.bodies)  # also the bodies of refused ranges


def test_the_token_is_read_from_a_header_only_never_from_a_url(client: TestClient) -> None:
    token = _token(client)
    for query in ("token", "playback_token", "t", "X-Playback-Token"):
        response = client.get(f"/v1/story-runs/{RUN_ID}/playback?{query}={token}")
        assert response.status_code == 401 and response.json()["code"] == "INVALID_TOKEN"
        assert token not in response.text
    assert _stream(client, token).status_code == 200


def test_a_bad_missing_or_expired_token_is_401_before_any_store_or_database_read(
    client: TestClient, clock: Clock
) -> None:
    token = _token(client)
    baseline = len(_Session.instances)
    calls = len(_Repo.calls)
    header, payload, mac = token.split(".")[1:]
    for bad in (
        None,
        "",
        "junk",
        f"ptk1.{header}.{payload}",
        f"ptk1.{header}.{payload}.{mac[:-3]}AAA",
    ):
        response = _stream(client, bad)
        assert response.status_code == 401 and response.json()["code"] == "INVALID_TOKEN"
        assert response.json()["retryable"] is False
    assert len(_Session.instances) == baseline and len(_Repo.calls) == calls
    clock.now += 301
    expired = _stream(client, token)
    assert expired.status_code == 401 and expired.json()["code"] == "TOKEN_EXPIRED"
    assert token not in expired.text
    assert "Mã" in expired.json()["message"]  # the safe message of the story family


def test_a_token_of_another_run_or_another_actor_and_a_revoked_grant_are_the_uniform_404(
    client: TestClient,
) -> None:
    token = _token(client)
    other_run = client.get(
        f"/v1/story-runs/{uuid4()}/playback", headers={"X-Playback-Token": token}
    )
    calls = len(_Repo.calls)
    assert other_run.status_code == 404 and len(_Repo.calls) == calls  # no store read
    _Repo.resolution = PlaybackResolution(
        PlaybackStatus.NOT_PLAYABLE
    )  # unsuitable, a rejected or failed generation (Complete and closeout no longer revoke)
    revoked = _stream(client, token)
    _Repo.resolution = PlaybackResolution(PlaybackStatus.NOT_FOUND)  # cancel, delete, foreign
    foreign = _stream(client, token)
    # a token minted for another actor (the token names an actor digest; the caller's scope differs)
    _Repo.resolution = PlaybackResolution(
        PlaybackStatus.PLAYABLE, PlaybackTarget(RUN_ID, GEN_ID, "someone-else", KEY)
    )
    stolen = _stream(client, token)
    codes = {_wire(item)[0] for item in (other_run, revoked, foreign, stolen)}
    bodies = {
        json.dumps(_wire(item)[1], sort_keys=True) for item in (other_run, revoked, foreign, stolen)
    }
    assert codes == {404} and len(bodies) == 1
    _Repo.resolution = _playable()
    assert _stream(client, token).status_code == 200
    payload = json.loads(base64.urlsafe_b64decode(token.split(".")[2] + "=="))
    assert payload["a"] == actor_digest(OWNER_SCOPE) and payload["r"] == RUN_ID


def test_a_role_that_is_neither_parent_nor_teacher_with_a_valid_token_is_404_and_no_store_read(
    client: TestClient, storage: _Storage
) -> None:
    token = _token(client)
    for role in ("school_manager", "platform_admin", "none"):
        _Session.role = role
        calls = len(_Repo.calls)
        response = _stream(client, token)
        assert response.status_code == 404 and response.json()["code"] == "RESOURCE_NOT_FOUND"
        assert len(_Repo.calls) == calls
    assert storage.keys == []


def test_the_database_session_is_closed_before_the_first_byte(
    client: TestClient, storage: _Storage
) -> None:
    token = _token(client)
    storage.reads.clear()
    _Session.instances.clear()
    response = _stream(client, token)
    assert response.status_code == 200
    assert len(_Session.instances) == 1 and _Session.instances[0].closed
    assert storage.reads and all(storage.reads)  # every read saw the session closed


def test_a_missing_object_a_failing_store_a_missing_store_and_an_oversize_object(
    client: TestClient, storage: _Storage
) -> None:
    token = _token(client)
    storage.content = None
    gone = _stream(client, token)
    assert gone.status_code == 404 and gone.json()["code"] == "RESOURCE_NOT_FOUND"
    storage.content = CONTENT
    storage.fail = True
    down = _stream(client, token)
    assert down.status_code == 503 and down.json()["code"] == "STORAGE_UNAVAILABLE"
    assert down.json()["retryable"] is True
    storage.fail = False
    client.app.state.story_playback_max_object_bytes = len(CONTENT) - 1  # type: ignore[attr-defined]
    big = _stream(client, token)
    assert big.status_code == 503 and big.json()["code"] == "STORAGE_UNAVAILABLE"
    assert storage.bodies[-1].closed and storage.reads == []  # refused before the first byte
    client.app.state.story_playback_max_object_bytes = len(CONTENT)  # type: ignore[attr-defined]
    assert _stream(client, token).status_code == 200
    client.app.state.lesson_library_storage = None  # type: ignore[attr-defined]
    none = _stream(client, token)
    assert none.status_code == 503 and none.json()["code"] == "STORAGE_UNAVAILABLE"
    for response in (gone, down, big, none):
        text = response.text.lower()
        for word in STORAGE_WORDS:
            assert word not in text


def test_a_database_failure_while_rechecking_is_503_and_head_is_not_defined(
    client: TestClient,
) -> None:
    token = _token(client)
    _Session.fail = True
    down = _stream(client, token)
    assert down.status_code == 503 and down.json()["code"] == "DATABASE_UNAVAILABLE"
    _Session.fail = False
    head = client.head(f"/v1/story-runs/{RUN_ID}/playback", headers={"X-Playback-Token": token})
    assert head.status_code == 405
    assert client.post(f"/v1/story-runs/{RUN_ID}/playback").status_code == 405


# ----------------------------------------------------------------------------- run detail
def _record(video: dict[str, Any] | None = None) -> ParentStoryRunRecord:
    now = datetime(2026, 11, 21, 8, 0, tzinfo=UTC)
    return ParentStoryRunRecord(
        run_id=RUN_ID,
        run_state="VIDEO_READY",
        run_revision=9,
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
        video=video,
        timeline=[{"event": "RUN_CREATED", "at": now}],
    )


class _Reader:
    view: Any = None
    calls: list[dict[str, Any]] = []

    def get_run(self, **kwargs: Any) -> Any:
        type(self).calls.append(kwargs)
        if isinstance(type(self).view, BaseException):
            raise type(self).view
        return type(self).view


@pytest.fixture
def reader(monkeypatch: pytest.MonkeyPatch) -> type[_Reader]:
    _Reader.view = _record()
    _Reader.calls = []
    monkeypatch.setattr(run_routes, "_service", lambda _db: _Reader())
    return _Reader


def _video() -> dict[str, Any]:
    return {
        "current_generation_id": GEN_ID,
        "generation_no": 1,
        "kind": "INITIAL",
        "state": "READY",
        "job": {
            "job_id": "vjob_x",
            "state": "succeeded",
            "stage": None,
            "retryable": False,
            "error_code": None,
        },
        "scenes": [{"scene_index": 1, "state": "READY"}],
        "playback": {
            "state": "AVAILABLE",
            "asset_ref": f"vid_{GEN_ID}",
            "token_route": f"/v1/story-runs/{RUN_ID}/playback-token",
        },
        "video_requests_used": 1,
        "video_requests_remaining": 2,
        "admission_pending": False,
        "history": [
            {"generation_id": GEN_ID, "generation_no": 1, "kind": "INITIAL", "state": "READY"}
        ],
    }


def test_the_detail_shows_the_video_the_quota_marker_and_a_strong_etag(
    client: TestClient, reader: type[_Reader]
) -> None:
    reader.view = _record(_video())
    response = client.get(f"/v1/story-runs/{RUN_ID}")
    assert response.status_code == 200
    run = response.json()["story_run"]
    assert run["video"]["playback"]["state"] == "AVAILABLE"
    assert run["video"]["video_requests_remaining"] == 2
    assert run["quota"] == {
        "state": "UNAVAILABLE",
        "granted": None,
        "used": None,
        "available": None,
        "month": None,
    }
    assert run["timeline"][0]["event"] == "RUN_CREATED"
    etag = response.headers["etag"]
    assert etag.startswith('"d1-') and etag.endswith('"') and "W/" not in etag
    assert response.headers["cache-control"] == "private, no-cache"
    assert response.headers["vary"] == "Authorization"
    # a plain run keeps a null video and the same additive fields
    reader.view = _record(None)
    plain = client.get(f"/v1/story-runs/{RUN_ID}").json()["story_run"]
    assert plain["video"] is None and plain["quota"]["state"] == "UNAVAILABLE"


def test_the_304_comes_only_after_authorisation_and_a_fresh_read(
    client: TestClient, reader: type[_Reader], monkeypatch: pytest.MonkeyPatch
) -> None:
    reader.view = _record(_video())
    etag = client.get(f"/v1/story-runs/{RUN_ID}").headers["etag"]
    reads = len(reader.calls)
    cached = client.get(f"/v1/story-runs/{RUN_ID}", headers={"If-None-Match": etag})
    assert cached.status_code == 304 and cached.content == b""
    assert cached.headers["etag"] == etag and len(reader.calls) == reads + 1  # recomputed, no cache
    # the video moves: the same tag no longer matches
    moved = _video() | {"state": "REJECTED_BY_ADULT"}
    reader.view = _record(moved)
    fresh = client.get(f"/v1/story-runs/{RUN_ID}", headers={"If-None-Match": etag})
    assert fresh.status_code == 200 and fresh.headers["etag"] != etag
    # a foreign caller with a matching tag gets the 404, never the 304
    reader.view = ParentStoryRunError(404, "RESOURCE_NOT_FOUND")
    foreign = client.get(f"/v1/story-runs/{RUN_ID}", headers={"If-None-Match": etag})
    assert foreign.status_code == 404 and "etag" not in foreign.headers
    _Session.role = "school_manager"
    wrong_role = client.get(f"/v1/story-runs/{RUN_ID}", headers={"If-None-Match": etag})
    assert wrong_role.status_code == 404 and "etag" not in wrong_role.headers
    # T-4a1: a Teacher passes the role guard; without the current assignment the repository
    # answers the same 404, never the 304 (the assignment is read before the tag is compared).
    _Session.role = "teacher"
    monkeypatch.setattr(run_routes, "_teacher_service", lambda _db, _actor: _Reader())
    unassigned = client.get(f"/v1/story-runs/{RUN_ID}", headers={"If-None-Match": etag})
    assert unassigned.status_code == 404 and "etag" not in unassigned.headers


def test_a_run_being_deleted_returns_the_content_free_envelope_without_a_tag(
    client: TestClient, reader: type[_Reader]
) -> None:
    reader.view = ParentStoryLifecycleRecord.from_body(
        lifecycle_projection_body(run_id=RUN_ID, run_state="DELETE_PENDING", revision=4, version=7)
    )
    response = client.get(f"/v1/story-runs/{RUN_ID}", headers={"If-None-Match": "*"})
    assert response.status_code == 200
    assert set(response.json()) == {"request_id", "lifecycle"}
    assert "etag" not in response.headers
    text = response.text.lower()
    for word in ("video", "quota", "timeline", "playback"):
        assert word not in text


def test_the_legacy_ai_route_builds_the_same_model_through_the_same_builder() -> None:
    from sketch2life.interfaces.http.routers import parent_ai

    record = _record(_video())
    assert parent_ai._story_response(record).model_dump(mode="json") == (
        run_routes.story_run_response(record).model_dump(mode="json")
    )
    assert parent_ai._story_response(record).video is not None


# ----------------------------------------------------------------------------- generator
def test_the_chunk_generator_reads_in_bounded_pieces_and_always_closes_the_body() -> None:
    big = bytes(range(251)) * 1000  # 251,000 bytes: four 64 KiB reads at most per pass
    reads: list[int] = []

    class _Counting(_Body):
        def read(self, size: int = -1) -> bytes:
            reads.append(size)
            return super().read(size)

    async def collect(body: _Body, first: int, last: int) -> bytes:
        return b"".join([chunk async for chunk in video_routes._stream_chunks(body, first, last)])

    body = _Counting(big, [])
    assert asyncio.run(collect(body, 0, len(big) - 1)) == big
    assert body.closed and max(reads) == 64 * 1024
    body = _Counting(big, [])
    assert asyncio.run(collect(body, 70_000, 70_009)) == big[70_000:70_010]
    assert body.closed
    # an object that ends early still closes the body and stops without raising
    short = _Counting(b"abc", [])
    assert asyncio.run(collect(short, 0, 99)) == b"abc" and short.closed
    # a client that leaves closes the generator: the body is closed, not left to the collector
    leaver = _Counting(big, [])

    async def leave() -> None:
        generator = video_routes._stream_chunks(leaver, 0, len(big) - 1)
        assert await generator.__anext__() == big[: 64 * 1024]
        await generator.aclose()

    asyncio.run(leave())
    assert leaver.closed
