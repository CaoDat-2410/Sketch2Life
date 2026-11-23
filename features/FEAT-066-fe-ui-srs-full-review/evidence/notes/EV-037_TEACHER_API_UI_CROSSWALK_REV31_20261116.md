# FEAT-066-EV-037 — Teacher API/UI source crosswalk for Rev31

- Date: 2026-11-16
- Purpose: Source-level evidence for PLAN_REV31_TEACHER_API_UI_REBUILD_20261116.md.
- Plan SHA-256: 2EB6235B8F8DFB5EB6EC4098FA2892687102DD4D922360E16751F6D21DA0E5E7
- Product baseline: canonical FEAT-063 SRS v2.7-draft Rev60, SHA-256 70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B; unsigned.
- Backend source baseline: origin/dev 1c9148e88600a101887e477541c4c4893ba1c7df.
- Frontend source baseline: codex/fe-ui-web-remediation b72f9e46f9c63e019807d7c4a2c309b0aa46a133.

## Source inspected

- Requirement authority: docs/context/SRS_AUTHORITY.md; docs/context/SOURCE_REGISTER.md; FEAT-063 SRS §§3, 5.2, 7.3, 9.6, 21.1, 21.5–21.6, 31.4–31.8 and OI-17.
- Teacher route map and shell: apps/web/src/modules/teacher/App.tsx; apps/web/src/shared/WebAppShell.tsx; apps/web/src/shared/PortalSessionContext.tsx.
- Current API client and Teacher calls: apps/web/src/shared/backendApi.tsx; Teacher Workbench, T05ClassesScreen, TeacherApiLessonPage, TeacherApiImportPage, TeacherAiLessonWorkflowPage and aiWorkflowService.
- BE1 identity, classes, roster and consent guards: backend/src/sketch2life/interfaces/http/routers/be1_registry.py and be1_sessions.py.
- Lesson Library routes/contracts: backend/src/sketch2life/interfaces/http/routers/lesson_library.py; backend/src/sketch2life/contracts/schemas/lesson_library.py; backend/src/sketch2life/infrastructure/lesson_library/service.py.
- Teacher AI routes and mounting: backend/src/sketch2life/interfaces/http/routers/teacher_ai.py; backend/src/sketch2life/interfaces/http/router_composition.py; backend/src/sketch2life/interfaces/http/app.py.

## Findings

1. The current Teacher adapter wires authenticated role/assignment reads, class/profile/consent reads, lesson list/detail/create/update/archive, public-review grant request, document upload/status/parts/completion/abort and source-document/revision reads.
2. The BE1 profile-create handler exists but is restricted to local/test synthetic-pilot configuration and marks the record SYNTHETIC_DEV; it is not a production Teacher profile/enrollment contract.
3. Lesson Library POST /organizations/{organization_id}/lessons/{lesson_id}/versions exists in backend source. It creates a DRAFT lesson version linked to a source revision and marks that document revision CONFIRMED. The Teacher adapter does not expose this route. Its semantics need to be checked against FR-T-07 before the UI uses it as the extraction review gate.
4. Lesson Library route presence does not establish storage, scanner or parser readiness in a runtime. Teacher AI routes require a development Modal configuration and return synchronous draft responses; no persistent plan lineage is supplied by the current Teacher UI.
5. The current Teacher UI explicitly marks occurrence/plan/checklist/deck lifecycle, server child selection/StoryRun, job/reconciliation, playback/projection/lifecycle, settings/profile, history, inbox and standalone activity catalog dependencies unavailable.
6. BE1 session/lobby/canvas and Parent/demo StoryRun routes are not substitutes for the SRS Teacher occurrence and single-child StoryRun flow. Manager-only access-grant decision operations remain outside Teacher authorization.
7. origin/dev advanced since the earlier FE review. Its backend OpenAPI projection changed; route-module source inspection and router composition were used for this crosswalk rather than counting projected OpenAPI operations.

## Limits

This is a static source review only. No endpoint was called; no account, credential, child record, provider, screenshot, build or application test was used. Runtime deployment/configuration and final OI-17 visual sign-off remain unverified/open. No implementation or product-policy decision is recorded by this evidence.