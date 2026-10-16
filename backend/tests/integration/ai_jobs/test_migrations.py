"""BE2-01 Phase B, batch B2: ``ai_jobs`` schema, Alembic branch and constraint checks.

Offline checks (script graph, metadata shape, generated SQL) need no database. Checks marked
``requires_postgres`` run only against a disposable PostgreSQL 17 database (see conftest);
skipped means NOT_RUN. Acceptance: FEAT-044 PHASE_B_PLAN.md rev3 B2 exit, B-01 (schema level),
B-07 (semantic key), B-11 (migration matrix).
"""

from __future__ import annotations

import io
import json
import re
from collections.abc import Callable, Iterator
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import Script, ScriptDirectory
from alembic.util.exc import CommandError
from sketch2life.contracts.schemas.ai_jobs import CreateAiJobCommandV1
from sketch2life.infrastructure.ai_jobs.harness import build_fixture_harness
from sketch2life.infrastructure.ai_jobs.sql import tables as t
from sketch2life.infrastructure.config.settings import get_core_database_settings
from sqlalchemy import Connection, String, create_engine, insert, select, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import URL
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import NullPool
from sqlalchemy.schema import CreateTable

BACKEND = Path(__file__).resolve().parents[3]
AI_HEAD = "20261015_ai_0001"
BE1_CHAIN = ("20261014_0004", "20261014_0003", "20261014_0002", "20261014_0001")
AI_TABLES = {
    "job",
    "attempt",
    "command_receipt",
    "semantic_request",
    "completion_receipt",
    "cancellation_notice",
    "outbox",
}
SHA_A = "a" * 64
SHA_B = "b" * 64
NOW = datetime(2026, 10, 15, 12, 0, tzinfo=UTC)


def _opaque_id_command(length: int) -> CreateAiJobCommandV1:
    return CreateAiJobCommandV1.model_validate(
        {
            "job_type": "j" * length,
            "target_id": "target_synthetic",
            "purpose_code": "p" * length,
            "session_id": None,
            "subject_refs": ("subject_synthetic_1",),
            "request_ref": {
                "request_id": "req_1",
                "request_revision": 1,
                "input_hash": SHA_A,
                "context_revision": 0,
            },
        }
    )


def _config(monkeypatch: pytest.MonkeyPatch, url: str, buffer: io.StringIO | None = None) -> Config:
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", url)
    get_core_database_settings.cache_clear()
    cfg = Config(str(BACKEND / "alembic.ini"), output_buffer=buffer)
    cfg.set_main_option("script_location", str(BACKEND / "alembic"))
    return cfg


@pytest.fixture
def offline_config(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[Config, io.StringIO]]:
    buffer = io.StringIO()
    # Offline SQL generation never connects; the URL only selects the PostgreSQL dialect.
    yield (
        _config(monkeypatch, "postgresql+psycopg://offline@offline.invalid/offline", buffer),
        buffer,
    )
    get_core_database_settings.cache_clear()


def _without_comments(sql: str) -> str:
    return "\n".join(line for line in sql.splitlines() if not line.lstrip().startswith("--"))


def _check_constraint_names() -> set[str]:
    """Final CHECK names as rendered by the naming convention in PostgreSQL DDL."""

    names: set[str] = set()
    for table in t.AI_JOBS_METADATA.sorted_tables:
        dialect = postgresql.dialect()  # type: ignore[no-untyped-call]
        ddl = str(CreateTable(table).compile(dialect=dialect))
        names.update(re.findall(r"CONSTRAINT (\S+) CHECK", ddl))
    return names


# ----------------------------------------------------------------------------- offline checks
def test_script_graph_keeps_be1_history_and_adds_independent_ai_jobs_branch(
    offline_config: tuple[Config, io.StringIO],
) -> None:
    script = ScriptDirectory.from_config(offline_config[0])
    assert set(script.get_heads()) == {BE1_CHAIN[0], AI_HEAD}

    ai = script.get_revision(AI_HEAD)
    assert ai is not None
    assert ai.branch_labels == {"ai_jobs"}
    assert ai.down_revision is None and not ai.dependencies

    chain: list[str] = []
    current: Script | None = script.get_revision(BE1_CHAIN[0])
    while current is not None:
        chain.append(current.revision)
        assert AI_HEAD not in (current.dependencies or ())
        down = current.down_revision
        assert down is None or isinstance(down, str)
        current = script.get_revision(down) if down else None
    assert tuple(chain) == BE1_CHAIN
    root = script.get_revision(BE1_CHAIN[-1])
    assert root is not None and root.branch_labels == {"be1_core"}


def test_plain_head_is_ambiguous_and_refused(offline_config: tuple[Config, io.StringIO]) -> None:
    with pytest.raises(CommandError, match="Multiple head revisions"):
        command.upgrade(offline_config[0], "head", sql=True)


def test_metadata_is_scoped_to_ai_jobs_without_foreign_owner_keys() -> None:
    assert {table.name for table in t.AI_JOBS_METADATA.sorted_tables} == AI_TABLES
    for table in t.AI_JOBS_METADATA.sorted_tables:
        assert table.schema == "ai_jobs"
        for fk in table.foreign_keys:
            assert fk.column.table.schema == "ai_jobs"


def _unique_column_sets(table_name: str) -> list[set[str]]:
    table = t.AI_JOBS_METADATA.tables[f"ai_jobs.{table_name}"]
    sets = [{c.name for c in table.primary_key.columns}]
    for constraint in table.constraints:
        if constraint.__class__.__name__ == "UniqueConstraint":
            sets.append({c.name for c in constraint.columns})  # type: ignore[attr-defined]
    sets += [{c.name for c in index.columns} for index in table.indexes if index.unique]
    return sets


def test_semantic_identity_is_only_the_canonical_key() -> None:
    assert _unique_column_sets("semantic_request") == [{"semantic_key_sha256"}]
    session = t.semantic_request.c.session_id
    assert session.nullable
    for table in t.AI_JOBS_METADATA.sorted_tables:
        for columns in _unique_column_sets(table.name):
            assert "session_id" not in columns


def test_command_scope_and_completion_keys() -> None:
    assert [c.name for c in t.command_receipt.primary_key.columns] == [
        "organization_id",
        "principal_id",
        "contract_name",
        "target_id",
        "idempotency_key",
    ]
    assert all(not c.nullable for c in t.command_receipt.primary_key.columns)
    assert [c.name for c in t.completion_receipt.primary_key.columns] == ["job_id", "attempt_id"]
    assert {"job_id", "attempt_number"} in _unique_column_sets("attempt")
    assert {"event_id"} in _unique_column_sets("outbox")


@pytest.mark.parametrize("length", [81, 120])
def test_contract_valid_opaque_ids_fit_metadata_and_migration(
    length: int, offline_config: tuple[Config, io.StringIO]
) -> None:
    candidate = _opaque_id_command(length)
    harness = build_fixture_harness()
    result = harness.service.create_job(
        replace(
            harness.create(job_type=candidate.job_type),
            purpose_code=candidate.purpose_code,
        )
    )
    stored = harness.store.snapshot().jobs[result.job_id]
    assert stored.job_type == candidate.job_type
    assert stored.scope.purpose_code == candidate.purpose_code

    cfg, buffer = offline_config
    command.upgrade(cfg, "ai_jobs@head", sql=True)
    migration_sql = buffer.getvalue()
    for table, values in (
        (t.job, {"job_type": candidate.job_type, "purpose_code": candidate.purpose_code}),
        (
            t.semantic_request,
            {"job_type": candidate.job_type, "purpose_code": candidate.purpose_code},
        ),
        (t.cancellation_notice, {"job_type": candidate.job_type}),
    ):
        ddl = re.search(rf"CREATE TABLE ai_jobs\.{table.name} \((.*?)\n\);", migration_sql, re.S)
        assert ddl is not None
        for name, value in values.items():
            column_type = table.c[name].type
            assert isinstance(column_type, String)
            assert column_type.length is None or len(value) <= column_type.length
            width = re.search(rf"\b{name} VARCHAR\((\d+)\)", ddl.group(1))
            assert width is not None and len(value) <= int(width.group(1))


def test_offline_upgrade_and_downgrade_sql_touch_only_ai_jobs(
    offline_config: tuple[Config, io.StringIO],
) -> None:
    cfg, buffer = offline_config
    command.upgrade(cfg, "ai_jobs@head", sql=True)
    up = buffer.getvalue()
    buffer.seek(0)
    buffer.truncate()
    command.downgrade(cfg, f"{AI_HEAD}:base", sql=True)
    down = buffer.getvalue()

    assert "CREATE SCHEMA ai_jobs" in up
    statements = [s.strip() for s in _without_comments(up).split(";") if s.strip()]
    for statement in statements:
        head = statement.split("(")[0]
        if head.startswith(("CREATE TABLE", "CREATE INDEX", "CREATE UNIQUE INDEX")):
            assert "alembic_version" in head or "ai_jobs." in head, head
        assert not statement.startswith(("DROP", "ALTER")), statement
    assert f"INSERT INTO alembic_version (version_num) VALUES ('{AI_HEAD}')" in up
    for be1_marker in ("be1_", "core_"):
        assert be1_marker not in up and be1_marker not in down

    assert "DROP SCHEMA ai_jobs RESTRICT" in down
    assert {f"DROP TABLE ai_jobs.{name}" for name in AI_TABLES} <= {
        s.strip() for s in _without_comments(down).split(";")
    }
    assert f"DELETE FROM alembic_version WHERE alembic_version.version_num = '{AI_HEAD}'" in down


# --------------------------------------------------------------------------- PostgreSQL checks
pg = pytest.mark.requires_postgres

Run = Callable[[str, str], None]


@pytest.fixture
def migrate(monkeypatch: pytest.MonkeyPatch, disposable_database_url: URL) -> Iterator[Run]:
    rendered = disposable_database_url.render_as_string(hide_password=False)
    cfg = _config(monkeypatch, rendered)

    def run(direction: str, target: str) -> None:
        getattr(command, direction)(cfg, target)

    yield run
    get_core_database_settings.cache_clear()


@pytest.fixture
def connect(disposable_database_url: URL) -> Iterator[Callable[[], Connection]]:
    engines = []

    def open_connection() -> Connection:
        engine = create_engine(disposable_database_url, poolclass=NullPool, hide_parameters=True)
        engines.append(engine)
        return engine.connect()

    yield open_connection
    for engine in engines:
        engine.dispose()


def _versions(conn: Connection) -> set[str]:
    return set(conn.execute(text("SELECT version_num FROM alembic_version")).scalars())


def _schema_snapshot(conn: Connection, schema: str) -> dict[str, list[Any]]:
    columns = conn.execute(
        text(
            "SELECT table_name, column_name, data_type, is_nullable, column_default "
            "FROM information_schema.columns WHERE table_schema = :s "
            "ORDER BY table_name, column_name"
        ),
        {"s": schema},
    ).all()
    constraints = conn.execute(
        text(
            "SELECT conrelid::regclass::text, conname, pg_get_constraintdef(oid) "
            "FROM pg_constraint WHERE connamespace = CAST(:s AS regnamespace) ORDER BY 1, 2"
        ),
        {"s": schema},
    ).all()
    indexes = conn.execute(
        text(
            "SELECT tablename, indexname, indexdef FROM pg_indexes "
            "WHERE schemaname = :s ORDER BY 1, 2"
        ),
        {"s": schema},
    ).all()
    return {
        "columns": [tuple(r) for r in columns],
        "constraints": [tuple(r) for r in constraints],
        "indexes": [tuple(r) for r in indexes],
    }


def _schema_exists(conn: Connection, schema: str) -> bool:
    return bool(
        conn.execute(
            text("SELECT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = :s)"), {"s": schema}
        ).scalar()
    )


@pg
def test_fresh_database_upgrade_heads_creates_both_module_branches(
    migrate: Run, connect: Callable[[], Connection]
) -> None:
    migrate("upgrade", "heads")
    with connect() as conn:
        assert _versions(conn) == {BE1_CHAIN[0], AI_HEAD}
        ai_tables = set(
            conn.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'ai_jobs'")
            ).scalars()
        )
        assert ai_tables == AI_TABLES
        public_tables = set(
            conn.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            ).scalars()
        )
        assert "be1_organizations" in public_tables and "alembic_version" in public_tables
        assert not any(name in public_tables for name in AI_TABLES)


@pg
def test_existing_be1_database_gains_ai_jobs_without_changing_be1(
    migrate: Run, connect: Callable[[], Connection]
) -> None:
    migrate("upgrade", "be1_core@head")
    with connect() as conn:
        before = _schema_snapshot(conn, "public")
        assert _versions(conn) == {BE1_CHAIN[0]}
        assert not _schema_exists(conn, "ai_jobs")
    migrate("upgrade", "ai_jobs@head")
    with connect() as conn:
        assert _schema_snapshot(conn, "public") == before
        assert _versions(conn) == {BE1_CHAIN[0], AI_HEAD}


@pg
def test_rerun_of_heads_is_a_no_op(migrate: Run, connect: Callable[[], Connection]) -> None:
    migrate("upgrade", "heads")
    with connect() as conn:
        first = (
            _versions(conn),
            _schema_snapshot(conn, "ai_jobs"),
            _schema_snapshot(conn, "public"),
        )
    migrate("upgrade", "heads")
    migrate("upgrade", "ai_jobs@head")
    with connect() as conn:
        again = (
            _versions(conn),
            _schema_snapshot(conn, "ai_jobs"),
            _schema_snapshot(conn, "public"),
        )
    assert again == first


@pg
def test_downgrade_removes_only_ai_jobs_on_disposable_database(
    migrate: Run, connect: Callable[[], Connection]
) -> None:
    migrate("upgrade", "heads")
    with connect() as conn:
        public_before = _schema_snapshot(conn, "public")
        ai_before = _schema_snapshot(conn, "ai_jobs")
    migrate("downgrade", "ai_jobs@base")
    with connect() as conn:
        assert not _schema_exists(conn, "ai_jobs")
        assert _versions(conn) == {BE1_CHAIN[0]}
        assert _schema_snapshot(conn, "public") == public_before
    migrate("upgrade", "ai_jobs@head")
    with connect() as conn:
        assert _schema_snapshot(conn, "ai_jobs") == ai_before
        assert _versions(conn) == {BE1_CHAIN[0], AI_HEAD}


@pg
def test_migration_matches_tables_metadata(migrate: Run, connect: Callable[[], Connection]) -> None:
    migrate("upgrade", "heads")
    with connect() as conn:
        context = MigrationContext.configure(
            conn,
            opts={
                "compare_type": True,
                "include_schemas": True,
                "include_name": lambda name, type_, _parents: (
                    type_ != "schema" or name == "ai_jobs"
                ),
            },
        )
        assert compare_metadata(context, t.AI_JOBS_METADATA) == []
        checks = set(
            conn.execute(
                text(
                    "SELECT conname FROM pg_constraint WHERE contype = 'c' "
                    "AND connamespace = 'ai_jobs'::regnamespace"
                )
            ).scalars()
        )
    assert checks == _check_constraint_names()


@pg
def test_introspected_keys_indexes_and_null_semantics(
    migrate: Run, connect: Callable[[], Connection]
) -> None:
    migrate("upgrade", "heads")
    with connect() as conn:
        keys = {
            (row[0], row[1]): row[2]
            for row in conn.execute(
                text(
                    "SELECT conrelid::regclass::text, contype, "
                    "array_agg(a.attname ORDER BY k.ord) "
                    "FROM pg_constraint c "
                    "CROSS JOIN LATERAL unnest(c.conkey) WITH ORDINALITY AS k(attnum, ord) "
                    "JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k.attnum "
                    "WHERE c.connamespace = 'ai_jobs'::regnamespace AND c.contype IN ('p') "
                    "GROUP BY 1, 2, c.oid"
                )
            )
        }
        assert keys[("ai_jobs.semantic_request", "p")] == ["semantic_key_sha256"]
        assert keys[("ai_jobs.command_receipt", "p")] == [
            "organization_id",
            "principal_id",
            "contract_name",
            "target_id",
            "idempotency_key",
        ]
        assert keys[("ai_jobs.completion_receipt", "p")] == ["job_id", "attempt_id"]

        unique_defs = (
            conn.execute(
                text(
                    "SELECT indexdef FROM pg_indexes WHERE schemaname = 'ai_jobs' "
                    "AND indexdef LIKE 'CREATE UNIQUE%'"
                )
            )
            .scalars()
            .all()
        )
        assert not any("session_id" in d for d in unique_defs)
        semantic_unique = [d for d in unique_defs if "semantic_request" in d]
        assert semantic_unique == [
            "CREATE UNIQUE INDEX pk_semantic_request ON ai_jobs.semantic_request "
            "USING btree (semantic_key_sha256)"
        ]
        outbox_event = [d for d in unique_defs if "uq_outbox_event_id" in d]
        assert outbox_event and "WHERE ((kind)::text <> 'dispatch'::text)" in outbox_event[0]

        foreign_targets = set(
            conn.execute(
                text(
                    "SELECT confrelid::regclass::text FROM pg_constraint "
                    "WHERE contype = 'f' AND connamespace = 'ai_jobs'::regnamespace"
                )
            ).scalars()
        )
        assert foreign_targets == {"ai_jobs.job", "ai_jobs.attempt"}


# ------------------------------------------------------------------ constraint behaviour checks
def _job(job_id: str = "job_b2_1", **changes: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "job_id": job_id,
        "organization_id": "org_synthetic",
        "job_type": "sketch_assist",
        "job_revision": 1,
        "state": "queued",
        "session_id": None,
        "subject_refs": ["subject_synthetic_1"],
        "purpose_code": "PURPOSE_SYNTHETIC",
        "target_id": "target_synthetic",
        "request_ref": {"request_id": "req_1", "request_revision": 1},
        "correlation_id": "corr_1",
        "policy_snapshot_id": "fixture.job_retry.v0",
        "policy_snapshot": {"max_attempts": 3},
        "progress": {"kind": "unknown"},
        "created_at": NOW,
        "updated_at": NOW,
    }
    row.update(changes)
    return row


def _attempt(
    attempt_id: str = "att_b2_1", job_id: str = "job_b2_1", number: int = 1
) -> dict[str, Any]:
    return {
        "attempt_id": attempt_id,
        "job_id": job_id,
        "attempt_number": number,
        "request_ref": {"request_id": "req_1"},
        "created_at": NOW,
    }


def _semantic(key: str, session_id: str | None = None) -> dict[str, Any]:
    return {
        "semantic_key_sha256": key,
        "organization_id": "org_synthetic",
        "job_type": "sketch_assist",
        "request_id": "req_1",
        "request_revision": 1,
        "input_hash": SHA_A,
        "context_revision": 0,
        "target_id": "target_synthetic",
        "purpose_code": "PURPOSE_SYNTHETIC",
        "session_id": session_id,
        "subject_refs": ["subject_synthetic_1"],
        "job_id": "job_b2_1",
        "created_at": NOW,
    }


def _receipt(key: str = "idem_1", fingerprint: str = SHA_A) -> dict[str, Any]:
    return {
        "organization_id": "org_synthetic",
        "principal_id": "teacher_synthetic",
        "contract_name": "CreateAiJob",
        "target_id": "target_synthetic",
        "idempotency_key": key,
        "fingerprint": fingerprint,
        "job_id": "job_b2_1",
        "outcome": "created",
        "job_revision_at_commit": 1,
        "recorded_at": NOW,
    }


def _outbox(
    message_id: str, kind: str = "dispatch", event_id: str | None = None, **changes: Any
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "message_id": message_id,
        "kind": kind,
        "event_id": event_id,
        "organization_id": "org_synthetic",
        "job_id": "job_b2_1",
        "attempt_id": "att_b2_1",
        "payload": {"job_type": "sketch_assist"},
        "available_at": NOW,
        "created_at": NOW,
    }
    row.update(changes)
    return row


def _violates(conn: Connection, statement: Any, constraint: str) -> None:
    savepoint = conn.begin_nested()
    with pytest.raises(IntegrityError) as caught:
        conn.execute(statement)
    savepoint.rollback()
    assert caught.value.orig is not None
    assert caught.value.orig.diag.constraint_name == constraint  # type: ignore[attr-defined]


@pg
@pytest.mark.parametrize("length", [81, 120])
def test_contract_valid_opaque_ids_round_trip_all_five_columns(
    length: int, migrate: Run, connect: Callable[[], Connection]
) -> None:
    candidate = _opaque_id_command(length)
    migrate("upgrade", "heads")
    with connect() as conn, conn.begin():
        conn.execute(
            insert(t.job).values(
                _job(job_type=candidate.job_type, purpose_code=candidate.purpose_code)
            )
        )
        semantic = _semantic(SHA_A)
        semantic.update(job_type=candidate.job_type, purpose_code=candidate.purpose_code)
        conn.execute(insert(t.semantic_request).values(semantic))
        conn.execute(
            insert(t.cancellation_notice).values(
                notice_id="notice_synthetic",
                organization_id="org_synthetic",
                reason_code="CONSENT_REVOKED",
                job_type=candidate.job_type,
                status="COMPLETE",
                applied_count=0,
                recorded_at=NOW,
            )
        )

    with connect() as conn:
        expected = (candidate.job_type, candidate.purpose_code)
        assert tuple(conn.execute(select(t.job.c.job_type, t.job.c.purpose_code)).one()) == expected
        assert (
            tuple(
                conn.execute(
                    select(t.semantic_request.c.job_type, t.semantic_request.c.purpose_code)
                ).one()
            )
            == expected
        )
        assert (
            conn.execute(select(t.cancellation_notice.c.job_type)).scalar_one()
            == candidate.job_type
        )


@pg
def test_constraints_reject_invalid_and_duplicate_rows(
    migrate: Run, connect: Callable[[], Connection]
) -> None:
    migrate("upgrade", "heads")
    with connect() as conn, conn.begin():
        conn.execute(insert(t.job).values(_job()))
        conn.execute(insert(t.attempt).values(_attempt()))
        conn.execute(insert(t.semantic_request).values(_semantic(SHA_A)))
        conn.execute(insert(t.command_receipt).values(_receipt()))

        _violates(conn, insert(t.job).values(_job("job_bad", state="stale")), "ck_job_state_data25")
        _violates(
            conn, insert(t.job).values(_job("job_bad", job_revision=0)), "ck_job_revision_positive"
        )
        _violates(
            conn,
            insert(t.attempt).values(_attempt("att_dup", number=1)),
            "uq_attempt_job_id_attempt_number",
        )
        # Semantic dedup is the canonical key only: same raw columns with NULL session and a
        # different canonical key are distinct rows; the same canonical key is a conflict.
        conn.execute(insert(t.semantic_request).values(_semantic(SHA_B)))
        _violates(
            conn,
            insert(t.semantic_request).values(_semantic(SHA_A, "session_x")),
            "pk_semantic_request",
        )
        _violates(
            conn,
            insert(t.semantic_request).values(_semantic("NOT-HEX")),
            "ck_semantic_request_key_sha256",
        )
        _violates(
            conn,
            insert(t.command_receipt).values(_receipt(fingerprint=SHA_B)),
            "pk_command_receipt",
        )
        conn.execute(insert(t.command_receipt).values(_receipt("idem_2")))

        conn.execute(
            insert(t.completion_receipt).values(
                job_id="job_b2_1",
                attempt_id="att_b2_1",
                receipt_id="rcpt_1",
                fingerprint=SHA_A,
                disposition="accepted",
                job_revision_after=2,
                recorded_at=NOW,
            )
        )
        _violates(
            conn,
            insert(t.completion_receipt).values(
                job_id="job_b2_1",
                attempt_id="att_b2_1",
                receipt_id="rcpt_2",
                fingerprint=SHA_B,
                disposition="accepted",
                job_revision_after=2,
                recorded_at=NOW,
            ),
            "pk_completion_receipt",
        )
        _violates(
            conn,
            insert(t.cancellation_notice).values(
                notice_id="n1",
                organization_id="org_synthetic",
                reason_code="CONSENT_REVOKED",
                status="PENDING",
                applied_count=0,
                recorded_at=NOW,
            ),
            "ck_cancellation_notice_status_complete",
        )

        conn.execute(insert(t.outbox).values(_outbox("msg_1")))
        conn.execute(insert(t.outbox).values(_outbox("msg_2")))
        conn.execute(insert(t.outbox).values(_outbox("msg_a1", "audit", SHA_A, attempt_id=None)))
        _violates(
            conn, insert(t.outbox).values(_outbox("msg_a2", "audit", SHA_A)), "uq_outbox_event_id"
        )
        _violates(
            conn,
            insert(t.outbox).values(_outbox("msg_a3", "quarantine")),
            "ck_outbox_side_effect_event_id",
        )
        _violates(
            conn,
            insert(t.outbox).values(_outbox("msg_3", payload={"capability": "x"})),
            "ck_outbox_payload_token_free",
        )
        _violates(
            conn,
            insert(t.outbox).values(_outbox("msg_4", lease_owner="worker")),
            "ck_outbox_lease_pair",
        )
        _violates(
            conn,
            insert(t.outbox).values(_outbox("msg_5", attempt_id=None)),
            "ck_outbox_dispatch_identity",
        )


@pg
def test_committed_rows_are_read_back_by_a_new_connection(
    migrate: Run, connect: Callable[[], Connection]
) -> None:
    """B-01 at schema level only: committed rows survive closing every connection/engine.
    Server restart and crash windows are B6 (`test_restart_recovery.py`), not claimed here."""

    migrate("upgrade", "heads")
    tables = (t.job, t.attempt, t.semantic_request, t.command_receipt, t.outbox)
    with connect() as conn, conn.begin():
        conn.execute(insert(t.job).values(_job()))
        conn.execute(insert(t.attempt).values(_attempt()))
        conn.execute(insert(t.semantic_request).values(_semantic(SHA_A)))
        conn.execute(insert(t.command_receipt).values(_receipt()))
        conn.execute(insert(t.outbox).values(_outbox("msg_1")))
    with connect() as conn:
        written = {
            table.name: json.dumps(
                [dict(r._mapping) for r in conn.execute(select(table))], default=str
            )
            for table in tables
        }
    with connect() as conn:
        reread = {
            table.name: json.dumps(
                [dict(r._mapping) for r in conn.execute(select(table))], default=str
            )
            for table in tables
        }
    assert reread == written
    assert all(json.loads(value) for value in written.values())
