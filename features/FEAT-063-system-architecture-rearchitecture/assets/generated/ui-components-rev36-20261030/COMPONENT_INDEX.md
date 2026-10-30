# Sketch2Life UI component and state mockups — Rev36

**Lifecycle:** generated visual drafts; not implementation-ready or approved for application.

Each group has its own directory with `components.png`, `PROMPT.md`, and `MOTION.md`. The detailed prompt briefs and motion behavior are collected in `PROMPT_LOG.md` and `MOTION_SPEC.md`.

| ID | Component group | SRS/API mapping | API status | Files |
|---|---|---|---|---|
| UI01 | Foundations and controls | Shared Parent/Teacher/Admin UI foundation; no endpoint | Visual proposal only; does not change app tokens | [PNG](ui01-foundations-controls/components.png) · [prompt](ui01-foundations-controls/PROMPT.md) · [motion](ui01-foundations-controls/MOTION.md) |
| UI02 | Parent dialogs and bottom sheets | SRS §21.5–§21.6; target script confirmation and run cancel; camera/gallery and microphone/text fallback | Existing flow concepts plus SRS target run actions; not a new route claim | [PNG](ui02-parent-dialogs-sheets/components.png) · [prompt](ui02-parent-dialogs-sheets/PROMPT.md) · [motion](ui02-parent-dialogs-sheets/MOTION.md) |
| UI03 | Web decision dialogs | Manager access-grant decision; Teacher lesson archive; Admin lesson moderation | Rev31 Lesson Library API | [PNG](ui03-web-decision-dialogs/components.png) · [prompt](ui03-web-decision-dialogs/PROMPT.md) · [motion](ui03-web-decision-dialogs/MOTION.md) |
| UI04 | Toasts, snackbars and inline notices | SRS §21.6; shared response patterns for success, validation, stale revision and retryable failure | UI behavior from SRS/API response classes; no separate endpoint | [PNG](ui04-toast-inline-notices/components.png) · [prompt](ui04-toast-inline-notices/PROMPT.md) · [motion](ui04-toast-inline-notices/MOTION.md) |
| UI05 | Loading, empty, unavailable and conflict states | SRS §21.6 error groups: auth, safe not-found, forbidden, stale revision, validation and provider unavailable | Mix of current API errors and SRS target states; exact route varies | [PNG](ui05-api-client-states/components.png) · [prompt](ui05-api-client-states/PROMPT.md) · [motion](ui05-api-client-states/MOTION.md) |
| UI06 | Upload and extraction states | Lesson upload-session, part upload, complete/scan/extract, document status/revision preview and LessonVersion confirmation | Rev31 Lesson Library API | [PNG](ui06-upload-extraction-states/components.png) · [prompt](ui06-upload-extraction-states/PROMPT.md) · [motion](ui06-upload-extraction-states/MOTION.md) |
| UI07 | Quota and AI job states | SRS `/v1/video-quota`, `/v1/video-quota/purchases`, `/v1/story-runs/{id}/video-generations`, run/job status | SRS target; video/quota APIs were not implemented in Rev31 | [PNG](ui07-quota-ai-job-states/components.png) · [prompt](ui07-quota-ai-job-states/PROMPT.md) · [motion](ui07-quota-ai-job-states/MOTION.md) |
| UI08 | Sharing and access grants | Lesson visibility/access grants, Parent group/named invitations and revoke; child-profile share is separately specified in SRS | Lesson-grant routes are Rev31; child-profile grant route remains SRS target | [PNG](ui08-sharing-access-grants/components.png) · [prompt](ui08-sharing-access-grants/PROMPT.md) · [motion](ui08-sharing-access-grants/MOTION.md) |
| UI09 | Feedback and notifications | SRS §31.6 school-scoped delivery feedback/history; notification status | LessonOccurrence feedback/history and related notification flow are not in the Rev31 Lesson Library contract | [PNG](ui09-feedback-notifications/components.png) · [prompt](ui09-feedback-notifications/PROMPT.md) · [motion](ui09-feedback-notifications/MOTION.md) |

## Explicit API boundary

The Rev31-reconciled Lesson Library contract provides current operations for lesson CRUD/versioning, filtered uploads, access grants, Manager publication decisions, Parent lesson reads and Platform Admin moderation. SRS concepts for new Parent/Teacher AI and video workflows, video quota, child-profile sharing, and LessonOccurrence history/feedback remain future API work. Existing Demo feedback/story routes do not implement those new product contracts.

## Review and use

All images are generated visual examples; text, dimensions, spacing and controls need product/design review. Do not reference them from app source or copy them into `assets/approved/` or `assets/applied/` before explicit visual approval.
