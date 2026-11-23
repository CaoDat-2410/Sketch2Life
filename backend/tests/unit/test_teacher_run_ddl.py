"""FEAT-066 T-4b2: the static shape of migration ``20261120_b2_0001`` (DDL-B2, offline).

The owner approved this extension by name: the Teacher lock and its index, the occurrence pin, the
creator ref (provenance only), the per-occurrence unique index and the pins CHECK, exactly those.
The
test pins the closed column list, the constraint, index and trigger names, the lock-free state list
(the same five states in the CHECK, the trigger and the domain), the ORM mirror and the revision
graph (one more revision, the Story branch head, heads 14 and 10). The behaviour of the trigger and
the unique indexes is proven on PostgreSQL in ``tests/integration/story_teacher``.
"""

from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path
from types import ModuleType

from sqlalchemy import CheckConstraint

from sketch2life.domain.story_teacher import LOCK_FREE_STATES
from sketch2life.infrastructure.story_run_lite import tables as story_tables

_VERSIONS = Path(__file__).resolve().parents[2] / "alembic" / "versions"
_MIGRATION = _VERSIONS / "20261120_b2_0001_teacher_run_owner.py"
_PARENT = "20261120_vb_0002"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("b2_0001_migration", _MIGRATION)
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


def _graph() -> dict[str, tuple[str, ...]]:
    graph: dict[str, tuple[str, ...]] = {}
    for path in sorted(_VERSIONS.glob("*.py")):
        found = _constants(path)
        down = found.get("down_revision")
        graph[str(found["revision"])] = (
            () if down is None else (down,) if isinstance(down, str) else tuple(down)  # type: ignore[arg-type]
        )
    return graph


# ----------------------------------------------------------------------------- the revision graph
def test_the_revision_is_the_only_child_of_the_story_head() -> None:
    constants = _constants(_MIGRATION)
    assert constants["revision"] == "20261120_b2_0001"
    assert len(str(constants["revision"])) <= 32
    assert constants["down_revision"] == _PARENT
    assert constants["branch_labels"] is None  # the frc08_lifecycle label is inherited
    assert constants["depends_on"] is None
    graph = _graph()
    assert {rev for rev, downs in graph.items() if _PARENT in downs} == {"20261120_b2_0001"}
    # FEAT-066 goal v4 T-2e-a: DDL-B3 (``20261123_as_0001``) is the one child; V4-A T-1b-fix:
    # DDL-B1c (``20261123_rv_0001``) is the one child of that and ends the branch.
    assert {rev for rev, downs in graph.items() if "20261120_b2_0001" in downs} == {
        "20261123_as_0001"
    }
    assert {rev for rev, downs in graph.items() if "20261123_as_0001" in downs} == {
        "20261123_rv_0001"
    }
    assert {rev for rev, downs in graph.items() if "20261123_rv_0001" in downs} == {
        "20261113_svg_catalog_review"
    }
    assert graph["20261120_b2_0001"] == (_PARENT,)


# ----------------------------------------------------------------------------- the columns
def test_the_upgrade_adds_exactly_the_three_approved_columns_and_nothing_else() -> None:
    module = _load()
    assert module.COLUMNS == ("active_owner_teacher_id", "occurrence_ref", "created_by_actor_ref")
    source = _MIGRATION.read_text(encoding="utf-8")
    assert source.count("op.add_column(") == 1  # one loop over the closed list
    assert "op.create_table(" not in source and "op.alter_column(" not in source
    assert "ForeignKey" not in source  # an opaque occurrence ref: DDL-A forbids deleting one


def test_the_orm_mirror_holds_the_same_columns_constraints_and_indexes() -> None:
    module = _load()
    runs = story_tables.story_runs
    for column in module.COLUMNS:
        assert column in runs.c
        assert runs.c[column].type.length == 36 and runs.c[column].nullable
    checks = {
        constraint.name: str(constraint.sqltext)
        for constraint in runs.constraints
        if isinstance(constraint, CheckConstraint) and constraint.name in dict(module.CHECKS)
    }
    assert checks == dict(module.CHECKS)
    mirrored = {
        index.name: index for index in runs.indexes if index.name in {n for n, *_ in module.INDEXES}
    }
    assert set(mirrored) == {name for name, *_ in module.INDEXES}
    for name, column, _predicate in module.INDEXES:
        assert [c.name for c in mirrored[name].columns] == [column]
        assert mirrored[name].unique is name.startswith("uq_")


def test_the_names_are_pinned() -> None:
    module = _load()
    assert [name for name, _ in module.CHECKS] == [
        "ck_story_run_teacher_pins",
        "ck_story_run_teacher_owner",
        "ck_story_run_teacher_lock_state",
    ]
    assert [name for name, *_ in module.INDEXES] == [
        "uq_story_run_active_teacher",
        "uq_story_run_active_occurrence",
        "ix_story_run_occurrence",
    ]
    assert module.TRIGGER == "trg_story_run_release_teacher_lock"
    assert module.FUNCTION == "release_teacher_lock"


def test_the_index_predicates_are_the_lock_and_the_pin() -> None:
    module = _load()
    predicates = {name: predicate for name, _, predicate in module.INDEXES}
    assert predicates["uq_story_run_active_teacher"] == "active_owner_teacher_id IS NOT NULL"
    # one active Teacher run per occurrence: the unique index covers the locked rows only
    assert predicates["uq_story_run_active_occurrence"] == "active_owner_teacher_id IS NOT NULL"
    assert predicates["ix_story_run_occurrence"] == "occurrence_ref IS NOT NULL"


# ----------------------------------------------------------------------------- the lock-free states
def test_the_lock_free_states_are_the_same_five_everywhere() -> None:
    module = _load()
    expected = {"COMPLETED", "FAILED", "ABANDONED", "DELETE_PENDING", "DELETED"}
    assert expected == set(LOCK_FREE_STATES)
    listed = set(re.findall(r"'([A-Z_]+)'", module.LOCK_FREE_STATES))
    assert listed == expected
    assert listed <= set(re.findall(r"'([A-Z_]+)'", _state_check()))
    assert "SAFETY_BLOCKED" not in listed  # an adult-wait state keeps the lock (SRS l.394)
    assert dict(module.CHECKS)["ck_story_run_teacher_lock_state"].count("COMPLETED") == 1
    assert "COMPLETED" in module.FUNCTION_SQL and "SAFETY_BLOCKED" not in module.FUNCTION_SQL


def _state_check() -> str:
    check = next(
        constraint
        for constraint in story_tables.story_runs.constraints
        if isinstance(constraint, CheckConstraint) and constraint.name == "ck_story_run_state"
    )
    return str(check.sqltext)


def test_every_run_state_is_classified_as_holding_the_lock_or_not() -> None:
    """A state added by a later task must be classified in the trigger and the CHECK together."""

    states = set(re.findall(r"'([A-Z_]+)'", _state_check()))
    assert len(states) == 18
    keeps = states - set(LOCK_FREE_STATES)
    assert {"SAFETY_BLOCKED", "VIDEO_READY", "SCRIPT_REVIEW", "INPUT_PROCESSING"} <= keeps
    assert len(keeps) == 13


# ----------------------------------------------------------------------------- the trigger text
def test_the_trigger_clears_only_the_teacher_lock_before_the_state_update() -> None:
    module = _load()
    function = " ".join(module.FUNCTION_SQL.split())
    assert "NEW.active_owner_teacher_id := NULL" in function
    assert "active_owner_parent_account_id" not in function  # the Parent column is untouched
    source = _MIGRATION.read_text(encoding="utf-8")
    assert "BEFORE UPDATE OF run_state ON" in source and "FOR EACH ROW" in source


def test_the_downgrade_refuses_before_it_removes_anything() -> None:
    module = _load()
    source = _MIGRATION.read_text(encoding="utf-8")
    downgrade = source[source.index("def downgrade()") :]
    assert downgrade.index("DOWNGRADE_GUARD") < downgrade.index("DROP TRIGGER")
    assert downgrade.index("DROP TRIGGER") < downgrade.index("op.drop_column")
    guard = " ".join(module.DOWNGRADE_GUARD.split())
    for column in module.COLUMNS:
        assert f"{column} IS NOT NULL" in guard
    assert "T-4b2 downgrade refused" in guard
    assert "alembic downgrade 20261120_vb_0002" in (module.__doc__ or "")
    assert "never ``-1``" in (module.__doc__ or "")
