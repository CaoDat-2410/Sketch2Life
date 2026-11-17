# M1 fixture compatibility addendum (GA1)

Test-first regression thật: `test_legacy_canvas_fingerprint_matches_pre_g1_payload_and_profile_changes_it` đỏ vì `_store` fake trả object không có get_receipt. Mock này chỉ kiểm fingerprint, không có port/session thật; PostgreSQL boundary đã kiểm cap thật.

Trong phạm vi goal A1 cho phép test tương ứng, thêm đúng `backend/tests/unit/test_canvas_operation_profile.py` vào task M1: chỉ mock get_receipt→None/current_revision→1 và db.scalar→0 ở test fingerprint nêu trên. Không đổi assertion, profile hoặc test cases khác. Không giả số cap để làm test capacity xanh; cap có test PG riêng.

Plan M1 gốc giữ nguyên hash. Tổng điểm implementation lấy toàn canvas mọi epoch theo V4D1; cụm epoch hiện hành trong plan M1 không được dùng để bỏ qua điểm lịch sử. Replay/stale/CAS giữ nguyên.

Cổng: chạy lại bộ baseline590 cùng11test renderer mới; kỳ vọng601pass4skip; PG5pass; ruff/mypy chỉ lỗi mới, validators. Không source ngoài task, không commit/stage/push.
