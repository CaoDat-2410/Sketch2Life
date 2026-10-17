"""C3b real SQL cases prepared, NOT_RUN until approved BE2-14 PG17 profile exists."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest
from alembic.config import Config
from sqlalchemy import func, select

from alembic import command
from sketch2life.application.ai_policy_commands import AiPolicyCommands
from sketch2life.domain.ai_policy.model import PolicyError
from sketch2life.infrastructure.ai_policy.activation_tables import SCOPE, SCOPE_EVENT
from sketch2life.infrastructure.ai_policy.sql import SqlPolicyStore, SqlPolicyTransaction
from sketch2life.infrastructure.ai_policy.tables import RECEIPT
from tests.ai_policy_fixtures import AssumedCommandBoundary, execute, published, reviewed
from tests.unit.test_ai_policy_domain import NOW

BACKEND = Path(__file__).resolve().parents[3]


@pytest.fixture
def activation_harness(policy_engine, monkeypatch):
    monkeypatch.setenv(
        "SKETCH2LIFE_DATABASE_URL", policy_engine.url.render_as_string(hide_password=False)
    )
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "alembic"))
    command.upgrade(config, "ai_policy@head")
    store = SqlPolicyStore(policy_engine)
    boundary = AssumedCommandBoundary()
    return AiPolicyCommands(store, boundary, clock=lambda: NOW), boundary, store


def test_actual_commands_publish_disable_and_restart_effective_pin(activation_harness):
    service, boundary, store = activation_harness
    result = published(service, store)
    with store.engine.connect() as connection:
        scope = connection.execute(select(SCOPE)).mappings().one()
        assert scope["epoch"] == 1 and scope["record_id"] == result.record.record_id
        assert connection.scalar(select(func.count()).select_from(SCOPE_EVENT)) == 1
    store.engine.dispose()
    restarted = AiPolicyCommands(SqlPolicyStore(store.engine), boundary, clock=lambda: NOW)
    retired = execute(restarted, "operator", "recall", "retire", result.record, reason="synthetic")
    assert retired.record.state == "recalled"
    with store.engine.connect() as connection:
        scope = connection.execute(select(SCOPE)).mappings().one()
        assert scope["disabled"] and scope["epoch"] == 2
        intents = connection.execute(select(SCOPE_EVENT)).mappings().all()
        assert len(intents) == 2 and all(row["delivered_at"] is None for row in intents)
        assert connection.scalar(select(func.count()).select_from(RECEIPT)) == 6


def test_actual_scope_and_lifecycle_rollback_if_receipt_insert_fails(
    activation_harness, monkeypatch
):
    from tests.ai_policy_fixtures import publish

    service, _, store = activation_harness
    record = reviewed(service, store).record

    def fail(self, receipt):
        raise PolicyError("SYNTHETIC_RECEIPT_FAILURE")

    monkeypatch.setattr(SqlPolicyTransaction, "add_receipt", fail)
    with pytest.raises(PolicyError, match="SYNTHETIC_RECEIPT_FAILURE"):
        publish(service, store, record, "failing-publish")
    with store.transaction() as tx:
        assert tx.load("school", record.record_id).state == "submitted"
        scope = tx.effective_scope("school", "fixture.feature")
        assert scope.epoch == 0 and scope.record_id is None
    with store.engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(SCOPE_EVENT)) == 0


def test_concurrent_publications_serialize_to_one_effective_pin(activation_harness):
    from tests.ai_policy_fixtures import publish

    service, _, store = activation_harness
    first = reviewed(service, store, "first").record
    second = reviewed(service, store, "second").record
    barrier = Barrier(2)

    def run(record):
        local = AiPolicyCommands(store, AssumedCommandBoundary(), clock=lambda: NOW)
        barrier.wait(timeout=15)
        return publish(local, store, record, record.record_id + "-publish")

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run, (first, second)))
    with store.engine.connect() as connection:
        scope = connection.execute(select(SCOPE)).mappings().one()
        assert scope["epoch"] == 2 and not scope["disabled"]
        assert scope["record_id"] in {item.record.record_id for item in results}
        assert connection.scalar(select(func.count()).select_from(SCOPE_EVENT)) == 2


def test_recall_of_old_pin_racing_replacement_does_not_disable_new_pin(activation_harness):
    from tests.ai_policy_fixtures import publish

    service, _, store = activation_harness
    old = published(service, store, "old").record
    new = reviewed(service, store, "replacement").record
    barrier = Barrier(2)

    def retire():
        local = AiPolicyCommands(store, AssumedCommandBoundary(), clock=lambda: NOW)
        barrier.wait(timeout=15)
        return execute(local, "operator", "recall", "recall-old", old, reason="synthetic")

    def activate():
        local = AiPolicyCommands(store, AssumedCommandBoundary(), clock=lambda: NOW)
        barrier.wait(timeout=15)
        return publish(local, store, new, "publish-replacement")

    with ThreadPoolExecutor(max_workers=2) as pool:
        pending = [pool.submit(retire), pool.submit(activate)]
        assert {item.result(timeout=30).record.state for item in pending} == {
            "recalled",
            "published",
        }
    with store.engine.connect() as connection:
        scope = connection.execute(select(SCOPE)).mappings().one()
        assert scope["record_id"] == new.record_id and not scope["disabled"]
        assert scope["epoch"] in {2, 3}


def test_emergency_stop_before_publication_is_durable_and_idempotent(activation_harness):
    from sketch2life.application.ai_policy_control import AiPolicyEmergencyStop
    from sketch2life.contracts.schemas.ai_policy_control import EmergencyStopCommand

    _, boundary, store = activation_harness
    stop = AiPolicyEmergencyStop(store, boundary, clock=lambda: NOW)
    cmd = EmergencyStopCommand(
        client_request_id="stop",
        feature_scope="fixture.feature",
        expected_epoch=0,
        reason="synthetic emergency",
    )
    first = stop.execute("operator", "school", cmd)
    store.engine.dispose()
    replay = AiPolicyEmergencyStop(
        SqlPolicyStore(store.engine), boundary, clock=lambda: NOW
    ).execute("operator", "school", cmd)
    assert first.epoch == 1 and first.record_id is None and replay.replayed
    with store.engine.connect() as connection:
        scope = connection.execute(select(SCOPE)).mappings().one()
        assert scope["disabled"] and scope["record_id"] is None
        assert connection.scalar(select(func.count()).select_from(SCOPE_EVENT)) == 1
        assert connection.scalar(select(func.count()).select_from(RECEIPT)) == 1


def test_emergency_stop_sql_failure_rolls_back_scope_and_intent(activation_harness, monkeypatch):
    from sketch2life.application.ai_policy_control import AiPolicyEmergencyStop
    from sketch2life.contracts.schemas.ai_policy_control import EmergencyStopCommand

    _, boundary, store = activation_harness

    def fail(self, receipt):
        raise PolicyError("SYNTHETIC_RECEIPT_FAILURE")

    monkeypatch.setattr(SqlPolicyTransaction, "add_receipt", fail)
    with pytest.raises(PolicyError, match="SYNTHETIC_RECEIPT_FAILURE"):
        AiPolicyEmergencyStop(store, boundary, clock=lambda: NOW).execute(
            "operator",
            "school",
            EmergencyStopCommand(
                client_request_id="stop",
                feature_scope="fixture.feature",
                expected_epoch=0,
                reason="synthetic emergency",
            ),
        )
    with store.engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(SCOPE)) == 0
        assert connection.scalar(select(func.count()).select_from(SCOPE_EVENT)) == 0
        assert connection.scalar(select(func.count()).select_from(RECEIPT)) == 0


def test_old_epoch_emergency_stop_cannot_disable_racing_replacement(activation_harness):
    from sketch2life.application.ai_policy_control import AiPolicyEmergencyStop
    from sketch2life.contracts.schemas.ai_policy_control import EmergencyStopCommand
    from tests.ai_policy_fixtures import publish

    service, _, store = activation_harness
    published(service, store, "old-stop-pin")
    replacement = reviewed(service, store, "new-stop-pin").record
    barrier = Barrier(2)

    def activate():
        local = AiPolicyCommands(store, AssumedCommandBoundary(), clock=lambda: NOW)
        barrier.wait(timeout=15)
        return publish(local, store, replacement, "replacement-publish")

    def stop():
        local = AiPolicyEmergencyStop(store, AssumedCommandBoundary(), clock=lambda: NOW)
        barrier.wait(timeout=15)
        try:
            return local.execute(
                "operator",
                "school",
                EmergencyStopCommand(
                    client_request_id="stop-old-epoch",
                    feature_scope="fixture.feature",
                    expected_epoch=1,
                    reason="synthetic emergency",
                ),
            )
        except PolicyError as error:
            assert str(error) == "AI_POLICY_STALE_SCOPE"
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        activation, stopping = pool.submit(activate), pool.submit(stop)
        assert activation.result(timeout=30).record.state == "published"
        stopping.result(timeout=30)
    with store.engine.connect() as connection:
        scope = connection.execute(select(SCOPE)).mappings().one()
        assert scope["record_id"] == replacement.record_id and not scope["disabled"]
        assert scope["epoch"] in {2, 3}


def test_current_use_sql_keeps_prior_pin_across_ordinary_replacement(activation_harness):
    from sketch2life.application.ai_policy_use import PolicyUseLeases
    from tests.unit.test_ai_policy_use import AssumedUseBoundary, request

    service, _, store = activation_harness
    old = published(service, store, "use-old").record
    leases = PolicyUseLeases(store, AssumedUseBoundary())
    with leases.begin("worker", "school", request()) as initial:
        pin = initial.pin
    new = published(service, store, "use-new").record
    with leases.continue_use("worker", "school", request(), pin, "completion") as result:
        assert result.pin.policy_ref.ref == old.record_id
        assert result.current_scope_epoch == 2 and result.pin.activation_epoch == 1
    with leases.begin("worker", "school", request()) as latest:
        assert latest.pin.policy_ref.ref == new.record_id


def test_current_use_sql_stop_history_cannot_be_bypassed_after_reactivation(activation_harness):
    from sketch2life.application.ai_policy_control import AiPolicyEmergencyStop
    from sketch2life.application.ai_policy_use import PolicyUseLeases
    from sketch2life.contracts.schemas.ai_policy_control import EmergencyStopCommand
    from tests.unit.test_ai_policy_use import AssumedUseBoundary, request

    service, _, store = activation_harness
    published(service, store, "use-stop-old")
    leases = PolicyUseLeases(store, AssumedUseBoundary())
    with leases.begin("worker", "school", request()) as initial:
        pin = initial.pin
    AiPolicyEmergencyStop(store, AssumedCommandBoundary(), clock=lambda: NOW).execute(
        "operator",
        "school",
        EmergencyStopCommand(
            client_request_id="use-stop",
            feature_scope="fixture.feature",
            expected_epoch=1,
            reason="synthetic emergency",
        ),
    )
    published(service, store, "use-after-stop")
    with (
        pytest.raises(PolicyError, match="AI_POLICY_PIN_REVOKED"),
        leases.continue_use("worker", "school", request(), pin, "exposure"),
    ):
        pytest.fail("pre-stop pin resurrected")
    forged = pin.model_copy(update={"activation_epoch": 3})
    with (
        pytest.raises(PolicyError, match="AI_POLICY_PIN_MISMATCH"),
        leases.continue_use("worker", "school", request(), forged, "exposure"),
    ):
        pytest.fail("old policy not active at new epoch")


def test_current_use_sql_scope_share_fence_blocks_stop_until_lease_exit(activation_harness):
    import time
    from threading import Event

    from sqlalchemy import text

    from sketch2life.application.ai_policy_control import AiPolicyEmergencyStop
    from sketch2life.application.ai_policy_use import PolicyUseLeases
    from sketch2life.contracts.schemas.ai_policy_control import EmergencyStopCommand
    from tests.unit.test_ai_policy_use import AssumedUseBoundary, request

    service, _, store = activation_harness
    published(service, store, "lease-lock")
    leases = PolicyUseLeases(store, AssumedUseBoundary())
    started = Event()

    def stop():
        local = AiPolicyEmergencyStop(store, AssumedCommandBoundary(), clock=lambda: NOW)
        started.set()
        return local.execute(
            "operator",
            "school",
            EmergencyStopCommand(
                client_request_id="blocked-stop",
                feature_scope="fixture.feature",
                expected_epoch=1,
                reason="synthetic emergency",
            ),
        )

    with ThreadPoolExecutor(max_workers=1) as pool:
        with leases.begin("worker", "school", request()) as observation:
            pending = pool.submit(stop)
            assert started.wait(timeout=10)
            deadline = time.monotonic() + 5
            lock_wait = False
            with store.engine.connect().execution_options(
                isolation_level="AUTOCOMMIT"
            ) as connection:
                while time.monotonic() < deadline:
                    lock_wait = connection.scalar(
                        text("""
                        SELECT EXISTS (SELECT 1 FROM pg_stat_activity
                        WHERE datname=current_database() AND pid<>pg_backend_pid()
                        AND wait_event_type='Lock' AND query LIKE '%effective_scope%')
                    """)
                    )
                    if lock_wait:
                        break
                    Event().wait(timeout=0.01)
            assert lock_wait and not pending.done()
            assert observation.current_scope_epoch == 1
        assert pending.result(timeout=15).disabled
    with (
        pytest.raises(PolicyError, match="AI_POLICY_NOT_ELIGIBLE"),
        leases.begin("worker", "school", request()),
    ):
        pytest.fail("new work after stop")
