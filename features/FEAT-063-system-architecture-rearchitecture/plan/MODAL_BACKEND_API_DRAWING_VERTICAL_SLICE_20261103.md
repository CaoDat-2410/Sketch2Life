# Backend API to Modal drawing VLM vertical slice — 2026-11-03

## Status and authorization

- Status: APPROVED / IN PROGRESS for one synthetic, local-dev API-to-Modal integration slice.
- Feature: FEAT-063; canonical requirements remain `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` v2.3-draft.
- Owner authorization: the owner directed “đặt mấy đó đi” after being told that backend-to-worker integration and rebuilding the API were the missing steps.
- This supplements the Modal hosting-wave plan only for the backend API connection and one additional API-triggered drawing-analysis inference. It does not turn any candidate into a production default.

## Objective

Connect the existing synthetic Parent StoryRun API in the backend to the deployed private Modal `analyze-drawing` function using the Modal Python SDK. Send one generated butterfly drawing through the current API, stage its validated bytes and manifest into a unique Modal Volume scratch prefix, call the worker with the path/hash-only envelope, validate the typed result, and return the existing subject-review state.

This is the first required `drawing.analyze` vertical slice. It does not create a generic test endpoint or claim that the other hosted model functions are integrated into product APIs.

## Scope

- Add a backend-owned Modal function adapter for `drawing.analyze`; use the existing model app/function names and environment `dev`.
- Preserve the existing StoryRun loopback-only demo guard, A1 invocation ledger, one-shot run fence, asset ownership/hash checks, idempotency, safe error mapping and adult subject-confirmation gate.
- Upload the validated synthetic image and manifest to `sketch2life-dev-job-scratch-v2` with the Modal SDK. The Modal function receives only the versioned manifest/path/hash envelope. Mount model weights read-only and clean the unique attempt prefix after terminal completion.
- Use the existing local Modal CLI profile only through a read-only mount into an isolated API container. Never read, print, copy into the repository, or include its secret values in evidence. Do not create a new token or Modal Secret.
- Build and run an isolated Compose project on a separate loopback port and isolated named database/volumes. Do not restart, rebuild, migrate, or write to the existing `sketch2life-api-1` or its PostgreSQL database.
- Run focused StoryRun API tests and one real synthetic API-triggered Modal call only after checking the pre-existing Qwen-VL call `fc-01M6GN62XVPDBR39205WQ35K9Q`. If it remains pending or becomes ambiguous, do not dispatch the API inference; finish code/test validation and record the live gate.

## Explicit exclusions

- No real child profile, image, voice, school lesson, or production data; no mobile/client deployment.
- No public Modal web endpoint, new API path, broad provider switch, new credential/token, new Modal Secret, or change to the production authentication boundary.
- No Qwen story/storyboard, ASR, TTS, FLUX, Wan, SAM2, lesson suggestion, video composition, safety model, or video-quota integration in this slice. Existing SRS API contracts remain authoritative for those later stages.
- No fallback GPU, duplicate request after an ambiguous call, output safety claim, SRS/ADR/schema redesign, reset/deletion of existing data, commit, push or merge.

## Acceptance criteria

1. The backend can resolve the deployed Modal function in `dev`, stage a synthetic asset and manifest using Modal Volume v2, and invoke the worker without raw media in function arguments or public HTTP exposure.
2. The isolated rebuilt backend exposes the current loopback-only StoryRun API contract; health/OpenAPI checks pass on its separate local port.
3. When the existing Qwen-VL call is resolved, exactly one HTTP API flow attaches the synthetic drawing and produces the validated adult subject-review state through the deployed `analyze-drawing` function. The Modal call ID, input/output hashes, duration and API state are recorded without secrets or image bytes.
4. Duplicate/idempotent attachment does not dispatch a second inference; invalid hashes, stale run fences, provider failure and unknown outcomes fail closed.
5. Existing API/DB containers and databases remain unchanged; the isolated task database and Compose project are retained for review.
6. Focused tests, `git diff --check`, and `python tools/validate_repository_security.py` pass; all product workload registry entries remain disabled.

## Allowed source paths

- `backend/pyproject.toml`
- `backend/uv.lock` (only to keep the declared Modal SDK dependency locked)
- `backend/Dockerfile` (install the existing `image-admission` extra required by eager runtime imports)
- `backend/src/sketch2life/infrastructure/config/settings.py`
- `backend/src/sketch2life/infrastructure/ai/modal_function_client.py` (new)
- `backend/src/sketch2life/infrastructure/story_run_lite/composition.py`
- `backend/src/sketch2life/infrastructure/story_run_lite/photo_bridge.py`
- `backend/src/sketch2life/interfaces/http/app.py` (only if composition wiring requires it)
- `backend/tests/unit/test_story_run_lite_photo_bridge.py`
- `backend/tests/contract/test_story_run_lite_main_composition.py`
- Additive FEAT-063 plan, approval, context, source-register, status, evidence-index and evidence files for this task.

Any additional runtime/test file requires a demonstrated dependency and an additive plan amendment before editing it.

## Additive plan amendment 1 — dependency lock

- Reason: `backend/pyproject.toml` declares the Modal SDK required by the approved API adapter, and the repository keeps a checked-in `backend/uv.lock` for reproducible installs.
- Added allowed path: `backend/uv.lock`, limited to the dependency graph changes caused by the exact Modal SDK pin.
- No Dockerfile or shared Compose file change is needed: the existing Dockerfile installs the project dependencies from `pyproject.toml`; the isolated test stack uses a temporary Compose override outside the repository.
- This amendment does not change the API contract, worker/model, Modal environment, call limit, data scope, or inference gate.

## Additive plan amendment 2 — runnable backend image

- Reason: the first isolated API container exited at import because `app.py` eagerly imports the PyAV image decoder while the Dockerfile installed only the base package, leaving the existing `image-admission` extra out of the runtime image.
- Added allowed path: `backend/Dockerfile`, limited to installing the already-declared `.[image-admission]` extra in the API image.
- No API or Compose contract changes; no new decoder, provider, model, or dependency pin is introduced.
- This amendment does not open the Modal dispatch gate or permit mutation of the existing Docker stack.

## Additive plan amendment 3 — Windows-host StoryRun API harness

- Reason: StoryRun image admission explicitly requires Windows Job Objects, which are unavailable in the Linux API container. The main-demo database guard also requires PostgreSQL to report loopback address `127.0.0.1` and server port `5433`; a normal Docker bridge port mapping reports the container address/port instead.
- Approved verification setup: install a temporary Python 3.12 runtime and venv under the OS temp directory; run the loopback-only API on `127.0.0.1:8002`; use a separate Compose PostgreSQL service with host networking on `5433` and its own named volume. Keep `STORYRUN_LITE_VISION_MODE=loopback` without an endpoint during route/data setup so no Modal inference can dispatch.
- Existing API, PostgreSQL, Redis and ClamAV containers and their data remain unchanged. The approved live-inference gate remains the pre-existing drawing function call reaching a terminal state.

## Verification sequence

1. Confirm this plan and approval hash; inspect the existing pending Qwen-VL call and isolate local Compose resources.
2. Implement and unit-test the Modal SDK adapter and typed result mapping with a fake function client.
3. Build the isolated API container; verify it has the API routes, health, database isolation and the read-only Modal profile mount, without printing credentials.
4. Run focused StoryRun contract/loopback tests, then one synthetic API-triggered inference only if the pending call has a terminal result.
5. Record all results, remaining gates and cleanup state; run repository security validation. Do not stop or remove the existing Docker stack or database.

## Additive plan amendment 4 — host-network API CRUD verification

- Reason: Docker Desktop host networking exposes the isolated PostgreSQL service at `127.0.0.1:5433` to peer host-network containers, but not to a Windows-host Python process. The Windows-host Alembic/API attempt therefore timed out before opening a database connection. The database itself reports the required `127.0.0.1:5433` identity over TCP inside its host-network namespace.
- Approved fallback: run migrations and a second disposable Linux API container in host networking, using only the isolated `sketch2life` database and loopback API port `8002`. This can exercise database-backed synthetic StoryRun CRUD routes. Keep the original isolated API on port `8001` and every pre-existing project container/database untouched.
- Limitation: Linux does not provide this repository's Windows Job Object image normalizer. Do not bypass image admission or attach an image through this fallback. The new host-network API must use Vision mode `loopback` with no target URL, so it cannot dispatch to Modal.
- The existing approval gate for one API-triggered inference is unchanged: first observe the pre-existing Modal call reaching a terminal status, then use a runtime that can execute the approved image-admission path. No inference is dispatched by this amendment.
- This amendment adds no product source paths, endpoint, auth behavior, provider configuration, credential, model call, data type, or production readiness claim. It authorizes only isolated database migration plus HTTP CRUD verification for the synthetic StoryRun routes.

## Additive plan amendment 5 — Windows-local PostgreSQL for the gated API inference

- Reason: the API CRUD fallback passed, and the pre-existing Modal call is now terminal-success. The actual upload/analysis route still requires the Windows Job Object image normalizer; Windows host networking cannot reach Docker Desktop's host-network PostgreSQL service. The approved API-to-Modal inference must therefore run on Windows with a PostgreSQL server that reports loopback `127.0.0.1:5433`.
- Approved database runtime: use the official EDB PostgreSQL 17.11-4 Windows x64 binaries archive only as a temporary runtime under the OS temp directory, verify its SHA-256 (`b9424ee7bc60b52450ff910a3630225df32e633f3cb29c1d126d9299d59aea28`) before extraction, initialize a new task-owned data directory and database, bind only to `127.0.0.1:5433`, and do not install a Windows service or alter system PATH. The official PostgreSQL Windows page identifies EDB's binary ZIP as the advanced-user option; the EDB installer repository records the archive checksum.
- Run the approved Windows-host Python API on `127.0.0.1:8002`, with the same isolated database, real local ClamAV scan and existing Windows Job Object image-admission path. First create one synthetic run and complete its image upload with the generated `drawing_vlm_synthetic_butterfly.png`; then restart only this task-owned API with `STORYRUN_LITE_VISION_MODE=modal_function` pinned to that run and issue exactly one asset-attachment request.
- Dispatch gate is satisfied by the confirmed terminal-success status of `fc-01M6GN62XVPDBR39205WQ35K9Q`. Keep the no-retry/unknown-outcome fence: if the API-triggered call becomes ambiguous, do not send another request. Record the new call ID and sanitized hashes/state only; do not record bytes, credentials or token values.
- This amendment replaces the inaccessible Windows-to-Docker database path for the single gated inference only. It adds no product code, API contract, provider, database schema, external exposure, or production default. Keep existing Docker resources untouched; all new PostgreSQL files remain in OS temp. Stop only processes started for this task after evidence capture, retaining the task database files for review.

## Additive plan amendment 6 — stop the drawing deployment after the call

- Owner's direct instruction after the API test: “chạy xong nhớ tắt app”.
- After the single API-triggered call reached terminal `success`, stop only the private `sketch2life-srs23-drawing-vlm-dev` app in Modal `dev`. Do not stop the language/audio, FLUX, or video candidate apps, and do not remove shared Volumes or model files.
- The local API had already recorded `VISION_OUTCOME_UNKNOWN` / `AWAITING_RECONCILIATION` before the remote call reached success. Stopping this app does not reconcile or rewrite that StoryRun. Do not retry; retain the task DB and evidence.
- Modal documents `app stop` as terminating app containers and preventing new inputs; the stopped deployment must be redeployed before future use. This amendment authorizes only that owner-requested stop, after the call became terminal; no additional inference or code change is included.
