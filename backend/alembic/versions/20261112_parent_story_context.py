"""Add Parent Story context and optional LessonVersion snapshots to Story inputs."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20261112_parent_story_context"
down_revision = "20261104_story_revisions"
branch_labels = None
depends_on = None


_ASSET_COLUMNS = (
    ("original_asset_ref", sa.String(256)),
    ("original_asset_version", sa.Integer()),
    ("original_sha256", sa.String(64)),
    ("original_media_type", sa.String(32)),
    ("original_size_bytes", sa.BigInteger()),
    ("derived_asset_ref", sa.String(256)),
    ("derived_asset_version", sa.Integer()),
    ("derived_sha256", sa.String(64)),
    ("derived_media_type", sa.String(32)),
    ("derived_size_bytes", sa.BigInteger()),
)


def upgrade() -> None:
    # This revision cannot reconstruct immutable Parent context for pre-existing
    # StoryRuns. Fail closed instead of leaving legacy active runs without a
    # current input pointer that the new API can serve.
    op.execute(
        sa.text(
            """
            DO $i2_story_baseline$
            BEGIN
                IF EXISTS (SELECT 1 FROM story.runs LIMIT 1) THEN
                    RAISE EXCEPTION
                        'I2 requires an empty story.runs baseline; review legacy StoryRuns first';
                END IF;
            END;
            $i2_story_baseline$;
            """
        )
    )
    op.add_column(
        "runs", sa.Column("current_input_revision", sa.Integer(), nullable=True), schema="story"
    )
    op.create_check_constraint(
        "ck_story_run_current_input_revision",
        "runs",
        "current_input_revision IS NULL OR current_input_revision > 0",
        schema="story",
    )
    op.drop_constraint("ck_story_run_state", "runs", schema="story", type_="check")
    op.create_check_constraint(
        "ck_story_run_state",
        "runs",
        "run_state IN ('INPUT_PROCESSING','SUBJECT_REVIEW','PREPARATION_REVIEW',"
        "'SCRIPT_GENERATING','SCRIPT_GENERATION_UNKNOWN','SCRIPT_REVIEW',"
        "'VIDEO_ADMISSION_PENDING','DELETE_PENDING','FAILED','COMPLETED')",
        schema="story",
    )

    for column_name, column_type in _ASSET_COLUMNS:
        op.alter_column(
            "run_inputs",
            column_name,
            schema="story",
            existing_type=column_type,
            existing_nullable=False,
            nullable=True,
        )

    op.drop_constraint("ck_story_run_input_versions", "run_inputs", schema="story", type_="check")
    op.drop_constraint("ck_story_run_input_hashes", "run_inputs", schema="story", type_="check")
    op.drop_constraint("ck_story_run_input_sizes", "run_inputs", schema="story", type_="check")
    op.create_check_constraint(
        "ck_story_run_input_versions",
        "run_inputs",
        "input_revision > 0 AND ((original_asset_ref IS NULL AND original_asset_version IS NULL "
        "AND original_sha256 IS NULL AND original_media_type IS NULL "
        "AND original_size_bytes IS NULL "
        "AND derived_asset_ref IS NULL AND derived_asset_version IS NULL "
        "AND derived_sha256 IS NULL AND derived_media_type IS NULL "
        "AND derived_size_bytes IS NULL) OR "
        "(original_asset_ref IS NOT NULL AND original_asset_version IS NOT NULL "
        "AND original_asset_version > 0 AND original_sha256 IS NOT NULL "
        "AND original_media_type IS NOT NULL AND original_size_bytes IS NOT NULL "
        "AND original_size_bytes > 0 AND derived_asset_ref IS NOT NULL "
        "AND derived_asset_version IS NOT NULL AND derived_asset_version > 0 "
        "AND derived_sha256 IS NOT NULL AND derived_media_type IS NOT NULL "
        "AND derived_size_bytes IS NOT NULL AND derived_size_bytes > 0))",
        schema="story",
    )
    op.create_check_constraint(
        "ck_story_run_input_hashes",
        "run_inputs",
        "(original_sha256 IS NULL AND derived_sha256 IS NULL) OR "
        "(original_sha256 IS NOT NULL AND derived_sha256 IS NOT NULL "
        "AND original_sha256 ~ '^[0-9a-f]{64}$' AND derived_sha256 ~ '^[0-9a-f]{64}$')",
        schema="story",
    )
    op.create_check_constraint(
        "ck_story_run_input_sizes",
        "run_inputs",
        "(original_size_bytes IS NULL AND derived_size_bytes IS NULL) OR "
        "(original_size_bytes IS NOT NULL AND derived_size_bytes IS NOT NULL "
        "AND original_size_bytes BETWEEN 1 AND 20971520 "
        "AND derived_size_bytes BETWEEN 1 AND 5000000)",
        schema="story",
    )

    op.add_column(
        "run_inputs",
        sa.Column("source_profile_revision_ref", sa.String(36), nullable=True),
        schema="story",
    )
    op.add_column(
        "run_inputs", sa.Column("typed_idea", sa.String(500), nullable=True), schema="story"
    )
    op.add_column(
        "run_inputs", sa.Column("idea_source", sa.String(16), nullable=True), schema="story"
    )
    op.add_column(
        "run_inputs", sa.Column("context_revision", sa.Integer(), nullable=True), schema="story"
    )
    op.add_column(
        "run_inputs",
        sa.Column("context_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        schema="story",
    )
    op.add_column(
        "run_inputs",
        sa.Column("context_snapshot_sha256", sa.String(64), nullable=True),
        schema="story",
    )
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
    op.add_column(
        "run_inputs",
        sa.Column("context_confirmed_by", sa.String(256), nullable=True),
        schema="story",
    )
    op.add_column(
        "run_inputs",
        sa.Column("context_confirmed_at", sa.DateTime(timezone=True), nullable=True),
        schema="story",
    )

    op.create_check_constraint(
        "ck_story_run_input_typed_idea",
        "run_inputs",
        "(typed_idea IS NULL AND idea_source IS NULL) OR "
        "(typed_idea IS NOT NULL AND length(typed_idea) BETWEEN 1 AND 500 "
        "AND idea_source = 'TEXT')",
        schema="story",
    )
    op.create_check_constraint(
        "ck_story_run_input_parent_context",
        "run_inputs",
        "(context_snapshot IS NULL AND context_snapshot_sha256 IS NULL "
        "AND context_revision IS NULL AND source_profile_revision_ref IS NULL "
        "AND context_confirmed_by IS NULL "
        "AND context_confirmed_at IS NULL) OR "
        "(context_snapshot IS NOT NULL AND context_snapshot_sha256 IS NOT NULL "
        "AND context_snapshot_sha256 ~ '^[0-9a-f]{64}$' "
        "AND context_revision IS NOT NULL AND context_revision > 0 "
        "AND source_profile_revision_ref IS NOT NULL "
        "AND ((context_confirmed_by IS NULL AND context_confirmed_at IS NULL) OR "
        "(context_confirmed_by IS NOT NULL AND context_confirmed_at IS NOT NULL)) "
        "AND octet_length(context_snapshot::text) <= 32768)",
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

    op.drop_constraint(
        "ck_story_receipt_operation", "command_receipts", schema="story", type_="check"
    )
    op.create_check_constraint(
        "ck_story_receipt_operation",
        "command_receipts",
        "operation IN ('CREATE_RUN','ATTACH_ASSET','CONFIRM_SUBJECT','CONFIRM_CONTEXT',"
        "'CANCEL_RUN','GENERATE_STORY_REVISION','CONFIRM_STORY_REVISION')",
        schema="story",
    )


def downgrade() -> None:
    raise RuntimeError(
        "No automatic downgrade: Parent context and optional LessonVersion snapshots may be "
        "in use. Preserve/export Story data and use a separately reviewed forward repair."
    )
