# Plan Rev45 — Non-video AI flows end-to-end

**Approval status:** APPROVED  
**Execution status:** VERIFICATION COMPLETE WITH EXTERNAL BLOCKERS  
**Date:** 2026-11-05 (Asia/Saigon)  
**Feature:** FEAT-063 — system architecture rearchitecture

## 1. Owner instruction and source of truth

The owner directly requested: continue fixing the AI flows and make them work end-to-end; video is excluded for this task. This continues Plan Rev44 but does not inherit its one-attempt limit, because this new direct instruction authorizes follow-up repairs and verification. It does not authorize blind retries after an unknown result.

Canonical product source:

- `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`
- SRS v2.3-draft, current synchronized SHA-256: `6BADEBAAD6C28239CA9B759CF17C57A0405D7242B45F3411F40B7E8FEBDC8381`
- The owner-resolved role policy from Q159 remains: Platform Admin and Teacher may initiate lesson/activity/plan suggestions; Parent may edit an authorized existing draft/personal copy but may not initiate new generation. Every generated lesson remains a private draft until human review.
- Current AI workload inventory: `artifacts/AI_API_WORKLOAD_CATALOG_FEAT063_REV44_20261105.md`.

## 2. Objective

Repair and verify the non-video AI path from backend request through Modal worker to a contract-valid terminal result. Make the existing Parent and Teacher flows, lesson suggestion/visual flows, and speech workers truthful and testable. Correct unsupported model wiring instead of masking failures. Report any stage that remains externally blocked; never report a worker-only call as a complete product API.

## 3. In scope

### 3.1 Non-video AI workers

Workload IDs covered individually:

1. `drawing.analyze` — pinned Qwen3.5-9B multimodal drawing analysis.
2. `story.generate` and `storyboard.generate` — pinned Qwen3.5-9B structured Parent story output.
3. `teacher.sketch-deck.generate` — pinned Qwen3.5-9B deck text from approved activity references.
4. `lesson.plan.suggest` — pinned Qwen3.5-9B private lesson draft from reviewed allowlisted fields.
5. `parent.sketch-guide.generate` — approved image model, generic topic/difficulty only.
6. `lesson.visual.generate` — approved image model, approved lesson/activity revision only.
7. `drawing.segment` — optional SAM2.1 path, source-preserving and reversible.
8. `asr.transcribe` — Vietnamese adult idea transcription.
9. `tts.narration.generate` — Vietnamese narration synthesis.

For each worker, validate immutable model revision, staged input lineage, Modal runtime/GPU readiness, request/response schema, strict output parsing, safe failure behavior, and one actual synthetic Modal inference after the relevant fix. A second attempt is allowed only after logs prove the first failure was a specific, corrected implementation issue or a terminal provider failure; unknown outcomes are not retried. Do not use real child, teacher, or parent data.

### 3.2 Backend/API path

- Repair the isolated StoryRun-lite HTTP path so its accepted AI requests produce a pollable terminal state and never report `202` while blocking the request thread.
- Wire authenticated Lesson Library AI suggestion only through the existing organization/role and lesson ownership guards, and accept reviewed allowlisted fields only. Admin/Teacher can generate; Parent generation must be rejected. Results must persist as private drafts.
- Wire Parent Sketch Guide and Teacher Sketch Deck only where the current session/occurrence owner, opt-in, authorization, asset provenance, and job lifecycle can be enforced. Disabled opt-in must create no job or asset.
- Add or mount a scoped shared job-status route only if it can use the existing durable AI Jobs service and owner authorization. Do not add a generic client-selectable Modal workload endpoint.
- Reconcile every newly exposed AI operation into OpenAPI and the FEAT-063 catalog. If a product route cannot use an existing safe domain/persistence boundary, record the precise missing boundary instead of exposing a synthetic route as production.

### 3.3 Operational behavior

- Keep all production workload switches disabled. Dev workers may be invoked for synthetic verification.
- Preserve the model and scratch Volumes. Stop only apps/deployments created for this task and verify zero active task-owned workers.
- No video generation, video composition, scene validation, final video safety, or playback test.
- Do not edit `.env`, create or read provider-secret values, or commit/push/merge.
- Do not replace FLUX.3 silently. If FLUX.3 access remains gated, use only an alternative explicitly selected by the owner.

## 4. Acceptance criteria

- **AC-45.1:** Qwen3.5 drawing, story/storyboard, Teacher deck, and lesson-suggestion workers each return strict contract-valid synthetic output from the pinned checkpoint, or a precise terminal blocker is recorded with logs and elapsed time.
- **AC-45.2:** ASR and TTS pass synthetic end-to-end contract checks; ASR records word-level or sentence-level quality evidence and does not auto-accept a transcript for a child-facing story without adult confirmation.
- **AC-45.3:** Parent Sketch Guide and lesson visual generation use a model that is actually available on Modal and return validated image artifacts with provenance; no child profile/artwork enters the Parent guide input.
- **AC-45.4:** SAM2 is either verified with a synthetic mask that preserves the source asset, or recorded as blocked after a bounded readiness/scheduling check. It remains optional and cannot block the core flow.
- **AC-45.5:** API tests prove role, organization/session scope, opt-in, idempotency, draft-only output, and pollable job behavior. Parent cannot start lesson suggestion; Admin/Teacher can. No raw uploaded lesson or unreviewed extracted text reaches a model.
- **AC-45.6:** Every non-video AI API/worker and every still-missing product route is listed in the FEAT-063 catalog with exact method/path or an explicit `route unspecified/missing` reason. No worker-only call is represented as a mounted production API.
- **AC-45.7:** Focused API, worker, parser, OpenAPI, lint/compile, and repository-security checks pass or have exact failures recorded. Evidence includes model revision, Modal call ID, terminal state, elapsed time, and cleanup state.
- **AC-45.8:** Video workloads are untouched and untested; no playable video is claimed. Production workload switches remain disabled.

## 5. Verification plan

1. Add regression tests for each discovered parser/runtime/business-rule failure before changing the corresponding worker.
2. Run focused local Modal worker tests, backend API tests, OpenAPI parity, lint, and compile checks.
3. For each available workload, deploy only its task-owned `dev` Modal app; check health, model revision/files, GPU, and secret-name availability before inference.
4. Run bounded synthetic requests through the API/Modal adapter and poll to a terminal result. Capture only safe metadata and synthetic fixtures. Diagnose failed calls from provider logs before any allowed retry.
5. Stop task-owned Modal apps and verify no task-owned tasks remain. Preserve shared Volumes.
6. Run `python tools/validate_repository_security.py` and `git diff --check` before closeout.

## 6. Risks and constraints

- Modal `dev` currently has no Hugging Face Secret. The pinned FLUX.3 checkpoint previously returned HTTP 401. This blocks image generation unless the owner adds a secret in Modal or explicitly selects a public Modal-hosted alternative.
- Qwen3.5 drawing, story, and lesson generation were not inference-verified after the Rev44 runtime/parser fixes.
- SAM2 previously waited 1,800 seconds for GPU scheduling without producing a mask. Test only after readiness and use a bounded queue window.
- The main backend OpenAPI currently has no AI dispatch operation. Existing StoryRun-lite is loopback-only and process-local; any new route must not imply production durability/authentication unless the real service boundary is wired.
- The SRS is draft and unsigned. This task implements its current recorded requirements without promoting the models or changing unrelated architecture.

## 7. Allowed paths

### Plan, approvals, feature records and evidence

- `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV45_NONVIDEO_AI_END_TO_END_20261105.md`
- `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
- `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
- `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
- `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
- `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/AI_NONVIDEO_AI_END_TO_END_20261105.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/assets/ai_nonvideo_ai_end_to_end_20261105/`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/scripts/`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/AI_API_WORKLOAD_CATALOG_FEAT063_REV44_20261105.md`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/openapi.json`

### Modal workers and tests

- `deployment/modal/srs_v23/contracts.py`
- `deployment/modal/srs_v23/drawing_vlm_app.py`
- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/flux_image_app.py`
- `deployment/modal/srs_v23/drawing_segment_app.py`
- `deployment/modal/srs_v23/workloads.json`
- `deployment/modal/srs_v23/README.md`
- `deployment/modal/srs_v23/tests/`

### Backend contracts, applications, persistence and APIs

- `backend/src/sketch2life/contracts/schemas/`
- `backend/src/sketch2life/application/ports/`
- `backend/src/sketch2life/application/services/ai_jobs.py`
- `backend/src/sketch2life/application/services/story_run_lite.py`
- `backend/src/sketch2life/infrastructure/ai/`
- `backend/src/sketch2life/infrastructure/ai_jobs/`
- `backend/src/sketch2life/infrastructure/lesson_library/`
- `backend/src/sketch2life/infrastructure/story_run_lite/`
- `backend/src/sketch2life/interfaces/http/routers/ai_jobs.py`
- `backend/src/sketch2life/interfaces/http/routers/lesson_library.py`
- `backend/src/sketch2life/interfaces/http/routers/story_run_lite.py`
- `backend/src/sketch2life/interfaces/http/app.py`
- `backend/src/sketch2life/interfaces/http/story_run_lite_app.py`
- `backend/tests/`

## 8. Explicit exclusions

- All video generation and post-video stages, including LTX-2.5, video composition, final safety, and playback.
- Production workload enablement, model promotion, real personal/child data, model fine-tuning, or external provider fallback.
- Reading/setting secret values, editing `.env`, deleting Volumes, changing the dirty primary checkout, and commit/push/merge.
- Changes to unrelated APIs, Data Table Register entries, or SRS history.

## 9. Execution outcome — 2026-11-05

The Vietnamese Unicode parser regression was fixed without relaxing the JSON schema or semantic checks. The LMFE CPU probe, pinned-Qwen GPU constrained-generation probe, and fresh synthetic inference passed for drawing analysis, Parent story/storyboard, Teacher Sketch Deck, and lesson-plan suggestion. Synthetic TTS and ASR both passed, including exact ASR text. Focused Modal tests passed (76); focused backend API/OpenAPI tests passed (61, 6 skipped); targeted Ruff and Python compilation passed.

The FLUX.3 Parent Guide and lesson-visual requests remain blocked because Modal `dev` still has no `sketch2life-dev-huggingface` Secret; no image inference was claimed. SAM2 remains optional and unverified in this pass; its last attempt waited 1,800 seconds for GPU scheduling and created no mask. The worker calls do not turn the missing durable authenticated product API boundaries into mounted APIs. All production workload flags remain disabled, no video call was made, and the two task-used Modal apps were stopped with zero tasks. Repository security validation passed; `git diff --check` exited 0. Detailed output and call IDs: `../evidence/AI_NONVIDEO_AI_END_TO_END_20261105.md`.
