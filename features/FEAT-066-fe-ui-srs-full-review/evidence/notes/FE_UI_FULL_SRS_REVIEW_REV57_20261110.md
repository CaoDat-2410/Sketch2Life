# Full FE review against canonical SRS Rev57

Date: 2026-11-10 (Asia/Bangkok)
Review type: read-only source review
Reviewed source: readable files in `F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation`
SRS: FEAT-063 `SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, v2.7-draft Rev57 (2026-11-09), SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`
SRS approval: draft awaiting formal owner sign-off.

## Summary

The review covered `apps/mobile`, `apps/ui-mobile`, Parent Web, Teacher, School Manager, Platform Admin, the additional Admin UI, and shared auth/API integration. The largest SRS gaps are that Parent Android remains a fixture harness, major Teacher flows are preview-only without backend integration, School Manager does not expose the required organization/billing workflows in backend mode, and Platform Admin operations cannot load safely through the present role/API integration.

Several earlier Parent UI mismatches appear resolved in current source: activity selection is after video, age scope uses 36–120 months, and completion/BGM controls are absent. The F5 path now begins signed out and validates the Firebase token against `parentLessons()`. These findings are source observations; no fresh build or runtime session was used.

## Findings

### P1 — Parent Android target is still only a fixture harness

`apps/mobile/src/app/AppRoot.tsx:3-8` mounts `FixtureFlowScreen`; `apps/mobile/README.md:55` describes the deterministic fixture harness. FR-P-01 and §21.5 identify `apps/mobile` as the Parent Android client, while `apps/ui-mobile` is reference material. The Parent Web app cannot be treated as a substitute for the missing Android target.

### P1 — Required Teacher run and Sketch Deck flows stop at preview mode

`apps/teacher-ui/src/App.tsx:54-56` wraps Sketch Deck, sample Story Run, and presentation-confirmation routes in `ApiOrPreview`; outside local preview they show an unavailable state. This leaves core Teacher flows unintegrated with the backend under FR-T-10–16, FR-T-18/19, and §21.5. The fail-closed UI is safer than fabricating successful backend actions, but the target flows are not usable in backend mode.

### P1 — School Manager backend surface covers only part of the SRS workflow

`apps/school-manager-ui/src/pages/ManagerScreens.tsx:393-478,480-488` loads class assignments/listing and supports class creation, then uses that page for the backend M02 route. Required organization capacity, roster, Teacher assignment, subscription/invoice/payment, quota purchase, billing notifications, and lifecycle/suspension flows are missing or incomplete in backend mode. Preview quota/slot values are explicitly illustrative and non-persistent. Relevant requirements: FR-T-02/03, FR-B-01–09, and §21.5.

### P1 — Platform Admin actions are not available through backend mode

`apps/shared/backendApi.tsx:459-464` refuses `platform_admin` sign-in because there is no role-discovery API. `apps/platform-admin-ui/src/pages/AdminScreens.tsx:84-86,94-109,270-280` exposes health checks but marks organization/content/policy/audit data and moderation queue unavailable outside preview. This is a fail-closed integration gap, not an authorization bypass. The SRS models Content Admin as a Platform Admin permission and denies access to child media; align any future role/API work to §3, §20, and §21.5.

### P2 — FE worktree source authority and register still point to v2.5

`docs/context/SRS_AUTHORITY.md:9,14` and `docs/context/SOURCE_REGISTER.md:6` in the FE worktree still direct contributors to v2.5-draft. The canonical root authority is v2.7-draft Rev57. This documentation drift can route later requirement work to a superseded baseline. Update the branch authority records in a separately scoped task before further SRS-based implementation; no requirement was taken from v2.5 in this review.

### P2 — Teacher preview allows manual child selection and cross-class fallback

`apps/teacher-ui/src/pages/T06T07T08Screens.tsx:50-57,121-132` falls back to every active roster entry if the selected class roster is empty and provides a manual child dropdown. FR-T-10 and FR-PL-20 require the system to randomly select an eligible child and the Teacher to review/confirm; they prohibit arbitrary Teacher selection. Q-01 leaves eligibility and empty-set policy open, but does not reopen the random-selection rule. This route is preview-only in the reviewed implementation, so this is a misleading demo flow rather than evidence of a production-data leak.

### P2 — Consent badge is not visibly bound to the returned child/purpose state

`apps/teacher-ui/src/pages/T05ClassesScreen.tsx:99-106,124-129` requests profile and consent data independently using `Promise.allSettled`, then renders profiles with the same “Consent effective” badge. The visible join does not establish the child, purpose, version, or effective status of each grant, and profiles still render if consent lookup fails. The SRS scopes grants by purpose/version. The server remains authoritative; the concern is that this UI can overstate consent. Render a state derived from an explicit child/purpose/version match or show unknown/unavailable.

### P2 — Teacher lesson upload cannot recover its session after a page reload

`apps/teacher-ui/src/pages/TeacherApiImportPage.tsx:36,110-142` keeps the upload session and accepted parts in component state. `apps/shared/backendApi.tsx:392-414` exposes create, part, complete, and abort operations, but no authorized session read/list/recovery operation. Reload loses the session ID and selected file reference. This conflicts with durable resumable upload sessions in FR-C-12 and AC-29/AT-10. Recovery should remain actor/scope-authorized and re-check the selected file hash.

### P2 — Parent logout changes local UI state without ending the Firebase session

`apps/parent-ui/src/App.tsx:65` places settings behind `ApiOrPreview`, so the settings/logout surface is unavailable in backend mode. In preview, `apps/parent-ui/src/pages/ParentScreens.tsx:3084-3092` clears local authentication state and navigates away but does not call the available auth bridge `signOut`; `apps/parent-ui/src/context/ParentContext.tsx:205-230` can restore the same Firebase session on refresh. This can make logout appear complete while the identity session persists. Keep logout reachable and invoke the auth bridge.

### P2 — Manager notification control has no action

`apps/school-manager-ui/src/components/ManagerLayout.tsx:86-89` renders a notification button with no handler and an unconditional unread dot. The Manager inbox and billing notices are part of §21.5 and FR-B-08/09. Current feedback implies an inbox state that cannot be opened.

### P3 — Parent README age range is stale

`apps/parent-ui/README.md:15` still documents 24–155 months while FR-PL-25/BR-18 set 36–120 months. Current Parent UI age context uses 36–120 months. Update the documentation when the implementation scope is next approved.

## Additional implementation risks outside SRS conformance

- **Local dev port collision:** `apps/school-manager-ui/package.json:7` pins Vite to 5173, while `apps/admin-ui/package.json:7` uses Vite's default 5173. `apps/platform-admin-ui/package.json:7` pins 5174, a common fallback when another Vite server already occupies 5173. Starting these apps together can move a portal away from its documented URL. This is a developer workflow issue, not an SRS requirement gap.
- **Portal regression coverage is absent:** no `.test.*` or `.spec.*` source files were found under the Parent, Teacher, School Manager, or Platform Admin app source directories. The previous review records removal of three Teacher tests, but Git metadata for this worktree was inaccessible, so the removal diff could not be independently rechecked. This is a confidence gap, not a direct SRS clause violation. Add focused coverage for route/auth gates, consent state, Parent flow constraints, and upload recovery before treating remediation as accepted.

## Confirmed improvements from earlier UI findings

- Parent activity selection is shown after video; current source states activities appear after the video. This matches FR-P-05. The no-preset activity catalog behavior remains open under §31.10.
- Parent age labels/limits use 36–120 months, matching FR-PL-25; the README remains stale as described above.
- Completion marking and BGM controls from the earlier UI mismatch are no longer present in the reviewed Parent flow; FR-PL-22 forbids a completion toggle.
- The F5 route no longer defaults to the API menu when there is no valid parent session: it starts signed out and checks the Firebase token plus `backendApi.parentLessons()` before entering the Parent flow.

## Scope and evidence limits

- `apps/mobile` is the target Android implementation under FR-P-01; `apps/ui-mobile` is reference-only and includes older activity-first flows. Do not ship those reference flows as current behavior; FR-P-05 requires post-video activities.
- Parent Web is present in source, but its target scope and account-creation behavior are not established by the §21.5 screen catalog used in this review. Do not infer registration/account creation requirements from a visual form.
- Exact eligibility, consent/exclusion, reselect, empty-set response, and selection evidence remain open under Q-01. Parent no-preset activity-catalog behavior also remains open. Preserve these as questions for their named owners.
- The existing 37-screen archive `features/FEAT-036-ui-current-direction-alignment/evidence/FE_UI_Project_Screenshots_20261109.zip` is historical synthetic-preview evidence from an earlier commit and does not establish the current branch's route/device coverage. Current tablet behavior was not exhaustively captured in this review.
- Git metadata for the FE worktree could not be accessed under this environment's filesystem boundary, so no commit SHA or clean/dirty assertion is made for that worktree. Its files were read directly.
- No product code was changed. No tests, builds, backend/API calls, production data access, or new device captures were run.
