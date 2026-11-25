from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
from types import ModuleType

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint

from sketch2life.infrastructure.notifications.tables import PUSH_DELIVERIES

_VERSIONS = Path(__file__).resolve().parents[2] / "alembic" / "versions"
_MIGRATION = _VERSIONS / "20261125_nt_0003_push_deliveries.py"
_REVISION = "20261125_nt_0003"
_PARENT = "20261121_nt_0002"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("ntf1_push_deliveries_migration", _MIGRATION)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _constants(path: Path) -> dict[str, object]:
    found: dict[str, object] = {}
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in {
                "revision",
                "down_revision",
                "branch_labels",
                "depends_on",
            }:
                found[target.id] = ast.literal_eval(node.value)
    return found


def test_migration_is_the_notification_leaf_and_preserves_head_counts() -> None:
    constants = _constants(_MIGRATION)
    assert constants == {
        "revision": _REVISION,
        "down_revision": _PARENT,
        "branch_labels": None,
        "depends_on": None,
    }
    graph: dict[str, tuple[str, ...]] = {}
    for path in _VERSIONS.glob("*.py"):
        current = _constants(path)
        down = current.get("down_revision")
        graph[str(current["revision"])] = (
            () if down is None else (down,) if isinstance(down, str) else tuple(down)  # type: ignore[arg-type]
        )
    assert graph[_PARENT] == ("20261121_pg_0001",)
    assert graph[_REVISION] == (_PARENT,)
    down_targets = {down for parents in graph.values() for down in parents}
    assert _REVISION not in down_targets
    assert len(graph) == 64
    assert len([revision for revision in graph if revision not in down_targets]) == 16


def test_orm_mirror_has_only_the_approved_delivery_columns_and_constraints() -> None:
    module = _load()
    assert PUSH_DELIVERIES.schema == module.SCHEMA == "notifications"
    assert PUSH_DELIVERIES.name == module.TABLE == "push_deliveries"
    assert set(PUSH_DELIVERIES.c.keys()) == {
        "delivery_id",
        "inbox_item_id",
        "push_endpoint_id",
        "recipient_account_id",
        "status",
        "attempt_count",
        "next_attempt_at",
        "last_attempt_at",
        "last_error_code",
        "created_at",
        "completed_at",
    }
    checks = {
        str(constraint.name): " ".join(str(constraint.sqltext).split())
        for constraint in PUSH_DELIVERIES.constraints
        if isinstance(constraint, CheckConstraint)
    }
    assert set(checks) == {
        "ck_push_delivery_status",
        "ck_push_delivery_attempts",
        "ck_push_delivery_error",
        "ck_push_delivery_completed",
        "ck_push_delivery_times",
    }
    assert checks["ck_push_delivery_attempts"] == "attempt_count BETWEEN 0 AND 5"
    assert "ENDPOINT_GONE" in checks["ck_push_delivery_error"]
    assert "SENDER_ERROR" in checks["ck_push_delivery_error"]
    unique = next(
        constraint
        for constraint in PUSH_DELIVERIES.constraints
        if isinstance(constraint, UniqueConstraint)
    )
    assert unique.name == "uq_push_delivery_item_endpoint"
    assert [column.name for column in unique.columns] == ["inbox_item_id", "push_endpoint_id"]
    foreign_keys = [
        constraint
        for constraint in PUSH_DELIVERIES.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    ]
    assert len(foreign_keys) == 2
    assert {constraint.ondelete for constraint in foreign_keys} == {"RESTRICT"}
    assert {str(index.name) for index in PUSH_DELIVERIES.indexes} == {
        "ix_push_delivery_due",
        "ix_push_delivery_endpoint_pending",
    }
    for index in PUSH_DELIVERIES.indexes:
        assert "status = 'PENDING'" in str(index.dialect_options["postgresql"]["where"])


def test_migration_downgrade_refuses_rows_before_dropping_objects() -> None:
    source = _MIGRATION.read_text(encoding="utf-8")
    refusal = source.index('raise RuntimeError("push delivery downgrade refused: rows exist")')
    first_drop = source.index("op.drop_index")
    assert "SELECT EXISTS (SELECT 1 FROM {SCHEMA}.{TABLE} LIMIT 1)" in source
    assert refusal < first_drop
