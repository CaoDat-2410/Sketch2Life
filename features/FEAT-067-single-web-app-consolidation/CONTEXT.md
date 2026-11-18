# FEAT-067 — Single web application consolidation

## Goal

Make `apps/web` the only active web application and build entry for Teacher, School Manager, BE1-backed school-admin, and Platform Admin. Keep Parent Android and mobile UI outside this web app.

## Product authority

Use the owner-supplied SRS v2.7-draft Rev68 as the working task baseline (SHA-256 `69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944`); it remains unsigned. §§9.2–9.3 and 21.5 describe the proposed web surfaces but do not require separate web deployments. Route and UI boundaries are presentation structure only; backend role, permission, assignment, and resource checks remain authoritative. Do not alter the SRS authority records in this feature.

## Migration boundary

- `/teacher/*` contains the Teacher portal.
- `/school/*` contains the Firebase/BE1 organization-admin flow. `/school/preview/*` contains M01/M02 fixture preview screens and remains visibly non-persistent.
- `/platform/*` contains Platform Admin and its Content Admin permission surface.
- `/login` is the role entry page. Teacher/preview/platform auth behavior remains the copied backend/local-preview behavior; BE1 school-admin continues to verify its current organization-level `school_admin` assignment.
- `apps/api`, `apps/ui-mobile`, mobile source, backend contracts, and authorization implementation are outside scope.

## Preservation and status

The original worktree carried dirty FEAT-066 source/assets and user-requested folder removals. The migrated source came from the working tree before changes; no Git checkout/reset/stash was used. The original FEAT-066 working tree was left intact while copying; only its older superseded web app folders were removed after static copy/import/reference review.

## 2026-11-16 closeout

The user later authorized one local commit that includes this consolidation and related FEAT-066 Rev28 UI work. The unified app, root web scripts, CI entry and role ownership are implemented and reviewed; see FEAT-066 EV-034 for the SRS/API route matrix and responsive screenshots. The owner's task-selected unsigned Rev68 remains distinct from the repository source register's unsigned Rev60; this mismatch is recorded and neither authority file was edited. Repository validator outcomes are added after the required pre-commit run. No push or deployment is authorized.
