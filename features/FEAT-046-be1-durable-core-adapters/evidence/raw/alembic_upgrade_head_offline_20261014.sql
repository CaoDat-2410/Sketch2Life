BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 20261014_0001

CREATE TABLE core_aggregate_revisions (
    aggregate_id VARCHAR(128) NOT NULL,
    organization_id VARCHAR(128) NOT NULL,
    revision BIGINT NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (aggregate_id),
    CONSTRAINT ck_core_aggregate_revision_positive CHECK (revision > 0)
);

CREATE INDEX ix_core_aggregate_revisions_organization_id ON core_aggregate_revisions (organization_id);

CREATE TABLE core_canvas_operations (
    operation_id VARCHAR(128) NOT NULL,
    organization_id VARCHAR(128) NOT NULL,
    canvas_id VARCHAR(128) NOT NULL,
    session_id VARCHAR(128) NOT NULL,
    turn_id VARCHAR(128) NOT NULL,
    participant_id VARCHAR(128) NOT NULL,
    document_epoch INTEGER NOT NULL,
    resulting_revision BIGINT NOT NULL,
    request_fingerprint VARCHAR(64) NOT NULL,
    accepted_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (operation_id),
    CONSTRAINT ck_core_operation_epoch_positive CHECK (document_epoch > 0),
    CONSTRAINT ck_core_operation_revision_positive CHECK (resulting_revision > 0),
    CONSTRAINT ck_core_operation_fingerprint_length CHECK (length(request_fingerprint) = 64),
    CONSTRAINT uq_core_canvas_epoch_revision UNIQUE (canvas_id, document_epoch, resulting_revision),
    FOREIGN KEY(canvas_id) REFERENCES core_aggregate_revisions (aggregate_id) ON DELETE RESTRICT
);

CREATE INDEX ix_core_operation_canvas_epoch_revision ON core_canvas_operations (canvas_id, document_epoch, resulting_revision);

CREATE TABLE core_idempotency_receipts (
    organization_id VARCHAR(128) NOT NULL,
    scope VARCHAR(256) NOT NULL,
    key VARCHAR(256) NOT NULL,
    request_fingerprint VARCHAR(64) NOT NULL,
    resulting_revision BIGINT NOT NULL,
    operation_id VARCHAR(128) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (organization_id, scope, key),
    CONSTRAINT ck_core_receipt_revision_positive CHECK (resulting_revision > 0),
    CONSTRAINT ck_core_receipt_fingerprint_length CHECK (length(request_fingerprint) = 64),
    UNIQUE (operation_id),
    FOREIGN KEY(operation_id) REFERENCES core_canvas_operations (operation_id) ON DELETE RESTRICT
);

CREATE TABLE core_canvas_checkpoints (
    checkpoint_id VARCHAR(128) NOT NULL,
    organization_id VARCHAR(128) NOT NULL,
    canvas_id VARCHAR(128) NOT NULL,
    document_epoch INTEGER NOT NULL,
    revision BIGINT NOT NULL,
    through_operation_id VARCHAR(128) NOT NULL,
    checksum_sha256 VARCHAR(64) NOT NULL,
    storage_ref VARCHAR(512) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (checkpoint_id),
    CONSTRAINT ck_core_checkpoint_epoch_positive CHECK (document_epoch > 0),
    CONSTRAINT ck_core_checkpoint_revision_positive CHECK (revision > 0),
    CONSTRAINT ck_core_checkpoint_checksum_length CHECK (length(checksum_sha256) = 64),
    CONSTRAINT uq_core_checkpoint_revision UNIQUE (canvas_id, document_epoch, revision),
    FOREIGN KEY(canvas_id) REFERENCES core_aggregate_revisions (aggregate_id) ON DELETE RESTRICT,
    FOREIGN KEY(through_operation_id) REFERENCES core_canvas_operations (operation_id) ON DELETE RESTRICT
);

CREATE INDEX ix_core_checkpoint_canvas_latest ON core_canvas_checkpoints (canvas_id, document_epoch, revision);

CREATE TABLE core_asset_metadata (
    asset_ref VARCHAR(256) NOT NULL,
    asset_version INTEGER NOT NULL,
    organization_id VARCHAR(128) NOT NULL,
    content_sha256 VARCHAR(64) NOT NULL,
    media_type VARCHAR(128) NOT NULL,
    source_refs JSONB NOT NULL,
    derived_from_ref VARCHAR(256),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (asset_ref, asset_version),
    CONSTRAINT ck_core_asset_version_positive CHECK (asset_version > 0),
    CONSTRAINT ck_core_asset_hash_length CHECK (length(content_sha256) = 64)
);

CREATE INDEX ix_core_asset_organization ON core_asset_metadata (organization_id, asset_ref);

CREATE TABLE core_audit_entries (
    audit_id VARCHAR(36) NOT NULL,
    organization_id VARCHAR(128) NOT NULL,
    actor_ref VARCHAR(128),
    action VARCHAR(128) NOT NULL,
    resource_type VARCHAR(64) NOT NULL,
    resource_id VARCHAR(256) NOT NULL,
    decision VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (audit_id)
);

CREATE INDEX ix_core_audit_org_created ON core_audit_entries (organization_id, created_at);

CREATE INDEX ix_core_audit_resource_created ON core_audit_entries (resource_id, created_at);

CREATE TABLE core_outbox_events (
    event_id VARCHAR(36) NOT NULL,
    event_type VARCHAR(160) NOT NULL,
    organization_id VARCHAR(128) NOT NULL,
    aggregate_id VARCHAR(128) NOT NULL,
    aggregate_revision BIGINT NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(16) NOT NULL,
    attempt_count INTEGER NOT NULL,
    available_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    lease_owner VARCHAR(128),
    lease_until TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (event_id),
    CONSTRAINT ck_core_outbox_revision_positive CHECK (aggregate_revision > 0),
    CONSTRAINT ck_core_outbox_attempt_nonnegative CHECK (attempt_count >= 0),
    CONSTRAINT ck_core_outbox_status_valid CHECK (status IN ('pending', 'leased', 'delivered')),
    CONSTRAINT ck_core_outbox_lease_complete CHECK (status != 'leased' OR (lease_owner IS NOT NULL AND lease_until IS NOT NULL)),
    FOREIGN KEY(aggregate_id) REFERENCES core_aggregate_revisions (aggregate_id) ON DELETE RESTRICT
);

CREATE INDEX ix_core_outbox_ready ON core_outbox_events (status, available_at, created_at);

CREATE INDEX ix_core_outbox_lease ON core_outbox_events (status, lease_until);

CREATE TABLE core_outbox_consumer_receipts (
    consumer_name VARCHAR(128) NOT NULL,
    event_id VARCHAR(36) NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (consumer_name, event_id),
    FOREIGN KEY(event_id) REFERENCES core_outbox_events (event_id) ON DELETE RESTRICT
);

INSERT INTO alembic_version (version_num) VALUES ('20261014_0001') RETURNING alembic_version.version_num;

COMMIT;
