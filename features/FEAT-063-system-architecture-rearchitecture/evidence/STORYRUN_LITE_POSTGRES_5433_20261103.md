# StoryRun-lite PostgreSQL suite — loopback port 5433 — 2026-11-03

## Setup

After one authentication failure before creating any database, the owner entered the password locally into a hidden prompt. The runner connected to PostgreSQL 17.11 at `127.0.0.1:5433` as `postgres`, created the uniquely named task database `storyrun_lite_e4eb465c9dd34d75be56` with owner `postgres`, and verified the connected database, owner, user, server address, port and version before migration. It did not modify or reset any pre-existing database or role.

The runner applied `pilot_vision@head` and committed a synthetic legacy Organization asset while the StoryRun revision and typed owner column were absent. It then applied only `story_run_lite@head` and verified revision `20261102_story_run_lite` and the original Organization row with null typed owner ref. Pytest used a unique task-owned base temporary directory and the synthetic asset ref in its environment. No credentials were recorded.

## Result

The complete 12-item PostgreSQL suite was started without selection or skips. At the 600-second watchdog it had reported **5 passed, 2 failed**, and was executing `test_expiry_uses_utc_time_after_story_run_lock_wait[get]`; the remaining **4 were not run**. The watchdog ended the test process tree with exit code `124`; no tests were reported skipped. The fixed owner assertion and both legacy fixture tests passed.

The two reported failures were `test_cancel_and_admission_finalizer_race_serializes_asset_commit[cancel]` and `[admission]`. Pytest was terminated before its failure summary, so no traceback or definitive cause was produced for either failure; the exact blocking statement in the interrupted expiry test is also unknown. The captured output is `STORYRUN_LITE_POSTGRES_5433_20261103_PYTEST.log` in this directory. These results do not constitute a passing suite.

The new task DB remains present, as requested. The test process tree was verified absent after timeout, and the existing PostgreSQL 17 and 18 services remained running. Bruno, ClamAV and worker gates were **NOT RUN** because the PostgreSQL gate failed; Modal invocation count was **0**. Runtime source, tests and migrations were not modified in this attempt; no stage, commit, push or merge occurred.

## Narrow diagnostic proposal

Read-only inspection shows the interrupted `[get]` case holds a row lock while coordinating an executor. A possible hang is an assertion or future timeout causing executor shutdown to wait for a worker that is itself waiting on the lock, while transaction cleanup is outside that executor context. This is an inference, not a demonstrated root cause. A separately authorized diagnostic run can use a fresh task DB, run each failing race case separately with immediate traceback, and use pytest's built-in `faulthandler_timeout` plus a bounded outer watchdog for the interrupted case. Preserve the current task DB and do not change source merely to obtain a green result.