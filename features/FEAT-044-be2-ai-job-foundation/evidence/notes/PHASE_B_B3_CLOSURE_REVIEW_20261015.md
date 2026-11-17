# BE2-01 B3 closure review —2026-10-15

- Result: **PASS_B3_REPOSITORY_FENCE_SCOPE**, **B3-R01 CLOSED_B3_SCOPE**.
- Independent review: Codex primary, SQL/schema reviewer and test reviewer; runner reviewer
  separately checked the before-proof error. No new backend defect remains from this review.
- Next: **Q01/B4_READY_FOR_IMPLEMENTATION**, B4 code NOT_STARTED. Parent BE2-01 remains
  IN_PROGRESS, exactly14cards/WIP1/full-cardDONE0. Existing Phase B rev3 B1–B6 approval applies.
- Current worktree: `.worktrees/be2-01-ai-job-foundation`, branch
  `feature/be2-01-ai-job-foundation`, base `993a26cae78c0a4fe983033f03881838c886b176` plus dirty
  B2/B3 source. No code, approved plan, approval or runtime package changed during closure.

## Attributable corrected-source execution

The user supplied the full Studio log. Provenance is **USER_REPORTED_REMOTE**, not direct
Codex PostgreSQL/Studio execution. The preceding permission-denied attempt stopped before tests
or delta application; the following successful attempt verified the previous 19-file snapshot,
applied the two-file delta and checked all20correctedsourcehashes before both suites.

| Item | Reported result |
|---|---|
| Run UTC | 2026-10-15T09:27:44Z (16:27:44 Asia/Saigon) |
| Receipt | `evidence/local/b3r01-postgres-20261015/run-20261015T092740Z-454946/` |
| Source transition | `previous_b3_snapshot` → corrected20-file manifest; retry must use corrected state |
| Delta sha256 | `f38dd1fea84b98d6621d98f35b47b19d166c77a05a311e0fbb51a3b146fd6ac1` |
| Corrected manifest sha256 | `0814d514cf75128a80552e313af871a0ceff2758ef2fa8d87a3e4d0b2402dbf8` |
| Executed runner sha256 (local package binding) | `05c5d6415222dd2962120bc2ff8a8747c3d08268e6494cb4caa468ba7659cd1f` |
| ZIP sha256 (local package binding) | `bba2444bfdd070a3f14b225199c99de48d3b7b47e2957b1a1fd2433cbd99a45d` |
| B2+B3 | **71passed/0skip**,60Alembicdeprecationwarnings,63.82s; exit/log0 |
| Test split from matching source | 22offline+49PostgreSQL; PG=39B3(including2newstart/retryregressions)+10B2 |
| Phase A | **224passed/0skip**,5.18s; exit/log0 |
| Default fixture runner | 20PASS/0FAIL,215checks/0failed;215-checkdigestmatchesbaseline; exit/log0 |
| Fixture limit | optional HTTP surface remains `not_run=1`; no new live-router integration claim |
| Final status | `outer_runner_exit=0`, `RUNNER_RESULT=PASS`, `studio_command_exit=0` |

Interpreter/packages reported: Python3.12.15, SQLAlchemy2.1.4, Alembic1.20.0, psycopg3.3.6,
pytest8.4.2. Alembic heads remain `20261014_0004(be1_core)` and `20261015_ai_0001(ai_jobs)`.
Warnings are the existing Alembic missing-path_separator deprecation, not a new failing test.

## B3-R01 closure basis

The unlocked repository read now selects job and labelled attempt columns in **one LEFT JOIN
statement**. That statement has one READ COMMITTED snapshot, so it cannot combine a pre-start/
pre-retry job row with post-commit attempt rows. Attempt ordering and row mapping are preserved.
The locked write path still locks the job row first, then reads attempts; writers mutate the
parent job before attempts. CAS, owner fences, accepted contracts and B2/BE1 history are unchanged.

The two new PostgreSQL regressions create the actual overlap: a writer pauses before commit,
the reader's statement hook releases it, waits for successful commit, checks hook/thread
completion and compares the exact pre-commit aggregate plus valid wire projection. A later read
must show the complete committed start/retry version. Both cases passed on the reported exact
corrected source. Independent reviewers found these checks meaningful and the fix correct.

The original independent offline probe demonstrates the old split-read defect through actual
repository mapping/projection/wire validation with simulated SQL results. Combined with code
review and current real PostgreSQL regressions, this is sufficient to close B3-R01. No new
full-suite rerun or approval gate is required just for the failed optional before-proof below.

## Correction to the optional before-proof label

The helper copied `b3_support.py` into `/tmp/b3r01-before/`, where its `Path(__file__).parents[3]`
assumption fails. Pytest collected0tests and exited2with **IndexError during collection**.
The runner's text "expected non-zero: B3-R01 reproduced" is inaccurate for this attempt.

**Record: NOT_PROVEN_SETUP_ERROR / COLLECTION_ERROR.** Do not count it as two failing regression
assertions, a successful PostgreSQL reproduction of the old bug or proof of the before/after
comparison. This correction overrides the historical runner label and executor expectation.
The valid corrected-source71PASS and PhaseA224PASS are unaffected. Original package bytes are
retained for provenance; the helper is historical and must not be reused as valid before-proof.

For future helper reuse, preserve the real backend path (for example symlink the helper to its
actual location), distinguish pytest assertion failure from collection/setup errors and inspect
both expected regression failures. This is an operator evidence limitation, not a new backend
business card or an obligation to rerun the unchanged71tests.

## Boundary and handoff

B3 closes repository/UoW, Δ1–Δ5 and ASSUMED_CONTRACT owner-fence component checks. Actual P2/P4
integration/sign-off, live routing/provider/model, production policy, B4/B5 queue/worker/effects,
full crash/restart and B6conformance remain future. No whole Phase B or parent-card DONE.

Next Claude work order is ignored
`evidence/local/claude/prompts/CLAUDE_PHASE_B_B4_IMPLEMENTATION_PROMPT.md`. B4 only, existing
approval reused, stop for independent B4 review before B5. No dependency install, service/volume
recreation, BE1-owned logic, FEAT-018/Wan, commit/push/deploy. Prompts/session handover stay local.

Original user log and source-preservation/check receipts are under ignored
`evidence/local/b3r01-studio-closure-20261015/`; public summary metrics accompany this review.
