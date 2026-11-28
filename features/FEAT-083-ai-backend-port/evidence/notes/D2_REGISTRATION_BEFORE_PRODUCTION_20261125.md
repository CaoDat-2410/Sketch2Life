# Parent registration completion — D2 evidence note

Date: 2026-11-25

## What was built

Added `POST /api/auth/v1/registrations/complete` for an adult identity that already has a verified Firebase token but has no matching BE1 identity row. The route uses the existing verified-adult dependency and derives the issuer and subject from its verified principal. It accepts no role, UID, or account-scope fields. A verified email and an issuer matching the configured Firebase project are required.

The backend creates an active Parent identity with a server-generated account ID and role revision 1. Repeating the request for the exact active Parent identity returns the same safe receipt shape: `role`, `state`, and `role_revision`. Other existing rows and non-matching uniqueness races receive the generic `ACCOUNT_SETUP_UNAVAILABLE` refusal. The route shares the existing registration rate limiter and uses the redacted registration database diagnostics.

No terms or consent record was invented. This completion flow is limited to the synthetic-only demo boundary in BR-27; it does not authorize real child data.

## Setting

The named setting is `parent_self_registration_enabled`, exposed as `SKETCH2LIFE_PARENT_SELF_REGISTRATION_ENABLED`. It defaults to `false` in backend settings, `.env.example`, and Compose. Settings validation rejects `true` unless the environment is `local` or `test`. The route returns the generic `ACCOUNT_SETUP_UNAVAILABLE` refusal while the setting is off.

## Verification

- New setting and completion API tests: 20 passed using fake sessions and a fake token verifier.
- Firebase token verifier tests: 2 passed.
- OpenAPI catalogue tests: 10 passed. The new route remains runtime-only.
- App composition tests: 14 passed.
- Existing registration API tests: 7 failed and 3 passed because the seven database-dependent cases require a database. This matches the known checkout limitation; that test module was not changed.

## Before production (owner tasks)

- Approve the terms and consent text and decide how adult consent is captured.
- Define account and profile deletion policy, retention, and the FR-C-10 executor.
- Identify the authoritative key source for support-needs notes.
- Define the role authorized to run data purges.
- Set and approve the real-names release gate.
- Resolve OD-13 push and e-mail provider choices and readiness.
- Review registration anti-abuse controls, including CAPTCHA and a business audit record.
- Formally sign off the canonical v2.7-draft SRS.
- Registration rate limit: the limiter is process-local, keyed on the client address and shared with the registration route; behind a proxy all users would share one bucket. A proxy-aware key and a shared store are required before any non-local enablement (review finding, hard blocker for production).
- Audit: identity creation by this route writes no business audit entry; add one (role assignment, BR-03/NFR-11) before production.
- Order of checks: the setting gate and the shared limiter run before token verification, so a disabled deployment never verifies tokens and unauthenticated floods are counted.
