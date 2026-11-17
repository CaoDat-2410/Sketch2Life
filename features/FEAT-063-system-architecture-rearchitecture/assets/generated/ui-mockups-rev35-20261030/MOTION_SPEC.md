# Motion notes — Rev35

These are implementation suggestions for review, not behavior implemented by the images. Durations are starting values; honor system reduced-motion preferences. Never imply success, permission, job progress or a visibility change before the corresponding API state confirms it.

## P01 — Parent lesson library

- **Suggested:** search/filter chips respond on tap; apply server results with a brief crossfade (160–200 ms). Show skeleton cards only while the list API is loading; fade cards in with a small 30–40 ms stagger.
- **Trigger/state:** user submits a search or changes a filter; show loading only while the request is pending, then render accessible results or an empty state.
- **Reduced motion:** replace fades/stagger with immediate content replacement. No idle animation.

## P02 — Parent lesson detail

- **Suggested:** expandable drawing/activity sections open with a short height transition (180–220 ms); the script-direction switch animates its thumb (120–160 ms).
- **Trigger/state:** explicit tap; retain the selected switch state in the draft/session request and show server-confirmed state after save.
- **Reduced motion:** immediate expand/collapse and switch position. No illustration parallax is needed.

## P03 — Parent drawing with optional line-sketch guide

- **Required interaction feedback:** when the adult turns the optional guide on, reveal the separate guide panel with a gentle slide/fade (200–240 ms); advance the highlighted step only after the adult taps next/back. A subtle stroke reveal may illustrate the selected guide step (250–350 ms).
- **Guard:** never animate a line onto the child's paper. Do not auto-advance, block capture, or start generation when the guide is hidden.
- **Reduced motion:** show the chosen step immediately and keep the card stationary.

## P04 — Parent capture and subject confirmation

- **Suggested:** camera shutter feedback as a single low-brightness flash (80–120 ms); when recognition response arrives, crossfade the suggested label/card (160–200 ms).
- **Trigger/state:** show the subject proposal only after API response; adult confirmation/correction must be a deliberate command.
- **Reduced motion:** no flash; render the confirmed capture and result immediately.

## P05 — Parent context and story review

- **Suggested:** storyboard cards enter with a restrained left-to-right fade (40 ms stagger, 160 ms each); editing changes to a clear editor state without a page-wide transition.
- **Trigger/state:** load only the exact current revision; disable confirmation while a save/revision request is pending; show success only after API acceptance.
- **Reduced motion:** render all cards at once. Never auto-confirm or auto-play story scenes.

## P06 — Parent video-generation progress

- **Required state feedback:** update the highlighted named stage only when the job-status API returns that stage. A soft pulse may indicate the active step (1.6–2.0 s loop); no percentage/count-up animation or fake ETA.
- **Trigger/state:** transitions use discrete crossfade (160–200 ms) after a confirmed state update. Terminal failure, safety hold and ready states need distinct non-animated labels/actions.
- **Reduced motion:** disable pulse and crossfade; retain clear stage/status text.

## P07 — Parent private video and activities

- **Suggested:** show player controls on tap, then fade them after a short idle period (about 2 s); show the activity section after video reaches its actual completed/ready state, using a simple 180 ms reveal.
- **Trigger/state:** playback follows user action; activities are lesson data and should remain available after player completion. Do not autoplay or share.
- **Reduced motion:** controls appear instantly; activity list is present without reveal animation.

## P08 — Parent history and feedback

- **Suggested:** expand/collapse a lesson feedback thread in 180 ms; after a successful feedback API response, show a small checkmark/state label for 200 ms and clear the text input.
- **Trigger/state:** keep the draft on validation/network failure; append the feedback only after server acceptance. Do not simulate Teacher replies.
- **Reduced motion:** immediate thread change and a static sent state.

## T01 — Teacher lesson workspace

- **Suggested:** filter changes update a small loading indicator in the table header; preserve row positions where possible. Use a restrained 150–180 ms fade for updated result sets.
- **Trigger/state:** show status/visibility changes from server data only. Do not optimistically change a lesson from School to Public.
- **Reduced motion:** replace result rows immediately; no row stagger.

## T02 — Teacher structured lesson authoring

- **Suggested:** add/remove activity cards with a short 160–200 ms expand/collapse; validation appears inline after blur or save attempt; “Lưu bản nháp” feedback uses a static success notice.
- **Trigger/state:** repeatable fields remain ordered and validated. No autosave animation unless a future API explicitly supports autosave.
- **Reduced motion:** immediate field insertion/removal.

## T03 — Teacher filtered document import and review

- **Required state feedback:** upload progress may animate only from actual transferred bytes. Virus scan, parsing, field mapping and review use discrete server-confirmed status chips; do not show invented percentages for opaque steps.
- **Trigger/state:** reveal extracted fields only when extraction returns; show warnings inline. Confirmation has a short review dialog, and filtered fields become eligible for AI only after Teacher confirmation.
- **Reduced motion:** no progress shimmer; show current status text and determinate byte progress if available.

## T04 — Teacher session and optional Sketch Deck

- **Required interaction feedback:** toggle changes visually in 120–160 ms. Turning it on may start the Deck job and show queued/running only after API acknowledgment; turning it off before start means no job is enqueued. Preview navigation between ordered steps uses a 180–220 ms crossfade.
- **Guard:** no auto-advance during class; the Teacher controls the presentation. If an already-started job cannot be cancelled, label its true state instead of implying cancellation.
- **Reduced motion:** instant toggle/step switch; no animated line tracing is required for the actual classroom prompt.

## M01 — School Manager publication review

- **Suggested:** selecting a queue item updates the review panel with a 160–200 ms crossfade; approval/return opens a confirmation dialog. After the API decision, update the queue status and audit trail.
- **Guard:** no celebratory/confetti effect; never switch visibility to Public before approval success.
- **Reduced motion:** immediate panel replacement and static decision status.

## A01 — Platform Admin content moderation

- **Suggested:** hide/reopen action uses a confirmation dialog; after server success, update the row and append an audit event with a short 160 ms highlight.
- **Guard:** do not optimistically expose/unpublish content. Keep child-media access out of this surface unless a separately authorized, audited flow is designed.
- **Reduced motion:** static confirmation and status update without highlight.
