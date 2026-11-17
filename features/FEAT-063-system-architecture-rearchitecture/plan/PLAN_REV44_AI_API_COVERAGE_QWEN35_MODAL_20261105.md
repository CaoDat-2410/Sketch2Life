# Plan Rev44 — FEAT-063 AI API coverage and Qwen3.5 Modal alignment

**Approval status:** APPROVED  
**Execution status:** COMPLETE WITH PARTIAL AI RESULTS; API and workload gaps remain explicitly listed in the catalog.  
**Date:** 2026-11-05 (Asia/Saigon)  
**Feature:** FEAT-063 — system architecture rearchitecture

## 1. Owner instruction and source of truth

The owner requested: align the AI flows with the current SRS, use Qwen 3.5 VL, inventory every AI API/workload required by the SRS, implement the missing work that fits the current backend, run API and AI tests, and report failures, contract drift, and business-rule violations. In the follow-up clarification for SRS Q157/Q159, the owner selected **Platform Admin and Teacher may initiate new AI lesson/activity suggestions; Parent may edit an existing draft/personal copy but may not initiate a new suggestion**.

The canonical product source is the owner's current FEAT-063 checkout, not the older SRS copy in this Modal worktree:

- `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`
- Source checkout: the owner's primary FEAT-063 checkout, identified by the repository-relative path above.
- SHA-256 at planning: `7D88057653104A5F3BFD791135DDD22144DEE033FF82928AA6F86775E6FC1AF4`
- Status: SRS v2.3-draft; not signed off.

Before product implementation, synchronize that exact SRS into this feature worktree, then make only additive amendments for the owner clarification and the explicitly dev-only Qwen checkpoint. Do not replace the preserved Q01–Q146/Q147–Q195 history, delete the v2.2 snapshot, or convert this POC into a production model decision.

## 2. Objective

Produce a reviewable, SRS-traceable inventory of all AI-backed API operations and internal Modal workloads; correct current AI contract/business-rule gaps; use the immutable official checkpoint `Qwen/Qwen3.5-9B@c202236235762e1c871ad0ccb60c8ee5ba337b9a` for development VLM/story/deck/lesson-generation tests; wire and test each capability that has a supported domain/API boundary; and label blocked/unimplemented surfaces without returning fabricated success. All product workload switches remain disabled.

## 3. In scope

### 3.1 SRS and API contract

1. Synchronize the latest SRS from the primary checkout using its recorded SHA-256.
2. Record the owner resolution of Q159 and trace it in §31 without changing unrelated requirements:
   - Platform Admin and Teacher may initiate AI lesson/activity/plan suggestions.
   - Parent may edit an existing draft/personal copy through an authorized edit path; Parent cannot start a new suggestion-generation job.
   - Every AI-produced lesson/activity/plan remains a private draft pending human review; no AI output is published automatically.
3. Add a FEAT-063 AI API/workload catalog. For every workload, record the business purpose, public API or internal-only boundary, method/path, request/response contract, role/tenant/session guard, job target kind, worker/model, SRS trace, current mount/implementation state, and test result.
4. Reconcile the catalog against SRS §§6.2–6.3, 9.5–9.6, 21.2, 22, 24–27, 31.4–31.5 and the complete active backend OpenAPI. Do not expose a public generic endpoint that lets clients select arbitrary Modal workload names.

### 3.2 Modal workers and models

1. Replace Qwen2.5 development pins for drawing VLM, story/storyboard, and Teacher Sketch Deck with the pinned Qwen3.5-9B checkpoint. Reuse the same pinned model for new lesson suggestion generation where the structured allowlist and authorized API boundary are implemented.
2. Use an inference/runtime version that officially supports Qwen3.5; do not leave the current Transformers 4.53 pin in a Qwen3.5 worker. Before GPU inference, verify checkpoint marker/revision, required files, runtime import, GPU visibility, and model readiness.
3. Keep the other SRS candidates explicit and versioned: FLUX.3 Image Klein for sketch/lesson visuals; faster-whisper for Vietnamese idea transcription; VieNeu-TTS for Vietnamese narration; SAM2.1 as optional drawing segmentation; LTX-2.5 for per-scene video. Do not silently substitute Wan2.2 for LTX-2.5.
4. Preserve original child artwork; line-sketch uses only generic topic/difficulty. Teacher deck uses approved plan/activity fields and no roster/profile/drawing. Lesson generation receives only reviewed allowlisted fields, never raw upload/extracted full text/images/metadata.
5. Keep scene consistency, final video safety, and any unselected safety model fail-closed. Do not issue playback readiness from a worker that has not passed the existing safety/coverage gate.

### 3.3 Backend APIs and route boundaries

1. Keep current StoryRun-lite API methods and correct any synchronous Modal call that holds the request open while returning `202`; acceptance should enqueue/record a pollable job or return the contractually correct terminal response.
2. Implement additive AI routes only where the existing domain, authorization, persistence, and owner ports can enforce SRS rules. Candidate resource names to reconcile in the catalog include:
   - Parent idea transcription under `POST /v1/story-runs/{id}/idea`.
   - Parent optional generic sketch guide under a Parent/session resource, with no profile/child/artwork/audio input and no job when disabled.
   - Existing drawing-analysis and story/storyboard commands under StoryRun resources.
   - Teacher Sketch Deck generation/status/step regeneration under `/v1/lesson-occurrences/{id}/sketch-decks`.
   - Admin/Teacher AI lesson/activity suggestion as a private draft under the Lesson Library resource; reject Parent generation, and preserve Parent's permitted edit-only path.
   - Optional lesson/activity visual or slide generation under a versioned lesson asset resource with provenance and safety state.
   - Shared job polling under `GET /v1/jobs/{job_id}`, scoped to the owner/tenant.
   - Video generation remains gated by current script hash, quota/cost admission, LTX-2.5 readiness, scene/technical validation, TTS/subtitle completion, and final safety. It must not dispatch on a rejected/unknown admission.
3. SRS §21.2 operations for context confirmation, rewrites, exact script confirmation, unsuitable-video handling, completion, deletion, playback-token issuance, and the complete StoryRun read model must be individually classified as mounted, implemented, or missing. Do not claim they are present merely because a related StoryRun-lite route exists.
4. Preserve current route prefixes and DTOs unless a documented SRS conflict requires an additive compatibility change. Any new public operation needs strict versioned request/response schemas, auth/role/tenant scope, idempotency for state-changing commands, safe error codes, and OpenAPI coverage.

## 4. Required workload inventory

The catalog and test report must cover these workload IDs separately, even when one worker implements more than one stage:

1. `asr.transcribe`
2. `drawing.analyze`
3. `story.generate`
4. `storyboard.generate`
5. `parent.sketch-guide.generate`
6. `teacher.sketch-deck.generate`
7. `lesson.plan.suggest`
8. `lesson.visual.generate`
9. `drawing.segment` (optional; preserve reversible/source lineage)
10. `video.scene.generate` (LTX-2.5 candidate only)
11. `video.scene.validate`
12. `tts.narration.generate`
13. `video.final-safety.validate`
14. `video.compose` is deterministic FFmpeg, not an AI workload, but must be listed as a pipeline stage.

The AI API surface and internal workload list are distinct. VLM/ASR/story/scene/TTS/safety worker calls are internal stages unless a domain route explicitly triggers them. No direct Modal URLs or credentials are added to clients.

## 5. Verification and operational boundaries

1. Run relevant API, DTO/parser/business-rule, OpenAPI parity, Modal worker-contract and repository-security checks. The owner explicitly requested API and AI tests.
2. Use only generated/synthetic fixtures; never use real child photos, profiles, voices, lessons, or credentials.
3. For each Modal model, deploy the task-owned `dev` app, verify `/health`/model readiness and immutable checkpoint files first, then make at most one inference attempt per workload. No retry after an unknown/ambiguous outcome. Keep per-request waits bounded; for GPU jobs inspect queue/readiness before dispatch and stop at the approved cap.
4. Do not mark an AI workload passed from parser-only tests, a prior model run, a fixture adapter, or an HTTP `202` without a terminal worker result.
5. Run the SRS video path only if the LTX-2.5 checkpoint/license and Modal resources are available. If gated/inaccessible, record the precise blocker and keep video disabled; do not substitute Wan or report a video pass.
6. After testing, stop only task-owned Modal apps and containers, verify zero task-owned tasks, and preserve shared Volumes and services. Do not change actual `.env`, create provider tokens, enable production flags, commit, or push.

## 6. Acceptance criteria

- **AC-44.1:** The exact current FEAT-063 SRS copy is synchronized and its SHA-256 is recorded in the catalog/evidence.
- **AC-44.2:** Q159 is resolved exactly as the owner stated and all conflicting open-question/role text is reconciled additively.
- **AC-44.3:** Every workload in §4 has one catalog row and an honest status; every AI-triggering API in the mounted backend OpenAPI and every SRS target API in §21.2 is accounted for.
- **AC-44.4:** No raw lesson upload or child/profile data reaches lesson suggestion, Parent guide, or Teacher deck generation beyond the exact SRS-authorized input fields.
- **AC-44.5:** Parent cannot start a new lesson/activity suggestion; Platform Admin and Teacher can start authorized suggestions; generation output remains draft-only.
- **AC-44.6:** Qwen worker configuration pins `Qwen/Qwen3.5-9B` to the recorded immutable revision, loads through a compatible runtime, and returns only contract-valid outputs or a safe failure.
- **AC-44.7:** Each callable AI worker/API receives one bounded synthetic test or is marked BLOCKED with concrete reason; outcomes include timing, HTTP/job state, model revision, and shutdown evidence.
- **AC-44.8:** No unavailable/unselected video safety stage is represented as passed; video remains non-playable unless every required gate passes.
- **AC-44.9:** Focused tests/OpenAPI checks pass or failures are listed with exact identifiers; security validator passes before any future commit/push.
- **AC-44.10:** Final FEAT-063 context, decision, source register, evidence index, and status record the result and limits. No production workload is enabled.

## 7. Allowed paths

The approved implementation/evidence set is limited to these paths; additions require an amended plan and approval record.

### Authority and plan

- `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV44_AI_API_COVERAGE_QWEN35_MODAL_20261105.md`
- `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/AI_API_WORKLOAD_CATALOG_FEAT063_REV44_20261105.md`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/openapi.json`

### Modal worker implementation

- `deployment/modal/srs_v23/contracts.py`
- `deployment/modal/srs_v23/drawing_vlm_app.py`
- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/flux_image_app.py`
- `deployment/modal/srs_v23/drawing_segment_app.py`
- `deployment/modal/srs_v23/video_app.py`
- `deployment/modal/srs_v23/workloads.json`
- `deployment/modal/srs_v23/README.md`
- `deployment/modal/srs_v23/tests/`

### Backend contracts, adapters, API and tests

- `backend/src/sketch2life/contracts/schemas/`
- `backend/src/sketch2life/application/ports/`
- `backend/src/sketch2life/application/services/story_run_lite.py`
- `backend/src/sketch2life/infrastructure/ai/modal_function_client.py`
- `backend/src/sketch2life/infrastructure/story_run_lite/`
- `backend/src/sketch2life/infrastructure/lesson_library/`
- `backend/src/sketch2life/interfaces/http/routers/story_run_lite.py`
- `backend/src/sketch2life/interfaces/http/routers/lesson_library.py`
- `backend/src/sketch2life/interfaces/http/story_run_lite_app.py`
- `backend/src/sketch2life/interfaces/http/app.py`
- `backend/tests/`

### Feature record and evidence

- `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
- `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
- `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
- `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/AI_API_QWEN35_MODAL_VALIDATION_20261105.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/assets/ai_api_qwen35_modal_validation_20261105/`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/scripts/`

## 8. Risks and explicit limits

- The primary checkout is dirty and on `dev`; all implementation is isolated to the existing Modal feature worktree. No unrelated checkout changes may be copied or overwritten.
- The current SRS copy in this worktree is stale. It must be synchronized before implementation and its contents preserved as the exact authority.
- The present StoryRun-lite API is a local synthetic slice; it is not proof that all FEAT-063 production APIs are implemented.
- Qwen3.5, FLUX.3, SAM2.1, Whisper, VieNeu-TTS, and LTX-2.5 have distinct runtime/license/capacity requirements. A model can be listed/implemented but remain untested or blocked if Modal cannot allocate the required GPU or a gated model license is unavailable.
- SRS final video-safety model and thresholds are not selected. Until that is resolved and validated, no generated video may become playable.
- AI lesson-suggestion and lesson-visual APIs must reuse real tenant/authorization/job/asset ownership boundaries; a test-only synthetic route is not a substitute for production authorization.

## 9. Explicit exclusions

- No full SRS redesign, deletion of older SRS history, changes to the Data Table Register, or unrelated API renaming.
- No production model approval or workload enablement, real child data, model training/fine-tuning, payments, mobile/UI work, or cross-organization access.
- No change to Modal Volumes by deletion, no secrets/env edits, no public Modal endpoint exposure, and no non-Modal provider fallback.
- No commit, push, merge, branch rewrite, or changes to the dirty primary `dev` checkout.
