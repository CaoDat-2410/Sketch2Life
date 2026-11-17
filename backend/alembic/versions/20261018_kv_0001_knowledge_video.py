"""Frozen owned08 run/receipt schema; independent branch, no cross-owner writes.

Only apply to an authorized database. Downgrade only a disposable test database.
Do not import mutable runtime metadata into this migration.
"""

from alembic import op

revision = "20261018_kv_0001"
down_revision = None
branch_labels = ("knowledge_video",)
depends_on = None

DDL = r"""
CREATE TABLE knowledge_video.run (
    organization_id VARCHAR(120) NOT NULL,
    video_id VARCHAR(120) NOT NULL,
    session_id VARCHAR(120) NOT NULL,
    job_id VARCHAR(120) NOT NULL,
    run_revision BIGINT NOT NULL,
    pin_digest VARCHAR(64) NOT NULL,
    run_json JSONB NOT NULL,
    PRIMARY KEY (organization_id, video_id),
    CONSTRAINT run_one_job UNIQUE (organization_id, job_id),
    CONSTRAINT run_one_semantic UNIQUE (organization_id, session_id, pin_digest),
    CONSTRAINT run_receipt_target UNIQUE (organization_id, session_id, video_id, pin_digest),
    CONSTRAINT run_revision_positive CHECK (run_revision > 0),
    CONSTRAINT run_pin_hash CHECK (pin_digest ~ '^[0-9a-f]{64}$'),
    CONSTRAINT run_json_object CHECK (jsonb_typeof(run_json) = 'object')
);
CREATE TABLE knowledge_video.receipt (
    organization_id VARCHAR(120) NOT NULL,
    session_id VARCHAR(120) NOT NULL,
    principal_id VARCHAR(120) NOT NULL,
    idempotency_key VARCHAR(120) NOT NULL,
    command_hash VARCHAR(64) NOT NULL,
    pin_digest VARCHAR(64) NOT NULL,
    video_id VARCHAR(120) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (organization_id, session_id, principal_id, idempotency_key),
    CONSTRAINT receipt_exact_run FOREIGN KEY
        (organization_id, session_id, video_id, pin_digest)
        REFERENCES knowledge_video.run (organization_id, session_id, video_id, pin_digest),
    CONSTRAINT receipt_body_hash CHECK (command_hash ~ '^[0-9a-f]{64}$'),
    CONSTRAINT receipt_pin_hash CHECK (pin_digest ~ '^[0-9a-f]{64}$')
);
"""


def upgrade() -> None:
    op.execute("CREATE SCHEMA knowledge_video")
    for statement in DDL.split(";"):
        if statement.strip():
            op.execute(statement)


def downgrade() -> None:
    op.execute("DROP TABLE knowledge_video.receipt")
    op.execute("DROP TABLE knowledge_video.run")
    op.execute("DROP SCHEMA knowledge_video")
