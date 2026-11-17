# BE2-07 → BE2-01 → BE2-08 persisted VideoWorker seam — scope revision 2

Date: 2026-10-22 (Asia/Saigon)
Status: `DRAFT / CR08-01 ADOPTION AND CARD APPROVAL REQUIRED / NO SOURCE-TEST AUTHORITY`
Worktree: FEAT-057 linked integration worktree (machine-specific path omitted)
Branch / HEAD: `feature/be2-backend-ai-integration / 1649b72978877d82b4d7662040ff3555dee0a3a7`

This revision supersedes the 2026-10-22 initial seam-scope draft for review. The earlier draft is retained as history. This revision applies the owner's direction to keep one flow, allow only isolated local database verification, and track the durable source fence separately.

## 1. One-flow objective and authority

Proposed flow:

`real BE2-07 KnowledgeBundleService creates exact bundle`
→ `real BE2-01 persists job/run/pin and dispatch intent`
→ `existing DispatchWorker sends the unchanged WorkerDispatchEnvelope`
→ `real BE2-08 VideoWorker uses concrete admission to verify persisted job/attempt/pin`
→ `real BE2-08 worker reads that exact bundle and processes it`
→ `one adopted BE2-01-owned UoW records accepted job/run result and authoritative receipt`.

Only this eligible, accepted-result path and its duplicate/identity-failure safeguards are in scope. Existing BE2-07 producer and BE2-01 typed route are consumed as-is. No BE2-07 source change is proposed. The envelope is unchanged. The test may fake queue transport, renderer/provider transport, unavailable external storage, and synthetic fixture data; it must use the real BE2-01 persistence/UoW, real BE2-08 admission/finalizer and real `VideoWorker`.

Because BE2-14 is excluded, the test covers one synthetic eligible request using the existing FEAT-044 `FixtureEligibility` test fixture only; it makes no BE2-14 policy or capacity claim. If the accepted path needs a new BE2-14 behavior or the existing fixture cannot represent the eligible case, stop and return for a scope decision.

This is a proposed contract and file-level scope only. It does not adopt CR08-01 or grant permission to edit source/tests. No source, test, migration or schema change may start until the CR08-01 contract, exact owner-card manifests and their approval records are updated. If a required path is outside this manifest, stop and seek a revised scope before editing.

## 2. Proposed narrow CR08-01 contract for owner adoption

Proposed contract label: `BE2-VIDEO-LIFECYCLE/1` (not adopted). BE2-01 alone owns begin/commit/rollback of each lifecycle transaction. BE2-08 participates through a typed, transaction-bound contract and may write only BE2-08 rows. No application port exposes a SQL connection, no owner writes directly to another card's tables, and no test substitutes a fake BE2-01 UoW or BE2-08 admission/finalizer.

The adopted public contract must cover only these operations for this flow:

1. **Create (A):** persist the BE2-01 job, BE2-08 queued run, exact BE2-07 pin mapping, idempotency receipt and dispatch/outbox intent in one UoW, or persist none. Publish only after commit.
2. **Start (S):** validate the unchanged envelope's capability against persisted job type, job ID and active attempt; resolve the persisted run/pin; atomically commit the paired BE2-01/BE2-08 start before `VideoWorker` processes the bundle. A duplicate, mismatched or already-settled delivery does not render.
3. **Accept (B):** atomically commit the accepted BE2-01 job/result refs/completion receipt and BE2-08 run/artifact/receipt. A participant rejection rolls back the entire UoW. The authoritative receipt can be read after commit and used to recover duplicate or ambiguous completion without creating a second artifact.
4. **Identity failure:** a job/attempt/pin/hash mismatch fails closed, writes no final artifact and cannot be reported as successful. This is a mismatch check at the operation being tested; it does not claim that source validity stays fenced between resolution and finalization.

The contract explicitly does not add an envelope field, route, migration, table, column, BE2-14 policy behavior, timeout/retry/budget lifecycle, D4 completion-time budget result, BE2-09 projection/read model, or BE1 implementation. If A/S/B and receipts cannot fit the already-approved schemas, stop and return with the exact schema/path needed; this scope authorizes no schema expansion.

## 3. Local database test boundary

The owner permits database use only for later offline verification, after scope and approvals are updated:

- Use one dedicated, newly-created local PostgreSQL 17 database with a random `be2_xlane_...` name, loopback host only, synthetic IDs/content, and a test-only credential source. The test must refuse a non-loopback host, a non-dedicated database name, or any database/schema that already exists.
- Create only the database owned by that test run; apply only existing approved migrations/schema definitions, then drop only the database created by the fixture. Never connect to a shared, staging or production database. Do not log credentials or persist test secrets.
- No new migration/schema file or edit to existing table/schema definitions is in this scope. If existing schemas cannot support the paired A/S/B UoW, stop for a revised scope and approval.
- No provider, Modal, Lightning, HTTP server, deployed service or runtime is used. Queue, renderer/provider transport and unavailable external storage are the only infrastructure fakes; the BE2-01 and BE2-08 lifecycle implementations remain real.
- No database is provisioned or contacted while this document remains unapproved. The user's permission for a local test DB does not itself approve source/test files or CR08-01.

## 4. Exact proposed file-level manifest

This is the complete candidate set for the narrow accepted-result flow. The owning-card approval records must freeze this exact reduced list (and reviewed scope hash) before source/test edits. `NEW` marks a proposed file not present at the inspected baseline. All other listed files already exist. No FEAT-056 file is included; its durable fence is a separate gate.

| Owner | Candidate path | Proposed edit and reason |
|---|---|---|
| BE2-01 / FEAT-044 | `backend/src/sketch2life/application/ports/ai_jobs.py` | Add the typed public BE2-08 participant/lifecycle binding without changing `WorkerDispatchEnvelope`. |
| BE2-01 / FEAT-044 | `backend/src/sketch2life/application/services/ai_jobs.py` | Enlist BE2-08 at A/S/B through BE2-01-owned transactions and return/recover authoritative completion receipt. |
| BE2-01 / FEAT-044 | `backend/src/sketch2life/infrastructure/ai_jobs/sql/repository.py` | Provide transaction-bound participant enlistment using the existing connection/transaction; preserve rollback and authoritative lookup. |
| BE2-01 / FEAT-044 | `backend/tests/unit/test_ai_job_application.py` | Preserve application-level job lifecycle behavior at the changed public boundary. |
| BE2-01 / FEAT-044 | `backend/tests/unit/test_ai_job_lifecycle.py` | Cover the selected paired start/accept invariants. |
| BE2-01 / FEAT-044 | `backend/tests/integration/ai_jobs/test_sql_repository.py` | Verify real PostgreSQL transaction/rollback behavior with the participant. |
| BE2-01 / FEAT-044 | `backend/tests/integration/ai_jobs/test_completion_recovery.py` | Verify duplicate/ambiguous accepted-result receipt replay. |
| BE2-08 / FEAT-050 | `backend/src/sketch2life/domain/knowledge_video/model.py` | Bind the accepted path's queued → running → succeeded run transition and immutable attempt/pin/artifact identity. |
| BE2-08 / FEAT-050 | `backend/src/sketch2life/infrastructure/knowledge_video/codec.py` | Strictly encode/decode the adopted run/receipt representation using the existing storage shape. |
| BE2-08 / FEAT-050 | `backend/src/sketch2life/infrastructure/knowledge_video/sql.py` | Implement a video-row-only participant and locked read/CAS inside the caller's BE2-01 UoW. |
| BE2-08 / FEAT-050 | `backend/src/sketch2life/application/ports/knowledge_video.py` | Expose the typed transaction participant/submission lookup contract. |
| BE2-08 / FEAT-050 | `backend/src/sketch2life/application/ports/knowledge_video_worker.py` | Define adopted real admission, atomic finalizer and authoritative receipt lookup outcomes. |
| BE2-08 / FEAT-050 | `backend/src/sketch2life/application/knowledge_video_create.py` | Bind the real exact pin to persisted job/run and idempotent create result. |
| BE2-08 / FEAT-050 | `backend/src/sketch2life/application/knowledge_video_worker.py` | Connect real admission, exact bundle processing, finalization and replay lookup. |
| BE2-08 / FEAT-050 | `backend/src/sketch2life/contracts/schemas/knowledge_video.py` | Define only the adopted versioned A/S/B result/receipt mapping; no BE2-09 projection. |
| BE2-08 / FEAT-050 | `backend/src/sketch2life/infrastructure/knowledge_video/foundation_lifecycle.py` (`NEW`) | Concrete adapter implementing BE2-08 admission/finalizer against the BE2-01 public contract, with no cross-owner SQL. |
| BE2-08 / FEAT-050 | `backend/tests/unit/test_knowledge_video_domain.py` | Verify selected run transitions and immutable lineage. |
| BE2-08 / FEAT-050 | `backend/tests/unit/test_knowledge_video_persistence.py` | Verify strict persisted run/receipt codec and participant guard behavior. |
| BE2-08 / FEAT-050 | `backend/tests/unit/test_knowledge_video_create.py` | Verify exact pin and idempotent submission mapping. |
| BE2-08 / FEAT-050 | `backend/tests/unit/test_knowledge_video_worker.py` | Verify real worker orchestration and mismatch/duplicate outcomes; isolated unit cases may use port fakes. |
| BE2-08 / FEAT-050 | `backend/tests/contract/test_knowledge_video_contract.py` | Pin the adopted versioned lifecycle receipt. |
| FEAT-057 composition | `backend/tests/integration/be2_cross_lane/test_persisted_video_worker_flow.py` (`NEW`) | Compose real BE2-07 producer, BE2-01 persisted service/dispatch and BE2-08 admission/worker/finalizer against the dedicated local PostgreSQL database. Assert unchanged envelope and final authoritative receipt. |

Read-only dependencies: `backend/src/sketch2life/infrastructure/ai_jobs/worker.py`, `typed_dispatch.py`, `backend/src/sketch2life/infrastructure/ai_jobs/sql/owner_fence_fixture.py` (`FixtureEligibility` only), `backend/tests/unit/test_ai_job_video_dispatch.py`, and the existing BE2-07 service/resolver files. No edits to them are in this manifest.

## 5. Acceptance evidence for a later approved implementation

| ID | Required result |
|---|---|
| P01 | The real BE2-07 service creates a synthetic bundle; exact exported hash and source/pin lineage are used by the real BE2-08 consumer. |
| P02 | Real BE2-01 service/UoW persists job/run/pin and dispatch intent all-or-none in the dedicated local database. |
| P03 | Existing typed dispatch forwards the same `WorkerDispatchEnvelope` to the real `VideoWorker`; the real admission validates it against persisted job/attempt/pin and commits S before work. |
| P04 | The real worker processes the exact persisted bundle pin and commits accepted BE2-01 job/result/receipt plus BE2-08 run/artifact/receipt atomically. A new connection reads back the same identities and receipt. |
| P05 | Duplicate delivery/completion returns one authoritative result; changed or mismatched job/attempt/pin/hash fails closed and cannot write a final artifact. |
| P06 | Injected failure in either A/S/B participant proves rollback leaves no split owner state or fabricated success receipt. |
| P07 | Test evidence records the dedicated database isolation checks, command, JUnit/log and hash under FEAT-057 `evidence/`; no external runtime/provider is used. |

The existing 330/330 JUnit remains bounded prior evidence only. It is not evidence for P01–P07.

## 6. Separate durable source-fence gate

No source fence implementation or BE2-07 file appears in this manifest. Exact resolution during this test proves that the worker reads the persisted pin's bundle; it does not prove invalidation cannot race with finalization. Track the held durable producer-currentness fence separately with BE2-07/BE2-08 owner adoption and its own exact manifest, transaction/race evidence, and approval. Until the fence is proven held through finalization, keep X01 `PARTIAL`; this flow cannot close X01 or claim durable-currentness protection.

## 7. Explicit exclusions

- BE2-09, BE2-14, D4, X05c/CR09-02 and any BE1 implementation/phase.
- Durable BE2-07 source fence implementation; it is a separate gate as above.
- Any change to the dispatch envelope, existing route files, HTTP/router, provider fallback, schemas/tables/migrations, or card acceptance/status.
- Budget/policy implementation, stale finalization/quarantine, retries/timeouts/cancellation, read-model projection and external artifact lifecycle.
- Database outside one test-owned loopback PostgreSQL 17 database; shared, staging and production databases are forbidden.
- Stage, commit, push, merge, branch/worktree change, Modal, Lightning, provider and runtime.

## 8. Missing contract and approvals — stop before code

CR08-01 is not adopted. The current FEAT-044 cross-lane approval authorizes only the typed dispatch route and freezes `worker.py`, `typed_dispatch.py`, and `test_ai_job_video_dispatch.py`. The current FEAT-050 supplemental approval leaves CR08-01/owner boundaries as gates and requires an exact execution subset before editing. The FEAT-057 approval permits composition only against already-adopted public candidate contracts and says an unadopted edge remains `NOT_IMPLEMENTED`.

Before any source/test edit, the owner must explicitly adopt or revise the proposed A/S/B participant/UoW/receipt contract in §2 and update the official approval records with the reviewed Rev2 scope hash and exact per-card path lists: FEAT-044 `approvals/PHASE_B_TASK_APPROVAL.md`, FEAT-050 `approvals/TASK_APPROVAL.md`, and FEAT-057 `approvals/TASK_APPROVAL.md`. If any owning-card approval or CR08-01 remains absent, stop at that gate. This proposal records the owner's local-database test restriction but is not itself CR08-01 adoption or source/test approval.
