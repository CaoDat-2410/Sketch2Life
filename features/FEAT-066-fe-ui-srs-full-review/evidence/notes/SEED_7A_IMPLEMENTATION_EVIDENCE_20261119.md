# SEED-7a implementation evidence, 2026-11-19

Accepted by the goal under the program approval; the final check by the owner is pending.

## Authority and reviews

Package Draft 3 (`plan/PLAN_SEED7A_S7_2A_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT3_20261119.md`). Package reviews, all Sonnet 5.5 high in a separate session: Draft 1 round 1 NOT READY (0 P1, 4 P2, 8 P3); Draft 2 round 2 NOT READY (0, 2, 10); Draft 3 round 3 READY WITH NOTES (0, 0, 6). Implementation review round 1: a fresh non-forked subagent (Sonnet 5.5 high; a session could not be started on that turn), ACCEPTABLE WITH NOTES (0 P1, 0 P2, 7 P3). Applied after that review: the foreign-run check now runs before the state check (P3-2), the Modal test uses `find_spec` instead of importing the client (P3-3), the error test asserts `__suppress_context__` (P3-4), the runbook wording (P3-5). Not applied: P3-1 (a test of the `main()` guard order and exit codes), P3-6 (a pure test of the S1 key sets), P3-7 (T4 unchanged: the S1-scoped-count property is carried by T5 only). These stay as recorded notes.

## What was built

`backend/tools/seed/` data (P4, P5, K4, K5, S7a specs and keys, expected counts 25, 5 and 7, `EXPECTED_S7A_COUNTS`), guard (`check_s7a_environment`, `check_no_provider`), `s1_core.py` (S1 rows counted by primary key), `s7a_runs.py` (new writer); tests T1 `test_seed_data.py`, T2 `test_seed_guard.py`, T3 `test_seed_s7a.py`, T5 `test_seed_s7a_postgres.py`; the S1 runbook update and `SEED_RUNBOOK_S7A_20261119.md`. T4 (`test_seed_s1_postgres.py`) is unchanged. No product module changed. S5 is recorded `NOT_BUILT` (package section 2.1).

## Runs (fresh database `frc08_seed7a_*` on the loopback container; name only)

- Step 0 source-tree check: `sketch2life.__file__` and `tools.seed.guard.__file__` both under the integration worktree: yes.
- `alembic upgrade heads`: exit 0.
- S1 run 1: 16 of 16 tables `ok yes` (adult identities 25, child profiles 5, revisions 7); S1 run 2: 0 new rows.
- S7a run 1: runs 2, run inputs 2, command receipts 4 (all `ok yes`), both runs `INPUT_PROCESSING/created`; S7a run 2: 0 new rows, both `kept`. S7a was run once more after the review fixes: 0 new rows.

## Checks

| Check | Result |
|---|---|
| ruff check and format on the changed files | clean |
| mypy `tools/seed` | clean in `tools/seed`; without `--follow-imports=silent` three pre-existing `no-untyped-def` errors in `parent_story_repository.py` are shown through the new import (not reproduced by the reviewer's run) |
| seed unit tests T1, T2, T3 | pass (139 in the review run) |
| T5 on the seed database | 11 tests pass |
| T4 on the seed database | one failure, `test_runs_read_back_through_the_product[r3]`: FR-C-08 returns a lifecycle record for the S1 `DELETE_PENDING` run; it also fails against the database seeded by the base code; design 11.8 owns that case |
| `pytest tests/unit tests/contract`, clean environment | 83 failing or erroring ids, 0 new against the base list of 83 (collection errors from missing optional packages are in the base list). A first run with the seed variables set showed two extra failures caused by the environment, both passing when rerun without them |
| validators (harness, repository security, architecture), `git diff --check` | exit 0 |
| `validate_skeleton.py` | invalid on the Android `applicationId` rule; no Android path is part of this change |

The untracked BRU-0a files in this worktree belong to the deferred task B2 and are not part of this change.
