"""Build the FEAT-063 API purpose catalog from the reviewed route inventory."""

from pathlib import Path


FEATURE_ROOT = Path(__file__).resolve().parents[1]
INVENTORY = FEATURE_ROOT / "artifacts" / "API_INVENTORY_FEAT063_REV31_20261028.md"
OUTPUT = FEATURE_ROOT / "artifacts" / "API_PURPOSE_CATALOG_FEAT063_REV32_20261028.md"

PURPOSES = {
    # BE1 session artifacts and collaborative canvas.
    "upload_session_artifact": "Tải một tệp kết quả hoặc tư liệu vào buổi học của tổ chức.",
    "download_session_artifact": "Đọc/tải một tệp đã gắn với buổi học sau khi kiểm tra quyền.",
    "sync_canvas_operations": "Lấy các thao tác canvas từ mốc đồng bộ để khôi phục trạng thái bảng vẽ.",
    "append_canvas_operation": "Ghi thêm một thao tác vẽ/chỉnh sửa canvas vào buổi học.",
    "save_checkpoint": "Lưu ảnh chụp trạng thái canvas của nhóm làm điểm khôi phục.",
    "read_latest_checkpoint": "Đọc checkpoint mới nhất của canvas trong nhóm.",
    "restore_checkpoint": "Khôi phục canvas của nhóm về một checkpoint đã lưu.",
    "reconnect_canvas": "Lấy dữ liệu cần thiết để đồng bộ lại canvas sau khi thiết bị kết nối lại.",
    # BE1 classroom records and gallery.
    "create_observation": "Ghi nhận quan sát của giáo viên cho lớp.",
    "read_portfolio": "Đọc portfolio/hồ sơ học tập của một trẻ trong lớp.",
    "create_data_request": "Tạo yêu cầu xử lý dữ liệu thuộc tổ chức.",
    "read_data_request": "Xem trạng thái và kết quả của yêu cầu dữ liệu.",
    "list_gallery": "Liệt kê các mục gallery của tổ chức.",
    "create_gallery_snapshot": "Tạo snapshot gallery từ tư liệu của buổi học.",
    "annotate_gallery": "Thêm chú thích vào một snapshot gallery.",
    "publish_gallery": "Công bố snapshot gallery cho phạm vi được phép trong tổ chức.",
    # BE1 organization, assignment, class, consent, and profile registry.
    "read_organization": "Đọc thông tin tổ chức/trường.",
    "create_assignment": "Gán một người dùng vào vai trò hoặc phạm vi công việc của tổ chức.",
    "revoke_assignment": "Thu hồi assignment/role của người dùng trong tổ chức.",
    "list_classes": "Liệt kê các lớp thuộc tổ chức.",
    "create_class": "Tạo lớp mới trong tổ chức.",
    "list_consents": "Liệt kê hồ sơ consent của lớp.",
    "record_consent": "Ghi nhận consent cho một lớp theo nội dung yêu cầu.",
    "revoke_consent": "Thu hồi một consent đã ghi nhận.",
    "list_profiles": "Liệt kê hồ sơ trẻ thuộc lớp.",
    "create_profile": "Tạo hồ sơ trẻ do tổ chức quản lý trong lớp.",
    "current_assignments": "Xem tổ chức/lớp/vai trò đang được gán cho người gọi.",
    "be1_health": "Kiểm tra tình trạng hoạt động của BE1 runtime.",
    "health": "Kiểm tra tình trạng hoạt động cơ bản của API service.",
    # BE1 session lifecycle and device access.
    "read_join_status": "Kiểm tra trạng thái yêu cầu tham gia của device grant.",
    "create_session": "Tạo một buổi học BE1 trong tổ chức.",
    "read_session": "Đọc thông tin và trạng thái buổi học BE1.",
    "complete_session": "Ghi nhận buổi học đã hoàn thành.",
    "refresh_device_grant": "Gia hạn/đổi thông tin grant cho thiết bị đang tham gia.",
    "finish_session": "Kết thúc buổi học theo trạng thái hiện tại.",
    "create_group": "Tạo nhóm cộng tác trong buổi học.",
    "control_group": "Thay đổi trạng thái điều khiển của nhóm trong buổi học.",
    "assign_member_to_group": "Gán hoặc chuyển trẻ vào nhóm của buổi học.",
    "start_child_turn": "Bắt đầu lượt thao tác của một trẻ trong nhóm.",
    "request_device_join": "Gửi yêu cầu để thiết bị tham gia buổi học.",
    "list_join_requests": "Liệt kê các yêu cầu thiết bị đang chờ tham gia.",
    "admit_device": "Chấp thuận thiết bị và cấp quyền tham gia buổi học.",
    "revoke_device_grant": "Thu hồi quyền tham gia của thiết bị.",
    "read_learning_stage": "Đọc giai đoạn học tập hiện tại của buổi học.",
    "advance_learning_stage": "Chuyển buổi học sang giai đoạn học tiếp theo.",
    "open_lobby": "Mở lobby để thiết bị yêu cầu tham gia.",
    "request_help": "Gửi yêu cầu trợ giúp từ thành viên trong buổi học.",
    "leave_session": "Ghi nhận thành viên rời buổi học.",
    "update_progress": "Cập nhật tiến độ của thành viên trong buổi học.",
    "read_session_outcome": "Đọc kết quả/tóm tắt trạng thái cuối của buổi học.",
    "pause_session": "Tạm dừng buổi học.",
    "resume_session": "Tiếp tục buổi học đang tạm dừng.",
    "rotate_room_code": "Tạo mã phòng mới để kiểm soát các lượt tham gia tiếp theo.",
    "read_session_roster": "Đọc danh sách thành viên và trạng thái tham gia của buổi học.",
    "start_session": "Chuyển buổi học sang trạng thái bắt đầu.",
    "request_room_code_join": "Gửi yêu cầu tham gia bằng mã phòng.",
    # Demo/local flow APIs.
    "classify_preferences": "Phân loại sở thích đã nhập để hỗ trợ cá nhân hóa luồng demo.",
    "upload_audio": "Tải tệp âm thanh vào session demo.",
    "upload_image": "Tải ảnh vào session demo làm đầu vào xử lý.",
    "run_understanding": "Chạy bước hiểu ảnh/nội dung của session demo.",
    "read_understanding_progress": "Đọc tiến độ xử lý understanding của session demo.",
    "get_session": "Đọc session demo và dữ liệu trạng thái của nó.",
    "list_story_video_jobs": "Liệt kê các job tạo story video của session demo.",
    "create_story_video_job": "Tạo job story video cho session demo.",
    "get_story_video_status": "Đọc trạng thái job story video.",
    "stream_story_video": "Phát/tải tệp story video đã tạo.",
    "read_renderer_pixi_asset": "Đọc asset PixiJS dùng bởi renderer demo.",
    "read_renderer_rig_mask": "Đọc mask của rig dùng bởi renderer demo.",
    "read_renderer_rig_package": "Đọc gói rig cần thiết để dựng renderer demo.",
    "read_renderer_source": "Đọc source/resource được phục vụ cho renderer demo.",
    "prepare_experience": "Chuẩn bị dữ liệu và trạng thái trải nghiệm của session demo.",
    "record_feedback": "Ghi feedback của người dùng cho trải nghiệm demo.",
    "read_gallery": "Đọc gallery/tư liệu đã tạo trong session demo.",
    "confirm_gate_a": "Xác nhận bước duyệt Gate A trong luồng demo.",
    "approve_gate_b": "Phê duyệt bước Gate B để luồng demo được tiếp tục.",
    "complete_handoff": "Hoàn tất bàn giao session sang bước/đối tượng xử lý kế tiếp.",
    "request_retake": "Đánh dấu ảnh/tư liệu cần chụp lại và đưa session về bước retake.",
    "set_p1_context": "Ghi context P1 do người lớn chọn cho session.",
    "run_p1_filter": "Chạy bộ lọc P1 trên dữ liệu/context của session.",
    "read_p1_activity_suggestions": "Lấy các gợi ý hoạt động P1 cho session.",
    "rank_p1_activity_suggestions": "Xếp hạng các gợi ý hoạt động P1.",
    "read_p1_context_candidates": "Liệt kê các ứng viên context P1 có thể chọn.",
    "read_p1_context_options": "Đọc các lựa chọn context P1 hiện có.",
    "read_personalized_p1_context_options": "Tạo/đọc lựa chọn context P1 đã cá nhân hóa cho session.",
    "finalize_p1_context_options": "Chốt lựa chọn context P1 để dùng tiếp trong session.",
    "prepare_renderer": "Khởi chạy/chuẩn bị renderer cho session demo.",
    "preview_storyboard": "Tạo bản xem trước storyboard whiteboard.",
    "get_whiteboard_video_status": "Đọc trạng thái video whiteboard của session.",
    "create_whiteboard_video_job": "Tạo job video từ storyboard whiteboard.",
    "stream_whiteboard_video": "Phát/tải video whiteboard đã tạo.",
    # Lesson Library: mounted in the combined app.
    "list_lesson_invitations": "Parent xem các lời mời chia sẻ lesson trực tiếp đang chờ.",
    "accept_lesson_invitation": "Parent chấp nhận lời mời xem/tải lesson được chia sẻ.",
    "decline_lesson_invitation": "Parent từ chối lời mời chia sẻ lesson.",
    "list_parent_lessons": "Parent tìm lesson Public hoặc lesson đã được chia sẻ hợp lệ.",
    "get_parent_lesson": "Parent đọc nội dung lesson mà mình có quyền truy cập.",
    "download_parent_lesson": "Parent tải bản xuất nội dung lesson; không tải file gốc giáo viên.",
    "list_parent_group_invitations": "Parent xem lời mời tham gia nhóm phụ huynh của trường.",
    "accept_parent_group_invitation": "Parent chấp nhận lời mời tham gia nhóm phụ huynh.",
    "list_access_grants": "Manager xem danh sách quyền chia sẻ và hàng chờ duyệt Public của trường.",
    "decide_access_grant": "Manager duyệt hoặc yêu cầu sửa một grant Public đang chờ.",
    "list_lessons": "Teacher/Manager liệt kê lesson trong phạm vi quyền của trường.",
    "create_lesson": "Teacher tạo lesson reusable mới, ban đầu ở trạng thái riêng tư.",
    "archive_lesson": "Archive lesson mà không xóa lịch sử phiên bản và kiểm toán.",
    "get_lesson": "Teacher/Manager đọc lesson và phiên bản hiện tại trong trường.",
    "update_lesson": "Teacher sửa nội dung bằng cách tạo phiên bản lesson mới.",
    "create_access_grant": "Tạo yêu cầu Public hoặc cấp quyền chia sẻ lesson cho audience phù hợp.",
    "revoke_access_grant": "Thu hồi grant chia sẻ để chặn quyền truy cập mới.",
    "get_source_document": "Teacher xem trạng thái scan/trích xuất của tài liệu lesson đã tải.",
    "get_document_revision": "Teacher xem trước các trường được trích xuất và cảnh báo của một revision.",
    "create_upload_session": "Teacher mở phiên upload riêng tư cho tài liệu nguồn của lesson.",
    "create_lesson_version": "Teacher xác nhận nội dung đã lọc và tạo phiên bản lesson bất biến.",
    "list_parent_groups": "Manager liệt kê nhóm phụ huynh thuộc trường.",
    "create_parent_group": "Manager tạo nhóm phụ huynh làm audience chia sẻ lesson.",
    "invite_parent_to_group": "Manager mời một phụ huynh vào nhóm của trường.",
    "revoke_parent_group_membership": "Manager thu hồi membership để kết thúc quyền chia sẻ qua nhóm.",
    "moderate_lesson": "Platform Admin ẩn hoặc khôi phục khả năng truy cập lesson và ghi lý do kiểm duyệt.",
    "abort_upload_session": "Teacher hủy phiên upload của mình và xóa các chunk riêng tư.",
    "get_upload_session": "Teacher kiểm tra tiến độ, các phần đã nhận và hạn hết phiên upload.",
    "complete_upload": "Ghép, quét malware, kiểm tra và trích xuất tài liệu để chuyển sang READY_FOR_REVIEW.",
    "upload_part": "Tải hoặc gửi lại một chunk có checksum của phiên upload.",
    # Local-only MinIO storage demonstration.
    "upload_lesson_source_example": "Tải tệp ví dụ vào bucket MinIO local; không tạo Lesson record.",
    "delete_lesson_source_example": "Xóa object của ví dụ upload trong MinIO local.",
    "download_lesson_source_example": "Đọc object của ví dụ upload qua backend từ MinIO local.",
    # Candidate/fixture/unmounted declarations; not active default-app APIs.
    "execute": "Thực thi một yêu cầu gán/chạy hoạt động cộng tác.",
    "get_job": "Đọc trạng thái job cộng tác/AI theo mã job.",
    "submit_correction": "Gửi chỉnh sửa của người dùng cho kết quả phân tích.",
    "submit": "Tạo yêu cầu hỗ trợ cộng tác.",
    "cancel": "Hủy một yêu cầu hỗ trợ đang còn hiệu lực.",
    "create": "Tạo một knowledge video trong luồng cộng tác.",
    "command": "Ghi/thực thi command quản trị cho learning content.",
    "live_understanding": "Chạy xử lý hiểu nội dung trực tiếp cho request đang hoạt động.",
    "disposition": "Ghi cách xử lý một knowledge video bị lỗi.",
    "playback": "Ghi nhận một lần playback knowledge video.",
    "review": "Gửi review/đánh giá cho knowledge video.",
}


def parse_route_rows(text: str):
    section = None
    sections = {
        "## BE1 / classroom routes": ("BE1 / classroom", "Combined app + classroom profile"),
        "## Demo / local flow routes": ("Demo / local flow", "Combined app + demo profile"),
        "## Lesson Library routes": ("Lesson Library", "Combined app"),
        "## Conditional local storage example": ("Local storage example", "Conditional: local env + storage-example flag"),
        "## Candidate, fixture or unmounted routes": ("Candidate / fixture", "Not mounted in default app"),
    }
    rows = []
    for line in text.splitlines():
        if line in sections:
            section = sections[line]
            continue
        if not line.startswith("| `") or " | `" not in line or section is None:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 3 or cells[0].strip("`") not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
            continue
        method, path, source = (cell.strip("`") for cell in cells)
        handler = source.split("::", 1)[-1]
        purpose = PURPOSES.get(handler)
        if source == "sessions.py::create_session":
            purpose = "Tạo session cho luồng demo."
        if purpose is None:
            raise ValueError(f"No purpose mapping for route handler: {handler}")
        rows.append((len(rows) + 1, section[0], section[1], method, path, purpose, source))
    return rows


def main() -> None:
    inventory = INVENTORY.read_text(encoding="utf-8")
    rows = parse_route_rows(inventory)
    if len(rows) != 135:
        raise ValueError(f"Expected 135 route declarations; found {len(rows)}")
    counts = {surface: sum(row[1] == surface for row in rows) for surface in {row[1] for row in rows}}
    expected = {
        "BE1 / classroom": 56,
        "Demo / local flow": 35,
        "Lesson Library": 30,
        "Local storage example": 3,
        "Candidate / fixture": 11,
    }
    if counts != expected:
        raise ValueError(f"Route totals do not match reviewed inventory: {counts}")

    lines = [
        "# Sketch2Life API purpose catalog - Rev32 (route baseline Rev31)",
        "",
        "This catalog gives the purpose of every HTTP method/path declared in the current backend source inventory. It distinguishes declaration from runtime exposure. A route marked profile-specific is mounted only in that app profile; candidate/fixture routes are not active in the default app.",
        "",
        "## Totals and exposure",
        "",
        "| Surface | Count | Exposure |",
        "|---|---:|---|",
        "| BE1 / classroom | 56 | Combined app and classroom profile |",
        "| Demo / local flow | 35 | Combined app and demo profile; demo capabilities may use in-memory/legacy behavior |",
        "| Lesson Library | 30 | Combined app |",
        "| Local storage example | 3 | Only when `SKETCH2LIFE_ENV=local` and `SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED=true` |",
        "| Candidate / fixture | 11 | Not mounted by default combined/classroom/demo composition |",
        "| **Declared route operations** | **135** | **121 unconditional combined-app routes; 3 additional conditional local routes** |",
        "",
        "FastAPI also generates `GET /openapi.json` (OpenAPI schema), `GET /docs` (Swagger UI) and `GET /docs/oauth2-redirect` (Swagger OAuth redirect helper); these are not included in the 135 router declarations. The optional `/renderer` static mount serves renderer files and is not a JSON API.",
        "",
        "## Declared API operations and purpose",
        "",
        "| # | Surface | Runtime exposure | Method | Path | Purpose | Handler/source |",
        "|---:|---|---|---|---|---|---|",
    ]
    for number, surface, exposure, method, path, purpose, source in rows:
        lines.append(f"| {number} | {surface} | {exposure} | `{method}` | `{path}` | {purpose} | `{source}` |")
    lines.extend(
        [
            "",
            "## Interpretation notes",
            "",
            "- The 11 candidate/fixture declarations include isolated fixture apps or router factories; they are listed for repository completeness and must not be presented as active product APIs.",
            "- The 3 local storage routes demonstrate MinIO upload/read/delete only. They do not create Lesson entities or metadata.",
            "- Rev31 adds Lesson Library CRUD, upload/review, grant/sharing, Parent read/download and moderation operations without changing existing Parent, Teacher, BE1 or demo method/path declarations.",
            "- Broader FEAT-063 requirements not implemented as APIs in Rev31: Parent-Teacher child-profile grants, LessonOccurrence delivery/history/feedback, AI lesson/sketch generation, billing/quota endpoints, and new Story/video-generation endpoints. Existing BE1 profile/classroom routes and demo Story/video routes are not substitutes for those future contracts.",
            "- Lesson Library purpose, actor authorization, payloads, status codes, headers and errors are specified in `LESSON_LIBRARY_API_CONTRACT_DRAFT_REV29_20261028.md` (Rev31 reconciliation).",
            "- This is a static source/composition catalog, not a runtime OpenAPI export. No app startup, tests, Docker, live database or migration was run to produce it.",
            "",
        ]
    )
    OUTPUT.write_text("\n".join(lines), encoding="utf-8", newline="")
    print(f"Wrote {OUTPUT} with {len(rows)} route-purpose entries.")


if __name__ == "__main__":
    main()
