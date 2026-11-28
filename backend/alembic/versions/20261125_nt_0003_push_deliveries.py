"""DDL-C part 3: durable, content-free push delivery attempts (T-NTF1).

Revision ID: 20261125_nt_0003
Revises: 20261121_nt_0002
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20261125_nt_0003"
down_revision = "20261121_nt_0002"
branch_labels = None
depends_on = None

SCHEMA = "notifications"
TABLE = "push_deliveries"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("delivery_id", sa.String(length=36), primary_key=True),
        sa.Column("inbox_item_id", sa.String(length=36), nullable=False),
        sa.Column("push_endpoint_id", sa.String(length=36), nullable=False),
        sa.Column("recipient_account_id", sa.String(length=36), nullable=False),
        sa.Column(
            "status", sa.String(length=16), server_default=sa.text("'PENDING'"), nullable=False
        ),
        sa.Column("attempt_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_code", sa.String(length=24), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["inbox_item_id"],
            ["notifications.inbox_items.inbox_item_id"],
            name="fk_push_delivery_inbox_item",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["push_endpoint_id"],
            ["notifications.push_endpoints.push_endpoint_id"],
            name="fk_push_delivery_endpoint",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "inbox_item_id", "push_endpoint_id", name="uq_push_delivery_item_endpoint"
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'SENT', 'FAILED', 'DEAD_ENDPOINT', 'SKIPPED')",
            name="ck_push_delivery_status",
        ),
        sa.CheckConstraint("attempt_count BETWEEN 0 AND 5", name="ck_push_delivery_attempts"),
        sa.CheckConstraint(
            "last_error_code IS NULL OR last_error_code IN "
            "('TRANSIENT', 'TIMEOUT', 'RATE_LIMITED', 'ENDPOINT_GONE', 'REJECTED', 'SENDER_ERROR')",
            name="ck_push_delivery_error",
        ),
        sa.CheckConstraint(
            "(status = 'PENDING' AND completed_at IS NULL) OR "
            "(status <> 'PENDING' AND completed_at IS NOT NULL)",
            name="ck_push_delivery_completed",
        ),
        sa.CheckConstraint(
            "(last_attempt_at IS NULL OR last_attempt_at >= created_at) "
            "AND (completed_at IS NULL OR completed_at >= created_at)",
            name="ck_push_delivery_times",
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_push_delivery_due",
        TABLE,
        ["next_attempt_at", "push_endpoint_id", "created_at", "delivery_id"],
        schema=SCHEMA,
        postgresql_where=sa.text("status = 'PENDING'"),
    )
    op.create_index(
        "ix_push_delivery_endpoint_pending",
        TABLE,
        ["push_endpoint_id", "created_at", "delivery_id"],
        schema=SCHEMA,
        postgresql_where=sa.text("status = 'PENDING'"),
    )


def downgrade() -> None:
    bind = op.get_bind()
    has_rows = bind.execute(
        sa.text(f"SELECT EXISTS (SELECT 1 FROM {SCHEMA}.{TABLE} LIMIT 1)")
    ).scalar_one()
    if has_rows:
        raise RuntimeError("push delivery downgrade refused: rows exist")
    op.drop_index("ix_push_delivery_endpoint_pending", table_name=TABLE, schema=SCHEMA)
    op.drop_index("ix_push_delivery_due", table_name=TABLE, schema=SCHEMA)
    op.drop_table(TABLE, schema=SCHEMA)
