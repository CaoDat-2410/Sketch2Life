"""Frozen own original-copy inventory; no provider dispatch or foundation rewrite."""

from alembic import op

revision = "20261017_ap_0004"
down_revision = "20261017_ap_0003"
branch_labels = None
depends_on = None

DDL = r"""
CREATE TABLE ai_policy.copy_scope (
 organization_id VARCHAR(120) NOT NULL, scope_ref VARCHAR(120) NOT NULL,
 revision BIGINT NOT NULL, purging BOOLEAN NOT NULL,
 PRIMARY KEY (organization_id, scope_ref),
 CONSTRAINT copy_scope_revision CHECK (revision >= 0)
);
CREATE TABLE ai_policy.copy_coverage (
 organization_id VARCHAR(120) NOT NULL, scope_ref VARCHAR(120) NOT NULL,
 applied_revision BIGINT NOT NULL, observation JSONB NOT NULL,
 PRIMARY KEY (organization_id, scope_ref, applied_revision),
 FOREIGN KEY(organization_id, scope_ref)
 REFERENCES ai_policy.copy_scope (organization_id, scope_ref),
 CONSTRAINT copy_coverage_revision CHECK (applied_revision > 0)
);
CREATE TABLE ai_policy.copy_registration (
 organization_id VARCHAR(120) NOT NULL, scope_ref VARCHAR(120) NOT NULL,
 copy_id VARCHAR(120) NOT NULL, kind VARCHAR(20) NOT NULL,
 original_profile_ref JSONB NOT NULL, initially_quarantined BOOLEAN NOT NULL,
 PRIMARY KEY (organization_id, scope_ref, copy_id),
 FOREIGN KEY(organization_id, scope_ref)
 REFERENCES ai_policy.copy_scope (organization_id, scope_ref),
 CONSTRAINT copy_registration_kind CHECK (kind IN ('input','output','job','cache'))
);
CREATE TABLE ai_policy.copy_registry_event (
 organization_id VARCHAR(120) NOT NULL, event_id VARCHAR(120) NOT NULL,
 scope_ref VARCHAR(120) NOT NULL, revision BIGINT NOT NULL,
 principal_id VARCHAR(120) NOT NULL, occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
 payload JSONB NOT NULL, delivered_at TIMESTAMP WITH TIME ZONE,
 PRIMARY KEY (organization_id, event_id),
 FOREIGN KEY(organization_id, scope_ref)
 REFERENCES ai_policy.copy_scope (organization_id, scope_ref),
 CONSTRAINT copy_registry_event_revision UNIQUE (organization_id, scope_ref, revision),
 CONSTRAINT copy_event_revision CHECK (revision > 0)
);
"""


def upgrade() -> None:
    for statement in DDL.split(";"):
        if statement.strip():
            op.execute(statement)
    for table in ("copy_registration", "copy_coverage"):
        op.execute(f"""
          CREATE TRIGGER immutable_copy_inventory BEFORE UPDATE OR DELETE
          ON ai_policy.{table} FOR EACH ROW EXECUTE FUNCTION ai_policy.protect_history()
        """)
    op.execute("""
      CREATE FUNCTION ai_policy.protect_copy_scope() RETURNS trigger
      LANGUAGE plpgsql AS $$
      BEGIN
        IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'AI_POLICY_IMMUTABLE_COPY_SCOPE'; END IF;
        IF ROW(OLD.organization_id, OLD.scope_ref) IS DISTINCT FROM
           ROW(NEW.organization_id, NEW.scope_ref) OR NEW.revision <> OLD.revision + 1 OR
           (OLD.purging AND NOT NEW.purging) THEN
          RAISE EXCEPTION 'AI_POLICY_IMMUTABLE_COPY_SCOPE';
        END IF;
        RETURN NEW;
      END; $$
    """)
    op.execute("""
      CREATE TRIGGER monotonic_copy_scope BEFORE UPDATE OR DELETE ON ai_policy.copy_scope
      FOR EACH ROW EXECUTE FUNCTION ai_policy.protect_copy_scope()
    """)
    op.execute("""
      CREATE FUNCTION ai_policy.protect_copy_registry_event() RETURNS trigger
      LANGUAGE plpgsql AS $$
      BEGIN
        IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'AI_POLICY_IMMUTABLE_COPY_EVENT'; END IF;
        IF ROW(OLD.organization_id, OLD.event_id, OLD.scope_ref, OLD.revision,
               OLD.principal_id, OLD.occurred_at, OLD.payload) IS DISTINCT FROM
           ROW(NEW.organization_id, NEW.event_id, NEW.scope_ref, NEW.revision,
               NEW.principal_id, NEW.occurred_at, NEW.payload) THEN
          RAISE EXCEPTION 'AI_POLICY_IMMUTABLE_COPY_EVENT';
        END IF;
        RETURN NEW;
      END; $$
    """)
    op.execute("""
      CREATE TRIGGER immutable_copy_registry_event BEFORE UPDATE OR DELETE
      ON ai_policy.copy_registry_event FOR EACH ROW
      EXECUTE FUNCTION ai_policy.protect_copy_registry_event()
    """)


def downgrade() -> None:
    for table in ("copy_registry_event", "copy_registration", "copy_coverage", "copy_scope"):
        op.drop_table(table, schema="ai_policy")
    op.execute("DROP FUNCTION ai_policy.protect_copy_registry_event()")
    op.execute("DROP FUNCTION ai_policy.protect_copy_scope()")
