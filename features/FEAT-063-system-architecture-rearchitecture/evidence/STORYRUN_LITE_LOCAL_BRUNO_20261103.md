# StoryRun-lite local synthetic Bruno flow — 2026-11-03

## ClamAV and fake Vision

The previously used portable scanner was no longer present. At the owner's direction, ClamAV 1.5.4 Windows portable was obtained from the official Cisco-Talos release, SHA-256 `0D9E0228B2674137EA1A2853566C98A0278AD52AB2582C3D6DBD75373848C395`, matching the release digest. `clamd.exe` reported Authenticode `NotSigned`; package digest verification, not an Authenticode signature, is claimed. FreshClam downloaded and tested official signatures: main 63, daily 28172 and bytecode 339.

A task-owned daemon bound only to `127.0.0.1:51855`. The repository `ClamAvScanner` returned **CLEAN** for a synthetic PNG and **INFECTED / CLAMAV_FOUND** for the 68-byte EICAR sample constructed only in memory; a mismatched digest was rejected. An initial probe scanned but then raised `AttributeError` due to the probe reading an incorrect verdict attribute; a subsequent probe with the actual attributes passed. The exact Bruno PNG (161 bytes, 64×48, SHA-256 `621587CAFFEA6BF2F1DD76A4AAE778E7AE94E0821007770E267C113EF9558322`) also returned **CLEAN** for that digest. No EICAR file was persisted.

The owner authorized a temporary Vision fake outside the repo, derived from the V2 success handler in `tests/integration/test_story_run_lite_loopback.py`. It listened only on `127.0.0.1:51811`. A synthetic V2 request returned HTTP 200; the V2 schema and `PhotoVisionBridge._verify_success` accepted the response. This was fake Vision, not a model or provider.

## API and Bruno

Previously verified PostgreSQL suite: **12 passed** before the type-only test fix. Worker synthetic suite: **18 passed** previously, including Windows Job Object and 40 MP checks. Neither entire suite was rerun in this turn.

The first API run used the verified prior test DB. Bruno 01 returned HTTP **409 `ACTIVE_RUN_EXISTS`**, so its other eight selected requests were skipped. That DB and its existing run were preserved. A new unique `storyrun_lite_*` DB was then created on PostgreSQL 17 loopback port 5433, verified for user/owner `postgres`, migrated only through `story_run_lite@head` and dependencies, and checked for revision `20261102_story_run_lite`. The random DB name was printed in the interactive helper console but was not captured in the task log; the DB was retained. The API bound only to `127.0.0.1:8778`.

Bruno CLI 4.3.0 was installed in the task directory after explicit owner permission; the connector could not access the temporary copy and an offline installation attempt lacked a cached dependency. A copy of the collection used unique synthetic idempotency keys and a Pillow-generated synthetic PNG. A temporary GET after confirm was added only to the copy. Fresh-DB results: **9 requests passed, 9 tests passed, 0 skipped**:

| Step | HTTP | Observed state |
|---|---:|---|
| 01 create run | 201 | INPUT_PROCESSING |
| 02 create upload | 201 | RECEIVING |
| 03 upload part | 200 | — |
| 04 complete upload | 202 | PENDING |
| 05 get upload | 200 | READY |
| 06 attach asset | 202 | INPUT_PROCESSING |
| 07 get run | 200 | SUBJECT_REVIEW |
| 08 confirm subject | 202 | PREPARATION_REVIEW |
| GET after confirm | 200 | PREPARATION_REVIEW |

The sanitized request/status/state/test summary for both attempts is `STORYRUN_LITE_LOCAL_BRUNO_20261103.json`, SHA-256 `B866350E44CE917364CBEE721EE42AFCA8C0442026EC005FEE5FA9E837423BC5`. It omits request identifiers and credentials. No real child data or Modal/provider invocation was used.

## Mypy and test-only change

The new `ControlledDateTime.now` diagnostic was addressed in the test by annotating the override and returning its own datetime subclass with the same instant and timezone. An isolated clock probe passed for naive, UTC and UTC+07 inputs including microseconds. The corresponding PostgreSQL recovery test was rerun on its verified task DB: **1 passed**, 0 skipped, no timeout. Mypy 1.20.2 on the integration test now reports **24 errors**, matching the previously identified baseline by message and line, exit 1; mypy is not clean. Ruff passed.

## Cleanup and limits

The API, ClamAV daemon and fake Vision stub created for this turn were stopped, and their three loopback listeners and verified PIDs were absent afterwards. Existing PostgreSQL 17/18 services remained running; task DBs were retained and existing DBs were not reset or deleted. The stub is a local fake; this verifies a synthetic local Parent flow, not live model inference or a full BE database. No stage, commit, push, merge or deploy occurred.
