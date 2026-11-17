"""Append-only delivery authority history, never live dispatch permission."""

from alembic import op

revision = "20261018_ap_0008"
down_revision = "20261018_ap_0007"
branch_labels = None
depends_on = None

DDL = """
CREATE TABLE ai_policy.copy_delivery_authority (
 organization_id VARCHAR(120) NOT NULL, evidence_id VARCHAR(120) NOT NULL,
 scope_ref VARCHAR(120) NOT NULL, operation_key VARCHAR(64) NOT NULL,
 evidence JSONB NOT NULL, PRIMARY KEY (organization_id, evidence_id),
 FOREIGN KEY(organization_id, scope_ref, operation_key)
 REFERENCES ai_policy.copy_operation (organization_id, scope_ref, operation_key)
);
"""


def upgrade() -> None:
    op.execute(DDL)
    op.execute("""
      CREATE TRIGGER immutable_delivery_authority BEFORE UPDATE OR DELETE
      ON ai_policy.copy_delivery_authority FOR EACH ROW EXECUTE FUNCTION ai_policy.protect_history()
    """)


def downgrade() -> None:
    op.drop_table("copy_delivery_authority", schema="ai_policy")
