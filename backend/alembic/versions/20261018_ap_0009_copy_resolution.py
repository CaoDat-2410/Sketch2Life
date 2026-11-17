"""Owned receipt resolution/current copy CAS, immutable proof history and no resurrection."""

from alembic import op

revision = "20261018_ap_0009"
down_revision = "20261018_ap_0008"
branch_labels = None
depends_on = None

DDL = """
CREATE TABLE ai_policy.copy_lifecycle (
 organization_id VARCHAR(120) NOT NULL, scope_ref VARCHAR(120) NOT NULL,
 copy_id VARCHAR(120) NOT NULL, revision BIGINT NOT NULL, snapshot JSONB NOT NULL,
 PRIMARY KEY (organization_id, scope_ref, copy_id),
 FOREIGN KEY(organization_id, scope_ref, copy_id)
 REFERENCES ai_policy.copy_registration (organization_id, scope_ref, copy_id),
 CONSTRAINT copy_lifecycle_revision CHECK (revision > 0)
);
CREATE TABLE ai_policy.copy_resolution (
 organization_id VARCHAR(120) NOT NULL, scope_ref VARCHAR(120) NOT NULL,
 resolution_key VARCHAR(64) NOT NULL, copy_id VARCHAR(120) NOT NULL,
 operation_key VARCHAR(64) NOT NULL, revision BIGINT NOT NULL,
 before_state JSONB NOT NULL, after_state JSONB NOT NULL, observation JSONB NOT NULL,
 PRIMARY KEY (organization_id, scope_ref, resolution_key),
 FOREIGN KEY(organization_id, scope_ref, copy_id)
 REFERENCES ai_policy.copy_registration (organization_id, scope_ref, copy_id),
 FOREIGN KEY(organization_id, scope_ref, operation_key)
 REFERENCES ai_policy.copy_operation (organization_id, scope_ref, operation_key),
 CONSTRAINT copy_resolution_copy_revision UNIQUE (organization_id, scope_ref, copy_id, revision),
 CONSTRAINT copy_resolution_revision CHECK (revision > 0)
);
"""


def upgrade() -> None:
    for statement in DDL.split(";"):
        if statement.strip():
            op.execute(statement)
    op.execute("""
      CREATE TRIGGER immutable_copy_resolution BEFORE UPDATE OR DELETE
      ON ai_policy.copy_resolution FOR EACH ROW EXECUTE FUNCTION ai_policy.protect_history()
    """)
    op.execute("""
      CREATE FUNCTION ai_policy.protect_copy_lifecycle() RETURNS trigger
      LANGUAGE plpgsql AS $$ BEGIN
        IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'AI_POLICY_IMMUTABLE_COPY_LIFECYCLE'; END IF;
        IF ROW(OLD.organization_id, OLD.scope_ref, OLD.copy_id) IS DISTINCT FROM
           ROW(NEW.organization_id, NEW.scope_ref, NEW.copy_id) OR
           NEW.revision <> OLD.revision + 1 OR
           OLD.snapshot->'registration' IS DISTINCT FROM NEW.snapshot->'registration' OR
           (OLD.snapshot->>'status' = 'deleted' AND
             ROW(OLD.snapshot->>'status', OLD.snapshot->'purge_reference',
                 OLD.snapshot->>'purge_evidence_kind') IS DISTINCT FROM
             ROW(NEW.snapshot->>'status', NEW.snapshot->'purge_reference',
                 NEW.snapshot->>'purge_evidence_kind')) OR
           (OLD.snapshot->>'cancel_confirmed' = 'true' AND
             NEW.snapshot->>'cancel_confirmed' IS DISTINCT FROM 'true') OR
           (OLD.snapshot->>'cancel_evidence_kind' = 'provider' AND
             NEW.snapshot->>'cancel_evidence_kind' IS DISTINCT FROM 'provider')
        THEN RAISE EXCEPTION 'AI_POLICY_IMMUTABLE_COPY_LIFECYCLE'; END IF;
        RETURN NEW;
      END; $$
    """)
    op.execute("""
      CREATE TRIGGER monotonic_copy_lifecycle BEFORE UPDATE OR DELETE
      ON ai_policy.copy_lifecycle FOR EACH ROW EXECUTE FUNCTION ai_policy.protect_copy_lifecycle()
    """)


def downgrade() -> None:
    for table in ("copy_resolution", "copy_lifecycle"):
        op.drop_table(table, schema="ai_policy")
    op.execute("DROP FUNCTION ai_policy.protect_copy_lifecycle()")
