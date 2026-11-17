# FEAT-064 — Quyết định và đề xuất

## Đã được chủ task chọn

- D-01, 2026-10-29: ưu tiên kiểm chứng luồng Child UI/BE1 hiện tại với Modal ở dev; luồng Parent/Teacher mới làm sau. Chỉ đạo được trích trong CONTEXT.md.
- D-02: nhiệm vụ hiện tại là lập kế hoạch. Không diễn giải thành phê duyệt implementation, migration, test DB, GPU hay publication.
- D-03, 2026-10-29, nguồn: chat của chủ task: chọn OD-3 phương án B, witness file cục bộ một host kèm bản chấp nhận rủi ro dư bằng văn bản. Restore cả máy về trạng thái cũ có thể mở lại lượt, gây thêm call Modal có phí trên dữ liệu giả lập; restore lặp có thể gây nhiều call/chi phí. Restore DB đơn thuần vẫn phải bị chặn. Đây là quyết định hướng plan, không phải implementation/live approval; bản chấp nhận phải được ghi riêng trong approval M3.
- D-04, 2026-10-29, nguồn: chat của chủ task: OD-1 chọn canvas dev tỉ lệ cố định, nền trắng, strokes-only, append-only; độ dày nét chuẩn hóa theo chiều rộng canvas, chỉ năm màu của palette, server từ chối ngoài profile. Pillow dựng PNG RGB từ accepted operations theo thứ tự revision, đầu nét và khớp tròn, nét một điểm xử lý khớp UI; receipt ghi version Pillow và renderer. Kích thước pixel cuối chốt ở T0 theo giới hạn admission. Đây là renderer pilot, không chốt stack cuối; lựa chọn này không tự cấp implementation/DB/live approval. Exact aspect, giá trị năm màu, stroke geometry và pixel size cần được pin trong contract T0 trước code.
- D-05, 2026-10-29, nguồn: chat của chủ task: OD-2 chọn bằng chứng synthetic riêng do server quản lý, tạo qua lệnh operator trong local/test với cờ pilot, gắn org/class/child/purpose/run/hạn dùng, có thu hồi. Mọi cổng consent đi qua hàm quyết định có kiểu `LEGAL_CONSENT` / `SYNTHETIC_DEV` / `DENIED`. Không tạo consent `effective`, không điền consent giả; cột consent của profile nullable có CHECK theo `data_origin`, dòng cũ là `LEGACY_UNCLASSIFIED` và bị từ chối. BE2 giữ `consent_effective=false`, dùng trường `eligibility_basis` có phiên bản. Bảng, tên trường, CHECK cụ thể, migration và danh sách call site chốt ở T0 theo inventory, giữ legal consent/real-data gates và fail-closed ngoài pilot. Đây là quyết định thiết kế, không cấp implementation/DB/migration/live approval.
- D-06, 2026-10-29, nguồn: chat của chủ task: OD-3 status-read chỉ cho Child đọc request của chính mình khi session `active` hoặc `paused`, khóa thiết bị khớp, grant và membership còn `admitted`, request thuộc đúng Child/canvas, eligibility hiện hành còn hiệu lực; không yêu cầu turn hoặc group active. Từ chối khi session `finished`, grant bị thu hồi hoặc khóa đã xoay; không thêm TTL cho grant. Cổng chỉ đọc, trả trạng thái được phép; lỗi từ chối dùng mã chung, UI giữ request ref và không gửi lại. T0 chốt `paused` có giữ hiệu lực request đang chạy hay không; đề xuất giữ request đang chạy nhưng không cho request mới, chưa là quyết định đã chốt. Chốt contract và các trường hợp deny khác ở T0; không cấp implementation/DB/live approval.
- D-07, 2026-10-29, nguồn: chat của chủ task: OD-4 chọn Person 2 là integration owner, điều phối file dùng chung và thứ tự migration, ký `OwnerFenceV1` cùng owner BE1/BE2 được nêu tên ở T0; Person 2 đồng thời là operator live. Phiên AI chỉ thực thi theo approval, không là owner. Phần phụ thuộc hợp đồng dừng nếu thiếu người đồng ký. Danh sách method UoW cần dùng/fail-closed và phân công từng task chốt ở T0; giữ review độc lập tại các cổng T0, T7a/b/c và trước T13. Quyết định phân công không tự cấp implementation/DB/migration/live approval.
- D-08, 2026-10-29, nguồn: chat của chủ task: owner BE1 là GitHub `CaoDat-2410`; owner BE2 là chủ task/Person 2, GitHub `AnhKhoaa157`. Person 2 đồng thời là integration owner và operator live theo D-07. Đây là ghi nhận phân công, chưa chứng minh BE1 hoặc BE2 đã đồng ký `OwnerFenceV1`; T0 cần ghi việc đồng ký của những người cần thiết, thiếu đồng ký thì dừng phần phụ thuộc. Phân công này không cấp implementation/DB/live approval.
- D-09, 2026-10-29, nguồn: chat của chủ task: khi session chuyển `paused`, request AI đang chạy tiếp tục xử lý, không nhận request mới. Quyền đọc status áp dụng D-06; các điều kiện eligibility, thu hồi và source freshness vẫn phải được kiểm tra. T0 đặc tả behavior/contract và test, không tự suy đây là approval implementation/DB/live.

## Đề xuất để duyệt, chưa phải quyết định được chấp thuận

- P-01: pilot dùng canvas mới, synthetic, append-only, nét vẽ trên nền trắng. Từ chối history/overlay chưa được hỗ trợ thay vì âm thầm bỏ lớp ảnh đang thấy.
- P-02: tạo nguồn từ operation đã được server chấp nhận, schema nét vẽ có version và export nhất quán tại epoch/revision; không coi checksum của JSON client là chứng minh derivation.
- P-03: dùng CPU rasterizer hẹp; Pillow có sẵn là một ứng viên. Chốt geometry/width/aspect/determinism và ADR trước code, không đóng stack production.
- P-04: eligibility synthetic do server kiểm soát trong môi trường cô lập, không tạo consent pháp lý giả và không mở cổng cho REAL/LEGACY_UNCLASSIFIED. Inventory registry/session/shared/records/artifact/BE2 và required profile consent refs phải có disposition/representation owner duyệt; phối hợp subset FEAT-063, không mặc định nhận Rev33.
- P-05: Vision `image_only` qua `/v2/vision` cho trường hợp policy cho phép. Không nới C1/C2, không giả hỗ trợ typed context; trường hợp cần C2 phải từ chối hoặc được lập scope riêng.
- P-06: dùng provider/config hiện có; không tạo enum provider Modal. Tạo runtime observation boundary được duyệt, provenance có version trung thực, tách khỏi evidence offline cũ.
- P-07: T7a minimal durable assistance/analysis repositories+migration, T7b owner-signed fence/UoW, T7c invocation ledger/run manifest có review riêng; baseline chỉ có in-memory stores và fixture fence. Chỉ state/receipt/reservation/review pointer cho selected path, không đầy đủ cache/billing/video/Parent targets.
- P-08: kết thúc ở Teacher thấy kết quả nhận diện `unconfirmed/pending`; Child chỉ thấy trạng thái. Không approve tự động, không phát Sketch hay tiến stage.
- P-09: sau CPU và live approval, tối đa một provider call; pilot max_attempts=1, run do operator/server tạo với approval/expiry/DB identity. Mất/reset/rollback ledger vô hiệu quyền live; invocation UNKNOWN không mở cap, A1 accounting giữ riêng. Owner khởi động/dừng Modal, không xóa marker FEAT-061.
- P-10: status-own dùng verified identity/grant/request scope và current disclosure/eligibility riêng, không yêu cầu active turn như write; revoke/expired grant vẫn deny, poll unavailable không resubmit.
- P-11: panel Teacher analysis-only riêng, không đổi trang Sketch approval; frontend dùng components/style có sẵn, asset/visual mới theo generated/provenance/visual-approval/approved/applied của AGENTS.

Các đề xuất P-01–P-11 cần được chuyển thành hợp đồng/ADR và phạm vi owner cụ thể trong T0 của plan. OD-1 chọn theo D-04, OD-2 theo D-05, OD-3 chọn B về witness, status-read D-06 và paused D-09, OD-4 chọn owner theo D-07/D-08; exact contracts/migration, đồng ký thực tế và phân công task còn mở. Approval một card cũ không tự mở quyền cho card khác.

## Phiếu quyết định T2B và T3 — 2026-11-01

- **D-10 — T2B, BE1 → BE2 facts:** A1 `Sửa`: thêm `age_revision` (bắt đầu 1, tăng khi tuổi đổi) và `age_source` có miền giá trị được kiểm soát; provenance tạo từ hai trường, hàng cũ không rõ nguồn dùng `LEGACY_UNKNOWN`, không suy từ ID/timestamp/session revision. A2 `Đồng ý`: chỉ `SYNTHETIC_DEV` được nullable consent ref/revision và `consent_effective=false`; `LEGAL_CONSENT` giữ nguyên yêu cầu. A3 `Sửa`: dùng digest có version làm token freshness toàn context; giữ `ContextDecision.context_revision` integer và thêm field digest rõ kiểu, so sánh equality. A4/A5 `Để sau`; A6 `Đồng ý`: T2B chỉ `MemberFact` và `ContextDecision`. Đây là quyết định thiết kế, không cấp quyền code/schema/migration.
- **D-11 — T3, stroke profile/canvas:** B1–B4 `Đồng ý` với giá trị trong T0; server ghim profile immutable vào session, client gửi đúng version, mismatch/hạ cấp bị từ chối, session cũ không bị diễn giải lại. B5 chọn A và B6 chọn B nhưng tách task sau T3; B7 `Đồng ý`. B8 `Sửa`: T3 §1 nguồn mà phiếu viện dẫn không có trong nhánh hiện tại; không tự dựng allowlist, implementation bị block đến khi danh sách gốc được khôi phục hoặc được duyệt lại. Đây là quyết định thiết kế, không cấp quyền implementation.
- **D-12 — operational follow-ups:** T12 PostgreSQL chờ database dùng-một-lần và `BE1_TEST_DATABASE_URL` được cấu hình cục bộ cùng approval riêng; B4b hoãn; cần báo Hiếu 31 test `test_live_image_demo_api.py` fail khi thiếu MinIO/AWS nhưng chưa gửi tin nhắn; D-114 được tham chiếu là D-119 trong nhánh Swagger hiện tại. Phiếu này không cấp quyền gửi tin.
- Nguồn và phần hiệu chỉnh A3 sau source review: `evidence/OWNER_DECISIONS_T2B_T3_20261101.md`.

## GOAL A2 — dùng database BE tổng hiện có (2026-11-03)

- **D-13:** Chủ task yêu cầu A2 dùng database BE tổng hiện có `sketch2life` thay cho database task-owned riêng. Mục tiêu kỳ vọng theo quan sát trước là PostgreSQL 17.11, loopback `127.0.0.1:5433`, user/owner `postgres`; phiên triển khai phải xác minh lại danh tính chỉ đọc trước khi ghi. Chỉ dữ liệu synthetic mới do fixture A2 tạo được phép ghi/xóa theo chính ID của lượt đó. Cấm migration/schema change, reset/drop/truncate, dọn hàng cũ hay ảnh hưởng hàng BE hiện hữu. Quyết định chỉ mở gate DB của A2; không áp dụng cho B1/B2 và không thay thế launch riêng. Chi tiết: `plan/CHAIN_A2_MAIN_BE_DB_ADDENDUM_20261103.md`.

### Review disposition for D-13 (2026-11-03; not a new owner decision)

Independent review concluded **A2 Rev3 overall ACCEPTED / complete** within the approved A2 plans/addenda. This review disposition records completion of D-13's A2 scope; it does not expand D-13 to B1/B2 or authorize their execution. See `evidence/A2_REV3_INDEPENDENT_REVIEW_CLOSEOUT_20261103.md` for the reviewer thread and remaining evidence limitations.

## GOAL B2 — quyết định owner và điều kiện review (2026-11-05)

Các mục trong phần này không gán mã D-xx vì approval và ledger không quy định mã quyết định cho chúng.

### Owner-recorded decisions and limits

- Owner chấp nhận giới hạn T12: round-trip chỉ nhánh pilot_vision ở trạng thái trung gian với bảng pilot rỗng; không coi đây là round-trip toàn đồ thị hoặc có dữ liệu. Phần DB của test_migrations.py NOT RUN.
- Owner chấp nhận mypy không có verdict cho test_be1_postgres_api.py làm giới hạn đã ghi. INTERNAL ERROR không phải PASS; chưa xác định lỗi đã tồn tại trước B2 hay phát sinh trong B2.
- OpenAPI P3 được hoãn tới trước khi frontend/client tích hợp hai route POST submit/cancel.
- OWNER_MODAL_CALL_APPROVED=NO; không có quyền gọi live từ các kết quả review này.

### Independent review disposition — không phải owner acceptance

Review vòng ba khuyến nghị ACCEPTED_WITH_CONDITIONS, không có P1. B2 vẫn NEEDS_REVISION cho tới khi owner quyết định riêng. N-1 yêu cầu test PostgreSQL mức route cho POST request/cancel trước D9 hoặc frontend. T13 chỉ chứng minh timeout của hàm script-local với stub. Stale-owner orphan B1 vẫn là điều kiện trước dữ liệu không synthetic hoặc provider. Mọi dữ kiện PostgreSQL là owner-run, chưa được reviewer xác minh bằng kết nối DB độc lập.

## GOAL B2 — owner acceptance with conditions (2026-11-05)

Các mục dưới đây không gán mã D-xx vì approval và ledger không quy định mã mới.

Owner chấp nhận Goal B2 ở trạng thái ACCEPTED_WITH_CONDITIONS theo chỉ thị trực tiếp "Chấp nhận B2", dựa trên khuyến nghị review độc lập vòng ba cùng trạng thái, không có P1. Đây là quyết định owner; reviewer không quyết định thay owner.

Phạm vi chấp nhận là T9, T13 và T12 theo plan B2 cho pilot local/test synthetic, default-off, loopback stub. T12 đóng có điều kiện: round-trip chỉ nhánh pilot_vision trạng thái trung gian với bảng pilot rỗng; không dữ liệu, không story_run_lite, không toàn đồ thị. Phần DB test_migrations.py NOT RUN; mypy test_be1_postgres_api.py NO VERDICT; dữ kiện PostgreSQL là owner-run.

Điều kiện còn ràng buộc: OpenAPI P3 trước frontend/client; orphan stale-owner B1 trước dữ liệu không synthetic/provider; T13 chỉ là timeout của hàm script-local với stub; N-1 cần test PostgreSQL mức route child request → job → status trước D9/frontend; N-3 ghi nhận rerun dùng runner không pin hash và runner đối soát không còn trong thư mục script cục bộ, nguyên nhân chưa biết.

Chấp nhận B2 không cho phép Modal/GPU/provider/live (`OWNER_MODAL_CALL_APPROVED=NO`), commit/push/merge/stage, xóa/dọn DB, gộp nhánh origin/codex/feat063-modal-backend-completion-20261103, bắt đầu goal sau B2, dùng dữ liệu không synthetic/provider thật hoặc tuyên bố production readiness.
