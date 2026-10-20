"""Actual policy service/sole CMD-48 composition, MEMORY and ASSUMED authority only."""

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from sketch2life.application.ai_policy_governance import bind_ai_policy
from sketch2life.application.governance_dispatcher import GovernanceDispatcher
from sketch2life.application.learning_content_commands import ContentCommands
from sketch2life.domain.ai_policy.model import PolicyError
from sketch2life.interfaces.http.routers.learning_content import (
    GovernanceIdentity,
    build_governance_commands_router,
)
from tests.ai_policy_fixtures import BODY, command, harness, published, reviewed, submitted
from tests.learning_content_fixtures import NOW, AssumedBoundary, ComponentStore

URL = "/api/collaboration/v1/governance/records"


@pytest.fixture
def transport():
    service, boundary, store = harness()
    content_store = ComponentStore(AssumedBoundary())
    content = ContentCommands(content_store, content_store.boundary, clock=lambda: NOW)
    dispatcher = GovernanceDispatcher(content, ai_policy=bind_ai_policy(service))
    identity = [GovernanceIdentity("author", "school")]
    app = FastAPI()
    app.include_router(
        build_governance_commands_router(
            dispatcher, lambda request: identity[0], max_body_bytes=16384
        )
    )
    with TestClient(app) as client:
        yield client, service, boundary, store, identity, content_store, dispatcher


def post(client, cmd, revision=None):
    headers = {"content-type": "application/json", "x-correlation-id": "fixture-correlation"}
    if revision is not None:
        headers["if-match"] = f'"{revision}"'
    return client.post(URL, content=cmd.model_dump_json(), headers=headers)


@pytest.mark.parametrize(
    "action",
    [
        "create",
        "edit",
        "submit_review",
        "record_review",
        "request_changes",
        "publish",
        "recall",
        "archive",
    ],
)
def test_all_eight_policy_actions_use_existing_route_actual_service(transport, action):
    client, service, _, store, identity, content_store, _ = transport
    actor, fields, record = "author", {}, None
    if action == "create":
        fields = {"policy": BODY}
    elif action in {"edit", "submit_review", "archive"}:
        record = service.execute("author", "school", command("create", "seed", policy=BODY)).record
        if action == "edit":
            fields = {"policy": BODY | {"title": "Synthetic edit"}}
        elif action == "archive":
            actor, fields = "operator", {"reason": "synthetic"}
    elif action in {"record_review", "request_changes"}:
        record = submitted(service).record
        item = store.load("school", record.record_id)
        actor = "reviewer"
        fields = {
            "review": dict(
                target_kind="ai_policy",
                target_id=item.record_id,
                target_version=item.version,
                target_hash=item.hash,
                context_revision=item.context_revision,
                expected_review_revision=item.review_revision,
                dimension="safety",
                decision="approve" if action == "record_review" else "request_changes",
                review_policy_version="fixture.governance",
            )
        }
        if action == "request_changes":
            fields["reason"] = "synthetic changes"
            fields["review"]["reason"] = fields["reason"]
    elif action == "publish":
        record = reviewed(service, store).record
        item = store.load("school", record.record_id)
        actor, fields = (
            "publisher",
            {
                "review_ref": dict(
                    safety_review_id=item.reviews[0].review_id,
                    pedagogical_review_id=item.reviews[1].review_id,
                    review_policy_version="fixture.governance",
                )
            },
        )
    else:
        record = published(service, store).record
        actor, fields = "operator", {"reason": "synthetic recall"}
    identity[0] = GovernanceIdentity(actor, "school")
    cmd = command(action, "http-action", record, **fields)
    response = post(client, cmd, None if record is None else record.revision)
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["record"]["policy_kind"] == "ai"
    assert data["record"]["organization_id"] == "school"
    assert response.headers["etag"] == f'"{data["current_revision"]}"'
    counts = len(store.events), len(store.scope_events), len(store.receipts)
    replay = post(client, cmd, None if record is None else record.revision)
    assert replay.status_code == 200 and replay.json()["data"]["replayed"] is True
    assert counts == (len(store.events), len(store.scope_events), len(store.receipts))
    assert not content_store.events
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("actor,org", [("unknown", "school"), ("author", "other-school")])
def test_current_authority_denial_is_safe_403_without_effects(transport, actor, org):
    client, _, _, store, identity, _, _ = transport
    identity[0] = GovernanceIdentity(actor, org)
    response = post(client, command("create", "denied", policy=BODY))
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "AI_POLICY_FORBIDDEN"
    assert not store.events and not store.receipts


def test_http_replay_rechecks_revoked_rights(transport):
    client, _, boundary, store, _, _, _ = transport
    cmd = command("create", "retry", policy=BODY)
    assert post(client, cmd).status_code == 200
    boundary.rights["author"] = set()
    response = post(client, cmd)
    assert response.status_code == 403 and len(store.events) == 1


def test_http_stale_revision_conflict_has_no_partial_effect(transport):
    client, service, _, store, _, _, _ = transport
    record = submitted(service).record
    before = len(store.events)
    response = post(client, command("edit", "stale", record, policy=BODY), record.revision - 1)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "AI_POLICY_STALE_REVISION"
    assert len(store.events) == before


@pytest.mark.parametrize(
    "change",
    [
        {"secret": "synthetic-private"},
        {"policy_kind": "unknown"},
        {"policy": None},
        {"action": "emergency_stop"},
    ],
)
def test_invalid_policy_transport_payload_has_no_effects(transport, change):
    client, _, _, store, _, _, _ = transport
    payload = command("create", "invalid", policy=BODY).model_dump(mode="json") | change
    response = client.post(URL, json=payload)
    assert response.status_code == 422
    assert "synthetic-private" not in response.text
    assert not store.events and not store.receipts


@pytest.mark.parametrize(
    "code,status",
    [
        ("AI_POLICY_FORBIDDEN", 403),
        ("AI_POLICY_SEPARATION_REQUIRED", 403),
        ("AI_POLICY_NOT_FOUND", 404),
        ("AI_POLICY_PRECONDITION_REQUIRED", 428),
        ("AI_POLICY_UNEXPECTED_PRECONDITION", 400),
        ("AI_POLICY_INVALID_COMMAND", 422),
        ("AI_POLICY_INVALID_BODY", 422),
        ("AI_POLICY_INVALID_REVIEW", 422),
        ("AI_POLICY_REASON_REQUIRED", 422),
        ("AI_POLICY_STALE_REVISION", 409),
        ("AI_POLICY_STALE_REVIEW", 409),
        ("AI_POLICY_COMMAND_CONFLICT", 409),
        ("AI_POLICY_WRITE_CONFLICT", 409),
        ("AI_POLICY_SUPERSEDED_VERSION", 409),
        ("AI_POLICY_HASH_MISMATCH", 409),
        ("AI_POLICY_REVIEW_REQUIRED", 409),
        ("AI_POLICY_REVIEW_MISMATCH", 409),
        ("AI_POLICY_REVIEW_INEFFECTIVE", 409),
        ("AI_POLICY_RECEIPT_INEFFECTIVE", 409),
        ("AI_POLICY_TRANSITION_DENIED", 409),
        ("AI_POLICY_FEATURE_CHANGE_DENIED", 409),
        ("AI_POLICY_FEATURE_UNAVAILABLE", 409),
        ("AI_POLICY_DEFINITION_UNAVAILABLE", 409),
        ("AI_POLICY_REGISTRY_CHANGED", 409),
        ("AI_POLICY_REGISTRY_UNAVAILABLE", 503),
        ("AI_POLICY_DEPENDENCY_UNAVAILABLE", 503),
        ("AI_POLICY_SCOPE_MISMATCH", 503),
        ("AI_POLICY_DEFINITION_MISMATCH", 503),
        ("AI_POLICY_INVALID_TIME", 503),
        ("synthetic-private token=not-a-real-secret", 503),
    ],
)
def test_closed_error_mapping_through_existing_router(transport, monkeypatch, code, status):
    client, service, _, _, _, _, _ = transport

    def fail(*args, **kwargs):
        raise PolicyError(code)

    monkeypatch.setattr(service, "execute", fail)
    response = post(client, command("create", "error", policy=BODY))
    assert response.status_code == status
    safe = (
        code
        if code
        not in {
            "AI_POLICY_SCOPE_MISMATCH",
            "AI_POLICY_DEFINITION_MISMATCH",
            "AI_POLICY_INVALID_TIME",
            "synthetic-private token=not-a-real-secret",
        }
        else "AI_POLICY_DEPENDENCY_UNAVAILABLE"
    )
    assert response.json()["error"]["code"] == safe
    assert response.json()["error"]["retryable"] is (status == 503)
    assert response.json()["correlation_id"] == "fixture-correlation"
    assert "synthetic-private" not in response.text
    assert response.headers["cache-control"] == "no-store"


def test_bound_policy_schema_and_single_route_no_implicit_other_delegates(transport):
    client, _, _, _, _, _, dispatcher = transport
    schema = client.get("/openapi.json").json()
    assert list(schema["paths"]) == [URL]
    encoded = json.dumps(schema)
    assert '"$ref"' not in encoded  # Inline titles are valid; unresolved references are not.
    assert "model_profile_refs" in encoded and "required_gates" in encoded
    assert dispatcher.preset is None and dispatcher.core_policy is None
    dispatcher.ai_policy = None
    response = post(client, command("create", "unbound", policy=BODY))
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "GOVERNANCE_DELEGATE_UNAVAILABLE"


def test_unauthenticated_policy_request_never_reaches_service(transport):
    client, _, _, store, identity, _, _ = transport
    identity[0] = None
    response = post(client, command("create", "no-identity", policy=BODY))
    assert response.status_code == 401 and not store.events


def test_dependency_exception_never_exposes_private_details(transport, monkeypatch):
    client, service, _, _, _, _, _ = transport

    def fail(*args, **kwargs):
        raise RuntimeError("synthetic-private connection-string and child-body")

    monkeypatch.setattr(service, "execute", fail)
    response = post(client, command("create", "dependency", policy=BODY))
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "synthetic-private" not in response.text and "child-body" not in response.text


@pytest.mark.parametrize("create", [True, False])
def test_shared_preconditions_rejected_before_policy_effects(transport, create):
    client, service, _, store, _, _, _ = transport
    record = None if create else submitted(service).record
    before = len(store.events)
    cmd = (
        command("create", "precondition", policy=BODY)
        if create
        else command("edit", "precondition", record, policy=BODY)
    )
    response = post(client, cmd, 1 if create else None)
    assert response.status_code == (400 if create else 428)
    assert len(store.events) == before
