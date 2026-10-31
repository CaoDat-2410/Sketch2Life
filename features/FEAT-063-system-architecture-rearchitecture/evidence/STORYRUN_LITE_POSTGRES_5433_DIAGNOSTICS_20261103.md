# StoryRun-lite PostgreSQL diagnostics — 2026-11-03

## Scope and setup

The owner requested diagnosis of three failing or interrupted cases, with no source, test or migration changes. The runner verified the existing task DB `storyrun_lite_e4eb465c9dd34d75be56`, PostgreSQL 17.11 at `127.0.0.1:5433`, connected user and DB owner `postgres`, migration `20261102_story_run_lite`, and the synthetic legacy Organization fixture. The fixture's pre-migration provenance was recorded in `STORYRUN_LITE_POSTGRES_5433_20261103.md`. No DB was reset or deleted.

Each case was run separately with `-vv -x --tb=long` and a unique pytest base temporary directory. The race variants had a 90-second outer watchdog each. The expiry case used `-o faulthandler_timeout=20` and a 75-second outer watchdog. The complete sanitized tracebacks and thread dump are in `STORYRUN_LITE_POSTGRES_5433_DIAGNOSTICS_20261103.log`, SHA-256 `5A30DA4A7C56E13327BFDA007DEF3130ECED8929BD608B178D951B2E7C1EB91E`.

## Observations

- Race `[cancel]`: **FAIL**, 16.08 s. The traceback identifies the unset `finalizer_waiting_for_run` event at test line 792; the outer watchdog did not fire.
- Race `[admission]`: **FAIL**, 15.93 s. The traceback identifies the unset `cancellation_waiting_for_run` event at test line 800; the outer watchdog did not fire.
- Expiry `[get]`: **TIMEOUT**, exit 124 after 75 s. The 20-second thread dump shows the worker waiting in psycopg execution from `repository.py:2200` (`_owned_run`), while the main thread is waiting in `ThreadPoolExecutor.__exit__` at test line 1049. The active test was `test_expiry_uses_utc_time_after_story_run_lock_wait[get]`; no pytest verdict was produced.

## Analysis and limits

The test hooks at lines 741, 751 and 1013 look for `story_runs` in the SQL statement. The runtime table object is `story.runs` (`tables.py:213`); compiling the `_owned_run`-shaped PostgreSQL SELECT with `FOR UPDATE` produces `story.runs` and no `story_runs` substring. This mismatch explains why the hooks do not recognize that query. The two tracebacks confirm the expected coordination events remained unset; they do not establish the correctness of the production race outcomes.

For expiry, the test acquires the row lock before starting the worker and releases it in a `finally` outside the executor context. The thread dump confirms the worker is in the database execute call and the main thread is waiting for executor shutdown. Together with the test's control flow, this supports the lock/executor wait explanation; the dump itself does not expose PostgreSQL's server-side wait event.

A narrow proposed repair is to make the test hooks identify the actual `story.runs` lock query robustly and ensure the holder transaction is released even when an event assertion fails, before waiting for executor shutdown. Apply the same examination to analogous lock-wait variants. Then rerun the affected tests and the full PostgreSQL suite. This is a proposal only: no source, test or migration was edited during diagnosis, and no production correctness verdict is claimed.

Bruno and Modal were not run; the task database was retained. No stage, commit, push or merge occurred.
