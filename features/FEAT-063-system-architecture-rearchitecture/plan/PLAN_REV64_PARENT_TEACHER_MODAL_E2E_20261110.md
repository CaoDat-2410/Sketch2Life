# Plan Rev64 — Parent/Teacher Modal AI integration and E2E evidence

**Status:** APPROVED scope; execution is **PARTIAL** because Parent drawing-understanding returned invalid Qwen JSON and the Parent story gate could not be reached. Approval hashes and the outcome are recorded in `approvals/TASK_APPROVAL.md`.
**Date:** 2026-11-10
**Authority:** Canonical FEAT-063 SRS v2.7-draft, §§5.1–5.2, 6.2, 7, 9, 21, 25, 28–29 and 31.4–31.5. The SRS remains unsigned. Use §32 only as an environment-specific as-built snapshot.

## Goal

Connect the active Parent Android and Teacher Web applications to the local backend and the existing development Modal AI functions. Run one low-cost, synthetic-data vertical slice per role and capture screenshots/log evidence. Preserve the separate Parent/Teacher account and data scopes.

## Current verified baseline

- The root `.env` now has the owner-provided Firebase Web API key. A non-mutating Identity Toolkit probe and a synthetic reset/sign-in/change-password lifecycle passed; see EV-063-73.
- The Parent app currently mounts `FixtureFlowScreen` after authentication. That screen labels itself a fixture and its “fixture AI” button makes no provider request.
- Teacher Web has authenticated route gating and BE1 session setup services, while multiple lesson/AI pages are explicitly wrapped as prototypes. `activityService` and `videoService` still return empty fixture values.
- Backend `SKETCH2LIFE_AI_PROVIDER` is `disabled`; current provider settings expose `disabled`, `lightning_dev`, and `runpod`, with no Modal adapter or Modal endpoint configuration in the root `.env.example`.
- FEAT-063 §32.2 records Modal development functions for Qwen story/storyboard, FLUX line-sketch, Whisper ASR, TTS and a WAN video candidate; it also states that those functions were not proven connected to the main backend. Exact deployed contracts and availability must be rechecked before calling them.
- Modal SDK 1.6.3 is installed in the ignored `backend/.venv`; the authenticated profile is `docaodat24-10`. The current checkout is `backup/dev-before-dedup-20261106-575139a5`, which does not contain deployment source. Source is present on local `dev` at `1431ef81972b71303fd4a7909748fd3005769a3c`. Earlier Rev52/Rev44 evidence records synthetic worker/API results, then stops the task-used apps at 0 tasks; the current empty Modal app list is consistent with that cleanup and does not mean the source or prior tests are absent. Those results are worker/API-level, not UI-to-backend-to-Modal acceptance. The profile's local secret material must never be printed, copied to logs, or committed.

## Approved scope

1. Reuse the existing non-video deployment source and versioned worker contracts from `dev` at the pinned commit above. Deploy only the existing apps required by this bounded run into authenticated `docaodat24-10/dev`: `sketch2life-srs23-drawing-vlm-dev`, `sketch2life-srs23-language-audio-dev`, and `sketch2life-srs23-flux-image-dev`. Use existing Modal Secrets and Volumes as-is; do not create/change secrets, weights, Volumes, or GPU settings. Stop the task-used apps after testing and verify zero active tasks.
2. Add or restore the backend-owned provider adapter and versioned HTTP contracts for the required non-video AI operations, using only the confirmed worker contracts:
   - Parent optional generic line-sketch guide through the deployed FLUX candidate.
   - Parent synthetic drawing understanding/story/storyboard through the deployed Qwen candidate.
   - Teacher AI lesson/activity draft and optional sketch deck through the deployed Qwen/FLUX candidates, only from Teacher-reviewed structured allowlisted fields.
   - Whisper ASR may be exercised once with a synthetic, non-person recording if the deployed function is available and its contract is confirmed.
3. Configure Modal only through the repository-root `.env` and `compose.yaml`/backend settings. No provider endpoint, token, or secret may be placed in React Native/Web bundles or committed. Keep the existing user `.env` ignored by Git.
4. Connect the Parent app to Firebase `/api/auth/v1/me` and the backend workflow. The tested route must not mount, call, or accept fixture behavior as success; fixture screens/services are not part of the E2E path. Keep the optional sketch off by default and send no child profile, age, voice, photo or artwork to the line-sketch function.
5. Connect Teacher Web to real lesson/filter/review and AI endpoints for the scoped draft/deck flow. Teacher must review and approve extracted structured fields before any content is sent to AI. Do not send source lesson files or raw extracted document text to Modal.
6. Keep Lightning out of these active Parent/Teacher flows. Preserve historical/research files unless removal is required by an approved source manifest; do not silently route to Lightning as fallback.
7. Run local Docker/API/UI services as needed, preserving services and volumes already running. Use one disposable PostgreSQL database with `rev64_e2e` in its name. Use only synthetic Firebase accounts and generated/synthetic drawing/audio inputs; delete all test identities and disposable records afterward.
8. Run bounded live Modal calls: at most one call for each distinct AI operation in each role flow, no repeated retries except a single explicitly approved transport retry, and no video generation. Stop AI calls for a function after its first contract/provider failure and report the exact sanitized cause.
9. Capture Parent and Teacher runtime screenshots in the feature-local evidence folder using an isolated/headless browser or emulator, not the owner's interactive computer. Record when a platform cannot be rendered in an isolated runtime; screenshots alone do not establish behavior.
10. Update the API contract, feature context, decisions, source register, status, evidence index and evidence record. Do not change the canonical SRS requirements or claim video completion.

## Explicit exclusions and safety limits

- No video generation, LTX/WAN inference, TTS, payment, production deployment, real child data, real recipient email, or modification of the pre-existing shared development database. The bounded development deployment above must be stopped after evidence capture.
- No app-to-Modal direct call; provider credentials stay backend-side.
- No public lesson publishing. Teacher AI results remain drafts for human review.
- If the existing Modal Secret/model Volumes are unavailable, or the deployed functions do not match the confirmed versioned contract, do not create replacements, infer a payload, or fall back to Lightning. Stop that AI path and record the blocker.
- Do not commit or push.

## Acceptance criteria

- Parent Firebase sign-in resolves `parent` through the backend role endpoint. A synthetic parent can enter the real Parent screen and use a synthetic drawing to complete the available pre-video flow with explicit adult subject/story review. No fixture route or deterministic fixture response is used for a passing result.
- Parent line-sketch AI runs only after the adult enables it; request metadata shows no child/profile/image/audio payload. If disabled, no sketch job or Modal call is created.
- Parent Qwen output satisfies the backend contract and SRS constraints (5–15 story scenes, Vietnamese, child-centered, no adult direct scene edits); the parent must explicitly confirm the generated story before the test reaches its stopping state. Since video is excluded, the run remains pre-video and is not marked complete.
- Teacher Firebase role resolves as `teacher`; non-Teacher role is denied the Teacher route. A synthetic Teacher can provide a text-only lesson, review structured extraction, request a draft suggestion/deck from Modal, and review the result. Original file/raw text is never included in the Modal request.
- Modal functions are called only through backend adapters. Request IDs, provider/model labels, status/latency and sanitized failure codes are captured without prompts, images, transcript, identity, token, or secret values.
- Both role workflows are driven from the connected Parent/Teacher UI (real login and UI actions) through the backend and live Modal inference, with the generated result visible in the same UI flow. A direct backend/API-only test, health check, build or fixture result does not satisfy E2E acceptance.
- Frontend build/typecheck pass as supporting checks only. Parent/Teacher screenshots and a sanitized UI-to-backend-to-Modal run log are stored under the approved evidence path.
- Disposable database, synthetic Firebase users and runtime containers are cleaned up; pre-existing services/volumes remain as they were.

## Verification and evidence plan

- Read-only Modal app/function discovery first; record exact app/function/model revision if exposed.
- Use `/health` and service checks only as preflight; they are not acceptance evidence for workflow completion.
- Parent UI flow: sign in/register in the real Parent UI → real Parent route/role gate → synthetic parent-owned test profile and generated artwork → enable optional FLUX guide in the UI → view generated guide → upload/capture the synthetic drawing in the UI → request Qwen understanding/story in the UI → review and confirm subject/story in the UI. Stop before video admission.
- Teacher UI flow: sign in in Teacher Web → real Teacher route/role gate → upload lesson text in the UI → review/approve structured extracted fields in the UI → request Qwen lesson/activity draft and FLUX sketch deck in the UI → review the actual Modal results in the UI. No video.
- Observe each operation from the UI and correlate its sanitized request/job ID with backend logs and Modal result/timing. API-only invocation does not substitute for a missing UI action or displayed result.
- Capture screenshots for login/role landing, AI-in-progress/result and review states for each supported client. Store sanitized logs and exact durations alongside screenshots.
- Record API and AI operation results individually as PASS, FAIL, or BLOCKED; do not convert an unavailable provider into fixture success.

## Exact path manifest

### FEAT-063 records and evidence

- `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV64_PARENT_TEACHER_MODAL_E2E_20261110.md`
- `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
- `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
- `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
- `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
- `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-74_PARENT_TEACHER_MODAL_E2E_20261110.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-74_PARENT_TEACHER_MODAL_E2E_20261110/screenshots/`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-74_PARENT_TEACHER_MODAL_E2E_20261110/logs/`

### Shared configuration and backend

- `.env.example`
- `compose.yaml`
- `backend/pyproject.toml`
- `backend/src/sketch2life/infrastructure/config/settings.py`
- `backend/src/sketch2life/infrastructure/identity/firebase_token_verifier.py` (bounded clock-skew tolerance required by the observed Firebase/backend clock offset; signature, issuer, audience and role validation remain unchanged)
- `backend/src/sketch2life/interfaces/http/app.py`
- `backend/src/sketch2life/interfaces/http/router_composition.py`
- `backend/src/sketch2life/application/ports/modal_ai.py` (new, if required)
- `backend/src/sketch2life/contracts/schemas/modal_ai.py` (new, if required)
- `backend/src/sketch2life/infrastructure/ai/modal_client.py` (new, if required)
- `backend/src/sketch2life/infrastructure/ai/modal_function_client.py` (restore the existing versioned client from `dev`, then adapt only where this approved UI path requires it)
- `backend/src/sketch2life/infrastructure/ai/modal_providers.py` (new, if required)
- `backend/src/sketch2life/interfaces/http/routers/parent_ai.py` (new, if required)
- `backend/src/sketch2life/interfaces/http/routers/teacher_ai.py` (new, if required)
- Existing API routers/services may be edited only when necessary to mount/use these versioned Modal-backed contracts: `backend/src/sketch2life/interfaces/http/routers/images.py`, `backend/src/sketch2life/interfaces/http/routers/live_understanding.py`, `backend/src/sketch2life/interfaces/http/routers/lesson_library.py`, `backend/src/sketch2life/application/services/story_video_planner.py`, `backend/src/sketch2life/application/services/sketch_generation.py`.

### Parent Android

- `apps/mobile/src/app/AppRoot.tsx`
- `apps/mobile/src/features/auth/ParentAuthScreen.tsx` (narrow accessibility repair; approved scope addendum below)
- `apps/mobile/src/features/fixture/FixtureFlowScreen.tsx`
- `apps/mobile/src/infrastructure/api/liveUnderstanding.ts`
- `apps/mobile/src/features/parent/ParentWorkflowScreen.tsx` (new, if required)
- `apps/mobile/src/infrastructure/api/parentWorkflowApi.ts` (new, if required)
- `apps/mobile/src/infrastructure/auth/firebaseAuthSession.ts`

### Teacher Web

- `apps/teacher-ui/src/App.tsx`
- `apps/teacher-ui/src/pages/ContentAuthoringPage.tsx`
- `apps/teacher-ui/src/pages/SessionSetupPage.tsx`
- `apps/teacher-ui/src/services/apiClient.ts`
- `apps/teacher-ui/src/services/authService.ts`
- `apps/teacher-ui/src/services/sessionService.ts`
- `apps/teacher-ui/src/services/aiWorkflowService.ts` (new, if required)
- `apps/teacher-ui/src/pages/ModalAiLessonFlowPage.tsx` (new, if required)

### Existing Modal worker source from `dev` — restore only non-video files required by this plan

- `deployment/modal/srs_v23/contracts.py`
- `deployment/modal/srs_v23/worker_observability.py`
- `deployment/modal/srs_v23/drawing_vlm_app.py`
- `deployment/modal/srs_v23/flux_image_app.py`
- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/README.md` (only if the runbook needs a scoped update)

Any source path outside this manifest requires an addendum and updated hash/approval before editing.

## Scope clarification — no fixture E2E

The owner clarified on 2026-11-10: “nối end to end 2 luồng đó vf test đi, ko test fixture”. This supersedes any ambiguous reading of “preserve an explicit fixture/dev route separately” above. The approved test path must exercise real Firebase auth, real backend APIs and live Modal functions only; fixture code may remain in the repository but is never invoked or counted as E2E success.

## Scope clarification — UI-driven end-to-end acceptance

The owner further clarified on 2026-11-10: both flows must be connected through their actual user interfaces; API/backend-only tests and smoke tests do not count as workflow E2E. Acceptance requires a real Parent UI path and a real Teacher Web path, each traversing Firebase role resolution, backend workflow endpoints, a live Modal function, and visible reviewed output. `/health`, API probes and builds remain preflight/supporting checks only. This clarification does not authorize video generation.

## Scope clarification — recovery call after a confirmed UI render defect

The first Parent line-sketch request completed successfully in Modal, but Android crashed while rendering the successful response because React Native rejected `accessibilityRole="status"`. The worker result was not displayed or persisted by the Parent UI. The owner's direct instruction requires the real UI workflow to work end to end and allows necessary UI fixes. After replacing the unsupported role with `accessibilityLiveRegion="polite"`, one additional Parent line-sketch call is allowed solely to confirm that the same live result now renders. This is the only exception to the one-call-per-operation limit; it does not authorize retry after any provider, contract, timeout or safety failure. No video generation is authorized.

### Plan Rev64 scope addendum — Parent Auth screen accessibility repair

- **Status:** APPROVED as a narrow UI repair required by the owner-authorized real Firebase UI flow.
- **Observed blocker:** The Parent sign-in/sign-up screen used the same unsupported React Native `accessibilityRole="status"` value that crashed the Parent workflow screen before rendering.
- **Added path:** `apps/mobile/src/features/auth/ParentAuthScreen.tsx`.
- **Change:** Replace the unsupported status role with `accessibilityLiveRegion="polite"`; authentication behavior and API contracts are unchanged.
- **Basis:** The owner directed a real UI-to-backend-to-Modal E2E for both roles; this accessibility-only path was necessary to exercise Parent login through the actual app.

## Rev64 execution outcome — 2026-11-10

- Local `dev` and `origin/dev` both point to `1431ef81972b71303fd4a7909748fd3005769a3c`. The Modal app source already exists on `dev`; temporary deployment was needed because the previous test run had stopped the apps.
- Parent Firebase registration and backend role resolution passed through Android UI. The optional FLUX line-sketch request passed after one approved recovery call and its result rendered in the app.
- Parent drawing-understanding did not pass: UI request `f54c995f-64dd-43cf-bc22-622f34b74de3` returned HTTP 504 / `MODAL_OUTCOME_UNKNOWN`. Modal call `fc-01M71JFYS8YR7V5CM5TC6MABTX` reached Qwen3.5-9B inference, generated 256 tokens, then failed strict JSON parsing with `MODAL_MODEL_OUTPUT_INVALID` (`JSONDecodeError: Unterminated string`). No retry was made. Parent story generation and adult subject confirmation are BLOCKED by that failed prerequisite.
- Teacher Firebase role resolution passed through Teacher Web. Qwen lesson suggestion, Qwen Sketch Deck and FLUX lesson visual each returned HTTP 200 and rendered in the Teacher UI. The teacher reviewed/edited the draft before deck generation. The page uses structured authoring fields; raw lesson-file upload/parser review was not exercised.
- Teacher results used Qwen/Qwen3.5-9B at revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`; FLUX results used `black-forest-labs/flux-3-image-klein` at revision `09561231f44e41381c461caf53d5452005a60ac9`.
- No video request was made. All three task-used Modal apps were stopped and verified at zero tasks. The two synthetic Firebase users and disposable `rev64_e2e` database were deleted; task-started Postgres/Redis and the emulator were stopped. Existing API/ClamAV services were preserved.
- Overall Plan Rev64 acceptance remains PARTIAL: Parent story review was not reached, and Teacher upload/parser is absent from the exercised screen. Exact timings, screenshots and worker evidence are recorded in EV-063-74.

### Plan Rev64 scope addendum — one Qwen drawing output-cap recovery

- **Status:** APPROVED under the owner’s direct instruction to fix and test the non-video AI workflows, together with the current direction to verify the source on `dev`.
- **Observed root cause:** Modal logs show Qwen3.5-9B reached `model_inference`, emitted exactly 256 tokens, and then failed strict JSON parsing. `deployment/modal/srs_v23/drawing_vlm_app.py` pins `MAX_OUTPUT_UNITS = 256`; this matches the observed truncation.
- **Approved code change:** Raise only the drawing-understanding worker’s bounded `MAX_OUTPUT_UNITS` to 512. Keep the output schema, constrained decoder, strict parser, model pin, GPU preferences, and business rules unchanged. Do not add fallback or soften validation.
- **Approved recovery:** Redeploy only `sketch2life-srs23-drawing-vlm-dev` and make exactly one additional drawing-understanding request through the real Parent UI. If it returns a valid candidate, the adult may confirm/edit it in the UI and the first Parent story-generation call may proceed once. No further retry is permitted for either operation.
- **Boundaries:** Use only a synthetic drawing and a newly created disposable synthetic Parent identity. The identity and `rev64_e2e` database from the prior run were already deleted during cleanup and must not be assumed to exist. Recreate only the disposable database and Parent identity needed to drive this recovery through the real UI; remove both afterward. No profile/media from a real child; no video, other Modal workload, secret/Volume/GPU change, backend-only invocation, commit, or push. Stop the drawing app and verify zero tasks after the bounded recovery.
