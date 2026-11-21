"""FEAT-066 T-1c: playback grant, header-borne stream and ``StoryRunDetailV1`` on PostgreSQL.

SRS l.575-576 (playback authorization is short and rechecked at each playback), l.1676
(``playback-token``: the current artifact at ``VIDEO_READY``, a short token for one asset, active
until complete, closeout or cancel), l.1691-1693 (one ready video, actor and run, rechecked against
the current ownership; no bucket, key or URL; the token never in a URL or a log), l.1811 and AC-41
(one aggregated run detail, no prompt, transcript or foreign-scope leak, ETag). Runs only against a
disposable database whose name contains ``be1_acceptance`` and ``frc08_v3_t1c``. The admission
ports are the local/test pair, object storage is in memory and no provider is called. Runs are
built by the T-1b helpers (direct inserts for the confirmed script, the real ``video-generations``
route and the fixture runner for the video).
"""

from __future__ import annotations

import io
import logging
import os
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import pytest
from fastapi import Header, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import event, update

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.object_storage import ObjectStorageFailure, StoredObject
from sketch2life.application.ports.story_video import QuotaStatus, VideoRenderResult
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.story_video.fixture_runner import FixtureVideoRenderer
from sketch2life.infrastructure.story_video.local_adapters import (
    VideoAdmissionScript,
    build_local_video_adapters,
)
from sketch2life.infrastructure.story_video.playback_tokens import PlaybackTokenCodec
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from tests.integration.story_video import test_video_commands_postgres as t1b

ISSUER = t1b.ISSUER  # the T-1b builders derive the owner scope from this issuer
STORAGE_WORDS = (
    "bucket",
    "object_key",
    "presigned",
    "s3mock",
    "parent/",
    "output.mp4",
    "amazonaws",
)
PROMPT_WORDS = ("visual_prompt", "character_anchors", "transcript", "support_note")
VG = t1b.VG
RUNS = t1b.RUNS


class Clock:
    def __init__(self) -> None:
        self.now = 1_900_000_000.0

    def __call__(self) -> float:
        return self.now


class WatchedBody:
    """A body that records how many pooled connections are checked out at each read."""

    def __init__(self, content: bytes, engine: Any, seen: list[int]) -> None:
        self._body = io.BytesIO(content)
        self._engine = engine
        self._seen = seen
        self.closed = False

    def read(self, size: int = -1) -> bytes:
        self._seen.append(self._engine.pool.checkedout())
        return self._body.read(size)

    def close(self) -> None:
        self.closed = True


class WatchedStorage(t1b.InMemoryStorage):
    def __init__(self) -> None:
        super().__init__()
        self.engine: Any = None
        self.checked_out: list[int] = []
        self.bodies: list[WatchedBody] = []
        self.fail_reads = False

    def get_object(self, key: str) -> StoredObject | None:
        if self.fail_reads:
            raise ObjectStorageFailure("synthetic outage")
        item = self.objects.get(key)
        if item is None:
            return None
        content, content_type = item
        body = WatchedBody(content, self.engine, self.checked_out)
        self.bodies.append(body)
        return StoredObject(body, len(content), content_type, {})


@dataclass
class Api(t1b.VideoApi):
    clock: Clock | None = None
    statements: list[str] | None = None


@pytest.fixture
def api(monkeypatch: pytest.MonkeyPatch) -> Iterator[Api]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    database_name = database_url.rsplit("/", 1)[-1]
    if "be1_acceptance" not in database_name or "frc08_v3_t1c" not in database_name:
        pytest.fail("BE1_TEST_DATABASE_URL must be a disposable frc08_v3_t1c*be1_acceptance db")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_AI_PROVIDER", "disabled")
    monkeypatch.delenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", raising=False)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    app = create_app()
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("PostgreSQL runtime did not initialize")
    token = uuid4().hex[:8]
    subjects = {
        "parent": f"synthetic-t1c-parent-{token}",
        "other_parent": f"synthetic-t1c-parent2-{token}",
        "teacher": f"synthetic-t1c-teacher-{token}",
        "manager": f"synthetic-t1c-manager-{token}",
        "admin": f"synthetic-t1c-admin-{token}",
    }
    roles = {
        "parent": "parent",
        "other_parent": "parent",
        "teacher": "teacher",
        "manager": "school_manager",
        "admin": "platform_admin",
    }
    with runtime.session_factory.begin() as db:
        for key, subject in subjects.items():
            db.add(
                AdultIdentityModel(
                    subject=subject, issuer=ISSUER, state="active", account_role=roles[key]
                )
            )

    async def verified(
        x_test_principal: str | None = Header(default=None, alias="X-Test-Principal"),
    ) -> VerifiedPrincipal:
        # The real dependency answers 401 AUTHENTICATION_REQUIRED without a bearer.
        if x_test_principal is None:
            raise HTTPException(status_code=401, detail={"code": "AUTHENTICATION_REQUIRED"})
        return VerifiedPrincipal(subject=x_test_principal, issuer=ISSUER, roles=frozenset())

    script = VideoAdmissionScript()
    adapters = build_local_video_adapters(env="test", script=script)
    storage = WatchedStorage()
    storage.engine = runtime.engine
    clock = Clock()
    app.state.story_video_ports = adapters
    app.state.lesson_library_storage = storage
    app.state.story_playback_tokens = PlaybackTokenCodec(
        active_key_id="k1", keys={"k1": b"synthetic-t1c-signing-secret-0123456789"}, clock=clock
    )
    app.dependency_overrides[get_verified_adult] = verified
    statements: list[str] = []

    def _record(_conn: Any, _cursor: Any, statement: str, *_rest: Any) -> None:
        statements.append(statement)

    event.listen(runtime.engine, "before_cursor_execute", _record)
    try:
        with TestClient(app) as client:
            yield Api(
                app,
                client,
                storage,
                script,
                adapters,
                subjects["parent"],
                subjects["other_parent"],
                subjects["teacher"],
                subjects["manager"],
                subjects["admin"],
                clock=clock,
                statements=statements,
            )
    finally:
        event.remove(runtime.engine, "before_cursor_execute", _record)
        app.dependency_overrides.clear()
        runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


@pytest.fixture(autouse=True)
def _bind_api(api: Api) -> Iterator[None]:
    t1b._API = api
    yield
    t1b._API = None


# ----------------------------------------------------------------------------- helpers
def h(subject: str | None, token: str | None = None, **extra: str) -> dict[str, str]:
    result: dict[str, str] = {}
    if subject is not None:
        result["X-Test-Principal"] = subject
    if token is not None:
        result["X-Playback-Token"] = token
    result.update(extra)
    return result


def issue(api: Api, run: Any, owner: str | None = None) -> Any:
    return api.client.post(
        f"/v1/story-runs/{run.run_id}/playback-token", headers=h(owner or run.owner)
    )


def stream(
    api: Api,
    run: Any,
    token: str | None,
    *,
    owner: str | None = "",
    run_id: str | None = None,
    **extra: str,
) -> Any:
    subject = run.owner if owner == "" else owner
    return api.client.get(
        f"/v1/story-runs/{run_id or run.run_id}/playback", headers=h(subject, token, **extra)
    )


def token_of(response: Any) -> str:
    assert response.status_code == 200, response.text
    return str(response.json()["playback"]["token"])


def ready_with_token(api: Api) -> tuple[Any, str, str]:
    run, generation_id = t1b.video_ready(api)
    return run, generation_id, token_of(issue(api, run))


def content_of(api: Api, run: Any) -> bytes:
    key = str(t1b.generations(run.run_id)[0]["output_asset_ref"])
    return api.storage.objects[key][0]


def detail(api: Api, run: Any, owner: str | None = None, **extra: str) -> Any:
    return api.client.get(f"/v1/story-runs/{run.run_id}", headers=h(owner or run.owner, **extra))


def wire(response: Any) -> dict[str, Any]:
    return {k: v for k, v in response.json().items() if k != "correlation_id"}


def assert_clean(text: str) -> None:
    lowered = text.lower()
    for word in (*STORAGE_WORDS, *PROMPT_WORDS):
        assert word not in lowered, word


# ============================================================================== issue
def test_the_owner_gets_a_short_token_for_the_ready_video(api: Api) -> None:
    run, generation_id = t1b.video_ready(api)
    before = (t1b.run_row(run.run_id), len(t1b.generations(run.run_id)))
    response = issue(api, run)
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"request_id", "playback"}
    playback = body["playback"]
    assert set(playback) == {"token", "expires_at", "stream_path", "media_type", "asset_ref"}
    assert playback["media_type"] == "video/mp4"
    assert playback["stream_path"] == f"/v1/story-runs/{run.run_id}/playback"
    assert playback["asset_ref"] == f"vid_{generation_id}"
    assert playback["token"].startswith("ptk1.") and len(playback["token"]) <= 512
    assert response.headers["Cache-Control"] == "no-store"
    # no database write: the run, its clocks and the receipts did not move (a grant, not a change)
    after = (t1b.run_row(run.run_id), len(t1b.generations(run.run_id)))
    assert after[0] == before[0] and after[1] == before[1]
    assert t1b.receipts(run.run_id, "COMPLETE_RUN") == []
    # no storage word, key or URL anywhere in the answer or its headers
    assert_clean(response.text.replace(playback["token"], "") + str(dict(response.headers)))


def test_a_token_is_not_issued_to_a_foreign_account_a_missing_run_or_another_role(
    api: Api,
) -> None:
    run, _ = t1b.video_ready(api)
    missing = api.client.post(f"/v1/story-runs/{uuid4()}/playback-token", headers=h(api.parent))
    foreign = issue(api, run, api.other_parent)
    assert missing.status_code == foreign.status_code == 404
    assert wire(missing) == wire(foreign)
    for subject in (api.teacher, api.manager, api.admin):
        assert issue(api, run, subject).status_code == 404
    assert api.client.post(f"/v1/story-runs/{run.run_id}/playback-token").status_code == 401


def test_no_token_before_the_video_is_ready(api: Api) -> None:
    script_run = t1b.new_script_run(api)
    assert issue(api, script_run).status_code == 409  # SCRIPT_REVIEW, no video at all
    queued = t1b.new_script_run(api)
    assert t1b.video_request(api, queued).status_code == 202
    assert t1b.run_row(queued.run_id)["run_state"] == "VIDEO_QUEUED"
    assert issue(api, queued).status_code == 409
    api.script.quotas.append(QuotaStatus.UNAVAILABLE)
    pending = t1b.new_script_run(api)
    assert t1b.video_request(api, pending).status_code == 202
    assert t1b.run_row(pending.run_id)["run_state"] == "VIDEO_ADMISSION_PENDING"
    assert issue(api, pending).status_code == 409


def test_a_rejected_generation_gets_no_token_even_though_the_pointer_still_names_it(
    api: Api,
) -> None:
    run, generation_id = t1b.video_ready(api)
    old = token_of(issue(api, run))
    assert t1b.unsuitable(api, run, generation_id).status_code == 200
    row = t1b.run_row(run.run_id)
    assert str(row["current_video_generation_id"]) == generation_id  # the pointer stays (T-1b D3)
    assert t1b.generations(run.run_id)[0]["state"] == "REJECTED_BY_ADULT"
    assert issue(api, run).status_code == 409
    gone = stream(api, run, old)
    assert gone.status_code == 404
    assert gone.json()["code"] == "RESOURCE_NOT_FOUND"


def test_a_completed_run_gets_no_token_and_the_old_token_stops_working(api: Api) -> None:
    run, _generation_id, token = ready_with_token(api)
    assert stream(api, run, token).status_code == 200
    assert t1b.complete(api, run).status_code == 200
    assert issue(api, run).status_code == 409  # Q5: l.1676 "active until complete"
    assert stream(api, run, token).status_code == 404


def test_a_cancelled_run_ends_playback_for_the_token_and_for_a_new_grant(api: Api) -> None:
    run, _generation_id, token = ready_with_token(api)
    assert t1b.cancel(api, run).status_code == 202
    assert stream(api, run, token).status_code == 404
    assert issue(api, run).status_code == 404  # the run is being deleted: uniform 404


def test_a_blocked_generation_gets_no_token(api: Api) -> None:
    blocked_run = t1b.new_script_run(api)
    blocked_id = str(
        t1b.video_request(api, blocked_run).json()["video_generation"]["generation_id"]
    )
    renderer = FixtureVideoRenderer()
    renderer.results[blocked_id] = VideoRenderResult(
        content=b"x", media_type="video/mp4", safety_passed=False
    )
    t1b.runner(api, renderer).run_to_end(blocked_id)
    assert t1b.run_row(blocked_run.run_id)["run_state"] == "SAFETY_BLOCKED"
    assert issue(api, blocked_run).status_code == 409


# ============================================================================== stream
def test_the_stream_returns_the_exact_bytes_with_the_safe_header_set(api: Api) -> None:
    run, generation_id, token = ready_with_token(api)
    content = content_of(api, run)
    response = stream(api, run, token)
    assert response.status_code == 200
    assert response.content == content
    headers = response.headers
    assert headers["content-type"] == "video/mp4"
    assert headers["accept-ranges"] == "bytes"
    assert headers["content-length"] == str(len(content))
    assert headers["content-disposition"] == "inline"
    assert headers["cache-control"] == "private, no-store"
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["referrer-policy"] == "no-referrer"
    assert "x-request-id" in headers
    assert_clean(str(dict(headers)))
    assert token not in str(dict(headers))
    # the same token streams again (a short-lived grant, not a one-time ticket)
    assert stream(api, run, token).content == content


def test_ranges_are_honoured_and_a_bad_range_is_416_with_the_size(api: Api) -> None:
    run, generation_id, token = ready_with_token(api)
    content = content_of(api, run)
    size = len(content)
    first = stream(api, run, token, Range="bytes=0-9")
    assert first.status_code == 206 and first.content == content[:10]
    assert first.headers["content-range"] == f"bytes 0-9/{size}"
    assert first.headers["content-length"] == "10"
    tail = stream(api, run, token, Range="bytes=12-")
    assert tail.status_code == 206 and tail.content == content[12:]
    suffix = stream(api, run, token, Range="bytes=-5")
    assert suffix.status_code == 206 and suffix.content == content[-5:]
    clipped = stream(api, run, token, Range=f"bytes={size - 3}-{size + 500}")
    assert clipped.status_code == 206 and clipped.content == content[-3:]
    for bad in (
        f"bytes={size}-",
        "bytes=5-2",
        "bytes=0-1,4-5",
        "items=0-1",
        "bytes=abc",
        "bytes=-",
    ):
        refused = stream(api, run, token, Range=bad)
        assert refused.status_code == 416, bad
        assert refused.headers["content-range"] == f"bytes */{size}"
        assert refused.json()["code"] == "RANGE_NOT_SATISFIABLE"
    # a refused range leaves no open body behind
    assert all(body.closed for body in api.storage.bodies)  # type: ignore[attr-defined]


def test_a_valid_token_in_another_authenticated_hand_is_the_uniform_404(api: Api) -> None:
    run, _generation_id, token = ready_with_token(api)
    stolen = stream(api, run, token, owner=api.other_parent)
    unknown = stream(api, run, token, owner=api.other_parent, run_id=str(uuid4()))
    assert stolen.status_code == unknown.status_code == 404
    for subject in (api.teacher, api.manager, api.admin):
        assert stream(api, run, token, owner=subject).status_code == 404
    assert wire(stolen) == wire(unknown)
    # the owner still streams
    assert stream(api, run, token).status_code == 200


def test_the_bearer_is_required_and_the_token_alone_is_not_enough(api: Api) -> None:
    run, _generation_id, token = ready_with_token(api)
    without_bearer = stream(api, run, token, owner=None)
    assert without_bearer.status_code == 401
    assert without_bearer.json()["code"] == "AUTHENTICATION_REQUIRED"


def test_a_missing_tampered_or_expired_token_is_401_before_any_store_read(api: Api) -> None:
    run, _generation_id, token = ready_with_token(api)
    statements_before = len(api.statements or [])
    missing = stream(api, run, None)
    assert missing.status_code == 401 and missing.json()["code"] == "INVALID_TOKEN"
    header, payload, mac = token.split(".")[1:]
    flipped = mac[:-2] + ("AA" if not mac.endswith("AA") else "BB")
    for bad in (
        f"ptk1.{header}.{payload}.{flipped}",
        f"ptk1.{header}.{payload}",
        f"ptk2.{header}.{payload}.{mac}",
        "ptk1." + "A" * 600,
        "not-a-token",
        token + "x",
        token.upper(),
    ):
        refused = stream(api, run, bad)
        assert refused.status_code == 401, bad
        assert refused.json()["code"] == "INVALID_TOKEN"
        assert bad not in refused.text
    assert len(api.statements or []) == statements_before  # no database statement ran
    assert api.clock is not None
    api.clock.now += 301
    expired = stream(api, run, token)
    assert expired.status_code == 401 and expired.json()["code"] == "TOKEN_EXPIRED"
    assert token not in expired.text


def test_a_token_of_another_run_or_generation_is_the_uniform_404(api: Api) -> None:
    run_a, _g_a, token_a = ready_with_token(api)
    run_b, _g_b = t1b.video_ready(api, t1b.new_script_run(api, api.other_parent))
    token_b = token_of(issue(api, run_b))
    # A's token on B's path, with B's owner or A's owner
    assert stream(api, run_b, token_a, owner=api.other_parent).status_code == 404
    assert stream(api, run_a, token_b).status_code == 404
    assert stream(api, run_a, token_a).status_code == 200
    assert stream(api, run_b, token_b, owner=api.other_parent).status_code == 200


def test_a_missing_object_is_404_and_a_failing_store_is_503(api: Api) -> None:
    run, generation_id, token = ready_with_token(api)
    key = str(t1b.generations(run.run_id)[0]["output_asset_ref"])
    content = api.storage.objects.pop(key)
    gone = stream(api, run, token)
    assert gone.status_code == 404 and gone.json()["code"] == "RESOURCE_NOT_FOUND"
    api.storage.objects[key] = content
    api.storage.fail_reads = True  # type: ignore[attr-defined]
    down = stream(api, run, token)
    assert down.status_code == 503 and down.json()["code"] == "STORAGE_UNAVAILABLE"
    assert_clean(down.text)


def test_an_object_over_the_ceiling_is_refused_before_the_first_byte(api: Api) -> None:
    run, _generation_id, token = ready_with_token(api)
    api.app.state.story_playback_max_object_bytes = 4
    refused = stream(api, run, token)
    assert refused.status_code == 503 and refused.json()["code"] == "STORAGE_UNAVAILABLE"
    assert all(body.closed for body in api.storage.bodies)  # type: ignore[attr-defined]
    assert api.storage.checked_out == []  # type: ignore[attr-defined]  # nothing was read


def test_no_database_connection_is_held_while_the_chunks_are_produced(api: Api) -> None:
    run, _generation_id, token = ready_with_token(api)
    storage: WatchedStorage = api.storage  # type: ignore[assignment]
    storage.checked_out.clear()
    big = b"v" * (64 * 1024 * 3 + 17)
    key = str(t1b.generations(run.run_id)[0]["output_asset_ref"])
    storage.objects[key] = (big, "video/mp4")
    response = stream(api, run, token)
    assert response.status_code == 200 and response.content == big
    assert len(storage.checked_out) >= 4  # one read per 64 KiB chunk and the end
    assert set(storage.checked_out) == {0}, "a pooled connection was open during the download"
    assert storage.bodies[-1].closed
    # a range that skips into the object reads and discards, still with no connection held
    storage.checked_out.clear()
    skipped = stream(api, run, token, Range="bytes=100000-100009")
    assert skipped.status_code == 206 and skipped.content == big[100000:100010]
    assert set(storage.checked_out) == {0}


def test_the_head_method_is_not_defined(api: Api) -> None:
    run, _generation_id, token = ready_with_token(api)
    response = api.client.head(f"/v1/story-runs/{run.run_id}/playback", headers=h(run.owner, token))
    assert response.status_code == 405


def test_the_token_never_reaches_a_log_line_a_url_or_a_body(
    api: Api, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    run, _generation_id = t1b.video_ready(api)
    issued = issue(api, run)
    token = token_of(issued)
    streamed = stream(api, run, token)
    assert streamed.status_code == 200
    refused = stream(api, run, token, owner=api.other_parent)
    assert token not in caplog.text
    assert token not in refused.text and token not in str(streamed.url)
    assert token not in str(dict(streamed.headers)) and token not in str(dict(refused.headers))


# ============================================================================== detail
def test_a_run_without_a_video_has_a_null_video_the_quota_marker_and_a_timeline(
    api: Api,
) -> None:
    run = t1b.new_script_run(api)
    response = detail(api, run)
    assert response.status_code == 200, response.text
    story_run = response.json()["story_run"]
    assert story_run["video"] is None
    assert story_run["quota"] == {
        "state": "UNAVAILABLE",
        "granted": None,
        "used": None,
        "available": None,
        "month": None,
    }
    assert [event["event"] for event in story_run["timeline"]] == ["RUN_CREATED"]
    assert response.headers["etag"].startswith('"d1-') and len(response.headers["etag"]) == 37
    assert response.headers["cache-control"] == "private, no-cache"
    assert response.headers["vary"] == "Authorization"
    # the older fields are unchanged
    for name in ("run_id", "run_revision", "run_state", "story", "job_state", "created_at"):
        assert name in story_run


def test_the_detail_of_a_ready_video_shows_state_job_scenes_playback_and_counts(
    api: Api,
) -> None:
    run, generation_id = t1b.video_ready(api)
    response = detail(api, run)
    assert response.status_code == 200, response.text
    story_run = response.json()["story_run"]
    video = story_run["video"]
    assert set(video) == {
        "current_generation_id",
        "generation_no",
        "kind",
        "state",
        "job",
        "scenes",
        "playback",
        "video_requests_used",
        "video_requests_remaining",
        "admission_pending",
        "history",
    }
    assert video["current_generation_id"] == generation_id
    assert video["generation_no"] == 1 and video["kind"] == "INITIAL" and video["state"] == "READY"
    assert video["job"]["state"] == "succeeded" and video["job"]["error_code"] is None
    assert video["job"]["retryable"] is False and video["job"]["stage"] is None
    assert video["video_requests_used"] == 1 and video["video_requests_remaining"] == 2
    assert video["admission_pending"] is False
    assert video["playback"] == {
        "state": "AVAILABLE",
        "asset_ref": f"vid_{generation_id}",
        "token_route": f"/v1/story-runs/{run.run_id}/playback-token",
    }
    assert [item["generation_id"] for item in video["history"]] == [generation_id]
    assert len(video["scenes"]) == 5
    assert [scene["scene_index"] for scene in video["scenes"]] == [1, 2, 3, 4, 5]
    assert {scene["state"] for scene in video["scenes"]} <= {"QUEUED", "GENERATING", "READY"}
    events = [event["event"] for event in story_run["timeline"]]
    assert events[0] == "RUN_CREATED"
    assert {"VIDEO_REQUESTED", "VIDEO_ACCEPTED", "VIDEO_STARTED", "VIDEO_READY"} <= set(events)
    text = response.text
    assert_clean(text)
    assert "scene_index" in text and "narration" in text  # the display story itself is unchanged
    # the physical key never appears: the job and playback blocks hold handles only
    key = str(t1b.generations(run.run_id)[0]["output_asset_ref"])
    assert key not in text


def test_the_composition_reads_one_bounded_story_owned_set_and_nothing_cross_schema(
    api: Api,
) -> None:
    run, _generation_id = t1b.video_ready(api)
    statements = api.statements
    assert statements is not None
    statements.clear()
    assert detail(api, run).status_code == 200
    video_reads = [text for text in statements if "video_generations" in text]
    scene_reads = [text for text in statements if "video_generation_scenes" in text]
    assert len(video_reads) <= 3 and len(scene_reads) == 1  # rows, scenes, the pointer join
    for text in statements:
        lowered = text.lower()
        assert "ai_jobs" not in lowered and "billing" not in lowered
        assert "core_asset" not in lowered
    assert any("LIMIT" in text.upper() for text in video_reads)


def test_the_etag_changes_with_the_video_and_a_matching_tag_is_304_after_authorisation(
    api: Api,
) -> None:
    run, generation_id = t1b.video_ready(api)
    first = detail(api, run)
    etag = first.headers["etag"]
    again = detail(api, run)
    assert again.headers["etag"] == etag  # stable: no per-call value (request_id) in the input
    assert first.json()["request_id"] != again.json()["request_id"]
    cached = detail(api, run, **{"If-None-Match": etag})
    assert cached.status_code == 304 and cached.content == b""
    assert cached.headers["etag"] == etag
    assert cached.headers["cache-control"] == "private, no-cache"
    assert detail(api, run, **{"If-None-Match": f'"other", W/{etag}'}).status_code == 304
    assert detail(api, run, **{"If-None-Match": '"d1-0000"'}).status_code == 200
    # authorisation first: another Parent with the right tag still gets the uniform 404, no 304
    foreign = detail(api, run, api.other_parent, **{"If-None-Match": etag})
    assert foreign.status_code == 404 and foreign.headers.get("etag") is None
    # a generation state change that bumps no run revision changes the tag
    with api.sessions().begin() as db:
        db.execute(
            update(t1b.story_tables.video_generation_scenes)
            .where(t1b.story_tables.video_generation_scenes.c.video_generation_id == generation_id)
            .values(state="FAILED")
        )
    changed = detail(api, run, **{"If-None-Match": etag})
    assert changed.status_code == 200 and changed.headers["etag"] != etag
    # and the run moving on changes it again
    moved = t1b.unsuitable(api, run, generation_id)
    assert moved.status_code == 200
    final = detail(api, run)
    assert final.headers["etag"] not in {etag, changed.headers["etag"]}
    assert final.json()["story_run"]["video"]["playback"] == {
        "state": "HIDDEN",
        "asset_ref": None,
        "token_route": None,
    }
    assert final.json()["story_run"]["video"]["state"] == "REJECTED_BY_ADULT"


def test_a_pending_intent_a_running_job_and_a_blocked_one_show_in_the_detail(api: Api) -> None:
    pending_run = t1b.new_script_run(api)
    api.script.quotas.append(QuotaStatus.UNAVAILABLE)
    response = t1b.video_request(api, pending_run)
    assert response.status_code == 202
    video = detail(api, pending_run).json()["story_run"]["video"]
    assert video["state"] == "ADMISSION_PENDING" and video["admission_pending"] is True
    assert video["job"] is None and video["generation_no"] is None
    assert video["video_requests_used"] == 0 and video["video_requests_remaining"] == 3
    assert video["history"] == [] and video["scenes"] == []
    assert video["playback"]["state"] == "UNAVAILABLE"

    running_run = t1b.new_script_run(api, api.other_parent)
    accepted = t1b.video_request(api, running_run).json()["video_generation"]
    t1b.runner(api).step(accepted["generation_id"])  # ACCEPTED -> QUEUED
    t1b.runner(api).step(accepted["generation_id"])  # QUEUED -> GENERATING
    running = detail(api, running_run, api.other_parent).json()["story_run"]["video"]
    assert running["state"] == "GENERATING" and running["job"]["state"] == "running"
    assert running["job"]["stage"] == "generating" and running["admission_pending"] is False
    assert running["playback"]["state"] == "UNAVAILABLE"


def test_a_blocked_and_a_failed_video_show_only_the_closed_public_failure_codes(api: Api) -> None:
    blocked_run = t1b.new_script_run(api)
    generation_id = str(
        t1b.video_request(api, blocked_run).json()["video_generation"]["generation_id"]
    )
    renderer = FixtureVideoRenderer()
    renderer.results[generation_id] = VideoRenderResult(
        content=b"x", media_type="video/mp4", safety_passed=False
    )
    t1b.runner(api, renderer).run_to_end(generation_id)
    blocked_run_body = detail(api, blocked_run).json()["story_run"]
    # the run-level code is the closed public one too (a raw stored code never reaches the client)
    assert blocked_run_body["error_code"] in (None, "VIDEO_SAFETY_BLOCKED")
    blocked = blocked_run_body["video"]
    assert blocked["state"] == "SAFETY_BLOCKED"
    assert blocked["job"]["state"] == "blocked_unsafe"
    assert blocked["job"]["error_code"] == "VIDEO_SAFETY_BLOCKED"
    assert blocked["job"]["retryable"] is False
    assert blocked["playback"]["state"] == "UNAVAILABLE"

    failed_run = t1b.new_script_run(api, api.other_parent)
    failed_id = str(t1b.video_request(api, failed_run).json()["video_generation"]["generation_id"])
    renderer = FixtureVideoRenderer()
    renderer.results[failed_id] = VideoRenderResult(
        content=b"x", media_type="video/mp4", failure_code="PROVIDER_STACK_TRACE_RAW"
    )
    t1b.runner(api, renderer).run_to_end(failed_id)
    failed = detail(api, failed_run, api.other_parent)
    video = failed.json()["story_run"]["video"]
    assert failed.json()["story_run"]["error_code"] == "VIDEO_TECHNICAL_FAILURE"
    assert "PROVIDER_STACK_TRACE_RAW" not in failed.text
    assert video["state"] == "FAILED" and video["job"]["state"] == "failed_exhausted"
    assert video["job"]["error_code"] == "VIDEO_TECHNICAL_FAILURE"
    assert "stack_trace" not in failed.text.lower()
    # the jobs route shows the same closed code for the same row (one mapper)
    job_id = video["job"]["job_id"]
    job = api.client.get(f"/v1/jobs/{job_id}", headers=h(api.other_parent))
    assert job.status_code == 200 and job.json()["failure"]["code"] == "VIDEO_TECHNICAL_FAILURE"


def test_the_counts_follow_one_two_and_three_accepted_requests(api: Api) -> None:
    run, first = t1b.video_ready(api)
    generator = t1b.make_rewritable(api, run)
    assert generator.calls == 0
    assert detail(api, run).json()["story_run"]["video"]["video_requests_remaining"] == 2
    assert t1b.unsuitable(api, run, first).status_code == 200
    second = t1b.regenerate(api, run)
    video = detail(api, run).json()["story_run"]["video"]
    assert video["video_requests_used"] == 2 and video["video_requests_remaining"] == 1
    assert video["generation_no"] == 2 and video["kind"] == "QUALITY_REGEN"
    assert video["current_generation_id"] == second
    assert [item["generation_no"] for item in video["history"]] == [1, 2]
    assert [item["state"] for item in video["history"]] == ["REJECTED_BY_ADULT", "READY"]
    assert t1b.unsuitable(api, run, second).status_code == 200
    third = t1b.regenerate(api, run)
    video = detail(api, run).json()["story_run"]["video"]
    assert video["video_requests_used"] == 3 and video["video_requests_remaining"] == 0
    assert video["current_generation_id"] == third and video["generation_no"] == 3
    assert [item["generation_no"] for item in video["history"]] == [1, 2, 3]
    assert len(video["history"]) <= 3
    events = [event["event"] for event in detail(api, run).json()["story_run"]["timeline"]]
    assert events.count("VIDEO_REQUESTED") == 3 and events.count("VIDEO_REJECTED_BY_ADULT") == 2


def test_a_completed_run_shows_playback_unavailable_and_a_deleting_run_the_lifecycle_envelope(
    api: Api,
) -> None:
    run, _generation_id = t1b.video_ready(api)
    assert t1b.complete(api, run).status_code == 200
    story_run = detail(api, run).json()["story_run"]
    assert story_run["run_state"] == "COMPLETED"
    assert story_run["video"]["state"] == "READY"
    assert story_run["video"]["playback"]["state"] == "UNAVAILABLE"
    assert story_run["video"]["playback"]["asset_ref"] is None
    assert story_run["timeline"][-1]["event"] == "RUN_COMPLETED"
    deleting_run, _ = t1b.video_ready(api, t1b.new_script_run(api))
    assert t1b.cancel(api, deleting_run).status_code == 202
    body = detail(api, deleting_run)
    assert body.status_code == 200 and "lifecycle" in body.json() and "story_run" not in body.json()
    assert "etag" not in body.headers


def test_a_foreign_account_and_a_wrong_role_get_one_uniform_404_for_the_detail(api: Api) -> None:
    run, _ = t1b.video_ready(api)
    unknown = api.client.get(f"/v1/story-runs/{uuid4()}", headers=h(api.parent))
    for subject in (api.other_parent, api.teacher, api.manager, api.admin):
        response = detail(api, run, subject)
        assert response.status_code == 404
        assert wire(response) == wire(unknown)
