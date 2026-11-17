# GOAL A2 Rev3 — main BE PostgreSQL verification and teardown correction

Date: 2026-11-03
Status: **A2 XONG-CHƯA REVIEW**. Independent review is still required; this is not A2 acceptance or completion.

## Scope and pinned inputs

This continuation handled only A2. B1/B2, Modal, GPU, provider calls, migrations, stage, commit, push, and merge were not performed.

| Input | SHA-256 |
|---|---|
| V4 owner decisions | `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6` |
| A2→B1→B2 sequential goal | `D7DEE2977C5AA28B26FCB117281DE8B23E4D4AA85A42922B8B37752FBDA8752A` |
| A2 Rev3 plan | `0F384549BE15D3BF38AF73287F9C6487D2D5B7AEAA1BFB08D71E18BE7CD2BA91` |
| Main BE DB addendum | `4AFA521E50A91FB6B06D4BB33303AEC3A39021BECEB2A26907964B99EDF15BB7` |
| Main DB scope decision record | `54BDB32FA43A5CC293C294411181B5BF5C5FC7AC21C7C6CAD50C10E52227633B` |
| FEAT-064 approval file at execution | `5426AC3561DC68CDBE20251C52198E784E3B501A829C8BCAF25D96C390ADB495` |

Checkout remained on `feature/feat063-be-foundation`, HEAD `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9`; the index was empty. Fresh pre-test snapshot: `.claude/handoff/snapshots/GA2_A2_DBMAIN_FRESH_20261103T175506/manifest.json`, SHA-256 `41090A2CD764B59ADC52A16F8ECF935D6449E447305CD556761FE95937D2C816`. Its 70 status paths matched the working tree before this task's test-only edit.

## PostgreSQL target and preflight

Under the separately approved A2 main-database addendum, the test target was the existing `sketch2life` database. Read-only checks immediately before database tests confirmed PostgreSQL 17, loopback `127.0.0.1:5433`, current user/database owner `postgres`, and zero other client sessions. The target schema inventory contained 117 expected application tables with no missing/extra table names. Required profile columns/check constraints, all 15 proof-table columns, proof constraints, foreign keys, and scope index were present.

The Alembic source revision `20261031_be1_se_0001` (parent `20261024_0005`) is **not an ancestor of any revision currently recorded in this database**. Its physical schema objects were already present. No Alembic command or migration ran. This database-history/schema discrepancy remains visible for the independent reviewer; no attempt was made to reconcile it.

Read-only row-count baseline before the first focused test: 117 tables, 24 total rows; count-map SHA-256 `3b08a731709bf11b84414cfca57786a095ea187bc6520d7f079b7c9d441d83a9`.

## Reproduced teardown failure and exact-ID correction

The focused PostgreSQL case `test_ga2_real_ai_job_acceptance_holds_both_fences_on_one_connection` was run before editing. Its assertion passed, then fixture teardown failed with `ForeignKeyViolation`: deleting the test-created `ai_jobs.job` was blocked by `fk_attempt_job_id_job` because its `ai_jobs.attempt` row still referenced it. The cleanup transaction rolled back.

The reflected generic cleanup skips `ai_jobs.attempt` because that table has no `organization_id`; it then reached the job row. The failed run left synthetic fixture rows. The all-schema count map changed from 24 to 82 rows (hash `b3da6df4225bf6b1e1b2534b67842987acabb7eb518bfcd91c87e7cc79107aa7`). The exact table-count delta is retained in the snapshot. No row values or identifiers were exported. These rows were not manually cleaned because the scope prohibits cleaning rows left by a prior run.

Only `backend/tests/integration/test_be1_synthetic_pilot_postgres.py` changed relative to the fresh baseline: SHA-256 `4322E2EC0C41366C43FAC1CF2DD5C2E6EF06F9E5037566128D0A1EFCB534F1CF` → `BAF126219995DD2D894EC8BEFB674D02417E546565E7BCE3C43213BD5F6346CE`. The final test-only cleanup records the `job_id` returned by the exact test call and its attempt IDs, deletes each attempt by `(attempt_id, job_id)`, excludes `ai_jobs.job` from the organization scan, and then deletes the exact recorded job ID. It asserts exact deletion counts around the transaction. Existing assertions are unchanged.

An intermediate cleanup draft selected attempts through all jobs in the fixture organization. Before final acceptance runs, that draft was narrowed to the exact captured-ID approach above. The final diff and final test results use only the exact-ID implementation.

## Verification results

All commands below were executed from the backend virtual environment unless noted. The test module's network guard allows loopback only; no provider or external network was called.

| Check | Result | Exit |
|---|---:|---:|
| URL safety predicate | 12 passed, 65 deselected | 0 |
| Focused teardown after exact-ID correction | 1 passed | 0 |
| Full PostgreSQL module after exact-ID correction | 77 passed in 96.49s | 0 |
| T2C/T7b and caller compatibility modules | 89 passed | 0 |
| Pinned offline GA2 runner, 19 unit/contract files | 401 passed, 0 failed, 0 skipped in 5.06s | 0 |
| Ruff check on pinned A2 source/test set | All checks passed | 0 |
| Ruff format check | 9 files already formatted | 0 |
| Strict mypy, 12 A2 source files | 1 existing protocol error at `infrastructure/assistance/harness.py:380` | 1 |
| Strict mypy against saved pre-change harness | Same `InMemoryAiJobStore.transaction()` / `AiJobRepository.transaction()` incompatibility at line 377 | 1 |
| `python tools/validate_harness.py` | `HARNESS_VALID` | 0 |
| `python tools/validate_repository_security.py` | `REPOSITORY_SECURITY_VALID`; 6,382 publishable files scanned | 0 |
| `python tools/validate_architecture.py` | `ARCHITECTURE_VALID` | 0 |
| `git diff --check` | Clean | 0 |

After the exact focused test and final full PostgreSQL module, the all-schema row-count map still contained 117 tables and 82 rows, with no count changes from the post-failure baseline; SHA-256 remained `b3da6df4225bf6b1e1b2534b67842987acabb7eb518bfcd91c87e7cc79107aa7`. Thus the final runs added no further rows. The synthetic rows left by the first failed teardown remain; no manual cleanup was done.

The pinned offline runner was copied byte-for-byte to `.claude/handoff/snapshots/GA2_A2_FINAL_20261103T181341/offline_check.py` (SHA-256 `3A714AB27A926672B7C65A35A17CE0F312E46C914AFFA08C806CFC19E4D184B9`) and run from that new snapshot. The exact test commands/output, database count maps, baseline file copy, code diff, static command records, and checkout manifest are retained in that snapshot. No credential or database URL was copied there.

## Remaining review notes

- Strict mypy remains non-zero, with the same diagnostic in the saved baseline and current harness; no new mypy error was observed.
- The database has the required physical schema but its recorded Alembic heads do not include the synthetic-eligibility source revision. No migration was applied.
- Synthetic rows from the first failed teardown remain in the main BE database by instruction. The final tests preserved the post-failure row-count inventory.
- A2 is **XONG-CHƯA REVIEW**. Independent review is required before the owner may launch B1. B1 and B2 remain unopened.
