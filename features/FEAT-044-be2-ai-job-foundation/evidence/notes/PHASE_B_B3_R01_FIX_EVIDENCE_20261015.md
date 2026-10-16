# BE2-01 Phase B B3-R01 fix — coherent aggregate reads

> Superseded local checkpoint: B3-R01 CLOSED_B3_SCOPE; B3 review PASS. See
> PHASE_B_B3_CLOSURE_REVIEW_20261015.md and matching closure metrics for corrected-source
> USER_REPORTED_REMOTE71B2+B3/224PhaseAPASS. The optional before-helper actually failed
> collection (0tests, IndexError, exit2), so its historical expected-nonzero wording below is
> NOT_PROVEN, not a successful reproduction. Local/pre-runtime entries remain historical.

- State: **B3-R01 FIXED_PENDING_RUNTIME_REVIEW**. Finding stays OPEN until the corrected snapshot
  runs on PostgreSQL and is independently reviewed. B3 not closed; B4 NOT_STARTED.
- Date/executor: 2026-10-15, Claude, `.worktrees/be2-01-ai-job-foundation`,
  `feature/be2-01-ai-job-foundation`, HEAD `993a26c`; nothing committed.
- Authorization: existing `approvals/PHASE_B_TASK_APPROVAL.md` (plan rev3 B1–B6); work order
  `plan/CLAUDE_PHASE_B_B3_FIX_PROMPT.md` from review `PHASE_B_B3_CODEX_REVIEW_20261015.md`.
  No new approval/card/plan revision; approvals and approved plan bytes unchanged.
- Preserved: the user-reported Studio run of the previous snapshot (patch `a2e479d5…`, manifest
  `ea5cf57e…`): 69 B2+B3 passed, 0 skipped, all exits 0 — USER_REPORTED_REMOTE. It proves the
  previous tests, not this fix.

## 1. Fix

`backend/src/sketch2life/infrastructure/ai_jobs/sql/repository.py` `SqlAiJobUnitOfWork.get_job`:

- **Unlocked read** (`for_update=False`, status/read paths): job row and attempt rows now come from
  one `SELECT job.*, attempt.* AS attempt__* FROM job LEFT JOIN attempt … ORDER BY attempt_number`.
  One statement = one READ COMMITTED snapshot, so a concurrent start/retry commit is seen either
  completely or not at all. A job row without attempts raises instead of looking "not found".
- **Locked read** (`for_update=True`, every write round): unchanged — `SELECT … FOR UPDATE` on the
  job first, then the attempts. Every aggregate writer (`cas_job`, `insert_job`) writes the job row
  before attempts in the same transaction, so after the lock the attempts read sees the same
  version. A join with `FOR UPDATE` was rejected: under READ COMMITTED the re-checked locked row can
  be newer than the joined rows' snapshot.
- READ COMMITTED, CAS, owner fences, contracts, wire validation, B2 schema and BE1 untouched.

## 2. Regression (PostgreSQL, `requires_postgres`)

`backend/tests/integration/ai_jobs/test_aggregate_reads.py`, two cases:

| Case | Schedule |
|---|---|
| `test_read_overlapping_start_commit_returns_one_coherent_version` | `start_attempt` paused right before commit (holding the job row lock); unlocked reader; an `after_cursor_execute` hook lets the writer commit right after the reader's first statement on `ai_jobs.job` and waits for it |
| `test_read_overlapping_retry_commit_returns_one_coherent_version` | same for `retry_job` (failed_retryable rev3 → queued rev4 + attempt 2) |

Assertions: the reader returns exactly the pre-commit aggregate; its projection validates through
`AsyncJobViewV1.model_validate` (the router path); a fresh read then shows the committed version,
which also validates. With the previous two-statement read the hook commit lands between the
statements, so the first assertion fails (torn aggregate). The reader never waits on the
writer's row lock, so the barrier cannot deadlock; all waits are bounded (30 s) and the writer is
released in `finally`.

## 3. Checks actually run (Windows, `backend/.venv` Py3.12.10, PYTHONPATH/MYPYPATH = worktree src)

| Check | Result | Type |
|---|---|---|
| Phase A 6 suites | 223 passed, 1 skipped (Pillow, live-route) | DIRECT_LOCAL_RUN |
| B2+B3 suite | 22 passed; **49 skipped = NOT_RUN** (39 B3 incl. 2 new + 10 B2 PostgreSQL) | DIRECT_LOCAL_RUN |
| Fixture runner | 20/20, 215 checks, digest `d17f58a3…41f68` unchanged | DIRECT_LOCAL_RUN |
| ruff, mypy strict (src + B3 tests), harness/security/architecture/skeleton, `git diff --check` | exit 0 | DIRECT_LOCAL_RUN |
| After-fix offline probe (reviewer's start schedule replayed on the fixed `get_job`; legit queued/running/failed_retryable/requeued views validate) | 1 statement, coherent pre-commit version | DIRECT_LOCAL_RUN, simulated SQL, not PostgreSQL |
| Runner host-logic simulation (scratch clone, docker stubbed) | previous→corrected, retry, unknown change refused, container failure → FAIL | DIRECT_LOCAL_RUN, no container/test |
| **PostgreSQL regression and full B3 suite on the corrected source** | **NOT_RUN** | — |

Ignored receipts: `evidence/local/b3-r01-fix-20261015/` (suites, probe, simulation, builder,
package self-check). Structured copy: `evidence/metrics/PHASE_B_B3_R01_FIX_CHECKS_20261015.json`.

## 4. Source and package identity

| Item | Previous (Studio now) | Corrected |
|---|---|---|
| repository.py | `f66dfb5d…c111b` | `a6e4815c…34d1d` |
| test_aggregate_reads.py | absent | `474ce2e4…dc9961` (new) |
| manifest | `ea5cf57e…939f` (19 files) | `0814d514…dbf8` (20 files) |

Package (ignored, local): `evidence/local/b3r01-studio-package-20261015/`, builder
`evidence/local/b3-r01-fix-20261015/build_b3r01_package.py`. Previous package directory
`b3-studio-package-20261015/` is kept byte-identical.

| File | sha256 |
|---|---|
| b3r01_delta.patch (2 files, previous → corrected) | `f38dd1fea84b98d6621d98f35b47b19d166c77a05a311e0fbb51a3b146fd6ac1` |
| b3r01_source.sha256 | `0814d514cf75128a80552e313af871a0ceff2758ef2fa8d87a3e4d0b2402dbf8` |
| b3_previous.sha256 (copy of the old manifest) | `ea5cf57e12058f48cbd6ef73b23ca9a8b60b78c374f655ba629623b6b308939f` |
| test_aggregate_reads.py (copy for the before-run) | `474ce2e437aec83fcc672542366331f492d32896cac86a5e429fd878fdfc9961` |
| run_b3r01_on_studio.sh | `05c5d6415222dd2962120bc2ff8a8747c3d08268e6494cb4caa468ba7659cd1f` |
| be2-b3r01-studio-20261015.zip (the five files) | `bba2444bfdd070a3f14b225199c99de48d3b7b47e2957b1a1fd2433cbd99a45d` |

Builder self-check: previous snapshot rebuilt from base blobs + B2 + B3 patches reproduces all 19
`ea5cf57e` hashes; + delta reproduces all 20 corrected hashes; a second delta application is
refused; reverse-check against this worktree exit 0; real index untouched.

Runner contract: accepts only (a) the exact previous snapshot — changed-path set and all 19 hashes
equal `ea5cf57e` — then first runs the new regression against that unchanged source
(informational, expected non-zero = B3-R01 reproduced on PostgreSQL), applies the delta and
re-verifies; or (b) the exact corrected snapshot (retry, verify only). Anything else is refused
without reset/clean. The main container verifies sources before each suite, runs B2+B3 (expected
71 cases), Phase A and the fixture runner, fails on any non-zero exit or skip, and ends with a
summary block that repeats source state/hashes/receipts so a pasted tail is attributable.

## 5. Limits

PostgreSQL proof of the fix and the "before" reproduction are NOT_RUN until the user's run.
B4 dispatch bookkeeping must keep the "job row written/locked before attempts" invariant that the
locked read relies on (or read under the same rule). ASSUMED_CONTRACT owner fence and B-12 limits
from `PHASE_B_B3_REPOSITORY_FENCE_EVIDENCE_20261015.md` still apply. Executor evidence, not review.

## 6. Superseded by the closure review

The user's Studio run of this package is recorded in `PHASE_B_B3_CLOSURE_REVIEW_20261015.md`
(USER_REPORTED_REMOTE, 71 passed/0 skip, Phase A 224 passed/0 skip, RUNNER_RESULT=PASS; B3-R01
CLOSED_B3_SCOPE). The optional before-run in §4 was an executor setup error: the copied
`b3_support.py` resolves `Path(__file__).parents[3]` outside the repository, so pytest collected
0 tests (exit 2, IndexError). Its runner label "expected non-zero: B3-R01 reproduced" is wrong;
record NOT_PROVEN_SETUP_ERROR, as the closure review does.
