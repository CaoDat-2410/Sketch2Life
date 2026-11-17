# Cross-lane foundation-owned UoW for BE2-01 / BE2-07 / BE2-08 — scope revision 4 draft

- Status: DRAFT / CHANGES_REQUIRED_ADDRESSED / READY_FOR_INDEPENDENT_REREVIEW
- Prepared: 2026-10-21 (Asia/Saigon)
- Foundation transaction owner: BE2-01 / FEAT-044
- Video-row participant: BE2-08 / FEAT-050
- Source-currentness dependency: BE2-07 / FEAT-056, only under a separately adopted durable fence
- Supersedes for review only: CROSS_LANE_FOUNDATION_UOW_SCOPE_REV3_DRAFT_20261021.md
- Parent SHA256: 507EF55787A36EAE2E75E1BBACD8EBDD8DA8A5ED68DB190974289D88C7666C56
- Owner decision D1 SHA256: 3EECF89A488F7B2539AF41BE5CEF830D4C2509D6E93D478F624DF46B4F32A16D
- Claude rereview report SHA256: 0507A53D569B34ACF9EB44549D6BE794851335F3DBB88FD89E48D17E4AA649F0
- Source manifest revision 2 SHA256: 01160A4876ABB97CC33AC17108ADAE6F95E876DB86A24DF84B9832EC2B4F74FC
- Candidate branch/HEAD: feature/be2-backend-ai-integration / 1649b72978877d82b4d7662040ff3555dee0a3a7; worktree is dirty and source identity is the per-file manifest, not HEAD alone.

This draft addresses the independent Claude rereview verdict CHANGES_REQUIRED and the owner's selected direction A. It remains a documentation/scope candidate. It is not an adopted cross-card contract, implementation approval, card acceptance, or runtime evidence. S and F still require independent review and separate supplemental approvals in the affected card records before implementation. Existing approved card scopes and approval records are not amended here. No production source, test, schema, migration, card status, or acceptance change is authorized.

## Owner direction and fixed limits

1. BE2-01 owns and opens the Unit of Work for A, S, B and F transitions. BE2-08 is a transaction participant that may mutate only BE2-08-owned video rows. It cannot begin, commit, or roll back the enclosing transaction.
2. BE2-01 is the only lifecycle writer for a foundation job. Reconciler and outbox-dispatcher paths that change a job and its paired run must use the BE2-01 orchestration/UoW with the BE2-08 participant. No job-only update may leave the paired run behind.
3. Retry, timeout and cancellation reconciliation are F transitions under the same ownership rule. The start route S is called by the worker admission path; reconcilers and dispatchers are not S callers.
4. A business rejection is committed through a separate BE2-01-owned reject UoW using the existing foundation quarantine-intent writer/outbox path. The intent is not preserved by rollback. Rollback of B is only for infrastructure errors and requires an explicit idempotent recovery path.
5. The common row-lock order is foundation job → paired BE2-08 video run → all required source-fence rows in stable canonical-key order. Multi-job operations process job/run pairs in stable job-key order. Every invalidator and transition writer that participates in a held fence must be compatible with this order.
6. Keep WorkerDispatchEnvelope unchanged. Resolve job → run → source-pin identity from authoritative persisted records; fail closed if the relation cannot be proved.
7. BE2-08 owns a separate read-only artifact model for BE2-09. It must not read foundation tables directly or let BE2-09 write BE2-08 rows.
8. BE2-14 eligibility, worker/provider execution authorization, and budget/concurrency are distinct gates. The owner has not supplied a budget unit or limit. Reservation expiry/renewal requires a versioned CR.
9. Keep X01 PARTIAL; X05d BLOCKED; X05c/CR09-02 OPEN; X09-08 NOT_IMPLEMENTED until its persisted composition contract is adopted and proved. Modal, Lightning, provider, server, database, and runtime remain outside this offline scope.

## Source facts pinned for this review

The source manifest revision 2 pins all 14 files in the prior manifest plus four files used to check this rereview. Hashes identify a dirty source snapshot; they do not imply that the files are committed, approved, or mutually integrated.

- Foundation JobState persists the existing values queued, running, succeeded, failed_retryable, failed_exhausted, blocked_unsafe, and cancelled. ResultDisposition is a separate axis with accepted, stale, and rejected; do not invent a REJECTED JobState.
- BE2-08 VideoRun uses the existing JobState values but its current domain methods implement start, finalize, and cancel only. Fail, timeout, and retry transitions are absent. VideoRun.start records attempt_id; the initial A-created run is queued without an attempt_id.
- The BE2-08 SQL RUN row is unique by organization/job_id. VideoRunRows currently looks up by video_id or by session/pin_digest; it has no get-by-job locked accessor. The artifact is in run_json; there is no separate immutable artifact table. The separate VIDEO receipt table is the submission/idempotency receipt, not a finalization receipt.
- Foundation completion receipts are keyed by job_id and attempt_id and store receipt_id, fingerprint, disposition, reason, revision and time. They do not store the BE2-08 completion_key. The adapter must not claim that the completion_key is persisted. A candidate recovery query by organization/job/attempt must reconcile that foundation receipt with the exact artifact in the locked video run; if the required identity cannot be recovered unambiguously, fail closed or prepare a versioned CR. Do not add a column/table in this scope.
- Foundation and video submission deduplication are separate: foundation SemanticRequestKey and BE2-08 find_semantic(session_id, pin_digest). They must be reconciled by explicit field checks. No request ID, input hash, pin digest, video ID, or run ID is interchangeable by assumption.
- Foundation transaction code holds owner fences through its connection when a production OwnerFencePort is supplied. The repository currently has no production binding for that port; the existing hold operation follows caller order rather than sorting keys. This does not establish a BE2-07 source fence.
- The current BE2-07 resolver resolves exact bundle/version/hash in its own transaction and checks bundle head/version, basis/context, audience, policy reference, catalog claims, and source records. Its approved scope has no SQL store or same-store held fence.
- BE2-08 VideoPin also carries policy epoch, kill/rights/encoding/content profile, retry policy, model profile and library asset identity; finalizer candidates include eligibility and artifact-descriptor fences. Their owner, persisted lock key, and invalidation writers must be inventoried rather than inferred.
- Creation lease wraps BE2-08 submission outside the foundation UoW. It is a separate guard, not an enlisted atomic row.
- Outbox publish occurs outside its database transaction. A logical delivery lease may remain active during publish; this is not the same as holding a SQL row lock.
- VideoRunRows maps SQL integrity failures to VIDEO_WRITE_CONFLICT. Foundation retry logic catches UniqueConflict. The composition adapter must translate the participant conflict into whole-UoW rollback and replay in a new transaction.
- BE2-14 accounting uses a separate transaction. Reservation currently has no expiry field.

These facts are limited to the exact source hashes in the manifest. They are not PostgreSQL conformance evidence or contract adoption.

## Lifecycle state mapping

Use only the existing foundation JobState values. BE2-10 owns retry policy/exhaustion semantics; BE2-08 owns how the resulting state is represented in its video row. The exact cross-card mapping below is a candidate gate, not an adopted BE2-08 domain contract.

| Trigger/result | Existing foundation outcome | Candidate video-run outcome | Owner/gate |
|---|---|---|---|
| Worker start admitted | queued → running | queued → running; bind the same active attempt_id | BE2-01 S API plus BE2-08 participant; capability and eligibility must be checked before provider invocation. |
| Start denied because current eligibility is false | queued → cancelled with the authoritative reason | queued → cancelled | Must commit as paired S denial; no provider call. |
| Retryable provider failure or retryable timeout | running → failed_retryable | running → failed_retryable | BE2-10 determines retryability/backoff; BE2-08 participant mirrors the decided state. |
| Scheduled retry with a new attempt | failed_retryable → queued with new attempt_id/number | failed_retryable → queued and bind the same new attempt_id | Paired F CAS; BE2-10 owns retry eligibility, BE2-08 owns its row transition. |
| Exhausted or non-retryable failure, including dispatch loss after publish bound | → failed_exhausted | → failed_exhausted only after the BE2-10/BE2-08 mapping and terminal meaning are confirmed | OPEN card-owner/CR gate: the foundation service says exhausted disposition is BE2-10-owned; this scope does not assign that policy to BE2-08. |
| Teacher/owner cancellation or eligibility-driven cancellation | cancellable state → cancelled | matching run state → cancelled | Paired F CAS. |
| Unsafe moderation rejection | queued/running → blocked_unsafe | matching run state → blocked_unsafe; output remains unexposed | Paired reject commit plus durable foundation quarantine intent. |
| Malformed output treated as non-retryable failure | → failed_exhausted | → failed_exhausted only after the exhausted mapping gate above | Paired reject/F commit; do not invent a rejected state. |
| Completion disposition stale | Foundation may be succeeded with ResultDisposition.STALE | No accepted/playable artifact may be inferred; exact video terminal/review/cleanup result is unresolved | Must be specified in CR08-01 and BE2-08 supplement before approval. Do not collapse stale into BLOCKED_UNSAFE or FAILED_EXHAUSTED. |
| Temporary/non-authoritative verdict | No authoritative job transition | No video lifecycle transition | Record pending/recovery only; no accepted artifact and no provider rerun based on an unknown receipt. |

## Writer-to-boundary coverage

Every writer that changes foundation lifecycle state and has a paired video run must use the listed boundary. The inventory is based on the pinned source and must be refreshed before a later implementation manifest.

| Current writer/path | Boundary and required video participation |
|---|---|
| BE2-08 create composed with foundation job create | A. One BE2-01 UoW enlists foundation job/attempt/semantic request/command receipt/dispatch outbox/audit intent and BE2-08 run/submission receipt. |
| AiJobService.start_attempt called by VideoWorkerAdmission.begin | S. BE2-01 performs capability/current-eligibility checks and the job start; BE2-08 starts the paired run. Eligibility denial that cancels the job also cancels the run in the same UoW. Preserve DUPLICATE_DELIVERY, ATTEMPT_NOT_ACTIVE and JOB_NOT_QUEUED semantics. |
| cancel_job | F. Pair the applicable job/attempt cancellation with the BE2-08 run cancellation. |
| apply_cancellation_notice | F. For each matching job, process the job/run pair in canonical job-key order within the notice protocol. Do not lock all job rows first and then all runs. Notice completion and its audit remain in the same approved foundation protocol. |
| retry_job / run_due_retries | F. Paired failed_retryable → queued transition with the same new attempt identity and retry/outbox data. Stale callbacks are no-ops after checking the paired state. |
| expire_overdue_attempts / _expire_overdue | F. Paired timeout/failure mapping. BE2-10 retry policy determines retryable versus exhausted; no job-only timeout CAS. |
| recover_unstarted_dispatches / _recover_unstarted | F only when dispatch loss closes the job attempt. The paired queued run must close to the mapped failure state. A mere republish/outbox insertion leaves job/run queued and is not a lifecycle transition. |
| completion branch that records failure, cancellation, unsafe, malformed, or business rejection | F/reject. Business rejection uses the separate reject commit below; ordinary failure/cancel is one paired BE2-01 UoW. |
| successful completion/finalization | B. One paired success commit; not routed through the reject transaction. |
| report_progress | Explicit job-only exception: progress updates while the same attempt remains running do not change video lifecycle state. Keep it in the foundation transaction. If a future progress operation changes lifecycle, it must enlist the video participant. |
| side-effect outbox delivery claim/ack, audit/quarantine sink delivery, dispatch publication with no job-state mutation | No video participant required because these paths do not change job/run lifecycle state. They must not be used to mutate job state outside A/S/B/F. |

## Boundary matrix

BE2-01 opens, commits, and rolls back each UoW. BE2-08 participants receive a transaction-scoped write capability for only their rows. No application protocol exposes a SQLAlchemy connection. The public enlistment mechanism is a required BE2-01 contract; its exact API name is not adopted here.

| Boundary | Owner and callers | Enlisted owned rows | Paired CAS / create condition | Recovery point |
|---|---|---|---|---|
| A — submit | BE2-01 UoW owner; BE2-08 create path calls the typed foundation submission surface and joins as participant. The creation lease is outside this UoW. | BE2-01: job, initial attempt, semantic key, command receipt, dispatch outbox, audit intent. BE2-08: queued run and submission receipt. | Create one foundation job and one BE2-08 run under same organization/job_id, protected by both unique constraints and same commit. The initial run has no attempt_id; do not claim it is bound to the initial attempt until S. Compare the foundation SemanticRequestKey and video session/pin semantic index explicitly; mismatch or split winner fails closed. | Any foundation or VIDEO_WRITE_CONFLICT rolls back the whole UoW. Translate participant conflict, then do authoritative replay lookup in a new transaction. Lost acknowledgement reads both receipt/index owners and proves one winner; otherwise remain pending. Creation lease is released/renewed by its own protocol and is not claimed atomic. |
| S — start/admission | BE2-01 start API called only by VideoWorkerAdmission.begin after capability and eligibility decisions. Reconciler/dispatcher are not S callers. BE2-08 joins as participant. | BE2-01: job and active attempt. BE2-08: the run found by organization/job_id, and its start revision/state. | Lock job then run. CAS job queued → running for the active attempt and run queued → running with the exact same attempt_id; both commit or neither. If eligibility denies start, paired cancellation CAS occurs; do not call provider. | After lost acknowledgement/crash, reread the persisted pair in a new UoW. Same running attempt is duplicate recovery; wrong/missing attempt, run, or state fails closed. Preserve duplicate and inactive-attempt results; never infer start from broker delivery. |
| B — successful finalization | BE2-01 opens/commits; the BE2-08 finalizer joins. External generation/media work is complete before B opens. | BE2-01: job, winning attempt, completion receipt, audit/outbox records. BE2-08: one run row with artifact stored in run_json. No separate artifact row is present in current schema. Source fences join only under a separately adopted same-store protocol. | CAS job running → succeeded and run running → succeeded for the same winning attempt and exact artifact identity. Commit the pair and foundation receipt atomically. Persisted completion receipt does not contain completion_key; recovery contract must query job/attempt receipt and verify exact run artifact or fail closed. | Lookup/reconcile in a new UoW. A late attempt loses the paired CAS. Infrastructure rollback has no business-reject intent in that transaction; recover the retained private stage through recover_stage/reconcile and receipt lookup. If a durable same-result recovery cannot be proved without rerender, keep the boundary blocked; timeout sweep alone is not proof. |
| F — failure, cancel, timeout, retry, dispatch loss | BE2-01 owns each UoW. API, worker, reconciler, cancellation-notice and dispatch-recovery callers route through it; BE2-08 participates for every paired run. | BE2-01: job, active/closed/new attempt, retry/dispatch records, notice/audit rows as applicable. BE2-08: matching run and attempt identity. Fence rows only if a specific transition requires them, acquired last. | Apply the mapping table above. For started work, both CASes require the exact same attempt_id. For pre-start dispatch loss, pair by organization/job_id and queued run revision; run has no attempt_id. Retry creates the same new attempt_id on both owners. Unresolved exhausted/stale mapping blocks approval. | Read the paired authoritative states in a new UoW after lost acknowledgement. Re-run due operations idempotently. A one-sided state or unknown mapping fails closed and enters recovery; do not let a job-only retry/timeout/cancel commit. |
| F-reject — business/policy rejection | BE2-01 exposes a separate reject operation/UoW. BE2-08 supplies the exact current result identity; its existing private-staging cleanup request is a separate subsystem and is not the foundation intent. | BE2-01: job/attempt if a state change applies, deterministic quarantine intent and outbox. BE2-08: paired run only if state changes; otherwise lock/read to prove its authoritative state. | Re-read under job → run locks. If the attempt remains current and maps to a terminal rejection, CAS the job and run to the approved existing states and insert the intent in the same reject commit. If already terminal/cancelled/superseded, make no state change but commit the idempotent intent after verifying the pair. Map BE2-08 ExactRef/artifact identity to foundation artifact_refs explicitly; unmappable identity fails closed. No REJECTED JobState. | A reject commit lost-ack is resolved by the deterministic event_id and paired receipt lookup in a new UoW. A failed reject commit remains pending and retries the same identity. It is never considered handled because B rolled back. If the worker can die before a durable reject request exists, CR08-01 must add an idempotent persisted recovery input or keep rerender/cleanup blocked. |

## Lock order, leases, and deadlock response

The required row-lock order is:

1. foundation job row;
2. the paired BE2-08 run row;
3. every required fence row, sorted by a stable canonical key.

For a multi-job cancellation notice, process each job/run pair in canonical job order; do not lock all matching job rows and then all runs. Foundation attempt/receipt/outbox rows are subordinate to their job and must not introduce an inverse lock path. Any operation that does not need source fences uses the job → run prefix. A participant locks its run after the job lock and before BE2-01 invokes any fence hold.

BE2-01 must sort fence keys itself or require a sorted, validated set at the typed UoW boundary. Current caller order is not a durable ordering guarantee. A source invalidator may lock/update its fence rows and commit, but must not then acquire job/run rows in that same transaction; any follow-up job/run mutation uses a new BE2-01 UoW in the common order. Prove both invalidation/finalization winner orderings with two PostgreSQL sessions before claiming a durable fence.

The BE2-08 creation lease is a separate logical guard around A, currently outside the UoW. It is not a row in the atomic commit and must not be described as atomic. Define release, expiry and lost-ack behavior separately; if it is ever made a held DB row in this UoW, prepare a new reviewed lock protocol first.

An outbox delivery lease is distinct from a SQL row lock. The current publisher commits its claim before broker I/O; no SQL transaction or row lock remains open across publish. A logical lease may remain active while publishing. Any later paired lifecycle transition starts a BE2-01 UoW in job → run → fence order and must not reuse a pre-held outbox row lock. Acknowledgement/release is a separate transaction governed by the lease token.

BE2-14 accounting uses its own transaction. Do not open or wait on an accounting transaction while holding the lifecycle UoW's job/run/fence locks; budget reservation is not atomic with A/S/B/F. Deadlock, lock timeout, missing/unknown source row, or unavailable owner data leaves the operation pending or fails closed. It never authorizes success.

## Persisted job → run → source-pin identity

The required lookup starts from the authenticated persisted foundation job and resolves the unique BE2-08 run by organization_id + job_id. Add a BE2-08 participant accessor equivalent to get_by_job(organization_id, job_id, for_update=True) to the candidate card scope; it does not exist in the pinned source. Validate, field by field:

- organization_id and job_id match the locked foundation job/run;
- foundation scope/session and video pin session agree;
- active attempt_id and attempt number agree once S has bound the run; before S, the queued run must have no attempt_id;
- foundation request_ref request identity/revision and context_revision agree with the video run/pin fields defined by the approved mapping;
- exact bundle reference/version/hash, audience/context revision, source refs, and content profile/policy identity match the producer-created pin;
- idempotency identities from foundation semantic/command receipts and the BE2-08 session/pin receipt produce one consistent winner.

Do not equate request ID, input_hash, pin_digest, video_id, run_id, completion_key, or receipt fingerprint without an adopted field-level rule. Keep WorkerDispatchEnvelope unchanged. If the persisted records cannot prove one unique exact lineage or any accessor returns missing/ambiguous data, fail closed and keep X09-08 NOT_IMPLEMENTED. A new persisted linkage requires a versioned CR and separate approval.

## Source-fence inventory and X01 blocker

A post-read resolve_exact or process-local coordinator is not a held fence. Before a durable X01 claim, the owning plans must map every finalizer currentness input to its owner, persisted key, invalidation writer, lock/CAS and connection:

| Currentness input | Candidate authority/owner | Required invalidation coverage | Current status |
|---|---|---|---|
| Bundle head/version and source bundle identity/hash | BE2-07 | Bundle head/version change and bundle replacement | Resolver checks exact currentness in a separate transaction; no shared SQL fence adopted. |
| Basis/context revision and contributor/context facts | BE2-07 plus the owner of the context facts | Context/session/basis revision change | Inputs are checked by currentness logic; exact persisted fence row and all writers remain to be adopted. |
| Audience revision and policy reference | BE2-07 and policy owner, exact ownership to be named by card owners | Audience/consent/context and policy-reference changes | No shared held fence adopted. |
| Catalog claims and source record identity/version/hash | BE2-07 and catalog/source-record owners | Claim, source record, version, hash, rights or availability mutation | No shared held fence or complete writer inventory adopted. |
| Policy epoch, kill switch, worker rights/authorization | BE2-14/policy owner and BE2-08 execution owner, exact key ownership to be named | Policy/kill/rights/revocation updates | Phase checks are candidate reads; execution fence and owner lock key are not adopted. |
| Encoding, content profile, retry policy, model profile, library asset | BE2-08 plus the owning profile/catalog providers | Profile/version, asset, retry-policy or model-profile update | Identity exists in VideoPin; every currentness writer and held fence remains to be specified. |
| Active job/run attempt and staged/final artifact descriptor/hash | BE2-01 for job/attempt; BE2-08 for run/artifact | Attempt winner change, artifact descriptor change, stage replacement | BE2-01 row and BE2-08 run lock can be enlisted; finalizer descriptor fence protocol still needs exact owner/key and invalidator list. |

The actual source manifest must be expanded with exact path/function references for every invalidation writer before implementation approval. Missing owner, row, lock, or writer inventory is a blocker; do not represent the table as complete.

A future held fence requires the finalizer and all relevant invalidators to use the same PostgreSQL rows/connection protocol: finalizer locks the complete set FOR SHARE through commit; invalidators lock the same rows FOR UPDATE or CAS the same monotonic epoch. All job/run locks precede fence locks. If an invalidator also triggers job/run cancellation, it commits the fence mutation first and then invokes a new BE2-01 paired transition. Test both two-session winners: invalidation first means finalization rejects with no accepted artifact; finalization first means invalidation waits until commit. Lock timeout/deadlock is pending/fail-closed.

Current BE2-07 approval has no SQL store and resolve_exact opens a separate transaction. Current foundation OwnerFencePort has no production binding and is not a BE2-07 fence. Therefore X01 remains PARTIAL. If the same-store mechanism is unavailable under a separately reviewed BE2-07 scope, omit the held-fence claim and retain PARTIAL. This commit-time fence would not provide X05d current-source use authority or implement X02.

## Reject and finalization recovery contract

The separate reject operation must be a public BE2-01 application boundary that accepts an authenticated job/attempt and exact rejected result identity. The foundation UoW reads current state, locks the paired run, applies a permitted existing JobState transition where one is due, adds the deterministic quarantine intent through AiJobUnitOfWork.add_quarantine_intent, and commits. The public API must not expose the SQL connection.

CR08-01 must define one stable event_id namespace from persisted job/attempt/result identity, including how output ExactRef values map to the foundation artifact_refs and how duplicate requests with the same identity replay. A mismatch for the same event_id is a conflict, not a replacement. Existing VideoPrivateStaging.request_quarantine is only a private-stage cleanup request; it can fail and be swallowed today, so it cannot stand in for the durable foundation intent. The reject path must not report handled until the foundation intent commit is authoritative.

B infrastructure rollback may be retried only after a new-UoW receipt lookup proves whether B committed. If no receipt exists, recover the same retained stage and retry the same finalization/reject identity. Existing recover_stage/reconcile and timeout sweeps are candidates, not proof. A worker crash before the reject identity/intent is durable creates a recovery gap; require a durable same-result replay input or retain the blocker. Never rerender merely because a lookup timed out, an intent write failed, or a stage lookup is unavailable.

## Composition adapter and API ownership

- BE2-01 owns the foundation UoW provider and public transaction-scoped enlistment API. The FEAT-057 adapter must not read SqlAiJobUnitOfWork.connection or put SQLAlchemy types in application protocols.
- BE2-08 owns VideoRunRows and domain state transitions for its rows, including candidate fail/retry/timeout operations. Add domain/model and codec paths to its candidate file list. No video participant may begin/commit/rollback.
- FEAT-057 owns the cross-lane composition adapter and integration tests under its separately approved scope.
- The adapter translates VIDEO_WRITE_CONFLICT to a whole-UoW abort/replay signal, rolls back before any replay query, and opens a new transaction for authoritative replay. It must not catch a SQL error and continue in an aborted transaction.
- Unique conflicts across the two semantic indexes, lost acknowledgement, lease expiry, duplicate delivery, one-sided state, and unknown receipt each have explicit fail-closed recovery.
- Candidate adapter path: backend/src/sketch2life/infrastructure/cross_lane/knowledge_video.py. It is present as untracked candidate work in this dirty worktree; that does not approve or include it in an implementation manifest.

## BE2-08 → BE2-09 artifact read model

The public read-only artifact model remains a separate BE2-08 scope. The current candidate run has artifact data in run_json and no separate artifact row; the foundation finalization receipt lives in BE2-01-owned tables with no BE2-08 FK. BE2-08 must not directly query or write foundation tables.

Before the read model is adopted, the card owners must choose a versioned public way to expose receipt identity: either BE2-01 provides a read-only receipt lookup that a FEAT-057 composition adapter joins to the BE2-08 run, or BE2-08 stores an opaque receipt reference supplied during the paired B commit. Do not claim either is implemented. The read model must identify organization/session, run/video, exact source and artifact hash/version, audience/context, visibility principal, and receipt provenance, with explicit read-after-commit and stale/superseded behavior. Current VideoRun has no superseded state, so the rule must be specified rather than inferred. BE2-09 may read only and cannot mutate BE2-08 rows. X05d remains BLOCKED; X05c/CR09-02 remains OPEN.

After this successor scope passes rereview, refresh the BE2-08 supplement's stale cross-reference from foundation scope revision 2 to this revision 4 and resolve its receipt-provenance clause in the owning-card supplement. Until then the prior supplement is preserved byte-for-byte.

## BE2-14 boundary

Eligibility, worker/provider execution authorization, and budget/concurrency reservation/accounting remain distinct and fail-closed. The accounting ledger transaction is separate; do not nest it inside the lifecycle UoW or claim atomicity with A/S/B/F. The owner has not supplied a budget unit or limit; do not invent one or use synthetic test values as permission. Reservation has no expiry field in current source. Expiry/renewal and related concurrency semantics require a versioned CR and separate approval.

## Candidate evidence for a later approved scope

| ID | Required evidence |
|---|---|
| U01 | BE2-01 alone opens/commits/rolls back; participant-negative tests prove BE2-08 cannot do so and writes only owned rows. |
| U02 | A/S/B/F writer inventory is complete; every paired lifecycle transition commits job/run together, while report_progress and delivery-only exceptions remain job/outbox-only. |
| U03 | State mapping covers retryable, exhausted, timeout, dispatch loss, cancel, unsafe reject, malformed output, stale and temporary outcomes without new enum values; unresolved BE2-10/BE2-08 decisions block acceptance. |
| U04 | A checks both semantic-dedup indexes, command receipts, run uniqueness, and split-winner failure. Unique VIDEO_WRITE_CONFLICT rolls back the whole UoW and replays in a new transaction. |
| U05 | S uses VideoWorkerAdmission through a BE2-01 capability/eligibility path; duplicate/inactive attempts fail closed and no provider call occurs on denial. |
| U06 | B and reject are distinct commits. Reject intent survives an independent reject commit, never a B rollback; same event replays, conflicting identity fails closed. |
| U07 | B receipt recovery reconciles foundation completion_receipt(job_id, attempt_id) with exact BE2-08 run_json artifact; ambiguity or unavailable lookup stays pending. |
| U08 | Reconciler, notice, retry, timeout and dispatch-loss paths all use paired F transitions; multi-job notice lock order is stable; progress-only and delivery-only exemptions are tested. |
| U09 | Job → run → sorted fence order has no inverse writer. PostgreSQL two-session tests prove invalidation-first and finalization-first; NOT_RUN until separately authorized. |
| U10 | Full persisted job/run/pin map is verified from owner records; missing or mismatched accessors/fields fail closed; WorkerDispatchEnvelope unchanged. |
| U11 | BE2-08 read model is separately adopted, receipt provenance has a public contract, and BE2-09 performs no BE2-08 writes. |
| U12 | BE2-14 remains a separate transaction; no nesting, invented budget, expiry or provider permission. |
| U13 | Fake/unit evidence is labelled as protocol evidence only; SQL, PostgreSQL, provider, Modal, Lightning and runtime NOT_RUN unless separately authorized and run. |
| U14 | Card approvals/status/acceptance remain unchanged; X01 PARTIAL, X05d BLOCKED, X05c/CR09-02 OPEN and X09-08 NOT_IMPLEMENTED until proved. |

Candidate paths are not an implementation manifest. Additional BE2-08 candidates now include backend/src/sketch2life/domain/knowledge_video/model.py and backend/src/sketch2life/infrastructure/knowledge_video/codec.py. BE2-01 candidates include its service/domain/SQL repository/table and public UoW ports. FEAT-057 candidates include the composition adapter and exact unit/integration tests. Every changed source/schema/test path still needs a reviewed minimal manifest and card-local supplemental approval. Published migrations remain frozen.

## Open gates before any implementation approval

1. BE2-10/BE2-08 owners confirm who decides retry exhaustion and how FAILED_EXHAUSTED maps to the video row. Define stale completion and cleanup semantics without new state values.
2. BE2-01/BE2-08/FEAT-057 specify the typed start API, locked get-by-job accessor, participant enlistment API, full writer inventory, row manifests, and A/S/B/F paired CAS.
3. CR08-01 defines dual dedup comparison, durable completion/reject identity, receipt recovery without a completion_key column, mapping of artifact refs, unique-conflict translation, and crash recovery before reject intent.
4. Reconcile all lock writers, multi-job cancellation notice, fence ordering, creation lease, outbox delivery lease and BE2-14 separate transaction. Identify any incompatible source path before approval.
5. BE2-07 owner must supply a separately reviewed same-store currentness fence and invalidator inventory before any X01 durable-fence claim; otherwise X01 stays PARTIAL.
6. BE2-08/BE2-09 owners resolve receipt provenance and stale/superseded behavior in the separate read-model supplement; refresh its Rev2 reference only after this scope passes review.
7. FEAT-057 must adopt this scope's boundary direction in a successor slice-plan revision 5. Revision 4 and its erratum stay immutable history and do not authorize implementation.
8. Obtain separate supplemental approvals for S/F and each affected card before implementation. The scope review itself is not approval.
9. Owner supplies BE2-14 budget unit/limit only when ready; until then no budget values are assumed.

## Offline sequence after approvals

1. Freeze the field-level job/run/pin/receipt contract and state mapping with card owners.
2. Freeze the public BE2-01 enlist/start/reject API and BE2-08 participant methods; verify source paths against reviewed per-card manifests.
3. Resolve source fence feasibility. If no same-store protocol exists, keep X01 PARTIAL and omit durable-fence claims.
4. Resolve BE2-08 read-model receipt provenance in the owning supplement before BE2-09 consumer work.
5. Obtain supplemental approvals for BE2-01, BE2-08, BE2-10 where state ownership applies, and FEAT-057 composition. Preserve BE2-14 budget inputs as pending.
6. Only then begin offline implementation and its scoped tests. PostgreSQL/two-session evidence, provider, Modal, Lightning, server and runtime remain separate authorization gates.
7. Have an independent code review, fix findings, and rerun affected offline checks. Component acceptance remains a separate owner decision.

## Approval state

This draft is ready for another independent scope review only. It does not amend any existing card approval, scope acceptance, status, migration, source or test. It does not authorize code, test execution, database, provider, server, Modal, Lightning or runtime. A/S/F remain pending separate review and supplemental approval. X01 remains PARTIAL; X05d BLOCKED; X05c/CR09-02 OPEN; X09-08 NOT_IMPLEMENTED; budget unit/limit unprovided.

