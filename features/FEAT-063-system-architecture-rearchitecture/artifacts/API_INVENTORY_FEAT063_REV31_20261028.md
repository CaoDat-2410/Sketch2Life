# FEAT-063 API inventory - Rev31 (2026-10-28)

This is a static inventory of HTTP route declarations under `backend/src/sketch2life/interfaces/http/routers/`, reconciled against `router_composition.py`, `be1_runtime.py`, and `app.py`. It lists method/path pairs and owning handler. Lesson Library purpose, authorization, request/response DTOs and status codes are specified in `LESSON_LIBRARY_API_CONTRACT_DRAFT_REV29_20261028.md` (Rev31 implementation reconciliation).

For the purpose of each declared method/path, see the [Rev32 API purpose catalog](API_PURPOSE_CATALOG_FEAT063_REV32_20261028.md). The catalog retains runtime exposure and handler attribution for all 135 declarations.

## Surface totals

| Surface | Declared routes | Runtime status |
|---|---:|---|
| BE1 / classroom | 56 | Mounted by combined and classroom profiles |
| Demo / local flow | 35 | Mounted by combined and demo profiles; in-memory/demo capabilities remain legacy surfaces |
| Lesson Library | 30 | Mounted by combined profile only |
| Local storage example | 3 | Combined profile only when `SKETCH2LIFE_ENV=local` and `SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED=true` |
| Candidate / fixture / unmounted | 11 | Not mounted by the default app; some have isolated fixture apps or router factories |
| **Total declared router operations** | **135** | **121 unconditional combined-app routes; local sample adds 3 when enabled** |

The combined app is `121` router operations before local-only storage examples. The classroom profile contains the BE1/classroom set; the demo profile contains the demo set. These counts come from source declarations and composition, not a running application or OpenAPI runtime export. FastAPI also generates `GET /openapi.json`, `GET /docs`, and `GET /docs/oauth2-redirect` in `create_app`; these framework routes are excluded from the router declaration count. A `/renderer` static-file mount is conditional on the demo renderer directory and is not a JSON API.

## BE1 / classroom routes

Purpose: organization and role assignments, classes/profiles/consent, session lifecycle and device admission, canvas operations/checkpoints, session artifacts, observations, portfolios, gallery and data requests. Adult endpoints use verified identity and organization assignments; device endpoints use scoped device grants.

| Method | Path | Handler / source |
|---|---|---|
| `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/artifacts` | `be1_artifacts.py::upload_session_artifact` |
| `GET` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/artifacts/{asset_ref:path}` | `be1_artifacts.py::download_session_artifact` |
| `GET` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/canvas/operations` | `be1_canvas.py::sync_canvas_operations` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/canvas/operations` | `be1_canvas.py::append_canvas_operation` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/checkpoints` | `be1_canvas.py::save_checkpoint` |
| `GET` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/checkpoints/latest` | `be1_canvas.py::read_latest_checkpoint` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/restore` | `be1_canvas.py::restore_checkpoint` |
| `GET` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/reconnect` | `be1_canvas.py::reconnect_canvas` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/observations` | `be1_records.py::create_observation` |
| `GET` | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles/{child_id}/portfolio` | `be1_records.py::read_portfolio` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/data-requests` | `be1_records.py::create_data_request` |
| `GET` | `/api/be1/v1/organizations/{organization_id}/data-requests/{request_id}` | `be1_records.py::read_data_request` |
| `GET` | `/api/be1/v1/organizations/{organization_id}/gallery` | `be1_records.py::list_gallery` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/gallery` | `be1_records.py::create_gallery_snapshot` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/gallery/{gallery_id}/annotations` | `be1_records.py::annotate_gallery` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/gallery/{gallery_id}/publish` | `be1_records.py::publish_gallery` |
| `GET` | `/api/be1/v1/organizations/{organization_id}` | `be1_registry.py::read_organization` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/assignments` | `be1_registry.py::create_assignment` |
| `DELETE` | `/api/be1/v1/organizations/{organization_id}/assignments/{assignment_id}` | `be1_registry.py::revoke_assignment` |
| `GET` | `/api/be1/v1/organizations/{organization_id}/classes` | `be1_registry.py::list_classes` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/classes` | `be1_registry.py::create_class` |
| `GET` | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents` | `be1_registry.py::list_consents` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents` | `be1_registry.py::record_consent` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents/{consent_id}/revoke` | `be1_registry.py::revoke_consent` |
| `GET` | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles` | `be1_registry.py::list_profiles` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles` | `be1_registry.py::create_profile` |
| `GET` | `/api/be1/v1/organizations/{organization_id}/me` | `be1_registry.py::current_assignments` |
| `GET` | `/api/be1/v1/health` | `be1_runtime.py::be1_health` |
| `POST` | `/api/be1/v1/device-grants/{grant_id}/join-status` | `be1_sessions.py::read_join_status` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/sessions` | `be1_sessions.py::create_session` |
| `GET` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}` | `be1_sessions.py::read_session` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/completion` | `be1_sessions.py::complete_session` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/device-grants/{grant_id}/refresh` | `be1_sessions.py::refresh_device_grant` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/finish` | `be1_sessions.py::finish_session` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups` | `be1_sessions.py::create_group` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/control` | `be1_sessions.py::control_group` |
| `PUT` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/members/{child_id}` | `be1_sessions.py::assign_member_to_group` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/turns/{child_id}` | `be1_sessions.py::start_child_turn` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/join` | `be1_sessions.py::request_device_join` |
| `GET` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/join-requests` | `be1_sessions.py::list_join_requests` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/join-requests/{grant_id}/admit` | `be1_sessions.py::admit_device` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/join-requests/{grant_id}/revoke` | `be1_sessions.py::revoke_device_grant` |
| `GET` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/learning-stage` | `be1_sessions.py::read_learning_stage` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/learning-stage/advance` | `be1_sessions.py::advance_learning_stage` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/lobby` | `be1_sessions.py::open_lobby` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/memberships/{membership_id}/help` | `be1_sessions.py::request_help` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/memberships/{membership_id}/leave` | `be1_sessions.py::leave_session` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/memberships/{membership_id}/progress` | `be1_sessions.py::update_progress` |
| `GET` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/outcome` | `be1_sessions.py::read_session_outcome` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/pause` | `be1_sessions.py::pause_session` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/resume` | `be1_sessions.py::resume_session` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/room-code/rotate` | `be1_sessions.py::rotate_room_code` |
| `GET` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/roster` | `be1_sessions.py::read_session_roster` |
| `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/start` | `be1_sessions.py::start_session` |
| `POST` | `/api/be1/v1/room-code/join` | `be1_sessions.py::request_room_code_join` |
| `GET` | `/health` | `health.py::health` |

## Demo / local flow routes

Purpose: legacy/demo session creation, image/audio ingestion and understanding, guided P1 flow, renderer assets, story-video jobs and whiteboard generation. These routes are distinct from the durable BE1 classroom APIs.

| Method | Path | Handler / source |
|---|---|---|
| `POST` | `/v1/profile/preferences/classify` | `child_preferences.py::classify_preferences` |
| `POST` | `/v1/sessions/{session_id}/media/audio` | `images.py::upload_audio` |
| `POST` | `/v1/sessions/{session_id}/media/image` | `images.py::upload_image` |
| `POST` | `/v1/sessions/{session_id}/understanding` | `images.py::run_understanding` |
| `GET` | `/v1/sessions/{session_id}/understanding/progress` | `images.py::read_understanding_progress` |
| `POST` | `/v1/sessions` | `sessions.py::create_session` |
| `GET` | `/v1/sessions/{session_id}` | `sessions.py::get_session` |
| `GET` | `/v1/sessions/{session_id}/story-video-jobs` | `story_video.py::list_story_video_jobs` |
| `POST` | `/v1/sessions/{session_id}/story-video-jobs` | `story_video.py::create_story_video_job` |
| `GET` | `/v1/sessions/{session_id}/story-video/{job_id}` | `story_video.py::get_story_video_status` |
| `GET` | `/v1/sessions/{session_id}/story-video/{job_id}/file` | `story_video.py::stream_story_video` |
| `GET` | `/v1/renderer/pixi-asset` | `supervised_flow.py::read_renderer_pixi_asset` |
| `GET` | `/v1/renderer/rig-mask` | `supervised_flow.py::read_renderer_rig_mask` |
| `GET` | `/v1/renderer/rig-package` | `supervised_flow.py::read_renderer_rig_package` |
| `GET` | `/v1/renderer/source` | `supervised_flow.py::read_renderer_source` |
| `POST` | `/v1/sessions/{session_id}/experience/prepare` | `supervised_flow.py::prepare_experience` |
| `POST` | `/v1/sessions/{session_id}/feedback` | `supervised_flow.py::record_feedback` |
| `GET` | `/v1/sessions/{session_id}/gallery` | `supervised_flow.py::read_gallery` |
| `POST` | `/v1/sessions/{session_id}/gate-a/confirm` | `supervised_flow.py::confirm_gate_a` |
| `POST` | `/v1/sessions/{session_id}/gate-b/approve` | `supervised_flow.py::approve_gate_b` |
| `POST` | `/v1/sessions/{session_id}/handoff` | `supervised_flow.py::complete_handoff` |
| `POST` | `/v1/sessions/{session_id}/media/retake` | `supervised_flow.py::request_retake` |
| `PUT` | `/v1/sessions/{session_id}/p1-context` | `supervised_flow.py::set_p1_context` |
| `POST` | `/v1/sessions/{session_id}/p1-filter` | `supervised_flow.py::run_p1_filter` |
| `POST` | `/v1/sessions/{session_id}/p1/activity-suggestions` | `supervised_flow.py::read_p1_activity_suggestions` |
| `POST` | `/v1/sessions/{session_id}/p1/activity-suggestions/rank` | `supervised_flow.py::rank_p1_activity_suggestions` |
| `GET` | `/v1/sessions/{session_id}/p1/context-candidates` | `supervised_flow.py::read_p1_context_candidates` |
| `GET` | `/v1/sessions/{session_id}/p1/context-options` | `supervised_flow.py::read_p1_context_options` |
| `POST` | `/v1/sessions/{session_id}/p1/context-options` | `supervised_flow.py::read_personalized_p1_context_options` |
| `POST` | `/v1/sessions/{session_id}/p1/context-options/finalize` | `supervised_flow.py::finalize_p1_context_options` |
| `POST` | `/v1/sessions/{session_id}/renderer/launch` | `supervised_flow.py::prepare_renderer` |
| `POST` | `/v1/whiteboard/storyboards/preview` | `whiteboard_storyboard.py::preview_storyboard` |
| `GET` | `/v1/sessions/{session_id}/whiteboard-video` | `whiteboard_video.py::get_whiteboard_video_status` |
| `POST` | `/v1/sessions/{session_id}/whiteboard-video-jobs` | `whiteboard_video.py::create_whiteboard_video_job` |
| `GET` | `/v1/sessions/{session_id}/whiteboard-video/file` | `whiteboard_video.py::stream_whiteboard_video` |

## Lesson Library routes

Purpose: text-only lesson CRUD/versioning, filtered upload/review, Manager publication, school/named/group sharing, Parent read/export and Platform Admin moderation. No AI route is implemented in this slice.

| Method | Path | Handler / source |
|---|---|---|
| `GET` | `/api/lesson-library/v1/me/lesson-invitations` | `lesson_library.py::list_lesson_invitations` |
| `POST` | `/api/lesson-library/v1/me/lesson-invitations/{access_grant_id}/accept` | `lesson_library.py::accept_lesson_invitation` |
| `POST` | `/api/lesson-library/v1/me/lesson-invitations/{access_grant_id}/decline` | `lesson_library.py::decline_lesson_invitation` |
| `GET` | `/api/lesson-library/v1/me/lessons` | `lesson_library.py::list_parent_lessons` |
| `GET` | `/api/lesson-library/v1/me/lessons/{lesson_id}` | `lesson_library.py::get_parent_lesson` |
| `GET` | `/api/lesson-library/v1/me/lessons/{lesson_id}/download` | `lesson_library.py::download_parent_lesson` |
| `GET` | `/api/lesson-library/v1/me/parent-group-invitations` | `lesson_library.py::list_parent_group_invitations` |
| `POST` | `/api/lesson-library/v1/me/parent-group-invitations/{membership_id}/accept` | `lesson_library.py::accept_parent_group_invitation` |
| `GET` | `/api/lesson-library/v1/organizations/{organization_id}/access-grants` | `lesson_library.py::list_access_grants` |
| `POST` | `/api/lesson-library/v1/organizations/{organization_id}/access-grants/{access_grant_id}/decision` | `lesson_library.py::decide_access_grant` |
| `GET` | `/api/lesson-library/v1/organizations/{organization_id}/lessons` | `lesson_library.py::list_lessons` |
| `POST` | `/api/lesson-library/v1/organizations/{organization_id}/lessons` | `lesson_library.py::create_lesson` |
| `DELETE` | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}` | `lesson_library.py::archive_lesson` |
| `GET` | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}` | `lesson_library.py::get_lesson` |
| `PATCH` | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}` | `lesson_library.py::update_lesson` |
| `POST` | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/access-grants` | `lesson_library.py::create_access_grant` |
| `DELETE` | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/access-grants/{access_grant_id}` | `lesson_library.py::revoke_access_grant` |
| `GET` | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/source-documents/{source_document_id}` | `lesson_library.py::get_source_document` |
| `GET` | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/source-documents/{source_document_id}/revisions/{revision_id}` | `lesson_library.py::get_document_revision` |
| `POST` | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/upload-sessions` | `lesson_library.py::create_upload_session` |
| `POST` | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/versions` | `lesson_library.py::create_lesson_version` |
| `GET` | `/api/lesson-library/v1/organizations/{organization_id}/parent-groups` | `lesson_library.py::list_parent_groups` |
| `POST` | `/api/lesson-library/v1/organizations/{organization_id}/parent-groups` | `lesson_library.py::create_parent_group` |
| `POST` | `/api/lesson-library/v1/organizations/{organization_id}/parent-groups/{parent_group_id}/invitations` | `lesson_library.py::invite_parent_to_group` |
| `DELETE` | `/api/lesson-library/v1/organizations/{organization_id}/parent-groups/{parent_group_id}/members/{membership_id}` | `lesson_library.py::revoke_parent_group_membership` |
| `PATCH` | `/api/lesson-library/v1/platform/lessons/{lesson_id}/moderation` | `lesson_library.py::moderate_lesson` |
| `DELETE` | `/api/lesson-library/v1/upload-sessions/{upload_session_id}` | `lesson_library.py::abort_upload_session` |
| `GET` | `/api/lesson-library/v1/upload-sessions/{upload_session_id}` | `lesson_library.py::get_upload_session` |
| `POST` | `/api/lesson-library/v1/upload-sessions/{upload_session_id}/complete` | `lesson_library.py::complete_upload` |
| `PUT` | `/api/lesson-library/v1/upload-sessions/{upload_session_id}/parts/{part_number}` | `lesson_library.py::upload_part` |

## Conditional local storage example

Purpose: synthetic local MinIO upload/read/delete demonstration. It creates no Lesson row and is enabled only for local development.

| Method | Path | Handler / source |
|---|---|---|
| `POST` | `/api/dev/v1/storage-examples/lesson-source-documents` | `storage_examples.py::upload_lesson_source_example` |
| `DELETE` | `/api/dev/v1/storage-examples/lesson-source-documents/{object_id}` | `storage_examples.py::delete_lesson_source_example` |
| `GET` | `/api/dev/v1/storage-examples/lesson-source-documents/{object_id}` | `storage_examples.py::download_lesson_source_example` |

## Candidate, fixture or unmounted routes

These declarations are not included by the combined/classroom/demo router composition. `ai_jobs`, `analysis_corrections`, and `assistance_requests` also have isolated fixture app factories using synthetic `Authorization: Fixture` principals. The remaining routes are candidate factories/source declarations only. Do not treat these as active product endpoints.

| Method | Path | Handler / source |
|---|---|---|
| `POST` | `/api/collaboration/v1/activity-assignments` | `activity_execution.py::execute` |
| `GET` | `/api/collaboration/v1/jobs/{job_id}` | `ai_jobs.py::get_job` |
| `POST` | `/api/collaboration/v1/analysis-results/{analysis_id}/corrections` | `analysis_corrections.py::submit_correction` |
| `POST` | `/api/collaboration/v1/assistance-requests` | `assistance_requests.py::submit` |
| `POST` | `/api/collaboration/v1/assistance-requests/{assistance_id}/cancel` | `assistance_requests.py::cancel` |
| `POST` | `/api/collaboration/v1/knowledge-videos` | `knowledge_video.py::create` |
| `POST` | `/api/collaboration/v1/governance/records` | `learning_content.py::command` |
| `POST` | `/v1/live-understanding` | `live_understanding.py::live_understanding` |
| `POST` | `/api/collaboration/v1/knowledge-videos/{video_id}/failure-dispositions` | `video_failure.py::disposition` |
| `POST` | `/api/collaboration/v1/knowledge-videos/{video_id}/playback` | `video_review.py::playback` |
| `POST` | `/api/collaboration/v1/knowledge-videos/{video_id}/reviews` | `video_review.py::review` |

## FEAT-063 platform requirements not implemented as APIs in Rev31

The inventory above is the current code route surface, not a promise that every broader SRS use case has an endpoint. Rev31 does not add Parent-Teacher child-profile share-grant APIs, LessonOccurrence delivery/history/feedback APIs, AI lesson drafting or sketch-generation APIs, billing/quota APIs, or new Story/video-generation APIs. The existing BE1 profile/classroom APIs and demo Story/video routes remain listed in their current categories; they are not substitutes for the future FEAT-063 product contracts. These capabilities need separate implementation scope and authorization contracts.

## Compatibility and verification notes

- No existing Parent, Teacher, BE1 or demo method/path was changed for Rev31. New Lesson Library routes use `/api/lesson-library/v1` and do not replace the existing Parent/Teacher flow routes.
- The original generic `learning_content` governance command route remains an unmounted candidate; it was not repurposed as a Lesson API.
- Platform Admin authorization is an explicit server-side verified-principal allowlist. Parent route identity resolution currently rejects principals with an active BE1 staff assignment; mixed Parent/Teacher identities need a future identity-role resolution design.
- Parent invitation targets are stored as opaque verified identity subject references; there is no new Parent account-registration/directory API in this implementation.
- Static source review only. No application startup, OpenAPI export, database migration, tests/builds, Docker pull/start, or security validation was performed. Runtime exposure, migration correctness, and ClamAV/MinIO availability remain unverified.
