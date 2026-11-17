# Contract outline — DRAFT, chưa phải API/DTO được chấp thuận

Các tên dưới đây là đề xuất để T0 chốt, không phải source đã có. Không nới contract C1/C2/A1 hoặc enum wire ngầm.

## A. Eligibility và quyền

Tách nguồn dữ liệu khỏi cách observation được tạo: synthetic input chạy Qwen thật vẫn là live-dev model evidence, không phải fake provider.

Đề xuất `SyntheticDevEligibilityEvidenceV1`: issuer/profile/version, isolated dev-run ref, org/session/group/contributors, server-verified origin, allowed purposes/operations, expiry và revocation/currentness version. Proof được tạo/đọc qua owner port từ state server; Child không cấp quyền bằng header/body `synthetic=true`, role hay scope tự khai.

REAL/LEGACY_UNCLASSIFIED bị từ chối trong pilot; không backfill dữ liệu cũ thành synthetic. Không biến proof thành consent giả hoặc `MemberFact.consent_effective=true` / `ContextDecision.consent_effective=true`. Cần scoped eligibility-contract amendment có version xuyên BE1/BE2, phân biệt legal consent và synthetic evidence. Real pending/revoked vẫn deny.

Phải rà đủ profile/enrollment, device, group/checkpoint, artifact, source và BE2 audience/context gates. Inventory khởi đầu ở `ELIGIBILITY_GUARD_INVENTORY_DRAFT.md`; T0 rà `consent_is_effective`, `deny_pending_consent` và so sánh state effective, gắn mỗi site với lifecycle và disposition được owner duyệt. `ManagedProfileModel.consent_id/consent_purpose_ref` NOT NULL, còn API creation đòi effective record: OD-2 phải chốt representation/schema/API synthetic profile mà không bịa consent record/ref/boolean hoặc nới real constraints. Sửa riêng device guard hoặc một origin flag không đủ.

Quyền AI request, cancel/status-own và Teacher analysis-read phải được cấp theo server policy; canvas.read/write không tự bao hàm chúng. Child actor từ grant/key đã xác minh; Teacher từ identity/assignment thật. Auth doubles chỉ trong test, không runtime resolver.

## B. Source/export/render/admission

Đề xuất descriptor có version:

1. `CanvasOperationProfileV1`: append-stroke, finite normalized points, bounded size/count, màu/width có đơn vị, logical viewport/aspect/profile.
2. `CanvasSourceExportV1`: canonical document ref/checksum, accepted-op manifest hash, schema/reducer version, org/session/canvas/group, epoch/revision, through-operation ID và contributor scope do server suy ra.
3. `RenderDerivationReceiptV1`: source ref/checksum → private image ref/hash, dimensions/content type, renderer/profile/version và derivation.
4. `VisionAdmissionBindingV1`: render ref/hash → actual decoder/policy/version/outcome và receipt ref/hash. Chỉ receipt thật được map sang BE2 admission model.

BE1 export nhất quán tại revision r, kiểm tra đủ baseline/operations/epoch; nhiều trang sync không thay atomic export. JSON snapshot client và checksum của nó không chứng minh tương đương accepted operations. Giữ checkpoints cũ, từ chối nguồn không chứng minh được thay vì tự nâng độ tin cậy.

Pilot đề xuất canvas mới strokes-only nền trắng. UI cũng phải hiển thị profile đó, không gallery/suggestion overlay trong mode này; giữ các màn prototype khác. Preview lấy đúng image/export ref/hash sắp gửi. Screenshot/client PNG không làm authoritative source.

ADR cần chốt viewport/aspect, width conversion, caps/joins/dots, deterministic encoding và limits phù hợp admission. Pillow là ứng viên CPU đã có dependency, chưa phải stack cuối.

## C. Gateway và projection

Path/name/version phải được owners duyệt; đề xuất gateway dưới BE1 hiện tại, không mount fixture app:

| Capability | Input client | Output |
| --- | --- | --- |
| Source export | Expected epoch/revision và canvas/group refs có quyền | Immutable export/render preview refs và receipt |
| Request Vision | Export ref, expected revision, stable request/idempotency key | Accepted + request/status ref; không chờ GPU |
| Cancel own | Request ref + command metadata | Durable cancellation/disposition, không refund nếu có thể đã send |
| Child status-own | Request ref đã được cấp quyền | Pending/stale/denied/failed/cancelled/awaiting-Teacher, không candidate/raw output |
| Teacher pending list/read | Server-scoped org/session/group/request | Private unconfirmed analysis/source refs hoặc refusal |

Child timeout hiện là 12 giây: gateway phải trả accepted trước provider completion; worker xử lý và client poll. Poll không submit/retry. Command/port BE2 có version; không map tùy tiện session BE1 thành session demo.

Khi invocation UNKNOWN, projection cho Child/Teacher có quyền là “chưa rõ kết quả, chờ operator”; giữ request ref, không đưa nút thử lại hoặc tự tạo request. Mapping ưu tiên evidence invocation UNKNOWN dù job failed_exhausted, không sửa A1 accounting. Test lost reply/reload, access denied/revoked và không resubmit.

Status-own có read authorization riêng, không dùng nguyên `get_verified_device` vốn đòi active session/group/turn cho write. Cần valid verified grant/identity, request ownership và org/session/group scope, current disclosure/eligibility/revocation checks; grant/membership đơn thuần chưa đủ. T0 chốt read-capability lifetime sau turn và khi pause, không cho đọc bằng grant đã hết hạn/thu hồi. Khi pause/turn kết thúc, trả trạng thái được phép theo disposition hoặc access/status unavailable; Child giữ request ref, không suy ra provider failure, không resubmit. Không nới preconditions của request mới/write để phục vụ poll.

Request pin nguồn tại r. Không khóa việc vẽ suốt inference; head/epoch/restore hoặc eligibility đổi làm request cũ stale/non-applicable trong pilot. Không rebind ảnh mới hoặc tự gọi lại. Private lịch sử không tự trở thành Teacher item hiện hành.

## D. Runtime observation và cap

Adapter/factory runtime riêng sau approval, tái sử dụng Vision V2 `/v2/vision`, IMAGE_ONLY nếu pinned policy cho phép. Giữ C1/C2 HTTP prohibitions; không tạo transport khác để né `isinstance`, không gắn nhãn offline cho HTTP thật.

Owner chốt representation/version mới cho runtime evidence/result, serializer/migration cần thiết và compatibility. Không đổi upstream `VisionUnderstandingResultV2` 2.0, model/profile/prompt. Trường hợp đòi typed-context phải unsupported/dừng; Modal hiện không có `/v1/vision/context`.

Run ID do operator/server tạo trước live, ngoài client API. OD-3=B chọn witness file local single-host; manifest pin approval/plan hash, expiry, source scope, DB identity, witness identity và host, mọi worker cùng host. Witness ngoài volume Docker DB, cloud sync và miền backup/restore DB; token UNUSED có mặt/xác minh, gắn run/DB/host/manifest hash. Sau T12 throwaway đạt và live approval có chấp nhận rủi ro dư, khởi tạo witness live riêng; preflight kiểm tra manifest/ledger/token. Missing/mismatch/xóa/quarantine/không đọc được fail-closed.

Trước outbound HTTP, guard claim atomic witness độc lập DB (UNUSED → CONSUMED), commit durable ledger rồi mới send. Witness là cổng bắt buộc cùng DB ledger và approval manifest; absence không chứng minh UNUSED. Claim/commit lỗi hoặc không chắc thì không send, không tự refund/reacquire. Chỉ worker thắng có thể tiếp tục; worker thua khi xác minh witness consumed nhận NOT_SENT_CAP_CLOSED, missing/unavailable/mismatch là NOT_SENT_CAP_UNAVAILABLE, không suy đoán UNKNOWN cho outbound chưa gửi. Crash chắc chắn trước claim và chứng minh DB/witness UNUSED, zero send thì cap còn mở, nhưng không auto retry.

Pilot inject retry policy `max_attempts=1` và finite reviewed deadlines, không sửa defaults của job khác. Known chỉ khi có bằng chứng chưa send hoặc response hoàn chỉnh xác thực theo contract cho phép kết luận; type của lỗi hoặc HTTP status đơn thuần không đủ. HTTP 5xx, URLError/reset/timeout, response thiếu hoặc nguồn không chắc sau possible-send là UNKNOWN/HOLD. Existing transport/adapter có thể gộp lỗi khác nhau thành typed failure; runtime boundary phải giữ provenance phân loại hoặc mặc định UNKNOWN. Không refund/re-authorize hoặc gọi lại; A1/AiJob state tách khỏi invocation outcome.

A1 stage reservation (`any_attempt_started` → consumed) khác invocation cap: không biến reservation A1 đã tiêu thành held do invocation unknown. Mapping settlement phải được chốt/test; mọi thay đổi domain accounting cần owner scope riêng. Quyền FEAT-061 đã dùng; live scope mới phải ghi trong approval. Cap một call không phải cap USD.

Rev5: OD-3=B, DB identity/ledger cùng database không tự biết restore; T0 chỉ đặc tả Windows exclusive-create/atomic transition/flush file/xử lý flush thư mục và failure/test plan. T7c/T12 sau approval dùng witness/run throwaway test race/crash/durability, xóa/mất và DB restore cùng identity không mở cap. M3 blocked nếu thiếu T12 hoặc approval chưa ghi chấp nhận rủi ro dư host rollback; không yêu cầu chứng minh chống rollback OS. Mỗi restore host hoặc DB hủy live authority, cần manifest + approval mới. Restore host không được báo có thể mở lại lượt, gây thêm call phí synthetic; restore lặp có thể gây nhiều call. Quy trình không chứng minh tự phát hiện restore. Operator đối chiếu Modal logs/ledger sau live là kiểm tra bổ sung, không thay witness.

Invariant `đã gửi ⇒ ledger DB đã commit ⇒ witness đã CONSUMED`. Nếu xác minh DB/host chưa rollback và đọc nhất quán: UNUSED → chưa gửi; CONSUMED + ledger vắng → chưa gửi/cap đóng; ledger có dòng/chưa có kết quả → UNKNOWN. Nếu DB restore/nghi restore thì CONSUMED + ledger vắng có thể đã gửi trước restore → UNKNOWN/cap đóng. Nếu host rollback/nghi rollback thì không suy luận từ UNUSED, authority mất hiệu lực. T6 giữ phase/status/provenance và T8 phân loại known/UNKNOWN/NOT_SENT_CAP_CLOSED/NOT_SENT_CAP_UNAVAILABLE; mất provenance sau possible-send mặc định UNKNOWN. NOT_SENT_* hiện cho Child/Teacher là chưa gửi/chờ operator, không nút thử lại, không hiện như lỗi provider.

T6 định nghĩa InvocationGuardPort; T7c cài đặt witness/ledger; T8 wire tại boundary trước transport HTTP. Missing/denied/error không gửi; transport-count tests cho concurrent/recovery/bypass. T0 pin enforced HTTP wall deadline, attempt deadline lớn hơn elapsed pre-send + HTTP wall deadline + completion margin; kiểm tra Modal/web/backend/sweep deadlines độc lập. `urlopen(timeout=...)` không tự chứng minh tổng wall deadline. Timeout sau possible-send giữ UNKNOWN.

## E. Analysis-only completion

A1 success hiện tạo SketchIntent và gọi SketchStage. Runtime pilot cần continuation/disposition được duyệt để lưu analysis/Teacher pending và settle đúng reservation, với zero SketchIntent/event/outbox/SketchStage/generation dispatch, kể cả reconcile replay/restart.

Không dùng RecordingSketchStage hay no-op fake để che side effect, không manufacture DATA-23. Hành vi A1 mode cũ giữ nguyên và regression test.

Owner fence/UoW bảo vệ acceptance commit trước source/eligibility race; pre/post read đơn thuần không đủ. Không giữ DB transaction qua network inference. BE2 không đọc/sửa bảng BE1 trực tiếp, mọi write qua owner ports.

T7a freeze minimal durable-state inventory/schema/repositories/migrations cho selected path; Assistance/Analysis stores hiện chỉ in-memory. T7b freeze owner-signed `OwnerFenceV1` hoặc version thay thế, port ownership và linearization/UoW; fixture `0.1-candidate` chưa là runtime contract. T7c freeze run ledger. Mỗi phần có manifest/review riêng; không mặc nhiên triển khai toàn bộ cache/event/table hoặc correction/Parent workflows.

T0 map từng method UoW tới call site và disposition: method cần mutation bền/atomic hoặc read-only semantics đúng contract; method không được hỗ trợ fail-closed nếu bị gọi, không silent no-op. Test method inventory và restart/failure, không giả định số method hoặc full adoption.

Teacher chỉ đọc field được duyệt, meaning unconfirmed và freshness; Child không đọc raw provider/candidate nội bộ. Approve/correct/Sketch/Child delivery nằm ngoài scope.

## F. Trước code

Chốt owner, schema/version, eligibility/purpose/profile, required consent representation và guard inventory, source/fence linearization, run/DB identity và deadline/retry/accounting semantics, read lifetime/status/retention và exact manifest. Các đề xuất này không cho phép đổi consent hoặc gọi GPU ngay.
