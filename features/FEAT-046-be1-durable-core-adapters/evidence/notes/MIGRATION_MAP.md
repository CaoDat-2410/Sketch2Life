# FEAT-046 core migration map

Migration: `backend/alembic/versions/20261014_0001_core_persistence.py` (`20261014_0001`).

| Table | Purpose | Integrity boundary |
|---|---|---|
| `core_aggregate_revisions` | Organization-scoped authoritative aggregate revision | Positive revision; aggregate ID primary key |
| `core_canvas_operations` | Immutable accepted operation metadata and turn/contributor attribution | FK to aggregate; unique canvas/epoch/result revision; positive epoch/revision; fingerprint length |
| `core_idempotency_receipts` | Organization-scoped request fingerprint and original operation/revision receipt | Composite organization/scope/key key; FK to operation; one receipt per operation |
| `core_canvas_checkpoints` | Checkpoint metadata and opaque external storage reference | FK to aggregate and through-operation; unique canvas/epoch/revision; checksum length |
| `core_asset_metadata` | Versioned hash, media type, and source/derivative lineage refs | Asset/version key; hash length; no media bytes |
| `core_audit_entries` | Append-oriented scoped action/resource/decision record | Organization/resource indexes; no request payload or token field |
| `core_outbox_events` | Same-transaction event for later at-least-once processing | FK to aggregate; revision/attempt checks; ready/lease indexes |
| `core_outbox_consumer_receipts` | Dedup key for local transactional consumer effects | Consumer/event composite key; FK to outbox event |

`PostgresCoreStore.commit_canvas_mutation` advances the revision with a conditional SQL update, then inserts operation, receipt, audit, and outbox rows in the same SQLAlchemy transaction. A failed CAS returns without inserting dependent rows; an integrity error rolls the transaction back and returns no acceptance. Other database exceptions propagate, so the application cannot return an accepted result.

Revision and idempotency receipt reads require the organization ID. Receipt identity is persisted as `(organization_id, scope, key)` so a reused scope/key in a different organization cannot return another organization's prior result.

`PostgresOutbox.claim_ready` uses row locks with `SKIP LOCKED` and lease expiry. `process_local_once` writes the consumer receipt, invokes a callback using the same SQLAlchemy session, and marks delivery in one transaction. Callbacks must keep effects inside that session; remote side effects need their own idempotency/receipt contract. A crashed lease can be reclaimed after expiry.

The migration is forward-only in ordinary rollout. Its downgrade removes this feature's tables, so restore from a verified backup before any destructive rollback. No deployment, database provisioning, real data, or provider connection is part of this feature.
