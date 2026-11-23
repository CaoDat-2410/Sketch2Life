"""Persist Parent activity suggestion snapshots and adult selections."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261114_parent_activity_selection"
down_revision = "20261113_svg_catalog_review"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("ck_story_receipt_operation", "command_receipts", schema="story", type_="check")
    op.create_check_constraint(
        "ck_story_receipt_operation",
        "command_receipts",
        "operation IN ('CREATE_RUN','ATTACH_ASSET','CONFIRM_SUBJECT','CONFIRM_CONTEXT',"
        "'CANCEL_RUN','GENERATE_STORY_REVISION','CONFIRM_STORY_REVISION',"
        "'GENERATE_ACTIVITY_SET','SELECT_ACTIVITY')",
        schema="story",
    )

    op.create_table(
        "parent_activity_suggestion_sets",
        sa.Column("suggestion_set_id", sa.String(36), nullable=False),
        sa.Column("run_id", sa.String(36), nullable=False),
        sa.Column("set_revision", sa.Integer(), nullable=False),
        sa.Column("understanding_revision", sa.Integer(), nullable=False),
        sa.Column("input_revision", sa.Integer(), nullable=False),
        sa.Column("context_revision", sa.Integer(), nullable=False),
        sa.Column("selection_mode", sa.String(32), nullable=False),
        sa.Column("catalog_candidate_count", sa.Integer(), nullable=False),
        sa.Column("activities_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("activities_snapshot_sha256", sa.String(64), nullable=False),
        sa.Column("provider_call_id", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["story.runs.run_id"], ondelete="CASCADE", name="fk_story_parent_activity_set_run"),
        sa.PrimaryKeyConstraint("suggestion_set_id", name="pk_story_parent_activity_suggestion_sets"),
        sa.UniqueConstraint("run_id", "set_revision", name="uq_story_parent_activity_set_revision"),
        sa.UniqueConstraint("run_id", "suggestion_set_id", name="uq_story_parent_activity_set_owner"),
        sa.CheckConstraint("set_revision > 0 AND understanding_revision > 0", name="ck_story_parent_activity_set_revisions"),
        sa.CheckConstraint("input_revision > 0 AND context_revision > 0", name="ck_story_parent_activity_set_inputs"),
        sa.CheckConstraint("selection_mode IN ('CATALOG_SELECTION','AI_GENERATED_FALLBACK')", name="ck_story_parent_activity_set_mode"),
        sa.CheckConstraint("catalog_candidate_count BETWEEN 0 AND 500", name="ck_story_parent_activity_set_candidate_count"),
        sa.CheckConstraint("length(activities_snapshot_sha256) = 64", name="ck_story_parent_activity_set_hash"),
        sa.CheckConstraint("jsonb_typeof(activities_snapshot) = 'array' AND octet_length(activities_snapshot::text) <= 262144", name="ck_story_parent_activity_set_snapshot"),
        schema="story",
    )
    op.create_index(
        "ix_story_parent_activity_set_current",
        "parent_activity_suggestion_sets",
        ["run_id", "understanding_revision", "set_revision"],
        schema="story",
    )

    op.create_table(
        "parent_activity_selections",
        sa.Column("activity_selection_id", sa.String(36), nullable=False),
        sa.Column("run_id", sa.String(36), nullable=False),
        sa.Column("selection_revision", sa.Integer(), nullable=False),
        sa.Column("suggestion_set_id", sa.String(36), nullable=False),
        sa.Column("understanding_revision", sa.Integer(), nullable=False),
        sa.Column("activity_index", sa.Integer(), nullable=False),
        sa.Column("activity_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("activity_snapshot_sha256", sa.String(64), nullable=False),
        sa.Column("actor_scope_ref", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id", "suggestion_set_id"],
            ["story.parent_activity_suggestion_sets.run_id", "story.parent_activity_suggestion_sets.suggestion_set_id"],
            ondelete="CASCADE",
            name="fk_story_parent_activity_selection_set_owner",
        ),
        sa.PrimaryKeyConstraint("activity_selection_id", name="pk_story_parent_activity_selections"),
        sa.UniqueConstraint("run_id", "selection_revision", name="uq_story_parent_activity_selection_revision"),
        sa.CheckConstraint("selection_revision > 0 AND understanding_revision > 0", name="ck_story_parent_activity_selection_revisions"),
        sa.CheckConstraint("activity_index BETWEEN 0 AND 23", name="ck_story_parent_activity_selection_index"),
        sa.CheckConstraint("length(activity_snapshot_sha256) = 64", name="ck_story_parent_activity_selection_hash"),
        sa.CheckConstraint("jsonb_typeof(activity_snapshot) = 'object' AND octet_length(activity_snapshot::text) <= 32768", name="ck_story_parent_activity_selection_snapshot"),
        schema="story",
    )
    op.create_index(
        "ix_story_parent_activity_selection_current",
        "parent_activity_selections",
        ["run_id", "understanding_revision", "selection_revision"],
        schema="story",
    )
    op.add_column(
        "story_revisions",
        sa.Column("activity_selection_id", sa.String(36), nullable=True),
        schema="story",
    )
    op.create_foreign_key(
        "fk_story_revision_activity_selection",
        "story_revisions",
        "parent_activity_selections",
        ["activity_selection_id"],
        ["activity_selection_id"],
        source_schema="story",
        referent_schema="story",
        ondelete="NO ACTION",
    )
    op.create_index(
        "ix_story_revision_activity_selection",
        "story_revisions",
        ["activity_selection_id"],
        schema="story",
    )


def downgrade() -> None:
    raise RuntimeError(
        "No automatic downgrade: Parent activity snapshots and selections may be in use. "
        "Preserve/export Story data and use a separately reviewed forward repair."
    )
