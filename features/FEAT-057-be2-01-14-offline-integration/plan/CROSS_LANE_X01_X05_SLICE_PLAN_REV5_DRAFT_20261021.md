# FEAT-057 BE2-01–14 cross-lane X01/X05 slice plan — revision 5 draft

- Status: DRAFT / OWNER_DIRECTION_RECORDED / CHANGES_REQUIRED_ADDRESSED / READY_FOR_INDEPENDENT_REREVIEW
- Revision: 5
- Feature: FEAT-057 offline cross-lane integration
- Candidate branch/HEAD: feature/be2-backend-ai-integration / 1649b72978877d82b4d7662040ff3555dee0a3a7
- Prepared: 2026-10-21 (Asia/Saigon)
- Worktree was dirty; exact reviewed source bytes are pinned by the manifest below.
- Successor FEAT-044 scope: CROSS_LANE_FOUNDATION_UOW_SCOPE_REV4_DRAFT_20261021.md
  SHA256 9B96CA79FDA1DB8DFCBD2DFED6550ECA0645AD0C86CCEEAAF79793B0B7200381

This is a consolidated successor for review to FEAT-057 plan revision 4 and erratum 1. It preserves those originals byte-for-byte; it does not retroactively amend them. The successor incorporates owner decision D1 and the Claude rereview report with verdict CHANGES_REQUIRED. It does not approve implementation, change a card scope/approval/status/acceptance, or authorize a test, database, Modal, Lightning, provider, server, or runtime run.

## 1. Current outcome and authority

The owner selected model A for the cross-lane transaction direction:

- BE2-01 owns and opens the UoW for submission, start, successful finalization, failure, cancellation, timeout, retry, reconciliation-driven lifecycle changes, and business rejection.
- BE2-08 participates only for its own video rows and cannot begin, commit, or roll back the foundation UoW.
- Reconciler and outbox-dispatcher paths that mutate a foundation job must enlist the matching BE2-08 run in the BE2-01 UoW. A job-only lifecycle mutation is prohibited.
- Business rejection writes quarantine/cleanup intent in a separate reject commit through the existing foundation quarantine-intent writer. Rolling back successful finalization is not how the intent is preserved. B rollback is reserved for infrastructure errors and needs recovery.
- Common row-lock order: foundation job → BE2-08 run → source-fence rows sorted by canonical key. Multi-job transitions process job/run pairs in stable job order.
- WorkerDispatchEnvelope stays unchanged; persisted data must prove job → run → source pin, otherwise fail closed.
- BE2-08 artifact read model for BE2-09 is a separate owning-card scope. BE2-14 eligibility, execution authorization and budget/concurrency stay separate. Budget unit/limit remain unprovided.
- S and F remain subject to independent review and separate supplemental approval. This plan is not implementation approval.

Owner dispositions remain: X01 agreed with changes but PARTIAL until a durable adopted fence is demonstrated; X05a agreed with changes; X05b agreed with changes; X05c open; X05d BLOCKED unless an already adopted resolver/fence is identified; X09-08 agreed with changes but NOT_IMPLEMENTED until persisted composition is proven; POLICY-08 agreed with changes; ENV/Modal deferred pending a separate resume instruction.

## 2. Baseline, exact sources, and limits

Prior plan revision 4 SHA256: 6AF69E07E7FC51BD6AAA992A703FBE97AC2BC8E588FEC9F8735FBF74E88C6601.
Prior erratum 1 SHA256: 7530294B18B30616EB9A968ABF0AD227C661294500CD0789A7EC514D54E5FE39.
Owner D1 receipt SHA256: 3EECF89A488F7B2539AF41BE5CEF830D4C2509D6E93D478F624DF46B4F32A16D.
Claude rereview report SHA256: 0507A53D569B34ACF9EB44549D6BE794851335F3DBB88FD89E48D17E4AA649F0.
Source manifest revision 2 SHA256: 01160A4876ABB97CC33AC17108ADAE6F95E876DB86A24DF84B9832EC2B4F74FC. It pins all 14 prior source files plus ai_jobs.py, the AI JobState model, the BE2-08 codec and AI Jobs SQL tables used in the rereview. All 18 hashes were verified against current bytes. The source tree remains dirty; this is not a commit or approval.

The candidate source confirms that the current foundation state enum is queued/running/succeeded/failed_retryable/failed_exhausted/blocked_unsafe/cancelled, while ResultDisposition is a separate accepted/stale/rejected axis. BE2-08 run transitions currently implement start/finalize/cancel only. A run is unique by organization/job_id, has no attempt_id until start, and stores its artifact in run_json. There is no separate artifact table and no persisted BE2-08 completion_key. The finalization receipt belongs to foundation. VideoRunRows currently lacks a locked lookup by job_id. These are design constraints, not implemented cross-card behavior.

No tests or runtime suites are authorized or run by this plan. Prior offline evidence remains limited to its pinned test/source package and does not establish the contracts below.

## 3. Consolidated A/S/B/F lifecycle boundaries

The detailed candidate matrix and state map are in the FEAT-044 scope revision 4 draft cited above. This plan adopts that direction as a required design gate, not as a completed contract.

| Boundary | Owner / caller | Required paired rows and CAS | Gate |
|---|---|---|---|
| A — submit | BE2-01 opens/commits; BE2-08 create path joins as participant. Creation lease is separate. | Foundation job/attempt/semantic key/command receipt/dispatch outbox/audit intent plus BE2-08 queued run/submission receipt in one commit. Pair by organization/job_id and unique constraints. The initial run has no attempt_id. Reconcile both independent semantic-dedup indexes or fail closed. | CR08-01 must define the field-level dedup comparison and whole-UoW rollback/new-transaction replay after either owner reports a unique conflict. |
| S — start/admission | BE2-01 start API called by VideoWorkerAdmission.begin after capability and eligibility checks; BE2-08 joins. Reconciler/dispatcher are not S callers. | Job queued → running and run queued → running with the exact same active attempt_id, or neither commits. Eligibility denial that cancels the job also cancels the run. | Requires independent review and supplemental approval for S. Preserve duplicate/inactive-attempt outcomes and never call provider on denial. |
| B — successful finalization | BE2-01 opens/commits; BE2-08 finalizer joins after generation/media work has ended. | Job running → succeeded and run running → succeeded for the same winning attempt and exact artifact. Foundation completion receipt commits with the job; artifact lives in BE2-08 run_json. | Recovery must reconcile foundation receipt by job/attempt with the exact locked video artifact. No completion_key column/table is assumed. |
| F — failure/cancel/timeout/retry/dispatch loss | BE2-01 owns each transition; APIs, worker, reconciler, notices and dispatch recovery use it. BE2-08 joins for every lifecycle pair. | Existing JobState mapping only. Pair job/run CAS. Started work checks identical attempt_id. Pre-start dispatch loss pairs by job_id and queued run revision. Retry binds the same new attempt_id on both records. | Requires independent review and supplemental approval for F. BE2-10/BE2-08 must resolve exhausted-state ownership and stale-result behavior before approval. |
| F-reject — business/policy rejection | Separate BE2-01 reject UoW; BE2-08 supplies exact rejected result identity and participates only in its own run transition. | Lock and reread job then run. If current attempt requires terminal state, paired CAS plus deterministic quarantine intent in the same reject commit. If already terminal/cancelled/superseded, preserve state and commit idempotent intent after verifying the pair. | Must use the existing foundation intent writer/outbox, not rollback. Map video ExactRef to foundation artifact_refs. Persist/replay reject identity and prove crash recovery before the intent commit. |

The writer inventory in the successor scope covers cancel_job, multi-job cancellation notices, start and denied-start, retry, overdue timeout, dispatch-loss reconciliation, completion failure/reject, successful B, report_progress, and delivery-only outbox paths. Progress-only updates and outbox delivery acknowledgement are explicitly job/outbox-only because they do not change video lifecycle state. Any new job lifecycle writer must be added to the inventory before approval.

## 4. Required lock, recovery, and identity protocol

Use the order job → paired run → canonical sorted source-fence keys. A participant acquires its run lock immediately after the job and before any fence hold. Multi-job cancellation notices process each job/run pair in canonical job order; they must not lock all jobs and then all runs. The current fence hold follows caller order, so BE2-01 must provide a stable ordering at the public UoW boundary.

The BE2-08 creation lease is currently a separate logical guard outside A; it is not part of the transaction. An outbox delivery lease may remain active during broker publish, but no SQL row lock/transaction may be held over broker I/O. These are different mechanisms. BE2-14 accounting is a separate transaction and must not be opened while lifecycle row/fence locks are held. Invalidation transactions may update fence rows and commit, then trigger any job/run work in a new BE2-01 UoW.

Start from persisted organization_id + job_id and use a new locked BE2-08 get_by_job accessor; compare organization, session, request identity/revision, context, exact bundle/source pin, attempt and idempotency fields. The accessor and complete field rules are not in current source. Do not equate request_id, input_hash, pin_digest, video_id, run_id, completion_key, or receipt fingerprint. Preserve WorkerDispatchEnvelope. Missing or ambiguous mapping fails closed and keeps X09-08 NOT_IMPLEMENTED.

For B recovery, the current foundation receipt is keyed by job_id/attempt_id and does not store completion_key. The candidate contract is to query the authoritative foundation receipt using authenticated job/attempt identity and reconcile its result with the locked run_json artifact. If this is not unique and exact, stay pending and raise a versioned CR; do not claim a stored completion_key or add schema in this plan.

## 5. Source fence and X01

The current BE2-07 exact resolver checks bundle head/version, basis/context, audience, policy reference, catalog claims and source records in its own transaction. The finalizer candidate also depends on policy epoch, kill/rights, encoding/content profile, model profile, library asset, BE2-14 eligibility and the staged/final artifact descriptor. Each input needs an owner, persisted fence key, invalidation writer and same-store lock/CAS rule. The full writer inventory is not yet adopted.

The current foundation OwnerFencePort has no production binding and does not create a BE2-07 fence. The BE2-07 approved scope has no shared SQL store/fence. Therefore X01 remains PARTIAL. A later durable-fence claim requires separately approved same-store owner scopes and PostgreSQL two-session evidence for both winner orderings. Post-read validation, exact resolve, SQLite, or a process-local coordinator cannot substitute.

A fence covers finalization commit ordering only; it does not implement X02 or provide the current-source use resolver required by X05d.

## 6. BE2-08 artifact model and BE2-14

The BE2-08 read-only artifact model is a separate FEAT-050 scope. Current video schema stores artifact data inside run_json and has no separate artifact row. Foundation completion receipt is in a separate owner schema with no BE2-08 FK. BE2-08 must not query foundation tables directly. Before BE2-09 use, BE2-01/FEAT-057 and BE2-08/09 owners must select a versioned public route for receipt provenance: read-only foundation receipt lookup composed with the run, or an opaque receipt reference supplied in B. Exact artifact identity, visibility, read-after-commit and stale/superseded behavior remain open. After this plan passes rereview, refresh the BE2-08 supplement's stale foundation-scope Rev2 reference to Rev4; do not edit that supplement before then. X05d stays BLOCKED and X05c/CR09-02 stays OPEN.

BE2-14 eligibility, execution authorization, and budget/concurrency remain distinct fail-closed gates. Accounting transaction is separate; do not nest it in A/S/B/F. Reservation has no expiry today. The owner has not provided a budget unit/limit; do not invent values. Expiry/renewal requires a versioned CR.

## 7. Exact revision-4 divergence now resolved in this successor

Revision 4 and erratum 1 remain immutable history. This revision replaces, rather than silently overrides, the following stale clauses:

- Revision 4 §4 OD-X05a and §4A X05a: expand the two-boundary A/B description to the separately owned A/S/B/F and reject boundaries above.
- Revision 4 §5 G0: include paired row manifest, state mapping, deterministic lock order, receipt/reject recovery and per-card supplemental approval gates.
- Revision 4 §5 G1: require separate S/F review and supplemental approvals before any card code or tests.
- Revision 4 §5 G2: route start through BE2-01 admission; dispatchers/reconcilers are F callers only; add locked get-by-job and exact persisted mapping gate.
- Revision 4 §5 G3 and §6 A4: separate successful B from reject commit; expand finalization-fence inputs and remove “hold or atomically revalidate” as an equivalent substitute.
- Revision 4 §5 G3/G4: do not imply foundation receipt identity is already exposed by the BE2-08 read model; require an adopted public read route and stale/superseded semantics.
- Erratum 1 lifecycle table and recommendation: replace “S/F pending owner disposition” with the owner-selected direction while retaining independent review and supplemental approval; state reject as its own commit, never as rollback side effect.
- Erratum 1 lock/lease text: distinguish SQL row locks from logical creation/outbox leases; creation lease remains outside A and is not atomic.
- Revision 4 and erratum's Modal sequencing language: ENV is deferred until an explicit separate resume instruction; no X01 Modal rerun is authorized by this plan.

No earlier text or approval is retroactively changed by this draft.

## 8. Gates and future verification sequence

G0 is documentation direction only. Before implementation:
1. BE2-01, BE2-08 and FEAT-057 owners adopt the exact public UoW/enlist/start/reject API, row manifest, receipt contract and paired CAS.
2. BE2-10 and BE2-08 resolve retry exhaustion and video-state mapping, including dispatch loss and stale result.
3. The source-fence owner inventory and same-store feasibility are approved; absent that, keep X01 PARTIAL.
4. The BE2-08 read-model supplement adopts receipt provenance, exact artifact identity, visibility, read-after-commit and stale/superseded behavior; BE2-09 remains read-only.
5. BE2-14 owner supplies budget unit/limit only when ready; no value is assumed.
6. Each affected card records a supplemental scope and explicit implementation approval. S/F require their own approval. Existing approvals do not cover them.
7. Only after those gates may offline code and scoped tests begin. Test groups must cover participant cannot begin/commit/rollback; A split-winner and replay; S deny/duplicate/inactive attempt; B receipt recovery and late result; every F writer; reject intent replay and crash recovery; lock-order and deadlock probes; persisted mapping; read-model access and BE2-14 separation.
8. PostgreSQL two-session fence tests are required for durable fence claims, but remain NOT_RUN until separately approved. Modal/Lightning/provider/server/runtime remain deferred.

## 9. Acceptance boundary

A future offline component result may establish only the exact source-bound tests run. It cannot establish durable X01 without the two PostgreSQL race orderings; cannot close X05d without an adopted current-source resolver/fence; cannot close X05c/CR09-02 from playback intent; cannot authorize provider execution from synthetic BE2-14 values; and cannot turn any card DONE without its owner acceptance.

Keep X01 PARTIAL, X05d BLOCKED, X05c/CR09-02 OPEN, X09-08 NOT_IMPLEMENTED, BE2-01/07/08/09/14 card statuses unchanged, and Modal/Lightning/runtime NOT_RUN.

## 10. Approval state

Revision 5 is a draft ready for independent rereview only. It consolidates the D1 design direction and corrects the listed revision-4/erratum divergence; it does not claim that any detailed interface, adapter, state mapping, fence, artifact read contract, or recovery route has been adopted or implemented. Do not code, stage, commit, push, merge, create a branch, or run tests/runtime under this plan.

