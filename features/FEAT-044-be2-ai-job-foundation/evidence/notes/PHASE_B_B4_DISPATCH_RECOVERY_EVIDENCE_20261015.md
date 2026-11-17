# BE2-01 Phase B batch B4 — fenced dispatcher, RQ envelope, reconciler, dispatch loss

> Latest review supersedes this earlier checkpoint: B4-RT01 CLOSED on USER_REPORTED_REMOTE
> exact32-source97PASS/0skip+224PhaseAPASS/all exits0. Full B4 NEEDS_REVISION only B4-R01
> (deferred retry page starvation); B5notstarted. See PHASE_B_B4_CODEX_REVIEW_20261015.md.
> Pending/NOT_RUN language below is historical; original package bytes remain unchanged.

> Current override: initial B4 runtime was95collected/88PASS/7FAIL, not still unrun. Claude's
> existing B4-RT01 local correction is packaged; corrected runtime remains NOT_RUN. See
> PHASE_B_B4_RT01_PACKAGE_EVIDENCE_20261015.md. Preserve original executor/checkpoint entries
> below as history; do not run the old B4 ZIP to test the new source.

- State: **B4_CODE_COMPLETE — PostgreSQL/Redis proof NOT_RUN (REQUIRES_STUDIO_RUN)**. Not yet
  B4_READY_FOR_REVIEW: B-02/B-04/B-06a/b need real PostgreSQL + Redis/RQ, which no local
  environment provides. Offline/fake checks below PASS in their own scope only. B5 NOT_STARTED.
- Date/executor: 2026-10-15, Claude (original backend assignment),
  `.worktrees/be2-01-ai-job-foundation`, `feature/be2-01-ai-job-foundation`, HEAD `993a26c`.
  Nothing committed. Work order: ignored `evidence/local/claude/prompts/CLAUDE_PHASE_B_B4_IMPLEMENTATION_PROMPT.md`.
- Authorization: existing `approvals/PHASE_B_TASK_APPROVAL.md` (plan rev3 B1–B6); B3 closed by
  `PHASE_B_B3_CLOSURE_REVIEW_20261015.md`. No new approval/card/plan revision; approval and
  approved plan bytes unchanged. Owner fence remains ASSUMED_CONTRACT.

## 1. Files (uncommitted)

| File | Change | Delta |
|---|---|---|
| `backend/src/sketch2life/domain/ai_jobs/model.py` | `record_dispatch_loss`, `DISPATCH_LOST` | Δ13 (only domain change) |
| `backend/src/sketch2life/application/ports/ai_jobs.py` | `WorkerDispatchEnvelope`, `WorkerCapabilityIssuer`, `OutboxLease`, `ClaimedDispatch`, `AttemptDispatch`; UoW `claim_outbox`/`lease_current`/`ack_dispatch`/`release_outbox`/`dispose_outbox`/`attempt_dispatch`/`has_pending_dispatch` and sweep queries; `add_outbox(now=)`; `DispatchQueuePort.enqueue(envelope)`; `pending_outbox`/`mark_dispatched` removed | Δ6, Δ7, Δ11, Δ14 |
| `backend/src/sketch2life/application/services/ai_jobs.py` | fenced `dispatch_outbox`, `recover_unstarted_dispatches`, targeted `expire_overdue_attempts`/`run_due_retries`, `DispatchPolicy` fixture, `capability_issuer` dependency, `DISPATCH_LOST` public message | Δ6, Δ7, Δ11, Δ13, Δ14 |
| `backend/src/sketch2life/infrastructure/ai_jobs/sql/repository.py` | SQL lease claim (`FOR UPDATE SKIP LOCKED`, generation+1), fenced ack bundle under the job row lock, release/dispose, bookkeeping and sweep queries on the B2 indexes | Δ6, Δ7, Δ11 |
| `backend/src/sketch2life/infrastructure/ai_jobs/rq_queue.py` | new: only broker adapter; envelope args, `description=message_id`, `result_ttl=0`, `failure_ttl=60`, no `Retry`; Redis connection failure → `QueueUnavailable`; fixture receiver `pop_envelope` | Δ14, D3 |
| `backend/src/sketch2life/infrastructure/ai_jobs/outbox_dispatcher.py`, `reconciler.py` | new: thin test-process entries (Q6) over the service | — |
| `backend/src/sketch2life/infrastructure/ai_jobs/fakes.py`, `harness.py` | leased fake outbox, bookkeeping, sweeps; `FakeQueue` carries envelopes; `FakeWorkerCapability` is issuer+verifier; `FakeWorker` uses the envelope capability | Δ12 subset |
| `backend/tests/unit/test_ai_job_application.py`, `features/.../src/run_fixture_contracts.py` | call-site updates for envelopes (3 lines, behaviour unchanged) | Δ14 |
| `features/.../fixtures/error_catalogue.json`, `MANIFEST.json` | regenerated: adds only `DISPATCH_LOST` | Δ13 |
| `backend/tests/unit/test_ai_job_b4_dispatch.py` | new, 11 offline cases | — |
| `backend/tests/integration/ai_jobs/b4_support.py`, `test_outbox_dispatch.py` (4), `test_dispatch_recovery.py` (9 incl. 2 parametrised) | new, 13 PostgreSQL(+Redis) cases | — |
| `backend/tests/integration/ai_jobs/b3_support.py` | rig passes the capability issuer | — |

No schema change: B2 columns (`lease_*`, `publish_attempts`, `last_error_code`, `dispatched_at`,
`dispatch_count`) and indexes are used as designed; B2 migration/BE1 history untouched.

## 2. Behaviour

- **Dispatch (Δ6, Δ14; sequence §2):** claim transaction leases ≤ 50 pending dispatch rows
  (`SKIP LOCKED`, generation+1, 10 s lease). Per row: read; decide eligibility outside SQL;
  short acceptance transaction re-checks the lease and the queued active attempt under the job
  lock and holds the eligibility fence (stale ⇒ one re-decision, then release). Ineligible ⇒
  fenced cancel + dispose. Then the capability is issued and the envelope enqueued outside any
  SQL transaction. Broker down ⇒ `release_outbox` (row pending, job queued). Success ⇒ fenced
  acknowledgement bundle: under the job row lock, mark delivered **and** set the attempt's
  `dispatched_at`/`dispatch_count+1` only if owner+generation still hold; stale or repeated ⇒
  whole-bundle no-op. Settled/stale attempts are disposed only by the current lease holder.
- **Recovery (Δ7, Δ11, Δ13; sequence §4):** `queued_dispatched_not_started` lists active queued
  attempts published ≥ 5 s ago, never started, with no pending dispatch row. Each is re-read under
  the job lock with its expected revision; below 3 publishes ⇒ one new dispatch row for the
  **same attempt**; at the bound ⇒ `record_dispatch_loss` CAS (retryable with existing backoff,
  or exhausted on the final attempt). Start and dispatch loss serialise on the job row: one winner.
- **Sweeps (Δ11):** `overdue_running` (policy attempt timeout from the job's policy snapshot)
  and `due_retries` replace the Phase A all-job scans; each page repeats until empty or no
  progress (no seen-marker, no scheduler). Retry requeue keeps its B3 owner fence.
- **Tokens:** capabilities live only in the transient envelope/RQ job args; outbox payloads stay
  token-free (B2 CHECK), RQ descriptions are the message id, envelopes hide the capability in repr.

Interpretations (no plan change): dispatch bookkeeping does not bump `job_revision` (A3 left it
open; the aggregate excludes these fields and the ack writes them under the job lock, keeping the
B3 parent-before-attempt invariant); `publish_attempts` counts claims; audit/quarantine outbox
delivery stays B5 (`claim_outbox` leases only `kind='dispatch'`); outbox `available_at` now uses
the service clock.

## 3. Acceptance mapping (PostgreSQL/Redis rows NOT_RUN until the Studio run)

| Acceptance | Tests |
|---|---|
| B-02 broker down loses nothing, replay creates no semantic attempt | `test_outbox_dispatch::test_broker_outage_keeps_sql_pending_and_recovery_adds_no_attempt` (injected unreachable endpoint, real RQ afterwards) + offline twin |
| Δ14 envelope/RQ options, token-free SQL | `test_dispatch_publishes_through_rq_and_commits_the_ack_bundle`; logs: `test_dispatcher_and_rq_logs_never_carry_the_capability` (B-05e dispatcher/RQ part only) |
| Δ6 disjoint concurrent claims | `test_concurrent_claims_lease_disjoint_rows` |
| B-04c stale lease mark/release no-op; repeated ack | `test_dispatch_recovery::test_stale_lease_holder_mark_and_release_are_no_ops_after_takeover` + offline twin |
| B-06a enqueue-before-mark crash, same-attempt redelivery dedup | `test_enqueue_then_crash_before_mark_republishes_same_attempt_and_start_dedups` (child dispatcher killed with `os._exit` after the real enqueue) |
| B-04a receive-before-start loss → same attempt completes | `test_lost_receive_is_republished_as_the_same_attempt_and_completes` |
| B-04b(i/iii/v) bound, backoff, null start, provenance, no early attempt | `test_publish_bound_then_dispatch_loss_keeps_provenance_and_policy_retries` + domain unit cases |
| B-04b(ii) final attempt exhausted, never reopened | `test_final_attempt_dispatch_loss_is_exhausted_and_never_reopened` |
| B-04b(iv) CAS race vs start, both orders | `test_dispatch_loss_and_start_have_exactly_one_winner[start|reconciler]` |
| No recovery fan-out | `test_concurrent_reconcilers_create_exactly_one_recovery_intent` |
| B-06b overdue running → policy retry; targeted queries | `test_overdue_running_and_due_retry_sweeps_are_targeted` |

Not in B4: worker loop, provider, completion recovery (B-06b provider/completion window beyond
the timeout path), HMAC attempt-bound verification (Δ8), incident/quarantine intents and sink
delivery (Δ9/Δ15), atomic notices (Δ10), B6 crash matrix/conformance.

## 4. Checks actually run (Windows, `backend/.venv` Py3.12.10, rq 2.11.0; PYTHONPATH/MYPYPATH = worktree src)

| Check | Result | Type |
|---|---|---|
| Phase A 6 suites | 223 passed, 1 skipped (Pillow, live-route) | DIRECT_LOCAL_RUN |
| B2+B3+B4 suite (`tests/integration/ai_jobs` + B3/B4 unit files) | 33 passed (8 B2 + 14 B3 + 11 B4 offline); **62 skipped = NOT_RUN** (10 B2 + 39 B3 + 13 B4 PostgreSQL/Redis) | DIRECT_LOCAL_RUN |
| Fixture runner (after regenerating fixtures) | 20/20, 215 checks, digest `d17f58a3…41f68` unchanged | DIRECT_LOCAL_RUN |
| ruff, ruff format (new files), mypy strict (src + tests) | exit 0 | DIRECT_LOCAL_RUN |
| harness / security / architecture / skeleton / `git diff --check` | exit 0 | DIRECT_LOCAL_RUN |
| Runner host-logic simulation (docker stubbed) | closed B3 → B4, retry, unknown change refused, container failure → FAIL | DIRECT_LOCAL_RUN, no container/test |
| **PostgreSQL + Redis/RQ B4 proofs and full regressions on Studio** | **NOT_RUN** | — |

Ignored receipts: `evidence/local/b4-local-checks-20261015/`. Structured copy:
`evidence/metrics/PHASE_B_B4_LOCAL_CHECKS_20261015.json`.

## 5. Package (ignored, local) — closed B3 snapshot → B4

| File | sha256 |
|---|---|
| b4_delta.patch (18 files) | `44d98cd6983b883a3ef6ab52d8804d669797e678e5d06e49a074c3dc5c44a8e6` |
| b4_source.sha256 (32 files) | `70b2a1600682aec3cfe2dabd80608d45c107f88d24ed25dd18d0e804aff8ef4d` |
| b3_closed.sha256 (closed B3 manifest copy) | `0814d514cf75128a80552e313af871a0ceff2758ef2fa8d87a3e4d0b2402dbf8` |
| run_b4_on_studio.sh | `6daa16b3c84a080a9c8863b4cec6b9e83e997cf5268be52473c7bea15ea37d4c` |
| be2-b4-studio-20261015.zip (the four files) | `2a06c8bb32c023602302b9d64183fb08adea580cfeb9d65c00d2d5ebef8fc8a4` |

Builder `evidence/local/b4-local-checks-20261015/build_b4_package.py` rebuilds the closed B3
snapshot from base blobs + B2 + B3 + B3-R01 patches (all 20 `0814d514` hashes), applies the delta
(all 32 B4 hashes), refuses a second application and reverse-checks this worktree. Earlier
package directories are unchanged. The runner accepts only the exact closed B3 snapshot or the
exact B4 snapshot (retry), runs B2+B3+B4 (expected 95 cases, 0 skips) with `BE2_TEST_REDIS_HOST`,
Phase A and the fixture runner, fails on any non-zero exit or skip, and ends with an attributable
summary block plus `outer_runner_exit`/`RUNNER_RESULT`. Redis tests use unique `be2_b4_<random>`
queues and delete only those keys; the shared services are never stopped or recreated.

## 6. Limits

All B4 runtime acceptance is NOT_RUN until the user's Studio run (USER_REPORTED_REMOTE). Local
rq is 2.11.0, Studio reported 2.12.0; the adapter uses only the stable `enqueue`/`pop_job_id`/
`Job.fetch` API. ASSUMED_CONTRACT owner fence and B-12 limits still apply. Executor evidence only.

## 7. Studio run attempt 1 —2026-10-15 (USER_REPORTED_REMOTE)

- Package hashes verified; `source_state=closed_b3_snapshot`; the B4 delta was applied and all 32
  B4 source hashes verified (`b4_source_verified=32`). Studio source is now the exact B4 snapshot,
  so a retry takes the `b4_snapshot_verify_only` path. Receipts dir
  `evidence/local/b4-runtime-20261015/run-20261015T100400Z-3200` (created, no test output).
- Docker had no local `python:3.12-slim` image (re-pulled, digest `sha256:a6e34c59…11b1`) and then
  failed: `network sketch2life-be2-net not found`, `outer_runner_exit=125`, `RUNNER_RESULT=FAIL`.
- Interpretation: **ENVIRONMENT_BLOCKED, every B4/B2/B3/Phase A runtime check NOT_RUN** — not a
  test failure. The previously reported dedicated network (and possibly containers, volumes and the
  Python 3.12 venv volume) is missing. Re-creating services/volumes or reinstalling dependencies is
  outside the B4 work order; it needs a read-only inventory first and an explicit user decision.

## 8. Environment inventory and authorized rebuild —2026-10-15

- User-reported read-only inventory: no `sketch2life-be2-*` network or containers; only volume
  `sketch2life-be2-venv312` (probably auto-created empty by attempt 1); image `python:3.12-slim`;
  private password file present. User explains the Studio had just been stopped, which evidently
  discards Docker state while `$HOME` (repo, package, password file) persists.
- Actual user authorization (verbatim): **"cho phép dựng lại"**, in reply to the offer to prepare
  a rebuild of the synthetic test environment. Scope: re-create only the dedicated synthetic
  network/PostgreSQL17/Redis8 services/volumes and reinstall the Python 3.12 venv; no data,
  secret or source transfer, no other card/batch.
- Prepared (not executed here): ignored `evidence/local/studio-env-rebuild-20261015/rebuild_be2_env.sh`
  sha256 `28950e637d27883bd4df8e5a92a6fc0b6d03284cec0a619a2ca9ce578c4b79d8`. Idempotent; keeps
  existing resources; same names/aliases/password file; PostgreSQL/Redis pinned to the recorded
  O-06 digests; pip constrained to the recorded O-08 versions; prints inventory and
  authenticated-connection checks only. Then rerun `run_b4_on_studio.sh` (verify-only path).

## 9. Studio environment rebuild and run attempt 2 —2026-10-15 (USER_REPORTED_REMOTE)

- Rebuild: `ENV_REBUILD_RESULT=PASS`, both containers healthy; inventory Python 3.12.15,
  SQLAlchemy 2.1.4, psycopg 3.3.6, Alembic 1.20.0, redis-py 6.4.0, RQ 2.12.0, pytest 8.4.2,
  FastAPI 0.143.1, Pydantic 2.14.1, Pillow 12.3.0, av 18.1.0; PostgreSQL 17.11, Redis 8.10.2;
  authenticated PostgreSQL and Redis connections PASS — identical to the O-08 baseline.
- Run `2026-10-15T10:24:24Z`, receipts `evidence/local/b4-runtime-20261015/run-20261015T102424Z-13661`,
  `source_state=b4_snapshot_verify_only`, manifest `70b2a160…` (32 files OK before each suite).
- **B2–B4: 95 collected, 88 passed, 7 failed, 0 skipped**; Phase A 224 passed/0 skip; fixture
  runner 20/20 (digest unchanged); `outer_runner_exit=1`, `RUNNER_RESULT=FAIL`.
- Passed B4 runtime cases: stale-lease no-op (B-04c), both CAS race orders vs start (B-04b iv),
  concurrent reconcilers (one intent), targeted sweeps (B-06b), disjoint concurrent claims.
- **B4-RT01 (executor finding):** all 7 failures are in the fixture receiver
  `rq_queue.pop_envelope`: on RQ 2.12 `Queue.pop_job_id()` raises `ValueError` on an empty queue
  instead of returning `None`, so every `drain` failed after taking its real envelopes. In each
  failing test the assertions before `drain` had passed (e.g. RQ job func/description/TTLs/no
  retry; broker-down release; crash child exit 17, held lease, one RQ job, lease-gated takeover
  publish). These 7 cases remain FAILED/unproven for their remaining assertions.
- Also observed: SQLAlchemy `SADeprecationWarning` for `Interval * Integer` in `overdue_running`.
