# FEAT-057 rereview 3 correction specification — draft 2026-10-21

- Status: DRAFT / AWAITING_OWNER_D3_DESIGN_CHOICES.
- Inputs: Claude rereview 3, CHANGES_REQUIRED, SHA256 80EB2B425A790BC4B9E8958C9ADB0576B639162458BD0153592749DEE5C5ADC0.
- Reviewed parents: FEAT-044 UoW scope Rev5 (8BCAD75E2E505053465349E1B93800626B494B6D1076561B437298A1E60A4EF4) and FEAT-057 slice plan Rev6 (1C44336ADE023C16AF7DF8D7972FCEE69C6155A529C1F4D5B27DA82B8B47D0C3).
- Source manifest Rev4: evidence/metrics/CROSS_LANE_UOW_SOURCE_HASHES_REV4_20261021.json, SHA256 2EAA11FCA7B510CA738D34ECED9EFD164C7734FCA8E6AD4792257F03AA68591F; 30 source files and one contract-test source read, no tests run.
- Branch/HEAD: feature/be2-backend-ai-integration / 1649b72978877d82b4d7662040ff3555dee0a3a7; worktree dirty, index empty at start.
- Authority: documentation/proposals only. D1 and D2 remain owner decisions. C1/C2 below are proposals pending owner response, not adoption or implementation approval.

This specification prepares the concrete corrections before new owning-card scope successors. Rev5/Rev6 have not passed review and remain immutable review inputs. S/F are not ready for supplemental approval. No source, test, schema, migration, official approval, acceptance, or runtime change follows.

## 1. Completion classification: authority and outcome, not receipt disposition alone

A receipt ACCEPTED can acknowledge a persisted failure claim. Distinguish AiJob.state, AiJob.result_disposition, completion-receipt disposition, and non-authoritative response disposition.

| Source decision in AiJobService | Required boundary candidate | Authoritative effect | Completion receipt / other effects |
|---|---|---|---|
| PROCEED, eligible, valid safe success, current context | B-accepted | Job SUCCEEDED/ACCEPTED and run SUCCEEDED with exact artifact/ready state | Authoritative ACCEPTED receipt and audit. |
| PROCEED, eligible, valid safe success, context superseded | B-stale | Job SUCCEEDED/STALE with persisted result refs; paired run terminal STALE under D2, no artifact and no ready state | Authoritative STALE receipt. Current source does not write a stale quarantine intent. Proposed durable stale cleanup is C2, not source behavior. |
| OutcomeKind.FAILURE after relevant checks | F-failure | Foundation selects FAILED_RETRYABLE or FAILED_EXHAUSTED; paired run mirrors that outcome | Receipt disposition ACCEPTED, job.result_disposition normally None. This is not accepted video output. Do not feed this into the current success-only worker _receipt path. |
| Current eligibility denied | F-reject | Paired CANCELLED | Authoritative REJECTED receipt; owned-ref quarantine intent where applicable. |
| Unsafe output | F-reject | Paired BLOCKED_UNSAFE | Authoritative REJECTED receipt and owned quarantine intent. |
| Malformed output | F-reject | Paired FAILED_EXHAUSTED | Authoritative REJECTED receipt; quarantine only for verified owned refs. |
| JOB_CANCELLED, JOB_TERMINAL, ATTEMPT_SUPERSEDED precondition | F-reject intent-only / incident | Preserve authoritative job/run winner; never turn an existing run STALE from this guard | Non-authoritative response. Durable audit and owned quarantine intents may be written; no authoritative completion-slot receipt. |
| INVALID_STATE, INPUT_MISMATCH, or malformed claim rejected by normalization | I-incident | No job/run lifecycle mutation | Separate durable audit-only incident commit, no authoritative completion receipt. No quarantine from a temporary guard. |
| Prior completion receipt | Lookup/replay | Preserve original winner | Same fingerprint replays receipt; conflicting claim records audit and conflicts. |

B-accepted and B-stale are authoritative foundation-owned finalization UoWs after external work. F-reject remains separate under D1. A declined B mutation is not permission to suppress the existing audit incident commit. “No job/run mutation” must not be abbreviated to “no persistence.”

### Valid persisted job/run pair table

| Job state | Job result_disposition | Authoritative completion receipt | Candidate paired video lifecycle |
|---|---|---|---|
| SUCCEEDED | ACCEPTED | ACCEPTED | SUCCEEDED, exact artifact, ready for review. |
| SUCCEEDED | STALE | STALE | Video-owned terminal STALE, no artifact and no ready state; only after versioned BE2-08 CR. |
| FAILED_RETRYABLE / FAILED_EXHAUSTED from failure claim | None | ACCEPTED | Matching failure state, no accepted artifact. |
| CANCELLED from completion eligibility denial | None | REJECTED | CANCELLED, no accepted artifact. |
| BLOCKED_UNSAFE | REJECTED | REJECTED | BLOCKED_UNSAFE, no accepted artifact. |
| FAILED_EXHAUSTED from malformed success output | None | REJECTED | FAILED_EXHAUSTED, no accepted artifact. |
| Administrative cancellation / dispatch loss / retry | Source-defined lifecycle | No completion receipt is required | Paired lifecycle from its own transition; do not fabricate a completion receipt. |

A non-authoritative guard response never replaces the persisted winner or changes this table.

## 2. Complete D2 impact in the BE2-08 versioned CR

Owner D2 is a design decision; current model, codec, terminal persistence guards, public schema, and receipt shape do not support it together. The CR must cover all of these before an implementation manifest is approved:

1. Define a video-owned lifecycle state type and terminal set including STALE. Foundation JobState is unchanged.
2. Add legal retry/fail/block/timeout/stale transitions to the current start/finalize/cancel model. QUEUED must have attempt_id=None; S alone binds; retry clears; terminal stale has no artifact or ready-for-review state.
3. Change codec _Run.generation_state under an explicit persisted-format compatibility/version decision; reject corrupt or unrecognized payloads.
4. Replace VideoRunRows.save's reliance on foundation TERMINAL_STATES with the adopted video terminal classification, retaining terminal, lineage, and artifact immutability.
5. Adopt a versioned public projection: current KnowledgeVideoView.generation_state and VideoAttemptView.state reject stale, and the contract test expects that rejection. Do not serialize a new stale value into the old contract.
6. Revise validate_submission_view's equality of foundation attempt state and video state to an explicit job-state/disposition/video-state mapping.
7. Resolve the non-accepted receipt shape. Current _receipt requires video_run=None unless receipt disposition is ACCEPTED and otherwise validates a succeeded run. Either an adopted adapter independently verifies the authoritative stale pair while preserving the old external shape, or a versioned receipt contract exposes a typed finalization outcome. Neither is currently implemented.
8. AR01/AR05 of the artifact read model exclude terminal stale without artifact. Distinguish stale generation from a historical accepted artifact whose later source eligibility changed; a status query is not an artifact/playback grant.

## 3. C1 budget-deferral candidate — owner decision pending

Recommended candidate: preserve QUEUED for dispatch/start deferral and FAILED_RETRYABLE for retry deferral; add a foundation-owned persisted execution-deferral record rather than a new JobState. This is a joint BE2-01/14 CR with BE2-08 participation and FEAT-057 composition. It requires a schema-specific plan and approved new migration if a new durable row/epoch is chosen. No migration is approved here.

The record must bind organization/job, active attempt, phase, deferral generation/revision, exact adopted resource definition/policy identity, typed reason/status, and idempotent deferral/resume identity. No unit, amount, limit, TTL, renewal, scheduler interval, or automatic cancellation time is assumed.

BE2-01 owns changes to _dispatch_one, start_attempt, and retry_job, and to every relevant claim, ack, dispatch-loss, retry, cancellation, query and fake/recovery path. Resource denial must not use the existing eligibility branches that cancel a job. Real consent/session/source eligibility denial retains its authoritative paired cancellation behavior.

Required mechanics:

- Query filters are optimization; each mutating path rechecks deferral/generation under the job lock and paired run lock.
- Deferred rows cannot be reclaimed repeatedly to increase publish_attempts; park/invalidate affected outbox leases with a persisted generation. Late ack cannot increase dispatch_count or recreate an unstarted timer for a deferred/obsolete generation.
- _recover_unstarted, queued_dispatched_not_started, and retry sweeps must not turn resource waiting into DISPATCH_LOST, failure, or retry-attempt consumption.
- Resume is an explicitly authorized command/resource-admission event. No new automatic scheduler is adopted. For a queued attempt, recheck current eligibility, execution grant, exact reservation proof for that actual persisted attempt, and deferral generation before S.
- Resume of QUEUED keeps the same attempt. Resume of FAILED_RETRYABLE first rechecks retry permission/current eligibility/backoff, atomically requeues once and closes the old deferral, creating one new persisted attempt. Resource reservation/execution proof must then be obtained for that new attempt at dispatch/admission before S; proof for the finished old attempt cannot authorize it. If resources are unavailable, defer the new queued attempt without closing it or creating another attempt. Reserving before retry would require a separately reviewed preallocation/idempotency CR. No provider runs and no usage is fabricated while waiting.
- Create a persisted recovery/watchdog epoch or an equivalent reviewed pause mechanism. Obsolete recovery callbacks, leases, and acknowledgements cannot mutate the new epoch. Preserve lifetime publication history; effective bounded recovery counts exclude resource-denied waiting. Do not silently reset historical counters. Current start capability has no dispatch epoch and WorkerDispatchEnvelope stays unchanged: an old delivery for the same active attempt may enter S only after CURRENT persisted eligibility/execution/reservation checks and one atomic start CAS. Rejecting such delivery solely by dispatch generation needs a separate versioned admission binding; do not claim the existing capability contains one.
- Cancellation/terminal lifecycle closes the deferral and invalidates resume/dispatch generation in the same paired UoW. Deferred work remains cancellable.
- Accounting stays in its separate transaction; never reserve/settle under job/run locks. Exact cross-store reservation proof and lost-ack recovery are required before S. Unknown execution/reservation outcome is pending, not a refund or permission to rerun.
- Current reservation schema phases are create/dispatch/retry; using admission S requires an explicit adopted phase mapping or versioned phase CR. Reservation expiry/renewal is still a separate versioned CR.
- No budget unit/limit was supplied. Budget-dependent execution remains disabled until those terms and handoff contract are adopted.

C1 settles this direction only if the owner selects it. Source currently has no such deferral record or epoch.

## 4. C2 durable B-stale cleanup candidate — owner decision pending

B-stale must commit the authoritative STALE receipt and D2 stale run atomically. For cleanup, the recommended new behavior is a keep-private/quarantine intent in that same foundation-owned B-stale commit, using verified owned output refs and the existing foundation intent/outbox primitives. BE2-08 owns retained-stage journal/recovery integration; the adopted storage owner owns actual quarantine/deletion and must protect any accepted artifact/reference. An intent receipt proves request durability, not physical cleanup.

Current source adds no quarantine intent for authoritative context-stale success, and the worker's _quarantine swallows errors. D2 did not previously adopt durable cleanup. C2 therefore needs an explicit owner choice and versioned CR. If the owner leaves cleanup open, record the precise BLOCKED gate and do not claim best-effort cleanup is sufficient.

## 5. Recovery, effect identity, and completion-key corrections

- claim.fingerprint() is computed before _normalise_claim. It canonicalizes claim material but is not a hash reconstructable from the later fallback failure code, reason, or current job/run alone.
- Persist authenticated claim/stage/moderation recovery input before relying on restart recovery. A digest is not the original input. Durable pre-intent crash input remains an explicit schema/contract gate.
- Accepted completion_key can be independently reconstructed from persisted accepted run/pin/strategy, media-operation identity, artifact material and blob hash, using the pinned media formula. The adapter computes its own value, compares caller input, and returns the independently computed result. It may not echo the caller's key.
- Stale/rejected runs have no accepted artifact. Require an authenticated durable private-stage journal with the exact key inputs. A receipt fingerprint alone cannot prove the key. If absent, lookup remains blocked/pending.
- Once a rejection-operation identity has committed, replay uses its stored effect identity/reason and cannot re-evaluate into a different event. The proposed reject-operation journal/receipt must not occupy the authoritative completion slot for an intent-only incident.
- Current event_id hashes reason, so a new reason yields a different event. Same operation key with changed canonical input conflicts; a redelivery replays the stored original decision. A truly new authorized incident uses a distinct operation identity and may create a second intent; it is not described as replay of the first.
- No job/run mutation does not prohibit I-incident's durable audit. Participant/infrastructure failure may be converted to pending only after the owning UoW has rolled back.

## 6. Lock and admission corrections

Notice ID discovery does not authorize cancellation. Under each sorted job lock and paired run lock, recheck notice_matches against the locked organization, CANCELLABLE_STATES, and OR-match of session/job_type/subject; recheck run identity/revision. Preserve notice_atomic_max, one-transaction notice atomicity, idempotency, and COMPLETE semantics.

Collect the complete union of foundation and participant fence requirements before holding fences. Reject missing/ambiguous keys and conflicting epochs. Lock every required job/run pair first, then hold the deduplicated canonical fence union once through commit. No job1/run1/fences → job2 order. Any newly discovered fence requires abandoning/restarting the UoW; do not append a lower key after earlier holds.

SqlAiJobUnitOfWork's wrapper preserves caller order; port implementations can sort, as the fixture does. Neither establishes a BE2-07 production fence.

Admission compares persisted job.job_type, message type, and configured VideoWorker route type using an adopted typed-route mapping; the run has no job_type field. Unknown or mismatched type fails closed before S.

## 7. Participant error classification

All participant errors escape the enclosing UoW so BE2-01 rolls back before any recovery query. An error alone is never evidence of committed replay.

| Error | Required classification after rollback |
|---|---|
| VIDEO_WRITE_CONFLICT | Translate to typed whole-UoW conflict; fresh transaction resolves exact winner/replay or conflict. Never continue in an aborted SQL transaction. |
| VIDEO_STALE_RUN | Fresh locked pair comparison; classify exact prior winner versus stale/conflicting mutation. |
| VIDEO_IMMUTABLE_LINEAGE, VIDEO_IMMUTABLE_ARTIFACT, VIDEO_TERMINAL_RUN | Integrity/conflicting-winner failure unless an independent authoritative lookup proves exact replay. |
| VIDEO_INVALID_TRANSITION, VIDEO_ATTEMPT_NOT_CURRENT | Fresh pair may prove duplicate/stale attempt; incompatible pair fails closed. No retry/rerender inferred. |
| VIDEO_STORAGE_CORRUPT | Integrity failure; never replay from corrupt payload. |
| VIDEO_RECEIPT_MISMATCH, VIDEO_INVALID_INITIAL_RUN, input/tenant/transaction errors | Fail closed. No automatic replay from the exception. |
| Infrastructure/driver error | Rollback; fresh authoritative commit lookup; pending when unavailable. No rerender because response was lost. |

## 8. Retry policy, owning scopes, and divergence bookkeeping

Foundation JobRetryPolicy has policy_id/status and retry parameters but no exact version/hash. AiJobDependencies.retry_policy supplies it, defaulting to FIXTURE_RETRY_POLICY; SQL persists its snapshot. VideoPin.retry_policy is a separate ExactRef. A currently cannot pass the exact mapping gate. A joint BE2-01/10 versioned policy mapping is required; source snapshots do not manufacture equivalence.

The next BE2-08 owning-card successor must cover A/S/B-accepted/B-stale/F/F-reject, model, codec, SQL terminal guards, worker receipt/projection paths, versioned public schema, and owned tests. The old exact-hash A/B addendum remains immutable; its header/blank in-document hash is historical and does not expand the later recorded approved manifest. No new source or schema permission is inferred.

Minimum BE2-08 candidate paths: domain/knowledge_video/model.py; infrastructure/knowledge_video/codec.py and sql.py; application/knowledge_video_create.py and knowledge_video_worker.py; application/ports/knowledge_video.py and knowledge_video_worker.py; contracts/schemas/knowledge_video.py only under versioned public/projection CR; owned domain/create/worker/persistence/contract tests. Tables/schema/new migration require a separately reviewed schema-specific manifest. Read-model queries/adapters/tests retain a separate scope.

Historical scope Rev4 incorrectly said infrastructure/cross_lane/knowledge_video.py exists. It does not. The actual knowledge_script_video.py is an exact-source reader with a process-local coordinator, not a lifecycle-UoW adapter. Record this correction explicitly in the next divergence table.

A prior disposition-path collision was repaired with exact hash recovery. The original note again hashes to 15139BD8...E9A6E1A; the later bytes are preserved as DISPOSITION_REV2 and hash to E6B0B844...8D84E30F. See the evidence-path recovery receipt; neither original validator receipt nor source was edited.

## 9. Next record transition

After owner C1/C2 responses, prepare FEAT-044 scope Rev6, FEAT-057 plan Rev7, the BE2-08 owning scope successor, and the joint BE2-01/14 budget CR proposal, all with exact manifests and open contract gates. Obtain independent review before supplemental S/F approval. Do not send the current Rev5/Rev6 as approved implementation scope.

X01 PARTIAL; X05d BLOCKED; X05c/CR09-02 OPEN; X09-08 NOT_IMPLEMENTED. Budget unit/limit remain unprovided. No pytest, database, provider, server, Modal, Lightning, or runtime was run.
