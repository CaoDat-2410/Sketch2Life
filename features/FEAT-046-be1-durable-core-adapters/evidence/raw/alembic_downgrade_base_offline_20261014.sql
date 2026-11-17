BEGIN;

-- Running downgrade 20261014_0001 ->

DROP TABLE core_outbox_consumer_receipts;

DROP INDEX ix_core_outbox_lease;

DROP INDEX ix_core_outbox_ready;

DROP TABLE core_outbox_events;

DROP INDEX ix_core_audit_resource_created;

DROP INDEX ix_core_audit_org_created;

DROP TABLE core_audit_entries;

DROP INDEX ix_core_asset_organization;

DROP TABLE core_asset_metadata;

DROP INDEX ix_core_checkpoint_canvas_latest;

DROP TABLE core_canvas_checkpoints;

DROP TABLE core_idempotency_receipts;

DROP INDEX ix_core_operation_canvas_epoch_revision;

DROP TABLE core_canvas_operations;

DROP INDEX ix_core_aggregate_revisions_organization_id;

DROP TABLE core_aggregate_revisions;

DELETE FROM alembic_version WHERE alembic_version.version_num = '20261014_0001';

COMMIT;
