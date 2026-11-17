# StoryRun-lite PostgreSQL owner test — 2026-11-03

## Change and scope

The owner authorized replacing the fixed `storyrun_lite_owner` assertion in `test_goal_database_owner_accepts_loopback_inet_prefix`. The test now compares `verify_goal_database_owner()` with the actual `current_user` and database owner returned by PostgreSQL. The runtime owner, name and loopback checks and migrations were not changed. See `plan/STORYRUN_LITE_POSTGRES_OWNER_TEST_20261103.md` and the matching append-only approval.

## Verification

- Ruff on the changed test: **PASS** with `--no-cache`; the initial ordinary invocation could not write its cache and had no lint verdict.
- Direct production guard checks with mocked database rows: **PASS** for connected `postgres` as owner on `127.0.0.1/32`, rejection of non-owner, non-loopback and wrong DB name, and URL rejection of a non-goal DB or non-loopback host. These checks made no DB connection and do not replace integration tests.
- A separate new PostgreSQL 17.11 cluster used loopback port `62480` and task-owned DB `storyrun_lite_53ee6392d49f431e9006`, with verified user/owner `postgres`. The existing PostgreSQL services and DBs were not used.
- Applied `pilot_vision@head`, committed a synthetic Organization asset while the StoryRun revision and owner column were absent, then applied only `story_run_lite@head`. Verified the new revision and the retained legacy Organization row with null typed owner ref. The original service DBs were not migrated.
- Full PostgreSQL file: **0 passed, 0 failed, 0 skipped, 12 setup errors** in 0.89 s; watchdog 600 s did not fire. Every case failed before test-body execution because pytest could not access its existing default temporary directory (`PermissionError: WinError 5`). The owner assertion and integration behavior therefore remain **NOT VERIFIED**. The complete sanitized pytest output is `STORYRUN_LITE_POSTGRES_OWNER_20261103_PYTEST.log` in this evidence directory.
- The task cluster was stopped after verifying its PID, data directory and port; its data directory was preserved. No database was dropped. Fix proposal: assign pytest a new task-owned `--basetemp` path inside the writable task directory, then rerun on a freshly verified task DB with the same pre-migration fixture; do not modify source to address the environment failure.
- Bruno, ClamAV and worker readiness checks: **NOT RUN** after the failed PostgreSQL gate. Modal invocation count: **0**. No stage, commit, push or merge.

The change is pending independent review and does not claim a green PostgreSQL suite or complete runtime flow.
