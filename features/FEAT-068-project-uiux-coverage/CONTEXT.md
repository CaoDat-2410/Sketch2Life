# FEAT-068 — Complete UI/UX coverage for the four project roles

- Status: COMPLETE and published to `origin/FE_UI_Project_Ver2` under approved Plan Rev1; implementation commit `18fd36fd78e498dc27818a84c43b6d43ed4c50c7`.
- Owner: Project owner/requester.
- Goal: Deliver a coherent, review-ready UI/UX across the Parent Android app and the Teacher, School Manager, and Platform Admin web workspaces on `FE_UI_Project_Ver2`.
- Scope: Update the existing `UI_Project/parent-ui`, Parent Android host as required for the bundled UI, the three role workspaces, and their shared web components/styles. Keep the Parent app on the existing Android WebView package path and keep the other three roles on web.
- Non-goals: Change backend/API contracts, database, auth provider, product SRS, or service deployment; delete or revive the legacy Child Expo workspace; sign a release APK; promote the Rev38 generated image boards as product assets.
- Dependencies: FEAT-063 canonical working SRS v2.5-draft; current source/API implementation; Rev38 mockups/component boards as non-contract references; current FE_UI_Project_Ver2 UI workspaces; Android SDK/emulator and frontend build toolchains.
- Risks: Many story/video/profile/occurrence actions lack a mounted authenticated API. UI must identify preview-only data and must not imply persistence or AI completion. The leader review and Rev38 references predate current SRS decisions in a few flow details.

## Context snapshot

The repository authority record routes current product intent to `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` v2.5-draft, which remains unsigned. Its §§1–31 are the current working target; §32 is dated implementation evidence. The provided Rev38 `ui-mockups` and `ui-components` folders describe themselves as generated visual drafts based on SRS v2.3/API Rev37 and are not approved implementation or API contracts.

The current Parent Android target is `UI_Project/parent-android/apps/mobile`; its `AppRoot` loads the sibling `UI_Project/parent-ui` bundle in a local WebView. `apps/ui-mobile` is a separate legacy Expo workspace. The Parent Vite UI and web role workspaces currently use local preview state for most business screens. The shared API client has selected Lesson Library and BE1 operations, but the current main API composition does not provide the complete target Parent story/video and Teacher occurrence/AI workflow.

## Source register

- `docs/context/SRS_AUTHORITY.md` and `docs/context/SOURCE_REGISTER.md`.
- FEAT-063 SRS v2.5-draft, especially §§5, 7, 9, 19, 21 and 31–32.
- `UI_Project/design-references/ui-mockups-rev38-20261030/SCREEN_INDEX.md` and `ui-components-rev38-20261030/COMPONENT_INDEX.md`.
- `UI_Project/parent-android/README.md`, `UI_Project/parent-android/apps/mobile/src/app/AppRoot.tsx`, `ParentWebPreview.tsx`, and `UI_Project/parent-ui/src/App.tsx`.
- `UI_Project/shared/backendApi.tsx`, `UI_Project/shared/webWorkspace.tsx`, `UI_Project/shared/roleFlows.tsx`, and `backend/src/sketch2life/interfaces/http/router_composition.py` / `app.py`.
- FEAT-067 is complete for Android packaging only; its scope expressly excluded UI/flow changes. FEAT-068 records this separately authorized UI/UX scope.

## Implementation snapshot (2026-11-13)

- Parent Android and all three web role workspaces now have role-specific responsive UI/flow coverage. Build, Parent typecheck, Android debug APK packaging, emulator launch and the Parent story preview path succeeded; details and screenshots are in `evidence/notes/EXECUTION.md`.
- Parent story screens preserve the SRS sequence and stop honestly before video generation when the authenticated Story/video API is unavailable. Teacher authoring/import/review, optional Sketch Deck, sample flow and presentation state are labeled previews where the mounted client/API is incomplete. Manager review and Admin moderation use the same truthful preview policy.
- The Android APK includes the Parent HTML bundle; Metro is still needed by the debug React Native host. The Vite server at port 5171 is not needed by the packaged Parent UI. The three other role entry points remain web.
- Manual browser evidence is limited to one dashboard screenshot per web role and source review of shared flows/styles. Full manual keyboard/dialog/narrow-viewport walkthrough is outstanding and is not represented as complete.
- No backend/API/auth/schema/SRS changes, backend writes, AI calls, child data, release signing or legacy Child Expo changes were made.
