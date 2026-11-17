"""PREPARED own10 PG17 tests, no provisioning. Collection is NOT actual SQL PASS.

Separate owner-approved VF10_TEST_DATABASE_URL and VF10_TEST_ALLOW_SCHEMA_DDL=1,
dedicated NEW loopback vf10_* PG17 DB required. Never inherit another card's opt-in.
"""

import os
from concurrent.futures import ThreadPoolExecutor

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, delete, inspect, select, text, update
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError

from sketch2life.domain.knowledge_video.model import VideoError
from sketch2life.domain.video_failure.model import Action
from sketch2life.infrastructure.video_failure.sql import SqlFailureStore
from sketch2life.infrastructure.video_failure.tables import EVENT, HISTORY, INTENT, METADATA
from tests.unit.test_video_failure_persistence import migration
from tests.video_failure_fixtures import context, intent, receipt


@pytest.fixture
def engine():
    if os.environ.get("VF10_TEST_ALLOW_SCHEMA_DDL") != "1":
        pytest.skip("NOT_RUN: separate own10 SQL environment authorization/opt-in required")
    try:
        url = make_url(os.environ.get("VF10_TEST_DATABASE_URL", ""))
        valid = (
            url.drivername == "postgresql+psycopg"
            and url.host in {"127.0.0.1", "localhost", "::1"}
            and url.database is not None
            and url.database.startswith("vf10_")
            and len(url.database) >= 12
        )
    except Exception:
        valid = False
    if not valid:
        pytest.fail("explicit dedicated loopback vf10_ test DB required", pytrace=False)
    db = create_engine(url, hide_parameters=True)
    owned = False
    try:
        with db.begin() as conn:
            assert str(conn.execute(text("SHOW server_version")).scalar_one()).startswith("17.")
            assert not inspect(conn).has_schema("video_failure"), "refuse existing schema"
            with Operations.context(MigrationContext.configure(conn)):
                migration().upgrade()
        owned = True
        yield db
    finally:
        if owned:
            with db.begin() as conn, Operations.context(MigrationContext.configure(conn)):
                migration().downgrade()  # Exact own objects, no CASCADE or database deletion.
        db.dispose()


def test_frozen_migration_exact_owned_tables(engine):
    with engine.begin() as conn:
        assert set(inspect(conn).get_table_names(schema="video_failure")) == {
            table.name for table in METADATA.tables.values()
        }


@pytest.mark.parametrize("action", list(Action))
def test_pending_then_receipt_commit_reconnect_all_actions(engine, action):
    i = intent(action)
    store = SqlFailureStore(engine)
    with store.transaction("school", "session") as rows:
        rows.insert(i)
    engine.dispose()  # Reopen connections, not actual process/cluster restart proof.
    with store.transaction("school", "session") as rows:
        assert rows.get("teacher", "key") == i
        rows.save(i.settle(receipt(i)), expected_revision=1)
    with store.transaction("school", "session") as rows:
        assert rows.get("teacher", "key") == i.settle(receipt(i))
        assert rows.get("foreign", "key") is None
    with store.transaction("foreign", "session") as rows:
        assert rows.get("teacher", "key") is None
    with engine.begin() as conn:
        assert (
            len(conn.execute(select(HISTORY)).all()) == len(conn.execute(select(EVENT)).all()) == 2
        )


def test_intent_claim_history_event_rollback_together(engine):
    store = SqlFailureStore(engine)
    with pytest.raises(RuntimeError), store.transaction("school", "session") as rows:
        rows.insert(intent())
        raise RuntimeError("synthetic rollback")
    with store.transaction("school", "session") as rows:
        assert rows.get("teacher", "key") is None
        rows.insert(intent())  # Claim was rolled back, not orphaned.
    with engine.begin() as conn:
        assert len(conn.execute(select(HISTORY)).all()) == 1


def test_concurrent_cross_actor_action_claim_one_winner(engine):
    def attempt(index):
        c = context(principal_id="teacher" if index == 1 else "teacher2", client_key=str(index))
        i = intent(
            Action.SKIP if index == 1 else Action.END,
            context=c,
            disposition_id="disposition." + str(index),
        )
        try:
            with SqlFailureStore(engine).transaction("school", "session") as rows:
                rows.insert(i)
            return "saved"
        except VideoError as exc:
            return str(exc)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(attempt, (1, 2)))
    assert sorted(outcomes) == ["VIDEO_DISPOSITION_CONFLICT", "saved"]
    with engine.begin() as conn:
        assert len(conn.execute(select(INTENT)).all()) == 1
        assert len(conn.execute(select(HISTORY)).all()) == 1


@pytest.mark.parametrize("table", [HISTORY, EVENT])
@pytest.mark.parametrize("operation", ["update", "delete"])
def test_append_only_rows_refuse_raw_mutation(engine, table, operation):
    with SqlFailureStore(engine).transaction("school", "session") as rows:
        rows.insert(intent())
    with pytest.raises(DBAPIError), engine.begin() as conn:
        conn.execute(delete(table) if operation == "delete" else update(table).values(revision=2))


def test_terminal_intent_cannot_overwrite_or_delete(engine):
    i = intent()
    store = SqlFailureStore(engine)
    with store.transaction("school", "session") as rows:
        rows.insert(i)
        rows.save(i.settle(receipt(i)), expected_revision=1)
    with (
        pytest.raises(VideoError, match="STALE_INTENT"),
        store.transaction("school", "session") as rows,
    ):
        rows.save(i.settle(receipt(i)), expected_revision=1)
    with pytest.raises(DBAPIError), engine.begin() as conn:
        conn.execute(delete(INTENT))


def test_duplicate_key_and_claim_abort_whole_transaction(engine):
    store = SqlFailureStore(engine)
    with store.transaction("school", "session") as rows:
        rows.insert(intent())
    with (
        pytest.raises(VideoError, match="CONFLICT"),
        store.transaction("school", "session") as rows,
    ):
        rows.insert(intent(Action.END, disposition_id="other", context=context(client_key="new")))
    with engine.begin() as conn:
        assert len(conn.execute(select(INTENT)).all()) == 1


def test_raw_mutation_of_original_intent_refused_on_settlement(engine):
    with SqlFailureStore(engine).transaction("school", "session") as rows:
        rows.insert(intent())
    with pytest.raises(DBAPIError), engine.begin() as conn:
        conn.execute(update(INTENT).values(revision=2, claim_key="f" * 64))


def test_receipt_settlement_rollback_keeps_pending(engine):
    i = intent()
    store = SqlFailureStore(engine)
    with store.transaction("school", "session") as rows:
        rows.insert(i)
    with pytest.raises(RuntimeError), store.transaction("school", "session") as rows:
        rows.save(i.settle(receipt(i)), expected_revision=1)
        raise RuntimeError("synthetic rollback")
    with store.transaction("school", "session") as rows:
        assert rows.get("teacher", "key") == i
    with engine.begin() as conn:
        assert len(conn.execute(select(HISTORY)).all()) == 1
