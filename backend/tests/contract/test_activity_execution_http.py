"""Real CMD-45 transport +MEMORY assumed owners, not production identity/adoption."""

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from sketch2life.domain.knowledge_video.model import VideoError
from sketch2life.interfaces.http.routers.activity_execution import build_activity_execution_router
from sketch2life.interfaces.http.routers.knowledge_video import VideoIdentity
from tests.activity_execution_fixtures import harness

URL = "/api/collaboration/v1/activity-assignments"
HEADERS = {"Authorization": "Fixture teacher", "Idempotency-Key": "key"}


def body(**changes):
    return (
        dict(
            action="select",
            activity_ref={"activity_id": "activity", "version": 1, "hash": "a" * 64},
            audience_scope={"session_id": "session", "group_ids": ["group"]},
        )
        | changes
    )


@pytest.fixture
def h():
    runtime = harness()
    identities = [VideoIdentity("teacher", "school", "session")]

    def resolve(request):
        return identities[0] if request.headers.get("authorization") == "Fixture teacher" else None

    app = FastAPI()
    app.include_router(
        build_activity_execution_router(runtime.service, resolve, max_body_bytes=4096)
    )
    with TestClient(app) as client:
        yield SimpleNamespace(
            runtime=runtime, client=client, identities=identities, resolve=resolve
        )


def post(h, payload=None, headers=None):
    return h.client.post(
        URL,
        json=body() if payload is None else payload,
        headers=HEADERS if headers is None else headers,
    )


def advance(h, previous, action, **changes):
    data = previous.json()["data"]
    payload = dict(action=action, assignment_id=data["assignment_id"])
    if action in {"confirm_ready", "start"}:
        payload["feasibility_confirmation"] = {"materials_available": True, "safety_checked": True}
    if action in {"skip", "interrupt"}:
        payload["reason"] = "Teacher explicitly chose"
    return post(
        h,
        payload | changes,
        HEADERS
        | {
            "Idempotency-Key": "key." + str(data["assignment_revision"]) + action,
            "If-Match": '"' + str(data["assignment_revision"]) + '"',
        },
    )


def test_local_group_snapshot_prepare_start_finish_and_truthful_pending_handoff(h):
    selected = post(h, body(teacher_adaptations={"instructions": "Group B new instructions"}))
    assert selected.status_code == 200, selected.text
    data = selected.json()["data"]
    assert data["effective_activity_snapshot"]["instructions"] == "Group B new instructions"
    assert data["source_activity_ref"]["hash"] == "a" * 64
    assert data["learning_objective_refs"][0]["ref"] == "objective"
    assert data["outcome_delivery"] == "not_required"
    confirmed = advance(h, selected, "confirm_ready")
    assert confirmed.status_code == 200 and confirmed.json()["data"]["state"] == "ready"
    started = advance(h, confirmed, "start")
    assert started.status_code == 200 and started.json()["data"]["state"] == "in_progress"
    finished = advance(h, started, "finish")
    assert finished.status_code == 200 and finished.json()["data"]["state"] == "completed"
    assert finished.json()["data"]["outcome_delivery"] == "pending"
    assert finished.headers["cache-control"] == "no-store"
    assert finished.headers["vary"] == "Authorization"
    assert not any(
        word in finished.text
        for word in (
            "child1",
            "child2",
            "age_months",
            "portfolio_saved",
            "reflection_record",
            "access_url",
        )
    )
    h.runtime.consumer.send.assert_not_called()


@pytest.mark.parametrize("action", ["skip", "interrupt"])
def test_skip_interrupt_not_completed(h, action):
    row = post(h)
    if action == "interrupt":
        row = advance(h, advance(h, row, "confirm_ready"), "start")
    result = advance(h, row, action)
    assert result.status_code == 200
    assert result.json()["data"]["state"] == ("skipped" if action == "skip" else "interrupted")


@pytest.mark.parametrize(
    "field",
    [
        "organization_id",
        "principal_id",
        "session_id",
        "role",
        "policy_allowed",
        "child_achievements",
        "portfolio_saved",
        "expected_revision",
        "api_key",
    ],
)
def test_spoof_fields_closed_without_echo(h, field):
    result = post(h, body(**{field: "synthetic_sensitive"}))
    assert result.status_code == 422 and "synthetic_sensitive" not in result.text
    assert not h.runtime.store.rows


@pytest.mark.parametrize(
    "action", ["start", "finish", "confirm_ready", "skip", "interrupt", "adapt"]
)
def test_existing_actions_require_assignment_and_action_fields(h, action):
    assert post(h, {"action": action}).status_code == 422


@pytest.mark.parametrize("header", ["Authorization", "Idempotency-Key"])
def test_duplicate_headers(h, header):
    assert post(h, headers=[*HEADERS.items(), (header, "extra")]).status_code == (
        401 if header == "Authorization" else 400
    )


@pytest.mark.parametrize("key", [None, "", "x" * 121, "with space", "../key"])
def test_required_valid_request_key(h, key):
    headers = {"Authorization": "Fixture teacher"}
    if key is not None:
        headers["Idempotency-Key"] = key
    assert post(h, headers=headers).status_code == 400


def test_create_no_if_match_existing_requires_strong_assignment_etag(h):
    assert post(h, headers=HEADERS | {"If-Match": '"1"'}).status_code == 400
    row = post(h)
    identity = row.json()["data"]["assignment_id"]
    cmd = {"action": "skip", "assignment_id": identity, "reason": "Teacher choice"}
    assert post(h, cmd, HEADERS | {"Idempotency-Key": "next"}).status_code == 428
    for etag in ("1", 'W/"1"', '"0"', "*", '"01"'):
        assert post(h, cmd, HEADERS | {"If-Match": etag}).status_code == 400
    assert post(h, cmd, HEADERS | {"If-Match": '"9"', "Idempotency-Key": "next"}).status_code == 409


@pytest.mark.parametrize("principal", ["child", "admin", "device"])
def test_action_specific_teacher_not_role_bypass(h, principal):
    h.identities[0] = VideoIdentity(principal, "school", "session")
    assert post(h).status_code == 403
    assert not h.runtime.store.rows


def test_identity_before_body_and_server_scope_not_spoofed_headers(h):
    unauth = h.client.post(URL, content="synthetic_sensitive")
    assert unauth.status_code == 401 and "synthetic_sensitive" not in unauth.text
    result = post(h, headers=HEADERS | {"X-Organization-Id": "foreign", "X-Session-Id": "foreign"})
    assert result.status_code == 200 and result.json()["data"]["organization_id"] == "school"
    foreign = body(audience_scope={"session_id": "foreign", "group_ids": ["group"]})
    assert post(h, foreign, HEADERS | {"Idempotency-Key": "foreign"}).status_code == 403


@pytest.mark.parametrize(
    "raw",
    [b"{", b"[]", b"null", b"\xff", b'{"x":NaN}', b'{"a":1,"a":2}', b'{"nested":{"a":1,"a":2}}'],
)
def test_strict_json_admission_no_effect(h, raw):
    assert (
        h.client.post(
            URL, content=raw, headers=HEADERS | {"Content-Type": "application/json"}
        ).status_code
        == 422
    )
    assert not h.runtime.store.rows


def test_stream_size_type_encoding_and_false_content_length(h):
    headers = HEADERS | {"Content-Type": "application/json"}
    assert (
        h.client.post(
            URL, content=(b" " * 2048 for _ in range(3)), headers=headers | {"Content-Length": "1"}
        ).status_code
        == 413
    )
    assert h.client.post(URL, content="{}", headers=HEADERS).status_code == 415
    assert post(h, headers=headers | {"Content-Encoding": "gzip"}).status_code == 415


def test_not_ready_hazard_edit_and_start_rechecks(h):
    row = post(h, body(teacher_adaptations={"materials": ["hazard"]}))
    assert advance(h, row, "confirm_ready").status_code == 409
    assert advance(h, row, "start").status_code == 409


def test_replay_current_projection_no_implicit_new_assignment_and_changed_body_conflict(h):
    row = post(h)
    advance(h, row, "confirm_ready")
    replay = post(h)
    assert replay.status_code == 200 and replay.json()["data"]["state"] == "ready"
    assert replay.json()["data"]["applied_revision"] == 1 and replay.json()["data"]["replayed"]
    assert len(h.runtime.store.rows) == 1
    assert post(h, body(teacher_adaptations={"instructions": "changed"})).status_code == 409


@pytest.mark.parametrize(
    "error", [RuntimeError("synthetic_sensitive"), VideoError("internal.synthetic_sensitive")]
)
def test_error_allowlist_no_raw_diagnostic(h, monkeypatch, error):
    monkeypatch.setattr(h.runtime.service, "execute", Mock(side_effect=error))
    result = post(h)
    assert result.status_code == 503 and "synthetic_sensitive" not in result.text


@pytest.mark.parametrize(
    "field,value",
    [
        ("applied_revision", True),
        ("applied_revision", 99),
        ("replayed", "true"),
        ("outcome_delivery", "portfolio_saved"),
    ],
)
def test_malformed_native_result_not_exposed(h, monkeypatch, field, value):
    original = h.runtime.service.execute
    monkeypatch.setattr(
        h.runtime.service, "execute", lambda *args: replace(original(*args), **{field: value})
    )
    assert post(h).status_code == 503


def test_missing_service_and_no_default_mount_or_competing_be1_route(h):
    app = FastAPI()
    router = build_activity_execution_router(None, h.resolve, max_body_bytes=4096)
    assert [route.path for route in router.routes] == [URL]
    app.include_router(router)
    with TestClient(app) as client:
        assert client.post(URL, json=body(), headers=HEADERS).status_code == 503
    path = Path(__file__).resolve().parents[2] / "src/sketch2life/interfaces/http/app.py"
    assert "build_activity_execution_router" not in path.read_text(encoding="utf-8")


@pytest.mark.parametrize("limit", [True, 0, -1, "4096"])
def test_body_limit_is_explicit_candidate_deployment_choice(h, limit):
    with pytest.raises(ValueError):
        build_activity_execution_router(h.runtime.service, h.resolve, max_body_bytes=limit)
