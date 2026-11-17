"""Pure claim/response fencing and strict hook references; no SQL or provider execution."""

from dataclasses import replace
from datetime import timedelta

import pytest
from pydantic import ValidationError

from sketch2life.application.ai_policy_copy_delivery import delivery_response
from sketch2life.contracts.schemas.ai_policy_copy import CopyReceiptReference
from sketch2life.contracts.schemas.ai_policy_copy_delivery import CopyHookResponse
from sketch2life.domain.ai_policy.copy_delivery import (
    DeliveryResponse,
    DeliveryState,
    DeliveryStatus,
    HookOutcome,
    claim_delivery,
    finish_delivery,
)
from sketch2life.domain.ai_policy.model import PolicyError
from tests.ai_policy_copy_operation_fixtures import schedule, setup
from tests.unit.test_ai_policy_domain import NOW

KEY, DIGEST = "a" * 64, "b" * 64
DEADLINE = NOW + timedelta(minutes=1)


def claim(state=None, *, token="claim-1", revision=0, now=NOW):
    return claim_delivery(
        state or DeliveryState(KEY, DIGEST),
        expected_revision=revision,
        token=token,
        now=now,
        expires_at=now + timedelta(minutes=1),
    )


def response(outcome=HookOutcome.PENDING, **changes):
    fields = dict(operation_key=KEY, binding_digest=DIGEST, outcome=outcome, reason_code="WAITING")
    if outcome is HookOutcome.RECEIPT_AVAILABLE:
        fields |= dict(reference="fixture-receipt", reference_hash="c" * 64, reason_code=None)
    return DeliveryResponse(**(fields | changes))


def finish(state, result=None, *, token="claim-1", revision=1, now=NOW):
    return finish_delivery(
        state, result or response(), token=token, expected_revision=revision, now=now
    )


def test_claim_increments_revision_keeps_key_and_has_no_execution_authority():
    state = claim()
    assert state.status is DeliveryStatus.IN_FLIGHT and state.revision == 1
    assert state.operation_key == KEY and state.used_tokens == ("claim-1",)
    assert state.claim_expires_at == DEADLINE
    assert not hasattr(state, "deleted") and not hasattr(state, "authorized")


@pytest.mark.parametrize("outcome", list(HookOutcome))
def test_hook_outcomes_remain_delivery_metadata_and_exact_finish_replay_is_idempotent(outcome):
    result = response(outcome)
    state = finish(claim(), result)
    assert state.status.value == outcome.value and state.revision == 2
    assert state.claim_token is None and state.last_response == result
    assert finish(state, result, now=NOW + timedelta(days=1)) == state
    assert not hasattr(state, "actual_deletion_proven")


@pytest.mark.parametrize("status", [HookOutcome.PENDING, HookOutcome.EXCEPTION])
def test_retryable_outcome_claim_preserves_operation_key_and_rotates_token(status):
    state = finish(claim(), response(status))
    again = claim(state, revision=2, token="claim-2")
    assert again.operation_key == KEY and again.revision == 3
    assert again.used_tokens == ("claim-1", "claim-2")
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_DELIVERY_STALE"):
        finish(again, response(status))


@pytest.mark.parametrize("status", [HookOutcome.UNSUPPORTED, HookOutcome.RECEIPT_AVAILABLE])
def test_unsupported_or_unverified_receipt_cannot_be_automatically_redispatched(status):
    state = finish(claim(), response(status))
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_DELIVERY_NOT_RETRYABLE"):
        claim(state, revision=2, token="claim-2")


def test_unexpired_claim_is_busy_and_expired_takeover_fences_old_response():
    original = claim()
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_DELIVERY_BUSY"):
        claim(original, revision=1, token="claim-2")
    replacement = claim(original, revision=1, token="claim-2", now=DEADLINE)
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_DELIVERY_STALE"):
        finish(replacement, now=DEADLINE)
    done = finish(replacement, token="claim-2", revision=2, now=DEADLINE)
    assert done.revision == 3 and done.operation_key == original.operation_key


@pytest.mark.parametrize("when", [DEADLINE, DEADLINE + timedelta(seconds=1)])
def test_expired_claim_cannot_accept_even_exact_response(when):
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_DELIVERY_EXPIRED"):
        finish(claim(), now=when)


def test_used_token_cannot_return_after_completion_or_expired_takeover():
    original = claim()
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_DELIVERY_TOKEN_REUSED"):
        claim(original, revision=1, now=DEADLINE)
    done = finish(original)
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_DELIVERY_TOKEN_REUSED"):
        claim(done, revision=2)


@pytest.mark.parametrize(
    "changes",
    [
        {"expected_revision": True},
        {"expected_revision": -1},
        {"expected_revision": 7},
        {"token": "https://private-url"},
        {"now": NOW.replace(tzinfo=None)},
        {"expires_at": NOW},
        {"expires_at": NOW.replace(tzinfo=None)},
    ],
)
def test_bad_claim_arguments_fail_closed(changes):
    with pytest.raises(PolicyError):
        claim_delivery(
            DeliveryState(KEY, DIGEST),
            **(dict(expected_revision=0, token="claim", now=NOW, expires_at=DEADLINE) | changes),
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"expected_revision": True},
        {"expected_revision": 0},
        {"token": "old-claim"},
        {"now": NOW.replace(tzinfo=None)},
    ],
)
def test_bad_completion_or_stale_claim_arguments_fail_closed(changes):
    with pytest.raises(PolicyError):
        finish_delivery(
            claim(), response(), **(dict(expected_revision=1, token="claim-1", now=NOW) | changes)
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"operation_key": "f" * 64},
        {"binding_digest": "f" * 64},
    ],
)
def test_response_wrong_operation_or_binding_rejected(changes):
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_DELIVERY_RESPONSE_MISMATCH"):
        finish(claim(), response(**changes))


def test_changed_response_after_completion_is_conflict_not_a_second_mutation():
    done = finish(claim())
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_DELIVERY_STALE"):
        finish(done, response(HookOutcome.EXCEPTION))


def test_response_cannot_predate_claim_start():
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_DELIVERY_EXPIRED"):
        finish(claim(), now=NOW - timedelta(seconds=1))


def test_snapshot_cannot_claim_receipt_available_is_in_flight_or_reverse_deadline():
    state = claim()
    for change in (
        {"claim_started_at": DEADLINE},
        {"claim_started_at": NOW.replace(tzinfo=None)},
        {"last_response": response(HookOutcome.RECEIPT_AVAILABLE)},
    ):
        with pytest.raises(PolicyError):
            replace(state, **change)


@pytest.mark.parametrize(
    "changes",
    [
        {"status": "in_flight"},
        {"revision": True},
        {"revision": -1},
        {"status": DeliveryStatus.PENDING},
        {"claim_token": "orphan"},
        {"used_tokens": ["claim"]},
        {"used_tokens": ("claim", "claim")},
        {"status": DeliveryStatus.IN_FLIGHT},
        {"last_response": "malformed"},
    ],
)
def test_invalid_delivery_snapshots_cannot_be_constructed(changes):
    with pytest.raises(PolicyError):
        replace(DeliveryState(KEY, DIGEST), **changes)


@pytest.mark.parametrize(
    "changes",
    [
        {"outcome": "deleted"},
        {"outcome": "pending"},
        {"reference": "raw-child-bytes"},
        {"reference_hash": "c" * 64},
        {"reason_code": None},
        {"reason_code": "secret url"},
    ],
)
def test_domain_response_rejects_untyped_or_false_terminal_and_private_payloads(changes):
    with pytest.raises(PolicyError):
        response(**changes)


@pytest.mark.parametrize("outcome", ["deleted", "cancelled", "accepted", "sent"])
def test_wire_response_cannot_claim_deleted_or_confirmed_from_transport_success(outcome):
    with pytest.raises(ValidationError):
        CopyHookResponse(operation_key=KEY, binding_digest=DIGEST, outcome=outcome)


@pytest.mark.parametrize("extra", ["verified", "actual_deletion_proven", "cancel_confirmed", "url"])
def test_hook_response_forbids_client_assertions_or_raw_endpoint_fields(extra):
    with pytest.raises(ValidationError):
        CopyHookResponse.model_validate(
            dict(
                operation_key=KEY,
                binding_digest=DIGEST,
                outcome="pending",
                reason_code="WAITING",
                **{extra: True},
            )
        )


def test_native_hook_echo_requires_original_key_and_binding_and_receipt_is_only_reference():
    service, _, _ = setup()
    envelope = schedule(service)
    raw = CopyHookResponse(
        operation_key=envelope.operation_key,
        binding_digest=envelope.binding_digest,
        outcome="receipt_available",
        reference=CopyReceiptReference(ref="fixture-receipt", hash="c" * 64),
    )
    result = delivery_response(envelope, raw)
    assert result.outcome is HookOutcome.RECEIPT_AVAILABLE and result.reference == "fixture-receipt"
    for changed in (
        {"operation_key": "f" * 64},
        {"binding_digest": "f" * 64},
        {"outcome": "deleted"},
        {"reference": None},
    ):
        with pytest.raises(PolicyError, match="AI_POLICY_COPY_DELIVERY_RESPONSE_MISMATCH"):
            delivery_response(envelope, raw.model_copy(update=changed))


@pytest.mark.parametrize(
    "changes",
    [
        {"outcome": "receipt_available"},
        {"reference": CopyReceiptReference(ref="proof", hash="c" * 64)},
        {"reason_code": None},
    ],
)
def test_wire_response_requires_receipt_for_receipt_available_and_reason_for_nonreceipt(changes):
    with pytest.raises(ValidationError):
        CopyHookResponse.model_validate(
            dict(operation_key=KEY, binding_digest=DIGEST, outcome="pending", reason_code="WAITING")
            | changes
        )
