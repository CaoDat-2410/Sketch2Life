"""Prepared actual PG17 ledger cases; NOT_RUN without card-specific opt-in."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from threading import Barrier

import pytest
from alembic.config import Config
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import DBAPIError

from alembic import command
from sketch2life.application.ports.ai_policy_ledger import LedgerEvent, LedgerReceipt
from sketch2life.domain.ai_policy import accounting as domain
from sketch2life.domain.ai_policy.model import PolicyError
from sketch2life.infrastructure.ai_policy.accounting_sql import SqlResourceLedgerStore
from sketch2life.infrastructure.ai_policy.accounting_tables import (
    BUCKET,
    LEDGER_EVENT,
    LEDGER_RECEIPT,
    RESERVATION,
    RESOURCE_SCOPE,
)

NOW = datetime(2026, 10, 17, tzinfo=UTC)
DEFINITION = domain.DefinitionKey("fixture-definition", 1, "a" * 64)
KEY = domain.BudgetKey("school", "fixture.feature", DEFINITION, "fixture-unit", "fixture-window")
TERMS = domain.LimitTerms(KEY, DEFINITION, 8, 2)
BACKEND = Path(__file__).resolve().parents[3]


@pytest.fixture
def ledger_store(policy_engine, monkeypatch):
    monkeypatch.setenv(
        "SKETCH2LIFE_DATABASE_URL", policy_engine.url.render_as_string(hide_password=False)
    )
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "alembic"))
    command.upgrade(config, "ai_policy@head")
    return SqlResourceLedgerStore(policy_engine)


def event(name):
    return LedgerEvent(name, "worker", NOW)


def reserve(tx, name="one", *, terms=TERMS, digest="b" * 64, attempt="attempt"):
    return tx.reserve(
        terms,
        reservation_id=name,
        request_digest=digest,
        attempt_id=attempt,
        estimated_units=4,
        event=event("reserve-" + name),
    )


def receipt(name="one", *, key="receipt-one", operation="reserve"):
    return LedgerReceipt("worker", key, "c" * 64, name, operation)


def proof(reservation, *, actual=3):
    return domain.SettlementProof(
        "fixture-terminal-proof",
        reservation.reservation_id,
        reservation.request_digest,
        reservation.attempt_id,
        reservation.terms.key,
        domain.SettlementOutcome.CONSUME,
        actual,
        domain.AccountingEvidence.FIXTURE,
        True,
    )


def count(store, table):
    with store.engine.connect() as connection:
        return connection.scalar(select(func.count()).select_from(table))


def test_operations_empty_read_does_not_create_ledger_scope_or_bucket(ledger_store):
    from sketch2life.contracts.schemas.ai_policy_operations import PolicyOperationsRequest
    from sketch2life.infrastructure.ai_policy.operations_sql import SqlResourceOperationsReader

    before = count(ledger_store, RESOURCE_SCOPE), count(ledger_store, BUCKET)
    snapshot = SqlResourceOperationsReader(ledger_store.engine).snapshot(
        "school", PolicyOperationsRequest(feature_scope="fixture.feature")
    )
    assert snapshot.occupied_slots is None and not snapshot.bucket_available
    assert snapshot.recorded_spent_units is None
    assert before == (count(ledger_store, RESOURCE_SCOPE), count(ledger_store, BUCKET)) == (0, 0)


def test_operations_reads_fixture_counters_not_actual_cost_and_scope_isolated(ledger_store):
    from sketch2life.contracts.schemas.ai_policy_operations import (
        BudgetWindowRef,
        PolicyOperationsRequest,
    )
    from sketch2life.infrastructure.ai_policy.operations_sql import SqlResourceOperationsReader

    key = TERMS.key
    request = PolicyOperationsRequest(
        feature_scope=key.feature_scope,
        budget_window=BudgetWindowRef(
            definition=dict(
                ref=key.definition.ref, version=key.definition.version, hash=key.definition.hash
            ),
            unit=key.unit,
            window_id=key.window_id,
        ),
    )
    with ledger_store.transaction("school", "fixture.feature") as tx:
        reserved = reserve(tx)
        tx.settle("one", proof(reserved.reservation), event=event("operations-fixture-settle"))
    ledger_store.engine.dispose()
    reader = SqlResourceOperationsReader(ledger_store.engine)
    before = tuple(
        count(ledger_store, table) for table in (RESOURCE_SCOPE, BUCKET, RESERVATION, LEDGER_EVENT)
    )
    snapshot = reader.snapshot("school", request)
    assert snapshot.bucket_available
    assert (
        snapshot.occupied_slots,
        snapshot.recorded_held_units,
        snapshot.recorded_spent_units,
    ) == (0, 0, 3)
    assert reader.snapshot("other-school", request).occupied_slots is None
    wrong_feature = request.model_copy(update={"feature_scope": "other-feature"})
    assert reader.snapshot("school", wrong_feature).recorded_spent_units is None
    wrong_window = request.model_copy(
        update={
            "budget_window": request.budget_window.model_copy(update={"window_id": "other-window"})
        }
    )
    missing = reader.snapshot("school", wrong_window)
    assert missing.occupied_slots == 0 and missing.recorded_spent_units is None
    assert before == tuple(
        count(ledger_store, table) for table in (RESOURCE_SCOPE, BUCKET, RESERVATION, LEDGER_EVENT)
    )


def test_ledger_commit_reconnect_preserves_original_terms_and_terminal_proof(ledger_store):
    store = ledger_store
    with store.transaction("school", "fixture.feature") as tx:
        reserved = reserve(tx)
        tx.add_receipt(receipt())
    store.engine.dispose()
    restarted = SqlResourceLedgerStore(store.engine)
    with restarted.transaction("school", "fixture.feature") as tx:
        assert tx.reservation("one") == reserved.reservation
        assert tx.receipt("worker", "receipt-one") == receipt()
        settled = tx.settle("one", proof(reserved.reservation), event=event("settle-one"))
        tx.add_receipt(receipt(key="settle-one", operation="consume"))
    with restarted.transaction("school", "fixture.feature") as tx:
        assert tx.reservation("one") == settled.reservation
        assert tx.snapshot(TERMS) == domain.LedgerSnapshot(KEY, 0, 3, 0)
        assert not tx.reservation("one").actual_usage_proven
    assert count(store, LEDGER_EVENT) == 2


def test_ledger_exception_rolls_back_counters_reservation_receipt_and_audit(ledger_store):
    with (
        pytest.raises(PolicyError, match="SYNTHETIC_FAILURE"),
        ledger_store.transaction("school", "fixture.feature") as tx,
    ):
        reserve(tx)
        tx.add_receipt(receipt())
        raise PolicyError("SYNTHETIC_FAILURE")
    for table in ACCOUNTING_TABLES:
        assert count(ledger_store, table) == 0


ACCOUNTING_TABLES = (RESOURCE_SCOPE, BUCKET, RESERVATION, LEDGER_RECEIPT, LEDGER_EVENT)


def test_ledger_duplicate_receipt_rolls_back_entire_second_reservation(ledger_store):
    with ledger_store.transaction("school", "fixture.feature") as tx:
        reserve(tx)
        tx.add_receipt(receipt())
    with (
        pytest.raises(PolicyError, match="AI_POLICY_RESOURCE_WRITE_CONFLICT"),
        ledger_store.transaction("school", "fixture.feature") as tx,
    ):
        reserve(tx, "two", attempt="attempt-two")
        tx.add_receipt(receipt("two"))
    with ledger_store.transaction("school", "fixture.feature") as tx:
        assert tx.reservation("two") is None
        assert tx.snapshot(TERMS) == domain.LedgerSnapshot(KEY, 4, 0, 1)
    assert count(ledger_store, LEDGER_EVENT) == 1


@pytest.mark.parametrize("mode", ["budget", "concurrency"])
def test_ledger_concurrent_reserves_have_exactly_one_capacity_winner(ledger_store, mode):
    terms = (
        replace(TERMS, budget_ceiling=4)
        if mode == "budget"
        else replace(TERMS, concurrency_ceiling=1)
    )
    barrier = Barrier(2)

    def contender(name):
        barrier.wait(timeout=10)
        try:
            with ledger_store.transaction("school", "fixture.feature") as tx:
                reserve(tx, name, terms=terms, attempt=name)
                tx.add_receipt(receipt(name, key=name))
            return "committed"
        except PolicyError as exc:
            return str(exc)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(contender, ("one", "two")))
    assert sorted(outcomes) == sorted(
        [
            "committed",
            "AI_POLICY_BUDGET_EXCEEDED" if mode == "budget" else "AI_POLICY_CONCURRENCY_EXCEEDED",
        ]
    )
    assert count(ledger_store, RESERVATION) == count(ledger_store, LEDGER_RECEIPT) == 1
    assert count(ledger_store, LEDGER_EVENT) == 1


def test_ledger_new_window_does_not_reset_global_slots(ledger_store):
    terms = replace(TERMS, concurrency_ceiling=1)
    with ledger_store.transaction("school", "fixture.feature") as tx:
        reserve(tx, terms=terms)
    later = replace(terms, key=replace(KEY, window_id="fixture-next-window"))
    with (
        pytest.raises(PolicyError, match="AI_POLICY_CONCURRENCY_EXCEEDED"),
        ledger_store.transaction("school", "fixture.feature") as tx,
    ):
        reserve(tx, "two", terms=later, attempt="attempt-two")
    assert count(ledger_store, BUCKET) == 1


def test_ledger_same_attempt_cannot_reserve_again_in_another_window(ledger_store):
    with ledger_store.transaction("school", "fixture.feature") as tx:
        reserve(tx)
    later = replace(TERMS, key=replace(KEY, window_id="fixture-next-window"))
    with (
        pytest.raises(PolicyError, match="AI_POLICY_RESERVATION_CONFLICT"),
        ledger_store.transaction("school", "fixture.feature") as tx,
    ):
        reserve(tx, "two", terms=later)
    assert count(ledger_store, RESERVATION) == 1


def test_ledger_live_and_terminal_replay_have_no_counter_or_audit_delta(ledger_store):
    with ledger_store.transaction("school", "fixture.feature") as tx:
        first = reserve(tx)
        assert reserve(tx).replayed
        evidence = proof(first.reservation)
        tx.settle("one", evidence, event=event("settle-one"))
    with ledger_store.transaction("school", "fixture.feature") as tx:
        assert tx.settle("one", evidence, event=event("reconcile-one")).replayed
        assert tx.snapshot(TERMS) == domain.LedgerSnapshot(KEY, 0, 3, 0)
    assert count(ledger_store, LEDGER_EVENT) == 2


def test_ledger_verified_release_frees_original_bucket_and_slot(ledger_store):
    with ledger_store.transaction("school", "fixture.feature") as tx:
        first = reserve(tx)
    evidence = replace(
        proof(first.reservation), outcome=domain.SettlementOutcome.RELEASE, actual_units=0
    )
    with ledger_store.transaction("school", "fixture.feature") as tx:
        tx.settle("one", evidence, event=event("release-one"))
        tx.add_receipt(receipt(key="release-one", operation="release"))
    with ledger_store.transaction("school", "fixture.feature") as tx:
        assert tx.snapshot(TERMS) == domain.LedgerSnapshot(KEY, 0, 0, 0)
        assert tx.reservation("one").state == domain.ReservationState.RELEASED
        later = replace(TERMS, key=replace(KEY, window_id="fixture-next-window"))
        reserve(tx, "two", terms=later, attempt="attempt-two")
        assert tx.snapshot(TERMS) == domain.LedgerSnapshot(KEY, 0, 0, 1)


def test_ledger_failed_settlement_audit_rolls_back_terminal_state_and_counters(ledger_store):
    with ledger_store.transaction("school", "fixture.feature") as tx:
        first = reserve(tx)
    with (
        pytest.raises(PolicyError, match="AI_POLICY_RESOURCE_WRITE_CONFLICT"),
        ledger_store.transaction("school", "fixture.feature") as tx,
    ):
        tx.settle("one", proof(first.reservation), event=event("reserve-one"))
    with ledger_store.transaction("school", "fixture.feature") as tx:
        assert tx.reservation("one") == first.reservation
        assert tx.snapshot(TERMS) == domain.LedgerSnapshot(KEY, 4, 0, 1)
    assert count(ledger_store, LEDGER_EVENT) == 1


def test_ledger_verified_overrun_recorded_truthfully_then_blocks_new_reserve(ledger_store):
    with ledger_store.transaction("school", "fixture.feature") as tx:
        first = reserve(tx)
        result = tx.settle("one", proof(first.reservation, actual=11), event=event("settle-one"))
        assert result.reservation.overrun
    with (
        pytest.raises(PolicyError, match="AI_POLICY_BUDGET_EXCEEDED"),
        ledger_store.transaction("school", "fixture.feature") as tx,
    ):
        reserve(tx, "two", attempt="attempt-two")
    with ledger_store.transaction("school", "fixture.feature") as tx:
        assert tx.snapshot(TERMS).spent_units == 11


@pytest.mark.parametrize("mutation", ["terminal", "delete", "receipt", "event", "bucket"])
def test_ledger_raw_sql_cannot_rewrite_terminal_or_provenance(ledger_store, mutation):
    with ledger_store.transaction("school", "fixture.feature") as tx:
        first = reserve(tx)
        tx.add_receipt(receipt())
        tx.settle("one", proof(first.reservation), event=event("settle-one"))
    statements = {
        "terminal": update(RESERVATION).values(state="reserved"),
        "delete": delete(RESERVATION),
        "receipt": update(LEDGER_RECEIPT).values(fingerprint="d" * 64),
        "event": update(LEDGER_EVENT).values(payload={"tampered": True}),
        "bucket": update(BUCKET).values(key={"tampered": True}),
    }
    with pytest.raises(DBAPIError), ledger_store.engine.begin() as connection:
        connection.execute(statements[mutation])


def test_ledger_wrong_scope_cannot_read_or_settle_other_reservation(ledger_store):
    with ledger_store.transaction("school", "fixture.feature") as tx:
        first = reserve(tx)
    with ledger_store.transaction("other-school", "fixture.feature") as tx:
        assert tx.reservation("one") is None
        with pytest.raises(PolicyError, match="AI_POLICY_RESERVATION_NOT_FOUND"):
            tx.settle("one", proof(first.reservation), event=event("settle-one"))
    with (
        pytest.raises(PolicyError, match="AI_POLICY_ACCOUNTING_SCOPE_MISMATCH"),
        ledger_store.transaction("school", "other-feature") as tx,
    ):
        tx.reservation("one")


def _guarded_service(store):
    # Actual SQL/UoW composition, still ASSUMED owner/registry/evidence boundaries.
    from sketch2life.application.ai_policy_accounting import ResourceAccountingService
    from sketch2life.application.ai_policy_commands import AiPolicyCommands
    from sketch2life.application.ai_policy_use import PolicyUseLeases
    from sketch2life.infrastructure.ai_policy.sql import SqlPolicyStore
    from tests.ai_policy_accounting_fixtures import AssumedAccountingBoundary
    from tests.ai_policy_fixtures import published
    from tests.unit.test_ai_policy_use import AssumedUseBoundary, pin_once

    use = AssumedUseBoundary()
    policy_store = SqlPolicyStore(store.engine)
    published(AiPolicyCommands(policy_store, use, clock=lambda: NOW), policy_store)
    leases = PolicyUseLeases(policy_store, use)
    boundary = AssumedAccountingBoundary()
    return (
        ResourceAccountingService(store, boundary, leases, clock=lambda: NOW),
        pin_once(leases),
        boundary,
        use,
        policy_store,
    )


def test_guarded_accounting_service_actual_sql_reserve_and_settle(ledger_store):
    from sketch2life.contracts.schemas.ai_policy_accounting import (
        ResourceReservationRequest,
        ResourceSettlementRequest,
    )
    from tests.ai_policy_accounting_fixtures import EVIDENCE

    service, pin, _, _, _ = _guarded_service(ledger_store)
    command = ResourceReservationRequest(
        client_request_id="reserve",
        request=pin.request,
        pin=pin,
        attempt_id="attempt",
        phase="dispatch",
    )
    reserved = service.reserve("worker", "school", command)
    assert service.reserve("worker", "school", command).replayed
    result = service.settle(
        "worker",
        "school",
        "fixture.feature",
        ResourceSettlementRequest(
            client_request_id="settle",
            reservation_id=reserved.reservation.reservation_id,
            operation="consume",
            evidence_ref=EVIDENCE,
        ),
    )
    assert result.snapshot.spent_units == 3 and result.snapshot.scope_occupied_slots == 0
    assert not result.reservation.actual_usage_proven
    assert count(ledger_store, LEDGER_RECEIPT) == count(ledger_store, LEDGER_EVENT) == 2


def test_guarded_accounting_sql_stop_blocks_reserve_but_allows_verified_reconcile(ledger_store):
    from sketch2life.application.ai_policy_control import AiPolicyEmergencyStop
    from sketch2life.contracts.schemas.ai_policy_accounting import (
        ResourceReservationRequest,
        ResourceSettlementRequest,
    )
    from sketch2life.contracts.schemas.ai_policy_control import EmergencyStopCommand
    from tests.ai_policy_accounting_fixtures import EVIDENCE

    service, pin, _, use, policy_store = _guarded_service(ledger_store)
    command = ResourceReservationRequest(
        client_request_id="reserve",
        request=pin.request,
        pin=pin,
        attempt_id="attempt",
        phase="dispatch",
    )
    reserved = service.reserve("worker", "school", command)
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
    with pytest.raises(PolicyError):
        service.reserve("worker", "school", command)
    result = service.settle(
        "worker",
        "school",
        "fixture.feature",
        ResourceSettlementRequest(
            client_request_id="reconcile",
            reservation_id=reserved.reservation.reservation_id,
            operation="reconcile",
            evidence_ref=EVIDENCE,
        ),
    )
    assert result.reservation.terms == reserved.reservation.terms
    assert result.snapshot.spent_units == 3 and result.snapshot.scope_occupied_slots == 0
    assert count(ledger_store, LEDGER_EVENT) == 2
