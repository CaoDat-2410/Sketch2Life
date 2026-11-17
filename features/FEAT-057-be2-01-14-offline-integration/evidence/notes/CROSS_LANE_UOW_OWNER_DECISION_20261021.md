# Owner decision needed before the shared-UoW scope can be finalized

- Status: AWAITING_OWNER_DECISION
- Related draft: features/FEAT-044-be2-ai-job-foundation/plan/CROSS_LANE_FOUNDATION_UOW_SCOPE_REV2_DRAFT_20261021.md
- Draft SHA256: 39B0FD5958D2C298460F7605A7F73E8BDC7BC9D269B6399822FD2A2EAAC4DDC4

The current owner direction covers submission and successful finalization as separate foundation-owned commits. The independent review found that start/admission and failure lifecycle transitions also mutate job/run state and need an explicit consistency model.

## Decision D1 — start and failure lifecycle

Which model should the scope use?

- **A — Extend the foundation UoW to paired lifecycle transitions (recommended).** BE2-01 owns the UoW for start, retry, failure, cancel, timeout, and terminal transitions whenever both job and BE2-08 run are authoritative. BE2-08 participates only in its own rows. Quarantine/cleanup intent that must survive a rolled-back completion is persisted through a separately recoverable boundary.
- **B — Make BE2-08 run lifecycle a projection.** The foundation job is the only lifecycle authority; BE2-08 run state is derived/reconciled and cannot independently claim a conflicting start or terminal state. This requires an explicit recovery/projection contract and may require a separate BE2-08 scope change.
- **C — Specify another model.** Name the authoritative record and transaction owner for start, retry, fail, cancel, timeout, late result, and quarantine/cleanup intent.

Reply with A, B, or C plus any changes. No implementation approval is requested by this ballot.

## Conditions that remain regardless of D1

- Current BE2-07 scope has no durable shared-store fence. X01 remains PARTIAL unless a separately approved source-fence scope proves the required same-store serialization; a last read is insufficient.
- Keep WorkerDispatchEnvelope unchanged. The persisted job_id-to-run lookup and exact request_ref-to-source-pin rule must be proven; missing linkage fails closed and may require a versioned CR.
- The BE2-08 read-only artifact model is a separate draft requiring its own review and exact owner-approved fields/access semantics.
- BE2-14 budget unit/limit remain owner-supplied; reservation expiry/renewal needs a versioned CR.
- X05d stays BLOCKED; X05c/CR09-02 stays OPEN. No tests, provider, database, runtime, Modal, or Lightning are authorized by this ballot.
