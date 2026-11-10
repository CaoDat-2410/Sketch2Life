# FEAT-066 status

- Status: MANUAL_UI_REVIEW_COMPLETE_SECURITY_VALIDATION_PASSED_PENDING_INTEGRATION
- Updated: 2026-11-10 (Asia/Bangkok)
- Active plan: revision 7; SHA-256 `72F462DCECE9DC2545368094FBA86E68AC3992589FD448CED5E76E82F057FD36`.
- Approval: `APPROVED_FOR_IMPLEMENTATION` for plan revision 7; direct user request and matching hash recorded in `approvals/TASK_APPROVAL.md` before code edits.
- Product baseline: FEAT-063 SRS v2.7-draft Rev57, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`, still unsigned.
- Current revision 7 scope: `apps/shared` login and existing `/login` pages in `apps/school-manager-ui`, `apps/teacher-ui`, and `apps/platform-admin-ui`, plus FEAT-066 governance/evidence in worktree `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`, branch `codex/fe-ui-web-remediation`. Parent, dashboards, additional Admin, and backend remain excluded.

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
- No automated tests or builds were run. Repository security validation passed on the final reviewed diff: 6,867 publishable files scanned, with no absolute machine paths. Commit/integration remain pending.
## Revision 7 three-role auth UI review (2026-11-10)

- Shared `/login` pages map Teacher, School Manager, and Platform Admin to the SRS §3 role values and expose the other two local web portal destinations. Keyboard navigation and active-role semantics are recorded in FEAT-066-EV-008.
- The first 390px capture found overlapping heading/description spacing. Mobile margins were corrected, then all six role/viewport combinations were recaptured. At 390x844, submit bottoms are 731px (Teacher), 731px (School Manager), and 750px (Platform Admin); all have 390px document width. At 1440x900, all pages fit without overflow.
- Three.js local rendering, reduced-motion static rendering, context-loss CSS fallback, and keyboard activation were reviewed. Real sign-in was not attempted; Platform Admin role discovery remains blocked by the existing API. Details and screenshots are in FEAT-066-EV-008.
- Repository security validation passed on the final reviewed diff: 6,867 publishable files scanned, with no absolute machine paths. Commit and integration have not occurred.
## Revision 7 auth UI integration (2026-11-10)

- Commit `89d8785d` (`feat(auth): redesign three web portal login pages`) was pushed fast-forward without force to `origin/codex/fe-ui-web-remediation` and `origin/feature/fe-ui-full-remediation`.
- Repository security validation passed immediately before commit and push: 6,867 publishable files scanned; no absolute machine paths.
- The local `feature/fe-ui-full-remediation` worktree was not checked out or modified because it contains unrelated changes. Its remote branch is now advanced to the reviewed commit.
- Unrelated root approval, Parent UI changes, and FEAT-070 evidence remain unstaged and unmodified.