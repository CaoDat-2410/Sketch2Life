"""Pure synthetic resource accounting invariants, NOT atomic SQL or actual cost proof."""

from dataclasses import FrozenInstanceError, replace

import pytest

from sketch2life.domain.ai_policy import accounting as ledger
from sketch2life.domain.ai_policy.model import PolicyError

DEFINITION = ledger.DefinitionKey("fixture.budget", 1, "a" * 64)
CONCURRENCY = ledger.DefinitionKey("fixture.concurrency", 1, "b" * 64)
KEY = ledger.BudgetKey("school", "fixture.feature", DEFINITION, "fixture-units", "fixture-window")
TERMS = ledger.LimitTerms(KEY, CONCURRENCY, 10, 2)


def snapshot(**changes):
    return replace(ledger.LedgerSnapshot(KEY, 0, 0, 0), **changes)


def held(estimate=4):
    return ledger.reserve(
        snapshot(),
        TERMS,
        reservation_id="reservation",
        request_digest="c" * 64,
        attempt_id="attempt",
        estimated_units=estimate,
    )


def proof(reservation=None, **changes):
    reservation = held().reservation if reservation is None else reservation
    return replace(
        ledger.SettlementProof(
            "receipt",
            reservation.reservation_id,
            reservation.request_digest,
            reservation.attempt_id,
            reservation.terms.key,
            ledger.SettlementOutcome.CONSUME,
            3,
            ledger.AccountingEvidence.FIXTURE,
            True,
        ),
        **changes,
    )


def test_reserve_exact_counters_and_immutable_originals():
    original = snapshot()
    result = held()
    assert result.snapshot.held_units == 4 and result.snapshot.scope_occupied_slots == 1
    assert original.held_units == 0 and result.reservation.state == ledger.ReservationState.RESERVED
    with pytest.raises(FrozenInstanceError):
        result.snapshot.held_units = 999


@pytest.mark.parametrize("estimate", [0, 1, 10])
def test_nonnegative_estimate_including_zero_still_holds_one_slot(estimate):
    result = held(estimate)
    assert result.snapshot.held_units == estimate and result.snapshot.scope_occupied_slots == 1


@pytest.mark.parametrize(
    "balance,terms,estimate,error",
    [
        (snapshot(), TERMS, 11, "BUDGET_EXCEEDED"),
        (snapshot(held_units=7, spent_units=1), TERMS, 3, "BUDGET_EXCEEDED"),
        (snapshot(), replace(TERMS, budget_ceiling=0), 0, "BUDGET_EXCEEDED"),
        (snapshot(), replace(TERMS, concurrency_ceiling=0), 0, "CONCURRENCY_EXCEEDED"),
        (snapshot(scope_occupied_slots=2), TERMS, 0, "CONCURRENCY_EXCEEDED"),
    ],
)
def test_reserve_ceilings_no_unlimited_zero_or_hidden_existing_usage(
    balance, terms, estimate, error
):
    with pytest.raises(PolicyError, match="AI_POLICY_" + error):
        ledger.reserve(
            balance,
            terms,
            reservation_id="r",
            request_digest="c" * 64,
            attempt_id="a",
            estimated_units=estimate,
        )


def test_duplicate_live_reservation_does_not_charge_or_hold_twice():
    result = held()
    replay = ledger.reserve(
        result.snapshot,
        TERMS,
        reservation_id="reservation",
        request_digest="c" * 64,
        attempt_id="attempt",
        estimated_units=4,
        existing=result.reservation,
    )
    assert replay.replayed and replay.snapshot == result.snapshot


@pytest.mark.parametrize(
    "change",
    [
        {"reservation_id": "other"},
        {"request_digest": "d" * 64},
        {"attempt_id": "other"},
        {"estimated_units": 5},
        {"terms": replace(TERMS, concurrency_ceiling=3)},
    ],
)
def test_duplicate_changed_binding_or_terms_conflicts(change):
    previous = held()
    args = (
        dict(
            reservation_id="reservation",
            request_digest="c" * 64,
            attempt_id="attempt",
            estimated_units=4,
            terms=TERMS,
        )
        | change
    )
    with pytest.raises(PolicyError, match="AI_POLICY_RESERVATION_CONFLICT"):
        ledger.reserve(previous.snapshot, existing=previous.reservation, **args)


@pytest.mark.parametrize("field", ["organization_id", "feature_scope", "unit", "window_id"])
def test_budget_bucket_is_exact_org_feature_unit_window(field):
    changed = snapshot(key=replace(KEY, **{field: "other"}))
    with pytest.raises(PolicyError, match="AI_POLICY_ACCOUNTING_SCOPE_MISMATCH"):
        ledger.reserve(
            changed,
            TERMS,
            reservation_id="r",
            request_digest="c" * 64,
            attempt_id="a",
            estimated_units=1,
        )


def test_new_budget_window_does_not_reset_global_scope_concurrency():
    key = replace(KEY, window_id="new-fixture-window")
    changed = ledger.LedgerSnapshot(key, 0, 0, 2)
    with pytest.raises(PolicyError, match="AI_POLICY_CONCURRENCY_EXCEEDED"):
        ledger.reserve(
            changed,
            replace(TERMS, key=key),
            reservation_id="new-reservation",
            request_digest="d" * 64,
            attempt_id="new-attempt",
            estimated_units=1,
        )


@pytest.mark.parametrize("quantity", [-1, True, 1.5, "1"])
def test_boolean_fractional_negative_or_string_quantities_rejected(quantity):
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_ACCOUNTING_QUANTITY"):
        held(quantity)
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_ACCOUNTING_QUANTITY"):
        snapshot(spent_units=quantity)
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_ACCOUNTING_QUANTITY"):
        replace(TERMS, concurrency_ceiling=quantity)


@pytest.mark.parametrize("actual", [0, 1, 4, 7, 11])
def test_consume_records_exact_actual_usage_and_frees_original_hold_slot(actual):
    previous = held()
    result = ledger.settle(previous.snapshot, previous.reservation, proof(actual_units=actual))
    assert result.snapshot.held_units == 0 and result.snapshot.scope_occupied_slots == 0
    assert result.snapshot.spent_units == actual
    assert result.reservation.overrun == (actual > 4)
    assert not result.reservation.actual_usage_proven  # Fixture is never real usage proof.
    if actual > TERMS.budget_ceiling:
        with pytest.raises(PolicyError, match="AI_POLICY_BUDGET_EXCEEDED"):
            ledger.reserve(
                result.snapshot,
                TERMS,
                reservation_id="next",
                request_digest="d" * 64,
                attempt_id="next-attempt",
                estimated_units=0,
            )


def test_release_only_with_verified_zero_usage_disposition():
    previous = held()
    released = ledger.settle(
        previous.snapshot,
        previous.reservation,
        proof(outcome=ledger.SettlementOutcome.RELEASE, actual_units=0),
    )
    assert released.reservation.state == ledger.ReservationState.RELEASED
    assert released.snapshot == snapshot()
    assert not released.reservation.actual_usage_proven


@pytest.mark.parametrize(
    "change",
    [
        {"reservation_id": "other"},
        {"request_digest": "d" * 64},
        {"attempt_id": "other"},
        {"key": replace(KEY, unit="other")},
        {"key": replace(KEY, window_id="other")},
    ],
)
def test_proof_must_match_exact_reservation_attempt_request_and_original_bucket(change):
    previous = held()
    with pytest.raises(PolicyError, match="AI_POLICY_ACCOUNTING_PROOF_MISMATCH"):
        ledger.settle(previous.snapshot, previous.reservation, proof(**change))


def test_unverified_evidence_or_nonzero_release_cannot_refund():
    previous = held()
    with pytest.raises(PolicyError, match="AI_POLICY_ACCOUNTING_PROOF_UNVERIFIED"):
        ledger.settle(previous.snapshot, previous.reservation, proof(verified=False))
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_ACCOUNTING_PROOF"):
        ledger.settle(
            previous.snapshot,
            previous.reservation,
            proof(outcome=ledger.SettlementOutcome.RELEASE, actual_units=1),
        )


@pytest.mark.parametrize(
    "outcome,actual", [(ledger.SettlementOutcome.CONSUME, 3), (ledger.SettlementOutcome.RELEASE, 0)]
)
def test_settlement_retry_or_reconcile_same_terminal_proof_does_not_charge_or_refund_twice(
    outcome, actual
):
    previous = held()
    evidence = proof(outcome=outcome, actual_units=actual)
    result = ledger.settle(previous.snapshot, previous.reservation, evidence)
    replay = ledger.settle(result.snapshot, result.reservation, evidence)
    assert replay.replayed and replay.snapshot == result.snapshot
    with pytest.raises(PolicyError, match="AI_POLICY_SETTLEMENT_CONFLICT"):
        ledger.settle(
            result.snapshot, result.reservation, replace(evidence, receipt_id="different")
        )
    with pytest.raises(PolicyError, match="AI_POLICY_RESERVATION_TERMINAL"):
        ledger.reserve(
            result.snapshot,
            TERMS,
            reservation_id="reservation",
            request_digest="c" * 64,
            attempt_id="attempt",
            estimated_units=4,
            existing=result.reservation,
        )


@pytest.mark.parametrize("change", [{"held_units": 3}, {"scope_occupied_slots": 0}])
def test_corrupt_counter_cannot_refund_another_reservations_resources(change):
    previous = held()
    with pytest.raises(PolicyError, match="AI_POLICY_ACCOUNTING_BALANCE_CONFLICT"):
        ledger.settle(replace(previous.snapshot, **change), previous.reservation, proof())


def test_settlement_keeps_original_budget_definition_window_and_limit_snapshot():
    previous = held()
    new_key = replace(KEY, window_id="later-window")
    with pytest.raises(PolicyError, match="AI_POLICY_ACCOUNTING_SCOPE_MISMATCH"):
        ledger.settle(
            snapshot(key=new_key, held_units=4, scope_occupied_slots=1),
            previous.reservation,
            proof(),
        )
    result = ledger.settle(previous.snapshot, previous.reservation, proof())
    assert result.reservation.terms == TERMS and result.snapshot.key == KEY


@pytest.mark.parametrize(
    "evidence,proven",
    [(ledger.AccountingEvidence.FIXTURE, False), (ledger.AccountingEvidence.RUNTIME, True)],
)
def test_fixture_evidence_not_promoted_to_actual_runtime_usage(evidence, proven):
    previous = held()
    result = ledger.settle(previous.snapshot, previous.reservation, proof(evidence_kind=evidence))
    assert result.reservation.actual_usage_proven is proven


@pytest.mark.parametrize("invalid", [True, 0])
def test_definition_version_requires_positive_nonboolean_int(invalid):
    with pytest.raises(PolicyError):
        ledger.DefinitionKey("ref", invalid, "a" * 64)


def test_terminal_reservation_cannot_be_constructed_with_mismatched_proof_state():
    previous = held()
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_RESERVATION"):
        replace(previous.reservation, state=ledger.ReservationState.RELEASED, settlement=proof())


def test_terminal_reservation_rejects_untyped_proof_with_safe_domain_error():
    previous = held()
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_RESERVATION"):
        replace(previous.reservation, state=ledger.ReservationState.RELEASED, settlement={})
