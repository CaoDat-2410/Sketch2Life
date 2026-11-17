# EV-063-75 — Teacher Sketch Deck presentation UI

**Date:** 2026-11-10
**Status:** Teacher presentation slice PASS; overall Parent/Teacher E2E remains PARTIAL.
**Plan:** `plan/PLAN_REV65_TEACHER_PRESENTATION_UI_20261110.md` (approved SHA-256 `FA7878EBC92E657B797FCD9A47BF4EA04610E18279351FBF516B52EFF134989C`).
**Authority:** FEAT-063 SRS v2.7-draft, Rev60 working copy (unsigned), §§6.2.1, FR-T-19, UC-17, BR-43 and NFR-33.

## Changes

- Replaced the raw JSON response in Teacher Web with a schema-checked presentation viewer for the existing `sketch2life.teacher-sketch-deck.v1` DRAFT.
- Added a white 16:9 slide canvas for orientation, drawing guide, subject exploration and approved activity slides, with slide selection, previous/next, drawing-step selection/skip, Escape close and arrow-key navigation.
- The drawing-guide slide shows the actual FLUX composite image from the existing lesson-visual API. The image is one 768×432 sequence image, not separate per-slide assets.
- Activity columns now scroll independently inside the 16:9 canvas so longer instructions and safety notes remain reachable. Display parsing handles line-separated and numbered text without changing the API response or persisting edits.
- The deck remains a DRAFT requiring Teacher review. No video, publication, persistence or backend contract change was made.

## Live Teacher UI-to-Modal result

Used the isolated headless Edge profile at `http://localhost:5174`, the local backend at port 8002, one disposable PostgreSQL database and a synthetic Firebase Teacher identity. The Teacher logged in through the UI and reached the authenticated authoring route. A text-only synthetic lesson was entered and reviewed in the UI. The teacher corrected the outdoor activity supervision/safety instructions before confirming review and requesting the deck.

| UI operation | Result | Request ID | Modal call / model | Backend duration |
|---|---|---|---|---:|
| Qwen lesson/activity suggestion | PASS; draft displayed for Teacher review | `7b557d10-a49a-4caf-a893-f98042ecdef6` | `fc-01M71NDRAV9YEQHQCGVQMRSMQZ`; `Qwen/Qwen3.5-9B`, revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a` | 102.265 s |
| Qwen Sketch Deck | PASS; 4-slide DRAFT accepted and shown in UI | `636563b4-63df-4bd0-a918-c63a16fb7cf0` | `fc-01M71NJVP394D8RHE83VCX6QSD`; `Qwen/Qwen3.5-9B`, same revision | 49.750 s |
| FLUX lesson visual | PASS; image rendered on drawing-guide slide | `4820b564-76e6-4258-b71b-154dbd0c408e` | `fc-01M71NME0WYEPFSHBKYBZDKB3J`; `black-forest-labs/flux-3-image-klein`, revision `09561231f44e41381c461caf53d5452005a60ac9` | 74.280 s |

The presentation showed all four returned slides. On slide 2, the actual FLUX image loaded at 768×432. Selecting a slide, arrow-key navigation, and advancing the drawing guide with “Bỏ qua bước” worked. The activity slide exposed all seven instructions and the safety note by scrolling its right-hand column.

### Worker log observation

The successful UI requests returned their results, and the backend logs recorded the model/revision and phase timings. The worker summary for the lesson suggestion and lesson visual reported `worker_started_without_terminal_event` with `worker_terminal_event=None`; terminal duration/output hash were absent even though the API response and visible UI result succeeded. This is a worker-observability gap, not a failed UI request. Preserve it as a separate follow-up; do not claim complete terminal worker telemetry.

## Supporting verification

- `npm run build` in `apps/teacher-ui` passed after the presentation and activity-content fixes. Vite retains an existing warning that the minified JS chunk is about 695 kB, above its 500 kB advisory threshold.
- No fixture response or direct API-only call was counted as the UI result. No video request was made.
- Screenshots in `EV-063-75_TEACHER_PRESENTATION_UI_20261110/screenshots/`:
  - `teacher-ai-lesson-draft.png`
  - `teacher-reviewed-plan.png`
  - `teacher-sketch-deck-generated.png`
  - `teacher-presentation-slide-1.png`
  - `teacher-presentation-slide-2.png`
  - `teacher-presentation-slide-4.png`
  - `teacher-presentation-slide-4-scrolled.png`

## Parent flow boundary

The Parent Android workflow was not executed in this follow-up. The test environment has no `adb` on PATH, no Android SDK/platform-tools at the checked Android SDK paths, and no emulator process. The approved drawing-worker output cap is now 512 and the updated drawing app was deployed then stopped, but the Parent Qwen drawing-understanding recovery was not sent through Android UI. The previous 256-token `MODAL_MODEL_OUTPUT_INVALID` remains the last live Parent analysis result; Parent story remains unverified. This report does not convert that earlier failure to PASS.

Teacher lesson-file upload/parser review also remains untested. The tested Teacher authoring path used structured text fields.

## Cleanup

- Modal drawing-VLM, language-audio and FLUX apps: STOPPED, 0 tasks.
- Synthetic Teacher Firebase identity: deleted.
- Disposable `rev64_e2e` database: dropped and verified absent.
- Task-started PostgreSQL and Redis containers, local backend, Teacher Vite server and isolated headless browser: stopped.
- Pre-existing API and ClamAV containers were preserved.
- No commit or push.
