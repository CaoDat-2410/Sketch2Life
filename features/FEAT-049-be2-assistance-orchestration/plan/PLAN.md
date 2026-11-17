# BE2-03 A1 — assistance request orchestration, offline component

- Status: APPROVED 2026-10-17 19:58 +07:00 (revision 3, approved bytes `PLAN_REV3_APPROVED.md`,
  SHA256 e1fce645…; D1–D11 as recommended; verbatim `../approvals/TASK_APPROVAL.md`)
- Plan revision: 3, 2026-10-17, Asia/Saigon (Claude correction of revision 2 per Codex re-review)
- Implementation status: A1 ACCEPTED at offline component scope 2026-10-17 23:24 +07:00
  (`../approvals/A1_COMPONENT_ACCEPTANCE.md`); card IN_PROGRESS / NOT_DONE
- Checkpoint: `ASSISTANCE_COMPONENT_OFFLINE` (A1). Full BE2-03 remains NOT_STARTED / NOT_DONE.
- Feature / branch: `features/FEAT-049-be2-assistance-orchestration`,
  `feature/be2-03-assistance-orchestration` (worktree `.worktrees/be2-03-assistance-orchestration`).
- Base: `f120c4fce8f7853e5ab5e061eff4bf916d45603c` = pushed BE2-02 C2 checkpoint
  (`origin/feature/be2-02-vision-correction`). **Stacked candidate branch**, not cut from dev; see §2.
- Authority: the user's direct 2026-10-17 requests to prepare BE2-03 planning and to correct it
  into revisions 2 and 3. They authorize planning only. D1–D11 (§13) are recommendations, not owner
  decisions. Approve this exact revision/SHA256 and the D-choices before any code. C1/C2
  approvals, accepted plans and acceptance bytes stay unchanged.
- Revision history: revision 1 (SHA256 `bb072cf5…`, 32784 bytes) was reviewed NEEDS_REVISION
  (`../evidence/notes/PLAN_CODEX_REVIEW_20261017.md`: A1-PR01 P1, A1-PR02–PR05 P2, two
  clarifications). Its bytes are kept as a historical draft in the ignored local planning area;
  it was never approved. Revision 2 (SHA256 `0894c39b…`, 48409 bytes) was re-reviewed
  NEEDS_REVISION, 0 P1 / 1 P2 (`../evidence/notes/PLAN_CODEX_REREVIEW_20261017.md`:
  A1-PR01-F1 shared fake commit boundary, plus three non-blocking notes); its bytes are kept the
  same way, never approved. Revision 3 changes only §8.2 (shared commit coordinator), §8.4
  (reader authority), §8.5, §9.1 (consumed row), §11 (R15a/R15b/R16 and test-boundary rule),
  §12 A1.4, §13 D2 note and §16. §16 maps every finding to plan text and tests.
- Neighbouring state kept as-is: BE2-01 IN_PROGRESS / WAITING_STUDIO (B6-CR01 open, B-12 HANDOFF,
  OwnerFence ASSUMED_CONTRACT); BE2-02 IN_PROGRESS / NOT_DONE (C1, C2 accepted at component scope).

Python paths below are relative to `backend/src/sketch2life/`; line numbers are at f120c4f.

## 1. Outcome and source coverage

Deliver, with synthetic fixtures and in-memory fakes only, the BE2-03 request owner: accept an
explicit Child/Teacher assistance request (DATA-21, CMD-32), validate scope/turn/audience/consent
per member, dedup/debounce/budget/cache it under an injected policy and clock, schedule exactly
one BE2-01 Vision analysis job through the foundation service, expose the trusted
`AssistancePin` that BE2-02 already consumes, handle cancellation (CMD-33), staleness and late
completion, and emit safe projections/audit candidates. No provider/model, Sketch generation,
real owner adapter, DB/queue, deployed route or Child exposure of AI output.

| Source (path, lines at f120c4f) | Obligation | A1 treatment |
|---|---|---|
| Master SRS FR024/025/028/029/030, lines 400–406; FR054, line 459 | Explicit request + Teacher manual trigger/cancel; levels; no stroke replacement, no idle inference; typed failure/log; dedup/cache/budget/debounce/stale (PROPOSED); queue/overload audit (PROPOSED) | FR024/028/030 core in A1; FR025 level passed through as policy-allowlisted value; FR029 typed refusals/audit candidates; FR054 only "audit every automated refusal", no priority queue |
| UC-019, lines 1276–1285 | Preconditions, main flow 1–5, budget/cache/cancel alternatives, AT-UC-019-P/N | Steps 1–3 and 5 (revalidation) in A1; step 4 (Sketch worker) simulated, §10 |
| UC-032, lines 1419–1428 | Help/review queue, overload disposition traceable | Out of A1 except safe Teacher projection fields; CMD-59 is BE1-12's |
| DATA-21, line 1648 | Command/response fields, Child/Teacher targeting, per-member audience, no inactivity request, stale/cancelled no late publish | Full field map §5 |
| DATA-25, line 1660; CMD-44 | Job view; stale is a disposition; completion checks | Consumed via BE2-01 ports, never rewritten |
| CMD-32/33, lines 1776–1777; B22.2 legend, lines 1739–1741 | T/D K V create `202`; T/D K M cancel, "target bound participant only" | Fixture handlers §10; both idempotency scopes §5 |
| B19.2 policy registry, lines 752–790 | `AI_REQUEST_DEBOUNCE` 5 s PROPOSED; `IDEMPOTENCY_TTL`; TBD ≠ 0/∞/disabled | Injected versioned fixture policy |
| B19.6 CS-008/011, lines 870–884; B19.10 RequestAssistance, CS-026, lines 948–974 | Verified principal vs contributor; per-command authorization; late results not published; each child's age, no mean | §7 checks |
| B19.11, lines 976–993; B22.1 idempotency/receipt/errors, lines 1710–1734 | Guard order, same key/different payload 409, receipt replay needs current disclosure, error codes | §7, §8.1 |
| FEAT-040 BE2-03 card, lines 534–544; H-* ledger, lines 126–147; BE2-14, lines 666–676; DAG line 189 | Deliverables, reviewers, acceptance ±, evidence; handoffs; policy owner BE2-14 | §3, §11, §12 |
| FEAT-044 BE2_ROADMAP §3–§4 (lines 86–168), §5–§6 (247–327) | Q05 exit; scope stop; component vs runtime vs integration; WIP 1 | §2, §14 |
| FEAT-048 C1/C2 handoff (`evidence/notes/H_AI_REVIEW_HANDOFF.md`), C2 review | AssistancePin, source-only input_hash, job scope mapping, typed context digest is C2's | §4 |

Offline PASS of A1 proves contract/fake behaviour only. It does not close FR030/FR054 runtime,
adopt any policy value, or mark BE2-01/02/03 DONE.

## 2. Baseline, stacking and WIP

- Parent chain: f120c4f contains BE2-01 foundation through `6dcc57e` (not accepted as a card,
  WAITING_STUDIO) and BE2-02 C1 + C2 commits (accepted components, card NOT_DONE). `origin/dev`
  (`f220781` at last fetch) contains neither. A future BE2-03 PR to dev must land after, or
  together with, its BE2-01/BE2-02 parent commits; this branch is not dev integration and does
  not approve the unfinished prerequisite runtime work.
- The owner workflow "branch per card from updated dev" (FEAT-044 tracker, 2026-10-16) is
  deviated from on purpose under roadmap §3.1 candidate-only substitution; the deviation is
  recorded in this feature's DECISIONS and the BE2 tracker.
- WIP 1: this planning opens no code slot. An approval of this plan must explicitly park
  BE2-02 (return: next C-checkpoint or real-provider gate) and keep BE2-01 WAITING_STUDIO
  (return: named Studio A17-fix01 run/review has priority when available).
- Lightning is not needed for A1. Windows lightweight checks only; no installs.

## 3. Dependency inventory (actual seams at f120c4f)

| Owner / seam | Existing fact | A1 treatment |
|---|---|---|
| BE2-01 `AiJobService.create_job` (`application/services/ai_jobs.py` 342–446) | Authorization 352–355 precedes receipt replay 384/401; `EligibilityPort.check` 389 and fence hold 406 before an independent commit 418–445 of job + semantic key + receipt + outbox; no queue call | Called only through BE2-03 `AssistanceJobPort`; never edited |
| BE2-01 eligibility checks | `_check(job)` 1239–1242 passes `scope`, active `request_ref`, `job_type`; checked and fenced at dispatch 566–582, start 662–681, completion 762, retry 900–913, status 974 | BE2-03 injects a request-aware `EligibilityPort` decorator (§8.2) — a new adapter over the existing port |
| BE2-01 dispatch `dispatch_outbox/_publish` 547–611 | Broker `QueueUnavailable` only in `_publish` 595–607: outbox lease released, returns false; job stays queued | §8.5 boundary 2 |
| BE2-01 attempt history (`domain/ai_jobs/model.py` 186–203, 231, 311–334, 390–408) | `AiJob.attempts` retains every `Attempt` with its own `started_at`; retry creates a fresh queued active attempt; `AiJob.started_at` is only the active attempt's | Budget evidence = any attempt with `started_at` (§9.1) via read-only `AiJobUnitOfWork.get_job`/`list_jobs` (`application/ports/ai_jobs.py` 338, 344) |
| BE2-01 workers (`infrastructure/ai_jobs/worker.py` 59→70; `fakes.py` FakeWorker 713–722) | `start_attempt` commits before `provider.run`; denied start returns without provider call | Provider start linearizes at the `start_attempt` commit |
| BE2-01 ports `Principal{teacher,admin,device}`, `AuthorizationPort`, `ClockPort`, `IdGeneratorPort`, `AuditPort`, `FakeOwnerFences` (`fakes.py` 79–98) | Fakes in `infrastructure/ai_jobs/fakes.py` | Reused types; BE2-03 adds owner ports for turn/roster/region/source |
| BE2-02 `AssistancePin`, `AnalysisScope` (`domain/vision_analysis.py` 307–337) | Contributor must be in audience; pin = assistance id, request revision, snapshot ref, context revision, scope | Produced unchanged by BE2-03 adapter implementing `AssistanceRequestPort` (`application/ports/vision_analysis.py` 141–144) |
| BE2-02 `job_scope_matches`, `check_lineage`, `check_input_hash` (vision_analysis.py 387–443) | Job session/subjects/purpose/target = pin; `job_type == "vision_analysis"`; input_hash = `SourceSnapshot.input_hash()`; terminal job → `JOB_TERMINAL` (411–412) | BE2-03 creates jobs exactly in that shape (A1-P09) |
| BE2-02 read APIs (`application/services/vision_analysis.py` 828 `downstream_meaning`, 853 `analysis_record`) | Authorized current read of a stored analysis and meaning state | Completion/cache gate (§8.4, §9.2). `record_observation` (304–317) is never called by BE2-03 |
| BE2-02 C2 `VisionContextSourcePort`, `RequestContextFact` enums (vision_context.py 57–72, 267–288) | C2-local candidate enums (`describe_drawing`, `support_meaning_check`; `brief`, `standard`) ≠ DATA-21 enums | Not mapped in A1 (D9); C2 context digest stays C2's |
| DATA-21 `ShapeSpec` 0.1-candidate (`contracts/schemas/ai_contract_candidates.py` 211–216) | Shallow required/enum check | Unchanged; new strict contracts must still pass it (A1-C02) |
| BE1 core ports (`application/ports/core_foundation.py`), `ActiveChildTurn` | Membership/consent/profile ports; no versioned H-SESSION-CONTROL / H-CANVAS-SYNC / H-CLASS-CONSENT handoff, no region-policy or roster port | BE2-03 consumer ports + fakes, ASSUMED_CONTRACT; no BE1 DB reads |
| BE2-14 policy | No published policy/budget port (teammate branch `origin/feature/be2-08-14` b358bc7 is on BE2-12) | Consumer-side `AssistancePolicyPort` proposal + FIXTURE_ONLY adapter (D10) |
| BE2-04 Sketch | Not started | Intent-only `SketchStagePort` fake (D8) |

## 4. Request vs job vs analysis

| Concept | Owner | Identity / revision | Lifecycle | A1 role |
|---|---|---|---|---|
| Assistance request (DATA-21) | BE2-03 | `assistance_id`, `request_revision` (ETag `"assistance:<id>:<rev>"`) | §6 | Created, cancelled, staled here |
| AI job / attempt (DATA-25) | BE2-01 | `job_id`, `job_revision`, `attempt_id` | queued…cancelled; disposition separate | One `vision_analysis` job per scheduled request; BE2-03 holds `job_id` only |
| Vision analysis (DATA-22) | BE2-02 | `analysis_id`, `analysis_revision` | accepted/stale/rejected; meaning states | BE2-03 reads outcome/meaning state; never corrects |
| Sketch proposal (DATA-23) | BE2-04/05 | — | — | Not created; intent only (D8) |

Agreement with BE2-02 (A1-P09):

- `AssistancePin.request_revision` = the request revision pinned into the job's `RequestRef`.
- `input_snapshot_ref` = `SourceSnapshot.snapshot_ref` resolved from DATA-21 `checkpoint_ref`;
  `RequestRef.input_hash` = `SourceSnapshot.input_hash()` (C1 source-only formula, unchanged).
- `RequestRef.context_revision` = owner context revision current at commit (must equal the
  client's DATA-21 `context_revision`).
- Job `target_id = assistance_id`, `session_id`, `subject_refs = audience`, `purpose_code` =
  scope purpose; `job_type = "vision_analysis"`.
- BE2-03 additionally pins `assistance_context_digest` (§8.3): its own binding of the owner
  facts it checked. It is distinct from C2's `payload_digest`/`context_digest`, never substituted.
- Render/admission bindings stay BE2-02's; BE2-03 checks admission PASS before scheduling only
  to avoid a wasted job (C1 re-checks).

## 5. Contracts and field/source map

New module `contracts/schemas/assistance_requests.py`, strict (`extra="forbid"`), all
`0.1-candidate`: `AssistanceRequestCommandV1`, `AssistanceRequestRecordV1` (Teacher/internal),
`AssistanceRequestDeviceViewV1`, `AssistanceCancelCommandV1`, `AssistanceReceiptEnvelopeV1`,
`AssistanceEventV1`. The DATA-21 `ShapeSpec` is not edited. Labels: **S** = SRS field;
**E** = existing contract/code; **TC-nn** = technical candidate recorded in DECISIONS.

| Field | Label | Rule |
|---|---|---|
| `canvas_id` | S DATA-21 | OpaqueId; must resolve inside principal's org/class/session |
| `checkpoint_ref{checkpoint_id,document_epoch,server_sequence,hash}` | S DATA-21 | Resolved by `AssistanceSourcePort` to `SourceSnapshot` (E) + owner `server_sequence`; epoch = current document epoch; `hash` = `checksum_sha256`; render admission PASS |
| `target_scope` union `individual{participant_id}` / `group{group_id}` | S DATA-21 | Child: individual = bound current-turn participant only. Teacher: authorized individual or group |
| `target_region_id` | S DATA-21 (nullable) | Must exist in current region policy; Child must be permitted in it (TC-05); never used for age |
| `requested_level` | S DATA-21 (`AssistanceLevel`, taxonomy PROPOSED) | Opaque level token allowlisted by policy snapshot (TC-02); no fixed taxonomy |
| `child_intent` | S DATA-21 (nullable LongText) | Normalized long text (`normalize_long_text`, E), device-originated requests only (TC-09); stored internal, not sent to Vision (C2 Q2), not in device views of others |
| `request_reason` | S DATA-21 | Closed enum `child_request`, `teacher_request`, `explicit_help_signal`; no inactivity value exists |
| `context_revision` | S DATA-21 | Must equal owner current revision else 409 `STALE_CONTEXT` |
| `client_request_id` | S DATA-21 | OpaqueId; part of payload fingerprint; not the idempotency key; not semantic |
| CMD-32 `Idempotency-Key` | S B22.1 | Header; scope `(org, principal, "AssistanceRequestCreateV1", canvas_id, key)`; fingerprint = canonical normalized command |
| CMD-33 `Idempotency-Key` + `If-Match` | S B22.1, CMD-33 | Scope `(org, principal, "AssistanceRequestCancelV1", assistance_id, key)`; fingerprint = `{assistance_id, if_match_revision, reason_code}`; missing key → 400 `MALFORMED_REQUEST`; missing If-Match → 428 |
| `assistance_id`, `request_revision` | S | Server ids; revision rule D2 |
| `organization_id`, `session_id`, `group_id` | S | Server-derived from canvas/session |
| `validated_target_scope` | S | Server echo after validation |
| `requester_principal` | S | `{principal_id, role}` from identity port |
| `contributor_snapshot` | S | `{participant_id, turn_id, turn_revision}`; Child: bound turn; Teacher: D5 |
| `age_policy_ref` | S | Policy ref/version used for eligibility (36–155 via `validate_age_months`, E) |
| `audience_age_context_refs` | S | One `{participant_id, age_provenance_ref, age_revision}` per member; no months/bands in projections |
| `consent_revision_refs` | S | One `{participant_id, consent_record_ref, revision}` per member |
| `status` | S (values TC-01) | §6 |
| `job_id` | S | BE2-01 job id; null while `scheduling` |
| `created_at` | S | Fake clock |
| `purpose_code` | TC-03 | Server-chosen AI-assistance purpose from policy; not client-supplied |
| `assistance_context_digest` | TC-08 | §8.3 |
| `semantic_identity` | TC-04 | §8.3; internal only |
| `policy_ref{policy_id,version,status}` | TC-02 | Pinned from `AssistancePolicyPort` |
| `budget_reservation{reservation_id,state}` | TC-06 | Teacher/internal only; §9.1 |
| `scheduling{create_key, principal, request_revision, job_id, cleanup}` | TC-10 | Internal; §8.2 |
| `cache_hit_of{assistance_id,request_revision,job_id,analysis_id,analysis_revision}` | TC-07 | Provenance of reuse, Teacher/internal only |
| `status_reason` | TC-01 | Closed tokens (`CANCELLED_BY_TEACHER`, `CANCELLED_BY_CHILD`, `CONTEXT_CHANGED`, `SOURCE_CHANGED`, `SUPERSEDED_BY_FACT_CHANGE`, `CONSENT_REVOKED`, `SESSION_ENDED`, `SCHEDULE_REFUSED`, `JOB_FAILED`, …) |

Device view (`AssistanceRequestDeviceViewV1`): `assistance_id`, `request_revision`, coarse
`status` (`pending`, `cancelled`, `unavailable`), `job_id`, `poll_after_ms`. No audience, ages,
consent refs, intent, budget, cache, analysis or provider details.

## 6. Request states and actors

States (TC-01; distinct from DATA-23 pipeline states and DATA-25 job states):
`scheduling` → `scheduled` → `analysis_ready` | `failed`; `scheduling`/`scheduled` →
`cancelled` | `stale`. Terminal: `analysis_ready`, `failed`, `cancelled`, `stale`.
`analysis_ready` means BE2-03 committed the handoff of an accepted BE2-02 analysis for this pin;
it is not a proposal, review or Child availability. Refusals (scope/consent/policy/debounce/
budget) create no request record; they produce a refusal audit candidate only.

Each request record also carries an internal `settlement` axis (TC-10) independent of `status`:
`open` (a job may exist or be created) → `settled` (no job can start any further attempt for
this request and the reservation is final). A terminal `cancelled`/`stale` request can remain
`open` while cleanup runs; it never returns to a non-terminal status.

| Transition | Trigger | Actor | Guard |
|---|---|---|---|
| ∅ → `scheduling` | CMD-32 | Child device (`child_request`/`explicit_help_signal`, individual = bound turn) or Teacher (`teacher_request`/`explicit_help_signal`) | §7 order; budget `held` |
| `scheduling` → `scheduled` | job created/replayed by BE2-01 and linked | System (scheduler) | Link CAS only while `scheduling` at the pinned revision (§8.2) |
| `scheduled` → `analysis_ready` | handoff commit (§8.4) | System | Linearization point; request still `scheduled` at pinned revision; current gate passes |
| `scheduled` → `failed` | job `failed_exhausted`/`blocked_unsafe`, or analysis `rejected` | System | Typed reason; no retry loop in BE2-03 |
| `scheduling`/`scheduled` → `cancelled` | CMD-33 | Teacher in class/session scope: any request. Child device: individual request whose target is its bound participant (D3) | If-Match request revision; group requests Teacher-only |
| `scheduling`/`scheduled` → `stale` | owner notice, fact-change supersession (§8.3), schedule refusal, or failed handoff gate | System | Late results never publish |

Child and Teacher rights are deliberately unequal: Child cannot target a group, another
participant or a non-current turn; cannot cancel a group request or another participant's
request. Teacher actions require current TeacherAssignment; Admin has no request/cancel role in
A1 (CMD-32/33 auth T/D only). After `analysis_ready` a cancel is 409 `INVALID_STATE` (D11).

## 7. Validation order and per-member checks

Order (B19.11 + B22.1): parse/size/schema → verified principal + disclosure scope → idempotency
receipt lookup (same key + same fingerprint → stored receipt after current read check; different
fingerprint → 409 `IDEMPOTENCY_PAYLOAD_MISMATCH`) → org/class/session/canvas scope (other class
→ 404 concealment) → session lifecycle `active` (paused/ended → 409 `INVALID_STATE`) → grant +
turn (Child: active bound turn, target = turn participant; `TURN_CLOSED`/`GRANT_REVOKED`) →
target/group/region → checkpoint/source/admission + `context_revision` (`STALE_CONTEXT`) →
audience resolution → **each member separately**: duplicate ids refused before any set/dict
conversion; membership current; age known and 36–155 (`AGE_NOT_SUPPORTED`); consent effective and
AI-assistance purpose granted (`CONSENT_REQUIRED`) → policy enabled/level allowed
(`POLICY_UNRESOLVED` when absent/TBD; disabled → 403 `FORBIDDEN_SCOPE`) → resolved pin and
digest (§8.3) → semantic dedup → debounce (429 `RATE_LIMITED` + `retry_after_s`) → budget
reservation (429 `BUDGET_EXCEEDED`) → commit request + reservation + receipt + audit intent
atomically (fake UoW) → scheduling (§8.2).

No inferred age, no inferred lack of knowledge, no automatic request from idle (closed reason
enum; no API takes inactivity), no averaging of mixed-age groups; one failing member refuses
the whole request (D4) with a member-agnostic code. Audience max 64 (aligned with C2
`CONTEXT_AUDIENCE_MAX`; pilot 40 is a target, not this bound).

## 8. Idempotency, scheduling, dedup, cancellation and completion

### 8.1 Command receipts (CMD-32 and CMD-33)

- Same key + same fingerprint returns the stored original status/body with `replayed=true`
  (accepted-receipt rule): a CMD-33 replay still returns the original `cancelled` receipt after
  the request revision moved again or the Child's turn closed. Disclosure is re-checked first:
  a caller whose read scope was revoked gets 404 and no receipt.
- Same key + different fingerprint → 409 `IDEMPOTENCY_PAYLOAD_MISMATCH`; missing key → 400
  `MALFORMED_REQUEST`; missing If-Match on CMD-33 → 428; stale If-Match → 412.
- Receipts are written in the same fake UoW as the state change; refusals reserve nothing.

### 8.2 Scheduling, in-flight creation and cleanup (A1-PR01, A1-PR05)

**Retained scheduling identity.** At request commit BE2-03 stores, immutable for the request:
`create_key = "assist:<assistance_id>:<request_revision>:vision"`, the original requester
`Principal` (execution authority), the pinned `RequestRef` and `JobScope`. Every create attempt
re-sends exactly the same `CreateJobCommand` (same principal, key, payload), so BE2-01's command
receipt replay (service 384, 401) or semantic key (364–374, 387, 404) returns the one existing
job.

**Request-aware eligibility (prevents provider start after cancel).** The BE2-01 service used by
BE2-03 is composed with `AssistanceEligibility(owner_eligibility, request_reader, fences)`, a new
adapter implementing the existing `EligibilityPort`. For `job_type == "vision_analysis"` and
`request_ref.request_id` = an assistance id it returns ineligible when the request is missing,
`cancelled` or `stale`, or its revision ≠ `request_ref.request_revision` (reasons
`CANCELLED_BY_TEACHER`/`CANCELLED_BY_CHILD`/`CONTEXT_CHANGED`/…); otherwise (`scheduling`,
`scheduled`, `failed`, `analysis_ready`) it returns the owner decision, so status reads of a
completed job (service 974) are unaffected. Its fence is an epoch that BE2-03 bumps together
with every request transition to a terminal status (`cancelled`, `stale`, `failed`,
`analysis_ready`). BE2-01 holds that fence in each create (406), dispatch (576), start (672),
retry (907) and completion (762) transaction and retries on staleness. A1 fake detail: the
decision carries one fence slot, so the fake composes the owner epoch and the request epoch
into one fence scope (`eligibility:<org>`, bumped by both) — coarse; a real per-request owner
fence is a B-12/OwnerFence runtime item (§14).

**Shared fake commit coordinator (rev3, A1-PR01-F1).** An epoch compare alone is not enough:
`FakeOwnerFences.hold` (`infrastructure/ai_jobs/fakes.py` 94–98, forwarded by `_UnitOfWork`
230–231) only compares at that instant, and `InMemoryAiJobStore.transaction` (471–479)
publishes the staged state later under its own lock, so a separate cancellation could
publish between the hold and the foundation commit (witness:
`../evidence/notes/PLAN_CODEX_REREVIEW_20261017.md`). A1 therefore composes, in new
`infrastructure/assistance/` code only, one `AssistanceCommitCoordinator` shared by:

1. `CoordinatedAiJobRepository`, a decorator implementing the existing `AiJobRepository`
   protocol over the foundation store: `transaction()` acquires the coordinator, then enters the
   inner `InMemoryAiJobStore.transaction()`, yields its unit of work, and releases the
   coordinator only after the inner context has exited (commit published at line 479, or the
   exception propagated with nothing published). Every foundation write transaction — create,
   dispatch acceptance, start, retry, completion, cancel, notice — is therefore one indivisible
   unit from the hold through its commit. The BE2-01 service in the A1 composition receives only
   this decorator; foundation source is unchanged.
2. The assistance fake unit of work: request state, receipt, ledger, audit intent **and** the
   epoch bump are staged and published together inside one coordinator section; an exception
   before publication publishes neither state nor epoch.
3. `AssistanceEligibility` reads the request state and the current epoch together inside one
   coordinator section and returns that epoch as the fence, so the decision and its fence
   describe the same snapshot. If the hold later passes inside a coordinated foundation
   transaction, no assistance publication can have happened since the decision was read, and
   none can happen until that transaction commits. Owner-fact changes in fakes are published
   through the same coordinator helper.

Lock ordering: coordinator → foundation store lock, never the reverse; no BE2-03 code takes the
store lock directly (read-only `snapshot()` takes only the store lock and never waits for the
coordinator). The assistance unit of work never calls the BE2-01 service while it holds the
coordinator; the scheduler and cleanup call BE2-01 between assistance transactions.

Re-entry/deferral: the coordinator tracks foundation-transaction depth per thread. A
cancellation/stale publication requested while the current thread is inside a coordinated
foundation transaction (for example a same-module hook or callback) is **not** applied there; it
is queued and executed as its own assistance transaction after the outermost foundation
transaction exits, whether that transaction committed or raised. Its order is therefore
"after that foundation commit", and tests must label it so. Another thread requesting a
publication blocks on the coordinator until the foundation commit. Locks are released in
`finally`; a deferred publication that itself raises publishes nothing and leaves the
coordinator free. Waiting is bounded by the in-memory transaction; no lock is held across a
provider call (workers call the provider after `start_attempt` returns).

**Guarantee (fake level).** Provider start linearizes at the coordinated `start_attempt` commit
(workers call the provider only after a successful start, `worker.py` 59→70). Exactly one of:
(a) the start transaction commits before the cancel/stale publication — that attempt may run,
BE2-03 records `consumed` and issues cleanup; or (b) the cancel/stale publication is first —
the start's hold fails (or its decision is re-read) and every later start/dispatch/retry is
denied by the fenced eligibility, and the job is cancelled by BE2-01 itself. This is a fake
composition contract, not a production SQL locking or real OwnerFence claim; no exactly-once
provider claim.

**Scheduler step outcomes** (all with the retained identity):

| Observed by scheduler | Action |
|---|---|
| `create_job` returns job (`created`/`deduplicated`/replay) and link CAS wins (request still `scheduling` at pinned revision) | `scheduled`, `job_id` linked; outbox dispatch is the foundation's |
| Job returned but link CAS loses (request already `cancelled`/`stale`) | Store `job_id` in the request's cleanup record (internal, no status change, no revival); call `cancel_job` with the canceller principal and read `job_revision` when that principal is still authorized, otherwise rely on fenced eligibility; settlement stays `open` |
| `create_job` refused before commit (eligibility/authorization error) | Request → `stale` (`SCHEDULE_REFUSED`) if still `scheduling`; then trusted lookup (below) to prove no job; `settled` + reservation `released` only if none |
| Retryable `IDEMPOTENCY_CONFLICT`/`STALE_CONTEXT` (service 213–219) | Keep `scheduling`; retry same command |
| Reply lost / process crash after BE2-01 commit, before link (A1-PR05 boundary 1) | Next scheduler pass re-sends the same command → receipt replay returns the same `job_id` → link; if the requester's authorization was revoked meanwhile, the trusted lookup finds the job by `target_id = assistance_id` and `request_ref` |

**Trusted lookup and settlement.** A read-only `AssistanceJobReader` (new adapter, pattern of
`infrastructure/vision_analysis/job_lineage.py`) opens a BE2-01 unit of work and reads jobs by
`job_id` or, when no id is known, scans `list_jobs()` for `scope.target_id == assistance_id`
(fake/component scale; an index is runtime work). It never writes. A request becomes `settled`
only when every job found for it is terminal (`cancelled`, `failed_exhausted`, `blocked_unsafe`,
`succeeded`) or no job exists after the create path is closed (status terminal, no create in
progress for the retained key). Until then the reservation stays `held` and a cleanup
obligation remains on the record; no time-based release. Lookup/repository failure = evidence
unknown = stay `open`/`held`.

**Broker down after linking (A1-PR05 boundary 2).** `QueueUnavailable` exists only in
`_publish` (595–607): the job stays `queued`, the outbox lease is released and a later
`dispatch_outbox` retries. BE2-03 does nothing special: request stays `scheduled`, reservation
`held`, exactly one job. Tests inject the broker failure into the BE2-01 fake queue, never into
`create_job`.

### 8.3 Semantic identity, digest and dedup (A1-PR02)

`assistance_context_digest` (TC-08) = strict canonical SHA256 (C2 rules: NFC strings, integers
only, explicit null, sorted keys; reuse `strict_canonical_sha256`, not a copy) of the resolved
owner facts: organization, class, session, canvas, group and roster/membership revision,
target scope, region id + region-policy revision, contributor participant, exact audience
sorted by participant id with per member `{completed_age_months, age_provenance_ref,
age_revision, consent_record_ref, consent_revision, purpose_granted}`, purpose, policy
ref/version, context revision, and the resolved source `{snapshot_ref, checkpoint id/epoch/
server_sequence/checksum, render_ref, render_sha256, input_hash}`.

`semantic_identity` (TC-04) = strict canonical SHA256 of `{org, session, canvas, target scope,
region, checkpoint_ref, input_hash, sorted audience ids, purpose, requested_level, reason class
(device|teacher), child_intent sha256 or null, context_revision, policy ref/version,
assistance_context_digest}`. Excluded operation identities: `assistance_id`, idempotency keys,
`client_request_id`, requester principal/device/grant/turn ids and revisions, correlation ids,
timestamps — those are re-checked freshly for every caller but do not make two requests
semantically different.

Dedup returns an existing request only when it is `scheduling`/`scheduled`, its stored
`semantic_identity` is byte-equal to the newly computed one, and the caller may read it. Same
operation-level target `(canvas, target, region, checkpoint_ref, level)` but a different
digest (changed roster, same-revision age/consent movement, different resolved render) is **not**
a duplicate: the older non-terminal request is moved to `stale` (`SUPERSEDED_BY_FACT_CHANGE`,
cleanup per §8.2) because its pinned facts are no longer current, and the new request continues
validation. A request staled this way is not counted by debounce.

### 8.4 Completion, handoff and cancel ordering (A1-PR04)

Completion is observed by BE2-03 polling/reading job state, never by worker replay. When the
linked job is `succeeded`, BE2-03 reads the BE2-02 analysis for the pinned `(job_id, attempt)`
through `analysis_record` + `downstream_meaning` and checks: analysis
`accepted`, `downstream_meaning.state != "not_applicable"`, exact bindings (snapshot ref,
checkpoint id/checksum, render hash, context revision; typed binding if present) equal the pin,
and the current `assistance_context_digest` recomputed from owner facts is unchanged.

Reader authority (rev3): those Vision read methods require an authorized scoped Teacher
principal (`application/services/vision_analysis.py` 878–892). `AnalysisOutcomePort` is
therefore constructed with an explicitly injected Teacher reader principal for that class/
session scope (a composition/fixture setting, checked by the BE2-02 authority port like any
Teacher). It is never derived from request fields, and a Child/device principal is never passed
to these methods. The requesting device's own disclosure and authorization are checked
independently by BE2-03 before any status or result reference is returned to it.

**Linearization point** = the BE2-03 handoff commit: one fake UoW transaction that CASes the
request `scheduled`@pinned revision → `analysis_ready`, writes the H-AI-REVIEW handoff event
and the simulated Sketch intent. Rules (D11):

| Order | Result |
|---|---|
| Cancel/stale commits before handoff commit (including when BE2-02 already **accepted** the observation) | Handoff CAS loses: no handoff event, no Sketch intent. The BE2-02 analysis stays BE2-02 history (C1 lineage now sees the bumped pin revision); request `cancelled`/`stale` |
| Handoff commits first | Request terminal `analysis_ready`. A later CMD-33 returns 409 `INVALID_STATE` (a same-key replay of an earlier accepted cancel still replays). The emitted intent is not withdrawn by BE2-03; downstream invalidation is BE2-04/05's pipeline (`cancelled`/`stale`/review reject) and BE2-02 owner notices |
| Gate fails at completion (digest/binding moved, meaning not_applicable) | `stale` (`CONTEXT_CHANGED`/`SOURCE_CHANGED`), no handoff |
| Analysis `rejected` / job `failed_exhausted`/`blocked_unsafe` | `failed`, no handoff |

Owner notices after `analysis_ready` do not reopen the request.

### 8.5 Owner notices

`apply_owner_notice` (consent revoked, session ended, turn/grant revoked, canvas restored) is
idempotent by notice id, moves matching `scheduling`/`scheduled` requests to `stale`/`cancelled`
with fence bump and cleanup per §8.2, and keeps history. Fake concurrency is one in-memory UoW
per module, joined at commit boundaries by the shared `AssistanceCommitCoordinator` (§8.2), with
controlled interleaving hooks (as in BE2-01/02 tests). A hook that runs inside a coordinated
foundation transaction may only request a publication, which is deferred until that
transaction exits; it proves the fake protocol, not PostgreSQL isolation.

## 9. Budget, debounce and cache

Policy comes from `AssistancePolicyPort.current(scope) -> AssistancePolicySnapshot` (D10):
`policy_id`, `version`, `status` (`FIXTURE_ONLY_NOT_ADOPTED` in A1), `assistance_enabled`,
`allowed_levels`, `debounce_seconds`, budget limits by scope, `cache_enabled`. Clock is the
BE2-01 `ClockPort` fake. FIXTURE_ONLY example values (not production): debounce 5 s (B19.2
candidate), per-target-per-session 3 provider stages, per-session 20.

### 9.1 Budget ledger (A1-PR03)

Ledger owned by BE2-03; values owned by BE2-14. Unit = one scheduled provider stage (D6).
States are monotonic: `held` → `consumed` (final) or `held` → `released` (final); `consumed`
never returns to `held`/`released`.

Evidence of provider use = the trusted attempt history: any `Attempt.started_at` non-null in
`AiJob.attempts` for any job found for the request (§8.2), read through `AssistanceJobReader`.
Current job state and `AiJob.started_at`/Teacher projection (active attempt only) are never
used as evidence.

| Situation | Reservation |
|---|---|
| Request committed | `held` atomically with the request |
| Dedup / receipt replay / cache hit / refusal | none taken |
| Any attempt of any job for the request has `started_at` (first time observed, any later state incl. retry-queued, cancelled, succeeded, failed) | `consumed` |
| Request settled (§8.2) and the history of every found job shows no started attempt (e.g. cancelled while queued; dispatch-lost attempt then retry never started) | `released` |
| Already `consumed` while cleanup/settlement is still open | stays `consumed` |
| Settlement open, history unreadable, or job possibly still creatable, and not yet consumed | stays `held` (conservative) |

BE2-01 retries of the same job never take a second unit. Exhaustion → 429 `BUDGET_EXCEEDED`
before commit; no request, no job, refusal audit candidate. Teacher override is not in A1.

### 9.2 Debounce and cache

Debounce: a semantically different request for the same `(canvas, target)` within the policy
window after the previous counted request → 429 with retry hint; requests staled by fact-change
supersession are not counted.

Cache (D7): reuse of a BE2-02 analysis for a **new** request only when the new request's
`semantic_identity` minus operation fields equals the cached entry's (same session, exact
audience, source/input_hash, context revision, `assistance_context_digest`, policy, level,
purpose) and a supported current-read gate passes: the original request is `analysis_ready`,
its job `succeeded`, `analysis_record` readable for the new caller's scope, record status
accepted, `downstream_meaning.state != "not_applicable"`, exact bindings equal (as §8.4), and
each member's consent/age/purpose is current. `record_observation` is never invoked for a cached
or terminal job. A hit creates its own request (own audit, no budget) ending `analysis_ready`
with `cache_hit_of` pointing at the original `assistance_id`/`request_revision`/`job_id`/
`analysis_id`/`analysis_revision`; the analysis keeps its original provenance and is not
relabelled. No cross-session or cross-audience reuse; no proposal/review/overlay is cached or
released; every downstream Sketch still needs per-item Teacher review.

## 10. Delegation and simulation

- Vision: only through `AssistanceJobPort` → BE2-01 `AiJobService`, the `AssistanceEligibility`
  decorator, the read-only `AssistanceJobReader`, and `AnalysisOutcomePort` → BE2-02 read APIs.
  The A1 chain test runs the real BE2-01 and BE2-02 services over their existing fakes with a
  scripted offline observation provider. No foundation/Vision source edit.
- Sketch (D8): the handoff transaction records `SketchStagePort.request_sketch(pin,
  analysis_ref)` as an intent marked `SIMULATED_NO_PRODUCER`. No BE2-01 sketch job type, no
  DATA-23, no reservation for the Sketch stage in A1, no success claim.
- HTTP: `interfaces/http/routers/assistance_requests.py` + `assistance_requests_fixture_app.py`
  (CMD-32 `202` with job/assistance refs, CMD-33 with Idempotency-Key + If-Match), not mounted in
  the live app; a test asserts the live app has no assistance route.
- Projections/events/handoffs: `AssistanceRequestRecordV1` (H-AI-REVIEW request
  status/context/target), safe budget/status summary for H-OPERATIONS, device view; audit/event
  candidates `assistance.requested|deduplicated|refused|scheduled|cancelled|stale|superseded|
  failed|analysis_ready|sketch_intent_simulated|cleanup_settled` with deterministic event ids;
  delivery NOT_RUN. CMD-59 read-model composition remains BE1-12's.

## 11. Acceptance cases (A1)

"Controlled" = deterministic interleaving hooks in fakes. Every race test respects the §8.2
atomic boundary: a same-thread hook inside a coordinated foundation transaction can only request
a cancellation, which is deferred and recorded as committed after that transaction; no test
publishes request state or epoch inside such a unit, and expected orders are named by actual
commit order.

| ID | Given / when | Expected | Test (proposed) |
|---|---|---|---|
| A1-P01 | Child, bound turn, individual self target, eligible, valid checkpoint | `scheduling`→`scheduled`, one vision job, `held`; no canvas mutation | service |
| A1-P02 | Teacher group request, mixed ages each 36–155, consent each | One job; subject_refs = audience; per-member refs; no mean | service |
| A1-P03 | CMD-32 same key + payload replayed | Original receipt, `replayed`, no job/budget change | service |
| A1-P04 | Different key, byte-equal semantic identity, non-terminal | `deduplicated`, same ids, no reservation | service |
| A1-P05 | Teacher cancels `scheduled` request whose job is queued, never started | `cancelled`; job cancelled; settled; `released` | chain |
| A1-P06 | Child cancels own individual request | `cancelled` | service |
| A1-P07 | Job succeeds, analysis accepted, gate passes | Handoff commit: `analysis_ready`, handoff event, Sketch intent simulated; `consumed`; no Child exposure | chain |
| A1-P08 | New request equals a cached `analysis_ready` entry; current-read gate passes | New record `analysis_ready`, `cache_hit_of` original ids, no job/budget; `record_observation` not called | chain |
| A1-P09 | Pin adapter for a scheduled request | C1 `check_lineage`=PROCEED, `job_scope_matches`, `check_input_hash`=PROCEED | chain |
| A1-N01 | Child target ≠ bound participant / group target | 403 `FORBIDDEN_SCOPE`, no job/budget | service |
| A1-N02 | Turn closed / grant revoked | 409 `TURN_CLOSED` / 403 `GRANT_REVOKED` | service |
| A1-N03 | Other class/session/canvas | 404, no existence leak | service |
| A1-N04 | One member consent/purpose missing | 403 `CONSENT_REQUIRED`, no provider/budget | service |
| A1-N05 | One member age null / 35 / 156 in a group with eligible others | 422 `AGE_NOT_SUPPORTED`; no averaging | service |
| A1-N06 | Roster returns duplicate participant | Refused before conversion; no job | service |
| A1-N07 | CMD-32 same key, changed payload | 409 `IDEMPOTENCY_PAYLOAD_MISMATCH` | service |
| A1-N08 | Client context_revision old / checkpoint epoch or hash mismatch / admission not PASS | 409 `STALE_CONTEXT` | service |
| A1-N09 | Policy absent / disabled / level not allowed | 409 `POLICY_UNRESOLVED` / 403 / 422 | service |
| A1-N10 | Budget exhausted | 429 `BUDGET_EXCEEDED`, no request/job, refusal audit | service |
| A1-N11 | Semantically different request inside debounce window | 429 `RATE_LIMITED` + retry hint | service |
| A1-N12 | Inactivity/idle-like reason or missing reason | 422; no request | contract |
| A1-N13 | Child cancels group or other participant's request | 403 | service |
| A1-N14 | CMD-33 without If-Match / stale If-Match / after `analysis_ready` | 428 / 412 / 409 `INVALID_STATE` | service |
| A1-N15 | Consent revoked after scheduling (owner notice) | `stale`; job denied at dispatch/start or cancelled; late result no handoff | chain |
| A1-N16 | CMD-32 or CMD-33 receipt replay after caller's scope revoked | 404, no disclosure | service |
| A1-N17 | Cache candidate with changed context/consent/policy/audience/binding, or meaning `not_applicable` | Miss → normal path; never reuse | chain |
| A1-N18 | `child_intent` too long / control chars; Teacher-supplied child_intent | 422 | contract |
| A1-N19 | Session paused/ended | 409 `INVALID_STATE` | service |
| A1-N20 | CMD-33 missing Idempotency-Key | 400 `MALFORMED_REQUEST` | service |
| A1-N21 | CMD-33 same key, changed reason/If-Match | 409 `IDEMPOTENCY_PAYLOAD_MISMATCH` | service |
| A1-N22 | CMD-33 accepted, then revision bumped again / Child turn closed; same key+payload replayed | Original `cancelled` receipt, `replayed` | service |
| A1-N23 | Same numeric context revision, no notice; roster changed A/B → A/C; new request | No dedup into A/B job; old request `stale` (`SUPERSEDED_BY_FACT_CHANGE`); new job subjects A/C | service |
| A1-N24 | Same revision, no notice; one member's age months or consent record changed | Different digest; no dedup; old request superseded | service |
| A1-N25 | Same checkpoint_ref, no notice; resolved render hash changed | Different input_hash; no dedup; old request superseded | service |
| A1-R01 | Two concurrent identical submissions, different keys | One request/job | races |
| A1-R02 | Two concurrent same-key submissions | One commit, one replay | races |
| A1-R03a | Cancel commits before handoff commit, after BE2-02 accepted the observation | Handoff CAS loses: no handoff/intent; request `cancelled`; analysis history kept | chain races |
| A1-R03b | Handoff commits before cancel | `analysis_ready`; cancel → 409 `INVALID_STATE`; intent stays | chain races |
| A1-R04 | Context/owner fact moves between scheduling and completion | `stale`, no handoff; `consumed` (attempt started) | chain |
| A1-R05 | Last budget unit raced by two targets | Exactly one reserves | races |
| A1-R06 | Start commit wins against cancel | Attempt runs; request `cancelled`; `consumed`; no handoff | chain races |
| A1-R07 | Completion after request stale | No resurrection, no handoff | chain |
| A1-R08a | Reply lost after BE2-01 create commit, before link; scheduler re-sends same command | Same `job_id` via receipt replay; one job; linked | chain races |
| A1-R08b | Broker unavailable during `dispatch_outbox` after link | Request `scheduled`, job `queued`, `held`; later dispatch → one job dispatched once | chain |
| A1-R09 | Cancel commits before `create_job` commit | Create refused by fenced eligibility; trusted lookup finds no job; `settled`, `released` | chain races |
| A1-R10 | Cancel commits after `create_job` commit, before link | Link CAS loses; job id kept in cleanup; dispatch/start denied, job cancelled by BE2-01; then `settled`, `released`; request never re-enters `scheduled` | chain races |
| A1-R11 | Stale (owner notice) in the same two windows as R09/R10 | Same as R09/R10 with `stale` | chain races |
| A1-R12 | Attempt 1 started and failed retryably; job queued for attempt 2; cancel | `consumed` (from attempt 1 `started_at`), never released | chain |
| A1-R13 | Attempt 1 dispatch lost (never started); retry queued; cancel | Settled with no started attempt → `released` | chain |
| A1-R14 | Requester authorization revoked before scheduler retry after lost reply | Trusted lookup by target finds the job; cleanup; no second job | chain races |
| A1-R15a | Post-hold/pre-commit seam, cancel first: cancel publication commits after `start_attempt` read its eligibility decision but before the start transaction acquires the coordinator | Hold sees the moved epoch → re-decide → denied; job cancelled by BE2-01; no `started_at`; settled, `released`. (Within the post-hold window itself a cancel cannot commit — R15b — so "cancel first" always lands here.) | chain races |
| A1-R15b | Post-hold/pre-commit seam, start first: a hook after the successful hold inside the start transaction requests cancellation (same thread), or another thread requests it and blocks | Cancellation deferred/blocked until the start commits; job RUNNING with `started_at`; then request `cancelled`; `consumed`; no handoff; recorded order "start committed first" | chain races |
| A1-R16 | Exception paths: injected foundation commit failure (`fail_next_commit`) with a deferred cancel pending; exception inside an assistance publication | Foundation publishes nothing; deferred cancel then commits on its own; a failed assistance publication leaves both request state and epoch unchanged; coordinator free afterwards (no deadlock) | races |
| A1-C01 | Contract round trips, extra fields refused, device view minimal | Pass | contract |
| A1-C02 | Command examples still satisfy DATA-21 `ShapeSpec` 0.1-candidate | Pass, ShapeSpec unchanged | contract |
| A1-C03 | Fixture app CMD-32/33 status codes/envelopes; live app has no route | Pass | contract/api |

## 12. Batches, files and checks

| Batch | Scope | Proposed files (new unless noted) |
|---|---|---|
| A1.1 | Domain: states/settlement, semantic identity/digest, budget ledger rules, cache key | `domain/assistance.py`; `backend/tests/unit/test_assistance_domain.py` |
| A1.2 | Contracts | `contracts/schemas/assistance_requests.py`; `backend/tests/contract/test_assistance_request_contracts.py` |
| A1.3 | Ports + service (submit, scheduler, cancel, owner notice, completion/handoff, settlement, pin, projections) | `application/ports/assistance.py`; `application/services/assistance.py`; `backend/tests/unit/test_assistance_service.py` |
| A1.4 | Fakes and adapters (`AssistanceCommitCoordinator`, `CoordinatedAiJobRepository`, `AssistanceEligibility`, `AssistanceJobReader`, job port, analysis outcome port with injected Teacher reader, pin port), harness, races, chain | `infrastructure/assistance/{__init__,fakes,harness,adapters}.py`; `backend/tests/unit/test_assistance_races.py`; `backend/tests/unit/test_assistance_chain.py` |
| A1.5 | Fixture HTTP, handoff examples, evidence | `interfaces/http/routers/assistance_requests.py`; `interfaces/http/assistance_requests_fixture_app.py`; `backend/tests/contract/test_assistance_requests_api.py`; `features/FEAT-049-.../fixtures/h_ai_review/*.json`; evidence notes |

No existing source file is modified in A1 except, if unavoidable, `__init__` exports; any other
edit to BE2-01/BE2-02 code is a scope change requiring an amendment. Checks per batch: the new
tests; then before review: `ruff` and strict `mypy` on touched paths; regression
`test_ai_job_*.py`, `test_vision_analysis_*.py`, `test_vision_context_*.py`,
`tests/contract/test_ai_job_*.py`, `test_analysis_*`, `test_h_ai_review_handoff_examples.py`,
`test_vision_context_contracts.py`; `tools/validate_harness.py`,
`validate_repository_security.py`, `validate_architecture.py`, `validate_skeleton.py`,
`git diff --check`. Pillow-dependent skips stay NOT_RUN with reason. No new conformance framework.

## 13. Owner decisions needed (recommendation first)

| ID | Recommended | Trade-off / alternative |
|---|---|---|
| D1 | Approve A1 only as §1–§12, on this stacked branch, parking BE2-02 and keeping BE2-01 WAITING_STUDIO | Waiting for dev integration delays BE2-03 with no dependency benefit; stacked PR ordering must be managed |
| D2 | `request_revision` bumps only on invalidating transitions (cancel, stale); job link/completion use an internal record version | Bump on every change would break C1 lineage of in-flight valid jobs; this makes ETag coarser. It is the lineage/If-Match revision only, not a representation cache validator; A1 adds no conditional GET/If-None-Match |
| D3 | CMD-33 literal: Child device may cancel an individual request whose target is its current bound participant (incl. Teacher-initiated); never group/others; Teacher any in scope | Stricter "own child-initiated only" protects Teacher intent but narrows the source |
| D4 | Group: one ineligible member refuses the whole request, member-agnostic code | Excluding members silently changes audience; partial audience needs a Teacher-chosen subset contract later |
| D5 | Contributor for Teacher requests = current bound-turn participant (must be in audience), else personal-canvas owner, else refuse `TURN_CLOSED` | Keeps the accepted `AnalysisScope` invariant; Teacher group help on a turnless canvas is blocked until a turn exists |
| D6 | Budget unit = scheduled provider stage; monotonic held→consumed on any started attempt; released only after settlement proves no start; unknown evidence keeps the hold; FIXTURE_ONLY numbers | Per-attempt charging is closer to cost but breaks "duplicate retry adds no semantic cost"; conservative hold can strand units until cleanup settles |
| D7 | Cache = analysis reuse only, same session + exact semantic identity/digest, supported current-read gate; no proposal cache | Lower hit rate; broader reuse risks cross-audience/consent leakage |
| D8 | Sketch stage intent-only fake (`SIMULATED_NO_PRODUCER`); no sketch job/DATA-23 in A1 | A fake sketch job type would look like generation progress without a producer |
| D9 | Do not map DATA-21 reason/level to C2-local request enums in A1; C2 typed mode keeps fixture request facts | Full typed-context chain stays fixture-joined at that seam; a mapping needs the level taxonomy decision |
| D10 | Define consumer `AssistancePolicyPort`/snapshot here as a proposal to the BE2-14 owner, FIXTURE_ONLY adapter; runtime waits for BE2-14 concurrence | Waiting for BE2-14 first would block A1; the shape may need a version bump after BE2-14 review |
| D11 | Linearize at the BE2-03 handoff commit: cancel/stale before it wins with no handoff; after it the request is terminal `analysis_ready` and CMD-33 returns `INVALID_STATE`; downstream withdrawal belongs to BE2-04/05 | Alternative: a cancellable post-handoff stage with a versioned `AssistanceHandoffWithdrawnV1` event and bounded consumer obligations — more Teacher control, but adds a contract with no A1 consumer |

Routine choices (TC-01…TC-10) are recorded in DECISIONS and follow existing conventions.

## 14. Exclusions and later runtime

Not in A1 and not closed by an A1 PASS: SQL tables/migrations, durable receipts and
transactional outbox, real concurrency/locking, indexed job lookup by target; Redis/RQ
scheduling, priority/overload queue (FR054/UC-032); real BE1 adapters (identity, turn/grant,
roster, region, checkpoint/render/admission, consent/age/context revision) and real per-request
OwnerFence composition; deployed API/router/auth; adopted policy values/limits/kill switch
(BE2-14) and Teacher budget override; provider/model, real Vision quality, real Sketch
generation (BE2-04), moderation/review (BE2-05), Child response (BE2-06); CMD-59 read model;
P1 UI; P4 integration INTG-05. BE2-01, BE2-02 and BE2-03 remain NOT_DONE after A1; no
prerequisite is marked DONE.

## 15. Evidence plan

Publishable: `evidence/notes/A1_IMPLEMENTATION_EVIDENCE_<date>.md` (case → test mapping, actual
commands/results, NOT_RUN reasons), `evidence/metrics/A1_CHECKS_<date>.json`, H-AI-REVIEW /
H-OPERATIONS example fixtures. Raw logs/scratch/prompts: `evidence/local/` (ignored).

## 16. Finding map (revisions 2 and 3)

| Finding | Plan text | Cases |
|---|---|---|
| A1-PR01 (P1) late create escapes cancel/budget | §6 settlement axis; §8.2 retained identity, request-aware fenced eligibility, scheduler outcome table, trusted lookup/settlement; §9.1 no release without settlement | R09, R10, R11, R14, P05 |
| A1-PR02 (P2) dedup omits resolved pin | §8.3 digest + semantic identity incl. input_hash/audience/purpose/policy/digest, canonical rules, excluded operation ids, fact-change supersession | N23, N24, N25, P04 |
| A1-PR03 (P2) retry refunds spent stage | §9.1 monotonic ledger, attempt-history evidence, unknown → hold, release only after settlement | R06, R12, R13, P05 |
| A1-PR04 (P2) terminal vs cancel-wins | §6, §8.4 linearization at handoff commit, observation-accepted vs handoff-committed rows; D11 | R03a, R03b, N14 |
| A1-PR05 (P2) wrong queue boundary | §8.2 lost reply/crash boundary vs broker-down boundary; broker injected only in `_publish` path | R08a, R08b |
| Clarification: cache replay wording | §9.2 supported current-read gate; `record_observation` never called; original provenance | P08, N17 |
| Clarification: CMD-33 idempotency | §5, §8.1 scope/fingerprint/missing key/replay/mismatch/revoked disclosure | N14, N16, N20, N21, N22 |
| A1-PR01-F1 (P2, rev2 re-review) epoch-only hold leaves a post-hold/pre-commit gap | Rev3 §8.2 shared `AssistanceCommitCoordinator` + `CoordinatedAiJobRepository` decorator spanning each foundation write transaction through commit and assistance state+epoch publication; decision-read/epoch snapshot; lock ordering; same-thread deferral; exception handling; §8.5 and §11 boundary rule for tests | R15a, R15b, R16 (R09, R10, R06 kept) |
| Rev2 re-review notes | Rev3 §8.4 injected scoped Teacher reader, independent device disclosure; §9.1 consumed stays consumed; §13 D2 lineage revision ≠ cache validator | P07, P08, R12 |

Implementation is blocked until `approvals/TASK_APPROVAL.md` says `APPROVED` for this revision.
