# Web dashboard alignment Rev25 — 2026-11-11

## Scope and authority

This pass keeps the accepted role shell and refines only the Teacher, School Manager, and Platform Admin overview dashboards against the Rev23 concept boards. The FEAT-063 v2.7-draft Rev57 remains the canonical working SRS; its recorded SHA-256 is `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5` and the authority record says it is awaiting owner sign-off. This visual pass does not change product requirements or API behavior.

The work is confined to `apps/teacher-ui`, `apps/school-manager-ui`, `apps/platform-admin-ui`, and FEAT-066 evidence/governance in `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation` on `codex/fe-ui-web-remediation`. Parent/mobile, other roles, backend/contracts, manifests, automated tests/builds, commit, and push are excluded.

## Teacher checkpoint

The current Teacher overview was reviewed against `assets/generated/rev23/teacher-flows.png` at 1440×900 and 390×844. It has one heading and three work areas (assigned classes, learning materials, teaching sessions). The duplicate preview banner, route shortcuts, and dashboard footer are absent; the shell keeps the local-preview indicator. Area-specific empty and unsupported API states remain, with no sample records or quota values.

Both viewport captures have no horizontal overflow, Vite overlay, runtime exception, or console error. At narrow width, Enter opens the navigation drawer and moves focus into it; Escape closes it and returns focus to the menu button. The preview only used synthetic local role session storage; requests were restricted to `127.0.0.1:5172`, and no product API was called.

- `screenshots/dashboard-alignment-rev25/teacher-overview-1440.png`
- `screenshots/dashboard-alignment-rev25/teacher-overview-390.png`
- `screenshots/dashboard-alignment-rev25/observations.json`

## Remaining checkpoints

School Manager and Platform Admin overview refinement and desktop/narrow review are pending. Add their observed layout, truthful API states, screenshots, keyboard results, and any remaining dependencies below after review.


## School Manager checkpoint

The overview follows the two-block Rev23 hierarchy: organization state and services. The class count is sourced only from the existing assignment-gated API read. In preview it shows an em dash with an explicit no-API-data explanation. Public review is identified as API-backed and requiring an authenticated School Manager session; invoice/payment, school subscription/quota, inbox, and feedback are marked unavailable because their APIs are absent.

Desktop and narrow captures have no horizontal overflow, Vite overlay, runtime exception, or console error. At narrow width, Enter opens the drawer and moves focus into the navigation; Escape closes it and returns focus to the menu button. Requests were restricted to `127.0.0.1:5173`; no product API was called.

- `screenshots/dashboard-alignment-rev25/manager-overview-1440.png`
- `screenshots/dashboard-alignment-rev25/manager-overview-390.png`
- `screenshots/dashboard-alignment-rev25/observations.json`

Platform Admin review remains pending.


## Platform Admin checkpoint

Replaced the preview banner, duplicate role-discovery warning, nested health panel, and six sidebar-duplicate shortcuts with four overview cards: health, queue/jobs, billing reconciliation, and lifecycle. The local health check remains behind the existing Firebase bridge + loopback conditions and never runs in preview. Queue/jobs, billing, and lifecycle state their missing API dependencies; role discovery remains on the permissions route.

## Cross-role review results

All six final captures were visually inspected at 1440×900 and 390×844. `observations.json` records viewport/document width equality (no horizontal overflow), no Vite overlay, runtime exception, or console error. Enter opens each narrow drawer and focuses the first navigation item; the logout action is visible while the drawer is open; Escape closes it and returns focus to the menu button. The capture helper uses only synthetic local sessionStorage flags and allows only the role's own `127.0.0.1` port. No authenticated/product API, provider, credentials, real user data, or child data were used.

- Teacher: `screenshots/dashboard-alignment-rev25/teacher-overview-1440.png` and `teacher-overview-390.png`.
- School Manager: `screenshots/dashboard-alignment-rev25/manager-overview-1440.png` and `manager-overview-390.png`.
- Platform Admin: `screenshots/dashboard-alignment-rev25/admin-overview-1440.png` and `admin-overview-390.png`.
- Measurements and keyboard results: `screenshots/dashboard-alignment-rev25/observations.json`.

## Out-of-scope accessibility finding

The DOM capture found `aria-current="page"` on 10 School Manager and 11 Platform Admin navigation entries because their React Router `NavLink`s share the same pathname and differ by query string. CSS still marks only the correct item visually, and each drawer's keyboard behavior passes. The Rev25 approval was limited to dashboard overview content and preserving the accepted shell, so this navigation semantics issue remains for a dedicated accessibility correction.

## Completion

Rev25 is complete pending user review. Teacher source was already aligned to the three-area board, so it was not changed in this pass. Manager/Admin dashboard source and styles changed as described; no backend flow was simulated. No automated tests/builds, commit, or push were run.
