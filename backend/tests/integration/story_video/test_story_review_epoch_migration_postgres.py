"""FEAT-066 goal v4 T-1b-fix: DDL-B1c ``20261123_rv_0001`` upgrade, guarded downgrade, re-upgrade.

Runs only against a SEPARATE disposable database named by ``T1BFIX_ROUNDTRIP_DATABASE_URL`` whose
name contains ``be1_acceptance``, ``frc08_v4_t1bfix`` and ``roundtrip``: the module moves the schema
down and up, which would break the other tests that share ``BE1_TEST_DATABASE_URL``. The downgrade
always names its target (``20261123_as_0001``, or ``20261120_b2_0001`` for the whole T-2e-a and
T-1b-fix stack), never ``-1`` (the graph has many heads). Nothing is dropped except the objects the
migration itself creates and removes.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.pool import NullPool

from alembic import command
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings

_BACKEND = Path(__file__).resolve().parents[3]
_PARENT = "20261123_as_0001"
_HEAD = "20261123_rv_0001"
_B2 = "20261120_b2_0001"
_REFUSED = "DDL-B1c downgrade refused"
_SCOPE = "s" * 64
_HASH = "a" * 64


@pytest.fixture
def roundtrip(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[Config, Engine]]:
    url = os.environ.get("T1BFIX_ROUNDTRIP_DATABASE_URL")
    if not url:
        pytest.skip("set T1BFIX_ROUNDTRIP_DATABASE_URL to a disposable round-trip PostgreSQL db")
    name = url.rsplit("/", 1)[-1]
    if not all(part in name for part in ("be1_acceptance", "frc08_v4_t1bfix", "roundtrip")):
        pytest.fail(
            "T1BFIX_ROUNDTRIP_DATABASE_URL must name a frc08_v4_t1bfix*roundtrip*be1_acceptance db"
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
        try:
            command.upgrade(config, "heads")
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


def _columns(engine: Engine) -> set[str]:
    with engine.connect() as connection:
        return {
            row[0]
            for row in connection.execute(
                text(
                    "select column_name from information_schema.columns "
                    "where table_schema = 'story' and table_name = 'story_revision_reviews'"
                )
            )
        }


def _constraints(engine: Engine) -> set[str]:
    with engine.connect() as connection:
        return {
            row[0]
            for row in connection.execute(
                text("select conname from pg_constraint where conrelid = to_regclass(:table)"),
                {"table": "story.story_revision_reviews"},
            )
        }


def _receipt_operations(engine: Engine) -> str:
    return str(
        _scalar(
            engine,
            "select pg_get_constraintdef(oid) from pg_constraint "
            "where conname = 'ck_story_receipt_operation'",
        )
    )


def _insert_run_with_revision(engine: Engine) -> tuple[str, str]:
    run_id, revision_id = str(uuid4()), str(uuid4())
    with engine.begin() as connection:
        connection.execute(
            text(
                "insert into story.runs (run_id, actor_scope_kind, actor_scope_ref, profile_ref, "
                "run_state, revision, version, retryable, dispatch_gate_open, created_at, "
                "updated_at) values (:run, 'PARENT_ACCOUNT', :scope, :profile, 'SCRIPT_REVIEW', "
                "1, 1, false, false, now(), now())"
            ),
            {"run": run_id, "scope": _SCOPE, "profile": str(uuid4())},
        )
        connection.execute(
            text(
                "insert into story.story_revisions (story_revision_id, run_id, revision_no, "
                "status, source_asset_sha256, understanding_revision, context_revision, "
                "story_sha256, language, title, duration_ms, story_content, schema_version, "
                "prompt_version, model_id, model_revision, request_sha256) values (:rev, :run, 1, "
                "'CONFIRMED', :h, 1, 1, :h, 'vi', 't', 60000, '{}'::jsonb, 's', 'p', 'm', '1', :h)"
            ),
            {"rev": revision_id, "run": run_id, "h": _HASH},
        )
    return run_id, revision_id


def _insert_review(engine: Engine, run_id: str, revision_id: str, epoch: int | None) -> None:
    """One review row (a fresh receipt each); ``epoch`` ``None`` leaves the column to its default
    (and, on the old schema, omits it)."""

    receipt_id = str(uuid4())
    columns = "review_epoch, " if epoch is not None else ""
    values = ":epoch, " if epoch is not None else ""
    with engine.begin() as connection:
        connection.execute(
            text(
                "insert into story.command_receipts (receipt_id, actor_scope_kind, "
                "actor_scope_ref, operation, idempotency_scope_kind, idempotency_scope_ref, "
                "idempotency_key_sha256, request_fingerprint_sha256, state, response_status, "
                "response_body, resource_ref, state_version, created_at, finalized_at) values "
                "(:id, 'PARENT_ACCOUNT', :scope, 'CONFIRM_STORY_REVISION', 'STORY_RUN', :run, "
                ":key, :key, 'FINAL', 200, '{}'::jsonb, :run, 1, now(), now())"
            ),
            {"id": receipt_id, "scope": _SCOPE, "run": run_id, "key": uuid4().hex + uuid4().hex},
        )
        connection.execute(
            text(
                "insert into story.story_revision_reviews (review_id, run_id, story_revision_id, "
                f"command_receipt_id, actor_scope_kind, actor_scope_ref, decision, {columns}"
                "target_story_sha256) values (:review, :run, :rev, :receipt, 'PARENT_ACCOUNT', "
                f":scope, 'CONFIRM', {values}:h)"
            ),
            {
                "review": str(uuid4()),
                "run": run_id,
                "rev": revision_id,
                "receipt": receipt_id,
                "scope": _SCOPE,
                "epoch": epoch,
                "h": _HASH,
            },
        )


def _delete_run(engine: Engine, run_id: str) -> None:
    with engine.begin() as connection:
        for sql in (
            "delete from story.story_revision_reviews where run_id = :r",
            "delete from story.story_revisions where run_id = :r",
            "delete from story.command_receipts where resource_ref = :r",
            "delete from story.runs where run_id = :r",
        ):
            connection.execute(text(sql), {"r": run_id})


# ----------------------------------------------------------------------------- the head
def test_the_head_is_the_new_revision_and_the_objects_exist(
    roundtrip: tuple[Config, Engine],
) -> None:
    _config, engine = roundtrip
    versions = _versions(engine)
    assert _HEAD in versions and {_PARENT, _B2}.isdisjoint(versions)
    assert "review_epoch" in _columns(engine)
    constraints = _constraints(engine)
    assert {"uq_story_revision_review_epoch", "ck_story_revision_review_epoch"} <= constraints
    assert "uq_story_revision_review_once" not in constraints
    assert {"uq_story_review_run_revision", "fk_story_revision_review_owner"} <= constraints
    assert "SELECT_ACTIVITY" in _receipt_operations(engine)  # the receipt check was not touched
    default = _scalar(
        engine,
        "select column_default from information_schema.columns where table_schema = 'story' "
        "and table_name = 'story_revision_reviews' and column_name = 'review_epoch'",
    )
    assert str(default) == "1"


def test_an_epoch_is_one_to_three_and_unique_per_revision(
    roundtrip: tuple[Config, Engine],
) -> None:
    _config, engine = roundtrip
    run_id, revision_id = _insert_run_with_revision(engine)
    try:
        _insert_review(engine, run_id, revision_id, None)  # the default epoch
        _insert_review(engine, run_id, revision_id, 2)
        _insert_review(engine, run_id, revision_id, 3)
        epochs = _scalar(
            engine,
            "select array_agg(review_epoch order by review_epoch) "
            "from story.story_revision_reviews where run_id = :r",
            r=run_id,
        )
        assert list(epochs) == [1, 2, 3]
        for duplicate in (1, 2, 3):
            with pytest.raises(IntegrityError, match="uq_story_revision_review_epoch"):
                _insert_review(engine, run_id, revision_id, duplicate)
        for bad in (0, 4, -1):
            with pytest.raises(IntegrityError, match="ck_story_revision_review_epoch"):
                _insert_review(engine, run_id, revision_id, bad)
    finally:
        _delete_run(engine, run_id)


# ----------------------------------------------------------------------------- the downgrade
def test_the_downgrade_refuses_while_a_re_confirmation_exists_and_changes_nothing(
    roundtrip: tuple[Config, Engine],
) -> None:
    config, engine = roundtrip
    run_id, revision_id = _insert_run_with_revision(engine)
    try:
        _insert_review(engine, run_id, revision_id, 1)
        _insert_review(engine, run_id, revision_id, 2)
        for target in (_PARENT, _B2):  # the T-2e-a target passes through this revision first
            with pytest.raises(DBAPIError, match=_REFUSED):
                command.downgrade(config, target)
            assert _HEAD in _versions(engine) and _PARENT not in _versions(engine)
            assert "review_epoch" in _columns(engine)
            assert "uq_story_revision_review_epoch" in _constraints(engine)
    finally:
        _delete_run(engine, run_id)


def test_the_explicit_downgrade_restores_the_old_unique_and_the_upgrade_restores_the_epoch(
    roundtrip: tuple[Config, Engine],
) -> None:
    config, engine = roundtrip
    run_id, revision_id = _insert_run_with_revision(engine)
    try:
        _insert_review(engine, run_id, revision_id, 1)  # epoch 1 only: the guard passes
        command.downgrade(config, _PARENT)  # explicit revision, never -1
        assert _PARENT in _versions(engine) and _HEAD not in _versions(engine)
        assert "review_epoch" not in _columns(engine)
        constraints = _constraints(engine)
        assert "uq_story_revision_review_once" in constraints
        assert (
            not {"uq_story_revision_review_epoch", "ck_story_revision_review_epoch"} & constraints
        )
        # the old rule is back: a second review of the same revision is refused
        with pytest.raises(IntegrityError, match="uq_story_revision_review_once"):
            _insert_review(engine, run_id, revision_id, None)
        command.upgrade(config, "heads")
        assert _HEAD in _versions(engine) and "review_epoch" in _columns(engine)
        assert (
            _scalar(
                engine,
                "select review_epoch from story.story_revision_reviews where run_id = :r",
                r=run_id,
            )
            == 1
        )
    finally:
        _delete_run(engine, run_id)


def test_the_whole_t2ea_and_t1bfix_stack_goes_down_to_b2_and_up_again(
    roundtrip: tuple[Config, Engine],
) -> None:
    """The T-2e-a downgrade target (``20261120_b2_0001``) runs this revision down first; its
    guard passes on an empty review table."""

    config, engine = roundtrip
    command.downgrade(config, _B2)
    assert _B2 in _versions(engine) and {_PARENT, _HEAD}.isdisjoint(_versions(engine))
    assert "review_epoch" not in _columns(engine)
    assert "uq_story_revision_review_once" in _constraints(engine)
    assert "SELECT_ACTIVITY" not in _receipt_operations(engine)
    command.upgrade(config, "heads")
    assert _HEAD in _versions(engine) and "review_epoch" in _columns(engine)
    assert "uq_story_revision_review_once" not in _constraints(engine)
    assert "SELECT_ACTIVITY" in _receipt_operations(engine)
