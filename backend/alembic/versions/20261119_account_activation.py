"""Require verified Firebase email for newly provisioned accounts; preserve existing identities."""

import sqlalchemy as sa

from alembic import op

revision = "20261119_account_activation"
down_revision = "20261119_admin_feedback"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "be1_adult_identities",
        sa.Column(
            "email_verification_required", sa.Boolean, nullable=False, server_default=sa.false()
        ),
    )
    op.add_column(
        "be1_organization_assignments",
        sa.Column("pending_activation", sa.Boolean, nullable=False, server_default=sa.false()),
    )


def downgrade():
    raise RuntimeError("Account activation state requires an explicit compatibility migration")
