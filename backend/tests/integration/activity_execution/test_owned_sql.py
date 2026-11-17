"""Prepared OWN11 PG17 cases; separate approval/AE11 opt-in, never provisions DB.

AE11_TEST_ALLOW_SCHEMA_DDL=1 +private AE11_TEST_DATABASE_URL must target new dedicated
loopback ae11_* DB. Collection/skips not SQL PASS. No other card's permission reused.
"""

import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, delete, inspect, select, text, update
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError

from sketch2life.application.activity_execution import event_id
from sketch2life.application.ports.activity_execution import OutcomeAck, OutcomeEvent, Receipt
from sketch2life.domain.activity_execution.model import Action, digest
from sketch2life.domain.knowledge_video.model import VideoError
from sketch2life.infrastructure.activity_execution.sql import SqlActivityStore
from sketch2life.infrastructure.activity_execution.tables import (
    ACK,
    EVENT,
    HEAD,
    HISTORY,
    METADATA,
    RECEIPT,
)
from tests.activity_execution_fixtures import (
    NOW,
    actor,
    assignment,
    prepared,
    ref,
)
from tests.activity_execution_fixtures import (
    select as command,
)
from tests.unit.test_activity_execution_persistence import migration


@pytest.fixture
def engine():
    if os.environ.get("AE11_TEST_ALLOW_SCHEMA_DDL") != "1":
        pytest.skip("NOT_RUN: separately authorized isolated own11 PG17 environment required")
    try:
        url = make_url(os.environ.get("AE11_TEST_DATABASE_URL", ""))
        valid = (
            url.drivername == "postgresql+psycopg"
            and url.host in {"127.0.0.1", "localhost", "::1"}
            and url.database is not None
            and url.database.startswith("ae11_")
            and len(url.database) >= 12
        )
    except Exception:
        valid = False
    if not valid:
        pytest.fail("explicit new dedicated loopback ae11_ test DB required", pytrace=False)
    db = create_engine(url, hide_parameters=True)
    owned = False
    try:
        with db.begin() as conn:
            assert str(conn.execute(text("SHOW server_version")).scalar_one()).startswith("17.")
            assert not inspect(conn).has_schema("activity_execution"), "refuse existing schema"
            with Operations.context(MigrationContext.configure(conn)):
                migration().upgrade()
        owned = True
        yield db
    finally:
        if owned:
            with db.begin() as conn, Operations.context(MigrationContext.configure(conn)):
                migration().downgrade()  # Exact own objects, never CASCADE/global DB deletion.
        db.dispose()


def seed(engine, terminal=False, acknowledge=False):
    row = assignment()
    store = SqlActivityStore(engine)
    with store.transaction("school", "session") as rows:
        rows.write(None, Receipt(actor(), command().fingerprint(), row), None)
    if terminal:
        after = row.transition(Action.SKIP, 1, NOW, reason="Teacher chose not performed")
        e = OutcomeEvent(event_id(after), after, NOW, "teacher")
        with store.transaction("school", "session") as rows:
            rows.write(row, Receipt(actor(client_key="skip"), digest("skip"), after), e)
            if acknowledge:
                rows.acknowledge(e, OutcomeAck(e.event_id, e.fingerprint(), ref("ack")))
        return after, e
    return row, None


def test_frozen_migration_owns_exact_five_tables(engine):
    with engine.begin() as conn:
        assert set(inspect(conn).get_table_names(schema="activity_execution")) == {
            table.name for table in METADATA.tables.values()
        }


def test_commit_receipt_history_and_reconnect_scope(engine):
    row, _ = seed(engine)
    engine.dispose()  # Connection reopen, NOT actual process/cluster restart.
    with SqlActivityStore(engine).transaction("school", "session") as rows:
        assert rows.load(row.assignment_id) == row
        assert rows.receipt("teacher", "key").assignment == row
        assert rows.receipt("other", "key") is None
    with SqlActivityStore(engine).transaction("other", "session") as rows:
        assert rows.load(row.assignment_id) is None


def test_atomic_assignment_receipt_history_rollback(engine):
    with (
        pytest.raises(RuntimeError),
        SqlActivityStore(engine).transaction("school", "session") as rows,
    ):
        rows.write(None, Receipt(actor(), command().fingerprint(), assignment()), None)
        raise RuntimeError("synthetic rollback")
    with SqlActivityStore(engine).transaction("school", "session") as rows:
        assert rows.load("assignment") is None and rows.receipt("teacher", "key") is None
    with engine.begin() as conn:
        assert not conn.execute(select(HISTORY)).all()


def test_cas_competing_ready_commands_one_winner(engine):
    before, _ = seed(engine)

    def run(index):
        try:
            with SqlActivityStore(engine).transaction("school", "session") as rows:
                rows.write(
                    before,
                    Receipt(
                        actor(client_key="confirm." + str(index)), digest(str(index)), prepared()
                    ),
                    None,
                )
            return "saved"
        except VideoError as exc:
            return str(exc)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(run, (1, 2)))
    assert sorted(outcomes) == ["ACTIVITY_STALE_REVISION", "saved"]
    with engine.begin() as conn:
        assert len(conn.execute(select(HISTORY)).all()) == 2


@pytest.mark.parametrize("table", [HISTORY, RECEIPT, EVENT, ACK])
@pytest.mark.parametrize("operation", ["update", "delete"])
def test_append_only_raw_mutation_refused(engine, table, operation):
    seed(engine, terminal=True, acknowledge=True)
    with pytest.raises(DBAPIError), engine.begin() as conn:
        conn.execute(delete(table) if operation == "delete" else update(table).values(revision=99))


def test_outcome_event_and_assignment_rollback_together(engine):
    before, _ = seed(engine)
    after = before.transition(Action.SKIP, 1, NOW, reason="Teacher choice")
    event = OutcomeEvent(event_id(after), after, NOW, "teacher")
    with (
        pytest.raises(RuntimeError),
        SqlActivityStore(engine).transaction("school", "session") as rows,
    ):
        rows.write(before, Receipt(actor(client_key="skip"), digest("skip"), after), event)
        raise RuntimeError("synthetic rollback")
    with SqlActivityStore(engine).transaction("school", "session") as rows:
        assert rows.load("assignment") == before
        assert rows.event(event.event_id) is None


def test_exact_ack_persists_replays_and_foreign_conflicts(engine):
    _, event = seed(engine, terminal=True)
    ack = OutcomeAck(event.event_id, event.fingerprint(), ref("ack"))
    store = SqlActivityStore(engine)
    with store.transaction("school", "session") as rows:
        rows.acknowledge(event, ack)
    with store.transaction("school", "session") as rows:
        assert rows.event(event.event_id) == (event, ack)
        rows.acknowledge(event, ack)
        with pytest.raises(VideoError, match="ACK_CONFLICT"):
            rows.acknowledge(event, replace(ack, receipt_ref=ref("different")))
        with pytest.raises(VideoError, match="INVALID_ACK"):
            rows.acknowledge(event, replace(ack, event_digest="f" * 64))


def test_ack_commit_rollback_preserves_pending_event(engine):
    _, event = seed(engine, terminal=True)
    ack = OutcomeAck(event.event_id, event.fingerprint(), ref("ack"))
    with (
        pytest.raises(RuntimeError),
        SqlActivityStore(engine).transaction("school", "session") as rows,
    ):
        rows.acknowledge(event, ack)
        raise RuntimeError("lost write before commit")
    with SqlActivityStore(engine).transaction("school", "session") as rows:
        assert rows.event(event.event_id) == (event, None)


def test_terminal_head_and_source_history_not_resurrected_or_deleted(engine):
    row, _ = seed(engine, terminal=True)
    with pytest.raises(DBAPIError), engine.begin() as conn:
        conn.execute(update(HEAD).values(revision=row.revision + 1))
    with pytest.raises(DBAPIError), engine.begin() as conn:
        conn.execute(delete(HEAD))


def test_duplicate_command_key_rolls_back_new_assignment(engine):
    seed(engine)
    row = assignment(assignment_id="different")
    with (
        pytest.raises(VideoError, match="WRITE_CONFLICT"),
        SqlActivityStore(engine).transaction("school", "session") as rows,
    ):
        rows.write(None, Receipt(actor(), digest("different"), row), None)
    with SqlActivityStore(engine).transaction("school", "session") as rows:
        assert rows.load("different") is None
