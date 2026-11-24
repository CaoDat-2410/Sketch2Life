"""Persist idempotent Parent StoryRun cancel/delete lifecycle requests."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20261111_parent_run_lifecycle"
down_revision = "20261110_parent_lesson_pin"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "run_lifecycle_requests",
        sa.Column("lifecycle_request_id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), nullable=False),
        sa.Column("actor_scope_kind", sa.String(32), nullable=False),
        sa.Column("actor_scope_ref", sa.String(128), nullable=False),
        sa.Column("operation", sa.String(24), nullable=False),
        sa.Column("idempotency_key_sha256", sa.String(64), nullable=False),
        sa.Column("request_sha256", sa.String(64), nullable=False),
        sa.Column("state", sa.String(24), nullable=False, server_default="REQUESTED"),
        sa.Column("purge_state", sa.String(24), nullable=False, server_default="PENDING"),
        sa.Column("job_cancel_state", sa.String(24), nullable=False, server_default="NOT_CONNECTED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ["run_id"], ["story.runs.run_id"], ondelete="RESTRICT",
            name="fk_story_run_lifecycle_run",
        ),
        sa.UniqueConstraint(
            "actor_scope_kind", "actor_scope_ref", "operation", "idempotency_key_sha256",
            name="uq_story_run_lifecycle_idempotency",
        ),
        sa.CheckConstraint("actor_scope_kind = 'PARENT_ACCOUNT'", name="ck_story_run_lifecycle_owner_kind"),
        sa.CheckConstraint("operation IN ('CANCEL','DELETE')", name="ck_story_run_lifecycle_operation"),
        sa.CheckConstraint("length(idempotency_key_sha256) = 64", name="ck_story_run_lifecycle_key_hash"),
        sa.CheckConstraint("length(request_sha256) = 64", name="ck_story_run_lifecycle_request_hash"),
        sa.CheckConstraint("state IN ('REQUESTED','RUNNING','COMPLETED','FAILED')", name="ck_story_run_lifecycle_state"),
        sa.CheckConstraint("purge_state IN ('PENDING','RUNNING','COMPLETED','FAILED')", name="ck_story_run_lifecycle_purge_state"),
        sa.CheckConstraint("job_cancel_state IN ('NOT_CONNECTED','REQUESTED','CONFIRMED','FAILED')", name="ck_story_run_lifecycle_job_cancel_state"),
        schema="story",
    )
    op.create_index(
        "ix_story_run_lifecycle_run_created",
        "run_lifecycle_requests",
        ["run_id", "created_at"],
        schema="story",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_story_run_lifecycle_run_created",
        table_name="run_lifecycle_requests",
        schema="story",
    )
    op.drop_table("run_lifecycle_requests", schema="story")
