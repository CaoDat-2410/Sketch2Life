"""FEAT-066 T-7d: static checks of the DDL-H migration ``20261120_cls_0002`` (no database).

The round trip on PostgreSQL (upgrade, downgrade to ``20261120_cls_0001`` by explicit revision,
re-upgrade, the two guards and the index behaviour) is in
``tests/integration/test_t7d_profile_move_postgres.py``. This module pins the text of the
migration, its place in the revision graph and its equality with the ORM indexes.
"""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any, cast

from sqlalchemy import Table, UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex

from sketch2life.infrastructure.persistence.be1_models import EnrollmentModel

_VERSIONS = Path(__file__).resolve().parents[2] / "alembic" / "versions"
_MIGRATION = _VERSIONS / "20261120_cls_0002_enrollment_active_unique.py"
_REVISION = "20261120_cls_0002"
_PARENT = "20261120_cls_0001"
_LIBRARY_ROOT = "20261028_ll_0001"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("cls_0002_migration", _MIGRATION)
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


def test_revision_is_a_short_unlabelled_single_child_of_the_class_revision_migration() -> None:
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
    assert children[_PARENT] == {_REVISION}
    # The lesson_library branch stays one linear chain with the new revision at its end.
    node = _LIBRARY_ROOT
    chain = [node]
    while children.get(node):
        # FEAT-072: the Platform Admin chain (20261119_admin_foundation onward) branches from
        # 20261110_ar_0001 as its own branch; it is not part of the lesson_library chain.
        next_nodes = {child for child in children[node] if "_admin_" not in child}
        assert len(next_nodes) == 1, node
        (node,) = next_nodes
        chain.append(node)
    # FEAT-066 T-8a: 20261120_nt_0001 (the notification inbox) now follows this revision.
    assert chain[-1] == "20261120_nt_0001"
    assert chain.index(_PARENT) + 1 == chain.index(_REVISION)
    assert chain.index(_REVISION) + 2 == len(chain)


def test_orm_has_no_full_unique_constraint_and_the_two_indexes_of_the_migration() -> None:
    module = _load()
    table = cast(Table, EnrollmentModel.__table__)
    assert not [c for c in table.constraints if isinstance(c, UniqueConstraint)]
    assert module.OLD_UNIQUE == "uq_be1_enrollment"
    indexes = {index.name: index for index in table.indexes}
    assert set(indexes) == {module.LOOKUP_INDEX, module.ACTIVE_UNIQUE_INDEX}

    lookup = indexes[module.LOOKUP_INDEX]
    assert [c.name for c in lookup.columns] == module.LOOKUP_COLUMNS
    assert lookup.unique is False

    active = indexes[module.ACTIVE_UNIQUE_INDEX]
    assert [c.name for c in active.columns] == module.ACTIVE_COLUMNS
    assert active.unique is True
    where = active.dialect_options["postgresql"]["where"]
    assert str(where) == module.ACTIVE_WHERE == "state = 'active'"
    ddl = str(CreateIndex(active).compile(dialect=postgresql.dialect()))  # type: ignore[no-untyped-call]
    assert "CREATE UNIQUE INDEX uq_be1_enrollment_active" in ddl
    assert "(organization_id, child_id)" in ddl and "WHERE state = 'active'" in ddl


def test_migration_text_swaps_one_constraint_for_two_indexes_and_has_no_delete() -> None:
    text = _MIGRATION.read_text(encoding="utf-8")
    assert "create_table" not in text and "drop_table" not in text
    assert text.count("op.drop_constraint(") == 1
    assert text.count("op.create_index(") == 2 and text.count("op.drop_index(") == 2
    assert text.count("op.create_unique_constraint(") == 1
    body = text.split("def upgrade", 1)[1]
    assert "DELETE" not in body.upper() and "UPDATE" not in body.upper()
    assert "alembic downgrade 20261120_cls_0001" in text
    assert "downgrade -1" not in text


def test_upgrade_and_downgrade_mirror_each_other_and_both_guard_first() -> None:
    module = _load()
    calls: list[tuple[str, tuple[Any, ...]]] = []

    class _Op:
        def execute(self, statement: Any) -> None:
            calls.append(("execute", (str(statement),)))

        def drop_constraint(self, name: str, table: str, *, type_: str) -> None:
            calls.append(("drop_constraint", (name, table, type_)))

        def create_index(
            self,
            name: str,
            table: str,
            columns: list[str],
            *,
            unique: bool = False,
            postgresql_where: Any = None,
        ) -> None:
            where = None if postgresql_where is None else str(postgresql_where)
            calls.append(("create_index", (name, table, tuple(columns), unique, where)))

        def drop_index(self, name: str, *, table_name: str) -> None:
            calls.append(("drop_index", (name, table_name)))

        def create_unique_constraint(self, name: str, table: str, columns: list[str]) -> None:
            calls.append(("create_unique", (name, table, tuple(columns))))

    module.__dict__["op"] = _Op()
    module.upgrade()
    upgrade_calls, calls[:] = list(calls), []
    module.downgrade()
    downgrade_calls = list(calls)

    assert [name for name, _ in upgrade_calls] == [
        "execute",
        "drop_constraint",
        "create_index",
        "create_index",
    ]
    guard = upgrade_calls[0][1][0]
    assert "state = 'active'" in guard and "HAVING count(*) > 1" in guard
    assert "RAISE EXCEPTION" in guard and "DELETE" not in guard.upper()
    assert upgrade_calls[1][1] == ("uq_be1_enrollment", "be1_enrollments", "unique")
    assert upgrade_calls[2][1] == (
        "ix_be1_enrollment_class_child",
        "be1_enrollments",
        ("organization_id", "class_id", "child_id"),
        False,
        None,
    )
    assert upgrade_calls[3][1] == (
        "uq_be1_enrollment_active",
        "be1_enrollments",
        ("organization_id", "child_id"),
        True,
        "state = 'active'",
    )

    assert [name for name, _ in downgrade_calls] == [
        "execute",
        "drop_index",
        "drop_index",
        "create_unique",
    ]
    down_guard = downgrade_calls[0][1][0]
    assert "GROUP BY organization_id, class_id, child_id HAVING count(*) > 1" in down_guard
    assert "RAISE EXCEPTION" in down_guard and "DELETE" not in down_guard.upper()
    assert downgrade_calls[1][1] == ("uq_be1_enrollment_active", "be1_enrollments")
    assert downgrade_calls[2][1] == ("ix_be1_enrollment_class_child", "be1_enrollments")
    assert downgrade_calls[3][1] == (
        "uq_be1_enrollment",
        "be1_enrollments",
        ("organization_id", "class_id", "child_id"),
    )
