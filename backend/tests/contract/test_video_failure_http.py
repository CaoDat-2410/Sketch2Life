"""Real HTTP +MEMORY/ASSUMED control, not production auth/session effects."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from sketch2life.domain.ai_jobs.model import JobState
from sketch2life.domain.knowledge_video.model import VideoError
from sketch2life.interfaces.http.routers.knowledge_video import VideoIdentity
from sketch2life.interfaces.http.routers.video_failure import build_video_failure_router
from tests.video_failure_fixtures import harness, receipt

URL = "/api/collaboration/v1/knowledge-videos/video/failure-dispositions"
HEADERS = {"Authorization": "Fixture teacher", "Idempotency-Key": "key", "If-Match": '"7"'}


def body(action="skip", **changes):
    return (
        dict(
            action=action,
            reason="fixture reason",
            expected_video_version=2,
            expected_job_revision=9,
            expected_session_revision=4,
        )
        | changes
    )


@pytest.fixture
def h():
    runtime = harness()
    actor = [VideoIdentity("teacher", "school", "session")]

    def resolve(request):
        return actor[0] if request.headers.get("authorization") == "Fixture teacher" else None

    app = FastAPI()
    app.include_router(build_video_failure_router(runtime.service, resolve, max_body_bytes=2048))
    with TestClient(app) as client:
        yield SimpleNamespace(runtime=runtime, client=client, actor=actor, resolve=resolve)


def post(h, payload=None, headers=None):
    return h.client.post(
        URL,
        json=body() if payload is None else payload,
        headers=HEADERS if headers is None else headers,
    )


@pytest.mark.parametrize(
    "action,outcome",
    [
        ("retry", "retry_pending"),
        ("skip", "skipped_by_teacher"),
        ("end_session", "session_ended_early"),
    ],
)
def test_data28_truthful_three_actions_and_original_replay(h, action, outcome):
    first = post(h, body(action))
    assert first.status_code == 200, first.text
    data = first.json()["data"]
    assert data["action"] == action and data["outcome"] == outcome
    assert data["recorded_by"] == "teacher" and data["prior_failure_ref"]["ref"] == "failure"
    assert data["new_job_id"] == ("new.job" if action == "retry" else None)
    assert data["video_run_revision"] == (1 if action == "retry" else 7)
    assert post(h, body(action)).json()["data"] == data
    assert h.runtime.bridge.execute.call_count == 1
    assert first.headers["cache-control"] == "no-store"
    assert first.headers["vary"] == "Authorization"
    assert "url" not in first.text and "generated" not in first.text


@pytest.mark.parametrize("action", ["retry", "skip", "end_session"])
def test_pending_extension_not_fake_upstream_confirmed_fields(h, action):
    h.runtime.bridge.execute.side_effect = TimeoutError("synthetic_sensitive")
    result = post(h, body(action))
    assert result.status_code == 202 and result.json()["data"]["status"] == "pending"
    assert set(result.json()["data"]) == {
        "contract_version",
        "status",
        "disposition_id",
        "operation_key",
        "reason_code",
    }
    assert "outcome" not in result.text and "synthetic_sensitive" not in result.text


@pytest.mark.parametrize(
    "field",
    [
        "organization_id",
        "session_id",
        "principal_id",
        "role",
        "approved",
        "budget_granted",
        "expected_run_revision",
        "endpoint",
        "api_key",
        "checkpoint",
    ],
)
def test_spoof_fields_rejected_no_echo(h, field):
    result = post(h, body(**{field: "synthetic_sensitive"}))
    assert result.status_code == 422 and "synthetic_sensitive" not in result.text
    assert not h.runtime.store.rows


@pytest.mark.parametrize(
    "field,value",
    [
        ("reason", " "),
        ("reason", "x" * 201),
        ("expected_video_version", True),
        ("expected_job_revision", "9"),
        ("expected_session_revision", True),
        ("expected_session_revision", -1),
        ("expected_job_revision", 2**63),
        ("retry_authorization_note", "budget"),
        ("action", "auto_skip"),
    ],
)
def test_strict_commands(h, field, value):
    assert post(h, body(**{field: value})).status_code == 422
    assert not h.runtime.store.rows


@pytest.mark.parametrize(
    "etag", [None, 'W/"7"', "7", '"0"', '"07"', "*", '"1", "7"', '"9223372036854775808"']
)
def test_primary_precondition_is_strong_run_revision(h, etag):
    headers = {k: v for k, v in HEADERS.items() if k != "If-Match"}
    if etag is not None:
        headers["If-Match"] = etag
    assert post(h, headers=headers).status_code == (428 if etag is None else 400)


@pytest.mark.parametrize("etag", ['"2"', '"9"', '"4"'])
def test_content_job_session_revisions_not_run_revision(h, etag):
    assert post(h, headers=HEADERS | {"If-Match": etag}).status_code == 409
    h.runtime.bridge.execute.assert_not_called()


@pytest.mark.parametrize("key", [None, "", "with space", "x" * 121, "../key"])
def test_required_valid_idempotency_key(h, key):
    headers = {k: v for k, v in HEADERS.items() if k != "Idempotency-Key"}
    if key is not None:
        headers["Idempotency-Key"] = key
    assert post(h, headers=headers).status_code == 400


@pytest.mark.parametrize("header", ["Idempotency-Key", "If-Match", "Authorization"])
def test_duplicate_headers(h, header):
    headers = list(HEADERS.items()) + [(header, "other")]
    assert post(h, headers=headers).status_code == (401 if header == "Authorization" else 400)


def test_identity_before_parsing_invalid_body(h):
    result = h.client.post(URL, content="synthetic_sensitive")
    assert result.status_code == 401 and "synthetic_sensitive" not in result.text


@pytest.mark.parametrize("actor", ["child", "device", "admin"])
def test_no_teacher_action_from_child_device_admin(h, actor):
    h.actor[0] = VideoIdentity(actor, "school", "session")
    assert post(h).status_code == 403
    assert not h.runtime.store.rows


@pytest.mark.parametrize(
    "raw",
    [
        b"{",
        b"[]",
        b"null",
        b"\xff",
        b'{"a":NaN}',
        b'{"a":Infinity}',
        b'{"a":1,"a":2}',
        b'{"nested":{"a":1,"a":2}}',
    ],
)
def test_malformed_json_no_effect(h, raw):
    result = h.client.post(URL, content=raw, headers=HEADERS | {"Content-Type": "application/json"})
    assert result.status_code == 422
    assert not h.runtime.store.rows


def test_actual_stream_bound_and_type_encoding(h):
    headers = HEADERS | {"Content-Type": "application/json"}
    assert (
        h.client.post(
            URL, content=(b" " * 1024 for _ in range(3)), headers=headers | {"Content-Length": "1"}
        ).status_code
        == 413
    )
    assert h.client.post(URL, content="{}", headers=HEADERS).status_code == 415
    assert post(h, headers=headers | {"Content-Encoding": "gzip"}).status_code == 415
    assert not h.runtime.store.rows


def test_server_scope_not_client_headers(h):
    assert (
        post(
            h, headers=HEADERS | {"X-Session-Id": "foreign", "X-Organization-Id": "foreign"}
        ).status_code
        == 200
    )
    assert next(iter(h.runtime.store.rows.values())).context.organization_id == "school"


@pytest.mark.parametrize(
    "state",
    [
        JobState.QUEUED,
        JobState.RUNNING,
        JobState.FAILED_RETRYABLE,
        JobState.SUCCEEDED,
        JobState.CANCELLED,
    ],
)
def test_only_exhausted_source_not_generating_or_success(h, state):
    # Forged native output revalidated, not authenticated current state proof.
    object.__setattr__(h.runtime.boundary.target, "state", state)
    result = post(h)
    assert result.status_code == 409 and result.json()["error"]["code"] == "VIDEO_NOT_EXHAUSTED"
    assert not h.runtime.store.rows


def test_budget_note_and_duplicate_different_action(h):
    h.runtime.boundary.retry_allowed = False
    assert post(h, body("retry", retry_authorization_note="grant please")).status_code == 409
    assert post(h).status_code == 200
    assert post(h, body("end_session")).status_code == 409
    assert (
        post(h, body("end_session"), headers=HEADERS | {"Idempotency-Key": "other"}).status_code
        == 409
    )
    assert h.runtime.bridge.execute.call_count == 1


def test_lost_ack_then_original_lookup_and_partial_end_never_confirmed(h):
    h.runtime.bridge.execute.side_effect = TimeoutError()
    assert post(h, body("end_session")).status_code == 202
    i = next(iter(h.runtime.store.rows.values()))
    h.runtime.bridge.lookup.return_value = receipt(i)
    assert post(h, body("end_session")).status_code == 200
    assert h.runtime.bridge.execute.call_count == 1


@pytest.mark.parametrize(
    "exception", [RuntimeError("synthetic_sensitive"), VideoError("internal.synthetic_sensitive")]
)
def test_unknown_error_redaction(h, monkeypatch, exception):
    monkeypatch.setattr(h.runtime.service, "decide", Mock(side_effect=exception))
    result = post(h)
    assert result.status_code == 503 and "synthetic_sensitive" not in result.text
    assert result.json()["error"]["retryable"]


def test_missing_service_closed_and_no_default_mount(h):
    app = FastAPI()
    app.include_router(build_video_failure_router(None, h.resolve, max_body_bytes=2048))
    with TestClient(app) as client:
        result = client.post(URL, json=body(), headers=HEADERS)
        assert result.status_code == 503
    path = Path(__file__).resolve().parents[2] / "src/sketch2life/interfaces/http/app.py"
    assert "build_video_failure_router" not in path.read_text(encoding="utf-8")


@pytest.mark.parametrize("limit", [True, 0, -1, "2048"])
def test_explicit_body_limit(h, limit):
    with pytest.raises(ValueError):
        build_video_failure_router(h.runtime.service, h.resolve, max_body_bytes=limit)


def test_foreign_or_forged_result_projection_is_not_exposed(h, monkeypatch):
    original = h.runtime.service.decide

    def foreign(*args):
        i = original(*args)
        object.__setattr__(i.context, "video_id", "foreign")
        return i

    monkeypatch.setattr(h.runtime.service, "decide", foreign)
    assert post(h).status_code == 503
