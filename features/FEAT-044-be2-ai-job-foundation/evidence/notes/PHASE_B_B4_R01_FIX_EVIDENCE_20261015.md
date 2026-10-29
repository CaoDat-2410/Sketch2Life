# Phase B B4-R01 fix evidence — 2026-10-15

> Codex code/package review PASS; see PHASE_B_B4_R01_CODEX_FIX_REVIEW_20261015.md. Runtime for f1c6834f remains NOT_RUN.
> B4-R01 FIXED_PENDING_RUNTIME_REVIEW; user may now run the reviewed package. B5notstarted.

- Status: **B4-R01 FIXED_PENDING_RUNTIME_REVIEW**. Q01 stays B4_NEEDS_REVISION until the
  corrected source passes a source-bound Studio run and a focused Codex closure review. B5 NOT_STARTED.
- Executor: Claude (backend). Authority: existing Phase B plan rev3 B1–B6 approval
  (approvals/PHASE_B_TASK_APPROVAL.md), Δ11 targeted paged sweeps. No new card or approval.
- Finding: notes/PHASE_B_B4_CODEX_REVIEW_20261015.md, P2 B4-R01. When the oldest `claim_limit`
  due rows stay deferred (for example a missing or stale owner decision), every sweep re-reads the
  same unchanged first page and later healthy rows are never reached.
- Metrics: metrics/PHASE_B_B4_R01_FIX_EVIDENCE_20261015.json. Raw receipts: ignored
  local/b4-r01-fix-20261015/ and package local/b4r01-studio-package-20261015/.

## Behaviour change

`AiJobService._sweep` now walks each sweep with a per-invocation keyset cursor:

- `now` and `claim_limit` are fixed once per invocation. Each page reads in its own short
  transaction and is handled row by row through the existing CAS/lock/fence paths.
- The next page starts strictly after the last row's `(sort time, unique id)`. The loop stops on
  the first page shorter than `claim_limit`. A page longer than the limit raises.
- Sort keys and cursors: due retries `(retry_not_before, job_id)`, overdue running attempts
  `(started_at, job_id)`, unstarted dispatches `(dispatched_at, attempt_id)`. Each matches the
  ORDER BY the query already used.
- The cursor lives only in the invocation. There is no persisted seen marker, scheduler, queue,
  larger LIMIT, full scan or extra state.

Files changed (previous 444cfead manifest hash → new hash):

| File | Change |
|---|---|
| backend/src/sketch2life/application/ports/ai_jobs.py `d588e282→6cd2977b` | `SweepCursor`, `DueJob`, `AttemptDispatch.cursor`; the three UoW sweep queries take `after: SweepCursor \| None = None`; overdue/retry queries return `DueJob` |
| backend/src/sketch2life/application/services/ai_jobs.py `42d5b6b3→8945b351` | keyset `_sweep` loop; the three callers pass `after` |
| backend/src/sketch2life/infrastructure/ai_jobs/fakes.py `6a8984c8→8af1865d` | fake parity: `_keyset_page` sorts by cursor and filters strictly after it |
| backend/src/sketch2life/infrastructure/ai_jobs/sql/repository.py `575f2b33→836d513c` | row-value predicate `(at, key) > (:at, :key)` on the existing ORDER BY columns |
| backend/tests/unit/test_ai_job_b4_dispatch.py `e64101fc→6c6a6c9d` | 5 new fake/service regressions; 1 assertion adapted to `DueJob` |
| backend/tests/integration/ai_jobs/test_dispatch_recovery.py `5da26fee→de09fe89` | 2 new PostgreSQL/Redis regressions; sweep assertions adapted to `DueJob` |

Unchanged: the owner fence, CAS/revision checks, the `FOR UPDATE` job lock and parent-before-attempt
order, rollback, retry policy and backoff, the dispatch profile, RQ identity, domain contracts,
D1–D7 and the schema/migration. Blocked rows are never cancelled; they stay `failed_retryable`
for later sweeps. `retry_job`, `_expire_overdue` and the republish path are untouched.
`recover_unstarted_dispatches` and `expire_overdue_attempts` use the same loop and are covered by
their own paging regressions.

Properties, and where each is proved:

- **Progress across pages:** a deferred full first page no longer hides later rows
  (`test_deferred_first_page_no_longer_starves_later_due_retries`, SQL
  `test_deferred_due_retries_do_not_starve_later_sql_pages`). Several healthy pages are crossed
  (`test_retry_sweep_crosses_several_healthy_pages`).
- **Finite termination:** each cursor is strictly greater than the last, and the rows due at the
  fixed `now` are finite. An all-deferred sweep returns `()`
  (`test_all_deferred_sweep_terminates_and_visits_each_row_once`, SQL second invocation).
- **No duplicates:** each blocked row gets exactly one bounded `retry_job` per invocation (7
  rows, `[2]*7` owner checks = fence check + recheck), and the returned ids are unique.
- **Rows changing between pages are not skipped:** each page re-evaluates the predicate. A row
  cancelled by another actor while an earlier page is being handled is left out with zero owner
  checks, and every other row is still retried (`test_rows_changing_between_pages_are_not_skipped`).
  A row that moves behind the cursor, or becomes due after `now`, belongs to the next invocation.
- **Blocked rows stay safe:** blocked snapshots are byte-for-byte equal before and after, on fakes
  and on SQL. Overdue and unstarted sweeps page past the limit
  (`test_overdue_and_unstarted_sweeps_also_page_past_the_limit`, SQL
  `test_overdue_and_unstarted_sweeps_page_through_sql`).

## Before/after proof (direct local, fakes/service only)

- Codex probe `local/b4-codex-review-20261015/service/probe_retry_page_starvation.py` (51 due
  jobs, claim_limit 50, oldest 50 with the missing-fence decision shape):
  - Before (copy in local/b4-r01-fix-20261015/before/): passes `[[],[],[]]`, healthy job 0 owner
    checks, still `failed_retryable`; a direct retry succeeds.
  - After (local/b4-r01-fix-20261015/after/): passes `[["job_fx0051"],[],[]]`, healthy job 1
    check, `queued` with 2 attempts. Blocked rows are unchanged.
- `local/b4-r01-fix-20261015/before_after.py` rebuilds the exact 444cfead snapshot outside the
  repository from base 993a26c and the five recorded patches, then runs the 5 new service
  regressions on it.
  - On 444cfead: **2 failed / 3 passed**. The failures are the starvation and all-deferred cases.
  - On the fix: **5 passed**.
  - The other 3 passed before because pages that make progress were already re-queried. They are
    guard regressions, not reproductions.
- The PostgreSQL regressions were not run before or after: there is no local PostgreSQL 17.
  **NOT_RUN**, with no PG reproduction claimed.

## Local checks (direct, Windows, root venv; PYTHONPATH/MYPYPATH pinned to this worktree)

| Check | Result |
|---|---|
| Phase A 6 suites | 223 passed, 1 skipped (live-app import needs Pillow, absent locally; see raw phase_a_suites.txt) |
| B2–B4 integration + B3/B4 unit | 40 passed, 64 skipped. The 64 are PostgreSQL/Redis cases, **NOT_RUN locally, not PASS** |
| Fixture runner | exit 0, 20 PASS / 215 checks, digest d17f58a3…, optional HTTP NOT_RUN 1 |
| ruff check / mypy src (16 files) / mypy changed tests (11 files) | PASS |
| validate_harness / repository_security / architecture / skeleton | exit 0 |
| `git diff --check`, CR bytes in the 6 changed files | clean / 0 |
| `ruff format --check` | 4 src files already unformatted at HEAD (including untouched harness.py); not a project gate, not reformatted |

Expected Studio counts for the corrected source: B2–B4 **104** (40 offline + 64 PG/Redis = the
97-case RT01 set + 7 new tests), Phase A **224**, fixture runner exit 0, no skips.

## Package (ignored, local/b4r01-studio-package-20261015/)

| Item | SHA-256 |
|---|---|
| Previous manifest b4_previous.sha256 (= RT01 b4rt01_source.sha256) | 444cfeadd3d7d0d0e1f23663b576270f46692e870fe532071f6cf025ffd9ff01 |
| b4r01_delta.patch (6 files) | 56af4fbd78a8dbcdaa4b9c8916fae8626324df775e396776c75dd55f5e28097b |
| b4r01_source.sha256 (32 files, includes both changed test files) | f1c6834f41dc798fe4475509b7d4b9c8c578ebfd15f34ff07f72f2d4bf24aeb4 |
| run_b4r01_on_studio.sh | c3ef682ff6ba9926951cdc9420e41cfd2c81b611acd17e09fde8ef3ff6d01813 |
| be2-b4r01-studio-20261015.zip (4 members) | a7afd57aec808458cf276c8187111ffa7321b0332af8ce7e3ea0764c22085b62 |

- The runner accepts exactly two source states and refuses anything else without resetting,
  cleaning or overwriting:
  - the 444cfead snapshot, where the delta is checked, applied and re-verified;
  - the corrected f1c6834f snapshot, as a verify-only retry.
- It reverse-checks the delta, uses BE2_TEST_REDIS_HOST=be2-redis, runs B2–B4, Phase A and the
  fixture runner, fails on any skip, prints a summary (including the 5 new B4-R01 test lines) and
  `outer_runner_exit` / `RUNNER_RESULT`, and propagates the container exit.
- Builder self-check (local/b4-r01-fix-20261015/package_checks.json): all PASS.
  - The 444cfead snapshot is rebuilt with all 32 hashes.
  - Previous plus delta equals the new manifest, and a second apply is refused.
  - The worktree reverse check exits 0.
  - ZIP members are byte-identical to the package files.
  - The older B2–B4-RT01 packages (30 files) are unchanged, and the real index is not modified.
- Host simulation (local/b4-r01-fix-20261015/runner_host_verification.json, adapted from the
  Codex RT01 proof): 8/8 PASS. It uses real scratch Git outside the repository and a Docker stub.
  - RT01→R01 apply and corrected retry: exit 0.
  - Docker failure: exit 125 with `RUNNER_RESULT=FAIL`; a verify-only retry then exits 0.
  - Foreign tracked file, foreign untracked file, known-file edit and tampered delta: each is
    refused before Docker with the source untouched.
  - The inner container script passes `bash -n`.
  - The stub runs no inner test, so this is not runtime proof.

## Remaining conditions to close B4

1. Codex reviews this fix and package before the user runs it.
2. The user runs `run_b4r01_on_studio.sh` on Studio (source at 444cfead or the corrected retry).
   Required: 104 B2–B4 passed / 0 skipped, 224 Phase A passed / 0 skipped, fixture runner exit 0,
   every exit 0 and `RUNNER_RESULT=PASS`. Record it as USER_REPORTED_REMOTE.
3. A focused Codex closure review of that runtime result. Only then is B4 CLOSED and B5 eligible.

The earlier RT01 97-pass run and these local tests do not close B4.
No staging, commit, push, deploy, install or service rebuild was done. No secrets, media or real
child data are in the package or logs.
