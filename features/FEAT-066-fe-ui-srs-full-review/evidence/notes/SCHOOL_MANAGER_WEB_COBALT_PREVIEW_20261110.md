# FEAT-066-EV-011 — School Manager dashboard Cool Grey + Cobalt preview

Date: 2026-11-10 (Asia/Bangkok)
Worktree: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation
Branch: codex/fe-ui-web-remediation
Plan revision: 9, SHA-256 03FF50D8330884BB815CCF8D8E68186F250DBE70279D6EC9FBD163423EFB24AC
SRS: FEAT-063 v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; awaiting formal owner sign-off. The SRS does not prescribe this palette.

## Scope

Local visual experiment on the default M02 dashboard route /m02-organization-management only. The route-scoped shell marker is present only when the M02 route has no section query. M02 teachers/classes/quota/settings, M01, shared styles, mobile apps, APIs, auth behavior, business behavior, and child-media privacy are outside this color preview and remain unchanged.

The generated light palette uses canvas #EEF0F3, surface #E2E5EA, ink #0B0C0E, muted text #5D6470, action #1F2DE6, and white action text. Neutral border and soft accent colors were derived for the preview. Existing warning and destructive status colors remain semantically distinct. Generated inverse tokens are included for dark theme, but this evidence capture used the light theme only.

## Manual browser review

Reused the local Vite server at http://127.0.0.1:5173/, bound to 127.0.0.1. Listener PID 23232 runs vite.js from the authorized worktree; the HTTP root returned 200. The existing isolated headless Edge review profile on port 9233 used synthetic School Manager sessionStorage only. No credentials, production data, backend, or external provider were used.

At 1440x900:
- Dashboard shell class is mg-shell mg-shell--palette-preview.
- Computed canvas token is #EEF0F3 and accent token is #1F2DE6.
- Document width is 1440; horizontalOverflow=false.
- The visible dashboard action is 46px high and inside the viewport.

At 390x844:
- The same dashboard-only marker and palette tokens are present.
- Document width is 390; horizontalOverflow=false.
- The primary dashboard action is inside the viewport.

Route-scope checks at 390x844:
- M02 teachers shell class remains mg-shell, canvas token #F3F1E8, accent token #3D6848.
- M01 shell class remains mg-shell, canvas token #F3F1E8, accent token #3D6848.

This is a visual/DOM check, not an assistive-technology evaluation. Dark mode, authenticated backend flows, automated tests, and builds were not run.

## Result

The desktop and narrow screenshots show the palette on the current dashboard. Route scope and horizontal bounds match the revision 9 acceptance criteria. The preview remains a local design experiment; it is not a permanent palette decision or a new SRS requirement.

## Artifacts

- screenshots/school-manager-cobalt-preview/m02-dashboard-desktop.png
- screenshots/school-manager-cobalt-preview/m02-dashboard-narrow.png
- screenshots/school-manager-cobalt-preview/observations.json
- capture_school_manager_cobalt_dashboard.mjs
- Product changes: apps/school-manager-ui/src/components/ManagerLayout.tsx and apps/school-manager-ui/src/styles/mg-manage.css
- No commit or push was made.
