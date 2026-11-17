"""Add SRS-aligned story revisions, ordered scenes, and script confirmation records."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20261104_story_revisions"
down_revision = "20261103_story_upload_compat"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "runs",
        sa.Column("child_age_months", sa.Integer(), nullable=True),
        schema="story",
    )
    op.create_check_constraint(
        "ck_story_run_child_age_months",
        "runs",
        "child_age_months IS NULL OR child_age_months BETWEEN 36 AND 120",
        schema="story",
    )
    op.drop_constraint("ck_story_run_state", "runs", schema="story", type_="check")
    op.create_check_constraint(
        "ck_story_run_state",
        "runs",
        "run_state IN ('INPUT_PROCESSING','SUBJECT_REVIEW','PREPARATION_REVIEW',"
        "'SCRIPT_GENERATING','SCRIPT_GENERATION_UNKNOWN','SCRIPT_REVIEW',"
        "'VIDEO_ADMISSION_PENDING','DELETE_PENDING','FAILED')",
        schema="story",
    )
    op.drop_constraint(
        "ck_story_receipt_operation", "command_receipts", schema="story", type_="check"
    )
    op.create_check_constraint(
        "ck_story_receipt_operation",
        "command_receipts",
        "operation IN ('CREATE_RUN','ATTACH_ASSET','CONFIRM_SUBJECT','CANCEL_RUN',"
        "'GENERATE_STORY_REVISION','CONFIRM_STORY_REVISION')",
        schema="story",
    )

    op.create_table(
        "story_revisions",
        sa.Column("story_revision_id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), nullable=False),
        sa.Column("revision_no", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("source_asset_sha256", sa.String(64), nullable=False),
        sa.Column("understanding_revision", sa.Integer(), nullable=False),
        sa.Column("context_revision", sa.Integer(), nullable=False),
        sa.Column("story_sha256", sa.String(64)),
        sa.Column("language", sa.String(8)),
        sa.Column("title", sa.String(120)),
        sa.Column("duration_ms", sa.Integer()),
        sa.Column("story_content", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("schema_version", sa.String(64), nullable=False),
        sa.Column("prompt_version", sa.String(64), nullable=False),
        sa.Column("model_id", sa.String(256), nullable=False),
        sa.Column("model_revision", sa.String(128), nullable=False),
        sa.Column("request_sha256", sa.String(64), nullable=False),
        sa.Column("provider_call_id", sa.String(128)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["story.runs.run_id"], ondelete="CASCADE", name="fk_story_revision_run"),
        sa.UniqueConstraint("run_id", "revision_no", name="uq_story_revision_run_no"),
        sa.UniqueConstraint("run_id", "story_revision_id", name="uq_story_revision_run_owner"),
        sa.CheckConstraint("revision_no BETWEEN 1 AND 4", name="ck_story_revision_no"),
        sa.CheckConstraint(
            "status IN ('GENERATING','DRAFT','CONFIRMED','SUPERSEDED','FAILED','AWAITING_RECONCILIATION')",
            name="ck_story_revision_status",
        ),
        sa.CheckConstraint("understanding_revision > 0 AND context_revision > 0", name="ck_story_revision_inputs"),
        sa.CheckConstraint(
            "length(source_asset_sha256) = 64 AND length(request_sha256) = 64",
            name="ck_story_revision_hashes",
        ),
        sa.CheckConstraint(
            "story_sha256 IS NULL OR length(story_sha256) = 64", name="ck_story_revision_content_hash"
        ),
        sa.CheckConstraint("duration_ms IS NULL OR duration_ms BETWEEN 30000 AND 90000", name="ck_story_revision_duration"),
        sa.CheckConstraint(
            "(status IN ('GENERATING','FAILED','AWAITING_RECONCILIATION') AND story_sha256 IS NULL) OR "
            "(status IN ('DRAFT','CONFIRMED','SUPERSEDED') AND story_sha256 IS NOT NULL AND "
            "language = 'vi' AND title IS NOT NULL AND duration_ms IS NOT NULL AND story_content IS NOT NULL)",
            name="ck_story_revision_result_shape",
        ),
        schema="story",
    )
    op.create_index("ix_story_revision_run_status", "story_revisions", ["run_id", "status"], schema="story")

    op.create_table(
        "story_scenes",
        sa.Column("scene_id", sa.String(36), primary_key=True),
        sa.Column("story_revision_id", sa.String(36), nullable=False),
        sa.Column("scene_index", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("action", sa.String(500), nullable=False),
        sa.Column("visual_prompt", sa.String(900), nullable=False),
        sa.Column("narration", sa.String(500), nullable=False),
        sa.Column("start_ms", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("character_anchors", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["story_revision_id"], ["story.story_revisions.story_revision_id"],
            ondelete="CASCADE", name="fk_story_scene_revision",
        ),
        sa.UniqueConstraint("story_revision_id", "scene_index", name="uq_story_scene_revision_index"),
        sa.CheckConstraint("scene_index BETWEEN 1 AND 15", name="ck_story_scene_index"),
        sa.CheckConstraint("start_ms >= 0 AND duration_ms BETWEEN 1000 AND 20000", name="ck_story_scene_timing"),
        schema="story",
    )
    op.create_index("ix_story_scene_revision_order", "story_scenes", ["story_revision_id", "scene_index"], schema="story")

    op.create_table(
        "story_revision_reviews",
        sa.Column("review_id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), nullable=False),
        sa.Column("story_revision_id", sa.String(36), nullable=False),
        sa.Column("command_receipt_id", sa.String(36), nullable=False),
        sa.Column("actor_scope_kind", sa.String(32), nullable=False),
        sa.Column("actor_scope_ref", sa.String(128), nullable=False),
        sa.Column("decision", sa.String(24), nullable=False),
        sa.Column("target_story_sha256", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id", "story_revision_id"],
            ["story.story_revisions.run_id", "story.story_revisions.story_revision_id"],
            ondelete="CASCADE", name="fk_story_revision_review_owner",
        ),
        sa.ForeignKeyConstraint(
            ["command_receipt_id"], ["story.command_receipts.receipt_id"],
            ondelete="RESTRICT", name="fk_story_revision_review_receipt",
        ),
        sa.UniqueConstraint("command_receipt_id", name="uq_story_revision_review_receipt"),
        sa.UniqueConstraint("story_revision_id", name="uq_story_revision_review_once"),
        sa.CheckConstraint("decision = 'CONFIRM'", name="ck_story_revision_review_decision"),
        sa.CheckConstraint("length(target_story_sha256) = 64", name="ck_story_revision_review_hash"),
        schema="story",
    )


def downgrade() -> None:
    op.drop_table("story_revision_reviews", schema="story")
    op.drop_index("ix_story_scene_revision_order", table_name="story_scenes", schema="story")
    op.drop_table("story_scenes", schema="story")
    op.drop_index("ix_story_revision_run_status", table_name="story_revisions", schema="story")
    op.drop_table("story_revisions", schema="story")
    op.drop_constraint("ck_story_receipt_operation", "command_receipts", schema="story", type_="check")
    op.create_check_constraint(
        "ck_story_receipt_operation",
        "command_receipts",
        "operation IN ('CREATE_RUN','ATTACH_ASSET','CONFIRM_SUBJECT','CANCEL_RUN')",
        schema="story",
    )
    op.drop_constraint("ck_story_run_state", "runs", schema="story", type_="check")
    op.create_check_constraint(
        "ck_story_run_state",
        "runs",
        "run_state IN ('INPUT_PROCESSING','SUBJECT_REVIEW','PREPARATION_REVIEW','DELETE_PENDING','FAILED')",
        schema="story",
    )
    op.drop_constraint("ck_story_run_child_age_months", "runs", schema="story", type_="check")
    op.drop_column("runs", "child_age_months", schema="story")
