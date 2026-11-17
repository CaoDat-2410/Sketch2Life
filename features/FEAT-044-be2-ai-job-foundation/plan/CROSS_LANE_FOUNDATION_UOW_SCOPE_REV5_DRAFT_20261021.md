# Cross-lane foundation-owned UoW for BE2-01 / BE2-07 / BE2-08 — scope revision 5 draft

- Status: DRAFT / OWNER_DECISIONS_RECORDED / CHANGES_ADDRESSED_PENDING_INDEPENDENT_REREVIEW
- Prepared: 2026-10-21 (Asia/Saigon)
- Foundation transaction owner: BE2-01 / FEAT-044
- Video-row participant: BE2-08 / FEAT-050
- Source-currentness dependency: BE2-07 / FEAT-056, only under a separately adopted durable fence
- Supersedes for review only: CROSS_LANE_FOUNDATION_UOW_SCOPE_REV4_DRAFT_20261021.md
- Parent SHA256: 9B96CA79FDA1DB8DFCBD2DFED6550ECA0645AD0C86CCEEAAF79793B0B7200381
- Owner decision D2 SHA256: 641A2239C6C1064C543D16A1DB24E73AC771AA4758889EC3A19C8458E1720103
- Owner decision D1: FEAT-057 evidence/notes/CROSS_LANE_UOW_OWNER_DECISION_D1_20261021.md, SHA256 3EECF89A488F7B2539AF41BE5CEF830D4C2509D6E93D478F624DF46B4F32A16D
- Claude rereview 2 report SHA256: 7A78475A0E8CE4A71C90E9F7019DA13DEB790C6EF4EB8F7B8CA2CA01DE535611
- Source manifest revision 3 SHA256: 8BC0998D505742C460FDCBE9EDDF98CBC327D41B118CF2A50E921C965D6C7342
- BE2-08 scope candidate SHA256: 6A195B6F3C9901621D268CF26B34AA217EECAFE66FA5922BD066149E6A9BC0B0
- Candidate branch/HEAD: feature/be2-backend-ai-integration / 1649b72978877d82b4d7662040ff3555dee0a3a7; worktree is dirty and exact source identity is the per-file manifest, not HEAD alone.

This is a documentation/scope successor incorporating owner D1, owner D2, and Claude rereview 2 findings. It is not an adopted cross-card contract, implementation approval, card acceptance, runtime evidence, or permission to modify source, tests, schema, or migrations. The D2 decisions settle stale-run representation and attempt-id timing only. S and F still require independent review and separate supplemental approvals in affected card records. Existing card approvals and manifests are unchanged.

## 1. Owner direction and fixed limits

1. BE2-01 opens and owns the UoW for A, S, B, F and reject transitions. BE2-08 may write only its own video rows as a participant; it cannot begin, commit, or roll back the enclosing transaction.
2. Reconciler and outbox-dispatcher paths that mutate a foundation job and have a paired video run use the BE2-01 orchestration/UoW with the BE2-08 participant. No job-only lifecycle mutation may leave a paired run behind.
3. A business rejection is written through a separate BE2-01 reject UoW using the foundation quarantine-intent writer/outbox. Intent durability never depends on rolling back B. B rollback is reserved for infrastructure failure and requires idempotent recovery.
4. The target row-lock order is job → paired video run → source-fence rows sorted by a stable canonical key. Named current-source exceptions and the cancellation-notice path are documented in section 6.
5. Keep WorkerDispatchEnvelope unchanged. Resolve job → run → source-pin identity from persisted records; fail closed when identity cannot be proved.
6. BE2-08 exposes a separately adopted, read-only artifact model for BE2-09. It must not query foundation tables directly or let BE2-09 write video-owned rows.
7. BE2-14 current-use eligibility, worker/provider authorization, and budget/concurrency are separate gates. The owner has not supplied a budget unit or limit. Reservation expiry/renewal needs a versioned CR.
8. Keep X01 PARTIAL, X05d BLOCKED, X05c/CR09-02 OPEN, and X09-08 NOT_IMPLEMENTED until their persisted contracts and evidence are adopted. Modal, Lightning, provider, server, database, and runtime remain outside this scope.

## 2. Source snapshot and corrections applied

Source manifest revision 3 pins 19 exact source files on the dirty worktree. All 18 files from revision 2 were rechecked; owner_fence_fixture.py is added because rereview 2 cited it. The BE2-08 scope candidate is separately hash-pinned. The reviewer’s source gaps are recorded: codec.py and the BE2-08 scope candidate were read for this disposition; no source was edited.

Source facts that govern this candidate:

- Foundation JobState remains queued, running, succeeded, failed_retryable, failed_exhausted, blocked_unsafe, and cancelled. ResultDisposition is a separate accepted, stale, or rejected axis; there is no rejected JobState.
- record_failure and record_dispatch_loss use the foundation job’s JobRetryPolicy to select failed_retryable versus failed_exhausted. Do not claim the runtime transition is decided by BE2-10. VideoPin.retry_policy is a separate ExactRef; its relationship to foundation JobRetryPolicy needs an explicit A-time mapping. If no exact versioned mapping is available, submission fails closed.
- VideoRun currently stores generation_state as JobState, requires an artifact whenever it is SUCCEEDED, and binds attempt_id when start is committed. The current codec persists those axes. It has no STALE video-run state today.
- Foundation retry creates a new Attempt with an attempt number and id. Under owner D2, the paired video run returns to QUEUED with attempt_id cleared; only S binds the new active attempt id. Attempt number remains foundation-owned and is not copied into VideoRun.
- The BE2-08 run row is unique by organization/job_id; artifact data is in run_json. There is no separate artifact table or persisted completion_key column. The completion receipt is keyed by job_id and attempt_id and stores receipt id, fingerprint, disposition, reason, revision, and time.
- BE2-08 VideoRunRows lacks a locked get-by-job accessor. The public participant API and the cross-lane adapter remain candidates, not adopted interfaces.
- Foundation’s owner-fence hold follows caller-provided order. The SQL test fixture sorts fence keys and locks rows in sorted order, but it is not a production binding and proves no BE2-07 fence.
- The exact BE2-07 resolver reads bundle/version/hash, context, audience, policy reference, catalog claims, and source records in its own transaction. Its currently approved scope has no same-store SQL fence.
- VideoPin also carries editorial_revision, context_revision, audience_revision, policy epoch, kill/rights/profile refs, retry policy, model profile, and library asset. Each owner key and invalidation writer must be named before a durable fence claim.
- ArtifactDescriptor.fence is supplied through the BE1 artifacts port, not owned by BE2-01 or BE2-08. The exact BE1 owner key and invalidation writer remain to be adopted.
- Creation lease wraps submission outside A. Outbox publish happens after its claim transaction commits; a logical delivery lease is not a held SQL row lock.
- BE2-08 persistence maps unique insert conflicts to VIDEO_WRITE_CONFLICT and stale row revisions to VIDEO_STALE_RUN. Both require whole-UoW rollback before authoritative reread; they are not interchangeable business outcomes.
- BE2-14 accounting uses its own transaction and Reservation has no expiry field.
- EligibilityDecision currently includes BUDGET_EXCEEDED, and some eligibility denials permanently cancel a job at dispatch, start, or retry. A budget reservation denial must not be sent through that cancellation path; see section 11.

These are source-snapshot observations, not adoption, PostgreSQL conformance, or evidence that the dirty branches are integrated.

## 3. Lifecycle state mapping

BE2-01’s persisted foundation state is authoritative. BE2-08 mirrors the chosen paired outcome and never independently decides retry exhaustion. The table is a candidate contract and requires card-local adoption.

| Trigger | Foundation decision | Candidate paired video outcome | Gate |
|---|---|---|---|
| S admitted | queued → running for the active attempt | queued → running; bind the exact active attempt_id | BE2-01 owns eligibility/capability decision and UoW; provider is not called before commit. |
| S denied by current eligibility | queued → cancelled with foundation reason | queued → cancelled | Paired S commit; preserve duplicate, inactive-attempt, and not-queued response semantics. |
| Provider failure or started timeout | record_failure applies job.retry_policy: failed_retryable if budget remains, otherwise failed_exhausted | Mirror foundation’s committed state; keep current attempt_id for the finished attempt until the paired retry/cancel/fail transition resolves | BE2-01 decides and commits; BE2-08 does not recalculate retryability. |
| Dispatch loss before S | record_dispatch_loss applies job.retry_policy from queued: failed_retryable if budget remains, otherwise failed_exhausted | Mirror the committed failure state; run remains unbound to an attempt id | Pair by organization/job_id and run revision; the foundation attempt id is not copied into the run before S. |
| Scheduled retry | foundation creates a new active attempt id and attempt number, then queues the job | failed_retryable → queued and clear any old VideoRun attempt_id | Paired F commit. Only a later S binds the new attempt id; attempt number remains foundation-only. |
| Eligibility denial during _dispatch_one or retry_job | Foundation cancels the queued or failed_retryable job | Matching queued/failed_retryable run → cancelled | These are F lifecycle writes and must enlist the run; do not call them publish-only or retry-only paths. |
| Teacher, owner, or notice cancellation | Foundation → cancelled | Matching run → cancelled | Paired F commit; apply the multi-job lock rule in section 6. |
| Unsafe result | Foundation → blocked_unsafe | Matching run → blocked_unsafe; no output is exposed | Separate reject commit with durable quarantine intent. |
| Malformed/non-retryable result | Foundation record_failure → failed_exhausted | Matching run → failed_exhausted | BE2-08 mirrors the foundation result; no invented REJECTED JobState. |
| Stale completion | Foundation may be SUCCEEDED with ResultDisposition.STALE | Under D2, a distinct terminal stale representation on the BE2-08 lifecycle axis, with no artifact and no ready-for-review state | Requires a versioned BE2-08 CR and review of model, codec, persistence, worker receipt and recovery semantics before implementation. Do not add STALE to foundation JobState through this scope. |
| Temporary/non-authoritative result | No authoritative foundation transition | No terminal video transition unless an adopted reject/stale result is committed; retain pending recovery | Never infer acceptance, cleanup completion, or permission to rerender from an unknown receipt. |

At A, the candidate contract must compare VideoPin.retry_policy with foundation JobRetryPolicy by an exact versioned mapping. The foundation policy drives the state transition. If a mapped policy identity cannot be persisted and compared, A is blocked; there is no fallback to one side’s unverified interpretation.

## 4. Complete writer inventory to boundary

Every current lifecycle writer below must be inventoried in the approved implementation manifest and use the paired participant. The current source does not yet satisfy this contract.

| Current path | Boundary and required behavior |
|---|---|
| BE2-08 create composed with foundation create | A: one BE2-01 UoW creates/replays foundation job/attempt/semantic key/command receipt/outbox/audit and BE2-08 run/submission receipt. |
| start_attempt via VideoWorkerAdmission.begin | S: BE2-01 start UoW; BE2-08 binds attempt_id at this commit only. Eligibility denial that cancels the job cancels the run in the same UoW. |
| cancel_job and apply_cancellation_notice | F: pair every job cancellation with its run. Cancellation notice must process a job/run pair at a time; section 6 names the current repository path that does not do this. |
| _dispatch_one eligibility denial | F: queued → cancelled job must cancel its queued paired run. _publish with no job-state mutation remains delivery-only. |
| retry_job eligibility denial | F: failed_retryable → cancelled job must cancel its paired run. |
| retry_job / run_due_retries | F: foundation requeue creates next attempt; paired run returns to queued and clears old attempt_id. Stale callbacks remain no-ops after paired-state validation. |
| expire_overdue_attempts / _expire_overdue | F: pair timeout outcome chosen by foundation retry policy. |
| recover_unstarted_dispatches / _recover_unstarted | F only when dispatch loss closes a job attempt. A republish/outbox insertion leaves both lifecycles queued and has no video mutation. |
| completion reject/failure/cancel branches | F or separate F-reject according to section 5; pair every state change and persist the appropriate intent. |
| successful completion | B: paired success commit, after external generation has ended. |
| report_progress | Job-only exception while the same attempt remains running; it does not change video lifecycle. Any future lifecycle change enlists the participant. |
| dispatch claim/ack, publish, and audit/quarantine sink delivery with no job-state change | No video participant for delivery-only work. Delivery code must not mutate the job lifecycle as a side effect outside A/S/B/F. |

## 5. Boundary matrix and reject decision point

BE2-01 opens, commits, and rolls back every UoW. BE2-08 receives a transaction-scoped capability limited to its rows. No application protocol exposes a SQLAlchemy connection.

| Boundary | Owner and callers | Enlisted rows and paired CAS | Recovery |
|---|---|---|---|
| A — submit | BE2-01 owns create/replay; BE2-08 create joins as participant. Creation lease remains outside A. | Foundation job, initial attempt, semantic key, command receipt, dispatch outbox, audit intent; BE2-08 queued run and submission receipt. One organization/job_id and one commit. Initial run has no attempt_id. Compare the independent semantic keys and retry-policy mapping explicitly. | Any participant or foundation conflict rolls back the whole UoW. Translate conflict, then perform authoritative replay in a new transaction. Lost acknowledgement checks both owners; ambiguous/split winner fails closed. |
| S — start/admission | BE2-01 start API, called only by VideoWorkerAdmission.begin; BE2-08 joins. | Lock job then run. Pair job queued → running and run queued → running with exact foundation active attempt_id. This is the only boundary that binds attempt_id. Eligibility denial pairs cancellation and invokes no provider. | After lost acknowledgement, reread pair in a new UoW. Same running attempt is duplicate recovery; missing/mismatched pair fails closed. |
| B — accepted finalization | BE2-01 owns the commit; BE2-08 finalizer participates after external media/generation work. | Pair job running → succeeded with accepted disposition and run running → succeeded with the exact artifact. Persist foundation receipt in the same commit. | Lookup in a new UoW. Verify receipt by job/attempt and exact persisted artifact. A late attempt loses CAS. Infrastructure rollback may recover the same retained stage only after lookup proves B did not commit. |
| B detects a non-accepted result | B must perform no lifecycle mutation and write no reject intent when its locked decision is non-accepted. It exits without a successful-finalization commit, then invokes F-reject as a separate UoW. | No B commit. F-reject reacquires job then run, rereads authoritative eligibility/moderation/artifact facts, and decides again under the current fences. If the result is still rejectable, commit the appropriate paired terminal state plus intent. If the state changed, classify/replay from current persisted facts; never commit a stale rejection over a new winner. | If the reject decision cannot be re-derived from durable input, require a versioned recovery-input CR and keep the boundary blocked. A B rollback is not evidence that reject intent exists. |
| F — failure, cancel, timeout, retry, dispatch loss | BE2-01 owns each transition; API, worker, reconciler, notices, dispatch recovery join through it; BE2-08 participates for paired rows. | Pair state changes. Started failure checks the run’s attempt id against the active/finished foundation attempt. Retry returns the run to queued with attempt_id cleared; only S can bind the next id. Pre-start dispatch loss pairs by organization/job_id and queued run revision. | Roll back full UoW on participant stale/CAS errors. Reread in a new UoW and classify exact replay versus conflict. Job-only transition is forbidden. |
| F-reject — business/policy rejection | Separate BE2-01-owned reject UoW after B declines non-accepted completion, or a direct authoritative rejection entrypoint. BE2-08 supplies exact private result identity and mutates only its row. | Lock job then run. If foundation state changes, pair the corresponding existing state transition and VideoRun update. Add deterministic foundation quarantine/cleanup intent in the same reject commit. If job is already terminal, intent-only is allowed after verifying the persisted pair; no fake receipt is required. | event_id is deterministic from persisted job_id, attempt_id, sorted artifact_refs, reason, and the normalized claim fingerprint. Intent-only recovery uses side_effect_recorded(event_id), not a paired completion receipt. Mismatch is a conflict. A crash before any durable reject identity exists blocks recovery until a CR supplies one. |

## 6. Lock ordering, named exceptions, and leases

The target transition order is foundation job row → paired BE2-08 run row → every required source-fence row sorted by stable canonical key. For multiple jobs, the target is one job/run pair at a time in stable job-id order.

Current source deviations that must be resolved before implementation approval:

- repository.jobs_for_notice currently selects and locks every matching job row in one query, then rereads each locked aggregate. It does not interleave the paired video-run lock. The implementation scope must replace this with ID discovery followed by one job lock, its paired run lock, and then the next pair, or another reviewed protocol that proves an equivalent order. The current path is explicitly not covered by the target pair-by-pair rule. This is a lock-order conformance gap; do not claim this code alone proves a deadlock.
- create_job holds source/authorization fences before inserting the new job and run. This A-only exception operates on rows being created and must be documented with the exact creation conflict and replay protocol. It does not authorize an existing job/run writer to acquire fences first.
- Foundation hold_owner_fences currently follows caller order. The public BE2-01 boundary must sort and validate canonical fence keys before locking. The pinned owner_fence_fixture sorts its scopes and locks them in SQL order; it is an ASSUMED_CONTRACT test fixture only, not a production BE2-07 fence.

An invalidator may update its fence rows and commit, then start a new BE2-01 UoW for a paired job/run action. It must not keep a fence lock and then acquire job/run rows in the same transaction. Prove both PostgreSQL two-session winner orders before claiming a durable fence.

The BE2-08 creation lease is a separate logical guard outside A, not an enlisted row. Outbox publish commits its claim before broker I/O; its logical delivery lease may remain active, but no SQL row lock or transaction remains open over publish. BE2-14 accounting remains in a separate transaction and must not be nested while lifecycle locks are held.

## 7. Persisted job → run → pin field mapping

Start from the locked foundation job, then resolve one BE2-08 run by organization_id + job_id using a required locked get-by-job participant accessor. The current accessor does not exist. Compare fields without inventing equivalences:

| Foundation value | BE2-08 value | Rule |
|---|---|---|
| job.organization_id | VideoPin.organization_id | Exact equality. |
| job.scope.session_id | VideoPin.session_id | Exact equality required. A null foundation session_id fails closed because VideoPin requires a session. |
| active attempt_id | VideoRun.attempt_id | Equal only after S. Before S, including retry-queued state, VideoRun.attempt_id is null. |
| active attempt_number | No VideoRun field | Foundation-only. Do not claim it is stored on VideoRun. |
| RequestRef.context_revision | VideoPin.context_revision | Exact equality. |
| RequestRef.request_id / request_revision | No direct VideoPin field | Require an adopted persisted linkage or versioned CR; do not infer from pin_digest or video_id. |
| RequestRef.input_hash | No direct VideoPin field | Require an adopted persisted linkage or CR; do not equate to pin digest or artifact hash. |
| RequestRef.target_id / purpose_code / subject_refs | Video id, pin sources, or policy fields are not proven equivalent by current source | Define field-level mapping in an owner-approved contract or fail closed. |
| exact source bundle/version/hash and source refs | VideoPin.bundle and VideoPin.sources | Exact ref/version/hash and audience/context identity must be compared using the adopted canonical encoding. |
| foundation command/semantic receipt identity | BE2-08 submission receipt and session/pin index | Compare explicit persisted fields and body fingerprint. Distinct keys do not become equivalent through naming. |

WorkerDispatchEnvelope remains unchanged. A missing session, missing run, duplicate run, unmapped field, mismatched identity, or unrecoverable receipt keeps X09-08 NOT_IMPLEMENTED.

## 8. Source-fence inventory and X01

The required inventory includes bundle head/version/hash, basis/context, audience revision, policy reference and epoch, catalog claims, source record identity/version/hash, editorial_revision, rights, kill switch, execution authorization, content/encoding/model profiles, library asset, retry-policy identity, and final artifact descriptor/hash.

For every input the adopting owner must name the persisted key, every invalidation writer, lock/CAS behavior, and database/connection used through B. Specific corrections from rereview 2:

- ArtifactDescriptor.fence belongs to the BE1 artifacts owner port. FEAT-057 must not assign this fence to BE2-01 or BE2-08.
- VideoPin.editorial_revision is a separate pinned field. Its authoritative source owner and every writer that can advance/revoke it remain to be named by the owning card.
- owner_fence_fixture.py is pinned for this review. Its sorted fixture locks are an ASSUMED_CONTRACT test pattern only and do not establish a production BE2-07 fence.

A durable fence is admissible only if finalization and all relevant invalidators use the same PostgreSQL rows/connection protocol: finalization locks the complete fence set FOR SHARE through commit; invalidators lock the same rows FOR UPDATE or CAS the same monotonic epoch. Job and run locks precede fence locks. An invalidator needing paired lifecycle work commits the fence update first, then opens a new BE2-01 UoW.

Current BE2-07 resolve_exact opens its own transaction and its approved scope has no shared SQL store/fence. Foundation OwnerFencePort has no production binding. Therefore X01 remains PARTIAL. A reread, process-local coordinator, or fixture lock is not a substitute. This commit-time fence does not close X05d or implement X02.

## 9. Rejection identity and finalization recovery

Accepted B recovery uses the persisted foundation completion receipt keyed by job_id/attempt_id and must compare its receipt identity/fingerprint/disposition to the exact accepted run_json artifact. The completion_key is not stored in that receipt. It may be recomputed only from persisted and authenticated inputs equivalent to the current canonical completion-key inputs: attempt/run identity, pin digest, media operation/blob hash, staging identity, and artifact material. If any input is missing or ambiguous, fail closed or prepare a versioned CR; do not add a column/table under this scope.

Rejected, stale, or intent-only outcomes do not necessarily have an artifact in the run and must not be recovered by exact artifact comparison. Use the persisted disposition/fingerprint and deterministic effect identity. For an intent-only reject, query side_effect_recorded(event_id). The quarantine event id currently derives from kind, job_id, attempt_id, sorted artifact_refs, reason, and claim fingerprint. If the fingerprint cannot be reconstructed after a worker crash, no recovery is claimed until a CR adds a durable input.

When B discovers a non-accepted result, it performs no accepted/finalization mutation. F-reject re-evaluates under fresh job/run locks and commits state/intent atomically in its own transaction. If B infrastructure rollback occurs, a new UoW must first establish whether B committed. Never use rollback as a business-rejection mechanism, never rerender on timeout alone, and never report cleanup handled before the durable intent exists.

## 10. Adapter ownership, API, and conflict recovery

- BE2-01 owns the foundation UoW provider and public transaction-scoped enlist/start/reject API.
- BE2-08 owns VideoRunRows, codec, and video domain transitions, including fail/retry/timeout and the D2 stale terminal contract after its CR is approved.
- FEAT-057 owns cross-lane composition adapters and integration evidence only under a reviewed supplemental scope.
- No application protocol exposes a SQLAlchemy connection; the participant cannot control transaction lifecycle.
- VIDEO_WRITE_CONFLICT and participant CAS failures such as VIDEO_STALE_RUN require whole-UoW rollback before any reread. The fresh UoW classifies a same-winner replay, stale state, or conflicting winner. Do not treat every stale CAS as a unique conflict or continue in an aborted transaction.
- VIDEO_IMMUTABLE_LINEAGE and VIDEO_TERMINAL_RUN also abort the attempted paired mutation; authoritative reread is required before deciding replay versus fail-closed conflict.
- Public get-by-job, participant methods, retries and recovery APIs remain candidate contracts, not implemented adoption.

## 11. BE2-08 → BE2-09 read model and BE2-14 policy boundary

The BE2-08 artifact read model is a separate owning-card scope. It must expose a versioned public receipt provenance route and never query foundation tables directly. The current BE2-08 scope candidate hash is recorded above. The existing artifact-read supplement still references older scope material and is intentionally not changed until this UoW scope passes independent review.

If the owners choose an opaque receipt reference written at B, the CR must update and test FinalArtifact, VideoRun persistence/codec, and the worker’s completed-run equality check, which currently constructs an expected run without that field. If the owners choose a BE2-01 read-only receipt lookup composed by FEAT-057, specify lookup authorization, receipt fields, visibility, read-after-commit, exact artifact/source identity, and superseded/stale behavior. VideoRun currently has no superseded state. The decision remains open; X05d stays BLOCKED and X05c/CR09-02 stays OPEN.

BE2-14 gates are separate:

- Current-use eligibility is not worker/provider authorization.
- Execution authorization is not budget reservation or concurrency accounting.
- A budget reservation denial must not be returned as an eligibility denial that triggers permanent cancellation in _dispatch_one, start_attempt, or retry_job.
- No budget unit, limit, expiry, renewal, or settlement policy is assumed. The owner will provide unit and limit separately; expiry/renewal requires a versioned CR.
- Until BE2-14 adopts a non-terminal budget-denial/defer contract, budget-dependent execution stays disabled and pending. Do not invent synthetic values or a provider grant.

## 12. Candidate acceptance evidence and open gates

| ID | Required evidence |
|---|---|
| U01 | BE2-01 alone owns UoW lifecycle; negative tests prove participant cannot begin/commit/rollback or write foreign rows. |
| U02 | Writer inventory covers A/S/B/F, both eligibility-denial cancellation writers, notices, retry, timeout, dispatch loss, progress-only, and delivery-only paths. |
| U03 | State mapping covers dispatch loss with retry remaining/exhausted, started retryable/non-retryable failure, retry clearing attempt_id until S, cancellation, unsafe, malformed, stale, and temporary outcomes. Foundation policy is authoritative; VideoPin mapping is explicit. |
| U04 | A proves semantic-index comparison, retry-policy mapping, atomic create, split-winner failure, full rollback and fresh-UoW replay. |
| U05 | S binds only the active attempt id; denied, duplicate, inactive and not-queued outcomes fail closed without provider invocation. |
| U06 | B accepted and F-reject are separate commits; B non-acceptance makes no mutation; reject event identity is deterministic and intent-only recovery uses side_effect_recorded(event_id). |
| U07 | Accepted receipt recovery verifies the exact artifact; rejected/stale recovery uses disposition/fingerprint and no nonexistent artifact. completion_key is recomputed only from persisted inputs or fails closed. |
| U08 | Reconciler, cancellation notices, retry, timeout and dispatch-loss use paired transitions; jobs_for_notice lock path is revised to pair-by-pair; stale participant CAS rolls back before reread. |
| U09 | Job → run → sorted-fence order and named A/create/notice exceptions are proven; PostgreSQL two-session tests cover invalidation-first and finalization-first before any durable-fence claim. |
| U10 | Persisted field mapping covers every RequestRef/JobScope to VideoPin field; null session, unmapped IDs, ambiguous run or identity mismatch fail closed. |
| U11 | BE2-08 read model is separately adopted; receipt provenance and any opaque ref impacts on FinalArtifact/VideoRun/codec/equality are tested; BE2-09 remains read-only. |
| U12 | BE2-14 eligibility, execution authorization, and budget/concurrency are separate; budget denial cannot cancel via eligibility; no invented value or expiry. |
| U13 | Unit/fake results are protocol evidence only. SQL/PostgreSQL/provider/Modal/Lightning/runtime remain NOT_RUN unless separately authorized. |
| U14 | No card acceptance/status changes; X01 PARTIAL, X05d BLOCKED, X05c/CR09-02 OPEN, X09-08 NOT_IMPLEMENTED. |

Before supplemental implementation approval, resolve: the BE2-08 STALE contract CR; exact retry-policy mapping; durable reject crash input; every RequestRef field without a pin counterpart; source-fence owner/key/invalidation writers; the public receipt-provenance choice; BE2-14 non-terminal budget behavior; whole-UoW replay for participant CAS conflicts; and the notice lock path. These remain blockers, not implicit approval.

## 13. Independent-review crosswalk and next gate

Claude rereview 2 findings are handled as follows:

- F-01: corrected failure/dispatch-loss/retry mapping; D2 stale terminal direction recorded, with the required BE2-08 CR left open.
- F-02: added _dispatch_one and retry_job eligibility-denial cancellation writers.
- F-03: D2 says only S binds attempt_id; retry clears the old run id; attempt number remains foundation-only.
- F-04: separate accepted-artifact recovery from stale/rejected/intent-only recovery; completion_key is recomputed only from persisted inputs.
- F-05: B does not mutate on non-accepted result; separate reject UoW re-evaluates. Intent-only recovery checks event_id, not a paired receipt. Crash before durable identity remains blocked.
- F-06: names jobs_for_notice, create_job, caller-order fence hold, and sorted fixture; does not call the notice path a proven deadlock.
- F-07: assigns ArtifactDescriptor fence to BE1 owner port, adds editorial_revision, limits fixture to ASSUMED_CONTRACT.
- F-08: adds field-by-field map and CR/fail-closed treatment for unpaired fields.
- F-09: successor plan Rev6 must explicitly crosswalk the divergence list in the review report.
- F-10: preserves BE2-08 supplement until review passes; records impacts if opaque receipt ref is selected.
- F-11: rolls back whole UoW on VIDEO_STALE_RUN and participant CAS errors, then rereads in a new UoW.
- N-01: status no longer says all findings are addressed; only CHANGES_ADDRESSED_PENDING_INDEPENDENT_REREVIEW.
- N-02: budget is not an eligibility denial; no denial may permanently cancel through that path.

This scope is ready for independent rereview only. A/S/F still require separate supplemental approvals and exact card manifests. Do not update existing approval records or the index’s governing accepted-plan fields until review passes and the owner authorizes that administrative transition. X01 remains PARTIAL; X05d BLOCKED; X05c/CR09-02 OPEN; X09-08 NOT_IMPLEMENTED. No tests, Modal, Lightning, provider, server, database, or runtime are authorized or claimed.
