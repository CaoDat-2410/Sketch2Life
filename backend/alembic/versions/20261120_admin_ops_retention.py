"""Organization revisions and explicit Platform Admin audit retention policy."""

from sqlalchemy import Column, Integer, text

from alembic import op

revision = "20261120_admin_ops_retention"
down_revision = "20261119_capacity_sandbox"
branch_labels = None
depends_on = None


def upgrade():
    from sketch2life.infrastructure.persistence.platform_models import AuditRetentionPolicyModel

    op.add_column(
        "be1_organizations",
        Column("revision", Integer(), nullable=False, server_default="1"),
    )
    op.create_check_constraint(
        "ck_be1_organization_revision", "be1_organizations", "revision > 0"
    )
    op.create_index("ix_core_audit_created", "core_audit_entries", ["created_at"])
    AuditRetentionPolicyModel.__table__.create(op.get_bind())
    op.get_bind().execute(
        text(
            "INSERT INTO platform_audit_retention_policies "
            "(policy_key, retention_days, revision, updated_by, last_purged_count) "
            "VALUES ('platform', NULL, 1, 'system', 0)"
        )
    )


def downgrade():
    raise RuntimeError(
        "Organization revisions and audit policy require a retention-aware migration"
    )
