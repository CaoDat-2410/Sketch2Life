"""Explicit fixture HTTP composition, not production identity/worker/provider proof."""

import json
from dataclasses import replace
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from sketch2life.application.knowledge_video_create import VideoCreateService
from sketch2life.contracts.schemas.knowledge_video import KnowledgeVideoView
from sketch2life.domain.knowledge_video.model import ExactRef, Strategy, VideoError, VideoPin
from sketch2life.infrastructure.knowledge_video.fakes import (
    FixtureAtomicVideoSubmission,
    FixtureVideoOwner,
)
from sketch2life.interfaces.http.routers.knowledge_video import (
    VideoIdentity,
    build_knowledge_video_router,
)

URL = "/api/collaboration/v1/knowledge-videos"
NOW = datetime(2026, 10, 18, tzinfo=UTC)


def body(**changes):
    return {"bundle_id": "bundle", "bundle_version": 1, "bundle_hash": "a" * 64,
            "audience_context_revision": 0, "strategy": "generate", **changes}


@pytest.fixture
def harness():
    def ref(name):
        return ExactRef(name, 1, "a" * 64)

    pin = VideoPin("school", "session", ref("bundle"), 0, 0, 0, (ref("source"),),
                   Strategy.GENERATE, ref("profile"), ref("encoding"), ref("rights"),
                   ref("retry"), ref("policy"), 1, ref("model"))
    owner = FixtureVideoOwner(pin)
    store = FixtureAtomicVideoSubmission(NOW)
    service = VideoCreateService(owner, store)
    identity = [VideoIdentity("teacher", "school", "session")]

    def resolve(request):
        return identity[0] if request.headers.get("authorization") == "Fixture teacher" else None

    app = FastAPI()
    app.state.fixture_only = True
    app.include_router(build_knowledge_video_router(service, resolve, max_body_bytes=4096))
    headers = {"Authorization": "Fixture teacher", "Idempotency-Key": "request"}
    return TestClient(app), store, owner, identity, headers, service


def test_create_and_replay_have_full_safe_projection(harness):
    client, store, _, _, headers, _ = harness
    response = client.post(URL, json=body(), headers=headers)
    assert response.status_code == 202
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["vary"] == "Authorization"
    data = response.json()["data"]
    assert data["generation_state"] == "queued"
    assert data["review_state"] == "pending_media"
    assert data["playback_state"] == "not_started"
    assert data["artifact_ref"] is None
    assert data["attempt_history"][0]["attempt_number"] == 1
    assert "url" not in response.text and "model" not in data
    second = client.post(URL, json=body(), headers=headers)
    assert second.status_code == 202 and second.json()["meta"]["outcome"] == "replayed"
    assert len(store.dispatch_intents) == 1


def test_auth_checked_before_invalid_body(harness):
    client, store, *_ = harness
    response = client.post(URL, content="secret.invalid.json",
                           headers={"Content-Type": "text/plain"})
    assert response.status_code == 401
    assert "secret.invalid" not in response.text and not store.runs


@pytest.mark.parametrize("key", [None, "", "with space", "x" * 121, "../x"])
def test_idempotency_key_required_validated(harness, key):
    client, store, _, _, headers, _ = harness
    headers = {"Authorization": headers["Authorization"]}
    if key is not None:
        headers["Idempotency-Key"] = key
    assert client.post(URL, json=body(), headers=headers).status_code == 400
    assert not store.runs


@pytest.mark.parametrize("field", ["organization_id", "principal_id", "session_id", "endpoint",
                                  "api_key", "script", "approved", "playback_url"])
def test_reject_spoof_fields_without_echo(harness, field):
    client, store, _, _, headers, _ = harness
    response = client.post(URL, json=body(**{field: "synthetic-sensitive-value"}), headers=headers)
    assert response.status_code == 422
    assert "synthetic-sensitive-value" not in response.text and not store.runs


@pytest.mark.parametrize("payload", [
    b"{", b"[]", b"null", b'"text"', b"\xff",
    b'{"bundle_id":"a","bundle_id":"b"}',
    b'{"nested":{"same":1,"same":2}}', b'{"value":NaN}', b'{"value":Infinity}',
    json.dumps(body(bundle_version=True)).encode(),
])
def test_strict_json_rejection_no_effects(harness, payload):
    client, store, _, _, headers, _ = harness
    response = client.post(URL, content=payload,
                           headers={**headers, "Content-Type": "application/json"})
    assert response.status_code == 422 and not store.runs


def test_streamed_size_bound_and_content_type(harness):
    client, store, _, _, headers, _ = harness
    response = client.post(URL, content=b" " * 4097,
                           headers={**headers, "Content-Type": "application/json"})
    assert response.status_code == 413 and not store.runs
    assert client.post(URL, content="{}", headers=headers).status_code == 415


def test_duplicate_header_and_untrusted_content_length(harness):
    client, store, _, _, headers, _ = harness
    duplicated = [("Authorization", headers["Authorization"]),
                  ("Idempotency-Key", "first"), ("Idempotency-Key", "second")]
    assert client.post(URL, json=body(), headers=duplicated).status_code == 400
    response = client.post(URL, content=(b" " * 2048 for _ in range(3)),
                           headers={**headers, "Content-Type": "application/json",
                                    "Content-Length": "1"})
    assert response.status_code == 413 and not store.runs


def test_replay_after_revocation_denied(harness):
    client, store, owner, _, headers, _ = harness
    assert client.post(URL, json=body(), headers=headers).status_code == 202
    owner.allowed_principals.clear()
    response = client.post(URL, json=body(), headers=headers)
    assert response.status_code == 403 and len(store.runs) == 1


def test_request_scope_never_from_client_headers(harness):
    client, store, _, _, headers, _ = harness
    response = client.post(URL, json=body(), headers={**headers, "X-Organization-Id": "other",
                                                   "X-Session-Id": "other"})
    assert response.status_code == 202
    assert response.json()["data"]["organization_id"] == "school"
    assert next(iter(store.runs.values())).pin.session_id == "session"


def test_same_key_new_body_conflict(harness):
    client, _, _, _, headers, _ = harness
    assert client.post(URL, json=body(), headers=headers).status_code == 202
    profile = {"ref": "profile", "version": 1, "hash": "a" * 64}
    response = client.post(URL, json=body(requested_profile_ref=profile), headers=headers)
    assert response.status_code == 409


@pytest.mark.parametrize("exception", [RuntimeError("secret diagnostic"),
                                       VideoError("unknown.internal.secret")])
def test_dependency_errors_closed_redacted(harness, monkeypatch, exception):
    client, _, _, _, headers, service = harness

    def fail(*args):
        raise exception

    monkeypatch.setattr(service, "create", fail)
    response = client.post(URL, json=body(), headers=headers)
    assert response.status_code == 503
    assert "secret" not in response.text and response.json()["error"]["retryable"]


@pytest.mark.parametrize("field,value", [
    ("organization_id", "other"), ("session_id", "other"), ("job_id", "other"),
    ("video_id", "other"), ("video_run_revision", 9), ("generation_state", "running"),
    ("playback_state", "playing"), ("artifact_ref", {"ref": "secret", "version": 1,
                                                   "hash": "b" * 64}),
])
def test_bad_submission_projection_is_never_exposed(harness, monkeypatch, field, value):
    client, store, _, _, headers, _ = harness
    original = store.submit

    def bad(**kwargs):
        result = original(**kwargs)
        return replace(result, view=result.view.model_copy(update={field: value}))

    monkeypatch.setattr(store, "submit", bad)
    response = client.post(URL, json=body(), headers=headers)
    assert response.status_code == 503
    assert "other" not in response.text and "secret" not in response.text


def test_missing_projection_not_invented(harness, monkeypatch):
    client, store, _, _, headers, _ = harness
    original = store.submit

    def missing(**kwargs):
        return replace(original(**kwargs), view=None)

    monkeypatch.setattr(store, "submit", missing)
    assert client.post(URL, json=body(), headers=headers).status_code == 503


def test_projection_normalized_before_outer_adapter_serialization(harness, monkeypatch):
    client, store, _, _, headers, _ = harness
    original = store.submit

    class ExtendedView(KnowledgeVideoView):
        def model_dump(self, *args, **kwargs):
            return {**super().model_dump(*args, **kwargs), "diagnostic": "synthetic_sensitive"}

    def extended(**kwargs):
        result = original(**kwargs)
        view = ExtendedView.model_validate_json(result.view.model_dump_json())
        return replace(result, view=view)

    monkeypatch.setattr(store, "submit", extended)
    response = client.post(URL, json=body(), headers=headers)
    assert response.status_code == 202
    assert "synthetic_sensitive" not in response.text and "diagnostic" not in response.text


@pytest.mark.parametrize("limit", [True, 0, -1, "4096"])
def test_body_bound_is_explicit_configuration(harness, limit):
    *_, service = harness
    with pytest.raises(ValueError):
        build_knowledge_video_router(service, lambda request: None, max_body_bytes=limit)
