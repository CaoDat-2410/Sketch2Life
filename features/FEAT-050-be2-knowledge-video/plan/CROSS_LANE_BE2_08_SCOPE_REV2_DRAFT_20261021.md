# BE2-08 cross-lane lifecycle participant scope — revision 2 draft

- Status: DRAFT / OWNER_D1_D2_D3_DESIGN_RECORDED / AWAITING_INDEPENDENT_REVIEW_AND_SUPPLEMENTAL_APPROVAL.
- Prepared: 2026-10-21 (Asia/Saigon).
- Owner: FEAT-050 / BE2-08; foundation UoW owner: FEAT-044 / BE2-01.
- Supersedes for review only: CROSS_LANE_BE2_08_SCOPE_DRAFT_20261021.md.
- Historical parent SHA256: 6A195B6F3C9901621D268CF26B34AA217EECAFE66FA5922BD066149E6A9BC0B0.
- Owner D3 record: features/FEAT-057-be2-01-14-offline-integration/evidence/notes/CROSS_LANE_UOW_OWNER_DECISION_D3_20261021.md.
- Source snapshot: features/FEAT-057-be2-01-14-offline-integration/evidence/metrics/CROSS_LANE_UOW_SOURCE_HASHES_REV4_20261021.json.
- Source manifest SHA256: 2EAA11FCA7B510CA738D34ECED9EFD164C7734FCA8E6AD4792257F03AA68591F.
- Candidate branch/HEAD: feature/be2-backend-ai-integration / 1649b72978877d82b4d7662040ff3555dee0a3a7. The worktree is dirty; per-file source hashes identify the reviewed bytes.

This successor expands the historical A/B-only proposal to the full paired lifecycle. It records design requirements for independently reviewed versioned contracts; it is not contract adoption, implementation approval, card acceptance, source/test/schema permission, or runtime evidence. The historical scope, frozen PLAN.md, artifact-read supplement, and official approvals remain unchanged. S/F still require their own supplemental approval after independent review and exact per-card manifests.

## 1. Ownership and fixed design constraints

BE2-01 alone opens, commits, and rolls back A, S, B-accepted, B-stale, F, F-reject, and incident UoWs. BE2-08 receives a transaction-scoped participant capability and writes only its own video rows and owned submission receipt. It cannot begin/commit/rollback, query foreign tables directly, publish a foundation job, choose foundation retry exhaustion, or turn a broker delivery into proof of committed start.

FEAT-057 owns the later composition adapter and composed evidence. Its adapter is not a BE2-08-owned foundation writer. BE2-07 owns producer source/currentness; BE2-14 owns separately adopted eligibility, execution, and budget contracts. BE1/storage adoption remains pending for authoritative artifact descriptors and accepted-reference protection.

WorkerDispatchEnvelope stays unchanged. Persisted foundation job -> unique organization/job video run -> exact VideoPin mapping must be proved through public owner APIs. The participant needs an adopted locked get-by-job accessor; it does not exist in the pinned VideoRunRows. Request identity, input hash, target/purpose/subject fields, retry-policy identity, and null session handling cannot be inferred from video_id or pin_digest.

Admission must compare persisted job.job_type, envelope message type, and configured typed video route under an adopted mapping. VideoRun has no job_type field. Unknown or mismatched type fails closed before S; the envelope alone is not authority.

## 2. D1/D2/D3 design directions

- D1: foundation owns every paired lifecycle UoW; video is a non-committing participant. Reconciler, dispatcher cancellation, retry, timeout, dispatch-loss and notice paths cannot change a job while bypassing its paired run. Business rejection uses a separate F-reject commit with durable foundation intents, not a rollback of B.
- D2: a foundation SUCCEEDED result with ResultDisposition.STALE maps to a distinct video-owned terminal STALE state. The stale run has no artifact and is not ready for review. Foundation JobState is unchanged. Only S binds VideoRun.attempt_id; retry clears the old id. Attempt number remains foundation-owned.
- D3 C1-A: while resource/budget-deferred, both job and run remain QUEUED with no new budget video state or foundation JobState. For a due, otherwise eligible retry, foundation performs its normal requeue exactly once to the new attempt and establishes the deferral atomically; the paired run becomes QUEUED and clears attempt_id under D2. The older proposal to hold budget-deferred work in FAILED_RETRYABLE is superseded. A not-yet-due or ineligible retry is not falsely labeled as a queued budget hold.
- D3 C2-A: B-stale commits the foundation SUCCEEDED/STALE outcome and receipt, the paired terminal stale run, and a durable keep-private/quarantine intent in the same foundation-owned commit. Intents contain only refs proved owned by an authoritative descriptor under the adopted exact job/attempt/organization rules. Fixed reason/event-id semantics and BE1 accepted-reference protection still require adoption; caller-provided refs or hashes are insufficient.

These settle design direction only. Unit, amount, limit, expiry, renewal, phase mapping, resource proof, public APIs, and schema-specific persistence remain separate CR gates. No value is guessed. No provider executes while a required gate is unknown or unavailable.

## 3. Candidate boundary inventory

Every row below is a required contract behavior, not a claim that the current source implements it. External source/media preparation, generation, staging, and validation occur outside these short database UoWs.

| Boundary | Foundation authority | BE2-08 participation | Recovery and effects |
|---|---|---|---|
| A — submit | Create/replay job, initial attempt, semantic/command receipt, dispatch outbox and audit intent. | Insert/replay one QUEUED run and owned submission receipt under the same organization/job identity; attempt_id=None. Compare both semantic indexes, exact command identity and adopted retry-policy mapping. | Any split winner or participant conflict rolls back the whole UoW. Fresh authoritative replay proves both owners' winner; ambiguity is pending, never permission to generate. Creation lease is a separate logical guard outside A. |
| S — admitted start | Capability/current request, eligibility, execution and reservation checks precede committed start. | Lock paired run and CAS QUEUED -> RUNNING with the exact active foundation attempt_id. S alone binds it. A true eligibility denial pairs cancellation; resource deferral leaves both QUEUED under the adopted deferral record. | Lost ack rereads the exact pair in a fresh UoW; same committed attempt can prove duplicate recovery. Missing/mismatched state fails closed; provider cannot run before authoritative admission. |
| B-accepted | Commit SUCCEEDED/ACCEPTED, exact result refs, authoritative completion receipt and required audit/outbox effects. | CAS matching RUNNING run to SUCCEEDED with exact FinalArtifact and READY_FOR_REVIEW. | Compare authoritative receipt, exact persisted artifact and independently reconstructed completion key; retain stage on ambiguous result. Late attempt cannot overwrite winner. |
| B-stale | Commit SUCCEEDED/STALE, result refs and authoritative STALE receipt plus D3 durable owned-ref keep-private intent. | CAS matching RUNNING run to video-owned terminal STALE with artifact=None and no READY_FOR_REVIEW. | This is authoritative successful finalization, not F-reject. Receipt/run/intent share one commit. Independently verify non-accepted key from adopted durable stage inputs; no accepted artifact is available in the run for comparison. Intent acknowledgement is not physical cleanup. |
| F — fail/cancel/timeout/retry/dispatch loss | Foundation selects and commits the existing lifecycle outcome, including retryable/exhausted choice and the next attempt. | Mirror committed lifecycle by paired CAS. Started failure checks current attempt; pre-start dispatch loss pairs queued run without binding its id. Retry clears old id. Eligible due retry followed by resource hold atomically requeues both to QUEUED exactly once. | Whole-UoW rollback on error, then fresh paired lookup. Reconciler and notice paths have the same participant obligation. No retry/exhaustion or automatic resource resume is chosen by video. |
| F-reject — business/policy rejection | Separate foundation-owned reject UoW rechecks current facts under locks and persists permitted lifecycle plus durable owned quarantine/cleanup intent. | Change only its paired run when the foundation winner changes. Intent-only handling of an already terminal winner preserves run and artifact. | Business rejection does not use B rollback. Reject identity/reason is durable and idempotent; unavailable pre-intent crash recovery remains blocked. A changed canonical input for the same operation conflicts. |
| I — incident only | Existing foundation audit-incident authority; no job/run lifecycle mutation or fabricated authoritative completion-slot receipt. | No video row mutation. | A temporary/invalid-state response may still have durable audit persistence. The incident is not accepted output, B-stale, or proof that quarantine happened. |

Completion receipt disposition alone does not identify the boundary: an ACCEPTED receipt may acknowledge an authoritative failure claim. The adopted typed outcome must distinguish job state, job result_disposition, receipt disposition and video state. SUCCEEDED/ACCEPTED maps to accepted artifact; SUCCEEDED/STALE maps to terminal stale without artifact; FAILED_RETRYABLE/FAILED_EXHAUSTED from a failure claim maps to that failure state even when its receipt is ACCEPTED. Guard-only responses preserve the original winner.

## 4. Complete video-state and persistence CR

The versioned BE2-08 CR must cover all of the following together:

1. Define a video-owned lifecycle type and terminal set including STALE without adding STALE to foundation JobState. Preserve previously persisted states through an explicit compatibility decision.
2. Add legal fail, block, timeout, retry and stale transitions to the existing start/finalize/cancel model. Enforce QUEUED attempt_id=None, S-only binding, retry clearing, exact revision/attempt checks, and terminal immutability. Stale has no artifact and no ready state.
3. Change codec _Run.generation_state from foundation JobState to the adopted video type under an explicit persisted-format/version contract. Unknown or corrupt payloads remain errors; do not silently coerce stale to succeeded or failed.
4. Change VideoRunRows.save's foundation TERMINAL_STATES dependency to the adopted video-owned terminal classification, including STALE. Retain immutable lineage/artifact checks and compare-and-swap revision semantics.
5. Add the public locked organization/job lookup and minimal transaction-bound participant methods. No application protocol exposes raw SQLAlchemy connections. Participant capability does not expose foreign-row or transaction-control operations.
6. Adopt a versioned projection contract: current KnowledgeVideoView.generation_state and VideoAttemptView.state reject stale, and the existing contract test expects it to be rejected. Foundation attempt state and video lifecycle are distinct axes; a new stale video value must not be inserted into the old public literal or invented as foundation attempt state.
7. Replace validate_submission_view's blind equality of latest foundation attempt state and video generation state with an explicit adopted job-state/disposition/video-state relation, retaining exact attempt identity and provenance checks.
8. Resolve VideoFinalizationReceipt and _receipt behavior. Today non-ACCEPTED requires video_run=None and ACCEPTED validates a succeeded run. Either an adopted adapter verifies the persisted stale/failure pair while preserving a compatible external shape or a versioned typed outcome exposes it. A failure claim's ACCEPTED receipt must never enter success-artifact validation.
9. Require independent completion-key computation from authenticated persisted accepted or private-stage inputs; caller input is compared and cannot simply be echoed. A fingerprint cannot reconstruct lost original claim/media inputs. Missing durable input leaves recovery pending/blocked.

State/codec changes alone do not authorize a migration. Existing run_json storage does not prove compatibility for a new lifecycle. Any additional durable journal, deferral row, column, constraint or migration requires a schema-specific scope and separately approved new migration; no existing migration may be rewritten under this draft.

## 5. Budget deferral and cleanup participant limits

Foundation owns the durable execution-deferral record, generation/recovery epoch, dispatch/outbox handling and resume authority. BE2-08 introduces no budget state. Its sole lifecycle effect is the exact paired QUEUED invariant and normal retry requeue/id clearing under D3. Repeated resource waiting must not consume attempts, dispatch-loss recovery allowance, or create duplicate retry attempts. Lifetime publication history is preserved.

Late outbox claims, acknowledgements and watchdog callbacks cannot unpark an obsolete generation or exhaust a resource-held job. True consent/session/source revocation may still cause authoritative paired cancellation. Resume is an explicitly authorized admission event with exact current identity and reservation proof, not a new automatic scheduler. Cancellation/terminal closure invalidates deferral/resume generation in the same foundation-owned paired UoW.

BE2-14 accounting remains a separate transaction and is not invoked under job/run locks. A joint BE2-01/14 contract must define exact reservation handoff, phase mapping, concurrency, lost-ack and terminal/deferral semantics; BE2-08 consumes that adopted result. No budget unit/limit or expiry/renewal is defined here. Unknown execution or resource authority remains pending and invokes no provider.

B-stale D3 cleanup uses foundation's existing intent/outbox primitives only after verified authoritative ownership descriptors and adopted fixed reason/event-id semantics exist. BE2-08 owns retained private-stage recovery input and journal integration; it does not claim actual deletion or bypass accepted-reference protection. Accepted artifact references must remain protected atomically at the storage owner; BE1 adoption is still pending. Best-effort _quarantine exceptions do not prove durable cleanup.

## 6. Locking, complete fences, and participant errors

The shared foundation-owned protocol locks job then paired video run, then the complete deduplicated canonical union of required foundation/participant fence keys once through commit. All relevant job/run pairs precede the fence hold. Late-discovered keys require restart; no participant adds a lower key or opens an independent UoW. A's pre-insert source-fence hold remains a separately reviewed creation exception.

Notice discovery and foundation writer changes belong to BE2-01's joint scope, not this card's file list. That scope must retain notice atomicity/idempotency/notice_atomic_max/COMPLETE semantics and recheck tenant, cancellable state, notice predicate and paired run after locking. Video supplies only its paired lookup/CAS. A fixture's sorted fence hold or process-local coordinator does not establish durable BE2-07 currentness. If there is no adopted same-store source fence through finalization, X01 remains PARTIAL.

Every participant error must escape the enclosing UoW so foundation rolls it back before recovery reads. The top-level worker may return pending after rollback; it must not swallow a participant failure inside a still-live UoW.

| Participant error | Required handling after whole-UoW rollback |
|---|---|
| VIDEO_WRITE_CONFLICT | Translate to typed whole-transaction conflict; fresh authoritative lookup resolves exact winner/replay versus conflict. Never query inside an aborted SQL transaction. |
| VIDEO_STALE_RUN | Fresh locked pair proves exact prior winner versus stale/conflicting mutation; no automatic unique-conflict classification. |
| VIDEO_IMMUTABLE_LINEAGE, VIDEO_IMMUTABLE_ARTIFACT, VIDEO_TERMINAL_RUN | Fail closed as integrity/conflicting winner unless independent authoritative lookup proves exact replay. |
| VIDEO_INVALID_TRANSITION, VIDEO_ATTEMPT_NOT_CURRENT | Fresh pair may prove duplicate or obsolete attempt; incompatible state fails closed. No inferred retry or rerender. |
| VIDEO_STORAGE_CORRUPT | Integrity failure; never replay from corrupt payload. |
| VIDEO_RECEIPT_MISMATCH, VIDEO_INVALID_INITIAL_RUN, input/tenant/transaction errors | Fail closed; exception alone never establishes replay. |
| Infrastructure/driver error | Fresh authoritative commit lookup; pending if authority unavailable. Response loss never authorizes rerender. |

## 7. Read-only artifact model candidate correction

CROSS_LANE_BE2_08_ARTIFACT_READ_MODEL_SCOPE_DRAFT_20261021.md is preserved as a historical exact-hash input. The following are explicit successor requirements for its AR01/AR05, not adopted implementation behavior:

- AR01: a terminal STALE run has artifact=None, so it cannot satisfy finalized-artifact lookup or return a playable/finalized artifact. Uncommitted, rolled-back, missing or incomplete output is likewise excluded.
- AR05: distinguish terminal stale generation without artifact from an earlier accepted artifact whose source eligibility later changed. Historical accepted lineage is not current-use authorization. Exact historical/superseded/quarantined visibility and response semantics remain pending owning-card/consumer decisions.
- A status response exposing stale requires the versioned projection above; it does not create an artifact or playback grant.
- Public field set, access/tenant/session checks, lookup key/version cursor and read-after-commit remain pending. So does receipt provenance: choose an adopted opaque receipt ref persisted at finalization or a BE2-01 read-only receipt lookup composed by FEAT-057. Do not read foundation tables directly or silently add a receipt field to FinalArtifact/VideoRun/codec without its CR and worker-equality impact.

BE2-09 consumes only the public versioned read model and never mutates BE2-08 rows. X05d remains BLOCKED; X05c/CR09-02 remains OPEN. Read-model implementation paths/tests remain a separate supplemental manifest.

## 8. Candidate owned implementation paths

These are candidate paths to freeze with exact hashes after independent contract/scope review; this draft grants no edit permission.

| Candidate path | Required scope |
|---|---|
| backend/src/sketch2life/domain/knowledge_video/model.py | Video state type, legal lifecycle transitions, queued attempt-id invariant and terminal rules. |
| backend/src/sketch2life/infrastructure/knowledge_video/codec.py | Explicit versioned persisted state format and strict corruption handling. |
| backend/src/sketch2life/infrastructure/knowledge_video/sql.py | Public locked get-by-job participant, paired CAS, video-owned terminal set and transaction-bound recovery behavior. |
| backend/src/sketch2life/application/ports/knowledge_video.py | Adopted submission/participant/lookup contract only. |
| backend/src/sketch2life/application/ports/knowledge_video_worker.py | Admission/finalization typed outcomes, recovery and cleanup handoff under CR. |
| backend/src/sketch2life/application/knowledge_video_create.py | Exact submission/projection mapping and replay checks. |
| backend/src/sketch2life/application/knowledge_video_worker.py | Committed S, typed completion/receipt validation, retained-stage recovery and adopted phase gates. |
| backend/src/sketch2life/contracts/schemas/knowledge_video.py | Only under a versioned public projection CR; preserve old-contract compatibility and distinguish foundation attempt from video state. |

Candidate existing owned tests:

- backend/tests/unit/test_knowledge_video_domain.py.
- backend/tests/unit/test_knowledge_video_persistence.py.
- backend/tests/unit/test_knowledge_video_create.py.
- backend/tests/unit/test_knowledge_video_worker.py.
- backend/tests/contract/test_knowledge_video_contract.py.
- backend/tests/integration/knowledge_video/test_run_rows_sql.py: source/collection and later authorized SQL conformance scope only; no database execution is authorized here.

Any new participant/contract-test filename must be frozen in the independently reviewed manifest before code. infrastructure/knowledge_video/tables.py and new migration paths are excluded until schema-specific scope/approval exists. application/ports/knowledge_video_media.py and staging/storage adapters are excluded unless a reviewed recovery-contract supplement identifies the exact changes. Existing media formula sources are review inputs, not implicit edit scope.

Foundation service/domain/SQL tables, BE2-07 producer/fence implementation, BE2-09 review rows, BE2-14 policy/accounting storage, FEAT-057 composition adapter/tests, live HTTP/router/configuration and provider/runtime wiring are outside this card manifest. Their owners require matching reviewed scopes and approvals.

## 9. Proposed acceptance and remaining approval gates

All cases below are planned evidence, not executed or passed results.

| ID | Required evidence |
|---|---|
| V201 | A creates both owners or none; replay/conflicting body/split winner/lost ack compare authoritative identity and adopted policy mapping. |
| V202 | S alone binds the run attempt id after persisted typed route/capability checks; no provider on unknown, duplicate, mismatch, resource hold or uncommitted admission. |
| V203 | B-accepted atomically stores exact artifact plus foundation receipt; duplicate/late result has one winner and never overwrites accepted lineage. |
| V204 | B-stale atomically stores SUCCEEDED/STALE receipt, stale run without artifact/ready state and descriptor-proven owned-ref intent; intent failure rolls back all three. Fixed event/reason and accepted-reference protection are adopted before claiming conformance. |
| V205 | All failure/timeout/dispatch-loss/notice/retry writers pair run/job; retry id clears; due eligible retry plus resource hold yields exactly one new foundation attempt and both QUEUED with no budget state. |
| V206 | F-reject is a separate commit with durable identity/intent; I incident preserves winner without fabricating a completion receipt. Missing durable recovery input stays pending/blocked. |
| V207 | Model, codec, SQL terminal guards and versioned public projection agree on stale/queued/id invariants; old format/schema compatibility is explicit and corrupt state never replays. |
| V208 | Participant errors escape UoW; whole rollback precedes recovery; negative tests prove no transaction lifecycle or foreign-row capability. |
| V209 | Complete fence union is held once after required job/run locks; notice recheck/atomicity is verified in owner/composition evidence. No fixture proof upgrades X01. |
| V210 | Read-model AR01/AR05 exclude terminal stale without artifact and distinguish historical accepted lineage from current eligibility; receipt-provenance choice and consumer agreement remain explicit gates. |
| V211 | Owned offline regression and separately approved composition run on a pinned snapshot; no runtime/provider/PostgreSQL fence/card-acceptance claim is inferred. |

Before source implementation: independently review this successor with the paired foundation/slice/policy successors; adopt the exact public lifecycle, mapping, retry-policy, descriptor/fence, deferral, receipt/recovery and projection CRs; settle the specified schema gates; freeze per-card source/test manifests; record matching supplemental approvals including S/F in official owning-card records. The prior A/B scope/approval cannot authorize these new lifecycle/state/schema paths.

Current gates remain X01 PARTIAL, X05d BLOCKED, X05c/CR09-02 OPEN, X09-08 NOT_IMPLEMENTED. Budget unit/limit are unprovided. Modal, Lightning, provider, server, database and runtime remain deferred. This document records no test run, stage, commit, push, merge, acceptance or card completion.
