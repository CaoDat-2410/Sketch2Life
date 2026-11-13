# FEAT-069 Rev3 API-to-UI crosswalk

- Captured: 2026-11-14 (Asia/Saigon).
- Delivery branch: `FE_UI_Project_Ver2`, baseline `ae2a8c8165aa1d11b62a7005a9e28d8c0ea8c046`.
- API source: current checkout's combined backend composition and `UI_Project/shared/backendApi.tsx`.
- Comparison source: permitted, read-only `origin/feature/feat063-m2-parent-teacher-foundation@5c07c94e86826447d975ef2757aa1fefdc876c8c` only. No source was taken from the screenshot-excluded branches.
- Requirement authority: FEAT-063 SRS v2.5-draft, still unsigned; leader feedback remains review input and does not supersede it.
- Method: local source inspection and UI builds/visual review. No live API call, authentication attempt, database request, mutation, AI call, upload, or child data was used.

## Mounted contracts and current UI behavior

| Role / screen | Delivery-branch route and client method | Rev3 UI behavior | Runtime limitation |
|---|---|---|---|
| Teacher dashboard and lesson list | `GET /api/lesson-library/v1/organizations/{organization_id}/lessons`; `backendApi.lessons(org)` | When a Firebase token bridge and organization ID exist, render API lesson summaries, versions, visibility and review state. Dashboard lesson counts are derived from returned rows. | No create/edit/archive/review mutation is wired to this list. Without auth/config, local rows are labeled preview. API errors show unavailable/error state with no fixture fallback. |
| Teacher dashboard assignment metric | `GET /api/be1/v1/organizations/{organization_id}/me`; `backendApi.assignments(org)` | Counts active teacher assignments with non-null `class_id` for the summary metric. | No class dashboard endpoint exists. Metric is a direct count of returned assignments, not an analytics API. |
| School Manager dashboard and classes | `GET /api/be1/v1/organizations/{organization_id}/classes`; `backendApi.classes(org)` | Displays the current organization class list and state. Dashboard values are derived from returned class rows. | Roster, consent, assignment management and mutations remain preview-only in this revision. No fixture fallback in API mode. |
| Platform Admin moderation | `PATCH /api/lesson-library/v1/platform/lessons/{lesson_id}/moderation`; `backendApi.moderateLesson(...)` | Moderation interface remains a visibly labeled preview. | No moderation queue-list route is mounted in the delivery branch; no mutation is called. |
| Parent mobile library | `GET /api/lesson-library/v1/me/lessons?source=ALL`; `GET /me/lesson-invitations`; `GET /me/lessons/{lesson_id}`; existing `backendApi.parentLessons`, `parentInvitations`, `parentLesson` methods | When the Firebase token bridge exists, public/shared lesson groups and invitation list use API summaries; opening a lesson loads its detail. Authenticated read failure displays an error and no sample rows. | Contract omits teacher/school display names for direct invitations; UI labels them neutrally and does not invent identities. Without a bridge, fixture preview is retained. |
| Parent invitation response | `POST /api/lesson-library/v1/me/lesson-invitations/{access_grant_id}/accept` or `/decline`; existing typed `backendApi.answerParentInvitation` includes an idempotency key | Calls only after the user presses Chấp nhận/Từ chối. Shows the result and reloads the Parent library/invitation lists. | API action cannot be verified in this checkout without the runtime auth/backend. |
| Parent story/profile/media | Target profile/story/ASR/video route families are not mounted as the target flow in the delivery composition. | Parent remains the `UI_Project/parent-ui` interface packaged by the Android WebView host; these workflows remain clearly labeled preview-only. | Parent profile CRUD, story, photo analysis, ASR, video generation/playback and full durable run workflow are not available to a teammate cloning this delivery branch. |
| Teacher session, slide/deck and child sample | BE1 session lifecycle routes exist, but the shared client does not expose the complete matching teacher occurrence/deck/sample workflow. | Review flow remains preview-only and is distinct from session persistence. | Do not infer that the BE1 classroom session route provides durable lesson occurrence or AI deck/sample behavior. |

## Authentication and environment gate

The conditional web reads run only if `window.sketch2lifeAuth.getIdToken` is present and a runtime organization ID is configured. Parent library reads need the token bridge but no organization ID because the routes scope data to the authenticated adult principal. Requests use bearer tokens and a 15-second timeout via the typed client. The client also defines `GET /api/auth/v1/me`, but no matching handler or runtime bridge implementation exists in this delivery checkout. Therefore the supported UI state is local preview by default; API-backed state is available only in a deployment/runtime that injects the documented bridge and (for web roles) organization context. This task did not test that external configuration.

When authenticated web mode is detected but the organization ID is missing, the UI reports the missing configuration and does not substitute local fixture rows. When an API call fails, the dashboard/list shows an error state and offers a read retry; failed API data is never converted into an empty-success claim. Parent invitation writes require a deliberate button click and show actual response/error status. A successful API result covers only the route-backed screen, not every item in the role workspace.

## Contract gaps and requirement conflicts

- The current branch lacks the expected auth identity handler/bridge for end-to-end login/role resolution.
- The current branch lacks complete Parent profile/story/photo/audio/ASR/video/playback flows, analytics endpoints, teacher occurrence/deck/sample APIs, and a platform moderation queue-list endpoint.
- Additional Parent story/profile and Parent/Teacher AI routers found on the permitted newer comparison branch are read-only context. They are not available to the `FE_UI_Project_Ver2` handoff and were not merged or referenced as connected.
- The leader asks for a Parent outdoor activity before video, while FEAT-063 SRS v2.5-draft FR-P-05 / FR-PL-16 place activities after playable video. The existing preview sequence remains labeled and the requirement conflict is open.
- Child gender and image mismatch analysis have no matching persisted field/result contract in this delivery branch; both remain preview-only.
- “100% leader review completion” can describe the preview presentation only. It cannot mean all reviewed paths are authenticated, persisted or supported by mounted APIs on the current branch.

## Branch boundary

This crosswalk uses only the current delivery checkout for implementation. The branch `origin/feature/feat063-m2-parent-teacher-foundation` was consulted read-only as explicitly permitted by the owner. The following branches were excluded as source: `FE_UI_Project_Ver2`, `dev`, `FE_UI_Project`, `FE/UI-Teacher`, `FE/UI-School-Manager`, `FE/UI-Platform-Admin`, `FE/UI-Parent`, `codex/feat-018-contract-plan`, and all `plan/person-3-*`. The top-level `apps/` tree and Child Expo were not used.
