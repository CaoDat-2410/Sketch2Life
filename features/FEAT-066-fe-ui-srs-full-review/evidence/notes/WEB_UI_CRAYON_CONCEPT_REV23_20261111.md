# FEAT-066-EV-026 — Complete web UI crayon design preview

## Scope and authority

This is a design-only review package for shared web Auth and the three SRS web roles: Teacher, School Manager and Platform Admin. The canonical working source is FEAT-063 v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; the authority record says it remains unsigned/awaiting owner sign-off. The plan is Rev23, SHA-256 E4E6D438FE4058694EE20EA25F01F670F2AB6F33E0BD05F9C3AA8101E9552774, approved for preview only. Requirements are traced to SRS §§1–31; §32 was not used as target requirements. OI-17 design/wireframe sign-off remains open.

The visual direction uses warm paper, oat, graphite, school blue, restrained school-color accents and single-color outline navigation. The exact colors are a design proposal; the SRS does not mandate a palette. Content Admin remains a permission within Platform Admin. Parent Android/mobile, the additional Admin UI, Teacher/Manager/Admin source implementation, backend and API changes are excluded.

## Deliverables

- assets/generated/rev23/auth-portals.png: shared desktop and narrow auth entry, role routing, and access-denied concept.
- assets/generated/rev23/teacher-flows.png: Teacher dashboard, assigned-class/roster shell, lessons/import/revision panel, and narrow occurrence with blank optional 16:9 Sketch Deck and server-selected single-child gate.
- assets/generated/rev23/school-manager-flows.png: organization overview, classes and Teacher assignment, exact-version content review with separate decision states, and narrow billing/subscription/quota/inbox/feedback dependency states.
- assets/generated/rev23/platform-admin-flows.png: platform overview, content/catalog versioning, aggregate operations and audit areas, metadata-only privacy boundary, and narrow responsive layout.
- evidence/notes/WEB_UI_CRAYON_ATLAS_REV23.md: full route/flow inventory with SRS references and the current frontend API boundary.
- assets/generated/rev23/PROVENANCE.md: generation provenance and SHA-256 for each board.

## SRS and API boundaries reflected in the concepts

- Auth resolves role/access through the server; a role link does not grant permission. Platform Admin role discovery is currently absent in the inspected frontend adapter.
- Teacher class/roster reads and lesson/document APIs exist at the adapter boundary, but profile writes, corrected immutable extraction confirmation, occurrence/plan, one-child server selection runtime, StoryRun/job, playback/projection/lifecycle, quota/history/inbox/settings flows are absent. The board shows blank/unavailable states, not fabricated content or child data.
- School Manager has tenant-scoped assignment/class/profile reads and M01 grant list/decision methods, but no verified exact immutable-version fetch. Class lifecycle, safe capacity admission, Teacher provisioning/reassignment/offboarding, invoice/payment/subscription/quota, inbox and feedback reply flows remain unavailable or unverified. Review actions remain distinct and disabled until exact-version evidence is available.
- Platform Admin health and a moderation method name exist, but role discovery, authenticated queue/list/exact-version flow, catalog versioning, organization/aggregate operations/billing reconciliation/lifecycle/audit feeds are absent in the inspected adapter. Admin screens remain unavailable and metadata-only; no child media/story is exposed.
- No price, payment terms, unresolved selection rule, consent policy or other open SRS item was inferred. No fake success, fake transaction, sample identity, unread badge or operational count is shown.

The API findings above are source inspection only. No authenticated API, live backend, production service, user/child record, credential or external provider was used. A method name alone does not verify server-side authorization or runtime behavior.

## Review result and limitations

All four generated boards were visually inspected as images and copied unchanged from their preserved ImageGen outputs. The role mapping, layout hierarchy, desktop/narrow composition, outline-icon treatment, empty/unavailable states and privacy boundaries are visible. The flow atlas—not small image text—is authoritative for exact labels and sequencing. ImageGen can misspell or distort fine print; these boards are reviewable direction-setting artifacts, not implementation specifications or accessibility/runtime evidence. The boards cover representative page families; the atlas enumerates the complete target flows and recovery states.

No web app was started or captured for this design-only task. No browser behavior, responsive CSS, keyboard/screen-reader interaction, API or runtime was tested. No app source was changed by this revision. Existing unrelated/pre-existing dirty worktree files remain untouched. No automated tests/builds, repository validators, commit or push were run.

## Next state

Ready for user visual review. Application implementation is not approved; wait for direct user acceptance and a matching plan/approval revision before changing app source. Do not promote these images into assets/approved or assets/applied until accepted.