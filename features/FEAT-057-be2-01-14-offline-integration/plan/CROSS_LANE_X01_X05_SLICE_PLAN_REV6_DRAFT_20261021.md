# FEAT-057 BE2-01–14 cross-lane X01/X05 slice plan — revision 6 draft

- Status: DRAFT / OWNER_DECISIONS_RECORDED / CHANGES_ADDRESSED_PENDING_INDEPENDENT_REREVIEW
- Revision: 6
- Feature: FEAT-057 offline cross-lane integration
- Candidate branch/HEAD: feature/be2-backend-ai-integration / 1649b72978877d82b4d7662040ff3555dee0a3a7
- Prepared: 2026-10-21 (Asia/Saigon)
- Worktree is dirty; exact source bytes are pinned by source manifest revision 3.
- Successor BE2-01 scope: CROSS_LANE_FOUNDATION_UOW_SCOPE_REV5_DRAFT_20261021.md
  SHA256: 8BCAD75E2E505053465349E1B93800626B494B6D1076561B437298A1E60A4EF4
- Parent FEAT-057 plan Rev5 SHA256: 423E1058317B63F7354E1DAC398D0B1D9AEDE7FAD0C3DCB786C41AB5FD263BE3
- Claude rereview 2 report SHA256: 7A78475A0E8CE4A71C90E9F7019DA13DEB790C6EF4EB8F7B8CA2CA01DE535611
- Source manifest revision 3 SHA256: 8BC0998D505742C460FDCBE9EDDF98CBC327D41B118CF2A50E921C965D6C7342

This is a review successor to FEAT-057 plan revision 5. It does not modify the historical Rev4 plan, Erratum 1, Rev5 draft, or any card approval. It is design documentation only; it is not implementation approval, contract adoption, card acceptance, test authorization, or runtime evidence.

## 1. Owner decisions and authority

Owner D1 selects BE2-01-owned UoWs for paired A/S/B/F and reject transitions, BE2-08 as a non-committing participant, a separate reject commit, job → run → sorted source-fence target order, and unchanged WorkerDispatchEnvelope.

Owner D2 now fixes two additional design choices:

- A foundation result with JobState SUCCEEDED and ResultDisposition.STALE receives a distinct terminal stale representation on the BE2-08 video-run lifecycle axis, with no artifact and no ready-for-review state. This requires a versioned BE2-08 CR; it does not add STALE to foundation JobState or authorize source/schema changes.
- VideoRun attempt_id is bound only at S. Retry returns the video run to QUEUED with the previous attempt_id cleared. Attempt number remains foundation-owned.

These decisions do not adopt contracts. Keep X01 PARTIAL, X05d BLOCKED, X05c/CR09-02 OPEN, X09-08 NOT_IMPLEMENTED. S/F still require independent review, exact file manifests, and separate supplemental approvals in owning card records. The owner has not supplied budget unit or limit. ENV/Modal remains deferred until a separate resume instruction.

## 2. Scope and current evidence boundary

The plan covers offline design and future composition of BE2-01/07/08/09/14. It distinguishes:

- A: atomic submission;
- S: worker admission/start;
- B: accepted successful finalization after external work;
- F: failure, cancellation, timeout, retry, dispatch-loss reconciliation;
- F-reject: a distinct foundation commit for business/policy rejection and durable quarantine/cleanup intent.

External generation is between commits; no UoW spans provider or media work. FEAT-057 owns only the cross-lane composition adapter and evidence under its own later approval. Card-owned APIs, rows, codecs, migrations, and worker transitions remain with their owning cards.

The existing Modal receipt is limited to the pinned X01 plus adjacent BE2-07/08 offline suite: 296 passed, 0 failed, 0 skipped on the source ZIP recorded in FEAT-057 evidence. It does not prove all BE2-01–14, durable PostgreSQL fencing, or BE1 integration. No test is run or newly authorized by this plan.

## 3. Consolidated lifecycle requirements

| Boundary | Owner and caller | Required atomic behavior | Remaining gate |
|---|---|---|---|
| A — submit | BE2-01 opens the UoW; BE2-08 create joins. Creation lease is separate. | Create/replay foundation job, initial attempt, semantic/command receipts, outbox/audit and BE2-08 queued run/submission receipt under one organization/job identity. Initial run has no attempt_id. Compare both semantic indexes and exact retry-policy mapping. | Public enlist API, field mappings, retry-policy CR, split-winner rollback and fresh-UoW replay need adoption. |
| S — start | BE2-01 start API called only by VideoWorkerAdmission.begin; BE2-08 participates. | CAS queued job/run to running together. Bind the exact foundation active attempt_id to the video run only at this commit. Eligibility denial that cancels a job also cancels the run. | S supplemental review/approval; no provider call before committed admission. |
| B — accepted finalization | BE2-01 owns commit; BE2-08 finalizer participates after external work. | Commit accepted job outcome, exact run artifact and foundation completion receipt atomically. | Recover by job/attempt receipt plus exact persisted artifact; completion_key has no receipt column. Same-store source fence remains absent; X01 stays PARTIAL. |
| B declines non-accepted result | B must not mutate job/run or write rejection intent. It exits, then calls separate F-reject. | F-reject locks and rereads job/run and current facts, makes the rejection decision again, then commits permitted paired state plus deterministic intent. | Requires a durable, reconstructable rejection identity and crash recovery before intent commit. |
| F — lifecycle updates | BE2-01 owns; API/worker/reconciler/notice/dispatch recovery routes through it; BE2-08 participates. | Pair all job/run state changes. Foundation retry policy decides retryable/exhausted. Retry clears VideoRun attempt_id; only S binds the next attempt id. Include dispatch-denial and retry-denial cancellation writers. | F supplemental review/approval; revise multi-job notice lock path and classify participant CAS failures via full rollback and fresh read. |
| F-reject | Separate BE2-01 UoW; BE2-08 mutates only its own run if its state changes. | Durable quarantine/cleanup intent shares the reject commit. Deterministic event_id uses persisted job, attempt, sorted artifact refs, reason, and claim fingerprint. | Intent-only lost-ack checks side_effect_recorded(event_id); no paired completion receipt is assumed. Crash before durable identity remains blocked. |

The detailed mapping, field-by-field identity rules, source-fence owner inventory, lock exceptions, recovery, card boundaries, and evidence criteria are in the paired FEAT-044 scope Rev5. Its unresolved gates remain open and are not silently adopted by this plan.

## 4. State, identity, lock, and policy constraints

- Foundation job state is authoritative. Foundation record_failure and record_dispatch_loss use the persisted job retry policy; BE2-08 mirrors the result. VideoPin.retry_policy is a separate pinned ref and needs an explicit versioned mapping or A fails closed.
- record_dispatch_loss can produce failed_retryable or failed_exhausted from queued. Started failure/timeout can also exhaust on the final attempt. Both cases are included; BE2-10 is not incorrectly named as the runtime state writer.
- A stale successful foundation result maps to the D2 stale terminal direction only after a BE2-08 CR changes and tests the model, codec, persistence, worker receipt, and cleanup/recovery behavior. No accepted artifact is exposed.
- Persisted lookup starts from organization_id + job_id. Compare fields explicitly. Null foundation session_id, missing run, unpaired request identifiers, or ambiguous source pin fail closed. Do not add run/source identity to WorkerDispatchEnvelope.
- Target row-lock order is job → paired run → canonically sorted fence rows; process multi-job transitions pair-by-pair. Current jobs_for_notice locks all matching jobs before rereading them; this is an identified conformance gap, not a proven deadlock. create_job's pre-insert fence hold is a named A-only exception. The creation lease and outbox delivery lease are logical leases, not transaction row locks.
- Every fence input needs an owner, persisted key, invalidator, and same-store lock/CAS. ArtifactDescriptor.fence belongs to the BE1 artifacts port. editorial_revision is a distinct input whose authoritative owner and writers remain to be identified. The sorted owner-fence fixture is only ASSUMED_CONTRACT test code.
- BE2-14 current eligibility, execution authorization, and budget/concurrency remain separate. BUDGET_EXCEEDED must not be routed through an eligibility branch that permanently cancels job/run. Until a non-terminal budget-denial/defer contract is adopted, budget-dependent execution remains disabled. No unit, limit, expiry, renewal, or synthetic value is assumed.

## 5. BE2-08 → BE2-09 read model

The public artifact read model is a separate BE2-08 scope. It must expose versioned receipt provenance without direct foundation-table reads and specify identity, visibility, read-after-commit, and stale/superseded behavior. The current VideoRun has no superseded state.

If an opaque receipt reference is chosen, the owning CR must account for its effect on FinalArtifact, VideoRun, codec persistence, and the worker's completed-run equality check. If a BE2-01 read-only receipt lookup is chosen, its authorization, returned receipt fields, and FEAT-057 composition are explicit. The existing supplement remains unchanged until the UoW scope passes review; then update it to cite scope Rev5 and this plan Rev6 and settle the listed contract choices. X05d and X05c/CR09-02 remain open.

## 6. Specific corrections from Claude rereview 2

This successor closes documentation gaps while preserving unresolved contracts:

- F-01: adds retryable/exhausted dispatch loss, final-attempt failure/timeout, foundation-owned retry decision, explicit policy mapping, D2 stale terminal direction, and the required BE2-08 CR.
- F-02: adds _dispatch_one eligibility-denial cancellation and retry_job eligibility-denial cancellation; only _publish/ack/delivery with no job-state mutation is exempt.
- F-03: D2 resolves the inconsistency: S alone binds attempt_id; retry clears it; attempt number is foundation-only.
- F-04: accepted recovery verifies exact artifact; stale/rejected/intent-only recovery uses disposition/fingerprint and does not require a nonexistent artifact. completion_key is recomputed only from authenticated persisted inputs or fails closed.
- F-05: B makes no mutation when it detects non-acceptance; F-reject re-evaluates in its own UoW. Intent-only recovery uses side_effect_recorded(event_id); missing crash-recovery input remains a blocker.
- F-06: names jobs_for_notice, create_job's A-only pre-insert fence, caller-order hold_owner_fences, and the sorted fixture. No unproven deadlock claim is made.
- F-07: assigns ArtifactDescriptor fence to the BE1 artifacts port, adds editorial_revision, and labels the fixture ASSUMED_CONTRACT.
- F-08: adds paired/unpaired field mapping and fail-closed/versioned-CR treatment; null session_id fails closed.
- F-09: this section explicitly enumerates revision/erratum divergence and source-manifest correction; see section 7.
- F-10: keeps the BE2-08 supplement untouched pending scope review, and names the VideoRun/codec/equality impact if opaque receipt ref is selected.
- F-11: whole-UoW rollback also covers VIDEO_STALE_RUN and participant CAS errors; fresh transaction classifies replay or conflict.
- N-01: no claim that all findings are fully closed; status remains pending independent rereview.
- N-02: budget reservation is not an eligibility denial and cannot trigger permanent cancellation.

## 7. Exact revision/erratum divergence log

Plan Rev4 and Erratum 1 are immutable history. Plan Rev5 is also preserved byte-for-byte. The reviewed Rev4 scope, Erratum 1, and Rev5 plan were checked against these precise corrections:

1. Rev4 X09-08 wording that no typed registration/adopter exists is superseded by the dirty-tree candidate typed_dispatch route and DispatchWorker video branch. The route currently calls the video target without start_attempt; S is still missing, persisted job→run→pin mapping is unproved, and X09-08 remains NOT_IMPLEMENTED.
2. Rev4 header's “after the X01 Modal rerun” is historical sequencing only. This plan does not authorize a Modal rerun. PostgreSQL two-session race tests remain a separate gated environment step; no location is represented as run or approved.
3. G0's earlier PASS was a design-direction review only. The later lifecycle reviews returned CHANGES_REQUIRED; G0 is not evidence that Rev4/Rev5 passed current independent review.
4. Erratum 1 cites source manifest revision 1 as historical. Current source checks use manifest revision 3, which pins 19 files including owner_fence_fixture.py.
5. Erratum G3's creation-lease wording is corrected: creation lease is outside the row-lock order and outside A's atomic rows. It is a logical guard.
6. Receipt provenance is sourced to the BE2-08 artifact-read supplement, not to a clause in the earlier FEAT-057 plan.
7. Avoid brittle source line numbers. Cite pinned file paths and function/type names; exact bytes are in manifest revision 3.
8. CARD_IMPLEMENTATION_SCOPE_INDEX, STATUS, CONTEXT, and the BE2-08 supplement remain historical/current records until this candidate passes independent review and the owner approves the administrative successor update. No approval record is rewritten here.
9. After review passes, update the BE2-08 supplement to reference FEAT-044 scope Rev5 and FEAT-057 plan Rev6, including receipt provenance, VideoRun/codec/equality consequences, identity, visibility, read-after-commit, and superseded behavior.

## 8. Gates and offline verification sequence

Before any source implementation:

1. Independent review must pass FEAT-044 scope Rev5 and FEAT-057 plan Rev6 against manifest revision 3.
2. BE2-08 must adopt a versioned stale-run CR, including model/state axis, codec/storage, receipt behavior, cleanup, and recovery. D2 is design direction only.
3. BE2-01/08 must adopt the retry-policy mapping and exact public UoW/enlist/start/reject APIs.
4. Define the durable reject identity before a crash can occur; intent-only recovery and pre-intent crash recovery must both be specified.
5. Resolve request fields without a pin counterpart, BE2-07 source-fence feasibility and every invalidator, the jobs_for_notice lock path, participant CAS replay semantics, and the BE2-08→09 receipt-provenance option.
6. Resolve a non-terminal BE2-14 budget-denial/defer contract without supplying or guessing a unit/limit.
7. Freeze exact per-card source/test manifests and record separate supplemental approvals for S/F in each affected owner card. The already approved BE2-01 typed-dispatch subset does not cover these lifecycle changes.
8. Then perform only approved offline changes and relevant tests on a pinned snapshot. PostgreSQL two-session testing is needed for durable fence claims and requires a separate environment authorization.
9. Independently review code, fix findings, and rerun affected offline suites. Card acceptance remains a separate owner decision.

Modal, Lightning, provider, server, database, and runtime remain deferred. X01 remains PARTIAL; X05d BLOCKED; X05c/CR09-02 OPEN; X09-08 NOT_IMPLEMENTED. Nothing in this plan makes BE2 “fully connected” or ready to claim BE1 integration.

## 9. Approval state

Revision 6 is a draft for independent rereview only. S/F supplemental approval and all card-local contract adoption remain pending. Do not update the scope index's governing accepted-plan fields or the BE2-08 supplement until the plan passes review and the owner authorizes that record transition. No source/test/schema/approval/card-status change, staging, commit, push, merge, test, database, Modal, Lightning, provider, server, or runtime action is authorized by this draft.
