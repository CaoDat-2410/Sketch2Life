# FEAT-066 EV-049 — School Manager login API verification (Rev41)

- Date: 2026-11-17.
- Plan: `features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_REV41_MANAGER_LOGIN_AUTH_API_20261117.md` (SHA-256 `E06D84FCEE12A168765876C892B3D9DD170D64FB81F804D0E551CD5F9EBE672B`).
- Approval: FEAT-066 Rev41 in `approvals/TASK_APPROVAL.md`; scoped to Manager login/API verification, tests, and evidence.
- Worktree: `codex/fe-ui-web-remediation`, baseline `b72f9e46`; unrelated existing changes preserved.

## Integration finding

The Manager login API chain was already wired in the application. `PortalEntryPage` calls `signInAndResolveRole("school_manager", ...)`, which signs in through the Firebase SDK bridge, fetches an ID token, calls shared `GET /api/auth/v1/me`, checks the returned account role, then calls `GET /api/be1/v1/organizations/{organization_id}/me` and requires a `school_admin` assignment. The shared portal session is set and navigation continues only after these checks. The protected Manager shell performs an additional organization-wide assignment check (`class_id === null`).

A pre-change test reproduced a real configuration defect: the shared API runtime read only `VITE_SKETCH2LIFE_API_BASE_URL` and `VITE_SKETCH2LIFE_ORGANIZATION_ID`, while the repository's `.env.example` documents `VITE_BE1_BASE_URL` and `VITE_BE1_ORGANIZATION_ID`. With only the documented BE1 variables, the organization assignment request could not be configured. `apps/web/src/shared/backendApi.tsx` now resolves configuration in this order: injected runtime config, generic Sketch2Life environment variables, then the documented BE1 environment variables. The resolver lives in `apps/web/src/shared/backendRuntimeConfig.ts` and is covered directly.

## Test changes and results

- Added `apps/web/src/shared/backendRuntimeConfig.ts` and `apps/web/src/app/__tests__/PortalEntryPage.auth.test.tsx`. Coverage includes the documented BE1 environment-variable fallback, successful Manager login/navigation and bearer headers, wrong account role, missing Manager organization assignment, and auth API 401.
- Corrected `apps/web/src/modules/school-manager/be1/__tests__/app.test.tsx`: it previously rendered the standalone Manager module at `/school/login`, which caused a redirect loop; it now tests the Manager organization gate and provides the required portal-session context.
- Focused tests: **2 files passed, 8 tests passed** using `npm run test -- --pool=threads --maxWorkers=1 --fileParallelism=false src/app/__tests__/PortalEntryPage.auth.test.tsx src/modules/school-manager/be1/__tests__/app.test.tsx`.
- `npm run build`: passed (`tsc -b` and Vite production build).
- `npm run lint`: exited 0. Oxlint reported existing project warnings for React effect updates, hook dependencies, and fast-refresh exports; no lint errors.

## Live API smoke

The existing local Docker PostgreSQL and API containers were restarted; both reported healthy. Read-only probes returned:

- `GET /health` → `200`.
- Unauthenticated `GET /api/auth/v1/me` → `401`, code `AUTHENTICATION_REQUIRED`.
- Unauthenticated `GET /api/be1/v1/organizations/scope-probe-only/me` → `401`.
- `http://127.0.0.1:5173` → connection refused during final check; no FE dev server was active for a browser-level live login smoke.

No Manager credentials were available in this task, so a successful authenticated Firebase/API login was **not** verified against the live backend. The positive login path above is verified by the FE integration test using mocked Firebase/backend responses. No account was created, password or role changed, credentials/token stored, or data mutation performed.

## Limits

No backend/API contract, account, or authorization data changed. The shared FE runtime config fix and focused tests are local worktree changes only. The local API and PostgreSQL containers remain running on their existing local ports for the owner's FE testing. No commit or push.
