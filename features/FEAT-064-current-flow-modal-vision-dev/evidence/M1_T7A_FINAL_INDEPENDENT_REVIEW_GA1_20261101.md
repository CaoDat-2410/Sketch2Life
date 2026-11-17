# M1 and T7a final independent review — GOAL A1

**Review date:** 2026-11-01
**Disposition:** M1 ACCEPTED; T7a NEEDS_REVISION; GOAL A1 NOT ACCEPTED
**Branch / HEAD:** `feature/feat063-be-foundation` / `1e93bc3f3ac645cf4baecbbc09c73afe48719c92`

## Authority and scope

Reviewed the pinned V4 and Goal A1, approved M1 plan and fixture-compatibility addendum, approved T7a plan, implementation reports, current source and tests, and snapshots `GA1_M1_20261101T192254` and `GA1_T7A_20261101T195106`. The V4 SHA-256 is `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6`; Goal A1 SHA-256 is `90B546430E1E1E2E8B40078EBD7FF2CA108D0F785C054C06620F2EBBF6902949`. M1 plan/addendum and T7a plan hashes match their approvals.

This was a read-only source review. Tests, validators, PostgreSQL/Alembic, Modal, GPU, provider, and external network were not run. Reported test and validator results below are implementation evidence read from the pinned reports, not results rerun by this reviewer.

## M1 — ACCEPTED

No actionable finding remains in the approved M1 scope. Review covered:

- Append ordering: idempotent replay and stale-revision checks precede the capacity check; final correctness still relies on the existing revision CAS.
- Stroke upper bound and JSONB point sum: limits fail closed before rendering and use the owner-approved whole-canvas point count from the M1 compatibility addendum.
- Export validation: organization/session/canvas/profile and complete revision history are verified before source construction. Checkpoint/restore history remains rejected under the already approved T4 contract; checkpoint JSON is not rendered.
- Renderer semaphore/deadline, exact stored-PNG admission and provenance binding, plus rollback/deletion of artifacts created by a failed handoff.

The M1 snapshot has 12 manifest entries; ten still match current files. The only differences are the append-only approval and ledger, which have since gained later records. The implementation report records its focused unit and PostgreSQL checks and validators; the later T6 aggregate report records the offline suite, including the M1 module, as 648 passed / 4 skipped / 0 failed. These results were not rerun in this review.

## T7a — NEEDS_REVISION

### P2 — Receipt snapshot is not checked against the bound organization

At `backend/src/sketch2life/infrastructure/assistance/sql_repository.py:168-178`, `put_receipt()` validates `receipt.key.organization_id` against the repository, then stores the repository organization in the SQL row while serializing the entire `CommandReceipt` payload without checking `receipt.snapshot.facts.organization_id`.

The composite foreign key verifies that the referenced assistance ID exists in the row's organization, but it cannot verify the organization embedded in the serialized snapshot. If the same assistance ID exists in organizations A and B, a repository bound to A can accept a receipt keyed to A whose snapshot is the B request. `get_receipt()` then returns that B snapshot from A's scoped repository. The database key is composite by organization and assistance ID, so it does not prevent that ID collision across organizations.

This violates the repository's organization-scoping guarantee and can expose a foreign-organization request through a valid receipt lookup. Before T7a can be accepted, reject a receipt whose snapshot organization differs from the bound repository organization and add a regression test for the mismatched-snapshot case. No implementation or test change was made in this review.

## Snapshot and gate

- M1 snapshot: 12 manifest entries; ten match current files. The approval and ledger entries differ only because those append-only records advanced after the snapshot.
- T7a snapshot: 74 manifest entries; 72 match current files. The approval and ledger entries differ only because those append-only records advanced after the snapshot.
- The T6 final independent review already accepted T6. M1 is accepted here; T7a is not.
- GOAL A1 remains **NEEDS_REVISION** until the T7a finding is fixed and independently reviewed. Do not start A2 on this review result.

No source, test, approval, plan, or snapshot was changed. The review report and the append-only FEAT-064 ledger entry are the only files updated for this review. The index was empty; no stage, commit, or push occurred.
