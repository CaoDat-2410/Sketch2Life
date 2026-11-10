# FEAT-066 status

- Status: `IMPLEMENTATION_VALIDATED`
- Updated: 2026-11-10 (Asia/Bangkok)
- Active plan: revision 6; SHA-256 `25E24871660A892C3380A359EA5285C6148B4C47FC75248C35D71FAC303231C9`.
- Approval: `APPROVED_FOR_IMPLEMENTATION`; revision 5 approval/hash preceded logout source edits, and revision 6 approval/hash preceded flow-guide authoring. Both direct user requests are recorded in `approvals/TASK_APPROVAL.md`.
- Product baseline: FEAT-063 SRS v2.7-draft Rev57, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`, still unsigned.
- Scope remains only `apps/school-manager-ui` and FEAT-066 governance/evidence in worktree `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`, branch `codex/fe-ui-web-remediation`.

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
