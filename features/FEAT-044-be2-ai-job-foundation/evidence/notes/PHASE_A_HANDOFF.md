# BE2-01 Phase A — consumer contract pack and handoff (P1/P2/P4)

- Date: 2026-10-14, Asia/Saigon. Executor: Claude, under `approvals/TASK_APPROVAL.md` (Phase A rev 1).
- Status of everything here: **candidate / fixture scope**. Not adopted into the shared registry,
  not durable, no real provider, no actual deletion. Phase B and BE2-02..14 are not started.
- Candidate specification: `plan/PHASE_A_CANDIDATE_SPEC.md`. Runner/tests evidence:
  `PHASE_A_IMPLEMENTATION_EVIDENCE.md`; review corrections: `PHASE_A_Q00_FIX_EVIDENCE.md`.
- **Q00 amendment (2026-10-14):** contract/handoff deltas from fixing review R01–R11 and
  follow-ups R03a/R04a/A18a are marked “(Q00)” below.
- **Review state (synced 2026-10-14):** final code review PASS at fake/contract scope; R01–R11
  and R03a/R04a/A18a CLOSED (`PHASE_A_Q00_FINAL_CODE_REVIEW_20261014.md`). Candidate semantics
  are **not adopted**; consumer review/decisions are tracked per row in
  `PHASE_A_ACCEPTANCE_GATE_RECORD.md`. Follow-up evidence: `PHASE_A_Q00_FOLLOWUP_FIX_EVIDENCE.md`.

## 1. What was built (file map)

| Layer | Path | Content |
|---|---|---|
| Domain (pure) | `backend/src/sketch2life/domain/ai_jobs/model.py` | DATA-25 states, disposition axis, progress, named retry/poll policies, job/attempt transitions, poll hint |
| Domain (pure) | `backend/src/sketch2life/domain/ai_jobs/completion.py` | Completion claim identity/fingerprint, ordered precondition guards, canonical JSON hash |
| Domain (pure) | `backend/src/sketch2life/domain/ai_jobs/provider_copy.py` | ProviderCopyLifecycle statuses/receipts; Deleted only with verified receipt |
| Ports | `backend/src/sketch2life/application/ports/ai_jobs.py` | Repository/unit of work, authorization, eligibility, worker capability, clock, ids, artifacts, audit, queue, provider, provider-copy ports |
| Application | `backend/src/sketch2life/application/services/ai_jobs.py` | Create (scoped idempotency + semantic dedup), dispatch outbox, start, progress, completion, timeout sweep, policy retry, cancel, owner notices, CMD-44 query + role projection |
| Application | `backend/src/sketch2life/application/services/provider_copy_lifecycle.py` | Scoped discover/cancel/purge with idempotent receipts and no resurrection |
| Contracts | `backend/src/sketch2life/contracts/schemas/ai_jobs.py` | `AsyncJobView`/`AsyncJobChildView` envelopes, `CollaborationError`, internal `AsyncJobCompletion`, `CreateAiJob` |
| Contracts | `backend/src/sketch2life/contracts/schemas/ai_contract_candidates.py` | DATA-24 candidate (owner BE2-05), ProviderCopyLifecycle report (owner BE2-14), DATA-21..23/26..29/33 shape specs |
| Fakes | `backend/src/sketch2life/infrastructure/ai_jobs/fakes.py`, `harness.py` | Staged-transaction fake store with CAS, queue, clock, ids, auth, eligibility, artifacts, audit, capability, provider, copy registry/adapter |
| HTTP | `backend/src/sketch2life/interfaces/http/routers/ai_jobs.py` | Thin CMD-44 `GET /jobs/{job_id}` adapter |
| HTTP (fixture) | `backend/src/sketch2life/interfaces/http/ai_jobs_fixture_app.py` | Isolated fixture app with synthetic `Authorization: Fixture <token>`; **not** imported by `app.py` |
| Tests | `backend/tests/unit/test_ai_job_lifecycle.py`, `test_ai_job_application.py`, `test_ai_job_review_regressions.py`, `test_ai_job_q00_followups.py`, `backend/tests/contract/test_ai_job_contracts.py`, `test_ai_job_polling.py` | Domain, application, review regressions, contract, HTTP |
| Runner | `features/FEAT-044-be2-ai-job-foundation/src/run_fixture_contracts.py`, `fixture_catalog.py` | Offline A-01..A-20 runner; deterministic fixture generation/verification |
| Fixtures | `features/FEAT-044-be2-ai-job-foundation/fixtures/` (90 files + `MANIFEST.json`; Q00 added 27 negatives) | Synthetic positive/negative fixtures, policies, P1 poll example, error catalogue |

The live composition `backend/src/sketch2life/interfaces/http/app.py` is unchanged.

## 2. Implemented transition table

| From | Event (guard) | To / effect |
|---|---|---|
| — | `create_job`: create authority, scoped key new, current eligibility, semantic key new | `queued`, attempt 1, command receipt, semantic index, outbox entry (one fake transaction) |
| — | same scoped key + same fingerprint | original receipt replayed after read-authority recheck; no mutation |
| — | same scoped key + different fingerprint | `409 IDEMPOTENCY_PAYLOAD_MISMATCH`, nothing changes |
| — | new key, semantic key exists (request **and** target/purpose/session/subjects; Q00 R02) | caller's own receipt `deduplicated` → existing job (read authority checked) |
| `queued` | `dispatch_outbox` with current eligibility denied (Q00 R09) | `cancelled` (reason), entry dropped, nothing enqueued |
| `queued` | `start_attempt` (worker capability, active attempt, eligibility) | `running`; eligibility denied → `cancelled` (reason) without provider call |
| `running` | duplicate delivery of same attempt | no-op `DUPLICATE_DELIVERY` |
| `running` | progress (active attempt) | same state, revision+1 when value changes |
| `running` | failure claim retryable, attempts remain / timeout sweep | `failed_retryable`, `retry_not_before` = backoff |
| `running` | failure non-retryable or attempts exhausted | `failed_exhausted` |
| `failed_retryable` | `retry_job` callback due, same attempt number, eligible | `queued`, new attempt, new outbox entry |
| `failed_retryable` | retry due but eligibility denied | `cancelled` (reason) |
| `queued`/`running`/`failed_retryable` | Teacher cancel (If-Match = job_revision) or owner notice | `cancelled`; scheduled retry cleared; stale callbacks/late outputs are no-ops |
| `running` | success claim, unsafe moderation | `blocked_unsafe`, disposition rejected, own (org + job/attempt lineage) outputs quarantined |
| `running` | success claim malformed (no/unknown/foreign/other-lineage/hash-mismatched/already-quarantined output) | `failed_exhausted` `OUTPUT_MALFORMED`, rejected; only own outputs quarantined, foreign/unowned never mutated |
| `running` | success claim, context advanced | `succeeded` + disposition `stale`, lineage note, refs never projected |
| `running` | success claim, all checks pass | `succeeded` + disposition `accepted` |
| any | wrong attempt / terminal job / input mismatch / not started / malformed claim | non-authoritative stale/rejected receipt, not stored, job unchanged; a later valid claim of the active attempt still lands (Q00 R03/R04, spec §3) |
| `queued`/`running` | temporary guard rejection `INVALID_STATE` / `INPUT_MISMATCH` (Q00 R03a) | no artifact change; final rejections (cancelled/terminal/superseded/revoked/unsafe/malformed) quarantine own outputs only |
| `running` | failure claim with an unrecognised **string** provider code (Q00 R04) | treated as `PROVIDER_ERROR`; original only hashed in audit |
| `running` | failure claim with a **non-string** code (list/dict/number/bool/bytes/set; Q00 R04a) | non-authoritative `MALFORMED_CLAIM`, job unchanged, hash-only audit; non-string ids → `400 MALFORMED_REQUEST` |
| any | same identity as a stored (authoritative) completion, different fingerprint | `COMPLETION_CONFLICT` incident, job unchanged |

## 3. P1 / FE package

- Contracts: `AsyncJobView` (Teacher/Admin) and `AsyncJobChildView` (Device), version
  `0.1-candidate`, inside API-CS-01 envelope `{contract_name, contract_version, correlation_id,
  data, meta}`; `meta.projection` is `teacher|admin|device`.
- States to render: `queued`, `running`, `succeeded`, `failed_retryable`, `failed_exhausted`,
  `blocked_unsafe`, `cancelled`. `succeeded` is **not** approval/playback/session completion.
- Progress: `unknown` has `value=null` (do not render 0%); `stages` has `stage_label`;
  `percentage` is a real value 0..100.
- Polling: honour `poll_after_ms` (≥2000 ms, ≤10000 ms under `fixture.job_poll.v0`, PROPOSED);
  `null` means terminal, stop polling. Send `If-None-Match` with the last `ETag`; a `304` has no
  body. A changed ETag can come from an authorization/eligibility change without a new revision.
  (Q00 R10) The ETag also changes when the computed `poll_after_ms` changes (e.g. idle backoff
  2000 → 10000 ms), so a conditional poll returns `200` with the new hint instead of `304`.
- (Q00 R08/R11) Validators: refs only with `succeeded`+`accepted`; non-terminal states have no
  disposition; Child view enforces the same failure/terminal-poll rules as the full view.
- Errors: `CollaborationError` `1.0-proposed`; codes in `fixtures/error_catalogue.json`.
  `404 RESOURCE_NOT_FOUND` is used for both missing and inaccessible jobs.
- Device projection never contains result refs, request refs or disposition.
- Example: `fixtures/consumer_examples/p1_job_poll_sequence.json` (actual harness output).

## 4. P2 / BE1 package (ports P3 consumes; P2 keeps authority)

| Port | P2 provides | Semantics expected by BE2 |
|---|---|---|
| `AuthorizationPort.decide(principal, action, scope)` | verified principal/grant, class/session scope | `create_job`, `read_job`, `cancel_job`; called on every command, replay and read (before ETag/304) |
| `EligibilityPort.check(scope, request_ref, job_type)` | consent/purpose, session state, recall, source expiry, kill switch, budget, current context revision | called on create, start, retry, completion and exposure; reason codes `CONSENT_REVOKED`, `SESSION_ENDED`, `CONTENT_RECALLED`, `SOURCE_EXPIRED`, `KILL_SWITCH`, `BUDGET_EXCEEDED` |
| `CancellationNotice` → `apply_cancellation_notice` | revoke/session-end/recall/kill-switch events | idempotent by `notice_id`; matches session, subject or job type within the organization |
| `ArtifactPort.describe/quarantine` | generic artifact descriptors (DATA-20) **with producer lineage** `producer_job_id`/`producer_attempt_id` (Q00 R01) | Admission requires org + producer lineage + sha256 match and no quarantine state. Quarantine applies only to refs owned by the same org/job/claimed attempt; it can include owned outputs with a bad claimed hash. Foreign/unknown refs are never mutated. (Q00 R03a) Descriptor also reports `quarantine_reason`; quarantined refs are never admitted; temporary guard rejections (`INVALID_STATE`, `INPUT_MISMATCH`) do not quarantine |
| `AuditPort.record` | DATA-35 audit sink | BE2 emits redacted events (diagnostic only as sha256) |
| `AiJobRepository` (Phase B) | adopted generic persistence contract | Phase A fake shows the needed unit-of-work: jobs CAS, command receipts, semantic index, completion receipts, outbox, notices |

CMD-59/60 stay BE1-owned; BE2 exposes projection/eligibility through ports only. Provider-copy
outcomes for DATA-34/H-DATA-REQUEST: `ProviderCopyLifecycleReport` with `fixture_marker` and
`actual_deletion_proven`; fixture receipts read `fixture_deleted_not_actual`.
(Q00 R05/R06) Purge requires a registry `scope_lock` atomic boundary: same-key concurrent calls
dispatch once and share the stored receipt; replaying an older key returns that request's own
result and never changes a copy a newer request already advanced. (Q00 A18a) `cancel_scope`,
`register_copy` and `purge_scope` all read/dispatch/save under the same scope lock, so a stale
cancellation cannot overwrite a purge result and a late copy in a purging scope is born
`purge_requested`. Fake concurrency only; durable equivalent belongs to Phase B.

## 5. P4 package (composition)

- Wire `build_ai_jobs_router(service, resolve_principal, prefix=...)` only after the namespace,
  identity port and durable repository are adopted; the fixture app is a test double.
- `AiJobDependencies` lists every port; Phase A fakes live under `infrastructure/ai_jobs/` and
  are marked `FIXTURE_ONLY_NOT_DURABLE`. They must not be imported by `app.py`.
- Worker path is internal: `start_attempt` / `report_progress` / `accept_completion` need a
  job-scoped worker capability (`WorkerCapabilityVerifier`). No HTTP completion route exists.
- One offline command for combined checks: `python features/FEAT-044-be2-ai-job-foundation/src/run_fixture_contracts.py [--with-http]`.

## 6. Compatibility and adoption notes

- Additive only: no legacy route/contract changed (`WorkflowJobV1`, story/whiteboard jobs untouched;
  their regressions pass). Namespace `/api/collaboration/v1` is the B22.1 candidate, mounted only
  in the fixture app.
- Candidate names: `AsyncJobView` ≙ FEAT-040 `JobStatusV1`; `CancellationNotice` ≙
  `CancellationNoticeV1`. Final names need the shared-registry cross-review.
- Adoption checkpoints still open: DATA-25/24 schema registry entry; ProviderCopyLifecycle owner
  sign-off (BE2-14); role allowlists (spec §6); `succeeded`+`stale` for context drift;
  non-retryable failure → `failed_exhausted`; cancel requires If-Match; retry/poll numbers;
  artifact producer lineage + `quarantine_reason`; authoritative/non-authoritative receipts;
  copy `scope_lock`. Per-consumer questions, evidence hashes and decision status:
  `PHASE_A_ACCEPTANCE_GATE_RECORD.md`.

## 7. Suggested next step

Follow `plan/BE2_ROADMAP.md` revision 2 / tracker: after Phase A checkpoint acceptance, Q01 is a
reviewable BE2-01 Phase B plan (durable repository/migrations, request/attempt CAS, receipts,
transactional outbox, queue adapter; restart/concurrency/fault-recovery acceptance). Its code
needs its own plan/approval, persistence/queue ADR and adopted BE1 ports. Other cards are queued
in the roadmap, not authorised by this handoff.
