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

## Revision 15 — FE-only remediation from the three-role v2.7 flow audit

- Status: APPROVED_FOR_IMPLEMENTATION
- Direct authorization: User follow-up in chat on 2026-11-11 (Asia/Bangkok): “Bật lên sửa tiếp nè”, following the complete three-role audit EV-016. This authorizes implementation of the FE-remediable findings below; it does not authorize backend/API or other-app changes.
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Product baseline: canonical FEAT-063 SRS v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; awaiting formal owner sign-off. Use §§1–31 as target requirements and §32 only as dated source evidence.
- Audit input: FEAT-066-EV-016, `evidence/notes/THREE_ROLE_WEB_FLOW_AUDIT_V27_REV57_20261110.md`.

### Scope

- Modify only `apps/teacher-ui`, `apps/school-manager-ui`, `apps/platform-admin-ui`, directly shared web modules those apps already consume, and FEAT-066 governance/evidence.
- Recheck each finding against current API contracts before coding. Implement only flows supported by an existing contract with the required auth, tenant, version and state semantics; otherwise show a clear unavailable/dependency state and record it.
- Teacher: correct consent labels; remove manual child selection and cross-class roster fallback from preview; add cursor pagination; use the existing upload-session status contract to recover uploads if it supports safe resume; inspect existing profile/extraction contracts for T02/T03 and keep unsupported occurrence, plan, StoryRun, video, projection and quota operations unavailable.
- School Manager: require the exact grant-linked immutable lesson version to be loaded and reviewable before enabling a decision; add cursor pagination where supported; retain explicit unavailable states for class-capacity/lifecycle, Teacher lifecycle, billing, quota, inbox and feedback operations lacking contracts.
- Platform Admin: remove local-only moderation/catalog actions that appear successful; expose operations only where an existing API supports them; otherwise show unavailable states and identify the missing API.
- Cross-cutting: preserve the same idempotency key for retries of one logical mutation wherever the existing API accepts an idempotency key; do not add a key to contracts that do not support it.

### Acceptance criteria

- AC1: Every changed action is backed by an existing API contract. Unsupported flows cannot appear to complete successfully and identify the missing dependency.
- AC2: Consent is shown as effective only when the relevant child/purpose consent record confirms it; missing or failed consent data is unknown/unavailable.
- AC3: Teacher preview has no manual child choice or cross-class fallback. Lesson lists follow opaque `next_cursor`. Upload resume uses server status only when the existing contract supports it and does not persist file bytes, credentials, or real child data.
- AC4: School Manager cannot approve a grant until the exact grant-linked immutable version is loaded and reviewable. Queue pagination follows opaque cursors. No child media/story is exposed.
- AC5: Platform Admin backend mode has no local-only success toast or mutation for unsupported moderation, publication, or operations flows.
- AC6: Retries of one logical mutation reuse one idempotency key where contract-supported; a new logical action receives a new key.
- AC7: Keep all SRS OPEN decisions open; do not invent pricing, quota policy, eligibility rules, roles, auth policy, or backend behavior.
- AC8: Manually inspect affected role routes at desktop and narrow widths in local loopback preview and record screenshots/observations under FEAT-066 evidence.
- AC9: No backend/contracts, Parent, additional Admin UI, mobile/native, package/lockfile, external credential/provider, production data, automated tests, build, commit, or push changes.

### Review workflow

1. Verify this worktree/branch and canonical SRS hash before implementation.
2. Record this plan SHA-256 and the direct authorization in the FEAT-066 approval ledger before app source changes.
3. Implement and review the smallest FE-only corrections in the scope above; preserve unrelated code and explicitly record API-blocked findings.
4. Use only loopback local previews; update FEAT-066 context, decisions, evidence and status after meaningful steps.
5. Leave this remediation uncommitted and unpushed for user review.

## Revision 16 — shared authentication and Teacher web visual preview

- Status: APPROVED_FOR_IMPLEMENTATION
- Direct authorization: User request on 2026-11-11 (Asia/Bangkok): “Sửa vào giao diện auth và của teacher trước cho tôi xem đi dùng skill mà làm ko đc làm chay”. This authorizes an implementation preview of the shared auth UI and Teacher UI in this worktree.
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Product baseline: canonical FEAT-063 SRS v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; unsigned, awaiting owner sign-off.
- Design inputs: the user-selected “paper + crayons” palette and the generated role concepts in the current conversation; use design-taste-frontend, frontend-design, ui-ux-pro-max, and ui-design-system. Palette is a visual direction, not an SRS requirement. Use warm paper #FFF9F0, white #FFFFFF, soft paper #F2EBDD, graphite #25241F, muted graphite #57574F, primary blue #245B9B, and restrained red #B93832, orange #B9561E, yellow #E0B12D, green #2F7048, teal #287887, and brown #765035. Keep yellow labels in graphite for contrast.

### Scope

- Redesign the shared web authentication presentation in apps/shared/WebPortalLoginPage.tsx and apps/shared/portal-login.css, covering the existing Teacher, School Manager, and Platform Admin login pages. Preserve role mapping, portal links, route destinations, login fields, existing authentication calls, validation/errors, and local-preview behavior.
- Apply the new visual system to the Teacher web app only: Teacher tokens/styles, authenticated shell/navigation, and Teacher workspace dashboard. Other Teacher routes inherit the semantic tokens where possible; preserve their existing interactions and API-backed/unavailable states. Keep the Sketch Deck projection surface white and 16:9 as required by NFR-33.
- Use existing code-native UI primitives and the already-present Three.js login scene only if it remains appropriate to the approved composition; do not add raster assets, packages, external services, or new 3D dependencies.
- Update FEAT-066 context, decisions, evidence, and status. Save manual preview screenshots under features/FEAT-066-fe-ui-srs-full-review/evidence/.

### SRS alignment and acceptance criteria

- SRS references: §2.3 (web role surfaces), §3 (role and tenant boundaries), §§5.2 and 7.3 (Teacher workflow), NFR-20/NFR-29 (accessible web interaction), and NFR-33 (white 16:9 Teacher Sketch Deck).
- AC1: The three login portal labels and role destinations remain correct; login actions still call the existing auth/local-preview paths. No auth or permission policy changes.
- AC2: Auth and Teacher use the paper-and-crayon visual direction with restrained semantic accents; Vietnamese text remains readable and correctly rendered, with no clipping or horizontal overflow at 1440×900 and 390×844.
- AC3: Keyboard focus, semantic labels, status/error announcements, and usable touch targets remain visible and accessible. The three auth portal links remain operable at narrow widths.
- AC4: Teacher navigation, class context, and existing workflow actions remain connected; UI must not imply unsupported API actions succeeded or expose child media by default. The Sketch Deck stays a white 16:9 projection surface.
- AC5: Manually inspect the three shared login routes and Teacher dashboard plus representative Teacher lesson/class routes at desktop and narrow viewports; save before/after screenshots and note any API/fixture limitation.
- AC6: Changes are limited to shared web authentication, Teacher web UI, and FEAT-066 records/evidence. No School Manager/Admin authenticated UI, Parent UI/mobile, backend/API/contracts, package/lockfile, production data, credentials, tests/builds, commit, or push.

### Review workflow

1. Verify this worktree, branch, dirty status, SRS authority, and canonical hash; preserve all existing changes.
2. Record this Rev16 plan SHA-256 and the direct-user approval in approvals/TASK_APPROVAL.md before editing app source.
3. Implement the shared auth and Teacher presentation with the listed skills; preserve flows and mark local preview data accurately.
4. Reuse or start only loopback previews; manually inspect desktop/narrow viewports and capture FEAT-066 evidence.
5. Update context, decisions, evidence index, and status; leave the worktree uncommitted and unpushed.
### Revision 16 scope clarification — shared login style cascade

Before source edits, review found that apps/shared/web-brand-theme.css applies later, important auth-only overrides to the shared login component. Updating portal-login.css alone would not reliably apply the approved palette to all three login pages. Rev16 therefore also permits editing only the .s2l-auth-shell and .s2l-auth-* rules in apps/shared/web-brand-theme.css. Do not alter its global tokens or authenticated Manager/Admin selectors.
## Revision 17 — child-friendly icon family across all three web roles

- Status: APPROVED_FOR_IMPLEMENTATION
- Direct authorization: User request on 2026-11-11 (Asia/Bangkok): “Đổi hết bộ icon của 3 role thành bộ icon thân thiện với trẻ cho tôi đi”.
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Product baseline: canonical FEAT-063 v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; unsigned, awaiting owner sign-off. This is a visual implementation choice, not a new SRS requirement.
- Scope: restyle the shared local SVG icon family in apps/shared/RoleDashboardIcon.tsx, which the Teacher, School Manager, and Platform Admin apps already use through their Icon exports. Apply consistently to shell navigation, dashboard/content icons, role/status indicators, and the shared login pages. Add no package, font, network asset, or backend behavior.
- Direction: rounded, friendly, lightly illustrated icons with restrained crayon-color accents that remain legible in the existing three role palettes. Keep each glyph recognizable and its current semantic mapping. Preserve currentColor contrast on primary controls and retain the current icon sizes and layout.
- Preserve routes, labels, actions, role checks, keyboard behavior, touch targets, and accessibility names. Icons remain decorative when adjacent text supplies the name. Do not alter Parent/mobile or the separate apps/admin-ui surface.

### Acceptance criteria

- AC1: Every icon rendered through the shared Icon component across all three SRS web roles uses the revised child-friendly visual treatment, with consistent rounded stroke and restrained semantic accents.
- AC2: Existing icon names still map to recognizable meanings; navigation labels, role/status meaning, actions, focus, permissions, and accessible names remain unchanged.
- AC3: Icons remain visible against existing light/dark, active/inactive, and primary-button states without changing layout, hit targets, or color tokens for other UI.
- AC4: Manually inspect representative authenticated screens for all three roles at 1440x900 and 390x844; save screenshots and record overflow/rendering observations.
- AC5: No package/lockfile, backend/API, Parent/mobile, separate Admin UI, external asset/provider, production data, automated tests/builds, commit, or push. Preserve existing dirty worktree changes.
- AC6: Update FEAT-066 context, decisions, evidence, and status; leave the worktree uncommitted and pending user review.

### Review workflow

1. Verify the designated worktree, branch and dirty state; preserve all existing modifications.
2. Record this plan SHA-256 and matching direct-user authorization before changing shared icon code.
3. Update the existing SVG icon component only; use the already-approved frontend design skills and do not add dependencies.
4. Review all three local role previews at desktop/narrow sizes and capture screenshots under FEAT-066 evidence.
5. Update context, decisions, evidence index and status; do not commit or push.

## Revision 18 — friendly full-color icons for role navigation and notifications

- Status: APPROVED_FOR_IMPLEMENTATION
- Direct authorization: User request on 2026-11-11 (Asia/Bangkok): “Dùng skill làm lại bộ icon của navbar và thông báo cho tôi đi và làm xong đợi yêu cầu tiếp theo”.
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Product baseline: canonical FEAT-063 v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; unsigned and awaiting owner sign-off. This is a visual implementation request, not an SRS requirement.
- Design skills: design-taste-frontend and frontend-design. The supplied screenshots are visual references.
- Scope: update the shared icon renderer and the dedicated authenticated shell call sites for Teacher, School Manager and Platform Admin so sidebar navigation, adjacent role/account actions, and notification/inbox icons use a recognizable full-color emoji glyph variant. Use the system emoji font stack and no image assets or added dependency. Keep page-content icons outside the role shells on the existing Rev17 icon treatment.
- Visual direction: choose familiar school and learning symbols with a warm crayon palette context and rounded existing icon tiles. Keep disclosure arrows/chevrons in their current directional style so control meaning remains clear. Preserve current sizes, hit areas, focus behavior, labels, navigation, role checks, and notification states.
- Preserve the Teacher unread count, School Manager's explicit inbox-unavailable state, and Platform Admin's existing notification indicator/behavior. This task changes icon presentation only.

### Acceptance criteria

- AC1: Teacher, School Manager and Platform Admin authenticated navigation and notification/inbox affordances use the friendly full-color icon variant consistently.
- AC2: Icon meanings remain recognizable and role-correct; existing labels, accessible names, decorative aria behavior, routes, buttons, role checks, unread/status semantics, and keyboard behavior remain unchanged.
- AC3: Icon appearance remains legible in active/inactive, light/dark and notification states without changing navbar dimensions or touch targets.
- AC4: Manually review all three role shells at 1440x900 and 390x844, plus dark desktop, and save screenshots with overflow/rendering observations.
- AC5: No packages/lockfiles, backend/API, Parent/mobile, separate apps/admin-ui, external assets/providers, real user/child data, automated tests/builds, commit, or push. Preserve all pre-existing dirty worktree changes.
- AC6: Update FEAT-066 context, decisions, evidence, and status. Leave the worktree uncommitted and pending user review.

### Review workflow

1. Verify the designated worktree, branch, and current dirty state.
2. Record the Rev18 plan hash and matching direct-user approval before changing app source.
3. Add the system emoji variant to the existing icon component and apply it only at the three role-shell navigation/notification call sites.
4. Use loopback previews to inspect all three roles at desktop/narrow widths and dark desktop; save evidence.
5. Update FEAT-066 records and stop for user review without commit or push.

## Revision 19 — monochrome line icons for role navigation and notifications

- Status: APPROVED_FOR_IMPLEMENTATION
- Direct authorization: User correction on 2026-11-11 (Asia/Bangkok): “navbar icon kiểu nét ko màu á”, after reviewing the Rev18 emoji preview.
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Product baseline: canonical FEAT-063 v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; unsigned and awaiting owner sign-off. This is a visual correction only.
- Skills/design inputs: design-taste-frontend and frontend-design; user-provided navbar/notification screenshots.
- Scope: revise only the navigation/notification variant in apps/shared/RoleDashboardIcon.tsx used by the Teacher, School Manager, and Platform Admin shells. Render the existing recognizable SVG paths as monochrome outline icons using currentColor and rounded caps/joins; use a bell outline consistently for all three notification/inbox controls. Retain shell call sites already added in Rev18.
- Preserve routes, labels, role checks, notification/unavailable states, unread counts, accessible names, keyboard behavior, dimensions, hit targets, and all non-shell icon treatment. No emoji glyphs in navbar/notification variant. No package or asset changes.

### Acceptance criteria

- AC1: Navbar icons and all three notification/inbox icons render as monochrome line glyphs with no emoji or semantic color fills.
- AC2: Foreground color follows the existing active/inactive/notification control color and remains legible in light/dark themes.
- AC3: Icon meanings and states remain recognizable; notification state, labels, actions, navigation, aria-hidden behavior, and layout remain unchanged.
- AC4: Manually inspect all three role dashboards at 1440x900, 390x844 and dark desktop; save screenshots and confirm no horizontal overflow or render/runtime error.
- AC5: No package/lockfile, backend/API, Parent/mobile, external asset/provider, production data, automated tests/builds, commit, or push. Preserve existing dirty worktree changes.
- AC6: Update FEAT-066 context, decisions, evidence and status; stop for user review.

### Review workflow

1. Verify the designated worktree, branch, and existing dirty state.
2. Record Rev19 plan SHA-256 and direct approval before source edits.
3. Replace only the Rev18 emoji output with the monochrome line rendering; keep existing role-shell variants and call sites.
4. Review desktop, narrow, and dark local previews for the three roles; record evidence.
5. Update FEAT-066 and leave the worktree uncommitted.

## Revision 20 — Teacher SRS layout diagnosis and demo proposal (audit only)

- Status: APPROVED_FOR_AUDIT_ONLY; FUTURE_TEACHER_IMPLEMENTATION_PENDING_USER_REVIEW.
- Direct authorization: User request on 2026-11-11 (Asia/Bangkok) to diagnose the current web UI against the newest SRS and present a proposed demo UI set; try Teacher first only if the user approves the proposal.
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Canonical product baseline: FEAT-063 v2.7-draft Rev57; SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5. Authority record confirms it remains unsigned. Requirements are §§1–31; §32 is as-built evidence only.

### Authorized in this revision

- One read-only review of Teacher UI route/navigation source, current FE API adapter contracts, prior Teacher screenshots/evidence, and SRS §§3–8, 19–21, 28 and 31.
- Produce a findings list separating SRS flow gaps, role/interaction errors, and visual/responsive simplification opportunities.
- Propose a Teacher-first screen inventory, navigation model, flow order, layout behavior and acceptance criteria for the user to review.
- Update only FEAT-066 plan/approval/context/decisions/evidence/status records. No Teacher source code, other role app, backend, package, or API change is included.

### Acceptance criteria for the audit deliverable

- AC1: Verify the canonical SRS path/hash and unsigned state; do not use old SRS copies or §32 as product requirements.
- AC2: Trace the Teacher screen inventory in §21.5 and use cases/requirements to current routes and checked frontend API methods.
- AC3: Distinguish supported API-backed screens from absent/partial contracts; do not present fixtures, unavailable routes, or local success as product behavior.
- AC4: Present a compact Teacher IA and demo-screen set that reduces clutter while retaining required SRS steps and privacy/authorization gates.
- AC5: Record the visual-evidence limitation: use prior local captures if a fresh loopback preview cannot be read; do not claim fresh browser validation.
- AC6: Make no application code change. Wait for direct user confirmation before any Teacher UI implementation.

### Candidate implementation boundary after user confirmation

If the user approves the proposed direction, a separate implementation authorization/plan revision is required before code. The proposed first prototype is limited to Teacher web UI plus FEAT-066 evidence/governance in this worktree. Keep API-blocked flows visibly unavailable, preserve one-child/server-selection and consent boundaries, keep Teacher/Manager/Admin role boundaries, and do not add backend behavior, fake data/success, real child data, Parent/mobile, tests/builds, commit or push unless separately authorized.

## Revision 21 — semantic crayon outline navbar icons across three web roles

- Status: APPROVED_FOR_IMPLEMENTATION.
- Direct authorization: User request on 2026-11-11 (Asia/Bangkok): replace navbar icons whose symbols do not match their actions; retain the crayon style with monochrome outline-only icons.
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Canonical SRS baseline: FEAT-063 v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; unsigned. This is a visual/navigation affordance correction only.

### Scope

- Update the shared navigation-variant SVG renderer in apps/shared/RoleDashboardIcon.tsx and semantic icon names in the Teacher, School Manager and Platform Admin role-shell navigation call sites.
- Include adjacent role/context/quota/logout/notification icons in those same shells where the current symbol does not describe the control.
- Use a friendly hand-drawn/crayon character through rounded, slightly organic strokes. Each glyph is one currentColor outline with no internal color fill or multicolor treatment. Preserve a subtle same-color sketch edge only if it remains legible at the smallest displayed size.
- Keep one consistent bell outline for all notification controls.
- Change only icon glyphs/mappings and navigation variant rendering. Do not change layout, menu labels, routes, actions, state, role authorization, target sizes, or page-content icon styling.

### Semantic mapping

- Teacher: overview → home; classes/students → users; classroom lessons group → classroom/board; lesson management and public library → book/library; AI assistance → wand/sparkle; sample video → video; classroom projection → projector/screen; history/reports → history/report; personal profile → user; settings → gear; role mark → teacher; video quota → gauge/video quota; notifications → bell; logout → exit.
- School Manager: overview → home; teachers/groups → users; classes/capacity → classroom; video quota → gauge/video quota; public review → shield-check; settings → gear; school context → school; notifications → bell; logout → exit.
- Platform Admin: overview → home; organizations → building; lesson library → book/library; activity catalog → catalog/grid; quota/policy → sliders; audit log → audit/log; platform role → shield; notifications → bell; logout → exit.

### Acceptance criteria

- AC1: Every navbar glyph describes its visible label/action in all three role shells; no palette used for Teacher identity, leaf for activity catalog, lock for quota policy, star for lesson library, play triangle for classroom projection, or unrelated sparkle for quota.
- AC2: All navigation and notification glyphs are outline-only, monochrome currentColor, rounded and crayon-friendly; no emoji or semantic multicolor/fill.
- AC3: Maintain readable line weight at desktop/narrow sizes and dark/light themes; preserve accessible names and decorative aria-hidden behavior.
- AC4: Manually review Teacher, School Manager and Platform Admin dashboards at 1440x900 and 390x844 plus dark desktop; save screenshots and note overflow/render/runtime observations.
- AC5: Do not change page-content icons, layout, copy, routing, business behavior, APIs, backend, mobile/Parent, apps/admin-ui, package/lockfiles, external assets, tests/builds, commit, or push. Preserve existing dirty worktree changes.
- AC6: Update FEAT-066 context, decisions, evidence and status; leave the worktree uncommitted for user review.

### Review workflow

1. Confirm the designated worktree, branch and existing dirty state.
2. Record this plan hash and matching direct-user approval before source changes.
3. Update the shared semantic glyph paths and only the three role shell mappings.
4. Use isolated loopback captures for the three role dashboards at desktop/narrow and dark desktop; inspect output visually.
5. Record results and stop without commit or push.

## Revision 23 — complete crayon Web UI design preview across three roles

- Status: APPROVED_FOR_DESIGN_PREVIEW_ONLY; APPLICATION_IMPLEMENTATION_NOT_APPROVED.
- Direct authorization: User request on 2026-11-11 to use design-taste-frontend, ui-ux-pro-max, frontend-design and relevant skills to create a complete crayon UI set aligned with the latest SRS for review before implementation.
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Canonical SRS: FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md, v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5. Authority confirms it is unsigned and awaiting owner sign-off. §§1–31 are target requirements; §32 is source/as-built evidence only.
- Boundary: create a traceable screen/flow atlas and generated design boards only. Do not change app source or treat generated visuals as product/design sign-off.

### In-scope web design set

- Shared Auth entry and role-mismatch/loading/error states for Teacher, School Manager and Platform Admin. Content Admin is a permission within Platform Admin, not a fourth role. Authentication and role assignment remain server-resolved; the UI cannot grant or self-assert authorization.
- Teacher: assigned org/class context; roster and structured profile; lesson library/editor/version; document upload/extraction/revision review; occurrence and plan/objective/story direction/activity checklist; optional white 16:9 AI Sketch Deck; server-selected single-child review; one-artwork capture/upload; idea/audio and transcript review; subject/context review; script/storyboard revision approval; truthful job/error/reconciliation states; safe playback; explicit projection confirmation; complete/cancel/delete lifecycle; school quota summary; occurrence/run history; notification/settings.
- School Manager: org overview; effective class capacity and create/archive/suspend; teacher directory/provision/assignment/reassignment/offboarding; org-scoped roster; exact-version public-lesson review; billing/invoice/payment status and renewal/downgrade; capacity/quota/top-up; inbox; org feedback/reply; account/settings.
- Platform Admin: permission-aware lesson/catalog draft, review, immutable publish version and hide/revoke; activity catalog revisions; org/role/permission surface only where authorized; health, aggregate queue/job, billing reconciliation, lifecycle backlog using metadata only; audit surface. System Operator remains a technical principal, not another product role.
- Excluded: Parent Android/mobile UI, backend/API implementation, other Admin app, real accounts or child data.

### Design and trust rules

- Use one shared crayon school design system with role-specific tasks/navigation; retain the user-approved warm paper/graphite/school-blue direction, restrained school-color accents and single-color outline navbar icons. Avoid dense KPI walls, nested cards, decorative scenes and unnecessary gradients.
- Show desktop and narrow layouts plus focus, permission, empty/unavailable, error/recovery and lifecycle states.
- School Manager and Platform Admin never see child media/story by default. Teacher media is limited to assigned class/run and exactly one child per run; never design batch generation from a roster.
- Separate SRS target from current API support. Mark unsupported flows visibly unavailable. Do not fabricate success, transactions, roster/child data, progress percentages, prices, consent or policy values. Keep owner-open decisions open.
- Generated assets stay in features/FEAT-066-fe-ui-srs-full-review/assets/generated/rev23 with provenance. Do not promote to approved/applied or app code before user acceptance.

### SRS traceability

- Roles, access and privacy: §§2–3, 20, 31.3.
- Teacher: §5.2; UC-03/04/05/17; §21.5–21.6; NFR-33 for projection surface.
- School Manager/billing: §5.3; UC-06/08/12/13; UC-10/15/16 for quota, inbox and feedback; §21.5–21.6.
- Platform Admin/content and operations: §§3, 20; UC-14/15; §21.5–21.6; §31.3.
- UI sign-off remains OI-17 §14.1. This preview informs review; it does not close OI-17 or make the unsigned SRS final.

### Acceptance criteria

- AC1: Deliver a complete screen/flow atlas for the in-scope screen families with SRS traceability and known FE API support status.
- AC2: Generate four coherent review boards: shared Auth/design language, Teacher, School Manager, and Platform Admin, with Vietnamese primary labels.
- AC3: Show desktop and narrow layout and enough states to review hierarchy, navigation, forms, revision approval, empty/unavailable, error/recovery, permissions and lifecycle.
- AC4: Make API-blocked and owner-open actions explicit; preserve role/privacy and one-child/revision approval rules; invent no data, price or success.
- AC5: Save generated assets/provenance only in FEAT-066 generated/evidence folders; visually inspect and record image text limitations.
- AC6: Update context, decisions, evidence and status; wait for user review before creating implementation approval.
- AC7: No Parent/mobile, backend/API, package/lockfile, other app, automated test/build, commit or push.

### Workflow

1. Verify worktree, branch, SRS authority and hash.
2. Record plan and matching direct-user design-preview approval.
3. Build the route/flow atlas from SRS target requirements and use existing FE API audit only as implementation-status evidence.
4. Generate four boards to assets/generated/rev23, record prompts/provenance, and inspect them.
5. Update evidence/status and stop for user review. Application implementation remains unapproved.

## Revision 24 — full three-role web UI rebuild from accepted crayon concept

- Status: APPROVED_FOR_IMPLEMENTATION.
- Direct authorization: User instruction on 2026-11-11 (Asia/Bangkok): replace the old web UI throughout with the Rev23 crayon concept, follow the latest SRS, and check each completed part once before continuing.
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Canonical product source: FEAT-063 SRS v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; authority confirms unsigned/awaiting owner sign-off. §§1–31 define target requirements; §32 is as-built/source evidence only.
- Accepted visual reference: FEAT-066/assets/generated/rev23/auth-portals.png, teacher-flows.png, school-manager-flows.png and platform-admin-flows.png. The plan hash and direct authorization must be recorded before source edits.

### Scope

Rebuild the presentation layer and information architecture of the shared web authentication entry and the three SRS web applications:
1. Shared Auth and role resolution UI.
2. Teacher portal.
3. School Manager portal.
4. Platform Admin portal, with Content Admin as a permission within Platform Admin.

Replace obsolete visual shells/layouts/pages/styles with the accepted paper-and-crayon direction. Preserve existing route contracts, role guards, authentication, API adapters, supported actions and business behavior. Remove/recompose existing UI rather than deleting supported product workflows. Use existing contracts only; keep unsupported flows visibly unavailable. Use a common token/component layer where it reduces duplication, with role-specific navigation and tasks.

Design direction: warm paper #FFF9F0, oat #F2EBDD, graphite #25241F, school blue #245B9B, restrained semantic school-color accents, friendly single-color outline icons, gear for settings. Desktop and narrow web layouts must remain readable and operable.

### Requirements and safety boundaries

- Follow role/tenant access from SRS §§2–5, 19–21 and 31.3. Auth never assigns a role from a client-selected link.
- Teacher flow follows §5.2/UC-03/04/05/17, FR-T and §21.5–21.6: exact lesson/revision lineage, server selection of one eligible child followed by Teacher confirmation, optional blank 16:9 Sketch Deck, no batch generation; all unresolved Q-01 policy stays open.
- School Manager follows §5.3, UC-06/08/10/12/13/15/16, FR-SM/PL and §21.5–21.6: organization capacity/class lifecycle, exactly one active Teacher per class, tenant-scoped roster, exact immutable-version review with separate approve/request-changes states, billing/quota/inbox/feedback only when contracts support them.
- Platform Admin follows §3, UC-14/15, FR-PL, §20, §21.5–21.6 and §31.3: permission-aware content/catalog versions, aggregate operations and audit metadata only; no default child media/story access. System Operator is not a product role.
- Do not fabricate people, children, classes, lessons, counters, job progress, success toasts, invoices, charges, payment history, prices, consent rules, commercial terms or open policy values. Do not use production services, credentials, real user/child data or external providers.
- Out of scope: Parent UI/mobile/native, apps/admin-ui, backend/API/contracts, packages/manifests/lockfiles and external services.
- Do not commit or push. Do not run automated tests/builds under the standing user instruction; use the requested manual UI/SRS review only.

### Acceptance criteria

- AC1: Shared Auth and all three role shells/pages use one coherent crayon design system based on the accepted boards, with functional navigation, role-correct labels, semantic outline icons, clear hierarchy and visible logout.
- AC2: Existing authenticated routes, role/tenant authorization, API calls and supported interactions remain correct; no client-side role self-assignment or cross-role handoff is introduced.
- AC3: Screen families in SRS §21.5 and required flows in §§5/19/20/21.6/31 are represented in the UI. Unsupported API-backed steps state the missing dependency clearly and do not simulate success.
- AC4: Teacher one-child/server-selection, consent/context, exact revision, safety, playback/projection and lifecycle gates are respected. School Manager and Platform Admin never see child media/story by default.
- AC5: Review each section in order (Auth, Teacher, School Manager, Platform Admin). After each section, manually compare route/flow behavior to SRS and inspect desktop 1440x900 and narrow 390x844 in the local loopback preview; correct issues and record screenshots/observations before continuing to the next section. Check keyboard focus/semantics on Auth and primary navigation, narrow overflow and truthful API states.
- AC6: Keep work only in apps/shared, apps/teacher-ui, apps/school-manager-ui, apps/platform-admin-ui and FEAT-066 governance/evidence. Preserve all pre-existing worktree changes outside the specific files deliberately rebuilt.
- AC7: Update context, decisions, evidence and status at each section checkpoint. No automated tests/builds, commit or push.

### Workflow

1. Verify this worktree/branch, dirty state and canonical SRS authority/hash.
2. Record this scope and direct user approval with the exact plan hash.
3. Inventory current route/API contracts and preserve a starting manifest of existing dirty files.
4. Rebuild Auth, then manually check and record it before proceeding to Teacher.
5. Rebuild Teacher, then manually check SRS flow/API boundaries and responsive states before proceeding to School Manager.
6. Rebuild School Manager, manually check role boundaries, separate review outcomes and unavailable commercial/communication states before proceeding to Platform Admin.
7. Rebuild Platform Admin, manually check permission-gated content/catalog and metadata-only operations.
8. Update EV-026 or add per-section evidence, refresh final status/context/decisions and stop for user review without commit/push.

## Revision 25 — dashboard alignment pass against Rev23 boards

- Status: APPROVED_FOR_IMPLEMENTATION by the user's direct request on 2026-11-11 to improve the second UI pass while keeping the base frame.
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Canonical SRS remains FEAT-063 v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; unsigned.
- Visual reference remains `assets/generated/rev23/teacher-flows.png`, `school-manager-flows.png`, and `platform-admin-flows.png`.

### Scope

Refine only the three authenticated role overview dashboards (Teacher workbench, School Manager overview, Platform Admin overview) to match the Rev23 screen hierarchy more closely and reduce visual noise. Preserve the accepted role shell, sidebar/header, logout, all routes, supported API behavior, role checks and unavailable dependencies. Keep Auth and non-overview detail routes unchanged. Remove redundant preview/status copy and quick-link grids where the same routes already exist in the sidebar. Use fewer, clearer dashboard cards with short labels and real API-backed empty/loading/error states. Keep the Teacher privacy boundary visible and keep School Manager/Admin unavailable states truthful.

Out of scope: new product flows, API/backend changes, data/model changes, Parent/mobile, other Admin UI, generated image assets, package files, automated tests/builds, commit and push.

### Acceptance criteria

- AC1: Preserve each role's existing base frame, role label, navigation, keyboard behavior and logout.
- AC2: Dashboard hierarchy matches the respective Rev23 board: Teacher has three work areas; School Manager has organization status and services; Platform Admin has health, queue, billing and lifecycle status. Remove duplicate route shortcuts already in the sidebar.
- AC3: Show no invented records/counts/progress/prices/health. In local preview, use one concise preview signal in the shell and avoid repeating the same banner in dashboard content.
- AC4: Preserve SRS privacy and authorization limits and visible API dependencies; no role or data access changes.
- AC5: Manually inspect all three overview routes at 1440×900 and 390×844, record screenshots and verify no overflow, Vite overlay, runtime exception or console error. Recheck mobile drawer keyboard focus and visible logout.
- AC6: Update context, decisions, evidence index and status. Leave all work uncommitted and unpushed.


## Revision 26 — paper-and-crayon content canvas background

- Status: APPROVED_FOR_IMPLEMENTATION by the user's direct request on 2026-11-11 to make the background match the Rev23 UI demo.
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Canonical SRS remains FEAT-063 v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; unsigned. The Rev23 generated boards are visual references, not replacement product requirements.

### Scope

Apply a subtle warm paper texture with sparse crayon corner marks behind the content canvas of Teacher, School Manager, and Platform Admin web screens. Keep the existing sidebar, topbar, cards, typography, routes, behaviors, API state, and authorization unchanged. Use local CSS only, with no external requests, new image asset, package, or backend change. Auth and all Parent/mobile surfaces are excluded.

### Acceptance criteria

- AC1: Each of the three role content canvases has a restrained paper/crayon background inspired by its Rev23 board; the effect remains behind UI content and does not reduce text/control readability.
- AC2: Existing role frame, navigation, cards, colors, routes, API behavior, permission boundaries, and privacy boundaries remain unchanged.
- AC3: Manually inspect overview and a representative detail/unavailable route for each role at 1440×900 and 390×844; record screenshots and confirm no clipping, horizontal overflow, Vite overlay, runtime exception, or console error.
- AC4: Local browser review is loopback-only; no production/provider, real user/child data, automated tests/builds, commit, or push.
- AC5: Update FEAT-066 context, decisions, evidence, and status; preserve all existing worktree changes.

## Revision 27 — shared three-role web authentication redesign

- Status: APPROVED_FOR_IMPLEMENTATION by the user's direct request on 2026-11-11 to use brainstorm and frontend design skills to rebuild the web login UI.
- Worktree/branch: `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`, `codex/fe-ui-web-remediation`.
- Product authority: FEAT-063 canonical working SRS v2.7-draft Rev57, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`; authority record confirms it remains an unsigned draft. Rev23 `auth-portals.png` is visual reference only.
- Role names: Teacher, School Manager and Platform Admin are the three web portals. Content Admin is a Platform Admin permission, not a separate role. Parent remains a separate Android/mobile scope.

### Approved scope

Redesign the shared `/login` presentation in `apps/shared/WebPortalLoginPage.tsx`, `apps/shared/portal-login.css`, and the existing `apps/shared/PortalLoginScene.tsx` only as needed. Apply the brainstorm recommendation: a Vietnamese-first crayon learning-studio composition with the login form as the primary action, a clear three-portal link selector, role-aware heading/accent, and the existing school model scene on desktop with a static SVG fallback. Reuse the current visual tokens and installed Three.js; do not add assets or dependencies.

Preserve all three existing portal URLs and role mappings, `signInAndResolveRole`, Firebase/backend behavior, pending and error states, local preview labeling and navigation, post-login destinations, authorization checks, and role-mismatch behavior. Do not add password reset, support, organization selection, onboarding, provider, or other auth flows unless an existing contract is already used. Do not introduce fake success, sample accounts, credentials, user data, or production calls.

Out of scope: Parent/mobile, Teacher/Manager/Admin authenticated screens, backend/contracts, login provider/auth semantics, environment or secret changes, package/lockfiles, generated raster assets, tests/builds, commit and push. Keep all changes in the shared login source and FEAT-066 records/evidence.

### Acceptance criteria

- AC1: The three existing web login routes use one coherent, school-friendly crayon layout. The role and primary login action are immediately clear; the visual hierarchy works at desktop and narrow widths.
- AC2: Each page names its correct role and links only to the existing Teacher, School Manager or Platform Admin login URL. The active portal is semantically identified; keyboard order and focus are visible; no cross-role session is created by switching links.
- AC3: Real login continues through the existing auth/API adapter with unchanged role verification, pending/error behavior and destinations. Local preview remains unmistakably non-authenticating and does not claim backend success. Platform Admin's existing role-discovery limitation remains visible.
- AC4: Preserve privacy/security boundaries and avoid invented help/reset/onboarding, price, organization, or account data. Parent remains outside the web portal set.
- AC5: Manually inspect all three login pages at 1440×900, 1024×768, 768×1024 and 390×844. Verify no horizontal overflow, overlapping/cut content, browser/runtime error, or remote request; inspect keyboard focus and portal links. Use the existing Three.js scene only with a static fallback and reduced-motion/performance behavior.
- AC6: Record 12 local screenshots and observations in FEAT-066. Update context, decisions, evidence and status. No automated tests/builds; leave every change uncommitted and unpushed.



## Revision 28 — Rev68 web audit, structure cleanup and UI rebuild

- Status: APPROVED_FOR_IMPLEMENTATION by the user's direct request on 2026-11-16 (Asia/Bangkok): clean the app structure, rebuild and correct the web UI against the SRS, follow the named frontend/UI skills, make one commit, and start the app for review.
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Product baseline selected by the user for this task: F:/Downloads/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md, v2.7-draft Rev68, SHA-256 69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944; unsigned. The repository's FEAT-063 copy and older FEAT-066 plans are not the baseline for this revision. Do not change SRS documents or claim sign-off.
- UI method: use the named design-taste-frontend, ui-ux-pro-max, frontend-design and senior-frontend skills. Treat this as an authenticated product app: apply their hierarchy, copy, interaction, focus, responsive and visual-quality guidance without forcing a marketing hero or invented product proof into role dashboards.

### Approved scope

- Review all apps/web routes and surfaces for Teacher, School Manager (BE1-backed and clearly separated preview), Platform Admin, and shared login against Rev68.
- Clean apps/web/src into one app/router, shared UI/auth/API boundary, and role-owned modules. Remove duplicate or role-misplaced copied screens/components only after imports and routes are migrated. Preserve supported API/auth behavior, direct deep links, role mismatch, and non-persistent preview disclosure.
- Rebuild the shared design system and role shells/pages so each available action and unavailable SRS target is clearly distinguished. Keep SRS flows with missing APIs read-only/unavailable; do not simulate success or fabricate records, metrics, permissions, consent, prices, or child data.
- Preserve Rev68 product boundaries: Teacher presentation edits create drafts and published revisions are immutable; School Manager reviews school-public scope; Platform Admin review is capability-gated for platform-public scope; Content Admin is a permission, not a role; Platform Admin has no child media/story access by default; Parent remains Android. A story run belongs to one child and one occurrence. Do not introduce classroom collaboration runtime, shared drawing canvas, QR/lobby/admission, batch multi-child processing, PixiJS, freeform SVG/HTML/JS guide generation, or FLUX fallback.
- Keep current web API/backend, Android/mobile, deployment, secret, and data-model behavior unchanged. Do not add dependencies or generated raster assets unless already required by an existing contract.
- Preserve and include the currently requested FEAT-067 app consolidation and related FEAT-066 web work in the user's requested single local commit, after reviewing the full staged path list and security scan. Commit once; do not push.
- Start the local Vite web app and leave it running for user review.

### Acceptance criteria

- AC1: One apps/web entry/router remains. src/app, src/shared, and src/modules/{teacher,school-manager,platform-admin} have clear ownership; no duplicated Teacher app screens are left inside School Manager or Platform Admin modules, and each routed page imports from its owner.
- AC2: Login, route guards, role mismatch, supported API calls, loading/error/empty states and the BE1-backed School Manager class workflows remain truthful and functional. The School Manager preview stays visibly non-persistent and cannot be mistaken for BE1 state.
- AC3: Teacher pages represent the Rev68 editable presentation and one-child/one-occurrence story boundaries. Missing slide/media/story-run/playback/lifecycle APIs are named as unavailable; no unsupported collaboration, multi-child, child selection, or fabricated completion is implied.
- AC4: School Manager approval is limited to school-public content; Platform Admin content review is permission-gated and limited to platform-public scope. Default Platform Admin surfaces contain no child media/story. Published revisions are presented as immutable.
- AC5: UI uses a coherent role-aware visual system, semantic navigation/forms/dialogs, visible keyboard focus, usable touch targets (44px minimum where applicable), reduced-motion support, and clear loading/empty/error/unavailable feedback.
- AC6: Manually inspect shared login and one overview plus representative available/unavailable route for each role at 1440x900, 768x1024 and 390x844. Confirm role labels, route behavior, keyboard focus, readable responsive layout, no horizontal overflow, no runtime/console errors, and no unsupported external requests. Record screenshots and observations under FEAT-066 evidence.
- AC7: Record the SRS trace, implementation decisions, inventory, screenshots, limitations and completion status in FEAT-066/FEAT-067. Preserve the earlier feature histories.
- AC8: Run the required repository security/harness/architecture checks and git diff --check before the one local commit; report any pre-existing or structural validator findings accurately. Do not add or run application tests.
- AC9: Make exactly one local commit containing the reviewed FEAT-067 consolidation plus this approved web UI/structure work and related feature records; leave the dev server running and report its loopback URL. Do not push.

### Workflow

1. Record this plan hash and direct-user approval; capture the existing dirty-path baseline before application edits.
2. Trace Rev68 target flows and current routes/API states; record a compact route-to-SRS/API matrix and decide which surfaces are available, preview-only, or unavailable.
3. Simplify role ownership and shared structure, then rebuild Auth and role surfaces without changing API or authorization contracts.
4. Start the local app; inspect Auth, Teacher, School Manager and Platform Admin at the approved viewports and correct observed issues.
5. Update FEAT-066/FEAT-067 context, decisions, evidence and status. Run required validators and inspect every staged path, then create one local commit.
6. Leave the local preview server running for the user.

### Out of scope

Parent/Android/mobile, backend/API/authorization changes, new SRS policy decisions, production services/data, credentials/secrets, dependencies, deployment, push/PR/merge, and automated application tests.


## Revision 29 — role login landing and remove local preview UX — 2026-11-16

- **Status:** APPROVED_FOR_IMPLEMENTATION from the user's direct follow-up in this conversation.
- **Worktree/branch:** `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`, `codex/fe-ui-web-remediation`.
- **SRS:** Continue the Rev68 task baseline already recorded in Revision 28. The separate repository Rev60 source-register mismatch remains open and unchanged.
- **Scope:** Make `/login` the only role-selection landing and remove its School Manager preview panel. Visiting `/teacher/login` must show that same role-selection page; selecting Teacher proceeds to the real Teacher sign-in at `/teacher/sign-in`. School Manager and Platform Admin selections continue to their real sign-in routes. Remove the local preview authentication bypass and the School Manager fixture-preview route/UI from active navigation/routing. Preserve current real Firebase/BE1 and Teacher API integrations; keep missing APIs clearly unavailable after authenticated entry. Preserve the existing single local commit by amending it after checks; no push.
- **Acceptance criteria:**
  - AC1: `/login` and `/teacher/login` show the attached role-entry composition; the preview panel and all user-facing preview login actions/banners are absent.
  - AC2: Role cards open the corresponding real sign-in flow; no local-only action can set a signed-in role or bypass Firebase/backend role verification.
  - AC3: `/school/preview/*` no longer renders fixture content and redirects to the role entry. BE1 School Manager routes stay distinct and preserve their authorization/API behavior.
  - AC4: Teacher and Platform Admin login preserve the existing auth/role-resolution adapter. Missing Platform Admin role discovery remains a visible backend limitation; no mock session or fake API success.
  - AC5: Existing supported class, lesson, document and BE1 review calls remain intact. Unsupported product APIs remain clearly unavailable; no child/media/sample data is fabricated.
  - AC6: Capture and inspect the shared role-entry at desktop/mobile, Teacher sign-in route, and a real School Manager login route. Verify route destinations, form presence, no preview copy, no horizontal overflow, and usable keyboard focus.
  - AC7: Update FEAT-066 context, decision, evidence and status; preserve the Rev28 history and the single-commit delivery.
- **Out of scope:** Backend/API/role-discovery changes, Firebase setup or credentials, new product roles, changes to available contracts, Parent/mobile, automated application tests, push, PR, merge, or deployment.

## Revision 30 — shared single-screen role login — 2026-11-16

- **Status:** APPROVED_FOR_IMPLEMENTATION by the owner's direct correction in this conversation.
- **Worktree/branch:** `codex/fe-ui-web-remediation`; current baseline commit `df07438e690cabf93ec9feacedcc5b6e3ca2709d`.
- **Product SRS:** continue the owner-selected unsigned v2.7-draft Rev68 task baseline recorded in Rev28. The repository source register remains at unsigned v2.7-draft Rev60; preserve that mismatch as open and do not edit SRS authority records. For identity and access behavior, follow FEAT-063 FR-C-01 and the rule that Firebase proves identity while the backend resolves application role/scope.
- **Design basis:** the attached Teacher sign-in screen is the approved reference. Treat this as an authenticated product-app screen; reuse the existing Sketch2Life login composition and controls, with `design-taste-frontend`, `ui-ux-pro-max`, `frontend-design`, `senior-frontend`, `clean-code`, and the Sketch2Life harness applied to hierarchy, responsive layout, keyboard access, async feedback, route composition, and evidence. No generated or remote visual asset is needed.
- **Scope:** make `/login` render the shared sign-in composition directly, defaulting to Teacher. Remove the standalone role-card chooser. Change role selection inside the same shared screen and layout for Teacher, School Manager, and Platform Admin. Legacy sign-in URLs resolve to `/login` with the appropriate role selected so School Manager does not open a second login design. Preserve the existing Teacher/Firebase role-resolution adapter, the School Manager BE1 Firebase login adapter and post-login assignment gate, and the Platform Admin missing-role-discovery error. Remove the obsolete standalone School Manager login UI after routing is unified. No API, authorization contract, provider, session-bypass, or mobile change.
- **Acceptance criteria:**
  - AC1: `/login` opens the reference sign-in layout and form immediately; the separate role-card page and preview panel are absent.
  - AC2: changing role updates the selected panel in the same layout and keeps the user on `/login`; direct compatibility routes select the same role without rendering a different page.
  - AC3: Teacher sign-in continues through Firebase identity and backend assignment role resolution; an unexpected role is rejected and signed out.
  - AC4: School Manager sign-in continues through the existing BE1/Firebase adapter and `school_admin` assignment gate after authentication; it never falls into the Teacher route or a duplicate login layout.
  - AC5: Platform Admin remains unable to start an authenticated product session until backend role/capability discovery exists; no client-selected role grants access.
  - AC6: form pending/error feedback, semantic labels, visible keyboard focus, 44px touch controls where practical, reduced-motion behavior, readable contrast, and no mobile horizontal overflow are retained at 1440×900 and 390×844.
  - AC7: route switches and legacy redirects are inspected in the local browser; record screenshots and observations under FEAT-066. Do not enter credentials or submit auth/API requests.
  - AC8: keep FEAT-066 evidence/context/decision/status current; build, architecture, security, harness and diff checks are recorded; do not run application tests under the existing task boundary.
  - AC9: amend the already-approved single local commit once the final staged set is reviewed. Keep the local app running. No push, PR, merge, or deployment.
- **Out of scope:** backend/API/auth contract, role discovery, new permissions or roles, Parent/mobile, real credentials/data, dependencies, production services, and automated application tests.
