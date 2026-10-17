"""Own delivery CAS/current state and immutable history; no provider/copy deletion claim."""

from alembic import op

revision = "20261018_ap_0007"
down_revision = "20261018_ap_0006"
branch_labels = None
depends_on = None

DDL = """
CREATE TABLE ai_policy.copy_delivery (
 organization_id VARCHAR(120) NOT NULL, scope_ref VARCHAR(120) NOT NULL,
 operation_key VARCHAR(64) NOT NULL, revision BIGINT NOT NULL,
 status VARCHAR(24) NOT NULL, snapshot JSONB NOT NULL,
 PRIMARY KEY (organization_id, scope_ref, operation_key),
 FOREIGN KEY(organization_id, scope_ref, operation_key)
 REFERENCES ai_policy.copy_operation (organization_id, scope_ref, operation_key),
 CONSTRAINT copy_delivery_revision CHECK (revision > 0),
 CONSTRAINT copy_delivery_status CHECK
 (status IN ('in_flight','pending','unsupported','exception','receipt_available'))
);
CREATE TABLE ai_policy.copy_delivery_history (
 organization_id VARCHAR(120) NOT NULL, scope_ref VARCHAR(120) NOT NULL,
 operation_key VARCHAR(64) NOT NULL, revision BIGINT NOT NULL, snapshot JSONB NOT NULL,
 PRIMARY KEY (organization_id, scope_ref, operation_key, revision),
 FOREIGN KEY(organization_id, scope_ref, operation_key)
 REFERENCES ai_policy.copy_operation (organization_id, scope_ref, operation_key),
 CONSTRAINT copy_delivery_history_revision CHECK (revision > 0)
);
"""


def upgrade() -> None:
    for statement in DDL.split(";"):
        if statement.strip():
            op.execute(statement)
    op.execute("""
      CREATE TRIGGER immutable_copy_delivery_history BEFORE UPDATE OR DELETE
      ON ai_policy.copy_delivery_history FOR EACH ROW
      EXECUTE FUNCTION ai_policy.protect_history()
    """)
    op.execute("""
      CREATE FUNCTION ai_policy.protect_copy_delivery() RETURNS trigger
      LANGUAGE plpgsql AS $$ BEGIN
        IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'AI_POLICY_IMMUTABLE_DELIVERY'; END IF;
        IF ROW(OLD.organization_id, OLD.scope_ref, OLD.operation_key) IS DISTINCT FROM
           ROW(NEW.organization_id, NEW.scope_ref, NEW.operation_key) OR
           NEW.revision <> OLD.revision + 1 THEN
          RAISE EXCEPTION 'AI_POLICY_IMMUTABLE_DELIVERY';
        END IF;
        RETURN NEW;
      END; $$
    """)
    op.execute("""
      CREATE TRIGGER monotonic_copy_delivery BEFORE UPDATE OR DELETE
      ON ai_policy.copy_delivery FOR EACH ROW EXECUTE FUNCTION ai_policy.protect_copy_delivery()
    """)


def downgrade() -> None:
    for table in ("copy_delivery_history", "copy_delivery"):
        op.drop_table(table, schema="ai_policy")
    op.execute("DROP FUNCTION ai_policy.protect_copy_delivery()")
