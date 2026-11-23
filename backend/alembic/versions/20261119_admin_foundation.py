"""Add durable Admin permissions, command receipts and communication metadata."""

from alembic import op

revision = "20261119_admin_foundation"
down_revision = "20261110_ar_0001"
branch_labels = None
depends_on = None


def upgrade():
    from sketch2life.infrastructure.persistence.platform_models import PLATFORM_TABLES

    for table in PLATFORM_TABLES:
        table.create(op.get_bind())


def downgrade():
    raise RuntimeError("Admin identity/audit records require an explicit data retention migration")
