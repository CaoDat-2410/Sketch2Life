# FEAT-066 EV-052 — School Manager navigation and theme restoration

- Date: 2026-11-17.
- Plan: Rev46, SHA-256 FA3EB6DFBB3E5E32BF61B75FD17E8230DF0D67C712079CAB1EB3F9222A34A255.
- Product authority: FEAT-063 v2.7-draft Rev60 per SRS_AUTHORITY.md; unsigned. The owner-supplied Rev69 copy was checked for the applicable School Manager responsibilities. No SRS was edited or signed.

## Findings and implementation

- The live application sets the Manager portal key to school-be1, while all four imported School Manager stylesheets were scoped to school-preview. Added a selector alias for both keys so current Manager styles activate without changing the route identity or other roles.
- Reorganized navigation into Nhà trường, Học liệu & phản hồi, Nguồn lực and Thông báo. It now covers overview, classes, minimal roster/consent, Teacher assignment and groups, Parent groups, Teacher public-lesson review, school feedback, capacity, video quota, billing and inbox.
- Existing contract-backed pages remain available. Teacher-group management, Teacher assignment, school feedback, capacity, quota, billing and inbox are labelled Chờ API and lead to explicit contract explanations. No unsupported request or business mutation was added.
- Kept roster/consent read-only and minimal. Replaced the School Manager account control that navigated to roster with a static role indicator because no Manager profile route exists.
- Added scoped paper/crayon sidebar styling, active/waiting states, dark-theme tokens, responsive drawer sizing, 44px controls and reduced-motion support. No image asset or dependency was added.

## Validation

- Web production build: passed (TypeScript and Vite).
- Focused Oxlint: exit 0; four existing warnings remain in WebAppShell.tsx (three fast-refresh export warnings and one set-state-in-effect warning); no new finding in SchoolManager App.tsx.
- git diff --check: exit 0. Git emitted only its existing CRLF-to-LF normalization warnings.
- Local FE login URL on port 5173 returned HTTP 200 after the CSS update. The dev server remains available for owner review.
- No automated application tests were run for this task.
- Authenticated visual capture was unavailable: the local review browser/CDP endpoint on port 9233 was not running. No synthetic session or account credential was used for screenshots. The owner can review the Manager portal after refreshing/signing in.

## Boundaries

- No backend/API/database/auth/role policy, Parent/mobile, SRS, credential, or child-data change.
- No commit or push.
