"""Narrow, fail-closed compatibility for the original Story upload tables.

The original Story and Lesson roots independently claimed the same public
names. Only the exact previously tested Story layout may be renamed; the
transaction retains the tables' OIDs, rows and foreign keys.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection

_OLD_NAMES = ("core_upload_sessions", "core_upload_parts")
_NEW_NAMES = ("storyrun_upload_sessions", "storyrun_upload_parts")
_LEGACY_REVISION = "20261102_story_run_lite"

# Pinned from the original, unmodified migration on a task-owned PostgreSQL 17
# instance. Unknown schemas, indexes, constraints or dependants are rejected.
_LEGACY_SIGNATURE = "7d70ea625e081ad0998cefd903adc949178da71bb88a1a7c15440587acbcd2b2"
_CURRENT_SIGNATURE = "fd3d190327f77323416a0046bfac652aa01e02619a5137f0e6cc691126723ff6"


def _present(connection: Connection, name: str) -> bool:
    result = connection.execute(
        text("SELECT to_regclass(:name) IS NOT NULL"), {"name": f"public.{name}"}
    ).scalar_one()
    return bool(result)


def _schema_snapshot(
    connection: Connection, *, legacy: bool
) -> dict[str, list[list[Any]]]:
    """Collect only schema/catalog metadata, never application data."""
    tables = (
        "'public.core_upload_sessions'::regclass, 'public.core_upload_parts'::regclass"
        if legacy
        else "'public.storyrun_upload_sessions'::regclass, 'public.storyrun_upload_parts'::regclass"
    )
    statements = {
        "columns": f"""
          SELECT t.relname, a.attnum, a.attname, pg_catalog.format_type(a.atttypid,a.atttypmod),
                 a.attnotnull, coalesce(pg_catalog.pg_get_expr(d.adbin,d.adrelid),'')
          FROM pg_catalog.pg_attribute a
          JOIN pg_catalog.pg_class t ON t.oid=a.attrelid
          LEFT JOIN pg_catalog.pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum
          WHERE a.attrelid IN ({tables}) AND a.attnum>0 AND NOT a.attisdropped
          ORDER BY 1,2
        """,
        "constraints": f"""
          SELECT t.relname, c.conname, c.contype::text, pg_catalog.pg_get_constraintdef(c.oid)
          FROM pg_catalog.pg_constraint c JOIN pg_catalog.pg_class t ON t.oid=c.conrelid
          WHERE c.conrelid IN ({tables}) ORDER BY 1,2
        """,
        "indexes": f"""
          SELECT t.relname, i.relname, pg_catalog.pg_get_indexdef(i.oid)
          FROM pg_catalog.pg_index x JOIN pg_catalog.pg_class t ON t.oid=x.indrelid
          JOIN pg_catalog.pg_class i ON i.oid=x.indexrelid
          WHERE x.indrelid IN ({tables}) ORDER BY 1,2
        """,
        "inbound": f"""
          SELECT t.relname, n.nspname, source.relname, c.conname,
                 pg_catalog.pg_get_constraintdef(c.oid)
          FROM pg_catalog.pg_constraint c JOIN pg_catalog.pg_class t ON t.oid=c.confrelid
          JOIN pg_catalog.pg_class source ON source.oid=c.conrelid
          JOIN pg_catalog.pg_namespace n ON n.oid=source.relnamespace
          WHERE c.confrelid IN ({tables}) ORDER BY 1,2,3,4
        """,
        "dependencies": f"""
          SELECT target.relname, d.refobjsubid, d.deptype::text,
                 CASE WHEN d.classid='pg_catalog.pg_class'::regclass
                            AND d.objid=target.reltoastrelid AND d.objsubid=0
                            AND d.deptype='i' AND d.refobjsubid=0
                      THEN 'internal toast table'
                      ELSE pg_catalog.pg_describe_object(d.classid,d.objid,d.objsubid)
                 END
          FROM pg_catalog.pg_depend d JOIN pg_catalog.pg_class target ON target.oid=d.refobjid
          WHERE d.refclassid='pg_catalog.pg_class'::regclass
            AND d.refobjid IN ({tables}) ORDER BY 1,2,3,4
        """,
    }
    return {
        key: [list(row) for row in connection.execute(text(query))]
        for key, query in statements.items()
    }


def _signature(snapshot: dict[str, list[list[Any]]]) -> str:
    payload = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def relocate_story_upload_tables(connection: Connection, *, required: bool) -> None:
    """Move only the pinned historical layout, or verify that no move is needed."""
    if connection.dialect.name != "postgresql":
        raise RuntimeError("Story upload compatibility requires online PostgreSQL")
    old = tuple(_present(connection, name) for name in _OLD_NAMES)
    new = tuple(_present(connection, name) for name in _NEW_NAMES)
    if any(new):
        if not all(new):
            raise RuntimeError("incomplete Story upload destination layout")
        if any(old) and not all(old):
            raise RuntimeError("incomplete public upload layout")
        connection.execute(
            text(
                "LOCK TABLE public.storyrun_upload_sessions, public.storyrun_upload_parts "
                "IN ACCESS EXCLUSIVE MODE NOWAIT"
            )
        )
        if _signature(_schema_snapshot(connection, legacy=False)) != _CURRENT_SIGNATURE:
            raise RuntimeError("Story upload destination schema or dependencies do not match")
        return
    if not any(old):
        if required:
            raise RuntimeError("Story upload tables are missing")
        return
    if not all(old):
        raise RuntimeError("incomplete legacy upload layout")
    # Freeze both relations before checking signatures and dependencies: concurrent
    # DDL cannot invalidate the check between inspection and the rename.
    connection.execute(
        text(
            "LOCK TABLE public.core_upload_sessions, public.core_upload_parts "
            "IN ACCESS EXCLUSIVE MODE NOWAIT"
        )
    )
    versions = set(
        connection.execute(text("SELECT version_num FROM public.alembic_version")).scalars()
    )
    if _LEGACY_REVISION not in versions:
        raise RuntimeError("public upload tables are not an applied legacy Story revision")
    if _signature(_schema_snapshot(connection, legacy=True)) != _LEGACY_SIGNATURE:
        raise RuntimeError(
            "legacy Story upload schema or dependencies do not match the verified layout"
        )
    for statement in (
        'ALTER TABLE public.core_upload_sessions RENAME TO storyrun_upload_sessions',
        'ALTER TABLE public.core_upload_parts RENAME TO storyrun_upload_parts',
        'ALTER TABLE public.storyrun_upload_sessions RENAME CONSTRAINT '
        'core_upload_sessions_pkey TO storyrun_upload_sessions_pkey',
        'ALTER TABLE public.storyrun_upload_parts RENAME CONSTRAINT '
        'core_upload_parts_pkey TO storyrun_upload_parts_pkey',
        'ALTER INDEX public.ix_core_upload_owner_state RENAME TO ix_storyrun_upload_owner_state',
        'ALTER INDEX public.ix_core_upload_recovery RENAME TO ix_storyrun_upload_recovery',
    ):
        connection.execute(text(statement))
    if _signature(_schema_snapshot(connection, legacy=False)) != _CURRENT_SIGNATURE:
        raise RuntimeError("relocated Story upload layout failed verification")


def prepare_lesson_upload_tables(connection: Connection) -> None:
    """Run before Lesson's original table creation, inside its transaction."""
    relocate_story_upload_tables(connection, required=False)
