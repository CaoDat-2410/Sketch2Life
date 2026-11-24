"""FEAT-066 goal v4 T-2e-a: the static shape of migration ``20261123_as_0001`` (DDL-B3, offline).

The owner approved this package by name: ``story.activity_selections`` (append-only, bounded
snapshot, one row per selection) and the ``SELECT_ACTIVITY`` receipt operation. The test pins the
column list, the constraint, index and trigger names, the ORM mirror, the receipt widening (13 to
14 names, the before set equal to the previous migration's after set), the downgrade guard and the
revision graph (one more revision, the Story branch head, heads stay 15 and 10). The behaviour of
the trigger, the checks and the round trip is proven on PostgreSQL in
``tests/integration/test_parent_activity_selection_postgres.py``.
"""

from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path
from types import ModuleType

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint

from sketch2life.infrastructure.story_run_lite import tables as story_tables

_VERSIONS = Path(__file__).resolve().parents[2] / "alembic" / "versions"
_MIGRATION = _VERSIONS / "20261123_as_0001_story_activity_selections.py"
_VIDEO_MIGRATION = _VERSIONS / "20261120_vb_0002_video_generations.py"
_REVISION = "20261123_as_0001"
_PARENT = "20261120_b2_0001"
SELECTIONS = story_tables.activity_selections


def _load(path: Path = _MIGRATION) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"{path.stem}_migration", path)
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


def _values(sql_list: str) -> list[str]:
    return re.findall(r"'([A-Z_]+)'", sql_list)


# ----------------------------------------------------------------------------- the revision graph
def test_the_revision_is_the_only_child_of_its_parent_and_the_review_epoch_follows_it() -> None:
    constants = _constants(_MIGRATION)
    assert constants["revision"] == _REVISION and len(_REVISION) <= 32
    assert constants["down_revision"] == _PARENT
    assert constants["branch_labels"] is None  # the frc08_lifecycle label is inherited
    assert constants["depends_on"] is None
    graph = _graph()
    assert {rev for rev, (downs, _) in graph.items() if _PARENT in downs} == {_REVISION}
    # V4-A T-1b-fix: DDL-B1c (``20261123_rv_0001``) is the one child; V4-B T-12b adds DDL-D
    # (``20261121_bpr_0001``) after that, which ends the branch.
    assert {rev for rev, (downs, _) in graph.items() if _REVISION in downs} == {
        "20261123_rv_0001"
    }


def test_one_more_revision_and_the_head_counts_are_sixteen_and_eleven() -> None:
    graph = _graph()
    # T-12a: 20261121_pce_0001 (Parent root); T-12b: 20261121_bpr_0001; T-12c: psn_0001, psn_0002;
    # T-12b-fix: 20261123_ppg_0001 (BE1 branch). AIPORT1 20261113_svg_catalog_review stays a
    # parallel child of 20261123_rv_0001 (one more head than Phase A alone).
    assert len(graph) == 60
    down_targets = {target for downs, _ in graph.values() for target in downs}
    dependency_targets = down_targets | {target for _, dep in graph.values() for target in dep}
    heads_down_only = {rev for rev in graph if rev not in down_targets}
    heads_with_depends = {rev for rev in graph if rev not in dependency_targets}
    assert (len(heads_down_only), len(heads_with_depends)) == (16, 11)
    assert _REVISION not in heads_down_only and _PARENT not in heads_down_only
    assert "20261113_svg_catalog_review" in heads_down_only  # AIPORT1 head, parallel to bpr
    assert "20261123_rv_0001" not in heads_down_only
    assert "20261121_bpr_0001" not in heads_down_only
    assert "20261123_ppg_0001" in heads_down_only
    assert "20261121_psn_0002" not in heads_down_only


# ----------------------------------------------------------------------------- the table
def test_the_column_list_is_closed_and_the_orm_mirror_is_equal() -> None:
    assert tuple(column.name for column in SELECTIONS.columns) == (
        "selection_id",
        "run_id",
        "selection_no",
        "target_understanding_revision",
        "source_kind",
        "lesson_id",
        "version_id",
        "content_sha256",
        "activity_index",
        "activity_snapshot",
        "activity_snapshot_sha256",
        "command_receipt_id",
        "actor_scope_kind",
        "actor_scope_ref",
        "created_at",
    )
    assert SELECTIONS.schema == "story" and SELECTIONS.name == "activity_selections"
    nullable = {column.name for column in SELECTIONS.columns if column.nullable}
    # only the lesson reference columns may be NULL (the AI draft shape reserved for T-2e-b)
    assert nullable == {"lesson_id", "version_id", "content_sha256", "activity_index"}
    source = _MIGRATION.read_text(encoding="utf-8")
    assert "op.create_table(" in source and "op.add_column(" not in source


def test_the_checks_equal_the_orm_checks_and_the_names_are_pinned() -> None:
    module = _load()
    assert [name for name, _ in module.CHECKS] == [
        "ck_as_selection_no",
        "ck_as_target_revision",
        "ck_as_source_kind",
        "ck_as_shape",
        "ck_as_snapshot_bound",
        "ck_as_snapshot_hash",
        "ck_as_actor_kind",
    ]
    orm = {
        constraint.name: re.sub(r"\s+", " ", str(constraint.sqltext))
        for constraint in SELECTIONS.constraints
        if isinstance(constraint, CheckConstraint)
    }
    assert orm == {name: re.sub(r"\s+", " ", sql) for name, sql in module.CHECKS}


def test_the_keys_and_the_index_are_mirrored() -> None:
    uniques = {
        constraint.name: [column.name for column in constraint.columns]
        for constraint in SELECTIONS.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert uniques == {
        "uq_as_run_selection_no": ["run_id", "selection_no"],
        "uq_as_command_receipt": ["command_receipt_id"],
    }
    foreign = {
        next(iter(column.parent for column in constraint.elements)).name: (
            str(constraint.elements[0].target_fullname),
            constraint.ondelete,
        )
        for constraint in SELECTIONS.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    }
    # the run key cascades (hygiene only: the purge deletes explicitly), the receipt key restricts
    assert foreign == {
        "run_id": ("story.runs.run_id", "CASCADE"),
        "command_receipt_id": ("story.command_receipts.receipt_id", "RESTRICT"),
    }
    (index,) = SELECTIONS.indexes
    assert index.name == "ix_as_run_target"
    assert [column.name for column in index.columns] == [
        "run_id",
        "target_understanding_revision",
        "selection_no",
    ]


def test_the_shape_check_ties_the_lesson_columns_to_the_source_kind() -> None:
    module = _load()
    shape = " ".join(dict(module.CHECKS)["ck_as_shape"].split())
    assert "source_kind = 'LESSON_ACTIVITY' AND lesson_id IS NOT NULL" in shape
    assert "length(content_sha256) = 64" in shape and "activity_index >= 0" in shape
    assert "source_kind = 'AI_DRAFT' AND lesson_id IS NULL" in shape
    assert "32768" in dict(module.CHECKS)["ck_as_snapshot_bound"]


# ----------------------------------------------------------------------------- the trigger
def test_the_trigger_forbids_update_only_so_the_purge_can_delete() -> None:
    module = _load()
    source = _MIGRATION.read_text(encoding="utf-8")
    assert "BEFORE UPDATE ON" in source and "FOR EACH ROW" in source
    assert "DELETE" not in " ".join(module.FUNCTION_SQL.split()).split("RAISE")[0]
    assert "BEFORE UPDATE OR DELETE" not in source and "OR DELETE" not in source
    assert "ACTIVITY_SELECTION_UPDATE_FORBIDDEN" in module.FUNCTION_SQL
    assert module.TRIGGER == "trg_story_activity_selection_append_only"


# ----------------------------------------------------------------------------- the receipt widening
def test_the_receipt_check_gains_exactly_select_activity() -> None:
    module = _load()
    previous = _load(_VIDEO_MIGRATION)
    # the before set is the final set of the previous revision that defined the check
    assert module.RECEIPT_OPERATIONS_BEFORE == previous.RECEIPT_OPERATIONS_AFTER
    before, after = (
        _values(module.RECEIPT_OPERATIONS_BEFORE),
        _values(module.RECEIPT_OPERATIONS_AFTER),
    )
    assert (len(before), len(after)) == (13, 14)
    assert after[:13] == before and after[13:] == ["SELECT_ACTIVITY"]
    assert len("SELECT_ACTIVITY") <= 32  # the operation column is varchar(32)
    orm = next(
        constraint
        for constraint in story_tables.story_command_receipts.constraints
        if isinstance(constraint, CheckConstraint)
        and constraint.name == "ck_story_receipt_operation"
    )
    assert _values(str(orm.sqltext)) == after


def test_the_downgrade_refuses_rows_and_receipts_before_it_removes_anything() -> None:
    module = _load()
    source = _MIGRATION.read_text(encoding="utf-8")
    downgrade = source[source.index("def downgrade()") :]
    assert downgrade.index("DOWNGRADE_GUARD") < downgrade.index("op.drop_constraint")
    assert downgrade.index("op.drop_constraint") < downgrade.index("DROP TRIGGER")
    assert downgrade.index("DROP TRIGGER") < downgrade.index("op.drop_table")
    guard = " ".join(module.DOWNGRADE_GUARD.split())
    assert "FROM story.activity_selections" in guard  # a row survives
    assert "operation IN ('SELECT_ACTIVITY')" in guard  # only receipts survive a purge
    assert "DDL-B3 downgrade refused" in guard
    assert "alembic downgrade 20261120_b2_0001" in (module.__doc__ or "")
    assert "never ``-1``" in (module.__doc__ or "")
