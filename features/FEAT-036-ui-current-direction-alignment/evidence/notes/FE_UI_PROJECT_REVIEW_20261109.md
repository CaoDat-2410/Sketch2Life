# FE_UI_Project UI source review — 2026-11-09

## Review record

- Target: origin/FE_UI_Project, commit c384dcc6705b54005eea5e3ce21ecccf349498d5.
- Comparison base: origin/dev merge base 1431ef81972b71303fd4a7909748fd3005769a3c.
- Scope: the Parent, Teacher, School Manager, and Platform Admin web apps added or rewritten on this branch, plus shared API/authentication and portal components. The pre-existing apps/admin-ui was checked where its dev port overlaps the new portals.
- Requirement baseline: FEAT-063 system architecture SRS v2.7-draft, as identified by the repository instructions supplied for this task. It remains a draft, not an approved final SRS.
- Authority drift: this branch's docs/context/SOURCE_REGISTER.md and docs/context/SRS_AUTHORITY.md still identify v2.5-draft. That conflicts with the v2.7-draft baseline governing this review. Keep the discrepancy visible and synchronize the branch's source register before implementation or requirement sign-off.
- Method: static review of route tables, page/state logic, API/auth gating, package scripts, and relevant requirements. A follow-up local browser pass captured 37 route/screens across the four branch portals with synthetic preview data. No UI source was changed; no tests or builds were run. Visual captures cover one viewport per route, not every scroll position or backend-authenticated state.

## Findings

Priority meanings for this report: P1 blocks a core product flow or a safety/account expectation before production use; P2 is a significant functional or data-truth issue; P3 is a minor interaction or developer-experience issue.

### UIR-01 — P1: Parent must choose an activity before reviewing the story

apps/parent-ui/src/pages/ParentScreens.tsx:1162-1177,1190-1259,1290 routes context confirmation to P05bActivitySelectionPage, asks the parent to choose one activity, and then routes to story review. The video/activity screens later read only selectedActivityId (1751-1755). This makes activity choice a pre-video gate and ties the downstream experience to one selected activity. FEAT-063 v2.7-draft §5.1 (lines 289-293), BR-55, and AC-52 put the Parent activity list after a playable video and do not make activity selection a video prerequisite. The route is replaced by an API-unavailable view outside local preview (apps/parent-ui/src/App.tsx:45), so this is currently a preview-flow defect and a production-readiness blocker, not a live backend flow. Remove the pre-video selection step and present the authorized lesson activities after playable media; preserve the unresolved no-preset behavior as an open product question.

### UIR-02 — P2: Teacher can freely select a sample child, with a cross-class fallback

apps/teacher-ui/src/pages/T06T07T08Screens.tsx:49-57,121-133 renders a child selector. If the active class has no active roster entries, eligible falls back to every active roster entry, including children outside that class. FEAT-063 v2.7-draft §5.2 requires system selection of one eligible child within the occurrence class and Teacher confirmation, not free selection. The route is intentionally unavailable in backend mode (apps/teacher-ui/src/App.tsx, /t06-sample-story-run route) and this finding currently applies to the local preview. Bind candidates to the occurrence class, let the system select, and expose a confirmation step when the Story Run API is ready.

### UIR-03 — P2: Teacher roster displays a generic green consent badge regardless of returned consent state

apps/teacher-ui/src/pages/T05ClassesScreen.tsx:72-73,99-107,124-130 fetches profiles and consent rows independently, then labels every returned profile “Consent effective.” The same screen separately renders consent rows with their actual state, including non-effective states, and can render profiles if the consent fetch failed or returned no rows. The generic badge can therefore contradict the consent information or imply a broader purpose than the effective grant. Map consent by child and purpose, show only the exact state supported by the API, and avoid a green assertion when consent state is missing or unknown.

### UIR-04 — P1: Parent Firebase session is not restored, and the production UI cannot sign out

apps/parent-ui/src/context/ParentContext.tsx:201-204 initializes isAuthenticated from preview mode rather than Firebase auth state. A successful Firebase login only flips React state (apps/parent-ui/src/pages/ParentScreens.tsx:2484-2505); after refresh, the route guard redirects to login even if Firebase still has a session (apps/parent-ui/src/App.tsx:29-34). The settings route, which contains logout, is replaced with ApiUnavailableView outside preview (App.tsx:56), and the preview logout only sets local state (ParentScreens.tsx:3202-3210) without calling Firebase signOut. Add Firebase auth-state rehydration and a reachable sign-out action that closes the real session.

### UIR-05 — P2: Parent profile UI accepts ages above the required maximum

The create/edit controls expose 36-155 months (apps/parent-ui/src/components/MobileLayout.tsx:244-254,283; apps/parent-ui/src/pages/ParentScreens.tsx:2282,2353-2360), and ParentContext.tsx:335-394 stores profile ages without enforcing the target range. FEAT-063 v2.7-draft FR-PL-25 and AC-62 specify 36-120 months. Values 121-155 are accepted in preview and may be shown as valid. Align labels, bounds, and context-level validation to 36-120; also correct the Parent README's separate 24-155-month description.

### UIR-06 — P2: Parent activity page records a completion checklist and completion action

apps/parent-ui/src/pages/ParentScreens.tsx:1751-1756,1813-1853 stores three completion booleans, exposes them as pressed checkboxes with a progress meter, and offers “Hoàn tất hoạt động & Tiếp tục.” FEAT-063 v2.7-draft §2.3, §31.8, and FR-PL-22 specify that Parent does not set activity completion. Keep materials and safety instructions as guidance; remove completion recording and completion language unless a separately approved contract adds that capability.

### UIR-07 — P2: Video player shows a background-music control even though background music must stay disabled

apps/parent-ui/src/pages/ParentScreens.tsx:1511,1636-1644,1695-1702 initializes bgmMuted to false and toggles it from two controls. The state only changes the control/icon; this page renders illustration artwork, not a media element controlled by that state. FEAT-063 v2.7-draft BR-24 requires background music to remain disabled. Remove the BGM controls and show only controls that affect the playable media and supported audio tracks.

### UIR-08 — P2: Teacher document upload cannot resume after a page refresh

apps/teacher-ui/src/pages/TeacherApiImportPage.tsx:36-39,110-143 holds the upload session, accepted part numbers, and selected file only in component state. After refresh the session ID and file reference are gone, and the UI has no authorized session lookup to recover the existing multipart upload. This conflicts with FEAT-063 v2.7-draft FR-C-12's durable resumability requirement. Persist a safe resumable session reference and recover server state for the same reselected/verified file, or expose an authorized active-session lookup; keep unknown upload outcomes recoverable.

### UIR-09 — P3: Manager and Platform Admin notification buttons are inert

apps/school-manager-ui/src/components/ManagerLayout.tsx:86-89 and apps/platform-admin-ui/src/components/AdminLayout.tsx:79-82 render notification buttons without a click handler or destination, and show a dot unconditionally. Remove the affordance until notifications exist, or connect it to a real notification view and derive the dot from unread data.

### UIR-10 — P2: Two portals and the existing admin app compete for dev ports

apps/school-manager-ui/package.json:7 pins Vite to 5173, while the pre-existing apps/admin-ui/package.json:7 uses Vite's 5173 default. apps/platform-admin-ui/package.json:7 pins 5174, which is also the usual fallback when a second Vite server cannot use 5173. Starting these portals together can move one or more apps away from their README URLs. Assign unique explicit ports across the four apps or document a single supported run matrix.

### UIR-11 — P2: Teacher UI regression tests were removed without replacements

The branch deletes apps/teacher-ui/src/__tests__/ObservationFeedbackPage.test.tsx, SessionLobbyRuntime.test.tsx, and app.test.tsx. No .test.* or .spec.* files are present under Parent, Teacher, School Manager, or Platform Admin UI in this branch. This removes regression coverage while replacing the Teacher routes and adding three portal surfaces. Restore or replace focused coverage for route/auth gates, consent display, Parent flow constraints, and upload recovery before implementation is accepted. Tests were not run as part of this review.

## Known integration blockers (not classified as UI defects)

- Platform Admin login correctly fails closed because the backend role-discovery endpoint is not available. apps/shared/backendApi.tsx:462-464 throws ROLE_DISCOVERY_UNAVAILABLE; the login screen explains this, and apps/platform-admin-ui/src/pages/AdminScreens.tsx:94-109 blocks moderation in backend mode. Do not bypass role verification. The portal remains unusable with a real backend until the contract is provided.
- Parent Story Run, video playback, feedback, settings, and several profile surfaces are explicitly replaced by API-unavailable screens in backend mode. Teacher T06/T07/T08 preview screens are also gated. These are visible integration gaps, but the current UI labels the missing APIs rather than claiming a successful backend operation.
- This source review did not validate visual spacing, mobile breakpoints, keyboard behavior, contrast, or screen-reader behavior. Capture and review real browser states after the backend/preview paths and a runtime environment are available.

## Review disposition

This is a read-only review under FEAT-036's recorded authorization. It does not approve implementation or change the feature plan's AWAITING_APPROVAL status. No product code, API contract, generated asset, approval record, or deployment configuration was changed.



## Visual capture supplement — 2026-11-09

The owner-requested capture set is stored in evidence/screenshots/fe-ui-project-20261109/, with a route index, capture manifest, and downloadable archive. It contains 37 PNGs: Parent 21 (including its splash, three onboarding steps, authentication, and child-profile section), Teacher 10, School Manager 3, and Platform Admin 3. Parent screens use a 430×932 viewport; the three desktop portals use 1440×1000. The capture used Google Chrome headless 157.0.8103.38 against local loopback preview with synthetic demo data. The browser log recorded no JavaScript exceptions. No provider credentials or backend API workflow was used.

The screenshots visually confirm the pre-video Parent activity chooser, Parent completion checklist, and Teacher sample-child selector. Production-mode API-unavailable states remain documented separately above.
