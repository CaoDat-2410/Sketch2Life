# T7c — Server-issued run manifest, invocation ledger, and host witness

- Status: **BLOCKED before implementation**.
- Group: G3. Owner authorized the G2–G6 no-commit run under the goal prompt §E; no live/provider authority is implied.
- Parent: `plan/PLAN.md`, T7c; T0 contract freeze §6/§9, execution manifest O16.
- Database: no writes or fault injection in this blocker-only task.

## Inventory and blocker

The T0 proposal requires a server/operator-issued manifest pinning approval/plan, expiry, DB generation, host, scope, config and witness; a pre-existing `UNUSED` witness; exclusive consumption; then a durable invocation ledger commit before possible-send. Missing, unreadable, mismatched or uncertain witness/ledger state fails closed. A consumed witness with a missing ledger after restore is `UNKNOWN`, never inferred “not sent.”

The task depends on T7a durable invocation state and T7b’s transaction/fence integration boundary. O16 does not name the implementation files, ledger schema/migration revision or assigned writer. The T0 Windows witness text is only a proposal: the selected host directory, filesystem and durability operations have not been verified. No filesystem type or directory-flush behavior may be assumed. Implementing a marker file without proving the actual host/DB/cloud-sync separation and crash behavior would create a false one-call cap.

## Owner questions

1. Which exact server/worker/operator boundary issues the run manifest and binds it to the invocation/approval?
2. Which O16 files, schema owner, migration revision and writer are approved for the manifest/ledger?
3. Which local witness directory/filesystem is selected outside DB backups and cloud sync, and what Windows primitive/durability guarantee is accepted after fault tests?
4. Which throwaway host/DB identities and restore/fault matrix are approved for T12? No live UNUSED token may be consumed by T7c tests.

## Layers and acceptance

| Layer | Planned scope | Status |
|---|---|---|
| L1 contracts/domain | Manifest and invocation lifecycle states | BLOCKED by exact contract/path freeze |
| L2 application | Fail-closed run verification and status classification | BLOCKED by T7a/T7b and T6 guard contract |
| L3 persistence/migration | Durable ledger with single-parent migration/downgrade | BLOCKED by O16/T7a |
| L4 adapters | Windows witness consume/read/flush adapter | BLOCKED: host filesystem and primitive unverified |
| L5 HTTP | No new route in T7c | NOT RUN |
| L6 UI | DEFERRED-BY-OWNER | DEFERRED |
| L7 integration | Throwaway crash/race/restore fault matrix | BLOCKED by T7a/T7b and explicit test host/DB boundary |

## Allowlist and exclusions

Candidate B5.1 boundary only: `backend/src/sketch2life/infrastructure/assistance/**`, `backend/src/sketch2life/infrastructure/vision_analysis/**`, and a migration only if T7a approves a ledger table. For this blocker-only disposition, the actual write allowlist is only this plan, the G3 blocker report, the append-only FEAT-064 approval entry, and the goal ledger.

No witness was created/consumed, no fault injection was run, and no provider or database call was made.
