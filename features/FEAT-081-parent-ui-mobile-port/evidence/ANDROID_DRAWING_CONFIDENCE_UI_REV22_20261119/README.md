# Rev22 — Parent Android drawing-confidence verification

**Result: PASS for one drawing-understanding request and the confidence UI.** This is a focused verification, not proof that the rest of the Parent workflow is complete.

## Run

- Date/time zone: 2026-11-19, Asia/Saigon.
- Surface: installed Expo Parent app on Android emulator `emulator-5554`, package `com.sketch2life.parentexpo.dev`; real task-local API in Docker. No preview harness and no mocked response.
- Account/profile: local synthetic Parent and newly created synthetic profile `SyntheticTurtleRev22`, age 60 months. The profile screen showed that simulated-data profiles do not require consent.
- Topic path: selected **Động vật**, chose the custom turtle subject through the app's topic flow, and skipped the optional sketch guide. The subject catalog/custom validator ran without a separate Modal AI call.
- Automation note: Android db input text rendered the typed turtle alias as ua%; the catalog validator folded it to the canonical turtle subject before continuing. This is a keyboard-automation artifact; the drawing request itself was submitted through the UI and the result screen showed the turtle candidate.
- Input: generated synthetic turtle illustration, suitable for young children, 13,850 bytes; SHA-256 `43596C821E6D80B3792F227F684B1C30DEA5D84653BB7D504C873F2F3B3F5A40`. No real child data.
- Exactly one `drawing.analyze` inference was sent from the UI. No retry. Stopped at the adult review screen; did not confirm the subject or proceed to activity/story/video/quota/payment.

## Outcome and timings

- Parent API: `POST /api/parent/v1/ai/drawing-understandings` → **HTTP 200**.
- Request ID: `4da09092-6dfe-426b-ad92-b73a02cd3528`.
- Modal Call ID: `fc-01M7SVM2RR3035ZYNXRGARQ89F`.
- Job / generation / attempt refs: `c78ab05c5a554d17` / `ad81f2f79a95cce2` / `916beed3a97c3c19`.
- UI tap: `19:13:18.839 +07:00`; backend-reported elapsed time: **45.785 s**. Scratch-image upload took **6.551 s**; Modal wait **43.979 s**.
- Worker terminal event: `worker_succeeded`, **30.301 s** total. Logged stages: model load **15.942 s**, constrained-decoder setup **3.239 s**, image-model inference **7.118 s**. Generated 91 tokens and ended with model EOS, below the 512-token limit.
- Model: `Qwen/Qwen3.5-9B`, revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`; worker configuration reports GPU choices `L40S|L4|A10` (the log does not establish which physical GPU served this call).
- UI displayed subject **“con rùa”**, confidence **95%**, four visible features, a warning that an adult must review, and the **“Xác nhận chủ thể”** action. Adult confirmation remains required; no confidence threshold auto-confirms the drawing.

## Log note

At response time, the API's short Modal-log tail reported `worker_started_without_terminal_event` because the terminal log had not appeared in its initial tail. Reading the same Modal Call ID later returned 25 sanitized structured events ending in `worker_succeeded` (30,301 ms). This was log-indexing/tail timing, not an inference failure. The sanitized event list is in `logs/modal-worker-events.json`; it contains no prompt, image, generated text, credentials, or raw child data.

## Checks and cleanup

- Focused drawing parser regression: **4 passed**, 2 Modal/asyncio deprecation warnings, using `.venv-modal`.
- Only the drawing Modal app was deployed for this run; it was stopped afterward. Task Compose project `s2l-feat081-rev20` was stopped without deleting persistent volumes. Task Metro was stopped, and the Parent app was force-stopped. The emulator itself was already running before this task and was left available.
- The synthetic profile and its drawing run remain in the local persistent database volume; no direct database mutation/deletion was performed.
- No activity/story/video or other Modal inference, no migration, commit, or push.

## Screenshots

- `screenshots/01-parent-login-result.png` — authenticated Parent home.
- `screenshots/05-profile-created.png` — synthetic profile.
- `screenshots/06-start-parent-session.png` — choose topic/lesson route.
- `screenshots/07-topic-selection.png` and `screenshots/09-subject-selection.png` — topic and animal-subject choices.
- `screenshots/11-optional-guide-skipped.png` — optional sketch guide left off.
- `screenshots/15-turtle-selected-before-submit.png` and `screenshots/16-turtle-photo-confirmed.png` — selected child-friendly input.
- `screenshots/17-drawing-understanding-review.png` — actual API/Modal result and adult review UI.
- `input/synthetic_turtle_drawing.png` — exact synthetic input.

