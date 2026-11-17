"""C4b fixed routing and strict binding fixtures, not preset/policy implementation."""

from __future__ import annotations

import json
from typing import Literal

import pytest
from pydantic import BaseModel, ConfigDict, Field

from sketch2life.application.governance_dispatcher import (
    GovernanceDispatcher,
    StrictDelegateBinding,
)
from sketch2life.application.learning_content_commands import ContentCommands
from sketch2life.contracts.schemas.governance import (
    DelegateRecord,
    DelegateResult,
    GovernanceSelection,
)
from sketch2life.contracts.schemas.learning_content import PublicationReviewSet
from sketch2life.domain.learning_content.model import ContentError
from tests.learning_content_fixtures import BODY, NOW, AssumedBoundary, ComponentStore, command


class FixtureFields(GovernanceSelection):
    """Minimal synthetic owner payload, NOT adopted BE2-13/14/core policy schema."""

    title: str = Field(min_length=1, max_length=200)
    record_id: str | None = None
    target_version: int | None = None
    target_hash: str | None = None
    reason: str | None = None
    review_ref: PublicationReviewSet | None = None


class FixturePreset(FixtureFields):
    record_kind: Literal["preset"] = "preset"
    policy_kind: None = None


class FixtureAi(FixtureFields):
    record_kind: Literal["policy"] = "policy"
    policy_kind: Literal["ai"] = "ai"


class FixtureCore(FixtureFields):
    record_kind: Literal["policy"] = "policy"
    policy_kind: Literal["core"] = "core"


class Spy:
    def __init__(self):
        self.calls = []
        self.wrong_scope = False

    def execute(self, principal_id, organization_id, command, *, expected_revision):
        assert isinstance(command, BaseModel) and not isinstance(command, dict)
        self.calls.append((principal_id, organization_id, command, expected_revision))
        version = (command.target_version or 1) + (command.action == "edit")
        return DelegateResult(record=DelegateRecord(
            record_kind=command.record_kind, policy_kind=command.policy_kind,
            record_id=command.record_id or "fixture-record",
            organization_id="wrong-school" if self.wrong_scope else organization_id,
            version=version, revision=2, hash=command.target_hash or "a" * 64,
            state="draft", authored_by=principal_id, created_at=NOW,
            publication_review_ref=None, recalled_at=None, recall_reason=None),
            current_revision=2, current_state="draft")


@pytest.fixture
def harness():
    boundary = AssumedBoundary()
    store = ComponentStore(boundary)
    content = ContentCommands(store, boundary, clock=lambda: NOW)
    spies = [Spy(), Spy(), Spy()]
    dispatcher = GovernanceDispatcher(
        content, preset=StrictDelegateBinding(FixturePreset, spies[0]),
        ai_policy=StrictDelegateBinding(FixtureAi, spies[1]),
        core_policy=StrictDelegateBinding(FixtureCore, spies[2]))
    return dispatcher, spies, store, content


def raw(kind="preset", policy_kind=None, action="create", **changes):
    value = {"record_kind": kind, "action": action, "client_request_id": "request",
             "title": "synthetic-owner-model"}
    if policy_kind is not None:
        value["policy_kind"] = policy_kind
    if action != "create":
        value.update(record_id="record", target_version=1, target_hash="a" * 64)
    if action in {"request_changes", "recall", "archive"}:
        value["reason"] = "fixture reason"
    if action == "publish":
        value["review_ref"] = {"safety_review_id": "safety", "pedagogical_review_id": "pedagogy",
                               "review_policy_version": "policy-v1"}
    value.update(changes)
    return json.dumps(value).encode()


@pytest.mark.parametrize("kind,policy,index,model", [
    ("preset", None, 0, FixturePreset), ("policy", "ai", 1, FixtureAi),
    ("policy", "core", 2, FixtureCore)])
@pytest.mark.parametrize("action", ["create", "edit", "submit_review", "record_review",
                                    "request_changes", "publish", "recall", "archive"])
def test_exactly_one_typed_delegate_receives_verified_scope_and_precondition(
    harness, kind, policy, index, model, action,
):
    dispatcher, spies, store, _ = harness
    expected = None if action == "create" else 1
    result = dispatcher.execute_json("verified", "school", raw(kind, policy, action),
                                     expected_revision=expected)
    assert result.record.record_kind == kind
    assert [len(spy.calls) for spy in spies] == [int(i == index) for i in range(3)]
    actor, org, payload, revision = spies[index].calls[0]
    assert (actor, org, revision) == ("verified", "school", expected)
    assert type(payload) is model and not store.events


def test_content_branch_uses_its_existing_strict_service(harness):
    dispatcher, spies, store, _ = harness
    result = dispatcher.execute_json("author", "school", command(
        "create", "create", content=BODY).model_dump_json().encode())
    assert result.record.record_kind == "learning_content"
    assert len(store.events) == 1 and not any(spy.calls for spy in spies)


@pytest.mark.parametrize("kind,policy", [("preset", None), ("policy", "ai"), ("policy", "core")])
def test_missing_binding_is_explicit_unavailable_and_never_content(harness, kind, policy):
    _, spies, store, content = harness
    dispatcher = GovernanceDispatcher(content)
    with pytest.raises(ContentError, match="GOVERNANCE_DELEGATE_UNAVAILABLE"):
        dispatcher.execute_json("verified", "school", raw(kind, policy))
    assert not store.events and not any(spy.calls for spy in spies)


@pytest.mark.parametrize("payload", [
    raw("unknown"), raw("policy"), raw("policy", "unknown"), raw("preset", "ai"),
    raw(action="unknown"), b'{}', b'[]', b'{', b'{"action":"create","action":"edit"}',
    raw(client_request_id=" "), raw(contract_version="999"), raw(title=""),
    raw(secret="never-forward"), raw(organization_id="injected-school"),
])
def test_invalid_branch_action_or_full_bound_payload_never_calls_owner(harness, payload):
    dispatcher, spies, store, _ = harness
    with pytest.raises(ContentError, match="INVALID_GOVERNANCE_COMMAND"):
        dispatcher.execute_json("verified", "school", payload)
    assert not any(spy.calls for spy in spies) and not store.events


@pytest.mark.parametrize("changes", [dict(record_id=None), dict(target_version=True),
                                    dict(target_version=0), dict(target_hash="invalid"),
                                    dict(reason=" ")])
def test_shared_target_validation_precedes_effectful_owner_call(harness, changes):
    dispatcher, spies, _, _ = harness
    with pytest.raises(ContentError, match="INVALID_GOVERNANCE_COMMAND"):
        dispatcher.execute_json("verified", "school", raw(action="recall", **changes),
                                expected_revision=1)
    assert not any(spy.calls for spy in spies)


def test_response_scope_is_not_trusted(harness):
    dispatcher, spies, _, _ = harness
    spies[0].wrong_scope = True
    with pytest.raises(ContentError, match="GOVERNANCE_DELEGATE_INVALID_RESPONSE"):
        dispatcher.execute_json("verified", "school", raw())


def test_loose_model_binding_is_rejected(harness):
    _, spies, _, _ = harness

    class Loose(BaseModel):
        model_config = ConfigDict(extra="allow")

    with pytest.raises(ValueError, match="strict frozen"):
        StrictDelegateBinding(Loose, spies[0])


def test_wrong_owner_model_cannot_change_branch(harness):
    _, spies, _, content = harness
    wrong = GovernanceDispatcher(content, preset=StrictDelegateBinding(FixtureAi, spies[0]))
    with pytest.raises(ContentError, match="INVALID_GOVERNANCE_COMMAND"):
        wrong.execute_json("verified", "school", raw())
    assert not spies[0].calls
