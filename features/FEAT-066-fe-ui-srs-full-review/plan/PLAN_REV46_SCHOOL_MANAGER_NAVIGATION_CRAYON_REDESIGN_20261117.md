# FEAT-066 Plan Rev46 — School Manager navigation and theme restoration

- **Type:** Existing product UI remediation using the established crayon/paper design system.
- **Status:** APPROVED_FOR_IMPLEMENTATION for the exact scope below.
- **Owner request:** “Bây giờ tối ưu và làm đẹp lại mấy phần bên trong của navbar đi toàn bộ theo SRS mới nhất cho đúng với ui/ux mà srs đề ra”.
- **Feature/worktree:** FEAT-066, branch `codex/fe-ui-web-remediation`.
- **Product source:** `docs/context/SRS_AUTHORITY.md` selects FEAT-063 v2.7-draft Rev60 as the canonical working SRS; it remains unsigned. The owner also supplied the later Rev69 copy for this task. The applicable School Manager responsibilities in the supplied copy are consistent with the canonical baseline; this plan does not change either SRS or claim formal sign-off.
- **Existing state:** Preserve all pre-existing worktree changes, including the Manager API/auth integration and Platform Admin UI work.

## Findings

1. The live `/school` route sets `html[data-portal="school-be1"]`, but the School Manager styles are scoped to `html[data-portal="school-preview"]`. This leaves the Manager business pages unstyled in the live portal and is consistent with the supplied screenshot.
2. The current shared shell gives the School Manager menu only two groups, omits several SRS responsibilities, and exposes an account control that navigates to the roster instead of an account page.
3. Current FE/backend evidence supports organization overview, class listing, public-grant review, class-scoped minimal roster/consent reads, and Parent-group list/create. Teacher-group management, Teacher assignment discovery, school feedback, capacity-safe operations, quota, billing and inbox contracts remain unavailable; these must remain clearly marked as waiting for APIs.

## Scope

- Reconcile the four imported School Manager stylesheets with the actual `school-be1` portal key while preserving other roles and any obsolete preview selector compatibility needed by existing source.
- Redesign only the School Manager navigation hierarchy, labels, waiting-state markers, sidebar appearance, and the Manager account indicator within the shared shell.
- Organize items by SRS work area: school/roster/groups, learning-content review/feedback, and capacity/quota/billing/inbox. Keep supported pages reachable; send unsupported items to explicit dependency explanations.
- Replace the Manager account button's misleading roster navigation with a non-interactive role/scope indicator because the SRS and current routes do not provide a Manager profile page.
- Use existing icons, fonts, colors and CSS; no generated bitmap asset, new dependency, API, backend or product-policy change.

## Acceptance criteria

- **AC1 — Correct style activation:** On `/school` and all mounted Manager routes, the Manager paper/crayon tokens, page styles and navigation styles apply under `data-portal="school-be1"`; other role styles remain unchanged.
- **AC2 — SRS navigation coverage:** The menu includes organization overview, classes, roster/consent, Teacher assignment and Teacher/Parent groups, Teacher public-lesson review, school-scoped feedback, capacity, quota, billing and inbox.
- **AC3 — Contract-aware availability:** Existing supported pages remain active. Every unsupported workflow is marked “Chờ API” and opens a page that names the missing contract; no unsupported action is represented as working.
- **AC4 — Scope and privacy:** Labels explain one-school organization scope. Roster/consent remains minimal and read-only; no child media or cross-organization data is introduced.
- **AC5 — Correct affordances:** The Manager role indicator does not link to an unrelated route. Active navigation has a single visible and accessible current item; focus, Escape, drawer close and logout/change-password behavior remain intact.
- **AC6 — Responsive/accessibility:** Sidebar scroll is independent from its fixed footer; link and button targets are at least 44 CSS px; labels and pending states remain legible at desktop, narrow/zoomed widths and keyboard focus; reduced-motion remains respected.
- **AC7 — Regression boundary:** Teacher and Platform Admin navigation, routes, auth, API contracts, backend, database, mobile app, SRS files, dependencies, credentials, commit and push remain untouched.

## Validation

- Run the existing Web production build to check TS/CSS bundling.
- Inspect the live Manager portal at desktop, tablet/zoomed width and phone width, including open/closed drawer, active route and keyboard focus. Record results and limitations in FEAT-066 evidence.
- Do not run the application test suite for this task.
