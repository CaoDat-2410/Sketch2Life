# BE1-02 — Durable core adapters, migrations, and transaction/outbox

- Status: APPROVED
- Plan revision: 1
- Implementation status: NOT_STARTED
- Created: 2026-10-14 (Asia/Saigon)
- Owner request: “implement tiếp đi”, after FEAT-045 completion identified BE1-02 as the next BE1 task.
- Allocation: P2 / BE1 core, per ADR-0015 and FEAT-040.

## Goal

Implement durable relational adapters for the FEAT-045 core boundary, with atomic aggregate revision, canvas operation, idempotency receipt, audit and outbox writes. Provide migrations and a recoverable outbox dispatch boundary without making caches or queues authoritative.

## Authorities

- `features/FEAT-040-four-person-delivery-plan/artifacts/TEAM_TASK_BREAKDOWN.md`, BE1-02.
- `features/FEAT-045-be1-core-domain-foundation/plan/PLAN.md` and approved BE1-01 boundary.
- `docs/adr/ADR-0003-tech-stack-pending-discovery.md` and `ADR-0005-auth-release-and-ai-provider-strategy.md`.
- `docs/adr/ADR-0014-collaborative-learning-scope-replacement.md`, which leaves detailed runtime adapters proposed.
- New scoped `docs/adr/ADR-0016-be1-02-postgresql-durable-core.md`.
- Canonical Master SRS v3.1, especially B19.3, B19.8, B21, and B22.3.
- Direct owner continuation instruction in this conversation, 2026-10-14 (Asia/Saigon).

## Scope

1. Use PostgreSQL 17 for BE1-02 relational source-of-truth records, SQLAlchemy 2.x for adapters, and Alembic for schema evolution, as the task-scoped choice recorded in ADR-0016. This does not freeze the complete product stack.
2. Persist core aggregate revision, canvas operation metadata, idempotency receipt, checkpoint metadata, asset metadata/lineage references, append-only audit entries, outbox events, and consumer processing receipts.
3. Implement one unit-of-work path for a canvas mutation: compare-and-swap revision and atomically commit operation, receipt, audit, and outbox event. A failed transaction cannot return durable acceptance.
4. Implement restart-safe outbox claiming/retry and an idempotent consumer receipt boundary. Keep delivery at-least-once; downstream handlers must use event identity to avoid duplicate local side effects.
5. Add forward and restore/downgrade migration steps with no real or seeded child data. Keep installation/configuration through runtime environment only; no secret values in repository files.
6. Preserve asset bytes behind opaque storage references. This feature persists metadata and lineage only; it does not select or call an S3-compatible provider.

## Explicit boundaries

- No change to domain/product rules, live authentication, HTTP routes, mobile contracts, worker/provider integration, Redis/RQ delivery, object-byte uploads, retention execution, or BE1-03 through BE1-16.
- PostgreSQL choice applies to this BE1-02 core adapter only. It is not a multi-school launch decision or full-stack freeze.
- No Firebase Storage, Firestore, Realtime Database, real child data, accounts, credentials, or committed `.env` files.
- No claim of production readiness or measured pilot capacity.

## Acceptance criteria

- AC-01: SQLAlchemy repositories map versioned FEAT-045 core records without leaking ORM types into domain/application code.
- AC-02: Alembic migrations create the required core tables and indexes, preserve opaque source/asset references, and document a supported upgrade plus restore/downgrade path.
- AC-03: A core canvas write uses one database transaction for revision CAS, immutable operation, idempotency receipt, scoped audit entry, and outbox event.
- AC-04: A stale revision, duplicate key with changed fingerprint, or database exception cannot increment revision or create a partial operation/audit/outbox record.
- AC-05: Reopening a new adapter/process against the same database preserves committed operation, receipt, audit, checkpoint metadata, and outbox state.
- AC-06: Outbox delivery can resume after restart; duplicate event delivery is recognized by event ID and does not repeat an idempotent local consumer side effect.
- AC-07: Audit and adapter logs exclude child names, tokens, credentials, raw media, and full operation payloads; fixtures use synthetic identifiers only.
- AC-08: Domain remains framework-independent; infrastructure implements inward-facing ports. PostgreSQL is authoritative; cache/pub-sub is not.
- AC-09: Evidence records plan/ADR decision, migration map, adapter verification results or remaining verification gate, and all limitations inside this feature.

## Steps

1. Record the bounded database/adaptor decision in ADR-0016; map BE1-02 records and invariants to tables and ports.
2. Define SQLAlchemy models, session/unit-of-work, and repository adapters under infrastructure.
3. Extend the mutation port contract and implement atomic CAS + operation/receipt/audit/outbox persistence.
4. Add checkpoint/asset metadata lineage records and idempotent outbox dispatch/consumer receipt handling.
5. Add Alembic environment and forward/restore migration; use synthetic-only configuration.
6. Review privacy, transaction failure paths, dependency direction, and evidence; update feature records.

## Risks and mitigations

- B21/B22 schemas are still proposed. Persist only the approved FEAT-045 bounded metadata, and retain versioned refs/status without claiming the entire logical model is adopted.
- PostgreSQL availability can block adapter integration evidence. Keep DB URL runtime-only and record any unavailable environment honestly; never substitute an in-memory pass for durable evidence.
- Outbox external delivery cannot guarantee exactly-once effects. Use at-least-once delivery plus consumer receipts and require side-effect idempotency.
- Shared-canvas deletion, retention classes, provider copies, and object-store lifecycle remain unresolved and belong to later approved work.

## Verification and evidence plan

- Verify SQLAlchemy mapping and Alembic migration shape; where a PostgreSQL service is available, demonstrate transaction failure, stale CAS, restart persistence, and outbox duplicate delivery using synthetic fixtures.
- Record exact commands, environment, outputs, and limits in this feature's `evidence/` folder.
- Run `python tools/validate_repository_security.py` before any commit/push only.

Implementation is allowed only for revision 1 and this exact bounded scope, as recorded in `approvals/TASK_APPROVAL.md`.
