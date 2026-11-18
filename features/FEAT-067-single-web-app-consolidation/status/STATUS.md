# FEAT-067 status

- **Status:** COMPLETE_WITH_LIMITATIONS.
- **Approved plan:** `plan/PLAN.md`; SHA-256 `0161673F9FD799B62E3CBA51D9AA2B9ACCDD4C3D8BFA574D7F4ACFEC483CF2ED`.
- **Approval:** recorded in this feature and the root task-approval register before implementation.
- **Scope delivered:** one `apps/web` entry/router with Teacher, School Manager preview, BE1-backed school-admin, Platform Admin, and shared UI modules; `/teacher/*`, `/school/*`, `/platform/*`, `/login`; root UI scripts and CI point to the consolidated app; superseded web app folders removed after migration review.
- **SRS baseline:** owner-supplied unsigned v2.7-draft Rev68; SHA-256 `69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944`.
- **Security boundary:** backend authorization is unchanged and remains authoritative. No mobile, API, DB, contracts, permissions, SRS, secret, or deployment changes.
- **Verification:** source mapping/import/package-lock/reference inventory and `git diff --check` are recorded in `evidence/notes/`; the full check has only two pre-existing FEAT-066 end-of-file whitespace findings. No automated tests/builds or browser walkthrough ran under the approved scope.
- **Limitations:** production host deep-link fallback and full dependency installation/build remain unverified; the offline npm lock regeneration was blocked by a missing cached optional Tailwind WASI package. Repository skeleton/harness validators remain invalid because they require the previously removed `apps/mobile` and unrelated FEAT-070 evidence scaffolding; no commit or push was made.


## Amendment 1 — commit authorization — 2026-11-16

- The owner's later direct request supersedes the original no-commit limitation for one local commit only.
- Amended plan hash: 9375A55AB5909D3D417F712832FC01B9720D9DD2714FC8108808D7B8D48561ED.
- The one commit may include the already delivered consolidation and related FEAT-066 Rev28 UI work after path/security review. No push, PR, merge, deployment, or technical-scope expansion.

## 2026-11-16 user-authorized closeout

- The approved consolidation is prepared for inclusion in the owner's requested single local commit with the related FEAT-066 web rebuild.
- `apps/web` build passed with separate lazy-loaded role chunks. Browser screenshots and UI route/API matrix are recorded under FEAT-066 EV-034.
- The app-folder removals captured in the initial dirty baseline were part of the user's preceding cleanup request; `apps/ui-mobile` and `apps/api` remain outside the web app.
- No application tests, production API, real child data, push, PR, merge, or deployment.
- Source mismatch remains open: this task's explicit Rev68 selection vs the repository authority pointer to Rev60.


### Final validation — 2026-11-16

Repository security and architecture checks pass; `git diff --check` exits 0. Harness and skeleton checks remain invalid for the intentionally removed mobile app package; harness also reports missing evidence directories in unrelated FEAT-070. Build passed and application tests were not run. The final route/API and responsive evidence is indexed from FEAT-066 EV-034.
