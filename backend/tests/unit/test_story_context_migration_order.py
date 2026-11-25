"""Fresh-database order of the two migrations that both add Story run context columns."""

from __future__ import annotations

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

_BACKEND = Path(__file__).resolve().parents[2]
_VERSIONS = _BACKEND / "alembic" / "versions"


def _script() -> ScriptDirectory:
    config = Config(str(_BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(_BACKEND / "alembic"))
    return ScriptDirectory.from_config(config)


def test_parent_profiles_runs_after_the_story_context_revision() -> None:
    script = _script()
    ancestors = {r.revision for r in script.iterate_revisions("20261110_parent_profiles", "base")}
    assert "20261112_parent_story_context" in ancestors


def test_overlapping_story_ddl_is_guarded_for_a_fresh_database() -> None:
    profiles = (_VERSIONS / "20261110_parent_profile_story_context.py").read_text(encoding="utf-8")
    pin = (_VERSIONS / "20261110_parent_lesson_pin.py").read_text(encoding="utf-8")
    assert "_story_context_already_applied()" in profiles
    assert "information_schema.columns" in profiles
    assert "lesson_pin_snapshot" in pin and "information_schema.columns" in pin


def test_legacy_parent_profiles_runs_after_the_m2_parent_foundation_and_skips_its_tables() -> None:
    ancestors = {r.revision for r in _script().iterate_revisions("20261110_parent_profiles", "base")}
    assert "20261109_m2_parent_profiles" in ancestors
    source = (_VERSIONS / "20261110_parent_profile_story_context.py").read_text(encoding="utf-8")
    for helper in ("_create_table(", "_create_index(", "_create_foreign_key("):
        assert helper in source
