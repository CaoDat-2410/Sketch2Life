# B0 — Snapshot OpenAPI mới của BE hiện tại

- Ngày: 2026-10-30. Chủ task yêu cầu tạo snapshot mới sau review B0.
- Nguồn: nhánh `feature/feat063-be-foundation`, HEAD `2cda6f5fdd79c069fb6221fabbb18e2fe9e3c603`, BE merge `9994692472ba08f6352b8958f0bd1a93611b1376`. Tại thời điểm xuất, `git diff HEAD` với `backend/src`, `backend/pyproject.toml`, `backend/uv.lock` không có thay đổi và không có file chưa theo dõi trong `backend/src`. Các file tài liệu ngoài phạm vi vẫn đang sửa dở; không kết luận toàn bộ working tree sạch.
- Đây là **snapshot mới offline**, không phải file OpenAPI gốc của Rev37, không phục hồi lịch sử hoặc xác minh kết quả test Compose cũ.

## Phương pháp và phạm vi

[Script xuất snapshot](b0_generate_openapi_offline.py) dùng Python venv backend, `create_app(_composition_profile="combined").openapi()`, cấu hình `env=local`, `auth_provider=development`, `ai_provider=disabled`; chạy hai lượt với `storage_example_enabled=false` và `true`. Script loại các biến `SKETCH2LIFE_` và `AWS_` khỏi process mà không in giá trị; `Settings.model_construct` không đọc `.env`. Constructor BE1 runtime và storage client được thay bằng stub trong process để không tạo engine DB, đọc chuỗi credentials AWS hay tạo runtime storage. Socket connect bị chặn; không chạy lifespan, HTTP request, DB, MinIO, AI provider hay Modal. Vì vậy đây là kiểm tra **schema/router registration**, không phải runtime Compose hay kiểm tra nghiệp vụ.

Môi trường: Python `3.12.10`, FastAPI `0.141.1`, Starlette `1.6.0`, Pydantic `2.13.4`, pydantic-settings `2.15.0`. Đây là phiên bản local tại lúc xuất, không khẳng định trùng các package trong Compose cũ. Script SHA-256 `FC06BF5CCC60985C8012680DD78F1024B44D2B81286779256CF694FCFF1D03C0`.

## Artifact và kết quả

| Cấu hình | Artifact | Operation / path | SHA-256 |
|---|---|---:|---|
| Storage example tắt | [OpenAPI JSON](B0_openapi_combined_storage-off_20261030.json) | 121 / 109 | `252D318DB7F97F94FC81C6483F0B0E56E62DE87036041BEE5E0D85889304DBF1` |
| Storage example bật | [OpenAPI JSON](B0_openapi_combined_storage-on_20261030.json) | 124 / 111 | `F139B41B6EBC1EA61CDDEB99003F62D08E17C7DB42CF8BB23959DCAEB417808B` |

Chênh lệch đúng ba operation: `POST /api/dev/v1/storage-examples/lesson-source-documents`, và `GET`/`DELETE /api/dev/v1/storage-examples/lesson-source-documents/{object_id}`. Route xuất hiện trong OpenAPI không chứng minh storage hoạt động hoặc MinIO khả dụng.

Catalog Rev37 do chủ task cung cấp có SHA-256 `56FC8BEA01360E11F73E45B2D43AC1897540B30BC8AE524CDE1ECEFACFBB1B88`. Trích được 135 dòng method/path: 124 có nhãn mount và 11 candidate/fixture chưa mount. Chuẩn hóa converter `{asset_ref:path}` trong catalog thành `{asset_ref}` như OpenAPI; so sánh tập `(method, path)` của 124 dòng mount với snapshot mới bật storage:

- Chỉ có ở catalog: **0**; chỉ có ở snapshot: **0**.
- Candidate/fixture của catalog xuất hiện trong snapshot: **0 / 11**.
- Framework `/openapi.json`, `/docs`, callback OAuth và static `/renderer` không tính vào tập operation trên.

**Giới hạn:** phép so sánh chỉ kiểm method/path, không so đầy đủ schema, request/response, auth, errors, logic, chất lượng, test results hay phiên bản phụ thuộc. Catalog Rev37 preview trường không thay thế OpenAPI JSON gốc. Không gọi route nào trong lượt này; không gán PASS nghiệp vụ cho 121/124 operation.

## Trạng thái B0

Theo dõi hai phần riêng: **B0a đạt phạm vi baseline offline mới** (`combined` với storage bật/tắt, không phải test runtime); **B0b blocked** về provenance/kết quả lịch sử Rev37. B0b không chặn B1 sử dụng baseline mới; không gọi toàn bộ B0 đã hoàn tất. Chưa xuất snapshot riêng cho `classroom`, là profile dự kiến của pilot FEAT-064.

Snapshot mới xác nhận được chênh lệch 121/124 trong cấu hình offline được mô tả và sự trùng method/path với 124 dòng catalog Rev37. Còn **BLOCKED đối chiếu lịch sử**: thiếu OpenAPI JSON và `EV-063-30` gốc, commit/working tree và cấu hình thực tế lúc chụp, nên chưa xác nhận kết quả test Compose cũ. Xem [báo cáo B0 ban đầu](B0_API_REV37_BASELINE_REVIEW_20261030.md) để phân biệt evidence cũ và công việc còn thiếu.

Không có code sản phẩm, approval, cơ sở dữ liệu hay provider nào được thay đổi. Tại thời điểm lập báo cáo, các artifact mới còn ở local và chưa commit/push.

Bổ sung trạng thái publication: artifact/script được commit `61c25690`, hai báo cáo tại `bbb43293` và đã push theo yêu cầu chủ task. Việc publish evidence không bổ sung bất kỳ kết quả test runtime nào.
