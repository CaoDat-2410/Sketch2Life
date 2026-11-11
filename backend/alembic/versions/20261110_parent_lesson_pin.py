"""Persist an immutable Parent lesson-version snapshot on StoryRun input."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261110_parent_lesson_pin"
down_revision = "20261110_parent_profile_story_context"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "run_inputs",
        sa.Column("lesson_pin_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        schema="story",
    )
    op.add_column(
        "run_inputs",
        sa.Column("lesson_pin_snapshot_sha256", sa.String(64), nullable=True),
        schema="story",
    )
    op.create_check_constraint(
        "ck_story_run_input_lesson_pin_snapshot",
        "run_inputs",
        "(lesson_pin_snapshot IS NULL AND lesson_pin_snapshot_sha256 IS NULL) OR "
        "(lesson_pin_snapshot IS NOT NULL AND lesson_pin_snapshot_sha256 IS NOT NULL "
        "AND lesson_pin_snapshot_sha256 ~ '^[0-9a-f]{64}$' "
        "AND octet_length(lesson_pin_snapshot::text) <= 1048576)",
        schema="story",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_story_run_input_lesson_pin_snapshot", "run_inputs", schema="story", type_="check"
    )
    op.drop_column("run_inputs", "lesson_pin_snapshot_sha256", schema="story")
    op.drop_column("run_inputs", "lesson_pin_snapshot", schema="story")
