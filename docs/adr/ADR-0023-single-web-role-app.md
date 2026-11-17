# ADR-0023: One web app with role-scoped portal modules

- **Status:** Accepted for FEAT-067 migration; app-local package baseline only.
- **Date:** 2026-11-16.
- **Authority:** owner-supplied unsigned SRS v2.7-draft Rev68. This ADR does not sign off or edit the SRS.

## Context

The worktree contains separate Teacher, School Manager preview, Platform Admin, BE1-backed school-admin, and shared web source. The current SRS defines Teacher, School Manager, and Platform Admin/content-permission web surfaces (§21.5), while its proposed web structure (§9.2) does not mandate separate frontend deployments. Parent remains Android. The existing web sources have different package generations and styles, and the worktree contains dirty FEAT-066 changes that must be preserved.

## Decision

1. Use one `apps/web` package, Vite HTML entry, and browser router.
2. Namespace routes under `/teacher/*`, `/school/*`, and `/platform/*`; use `/login` for the role entry.
3. Keep School Manager M01/M02 preview at `/school/preview/*`, separate from the Firebase/BE1 organization-admin flow at `/school/*`.
4. Keep each portal's provider, preview semantics, and service boundary distinct. Route and frontend role state are not authorization. Backend principal, role, permission, assignment, and resource checks remain authoritative.
5. Scope migrated CSS to the active portal marker so standalone themes do not cascade across the unified document.
6. Use React 19.2.8, React Router 7.18.4, Vite 8.3, TypeScript 6.0.2, Tailwind 4.3, and Firebase 13 as a migration-compatible app-local baseline. Keep the project-wide final frontend stack open under ADR-0003 until the existing project questions are answered and recorded.

## Consequences

- A single web package/lockfile and one CI UI job own the active web portals.
- Deep links depend on the hosting layer serving the SPA entry document for role paths. Deployment configuration is not part of FEAT-067 and remains to be verified when a host is selected.
- School Manager preview remains fixture-only and non-persistent. Only current BE1 class list/create capability is represented as API-backed in this migrated admin UI; unsupported actions remain unavailable.
- Existing teacher/platform login backend behavior and local-preview mode are preserved; BE1 school-admin retains Firebase login and assignment verification.
- The package baseline is not a permanent stack decision and does not change the product SRS or backend architecture.

## Alternatives considered

- Separate deployments for each role: not required by the working SRS and retains duplicated application/configuration boundaries.
- Merge preview and BE1 functionality into one state/auth flow: rejected because it would blur fixture state and verified backend state.
