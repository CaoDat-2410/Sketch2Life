# G6 review fixes — báo cáo thực hiện

Ngày: 2026-11-01. Đây là lượt TREO KHÔNG COMMIT riêng, không đổi trạng thái goal G2–G6.

- Plan: `plan/G6_REVIEW_FIXES_PLAN_20261101.md`; SHA-256 `F17A53203EFCD901FDA058FFF329D8EEFFBA28A87117D9CCD2D19E26FA62416B`.
- HEAD giữ nguyên `1e93bc3f3ac645cf4baecbbc09c73afe48719c92`; nhánh `feature/feat063-be-foundation`; index rỗng.

## Kết quả F1–F4

| Mục | Trước | Sau / kết quả | File trong lượt này |
|---|---|---|---|
| F1 — đếm route BE1 | Test PostgreSQL thất bại tại kỳ vọng 50 path; app thực tế có 51 path và 56 operation (kỳ vọng cũ 55). | Sửa hai assertion thành 51/56. Test F1 xanh trong lần chạy module cuối: module có 3 passed, 1 failed (lỗi còn lại là F2). Kiểm kê độc lập cũng là 51/56. | `backend/tests/integration/test_be1_postgres_api.py` |
| F2 — fixture consent | Test dừng với HTTP 409 `CONSENT_NOT_EFFECTIVE`. | **BLOCKED.** Patch alias test-local trong `be1_canvas` vẫn không qua: `get_verified_device` tại `be1_runtime` kiểm tra consent sớm hơn và có alias riêng. Cần thêm patch thứ ba, vượt phạm vi F2 đã duyệt. Không thêm patch đó, không thêm test âm và không đổi guard sản phẩm. | Không có thay đổi cuối cùng ngoài hai assertion F1 trong cùng file. |
| F3 — báo cáo T12 | Bản đã commit và bản hiện tại khác nhau về việc fixture B5 có tự dọn hàng hay không. | Sao chép nguyên byte bản HEAD; SHA-256 `98DE23DFEE611B491E90FFEA9DDAAB82962D4D0565253E9C6885CD1C80574D63`. Đã nối phần đối chiếu: không có log hoặc số đếm B5 riêng để phân xử, nên ghi **MÂU THUẪN CHƯA PHÂN XỬ** và đề xuất lượt kiểm riêng có approval. | `evidence/notes/T12_LITE_POSTGRES_REPORT_20261101.md` (append-only); `..._RUN1_AS_COMMITTED.md` (bản sao mới). |
| F4 — Ruff | Ruff cài trong backend venv là 0.16.4; `backend/pyproject.toml` khai báo `ruff>=0.12,<1`, line length 100; `backend/uv.lock` khóa 0.17.2. | Check toàn bộ 17 file Python đổi/tạo: còn I001 trong `test_be1_postgres_api.py`; format-check báo `test_app_composition.py` và `test_be1_postgres_api.py`. Không sửa thêm các file đó. Sửa import order duy nhất trong `test_canvas_source_render.py`; check và format-check riêng hai file được nêu trong F4 (`test_canvas_source_render.py`, `test_openapi_contract_catalog.py`) đều đạt. Không kiểm được bản 0.17.2 đúng lock trong môi trường này. | `backend/tests/unit/test_canvas_source_render.py` (chỉ import order). |

## Kiểm thử

- Contract suite (không gọi mạng): **1381 passed** trong 72.19 giây. `tests/contract/test_live_image_demo_api.py` **NOT RUN** vì cần mạng ngoài. Bài test phụ thuộc `.git` chạy đạt trong repo hiện tại.
- Unit suite: **6204 passed, 13 failed, 24 skipped, 12 collection errors**. 12 lỗi collection: 11 thiếu `imageio`, 1 thiếu `imageio_ffmpeg`. Trong 13 lỗi: một kiểm tra source closure nhận 20 nguồn thay vì 19; bảy kiểm tra semantic thiếu `backend/data/activity-catalog/golden/v1/semantic-anchor-profiles.v1.json`; một kiểm tra whiteboard cần `imageio`; một kiểm tra Lightning dùng thư mục `/tmp/story-video-artifacts` bị từ chối quyền (chạy riêng với thư mục tạm hợp lệ thì đạt); ba kiểm tra Pixi thất bại ở lượt suite nhưng đều đạt khi chạy lại riêng. Không cài gói và không sửa các lỗi ngoài phạm vi.
- PostgreSQL BE1 API module: **3 passed, 1 failed**; F1 đạt, F2 còn HTTP 409 `CONSENT_NOT_EFFECTIVE`. Không in/ghi chuỗi kết nối.
- PostgreSQL synthetic pilot module (gồm T4/T5): **56 passed** trong 63.45 giây.
- Validator cuối: `validate_harness.py` → `HARNESS_VALID`; `validate_repository_security.py` → `REPOSITORY_SECURITY_VALID` (6035 file); `validate_architecture.py` → `ARCHITECTURE_VALID`; `git diff --check` → exit 0, không có diff lỗi whitespace.
- Ruff trên hai file F4 được phép: `ruff check` → `All checks passed!`; `ruff format --check` → `2 files already formatted`.

## Ranh giới và trạng thái cuối

- M1 (trần số thao tác/thời gian), M3 (checkpoint chặn export) và route để Teacher xem PNG vẫn cần owner quyết định; không thực hiện ở lượt này.
- Không sửa mã dưới `backend/src`, guard, consent, schema, migration hay OpenAPI catalog. Không chạy Modal/GPU/provider/mạng ngoài; không dùng dữ liệu trẻ thật.
- Bảy file owner bảo vệ giữ đúng prefix hash: SOURCE_REGISTER `0B43E4BA`, FEAT-063 CONTEXT `E7C8143A`, STATUS `F1ADB793`, REMAINING_AI `8BBFD0ED`, REV36_DELTA `B61B0607`, VIDEO_FLOW `93374E96`, S1_DECISION_CARD `4D95D303`.
- So với snapshot G2: hai file nguồn T4 `be1_runtime.py` (`59A2CA1A…`) và `be1_canvas.py` (`62333F14…`), cùng `test_canvas_source_export.py` (`045228A9…`), giữ nguyên hash. `test_be1_synthetic_pilot_postgres.py` khác hash G2 (`C159CB4D…`) nhưng đã ở hash `585C97BD…` trong snapshot G6 và không bị sửa ở G6R. `test_canvas_source_render.py` có đổi import theo F4.
- Không stage, commit hoặc push. Snapshot cuối G6R được ghi tại `.claude/handoff/snapshots/G6R_20261101T175708/`.