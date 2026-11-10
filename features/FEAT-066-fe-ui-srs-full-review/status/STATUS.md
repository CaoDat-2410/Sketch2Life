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
