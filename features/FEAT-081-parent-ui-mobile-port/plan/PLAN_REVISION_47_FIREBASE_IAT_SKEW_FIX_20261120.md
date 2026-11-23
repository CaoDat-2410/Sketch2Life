# FEAT-081 — Plan Revision 47: Firebase token clock-skew fix for Parent E2E

**Status:** Approved narrow amendment to Plan Revision 46 under the owner's active instruction to register and complete the real Parent flow.  
**Worktree:** branch `feature/fe-mobile-remediation`.  
**Product authority:** FEAT-063 SRS v2.7-draft / Rev71; unsigned. FR-C-01 requires Firebase Authentication ID-token verification and server-owned role resolution. This amendment changes only verifier tolerance, not product behavior or authorization policy.

## Evidence and diagnosis

- One synthetic Parent was registered through the real Expo UI; the backend returned HTTP 201. Do not repeat registration.
- Firebase Identity Toolkit accepted the same account credentials (HTTP 200); credentials and token material remain ephemeral and are not recorded.
- A freshly minted token had `iat` 11 seconds ahead of the API container clock. `/api/auth/v1/me` rejected it as `INVALID_TOKEN` while the verifier allowed only 10 seconds of clock skew.
- Reusing a freshly minted token after a 3-second delay reduced the measured skew to 7 seconds; `/api/auth/v1/me` returned HTTP 200. Host and API-container clocks matched. This isolates the failure to the hard-coded 10-second tolerance.

## Authorized implementation

1. Increase `FIREBASE_AUTH_CLOCK_SKEW_SECONDS` in `backend/src/sketch2life/infrastructure/identity/firebase_token_verifier.py` from 10 to 30 seconds.
2. Preserve signature verification, issuer/audience checks, expiration, revocation checks, account-role resolution, and all other auth gates unchanged.
3. Run the focused verifier/auth contract checks and repository security validator; rebuild/recreate only `s2l-feat081-rev23-api-1` from the active worktree.
4. Sign in again through the existing real Expo UI using the already-created synthetic account. Reuse Plan Revision 46's single account/profile/run allowance; do not register another account.
5. Continue Plan Revision 46's UI-only Parent workflow and bounded inference/video ceilings after authenticated role resolution succeeds.

## Acceptance and limits

- The same app login reaches `/api/auth/v1/me` successfully immediately after Firebase sign-in, and resolves the existing Parent role.
- No other source path, public API contract, env/secret, SRS, migration, account, profile, or run changes as part of this amendment.
- No token/password/email is written to logs or evidence. Record only sanitized timing, HTTP status, stable error code, and screenshot evidence.
- Plan Revision 46 limits remain: real Expo UI, synthetic-only data, no fixture response, no direct API/worker bypass for product flow, no quota read/mutation/payment/bypass, no duplicate inference, no retry of AI/video, no warm-up/deploy/app stop, no unrelated service shutdown, no commit or push.

## Verification

- Run the focused existing backend auth/verifier tests plus any added regression assertion limited to the 30-second boundary.
- Confirm `git diff --check` and `python tools/validate_repository_security.py` pass.
- Capture an emulator screenshot after successful login and continue from the real UI. If authentication still fails, stop before creating a profile or sending any inference and report sanitized diagnostics.
