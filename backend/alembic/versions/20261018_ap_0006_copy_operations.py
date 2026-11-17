"""Frozen exact copy-operation intents and authority observations, not provider effects."""

from alembic import op

revision = "20261018_ap_0006"
down_revision = "20261017_ap_0005"
branch_labels = None
depends_on = None

DDL = """
CREATE TABLE ai_policy.copy_operation (
 organization_id VARCHAR(120) NOT NULL, scope_ref VARCHAR(120) NOT NULL,
 operation_key VARCHAR(64) NOT NULL, copy_id VARCHAR(120) NOT NULL,
 envelope JSONB NOT NULL, PRIMARY KEY (organization_id, scope_ref, operation_key),
 FOREIGN KEY(organization_id, scope_ref, copy_id)
 REFERENCES ai_policy.copy_registration (organization_id, scope_ref, copy_id)
);
CREATE TABLE ai_policy.copy_operation_authority (
 organization_id VARCHAR(120) NOT NULL, observation_id VARCHAR(120) NOT NULL,
 scope_ref VARCHAR(120) NOT NULL, operation_key VARCHAR(64) NOT NULL,
 observation JSONB NOT NULL, PRIMARY KEY (organization_id, observation_id),
 FOREIGN KEY(organization_id, scope_ref, operation_key)
 REFERENCES ai_policy.copy_operation (organization_id, scope_ref, operation_key)
);
"""


def upgrade() -> None:
    for statement in DDL.split(";"):
        if statement.strip():
            op.execute(statement)
    for table in ("copy_operation", "copy_operation_authority"):
        op.execute(f"""
          CREATE TRIGGER immutable_copy_operation BEFORE UPDATE OR DELETE
          ON ai_policy.{table} FOR EACH ROW EXECUTE FUNCTION ai_policy.protect_history()
        """)


def downgrade() -> None:
    for table in ("copy_operation_authority", "copy_operation"):
        op.drop_table(table, schema="ai_policy")
