# Plan Rev84 — Teacher SVG Illustration through Modal and real UI

**Status:** PLANNED — implementation may start only after the task approval record below is appended to `approvals/TASK_APPROVAL.md` with this plan's SHA-256.

**Date:** 2026-11-13<br>
**Canonical requirements:** FEAT-063 v2.7-draft Rev69, unsigned; `docs/context/SRS_AUTHORITY.md`<br>
**Worktree:** `codex/feat063-parent-docker-modal-seed-20261111`<br>
**Objective:** Add and exercise one real Teacher Web → backend → Modal Qwen3.5 → validated SVG → browser-rendered draft path.

## 1. Why this work is needed

Rev69 records that the Teacher SVG editor is catalog/manual only and that no Modal or UI runtime behavior was verified. The current authenticated Teacher AI router has lesson-plan, sketch-deck and raster visual routes, but no structured SVG illustration workload. The current SVG editor renders catalog documents and line guides; it has no AI-generated illustration preview. The repository's existing SVG files are fixtures, icons or prior generated assets without a reviewed source/license record, so none is eligible as a production dataset for this test.

The owner explicitly requested a real UI test connected to Modal and confirmed: “ko làm fixture, làm real nhé”. Docker Engine may be used if its API is reachable. An Android emulator is available, but this bounded slice targets Teacher Web because the requested output is a Teacher presentation illustration.

## 2. User-visible flow

1. A signed-in Teacher opens **Minh họa SVG AI** in Teacher Web.
2. The Teacher enters a topic and target age in months. No child profile, drawing, personal data, arbitrary URL, uploaded file or fixture response is sent.
3. The UI calls the authenticated Teacher organization API.
4. In local development only, the backend dispatches the allowlisted `teacher.svg-illustration.generate` workload to the existing Modal language/audio app running pinned Qwen3.5.
5. Modal returns bounded structured `SvgDocumentV1` JSON, not executable SVG markup. The backend validates the output schema, converts it through the existing SVG sanitizer/canonicalizer, enforces path-count/geometry/size limits and returns a non-persisted `DRAFT` with model provenance and `review_required=true`.
6. The UI renders the returned document with native SVG path elements and labels it as an unreviewed draft. The Teacher may inspect it and discard it; this slice does not save it to a lesson/catalog or publish it.

The live acceptance prompt will be entered by the Teacher during the UI run (a non-personal topic such as an animal/object). The successful result must come from that real Modal call. No fixture, canned SVG, fake provider, test stub or prior output may be displayed as the live result.

## 3. Scope

- Add a versioned request/response contract for a Teacher SVG illustration draft.
- Add a separately gated, local-development-only authenticated API route:
  `POST /api/teacher/v1/organizations/{organization_id}/ai/svg-illustrations`.
- Add `teacher.svg-illustration.generate` to the Modal worker allowlist and bind it to one named function in the existing language/audio app and the pinned Qwen3.5 checkpoint.
- Use constrained JSON decoding and strict worker/backend validation. Never accept model-generated XML/HTML/JavaScript or references to external resources.
- Reuse the existing SVG sanitizer/canonicalizer; reject malformed geometry, unsupported commands/colors, duplicate paths, fewer than four drawable paths, over-limit output, or invalid metadata as a terminal error.
- Add a dedicated Teacher UI page, authenticated service call, typed output and safe inline SVG renderer.
- Add a setting `SKETCH2LIFE_SVG_ILLUSTRATION_GENERATION_ENABLED`, default `false`; local inference requires both `ai_provider=modal_dev`, local/test environment, and this capability flag. Docker Compose passes the flag as a normal environment variable with a false default; no additional `.env` file or secret is introduced.
- Add focused offline contract tests and execute a real browser/API/Modal flow with one new model inference.
- Capture the real SVG response, rendered UI screenshot, sanitized logs, timing and final Modal app/container state under the feature evidence folder.
- Update FEAT-063 context/status/source register/evidence index and append an environment-specific §32 as-built note only after observing actual results. §§1–31 remain unchanged; flags remain off by default.

## 4. Out of scope

- No fixture or canned content in the product flow or live acceptance run.
- No external dataset import. No current repository SVG is used as a prompt dataset, training set, catalog source or acceptance result. A later dataset task requires verified provenance/license and review records.
- No FLUX call, FLUX removal, image-to-SVG conversion, raster-image generation, Parent Android workflow, line-guide synthesis, presentation persistence, catalog insertion, educator approval, public sharing, video, LTX, database migration, real child data, production account, or public deployment.
- No change to the existing lesson-plan, sketch-deck, raster-visual, Parent or video API behavior.
- No automatic retry. No second inference to tune prompts or quality gates. No minimum Modal containers or persistent warm pool.
- No commit, push, merge, destructive cleanup, `.env` edit, secret display or use of production credentials.

## 5. API and AI contracts

### Request

`TeacherSvgIllustrationDraftRequestV1`:

- `contract`: exact version string.
- `topic`: 1–120 Unicode characters after trimming.
- `target_age_months`: integer 36–120.
- `visual_style`: a small server allowlist; the caller cannot supply instructions, URLs, SVG source, file content or model parameters.

The worker input is a separately versioned `sketch2life.teacher-svg-illustration-input.v1` object with the same minimized fields. It is staged by the existing Modal JSON client under the normal job/generation/attempt envelope.

### Output

`TeacherSvgIllustrationDraftV1`:

- `status: DRAFT`, `review_required: true`, `persisted: false`.
- pinned model ID/revision and Modal request/call identifiers.
- `title_vi`, `alt_text_vi`, and `document: SvgDocumentV1`.
- canonical SVG/document SHA-256 and path count.

The model returns only JSON fields (`schema_version`, `view_box`, bounded `paths[]` with stable `path_id`, path data, fill, stroke and stroke width). Backend sanitization and canonical validation are authoritative. The response is rendered from structured path data, never via `dangerouslySetInnerHTML` or a remote URL.

### Runtime gating

The new workload is disabled by default. It is callable only when all of these are true: Teacher organization authorization succeeds, `SKETCH2LIFE_AI_PROVIDER=modal_dev`, environment is local/test, and `SKETCH2LIFE_SVG_ILLUSTRATION_GENERATION_ENABLED=true`. A disabled flag returns `CAPABILITY_DISABLED` without Modal dispatch. There is no FLUX or alternate-workload fallback.

## 6. Acceptance criteria

### Source and offline checks

- Strict request/output schemas reject unknown fields, invalid age/topic, invalid path geometry and output outside size/count limits.
- The worker's JSON schema, workload registry, Modal function name, backend dispatch map and API workload name agree exactly.
- The endpoint rejects unauthenticated, non-Teacher, wrong-organization, non-local-provider, or disabled-capability calls before dispatch.
- Sanitizer output contains only canonical vector geometry; response is a non-persisted draft and does not become an approved asset.
- Teacher UI uses the real authenticated API service and renders only the validated structured result.
- Relevant focused tests, typecheck/build and `git diff --check` pass. Test doubles may be used only in unit/contract tests and never as evidence of the live UI workflow.

### Real end-to-end acceptance

- Use Docker-backed local services if available, a real local Teacher sign-in/organization and the browser UI. Do not use a mock server, fixture user response, canned lesson output, or direct-only API call as a substitute for UI testing.
- Modal dev app health is checked before generation; the exact pinned Qwen3.5 model status is confirmed through available readiness/log evidence before the one UI-triggered inference. The endpoint itself must be the source of the generated output.
- One and only one new GPU inference is dispatched from the UI. The returned output passes backend validation/sanitization, the UI renders it, and the screenshot/evidence contains the actual generated paths and a visible draft/review label.
- Record wall time, Modal call ID, workload, model revision, worker phase/error diagnostics, API status, path count, output hash, screenshot path, and final app/container state. Never record credentials, bearer tokens, raw auth headers or personal data.
- No success claim if the call times out, has unknown outcome, fails validation, returns no image/vector, or cannot be visibly rendered. Stop after that outcome; do not retry under this plan.
- Turn the local SVG capability flag back off after the run. Do not stop or change unrelated Modal apps/containers. If a task-specific container remains after a terminal run, confirm it has scaled down; do not stop shared apps without identifying ownership.

## 7. Cost, timeout and stop limits

- One deployment/update of only `sketch2life-srs23-language-audio-dev` is permitted if the named function is not already deployed. No other app is deployed or started.
- One CPU `/health` check before the inference. No separate GPU warm-up/readiness invocation; that would create extra billable startup without proving the UI flow.
- Maximum: one UI-triggered Qwen3.5 model inference, no retry, no video, no FLUX, no dataset download. Use the worker's approved 1,800-second hard timeout; report elapsed time if it reaches the cap. Unknown outcome is terminal for this plan.
- Keep Modal `min_containers=0` and the existing bounded `max_containers`; no always-on GPU or idle warm pool. After the test, verify whether the worker container has scaled down and report any ongoing container explicitly.
- Stop before deploy/inference if Docker or local auth infrastructure cannot be accessed, required Modal app/credential is unavailable, model readiness is unverified, the pinned checkpoint is missing, or the estimated billable action differs from this scope. Do not expose or print secret values to diagnose.

## 8. Exact file manifest

Only these paths may be edited for this plan. Any additional source path requires a written amendment before editing.

1. `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV84_TEACHER_SVG_MODAL_UI_REAL_20261113.md`
2. `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
3. `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (append §32 as-built facts only; do not modify §§1–31)
4. `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
5. `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
6. `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
7. `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`
8. `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`
9. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-94_TEACHER_SVG_MODAL_UI_20261113/REPORT.md`
10. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-94_TEACHER_SVG_MODAL_UI_20261113/generated-svg-draft.json`
11. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-94_TEACHER_SVG_MODAL_UI_20261113/generated-svg-draft.svg`
12. `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-94_TEACHER_SVG_MODAL_UI_20261113/teacher-svg-draft.png`
13. `deployment/modal/srs_v23/contracts.py`
14. `deployment/modal/srs_v23/language_audio_app.py`
15. `deployment/modal/srs_v23/workloads.json`
16. `deployment/modal/srs_v23/tests/test_teacher_svg_illustration_contract.py`
17. `backend/src/sketch2life/contracts/schemas/svg_engine.py`
18. `backend/src/sketch2life/infrastructure/ai/modal_function_client.py`
19. `backend/src/sketch2life/infrastructure/config/settings.py`
20. `backend/src/sketch2life/interfaces/http/routers/teacher_ai.py`
21. `backend/src/sketch2life/interfaces/http/openapi_contract.py`
22. `backend/tests/contract/test_teacher_svg_illustration.py`
23. `compose.yaml`
24. `apps/teacher-ui/src/App.tsx`
25. `apps/teacher-ui/src/components/TeacherLayout.tsx`
26. `apps/teacher-ui/src/domain/svgGuide.ts`
27. `apps/teacher-ui/src/pages/TeacherSvgIllustrationDraftPage.tsx`
28. `apps/teacher-ui/src/components/SvgDocumentPreview.tsx`
29. `apps/teacher-ui/src/services/svgIllustrationService.ts`
30. `apps/teacher-ui/src/__tests__/teacherSvgIllustrationDraft.test.tsx`
31. `backend/tests/contract/test_app_composition.py` (add the explicitly approved route/schema to the mounted-API contract expectations)
32. `apps/teacher-ui/src/services/svgCatalogService.ts` (replace pre-existing TypeScript parameter properties that block the requested UI build under `erasableSyntaxOnly`)

## 9. Execution order

1. Freeze this plan and record direct owner approval plus its exact SHA-256.
2. Implement the worker and strict contracts; add offline tests; verify workload/function/model mapping.
3. Implement the gated backend endpoint and authenticated UI preview; run focused checks/build.
4. Check Docker and Modal app state read-only. Start only required local services; perform at most one language/audio app update if needed, then one CPU `/health` check.
5. Sign in through Teacher Web and trigger exactly one real inference. Capture output and timing. Stop on failure/unknown without retry.
6. Disable the local flag, collect final container/app state, write evidence, update context/status/SRS §32, and report limits. No commit or push.

## 10. Known limits

- A successful render proves structured generation, backend sanitation and UI display for one prompt. It does not prove illustration quality across topics, child usability, educator approval, dataset quality, publication rights, renderer performance targets, persistent lesson integration, Parent playback, or production readiness.
- The user-facing result remains an unreviewed, ephemeral draft. Persisting it into a lesson presentation or shared catalog is a separate authorized milestone with immutable revision, provenance and review workflow.
- If Modal deployment would require a new GPU/model download or a new secret, stop and report before that action. This plan does not authorize adding credentials or downloading a dataset.
