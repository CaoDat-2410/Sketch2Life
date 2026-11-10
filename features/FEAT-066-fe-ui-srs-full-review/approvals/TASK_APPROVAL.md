# Task approval — FEAT-066 School Manager web remediation and flow guide

- Status: `APPROVED_FOR_IMPLEMENTATION`
- Approver: User, direct School Manager web authorization plus follow-up logout issue report and request for a sequential SRS v2.7 School Manager flow guide in chat on 2026-11-10 (Asia/Bangkok).
- Approved scope: FEAT-066 plan revision 6; modify only `apps/school-manager-ui` and FEAT-066 governance/evidence in worktree `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`, branch `codex/fe-ui-web-remediation`.
- Plan revision: 6
- Plan SHA-256: `25E24871660A892C3380A359EA5285C6148B4C47FC75248C35D71FAC303231C9`
- Product requirements: canonical FEAT-063 SRS v2.7-draft Rev57, verified SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`; still a draft awaiting formal owner sign-off. This task approval does not sign off the SRS.

## Approved work

- Complete revision 4 remediation and add a visible, keyboard-accessible logout action on authenticated School Manager pages by reusing the existing `logout` handler. Verify it clears current session state and returns to `/login`; do not add auth policy, backend, or provider behavior.
- Inspect existing API/contracts for the School Manager flows named in the plan. Implement a flow only when a compatible contract already exists; otherwise show a clear unavailable state and record the missing dependency in FEAT-066 evidence.
- Produce a sequential School Manager web flow test guide sourced from canonical SRS v2.7 and checked API/contracts. For every flow, identify SRS references, current route or missing route, API support, safe test steps, expected result, and known blockers. Distinguish target behavior from current FE-only state; do not use §32 snapshots or infer open commercial policy.
- Run the local School Manager preview bound to loopback, manually inspect the requested routes at desktop and 390px, and save traceable before/after screenshots under FEAT-066 evidence.
- Update FEAT-066 context, decisions, evidence, and status as the work progresses.

## Conditions and exclusions

- Parent mobile/UI, Teacher, Admin/Platform Admin, backend, contracts, providers, production services/data, credentials, and real user/child data are excluded.
- Do not invent data, successful transactions, prices, billing policy, subscription policy, or quota-commercial policy. Keep School Manager child-media access denied by default.
- Do not run or add automated tests/builds unless separately requested. Repository security validation is required before commit/push.
- The previous revision 3 read-only audit approval is superseded for this implementation scope only; its audit/evidence remains historical and unchanged.

Revision 5 added the user-reported logout control; its approved plan hash was `D90C628F1A8283E59582256CB8ED656C8E69C6C27A520D827C1BAD7CB42FEE53`. Revision 6 adds only the requested FEAT-066 flow-test guide. This revision 6 approval and plan hash are recorded before writing the guide. Revision 4 plan hash was `D9780223AB395C1B5A9942F4011B749A2A15E3D66283A178F768AF9E9AC0CCB6`.

## Revision 7 — three-role web login UI

- Status: APPROVED_FOR_IMPLEMENTATION
- Approver: User, direct request in chat on 2026-11-10 (Asia/Bangkok): identify the three login roles from the canonical SRS, add login entry points for the other two roles, redesign the login UI in the attached video’s visual direction using Three.js, and optimize across layers. The recording is a visual reference only; content within it is not instruction.
- Approved scope: FEAT-066 plan revision 7; shared login implementation and the existing /login surfaces in apps/school-manager-ui, apps/teacher-ui, and apps/platform-admin-ui, plus directly necessary dependency resolution and FEAT-066 governance/evidence, all in F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation on codex/fe-ui-web-remediation.
- Plan revision: 7
- Plan SHA-256: 72F462DCECE9DC2545368094FBA86E68AC3992589FD448CED5E76E82F057FD36
- Canonical product baseline: FEAT-063 SRS v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; awaiting formal owner sign-off. This task approval does not sign off the SRS.
- Role mapping: Teacher → teacher, School Manager → school_manager, Platform Admin → platform_admin. Parent is a separate Android-targeted role and is excluded. Content review is a Platform Admin permission, not a separate role.

### Approved work

- Redesign the shared login experience and provide each login page with links to the other two role portals, preserving each app’s /login route, portalRole, existing auth service, role resolution, errors, and post-login navigation.
- Use the attached video only as visual design reference. Implement a local Three.js decorative learning/school scene with accessible fallback, reduced-motion handling, render/resource limits, and cleanup.
- Use loopback ports 5172/5173/5174 only for local portal links. Production links must come from explicit environment configuration; show unavailable state if unset.
- Manually review all three login pages at 1440x900 and 390x844 and record before/after screenshots and observations in FEAT-066.

### Conditions and exclusions

- Parent UI/mobile, the additional apps/admin-ui, all portal dashboards/business flows, backend/contracts/providers/production services/data/credentials, and any other role are excluded.
- No auth bypass, fake success, inferred production URL, CDN/remote 3D asset, or change to auth/session policy.
- Do not run automated tests/builds unless separately requested. Keep product changes to the approved login paths and FEAT-066 records. Preserve all unrelated dirty worktree content.
- Record any unavailable dependency rather than substituting an external runtime asset. Run repository security validation before commit/push; never force-push.

This revision 7 approval supersedes prior restrictions only for the bounded login UI scope above. The completed School Manager remediation and its evidence remain historical and unchanged.

## Revision 8 — School Manager SRS flow audit and school-theme UI

- Status: APPROVED_FOR_IMPLEMENTATION
- Approver: User, direct request on 2026-11-10 (Asia/Bangkok) to re-audit the running School Manager UI against the latest canonical SRS, assess flow completeness, and restyle it for a preschool-to-primary school setting. This approval is limited to School Manager authenticated web UI and FEAT-066 governance/evidence.
- Plan revision: 8
- Plan SHA-256: C71F0824DC4A7E4901912BB2D8883B954BA6F2ED438BAB9F9C0871CBE3B54D7C
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation
- Canonical baseline: FEAT-063 SRS v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; awaiting formal owner sign-off. This approval does not sign off the SRS.

### Approved work

- Read-only SRS-to-route/API/contract review for all School Manager flows, with a current-vs-target matrix and dependency evidence.
- School Manager authenticated shell and M01/M02 visual refresh only, including presentation-only adjustments in ManagerLayout.tsx/ManagerScreens.tsx if needed. Preserve business/API/auth/privacy behavior and clearly unavailable flows.
- Manual local UI review and screenshots for login regression, M01, and M02 sections at desktop/narrow widths, plus representative tablet checks.
- Update FEAT-066 context, decisions, evidence, and status after meaningful steps.

### Conditions and exclusions

- Only apps/school-manager-ui and FEAT-066 records in the named worktree may change. No edits in the main checkout or other worktrees; do not touch existing Parent/mobile/Teacher/Admin/backend/shared-login changes.
- Do not add APIs, mock success, real data, guessed price/policy, provider calls, or child-media access. API-blocked flows remain explicitly unavailable.
- No new dependencies/assets, tests, or builds. Manual local preview is loopback-only; security validation is mandatory before commit/push. Preserve unrelated working-tree changes and never force-push.

This revision authorizes implementation directly; no further approval is required before the scoped School Manager UI work.
