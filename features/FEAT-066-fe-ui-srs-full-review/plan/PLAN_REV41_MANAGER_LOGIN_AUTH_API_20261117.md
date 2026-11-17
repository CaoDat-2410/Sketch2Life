# FEAT-066 Plan Rev41 — School Manager login and auth API verification

- Status: APPROVED_FOR_IMPLEMENTATION for the exact scope below.
- Owner request: “ghép các api login trước cho tôi đi sau đó test và record lại kết quả cho tôi đi”.
- Scope: trace and verify the Manager login path only; repair a confirmed defect if found; add focused auth-flow coverage; exercise the local API/FE when the development stack is available; record sanitized results. Do not start the other 10 Manager APIs.
- Worktree/branch: `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`; `codex/fe-ui-web-remediation` at `b72f9e46` before this task.
- Source baseline: `origin/dev` at `1c9148e88600a101887e477541c4c4893ba1c7df`.
- Requirements: FEAT-063 SRS v2.7-draft Rev60 via `docs/context/SRS_AUTHORITY.md`, unsigned. Backend identity and organization assignment must both authorize Manager access.

## Observed current flow

The FE already calls Firebase `signInWithEmailAndPassword`, then `signInAndResolveRole` calls shared `GET /api/auth/v1/me` and checks role `school_manager`, then calls `GET /api/be1/v1/organizations/{organization_id}/me` and checks for an organization-wide `school_admin` assignment. Only after these checks does the shared login page mark the portal session and navigate to `/school`. Firebase sign-in is an SDK operation, not a backend `/login` route.

The Manager BE1 shell separately observes Firebase auth and checks the active organization assignment before rendering protected pages. Static source inspection found a service-level `authService.getAccountRole` helper that is not used by this flow; do not add a duplicate call unless test evidence shows the shared flow is incomplete.

## Acceptance criteria

1. A valid Manager login calls Firebase sign-in, then authenticated `GET /api/auth/v1/me`, then the configured organization's `GET /api/be1/v1/organizations/{organization_id}/me`; it opens the Manager portal only for `school_manager` plus a qualifying organization-wide `school_admin` assignment.
2. A wrong account role, missing/wrong organization assignment, expired/invalid token, or backend failure does not set the authenticated Manager session and does not leave Firebase signed in after a post-login authorization failure.
3. Focused automated coverage asserts call order, headers/token forwarding at the API boundary, correct navigation on success, and denial/sign-out on role or assignment failure. Do not add credentials, bearer tokens, or real user data to fixtures.
4. If the local development backend and Firebase dev configuration are available, perform a real authenticated read-only login/API smoke with the existing owner-authorized nonproduction QA account. Record only status codes, returned role/assignment shape, and redacted errors; never persist email/password/token.
5. Record all checks and limitations in FEAT-066 evidence. Do not claim a live API success when only mocks pass.

## Work sequence

1. Record the dirty worktree baseline and inspect existing auth/API contracts and available local services without printing secret values.
2. Record this exact scope and the owner's direct request in `approvals/TASK_APPROVAL.md` before source changes.
3. Run the current focused auth/Manager tests to establish their baseline; repair only confirmed test or login-flow defects.
4. Add or adjust focused tests for the accepted and denied Manager login paths; make the smallest necessary app change if evidence identifies a defect.
5. Run focused frontend tests and type/build checks. Attempt a real local API smoke only if the Docker/API service and nonproduction auth are available; preserve existing FE sessions and local files.
6. Record automated and runtime results separately in a new evidence note. Update FEAT-066 status/context/decision/plan/evidence indexes. Do not commit or push.

## Risks and limits

- Local Docker was not listening during initial inspection; a live API smoke may remain unavailable unless the user-authorized dev stack can be started safely.
- Firebase network/auth availability may prevent a real credential check. Mocks verify the FE contract only and must be labeled as such.
- Current product SRS calls the product role School Manager; BE organization assignment uses `school_admin`. Keep account-role and tenant-assignment checks distinct.
- No account bootstrap, password reset, role mutation, data mutation, backend contract change, other Manager API integration, or production access is in scope.

## Rev41 implementation finding — Manager runtime config mismatch

Before changing source, a focused test reproduced this defect: when only the repository's documented `VITE_BE1_BASE_URL` and `VITE_BE1_ORGANIZATION_ID` are configured, the shared login resolver does not read either variable. It reaches no configured organization assignment check and the Manager login remains on the login page. `runtimeConfig()` currently reads only `VITE_SKETCH2LIFE_API_BASE_URL` and `VITE_SKETCH2LIFE_ORGANIZATION_ID`; the root `.env.example` documents the BE1 names instead.

Approved minimal repair: preserve injected/generic config precedence, then fall back to `VITE_BE1_BASE_URL` and `VITE_BE1_ORGANIZATION_ID` in the shared API runtime config. Add an integration assertion that the auth and assignment requests use that base URL and organization, then rerun the focused tests/build/lint. No backend contract or login endpoint changes.
