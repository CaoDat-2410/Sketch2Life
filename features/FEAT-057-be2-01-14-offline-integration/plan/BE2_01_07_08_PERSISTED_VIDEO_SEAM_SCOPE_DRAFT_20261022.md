# BE2-07 → BE2-01 → BE2-08 persisted VideoWorker seam

Date: 2026-10-22 (Asia/Saigon)
Status: `DRAFT / FOR OWNER REVIEW / NOT APPROVED FOR SOURCE CHANGES`
Worktree: FEAT-057 linked integration worktree (machine-specific path omitted)
Branch / HEAD: `feature/be2-backend-ai-integration / 1649b72978877d82b4d7662040ff3555dee0a3a7`

## 1. Purpose and authority boundary

Propose one offline BE2 seam for review: a real BE2-07 bundle is pinned to a real persisted BE2-01 job/run; the unchanged `WorkerDispatchEnvelope` is sent through the existing typed dispatcher to the real BE2-08 `VideoWorker`; BE2-08 admission verifies the persisted job, attempt and pin; and an adopted atomic lifecycle contract records the final job/run result and authoritative receipt.

This draft is a proposed contract and candidate file manifest only. It grants no permission to edit source/tests, does not adopt CR08-01 or the BE2-07 source fence, does not alter owning-card approvals/status/acceptance, and does not make the earlier 330-test run evidence for this seam. Any source implementation requires each owning card's independent contract adoption and exact supplemental approval.

## 2. Verified baseline

- The requested worktree, branch and HEAD match the values above. Before preparing this proposal, the worktree had 146 dirty paths and 0 staged paths; all pre-existing changes remain untouched. The proposal adds one new plan file, bringing the current count to 147 dirty paths and 0 staged paths.
- Existing offline JUnit evidence is 330 tests, 0 failures/errors/skips, SHA256 `4AAF9563B5CF3F1B4774BCCC29300A33E9B7B9CF46BD97E68F1C9087C5D43695`. It proves the recorded BE2-07 exact-export/media fixture and BE2-01 typed routing to a fake video target, not persisted job/run admission into the real `VideoWorker` or final receipt.
- `DispatchWorker` already forwards the unchanged envelope to a configured typed video target and fails closed for unsupported job types. The existing approved route manifest is limited to `backend/src/sketch2life/infrastructure/ai_jobs/worker.py`, `typed_dispatch.py`, and `backend/tests/unit/test_ai_job_video_dispatch.py`; this proposal does not add changes to those route files.
- The BE2-07 resolver performs exact bundle/source/pin checks, but its current source coordinator is process-local. There is no adopted durable source fence held through BE2-08 finalization.
- `VideoWorkerAdmission.begin` and `AtomicVideoFinalizer` are protocols. No concrete implementation binding them to the BE2-01-owned UoW/recovery entrypoint was found.
- FEAT-044 UoW Rev7, FEAT-050 BE2-08 Rev3 and FEAT-056 BE2-07 scope are drafts. D3 C1-A/C2-A remain design direction, not contract adoption or implementation approval. D4 completion-time `BUDGET_EXCEEDED` and the BE1-owned artifact descriptor/quarantine adoption are still separate gates.
- Existing cross-lane approvals are narrower than this candidate seam: FEAT-044's approved BE2-01 route addendum is pinned to `AD1BA2706655CD040ACBBBF508577F79A41F5D5B3EF57D1437DA4C7F7F185DBD`; FEAT-050's approved BE2-08 addendum is pinned to `6A195B6F3C9901621D268CF26B34AA217EECAFE66FA5922BD066149E6A9BC0B0`; and FEAT-056's approved BE2-07 addendum is pinned to `CA531682CCB0ABD12BB8B270F0258D9B3EBBCE4DBF917805FBC7A770BBF6EB24`. These approvals require an exact execution subset before edits, and explicitly leave CR08-01 / durable fence through finalization as gates. FEAT-044 UoW Rev7 (`BD119A05F72D311BAC299F3E940927DCE80D67DC1CD38EBE87B7D5ACC1B6EAE9`), FEAT-050 scope Rev3 (`66C614FF268E418F27FA4923FB7272A845F7BC7DA8BB225B8CD10032D364F801`) and FEAT-056 fence draft (`CA531682CCB0ABD12BB8B270F0258D9B3EBBCE4DBF917805FBC7A770BBF6EB24`) are candidate successors, not authority to edit their paths.

## 3. Proposed versioned contract direction

Proposed review label: `BE2-VIDEO-LIFECYCLE/1` (name/version are not adopted). Keep the dispatch envelope byte-for-byte/API compatible. Cross-feature behavior uses public typed contracts; no application-layer SQL connection, direct foreign-owner table access, or caller-supplied `is_current`/authorization boolean.

### 3.1 Create and dispatch

1. BE2-07 supplies a producer-owned exact identity binding organization/session, bundle ID/version/hash, editorial/context/audience revisions, and every pinned source ref/version/hash needed by the video request. The consumer cannot reconstruct a weaker identity from internal producer rows.
2. BE2-01 remains the only lifecycle transaction owner. Creating the video work persists the foundation job, video run, exact pin mapping, dispatch/outbox intent and their idempotency receipt atomically, or persists none. Dispatch publication happens only after that commit.
3. `WorkerDispatchEnvelope` remains unchanged and token-bearing only as currently defined. The receiver validates its capability and message against the persisted job, run, job type, current attempt and pin; envelope fields never override persisted truth.

### 3.2 Admission and processing

1. `VideoWorkerAdmission.begin(envelope)` is a real implementation over the adopted BE2-01 public lifecycle contract. It performs the authoritative eligibility/capability checks and commits the paired BE2-01/BE2-08 start (`S`) in the same UoW before the pipeline runs. A duplicate, settled, stale or invalid delivery does not start provider/render work. Ambiguous commit is resolved by authoritative lookup; it is never guessed to mean “not started.”
2. The real BE2-08 worker resolves the exact persisted BE2-07 pin and verifies the exported bundle hash and complete lineage before preparing media. A process-local mutex or an immediate re-read is not a durable held source fence.
3. A durable producer-currentness fence must cover the complete identity and invalidator set and remain valid through finalization. The proposed direction is a same-store, transaction-scoped BE2-07 participant enlisted by the BE2-01-owned finalization UoW. BE2-07 and BE2-08 must adopt the contract and prove both race winner orders. If a shared store/transaction cannot be established, record X01 as PARTIAL; do not claim the requested full seam.

### 3.3 Final result, receipt and replay

1. The adopted completion operation (`B`) commits the authoritative BE2-01 job state/result refs/completion receipt and BE2-08 run/artifact/receipt together in one BE2-01-owned UoW. The BE2-08 participant writes only its own rows. No success is returned for a split commit.
2. The receipt binds the exact persisted organization/job/attempt/pin/artifact and contract version, and distinguishes accepted, stale and rejected outcomes. Job state and video state are mapped explicitly; they are not required to be equal literals.
3. Duplicate completion returns the same authoritative receipt. Ambiguous commit is resolved through an authoritative receipt lookup. A changed payload under the same operation identity conflicts. A stale or invalid pin fails closed, cannot expose an artifact, and follows the adopted stale/rejection receipt semantics.
4. D3's selected C1-A/C2-A behavior remains the design input for paired state and stale handling, subject to owner adoption. This proposal does not choose the unresolved D4 completion-time `BUDGET_EXCEEDED` result, invent quarantine descriptors/reasons, or imply BE1 has adopted accepted-reference protection.

## 4. Proposed exact candidate file manifest

Paths below are the proposed source/test candidate set for this seam, not an edit grant. Owning-card manifests must be reduced/frozen against exact current hashes after the contract is adopted. If owner review requires an unlisted path (including schema/migration), stop and revise the manifest before edits. `NEW` identifies a proposed filename that does not exist in the current tree. Existing path presence does not imply approval.

| Owner | Candidate path | Proposed change and reason |
|---|---|---|
| BE2-01 / FEAT-044 | `backend/src/sketch2life/application/ports/ai_jobs.py` | Add/adjust the typed public UoW participant and persisted mapping contract; keep `WorkerDispatchEnvelope` unchanged. |
| BE2-01 / FEAT-044 | `backend/src/sketch2life/application/services/ai_jobs.py` | Enlist paired video lifecycle operations at create/start/completion and the reviewed paired terminal/recovery writers. |
| BE2-01 / FEAT-044 | `backend/src/sketch2life/infrastructure/ai_jobs/sql/repository.py` | Implement BE2-01-owned UoW enlistment, transaction-scoped participant, commit/rollback and authoritative recovery lookup. |
| BE2-01 / FEAT-044 | `backend/tests/integration/ai_jobs/test_sql_repository.py` | Extend real UoW rollback/commit and paired-row evidence. |
| BE2-01 / FEAT-044 | `backend/tests/integration/ai_jobs/test_completion_recovery.py` | Extend authoritative completion receipt and ambiguous-commit replay evidence. |
| BE2-01 / FEAT-044 | `backend/tests/integration/ai_jobs/test_dispatch_recovery.py` | Verify the persisted attempt is dispatched/admitted once without changing envelope semantics. |
| BE2-01 / FEAT-044 | `backend/tests/integration/ai_jobs/test_restart_recovery.py` | Verify persisted lifecycle/recovery behavior across worker restart boundaries. |
| BE2-08 / FEAT-050 | `backend/src/sketch2life/domain/knowledge_video/model.py` | Adopt paired state transitions, attempt binding at S, terminal stale/no-artifact rules. |
| BE2-08 / FEAT-050 | `backend/src/sketch2life/infrastructure/knowledge_video/codec.py` | Version and strictly decode the adopted persisted run/receipt representation. |
| BE2-08 / FEAT-050 | `backend/src/sketch2life/infrastructure/knowledge_video/sql.py` | Provide a video-row-only transaction participant, locked lookup and paired CAS; never open/commit the transaction. |
| BE2-08 / FEAT-050 | `backend/src/sketch2life/application/ports/knowledge_video.py` | Expose only the adopted submission/participant/lookup API. |
| BE2-08 / FEAT-050 | `backend/src/sketch2life/application/ports/knowledge_video_worker.py` | Version typed admission/finalization/receipt/recovery outcomes; preserve fail-closed semantics. |
| BE2-08 / FEAT-050 | `backend/src/sketch2life/application/knowledge_video_create.py` | Map the exact persisted BE2-07 pin and foundation job/run without caller-derived identity. |
| BE2-08 / FEAT-050 | `backend/src/sketch2life/application/knowledge_video_worker.py` | Consume committed admission, exact pin and authoritative finalization/replay receipt. |
| BE2-08 / FEAT-050 | `backend/src/sketch2life/contracts/schemas/knowledge_video.py` | Version only the adopted public receipt/projection; retain explicit state mapping. |
| BE2-08 / FEAT-050 | `backend/src/sketch2life/infrastructure/knowledge_video/foundation_lifecycle.py` (`NEW`) | Proposed infrastructure adapter implementing admission/finalizer through the BE2-01 public UoW contract; no direct cross-owner SQL. Filename and owner boundary require review. |
| BE2-08 / FEAT-050 | `backend/tests/unit/test_knowledge_video_domain.py` | Cover the adopted legal transition and attempt/pin invariants. |
| BE2-08 / FEAT-050 | `backend/tests/unit/test_knowledge_video_persistence.py` | Cover codec/participant validation and rejection behavior. |
| BE2-08 / FEAT-050 | `backend/tests/unit/test_knowledge_video_create.py` | Cover persisted creation mapping and idempotency contract. |
| BE2-08 / FEAT-050 | `backend/tests/unit/test_knowledge_video_worker.py` | Cover real worker behavior against the adopted public ports; no fake admission/finalizer in the end-to-end proof. |
| BE2-08 / FEAT-050 | `backend/tests/contract/test_knowledge_video_contract.py` | Pin the adopted versioned receipt/state projection. |
| BE2-07 / FEAT-056 | `backend/src/sketch2life/application/ports/knowledge_bundle.py` | Expose producer-owned exact identity and transaction-scoped currentness fence contract. |
| BE2-07 / FEAT-056 | `backend/src/sketch2life/application/services/knowledge_bundle.py` | Resolve exact currentness through the public producer contract and fail closed. |
| BE2-07 / FEAT-056 | `backend/src/sketch2life/infrastructure/knowledge_bundle/coordination.py` | Replace or constrain process-local coordination so it cannot be represented as durable fencing. |
| BE2-07 / FEAT-056 | `backend/src/sketch2life/infrastructure/knowledge_bundle/sql_source_fence.py` (`NEW`, conditional) | Candidate same-store source fence participant. Requires BE2-07/BE2-01/BE2-08 store and transaction adoption; if it requires schema/migration or a different owner, stop and revise this manifest. |
| BE2-07 / FEAT-056 | `backend/src/sketch2life/infrastructure/knowledge_bundle/fakes.py` | Keep test doubles explicitly test-only; do not use them for the durable-fence acceptance claim. |
| BE2-07 / FEAT-056 | `backend/tests/unit/test_knowledge_bundle_service.py` | Verify complete exact identity and fail-closed currentness API. |
| BE2-07 / FEAT-056 | `backend/tests/unit/test_knowledge_bundle_races.py` | Cover invalidation and stale/currentness ordering at the producer boundary. |
| BE2-07 / FEAT-056 | `backend/tests/integration/knowledge_bundle/test_source_fence.py` (`NEW`) | Verify the adopted durable fence and both race winner orders; requires a permitted real transactional store. |
| FEAT-057 composition | `backend/tests/integration/be2_cross_lane/test_persisted_video_worker_flow.py` (`NEW`) | One end-to-end test wiring the real BE2-07 service, persisted BE2-01 service/dispatch, concrete BE2-08 admission, real `VideoWorker`, exact pin and final receipt. Only queue transport, renderer/provider transport and unavailable external storage may be fake. |

### Explicit exclusions

- No changes to `WorkerDispatchEnvelope`, `worker.py`, `typed_dispatch.py`, route behavior, public HTTP handlers or provider fallback.
- No FEAT-057-owned fake UoW, admission, finalizer, or persisted repository used to claim full-flow success.
- No change to `backend/src/sketch2life/infrastructure/knowledge_video/tables.py`, any migration/schema, PostgreSQL setup, server, database, runtime, Modal, Lightning, real provider or external service under the current request.
- No BE1 source/phase work; no X05c/CR09-02, BE2-09/14, read-model feature, or unrelated lifecycle feature. BE1-owned artifact descriptor/quarantine/accepted-reference adoption remains a dependency only where the adopted stale/cleanup contract needs it.
- No stage, commit, push, merge, branch/worktree change, or edits to owning-card approval/status/acceptance records.

## 5. Acceptance criteria for a later approved implementation

| ID | Required evidence |
|---|---|
| S01 | BE2-07 creates the exact bundle identity; BE2-01 persists a job/run/pin with matching source hash and complete lineage, all-or-none. |
| S02 | Persisted dispatch uses the unchanged envelope; the real typed dispatcher reaches the real BE2-08 `VideoWorker`, never a provider fallback for this job type. |
| S03 | Real admission validates capability, job type, job/run identity, active attempt and persisted pin, then commits paired S before processing. Unknown, mismatched, duplicate or settled delivery does not render. |
| S04 | Real worker resolves the same BE2-07 bundle by persisted pin/hash and validates all lineage. A durable source fence is held through finalization; otherwise X01 remains PARTIAL. |
| S05 | Accepted completion commits job, video run, artifact reference and authoritative receipts atomically under the BE2-01-owned UoW. Read-after-commit returns the same receipt. |
| S06 | Duplicate and ambiguous completion recover the one authoritative winner; changed payload conflicts. Stale/invalid source is fail-closed and never exposes a final artifact. |
| S07 | Paired rollback is shown when either participant rejects; no split job/run, fabricated receipt or provider work before committed admission. |
| S08 | JUnit/log/hash and source snapshot are stored under FEAT-057 `evidence/`; independent diff/scope review passes. No card is marked complete from this evidence alone. |

## 6. Blocking gates and current execution constraint

1. **Owner adoption:** FEAT-044 must adopt the CR08-01 UoW/recovery and public mapping contract; FEAT-050 must adopt concrete admission/finalizer, lifecycle/state/receipt/codec/projection behavior; FEAT-056 and FEAT-050 must adopt the matching durable source-fence-through-finalization contract. The current Rev7/Rev3 documents are drafts. Existing cross-lane approvals cover only earlier, narrower addenda and do not adopt these successor contracts. Each owner must freeze and approve its exact reduced file/hash manifest in its own approval record.
2. **Open lifecycle outcome:** the FEAT-044/050 drafts still leave D4 completion-time `BUDGET_EXCEEDED` unresolved. This proposal does not select a result. The owning cards must settle or explicitly bound that case before approving the full lifecycle scope.
3. **BE1-owned cleanup dependency:** where stale/rejected outputs require quarantine or accepted-reference arbitration, obtain the BE1 owner contract/adoption. No BE1 implementation is included here.
4. **No-database constraint:** the requested final proof requires a real persisted UoW and a durable same-store source fence. The user's current execution boundary forbids database use. Under that boundary, a test cannot prove durable commit/rollback, restart recovery or held-fence race ordering without substituting a fake (which is expressly disallowed). Therefore this draft can be reviewed, but S01/S04/S05/S07 cannot be claimed PASS or fully implemented under the current no-database constraint. Do not introduce SQLite, PostgreSQL, an in-memory repository, or a fake UoW/finalizer silently. A later full-flow run needs an explicit change to the database restriction or an already approved persistence harness that demonstrates these exact durable properties without violating it.

Until these gates are resolved, report the seam `PARTIAL / BLOCKED`, keep X01 `PARTIAL` and X09-08 `NOT_IMPLEMENTED`, and keep the local BE1 handoff `NOT_SENT / NOT_READY_FOR_BE1_INTEGRATION`.

## 7. Review and approval sequence

1. Review this scope/contract proposal and the exact candidate paths. Any path or owner-boundary change creates a revised draft.
2. Obtain owner contract adoption and independent review in FEAT-044, FEAT-050 and FEAT-056; close D4 and any BE1 artifact dependency that the selected lifecycle requires.
3. Reduce each owner's candidate manifest, hash the reviewed source bytes and record matching supplemental approvals. A FEAT-057 review alone cannot approve owning-card source edits.
4. Resolve the no-database acceptance conflict before implementation/test work. If that restriction stays in force, preserve PARTIAL/BLOCKED and stop short of claiming the requested durable integration.
5. Only after all gates are met may the approved files be implemented and the acceptance evidence collected. This draft itself authorizes no source/test change or test run.
