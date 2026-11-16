# FEAT-066-EV-019 — Shared auth and Teacher paper-and-crayon UI preview

- Date: 2026-11-11 (Asia/Bangkok)
- Worktree: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation
- Branch: codex/fe-ui-web-remediation
- Plan: Rev16, SHA-256 9C446770A6232A9A42B8677B345D25DECB5097D1AF4DD2FFD810A100CD3A4D5D
- Product baseline: canonical FEAT-063 SRS v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; draft remains unsigned and awaiting owner sign-off.
- Related prior evidence: auth-before/auth-after (EV-008) and Teacher dashboard baseline (EV-013).

## Scope and implementation

This is an implementation preview authorized directly by the user. It applies the design-taste-frontend, frontend-design, ui-ux-pro-max and ui-design-system workflows to the existing shared authentication and Teacher web portal. It implements the generated “paper + crayons” direction; the palette is a visual choice, not an SRS requirement.

- Redesigned shared auth layout/styles in apps/shared/portal-login.css and updated only auth-scoped overrides in apps/shared/web-brand-theme.css. Existing Teacher, School Manager and Platform Admin labels, destinations, login actions, local preview, validation/errors and role semantics were retained.
- Recolored the existing local Three.js school/books sculpture in apps/shared/PortalLoginScene.tsx. No geometry/dependency/remote asset was added; its reduced-motion, visibility pause, pixel-ratio cap, fallback and resource cleanup remain.
- Added apps/teacher-ui/src/styles/teacher-paper-crayon.css and loaded it after the shared brand stylesheet from apps/teacher-ui/src/main.tsx. It defines Teacher-local palette/tokens and restyles the authenticated shell, navigation, controls, and T01 dashboard; the shared dashboard art is overridden only inside the Teacher dashboard.
- Teacher routes/actions and API/unavailable semantics were not changed. No child media is shown. The T04 Sketch Deck route still renders its existing “Màn hình này chưa sẵn sàng” state; its white 16:9 projection surface cannot be reviewed because that surface is not implemented/connected in the current preview.

## SRS alignment

The review used §§2.3 and 3 for the web role mapping, §§5.2 and 7.3 for Teacher's assigned-class and lesson workflow, and NFR-20/NFR-29/NFR-33 for accessible web interaction and the white 16:9 Sketch Deck target. The three shared auth pages showed Teacher, School Manager and Platform Admin as the active role in turn, with corresponding existing local login destinations. No Parent, Manager-authenticated, Admin-authenticated, backend, or mobile screens were changed in this revision.

## Manual preview

A headless local browser target captured 14 PNGs: the three login routes and Teacher dashboard, classes, lessons, and Sketch Deck routes at 1440x900 and 390x844. The capture helper allowed HTTP only to 127.0.0.1:5172, :5173 and :5174; non-loopback HTTP(S) requests were blocked.

- 0 captured pages had horizontal document overflow.
- 0 Vite error overlays and 0 observed runtime exceptions.
- The auth submit control is within the first 390x844 viewport on all three login routes.
- Each auth page reports the correct active portal link via aria-current and retains the other two loopback destinations.
- The Teacher local-preview action was manually activated using the synthetic address preview@example.invalid. It navigated to /t01-lesson-workspace and set only the local TEACHER/authenticated session state; no backend or real authentication was used.
- The T01 dashboard is marked “Xem thử · không lưu” and uses local fixture data. The screenshots do not validate live Teacher data or API actions.
- Source markup retains the existing form labels, nav label/current-page semantics, status/error roles, keyboard focus rules and reduced-motion handling. No dedicated screen-reader device/session was available.

Screenshots and machine-readable viewport observations are in evidence/screenshots/auth-teacher-v16/. The capture helper is evidence/capture_auth_teacher_v16.mjs. Prior comparison images are evidence/screenshots/auth-after/teacher-desktop.png, teacher-narrow.png and evidence/screenshots/web-dashboard-icons-v11/teacher-dashboard-desktop.png, teacher-dashboard-narrow.png.

No automated tests or builds were added or run. No packages, backend/contracts, production data, credentials or provider services were changed or used. No commit or push was made.

## Evidence integrity correction — Rev24

An Auth Rev24 capture helper initially targeted this Rev16 screenshot directory before its output path was corrected. As a result, the six Auth login PNGs (Teacher, School Manager and Platform Admin at desktop and narrow widths) and `observations.json` here were overwritten on 2026-11-11. They now contain Rev24 Auth evidence and must not be attributed to EV-019. The eight Teacher route PNGs in this directory remain the original EV-019 captures. No backup of the six original Auth files or original observations was found. Use `screenshots/auth-rev24/` for current Auth evidence; `screenshots/auth-teacher-v16/` is mixed provenance until the EV-019 Auth artifacts can be restored.
