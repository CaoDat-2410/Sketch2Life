# Source review cho plan — 2026-10-29

Chỉ đọc source/tài liệu và Git objects; không phải test/runtime evidence mới.

## Chỉ đạo owner

- “lên plan cho tôi đi”.
- Chọn current flow: “Test luồng hiện tại chạy ok trên modal đi r mới làm luồng mới được nha :))) luồng mới hơi nhìu”.
- Đây là planning và hướng ưu tiên, không phải implementation/DB/GPU/publication approval.

## Baseline và code đã đọc

| Source tại dev `529cbef9` | Phát hiện |
| --- | --- |
| `apps/child-ui/src/services/apiClient.ts:27,81` | BE1 `/api/be1/v1`, timeout 12 giây; khác demo |
| `apps/child-ui/app/index.tsx:280,351–365,423,426` | Points normalized, width layout units, gallery/suggestion overlays; Gợi ý báo chưa nối BE2/teacher |
| `apps/child-ui/src/hooks/useReviewStatus.ts:11` | Prototype tự approved bằng timer |
| `backend/src/sketch2life/contracts/schemas/be1_runtime.py:172–203` | Operation/snapshot generic dict, chưa là trusted drawing schema |
| `backend/src/sketch2life/interfaces/http/routers/be1_canvas.py:312–347` | Serialize snapshot client sau authority/revision checks, chưa chứng minh nội dung tương đương accepted ops |
| `backend/src/sketch2life/infrastructure/persistence/core_store.py:103–117` | Sync pagination không tự cung cấp atomic source export |
| `backend/src/sketch2life/infrastructure/persistence/be1_models.py:147` | Consent state CHECK chỉ pending/revoked |
| Cùng file `:117–118`; `interfaces/http/routers/be1_registry.py:276,329–347,414–449` | Profile consent refs NOT NULL, API creation đòi effective record, record_consent tạo pending; list_profiles cũng dùng shared check |
| `backend/src/sketch2life/interfaces/http/routers/be1_sessions.py:748,1309,1588,1752,1817,1948` | Consent checks trên Start/admit/group/progress/help/turn; inventory cụ thể cần T0 disposition |
| `backend/src/sketch2life/interfaces/http/routers/be1_common.py:213–258`, `be1_records.py:51–71` | Shared consent helpers và record contributor gate/callers |
| `backend/src/sketch2life/interfaces/http/be1_runtime.py:143–205` | Device/membership/group/turn checks; positive device path đòi consent effective |
| Cùng file `:163–227` | Write guard đòi active session/group/turn; status-own chưa tồn tại, nên không mặc định tái dùng guard này cho read sau pause/turn |
| `backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py:77–175` | Artifact/hash/contributor ingress có thật, chưa là source/render/admission binding |
| `backend/src/sketch2life/domain/assistance.py:358–381` | Audience gate cần consent booleans; origin flag không đủ |
| `backend/src/sketch2life/application/services/assistance.py:872–911` | Success reconciliation tạo SketchIntent và gọi SketchStage |
| `backend/src/sketch2life/domain/vision_analysis.py:75`, `contracts/schemas/analysis_results.py:114` | Evidence kinds/result hiện chỉ fake/offline |
| `backend/src/sketch2life/infrastructure/vision_analysis/legacy_v2.py:125`, `context_adapter.py:178` | Chặn UrllibJsonTransport trong C1/C2 |
| `backend/src/sketch2life/contracts/schemas/vision_context.py` | C2 endpoint khác `/v2/vision` và chưa có trong Modal recipe |
| `backend/src/sketch2life/interfaces/http/router_composition.py:24–40` | Runtime classroom/demo không tự include fixture apps |
| `backend/src/sketch2life/infrastructure/assistance/fakes.py:314`, `vision_analysis/fakes.py:194` | Assistance/analysis stores hiện in-memory, không có runtime SQL repo để chỉ wire vào |
| `backend/src/sketch2life/infrastructure/ai_jobs/sql/owner_fence_fixture.py:1–18` | OwnerFenceV1/0.1-candidate là disposable fixture, không live app/Alembic revision; cần owner contract adoption riêng |
| `backend/src/sketch2life/application/services/ai_jobs.py:96–103,342,945–980`, `infrastructure/ai_jobs/worker.py:94–98` | Fixture policy mặc định ba attempts; overdue sweep có retry semantics; worker exception để recovery xử lý |
| `backend/src/sketch2life/infrastructure/ai/lightning_vision_v2.py:168–177` | OSError trả retryable=True, không có nghĩa adapter tự retry hoặc pilot được gọi lại |
| `backend/src/sketch2life/domain/assistance.py:544–568`, `application/services/assistance.py:901` | Stage reservation consume khi any_attempt_started; khác invocation-ledger UNKNOWN/HOLD |
| `apps/teacher-ui/src/pages/AiSuggestionReviewPage.tsx:432–466` | Prototype có chỉnh ý nghĩa/duyệt Sketch, không phải read-only pending-analysis panel |

Line refs là locator tại snapshot đã đọc, không phải quyền sửa cả file.

Rev2 xác minh bổ sung từ Claude review rev1. F1/F2 cụ thể hóa invariant đã nêu; status-own chưa có nên lỗi sau turn là rủi ro nếu reuse write guard, không phải failure đã chạy. Tách T7 không mặc nhiên thêm toàn bộ cache/events/persistence BE2. Baseline chỉ có classroom/demo composition; classroom-retirement fence là đề xuất Rev33 chưa được duyệt, khác owner fence.

## Các record cần giữ nguyên

- FEAT-060 ghi current classroom và runtime/adoption gaps. Ghi chú lịch sử chưa có Modal không phủ nhận FEAT-061 đến sau.
- FEAT-063 Rev33 còn AWAITING_APPROVAL; current-flow plan không phê duyệt Parent/Teacher foundation hay tự thực hiện S1/S2/S3.
- Rev33 là input local chưa tracked ở worktree lúc kiểm tra, không nằm trong committed baseline `529cbef9`; SHA-256 `B087E87CF0A27004ECAE54AF8623B3FD81A894E7C709EA83037A23841DF92919`. FEAT-063 CONTEXT cũng có thay đổi ngoài nhiệm vụ này. Các thay đổi đó được giữ nguyên, không stage/restore/approve từ FEAT-064.
- C1/C2/A1 của BE2-02/03 là component/offline scope, không tự cấp runtime adoption.
- FEAT-057 video-seam evidence không chứng minh classroom Vision đã sẵn sàng và không tự là prerequisite cho toàn lát cắt image-only.

## Evidence Modal ở checkout gốc khác

Các file sau dưới FEAT-061/evidence hiện có local ở checkout gốc, chưa có trong baseline dev này. Không giả đã publish hoặc tái dùng receipt/cap cũ cho lượt mới.

| File | SHA-256 của bản đã đọc |
| --- | --- |
| `BACKEND_DEMO_MODAL_SMOKE_20261029.md` | `33624B16EE3E2F0D4587FCA658708D3487ED5655E56C6C76F24D528C08B5F09B` |
| `BE1_BE2_BRIDGE_WORKTREE_REVIEW_20261029.md` | `EAC2BFFCD913B52C69F68FD43236E8BA42AA0A955B4A22CECFDAE21B3AA9A11E` |

Demo cuối `SUCCEEDED`: client 23.938 s, bốn entity, attempt 1/repair true, đúng pinned Qwen3-VL-8B; server HTTP 23.0 s/execution 19.5 s. Owner xác nhận Modal App aborted và backend PID 44944 shutdown. Budget một request đã dùng; không xóa marker/replay. Không chứng minh Child UI/BE1 hiện tại đã hoạt động với AI.

## Giới hạn của nhiệm vụ này

Đã phân tích source, viết hồ sơ DRAFT và tham khảo hai review độc lập. Chưa chạy application tests, DB/migration, renderer, backend/frontend hoặc model. Document/static validator output sau hoàn thiện được ghi riêng, không là runtime pass.
