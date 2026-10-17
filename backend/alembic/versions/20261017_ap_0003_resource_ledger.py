"""Frozen own resource ledger; application/authority adapters are separate gates."""

from alembic import op

revision = "20261017_ap_0003"
down_revision = "20261017_ap_0002"
branch_labels = None
depends_on = None

DDL = r"""
CREATE TABLE ai_policy.resource_scope (
 organization_id VARCHAR(120) NOT NULL, feature_scope VARCHAR(120) NOT NULL,
 occupied_slots BIGINT NOT NULL, PRIMARY KEY (organization_id, feature_scope),
 CONSTRAINT resource_slots CHECK (occupied_slots >= 0)
);
CREATE TABLE ai_policy.budget_bucket (
 organization_id VARCHAR(120) NOT NULL, bucket_id VARCHAR(64) NOT NULL,
 feature_scope VARCHAR(120) NOT NULL, key JSONB NOT NULL,
 held_units BIGINT NOT NULL, spent_units BIGINT NOT NULL,
 PRIMARY KEY (organization_id, bucket_id),
 FOREIGN KEY(organization_id, feature_scope)
 REFERENCES ai_policy.resource_scope (organization_id, feature_scope),
 CONSTRAINT budget_scope_key UNIQUE (organization_id, feature_scope, bucket_id),
 CONSTRAINT budget_counters CHECK (held_units >= 0 AND spent_units >= 0)
);
CREATE TABLE ai_policy.resource_reservation (
 organization_id VARCHAR(120) NOT NULL, reservation_id VARCHAR(120) NOT NULL,
 feature_scope VARCHAR(120) NOT NULL, bucket_id VARCHAR(64) NOT NULL,
 request_digest VARCHAR(64) NOT NULL, attempt_id VARCHAR(120) NOT NULL,
 state VARCHAR(20) NOT NULL, payload JSONB NOT NULL,
 PRIMARY KEY (organization_id, reservation_id),
 FOREIGN KEY(organization_id, feature_scope, bucket_id)
 REFERENCES ai_policy.budget_bucket (organization_id, feature_scope, bucket_id),
 CONSTRAINT reservation_scope UNIQUE (organization_id, feature_scope, reservation_id),
 CONSTRAINT resource_attempt UNIQUE (organization_id, request_digest, attempt_id),
 CONSTRAINT reservation_state CHECK (state IN ('reserved','consumed','released')),
 CONSTRAINT reservation_request_digest CHECK (request_digest ~ '^[0-9a-f]{64}$')
);
CREATE TABLE ai_policy.resource_event (
 organization_id VARCHAR(120) NOT NULL, event_id VARCHAR(120) NOT NULL,
 feature_scope VARCHAR(120) NOT NULL,
 reservation_id VARCHAR(120) NOT NULL, principal_id VARCHAR(120) NOT NULL,
 occurred_at TIMESTAMP WITH TIME ZONE NOT NULL, payload JSONB NOT NULL,
 delivered_at TIMESTAMP WITH TIME ZONE, PRIMARY KEY (organization_id, event_id),
 FOREIGN KEY(organization_id, feature_scope, reservation_id)
 REFERENCES ai_policy.resource_reservation (organization_id, feature_scope, reservation_id)
);
CREATE TABLE ai_policy.resource_receipt (
 organization_id VARCHAR(120) NOT NULL, principal_id VARCHAR(120) NOT NULL,
 client_request_id VARCHAR(120) NOT NULL, feature_scope VARCHAR(120) NOT NULL,
 fingerprint VARCHAR(64) NOT NULL, reservation_id VARCHAR(120) NOT NULL,
 operation VARCHAR(20) NOT NULL,
 PRIMARY KEY (organization_id, principal_id, client_request_id),
 FOREIGN KEY(organization_id, feature_scope, reservation_id)
 REFERENCES ai_policy.resource_reservation (organization_id, feature_scope, reservation_id),
 CONSTRAINT resource_operation CHECK (operation IN ('reserve','consume','release','reconcile')),
 CONSTRAINT resource_fingerprint CHECK (fingerprint ~ '^[0-9a-f]{64}$')
);
"""


def upgrade() -> None:
    for statement in DDL.split(";"):
        if statement.strip():
            op.execute(statement)
    op.execute("""
      CREATE FUNCTION ai_policy.protect_resource_reservation() RETURNS trigger
      LANGUAGE plpgsql AS $$
      BEGIN
        IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'AI_POLICY_IMMUTABLE_RESERVATION'; END IF;
        IF TG_OP = 'UPDATE' THEN
          IF OLD.state <> 'reserved' OR NEW.state NOT IN ('consumed','released') OR
             ROW(OLD.organization_id, OLD.reservation_id, OLD.feature_scope, OLD.bucket_id,
                 OLD.request_digest, OLD.attempt_id) IS DISTINCT FROM
             ROW(NEW.organization_id, NEW.reservation_id, NEW.feature_scope, NEW.bucket_id,
                 NEW.request_digest, NEW.attempt_id) OR
             (OLD.payload - ARRAY['state','settlement']) IS DISTINCT FROM
             (NEW.payload - ARRAY['state','settlement']) THEN
            RAISE EXCEPTION 'AI_POLICY_IMMUTABLE_RESERVATION';
          END IF;
        ELSIF NEW.state <> 'reserved' OR
              NEW.payload->'settlement' IS DISTINCT FROM 'null'::jsonb THEN
          RAISE EXCEPTION 'AI_POLICY_INVALID_RESERVATION';
        END IF;
        IF NEW.payload->>'state' IS DISTINCT FROM NEW.state OR
           NEW.payload->>'reservation_id' IS DISTINCT FROM NEW.reservation_id OR
           NEW.payload->>'request_digest' IS DISTINCT FROM NEW.request_digest OR
           NEW.payload->>'attempt_id' IS DISTINCT FROM NEW.attempt_id OR
           NEW.payload#>>'{terms,key,organization_id}' IS DISTINCT FROM NEW.organization_id OR
           NEW.payload#>>'{terms,key,feature_scope}' IS DISTINCT FROM NEW.feature_scope OR
           (NEW.state <> 'reserved' AND
            (NEW.payload->'settlement' IS NULL OR NEW.payload->'settlement' = 'null'::jsonb)) THEN
          RAISE EXCEPTION 'AI_POLICY_INVALID_RESERVATION';
        END IF;
        RETURN NEW;
      END; $$
    """)
    op.execute("""
      CREATE TRIGGER immutable_resource_reservation BEFORE INSERT OR UPDATE OR DELETE
      ON ai_policy.resource_reservation FOR EACH ROW
      EXECUTE FUNCTION ai_policy.protect_resource_reservation()
    """)
    op.execute("""
      CREATE FUNCTION ai_policy.protect_budget_identity() RETURNS trigger
      LANGUAGE plpgsql AS $$
      BEGIN
        IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'AI_POLICY_IMMUTABLE_BUDGET'; END IF;
        IF ROW(OLD.organization_id, OLD.bucket_id, OLD.feature_scope, OLD.key) IS DISTINCT FROM
           ROW(NEW.organization_id, NEW.bucket_id, NEW.feature_scope, NEW.key) THEN
          RAISE EXCEPTION 'AI_POLICY_IMMUTABLE_BUDGET';
        END IF;
        RETURN NEW;
      END; $$
    """)
    op.execute("""
      CREATE TRIGGER immutable_budget_identity BEFORE UPDATE OR DELETE
      ON ai_policy.budget_bucket FOR EACH ROW EXECUTE FUNCTION ai_policy.protect_budget_identity()
    """)
    op.execute("""
      CREATE TRIGGER immutable_resource_receipt BEFORE UPDATE OR DELETE
      ON ai_policy.resource_receipt FOR EACH ROW EXECUTE FUNCTION ai_policy.protect_history()
    """)
    op.execute("""
      CREATE FUNCTION ai_policy.protect_resource_event() RETURNS trigger
      LANGUAGE plpgsql AS $$
      BEGIN
        IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'AI_POLICY_IMMUTABLE_RESOURCE_EVENT'; END IF;
        IF ROW(OLD.organization_id, OLD.feature_scope, OLD.event_id,
               OLD.reservation_id, OLD.principal_id,
               OLD.occurred_at, OLD.payload) IS DISTINCT FROM
           ROW(NEW.organization_id, NEW.feature_scope, NEW.event_id,
               NEW.reservation_id, NEW.principal_id,
               NEW.occurred_at, NEW.payload) THEN
          RAISE EXCEPTION 'AI_POLICY_IMMUTABLE_RESOURCE_EVENT';
        END IF;
        RETURN NEW;
      END; $$
    """)
    op.execute("""
      CREATE TRIGGER immutable_resource_event BEFORE UPDATE OR DELETE
      ON ai_policy.resource_event FOR EACH ROW EXECUTE FUNCTION ai_policy.protect_resource_event()
    """)


def downgrade() -> None:
    for table in (
        "resource_receipt",
        "resource_event",
        "resource_reservation",
        "budget_bucket",
        "resource_scope",
    ):
        op.drop_table(table, schema="ai_policy")
    for function in (
        "protect_resource_event",
        "protect_budget_identity",
        "protect_resource_reservation",
    ):
        op.execute(f"DROP FUNCTION ai_policy.{function}()")
