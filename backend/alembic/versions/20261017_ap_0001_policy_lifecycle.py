"""Frozen own AI-policy lifecycle branch. Upgrade only an authorized DB.

Downgrade is for disposable tests only. No mutable runtime table imports.
"""

from alembic import op

revision = "20261017_ap_0001"
down_revision = None
branch_labels = ("ai_policy",)
depends_on = None

DDL = r"""
CREATE TABLE ai_policy.receipt (
 organization_id VARCHAR(120) NOT NULL,
 principal_id VARCHAR(120) NOT NULL,
 request_id VARCHAR(120) NOT NULL,
 fingerprint VARCHAR(64) NOT NULL,
 result_json TEXT NOT NULL,
 PRIMARY KEY (organization_id, principal_id, request_id),
 CONSTRAINT receipt_hash CHECK (fingerprint ~ '^[0-9a-f]{64}$')
);
CREATE TABLE ai_policy.record (
 organization_id VARCHAR(120) NOT NULL,
 record_id VARCHAR(120) NOT NULL,
 current_version INTEGER NOT NULL,
 revision BIGINT NOT NULL,
 PRIMARY KEY (organization_id, record_id),
 CONSTRAINT record_positive CHECK (current_version > 0 AND revision > 0)
);
CREATE TABLE ai_policy.version (
 organization_id VARCHAR(120) NOT NULL,
 record_id VARCHAR(120) NOT NULL,
 version INTEGER NOT NULL,
 body_json TEXT NOT NULL,
 hash VARCHAR(64) NOT NULL,
 state VARCHAR(24) NOT NULL,
 authored_by VARCHAR(120) NOT NULL,
 created_at TIMESTAMP WITH TIME ZONE NOT NULL,
 context_revision BIGINT NOT NULL,
 review_revision BIGINT NOT NULL,
 publication_review_ids JSONB NOT NULL,
 publication_policy_version VARCHAR(120),
 recalled_at TIMESTAMP WITH TIME ZONE,
 recall_reason VARCHAR(200),
 PRIMARY KEY (organization_id, record_id, version),
 FOREIGN KEY(organization_id, record_id) REFERENCES ai_policy.record (organization_id, record_id),
 CONSTRAINT version_positive CHECK (version > 0 AND context_revision >= 0 AND review_revision >= 0),
 CONSTRAINT version_hash CHECK (hash ~ '^[0-9a-f]{64}$'),
 CONSTRAINT version_state CHECK (state IN (
 'draft','submitted','changes_requested','published','recalled','archived'))
);
CREATE TABLE ai_policy.event (
 organization_id VARCHAR(120) NOT NULL,
 event_id VARCHAR(120) NOT NULL,
 record_id VARCHAR(120) NOT NULL,
 version INTEGER NOT NULL,
 revision BIGINT NOT NULL,
 kind VARCHAR(80) NOT NULL,
 principal_id VARCHAR(120) NOT NULL,
 occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
 payload JSONB NOT NULL,
 PRIMARY KEY (organization_id, event_id),
 FOREIGN KEY(organization_id, record_id, version)
 REFERENCES ai_policy.version (organization_id, record_id, version),
 CONSTRAINT event_revision_unique UNIQUE (organization_id, record_id, revision)
);
CREATE TABLE ai_policy.review (
 organization_id VARCHAR(120) NOT NULL,
 review_id VARCHAR(120) NOT NULL,
 record_id VARCHAR(120) NOT NULL,
 version INTEGER NOT NULL,
 context_revision BIGINT NOT NULL,
 review_revision BIGINT NOT NULL,
 dimension VARCHAR(24) NOT NULL,
 proof JSONB NOT NULL,
 PRIMARY KEY (organization_id, review_id),
 FOREIGN KEY(organization_id, record_id, version)
 REFERENCES ai_policy.version (organization_id, record_id, version),
 CONSTRAINT review_revision_unique UNIQUE (organization_id, record_id, version, review_revision),
 CONSTRAINT review_dimension CHECK (dimension IN ('safety','pedagogical')),
 CONSTRAINT review_positive CHECK (context_revision > 0 AND review_revision > 0)
);
CREATE TABLE ai_policy.outbox (
 organization_id VARCHAR(120) NOT NULL,
 event_id VARCHAR(120) NOT NULL,
 payload JSONB NOT NULL,
 delivered_at TIMESTAMP WITH TIME ZONE,
 PRIMARY KEY (organization_id, event_id),
 FOREIGN KEY(organization_id, event_id) REFERENCES ai_policy.event (organization_id, event_id)
);
"""


def upgrade() -> None:
    op.execute("CREATE SCHEMA ai_policy")
    for statement in DDL.split(";"):
        if statement.strip():
            op.execute(statement)
    op.execute("""
      CREATE FUNCTION ai_policy.protect_version() RETURNS trigger
      LANGUAGE plpgsql AS $$
      BEGIN
        IF TG_OP = 'DELETE' THEN
          RAISE EXCEPTION 'AI_POLICY_IMMUTABLE_VERSION';
        END IF;
        IF ROW(OLD.organization_id, OLD.record_id, OLD.version, OLD.body_json,
               OLD.hash, OLD.authored_by, OLD.created_at)
           IS DISTINCT FROM
           ROW(NEW.organization_id, NEW.record_id, NEW.version, NEW.body_json,
               NEW.hash, NEW.authored_by, NEW.created_at) THEN
          RAISE EXCEPTION 'AI_POLICY_IMMUTABLE_VERSION';
        END IF;
        IF OLD.state IN ('recalled','archived') OR
           (OLD.state = 'published' AND NEW.state NOT IN ('recalled','archived')) OR
           NEW.context_revision < OLD.context_revision OR
           NEW.review_revision < OLD.review_revision THEN
          RAISE EXCEPTION 'AI_POLICY_TRANSITION_DENIED';
        END IF;
        IF OLD.state = 'published' AND ROW(
            OLD.context_revision, OLD.review_revision, OLD.publication_review_ids,
            OLD.publication_policy_version) IS DISTINCT FROM ROW(
            NEW.context_revision, NEW.review_revision, NEW.publication_review_ids,
            NEW.publication_policy_version) THEN
          RAISE EXCEPTION 'AI_POLICY_IMMUTABLE_PUBLICATION';
        END IF;
        RETURN NEW;
      END; $$
    """)
    op.execute("""
      CREATE TRIGGER immutable_policy_version BEFORE UPDATE OR DELETE
      ON ai_policy.version FOR EACH ROW EXECUTE FUNCTION ai_policy.protect_version()
    """)
    op.execute("""
      CREATE FUNCTION ai_policy.protect_history() RETURNS trigger
      LANGUAGE plpgsql AS $$
      BEGIN
        RAISE EXCEPTION 'AI_POLICY_IMMUTABLE_HISTORY';
      END; $$
    """)
    for table in ("review", "receipt", "event"):
        op.execute(f"CREATE TRIGGER immutable_policy_history BEFORE UPDATE OR DELETE "
                   f"ON ai_policy.{table} FOR EACH ROW "
                   f"EXECUTE FUNCTION ai_policy.protect_history()")


def downgrade() -> None:
    for table in ("outbox", "event", "review", "version", "record", "receipt"):
        op.drop_table(table, schema="ai_policy")
    op.execute("DROP FUNCTION ai_policy.protect_history()")
    op.execute("DROP FUNCTION ai_policy.protect_version()")
    op.execute("DROP SCHEMA ai_policy")
