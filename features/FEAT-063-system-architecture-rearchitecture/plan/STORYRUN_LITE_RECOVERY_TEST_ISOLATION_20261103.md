# StoryRun-lite recovery test isolation — 2026-11-03

Status: **APPROVED / IN_PROGRESS** by the owner's direct instruction.

## Scope and acceptance

- Modify only the two recovery tests in `backend/tests/integration/test_story_run_lite_postgres.py`. Account exactly for all DB-wide recovery candidates while asserting the state and cleanup of the test-created upload and blocker individually. Inject the first cleanup error only for the test-created upload and prove it is retried and removed. Do not delete unrelated data, remove assertions or weaken behavioral checks.
- Run the two cases individually on fresh task-owned PostgreSQL 17 loopback databases with the synthetic legacy Organization asset committed before StoryRun-lite migration. If both pass, run the nine focused cases in the previously failing order on a fresh task DB, then the complete 12-case suite on another fresh task DB if focused passes. Use unique base temporary directories, per-case watchdogs and sanitized evidence.
- If the suite passes, verify real ClamAV, worker and loopback Vision readiness before Bruno; stop if a runtime change is needed or a readiness gate fails. No Modal, provider, external inference, stage, commit, push, merge, reset or cleanup of existing databases.

## Records and preservation

Append the owner approval and feature evidence/status, and create an additive snapshot. Preserve unrelated local changes and all earlier snapshots. Runtime source and migrations are excluded.
