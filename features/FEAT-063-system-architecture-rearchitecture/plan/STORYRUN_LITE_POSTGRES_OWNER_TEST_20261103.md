# StoryRun-lite PostgreSQL owner test — 2026-11-03

Status: **APPROVED / IN_PROGRESS** by the owner's direct instruction in this thread.

## Scope and acceptance

- Change only `test_goal_database_owner_accepts_loopback_inet_prefix` in `backend/tests/integration/test_story_run_lite_postgres.py`: compare the return of `verify_goal_database_owner()` with both the actual `current_user` and the actual owner of `current_database()`, rather than a fixed role name.
- Preserve the runtime checks for the `storyrun_lite_*` name, loopback address and equality between the connected user and the database owner. Do not change runtime source or migrations.
- Verify on a newly created task-owned loopback PostgreSQL 17 database whose current user and owner are `postgres`. Before the StoryRun-lite migration, apply only its required pilot-vision predecessor branch, commit a synthetic legacy Organization asset, and verify that the StoryRun-lite revision is absent. Then migrate only `story_run_lite@head`, verify the legacy fixture and execute the complete PostgreSQL integration file with a bounded timeout and sanitized output. Do not skip tests to claim success.
- If the suite fails or times out, stop and report. Continue to ClamAV, worker and Bruno only if the PostgreSQL gate passes and the subsequent readiness gates are verified. No Modal, provider, external inference, database reset or deletion, source/migration modification, staging, commit, push or merge.

## Preservation and records

Preserve all existing local changes and previous snapshots. The implementation allowlist is the one test function above; append the owner approval, feature evidence and status, and add a new snapshot. An isolated, loopback-only PostgreSQL cluster and a temporary runner may be used for this task; do not change existing services or databases.
