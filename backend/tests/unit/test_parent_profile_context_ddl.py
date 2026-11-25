"""FEAT-066 goal v4 T-12a: the static shape of migration ``20261121_pce_0001`` (DDL-D, offline).

One Parent table (``parent.profile_context_entries``), one append-only trigger, five named checks,
the page index, a RESTRICT foreign key (no terminal purge of the profile exists), no Story DDL and
no receipt DDL. The behaviour of the trigger, the checks and the round trip is proven on PostgreSQL
in ``tests/integration/test_parent_profile_context_postgres.py``.
"""

from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path
from types import ModuleType

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Table

from sketch2life.infrastructure.persistence.parent_models import (
    ParentPersistenceBase,
    ParentProfileContextEntryModel,
)

_VERSIONS = Path(__file__).resolve().parents[2] / "alembic" / "versions"
_MIGRATION = _VERSIONS / "20261121_pce_0001_parent_context_entries.py"
_REVISION = "20261121_pce_0001"
_PARENT = "20261109_m2_parent_profiles"
ENTRIES: Table = ParentProfileContextEntryModel.__table__  # type: ignore[assignment]


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("pce_0001_migration", _MIGRATION)
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


def _graph() -> dict[str, tuple[tuple[str, ...], tuple[str, ...]]]:
    graph: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {}
    for path in sorted(_VERSIONS.glob("*.py")):
        found = _constants(path)
        down, depends = found.get("down_revision"), found.get("depends_on")
        graph[str(found["revision"])] = (
            () if down is None else (down,) if isinstance(down, str) else tuple(down),  # type: ignore[arg-type]
            () if depends is None else (depends,) if isinstance(depends, str) else tuple(depends),  # type: ignore[arg-type]
        )
    return graph


def _normal(expression: str) -> str:
    return re.sub(r"\s+", " ", expression).strip()


def test_the_revision_is_the_only_child_of_the_parent_root_and_declares_no_label() -> None:
    constants = _constants(_MIGRATION)
    assert constants == {
        "revision": _REVISION,
        "down_revision": _PARENT,
        "branch_labels": None,
        "depends_on": None,
    }
    assert len(_REVISION) <= 32
    graph = _graph()
    assert {rev for rev, (downs, _) in graph.items() if _PARENT in downs} == {_REVISION}
    assert {rev for rev, (downs, _) in graph.items() if _REVISION in downs} == {
        "20261121_psn_0001"
    }


def test_the_graph_has_64_revisions_and_the_head_counts_are_sixteen_and_eleven() -> None:
    graph = _graph()
    # V4-B T-12b adds 20261121_bpr_0001 on the Story branch; T-12c adds 20261121_psn_0001
    # here (the Parent head) and 20261121_psn_0002 on the Story branch (53 before them).
    assert len(graph) == 64  # T-NTF1 adds 20261125_nt_0003 after the notification-chain head
    down_targets = {target for downs, _ in graph.values() for target in downs}
    dependency_targets = down_targets | {target for _, dep in graph.values() for target in dep}
    heads_down_only = {rev for rev in graph if rev not in down_targets}
    heads_with_depends = {rev for rev in graph if rev not in dependency_targets}
    assert (len(heads_down_only), len(heads_with_depends)) == (16, 11)
    assert _REVISION not in heads_down_only and _PARENT not in heads_down_only
    assert _REVISION not in heads_with_depends and _PARENT not in heads_with_depends
    assert "20261121_psn_0001" in heads_down_only and "20261121_psn_0001" in heads_with_depends


def test_the_migration_adds_one_parent_table_and_no_story_or_receipt_ddl() -> None:
    source = _MIGRATION.read_text(encoding="utf-8")
    module = _load()
    assert module.SCHEMA == "parent" and module.TABLE == "profile_context_entries"
    # one table is created, in the Parent schema only; the upgrade body names no Story object
    assert source.count("op.create_table(") == 1
    upgrade_body = source.split("def upgrade()", 1)[1].split("def downgrade()", 1)[0]
    for forbidden in ("story", "command_receipts", "run_inputs"):
        assert forbidden not in upgrade_body, forbidden


def test_the_column_list_is_closed_and_the_orm_mirror_is_equal() -> None:
    assert tuple(column.name for column in ENTRIES.columns) == (
        "context_entry_id",
        "parent_profile_id",
        "entry_kind",
        "short_text",
        "source_kind",
        "source_ref",
        "approximate_date",
        "created_by",
        "created_at",
    )
    assert {column.name for column in ENTRIES.columns if column.nullable} == {
        "source_ref",
        "approximate_date",
    }
    assert [column.name for column in ENTRIES.primary_key.columns] == ["context_entry_id"]
    assert "parent.profile_context_entries" in ParentPersistenceBase.metadata.tables
    migration = _MIGRATION.read_text(encoding="utf-8")
    for column in ENTRIES.columns:
        assert f'"{column.name}"' in migration, column.name


def test_the_checks_equal_the_orm_checks_and_the_names_are_pinned() -> None:
    module = _load()
    migration_checks = {name: _normal(expression) for name, expression in module.CHECKS}
    orm_checks = {
        str(constraint.name): _normal(str(constraint.sqltext))
        for constraint in ENTRIES.constraints
        if isinstance(constraint, CheckConstraint)
    }
    assert migration_checks == orm_checks
    assert set(migration_checks) == {
        "ck_parent_profile_context_entries_kind",
        "ck_parent_profile_context_entries_text",
        "ck_parent_profile_context_entries_source_kind",
        "ck_parent_profile_context_entries_source_ref",
        "ck_parent_profile_context_entries_created_by",
    }
    assert (
        "'OBSERVATION','ACHIEVEMENT','OUTSIDE_EXPERIENCE'"
        in migration_checks["ck_parent_profile_context_entries_kind"]
    )


def test_the_foreign_key_restricts_and_the_page_index_is_mirrored() -> None:
    foreign = [c for c in ENTRIES.constraints if isinstance(c, ForeignKeyConstraint)]
    assert len(foreign) == 1
    assert foreign[0].name == "fk_parent_profile_context_entries_profile"
    assert foreign[0].ondelete == "RESTRICT"
    assert [element.target_fullname for element in foreign[0].elements] == [
        "parent.child_profiles.parent_profile_id"
    ]
    migration = _MIGRATION.read_text(encoding="utf-8")
    assert (
        'ondelete="RESTRICT"' in migration
        and "CASCADE" not in migration.split("def upgrade()", 1)[1]
    )
    index = {index.name: [column.name for column in index.columns] for index in ENTRIES.indexes}
    assert index == {
        "ix_parent_profile_context_entries_page": [
            "parent_profile_id",
            "created_at",
            "context_entry_id",
        ]
    }
    module = _load()
    assert module.INDEX == "ix_parent_profile_context_entries_page"


def test_the_trigger_forbids_update_only_so_the_purge_can_delete() -> None:
    module = _load()
    assert "BEFORE UPDATE" in _normal(
        _MIGRATION.read_text(encoding="utf-8")
    ) and "BEFORE UPDATE OR DELETE" not in _normal(_MIGRATION.read_text(encoding="utf-8"))
    assert "RAISE EXCEPTION" in module.FUNCTION_SQL
    assert module.TRIGGER == "trg_parent_profile_context_entries_append_only"


def test_the_downgrade_refuses_rows_before_it_removes_anything() -> None:
    module = _load()
    assert "SELECT 1 FROM parent.profile_context_entries" in module.DOWNGRADE_GUARD
    assert "RAISE EXCEPTION" in module.DOWNGRADE_GUARD
    tree = ast.parse(_MIGRATION.read_text(encoding="utf-8"))
    downgrade = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "downgrade"
    )
    statements = [ast.unparse(statement) for statement in downgrade.body]
    assert "DOWNGRADE_GUARD" in statements[0]
    assert "DROP TRIGGER" in statements[1] or "TRIGGER" in statements[1]
    assert "drop_table" in statements[-1]
