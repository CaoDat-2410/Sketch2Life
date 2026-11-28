from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path
from types import ModuleType

from sqlalchemy import CheckConstraint

from sketch2life.infrastructure.persistence.be1_models import (
    Be1CommandReceiptModel,
    Be1TeacherAssignmentTransferModel,
    ClassroomModel,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables

_BACKEND = Path(__file__).resolve().parents[2]
_VERSIONS = _BACKEND / "alembic" / "versions"
_BE1_PATH = _VERSIONS / "20261122_t6b_0001_be1_teacher_transfers.py"
_STORY_PATH = _VERSIONS / "20261122_t6b_0002_story_owner_transfer.py"


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"{path.stem}_migration", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _constants(path: Path) -> dict[str, object]:
    values: dict[str, object] = {}
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                try:
                    values[target.id] = ast.literal_eval(node.value)
                except (ValueError, TypeError):
                    continue
    return values


def _nodes(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    assert isinstance(value, (list, tuple))
    assert all(isinstance(item, str) for item in value)
    return tuple(value)


def _graph() -> dict[str, tuple[tuple[str, ...], tuple[str, ...]]]:
    graph: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {}
    for path in sorted(_VERSIONS.glob("*.py")):
        values = _constants(path)
        revision = values.get("revision")
        down, depends = values.get("down_revision"), values.get("depends_on")
        assert isinstance(revision, str)
        graph[revision] = (_nodes(down), _nodes(depends))
    return graph


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return node.func.id if isinstance(node.func, ast.Name) else None


def _column_specs(path: Path, table_name: str) -> dict[str, tuple[str, int | None, bool]]:
    found: dict[str, tuple[str, int | None, bool]] = {}
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if not isinstance(node, ast.Call) or _call_name(node) != "create_table":
            continue
        if not node.args:
            continue
        first = node.args[0]
        value = first.value if isinstance(first, ast.Constant) else (table_name if isinstance(first, ast.Name) and first.id == "TABLE" else None)
        if value != table_name:
            continue
        for item in node.args[1:]:
            if not isinstance(item, ast.Call) or _call_name(item) != "Column":
                continue
            name = item.args[0]
            type_call = item.args[1]
            assert isinstance(name, ast.Constant) and isinstance(type_call, ast.Call)
            type_name = _call_name(type_call)
            assert type_name is not None
            length_node = next(
                (kw.value for kw in type_call.keywords if kw.arg == "length"), None
            )
            nullable_node = next(
                (kw.value for kw in item.keywords if kw.arg == "nullable"), None
            )
            length = ast.literal_eval(length_node) if length_node is not None else None
            nullable = ast.literal_eval(nullable_node) if nullable_node is not None else True
            found[str(name.value)] = (type_name, length, bool(nullable))
    return found


def _orm_column_specs(table: object) -> dict[str, tuple[str, int | None, bool]]:
    return {
        column.name: (
            type(column.type).__name__,
            getattr(column.type, "length", None),
            bool(column.nullable),
        )
        for column in table.columns  # type: ignore[attr-defined]
    }


def _constraint_names(path: Path, table_name: str) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if not isinstance(node, ast.Call) or _call_name(node) != "create_table":
            continue
        if not node.args:
            continue
        first = node.args[0]
        value = first.value if isinstance(first, ast.Constant) else (table_name if isinstance(first, ast.Name) and first.id == "TABLE" else None)
        if value != table_name:
            continue
        for item in node.args[1:]:
            if not isinstance(item, ast.Call) or _call_name(item) not in {
                "PrimaryKeyConstraint",
                "ForeignKeyConstraint",
                "UniqueConstraint",
                "CheckConstraint",
            }:
                continue
            name = next((kw.value for kw in item.keywords if kw.arg == "name"), None)
            if isinstance(name, ast.Constant):
                names.add(str(name.value))
    return names


def _orm_constraint_names(table: object) -> set[str]:
    return {
        str(constraint.name)
        for constraint in table.constraints  # type: ignore[attr-defined]
        if constraint.name is not None
    }


def _orm_check(table: object, name: str) -> str:
    return next(
        str(constraint.sqltext)
        for constraint in table.constraints  # type: ignore[attr-defined]
        if isinstance(constraint, CheckConstraint) and constraint.name == name
    )


def _normal(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def test_three_revisions_extend_the_declared_heads_without_merging_them() -> None:
    be1, story = _load(_BE1_PATH), _load(_STORY_PATH)
    graph = _graph()
    assert (be1.revision, be1.down_revision) == ("20261122_t6b_0001", "20261125_nt_0003")
    assert (story.revision, story.down_revision) == ("20261122_t6b_0002", "20261125_as_0002")
    assert be1.depends_on is None and story.depends_on is None
    assert len(graph) == 83
    down_targets = {parent for downs, _ in graph.values() for parent in downs}
    depends_targets = down_targets | {parent for _, deps in graph.values() for parent in deps}
    assert len({revision for revision in graph if revision not in down_targets}) == 12
    assert len({revision for revision in graph if revision not in depends_targets}) == 1
    assert graph[be1.revision] == (("20261125_nt_0003",), ())
    assert graph[story.revision] == (("20261125_as_0002",), ())
    assert graph["20261122_t6c_0001"] == (("20261122_t6b_0002",), ())


def test_be1_transfer_table_and_added_columns_match_the_orm() -> None:
    module = _load(_BE1_PATH)
    orm = Be1TeacherAssignmentTransferModel.__table__
    assert _column_specs(_BE1_PATH, module.TABLE) == _orm_column_specs(orm)
    assert _constraint_names(_BE1_PATH, module.TABLE) == _orm_constraint_names(orm)
    assert {index.name for index in orm.indexes} == {
        "uq_be1_teacher_transfer_pending_class",
        "ix_be1_teacher_transfer_org_class_created",
        "ix_be1_teacher_transfer_state_updated",
    }
    assert "assignment_revision" in ClassroomModel.__table__.c
    assert "response_status" in Be1CommandReceiptModel.__table__.c
    assert "ck_be1_class_assignment_revision" in _orm_constraint_names(
        ClassroomModel.__table__
    )
    assert "ck_be1_command_receipt_status" in _orm_constraint_names(
        Be1CommandReceiptModel.__table__
    )
    assert "child_name" not in orm.c and "email" not in orm.c


def test_story_binding_epoch_receipt_and_orm_match_the_migration() -> None:
    module = _load(_STORY_PATH)
    runs = story_tables.story_runs
    assert runs.c.organization_ref.type.length == 128 and runs.c.organization_ref.nullable
    assert runs.c.class_ref.type.length == 128 and runs.c.class_ref.nullable
    assert runs.c.owner_epoch.type.__class__.__name__ == "BigInteger"
    assert runs.c.owner_epoch.nullable is False
    assert _normal(_orm_check(runs, "ck_story_run_owner_epoch")) == module.OWNER_EPOCH_CHECK
    assert _normal(_orm_check(runs, "ck_story_run_teacher_binding")) == module.NEW_BINDING_CHECK
    assert _normal(_orm_check(runs, "ck_story_run_teacher_owner")) == module.NEW_OWNER_CHECK
    assert "ix_story_run_teacher_class_owner" in {index.name for index in runs.indexes}
    receipt_check = _orm_check(story_tables.story_command_receipts, "ck_story_receipt_operation")
    force_close = _load(_VERSIONS / "20261122_t6c_0001_story_force_close.py")
    assert force_close.RECEIPT_OPERATIONS_BEFORE == module.RECEIPT_OPERATIONS_AFTER
    repair = _load(_VERSIONS / "20261126_as_0003_activity_set_receipt_operation.py")
    assert re.findall(r"'([A-Z_]+)'", receipt_check) == list(repair.RECEIPT_OPERATIONS_AFTER)
    assert "SELECT_ACTIVITY" in module.RECEIPT_OPERATIONS_BEFORE
    assert "TRANSFER_TEACHER_OWNER" in module.RECEIPT_OPERATIONS_AFTER
    assert len(module.RECEIPT_OPERATIONS_AFTER) == 17
    assert "child_name" not in runs.c and "email" not in runs.c
