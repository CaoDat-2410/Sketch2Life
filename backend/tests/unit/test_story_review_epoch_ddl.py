"""FEAT-066 goal v4 T-1b-fix: the static shape of migration ``20261123_rv_0001`` (DDL-B1c, offline).

The owner approved this package by name: ``story.story_revision_reviews`` gains ``review_epoch``
(1..3), the one-review-per-revision unique becomes one-per-epoch, nothing else changes. The test
pins the column, the constraint names, the swap order, the ORM mirror, the guarded downgrade, that
the receipt check is NOT touched, and the revision graph (one more revision on the Story branch,
heads stay 15 and 10). Behaviour and the round trip are proven on PostgreSQL in
``tests/integration/story_video/test_story_review_epoch_migration_postgres.py``.
"""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
from types import ModuleType

from sqlalchemy import CheckConstraint, SmallInteger, UniqueConstraint

from sketch2life.infrastructure.story_run_lite import tables as story_tables

_VERSIONS = Path(__file__).resolve().parents[2] / "alembic" / "versions"
_MIGRATION = _VERSIONS / "20261123_rv_0001_story_review_epoch.py"
_REVISION = "20261123_rv_0001"
_PARENT = "20261123_as_0001"
REVIEWS = story_tables.story_revision_reviews


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


# ----------------------------------------------------------------------------- the revision graph
def test_the_revision_is_the_only_child_of_the_story_head_and_precedes_svg_catalog() -> None:
    constants = _constants(_MIGRATION)
    assert constants["revision"] == _REVISION and len(_REVISION) <= 32
    assert constants["down_revision"] == _PARENT
    assert constants["branch_labels"] is None  # the frc08_lifecycle label is inherited
    assert constants["depends_on"] is None
    graph = _graph()
    assert {rev for rev, (downs, _) in graph.items() if _PARENT in downs} == {_REVISION}
    # V4-B T-12b adds DDL-D (``20261121_bpr_0001``) as a second child, parallel to the AIPORT1
    # ``20261113_svg_catalog_review`` (the Phase B squash keeps both heads).
    assert {rev for rev, (downs, _) in graph.items() if _REVISION in downs} == {
        "20261113_svg_catalog_review",
        "20261121_bpr_0001",
    }


def test_one_more_revision_and_the_head_counts_are_sixteen_and_eleven() -> None:
    graph = _graph()
    # T-12a: 20261121_pce_0001 (Parent root); T-12b: 20261121_bpr_0001; T-12c: psn_0001, psn_0002;
    # T-NTF1 adds 20261125_nt_0003 after the notification-chain head; AIPORT1 stays a parallel head.
    assert len(graph) == 64
    down_targets = {target for downs, _ in graph.values() for target in downs}
    dependency_targets = down_targets | {target for _, dep in graph.values() for target in dep}
    heads_down_only = {rev for rev in graph if rev not in down_targets}
    heads_with_depends = {rev for rev in graph if rev not in dependency_targets}
    assert (len(heads_down_only), len(heads_with_depends)) == (16, 11)
    assert "20261113_svg_catalog_review" in heads_down_only  # AIPORT1 head, parallel to bpr
    assert _REVISION not in heads_down_only and _PARENT not in heads_down_only
    assert "20261121_bpr_0001" not in heads_down_only
    assert "20261123_ppg_0001" in heads_down_only
    assert "20261121_psn_0002" not in heads_down_only


# ----------------------------------------------------------------------------- the table
def test_the_orm_mirror_has_the_epoch_column_and_the_swapped_constraints() -> None:
    module = _load()
    column = REVIEWS.c[module.COLUMN]
    assert module.COLUMN == "review_epoch"
    assert isinstance(column.type, SmallInteger) and column.nullable is False
    assert str(column.server_default.arg) == "1"  # type: ignore[union-attr]
    names = {str(constraint.name) for constraint in REVIEWS.constraints}
    assert module.NEW_UNIQUE in names and module.CHECK_NAME in names
    assert module.OLD_UNIQUE not in names
    unique = next(
        constraint
        for constraint in REVIEWS.constraints
        if isinstance(constraint, UniqueConstraint) and constraint.name == module.NEW_UNIQUE
    )
    assert [column.name for column in unique.columns] == ["story_revision_id", "review_epoch"]
    check = next(
        constraint
        for constraint in REVIEWS.constraints
        if isinstance(constraint, CheckConstraint) and constraint.name == module.CHECK_NAME
    )
    assert str(check.sqltext) == module.CHECK_EXPRESSION == "review_epoch BETWEEN 1 AND 3"
    # the targets of the video foreign keys and the receipt unique stay
    assert "uq_story_review_run_revision" in names
    assert REVIEWS.c.command_receipt_id.unique is True


def test_the_upgrade_adds_before_it_swaps_and_checks_last() -> None:
    source = _MIGRATION.read_text(encoding="utf-8")
    upgrade = source[source.index("def upgrade()") : source.index("def downgrade()")]
    add = upgrade.index("op.add_column")
    create_unique = upgrade.index("op.create_unique_constraint")
    drop_old = upgrade.index("op.drop_constraint")
    check = upgrade.index("op.create_check_constraint")
    assert add < create_unique < drop_old < check
    assert "OLD_UNIQUE" in upgrade[drop_old : drop_old + 120]


def test_the_downgrade_refuses_a_re_confirmation_before_it_removes_anything() -> None:
    module = _load()
    source = _MIGRATION.read_text(encoding="utf-8")
    downgrade = source[source.index("def downgrade()") :]
    assert downgrade.index("DOWNGRADE_GUARD") < downgrade.index("op.create_unique_constraint")
    assert downgrade.index("op.create_unique_constraint") < downgrade.index("op.drop_column")
    guard = " ".join(module.DOWNGRADE_GUARD.split())
    assert "review_epoch > 1" in guard and "DDL-B1c downgrade refused" in guard
    assert "op.drop_column" in downgrade and downgrade.rindex("op.drop_column") > downgrade.index(
        "NEW_UNIQUE"
    )


def test_the_receipt_check_is_not_touched() -> None:
    source = _MIGRATION.read_text(encoding="utf-8")
    assert "ck_story_receipt_operation" not in source.replace(
        "``ck_story_receipt_operation`` is NOT touched", ""
    )
    assert "command_receipts" not in source
