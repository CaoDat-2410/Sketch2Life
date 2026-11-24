# FEAT-081 — Plan Revision 32: recover synthetic Parent authentication for the real E2E

- **Status:** APPROVED under the owner's active 2026-11-20 instruction to keep fixing and run the Parent flow until it works.
- **Feature/worktree:** FEAT-081, `feature/fe-mobile-remediation`, `<local-machine-path>
- **Authority:** FEAT-063 canonical working SRS v2.7-draft through local amendments; unsigned.
- **Relationship:** narrowly supersedes only the no-extra-account condition in Revision 30/Addendum 53 for one synthetic Parent account, because the emulator returned to auth and the transient login values were rejected. Revision 31 drawing deployment and Revision 25 workload limits remain active.

## 1. Authorized recovery

1. Create exactly one new synthetic Parent account through the real Expo signup UI, with a newly generated unique test email and password held only transiently in the current shell/UI. Never print, screenshot, write, or otherwise persist those credentials.
2. Create one synthetic profile through the same UI only after signup succeeds. Use the existing synthetic drawing and current approved topic flow. Do not create another account or profile if this attempt fails.
3. Continue through the existing real Parent workflow. The drawing Modal deployment is already authorized by Revision 31; submit at most one actual drawing inference for this fresh run. Continue activity/story/video only within Revision 25 caps and only after all preceding gates pass.

## 1.1 Auth token verification diagnostic amendment (2026-11-20)

- Evidence: the single signup request reached the local backend and returned HTTP 201. The mobile then called `/api/auth/v1/me`, which returned 401 after Firebase Admin logged `InvalidIdTokenError`. Root `.env`, the resolved Expo public Firebase project/key values, the backend project setting, and the project ID embedded in the configured Admin credential were compared without exposing key material; the project IDs and resolved public config matched.
- Authorized next step: add narrowly scoped Firebase-token diagnostics that decode claims only for comparison and log booleans for JWT structure, audience/project match, issuer/project match, subject presence, and expiration. Never log claim values, token segments, email, UID, or provider error messages. Add focused contract coverage, rebuild only the task-local API container, and use the already-created Parent account through the Expo sign-in UI once to observe the diagnostic.
- The existing account was created by the authorized signup and must be reused. This amendment authorizes no signup retry, account enumeration/reset/deletion, credential persistence, project/key/secret edit, direct DB change, or additional AI inference. If sign-in still fails, use the sanitized diagnostic to fix only the demonstrated cause before proceeding.

## 2. Boundaries

- Do not enumerate, look up, reset, delete, or transfer the prior account/profile. Do not use backend/admin account creation, direct DB writes, fixtures/mocks, real child data, quota/payment changes, `.env` or secret edits, or migrations.
- Do not restart Expo or use Android system Back during the authenticated workflow; use visible in-app navigation only.
- If signup or profile creation fails, capture the sanitized error and stop. No further account/profile attempt.
- Preserve all existing inference limits, safety checks, evidence location, cleanup rules, and no-commit/no-push boundary.
