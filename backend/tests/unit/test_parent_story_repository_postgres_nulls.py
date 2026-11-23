"""Offline regression tests for Parent story-run writes that PostgreSQL refused.

An explicit ``None`` on a JSONB column is bound as the JSON value ``null``, not SQL NULL,
and two check constraints require SQL NULL. ``attach_artwork`` also has to flush its asset
rows before the lineage insert, because the product session factory disables autoflush.
These tests inspect the statements the repository builds; they use no database.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest
from sqlalchemy.dialects import postgresql

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_profile_lookup import (
    ParentStoryProfileReference,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)

_PRINCIPAL = VerifiedPrincipal("parent-1", "issuer-1", frozenset({"parent"}))
_RUN_ID = "22222222-2222-4222-8222-222222222222"
_HASH = "a" * 64
_LESSON_PIN = {"schema_version": "sketch2life.parent-lesson-pin.v1", "lesson_id": "lesson-1"}


class _Session:
    """Records what the repository asks of the session, in order."""

    def __init__(self) -> None:
        self.events: list[tuple[str, Any]] = []

    def execute(self, statement: Any, *_args: Any, **_kwargs: Any) -> None:
        self.events.append(("execute", statement))

    def scalar(self, statement: Any, *_args: Any, **_kwargs: Any) -> None:
        self.events.append(("scalar", statement))

    def add_all(self, instances: Any) -> None:
        self.events.append(("add_all", list(instances)))

    def flush(self) -> None:
        self.events.append(("flush", None))

    def commit(self) -> None:
        self.events.append(("commit", None))

    def rollback(self) -> None:
        self.events.append(("rollback", None))

    def insert_into(self, table_name: str) -> Any:
        matches = [
            payload
            for kind, payload in self.events
            if kind == "execute" and _table_name(payload) == table_name
        ]
        assert len(matches) == 1, f"expected one insert into {table_name}"
        return matches[0]


def _table_name(statement: Any) -> str:
    return str(getattr(getattr(statement, "table", None), "name", ""))


def _bound_parameters(statement: Any) -> tuple[dict[str, Any], str]:
    dialect: Any = postgresql.dialect  # the dialect class has no type annotations
    compiled = statement.compile(dialect=dialect())
    return dict(compiled.params), str(compiled)


def _repository() -> tuple[SqlParentStoryRunRepository, _Session]:
    session = _Session()
    return SqlParentStoryRunRepository(session), session  # type: ignore[arg-type]


def _create(monkeypatch: pytest.MonkeyPatch, lesson_pin: dict[str, Any] | None) -> Any:
    repository, session = _repository()
    monkeypatch.setattr(repository, "_lock_idempotency", lambda **_kwargs: None)
    monkeypatch.setattr(repository, "_find_idempotency_receipt", lambda **_kwargs: None)
    monkeypatch.setattr(repository, "_store_idempotency_receipt", lambda **_kwargs: "receipt")
    monkeypatch.setattr(repository, "get_run", lambda **_kwargs: None)
    repository.create_run(
        principal=_PRINCIPAL,
        account_id="account-1",
        profile=ParentStoryProfileReference(
            profile_id=UUID("11111111-1111-4111-8111-111111111111"),
            profile_revision_id=UUID("33333333-3333-4333-8333-333333333333"),
            state="ACTIVE",
            data_origin="SYNTHETIC_DEV",
            age_months=60,
            interests_summary=None,
        ),
        idempotency_key="create-1",
        run_id=_RUN_ID,
        topic="topic",
        adult_confirmed_idea="",
        lesson_pin_snapshot=lesson_pin,
    )
    return session.insert_into("run_inputs")


def test_create_without_lesson_pin_writes_sql_null(monkeypatch: pytest.MonkeyPatch) -> None:
    parameters, sql = _bound_parameters(_create(monkeypatch, None))
    assert "lesson_pin_snapshot" not in parameters
    assert "NULL" in sql
    assert parameters["lesson_pin_snapshot_sha256"] is None


def test_create_with_lesson_pin_writes_the_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    parameters, _sql = _bound_parameters(_create(monkeypatch, dict(_LESSON_PIN)))
    assert parameters["lesson_pin_snapshot"] == _LESSON_PIN
    assert isinstance(parameters["lesson_pin_snapshot_sha256"], str)


def _attach(monkeypatch: pytest.MonkeyPatch, lesson_pin: dict[str, Any] | None) -> _Session:
    repository, session = _repository()
    run = {"run_id": _RUN_ID, "run_state": "INPUT_PROCESSING", "current_input_revision": 1}
    from sketch2life.infrastructure.story_run_lite import tables as story_tables

    # T-2c: the writer copies every non-drawing column, so the fake row names all of them.
    previous: dict[str, Any] = {column.name: None for column in story_tables.run_inputs.columns}
    previous.update(
        {
            "run_id": _RUN_ID,
            "input_revision": 1,
            "source_profile_revision_ref": "33333333-3333-4333-8333-333333333333",
            "context_revision": 1,
            "context_snapshot": {"schema_version": "sketch2life.parent-context.v1"},
            "context_snapshot_sha256": _HASH,
            "lesson_pin_snapshot": lesson_pin,
            "lesson_pin_snapshot_sha256": _HASH if lesson_pin is not None else None,
        }
    )
    monkeypatch.setattr(repository, "_owned_run", lambda *_args, **_kwargs: dict(run))
    monkeypatch.setattr(repository, "_current_input", lambda _run: dict(previous))
    monkeypatch.setattr(repository, "read_current_input", lambda **_kwargs: None)
    repository.attach_artwork(
        principal=_PRINCIPAL,
        run_id=_RUN_ID,
        original_asset_ref="parent/run/original",
        original_sha256=_HASH,
        original_media_type="image/png",
        original_size_bytes=2048,
        derived_asset_ref="parent/run/normalized.png",
        derived_sha256=_HASH,
        derived_size_bytes=1024,
        scanner_name="scanner",
        scanner_version="1",
    )
    return session


def test_attach_artwork_flushes_assets_before_the_lineage_insert(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _attach(monkeypatch, None)
    kinds = [kind for kind, _payload in session.events]
    assert kinds[:3] == ["add_all", "flush", "execute"]
    first_statement = session.events[2][1]
    assert first_statement.table.name == "core_asset_lineage"
    assert kinds.count("flush") == 1
    assert kinds[-1] == "commit"


def test_attach_artwork_without_lesson_pin_writes_sql_null(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parameters, sql = _bound_parameters(_attach(monkeypatch, None).insert_into("run_inputs"))
    assert "lesson_pin_snapshot" not in parameters
    assert "NULL" in sql


def test_attach_artwork_carries_an_existing_lesson_pin(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _attach(monkeypatch, dict(_LESSON_PIN))
    parameters, _sql = _bound_parameters(session.insert_into("run_inputs"))
    assert parameters["lesson_pin_snapshot"] == _LESSON_PIN


def test_profile_ref_is_nullable_only_in_the_schema() -> None:
    """FR-C-08 (D-218 A-4): the database accepts NULL; code requires it for live runs."""
    from sketch2life.infrastructure.story_run_lite import tables as story_tables

    assert story_tables.story_runs.c.profile_ref.nullable is True
    checks = {
        constraint.name: str(constraint.sqltext)
        for constraint in story_tables.story_runs.constraints
        if constraint.__class__.__name__ == "CheckConstraint"
    }
    assert "'DELETED'" in checks["ck_story_run_state"]
    receipt_checks = {
        constraint.name: str(constraint.sqltext)
        for constraint in story_tables.story_command_receipts.constraints
        if constraint.__class__.__name__ == "CheckConstraint"
    }
    assert "'DELETE_RUN'" in receipt_checks["ck_story_receipt_operation"]


def test_a_live_run_with_a_null_profile_ref_is_never_served(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from sketch2life.application.ports.parent_story_runs import ParentStoryRunError

    repository, _session = _repository()
    run = {"run_id": _RUN_ID, "run_state": "SCRIPT_REVIEW", "profile_ref": None}
    monkeypatch.setattr(repository, "_owned_run", lambda *_args, **_kwargs: dict(run))
    with pytest.raises(ParentStoryRunError) as refused:
        repository.get_run(principal=_PRINCIPAL, run_id=_RUN_ID)
    assert refused.value.status_code == 503


def test_a_deleted_tombstone_with_a_null_profile_ref_reads_as_the_projection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from sketch2life.application.ports.parent_story_runs import ParentStoryLifecycleRecord

    repository, session = _repository()
    run = {
        "run_id": _RUN_ID,
        "run_state": "DELETED",
        "revision": 5,
        "version": 7,
        "profile_ref": None,
        "current_input_revision": None,
    }
    monkeypatch.setattr(repository, "_owned_run", lambda *_args, **_kwargs: dict(run))
    view = repository.get_run(principal=_PRINCIPAL, run_id=_RUN_ID)
    assert isinstance(view, ParentStoryLifecycleRecord)
    assert (view.run_state, view.purge_state, view.revision) == ("DELETED", "COMPLETED", 5)
    assert session.events == []  # no input, story or profile read


def test_pending_receipt_writes_sql_null_response_body() -> None:
    repository, session = _repository()
    repository._store_pending_idempotency_receipt(
        principal=_PRINCIPAL,
        operation="GENERATE_STORY_REVISION",
        scope_kind="STORY_RUN",
        scope_ref=_RUN_ID,
        key_hash=_HASH,
        fingerprint=_HASH,
        run_id=_RUN_ID,
        resource_version=2,
        now=datetime.now(UTC),
    )
    parameters, sql = _bound_parameters(session.insert_into("command_receipts"))
    assert "response_body" not in parameters
    assert "NULL" in sql
    assert parameters["state"] == "PENDING"
