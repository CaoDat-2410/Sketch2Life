# BE2-01 Phase B — durable AI job foundation (plan)

- Plan revision: 1
- Status: PLANNED
- Approval status: AWAITING_APPROVAL (no approval exists; Phase A approval does not cover Phase B)
- Implementation status: NOT_STARTED
- Date: 2026-10-14, Asia/Saigon. Author: Claude (executor), planning only — no code, install,
  DB/broker start, cloud run or source upload in this turn.
- Owner: P3 / BE2. Branch: `feature/be2-01-ai-job-foundation` (worktree `.worktrees/be2-01-ai-job-foundation`).
- Companions: `PHASE_B_ADR_PROPOSAL.md` (PROPOSED decisions), `PHASE_B_PORT_REVIEW.md` (P2/P3/P4).
- Roadmap slot: Q01 — PLAN_PREPARATION only. ACTIVE slot stays Q00 until Phase A has a valid
  checkpoint disposition.

## 1. Problem and result

Phase A proved job/attempt/receipt/cancel/completion semantics with in-memory fakes only
(`PHASE_A_Q00_FINAL_CODE_REVIEW_20261014.md`: PASS at fake/contract scope). Nothing survives a
process restart, CAS is a Python lock, the outbox is a dict and there is no broker. SRS B22.3,
B19.11, DATA-25 and the BE2-01 card require the durable chặng: “restart sau commit giữ
job/attempt/receipt, outbox dispatch retry không tạo semantic attempt mới và CAS chặn concurrent
completion” (FEAT-040 `BE_AI_TASKS.md` BE2-01).

Result of Phase B: an AI-owned durable repository/unit-of-work, migrations, transactional outbox,
queue dispatcher, durable worker/completion recovery and actual adapter fault evidence, reusing
the reviewed Phase A domain/application semantics unchanged except for the minimal port changes
listed in §5. Phase B does **not** deliver live routing, provider inference, real copy deletion or
BE1 tables.

## 2. Preconditions before any Phase B code (gates)

| # | Gate | Current state |
|---|---|---|
| G1 | Phase A checkpoint disposition (task owner) with production adoption explicitly deferred or decided | PENDING (`PHASE_A_ACCEPTANCE_GATE_RECORD.md`) |
| G2 | This plan independently reviewed, then explicit approval naming `plan/PHASE_B_PLAN.md` revision 1 in a separate record | NOT_STARTED |
| G3 | ADR decisions D1–D6 in `PHASE_B_ADR_PROPOSAL.md` adopted (DB, migrations, queue, UoW/isolation, dispatch/recovery, worker identity) | PROPOSED |
| G4 | P2/P4 answers in `PHASE_B_PORT_REVIEW.md` (schema ownership, artifact/audit/notice delivery, composition/migration order) | PENDING |
| G5 | Authorised synthetic-only execution environment with PostgreSQL + Redis (Linux; separate Sketch2Life env, never Wan2.2), dependency inventory recorded before tests | NOT_STARTED |

Batch B1 exists to close G3/G4; B2–B6 code starts only after G1–G5.

## 3. Allowed changes and exclusions

Allowed (after approval): new AI-owned infrastructure modules, migrations, worker/dispatcher
entry modules for tests, integration tests, a durable conformance runner, the minimal port/service
changes in §5, FEAT-044 records/evidence.

Excluded: Phase A behaviour changes beyond §5; BE1 tables or BE1 repository code; mounting the
CMD-44 router in the live app or registry adoption (P4/INTG-02); provider/model adapters and real
inference (BE2-04/08); durable ProviderCopyLifecycle (BE2-14 — fake stays); production numeric
policy (retry/poll/TTL stay named PROPOSED values); dependency installs on Windows; cloud
resources/deployment; commit/push unless separately requested; other BE2 cards.

## 4. File map (proposed outputs)

| Path | Batch | Content |
|---|---|---|
| `backend/src/sketch2life/infrastructure/ai_jobs/sql/tables.py` | B2 | SQLAlchemy Core metadata in PostgreSQL schema `ai_jobs` (tables in §6) |
| `backend/migrations/` (+ `alembic.ini`, branch label `ai_jobs`) | B2 | Alembic env + first AI revision; layout per D2/P4 answer |
| `backend/src/sketch2life/infrastructure/ai_jobs/sql/repository.py` | B3 | `SqlAiJobRepository` / unit of work implementing `AiJobUnitOfWork` |
| `backend/src/sketch2life/infrastructure/ai_jobs/outbox_dispatcher.py` | B4 | Lease-based outbox claim → eligibility recheck → enqueue → mark |
| `backend/src/sketch2life/infrastructure/ai_jobs/rq_queue.py` | B4 | `DispatchQueuePort` adapter (D3 preferred: Redis/RQ) |
| `backend/src/sketch2life/infrastructure/ai_jobs/worker_capability.py` | B5 | HMAC job/attempt-scoped capability issuer/verifier (D6) |
| `backend/src/sketch2life/infrastructure/ai_jobs/worker.py` | B5 | Worker loop: receive → start → (fake) provider → completion; sweeps |
| `backend/src/sketch2life/application/ports/ai_jobs.py`, `application/services/ai_jobs.py` | B3/B5 | Minimal changes in §5 only |
| `backend/tests/integration/ai_jobs/test_sql_repository.py`, `test_migrations.py`, `test_outbox_dispatch.py`, `test_restart_recovery.py`, `test_concurrency.py`, `test_completion_recovery.py` | B2–B5 | Marked `requires_postgres` / `requires_redis`; skip ⇒ NOT_RUN, never PASS |
| `features/FEAT-044-be2-ai-job-foundation/src/run_durable_conformance.py` | B6 | Re-runs Phase A scenario set against the SQL adapter + crash-point matrix |
| `features/FEAT-044-be2-ai-job-foundation/evidence/…` | B1–B6 | Diagrams, migration matrix, receipts, fault traces, handoff |

## 5. Minimal port/service changes (exact behaviour, reason, tests)

| Change | Reason | Test |
|---|---|---|
| Replace `AiJobUnitOfWork.list_jobs()` scans with targeted queries `due_retries(now, limit)`, `overdue_running(now, limit)`, `jobs_for_notice(notice, limit)` | Full scans do not scale and hold locks; same results as Phase A filters | Phase A suites on fake + SQL parity tests |
| Outbox entries gain `kind` (`dispatch`, `audit`, `quarantine`) and lease fields; `claim_outbox(now, lease, limit)` / `mark_dispatched` / `release` | Audit and quarantine are external side effects; recording them in the same commit and delivering after commit removes the “committed but audit lost” window (FIX-NFR-03) | Crash after commit before delivery → delivered once on restart (idempotent by message id) |
| Service: external port calls (eligibility/authorization/artifact describe) happen before the write transaction; the write re-reads and CASes on the expected `job_revision`, retrying the decision once on conflict | Avoid holding row locks across P2 calls; CAS already guards correctness | Concurrency test: eligibility change between read and write → re-decided, no stale write |
| `InMemoryAiJobStore` implements the same new methods | Keep Phase A runner/tests valid | Full Phase A suites + runner unchanged results |

No other domain/contract change. Any further change discovered in B3–B5 is recorded as a plan
change and reviewed before merge.

## 6. Durable data model (proposed; D1/D2)

Schema `ai_jobs` (AI-owned; no foreign keys into BE1 tables, references are opaque ids):

| Table | Key / constraints | Notes |
|---|---|---|
| `job` | PK `job_id`; `job_revision` CAS column; check state ∈ DATA-25 states | scope columns, pinned request ref, progress/failure JSONB, policy snapshot id, timestamps (timestamptz) |
| `attempt` | PK `attempt_id`; unique (`job_id`, `attempt_number`) | pinned request ref per attempt, started/finished/outcome |
| `command_receipt` | PK (`organization_id`, `principal_id`, `contract_name`, `target_id`, `idempotency_key`) | fingerprint, job_id, outcome, revision at commit; retention = named PROPOSED IDEMPOTENCY_TTL |
| `semantic_request` | unique (org, job_type, request_id, request_revision, input_hash, context_revision, target_id, purpose_code, session_id, subject_refs_hash) | → job_id; business uniqueness survives receipt expiry |
| `completion_receipt` | PK (`job_id`, `attempt_id`) | authoritative only; fingerprint, disposition, reason, revision after |
| `cancellation_notice` | PK `notice_id` | idempotent owner notices |
| `outbox` | PK `message_id`; index (`dispatched_at` null, `available_at`) | kind, payload JSONB (no secrets/child data), lease owner/until, publish attempts, last error code |

## 7. Batches (no code until gates)

| Batch | Scope | Exit / evidence |
|---|---|---|
| **B1** | Close D1–D6 and P2/P4 port questions; transaction/failure-point sequence diagram (create, dispatch, start, completion, retry, cancel/notice); crash-window table; environment inventory plan | ADR record(s) adopted by owner; port answers recorded; diagrams in evidence. No code |
| **B2** | `tables.py` + Alembic revision for §6; upgrade on empty DB, re-run idempotent, downgrade policy per D2 | Migration matrix (fresh/existing/rerun), constraint introspection, restart keeps rows (B-01) |
| **B3** | `SqlAiJobRepository`: transaction per use case, CAS UPDATE … WHERE revision, `INSERT … ON CONFLICT DO NOTHING` + re-read for receipts/semantic index, rollback on error; §5 port changes | B-03, B-05, B-07, B-08 on real PostgreSQL; Phase A suites still green on fake |
| **B4** | Outbox dispatcher (lease, SKIP LOCKED, eligibility recheck R09, mark after enqueue), RQ adapter with message id as broker job id, bounded publish retry; side-effect outbox kinds | B-02, B-04, B-06 incl. broker-down and crash between enqueue and mark |
| **B5** | Worker loop + capability; timeout/retry sweeps via targeted queries; completion recovery after restart; cancel/revoke/recall/context races with current-authority checks | B-05, B-06, B-09; provider remains the Phase A fake (`AiProviderPort`) |
| **B6** | Durable conformance runner, crash-point matrix, regression of Phase A semantics on SQL adapter, handoff to P2/P4 | B-10, B-11, B-12; remaining integration/provider gates listed |

### Crash windows and recoverability (no exactly-once claim)

| Window | Recovery |
|---|---|
| Crash before commit | Nothing durable; client retries same key → normal create |
| Commit done, crash before outbox delivery | Outbox row pending → dispatcher delivers after restart |
| Enqueued to broker, crash before `mark_dispatched` | Re-enqueue with same message/broker id; worker `start_attempt` dedup (`DUPLICATE_DELIVERY`/`ATTEMPT_NOT_ACTIVE`) → no new semantic attempt |
| Broker down | Enqueue fails → row stays pending, job stays `queued` (recoverable) |
| Worker crash after provider call, before completion commit | Attempt times out → policy retry (new attempt) or worker re-submits same claim; provider may have run twice — reconciliation by attempt id/output lineage; provider-side dedup is a provider-adapter concern (BE2-04/08) |
| Completion committed, crash before audit/quarantine | Side-effect outbox rows delivered after restart |
| Concurrent completion/cancel | Row CAS + completion receipt PK → one authoritative outcome |

## 8. Acceptance (to verify; nothing claimed PASS)

| ID | Acceptance | Source | Planned check / environment |
|---|---|---|---|
| B-01 | Restart after commit keeps job/request/attempt revisions, receipts/fingerprints, outbox | B22.3; P-NFR-04; FIX-NFR-03; BE2-01 card | `test_restart_recovery.py` — kill process after commit, new process reads identical rows (checksum) · PostgreSQL |
| B-02 | Broker down does not lose job; dispatcher replay creates no new semantic attempt | B22.3 “Queue unavailable after commit leaves recoverable queued job” | `test_outbox_dispatch.py` with Redis stopped/restarted · PostgreSQL + Redis |
| B-03 | Same key + same payload replays; changed payload conflicts; correct scope incl. concurrent callers and process restart | B22.1 idempotency lifecycle; B19.11 | `test_sql_repository.py` + `test_concurrency.py` (N parallel creates, two processes) |
| B-04 | Same-attempt redelivery dedup; only allowed retry creates next attempt | DATA-25; B22.3 | Duplicate broker delivery + crash-between-enqueue-and-mark cases |
| B-05 | Concurrent completion → one authoritative outcome/receipt; identical replay same result; conflicting completion never overwrites | B22.3 completion rules | Parallel completion workers on one attempt; replay after restart |
| B-06 | Crash/replay around dispatch/output/persist keeps identity, fingerprint, disposition, provenance; external effects reconciled | B22.3; MP-04 | Crash-point matrix (§7) with fault injection hooks |
| B-07 | Semantic dedup scope isolation (target/purpose/session/subjects) durable | Phase A R02; B22.1 | SQL unique constraint tests |
| B-08 | Transaction rollback leaves no partial job/receipt/outbox | B22.1 “Failed storage rolls back domain mutation” | Injected DB error mid-transaction |
| B-09 | Cancel/revoke/recall/context-change races do not reopen or expose; current authority checked before read/cache/completion | B19.11 collision table; DATA-25 | Race tests with real CAS; Phase A R03a/R09/R10 parity |
| B-10 | Durable outbox/receipt/CAS/rollback verified on the real adapter (fake pass not substituted) | BE2-01 card evidence | Conformance runner on SQL adapter; report lists adapter + environment |
| B-11 | Migration/conformance report; Phase A regression suites still pass on fake; checks needing LightningAI/Linux labelled | PLAN.md §6; tracker | Migration matrix + Phase A suites + runner (Windows OK for fake parts) |
| B-12 | Not proven here and listed as remaining: namespace/live router, provider inference, actual copy deletion, production policy, deployment | ADR-0015; roadmap | Handoff section with owners (P4 INTG-02, BE2-04/08/14) |

## 9. Verification and evidence

Commands (planned; not run): Alembic upgrade/downgrade on a disposable database; `python -m pytest
backend/tests/integration/ai_jobs -m "requires_postgres or requires_redis"`; Phase A suites and
runner; ruff/mypy on changed modules; `tools/validate_{harness,architecture,repository_security,skeleton}.py`;
`git diff --check`. Integration tests skip with an explicit reason when services are absent and
are reported NOT_RUN / REQUIRES_LIGHTNINGAI_TEST. Evidence per batch in `evidence/` with command,
interpreter/service versions, synthetic data only, redacted logs, crash-point receipts.

## 10. Sample approval text (NOT an approval)

```text
Tôi duyệt BE2-01 Phase B theo features/FEAT-044-be2-ai-job-foundation/plan/PHASE_B_PLAN.md
revision 1, batch B1–B6, với các quyết định đã adopt trong <ADR record> và câu trả lời P2/P4 trong
<port review record>. Môi trường thực thi: <tên môi trường synthetic đã được phép>. Không gồm live
router, provider/model, durable ProviderCopyLifecycle, BE1 tables, commit/push/deploy.
```
