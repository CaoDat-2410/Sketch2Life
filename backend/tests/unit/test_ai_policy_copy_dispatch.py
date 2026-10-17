"""ASSUMED owner/retry policy + MEMORY + synthetic hooks, not real provider/DB proof."""

from datetime import timedelta

import pytest

from sketch2life.contracts.schemas.ai_policy_copy import CopyReceiptReference
from sketch2life.domain.ai_policy.copy_delivery import DeliveryStatus
from sketch2life.domain.ai_policy.model import PolicyError
from tests.ai_policy_copy_dispatch_fixtures import dispatch, setup
from tests.ai_policy_copy_operation_fixtures import command
from tests.unit.test_ai_policy_domain import NOW


def current(store, envelope):
    return store.scopes["school", "scope"].get("deliveries", {}).get(envelope.operation_key)


def test_claim_commits_then_hook_runs_without_db_transaction_then_guarded_completion():
    dispatcher, boundary, hook, store, envelope = setup()
    observed = []
    hook.on_call = lambda env: observed.append(current(store, env).status)
    result = dispatch(dispatcher, envelope)
    assert result.status is DeliveryStatus.PENDING and result.revision == 2
    assert observed == [DeliveryStatus.IN_FLIGHT] and hook.calls == [envelope]
    assert current(store, envelope) == result
    assert [c[0] for c in boundary.delivery_calls] == [
        "claim",
        "claim",
        "dispatch",
        "dispatch",
        "dispatch",
        "completion",
        "completion",
    ]
    assert not hasattr(result, "actual_deletion_proven")


def test_missing_hook_is_unsupported_and_cannot_be_automatically_redispatched():
    dispatcher, _, hook, _, envelope = setup()
    dispatcher.hook = None
    result = dispatch(dispatcher, envelope)
    assert result.status is DeliveryStatus.UNSUPPORTED
    assert result.last_response.reason_code == "HOOK_UNAVAILABLE" and not hook.calls
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_DELIVERY_NOT_RETRYABLE"):
        dispatch(dispatcher, envelope, revision=2)


def test_hook_exception_is_redacted_and_committed_as_exception_metadata():
    dispatcher, _, hook, _, envelope = setup()
    hook.fail = True
    result = dispatch(dispatcher, envelope)
    assert result.status is DeliveryStatus.EXCEPTION
    assert result.last_response.reason_code == "HOOK_EXCEPTION"


@pytest.mark.parametrize(
    "changes",
    [
        {"operation_key": "f" * 64},
        {"binding_digest": "f" * 64},
        {"outcome": "deleted"},
        {"outcome": "cancelled"},
        {"reason_code": None},
    ],
)
def test_malformed_hook_response_records_safe_exception_not_false_ack(changes):
    dispatcher, _, hook, _, envelope = setup()
    hook.changes = changes
    result = dispatch(dispatcher, envelope)
    assert result.status is DeliveryStatus.EXCEPTION
    assert result.last_response.reason_code == "HOOK_RESPONSE_INVALID"


def test_receipt_available_does_not_verify_deletion_and_is_not_redispatched():
    dispatcher, _, hook, _, envelope = setup()
    hook.changes = dict(
        outcome="receipt_available",
        reference=CopyReceiptReference(ref="fixture-proof", hash="c" * 64),
    )
    result = dispatch(dispatcher, envelope)
    assert result.status is DeliveryStatus.RECEIPT_AVAILABLE
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_DELIVERY_NOT_RETRYABLE"):
        dispatch(dispatcher, envelope, revision=2)
    assert len(hook.calls) == 1


@pytest.mark.parametrize("phase", ["claim", "dispatch", "completion"])
def test_current_phase_denial_never_becomes_provider_success(phase):
    dispatcher, boundary, hook, store, envelope = setup()
    boundary.denied_phase = phase
    with pytest.raises(PolicyError, match="AI_POLICY_FORBIDDEN"):
        dispatch(dispatcher, envelope)
    if phase == "claim":
        assert current(store, envelope) is None and not hook.calls
    else:
        assert current(store, envelope).status is DeliveryStatus.IN_FLIGHT
        assert len(hook.calls) == (1 if phase == "completion" else 0)


def test_current_command_read_denial_happens_before_read_or_hook():
    dispatcher, boundary, hook, store, envelope = setup()
    before = store.commits
    boundary.changes = {"allowed": False}
    with pytest.raises(PolicyError, match="AI_POLICY_FORBIDDEN"):
        dispatch(dispatcher, envelope)
    assert store.commits == before and not hook.calls


def test_original_profile_must_match_exact_version_not_latest_alias():
    dispatcher, boundary, hook, _, envelope = setup()
    boundary.profile = boundary.profile.model_copy(update={"version": 2})
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_PROFILE_MISMATCH"):
        dispatch(dispatcher, envelope)
    assert not hook.calls


def test_explicit_deadline_from_trusted_policy_is_required_and_bounded_by_grant():
    dispatcher, boundary, hook, _, envelope = setup()
    boundary.deadline = NOW
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_DELIVERY_EXPIRED"):
        dispatch(dispatcher, envelope)
    boundary.deadline = NOW + timedelta(hours=2)
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_DEPENDENCY_UNAVAILABLE"):
        dispatch(dispatcher, envelope)
    assert not hook.calls


def test_pending_retry_requires_current_revision_and_reuses_exact_provider_key():
    dispatcher, _, hook, _, envelope = setup()
    first = dispatch(dispatcher, envelope)
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_DELIVERY_STALE"):
        dispatch(dispatcher, envelope)
    second = dispatch(dispatcher, envelope, revision=first.revision)
    assert second.revision == 4 and len(hook.calls) == 2
    assert hook.calls[0] == hook.calls[1] == envelope


def test_late_hook_result_leaves_expired_claim_for_recovery_not_false_rollback():
    dispatcher, boundary, hook, store, envelope = setup()
    hook.on_call = lambda env: setattr(dispatcher, "clock", lambda: NOW + timedelta(minutes=2))
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_DELIVERY_EXPIRED"):
        dispatch(dispatcher, envelope)
    assert current(store, envelope).status is DeliveryStatus.IN_FLIGHT and len(hook.calls) == 1


def test_owner_revocation_after_hook_does_not_record_response_or_invent_external_rollback():
    dispatcher, boundary, hook, store, envelope = setup()
    hook.on_call = lambda env: setattr(boundary, "denied_phase", "completion")
    with pytest.raises(PolicyError, match="AI_POLICY_FORBIDDEN"):
        dispatch(dispatcher, envelope)
    assert current(store, envelope).revision == 1 and hook.calls == [envelope]


def test_commit_failure_before_hook_rolls_back_claim_and_never_invokes_hook():
    dispatcher, _, hook, store, envelope = setup()
    original = store.claim_delivery

    def fail(*args, **kwargs):
        result = original(*args, **kwargs)
        store.fail_commit = True
        return result

    store.claim_delivery = fail
    with pytest.raises(PolicyError, match="SYNTHETIC_INVENTORY_COMMIT_FAILURE"):
        dispatch(dispatcher, envelope)
    assert current(store, envelope) is None and not hook.calls


@pytest.mark.parametrize("revision", [True, -1, "0"])
def test_invalid_revision_rejected_before_authority_or_hook(revision):
    dispatcher, boundary, hook, _, envelope = setup()
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_COPY_OPERATION"):
        dispatch(dispatcher, envelope, revision=revision)
    assert not boundary.calls and not hook.calls


def test_wrong_data_request_cannot_dispatch_original_intent():
    dispatcher, _, hook, _, envelope = setup()
    changed = command(
        data_request_ref=envelope.command.data_request_ref.model_copy(update={"version": 2})
    )
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_SCOPE_MISMATCH"):
        dispatcher.dispatch(
            "operator", "school", changed, envelope.operation_key, expected_revision=0
        )
    assert not hook.calls
