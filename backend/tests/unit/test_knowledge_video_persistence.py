"""Codec/SQL-shape/participant behavior mocks only, NOT actual PostgreSQL evidence."""

import importlib.util
import json
import re
from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock

import pytest
from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.schema import CreateTable

from sketch2life.domain.knowledge_video.model import (
    ExactRef,
    FinalArtifact,
    Strategy,
    VideoError,
    VideoPin,
    VideoRun,
)
from sketch2life.infrastructure.knowledge_video.codec import decode_run, encode_run
from sketch2life.infrastructure.knowledge_video.sql import VideoCommandReceipt, VideoRunRows
from sketch2life.infrastructure.knowledge_video.tables import METADATA, RUN

NOW = datetime(2026, 10, 18, tzinfo=UTC)


def run():
    def ref(name):
        return ExactRef(name, 1, "a" * 64)

    pin = VideoPin("school", "session", ref("bundle"), 0, 0, 0, (ref("source"),),
                   Strategy.GENERATE, ref("profile"), ref("encoding"), ref("rights"),
                   ref("retry"), ref("policy"), 1, ref("model"))
    return VideoRun("video", 1, 1, 1, "job", pin, NOW)


def row(value=None):
    value = value or run()
    return {"organization_id": value.pin.organization_id, "session_id": value.pin.session_id,
            "video_id": value.video_id, "job_id": value.job_id, "run_revision": value.run_revision,
            "pin_digest": value.pin.digest(), "run_json": encode_run(value)}


def connection():
    conn = Mock()
    conn.dialect.name = "postgresql"
    conn.in_transaction.return_value = True
    conn.execute.return_value.mappings.return_value.one_or_none.return_value = row()
    conn.execute.return_value.rowcount = 1
    return conn


def receipt(**changes):
    return replace(VideoCommandReceipt("school", "session", "teacher", "key", "b" * 64,
                                       run().pin.digest(), "video", NOW), **changes)


def test_queued_running_ready_codec_roundtrip():
    queued = run()
    running = queued.start(1, "attempt")
    artifact = FinalArtifact(ExactRef("asset", 1, "b" * 64), queued.pin.digest(),
                             queued.pin.encoding, queued.pin.content_profile)
    ready = running.finalize(2, "attempt", artifact)
    for value in (queued, running, ready, running.cancel(2)):
        assert decode_run(json.loads(json.dumps(encode_run(value)))) == value


@pytest.mark.parametrize("changes", [
    {"run_revision": True}, {"run_revision": "1"}, {"created_at": "2026-10-18"},
    {"created_at": "2026-10-18T00:00:00"}, {"job_id": "https://endpoint"},
    {"generation_state": "stale"}, {"review_state": "approved"}, {"secret": "value"},
    {"generation_state": "succeeded"}, {"attempt_id": {}}, {"pin": None},
])
def test_corrupt_run_payload_rejected(changes):
    payload = {**encode_run(run()), **changes}
    with pytest.raises(VideoError, match="VIDEO_STORAGE_CORRUPT"):
        decode_run(payload)


@pytest.mark.parametrize("field,value", [
    ("policy_epoch", True), ("sources", []), ("strategy", "wan"), ("bundle", {}),
    ("secret", "value"), ("model_profile", None),
])
def test_corrupt_pin_rejected(field, value):
    payload = deepcopy(encode_run(run()))
    payload["pin"][field] = value
    with pytest.raises(VideoError, match="VIDEO_STORAGE_CORRUPT"):
        decode_run(payload)


def test_caller_transaction_required_no_autocommit_or_autobegin():
    conn = connection()
    conn.in_transaction.return_value = False
    rows = VideoRunRows(conn, "school")
    for call in (lambda: rows.get("video"), lambda: rows.insert(run()),
                 lambda: rows.save(run().start(1, "attempt"), expected_revision=1),
                 lambda: rows.get_receipt("session", "teacher", "key"),
                 lambda: rows.put_receipt(receipt()),
                 lambda: rows.find_semantic("session", run().pin.digest())):
        with pytest.raises(VideoError, match="VIDEO_TRANSACTION_REQUIRED"):
            call()
    conn.execute.assert_not_called()
    conn.begin.assert_not_called()
    conn.commit.assert_not_called()


def test_only_postgresql_participant():
    conn = connection()
    conn.dialect.name = "sqlite"
    with pytest.raises(VideoError, match="VIDEO_POSTGRESQL_REQUIRED"):
        VideoRunRows(conn, "school")


@pytest.mark.parametrize("column,value", [
    ("organization_id", "other"), ("session_id", "other"), ("video_id", "other"),
    ("job_id", "other"), ("run_revision", 2), ("pin_digest", "b" * 64),
])
def test_row_envelope_binding_checked(column, value):
    conn = connection()
    corrupt = {**row(), column: value}
    conn.execute.return_value.mappings.return_value.one_or_none.return_value = corrupt
    with pytest.raises(VideoError, match="VIDEO_STORAGE_CORRUPT"):
        VideoRunRows(conn, "school").get("video")


def test_cas_is_scoped_locked_and_never_commits():
    conn = connection()
    value = run().start(1, "attempt")
    VideoRunRows(conn, "school").save(value, expected_revision=1)
    statements = [call.args[0] for call in conn.execute.call_args_list]
    assert "FOR UPDATE" in str(statements[0])
    update = str(statements[1].compile(dialect=dialect()))
    assert "organization_id" in update and "run_revision =" in update
    conn.commit.assert_not_called()
    conn.rollback.assert_not_called()


@pytest.mark.parametrize("changes", [
    {"job_id": "other"}, {"video_version": 2},
    {"review_revision": 2},
    {"created_at": datetime(2026, 10, 19, tzinfo=UTC)},
    {"pin": replace(run().pin, policy_epoch=2)},
])
def test_cas_cannot_rewrite_original_lineage(changes):
    conn = connection()
    candidate = replace(run().start(1, "attempt"), **changes)
    with pytest.raises(VideoError, match="VIDEO_IMMUTABLE_LINEAGE"):
        VideoRunRows(conn, "school").save(candidate, expected_revision=1)
    assert conn.execute.call_count == 1


@pytest.mark.parametrize("expected", [0, True, "1", 2])
def test_cas_expected_revision_strict(expected):
    with pytest.raises(VideoError):
        VideoRunRows(connection(), "school").save(run().start(1, "attempt"),
                                                expected_revision=expected)


def test_cas_lost_update_raises_and_leaves_rollback_to_caller():
    conn = connection()
    conn.execute.return_value.rowcount = 0
    with pytest.raises(VideoError, match="VIDEO_STALE_RUN"):
        VideoRunRows(conn, "school").save(run().start(1, "attempt"), expected_revision=1)
    conn.rollback.assert_not_called()


def test_terminal_run_cannot_resurrect():
    conn = connection()
    cancelled = run().cancel(1)
    conn.execute.return_value.mappings.return_value.one_or_none.return_value = row(cancelled)
    candidate = replace(run().start(1, "attempt"), run_revision=3)
    with pytest.raises(VideoError, match="VIDEO_TERMINAL_RUN"):
        VideoRunRows(conn, "school").save(candidate, expected_revision=2)


@pytest.mark.parametrize("changes", [{"organization_id": "other"}, {"run_revision": 2}])
def test_insert_initial_scope_revision(changes):
    conn = connection()
    value = run()
    value = (replace(value, pin=replace(value.pin, organization_id="other"))
             if "organization_id" in changes else replace(value, **changes))
    with pytest.raises(VideoError, match="VIDEO_INVALID_INITIAL_RUN"):
        VideoRunRows(conn, "school").insert(value)
    conn.execute.assert_not_called()


def test_insert_conflict_not_swallowed_or_committed():
    conn = connection()
    conn.execute.side_effect = IntegrityError("synthetic", {}, Exception("synthetic"))
    with pytest.raises(VideoError, match="VIDEO_WRITE_CONFLICT"):
        VideoRunRows(conn, "school").insert(run())
    conn.commit.assert_not_called()
    conn.rollback.assert_not_called()


@pytest.mark.parametrize("changes", [
    {"organization_id": "other"}, {"session_id": "other"}, {"pin_digest": "b" * 64},
])
def test_receipt_cannot_point_to_foreign_or_wrong_pin(changes):
    conn = connection()
    with pytest.raises(VideoError, match="VIDEO_RECEIPT_MISMATCH"):
        VideoRunRows(conn, "school").put_receipt(receipt(**changes))
    assert conn.execute.call_count == 1


def test_frozen_migration_matches_metadata_and_has_no_foreign_owner_fk():
    path = (Path(__file__).resolve().parents[2]
            / "alembic/versions/20261018_kv_0001_knowledge_video.py")
    spec = importlib.util.spec_from_file_location("owned08_migration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def normalize(value):
        return re.sub(r"\s+", "", value).lower().strip(";")

    frozen = [normalize(sql) for sql in module.DDL.split(";") if sql.strip()]
    current = [normalize(str(CreateTable(table).compile(dialect=dialect())))
               for table in METADATA.sorted_tables]
    assert frozen == current
    assert module.branch_labels == ("knowledge_video",) and module.down_revision is None
    assert all(fk.target_fullname.startswith("knowledge_video.")
               for table in METADATA.tables.values() for fk in table.foreign_keys)
    assert RUN.schema == "knowledge_video"


def test_encoder_rechecks_domain_even_if_object_was_forced_mutable():
    value = run()
    object.__setattr__(value, "run_revision", True)
    with pytest.raises(VideoError, match="VIDEO_STORAGE_CORRUPT"):
        encode_run(value)
