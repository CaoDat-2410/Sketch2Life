from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
from types import ModuleType

from sqlalchemy import CheckConstraint

from sketch2life.infrastructure.story_run_lite import tables

_VERSIONS = Path(__file__).resolve().parents[2] / "alembic" / "versions"
_MIGRATION = _VERSIONS / "20261122_t6c_0001_story_force_close.py"
_T6B = _VERSIONS / "20261122_t6b_0002_story_owner_transfer.py"


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"{path.stem}_migration", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _graph() -> dict[str, tuple[tuple[str, ...], tuple[str, ...]]]:
    graph: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {}
    for path in _VERSIONS.iterdir():
        if path.suffix != ".py":
            continue
        values: dict[str, object] = {}
        for node in ast.parse(path.read_text(encoding="utf-8")).body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Name) and target.id in {
                    "revision",
                    "down_revision",
                    "depends_on",
                }:
                    values[target.id] = ast.literal_eval(node.value)
        if "revision" not in values:
            continue
        down = values.get("down_revision")
        depends = values.get("depends_on")
        graph[str(values["revision"])] = (
            () if down is None else (down,) if isinstance(down, str) else tuple(down),
            ()
            if depends is None
            else (depends,)
            if isinstance(depends, str)
            else tuple(depends),
        )  # type: ignore[arg-type]
    return graph


def test_force_close_migration_is_one_child_of_t6b_and_preserves_heads() -> None:
    module = _load(_MIGRATION)
    t6b = _load(_T6B)
    assert (module.revision, module.down_revision) == (
        "20261122_t6c_0001",
        "20261122_t6b_0002",
    )
    assert module.branch_labels is None and module.depends_on is None
    assert module.RECEIPT_OPERATIONS_BEFORE == t6b.RECEIPT_OPERATIONS_AFTER
    assert module.RECEIPT_OPERATIONS_AFTER[-1] == "FORCE_CLOSE_RUN"
    assert len(module.RECEIPT_OPERATIONS_AFTER) == 17

    graph = _graph()
    assert len(graph) == 83
    down_targets = {parent for downs, _ in graph.values() for parent in downs}
    depends_targets = down_targets | {parent for _, deps in graph.values() for parent in deps}
    assert len({revision for revision in graph if revision not in down_targets}) == 12
    assert len({revision for revision in graph if revision not in depends_targets}) == 1
    assert {rev for rev, (downs, _) in graph.items() if "20261122_t6b_0002" in downs} == {
        "20261122_t6c_0001"
    }


def test_force_close_receipt_operation_matches_orm_and_is_append_only() -> None:
    module = _load(_MIGRATION)
    constraint = next(
        constraint
        for constraint in tables.story_command_receipts.constraints
        if isinstance(constraint, CheckConstraint)
        and constraint.name == "ck_story_receipt_operation"
    )
    assert all(
        f"'{operation}'" in str(constraint.sqltext)
        for operation in module.RECEIPT_OPERATIONS_AFTER
    )
    assert "FORCE_CLOSE_RUN" in module.GUARD_SQL
    assert "BEFORE UPDATE OR DELETE" in _MIGRATION.read_text(encoding="utf-8")
    assert "FORCE_CLOSE_RUN" in module.DOWNGRADE_GUARD
    source = _MIGRATION.read_text(encoding="utf-8")
    assert "reason_text" not in source and "core_audit_entries" not in source
    assert "FORCE_CLOSE_RUN" in str(constraint.sqltext)
