# Parent Image-to-Script API and AI Retest - 2026-11-03

## Status

APPROVED / IN PROGRESS. This plan authorizes one synthetic Parent flow through image understanding and sample script generation. Video generation is excluded.

## Owner request and objective

The owner requested a retest of the AI/API flow from one drawing through the Parent path, including AI script generation and excluding video. Verify every API used along the path, report failures and missing operations, and preserve the earlier ambiguous run without retrying it.

## Canonical sources reviewed

- `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` is the current FEAT-063 working SRS. Its Parent path places drawing admission and adult subject confirmation before story/script review; video is a later stage.
- `SOURCE_REGISTER.md`, `CONTEXT.md`, and `DECISIONS.md` in FEAT-063 route requirements to that SRS and distinguish direct Modal POCs from backend integration.
- Current API contracts: `backend/src/sketch2life/interfaces/http/routers/story_run_lite.py`, `backend/src/sketch2life/interfaces/http/story_run_lite_openapi.json`, and the corresponding StoryRun-lite DTO/service/domain modules.
- Current worker contracts: `deployment/modal/srs_v23/workloads.json`, `language_audio_app.py`, `drawing_vlm_app.py`, `contracts.py`, and prior POC evidence.
- Prior run and limitation: `evidence/MODAL_BACKEND_API_DRAWING_VERTICAL_SLICE_20261103.md`; previous bounded attempt is unknown to the API and must not be retried or mutated.

## Data and isolation

- Use only the existing generated fixture `evidence/assets/drawing_vlm_synthetic_butterfly.png`, synthetic Parent profile `synthetic-parent-demo`, and synthetic topic `butterfly`. This is not a real child's photo or child data.
- Use a new, task-owned PostgreSQL database and loopback API port `127.0.0.1:8002`; do not reuse the prior run's database state. Preserve all existing project containers, databases, volumes, and data.
- Run upload malware scanning and the Windows image-admission normalizer. Do not bypass either gate.
- Stage media only through the approved private Modal SDK/Volume path. No public endpoint, credential exposure, or production service.

## Approved execution

1. Verify deployment/function state and isolated local prerequisites without printing secrets. Deploy a fresh drawing VLM app only because the prior drawing deployment was stopped. Run task-scoped migrations in the new isolated database and start the synthetic loopback API.
2. Check `/health`, `/openapi.json`, and the current StoryRun/upload-session operations. Record whether a script-generation operation is present.
3. Run the available Parent API path once: create StoryRun; create upload session; upload the fixture; complete and poll upload admission; attach the admitted drawing; poll for adult subject review; confirm the recognized subject; and read the resulting run state. Record each HTTP status, response code/state, ETag/version, correlation ID and elapsed time, omitting secrets and image bytes.
4. After the API's adult subject-confirmation gate, invoke `story.generate` exactly once through the existing private Modal `generate-story-and-storyboard` function, using only the confirmed synthetic topic, Vietnamese, and the worker's fixed five-scene limit. Capture the returned structured story/script for evidence. Do not call a video function.
5. Because the current StoryRun API exposes no script-generation route, report direct worker success separately from API integration. Do not invent or implement an API route in this test-only plan.
6. If either inference has an unknown/ambiguous outcome, do not retry it. Preserve its call ID and state for operator review. No second inference for the same stage/run.
7. Stop task-owned API/PostgreSQL processes and stop the drawing and language/audio Modal apps used for this retest after terminal results, in line with the owner's prior stop-after-run instruction. Retain shared model Volumes and task evidence; do not stop unused FLUX/video apps.

## Explicit exclusions

- All video generation, Wan/LTX inference, video composition, and safety validation.
- Parent line-sketch generation (the input drawing already exists), ASR/TTS (no spoken idea or video narration is requested), FLUX, SAM2, lesson suggestion, and Teacher flows.
- Real child images/profiles/voices, school data, production DB, existing application databases/containers, production enablement, schema/product code changes, adding a missing story endpoint, changing AI model policy, commit, push, or merge.

## Acceptance criteria

- AC1: The isolated API starts and its health/OpenAPI checks pass; all currently exposed Parent StoryRun/upload operations used by the test return documented or captured errors.
- AC2: Fixture upload passes SHA-256, ClamAV, normalization, and persistence gates; no real child data is used.
- AC3: Exactly one API-triggered drawing inference reaches a terminal result and, if successful, the API returns the subject-review state. An ambiguous call remains unretried.
- AC4: Adult subject confirmation reaches the documented next StoryRun state.
- AC5: Exactly one `story.generate` Modal call returns a schema-valid Vietnamese sample story and five-scene storyboard, or its failure is captured. This is direct worker evidence, not a claim that the API has a script-generation operation.
- AC6: Video inference requests equal zero. The final report identifies each tested route's result and the missing/unimplemented script API boundary.
- AC7: Task-owned local processes and the two Modal apps used for this retest are stopped; shared weights, Volumes, previous run and existing project services remain untouched. Evidence and current FEAT-063 records are updated.

## Allowed paths

- `features/FEAT-063-system-architecture-rearchitecture/plan/PARENT_IMAGE_TO_SCRIPT_API_AI_RETEST_20261103.md`
- `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
- Additive task evidence, evidence index, `CONTEXT.md`, `DECISIONS.md`, `SOURCE_REGISTER.md`, and `status/STATUS.md` entries within FEAT-063.
- A task-specific runner/evidence JSON only under `features/FEAT-063-system-architecture-rearchitecture/evidence/scripts/` and `evidence/assets/`.

No backend product source, API contract, database schema, model worker, workload registry, or previous evidence artifact may be changed under this plan.

## Owner-requested cleanup amendment - 2026-11-03

The owner subsequently asked to stop the apps after the simulated Parent flow. This supersedes the narrower cleanup wording in step 7 and AC7 above: after the request reaches a terminal state or is recorded as unknown and evidence is captured, stop every Modal app currently deployed in the `dev` environment: `sketch2life-srs23-drawing-vlm-dev`, `sketch2life-srs23-language-audio-dev`, `sketch2life-srs23-flux-image-dev`, and `sketch2life-srs23-video-candidate-dev`. No FLUX or video inference is authorized by this amendment. Stop deployments only; do not delete app records, shared Volumes, or model files.

## Owner-authorized script-worker fallback - 2026-11-03

The single API-triggered drawing inference returned after 904.056 seconds with `VISION_OUTCOME_UNKNOWN` / `AWAITING_RECONCILIATION` while Modal reported no available L4 capacity. Preserve that StoryRun and do not retry or reconcile it here. To fulfill the owner's explicit request for a sample script while skipping video, allow exactly one detached `story.generate` worker call using the visually verified synthetic fixture topic (`butterfly`), Vietnamese, and the worker's fixed five-scene limit. This is an out-of-band worker test: it does not pass through the unavailable Parent subject-confirmation route and must not be reported as a successful Parent API end-to-end script flow. If its outcome is unknown, do not retry. No video inference.
