# Plan Revision 62 — cold-resume saved story and video candidate

**Feature:** FEAT-081 Parent UI mobile port  
**Date:** 2026-11-22  
**Status:** APPROVED by the owner's direct 2026-11-22 instruction: “chạy fix đi”  
**Authority:** FEAT-063 canonical working SRS v2.7-draft, with FEAT-081 implementation records as evidence only.

## Goal

Fix the real Parent resume path so a fresh app session can reopen a server-confirmed story and its existing video candidate, then verify the Rev60 Play/Pause controls on Android without sending a new AI/video request.

## Evidence motivating this amendment

- The synthetic run `0af8455f…a40ea7` is `SCRIPT_REVIEW`; story revision 1 is `CONFIRMED`; its video candidate is `CANDIDATE_READY` with a persisted Modal call reference.
- One Android Activity-suggestion request returned HTTP 409 because the run had already advanced to `SCRIPT_REVIEW`; no Modal inference was dispatched.
- After a fresh login, resuming the open run returned the UI to Activity instead of the saved story. Source inspection indicates a new controller's local understanding revision `0` is treated as a server revision change, so `adoptServerStory` is skipped.
- Entering the video screen after a cold resume must read the existing candidate before exposing a path that could POST a new video request.
- Rev61 explicitly disallows product-code edits; this amendment requests that narrow additional scope.

## Proposed implementation

1. Treat empty client state as initial hydration, not a change that invalidates persisted server story state. Preserve stale-revision handling when an already loaded client run genuinely conflicts with the server.
2. On entering the video step for an authenticated run, GET the current video candidate before any generation POST can be offered. A ready candidate must populate the player without a new generation request.
3. Keep server ownership, story revision/hash validation, preview authentication, safety status, product-playable state, and all existing gates unchanged.

## Allowed files if approved

- `apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts`
- `apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx`
- `apps/ui-mobile/src/parent/presentation/navigation/useParentPlatformController.ts`
- `apps/ui-mobile/tests/parentFlowV1.test.ts`
- `features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md`
- `features/FEAT-081-parent-ui-mobile-port/status/STATUS.md`
- `features/FEAT-081-parent-ui-mobile-port/CONTEXT.md`
- `features/FEAT-081-parent-ui-mobile-port/evidence/PARENT_AI_VIDEO_PLAYBACK_REV62_20261122/**`
- This plan file.

No other files are in scope without a further amendment.

## Acceptance criteria

1. A cold Parent login followed by “Tiếp tục” for the existing run opens its server-confirmed story review; it does not route to Activity or POST a new activity suggestion.
2. Opening the video step GETs the current candidate and displays the existing ready preview; it does not POST a video-generation request.
3. The authenticated preview returns successfully on Android. Play advances elapsed time, Pause holds it, and Play resumes.
4. Record sanitized API status/timings, Modal task inventory, and Android screenshots. Verify no new Modal inference/video call, no database mutation, no quota/payment operation, and no gate bypass.
5. Run mobile typecheck and scoped UI verification. No commit or push.

## Limits

- Use only the existing synthetic Parent account, run, story, and ready candidate.
- No new account/run/profile, AI inference, video-generation request, new Modal deploy/warm-up, DB mutation, seed change, quota/payment call, or consent/safety/quality/ownership bypass.
- Preserve candidate safety status and `product_playable=false`; playback verification is technical preview only.
- Do not stop pre-existing Modal deployments. Stop only a Modal app started by this task; none are expected.
- If the existing run cannot be reopened or the player errors, stop and report; do not retry AI/video.
