"""FEAT-066 T-4b2: DDL-B2 ``20261120_b2_0001`` upgrade, guarded downgrade, re-upgrade (PostgreSQL).

The downgrade is explicit (``downgrade 20261120_vb_0002``, never ``-1``: the graph has many
heads), runs
on a disposable database only and refuses while any run row holds a Teacher column. Needs
``T4B2_ROUNDTRIP_DATABASE_URL`` naming a ``frc08_v3_t4b2*_rt_*be1_acceptance`` database; the fixture
runs ``alembic upgrade heads`` first, so an empty database is enough.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool

from alembic import command
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings

_BACKEND = Path(__file__).resolve().parents[3]
_REVISION = "20261120_b2_0001"
_PARENT = "20261120_vb_0002"
# FEAT-066 goal v4 T-2e-a: DDL-B3 follows this revision; V4-A T-1b-fix: DDL-B1c follows that and is
# the head of the branch now; the downgrade to ``_PARENT`` runs their (guarded) downgrades first.
# V4-B T-12b: 20261121_bpr_0001 follows 20261123_rv_0001; T-12c: 20261121_psn_0002 follows
# it and is the live head now.
_HEAD = "20261125_as_0002"
_REFUSED = "T-4b2 downgrade refused"
_COLUMNS = {"active_owner_teacher_id", "occurrence_ref", "created_by_actor_ref"}
_CHECKS = {
    "ck_story_run_teacher_pins",
    "ck_story_run_teacher_owner",
    "ck_story_run_teacher_lock_state",
}
_INDEXES = {
    "uq_story_run_active_teacher",
    "uq_story_run_active_occurrence",
    "ix_story_run_occurrence",
}


@pytest.fixture
def roundtrip(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[Config, Engine]]:
    url = os.environ.get("T4B2_ROUNDTRIP_DATABASE_URL")
    if not url:
        pytest.skip(
            "set T4B2_ROUNDTRIP_DATABASE_URL to a disposable round-trip PostgreSQL database"
        )
    name = url.rsplit("/", 1)[-1]
    if not all(part in name for part in ("be1_acceptance", "frc08_v3_t4b2", "_rt_")):
        pytest.fail("T4B2_ROUNDTRIP_DATABASE_URL must name a frc08_v3_t4b2*_rt_*be1_acceptance db")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", url)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    config = Config(str(_BACKEND / "alembic.ini"))
    command.upgrade(config, "heads")
    engine = create_engine(url, poolclass=NullPool)
    try:
        yield config, engine
    finally:
        engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


def _versions(engine: Engine) -> set[str]:
    with engine.connect() as connection:
        return {
            row[0] for row in connection.execute(text("select version_num from alembic_version"))
        }


def _names(engine: Engine, sql: str) -> set[str]:
    with engine.connect() as connection:
        return {row[0] for row in connection.execute(text(sql))}


def _columns(engine: Engine) -> set[str]:
    return _names(
        engine,
        "select column_name from information_schema.columns "
        "where table_schema = 'story' and table_name = 'runs'",
    )


def _constraints(engine: Engine) -> set[str]:
    return _names(
        engine,
        "select conname from pg_constraint where conrelid = to_regclass('story.runs')",
    )


def _indexes(engine: Engine) -> set[str]:
    return _names(
        engine, "select indexname from pg_indexes where schemaname = 'story' and tablename = 'runs'"
    )


def _triggers(engine: Engine) -> set[str]:
    return _names(
        engine,
        "select tgname from pg_trigger "
        "where tgrelid = to_regclass('story.runs') and not tgisinternal",
    )


def _function_exists(engine: Engine) -> bool:
    return bool(
        _names(
            engine,
            "select proname from pg_proc p join pg_namespace n on n.oid = p.pronamespace "
            "where n.nspname = 'story' and proname = 'release_teacher_lock'",
        )
    )


def _insert_run(engine: Engine, **values: Any) -> str:
    run_id, now = str(uuid4()), datetime.now(UTC)
    row: dict[str, Any] = {
        "run_id": run_id,
        "actor_scope_kind": "PARENT_ACCOUNT",
        "actor_scope_ref": "s" * 64,
        "profile_ref": str(uuid4()),
        "run_state": "INPUT_PROCESSING",
        "revision": 1,
        "version": 1,
        "retryable": False,
        "dispatch_gate_open": False,
        "created_at": now,
        "updated_at": now,
        **values,
    }
    columns = ", ".join(row)
    placeholders = ", ".join(f":{name}" for name in row)
    with engine.begin() as connection:
        connection.execute(text(f"insert into story.runs ({columns}) values ({placeholders})"), row)  # noqa: S608
    return run_id


def _delete_run(engine: Engine, run_id: str) -> None:
    with engine.begin() as connection:
        connection.execute(text("delete from story.runs where run_id = :r"), {"r": run_id})


def test_the_head_is_the_new_revision_and_the_objects_exist(
    roundtrip: tuple[Config, Engine],
) -> None:
    _config, engine = roundtrip
    versions = _versions(engine)
    assert _HEAD in versions and {_REVISION, _PARENT}.isdisjoint(versions)
    assert _columns(engine) >= _COLUMNS
    assert _constraints(engine) >= _CHECKS
    assert _indexes(engine) >= _INDEXES
    assert "trg_story_run_release_teacher_lock" in _triggers(engine)
    assert _function_exists(engine)


def test_the_explicit_downgrade_removes_every_object_and_the_upgrade_restores_them(
    roundtrip: tuple[Config, Engine],
) -> None:
    config, engine = roundtrip
    parent_run = _insert_run(engine, active_owner_parent_account_id=uuid4().hex)
    try:
        command.downgrade(config, _PARENT)  # explicit revision, never -1
        versions = _versions(engine)
        assert _PARENT in versions and _REVISION not in versions
        assert not _COLUMNS & _columns(engine)
        assert not _CHECKS & _constraints(engine)
        assert not _INDEXES & _indexes(engine)
        assert "trg_story_run_release_teacher_lock" not in _triggers(engine)
        assert not _function_exists(engine)
        # the Parent row and the Parent lock index are untouched
        assert "uq_story_run_active_parent" in _indexes(engine)
        assert _names(engine, f"select run_id from story.runs where run_id = '{parent_run}'") == {
            parent_run
        }
        command.upgrade(config, "heads")
        assert _HEAD in _versions(engine) and _PARENT not in _versions(engine)
        assert _columns(engine) >= _COLUMNS and _constraints(engine) >= _CHECKS
        assert _indexes(engine) >= _INDEXES
        assert "trg_story_run_release_teacher_lock" in _triggers(engine)
        assert _function_exists(engine)
    finally:
        command.upgrade(config, "heads")
        _delete_run(engine, parent_run)


@pytest.mark.parametrize("case", ["teacher_lock", "terminal_pinned_run", "occurrence_only_run"])
def test_the_downgrade_refuses_while_a_teacher_run_row_exists_and_changes_nothing(
    roundtrip: tuple[Config, Engine], case: str
) -> None:
    config, engine = roundtrip
    teacher = {
        "actor_scope_kind": "ORGANIZATION",
        "actor_scope_ref": "synthetic-org",
        "occurrence_ref": str(uuid4()),
        "created_by_actor_ref": "synthetic-account",
    }
    if case == "teacher_lock":
        run_id = _insert_run(engine, **teacher, active_owner_teacher_id=uuid4().hex[:30])
    elif case == "terminal_pinned_run":
        # the lock is gone (the trigger or the writer cleared it) but the run keeps its pin
        run_id = _insert_run(engine, **teacher, run_state="FAILED")
    else:
        run_id = _insert_run(engine, **teacher)
    try:
        with pytest.raises(Exception, match=_REFUSED):
            command.downgrade(config, _PARENT)
        # a refused downgrade changes nothing (the DDL is transactional)
        assert _HEAD in _versions(engine) and _PARENT not in _versions(engine)
        assert _columns(engine) >= _COLUMNS and _constraints(engine) >= _CHECKS
        assert "trg_story_run_release_teacher_lock" in _triggers(engine)
        assert _names(engine, f"select run_id from story.runs where run_id = '{run_id}'") == {
            run_id
        }
    finally:
        _delete_run(engine, run_id)


def test_the_trigger_frees_a_lock_when_the_run_state_is_written(
    roundtrip: tuple[Config, Engine],
) -> None:
    _config, engine = roundtrip
    account = uuid4().hex[:30]
    run_id = _insert_run(
        engine,
        actor_scope_kind="ORGANIZATION",
        actor_scope_ref="synthetic-org",
        occurrence_ref=str(uuid4()),
        created_by_actor_ref=account,
        active_owner_teacher_id=account,
    )
    try:
        with engine.begin() as connection:
            connection.execute(
                text("update story.runs set run_state = 'SAFETY_BLOCKED' where run_id = :r"),
                {"r": run_id},
            )
        assert _names(
            engine, f"select active_owner_teacher_id from story.runs where run_id = '{run_id}'"
        ) == {account}
        with engine.begin() as connection:
            connection.execute(
                text("update story.runs set run_state = 'COMPLETED' where run_id = :r"),
                {"r": run_id},
            )
            # the same transaction sees the lock gone (a BEFORE trigger, not a deferred check)
            held = connection.execute(
                text("select active_owner_teacher_id from story.runs where run_id = :r"),
                {"r": run_id},
            ).scalar()
        assert held is None
    finally:
        _delete_run(engine, run_id)
