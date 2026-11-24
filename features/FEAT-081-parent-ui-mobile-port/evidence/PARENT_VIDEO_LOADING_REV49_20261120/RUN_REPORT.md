# Rev49 — Parent video loading UI and one-candidate attempt

**Date:** 2026-11-20 14:26 UTC  
**Branch:** `feature/fe-mobile-remediation`  
**Plan / approval:** Plan Revision 49; TASK_APPROVAL Addendum 79  
**Result:** Loading-state implementation and static checks passed. Real video inference was not dispatched because the Android app could not authenticate the existing synthetic Parent accounts.

## Changes

- Added `videoCandidateProgressFor`, mapping actual candidate states to four user-facing phases: prepare inputs, wait for processing, create motion, and validate/save preview.
- Updated the Parent video screen with a distinct initial status lookup, request-submission message, progress steps, 30-second status-poll explanation, and guidance not to resubmit an uncertain request.
- Failed and reconciliation states do not show a misleading progress track. Reconciliation explicitly says the result is unknown and the app will not resend automatically.
- Kept the current app palette and compact card components; progress has no invented percentage and does not expose Modal/GPU implementation details.

## Verification

| Check | Result |
|---|---|
| Mobile typecheck | PASS, exit 0 |
| Mobile tests | PASS, 133 tests across 16 files |
| UI copy/recovery validator | PASS (`UI_COPY_AND_RECOVERY_VALID`) |
| `git diff --check` | PASS |
| Task API health | HTTP 200 from `127.0.0.1:58100/health` |
| Video candidate runtime flag | `false` before and after this attempt |

## Emulator and Modal result

- The app restarted at Parent sign-in after the Metro bundle reload.
- Sign-in was attempted with the two pre-existing synthetic credential sets available from the earlier E2E session. The real app returned its generic invalid-email/password message for both sets. No account was created and no more authentication attempts were made, to avoid risking account lockout.
- Because no authenticated session was available, the exact approved StoryRun could not be opened or confirmed in the UI. No candidate request was sent; there is no candidate ID or Modal call ID, and no LTX inference was started.
- `SKETCH2LIFE_PARENT_VIDEO_DEV_CANDIDATE_ENABLED` remained `false`. No environment or secret was changed, no quota/billing state was read, and no Modal app was started, deployed, warmed, or stopped.

## Next unblock

Restore valid Parent sign-in for the already-created synthetic account in the Expo app, then resume only the approved StoryRun and one candidate request. Do not create a second account or issue another LTX request if the first request is accepted or its outcome becomes uncertain.
