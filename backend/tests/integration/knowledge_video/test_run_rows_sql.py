"""Prepared actual PG17 OWN-row cases. Not atomic BE2-01 bridge/provider evidence.

Never starts/provisions PostgreSQL. Requires separate owner-approved environment,
explicit KV08_TEST_ALLOW_SCHEMA_DDL=1, and KV08_TEST_DATABASE_URL for a NEW dedicated
loopback database kv08_*. Skips without opt-in; skipped is NOT actual evidence.
"""

import importlib.util
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from sketch2life.domain.knowledge_video.model import (
    ExactRef,
    FinalArtifact,
    Strategy,
    VideoError,
    VideoPin,
    VideoRun,
)
from sketch2life.infrastructure.knowledge_video.sql import VideoCommandReceipt, VideoRunRows

NOW = datetime(2026, 10, 18, tzinfo=UTC)


def run():
    def ref(name):
        return ExactRef(name, 1, "a" * 64)

    pin = VideoPin("school", "session", ref("bundle"), 0, 0, 0, (ref("source"),),
                   Strategy.GENERATE, ref("profile"), ref("encoding"), ref("rights"),
                   ref("retry"), ref("policy"), 1, ref("model"))
    return VideoRun("video", 1, 1, 1, "job", pin, NOW)


def receipt():
    return VideoCommandReceipt("school", "session", "teacher", "key", "b" * 64,
                               run().pin.digest(), "video", NOW)


@pytest.fixture
def engine():
    if os.environ.get("KV08_TEST_ALLOW_SCHEMA_DDL") != "1":
        pytest.skip("NOT_RUN: separate BE2-08 SQL environment approval/opt-in required")
    raw_url = os.environ.get("KV08_TEST_DATABASE_URL")
    if not raw_url:
        pytest.fail("explicit isolated database URL required", pytrace=False)
    try:
        url = make_url(raw_url)
        valid = (url.drivername == "postgresql+psycopg"
                 and url.host in {"127.0.0.1", "localhost", "::1"}
                 and url.database is not None and url.database.startswith("kv08_")
                 and len(url.database) >= 12)
    except Exception:
        valid = False
    if not valid:
        pytest.fail("dedicated loopback kv08_ database required", pytrace=False)
    path = (Path(__file__).resolve().parents[3]
            / "alembic/versions/20261018_kv_0001_knowledge_video.py")
    spec = importlib.util.spec_from_file_location("kv08_sql_migration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    db = create_engine(url, hide_parameters=True)
    owned = False
    try:
        with db.begin() as conn:
            assert str(conn.execute(text("SHOW server_version")).scalar_one()).startswith("17.")
            assert not inspect(conn).has_schema("knowledge_video"), "refuse existing schema"
            with Operations.context(MigrationContext.configure(conn)):
                module.upgrade()
        owned = True
        yield db
    finally:
        if owned:
            # Exact schema created by THIS fixture in validated isolated database.
            # Frozen downgrade drops only own two tables/schema, never CASCADE.
            with db.begin() as conn, Operations.context(MigrationContext.configure(conn)):
                module.downgrade()
        db.dispose()


def test_frozen_migration_creates_only_owned_tables(engine):
    with engine.begin() as conn:
        assert set(inspect(conn).get_table_names(schema="knowledge_video")) == {"run", "receipt"}


def test_commit_reconnect_preserves_exact_pin_and_receipt(engine):
    with engine.begin() as conn:
        rows = VideoRunRows(conn, "school")
        rows.insert(run())
        rows.put_receipt(receipt())
    with engine.begin() as conn:
        rows = VideoRunRows(conn, "school")
        assert rows.get("video") == run()
        assert rows.find_semantic("session", run().pin.digest()) == run()
        assert rows.get_receipt("session", "teacher", "key") == receipt()
        assert rows.get_receipt("session", "other", "key") is None


def test_transaction_failure_rolls_back_run_and_receipt(engine):
    with pytest.raises(RuntimeError, match="synthetic"), engine.begin() as conn:
        rows = VideoRunRows(conn, "school")
        rows.insert(run())
        rows.put_receipt(receipt())
        raise RuntimeError("synthetic")
    with engine.begin() as conn:
        assert VideoRunRows(conn, "school").get("video") is None


@pytest.mark.parametrize("duplicate", ["receipt", "semantic", "job"])
def test_duplicate_conflict_aborts_enclosing_transaction(engine, duplicate):
    with engine.begin() as conn:
        rows = VideoRunRows(conn, "school")
        rows.insert(run())
        rows.put_receipt(receipt())
    with pytest.raises(VideoError, match="VIDEO_WRITE_CONFLICT"), engine.begin() as conn:
        rows = VideoRunRows(conn, "school")
        if duplicate == "receipt":
            rows.put_receipt(receipt())
        elif duplicate == "semantic":
            rows.insert(replace(run(), video_id="video2", job_id="job2"))
        else:
            other_pin = replace(run().pin, context_revision=1)
            rows.insert(replace(run(), video_id="video2", pin=other_pin))
    with engine.begin() as conn:
        assert VideoRunRows(conn, "school").get("video2") is None


def test_scope_isolation(engine):
    with engine.begin() as conn:
        VideoRunRows(conn, "school").insert(run())
        assert VideoRunRows(conn, "other").get("video") is None
        assert VideoRunRows(conn, "other").find_semantic("session", run().pin.digest()) is None


def test_stale_cas_rejected_without_partial_write(engine):
    with engine.begin() as conn:
        rows = VideoRunRows(conn, "school")
        rows.insert(run())
        rows.save(run().start(1, "attempt"), expected_revision=1)
    with pytest.raises(VideoError, match="VIDEO_STALE_RUN"), engine.begin() as conn:
        VideoRunRows(conn, "school").save(run().cancel(1), expected_revision=1)
    with engine.begin() as conn:
        assert VideoRunRows(conn, "school").get("video") == run().start(1, "attempt")


def test_two_concurrent_cas_writers_have_one_winner(engine):
    with engine.begin() as conn:
        VideoRunRows(conn, "school").insert(run())

    def write(attempt):
        try:
            with engine.begin() as conn:
                VideoRunRows(conn, "school").save(run().start(1, attempt), expected_revision=1)
            return "winner"
        except VideoError as error:
            assert str(error) == "VIDEO_STALE_RUN"
            return "stale"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(write, ("attempt1", "attempt2"))) == ["stale", "winner"]


def test_final_artifact_immutable_and_policy_lineage_preserved(engine):
    running = run().start(1, "attempt")
    artifact = FinalArtifact(ExactRef("asset", 1, "c" * 64), running.pin.digest(),
                             running.pin.encoding, running.pin.content_profile)
    ready = running.finalize(2, "attempt", artifact)
    with engine.begin() as conn:
        rows = VideoRunRows(conn, "school")
        rows.insert(run())
        rows.save(running, expected_revision=1)
        rows.save(ready, expected_revision=2)
    changed = replace(ready, run_revision=4, artifact=replace(
        artifact, artifact=ExactRef("another", 1, "d" * 64)))
    with pytest.raises(VideoError, match="VIDEO_IMMUTABLE_ARTIFACT"), engine.begin() as conn:
        VideoRunRows(conn, "school").save(changed, expected_revision=3)
    with engine.begin() as conn:
        assert VideoRunRows(conn, "school").get("video") == ready


def test_terminal_cancel_cannot_be_resurrected(engine):
    with engine.begin() as conn:
        rows = VideoRunRows(conn, "school")
        rows.insert(run())
        rows.save(run().cancel(1), expected_revision=1)
    with pytest.raises(VideoError, match="VIDEO_TERMINAL_RUN"), engine.begin() as conn:
        VideoRunRows(conn, "school").save(replace(run().start(1, "attempt"), run_revision=3),
                                         expected_revision=2)
