# FEAT-018 main-flow hardening plan — 2026-09-28

## Status

Approved for implementation by the project owner in the current conversation. This is a bounded
client-flow reliability slice; it does not change backend contracts or provider behavior.

## Problem statement

The current Android demo has several reproducible breaks across its primary journey:

1. `runAiSimulation` acquires its request lock before validating text/audio narration. Its early
   validation returns skip the `finally` block, permanently preventing another understanding
   request until the app is restarted.
2. UI busy state alone is not a synchronous duplicate-request guard. Rapid taps can start multiple
   session commands before React rerenders, advancing the same session with different idempotency
   keys or creating duplicate sessions.
3. `beginWorkflow` does not clear the previous correction, re-query flag, selected source drawing,
   activity/checklist state and feedback values. Old data can leak into a new session; a stale
   correction can trigger an unintended extra Qwen re-query.
4. Audio duration is incremented in both `AppContext` and `VoiceScreen`; recording failures can
   leave the timer running, and the 3-minute stop side effect currently occurs inside a state updater.
5. The image picker labels every non-PNG file as JPEG, including formats the backend does not
   admit. Such uploads fail later with a confusing error.
6. Feedback sends Vietnamese presentation labels and stale demo defaults where `FeedbackV1`
   accepts only five fixed observation codes. The backend rejects unsupported tags. The free-text
   parent note is displayed as though it belongs to the feedback form, but the versioned contract
   explicitly rejects notes and the client never sends the field.
7. Dashboard shortcuts can open recommendation/feedback screens without the state those gated
   screens require, producing empty or unsavable dead ends.
8. Pixi renderer preparation is retriggered by an effect whose function dependency changes every
   render; after an API failure this can automatically retry indefinitely. The global error modal's
   “Thử lại” action only dismisses the modal and does not retry any operation.
9. On timeout/network loss, tapping the same API action again currently creates a new idempotency
   key (and `createSession` creates a new session ID), so an operation that succeeded before its
   response was lost can be applied again instead of replayed.

## Approved scope

- Add one synchronous single-flight guard for session-changing API operations, releasing it on every
  success, error and early-return path. Keep UI busy labels and existing backend idempotency/version
  contracts unchanged.
- Validate narration before acquiring the understanding lock and preserve retry after invalid input.
- Reset session-scoped media, corrections/re-query state, topic/claim state, renderer/activity state,
  checklists and feedback values only after a new session is successfully created.
- Make recording start/stop single-flight, use one duration clock, clear timers on every outcome,
  clamp at 180 seconds and avoid side effects inside React state updaters.
- Admit only explicitly identified JPEG/PNG picker assets and fail early with actionable copy for
  unsupported or ambiguous formats.
- Store feedback observations as `FeedbackV1` enum codes, render their Vietnamese labels in the UI,
  initialize the selection empty, and avoid sending any unsupported fields.
- Remove or replace the misleading free-text note input with a clear statement that free-text notes
  are not stored in this demo; do not expand the backend contract or accept personal notes.
- Keep dashboard entry points from dropping users into a gated live workflow without a valid session;
  retain the developer-only screen switch for deliberate testing.
- Attempt renderer preparation once automatically per screen entry, expose an explicit manual retry
  after failure, and make the shared error-modal action label match its dismiss-only behavior.
- Reuse the existing idempotency key and session ID only when retrying the identical command after
  an ambiguous transport/server outcome; clear the pending key after a definitive response or a
  changed command. Keep the versioned backend contract unchanged.
- Add deterministic regression checks for the guards, input validation, reset behavior, feedback
  mapping, and screen-entry requirements. Preserve the existing Pixi startup work and unrelated
  worktree changes.

## Out of scope

- Backend schema/contract changes, free-text note storage, durable persistence, auth, provider/model
  calls, Lightning configuration, real child data, video generation, Pixi animation redesign,
  unrelated assets/screens and commit/push.
- Changing the existing owner-run live Lightning acceptance boundary.

## Acceptance criteria

1. Invalid text/audio preflight returns without leaving any lock held; after correcting the input,
   exactly one understanding command can run.
2. Two same-tick calls to a mutating workflow method result in at most one API mutation; all error
   and success paths release the lock so a later retry succeeds.
3. Starting a new session removes the previous drawing/admission, narration, correction/re-query,
   claims/topics, activity recommendation/checklists, renderer launch and feedback values. It does
   not clear state when session creation fails.
4. The visible recording duration advances once per second, stops at 03:00, and no timer or recorder
   remains active after stop/start failure.
5. PNG/JPEG assets receive matching MIME and extension; HEIC/WebP/unknown/conflicting metadata is
   rejected before upload with a recoverable message.
6. Feedback payload contains only valid `FeedbackV1` observation codes; default tags are empty;
   unsupported free-text notes are not presented as saved feedback.
7. Normal dashboard actions cannot reach an activity recommendation or feedback action that is
   missing its required prior gate/session state; valid ordered flow remains unchanged.
8. Renderer preparation does not repeat after failure without an explicit user retry, and the shared
  error modal does not claim a dismiss action will retry.
9. Retrying the same command after timeout/network loss reuses its idempotency key; successful or
  definitive rejected outcomes do not reuse it for a later independent action.
10. Relevant UI typecheck, focused mobile regression tests, UI-copy/recovery validation, renderer
   tests and Android bundle/build checks pass. No live AI call is performed.

## Verification plan

- Run focused workflow helper tests and mobile UI-copy/recovery validation.
- Verify renderer preparation effect/manual retry and error-modal recovery copy with focused checks.
- Simulate a lost response followed by an explicit retry and verify idempotency replay identity.
- Run mobile TypeScript checking through the existing workspace TypeScript toolchain.
- Run art-renderer tests/typecheck/build to guard the existing Pixi integration.
- Run relevant backend feedback contract tests read-only to confirm the client payload matches the
  current `FeedbackV1` contract; do not modify backend behavior.
- Attempt Android build/start only if the already-configured local toolchain and emulator are
  available; report clearly if device acceptance remains unavailable.
- Do not run Lightning/Qwen/SAM or send real media.

## Evidence to record

Add a feature-local note under `features/FEAT-018-live-image-canvas-flow/evidence/notes/` with
changed behavior, commands/results, environment limitations and deferred contract risks. Do not
include source images, credentials, tokens, raw user data or shared runtime output.
