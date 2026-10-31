# M1 — trần canvas và render budget (GOAL A1)

## Phạm vi và lớp

Theo V4 D1 được owner duyệt: tối đa 500 nét và 60.000 điểm; render semaphore1/deadline6s. Giữ nguyên CanvasOperationProfileV1 và service/core_store.

| Lớp | Việc và cổng |
|---|---|
| L1 | Hợp đồng profile không đổi; xác nhận hash và unit profile hiện có. |
| L2 | Không sửa application/domain; kiểm service/CAS hiện có. |
| L3 | Không migration; test PG fixture riêng và SUM JSONB thật. |
| L4 | Limits/error constants; semaphore/deadline trong renderer; unit trước/sau. |
| L5 | Router precheck receipt → current_revision → require_expected_revision → limits → service CAS; export/handoff mapping HTTP. |
| L6 | DEFERRED-BY-OWNER. |
| L7 | PostgreSQL boundary/replay, regression baseline590pass4skip và API4pass. |

## Chi tiết chốt

- current_revision−1 là cận trên số nét; restore làm revision tăng mà không thêm operation nên giới hạn có thể chặt hơn; owner chấp nhận. Không dùng đếm thao tác client.
- Tổng điểm đọc từ cột JSONB `core_canvas_operations.operation_payload`, đường `points`; SUM(CASE WHEN jsonb_typeof(payload->'points')='array' THEN jsonb_array_length(payload->'points') ELSE 0 END). Scope organization/session/canvas và epoch hiện hành; số nét upper-bound revision bao trùm cả lịch sử restore.
- Không đòi cùng transaction với core_store: correctness dựa CAS expected==current ở router/service/UPDATE; replay receipt hợp lệ bỏ qua cap nhưng vẫn qua các guard và payload validation hiện có. Receipt mismatch giữ lỗi idempotency hiện có, stale revision giữ lỗi hiện có.
- Append quá trần409 CANVAS_CAPACITY_REACHED; export/render nguồn quá trần409 CANVAS_SOURCE_TOO_LARGE trước vẽ. Lưới render đếm operation/points cả canvas cũ, không đổi DTO profile.
- BoundedSemaphore(1) cấp module bao quanh render; budget monotonic6s bắt đầu từ create_canvas_render_handoff, truyền deadline vào renderer gồm thời gian chờ. Chờ hết budget: CANVAS_RENDER_BUSY; deadline tính toán/vẽ/admission/persist: CANVAS_RENDER_DEADLINE_EXCEEDED. Kiểm giữa các nét và các pha. Không retry hoặc nới consent.

## Allowlist chính xác

- `backend/src/sketch2life/infrastructure/canvas_render/limits.py` (mới).
- `backend/src/sketch2life/infrastructure/canvas_render/renderer.py`.
- `backend/src/sketch2life/interfaces/http/routers/be1_canvas.py`.
- `backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py`.
- `backend/tests/unit/test_canvas_render_limits_ga1.py` (mới).
- `backend/tests/integration/test_canvas_capacity_ga1_postgres.py` (mới).
- Plan này, `evidence/M1_CANVAS_CAPACITY_RENDER_REPORT_GA1_20261101.md`, append approval/ledger FEAT064, snapshot mới.

## Test trước và acceptance

- Unit mới trước implementation: constants500/60000/reconnect500; quátrần500/60000; semaphore concurrency tuần tự; busy; clockdeadline trước/giữa/sau render; không vẽ khi capfail; budgethandoff tính từđầu. Ghi số đỏ thật.
- PostgreSQL: 500 nét và60kpoint đúngboundary, nét tiếp theo409; stale trảstale trướccap; replay nét đã nhận khiđầy khôngcommitmới; exportcanvascũquátrầnfailclosed. Dữliệufixture synthetic có scope, dọnđúnghàng.
- Hồi quy renderer/export/profile/pilot/5CI/analysis/assistance; ruff/mypy chỉ lỗi mới; architecture/harness/security/diffcheck. Không dùng số lịch sử thay lượt chạy thật.

## Loại trừ và rủi ro

Không core_store/application core/domain profile, không migration, không checkpoint M3/routePNG/UI, không Modal/GPU/provider/mạngngoài/dữliệuthật; không Git mutation. Semaphore chỉ một process; deadline hợp tác giữa strokes/pha, mỗi C-call Pillow không preempt được; giới hạn60000 điểm giảm tải, kiểmclock sauC-call ngăn trả kết quả quábudget. Chưa là cam kết SLA production.
