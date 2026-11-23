"""FEAT-066 T-1a: DDL-B1 part 2 ``20261120_vb_0002`` upgrade, guarded downgrade, re-upgrade.

Runs only against a SEPARATE disposable database named by ``T1A_ROUNDTRIP_DATABASE_URL`` whose name
contains ``be1_acceptance``, ``frc08_v3_t1a`` and ``roundtrip``: the module moves the schema down
and up, which would break the other T-1a tests that share ``BE1_TEST_DATABASE_URL``. The downgrade
always names its target (``20261120_b1_0001``, the revision that part 2 sits on), never ``-1`` (the
graph has many heads). Nothing is dropped except the objects the migration itself creates and
removes.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
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
_PARENT = "20261120_b1_0001"
_REVISION = "20261120_vb_0002"
# FEAT-066 goal v4 T-2e-a: DDL-B3 follows DDL-B2; V4-A T-1b-fix: DDL-B1c follows DDL-B3 and is the
# head of the branch now.
_HEAD = "20261123_rv_0001"
_REFUSED = "DDL-B1 part 2 downgrade refused"
_NEW_STATES = (
    "VIDEO_QUEUED",
    "VIDEO_GENERATING",
    "VIDEO_SAFETY_VALIDATING",
    "VIDEO_READY",
    "SAFETY_BLOCKED",
    "ABANDONED",
)
_NEW_OPERATIONS = ("CREATE_VIDEO_GENERATION", "MARK_VIDEO_UNSUITABLE", "COMPLETE_RUN")


@pytest.fixture
def roundtrip(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[Config, Engine]]:
    url = os.environ.get("T1A_ROUNDTRIP_DATABASE_URL")
    if not url:
        pytest.skip("set T1A_ROUNDTRIP_DATABASE_URL to a disposable round-trip PostgreSQL database")
    name = url.rsplit("/", 1)[-1]
    if not all(part in name for part in ("be1_acceptance", "frc08_v3_t1a", "roundtrip")):
        pytest.fail(
            "T1A_ROUNDTRIP_DATABASE_URL must name a frc08_v3_t1a*roundtrip*be1_acceptance db"
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


def _has_table(engine: Engine, table: str = "video_generations") -> bool:
    return bool(_scalar(engine, f"select to_regclass('story.{table}') is not null"))


def _columns(engine: Engine, table: str = "runs") -> set[str]:
    with engine.connect() as connection:
        return {
            row[0]
            for row in connection.execute(
                text(
                    "select column_name from information_schema.columns "
                    "where table_schema = 'story' and table_name = :table"
                ),
                {"table": table},
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
    state: str = "SCRIPT_REVIEW",
    pointer: str | None = None,
    updated_at: datetime | None = None,
) -> str:
    run_id, now = str(uuid4()), updated_at or datetime.now(UTC)
    columns = "current_video_generation_id, " if pointer else ""
    values = ":pointer, " if pointer else ""
    with engine.begin() as connection:
        connection.execute(
            text(
                "insert into story.runs (run_id, actor_scope_kind, actor_scope_ref, profile_ref, "
                "run_state, revision, version, retryable, dispatch_gate_open, "
                f"{columns}created_at, updated_at) values (:run, 'PARENT_ACCOUNT', :scope, "
                ":profile, :state, 1, 1, "
                f"false, false, {values}:now, :now)"
            ),
            {
                "run": run_id,
                "scope": "s" * 64,
                "profile": str(uuid4()),
                "state": state,
                "now": now,
                "pointer": pointer,
            },
        )
    return run_id


def _insert_receipt(engine: Engine, run_id: str, operation: str) -> str:
    receipt_id = str(uuid4())
    with engine.begin() as connection:
        connection.execute(
            text(
                "insert into story.command_receipts (receipt_id, actor_scope_kind, "
                "actor_scope_ref, operation, idempotency_scope_kind, idempotency_scope_ref, "
                "idempotency_key_sha256, request_fingerprint_sha256, state, response_status, "
                "response_body, resource_ref, state_version, created_at, finalized_at) values "
                "(:id, 'PARENT_ACCOUNT', :scope, :operation, 'STORY_RUN', :run, :key, :key, "
                "'FINAL', 200, '{}'::jsonb, :run, 1, now(), now())"
            ),
            {
                "id": receipt_id,
                "scope": "s" * 64,
                "operation": operation,
                "run": run_id,
                "key": uuid4().hex + uuid4().hex,
            },
        )
    return receipt_id


def _insert_generation(engine: Engine) -> tuple[str, str]:
    """A run with a script revision, its review and one video generation row (all legal)."""
    run_id = _insert_run(engine)
    revision_id, generation_id = str(uuid4()), str(uuid4())
    receipt_id = _insert_receipt(engine, run_id, "CONFIRM_STORY_REVISION")
    with engine.begin() as connection:
        connection.execute(
            text(
                "insert into story.story_revisions (story_revision_id, run_id, revision_no, "
                "status, source_asset_sha256, understanding_revision, context_revision, "
                "story_sha256, language, title, duration_ms, story_content, schema_version, "
                "prompt_version, model_id, model_revision, request_sha256) values (:rev, :run, 1, "
                "'CONFIRMED', :h, 1, 1, :h, 'vi', 't', 60000, '{}'::jsonb, 's', 'p', 'm', '1', :h)"
            ),
            {"rev": revision_id, "run": run_id, "h": "a" * 64},
        )
        connection.execute(
            text(
                "insert into story.story_revision_reviews (review_id, run_id, story_revision_id, "
                "command_receipt_id, actor_scope_kind, actor_scope_ref, decision, "
                "target_story_sha256) values (:review, :run, :rev, :receipt, 'PARENT_ACCOUNT', "
                ":scope, 'CONFIRM', :h)"
            ),
            {
                "review": str(uuid4()),
                "run": run_id,
                "rev": revision_id,
                "receipt": receipt_id,
                "scope": "s" * 64,
                "h": "a" * 64,
            },
        )
        review_id = connection.execute(
            text("select review_id from story.story_revision_reviews where run_id = :run"),
            {"run": run_id},
        ).scalar()
        connection.execute(
            text(
                "insert into story.video_generations (video_generation_id, story_run_id, "
                "story_revision_id, story_review_id, generation_kind, state, "
                "request_idempotency_key_hash, request_fingerprint_sha256, target_script_hash, "
                "admission_started_at) values (:gen, :run, :rev, :review, 'INITIAL', "
                "'ADMISSION_PENDING', :h, :h, :h, now())"
            ),
            {
                "gen": generation_id,
                "run": run_id,
                "rev": revision_id,
                "review": review_id,
                "h": "b" * 64,
            },
        )
    return run_id, generation_id


def _delete_all(engine: Engine, run_id: str) -> None:
    has_video = _has_table(engine) and "current_video_generation_id" in _columns(engine)
    with engine.begin() as connection:
        if has_video:
            connection.execute(
                text("update story.runs set current_video_generation_id = null where run_id = :r"),
                {"r": run_id},
            )
            connection.execute(
                text("delete from story.video_generations where story_run_id = :r"), {"r": run_id}
            )
        connection.execute(
            text("delete from story.story_revision_reviews where run_id = :r"), {"r": run_id}
        )
        connection.execute(
            text("delete from story.story_revisions where run_id = :r"), {"r": run_id}
        )
        connection.execute(
            text("delete from story.command_receipts where resource_ref = :r"), {"r": run_id}
        )
        connection.execute(text("delete from story.runs where run_id = :r"), {"r": run_id})


# ----------------------------------------------------------------------------- the head
def test_the_head_is_the_new_revision_and_the_objects_exist(
    roundtrip: tuple[Config, Engine],
) -> None:
    _config, engine = roundtrip
    versions = _versions(engine)
    # FEAT-066 T-4b2: DDL-B2 (``20261120_b2_0001``) sits on top of this revision and is the head.
    assert _HEAD in versions and {_REVISION, _PARENT}.isdisjoint(versions)
    assert _has_table(engine) and _has_table(engine, "video_generation_scenes")
    assert {
        "current_video_generation_id",
        "adult_wait_started_at",
        "last_meaningful_activity_at",
        "finished_at",
    } <= _columns(engine)
    assert {"fk_vg_story_revision", "fk_vg_story_review", "uq_vg_run_key"} <= _constraints(
        engine, "video_generations"
    )
    assert "fk_story_run_current_video_generation" in _constraints(engine, "runs")
    assert "uq_story_scene_revision_scene" in _constraints(engine, "story_scenes")
    assert "uq_story_review_run_revision" in _constraints(engine, "story_revision_reviews")


def test_the_new_states_and_operations_are_accepted_at_the_head(
    roundtrip: tuple[Config, Engine],
) -> None:
    _config, engine = roundtrip
    for state in _NEW_STATES:
        run_id = _insert_run(engine, state=state)
        _delete_all(engine, run_id)
    run_id = _insert_run(engine)
    try:
        for operation in _NEW_OPERATIONS:
            _insert_receipt(engine, run_id, operation)
    finally:
        _delete_all(engine, run_id)


# ----------------------------------------------------------------------------- guarded downgrade
@pytest.mark.parametrize(
    "case",
    ["generation", "new_state_run", "video_receipt_create", "video_receipt_complete"],
)
def test_the_downgrade_refuses_while_any_video_data_exists(
    roundtrip: tuple[Config, Engine], case: str
) -> None:
    config, engine = roundtrip
    if case == "generation":
        run_id, _generation = _insert_generation(engine)
    elif case == "new_state_run":
        run_id = _insert_run(engine, state="VIDEO_READY")
    else:
        run_id = _insert_run(engine)
        _insert_receipt(
            engine,
            run_id,
            "CREATE_VIDEO_GENERATION" if case == "video_receipt_create" else "COMPLETE_RUN",
        )
    try:
        with pytest.raises(Exception, match=_REFUSED):
            command.downgrade(config, _PARENT)
        # a refused downgrade changes nothing (the DDL is transactional)
        assert _HEAD in _versions(engine) and _has_table(engine)
        assert "current_video_generation_id" in _columns(engine)
    finally:
        _delete_all(engine, run_id)


def test_the_downgrade_does_not_refuse_on_the_values_part_one_owns(
    roundtrip: tuple[Config, Engine],
) -> None:
    config, engine = roundtrip
    review_run = _insert_run(engine, state="INPUT_REVIEW")
    _insert_receipt(engine, review_run, "SUBMIT_IDEA")
    try:
        command.downgrade(config, _PARENT)
        assert _PARENT in _versions(engine) and _REVISION not in _versions(engine)
        kept = _scalar(engine, "select run_state from story.runs where run_id = :r", r=review_run)
        assert kept == "INPUT_REVIEW"
    finally:
        command.upgrade(config, "heads")
        _delete_all(engine, review_run)


def test_downgrade_by_explicit_revision_then_upgrade_keeps_rows_and_backfills_the_clocks(
    roundtrip: tuple[Config, Engine],
) -> None:
    config, engine = roundtrip
    legacy = _insert_run(engine, state="SCRIPT_REVIEW")
    try:
        command.downgrade(config, _PARENT)
        versions = _versions(engine)
        assert _PARENT in versions and _REVISION not in versions
        assert not _has_table(engine) and not _has_table(engine, "video_generation_scenes")
        assert not {
            "current_video_generation_id",
            "adult_wait_started_at",
            "last_meaningful_activity_at",
            "finished_at",
        } & _columns(engine)
        assert "uq_story_scene_revision_scene" not in _constraints(engine, "story_scenes")
        assert "uq_story_review_run_revision" not in _constraints(engine, "story_revision_reviews")
        # part one's sets are back: its own values stay, part two's are refused
        _insert_receipt(engine, legacy, "SUBMIT_IDEA")
        _delete_all(engine, _insert_run(engine, state="INPUT_REVIEW"))
        with pytest.raises(Exception, match="ck_story_run_state"):
            _insert_run(engine, state="ABANDONED")
        with pytest.raises(Exception, match="ck_story_receipt_operation"):
            _insert_receipt(engine, legacy, "CREATE_VIDEO_GENERATION")
        # rows written while the schema was down: a waiting run and a run in system work
        past = datetime.now(UTC) - timedelta(days=3)
        waiting = _insert_run(engine, state="SCRIPT_REVIEW", updated_at=past)
        working = _insert_run(engine, state="SCRIPT_GENERATING", updated_at=past)
        command.upgrade(config, "heads")
        assert _HEAD in _versions(engine) and _PARENT not in _versions(engine)
        assert _has_table(engine) and _has_table(engine, "video_generation_scenes")
        for run_id in (waiting, legacy):
            assert (
                _scalar(
                    engine,
                    "select adult_wait_started_at = updated_at and "
                    "last_meaningful_activity_at = updated_at from story.runs where run_id = :r",
                    r=run_id,
                )
                is True
            )
        assert (
            _scalar(
                engine,
                "select adult_wait_started_at is null and last_meaningful_activity_at is null "
                "from story.runs where run_id = :r",
                r=working,
            )
            is True
        )
        # the new objects work again
        run_id, _generation = _insert_generation(engine)
        _delete_all(engine, run_id)
        for run_id in (waiting, working):
            _delete_all(engine, run_id)
    finally:
        command.upgrade(config, "heads")
        _delete_all(engine, legacy)
