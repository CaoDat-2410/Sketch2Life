"""Prepared PG17 OWN09 tests. No provisioning; skipped is NOT actual evidence.

Separate environment approval and both VR09_TEST_ALLOW_SCHEMA_DDL=1 and
VR09_TEST_DATABASE_URL required. Never reuse KV08 opt-in or production databases.
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

from sketch2life.application.ports.video_review_lifecycle import ReviewChangeReceipt
from sketch2life.domain.knowledge_video.model import VideoError
from sketch2life.domain.video_review.model import ReviewHead
from sketch2life.infrastructure.video_review.sql import SqlVideoPlaybackStore, SqlVideoReviewStore
from sketch2life.infrastructure.video_review.tables import (
    EVENT,
    HEAD,
    HISTORY,
    METADATA,
    PLAYBACK,
    PLAYBACK_HISTORY,
    RECEIPT,
)
from tests.unit.test_video_playback import receipt as play_receipt
from tests.unit.test_video_review_lifecycle import change, invalidate, rebind
from tests.unit.test_video_review_persistence import migration, pending, write_receipt


@pytest.fixture
def engine():
    if os.environ.get("VR09_TEST_ALLOW_SCHEMA_DDL") != "1":
        pytest.skip("NOT_RUN: separate owned09 SQL environment approval/opt-in required")
    raw = os.environ.get("VR09_TEST_DATABASE_URL")
    try:
        url = make_url(raw or "")
        valid = (
            url.drivername == "postgresql+psycopg"
            and url.host in {"127.0.0.1", "localhost", "::1"}
            and url.database is not None
            and url.database.startswith("vr09_")
            and len(url.database) >= 12
        )
    except Exception:
        valid = False
    if not valid:
        pytest.fail("explicit dedicated loopback vr09_ database required", pytrace=False)
    db = create_engine(url, hide_parameters=True)
    owned = False
    module = migration()
    try:
        with db.begin() as conn:
            assert str(conn.execute(text("SHOW server_version")).scalar_one()).startswith("17.")
            assert not inspect(conn).has_schema("video_review"), "refuse existing schema"
            with Operations.context(MigrationContext.configure(conn)):
                module.upgrade()
        owned = True
        yield db
    finally:
        if owned:
            # Exact own objects created by THIS fixture, no CASCADE/server/db deletion.
            with db.begin() as conn, Operations.context(MigrationContext.configure(conn)):
                module.downgrade()
        db.dispose()


def save_first(engine, key="key"):
    rec = write_receipt()
    rec = replace(rec, context=replace(rec.context, client_key=key))
    head = ReviewHead(rec.entry.subject, rec.entry.revision, rec.entry)
    with SqlVideoReviewStore(engine).transaction("school", "session", "video") as rows:
        rows.write(None, head, rec)
    return rec, head


def test_frozen_migration_owns_exact_six_tables(engine):
    with engine.begin() as conn:
        assert set(inspect(conn).get_table_names(schema="video_review")) == {
            table.name for table in METADATA.tables.values()
        }


def test_review_commit_reconnect_scoped_receipt_history_event(engine):
    rec, head = save_first(engine)
    with SqlVideoReviewStore(engine).transaction("school", "session", "video") as rows:
        assert rows.head() == head and rows.receipt("teacher", "key") == rec
        assert rows.receipt("other", "key") is None
        with pytest.raises(VideoError, match="IDEMPOTENCY_CONFLICT"):
            rows.change_receipt("teacher", "key")
    with SqlVideoReviewStore(engine).transaction("other", "session", "video") as rows:
        assert rows.head() is None
    with engine.begin() as conn:
        assert (
            len(conn.execute(select(HISTORY)).all()) == len(conn.execute(select(EVENT)).all()) == 1
        )


def test_rollback_discards_head_receipt_history_event(engine):
    rec = write_receipt()
    head = ReviewHead(rec.entry.subject, rec.entry.revision, rec.entry)
    with (
        pytest.raises(RuntimeError),
        SqlVideoReviewStore(engine).transaction("school", "session", "video") as rows,
    ):
        rows.write(None, head, rec)
        raise RuntimeError("synthetic rollback")
    with SqlVideoReviewStore(engine).transaction("school", "session", "video") as rows:
        assert rows.head() is None and rows.receipt("teacher", "key") is None
    with engine.begin() as conn:
        assert not conn.execute(select(HISTORY)).all() and not conn.execute(select(EVENT)).all()


def test_first_write_race_one_winner(engine):
    def attempt(index):
        try:
            save_first(engine, "key." + str(index))
            return "saved"
        except VideoError as exc:
            return str(exc)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(attempt, (1, 2)))
    assert outcomes.count("saved") == 1
    assert outcomes.count("VIDEO_REVIEW_STALE_REVISION") == 1
    with engine.begin() as conn:
        assert len(conn.execute(select(HISTORY)).all()) == 1


@pytest.mark.parametrize("table", [HISTORY, EVENT, RECEIPT, PLAYBACK_HISTORY])
@pytest.mark.parametrize("operation", ["update", "delete"])
def test_raw_immutable_rows_mutation_refused(engine, table, operation):
    save_first(engine)
    with SqlVideoPlaybackStore(engine).transaction("school", "session") as rows:
        rows.insert(pending())
    with pytest.raises(DBAPIError), engine.begin() as conn:
        conn.execute(update(table).values(revision=99) if operation == "update" else delete(table))


def test_raw_head_revision_skip_refused(engine):
    save_first(engine)
    with pytest.raises(DBAPIError), engine.begin() as conn:
        conn.execute(update(HEAD).values(revision=99))


@pytest.mark.parametrize("operation", [invalidate(), rebind()])
def test_lifecycle_commit_archives_original_and_conflicts_with_review_key(engine, operation):
    rec, head = save_first(engine)
    event = change(operation, head)
    ctx = replace(rec.context, client_key="change.key", expected_review_revision=head.revision)
    changed = ReviewChangeReceipt(ctx, event.request, event)
    store = SqlVideoReviewStore(engine)
    with store.transaction("school", "session", "video") as rows:
        rows.change(changed)
    with store.transaction("school", "session", "video") as rows:
        assert rows.head() == event.after
        assert rows.receipt("teacher", "key") == rec
        assert rows.change_receipt("teacher", "change.key") == changed
        assert changed.change.archived.entry == head.entry
        with pytest.raises(VideoError, match="IDEMPOTENCY_CONFLICT"):
            rows.receipt("teacher", "change.key")


def test_playback_commit_reconnect_terminal_and_raw_overwrite_refused(engine):
    intent = pending()
    store = SqlVideoPlaybackStore(engine)
    with store.transaction("school", "session") as rows:
        rows.insert(intent)
    with store.transaction("school", "session") as rows:
        assert rows.get("teacher", "key") == intent
        rows.save(intent.settle(play_receipt(intent)), expected_revision=1)
    with store.transaction("school", "session") as rows:
        assert rows.get("teacher", "key") == intent.settle(play_receipt(intent))
        with pytest.raises(VideoError, match="STALE_INTENT"):
            rows.save(intent.settle(play_receipt(intent)), expected_revision=1)
    with pytest.raises(DBAPIError), engine.begin() as conn:
        conn.execute(update(PLAYBACK).values(state="pending", revision=1))


def test_new_connections_after_pool_dispose_preserve_original_pending_key(engine):
    intent = pending()
    with SqlVideoPlaybackStore(engine).transaction("school", "session") as rows:
        rows.insert(intent)
    engine.dispose()  # Reopen connections; not a simulated external service restart.
    with SqlVideoPlaybackStore(engine).transaction("school", "session") as rows:
        assert rows.get("teacher", "key") == intent
        assert rows.get("foreign", "key") is None


def test_lifecycle_cas_race_no_second_history_or_receipt(engine):
    rec, head = save_first(engine)

    def attempt(index):
        event = replace(change(invalidate(), head), event_id="event." + str(index))
        ctx = replace(
            rec.context, client_key="change." + str(index), expected_review_revision=head.revision
        )
        try:
            with SqlVideoReviewStore(engine).transaction("school", "session", "video") as rows:
                rows.change(ReviewChangeReceipt(ctx, event.request, event))
            return "saved"
        except VideoError as exc:
            return str(exc)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(attempt, (1, 2)))
    assert sorted(outcomes) == ["VIDEO_REVIEW_STALE_REVISION", "saved"]
    with engine.begin() as conn:
        assert len(conn.execute(select(HISTORY)).all()) == 2
        assert len(conn.execute(select(RECEIPT)).all()) == 2


def test_duplicate_playback_insert_aborts_whole_transaction(engine):
    store = SqlVideoPlaybackStore(engine)
    intent = pending()
    with store.transaction("school", "session") as rows:
        rows.insert(intent)
    with (
        pytest.raises(VideoError, match="WRITE_CONFLICT"),
        store.transaction("school", "session") as rows,
    ):
        rows.insert(replace(intent, request=replace(intent.request, review_id="different")))
    with store.transaction("school", "session") as rows:
        assert rows.get("teacher", "key") == intent
    with engine.begin() as conn:
        assert len(conn.execute(select(PLAYBACK_HISTORY)).all()) == 1


def test_pending_intent_and_event_rollback_together(engine):
    store = SqlVideoPlaybackStore(engine)
    with pytest.raises(RuntimeError), store.transaction("school", "session") as rows:
        rows.insert(pending())
        raise RuntimeError("synthetic rollback")
    with store.transaction("school", "session") as rows:
        assert rows.get("teacher", "key") is None
    with engine.begin() as conn:
        assert not conn.execute(select(PLAYBACK_HISTORY)).all()
        assert not conn.execute(select(EVENT)).all()


def test_changed_subject_cannot_copy_raw_approval(engine):
    save_first(engine)
    with pytest.raises(DBAPIError), engine.begin() as conn:
        conn.execute(update(HEAD).values(revision=3, subject_digest="f" * 64))
