# Sketch2Life UI mockups — Rev35

**Lifecycle:** Generated visual drafts; not visually approved and not connected to product UI.

Each screen has a separate folder with `screen.png`, `PROMPT.md`, and `MOTION.md`. The Parent app uses portrait Android compositions. Teacher, School Manager, and Platform Admin use desktop web compositions.

| ID | Role | Screen | SRS/API mapping | API status | Files |
|---|---|---|---|---|---|
| P01 | Parent | Lesson library | `GET /api/lesson-library/v1/me/lessons` | Rev31 Lesson Library API | [PNG](parent/p01-lesson-library/screen.png) · [prompt](parent/p01-lesson-library/PROMPT.md) · [motion](parent/p01-lesson-library/MOTION.md) |
| P02 | Parent | Lesson detail | `GET /api/lesson-library/v1/me/lessons/{lesson_id}` | Rev31 Lesson Library API | [PNG](parent/p02-lesson-detail/screen.png) · [prompt](parent/p02-lesson-detail/PROMPT.md) · [motion](parent/p02-lesson-detail/MOTION.md) |
| P03 | Parent | Drawing with optional line-sketch guide | SRS §31.5, FR-PL-15, target `PARENT_SKETCH_GUIDE` | SRS target; no Parent Guide route is enumerated in the Rev31 API inventory | [PNG](parent/p03-drawing-line-guide/screen.png) · [prompt](parent/p03-drawing-line-guide/PROMPT.md) · [motion](parent/p03-drawing-line-guide/MOTION.md) |
| P04 | Parent | Capture and subject confirmation | SRS §21.5/§31.5; target `POST /v1/upload-sessions`, `/v1/story-runs/{id}/assets`, `/subject-confirmation` | SRS target flow; not part of Rev31 Lesson Library runtime API | [PNG](parent/p04-capture-subject-confirmation/screen.png) · [prompt](parent/p04-capture-subject-confirmation/PROMPT.md) · [motion](parent/p04-capture-subject-confirmation/MOTION.md) |
| P05 | Parent | Context and story review | SRS target `POST /v1/story-runs/{id}/idea`, `/context-confirmation`, `/script-confirmation` | SRS target flow; not part of Rev31 Lesson Library runtime API | [PNG](parent/p05-story-review/screen.png) · [prompt](parent/p05-story-review/PROMPT.md) · [motion](parent/p05-story-review/MOTION.md) |
| P06 | Parent | Video generation progress | SRS target `POST /v1/story-runs/{id}/video-generations`, `GET /v1/story-runs/{id}`, `GET /v1/jobs/{job_id}` | SRS target flow; broader video APIs are not implemented in Rev31 | [PNG](parent/p06-video-generation-progress/screen.png) · [prompt](parent/p06-video-generation-progress/PROMPT.md) · [motion](parent/p06-video-generation-progress/MOTION.md) |
| P07 | Parent | Private video and outdoor activities | SRS target `POST /v1/story-runs/{id}/playback-token`; activity data from authorized lesson detail | Video route is SRS target; lesson detail is Rev31 Lesson Library API | [PNG](parent/p07-video-and-activities/screen.png) · [prompt](parent/p07-video-and-activities/PROMPT.md) · [motion](parent/p07-video-and-activities/MOTION.md) |
| P08 | Parent | Lesson history and feedback | SRS §31.6, delivery/history/feedback resources | Required by SRS; routes are not in the Rev31 Lesson Library contract (Demo feedback is unrelated) | [PNG](parent/p08-history-feedback/screen.png) · [prompt](parent/p08-history-feedback/PROMPT.md) · [motion](parent/p08-history-feedback/MOTION.md) |
| T01 | Teacher | Organization lesson workspace | `GET /api/lesson-library/v1/organizations/{organization_id}/lessons` | Rev31 Lesson Library API | [PNG](teacher/t01-lesson-workspace/screen.png) · [prompt](teacher/t01-lesson-workspace/PROMPT.md) · [motion](teacher/t01-lesson-workspace/MOTION.md) |
| T02 | Teacher | Structured lesson authoring | `POST`/`PATCH /api/lesson-library/v1/organizations/{organization_id}/lessons`; Public request through `/access-grants` | Rev31 Lesson Library API | [PNG](teacher/t02-lesson-authoring/screen.png) · [prompt](teacher/t02-lesson-authoring/PROMPT.md) · [motion](teacher/t02-lesson-authoring/MOTION.md) |
| T03 | Teacher | Filtered document import and review | Upload sessions/parts/complete; `GET` source-document/revision; `POST .../versions` | Rev31 Lesson Library API | [PNG](teacher/t03-document-import-review/screen.png) · [prompt](teacher/t03-document-import-review/PROMPT.md) · [motion](teacher/t03-document-import-review/MOTION.md) |
| T04 | Teacher | Session with optional Sketch Deck | SRS §21 API target `/v1/lesson-occurrences/{id}/sketch-decks` | SRS target AI route; not in Rev31 runtime API | [PNG](teacher/t04-session-sketch-deck/screen.png) · [prompt](teacher/t04-session-sketch-deck/PROMPT.md) · [motion](teacher/t04-session-sketch-deck/MOTION.md) |
| M01 | School Manager | Public publication review | `GET /api/lesson-library/v1/organizations/{organization_id}/access-grants?state=PENDING_REVIEW`; `POST .../{access_grant_id}/decision` | Rev31 Lesson Library API | [PNG](school-manager/m01-publication-review/screen.png) · [prompt](school-manager/m01-publication-review/PROMPT.md) · [motion](school-manager/m01-publication-review/MOTION.md) |
| A01 | Platform Admin | Public catalog moderation | `PATCH /api/lesson-library/v1/platform/lessons/{lesson_id}/moderation` | Moderation action is in Rev31; Admin catalog list/search route is not enumerated by the Rev31 contract | [PNG](platform-admin/a01-content-moderation/screen.png) · [prompt](platform-admin/a01-content-moderation/PROMPT.md) · [motion](platform-admin/a01-content-moderation/MOTION.md) |

## Reading the motion notes

The images are still mockups. `MOTION.md` specifies suggested transitions and state feedback; none of those animations are implemented. Job indicators must follow backend stage/state responses, and role/visibility changes must appear only after the corresponding API command succeeds.

The rows marked “SRS target” are product-contract concepts, not claims that the route is mounted today. Current runtime status is cross-checked against the Rev31 API inventory and Rev32 purpose catalog. The catalog itself notes that LessonOccurrence history/feedback and the new Parent/Teacher AI/video flows were not implemented in Rev31.

Age labels/chips shown in the pictures are sample content for a 3–10-year-old product scope. The SRS keeps the age-band catalog/version open, so these exact ranges are not a product decision.

## Visual approval

Review the images and notes in this folder. Until approved, keep all files under `assets/generated/`; do not reference them from application source or copy them into `assets/approved/` or `assets/applied/`.
