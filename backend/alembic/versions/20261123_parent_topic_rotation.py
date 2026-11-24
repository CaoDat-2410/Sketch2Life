"""Add privacy-minimal Parent topic and subject rotation state/receipts."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261123_parent_topic_rotation"
down_revision = "20261109_m2_parent_profiles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "topic_rotation_states",
        sa.Column("rotation_state_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", sa.String(length=36), nullable=False),
        sa.Column("catalog_revision", sa.String(length=80), nullable=False),
        sa.Column("rotation_kind", sa.String(length=12), nullable=False),
        sa.Column("scope_id", sa.String(length=64), nullable=False),
        sa.Column("ordered_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("cycle_number", sa.BigInteger(), server_default=sa.text("1"), nullable=False),
        sa.Column("cursor_position", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("rotation_state_id", name="pk_parent_topic_rotation_states"),
        sa.UniqueConstraint(
            "account_id", "catalog_revision", "rotation_kind", "scope_id",
            name="uq_parent_topic_rotation_state_scope",
        ),
        sa.CheckConstraint("rotation_kind IN ('TOPIC', 'SUBJECT')", name="ck_parent_topic_rotation_kind"),
        sa.CheckConstraint("cycle_number >= 1", name="ck_parent_topic_rotation_cycle"),
        sa.CheckConstraint("cursor_position >= 0", name="ck_parent_topic_rotation_cursor"),
        sa.CheckConstraint(
            "jsonb_typeof(ordered_ids) = 'array' AND octet_length(ordered_ids::text) <= 8192",
            name="ck_parent_topic_rotation_ordered_ids",
        ),
        schema="parent",
    )
    op.create_index(
        "ix_parent_topic_rotation_account_updated",
        "topic_rotation_states",
        ["account_id", "updated_at"],
        schema="parent",
    )
    op.create_table(
        "topic_rotation_receipts",
        sa.Column("rotation_receipt_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", sa.String(length=36), nullable=False),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("draft_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("catalog_revision", sa.String(length=80), nullable=False),
        sa.Column("rotation_kind", sa.String(length=12), nullable=False),
        sa.Column("scope_id", sa.String(length=64), nullable=False),
        sa.Column("request_fingerprint", postgresql.BYTEA(), nullable=False),
        sa.Column("cycle_number", sa.BigInteger(), nullable=False),
        sa.Column("set_id", sa.String(length=32), nullable=False),
        sa.Column("selected_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("rotation_receipt_id", name="pk_parent_topic_rotation_receipts"),
        sa.UniqueConstraint("account_id", "request_id", name="uq_parent_topic_rotation_receipt_request"),
        sa.CheckConstraint("octet_length(request_fingerprint) = 32", name="ck_parent_topic_rotation_fingerprint"),
        sa.CheckConstraint(
            "jsonb_typeof(selected_ids) = 'array' AND octet_length(selected_ids::text) <= 2048",
            name="ck_parent_topic_rotation_selected_ids",
        ),
        schema="parent",
    )
    op.create_index(
        "ix_parent_topic_rotation_receipt_created",
        "topic_rotation_receipts",
        ["created_at"],
        schema="parent",
    )


def downgrade() -> None:
    raise RuntimeError(
        "No automatic downgrade: Parent topic rotation receipts preserve retry behavior. "
        "Review/export rotation state before a separately approved forward repair."
    )
