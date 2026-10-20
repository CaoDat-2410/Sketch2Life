"""Closed codec/mock rows/offline migrations, NOT actual PG transaction/trigger proof."""

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

from sketch2life.application.activity_execution import event_id
from sketch2life.application.ports.activity_execution import OutcomeAck, OutcomeEvent, Receipt
from sketch2life.domain.activity_execution.model import Action, State, digest
from sketch2life.domain.knowledge_video.model import VideoError
from sketch2life.infrastructure.activity_execution.codec import decode, encode
from sketch2life.infrastructure.activity_execution.sql import (
    ActivityRows,
    SqlActivityStore,
    validate_change,
)
from sketch2life.infrastructure.activity_execution.tables import METADATA
from tests.activity_execution_fixtures import NOW, actor, assignment, prepared, ref, select


def event():
    row = prepared(State.COMPLETED)
    return OutcomeEvent(event_id(row), row, NOW, "teacher")


def connection(row=None):
    conn = Mock()
    conn.dialect.name = "postgresql"
    conn.in_transaction.return_value = True
    conn.execute.return_value.mappings.return_value.one_or_none.return_value = row
    conn.execute.return_value.rowcount = 1
    return conn


def head_row(row=None):
    row = row or assignment()
    return dict(
        organization_id="school",
        session_id="session",
        assignment_id=row.assignment_id,
        revision=row.revision,
        payload=encode("assignment", row),
    )


@pytest.mark.parametrize(
    "kind,value",
    [
        ("assignment", assignment()),
        ("assignment", prepared()),
        ("assignment", prepared(State.RUNNING)),
        ("assignment", prepared(State.COMPLETED)),
        ("receipt", Receipt(actor(), select().fingerprint(), assignment())),
        ("event", event()),
        ("ack", OutcomeAck(event().event_id, event().fingerprint(), ref("ack"))),
    ],
)
def test_closed_json_roundtrip_nested_tuple_datetime_and_exact_domain(kind, value):
    assert decode(kind, json.loads(json.dumps(encode(kind, value)))) == value


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p.update(format="future"),
        lambda p: p.update(kind="ack"),
        lambda p: p.update(extra=True),
        lambda p: p["value"].update(revision=True),
        lambda p: p["value"].update(state="completed"),
        lambda p: p["value"].update(extra=True),
        lambda p: p["value"].update(created_at="naive"),
        lambda p: p["value"]["audience"]["children"][0].update(age_months=True),
        lambda p: p["value"]["source"]["source_ref"].update(hash="bad"),
        lambda p: p["value"]["source"].update(instructions=" "),
    ],
)
def test_corrupt_envelope_or_graph_rejected(mutate):
    payload = copy.deepcopy(encode("assignment", assignment()))
    mutate(payload)
    with pytest.raises(VideoError, match="STORAGE_CORRUPT"):
        decode("assignment", payload)


@pytest.mark.parametrize(
    "field,value",
    [
        ("organization_id", "foreign"),
        ("session_id", "foreign"),
        ("assignment_id", "foreign"),
        ("revision", True),
        ("revision", 2),
    ],
)
def test_relational_scope_revision_agrees_with_payload(field, value):
    row = head_row()
    row[field] = value
    with pytest.raises(VideoError, match="STORAGE_CORRUPT"):
        ActivityRows(connection(row), "school", "session").load("assignment")


def test_query_scope_and_head_roundtrip_requires_pg_tx():
    conn = connection(head_row())
    rows = ActivityRows(conn, "school", "session")
    assert rows.load("assignment") == assignment()
    params = conn.execute.call_args.args[0].compile(dialect=postgresql.dialect()).params
    assert set(params.values()) == {"school", "session", "assignment"}
    conn.in_transaction.return_value = False
    with pytest.raises(VideoError, match="TRANSACTION_REQUIRED"):
        rows.load("assignment")
    conn.dialect.name = "sqlite"
    with pytest.raises(VideoError, match="POSTGRESQL_REQUIRED"):
        ActivityRows(conn, "school", "session")


def test_initial_write_history_receipt_no_cross_owner_commit():
    conn = connection()
    ActivityRows(conn, "school", "session").write(
        None, Receipt(actor(), select().fingerprint(), assignment()), None
    )
    assert [call.args[0].table.name for call in conn.execute.call_args_list[1:]] == [
        "assignment",
        "history",
        "receipt",
    ]
    conn.commit.assert_not_called()


def test_invalid_transition_and_terminal_mutation_rejected_before_sql():
    row = assignment()
    with pytest.raises(VideoError):
        validate_change(row, replace(row, revision=2, source=replace(row.source, title="Changed")))
    done = prepared(State.COMPLETED)
    with pytest.raises(VideoError):
        validate_change(done, replace(done, revision=done.revision + 1))


def test_exact_pure_transition_matches_rows_and_cas_no_append_on_conflict():
    before, after = assignment(), prepared()
    validate_change(before, after)
    conn = connection(head_row(before))
    conn.execute.return_value.rowcount = 0
    with pytest.raises(VideoError, match="STALE_REVISION"):
        ActivityRows(conn, "school", "session").write(
            before, Receipt(actor(), digest("confirm"), after), None
        )
    assert conn.execute.call_count == 2


def test_unique_error_caller_rolls_back_no_partial_commit():
    conn = connection()
    result = conn.execute.return_value
    conn.execute.side_effect = [result, IntegrityError("private", {}, Exception("secret"))]
    with pytest.raises(VideoError, match="WRITE_CONFLICT"):
        ActivityRows(conn, "school", "session").write(
            None, Receipt(actor(), select().fingerprint(), assignment()), None
        )
    conn.commit.assert_not_called()


def test_exact_ack_read_binding_and_immutable_replay():
    e = event()
    ack = OutcomeAck(e.event_id, e.fingerprint(), ref("ack"))
    conn = connection()
    rows = ActivityRows(conn, "school", "session")
    rows.event = Mock(return_value=(e, None))
    rows.acknowledge(e, ack)
    assert conn.execute.call_args.args[0].table.name == "ack"
    conn.reset_mock()
    rows.event.return_value = (e, ack)
    rows.acknowledge(e, ack)
    conn.execute.assert_not_called()
    with pytest.raises(VideoError, match="ACK_CONFLICT"):
        rows.acknowledge(e, replace(ack, receipt_ref=ref("different")))
    with pytest.raises(VideoError, match="INVALID_ACK"):
        rows.acknowledge(e, replace(ack, event_digest="f" * 64))


def migration():
    path = (
        Path(__file__).resolve().parents[2]
        / "alembic/versions/20261019_ae_0001_activity_execution.py"
    )
    spec = importlib.util.spec_from_file_location("ae11_migration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_frozen_migration_own_five_tables_no_cascade_or_cross_owner_fk():
    output = io.StringIO()
    context = MigrationContext.configure(
        dialect_name="postgresql", opts={"as_sql": True, "output_buffer": output}
    )
    with Operations.context(context):
        migration().upgrade()
        migration().downgrade()
    sql = output.getvalue()
    assert sql.count("CREATE TABLE activity_execution.") == len(METADATA.tables) == 5
    assert sql.count("DROP TABLE activity_execution.") == sql.count("CREATE TRIGGER") == 5
    assert "CASCADE" not in sql and "learning_content." not in sql
    assert all(not table.foreign_keys for table in METADATA.tables.values())


def test_own_store_scope_lock_single_uow_not_actual_owner_fence():
    engine = Mock()
    engine.dialect.name = "postgresql"
    conn = connection()
    engine.begin.return_value.__enter__ = Mock(return_value=conn)
    engine.begin.return_value.__exit__ = Mock(return_value=False)
    with SqlActivityStore(engine).transaction("school", "session") as rows:
        assert rows.conn is conn
    sql, params = conn.execute.call_args.args
    assert "pg_advisory_xact_lock" in str(sql) and len(params["scope"]) == 64


def test_terminal_event_actor_must_match_authenticated_command_receipt():
    before = prepared(State.RUNNING)
    after = before.transition(Action.FINISH, before.revision, NOW)
    conn = connection(head_row(before))
    receipt = Receipt(actor(principal_id="teacher2"), digest("finish"), after)
    with pytest.raises(VideoError, match="INVALID_EVENT"):
        ActivityRows(conn, "school", "session").write(
            before, receipt, OutcomeEvent(event_id(after), after, NOW, "teacher")
        )
    conn.execute.assert_not_called()
