# FEAT-036 plan revision 15 — Parent auth guard on hard refresh

- Revision: 15
- Status: APPROVED
- Prepared / approved: 2026-11-10
- Type: Parent local-preview auth and route-guard correction
- Product baseline: FEAT-063 SRS v2.7-draft from the main checkout; unsigned working baseline.
- Requirement boundary: presentation/runtime routing only. Parent Web target-client scope remains open in the SRS.

## Objective

When a Parent route is hard-refreshed without an authenticated session, send the user to Parent authentication. Keep a real authenticated session across refresh when the existing auth bridge can confirm it.

## Scope

1. Do not initialize Parent authentication from local-preview mode.
2. Start without an authenticated session. Local preview becomes active only after the user explicitly selects its preview action and remains in memory for that tab session.
3. On startup, check the existing auth bridge for an ID token and run the same Parent API access check used by sign-in. Hold protected-route decisions until both checks finish so a valid Parent session is not redirected before hydration.
4. Replace protected route navigation with /p11-authentication when there is no token, including direct URL loads and browser refreshes.
5. Keep sign-in, password recovery, and registration reachable while signed out.
6. Preserve Firebase configuration and existing auth bridge, backend authorization, and API token checks. Do not create a demo token or change backend behavior.

## Acceptance criteria

1. On localhost with no auth bridge/session, refreshing /p01-lesson-library lands on /p11-authentication.
2. Opening another protected Parent URL while signed out also lands on /p11-authentication.
3. The user can enter the local preview explicitly from sign-in. A hard refresh clears that in-memory preview session and returns the user to authentication.
4. If the auth bridge returns a token at startup, the existing Parent API access check used at sign-in must also succeed before a protected route remains open.
5. A missing token or token-check error resolves to the signed-out state; no protected screen or mock success is shown as authenticated.
6. Auth routes remain available while signed out. Firebase configuration, backend auth enforcement, and product SRS are unchanged.

## Out of scope

- Removing, replacing, or changing Firebase configuration or provider behavior.
- Persisting a local preview session across reloads.
- Changes to API/backend authorization, protected route policy, or other portals.
- Automated tests/builds, deployment, publishing, commit, or push.

## Verification approach

Manually review the local Parent routes with no backend/auth bridge and inspect the startup behavior for an active bridge session. Check source diff and route/module HTTP responses. Automated tests/builds are not part of this authorization.