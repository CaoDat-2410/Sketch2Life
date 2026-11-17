"""Persist BE1 room-code, SRS stage, draft and outcome contracts."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20261024_0005"
down_revision = "20261014_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "be1_session_room_codes",
        sa.Column("session_id", sa.String(128), primary_key=True),
        sa.Column("organization_id", sa.String(128), nullable=False),
        sa.Column("room_code_hmac", sa.String(64), nullable=False),
        sa.Column("key_version", sa.String(32), nullable=False),
        sa.Column(
            "rotated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("room_code_hmac", name="uq_be1_room_code_hmac"),
    )
    op.create_table(
        "be1_room_code_rate_limits",
        sa.Column("source_hmac", sa.String(64), primary_key=True),
        sa.Column("attempts", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    )
    op.create_table(
        "be1_session_learning_stages",
        sa.Column("session_id", sa.String(128), primary_key=True),
        sa.Column("organization_id", sa.String(128), nullable=False),
        sa.Column("stage", sa.String(32), nullable=False),
        sa.Column("stage_revision", sa.Integer(), nullable=False),
        sa.Column(
            "entered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("last_command_id", sa.String(128), nullable=True),
        sa.CheckConstraint(
            "stage IN ('preparation','join','explore_draw','assistance','sharing','knowledge',"
            "'off_screen','reflection','completion')",
            name="ck_be1_learning_stage",
        ),
        sa.CheckConstraint("stage_revision > 0", name="ck_be1_learning_stage_revision"),
    )
    op.create_table(
        "be1_session_learning_stage_events",
        sa.Column("event_id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(128), nullable=False),
        sa.Column("session_id", sa.String(128), nullable=False),
        sa.Column("from_stage", sa.String(32), nullable=False),
        sa.Column("to_stage", sa.String(32), nullable=False),
        sa.Column("stage_revision", sa.Integer(), nullable=False),
        sa.Column("command_id", sa.String(128), nullable=False),
        sa.Column("actor", sa.String(256), nullable=False),
        sa.Column("disposition", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint(
            "organization_id", "session_id", "stage_revision", name="uq_be1_stage_event_revision"
        ),
        sa.UniqueConstraint(
            "organization_id", "session_id", "command_id", name="uq_be1_stage_event_command"
        ),
    )
    op.create_table(
        "be1_session_command_receipts",
        sa.Column("organization_id", sa.String(128), primary_key=True),
        sa.Column("session_id", sa.String(128), primary_key=True),
        sa.Column("command_type", sa.String(48), primary_key=True),
        sa.Column("idempotency_key", sa.String(128), primary_key=True),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("response_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "be1_group_drafts",
        sa.Column("draft_id", sa.String(36), primary_key=True),
        sa.Column("organization_id", sa.String(128), nullable=False),
        sa.Column("session_id", sa.String(128), nullable=False),
        sa.Column("group_id", sa.String(128), nullable=False),
        sa.Column("stage_revision", sa.Integer(), nullable=False),
        sa.Column("disposition", sa.String(24), nullable=False),
        sa.Column("durable_canvas_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_by", sa.String(256), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint(
            "organization_id",
            "session_id",
            "group_id",
            "stage_revision",
            name="uq_be1_group_draft_stage",
        ),
        sa.CheckConstraint("disposition = 'save_draft'", name="ck_be1_group_draft_disposition"),
    )
    op.create_table(
        "be1_session_outcomes",
        sa.Column("session_id", sa.String(128), primary_key=True),
        sa.Column("organization_id", sa.String(128), nullable=False),
        sa.Column("outcome", sa.String(24), nullable=False),
        sa.Column("reason_category", sa.String(24), nullable=True),
        sa.Column("teacher_note", sa.String(240), nullable=True),
        sa.Column("outcome_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("stage_revision", sa.Integer(), nullable=False),
        sa.Column("command_id", sa.String(128), nullable=False),
        sa.Column("created_by", sa.String(256), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("outcome IN ('completed','ended_early')", name="ck_be1_session_outcome"),
        sa.CheckConstraint(
            "(outcome = 'completed' AND reason_category IS NULL) OR "
            "(outcome = 'ended_early' AND reason_category IS NOT NULL AND reason_category IN "
            "('time','safety','technical','other'))",
            name="ck_be1_session_outcome_reason",
        ),
    )


def downgrade() -> None:
    op.drop_table("be1_session_outcomes")
    op.drop_table("be1_group_drafts")
    op.drop_table("be1_session_command_receipts")
    op.drop_table("be1_session_learning_stage_events")
    op.drop_table("be1_session_learning_stages")
    op.drop_table("be1_room_code_rate_limits")
    op.drop_table("be1_session_room_codes")
