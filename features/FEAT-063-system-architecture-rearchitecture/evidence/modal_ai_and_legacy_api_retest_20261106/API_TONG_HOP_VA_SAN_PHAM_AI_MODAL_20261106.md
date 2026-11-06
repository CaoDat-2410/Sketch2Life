# API tổng hợp và sản phẩm AI Modal - 2026-11-06

**Kết quả:** đã kiểm tra OpenAPI runtime, chạy regression API/contract và thu thập kết quả worker AI synthetic đã pass. Không gọi inference mới trong lượt này để tránh tốn GPU credit. Có 6 test API/contract fail; nguyên nhân và giới hạn bằng chứng ghi bên dưới.
**Chuẩn:** FEAT-063 SRS v2.4-draft (bản làm việc, chưa phê duyệt chính thức). Nhánh `dev`, baseline `4749451080f49243464d40a464b8f83a03ae77bb`.
**Plan/approval:** `plan/PLAN_REV51_MODAL_AI_AND_LEGACY_API_RETEST_20261106.md`; SHA-256 đã duyệt `B20103A217D7A9623E02279CE0BD82D5BC61141518D820FA683104057B1A6A2F`.

## Kết quả API và regression

| Check | Result |
|---|---|
| `GET /health` | HTTP 200, 0.042 s |
| `GET /docs` | HTTP 200, 0.025 s |
| `GET /openapi.json` | HTTP 200, 0.014 s |
| Live OpenAPI | 111 paths / 124 operations; operationId unique |
| Backend API/contract suite | 1,454 passed, 6 failed / 1,460 collected |
| Modal worker contract suite | 79 passed, 2 skipped; provider calls 0 |
| Inference mới | 0; dùng lại kết quả synthetic đã có |

Inventory gồm đủ 124 operation từ OpenAPI runtime. Regression suite chạy trên test fixtures/container riêng. Chỉ `GET /health` trong các operation của inventory được gọi trực tiếp; `/docs` và `/openapi.json` cũng được kiểm tra read-only. Các API ghi dữ liệu không bị gọi vào database dùng chung. Không có mapping test theo từng operation; xem `api_operations.json` và cột `direct_live_probe_status`. Vì vậy inventory không có nghĩa là 124 endpoint đã được gọi trực tiếp.

### Sáu test fail cần theo dõi

| Test | Kết quả quan sát |
|---|---|
| `tests/contract/test_app_composition.py::test_compatibility_app_preserves_baseline_route_surface` | default create_app composition differs from frozen FEAT-059 route baseline; 76 expected paths vs 17 default-profile paths; 68 missing/method-changed |
| `tests/contract/test_app_composition.py::test_classroom_profile_excludes_process_local_demo_routes` | create_classroom_app omits root /health expected by test |
| `tests/contract/test_app_composition.py::test_demo_profile_excludes_durable_classroom_routes` | create_demo_app publishes zero paths in this test environment; expected /v1/sessions |
| `tests/contract/test_be1_synthetic_pilot.py::test_five_other_canvas_sites_keep_the_legal_helper[reconnect_canvas]` | static AST assertion expects direct _require_group_consent; implementation uses _require_group_eligibility; review call chain separately |
| `tests/contract/test_session_http_api.py::test_openapi_exposes_session_contract_but_not_legacy_audio_route` | test app OpenAPI lacks /v1/sessions |
| `tests/contract/test_sketch_review_contracts.py::test_rv_c02_shared_pack_bytes_unchanged_from_baseline` | test runner container has no git executable; test assertion not evaluated |

Các test composition/session/compatibility chưa được sửa trong task này vì không phải lỗi Modal AI và cần plan sửa riêng. Lỗi AST `reconnect_canvas` mới xác nhận là khác helper mà test mong đợi; chưa chứng minh HTTP request sai policy. Test RV-C02 không thể đánh giá vì container thiếu `git`.

## Trạng thái AI Modal

| Workload | Model / kết quả worker | Trạng thái API sản phẩm |
|---|---|---|
| `drawing.analyze` | Qwen/Qwen3.5-9B@c202236235762e1c871ad0ccb60c8ee5ba337b9a; PASS; 44.014 s | Synthetic worker passed; authenticated durable Parent API is not established. Historical StoryRun-lite HTTP request ended UNKNOWN after 303.762 s; no worker-stage log. |
| `story.generate + storyboard.generate` | Qwen/Qwen3.5-9B@c202236235762e1c871ad0ccb60c8ee5ba337b9a; PASS; 113.381 s | Worker returned 5 Vietnamese scenes / 30 s. Historical API test (before Qwen3.5-only migration) returned 502 STORY_OUTPUT_INVALID after EDUCATIONAL_FACT_INVALID; no current API inference repeated. |
| `parent.sketch-guide.generate` | FLUX.3 Image Klein (pinned Rev46A); PASS; 65.772 s | Synthetic 3-panel 768x512 private DRAFT; dedicated authenticated product dispatch route not established. |
| `teacher.sketch-deck.generate` | Qwen/Qwen3.5-9B@c202236235762e1c871ad0ccb60c8ee5ba337b9a; PASS; 43.464 s | 5-slide 16:9 draft, 4 drawing steps, 2 approved activity refs; durable Teacher occurrence/deck API remains absent. |
| `lesson.plan.suggest` | Qwen/Qwen3.5-9B@c202236235762e1c871ad0ccb60c8ee5ba337b9a; PASS; 61.636 s | Synthetic draft_only output passed; durable authenticated API/job persistence remains absent. SRS role boundary: Platform Admin/Teacher generate; Parent edits only. |
| `lesson.visual.generate` | FLUX.3 Image Klein (pinned Rev46A); PASS; 47.206 s | Synthetic 3-panel 768x432 private DRAFT with lesson lineage; dedicated authenticated product route absent. |
| `tts.narration.generate` | VieNeu-TTS-v3-Turbo + MOSS-Audio-Tokenizer-Nano-ONNX; PASS; 19.161 s | Synthetic Vietnamese WAV created; durable product dispatch API absent. |
| `asr.transcribe` | faster-whisper-large-v3; PASS; 23.9 s | Exact synthetic Vietnamese transcript returned; durable product dispatch API absent. |
| `drawing.segment` | SAM 2.1 Hiera-Small (optional); BLOCKED; 1800 s | Checkpoint verified; previous call waited 1,800 s for GPU_L4 scheduling and produced no mask. Dedicated product API absent. Not retried because no dev app is currently deployed and unchanged retry would repeat the known capacity wait. |
| `video.scene.generate / validate / compose / final-safety` | LTX-2.5 remains target; not exercised; EXCLUDED_BY_OWNER; n/a s | No video calls or product claims in this pass. |

Worker pass chỉ xác nhận handler/model trả output theo fixture. Điều đó không chứng minh product API đã có authentication, job state bền vững, quota admission, lưu trữ hay safety acceptance. Các workload vẫn disabled. Video không được gọi theo phạm vi đã chốt.

## Timeout và nguyên nhân

- Không có log nào trong lượt này cho thấy worker inference bị cắt bởi execution timeout; vì thế không tăng timeout cấu hình.
- `drawing.segment`/SAM 2.1 từng chờ 1.800 giây ở bước xếp lịch `GPU_L4`, không có mask và không có bằng chứng model bắt đầu chạy. Đây là capacity/scheduling wait, không phải inference chậm; tăng execution timeout không giải quyết được queue.
- Parent drawing API có một kết quả lịch sử `ModalFunctionOutcomeUnknown` sau 303.762 giây, không có worker-stage log. Chưa xác định được request đã vào model hay chưa; không gán nguyên nhân chắc chắn là GPU queue.
- Story API lỗi lịch sử do `EDUCATIONAL_FACT_INVALID` khi kiểm tra nội dung, không phải timeout. Output bị guard từ chối theo business rule.

## Modal apps

Modal CLI 1.6.3, profile `docaodat24-10`, môi trường `dev`: lệnh `modal app list --env dev` trả danh sách rỗng. Task này không deploy/gọi app nào, không có task-owned app/task cần tắt. Hai shared Volumes không bị thay đổi; không đọc secret/token. Snapshot nằm trong `modal_dev_app_inventory.json`.

## Sản phẩm synthetic được gom

16 file output synthetic/historical được sao chép nguyên bản từ evidence gốc; không tạo lại trong task này. `artifact_manifest.json` ghi nguồn, kích thước, SHA-256, tính synthetic và `generated_in_this_task=false`.

| File | Loại sản phẩm |
|---|---|
| `products/qwen_drawing_analysis.json` | Qwen worker output or companion result; SHA-256 `a77802ccb49563e875a2a1c5f680f26f94e1cddf5dcfe32f5c11661b777ce5e0` |
| `products/qwen_story_worker_result.json` | Qwen worker output or companion result; SHA-256 `a46291c7b06065ed3ace343a1477453a17f89f288bfdf867c64eb05ef401fbc7` |
| `products/qwen_storyboard_worker_result.json` | Qwen worker output or companion result; SHA-256 `171c4179203338f4652880ddc53707f99d61dc751f5eae32b4cb1442af181745` |
| `products/qwen_teacher_sketch_deck.json` | Qwen worker output or companion result; SHA-256 `d58893adbcd38e5d3e1e847d8de5d7888144e5734044ad77b9715ca55236e77c` |
| `products/qwen_lesson_plan_suggestion.json` | Qwen worker output or companion result; SHA-256 `eae8870b2c820d367c767f8a8c5e546aa6d561028073fec19182bd9b240884dc` |
| `products/synthetic_vietnamese_narration.wav` | Synthetic Vietnamese narration audio; SHA-256 `969bc864861624da7a620af4264b5bfb5bb14475f986896121859a0b6462a2df` |
| `products/whisper_asr_result.json` | Whisper ASR result; SHA-256 `5134309b62d914474e9e227aba3ce65a45a19dae04ce855d7a6325d7be7ac885` |
| `products/flux_parent_sketch_guide.png` | FLUX.3 image; SHA-256 `ee22f36b5b9a465bffd08c826f52bd8570436a7f900aca01dce08a4105d0686d` |
| `products/flux_parent_sketch_guide_result.json` | Qwen worker output or companion result; SHA-256 `cf4370cda181de183635aa4786449ef750a8c16958390c37b520022713b1eeec` |
| `products/flux_lesson_visual.png` | FLUX.3 image; SHA-256 `a5ca6981ec5418d9cfa13aa86a5adcf347753307d9111d79760f6f95365288b2` |
| `products/flux_lesson_visual_result.json` | Qwen worker output or companion result; SHA-256 `30dd124b9b3be595e01387dff01abdfb856536722411a92bfc0ff993f1761d21` |
| `products/sam2_timeout_result.json` | SAM2 timeout record; SHA-256 `74af5cec58dd794ddc53a560ff864fe34c4777f8bcaf7cd69c83dbea9eea4be4` |
| `products/parent_story_api_trace_safe.json` | Parent StoryRun API trace/result; SHA-256 `b45109275f04378dd1b2e217abf16b150123327bec12d279e6de27fa28c294fa` |
| `products/parent_story_api_result_summary_safe.json` | Parent StoryRun API trace/result; SHA-256 `cb0e954c8a9a8c170cefd69c4fae0a4520cf0350663bab4087d644caadc754e9` |
| `products/parent_story_api_drawing_unknown.json` | Parent StoryRun API trace/result; SHA-256 `65882b7ee374f69a7e6a80ca313e03ba48845225694493cd40ccb445229a9b6c` |
| `products/parent_story_api_story_rejected.json` | Parent StoryRun API trace/result; SHA-256 `6061c7e8937cdfd193fa621044406bb3812530c752e962067de9c272dc297b89` |

## Toàn bộ API operation runtime

Danh sách dưới lấy từ OpenAPI runtime. Mô tải là operation summary do app công bố; nó không phải xác nhận rằng endpoint đã được gọi trực tiếp.

| # | Method | Path | Operation ID | Tag | Responses | Purpose | Live probe |
|---:|---|---|---|---|---|---|---|
| 1 | `POST` | `/api/be1/v1/device-grants/{grant_id}/join-status` | `read_join_status_api_be1_v1_device_grants__grant_id__join_status_post` | BE1 sessions | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Read Join Status | not_called |
| 2 | `GET` | `/api/be1/v1/health` | `be1_health_api_be1_v1_health_get` | BE1 runtime v1 | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Be1 Health | not_called |
| 3 | `GET` | `/api/be1/v1/organizations/{organization_id}` | `read_organization_api_be1_v1_organizations__organization_id__get` | BE1 registry | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Read Organization | not_called |
| 4 | `POST` | `/api/be1/v1/organizations/{organization_id}/assignments` | `create_assignment_api_be1_v1_organizations__organization_id__assignments_post` | BE1 registry | 201, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Create Assignment | not_called |
| 5 | `DELETE` | `/api/be1/v1/organizations/{organization_id}/assignments/{assignment_id}` | `revoke_assignment_api_be1_v1_organizations__organization_id__assignments__assignment_id__delete` | BE1 registry | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Revoke Assignment | not_called |
| 6 | `GET` | `/api/be1/v1/organizations/{organization_id}/classes` | `list_classes_api_be1_v1_organizations__organization_id__classes_get` | BE1 registry | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | List Classes | not_called |
| 7 | `POST` | `/api/be1/v1/organizations/{organization_id}/classes` | `create_class_api_be1_v1_organizations__organization_id__classes_post` | BE1 registry | 201, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Create Class | not_called |
| 8 | `GET` | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents` | `list_consents_api_be1_v1_organizations__organization_id__classes__class_id__consents_get` | BE1 registry | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | List Consents | not_called |
| 9 | `POST` | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents` | `record_consent_api_be1_v1_organizations__organization_id__classes__class_id__consents_post` | BE1 registry | 201, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Record Consent | not_called |
| 10 | `POST` | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents/{consent_id}/revoke` | `revoke_consent_api_be1_v1_organizations__organization_id__classes__class_id__consents__consent_id__revoke_post` | BE1 registry | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Revoke Consent | not_called |
| 11 | `POST` | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/observations` | `create_observation_api_be1_v1_organizations__organization_id__classes__class_id__observations_post` | BE1 records and lifecycle | 201, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Create Observation | not_called |
| 12 | `GET` | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles` | `list_profiles_api_be1_v1_organizations__organization_id__classes__class_id__profiles_get` | BE1 registry | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | List Profiles | not_called |
| 13 | `POST` | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles` | `create_profile_api_be1_v1_organizations__organization_id__classes__class_id__profiles_post` | BE1 registry | 201, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Create Profile | not_called |
| 14 | `GET` | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles/{child_id}/portfolio` | `read_portfolio_api_be1_v1_organizations__organization_id__classes__class_id__profiles__child_id__portfolio_get` | BE1 records and lifecycle | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Read Portfolio | not_called |
| 15 | `POST` | `/api/be1/v1/organizations/{organization_id}/data-requests` | `create_data_request_api_be1_v1_organizations__organization_id__data_requests_post` | BE1 records and lifecycle | 202, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Create Data Request | not_called |
| 16 | `GET` | `/api/be1/v1/organizations/{organization_id}/data-requests/{request_id}` | `read_data_request_api_be1_v1_organizations__organization_id__data_requests__request_id__get` | BE1 records and lifecycle | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Read Data Request | not_called |
| 17 | `GET` | `/api/be1/v1/organizations/{organization_id}/gallery` | `list_gallery_api_be1_v1_organizations__organization_id__gallery_get` | BE1 records and lifecycle | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | List Gallery | not_called |
| 18 | `POST` | `/api/be1/v1/organizations/{organization_id}/gallery` | `create_gallery_snapshot_api_be1_v1_organizations__organization_id__gallery_post` | BE1 records and lifecycle | 201, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Create Gallery Snapshot | not_called |
| 19 | `POST` | `/api/be1/v1/organizations/{organization_id}/gallery/{gallery_id}/annotations` | `annotate_gallery_api_be1_v1_organizations__organization_id__gallery__gallery_id__annotations_post` | BE1 records and lifecycle | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Annotate Gallery | not_called |
| 20 | `POST` | `/api/be1/v1/organizations/{organization_id}/gallery/{gallery_id}/publish` | `publish_gallery_api_be1_v1_organizations__organization_id__gallery__gallery_id__publish_post` | BE1 records and lifecycle | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Publish Gallery | not_called |
| 21 | `GET` | `/api/be1/v1/organizations/{organization_id}/me` | `current_assignments_api_be1_v1_organizations__organization_id__me_get` | BE1 registry | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Current Assignments | not_called |
| 22 | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions` | `create_session_api_be1_v1_organizations__organization_id__sessions_post` | BE1 sessions | 201, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Create Session | not_called |
| 23 | `GET` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}` | `read_session_api_be1_v1_organizations__organization_id__sessions__session_id__get` | BE1 sessions | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Read Session | not_called |
| 24 | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/artifacts` | `upload_session_artifact_api_be1_v1_organizations__organization_id__sessions__session_id__artifacts_post` | BE1 artifacts | 201, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Upload Session Artifact | not_called |
| 25 | `GET` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/artifacts/{asset_ref}` | `download_session_artifact_api_be1_v1_organizations__organization_id__sessions__session_id__artifacts__asset_ref__get` | BE1 artifacts | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Download Session Artifact | not_called |
| 26 | `GET` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/canvas/operations` | `sync_canvas_operations_api_be1_v1_organizations__organization_id__sessions__session_id__canvas_operations_get` | BE1 canvas | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Sync Canvas Operations | not_called |
| 27 | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/canvas/operations` | `append_canvas_operation_api_be1_v1_organizations__organization_id__sessions__session_id__canvas_operations_post` | BE1 canvas | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Append Canvas Operation | not_called |
| 28 | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/completion` | `complete_session_api_be1_v1_organizations__organization_id__sessions__session_id__completion_post` | BE1 sessions | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Complete Session | not_called |
| 29 | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/device-grants/{grant_id}/refresh` | `refresh_device_grant_api_be1_v1_organizations__organization_id__sessions__session_id__device_grants__grant_id__refresh_post` | BE1 sessions | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Refresh Device Grant | not_called |
| 30 | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/finish` | `finish_session_api_be1_v1_organizations__organization_id__sessions__session_id__finish_post` | BE1 sessions | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Finish Session | not_called |
| 31 | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups` | `create_group_api_be1_v1_organizations__organization_id__sessions__session_id__groups_post` | BE1 sessions | 201, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Create Group | not_called |
| 32 | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/checkpoints` | `save_checkpoint_api_be1_v1_organizations__organization_id__sessions__session_id__groups__group_id__checkpoints_post` | BE1 canvas | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Save Checkpoint | not_called |
| 33 | `GET` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/checkpoints/latest` | `read_latest_checkpoint_api_be1_v1_organizations__organization_id__sessions__session_id__groups__group_id__checkpoints_latest_get` | BE1 canvas | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Read Latest Checkpoint | not_called |
| 34 | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/control` | `control_group_api_be1_v1_organizations__organization_id__sessions__session_id__groups__group_id__control_post` | BE1 sessions | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Control Group | not_called |
| 35 | `PUT` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/members/{child_id}` | `assign_member_to_group_api_be1_v1_organizations__organization_id__sessions__session_id__groups__group_id__members__child_id__put` | BE1 sessions | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Assign Member To Group | not_called |
| 36 | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/restore` | `restore_checkpoint_api_be1_v1_organizations__organization_id__sessions__session_id__groups__group_id__restore_post` | BE1 canvas | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Restore Checkpoint | not_called |
| 37 | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/turns/{child_id}` | `start_child_turn_api_be1_v1_organizations__organization_id__sessions__session_id__groups__group_id__turns__child_id__post` | BE1 sessions | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Start Child Turn | not_called |
| 38 | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/join` | `request_device_join_api_be1_v1_organizations__organization_id__sessions__session_id__join_post` | BE1 sessions | 202, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Request Device Join | not_called |
| 39 | `GET` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/join-requests` | `list_join_requests_api_be1_v1_organizations__organization_id__sessions__session_id__join_requests_get` | BE1 sessions | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | List Join Requests | not_called |
| 40 | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/join-requests/{grant_id}/admit` | `admit_device_api_be1_v1_organizations__organization_id__sessions__session_id__join_requests__grant_id__admit_post` | BE1 sessions | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Admit Device | not_called |
| 41 | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/join-requests/{grant_id}/revoke` | `revoke_device_grant_api_be1_v1_organizations__organization_id__sessions__session_id__join_requests__grant_id__revoke_post` | BE1 sessions | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Revoke Device Grant | not_called |
| 42 | `GET` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/learning-stage` | `read_learning_stage_api_be1_v1_organizations__organization_id__sessions__session_id__learning_stage_get` | BE1 sessions | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Read Learning Stage | not_called |
| 43 | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/learning-stage/advance` | `advance_learning_stage_api_be1_v1_organizations__organization_id__sessions__session_id__learning_stage_advance_post` | BE1 sessions | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Advance Learning Stage | not_called |
| 44 | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/lobby` | `open_lobby_api_be1_v1_organizations__organization_id__sessions__session_id__lobby_post` | BE1 sessions | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Open Lobby | not_called |
| 45 | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/memberships/{membership_id}/help` | `request_help_api_be1_v1_organizations__organization_id__sessions__session_id__memberships__membership_id__help_post` | BE1 sessions | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Request Help | not_called |
| 46 | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/memberships/{membership_id}/leave` | `leave_session_api_be1_v1_organizations__organization_id__sessions__session_id__memberships__membership_id__leave_post` | BE1 sessions | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Leave Session | not_called |
| 47 | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/memberships/{membership_id}/progress` | `update_progress_api_be1_v1_organizations__organization_id__sessions__session_id__memberships__membership_id__progress_post` | BE1 sessions | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Update Progress | not_called |
| 48 | `GET` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/outcome` | `read_session_outcome_api_be1_v1_organizations__organization_id__sessions__session_id__outcome_get` | BE1 sessions | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Read Session Outcome | not_called |
| 49 | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/pause` | `pause_session_api_be1_v1_organizations__organization_id__sessions__session_id__pause_post` | BE1 sessions | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Pause Session | not_called |
| 50 | `GET` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/reconnect` | `reconnect_canvas_api_be1_v1_organizations__organization_id__sessions__session_id__reconnect_get` | BE1 canvas | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Reconnect Canvas | not_called |
| 51 | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/resume` | `resume_session_api_be1_v1_organizations__organization_id__sessions__session_id__resume_post` | BE1 sessions | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Resume Session | not_called |
| 52 | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/room-code/rotate` | `rotate_room_code_api_be1_v1_organizations__organization_id__sessions__session_id__room_code_rotate_post` | BE1 sessions | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Rotate Room Code | not_called |
| 53 | `GET` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/roster` | `read_session_roster_api_be1_v1_organizations__organization_id__sessions__session_id__roster_get` | BE1 sessions | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Read Session Roster | not_called |
| 54 | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/start` | `start_session_api_be1_v1_organizations__organization_id__sessions__session_id__start_post` | BE1 sessions | 200, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Start Session | not_called |
| 55 | `POST` | `/api/be1/v1/room-code/join` | `request_room_code_join_api_be1_v1_room_code_join_post` | BE1 sessions | 202, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503 | Request Room Code Join | not_called |
| 56 | `POST` | `/api/dev/v1/storage-examples/lesson-source-documents` | `upload_lesson_source_example_api_dev_v1_storage_examples_lesson_source_documents_post` | local-storage-example | 201, 422 | Upload a local lesson-source storage example | not_called |
| 57 | `DELETE` | `/api/dev/v1/storage-examples/lesson-source-documents/{object_id}` | `delete_lesson_source_example_api_dev_v1_storage_examples_lesson_source_documents__object_id__delete` | local-storage-example | 204, 422 | Delete a local lesson-source storage example | not_called |
| 58 | `GET` | `/api/dev/v1/storage-examples/lesson-source-documents/{object_id}` | `download_lesson_source_example_api_dev_v1_storage_examples_lesson_source_documents__object_id__get` | local-storage-example | 200, 422 | Stream a local lesson-source storage example | not_called |
| 59 | `GET` | `/api/lesson-library/v1/me/lesson-invitations` | `list_lesson_invitations_api_lesson_library_v1_me_lesson_invitations_get` | Lesson Library v1 | 200, 422 | List Lesson Invitations | not_called |
| 60 | `POST` | `/api/lesson-library/v1/me/lesson-invitations/{access_grant_id}/accept` | `accept_lesson_invitation_api_lesson_library_v1_me_lesson_invitations__access_grant_id__accept_post` | Lesson Library v1 | 200, 422 | Accept Lesson Invitation | not_called |
| 61 | `POST` | `/api/lesson-library/v1/me/lesson-invitations/{access_grant_id}/decline` | `decline_lesson_invitation_api_lesson_library_v1_me_lesson_invitations__access_grant_id__decline_post` | Lesson Library v1 | 200, 422 | Decline Lesson Invitation | not_called |
| 62 | `GET` | `/api/lesson-library/v1/me/lessons` | `list_parent_lessons_api_lesson_library_v1_me_lessons_get` | Lesson Library v1 | 200, 422 | List Parent Lessons | not_called |
| 63 | `GET` | `/api/lesson-library/v1/me/lessons/{lesson_id}` | `get_parent_lesson_api_lesson_library_v1_me_lessons__lesson_id__get` | Lesson Library v1 | 200, 422 | Get Parent Lesson | not_called |
| 64 | `GET` | `/api/lesson-library/v1/me/lessons/{lesson_id}/download` | `download_parent_lesson_api_lesson_library_v1_me_lessons__lesson_id__download_get` | Lesson Library v1 | 200, 422 | Download Parent Lesson | not_called |
| 65 | `GET` | `/api/lesson-library/v1/me/parent-group-invitations` | `list_parent_group_invitations_api_lesson_library_v1_me_parent_group_invitations_get` | Lesson Library v1 | 200, 422 | List Parent Group Invitations | not_called |
| 66 | `POST` | `/api/lesson-library/v1/me/parent-group-invitations/{membership_id}/accept` | `accept_parent_group_invitation_api_lesson_library_v1_me_parent_group_invitations__membership_id__accept_post` | Lesson Library v1 | 200, 422 | Accept Parent Group Invitation | not_called |
| 67 | `GET` | `/api/lesson-library/v1/organizations/{organization_id}/access-grants` | `list_access_grants_api_lesson_library_v1_organizations__organization_id__access_grants_get` | Lesson Library v1 | 200, 422 | List Access Grants | not_called |
| 68 | `POST` | `/api/lesson-library/v1/organizations/{organization_id}/access-grants/{access_grant_id}/decision` | `decide_access_grant_api_lesson_library_v1_organizations__organization_id__access_grants__access_grant_id__decision_post` | Lesson Library v1 | 200, 422 | Decide Access Grant | not_called |
| 69 | `GET` | `/api/lesson-library/v1/organizations/{organization_id}/lessons` | `list_lessons_api_lesson_library_v1_organizations__organization_id__lessons_get` | Lesson Library v1 | 200, 422 | List Lessons | not_called |
| 70 | `POST` | `/api/lesson-library/v1/organizations/{organization_id}/lessons` | `create_lesson_api_lesson_library_v1_organizations__organization_id__lessons_post` | Lesson Library v1 | 201, 422 | Create Lesson | not_called |
| 71 | `DELETE` | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}` | `archive_lesson_api_lesson_library_v1_organizations__organization_id__lessons__lesson_id__delete` | Lesson Library v1 | 200, 422 | Archive Lesson | not_called |
| 72 | `GET` | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}` | `get_lesson_api_lesson_library_v1_organizations__organization_id__lessons__lesson_id__get` | Lesson Library v1 | 200, 422 | Get Lesson | not_called |
| 73 | `PATCH` | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}` | `update_lesson_api_lesson_library_v1_organizations__organization_id__lessons__lesson_id__patch` | Lesson Library v1 | 200, 422 | Update Lesson | not_called |
| 74 | `POST` | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/access-grants` | `create_access_grant_api_lesson_library_v1_organizations__organization_id__lessons__lesson_id__access_grants_post` | Lesson Library v1 | 201, 422 | Create Access Grant | not_called |
| 75 | `DELETE` | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/access-grants/{access_grant_id}` | `revoke_access_grant_api_lesson_library_v1_organizations__organization_id__lessons__lesson_id__access_grants__access_grant_id__delete` | Lesson Library v1 | 200, 422 | Revoke Access Grant | not_called |
| 76 | `GET` | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/source-documents/{source_document_id}` | `get_source_document_api_lesson_library_v1_organizations__organization_id__lessons__lesson_id__source_documents__source_document_id__get` | Lesson Library v1 | 200, 422 | Get Source Document | not_called |
| 77 | `GET` | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/source-documents/{source_document_id}/revisions/{revision_id}` | `get_document_revision_api_lesson_library_v1_organizations__organization_id__lessons__lesson_id__source_documents__source_document_id__revisions__revision_id__get` | Lesson Library v1 | 200, 422 | Get Document Revision | not_called |
| 78 | `POST` | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/upload-sessions` | `create_upload_session_api_lesson_library_v1_organizations__organization_id__lessons__lesson_id__upload_sessions_post` | Lesson Library v1 | 201, 422 | Create Upload Session | not_called |
| 79 | `POST` | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/versions` | `create_lesson_version_api_lesson_library_v1_organizations__organization_id__lessons__lesson_id__versions_post` | Lesson Library v1 | 201, 422 | Create Lesson Version | not_called |
| 80 | `GET` | `/api/lesson-library/v1/organizations/{organization_id}/parent-groups` | `list_parent_groups_api_lesson_library_v1_organizations__organization_id__parent_groups_get` | Lesson Library v1 | 200, 422 | List Parent Groups | not_called |
| 81 | `POST` | `/api/lesson-library/v1/organizations/{organization_id}/parent-groups` | `create_parent_group_api_lesson_library_v1_organizations__organization_id__parent_groups_post` | Lesson Library v1 | 201, 422 | Create Parent Group | not_called |
| 82 | `POST` | `/api/lesson-library/v1/organizations/{organization_id}/parent-groups/{parent_group_id}/invitations` | `invite_parent_to_group_api_lesson_library_v1_organizations__organization_id__parent_groups__parent_group_id__invitations_post` | Lesson Library v1 | 201, 422 | Invite Parent To Group | not_called |
| 83 | `DELETE` | `/api/lesson-library/v1/organizations/{organization_id}/parent-groups/{parent_group_id}/members/{membership_id}` | `revoke_parent_group_membership_api_lesson_library_v1_organizations__organization_id__parent_groups__parent_group_id__members__membership_id__delete` | Lesson Library v1 | 200, 422 | Revoke Parent Group Membership | not_called |
| 84 | `PATCH` | `/api/lesson-library/v1/platform/lessons/{lesson_id}/moderation` | `moderate_lesson_api_lesson_library_v1_platform_lessons__lesson_id__moderation_patch` | Lesson Library v1 | 200, 422 | Moderate Lesson | not_called |
| 85 | `DELETE` | `/api/lesson-library/v1/upload-sessions/{upload_session_id}` | `abort_upload_session_api_lesson_library_v1_upload_sessions__upload_session_id__delete` | Lesson Library v1 | 200, 422 | Abort Upload Session | not_called |
| 86 | `GET` | `/api/lesson-library/v1/upload-sessions/{upload_session_id}` | `get_upload_session_api_lesson_library_v1_upload_sessions__upload_session_id__get` | Lesson Library v1 | 200, 422 | Get Upload Session | not_called |
| 87 | `POST` | `/api/lesson-library/v1/upload-sessions/{upload_session_id}/complete` | `complete_upload_api_lesson_library_v1_upload_sessions__upload_session_id__complete_post` | Lesson Library v1 | 200, 422 | Complete Upload | not_called |
| 88 | `PUT` | `/api/lesson-library/v1/upload-sessions/{upload_session_id}/parts/{part_number}` | `upload_part_api_lesson_library_v1_upload_sessions__upload_session_id__parts__part_number__put` | Lesson Library v1 | 200, 422 | Upload Part | not_called |
| 89 | `GET` | `/health` | `health_health_get` | health | 200 | Health | 200 (0.042 s) |
| 90 | `POST` | `/v1/profile/preferences/classify` | `classify_preferences_v1_profile_preferences_classify_post` | child-preferences | 200, 422 | Classify Preferences | not_called |
| 91 | `GET` | `/v1/renderer/pixi-asset` | `read_renderer_pixi_asset_v1_renderer_pixi_asset_get` | renderer | 200, 422 | Read Renderer Pixi Asset | not_called |
| 92 | `GET` | `/v1/renderer/rig-mask` | `read_renderer_rig_mask_v1_renderer_rig_mask_get` | renderer | 200, 422 | Read Renderer Rig Mask | not_called |
| 93 | `GET` | `/v1/renderer/rig-package` | `read_renderer_rig_package_v1_renderer_rig_package_get` | renderer | 200, 422 | Read Renderer Rig Package | not_called |
| 94 | `GET` | `/v1/renderer/source` | `read_renderer_source_v1_renderer_source_get` | renderer | 200, 422 | Read Renderer Source | not_called |
| 95 | `POST` | `/v1/sessions` | `create_session_v1_sessions_post` | sessions | 201, 422 | Create Session | not_called |
| 96 | `GET` | `/v1/sessions/{session_id}` | `get_session_v1_sessions__session_id__get` | sessions | 200, 422 | Get Session | not_called |
| 97 | `POST` | `/v1/sessions/{session_id}/experience/prepare` | `prepare_experience_v1_sessions__session_id__experience_prepare_post` | supervised-flow | 200, 422 | Prepare Experience | not_called |
| 98 | `POST` | `/v1/sessions/{session_id}/feedback` | `record_feedback_v1_sessions__session_id__feedback_post` | supervised-flow | 200, 422 | Record Feedback | not_called |
| 99 | `GET` | `/v1/sessions/{session_id}/gallery` | `read_gallery_v1_sessions__session_id__gallery_get` | supervised-flow | 200, 422 | Read Gallery | not_called |
| 100 | `POST` | `/v1/sessions/{session_id}/gate-a/confirm` | `confirm_gate_a_v1_sessions__session_id__gate_a_confirm_post` | supervised-flow | 200, 422 | Confirm Gate A | not_called |
| 101 | `POST` | `/v1/sessions/{session_id}/gate-b/approve` | `approve_gate_b_v1_sessions__session_id__gate_b_approve_post` | supervised-flow | 200, 422 | Approve Gate B | not_called |
| 102 | `POST` | `/v1/sessions/{session_id}/handoff` | `complete_handoff_v1_sessions__session_id__handoff_post` | supervised-flow | 200, 422 | Complete Handoff | not_called |
| 103 | `POST` | `/v1/sessions/{session_id}/media/audio` | `upload_audio_v1_sessions__session_id__media_audio_post` | image-demo | 200, 413, 422 | Upload optional session-local narration audio | not_called |
| 104 | `POST` | `/v1/sessions/{session_id}/media/image` | `upload_image_v1_sessions__session_id__media_image_post` | image-demo | 200, 413, 422 | Upload and admit one synthetic non-child image | not_called |
| 105 | `POST` | `/v1/sessions/{session_id}/media/retake` | `request_retake_v1_sessions__session_id__media_retake_post` | supervised-flow | 200, 422 | Request Retake | not_called |
| 106 | `PUT` | `/v1/sessions/{session_id}/p1-context` | `set_p1_context_v1_sessions__session_id__p1_context_put` | supervised-flow | 200, 422 | Set P1 Context | not_called |
| 107 | `POST` | `/v1/sessions/{session_id}/p1-filter` | `run_p1_filter_v1_sessions__session_id__p1_filter_post` | supervised-flow | 200, 422 | Run P1 Filter | not_called |
| 108 | `POST` | `/v1/sessions/{session_id}/p1/activity-suggestions` | `read_p1_activity_suggestions_v1_sessions__session_id__p1_activity_suggestions_post` | supervised-flow | 200, 422 | Read P1 Activity Suggestions | not_called |
| 109 | `POST` | `/v1/sessions/{session_id}/p1/activity-suggestions/rank` | `rank_p1_activity_suggestions_v1_sessions__session_id__p1_activity_suggestions_rank_post` | supervised-flow | 200, 422 | Rank P1 Activity Suggestions | not_called |
| 110 | `GET` | `/v1/sessions/{session_id}/p1/context-candidates` | `read_p1_context_candidates_v1_sessions__session_id__p1_context_candidates_get` | supervised-flow | 200, 422 | Read P1 Context Candidates | not_called |
| 111 | `GET` | `/v1/sessions/{session_id}/p1/context-options` | `read_p1_context_options_v1_sessions__session_id__p1_context_options_get` | supervised-flow | 200, 422 | Read P1 Context Options | not_called |
| 112 | `POST` | `/v1/sessions/{session_id}/p1/context-options` | `read_personalized_p1_context_options_v1_sessions__session_id__p1_context_options_post` | supervised-flow | 200, 422 | Read Personalized P1 Context Options | not_called |
| 113 | `POST` | `/v1/sessions/{session_id}/p1/context-options/finalize` | `finalize_p1_context_options_v1_sessions__session_id__p1_context_options_finalize_post` | supervised-flow | 200, 422 | Finalize P1 Context Options | not_called |
| 114 | `POST` | `/v1/sessions/{session_id}/renderer/launch` | `prepare_renderer_v1_sessions__session_id__renderer_launch_post` | supervised-flow | 200, 422 | Prepare Renderer | not_called |
| 115 | `GET` | `/v1/sessions/{session_id}/story-video-jobs` | `list_story_video_jobs_v1_sessions__session_id__story_video_jobs_get` | story-video | 200, 422 | List Story Video Jobs | not_called |
| 116 | `POST` | `/v1/sessions/{session_id}/story-video-jobs` | `create_story_video_job_v1_sessions__session_id__story_video_jobs_post` | story-video | 201, 422 | Create Story Video Job | not_called |
| 117 | `GET` | `/v1/sessions/{session_id}/story-video/{job_id}` | `get_story_video_status_v1_sessions__session_id__story_video__job_id__get` | story-video | 200, 422 | Get Story Video Status | not_called |
| 118 | `GET` | `/v1/sessions/{session_id}/story-video/{job_id}/file` | `stream_story_video_v1_sessions__session_id__story_video__job_id__file_get` | story-video | 200, 422 | Stream Story Video | not_called |
| 119 | `POST` | `/v1/sessions/{session_id}/understanding` | `run_understanding_v1_sessions__session_id__understanding_post` | image-demo | 200, 422 | Explicitly run optional narration then Vision V2 understanding | not_called |
| 120 | `GET` | `/v1/sessions/{session_id}/understanding/progress` | `read_understanding_progress_v1_sessions__session_id__understanding_progress_get` | image-demo | 200, 422 | Read the last sanitized understanding stage projection | not_called |
| 121 | `GET` | `/v1/sessions/{session_id}/whiteboard-video` | `get_whiteboard_video_status_v1_sessions__session_id__whiteboard_video_get` | whiteboard-video | 200, 422 | Get Whiteboard Video Status | not_called |
| 122 | `POST` | `/v1/sessions/{session_id}/whiteboard-video-jobs` | `create_whiteboard_video_job_v1_sessions__session_id__whiteboard_video_jobs_post` | whiteboard-video | 201, 422 | Create Whiteboard Video Job | not_called |
| 123 | `GET` | `/v1/sessions/{session_id}/whiteboard-video/file` | `stream_whiteboard_video_v1_sessions__session_id__whiteboard_video_file_get` | whiteboard-video | 200, 422 | Stream Whiteboard Video | not_called |
| 124 | `POST` | `/v1/whiteboard/storyboards/preview` | `preview_storyboard_v1_whiteboard_storyboards_preview_post` | whiteboard-storyboard | 200, 422 | Preview Storyboard | not_called |

## File trong folder

- `api_operations.json`
- `workload_matrix.json`
- `backend_api_test_summary.json`
- `modal_worker_test_summary.json`
- `api_read_only_probe.json`
- `modal_dev_app_inventory.json`
- `artifact_manifest.json`
- `backend_contract_tests.log`
- `modal_worker_contract_tests.log`
- `host_test_environment_note.md`
- `products/`: 16 captured synthetic/history outputs with provenance manifest.

**Không có code fix nào được thực hiện:** evidence hiện có không chỉ ra timeout cần tăng hay defect Modal có thể tái hiện an toàn. Các lỗi regression/API đã liệt kê cần task sửa riêng.
