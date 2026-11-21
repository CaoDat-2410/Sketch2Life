"""FEAT-066 T-7b: static checks of the DDL-H migration ``20261120_cls_0001`` (no database).

The round trip on PostgreSQL (upgrade, downgrade by explicit revision, re-upgrade and the
downgrade guard) is in ``tests/integration/test_t7b_class_state_postgres.py``. This module pins the
text of the migration, its place in the revision graph and its equality with the ORM column.
"""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any, cast

from sqlalchemy import CheckConstraint, Table

from sketch2life.infrastructure.persistence.be1_models import ClassroomModel

_VERSIONS = Path(__file__).resolve().parents[2] / "alembic" / "versions"
_MIGRATION = _VERSIONS / "20261120_cls_0001_class_revision.py"
_REVISION = "20261120_cls_0001"
_PARENT = "20261119_oc_0001"
_LIBRARY_ROOT = "20261028_ll_0001"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("cls_0001_migration", _MIGRATION)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _constants(path: Path) -> dict[str, Any]:
    found: dict[str, Any] = {}
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


def _graph() -> dict[str, tuple[str, ...]]:
    graph: dict[str, tuple[str, ...]] = {}
    for path in sorted(_VERSIONS.glob("*.py")):
        constants = _constants(path)
        down = constants.get("down_revision")
        graph[str(constants["revision"])] = (
            () if down is None else (down,) if isinstance(down, str) else tuple(down)
        )
    return graph


def test_revision_is_a_short_unlabelled_child_on_the_lesson_library_chain() -> None:
    constants = _constants(_MIGRATION)
    assert constants["revision"] == _REVISION
    assert len(_REVISION) <= 32
    assert constants["down_revision"] == _PARENT
    assert constants["branch_labels"] is None
    assert constants["depends_on"] is None
    graph = _graph()
    assert _PARENT in graph
    children: dict[str, set[str]] = {}
    for revision, downs in graph.items():
        for down in downs:
            children.setdefault(down, set()).add(revision)
    # The new revision is the only child of its parent, so the lesson_library branch stays linear
    # (the T-3a chain test walks the same single-child chain).
    assert children[_PARENT] == {_REVISION}
    node = _LIBRARY_ROOT
    chain = [node]
    while children.get(node):
        # FEAT-072: the Platform Admin chain (20261119_admin_foundation onward) branches from
        # 20261110_ar_0001 as its own branch; it is not part of the lesson_library chain.
        next_nodes = {child for child in children[node] if "_admin_" not in child}
        assert len(next_nodes) == 1, node
        (node,) = next_nodes
        chain.append(node)
    assert _PARENT in chain and _REVISION in chain
    assert chain.index(_PARENT) + 1 == chain.index(_REVISION)


def test_the_check_text_equals_the_orm_check() -> None:
    module = _load()
    orm_checks = {
        str(constraint.name): str(constraint.sqltext)
        for constraint in cast(Table, ClassroomModel.__table__).constraints
        if isinstance(constraint, CheckConstraint)
    }
    assert orm_checks == {module.CHECK_NAME: module.CHECK_TEXT}
    assert module.CHECK_NAME == "ck_be1_class_revision"
    assert module.CHECK_TEXT == "revision > 0"


def test_orm_column_mirrors_the_migration() -> None:
    column = ClassroomModel.__table__.c.revision
    assert str(column.type) == "INTEGER"
    assert column.nullable is False
    assert column.default is not None and column.default.arg == 1
    assert column.server_default is not None and str(column.server_default.arg) == "1"


def test_migration_text_adds_one_column_one_check_and_no_table() -> None:
    text = _MIGRATION.read_text(encoding="utf-8")
    assert "create_table" not in text and "drop_table" not in text
    assert text.count("op.add_column(") == 1 and text.count("op.drop_column(") == 1
    assert text.count("op.create_check_constraint(") == 1
    assert text.count("op.drop_constraint(") == 1
    assert "alembic downgrade 20261119_oc_0001" in text
    assert "downgrade -1" not in text


def test_upgrade_and_downgrade_mirror_each_other() -> None:
    module = _load()
    calls: list[tuple[str, tuple[Any, ...]]] = []

    class _Op:
        def add_column(self, table: str, column: Any) -> None:
            calls.append(("add_column", (table, column.name, column.nullable)))

        def create_check_constraint(self, name: str, table: str, text: str) -> None:
            calls.append(("create_check", (name, table, text)))

        def drop_constraint(self, name: str, table: str, *, type_: str) -> None:
            calls.append(("drop_constraint", (name, table, type_)))

        def drop_column(self, table: str, column: str) -> None:
            calls.append(("drop_column", (table, column)))

        def execute(self, statement: Any) -> None:
            calls.append(("execute", (str(statement),)))

    module.__dict__["op"] = _Op()
    module.upgrade()
    module.downgrade()
    names = [name for name, _ in calls]
    assert names == [
        "add_column",
        "create_check",
        "execute",
        "drop_constraint",
        "drop_column",
    ]
    assert calls[0][1] == ("be1_classrooms", "revision", False)
    assert calls[1][1] == ("ck_be1_class_revision", "be1_classrooms", "revision > 0")
    assert "revision > 1" in calls[2][1][0] and "RAISE EXCEPTION" in calls[2][1][0]
    assert calls[3][1] == ("ck_be1_class_revision", "be1_classrooms", "check")
    assert calls[4][1] == ("be1_classrooms", "revision")
