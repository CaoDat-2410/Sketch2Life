"""Persist Parent activity suggestions and adult selections per StoryRun."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261122_parent_activity_selection"
down_revision = "20261113_parent_consent_policy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "activity_suggestion_sets",
        sa.Column("suggestion_set_id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), nullable=False),
        sa.Column("owner_scope_kind", sa.String(32), nullable=False),
        sa.Column("owner_scope_ref", sa.String(256), nullable=False),
        sa.Column("input_revision", sa.Integer(), nullable=False),
        sa.Column("understanding_revision", sa.Integer(), nullable=False),
        sa.Column("selection_mode", sa.String(32), nullable=False),
        sa.Column("candidates_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("candidates_sha256", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"], ["story.runs.run_id"], ondelete="CASCADE",
            name="fk_story_activity_suggestion_run",
        ),
        sa.UniqueConstraint("run_id", "suggestion_set_id", name="uq_story_activity_suggestion_owner"),
        sa.CheckConstraint("owner_scope_kind = 'PARENT_ACCOUNT'", name="ck_story_activity_suggestion_owner_kind"),
        sa.CheckConstraint("input_revision > 0 AND understanding_revision > 0", name="ck_story_activity_suggestion_revisions"),
        sa.CheckConstraint("selection_mode IN ('CATALOG_SELECTION','AI_GENERATED_FALLBACK')", name="ck_story_activity_suggestion_mode"),
        sa.CheckConstraint("length(candidates_sha256) = 64", name="ck_story_activity_suggestion_hash"),
        sa.CheckConstraint(
            "jsonb_typeof(candidates_snapshot) = 'array' AND octet_length(candidates_snapshot::text) <= 262144",
            name="ck_story_activity_suggestion_snapshot",
        ),
        schema="story",
    )
    op.create_index(
        "ix_story_activity_suggestion_current",
        "activity_suggestion_sets",
        ["run_id", "input_revision", "understanding_revision", "created_at"],
        schema="story",
    )
    op.create_table(
        "activity_selections",
        sa.Column("selection_id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), nullable=False),
        sa.Column("suggestion_set_id", sa.String(36), nullable=False),
        sa.Column("owner_scope_kind", sa.String(32), nullable=False),
        sa.Column("owner_scope_ref", sa.String(256), nullable=False),
        sa.Column("input_revision", sa.Integer(), nullable=False),
        sa.Column("understanding_revision", sa.Integer(), nullable=False),
        sa.Column("activity_selection_id", sa.String(36), nullable=False),
        sa.Column("selected_activity_sha256", sa.String(64), nullable=False),
        sa.Column("selected_activity_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("state", sa.String(16), server_default=sa.text("'ACTIVE'"), nullable=False),
        sa.Column("selected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id", "suggestion_set_id"],
            ["story.activity_suggestion_sets.run_id", "story.activity_suggestion_sets.suggestion_set_id"],
            ondelete="RESTRICT",
            name="fk_story_activity_selection_suggestion_set",
        ),
        sa.CheckConstraint("owner_scope_kind = 'PARENT_ACCOUNT'", name="ck_story_activity_selection_owner_kind"),
        sa.CheckConstraint("input_revision > 0 AND understanding_revision > 0", name="ck_story_activity_selection_revisions"),
        sa.CheckConstraint("length(selected_activity_sha256) = 64", name="ck_story_activity_selection_hash"),
        sa.CheckConstraint("state IN ('ACTIVE','SUPERSEDED')", name="ck_story_activity_selection_state"),
        sa.CheckConstraint(
            "jsonb_typeof(selected_activity_snapshot) = 'object' AND octet_length(selected_activity_snapshot::text) <= 65536",
            name="ck_story_activity_selection_snapshot",
        ),
        schema="story",
    )
    op.create_index(
        "uq_story_activity_selection_one_active",
        "activity_selections",
        ["run_id"],
        unique=True,
        schema="story",
        postgresql_where=sa.text("state = 'ACTIVE'"),
    )
    op.create_index(
        "ix_story_activity_selection_current",
        "activity_selections",
        ["run_id", "input_revision", "understanding_revision", "selected_at"],
        schema="story",
    )


def downgrade() -> None:
    op.drop_index("ix_story_activity_selection_current", table_name="activity_selections", schema="story")
    op.drop_index("uq_story_activity_selection_one_active", table_name="activity_selections", schema="story")
    op.drop_table("activity_selections", schema="story")
    op.drop_index("ix_story_activity_suggestion_current", table_name="activity_suggestion_sets", schema="story")
    op.drop_table("activity_suggestion_sets", schema="story")
