"""Guarded services with real use component + ASSUMED authority/MEMORY ledger, not SQL."""

from dataclasses import replace

import pytest

from sketch2life.application.ai_policy_control import AiPolicyEmergencyStop
from sketch2life.contracts.schemas.ai_policy_accounting import (
    AccountingEvidenceRef,
    ResourceReservationRequest,
    ResourceSettlementRequest,
)
from sketch2life.contracts.schemas.ai_policy_control import EmergencyStopCommand
from sketch2life.domain.ai_policy import accounting as domain
from sketch2life.domain.ai_policy.model import PolicyError
from tests.ai_policy_accounting_fixtures import EVIDENCE, accounting_setup
from tests.unit.test_ai_policy_domain import NOW


def reserve_command(pin, **changes):
    return ResourceReservationRequest.model_validate(
        dict(
            client_request_id="reserve-one",
            request=pin.request,
            pin=pin,
            attempt_id="attempt-one",
            phase="dispatch",
        )
        | changes
    )


def settle_command(reservation, **changes):
    return ResourceSettlementRequest.model_validate(
        dict(
            client_request_id="settle-one",
            reservation_id=reservation.reservation_id,
            operation="consume",
            evidence_ref=EVIDENCE,
        )
        | changes
    )


def reserve(service, pin, **changes):
    return service.reserve("worker", "school", reserve_command(pin, **changes))


def settle(service, reservation, **changes):
    return service.settle(
        "worker", "school", "fixture.feature", settle_command(reservation, **changes)
    )


@pytest.mark.parametrize("phase", ["create", "dispatch", "retry"])
def test_reserve_holds_current_use_and_accounting_to_commit_with_exact_original_pin(phase):
    service, boundary, store, pin, _, use, _ = accounting_setup()
    result = reserve(service, pin, phase=phase)
    assert result.snapshot.held_units == 4 and result.snapshot.scope_occupied_slots == 1
    assert boundary.quote_calls[-1][0].pin == pin
    assert store.commit_count == 1 and len(store.events) == len(store.receipts) == 1
    assert not boundary.held and not use.held


@pytest.mark.parametrize("new_key", [False, True])
def test_duplicate_attempt_same_or_new_client_key_never_allocates_twice(new_key):
    service, boundary, store, pin, *_ = accounting_setup()
    first = reserve(service, pin)
    result = reserve(service, pin, client_request_id="another-key" if new_key else "reserve-one")
    assert result.replayed and result.reservation == first.reservation
    assert result.snapshot == first.snapshot and len(store.events) == 1
    assert len(boundary.quote_calls) == 2
    assert len(store.receipts) == (2 if new_key else 1)


def test_changed_command_same_receipt_key_conflicts_without_second_hold():
    service, _, store, pin, *_ = accounting_setup()
    reserve(service, pin)
    with pytest.raises(PolicyError, match="AI_POLICY_RESOURCE_RECEIPT_CONFLICT"):
        reserve(service, pin, attempt_id="attempt-two")
    assert len(store.reservations) == len(store.events) == 1


@pytest.mark.parametrize(
    "change",
    [
        {"window_id": "next-window"},
        {"unit": "different-unit"},
        {"estimated_units": 5},
        {"budget_ceiling": 11},
        {"concurrency_ceiling": 3},
    ],
)
def test_replay_cannot_silently_replace_original_terms_after_current_quote_changes(change):
    service, boundary, store, pin, *_ = accounting_setup()
    first = reserve(service, pin)
    boundary.quote_changes = change
    with pytest.raises(PolicyError, match="AI_POLICY_RESERVATION_CONFLICT"):
        reserve(service, pin)
    assert store.reservations["school", first.reservation.reservation_id] == first.reservation
    assert len(store.events) == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("binding_digest", "f" * 64),
        ("attempt_id", "other-attempt"),
        ("estimated_units", True),
    ],
)
def test_bad_current_quote_denied_before_any_ledger_commit(field, value):
    service, boundary, store, pin, *_ = accounting_setup()
    boundary.quote_changes[field] = value
    with pytest.raises(PolicyError, match="AI_POLICY_RESOURCE_QUOTE_MISMATCH"):
        reserve(service, pin)
    assert store.commit_count == 0 and not store.reservations


@pytest.mark.parametrize("where", ["accounting", "use", "principal", "organization"])
def test_replay_rechecks_current_authority_and_identity(where):
    service, boundary, store, pin, _, use, _ = accounting_setup()
    reserve(service, pin)
    if where == "accounting":
        boundary.allowed = False
    elif where == "use":
        use.use_allowed = False
    else:
        boundary.authority_changes[where + "_id"] = "different"
    with pytest.raises(PolicyError):
        reserve(service, pin)
    assert len(store.events) == 1


@pytest.mark.parametrize("failure", ["fail_receipt", "fail_commit"])
def test_reservation_error_rolls_back_counters_reservation_receipt_and_audit(failure):
    service, _, store, pin, *_ = accounting_setup()
    setattr(store, failure, True)
    with pytest.raises(PolicyError, match="SYNTHETIC_LEDGER"):
        reserve(service, pin)
    assert not store.reservations and not store.receipts and not store.events
    assert not store.slots and not store.buckets


@pytest.mark.parametrize("operation", ["consume", "release", "reconcile"])
def test_verified_settlement_frees_original_resources_once_even_new_client_key(operation):
    service, boundary, store, pin, *_ = accounting_setup()
    first = reserve(service, pin)
    if operation == "release":
        boundary.proof_changes = dict(outcome=domain.SettlementOutcome.RELEASE, actual_units=0)
    result = settle(service, first.reservation, operation=operation)
    again = settle(service, first.reservation, operation=operation, client_request_id="new-key")
    replay = settle(service, first.reservation, operation=operation)
    assert replay.replayed and again.replayed
    assert replay.snapshot == result.snapshot
    assert result.snapshot.held_units == result.snapshot.scope_occupied_slots == 0
    assert result.snapshot.spent_units == (0 if operation == "release" else 3)
    assert not result.reservation.actual_usage_proven and len(store.events) == 2
    assert len(boundary.proof_calls) == 3


@pytest.mark.parametrize(
    "change",
    [
        {"reservation_id": "other"},
        {"attempt_id": "other"},
        {"request_digest": "f" * 64},
        {"verified": False},
    ],
)
def test_wrong_or_unverified_terminal_proof_cannot_settle(change):
    service, boundary, store, pin, *_ = accounting_setup()
    first = reserve(service, pin)
    boundary.proof_changes = change
    with pytest.raises(PolicyError):
        settle(service, first.reservation)
    assert len(store.events) == 1
    assert store.reservations["school", first.reservation.reservation_id] == first.reservation


@pytest.mark.parametrize(
    "change", [{"actual_units": True}, {"verified": 1}, {"outcome": "consume"}]
)
def test_native_malformed_proof_is_revalidated_not_coerced(change):
    service, boundary, store, pin, *_ = accounting_setup()
    first = reserve(service, pin)
    boundary.native_proof_changes = change
    with pytest.raises(PolicyError, match="AI_POLICY_ACCOUNTING_PROOF_MISMATCH"):
        settle(service, first.reservation)
    assert len(store.events) == 1


def test_nested_native_proof_key_is_revalidated():
    service, boundary, store, pin, *_ = accounting_setup()
    first = reserve(service, pin)
    malformed_key = replace(first.reservation.terms.key)
    object.__setattr__(malformed_key, "definition", replace(malformed_key.definition))
    object.__setattr__(malformed_key.definition, "version", True)
    boundary.native_proof_changes = {"key": malformed_key}
    with pytest.raises(PolicyError, match="AI_POLICY_ACCOUNTING_PROOF_MISMATCH"):
        settle(service, first.reservation)
    assert len(store.events) == 1


def test_consume_release_dispositions_cannot_be_substituted():
    service, boundary, _, pin, *_ = accounting_setup()
    first = reserve(service, pin)
    with pytest.raises(PolicyError, match="AI_POLICY_ACCOUNTING_PROOF_MISMATCH"):
        settle(service, first.reservation, operation="release")
    boundary.proof_changes = dict(outcome=domain.SettlementOutcome.RELEASE, actual_units=0)
    with pytest.raises(PolicyError, match="AI_POLICY_ACCOUNTING_PROOF_MISMATCH"):
        settle(service, first.reservation, operation="consume")


def test_after_stop_reconcile_uses_original_window_without_reauthorizing_use():
    service, boundary, store, pin, _, use, policy_store = accounting_setup()
    first = reserve(service, pin)
    AiPolicyEmergencyStop(policy_store, use, clock=lambda: NOW).execute(
        "operator",
        "school",
        EmergencyStopCommand(
            client_request_id="stop",
            feature_scope="fixture.feature",
            expected_epoch=1,
            reason="fixture-stop",
        ),
    )
    use.use_allowed = False
    with pytest.raises(PolicyError):
        reserve(service, pin)
    uses_before = len(use.use_calls)
    boundary.quote_changes = {"window_id": "different-window"}
    result = settle(service, first.reservation, operation="reconcile")
    assert result.reservation.terms == first.reservation.terms
    assert result.snapshot.spent_units == 3 and len(use.use_calls) == uses_before
    assert len(store.events) == 2


def test_terminal_reservation_cannot_resume_and_conflicting_proof_cannot_charge_again():
    service, boundary, store, pin, *_ = accounting_setup()
    first = reserve(service, pin)
    settle(service, first.reservation)
    with pytest.raises(PolicyError, match="AI_POLICY_RESERVATION_TERMINAL"):
        reserve(service, pin)
    boundary.proof_changes = {"actual_units": 9}
    with pytest.raises(PolicyError, match="AI_POLICY_SETTLEMENT_CONFLICT"):
        settle(service, first.reservation)
    assert len(store.events) == 2


def test_settlement_replay_rechecks_rights_and_evidence_hash():
    service, boundary, store, pin, *_ = accounting_setup()
    first = reserve(service, pin)
    settle(service, first.reservation)
    boundary.allowed = False
    with pytest.raises(PolicyError, match="AI_POLICY_FORBIDDEN"):
        settle(service, first.reservation)
    boundary.allowed = True
    with pytest.raises(PolicyError, match="AI_POLICY_ACCOUNTING_PROOF_UNVERIFIED"):
        settle(
            service,
            first.reservation,
            evidence_ref=AccountingEvidenceRef(ref=EVIDENCE.ref, hash="f" * 64),
        )
    assert len(store.events) == 2


@pytest.mark.parametrize("failure", ["fail_receipt", "fail_commit"])
def test_settlement_failure_rolls_back_terminal_state_and_counters(failure):
    service, _, store, pin, *_ = accounting_setup()
    first = reserve(service, pin)
    setattr(store, failure, True)
    with pytest.raises(PolicyError, match="SYNTHETIC_LEDGER"):
        settle(service, first.reservation)
    assert store.reservations["school", first.reservation.reservation_id] == first.reservation
    assert len(store.events) == len(store.receipts) == 1


@pytest.mark.parametrize("operation", ["reserve", "settle"])
def test_private_dependency_error_is_never_returned_to_caller(operation):
    service, boundary, _, pin, *_ = accounting_setup()
    first = reserve(service, pin)
    if operation == "reserve":
        boundary.quote_error = True
    else:
        boundary.proof_error = True
    with pytest.raises(PolicyError, match="^AI_POLICY_DEPENDENCY_UNAVAILABLE$"):
        if operation == "reserve":
            reserve(service, pin)
        else:
            settle(service, first.reservation)


@pytest.mark.parametrize("scope", ["organization", "feature"])
def test_wrong_scope_cannot_settle_existing_reservation(scope):
    service, _, store, pin, *_ = accounting_setup()
    first = reserve(service, pin)
    with pytest.raises(PolicyError):
        service.settle(
            "worker",
            "other-school" if scope == "organization" else "school",
            "other-feature" if scope == "feature" else "fixture.feature",
            settle_command(first.reservation),
        )
    assert len(store.events) == 1


def test_native_malformed_commands_rejected_before_authority_or_mutation():
    service, boundary, store, pin, *_ = accounting_setup()
    invalid = reserve_command(pin).model_copy(update={"phase": "exposure"})
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_ACCOUNTING_REQUEST"):
        service.reserve("worker", "school", invalid)
    assert not boundary.quote_calls and not store.reservations
    first = reserve(service, pin)
    invalid = settle_command(first.reservation).model_copy(update={"operation": "unknown"})
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_ACCOUNTING_REQUEST"):
        service.settle("worker", "school", "fixture.feature", invalid)
    assert not boundary.proof_calls and len(store.events) == 1


def test_create_phase_does_not_silently_replace_supplied_old_pin():
    service, _, store, pin, *_ = accounting_setup()
    stale = pin.model_copy(update={"activation_epoch": 2})
    with pytest.raises(PolicyError, match="AI_POLICY_PIN_MISMATCH"):
        reserve(service, stale, phase="create")
    assert not store.reservations


def test_conflicting_settlement_command_same_key_does_not_refund_consumed_usage():
    service, _, store, pin, *_ = accounting_setup()
    first = reserve(service, pin)
    settle(service, first.reservation)
    with pytest.raises(PolicyError, match="AI_POLICY_RESOURCE_RECEIPT_CONFLICT"):
        settle(service, first.reservation, operation="reconcile")
    assert len(store.events) == 2


def test_receipt_for_uncommitted_settlement_fails_closed_and_rolls_back():
    from sketch2life.application.ai_policy_commands import _digest
    from sketch2life.application.ports.ai_policy_ledger import LedgerReceipt

    service, _, store, pin, *_ = accounting_setup()
    first = reserve(service, pin)
    command = settle_command(first.reservation)
    fingerprint = _digest(
        dict(
            operation="consume",
            principal_id="worker",
            organization_id="school",
            feature_scope="fixture.feature",
            command=command.model_dump(mode="json"),
        )
    )
    store.receipts["school", "worker", "settle-one"] = (
        "fixture.feature",
        LedgerReceipt(
            "worker", "settle-one", fingerprint, first.reservation.reservation_id, "consume"
        ),
    )
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_LEDGER_STORAGE"):
        settle(service, first.reservation)
    assert store.reservations["school", first.reservation.reservation_id] == first.reservation
    assert len(store.events) == 1


def test_guard_exit_failure_after_commit_does_not_invent_refund_or_double_allocate():
    service, boundary, store, pin, *_ = accounting_setup()
    boundary.fail_exit = True
    with pytest.raises(PolicyError, match="^AI_POLICY_DEPENDENCY_UNAVAILABLE$"):
        reserve(service, pin)
    # Ledger already committed while guard was held. Outer guard failure cannot
    # be called a SQL rollback/refund; exact retry must inspect durable receipt.
    assert len(store.events) == len(store.reservations) == len(store.receipts) == 1
    boundary.fail_exit = False
    result = reserve(service, pin)
    assert result.replayed and result.snapshot.held_units == 4
    assert len(store.events) == 1


@pytest.mark.parametrize("mode", ["budget", "concurrency"])
def test_current_server_limits_reject_second_attempt_without_partial_ledger_write(mode):
    service, boundary, store, pin, *_ = accounting_setup()
    boundary.quote_changes = (
        {"budget_ceiling": 4}
        if mode == "budget"
        else {
            "concurrency_ceiling": 1,
        }
    )
    first = reserve(service, pin)
    with pytest.raises(
        PolicyError,
        match=(
            "AI_POLICY_BUDGET_EXCEEDED" if mode == "budget" else "AI_POLICY_CONCURRENCY_EXCEEDED"
        ),
    ):
        reserve(service, pin, attempt_id="attempt-two", client_request_id="reserve-two")
    assert store.reservations["school", first.reservation.reservation_id] == first.reservation
    assert len(store.events) == len(store.receipts) == 1


def test_verified_fixture_overrun_is_not_hidden_and_blocks_new_reservation():
    service, boundary, store, pin, *_ = accounting_setup()
    first = reserve(service, pin)
    boundary.proof_changes = {"actual_units": 11}
    result = settle(service, first.reservation)
    assert result.reservation.overrun and result.snapshot.spent_units == 11
    assert not result.reservation.actual_usage_proven
    with pytest.raises(PolicyError, match="AI_POLICY_BUDGET_EXCEEDED"):
        reserve(service, pin, attempt_id="attempt-two", client_request_id="reserve-two")
    assert len(store.events) == 2
