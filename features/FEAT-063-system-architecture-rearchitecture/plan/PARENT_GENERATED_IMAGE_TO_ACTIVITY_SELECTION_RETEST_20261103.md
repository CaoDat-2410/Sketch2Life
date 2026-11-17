# Parent generated-image and activity-selection retest — 2026-11-03

## Status

APPROVED / COMPLETE (2026-11-04 Asia/Saigon). Test-only synthetic run. No video generation.

## Objective

Generate a new synthetic drawing and run the available Parent image-upload, subject-understanding, adult-confirmation, sample-story, and selectable-activity steps. Record elapsed time and API outcomes. Stop the deployed Modal `dev` apps after evidence is captured.

## Canonical sources

- `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, especially §§6.1–6.2 and 31.5: current FEAT-063 Parent flow and video/activity ordering.
- `SOURCE_REGISTER.md`, `CONTEXT.md`, and `DECISIONS.md` in FEAT-063.
- Current StoryRun-lite contracts and routes: `backend/src/sketch2life/interfaces/http/routers/story_run_lite.py` and `story_run_lite_openapi.json`.
- Existing demo activity-selection route: `backend/src/sketch2life/interfaces/http/routers/supervised_flow.py`, `/v1/sessions/{session_id}/p1/activity-suggestions`, and its request/response schemas.
- Modal worker contracts and prior results: `deployment/modal/srs_v23/` and the previous Parent retest evidence.

## Data, services, and boundaries

- Use one newly generated synthetic childlike butterfly drawing. No real child image, profile, account, voice, or school data.
- Use a fresh task-owned `storyrun_lite_*` PostgreSQL database and loopback StoryRun-lite API on `127.0.0.1:8002`. Preserve previous test databases/runs and project services.
- For the separately exposed activity-list demo API, use the existing HTTP router in an in-process `TestClient` harness with an explicit synthetic deterministic VLM fixture set to the visually verified drawing topic. This avoids sending the image to an unverified non-Modal provider and creates no durable record. The activity list itself is produced by the curated catalog service, not an AI call.
- For StoryRun-lite, run the configured malware scanning, image admission, normalization, and storage gates. The activity API contract harness uses its existing test-only image decoder; do not claim that harness performed ClamAV scanning or production normalization.
- Deploy/call only the Modal drawing VLM and story-generation workers if needed. Keep calls synthetic, private, bounded, and at most once per stage. Never retry an unknown result.
- Do not invoke video, FLUX, SAM2, ASR, TTS, or any video composition/safety worker.

## Execution

1. Generate and visually inspect a new synthetic butterfly drawing; save its provenance, SHA-256, and image under the task evidence directory.
2. Start a fresh owned PostgreSQL test database and StoryRun-lite API. Record startup and API health/route-probe timings.
3. Exercise the available StoryRun-lite Parent operations: create run, create/upload/complete upload session, poll upload readiness, attach the admitted drawing, read the run, and confirm the detected subject if the inference reaches an adult-review state. Record HTTP status, returned state/error, request ID, elapsed milliseconds, and provider call ID where available.
4. If subject confirmation succeeds, invoke the private `story.generate` worker exactly once with the confirmed synthetic topic, Vietnamese, and the worker's fixed scene count. Record output or bounded timeout. Do not claim worker evidence as a Parent API script endpoint: current StoryRun-lite has no script-generation route.
5. Exercise the current `/v1/sessions/{session_id}/p1/activity-suggestions` HTTP route in an in-process TestClient using the same synthetic drawing and a deterministic synthetic VLM fixture set to its visually verified topic. Capture the complete selectable activity list and select one option through the existing context-selection route if returned. Identify this as a separate legacy demo route: it currently exposes suggestions before video and is not integrated with StoryRun-lite. Do not describe it as satisfying the SRS §31.5 post-video ordering or as a live AI result.
6. Record a per-step timing table and exact route coverage, including unavailable or failed routes. Keep video inference count at zero.
7. Stop task-owned API/PostgreSQL processes and every Modal app currently deployed in the `dev` environment: drawing VLM, language/audio, FLUX image, and video candidate. Preserve app records, shared model Volumes, and model files. Do not stop the pre-existing developer API on port 8000 or unrelated project services.
8. Add task-scoped evidence and update FEAT-063 context/source/status records.

## Retry and failure policy

- At most one VLM inference and one story-generation inference for this run.
- A timed-out, detached, or otherwise ambiguous provider call is `UNKNOWN`; preserve its call ID and do not retry.
- If the new drawing or subject is not understood, do not silently substitute a different topic. Record the adult correction/mismatch gate and stop dependent stages.
- If the activity route cannot share the same Parent StoryRun, still report the route test as a separate demo session and document the integration gap.

## Pre-dispatch configuration recovery amendment

- The first isolated StoryRun returned `VISION_ATTEMPT_HOLD` before a durable `pilot_vision.invocation` row existed. Its generated `run_ref` did not match the runtime's pinned Modal run ID, so no Modal function dispatch took place. Preserve this failed run and its evidence; do not mutate or retry it.
- To finish the owner-requested flow, this test may create one replacement synthetic StoryRun in the same task-owned database, read its server-generated `run_ref`, restart only the task-owned API with that exact run ID pinned, then upload and attach the drawing once.
- This setup recovery does not increase the provider-call budget: at most one actual drawing VLM inference and one story-generation inference may be dispatched across the entire task. Record both run-creation attempts and their timings. If the replacement run still cannot reach the provider, stop without another replacement.
- The first failed run is a setup/configuration failure and remains part of the API failure report. No product files, API contracts, or database schema may be changed.

## Acceptance criteria

- AC1: A new ImageGen-produced synthetic drawing is saved with provenance and SHA-256; no real child data is used.
- AC2: Each available Parent upload/API operation is exercised once, with HTTP/result state and elapsed time recorded; admission gates remain enabled.
- AC3: At most one VLM call is dispatched; a terminal result is recorded or an ambiguous result remains unretried.
- AC4: Subject confirmation is exercised only after an adult-review result; exactly one story worker call follows confirmation if available. Video calls equal zero.
- AC5: The current activity-list API route is exercised with the actual generated image uploaded and a deterministic VLM fixture; its complete response and selected option are recorded. The separate-session, non-AI, pre-video boundary is explicit.
- AC6: Evidence contains a step-by-step elapsed-time table, API route inventory, output summary, failures, and limitations.
- AC7: Task-owned local processes and all currently deployed Modal `dev` apps are stopped; shared Volumes/models and pre-existing project services are preserved.

## Final execution record

- AC1: Pass. One new ImageGen synthetic butterfly PNG and matching provenance/hash record are stored in evidence.
- AC2: Pass for available upload/admission and StoryRun routes. The initial run exposed a run-ID pin configuration error before provider dispatch; it was preserved. One replacement run reached `READY`, VLM review, and adult confirmation. `/health` and `/openapi.json` are not registered (404).
- AC3: Pass. Exactly one actual drawing inference was dispatched; Modal terminal status was success and subject `bướm` was persisted. The first run never created a provider invocation.
- AC4: Pass with the worker boundary documented. Adult confirmation reached `PREPARATION_REVIEW`/`SUCCEEDED`; one direct Modal story worker returned five scenes. No Parent REST script endpoint exists. Video calls equal zero.
- AC5: Pass as a separate legacy route demonstration only. It returned one curated catalog activity and accepted selection using a deterministic VLM fixture; it does not verify SRS post-video ordering.
- AC6: Pass. Per-route, Modal queue/execution, and total timings plus output limitations are in the evidence report.
- AC7: Pass. All deployed Modal dev apps are stopped, task API/PostgreSQL ports are closed, and shared Volumes plus pre-existing services remain untouched.
- Content note: the generated story has factual butterfly-lifecycle errors and requires educator review.

## Allowed changes

- This plan and its approval entry.
- Additive files only under `features/FEAT-063-system-architecture-rearchitecture/evidence/`, including task-scoped assets/scripts.
- Additive entries in FEAT-063 `CONTEXT.md`, `DECISIONS.md`, `SOURCE_REGISTER.md`, `evidence/README.md`, and `status/STATUS.md`.

No product/backend API code, OpenAPI contract, database schema, model code, workload registry, previous run/evidence, or production configuration may be changed. The pre-existing API on port 8000 and unrelated project services are left running. No commit, push, or merge is included.
