# BE2-01 Phase B — durable AI job foundation (plan)

- Plan revision: 3 (supersedes revision 2; archives byte-identical: rev 1
  `evidence/notes/PHASE_B_PLAN_REV1_ARCHIVE_20261014.md` sha256 `cdbb2be6…ffb7ec0`, rev 2
  `evidence/notes/PHASE_B_PLAN_REV2_ARCHIVE_20261015.md` sha256 `6bdf86d0…00869f1`)
- Status: PLANNED
- Approval status: AWAITING_APPROVAL (no approval exists; Phase A approval does not cover Phase B)
- Implementation status: NOT_STARTED
- Date: 2026-10-15, Asia/Saigon. Author: Claude (executor), docs only — no code, install,
  DB/broker start, cloud run or source upload.
- Owner: P3 / BE2. Branch `feature/be2-01-ai-job-foundation`, worktree `.worktrees/be2-01-ai-job-foundation`.
- Companions (revision 3): `PHASE_B_ADR_PROPOSAL.md` (PROPOSED), `PHASE_B_PORT_REVIEW.md` (PENDING).
- Revision 2 addresses `evidence/notes/PHASE_B_PLAN_CODEX_REVIEW_20261014.md` PB-R01–PB-R06
  (mapping: `evidence/notes/PHASE_B_PLAN_REVISION_EVIDENCE.md`). Changed sections carry “(rev2 PB-Rxx)”.
- Revision 3 adds only PB-C01/PB-C02 from `evidence/notes/PHASE_B_REV2_CLOSURE_REVIEW_20261015.md`
  (PB-R01–R06 CLOSED_ORIGINAL_PLAN_CASE there); mapping `evidence/notes/PHASE_B_PLAN_REV3_EVIDENCE.md`.
  Changed text carries “(rev3 PB-Cxx)”.
- Roadmap slot: Q01 — PLAN_PREPARATION only. ACTIVE slot stays Q00.

## 1. Problem and result

Phase A proved job/attempt/receipt/cancel/completion semantics with in-memory fakes only
(`PHASE_A_Q00_FINAL_CODE_REVIEW_20261014.md`: PASS at fake/contract scope). Nothing survives a
restart; CAS is a Python lock; the outbox is a dict; there is no broker. SRS B22.3, B19.11, DATA-25
and the BE2-01 card require the durable chặng: restart after commit keeps job/attempt/receipt,
outbox dispatch retry creates no new semantic attempt, CAS blocks concurrent completion.

Result: AI-owned durable repository/unit-of-work, migrations, transactional outbox, queue
dispatcher with SQL reconciliation, attempt-bound worker capability, owner-decision fencing at
every acceptance point, durable incident audit, and real-adapter fault evidence — reusing the
reviewed Phase A semantics except for the deltas in §5. Phase B does **not** deliver live routing,
provider inference, real copy deletion or BE1 tables/implementation.

## 2. Preconditions before any Phase B code (gates)

| # | Gate | Current state |
|---|---|---|
| G1 | Phase A checkpoint disposition (task owner), production adoption explicitly deferred or decided | PENDING (`PHASE_A_ACCEPTANCE_GATE_RECORD.md`) |
| G2 | This plan independently re-reviewed (rev 3), then explicit approval naming `plan/PHASE_B_PLAN.md` revision 3 in a separate record | rev 1 NEEDS_REVISION; rev 2 PB-R01–R06 closed, PB-C01/C02 open; rev 3 pending focused review |
| G3 | ADR D1–D7 in `PHASE_B_ADR_PROPOSAL.md` adopted | PROPOSED |
| G4 | P2/P4 answers in `PHASE_B_PORT_REVIEW.md`, **including the owner-fence protocol (Q8) adoption** | PENDING |
| G5 | Authorised synthetic-only Linux environment with PostgreSQL 17 + Redis (separate Sketch2Life env, never Wan2.2); dependency inventory recorded before tests | NOT_STARTED |

B1 closes G3/G4; B2–B6 code starts only after G1–G5. If P2 rejects the preferred fence (Q8), the
plan must be amended (fallback in §5.1) and re-reviewed before approval.

## 3. Allowed changes and exclusions

Allowed (after approval): AI-owned infrastructure modules, migrations, worker/dispatcher/reconciler
entry modules for tests, integration tests, a durable conformance runner, the port/service/fake
deltas in §5 — including the pure domain transition `record_dispatch_loss` in
`domain/ai_jobs/model.py` (rev3 PB-C01), the transient dispatch envelope/issuer and
`QuarantineIntent` port changes (rev3 PB-C02), the matching Phase A fake/harness/test updates and
regeneration of the error-catalogue fixture for the new `DISPATCH_LOST` code — a **test-only**
owner-fence fixture schema implementing the assumed P2 contract, FEAT-044 records/evidence.

Excluded: Phase A behaviour changes beyond §5; BE1 tables/repositories/fence implementation
(owned by P2 — BE2 only consumes the port); mounting CMD-44 in the live app or registry adoption
(P4/INTG-02); provider/model adapters and real inference (BE2-04/08); durable
ProviderCopyLifecycle (BE2-14 — fake stays); production numeric policy; dependency installs on
Windows; cloud resources/deployment; a general scheduler/pagination engine; a second queue
adapter; commit/push unless separately requested; other BE2 cards.

## 4. File map (proposed outputs)

| Path | Batch | Content |
|---|---|---|
| `backend/src/sketch2life/infrastructure/ai_jobs/sql/tables.py` | B2 | SQLAlchemy Core metadata, PostgreSQL schema `ai_jobs` (§6) |
| `backend/migrations/` (+ `alembic.ini`, branch label `ai_jobs`) | B2 | Alembic env + first AI revision (layout per D2/Q7) |
| `backend/src/sketch2life/infrastructure/ai_jobs/sql/repository.py` | B3 | `SqlAiJobRepository`/unit of work; plain INSERT + typed unique-violation handling (§7.2) |
| `backend/src/sketch2life/infrastructure/ai_jobs/sql/owner_fence_fixture.py` + test migration | B3 | **Test-only** implementation of the assumed `OwnerFencePort` contract (schema `owner_fence_fixture`), labelled ASSUMED_CONTRACT; never wired in production |
| `backend/src/sketch2life/infrastructure/ai_jobs/outbox_dispatcher.py` | B4 | Lease/generation-fenced claim → eligibility recheck → mint capability → enqueue → fenced mark |
| `backend/src/sketch2life/infrastructure/ai_jobs/rq_queue.py` | B4 | `DispatchQueuePort` RQ adapter (D3 preferred), RQ retries disabled (`retries_left=0`) |
| `backend/src/sketch2life/infrastructure/ai_jobs/reconciler.py` | B4/B5 | SQL sweeps: queued-dispatched-not-started (same attempt republish), overdue running, due retries |
| `backend/src/sketch2life/infrastructure/ai_jobs/worker_capability.py` | B5 | HMAC issuer/verifier returning typed `VerifiedCapability` (D6) |
| `backend/src/sketch2life/infrastructure/ai_jobs/worker.py` | B5 | Worker loop: receive → start → (fake) provider → completion |
| `backend/src/sketch2life/domain/ai_jobs/model.py` | B4 | Δ13 only: pure `record_dispatch_loss` transition (rev3 PB-C01) |
| `backend/src/sketch2life/application/ports/ai_jobs.py`, `application/services/ai_jobs.py`, `infrastructure/ai_jobs/fakes.py`, `infrastructure/ai_jobs/harness.py` | B3–B5 | Exactly the deltas in §5 (incl. Δ13–Δ15) |
| `backend/tests/unit/test_ai_job_lifecycle.py`, `test_ai_job_application.py`, `test_ai_job_review_regressions.py`, `test_ai_job_q00_followups.py`, `backend/tests/contract/test_ai_job_contracts.py`, `test_ai_job_polling.py`; `features/FEAT-044-be2-ai-job-foundation/src/*.py`; `fixtures/error_catalogue.json` + `MANIFEST.json` | B4–B5 | Signature/call-site updates for Δ13–Δ15 and new unit cases; fixture regenerated for `DISPATCH_LOST`; Phase A semantics otherwise unchanged |
| `backend/tests/integration/ai_jobs/test_sql_repository.py`, `test_migrations.py`, `test_create_races.py`, `test_owner_fence.py`, `test_outbox_dispatch.py`, `test_dispatch_recovery.py`, `test_capability.py`, `test_restart_recovery.py`, `test_completion_recovery.py`, `test_audit_durability.py`, `test_notice_coverage.py` | B2–B5 | Markers `requires_postgres` / `requires_redis`; skip ⇒ NOT_RUN, never PASS |
| `features/FEAT-044-be2-ai-job-foundation/src/run_durable_conformance.py` | B6 | Phase A scenarios on the SQL adapter + crash-point matrix |
| `features/FEAT-044-be2-ai-job-foundation/evidence/…` | B1–B6 | Diagrams, migration matrix, receipts, fault traces, handoff |

## 5. Port / service / fake deltas (complete list; rev2)

### 5.1 Owner-decision fence (rev2 PB-R01)

Job CAS protects only AI rows. Acceptance must be linearised with the owner's decision state.

**Preferred protocol (requires P2 adoption, Q8):** shared PostgreSQL (D1), P2 owns a fence table
and a fence-read function in its own schema; BE2 never writes it.

1. Every owner decision BE2 relies on carries a fence `OwnerFence(fence_scope, epoch)`:
   eligibility (consent/purpose/session/recall/source-expiry/kill-switch/context revision),
   authorization grant, and artifact state (lineage/quarantine version).
2. P2 bumps `epoch` with `SELECT … FOR UPDATE` on its fence row in the **same transaction** that
   changes the decision, and writes the corresponding cancellation notice to its outbox there.
3. BE2's write transaction calls `OwnerFencePort.hold(fences)` on the **same connection**; the P2
   implementation reads the fence rows `FOR SHARE` and returns current epochs. If any epoch ≠
   the decision's epoch → the write is not applied; BE2 rolls back, re-decides once with a fresh
   decision, else returns a typed `STALE_CONTEXT`/eligibility outcome.
4. **Linearization point:** commit order on the owner fence row. An owner change committed first
   makes the BE2 hold fail; a BE2 acceptance committed first is historically valid and the later
   owner change is handled by its notice (terminal results stay terminal, exposure is blocked by
   the current-authority read check).
5. Reads/cache (CMD-44) keep the Phase A live current-authority check before ETag/304; no fence
   hold needed because nothing is written.

Fenced acceptance points: create (authorization + eligibility), start, retry requeue, dispatch
(eligibility recheck), completion acceptance (eligibility + artifact fences of admitted outputs),
Teacher cancel (authorization).

**Fallback if P2 rejects a shared-transaction fence:** decisions still carry epochs that BE2
records with each acceptance; acceptance can then commit concurrently with an owner change and
is never exposed (read-time check) but is not prevented. This weaker guarantee requires amending
B-09 and re-review before approval. Not the preferred plan.

**Proof split:** component proof uses the test-only fixture implementing the assumed contract
(`ASSUMED_CONTRACT` label on every receipt); actual owner integration evidence is a P2/P4 gate,
not claimed by Phase B.

### 5.2 Delta table

| # | Change | Reason (finding) | Test |
|---|---|---|---|
| Δ1 | `EligibilityDecision`, `AuthorizationDecision` gain `fence: OwnerFence`; `ArtifactDescriptor` gains `fence` (artifact state version) | PB-R01 | `test_owner_fence.py` |
| Δ2 | New `OwnerFencePort.hold(fences) -> FenceResult(current: bool, stale: tuple[OwnerFence, ...])`, bound to the unit of work's connection (`AiJobUnitOfWork.hold_owner_fences`) ; fake: in-memory epochs that tests can bump between precheck and write | PB-R01 | barrier tests B-09a–c |
| Δ3 | Service: owner decisions obtained before the write transaction, then `hold_owner_fences` inside it before any mutation; stale ⇒ rollback, one re-decision, else typed outcome. Removes rev1's “CAS re-decides” claim | PB-R01 | B-09a–d |
| Δ4 | `SemanticRequestKey` canonicalisation: `semantic_key_sha256` = sha256 of canonical JSON (NFC strings, explicit `null` for missing `session_id`, `subject_refs` sorted, duplicates kept as Phase A) — single PK column | PB-R02 | B-03d/e, B-07 |
| Δ5 | `put_*` UoW methods raise typed `UniqueConflict(kind)` instead of silently ignoring; create runs as one candidate transaction (job, attempt, semantic, command receipt, outbox, audit intent); any `UniqueConflict` ⇒ full rollback, then a fresh transaction re-reads the winner (≤ 2 bounded rounds) | PB-R02 | B-03a–f, B-08 |
| Δ6 | Outbox rows: `kind` ∈ {`dispatch`,`audit`,`quarantine`}, `event_id`, `lease_owner`, `lease_generation`, `lease_until`; `claim_outbox(owner, now, lease, limit)` increments generation; `mark_dispatched`/`release` require matching (`owner`,`generation`) and are no-ops otherwise | PB-R03, PB-R05 | B-04c, B-06b |
| Δ7 | Attempt fields `dispatched_at`, `dispatch_count`; reconciler query `queued_dispatched_not_started(now, start_timeout, limit)` republishes the **same attempt** (new outbox row, same `attempt_id`) up to `DISPATCH_MAX` (named PROPOSED); exceeded ⇒ Δ13 `record_dispatch_loss` (rev3 PB-C01) → existing backoff / normal policy retry (only path that increments `attempt_number`); republish before the bound never creates an attempt | PB-R03, PB-C01 | B-04a/b, B-06a |
| Δ8 | `WorkerCapabilityVerifier.verify(token) -> VerifiedCapability \| None` (`job_id`, `attempt_id`, `issued_at`, `expires_at`, `key_id`); `_require_worker(token, job_id, attempt_id)` at `start_attempt`, `report_progress`, `accept_completion` (uses `claim.attempt_id`) compares both ids; fake issuer/verifier updated. Carrier: Δ14 | PB-R04 | B-05e, B-10c |
| Δ9 | `AuditEvent` gains deterministic `event_id` (sha256 of type, job, attempt, fingerprint/notice, reason). **Authoritative settlement** (rev3 wording) = every committed job-changing completion — accepted, stale, rejected/unsafe/malformed, eligibility-cancel — writes mutation + completion receipt + audit intent + quarantine intent (Δ15) in one transaction. **Non-authoritative rejection/conflict** (guard verdicts that leave the job unchanged, `MALFORMED_CLAIM`, `COMPLETION_CONFLICT`) commits an **audit-only incident transaction** (plus quarantine intent only for committed-final verdicts) before returning; audit-only commit failure ⇒ `503 DEPENDENCY_UNAVAILABLE` (retryable) instead of the 409/receipt | PB-R05 | B-06c/d, B-08b |
| Δ10 | Notices: `apply_cancellation_notice` keeps the Phase A all-match semantics in **one transaction**: `jobs_for_notice(notice)` (no limit, `FOR UPDATE`) cancels every match, then records the notice `COMPLETE`. Guard `NOTICE_ATOMIC_MAX` (named PROPOSED): above it, fail typed without marking — no partial completion, no pagination engine | PB-R06 | B-09e–g |
| Δ11 | Sweeps use targeted, paged queries `due_retries`, `overdue_running`, `queued_dispatched_not_started` (safe to page: they repeat until empty and carry no seen-marker) | rev1 + PB-R03 | parity tests |
| Δ12 | `InMemoryAiJobStore` / fakes implement Δ1–Δ11 and Δ13–Δ15 so Phase A runner/tests stay valid | all | Phase A suites + runner unchanged results |
| Δ13 | **Domain (rev3 PB-C01):** pure `record_dispatch_loss(job, attempt_id, *, public_message, now) -> AiJob`. Guards: state `queued`, attempt is active, `attempt.started_at is None`; otherwise `InvalidJobTransition`. Effects: attempt `finished_at=now`, `outcome="dispatch_lost"`, `started_at` stays `None`, pinned request/provenance unchanged, history event `dispatch_lost`, `job_revision+1`; code fixed to `DISPATCH_LOST` (no caller-supplied code). Retry budget left (`attempts_remaining(n) > 0`) ⇒ `failed_retryable`, `failure(DISPATCH_LOST, retryable=True, attempts_remaining)`, `retry_not_before = now + backoff_after(n)`; none left ⇒ `failed_exhausted`, `failure(…, retryable=False, 0)`, `completed_at=now`, no schedule. `record_failure` stays RUNNING-only (no generic queued provider failure). Service: reconciler use case re-reads in its transaction and applies Δ13 only if the job is still `queued` with the same active, unstarted attempt and the expected `job_revision`; otherwise no-op (start won or job settled). New public message `DISPATCH_LOST` in the catalogue | PB-C01 | B-04b(i–v) |
| Δ14 | **Queue carrier (rev3 PB-C02):** new transient `WorkerDispatchEnvelope(message: DispatchMessage, capability: str)` (frozen; never persisted); `DispatchQueuePort.enqueue(envelope: WorkerDispatchEnvelope) -> None` (replaces `enqueue(message)`); new P3 port `WorkerCapabilityIssuer.issue(job_id, attempt_id, now) -> str`, called by the dispatcher/reconciler immediately before enqueue (outside the SQL write); `AiJobDependencies` gains `capability_issuer`. RQ adapter passes the envelope as job args with `description=message_id`, `result_ttl=0`, short `failure_ttl`, and no argument logging; worker receives the envelope and uses `envelope.capability` for start/progress/completion. `DispatchMessage`, outbox payloads, receipts, audit and logs stay token-free. Fakes: `FakeQueue.enqueue/receive` carry envelopes; `FakeWorkerCapability` implements issuer + verifier; `FakeWorker` stops minting its own token | PB-C02 | B-05e, B-10c |
| Δ15 | **Quarantine carrier (rev3 PB-C02):** new `QuarantineIntent(event_id, organization_id, job_id, attempt_id, artifact_refs, reason_code)`; `ArtifactPort.quarantine(intent: QuarantineIntent) -> None` (replaces `quarantine(refs, reason)`), idempotent by `event_id` at the sink. `event_id` = deterministic sha256(`quarantine`, job, attempt, sorted refs, reason, claim fingerprint/verdict) computed once when the intent is written; the outbox stores it and every redelivery sends that exact value. Intents are built only from `_owned_refs` (org + job/attempt lineage) and only inside the committing transaction, so rolled-back/loser work produces none. Fake: `FakeArtifacts.quarantine(intent)` keeps the `quarantined` ref→reason map plus applied `event_id`s and treats a repeated `event_id` as a no-op | PB-C02 | B-06c/d |

No other domain/contract change beyond Δ1–Δ15 (Δ13 is the only domain change; `DISPATCH_LOST`
is the only new public failure code). Discoveries during B3–B5 become a plan change for review.

## 6. Durable data model (proposed; D1/D2)

Schema `ai_jobs` (AI-owned; no FK into BE1; owner refs opaque):

| Table | Key / constraints | Notes |
|---|---|---|
| `job` | PK `job_id`; `job_revision` CAS; check state ∈ DATA-25 | scope, pinned request ref, progress/failure JSONB, policy snapshot id, `accepted_fences` JSONB (epochs held at last acceptance), timestamptz |
| `attempt` | PK `attempt_id`; UNIQUE (`job_id`,`attempt_number`) | pinned request, `dispatched_at`, `dispatch_count`, started/finished/outcome |
| `command_receipt` | PK (`organization_id`,`principal_id`,`contract_name`,`target_id`,`idempotency_key`) — all NOT NULL | fingerprint, job_id, outcome, revision; retention named PROPOSED IDEMPOTENCY_TTL |
| `semantic_request` | PK `semantic_key_sha256` (rev2 PB-R02); raw key columns kept for audit | `session_id` nullable but not part of a NULL-sensitive unique index |
| `completion_receipt` | PK (`job_id`,`attempt_id`) | authoritative only |
| `cancellation_notice` | PK `notice_id`; `status` ∈ {`COMPLETE`} written only after all matches cancelled | applied count |
| `outbox` | PK `message_id`; UNIQUE `event_id` where kind ≠ dispatch; index (pending, `available_at`) | kind, payload JSONB (no secrets/tokens/child data), lease owner/generation/until, publish attempts, last error code |

## 7. Batches (no code until gates)

| Batch | Scope | Exit / evidence |
|---|---|---|
| **B1** | Close D1–D7, Q1–Q8; sequence diagrams for create, dispatch/receive/start, completion, retry, cancel, notice, incident audit; crash-window table (§7.1) | ADR + port answers recorded; diagrams in evidence. No code |
| **B2** | `tables.py` + Alembic revision for §6; fresh / existing / rerun; downgrade only on disposable DB | Migration matrix; constraint introspection (incl. semantic PK); B-01 |
| **B3** | SQL repository/UoW (Δ4, Δ5), owner-fence hold (Δ1–Δ3) with test-only fixture | B-03, B-07, B-08, B-09a–d on PostgreSQL |
| **B4** | Fenced outbox dispatcher (Δ6), RQ adapter with envelope (Δ14), reconciler (Δ7, Δ11) incl. domain dispatch-loss (Δ13), side-effect outbox kinds | B-02, B-04, B-06a/b |
| **B5** | Capability issue/verify (Δ8, Δ14), worker loop, completion recovery, durable incident audit (Δ9), quarantine intents (Δ15), atomic notices (Δ10) | B-05, B-06c/d, B-09e–g, B-10c |
| **B6** | Conformance runner, crash-point matrix, Phase A regression on SQL adapter, handoff | B-10, B-11, B-12 |

### 7.1 Receive/start/ack boundaries and crash windows (rev2 PB-R03; no exactly-once claim)

Boundaries: **publish** = RQ enqueue succeeded and outbox row marked by the current lease holder;
**durable start** = `start_attempt` commit (`attempt.started_at`); **broker ack** = RQ job finish,
never treated as an application acknowledgement; **completion** = authoritative completion
commit. RQ transport retries are disabled; redelivery is owned by the SQL reconciler.

| Window | Recovery |
|---|---|
| Crash before create commit | Nothing durable; caller retries same key |
| Commit done, before publish | Outbox pending → dispatcher publishes after restart |
| Enqueued, crash before fenced mark | Lease expires → new holder (generation+1) republishes same message/attempt; old holder's late mark/release is a no-op; worker dedups by attempt (`DUPLICATE_DELIVERY`/`ATTEMPT_NOT_ACTIVE`) |
| Broker down | Enqueue fails → row stays pending, job `queued` |
| Worker received, died before durable start commit | Job `queued`, attempt `dispatched_at` set, `started_at` null → after `DISPATCH_START_TIMEOUT` (named PROPOSED) reconciler republishes the **same attempt** with a fresh capability (≤ `DISPATCH_MAX`); then Δ13 `record_dispatch_loss` (CAS vs `start_attempt`: one winner) → backoff → policy retry, or `failed_exhausted` if no budget |
| Started, died before provider result | Overdue-running sweep → `failed_retryable PROVIDER_TIMEOUT` → policy retry (new attempt) |
| Provider returned, died before completion commit | **No same-claim recovery** (claim is not durably stored). Attempt times out → policy retry; the old attempt keeps its provenance; any uploaded output of the old attempt is orphaned and, if later claimed, gets `ATTEMPT_SUPERSEDED` (owned output quarantined). Provider may have executed twice; no fingerprint is invented |
| Completion committed, crash before audit/quarantine delivery | Intents in outbox → delivered after restart, dedup by `event_id` |
| Quarantine effect applied by the sink, crash before outbox delivery is marked (rev3 PB-C02) | Redelivery sends the **same stored `event_id`** → sink no-op; artifact state unchanged |
| Rejection/conflict, crash before incident commit | No response was returned; worker retry recomputes the same `event_id` → incident committed once |

### 7.2 Create race rule (rev2 PB-R02)

Candidate transaction inserts with plain `INSERT` (no `ON CONFLICT DO NOTHING`). PostgreSQL blocks
the second inserter until the first commits/aborts, then raises a unique violation. Loser: roll
back the **whole** candidate transaction (job, attempt, semantic row, receipt, outbox, audit
intent — nothing survives), then open a fresh READ COMMITTED transaction that sees the committed
winner: same command key ⇒ replay or `IDEMPOTENCY_PAYLOAD_MISMATCH`; same semantic key ⇒ insert
only the caller's own command receipt pointing at the winner job (again rollback-on-conflict);
at most two rounds, then typed `409 IDEMPOTENCY_CONFLICT` (retryable).

## 8. Acceptance (to verify; nothing claimed PASS)

| ID | Acceptance (subcases) | Source | Planned check / environment |
|---|---|---|---|
| B-01 | Restart after commit keeps job/request/attempt revisions, receipts/fingerprints, outbox | B22.3; P-NFR-04; FIX-NFR-03 | `test_restart_recovery.py` kill-after-commit, checksum rows · PostgreSQL |
| B-02 | Broker down loses nothing; replay creates no semantic attempt | B22.3 | `test_outbox_dispatch.py`, Redis stopped/restarted |
| B-03 | (a) two processes same key+payload → one job, both get replay; (b) different keys same semantic → one job, one attempt, one dispatch, one semantic row, per-key receipts; (c) same key different payload → mismatch; (d) `session_id` null vs populated distinct, null+null deduped; (e) permuted subject order deduped; (f) restart between rounds; no orphan job/attempt/outbox/audit rows | B22.1; B19.11; PB-R02 | `test_create_races.py` (barriers, 2 processes) |
| B-04 | (a) worker killed after receive before start commit → reconciler republishes, completes with the **same** `attempt_id`; (b) `DISPATCH_MAX` exceeded (rev3 PB-C01): (i) queued attempt with retry budget → `failed_retryable` `DISPATCH_LOST` with `retry_not_before` from existing backoff; (ii) final attempt → `failed_exhausted`, no schedule, never reopened; (iii) `started_at` stays null, no provider-start/progress event invented, pinned request/provenance kept; (iv) reconciler vs `start_attempt` CAS race: exactly one winner, reconciler never overwrites a committed running/completed job; (v) republish before the bound keeps the same `attempt_id` (no new attempt); plus pure domain unit cases incl. `record_failure` still rejecting `queued`; (c) stale lease holder mark/release after takeover is a no-op; same-attempt redelivery dedup | DATA-25; B22.3; PB-R03; PB-C01 | `test_dispatch_recovery.py` (process kill, lease expiry) |
| B-05 | One authoritative completion under concurrency; identical replay same receipt; conflicting never overwrites; (e) token for attempt A cannot start/progress/complete B; wrong job/tampered/expired denied; the token reaches the worker only through the broker envelope (rev3 PB-C02) and is absent from SQL outbox rows, receipts, audit intents and captured dispatcher/RQ/worker logs | B22.3; PB-R04; PB-C02 | `test_completion_recovery.py`, `test_capability.py` |
| B-06 | Crash matrix §7.1: (a) enqueue/mark and receive/start windows; (b) provider/completion window bounded as stated; (c) committed incident audit survives restart, redelivery dedups by `event_id`; crash after the quarantine effect but before delivery mark → redelivery with the same stored `event_id` is a sink no-op (rev3 PB-C02); (d) no quarantine delivery from loser/rolled-back work; intents contain only owned-lineage refs | B22.3; MP-04; PB-R03/R05; PB-C02 | Fault-injection hooks per boundary |
| B-07 | Semantic scope isolation durable (target/purpose/session/subjects) | Phase A R02 | Semantic PK tests |
| B-08 | (a) rollback leaves nothing partial; (b) storage failure at each commit boundary: no accepted success without durable audit intent; audit-only failure ⇒ 503, not 409 | B22.1; FIX-NFR-03; PB-R05 | Injected DB errors |
| B-09 | (a) consent/context changed between precheck and write with notice withheld and `job_revision` unchanged → stale decision does not authorise start/completion; (b) same for artifact quarantine/version; (c) same for authorization on create/cancel; (d) read/cache still current-authority checked, historical accepted receipts unchanged; (e) notice with > `NOTICE_ATOMIC_MAX`/2 matches (multi-“page” volume) cancels all atomically; (f) duplicate notice no-op; (g) crash mid-notice → rollback → redelivery cancels all, nothing reopened; concurrent create after owner bump fails fence | B19.11; B22.3; PB-R01/R06 | `test_owner_fence.py` (ASSUMED_CONTRACT fixture), `test_notice_coverage.py` |
| B-10 | Durable outbox/receipt/CAS/rollback and (c) capability on the real adapter (envelope via real Redis/RQ, token-free SQL/logs), not fakes | BE2-01 card; PB-C02 | Conformance runner on SQL adapter |
| B-11 | Migration/conformance report; Phase A suites still pass on fakes; Linux/LightningAI-only checks labelled | PLAN.md §6; tracker | Migration matrix + Phase A suites + runner |
| B-12 | Not proven here: live router/namespace, provider inference, actual copy deletion, production policy, deployment, **real owner fence integration** | ADR-0015; roadmap; PB-R01 | Handoff with owners (P2, P4 INTG-02, BE2-04/08/14) |

## 9. Verification and evidence

Planned commands (not run): Alembic upgrade/downgrade on a disposable database; `python -m pytest
backend/tests/integration/ai_jobs -m "requires_postgres or requires_redis"`; process-kill fault
harness; Phase A suites + runner; ruff/mypy; repository validators; `git diff --check`. Missing
services ⇒ explicit skip reason ⇒ NOT_RUN / REQUIRES_LIGHTNINGAI_TEST. Receipts list interpreter,
PostgreSQL/Redis/RQ versions, synthetic data only, redacted logs, ASSUMED_CONTRACT label for
owner-fence component tests.

## 10. Sample approval text (NOT an approval)

```text
Tôi duyệt BE2-01 Phase B theo features/FEAT-044-be2-ai-job-foundation/plan/PHASE_B_PLAN.md
revision 3, batch B1–B6, với ADR D1–D7 đã adopt trong <ADR record>, owner-fence protocol và câu
trả lời P2/P4 trong <port review record>. Môi trường thực thi: <môi trường synthetic đã được phép>.
Không gồm live router, provider/model, durable ProviderCopyLifecycle, BE1 tables/fence
implementation, commit/push/deploy.
```
