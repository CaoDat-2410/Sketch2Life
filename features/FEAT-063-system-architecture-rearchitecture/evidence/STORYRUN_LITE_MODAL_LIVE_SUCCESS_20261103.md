# StoryRun-lite one-request Modal live smoke — 2026-11-03

Status: **LIVE FLOW PASS** for one synthetic Parent flow, not a production-readiness or independent-review claim. The supplemental owner-authorized plan is `plan/STORYRUN_LITE_MODAL_DIAGNOSE_CONTRACT_20261103.md`. Earlier reports and snapshots remain historical.

## Diagnosis and port contract

- Prior app `ap-r6Ex8GdPrXPylyESiMzmr7`: Modal function records show the health input enqueued, never started and never assigned a container before the app was stopped. The image build succeeded, the read-only Volume and named Secret were attached, and function configuration requested one L40S. Available CLI data did not establish a queue wait reason, L40S capacity or quota; no cause is asserted.
- A new temporary serve used the task-local archive of committed `a88de875ff92e9b4d4fa5cc2f5f8d5fc1f626f58`, excluding unpublished worktree changes. App `ap-aZM3GSti5OtKPixEcefji2` started a container and GET `/health` returned **200 OK** in 17.8 s client elapsed (Modal log 17.0 s). Different outcome from the previous app does not prove the previous cause.
- `StoryRunLiteRepositoryPort.remove_upload_quarantine` now returns `bool` in its type contract, matching the SQL repository and recovery caller; runtime cleanup behavior was not changed. A focused test checks successful, idempotent and target-only cleanup, plus OSError and QuarantineError failure. Focused tests: **104 passed, 0 skipped**, including bridge/A1, cleanup and worker. Mypy: **Success: no issues found in 3 checked source files** (two live source files plus new test); this is not a whole-repository mypy verdict. Ruff, harness, architecture, repository security and `git diff --check` passed.

## Live gates and result

- Real local ClamAV returned CLEAN for the selected synthetic PNG SHA-256 `030EBBDA7604C0B7235AC6E6BB54894443615376C5F85A09805A68F752D81571` and INFECTED for in-memory EICAR. Worker tests were included in the 104 passed. The retained task-owned PG17 database `storyrun_lite_6f84a04faaac492eb0a7` on `127.0.0.1:5433` was reverified for user/owner `postgres`, expected migration, pre-attach run, matching READY upload and empty ledger; no existing DB was reset.
- A task-local HTTP helper equivalent to the documented Parent route sequence pinned the run in live mode, created an exclusive persistent one-shot marker, and issued one attach through the backend and A1 guard/ledger. This was not a Bruno CLI run. The attach returned **202** in **20.734 s**. GET showed **SUBJECT_REVIEW** and a Vision result, confirm returned **202**, and subsequent GET showed **PREPARATION_REVIEW**.
- Modal function calls and logs show exactly **one POST `/v2/vision`**, **HTTP 200**, typed Vision `SUCCEEDED`, attempt 1, `repair_attempted=True`, two entities; Modal recorded 19.9 s request/execution. The other function input was the successful health GET. One HTTP request does not establish the number of internal model generations; no content or image bytes are recorded here.
- The A1 ledger ended **SUCCEEDED**, `sent_at=2026-11-03T01:50:54.948391+07:00`, `finished_at=2026-11-03T01:51:15.078721+07:00`, result SHA-256 `b11aaf9c7d7a4265dbc224d54b918bdc784903cb49dd26a889c01e32d19485cb`. No retry was sent.
- A later app-specific billing report returned raw `Cost` values L40S `0.04370344`, memory `0.00573748`, CPU `0.00848071`, sum `0.05792163`. The local CLI output did not specify currency; billing may update later, so neither a currency nor a final charge is asserted.

## Cleanup and limits

The temporary app was confirmed stopped at 01:51:34 +07 after the result, along with task API, scanner and helper console; DB and quarantine remain for inspection. No persistent deployment, stage, commit, push or merge occurred. The earlier full PostgreSQL suite result was 12/12; it was not rerun for this type-contract change. The previous full-file test mypy baseline of 24 errors is not claimed resolved.
