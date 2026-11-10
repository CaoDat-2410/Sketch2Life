# FEAT-066 — Bright web branding, shared login font correction, dashboard icon refresh and three-role logout controls

- Status: APPROVED_FOR_IMPLEMENTATION
- Plan revision: 13
- Updated: 2026-11-10 (Asia/Bangkok)
- Worktree: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation
- Branch: codex/fe-ui-web-remediation
- Canonical SRS: FEAT-063 v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; unsigned
- Governance/evidence: features/FEAT-066-fe-ui-srs-full-review

## User authorization and design direction

The user directly requested replacing the current web logo with the attached Sketch2Life artwork and applying the brighter blue/grey colors across all web UIs. The supplied asset is F:/Downloads/244247a40d95f81c31620a78d34d04d8.jpg, SHA-256 86010669F03972BC1273DC02BEB8F34B39BD5E47C00771B2632003C1D62F9042. Copy it unchanged to apps/shared/assets/sketch2life-brand-art-20261110.jpg and record its user-supplied provenance.

Continue the approved design-taste-frontend Cool Grey + Cobalt direction from revision 9: canvas #EEF0F3, surface #E2E5EA, white raised surface, ink #0B0C0E, muted text #5D6470, cobalt action #1F2DE6 with white action text, and a pale cobalt tint. Use the generated inverse tokens for dark mode. Keep the UI light and bright overall; the artwork is the vivid brand focal point. Preserve semantic success, warning and error colors. The SRS does not prescribe a product palette.

## Included browser apps

Apply the shared logo and palette to:
- apps/parent-ui (existing browser preview only; SRS Parent target remains Android)
- apps/school-manager-ui
- apps/teacher-ui
- apps/platform-admin-ui
- apps/admin-ui (existing browser school-admin interface; do not infer a new SRS role)
- apps/shared brand components and styles used by these web apps
- FEAT-066 plan, approvals, context, decisions, evidence and status

## Exclusions and constraints

- Do not modify apps/mobile, apps/ui-mobile, apps/child-ui, backend/API, credentials, real user/child data, production providers, packages, manifests, lockfiles or external services.
- apps/parent-web is explicitly historical/inactive and receives no new code.
- Preserve existing behavior, layouts except necessary logo sizing, routes, role/permission checks, status meaning, privacy and fixture labels. Do not change authentication or business flows.
- Do not make the user-provided logo an externally hosted asset. Do not redraw or crop the source; preserve its aspect ratio and provide useful alt text.
- Do not run automated tests or builds. Do not commit or push this visual rollout.

## Acceptance criteria

- AC1: Shared portal branding and each included app display the exact user-provided image at a suitable responsive size without clipping, distortion or duplicate wordmark text. Parent login splash and Admin-specific logo slots also use it.
- AC2: All included web apps use the same bright Cool Grey + Cobalt family across login, shells, surfaces, controls and focus indicators. Dark mode uses the generated inverse palette where supported.
- AC3: Existing success/warning/error meanings remain distinct and are not conveyed by color alone. Keep readable contrast and visible keyboard focus.
- AC4: Preserve routes, data, API behavior, authentication/permissions, content and privacy. Make no mobile/native/backend changes.
- AC5: Manually review each included app at desktop 1440x900 and narrow 390x844 on representative login and authenticated/primary screens where local fixture access supports it. Capture screenshots and report any route that cannot be exercised without credentials/backend.
- AC6: Keep changes confined to the listed web app/shared paths and FEAT-066. Record provenance and results in FEAT-066 evidence. No tests/builds, package changes, commit or push.

## Review workflow

1. Verify canonical SRS authority/hash, current worktree/branch/status, browser app inventory and supplied image hash.
2. Record revision 10 and its exact SHA-256 in feature-local approvals before changing app code or copying the brand image.
3. Copy the supplied image unchanged, apply the shared palette and logo across the included web app roots, and preserve unrelated dirty files.
4. Use local loopback previews only. Manually inspect desktop and narrow screenshots; never use production auth/backend data.
5. Update FEAT-066 context, decisions, evidence index and status. Report branch, dirty state and that no commit/push occurred.

## Revision 11 — shared icon family for the three SRS role dashboards

- Status: APPROVED_FOR_IMPLEMENTATION
- Approver: User, direct request on 2026-11-10 (Asia/Bangkok), to change the dashboard icon set across the three web roles.
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Scope: authenticated dashboard iconography (shell navigation, role/status indicators, and route content using existing icon components) in `apps/school-manager-ui`, `apps/teacher-ui`, and `apps/platform-admin-ui`; FEAT-066 plan, approval, context, decision, evidence, and status records.
- Role mapping follows canonical SRS §3: Teacher (`teacher`), School Manager (`school_manager`), Platform Admin (`platform_admin`).
- Design: one local SVG icon family with rounded strokes and restrained duotone fills, using the existing bright Cool Grey + Cobalt palette. Use no external icon service, font, or package.
- Preserve routes, navigation labels, role checks, actions, content, and accessibility names. Keep icons decorative to assistive technology where adjacent text already names navigation. Do not redesign login layout; shared icon glyphs may use the same icon family. No changes to Parent, the additional Admin UI surface, mobile/native apps, backend/API, packages, or lockfiles.

### Acceptance criteria

- AC1: The three authenticated role dashboards use the same newly styled icon family across shell navigation, dashboard content, and role/status indicators, with recognizable symbols, consistent size/stroke, and cobalt-compatible inactive/active states.
- AC2: Navigation labels, links, selected states, keyboard behavior, and role permissions are unchanged; icons remain hidden from screen readers when the adjacent label provides the name.
- AC3: No dependencies or manifests change. No mobile, backend, production data, credentials, or external provider use.
- AC4: Manually review representative dashboard screens for all three roles at 1440x900 and 390x844, save screenshots and note any unavailable local preview.
- AC5: No automated tests or builds. Update FEAT-066 context, decisions, evidence, and status; leave changes uncommitted and unpushed.

### Review workflow

1. Verify the requested worktree, branch and dirty status; use only FEAT-066 v2.7-draft Rev57 authority.
2. Record the exact SHA-256 of this revision and matching direct-user approval before modifying role UI code.
3. Implement the shared local SVG icon family across the three role dashboards and align navigation icon treatment with the bright palette.
4. Manually inspect all three local role dashboards at desktop and narrow widths, then save evidence and update governance records.

## Revision 12 — Vietnamese-safe typography on shared web login pages

- Status: APPROVED_FOR_IMPLEMENTATION
- Approver: User, direct request on 2026-11-10 (Asia/Bangkok), reporting the displayed Vietnamese login headline font as broken and asking to replace it.
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Scope: the shared login headline typography in apps/shared/portal-login.css, used by Teacher, School Manager, and Platform Admin /login routes; FEAT-066 plan, approval, context, decision, evidence, and status records.
- Direction: use the existing login sans-serif stack with Vietnamese glyph coverage for the headline and emphasized phrase; remove the serif/italic treatment responsible for the visibly malformed Vietnamese accents. Do not add fonts, packages, external font imports, or layout changes.
- Preserve login text, role destinations, authentication behavior, palette, page layout, accessibility names, and privacy.

### Acceptance criteria

- AC1: Vietnamese headline diacritics render cleanly with consistent glyph shape and alignment on all three shared role login pages.
- AC2: The existing headline hierarchy remains clear and responsive at desktop 1440x900 and narrow 390x844; no clipping or overflow is introduced.
- AC3: No route, copy, authentication, API, app behavior, package, or manifest changes; no mobile/native, backend, credentials, production data, or external provider use.
- AC4: Manually inspect all three local loopback login pages at desktop and narrow widths and save FEAT-066 screenshots with observations.
- AC5: Do not run automated tests/builds or commit/push. Preserve all unrelated dirty worktree changes.

### Review workflow

1. Verify the designated worktree, branch and existing dirty status; use FEAT-063 v2.7-draft Rev57 as the canonical SRS authority.
2. Record the plan SHA-256 and this direct-user authorization in FEAT-066 before changing app code.
3. Adjust only the shared headline font rules in apps/shared/portal-login.css.
4. Manually inspect Teacher, School Manager and Platform Admin login pages using loopback previews at desktop and narrow widths; record screenshots and results.
5. Update FEAT-066 context, decisions, evidence and status. Leave changes uncommitted and unpushed.

## Revision 13 — visible logout controls for the three SRS web roles

- Status: APPROVED_FOR_IMPLEMENTATION
- Approver: User, direct request on 2026-11-10 (Asia/Bangkok), asking for a logout button on all three role UIs.
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Scope: authenticated shell logout controls for Teacher, School Manager, and Platform Admin in apps/teacher-ui, apps/school-manager-ui, and apps/platform-admin-ui; directly necessary shell styles and logout prop wiring; FEAT-066 records/evidence.
- Placement: keep one clearly labeled logout button beside the account identity at the bottom of each role sidebar. Retain School Manager's existing button; move Teacher's existing button from the top bar into the sidebar so it remains visible at narrow widths; add the missing Platform Admin sidebar button.
- Behavior: call each app's existing logout handler, which clears role/auth session state, signs out the existing auth bridge when available, and relies on the current route guard to return to /login. Add no new auth policy or backend behavior.
- Role mapping follows canonical SRS §3: Teacher (teacher), School Manager (school_manager), Platform Admin (platform_admin).

### Acceptance criteria

- AC1: Each of the three authenticated role shells exposes one visible logout button with a clear Vietnamese label at desktop and narrow widths.
- AC2: The buttons are keyboard reachable, have visible focus, and provide an accessible name; narrow collapsed sidebars retain a recognizable logout icon with an accessible label.
- AC3: Activating each button invokes the existing role logout handler, clears session auth/role state, and returns to that app's /login route.
- AC4: Preserve all other role routes, actions, permissions, layout content, privacy and data. No Parent/Admin UI, mobile/native, backend/API, packages, or lockfiles.
- AC5: Manually review all three dashboards at 1440x900 and 390x844, capture screenshots, and record logout interaction results.
- AC6: Do not run automated tests/builds or commit/push. Preserve unrelated dirty worktree changes.

### Review workflow

1. Verify the named worktree, branch, dirty state, and FEAT-063 v2.7-draft Rev57 authority.
2. Record this plan revision's SHA-256 and direct-user authorization in FEAT-066 before app code changes.
3. Reuse the existing logout handlers and implement one persistent sidebar control per role, preserving responsive access.
4. Manually inspect desktop/narrow dashboards and activate each logout control in isolated local preview state.
5. Update FEAT-066 context, decisions, evidence and status; leave the branch uncommitted and unpushed.
