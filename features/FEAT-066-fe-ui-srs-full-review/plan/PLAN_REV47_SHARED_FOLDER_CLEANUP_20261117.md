# Plan Rev47 — Organize apps/web shared folder

- Date: 2026-11-17 (Asia/Bangkok)
- Status: APPROVED_FOR_IMPLEMENTATION per Rev47 approval record; no files had been moved when approval was recorded.
- Worktree: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation
- Scope: apps/web/src/shared only, plus import specifiers that directly reference those shared files and FEAT-066 governance records.

## Goal

Group shared web files by responsibility so the shared folder is navigable while preserving all runtime behavior and existing local work.

## Inventory

- 17 files at the shared folder root and one existing assets directory.
- 50 direct source import/style references across 27 consumer files under apps/web/src.
- Existing local changes include WebAppShell.tsx and backendApi.tsx; backendRuntimeConfig.ts is untracked. Preserve their contents and only adjust imports that must change for this organization.

## Proposed target layout

apps/web/src/shared/
  api/
    backendApi.tsx
    backendRuntimeConfig.ts
  auth/
    PortalSessionContext.tsx
    RoleMismatchPage.tsx
    WebPortalLoginPage.tsx
  components/
    BrandMark.tsx
    FeatureAvailability.tsx
    RoleDashboardIcon.tsx
    RoleHelp.tsx
    ui.tsx
  navigation/
    WebAppShell.tsx
  styles/
    portal-ui.css
    role-crayon-theme.css
    tailwind-utilities.css
    ui-primitives.css
    web-app.css
    web-brand-theme.css
  assets/
    sketch2life-brand-art-20261110.jpg (preserve in place)

## Move and import plan

- Move backendApi.tsx and backendRuntimeConfig.ts into shared/api/.
- Move PortalSessionContext.tsx, RoleMismatchPage.tsx and WebPortalLoginPage.tsx into shared/auth/.
- Move BrandMark.tsx, FeatureAvailability.tsx, RoleDashboardIcon.tsx, RoleHelp.tsx and ui.tsx into shared/components/.
- Move WebAppShell.tsx into shared/navigation/.
- Move all six shared CSS files into shared/styles/.
- Keep the existing shared/assets directory and its artwork unchanged.
- Rewrite the 50 direct references in the 27 consumer files under apps/web/src, update internal relative imports in moved files, and adjust main.tsx stylesheet paths. Preserve import ordering where it affects CSS cascade.

## Boundaries

- No deletions, renames of exported symbols, API/auth behavior changes, styling/content changes, dependency/config changes, or unrelated refactors.
- Do not inspect, move, copy, or edit .env or other local environment/secret files.
- Preserve all existing staged, unstaged, and untracked worktree content. No commit or push.
- Do not run the application test suite. After approval, verify the final path/import map and run the web production build to catch broken imports.

## Acceptance criteria

1. The shared directory matches the proposed layout, with assets preserved.
2. Every listed source file remains present exactly once with its current content; only import specifiers required by the moves change.
3. All imports and stylesheet references resolve, and no source reference points to the former shared-root paths.
4. Existing unrelated dirty changes remain intact; review the final diff and git status for accidental edits.
5. The web production build succeeds. No commit or push is made.

## Approval gate

Implementation is blocked until this exact move/import plan is approved and recorded in approvals/TASK_APPROVAL.md. The organization is broad and changes paths in 27 source files, so approval is requested before bulk moves.
