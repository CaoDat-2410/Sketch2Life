# FEAT-081 — Plan Revision 48: recover Parent profile creation after DB error

**Status:** Approved narrow continuation of the owner's active request to complete the real Parent E2E.  
**Worktree:** branch `feature/fe-mobile-remediation`.  
**Product authority:** FEAT-063 SRS v2.7-draft / Rev71; unsigned. FR-C-01 and Parent profile APIs remain unchanged.

## Current evidence

- Firebase registration and Expo sign-in now succeed; `/api/auth/v1/me` returned 200 after the bounded token-clock-skew correction.
- The real UI sent one `POST /v1/parent/profiles`; it returned 503 `PARENT_STORE_UNAVAILABLE`. API log records `DataError`, but the underlying driver type and SQLSTATE are unavailable in the current sanitized log. Profile list was empty before the attempt.
- The form contains synthetic display name `E2E Profile R46`, age 60 months, and synthetic interests only. No inference was sent.

## Scope

1. Improve only the safe database failure log in `backend/src/sketch2life/interfaces/http/parent_runtime.py`, recording the underlying exception type/module and available SQLSTATE. Never log SQL text, bound values, profile text, email, UID, or tokens.
2. Inspect the exact runtime diagnosis and the task database schema read-only. Make at most one source correction in the Parent profile repository/runtime if the cause is localized; no business-data database edits and no schema migration unless a separately approved plan is added.
3. Rebuild/recreate only `s2l-feat081-rev23-api-1` and replay the same profile-create UI action at most once, using the client-retained idempotency key. First verify the profile list is still empty through the authenticated app; do not create a duplicate.
4. Continue Plan Revision 46 only after the profile is created and read back successfully. No AI/video call is authorized by this plan until then.

## Limits and acceptance

- The UI must create one synthetic profile and read it back as ACTIVE. If the same safe diagnostic still cannot identify a bounded repair, stop and report the exact sanitized type/module/SQLSTATE.
- Keep all Rev46 synthetic-only, no-quota, UI-only, no-secret, no-extra-account/run limits. No direct product API or worker bypass; no real child data; no consent fabrication; no inference retry; no Modal deploy/warm-up/stop; no unrelated service stop; no commit/push.
- Do not change the public API schema, product SRS, or consent/auth policy. Preserve all existing dirty worktree changes.
