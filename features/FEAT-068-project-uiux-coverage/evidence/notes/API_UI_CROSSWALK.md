# FEAT-068 UI and API crosswalk

- Captured: 2026-11-13, Asia/Saigon.
- Method: read-only source review of `FE_UI_Project_Ver2` at `d41b48ba`; no request was sent to a running backend.
- Requirement authority: FEAT-063 SRS v2.5-draft, unsigned. Rev38 mockups describe SRS v2.3/API Rev37 and are reference material only.

## Current frontend wiring

| Surface | Current source/runtime behavior | Consequence for FEAT-068 |
|---|---|---|
| Parent browser and Android | `UI_Project/parent-ui/src/App.tsx` stores profiles, lessons, stories, runs, notifications, grants, and progression in local React state. No Parent API client is imported. The Android host loads a bundled `parent-ui` document in WebView. | Make the mobile UI flow complete and responsive. Keep actions local and visibly preview-only unless a supported authenticated API is actually configured. Do not imply that the preview writes a story/profile or completes AI generation. |
| Teacher / School Manager / Platform Admin | Their entry files mount `Workspace` from `UI_Project/shared/webWorkspace.tsx`; business-page data and actions are local state. | Complete the role workspaces without presenting local actions as server-persisted. |
| Shared API client | `UI_Project/shared/backendApi.tsx` defines `/api/be1/v1` and `/api/lesson-library/v1` operations. Search of the current UI call sites found only `signInAndResolveRole` usage (account/assignment resolution); the lesson/class CRUD methods are not connected to their corresponding screens. | Reuse the current contracts only where connected mode is available; keep normal local preview usable and label its data. |
| Account login | The web client calls `GET /api/auth/v1/me`; no matching handler was found in current `backend/src`. The client expects `window.sketch2lifeAuth`, but this checkout contains no bridge implementation in the UI workspaces. | Do not claim real account/role resolution is working. Keep preview login separated from backend-connected identity and show a useful unavailable/error state in connected mode. |

## Exact mounted operations relevant to these screens

These operations are registered by `router_composition.mount_all_routers()` and have matching methods in `UI_Project/shared/backendApi.tsx`. The role screens themselves currently do not invoke them; they remain local previews until an authorized auth bridge, API base URL, and role/tenant context are available. This distinction is intentional: an operation existing in the repository does not mean it is connected to the UI or available in the current runtime.

| UI screen/action | Existing mounted operation | Client method | UI state in this branch |
|---|---|---|---|
| Parent public/shared lesson library, lesson detail, invitation list/response, permitted lesson download | `GET /api/lesson-library/v1/me/lessons`; `GET /me/lessons/{lesson_id}`; `GET /me/lessons/{lesson_id}/download`; `GET /me/lesson-invitations`; `POST /me/lesson-invitations/{grant_id}/accept`; `POST /me/lesson-invitations/{grant_id}/decline` | `parentLessons`, `parentLesson`, `parentInvitations`, `answerParentInvitation` (download is not wired) | Clearly marked sample lessons and invitation states. No live data or access decision is claimed. |
| Teacher reusable lesson list/detail, create/update/archive, public-review request | `GET /organizations/{organization_id}/lessons`; `GET/PATCH/DELETE /organizations/{organization_id}/lessons/{lesson_id}`; `POST /organizations/{organization_id}/lessons/{lesson_id}/versions`; `POST /organizations/{organization_id}/lessons/{lesson_id}/access-grants` | `lessons`, `teacherLesson`, `createLesson`, `updateLesson`, `archiveLesson`, `requestPublicReview` | Authoring/list interactions are preview-only. API contracts inform the role/visibility/version language; no unsaved fixture is presented as persisted. |
| Teacher document import, upload, deterministic extraction review | `POST /organizations/{organization_id}/lessons/{lesson_id}/upload-sessions`; `PUT /upload-sessions/{upload_session_id}/parts/{part_number}`; `POST /upload-sessions/{upload_session_id}/complete`; `GET /organizations/{organization_id}/lessons/{lesson_id}/source-documents/{document_id}` and revision read | `createUploadSession`, `uploadLessonPart`, `completeUpload`, `sourceDocument`, `documentRevision`, `abortUploadSession` | The selected local filename is not uploaded; extraction preview is not run. UI does not claim OCR/AI extraction. |
| School Manager version-specific public lesson review | `GET /organizations/{organization_id}/access-grants`; `POST /organizations/{organization_id}/access-grants/{access_grant_id}/decision` | `accessGrants`, `decideAccessGrant` | Preview decisions only. The screen shows a version/reason checklist but does not claim to publish or persist a decision. |
| Platform Admin lesson visibility moderation | `PATCH /platform/lessons/{lesson_id}/moderation` with revision precondition and reason | `moderateLesson` | Fixture queue only. No moderation mutation is sent from the UI. |
| Teacher / School Manager organization, class, roster and consent context | `GET /api/be1/v1/organizations/{organization_id}`; `GET /me`; `GET/POST /classes`; `GET /classes/{class_id}/profiles`; `GET /classes/{class_id}/consents`; `POST /classes/{class_id}/consents`; assignments `GET/POST/DELETE` | `assignments`, `classes`, `profiles`, `consents`, `recordConsent`, `createClass`, `createAssignment` | Current workspace screens are still fixture-only. These BE1 routes model organization roster/consent and must not be reused as Parent-owned profile CRUD. |
| Teacher classroom session lifecycle and roster | `POST /api/be1/v1/organizations/{organization_id}/sessions`; `GET /organizations/{organization_id}/sessions/{session_id}` plus learning-stage, roster, lobby, start, pause, resume, finish, outcome and control operations | `backendApi.tsx` has no matching session method, and the UI session preview does not call these operations. | Teacher session/deck/sample-video screens are target-flow previews; BE1 session is not the same contract as a durable lesson occurrence/story run. |

## Routes deliberately excluded from “connected” status

- `GET /api/auth/v1/me` is referenced by the shared client but is not registered by the current combined backend app; the expected `window.sketch2lifeAuth` bridge is also absent in these UI workspaces.
- The complete authenticated Parent profile, story, script, video, playback, feedback, quota, billing, and deletion lifecycle is not exposed as the target product flow in the mounted app. Parent UI stores only synthetic state in memory and labels unavailable operations.
- Teacher occurrence, optional Sketch Deck generation, child selection for a sample run, sample-video generation, and audited presentation confirmation do not have the full matching mounted route set in this combined app.
- Candidate routers (`ai_jobs`, `activity_execution`, knowledge/video review candidates and related modules) are not automatically mounted just because source files exist. `/v1/sessions` and `/v1/sessions/{id}/story-video-*` are local/ephemeral demo operations, and `story-run-lite` is a separate opt-in app with synthetic-data restrictions; neither is promoted to the authenticated Parent product API.
- No API mutation, authentication attempt, upload, AI request, media playback request, or write against a shared backend was made while preparing this crosswalk.

## Source routes available in the current combined backend composition

`create_app()` defaults to the combined profile. `router_composition.mount_all_routers()` includes the BE1 runtime route group, local/demo `/v1/sessions` route group, and Lesson Library. BE1 runtime aggregates the registry, session, canvas, artifact, and record routers.

| UI area | Current source route capability | UI policy |
|---|---|---|
| Parent lesson library/detail/invitations | `/api/lesson-library/v1/me/lessons`, detail, download and invitation/group routes are implemented and included in the combined composition. | The UI can model system-public/shared/delivered lesson states, but should only claim live data when valid auth/config is present. |
| Teacher lesson workspace/authoring/import | `/api/lesson-library/v1/organizations/{organization_id}/lessons`, detail/create/update/archive, upload-session/parts/complete, document/revision reads, version and grant routes are implemented and included in the combined composition. | Match form fields and statuses to the existing contracts; otherwise show labeled sample data. Extraction is deterministic source parsing, not an AI promise. |
| School Manager publication review | Organization access-grant listing/decision routes exist under Lesson Library. | Show version-specific review and explicit state; do not invent organization-wide management persistence. |
| Platform Admin moderation | `/api/lesson-library/v1/platform/lessons/{lesson_id}/moderation` is implemented and included in the combined composition. | Moderation UI can reflect the mounted action only in connected mode. Broader platform operations remain preview-only. |
| Teacher classes/roster/consent | `/api/be1/v1/organizations/...` registry/profile/consent routes exist in the included BE1 runtime. These are organization-owned classroom records, not Parent-owned child profiles. | Keep organization/tenant scope visible; do not reuse these routes for Parent profile CRUD. |
| Parent profile/run/story/video/quota/playback | The target SRS describes these APIs, but the current combined source does not expose the full authenticated durable flow. | Use honest preview or unavailable states for profile writes, story jobs, video, quota, and playback; never fake server progress or success. |
| Teacher occurrence/Sketch Deck/sample-video/presentation | These target screens are in SRS and Rev38 references, but matching occurrence/deck/story-video contracts are not mounted as the complete target flow in the current combined app. | Present optional deck, story, and presentation states as preview-only unless a supported mounted route is identified; keep deck separate from the child sample run. |

## Conditional demo routes and limitations

- `/v1/story-runs` is implemented by a separate StoryRun-lite slice. The main-app opt-in flag `STORYRUN_LITE_MAIN_DEMO_ENABLED` defaults to `0`; when enabled it is limited to the combined local/test app, loopback-only, and synthetic demo data. It is not a production authenticated Parent API.
- The mounted `/v1/sessions` family is local/ephemeral demo flow and should not be represented as the SRS durable StoryRun API.
- Source registration is not live-runtime proof. No backend health/OpenAPI request, mutation, or AI job was issued for this crosswalk.

## SRS flow constraints applied to the UI

- Parent: optional generic line-sketch while the child draws → capture → idea / confirmed transcript → subject review/correction → adult context snapshot confirmation → script review/confirmation → video → activities after playable video.
- Parent activities are not selected before video; do not remove context review when removing the separate arbitrary context opt-in selector.
- Do not add a persisted gender field absent from SRS/API. Do not add the old mismatch-direction modal without a specified server state/contract.
- Teacher Sketch Deck is optional and produces no job when disabled. Teacher’s explicit presentation confirmation is distinct from video safety/readiness.
