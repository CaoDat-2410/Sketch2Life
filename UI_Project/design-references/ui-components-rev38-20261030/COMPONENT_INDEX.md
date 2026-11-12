# Sketch2Life component boards — Rev38

Nine generated component/state boards for review. They are static visual proposals, not approved production components.

| ID | Component group | Board | Current API boundary |
|---|---|---|---|
| UI01 | Foundations and controls | [board](ui01-foundations-controls/components.png) | Visual-only; no API. |
| UI02 | Parent dialogs and sheets | [board](ui02-parent-dialogs-sheets/components.png) | Script, subject and video-request dialog states are SRS target; no matching mounted Story API. |
| UI03 | Web decision dialogs | [board](ui03-web-decision-dialogs/components.png) | Manager access-grant decision, lesson archive and Admin moderation map to mounted Lesson Library operations. |
| UI04 | Toasts and inline notices | [board](ui04-feedback-toasts/components.png) | Generic presentation only; actual state comes from the owning API. |
| UI05 | Loading, empty, error and safety states | [board](ui05-loading-empty-error/components.png) | Lesson states may reflect mounted Lesson Library routes; video safety/job states are SRS target. |
| UI06 | Teacher import and extraction review | [board](ui06-teacher-import-review/components.png) | Upload sessions, parts, completion, extraction revision and version creation are mounted under /api/lesson-library/v1. |
| UI07 | Video quota and job states | [board](ui07-video-quota/components.png) | Billing/video admission and job APIs are SRS target, not mounted in Rev37. |
| UI08 | Lesson and child-profile grants | [board](ui08-access-grants/components.png) | Lesson grants and revoke are mounted; child-profile grant/invitation is SRS target. |
| UI09 | Lesson-scoped feedback | [board](ui09-lesson-feedback/components.png) | Lesson-scoped history/feedback/thread APIs are SRS target, not mounted. |

Each group folder contains PROMPT.md and MOTION.md. Status-specific actions are illustrative and must follow server state. See [PROMPT_LOG.md](PROMPT_LOG.md) and [MOTION_SPEC.md](MOTION_SPEC.md).
