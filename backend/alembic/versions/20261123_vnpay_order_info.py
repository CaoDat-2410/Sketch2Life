"""Persist VNPAY order description for exact payment reconciliation."""

from alembic import op
from sqlalchemy import Column, String, inspect

revision = "20261123_vnpay_order_info"
down_revision = "20261122_quota_commerce"
branch_labels = None
depends_on = None


def upgrade():
    names = {
        column["name"]
        for column in inspect(op.get_bind()).get_columns(
            "payment_attempts", schema="billing"
        )
    }
    if "provider_order_info" not in names:
        op.add_column(
            "payment_attempts",
            Column("provider_order_info", String(255), nullable=True),
            schema="billing",
        )


def downgrade():
    raise RuntimeError("Payment attempt reconciliation metadata is retained")
