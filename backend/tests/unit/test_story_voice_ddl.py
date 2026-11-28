"""FEAT-066 T-2c: static checks of the DDL-B1 migration ``20261120_b1_0001`` (no database).

The round trip on PostgreSQL (upgrade, downgrade by explicit revision, re-upgrade, the downgrade
guard and the behaviour of the CHECKs and partial indexes) is in
``tests/integration/test_parent_story_idea_postgres.py``. This module pins the text of the
migration, its place in the revision graph and its equality with the ORM tables of
``infrastructure/story_run_lite/tables.py``.
"""

from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from sqlalchemy import CheckConstraint, Index, Table

from sketch2life.infrastructure.story_run_lite import tables

_VERSIONS = Path(__file__).resolve().parents[2] / "alembic" / "versions"
_MIGRATION = _VERSIONS / "20261120_b1_0001_story_voice_transcript.py"
# FEAT-066 T-1a: DDL-B1 part 2 replaces the same two CHECKs on top of this revision; the ORM holds
# its final sets, so the equality of those two checks is asserted against that migration.
_NEXT_MIGRATION = _VERSIONS / "20261120_vb_0002_video_generations.py"
# FEAT-066 goal v4 T-2e-a widens the receipt check from 13 to 14 names; T-6b adds the 15th and
# T-6c adds the 16th.
# The ORM holds the final receipt set, so its assertion uses the latest migration below.
_RECEIPT_FINAL_MIGRATION = _VERSIONS / "20261123_as_0001_story_activity_selections.py"
_RECEIPT_TRANSFER_MIGRATION = _VERSIONS / "20261122_t6b_0002_story_owner_transfer.py"
_RECEIPT_FORCE_CLOSE_MIGRATION = _VERSIONS / "20261122_t6c_0001_story_force_close.py"
_REVISION = "20261120_b1_0001"
_PARENT = "20261119_frc08_lifecycle_scope"
_LESSON_LIBRARY_HEAD_AT_T3A = "20261119_oc_0001"


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


def test_revision_is_a_short_unlabelled_child_of_the_story_lifecycle_revision() -> None:
    constants = _constants(_MIGRATION)
    assert constants["revision"] == _REVISION
    assert len(_REVISION) <= 32
    assert constants["down_revision"] == _PARENT
    assert constants["branch_labels"] is None  # the frc08_lifecycle label is inherited
    assert constants["depends_on"] == ("20261112_parent_audio_transcripts",)
    graph = _graph()
    assert _PARENT in graph
    children = {rev for rev, downs in graph.items() if _PARENT in downs}
    assert children == {_REVISION}
    # T-1a chains after this revision (never a second child of the lifecycle revision).
    assert {rev for rev, downs in graph.items() if _REVISION in downs} == {"20261120_vb_0002"}
    # The T-3a lesson_library head is a different chain: it is not the parent.
    assert _LESSON_LIBRARY_HEAD_AT_T3A in graph
    assert graph[_REVISION] == (_PARENT,)


def test_the_run_input_checks_equal_the_orm_checks() -> None:
    module = _load()
    checks = _orm_checks(tables.run_inputs)
    assert "ck_story_run_input_typed_idea" not in checks
    assert checks["ck_story_run_input_idea"] == _normal(module.IDEA_CHECK)
    assert checks["ck_story_run_input_voice"] == _normal(module.VOICE_CHECK)
    # The Parent audio migration already allowed this value; DDL-B1 must preserve it for rows
    # written before the voice-input migration.
    assert "idea_source = 'TRANSCRIPT'" in module.IDEA_CHECK


def test_the_run_state_and_receipt_checks_equal_the_orm_checks() -> None:
    module = _load()
    final = _load(_NEXT_MIGRATION)
    receipt_final = _load(_RECEIPT_FINAL_MIGRATION)
    owner_transfer = _load(_RECEIPT_TRANSFER_MIGRATION)
    force_close = _load(_RECEIPT_FORCE_CLOSE_MIGRATION)
    runs = _orm_checks(tables.story_runs)
    receipts = _orm_checks(tables.story_command_receipts)
    # The ORM holds the final sets (T-1a); part 2 starts from exactly the sets of this revision.
    assert runs["ck_story_run_state"] == _normal(f"run_state IN ({final.RUN_STATES_AFTER})")
    # T-2e-a: the receipt set is the one of DDL-B3, which starts from the set of part 2.
    assert force_close.RECEIPT_OPERATIONS_BEFORE == owner_transfer.RECEIPT_OPERATIONS_AFTER
    repair = _load(_VERSIONS / "20261126_as_0003_activity_set_receipt_operation.py")
    assert re.findall(r"'([A-Z_]+)'", receipts["ck_story_receipt_operation"]) == list(
        repair.RECEIPT_OPERATIONS_AFTER
    )
    assert receipt_final.RECEIPT_OPERATIONS_BEFORE == final.RECEIPT_OPERATIONS_AFTER
    assert tuple(
        re.findall(r"'([A-Z_]+)'", receipt_final.RECEIPT_OPERATIONS_AFTER)
    ) == owner_transfer.RECEIPT_OPERATIONS_BEFORE
    assert final.RUN_STATES_BEFORE == module.RUN_STATES_AFTER
    assert final.RECEIPT_OPERATIONS_BEFORE == module.RECEIPT_OPERATIONS_AFTER
    assert module.RUN_STATES_AFTER.count("'") // 2 == 20
    assert "'INPUT_REVIEW'" in module.RUN_STATES_AFTER
    assert module.RECEIPT_OPERATIONS_AFTER.count("'") // 2 == 17
    assert module.RUN_STATES_BEFORE.count("'") // 2 == 20
    assert module.RECEIPT_OPERATIONS_BEFORE.count("'") // 2 == 17


def test_the_transcript_checks_equal_the_orm_checks() -> None:
    module = _load()
    expected = {name: _normal(text) for name, text in module.TRANSCRIPT_CHECKS}
    assert _orm_checks(tables.transcript_revisions) == expected
    assert len(expected) == 9


def test_the_two_partial_unique_indexes_equal_the_orm_indexes() -> None:
    indexes: dict[str, Index] = {
        str(index.name): index
        for index in tables.transcript_revisions.indexes
        if isinstance(index, Index)
    }
    assert set(indexes) == {"uq_story_transcript_confirmed", "uq_story_transcript_open"}
    for index in indexes.values():
        assert index.unique
        assert [column.name for column in index.columns] == ["run_id", "source_asset_ref"]
    assert str(indexes["uq_story_transcript_confirmed"].dialect_options["postgresql"]["where"]) == (
        "state = 'CONFIRMED'"
    )
    assert _normal(
        str(indexes["uq_story_transcript_open"].dialect_options["postgresql"]["where"])
    ) == ("state IN ('PENDING','NEEDS_CONFIRMATION')")


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


def test_upgrade_and_downgrade_mirror_each_other() -> None:
    module = _load()
    up = _run(module, "upgrade")
    down = _run(module, "downgrade")
    up_names = [name for name, _a, _k in up]
    down_names = [name for name, _a, _k in down]
    assert up_names.count("create_table") == 1
    assert down_names.count("drop_table") == 1
    assert up_names.count("add_column") == 3 and down_names.count("drop_column") == 3
    assert up_names.count("create_index") == 2 and down_names.count("drop_index") == 2
    # The guard runs first; the reversed steps follow in the opposite order of the upgrade.
    assert down_names[0] == "execute"
    created = [args[0] for name, args, _k in up if name == "create_check_constraint"]
    assert created[:2] == ["ck_story_run_input_idea", "ck_story_run_input_voice"]
    assert created[-2:] == ["ck_story_run_state", "ck_story_receipt_operation"]
    recreated = [args[0] for name, args, _k in down if name == "create_check_constraint"]
    assert recreated == [
        "ck_story_receipt_operation",
        "ck_story_run_state",
        "ck_story_run_input_typed_idea",
    ]
    dropped_columns = [args[1] for name, args, _k in down if name == "drop_column"]
    assert dropped_columns == ["voice_duration_ms", "voice_asset_version", "voice_asset_ref"]
    assert down_names.index("drop_table") < down_names.index("drop_column")
    assert all(kwargs.get("schema") == "story" for _n, _a, kwargs in up if _n != "execute")


def test_the_guard_names_every_condition_the_reversal_would_lose() -> None:
    module = _load()
    guard = module.DOWNGRADE_GUARD
    for needle in (
        "story.transcript_revisions",
        "voice_asset_ref IS NOT NULL",
        "voice_asset_version IS NOT NULL",
        "voice_duration_ms IS NOT NULL",
        "idea_source IN ('VOICE','TEXT_AND_VOICE')",
        "run_state = 'INPUT_REVIEW'",
        "'SUBMIT_IDEA','CONFIRM_TRANSCRIPT'",
    ):
        assert needle in guard, needle
    assert guard.count("RAISE EXCEPTION") == 4


def test_the_table_columns_equal_the_migration_create_table() -> None:
    module = _load()
    (call,) = [item for item in _run(module, "upgrade") if item[0] == "create_table"]
    _name, args, _kwargs = call
    assert args[0] == "transcript_revisions"
    migration_columns = {
        item.name: (str(item.type), item.nullable)
        for item in args[1:]
        if hasattr(item, "nullable") and hasattr(item, "type")
    }
    orm_columns = {
        column.name: (str(column.type), column.nullable)
        for column in tables.transcript_revisions.columns
    }
    normalised = {
        name: (re.sub(r"\(.*\)", "", kind), nullable)
        for name, (kind, nullable) in orm_columns.items()
    }
    migrated = {
        name: (re.sub(r"\(.*\)", "", kind), nullable)
        for name, (kind, nullable) in migration_columns.items()
    }
    # ``primary_key`` makes the id non-nullable in the ORM; the migration states it separately.
    migrated["transcript_revision_id"] = (migrated["transcript_revision_id"][0], False)
    assert migrated == normalised
    assert str(tables.run_inputs.c.voice_asset_ref.type) == "VARCHAR(256)"
    for name in ("voice_asset_ref", "voice_asset_version", "voice_duration_ms"):
        assert tables.run_inputs.c[name].nullable is True


def test_the_text_never_uses_a_relative_downgrade_or_a_label() -> None:
    text = _MIGRATION.read_text(encoding="utf-8")
    assert "alembic downgrade 20261119_frc08_lifecycle_scope" in text
    assert "downgrade -1" not in text.replace("never ``-1``", "")
    assert "branch_labels = None" in text
    assert "GRANT" not in text.replace("No GRANT statement", "")


@pytest.mark.parametrize("name", ["ck_story_run_input_typed_idea"])
def test_the_replaced_constraint_is_dropped_before_the_new_ones_are_created(name: str) -> None:
    module = _load()
    calls = _run(module, "upgrade")
    order = [(n, a[0]) for n, a, _k in calls if n in {"drop_constraint", "create_check_constraint"}]
    assert order.index(("drop_constraint", name)) < order.index(
        ("create_check_constraint", "ck_story_run_input_idea")
    )
