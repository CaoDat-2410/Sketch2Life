"""Frozen own effective pin and durable scope intent; no provider/jobs writes."""

from alembic import op

revision = "20261017_ap_0002"
down_revision = "20261017_ap_0001"
branch_labels = None
depends_on = None

DDL = r"""
CREATE TABLE ai_policy.effective_scope (
 organization_id VARCHAR(120) NOT NULL,
 feature_scope VARCHAR(120) NOT NULL,
 epoch BIGINT NOT NULL,
 record_id VARCHAR(120), version INTEGER, hash VARCHAR(64), disabled BOOLEAN NOT NULL,
 PRIMARY KEY (organization_id, feature_scope),
 CONSTRAINT scope_epoch CHECK (epoch >= 0),
 CONSTRAINT scope_pin CHECK (
 (record_id IS NULL AND version IS NULL AND hash IS NULL) OR
 (record_id IS NOT NULL AND version IS NOT NULL AND hash IS NOT NULL
 AND version > 0 AND hash ~ '^[0-9a-f]{64}$'))
);
CREATE TABLE ai_policy.scope_transition (
 organization_id VARCHAR(120) NOT NULL,
 feature_scope VARCHAR(120) NOT NULL,
 epoch BIGINT NOT NULL,
 event_id VARCHAR(120) NOT NULL,
 principal_id VARCHAR(120) NOT NULL,
 occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
 payload JSONB NOT NULL,
 delivered_at TIMESTAMP WITH TIME ZONE,
 PRIMARY KEY (organization_id, feature_scope, epoch),
 FOREIGN KEY(organization_id, feature_scope)
 REFERENCES ai_policy.effective_scope (organization_id, feature_scope),
 CONSTRAINT scope_event_unique UNIQUE (organization_id, event_id),
 CONSTRAINT scope_event_epoch CHECK (epoch > 0)
);
"""


def upgrade() -> None:
    for statement in DDL.split(";"):
        if statement.strip():
            op.execute(statement)
    op.execute("""
      CREATE FUNCTION ai_policy.protect_scope_event() RETURNS trigger
      LANGUAGE plpgsql AS $$
      BEGIN
        IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'AI_POLICY_IMMUTABLE_SCOPE_EVENT'; END IF;
        IF ROW(OLD.organization_id, OLD.feature_scope, OLD.epoch, OLD.event_id,
               OLD.principal_id, OLD.occurred_at, OLD.payload) IS DISTINCT FROM
           ROW(NEW.organization_id, NEW.feature_scope, NEW.epoch, NEW.event_id,
               NEW.principal_id, NEW.occurred_at, NEW.payload) THEN
          RAISE EXCEPTION 'AI_POLICY_IMMUTABLE_SCOPE_EVENT';
        END IF;
        RETURN NEW;
      END; $$
    """)
    op.execute("""
      CREATE TRIGGER immutable_scope_event BEFORE UPDATE OR DELETE
      ON ai_policy.scope_transition FOR EACH ROW EXECUTE FUNCTION ai_policy.protect_scope_event()
    """)


def downgrade() -> None:
    op.drop_table("scope_transition", schema="ai_policy")
    op.drop_table("effective_scope", schema="ai_policy")
    op.execute("DROP FUNCTION ai_policy.protect_scope_event()")
