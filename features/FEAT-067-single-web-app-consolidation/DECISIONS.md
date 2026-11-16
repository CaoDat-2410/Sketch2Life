# FEAT-067 decisions

## D-001 — One web application with role-scoped modules

- **Status:** Accepted for this migration.
- One `apps/web` package, Vite entry, and `BrowserRouter` owns the web role areas. Route prefixes are `/teacher/*`, `/school/*`, `/platform/*`, with `/login` as the entry.
- Route namespaces and client UI state never grant authorization. Protected BE1/API requests remain subject to server-side principal, role, permission, assignment, and resource checks.
- Parent remains Android.

## D-002 — School Manager preview and BE1 admin remain distinct capabilities

- **Status:** Accepted for this migration.
- Keep M01/M02 under `/school/preview/*`, clearly marked as fixture-only and non-persistent.
- Keep the BE1-backed organization-admin flow under `/school/*`, preserving Firebase login, current `school_admin` assignment verification, class list/create API behavior, and explicit unavailable states for unsupported capabilities.
- Do not merge their auth state or present preview writes as server persistence.

## D-003 — App-local migration pin does not settle the final product stack

- **Status:** Accepted for this migration only.
- `apps/web` uses the compatible package baseline recorded in ADR-0023 (React 19, React Router 7, Vite 8, TypeScript 6, Tailwind 4, Firebase 13).
- This app-local migration pin does not amend ADR-0003, settle the project-wide frontend stack, or change the unsigned SRS.

## D-004 — Portal CSS is scoped by the active route marker

- **Status:** Implemented.
- The unified router sets `html[data-portal]`; migrated CSS selectors are prefixed by the relevant portal so the previous standalone roots do not leak theme/layout declarations into other role areas.
- The BE1 Tailwind preflight remains its shared base reset; BE1 component styles are scoped to its portal wrapper.
