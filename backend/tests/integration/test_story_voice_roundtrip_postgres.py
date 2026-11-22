"""FEAT-066 T-2c: DDL-B1 ``20261120_b1_0001`` upgrade, guarded downgrade, re-upgrade (PostgreSQL).

Runs only against a SEPARATE disposable database named by ``T2C_ROUNDTRIP_DATABASE_URL`` whose
name contains ``be1_acceptance``, ``frc08_v3_t2c`` and ``roundtrip``: the module moves the schema
down and up, which would break the other T-2c tests that share ``BE1_TEST_DATABASE_URL``. The
downgrade always names its target (``20261119_frc08_lifecycle_scope``), never ``-1`` (the graph has
many heads). Nothing is dropped except the objects the migration itself creates and removes.
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

_BACKEND = Path(__file__).resolve().parents[2]
_PARENT = "20261119_frc08_lifecycle_scope"
_REVISION = "20261120_b1_0001"
# FEAT-066 T-1a: DDL-B1 part 2 sits on top of this revision; FEAT-066 T-4b2: DDL-B2 sits on top of
# that and is the head of the branch. The explicit downgrade to ``_PARENT`` first runs their
# (guarded) downgrades, the upgrade restores them.
_HEAD = "20261120_b2_0001"
_REFUSED = "DDL-B1 downgrade refused"


@pytest.fixture
def roundtrip(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[Config, Engine]]:
    url = os.environ.get("T2C_ROUNDTRIP_DATABASE_URL")
    if not url:
        pytest.skip("set T2C_ROUNDTRIP_DATABASE_URL to a disposable round-trip PostgreSQL database")
    name = url.rsplit("/", 1)[-1]
    if not all(part in name for part in ("be1_acceptance", "frc08_v3_t2c", "roundtrip")):
        pytest.fail(
            "T2C_ROUNDTRIP_DATABASE_URL must name a frc08_v3_t2c*roundtrip*be1_acceptance db"
        )
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


def _scalar(engine: Engine, sql: str, **params: Any) -> Any:
    with engine.connect() as connection:
        return connection.execute(text(sql), params).scalar()


def _has_table(engine: Engine) -> bool:
    return bool(_scalar(engine, "select to_regclass('story.transcript_revisions') is not null"))


def _columns(engine: Engine) -> set[str]:
    with engine.connect() as connection:
        return {
            row[0]
            for row in connection.execute(
                text(
                    "select column_name from information_schema.columns "
                    "where table_schema = 'story' and table_name = 'run_inputs'"
                )
            )
        }


def _constraints(engine: Engine, table: str) -> set[str]:
    with engine.connect() as connection:
        return {
            row[0]
            for row in connection.execute(
                text("select conname from pg_constraint where conrelid = to_regclass(:table)"),
                {"table": f"story.{table}"},
            )
        }


def _insert_run(
    engine: Engine,
    *,
    state: str = "INPUT_PROCESSING",
    voice: bool = False,
    typed: str | None = "legacy idea",
) -> tuple[str, str]:
    """A plain Story run with one input row (the shape every earlier version could write)."""
    run_id, input_id, now = str(uuid4()), str(uuid4()), datetime.now(UTC)
    source = None if typed is None else "TEXT"
    if voice:
        source = "TEXT_AND_VOICE" if typed else "VOICE"
    with engine.begin() as connection:
        connection.execute(
            text(
                "insert into story.runs (run_id, actor_scope_kind, actor_scope_ref, profile_ref, "
                "run_state, revision, version, retryable, dispatch_gate_open, created_at, "
                "updated_at) values (:run, 'PARENT_ACCOUNT', :scope, :profile, :state, 1, 1, "
                "false, false, :now, :now)"
            ),
            {"run": run_id, "scope": "s" * 64, "profile": str(uuid4()), "state": state, "now": now},
        )
        connection.execute(
            text(
                "insert into story.run_inputs (run_input_id, run_id, input_revision, typed_idea, "
                "idea_source, voice_asset_ref, voice_asset_version, voice_duration_ms, created_at) "
                "values (:input, :run, 1, :typed, :source, :voice, :version, :duration, :now)"
            ),
            {
                "input": input_id,
                "run": run_id,
                "typed": typed,
                "source": source,
                "voice": f"parent/{run_id}/x/original" if voice else None,
                "version": 1 if voice else None,
                "duration": 1000 if voice else None,
                "now": now,
            },
        )
    return run_id, input_id


def _insert_transcript(engine: Engine, run_id: str, input_id: str) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "insert into story.transcript_revisions (transcript_revision_id, run_id, "
                "run_input_id, source_asset_ref, revision_no, origin, state) values (:id, :run, "
                ":input, :ref, 1, 'ASR', 'PENDING')"
            ),
            {"id": str(uuid4()), "run": run_id, "input": input_id, "ref": f"parent/{run_id}/x"},
        )


def _insert_receipt(engine: Engine, run_id: str, operation: str) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "insert into story.command_receipts (receipt_id, actor_scope_kind, "
                "actor_scope_ref, "
                "operation, idempotency_scope_kind, idempotency_scope_ref, idempotency_key_sha256, "
                "request_fingerprint_sha256, state, response_status, response_body, resource_ref, "
                "state_version, created_at, finalized_at) values (:id, 'PARENT_ACCOUNT', :scope, "
                ":operation, 'STORY_RUN', :run, :key, :key, 'FINAL', 202, '{}'::jsonb, :run, 1, "
                "now(), now())"
            ),
            {
                "id": str(uuid4()),
                "scope": "s" * 64,
                "operation": operation,
                "run": run_id,
                "key": "k" * 64,
            },
        )


def _delete_run(engine: Engine, run_id: str) -> None:
    with engine.begin() as connection:
        for table in ("transcript_revisions", "run_inputs"):
            connection.execute(
                text(f"delete from story.{table} where run_id = :run"), {"run": run_id}
            )
        connection.execute(
            text("delete from story.command_receipts where resource_ref = :run"), {"run": run_id}
        )
        connection.execute(text("delete from story.runs where run_id = :run"), {"run": run_id})


def test_the_head_is_the_new_revision_and_the_objects_exist(
    roundtrip: tuple[Config, Engine],
) -> None:
    _config, engine = roundtrip
    assert _HEAD in _versions(engine) and {_REVISION, _PARENT}.isdisjoint(_versions(engine))
    assert _has_table(engine)
    assert {"voice_asset_ref", "voice_asset_version", "voice_duration_ms"} <= _columns(engine)
    assert {"ck_story_run_input_idea", "ck_story_run_input_voice"} <= _constraints(
        engine, "run_inputs"
    )
    assert "ck_story_run_input_typed_idea" not in _constraints(engine, "run_inputs")


@pytest.mark.parametrize(
    "case",
    ["transcript", "voice_input", "input_review_run", "submit_idea_receipt", "confirm_receipt"],
)
def test_the_downgrade_refuses_while_any_new_data_exists(
    roundtrip: tuple[Config, Engine], case: str
) -> None:
    config, engine = roundtrip
    if case == "transcript":
        run_id, input_id = _insert_run(engine)
        _insert_transcript(engine, run_id, input_id)
    elif case == "voice_input":
        run_id, _input = _insert_run(engine, voice=True)
    elif case == "input_review_run":
        run_id, _input = _insert_run(engine, state="INPUT_REVIEW")
    else:
        run_id, _input = _insert_run(engine)
        _insert_receipt(
            engine, run_id, "SUBMIT_IDEA" if case == "submit_idea_receipt" else "CONFIRM_TRANSCRIPT"
        )
    try:
        with pytest.raises(Exception, match=_REFUSED):
            command.downgrade(config, _PARENT)
        # a refused downgrade changes nothing (the DDL is transactional)
        assert _HEAD in _versions(engine) and _has_table(engine)
        assert "voice_asset_ref" in _columns(engine)
    finally:
        _delete_run(engine, run_id)


def test_downgrade_by_explicit_revision_then_upgrade_again_keeps_legacy_rows(
    roundtrip: tuple[Config, Engine],
) -> None:
    config, engine = roundtrip
    legacy_run, _input = _insert_run(engine, typed="a legacy text idea")
    try:
        command.downgrade(config, _PARENT)
        versions = _versions(engine)
        assert _PARENT in versions and {_REVISION, _HEAD}.isdisjoint(versions)
        assert not _has_table(engine)
        assert not {"voice_asset_ref", "voice_asset_version", "voice_duration_ms"} & _columns(
            engine
        )
        constraints = _constraints(engine, "run_inputs")
        assert "ck_story_run_input_typed_idea" in constraints
        assert not {"ck_story_run_input_idea", "ck_story_run_input_voice"} & constraints
        # the old CHECKs are back: no INPUT_REVIEW run state, no new receipt operation
        with pytest.raises(Exception, match="ck_story_run_state"):
            _insert_run(engine, state="INPUT_REVIEW")
        with pytest.raises(Exception, match="ck_story_receipt_operation"):
            _insert_receipt(engine, legacy_run, "SUBMIT_IDEA")
        assert (
            _scalar(
                engine,
                "select typed_idea from story.run_inputs where run_id = :run",
                run=legacy_run,
            )
            == "a legacy text idea"
        )
        command.upgrade(config, "heads")
        assert _HEAD in _versions(engine) and {_REVISION, _PARENT}.isdisjoint(_versions(engine))
        assert _has_table(engine)
        assert {"voice_asset_ref", "voice_asset_version", "voice_duration_ms"} <= _columns(engine)
        assert (
            _scalar(
                engine,
                "select typed_idea from story.run_inputs where run_id = :run",
                run=legacy_run,
            )
            == "a legacy text idea"
        )
        # the new objects work again
        run_id, input_id = _insert_run(engine, state="INPUT_REVIEW", voice=True)
        _insert_transcript(engine, run_id, input_id)
        _insert_receipt(engine, run_id, "CONFIRM_TRANSCRIPT")
        _delete_run(engine, run_id)
    finally:
        command.upgrade(config, "heads")
        _delete_run(engine, legacy_run)
