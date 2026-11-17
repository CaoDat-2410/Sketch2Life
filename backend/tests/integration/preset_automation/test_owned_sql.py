"""PREPARED actual13 PG17 tests; opt-in environment separately authorized. No provisioning."""

import os
from concurrent.futures import ThreadPoolExecutor

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError

from sketch2life.domain.preset_automation.model import (
    EffectReceipt,
    IntentState,
    PresetError,
    Stamp,
)
from sketch2life.infrastructure.preset_automation.sql import SqlPresetStore
from tests.preset_automation_fixtures import NOW, body, library
from tests.unit.test_preset_automation_domain import intent
from tests.unit.test_preset_automation_persistence import migration


@pytest.fixture
def engine():
    if os.environ.get("PA13_TEST_ALLOW_SCHEMA_DDL") != "1":
        pytest.skip("NOT_RUN: separately approved isolated13 PG17 environment required")
    try:
        url = make_url(os.environ.get("PA13_TEST_DATABASE_URL", ""))
        valid = (
            url.drivername == "postgresql+psycopg"
            and url.host in {"localhost", "127.0.0.1", "::1"}
            and url.database
            and url.database.startswith("pa13_")
            and len(url.database) >= 12
        )
    except Exception:
        valid = False
    if not valid:
        pytest.fail("dedicated new loopback pa13_ database required", pytrace=False)
    db = create_engine(url, hide_parameters=True)
    owned = False
    try:
        with db.begin() as conn:
            assert str(conn.execute(text("SHOW server_version")).scalar_one()).startswith("17.")
            assert not inspect(conn).has_schema("preset_automation"), "refuse existing schema"
            with Operations.context(MigrationContext.configure(conn)):
                migration()["upgrade"]()
        owned = True
        yield db
    finally:
        if owned:
            with db.begin() as conn, Operations.context(MigrationContext.configure(conn)):
                migration()["downgrade"]()  # Exact owned schema, no CASCADE or DB/server deletion.
        db.dispose()


def seed(engine):
    store = SqlPresetStore(engine)
    with store.transaction("school", "library") as rows:
        rows.put("preset", None, library())
    return store


def test_actual_schema_and_frozen_migration(engine):
    with engine.begin() as conn:
        assert set(inspect(conn).get_table_names(schema="preset_automation")) == {"head", "history"}


def test_actual_reconnect_history_and_scoping(engine):
    store = seed(engine)
    with store.transaction("school", "library") as rows:
        before = rows.get("preset")
        after = before.change("submit_review", 1, 1, body().hash, "author", NOW)
        rows.put("preset", before, after)
    engine.dispose()
    with store.transaction("school", "library") as rows:
        assert rows.history("preset", 1) == library() and rows.get("preset") == after
    with store.transaction("other", "library") as rows:
        assert rows.get("preset") is None


def test_actual_whole_transaction_rollback(engine):
    store = SqlPresetStore(engine)
    with pytest.raises(RuntimeError), store.transaction("school", "library") as rows:
        rows.put("preset", None, library())
        raise RuntimeError("synthetic failure")
    with store.transaction("school", "library") as rows:
        assert rows.get("preset") is None and rows.history("preset", 1) is None


def test_actual_competing_cas_single_winner(engine):
    store = seed(engine)
    before = library()
    after = before.change("submit_review", 1, 1, body().hash, "author", NOW)

    def mutate(_):
        try:
            with store.transaction("school", "library") as rows:
                rows.put("preset", before, after)
            return "won"
        except PresetError:
            return "stale"

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(mutate, range(2))) == ["stale", "won"]


@pytest.mark.parametrize(
    "table,action", [("history", "UPDATE"), ("history", "DELETE"), ("head", "DELETE")]
)
def test_actual_immutable_history_no_head_delete(engine, table, action):
    seed(engine)
    with pytest.raises(DBAPIError), engine.begin() as conn:
        sql = (
            f"UPDATE preset_automation.{table} SET revision=revision+1"
            if action == "UPDATE"
            else (f"DELETE FROM preset_automation.{table}")
        )
        conn.execute(text(sql))


def test_actual_terminal_requires_exact_receipt(engine):
    store = SqlPresetStore(engine)
    queued = intent()
    sending = queued.transition(IntentState.SENDING, "sending")
    with store.transaction("school", "session") as rows:
        rows.put("intent", None, queued)
        rows.put("intent", queued, sending)
    applied = sending.transition(IntentState.APPLIED, "applied")
    with pytest.raises(PresetError), store.transaction("school", "session") as rows:
        rows.put("intent", sending, applied)
    receipt = EffectReceipt(
        "intent",
        "school",
        "session",
        queued.hash,
        "applied",
        queued.observed,
        Stamp(1, 2, 1, 2),
        "native",
        "applied",
    )
    with store.transaction("school", "session") as rows:
        rows.put("effect-intent", None, receipt)
        rows.put("intent", sending, applied)
    with store.transaction("school", "session") as rows:
        assert rows.get("intent") == applied and rows.get("effect-intent") == receipt


def test_actual_receipt_write_failure_rolls_back_terminal(engine):
    store = SqlPresetStore(engine)
    queued = intent()
    sending = queued.transition(IntentState.SENDING, "sending")
    with store.transaction("school", "session") as rows:
        rows.put("intent", None, queued)
        rows.put("intent", queued, sending)
    receipt = EffectReceipt(
        "intent",
        "school",
        "session",
        queued.hash,
        "applied",
        queued.observed,
        Stamp(1, 2, 1, 2),
        "native",
        "applied",
    )
    with pytest.raises(RuntimeError), store.transaction("school", "session") as rows:
        rows.put("effect-intent", None, receipt)
        rows.put("intent", sending, sending.transition(IntentState.APPLIED, "applied"))
        raise RuntimeError("synthetic commit failure")
    with store.transaction("school", "session") as rows:
        assert rows.get("intent") == sending and rows.get("effect-intent") is None


def test_actual_receipt_immutable_direct_sql(engine):
    from sketch2life.application.ports.preset_automation import LocalReceipt
    from sketch2life.application.preset_governance import receipt_key

    store = seed(engine)
    key = receipt_key("author", "key")
    with store.transaction("school", "library") as rows:
        rows.put(key, None, LocalReceipt("author", "key", "a" * 64, "preset", 1, 1))
    with pytest.raises(DBAPIError), engine.begin() as conn:
        conn.execute(
            text("UPDATE preset_automation.head SET revision=2 WHERE object_key=:key"), {"key": key}
        )


def test_actual_foreign_receipt_does_not_commit(engine):
    store = SqlPresetStore(engine)
    row = intent()
    with store.transaction("school", "session") as rows:
        rows.put("intent", None, row)
        rows.put("intent", row, row.transition(IntentState.SENDING, "sending"))
    receipt = EffectReceipt(
        "intent",
        "other",
        "session",
        row.hash,
        "applied",
        row.observed,
        Stamp(1, 2, 1, 2),
        "native",
        "applied",
    )
    with pytest.raises(PresetError), store.transaction("school", "session") as rows:
        rows.put("effect-intent", None, receipt)
