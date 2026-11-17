# Cross-lane budget-deferral contract CR — revision 2 draft 2026-10-21

- Status: DRAFT / READY_FOR_INDEPENDENT_CONTRACT_REVIEW; not adopted or approved for implementation.
- Owning contracts: joint BE2-01 / BE2-14; BE2-01 owns lifecycle transitions and UoWs, BE2-08 is a video-row participant, FEAT-057 owns composition under its own scope.
- Authority: owner D3 C1-A in FEAT-057 `evidence/notes/CROSS_LANE_UOW_OWNER_DECISION_D3_20261021.md`. D1/D2 continue to apply. The elaborations below are candidates for review, not additional inferred owner choices.
- Source baseline: `features/FEAT-057-be2-01-14-offline-integration/evidence/metrics/CROSS_LANE_UOW_SOURCE_HASHES_REV4_20261021.json`, SHA256 `2EAA11FCA7B510CA738D34ECED9EFD164C7734FCA8E6AD4792257F03AA68591F`.
- Branch / HEAD at preparation: `feature/be2-backend-ai-integration` / `1649b72978877d82b4d7662040ff3555dee0a3a7`; existing dirty checkout is not an approved implementation.
- Schema companion: `CROSS_LANE_BUDGET_DEFERRAL_SCHEMA_CR_DRAFT_20261021.md`. No table, migration, source, test, or approval is changed by these drafts.

## 1. Source facts and the selected waiting invariant

Current BE2-01 `_dispatch_one`, `start_attempt`, and `retry_job` cancel on eligibility denial, including `BUDGET_EXCEEDED`. The current unstarted-dispatch reconciler republishes queued attempts and eventually records `DISPATCH_LOST`. Outbox claim increments `publish_attempts`; acknowledgement increments `attempt.dispatch_count` and replaces `dispatched_at`. Keeping an unmarked queued job is therefore insufficient.

Owner D3 requires BOTH foundation job and paired video run to be QUEUED while budget-deferred. There is no new JobState or video budget state. BE2-01 persists a separate execution-deferral record. A run queued under D2 has `attempt_id=None`; the foundation keeps its active unstarted attempt. Only S may bind that id to the run. A predecessor FAILED_RETRYABLE row is not retained as the authoritative waiting state.

Budget waiting itself never closes an attempt, records provider failure/dispatch loss, allocates repeated retry attempts, or consumes effective dispatch-recovery allowance. Normal retry caps and immutable history remain authoritative. D3 supplies no numeric upper bound or action at that bound; both remain PENDING and execution cannot claim a complete bounded-wait policy.

## 2. Authority and denial classes

BE2-14 supplies a versioned deny/defer resource-admission contract only within this scope. Its observation is neither current-use eligibility nor worker/provider execution authority, and is not a grant to call a provider. Units, limits, amounts, expiry, renewal, numeric ceilings and authorization cannot be inferred from this CR.

Consent/session/source/kill-switch eligibility denial retains its authoritative paired cancellation path. Only the typed budget/resource deferral outcome uses this CR. Unknown identity, incompatible resource definition, unavailable authority/proof, missing contract adoption, and corrupt data fail closed as pending/error; they are not fabricated budget depletion or consent revocation. The exact mapping from BE2-14 error vocabulary to BE2-01 `BUDGET_EXCEEDED`/defer must be versioned and jointly adopted.

## 3. Phase and state transitions

| Entry | Candidate BE2-01-owned UoW | Persisted result while waiting | Repeated delivery |
|---|---|---|---|
| Dispatch detects budget deferral | Lock current job and paired run, recheck queued active attempt and exact identities, persist the hold and generation, park/invalidate applicable outbox delivery leases. | Job QUEUED; run QUEUED with no attempt id; same foundation attempt, no provider start. | Return the same hold observation after exact input comparison; no new attempt or dispatch count. |
| S admission detects budget deferral | Under current job/run locks, prove no S winner, persist hold and invalidate/park outstanding recovery/delivery work. | Job/run QUEUED; foundation active attempt remains unstarted; run id remains null. | Same hold; no RUNNING transition, no provider work. |
| Due retry detects budget deferral | Recheck normal `_retry_due`, current eligibility and remaining ordinary retry cap. In ONE paired UoW perform normal requeue exactly once, create the one next foundation attempt, put run QUEUED with id cleared, and persist a hold bound to that NEW attempt. Do not publish held work. | Job/run QUEUED; predecessor attempt remains finished in immutable history; new attempt is unstarted and held. | Old scheduled callback is no longer due because job is queued; exact replay returns existing held new attempt. It cannot allocate another attempt. |
| Resume held work | Resolve the persisted hold and exact current job/attempt/generation; revalidate current eligibility and required exact reservation evidence outside lifecycle locks, then verify the adopted held proof under the short paired acceptance UoW. Close the hold as RESUMED and install/reuse a single current recovery epoch/dispatch intent. | Job/run stay QUEUED until S wins; no retry requeue here. Provider authorization remains separately required. | Replay the persisted resume winner. No second outbox intent or new attempt. |
| Consent/kill cancellation or other authoritative terminal winner | Use the ordinary paired lifecycle UoW and atomically close the active hold, invalidating resume and outstanding delivery generations. | Paired CANCELLED/other legitimate winner, never a budget-specific state. | Late resume/dispatch/retry is a no-op or typed conflict after authoritative lookup. |

The retry elaboration reconciles D3's both-QUEUED rule with normal retry history; it requires independent review. Allocating the one normally due next attempt is not unlimited free retries. Waiting cannot consume any further attempt. If the preceding failure already exhausted the normal cap, retry cannot enter this path or create an extra attempt.

For retry deferral, any reservation/proof for the finished predecessor attempt is INVALID for the held new attempt. Quote/reserve, when separately adopted and configured, binds the NEW persisted active attempt before S. No reservation service call occurs inside the retry UoW. If no proof exists yet, keep the new attempt queued/held and execute no provider. Existing accounting phases are `create|dispatch|retry`; S must use an explicit adopted mapping or a versioned phase CR, never an invented `start` value.

## 4. Deferral ends, resume, and pending upper bound

An active deferral ends only by a persisted RESUMED winner after exact adopted checks, or by a persisted CLOSED winner for a legitimate authoritative cancellation/terminal lifecycle. A response lost after that commit replays that winner. A failed or ambiguous resume leaves the hold active/pending, not silently ended.

Resume is an explicitly authorized command or adopted resource-admission event, never an unapproved periodic scheduler. Eligibility and reservation evidence are rechecked; stale resource observations or a grant for a different attempt do not end waiting. Eligibility denial at resume may cancel through F. Resource denial keeps the same hold active. Execution authority must be checked independently before S/provider; this CR creates none.

Upper-bound number, what is counted, owner of the bound, and the lifecycle action when the bound is reached remain PENDING. Do not substitute `max_attempts`, `max_publishes`, attempt timeout, a UI poll hint, a synthetic TTL, or reservation expiry. The definition and terminal action need a separately reviewed owner decision; no automatic permanent budget cancellation is authorized here.

## 5. Delivery, timers, counters and recovery

All dispatcher/recovery query filters are optimizations. Each mutation rechecks hold, active attempt and generation under the BE2-01-owned paired job/run UoW. A preselected row is not authorization to publish, start, retry or record loss.

- `claim_outbox` excludes held work; begin-defer parks or invalidates already claimed leases. Waiting cannot create repeated claim increments or broker publishes.
- `_dispatch_one` rechecks held state after lease and job/run acquisition. A publish already racing outside SQL can still physically deliver; S checks persisted admission, and no provider executes while held.
- `ack_dispatch` uses the current lease and recovery generation while holding the parent job. An obsolete or held acknowledgement cannot increase effective dispatch counts, refresh a start timer, or undo a hold. Retain any physical publication history truthfully; acknowledgement is not proof S ran.
- `_recover_unstarted` and `queued_dispatched_not_started` exclude an active hold in both selection and locked recheck. Deferred elapsed time cannot lead to `record_dispatch_loss` or failure. `run_due_retries`/`retry_job` cannot allocate a further attempt for queued held work.
- Persist a recovery epoch or an equivalent reviewed pause protocol. On resume, use a new current watchdog window that excludes wait time and resource-denied delivery from effective exhaustion; preserve lifetime publication history and completed prior attempts. No blind reset of historical counters.
- Old recovery callbacks, leases and acks cannot mutate a newer epoch. Existing envelope and start capability contain no recovery epoch; do not claim otherwise. A same-active-attempt old physical delivery may proceed ONLY after current persisted eligibility, separate execution authority and exact reservation admission permit the single S CAS. If strict generation-bound delivery rejection is wanted, a versioned admission binding is an additional gate.
- `expire_overdue_attempts` applies only after a real RUNNING/S winner. No start/attempt timer is invented while held; S writes its actual start time. Legitimate failure after S uses the ordinary retry policy.

Lost-ack lookup compares persisted operation identity, fingerprint, job/attempt, hold revision/generation and the exact paired winner in a fresh UoW. It never infers a refund, extra attempt, rerender or provider execution from a timeout. Crash before durable hold/resume outcome is an unresolved operation until authoritative lookup succeeds. A later scan of persisted active holds may expose work for an adopted recovery operator; this CR does not add a scheduler.

## 6. Transactions, accounting and reservation safety

BE2-01 alone begins/commits/rolls back lifecycle UoWs. BE2-08 only mutates its video rows. Lock job then paired run, then reviewed foundation-owned hold/dispatch bookkeeping before the complete sorted source-fence set. Multi-job lock protocol and outbox claim exceptions require explicit shared-UoW review; a participant may not add late fences.

Accounting remains in its own transaction outside job/run locks. A versioned handoff must define exact reservation identity/attempt/definition, validity through S, invalidation and lost-ack recovery without holding one owner's lock while calling another transaction. Current ledger snapshots do not authorize execution. If handoff validity cannot be proven, keep the hold pending. Unknown execution or reservation outcome is not terminal evidence and cannot release/refund, consume invented usage, or authorize another provider run. Expiry/renewal is a separate versioned CR.

## 7. Candidate affected source and owning-card manifests

BE2-01 source candidates: `backend/src/sketch2life/application/services/ai_jobs.py`; `application/ports/ai_jobs.py`; `domain/ai_jobs/model.py` only for an explicitly reviewed auxiliary deferral/domain protocol, never a new JobState; `infrastructure/ai_jobs/sql/repository.py`; `infrastructure/ai_jobs/sql/tables.py`; `infrastructure/ai_jobs/fakes.py`; `infrastructure/ai_jobs/reconciler.py` and `outbox_dispatcher.py` only if their adopted command/result wiring changes. Every path after the first is relative to `backend/src/sketch2life/`. New schema/migration paths require the companion schema CR and exact reviewed manifest; never edit a published migration.

BE2-08 candidates under its own successor scope: `domain/knowledge_video/model.py`; `application/ports/knowledge_video.py` and `knowledge_video_worker.py`; `application/knowledge_video_worker.py`; `infrastructure/knowledge_video/sql.py` and `codec.py`; exact create/retry participant paths named by the S/F review. No video budget state. FEAT-057 composition adapter paths are proposed/new unless verified to exist.

BE2-14 primary deny/defer candidate paths: backend/src/sketch2life/contracts/schemas/ai_policy_use.py; backend/src/sketch2life/application/ports/ai_policy_use.py; backend/src/sketch2life/application/ai_policy_use.py. Conditional reservation/phase inputs only: backend/src/sketch2life/contracts/schemas/ai_policy_accounting.py and backend/src/sketch2life/application/ports/ai_policy_accounting.py, if a separately adopted scope requires them. Settlement/accounting remains outside this CR.

## 8. Required evidence, not run

| ID | Future evidence before claiming the behavior |
|---|---|
| BD01 | All three budget branches produce paired QUEUED hold, while real consent/kill denial still cancels. |
| BD02 | Due retry atomically creates exactly one normal next attempt plus queued unbound run and hold; repeated callbacks/restarts create no extra attempt; cap/history preserved. |
| BD03 | Deferred wall time cannot trigger dispatch loss, retry consumption, hot claim/publish or attempt timeout; counters preserve honest history. |
| BD04 | Defer versus late ack/publish/start, and resume versus cancel, prove both winner orders; obsolete generations cannot spend current recovery allowance. |
| BD05 | Old-attempt reservation, mismatched definition and unknown outcome fail closed; current-attempt admission before S is required; accounting is never called under lifecycle locks. |
| BD06 | Lost-ack/restart resume replays exact persisted winner; cancelled hold never resumes; no duplicate provider execution or fabricated refund. |
| BD07 | Pending bound and action, expiry/renewal, policy mapping and execution authority remain explicit gates; no numeric default or new state slips into contracts. |

Candidate existing test paths: `backend/tests/unit/test_ai_job_application.py`; `test_ai_job_b4_dispatch.py`; `test_ai_job_lifecycle.py`; `test_ai_job_video_dispatch.py`; `test_ai_policy_accounting_service.py`; `test_knowledge_video_worker.py`; `test_knowledge_video_create.py` (unit directory for unqualified names). SQL/race/schema candidates: `backend/tests/integration/ai_jobs/test_dispatch_recovery.py`, `test_outbox_dispatch.py`, `test_restart_recovery.py`, `test_notice_coverage.py`, `test_migrations.py`; future cross-lane hold/resume suite under its exact supplemental manifest. Contract tests require explicit versioned changes. These are future review targets, not executed tests or current coverage claims.

## 9. Review and approval gate

Review this contract and the schema companion with BE2-01/14 and BE2-08 participation, resolve the numeric-bound/action and exact reservation/phase contracts, then obtain separate supplemental S/F and schema-specific approval before implementation. Owner D3 selected direction, not code or migration approval. X01 remains PARTIAL; X05d BLOCKED; X05c/CR09-02 OPEN; X09-08 NOT_IMPLEMENTED. SQL/database/provider/server/Modal/Lightning/runtime remain deferred.

### Rereview 4: completion-time resource result is a separate owner gate

D3 selected defer in the dispatch, start and retry branches. It did not decide the result when provider work has already completed and completion-time policy returns only BUDGET_EXCEEDED. The generic current source branch treats any ineligible result as cancel plus quarantine; that behavior is not adopted by D3 for resource-only completion denial.

Until the owner/card contract decides this case, do not classify completion-time BUDGET_EXCEEDED as consent/kill revocation, F-reject or the pre-execution C1 hold. Its paired state, receipt, durable recovery, output visibility and settlement remain PENDING under the D4 ballot. No implementation may infer cancellation/quarantine, acceptance/settlement, refund, retry or provider rerun from that resource result. Recommended option A is to keep output private and completion pending; this recommendation is not owner-approved behavior.

### Rereview 4: aligned BE2-14 candidate paths

This section replaces the earlier candidate-path split in Section 7. The primary deny/defer paths under BE2-14 are backend/src/sketch2life/contracts/schemas/ai_policy_use.py, backend/src/sketch2life/application/ports/ai_policy_use.py, and backend/src/sketch2life/application/ai_policy_use.py. The accounting schema/port at backend/src/sketch2life/contracts/schemas/ai_policy_accounting.py and backend/src/sketch2life/application/ports/ai_policy_accounting.py are conditional review inputs only if a separately adopted reservation/phase contract requires them. This joint CR does not change settlement/accounting or call it inside lifecycle locks. The BE2-14 successor uses the same split. Freeze exact paths only after review and approval.
