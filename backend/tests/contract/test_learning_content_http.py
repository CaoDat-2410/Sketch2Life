"""ASGI content seam tests, injected synthetic identity; not production adoption."""

from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from sketch2life.application.learning_content_commands import ContentCommands
from sketch2life.domain.learning_content.model import ContentError
from sketch2life.interfaces.http.routers.learning_content import (
    GovernanceIdentity,
    build_content_commands_router,
)
from tests.learning_content_fixtures import (
    BODY,
    NOW,
    AssumedBoundary,
    ComponentStore,
    approved,
    command,
    review_command,
    submitted,
)


@pytest.fixture
def harness():
    boundary = AssumedBoundary()
    store = ComponentStore(boundary)
    service = ContentCommands(store, boundary, clock=lambda: NOW)
    current = [GovernanceIdentity("author", "school")]
    app = FastAPI()
    app.include_router(build_content_commands_router(
        service, lambda request: current[0], max_body_bytes=8192))
    return TestClient(app), store, current, service


URL = "/api/collaboration/v1/governance/records"


def create_payload():
    return json.loads(command("create", "create", content=BODY).model_dump_json())


def test_create_duplicate_and_submit_http_roundtrip(harness):
    client, store, _, _ = harness
    first = client.post(URL, json=create_payload(), headers={"x-correlation-id": "corr-known"})
    assert first.status_code == 200
    assert first.json()["correlation_id"] == "corr-known"
    assert first.headers["etag"] == '"1"' and first.headers["cache-control"] == "no-store"
    assert client.post(URL, json=create_payload()).json()["data"]["replayed"]
    data = first.json()["data"]["record"]
    payload = {"record_kind": "learning_content", "action": "submit_review",
               "client_request_id": "submit", "record_id": data["record_id"],
               "target_version": 1, "target_hash": data["hash"]}
    missing = client.post(URL, json=payload)
    assert missing.status_code == 428
    response = client.post(URL, json=payload, headers={"if-match": '"1"'})
    assert response.status_code == 200 and response.headers["etag"] == '"2"'
    assert len(store.events) == 2


def test_no_client_identity_header_or_body_can_grant_access(harness):
    client, store, current, _ = harness
    current[0] = None
    response = client.post(URL, json=create_payload(), headers={
        "x-principal-id": "author", "x-role": "admin", "x-organization-id": "school"})
    assert response.status_code == 401 and not store.events
    current[0] = GovernanceIdentity("consumer", "school")
    assert client.post(URL, json=create_payload()).status_code == 403
    current[0] = GovernanceIdentity("author", "school")
    payload = {**create_payload(), "organization_id": "other", "role": "admin"}
    assert client.post(URL, json=payload).status_code == 422


@pytest.mark.parametrize("value", ['*', 'W/"1"', '1', '"0"', '"-1"', '"01"',
                                  '"9223372036854775808"', '"1", "2"'])
def test_if_match_is_one_strong_positive_revision(harness, value):
    client, store, _, _ = harness
    response = client.post(URL, json=create_payload(), headers={"if-match": value})
    assert response.status_code == 400 and not store.events


@pytest.mark.parametrize("raw", [b'{"private":"never-echo-this"}', b'{', b'[]', b'null',
                                 b'{"action":"create","action":"edit"}', b'{"x":NaN}',
                                 b'\xff'])
def test_invalid_json_has_safe_envelope_without_input(harness, raw):
    client, _, _, _ = harness
    response = client.post(URL, content=raw, headers={"content-type": "application/json"})
    assert response.status_code == 422
    assert "never-echo-this" not in response.text and '"input"' not in response.text
    assert set(response.json()) == {"contract_name", "contract_version", "correlation_id", "error"}


def test_body_admission_is_bounded_and_media_type_is_checked(harness):
    client, store, _, _ = harness
    assert client.post(URL, content="x" * 8193, headers={
        "content-type": "application/json"}).status_code == 413
    assert client.post(URL, content="private").status_code == 415
    assert not store.events


@pytest.mark.parametrize("error,status,code", [
    (ContentError("CONTENT_STALE_REVISION"), 409, "CONTENT_STALE_REVISION"),
    (ContentError("unsafe-private-adapter-detail"), 503, "CONTENT_DEPENDENCY_UNAVAILABLE"),
    (RuntimeError("unsafe-private-adapter-detail"), 500, "INTERNAL_ERROR"),
])
def test_adapter_failures_never_echo_exception_text(harness, monkeypatch, error, status, code):
    client, _, _, service = harness

    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(service, "execute", fail)
    response = client.post(URL, json=create_payload())
    assert response.status_code == status and response.json()["error"]["code"] == code
    assert "unsafe-private" not in response.text


def test_exactly_one_command_path_and_no_new_delivery_gateway(harness):
    client, _, _, _ = harness
    paths = client.get("/openapi.json").json()["paths"]
    assert list(paths) == [URL] and set(paths[URL]) == {"post"}
    schema = paths[URL]["post"]["requestBody"]["content"]["application/json"]["schema"]
    assert len(schema["oneOf"]) == 7  # RetireContent has both recall and archive.
    assert '"$ref"' not in json.dumps(schema)
    assert "#/$defs/" not in json.dumps(schema)


@pytest.mark.parametrize("kind", ["preset", "policy", "unknown"])
def test_missing_owner_contracts_are_not_treated_as_content(harness, kind):
    client, store, _, _ = harness
    response = client.post(URL, json={**create_payload(), "record_kind": kind})
    assert response.status_code == 422 and not store.events


@pytest.mark.parametrize("action", ["create", "edit", "submit_review", "record_review",
                                    "request_changes", "publish", "recall", "archive"])
def test_all_content_actions_use_the_same_http_route(harness, action):
    client, _, current, service = harness
    revision = None
    if action == "create":
        payload = command("create", "http-create", content=BODY)
        actor = "author"
    elif action == "submit_review":
        record = service.execute(
            "author", "school", command("create", "create", content=BODY)).record
        payload, actor, revision = command(action, "http-submit", record), "author", record.revision
    elif action in {"record_review", "request_changes"}:
        record = submitted(service)
        decision = "approve" if action == "record_review" else "request_changes"
        payload = review_command(record, "safety", "http-review", decision=decision, action=action)
        actor, revision = "reviewer", record.revision
    elif action in {"publish", "recall"}:
        record, refs = approved(service)
        payload = command("publish", "http-publish", record, review_ref=refs)
        actor, revision = "publisher", record.revision
        if action == "recall":
            record = service.execute(actor, "school", payload, expected_revision=revision).record
            payload = command("recall", "http-recall", record, reason="withdrawn")
            actor, revision = "recaller", record.revision
    else:
        record = submitted(service)
        if action == "edit":
            payload, actor = command(action, "http-edit", record, content=BODY), "author"
        else:
            payload, actor = command(action, "http-archive", record, reason="withdrawn"), "recaller"
        revision = record.revision
    current[0] = GovernanceIdentity(actor, "school")
    headers = {} if revision is None else {"if-match": f'"{revision}"'}
    response = client.post(URL, json=json.loads(payload.model_dump_json()), headers=headers)
    assert response.status_code == 200, response.text
    expected = {"create": "draft", "edit": "draft", "submit_review": "submitted",
                "record_review": "submitted", "request_changes": "changes_requested",
                "publish": "published", "recall": "recalled", "archive": "archived"}
    assert response.json()["data"]["record"]["state"] == expected[action]
