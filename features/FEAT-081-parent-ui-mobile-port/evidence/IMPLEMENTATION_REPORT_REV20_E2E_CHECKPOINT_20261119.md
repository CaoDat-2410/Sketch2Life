# FEAT-081 Rev20 — implementation and Android E2E checkpoint

- **Status:** PARTIAL; the real Parent flow reaches drawing analysis, then is blocked by a terminal Qwen output error.
- **Date:** 2026-11-19 (Asia/Ho_Chi_Minh).
- **Branch/worktree:** `feature/fe-mobile-remediation`, FEAT-081 integration worktree.
- **Plan/authorization:** Plan Revision 20, Addendum 35. No commit or push was made.
- **Evidence ID:** `EV-081-REV20-E2E-01`.

## What ran

The Expo Android app ran with the visual-preview harness disabled against the local Docker backend and its disposable development services. A synthetic Parent account authenticated through Firebase Authentication; the backend created and returned a synthetic child profile. The tester used the live topic/object suggestion and validation flow, rendered the catalog SVG guide through six progressive steps, and selected the generated synthetic turtle drawing at `ANDROID_E2E_REV20_20261119/synthetic_turtle_drawing.png`.

The app created StoryRun `f9b29982-5472-4456-b2e8-2f44dc900382` and sent one real request to `POST /api/parent/v1/ai/drawing-understandings`. Modal call ID: `fc-01M7S077P6SMV7T3M01Y1A7FJJ`. Model: `Qwen/Qwen3.5-9B`, pinned revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`.

The request took about 76 seconds at the API boundary and returned HTTP 504 `MODAL_OUTCOME_UNKNOWN`. Modal logs show the worker itself had reached a terminal error: the constrained decoder generated 512/512 output tokens, and JSON parsing found an unterminated string at character 146 (`MODAL_MODEL_OUTPUT_INVALID`). Logged worker phases were model load 16.696 s, preprocessing 0.014 s, prompt encoding 0.231 s, and inference 30.937 s. No raw generated text, image, Firebase credential, or token is included in this report.

Because drawing analysis did not return a valid subject, the flow correctly did not invent one or continue to activity selection/story generation. No activity or story result was produced; no video request was made. The final UI capture remains on the pending/error recovery screen. This is a real failure-path capture, not a successful AI output.

## Changes made after diagnosing the worker failure

1. The drawing worker now takes EOS IDs from the model generation configuration and uses the same EOS set for constrained decoding, generation, and padding. EOS tokens are excluded from the ordinary LMFE vocabulary table; decoder text normalization follows the working language/story worker behavior.
2. The worker emits content-free diagnostics for token limits, EOS termination, parser state, JSON parse failure type/position, and generated length. When invalid JSON reaches the token cap without model EOS, it returns `MODAL_MODEL_OUTPUT_TRUNCATED` rather than a generic invalid-output code.
3. The backend Modal client classifies terminal drawing worker errors even when Modal surfaces them as `RuntimeError`, using structured worker logs. It no longer turns this known terminal failure into the generic unknown-outcome/504 classification. Story worker truncation/empty-output classifications were aligned as well.
4. Parent UI recovery maps the drawing error to a localized terminal-failure message and safe recovery state. No success result or fallback subject was fabricated.

These changes are **not confirmed against a fresh live inference**. The bounded live drawing call for this path has already been used; a new live call requires a separate bounded inference authorization. Offline tests cover the EOS wiring and error classification, but cannot prove the remote model now completes valid JSON.

## Verification results

| Check | Result |
|---|---|
| Parent Android real-app path | Passed through authentication, synthetic profile, topic/object suggestion and validation, SVG guide rendering, image selection, StoryRun creation; blocked at live drawing analysis as described above. |
| Backend focused tests in the local API container | 68 passed in 4.69 s after correcting a test fixture; exercised current Modal client source and focused tests. No live AI inference was part of this test run. |
| Modal worker contract tests | `python -m pytest deployment/modal/srs_v23/tests/test_qwen35_lesson_suggestion_contract.py -q --basetemp=.pytest-tmp-modal` — 29 passed. |
| Parent mobile tests | `pnpm --dir apps/ui-mobile test` — 8 files / 94 tests passed; `UI_COPY_AND_RECOVERY_VALID`. |
| Python compile check | Passed for the changed worker/client/test files. |
| Mobile typecheck | `pnpm --dir apps/ui-mobile typecheck` failed with 594 TypeScript diagnostics overall, including 247 in Parent source. The recorded failures are predominantly JSX/component typing mismatches (`Ionicons`, `LinearGradient`, React Native SVG types). This remains open. |
| API service | Rebuilt local API image, `/health` returned `ok`, and OpenAPI exposed 13 relevant Parent/StoryRun/AI routes. This confirms service startup and route registration, not successful completion of every route. |
| Evidence privacy scan | No email, Firebase API key pattern, or token pattern was found in retained XML/Markdown evidence text. Login/signup captures that visibly contained the synthetic email and a gallery-picker capture with unrelated images were removed. |

## Evidence index and provenance

See `ANDROID_E2E_REV20_20261119/README.md` for the screenshot index and hashes. It contains 34 retained Android screen captures plus the separately generated synthetic input artwork. The capture sequence is from the actual Expo app, not the visual-preview harness. The catalog SVG guide is a real catalog/render path; this run did not invoke FLUX or claim AI-generated SVG output.

Key captures:

- `11-after-register.png`, `14-profile-create.png`, `15-profile-created.png`, `17-profile-selected.png`: authenticated Parent and synthetic profile path.
- `20-topic-screen-after-backend-fix.png` through `25-subject-validation-result.png`: live topic/object suggestion and custom-subject validation screens.
- `28-svg-guide-result.png`, `30-svg-guide-stage-2.png`, `32-svg-guide-stage-3.png` through `35-svg-guide-stage-6.png`, `36-guide-approved.png`: progressive catalog SVG guide.
- `37-capture-screen.png`, `38-image-selected.png`: required artwork step and selected synthetic artwork.
- `40-drawing-analysis-result.png`, `41-run-status-poll.png`: real drawing request failure and pending/recovery state.

The synthetic artwork SHA-256 is `43596C821E6D80B3792F227F684B1C30DEA5D84653BB7D504C873F2F3B3F5A40`. The failure-screen SHA-256 values are recorded in the evidence README.

## Services and remaining work

- Stopped only the task-local Compose project `s2l-feat081-rev20` after the checks.
- Stopped Modal app `sketch2life-srs23-drawing-vlm-dev` and verified it had zero active tasks. The existing video app was left untouched; no video inference ran.
- The emulator was not explicitly stopped by this checkpoint.
- StoryRun `f9b29982-5472-4456-b2e8-2f44dc900382` may remain in `INPUT_PROCESSING` / `AWAITING_RECONCILIATION` after the request timeout. No direct database mutation was used to clean it up. The app did not expose a verified authenticated cancellation path during this run.
- Activity-selection persistence, story generation, lesson-pinned E2E, support screens, and video were not proven end-to-end by this run. Quota/payment remained untouched.
- No database migration was run against a shared or production database.
- No commit, push, staging, branch switch, or history rewrite occurred.

