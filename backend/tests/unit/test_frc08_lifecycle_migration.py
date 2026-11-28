from __future__ import annotations

import importlib.util
import re
from pathlib import Path

from sketch2life.infrastructure.story_run_lite.tables import story_command_receipts


def test_lifecycle_migration_preserves_every_existing_story_receipt_operation() -> None:
    migration_path = (
        Path(__file__).resolve().parents[2]
        / "alembic"
        / "versions"
        / "20261119_frc08_lifecycle_scope.py"
    )
    spec = importlib.util.spec_from_file_location("frc08_lifecycle_scope", migration_path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    runtime_constraint = next(
        constraint
        for constraint in story_command_receipts.constraints
        if constraint.name == "ck_story_receipt_operation"
    )
    runtime_operations = set(re.findall(r"'([^']+)'", str(runtime_constraint.sqltext)))
    migration_operations = set(re.findall(r"'([^']+)'", migration.RECEIPT_OPERATIONS_BEFORE))

    # The integration model includes operations added after this migration, so compare its
    # original operation set plus FR-C-08's addition as a subset rather than requiring equality.
    assert {"GENERATE_ACTIVITY_SET", "SELECT_ACTIVITY"} <= migration_operations
    assert "DELETE_RUN" in runtime_operations
    assert migration_operations | {"DELETE_RUN"} <= runtime_operations
