"""Real migration/atomicity/race tests. Skips are NOT_RUN, not runtime PASS."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from threading import Barrier

import pytest
from alembic.config import Config
from sqlalchemy import Engine, func, inspect, select, text
from sqlalchemy.exc import DBAPIError

from alembic import command
from sketch2life.application.ports.learning_content import ContentEvent, ContentReceipt
from sketch2life.domain.learning_content.model import (
    Authority,
    Capability,
    ContentError,
    ContentState,
    create,
    edit,
    submit,
)
from sketch2life.infrastructure.learning_content.sql import SqlContentStore
from sketch2life.infrastructure.learning_content.tables import EVENT, OUTBOX, RECORD, VERSION

BACKEND = Path(__file__).resolve().parents[3]
NOW = datetime(2026, 10, 17, tzinfo=UTC)
ACTOR = Authority("author", "school", frozenset(Capability))


def migrate(engine: Engine, monkeypatch: pytest.MonkeyPatch) -> Config:
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL",
                       engine.url.render_as_string(hide_password=False))
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "alembic"))
    command.upgrade(config, "learning_content@head")
    return config


def seed(store: SqlContentStore):
    content = create("record", ACTOR, {"title": "Butterfly"}, NOW)
    with store.transaction() as tx:
        tx.save(content, expected_revision=None, event=ContentEvent("e1", "created", "author", NOW))
    return content


def test_upgrade_downgrade_only_owns_its_schema(content_engine, monkeypatch) -> None:
    config = migrate(content_engine, monkeypatch)
    assert len(inspect(content_engine).get_table_names(schema="learning_content")) == 6
    assert "ai_jobs" not in inspect(content_engine).get_schema_names()
    command.downgrade(config, "learning_content@base")
    assert "learning_content" not in inspect(content_engine).get_schema_names()
    command.upgrade(config, "learning_content@head")


def test_restart_reads_bytes_and_atomic_event_outbox(content_engine, monkeypatch) -> None:
    migrate(content_engine, monkeypatch)
    original = seed(SqlContentStore(content_engine))
    with SqlContentStore(content_engine).transaction() as tx:
        assert tx.load("school", "record") == original
        assert tx.load("another-school", "record") is None
    with content_engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(EVENT)) == 1
        assert connection.scalar(select(func.count()).select_from(OUTBOX)) == 1
    # A second Python process and new engine must recover committed bytes.
    # Merely reconstructing a repository over the same pool is not restart proof.
    content_engine.dispose()
    environment = os.environ.copy()
    environment["LC_CHILD_DATABASE_URL"] = content_engine.url.render_as_string(hide_password=False)
    environment["PYTHONPATH"] = (
        str(BACKEND / "src") + os.pathsep + environment.get("PYTHONPATH", ""))
    child = subprocess.run(
        [sys.executable, "-c", """
import json, os
from sqlalchemy import create_engine, select, func
from sketch2life.infrastructure.learning_content.sql import SqlContentStore
from sketch2life.infrastructure.learning_content.tables import EVENT, OUTBOX
engine = create_engine(os.environ["LC_CHILD_DATABASE_URL"], hide_parameters=True)
with SqlContentStore(engine).transaction() as tx:
    content = tx.load("school", "record")
    assert content is not None
    snapshot = {"hash": content.hash, "revision": content.revision, "pid": os.getpid()}
with engine.connect() as connection:
    snapshot["events"] = connection.scalar(select(func.count()).select_from(EVENT))
    snapshot["outbox"] = connection.scalar(select(func.count()).select_from(OUTBOX))
engine.dispose()
print(json.dumps(snapshot))
"""],
        env=environment, cwd=BACKEND, capture_output=True, text=True, timeout=30, check=True)
    snapshot = json.loads(child.stdout)
    assert snapshot["pid"] != os.getpid()
    assert snapshot["hash"] == original.hash
    assert (snapshot["revision"], snapshot["events"], snapshot["outbox"]) == (1, 1, 1)


def test_exception_rolls_back_state_receipt_and_events(content_engine, monkeypatch) -> None:
    migrate(content_engine, monkeypatch)
    store = SqlContentStore(content_engine)
    with pytest.raises(RuntimeError), store.transaction() as tx:
        tx.save(create("record", ACTOR, {}, NOW), expected_revision=None,
                event=ContentEvent("e1", "created", "author", NOW))
        tx.add_receipt(ContentReceipt("school", "author", "cmd", "a" * 64, "{}"))
        raise RuntimeError("synthetic rollback")
    with store.transaction() as tx:
        assert tx.load("school", "record") is None
        assert tx.receipt("school", "author", "cmd") is None
    with content_engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(EVENT)) == 0
        assert connection.scalar(select(func.count()).select_from(OUTBOX)) == 0


def test_stale_save_is_not_a_second_winner(content_engine, monkeypatch) -> None:
    migrate(content_engine, monkeypatch)
    store = SqlContentStore(content_engine)
    initial = seed(store)
    updated = submit(initial, ACTOR, expected_revision=1)
    with store.transaction() as tx:
        tx.save(updated, expected_revision=1, event=ContentEvent("e2", "submitted", "author", NOW))
    with pytest.raises(ContentError, match="CONTENT_STALE_REVISION"), store.transaction() as tx:
        tx.save(updated, expected_revision=1,
                event=ContentEvent("e3", "submitted", "author", NOW))


def test_concurrent_updates_have_one_cas_winner(content_engine, monkeypatch) -> None:
    migrate(content_engine, monkeypatch)
    store = SqlContentStore(content_engine)
    initial = seed(store)
    updated = submit(initial, ACTOR, expected_revision=1)
    barrier = Barrier(2)

    def attempt(index: int) -> str:
        barrier.wait(timeout=15)
        try:
            with store.transaction() as tx:
                tx.save(updated, expected_revision=1,
                        event=ContentEvent(f"race-{index}", "submitted", "author", NOW))
            return "winner"
        except ContentError as error:
            return str(error)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, (1, 2)))
    assert sorted(results) == ["CONTENT_STALE_REVISION", "winner"]
    with content_engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(EVENT)) == 2


def test_edit_creates_version_and_preserves_previous_bytes(content_engine, monkeypatch) -> None:
    migrate(content_engine, monkeypatch)
    store = SqlContentStore(content_engine)
    initial = seed(store)
    changed = edit(initial, ACTOR, {"title": "Changed"}, NOW,
                   expected_revision=1, next_version=2)
    with store.transaction() as tx:
        tx.save(changed, expected_revision=1, event=ContentEvent("e2", "edited", "author", NOW))
    with store.transaction() as tx:
        previous = tx.load("school", "record", version=1)
        current = tx.load("school", "record")
        assert previous is not None and previous.hash == initial.hash
        assert previous.revision == current.revision == 2
        assert current.state == ContentState.DRAFT and current.version == 2


@pytest.mark.parametrize("mutation", [
    "UPDATE learning_content.version SET body_json='{}'",
    "UPDATE learning_content.event SET kind='forged'",
    "DELETE FROM learning_content.event",
])
def test_database_rejects_rewriting_immutable_history(
    content_engine, monkeypatch, mutation: str,
) -> None:
    migrate(content_engine, monkeypatch)
    seed(SqlContentStore(content_engine))
    with pytest.raises(DBAPIError), content_engine.begin() as connection:
        connection.execute(text(mutation))
    with content_engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(RECORD)) == 1
        assert connection.scalar(select(func.count()).select_from(VERSION)) == 1
