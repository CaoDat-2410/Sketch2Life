# Plan Rev82 — Parent/Teacher AI contract, gates, local seed and E2E

**Date:** 2026-11-12<br>
**Status:** Approved for implementation under the owner request recorded in `approvals/TASK_APPROVAL.md`<br>
**Product authority:** FEAT-063 SRS v2.7-draft, Rev57 baseline with local amendments through Rev64 (unsigned), plus the approved owner-directed Rev81 implementation deltas. This plan does not amend or sign the SRS.

## 1. Goal

Make the real Parent and Teacher non-video workflows runnable end to end on the existing local Docker/Auth Emulator and Modal dev Apps. Fix observed API/schema failures, moderately relax only subjective AI quality heuristics, seed a synthetic Teacher/org/class/lesson idempotently, and preserve useful failure diagnostics without repeated Modal deployment or inference loops.

## 2. Evidence-driven problems

1. Parent drawing-understanding Qwen3.5 inference returned malformed/truncated JSON at exactly the 512-token ceiling; the generation path's LMFE configuration differs from the known language-worker path for Vietnamese alphabet and model EOS IDs.
2. Parent progressive FLUX guide was rejected because panel strokes shifted between stages despite otherwise usable candidate generation.
3. Parent UI requests `GET /api/parent/v1/story-runs` and receives 405.
4. Teacher end-to-end is blocked by the lack of a local Teacher Auth Emulator account, organization/class assignment, and Teacher-owned reviewed lesson seed.
5. Modal language/audio functions were reported `NotFoundError`; the deployed app build and worker registration need inspection/fix before a single bounded redeploy. Docker's health sidecar must not repeatedly deploy, warm, or restart Modal Apps.
6. Prior reports do not establish live Parent activity/story or Teacher lesson-plan/deck/presentation success; no fixture output may be counted as success.

## 3. Approved work requested by the owner

The owner's direct request on 2026-11-12 authorizes:

- Correct Parent and Teacher API/AI JSON contracts and fix the observed workflow errors.
- Reduce overly strict quality gates to a moderate level.
- Create a synthetic local Teacher account and seed only missing local entities needed to exercise both workflows through Docker.
- Run real Parent and Teacher UI/API workflows and real non-video Modal inference; record all results and remaining failures.
- Reduce Modal crash-loop/repeated-start behavior.

## 4. Implementation direction and safety boundaries

### 4.1 AI schemas and quality gates

- Keep strict versioned JSON schemas, required fields, bounded lengths/counts, duplicate-key rejection and Pydantic/backend contract validation. Do not accept malformed/truncated JSON or silently repair it into a success.
- Align drawing Qwen constrained decoding with the proven language-worker implementation: Vietnamese JSON alphabet, effective model EOS token IDs from the loaded model, explicit end-of-sequence diagnostics, and a bounded output budget appropriate for the compact drawing schema. Report token-ceiling exhaustion as a distinct terminal error.
- Relax only subjective visual continuity tolerances enough to accept small FLUX line-position drift across cumulative guide panels. Retain panel count/layout, nonblank/minimum ink, meaningful progression, requested-subject, output schema, adult review and image-safety checks.
- Relax only subjective activity prose/format checks where safe concise Vietnamese is equivalent. Preserve age suitability, parent-accessible catalog ownership, deduplication/exclusion, adult supervision, material safety, outdoor/activity constraints, schema, PII, and the rule that an adult selects the primary activity.
- Preserve story scene count and schema, child safety, adult script confirmation, authorization/consent and all role/privacy/business gates.

### 4.2 API and local test data

- Add an authenticated, owner-scoped Parent StoryRun collection GET compatible with the mobile history call, with bounded pagination and no cross-profile leakage.
- Create an insert-only `teacher_seed` one-shot Compose service using Firebase Auth Emulator only. Store its local test email/password only in the ignored project-root `.env`; never print, stage, commit or copy credentials to evidence. Reuse exact existing seed entities; stop on identity/ownership conflicts.
- Seed only synthetic local identities and app records needed for Teacher: teacher role, organization, classroom assignment, teacher-owned reviewed lesson/version/presentation and activity references. Reuse the existing Parent synthetic profile/lesson/catalog where valid. Do not fabricate legal consent or create real-child data.
- Root `.env.example` has placeholders only. No production Firebase Auth write and no Firebase Storage, Firestore or RTDB.

### 4.3 Modal/Docker stability and cost boundary

- Inspect the registered Modal Apps, function names, build logs and image dependencies before changing deployment configuration. Fix only the verified cause of missing language functions; preserve Qwen3.5 and FLUX pins.
- Modal startup attempts each approved non-video warmup at most once per Compose startup, with bounded concurrency (sequential by default), no automatic retry loop and no `min_containers`. Warmup must use the approved non-inference envelope. `/health` follows; unavailable Apps are reported as DEGRADED without blocking the local API.
- Do not deploy/update Apps on each Docker restart. Do not stop shared Modal Apps when Compose stops. Keep video and disabled SAM2 excluded. Model loading/warmup GPU cost is accepted under prior owner approval but must be counted/reported; no product inference is sent by the startup health service.

## 5. Acceptance criteria

1. Drawing-understanding worker returns schema-valid JSON for one generated synthetic image through the actual Parent UI/API path; adult confirmation remains required.
2. Parent optional line guide returns a real multi-step AI candidate that passes moderate visual continuity checks, or reports a specific failure without blocking capture.
3. Parent catalog activity selection and story generation each return actual Qwen3.5 outputs through real API contracts; activity selection remains catalog-first and adult-confirmed. No video call.
4. Parent history collection GET returns only the signed-in Parent's authorized runs with documented response schema and bounded pagination.
5. Docker seeds one local Teacher identity and required org/class/lesson data idempotently; a second seed run adds no duplicates and conflicts fail closed.
6. Teacher signs in through the local Auth Emulator, requests a real lesson-plan suggestion and Sketch Deck, and displays the full persisted/current presentation with the generated AI output/media in slide order. Capture every AI-generated presentation slide/result; do not capture generic UI as evidence.
7. Modal image build/deployment and health logs identify each app/function failure precisely. Compose restart does not create a retry/deployment loop. Record startup warmups separately from real inference calls.
8. Focused unit/API/UI checks pass for changed contracts. One real call maximum per required inference workload after fixes; do not repeat a passing call or retry unknown outcomes. If a call fails, preserve its request/correlation/timing and do not loop.
9. Evidence contains synthetic input/output only, sanitized logs and per-workload timing/status. No credentials, raw secrets or real child data.
10. No LTX/video inference, production Auth operation, destructive database reset, volume deletion, commit, push or merge.

## 6. Planned change manifest

Implementation is restricted to these path families:

- `deployment/modal/srs_v23/drawing_vlm_app.py`
- `deployment/modal/srs_v23/flux_image_app.py`
- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/workloads.json`
- `deployment/modal/srs_v23/docker_health_lifecycle.py`
- focused tests under `deployment/modal/srs_v23/tests/`
- Parent collection route/application/repository and API schema under `backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py`, `backend/src/sketch2life/application/ports/parent_story_runs.py`, `backend/src/sketch2life/application/services/parent_story_runs.py`, `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py`, and `backend/src/sketch2life/contracts/schemas/parent_story_runs.py`
- local Teacher seed and related local Docker wiring under `backend/src/sketch2life/infrastructure/local_demo/`, `compose.yaml`, and `docs/local-development/`
- narrowly relevant Parent mobile history/API and Teacher AI/presentation UI paths under `apps/ui-mobile/src/parent/` and `apps/teacher-ui/src/`
- `apps/teacher-ui/vite.config.ts` only to resolve the single CAPSTONE-root `.env` when the app runs from an isolated worktree; do not add an app-local env file.
- focused tests under `backend/tests/`
- Parent activity worker/application response schema and moderate fallback quality checks under `backend/src/sketch2life/application/services/parent_activity_suggestions.py`, `backend/src/sketch2life/contracts/schemas/modal_ai.py`, `backend/tests/unit/test_parent_activity_suggestions.py`, and `backend/tests/unit/test_parent_activity_worker_contract.py`.
- FEAT-063 plan approval, context/decision/source/status/evidence indexes and new evidence under `features/FEAT-063-system-architecture-rearchitecture/`
- project-root `.env`: local ignored Teacher seed email/password only; never stage or include in artifacts. `.env.example` may receive placeholders only.

Do not modify canonical SRS/DTR, unrelated legacy APIs, unrelated services, or existing work outside this manifest. Preserve all pre-existing user changes and Docker volumes.

## 7. Verification sequence

1. Run targeted offline parser, gate, repository/API contract and seed-idempotency tests.
2. Build/recreate only the isolated local Compose project without `down -v`; run migrations and idempotent Parent/Teacher seeds; verify Docker health and role-scoped route contracts.
3. Inspect Modal app/function deployment state and logs. Deploy only the corrected required non-video App(s), at most once each; call `/health` and the no-inference warmup contract with bounded concurrency.
4. Exercise Parent on Android emulator: sign-in, profile/context, optional guide, synthetic image capture/upload, drawing understanding and adult confirmation, catalog activity selection, story generation/review, history. Stop before video.
5. Exercise Teacher web: sign-in, seeded org/class/lesson, AI lesson suggestion/review, Sketch Deck generation and complete presentation display.
6. Save AI outputs/screenshots and sanitized logs under the new feature evidence folder. Update FEAT-063 local context/status after observed results.

## 8. Explicit limitations

No result is considered PASS solely from a fixture, unit test, `/health`, seed record, or worker warmup. If provider deployment or an unknown Modal outcome blocks a workload, report it as blocked with the observable cause and do not send repeated paid requests. Video remains outside this execution.

## 9. Evidence-driven local web CORS repair amendment

The real Teacher UI login reaches Firebase Auth Emulator, but its follow-up role check fails because the browser's preflight `OPTIONS /api/auth/v1/me` receives `405 Method Not Allowed` from the local API.

- In the local/test backend only, allow credentialed CORS requests from HTTP loopback origins (`localhost` and `127.0.0.1`, explicit ports); do not use wildcard origins. Production/staging behavior remains unchanged.
- Allow only the HTTP methods and headers required by the real UI/API (`GET`, `POST`, `PATCH`, `PUT`, `DELETE`, `OPTIONS`; `Authorization`, `Accept`, `Content-Type`, `X-Request-ID`, `Idempotency-Key`). The Parent client sends `Idempotency-Key` for cancellation and other idempotent commands; a preflight must allow it without widening origins.
- Add a focused app-level test proving a valid local preflight succeeds and a non-loopback origin receives no CORS grant.
- Add `backend/src/sketch2life/interfaces/http/app.py` and the focused backend test path to the change manifest. The focused test must exercise the Parent idempotency header as well as Teacher auth headers. Keep the root `.env`, API auth, roles, and token validation unchanged.
- Acceptance: Teacher browser role verification no longer fails with a CORS/preflight error; the route still enforces authenticated role and organization assignment.

## 10. Rev82 API schema visibility amendment

Live inspection of `GET /openapi.json` after rebuilding the approved Docker API showed only 16 documented paths. Parent profile/AI/StoryRun and Teacher AI handlers were mounted and callable in the application, but the old Rev37 projection omitted them and its description incorrectly said those capabilities were unavailable. This prevents frontend/API contract review even where handlers exist.

- Include the currently mounted, non-video workflow operations under `/api/auth/v1`, `/api/parent/v1`, `/api/teacher/v1`, `/api/billing/v1`, and `/api/lesson-library/v1` in runtime OpenAPI, preserving their FastAPI request/response schemas and bearer security declarations.
- Keep the existing documented BE1 operations intact. Do not publish video-generation routes as part of this amendment.
- Replace stale “Parent profile/story/activity” and “Teacher occurrence/Sketch Deck” unavailable copy with an accurate statement that the document describes mounted operations and their current implementation surface; do not describe the v2.2 or Rev37 catalog as the current SRS authority.
- Add a contract test that checks representative Parent auth/profile/AI/activity/story/history and Teacher lesson-plan/Sketch Deck/visual paths and referenced schemas appear in the generated OpenAPI JSON; assert video routes remain excluded.
- Add `backend/src/sketch2life/interfaces/http/openapi_srs_v22.py` and the focused OpenAPI contract test path to the manifest. This is an API-documentation projection fix only; no product requirement, SRS/DTR, auth policy, route behavior, or video implementation changes.

## 14. Evidence-driven Qwen drawing output and terminal failure classification

- **Observed evidence:** One real Android Parent drawing-analysis request used a synthetic deer drawing and reached the pinned Qwen3.5-9B worker. The worker loaded the model, completed image preprocessing and inference, then emitted `MODAL_MODEL_OUTPUT_TOKEN_LIMIT` at 512 tokens. The final constrained-parser state reported that the JSON schema could end and model EOS was allowed, but the model did not emit EOS. The worker's terminal failure event became visible about seven seconds after the backend's first log read; the API therefore returned `504 MODAL_OUTCOME_UNKNOWN` even though the call's terminal worker log later identified a known token-limit error.
- **Fix:** Decode and strictly parse the constrained output before rejecting solely because the generation budget was reached. Accept a no-EOS response only when the complete decoded text parses as exactly one schema-valid candidate; do not repair/truncate malformed output. Keep the existing output budget. If parsing fails at the budget, preserve `MODAL_MODEL_OUTPUT_TOKEN_LIMIT` as a terminal failure.
- **Failure classification:** After a non-timeout Modal exception, wait at most 10 seconds for its structured terminal worker event. If `worker_failed` and its allowlisted error code are observed, classify that exact code as terminal; otherwise retain `OUTCOME_UNKNOWN` and do not redispatch. In the StoryRun photo bridge, a confirmed terminal worker failure finalizes the invocation ledger as `FAILED`; if finalization fails, return `UNKNOWN` with a ledger error.
- **Verification:** Add focused tests for valid complete JSON without EOS, malformed/truncated JSON at the token ceiling, delayed terminal-log indexing, and confirmed terminal failure finalization. Update only the already-approved `sketch2life-srs23-drawing-vlm-dev` app once; make one fresh synthetic Parent UI inference for verification. This is a new verification request after a known terminal worker failure, not a retry of the prior request. Do not repeat the Parent guide call or any passing AI workload; no video.
- **Added paths:** `backend/src/sketch2life/infrastructure/ai/modal_function_client.py`, `backend/src/sketch2life/infrastructure/story_run_lite/photo_bridge.py`, and focused tests under `backend/tests/unit/`. Existing `deployment/modal/srs_v23/drawing_vlm_app.py` and its focused Modal tests remain in the existing manifest.
- All other Rev82 no-fixture, no-production-data, no-destructive-reset, no-commit/push/merge, and secret-handling boundaries remain unchanged.

## 15. Evidence-driven Qwen drawing decoder termination

- **Observed evidence:** The fresh Android Parent call after §14 reached Qwen3.5-9B, loaded the pinned model, and completed inference in about 48 seconds. At the final decoder callback, the JSON schema parser reported `can_end=true` and model EOS was allowed, but the allowed token set also permitted continuation. The model generated 512 tokens; strict parsing then rejected trailing extra data (`JSONDecodeError: Extra data`, line 12, column 3). The worker correctly returned a terminal `MODAL_MODEL_OUTPUT_TOKEN_LIMIT`; this was not a cold-start or provider availability failure.
- **Fix:** When the constrained JSON parser reaches a complete schema-valid terminal state, restrict the next-token allowlist to model EOS only. Keep strict whole-output JSON parsing and duplicate-key/schema validation; do not strip trailing output, salvage a JSON prefix, or raise the token ceiling.
- **Verification:** Add focused tests proving EOS is the only allowed continuation after a complete schema state and that incomplete states retain their normal allowed tokens. Run offline contract tests, redeploy only the existing drawing VLM app once, and make one new synthetic Parent UI inference after this fix. The previous call is terminal and will not be retried. Do not repeat the already-passing Flux guide. No video.
- **Added paths:** Existing `deployment/modal/srs_v23/drawing_vlm_app.py` and its focused Modal contract test path only, plus the existing FEAT-063 evidence/context/status files.
- **Scope limits:** The owner's direct Rev82 request to fix AI failures and verify both workflows authorizes this one evidence-driven worker update and one fresh drawing-analysis call. All no-fixture, no-production-data, no-destructive-reset, no-commit/push/merge, and secret-handling limits remain unchanged.

## 11. Evidence-driven Android Metro dependency resolution amendment

- **Observed blocker:** The real Android Expo bundle fails before rendering. Metro 0.81.5 loads `@expo/metro-config` 0.19.12, but that package resolves `metro-cache-key` 0.87.0 from the monorepo root. The Expo 52 / React Native 0.76 worker expects the Metro 0.81.5 callable export and throws `TypeError: metro_cache_key_1.default is not a function`, leaving Metro's transformer unset and returning HTTP 500.
- **Fix:** Add the exact `metro-cache-key@0.81.5` dependency to the existing `@expo/metro-config@0.19.12` pnpm package extension and synchronize the root lockfile. Do not change the mobile UI architecture or upgrade Expo/React Native/Metro; do not alter sibling `apps/mobile` dependencies.
- **Verification:** Resolve the package from the `@expo/metro-config` runtime context and confirm it is 0.81.5, start Metro once, obtain a successful Android bundle, then continue the real Parent UI flow.
- **Added paths:** `pnpm-workspace.yaml` and `pnpm-lock.yaml` only.
- All Rev82 limits remain unchanged: no fixture output, no video, no destructive reset, no production data, no repeat paid Modal calls, and no commit/push/merge.

## 13. Evidence-driven FLUX progression gate adjustment

- **Observed evidence:** The first real Parent guide call failed with `MODAL_PROGRESSIVE_GUIDE_NOT_CUMULATIVE` because total panel ink was required to grow at every step. After changing that check to require new ink in every transition, the next real call failed at the same gate, although FLUX inference itself completed successfully. Modal logs identify the quality heuristic as the only worker failure; API and Modal health remain good.
- **Approved adjustment:** Evaluate progression across the sequence instead of rejecting one quiet transition. At least half of consecutive transitions must add a small amount of new ink. Keep per-panel blank/dense checks, panel layout/count validation, 20% retained-stroke overlap, output schema, draft status, and adult review. Do not accept a sequence with no progression or a material full redraw.
- **Verification:** The focused synthetic gate suite must pass. Update only the existing FLUX dev App once more, then make one final real Parent UI inference. If it still fails, preserve the terminal logs and stop further paid guide calls.
- **Scope/approval:** This explicit owner request to fix the AI quality gate and retest authorizes one additional deployment of `sketch2life-srs23-flux-image-dev` and one final real line-sketch inference. This narrowly supersedes the earlier one-deployment limit for this Flux App only; it does not authorize deployment of Qwen/video Apps, repeated warmups, or other retries.
- **Paths:** Existing approved `deployment/modal/srs_v23/flux_image_app.py`, its focused quality test, and FEAT-063 evidence/context/status records only.
- All other Rev82 safety, data, no-fixture, no-video, no-reset/volume-delete, and no-commit/push/merge restrictions remain unchanged.

## 12. Evidence-driven local seed credential reconciliation amendment

- **Observed blocker:** The local Parent seed identity exists in Firebase Auth Emulator, while the configured `.env` email/password pair fails sign-in with `INVALID_PASSWORD`. The insert-only seed reuses the existing UID but leaves its earlier password unchanged, so a later `.env` update cannot restore a usable local demo login.
- **Fix:** In the local Parent and Teacher seed adapters only, reconcile the password for the exact configured synthetic seed email to the current project-root `.env` value whenever that seed runs. Keep UID/identity ownership conflict checks and all database insert-only behavior; do not print or persist the password outside Auth Emulator and ignored `.env`.
- **Verification:** Re-run each seed idempotently, confirm same UIDs/entity counts and successful sign-in for the configured synthetic accounts through Firebase Auth Emulator; production Firebase is never contacted.
- **Paths:** Existing approved `backend/src/sketch2life/infrastructure/local_demo/` seed family and focused tests under `backend/tests/`; no new path family.
- All Rev82 limits remain unchanged: no fixture output, no video, no destructive reset, no production data, no repeat paid Modal calls, and no commit/push/merge.

## 16. Evidence-driven Parent activity workload allowlist correction

- **Observed evidence:** One real Parent Android activity-suggestion request reached `sketch2life-srs23-language-audio-dev` and was rejected at the worker's `input_envelope` phase with `MODAL_WORKLOAD_NOT_ALLOWED`. The function-call logs show the worker started and failed before reading the request asset or loading Qwen. The local handler and `workloads.json` register `parent.activity.suggest`, but `contracts.py:L4_WORKLOADS` omits it. This is a worker contract mismatch, not cold start, model inference, JSON parsing, or a subjective quality-gate rejection. The activity screen offered only continue/skip after the terminal error; backing up and reconfirming the subject then returned `PARENT_SUBJECT_REVIEW_NOT_ACTIVE`, because subject confirmation had already succeeded.
- **Fix:** Add `parent.activity.suggest` to the L4 allowlist. Add a focused test proving the exact workload envelope is accepted for L4 and remains rejected for the video execution group. Do not broaden the allowlist or weaken input validation. Add a one-time retry action in the Parent activity screen only for a confirmed `MODAL_WORKER_FAILED_TERMINAL`; preserve the skip-to-story option and never offer retry for `MODAL_OUTCOME_UNKNOWN`. When resuming an active run whose subject is already adult-confirmed but story is not generated, resume at the optional activity step instead of asking for subject confirmation again.
- **Verification:** Run the focused offline worker-contract test. Update only the existing `sketch2life-srs23-language-audio-dev` Modal App once and verify its CPU `/health` (completed). Then use the Parent Android UI to sign back in, resume the existing confirmed-subject synthetic run at the activity step, and make one new activity-suggestion inference after the fix. This is a new verification after the allowlist fix; the failed call is terminal and will not be retried. If the post-fix call fails, preserve its logs and stop without another inference. No video and no repeated successful workload.
- **Added paths:** `deployment/modal/srs_v23/contracts.py`, one focused test under `deployment/modal/srs_v23/tests/`, `apps/ui-mobile/src/parent/presentation/screens/ActivityScreen.tsx`, `apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts`, and the already-approved FEAT-063 evidence/context/status files. No other Modal App deployment is authorized by this amendment.
- All existing Rev82 no-fixture, synthetic-data-only, no-production-Auth, no-destructive-reset/volume-delete, no-commit/push/merge, and secret-handling limits remain unchanged.

## 17. Teacher authentication UI test harness correction

- **Observed failure:** `apps/teacher-ui` builds, but two authentication-boundary tests fail because their mocked `authService.observe` invokes the initial signed-out callback and never emits the authenticated user after the mocked Firebase sign-in. The actual gate then correctly refuses the Teacher route. This is a stale test double, not evidence of a production auth defect.
- **Fix:** Update only `apps/teacher-ui/src/__tests__/app.test.tsx` so the observer mock emits the synthetic test user after successful sign-in and the teacher role check is explicitly mocked as `teacher`. Keep the signed-out route denied and the `?demo=1` fixture-only test explicit.
- **Verification:** Run the Teacher Web build and focused Vitest suite; this test correction adds no live account, credential, backend role, or provider request.
- **Added path:** `apps/teacher-ui/src/__tests__/app.test.tsx`.
- All Rev82 real-data, no-fixture, no-video, no-production-auth, no-destructive-reset/volume-delete, no-commit/push/merge, and secret-handling limits remain unchanged.

## 18. Evidence-driven Qwen language JSON termination correction

- **Observed evidence:** One real Parent activity request reached Qwen3.5-9B on a Modal L40S, loaded weights, encoded the prompt, and completed constrained-decoder setup. It then remained in `model_inference` for over 24 minutes without a terminal worker event. A read-only container check showed 0% GPU utilization, about 98% CPU utilization, about 19 GB of model memory, and a running Torch Inductor compile-worker pool. The caller's 15-minute socket wait expired while the Modal call remained active. Inspection of `_build_json_prefix_allowed_tokens_fn` shows it records `parser.can_end()` and whether model EOS is allowed, but returns all allowed tokens even after the schema is complete. The drawing worker already has an EOS-only terminal rule; the shared language worker does not.
- **Fix:** In the shared language-worker decoder, when the incremental JSON parser confirms the full schema is complete, restrict the next-token allowlist to the effective model EOS token IDs only. Preserve normal tokens while the schema is incomplete and retain strict whole-output JSON/schema validation; do not salvage/truncate output. Keep a hard 2,048-token safety ceiling that supports three fallback drafts whether or not catalog candidates were supplied; EOS-only stopping should end compact catalog selections as soon as their schema is complete.
- **Cost containment:** Stop only the identified in-flight synthetic activity worker container after recording its call ID and last phase; do not stop the Modal App or any other container. The call is not retried. After one update of the existing language/audio Modal App, make one fresh Parent activity API inference. If it fails, stop that workload without a second retry.
- **Verification:** Add focused tests for EOS-only after complete schema, unchanged allowed tokens while incomplete, and multiple model EOS IDs. Run relevant offline Modal/backend tests. Then exercise one live Parent activity inference and one real Teacher lesson-plan/deck workflow if the shared App completes them within the approved 30-minute workload bound; no video.
- **Added paths:** `deployment/modal/srs_v23/language_audio_app.py`, focused tests under `deployment/modal/srs_v23/tests/`, and the existing FEAT-063 evidence/context/status files.
- All Rev82 synthetic-only, no-fixture, no-production-Auth, no-destructive reset/volume-delete, no-commit/push/merge, and secret-handling boundaries remain unchanged.

## 19. Moderate Parent activity JSON and quality contract

- **Scope:** Align the constrained Modal JSON schema, worker parser, backend Pydantic response contract, and Parent activity service checks so harmless punctuation/wording differences do not reject a useful result. Use bounded but practical text maxima: title 80, objective 160, materials 120, preparation 180, instructions 320, observation 120, safety 140 characters. Remove sentence-ending punctuation patterns and the exact required phrase `trẻ tự chọn`.
- **Moderate quality checks:** Keep exactly three fallback drafts; outdoor kind and a recognizable outdoor setting per activity; each activity remains linked to the confirmed subject/context; each has nonempty objective/instructions/safety notes; adult guidance, child agency, and exploration language must appear across the suggestion set rather than being repeated verbatim in every item. Allow reasonable variation in activity wording and methods; use less brittle similarity thresholds while still rejecting duplicates.
- **Unchanged hard gates:** Strict single-object JSON, exact keys/types, schema and age-band validation, catalog-first selection, only parent-accessible exact-age published/shared lesson candidates, excluded-activity handling, adult review/selection, non-Latin-script rejection, PII filtering, unsafe-material/action blocking, outdoor scope, and no unauthorized child/profile data. No JSON repair, prefix salvage, or retry of unknown provider outcomes.
- **Tests:** Add acceptance cases for concise Vietnamese without terminal punctuation and for one activity omitting repeated agency phrasing while the set retains child-centered/adult-guided intent. Retain rejection tests for malformed JSON, unsafe actions, PII, wrong activity kind, wrong age, excluded/duplicate items, and missing required fields.
- **Added paths:** `backend/src/sketch2life/application/services/parent_activity_suggestions.py`, `backend/src/sketch2life/contracts/schemas/modal_ai.py`, `backend/tests/unit/test_parent_activity_suggestions.py`, and `backend/tests/unit/test_parent_activity_worker_contract.py`.
- All prior Rev82 synthetic-only, no-fixture, no-production-Auth, no-video, no-destructive reset/volume-delete, no-commit/push/merge, and secret-handling constraints remain unchanged.

## 20. Evidence-driven Teacher lesson-visual progression gate

- **Observed evidence:** One real authenticated Teacher `POST /api/teacher/v1/organizations/{organization_id}/ai/lesson-visuals` request reached the pinned FLUX.3 worker. Firebase/Auth, role and organization authorization, request-envelope validation, reviewed-plan contract, GPU preflight, Qwen prompt upsampling (54.7 s), FLUX model load (6.3 s), and image inference (6.7 s) succeeded. The worker then failed at `progressive_panel_quality_gate` with terminal `MODAL_PROGRESSIVE_GUIDE_STROKES_CHANGED`; the API returned HTTP 502 after 380.9 s total. This is a subjective cumulative-stroke overlap gate failure, not cold start, model load, GPU, API authorization, or parser failure. The failed function call is terminal and will not be retried.
- **Fix:** Keep panel count/layout, minimum/maximum ink, and sequence-level meaningful-progression checks. Permit at most one low-retention transition in an 8-step guide when the remaining transitions preserve the earlier drawing; retain a 12% minimum retained-stroke floor with the existing spatial tolerance. Emit a sanitized worker diagnostic containing only transition index, measured overlap, threshold, and coverage so future failures identify the exact transition. Continue returning a review-required draft; do not auto-approve or publish the image.
- **Verification:** Add offline image-mask tests for the tolerated single transition and continued rejection of full redraw/no-progression. Deploy only the already-existing FLUX image App once after tests, then make one new authenticated Teacher lesson-visual API inference from the same already-reviewed synthetic lesson request. This is the single post-fix verification call; if it fails or has an unknown outcome, record it and stop without another call. No new Qwen, Parent guide, or video inference for this correction.
- **Added paths:** Existing `deployment/modal/srs_v23/flux_image_app.py`, focused tests under `deployment/modal/srs_v23/tests/`, and FEAT-063 plan approval/evidence/context/status records.
- **Safety:** Synthetic lesson data only; no production Auth, no fixture counted as success, no destructive reset or volume deletion, no commit/push/merge, and no secret exposure.

## 21. Modal deploy client encoding recovery

- **Observed deployment blocker:** The approved FLUX app deployment began building Modal images, then failed before app publication when the Windows Python client could not encode a Unicode dependency-install log using the active legacy `charmap` codec. No inference, GPU allocation, or worker warmup was started.
- **Recovery:** Run the same already-approved FLUX app deployment once with `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8`. This is a client-runtime encoding fix; it does not change the app, workload, model, or test scope.
- **Verification:** Confirm deployment completion and the existing app health endpoint, then make the single approved authenticated synthetic Teacher lesson-visual API request. If deployment fails again, or the request fails/has unknown outcome, stop and record it. No additional app deploy, warmup, Parent guide, Qwen, or video calls.
- **Scope:** This amendment allows one successful deployment attempt because the first attempt failed during local client log encoding before app publication. It does not increase the approved number of AI inference calls.
- **Added paths:** No additional code paths; existing FLUX app and the approved FEAT-063 evidence/context/status records only.
- **Safety:** Synthetic-only verification; no production Auth, no fixture counted as success, no destructive reset or volume deletion, no commit/push/merge, and no secret exposure.

## 22. Owner-approved final bounded FLUX and Parent verification — 2026-11-12

- **Owner approval:** The owner explicitly selected “Tiếp tục một lượt giới hạn” after the §21 stop. This supersedes §21 only for the exact deployment/inference bounds below.
- **Observed evidence:** The post-fix Teacher visual worker completed FLUX inference, then failed because one transition retained 9.46%, below the 12% floor; the other observed transitions retained 81.55–90.53%. The API returned a terminal 502. No retry was sent.
- **Gate change:** Keep a 20% soft threshold. For an 8-step guide only, permit at most one transition below 20% if it retains at least 8% of prior-panel ink. Reject any transition below 8%, a second low transition, invalid/blank/dense panel, invalid layout, or sequence without meaningful progression. Keep all draft, adult-review, output-schema and safety checks.
- **Offline verification:** Extend mask tests to prove an approximately 9.5% single transition passes, a transition below 8% fails, a second low transition fails, and no-progression/full-redraw cases remain rejected.
- **Bounded deployment and Teacher call:** Deploy the existing FLUX dev App once, verify only its CPU `/health`, and submit one authenticated synthetic Teacher visual request from the same already-reviewed lesson. No warmup, Parent guide, Qwen plan/deck call, repeat call or video. If this visual request fails or is unknown, stop the remaining AI work.
- **Conditional Parent calls:** Only if the Teacher visual API call passes, create one new Parent account via the real local registration API and Firebase Auth Emulator; create one synthetic profile/consent grant and StoryRun; use the existing generated synthetic deer drawing. Submit drawing-understanding once; require the model output to match the image/topic and explicitly confirm the subject as the adult. Then call catalog-first activity suggestions once and story generation once, choosing one returned activity as the test adult. Each call is sequential, has a 30-minute client bound, and is never retried. Stop downstream steps if a prerequisite fails, is unknown or mismatches. Reuse the existing successful Parent line-sketch artifact; do not regenerate it.
- **Hard cap:** At most four new GPU inference calls total: one FLUX lesson visual, then (only if it passes) one Parent drawing, one Parent activity, and one Parent story call. Parent calls do not run concurrently. No video, no production Auth, no real child data, no fixture responses, no destructive reset/volume deletion, no shared Modal App stop, no commit/push/merge.
- **Evidence:** Save sanitized per-call timings/errors, complete AI JSON outputs, the generated Teacher visual image if accepted, the Parent drawing-analysis/activity/story responses, and the final Docker/Modal container state under the existing EV-063-90 evidence folder. Do not save account credentials, Firebase ID tokens or secrets.
