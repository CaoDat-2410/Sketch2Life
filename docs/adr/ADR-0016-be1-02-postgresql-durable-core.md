# ADR-0016: PostgreSQL durable core adapter for BE1-02

- Date: 2026-10-14 (Asia/Saigon).
- Status: ACCEPTED FOR FEAT-046 / BE1-02 ONLY.
- Owner: Sketch2Life project owner by direct instruction to continue with BE1-02.
- Refines: ADR-0003, ADR-0005, ADR-0014.
- Feature approval: `features/FEAT-046-be1-durable-core-adapters/approvals/TASK_APPROVAL.md`.

## Context

BE1-01 established framework-independent core policies and ports. BE1-02 requires durable core records, migrations, atomic revision/idempotency/audit/outbox writes, and restart-safe recovery. ADR-0003 accepted PostgreSQL/SQLAlchemy/Alembic as foundation scaffolding; ADR-0014 retained them as reuse candidates and explicitly said the new product still needed adapters. The repository already declares SQLAlchemy 2.x, Alembic, and psycopg 3, and its local Compose file uses PostgreSQL 17. The user instructed implementation of the next BE1 task after BE1-01.

## Decision

1. Use PostgreSQL 17 as the authoritative relational store for the FEAT-046 core adapter. Use SQLAlchemy 2.x, psycopg 3, and Alembic, already declared in `backend/pyproject.toml`.
2. Keep aggregate revisions, immutable canvas operation metadata, idempotency receipts, checkpoint metadata, asset metadata/lineage, append-only audit entries, outbox events, and consumer receipts in the same relational transaction boundary where required.
3. Use a database-backed outbox with resumable at-least-once dispatch. Event identity and consumer receipts make local consumer effects idempotent. Redis/RQ may be considered later as delivery accelerators but cannot become authoritative state.
4. Store opaque asset/source references and hashes only. Do not select or call S3-compatible storage, and do not put media bytes in PostgreSQL in this feature.
5. Load database URLs and credentials at runtime. No real secret, account, child data, or `.env` value is committed.

## Scope and non-decisions

This is a feature-scoped adapter choice for BE1-02. It does not freeze the complete product stack, cloud/deployment topology, queue, object store, realtime transport, identity provider wiring, or multi-school launch. Any change to the relational source of truth or addition of object-byte persistence requires a separately reviewed ADR/feature plan.

## Consequences

- CAS, operation records, idempotency receipts, audit, and outbox publication can commit atomically against one PostgreSQL transaction.
- A restart resumes from persisted database state and outbox rows; in-memory state is not authoritative.
- External delivery remains at-least-once. A remote side effect cannot be made exactly-once by a local database transaction, so handlers must be idempotent or provide their own durable receipt.
- SQL migrations require forward and restore/downgrade planning; no deployment or live database provisioning is authorized by this ADR.

## Evidence

- Repository dependencies: `backend/pyproject.toml`.
- Local service baseline: `compose.yaml` PostgreSQL 17 service (its placeholder credentials are not production credentials).
- Task scope and acceptance: `features/FEAT-040-four-person-delivery-plan/artifacts/TEAM_TASK_BREAKDOWN.md`, BE1-02.
- Owner instruction and exact implementation scope: FEAT-046 plan and approval record.
