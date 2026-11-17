"""Emergency stop component only; assumed guard/transactional memory, no DB proof."""

from dataclasses import replace

import pytest
from pydantic import ValidationError

from sketch2life.application.ai_policy_control import AiPolicyEmergencyStop
from sketch2life.contracts.schemas.ai_policy_control import (
    EmergencyStopCommand,
    EmergencyStopResult,
)
from sketch2life.domain.ai_policy.model import Capability, PolicyError
from tests.ai_policy_fixtures import BODY, execute, harness, published
from tests.unit.test_ai_policy_domain import NOW


def command(epoch=0, key="stop", **changes):
    return EmergencyStopCommand.model_validate(dict(
        client_request_id=key, feature_scope="fixture.feature", expected_epoch=epoch,
        reason="synthetic emergency") | changes)


def setup():
    service, boundary, store = harness()
    return (AiPolicyEmergencyStop(store, boundary, clock=lambda: NOW),
            service, boundary, store)


def test_stop_known_feature_before_any_policy_and_replay_exactly_once():
    stop, _, boundary, store = setup()
    result = stop.execute("operator", "school", command())
    assert result.disabled and result.epoch == 1 and result.record_id is None
    assert len(store.scope_events) == 1 and not store.events and len(store.receipts) == 1
    replay = stop.execute("operator", "school", command())
    assert replay.replayed and replay.epoch == result.epoch
    assert len(store.scope_events) == 1 and not boundary.held


def test_new_stop_key_already_disabled_does_not_emit_another_intent():
    stop, _, _, store = setup()
    stop.execute("operator", "school", command())
    result = stop.execute("operator", "school", command(1, key="second-stop"))
    assert result.epoch == 1 and len(store.scope_events) == 1 and len(store.receipts) == 2


def test_unknown_uninitialized_feature_fails_and_rolls_back_lazy_scope_row():
    stop, _, boundary, store = setup()
    boundary.feature = False
    with pytest.raises(PolicyError, match="AI_POLICY_FEATURE_UNAVAILABLE"):
        stop.execute("operator", "school", command())
    assert not store.scopes and not store.scope_events and not store.receipts


def test_existing_active_scope_can_stop_when_registry_is_withdrawn():
    stop, service, boundary, store = setup()
    prior = published(service, store).record
    boundary.feature = False
    boundary.missing = "model_profile"
    result = stop.execute("operator", "school", command(1))
    assert result.epoch == 2 and result.record_id == prior.record_id
    assert store.load("school", prior.record_id).state == "published"
    assert len(store.scope_events) == 2  # No actual worker/provider ACK implied.


@pytest.mark.parametrize("expected", [0, 2, 999])
def test_epoch_cas_denies_stale_or_future_operator_action(expected):
    stop, service, _, store = setup()
    published(service, store)
    with pytest.raises(PolicyError, match="AI_POLICY_STALE_SCOPE"):
        stop.execute("operator", "school", command(expected))
    assert not store.scopes[("school", "fixture.feature")].disabled
    assert len(store.scope_events) == 1


@pytest.mark.parametrize("actor,org", [("author", "school"), ("publisher", "school"),
                                      ("unknown", "school"), ("operator", "wrong-school")])
def test_scoped_disable_not_implied_by_other_capabilities(actor, org):
    stop, _, _, store = setup()
    with pytest.raises(PolicyError, match="AI_POLICY_FORBIDDEN"):
        stop.execute(actor, org, command())
    assert not store.scopes and not store.receipts


def test_replay_after_current_disable_right_withdrawn_denied():
    stop, _, boundary, store = setup()
    stop.execute("operator", "school", command())
    boundary.rights["operator"] = {Capability.OPERATIONS_READ}
    with pytest.raises(PolicyError, match="AI_POLICY_FORBIDDEN"):
        stop.execute("operator", "school", command())
    assert len(store.scope_events) == 1


def test_replayed_old_stop_never_disables_new_reviewed_activation():
    stop, service, _, store = setup()
    stop.execute("operator", "school", command())
    new = published(service, store).record
    assert not store.scopes[("school", "fixture.feature")].disabled
    with pytest.raises(PolicyError, match="AI_POLICY_RECEIPT_INEFFECTIVE"):
        stop.execute("operator", "school", command())
    assert store.scopes[("school", "fixture.feature")].record_id == new.record_id
    assert store.scopes[("school", "fixture.feature")].epoch == 2


def test_changed_body_under_same_stop_key_conflicts():
    stop, _, _, store = setup()
    stop.execute("operator", "school", command())
    with pytest.raises(PolicyError, match="AI_POLICY_COMMAND_CONFLICT"):
        stop.execute("operator", "school", command(reason="different reason"))
    assert len(store.scope_events) == 1


@pytest.mark.parametrize("failure", ["fail_scope", "fail_receipt", "fail_commit"])
def test_failure_rolls_back_epoch_intent_receipt_together(failure):
    stop, _, boundary, store = setup()
    setattr(store, failure, True)
    with pytest.raises(PolicyError, match="SYNTHETIC_"):
        stop.execute("operator", "school", command())
    assert not store.scopes and not store.scope_events and not store.receipts
    assert not boundary.held


@pytest.mark.parametrize("changes", [
    {"expected_epoch": True}, {"expected_epoch": -1}, {"reason": " "},
    {"reason": None}, {"feature_scope": ""}, {"principal_id": "client-spoof"},
    {"action": "emergency_stop"},
])
def test_strict_internal_command_does_not_extend_cmd48_or_accept_client_authority(changes):
    with pytest.raises(ValidationError):
        command(**changes)


def test_constructed_boolean_epoch_cannot_bypass_revalidation():
    stop, _, _, store = setup()
    malformed = command().model_copy(update={"expected_epoch": False})
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_COMMAND"):
        stop.execute("operator", "school", malformed)
    assert not store.scopes


def test_stop_key_cannot_reuse_a_lifecycle_receipt():
    stop, service, _, store = setup()
    # Same principal must have independent capabilities; no synthetic role inference.
    store.boundary.rights["operator"].add(Capability.AUTHOR)
    execute(service, "operator", "create", "collision", policy=BODY)
    with pytest.raises(PolicyError, match="AI_POLICY_COMMAND_CONFLICT"):
        stop.execute("operator", "school", command(key="collision"))
    assert not store.scope_events


def test_scope_substitution_cannot_be_acknowledged(monkeypatch):
    stop, _, _, store = setup()
    original = store.effective_scope

    def wrong(org, feature, **kwargs):
        return replace(original(org, feature, **kwargs), organization_id="wrong")

    monkeypatch.setattr(store, "effective_scope", wrong)
    with pytest.raises(PolicyError, match="AI_POLICY_SCOPE_MISMATCH"):
        stop.execute("operator", "school", command())
    assert not store.receipts


@pytest.mark.parametrize("change", [{"version": 1}, {"record_id": "partial"},
                                    {"hash": "a" * 64}, {"epoch": 0}])
def test_result_is_strict_complete_pin_metadata(change):
    value = dict(organization_id="school", feature_scope="fixture.feature", epoch=1,
                 disabled=True, record_id=None, version=None, hash=None) | change
    with pytest.raises(ValidationError):
        EmergencyStopResult.model_validate(value)
