"""One candidate HTTP dispatcher; strict bound-owner spies, not real integration."""

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from sketch2life.application.governance_dispatcher import (
    GovernanceDispatcher,
    StrictDelegateBinding,
)
from sketch2life.application.learning_content_commands import ContentCommands
from sketch2life.interfaces.http.routers.learning_content import (
    GovernanceIdentity,
    build_governance_commands_router,
)
from tests.contract.test_governance_dispatcher import (
    FixtureAi,
    FixtureCore,
    FixturePreset,
    Spy,
    raw,
)
from tests.learning_content_fixtures import NOW, AssumedBoundary, ComponentStore

URL = "/api/collaboration/v1/governance/records"


@pytest.fixture
def harness():
    store = ComponentStore(AssumedBoundary())
    content = ContentCommands(store, store.boundary, clock=lambda: NOW)
    spies = [Spy(), Spy(), Spy()]
    dispatcher = GovernanceDispatcher(
        content, preset=StrictDelegateBinding(FixturePreset, spies[0]),
        ai_policy=StrictDelegateBinding(FixtureAi, spies[1]),
        core_policy=StrictDelegateBinding(FixtureCore, spies[2]))
    app = FastAPI()
    app.include_router(build_governance_commands_router(
        dispatcher, lambda request: GovernanceIdentity("verified", "school"), max_body_bytes=8192))
    return TestClient(app), spies, store, content


@pytest.mark.parametrize("kind,policy,index", [("preset", None, 0), ("policy", "ai", 1),
                                               ("policy", "core", 2)])
def test_bound_owner_calls_use_one_http_path(harness, kind, policy, index):
    client, spies, store, _ = harness
    response = client.post(
        URL, content=raw(kind, policy),
        headers={"content-type": "application/json", "x-correlation-id": "corr-1"})
    assert response.status_code == 200
    assert response.json()["correlation_id"] == "corr-1"
    assert response.json()["data"]["record"]["record_kind"] == kind
    assert len(spies[index].calls) == 1 and not store.events
    paths = client.get("/openapi.json").json()["paths"]
    assert list(paths) == [URL] and set(paths[URL]) == {"post"}
    body_schema = paths[URL]["post"]["requestBody"]["content"]["application/json"]["schema"]
    assert len(body_schema["anyOf"]) == 4
    assert "#/$defs/" not in json.dumps(body_schema)


@pytest.mark.parametrize("kind,policy", [("preset", None), ("policy", "ai"), ("policy", "core")])
def test_unbound_owner_is_typed_503_not_content_fallthrough(harness, kind, policy):
    _, spies, store, content = harness
    app = FastAPI()
    app.include_router(build_governance_commands_router(
        GovernanceDispatcher(content), lambda request: GovernanceIdentity("verified", "school"),
        max_body_bytes=8192))
    response = TestClient(app).post(URL, content=raw(kind, policy),
                                    headers={"content-type": "application/json"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "GOVERNANCE_DELEGATE_UNAVAILABLE"
    assert not store.events and not any(spy.calls for spy in spies)


def test_full_owner_schema_validation_errors_never_echo_input(harness):
    client, spies, _, _ = harness
    response = client.post(URL, content=raw(secret="private-owner-value"),
                           headers={"content-type": "application/json"})
    assert response.status_code == 422
    assert "private-owner-value" not in response.text and not spies[0].calls


def test_owner_target_and_http_if_match_checked_before_effect(harness):
    client, spies, _, _ = harness
    payload = raw(action="recall", target_hash="invalid")
    response = client.post(URL, content=payload, headers={"content-type": "application/json"})
    assert response.status_code == 428 and not spies[0].calls
    response = client.post(URL, content=payload,
                           headers={"content-type": "application/json", "if-match": '"1"'})
    assert response.status_code == 422 and not spies[0].calls


def test_invalid_delegate_response_is_safe_503(harness):
    client, spies, _, _ = harness
    spies[0].wrong_scope = True
    response = client.post(URL, content=raw(), headers={"content-type": "application/json"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "GOVERNANCE_DELEGATE_INVALID_RESPONSE"
    assert "wrong-school" not in response.text
