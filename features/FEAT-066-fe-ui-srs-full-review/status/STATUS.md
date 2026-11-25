# FEAT-066 status

- Status: AUTH_UI_REDESIGN_REV27_APPROVED_IMPLEMENTATION_IN_PROGRESS
- Updated: 2026-11-11 (Asia/Bangkok)
- Active plan: revision 27, SHA-256 C9EF609A920F3C53F0153ED109660B85003D4D03A8E1E76C2F46C3EB2EEF21C2; shared three-role web authentication presentation redesign.
- Approval: user directly requested a shared login UI redesign using brainstorm and frontend design skills; matching Rev27 plan hash C9EF609A920F3C53F0153ED109660B85003D4D03A8E1E76C2F46C3EB2EEF21C2 is recorded in approvals/TASK_APPROVAL.md before source edits.
- Product baseline: FEAT-063 SRS v2.7-draft Rev57, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`, still unsigned.
- Current scope: Rev27 auth presentation only for the existing Teacher, School Manager and Platform Admin `/login` pages. Parent/mobile, authenticated role UI, backend/contracts and authentication semantics remain out of scope.

## Follow-up finding and resolution

Before revision 5, the authenticated M02 dashboard and settings routes lacked a visible logout control. Revision 5 exposes `TeacherContext.logout` from ManagerLayout; that existing handler clears the web role/auth session keys, invokes configured Firebase sign-out when present, and causes protected routes to return to `/login`. AC12–AC13 were manually verified and the results are recorded as EV-005. The SRS does not list a School Manager logout screen/control in §21.5; this is a user-reported FE defect, not a newly inferred product requirement.

## Previously completed revision 4 work

M01 outcome counters, accessible tabs, unavailable inbox state, static organization context and M02 responsive/unavailable states remain implemented and integrated. The before/after route review remains in EV-004; its plan hash was `D9780223AB395C1B5A9942F4011B749A2A15E3D66283A178F768AF9E9AC0CCB6`. Existing API dependencies and limits are recorded in EV-003.

## Revision 5 approved verification criteria

- Show logout on authenticated M01 and M02 pages using the existing callback.
- Manually test sign-out from M02 dashboard/settings at 1440x900 and 390x844; confirm `/login`, removal of `s2l-web-role` and `s2l-web-authenticated`, and protected-route redirect after logout.
- Save before/after screenshots and interaction observations inside FEAT-066 evidence. No production backend, provider, credential, or real user data.
- No automated tests/builds unless the user asks. Run repository security validation before commit/push; retain non-force integration behavior and preserve unrelated worktree edits.

## Revision 5 logout verification

- Added a visible `Đăng xuất` button to the shared authenticated Manager sidebar and reused `TeacherContext.logout`.
- Manual browser review passed on dashboard and settings at 1440x900 and 390x844. The button remained visible, was keyboard-focusable with Enter activation, and measured 44x44px in the collapsed narrow sidebar.
- Each logout returned to `/login`, removed `s2l-web-role` and `s2l-web-authenticated`, and a direct attempt to revisit the protected route remained at `/login`.
- Screenshots, route/session observations, and capture helper are recorded as FEAT-066-EV-005. Preview used only a synthetic local session; Firebase sign-out was not configured or tested.
- No tests/builds/scanners were run. Repository security validation remains required before commit/push.

## Integration history

Revision 4 code commit `c43f4b0a` and status commit `55485a07` were pushed without force to `origin/feature/fe-ui-full-remediation`. The separate local target worktree contains unrelated uncommitted Parent mobile/UI and FEAT-036/067/068/069 changes and remains untouched.



## Revision 6 flow-guide deliverable

- Added `evidence/notes/SCHOOL_MANAGER_WEB_FLOW_TEST_GUIDE_V27.md` after plan revision 6 and approval recorded the direct request.
- It enumerates login/tenant context, dashboard, class capacity/lifecycle, Teacher provisioning/assignment/transfer, roster, billing/subscription, organization quota, inbox, M01 lesson review, school-scoped feedback, privacy checkpoints, and logout.
- Every flow is tied to SRS v2.7 references, current UI route/absence, source-checked API support, safe local review steps, expected result, and backend blocker.
- Evidence index entry: FEAT-066-EV-006. It does not authorize production/backend calls or change the FE-only implementation scope.

## Integration result

- Commit `52e84c15` contains the School Manager logout action, the Rev57 sequential flow guide, and the associated QA screenshots/observations.
- Pushed non-force to `origin/feature/fe-ui-full-remediation` on 2026-11-10; remote target advanced from `55485a07` to `52e84c15`.
- Source changes were made only in `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation` on `codex/fe-ui-web-remediation`. Unrelated Parent UI, root approval, and FEAT-070 worktree changes were not staged or modified.

## Revision 6 School Manager double-check (2026-11-10)

- Re-read the canonical authority and verified FEAT-063 v2.7-draft Rev57 SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`; it remains unsigned.
- Confirmed repository root/worktree `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`, branch `codex/fe-ui-web-remediation`, starting HEAD `bd55ffd8cff06d0f395f1afa5a8a8ac4081d5c75`. Existing unrelated root approval, Parent UI, and FEAT-070 worktree changes remain unstaged and untouched.
- Reused loopback School Manager Vite preview at 127.0.0.1:5173 (PID 19084); recaptured `/login`, M01 and all M02 sections at 1440x900 and 390x844 in EV-007. No backend/provider/credentials/real data; no automated tests or builds.
- Confirmed M01 request-change counters `pending=2`, `approved=0`, `requested_changes=1`; tab/panel ARIA references and ArrowRight selection/focus; static inbox status with no unread dot; static organization context; no document horizontal overflow. Narrow class/quota actions remain inside the viewport; the class table uses an internal horizontal scroll region.
- Double-check removed an unsupported monthly-only implication from the unavailable auto-renew label (`Tự động gia hạn`). M01's four-check approval rubric is unlisted in FR-PL-05 and remains an owner clarification, not an inferred SRS requirement.
- Existing contract blockers remain: capacity-safe class creation/archive/suspend; Teacher directory/provisioning/assignment transfer; group flow; invoice/payment/subscription; organization quota/top-up; inbox; school feedback reply. Class list/profile-list read and M01 access-grant list/decision are source-checked, not authenticated end-to-end runtime tested. Child media remains absent.
- Detailed evidence: `evidence/notes/SCHOOL_MANAGER_WEB_DOUBLE_CHECK_REV57_20261110.md`; screenshots and capture observations: `evidence/screenshots/double-check/`. EV-007 added to `evidence/README.md`.
- Current review is complete for the School Manager FE scope. Other portals may be reviewed after this handoff; no other portal has been checked or modified in this step.
## Repository validation results

- `python tools/validate_repository_security.py`: PASS (`REPOSITORY_SECURITY_VALID`; 6,845 publishable files scanned).
- `python tools/validate_architecture.py`: PASS.
- `git diff --check`: PASS; only CRLF-to-LF normalization warnings were printed for edited Markdown files.
- `python tools/validate_harness.py`: FAIL only because the unrelated untracked FEAT-070 feature directory lacks `evidence/raw`, `evidence/screenshots`, `evidence/metrics`, and `evidence/notes`. Left untouched because FEAT-070 is outside this approved scope.
- No tests/builds were run.

## Double-check integration result

- Commit `cebeb2e9` contains the final in-scope Settings wording correction plus EV-007 screenshots, observations, and FEAT-066 context/decision/status updates.
- `python tools/validate_repository_security.py` passed immediately before push.
- Non-force push to `origin/feature/fe-ui-full-remediation` succeeded; target advanced from `bd55ffd8` to `cebeb2e9`.
- No Parent/root/FEAT-070 changes were included. The local `codex/fe-ui-web-remediation` branch remains the active worktree branch.

## Revision 7 approval checkpoint (2026-11-10)

- Plan revision 7 is approved for implementation; SHA-256 72F462DCECE9DC2545368094FBA86E68AC3992589FD448CED5E76E82F057FD36 matches approvals/TASK_APPROVAL.md.
- Canonical SRS remains v2.7-draft Rev57 and unsigned. The approved roles are Teacher, School Manager, and Platform Admin; Parent is excluded.
- At this checkpoint, product-code edits have not started. The current task is limited to shared login UI and the three existing web /login routes. The recording is a visual reference only.
- Starting worktree status was verified on codex/fe-ui-web-remediation. Existing dirty files are root approvals/TASK_APPROVAL.md, Parent UI files, and untracked FEAT-070; they are unrelated and will remain untouched.
## Revision 7 dependency checkpoint (2026-11-10)

- Local pnpm store path did not exist; npm cache contained no Three.js packages.
- Installed exact Three.js 0.187.0 and @types/three 0.187.0 from the official npm registry in school-manager-ui, teacher-ui, and platform-admin-ui after approval hash verification. Dependency install scripts/audit were disabled. Runtime remains locally bundled; no CDN or model source is planned.
- Only the three approved app manifests and applicable npm lockfiles changed at this dependency step. No shared login source changes or tests/builds have run yet.
## Revision 7 implementation and manual review

- Shared login redesign completed for Teacher, School Manager, and Platform Admin. The three existing app routes and their role/auth mappings remain separate.
- Added the lazy local Three.js sculpture and pinned runtime/type packages only in the three in-scope web apps. No CDN/runtime assets were used.
- Captured before/after desktop 1440x900 and narrow 390x844 login screenshots for all three apps under FEAT-066-EV-008.
- Manual checks: 0 horizontal overflow at both widths; narrow submit remains visible in 844px; portal links work; Tab focus has a visible outline; Enter opens Teacher; Platform Admin link opens its correct route; reduced-motion state is static; forced WebGL context loss exposes fallback.
- Authenticated login was not exercised because the local preview has no Firebase bridge and no credentials were supplied. Teacher/Manager backend assignment resolution and Platform Admin role discovery remain outside this FE-only change; Platform Admin API blocker is recorded as ROLE_DISCOVERY_UNAVAILABLE (501). Production URLs must be configured through the documented VITE_S2L_*_LOGIN_URL variables.
- No automated tests or builds were run. Repository security validation passed on the final reviewed diff: 6,867 publishable files scanned, with no absolute machine paths. Implementation commit 89d8785d is on codex/fe-ui-web-remediation and was pushed non-force to origin/feature/fe-ui-full-remediation.
## Revision 7 three-role auth UI review (2026-11-10)

- Shared `/login` pages map Teacher, School Manager, and Platform Admin to the SRS §3 role values and expose the other two local web portal destinations. Keyboard navigation and active-role semantics are recorded in FEAT-066-EV-008.
- The first 390px capture found overlapping heading/description spacing. Mobile margins were corrected, then all six role/viewport combinations were recaptured. At 390x844, submit bottoms are 731px (Teacher), 731px (School Manager), and 750px (Platform Admin); all have 390px document width. At 1440x900, all pages fit without overflow.
- Three.js local rendering, reduced-motion static rendering, context-loss CSS fallback, and keyboard activation were reviewed. Real sign-in was not attempted; Platform Admin role discovery remains blocked by the existing API. Details and screenshots are in FEAT-066-EV-008.
- Repository security validation passed on the final reviewed diff: 6,867 publishable files scanned, with no absolute machine paths. Implementation commit 89d8785d was pushed non-force to origin/codex/fe-ui-web-remediation and origin/feature/fe-ui-full-remediation.
## Revision 7 auth UI integration (2026-11-10)

- Commit `89d8785d` (`feat(auth): redesign three web portal login pages`) was pushed fast-forward without force to `origin/codex/fe-ui-web-remediation` and `origin/feature/fe-ui-full-remediation`.
- Repository security validation passed immediately before commit and push: 6,867 publishable files scanned; no absolute machine paths.
- The local `feature/fe-ui-full-remediation` worktree was not checked out or modified because it contains unrelated changes. Its remote branch is now advanced to the reviewed commit.
- Unrelated root approval, Parent UI changes, and FEAT-070 evidence remain unstaged and unmodified.

## Revision 8 approval and flow audit checkpoint

- Plan SHA-256: C71F0824DC4A7E4901912BB2D8883B954BA6F2ED438BAB9F9C0871CBE3B54D7C; feature-local approval ledger match verified before code edits.
- SRS: v2.7-draft Rev57; canonical hash BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5, awaiting formal owner sign-off.
- Flow completeness result: incomplete against §21.5. Current API and UI coverage with exact gaps is documented in evidence/notes/SCHOOL_MANAGER_WEB_SRS_FLOW_AUDIT_REV57_20261110.md.
- Implementation has not started at this checkpoint. Next authorized step: restyle the authenticated School Manager shell/M01/M02 only and manually review local routes.


## Revision 8 implementation and review result (2026-11-10)

- Status: WEB_UI_CRAYON_IMPLEMENTATION_REV24_APPROVED_IN_PROGRESS; SECTION_1_AUTH;; ROLE_NAV_SETTINGS_GEAR_V22_COMPLETE_PENDING_USER_REVIEW; FE_REMEDIATION_COMPLETE
- Plan revision 8 SHA-256 C71F0824DC4A7E4901912BB2D8883B954BA6F2ED438BAB9F9C0871CBE3B54D7C matches feature-local direct-user approval.
- Canonical baseline remains unsigned SRS v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5.
- Final manual capture: 16 route/viewport observations across 1440x900, 768x1024 and 390x844; 0 horizontal-overflow pages and 0 disabled actions outside the viewport. M01 count separation, tab keyboard/ARIA semantics, unavailable inbox/static organization context and logout were checked in local preview.
- Evidence: evidence/notes/SCHOOL_MANAGER_WEB_THEME_REVIEW_REV57_20261110.md and evidence/screenshots/school-manager-theme-final/ (EV-010).
- No automated tests/builds or backend/provider/production calls were run. Existing unrelated root approval, Parent UI and FEAT-070 changes remain unstaged and untouched.

## Revision 8 integration result (2026-11-10)

- School Manager theme and flow-review commit: c3cf2f0d19ce6c07e1da796a661a2039118561e9.
- Pushed without force to origin/codex/fe-ui-web-remediation and origin/feature/fe-ui-full-remediation. Both remote branches advanced from 9a901ae9 to c3cf2f0d.
- Active worktree remains F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation on codex/fe-ui-web-remediation. Pre-existing root approval, Parent UI and FEAT-070 modifications remain outside the commit.

## Revision 9 dashboard palette preview — ready for review (2026-11-10)

- Status: WEB_UI_CRAYON_IMPLEMENTATION_REV24_APPROVED_IN_PROGRESS; SECTION_1_AUTH;; ROLE_NAV_SETTINGS_GEAR_V22_COMPLETE_PENDING_USER_REVIEW; FE_REMEDIATION_COMPLETE
- Direct user authorization and matching plan revision 9 SHA-256 03FF50D8330884BB815CCF8D8E68186F250DBE70279D6EC9FBD163423EFB24AC were recorded before product-code edits.
- Added a route-scoped Cool Grey + Cobalt preview on the default M02 dashboard. Other Manager routes remain on revision 8 colors.
- Manual local capture at 1440x900 and 390x844: no horizontal overflow; primary action remains inside viewport. M02 teachers and M01 computed colors remain unchanged.
- Evidence: evidence/notes/SCHOOL_MANAGER_WEB_COBALT_PREVIEW_20261110.md; evidence/screenshots/school-manager-cobalt-preview/.
- Preview is on the loopback FE at http://127.0.0.1:5173/m02-organization-management. It is uncommitted and unpushed. No tests/builds ran.

## Revision 10 — approved web-wide branding rollout (2026-11-10)

- Status: WEB_UI_CRAYON_IMPLEMENTATION_REV24_APPROVED_IN_PROGRESS; SECTION_1_AUTH;; ROLE_NAV_SETTINGS_GEAR_V22_COMPLETE_PENDING_USER_REVIEW; FE_REMEDIATION_COMPLETE
- Direct user instruction: use the supplied image as logo and apply the bright Cool Grey + Cobalt palette across the browser web apps.
- Plan revision: 10. Exact SHA-256 is recorded in approvals/TASK_APPROVAL.md.
- In scope: parent-ui browser preview, school-manager-ui, teacher-ui, platform-admin-ui, admin-ui and apps/shared web branding/styles. Native/mobile and historical parent-web are excluded.
- The SRS remains unsigned v2.7-draft Rev57 and does not specify colors.


## Revision 10 implementation result — 2026-11-10

- Implemented the supplied logo and shared bright palette across the five in-scope browser apps and shared web styles. Plan rev10 and approval hash remain matched.
- Manual local review saved as EV-012: 18 desktop/narrow captures, 0 horizontal document overflow, updated brand visible on shared portal shells, and narrow M01/M02 layouts remain within the viewport.
- Remaining review limitations: Admin UI dev preview could not start because offline npm cache lacks `@tailwindcss/vite` (`ENOTCACHED`); Parent `/p11-authentication` redirects to the already-authenticated local Parent library fixture. Source changes are present for both browser packages; no network, credentials or changes to auth behavior were used to bypass these limitations.
- No tests/builds, commit/push, APIs, backend, mobile, or unrelated existing worktree files were changed. Security validator was not run because no commit/push is being prepared.
- Evidence: `evidence/notes/WEB_BRAND_ROLLOUT_V10_20261110.md`; captures and observations: `evidence/screenshots/web-brand-rollout-v10/`.
## Revision 11 — approved three-role dashboard icon refresh (2026-11-10)

- Status: WEB_UI_CRAYON_IMPLEMENTATION_REV24_APPROVED_IN_PROGRESS; SECTION_1_AUTH;; ROLE_NAV_SETTINGS_GEAR_V22_COMPLETE_PENDING_USER_REVIEW; FE_REMEDIATION_COMPLETE
- Direct user request and matching plan revision 11 SHA-256 `0B2B90980B2D2CB491DCCC15BC1E22ED6FFCEBD3D8B21AEADE795670B9875BC1` are recorded in the feature-local approval ledger.
- Scope: authenticated dashboard iconography (shell and route content) in School Manager, Teacher and Platform Admin web role apps, plus FEAT-066 governance/evidence.
- Canonical baseline: FEAT-063 v2.7-draft Rev57, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`, unsigned.
- Next: implement the local icon family, manually review 1440x900 and 390x844 captures for each role, then record evidence. No tests/builds, commit, or push.

## Revision 11 — implementation and manual UI review complete (2026-11-10)

- Status: WEB_UI_CRAYON_IMPLEMENTATION_REV24_APPROVED_IN_PROGRESS; SECTION_1_AUTH;; ROLE_NAV_SETTINGS_GEAR_V22_COMPLETE_PENDING_USER_REVIEW; FE_REMEDIATION_COMPLETE
- Plan/approval SHA-256: 0B2B90980B2D2CB491DCCC15BC1E22ED6FFCEBD3D8B21AEADE795670B9875BC1.
- Updated the shared local SVG icon family for Teacher, School Manager and Platform Admin dashboard shells/content while preserving existing navigation and role behavior.
- EV-013: six local captures at 1440×900 and 390×844; no horizontal overflow, Vite error overlay, or observed runtime errors; nav icon tiles are 32×32px.
- No tests/builds, commit or push. Existing unrelated worktree changes remain untouched.
- Evidence note: evidence/notes/WEB_DASHBOARD_ICON_REFRESH_V11_20261110.md; screenshots/observations: evidence/screenshots/web-dashboard-icons-v11/.
## Revision 12 — shared login font correction complete (2026-11-10)

- Status: WEB_UI_CRAYON_IMPLEMENTATION_REV24_APPROVED_IN_PROGRESS; SECTION_1_AUTH;; ROLE_NAV_SETTINGS_GEAR_V22_COMPLETE_PENDING_USER_REVIEW; FE_REMEDIATION_COMPLETE
- Plan/approval SHA-256: 00D41575B3D5912DE9A2CB2D1080DC9D588C91E366D762B79092DC7F618FBCC7.
- Updated the shared login headline font rules in apps/shared/portal-login.css: existing Vietnamese-capable sans stack, upright accent, 700 weight, improved tracking and line height.
- EV-014 records six Teacher, School Manager and Platform Admin /login captures at 1440×900 and 390×844. No overflow, Vite overlay, or runtime errors; existing per-origin preview storage was restored.
- No automated tests/builds, commit or push. Existing unrelated worktree changes remain untouched.
- Evidence: evidence/notes/WEB_LOGIN_FONT_FIX_V12_20261110.md; evidence/screenshots/web-login-font-v12/.
## Revision 13 — three-role logout controls complete (2026-11-10)

- Status: WEB_UI_CRAYON_IMPLEMENTATION_REV24_APPROVED_IN_PROGRESS; SECTION_1_AUTH;; ROLE_NAV_SETTINGS_GEAR_V22_COMPLETE_PENDING_USER_REVIEW; FE_REMEDIATION_COMPLETE
- Plan/approval SHA-256: 5DF172969F85296D5A1100BB288337CD0EEFF06373CC157DE719EA59B3C6029B.
- Teacher logout moved to the sidebar account area and remains visible as a named icon button in the collapsed rail. School Manager's existing sidebar button was retained. Platform Admin now has a sidebar button wired through AdminPortalFrame to the existing logout handler.
- EV-015 records six desktop/narrow dashboard captures. All controls were visible/in-viewport with no horizontal overflow; pointer activation in each role cleared role/auth session keys and returned to /login. Focus outline: 3px cobalt. No runtime errors.
- No automated tests/builds, commit or push. Existing unrelated worktree changes remain untouched.
- Evidence: evidence/notes/WEB_ROLE_LOGOUT_V13_20261110.md; evidence/screenshots/web-logout-v13/.
## Revision 14 — three-role flow audit complete (2026-11-10)

- Current request completed as a source/contract audit only; detailed findings are FEAT-066-EV-016.
- Scope: Teacher, School Manager and Platform Admin web apps. No Parent, additional Admin UI, mobile, backend or UX implementation.
- SRS: canonical FEAT-063 v2.7-draft Rev57 verified against authority at SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; unsigned. §32 excluded from target requirements.
- Main P1 blockers: Teacher run/occurrence/projection and extraction review; School Manager exact-version content review, class/Teacher lifecycle, billing/quota/inbox/feedback; Platform Admin backend login, moderation, catalog and operations APIs.
- P2 findings and owner-open items are separated in EV-016. Existing logout controls, M01 counters, unavailable inbox signal and privacy-minimal roster are not counted as current defects.
- No application source/API changed; no tests/builds, production/backend/provider access, commit or push.
- Git verified root and branch, but git status --short --branch failed with fatal: this operation must be run in a work tree; worktree was left intact. No attempt was made to repair Git metadata or touch the main checkout.
- Product remediation remains unapproved and must have its own plan/acceptance checkpoint after user review.

## Revision 15 — FE remediation complete, pending user review (2026-11-11)

- Status: WEB_UI_CRAYON_IMPLEMENTATION_REV24_APPROVED_IN_PROGRESS; SECTION_1_AUTH;; ROLE_NAV_SETTINGS_GEAR_V22_COMPLETE_PENDING_USER_REVIEW; FE_REMEDIATION_COMPLETE
- Worktree: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation; branch codex/fe-ui-web-remediation; source baseline commit 3c1caf479eb6d6757d84890f73c07f185e32a9f9.
- Canonical SRS: FEAT-063 v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; unsigned.
- Approved plan revision 15 SHA-256 remains 86c6a13185797c8b5912ca3b6adb54b63f58d8ff87f1bebb16a6652434eb331e.
- Implemented FE-supported remediation across Teacher, School Manager, Platform Admin and shared web API client. Unsupported flows remain explicitly unavailable; details and dependencies are in EV-018.
- EV-018 contains 34 desktop/narrow route captures plus one M01 post-action screenshot (35 PNGs total) across 17 route states, interaction observations, and validation limitations. All captures show no horizontal overflow and no Vite error overlay. M01 local preview request-changes result: 2 pending, 0 approved, 1 requested.
- No automated tests/builds, authenticated backend, real data, credentials, security validator, commit, or push. Changes are left uncommitted/unpushed for user review.

## Revision 16 — auth and Teacher visual preview complete for user review (2026-11-11)

- Status: WEB_UI_CRAYON_IMPLEMENTATION_REV24_APPROVED_IN_PROGRESS; SECTION_1_AUTH;; ROLE_NAV_SETTINGS_GEAR_V22_COMPLETE_PENDING_USER_REVIEW; FE_REMEDIATION_COMPLETE
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation; codex/fe-ui-web-remediation.
- Plan Rev16 SHA-256: 9C446770A6232A9A42B8677B345D25DECB5097D1AF4DD2FFD810A100CD3A4D5D, matching the feature approval ledger.
- Scope: shared web auth presentation for Teacher/School Manager/Platform Admin, Teacher authenticated visual system/dashboard, and FEAT-066 records only. School Manager/Admin authenticated interfaces, Parent/mobile, APIs/backend and SRS-open policy remain outside scope.
- EV-019: 14 screenshots across all three login routes and Teacher dashboard/classes/lessons/Sketch Deck at 1440x900 and 390x844. No horizontal overflow, Vite error overlay or browser runtime exception. All auth submit controls fit within the narrow first viewport. Teacher local-preview login reached /t01-lesson-workspace with the TEACHER local session.
- Remaining blocker: T04 Sketch Deck still shows the existing unavailable state, so no projection surface exists to validate against NFR-33; recorded without inventing UI/API behavior.
- No automated tests/builds, production/backend data, credentials, external services, commit or push. Preview remains available on loopback at http://127.0.0.1:5172/login.
- Evidence note: evidence/notes/AUTH_TEACHER_UI_PREVIEW_V16_20261111.md; screenshots and observations: evidence/screenshots/auth-teacher-v16/.
## Revision 17 — child-friendly three-role icon preview complete

- Status: WEB_UI_CRAYON_IMPLEMENTATION_REV24_APPROVED_IN_PROGRESS; SECTION_1_AUTH;; ROLE_NAV_SETTINGS_GEAR_V22_COMPLETE_PENDING_USER_REVIEW; FE_REMEDIATION_COMPLETE
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation; codex/fe-ui-web-remediation.
- Approved plan: Rev17, SHA-256 49D2B35334A952201387661B50C57DA971453F6C3A8F7518E4E86D48A90AC0E4.
- Updated shared SVG icons used across the Teacher, School Manager, and Platform Admin UIs and shared login pages. Rounded strokes and restrained semantic crayon accents preserve existing meanings and foreground contrast.
- EV-020 records 15 captures: desktop/narrow light mode plus dark desktop (all three login pages and representative dashboards). No horizontal overflow, Vite error overlay, or observed runtime exception. Platform Admin shows the existing backend-unavailable state.
- No packages, tests/builds, backend/API, real data, screen-reader audit, commit, or push. Changes remain pending user review.
- Evidence note: evidence/notes/THREE_ROLE_CHILD_FRIENDLY_ICONS_V17_20261111.md; screenshots: evidence/screenshots/role-icons-v17/.
## Revision 18 — navbar and notification icon preview complete

- Status: WEB_UI_CRAYON_IMPLEMENTATION_REV24_APPROVED_IN_PROGRESS; SECTION_1_AUTH;; ROLE_NAV_SETTINGS_GEAR_V22_COMPLETE_PENDING_USER_REVIEW; FE_REMEDIATION_COMPLETE
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation; codex/fe-ui-web-remediation.
- Approved plan: Rev18, SHA-256 AA075090DFD47E98B62B5287BDDABF9BD199395847CDAA9FB1275C34A789D9FA.
- Applied full-color system emoji glyphs to Teacher, School Manager, and Platform Admin shell navigation/account icons; all three notification/inbox affordances use the same yellow bell. Labels, state semantics and actions remain unchanged.
- EV-021: nine screenshots at desktop/narrow and dark desktop. No horizontal overflow, Vite error overlay or browser runtime exception.
- No added package/assets, API/backend, automated tests/builds, commit, or push. Pending user review.
- Evidence note: evidence/notes/ROLE_NAV_NOTIFICATION_ICONS_V18_20261111.md; screenshots: evidence/screenshots/role-nav-icons-v18/.

## Revision 19 — monochrome navbar and notification icon preview complete

- Status: WEB_UI_CRAYON_IMPLEMENTATION_REV24_APPROVED_IN_PROGRESS; SECTION_1_AUTH;; ROLE_NAV_SETTINGS_GEAR_V22_COMPLETE_PENDING_USER_REVIEW; FE_REMEDIATION_COMPLETE
- Plan/approval: Rev19, direct user authorization; plan SHA-256 FABD3A9230620BE08F7E4B6D04FA178C3EAC372377F760F37C266182BB9F1141.
- Replaced the Rev18 emoji output for shell navigation and notification controls with monochrome single-color SVG line icons. All three roles use the same outline bell; existing state indicators and accessible behavior remain.
- EV-022: nine captures across the three roles at 1440x900 and 390x844, plus dark desktop. Zero horizontal overflow, Vite overlays or browser runtime exceptions. Representative captures were visually inspected.
- No automated tests/builds or screen-reader device audit. No packages/assets/backend/API or credentials used; no commit/push.
- Evidence note: evidence/notes/ROLE_NAV_NOTIFICATION_MONO_ICONS_V19_20261111.md; screenshots: evidence/screenshots/role-nav-icons-v19/.

## Revision 20 — Teacher UI diagnosis complete; awaiting design approval

- Plan/approval: Rev20, SHA-256 0BAAFA4133B6ABDF9C225985C93CE32AF07F62A6E3C83C69B6F251DABC337219; audit-only.
- EV-023 documents the canonical SRS baseline, current Teacher routes/API boundaries, specific role and presentation findings, and the proposed Teacher screen set/layout.
- Current visual audit uses EV-018/EV-019 screenshots; no fresh browser run because sandbox socket access to 127.0.0.1:5172 was denied.
- No application source, tests, builds, backend, packages, or other portal were changed.
- Next step is user review of the proposed Teacher IA and demo flows. Implementation begins only after direct acceptance and a separately matched implementation plan/approval.

## Revision 21 — authorization checkpoint before icon source changes

- Direct user request authorizes replacing semantically mismatched navbar glyphs with a crayon-style, monochrome outline set across the three SRS web roles.
- Plan revision 21 SHA-256: D97702B032B44573A9733F3978A175EF0C9EF45A50AF5D5A88A673192104FFE2. Matching approval is present: True.
- Scope is limited to shared navigation SVG glyphs and the three role-shell icon mappings; all labels, routes, actions, layout and non-shell page icons remain out of scope.
- Source changes have not started at this checkpoint.

## Revision 21 completion checkpoint — 2026-11-11

- Updated semantic outline glyphs and role mappings for the three web navbars; all nine desktop/narrow/dark loopback captures were visually inspected and recorded under EV-024.
- Capture observations: no horizontal overflow, Vite overlay, or browser runtime exceptions. Only icon glyphs/mappings changed within the Rev21 scope; the separate Teacher layout proposal remains pending user review.
- No tests/builds, commit, or push. Existing worktree changes were preserved.

## Revision 22 completion checkpoint — 2026-11-11

- Replaced the sun-like settings spokes with a recognizable toothed cog in the Teacher and School Manager navbar mappings. Preserved non-navigation settings glyph use.
- Captured and visually reviewed role settings screenshots; all nine Rev22 captures have no overflow, Vite overlay, or browser runtime exception. Details in EV-025.
- No tests/builds, commit, or push. Existing worktree changes were preserved.

## Revision 23 kickoff — 2026-11-11

- Verified worktree F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation on codex/fe-ui-web-remediation; existing dirty work was present and will be preserved.
- Verified authority-selected FEAT-063 SRS v2.7-draft Rev57 SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5. Authority says unsigned; §§1–31 are target and §32 is evidence only.
- Recorded Rev23 plan and matching direct-user approval for design preview only. No application source has been changed for Rev23.
## Revision 23 flow-atlas checkpoint — 2026-11-11

- Completed the full web screen/flow map from SRS §§5/19/20/21.5–21.6 for Auth and three product roles. Current FE API surface is recorded separately as implementation evidence; no API runtime was called.
- The generated preview remains next. API-blocked flows, owner-open decisions and media/privacy gates must stay visible. No app source changed.

## Revision 24 implementation status — 2026-11-11

- Plan Rev24 and direct user approval recorded before source changes; plan SHA-256 `072778CC86CCF6C2CDE18CDD034276F75371A4930FF5C18924F58191187BC345`.
- Auth section rebuilt and manually reviewed at 1440×900 and 390×844; role-mismatch isolation verified for Teacher, School Manager and Platform Admin. Evidence: FEAT-066-EV-027.
- Teacher section rebuilt and reviewed at 1440×900 and 390×844 across 12 routes. Keyboard menu focus, Enter, Escape and focus return were verified. Evidence: FEAT-066-EV-028.
- School Manager is complete after route/API boundary review and 22 desktop/narrow captures; logout clears the local role/session keys. Evidence: FEAT-066-EV-029.
- Platform Admin is complete after route/API boundary review and 24 desktop/narrow captures; logout clears the local role/session keys. Evidence: FEAT-066-EV-030.
- All four ordered sections (Auth, Teacher, School Manager, Platform Admin) are complete. Platform Admin role discovery and the API dependencies recorded in EV-030 remain unresolved.
- Rev25 is active: refine only the three overview dashboards to match Rev23 boards more closely; keep shell and detail routes unchanged. No source edits for Rev25 have started at this checkpoint.
- Worktree remains uncommitted/unpushed. No automated tests/builds, authenticated API/backend, production data, credentials, or Parent/mobile were used or changed.


## Revision 25 — Teacher dashboard checkpoint — 2026-11-11

- Teacher overview manually checked at 1440×900 and 390×844; no overflow, Vite overlay, runtime exception, or console error. Enter/Escape drawer behavior and focus return pass. Evidence screenshots and observations are recorded in EV-031 (three-role pass in progress).
- Teacher overview matches the three-area Rev23 hierarchy. Next: simplify School Manager to organization status plus services, then review before Platform Admin.
- Worktree remains uncommitted/unpushed. No tests/builds or backend/API requests were made.


## Revision 25 — School Manager dashboard checkpoint — 2026-11-11

- School Manager overview now follows the two-block Rev23 hierarchy; only assignment-gated API class data can populate the organization state, and unavailable billing/subscription/quota/inbox/feedback remain explicit. Public review is labeled as API-backed but still requires authenticated access.
- Desktop/narrow and mobile drawer keyboard checks passed with no overflow, Vite overlay, runtime or console errors. Evidence is part of FEAT-066-EV-031. Next: Platform Admin overview.
- No product API, automated tests/builds, commit or push.


## Revision 25 — complete pending user review — 2026-11-11

- Teacher is represented by its existing cleaned three-area overview; no additional Teacher source edit was needed in this alignment pass.
- School Manager overview now has two blocks: organization status and services. The class count remains assignment-gated; preview uses no sample rows. Public review is API-backed; billing/payment, subscription/quota, inbox and feedback are explicitly unavailable.
- Platform Admin overview now has four cards: health, queue/jobs, billing reconciliation and lifecycle. Preview does not call health; queue/jobs, billing and lifecycle remain unavailable until APIs exist.
- Six screenshots were captured and visually checked at 1440×900 and 390×844. Recorded metrics: no horizontal overflow, Vite overlay, runtime exception or console error. Enter opens each mobile drawer and focuses the first navigation item; logout is visible while the drawer is open; Escape closes it and restores focus.
- Known out-of-scope finding from the DOM review: School Manager and Platform Admin `NavLink` items sharing one pathname each expose `aria-current="page"` on 10 and 11 items respectively, although only one item is visually active. The visual shell/routes were kept unchanged in this overview-only pass; log as a follow-up accessibility issue.
- Evidence: FEAT-066-EV-031. No tests/builds, authenticated/product API, external service, real user/child data, Parent/mobile, commit or push. Worktree remains uncommitted/unpushed pending user review.


## Revision 26 — approved/in progress — 2026-11-11

- Scope: CSS-only paper/crayon backdrop behind authenticated content canvases for Teacher, School Manager and Platform Admin.
- Plan revision 26 SHA-256: `247E06100BD2506B1872EBA47E71549ACE8DFDC200614320464933A428800B38`; matching direct-user approval recorded in `approvals/TASK_APPROVAL.md` before code.
- Worktree: `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`, branch `codex/fe-ui-web-remediation`.
- UI edits have not started at this checkpoint.

## Revision 26 completion — 2026-11-11

- The shared CSS canvas background and corner layer are in place for all three roles.
- 12 desktop/narrow overview and representative-route captures are visually inspected. No clipping, horizontal overflow, Vite overlay, runtime exception or console error; mobile drawer Enter/Escape focus behavior passed for all roles.
- Evidence: FEAT-066-EV-032 and `evidence/screenshots/paper-crayon-background-rev26/`.
- No tests/builds or product API calls. Work remains uncommitted and unpushed pending user review.

## Revision 27 kickoff — 2026-11-11

- Brainstorm and recommended direction recorded in `evidence/notes/AUTH_UI_REDESIGN_BRAINSTORM_REV27_20261111.md`.
- User approval and plan hash `C9EF609A920F3C53F0153ED109660B85003D4D03A8E1E76C2F46C3EB2EEF21C2` recorded before implementation.
- Source changes have not started at this checkpoint.


## Revision 27 completion — 2026-11-12

- Plan revision 27 and direct-user approval were recorded before implementation. Verified plan SHA-256: `C9EF609A920F3C53F0153ED109660B85003D4D03A8E1E76C2F46C3EB2EEF21C2`.
- Shared auth presentation for Teacher, School Manager and Platform Admin is implemented. Existing URLs, role mappings, auth adapter, preview state, pending/error behavior and role-discovery limitation remain in place.
- Twelve desktop/tablet/narrow captures show no horizontal overflow, Vite overlay, runtime exception, console error, HTTP error, or missing login action. Keyboard focus/portal state and forced WebGL-failure SVG fallback are documented in FEAT-066-EV-033.
- `design-taste-frontend` full gate: `GATE: OPEN 22 (rounds used up)` after round 3. A final manual capture then exposed and fixed a role-specific fallback-opacity issue; all 12 captures and the forced shader-failure observation were rerun afterward. No fourth full gate round was run. The stored open dependency-scanner and marketing-layout findings are enumerated in the completion evidence.
- No automated tests/builds, auth submission, product API call, external request, real user/child data, Parent/mobile change, commit or push. Worktree stays on `codex/fe-ui-web-remediation`; pending user review.

## Revision 28 kickoff — approved / in progress — 2026-11-16

- Plan revision 28 SHA-256: 8A63A0C4C3B80C5628E46AF7733FF4633964A7D73DD820E877833E2F7C59D029; direct user approval is recorded in feature and root approval files before source edits.
- Current task SRS: user-selected unsigned Rev68 file and hash are recorded in Plan 28. The prior Rev57-based plans remain historical.
- Scope: app structure cleanup and full role-based web UI audit/rebuild, preservation of supported API/auth, feature-local evidence, required precommit validation, one local commit, and local preview startup.
- Baseline dirty paths are captured in evidence/notes/WEB_UI_REBUILD_BASELINE_20261116.txt before app source changes.

## Revision 28 — implementation and review complete; local commit closeout — 2026-11-16

- The approved one-app cleanup and three-role web rebuild are complete in `apps/web`; the route/API truth matrix and Rev68-to-current-API review are in EV-034.
- Shared entry/auth, Teacher, School Manager BE1/preview, and Platform Admin surfaces preserve current roles, contracts and privacy boundaries. Missing APIs remain unavailable.
- Nine local screenshots were visually inspected at desktop, tablet and mobile sizes; the mobile dashboard was recaptured in its stable closed-drawer state. Keyboard drawer focus/escape behavior was reviewed.
- `npm ci` and `npm run build` passed. No application tests were run. Security, harness, architecture, and diff-check results are appended to EV-034 after final validation.
- Source mismatch remains open: task-selected unsigned Rev68 vs repository source-register unsigned Rev60. No SRS or authority record was edited.
- The requested single local commit is the final closeout action. No push, PR, merge, or deployment.

### Final validation — 2026-11-16

- Security: `REPOSITORY_SECURITY_VALID`, 7,357 files scanned. The final run passed after normalizing machine-specific paths in Rev23 provenance.
- Architecture: `ARCHITECTURE_VALID`.
- `git diff --check`: passed (exit 0; line-ending warnings only).
- Harness/skeleton: blocked by the intentionally removed `apps/mobile/package.json`; harness additionally reports missing evidence scaffolding in unrelated FEAT-070. The UI task did not recreate these paths.
- Build: `npm run build` passed; application tests were not run.

## Revision 29 kickoff — 2026-11-16

The owner directly approved the shared login landing and removal of local-preview UX. Plan hash and approval are recorded in both task approval registers before source changes. Route/auth behavior will be preserved for real sign-in, and the existing Rev28 local commit will be amended so the branch still contains one final commit.

## Revision 29 complete — 2026-11-16

- The role-entry page now matches the approved reference without the preview panel. Legacy Teacher and preview routes resolve to the shared entry; Teacher and School Manager use their real sign-in flows. The local preview app and fake sign-in bypass are removed. Platform Admin role discovery remains visibly unavailable because the backend API is absent.
- EV-035 records the route/form review, desktop and mobile screenshots, role destinations, no overflow, 3px keyboard focus, empty runtime/console/external-request results, and final build.
- Web build: passed (npm run build). Application tests: not run per the task boundary.
- Security: REPOSITORY_SECURITY_VALID, 6,874 files scanned; no machine paths or credentials found.
- Architecture: ARCHITECTURE_VALID.
- git diff --check: passed (exit 0; Git reported only its existing CRLF-to-LF normalization warnings).
- Harness: HARNESS_INVALID because apps/mobile/package.json is intentionally absent from the prior owner-approved structure cleanup and unrelated FEAT-070 lacks raw/screenshots/metrics/notes evidence folders. Skeleton validation stops with FileNotFoundError for that same removed mobile package. Parent/mobile is outside this revision; these paths were not restored or generated.
- The selected Rev68 task SRS and repository Rev60 authority mismatch remain open; no SRS authority record was edited.
- Amend the existing single local commit after this closeout; leave Vite on 127.0.0.1:5173 for review. No push, PR, merge, or deployment.

## Revision 30 — shared single-screen role login complete — 2026-11-16

- Rev30 plan SHA-256 8D167E39A75B3A13E68FBBB1C4672C018E9282920CC4478D9DFA4B16B1DAD12F; direct user approval recorded in root and feature task approvals before source edits.
- /login now opens the existing split-panel sign-in UI directly. The role-card landing and the duplicate School Manager login presentation are removed. Role tabs change the selected role without leaving /login; legacy sign-in URLs resolve to the correct tab.
- Teacher identity/assignment resolution and School Manager BE1/Firebase login plus school_admin assignment check remain real and separate. Platform Admin still fails closed on missing role/capability discovery. No backend, authorization contract, provider, local session bypass, or mobile code changed.
- EV-036 records the SRS trace, browser route matrix, screenshots, 1440×900/390×844 measurements, keyboard activation/focus retention, and zero runtime/console/external-request errors. No credentials or product API calls were made.
- Web build passed. Web lint exited 0; its remaining warnings are in pre-existing API, shell, Teacher and Manager components, not the revised login component. Application tests were not run under the task boundary.
- Security: REPOSITORY_SECURITY_VALID, 6,879 publishable files scanned. Architecture: ARCHITECTURE_VALID. git diff --check: passed with only existing CRLF normalization warnings.
- Harness remains invalid due the intentionally removed apps/mobile/package.json and missing evidence scaffolding in unrelated FEAT-070. Neither path was restored or generated. Skeleton validation was unnecessary because repository structure was unchanged.
- Vite is running at http://127.0.0.1:5173/login. The existing single local commit was amended after final review; the branch is one commit ahead and nothing was pushed.

## Revision 31 — Teacher-first API/UI plan — 2026-11-16

- Status: PLANNED — AWAITING IMPLEMENTATION APPROVAL.
- Plan: features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_REV31_TEACHER_API_UI_REBUILD_20261116.md; SHA-256 2EB6235B8F8DFB5EB6EC4098FA2892687102DD4D922360E16751F6D21DA0E5E7.
- Requirements: canonical unsigned FEAT-063 v2.7-draft Rev60. API source baseline: origin/dev 1c9148e88600a101887e477541c4c4893ba1c7df. Teacher UI baseline: codex/fe-ui-web-remediation b72f9e46f9c63e019807d7c4a2c309b0aa46a133.
- EV-037 records the static route/guard/UI crosswalk and its limits. It confirms existing assignment/class/roster/lesson/upload routes, one backend-only lesson-version route, development-gated Teacher AI routes, and the missing occurrence/sample/job/playback/quota/supporting contracts.
- No code, backend, contract, visual asset or approval register changed. No runtime API call, test/build, commit or push was performed for Rev31.
- Next gate: owner approves a specific implementation scope and updates approvals/TASK_APPROVAL.md; resolve or preserve SRS owner-open decisions and the OI-17 visual review gate before affected implementation.
## Revision 32 — Platform Admin available API wiring — 2026-11-16

- Status: IMPLEMENTED; runtime response not verified in this task.
- Approved plan: features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_REV32_PLATFORM_ADMIN_AVAILABLE_API_INTEGRATION_20261116.md; SHA-256 56A6985B7D486E79F1B8C9AB39B4C56275BC401C7ECF4730014D01BC167A1A92. Approval: root approvals/TASK_APPROVAL.md, FEAT-066 Rev32.
- Changed apps/web/src/modules/platform-admin/pages/AdminScreens.tsx: health probe now calls the configured API base instead of requiring loopback; blocked/loading/response/error/retry copy is explicit and does not claim subsystem health.
- Preserved existing GET /api/auth/v1/me and Platform Admin account GET/POST/PATCH integrations. No account mutation behavior changed. Moderation remains unavailable pending queue/detail reads and Content Admin permission enforcement.
- Validation: git diff --check passed; direct trailing-whitespace scan clean. No live API request, test/build, commit or push.
- Evidence: features/FEAT-066-fe-ui-srs-full-review/evidence/notes/EV-038_PLATFORM_ADMIN_CONFIGURED_HEALTH_API_REV32_20261116.md. SRS remains unsigned Rev60; Q-13 and OI-17 remain open.
## Revision 33 — Docker API verification and FE handoff — 2026-11-17

- Status: LOCAL HANDOFF ACTIVE; backend/API scope partial due unavailable MinIO registry image.
- Plan: features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_REV33_DOCKER_API_FE_SMOKE_20261117.md; SHA-256 0AB2F79A26EDCBA27871C559016A8A6A56466DA82867519E2FB147995C8380F0. Approval: approvals/TASK_APPROVAL.md, FEAT-066 Rev33.
- Docker Desktop running. PostgreSQL is healthy on 5432. API container `sketch2life-api-1` is healthy on 127.0.0.1:8000 using a local image equivalent to backend/Dockerfile except the absent optional renderer static bundle.
- `GET /health`: 200. Unauthenticated `GET /api/auth/v1/me` and `GET /api/platform-admin/v1/accounts`: 401; no credentials or account data. Successful authenticated account operations remain unverified.
- Quay MinIO pull failed with 401; MinIO, ClamAV and Redis are not running. API routes that need those services are not ready. The standard OpenAPI projection omits auth/account route paths.
- Direct CORS is absent. Existing FE on 127.0.0.1:5173 is preserved. Proxy FE on 127.0.0.1:5174/login returns 200; proxied health returns 200 and protected routes return 401. Use 5174 for same-origin testing.
- No app tests or frontend production build. Docker image build and ignored temporary Vite config were used to make the local handoff. No tracked application code/config change, commit or push in Rev33.
- Evidence: features/FEAT-066-fe-ui-srs-full-review/evidence/notes/EV-039_DOCKER_API_FE_HANDOFF_20261117.md.
## Revision 34 — Platform Admin test account — 2026-11-17

- Status: COMPLETE; account ready for owner FE testing.
- Plan: features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_REV34_PLATFORM_ADMIN_TEST_ACCOUNT_20261117.md; SHA-256 3EBDE69AFFA105F09DFB04901DA5539EE555361EBCBC3F8D035831A5291A9EBE. Approval: approvals/TASK_APPROVAL.md, FEAT-066 Rev34.
- Project: verified Firebase `sketch2life-dev`; local Docker PostgreSQL only. Applied `be1_core@head` and `lesson_library@head` to the previously empty schema; no volume reset or unrelated branch migration.
- One Platform Admin identity provisioned through the documented bootstrap. Firebase sign-in: 200. Auth role endpoint: `platform_admin`. Account list: 200, total 1. No email delivery; test email is reserved `example.com` and unverified.
- FE test URL: http://127.0.0.1:5174/login, with dev Firebase config and same-origin API proxy. Existing port 5173 is preserved.
- Credential and ID token are absent from evidence/repo files and are returned directly to the owner. No Content Admin capability, child-media access, production action, app test suite, code edit, commit or push.
- Evidence: features/FEAT-066-fe-ui-srs-full-review/evidence/notes/EV-040_PLATFORM_ADMIN_TEST_ACCOUNT_20261117.md.
## Revision 35 — Active FE port API proxy — 2026-11-17

- Status: COMPLETE; active FE port now proxies to Docker API.
- Plan: features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_REV35_ACTIVE_FE_PORT_API_PROXY_20261117.md; SHA-256 479A937FDDDD09AD6CC681B5D951C7D434B9ACAD29B3ECBB4918EC3225B9E200. Approval: approvals/TASK_APPROVAL.md, FEAT-066 Rev35.
- Port 5173 uses a Git-ignored temporary Vite config with same-origin `/health` and `/api` proxies to 127.0.0.1:8000; dev Firebase config is process-only. Port 5174 remains available.
- Verification: admin login route 200, proxied health 200, unauthenticated `/api/auth/v1/me` 401, expected dev project and API base injected.
- No credential submitted, no app test suite, tracked source, account or backend change, commit or push.
- Evidence: features/FEAT-066-fe-ui-srs-full-review/evidence/notes/EV-041_ACTIVE_FE_PORT_API_PROXY_20261117.md.

## Revision 36 — Platform Accounts crayon UX rebuild — COMPLETE
- Plan: PLAN_REV36_PLATFORM_ADMIN_ACCOUNTS_CRAYON_REBUILD_20261117.md, SHA-256 6AE92FAEB7ED005B463E05176A58539A6927323E9C61ED3350F9CA243446E0D9; approval recorded before app edits.
- Task SRS: owner attachment dated 2026-11-13, amendments through Rev69, SHA-256 B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5. Repository Rev60 authority unchanged.
- Four desktop/tablet/mobile captures: no horizontal overflow or runtime exceptions; expected missing-Firebase-session state, no fabricated empty result. Authenticated account operations were not runtime-verified.
- Build, focused UsersPage oxlint and git diff --check pass. No app tests, commit or push.
- Open gaps: offset pagination vs SRS cursor, missing capability grant/read API and no visible audit-event viewer on this page.
- Evidence: evidence/notes/EV-042_PLATFORM_ACCOUNTS_CRAYON_UX_REV36_20261117.md and evidence/screenshots/rev36-platform-accounts/.


## Revision 37 — Platform Admin sidebar crayon redesign — COMPLETE

- Plan: PLAN_REV37_PLATFORM_ADMIN_SIDEBAR_CRAYON_REDESIGN_20261117.md; SHA-256 A3F276D0EB8D163F35B107A9CC154D448437A4F5F6BFAF65EE49F82DB399940C. Owner approval is in approvals/TASK_APPROVAL.md.
- Source: only apps/web/src/modules/platform-admin/styles/admin-rebuild.css changed for Rev37. Shared shell behavior, routes, APIs, auth/session actions, and other role sidebars are unchanged.
- Browser review: desktop 1440×900, open drawer at 768×1024 and 390×844. No horizontal overflow/runtime exceptions; mobile nav scrolls independently and footer remains anchored.
- Validation: production build passed; focused shared-shell oxlint exited 0 with existing warnings; git diff --check passed.
- Evidence: evidence/notes/EV-044_PLATFORM_ADMIN_SIDEBAR_CRAYON_REV37_20261117.md and evidence/screenshots/rev37-platform-sidebar/.
- No application tests, credentials, protected mutations, commit, or push.

## Revision 38 — Platform Accounts zoom-width layout — IMPLEMENTED

- Plan: PLAN_REV38_PLATFORM_ACCOUNTS_ZOOM_WIDTH_20261117.md; SHA-256 DD3BC84855986B15C8FAA4356A4231B93E4096D4F6A0FC3C4316FD73C79ABC79. Approval recorded in approvals/TASK_APPROVAL.md before app-source changes.
- Source: Platform Accounts CSS now fixes the five-column layout/action column through 1120px and switches to labelled cards through 900px. The desktop action-column heading is visible. API/auth/permissions/data behavior is unchanged.
- Browser: no horizontal overflow or runtime exceptions at 1440×900, 1120×800, 1024×768, 987×600, 900×600, 820×900, 768×1024 and 390×844 in an isolated no-auth page state.
- Verification limitation: the isolated browser had no Firebase session, so the populated row and its action buttons were not rendered or captured after the fix. No fake account fixture/token was used. The owner’s active local tab can hot-reload the source.
- Validation: production build, focused UsersPage oxlint and git diff --check passed.
- Evidence: evidence/notes/EV-046_PLATFORM_ACCOUNTS_ZOOM_WIDTH_REV38_20261117.md and evidence/screenshots/rev38-accounts-zoom/.
- No app test suite, credential, account mutation, commit, or push.
## Revision 39 — School Manager API/UI crosswalk — 2026-11-17

- Status: DRAFT — planning only; awaiting explicit implementation approval.
- Plan: `plan/PLAN_REV39_SCHOOL_MANAGER_API_UI_CROSSWALK_20261117.md`; SHA-256 `589D260604CE8DECBC54F8A88AE0F6749D3446CBA0155738B3FF3C3528E9C05F`.
- API baseline: `origin/dev` `1c9148e88600a101887e477541c4c4893ba1c7df`; web worktree baseline `b72f9e46`.
- Admin closeout: account GET/POST/PATCH and shared GET /health are wired. The moderation PATCH has no platform queue/exact-version reads and does not enforce SRS Content Admin permission; it remains blocked.
- Manager: public-grant review and class list/create are already wired. Teacher assignment, profile/consent and Parent groups have backend routes without corresponding Manager UI wiring; exact-version review, teacher candidate read, quota/billing and organization feedback remain gaps as detailed in EV-047.
- Evidence: `evidence/notes/EV-047_SCHOOL_MANAGER_API_UI_CROSSWALK_REV39_20261117.md`.
- No application source, approval record, test, build, runtime API call, commit, or push changed in Rev39. Do not implement until the owner approves a concrete scope.

## Revision 40 — School Manager API integration plan — 2026-11-17

- Status: DRAFT — planning only; awaiting owner approval before implementation.
- Plan: `plan/PLAN_REV40_SCHOOL_MANAGER_API_INTEGRATION_20261117.md`; SHA-256 `84E8779D7F169BEE9E5ECA8D02EABB571D23F66E11B167F782A04D04F261F070`.
- Count: 17 Manager business routes (6 already wired, 10 proposed for integration, 1 class-assignment command blocked by missing scoped Teacher candidate read) plus shared `GET /api/auth/v1/me` = 18 BE routes relevant to Manager. Firebase SDK sign-in is not a BE route.
- SRS scope: FEAT-063 v2.7-draft Rev60, unsigned. Preserve tenant scope, child-media deny-by-default, exact lesson-version gate and open quota-purchase policy Q193.
- Evidence: `evidence/notes/EV-048_SCHOOL_MANAGER_API_INTEGRATION_PLAN_REV40_20261117.md`.
- No app source, `approvals/TASK_APPROVAL.md`, tests, build, live API call, commit or push changed. Implementation remains unapproved.

## Revision 41 — Manager login/auth API verification — 2026-11-17

- Status: VERIFIED WITH LIVE AUTH LIMITATION; the existing login API chain is wired and a confirmed BE1 runtime configuration defect was fixed.
- Plan: `plan/PLAN_REV41_MANAGER_LOGIN_AUTH_API_20261117.md`; SHA-256 `E06D84FCEE12A168765876C892B3D9DD170D64FB81F804D0E551CD5F9EBE672B`. Approval recorded in `approvals/TASK_APPROVAL.md` before implementation.
- Fix: shared runtime config now falls back to `.env.example`'s `VITE_BE1_BASE_URL` and `VITE_BE1_ORGANIZATION_ID` after injected and generic config.
- Tests: 2 focused files passed, 8 tests passed. `npm run build` passed. `npm run lint` exited 0 with existing warnings and no errors.
- Runtime: local Docker API/PostgreSQL healthy; GET `/health` 200; unauthenticated GET `/api/auth/v1/me` 401 `AUTHENTICATION_REQUIRED`; unauthenticated BE1 assignment read 401. FE dev server port 5173 refused connection.
- Limitation: no Manager test credential or active FE dev server was available, so successful Firebase sign-in against the live backend remains unverified. Positive FE role/assignment flow and BE1 config fallback passed focused tests. No account or role mutation.
- Source: one production FE runtime-config fix and focused test changes; backend contract unchanged. Containers remain running locally. No commit or push.
- Evidence: `evidence/notes/EV-049_MANAGER_LOGIN_API_VERIFICATION_20261117.md`.

## Revision 42 — Manager QA account and live login — 2026-11-17

- Status: APPROVED_FOR_EXECUTION; waiting for local Firebase Web config before account creation.
- Plan: `plan/PLAN_REV42_MANAGER_QA_ACCOUNT_AND_LIVE_LOGIN_20261117.md`; SHA-256 `96AE1FC25F8BAE840371D9CB41D5F52652F74C1F59C0F6D2A6AD22F5848C9D6D`.
- Read-only preflight: Docker API/PostgreSQL healthy; Firebase Admin configured for `sketch2life-dev`; DB has 1 Platform Admin, 0 Managers, 0 organizations and 0 assignments. No row identities were read.
- Gate: no Firebase Web config exists in the worktree and port 5173 refuses connection. No account/organization/password/token was created. Wait for config in ignored `apps/web/.env.local` or its existing local path.
- Rev43 business API integration is APPROVED_CONDITIONALLY and starts only after Rev42's live Manager login and both authenticated authorization reads pass. Static route audit allows five operations and blocks five Rev40 operations due to guard/contract gaps; the existing class-create API also lacks SRS capacity enforcement.
- Evidence: `evidence/notes/EV-050_MANAGER_QA_ACCOUNT_READINESS_20261117.md`.

## Revision 44 — Manager QA bootstrap ordering repair — 2026-11-17

Plan Rev44 and its approval record the direct task authorization. The supported first-school-admin helper failed on the organization-assignment organization foreign key after Firebase sign-in. Its transaction rolled back; Firebase test identities were removed. Read-only counts are one existing identity, zero organizations, and zero assignments. The narrowly scoped repair will flush the organization and adult identity before adding the assignment, add a focused ordering test, then retry the local login flow. No user account is retained yet.

## Revision 45 — Manager QA login and business API integration — 2026-11-17

- Rev44 parent-row flush repair is implemented; the bootstrap ordering unit test passed.
- Rev42 gate is fulfilled: Firebase password sign-in succeeded; authenticated account role is school_manager; the dedicated organization returns an organization-wide school_admin assignment.
- Rev43 connected organization read, minimal class roster read, consent-status read, and Parent-group list/create with idempotency. Teacher assignment, Parent invitation/membership revoke, consent writes, class assignment, capacity/billing/quota/feedback remain unavailable under the approved route review.
- Live organization, classes, and Parent-group reads returned 200; classes and groups are empty. Profile/consent reads require a class and were not sent. No business write was sent. Class creation remains unavailable until BE enforces SRS FR-T-03 capacity.
- The FE dev server is running at 127.0.0.1:5173 with the ignored Firebase config and QA organization injected into process environment. Login and Manager SPA/API proxy routes returned 200. Browser-based SDK sign-in could not be automated in this environment; EV-051 records this limit.
- Focused FE tests: 18 passed. Backend bootstrap test: 1 passed. TypeScript/Vite build passed. Targeted Oxlint exited 0 with existing WebAppShell warnings. No commit or push.
- Evidence: evidence/notes/EV-051_MANAGER_LOGIN_AND_BUSINESS_API_INTEGRATION_20261117.md.

## Revision 46 — School Manager navigation and theme restoration — IMPLEMENTED; visual review pending

- Plan Rev46 is approved and implementation is recorded in EV-052.
- Fixed the Manager CSS portal-key mismatch, reorganized the SRS navigation areas, and marked unsupported API areas as waiting.
- Production build passed; targeted lint exited 0 with four existing shared-shell warnings; git diff --check passed. No app tests were run.
- Port 5173 serves the FE. Authenticated visual inspection remains for owner review because the local browser CDP endpoint was unavailable.
- No credentials, child data, commit or push.

## Revision 47 — shared folder cleanup — IMPLEMENTED; BUILD PASSED

- Plan: plan/PLAN_REV47_SHARED_FOLDER_CLEANUP_20261117.md; current SHA-256 `82AB4F0E97144E8070E228B0ACDA59CB33102CCFF13C5F7927A0746FFF590E22`.
- Approval: recorded in approvals/TASK_APPROVAL.md before source moves.
- Moved 17 files into api/auth/components/navigation/styles; preserved assets; updated 50 references in 27 source files.
- No old shared-root paths remain. Four-group Manager navigation preserved.
- Production build passed; git diff --check exit 0 with CRLF normalization warnings. No app tests, commit, or push.
- Evidence: evidence/notes/EV-053_SHARED_FOLDER_ORGANIZATION_REV47_20261117.md.

## Revision 48 — Manager 17 API test record — 2026-11-17

- Plan Rev48 and owner approval are recorded.
- Route composition: 17/17 mounted. Public OpenAPI projection: 11/17, omitting Lesson Library rows 4, 6, 13–16.
- Focused FE tests: 18 passed; isolated BE contract/unit tests: 90 passed.
- Build, lint command, harness, architecture, security, and diff checks completed; lint exits 0 with 28 React warnings.
- No live business mutation. PostgreSQL acceptance tests skipped because no disposable BE1_TEST_DATABASE_URL is configured.
- 11 routes remain wired/adapter-backed; six remain blocked pending contract/policy. See EV-054 for per-route status and limits.

## Revision 49 — Admin and Manager QA credentials — 2026-11-17

- Existing QA Admin and Manager passwords were reset in sketch2life-dev; no duplicate accounts were created.
- Firebase sign-in and GET /api/auth/v1/me passed for both roles.
- Admin accounts GET returned 200; Manager assignment GET returned 200 with organization-wide school_admin.
- Both FE role login pages at port 5173 returned 200.
- Credentials are stored only in Git-ignored tmp/qa-test-accounts.local.md. No source changes, commit, or push.
- Browser form interaction remains for the owner; see EV-055.

## Revision 50 — Manager Classes screen review — 2026-11-17

- Authenticated classes GET returned 200 with zero items; the screenshot matches the QA organization state.
- Class creation remains disabled pending BE1 capacity enforcement required by FR-T-03.
- Review found duplicate error/empty feedback on failures, misleading empty copy, and an out-of-context detail note.
- No source edit, test suite/build, commit, or push. See EV-056.

## Revision 51 — consolidated web handoff — 2026-11-17

- One-commit handoff approved for all current non-ignored worktree changes.
- FE: 18 focused tests passed; production build passed; lint exit 0 with 28 warnings.
- BE selected contract/unit suite: 90 passed.
- Security, harness, architecture and diff checks passed after removing the approval EOF blank line.
- .env and QA credentials under ignored tmp are excluded. No history rewrite; prior Rev48 commit remains.
- EV-057 records the commit scope and verification.

## MGR-1 owner disposition checkpoint — 2026-11-17

- MGR-0 source/evidence inventory is complete; it does not claim fresh runtime verification.
- Owner choices are recorded in D-066-62: Manager Parent discovery/invitation stays unavailable pending separate approval; staff cannot create or revoke effective Parent consent; eligible assignment candidates are verified Teachers in the same organization.
- The School Manager API gap-closure plan remains DRAFT / NOT APPROVED / NOT LAUNCHED. MGR-2 Billing-capacity contract design is next; no implementation is authorized before MGR-7 and a separate Task Approval.
- Owner-selected external SRS review input: 701,157 bytes / `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5` (header Rev69; revision table through Rev68). Repo SRS authority remains Rev60.
- No source, approval, SRS, or FE worktree changes; no tests, builds, validators, backend/runtime, database, Docker, provider, network, or Modal commands were run.

## MGR-2 contract planning review — 2026-11-17

- MGR-2 contract Draft 1 received an independent cold review: **ACCEPT WITH NOTES**, zero actionable findings. The reviewer did not verify generated OpenAPI, runtime behavior, or Billing integration.
- D-066-63 records the selected planning direction: Billing owns effective class capacity; BE1 must use a versioned, concurrency-safe admission decision and fail closed when capacity cannot be verified. SRS-defined idempotency, `GRACE`/`RESTRICTED`, effective-time suspension projection, and scope/error behavior are retained.
- Billing-unavailable status/code/retry mapping, literal idempotency header/format/retention, reservation/receipt protocol, and SRS-to-BE route-prefix mapping remain OPEN.
- MGR-2 remains **DRAFT / NOT APPROVED / NOT LAUNCHED**. No source, OpenAPI, schema, migration, FE, or official task approval was changed. MGR-7 and its separate Task Approval remain required before implementation.
- Next roadmap work: MGR-3 tenant-scoped Teacher-candidate and assignment contract planning. Respect listed parallel work and any owner/contract dependency; no implementation is authorized here.
- Evidence: `evidence/notes/MGR_2_COLD_REVIEW_OWNER_DISPOSITION_20261117.md`. No tests, builds, validators, runtime, database, Docker, network/provider, or Modal commands were run. Nothing was staged, committed, or pushed.

## MGR-2 Rev60 citation correction and cold review R3 — 2026-11-17

- Corrected the MGR-2 plan/evidence traceability: Rev60 §9.6 line 791 is the general idempotency-key requirement; §§21.1/21.4 specify key scope/replay behavior; §9.8 line 835 maps mismatched payload reuse to HTTP 400 `INVALID_IDEMPOTENCY_KEY`. The proposed route-group list at §9.6 lines 766–775 is not conflated with the detailed protocol.
- Independent read-only cold review of the exact updated plan (24,013 B / `8D9780892575675DAC9FB7436D8A587FDDC61C0A9F2E5C27153969CAD1E1C055`) and evidence (15,158 B / `762C89B81869D820DE9A04A1911724FA7CADA29BC1BEC833A3988447F8CAA6CA`) returned **ACCEPT; 0 P0/P1/P2/P3 actionable findings**. See `evidence/notes/MGR_2_COLD_REVIEW_DRAFT1_R3_20261117.md`.
- MGR-2 remains **DRAFT / NOT APPROVED / NOT LAUNCHED**. Open Billing protocol and wire details remain unresolved; MGR-7 allowlist and separate official Task Approval are still required before implementation. Runtime, generated OpenAPI, tests, database, and Billing integration were not verified.
- No source, SRS, decision, or approval record changed. No tests, validators, runtime, database, Docker, network/provider, Modal, staging, commit, or push were performed.

## MGR-7 bounded BE approval checkpoint — 2026-11-18

- MGR-7 package pin `37B412F3E10403238FDC9B940C437941293AD91F78EFDB76E61F5DE4C97E3FC3` received a conditional owner approval after its R2 cold review returned **ACCEPT**, no findings.
- The feature-local Task Approval records the exact six-file allowlist and scope. Source edits are approved within that boundary; test execution and all verification/runtime commands remain unauthorized pending a separate launch instruction.
- Implementation has not started; no API is newly ready for FE integration. MGR-9 remains a separate FE plan/approval after BE implementation evidence. MGR-2–MGR-6 gaps remain outside MGR-7.

### 2026-11-18 — MGR-8 verification status

Status: NOT VERIFIED. The first pytest command was invoked once and interrupted after remaining pending without captured output; no result or exit code was captured. The second command was not run, and no retry was made. See the implementation verification evidence note.

### 2026-11-18 — MGR-8 diagnostic status

D1: 8 passed. D2: interrupted at the no-growth limit with no final pytest summary. D3: not run by the stop rule. MGR-8 verification disposition remains for the owner. See the diagnostic evidence note.

### 2026-11-18 — MGR-8 owner-run results status

Status: NOT VERIFIED, pending owner disposition.

- D1 (unit, Codex diagnostic): 8 passed.
- D2 (catalog, owner-run): 2 passed, 1 failed. A pre-existing `dev` `app.py` description gate stops the test before the MGR-7 catalog assertions run. Not re-run; the next step is undecided.
- D3 (integration, owner-run): 6 failed with 403 because the fixture had no `account_role`.
- Owner-approved scoped fixture amendment, recorded in Task Approval.
- D3-R2 (owner-run): 6 passed, 1 failed. The MGR-7 default-25 and `INVALID_IDEMPOTENCY_KEY` tests passed. The teacher PDF upload test failed with 503 because ClamAV was not reachable; MGR-7 did not change that test.
- No commit or push. See `evidence/notes/MGR_8_OWNER_RUN_RESULTS_20261118.md`.

### 2026-11-18 — MGR-8 owner disposition status

Status: **PARTIAL — runtime behaviour verified, catalog pending.** This is the owner's instruction, relayed by the coordinating BE session.

- Runtime: D1 8 passed; D3-R2 6 of 7 passed, covering both MGR-7 behaviours.
- Accepted environment limit: the PDF upload test failed with 503 because ClamAV was not running.
- Catalog (`openapi_contract.py`): not verified.
- D2 direction: wait for M2 on `dev` (O-0); no `app.py` port.
- Next: M2 reaches `dev`, S-LL moves onto it, the owner re-runs D2 and D3, an independent review runs, then one S-LL commit, each only on the owner's word.
- No commit or push.

## 2026-11-18 — MGR-8 VERIFIED (S-LL ready for its commit)

- **Status:** **VERIFIED**, by the owner ("R ok verified làm bước 5 đi").
- **Where:** the owner-run happened in the root checkout, on the M2 branch after merge `b93d7334`. The S-LL changes are applied there, uncommitted.
- **Results:**
  - D1: 8/8 passed.
  - D2: 5/5 passed (the catalog part is now verified).
  - D3: 6/7 passed. The PDF test failed on ClamAV, which is an environment limit.
  - `test_app_composition`: 7/7 passed.
- **Evidence:** `evidence/notes/MGR_8_ROOT_RUN_RESULTS_20261118.md` (`19A6E63C106EFF95…`).
- **Next:** an independent evidence review (Sonnet 5.5 high), then the S-LL commit on the owner's word. After that, push and one PR into `dev`, also on the owner's word.
- **Not yet done:** no commit for S-LL, and no push.

## 2026-11-18 — G0 closed: MGR-8 evidence review PASS WITH NOTES

- **Review:** an independent review on Sonnet 5.5 at high effort found **PASS WITH NOTES** (P1 0, P2 0, P3 4).
  - E-01 to E-03 are corrected in the review record, not by editing the pinned note.
  - E-04 is handled by staging explicit paths.
- **Record:** `evidence/notes/MGR_8_EVIDENCE_INDEPENDENT_REVIEW_20261118.md` (6,705 B, `8AE285D1B68DFFB2…`).
- **Commit:** the owner word "Làm G0 luôn" covers the record, one S-LL task commit and a push to the M2 branch, which updates PR #30 into `dev`.
- **Next:** Phase B, starting with CONV-1.

## 2026-11-18 — CONV-1 implemented and verified (local branch, not pushed)

- **Status:** **VERIFIED** with recorded limits. The code is in the local branch `feature/feat066-conv1`, which is never pushed (CV-B). Evidence: `evidence/notes/CONV_1_IMPLEMENTATION_EVIDENCE_20261118.md`. Independent review: `evidence/notes/CONV_1_IMPLEMENTATION_REVIEW_20261118.md`, CHANGES REQUIRED (small), with the P2 fixed.
- **Owner runs, against the disposable `be1_acceptance` database with no ClamAV:**
  - contract and unit: 163 passed;
  - DB integration: 130 passed;
  - the last fixed test: 2/2.

  Every remaining failure is pre-existing or comes from the environment (see the evidence).
- **Not run:** tests that need `sketch2life_m2_s1a`, which is a forbidden database.
- **Follow-ups (package §6, AC9):**

  | Owner | Follow-up |
  |---|---|
  | Web FE | The callers in `backendApi.tsx`, `be1Client.ts`, `authService.ts`, `userService.ts`, `UsersPage.tsx`, `aiWorkflowService.ts` and `TeacherAiLessonWorkflowPage.tsx` must read the new envelope and codes. FEBASE and the role FE slices build on CONV-1 |
  | Mobile | Read-only check of the `/api/auth/v1` and `/api/lesson-library/v1` calls in `apps/mobile` and `apps/ui-mobile` |
  | C-P | `/api/parent/v1/ai` envelope, together with the mobile parser |
  | C-T | Upload and file code and status alignment; the Lesson Library and Teacher AI domain 422 codes; Teacher AI request-ID logging and OpenAPI errors; `assistance_requests.py` envelope; ClamAV |
  | C-M and C-T | BE1 domain 422 codes; `CLASS_SCOPE_MISMATCH` and route-specific scope checks; BE1 `IDEMPOTENCY_KEY_REUSED` aligned to `INVALID_IDEMPOTENCY_KEY` |
  | C-A | Platform Admin domain 422 codes; Platform Admin and auth OpenAPI errors; account `Idempotency-Key`; `ACCOUNT_SETUP_UNAVAILABLE` status; account cursor paging |
  | Lesson Library | `STALE_REVISION` current ETag |
  | BRU-0 | Bruno status and code assertions for the in-scope families |

- **Pre-existing defects found, not fixed** (outside CONV-1):
  - the auth test spy returns `None`;
  - the mapping test cannot parse `openapi_contract.py`;
  - the BE1 OpenAPI path count is 54 where the test expects 55;
  - `CANVAS_PROFILE_MISMATCH` in the room-code test;
  - the pending-consent test still expects a School Manager to create a profile.

## FEAT-063 FR-C-08 SRS wording edit applied (D-219) — 2026-11-19

The canonical working SRS `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` now holds 701,810 bytes / SHA-256 `443A3CA37272D2FE96127564BAF400461F394E098724A6BD999D723A4E504021` (before: 701,157 bytes / `B9B1F42D…`, the copy adopted by D-209). The documentation-only FR-C-08 wording edit (program task B4, `features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_SRS_WORDING_EDIT_DRAFT3_20261119.md`) changed 13 lines with 14 edits: user delete is for runs in COMPLETED, FAILED or ABANDONED; FAILED and ABANDONED are never purged automatically; the retention sites name FAILED; and line 394 records SCRIPT_GENERATING and SCRIPT_GENERATION_UNKNOWN as noted extension values. The header and lines 1-39 were not changed and no line moved, so SRS line citations stay valid. Records pinned to `B9B1F42D…` stay as historical records of the earlier bytes. Contract alignment: `features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_PARENT_TEACHER_LIFECYCLE_CONTRACT_DRAFT12_20261119.md`. Authority: FEAT-063 D-219. Local commit on its own branch; not pushed or merged.
## 2026-11-19 - Backend restart preflight (FEAT-066 Rev33)

- The owner asked to run the backend again for FE testing under the already approved Rev33 runtime scope.
- Docker is installed, but both configured named pipes deny access; WSL reports `E_ACCESSDENIED`. No Compose service started and no volume was touched.
- The host API fallback exits on missing `av==18.1.0`; no online dependency install was attempted. PostgreSQL port 5432 is closed.
- The backend is not running from this session. No HTTP probes, tests, builds, credentials, or data operations were used. See `evidence/notes/EV-058_DOCKER_API_RESTART_PREFLIGHT_20261119.md`.


## Goal v4 Phase A web wiring - Teacher (2026-11-23)

- Status: IN_PROGRESS; task-specific approval is recorded in `approvals/TASK_APPROVAL.md`.
- Active plan: `plan/PLAN_V4A_FE_WEB_WIRING_20261123.md` revision 52; SHA-256 `EEE3C31BF21B3BB4E8C991FCF5AF991AE7A06F18AE38D8673B34D436BAC5B43E`.
- Scope: Teacher web contract wiring and named tests under `apps/web`, plus this feature\'s governance and evidence records.
- Implementation choice: wait hint; no context-confirmation resend.
- Gates and evidence are pending. No commit or push is authorized.

## Goal v4 Phase A Teacher web wiring (2026-11-23)

- **Status:** IMPLEMENTATION_COMPLETE_PENDING_OWNER_REVIEW.
- **Plan:** revision 52; approval recorded; decision D-066-80 (web) selected the wait hint with no context-confirmation resend.
- **Checks:** `npm --prefix apps/web run check` passed (67 files, 684 tests); security and architecture validators passed; `git diff --check` passed.
- **Open repository gate:** `validate_harness.py` fails on missing `apps/mobile/package.json` and FEAT-072 paths outside this task.
- **Evidence:** `evidence/notes/EV-066-059_V4A_WEB_WIRING_20261123.md`.
- **Delivery:** no stage, commit, or push; working tree left for owner review.

## Goal v4 Phase A Parent Android wiring — 2026-11-23

- Status: IN_PROGRESS under the task-specific approval appended to approvals/TASK_APPROVAL.md.
- Scope: apps/ui-mobile plus this task's required FEAT-066 plan and evidence records; no backend or obsolete apps/mobile.

## Goal v4 Phase A Parent Android wiring completion - 2026-11-23

- Status: IMPLEMENTED AND VERIFIED; all six requested gates exited 0.
- App tests: 18 files passed, 228 tests passed, and UI_COPY_AND_RECOVERY_VALID printed.
- Evidence: evidence/notes/PHASE_A_PARENT_ANDROID_WIRING_EVIDENCE_20261123.md.
- Limitations: no lint script or native Android test suite exists in apps/ui-mobile; optional Gradle assembly was not run.
- Working tree: changes remain unstaged and uncommitted for owner review. No push was made.

## Goal v4 Phase B T-7e Teacher roster paging — 2026-11-24

- Status: IN_PROGRESS; app implementation is complete and final evidence/gate review is underway.
- Active plan: revision 53, plan/PLAN_V4B_FE_WEB_T-7E_20261124.md, SHA-256 6D0CB1511BB9468AEC030D338AEE1873D72D08F5810B0602239C4F90679DB14C.
- Scope: Teacher roster API, reusable cursor pager, T05 class detail screen and the two named test files, plus FEAT-066 records. No School Manager or backend changes.
- Implemented: limit-100 paging, unchanged cursor pass-through, child-ID dedupe, first-page active count, partial results on later-page failure, count-aware empty copy, generic legacy-409 error path, and corrected synthetic-profile success copy.
- Consent detail read stays independent; its failure notice does not hide the API-filtered roster.
- Initial gates: web check passed (67 files, 696 tests); security and architecture validators passed; diff check passed with a CRLF normalization warning. Harness validation reports missing apps/mobile/package.json.
- Evidence: evidence/notes/EV-066-060_V4B_WEB_T7E_20261124.md.
- No stage, commit, push, stash, or branch switch. Keep the working tree for owner review.

## Goal v4 Phase B T-7e implementation result — 2026-11-24

- Status: IMPLEMENTATION_COMPLETE_PENDING_OWNER_REVIEW.
- Final web check: build and lint completed; Vitest passed 67 files and 696 tests. Lint exited 0 with warnings.
- Final validators: harness exited 1 only for the missing apps/mobile/package.json path; repository security and architecture validators exited 0.
- Final diff check exited 0 with Git line-ending normalization warnings for the new FEAT-066 records.
- Evidence: evidence/notes/EV-066-060_V4B_WEB_T7E_20261124.md.
- No commit, push, stage, stash, or branch switch. Changes remain unstaged for owner review.

## Goal v4 Phase B T-12b/T-12c Teacher profile revisions and support needs - 2026-11-24

- Status: IMPLEMENTATION_COMPLETE_PENDING_OWNER_REVIEW; requested app tests pass and final repository gates are being recorded.
- Plan: revision 54, plan/PLAN_V4B_FE_WEB_T-12BC_20261124.md; task approval recorded before apps/web edits.
- Scope: Teacher API, revision/edit and support-needs panels, T05 row integration, safe error copy, and mocked tests under apps/web/src; FEAT-066 governance and evidence only.
- Paging choice: load history on demand at limit 100; fetch the next cursor after the user selects Tải thêm.
- UI check: npm --prefix apps/web run check passed; Vitest 69 files / 723 tests. Build passed; lint exited 0 with project warnings.
- Open harness gap: validate_harness.py reports the pre-existing missing apps/mobile/package.json path.
- Evidence: evidence/notes/EV-066-061_V4B_WEB_T12BC_20261124.md.
- No commit, push, stage, stash, or branch switch. Working tree remains for owner review.

## Goal v4 Phase B T-12b/T-12c final verification - 2026-11-24

- Status: IMPLEMENTATION_COMPLETE_PENDING_OWNER_REVIEW.
- Final web check: exit 0; build passed; lint exited 0 with project warnings; 69 test files and 723 tests passed.
- Harness: exit 1 only for the pre-existing missing apps/mobile/package.json path; not repaired.
- Repository security: exit 0; 8,870 files scanned; no absolute machine paths or prohibited files detected.
- Architecture: exit 0; dependency direction, mobile isolation, frontend asset gate, mobile AI boundary, and Firebase data-product checks valid.
- git diff --check: exit 0; line-ending normalization warnings only.
- Evidence: evidence/notes/EV-066-061_V4B_WEB_T12BC_20261124.md.
- No commit, push, stage, stash, or branch switch; working tree remains for owner review.

## Goal v4 Phase B Android Parent T-12a/T-12c/BR-20 — implemented and verified — 2026-11-24

- **Status:** IMPLEMENTED AND VERIFIED; pending owner review. Changes remain local, unstaged and uncommitted.
- **Scope:** `apps/ui-mobile` plus this task's FEAT-066 plan, approval amendment, context, implementation record and evidence. No backend or obsolete `apps/mobile` changes.
- **Tests:** 22 files and 252 tests passed; `UI_COPY_AND_RECOVERY_VALID` printed.
- **Gates:** typecheck, harness, repository security, architecture and `git diff --check` all exited 0. The diff check printed a CRLF-to-LF warning for `approvals/TASK_APPROVAL.md` but no whitespace errors.
- **Limitations:** no Android lint script or native test suite exists in `apps/ui-mobile`; optional Gradle assembly was not run. No backend/runtime request was made. D-066-101 governs the unavailable support-needs production state while no key source is configured.
- **Evidence:** `evidence/notes/GOAL_V4_PHASE_B_ANDROID_T12AC_EVIDENCE_20261124.md`; the append-only run log is in the designated external log folder.
