# Plan Rev1 — Qwen3.8-27B-FP8 and Parent story prompt

**Feature:** FEAT-082 — Qwen3.8 FP8 story quality
**Date:** 2026-11-22
**Status:** APPROVED for the exact scope below
**Authority:** FEAT-063 SRS v2.7-draft Rev67 (unsigned), plus the owner's direct instruction to switch to Qwen3.8 and optimize the prompt.

## 1. Objective

Replace the shared Qwen3.5-9B BF16 checkpoint in the Modal language/audio development app with the official, revision-pinned Qwen3.8-27B-FP8 checkpoint. Improve Parent story specificity and narrative progression using the context already approved and stored for the run. Preserve existing response/API behavior, educational safeguards, adult review, and privacy limits.

## 2. As-built findings driving the change

1. `language_audio_app.py` currently pins Qwen3.5-9B and forces `torch.bfloat16` during model loading.
2. One shared text checkpoint serves four workloads: Parent story, Teacher Sketch Deck, lesson-plan suggestions, and Parent activity suggestions. The model change therefore applies to those four workloads; only the Parent story prompt and its internal request context change.
3. The pre-change story prompt asks for short, generic observations, always exactly five scenes, and does not use the run topic or pinned lesson knowledge. The backend already supplies optional `lesson_direction`, but the worker/adapter reject non-null lesson direction. Free-text profile interests are not an approved input and are excluded.
4. Current story input does not contain the Parent-selected primary activity. The current selection response is not persisted or passed by the UI/API. This task must not fabricate or silently choose an activity; this remains a separate SRS alignment gap.
5. The story response contract and API already support five scenes and a 30-second draft. This plan retains those bounds; it does not change video timing or the 5–15 scene product range.

## 3. Scope

### In scope

- Pin `Qwen/Qwen3.8-27B-FP8` to Hugging Face revision `c3a462cc3d38cf351f3b26cbd763469eeb74ef81` in the Modal language/audio model manifest, cache path, and backend story provenance.
- Load the checkpoint according to its shipped FP8 quantization configuration; remove the unconditional BF16 override and verify the effective model/runtime configuration before inference.
- Restrict Qwen text functions to L40S for this 27B checkpoint. Keep the existing Modal function names used by backend callers.
- Align model provenance checks in Parent story and Teacher lesson-plan/Sketch Deck APIs with the shared text checkpoint; keep drawing-VLM and image-generation provenance separate.
- Version the internal story-generation input contract and pass the approved run topic and exact pinned lesson's subject-learning notes. Continue excluding raw drawing bytes, profile name, profile interests, and unrelated profile fields.
- Allow the already-pinned `lesson_direction` only when it is present in the server-owned run snapshot; use it in the prompt when supplied. Keep the adapter and worker validation aligned.
- Do not send `interests_summary` in this change: the current profile field is free text, while the SRS permits an allowlisted interests context. The code has no allowlist normalizer yet.
- Rewrite the Vietnamese story prompt around a specific narrative arc, visible drawing anchors, age-appropriate language, non-repetitive scene actions, and a meaningful ending. Keep the strict JSON shape, current five-scene/30-second composition, safety rules, and butterfly lifecycle checks.
- Apply Qwen's documented non-thinking sampling values where supported by the pinned Transformers runtime; keep grammar-constrained JSON decoding and validate the output through existing parsers.
- Record the change as a development implementation candidate in a new ADR. Do not rewrite the unsigned product SRS in this task.
- Deploy the language/audio app, download the pinned checkpoint to the existing Modal volume without deleting the prior checkpoint, and make at most one synthetic Parent story inference. Capture sanitized worker logs and output validation evidence, then stop this app.

### Out of scope

- Drawing-understanding/VLM checkpoint, activity-selection API or persistence/UI, profile/consent/database schema, SVG, teacher UI, TTS/ASR model changes, LTX/video, quota/billing, production deployment, and SRS sign-off.
- Repeated GPU retries or a broad quality benchmark. One successful synthetic inference proves the new worker path and schema, not a statistically significant quality improvement.

## 4. Implementation steps

1. Record this plan and the owner's direct approval before code changes.
2. Update the shared Modal text-model pin, path, manifest validation, readiness metadata, GPU allocation, and loader behavior for FP8.
3. Update backend model provenance and internal story input construction/validation to include the run topic and bounded fields from the exact pinned lesson only; exclude profile interests. Align `lesson_direction` validation across API adapter and worker.
4. Replace the Parent story prompt with a structured, Vietnamese-first narrative brief; preserve all output keys, schema bounds, and safety/business validators.
5. Add ADR-0024 and feature-local context, decisions, source register, status, and evidence entries. Leave historical SRS copies and unrelated working-tree changes untouched.
6. Perform static source/security review. Deploy the Modal app, stage the pinned public model, send one synthetic story request, inspect returned contract and sanitized logs, and stop the app.

## 5. Acceptance criteria

- **AC1 — Model identity:** Modal manifests/readiness and backend Parent story plus Teacher text API metadata report the same Qwen3.8-27B-FP8 model ID and exact pinned revision. Drawing VLM remains Qwen3.5-9B.
- **AC2 — FP8 loading:** the loader does not force a BF16 conversion; model config/runtime evidence confirms the checkpoint's FP8 quantization is active on L40S without OOM.
- **AC3 — Contract alignment:** backend, adapter, and worker agree on the versioned internal story input. Topic and pinned lesson fields are bounded server-owned values; free-text profile interests, raw drawing bytes, and profile identity are absent; `lesson_direction` is accepted only from the eligible server snapshot.
- **AC4 — Prompt quality shape:** prompt defines a concrete opening → change/action → discovery/resolution arc, uses visible features and approved session context, avoids repetitive filler and unsupported facts, and retains child-safe, adult-review, and strict JSON constraints.
- **AC5 — Live worker:** one synthetic story request completes on the new model, passes worker parser plus backend response validation, and returns the expected five scenes/30-second structure. If it fails, stop after capturing the first terminal cause; do not retry.
- **AC6 — Cleanup and records:** no real child data or secrets in evidence; Modal language/audio app is stopped after the run; feature status and evidence identify exactly what passed and what remains unverified.

## 6. Verification and risks

- Static review of source diffs, exact model pin, schema agreement, prompt safety, and `python tools/validate_repository_security.py`.
- One Modal model download and one live synthetic story inference; model cold-start/load time, inference time, GPU name/memory, response schema, and non-sensitive call identifiers are recorded. No video call.
- Main risk: the 27B checkpoint or FP8 loader may exceed L40S memory or require a different Transformers kernel. If model-load or first inference fails, record the exact stage and stop; do not silently fall back to 9B.
- Quality limitation: one sample cannot establish that stories are consistently better. The missing selected-activity input remains a known SRS gap and is not papered over by prompt text.

## 7. Approved file scope

- `deployment/modal/srs_v23/language_audio_app.py`
- `backend/src/sketch2life/infrastructure/ai/modal_function_client.py`
- `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py`
- `backend/src/sketch2life/interfaces/http/routers/parent_ai.py`
- `backend/src/sketch2life/interfaces/http/routers/teacher_ai.py`
- `deployment/modal/srs_v23/README.md`
- `docs/adr/ADR-0024-qwen38-fp8-development-story-candidate.md`
- `apps/ui-mobile/App.tsx` and `apps/ui-mobile/src/parent/**` (Amendment E: Parent Android UI path only)
- `features/FEAT-082-qwen38-story-quality/**`
- `docs/context/SOURCE_REGISTER.md` (one feature implementation record only)

No other file is in scope without a plan amendment.

## Amendment A — 2026-11-22

Source inspection found that `interests_summary` is unrestricted profile text, not the SRS-required allowlisted interests set. The approved scope is narrowed to exclude it from Modal input; only topic and approved fields from the exact lesson pin may be added. This security-driven narrowing does not add files or relax any acceptance criterion. The plan hash in `approvals/TASK_APPROVAL.md` is updated to this exact file.

## Amendment B — 2026-11-22

The implementation checklist had stale wording about an “approved interest summary.” The code and approved scope exclude profile interests entirely because the stored field is free text. The Modal FP8 image also installs the pinned Transformers FP8 kernel extra, as required by the official Fine-grained FP8 loading documentation; this is a loader/runtime implementation detail within AC2 and the already approved file scope.

## Amendment C — 2026-11-22

The shared text worker serves Teacher lesson-plan suggestions and Sketch Deck generation as well as Parent story generation. Source review found that Teacher API response validation still compared the worker's model provenance against the separate Qwen3.5 drawing-VLM constants; that would make both Teacher text endpoints fail after the shared checkpoint switch. Add the Teacher AI router and dedicated Qwen text provenance constants to the approved file scope. Drawing VLM and image-generation checks remain unchanged.

## Amendment D — 2026-11-22

The single approved synthetic inference reached model generation but failed when Transformers attempted to verify the Hugging Face publisher for its fine-grained FP8 kernel. The underlying publisher-overview lookup failed; this is a kernel trust-resolution failure, not a story parser or prompt rejection. The official kernel is `kernels-community/finegrained-fp8`, Apache-2.0, and Transformers 5.22.1 maps this integration to kernel version 4. The worker now preloads only that repository from immutable Hub revision `3c8fcc86c0e42b7abe5bcf666d3a3afdce93a0e8` using the exact repository ID in the `trust_remote_code` allowlist, verifies the required exported functions, and registers the module in Transformers' FP8 kernel cache before allocating the model. It does not enable trust for arbitrary repositories. This amendment keeps the existing one-inference cap: it authorizes static validation and deployment of this fix only; a second synthetic inference requires a separate explicit owner approval.

## Amendment E — 2026-11-22

The owner directly requested: “chạy thử trên UI đi, fix nếu có bug.” This approves one fresh Parent story-generation attempt initiated from the real Android UI and routed through the local backend to the deployed Qwen3.8 Modal worker. It extends the prior one-request cap by exactly one story inference, for at most two total story attempts in FEAT-082. Use only synthetic account/profile/run/image data; do not use fixtures or real child data. Preserve normal auth, consent, catalog/activity selection and backend admission; do not bypass quota or business/safety gates. No video generation. A UI/API defect that blocks the request may be fixed within `apps/ui-mobile/App.tsx`, `apps/ui-mobile/src/parent/**`, and the existing approved Parent story/backend/Modal files in §7. If the worker returns a terminal error, record it and stop; do not send another inference. If a story is persisted but the UI fails to render it, fix the UI and retrieve that same persisted result without generating again. Capture screenshots, request IDs, timing and sanitized logs in FEAT-082 evidence, then stop the language/audio Modal app.

## Amendment F — 2026-11-22

The owner requested a real UI run and bug fixes. Inspection found that the Parent activity screen allows continuing without selecting an activity, and the story request neither persists nor sends the selected activity. This conflicts with FEAT-063 Rev67 FR-P-05 and §31.17, which require one adult-selected main activity before story generation.

This amendment authorizes the narrow product-contract fix needed for the real UI workflow:

1. Persist each server-resolved activity suggestion set against its Parent StoryRun, owner, current input revision, and drawing-understanding revision. Return opaque set/candidate identifiers. Persist the resolved server-side candidate payload and its digest so a client cannot substitute activity content.
2. Add an authenticated selection command that accepts only a candidate from that stored set, validates run/revision/authorization, and rechecks access to the exact published/shared lesson version before accepting catalog activities. AI drafts are selectable only from the stored, quality-gated fallback response.
3. Store the adult's selection and exact source/version/content hash as a separate immutable selection record. Do not mutate prior drawing, context, lesson, or suggestion snapshots.
4. Reject story generation unless the current run has a valid selection for the current input and understanding revisions. Include a bounded server-owned activity snapshot and provenance in a versioned Qwen story input; instruct the model to connect the narrative to the selected after-video activity without claiming that the child has already done it.
5. Update the real Parent UI to require an explicit selected card and a successful server selection before continuing. Remove the skip path; show loading/error/retry states without generating a story from an unselected activity.

The implementation may add one Alembic migration and focused tests. Approved file scope is expanded to `apps/ui-mobile/src/parent/**`; the existing approved FEAT-082 Parent story files; `backend/src/sketch2life/application/ports/parent_story_runs.py`; `backend/src/sketch2life/application/services/parent_story_runs.py`; `backend/src/sketch2life/contracts/schemas/modal_ai.py`; `backend/src/sketch2life/contracts/schemas/parent_story_runs.py`; `backend/src/sketch2life/infrastructure/story_run_lite/tables.py`; `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py`; `backend/src/sketch2life/interfaces/http/routers/parent_ai.py`; `backend/alembic/versions/` (one new migration); the focused Parent activity/story tests; and FEAT-082 records/evidence. No unrelated files or broad SRS rewrite are authorized.

Runtime cap: at most one Parent activity-suggestion Modal inference and one fresh story-generation inference from Android UI (in addition to the already completed failed story call). Synthetic data only; normal authentication, consent, activity quality/access, quota/admission, and safety gates remain on. No video and no inference retry after a terminal worker failure. Record database migration state, request/call IDs, timings, sanitized logs, and screenshots in FEAT-082 evidence, then stop the language/audio app.

## Amendment G — 2026-11-22

The owner asked to run the changed story flow on the real UI and fix any bugs. The execution target is the dirty `feature/fe-mobile-remediation` worktree because that is the source mounted by the active Parent API container and the current Expo UI. Source inspection shows this worktree already has the required persisted Parent activity-suggestion set and adult-selection API/migration; do not create a duplicate table, route, or migration. Reuse the existing selected-activity snapshot and its revision/hash checks.

The Qwen3.8 model and prompt update from this plan is not yet present in that target worktree: its shared text worker and backend provenance still name Qwen3.5. This amendment authorizes porting the approved pinned Qwen3.8-27B-FP8 loader, strict FP8/kernel checks, L40S placement, story prompt, and text-model provenance into the current worktree while preserving its Parent activity worker/parser, progress logging, activity-selection input contract, and existing APIs. Version the internal story input as `story-generation-input.v3` and include only the bounded topic from the server-owned run context and subject-learning notes from the exact pinned lesson snapshot, alongside the currently approved story fields. Exclude free-text profile interests, profile identity, and unrelated profile data. Update the workload manifest and focused tests/docs so the worker, backend, and UI call report one matching model revision. Drawing VLM remains Qwen3.5; no vision or video model change is included.

The real Android test may reuse a persisted synthetic activity selection. If no valid selection exists for the chosen synthetic run, at most one activity-suggestion call is allowed; at most one new story request may be sent from the Android UI. No direct worker/API inference, fixture data, real child data, quota bypass, video request, or retry after a terminal worker error. Save sanitized logs, model/runtime identity, request and Modal call IDs, timing, and Android screenshots under `evidence/ANDROID_UI_RUN_20261122/`; stop the language/audio app after the attempt.

Approved implementation/evidence paths for this amendment are the existing §7 Qwen/story files, `deployment/modal/srs_v23/workloads.json`, the focused story/model contract tests, and this feature's records/evidence. No unrelated files, SRS rewrite, commit, or push is authorized.

## Amendment H — 2026-11-22

The real Android flow stopped before AI dispatch because the FEAT-082 ClamAV container could not join its Docker network: the compose host port `127.0.0.1:3310` is already owned by a separate older ClamAV container. The owner approved the following test-environment-only repair in response to the exact scope question in this conversation:

1. Use a temporary Compose override outside the repository to publish only the FEAT-082 ClamAV service on `127.0.0.1:53310`.
2. Recreate only the FEAT-082 ClamAV container under the existing compose project, preserving its existing named signature-database volume. Do not stop, recreate, or modify the older stack/container.
3. Verify that the FEAT-082 ClamAV container is attached to `s2l-feat081-rev23_default`, the API resolves service host `clamav`, and the exact synthetic image scan returns a clean verdict before retrying through the real Parent UI.
4. Retry the existing UI artwork-analysis action once. This is a pre-dispatch failure: the previous attempt sent no AI request. Preserve all AI inference caps in Amendment G; do not retry after a terminal worker failure.

No tracked Compose/source file is changed by this runtime amendment. The temporary override is removed after the test. Existing story/activity caps, synthetic-only requirement, no-video rule, no quota/safety bypass, evidence requirements, and Modal cleanup remain unchanged.

## Amendment I — 2026-11-22

The single approved Parent activity-suggestion inference loaded the pinned Qwen3.8 FP8 model on L40S, then failed before output because `kernels==0.17.3` produced an empty Hugging Face user-agent while telemetry was disabled; `huggingface_hub==1.32.0` formatted it with a trailing separator and `httpx` rejected the header. This is a kernel bootstrap transport error, not a model-load, prompt, activity-parser, or output-quality failure.

This amendment authorizes a narrow fix inside the existing approved Modal worker and its focused contract test:

1. Temporarily enable only generic Hugging Face package/runtime user-agent metadata while resolving the single pinned `kernels-community/finegrained-fp8` repository; keep the exact repository allowlist and revision unchanged.
2. Restore the process telemetry flag in a `finally` block whether kernel resolution succeeds or fails. Do not include request, profile, child, prompt, image, or generated-content data in the user-agent.
3. Add offline tests proving the repository/revision/allowlist remain pinned and the telemetry flag is restored on both success and failure.
4. Run focused offline tests and static/security checks; if useful, deploy and call only the Modal health/readiness endpoint. Do not run another activity or story inference under this amendment. A new inference requires separate explicit owner approval because the one activity-inference allowance ended in a terminal worker failure.

All existing synthetic-only, no-video, no-quota/safety-bypass, file-scope, no-commit/push, evidence, and cleanup limits remain unchanged. Drawing VLM remains Qwen3.5 by design; shared text/story workloads use the pinned Qwen3.8 checkpoint. The old Qwen3.5 volume folder is retained for the drawing workload and rollback.

## Amendment J — Full real Parent Android-to-video E2E — 2026-11-22

The owner directly requested: “chạy adb, emulator và fix lỗi tiếp đi, gọi cả vid và mấy cái kia luôn, làm luồng end to end đi, check nào hết lỗi thì ấy”. This supersedes the prior no-new-inference/no-video execution cap for this bounded synthetic test, including Amendment I's health-only limit.

### Authorized scope

1. Start an Android emulator with ADB and the real Expo Parent app from the `feature/fe-mobile-remediation` worktree; use a synthetic Parent account/profile and synthetic drawing only.
2. Continue from the existing Parent flow where safe, or create a fresh synthetic StoryRun if the earlier failed run cannot be recovered through supported APIs. Do not use the preview harness, fixtures, direct worker calls, or direct database mutation to advance workflow state.
3. Diagnose and fix defects required for the real Parent path across the existing Parent UI, backend, Modal text worker, video API/worker, and test Docker configuration. Reuse the existing Qwen3.8 shared text checkpoint for activity/story workloads; drawing VLM remains Qwen3.5; video remains the pinned LTX-2.5 worker. Keep the story silent (no narration/audio) as currently implemented.
4. Run actual activity suggestion when the catalog is empty, adult-select a valid persisted activity, generate and review a story through the UI, then request and poll a video candidate through the UI. Video is accepted only if the actual output plays and all current hard safety/business checks pass.
5. Preserve authentication, consent, malware, age, ownership, activity selection, story review, video safety and other hard gates. Use the existing synthetic/dev quota seed or approved dev quota mechanism; do not alter quota/payment production behavior or falsify a ledger.
6. For each distinct deterministic defect, make the smallest scoped fix, run focused offline tests, then make at most one fresh live request for the fixed workload stage. If that fresh request fails terminally for a different cause, capture the diagnostics and continue only after fixing that new cause; do not blindly retry an unchanged request/model/prompt.
7. Capture timestamped UI screenshots, sanitized backend/Modal logs, request/call IDs, per-stage latency and final video evidence in `evidence/ANDROID_UI_RUN_20261122/`. Never store credentials, real child data, raw prompts, or access tokens.
8. Stop the test emulator, Expo/Metro processes, test-specific Docker services, and the Modal language/audio and video apps after completion. Do not stop or recreate unrelated Docker/Modal apps or persistent volumes.

### Approved implementation file scope

Existing Plan Rev1 §7 paths plus the existing Parent workflow source/tests and video candidate source/tests already present in the current FEAT-081 worktree: `apps/ui-mobile/src/parent/**`, `apps/ui-mobile/App.tsx`, `backend/src/sketch2life/**` paths directly involved in Parent activity/story/video candidate orchestration, `backend/alembic/versions/` only if a required migration is missing, `deployment/modal/srs_v23/language_audio_app.py`, `deployment/modal/srs_v23/video_app.py`, their focused tests, `deployment/modal/srs_v23/workloads.json`, `compose.yaml` only for isolated test-service startup/ports, and FEAT-082/FEAT-081 evidence/status/approval records. Preserve all unrelated dirty and staged changes. No broad SRS rewrite, unrelated feature implementation, commit, or push is authorized.

### Acceptance criteria

- Android UI sends the actual authenticated Parent API requests for topic/subject, drawing analysis, activity selection, story generation/review, and video creation/status/playback.
- All AI calls report the expected model IDs/revisions: drawing Qwen3.5; text Qwen3.8-27B-FP8; video LTX-2.5. No hidden fallback to another model.
- Story includes the selected activity and visible drawing context, passes current validators and adult review; generated silent video is produced from the child drawing/story, passes hard safety checks, persists, and plays in the UI.
- Each failed stage has a clear root cause and evidence; any unresolved failure is explicitly marked, not presented as complete.
- Test-specific Modal apps and local processes are stopped after evidence capture; no commit/push.
