# StoryRun-lite PostgreSQL coordination fix — 2026-11-03

## Scope and change

The owner approved the test-only plan `STORYRUN_LITE_POSTGRES_COORDINATION_FIX_20261103.md`. The existing test module now recognizes the PostgreSQL `FROM story.runs ... FOR UPDATE` query. Race coordination events and lock-holder transactions are released in inner `finally` blocks before executor shutdown on failure. Existing behavior assertions remain. Runtime source and migration were not changed.

## Verification

- Ruff `check --no-cache`: **PASS**. Pytest collection: **12 cases**. An offline SQLAlchemy PostgreSQL dialect probe accepted the run lock query and rejected an unlocked run query and an upload-table lock query.
- PostgreSQL 17.11 at `127.0.0.1:5433`, database `storyrun_lite_e4eb465c9dd34d75be56`, user/owner `postgres`, StoryRun revision and synthetic legacy fixture were verified. The fixture's pre-migration provenance is recorded in `STORYRUN_LITE_POSTGRES_5433_20261103.md`.
- Each of nine focused cases had a separate base temporary directory, faulthandler and a 75-second watchdog. **7 passed, 2 failed, 0 skipped, 0 timed out.** Passed: cancel/complete race; admission/cancel race `[cancel]` and `[admission]`; expiry boundary; and lock-wait `[get]`, `[put]`, `[complete]`.
- `test_recovery_rechecks_expiry_after_wait_on_unfinished_upload_lock` failed at `core_sessions_expired == 1`: actual value was **3**. `test_startup_recovery_expires_receiving_and_retries_staging_cleanup` failed because `parts_path.exists()` was false after the injected first cleanup failure. The complete sanitized traces are in `STORYRUN_LITE_POSTGRES_COORDINATION_FIX_20261103.log`, SHA-256 `55FF562160320391A7853D451E6B35AE36E8EEF13CA8405AE9279B037D1E13FD`.
- The reused task DB contains records from earlier runs; their contribution to these recovery failures is a hypothesis, not a proven cause. No existing data was reset or deleted. Further diagnosis on an independently provisioned task DB with correct fixture and isolated initial state is proposed; do not weaken counts or cleanup assertions to force a pass.
- The full 12-test suite and ClamAV/worker/Bruno are **NOT RUN** because the focused gate failed. Modal/provider calls: **0**. No stage, commit, push or merge occurred. PostgreSQL suite and runtime behavior remain unverified.
