from __future__ import annotations

import ast
from contextlib import suppress
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from sketch2life.infrastructure.lesson_occurrences.sketch_deck_tables import (
    SKETCH_DECK_REVISIONS,
    SKETCH_DECK_STEPS,
)

_BACKEND = Path(__file__).resolve().parents[2]
_MIGRATION = (
    _BACKEND / "alembic" / "versions" / "20261126_dc_0001_sketch_deck_revisions.py"
)


def _module_constants() -> dict[str, object]:
    values: dict[str, object] = {}
    for node in ast.parse(_MIGRATION.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                with suppress(TypeError, ValueError):
                    values[target.id] = ast.literal_eval(node.value)
    return values


def test_revision_is_one_new_child_of_current_lesson_library_head() -> None:
    constants = _module_constants()
    assert constants["revision"] == "20261126_dc_0001"
    assert constants["down_revision"] == "20261126_sh_0001"
    assert constants["branch_labels"] is None
    assert constants["depends_on"] is None

    scripts = ScriptDirectory.from_config(Config(str(_BACKEND / "alembic.ini")))
    revision = scripts.get_revision("20261126_dc_0001")
    assert revision is not None and revision.down_revision == "20261126_sh_0001"
    assert "20261126_dc_0001" in scripts.get_heads()
    assert len(list(scripts.walk_revisions())) == 83
    assert len(scripts.get_heads()) == 12


def test_table_mirrors_pin_revision_and_step_contracts() -> None:
    migration = _MIGRATION.read_text(encoding="utf-8")
    revision_columns = set(SKETCH_DECK_REVISIONS.c.keys())
    step_columns = set(SKETCH_DECK_STEPS.c.keys())

    assert SKETCH_DECK_REVISIONS.name == "sketch_deck_revisions"
    assert SKETCH_DECK_STEPS.name == "sketch_deck_steps"
    assert {
        "sketch_deck_revision_id",
        "occurrence_id",
        "plan_revision_id",
        "revision_no",
        "plan_content_hash",
        "review_confirmed",
        "topic",
        "drawing_steps",
        "subject_knowledge",
        "target_age_band",
        "deck_schema_version",
        "state",
        "model_profile_ref",
        "model_profile_version",
        "prompt_template_version",
        "config_hash",
        "compute_reservation_ref",
        "content_hash",
        "created_by",
        "created_at",
        "ready_at",
        "superseded_at",
    } == revision_columns
    assert {
        "sketch_deck_step_id",
        "sketch_deck_revision_id",
        "plan_activity_id",
        "instruction_group_key",
        "step_index",
        "step_kind",
        "subject_key",
        "short_title",
        "child_facing_prompt",
        "teacher_explanation",
        "bounded_layout_hints",
        "line_sketch_asset_ref",
        "line_sketch_asset_version",
        "source_job_ref",
        "state",
        "created_at",
    } == step_columns
    assert all(
        f"'{state}'" in migration
        for state in ("GENERATING", "READY", "FAILED", "STALE", "SUPERSEDED")
    )
    assert "BETWEEN 4 AND 8" in migration
    assert "review_confirmed IS TRUE" in migration
    assert "octet_length(drawing_steps::text) <= 32768" in migration
    assert "octet_length(subject_knowledge::text) <= 65536" in migration
    assert "COUNT(DISTINCT COALESCE(s.plan_activity_id, '')) <> 1" in migration
    assert "octet_length(bounded_layout_hints::text) <= 16384" in migration
    assert "SKETCH_DECK_REVISION_IMMUTABLE" in migration
    assert "SKETCH_DECK_STEP_IMMUTABLE" in migration
    assert "Refusing to downgrade Sketch Deck tables while deck data exists" in migration
    assert not {"child_id", "profile_id", "roster_id"} & revision_columns
    assert not {"child_id", "profile_id", "roster_id"} & step_columns


def test_downgrade_drops_trigger_tables_before_their_functions() -> None:
    migration = _MIGRATION.read_text(encoding="utf-8")
    downgrade = migration.split("def downgrade() -> None:", maxsplit=1)[1]
    operations = [
        'op.drop_table("sketch_deck_steps", schema=SCHEMA)',
        (
            'op.drop_index("uq_sketch_deck_one_ready", table_name="sketch_deck_revisions", '
            'schema=SCHEMA)'
        ),
        'op.drop_table("sketch_deck_revisions", schema=SCHEMA)',
        'op.execute("DROP FUNCTION lesson.protect_sketch_deck_step()")',
        'op.execute("DROP FUNCTION lesson.protect_sketch_deck_revision()")',
    ]
    positions = [downgrade.index(operation) for operation in operations]

    assert positions == sorted(positions)
