# StoryRun-lite PostgreSQL test coordination fix — 2026-11-03

Status: **APPROVED / IN_PROGRESS**, by the owner's direct instruction in this thread.

## Scope and acceptance

- Amend only `backend/tests/integration/test_story_run_lite_postgres.py`: identify the real PostgreSQL `story.runs` lock query in all relevant coordination hooks; retain race, expiry and recovery assertions and outcomes.
- Release any transaction or event blocking a worker in an inner `finally` before waiting for `ThreadPoolExecutor` shutdown, including exceptional paths. Do not swallow failures or remove behavioral assertions.
- Run both admission/cancel race variants and all expiry lock-wait and recovery cases separately on the verified task-owned loopback PostgreSQL 17 DB. Use unique test temporary directories, per-case timeout and faulthandler. If focused tests pass, run the full 12-test file without skips on the verified DB with its documented pre-migration synthetic legacy fixture. Report actual pass, fail, skip, timeout and traceback results.
- If PostgreSQL passes, check real ClamAV, worker and loopback Vision stub readiness before Bruno. Stop on a runtime defect, missing readiness, or a needed change outside scope. No Modal, GPU, provider or external inference.

## Boundaries and records

Preserve all existing local changes and snapshots. Do not edit runtime source or migration, reset or modify the A2 or aggregate application DB, or stage, commit, push or merge. Authorized records are this plan, the append-only approval, feature evidence/status and an additive snapshot. Use no real child data.
