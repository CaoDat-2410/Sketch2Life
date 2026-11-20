"""FEAT-066 T-3a: static checks of the DDL-A migration ``20261119_oc_0001`` (no database).

The behaviour of the CHECKs and triggers is proven on PostgreSQL in
``tests/integration/lesson_occurrences/test_ddl_a_triggers_postgres.py``; this module pins the
shape of the migration text, its place in the revision graph and its equality with the Core
tables of ``infrastructure/lesson_occurrences/tables.py``.
"""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from sketch2life.infrastructure.lesson_occurrences import tables

_VERSIONS = Path(__file__).resolve().parents[2] / "alembic" / "versions"
_MIGRATION = _VERSIONS / "20261119_oc_0001_lesson_occurrence_plan.py"
_REVISION = "20261119_oc_0001"
_LIBRARY_ROOT = "20261028_ll_0001"

_TABLES = (
    "occurrences",
    "source_documents",
    "document_revisions",
    "plan_revisions",
    "plan_activities",
)


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("oc_0001_migration", _MIGRATION)
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
    assert constants["branch_labels"] is None
    assert constants["depends_on"] is None
    graph = _graph()
    parent = constants["down_revision"]
    assert isinstance(parent, str) and parent in graph
    # The parent is the one lesson_library predecessor: the chain below the branch root is linear,
    # so the test does not pin the parent text and keeps passing when a task is re-ordered.
    children: dict[str, set[str]] = {}
    for revision, downs in graph.items():
        for down in downs:
            children.setdefault(down, set()).add(revision)
    assert children[parent] == {_REVISION}
    node = _LIBRARY_ROOT
    chain = [node]
    while children.get(node):
        assert len(children[node]) == 1, node
        (node,) = children[node]
        chain.append(node)
    assert _REVISION in chain
    assert chain.index(parent) + 1 == chain.index(_REVISION)


def test_names_checks_and_the_composite_pointer_are_spelled_out() -> None:
    module = _load()
    text = _MIGRATION.read_text(encoding="utf-8")
    assert module.SCHEMA == "lesson" and module.TABLES == _TABLES
    # A1: composite, immediate pointer, with the unique pair it needs.
    assert "fk_occ_approved_plan" in text and "uq_plan_id_occurrence" in text
    assert '["approved_plan_revision_id", "occurrence_id"]' in text
    assert '["plan_revision_id", "occurrence_id"]' in text
    assert "DEFERRABLE" not in text and "deferrable" not in text and "initially" not in text
    assert "OCCURRENCE_PLAN_NOT_APPROVED" in text
    # One approved plan per occurrence (SRS l.775) and the FR-T-09 approval backstop (l.548).
    assert "uq_plan_one_approved" in text and "state = 'APPROVED'" in text
    assert "LESSON_PLAN_CHECKLIST_REQUIRED" in text
    # A2: a plan is born a draft with the occurrence's pin and a document of the same occurrence.
    for fragment in (
        "PLAN_INSERT_NOT_DRAFT",
        "PLAN_PIN_MISMATCH",
        "PLAN_DOCUMENT_MISMATCH",
        "PLAN_REVISION_NUMBER_GAP",
        "PLAN_OBJECTIVE_INVALID",
    ):
        assert fragment in text
    names = {name for checks in _all_checks(module) for name, _ in checks}
    assert {
        "ck_occ_title",
        "ck_occ_state",
        "ck_occ_plan_state",
        "ck_occ_pin",
        "ck_occ_sample",
        "ck_srcdoc_extension",
        "ck_srcdoc_pages",
        "ck_srcdoc_deleted",
        "ck_docrev_lineage",
        "ck_docrev_text_size",
        "ck_docrev_text_hash",
        "ck_docrev_review",
        "ck_plan_objectives",
        "ck_plan_approval",
        "ck_plan_hash",
        "ck_plan_pin",
        "ck_planact_order",
        "ck_planact_shape",
        "ck_planact_checklist",
    } <= names
    assert "BETWEEN 1 AND 12" in dict(module.PLAN_REVISION_CHECKS)["ck_plan_objectives"]
    assert "BETWEEN 1 AND 24" in dict(module.PLAN_ACTIVITY_CHECKS)["ck_planact_order"]
    assert "2097152" in dict(module.DOCUMENT_REVISION_CHECKS)["ck_docrev_text_size"]
    assert "BETWEEN 1 AND 100" in dict(module.SOURCE_DOCUMENT_CHECKS)["ck_srcdoc_pages"]
    assert [function for _t, function, _e in module.TRIGGERS] == [
        "protect_occurrence",
        "protect_source_document",
        "protect_document_revision",
        "protect_plan_revision",
        "protect_plan_activity",
    ]
    assert all(events == "INSERT OR UPDATE OR DELETE" for _t, _f, events in module.TRIGGERS)


def _all_checks(module: ModuleType) -> list[tuple[tuple[str, str], ...]]:
    return [
        module.OCCURRENCE_CHECKS,
        module.SOURCE_DOCUMENT_CHECKS,
        module.DOCUMENT_REVISION_CHECKS,
        module.PLAN_REVISION_CHECKS,
        module.PLAN_ACTIVITY_CHECKS,
    ]


def test_every_constraint_and_index_name_is_unique_and_within_the_limit() -> None:
    module = _load()
    names = [name for checks in _all_checks(module) for name, _ in checks]
    tree = ast.parse(_MIGRATION.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            for keyword in node.keywords:
                if keyword.arg == "name" and isinstance(keyword.value, ast.Constant):
                    names.append(str(keyword.value.value))
            callee = ast.unparse(node.func)
            if callee in {"op.create_index", "op.create_foreign_key"} and isinstance(
                node.args[0], ast.Constant
            ):
                names.append(str(node.args[0].value))
    assert len(names) == len(set(names)), sorted(n for n in names if names.count(n) > 1)
    assert max(len(name) for name in names) <= 63
    existing = ""
    for path in _VERSIONS.glob("*.py"):
        if path != _MIGRATION:
            existing += path.read_text(encoding="utf-8")
    for name in names:
        assert f'"{name}"' not in existing, name


def test_downgrade_refuses_while_rows_exist_and_drops_in_reverse_order() -> None:
    tree = ast.parse(_MIGRATION.read_text(encoding="utf-8"))
    functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    downgrade = ast.unparse(functions["downgrade"])
    assert downgrade.index("_refuse_while_rows_exist()") < downgrade.index("drop_constraint")
    assert downgrade.index("drop_constraint") < downgrade.index("drop_table")
    assert "reversed(TABLES)" in downgrade and "DROP FUNCTION" in downgrade
    guard = ast.unparse(functions["_refuse_while_rows_exist"])
    assert "RuntimeError" in guard and "LIMIT 1" in guard


@pytest.mark.parametrize("table_with_rows", _TABLES)
def test_the_downgrade_guard_names_each_table_that_holds_a_row(table_with_rows: str) -> None:
    module = _load()

    class Bind:
        def __init__(self) -> None:
            self.asked: list[str] = []

        def execute(self, statement: object) -> object:
            sql = str(statement)
            self.asked.append(sql)
            has_row = sql.endswith(f"lesson.{table_with_rows} LIMIT 1")
            return SimpleNamespace(first=lambda: (1,) if has_row else None)

    bind = Bind()
    module.op = SimpleNamespace(get_bind=lambda: bind)
    with pytest.raises(RuntimeError) as refused:
        module.downgrade()
    assert f"lesson.{table_with_rows} holds rows" in str(refused.value)
    # Every table before the first non-empty one was asked; nothing was dropped.
    assert len(bind.asked) == _TABLES.index(table_with_rows) + 1


def test_the_downgrade_guard_lets_empty_tables_through() -> None:
    module = _load()
    calls: list[tuple[str, tuple[Any, ...]]] = []

    class Operations:
        @staticmethod
        def get_bind() -> object:
            return SimpleNamespace(execute=lambda _s: SimpleNamespace(first=lambda: None))

        def __getattr__(self, name: str) -> Any:
            return lambda *args, **kwargs: calls.append((name, args))

    module.op = Operations()
    module.downgrade()
    dropped = [args[0] for name, args in calls if name == "drop_table"]
    assert dropped == list(reversed(_TABLES))
    assert [name for name, _ in calls].count("drop_constraint") == 1
    assert [a[0] for n, a in calls if n == "execute"] == [
        f"DROP FUNCTION lesson.{function}()" for function in module.FUNCTIONS
    ]


def _migration_columns() -> dict[str, dict[str, bool]]:
    result: dict[str, dict[str, bool]] = {}
    tree = ast.parse(_MIGRATION.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and ast.unparse(node.func) == "op.create_table"):
            continue
        first = node.args[0]
        assert isinstance(first, ast.Constant)
        columns: dict[str, bool] = {}
        for argument in node.args[1:]:
            if not isinstance(argument, ast.Call):
                continue
            callee = ast.unparse(argument.func)
            if callee == "_created_at":
                columns["created_at"] = False
            elif callee == "sa.Column":
                name = argument.args[0]
                assert isinstance(name, ast.Constant)
                flags = {kw.arg: kw.value for kw in argument.keywords}
                primary = "primary_key" in flags
                not_null = (
                    isinstance(flags.get("nullable"), ast.Constant)
                    and flags["nullable"].value is False  # type: ignore[attr-defined]
                )
                columns[str(name.value)] = not (primary or not_null)
        result[str(first.value)] = columns
    return result


@pytest.mark.parametrize("table", _TABLES)
def test_core_table_columns_equal_the_migration(table: str) -> None:
    migration = _migration_columns()[table]
    core = getattr(tables, table.upper())
    assert tuple(column.name for column in core.columns) == tuple(migration)
    assert {column.name: column.nullable for column in core.columns} == migration
    assert core.schema == "lesson"
    assert core in tables.DDL_A_TABLES
    assert "lesson.library_items" not in {
        t.fullname for t in tables.OCCURRENCE_METADATA.tables.values()
    }
