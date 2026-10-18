"""ASSUMED authority/bridge +MEMORY UoW through real HTTP, not BE1/provider proof."""

from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from sketch2life.domain.knowledge_video.model import ExactRef, Strategy, VideoError
from sketch2life.domain.video_review.model import Invalidation, ReviewHead, ReviewSubject
from sketch2life.interfaces.http.routers.knowledge_video import VideoIdentity
from sketch2life.interfaces.http.routers.video_review import build_video_review_router
from tests.contract.test_video_review_contract import command
from tests.unit.test_knowledge_video_worker import harness as render_fixture
from tests.unit.test_video_playback import receipt
from tests.unit.test_video_playback import setup as play_setup
from tests.unit.test_video_review_domain import subject
from tests.unit.test_video_review_write import setup as review_setup

BASE = "/api/collaboration/v1/knowledge-videos/video"


def review_body(**changes):
    return command().model_dump(mode="json") | changes


def play_body(h, **changes):
    head = h.r.store.heads.get(("school", "session", "video"), h.r.boundary.initial)
    return (
        dict(
            target_version=h.target[0].video_version,
            target_hash=h.target[0].artifact.hash,
            subject_digest=h.target[0].digest(),
            review_id=head.entry.review_id if head.entry else "review",
            review_revision=head.revision,
            expected_session_revision=4,
        )
        | changes
    )


@pytest.fixture
def h():
    r, p = review_setup(), play_setup()
    identity = [VideoIdentity("teacher", "school", "session")]
    target = [subject()]

    def resolve(request):
        return identity[0] if request.headers.get("authorization") == "Fixture teacher" else None

    original_guard, original_check = p.boundary.guard, p.boundary.check

    @contextmanager
    def guarded(principal, org, session):
        if (principal, org, session) != ("teacher", "school", "session"):
            raise VideoError("VIDEO_PLAYBACK_FORBIDDEN")
        with original_guard(principal, org, session) as access:
            yield access

    def check(intent, phase):
        original_check(intent, phase)
        if phase == "dispatch" and intent.request.expected_session_revision != 4:
            raise VideoError("VIDEO_PLAYBACK_STALE_SESSION")

    p.boundary.guard, p.boundary.check = guarded, check
    p.boundary.review_head = lambda request: r.store.heads.get(
        ("school", "session", "video"), r.boundary.initial
    )
    target_resolver = Mock(side_effect=lambda actor, video, cmd: target[0])
    app = FastAPI()
    app.include_router(
        build_video_review_router(
            r.service, p.service, resolve, target_resolver, max_body_bytes=4096
        )
    )
    with TestClient(app) as client:
        yield SimpleNamespace(
            r=r,
            p=p,
            client=client,
            identity=identity,
            target=target,
            resolver=target_resolver,
            resolve=resolve,
        )


def post(h, kind="reviews", body=None, headers=None, **kwargs):
    defaults = {
        "Authorization": "Fixture teacher",
        "Idempotency-Key": "review.key" if kind == "reviews" else "play.key",
    }
    if kind == "reviews":
        defaults["If-Match"] = '"1"'
    return h.client.post(
        BASE + "/" + kind,
        json=body if body is not None else (review_body() if kind == "reviews" else play_body(h)),
        headers=defaults if headers is None else headers,
        **kwargs,
    )


def approve(h):
    result = post(h)
    assert result.status_code == 200, result.text
    return result.json()["data"]


def test_ready_never_autoplays_approve_then_explicit_start_and_replay(h):
    assert post(h, "playback").status_code == 409
    h.p.bridge.start.assert_not_called()
    reviewed = approve(h)
    assert reviewed["record"]["review_revision"] == reviewed["current_review_revision"] == 2
    assert reviewed["record"]["state"] == "effective"
    h.p.bridge.start.assert_not_called()
    first = post(h, "playback")
    assert first.status_code == 200 and first.json()["data"]["status"] == "confirmed"
    assert post(h, "playback").json()["data"] == first.json()["data"]
    assert len(h.r.store.history) == len(h.p.store.rows) == h.p.bridge.start.call_count == 1
    for result in (post(h), first):
        assert result.headers["cache-control"] == "no-store"
        assert result.headers["vary"] == "Authorization"
        assert not any(
            value in result.text
            for value in (
                "playback_url",
                "access_ref",
                "capability",
                "child",
                "group",
                "script",
                "playing",
            )
        )
    assert post(h).json()["data"]["replayed"] is True


@pytest.mark.parametrize("kind", ["reviews", "playback"])
def test_unauthenticated_before_body_no_echo(h, kind):
    response = h.client.post(BASE + "/" + kind, content="private invalid body")
    assert response.status_code == 401 and "private" not in response.text
    assert not h.r.store.heads and not h.p.store.rows


@pytest.mark.parametrize("kind", ["reviews", "playback"])
@pytest.mark.parametrize(
    "field",
    [
        "organization_id",
        "session_id",
        "principal_id",
        "approved",
        "url",
        "script",
        "endpoint",
        "api_key",
    ],
)
def test_spoof_authority_and_diagnostics_rejected_before_effect(h, kind, field):
    body = review_body() if kind == "reviews" else play_body(h)
    result = post(h, kind, body | {field: "synthetic_sensitive"})
    assert result.status_code == 422 and "synthetic_sensitive" not in result.text
    h.resolver.assert_not_called()
    h.p.bridge.start.assert_not_called()
    assert not h.r.store.heads


@pytest.mark.parametrize("kind", ["reviews", "playback"])
@pytest.mark.parametrize("key", [None, "", "x" * 121, "with space", "../key"])
def test_missing_invalid_key(h, kind, key):
    headers = {"Authorization": "Fixture teacher", "If-Match": '"1"'}
    if kind == "playback":
        headers.pop("If-Match")
    if key is not None:
        headers["Idempotency-Key"] = key
    assert post(h, kind, headers=headers).status_code == 400
    assert not h.r.store.heads and not h.p.store.rows


@pytest.mark.parametrize(
    "etag",
    [None, "1", 'W/"1"', '"0"', '"01"', "*", '"1", "2"', '"9223372036854775808"', '"-1"', '"true"'],
)
def test_review_etag_is_strong_single_review_revision(h, etag):
    headers = {"Authorization": "Fixture teacher", "Idempotency-Key": "key"}
    if etag is not None:
        headers["If-Match"] = etag
    assert post(h, headers=headers).status_code == (428 if etag is None else 400)
    assert not h.r.store.heads


@pytest.mark.parametrize(
    "kind,header",
    [
        ("reviews", "if-match"),
        ("reviews", "idempotency-key"),
        ("playback", "idempotency-key"),
        ("reviews", "authorization"),
        ("playback", "authorization"),
    ],
)
def test_duplicate_preconditions_and_identity_headers_rejected(h, kind, header):
    headers = [("Authorization", "Fixture teacher"), ("Idempotency-Key", "key")]
    if kind == "reviews":
        headers.append(("If-Match", '"1"'))
    headers.append((header, '"1"' if header == "if-match" else "extra"))
    assert post(h, kind, headers=headers).status_code == (401 if header == "authorization" else 400)


@pytest.mark.parametrize("kind", ["reviews", "playback"])
@pytest.mark.parametrize(
    "raw",
    [
        b"{",
        b"[]",
        b"null",
        b'"text"',
        b"\xff",
        b'{"key":1,"key":2}',
        b'{"a":{"key":1,"key":2}}',
        b'{"a":NaN}',
        b'{"a":Infinity}',
    ],
)
def test_malformed_strict_json(h, kind, raw):
    headers = {
        "Authorization": "Fixture teacher",
        "Idempotency-Key": "key",
        "Content-Type": "application/json",
    }
    if kind == "reviews":
        headers["If-Match"] = '"1"'
    response = h.client.post(BASE + "/" + kind, content=raw, headers=headers)
    assert response.status_code == 422
    assert not h.r.store.heads and not h.p.store.rows


@pytest.mark.parametrize("kind", ["reviews", "playback"])
def test_stream_limit_not_content_length_and_encoding_policy(h, kind):
    headers = {
        "Authorization": "Fixture teacher",
        "Idempotency-Key": "key",
        "Content-Type": "application/json",
    }
    if kind == "reviews":
        headers["If-Match"] = '"1"'
    url = BASE + "/" + kind
    result = h.client.post(
        url, content=(b" " * 2048 for _ in range(3)), headers=headers | {"Content-Length": "1"}
    )
    assert result.status_code == 413
    assert (
        h.client.post(url, content="{}", headers=headers | {"Content-Encoding": "gzip"}).status_code
        == 415
    )
    headers["Content-Type"] = "text/plain"
    assert h.client.post(url, content="{}", headers=headers).status_code == 415
    assert not h.r.store.heads and not h.p.store.rows


@pytest.mark.parametrize(
    "field,value",
    [
        ("target_version", True),
        ("review_revision", True),
        ("expected_session_revision", True),
        ("expected_session_revision", -1),
        ("review_revision", 2**63),
        ("target_hash", "private/url"),
        ("subject_digest", "bad"),
    ],
)
def test_playback_strict_scalar_bounds(h, field, value):
    assert post(h, "playback", play_body(h, **{field: value})).status_code == 422
    h.resolver.assert_not_called()


@pytest.mark.parametrize(
    "field,value",
    [
        ("target_version", 2),
        ("target_hash", "f" * 64),
        ("subject_digest", "f" * 64),
        ("review_revision", 9),
        ("review_id", "foreign"),
        ("expected_session_revision", 9),
    ],
)
def test_wrong_exact_target_review_or_session_cas_never_dispatches(h, field, value):
    approve(h)
    assert post(h, "playback", play_body(h, **{field: value})).status_code == 409
    h.p.bridge.start.assert_not_called()


@pytest.mark.parametrize("kind", ["reviews", "playback"])
def test_child_identity_cannot_perform_teacher_action(h, kind):
    h.identity[0] = VideoIdentity("child", "school", "session")
    assert post(h, kind).status_code == 403
    assert not h.r.store.heads and not h.p.store.rows


def test_scope_not_taken_from_untrusted_headers(h):
    headers = {
        "Authorization": "Fixture teacher",
        "Idempotency-Key": "review.key",
        "If-Match": '"1"',
        "X-Session-Id": "foreign",
        "X-Organization-Id": "foreign",
    }
    assert post(h, headers=headers).status_code == 200
    assert set(h.r.store.heads) == {("school", "session", "video")}


def test_review_path_body_target_and_job_run_revision_not_accepted(h):
    assert post(h, body=review_body(target_id="foreign")).status_code == 409
    assert (
        post(
            h,
            headers={
                "Authorization": "Fixture teacher",
                "Idempotency-Key": "key",
                "If-Match": '"8"',
            },
        ).status_code
        == 409
    )
    assert not h.r.store.heads


def test_playback_does_not_silently_accept_review_if_match(h):
    assert (
        post(
            h,
            "playback",
            headers={
                "Authorization": "Fixture teacher",
                "Idempotency-Key": "key",
                "If-Match": '"2"',
            },
        ).status_code
        == 400
    )
    h.resolver.assert_not_called()


@pytest.mark.parametrize("decision", ["reject", "request_changes"])
def test_review_decisions_and_stale_approval_projection(h, decision):
    approve(h)
    headers = {"Authorization": "Fixture teacher", "Idempotency-Key": "second", "If-Match": '"2"'}
    assert (
        post(
            h, body=review_body(decision=decision, reason="fixture changes"), headers=headers
        ).status_code
        == 200
    )
    assert post(h).json()["data"]["record"]["state"] == "stale"
    assert post(h, "playback").status_code == 409


def test_changed_body_key_conflicts_and_replay_denial(h):
    approve(h)
    assert post(h, body=review_body(reason="changed")).status_code == 409
    h.r.boundary.denied = "replay"
    assert post(h).status_code == 403 and len(h.r.store.history) == 1


@pytest.mark.parametrize("phase", ["prepare", "commit_intent", "dispatch"])
def test_current_gate_denial_never_calls_bridge(h, phase):
    approve(h)
    h.p.boundary.denied = phase
    assert post(h, "playback").status_code == 403
    h.p.bridge.start.assert_not_called()


def test_lost_ack_pending_then_original_receipt_lookup_no_repeat_start(h):
    approve(h)
    h.p.bridge.start.side_effect = TimeoutError("synthetic_sensitive")
    original_body = play_body(h)
    result = post(h, "playback", original_body)
    assert result.status_code == 202 and result.json()["data"]["status"] == "pending"
    intent = next(iter(h.p.store.rows.values()))
    h.p.bridge.lookup.return_value = receipt(intent)
    result = post(h, "playback", original_body)
    assert result.status_code == 200 and result.json()["data"]["status"] == "confirmed"
    assert h.p.bridge.start.call_count == h.p.bridge.lookup.call_count == 1
    assert "synthetic_sensitive" not in result.text


def test_malformed_foreign_receipt_stays_pending_not_false_confirmation(h):
    approve(h)
    h.p.bridge.start.side_effect = lambda intent: receipt(intent, request_digest="f" * 64)
    result = post(h, "playback")
    assert result.status_code == 202 and result.json()["data"]["receipt_id"] is None
    assert next(iter(h.p.store.rows.values())).receipt is None


def test_historical_confirmation_after_invalidation_not_new_play_or_access(h):
    approve(h)
    body = play_body(h)
    assert post(h, "playback", body).status_code == 200
    key = ("school", "session", "video")
    before = h.r.store.heads[key]
    h.r.store.heads[key] = before.invalidate(before.revision, Invalidation.USAGE_REVOKED)
    replay = post(h, "playback", body)
    assert replay.status_code == 200 and replay.json()["data"]["status"] == "confirmed"
    new = post(
        h,
        "playback",
        body,
        headers={"Authorization": "Fixture teacher", "Idempotency-Key": "different"},
    )
    assert new.status_code == 409 and h.p.bridge.start.call_count == 1
    assert set(replay.json()["data"]) == {
        "contract_version",
        "status",
        "operation_key",
        "reason_code",
        "receipt_id",
    }


@pytest.mark.parametrize(
    "failure", [RuntimeError("synthetic_sensitive"), VideoError("internal.synthetic_sensitive")]
)
@pytest.mark.parametrize("kind", ["reviews", "playback"])
def test_dependency_errors_not_echoed(h, monkeypatch, kind, failure):
    if kind == "reviews":
        monkeypatch.setattr(h.r.service, "record", Mock(side_effect=failure))
    else:
        h.resolver.side_effect = failure
    result = post(h, kind)
    assert result.status_code == 503 and "synthetic_sensitive" not in result.text
    assert result.json()["error"]["retryable"] is True


@pytest.mark.parametrize(
    "field,value",
    [
        ("current_review_revision", True),
        ("current_review_revision", 1),
        ("replayed", "true"),
        ("record", command()),
        ("current_review_revision", 99),
    ],
)
def test_malformed_review_result_fails_closed(h, monkeypatch, field, value):
    original = h.r.service.record
    monkeypatch.setattr(h.r.service, "record", lambda *a: replace(original(*a), **{field: value}))
    result = post(h)
    assert result.status_code == 503


@pytest.mark.parametrize(
    "changes",
    [
        {"status": "playing"},
        {"status": "confirmed", "receipt_id": None},
        {"operation_key": "f" * 64},
        {"receipt_id": "private/url"},
        {"reason_code": "internal.synthetic_sensitive"},
    ],
)
def test_malformed_playback_projection_never_grants_access(h, monkeypatch, changes):
    approve(h)
    original = h.p.service.start
    monkeypatch.setattr(h.p.service, "start", lambda *a: replace(original(*a), **changes))
    result = post(h, "playback")
    assert result.status_code == 503 and "synthetic_sensitive" not in result.text


@pytest.mark.parametrize("kind", ["reviews", "playback"])
def test_unconfigured_services_fail_closed_no_default_authority(h, kind):
    app = FastAPI()
    app.include_router(build_video_review_router(None, None, h.resolve, None, max_body_bytes=4096))
    with TestClient(app) as client:
        h.client = client
        assert post(h, kind).status_code == 503
    assert not h.r.store.heads and not h.p.store.rows


@pytest.mark.parametrize("limit", [True, 0, -1, "4096"])
def test_body_limit_has_no_hidden_policy_default(h, limit):
    with pytest.raises(ValueError):
        build_video_review_router(
            h.r.service, h.p.service, h.resolve, h.resolver, max_body_bytes=limit
        )


def test_no_production_default_route_registration():
    path = Path(__file__).resolve().parents[2] / "src/sketch2life/interfaces/http/app.py"
    assert "build_video_review_router" not in path.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "changes",
    [
        {"organization_id": "foreign"},
        {"video_id": "foreign"},
        {"audience": replace(subject().audience, session_id="foreign")},
    ],
)
def test_foreign_resolved_subject_never_reaches_bridge(h, changes):
    h.target[0] = replace(subject(), **changes)
    result = post(h, "playback")
    assert result.status_code == 403
    h.p.bridge.start.assert_not_called()


def test_owner_resolver_changed_media_cannot_substitute_target(h):
    body = play_body(h)
    h.target[0] = replace(subject(), artifact=ExactRef("other", 1, "f" * 64))
    assert post(h, "playback", body).status_code == 409
    h.p.bridge.start.assert_not_called()


def test_reviewed_library_path_needs_session_review_not_sketch_or_generation(h):
    # Synthetic final artifact, NOT actual decoder/provider/publication authority.
    run = render_fixture().finalized.video_run
    pin = replace(
        run.pin,
        strategy=Strategy.REVIEWED_LIBRARY,
        model_profile=None,
        library_asset=ExactRef("reviewed.library", 1, run.artifact.artifact.hash),
    )
    ready = replace(run, pin=pin, artifact=replace(run.artifact, pin_digest=pin.digest()))
    target = ReviewSubject.from_ready(ready, subject().audience)
    h.target[0] = target
    h.r.boundary.initial = ReviewHead(target, 1)
    assert post(h, "playback").status_code == 409  # Publication !=session approval.
    approve(h)
    result = post(h, "playback")
    assert result.status_code == 200 and result.json()["data"]["status"] == "confirmed"
    assert h.p.bridge.start.call_count == 1
