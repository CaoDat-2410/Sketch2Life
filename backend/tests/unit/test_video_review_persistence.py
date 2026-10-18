"""Closed codec, mock SQL and offline migration; NOT actual PostgreSQL evidence."""

import copy
import importlib.util
import io
import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError

from sketch2life.application.ports.video_review_lifecycle import ReviewChangeReceipt
from sketch2life.application.ports.video_review_write import ReviewWriteContext
from sketch2life.domain.knowledge_video.model import VideoError
from sketch2life.domain.video_review.model import ReviewHead
from sketch2life.domain.video_review.playback import PlaybackIntent, PlaybackRequest
from sketch2life.infrastructure.video_review.codec import decode, encode
from sketch2life.infrastructure.video_review.sql import (
    PlaybackRows,
    ReviewRows,
    SqlVideoPlaybackStore,
    SqlVideoReviewStore,
)
from sketch2life.infrastructure.video_review.tables import METADATA, SCHEMA
from tests.unit.test_video_playback import receipt as play_receipt
from tests.unit.test_video_review_domain import NOW, approved
from tests.unit.test_video_review_lifecycle import change
from tests.unit.test_video_review_write import execute, setup


def write_receipt():
    h = setup()
    execute(h)
    return next(iter(h.store.receipts.values()))


def change_receipt():
    event = change()
    ctx = ReviewWriteContext("teacher", "school", "session", "video", "change.key", 2)
    return ReviewChangeReceipt(ctx, event.request, event)


def pending():
    head = approved()
    request = PlaybackRequest(head.subject, head.entry.review_id, head.revision, 4)
    return PlaybackIntent("teacher", "key", request, NOW)


def connection(row=None):
    conn = Mock()
    conn.dialect.name = "postgresql"
    conn.in_transaction.return_value = True
    conn.execute.return_value.mappings.return_value.one_or_none.return_value = row
    conn.execute.return_value.rowcount = 1
    return conn


def head_row(head):
    return dict(
        organization_id="school",
        session_id="session",
        video_id="video",
        revision=head.revision,
        subject_digest=head.subject.digest(),
        payload=encode("head", head),
    )


def playback_row(intent):
    return dict(
        organization_id="school",
        session_id="session",
        video_id="video",
        principal_id="teacher",
        client_key="key",
        revision=intent.revision,
        state=intent.state.value,
        payload=encode("playback", intent),
    )


@pytest.mark.parametrize(
    "kind,value",
    [
        ("head", approved()),
        ("head", change().after),
        ("head", change().archived),
        ("write", write_receipt()),
        ("change", change_receipt()),
        ("playback", pending()),
        ("playback", pending().settle(play_receipt(pending()))),
        (
            "playback",
            pending().settle(play_receipt(pending(), accepted=False, session_revision_after=4)),
        ),
    ],
)
def test_closed_json_roundtrip_revalidates_full_native_graph(kind, value):
    payload = json.loads(json.dumps(encode(kind, value)))
    assert decode(kind, payload) == value
    assert "__class__" not in json.dumps(payload)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p.update(format="future"),
        lambda p: p.update(kind="change"),
        lambda p: p.update(extra=True),
        lambda p: p.pop("value"),
        lambda p: p["value"].update(extra=True),
        lambda p: p["value"].pop("subject"),
        lambda p: p["value"].update(revision=True),
        lambda p: p["value"].update(revision="2"),
        lambda p: p["value"].update(applicability="unknown"),
        lambda p: p["value"]["subject"]["artifact"].update(hash="wrong"),
        lambda p: p["value"]["subject"]["audience"].update(group_ids=["group", "group"]),
        lambda p: p["value"]["entry"].update(recorded_at="2026-10-18T00:00:00"),
        lambda p: p["value"]["entry"].update(revision=99),
    ],
)
def test_corrupt_envelope_or_nested_domain_fails_closed(mutate):
    payload = copy.deepcopy(encode("head", approved()))
    mutate(payload)
    with pytest.raises(VideoError, match="VIDEO_REVIEW_STORAGE_CORRUPT"):
        decode("head", payload)


@pytest.mark.parametrize("payload", [None, [], "raw", {}, {"__class__": "os.system"}])
def test_no_arbitrary_type_loading(payload):
    with pytest.raises(VideoError, match="VIDEO_REVIEW_STORAGE_CORRUPT"):
        decode("head", payload)


def test_forged_native_graph_is_not_trusted():
    head = approved()
    object.__setattr__(head, "revision", True)
    with pytest.raises(VideoError, match="VIDEO_REVIEW_STORAGE_CORRUPT"):
        encode("head", head)
    with pytest.raises(VideoError):
        encode("playback", approved())


@pytest.mark.parametrize(
    "field,value",
    [
        ("organization_id", "other"),
        ("session_id", "other"),
        ("video_id", "other"),
        ("revision", 3),
        ("revision", True),
        ("subject_digest", "b" * 64),
    ],
)
def test_head_relational_envelope_cannot_disagree_with_payload(field, value):
    row = head_row(approved())
    row[field] = value
    with pytest.raises(VideoError, match="VIDEO_REVIEW_STORAGE_CORRUPT"):
        ReviewRows(connection(row), "school", "session", "video").head()


def test_head_roundtrip_and_query_scope():
    conn = connection(head_row(approved()))
    assert ReviewRows(conn, "school", "session", "video").head() == approved()
    stmt = conn.execute.call_args.args[0].compile(dialect=postgresql.dialect())
    assert set(stmt.params.values()) == {"school", "session", "video"}


@pytest.mark.parametrize(
    "cls,args",
    [
        (ReviewRows, ("school", "session", "video")),
        (PlaybackRows, ("school", "session")),
    ],
)
def test_requires_postgres_and_explicit_transaction(cls, args):
    conn = connection()
    conn.dialect.name = "sqlite"
    with pytest.raises(VideoError, match="POSTGRESQL_REQUIRED"):
        cls(conn, *args)
    conn.dialect.name = "postgresql"
    conn.in_transaction.return_value = False
    rows = cls(conn, *args)
    with pytest.raises(VideoError, match="TRANSACTION_REQUIRED"):
        rows.head() if cls is ReviewRows else rows.get("teacher", "key")
    conn.execute.assert_not_called()


def test_review_write_emits_head_receipt_history_event_no_commit():
    rec = write_receipt()
    head = ReviewHead(rec.entry.subject, rec.entry.revision, rec.entry)
    conn = connection()
    ReviewRows(conn, "school", "session", "video").write(None, head, rec)
    statements = [c.args[0] for c in conn.execute.call_args_list]
    assert [s.table.name for s in statements[1:]] == ["head", "receipt", "history", "event"]
    conn.commit.assert_not_called()
    conn.rollback.assert_not_called()  # Enclosing UoW owns rollback, never per-row commits.


def test_lifecycle_cas_and_receipt_retains_archive():
    rec = change_receipt()
    conn = connection(head_row(rec.change.before))
    ReviewRows(conn, "school", "session", "video").change(rec)
    statements = [c.args[0] for c in conn.execute.call_args_list]
    assert [s.table.name for s in statements[1:]] == ["head", "receipt", "history", "event"]
    params = statements[2].compile(dialect=postgresql.dialect()).params
    assert decode("change", params["payload"]).change.archived == rec.change.archived


@pytest.mark.parametrize("mode", ["missing", "cas", "integrity"])
def test_change_conflict_never_appends_history_or_event(mode):
    rec = change_receipt()
    conn = connection(None if mode == "missing" else head_row(rec.change.before))
    if mode == "cas":
        conn.execute.return_value.rowcount = 0
    if mode == "integrity":
        result = conn.execute.return_value
        conn.execute.side_effect = [result, IntegrityError("hidden", {}, Exception("private"))]
    with pytest.raises(VideoError, match="STALE_REVISION|WRITE_CONFLICT"):
        ReviewRows(conn, "school", "session", "video").change(rec)
    assert conn.execute.call_count <= 2


@pytest.mark.parametrize("kind", ["write", "change"])
def test_shared_receipt_namespace_rejects_cross_kind(kind):
    conn = connection({"kind": kind})
    rows = ReviewRows(conn, "school", "session", "video")
    with pytest.raises(VideoError, match="IDEMPOTENCY_CONFLICT"):
        (rows.change_receipt if kind == "write" else rows.receipt)("teacher", "key")


@pytest.mark.parametrize(
    "field,value",
    [
        ("video_id", "other"),
        ("principal_id", "other"),
        ("client_key", "other"),
        ("session_id", "other"),
        ("revision", True),
        ("state", "playing"),
    ],
)
def test_playback_relational_scope_and_state_checked(field, value):
    row = playback_row(pending())
    row[field] = value
    with pytest.raises(VideoError, match="STORAGE_CORRUPT"):
        PlaybackRows(connection(row), "school", "session").get("teacher", "key")


def test_playback_pending_insert_and_terminal_cas_append():
    intent = pending()
    conn = connection()
    rows = PlaybackRows(conn, "school", "session")
    rows.insert(intent)
    assert [c.args[0].table.name for c in conn.execute.call_args_list] == [
        "playback",
        "playback_history",
        "event",
    ]
    conn.reset_mock()
    conn.execute.return_value.mappings.return_value.one_or_none.return_value = playback_row(intent)
    rows.save(intent.settle(play_receipt(intent)), expected_revision=1)
    assert [c.args[0].table.name for c in conn.execute.call_args_list[1:]] == [
        "playback",
        "playback_history",
        "event",
    ]
    conn.commit.assert_not_called()


def test_playback_terminal_and_changed_intent_cannot_be_overwritten():
    intent = pending()
    settled = intent.settle(play_receipt(intent))
    rows = PlaybackRows(connection(playback_row(settled)), "school", "session")
    with pytest.raises(VideoError, match="STALE_INTENT"):
        rows.save(settled, expected_revision=2)
    rows = PlaybackRows(connection(playback_row(intent)), "school", "session")
    with pytest.raises(VideoError, match="STALE_INTENT"):
        rows.save(replace(settled, created_at=NOW.replace(year=2025)), expected_revision=1)


@pytest.mark.parametrize("kind", ["write", "change"])
def test_matching_receipt_roundtrip(kind):
    rec = write_receipt() if kind == "write" else change_receipt()
    ctx = rec.context
    row = dict(
        organization_id=ctx.organization_id,
        session_id=ctx.session_id,
        video_id=ctx.video_id,
        principal_id=ctx.principal_id,
        client_key=ctx.client_key,
        kind=kind,
        revision=2 if kind == "write" else 3,
        payload=encode(kind, rec),
    )
    rows = ReviewRows(connection(row), "school", "session", "video")
    read = rows.receipt if kind == "write" else rows.change_receipt
    assert read(ctx.principal_id, ctx.client_key) == rec


@pytest.mark.parametrize(
    "field,value",
    [
        ("kind", "unknown"),
        ("organization_id", "foreign"),
        ("video_id", "foreign"),
        ("principal_id", "foreign"),
        ("client_key", "foreign"),
        ("revision", True),
        ("revision", 99),
        ("payload", {}),
    ],
)
def test_receipt_relational_corruption_fails_closed(field, value):
    rec = write_receipt()
    row = dict(
        organization_id="school",
        session_id="session",
        video_id="video",
        principal_id="teacher",
        client_key="key",
        kind="write",
        revision=2,
        payload=encode("write", rec),
    )
    row[field] = value
    with pytest.raises(VideoError, match="STORAGE_CORRUPT"):
        ReviewRows(connection(row), "school", "session", "video").receipt("teacher", "key")


@pytest.mark.parametrize("mode", ["missing", "cas", "integrity"])
def test_playback_save_conflict_never_appends(mode):
    intent = pending()
    conn = connection(None if mode == "missing" else playback_row(intent))
    if mode == "cas":
        conn.execute.return_value.rowcount = 0
    if mode == "integrity":
        result = conn.execute.return_value
        conn.execute.side_effect = [result, IntegrityError("hidden", {}, Exception("private"))]
    with pytest.raises(VideoError, match="STALE_INTENT|WRITE_CONFLICT"):
        PlaybackRows(conn, "school", "session").save(
            intent.settle(play_receipt(intent)), expected_revision=1
        )
    assert conn.execute.call_count <= 2


@pytest.mark.parametrize("cls", [SqlVideoReviewStore, SqlVideoPlaybackStore])
def test_store_rejects_non_postgres_engine(cls):
    engine = Mock()
    engine.dialect.name = "sqlite"
    with pytest.raises(VideoError, match="POSTGRESQL_REQUIRED"):
        cls(engine)
    engine.begin.assert_not_called()


@pytest.mark.parametrize(
    "store,args",
    [
        (SqlVideoReviewStore, ("school", "session", "video")),
        (SqlVideoPlaybackStore, ("school", "session")),
    ],
)
def test_store_uses_single_uow_and_scoped_advisory_lock(store, args):
    engine = Mock()
    engine.dialect.name = "postgresql"
    conn = connection()
    engine.begin.return_value.__enter__ = Mock(return_value=conn)
    engine.begin.return_value.__exit__ = Mock(return_value=False)
    with store(engine).transaction(*args) as rows:
        assert rows.conn is conn
    engine.begin.assert_called_once_with()
    stmt, params = conn.execute.call_args.args
    assert "pg_advisory_xact_lock" in str(stmt) and len(params["scope"]) == 64


def migration():
    path = Path(__file__).resolve().parents[2] / "alembic/versions/20261018_vr_0001_video_review.py"
    spec = importlib.util.spec_from_file_location("review_migration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_offline_migration_is_owned_frozen_and_downgrade_exact_no_cascade():
    output = io.StringIO()
    context = MigrationContext.configure(
        dialect_name="postgresql", opts={"as_sql": True, "output_buffer": output}
    )
    module = migration()
    with Operations.context(context):
        module.upgrade()
        module.downgrade()
    sql = output.getvalue()
    assert sql.count("CREATE TABLE video_review.") == len(METADATA.tables) == 6
    assert sql.count("DROP TABLE video_review.") == 6
    assert sql.count("CREATE TRIGGER") == 6 and "CASCADE" not in sql
    assert module.down_revision is None and module.branch_labels == (SCHEMA,)
    assert "knowledge_video." not in sql and "learning_content." not in sql


def test_metadata_keys_separate_review_scope_from_session_playback_namespace():
    keys = {t.name: tuple(c.name for c in t.primary_key) for t in METADATA.tables.values()}
    assert keys["receipt"] == (
        "organization_id",
        "session_id",
        "video_id",
        "principal_id",
        "client_key",
    )
    assert keys["playback"] == ("organization_id", "session_id", "principal_id", "client_key")
    assert all(not table.foreign_keys for table in METADATA.tables.values())
