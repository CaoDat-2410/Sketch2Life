# FEAT-081 — Plan Revision 46: fresh Parent account and full video E2E

**Status:** APPROVED by the owner's direct 2026-11-20 instruction to register and continue.  
**Worktree:** `<local-machine-path>, branch `feature/fe-mobile-remediation`.  
**Product authority:** FEAT-063 canonical working SRS v2.7-draft / Rev67; unsigned.  
**Prior run:** Rev45 activity/story stages succeeded, but the Expo process was restarted during bundle diagnosis. The confirmed StoryRun belongs to the previous Firebase UID and cannot be resumed by a newly registered account.

## Goal

Complete one real Android Parent → backend → Modal run through a private silent LTX candidate and playback, using a newly registered synthetic Parent because the prior account session is unavailable. The user explicitly instructed the agent to register and proceed.

## Approved scope

1. Register exactly one uniquely named synthetic Parent through the real Expo sign-up flow so the app/backend/Firebase registration path runs normally. Keep generated credentials ephemeral and never print or commit them. The Firebase account is a persistent external test record; do not delete it as part of this run.
2. Create exactly one synthetic profile (60 months) and one new StoryRun through the UI. Do not fabricate legal consent or use real child data.
3. Reuse the existing generated synthetic turtle artwork from `evidence/PARENT_VIDEO_CANDIDATE_E2E_REV43_20261120/input/synthetic-sea-turtle-drawing-rev43.png`, selected through the Android photo picker. It is test input, not a fixture response.
4. Send at most one real inference at each remaining stage: drawing understanding, activity suggestion, story generation. Select and persist one returned activity in the UI; inspect the exact story and confirm only if it matches the drawing/activity and passes adult review.
5. After the new story is confirmed, submit at most one silent LTX-2.5 candidate request through the authenticated UI and the existing local/test synthetic-only candidate guard. If ready, open its authenticated private preview in the UI.

## Limits

- No quota or billing reads/mutations, payment action, quota bypass, or product `VIDEO_READY` claim. Only the existing local/test + `modal_dev` + synthetic candidate guard may admit the technical candidate.
- No direct API/worker call to bypass UI, no business-data DB inserts/updates, no fixture/provider response, no real child data, and no consent fabrication.
- No retries, duplicate inference, second account/profile/run, drawing re-inference, video retry, scene retry, model warm-up, or additional Modal deployment. If any stage fails or the story is unsuitable, stop downstream calls and record diagnostics.
- Do not modify `.env`, secrets, migration state, SRS, or unrelated Modal apps. Do not stop user/unrelated services. No commit/push.

## Acceptance

- The account is registered by the real UI and backend; the synthetic profile and new run are owned by that account.
- The UI completes drawing review, activity selection, story review/confirmation, video candidate status, and authenticated private preview, or records the exact bounded failure without retry.
- Correlate API request IDs, Modal call IDs, durations, candidate state, and sanitized screenshots. Confirm no quota table was read or changed.

## Evidence

Append sanitized evidence to `evidence/PARENT_VIDEO_CANDIDATE_E2E_REV43_20261120/` and update FEAT-081 `CONTEXT.md` and `status/STATUS.md`.
