# M1 — evidence GOAL A1 (XONG-CHƯA REVIEW)

- V4D1/goal A1 owner-approved. Plan SHA `D27E902D268200F954758F26D262DA6E1D3A3D1D3F470AF05A9442D4863B418F`; fixture addendum SHA `49E05F5BEF07A235489DA626D28F40F8F6FC6C2C3DC72B4B2F5A396B149C6723`. Approvals append-only.
- 500 nét/60.000 điểm: receipt replay trước cap, stale revision trước cap, SUM JSONB an toàn với non-array, scope org/session/canvas mọi epoch. CAS service/store gốc không đổi. Revision−1 là cận trên nét do restore tăng revision, như owner chấp nhận. Giữ nguyên profile/domain.
- Export cũ vượt cap409 CANVAS_SOURCE_TOO_LARGE; append409 CANVAS_CAPACITY_REACHED. Renderer slot1; deadline6s từ đầu handoff bao gồm chờslot/export/admission/persist, 503BUSY/DEADLINE. Kiểmgiữa strokes vàpha. Deadline hợp tác, không preempt C-call. Nếu commit hoàn tất sau budget, trả503 nhưng artifact/metadata đúng provenance đã commit được giữ; không xóa file đã được metadata tham chiếu. Không hứa SLA production.

| Lớp | Kết quả |
|---|---|
| L1 | Profile/domain/DTO không đổi bytes so GA1_BASE; các test profile xanh. |
| L2 | Không sửa application/service/store. |
| L3 | Không migration; PG SUM/replay/CAS boundary kiểm thật. |
| L4 | Unit test-first9fail1pass; thêm canonical-array safetytest, cuối11mới+9cũ=20pass. |
| L5 | PG4 ca capacity/export đỏ trước sửa; sau cap4pass và deadlinecase1fail; nối budget rồi PG5pass (lượt cuối7.69s). |
| L6 | DEFERRED-BY-OWNER. |
| L7 | Baseline590pass4skip; sau11testmới601pass4skip7.83s. PGsyntheticpilot56pass66.02s; F2/APIbaseline4pass2.76s trước M1. |

- Test fixture fingerprint cũ dùng object thay port nên đỏ do không get_receipt. Addendum bổ sung fake receipt/currentrevision/db.scalar; không sửa assertion fingerprint; baseline phục hồi. Đây là sửa test wiring, không bypass cap sản phẩm.
- PG dùng owner-created loopback acceptance DB, Settings(_env_file=None); sau các lượt bảng từng số hàng khớp mốc98application/561rows; chỉ dọn hàng synthetic của test. Không DROP/TRUNCATE/migration hoặc mạngngoài.
- Ruff7file task sạch;7file đúngformat. Mypy6file còn đúng4lỗi có trước trong2router (responses2, record_response thiếuannotation, rowcount); so shadowbaseline cũng4lỗi; không lỗi mới. 3file renderer/newunit do revieweragent kiểmstrict riêng xanh.
- Validators chạy thật HARNESS_VALID; REPOSITORY_SECURITY_VALID (6042 file trước report); ARCHITECTURE_VALID; gitdiffcheck sạch. Independent reviewread-only không findingchặn; chưa ownerreview, không đặt REVIEWED.
- UI contract: khi409capacity giữ canvas và không tự gửi lại nét; hiển thị đạtgiớihạn; nguồn ảnh vượt trầnkhông gửiAI; renderbusy/deadline503 giữrequest/source chưa hoàn tất và để người lớn quyết. UIcode/visual NOTRUN.
- M1 file paths mới/sửa theo manifest snapshot;7hash owner giữ nguyên, HEAD/index không đổi. Không commit/stage/push/Modal/GPU/provider/dữ liệu trẻ thật.
