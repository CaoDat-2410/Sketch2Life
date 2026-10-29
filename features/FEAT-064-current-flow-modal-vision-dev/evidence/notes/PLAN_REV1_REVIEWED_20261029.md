# FEAT-064 — Plan kiểm chứng luồng hiện tại với Modal Vision ở dev

- Status: DRAFT
- Plan revision: 1
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

Runtime đích là `sketch2life.classroom_main:app` với composition current-flow được duyệt và worker tương ứng, không phải demo backend đã smoke. Child UI dùng `EXPO_PUBLIC_BE1_BASE_URL` trỏ backend này; URL/token Modal chỉ ở backend. Feature pilot phải opt-in ở dev và tuân thủ classroom fence, không mở route bằng cách dùng compatibility app để né fence.

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
| C1/C2 bridges và Vision V2 adapter | C1/C2 chủ động chặn HTTP thật; C2 đòi `/v1/vision/context`, Modal hiện không có |
| Teacher/Child UI và BE1 grant/assignment | Review timer của prototype không phải review state thật |

Các rủi ro phải giải quyết trước positive-path test:

1. `ConsentRecordModel` chỉ cho `pending/revoked`, nhưng device guard đòi `effective`. Chưa có bằng chứng runtime DB cho thấy đường Child hợp lệ vượt được điểm này. Không tự đổi consent thành effective.
2. Điểm nét vẽ được chuẩn hóa nhưng width đang theo layout; artwork/suggestion overlays không nằm trong operation. Screenshot parity chưa được chứng minh.
3. Sync operation phân trang không tự tạo một snapshot nhất quán tại revision r. Phải có export phía owner với epoch/revision và completeness đã pin.
4. Evidence kinds/result contracts BE2 hiện chỉ mô tả fake/offline; live-dev cần provenance/version trung thực.
5. FEAT-063 Rev33 đang chờ duyệt, chạm classroom fence, synthetic provenance và job ownership. Phải chốt quyền sửa file/migration giao nhau, không mặc nhiên thực hiện Rev33.
6. BE2-03 hiện tạo SketchIntent và gọi SketchStage khi reconcile thành công. Điểm dừng analysis-only cần một continuation contract riêng được duyệt; không nối fake/no-op SketchStage để giả hoàn tất.

Nguồn chi tiết và dòng code: `../evidence/notes/SOURCE_REVIEW_20261029.md`. Ba worktree BE2 đã đọc đều là tổ tiên của baseline dev; không có bridge mới hơn để chỉ cần merge.

## 4. Mốc triển khai

### M0 — Chốt hợp đồng và phạm vi owner trước code

Chốt các quyết định ở mục 8, ADR/hợp đồng nguồn/eligibility/capability, manifest file chính xác và migration ownership. Approval phải chỉ rõ task/mốc được phép làm, quyền test DB và quyền provider nếu có. Không coi bảng đường dẫn dự kiến là execution manifest đã duyệt.

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
| T0 | Chốt ADR, contract/profile/policy, owner allocation, exact manifest và migration order | — | — | Không còn mâu thuẫn scope ở mục 8; approval đúng revision/task | S–M | Chồng FEAT-063; chủ task + owners |
| T1 | Synthetic eligibility evidence riêng; sửa đủ schema/guard BE1 và gate BE2 trong scope | T0 | T3, T6 | Profile/device/group/artifact/source/BE2 nhận proof synthetic thật; REAL/unclassified/pending vẫn từ chối; không bịa consent boolean | M–L | Guard/schema/policy BE1/BE2; owners |
| T2 | Actor/authority/context/fence và AI-capability adapters thật | T1 | T4/T5, T6/T7 nếu khác file | Grant, membership, turn, age/purpose/eligibility, quyền AI riêng và Teacher assignment do server xác minh | M | Revocation/race; BE1 + integration |
| T3 | Stroke DTO/profile, geometry/width và canvas dev trắng tương ứng | T0 | T1, T6/T7 | Dev mode hiển thị strokes-only, không gallery/suggestion; client/server pin cùng profile/geometry và từ chối dữ liệu ngoài profile | M | Render fidelity; BE1 + FE |
| T4 | Export authoritative source nhất quán tại epoch/revision | T3 | T2, T6/T7 | Canonical document + op manifest/digest đầy đủ; JSON client, mixed epoch và history không chứng minh được bị từ chối | M–L | Snapshot race; BE1 owner |
| T5 | CPU render + private artifact + admission receipt + source handoff | T4 | T6/T7 | Ảnh gắn đúng source hash/renderer version; decode thật; BE2 nhận đúng render/admission qua port | M | Overlay/receipt mismatch; BE1 + BE2 |
| T6 | Runtime observation/capability và provenance version trung thực | T0 | T1–T5, T7 nếu khác file | Giữ guard C1/C2; adapter mới dùng Vision V2 hiện có; context không hỗ trợ bị từ chối | M | Contract compatibility; BE2 owner |
| T7 | State/receipt/review pointer + durable run-level invocation ledger + UoW/fence | T0 | T3–T6 nếu khác file | Reservation được commit trước send, dùng chung mọi ID/worker của run; restart/unknown không mở lại cap | L | Concurrency/durability; BE2 + core owners |
| T8 | Worker → observe → atomic acceptance → analysis-only reconciliation | T2,T5,T6,T7 | Chỉ chuẩn bị client mock riêng sau contract freeze | Lưu analysis/Teacher pending và settle đúng; không Sketch intent/event/outbox/call; duplicate/stale/revoked fail closed | M–L | TOCTOU/auto Sketch; BE2 + integration |
| T9 | Runtime gateway request/cancel + child status / Teacher read | T2,T7,T8 | T10/T11 theo contract | BE1 auth thật; trả accepted/request ref trước provider completion, worker xử lý sau; cô lập scope/fence | M | Timeout/disclosure; BE1 + BE2 |
| T10 | Child UI flush/ack → preview nguồn đã export → request → trạng thái thật | T3,T9 | T11 | Preview đúng hash/profile ở r; không gửi PNG/scope claim để được tin; giữ key khi mất reply; không timer approved | M | Pending ops/false success; FE owner |
| T11 | Teacher pending-analysis panel scoped, read-only | T9 | T10 | Refresh còn item đúng nguồn; meaning unconfirmed; Child không thấy Teacher-only result | M | Nhầm với Sketch approval; FE owner |
| T12 | CPU + isolated persistence/runtime tests và regressions | T1–T11 | Review docs | Các invariant mục 7 đạt, không provider thật; không hợp thức hóa fake composition | M–L | Môi trường/migration; integration + owners |
| T13 | Fresh bounded live smoke từ nét vẽ thật của UI, nhưng synthetic | T12 + live scope được duyệt | — | Một call, đúng nguồn/provenance, Teacher pending; giữ marker và xác nhận shutdown | M | Cost/unknown outcome; owner vận hành + test runner |
| T14 | Rà evidence, cập nhật trạng thái và bàn giao | T13 hoặc ghi rõ gate chưa chạy | — | Không nâng component/production/quality gate ngoài scope; ghi done/not-run thật | S | Overclaim; reviewer |

S: tài liệu hoặc thay đổi hẹp trong một vòng review. M: một hợp đồng/component với test liên quan. L: nhiều boundary/concurrency; tách tiếp thành manifest owner-sized trước khi code. Đây là effort tương đối, không phải cam kết ngày công; phụ thuộc hợp đồng và môi trường chưa chốt.

Critical path: `T0 → T1/T3 → T2/T4 → T5 → T8 → T9 → T10+T11 → T12 → T13 → T14`; T6/T7 là nhánh song song bắt buộc trước T8.

Không làm song song các task sửa cùng `be1_models.py`, shared runtime guards, `app.py`/router composition, result enums/contracts hoặc cùng `app/index.tsx`. T3 phải xong phần geometry trong Child UI trước T10. Mỗi nhóm dùng manifest riêng; migration order do owner chốt, không tự merge Alembic heads.

## 6. Hợp đồng và runtime cần chốt

Chi tiết đề xuất ở `CONTRACT_OUTLINE_DRAFT.md` và `OWNER_PATH_MANIFEST_DRAFT.md` cùng thư mục; chưa tạo DTO/API/source thật.

- Nguồn: org/session/canvas/group, epoch/revision, through-operation ID, accepted-op manifest hash, canonical checksum, schema/reducer version và contributor scope do server suy ra.
- Render/admission: bind source ref/hash → render ref/hash/dimensions/version → actual validation outcome/policy/receipt hash. Admission của FEAT-018 không tự đồng nghĩa receipt BE2; cần mapping có nguồn gốc đúng, không bịa PASS.
- Request: explicit user action + stable idempotency + server-resolved source/actor; không dùng session demo để thay session BE1.
- HTTP/worker: Child API hiện timeout 12 giây, ngắn hơn lượt model đã đo. Gateway trả accepted + request/status ref mà không đợi provider; worker xử lý và client poll request đã có. Poll/lost reply không tự tạo job mới. Không chỉ tăng timeout để che thiếu lifecycle.
- Eligibility: proof synthetic là một loại bằng chứng riêng, không biến thành `consent_effective=true` hoặc consent pháp lý giả trong `MemberFact`/`ContextDecision`. Chốt amendment có version cho các gate BE1 và BE2 liên quan; origin flag đơn thuần không đủ. Quyền canvas.read/write không tự cấp quyền yêu cầu/hủy/đọc AI.
- Freshness: không khóa việc vẽ suốt inference. Request giữ nguồn bất biến tại r; operation mới/restore/epoch hoặc owner eligibility đổi làm request cũ stale/non-applicable trong pilot, không tự rebind hoặc tự gửi lại. Read projection luôn kiểm tra currentness/revocation.
- Acceptance: revalidate nguồn/quyền/context dưới owner fence/UoW được duyệt ở điểm commit. Chỉ đọc lại trước/sau GPU không đủ chứng minh atomicity; không giữ transaction DB suốt thời gian gọi GPU.
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
| AC05 | Grant/turn/membership/assignment/age/purpose/eligibility sai hoặc bị thu hồi thì từ chối trước chạy và trước disclose/acceptance |
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
| AC17 | Synthetic eligibility có proof/tag riêng xuyên BE1/BE2; không forge effective consent; mọi guard dương tính cần thiết được kiểm chứng |
| AC18 | Cap live ở backend ledger, commit trước send và chống concurrent/new-ID/restart; possible-send/timeout/crash giữ unknown, không retry hoặc tự mở lại |
| AC19 | Gateway trả receipt trước provider completion; Child poll request đã có, không giữ HTTP chờ GPU hoặc tự submit lại để chờ kết quả |

Negative tests cần có: forged checkpoint JSON; client PNG giả; swap render/receipt; revision đổi giữa export và render; thiếu op ở ranh giới page; stale/revoke trước claim và giữa provider/acceptance; duplicate concurrent submission/delivery; storage/transaction failure; timeout/unknown budget; foreign scope; unsupported typed context; flag off; real/unclassified data; gallery/restore/operation ngoài profile.

Kiểm chứng theo pha:

Ca current-flow dương tính phải đi đúng lifecycle BE1: Teacher có assignment tạo Lobby; Child synthetic join trước Start và được admit; Teacher Start rồi cấp turn; Child vẽ/nhận ack và mới export/request. Không join mới sau Start, seed grant/consent để né API hoặc đổi stage tùy ý. Test setup giữ đúng quy tắc hiện có, không tự đưa quyền quản trị vào Child.

1. T0: review contract/ADR/manifest và approval của đúng owner, chưa chạy dịch vụ.
2. T1–T12 sau approval: unit/contract của modules thay đổi, focused frontend checks, integration trên DB local riêng với dữ liệu giả nếu được duyệt; chạy regression C1/C2/A1 và route isolation liên quan. Không dùng DB sản phẩm hoặc credential trong Git.
3. T13 chỉ khi approval bao gồm live: owner khởi động bằng recipe đã kiểm chứng. Backend phải atomically reserve/consume một invocation của approved dev run trước outbound HTTP; helper chỉ là chốt bổ sung. Cap chống mọi request ID, attempt, worker delivery và restart; job/provider không auto retry. Possible-send/crash/timeout là unknown, giữ hold và chờ xử lý. Tối đa một inference-bearing call; FEAT-061 không cấp thêm lượt này. Đây là cap số lần gọi, không phải cam kết USD; timeout/stop procedure ghi trong run manifest.
4. Static repository checks phù hợp; trước mỗi commit/push bắt buộc security validator cùng harness/architecture/diff checks theo repo. Không tự publish từ việc duyệt một lượt test.

## 8. Quyết định còn mở và mặc định đề xuất

| ID | Cần chốt trước task phụ thuộc | Đề xuất để chủ task duyệt |
| --- | --- | --- |
| OD-1 | Nguồn/render profile và lựa chọn renderer | Fresh synthetic append-only, strokes-only nền trắng; schema có geometry/width chuẩn; CPU rasterizer hẹp, Pillow là ứng viên; từ chối overlay/restore ngoài profile |
| OD-2 | Synthetic eligibility proof và quyền sửa đủ schema/guard/domain gate BE1/BE2 | Evidence synthetic có tag/version riêng cho isolated dev; không bịa effective consent/MemberFact; chỉ subset tối thiểu, phối hợp field/migration FEAT-063; không Parent foundation |
| OD-3 | Vision capability, policy/profile/level/purpose và budget | IMAGE_ONLY `/v2/vision` nếu policy cho phép; backend vẫn kiểm tra context/eligibility; typed-context unsupported; live smoke tối đa một call, không auto retry |
| OD-4 | Persistence/fence/version, analysis-only continuation và owner allocation | Dùng port/UoW/datastore được duyệt; state và run-level cap bền tối thiểu; success không Sketch side effect; freeze exact manifest/versions, không full BE2 adoption |

Luồng hiện tại đã được chọn; không hỏi lại lựa chọn đó. Nếu thiếu quyết định/approval ở trên, tiếp tục làm rõ hồ sơ nhưng không chạy implementation phụ thuộc. Khi quyền đúng scope đã được cấp thì không hỏi lại vô cớ. Approval phải ghi task/mốc được duyệt và quyền DB/live nếu có; phê duyệt planning không đồng nghĩa phê duyệt các thao tác đó.

## 9. Rủi ro, giới hạn và rollback

- Tưởng checksum là nguồn tin cậy: tách byte integrity khỏi semantic derivation; server export từ history đã validate, giữ legacy nguyên trạng.
- Tưởng ảnh gửi giống canvas: pin geometry/profile, preview nguồn render; không âm thầm bỏ gallery/suggestion layer.
- Bất nhất consent: giải quyết hợp đồng synthetic riêng; không flip pending/effective, không nhận classification từ Child.
- TOCTOU/duplicate: owner fence/UoW + durable uniqueness/reservation, test race thật; unknown outcome giữ hold.
- Trùng FEAT-063: chỉ chọn subset phục vụ current flow, một owner cho shared files/migrations; không implement Rev33 ngầm.
- Scope phình: dừng tại Teacher pending-analysis, không kéo video/Parent/Sketch/approval vào. Video-specific gates của FEAT-057 không tự là prerequisite cho lát cắt này.
- Model quality chưa đạt production: live pass chỉ chứng minh kết nối/contract cho synthetic case, không nâng FEAT-003 quality gate.

Rollback đề xuất: feature flag dev mặc định off; tắt wiring/worker mới, giữ drawing/request/audit data và các guard cũ. Không xóa bảng/artefact/snapshot để rollback. Downgrade có dữ liệu phải dừng để owner xử lý; không tự migrate hoặc restore DB.

## 10. Evidence và bàn giao

Lưu theo task trong feature này: baseline/source hashes, owner decisions/ADR, frozen manifests, contract tests, source/render/admission receipts, race/restart/idempotency results, Teacher/Child scoped screenshots dùng synthetic, metadata live-call và hai shutdown receipts.

Evidence public chỉ chứa metadata/synthetic được phép; không secret, `.env`, device credentials, raw provider output, real child data hoặc absolute machine paths. Private validated result phục vụ Teacher không được copy thành evidence publish. Không sửa receipt/cap marker của FEAT-061 để tạo một lượt mới.

Approval template hiện vẫn AWAITING_APPROVAL và chưa có approver/scope. **Chưa triển khai hoặc chạy test/runtime theo plan này.** Implementation chỉ bắt đầu khi `../approvals/TASK_APPROVAL.md` ghi APPROVED cho đúng revision/hash, task/manifest và owner scope.
