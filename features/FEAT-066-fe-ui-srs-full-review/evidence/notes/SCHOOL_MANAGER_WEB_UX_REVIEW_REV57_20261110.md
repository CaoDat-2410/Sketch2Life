# School Manager web — SRS and UI/UX review

Date: 2026-11-10 (Asia/Bangkok)
Review type: source review plus local fixture-preview inspection
Source worktree: `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`, branch `codex/fe-ui-web-remediation`, based on `95433b3a9bef893a671df6623476784dbd0fd83d`
SRS baseline: FEAT-063 `SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, v2.7-draft Rev57 (2026-11-09), SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`
SRS approval: draft awaiting formal owner sign-off; this is the canonical working baseline, not a signed final SRS.

## Scope and method

Reviewed only `apps/school-manager-ui`: `/login`, `/m01-publication-review`, and `/m02-organization-management` including the `teachers`, `classes`, `quota`, and `settings` sections. Parent mobile and all other portals were out of scope and were not inspected or run for this review.

Compared the routes and available actions with SRS §21.5 and the relevant FR/UC clauses. Inspected source for state transitions, action feedback, route coverage, accessible tab semantics, and responsive layout. Captured the local preview at 1440×900 and 390×844. The Vite preview was configured for loopback at `http://127.0.0.1:5173/`; it used synthetic preview data. No backend, external provider, credential, real account, or child data was used. The preview’s synthetic state is not evidence that an operation persists or is connected to the backend.

## Findings

### P1 — Required School Manager operations are missing or preview-only in the backend flow

The SRS screen catalog requires an organization dashboard, class capacity, class create/archive/suspend, Teacher assignment, roster management, billing period/invoice/payment state, renewal/downgrade, organization quota purchase/summary, and a notification inbox (§21.5). The implementation’s backend M02 route is `ManagerApiOrganizationPage` (`apps/school-manager-ui/src/pages/ManagerScreens.tsx:393-475`): it loads and creates classes, then explicitly states that Teacher management, parent groups, video quota, billing, and package settings are not available there. There is no School Manager feedback-reply or notification-inbox route in `App.tsx:19-24`.

This leaves required flows absent or incomplete against FR-T-02/03, FR-B-01–14, UC-06/08/12/13, and FR-PL-22. In preview mode, class/slot/quota/subscription actions are illustrative local state or toast-only handlers (`ManagerScreens.tsx:480-488, 597-742`); they do not close the backend gap. The preview labels its data as illustrative, so those values must not be presented as live capacity, quota, or billing evidence. SRS pricing and some quota commercial values remain open; this finding does not infer a price or invent a product rule.

### P2 — “Request changes” increases the “Approved” count in M01 preview

`finish()` always appends the lesson ID to `done` (`ManagerScreens.tsx:178-184`). Both `approve()` and `reject()` call it (`:186-203`), and the header labels `done.length` as “Đã duyệt” (`:218-220`). Reproduced in the local preview: after “Yêu cầu chỉnh sửa”, the count changes from 0 to 1 even though the lesson was not approved. Screenshot: `../screenshots/m01-after-request-changes-desktop.png`.

This is a preview-state correctness bug; no backend data was changed. Keep approval and change-request outcomes in distinct states/counts.

### P2 — Notification bell advertises an inbox that cannot be opened

`ManagerLayout.tsx:86-89` renders an accessible-name button with no click handler and an unconditional unread dot. The SRS requires an in-app inbox as the canonical notification surface, including billing notices (§21.5; FR-B-08/09/14). The current control communicates unread work but provides no way to inspect or act on it.

### P2 — Narrow layouts clip the M02 class and quota controls

At 390×844, the “Lớp học” heading collides with the “Tạo lớp mới” and “Xem lượt video” actions; quota action buttons extend past the visible content. Screenshots: `../screenshots/m02-classes-narrow.png` and `../screenshots/m02-quota-narrow.png`. The contributing rules keep `.mg-card-head` and `.mg-kpi-row` on one flex row and small buttons at 38px (`mg-manage.css:42,56,76`); the page clips overflow at the container level, which hides the problem instead of reflowing it.

Desktop is the SRS target for this web portal; the narrow-viewport observation is an exploratory UX robustness finding, not a claim that the SRS promises mobile-web support. The 38px controls are also difficult to target at narrow widths.

### P2 — M01 review tabs lack complete keyboard and screen-reader tab semantics

The preview declares a `tablist` and two `tab` buttons with `aria-selected` (`ManagerScreens.tsx:276-278`), but the tabs have no `aria-controls`, there is no associated `tabpanel`, and there is no arrow-key/roving-focus handling. Keyboard users cannot use the expected tab interaction model, and assistive technology is not given a programmatic link from each tab to its panel.

### P3 — Organization pill looks like a dropdown but is not interactive

`ManagerLayout.tsx:90-97` renders the organization name and down-chevron inside a static `<span>`, not a button or menu trigger. The SRS models each school as one organization per School Manager, so this is not a missing organization-switch requirement; the chevron creates a misleading affordance. Remove the dropdown cue or provide an actual supported action.

## Positive observations

- Desktop captures of login, dashboard, teachers, classes, quota, settings, and publication review showed a readable hierarchy and no visible horizontal clipping.
- Login and preview states clearly say that the data is illustrative and not saved.
- M01 preview requires a public scope and four review checks before approval, and requires a written reason before requesting changes.
- M01 and settings explicitly state that child media is hidden from the Manager; that presentation is consistent with the SRS privacy boundary.

## Evidence and limits

Captured screenshots are under `evidence/screenshots/`:

- `school-manager-login-desktop.png`, `school-manager-login-narrow.png`
- `m02-dashboard-desktop.png`, `m02-dashboard-narrow.png`
- `m02-teachers-desktop.png`, `m02-classes-desktop.png`, `m02-classes-narrow.png`
- `m02-quota-desktop.png`, `m02-quota-narrow.png`, `m02-settings-desktop.png`
- `m01-publication-review-desktop.png`, `m01-publication-review-narrow.png`, `m01-after-request-changes-desktop.png`

These captures show only local synthetic preview states. No automated tests, accessibility scanner, build, backend call, external provider call, or real-data flow was run. The review confirms UI/source gaps, not the behavior of unstarted backend services. Worktree Git metadata was not readable from the current sandbox during final status inspection, so no new clean/dirty assertion is made here.
