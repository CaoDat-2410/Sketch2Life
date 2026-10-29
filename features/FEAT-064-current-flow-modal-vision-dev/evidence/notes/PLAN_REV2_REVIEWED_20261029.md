# FEAT-064 — Plan kiểm chứng luồng hiện tại với Modal Vision ở dev

- Status: DRAFT
- Plan revision: 2
- Implementation status: NOT_STARTED
- Date: 2026-10-29, Asia/Saigon.
- Baseline: dev `529cbef9c71c0b225dca0d6a88f50f099e05176e`, worktree `feature/modal-vision-dev`.
- Authority: chủ task yêu cầu lập plan và chọn test luồng hiện tại trước. Chưa có implementation approval.

## 1. Mục tiêu và định nghĩa hoàn tất

Một thiết bị Child được xác thực trong môi trường synthetic dev vẽ trên canvas của luồng hiện tại, gửi yêu cầu rõ ràng, và Teacher đúng quyền thấy một kết quả nhận diện Qwen gắn đúng nguồn ở trạng thái **chưa xác nhận/chờ duyệt**. Trạng thái request và review khôi phục được khi tải lại giao diện; callback thành công giả bằng timer không được dùng trong luồng này.

Chuỗi cần kiểm chứng:

`Child UI → operation được BE1 chấp nhận → source export tại epoch/revision → ảnh + admission → BE2 request/job/analysis → Qwen trên Modal → Teacher pending-analysis`.

Đây là lát cắt Vision đầu tiên của luồng hiện tại, không phải kiểm thử hoàn tất chín stage hay toàn bộ app. Kết quả nhận diện chưa được Teacher xác nhận không được coi là Sketch, ý nghĩa đã duyệt hoặc kết quả đã phát cho Child.

## 2. Phạm vi và cách giữ nhỏ

Trong scope đề xuất:

- Dữ liệu giả lập, môi trường local/dev cô lập; một session, một canvas/group, một thiết bị Child và một Teacher cho ca live đầu tiên.
- Tái sử dụng BE1 ingress/artifact, BE2-01/02/03 services/ports và Qwen Vision V2 hiện có.
- Chỉ các operation/render profile được chốt; đề xuất canvas mới, append-only, strokes-only trên nền trắng. Trường hợp ngoài profile dừng rõ ràng.
- Eligibility, request/attempt/result/reservation và Teacher-pending state thật cho phạm vi được chọn. Không gọi fixture router như API sản phẩm.
- Kiểm chứng CPU/isolated DB trước; cuối cùng mới một ca synthetic với provider thật nếu được duyệt.

Runtime đích là `sketch2life.classroom_main:app` với composition current-flow được duyệt và worker tương ứng, không phải demo backend đã smoke. Child UI dùng `EXPO_PUBLIC_BE1_BASE_URL` trỏ backend này; URL/token Modal chỉ ở backend. Baseline chỉ có tách composition classroom/demo, chưa có classroom-retirement fence của Rev33. Pilot đề xuất dev opt-in mặc định off trong classroom profile, không mount demo/combined. Owner fence BE2 ở acceptance commit là hợp đồng khác, phải được chốt riêng; không lấy S1 Rev33 làm dependency ngầm.

Ngoài scope:

- Parent/Teacher mới, StoryRun và triển khai FEAT-063 Rev33; không đổi danh tính/mô hình sở hữu toàn hệ thống.
- ASR, SAM, video, ranking/recommendation, Pixi, generation, Teacher approve/correct/reject, Child result delivery và tự tiến stage.
- Dữ liệu trẻ em thật, production, đổi Runpod policy, benchmark chất lượng, scale 40 trẻ hoặc throughput/SLA.
- Merge/push/deploy, tải lại model/Volume/Secret; mọi thao tác như vậy cần yêu cầu riêng phù hợp.

## 3. Những gì đã có và những điểm chặn đã xác minh

| Đã có | Chưa thể suy ra là chạy được trong app hiện tại |
| --- | --- |
| Demo backend gọi Qwen trên Modal thành công 23.938 s | Demo dùng session in-memory khác BE1; không chứng minh Child UI → BE1 → AI |
| BE1 operation/checkpoint/artifact APIs, revision/idempotency và hash | Operation là dict generic; checkpoint lưu JSON client mà chưa đối chiếu nội dung với operation |
| BE2 analysis, assistance lifecycle, job adapters và kiểm tra lineage | Composition được thử vẫn dùng fake source/owner/fence; chưa phải runtime composition |
| AiJob có SQL repository | Assistance/analysis hiện chỉ có in-memory stores; owner-fence SQL là fixture `OwnerFenceV1/0.1-candidate`, chưa có runtime adoption hoặc Alembic revision |
| C1/C2 bridges và Vision V2 adapter | C1/C2 chủ động chặn HTTP thật; C2 đòi `/v1/vision/context`, Modal hiện không có |
| Teacher/Child UI và BE1 grant/assignment | Review timer của prototype không phải review state thật |

Các rủi ro phải giải quyết trước positive-path test:

1. `ConsentRecordModel` chỉ cho `pending/revoked`, nhưng profile creation, session transition/admit/group/turn và shared device/record guards đòi `effective`. `ManagedProfileModel.consent_id` và `consent_purpose_ref` còn NOT NULL; API profile creation đòi consent record effective, không chỉ một chuỗi khác null. T0 phải lập inventory từng call site, kể cả progress/help/checkpoint/artifact và BE2 gates; T1 ghi rõ nhận proof synthetic, giữ nguyên hay ngoài lifecycle. OD-2 phải chốt representation synthetic profile không bịa consent row/boolean hoặc blanket-relax real constraints. Xem `ELIGIBILITY_GUARD_INVENTORY_DRAFT.md`.
2. Điểm nét vẽ được chuẩn hóa nhưng width đang theo layout; artwork/suggestion overlays không nằm trong operation. Screenshot parity chưa được chứng minh.
3. Sync operation phân trang không tự tạo một snapshot nhất quán tại revision r. Phải có export phía owner với epoch/revision và completeness đã pin.
4. Evidence kinds/result contracts BE2 hiện chỉ mô tả fake/offline; live-dev cần provenance/version trung thực.
5. FEAT-063 Rev33 đang chờ duyệt, chạm classroom fence, synthetic provenance và job ownership. Phải chốt quyền sửa file/migration giao nhau, không mặc nhiên thực hiện Rev33.
6. BE2-03 hiện tạo SketchIntent và gọi SketchStage khi reconcile thành công. Điểm dừng analysis-only cần một continuation contract riêng được duyệt; không nối fake/no-op SketchStage để giả hoàn tất.
7. Durable assistance/analysis adapters và owner fence chưa có sẵn. T7a/b/c là nhánh rủi ro lớn: schema/repository tối thiểu cho selected path, owner-fence/UoW và invocation ledger; không ước lượng chúng như chỉ nối port. Inventory state thực sự cần dùng phải được owner freeze, không tự nhận scope triển khai mọi cache/event/table của BE2.
8. Job mặc định dùng fixture retry policy ba attempts; adapter có thể trả `OSError` là retryable và timeout sweep cũng có retry semantics. Invariant không retry trong rev1 cần được cụ thể thành policy pilot `max_attempts=1` và possible-send outcome mapping ở worker/ledger, không sửa mặc định của các job khác.

Nguồn chi tiết và dòng code: `../evidence/notes/SOURCE_REVIEW_20261029.md`. Ba worktree BE2 đã đọc đều là tổ tiên của baseline dev; không có bridge mới hơn để chỉ cần merge.

## 4. Mốc triển khai

### M0 — Chốt hợp đồng và phạm vi owner trước code

Chốt các quyết định ở mục 8, ADR/hợp đồng nguồn/eligibility/capability, inventory guard, minimal durable-state inventory, `OwnerFenceV1` hoặc phiên bản thay thế được owners ký nhận, manifest file chính xác và migration ownership. Chốt run manifest phía server, DB identity và retry/outcome policy trước scope live. Approval phải chỉ rõ task/mốc được phép làm, quyền test DB và quyền provider nếu có. Không coi bảng đường dẫn dự kiến là execution manifest đã duyệt.

### M1 — Đầu vào BE1 và ảnh được chứng minh, chưa có provider

Chứng minh Child synthetic hợp lệ có thể join/được admit/vẽ qua BE1 thật; xác thực stroke schema; export một nguồn nhất quán từ accepted operations; render và chạy admission thật. Giữ nguyên operation/checkpoint gốc. Dữ liệu cũ, history restore hoặc lớp ảnh chưa hỗ trợ bị từ chối cho AI, không tự chuyển thành nguồn tin cậy.

### M2 — BE2 và giao diện thật, kiểm chứng CPU trước

Nối real owner ports, state bền và worker vào runtime gateway; dùng transport kiểm thử chỉ trong bộ test với provenance kiểm thử đúng nghĩa. Child gửi request/ref, Teacher đọc projection scoped. Kiểm thử end-to-end bằng provider được inject không có nghĩa đã gọi Qwen thật. Các fixture resolver, fake quyền/consent và timer approved không được lọt vào runtime composition.

### M3 — Một lượt Qwen thật rồi dừng

Chỉ sau M1/M2 đạt và phạm vi live được duyệt: owner khởi động Modal, kiểm tra cấu hình đã pin, thực hiện đúng một request từ luồng canvas hiện tại và xác nhận Teacher-pending. Thu bằng chứng, owner dừng Modal và backend. Nếu timeout/unknown/fail thì dừng và chẩn đoán; không tự gọi lại.

## 5. Work breakdown và phụ thuộc

Owner dưới đây là vai trò đề xuất; chủ task chốt người thực hiện. Không mặc định giao backend/E2E cho Person 4 hay toàn bộ Android cho Person 3.

| ID | Task / đầu ra | Depends on | Parallel with | Acceptance check | Effort | Risk / owner |
| --- | --- | --- | --- | --- | --- | --- |
| T0 | Chốt ADR, contract/profile/policy, guard/state inventories, owner-fence version, run manifest, exact paths và migration order | — | — | OD-1–OD-4, từng consent call site/required profile fields, DB/run identity và owner scope có disposition; approval đúng revision/task | M | Chồng FEAT-063; chủ task + owners |
| T1 | Synthetic eligibility evidence riêng; sửa đủ selected schema/guard BE1 và gate BE2 | T0 | T3, T6 | Inventory được tick từng site; synthetic profile tạo hợp lệ không giả consent; lifecycle join/admit/Start/group/turn/export đạt; REAL/unclassified/pending vẫn deny | L | Nhiều route/representation; BE1 + BE2 owners |
| T2 | Actor/authority/context và AI-capability adapters thật; tách status-read khỏi write guard | T1 | T4/T5, T6/T7a nếu khác file | Server xác minh grant/identity/scope/eligibility; write cần turn, status-own không cần active turn nhưng vẫn chặn revoke/foreign scope | M | Revocation/disclosure; BE1 + integration |
| T3 | Stroke DTO/profile, geometry/width và canvas dev trắng tương ứng | T0 | T1, T6/T7a | Strokes-only, cùng logical viewport/aspect/width; từ chối ngoài profile; dùng components/style có sẵn, visual gate AC20 | M | Render fidelity; BE1 + FE |
| T4 | Export authoritative source nhất quán tại epoch/revision | T3 | T2, T6/T7a | Canonical document + op manifest/digest đầy đủ; JSON client, mixed epoch và history không chứng minh được bị từ chối | M–L | Snapshot race; BE1 owner |
| T5 | CPU render + private artifact + admission receipt + source handoff | T4 | T6/T7a | Ảnh gắn đúng source hash/renderer version; decode thật; BE2 nhận đúng render/admission qua port | M | Overlay/receipt mismatch; BE1 + BE2 |
| T6 | Runtime observation/capability và provenance version trung thực | T0 | T1–T5, T7a nếu khác file | Giữ guard C1/C2; adapter mới dùng Vision V2 hiện có; context không hỗ trợ bị từ chối | M | Contract compatibility; BE2 owner |
| T7a | Minimal durable assistance/analysis repositories và migration | T0 | T3–T6 nếu khác file | Selected request/result/reservation/pending/idempotency/currentness state có schema, rollback/retention và restart tests; state khác có disposition rõ | L | Chưa có runtime stores; BE2 + persistence owner |
| T7b | Owner-fence contract/adapter và acceptance UoW | T0,T7a | T7c chỉ khi khác file/transaction boundary | Version được owners duyệt; acceptance atomic với source/eligibility updates; không dùng fixture fence hoặc giữ lock qua GPU | L | Cross-owner transaction; core + BE1/BE2 owners |
| T7c | Server-issued run manifest và durable invocation ledger | T0,T7a | T7b nếu đã freeze integration contract | DB/run identity đúng, cap chung mọi session/canvas/ID; commit trước send; unknown không mở cap; reset DB hủy quyền live | M–L | Cost/concurrency; BE2 + operator |
| T8 | Worker → observe → atomic acceptance → analysis-only reconciliation | T2,T5,T6,T7a,T7b,T7c | Chỉ chuẩn bị client mock riêng sau contract freeze | Pilot max_attempts=1; possible-send giữ invocation UNKNOWN/HOLD, không attempt mới; analysis/pending đúng và zero Sketch side effects | L | Retry/accounting/TOCTOU; BE2 + integration |
| T9 | Runtime gateway request/cancel + child status / Teacher read | T2,T7a,T7b,T7c,T8 | T10/T11 theo contract | Accepted/ref trả sớm; status-own qua guard read riêng khi pause/turn đóng, revoke vẫn deny; worker/freshness đúng | M | Timeout/disclosure; BE1 + BE2 |
| T10 | Child UI flush/ack → preview nguồn đã export → request → trạng thái thật | T3,T9 | T11 | Preview đúng hash/profile ở r; giữ key/ref khi mất reply/poll denied; không auto resubmit/timer approved; AC20 | M | Pending ops/false success; FE owner |
| T11 | Teacher pending-analysis panel scoped, read-only riêng | T9 | T10 | Refresh còn item đúng nguồn/meaning unconfirmed; không biến Sketch-approval prototype thành analysis approval; AC20 | M | Disclosure/nhầm chức năng; FE owner |
| T12 | CPU + isolated persistence/runtime tests và regressions | T1–T11 | Review docs | Các invariant mục 7 đạt, không provider thật; không hợp thức hóa fake composition | M–L | Môi trường/migration; integration + owners |
| T13 | Fresh bounded live smoke từ nét vẽ thật của UI, nhưng synthetic | T12 + live scope được duyệt | — | Operator run manifest/DB identity còn hiệu lực, ledger chưa consumed; một call, đúng nguồn/provenance, Teacher pending; shutdown receipts | M | Cost/unknown outcome; owner vận hành + test runner |
| T14 | Rà evidence, cập nhật trạng thái và bàn giao | T13 hoặc ghi rõ gate chưa chạy | — | Không nâng component/production/quality gate ngoài scope; ghi done/not-run thật | S | Overclaim; reviewer |

S: tài liệu hoặc thay đổi hẹp trong một vòng review. M: một hợp đồng/component với test liên quan. L: nhiều boundary/concurrency; tách tiếp thành manifest owner-sized trước khi code. Đây là effort tương đối, không phải cam kết ngày công; phụ thuộc hợp đồng và môi trường chưa chốt.

Critical path: hội tụ `T0 → T1/T3 → T2/T4 → T5`, `T0 → T6` và `T0 → T7a → T7b/T7c` trước `T8 → T9 → T10+T11 → T12 → T13 → T14`. Nhánh persistence/fence T7a/b/c có thể là nhánh dài nhất; từng phần có manifest/review/approval riêng, không coi tổng T7 là một task L nhỏ.

Không làm song song các task sửa cùng `be1_models.py`, shared runtime guards, `app.py`/router composition, result enums/contracts hoặc cùng `app/index.tsx`. T3 phải xong phần geometry trong Child UI trước T10. Mỗi nhóm dùng manifest riêng; migration order do owner chốt, không tự merge Alembic heads.

## 6. Hợp đồng và runtime cần chốt

Chi tiết đề xuất ở `CONTRACT_OUTLINE_DRAFT.md`, `OWNER_PATH_MANIFEST_DRAFT.md` và `ELIGIBILITY_GUARD_INVENTORY_DRAFT.md` cùng thư mục; chưa tạo DTO/API/source thật.

- Nguồn: org/session/canvas/group, epoch/revision, through-operation ID, accepted-op manifest hash, canonical checksum, schema/reducer version và contributor scope do server suy ra.
- Render/admission: bind source ref/hash → render ref/hash/dimensions/version → actual validation outcome/policy/receipt hash. Admission của FEAT-018 không tự đồng nghĩa receipt BE2; cần mapping có nguồn gốc đúng, không bịa PASS.
- Request: explicit user action + stable idempotency + server-resolved source/actor; không dùng session demo để thay session BE1.
- HTTP/worker: Child API hiện timeout 12 giây, ngắn hơn lượt model đã đo. Gateway trả accepted + request/status ref mà không đợi provider; worker xử lý và client poll request đã có. Poll/lost reply không tự tạo job mới. Không chỉ tăng timeout để che thiếu lifecycle.
- Status-own có authorization read riêng: verified grant/identity + request ownership/scope + current disclosure/eligibility, không tái dùng nguyên write guard đòi active session/group/turn. Pause hoặc hết turn không tự là provider failure; theo disposition được duyệt, Child đọc trạng thái được phép hoặc thấy status/access unavailable và giữ request ref. Revoke/foreign scope vẫn deny; không tự submit lại khi 403/network failure.
- Eligibility: proof synthetic là một loại bằng chứng riêng, không biến thành `consent_effective=true` hoặc consent pháp lý giả trong `MemberFact`/`ContextDecision`. Chốt amendment có version cho các gate BE1 và BE2 liên quan; origin flag đơn thuần không đủ. Quyền canvas.read/write không tự cấp quyền yêu cầu/hủy/đọc AI.
- Freshness: không khóa việc vẽ suốt inference. Request giữ nguồn bất biến tại r; operation mới/restore/epoch hoặc owner eligibility đổi làm request cũ stale/non-applicable trong pilot, không tự rebind hoặc tự gửi lại. Read projection luôn kiểm tra currentness/revocation.
- Acceptance: revalidate nguồn/quyền/context dưới owner fence/UoW được duyệt ở điểm commit. Chỉ đọc lại trước/sau GPU không đủ chứng minh atomicity; không giữ transaction DB suốt thời gian gọi GPU.
- Persistence/fence: T0 freeze state inventory tối thiểu và owner-signed `OwnerFenceV1` hoặc version thay thế. In-memory assistance/analysis stores và SQL owner-fence fixture không phải runtime adapters. T7a/b/c tách schema/repository, cross-owner UoW và invocation ledger; không mở rộng thành toàn bộ BE2 storage.
- Retry/accounting: pilot pin `max_attempts=1` và finite reviewed deadlines, không kế thừa fixture default 3; duplicate dispatch/timeout sweep không tạo provider attempt mới. Possible-send `OSError`, crash hoặc timeout chưa có definitive result giữ invocation UNKNOWN/HOLD kể cả job đã terminal; typed failure xác định là known failure với cap đã tiêu, không gắn unknown cho mọi provider_invoked. Không refund/re-authorize invocation. A1 stage reservation (`any_attempt_started` → consumed) là trục accounting khác, phải map rõ, không đổi thành held chỉ vì invocation unknown hoặc sửa policy job khác; không tự thêm global AiJob state.
- Run: operator/server tạo run ID trước live ngoài client API; manifest pin owner approval/plan hash, expiry, database identity/generation, baseline/config/policy, cap và run-wide scope xuyên session/canvas/ID. Ledger monotonic/audited (append-only event là một lựa chọn); không delete/reset để dùng lại. Mất/reset/rebuild hoặc restore làm lùi ledger vô hiệu quyền live, cần manifest và approval mới; migration bảo toàn ledger/identity theo manifest không tự reset cap hoặc cấp lượt, mismatch thì dừng.
- Continuation: runtime disposition analysis-only được duyệt phải lưu Teacher pending và settle reservation đúng, với **zero** SketchIntent/event/outbox/SketchStage/generation dispatch, kể cả reconcile replay/restart. Giữ hành vi A1 cũ ở mode cũ; không cắm fake/no-op để che side effect.
- Provider: đề xuất `image_only`, `/v2/vision`, profile `QWEN3_VL_8B_INSTRUCT_BF16_V1`, revision `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`. Không tạo provider Modal mới; không thêm C2 endpoint hoặc đổi prompt/model trong scope này.
- Evidence/version: live-dev không được mang nhãn `synthetic_fake` hay `offline_legacy_bridge`. Giữ consumer/fixture contract cũ; chốt version/projection mới được owner duyệt trước code.
- Result: validated analysis được lưu riêng tư để Teacher đọc có quyền; không log raw provider body, token hoặc đưa predicted text vào evidence publish. Child chỉ nhận trạng thái được cho phép.

## 7. Acceptance criteria và kiểm chứng

| AC | Tiêu chí bắt buộc |
| --- | --- |
| AC01 | Chỉ synthetic server-classified trong môi trường cô lập; không nới consent/authority cho real hoặc unclassified data |
| AC02 | Pixel nguồn được dựng từ accepted operations đã validate và pin nhất quán; không dùng snapshot/PNG do client khai để bỏ qua chứng minh |
| AC03 | Revision/epoch, source/render/admission hashes và policy/renderer versions khớp xuyên suốt; originals được giữ nguyên |
| AC04 | Thiếu/reorder/duplicate/mixed epoch/unsupported operation hoặc geometry quá giới hạn bị xử lý đúng; không tạo model call |
| AC05 | Grant/membership/assignment/age/purpose/eligibility sai hoặc bị thu hồi thì từ chối đúng gate; create/write cần turn hợp lệ; status-own dùng quyền read riêng, không yêu cầu turn active |
| AC06 | Lặp command, lost reply và duplicate worker delivery không tạo provider call thứ hai; unknown outcome không tự refund/retry |
| AC07 | Request/attempt/result/reservation/pending pointer được lưu đúng; restart/refresh không biến pending thành approved hoặc tự phát lại call |
| AC08 | Source đổi hoặc revoke trong lúc provider chạy không tạo kết quả hiện hành được chấp nhận; kiểm chứng cửa sổ race ở acceptance commit |
| AC09 | Child bấm rõ ràng sau flush/ack, giữ tranh và hiển thị pending/denied/stale/failure thật; không timer approved trong runtime path |
| AC10 | Teacher đúng quyền thấy item nguồn-bound, meaning unconfirmed; Child/foreign Teacher không đọc raw/candidate riêng tư |
| AC11 | Profile/model/revision/source/schema/config/provenance sai không thành công; repair true hợp lệ không bị coi là retry |
| AC12 | Trước live: CPU/contract/persistence regressions và review đạt; chỉ fixture transport trong test không được ghi là live pass |
| AC13 | Live khi được duyệt: đúng một call từ canvas UI của lượt mới; metadata và shutdown receipt đầy đủ; không replay probe FEAT-061 |
| AC14 | API/guard/fixture cũ không bị đổi ngầm; original FEAT-061 approvals và FEAT-063 Rev33 giữ nguyên; không đổi production policy |
| AC15 | Synthetic dev canvas đang hiển thị nền trắng/nét được hỗ trợ; preview server/export cùng profile/geometry/hash, không âm thầm bỏ gallery/suggestion đang thấy |
| AC16 | Analysis-only success/replay/restart không tạo Sketch intent/event/outbox/call hoặc DATA-23; Teacher chỉ có unconfirmed analysis |
| AC17 | Proof synthetic riêng xuyên BE1/BE2; inventory profile required fields + registry/session/shared/records/artifact/domain gates có disposition và tests; không forge effective consent hoặc relax real constraints |
| AC18 | Backend ledger/run manifest đúng DB identity, commit trước send, cap chung mọi session/canvas/ID/restart; pilot max_attempts=1; OSError sau possible-send/timeout/sweep/crash không attempt mới, invocation UNKNOWN/HOLD không mở lại; A1 accounting phân biệt; mất/reset ledger hủy live authority |
| AC19 | Accepted/ref trước provider completion; poll không cần turn active, pause/turn closure có disposition rõ; revoked/foreign vẫn deny; khi poll unavailable/403 giữ ref, không giả provider failure/resubmit |
| AC20 | T3/T10/T11 dùng components/style hiện có, không thêm asset mới trong đề xuất hiện tại; mọi asset/visual mới phát sinh phải theo AGENTS mục 6: generated/provenance → visual approval → approved/applied; synthetic scoped screenshots không tự là approval |

Negative tests cần có: forged checkpoint JSON; client PNG giả; swap render/receipt; revision đổi giữa export và render; thiếu op ở ranh giới page; stale/revoke trước claim và giữa provider/acceptance; duplicate concurrent submission/delivery; storage/transaction failure; possible-send OSError/timeout sweep/restart không attempt mới; DB identity mismatch/reset/restore ledger không mở quyền; pause/turn closure khi poll và grant revoke; foreign scope; unsupported typed context; flag off; real/unclassified data; gallery/restore/operation ngoài profile.

Kiểm chứng theo pha:

Ca current-flow dương tính phải đi đúng lifecycle BE1: Teacher có assignment tạo Lobby; Child synthetic join trước Start và được admit; Teacher Start rồi cấp turn; Child vẽ/nhận ack và mới export/request. Không join mới sau Start, seed grant/consent để né API hoặc đổi stage tùy ý. Test setup giữ đúng quy tắc hiện có, không tự đưa quyền quản trị vào Child.

1. T0: review contract/ADR/manifest và approval của đúng owner, chưa chạy dịch vụ.
2. T1–T12 sau approval: unit/contract của modules thay đổi, focused frontend checks, integration trên DB local riêng với dữ liệu giả nếu được duyệt; chạy regression C1/C2/A1 và route isolation liên quan. Không dùng DB sản phẩm hoặc credential trong Git.
3. T13 chỉ khi approval bao gồm live: xác minh operator/server-issued run manifest, DB identity/generation, config/policy và ledger chưa consumed trước khi owner khởi động bằng recipe đã kiểm chứng. Backend atomically reserve/consume một invocation của approved run trước outbound HTTP; helper chỉ bổ sung. Cap xuyên session/canvas/request/attempt/worker/restart; pilot `max_attempts=1`, không provider/job retry kể cả timeout sweep. Possible-send OSError/crash/timeout giữ invocation UNKNOWN/HOLD, không tự refund/re-authorize; settle A1 reservation theo contract riêng. DB reset/rebuild/mất hoặc rollback ledger hủy quyền live; mismatch thì dừng, cần approval mới. Tối đa một inference-bearing call; FEAT-061 không cấp thêm lượt. Đây là cap số lần gọi, không phải cap USD; timeout/stop procedure ghi trong manifest.
4. Static repository checks phù hợp; trước mỗi commit/push bắt buộc security validator cùng harness/architecture/diff checks theo repo. Không tự publish từ việc duyệt một lượt test.

## 8. Quyết định còn mở và mặc định đề xuất

| ID | Cần chốt trước task phụ thuộc | Đề xuất để chủ task duyệt |
| --- | --- | --- |
| OD-1 | Nguồn/render profile và lựa chọn renderer | Fresh synthetic append-only, strokes-only nền trắng; schema có geometry/width chuẩn; CPU rasterizer hẹp, Pillow là ứng viên; từ chối overlay/restore ngoài profile |
| OD-2 | Synthetic eligibility proof, required consent fields và toàn bộ selected lifecycle gates | Proof/tag/version riêng; quyết định representation synthetic profile khi consent refs NOT NULL và API đòi effective; tick inventory, không bịa legal consent/MemberFact; phối hợp subset FEAT-063, không Parent foundation |
| OD-3 | Vision capability, policy/profile/level/purpose và operator live-run authority | IMAGE_ONLY `/v2/vision` nếu policy cho phép; typed-context unsupported; một call, max_attempts=1; server-issued run/DB identity và reset-invalidates-authority, không tự re-authorize |
| OD-4 | Minimal persistence T7a/b/c, owner-fence version/UoW, continuation và allocation | Freeze selected-state inventory và owner-signed fence contract; một integration owner cho shared models/app/settings/migrations; invocation unknown tách A1 accounting; zero Sketch, không full BE2 adoption |

Luồng hiện tại đã được chọn; không hỏi lại lựa chọn đó. Nếu thiếu quyết định/approval ở trên, tiếp tục làm rõ hồ sơ nhưng không chạy implementation phụ thuộc. Khi quyền đúng scope đã được cấp thì không hỏi lại vô cớ. Approval phải ghi task/mốc được duyệt và quyền DB/live nếu có; phê duyệt planning không đồng nghĩa phê duyệt các thao tác đó.

## 9. Rủi ro, giới hạn và rollback

- Tưởng checksum là nguồn tin cậy: tách byte integrity khỏi semantic derivation; server export từ history đã validate, giữ legacy nguyên trạng.
- Tưởng ảnh gửi giống canvas: pin geometry/profile, preview nguồn render; không âm thầm bỏ gallery/suggestion layer.
- Bất nhất consent: giải quyết hợp đồng synthetic riêng; không flip pending/effective, không nhận classification từ Child.
- TOCTOU/duplicate: owner fence/UoW + durable uniqueness/reservation, test race thật; unknown outcome giữ hold.
- Trùng FEAT-063: chỉ chọn subset phục vụ current flow, một owner cho shared files/migrations; không implement Rev33 ngầm.
- Scope phình: dừng tại Teacher pending-analysis, không kéo video/Parent/Sketch/approval vào. Video-specific gates của FEAT-057 không tự là prerequisite cho lát cắt này.
- Sizing: runtime persistence/fence là công việc mới qua nhiều owner, không chỉ đổi endpoint. M1/M2 cần review theo từng T7a/b/c; vướng owner contract thì dừng phần phụ thuộc, không thay bằng in-memory/no-op để rút ngắn.
- Model quality chưa đạt production: live pass chỉ chứng minh kết nối/contract cho synthetic case, không nâng FEAT-003 quality gate.

Rollback đề xuất: feature flag dev mặc định off; tắt wiring/worker mới, giữ drawing/request/audit data và các guard cũ. Không xóa bảng/artefact/snapshot để rollback. Downgrade có dữ liệu phải dừng để owner xử lý; không tự migrate hoặc restore DB.

## 10. Evidence và bàn giao

Lưu theo task trong feature này: baseline/source hashes, owner decisions/ADR, frozen manifests, contract tests, source/render/admission receipts, race/restart/idempotency results, Teacher/Child scoped screenshots dùng synthetic, metadata live-call và hai shutdown receipts.

Evidence public chỉ chứa metadata/synthetic được phép; không secret, `.env`, device credentials, raw provider output, real child data hoặc absolute machine paths. Private validated result phục vụ Teacher không được copy thành evidence publish. Không sửa receipt/cap marker của FEAT-061 để tạo một lượt mới.

Approval template hiện vẫn AWAITING_APPROVAL và chưa có approver/scope. **Chưa triển khai hoặc chạy test/runtime theo plan này.** Implementation chỉ bắt đầu khi `../approvals/TASK_APPROVAL.md` ghi APPROVED cho đúng revision/hash, task/manifest và owner scope.

## 11. Lịch sử review

Rev1 SHA-256 `B563BEB6552AADB4B2658BE8DE3806CE1DF401DAF5BF96D38D413DF56246155A` được giữ nguyên trong `../evidence/notes/PLAN_REV1_REVIEWED_20261029.md`. Claude review rev1: NEEDS_REVISION, 0 P1 / 3 P2 / 4 P3. Rev2 bổ sung F1–F7 ở mức kế hoạch, giữ OD-1–OD-4 mở và chưa có implementation approval. F1/F2 là cụ thể hóa invariant đã có; F3 chỉ tách minimum durable path, không mặc nhiên nhận toàn bộ BE2 persistence. Kết quả xử lý và checks ở `../evidence/notes/CLAUDE_PLAN_REVIEW_REV2_20261029.md`; chưa có verdict PASS của Claude cho rev2.
