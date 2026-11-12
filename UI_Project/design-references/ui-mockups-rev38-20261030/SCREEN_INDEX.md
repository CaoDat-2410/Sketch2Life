# Sketch2Life screen mockups — Rev38

Generated visual drafts for owner review. All people, school names, counts, and dates are fictional. SRS v2.3 remains a draft; the screen images and proposed visual tokens are not implementation contracts.

| ID | Role | Screen | Purpose / API boundary |
|---|---|---|---|
| P01 | Parent | [screen](parent/p01-lesson-library/screen.png) | Lesson library and child selection entry. Mounted: GET /api/lesson-library/v1/me/lessons. Child-profile read/selection is not covered by this route and remains an SRS target. |
| P02 | Parent | [screen](parent/p02-lesson-detail/screen.png) | Reusable lesson detail. Mounted: GET /api/lesson-library/v1/me/lessons/{lesson_id}. Starting a child occurrence remains target. |
| P03 | Parent | [screen](parent/p03-drawing-line-guide/screen.png) | Drawing with optional generic line-sketch guide. Guide-generation API is SRS target, not mounted. |
| P04 | Parent | [screen](parent/p04-capture-subject-confirmation/screen.png) | Capture/import artwork and adult subject confirmation after VLM suggestion. Capture/VLM routes are SRS target, not mounted. |
| P05 | Parent | [screen](parent/p05-context-idea-confirmation/screen.png) | Pinned child context and text/voice idea transcript confirmation. Story/ASR routes are SRS target, not mounted. |
| P06 | Parent | [screen](parent/p06-story-review/screen.png) | Review 5–15 scene script, suggest up to three AI rewrites, confirm exact revision. Story routes are SRS target, not mounted. |
| P07 | Parent | [screen](parent/p07-video-job-status/screen.png) | Resume discrete background video stages; show failed and automatic safety-blocked states. Video/quota routes are SRS target, not mounted. |
| P08 | Parent | [screen](parent/p08-video-and-activities/screen.png) | Private video uses the shared child artwork; captions and finish/retry precede lesson outdoor activities. Playback/occurrence routes are SRS target, not mounted. |
| P09 | Parent | [screen](parent/p09-history-feedback/screen.png) | 30/60-day history concept, delete action, lesson-scoped school feedback. Lesson read is mounted; occurrence history/feedback routes are SRS target. |
| P10 | Parent | [screen](parent/p10-child-profiles/screen.png) | Create/edit/archive Parent child profiles. Profile-management routes are SRS target, not mounted. |
| P11 | Parent | [screen](parent/p11-authentication/screen.png) | Sign-in/register and recovery entry. Firebase is Authentication-only by governance; no matching application route is claimed here. |
| P12 | Parent | [screen](parent/p12-video-quota/screen.png) | Numeric quota and optional top-up choices. Billing/quota routes are SRS target, not mounted. |
| T01 | Teacher | [screen](teacher/t01-lesson-workspace/screen.png) | Teacher lesson workspace. Mounted: GET /api/lesson-library/v1/organizations/{organization_id}/lessons and lesson detail. |
| T02 | Teacher | [screen](teacher/t02-lesson-authoring/screen.png) | Structured, multi-activity lesson drafting and review submission. Mounted: lesson POST/PATCH, version creation, access-grant request under /api/lesson-library/v1. |
| T03 | Teacher | [screen](teacher/t03-document-import-review/screen.png) | Upload, deterministic scan/extraction, extracted-field review and confirmation. Mounted: lesson upload-session/parts/complete, source-document/revision read and version creation under /api/lesson-library/v1; no AI extraction is implied. |
| T04 | Teacher | [screen](teacher/t04-session-sketch-deck/screen.png) | Occurrence preparation with one optional Sketch Deck toggle. Occurrence/deck generation routes are SRS target, not mounted. |
| T05 | Teacher | [screen](teacher/t05-classes-and-children/screen.png) | Class and assigned-child roster/profile workspace. Class/roster management routes are SRS target; BE1 session endpoints do not implement this screen contract. |
| T06 | Teacher | [screen](teacher/t06-sample-story-run/screen.png) | One randomly selected eligible child, one lesson activity, adult script confirmation. Story/video routes are SRS target, not mounted. |
| T07 | Teacher | [screen](teacher/t07-video-presentation-confirmation/screen.png) | Private sample-video preview and explicit presentation confirmation for one occurrence. Playback/presentation routes are SRS target, not mounted. |
| M01 | School Manager | [screen](school-manager/m01-publication-review/screen.png) | Version-specific public review; checklist begins unchecked and approval disabled until complete. Mounted: GET organization access grants and POST decision under /api/lesson-library/v1. |
| M02 | School Manager | [screen](school-manager/m02-organization-management/screen.png) | Organization teachers/groups/classes/slots/quota. This full management surface is SRS target; Rev37 has no matching organization-admin contract for these actions. |
| A01 | Platform Admin | [screen](platform-admin/a01-content-moderation/screen.png) | State-dependent public lesson moderation. Mounted: PATCH /api/lesson-library/v1/platform/lessons/{lesson_id}/moderation. |
| A02 | Platform Admin | [screen](platform-admin/a02-platform-operations/screen.png) | Organization/catalog/policy/quota overview. Full platform operations remain SRS target; A01 moderation is mounted separately. |

## Design and flow rules

- Parent and Teacher flows stay separate; all child examples use the same fictional five-year-old Minh.
- The shared butterfly artwork stays recognizable through capture/story/video. Activities follow the video.
- Parent guide and Teacher Sketch Deck are optional; when disabled they create no generation job.
- Adult confirms the script before video. Video safety is automatic; no final adult video-review gate is shown.
- Feedback is lesson-scoped; lesson grants and child-profile grants are separate and revocable.
- Blue is a proposed primary action, yellow a secondary accent, mint supportive, red destructive/error only. These are not approved production tokens.
- API status is mapped against Rev37's 135 declared / 124 mounted operation inventory; “SRS target” does not mean a current route exists.

Each screen folder contains its prompt and motion note. See [PROMPT_LOG.md](PROMPT_LOG.md) and [MOTION_SPEC.md](MOTION_SPEC.md).
