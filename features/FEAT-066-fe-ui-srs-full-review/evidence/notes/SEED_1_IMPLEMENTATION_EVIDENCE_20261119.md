# FEAT-066 SEED-1 — implementation evidence (2026-11-19)

Status: **OWNER RUN PASSED — INDEPENDENT REVIEW PENDING.** Not committed.

## 1. Authority and base

- Package: `PLAN_SEED1_S1_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT4_20261118.md` (approved), queue
  order D-066-77.
- Branch `feature/feat066-seed1` (local only), worktree `.worktrees/seed1`, base `03342207`.
- No product module was changed. Every file is inside the package §4 allowlist.

## 2. Files

| # | Path | Kind |
|---|---|---|
| 1 | `backend/tools/seed/__init__.py` | new, empty |
| 2 | `backend/tools/seed/guard.py` | new |
| 3 | `backend/tools/seed/data.py` | new |
| 4 | `backend/tools/seed/s1_core.py` | new |
| 5 | `backend/tests/unit/test_seed_guard.py` | new |
| 6 | `backend/tests/unit/test_seed_data.py` | new |
| 7 | `backend/tests/integration/test_seed_s1_postgres.py` | new, owner-run |
| 8 | `features/FEAT-066-fe-ui-srs-full-review/plan/SEED_RUNBOOK_S1_20261119.md` | new |
| 9 | `features/FEAT-066-fe-ui-srs-full-review/evidence/notes/SEED_1_IMPLEMENTATION_EVIDENCE_20261119.md` | new, this note |

## 3. Implementation notes

- **Guard:** reads only `S2L_SEED_DATABASE_URL`; every refusal is a fixed message raised
  `from None`; `GuardedTarget.__repr__` is redacted. Steps: URL checks, then the runtime
  (`SKETCH2LIFE_DATABASE_URL`, both settings caches cleared, `env` local or test), then an
  engine built from the explicit URL and compared with the target, then the live check:
  database name and database owner only (D-066-78; host and port are enforced client-side,
  because Docker port mapping reports the in-container side).
- **Writer:** one `engine.begin()` transaction; each table is one
  `INSERT … ON CONFLICT (primary key) DO NOTHING RETURNING primary key`, so the new-row count is
  exact. No `DO UPDATE`. A driver error is reported as the table name, the driver error class
  and the constraint name only.
- **Data:** values follow package §3.2. Grants: GR1 L1 v2 ORGANIZATION ACTIVE; GR2 L1 v1
  PARENT_GROUP PENDING_REVIEW; GR3 L2 v1 PRINCIPAL DOWNLOAD REVOKED; GR4 L3 v1 PUBLIC
  PENDING_REVIEW. Expected visibility L1 `SCHOOL`, L2 `PRIVATE`, L3 `SCHOOL`. Runs: P1 has
  COMPLETED, FAILED, DELETE_PENDING and the active INPUT_PROCESSING run; P2 has COMPLETED and the
  active PREPARATION_REVIEW run.
- **Test 7** maps the repository record to `ParentStoryRunResponseV1` field by field, as the
  router's `_response` does, without importing the router.

## 4. Coordinator checks (no database)

Python: the repository's `backend/.venv`, with `PYTHONPATH` pinned to the worktree `src` and
`backend` (import origin checked: both `sketch2life` and `tools.seed` load from the worktree).

| Check | Result |
|---|---|
| `ruff check tools/seed` + the 3 test files | All checks passed (after `ruff format` on the new files) |
| `mypy --explicit-package-bases tools/seed` (`MYPYPATH=src`) | Success: no issues found in 4 source files |
| `pytest` unit tests 5 and 6 (+ test 7 collected) | 91 passed, 8 skipped before D-066-78; 89 passed, 8 skipped after it; see §5.2 for the final count (test 7 skips: `S2L_SEED_DATABASE_URL` unset) |
| `validate_harness.py` | exit 0 |
| `validate_repository_security.py` | exit 0 |
| `validate_architecture.py` | exit 0 |
| `validate_skeleton.py` | exit 1: `active Android app must retain applicationId com.sketch2life.mobile`. Pre-existing on the base and on `dev`; not caused by this task |
| `git add -N` (9 paths) + `git diff --check` | exit 0 (§6) |

## 5. Owner run (pending)

Command file: `tmp/feat066-seed1/OWNER_RUN_SEED1_20261119.txt` (one PowerShell block): guard
only, `alembic upgrade heads` on the fresh seed database, S1 run 1, S1 run 2, test 7. Logs,
exit codes and log hashes are in `tmp/feat066-seed1/owner-run/`. No URL is recorded.

**Result (owner run 3, 2026-11-19, after D-066-78):** target = the `s2l-seed` container
(PostgreSQL 17, published on loopback port 5435, database name contains `seed`).

| Step | Exit | Log SHA-256 |
|---|---|---|
| 0 guard only | 0 (`guard ok`) | `07CEA093503E5033437EC44F51FB7E905A17AA289B6ED01642B31A20E69E5529` |
| 1 `alembic upgrade heads` | 0 | `A376D0CDE88E476D213D7CDD22B35CA30A70B7B72D6A78AA62B72467FA8D31A6` |
| 2 S1 run 1 | 0 | `12E493C72658E824A77CE40615E6EC635AD6A8F183BD2750BF91FC41B201967E` |
| 3 S1 run 2 | 0 | `DFDD0812EAF56440910F4CD69689EB1D7F21EE2BE5077BAFD6602ED2BBF528C4` |
| 4 test 7 | 0 (eight dots, no summary line because `-q` was doubled; no skip or failure mark) | `81850AD9ED5828A6D78588F93E17568B3A1418709F8BEB38CCCDE113FE53C003` |

- Run 1 created exactly `EXPECTED_COUNTS` on all 16 tables (8, 23, 41, 19, 52, 52, 2, 3, 3, 5,
  3, 4, 8, 4, 6, 6), every row `ok yes`.
- Run 2 created 0 rows on every table; the totals stayed equal to `EXPECTED_COUNTS`.
- Test 7 passed: second run adds nothing and counts match; `_recalculate_visibility` parity
  for L1–L3 (rolled back); all six seeded runs read back through `get_run` as their Parent and
  validated through `ParentStoryRunResponseV1`.
- The coordinator scanned all five logs for URL fragments (host, port, user, database name):
  none found.

### 5.1 Earlier attempts (no row written in either)

- Attempt 1: the guard step exited 1 with a Python `SyntaxError` before importing the guard.
  Windows PowerShell 5.1 strips embedded double quotes from native-command arguments; the
  command file now uses single quotes. Log kept in `tmp/feat066-seed1/owner-run-attempt1-syntax/`.
- Attempt 2: the guard refused with `the server port does not match the guarded port` (no URL
  printed). Through Docker port mapping the server reports its in-container port and
  interface address. D-066-78 amended the live check to the database name and owner only;
  coordinator rechecks after the change: ruff and mypy clean, 89 passed and 8 skipped,
  `git diff --check`, security and harness validators exit 0.

### 5.2 Independent review round 1 and fixes

- Reviewer: separate read-only session, Sonnet 5.5, effort high. Report kept locally at
  `tmp/feat066-seed1/review-r1/SEED_1_INDEPENDENT_REVIEW_R1_20261119.md` (14,517 bytes).
  Verdict **PASS WITH NOTES**, 0 P1 / 1 P2 / 3 P3. The reviewer re-verified the five log hashes
  and found no URL fragment in any log.
- F1 (P2, fixed): the runbook §2 and this note §3 still described the removed port/address
  check; both now state the D-066-78 live check.
- F2 (P3, fixed): added guard tests for `[::1]` and `localhost`, for an engine that does not
  match the target, and for `s1_core.main()` returning 2 on a refused target.
- F3 (P3, fixed): the test-7 fixture now restores `SKETCH2LIFE_DATABASE_URL` and clears both
  settings caches on teardown; the runbook says to run that file on its own.
- F4 (P3, fixed): wording of the test-7 row and the unit-test count.
- Coordinator rechecks after the fixes: ruff and mypy clean; 96 passed, 8 skipped;
  `git diff --check` and the security validator exit 0. Test 7 was not re-run after the F3
  fixture change (teardown only; no assertion changed).

## 6. Diff check

`git add -N` on exactly the 9 paths of §2, then `git diff --check`: exit 0, no output. No CR
byte in any new text file. No other path was added.

## 7. Not verified

- Independent evidence review (Sonnet 5.5 high) has not run.
- Signing in as a seeded adult (SD-5, deferred).
