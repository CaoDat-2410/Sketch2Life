"""Prepared actual PG17 inventory cases; no provider/current-owner adapter implied."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest
from alembic.config import Config
from sqlalchemy import delete, func, select, text, update
from sqlalchemy.exc import DBAPIError

from alembic import command
from sketch2life.contracts.schemas.ai_policy import PolicyDefinitionRef
from sketch2life.contracts.schemas.ai_policy_copy import CopyReceiptReference
from sketch2life.contracts.schemas.ai_policy_copy_registry import (
    CopyCoverageObservation,
    CopyRegistryRegistration,
)
from sketch2life.domain.ai_jobs.provider_copy import CopyStatus
from sketch2life.domain.ai_policy.model import PolicyError
from sketch2life.infrastructure.ai_policy.copy_registry_sql import SqlProviderCopyInventoryStore
from sketch2life.infrastructure.ai_policy.copy_registry_tables import (
    COPY_COVERAGE,
    COPY_DELIVERY,
    COPY_DELIVERY_HISTORY,
    COPY_EVENT,
    COPY_EVIDENCE,
    COPY_OPERATION,
    COPY_OPERATION_AUTHORITY,
    COPY_REGISTRATION,
    COPY_SCOPE,
)

BACKEND = Path(__file__).resolve().parents[3]


def registration(copy_id="copy", **changes):
    return CopyRegistryRegistration.model_validate(
        dict(
            organization_id="school",
            scope_ref="scope",
            copy_id=copy_id,
            kind="input",
            original_profile_ref=PolicyDefinitionRef(
                ref="fixture-profile", version=1, hash="a" * 64
            ),
        )
        | changes
    )


def observation(revision):
    return CopyCoverageObservation(
        organization_id="school",
        scope_ref="scope",
        expected_revision=revision,
        registry_revision="fixture-registry",
        attestation_ref=CopyReceiptReference(ref="fixture-coverage", hash="b" * 64),
        required_sources=("fixture-source",),
        observed_sources=("fixture-source",),
    )


@pytest.fixture
def inventory_store(policy_engine, monkeypatch):
    monkeypatch.setenv(
        "SKETCH2LIFE_DATABASE_URL", policy_engine.url.render_as_string(hide_password=False)
    )
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "alembic"))
    command.upgrade(config, "ai_policy@head")
    return SqlProviderCopyInventoryStore(policy_engine)


def transaction(store, *, org="school", scope="scope", write=False):
    return store.transaction(org, scope, principal_id="worker", for_update=write)


def count(store, table):
    with store.engine.connect() as connection:
        return connection.scalar(select(func.count()).select_from(table))


def test_inventory_empty_read_is_unknown_and_does_not_create_scope(inventory_store):
    with transaction(inventory_store) as tx:
        page = tx.page(limit=1)
        assert page.revision == 0 and not page.records and page.coverage_status == "unknown"
    assert count(inventory_store, COPY_SCOPE) == 0


def test_inventory_registration_reconnect_preserves_exact_original_profile(inventory_store):
    with transaction(inventory_store, write=True) as tx:
        original = tx.register(registration())
        assert tx.register(registration()) == original
    inventory_store.engine.dispose()
    restarted = SqlProviderCopyInventoryStore(inventory_store.engine)
    with transaction(restarted) as tx:
        page = tx.page(limit=1)
        assert page.revision == 1 and page.records == (original,) and page.next_after is None
        assert tx.get("copy") == original
        assert page.records[0].initial_copy().status == CopyStatus.DISCOVERED
    assert count(inventory_store, COPY_EVENT) == 1


@pytest.mark.parametrize(
    "change",
    [
        {"kind": "output"},
        {
            "original_profile_ref": PolicyDefinitionRef(
                ref="fixture-profile", version=2, hash="a" * 64
            )
        },
        {
            "original_profile_ref": PolicyDefinitionRef(
                ref="fixture-profile", version=1, hash="c" * 64
            )
        },
    ],
)
def test_inventory_duplicate_cannot_replace_original_provenance(inventory_store, change):
    with transaction(inventory_store, write=True) as tx:
        tx.register(registration())
    with (
        pytest.raises(PolicyError, match="AI_POLICY_COPY_REGISTRATION_CONFLICT"),
        transaction(inventory_store, write=True) as tx,
    ):
        tx.register(registration(**change))
    assert count(inventory_store, COPY_EVENT) == count(inventory_store, COPY_REGISTRATION) == 1


def test_inventory_failure_rolls_back_registration_scope_and_event(inventory_store):
    with (
        pytest.raises(PolicyError, match="SYNTHETIC_FAILURE"),
        transaction(inventory_store, write=True) as tx,
    ):
        tx.register(registration())
        tx.mark_purging()
        raise PolicyError("SYNTHETIC_FAILURE")
    for table in (COPY_SCOPE, COPY_REGISTRATION, COPY_EVENT, COPY_EVIDENCE):
        assert count(inventory_store, table) == 0


def record_guarded_registration(store):
    from sketch2life.application.ai_policy_copy_inventory import ProviderCopyInventoryService
    from tests.ai_policy_copy_inventory_fixtures import SOURCE, AssumedInventoryBoundary, context
    from tests.unit.test_ai_policy_domain import NOW

    service = ProviderCopyInventoryService(store, AssumedInventoryBoundary(), clock=lambda: NOW)
    service.register("operator", "school", context(), registration(), SOURCE)
    return service


def test_inventory_evidence_reconnect_and_retry_preserve_original_proof(inventory_store):
    from sketch2life.infrastructure.ai_policy.copy_registry_sql import decode_inventory_evidence
    from tests.ai_policy_copy_inventory_fixtures import SOURCE, context

    service = record_guarded_registration(inventory_store)
    inventory_store.engine.dispose()
    with inventory_store.engine.connect() as connection:
        original = decode_inventory_evidence(
            connection.execute(select(COPY_EVIDENCE)).mappings().one()
        )
    assert original.source.reference == SOURCE
    assert original.registration == registration()
    service.register("operator", "school", context(), registration(), SOURCE)
    assert count(inventory_store, COPY_EVIDENCE) == 2
    assert count(inventory_store, COPY_EVENT) == 1
    with transaction(inventory_store) as tx:
        assert tx.page(limit=1).revision == 1


@pytest.mark.parametrize("mutation", ["update", "delete"])
def test_inventory_evidence_is_immutable_even_through_raw_sql(inventory_store, mutation):
    record_guarded_registration(inventory_store)
    statement = (
        update(COPY_EVIDENCE).values(record={}) if mutation == "update" else delete(COPY_EVIDENCE)
    )
    with pytest.raises(DBAPIError), inventory_store.engine.begin() as connection:
        connection.execute(statement)
    assert count(inventory_store, COPY_EVIDENCE) == 1


def test_inventory_evidence_insert_failure_rolls_back_registration_and_event(inventory_store):
    with inventory_store.engine.begin() as connection:
        connection.execute(
            text("""
          CREATE FUNCTION ai_policy.synthetic_evidence_failure() RETURNS trigger
          LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'SYNTHETIC_EVIDENCE_FAILURE'; END; $$
        """)
        )
        connection.execute(
            text("""
          CREATE TRIGGER synthetic_evidence_failure BEFORE INSERT
          ON ai_policy.copy_inventory_evidence FOR EACH ROW
          EXECUTE FUNCTION ai_policy.synthetic_evidence_failure()
        """)
        )
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_REGISTRY_STORAGE_UNAVAILABLE"):
        record_guarded_registration(inventory_store)
    for table in (COPY_SCOPE, COPY_REGISTRATION, COPY_EVENT, COPY_EVIDENCE):
        assert count(inventory_store, table) == 0


def test_inventory_evidence_forward_branch_roundtrip_preserves_inventory(
    inventory_store, monkeypatch
):
    record_guarded_registration(inventory_store)
    monkeypatch.setenv(
        "SKETCH2LIFE_DATABASE_URL", inventory_store.engine.url.render_as_string(hide_password=False)
    )
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "alembic"))
    command.downgrade(config, "20261017_ap_0004")
    assert count(inventory_store, COPY_REGISTRATION) == 1
    command.upgrade(config, "ai_policy@head")
    assert count(inventory_store, COPY_EVIDENCE) == 0
    record_guarded_registration(inventory_store)
    assert count(inventory_store, COPY_EVIDENCE) == 1
    assert count(inventory_store, COPY_EVENT) == 1


def operation_service(store):
    from sketch2life.application.ai_policy_copy_operations import ProviderCopyOperationService
    from tests.ai_policy_copy_inventory_fixtures import AssumedInventoryBoundary
    from tests.ai_policy_copy_operation_fixtures import AssumedOperationBoundary
    from tests.unit.test_ai_policy_domain import NOW

    boundary = AssumedOperationBoundary(AssumedInventoryBoundary())
    return ProviderCopyOperationService(store, boundary, clock=lambda: NOW), boundary


def scheduled_delivery(store):
    from tests.ai_policy_copy_operation_fixtures import schedule
    from tests.unit.test_ai_policy_domain import NOW

    store.clock = lambda: NOW
    record_guarded_registration(store)
    service, _ = operation_service(store)
    return schedule(service)


def test_delivery_claim_reconnect_finish_and_replay_are_atomic_metadata(inventory_store):
    from datetime import timedelta

    from sketch2life.domain.ai_policy.copy_delivery import DeliveryResponse, HookOutcome
    from tests.unit.test_ai_policy_domain import NOW

    op = scheduled_delivery(inventory_store)
    with transaction(inventory_store, write=True) as tx:
        claimed = tx.claim_delivery(
            op.operation_key,
            expected_revision=0,
            token="worker-1",
            expires_at=NOW + timedelta(minutes=1),
        )
    inventory_store.engine.dispose()
    with transaction(inventory_store) as tx:
        assert tx.get_delivery(op.operation_key) == claimed
    response = DeliveryResponse(
        op.operation_key, op.binding_digest, HookOutcome.PENDING, reason_code="WAITING"
    )
    with transaction(inventory_store, write=True) as tx:
        done = tx.finish_delivery(response, expected_revision=1, token="worker-1")
    assert count(inventory_store, COPY_DELIVERY_HISTORY) == 2
    with transaction(inventory_store, write=True) as tx:
        assert tx.finish_delivery(response, expected_revision=1, token="worker-1") == done
    assert count(inventory_store, COPY_DELIVERY_HISTORY) == 2


def test_delivery_concurrent_claims_admit_one_revision_winner(inventory_store):
    from datetime import timedelta

    from tests.unit.test_ai_policy_domain import NOW

    op = scheduled_delivery(inventory_store)
    barrier = Barrier(2)

    def attempt(token):
        barrier.wait(timeout=10)
        try:
            with transaction(inventory_store, write=True) as tx:
                tx.claim_delivery(
                    op.operation_key,
                    expected_revision=0,
                    token=token,
                    expires_at=NOW + timedelta(minutes=1),
                )
            return "won"
        except PolicyError as error:
            assert str(error) == "AI_POLICY_COPY_DELIVERY_STALE"
            return "lost"

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(attempt, token) for token in ("worker-1", "worker-2")]
        assert sorted(f.result(timeout=30) for f in futures) == ["lost", "won"]
    assert count(inventory_store, COPY_DELIVERY) == 1
    assert count(inventory_store, COPY_DELIVERY_HISTORY) == 1


def test_delivery_expired_takeover_rejects_old_response_without_duplicate_operation(
    inventory_store,
):
    from datetime import timedelta

    from sketch2life.domain.ai_policy.copy_delivery import DeliveryResponse, HookOutcome
    from tests.unit.test_ai_policy_domain import NOW

    op = scheduled_delivery(inventory_store)
    with transaction(inventory_store, write=True) as tx:
        tx.claim_delivery(
            op.operation_key,
            expected_revision=0,
            token="worker-1",
            expires_at=NOW + timedelta(seconds=1),
        )
    inventory_store.clock = lambda: NOW + timedelta(seconds=1)
    with transaction(inventory_store, write=True) as tx:
        tx.claim_delivery(
            op.operation_key,
            expected_revision=1,
            token="worker-2",
            expires_at=NOW + timedelta(minutes=1),
        )
    response = DeliveryResponse(
        op.operation_key, op.binding_digest, HookOutcome.PENDING, reason_code="WAITING"
    )
    with (
        pytest.raises(PolicyError, match="AI_POLICY_COPY_DELIVERY_STALE"),
        transaction(inventory_store, write=True) as tx,
    ):
        tx.finish_delivery(response, expected_revision=1, token="worker-1")
    with transaction(inventory_store, write=True) as tx:
        tx.finish_delivery(response, expected_revision=2, token="worker-2")
    assert count(inventory_store, COPY_OPERATION) == 1
    assert count(inventory_store, COPY_DELIVERY_HISTORY) == 3


def test_delivery_history_failure_rolls_back_claim_current_state_and_event(inventory_store):
    from datetime import timedelta

    from tests.unit.test_ai_policy_domain import NOW

    op = scheduled_delivery(inventory_store)
    before = count(inventory_store, COPY_EVENT)
    with inventory_store.engine.begin() as connection:
        connection.execute(
            text("""
          CREATE FUNCTION ai_policy.synthetic_delivery_failure() RETURNS trigger
          LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'SYNTHETIC_DELIVERY_FAILURE'; END; $$
        """)
        )
        connection.execute(
            text("""
          CREATE TRIGGER synthetic_delivery_failure BEFORE INSERT
          ON ai_policy.copy_delivery_history FOR EACH ROW
          EXECUTE FUNCTION ai_policy.synthetic_delivery_failure()
        """)
        )
    with (
        pytest.raises(PolicyError, match="AI_POLICY_COPY_REGISTRY_STORAGE_UNAVAILABLE"),
        transaction(inventory_store, write=True) as tx,
    ):
        tx.claim_delivery(
            op.operation_key,
            expected_revision=0,
            token="worker-1",
            expires_at=NOW + timedelta(minutes=1),
        )
    assert count(inventory_store, COPY_DELIVERY) == 0
    assert count(inventory_store, COPY_DELIVERY_HISTORY) == 0
    assert count(inventory_store, COPY_EVENT) == before


@pytest.mark.parametrize("mutation", ["update", "delete"])
def test_delivery_history_cannot_be_rewritten_by_raw_sql(inventory_store, mutation):
    from datetime import timedelta

    from tests.unit.test_ai_policy_domain import NOW

    op = scheduled_delivery(inventory_store)
    with transaction(inventory_store, write=True) as tx:
        tx.claim_delivery(
            op.operation_key,
            expected_revision=0,
            token="worker-1",
            expires_at=NOW + timedelta(minutes=1),
        )
    statement = (
        update(COPY_DELIVERY_HISTORY).values(snapshot={})
        if mutation == "update"
        else delete(COPY_DELIVERY_HISTORY)
    )
    with pytest.raises(DBAPIError), inventory_store.engine.begin() as connection:
        connection.execute(statement)
    assert count(inventory_store, COPY_DELIVERY_HISTORY) == 1


def test_copy_operation_pages_reconnect_scope_and_revision_cursor(inventory_store):
    from tests.ai_policy_copy_operation_fixtures import schedule

    record_guarded_registration(inventory_store)
    service, _ = operation_service(inventory_store)
    keys = sorted(
        schedule(service, client_request_id=f"fixture-{i}").operation_key for i in range(3)
    )
    inventory_store.engine.dispose()
    with transaction(inventory_store) as tx:
        first = tx.operation_page(limit=2)
        assert first.operation_keys == tuple(keys[:2]) and first.next_after == keys[1]
        last = tx.operation_page(limit=2, after=first.next_after, expected_revision=first.revision)
        assert last.operation_keys == (keys[2],) and last.next_after is None
    for values in ({"org": "other"}, {"scope": "other"}):
        with transaction(inventory_store, **values) as tx:
            empty = tx.operation_page(limit=2)
            assert empty.revision == 0 and not empty.operation_keys
    schedule(service, client_request_id="fixture-new")
    with (
        transaction(inventory_store) as tx,
        pytest.raises(PolicyError, match="AI_POLICY_COPY_REGISTRY_STALE"),
    ):
        tx.operation_page(limit=2, after=first.next_after, expected_revision=first.revision)


def test_copy_operation_page_missing_scope_does_not_mix_later_intent(inventory_store):
    from tests.ai_policy_copy_operation_fixtures import schedule

    with transaction(inventory_store) as reader:
        record_guarded_registration(inventory_store)
        service, _ = operation_service(inventory_store)
        schedule(service)
        page = reader.operation_page(limit=1)
        assert page.revision == 0 and not page.operation_keys
    with transaction(inventory_store) as reader:
        assert len(reader.operation_page(limit=1).operation_keys) == 1


def test_copy_operation_reconnect_replay_and_scope_isolation(inventory_store):
    from tests.ai_policy_copy_operation_fixtures import schedule

    record_guarded_registration(inventory_store)
    service, _ = operation_service(inventory_store)
    original = schedule(service)
    inventory_store.engine.dispose()
    with transaction(inventory_store) as tx:
        assert tx.get_operation(original.operation_key) == original
        revision = tx.page(limit=1).revision
        assert tx.page(limit=1).scope_purging
    assert schedule(service) == original
    assert count(inventory_store, COPY_OPERATION) == 1
    assert count(inventory_store, COPY_OPERATION_AUTHORITY) == 2
    with transaction(inventory_store) as tx:
        assert tx.page(limit=1).revision == revision
    for values in ({"org": "other-school"}, {"scope": "other-scope"}):
        with transaction(inventory_store, **values) as tx:
            assert tx.get_operation(original.operation_key) is None


@pytest.mark.parametrize(
    "table,mutation",
    [
        (COPY_OPERATION, "update"),
        (COPY_OPERATION, "delete"),
        (COPY_OPERATION_AUTHORITY, "update"),
        (COPY_OPERATION_AUTHORITY, "delete"),
    ],
    ids=["envelope-update", "envelope-delete", "authority-update", "authority-delete"],
)
def test_copy_operation_raw_sql_history_is_immutable(inventory_store, table, mutation):
    from tests.ai_policy_copy_operation_fixtures import schedule

    record_guarded_registration(inventory_store)
    service, _ = operation_service(inventory_store)
    schedule(service)
    payload = "envelope" if table is COPY_OPERATION else "observation"
    statement = update(table).values(**{payload: {}}) if mutation == "update" else delete(table)
    with pytest.raises(DBAPIError), inventory_store.engine.begin() as connection:
        connection.execute(statement)
    assert count(inventory_store, table) == 1


def test_copy_operation_authority_insert_failure_rolls_back_intent_fence_and_event(inventory_store):
    from tests.ai_policy_copy_operation_fixtures import schedule

    record_guarded_registration(inventory_store)
    with inventory_store.engine.begin() as connection:
        connection.execute(
            text("""
          CREATE FUNCTION ai_policy.synthetic_operation_failure() RETURNS trigger
          LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'SYNTHETIC_OPERATION_FAILURE'; END; $$
        """)
        )
        connection.execute(
            text("""
          CREATE TRIGGER synthetic_operation_failure BEFORE INSERT
          ON ai_policy.copy_operation_authority FOR EACH ROW
          EXECUTE FUNCTION ai_policy.synthetic_operation_failure()
        """)
        )
    service, _ = operation_service(inventory_store)
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_REGISTRY_STORAGE_UNAVAILABLE"):
        schedule(service)
    assert count(inventory_store, COPY_OPERATION) == 0
    assert count(inventory_store, COPY_OPERATION_AUTHORITY) == 0
    assert count(inventory_store, COPY_EVENT) == 1
    with transaction(inventory_store) as tx:
        assert not tx.page(limit=1).scope_purging and tx.page(limit=1).revision == 1


def test_copy_operation_concurrent_duplicate_has_one_intent_and_queued_event(inventory_store):
    from tests.ai_policy_copy_operation_fixtures import schedule

    record_guarded_registration(inventory_store)
    barrier = Barrier(2)

    def submit():
        service, _ = operation_service(inventory_store)
        barrier.wait(timeout=10)
        return schedule(service)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = [
            future.result(timeout=30) for future in (pool.submit(submit), pool.submit(submit))
        ]
    assert first == second
    assert count(inventory_store, COPY_OPERATION) == 1
    assert count(inventory_store, COPY_OPERATION_AUTHORITY) == 2
    # register, purge fence and exactly one queued event.
    assert count(inventory_store, COPY_EVENT) == 3


def test_copy_operation_final_owner_denial_rolls_back_all_new_writes(inventory_store):
    from tests.ai_policy_copy_operation_fixtures import schedule

    record_guarded_registration(inventory_store)
    service, boundary = operation_service(inventory_store)
    original, calls = boundary.authorize, []

    def revoke(command, digest):
        calls.append(digest)
        grant = original(command, digest)
        return grant.model_copy(update={"allowed": False}) if len(calls) == 3 else grant

    boundary.authorize = revoke
    with pytest.raises(PolicyError, match="AI_POLICY_FORBIDDEN"):
        schedule(service)
    assert count(inventory_store, COPY_OPERATION) == 0
    assert count(inventory_store, COPY_OPERATION_AUTHORITY) == 0
    with transaction(inventory_store) as tx:
        assert not tx.page(limit=1).scope_purging and tx.page(limit=1).revision == 1


def test_inventory_keyset_pages_stable_revision_and_reject_intervening_registration(
    inventory_store,
):
    with transaction(inventory_store, write=True) as tx:
        for name in ("c", "a", "b"):
            tx.register(registration(name))
    with transaction(inventory_store) as tx:
        first = tx.page(limit=2)
        assert tuple(item.registration.copy_id for item in first.records) == ("a", "b")
    with transaction(inventory_store) as tx:
        second = tx.page(limit=2, after=first.next_after, expected_revision=first.revision)
        assert tuple(item.registration.copy_id for item in second.records) == ("c",)
        assert second.next_after is None
    with transaction(inventory_store, write=True) as tx:
        tx.register(registration("d"))
    with (
        pytest.raises(PolicyError, match="AI_POLICY_COPY_REGISTRY_STALE"),
        transaction(inventory_store) as tx,
    ):
        tx.page(limit=2, after=first.next_after, expected_revision=first.revision)


def test_inventory_coverage_report_invalidated_by_new_registration(inventory_store):
    with transaction(inventory_store, write=True) as tx:
        tx.register(registration())
        tx.record_coverage(observation(1))
    with transaction(inventory_store) as tx:
        report = tx.page(limit=1)
        assert report.revision == 2 and report.coverage_status == "reported_complete"
        assert not report.records[0].initial_copy().actual_deletion_proven
    with transaction(inventory_store, write=True) as tx:
        tx.register(registration("late"))
    with transaction(inventory_store) as tx:
        assert tx.page(limit=2).coverage_status == "unknown"
    assert count(inventory_store, COPY_COVERAGE) == 1


def test_inventory_stale_coverage_cas_has_no_partial_audit(inventory_store):
    with transaction(inventory_store, write=True) as tx:
        tx.register(registration())
    with (
        pytest.raises(PolicyError, match="AI_POLICY_COPY_REGISTRY_STALE"),
        transaction(inventory_store, write=True) as tx,
    ):
        tx.record_coverage(observation(0))
    assert count(inventory_store, COPY_EVENT) == 1
    assert count(inventory_store, COPY_COVERAGE) == 0


def test_inventory_other_scope_coverage_cannot_be_reused_at_same_revision(inventory_store):
    with (
        pytest.raises(PolicyError, match="AI_POLICY_COPY_SCOPE_MISMATCH"),
        transaction(inventory_store, write=True) as tx,
    ):
        tx.record_coverage(observation(0).model_copy(update={"scope_ref": "other"}))
    assert count(inventory_store, COPY_COVERAGE) == count(inventory_store, COPY_EVENT) == 0


def test_inventory_registration_racing_purge_is_fenced_and_later_copy_quarantined(inventory_store):
    barrier = Barrier(2)

    def contender(mode):
        barrier.wait(timeout=10)
        with transaction(inventory_store, write=True) as tx:
            return tx.mark_purging() if mode == "purge" else tx.register(registration())

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(contender, ("purge", "register")))
    with transaction(inventory_store, write=True) as tx:
        before = tx.page(limit=2)
        assert before.scope_purging
        assert tx.mark_purging() == before.revision
        late = tx.register(registration("late"))
        assert late.initially_quarantined
        assert late.initial_copy().status == CopyStatus.PURGE_REQUESTED
    assert count(inventory_store, COPY_EVENT) == 3


def test_inventory_concurrent_duplicate_register_has_one_audit_event(inventory_store):
    barrier = Barrier(2)

    def contender(_):
        barrier.wait(timeout=10)
        with transaction(inventory_store, write=True) as tx:
            return tx.register(registration())

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(contender, range(2)))
    assert outcomes[0] == outcomes[1]
    assert count(inventory_store, COPY_EVENT) == count(inventory_store, COPY_REGISTRATION) == 1


@pytest.mark.parametrize("mutation", ["profile", "quarantine", "coverage", "event", "unpurge"])
def test_inventory_raw_sql_cannot_rewrite_originals_or_unpurge_scope(inventory_store, mutation):
    with transaction(inventory_store, write=True) as tx:
        tx.mark_purging()
        tx.register(registration())
        tx.record_coverage(observation(2))
    statements = {
        "profile": update(COPY_REGISTRATION).values(original_profile_ref={"tampered": True}),
        "quarantine": update(COPY_REGISTRATION).values(initially_quarantined=False),
        "coverage": update(COPY_COVERAGE).values(observation={"tampered": True}),
        "event": update(COPY_EVENT).values(payload={"tampered": True}),
        "unpurge": update(COPY_SCOPE).values(purging=False, revision=COPY_SCOPE.c.revision + 1),
    }
    with pytest.raises(DBAPIError), inventory_store.engine.begin() as connection:
        connection.execute(statements[mutation])


def test_inventory_scope_isolation_and_read_only_mutation_denial(inventory_store):
    with transaction(inventory_store, write=True) as tx:
        tx.register(registration())
    for values in ({"org": "other-school"}, {"scope": "other-scope"}):
        with transaction(inventory_store, **values) as tx:
            assert not tx.page(limit=2).records
            assert tx.get("copy") is None
    with (
        pytest.raises(PolicyError, match="AI_POLICY_COPY_REGISTRY_READ_ONLY"),
        transaction(inventory_store) as tx,
    ):
        tx.mark_purging()
    with (
        pytest.raises(PolicyError, match="AI_POLICY_COPY_SCOPE_MISMATCH"),
        transaction(inventory_store, write=True) as tx,
    ):
        tx.register(registration(scope_ref="other-scope"))


def test_inventory_missing_scope_reader_does_not_mix_later_insert_into_revision_zero(
    inventory_store,
):
    with transaction(inventory_store) as reader:
        with transaction(inventory_store, write=True) as writer:
            writer.register(registration())
        page = reader.page(limit=1)
        assert page.revision == 0 and not page.records and page.coverage_status == "unknown"
    with transaction(inventory_store) as reader:
        assert reader.page(limit=1).revision == 1 and len(reader.page(limit=1).records) == 1


def test_guarded_inventory_service_sql_source_coverage_and_late_fence(inventory_store):
    from sketch2life.application.ai_policy_copy_inventory import ProviderCopyInventoryService
    from tests.ai_policy_copy_inventory_fixtures import (
        COVERAGE,
        SOURCE,
        AssumedInventoryBoundary,
        context,
        read_request,
    )
    from tests.unit.test_ai_policy_domain import NOW

    service = ProviderCopyInventoryService(
        inventory_store, AssumedInventoryBoundary(), clock=lambda: NOW
    )
    original = service.register("operator", "school", context(), registration(), SOURCE)
    service.coverage("operator", "school", context(), expected_revision=1, reference=COVERAGE)
    assert service.page("operator", "school", read_request()).coverage_status == "reported_complete"
    assert not original.initial_copy().actual_deletion_proven
    assert service.fence("operator", "school", context()) == 3
    late = service.register("operator", "school", context(), registration("late"), SOURCE)
    assert late.initially_quarantined
    assert service.page("operator", "school", read_request()).coverage_status == "unknown"
    assert count(inventory_store, COPY_EVENT) == 4


def test_guarded_inventory_service_sql_revocation_before_commit_rolls_back(inventory_store):
    from sketch2life.application.ai_policy_copy_inventory import ProviderCopyInventoryService
    from tests.ai_policy_copy_inventory_fixtures import SOURCE, AssumedInventoryBoundary, context
    from tests.unit.test_ai_policy_domain import NOW

    boundary = AssumedInventoryBoundary()
    authorize, calls = boundary.authorize, []

    def current_owner(ctx, action, digest):
        calls.append(action)
        grant = authorize(ctx, action, digest)
        return grant.model_copy(update={"allowed": False}) if len(calls) == 2 else grant

    boundary.authorize = current_owner
    service = ProviderCopyInventoryService(inventory_store, boundary, clock=lambda: NOW)
    with pytest.raises(PolicyError, match="AI_POLICY_FORBIDDEN"):
        service.register("operator", "school", context(), registration(), SOURCE)
    for table in (COPY_SCOPE, COPY_REGISTRATION, COPY_EVENT):
        assert count(inventory_store, table) == 0
