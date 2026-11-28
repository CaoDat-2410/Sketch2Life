# Koi UI redesign: wave notes (UI-KOI-1 to UI-KOI-11)

Merged from the per-wave folders that the Codex runs created. This is a working note, not an approval record.

## UI-KOI-1

### CONTEXT

﻿# UI-KOI-1 context and status
Status: REVIEW. Shared koi palette and shell, teacher overview composition, manager school panel and admin metric styling implemented within apps/web. The visual match and accessibility require browser review; do not treat the wave as fully verified. The task instruction restricts records to apps/web rather than the repository-root features directory.

### DECISIONS

﻿# Decisions
Use existing koi asset and live data; retain tested Vietnamese and accessible names. Google Fonts with system fallback per task instruction. Keep app-only records because root feature records are outside the allowed edit boundary.

### CHECKS

﻿# UI-KOI-1 evidence
2026-11-28: `npm run test -- --maxWorkers=8` passed (137 files, 1305 tests); `npx tsc -b` passed; `npm run lint` passed with warnings; `npm run build` passed with chunk-size warning. No server started. Browser rendering, contrast, touch targets and overflow were not verified. Mockup differences include live koi instead of still, existing tested quota wording and step accessible label, existing shell controls, simplified card strokes and overview layout. No LOCKED.md found in repository file list. Existing session and authoring pages retain structure.

### PLAN

﻿# UI-KOI-1 wave 1
Scope: shared tokens, primitives and shell; teacher overview and manager/admin overview styling. Preserve behavior, routes, strings, access gates, and phase-1 work. Session and authoring structure are excluded.
Acceptance: approved koi direction visible across all roles; accessible focus, contrast, 40px touch targets, responsive layout and reduced motion; requested tests, typecheck, lint and build reported. No server, backend, dependencies or git writes.

## UI-KOI-2

### CONTEXT

### UI-KOI-2

Scope: user-requested wave 1 defect fixes and wave 2 session and lesson presentation, preserving behavior and existing work. Sources: user brief, tmp/koi-design/02-session.html and 03-lesson-authoring.html, existing frontend.
Status: APPROVED / IN PROGRESS

Review: implementation and automated checks complete; browser and exhaustive cross-role contrast verification remain open.

### VERIFY

### Verification

Tests: 137 files, 1317 tests passed. TypeScript passed. Lint passed with warnings. Build passed with chunk-size warning. Vietnamese question-mark search found URL/query syntax only. Edited source files checked UTF-8 without BOM.

Occurrence tests now open the plan step before plan interactions; added step draft retention. Added token contrast-pair test. Visual review and exhaustive cross-role button/chip contrast remain unverified.

### PLAN

### Plan and acceptance

1. Repair corrupted text and contrast, including the teacher hero.
2. Present session steps in order while preserving state and deep links.
3. Place lesson save actions in the editor header and phone form end; number sections and stack phone lists.
4. Search for corrupted Vietnamese and run the four requested checks.

Acceptance: existing behavior, accessible names, prefill and typed values remain intact; no prohibited files or services changed.

## UI-KOI-3

### CONTEXT

### UI-KOI-3

Status: REVIEW. Scope: user-directed teacher fixes and manager/admin presentation, preserving behavior and privacy. Sources: user brief, existing UI, tmp/koi-design mockups, FEAT-UI-KOI-2. Automated checks pass; browser verification remains open because the user prohibits a web server.

### DECISIONS

### Decisions

Use existing approved mockups and UI data; no generated assets. Respect the user restriction to apps/web for repository changes.

Teacher card styles use an important background, so both band headers use an explicit shared class with a higher-specificity important background. The save bar stays in normal flow. Roster uses anonymous references and preserves placement and move confirmation portals.

### VERIFY

### Verification

- `npm run test -- --maxWorkers=8`: 137 files, 1318 tests passed.
- `npx tsc -b`: passed.
- `npm run lint`: passed with warnings.
- `npm run build`: passed with a chunk-size warning.
- Mockups reviewed as supplied screenshots; live responsive layout and interactions were not visually verified because no web server was allowed.

### PLAN

### Plan and acceptance

1. Fix teacher session and lesson header bands, session layout and save bar; add regression coverage.
2. Align manager overview and roster and admin dashboard and accounts with supplied mockups using existing data. Preserve roster tables and portal dialogs; never show child names, ages or media to managers.
3. Run requested tests, typecheck, lint and build. Preserve existing work; no routes, APIs, dependencies or backend changes.

## UI-KOI-4

### CONTEXT

### UI-KOI-4

Status: REVIEW. Owner requested the original cozy styling while preserving current layouts and behavior. Sources: owner brief, HEAD cozy-shell.css and cozy-v9.css, original sketch2life-theme.css, UI-KOI-3 context, source register.

### DECISIONS

### Decisions

Use the original HEAD palette and hero gradient, retaining AA-compatible foregrounds. The owner supplied the visual direction; no generated assets are involved.

### VERIFY

### Verification

- npm run test -- --maxWorkers=8: passed, 137 files / 1318 tests.
- Updated token contrast test rerun: passed, 3 tests.
- npx tsc -b: passed.
- npm run lint: passed with existing warnings.
- npm run build: passed; chunk-size warning. Rebuilt after final CSS change.
- Browser and 390px visual verification not performed: user prohibited a web server. Responsive layout rules preserved.

### PLAN

### Plan and acceptance

Restore cream, pale violet navigation, pastel hero and bands, soft surfaces, buttons and original fonts. Preserve session steps, header save actions, layouts, 40px targets and 390px responsiveness. Verify AA token contrast and run tests, typecheck, lint and build. No behavior or dependency changes.

## UI-KOI-5

### CONTEXT

### UI-KOI-5

Status: REVIEW. Responsive overview and teacher session navigation implemented. Sources: owner brief, project context and source register, existing components and tmp/koi-design references. Visual viewport verification remains open; no server was started.

### DECISIONS

### Decisions

Use CSS and existing step state; no generated assets or behavior changes.

### VERIFY

### Verification

2026-11-29, Windows, apps/web:
- `npm run test -- --maxWorkers=8`: passed, 137 files and 1318 tests.
- `npx tsc -b`: passed.
- `npm run lint`: passed with warnings.
- `npm run build`: passed with chunk-size warning.
- Step accessible names and UTF-8 strings checked; existing navigation handler retained.
- CSS reviewed for shrinkable columns and wrapping; actual 1440, 1024 and 390 viewport rendering was not verified. No server started.

### PLAN

### Plan, revision 1

1. Remove overview row minimum widths and arrange card contents safely at desktop and mobile widths.
2. Present existing teacher step navigation as a full-width responsive bar with current state.
3. Run requested test, TypeScript, lint and build checks.

Acceptance: no card overflow at 1440, 1024 or 390; three labeled steps show a short state and active violet styling; existing navigation and tested strings remain; requested checks recorded. No generated image assets are needed.

## UI-KOI-6

### CONTEXT

### UI-KOI-6

Status: REVIEW. Three presentation changes implemented; requested automated checks passed. Sources: project context and source register, HEAD cozy-v9.css, current UI and the two local koi design references. Work is restricted to apps/web; no generated assets or server. Visual viewport verification remains open.

### DECISIONS

### Decisions

Use existing koi asset and base hero geometry; place steps outside the hero so their layout cannot change the fish stage or overlap it. No generated assets are needed.

Keep existing labeled controls and validation; visually consolidate labels on desktop and show them on narrow screens. Move the existing save actions to the header using native form association, and show them only for the content tab.

### VERIFY

### Verification, 2026-11-29

Environment: Windows worktree, commands run in apps/web. Reviewer: Codex. Inputs: owner brief, HEAD cozy-v9.css, tmp/koi-design/02-session.html and 03-lesson-authoring.html, existing implementation.

- `npm run test -- --maxWorkers=8`: 137 files and 1,318 tests passed. The header placement assertion was updated to match the requested layout and verify tab visibility.
- `npx tsc -b`: passed.
- `npm run lint`: passed with existing warnings.
- `npm run build`: passed after each of the three implementation steps; Vite reported a large chunk warning.
- `git diff --check -- apps/web`: passed; edited source files decode as UTF-8 without BOM.
- Source review: removed overview overrides for base hero dimensions and stage placement; the step row is outside the hero; section badges preserve heading text and save uses the existing form.
- No server was started per task constraint. Visual fidelity and 390px rendering have not been verified in a browser; automated checks do not establish visual acceptance.

### PLAN

### Plan revision 1

1. Restore base hero geometry and place the three steps below the hero without fish overlap.
2. Arrange Sketch Deck drawing steps as compact labeled rows, stacking on small screens.
3. Add section number badges and ensure existing lesson save actions appear in the editor header.
4. Run the requested test, typecheck, lint and build commands.

Acceptance: base desktop and mobile hero geometry; three steps in a row; compact responsive step fields with existing accessible names and behavior; numbered lesson sections and header save actions; existing tested strings preserved. No generated visual assets.

## UI-KOI-7

### CONTEXT

### UI-KOI-7

Status: REVIEW. Sources: owner brief, local mockups, existing UI and source register. Implemented requested presentation changes using existing data and controls; no generated assets. Browser visual verification remains open because the owner prohibited a web server.

### DECISIONS

### Decisions

Use existing data and controls, retain live KoiHero and existing copy. Feature records live under apps/web to respect the owner edit boundary.

### VERIFY

### Verification

Incremental npm run build passed after each of four items. Final build passed with Vite chunk-size warning. npx tsc -b passed. npm run test -- --maxWorkers=8 passed: 137 files, 1318 tests. No server started; visual match and responsive layout remain unverified in a browser. KoiHero was not modified.

### PLAN

### Plan

1. Session header and step bar. 2. Teacher overview lesson cards, class rows and quota. 3. Manager overview school band and area rows. 4. Authoring header and admin metrics and role bars. Build after each.

Acceptance: match owner-approved mockup layouts using existing data, cozy palette, live base-sized KoiHero, existing behavior, accessible names and tested strings. Run requested tests, typecheck and build; record limitations.

## UI-KOI-8

### CONTEXT

### UI-KOI-8

Status: REVIEW. Sources: user brief, UI-KOI-7 context, source register, existing styles and supplied dashboard mockup. Layout repairs preserve behavior, strings, accessible names and cozy colors. Browser visual verification remains open because the user prohibits a web server.

### DECISIONS

### Decisions

Removed the conflicting manager multi-column rule and obsolete role-chart overrides. The role list uses share percentages; the existing chart summary and named list remain available to assistive technology. Teacher row text takes remaining space. No new visual assets are required.

### VERIFY

### Verification

- npm run test -- --maxWorkers=8: 137 files, 1318 tests passed on final run. Initial run had a transient teacher slide test failure and a role chart accessible-summary failure; summary was restored before the passing run.
- npx tsc -b: passed.
- npm run build: passed, with existing large-chunk warning.
- git diff --check -- apps/web: passed.
- Visual browser verification not performed: user prohibits a web server.

### PLAN

### Plan and acceptance

Repair conflicting layout rules for manager overview cards and teacher class rows; render admin role counts as horizontal rows using the supplied mockup. At 1440 and 1024 manager card content stacks with a single-line link; teacher rows align icon, text and arrow; role rows show label, bar, count and percent. Run requested tests, typecheck and build; no server.

## UI-KOI-9

### CONTEXT

### UI-KOI-9

Status: REVIEW. Sources: owner brief, project context, source register, existing UI and supplied teacher mockup. Implemented shared navigation colors and teacher overview layout. Visual viewport review remains open because the user prohibited a web server.

### DECISIONS

### Decisions

Use existing assets and live koi; no generated assets. The supplied mockup is the visual reference.

### VERIFY

### Verification

- npm run test -- --maxWorkers=8: PASS (137 files, 1318 tests).
- npx tsc -b: PASS.
- npm run build: PASS; Vite reports a chunk-size warning.
- git diff --check -- apps/web: PASS.
- Browser viewport review not run: task prohibits a web server.

### PLAN

### Plan and acceptance

Apply the specified Fable sidebar colors for all roles and drawer. Place steps within the teacher hero, arrange lessons left and classes with quota right, align class rows and edges, and stack at 1024 and 390. Preserve behavior, names, strings, cozy page colors and koi size. Run requested tests, typecheck and build; no server.

## UI-KOI-10

### CONTEXT

### UI-KOI-10

Status: REVIEW. Owner-supplied layout brief and manager/admin mockups applied to existing UI. Behavior, labels, data and cozy palette retained; no new visual assets. Viewport inspection remains open because the task prohibited a web server.

### DECISIONS

### Decisions

Use existing components and palette; no new generated visual assets. User-provided mockups establish layout direction.

### VERIFY

### Verification

2026-11-29, Windows worktree, apps/web: npm run build passed after each of the three ordered changes (Vite warned about large chunks); npm run test -- --maxWorkers=8 passed 137 files and 1318 tests; npx tsc -b passed. Mockup references: tmp/koi-design/manager-admin/04-manager-overview.html, 06-admin-dashboard.html, 07-admin-accounts.html. Browser viewport inspection not performed: no web server authorized.

### PLAN

### Plan revision 1 and acceptance

1. Match manager overview band and divided responsive area rows. 2. Replace only school-status chart with accessible segmented bar and legend. 3. Compact account rows and outline lock action. Preserve behavior, text, data, and colors. Build after each step; run requested tests, typecheck, and final build. No server.

## UI-KOI-11

### CONTEXT

### UI-KOI-11

Status: REVIEW. Four requested existing UI refinements implemented with the cozy palette and existing validation retained. No new visual assets. Viewport inspection remains open because the task prohibited a web server.

### DECISIONS

### Decisions

Use existing tokens and components; no generated visual assets are needed. The SVG forms remain mounted in hidden tab panels. The shared dialog keeps Radix focus and Escape handling.

### VERIFY

### Verification

- Production build passed after each of the four items and after final refinements.
- Full test suite: 137 files and 1,318 tests passed.
- TypeScript project build passed after final refinements.
- Focused SVG and shell tests after final refinements: 31 passed.
- Visual viewport inspection was not performed; the request prohibited running a web server.
- Vite reported its existing large-chunk warning.

### PLAN

### Plan and acceptance

1. Center each role content column at wide widths. 2. Present SVG forms in accessible tabs with mounted state and compact rows. 3. Align monitoring cards and wrap values. 4. Compact the in-session password dialog with accessible visibility toggles and responsive actions. Preserve validation, behavior and tested strings. Build after each item and run requested checks; no server.
