# StoryRun-lite fresh database recovery diagnosis — 2026-11-03

## Setup and results

At the owner's request, PostgreSQL 17.11 at `127.0.0.1:5433` was used with user/owner `postgres`. Each new task database was created uniquely, its identity verified, `pilot_vision@head` applied, a synthetic legacy Organization asset committed before the StoryRun-lite migration, then only `story_run_lite@head` applied and the fixture verified. No existing database was reset, dropped or modified by this diagnostic.

- `test_recovery_rechecks_expiry_after_wait_on_unfinished_upload_lock`: **PASS**, alone on fresh DB `storyrun_lite_6c0529aa5906470ca3f4`.
- `test_startup_recovery_expires_receiving_and_retries_staging_cleanup`: **PASS**, alone on fresh DB `storyrun_lite_b0e8df89057e4301a456`.
- Nine focused tests then ran separately, each with its own `--basetemp`, on a third new DB `storyrun_lite_421fb54fad6340b4af19`: **7 passed, 2 failed, 0 skipped, 0 timed out**. Both race variants, cancel/complete, expiry boundary and all three expiry lock-wait variants passed. The two recovery cases failed after those earlier cases had used the same DB.
- In focused recovery lock-wait, `core_expired_cleanup_succeeded` was **5**, expected **1**. In focused startup cleanup, `parts_path.exists()` was false after the injected first cleanup failure. The full tracebacks, migration/fixture checkpoints and per-case results are in `STORYRUN_LITE_FRESH_RECOVERY_20261103.log`, SHA-256 `6514640452BC6ABBC136F8CBDA13B3116FCCEFD3DC649AFF013F00C8DD9FA4A0`.

## Analysis and next gate

Both cases pass on isolated initial DB state and fail after other focused tests accumulate rows on a shared DB. `recover_after_restart()` scans database-wide receiving and expired sessions; the test fixture creates a new quarantine directory per test while leaving DB rows. The lock-wait test asserts a global cleanup count of exactly one, and the startup test injects an exception on the first cleanup call without tying it to its own upload. These facts explain how earlier rows can affect the assertions. The tests' dependence on a clean DB is demonstrated; the exact rows processed in the focused failures were not independently enumerated, so their individual identity is not claimed. This result does not establish a production recovery defect or prove production correctness.

The focused gate did not pass. Full PostgreSQL suite, ClamAV/worker and Bruno are **NOT RUN**; Modal invocation count is **0**. A narrow follow-up is to isolate DB state per test or make recovery assertions and injected failures specific to the test's upload while preserving the intended behavioral checks, then rerun the complete suite. This diagnosis did not change source, test or migration; the three new task DBs were retained. No stage, commit, push or merge occurred.
