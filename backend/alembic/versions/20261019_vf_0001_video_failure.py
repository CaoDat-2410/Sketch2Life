"""Frozen own10 storage; no published migrations or cross-owner tables touched."""

from alembic import op

revision = "20261019_vf_0001"
down_revision = None
branch_labels = ("video_failure",)
depends_on = None

DDL = r"""
CREATE TABLE video_failure.intent (
 organization_id VARCHAR(120) NOT NULL, session_id VARCHAR(120) NOT NULL,
 principal_id VARCHAR(120) NOT NULL, client_key VARCHAR(120) NOT NULL,
 disposition_id VARCHAR(120) NOT NULL, claim_key VARCHAR(64) NOT NULL,
 revision BIGINT NOT NULL, payload JSONB NOT NULL,
 PRIMARY KEY(organization_id,session_id,principal_id,client_key),
 CONSTRAINT failure_one_winner UNIQUE(organization_id,claim_key),
 CONSTRAINT failure_disposition_id UNIQUE(organization_id,disposition_id),
 CONSTRAINT failure_revision CHECK(revision IN (1,2)),
 CONSTRAINT failure_claim CHECK(claim_key ~ '^[0-9a-f]{64}$'),
 CONSTRAINT failure_object CHECK(jsonb_typeof(payload) = 'object')
);
CREATE TABLE video_failure.history (
 organization_id VARCHAR(120) NOT NULL, disposition_id VARCHAR(120) NOT NULL,
 revision BIGINT NOT NULL, payload JSONB NOT NULL,
 PRIMARY KEY(organization_id,disposition_id,revision),
 CONSTRAINT fh_revision CHECK(revision IN (1,2)),
 CONSTRAINT fh_object CHECK(jsonb_typeof(payload) = 'object')
);
CREATE TABLE video_failure.event (
 organization_id VARCHAR(120) NOT NULL, disposition_id VARCHAR(120) NOT NULL,
 revision BIGINT NOT NULL, operation_key VARCHAR(64) NOT NULL,
 target_digest VARCHAR(64) NOT NULL,
 PRIMARY KEY(organization_id,disposition_id,revision),
 CONSTRAINT fe_revision CHECK(revision IN (1,2)),
 CONSTRAINT fe_operation CHECK(operation_key ~ '^[0-9a-f]{64}$'),
 CONSTRAINT fe_target CHECK(target_digest ~ '^[0-9a-f]{64}$')
);
"""
IMMUTABLE = r"""
CREATE FUNCTION video_failure.immutable_row() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'immutable video failure history'; END; $$
"""
GUARD = r"""
CREATE FUNCTION video_failure.guard_intent() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP = 'DELETE' THEN RAISE EXCEPTION 'video failure delete forbidden'; END IF;
 IF (NEW.organization_id,NEW.session_id,NEW.principal_id,NEW.client_key,
     NEW.disposition_id,NEW.claim_key) IS DISTINCT FROM
    (OLD.organization_id,OLD.session_id,OLD.principal_id,OLD.client_key,
     OLD.disposition_id,OLD.claim_key)
    OR OLD.revision <> 1 OR NEW.revision <> 2
    OR (OLD.payload #> '{value,receipt}') IS DISTINCT FROM 'null'::jsonb
    OR (NEW.payload #> '{value,receipt}') IS NOT DISTINCT FROM 'null'::jsonb
    OR (NEW.payload #> '{value}') - 'receipt' - 'revision'
       IS DISTINCT FROM (OLD.payload #> '{value}') - 'receipt' - 'revision'
 THEN RAISE EXCEPTION 'video failure stale or immutable intent'; END IF;
 RETURN NEW;
END; $$
"""


def upgrade() -> None:
    op.execute("CREATE SCHEMA video_failure")
    for statement in DDL.split(";"):
        if statement.strip():
            op.execute(statement)
    op.execute(IMMUTABLE)
    op.execute(GUARD)
    for table in ("history", "event"):
        op.execute(
            f"CREATE TRIGGER immutable_row BEFORE UPDATE OR DELETE ON video_failure.{table} "
            "FOR EACH ROW EXECUTE FUNCTION video_failure.immutable_row()"
        )
    op.execute(
        "CREATE TRIGGER guard_intent BEFORE UPDATE OR DELETE ON video_failure.intent "
        "FOR EACH ROW EXECUTE FUNCTION video_failure.guard_intent()"
    )


def downgrade() -> None:
    # Exact own schema, only separately approved disposable test environment.
    for table in ("event", "history", "intent"):
        op.execute(f"DROP TABLE video_failure.{table}")
    op.execute("DROP FUNCTION video_failure.guard_intent()")
    op.execute("DROP FUNCTION video_failure.immutable_row()")
    op.execute("DROP SCHEMA video_failure")
