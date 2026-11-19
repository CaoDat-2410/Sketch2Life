"""BE1-owned command receipts for idempotent identity commands (FEAT-066 C5, CA-6).

Generic module receipt (data-table register line 91): Platform Admin account create and update
now; a tenant-scoped BE1 command puts its organization in ``operation_scope`` and may also record
``organization_id``. The response holds no email or display name. Pending register amendment:
see the C5 evidence note.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20261119_ar_0002"
down_revision = "20261110_ar_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "be1_command_receipts",
        sa.Column("principal_ref", sa.String(length=256), nullable=False),
        sa.Column("operation_scope", sa.String(length=256), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("organization_id", sa.String(length=128), nullable=True),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("response_json", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "principal_ref", "operation_scope", "idempotency_key", name="pk_be1_command_receipts"
        ),
        sa.CheckConstraint(
            "length(request_fingerprint) = 64", name="ck_be1_command_receipt_fingerprint"
        ),
    )


def downgrade() -> None:
    op.drop_table("be1_command_receipts")
