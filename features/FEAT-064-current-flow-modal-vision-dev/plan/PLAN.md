# FEAT-064 — Plan kiểm chứng luồng hiện tại với Modal Vision ở dev

- Status: DRAFT
- Plan revision: 6
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

Chốt các quyết định ở mục 8, ADR/hợp đồng nguồn/eligibility/capability, inventory guard và từng method UoW, `OwnerFenceV1` hoặc phiên bản thay thế được owners ký nhận, manifest file chính xác và migration ownership. Chốt run manifest, chốt chống rollback độc lập DB, retry/deadline/outcome và lifetime quyền đọc status sau turn/pause/session finish trước task phụ thuộc. Approval phải chỉ rõ task/mốc được phép làm, quyền test DB và quyền provider nếu có. Không coi bảng đường dẫn dự kiến là execution manifest đã duyệt.

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
| T0 | Chốt ADR, contract/profile/policy, guard/state inventories, owner-fence version, run manifest, exact paths và migration order | — | — | OD-1–OD-4 và owner scope có disposition; từng consent call site/required profile fields, DB/run identity; approval đúng revision/task; witness spec Windows, failure model, test plan và bản chấp nhận rủi ro dư soạn sẵn để chủ task ghi vào approval; T0 chỉ tài liệu | M | Chồng FEAT-063; chủ task + owners |
| T1 | Synthetic eligibility evidence riêng; sửa đủ selected schema/guard BE1 và gate BE2 | T0 | T3, T6 | Inventory được tick từng site; synthetic profile tạo hợp lệ không giả consent; lifecycle join/admit/Start/group/turn/export đạt; REAL/unclassified/pending vẫn deny | L | Nhiều route/representation; BE1 + BE2 owners |
| T2 | Actor/authority/context và AI-capability adapters thật; tách status-read khỏi write guard | T1 | T4/T5, T6/T7a nếu khác file | Server xác minh grant/identity/scope/eligibility; write cần turn, status-own không cần active turn nhưng vẫn chặn revoke/foreign scope | M | Revocation/disclosure; BE1 + integration |
| T3 | Stroke DTO/profile, geometry/width và canvas dev trắng tương ứng | T0 | T1, T6/T7a | Strokes-only, cùng logical viewport/aspect/width; từ chối ngoài profile; dùng components/style có sẵn, visual gate AC20 | M | Render fidelity; BE1 + FE |
| T4 | Export authoritative source nhất quán tại epoch/revision | T3 | T2, T6/T7a | Canonical document + op manifest/digest đầy đủ; JSON client, mixed epoch và history không chứng minh được bị từ chối | M–L | Snapshot race; BE1 owner |
| T5 | CPU render + private artifact + admission receipt + source handoff | T4 | T6/T7a | Ảnh gắn đúng source hash/renderer version; decode thật; BE2 nhận đúng render/admission qua port | M | Overlay/receipt mismatch; BE1 + BE2 |
| T6 | Runtime observation/capability, provenance và `InvocationGuardPort` | T0 | T1–T5, T7a nếu khác file | Giữ guard C1/C2; guard thiếu/refuse/error không send; giữ phase/HTTP status ở transport boundary và phân loại known/UNKNOWN/NOT_SENT_CAP_CLOSED/NOT_SENT_CAP_UNAVAILABLE; mất provenance → UNKNOWN khi possible-send; fail-closed và transport-count test | M | Contract compatibility; BE2 owner |
| T7a | Minimal durable assistance/analysis repositories và migration | T0 | T3–T6 nếu khác file | Inventory từng method port/UoW theo selected path: dùng thì durable và có test; không dùng phải fail-closed nếu gọi, không no-op; schema/rollback/retention/restart | L | Chưa có runtime stores; BE2 + persistence owner |
| T7b | Owner-fence contract/adapter và acceptance UoW | T0,T7a | T7c chỉ khi khác file/transaction boundary | Version được owners duyệt; acceptance atomic với source/eligibility updates; không dùng fixture fence hoặc giữ lock qua GPU | L | Cross-owner transaction; core + BE1/BE2 owners |
| T7c | Server-issued run manifest, invocation ledger và witness local độc lập miền DB | T0,T7a | T7b nếu đã freeze integration contract | Token UNUSED hiện hữu pin run/DB/host/manifest, consume atomic/bền Windows; thử fault injection throwaway sau approval; restore DB cùng identity không mở cap | M–L | Cost/concurrency/recovery; BE2 + operator |
| T8 | Worker → guarded observe → atomic acceptance → analysis-only reconciliation | T2,T5,T6,T7a,T7b,T7c | Chỉ chuẩn bị client mock riêng sau contract freeze | Wire T6/T7c, không transport bypass; pilot `max_attempts=1`, UNKNOWN/HOLD không attempt mới; phân loại known/UNKNOWN/NOT_SENT_CAP_CLOSED/NOT_SENT_CAP_UNAVAILABLE; NOT_SENT_* hiển thị cho Child/Teacher không như lỗi provider, không nút thử lại; zero Sketch | L | Retry/accounting/TOCTOU; BE2 + integration |
| T9 | Runtime gateway request/cancel + child status / Teacher read | T2,T7a,T7b,T7c,T8 | T10/T11 theo contract | Accepted/ref trả sớm; status-own qua guard read riêng khi pause/turn đóng, revoke vẫn deny; worker/freshness đúng | M | Timeout/disclosure; BE1 + BE2 |
| T10 | Child UI flush/ack → preview nguồn đã export → request → trạng thái thật | T3,T9 | T11 | Preview đúng hash/profile ở r; giữ key/ref khi mất reply/poll denied; không auto resubmit/timer approved; AC20 | M | Pending ops/false success; FE owner |
| T11 | Teacher pending-analysis panel scoped, read-only riêng | T9 | T10 | Refresh còn item đúng nguồn/meaning unconfirmed; không biến Sketch-approval prototype thành analysis approval; AC20 | M | Disclosure/nhầm chức năng; FE owner |
| T12 | CPU + isolated persistence/runtime tests và regressions | T1–T11 | Review docs | Witness throwaway: atomic/durability Windows, crash/race/DB restore, xóa/mất file fail-closed; không provider thật, không tiêu witness live | M–L | Môi trường/migration; integration + owners |
| T13 | Fresh bounded live smoke từ nét vẽ thật của UI, nhưng synthetic | T12 + live scope được duyệt | — | Đúng nguồn/provenance và Teacher pending; manifest/DB/host và token UNUSED hiện hữu khớp; approval ghi chấp nhận rủi ro dư; một call; operator đối chiếu Modal log/ledger và shutdown receipts | M | Cost/unknown outcome; owner vận hành + test runner |
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
- Retry/accounting: pilot pin `max_attempts=1`; duplicate dispatch/timeout sweep không tạo attempt mới. Chỉ known khi có bằng chứng đủ tin cậy: từ chối trước outbound là chưa gửi, hoặc phản hồi hoàn chỉnh được contract xác thực là kết quả xác định; typed exception/HTTP status đơn thuần không chứng minh model chưa chạy. 5xx, URLError, reset, timeout, response thiếu/không chắc sau possible-send là UNKNOWN/HOLD; tập status known cụ thể phải được chứng minh theo endpoint contract, không mặc định 401/403/404/422 không tốn GPU. Cap đã claim không refund. A1 reservation consumed là trục riêng; không tự thêm global AiJob state.
- Run: operator/server tạo run ID ngoài client API; manifest pin approval/plan hash, expiry, DB identity/generation, witness identity, scope và config. Witness độc lập DB phải xác minh được trạng thái UNUSED có mặt và atomic transition sang CONSUMED, rồi DB ledger commit trước send. Mất/mismatch/không đọc được/rollback không xác định của witness hay DB fail-closed. Không xóa/reset/reuse; migration bảo toàn identity và ledger không tự cấp lượt. T0 chỉ đặc tả và lập test plan; fault injection dùng run/witness throwaway ở T7c/T12 sau approval. Witness live chỉ khởi tạo sau T12 đạt và live scope được duyệt.
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
| AC06 | Lặp command, lost reply và duplicate delivery không tạo call thứ hai; T6/T8 phân loại known/UNKNOWN/NOT_SENT_CAP_CLOSED/NOT_SENT_CAP_UNAVAILABLE; UI không retry hoặc báo nhầm NOT_SENT là lỗi provider |
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
| AC18 | Witness local single-host độc lập miền DB: token UNUSED hiện hữu pin run/DB/host/manifest → consume atomic/bền → DB commit → send; missing/mismatch/xóa/quarantine/unreadable fail-closed. T12 chứng minh bằng witness throwaway atomicity/durability Windows, race, fault injection mọi cửa sổ, DB restore cùng identity không mở cap. Mỗi restore DB hoặc host hủy authority, cần manifest + approval mới; approval M3 ghi chấp nhận rủi ro dư host rollback. Thiếu T12 hoặc văn bản chấp nhận trong approval thì M3 blocked. Không yêu cầu chứng minh chống rollback cấp OS cho B; max_attempts=1, UNKNOWN/HOLD, A1 accounting riêng |
| AC19 | Accepted/ref trước provider completion; poll không cần turn active, pause/turn closure có disposition rõ; revoked/foreign vẫn deny; khi poll unavailable/403 giữ ref, không giả provider failure/resubmit |
| AC20 | T3/T10/T11 dùng components/style hiện có, không thêm asset mới trong đề xuất hiện tại; mọi asset/visual mới phát sinh phải theo AGENTS mục 6: generated/provenance → visual approval → approved/applied; synthetic scoped screenshots không tự là approval |

Negative tests cần có: forged checkpoint JSON; client PNG giả; swap render/receipt; revision đổi giữa export và render; thiếu op ở ranh giới page; stale/revoke trước claim và giữa provider/acceptance; duplicate concurrent submission/delivery; storage/transaction failure; possible-send OSError/5xx/URLError/timeout sweep/restart không attempt mới; restore DB cùng identity, witness missing/unavailable/rollback, crash trước/sau witness claim/DB commit/send, bên thua concurrent guard; pause/turn closure khi poll và grant revoke; foreign scope; unsupported typed context; flag off; real/unclassified data; gallery/restore/operation ngoài profile.

Kiểm chứng theo pha:

Ca current-flow dương tính phải đi đúng lifecycle BE1: Teacher có assignment tạo Lobby; Child synthetic join trước Start và được admit; Teacher Start rồi cấp turn; Child vẽ/nhận ack và mới export/request. Không join mới sau Start, seed grant/consent để né API hoặc đổi stage tùy ý. Test setup giữ đúng quy tắc hiện có, không tự đưa quyền quản trị vào Child.

1. T0: review contract/ADR/manifest và approval của đúng owner, chưa chạy dịch vụ.
2. T1–T12 sau approval: unit/contract của modules thay đổi, focused frontend checks, integration trên DB local riêng với dữ liệu giả nếu được duyệt; chạy regression C1/C2/A1 và route isolation liên quan. Không dùng DB sản phẩm hoặc credential trong Git.
3. T13 chỉ khi T12 chứng minh invariant bằng witness/run throwaway và approval gồm live cùng chấp nhận rủi ro dư host rollback bằng văn bản. Sau T12 khởi tạo witness live mới; preflight xác minh manifest/host/DB/ledger và token UNUSED hiện hữu. Guard consume witness atomic → commit DB → send. Mỗi restore DB hoặc máy hủy quyền live, cần manifest + approval mới; missing/mismatch/unavailable dừng, không tự tạo witness mới. Sau live operator đối chiếu số request log Modal với ledger như kiểm tra bổ sung, không thay witness. `max_attempts=1`; possible-send UNKNOWN/HOLD; cap không phải USD, chỉ dữ liệu giả lập.
4. Static repository checks phù hợp; trước mỗi commit/push bắt buộc security validator cùng harness/architecture/diff checks theo repo. Không tự publish từ việc duyệt một lượt test.

## 8. Quyết định còn mở và mặc định đề xuất

| ID | Cần chốt trước task phụ thuộc | Đề xuất để chủ task duyệt |
| --- | --- | --- |
| OD-1 | Nguồn/render profile và lựa chọn renderer | Fresh synthetic append-only, strokes-only nền trắng; schema có geometry/width chuẩn; CPU rasterizer hẹp, Pillow là ứng viên; từ chối overlay/restore ngoài profile |
| OD-2 | Synthetic eligibility proof, required consent fields và toàn bộ selected lifecycle gates | Proof/tag/version riêng; quyết định representation synthetic profile khi consent refs NOT NULL và API đòi effective; tick inventory, không bịa legal consent/MemberFact; phối hợp subset FEAT-063, không Parent foundation |
| OD-3 | Vision capability, deadline, live-run authority và lifetime status-read | Chủ task chọn B: witness file local single-host độc lập miền DB + chấp nhận rủi ro dư host rollback bằng văn bản ở approval; điều kiện §12/AC18. IMAGE_ONLY nếu policy cho phép, một call/max_attempts=1; read lifetime sau turn/pause/session finish còn chốt |
| OD-4 | Minimal persistence T7a/b/c, owner-fence version/UoW, continuation và allocation | Freeze inventory từng method, required bền / unused fail-closed; owner-signed fence contract, một integration owner cho shared models/app/settings/migrations; invocation unknown tách A1 accounting; zero Sketch, không full BE2 adoption |

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

Claude review rev2: NEEDS_REVISION, 0 P1 / 1 P2 / 6 P3 (chi tiết review liệt kê P3-1–P3-6). Rev2 nguyên bytes SHA-256 `F321EE9FECF0870D52CC25B50F51B510F8046938A6D9AB99F188534DB9C7290F` được giữ trong `../evidence/notes/PLAN_REV2_REVIEWED_20261029.md`. Rev3 bổ sung các nội dung dưới đây; đây là draft, chưa có reviewer PASS hoặc implementation approval.

## 12. Điều kiện witness và runtime rev3–rev5

- **OD-3=B / chống DB restore:** Chủ task chọn file witness cục bộ single-host và chấp nhận rủi ro dư bằng văn bản trong approval: restore cả máy/System Restore/shadow/OneDrive rollback có thể mở lại lượt, gây thêm call có phí trên dữ liệu giả lập. Token UNUSED phải CÓ MẶT, xác minh và gắn run ID/DB identity/host/manifest hash; consume là chuyển atomic sang bản ghi CONSUMED bền. Thiếu cả hai, mâu thuẫn, không đọc được, xóa hay antivirus quarantine → đóng; absence không chứng minh UNUSED. File ngoài volume Docker DB, cloud sync và tập backup/restore DB; manifest pin host, mọi worker cùng host. T0 đặc tả cơ chế Windows tạo độc quyền, atomic transition, flush file và xử lý flush thư mục; T12 kiểm thử throwaway sau approval, không giả định NTFS/exFAT hay primitive đã bảo đảm. Mỗi restore máy hoặc DB hủy quyền live; cần manifest + approval mới. Đây là quy trình phụ thuộc phát hiện/báo restore, không chứng minh ngăn host rollback. Approval M3 phải ghi chấp nhận rủi ro dư; không chứng minh chống rollback OS là điều kiện cho B. Witness không cấp approval/lượt mới.
- **Thứ tự và concurrency:** preflight manifest + DB + token UNUSED; atomic consume witness → commit ledger → outbound, chỉ winner được send. Bên thua chưa gửi gọi `NOT_SENT_CAP_CLOSED` khi xác minh consumed; missing/unavailable/mismatch là `NOT_SENT_CAP_UNAVAILABLE`. Mọi ambiguity giữ đóng, không tự retry/refund/recreate; DB restore cũ không mở cap nếu witness không bị rollback. T0 chỉ đặc tả test/failure model và soạn bản chấp nhận rủi ro; T7c/T12 sau approval chạy fault injection throwaway từng cửa sổ, M3 blocked nếu thiếu bằng chứng atomicity/durability/DB-restore hoặc approval thiếu chấp nhận rủi ro. Witness live khởi tạo sau T12 và live approval. Sau live operator đối chiếu số request Modal log/ledger, không thay witness.
- **Deadlines:** T0 pin và xác minh điểm bắt đầu, bao gồm xếp hàng/cold start, HTTP, model/web function và sweep. Khi attempt timeout bắt đầu từ attempt start: `attempt_deadline > elapsed_pre_send + enforced_HTTP_wall_deadline + completion_margin`; HTTP wall deadline cần bao trùm cold start + inference + network margin đã dự kiến. `urlopen(timeout=...)` chưa chứng minh wall deadline tổng, phải có cơ chế enforce/verification hoặc chốt disposition late response fail-closed; Modal startup 300s, web timeout và backend timeout là giới hạn riêng, không tự hứa sẽ khớp. Không suy ra một con số cố định từ 23.9 giây đo một lần. Sweep không cắt request đang bay trong thời gian hợp lệ; timeout/cancel sau possible-send là UNKNOWN và cap đóng. Pin retry policy riêng cho pilot, không sửa default job khác.
- **UNKNOWN projection:** khi invocation UNKNOWN, Child/Teacher có quyền thấy “chưa rõ kết quả, chờ operator”, giữ request ref; `NOT_SENT_CAP_CLOSED`/`NOT_SENT_CAP_UNAVAILABLE` hiện chưa gửi/chờ operator, không hiện là lỗi provider. Không nút thử lại, không tự submit/new ID. Mapping override `failed_exhausted` mà không đổi A1 accounting; test lost reply/reload/denied/revoked.
- **Invocation guard:** T6 định nghĩa contract `InvocationGuardPort`; T7c thực hiện ledger/witness và T8 wire ngay trước transport send. Guard missing/denied/error không send; bảo vệ mọi outbound path và test concurrent duplicate/fault bằng transport đếm calls. Guard không dùng để né offline C1/C2.
- **UoW:** T0 lập inventory từng method assistance/analysis qua selected path, kể cả decision epoch, fence publication, cache, notice/invalidation nếu thực sự được gọi; method cần dùng phải có semantics đúng và tests (state mutations bền/atomic, pure read-only theo contract); method không hỗ trợ fail-closed khi bị gọi thay vì silent no-op. Không mặc định triển khai toàn bộ BE2 hoặc corrections.
- **Quyền đọc:** OD-3/T0 xác định expiry/revocation và tình huống sau turn, pause, session finish; request write vẫn có gate riêng. Status unavailable không tạo request mới.

## 13. Review rev3–rev4 và outcome boundary

Claude review rev3: NEEDS_REVISION, 1 P2 / 2 P3. Rev3 SHA-256 `53573E2A35CECCE08889F3C0C62072B1E92935353D79153574CF04774CD115BC` được giữ nguyên trong `../evidence/notes/PLAN_REV3_REVIEWED_20261029.md`. Claude review rev4: PLAN_REVIEW_PASS với 1 P3-C và khuyến nghị OD-3; rev4 snapshot tại `../evidence/notes/PLAN_REV4_REVIEWED_20261029.md`. Rev5 gộp OD-3=B và P3-C, chưa có review rev5 hoặc approval.

Bất biến thực thi: **đã gửi ⇒ ledger DB đã commit ⇒ witness đã CONSUMED**. Bảng suy từ trạng thái lưu chỉ hợp lệ khi xác minh không có restore/rollback liên quan và các primitive đã được chứng minh; host rollback là rủi ro dư B. Mỗi restore đã biết hoặc nghi ngờ hủy quyền live, không tự retry. Đặc biệt witness CONSUMED + ledger vắng sau DB restore có thể đã gửi trước restore: UNKNOWN, cap đóng; không suy ngược từ ledger vắng.

T0 phải chốt nguồn bằng chứng và quy trình operator ghi lịch sử restore trong run manifest. Lời khai operator có ích cho vận hành nhưng tự nó không chứng minh database chưa rollback; thiếu bằng chứng đáng tin cậy để loại trừ rollback thì mặc định UNKNOWN/cap đóng. Không giả định DB tự phát hiện restore cùng identity.

| Cửa sổ | Kết quả bảo thủ |
| --- | --- |
| Guard từ chối/worker thua trước outbound | Chưa gửi; witness consumed đã xác minh → `NOT_SENT_CAP_CLOSED`; missing/unavailable/mismatch → `NOT_SENT_CAP_UNAVAILABLE`; không ảnh hưởng winner |
| Crash trước claim | Chỉ coi chưa gửi/cap mở khi chứng minh được witness và DB chưa consumed và outbound chưa xảy ra; nếu không chắc fail-closed. Không tự retry |
| Witness UNUSED hiện hữu, DB chưa consumed | Chắc chắn chưa gửi nếu xác minh không có rollback witness/host và invariant còn hiệu lực; nếu không chắc → UNKNOWN/đóng |
| Witness CONSUMED, ledger chưa có dòng | Chắc chắn chưa gửi/cap đóng nếu chứng minh DB không rollback và đọc nhất quán; restore/nghi restore hoặc chứng cứ thiếu → UNKNOWN/đóng |
| Ledger đã commit, chưa có kết quả | UNKNOWN/cap đóng; crash trước outbound chỉ kết luận NOT_SENT khi có evidence độc lập đủ tin cậy |
| DB committed, outbound có thể đã xảy ra; 5xx/URLError/reset/timeout/mất body | UNKNOWN/HOLD, cap đóng; typed provider error không đủ chứng minh model không chạy |
| Phản hồi hoàn chỉnh xác thực theo contract | Known result/failure nếu contract cho phép xác định; cap đã tiêu và không tự retry |

Claude review rev5: PLAN_REVIEW_PASS kèm P3 cần khôi phục tiêu chí ở T0/T6/T8/T13 trước approval; bản rev5 nguyên bytes tại `../evidence/notes/PLAN_REV5_REVIEWED_20261029.md`. Rev6 khôi phục các tiêu chí đó và làm rõ bằng chứng restore; chưa có review rev6 hoặc approval.
