# T7a — Minimal durable assistance and analysis state

- Status: **BLOCKED before implementation**.
- Group: G3. Owner authorized this no-commit goal run under the goal prompt §E; this plan records the unresolved T0/O16 gate.
- Parent: `plan/PLAN.md`, T7a; T0 method inventory; execution manifest O07/O15/O16.
- Database: only the owner-approved isolated loopback `*_be1_acceptance` database after exact migration scope is frozen. No database operation is run by this blocker-only task.

## Inventory and blocker

The T0 method inventory identifies selected durable assistance methods (request insert/read/CAS, semantic dedupe, idempotency receipts, transition events, pending reads and selected policy fencing) and selected analysis methods (attempt reconciliation, immutable head/observation/provider-result writes and reads). It also explicitly marks caches, corrections, notices, and Sketch intent as out of this pilot path unless separately selected; unavailable selected methods must not silently no-op.

Manifest O16 still says the selected repositories and migration path are `NEEDS_OWNER`: exact file, schema, migration revision, database boundary and writer must be named and approved before creation. No single schema owner is frozen. Choosing an Alembic branch, schema, revision identifier, table shape or writer would invent an ownership decision. T6 is also a prerequisite for the selected runtime lifecycle where it shares files; T6 is currently blocked by its explicit deadline/guard contract gate.

## Owner questions

1. Who is the single schema/migration owner for the pilot assistance and analysis state?
2. Which exact migration branch/parent and revision should hold the selected state, and which existing database schema owns it?
3. Which exact repository/table files and methods are in the selected durable subset, including whether `add_event`, `list_requests`, `publish_request_fence`, and `decision_epoch` are required now or remain fail-closed?
4. Who is the assigned writer for the O16 schema/repository paths?

## Layers and acceptance

| Layer | Planned scope | Status |
|---|---|---|
| L1 contracts/domain | Keep current assistance/analysis records and method contracts | NOT RUN |
| L2 application | Selected lifecycle consumers of durable methods | BLOCKED by T6/selected-method disposition |
| L3 persistence/migration | Durable repositories, single-parent migration, downgrade/backfill, PG test | BLOCKED: O16 owner/schema/path unresolved |
| L4 adapters | Runtime repository adapters | BLOCKED by L3 |
| L5 HTTP | No new route in T7a | NOT RUN |
| L6 UI | DEFERRED-BY-OWNER | DEFERRED |
| L7 integration | Restart/retention/rollback checks on isolated PostgreSQL | BLOCKED by L3 and exact DB scope |

## Allowlist and exclusions

Candidate new-path boundary from B5.1 only: `backend/src/sketch2life/infrastructure/assistance/**`, `backend/src/sketch2life/infrastructure/vision_analysis/**`, and one approved migration under `backend/alembic/versions/`. Potential integration test: `backend/tests/integration/test_be2_pilot_durability_postgres.py`. For this blocker-only disposition, the actual write allowlist is only this plan, the G3 blocker report, the append-only FEAT-064 approval entry, and the goal ledger.

No schema, migration, repository, or test was created/run. No Alembic command or DB write was run.
