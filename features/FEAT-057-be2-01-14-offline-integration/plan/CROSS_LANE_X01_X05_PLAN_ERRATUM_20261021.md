# FEAT-057 X01/X05 slice plan — review erratum 1

- Status: DRAFT / CHANGES_REQUIRED_REVIEWED / OWNER_SCOPE_DECISIONS_PENDING
- Applies to: CROSS_LANE_X01_X05_SLICE_PLAN_DRAFT_20261021.md, revision 4
- Parent SHA256: 6AF69E07E7FC51BD6AAA992A703FBE97AC2BC8E588FEC9F8735FBF74E88C6601
- Prepared: 2026-10-21 (Asia/Saigon)
- Branch/HEAD observed: feature/be2-backend-ai-integration / 1649b72978877d82b4d7662040ff3555dee0a3a7
- Source file hashes: features/FEAT-057-be2-01-14-offline-integration/evidence/metrics/CROSS_LANE_UOW_SOURCE_HASHES_20261021.json
  SHA256 88368265E8EE262F7DA6DEC23F3DAB6C749F482016EC79AA69F40B186DD5B92F

This erratum preserves revision 4 byte-for-byte and overrides only the clauses below. It records the independent review supplied on 2026-10-21, verdict CHANGES_REQUIRED. It is a planning correction, not implementation approval, contract adoption, card acceptance, or runtime evidence. The worktree source was dirty; the listed file hashes, not HEAD alone, identify the reviewed bytes.

## Corrections to revision 4

### G2 — job to run and source-pin mapping

The G0 owner direction is not an adopted mapping. The current dispatch envelope carries job and attempt identifiers and request_ref; it does not carry a run ID or source pin. The candidate persisted lookup is foundation job_id to the BE2-08 run row keyed by organization and job_id. The draft must define and test how the run's persisted pin corresponds to the foundation request_ref fields. Do not assume input_hash equals pin_digest or that request_id is a video ID.

If the persisted records cannot prove one exact organization/session, request, attempt, run, source bundle/version/hash, audience/context and idempotency identity, fail closed and keep X09-08 NOT_IMPLEMENTED. A missing field requires a versioned contract change approved by its owner. Keep WorkerDispatchEnvelope unchanged unless that separate CR is approved.

### G3 — held source fence and X01 result

A finalizer read or revalidation is not a held fence. A complete fence requires all currentness inputs used by BE2-07 to be inventoried, including bundle head/version, basis/context, audience, policy reference, catalog claims, and source record identity/version/hash. Each input must map to an owner, persisted fence key, and invalidation writer.

The candidate mechanism is admissible only if finalization and every relevant invalidator use the same PostgreSQL database and transactional rows. The finalizer must acquire FOR SHARE locks for the complete fence set before its final CAS and hold them through commit; invalidators must take FOR UPDATE on the same rows or CAS the same epoch. Lock order for job, run, fence and creation lease must be deterministic and documented. Lock timeout, deadlock, unknown source, or unavailable owner data fails closed or leaves the operation pending.

Two-session SQL evidence must test both winners: invalidation first makes finalization reject with no accepted artifact; finalization first holds the source rows until commit and invalidation proceeds only afterward. This boundary proves ordering at commit only; later invalidation and playback/current-use are still separate X05d/X02 concerns.

The current BE2-07 source and approved scope do not provide this shared SQL fence: resolve_exact opens its own transaction, BE2-07 has no SQL persistence in this scope, and the approved addendum excludes a real cross-service lock/schema. Therefore X01 is PARTIAL by default. Do not implement a last-read substitute or report X01 PASS. A changed BE2-07 scope, participating data-owner approvals and an adopted same-store mechanism are prerequisites; if they cannot be obtained, retain PARTIAL.

### Transaction lifecycle is not yet fully scoped

Revision 4's two owner-directed commits cover submission and successful finalization around external generation. They do not define start, failure, cancellation, timeout, retry, or durable quarantine/cleanup intent. Run state mirrors job state, and VideoRun.start records attempt identity, so these are correctness boundaries rather than incidental details.

| Boundary | Candidate responsibility | State |
|---|---|---|
| A — submission | BE2-01 opens/owns the UoW; BE2-08 writes its run/receipt rows as participant. Job, run, dispatch/outbox and receipt must not split. | Owner-directed; exact CR08-01 remains open. |
| S — start/admission | Job attempt and run start/attempt identity must either change atomically under the foundation UoW, or the owner must adopt a model where run state is derived and not separately authoritative. | Pending owner disposition. |
| B — successful finalization | BE2-01 owns the UoW; BE2-08 participates; completion, artifact and receipt share the commit, subject to the source-fence gate above. | Owner-directed; exact recovery/winner rules remain open. |
| F — fail/cancel/timeout/retry/quarantine | Specify paired job/run CAS, retry attempt winner, late result behavior and durable cleanup/quarantine intent. An intent that must survive a rolled-back completion cannot be written only inside that rolled-back transaction. | Pending owner disposition and CR08-01. |

Recommended direction for S/F: use foundation-owned UoWs for every authoritative mutation that changes both job and run; persist cleanup intent in a separately committed/recoverable boundary when completion rolls back. This recommendation is not adopted. Do not approve implementation until the owner selects this or records a different explicit model.

### Composition ownership and conflict recovery

BE2-01 owns the foundation UoW provider and transaction-scoped enlistment API. BE2-08 owns VideoRunRows and video state transitions. FEAT-057 owns cross-lane composition adapters/tests under its integration scope. Keep SQLAlchemy connection details in infrastructure; do not add them to an application protocol. Candidate adapter path: backend/src/sketch2life/infrastructure/cross_lane/knowledge_video.py; it requires a reviewed FEAT-057 manifest before implementation.

The lock order across foundation job, source fences, video run and any resolver creation lease must be named and shared by all writers. A PostgreSQL unique conflict aborts the transaction: roll back the whole UoW, then perform authoritative replay lookup in a new transaction. Do not replay in the failed transaction. Define whether the current creation lease participates in the same UoW or is a separately acquired/released guard; do not call the latter atomic.

### Read model and policy boundary

The read-only finalized-artifact model is a BE2-08-owned supplemental scope, not a BE2-01 UoW acceptance row. BE2-09 consumes it but cannot write BE2-08 state. The BE2-08 owner must separately adopt its exact fields, organization/session/principal visibility, read-after-commit behavior, immutable artifact identity, and stale/superseded behavior before CR09-01 can proceed.

BE2-14's current accounting ledger opens its own transaction, and Reservation has no expiry field. No atomicity with Boundary A/B, expiry, or renewal may be claimed. Keep eligibility, execution authorization, and budget/concurrency separate. Budget unit/limit and reservation timing/settlement/recovery stay pending; any test values must be explicitly marked synthetic and cannot enable a provider.

### Required evidence and scope control

Before any implementation approval, the revised scope must name exact owned files and tests for A/S/B/F, run replay in a new transaction after unique conflict, lost-ack, rollback, cancellation, retry, late result, and quarantine/cleanup recovery. Unit/fake tests are protocol evidence only. PostgreSQL two-session fence tests are required to claim durable serialization and remain NOT_RUN until separately authorized and run; SQLite or a process-local coordinator cannot substitute.

Update the FEAT-057 scope index and each affected card's supplement/approval after the owner resolves the pending S/F decision and the durable fence feasibility. Keep all existing approvals and accepted card records unchanged. X01 remains PARTIAL by default; X05d BLOCKED; X05c/CR09-02 OPEN; X09-08 NOT_IMPLEMENTED until persisted composition is proved. No Modal, Lightning, provider, server, database or runtime work is authorized here.

## Approval state

This erratum and its companion foundation UoW scope revision are drafts for another independent review. They do not modify revision 4, existing card scope approvals, TASK_APPROVAL records, source, tests, schema, migration, card status, acceptance or publication authority.
