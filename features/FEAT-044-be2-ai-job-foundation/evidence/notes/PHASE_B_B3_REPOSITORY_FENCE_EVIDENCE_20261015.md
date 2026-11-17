# BE2-01 Phase B batch B3 — SQL repository/UoW, Δ1–Δ5, ASSUMED_CONTRACT owner fence

> Superseded checkpoint: user has now reported 69 B2+B3 tests PASS/0skip on Studio, but
> independent review is **NEEDS_REVISION, B3-R01 OPEN**. See
> `PHASE_B_B3_CODEX_REVIEW_20261015.md` and matching review metrics for the current state.
> The NOT_RUN/local/self-review entries below preserve the executor's pre-Studio evidence.

- State: **B3_CODE_COMPLETE — PostgreSQL proof NOT_RUN (REQUIRES_STUDIO_RUN)**. Not yet
  B3_READY_FOR_REVIEW: the B3 acceptance (B-03, B-07, B-08, B-09a–d) is defined on PostgreSQL and
  no PostgreSQL run of this source exists. Offline/fake checks below PASS in their own scope only.
- Date/executor: 2026-10-15, Asia/Saigon; Claude (original backend assignment), in worktree
  `.worktrees/be2-01-ai-job-foundation`, branch `feature/be2-01-ai-job-foundation`, HEAD `993a26c`.
- Authorization: existing `approvals/PHASE_B_TASK_APPROVAL.md` (plan rev3 B1–B6; B2 review stop
  satisfied by `PHASE_B_B2_CLOSURE_REVIEW_20261015.md`). User step-2 instruction in the same session
  restates it; no new approval, card or plan revision. Phase A approval and approved plans unchanged.
- Owner fence is **ASSUMED_CONTRACT** (OwnerFenceV1/0.1-candidate). No P2 adapter, P1/P2/P4
  sign-off or real integration is claimed (B-12). Provider stays fake; no B4/B5 code.

## 1. Files (all uncommitted)

| File | Change | Role |
|---|---|---|
| `backend/src/sketch2life/application/ports/ai_jobs.py` | modified | Δ1 `OwnerFence` on authorization/eligibility/artifact decisions; Δ2 `FenceResult`, versioned `OwnerFencePort`, `AiJobUnitOfWork.hold_owner_fences`; Δ4 `SemanticRequestKey.sha256()`; Δ5 `UniqueConflict(kind)`; `JobRevisionConflict` moved here; `get_job(for_update=)`, `add_audit_intent` |
| `backend/src/sketch2life/application/services/ai_jobs.py` | modified | Δ3/Δ5 round structure for create, cancel, start, completion and retry requeue |
| `backend/src/sketch2life/infrastructure/ai_jobs/fakes.py`, `harness.py` | modified | Δ12 subset: `FakeOwnerFences` shared by fake ports/store, typed conflicts, semantic store keyed by the canonical sha256, audit intents |
| `backend/src/sketch2life/infrastructure/ai_jobs/sql/repository.py` | new | `SqlAiJobRepository`/`SqlAiJobUnitOfWork` over the B2 `ai_jobs` schema |
| `backend/src/sketch2life/infrastructure/ai_jobs/sql/owner_fence_fixture.py` | new | test-only ASSUMED_CONTRACT fixture schema `owner_fence_fixture` + fixture owner ports |
| `backend/tests/unit/test_ai_job_b3_fences.py` | new | 14 offline cases on fakes |
| `backend/tests/integration/ai_jobs/b3_support.py`, `test_sql_repository.py`, `test_create_races.py`, `test_owner_fence.py` | new | 37 `requires_postgres` cases |

Unchanged: B2 migration/metadata/env/conftest/test_migrations (all eight B2 hashes still match
`f388ce36…`), BE1 Alembic history, domain model, contracts. No new Alembic revision: B3 needs no
schema change (`job.accepted_fences` already exists). The fixture DDL is created only by tests,
only on databases matching the conftest disposable name `be2_b2_<16 hex>`.

## 2. Behaviour and Δ1–Δ5 mapping

| Delta | Implementation |
|---|---|
| Δ1 | Decisions carry `fence: OwnerFence \| None`. A missing fence is never current: `_hold` treats it as stale. Fakes/fixture always supply one |
| Δ2 | `hold_owner_fences` delegates to an `OwnerFencePort` built on the UoW's own connection; the fixture reads fence rows `FOR SHARE ... ORDER BY fence_scope`, so the hold lasts to commit/rollback; unknown rows are stale. The repository refuses a port whose `contract_version` ≠ `OwnerFenceV1/0.1-candidate`. Held epochs are written to `job.accepted_fences` on insert/CAS |
| Δ3 | Each fenced use case: read transaction → owner decisions outside any write transaction → write transaction re-reads (`get_job(for_update=True)`, receipts), applies guards, holds the decisions' fences **before any mutation**, writes, commits. Stale/missing fence ⇒ rollback, one fresh re-decision; still stale ⇒ typed outcome (`409 STALE_CONTEXT` retryable for create/cancel/completion, `StartResult(False,"STALE_CONTEXT")`, retry not requeued). Applied to create (grant + eligibility), cancel (grant), start (eligibility), completion (eligibility + admitted owned-output artifact fences), retry requeue (eligibility) |
| Δ4 | `SemanticRequestKey.sha256()` = sha256 of canonical JSON: all strings NFC, explicit `null` session, subject refs NFC-normalised then sorted, duplicates kept. Fake and SQL both key the semantic row only by it |
| Δ5 | Plain INSERTs; PostgreSQL unique violation (SQLSTATE 23505) → `UniqueConflict(kind)` by constraint name; the whole UoW rolls back. Create is one candidate transaction: job, attempt, semantic, command receipt, dispatch outbox row, audit intent. A conflict starts a fresh round that re-reads the winner: same key ⇒ replay/`IDEMPOTENCY_PAYLOAD_MISMATCH`; same semantic ⇒ own `deduplicated` receipt + audit intent only. Two rounds max, then `409 IDEMPOTENCY_CONFLICT` retryable. No `ON CONFLICT DO NOTHING` in BE2 tables |

Same-transaction audit intents (B-08b, B3 part): create, dedup receipt and Teacher cancel write a
deterministic-`event_id` audit outbox row (`kind='audit'`) in the committing transaction; the
Phase A fake audit sink still receives the event after commit. Completion/incident/quarantine
intents (Δ9/Δ15), dispatcher lease (Δ6), reconciler (Δ7/Δ11/Δ13), envelope/capability (Δ8/Δ14)
and atomic notices (Δ10) are **not** implemented; the SQL UoW raises `NotImplementedError` for
`pending_outbox`, `mark_dispatched`, `notice_seen`, `record_notice` instead of guessing B4/B5.

Interpretations within scope (no plan change):

1. `dispatch_outbox` keeps the Phase A path. Its fenced pre-publish acceptance belongs to the
   B4 dispatcher rewrite (Δ6 and B1 assumption A2), so B3 does not half-rewrite it.
2. Completion side effects (`ArtifactPort.quarantine`, input-mismatch audit) are collected during
   the decision and applied only after the write commits, so a rolled-back stale round causes no
   effect. Phase A order of audit events/quarantine is preserved (runner digest identical).
3. `FakeArtifacts.quarantine` now bumps the artifact fence (an owner state change), matching the
   fixture. Fake eligibility set mutations do not bump; tests bump explicitly.
4. `owner_fence_fixture.py` sits under `src/.../sql/` exactly as plan §4 names it; nothing imports
   it outside tests and no Alembic revision creates it.
5. `attempt.outcome` stays `VARCHAR(40)` (B2): every current outcome string fits; longer codes
   would need a forward revision, not a B2 rewrite.

## 3. Acceptance mapping (all PostgreSQL rows NOT_RUN until the Studio run)

| Acceptance | Tests |
|---|---|
| B-03a two processes, same key+payload | `test_create_races::test_b03a_*` (spawn processes, barrier after first fence hold, loser needs round 2) |
| B-03b different keys, same semantic | `test_b03b_*` (1 job/attempt/dispatch/semantic, 2 receipts, 2 audit intents) |
| B-03c same key, different payload | `test_b03c_*` (`IDEMPOTENCY_PAYLOAD_MISMATCH`, no orphan) |
| B-03d session null vs populated / null+null | `test_b03d_*` |
| B-03e permuted / NFC-equivalent subjects | `test_b03e_*` |
| B-03f restart between rounds | `test_b03f_*` (loser process exits after round-1 rollback; restarted process converges) |
| B-07 semantic/idempotency/CAS | `test_sql_repository::test_semantic_scope_isolation_is_durable` (8 scope variations, restarted engine), `test_cas_and_plain_inserts_*`, `test_concurrent_cas_lets_exactly_one_writer_win`, `test_job_and_attempts_round_trip_*`, `test_create_bundle_*` |
| B-08a rollback leaves nothing | `test_failure_at_each_create_boundary_leaves_nothing` (6 boundaries), `test_cancel_commits_*_or_nothing`, `test_unresolved_unique_conflicts_*` |
| B-08b (B3 part) no accepted create/cancel without audit intent | same tests: audit row present iff the mutation committed; the incident `503` path is B5 |
| B-09a consent/context stale | `test_owner_fence::test_b09a_*` (start, completion, repeated-stale typed outcome), notice withheld, CAS alone unaware |
| B-09b artifact state stale | `test_b09b_*` |
| B-09c authorization stale (create/cancel) | `test_b09c_*` |
| B-09d read/cache current authority, history unchanged | `test_b09d_*` |
| Linearization both orders | owner-first: B-09a/b/c; BE2-first: `test_be2_hold_first_commits_first_and_owner_change_waits` |
| Missing/unknown fence | `test_missing_or_unknown_fence_is_never_treated_as_current` (+ offline twin) |

## 4. Checks actually run (Windows, `backend/.venv` Py3.12.10; PYTHONPATH/MYPYPATH = worktree `backend/src`)

| Check | Result | Type |
|---|---|---|
| Phase A 6 suites | 223 passed, 1 skipped (Pillow, live-route; historical local skip) | DIRECT_LOCAL_RUN |
| B2+B3 suite (`tests/integration/ai_jobs` + `test_ai_job_b3_fences.py`) | 22 passed (14 B3 offline + 8 B2 offline), **47 skipped = NOT_RUN** (37 B3 + 10 B2 PostgreSQL) | DIRECT_LOCAL_RUN |
| Phase A fixture runner (default) | 20/20 PASS, 215 checks, not_run 1; `results_sha256=d17f58a3…41f68`, identical to the Q00 final run | DIRECT_LOCAL_RUN |
| ruff (application, infrastructure/ai_jobs, B3 tests), ruff format (new files), mypy strict (ports, service, infrastructure/ai_jobs; B3 tests) | exit 0 | DIRECT_LOCAL_RUN |
| harness / repository security / architecture / skeleton / `git diff --check` | exit 0 | DIRECT_LOCAL_RUN |
| PostgreSQL B3 proofs | **NOT_RUN** (no local PostgreSQL 17; local Docker engine unavailable) | — |

Receipts: ignored `evidence/local/b3-local-checks-20261015/`. Structured copy:
`evidence/metrics/PHASE_B_B3_LOCAL_CHECKS_20261015.json`.

## 5. Studio package (ignored, local only)

Directory `evidence/local/b3-studio-package-20261015/`, builder
`evidence/local/b3-local-checks-20261015/build_b3_package.py`.

| File | sha256 |
|---|---|
| b3_source.patch (11 files, on top of the B2 snapshot) | `a2e479d5ee8fc59c67568f5089cf981672b76315d7b0796c3bddc1d0d956e312` |
| b3_source.sha256 (19-file manifest = 8 B2 + 11 B3) | `ea5cf57e12058f48cbd6ef73b23ca9a8b60b78c374f655ba629623b6b308939f` |
| run_b3_on_studio.sh | `6a9e57b787a3b76b5c3cae4f9fe87c4179b088336859b745a5d2c4eae2f1f5cc` |
| b2_source.patch (copy, only for a pristine base) | `f388ce3646db5844ca8baabe17db657e0580a92fc21f800f75753e139a419bff` |
| be2-b3-studio-20261015.zip (the four files above) | `4a7e5dd9a30ccdc1abc6d00cf95f82295f9aec0ed15f148ed9527e8ca06e050f` |

Builder self-check: reverse-check against this worktree exit 0; pristine base blobs + B2 patch +
B3 patch in an isolated scratch checkout reproduce all 19 hashes; real index not touched. Files
were normalised to LF before hashing. The local EOF disposition of
`test_ai_job_q00_followups.py` is a separate approved fix, excluded from the package.

Runner contract: accepts the reported B2 snapshot (verifies the eight B2 hashes and the exact B2
patch, then applies B3), a pristine base (applies B2 then B3) or an already-applied exact B3
snapshot; refuses anything else without reset/clean. Inside the existing Python 3.12 runner
image/venv it verifies sources before every suite, runs B3+B2, Phase A and the fixture runner,
fails on any non-zero exit **or any skip**, and always prints `outer_runner_exit` and
`RUNNER_RESULT`. Services, volumes and `be2_synthetic` are untouched.

## 6. Remaining limits

- PostgreSQL B-03/B-07/B-08/B-09a–d proofs: NOT_RUN until the user runs the package; results will
  be USER_REPORTED_REMOTE and bound to the hashes above.
- ASSUMED_CONTRACT fixture only; actual P2 fence rows/function, notice transport and role
  concurrence remain B-12. Dispatch fence, incident/quarantine intents, notices, capability and
  worker remain B4/B5; full restart/crash (B-01) and conformance (B-11) remain B6.
- This is executor evidence, not an independent review.

## 7. Executor self-review before the Studio run —2026-10-15

Requested by the user before running the package. Executor review, not independent.

| # | Finding | Disposition |
|---|---|---|
| SR-1 | `test_cas_and_plain_inserts_*` stale-CAS case was refused by the Python precondition (replacement revision not advancing) before reaching PostgreSQL, so it did not prove the conditional UPDATE | FIXED: the replacement now advances, so the `WHERE job_revision = :expected` UPDATE itself returns 0 rows |
| SR-2 | No test showed CAS under real concurrency (B-07 CAS) | FIXED: new `test_concurrent_cas_lets_exactly_one_writer_win`: the second writer blocks on the uncommitted row and, after the first commit, re-evaluates to 0 rows → `JobRevisionConflict`; stored job = first writer |
| SR-3 | B-03f restarted child process had no exit check or cleanup on timeout | FIXED: result drained first, exit code 0 asserted, process terminated on failure |
| SR-4 | On the race path only, `_replay` still asks the authorization port for READ_JOB inside the write transaction, before any fence hold or write | ACCEPTED, documented: disclosure check only, no mutation and no fence held yet; owner decisions that authorise writes stay outside the write transaction |
| SR-5 | `expire_overdue_attempts`/`run_due_retries` still use Phase A `list_jobs()` scans and unlocked CAS | ACCEPTED, B4 scope (Δ11 targeted sweeps); not exercised on SQL by B3 tests |

No change to production source (`src/`) was needed; the source hashes in the metrics file are
unchanged. Package rebuilt after SR-1..SR-3; §5 hashes are the rebuilt ones. B3 PostgreSQL proofs
are now 37 cases and remain NOT_RUN.
