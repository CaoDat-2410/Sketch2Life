# Backend API to Modal drawing VLM vertical slice - 2026-11-03

## Status

**PARTIAL / AWAITING RECONCILIATION:** adapter, isolated migrations, API upload/admission, and exactly one API-triggered Modal call were exercised. The API client timed out and recorded an unknown outcome; Modal later reported that call as terminal `success`, but the API did not receive or persist its result. The StoryRun remains locked for operator review. No second inference was sent.

- Feature plan: `plan/MODAL_BACKEND_API_DRAWING_VERTICAL_SLICE_20261103.md`
- Current cumulative plan SHA-256: `855235EA0B209A8B64699074C6D861734A5AC17CBD82B1E56E42F9FA9039D0F5`
- Approval: `approvals/TASK_APPROVAL.md`, corrected operative record for this vertical slice.
- Requirements source: latest SRS in FEAT-063. The legacy StoryRun-lite contract is the existing local synthetic API surface used for this adapter.

## Implementation

- Added `ModalDrawingFunctionClient` for the private Modal dev function `sketch2life-srs23-drawing-vlm-dev/analyze-drawing` and scratch Volume v2 `sketch2life-dev-job-scratch-v2`.
- The client verifies the admitted drawing hash, re-encodes the bounded input as PNG, stages the image and versioned manifest in a unique attempt prefix, and sends the function only the path/hash/size envelope. It uses one `spawn`/`get` attempt, retains staged inputs when the outcome is unknown, and removes the attempt prefix only after a terminal result.
- Added `ModalFunctionPhotoVisionBridge` and `STORYRUN_LITE_VISION_MODE=modal_function`. It remains run-pinned, synthetic Parent scoped, A1-ledger guarded, and fail-closed; it maps a successful drawing result into the existing adult subject-review state. Legacy HTTP/Lightning bridge behavior is unchanged.
- The Qwen2.5-VL worker does not return calibrated confidence. The legacy DTO requires a numeric value, so the adapter currently stores conservative `0.0`; this is a compatibility placeholder, not a confidence estimate or safety score.
- No public Modal endpoint, new credential, generic AI route, or product workload enablement was added. Workload registry entries remain disabled.

## Isolated runtime and migration

- Existing `sketch2life-api-1`, its PostgreSQL, Redis, and ClamAV containers were left running and untouched.
- Docker Desktop's host-network PostgreSQL was not reachable from a Windows-host process. A separate Docker-host API/DB fallback was used for CRUD checks; a temporary Windows PostgreSQL 17.11 runtime was then extracted under the OS temp directory to meet the strict `127.0.0.1:5433` guard and run the Windows Job Object image-admission code.
- EDB archive: `postgresql-17.11-4-windows-x64-binaries.zip`; SHA-256 verified as `b9424ee7bc60b52450ff910a3630225df32e633f3cb29c1d126d9299d59aea28` before extraction. No service was installed and system PATH was not changed.
- The new PostgreSQL instance listens only on `127.0.0.1:5433`; database/user/owner identity was verified as `sketch2life`/`sketch2life`/`sketch2life`. Its data directory and binaries are in OS temp, separate from every existing database.
- `alembic upgrade heads` succeeded on the isolated database. Applied heads: `20261017_lc_0001`, `20261018_ap_0009`, `20261018_kv_0001`, `20261018_vr_0001`, `20261019_ae_0001`, `20261019_pa_0001`, `20261019_vf_0001`, `20261028_ll_0001`, and `20261103_story_upload_compat`.

## API checks

- Isolated Windows-host API bound to `127.0.0.1:8002`; `/health` returned 200 and `/openapi.json` returned 200 with nine StoryRun/upload-session operations.
- Synthetic run creation returned `201 INPUT_PROCESSING`; upload-session creation returned 201; one raw part returned 200; complete returned 202 and the session reached `READY` after the ClamAV and Windows image-normalization gates.
- Source fixture: generated synthetic butterfly PNG, 3,919 bytes, SHA-256 `4b18777ae70eb429273c1e0ba7189ff005171b9dda88491510d91965aafa07fc`. The staged PNG hash logged by the adapter is `c489d4e8a2d7a10c0daba3c9d9bd87b20babaf321aa5f15d37201392aea04a58`.
- The prior direct Modal call `fc-01M6GN62XVPDBR39205WQ35K9Q` reached terminal `success`, clearing the duplicate-call gate.
- Exactly one API attach request was sent and returned `202 Accepted`. Modal call ID: `fc-01M6GYB9EZHJ4TCPAKFPT20Z7G`. At the API timeout it was pending with no `started_at`; later Modal call history reported terminal `success` (started at `2026-11-03T15:10:43.240775Z`). The API did not collect the result/output hash or duration.
- After the bounded client wait, the StoryRun GET returned `INPUT_PROCESSING`, job `AWAITING_RECONCILIATION`, error `VISION_OUTCOME_UNKNOWN`, action `OPERATOR_REVIEW`, version 4. The bridge emitted `modal_drawing_function_outcome_unknown`. No result/output hash or duration was returned to the API; the staged prefix is retained. No retry was sent.

## Validation

- Focused StoryRun bridge/composition suite: **83 passed**.
- Ruff: passed.
- Mypy on the three changed production modules with `--follow-imports=silent`: passed. Default follow mode also surfaced two errors in unchanged imported files (`image_worker.py` Windows `WinDLL` typing and `repository.py` `pending_receipts` annotation); no whole-repository clean claim is made.
- `git diff --check`: passed. `python tools/validate_repository_security.py`: `REPOSITORY_SECURITY_VALID`, 6,201 publishable files scanned; no absolute machine paths, credentials, or signing keys detected.

## Remaining gate

The remote call `fc-01M6GYB9EZHJ4TCPAKFPT20Z7G` reached Modal terminal `success` after the API recorded `VISION_OUTCOME_UNKNOWN` / `AWAITING_RECONCILIATION`. Its result was not delivered to or persisted by the API. Do not retry or automatically reopen the run; use a separately approved operator reconciliation procedure. The API integration and non-AI route checks passed; end-to-end result delivery and the StoryRun subject-review outcome remain **NOT VERIFIED**.

## Final resource state

- The temporary Windows Uvicorn API and PostgreSQL server were stopped after evidence capture. The EDB archive, extracted binaries, and task database directory remain under OS temp for review.
- The three task-owned Docker API/PostgreSQL containers were stopped; their images and named volumes were retained. No existing `sketch2life-api-1`, PostgreSQL, Redis, or ClamAV container was stopped or changed. Existing API `/health` still returned `ok`.
at the owner's request.
