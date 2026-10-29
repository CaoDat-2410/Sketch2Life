# Sketch2Life API purpose catalog - Rev32 (route baseline Rev31)

This catalog gives the purpose of every HTTP method/path declared in the current backend source inventory. It distinguishes declaration from runtime exposure. A route marked profile-specific is mounted only in that app profile; candidate/fixture routes are not active in the default app.

## Totals and exposure

| Surface | Count | Exposure |
|---|---:|---|
| BE1 / classroom | 56 | Combined app and classroom profile |
| Demo / local flow | 35 | Combined app and demo profile; demo capabilities may use in-memory/legacy behavior |
| Lesson Library | 30 | Combined app |
| Local storage example | 3 | Only when `SKETCH2LIFE_ENV=local` and `SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED=true` |
| Candidate / fixture | 11 | Not mounted by default combined/classroom/demo composition |
| **Declared route operations** | **135** | **121 unconditional combined-app routes; 3 additional conditional local routes** |

FastAPI also generates `GET /openapi.json` (OpenAPI schema), `GET /docs` (Swagger UI) and `GET /docs/oauth2-redirect` (Swagger OAuth redirect helper); these are not included in the 135 router declarations. The optional `/renderer` static mount serves renderer files and is not a JSON API.

## Declared API operations and purpose

| # | Surface | Runtime exposure | Method | Path | Purpose | Handler/source |
|---:|---|---|---|---|---|---|
| 1 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/artifacts` | Tải một tệp kết quả hoặc tư liệu vào buổi học của tổ chức. | `be1_artifacts.py::upload_session_artifact` |
| 2 | BE1 / classroom | Combined app + classroom profile | `GET` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/artifacts/{asset_ref:path}` | Đọc/tải một tệp đã gắn với buổi học sau khi kiểm tra quyền. | `be1_artifacts.py::download_session_artifact` |
| 3 | BE1 / classroom | Combined app + classroom profile | `GET` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/canvas/operations` | Lấy các thao tác canvas từ mốc đồng bộ để khôi phục trạng thái bảng vẽ. | `be1_canvas.py::sync_canvas_operations` |
| 4 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/canvas/operations` | Ghi thêm một thao tác vẽ/chỉnh sửa canvas vào buổi học. | `be1_canvas.py::append_canvas_operation` |
| 5 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/checkpoints` | Lưu ảnh chụp trạng thái canvas của nhóm làm điểm khôi phục. | `be1_canvas.py::save_checkpoint` |
| 6 | BE1 / classroom | Combined app + classroom profile | `GET` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/checkpoints/latest` | Đọc checkpoint mới nhất của canvas trong nhóm. | `be1_canvas.py::read_latest_checkpoint` |
| 7 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/restore` | Khôi phục canvas của nhóm về một checkpoint đã lưu. | `be1_canvas.py::restore_checkpoint` |
| 8 | BE1 / classroom | Combined app + classroom profile | `GET` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/reconnect` | Lấy dữ liệu cần thiết để đồng bộ lại canvas sau khi thiết bị kết nối lại. | `be1_canvas.py::reconnect_canvas` |
| 9 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/observations` | Ghi nhận quan sát của giáo viên cho lớp. | `be1_records.py::create_observation` |
| 10 | BE1 / classroom | Combined app + classroom profile | `GET` | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles/{child_id}/portfolio` | Đọc portfolio/hồ sơ học tập của một trẻ trong lớp. | `be1_records.py::read_portfolio` |
| 11 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/data-requests` | Tạo yêu cầu xử lý dữ liệu thuộc tổ chức. | `be1_records.py::create_data_request` |
| 12 | BE1 / classroom | Combined app + classroom profile | `GET` | `/api/be1/v1/organizations/{organization_id}/data-requests/{request_id}` | Xem trạng thái và kết quả của yêu cầu dữ liệu. | `be1_records.py::read_data_request` |
| 13 | BE1 / classroom | Combined app + classroom profile | `GET` | `/api/be1/v1/organizations/{organization_id}/gallery` | Liệt kê các mục gallery của tổ chức. | `be1_records.py::list_gallery` |
| 14 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/gallery` | Tạo snapshot gallery từ tư liệu của buổi học. | `be1_records.py::create_gallery_snapshot` |
| 15 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/gallery/{gallery_id}/annotations` | Thêm chú thích vào một snapshot gallery. | `be1_records.py::annotate_gallery` |
| 16 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/gallery/{gallery_id}/publish` | Công bố snapshot gallery cho phạm vi được phép trong tổ chức. | `be1_records.py::publish_gallery` |
| 17 | BE1 / classroom | Combined app + classroom profile | `GET` | `/api/be1/v1/organizations/{organization_id}` | Đọc thông tin tổ chức/trường. | `be1_registry.py::read_organization` |
| 18 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/assignments` | Gán một người dùng vào vai trò hoặc phạm vi công việc của tổ chức. | `be1_registry.py::create_assignment` |
| 19 | BE1 / classroom | Combined app + classroom profile | `DELETE` | `/api/be1/v1/organizations/{organization_id}/assignments/{assignment_id}` | Thu hồi assignment/role của người dùng trong tổ chức. | `be1_registry.py::revoke_assignment` |
| 20 | BE1 / classroom | Combined app + classroom profile | `GET` | `/api/be1/v1/organizations/{organization_id}/classes` | Liệt kê các lớp thuộc tổ chức. | `be1_registry.py::list_classes` |
| 21 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/classes` | Tạo lớp mới trong tổ chức. | `be1_registry.py::create_class` |
| 22 | BE1 / classroom | Combined app + classroom profile | `GET` | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents` | Liệt kê hồ sơ consent của lớp. | `be1_registry.py::list_consents` |
| 23 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents` | Ghi nhận consent cho một lớp theo nội dung yêu cầu. | `be1_registry.py::record_consent` |
| 24 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents/{consent_id}/revoke` | Thu hồi một consent đã ghi nhận. | `be1_registry.py::revoke_consent` |
| 25 | BE1 / classroom | Combined app + classroom profile | `GET` | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles` | Liệt kê hồ sơ trẻ thuộc lớp. | `be1_registry.py::list_profiles` |
| 26 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles` | Tạo hồ sơ trẻ do tổ chức quản lý trong lớp. | `be1_registry.py::create_profile` |
| 27 | BE1 / classroom | Combined app + classroom profile | `GET` | `/api/be1/v1/organizations/{organization_id}/me` | Xem tổ chức/lớp/vai trò đang được gán cho người gọi. | `be1_registry.py::current_assignments` |
| 28 | BE1 / classroom | Combined app + classroom profile | `GET` | `/api/be1/v1/health` | Kiểm tra tình trạng hoạt động của BE1 runtime. | `be1_runtime.py::be1_health` |
| 29 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/device-grants/{grant_id}/join-status` | Kiểm tra trạng thái yêu cầu tham gia của device grant. | `be1_sessions.py::read_join_status` |
| 30 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions` | Tạo một buổi học BE1 trong tổ chức. | `be1_sessions.py::create_session` |
| 31 | BE1 / classroom | Combined app + classroom profile | `GET` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}` | Đọc thông tin và trạng thái buổi học BE1. | `be1_sessions.py::read_session` |
| 32 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/completion` | Ghi nhận buổi học đã hoàn thành. | `be1_sessions.py::complete_session` |
| 33 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/device-grants/{grant_id}/refresh` | Gia hạn/đổi thông tin grant cho thiết bị đang tham gia. | `be1_sessions.py::refresh_device_grant` |
| 34 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/finish` | Kết thúc buổi học theo trạng thái hiện tại. | `be1_sessions.py::finish_session` |
| 35 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups` | Tạo nhóm cộng tác trong buổi học. | `be1_sessions.py::create_group` |
| 36 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/control` | Thay đổi trạng thái điều khiển của nhóm trong buổi học. | `be1_sessions.py::control_group` |
| 37 | BE1 / classroom | Combined app + classroom profile | `PUT` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/members/{child_id}` | Gán hoặc chuyển trẻ vào nhóm của buổi học. | `be1_sessions.py::assign_member_to_group` |
| 38 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/turns/{child_id}` | Bắt đầu lượt thao tác của một trẻ trong nhóm. | `be1_sessions.py::start_child_turn` |
| 39 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/join` | Gửi yêu cầu để thiết bị tham gia buổi học. | `be1_sessions.py::request_device_join` |
| 40 | BE1 / classroom | Combined app + classroom profile | `GET` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/join-requests` | Liệt kê các yêu cầu thiết bị đang chờ tham gia. | `be1_sessions.py::list_join_requests` |
| 41 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/join-requests/{grant_id}/admit` | Chấp thuận thiết bị và cấp quyền tham gia buổi học. | `be1_sessions.py::admit_device` |
| 42 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/join-requests/{grant_id}/revoke` | Thu hồi quyền tham gia của thiết bị. | `be1_sessions.py::revoke_device_grant` |
| 43 | BE1 / classroom | Combined app + classroom profile | `GET` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/learning-stage` | Đọc giai đoạn học tập hiện tại của buổi học. | `be1_sessions.py::read_learning_stage` |
| 44 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/learning-stage/advance` | Chuyển buổi học sang giai đoạn học tiếp theo. | `be1_sessions.py::advance_learning_stage` |
| 45 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/lobby` | Mở lobby để thiết bị yêu cầu tham gia. | `be1_sessions.py::open_lobby` |
| 46 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/memberships/{membership_id}/help` | Gửi yêu cầu trợ giúp từ thành viên trong buổi học. | `be1_sessions.py::request_help` |
| 47 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/memberships/{membership_id}/leave` | Ghi nhận thành viên rời buổi học. | `be1_sessions.py::leave_session` |
| 48 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/memberships/{membership_id}/progress` | Cập nhật tiến độ của thành viên trong buổi học. | `be1_sessions.py::update_progress` |
| 49 | BE1 / classroom | Combined app + classroom profile | `GET` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/outcome` | Đọc kết quả/tóm tắt trạng thái cuối của buổi học. | `be1_sessions.py::read_session_outcome` |
| 50 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/pause` | Tạm dừng buổi học. | `be1_sessions.py::pause_session` |
| 51 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/resume` | Tiếp tục buổi học đang tạm dừng. | `be1_sessions.py::resume_session` |
| 52 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/room-code/rotate` | Tạo mã phòng mới để kiểm soát các lượt tham gia tiếp theo. | `be1_sessions.py::rotate_room_code` |
| 53 | BE1 / classroom | Combined app + classroom profile | `GET` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/roster` | Đọc danh sách thành viên và trạng thái tham gia của buổi học. | `be1_sessions.py::read_session_roster` |
| 54 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/start` | Chuyển buổi học sang trạng thái bắt đầu. | `be1_sessions.py::start_session` |
| 55 | BE1 / classroom | Combined app + classroom profile | `POST` | `/api/be1/v1/room-code/join` | Gửi yêu cầu tham gia bằng mã phòng. | `be1_sessions.py::request_room_code_join` |
| 56 | BE1 / classroom | Combined app + classroom profile | `GET` | `/health` | Kiểm tra tình trạng hoạt động cơ bản của API service. | `health.py::health` |
| 57 | Demo / local flow | Combined app + demo profile | `POST` | `/v1/profile/preferences/classify` | Phân loại sở thích đã nhập để hỗ trợ cá nhân hóa luồng demo. | `child_preferences.py::classify_preferences` |
| 58 | Demo / local flow | Combined app + demo profile | `POST` | `/v1/sessions/{session_id}/media/audio` | Tải tệp âm thanh vào session demo. | `images.py::upload_audio` |
| 59 | Demo / local flow | Combined app + demo profile | `POST` | `/v1/sessions/{session_id}/media/image` | Tải ảnh vào session demo làm đầu vào xử lý. | `images.py::upload_image` |
| 60 | Demo / local flow | Combined app + demo profile | `POST` | `/v1/sessions/{session_id}/understanding` | Chạy bước hiểu ảnh/nội dung của session demo. | `images.py::run_understanding` |
| 61 | Demo / local flow | Combined app + demo profile | `GET` | `/v1/sessions/{session_id}/understanding/progress` | Đọc tiến độ xử lý understanding của session demo. | `images.py::read_understanding_progress` |
| 62 | Demo / local flow | Combined app + demo profile | `POST` | `/v1/sessions` | Tạo session cho luồng demo. | `sessions.py::create_session` |
| 63 | Demo / local flow | Combined app + demo profile | `GET` | `/v1/sessions/{session_id}` | Đọc session demo và dữ liệu trạng thái của nó. | `sessions.py::get_session` |
| 64 | Demo / local flow | Combined app + demo profile | `GET` | `/v1/sessions/{session_id}/story-video-jobs` | Liệt kê các job tạo story video của session demo. | `story_video.py::list_story_video_jobs` |
| 65 | Demo / local flow | Combined app + demo profile | `POST` | `/v1/sessions/{session_id}/story-video-jobs` | Tạo job story video cho session demo. | `story_video.py::create_story_video_job` |
| 66 | Demo / local flow | Combined app + demo profile | `GET` | `/v1/sessions/{session_id}/story-video/{job_id}` | Đọc trạng thái job story video. | `story_video.py::get_story_video_status` |
| 67 | Demo / local flow | Combined app + demo profile | `GET` | `/v1/sessions/{session_id}/story-video/{job_id}/file` | Phát/tải tệp story video đã tạo. | `story_video.py::stream_story_video` |
| 68 | Demo / local flow | Combined app + demo profile | `GET` | `/v1/renderer/pixi-asset` | Đọc asset PixiJS dùng bởi renderer demo. | `supervised_flow.py::read_renderer_pixi_asset` |
| 69 | Demo / local flow | Combined app + demo profile | `GET` | `/v1/renderer/rig-mask` | Đọc mask của rig dùng bởi renderer demo. | `supervised_flow.py::read_renderer_rig_mask` |
| 70 | Demo / local flow | Combined app + demo profile | `GET` | `/v1/renderer/rig-package` | Đọc gói rig cần thiết để dựng renderer demo. | `supervised_flow.py::read_renderer_rig_package` |
| 71 | Demo / local flow | Combined app + demo profile | `GET` | `/v1/renderer/source` | Đọc source/resource được phục vụ cho renderer demo. | `supervised_flow.py::read_renderer_source` |
| 72 | Demo / local flow | Combined app + demo profile | `POST` | `/v1/sessions/{session_id}/experience/prepare` | Chuẩn bị dữ liệu và trạng thái trải nghiệm của session demo. | `supervised_flow.py::prepare_experience` |
| 73 | Demo / local flow | Combined app + demo profile | `POST` | `/v1/sessions/{session_id}/feedback` | Ghi feedback của người dùng cho trải nghiệm demo. | `supervised_flow.py::record_feedback` |
| 74 | Demo / local flow | Combined app + demo profile | `GET` | `/v1/sessions/{session_id}/gallery` | Đọc gallery/tư liệu đã tạo trong session demo. | `supervised_flow.py::read_gallery` |
| 75 | Demo / local flow | Combined app + demo profile | `POST` | `/v1/sessions/{session_id}/gate-a/confirm` | Xác nhận bước duyệt Gate A trong luồng demo. | `supervised_flow.py::confirm_gate_a` |
| 76 | Demo / local flow | Combined app + demo profile | `POST` | `/v1/sessions/{session_id}/gate-b/approve` | Phê duyệt bước Gate B để luồng demo được tiếp tục. | `supervised_flow.py::approve_gate_b` |
| 77 | Demo / local flow | Combined app + demo profile | `POST` | `/v1/sessions/{session_id}/handoff` | Hoàn tất bàn giao session sang bước/đối tượng xử lý kế tiếp. | `supervised_flow.py::complete_handoff` |
| 78 | Demo / local flow | Combined app + demo profile | `POST` | `/v1/sessions/{session_id}/media/retake` | Đánh dấu ảnh/tư liệu cần chụp lại và đưa session về bước retake. | `supervised_flow.py::request_retake` |
| 79 | Demo / local flow | Combined app + demo profile | `PUT` | `/v1/sessions/{session_id}/p1-context` | Ghi context P1 do người lớn chọn cho session. | `supervised_flow.py::set_p1_context` |
| 80 | Demo / local flow | Combined app + demo profile | `POST` | `/v1/sessions/{session_id}/p1-filter` | Chạy bộ lọc P1 trên dữ liệu/context của session. | `supervised_flow.py::run_p1_filter` |
| 81 | Demo / local flow | Combined app + demo profile | `POST` | `/v1/sessions/{session_id}/p1/activity-suggestions` | Lấy các gợi ý hoạt động P1 cho session. | `supervised_flow.py::read_p1_activity_suggestions` |
| 82 | Demo / local flow | Combined app + demo profile | `POST` | `/v1/sessions/{session_id}/p1/activity-suggestions/rank` | Xếp hạng các gợi ý hoạt động P1. | `supervised_flow.py::rank_p1_activity_suggestions` |
| 83 | Demo / local flow | Combined app + demo profile | `GET` | `/v1/sessions/{session_id}/p1/context-candidates` | Liệt kê các ứng viên context P1 có thể chọn. | `supervised_flow.py::read_p1_context_candidates` |
| 84 | Demo / local flow | Combined app + demo profile | `GET` | `/v1/sessions/{session_id}/p1/context-options` | Đọc các lựa chọn context P1 hiện có. | `supervised_flow.py::read_p1_context_options` |
| 85 | Demo / local flow | Combined app + demo profile | `POST` | `/v1/sessions/{session_id}/p1/context-options` | Tạo/đọc lựa chọn context P1 đã cá nhân hóa cho session. | `supervised_flow.py::read_personalized_p1_context_options` |
| 86 | Demo / local flow | Combined app + demo profile | `POST` | `/v1/sessions/{session_id}/p1/context-options/finalize` | Chốt lựa chọn context P1 để dùng tiếp trong session. | `supervised_flow.py::finalize_p1_context_options` |
| 87 | Demo / local flow | Combined app + demo profile | `POST` | `/v1/sessions/{session_id}/renderer/launch` | Khởi chạy/chuẩn bị renderer cho session demo. | `supervised_flow.py::prepare_renderer` |
| 88 | Demo / local flow | Combined app + demo profile | `POST` | `/v1/whiteboard/storyboards/preview` | Tạo bản xem trước storyboard whiteboard. | `whiteboard_storyboard.py::preview_storyboard` |
| 89 | Demo / local flow | Combined app + demo profile | `GET` | `/v1/sessions/{session_id}/whiteboard-video` | Đọc trạng thái video whiteboard của session. | `whiteboard_video.py::get_whiteboard_video_status` |
| 90 | Demo / local flow | Combined app + demo profile | `POST` | `/v1/sessions/{session_id}/whiteboard-video-jobs` | Tạo job video từ storyboard whiteboard. | `whiteboard_video.py::create_whiteboard_video_job` |
| 91 | Demo / local flow | Combined app + demo profile | `GET` | `/v1/sessions/{session_id}/whiteboard-video/file` | Phát/tải video whiteboard đã tạo. | `whiteboard_video.py::stream_whiteboard_video` |
| 92 | Lesson Library | Combined app | `GET` | `/api/lesson-library/v1/me/lesson-invitations` | Parent xem các lời mời chia sẻ lesson trực tiếp đang chờ. | `lesson_library.py::list_lesson_invitations` |
| 93 | Lesson Library | Combined app | `POST` | `/api/lesson-library/v1/me/lesson-invitations/{access_grant_id}/accept` | Parent chấp nhận lời mời xem/tải lesson được chia sẻ. | `lesson_library.py::accept_lesson_invitation` |
| 94 | Lesson Library | Combined app | `POST` | `/api/lesson-library/v1/me/lesson-invitations/{access_grant_id}/decline` | Parent từ chối lời mời chia sẻ lesson. | `lesson_library.py::decline_lesson_invitation` |
| 95 | Lesson Library | Combined app | `GET` | `/api/lesson-library/v1/me/lessons` | Parent tìm lesson Public hoặc lesson đã được chia sẻ hợp lệ. | `lesson_library.py::list_parent_lessons` |
| 96 | Lesson Library | Combined app | `GET` | `/api/lesson-library/v1/me/lessons/{lesson_id}` | Parent đọc nội dung lesson mà mình có quyền truy cập. | `lesson_library.py::get_parent_lesson` |
| 97 | Lesson Library | Combined app | `GET` | `/api/lesson-library/v1/me/lessons/{lesson_id}/download` | Parent tải bản xuất nội dung lesson; không tải file gốc giáo viên. | `lesson_library.py::download_parent_lesson` |
| 98 | Lesson Library | Combined app | `GET` | `/api/lesson-library/v1/me/parent-group-invitations` | Parent xem lời mời tham gia nhóm phụ huynh của trường. | `lesson_library.py::list_parent_group_invitations` |
| 99 | Lesson Library | Combined app | `POST` | `/api/lesson-library/v1/me/parent-group-invitations/{membership_id}/accept` | Parent chấp nhận lời mời tham gia nhóm phụ huynh. | `lesson_library.py::accept_parent_group_invitation` |
| 100 | Lesson Library | Combined app | `GET` | `/api/lesson-library/v1/organizations/{organization_id}/access-grants` | Manager xem danh sách quyền chia sẻ và hàng chờ duyệt Public của trường. | `lesson_library.py::list_access_grants` |
| 101 | Lesson Library | Combined app | `POST` | `/api/lesson-library/v1/organizations/{organization_id}/access-grants/{access_grant_id}/decision` | Manager duyệt hoặc yêu cầu sửa một grant Public đang chờ. | `lesson_library.py::decide_access_grant` |
| 102 | Lesson Library | Combined app | `GET` | `/api/lesson-library/v1/organizations/{organization_id}/lessons` | Teacher/Manager liệt kê lesson trong phạm vi quyền của trường. | `lesson_library.py::list_lessons` |
| 103 | Lesson Library | Combined app | `POST` | `/api/lesson-library/v1/organizations/{organization_id}/lessons` | Teacher tạo lesson reusable mới, ban đầu ở trạng thái riêng tư. | `lesson_library.py::create_lesson` |
| 104 | Lesson Library | Combined app | `DELETE` | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}` | Archive lesson mà không xóa lịch sử phiên bản và kiểm toán. | `lesson_library.py::archive_lesson` |
| 105 | Lesson Library | Combined app | `GET` | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}` | Teacher/Manager đọc lesson và phiên bản hiện tại trong trường. | `lesson_library.py::get_lesson` |
| 106 | Lesson Library | Combined app | `PATCH` | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}` | Teacher sửa nội dung bằng cách tạo phiên bản lesson mới. | `lesson_library.py::update_lesson` |
| 107 | Lesson Library | Combined app | `POST` | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/access-grants` | Tạo yêu cầu Public hoặc cấp quyền chia sẻ lesson cho audience phù hợp. | `lesson_library.py::create_access_grant` |
| 108 | Lesson Library | Combined app | `DELETE` | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/access-grants/{access_grant_id}` | Thu hồi grant chia sẻ để chặn quyền truy cập mới. | `lesson_library.py::revoke_access_grant` |
| 109 | Lesson Library | Combined app | `GET` | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/source-documents/{source_document_id}` | Teacher xem trạng thái scan/trích xuất của tài liệu lesson đã tải. | `lesson_library.py::get_source_document` |
| 110 | Lesson Library | Combined app | `GET` | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/source-documents/{source_document_id}/revisions/{revision_id}` | Teacher xem trước các trường được trích xuất và cảnh báo của một revision. | `lesson_library.py::get_document_revision` |
| 111 | Lesson Library | Combined app | `POST` | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/upload-sessions` | Teacher mở phiên upload riêng tư cho tài liệu nguồn của lesson. | `lesson_library.py::create_upload_session` |
| 112 | Lesson Library | Combined app | `POST` | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/versions` | Teacher xác nhận nội dung đã lọc và tạo phiên bản lesson bất biến. | `lesson_library.py::create_lesson_version` |
| 113 | Lesson Library | Combined app | `GET` | `/api/lesson-library/v1/organizations/{organization_id}/parent-groups` | Manager liệt kê nhóm phụ huynh thuộc trường. | `lesson_library.py::list_parent_groups` |
| 114 | Lesson Library | Combined app | `POST` | `/api/lesson-library/v1/organizations/{organization_id}/parent-groups` | Manager tạo nhóm phụ huynh làm audience chia sẻ lesson. | `lesson_library.py::create_parent_group` |
| 115 | Lesson Library | Combined app | `POST` | `/api/lesson-library/v1/organizations/{organization_id}/parent-groups/{parent_group_id}/invitations` | Manager mời một phụ huynh vào nhóm của trường. | `lesson_library.py::invite_parent_to_group` |
| 116 | Lesson Library | Combined app | `DELETE` | `/api/lesson-library/v1/organizations/{organization_id}/parent-groups/{parent_group_id}/members/{membership_id}` | Manager thu hồi membership để kết thúc quyền chia sẻ qua nhóm. | `lesson_library.py::revoke_parent_group_membership` |
| 117 | Lesson Library | Combined app | `PATCH` | `/api/lesson-library/v1/platform/lessons/{lesson_id}/moderation` | Platform Admin ẩn hoặc khôi phục khả năng truy cập lesson và ghi lý do kiểm duyệt. | `lesson_library.py::moderate_lesson` |
| 118 | Lesson Library | Combined app | `DELETE` | `/api/lesson-library/v1/upload-sessions/{upload_session_id}` | Teacher hủy phiên upload của mình và xóa các chunk riêng tư. | `lesson_library.py::abort_upload_session` |
| 119 | Lesson Library | Combined app | `GET` | `/api/lesson-library/v1/upload-sessions/{upload_session_id}` | Teacher kiểm tra tiến độ, các phần đã nhận và hạn hết phiên upload. | `lesson_library.py::get_upload_session` |
| 120 | Lesson Library | Combined app | `POST` | `/api/lesson-library/v1/upload-sessions/{upload_session_id}/complete` | Ghép, quét malware, kiểm tra và trích xuất tài liệu để chuyển sang READY_FOR_REVIEW. | `lesson_library.py::complete_upload` |
| 121 | Lesson Library | Combined app | `PUT` | `/api/lesson-library/v1/upload-sessions/{upload_session_id}/parts/{part_number}` | Tải hoặc gửi lại một chunk có checksum của phiên upload. | `lesson_library.py::upload_part` |
| 122 | Local storage example | Conditional: local env + storage-example flag | `POST` | `/api/dev/v1/storage-examples/lesson-source-documents` | Tải tệp ví dụ vào bucket MinIO local; không tạo Lesson record. | `storage_examples.py::upload_lesson_source_example` |
| 123 | Local storage example | Conditional: local env + storage-example flag | `DELETE` | `/api/dev/v1/storage-examples/lesson-source-documents/{object_id}` | Xóa object của ví dụ upload trong MinIO local. | `storage_examples.py::delete_lesson_source_example` |
| 124 | Local storage example | Conditional: local env + storage-example flag | `GET` | `/api/dev/v1/storage-examples/lesson-source-documents/{object_id}` | Đọc object của ví dụ upload qua backend từ MinIO local. | `storage_examples.py::download_lesson_source_example` |
| 125 | Candidate / fixture | Not mounted in default app | `POST` | `/api/collaboration/v1/activity-assignments` | Thực thi một yêu cầu gán/chạy hoạt động cộng tác. | `activity_execution.py::execute` |
| 126 | Candidate / fixture | Not mounted in default app | `GET` | `/api/collaboration/v1/jobs/{job_id}` | Đọc trạng thái job cộng tác/AI theo mã job. | `ai_jobs.py::get_job` |
| 127 | Candidate / fixture | Not mounted in default app | `POST` | `/api/collaboration/v1/analysis-results/{analysis_id}/corrections` | Gửi chỉnh sửa của người dùng cho kết quả phân tích. | `analysis_corrections.py::submit_correction` |
| 128 | Candidate / fixture | Not mounted in default app | `POST` | `/api/collaboration/v1/assistance-requests` | Tạo yêu cầu hỗ trợ cộng tác. | `assistance_requests.py::submit` |
| 129 | Candidate / fixture | Not mounted in default app | `POST` | `/api/collaboration/v1/assistance-requests/{assistance_id}/cancel` | Hủy một yêu cầu hỗ trợ đang còn hiệu lực. | `assistance_requests.py::cancel` |
| 130 | Candidate / fixture | Not mounted in default app | `POST` | `/api/collaboration/v1/knowledge-videos` | Tạo một knowledge video trong luồng cộng tác. | `knowledge_video.py::create` |
| 131 | Candidate / fixture | Not mounted in default app | `POST` | `/api/collaboration/v1/governance/records` | Ghi/thực thi command quản trị cho learning content. | `learning_content.py::command` |
| 132 | Candidate / fixture | Not mounted in default app | `POST` | `/v1/live-understanding` | Chạy xử lý hiểu nội dung trực tiếp cho request đang hoạt động. | `live_understanding.py::live_understanding` |
| 133 | Candidate / fixture | Not mounted in default app | `POST` | `/api/collaboration/v1/knowledge-videos/{video_id}/failure-dispositions` | Ghi cách xử lý một knowledge video bị lỗi. | `video_failure.py::disposition` |
| 134 | Candidate / fixture | Not mounted in default app | `POST` | `/api/collaboration/v1/knowledge-videos/{video_id}/playback` | Ghi nhận một lần playback knowledge video. | `video_review.py::playback` |
| 135 | Candidate / fixture | Not mounted in default app | `POST` | `/api/collaboration/v1/knowledge-videos/{video_id}/reviews` | Gửi review/đánh giá cho knowledge video. | `video_review.py::review` |

## Interpretation notes

- The 11 candidate/fixture declarations include isolated fixture apps or router factories; they are listed for repository completeness and must not be presented as active product APIs.
- The 3 local storage routes demonstrate MinIO upload/read/delete only. They do not create Lesson entities or metadata.
- Rev31 adds Lesson Library CRUD, upload/review, grant/sharing, Parent read/download and moderation operations without changing existing Parent, Teacher, BE1 or demo method/path declarations.
- Broader FEAT-063 requirements not implemented as APIs in Rev31: Parent-Teacher child-profile grants, LessonOccurrence delivery/history/feedback, AI lesson/sketch generation, billing/quota endpoints, and new Story/video-generation endpoints. Existing BE1 profile/classroom routes and demo Story/video routes are not substitutes for those future contracts.
- Lesson Library purpose, actor authorization, payloads, status codes, headers and errors are specified in `LESSON_LIBRARY_API_CONTRACT_DRAFT_REV29_20261028.md` (Rev31 reconciliation).
- This is a static source/composition catalog, not a runtime OpenAPI export. No app startup, tests, Docker, live database or migration was run to produce it.
