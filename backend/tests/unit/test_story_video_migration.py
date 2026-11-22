"""FEAT-066 T-1a: static checks of the DDL-B1 part 2 migration ``20261120_vb_0002`` (no database).

The round trip on PostgreSQL (upgrade, guarded downgrade to ``20261120_b1_0001``, re-upgrade) is in
``tests/integration/story_video/test_video_roundtrip_postgres.py`` and the behaviour of the CHECKs,
the partial indexes and the composite keys is in ``test_video_generations_postgres.py``. This module
pins the text of the migration, its place in the revision graph (one child of part 1, heads stay
14 and 10) and its equality with the ORM tables of ``story_run_lite/tables.py``.
"""

from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path
from types import ModuleType
from typing import Any

from sqlalchemy import CheckConstraint, Index, Table

from sketch2life.application.ports.story_run_lifecycle import PUBLIC_RUN_STATES
from sketch2life.infrastructure.story_run_lite import tables

_VERSIONS = Path(__file__).resolve().parents[2] / "alembic" / "versions"
_MIGRATION = _VERSIONS / "20261120_vb_0002_video_generations.py"
_REVISION = "20261120_vb_0002"
_PARENT = "20261120_b1_0001"
_LIFECYCLE = "20261119_frc08_lifecycle_scope"
_B1_MIGRATION = _VERSIONS / "20261120_b1_0001_story_voice_transcript.py"


def _load(path: Path = _MIGRATION) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"{path.stem}_migration", path)
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


def _normal(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _orm_checks(table: Table) -> dict[str, str]:
    return {
        str(constraint.name): _normal(str(constraint.sqltext))
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }


def _values(sql_list: str) -> list[str]:
    return re.findall(r"'([A-Z_]+)'", sql_list)


# ------------------------------------------------------------------------------- the chain
def test_revision_is_a_short_unlabelled_child_of_part_one_and_the_only_one() -> None:
    constants = _constants(_MIGRATION)
    assert constants["revision"] == _REVISION
    assert len(_REVISION) <= 32
    assert constants["down_revision"] == _PARENT
    assert constants["branch_labels"] is None  # the frc08_lifecycle label is inherited
    assert constants["depends_on"] is None
    graph = _graph()
    # No fallback onto the lifecycle revision: that would fork the branch (two heads) and both
    # revisions replace the same two CHECKs (plan review F-03).
    assert {rev for rev, downs in graph.items() if _LIFECYCLE in downs} == {_PARENT}
    assert {rev for rev, downs in graph.items() if _PARENT in downs} == {_REVISION}
    assert graph[_REVISION] == (_PARENT,)


def test_the_head_counts_stay_fifteen_and_ten() -> None:
    # FEAT-072 adds the Platform Admin branch from 20261110_ar_0001: one more down-only head.
    graph: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {}
    for path in sorted(_VERSIONS.glob("*.py")):
        constants = _constants(path)
        down, depends = constants.get("down_revision"), constants.get("depends_on")
        graph[str(constants["revision"])] = (
            () if down is None else (down,) if isinstance(down, str) else tuple(down),
            () if depends is None else (depends,) if isinstance(depends, str) else tuple(depends),
        )
    down_targets = {target for down, _ in graph.values() for target in down}
    dependency_targets = down_targets | {target for _, dep in graph.values() for target in dep}
    heads_down_only = {rev for rev in graph if rev not in down_targets}
    heads_with_depends = {rev for rev in graph if rev not in dependency_targets}
    assert (len(heads_down_only), len(heads_with_depends)) == (15, 10)
    # T-4b2: ``20261120_b2_0001`` (DDL-B2) follows this revision and is the head of the branch now.
    assert _REVISION not in heads_down_only and _PARENT not in heads_down_only
    assert "20261120_b2_0001" in heads_down_only
    assert {rev for rev, (downs, _) in graph.items() if _REVISION in downs} == {"20261120_b2_0001"}


# --------------------------------------------------------------- the two replaced CHECK sets
def test_the_final_sets_are_exactly_part_one_plus_the_values_t1a_writes() -> None:
    module = _load()
    part_one = _load(_B1_MIGRATION)
    assert module.RUN_STATES_BEFORE == part_one.RUN_STATES_AFTER
    assert module.RECEIPT_OPERATIONS_BEFORE == part_one.RECEIPT_OPERATIONS_AFTER
    before = _values(module.RUN_STATES_BEFORE)
    after = _values(module.RUN_STATES_AFTER)
    assert (len(before), len(after)) == (12, 18)
    assert after[:12] == before
    assert set(after[12:]) == {
        "VIDEO_QUEUED",
        "VIDEO_GENERATING",
        "VIDEO_SAFETY_VALIDATING",
        "VIDEO_READY",
        "SAFETY_BLOCKED",
        "ABANDONED",
    }
    assert set(after) <= set(PUBLIC_RUN_STATES)
    # DRAFT and STORY_GENERATING are added by whoever first writes them (not T-1a).
    assert set(PUBLIC_RUN_STATES) - set(after) == {"DRAFT", "STORY_GENERATING"}
    operations_before = _values(module.RECEIPT_OPERATIONS_BEFORE)
    operations_after = _values(module.RECEIPT_OPERATIONS_AFTER)
    assert (len(operations_before), len(operations_after)) == (10, 13)
    assert set(operations_after[10:]) == {
        "CREATE_VIDEO_GENERATION",
        "MARK_VIDEO_UNSUITABLE",
        "COMPLETE_RUN",
    }
    assert "INPUT_REVIEW" in before and "SUBMIT_IDEA" in operations_before


def test_the_orm_run_state_and_receipt_checks_equal_the_final_sets() -> None:
    module = _load()
    runs = _orm_checks(tables.story_runs)
    receipts = _orm_checks(tables.story_command_receipts)
    assert runs["ck_story_run_state"] == _normal(f"run_state IN ({module.RUN_STATES_AFTER})")
    assert receipts["ck_story_receipt_operation"] == _normal(
        f"operation IN ({module.RECEIPT_OPERATIONS_AFTER})"
    )


# ------------------------------------------------------------------------ the new tables
def test_the_generation_checks_equal_the_orm_checks() -> None:
    module = _load()
    expected = {name: _normal(text) for name, text in module.GENERATION_CHECKS}
    assert _orm_checks(tables.video_generations) == expected
    assert len(expected) == 11


def test_the_scene_checks_equal_the_orm_checks() -> None:
    module = _load()
    expected = {name: _normal(text) for name, text in module.SCENE_CHECKS}
    assert _orm_checks(tables.video_generation_scenes) == expected


def test_the_four_partial_unique_indexes_have_the_exact_predicates() -> None:
    module = _load()
    indexes: dict[str, Index] = {
        str(index.name): index for index in tables.video_generations.indexes
    }
    assert set(indexes) == {name for name, _c, _p in module.GENERATION_INDEXES}
    assert len(indexes) == 4
    for name, columns, predicate in module.GENERATION_INDEXES:
        index = indexes[name]
        assert index.unique
        assert [column.name for column in index.columns] == list(columns)
        assert _normal(str(index.dialect_options["postgresql"]["where"])) == _normal(predicate)
    by_name = {name: predicate for name, _c, predicate in module.GENERATION_INDEXES}
    # the review of a refused intent stays reusable; every other state consumes it
    assert by_name["uq_vg_review_consumed"] == "state <> 'ADMISSION_REJECTED'"
    assert by_name["uq_vg_one_ready"] == "state = 'READY'"
    assert by_name["uq_vg_number"] == "generation_no IS NOT NULL"
    assert set(_values(by_name["uq_vg_one_open"])) == {
        "ADMISSION_PENDING",
        "ACCEPTED",
        "QUEUED",
        "GENERATING",
        "TECHNICAL_VALIDATING",
        "SAFETY_VALIDATING",
    }


def test_the_composite_keys_and_uniques_are_in_the_orm() -> None:
    constraints = {
        str(constraint.name): constraint
        for constraint in tables.video_generations.constraints
        if constraint.name is not None
    }
    assert {"fk_vg_story_revision", "fk_vg_story_review", "uq_vg_job_ref", "uq_vg_run_key"} <= set(
        constraints
    )
    assert "uq_vg_generation_revision" in constraints
    scenes = {str(constraint.name) for constraint in tables.video_generation_scenes.constraints}
    assert {"fk_vgs_generation", "fk_vgs_scene", "uq_vgs_generation_scene"} <= scenes
    assert "uq_story_scene_revision_scene" in {
        str(constraint.name) for constraint in tables.story_scenes.constraints
    }
    assert "uq_story_review_run_revision" in {
        str(constraint.name) for constraint in tables.story_revision_reviews.constraints
    }


def test_the_run_columns_equal_the_migration() -> None:
    for name in (
        "current_video_generation_id",
        "adult_wait_started_at",
        "last_meaningful_activity_at",
        "finished_at",
    ):
        assert tables.story_runs.c[name].nullable is True
    foreign_keys = list(tables.story_runs.c.current_video_generation_id.foreign_keys)
    assert len(foreign_keys) == 1
    assert foreign_keys[0].ondelete == "SET NULL"
    assert foreign_keys[0].use_alter is True


def test_the_generation_columns_equal_the_migration_create_table() -> None:
    module = _load()
    recorder = _Recorder()
    module.__dict__["op"] = recorder
    module.upgrade()
    created = {args[0]: args[1:] for name, args, _k in recorder.calls if name == "create_table"}
    assert set(created) == {"video_generations", "video_generation_scenes"}
    for table_name, table in (
        ("video_generations", tables.video_generations),
        ("video_generation_scenes", tables.video_generation_scenes),
    ):
        migrated = {
            item.name: (re.sub(r"\(.*\)", "", str(item.type)), item.nullable)
            for item in created[table_name]
            if hasattr(item, "nullable") and hasattr(item, "type")
        }
        orm = {
            column.name: (re.sub(r"\(.*\)", "", str(column.type)), column.nullable)
            for column in table.columns
        }
        pk = next(column.name for column in table.columns if column.primary_key)
        migrated[pk] = (migrated[pk][0], False)
        assert migrated == orm, table_name


# --------------------------------------------------------------------- upgrade and downgrade
class _Recorder:
    """A fake ``op`` that records the calls of upgrade and downgrade, in order."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def __getattr__(self, name: str) -> Any:
        def record(*args: Any, **kwargs: Any) -> None:
            self.calls.append((name, args, kwargs))

        return record


def _run(module: ModuleType, function: str) -> list[tuple[str, tuple[Any, ...], dict[str, Any]]]:
    recorder = _Recorder()
    module.__dict__["op"] = recorder
    getattr(module, function)()
    return recorder.calls


def test_the_circular_pointer_is_added_after_both_tables_and_dropped_before_them() -> None:
    module = _load()
    up = _run(module, "upgrade")
    down = _run(module, "downgrade")
    up_order = [(name, args[0] if args else None) for name, args, _k in up if name != "execute"]
    tables_created = [i for i, (name, _a) in enumerate(up_order) if name == "create_table"]
    pointer_fk = up_order.index(("create_foreign_key", "fk_story_run_current_video_generation"))
    assert len(tables_created) == 2 and max(tables_created) < pointer_fk
    down_order = [(name, args[0] if args else None) for name, args, _k in down if name != "execute"]
    assert down_order.index(
        ("drop_constraint", "fk_story_run_current_video_generation")
    ) < down_order.index(("drop_table", "video_generation_scenes"))
    assert down_order.index(("drop_table", "video_generation_scenes")) < down_order.index(
        ("drop_table", "video_generations")
    )
    # the two M2 uniques are created first and dropped last
    assert up_order[0] == ("create_unique_constraint", "uq_story_scene_revision_scene")
    assert down_order[-1] == ("drop_constraint", "uq_story_scene_revision_scene")


def test_upgrade_and_downgrade_mirror_each_other() -> None:
    module = _load()
    up = _run(module, "upgrade")
    down = _run(module, "downgrade")
    up_names = [name for name, _a, _k in up]
    down_names = [name for name, _a, _k in down]
    assert up_names.count("create_table") == 2 and down_names.count("drop_table") == 2
    assert up_names.count("add_column") == 4 and down_names.count("drop_column") == 4
    assert up_names.count("create_index") == 4 and down_names.count("drop_index") == 4
    assert up_names.count("create_unique_constraint") == 2
    # the guard runs first
    assert down_names[0] == "execute"
    created = [args[0] for name, args, _k in up if name == "create_check_constraint"]
    assert created[-2:] == ["ck_story_run_state", "ck_story_receipt_operation"]
    recreated = [args[0] for name, args, _k in down if name == "create_check_constraint"]
    # part 1's two sets are restored (12 states, 10 operations), receipts first
    assert recreated == ["ck_story_receipt_operation", "ck_story_run_state"]
    restored = {args[0]: args[2] for name, args, _k in down if name == "create_check_constraint"}
    assert restored["ck_story_run_state"] == f"run_state IN ({module.RUN_STATES_BEFORE})"
    assert restored["ck_story_receipt_operation"] == (
        f"operation IN ({module.RECEIPT_OPERATIONS_BEFORE})"
    )
    dropped = [args[1] for name, args, _k in down if name == "drop_column"]
    assert dropped == [
        "finished_at",
        "last_meaningful_activity_at",
        "adult_wait_started_at",
        "current_video_generation_id",
    ]
    assert all(
        kwargs.get("schema") == "story"
        for _n, _a, kwargs in up
        if _n not in {"execute", "create_foreign_key"}
    )
    (foreign_key,) = [item for item in up if item[0] == "create_foreign_key"]
    assert foreign_key[2]["source_schema"] == "story"
    assert foreign_key[2]["referent_schema"] == "story"
    assert foreign_key[2]["ondelete"] == "SET NULL"


def test_the_guard_names_every_condition_the_reversal_would_lose() -> None:
    module = _load()
    guard = module.DOWNGRADE_GUARD
    for needle in (
        "story.video_generations",
        "'VIDEO_QUEUED','VIDEO_GENERATING','VIDEO_SAFETY_VALIDATING','VIDEO_READY'",
        "'SAFETY_BLOCKED','ABANDONED'",
        "current_video_generation_id IS NOT NULL",
        "'CREATE_VIDEO_GENERATION','MARK_VIDEO_UNSUITABLE','COMPLETE_RUN'",
    ):
        assert needle in guard, needle
    assert guard.count("RAISE EXCEPTION") == 3
    # the guard never refuses on a value part 1 owns (INPUT_REVIEW, SUBMIT_IDEA)
    assert "INPUT_REVIEW" not in guard and "SUBMIT_IDEA" not in guard


def test_the_clocks_are_backfilled_only_for_the_runs_that_wait_for_the_adult() -> None:
    module = _load()
    (statement,) = [args[0] for name, args, _k in _run(module, "upgrade") if name == "execute"]
    text = str(statement)
    assert "adult_wait_started_at = updated_at" in text
    assert "last_meaningful_activity_at = updated_at" in text
    assert set(_values(module.WAIT_RUN_STATES)) == {
        "INPUT_REVIEW",
        "SUBJECT_REVIEW",
        "PREPARATION_REVIEW",
        "SCRIPT_REVIEW",
    }
    assert "VIDEO_ADMISSION_PENDING" not in module.WAIT_RUN_STATES


def test_the_text_never_uses_a_relative_downgrade_a_label_or_a_grant() -> None:
    text = _MIGRATION.read_text(encoding="utf-8")
    assert "alembic downgrade 20261120_b1_0001" in text
    assert "downgrade -1" not in text.replace("never ``-1``", "")
    assert "branch_labels = None" in text
    assert "GRANT" not in text.replace("No GRANT statement", "")
    # no conditional Q4 item: the regeneration path owns its own migration if the owner chooses it
    assert "uq_story_revision_review_once" not in text
