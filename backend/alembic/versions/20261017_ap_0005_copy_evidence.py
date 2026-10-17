"""Append-only inventory authority/source verification history, not dispatch permission."""

from alembic import op

revision = "20261017_ap_0005"
down_revision = "20261017_ap_0004"
branch_labels = None
depends_on = None

DDL = """
CREATE TABLE ai_policy.copy_inventory_evidence (
 organization_id VARCHAR(120) NOT NULL, evidence_id VARCHAR(120) NOT NULL,
 scope_ref VARCHAR(120) NOT NULL, principal_id VARCHAR(120) NOT NULL,
 inventory_revision BIGINT NOT NULL, observed_at TIMESTAMP WITH TIME ZONE NOT NULL,
 record JSONB NOT NULL, PRIMARY KEY (organization_id, evidence_id),
 FOREIGN KEY(organization_id, scope_ref)
 REFERENCES ai_policy.copy_scope (organization_id, scope_ref),
 CONSTRAINT copy_evidence_revision CHECK (inventory_revision >= 0)
);
"""


def upgrade() -> None:
    op.execute(DDL)
    op.execute("""
      CREATE TRIGGER immutable_copy_inventory_evidence BEFORE UPDATE OR DELETE
      ON ai_policy.copy_inventory_evidence FOR EACH ROW
      EXECUTE FUNCTION ai_policy.protect_history()
    """)


def downgrade() -> None:
    op.drop_table("copy_inventory_evidence", schema="ai_policy")
