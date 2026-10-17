"""Frozen BE2-12 learning_content schema; own module branch, no cross-owner FK.

Upgrade only an authorized database; downgrade only a disposable test database.
Never import mutable runtime metadata into this frozen migration.
"""

from __future__ import annotations

from alembic import op

revision = "20261017_lc_0001"
down_revision = None
branch_labels = ("learning_content",)
depends_on = None

DDL = r"""
CREATE TABLE learning_content.receipt (
	organization_id VARCHAR(120) NOT NULL,
	principal_id VARCHAR(120) NOT NULL,
	request_id VARCHAR(120) NOT NULL,
	fingerprint VARCHAR(64) NOT NULL,
	result_json TEXT NOT NULL,
	PRIMARY KEY (organization_id, principal_id, request_id),
	CONSTRAINT receipt_hash CHECK (fingerprint ~ '^[0-9a-f]{64}$')
);
CREATE TABLE learning_content.record (
	organization_id VARCHAR(120) NOT NULL,
	record_id VARCHAR(120) NOT NULL,
	current_version INTEGER NOT NULL,
	revision BIGINT NOT NULL,
	PRIMARY KEY (organization_id, record_id),
	CONSTRAINT record_positive CHECK (current_version > 0 AND revision > 0)
);
CREATE TABLE learning_content.version (
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
	FOREIGN KEY(organization_id, record_id)
        REFERENCES learning_content.record (organization_id, record_id),
	CONSTRAINT version_positive CHECK (
        version > 0 AND context_revision >= 0 AND review_revision >= 0),
	CONSTRAINT version_hash CHECK (hash ~ '^[0-9a-f]{64}$'),
	CONSTRAINT version_state CHECK (state IN (
        'draft','submitted','changes_requested','published','recalled','archived'))
);
CREATE TABLE learning_content.event (
	event_id VARCHAR(120) NOT NULL,
	organization_id VARCHAR(120) NOT NULL,
	record_id VARCHAR(120) NOT NULL,
	version INTEGER NOT NULL,
	revision BIGINT NOT NULL,
	kind VARCHAR(80) NOT NULL,
	principal_id VARCHAR(120) NOT NULL,
	occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
	payload JSONB NOT NULL,
	PRIMARY KEY (event_id),
	FOREIGN KEY(organization_id, record_id, version)
        REFERENCES learning_content.version (organization_id, record_id, version)
);
CREATE TABLE learning_content.review (
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
        REFERENCES learning_content.version (organization_id, record_id, version),
	CONSTRAINT review_dimension CHECK (dimension IN ('safety','pedagogical'))
);
CREATE TABLE learning_content.outbox (
	event_id VARCHAR(120) NOT NULL,
	organization_id VARCHAR(120) NOT NULL,
	payload JSONB NOT NULL,
	delivered_at TIMESTAMP WITH TIME ZONE,
	PRIMARY KEY (event_id),
	FOREIGN KEY(event_id)
        REFERENCES learning_content.event (event_id)
);
"""


def upgrade() -> None:
    op.execute("CREATE SCHEMA learning_content")
    for statement in DDL.split(";"):
        if statement.strip():
            op.execute(statement)
    op.execute("""
        CREATE FUNCTION learning_content.protect_version() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
          IF ROW(OLD.organization_id, OLD.record_id, OLD.version, OLD.body_json,
                 OLD.hash, OLD.authored_by, OLD.created_at)
             IS DISTINCT FROM
             ROW(NEW.organization_id, NEW.record_id, NEW.version, NEW.body_json,
                 NEW.hash, NEW.authored_by, NEW.created_at) THEN
            RAISE EXCEPTION 'CONTENT_IMMUTABLE_VERSION';
          END IF;
          RETURN NEW;
        END; $$
    """)
    op.execute("""
        CREATE TRIGGER immutable_content_version BEFORE UPDATE
        ON learning_content.version FOR EACH ROW
        EXECUTE FUNCTION learning_content.protect_version()
    """)
    op.execute("""
        CREATE FUNCTION learning_content.protect_history() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
          RAISE EXCEPTION 'CONTENT_IMMUTABLE_HISTORY';
        END; $$
    """)
    for table in ("review", "event", "receipt"):
        op.execute(
            f"CREATE TRIGGER immutable_content_history BEFORE UPDATE OR DELETE "
            f"ON learning_content.{table} FOR EACH ROW "
            f"EXECUTE FUNCTION learning_content.protect_history()"
        )


def downgrade() -> None:
    for table in ("outbox", "event", "receipt", "review", "version", "record"):
        op.drop_table(table, schema="learning_content")
    op.execute("DROP FUNCTION learning_content.protect_history()")
    op.execute("DROP FUNCTION learning_content.protect_version()")
    op.execute("DROP SCHEMA learning_content")
