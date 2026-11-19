# FEAT-066 SEED-7a: S7a seed runbook (2026-11-19)

Authority: the SEED-7a implementation approval package, Draft 3
(`PLAN_SEED7A_S7_2A_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT3_20261119.md`), seed design Draft 11 §11.4
item 2a, and the goal v2 program approval. S7a covers S7 item 2a only: one command-made Parent run for
each of P4 and P5. S5 is `NOT_BUILT` (package §2.1), and S7 items 1, 2b and 3 are out of scope.

## 1. What S7a writes

The product's own service methods make the runs: `create_run`, then `confirm_context`. Each Parent
ends with one active run in `INPUT_PROCESSING` with a confirmed context. S7a writes no object, calls
no provider, and consumes no quota.

| Table | Rows added by run 1 |
|---|---|
| `story.runs` | 2 |
| `story.run_inputs` | 2 |
| `story.command_receipts` | 4 (one `CREATE_RUN` and one `CONFIRM_CONTEXT` per Parent) |

`backend/tools/seed/data.py` holds them as `EXPECTED_S7A_COUNTS`. A second run adds nothing: the
decision table finds the confirmed seed run and changes nothing, as long as the runs are still in `INPUT_PROCESSING` (a later stage that advances them makes a replay stop with `S7A_UNEXPECTED_RUN_STATE`).

## 2. Guards, in this order

1. `check_s7a_environment()`, before any settings are read: `STORYRUN_LITE_DATABASE_URL`,
   `STORYRUN_LITE_MODAL_BASE_URL`, `STORYRUN_LITE_MODAL_TOKEN` and `STORYRUN_LITE_MODAL_RUN_ID` must be
   unset; the vision mode is unset or `loopback`; the story mode is unset or `disabled`; a vision
   loopback URL must be a loopback address; no `MODAL_*` variable is set except `MODAL_CONFIG_PATH`;
   the Modal client is not imported. The check then points `MODAL_CONFIG_PATH` at a file that does not
   exist, in a fresh directory under `tmp/seed7a/` (git-ignored).
2. `guarded_engine()`, the S1 database guard (see the S1 runbook §2).
3. `check_no_provider()`, on the resolved settings: AI provider `disabled`, auth provider
   `development`, every Firebase, Lightning and Runpod setting empty, and the scanner host unset or
   loopback.

## 3. Steps (PowerShell, from `backend/` of the worktree, against a fresh seed database)

Set the session variables first: `$env:S2L_SEED_DATABASE_URL` (the seed database URL), `$env:S1A_P_ALEMBIC_DATABASE_URL` (the same URL) and `$env:SKETCH2LIFE_ENV = 'local'`; clear them at the end. Leave every `STORYRUN_LITE_*` provider variable and every `MODAL_*` variable unset.

0. Interpreter and source tree: as step 0 of the S1 runbook §3. Stop unless `sketch2life.__file__` and
   `tools.seed.guard.__file__` are both under this worktree.
1. The database is created outside the seed tools (the seed never creates one). Its name contains
   `seed`; the port is neither 5432 nor 5433.
2. `python -m alembic upgrade heads` on the fresh database, with `S1A_P_ALEMBIC_DATABASE_URL` set
   explicitly (S1 runbook §3).
3. S1: `python -m tools.seed.s1_core` (every row `ok yes`, exit 0).
4. S7a run 1: `python -m tools.seed.s7a_runs`. Every row must say `ok yes`; exit 0. The last line lists
   the two runs as `INPUT_PROCESSING/created`.
5. S7a run 2: the same command. Every `new` value must be 0 and the runs say `kept`.
6. Tests T4 and T5, each file on its own: `python -m pytest tests/integration/test_seed_s1_postgres.py -q`
   and `python -m pytest tests/integration/test_seed_s7a_postgres.py -q`. T5 starts S1 and S7a as
   subprocesses, so the Modal-import check runs in a clean process.

Exit codes of `tools.seed.s7a_runs`: 0 counts match; 1 counts differ; 2 a guard refused; 3 a command
or database failure. Messages carry a fixed code only (for example `S7A_FOREIGN_ACTIVE_RUN`,
`S7A_UNEXPECTED_RUN_STATE`, `S7A_COMMAND_FAILED_<code>`) and never a URL, an ID or content.

## 4. Warnings

- Never `upgrade` a database that is already seeded; re-seed it instead (drop and recreate, then start
  at step 1). A database seeded before SEED-7a is re-seeded, not upgraded.
- The base contains FR-C-08. Never run, on a seed database, the FR-C-08 reconciliation command, its
  lifecycle consumer, an outbox publisher or a sweep runner. The S1 direct-SQL `DELETE_PENDING` run has
  no lifecycle event (design §11.8).
- S7a is not atomic per Parent: two committed transactions (create, then confirm). A crash between them
  leaves an unconfirmed seed run; running S7a again confirms it (decision table row 2).
- S7a uses wall-clock time (the services stamp `now`), unlike S1's fixed seed time. No clock-sensitive
  case is asserted.
- Known base failure, not caused by SEED-7a: `test_runs_read_back_through_the_product[r3]` in the S1
  integration test fails because FR-C-08 returns a lifecycle record for the S1 `DELETE_PENDING` run. The
  design §11.8 seed task will change that case.
