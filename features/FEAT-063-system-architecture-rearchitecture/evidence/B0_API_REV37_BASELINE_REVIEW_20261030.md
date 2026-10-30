# B0 — Đối chiếu catalog API Rev37 và baseline BE

- Ngày: 2026-10-30. Phạm vi: đọc catalog, source, lịch sử Git và evidence sẵn có; không khởi động backend, database, MinIO hoặc Modal và không chạy test runtime mới.
- Trạng thái: **PARTIAL / BLOCKED về provenance snapshot**. Đã đối chiếu tĩnh và phân loại trạng thái được catalog báo. Chưa tìm thấy OpenAPI JSON và báo cáo `EV-063-30` gốc nên chưa xác nhận độc lập commit, profile, flags hoặc toàn bộ kết quả lần chạy Rev37. Không kết luận B0 đã đạt toàn bộ tiêu chí.
- Baseline checkout: nhánh `feature/feat063-be-foundation`, HEAD `2cda6f5fdd79c069fb6221fabbb18e2fe9e3c603`; commit merge BE `9994692472ba08f6352b8958f0bd1a93611b1376`, gồm các parent `726108522d70d239c7466ebb69ad02df00643df0` và `111ae547007801d7d171dd12f3ac6f1085d22199`. `git diff --name-status 99946924 HEAD` chỉ thêm backlog Markdown, không thay đổi BE.
- Backlog yêu cầu: [B0 trong backlog Rev37](../plan/BACKLOG_API_REV37_SRS23_MODAL_20261030.md). Bản này là evidence review, không sửa plan hay cấp approval triển khai.

**Bổ sung sau review:** chủ task yêu cầu xuất snapshot mới. [Báo cáo snapshot offline](B0_OPENAPI_OFFLINE_SNAPSHOT_20261030.md) ghi kết quả 121/124 operation và đối chiếu method/path với catalog. Snapshot mới không thay thế OpenAPI JSON và evidence gốc bị thiếu; phần provenance lịch sử vẫn blocked.

## Provenance và những nguồn còn thiếu

Catalog `API_CONTRACT_CATALOG_FEAT063_REV37_20261030.md` do chủ task cung cấp có SHA-256 `56FC8BEA01360E11F73E45B2D43AC1897540B30BC8AE524CDE1ECEFACFBB1B88`. Git blob của file trùng `56fee2a1f54317f6fc79a34698da9b887701e001`, được thêm tại commit `e9ba2ddde46c576aff5dbd919ba3ab285b464a87` trên remote-tracking branch `origin/codex/feat063-rev38-ui-mockups-20261030`. Xem [catalog tại commit lưu bản](https://github.com/CaoDat-2410/Sketch2Life/blob/e9ba2ddde46c576aff5dbd919ba3ab285b464a87/features/FEAT-063-system-architecture-rearchitecture/artifacts/API_CONTRACT_CATALOG_FEAT063_REV37_20261030.md). Đây là commit **lưu tài liệu**, chưa chứng minh commit hoặc working tree đã dùng khi chụp OpenAPI.

So sánh Git cho thấy `backend/src` giống nhau giữa commit merge BE `99946924` và commit lưu catalog `e9ba2ddd`. Một số file test khác nhau và commit lưu catalog không có file triển khai Modal trên nhánh hiện tại. So sánh này không chứng minh snapshot được tạo từ working tree sạch của một trong hai commit hay test coverage tương đương.

Catalog dẫn tới `EV-063-30_openapi-local-compose-20261030.json` và `EV-063-30_API_CONTRACT_AND_FULL_STACK_VERIFICATION_20261030.md`. Tìm theo tên trong checkout, thư mục chứa catalog và lịch sử/ref Git local chưa thấy hai file này; điều đó không chứng minh chúng không tồn tại ở máy hoặc nơi lưu khác. Chưa có hash hai file, manifest, cấu hình hay log gốc để xác thực snapshot.

[STATUS tại commit lưu catalog](https://github.com/CaoDat-2410/Sketch2Life/blob/e9ba2ddde46c576aff5dbd919ba3ab285b464a87/features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md) là **nguồn thứ cấp** nói Rev37 có 1.259 API/contract test pass và 1 fail, Lesson Library DB 5/5, BE1 DB 3/4 và MinIO bị chặn. Tài liệu đó còn ghi full backend suite từng có 12 lỗi, lượt chạy lại sau sửa dừng ở 66%, không được tính là pass. Các con số này chưa được đối chiếu với EV-063-30 hoặc gắn chắc với HEAD hiện tại; không gộp chúng thành kết quả test của lượt B0.

## Kiểm tra 121, 124 và 135

Theo catalog, 135 là số operation trong inventory, không phải số API SRS mới đã hoàn tất. Snapshot Compose được mô tả có 124 operation trên 111 path; 11 operation candidate/fixture chưa mount. Bảng thống kê nhãn của catalog:

| Nhóm | Tổng | Kết quả được catalog ghi | Giới hạn |
|---|---:|---|---|
| BE1/classroom, gồm health gốc | 56 | 2 probe health PASS; 54 mount, chưa probe riêng | Chỉ probe health không chứng minh flow lớp học. |
| Demo/local flow | 35 | 2 PASS cho kiểm tra audio và ảnh quá lớn nhận 413; 33 mount, chưa probe riêng | Không chứng minh upload hợp lệ hay inference. |
| Lesson Library | 30 | 1 PASS từ chối request không xác thực bằng 401; 29 mount, chưa probe riêng | 401 không chứng minh flow nghiệp vụ có xác thực. |
| Storage example | 3 | BLOCKED — catalog nói không tải được image MinIO, chưa dispatch storage | Chưa xác minh MinIO thật. |
| Candidate/fixture | 11 | NOT RUN — không mount trong Compose | Không tự bật hoặc tính là flow SRS đã chạy. |
| Tổng | **135** | **5 probe PASS, 116 mount chưa probe riêng, 3 BLOCKED, 11 NOT RUN** | Đây là nhãn ở catalog, chưa đối chiếu EV-063-30. |

Catalog có thể dẫn test theo nhóm trong EV-063-30 cho các route chưa probe riêng; không suy ra các route đó fail hoặc chưa có bất kỳ family test nào. Không thấy nhãn SKIP riêng trong bảng catalog; số skip thực tế của suite chưa xác minh.

`56 + 35 + 30 = 121`; thêm 3 storage example thành `124`. [Plan backend Rev36](../plan/PLAN_REV36_BACKEND_SRS23_ALIGNMENT_20261029.md) ghi 121 operation vô điều kiện của baseline Rev31/32. Static source hiện tại tại [router_composition.py](../../../backend/src/sketch2life/interfaces/http/router_composition.py) và [app.py](../../../backend/src/sketch2life/interfaces/http/app.py) cho thấy nhóm storage chỉ mount khi composition là `combined`, `env` là `local` và `storage_example_enabled` là `true`; cờ này mặc định `false` tại [settings.py](../../../backend/src/sketch2life/infrastructure/config/settings.py). Điều này giải thích **khả dĩ** chênh lệch 121/124 về mặt cơ chế; chưa chứng minh cấu hình được dùng trong snapshot Rev37 hay tập route của hai thời điểm giống hệt nhau.

## Kết quả cũ liên quan, không phải test mới của B0

- [Rev33 non-AI test](REV33_NON_AI_API_TESTS_AND_LOCAL_MIGRATION_20261029.md) ghi Lesson Library HTTP suite **5 passed**, BE1 PostgreSQL **3 passed / 1 failed** do `CONSENT_NOT_EFFECTIVE`; storage example dùng adapter memory vì MinIO không chạy. Không suy ra MinIO hoặc BE hiện tại đã pass.
- [Modal smoke FEAT-061](../../FEAT-061-modal-qwen-vl-endpoint/evidence/BACKEND_DEMO_MODAL_SMOKE_20261029.md): BE demo dựa trên `529cbef9`, ảnh synthetic, Vision `SUCCEEDED`, client wall time 23,938 giây. Không phải test BE sau merge, không chứng minh chất lượng model hay flow SRS.
- [Dev backend sync](notes/DEV_BACKEND_SYNC_20261030.md) ghi 26 unit/contract test chọn lọc sau merge; PostgreSQL/MinIO và Modal không chạy trong kiểm tra đó. CI của commit merge được báo thành công, nhưng cấu hình CI chỉ chọn một tập file test; log chi tiết job không đọc được do HTTP 403, không suy đoán số skip.

## Việc cần để đóng B0

1. Xin chủ sở hữu Rev37 cung cấp nguyên bản OpenAPI JSON, `EV-063-30`, hash, commit/working-tree snapshot, profile và cờ lúc chạy; xác nhận có thay đổi chưa commit hay không.
2. Đối chiếu method/path, schema, số operation và kết quả/skip trong evidence với catalog và commit đã pin. Làm rõ 121/124 bằng dữ liệu gốc, không chỉ bằng phép cộng.
3. Cập nhật bảng provenance và đánh dấu rõ từng bằng chứng, sau đó BA/BE dùng bảng đã xác thực làm đầu vào B1. Nếu nguồn không còn, giữ B0 partial/blocked và quyết định có tạo snapshot mới theo scope và approval riêng.

Không có thay đổi code, dữ liệu, approval, dịch vụ hay provider trong lượt B0 này. Không có thông tin token hoặc dữ liệu trẻ được sử dụng.
