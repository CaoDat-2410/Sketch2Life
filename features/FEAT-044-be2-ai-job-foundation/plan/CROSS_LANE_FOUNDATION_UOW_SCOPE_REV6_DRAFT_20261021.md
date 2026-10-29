# Foundation-owned cross-lane lifecycle UoW — scope revision 6 draft

- Status: DRAFT / OWNER_D1_D2_D3_RECORDED / CHANGES_ADDRESSED_PENDING_INDEPENDENT_REVIEW.
- Owner: BE2-01 / FEAT-044; video-row participant: BE2-08 / FEAT-050; integration composition: FEAT-057.
- Parent for review: CROSS_LANE_FOUNDATION_UOW_SCOPE_REV5_DRAFT_20261021.md, SHA256 8BCAD75E2E505053465349E1B93800626B494B6D1076561B437298A1E60A4EF4.
- Owner D3 receipt: FEAT-057 evidence/notes/CROSS_LANE_UOW_OWNER_DECISION_D3_20261021.md, SHA256 C1799417AFD2DDB989D6C888A8B3F9702D4A6B4DC2A8B90637DBD6E11C3AE54C.
- Source manifest Rev4: FEAT-057 evidence/metrics/CROSS_LANE_UOW_SOURCE_HASHES_REV4_20261021.json, SHA256 2EAA11FCA7B510CA738D34ECED9EFD164C7734FCA8E6AD4792257F03AA68591F; 30 source files and one contract-test source read, not run.
- Review input: Claude rereview 3 (CHANGES_REQUIRED), SHA256 80EB2B425A790BC4B9E8958C9ADB0576B639162458BD0153592749DEE5C5ADC0.
- Branch/HEAD: feature/be2-backend-ai-integration / 1649b72978877d82b4d7662040ff3555dee0a3a7; dirty source bytes are identified by the manifest, not by HEAD alone.

This is a consolidated design/scope successor, not implementation approval or proof that any candidate contract is implemented. Existing approved addenda, manifests, migrations, acceptance and official approvals are unchanged. S/F and all new schema/public-contract work require independent review and separate exact supplemental approval.

## 1. Governing owner decisions

D1: BE2-01 alone opens/commits/rolls back the lifecycle UoW. BE2-08 writes only its own rows through a transaction-scoped participant; no connection or SQLAlchemy type is exposed in application ports. Every paired lifecycle writer, including reconciliation/outbox paths, enlists the run. Business rejection has a separate foundation commit, not an intent preserved by rollback. External generation spans no transaction.

D2: VideoRun gains its own terminal stale representation only via a versioned BE2-08 CR, with no artifact or ready state. Foundation JobState gets no STALE addition. VideoRun attempt_id is bound only at S; retry clears the old id and attempt number remains foundation-owned.

D3 C1: while budget-deferred BOTH job/run are QUEUED. The durable hold is BE2-01-owned metadata, not a new job/video budget state. _dispatch_one, start_attempt, retry_job resource-denial branches defer rather than cancel; genuine consent/kill denial still cancels. Waiting consumes no dispatch-loss time/recovery allowance. The maximum defer duration is owner-supplied later and PENDING; no value or terminal timeout action is invented. BE2-14 supplies deny/defer contract, not budget or execution authority.

D3 C2: B-stale atomically commits job SUCCEEDED with STALE/result refs, authoritative receipt, paired video stale state and durable private-stage keep-private/quarantine intent. BE2-01 owns the _decide_completion change. Intent refs come only from BE1 artifacts-port descriptors produced by the exact job/attempt; unmappable refs fail closed. BE1 owner adoption is required for quarantining refs in a SUCCEEDED job's result_refs and for accepted-reference protection. Accepted output always wins.

WorkerDispatchEnvelope stays unchanged. X01 PARTIAL; X05d BLOCKED; X05c/CR09-02 OPEN; X09-08 NOT_IMPLEMENTED until proved. This draft authorizes no test, SQL, database, provider, server, Modal, Lightning or runtime.

## 2. Related owning CRs and exact source facts

Related drafts, all pending independent review/adoption and implementation approval:

- BE2-01/14 joint budget CR: CROSS_LANE_BUDGET_DEFERRAL_CR_DRAFT_20261021.md.
- Separate BE2-01 schema/migration CR: CROSS_LANE_BUDGET_DEFERRAL_SCHEMA_CR_DRAFT_20261021.md.
- BE2-01 stale-branch CR: CROSS_LANE_STALE_FINALIZATION_CR_DRAFT_20261021.md.
- BE2-08 lifecycle/state/codec/projection/receipt CR in FEAT-050 plan/CROSS_LANE_BE2_08_SCOPE_REV2_DRAFT_20261021.md.
- BE2-14 deny/defer scope in FEAT-049 plan/CROSS_LANE_BE2_14_SCOPE_REV2_DRAFT_20261021.md.
- BE1 artifacts adoption packet under FEAT-057 evidence/notes; not sent and no BE1 adoption is claimed.

Pinned source facts:

- Foundation JobState remains queued/running/succeeded/failed_retryable/failed_exhausted/blocked_unsafe/cancelled; ResultDisposition is a distinct axis.
- CompletionReceipt.disposition ACCEPTED may acknowledge a failure claim; it does not by itself mean a succeeded artifact or equal AiJob.result_disposition.
- Foundation record_failure/record_dispatch_loss use job.retry_policy. JobRetryPolicy has policy_id/status/parameters but no version/hash; dependencies supply the policy, defaulting to FIXTURE_RETRY_POLICY. SQL snapshot storage does not establish an exact mapping to VideoPin.retry_policy: ExactRef. A is blocked until BE2-01/10 adopt a versioned mapping.
- Current authoritative context-stale success commits SUCCEEDED/STALE with result refs and receipt, but no quarantine intent. D3 adds intent through a new BE2-01 CR; it is not current behavior.
- VideoRun currently uses foundation JobState, codec validates that enum, SQL save uses foundation TERMINAL_STATES, and public schemas/projection do not accept the new video stale axis. D2 needs all these changes and defined transitions, not only a new method.
- Foundation completion receipts contain job/attempt/id/fingerprint/disposition/reason/revision/time, not completion_key. Accepted exact key material can be reconstructed from the persisted accepted run/pin/artifact and pinned media formula; stale/rejected recovery requires durable private-stage journal inputs, not a digest alone.
- claim.fingerprint is computed before _normalise_claim. It canonicalizes claim material but is not recoverable from the later failure-code fallback/reason/job alone.
- Current _receipt expects video_run=None for non-ACCEPTED and a succeeded run for ACCEPTED. Failure acknowledgment and B-stale require a versioned outcome/receipt interpretation or an adopted adapter boundary; source does not already prove them.
- SqlAiJobUnitOfWork forwards fence order; a port may sort, as the ASSUMED_CONTRACT fixture does. Neither gives BE2-07 a production shared-store fence.
- Outbox claim increments publish_attempts; ack can increment attempt dispatch_count and dispatched_at. Existing sweeps know no budget hold. A durable hold must cover these paths, not only the first denial branch.
- ArtifactDescriptor.fence is supplied through the BE1 artifacts port. BE1 actual quarantine/currentness adoption remains open.
- Current cross_lane directory has knowledge_script_video.py, an exact-source reader with a process-local coordinator; no lifecycle-UoW knowledge_video.py exists.

## 3. Outcome-to-boundary classification

The classification uses authority, claim outcome, job state and receipt meaning together.

| Source decision | Boundary | Job/run action | Receipt/effects |
|---|---|---|---|
| Valid safe SUCCESS, current context | B-accepted | Job SUCCEEDED/ACCEPTED and run SUCCEEDED with exact artifact/ready state | Authoritative ACCEPTED receipt and audit. |
| Valid safe SUCCESS, context superseded | B-stale | Job SUCCEEDED/STALE/result_refs and run video-terminal STALE/no artifact/no ready state | Authoritative STALE receipt plus D3 private-stage intent atomically; BE1 adoption gate. |
| FAILURE claim after relevant checks | F-failure | Foundation policy chooses FAILED_RETRYABLE or FAILED_EXHAUSTED; paired run follows | Authoritative receipt ACCEPTED, but no success artifact; job.result_disposition normally None. |
| Genuine eligibility denial at completion | F-reject | Paired CANCELLED | Authoritative REJECTED receipt and owned-ref intent as applicable. |
| Unsafe output | F-reject | Paired BLOCKED_UNSAFE | REJECTED receipt and owned quarantine intent. |
| Malformed output | F-reject | Paired FAILED_EXHAUSTED | REJECTED receipt; owned-ref intent where verifiable. |
| JOB_CANCELLED / JOB_TERMINAL / ATTEMPT_SUPERSEDED guard | F-reject incident/intent-only | Preserve authoritative winner; guard-STale does not make a run STALE | Non-authoritative response, audit/verified owned intent; no completion-slot occupation. Accepted-reference protection still applies. |
| INVALID_STATE / INPUT_MISMATCH / failed claim normalization | No lifecycle/authoritative-outcome commit | No job/run mutation | Existing durable audit-only incident path is retained as I-incident, not called lifecycle success. |
| Prior receipt | Replay/conflict lookup | Preserve winner | Same fingerprint returns stored result; conflicting claim produces conflict audit/error. |

The owner's “temporary → no commit” is applied to lifecycle/authoritative completion, preserving the audit-only incident distinction explicitly required by the rereview P3. No removal of durable security audit is proposed.

### Valid persisted axes

| Job state | AiJob.result_disposition | Completion receipt disposition | Video-run state / output |
|---|---|---|---|
| SUCCEEDED | ACCEPTED | ACCEPTED | SUCCEEDED, exact artifact, ready. |
| SUCCEEDED | STALE | STALE | Video STALE terminal, no artifact/no ready, with same-commit D3 intent. |
| FAILED_RETRYABLE / FAILED_EXHAUSTED from failure claim | None | ACCEPTED | Corresponding failure state, no accepted artifact. |
| CANCELLED from eligibility completion denial | None | REJECTED | CANCELLED, no accepted artifact. |
| BLOCKED_UNSAFE | REJECTED | REJECTED | BLOCKED_UNSAFE, no accepted artifact. |
| FAILED_EXHAUSTED from malformed output | None | REJECTED | FAILED_EXHAUSTED, no accepted artifact. |
| Dispatch loss / admin cancellation / retry / start / defer | Source-defined lifecycle | None required | Paired outcome of that boundary; no fabricated completion receipt. |

Non-authoritative response disposition does not replace persisted winner axes.

## 4. Lifecycle writers and atomic boundaries

| Boundary / writer | Foundation-owned UoW and participant obligation |
|---|---|
| A submit / create_job | One job/initial attempt/semantic key/command receipt/outbox/audit plus BE2-08 queued run/submission receipt, or exact replay. Reconcile both independent semantic indexes and retry-policy mapping. Run attempt_id=None. Creation lease is external. |
| S / start_attempt via VideoWorkerAdmission.begin | Lock job/run, validate typed route and current eligibility/execution/reservation; atomically start both and bind active attempt id. No provider before committed S. Duplicate/inactive/not-queued semantics preserved. |
| S resource denial | Do not start/cancel; commit/verify durable hold with both already QUEUED and run attempt_id=None. Park dispatch generation. |
| _dispatch_one eligibility denial | Genuine consent/kill: paired F cancellation. BUDGET_EXCEEDED: QUEUED hold, not cancel or publish. |
| retry_job / run_due_retries | Genuine eligibility denial: paired cancel. A due/otherwise authorized retry normally requeues once to a new foundation attempt, clears video attempt_id, and creates both QUEUED plus hold in the same UoW when resource-denied. Repeated callbacks do not allocate another attempt. |
| _recover_unstarted / recover_unstarted_dispatches | Mere republish has no video lifecycle mutation. Actual dispatch loss pairs queued job/run to foundation-selected failed_retryable/exhausted. Active hold/obsolete epoch must not count as dispatch loss or spend recovery allowance. |
| _expire_overdue / expire_overdue_attempts | Started timeout outcome chosen by foundation retry policy; paired F CAS. Budget waiting is not a RUNNING attempt timeout. |
| cancel_job / apply_cancellation_notice | Pair cancellation and close/invalidate hold/resume generation; preserve notice atomicity/idempotency/limit and locked predicate checks. |
| accept_completion accepted or stale | B-accepted or B-stale below; distinct from a generic receipt ACCEPTED label. |
| accept_completion failure/rejection | F or separate F-reject according to classification; mirror authoritative outcome and effects. |
| report_progress | Foundation-only running-progress exception, no video lifecycle change; future lifecycle changes must enlist participant. |
| _publish, claim/ack and sink delivery | Delivery bookkeeping is not a video lifecycle transition, but budget hold/epoch must guard relevant claims/acks. A denial branch that cancels is not exempt. |
| I-incident | Durable audit only; not a completed lifecycle or accepted artifact. |

### Commit/recovery matrix

| Boundary | Enlisted rows / CAS | Recovery point |
|---|---|---|
| A | Foundation job/attempt/semantic/command receipt/outbox/audit + video run/submission receipt. Both unique indexes reconciled. | Whole-UoW rollback after either owner's conflict; fresh-transaction lookup resolves exact winner. No replay in an aborted transaction. |
| S | Job queued→running, run queued→running with exact active attempt id; any denial/deferral branch is explicit. | New-UoW authoritative pair lookup. Same already-running attempt proves duplicate only through exact pair/current authorization, not broker delivery. |
| B-accepted | Job running→SUCCEEDED/ACCEPTED + receipt + run exact artifact/ready atomically. Complete source fences only if adopted. | Independently reconstruct key; exact receipt/artifact/pair comparison; unknown lookup stays pending. |
| B-stale | Job running→SUCCEEDED/STALE/result_refs + authoritative STALE receipt + video stale/no artifact/no ready + verified D3 intent, one commit. | Same stored decision/intent identities and durable stage journal; unmappable/unadopted refs or missing accepted protection fail closed before commit. Intent proves request durability only. |
| F | Every current failure/cancel/timeout/dispatch-loss/retry writer uses paired job/run CAS. Retry+hold remains one normal next attempt. | Full rollback on participant error; fresh pair classification distinguishes replay/stale/conflicting mutation. |
| F-reject | Separate reject UoW rereads current job/run and required facts. Pair a permitted state transition when authoritative; otherwise preserve terminal winner and write idempotent incident/intent without consuming completion slot. | Stable reject-operation journal/id, stored reason/event/ref material. Crash before durable input remains blocked. No reliance on B rollback. |
| H hold/resume metadata | BE2-01 locks job/run; both QUEUED; update durable hold/lease/watchdog generation, not lifecycle state. Resume closes hold but does not start provider. | Exact operation receipt/generation; stale ack/callback cannot reopen or charge new epoch. No new JobState. |
| I-incident | Audit/effect rows only, no job/run lifecycle CAS or authoritative completion receipt. | Existing idempotent incident/effect identity; no fake replay winner. |

## 5. C1 hold invariants and endpoint

The joint budget CR and separate schema CR govern details. State while held is always job QUEUED + run QUEUED + no video attempt_id. A due retry enters this pair once through normal foundation requeue, not by resetting a finished old attempt. Its normal retry cap/backoff/history remain effective; holding never creates or closes further attempts.

Every claim/ack/recovery/retry mutator must have query filtering and a locked authoritative hold/generation recheck. Park/invalidate existing leases; never repeatedly claim held rows and increase counters. Persist a recovery epoch/pause protocol so old timestamps do not cause immediate dispatch loss after resume. Preserve lifetime audit counts separately from effective bounded recovery counts. Current capability/envelope has no assumed epoch: same-active-attempt old delivery may enter S only after CURRENT persisted gates and unique atomic start; rejecting it by epoch needs a separately adopted admission binding.

A failed attempt's reservation cannot authorize its replacement. Reserve/verify for the new persisted attempt before S; accounting stays outside lifecycle locks. BE2-14 deny/defer itself is no execution grant.

Hold endpoints:
1. Verified authorized resume: re-evaluate genuine eligibility and current actual-attempt reservation/execution proof, close hold and activate valid recovery epoch; pair stays QUEUED until S.
2. Genuine consent/kill/owner cancellation: paired CANCELLED and closed hold, late resume invalid.
3. Another authoritative terminal outcome: close/fence hold through its reviewed lifecycle transition.
4. Maximum duration: numeric value is PENDING; deadline action also remains a named contract gate. No TTL, auto-fail/cancel/refund or indefinite-runtime-readiness claim is invented. Budget-dependent runtime cannot be called ready until the missing terms are adopted.

## 6. C2 owned-ref intent and accepted winner

BE2-01 changes the authoritative stale branch through its stale-finalization CR. Source currently emits no intent for this path. The intent must use artifacts-port BE1 descriptors with exact artifact ref/hash/organization and producer job/attempt. Strings or private-stage refs are not silently substituted. Missing/unowned/ambiguous descriptors fail closed.

STALE_CONTEXT is the proposed fixed source-existing reason; the BE1 artifacts owner must adopt that exact reason and its meaning for refs retained in result_refs of a SUCCEEDED/STALE job. It is not auto-approved by D3 or a fallback to an arbitrary reason.

Deterministic event_id uses the adopted canonical quarantine material: job, attempt, sorted verified artifact_refs, fixed reason and original claim fingerprint. Persist operation/decision/event identity once; replay never changes it. Any actual reason/identity change follows an explicitly new operation/CR, not the same replay.

BE1 must adopt accepted-reference protection for both winner orders. A private-stage cleanup intent never deletes or makes unavailable accepted artifact/reference. Accepted finalization and later stale guards cannot be reversed by cleanup. Physical cleanup, permission checks and adopted storage-side compare/fence behavior remain BE1 responsibilities; an outbox intent is not proof of deletion. The BE1 packet is prepared but not sent/adopted.

## 7. Full persisted identity and source-fence gates

| Foundation input | Video/pin counterpart | Rule |
|---|---|---|
| organization_id and job_id | VideoPin org + run.job_id | Exact authenticated equality; unique locked get-by-job required. |
| scope.session_id | VideoPin.session_id | Exact equality; null foundation session fails closed. |
| active attempt id | run.attempt_id | Equal only after S; queued/hold/retry-queued run has null id. |
| attempt number | No video field | Foundation-only. |
| request_ref.context_revision | pin.context_revision | Exact equality. |
| request_id/request_revision/input_hash | No directly equivalent pin field | Persisted approved mapping or versioned CR; no equality to video_id/pin_digest/artifact hash by assumption. |
| target_id/purpose_code/subject_refs | No proven direct counterpart | Owner-approved field rules or fail closed. |
| exact bundle/source refs + audience/context | pin bundle/sources/revisions | Canonical exact ref/version/hash comparison. |
| job.job_type, message type, configured route type | Run has no job_type field | Versioned typed-route mapping; unknown/mismatch fails before S. |
| command/semantic/body identities | video receipt/session-pin index | Reconcile one exact winner; different key names are not equivalence. |
| foundation retry policy snapshot | pin.retry_policy ExactRef | BE2-01/10 versioned mapping required; current A cannot pass. |

Inventory every currentness input: bundle head/version/hash; basis/context; audience; policy ref/epoch; source/catalog claims; editorial_revision; rights/kill/execution; encoding/content/model/retry profile/library asset; artifact descriptors. Each needs owner, persisted key, complete invalidator list and same-store lock/CAS.

ArtifactDescriptor.fence is BE1-owned. editorial_revision authoritative owner/writers remain a gate. The fixture is ASSUMED_CONTRACT only. BE2-07 current scope has no shared SQL fence, so X01 stays PARTIAL. Revalidation/process-local coordination is not durable serialization, and finalization fence does not close X05d/X02.

## 8. Lock order, complete hold, and notices

Target order is all required job/run pairs in stable job order, then the complete canonical sorted union of source fences, held once through commit. Collect foundation/participant fence needs before hold, reject conflicting epochs, and abandon/restart on any late-discovered fence. No pair1/fences→pair2 and no appending a smaller key.

jobs_for_notice currently locks all job rows before aggregate reread; implementation must revise the path while retaining notice_atomic_max, one-transaction notice completion, idempotency and COMPLETE semantics. After each job→run lock, recheck notice_matches (tenant, CANCELLABLE_STATES, OR session/type/subject predicate) and paired run revision/identity. ID discovery is not authority.

create_job's fence-before-insert is an explicit A-only fresh-row exception with reviewed uniqueness/replay; it is not permission for existing-row writers to reverse order. Creation lease is outside A, not an enlisted row. Outbox logical lease differs from SQL row lock; no database lock/transaction spans publish/provider I/O. An invalidator committing fences first must open a new lifecycle UoW for later job/run work. Accounting/reservation transactions cannot be nested under lifecycle locks.

## 9. Recovery and participant errors

Accepted keys are independently reconstructed from persisted material and compared to caller keys; adapters return their own value. Stale/rejected run lacks an accepted artifact, so authenticated durable stage/journal material is mandatory. Fingerprint alone cannot reconstruct the stage or post-normalization claim. Missing recovery data is pending/CR, never permission to rerender.

Reject operation journal and event IDs are stable after first commit. Redelivery replays stored reason/material. Intent-only receipt is not a completion-slot receipt; side_effect_recorded(event_id) proves intent storage, not deletion. Audit-only temporary outcomes can persist incidents while lifecycle/authoritative completion does not commit.

Every participant error must escape the enclosing UoW; a top-level worker converts to pending only after rollback:

| Error | Fresh-UoW classification |
|---|---|
| VIDEO_WRITE_CONFLICT | Typed whole-UoW abort, authoritative winner lookup, exact replay or conflict. |
| VIDEO_STALE_RUN | Locked pair comparison; no automatic unique-conflict/replay equivalence. |
| VIDEO_IMMUTABLE_LINEAGE / VIDEO_IMMUTABLE_ARTIFACT / VIDEO_TERMINAL_RUN | Integrity/conflicting winner unless separate exact persisted lookup proves replay. |
| VIDEO_INVALID_TRANSITION / VIDEO_ATTEMPT_NOT_CURRENT | Legitimate duplicate/stale attempt only if fresh pair proves it; otherwise fail closed. |
| VIDEO_STORAGE_CORRUPT | Integrity failure, never replay from corrupt state. |
| VIDEO_RECEIPT_MISMATCH / VIDEO_INVALID_INITIAL_RUN / input/tenant/transaction errors | Fail closed; exception itself proves no accepted winner. |
| Driver/infrastructure failure | Rollback, fresh authoritative lookup, pending if unknown; never rerender on lost response. |

## 10. BE2-08 versioned state, receipt, read model and ownership

BE2-08's successor scope must include domain/model, codec, SQL video-owned terminal set in save, _receipt, create/projection validation, public schema version, legal retry/fail/block/timeout/stale transitions, queued-id invariant, and locked get-by-job participant API. No stale literal is silently added to foundation JobState or the old public codec/schema. Versioned outcome mapping replaces blind equality of job state and video state.

The finalized-artifact read model remains separate. AR01/AR05 exclude terminal stale without artifact; historical accepted output later ineligible is a distinct current-use question. Choose adopted public receipt provenance (foundation read lookup via composition or opaque ref with model/codec/equality impacts), exact identity, visibility and read-after-commit before BE2-09 writes its projection. BE2-09 never writes BE2-08 rows; X05d remains BLOCKED, X05c/CR09-02 OPEN.

BE2-01 owns its service/domain/ports/SQL UoW/dispatch/recovery and new hold schema. BE2-08 owns video state/rows/ports/codecs. BE2-14 owns deny/defer contract only in this revision. FEAT-057 owns lifecycle composition and edge tests under a separate exact supplemental manifest. No application SQL connection, foreign-owner direct table write, new migration, or public-contract edit is approved by this scope.

## 11. Candidate evidence and gates before source approval

Evidence must cover:
- participant-negative transaction/write authority; complete lifecycle writer inventory;
- A dedup/policy mapping/split winner and fresh-transaction replay;
- S duplicate/inactive/denied/deferred/valid resume, no provider while held, exact actual-attempt proof;
- B accepted versus authoritative stale versus guard-STale/failure acknowledgment; receipt/result/run axes;
- same-commit B-stale owned-ref intent, deterministic reason/event replay, accepted wins both race orders, BE1 adoption proof;
- all F writers and queued retry+hold once; old-lease/late-ack/watchdog/retry counters, hold resume/cancel/lost ack and missing upper-bound gate;
- full notice predicate recheck/atomic completion; one complete fence hold, late fence restart and PostgreSQL winner orderings when separately authorized;
- independent key reconstruction/non-echo; durable pre-intent recovery; full participant error taxonomy;
- video-owned stale codec/terminal/projection/receipt compatibility and artifact-read exclusions.

Before supplemental implementation approval: independent scope/CR review; exact minimal per-card source/test manifests; BE2-01 schema/new migration approval; BE2-01/10 retry-policy and missing request-field mappings; versioned BE2-08 lifecycle/receipt/public projection; BE1 artifacts adoption; actual execution/reservation/phase and max-defer policy; read-model receipt provenance; separate source-fence owner scope for a durable X01 claim. Named open gates are not treated as implemented.

No test ran for this draft. Card statuses/acceptance and approvals remain unchanged. This is ready only for independent document/source review, not supplemental S/F execution approval.
