"""Migration and ORM alignment tests for T-6c (Manager emergency force-close)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.infrastructure.story_run_lite import tables as story_tables

_BACKEND = Path(__file__).resolve().parents[2]
_MIGRATION = _BACKEND / "alembic" / "versions" / "20261122_t6c_0001_story_force_close.py"
_PRIOR_OPERATIONS = {
    "CREATE_RUN",
    "ATTACH_ASSET",
    "CONFIRM_SUBJECT",
    "CONFIRM_CONTEXT",
    "CANCEL_RUN",
    "GENERATE_STORY_REVISION",
    "CONFIRM_STORY_REVISION",
    "DELETE_RUN",
    "SUBMIT_IDEA",
    "CONFIRM_TRANSCRIPT",
    "CREATE_VIDEO_GENERATION",
    "MARK_VIDEO_UNSUITABLE",
    "COMPLETE_RUN",
    "SELECT_ACTIVITY",
    "GENERATE_ACTIVITY_SET",
    "TRANSFER_TEACHER_OWNER",
}


def test_force_close_migration_chains_after_t6b_and_widens_receipt_check() -> None:
    """covers: D_T-6C_PROMPT.md Coordinator-1/3 & §5/§6"""
    assert _MIGRATION.is_file(), f"missing T-6c migration: {_MIGRATION}"
    spec = importlib.util.spec_from_file_location("t6c_migration", _MIGRATION)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.revision == "20261122_t6c_0001"
    assert module.down_revision == "20261122_t6b_0002"
    assert module.branch_labels is None
    assert module.depends_on is None

    receipt_check = next(
        constraint
        for constraint in story_tables.story_command_receipts.constraints
        if constraint.name == "ck_story_receipt_operation"
    )
    sql = str(receipt_check.sqltext)
    for op in _PRIOR_OPERATIONS | {"FORCE_CLOSE_RUN"}:
        assert f"'{op}'" in sql
    assert "reason_text" not in CoreAuditEntryModel.__table__.columns
