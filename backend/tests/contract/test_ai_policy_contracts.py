"""BE2-14 C1 shape and typed-binding checks; handler below is only a spy."""

import json

import pytest
from pydantic import ValidationError

from sketch2life.application.governance_dispatcher import StrictDelegateBinding
from sketch2life.contracts.schemas.ai_policy import AiPolicyCommand, AiPolicyWrite
from sketch2life.contracts.schemas.governance import select_governance

REF = {"ref": "synthetic-definition", "version": 1, "hash": "a" * 64}
BODY = {
    "title": "Synthetic policy", "feature_scope": "fixture.feature",
    "model_profile_refs": [REF], "moderation_policy_ref": REF,
    "retry_policy_ref": REF, "budget_policy_ref": REF, "concurrency_policy_ref": REF,
    "required_gates": dict.fromkeys(
        ["teacher_review", "consent", "current_source", "safety"], True),
}
ACTIONS = ("create", "edit", "submit_review", "record_review", "request_changes",
           "publish", "recall", "archive")


def payload(action):
    value = dict(record_kind="policy", policy_kind="ai", action=action, client_request_id="req")
    if action != "create":
        value.update(record_id="policy", target_version=1, target_hash="a" * 64)
    if action in {"create", "edit"}:
        value["policy"] = BODY
    if action in {"record_review", "request_changes"}:
        value["review"] = dict(
            target_kind="ai_policy", target_id="policy", target_version=1, target_hash="a" * 64,
            context_revision=1, expected_review_revision=1, dimension="safety",
            decision="request_changes" if action == "request_changes" else "approve",
            review_policy_version="fixture.governance", reason="synthetic reason")
    if action in {"recall", "archive", "request_changes"}:
        value["reason"] = "synthetic reason"
    if action == "publish":
        value["review_ref"] = dict(safety_review_id="safety", pedagogical_review_id="pedagogy",
                                   review_policy_version="fixture.governance")
    return value


@pytest.mark.parametrize("action", ACTIONS)
def test_eight_actions_roundtrip_and_select_only_ai_policy(action):
    command = AiPolicyCommand.model_validate_json(json.dumps(payload(action)))
    assert AiPolicyCommand.model_validate_json(command.model_dump_json()) == command
    assert select_governance(command.model_dump_json().encode()).branch == "ai_policy"


@pytest.mark.parametrize("action", ACTIONS)
def test_spare_null_field_rejected(action):
    value = payload(action)
    value["policy" if action not in {"create", "edit"} else "reason"] = None
    with pytest.raises(ValidationError):
        AiPolicyCommand.model_validate_json(json.dumps(value))


@pytest.mark.parametrize("action", ACTIONS)
def test_required_action_payload_cannot_be_missing(action):
    value = payload(action)
    del value["policy" if action == "create" else "target_hash"]
    with pytest.raises(ValidationError):
        AiPolicyCommand.model_validate_json(json.dumps(value))


@pytest.mark.parametrize("gate", ["teacher_review", "consent", "current_source", "safety"])
@pytest.mark.parametrize("value", [False, 1, "true", None])
def test_no_mandatory_gate_bypass_or_coercion(gate, value):
    body = BODY | {"required_gates": BODY["required_gates"] | {gate: value}}
    with pytest.raises(ValidationError):
        AiPolicyWrite.model_validate_json(json.dumps(body))


@pytest.mark.parametrize("extra", ["api_key", "endpoint", "budget", "configuration"])
def test_unallowlisted_settings_rejected(extra):
    with pytest.raises(ValidationError):
        AiPolicyWrite.model_validate_json(json.dumps(BODY | {extra: "synthetic"}))


@pytest.mark.parametrize("change", [
    {"title": " "}, {"model_profile_refs": []}, {"model_profile_refs": [REF, REF]},
    {"budget_policy_ref": REF | {"version": True}},
    {"retry_policy_ref": REF | {"hash": "not-a-hash"}},
    {"concurrency_policy_ref": REF | {"endpoint": "synthetic"}},
])
def test_definition_shapes_and_uniqueness(change):
    with pytest.raises(ValidationError):
        AiPolicyWrite.model_validate_json(json.dumps(BODY | change))


@pytest.mark.parametrize("change", [
    {"target_kind": "learning_content"}, {"target_id": "other"}, {"target_version": 2},
    {"target_hash": "b" * 64}, {"context_revision": 0}, {"expected_review_revision": -1},
    {"reviewer_id": "client-spoof"}, {"effective": True},
])
def test_review_exact_target_no_spoofed_server_fields(change):
    value = payload("record_review")
    value["review"] |= change
    with pytest.raises(ValidationError):
        AiPolicyCommand.model_validate_json(json.dumps(value))


@pytest.mark.parametrize("change", [{"decision": "approve"}, {"reason": " "},
                                    {"reason": "different"}])
def test_changes_action_requires_matching_negative_proof(change):
    value = payload("request_changes")
    value["review"] |= change
    with pytest.raises(ValidationError):
        AiPolicyCommand.model_validate_json(json.dumps(value))


def test_publish_needs_distinct_review_ids():
    value = payload("publish")
    value["review_ref"]["pedagogical_review_id"] = "safety"
    with pytest.raises(ValidationError):
        AiPolicyCommand.model_validate_json(json.dumps(value))


@pytest.mark.parametrize("action", ACTIONS)
def test_concrete_model_binds_before_spy_effect(action):
    class StopAfterValidation(Exception):
        pass

    class Spy:
        def execute(self, principal_id, organization_id, command, *, expected_revision):
            assert isinstance(command, AiPolicyCommand)
            assert (principal_id, organization_id) == ("verified-admin", "school")
            assert expected_revision == (None if action == "create" else 4)
            raise StopAfterValidation

    raw = json.dumps(payload(action)).encode()
    with pytest.raises(StopAfterValidation):
        StrictDelegateBinding(AiPolicyCommand, Spy()).invoke(
            "verified-admin", "school", raw, select_governance(raw),
            expected_revision=None if action == "create" else 4)


@pytest.mark.parametrize("action", ACTIONS)
def test_invalid_payload_cannot_reach_bound_handler(action):
    from sketch2life.domain.learning_content.model import ContentError

    class Never:
        def execute(self, *args, **kwargs):
            pytest.fail("invalid command reached a business handler")

    raw = json.dumps(payload(action) | {"unknown_config": "synthetic"}).encode()
    with pytest.raises(ContentError, match="INVALID_GOVERNANCE_COMMAND"):
        StrictDelegateBinding(AiPolicyCommand, Never()).invoke(
            "verified-admin", "school", raw, select_governance(raw), expected_revision=4)
