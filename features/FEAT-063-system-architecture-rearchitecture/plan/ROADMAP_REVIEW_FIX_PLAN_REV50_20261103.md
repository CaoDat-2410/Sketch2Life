# Plan Rev50 — sửa roadmap sau independent review vòng 2 — 2026-11-03

## Mục tiêu

Sửa các finding có căn cứ trong review vòng 2 cho roadmap BE Parent/Teacher sáu mốc; sửa lại những kết luận ở disposition Rev49 mà đối chiếu local cho thấy chưa chính xác. Đây là cập nhật tài liệu và điều kiện lập kế hoạch, không phải quyết định sản phẩm, approval triển khai hay goal thực thi.

Owner instruction tiếp tục áp dụng: “lấy những phần review của claude đúng và sửa và cũng chỉ ra cho nó tại sao chỗ đó của nó lại sai đi”.

## Baseline đã đối chiếu

- Branch/HEAD/index lúc bắt đầu: `feature/feat063-be-foundation` / `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9` / rỗng.
- Roadmap Rev49: `plan/BE_PARENT_TEACHER_VISION_DEMO_ROADMAP_20261102.md`, SHA-256 `9DF3FECF0FFF45972ADFB4D49A50E31773CBAD8832F0B5C5B625C9702CEB49CC`.
- Disposition Rev49: `evidence/CLAUDE_ROADMAP_REVIEW_DISPOSITION_20261103.md`, SHA-256 `72150BEC8A624D03E6205CE40C2AA9A48942BCF8A1D7CA0A40BAF8CC60851A1E`.
- SRS v2.3-draft: SHA-256 `DCBF9786FF8983E34F2D3B4EBAB76301D0C52A6C9DE72CD08D0816BBD0D983FC`; chưa sign-off.
- DTR working copy: SHA-256 CRLF `3E793BB2C62C9E6C50780DE636EDDE442D382C62B4643552F2298AF374171E22`; nội dung chuẩn hóa LF SHA-256 `201D381C5025BF6BB5EA2415E916835EB291AFE96CD948D76C0DC5604C28D1B2`.
- A2 local closeout: `features/FEAT-064-current-flow-modal-vision-dev/evidence/A2_REV3_INDEPENDENT_REVIEW_CLOSEOUT_20261103.md`, SHA-256 `10B12F4417A5E29DF0ED1697F33A8FAA08D692E71015998CCC8DE297328A1C36`.
- FEAT-064 A2→B1→B2 sequential goal: SHA-256 `D7DEE2977C5AA28B26FCB117281DE8B23E4D4AA85A42922B8B37752FBDA8752A`; tài liệu này không đủ để xác định phase nào đang chạy.
- B0–B13 plan hiện tại SHA-256 `773C4A8340C8E33AE39764D920B042AC19BACBAF6DC561FE9D5D3DFFCC4B5A5A`; report đang ghi SHA `03AEA386B8545624100688B68AA828A84CD154B47857CB5E98FB06354D6BB582`. Đây là lệch nội dung/provenance chưa giải quyết; không tự thay hash được phê duyệt.

## Phạm vi được phép

Chỉ cập nhật:

1. `plan/BE_PARENT_TEACHER_VISION_DEMO_ROADMAP_20261102.md`.
2. `DECISIONS.md` để loại ID trùng và giữ nguyên nội dung lịch sử.
3. `evidence/CLAUDE_ROADMAP_REVIEW_DISPOSITION_20261103.md` để ghi disposition vòng 2 và phản hồi có thể gửi reviewer.
4. `CONTEXT.md`, `SOURCE_REGISTER.md`, `status/STATUS.md`.
5. File plan này và một entry append-only trong `approvals/TASK_APPROVAL.md`.

Không sửa SRS, DTR, backlog B0–B13, mã nguồn, tests, migrations hay hồ sơ FEAT-064. Không truy cập/sửa DB, không gọi Modal/provider/mạng, không thao tác Git history/index/remote, không stage/commit/push/merge. Bảo toàn các thay đổi local khác.

## Nội dung phải xử lý

1. **Quota M5/M6:** M5 phải có Billing `video_quota_grants` và `video_quota_usage` hoạt động cho Parent scope, tháng `Asia/Ho_Chi_Minh`, included trước rồi top-up FIFO, concurrency/AT-06/AT-09, request/run cap BR-11 và AI Policy compute reservation có lease/release/reconcile. Cùng idempotency key; reservation + admission + usage receipt hoàn tất trước accepted/dispatch theo BR-38. M6 mở rộng commerce (price/invoice/payment/top-up/subscription/capacity), Teacher/school scope và quota summary; không dời gate M5 sang M6.
2. **Lesson access M4/M5:** SRS cho phép Parent run không có lesson. Roadmap đặt no-lesson flow làm đường mặc định ban đầu của M4/M5; optional lesson-version/script-following/activity-list chỉ bật khi current authorization/read contract, revoke/unpublish behavior và dependency Lesson đã có. Phase plan phải chọn rõ một trong hai: giữ no-lesson scope, hoặc xin approval kéo phần đọc quyền tối thiểu lên sớm. Synthetic lesson fixture không chứng minh authorization; không public fallback khi ref bị revoke/unpublish.
3. **Q146:** ghi rõ Q146 đã được trả lời về sản phẩm. Parent line-sketch có thể được lên lịch theo quyết định đó; model/version, license, cost, safety, retention, synthetic POC và SRS sign-off vẫn là các gate riêng. Hoãn lịch không phải chờ trả lời Q146.
4. **Lifecycle:** phân công +144h đúng một inbox reminder và +168h adult-wait closeout theo BR-39/FR-C-11/FR-B-14/NFR-26/AC-22/30; từng milestone sở hữu cancel, late-result handling, purge hoặc debt cho artifact do nó tạo. Video-job cancellation thuộc M5; nêu debt D-127 ở M2.
5. **Model gates M3/M4:** trước M3/M4 cần synthetic POC và owner chọn model/version cùng license/cost/safety/retention/capacity gates. Không ghi Qwen3-VL là lựa chọn: SRS đánh dấu NO_GO; Qwen2.5-VL-7B là candidate, Whisper và Qwen2.5-7B chưa benchmark.
6. **A2 entry gate M2:** mang theo đúng giới hạn trong closeout local: 58 synthetic rows còn trong shared `sketch2life`; physical schema chưa đối soát Alembic history; mypy còn một baseline protocol issue. Trước migration M2, đối soát trên DB task-owned cô lập hoặc có quyết định an toàn riêng; ghi disposition hàng còn lại, không tự xóa/reset DB dùng chung; ghi baseline/type-check exception và không thêm lỗi mới trong scope M2.
7. **B-ID và độ rộng phase:** thống nhất B10: job/idempotency foundation ở M2; Parent quota/usage/compute gate ở M5; commerce và Teacher/school mở rộng ở M6. Gắn pointer trong backlog lịch sử về roadmap hiện hành. B4b chỉ sau OI-05..08; M2 từ chối `REAL`/`LEGACY_UNCLASSIFIED` nếu consent gate chưa đạt. M2/M6 phải được chia subphase trong plan riêng trước khi launch goal. Chuyển “không video trước script approval” thành M5 entry/dispatch gate.
8. **Ưu tiên và trạng thái:** nói rõ chuỗi A2→B1→B2 là luồng điều phối riêng có thể tạm giữ ưu tiên thực thi trước M2–M6; phase đang chạy phải lấy từ active implementation thread, không suy ra từ header DRAFT của file goal. Không tuyên bố B1/B2 hay M2–M6 hoàn tất.
9. **Decision IDs:** đổi OpenAPI decision Rev45 từ D-130 thành ID trống D-131. Giữ nguyên quyết định Full BE API inventory là D-130. Đổi bảng Swagger lịch sử có ID D-114..D-119 thành mục lục/tóm tắt lịch sử không mang decision ID để không trùng với các quyết định hiện hành.
10. **Provenance và local visibility:** DTR mismatch vòng 2 là line-ending-only: chuẩn hóa bytes local CRLF sang LF tái tạo SHA `201D…D1B2`; không gọi đây là khác nội dung. B0 plan/report mismatch là khác nội dung thật; yêu cầu owner xác nhận lại plan hiện tại `773C…B5A5A` hoặc addendum trước khi dùng làm authority. Ghi rằng cloud reviewer không thể xác minh source register và A2/sequential records local-only; đó là giới hạn quan sát đúng, không phải lỗi của reviewer. Sửa lại disposition Rev49 đã gán nhầm D-130 và mô tả sai DTR.

## Tiêu chí chấp nhận

- Từng finding N1–N7 và các điểm P2/P3 liên quan có kết quả rõ trong roadmap/disposition; phần phụ thuộc owner vẫn là gate, không tự quyết thay owner.
- Không có decision ID trùng trong các mục đang mang ID; D-130 và D-131 mỗi ID chỉ có một quyết định.
- Các giới hạn A2, SRS draft, B0 provenance và phạm vi local-vs-cloud được mô tả đúng nguồn/thời điểm.
- Context/source register/status trỏ đúng plan/disposition và hash mới.
- Chỉ các file trong allowlist thay đổi; `git diff --check` sạch; branch/HEAD/index không đổi.
- Kết thúc `FIXED — XONG-CHƯA REVIEW`; không tuyên bố review cloud đã ACCEPTED.
