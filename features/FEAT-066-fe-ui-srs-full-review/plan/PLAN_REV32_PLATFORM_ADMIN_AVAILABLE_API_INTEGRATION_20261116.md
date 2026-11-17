# software — Platform Admin configured health API integration

- Feature: FEAT-066 — Web SRS full review
- Plan revision: 32
- Status: APPROVED_FOR_IMPLEMENTATION
- Date: 2026-11-16
- Scope: Platform Admin API wiring only

## Owner request and objective

The owner directly approved: “ok ghép mấy cái trên cho tôi đi”. Connect the safe Platform Admin APIs identified in the preceding review to the web UI, without inventing backend capabilities.

The identity and account APIs are already connected. The actual remaining safe wiring is the Platform Admin overview health card, which currently suppresses GET /health unless the configured API URL is loopback. Change it to call GET /health against the configured API base after entry through the authenticated Platform Admin shell, with clear loading, response, error and retry feedback.

## Baselines

- Product authority: FEAT-063 v2.7-draft Rev60, SHA-256 70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B; unsigned. Use docs/context/SRS_AUTHORITY.md.
- API baseline: origin/dev 1c9148e88600a101887e477541c4c4893ba1c7df.
- Frontend baseline: codex/fe-ui-web-remediation b72f9e46f9c63e019807d7c4a2c309b0aa46a133.
- Design context: current authenticated Platform Admin shell and shared status styles.

## Exact scope

1. Update apps/web/src/modules/platform-admin/pages/AdminScreens.tsx:
   - Remove the loopback-host restriction from the existing Health panel.
   - Use the existing backendApi.health() call, which resolves its URL from the configured API base.
   - Keep the Platform Admin route behind the existing authenticated/role-checked shell.
   - Retain pending, success, unavailable-auth and error states, plus a retry control.
   - Change text and accessible retry name from “local health” to the configured API health check.
   - Label the result narrowly as an API health probe. Do not claim that queue, billing, database, inference provider or all platform subsystems are healthy.
   - Do not display the configured API hostname.
2. Verify and preserve the existing shared role lookup and account API integration:
   - GET /api/auth/v1/me.
   - GET /api/platform-admin/v1/accounts.
   - POST /api/platform-admin/v1/accounts.
   - PATCH /api/platform-admin/v1/accounts/{account_id}.
   These are already wired by the login adapter, UsersPage and userService; do not duplicate them or change their mutation semantics in this revision.
3. Keep lesson moderation unavailable. The available moderation PATCH command has no queue/detail read API and the backend does not resolve the SRS Content Admin capability. Do not call it from a new UI action.
4. Keep queue/jobs, lifecycle, audit, billing/quota, organization directory, feedback, inbox, settings and activity catalog unavailable where their scoped APIs are absent or not mounted.

## Acceptance criteria

- AC1: An authenticated Platform Admin overview sends GET /health to the API base resolved by the existing runtime configuration, whether that base is loopback or a configured remote endpoint.
- AC2: Without the Firebase auth bridge, show a truthful blocked state and do not issue the health request. A configured API failure appears as an error with a retry action; a successful response shows only the returned service name and a narrow health-probe explanation.
- AC3: The page never claims that a successful GET /health proves queue, billing, database, provider or whole-platform health. It does not display the API hostname.
- AC4: Existing role discovery and account list/create/update flows remain unchanged and continue using their existing typed API methods.
- AC5: Moderation and all other API-unavailable panels remain unavailable; no role-only bypass of the Content Admin permission is introduced.
- AC6: No backend, auth, authorization, API contract, environment, secret, generated asset, mobile or other role code changes.
- AC7: Only the scoped frontend file and FEAT-066 plan/evidence/context/decision/status records plus the required approval record are changed.
- AC8: Run git diff --check. Do not run application tests/builds, live API calls, commit or push in this task.

## Implementation method

Apply the relevant UI/UX and frontend guidance: keep existing design tokens and component structure, use clear service states and semantic status/alert roles, retain keyboard-accessible retry, and avoid presenting one probe as an operations dashboard. Keep the change small and use the existing typed API client. Record the owner request as the implementation approval before the source edit.

## Risks and boundaries

- The SRS remains an unsigned draft. Q-13 role/permission persistence and OI-17 visual sign-off remain open.
- GET /health is explicitly a health probe; it cannot replace the missing operational read APIs.
- The browser may be unable to reach the configured API because of CORS/network/environment configuration. Display that as a connection error; do not fall back to mock data or a different host.
- Account APIs are included as existing integration evidence, not newly implemented behavior. Their account-create and role/state mutations retain their current semantics.
- This plan authorizes only the scope above. No moderation, content catalog, billing, audit, queue, lifecycle or deployment work is approved.
