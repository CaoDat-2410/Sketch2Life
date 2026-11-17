"""Mock SQL, closed codec and offline migration. NOT actual PostgreSQL proof."""

import copy
import importlib.util
import io
import json
from pathlib import Path
from unittest.mock import Mock

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError

from sketch2life.domain.knowledge_video.model import VideoError
from sketch2life.domain.video_failure.model import Action
from sketch2life.infrastructure.video_failure.codec import decode, encode
from sketch2life.infrastructure.video_failure.sql import FailureRows, SqlFailureStore
from sketch2life.infrastructure.video_failure.tables import METADATA
from tests.video_failure_fixtures import intent, receipt


def row(i):
    c = i.context
    return dict(
        organization_id=c.organization_id,
        session_id=c.session_id,
        principal_id=c.principal_id,
        client_key=c.client_key,
        disposition_id=i.disposition_id,
        claim_key=i.target.claim_key(),
        revision=i.revision,
        payload=encode(i),
    )


def connection(value=None):
    conn = Mock()
    conn.dialect.name = "postgresql"
    conn.in_transaction.return_value = True
    conn.execute.return_value.mappings.return_value.one_or_none.return_value = value
    conn.execute.return_value.rowcount = 1
    return conn


@pytest.mark.parametrize("action", list(Action))
@pytest.mark.parametrize("confirmed", [False, True])
def test_roundtrip_all_actions_and_pending_receipt_graphs(action, confirmed):
    i = intent(action)
    if confirmed:
        i = i.settle(receipt(i))
    assert decode(json.loads(json.dumps(encode(i)))) == i


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p.update(format="unknown"),
        lambda p: p.update(extra=True),
        lambda p: p.pop("value"),
        lambda p: p["value"].update(revision=True),
        lambda p: p["value"].update(extra=True),
        lambda p: p["value"].update(revision=2),
        lambda p: p["value"]["target"].update(state="running"),
        lambda p: p["value"]["target"].update(pin_digest="url"),
        lambda p: p["value"]["choice"].update(expected_job_revision="9"),
        lambda p: p["value"].update(created_at="2026-10-19T00:00:00"),
        lambda p: p["value"]["context"].update(video_id="foreign"),
        lambda p: p["value"]["target"].update(exhausted_at="future"),
    ],
)
def test_unknown_fields_and_corrupt_native_nested_data_fail_closed(mutate):
    payload = copy.deepcopy(encode(intent()))
    mutate(payload)
    with pytest.raises(VideoError, match="STORAGE_CORRUPT"):
        decode(payload)


@pytest.mark.parametrize("payload", [None, [], {}, "raw", {"__class__": "os.system"}])
def test_no_arbitrary_python_deserialization(payload):
    with pytest.raises(VideoError, match="STORAGE_CORRUPT"):
        decode(payload)


def test_forged_native_values_revalidated_on_encode():
    i = intent()
    object.__setattr__(i.choice, "expected_job_revision", True)
    with pytest.raises(VideoError, match="STORAGE_CORRUPT"):
        encode(i)


@pytest.mark.parametrize(
    "field,value",
    [
        ("organization_id", "foreign"),
        ("session_id", "foreign"),
        ("principal_id", "foreign"),
        ("client_key", "foreign"),
        ("disposition_id", "foreign"),
        ("claim_key", "f" * 64),
        ("revision", True),
        ("revision", 2),
    ],
)
def test_relational_envelope_must_match_closed_payload(field, value):
    data = row(intent())
    data[field] = value
    with pytest.raises(VideoError, match="STORAGE_CORRUPT"):
        FailureRows(connection(data), "school", "session").get("teacher", "key")


def test_get_scope_and_native_roundtrip_no_commit():
    conn = connection(row(intent()))
    assert FailureRows(conn, "school", "session").get("teacher", "key") == intent()
    compiled = conn.execute.call_args.args[0].compile(dialect=postgresql.dialect())
    assert set(compiled.params.values()) == {"school", "session", "teacher", "key"}
    conn.commit.assert_not_called()


def test_requires_postgres_and_explicit_caller_transaction():
    conn = connection()
    conn.dialect.name = "sqlite"
    with pytest.raises(VideoError, match="POSTGRESQL_REQUIRED"):
        FailureRows(conn, "school", "session")
    conn.dialect.name = "postgresql"
    conn.in_transaction.return_value = False
    with pytest.raises(VideoError, match="TRANSACTION_REQUIRED"):
        FailureRows(conn, "school", "session").get("teacher", "key")
    conn.execute.assert_not_called()


def test_insert_head_history_minimal_event_single_uow_no_dispatch():
    conn = connection()
    FailureRows(conn, "school", "session").insert(intent())
    statements = [call.args[0] for call in conn.execute.call_args_list]
    assert [s.table.name for s in statements] == ["intent", "history", "event"]
    params = statements[-1].compile(dialect=postgresql.dialect()).params
    assert set(params) == {
        "organization_id",
        "disposition_id",
        "revision",
        "operation_key",
        "target_digest",
    }
    assert "reason" not in json.dumps(params)
    conn.commit.assert_not_called()


@pytest.mark.parametrize("action", list(Action))
def test_save_exact_original_pending_cas_and_history(action):
    i = intent(action)
    conn = connection(row(i))
    FailureRows(conn, "school", "session").save(i.settle(receipt(i)), expected_revision=1)
    statements = [call.args[0] for call in conn.execute.call_args_list]
    assert [s.table.name for s in statements[1:]] == ["intent", "history", "event"]
    assert 1 in statements[1].compile(dialect=postgresql.dialect()).params.values()


@pytest.mark.parametrize("mode", ["missing", "terminal", "cas", "integrity", "bool"])
def test_save_conflicts_never_append_history(mode):
    i = intent()
    settled = i.settle(receipt(i))
    conn = connection(None if mode == "missing" else row(settled if mode == "terminal" else i))
    if mode == "cas":
        conn.execute.return_value.rowcount = 0
    if mode == "integrity":
        result = conn.execute.return_value
        conn.execute.side_effect = [result, IntegrityError("private", {}, Exception("secret"))]
    with pytest.raises(VideoError, match="STALE_INTENT|CONFLICT"):
        FailureRows(conn, "school", "session").save(
            settled, expected_revision=True if mode == "bool" else 1
        )
    assert conn.execute.call_count <= 2


def test_unique_insert_conflict_caller_must_rollback_no_partial_commit():
    conn = connection()
    conn.execute.side_effect = IntegrityError("private", {}, Exception("secret"))
    with pytest.raises(VideoError, match="CONFLICT"):
        FailureRows(conn, "school", "session").insert(intent())
    assert conn.execute.call_count == 1
    conn.commit.assert_not_called()


def test_wrong_scope_cannot_insert_or_save():
    conn = connection()
    with pytest.raises(VideoError, match="SCOPE_MISMATCH"):
        FailureRows(conn, "foreign", "session").insert(intent())
    conn.execute.assert_not_called()


def test_store_one_begin_and_own_session_lock_not_cross_owner_fence():
    engine = Mock()
    engine.dialect.name = "postgresql"
    conn = connection()
    engine.begin.return_value.__enter__ = Mock(return_value=conn)
    engine.begin.return_value.__exit__ = Mock(return_value=False)
    with SqlFailureStore(engine).transaction("school", "session") as rows:
        assert rows.conn is conn
    sql, params = conn.execute.call_args.args
    assert "pg_advisory_xact_lock" in str(sql) and len(params["scope"]) == 64
    engine.begin.assert_called_once_with()


def migration():
    path = (
        Path(__file__).resolve().parents[2] / "alembic/versions/20261019_vf_0001_video_failure.py"
    )
    spec = importlib.util.spec_from_file_location("vf10_migration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_frozen_own_offline_upgrade_downgrade_and_unique_claim():
    output = io.StringIO()
    context = MigrationContext.configure(
        dialect_name="postgresql", opts={"as_sql": True, "output_buffer": output}
    )
    with Operations.context(context):
        migration().upgrade()
        migration().downgrade()
    sql = output.getvalue()
    assert sql.count("CREATE TABLE video_failure.") == len(METADATA.tables) == 3
    assert sql.count("DROP TABLE video_failure.") == sql.count("CREATE TRIGGER") == 3
    assert "CASCADE" not in sql and "failure_one_winner" in sql
    assert "knowledge_video." not in sql and "ai_jobs." not in sql
    assert all(not table.foreign_keys for table in METADATA.tables.values())
