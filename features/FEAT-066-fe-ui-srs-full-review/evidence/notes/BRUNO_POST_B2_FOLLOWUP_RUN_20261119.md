# Bruno follow-up run evidence — 2026-11-19

The coordinating review session performed the run. This Codex session did not run Bruno, Docker, the database, or the API. Counts below are transcribed from `tmp/bruno-next/RUN_RESULT_FOR_CODEX.md`; no request bodies, request headers, response bodies, or response headers are recorded.

## Aggregate counts

| Class | Count |
|---|---:|
| Requests run | 153 |
| PASS | 4 |
| FAIL | 0 |
| BLOCKED-AUTH | 101 |
| BLOCKED-ENV | 46 |
| STALE | 2 |

The collection contains 160 requests: 159 regular requests plus the separate L5 A02 request. The run used 153 because sequences 153–159 were intentionally excluded from the run copy. Those seven requests were not sent.

## Run conditions and provenance

The coordinating review session ran Bruno CLI 4.3.0 against the loopback API at `127.0.0.1:8010`, with the collection loopback guard active and a new disposable database. The collection environment supplied only a placeholder bearer; no real token, Firebase request, or Modal call was used. The CLI setting `--env-var baseUrl=http://127.0.0.1:8010` selected the loopback API. The guard file `collection.bru` had SHA-256 `AD0A6A9A42A5038090725FF3E7615CCB9AA3BC070B951035E6D2774C0E9B69EE`.

The run used a copy at `tmp/bruno-next/coll` with requests 153–159 removed. The README was edited after that copy was made; aside from the seven intentionally removed request files and that later README edit, the copy matched the worktree collection. Requests 153–159 were neither sent nor parsed by Bruno CLI; parsing is NOT VERIFIED.

The supplied `rows.json` SHA-256 is `722C7B39BEB2AF54A6739EB40A58CB010D003CFDE0A42AD88CACB70ED916FBA3`; the supplied `run_body.json` SHA-256 is `28BE0AEA7A4CC61B378A08ECF03BFAB42D4983E22F7CB357267E5ED73A35A09C`. The files' contents are not reproduced here.

The four PASS requests were `002` GET `/api/be1/v1/health`, `090` GET `/health`, `001` GET `/health`, and `116` GET `/v1/sessions/{{session_id}}/story-video-jobs`.

## Class definitions

- PASS means the request's success checks passed.
- FAIL means evidence shows a reproducible product defect rather than an authentication, environment, or stale-route blocker.
- BLOCKED-AUTH means the request was prevented from establishing authenticated behavior: 92 responses were 503 because the identity provider was unavailable, and 9 of the 10 rows with status 401 were authentication or device-credential failures.
- BLOCKED-ENV means the request could not establish the intended behavior because a route, local feature, fixture, or placeholder value was unavailable or unsuitable in this run environment. The other 401 row is request 126, `requests/storyrun-lite/126-readiness-v1-story-runs-readiness-get.bru`; its StoryRun-lite readiness route exists only in the demo router, so with demo mode off its path reaches the Parent run route. Counting request 126 under BLOCKED-ENV leaves the summary at 101 BLOCKED-AUTH and 46 BLOCKED-ENV.
- STALE means the request targets a replaced route; requests 004 and 005 are retained as stale examples.

## Request paths included in the run

| Method | Request path |
|---|---|
| GET | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/pilot-profiles |
| GET | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/canvas/operations |
| POST | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/canvas/operations |
| POST | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/groups/{{group_id}}/checkpoints |
| GET | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/groups/{{group_id}}/checkpoints/latest |
| POST | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/groups/{{group_id}}/restore |
| GET | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/reconnect |
| GET | /api/be1/v1/health |
| GET | /health |
| POST | /v1/parent/profiles |
| PATCH | /v1/parent/profiles/{{parent_profile_id}} |
| DELETE | /v1/parent/profiles/{{parent_profile_id}} |
| DELETE | /v1/story-runs/{{parent_story_run_id}} |
| POST | /v1/story-runs/{{parent_story_run_id}}/context-confirmation |
| POST | /v1/story-runs/{{parent_story_run_id}}/script-confirmation |
| GET | /health |
| DELETE | /api/lesson-library/v1/upload-sessions/{{upload_session_id}} |
| GET | /api/lesson-library/v1/upload-sessions/{{upload_session_id}} |
| POST | /api/lesson-library/v1/upload-sessions/{{upload_session_id}}/complete |
| PUT | /api/lesson-library/v1/upload-sessions/{{upload_session_id}}/parts/{{part_number}} |
| POST | /v1/profile/preferences/classify |
| POST | /v1/sessions/{{session_id}}/media/audio |
| POST | /v1/sessions/{{session_id}}/media/image |
| POST | /v1/sessions/{{session_id}}/understanding |
| GET | /v1/sessions/{{session_id}}/understanding/progress |
| POST | /v1/sessions |
| GET | /v1/sessions/{{session_id}} |
| POST | /v1/sessions/{{session_id}}/experience/prepare |
| POST | /v1/sessions/{{session_id}}/feedback |
| GET | /v1/sessions/{{session_id}}/gallery |
| POST | /v1/sessions/{{session_id}}/gate-a/confirm |
| POST | /v1/sessions/{{session_id}}/gate-b/approve |
| POST | /v1/sessions/{{session_id}}/handoff |
| POST | /v1/sessions/{{session_id}}/media/retake |
| PUT | /v1/sessions/{{session_id}}/p1-context |
| POST | /v1/sessions/{{session_id}}/p1-filter |
| POST | /v1/sessions/{{session_id}}/p1/activity-suggestions |
| POST | /v1/sessions/{{session_id}}/p1/activity-suggestions/rank |
| GET | /v1/sessions/{{session_id}}/p1/context-candidates?age_months={{age_months}} |
| GET | /v1/sessions/{{session_id}}/p1/context-options?age_months={{age_months}} |
| POST | /v1/sessions/{{session_id}}/p1/context-options |
| POST | /v1/sessions/{{session_id}}/p1/context-options/finalize |
| POST | /v1/sessions/{{session_id}}/renderer/launch |
| GET | /v1/renderer/pixi-asset |
| GET | /v1/renderer/rig-mask |
| GET | /v1/renderer/rig-package |
| GET | /v1/renderer/source |
| POST | /api/dev/v1/storage-examples/lesson-source-documents |
| DELETE | /api/dev/v1/storage-examples/lesson-source-documents/{{object_id}} |
| GET | /api/dev/v1/storage-examples/lesson-source-documents/{{object_id}} |
| GET | /v1/sessions/{{session_id}}/story-video-jobs |
| POST | /v1/sessions/{{session_id}}/story-video-jobs |
| GET | /v1/sessions/{{session_id}}/story-video/{{job_id}} |
| GET | /v1/sessions/{{session_id}}/story-video/{{job_id}}/file |
| GET | /v1/sessions/{{session_id}}/whiteboard-video |
| POST | /v1/sessions/{{session_id}}/whiteboard-video-jobs |
| GET | /v1/sessions/{{session_id}}/whiteboard-video/file |
| POST | /v1/whiteboard/storyboards/preview |
| GET | /api/be1/v1/organizations/{{organization_id}} |
| POST | /api/be1/v1/organizations/{{organization_id}}/assignments |
| DELETE | /api/be1/v1/organizations/{{organization_id}}/assignments/{{assignment_id}} |
| GET | /api/be1/v1/organizations/{{organization_id}}/classes |
| POST | /api/be1/v1/organizations/{{organization_id}}/classes |
| GET | /api/be1/v1/organizations/{{organization_id}}/classes/{{class_id}}/consents |
| POST | /api/be1/v1/organizations/{{organization_id}}/classes/{{class_id}}/consents |
| POST | /api/be1/v1/organizations/{{organization_id}}/classes/{{class_id}}/consents/{{consent_id}}/revoke |
| GET | /api/be1/v1/organizations/{{organization_id}}/classes/{{class_id}}/profiles |
| POST | /api/be1/v1/organizations/{{organization_id}}/classes/{{class_id}}/profiles |
| GET | /api/be1/v1/organizations/{{organization_id}}/me |
| GET | /api/be1/v1/organizations/{{organization_id}}/teacher-candidates?limit=25 |
| POST | /api/be1/v1/classes/{{class_id}}/assignments |
| DELETE | /api/lesson-library/v1/organizations/{{organization_id}}/parent-groups/{{parent_group_id}}/members/{{membership_id}} |
| GET | /api/lesson-library/v1/me/lesson-invitations |
| POST | /api/lesson-library/v1/me/lesson-invitations/{{access_grant_id}}/accept |
| POST | /api/lesson-library/v1/me/lesson-invitations/{{access_grant_id}}/decline |
| GET | /api/lesson-library/v1/me/lessons |
| GET | /api/lesson-library/v1/me/lessons/{{lesson_id}} |
| GET | /api/lesson-library/v1/me/lessons/{{lesson_id}}/download |
| GET | /api/lesson-library/v1/me/parent-group-invitations |
| POST | /api/lesson-library/v1/me/parent-group-invitations/{{membership_id}}/accept |
| GET | /v1/parent/profiles |
| GET | /v1/parent/profiles/{{parent_profile_id}} |
| GET | /v1/story-runs/active/current |
| GET | /v1/story-runs/{{parent_story_run_id}} |
| GET | /api/platform-admin/v1/accounts?limit=25 |
| POST | /api/platform-admin/v1/accounts |
| PATCH | /api/platform-admin/v1/accounts/{{platform_account_id}} |
| PATCH | /api/lesson-library/v1/platform/lessons/{{lesson_id}}/moderation |
| GET | /api/auth/v1/me |
| POST | /api/be1/v1/organizations/{{organization_id}}/classes/{{class_id}}/observations |
| GET | /api/be1/v1/organizations/{{organization_id}}/classes/{{class_id}}/profiles/{{child_id}}/portfolio |
| POST | /api/be1/v1/organizations/{{organization_id}}/data-requests |
| GET | /api/be1/v1/organizations/{{organization_id}}/data-requests/{{request_id}} |
| GET | /api/be1/v1/organizations/{{organization_id}}/gallery?session_id={{session_id}} |
| POST | /api/be1/v1/organizations/{{organization_id}}/gallery |
| POST | /api/be1/v1/organizations/{{organization_id}}/gallery/{{gallery_id}}/annotations |
| POST | /api/be1/v1/organizations/{{organization_id}}/gallery/{{gallery_id}}/publish |
| GET | /api/lesson-library/v1/organizations/{{organization_id}}/access-grants?state=PENDING_REVIEW&audience_kind=PUBLIC |
| POST | /api/lesson-library/v1/organizations/{{organization_id}}/access-grants/{{access_grant_id}}/decision |
| GET | /api/lesson-library/v1/organizations/{{organization_id}}/parent-groups?limit=50 |
| POST | /api/lesson-library/v1/organizations/{{organization_id}}/parent-groups |
| POST | /api/lesson-library/v1/organizations/{{organization_id}}/parent-groups/{{parent_group_id}}/invitations |
| POST | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/artifacts |
| GET | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/artifacts/{{asset_ref}} |
| POST | /api/be1/v1/device-grants/{{grant_id}}/join-status |
| POST | /api/be1/v1/organizations/{{organization_id}}/sessions |
| GET | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}} |
| POST | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/completion |
| POST | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/device-grants/{{grant_id}}/refresh |
| POST | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/finish |
| POST | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/groups |
| POST | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/groups/{{group_id}}/control |
| PUT | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/groups/{{group_id}}/members/{{child_id}} |
| POST | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/groups/{{group_id}}/turns/{{child_id}} |
| POST | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/join |
| GET | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/join-requests |
| POST | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/join-requests/{{grant_id}}/admit |
| POST | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/join-requests/{{grant_id}}/revoke |
| GET | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/learning-stage |
| POST | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/learning-stage/advance |
| POST | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/lobby |
| POST | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/memberships/{{membership_id}}/help |
| POST | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/memberships/{{membership_id}}/leave |
| POST | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/memberships/{{membership_id}}/progress |
| GET | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/outcome |
| POST | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/pause |
| POST | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/resume |
| POST | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/room-code/rotate |
| GET | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/roster |
| POST | /api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/start |
| POST | /api/be1/v1/room-code/join |
| GET | /api/lesson-library/v1/organizations/{{organization_id}}/lessons |
| DELETE | /api/lesson-library/v1/organizations/{{organization_id}}/lessons/{{lesson_id}} |
| GET | /api/lesson-library/v1/organizations/{{organization_id}}/lessons/{{lesson_id}} |
| DELETE | /api/lesson-library/v1/organizations/{{organization_id}}/lessons/{{lesson_id}}/access-grants/{{access_grant_id}} |
| POST | /v1/story-runs |
| GET | /v1/story-runs/readiness |
| GET | /v1/story-runs/{{run_ref}} |
| POST | /v1/story-runs/{{run_ref}}/assets |
| POST | /v1/story-runs/{{run_ref}}/cancel |
| POST | /v1/story-runs/{{run_ref}}/subject-confirmation |
| POST | /v1/upload-sessions |
| DELETE | /v1/upload-sessions/{{upload_ref}} |
| GET | /v1/upload-sessions/{{upload_ref}} |
| POST | /v1/upload-sessions/{{upload_ref}}/complete |
| PUT | /v1/upload-sessions/{{upload_ref}}/parts/{{part_no}} |
| POST | /api/lesson-library/v1/organizations/{{organization_id}}/lessons |
| PATCH | /api/lesson-library/v1/organizations/{{organization_id}}/lessons/{{lesson_id}} |
| POST | /api/lesson-library/v1/organizations/{{organization_id}}/lessons/{{lesson_id}}/access-grants |
| GET | /api/lesson-library/v1/organizations/{{organization_id}}/lessons/{{lesson_id}}/source-documents/{{source_document_id}} |
| GET | /api/lesson-library/v1/organizations/{{organization_id}}/lessons/{{lesson_id}}/source-documents/{{source_document_id}}/revisions/{{revision_id}} |
| POST | /api/lesson-library/v1/organizations/{{organization_id}}/lessons/{{lesson_id}}/upload-sessions |
| POST | /api/lesson-library/v1/organizations/{{organization_id}}/lessons/{{lesson_id}}/versions |

## Intentionally excluded request paths

| Sequence | Method | Request path |
|---:|---|---|
| 153 | POST | /api/auth/v1/registrations |
| 154 | POST | /api/parent/v1/ai/drawing-understandings |
| 155 | POST | /api/parent/v1/ai/sketch-guides |
| 156 | POST | /api/parent/v1/ai/story-runs/{{parent_story_run_id}}/story-revisions |
| 157 | POST | /api/teacher/v1/organizations/{{organization_id}}/ai/lesson-plan-suggestions |
| 158 | POST | /api/teacher/v1/organizations/{{organization_id}}/ai/lesson-visuals |
| 159 | POST | /api/teacher/v1/organizations/{{organization_id}}/ai/sketch-decks |

## Requests with no mounted application route

The run record reports no mounted non-framework route without a request. The following request paths were identified as stale or development-only and have no matching mounted application route:

| Sequence | Method | Request path |
|---:|---|---|
| 4 | POST | /api/be1/v1/organizations/{{organization_id}}/assignments |
| 5 | DELETE | /api/be1/v1/organizations/{{organization_id}}/assignments/{{assignment_id}} |
| 57 | POST | /api/dev/v1/storage-examples/lesson-source-documents |
| 58 | DELETE | /api/dev/v1/storage-examples/lesson-source-documents/{{object_id}} |
| 59 | GET | /api/dev/v1/storage-examples/lesson-source-documents/{{object_id}} |
| 126 | GET | /v1/story-runs/readiness |
| 128 | POST | /v1/story-runs/{{run_ref}}/assets |
| 131 | POST | /v1/upload-sessions |
| 132 | DELETE | /v1/upload-sessions/{{upload_ref}} |
| 133 | GET | /v1/upload-sessions/{{upload_ref}} |
| 134 | POST | /v1/upload-sessions/{{upload_ref}}/complete |
| 135 | PUT | /v1/upload-sessions/{{upload_ref}}/parts/{{part_no}} |
