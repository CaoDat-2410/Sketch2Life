# PostgreSQL 17 verification — persisted BE2-07 → BE2-01 → BE2-08 flow

Date: 2026-10-22 (Asia/Saigon)
Result: **PASS — 9 passed, 0 failed, 0 errors, 0 skipped**

## Scope and environment

- Approved scope: `plan/BE2_01_07_08_PERSISTED_VIDEO_SEAM_SCOPE_REV2_DRAFT_20261022.md`, SHA256 `1C199CF6CD1E7C2F2D5981D253256278079D840197CB1B05D304E2620FD2E90D`.
- Test: `backend/tests/integration/be2_cross_lane/test_persisted_video_worker_flow.py` (approved FEAT-057 composition test only).
- Python 3.12.10; PostgreSQL 17.11 on loopback (`localhost:5433`). The test-only credential file remained outside the repository.
- Each test created a fresh random `be2_xlane_...` database, applied only the two existing approved migrations, then dropped the database. A read-only post-run query found no leftover `be2_xlane_...` databases.
- All records/content were synthetic. No provider, Modal, Lightning, HTTP server, deployed service, or runtime was used.

## What passed

The nine cases exercise the exact BE2-07 bundle and source-pin lineage, persisted BE2-01 job plus BE2-08 run submission/start/acceptance, unchanged dispatch envelope through the real `VideoWorker`, authoritative receipt readback and duplicate delivery, fail-closed mismatches for job ID, attempt ID, request pin, staged pin and artifact hash, plus transaction rollback injection at submit/start/accept. These results satisfy the approved scope's bounded P01–P07 evidence.

The initial runs exposed assertion defects in the new test fixture: it looked up staged content by `completion_key` instead of `staging_key`, and counted all outbox kinds together (including audit intents). The fixture was corrected to use the staging key and separately count dispatch/audit/quarantine rows. Added job-ID and attempt-ID mismatch cases to cover the P05 acceptance wording. No production source was changed.

## Reproduction and artifacts

From the worktree root, after loading the external test environment file:

```powershell
backend\.venv\Scripts\python.exe -m pytest backend/tests/integration/be2_cross_lane/test_persisted_video_worker_flow.py -q -rs --junitxml=features/FEAT-057-be2-01-14-offline-integration/evidence/raw/be2-video-lifecycle-20261022/postgres17-integration-final2.xml
```

- [Final pytest log](../raw/be2-video-lifecycle-20261022/postgres17-integration-final2.log), SHA256 `0BF72D5DF337F14F3652F2076FFC7880F53331EA15CCF1A8FB68A89E60AF7E2C`.
- [Final JUnit XML](../raw/be2-video-lifecycle-20261022/postgres17-integration-final2.xml), SHA256 `7FFB20AF163F69C7B4C95D4723253805FD3DF92E9AADCDF4DD6288EF85399214`.
- Test source SHA256: `C18D6FD373F83C617B0FF470DC523C99E3A5EDB5B0D2DF1A040ECC0E6F7E67ED`.
- Machine-readable receipt: `../metrics/BE2_01_07_08_POSTGRESQL17_FLOW_TEST_20261022.json`.
- Repository checks: harness, security, architecture, skeleton, and `git diff --check` all passed.

## Limits and unchanged gates

This verifies the approved persisted lifecycle slice only. Durable source fencing through finalization remains separate and unproven; X01 remains `PARTIAL`. X05d remains `BLOCKED`, X05c/CR09-02 remain `OPEN`, and FEAT-057 / BE2-01–14 are not marked complete. The BE1 handoff remains `NOT_SENT / NOT_READY_FOR_BE1_INTEGRATION`. No approval, card status, or acceptance was changed. Nothing was staged or committed.
