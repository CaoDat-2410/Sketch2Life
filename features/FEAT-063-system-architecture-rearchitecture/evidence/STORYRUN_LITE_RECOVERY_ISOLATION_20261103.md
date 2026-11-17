# StoryRun-lite recovery test independence — 2026-11-03

## Change

The owner approved the test-only scope in `plan/STORYRUN_LITE_RECOVERY_TEST_ISOLATION_20261103.md`. The two recovery tests now snapshot the relevant database-wide upload candidates and assert exact resulting counts and cleanup IDs. They separately verify the test-created upload's state, version and cleanup. The injected first cleanup failure is restricted to the test upload, and the test verifies that same upload is retried and its parts and snapshot are removed. Time is fixed during the retry test. Runtime source and migrations were not changed; no unrelated data was deleted.

## PostgreSQL evidence

Four uniquely created databases on PostgreSQL 17.11 `127.0.0.1:5433` were verified with connected user/owner `postgres`. For each, the required pilot branch was migrated, the synthetic legacy Organization asset committed before StoryRun-lite migration, and the row and revision checked after migration.

- Recovery lock-wait alone, DB `storyrun_lite_cfc0f21fbb7c4b36bc54`: **1 passed**, 0 failed, 0 skipped, no timeout.
- Recovery cleanup/retry alone, DB `storyrun_lite_91b6cbb7cbb54e68b7c8`: **1 passed**, 0 failed, 0 skipped, no timeout.
- Nine focused cases in the previously failing order, DB `storyrun_lite_630b04c1975340109a26`: **9 passed**, 0 failed, 0 skipped, no timeout.
- Complete PostgreSQL integration file, separate DB `storyrun_lite_73ff2b1faaa946f186b5`: **12 passed**, 0 failed, 0 skipped in 2.89 seconds; no watchdog timeout.

Per-case pytest base temporary directories and watchdogs were used. The sanitized checkpoint and pytest log is `STORYRUN_LITE_RECOVERY_ISOLATION_20261103.log`, SHA-256 `F3F4603CCE8B42E2E168C646703CC51D29ED42AE940467ED2A48B5DA311297FC`. Task databases were retained; pre-existing databases were not reset or deleted.

## Local flow readiness

- Worker synthetic suite `tests/unit/test_story_run_lite_image_worker.py`: **18 passed**, 0 skipped. It includes Windows Job Object kill-on-close, RAM/CPU limit readback, 40 MP synthetic input and fail-closed branches. Its scanner protocol stub is not real ClamAV evidence.
- ClamAV: **NOT VERIFIED**. `clamd`, `clamdscan`, `clamscan` and `freshclam` were absent from PATH, no Clam-named service was found, and no listener on the checked default port 3310 was found. The current process had no ClamAV host/port configured. These observations do not exclude another installation or port.
- Vision loopback stub: **NOT VERIFIED**. The current process had no loopback URL configured; the only repo stub found was an inline pytest fixture rather than a standalone launcher. The prior goal-owned stub and scanner were recorded as stopped and removed.
- Bruno `01`–`08` and post-confirm GET: **NOT RUN** because the real scanner and Vision stub gates were not verified. No API was started for this flow. Modal/provider calls: **0**.

The PostgreSQL suite is verified for this task; the complete local Parent flow remains blocked pending real ClamAV and a usable repo-described loopback Vision stub. No stage, commit, push or merge occurred.

## Checks after the change

- Ruff `check --no-cache` on the changed integration test: **PASS**. Harness, repository security, architecture and `git diff --check`: **PASS**; Git emitted CRLF normalization notices.
- Mypy on the entire integration test file (`--no-incremental --cache-dir nul`): **FAIL, 25 errors**, chiefly missing annotations and an `Any` return. This is a file-wide result; no clean type-check verdict or claim about the origin of each error is made. Annotation changes are outside the approved narrow scope.