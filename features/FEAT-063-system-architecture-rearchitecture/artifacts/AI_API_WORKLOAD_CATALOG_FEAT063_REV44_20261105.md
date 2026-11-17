# FEAT-063 AI API and Modal Workload Catalog — Rev44

**Status:** implementation crosswalk; SRS remains draft and unsigned  
**Plan/approval:** Plan Rev44, approval SHA-256 `59C1CC86C59C6BDFEE1E87ACF58A634830EC1DA399A758FCD4D1A35682E73157`  
**Canonical source:** `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`; source checkout baseline at synchronization SHA-256 `7D88057653104A5F3BFD791135DDD22144DEE033FF82928AA6F86775E6FC1AF4`. The current synchronized copy, after the additive Q159/Qwen3.5 amendment in §31.12, has SHA-256 `6BADEBAAD6C28239CA9B759CF17C57A0405D7242B45F3411F40B7E8FEBDC8381`.  
**Role decision:** Platform Admin and Teacher may start new AI lesson/activity/plan suggestions. Parent may edit an authorized existing draft/personal copy, but cannot start new suggestion generation. AI output stays a private draft pending human review. School Manager is not a generation role under this clarification.

## 1. Reading this catalog

The SRS separates client API routes from internal AI jobs. A Modal function is not a public API. Clients must not select a Modal workload, URL, model, GPU, or storage path. The authenticated backend validates actor, tenant/session, consent/grant, revision, opt-in, quota and idempotency, persists a pollable job, then dispatches one allowlisted worker. The worker receives only the corresponding bounded, versioned input and returns a typed result or safe failure.

Status terms:

- **Mounted:** present in the backend application's active OpenAPI.
- **Fixture-only:** present in the isolated StoryRun-lite synthetic app; not a production capability.
- **Worker-only:** private Modal worker exists, but no authenticated product route/job persistence reaches it.
- **Missing:** SRS target has no matching route or use case in this checkout.
- **Blocked:** cannot be safely or truthfully tested yet; reason is stated.
- All rows in `workloads.json` remain `enabled: false`.

## 2. AI workload inventory

| Workload | Purpose and allowed input | Candidate on Modal | Backend API boundary / role | Current implementation and test state |
|---|---|---|---|---|
| `asr.transcribe` | Vietnamese adult idea audio; bounded audio asset only | `Systran/faster-whisper-large-v3@edaa852ec7e145841d8ffdb056a99866b5f0a478` | SRS `POST /v1/story-runs/{id}/idea`; Parent or assigned Teacher. **Missing** in mounted API. | Rev44 worker completed in 31.564s. Paired TTS requested “Con bướm bay qua khu vườn đầy nắng.” but ASR returned “Con đứng bay qua khu vườn đầy nắng.”; execution passed, exact fixture transcription failed. Adult confirmation remains mandatory. |
| `drawing.analyze` | Inspect one validated child drawing and return candidate subject/features plus adult-confirmation requirement | `Qwen/Qwen3.5-9B@c202236235762e1c871ad0ccb60c8ee5ba337b9a` | SRS `POST /v1/story-runs/{id}/assets`; actor of that one-child run. | One Qwen3.5 inference terminated in about 27s with unusable/empty decoded text; no subject was accepted. Source now uses the documented Qwen3.5 image-message form, but that patch was not inference-tested. Fixture API can dispatch; not a production API. |
| `story.generate` | Generate child-centered Vietnamese story text from confirmed subject, approved context and adult idea | Same pinned Qwen3.5-9B | SRS `POST /v1/story-runs/{id}/story-rewrites`; actor of run. | One Rev44 call failed before generation with `MODAL_CONSTRAINED_DECODER_UNAVAILABLE`: LMFE's Transformers adapter imports an obsolete Transformers 4 tokenizer module. A direct LMFE TokenEnforcer adapter is now pinned to 0.11.3 and passed local constrained-token tests plus Modal runtime-import readiness; no inference retry was made. Fixture API is not the complete SRS rewrite contract. |
| `storyboard.generate` | Produce 5–15 ordered scenes, 30–90 seconds, compatible with confirmed script and video policy | Same pinned Qwen3.5-9B | Same story job; not a separate arbitrary client dispatch. | Shares the story call and pre-generation decoder failure. The decoder patch is verified locally and by Modal runtime imports, not by a new Qwen generation. |
| `parent.sketch-guide.generate` | Optional 3–5-step line-art guide from generic topic/difficulty only; no child image/profile; enqueue only after adult turns it on in the drawing session | `black-forest-labs/FLUX.3 Image Klein@09561231f44e41381c461caf53d5452005a60ac9` plus pinned PUP `@a57899549f8f6f64c6c4d88db30827d496ff76d0` | SRS §9.5/§9.6 and §31.5; Parent session. Exact public path is **not specified**. | Current Modal file still executes legacy FLUX.2 code, so it is **not** a FLUX.3 implementation. HF returned HTTP 401 for the pinned FLUX.3 weights and Modal dev has no Hugging Face Secret. **Blocked; no FLUX inference claimed.** |
| `teacher.sketch-deck.generate` | 3–5 ordered line-sketch steps per approved activity; 16:9 deck; approved plan revision only; no child roster/profile/artwork | Same pinned Qwen3.5-9B for text; visuals are a separate workload | SRS `POST /v1/lesson-occurrences/{id}/sketch-decks` route group; assigned Teacher; only if enabled in session. | Rev44 Qwen3.5 worker call succeeded in 40.042s: 5-slide 16:9 Vietnamese DRAFT, four drawing steps, and exactly two approved activity refs. No authenticated Teacher occurrence/deck API or persistent deck/job workflow exists. |
| `lesson.plan.suggest` | Create structured Vietnamese draft from reviewed allowlisted fields only; never raw upload, full extracted text, embedded images, child data or metadata | Same pinned Qwen3.5-9B | SRS §31.4 / Q159; Platform Admin or Teacher may initiate. Parent is edit-only. Exact API path is **not specified**. | One Rev44 call failed before generation with the LMFE/Transformers 5 adapter import error. The compatibility fix passed local contract tests and Modal runtime-import readiness; inference after the fix is unverified. The worker/output adapter is draft-only; no authenticated durable API/job persistence is wired. |
| `lesson.visual.generate` | Optional visual or session slide from an approved lesson/activity revision; preserve provenance and human review | FLUX.3 Image Klein + pinned PUP | SRS FR-PL-14; authorized lesson/session owner. Exact API path is **not specified**. | Current Modal function still runs FLUX.2 code, incompatible with the candidate. Same gated-weight block as Parent Guide; no FLUX.3 output claimed. |
| `drawing.segment` | Optional reversible segmentation of a validated drawing; preserve the source asset and lineage | SAM 2.1 Hiera-Small dev candidate | Internal stage only; no client route. | Prior synthetic call waited 1,800 seconds for `GPU_L4`; no inference/mask. Mark `UNKNOWN_NO_RETRY`; not re-dispatched in this run. OpenCV/Pillow remains the non-AI baseline. |
| `video.scene.generate` | Generate new per-child scene clips from that child’s drawing and confirmed storyboard | SRS target `Lightricks/LTX-2.5@49b093a39c19169a8a81721dcc541e07e945232f` | SRS `POST /v1/story-runs/{id}/video-generations`; actor of run after script confirmation, admission and quota reservation. | Contract-only; no verified LTX-2.5 worker/access. Video testing is deferred per owner’s prior instruction. Wan2.2 is not an accepted substitute. |
| `video.scene.validate` | Check scene continuity/technical safety before composition | Versioned OpenCV checks plus an unselected VLM adapter | Internal video pipeline stage | Contract-only; not invoked while video is deferred. |
| `video.compose` | Deterministic audio/subtitle/scene composition; not an AI model | FFmpeg | Internal worker, never client-selectable | No current product API/job wiring. Not tested in this non-video pass. |
| `tts.narration.generate` | Vietnamese narration audio from an approved script | `pnnbao-ump/VieNeu-TTS-v3-Turbo@61b85e3d937fbbacb387714180e8182823512523` plus `OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX@ceff0d0749bfb3fa2d61149794ec6feef0d1e1ae` | Internal video pipeline stage; script/run scope only | Rev44 worker produced a 184,364-byte Vietnamese WAV in 23.501s. Paired ASR substituted one word; broader pronunciation/timing quality remains unverified. |
| `video.final-safety.validate` | Fail-closed final artifact safety gate | No model/policy implementation selected | Internal video pipeline stage; no direct API | Not implemented or invoked. A generated artifact must not become playable without this gate. |

The official Qwen model card demonstrates `AutoProcessor` with `AutoModelForMultimodalLM` and identifies the task as image-text-to-text. Rev44 uses that loading interface and the pinned immutable revision; this does not approve model quality or production use. See the [Qwen3.5-9B model card](https://huggingface.co/Qwen/Qwen3.5-9B) and [Transformers Qwen3.5 documentation](https://huggingface.co/docs/transformers/main/model_doc/qwen3_5).

FLUX.3 Image Klein requires its separate prompt upsampler; the official Diffusers documentation describes a modular pipeline and the BFL reference says not to use the image model without that upsampler. The current worker is still FLUX.2, so the FLUX.3 candidate is not callable until implementation, gated access and output validation are complete. See [official Diffusers FLUX 3 docs](https://huggingface.co/docs/diffusers/main/en/api/pipelines/flux3) and [BFL reference repository](https://github.com/black-forest-labs/flux-3-image-klein).

### 2.1 Rev45 execution update — 2026-11-05

This addendum supersedes the Rev44 test-state phrases in Section 2; it does not change the API-boundary classification or enable any workload.

| Workload | Rev45 synthetic worker result | Current boundary |
|---|---|---|
| `drawing.analyze` | Qwen3.5 returned a butterfly candidate and visible features in 44.014 s; adult confirmation remains required. | Worker POC only; authenticated durable Parent route remains absent. |
| `story.generate` / `storyboard.generate` | Passed existing parser and lifecycle checks; 5 scenes / 30 seconds in 113.381 s. | Worker POC only; StoryRun-lite is fixture-only and process-local. |
| `teacher.sketch-deck.generate` | Passed as a 5-slide 16:9 DRAFT with 4 drawing steps and 2 approved activity references in 43.464 s. | No authenticated occurrence/deck API or durable job persistence. |
| `lesson.plan.suggest` | Passed `LessonContentInputV1`; one outdoor activity, `age-band-3-6`, `vi-VN`, `draft_only=true`, in 61.636 s. | No authenticated durable suggestion API/job persistence. Platform Admin and Teacher may initiate; Parent remains edit-only. |
| `tts.narration.generate` / `asr.transcribe` | Synthetic WAV generation passed in 19.161 s; Whisper returned the exact Vietnamese fixture text in 23.900 s. | Internal worker POC only; adult review remains required for ASR. |
| `parent.sketch-guide.generate` / `lesson.visual.generate` | Not dispatched: Modal `dev` still has no `sketch2life-dev-huggingface` Secret; the pinned checkpoint previously returned HTTP 401. | Blocked pending owner-managed Modal Secret and checkpoint access. No secret value was read or written. |
| `drawing.segment` | Not re-dispatched. The pinned SAM2 checkpoint is staged, but the last call waited 1,800 s for GPU_L4 scheduling and produced no mask; current GPU availability was not rechecked in Rev45. | Optional and not inference-verified; OpenCV/Pillow remains baseline. |

The decoder regression was caused by LMFE's default ASCII-only alphabet dropping parser state inside Vietnamese JSON strings, which made model EOS appear valid too early. The worker extends the runtime alphabet for Vietnamese/Unicode while retaining all schema, length, semantic, and human-review gates. All production workload switches remain disabled. Full results and call IDs: `../evidence/AI_NONVIDEO_AI_END_TO_END_20261105.md`.

## 3. SRS API target crosswalk

| SRS method/path or route group | Intended purpose and AI stage | Current state / contract gap |
|---|---|---|
| `POST /v1/lesson-occurrences/{id}/documents` | Attach a validated source and start document extraction/filtering | Not mounted. Extraction is not permission to send raw file/full extracted text to a model. |
| `POST /v1/lesson-occurrences/{id}/plan-revisions` | Teacher authors a structured plan revision | Not mounted. This is a human authoring command, not a hidden model-generation call. |
| `POST /v1/lesson-occurrences/{id}/plan-revisions/{revision}/confirm` | Teacher approves the exact safe plan hash | Not mounted; required before deck or occurrence generation. |
| `POST /v1/lesson-occurrences/{id}/sketch-decks` (route group in §9.6) | Generate a deck from approved plan; read current version/status; regenerate one step | No exact final OpenAPI path and no authenticated/durable implementation. Teacher’s session opt-in is mandatory; off means no job, asset or sketch quota. |
| Parent Sketch Guide (route unspecified) | Generate 3–5 line-sketch steps during an opted-in drawing session | No exact route. It must use only generic topic/difficulty, never child profile/artwork. Failure cannot block drawing/capture. |
| Lesson/activity/plan suggestion API (route unspecified) | Start an authorized Qwen3.5 suggestion and return private draft/job refs | No exact route or persistence. Platform Admin/Teacher only; Parent edits an existing authorized copy and cannot start generation. |
| Lesson visual/session slide API (route unspecified) | Optional FLUX visual derived from an approved revision | No exact route/job/asset lifecycle; FLUX.3 worker currently unavailable. |
| `POST /v1/story-runs` | Create one-child run and pin actor/profile/context | Not present in mounted main API or StoryRun-lite subset. |
| `POST /v1/story-runs/{id}/assets` | Validate/attach drawing; optionally start drawing VLM | Fixture-only path exists at `/v1/story-runs/{run_ref}/assets`; returns acceptance and schedules in-process work. No durable queue or production auth. |
| `POST /v1/story-runs/{id}/idea` | Accept text/audio; optionally ASR job | Missing. Current fixture story-generation request accepts text only; no ASR dispatch/API. |
| `POST /v1/story-runs/{id}/subject-confirmation` | Accept/correct VLM candidate; optionally request a new VLM revision | Fixture confirmation route exists, but correction-triggered re-analysis is not the full SRS contract. |
| `POST /v1/story-runs/{id}/context-confirmation` | Pin explicit adult-approved profile context snapshot | Missing. |
| `POST /v1/story-runs/{id}/story-rewrites` | Request bounded Qwen rewrite from an adult suggestion | Missing. Fixture instead exposes `POST /v1/story-runs/{run_ref}/story-revisions`, with a simplified request contract. |
| `POST /v1/story-runs/{id}/script-confirmation` | Human gate on exact script/storyboard hash | Fixture has a story-revision confirmation route with narrower semantics; not equivalent to the full SRS resource. |
| `POST /v1/story-runs/{id}/video-generations` | Admit and enqueue LTX scene pipeline after script confirmation | Missing; intentionally not tested in this pass. |
| `GET /v1/jobs/{job_id}` | Poll authorized, versioned AI job with safe stage/error | Missing. StoryRun-lite polls a revision resource instead; that is not a shared AiJob API. |
| `POST /v1/story-runs/{id}/playback-token` | Issue short-lived playback capability only after all safety gates | Missing; no video readiness is claimed. |

Other §21.2 endpoints for quota, billing, notification, profile and organization workflows are not AI dispatch endpoints. They still require implementation for the full product but are outside this AI-backed route list.

## 4. Mounted backend OpenAPI inventories

### 4.1 Main backend artifact

`artifacts/OPENAPI_FEAT063_REV45_20261101.json` contains **24 operations across 17 path templates**. None directly dispatches an AI model. The 13 Lesson Library operations are CRUD/archive/version plus upload-session lifecycle and source-document reads; extraction/review/AI suggestion is not implemented there.

| Method | Path | Purpose | AI dispatch |
|---|---|---|---|
| GET | `/api/be1/v1/organizations/{organization_id}` | Read organization | No |
| GET | `/api/be1/v1/organizations/{organization_id}/me` | Read caller assignments | No |
| POST | `/api/be1/v1/organizations/{organization_id}/assignments` | Assign organization role | No |
| DELETE | `/api/be1/v1/organizations/{organization_id}/assignments/{assignment_id}` | Revoke assignment | No |
| GET | `/api/be1/v1/organizations/{organization_id}/classes` | List classes | No |
| POST | `/api/be1/v1/organizations/{organization_id}/classes` | Create class | No |
| GET | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles` | List class profiles | No |
| POST | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles` | Create class profile | No |
| POST | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents` | Record consent | No |
| GET | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents` | List consents | No |
| POST | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents/{consent_id}/revoke` | Revoke consent | No |
| POST | `/api/lesson-library/v1/organizations/{organization_id}/lessons` | Create lesson draft | No |
| GET | `/api/lesson-library/v1/organizations/{organization_id}/lessons` | List lessons | No |
| GET | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}` | Read lesson | No |
| PATCH | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}` | Edit lesson draft | No |
| DELETE | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}` | Archive lesson | No |
| POST | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/upload-sessions` | Start source upload | No; extraction/filter not exposed |
| GET | `/api/lesson-library/v1/upload-sessions/{upload_session_id}` | Read upload state | No |
| DELETE | `/api/lesson-library/v1/upload-sessions/{upload_session_id}` | Abort upload | No |
| PUT | `/api/lesson-library/v1/upload-sessions/{upload_session_id}/parts/{part_number}` | Upload source chunk | No |
| POST | `/api/lesson-library/v1/upload-sessions/{upload_session_id}/complete` | Verify and complete source upload | No; must not pass raw file to model |
| GET | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/source-documents/{source_document_id}` | Read source-document metadata | No |
| GET | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/source-documents/{source_document_id}/revisions/{revision_id}` | Read source-document revision | No |
| POST | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/versions` | Create immutable lesson version | No; no suggestion call is wired |

### 4.2 Isolated StoryRun-lite OpenAPI

`backend/src/sketch2life/interfaces/http/story_run_lite_openapi.json` contains **13 operations**. It is an isolated synthetic app, not proof the production FEAT-063 API is complete.

| Method/path | Purpose | AI behavior |
|---|---|---|
| `POST /v1/story-runs` | Create synthetic run | None |
| `GET /v1/story-runs/{run_ref}` | Read run | Poll current fixture run state |
| `POST /v1/story-runs/{run_ref}/assets` | Attach validated drawing | Dispatches drawing VLM via background task |
| `POST /v1/story-runs/{run_ref}/subject-confirmation` | Confirm subject | No fresh VLM retry in current route |
| `POST /v1/story-runs/{run_ref}/cancel` | Cancel run | No model dispatch |
| `POST /v1/upload-sessions` | Start upload | No model dispatch |
| `PUT /v1/upload-sessions/{upload_ref}/parts/{part_no}` | Store upload part | No model dispatch |
| `POST /v1/upload-sessions/{upload_ref}/complete` | Validate completed upload | No model dispatch |
| `GET /v1/upload-sessions/{upload_ref}` | Read upload status | No model dispatch |
| `DELETE /v1/upload-sessions/{upload_ref}` | Abort upload | No model dispatch |
| `POST /v1/story-runs/{run_ref}/story-revisions` | Generate story/storyboard revision | Dispatches Qwen3.5 story worker via background task |
| `GET /v1/story-runs/{run_ref}/story-revisions/{story_revision_ref}` | Read revision | Poll revision, not generic `AiJobStatusV1` |
| `POST /v1/story-runs/{run_ref}/story-revisions/{story_revision_ref}/confirmation` | Confirm exact fixture revision | Human gate |

The two dispatch routes now respond before the Modal call completes and attach work to FastAPI `BackgroundTasks`. This is **process-local, non-durable execution**: a process crash can strand a persisted pending state. Do not treat this as the SRS durable `ai_jobs` queue or expose it as production-ready. The current synthetic API also lacks Firebase role/tenant/consent authorization.

## 5. Priority gaps

1. **P0 — durable job contract:** implement `ai_jobs` persistence, outbox/queue dispatch, authorized `GET /v1/jobs/{job_id}`, idempotent completion/reconciliation and process-restart recovery; the fixture background task is only a responsiveness correction.
2. **P0 — Parent workflow API:** add scoped idea/audio/ASR, context-confirmation, rewrite, script-confirmation, video-admission, completion/delete and playback-token operations from SRS §21.2; keep each command tied to one Child/run and exact immutable revisions.
3. **P0 — Teacher occurrence workflow:** add plan revision/approval, occurrence assignment checks, opt-in deck creation/status/step-regeneration, and projection confirmation. No deck job when the Teacher toggle is off.
4. **P1 — lesson authoring assistance:** add an authenticated Admin/Teacher suggestion API with reviewed allowlist input, durable draft/job persistence, draft-only visibility and human review. Parent can edit authorized copies only.
5. **P1 — Parent Guide:** specify its route contract and session opt-in in OpenAPI; generic topic/difficulty input only; failure must not block drawing.
6. **P1 — FLUX.3 runtime:** replace legacy FLUX.2 handlers, include official prompt upsampler, resolve accepted license + Modal HF Secret, validate step/slide output, and only then run a synthetic generation.
7. **P1 — document filter boundary:** implement deterministic extraction/field mapping + Teacher preview/confirmation before any structured fields reach lesson suggestion; never send original file or full text.
8. **P2 — remaining video stages:** verify LTX-2.5 gated access, scene validation, TTS timing, deterministic composition and selected fail-closed final safety model before any playback API.

## 6. Rules for future API implementation

- Preserve SRS `POST /v1/...` target shapes; the current `/api/lesson-library/v1/...` mounted prefix is an implementation-era route and must be reconciled before product clients depend on it.
- Do not add a public `POST /ai/{workload}` endpoint. Backend chooses a worker from a closed registry.
- Trust verified Firebase principal and server-loaded org/assignment/profile grants only; never accept role/owner/tenant/consent as authority from the request body.
- Require request idempotency and expected revisions for state-changing requests; never retry an ambiguous provider dispatch as a new billable attempt.
- Return a pollable resource/job version with safe stage/error; do not claim HTTP `202` is durable unless its job/outbox receipt is committed before response.
- Keep all AI output private and versioned until the authorized human review/publish gate passes. Never overwrite the original drawing, source lesson, approved revision or historical artifact.
- Feature flags remain off until model, access/license, quality, privacy, quota, safety and durable workflow gates pass.

## 7. Rev44 verification record

All inputs were synthetic. The immutable Qwen pin was `Qwen/Qwen3.5-9B@c202236235762e1c871ad0ccb60c8ee5ba337b9a`. The Modal checkpoint, Transformers 5.22.1 (`AutoModelForMultimodalLM` and `AutoProcessor`), and GPU readiness were confirmed. After fixing the constrained decoder, a CPU-only Modal readiness function verified Transformers 5.22.1, LMFE 0.11.3, `JsonSchemaParser`, `TokenEnforcer`, and the Qwen3.5 loaders. That readiness check loaded no model and performed no inference.

| Workload | Rev44 result | Elapsed | Modal call | Decision |
|---|---|---:|---|---|
| `drawing.analyze` | Failed terminal: unusable/empty decoded output; no candidate accepted | about 27s | `fc-01M6NBS5J15QCCTBEBSS9PMV1P` | Corrected Qwen image-message shape after the attempt; no retry under the approved one-attempt cap |
| `story.generate` + `storyboard.generate` | Failed before text generation: `MODAL_CONSTRAINED_DECODER_UNAVAILABLE` | 26.280s | `fc-01M6NBT067B8Q397JCPWXWQKPM` | Obsolete LMFE Transformers import fixed locally and Modal-import-checked; inference after fix remains unverified |
| `teacher.sketch-deck.generate` | Passed worker contract: 5-slide Vietnamese DRAFT, 4 drawing steps, 2 approved activity refs | 40.042s | `fc-01M6NBTT00BYWZ26Z6NC39GMNW` | Worker POC only; no authenticated durable Teacher API |
| `lesson.plan.suggest` | Failed before generation: `MODAL_CONSTRAINED_DECODER_UNAVAILABLE` | 23.106s | `fc-01M6NBW4AQ6GZZ43R8GN4EGSVB` | Same local/runtime decoder fix; no inference after fix |
| `tts.narration.generate` | Passed WAV generation (184,364 bytes) | 23.501s | `fc-01M6NBWQJB2TP9V7CM3E9PB0KA` | Synthetic sample only |
| `asr.transcribe` | Completed, but one-word mismatch: “bướm” became “đứng” | 31.564s | `fc-01M6NBXHY3BR862BXDWCQX66XJ` | ASR execution succeeded; exact fixture accuracy did not |
| `parent.sketch-guide.generate`, `lesson.visual.generate` | Not dispatched; FLUX.3 weights returned HTTP 401 and no Modal HF Secret exists | n/a | n/a | Blocked; current FLUX file is legacy FLUX.2 and fails closed |
| `drawing.segment` | Prior 1,800s wait ended UNKNOWN while queued for `GPU_L4`; no inference/mask | 1,800s prior attempt | See prior SAM2 evidence | No retry |
| `video.scene.generate`, `video.scene.validate`, `video.compose`, `video.final-safety.validate` | Deferred/not run; owner deferred video and final safety policy is unselected | n/a | n/a | No video or playback claim |

Focused validation: 59 Modal worker/parser tests passed; 79 backend contract/API tests passed and 6 were skipped. Modal decoder readiness, touched-file Ruff, `compileall`, OpenAPI catalog checks, and `git diff --check` are also recorded in the evidence report. A broader Ruff invocation over the entire Modal folder surfaced seven findings in untouched legacy files; these do not affect the touched-file lint result. See `evidence/AI_API_QWEN35_MODAL_VALIDATION_20261105.md` for detailed API gaps and shutdown evidence.

