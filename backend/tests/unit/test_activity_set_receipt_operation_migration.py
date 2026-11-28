"""DDL-B4 fix: as_0003 restores GENERATE_ACTIVITY_SET to the receipt check (offline)."""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from types import ModuleType

from sqlalchemy import CheckConstraint

from sketch2life.infrastructure.story_run_lite import tables

_VERSIONS = Path(__file__).resolve().parents[2] / "alembic" / "versions"
_MIGRATION = _VERSIONS / "20261126_as_0003_activity_set_receipt_operation.py"


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_revision_keeps_the_full_receipt_operation_union() -> None:
    module = _load(_MIGRATION)
    force_close = _load(_VERSIONS / "20261122_t6c_0001_story_force_close.py")
    activity_sets = _load(_VERSIONS / "20261125_as_0002_activity_suggestion_sets.py")
    assert (module.revision, module.down_revision) == ("20261126_as_0003", "20261122_t6c_0001")
    assert module.RECEIPT_OPERATIONS_BEFORE == force_close.RECEIPT_OPERATIONS_AFTER
    assert module.RECEIPT_OPERATIONS_AFTER == module.RECEIPT_OPERATIONS_BEFORE
    assert len(module.RECEIPT_OPERATIONS_AFTER) == 17
    assert set(module.RECEIPT_OPERATIONS_AFTER) == {
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
        "FORCE_CLOSE_RUN",
    }
    # nothing that an earlier revision allowed may be missing at the head
    earlier = set(re.findall(r"'([A-Z_]+)'", activity_sets.RECEIPT_OPERATIONS_AFTER))
    assert earlier <= set(module.RECEIPT_OPERATIONS_AFTER)


def test_final_receipt_check_equals_the_orm_check() -> None:
    module = _load(_MIGRATION)
    constraint = next(
        item
        for item in tables.story_command_receipts.constraints
        if isinstance(item, CheckConstraint) and item.name == "ck_story_receipt_operation"
    )
    assert re.findall(r"'([A-Z_]+)'", str(constraint.sqltext)) == list(
        module.RECEIPT_OPERATIONS_AFTER
    )


def test_upgrade_tolerates_a_missing_constraint_and_downgrade_is_guarded() -> None:
    module = _load(_MIGRATION)
    source = _MIGRATION.read_text(encoding="utf-8")
    assert "DROP CONSTRAINT IF EXISTS" in source
    assert "GENERATE_ACTIVITY_SET" in module.DOWNGRADE_GUARD
    assert "RAISE EXCEPTION" in module.DOWNGRADE_GUARD


def test_upgrade_converts_legacy_profile_reference_types_without_skipping_values() -> None:
    source = _MIGRATION.read_text(encoding="utf-8")
    assert "ALTER COLUMN source_profile_revision_ref TYPE uuid" in source
    assert "ALTER COLUMN parent_profile_id TYPE uuid" in source
    assert "ADD CONSTRAINT fk_parent_profile_share_profile" in source
