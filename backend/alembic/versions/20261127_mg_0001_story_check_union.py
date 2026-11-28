"""Merge repair: give every database the same Story run-state and idea checks.

Revisions that a database already applied before the dev merge do not run again, so such a
database kept checks without the values the dev branch added (two run states and the TRANSCRIPT idea
source). This revision rewrites both checks with the full union used by either branch.
"""

from __future__ import annotations

from alembic import op

revision = "20261127_mg_0001"
down_revision = "20261126_as_0003"
branch_labels = None
depends_on = None

SCHEMA = "story"

RUN_STATES = (
    "DRAFT",
    "INPUT_PROCESSING",
    "INPUT_REVIEW",
    "SUBJECT_REVIEW",
    "PREPARATION_REVIEW",
    "STORY_GENERATING",
    "SCRIPT_REVIEW",
    "VIDEO_ADMISSION_PENDING",
    "VIDEO_QUEUED",
    "VIDEO_GENERATING",
    "VIDEO_SAFETY_VALIDATING",
    "VIDEO_READY",
    "SAFETY_BLOCKED",
    "COMPLETED",
    "FAILED",
    "ABANDONED",
    "DELETE_PENDING",
    "DELETED",
    "SCRIPT_GENERATING",
    "SCRIPT_GENERATION_UNKNOWN",
)


_TEXT = "typed_idea IS NOT NULL AND length(typed_idea) BETWEEN 1 AND 500"
IDEA_CHECK = (
    "(typed_idea IS NULL AND voice_asset_ref IS NULL AND idea_source IS NULL) OR "
    f"({_TEXT} AND voice_asset_ref IS NULL AND idea_source = 'TEXT') OR "
    f"({_TEXT} AND voice_asset_ref IS NULL AND idea_source = 'TRANSCRIPT') OR "
    "(typed_idea IS NULL AND voice_asset_ref IS NOT NULL AND idea_source = 'VOICE') OR "
    f"({_TEXT} AND voice_asset_ref IS NOT NULL AND idea_source = 'TEXT_AND_VOICE')"
)


def _replace_check(table: str, name: str, column: str, values: tuple[str, ...]) -> None:
    allowed = ",".join(f"'{value}'" for value in values)
    op.execute(f"ALTER TABLE {SCHEMA}.{table} DROP CONSTRAINT IF EXISTS {name}")
    op.create_check_constraint(name, table, f"{column} IN ({allowed})", schema=SCHEMA)


def upgrade() -> None:
    _replace_check("runs", "ck_story_run_state", "run_state", RUN_STATES)


    op.execute(f"ALTER TABLE {SCHEMA}.run_inputs DROP CONSTRAINT IF EXISTS ck_story_run_input_idea")
    op.create_check_constraint("ck_story_run_input_idea", "run_inputs", IDEA_CHECK, schema=SCHEMA)


def downgrade() -> None:
    # The wider checks stay: narrowing it could reject existing rows.
    pass
