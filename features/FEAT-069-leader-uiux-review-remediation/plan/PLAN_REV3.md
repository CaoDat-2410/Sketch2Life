# FEAT-069 API-aligned UI/UX completion — Plan Rev3

- **Status:** APPROVED for this exact frontend-only scope.
- **Feature:** FEAT-069 — Leader review UI/UX remediation.
- **Revision:** 3.
- **Delivery branch:** `FE_UI_Project_Ver2` at baseline `ae2a8c8165aa1d11b62a7005a9e28d8c0ea8c046`.

## Goal

Bring the Parent Android UI and the Teacher, School Manager, and Platform Admin web UIs into closer alignment with the leader review, FEAT-063 SRS v2.5-draft, and API contracts actually mounted in the delivery branch. Use the permitted newer API feature branch only as read-only contract context. A route found on another branch is not available to a teammate cloning this delivery branch.

## Sources and branch boundaries

- Canonical requirements: `docs/context/SRS_AUTHORITY.md` and `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` v2.5-draft (unsigned).
- Review input: owner-provided leader-review transcript in the local attachment; feedback is not a replacement for canonical SRS/API contracts.
- Delivery API baseline: backend and `UI_Project/shared/backendApi.tsx` at the delivery branch baseline above.
- Read-only newer API comparison: `origin/feature/feat063-m2-parent-teacher-foundation@5c07c94e86826447d975ef2757aa1fefdc876c8c`.
- Source exclusions: `FE_UI_Project_Ver2`, `dev`, `FE_UI_Project`, `FE/UI-Teacher`, `FE/UI-School-Manager`, `FE/UI-Platform-Admin`, `FE/UI-Parent`, `codex/feat-018-contract-plan`, and all `plan/person-3-*` branches. Do not use top-level `apps/` legacy UI or Child Expo as implementation sources.

## API audit conclusions

- Delivery branch mounts Lesson Library and BE1 runtime routers. Supported contract areas include Parent lesson list/detail/download/invitations; Teacher lesson list/detail/create/update/archive/source-document/version/access-grant operations; Manager organization assignments/classes/roster/consent and access-grant decisions; Platform Admin lesson moderation; and classroom session lifecycle operations.
- The existing shared client defines methods for many Lesson Library and BE1 operations, but current role pages do not invoke them. The client also references `GET /api/auth/v1/me`; that handler and the expected `window.sketch2lifeAuth` bridge are absent in this delivery checkout, so live role login cannot be claimed.
- The allowed newer API feature branch mounts Parent profile/story-run and Parent/Teacher AI router groups, but these are absent from the delivery branch. Do not call them from the handoff UI or imply that they are available to teammates on this branch.
- Delivery branch does not provide the complete Parent ASR, story/video generation/playback, child-profile CRUD, dashboard analytics, teacher occurrence/Sketch Deck, or platform moderation queue-list APIs. A UI preview must not imply those server operations completed.

## Scope

1. Keep the implementation under `UI_Project/`: Parent experience stays in `parent-ui` and is packaged by the Parent Android WebView app; Teacher, School Manager, and Platform Admin remain web workspaces.
2. Make API availability and preview behavior consistent across screens. When a supported authenticated API/context is not present, preserve a usable, visibly labeled preview; never turn fixture success into a backend-success message.
3. Align Parent lesson library/invitations to the existing public/shared contract shape and current route capability. Keep story/photo/audio/script/video steps as preview-only wherever the delivery branch has no corresponding mounted API. Keep the lesson-linked outdoor activity before video only as the already-approved review prototype and record its conflict with the canonical SRS; keep gender local-only and mismatch analysis simulated.
4. Align Teacher lesson authoring/list/detail/review language to the current Lesson Library contracts. Keep dashboard counts, lesson extraction, AI deck, child sample, and occurrence presentation preview-only unless an exact delivery-branch route supports the action and the UI has authenticated identity/context.
5. Align School Manager class/roster/consent and lesson-review screens to BE1/Lesson Library concepts; do not claim class lifecycle, billing, quota, capacity, transfer, or notification persistence without matching mounted routes.
6. Keep Platform Admin moderation UI bounded to the mounted moderation operation; do not represent a fixture queue as a server queue because this branch lacks a moderation queue-list route.
7. Add clear loading, empty, unavailable, and error states to any screen that can consume an existing contract. Do not issue API requests or mutations during implementation/verification. Do not seed organization IDs or child data. Any user-triggered write in code must use an existing typed operation, respect revision/idempotency requirements, and show its actual API result.
8. Update FEAT-069 context, decisions, source/API crosswalk, evidence, status, and root approval/source records. Build the five UI workspaces and Parent Android debug APK; visually inspect relevant screens. Do not add or run automated tests.
9. Run `git diff --check` and `python tools/validate_repository_security.py` before each commit/push. Use a normal fast-forward push to `origin/FE_UI_Project_Ver2` only, under the existing user authorization.

## Acceptance criteria

- **AC1:** Every displayed server-data area identifies a mounted delivery-branch endpoint or is clearly labeled preview-only; no route available only on the read-only comparison branch is presented as available.
- **AC2:** Parent public and shared lesson groups, lesson details, and invitations match the existing Lesson Library data concepts; local preview remains usable without Firebase auth.
- **AC3:** Parent profile/story/photo/audio/ASR/video steps make no claim of persistence or generation by the delivery backend where the corresponding mounted API is absent.
- **AC4:** Teacher lesson authoring, versions, review, and import language matches the current Lesson Library contracts and does not imply an AI extraction/slide route that is not mounted.
- **AC5:** Teacher dashboard does not invent a dashboard endpoint or label fixture totals as live API data.
- **AC6:** School Manager organization, class, roster, consent, and lesson review screens reflect BE1/Lesson Library fields and preserve role/consent boundaries; unsupported management operations remain labeled preview-only.
- **AC7:** Platform Admin moderation does not imply a live moderation queue where only the moderation mutation is mounted.
- **AC8:** Leader-review UI items from Rev2 remain present, including Parent compact home/center create/settings, optional guide, audio copy, context confirmation, activity-order prototype, and Teacher no-dashboard-notification card/centered lesson detail/session-flow preview.
- **AC9:** SRS conflicts and unsupported API/data requirements (pre-video activity order, gender, mismatch decision, ASR, missing identity bridge) are explicitly recorded as open product/integration gaps, not silently represented as approved API behavior.
- **AC10:** Five frontend builds, Parent Android typecheck/package, manual visual review, source records, security validation, and publication result are recorded under FEAT-069. No automated test suite is run.

## Open product and integration gaps

- The canonical SRS puts Parent outdoor activities after video (FR-P-05 / FR-PL-16), while the leader requests them before video. Rev3 retains the explicit preview sequence from Rev2 pending SRS owner resolution.
- Gender is absent from current delivery SRS/API profile contracts; it remains preview-only.
- A mismatch-choice modal is a simulated leader-review state; the delivery branch has no corresponding Parent analysis result contract.
- Parent story-run/profile/AI routes visible in the allowed newer feature branch are not mounted in the delivery branch; ASR and video routes are also unavailable in this handoff composition.
- Current checkout lacks the Firebase bridge and `/api/auth/v1/me` implementation required to log in and resolve roles end-to-end. API-informed UI is not evidence of a working authenticated runtime.
- No delivery-branch endpoint provides Teacher dashboard analytics, moderation queue listing, durable teacher occurrence/deck/sample flow, billing, quota, or audit UI data.

## Exclusions

Backend/API/schema/auth/provider/SRS changes or route merges; calling any live API or AI service; API/database writes during implementation or QA; use of excluded branches as source; migration of the entire backend feature branch; Child Expo and top-level legacy `apps/`; production credentials/real child data; release signing; force push/history rewrite; automated tests.

## Approval basis

The project owner directly requested that the UI be built from the APIs in the GitHub project and that the leader's full review be satisfied. This approves the exact frontend-only scope above. It does not approve backend/API changes, an SRS sign-off, or a claim that missing authenticated services are working.
