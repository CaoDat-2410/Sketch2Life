# M0 V7 — Đề xuất chốt StoryRun-lite Vision cho BE demo

Ngày: 2026-11-02. Trạng thái: **DRAFT / CHỜ OWNER DUYỆT / CHỜ REVIEW ĐỘC LẬP**. Đây là đề xuất kiến trúc và contract, không phải approval triển khai. Không được coi các lựa chọn bên dưới là owner đã duyệt.

V7 thay thế V6 sau khi review độc lập kết luận NEEDS_REVISION (2 P1, 9 P2, 1 P3). Bản này làm rõ worker không chặn API, fencing, race/recovery upload Core, mapping ownership/state, evidence và wire contract. Report V3/V6 đã lưu nguyên văn trong evidence; report gốc V4/V5 chưa khôi phục được trong checkout, nên crosswalk ghi rõ phần đó là tái dựng, chưa phải archive đầy đủ.

## 1. Mục tiêu, ranh giới và baseline

Mục tiêu đề xuất là một flow BE demo Parent, chỉ dùng dữ liệu tổng hợp: tạo một run → nhận ảnh tranh giấy → validate và chuẩn hóa ảnh → gọi Vision đúng một lần → API cho frontend đọc trạng thái/kết quả → người lớn xác nhận chủ thể. Bruno và OpenAPI dùng để kiểm tra/ghép API; UI do người khác phụ trách.

Goal gộp S1+S2 chỉ được viết sau khi owner chấp nhận M0 và có plan cùng approval riêng. Goal dùng fake/loopback để chứng minh API, persistence, guard, recovery và contract. Gọi Modal thật là cổng riêng, chỉ sau review readiness và approval live.

Baseline:

- M0 V5: SHA-256 **FE532FB2EEC71DAE4A407428C23A1F54267698C3B9CA8262C971F410F1590262**; review độc lập kết luận CHƯA ACCEPTED, 1 P1, 2 P2 và 1 P3.
- M0 V6: SHA-256 **8240A3FA208C9B41D157A5254F520CD3E9F460DAC13DFE82D21E33911E573018**; review V6 kết luận NEEDS_REVISION (2 P1, 9 P2, 1 P3), report nguyên văn tại `evidence/STORYRUN_LITE_VISION_M0_V6_INDEPENDENT_REVIEW_20261102.md`, SHA-256 **E80C77E1614093137744FFDBC84B03E61FE2F61AB86E710D0D991DD2EFD0ABC3**.
- M0 V4: SHA-256 **96D40096E7D57DFBBBF270D80AD7BE2C24555D69935156CBBEA5A648C170BC7E**; review độc lập kết luận CHƯA ACCEPTED, 2 P1 và 2 P2.
- M0 V3: SHA-256 **2223310837BD1B42757CE818BF932FF5F98D1AE9EB7FB5552904F3AF9A51FCEE**.
- M0 V2: SHA-256 **06346124F6851DD401148CE25EC2541B29C2738E0D67A77FE3258666F81CB71B**.
- HEAD: **a88de875ff92e9b4d4fa5cc2f5f8d5fc1f626f58**, nhánh **feature/feat063-be-foundation**.
- Working tree có nhiều thay đổi A2 chưa commit cùng các draft M0/roadmap local. Giữ nguyên các thay đổi có sẵn; chỉ V7 và hai report review mới là output của lần này. Goal tương lai dùng worktree/snapshot riêng ghim HEAD để tách baseline.
- A2 pause report ghi PostgreSQL cleanup teardown lỗi FK; database cục bộ có thể còn synthetic rows. Không dùng/dọn database đó. Test PostgreSQL chỉ trên disposable database mới, tạo và xóa có kiểm chứng.
- SRS FEAT-063 v2.3 và DATA_TABLE_REGISTER là draft. Rev37 vẫn là catalog baseline; operation pilot được đếm riêng.
- FEAT-061 smoke chứng minh đường demo Modal cũ với ảnh synthetic, không chứng minh A1 guard/ledger/transport chạy với Modal thật.

## 2. Các lựa chọn owner đề xuất

Mọi D dưới đây vẫn **CHỜ OWNER**. Bản nháp không tự duyệt deviation hoặc migration.

| ID | Đề xuất | Giới hạn/trách nhiệm |
|---|---|---|
| D1 — Scope | Parent synthetic; một run, một ảnh được chấp nhận, một Vision attempt; trả chủ thể đề xuất/độ không chắc chắn và cho người lớn xác nhận. Có thể thay một upload bị reject trước khi attach; không được gọi Vision khi admission chưa sạch. Chưa hỗ trợ correction/rerun/cancel StoryRun command, Teacher auth/assignment thật, story/video/audio, quota production hay UI. | Ghi deviation với SRS AT-14 và lệnh hủy StoryRun chưa có trong pilot; không tuyên bố hoàn tất các yêu cầu này. |
| D2 — Identity | Một actor/profile synthetic cố định do server cấu hình; chỉ local/test, synthetic gate bật, API bind loopback. Không nhận X-Actor-Ref hoặc owner ID để phân quyền. | Đây không phải Parent Authentication, BOLA protection hay authorization cho dữ liệu thật. Startup fail-closed ngoài chế độ demo. |
| D3 — Binding ảnh | Thêm typed `PhotoInputV1`/`StoryPhotoBindingV1` và `StoryPhotoVisionAdapterV1`/bridge riêng; không giả `RenderBinding`/`CheckpointBinding`, không đổi codec/call sites canvas. Photo bridge dựng `LightningVisionRequestV2` theo schema hiện có (`source_image.artifact_ref/sha256/content_type/content_base64` cùng trusted admission receipt) từ đúng bytes normalized rồi gọi A1 `HttpJsonTransport`; response V2 map vào Story result. Wrapper dùng generic request type hoặc equivalent typed adapter để giữ cùng guard identity và không buộc `ObservationRequest.render`. Thêm optional `before_finalize` hook và `success_evidence_kind`; default giữ nguyên hành vi/evidence canvas. Story hook ghi durable result trước finalize, chỉ sau response V2 hợp lệ; hook lỗi sau SENT trả UNKNOWN/hold, không resend. Evidence kind do server config chọn: `STORY_PHOTO_LOOPBACK` cho test, `STORY_PHOTO_LIVE` chỉ sau live gate; client không tự gán. | Không truyền `processing_image_ref` vào `legacy_v2`, không sửa `ObservationRequest`, codec, `application/services/vision_analysis.py`, Modal server hay canvas call sites. Chỉ cho phép additive type/hook trong shared guard và Story-specific bridge có allowlist riêng; regression chứng minh canvas default behavior/evidence không đổi. |
| D4 — Admission và AV | Model input tuân FEAT-018: PNG/JPEG, tối đa 5.000.000 byte, 4 MP, cạnh 4096; client chuẩn hóa và server chỉ xác minh chữ ký/media/dimensions/hash, không tái chuẩn hóa. Original tùy chọn cũng bị giới hạn 5 MB/4 MP/cạnh 4096 trong demo nhỏ. Mỗi source/normalized asset được decode trong subprocess có hard wall timeout 3 s, giới hạn memory 256 MiB và kill khi vượt; nếu runtime OS không cung cấp cách enforce thì readiness fail. Vision chỉ nhận khi mọi asset đính kèm READY/CLEAN. | Đây là deviation tạm với SRS §24.2 (20 MiB/40 MP/WebP/server normalization), phải được owner chấp thuận. Không tuyên bố hỗ trợ ảnh 12 MP. Scanner/decoder absent, ERROR, timeout hoặc INFECTED fail-closed và không provider call. |
| D5 — Asset/scope | Core Asset là nguồn chuẩn. Metadata mới thêm `owner_scope_kind/ref` typed (`PARENT_ACCOUNT` hoặc `ORGANIZATION`); giữ `organization_id` legacy nullable có điều kiện: org asset phải có org ref, Parent asset phải có parent ref và không organization giả. Migration backfill hàng cũ thành ORGANIZATION, giữ hash/type/size/storage. Original và normalized là hai asset riêng; transform edge mới chỉ ghi tại `core.asset_lineage`. | DATA_TABLE_REGISTER phải sửa trước migration: owner constraint, index/FK, state mapping và tương thích dữ liệu legacy. Core persisted upload `COMPLETED` là nguồn duy nhất cho asset ref; API `READY` chỉ là projection của `COMPLETED` + validation CLEAN. Không dùng `source_refs` cho lineage mới. |
| D6 — Identity invocation | Server tạo `story_run_id` UUIDv4 ngẫu nhiên ổn định; chính UUID string này là public `story_run_ref` opaque và ledger `run_id`. UUID không chứa nghĩa nghiệp vụ; không tạo alias/map riêng. | Guard A1 parse run_id bằng UUID. Tất cả lệnh lặp lại cùng key/fingerprint phải trả lại cùng story_run_id. |
| D7 — Job/attempt và ledger namespace | Vì demo chỉ có stage VISION_SUBJECT_V1 và đúng một attempt/run, đề xuất job_id = UUIDv5(NAMESPACE_URL, “sketch2life:story-vision:v1:{story_run_id}:job”), attempt_id = UUIDv5(NAMESPACE_URL, “sketch2life:story-vision:v1:{story_run_id}:attempt:1”). organization_id của ledger dùng hằng kỹ thuật “storyrun-lite-parent-demo-v1”; đây chỉ là namespace khóa/phân vùng invocation, không phải Parent scope, không tạo organization row và không cấp quyền. | Tuple/derivation version được lưu hoặc suy ra ổn định từ StoryRun UUID; exact replay/restart phải tạo lại đúng tuple. Invocation ledger hiện dùng String cho các ID và organization_id, không có FK trên invocation. Nếu code/schema/runtime thực tế có ràng buộc khác, dừng trước provider call và xin owner chọn mapping; không tạo organization giả. |
| D8 — Kết quả bền vững | Story understanding revision/immutable invocation result receipt là nguồn chuẩn nội dung. Story-specific `before_finalize` hook ghi receipt + structured result trong một UoW trước ledger finalize; projection `story.runs.current_understanding_revision_ref/state` cập nhật bằng CAS theo expected run revision + worker epoch. Lưu raw transport body SHA khác canonical result SHA, contract version và tuple. | DATA_TABLE_REGISTER cập nhật trước migration; sink idempotent theo tuple. Immutable receipt có thể được reconcile sau lock loss; stale worker không thể ghi đè run head. Canvas path giữ hook mặc định rỗng. |
| D9 — UNKNOWN và reconcile | Ledger là anti-resend barrier, không phải nguồn payload. Nếu result receipt bền và tuple là accepted run attempt, API/reconciler có thể chiếu SUBJECT_REVIEW kể cả ledger UNKNOWN, không mutate UNKNOWN. Nếu chưa có result hoặc attempt CLAIMED/SENT/UNKNOWN thì dùng SRS `AWAITING_RECONCILIATION`, code extension đúng ngữ cảnh, retry_allowed=false và operator action; không `INPUT_REVIEW`, cooldown retry hay redispatch. | Result receipt không chứng minh provider hoàn tất nếu chưa có response V2 hợp lệ. UNKNOWN không retry tự động hoặc dựa riêng vào thời gian; live retry cần đối soát/owner decision và command mới được phê duyệt riêng. |
| D10 — API/OpenAPI | Giữ route SRS `/v1/story-runs`, `/assets` và `/subject-confirmation`; không `/drawing` hoặc `/subject-review`. Goal S1+S2 phải tạo OpenAPI pilot versioned gồm đủ schema, error envelope, headers, status, polling, examples và concurrency semantics; đây là gate trước handoff UI. | Mục 4 chốt contract pilot cụ thể. Các mã thêm cho pilot là extensions có version; Rev37 operation catalog vẫn đếm riêng. |
| D11 — AiJobService | Hoãn full AiJobService/outbox/multi-stage retry cho demo một stage; Story sở hữu state/result, A1 ledger sở hữu invocation. Tái dùng `pilot_policy` `max_attempts=1`, không endpoint reanalyze. | Process/lease loss hoặc UNKNOWN không mở attempt khác; run giữ SRS `AWAITING_RECONCILIATION` đến khi receipt cùng tuple được reconcile hoặc operator xử lý. Đây là nợ demo, không phải lifecycle production. |
| D12 — Worker topology | Một API process bị giới hạn bằng PostgreSQL session advisory lock trên dedicated connection. `asyncio.Queue`/semaphore tổng capacity=1 (tính cả queued + running); worker dùng `ThreadPoolExecutor(max_workers=1)` hoặc tương đương để chạy toàn bộ sync A1 `observe()` ngoài event loop. Blocking DB/object-store work không chạy trên event loop; status/readiness có đường điều khiển riêng để trả trong lúc loopback call chậm. Lease loss làm readiness fail, từ chối lệnh mới và kích hoạt D17 fencing. | Reserve capacity trước khi ghi PENDING; đầy thì 503 `QUEUE_UNAVAILABLE` và không receipt/key consumption. Queue trong RAM không dispatch lại sau restart. Startup chốt PENDING thành hold trước readiness. Validation retry được bằng key mới; Vision sau SENT tuyệt đối không tự resend. |
| D13 — Test baseline | Dùng worktree/snapshot riêng ghim HEAD; PostgreSQL chỉ trên disposable DB mới, cleanup được chứng minh. | Không dùng/dọn DB A2 hoặc BE1 cục bộ chưa xác định sạch. |
| D14 — Story command receipt | Giữ `story.command_receipts` schema/scope/hash/fingerprint/16 KiB snapshot và CHECK/unique như V6; `POST /story-runs` ghi run+FINAL 201; attach ghi binding+PENDING rồi FINAL 202 sau queue ack; confirmation ghi decision+FINAL 202. Same-key/fingerprint PENDING chờ cùng dispatcher; nếu mất dispatcher thì recovery chốt FINAL hold, không enqueue lần hai. Deterministic 4xx sau khi command được nhận là FINAL; pre-acceptance validation (đặc biệt `UPLOAD_INCOMPLETE`) và queue-full không consume key/receipt. Raw key/bytes/provider payload/signed URL không lưu. | No TTL trong pilot cho Story và Core receipt; command response replay vẫn đúng dù upload resource đã EXPIRED (GET có thể trả 410). Production retention phải sửa SRS/contract trước khi TTL/purge receipts. |
| D15 — Quarantine scanner | Thêm versioned `ImageSafetyScannerPort`; scan đúng digest của từng source/original và normalized asset trong deadline tối đa 15 giây/asset. Mỗi asset CLEAN mới thành Core COMPLETED/API READY hoặc attach/Vision; ghi scanner version/digest/time. Fake scanner có CLEAN/INFECTED/ERROR/timeout. | Live Modal readiness cần scanner thật CLEAN cho exact hashes; absent/ERROR/timeout fail-closed. Không chọn vendor ở M0. |
| D16 — Core upload command receipt | Thêm `core.upload_command_receipts` cho create/complete/abort với `receipt_id`, `actor_scope_kind/ref`, `operation`, `resource_scope_ref`, `idempotency_key_sha256 CHAR(64)`, `request_fingerprint_sha256 CHAR(64)`, PENDING/FINAL, status, response contract version, bounded 16 KiB snapshot, resource ref, created/finalized timestamps và `state_version`. Unique `(actor_scope_kind, actor_scope_ref, operation, resource_scope_ref, idempotency_key_sha256)`; CHECK PENDING không có response/finalized fields, FINAL có đủ. Core Idempotency-Key là 1–128 printable ASCII chars, hash SHA-256 của exact UTF-8; fingerprint canonical hóa method/operation/API version/purpose/size/hash/expected state-version. `core.upload_parts` unique `(upload_session_id, part_no)` + digest; part ≤4 MiB và dùng natural key `(session, part_no)` + digest. | Core receipt không TTL trong pilot. Session giữ legacy lifecycle `OPEN/COMPLETED/ABORTED/EXPIRED/FAILED`; bổ sung `validation_state` (`NONE/PENDING/CLEAN/QUARANTINED/REJECTED`), `state_version`, `purge_state`, `purge_completed_at`. API map OPEN/NONE→RECEIVING, OPEN/PENDING→VALIDATION_PENDING, OPEN/QUARANTINED→QUARANTINED, COMPLETED/CLEAN→READY, FAILED/REJECTED→REJECTED; chỉ COMPLETED/CLEAN có asset ref. |
| D17 — Worker epoch/fencing | Một singleton runtime lease row giữ monotonically increasing `worker_epoch`; process chỉ tăng epoch sau khi lấy advisory lock. Mọi command/receipt lưu epoch + expected run revision. Invocation ledger/guard có additive fence hook để transaction của `claim` và `mark_sent` xác minh epoch hiện hành cùng expected attempt trước khi commit. Lock loss trước SENT ⇒ guard denial và zero HTTP send; sau SENT, attempt đó có thể hoàn tất đúng một lần, process mới thấy SENT và không gửi lại. | Result receipt immutable theo tuple+epoch; run head chỉ update CAS nếu revision/epoch còn khớp. Stale epoch không thể overwrite recovery. Reconciler có thể đọc receipt hợp lệ của đúng attempt rồi project dưới epoch hiện hành; không tạo attempt/provider send mới. |
| D18 — Core session serialization/cleanup | `PUT part`, `POST complete`, `DELETE abort` và expiry sweeper lock cùng upload_session row `FOR UPDATE` hoặc CAS `state_version`; chỉ một transition thắng. Part chỉ được thêm khi OPEN + validation_state=NONE. Complete kiểm liên tục part 1..N + byte sum + aggregate SHA trước PENDING/queue; thiếu part trả 422 `UPLOAD_INCOMPLETE`, không tiêu key và session vẫn resumable. | Duplicate cùng key/fingerprint PENDING chỉ chờ dispatcher đó; nếu dispatcher mất thì startup chốt hold, không tạo validation thứ hai. Abort/expiry ghi tombstone + `purge_state=PENDING` bền trước 202; startup và periodic sweeper idempotently xóa mọi stored part/staging object rồi ghi PURGED. Retry upload, abort, expiry không đua state; orphan staging objects bị quét/purge bằng deterministic session prefix và TTL phụ trợ. |

## 3. Luồng command, invocation và phục hồi bắt buộc

1. `POST /story-runs` tạo UUID run/input và FINAL 201 receipt trong cùng Story transaction. Run UUID đồng thời là `story_run_id`, opaque public `story_run_ref` và ledger `run_id`. Fingerprint gồm method/operation, canonical request body, contract version và actor/scope do server resolve. Cùng key/fingerprint replay snapshot; khác fingerprint là 400 `INVALID_IDEMPOTENCY_KEY`. Unique active-owner constraint cho 409 `ACTIVE_RUN_EXISTS`.
2. Core upload create/part dùng session owner scope Parent có kiểu. `PUT part` khóa row session; nếu `(session, part_no)` đã có cùng digest thì replay 200 trước khi xét lifecycle, nếu digest khác thì 409 `UPLOAD_PART_CONFLICT`. Chỉ part mới được nhận khi `OPEN + validation_state=NONE`; ghi object/metadata trong cùng vùng serialize, metadata commit trước nhả row lock. Object key staging deterministic theo session/part/hash.
3. Mọi mutation session (part, complete, abort, expiry) cùng serialize qua row lock/CAS `state_version`. Complete chỉ reserve capacity sau khi kiểm part liên tục 1..N, tổng bytes và checksum; thiếu part trả 422 `UPLOAD_INCOMPLETE` trước khi tiêu key, giữ RECEIVING/resumable. Hai complete khác key: transition đầu tiên OPEN→VALIDATION_PENDING thắng; request sau 409. Cùng key/fingerprint đang PENDING chờ đúng dispatcher hoặc startup chốt hold; không dispatch validation hai lần.
4. Khi capacity còn, Core transaction ghi validation_state=PENDING + Core PENDING receipt, commit, enqueue gated command, nhận ack rồi chốt FINAL 202; chỉ sau commit mở gate. Worker dùng sync image decode/scanner/storage trong bounded worker thread/process, không block FastAPI event loop. Queue full trả 503 `QUEUE_UNAVAILABLE` trước mutation/receipt. Worker kiểm chữ ký/media/dimension/aggregate hash; scan CLEAN mọi source/normalized digest; chỉ khi đạt mới chuyển persisted upload state COMPLETED + validation_state=CLEAN và tạo Core Asset ref.
5. Mapping API: Core OPEN/NONE→RECEIVING; OPEN/PENDING→VALIDATION_PENDING; OPEN/QUARANTINED→QUARANTINED (retry scan/validation bằng key mới); COMPLETED/CLEAN→READY và asset ref; FAILED/REJECTED→REJECTED; ABORTED/EXPIRED giữ nguyên. DATA_TABLE_REGISTER phải ghi mapping, validation fields, owner scope, state_version và cleanup fields trước migration. Core `organization_id` không giả Parent tenant; Parent ref typed, org legacy rows được backfill.
6. Abort và expiry cạnh tranh cùng row lock với part/complete. Abort chỉ RECEIVING/QUARANTINED; expiry chỉ session hết hạn ở trạng thái resumable. Transition ghi ABORTED/EXPIRED, purge_state=PENDING, tăng version và FINAL 202 receipt trong cùng transaction. Durable tombstone là lệnh cleanup; startup/periodic sweeper xóa tất cả part/staging objects idempotently, rồi đánh dấu PURGED. Crash sau 202 không làm mất cleanup. Command receipt/tombstone không xóa theo session TTL trong pilot.
7. Story attach/dispatch chỉ nhận asset READY/CLEAN đã thuộc actor/run và đúng digest; request có expected run revision + Idempotency-Key. Reserve một permit tổng active+queued trước transaction. Full → 503 không mutate/key. Story transaction lock/CAS run revision, ghi binding + `INPUT_PROCESSING` + PENDING receipt; enqueue gated command; queue ack → FINAL 202 commit → mở gate. Duplicate cùng key PENDING chờ dispatcher; nếu dispatcher không còn, recovery chốt FINAL 409 `VISION_ATTEMPT_HOLD`, không enqueue mới.
8. Startup chỉ sau khi lấy advisory lock và cấp epoch mới mới reconcile PENDING receipts: không redispatch; Core validation receipt pending thành QUARANTINED/hold retryable bằng key mới (zero provider); Story attach pending thành `AWAITING_RECONCILIATION`/`VISION_ATTEMPT_HOLD`. Queue RAM không là nguồn dispatch bền.
9. Worker A1 chạy đồng bộ trong thread executor riêng; mọi transition `claim` và `mark_sent` transactionally kiểm worker_epoch + expected run revision qua D17. Lock/fence refusal trước SENT là zero send. Sau durable SENT chỉ attempt đó được phép đi qua HTTP, kể cả lock loss ngay sau SENT; process mới không bao giờ mở attempt khác. Deadline/decode/scanner không block event loop.
10. Story result hook nằm trong `InvocationGuardedVisionObservationPort` trước `finalize()`: khi response V2 hợp lệ, UoW ghi immutable result/revision receipt keyed by run/job/attempt/hash. Cập nhật run head chỉ bằng CAS expected revision+worker_epoch. Hook/write failure sau SENT tạo UNKNOWN/hold, không success/resend. `transport_response_body_sha256` là raw HTTP body; `canonical_result_sha256` là canonical validated JSON; không gộp hai hash.
11. Nếu ledger finalize thành UNKNOWN nhưng durable result receipt tồn tại và tuple đúng, reconciler giữ ledger UNKNOWN, đọc receipt và cập nhật Story projection dưới epoch hiện hành; API có thể trả SUBJECT_REVIEW. Nếu không có receipt/result mà ledger CLAIMED/SENT/UNKNOWN, state là SRS `AWAITING_RECONCILIATION`, error code versioned, retry_allowed=false, action_required=OPERATOR_REVIEW. Không cooldown retry hoặc reanalyze.
12. `GET`/health/status chạy trên event loop riêng, phải trả trong lúc blocking worker chờ loopback. Pending state chỉ báo `INPUT_PROCESSING` khi receipt/worker còn active; hold/UNKNOWN không bao giờ trả 202 như gợi ý gửi lại.

### Crash/race matrix cho upload/attach/dispatch

| Sự kiện | Kết quả bền và API | Bảo đảm không lặp |
|---|---|---|
| Queue full trước Core/Story receipt | 503 `QUEUE_UNAVAILABLE`; không mutation/key use | Không có command để worker chạy |
| Part bị thiếu khi complete | 422 `UPLOAD_INCOMPLETE`; Core vẫn OPEN/RECEIVING, state_version không đổi, key không tiêu thụ | Client bổ sung part và complete lại cùng session |
| PUT part đua complete/abort | Row lock/CAS có một winner; loser reread state và nhận conflict, metadata không chèn sau transition | Staging object không tham chiếu bị sweeper xóa |
| Hai complete khác key | Chỉ một chuyển OPEN→VALIDATION_PENDING; request thứ hai 409 | Chỉ một validation dispatch |
| Cùng complete key còn PENDING | Chờ cùng dispatcher; nếu dispatcher mất, recovery chốt hold | Không enqueue bản thứ hai |
| Crash sau Core abort/expiry 202 | Tombstone + purge_state=PENDING; GET thể hiện abort/expired và cleanup pending | Startup/periodic sweeper tiếp tục purge idempotent |
| Crash sau PENDING trước queue ack | Recovery hold/quarantine; không tạo asset/provider | Key cũ replay hold; validation retry phải dùng key mới sau GET |
| Lock lost trước claim hoặc mark_sent | Epoch mismatch làm transition từ chối, readiness fail | 0 HTTP send |
| Lock lost sau SENT | Run hold/reconcile; attempt đó có thể kết thúc tối đa một lần, receipt immutable theo epoch | New process thấy SENT; không có attempt/send mới |
| Result receipt commit trước ledger finalize | Story result bền; finalize có thể UNKNOWN | Reconcile cùng tuple; ledger UNKNOWN không mutate |
| Stale epoch ghi run head | CAS không khớp, projection không đổi; immutable receipt vẫn audit được | Worker cũ không overwrite recovery |

### Hai hash kết quả không được gộp

- `transport_response_body_sha256`: SHA-256 của đúng raw HTTP response body; A1 transport đưa hash này vào InvocationGuard/Ledger field hiện có `result_sha256`.
- `canonical_result_sha256`: SHA-256 canonical JSON sau khi bridge/model validation hoàn tất; đây là hash result document/evidence và Story revision.
- `original_image_sha256` và `model_input_sha256` là hai hash khác của ảnh gốc và ảnh dẫn xuất thực gửi VLM.

Story receipt phải ghi tên/ý nghĩa/version của từng hash. Không so sánh raw HTTP body hash với canonical JSON hash như thể chúng cùng bytes. Nếu mapping/version không khớp, receipt không đủ điều kiện reconcile.

## 4. Contract API cụ thể cho UI

Đây là wire contract pilot; OpenAPI `StoryRunLite-v1` và schema test phải được tạo trong goal trước handoff UI. Giữ route SRS; Rev37 catalog tách riêng.

| Thao tác | Thành công | Contract chính |
|---|---:|---|
| POST /v1/story-runs | 201 Created | Body `run_ref`, SRS `state`, `revision`, `state_version`, `created_at`; Idempotency-Key bắt buộc. |
| POST /v1/upload-sessions | 201 Created | Body `upload_ref`, `state=RECEIVING`, `state_version`, `part_size_bytes=4194304`, `expires_at`; purpose + expected media/size/SHA bắt buộc; không storage URL/credential. |
| GET /v1/upload-sessions/{upload_id} | 200 OK | API state, `state_version`, `updated_at`, expiry, part counts, safe error, `purge_state`; ETag=quoted state_version; asset ref chỉ khi Core COMPLETED/CLEAN. |
| PUT /v1/upload-sessions/{upload_id}/parts/{part_no} | 200 OK | Raw bytes ≤4 MiB; `Content-SHA256`/`Content-Length` bắt buộc. Part number bắt đầu 1, không gap; exact retry idempotent; digest khác cùng part là 409. |
| POST /v1/upload-sessions/{upload_id}/complete | 202 Accepted | Expected aggregate bytes/SHA + Idempotency-Key. `Location` resource, `Retry-After: 2`; thiếu part trả 422 đồng bộ, không consume key. |
| DELETE /v1/upload-sessions/{upload_id} | 202 Accepted | Idempotency-Key + expected version (`If-Match`); durable ABORTED tombstone/purge_pending commit trước 202; GET poll purge state, cleanup resume sau crash. |
| POST /v1/story-runs/{id}/assets | 202 Accepted | Sau queue ack + FINAL receipt; body run ref/state/version; `Location` run, `Retry-After: 2`. |
| GET /v1/story-runs/{id} | 200 OK | SRS state/version, `updated_at`, `job_stage`, `retryable`, `action_required`, optional result only at SUBJECT_REVIEW, safe error; ETag/If-None-Match. Unknown outcome is SRS `AWAITING_RECONCILIATION`, retryable=false. |
| POST /v1/story-runs/{id}/subject-confirmation | 202 Accepted | SRS route/status. Body decision=CONFIRM + expected understanding revision; Idempotency-Key, Location + Retry-After. GET later shows PREPARATION_REVIEW. |

### Request/response contract tối thiểu

- Create run nhận đúng một `profile_ref` là server-seeded synthetic profile; cấm list children/profiles.
- Create upload nhận `purpose=RUN_ARTWORK` hoặc optional `RUN_ARTWORK_ORIGINAL`, `media_type`, `expected_size_bytes`, `expected_sha256`; optional original liên kết typed với model input. Trả opaque upload ref, part size và expiry.
- Upload part dùng request body bytes, path part number từ 1, Content-SHA256 và Content-Length; client không gửi storage key.
- Complete nhận aggregate byte count/hash + Idempotency-Key; response snapshot không đổi. GET upload resource là nguồn chuẩn cho tiến độ validation.
- Story attach nhận model-input asset ref, optional original ref và expected run revision; backend kiểm owner, CLEAN và hash chính xác bytes gửi VLM.
- Subject confirmation chỉ nhận CONFIRM, expected understanding revision và Idempotency-Key.
- Error envelope theo SRS: `{code, message, correlation_id, retryable, retry_after_seconds?, field_errors?}`; message an toàn, không echo bytes/key/token/signed URL/provider detail.
- Poll resource trả `state`, monotonically increasing `state_version`, `updated_at`, optional `job_stage`, `retryable`, `action_required`, `error`, `result`; ETag/If-None-Match hỗ trợ poll tiết kiệm; Retry-After là số giây khi có backpressure.
- `VISION_ATTEMPT_HOLD`, `PROVIDER_OUTCOME_UNKNOWN`, `SAFETY_SCANNER_UNAVAILABLE` là pilot extension codes được version trong OpenAPI `StoryRunLite-v1`; không thêm SRS run state. UNKNOWN dùng SRS `AWAITING_RECONCILIATION`.

### Status, errors và limits

- 400 `INVALID_REQUEST`/`INVALID_IDEMPOTENCY_KEY`; 404 `RESOURCE_NOT_FOUND` cùng shape cho absent/out-of-scope.
- 409 `STALE_REVISION`, `ACTIVE_RUN_EXISTS`, `INVALID_STATE_TRANSITION`, `UPLOAD_PART_CONFLICT`, `UPLOAD_SESSION_STATE_CONFLICT`; pilot `VISION_ATTEMPT_HOLD` có versioned extension.
- 410 `UPLOAD_SESSION_EXPIRED`; Core tombstone/receipt vẫn cho phép replay command response gốc.
- 413 `MEDIA_TOO_LARGE`; 415 `UNSUPPORTED_MEDIA_TYPE`; 422 `INVALID_FILE_CONTENT`, `IMAGE_DIMENSIONS_EXCEEDED`, `UPLOAD_INCOMPLETE`, `UPLOAD_CHECKSUM_MISMATCH`, `UPLOAD_CONTENT_MISMATCH`, `IMAGE_SAFETY_REJECTED`. Scanner unavailable/error/timeout remains a retryable upload resource state `QUARANTINED` with versioned `SAFETY_SCANNER_UNAVAILABLE`, never an attached asset or provider call.
- 429 `RATE_LIMITED` + Retry-After theo SRS §10.4: generic API 60/min/account; local unauthenticated IP 20/min; create run 2/min/account; upload create/complete/abort 10/min/account; chunk PUT 60/min/account và tối đa 40 MiB byte mới/min/account; tối đa 3 active upload sessions/account; status/list parts 30/min/session. Exact-digest chunk retry tính request nhưng không tính byte mới. Demo dùng một synthetic principal, không nới ngưỡng.
- 503 `QUEUE_UNAVAILABLE` + Retry-After khi bounded outstanding capacity=1 đang dùng; từ chối trước DB mutation/receipt/key use. Đây là command admission, khác rate limit.
- `GET /v1/story-runs/{id}` vẫn HTTP 200 cho run đã tạo. Result có sẵn trả SUBJECT_REVIEW; chưa có response V2 hợp lệ trả SRS `AWAITING_RECONCILIATION` + versioned code, `retryable=false`, action operator. Không dùng 202/503 để gợi ý resend.

## 5. Điều kiện acceptance cho goal sau M0

Goal gộp S1+S2 chỉ được mở sau owner approval riêng. Bắt buộc chứng minh:

- Sync A1 observation chạy trong single-thread executor ngoài FastAPI event loop: loopback giữ chậm vẫn cho GET/health trả đúng hạn; capacity=1 exhausted trả 503 trước receipt.
- `InvocationGuard` identity chính xác; optional hook/evidence kind giữ canvas default unchanged. Story sink chạy trước finalize; evidence loopback không bị gắn LIVE. Regression canvas + Story path.
- Fencing test mất advisory connection/process lease trước claim, giữa claim/SENT, ngay sau SENT: trước SENT zero send; sau SENT tối đa một invocation, process mới không resend; stale worker không update run head.
- Race test cùng session: PUT/complete/abort/expiry; hai complete khác key; same key PENDING; exact part retry/mismatched digest; missing/non-contiguous part returns 422, preserves RECEIVING and does not consume key; resume after process restart.
- Crash after abort/expiry 202 then restart: durable tombstone sweeper eventually deletes all known part/staging objects idempotently and marks PURGED; receipt replay still works.
- Core schema/DATA_TABLE_REGISTER amendment before migration: typed Parent owner scope, nullable legacy org mapping with constraints/backfill, validation_state/state_version/purge_state; exact persisted/API mapping tested; Core asset ref only at COMPLETED/CLEAN. PostgreSQL only on newly provisioned disposable DB with creation/cleanup proof; never A2 DB.
- Story command receipt same key/payload replays exact snapshot; different payload gets INVALID_IDEMPOTENCY_KEY; PENDING duplicate never dispatches twice; run/create concurrency and STALE_REVISION covered.
- Test verifies immutable result receipt durable before ledger finalize, distinct raw-body/canonical-result hashes, UNKNOWN reconcile without ledger mutation or resend.
- Image decoder test uses resource-limited subprocess for normalized and optional original assets; corrupt/decompression-bomb, timeout/kill and memory cap fail closed. Both exact digests must scan CLEAN before asset completion/Vision send; all other scanner outcomes give zero send.
- Model input limits are 5 MB/4 MP/4096 PNG/JPEG; optional original uses the same small-demo cap. FEAT-018 deviation vs SRS is explicit; no 12 MP support claim.
- OpenAPI StoryRunLite-v1 has every request/response/error schema above, SRS envelope, poll/version headers, SRS route/status including confirmation 202, §10.4 rate limits and examples. Contract tests + Bruno collection run after OpenAPI gates; no UI handoff before the gate.
- Fake/loopback tests block external network and verify no provider outside stub. Modal live readiness and owner approval are separate; fake success never proves Modal live.
- A2 remains paused; preserve all local work. PostgreSQL tests do not use/clean uncertain A2 database.
- Historical crosswalk covers every recorded V3/V4/V5/V6 finding. Exact archived reports are cited; unrecovered V4/V5 originals stay explicitly marked unavailable, with no fabricated finding IDs or claim of full archival closure.

## 6. Vẫn chờ owner chấp thuận

1. Demo chỉ CONFIRM; correction/rerun theo AT-14 vẫn ngoài scope.
2. FEAT-018 image policy và giới hạn nhỏ synthetic (cả original optional lẫn normalized ≤5 MB/4 MP/4096) là deviation SRS §24.2.
3. Photo binding riêng và additive `before_finalize`/evidence-kind hook trong shared A1 guard; canvas default không đổi.
4. Typed Parent Core Asset owner scope, DTR/SRS amendment, state/version/cleanup fields; không migration trước approval.
5. Worker executor, one outstanding permit, PostgreSQL process lock + worker epoch/fencing; không multi-process hoặc auto retry.
6. UUIDv4 run/public ref/ledger run ID; deterministic UUIDv5 job/attempt và technical namespace.
7. Durable Story result receipt before finalize; ledger UNKNOWN remains anti-resend barrier; reconcile cùng tuple.
8. Story/Core receipts không TTL trong pilot; production retention policy cần quyết định SRS riêng.
9. Async Core uploads dùng serialized row lock/CAS, resumable incomplete upload, durable abort/expiry purge.
10. Identity là một server-seeded synthetic actor trên loopback; không phải Parent authentication/BOLA proof.
11. A2 vẫn paused/unreviewed; mọi DB acceptance chỉ dùng disposable DB mới.

Review V7 phải xác nhận các quyết định này đủ cụ thể để viết goal. Không có approval triển khai nào được suy ra từ V7.

## 7. Crosswalk các finding review trước

### Nguồn và giới hạn traceability

- Review V3: report nguyên văn lưu tại `evidence/STORYRUN_LITE_VISION_M0_V3_INDEPENDENT_REVIEW_20261102.md`, Codex thread `01a19ace-ea77-7cd2-a630-ca55fdb2b5f7`, SHA-256 **47772B37E91A57C11ACD32664ADAEC511574B7685699FC9F118835E55D29FD4B**.
- Review V6: report nguyên văn lưu tại `evidence/STORYRUN_LITE_VISION_M0_V6_INDEPENDENT_REVIEW_20261102.md`, Codex thread `01a19b0d-5746-79e3-8dfa-81f622647d09`, SHA-256 **E80C77E1614093137744FFDBC84B03E61FE2F61AB86E710D0D991DD2EFD0ABC3**.
- Report gốc V4/V5 chưa tìm thấy trong checkout hoặc các thread Codex liên quan đã truy vấn. V4 draft hash **96D40096E7D57DFBBBF270D80AD7BE2C24555D69935156CBBEA5A648C170BC7E** và V5 draft hash **FE532FB2EEC71DAE4A407428C23A1F54267698C3B9CA8262C971F410F1590262** chỉ ghi tóm tắt kết quả/finding; các hàng V4/V5 dưới đây được khôi phục từ chúng và crosswalk V6, không phải report nguyên văn. Không tự tạo finding ID.

| Nguồn / mức | Finding được ghi nhận | Disposition V7 |
|---|---|---|
| V3 P1-1 | Story finalize trước khi payload bền có thể làm mất kết quả | Durable Story hook trước finalize; immutable result receipt, UNKNOWN reconcile — D3/D8/D9/§3/§5 |
| V3 P1-2 | Sweeper/reclaim CLAIMED có thể cho phép worker cũ gửi sau khi run thử lại | No reclaim/retry; worker epoch fenced claim/SENT; CAS result projection — D9/D12/D17/§3/§5 |
| V3 P1-3 | Cooldown không chứng minh invocation UNKNOWN đã dừng | Không retry theo thời gian; AWAITING_RECONCILIATION + operator/owner gate — D9/D11/§4/§6 |
| V3 P1-4 | Core Asset dùng org giả/source_refs sai Parent scope/lineage | Typed Parent owner scope, migration/backfill, lineage table chuẩn — D5/D18/§5/§6 |
| V3 P1-5 | Route list thiếu contract đủ để ghép UI | OpenAPI v1 schemas/status/errors/polling/idempotency/examples/rate limits — D10/§4/§5 |
| V3 P2-1 | Photo binding không được giả checkpoint hoặc phá canvas codec | Photo binding riêng, canvas semantics giữ nguyên — D3/§5 |
| V3 P2-2 | narration_context không thực hiện subject correction theo SRS | Correction/rerun vẫn ngoài scope, deviation rõ — D1/§6 |
| V3 P2-3 | Admission/normalization khác SRS, error mapping chưa đủ | Deviation FEAT-018 công khai, byte/pixel limits, decoder resource isolation, explicit errors — D4/§4/§5 |
| V3 P2-4 | X-Actor-Ref không phải authorization | Server-seeded synthetic identity + loopback only — D2/§6 |
| V4 P1-1 | Result recovery/finalize order và raw-vs-canonical hash | Hook before finalize; two hashes have separate names/semantics — D3/D8/§3 |
| V4 P1-2 | Invocation tuple không ổn định khi hoãn AiJobService | UUIDv4 public/run/ledger + UUIDv5 deterministic job/attempt — D6/D7/§5 |
| V4 P2-1 | OpenAPI chưa chốt frontend behavior | Wire contract v1 and request/response examples/gates — D10/§4/§5 |
| V4 P2-2 | Photo adapter chưa chỉ đường vào A1 | Story photo adapter uses same guard/transport; no legacy image ref/canvas path — D3/§5 |
| V5 P1 | Thiếu durable receipt/public idempotent reference | Story/Core receipts, public run UUID, replay contract — D6/D14/D16/§3/§4 |
| V5 P2-1 | 202 handoff/recovery và AV CLEAN gate chưa đủ ràng buộc | Reserve→PENDING→ack→FINAL→gate; hash cụ thể phải CLEAN; crash/race matrix — D4/D12/D14/D15/D18/§3/§5 |
| V5 P2-2 | Error/status/polling choices open | Exact SRS state/status/error envelope and versioned extensions — D10/§4 |
| V5 P3 | Review traceability absent | V3/V6 exact reports archived; V4/V5 originals explicitly unavailable and reconstruction labeled — §7 (archive limitation remains explicit) |
| V6 P1-1 | Sync worker blocks polling/event loop | Dedicated executor, max outstanding=1, slow-loopback GET acceptance — D12/§4/§5 |
| V6 P1-2 | Core concurrent part/complete/abort and PENDING replay race | Single session row lock/CAS/version; one transition/dispatcher — D16/D18/§3/§5 |
| V6 P2-1 | Lock loss does not fence old worker/result write | Monotonic epoch checked atomically at claim/SENT; result-head CAS; reconcile immutable receipt — D17/§3/§5 |
| V6 P2-2 | Incomplete upload can become terminal/non-resumable | 422 before key use; remain OPEN/RECEIVING; continuity/resume tests — D18/§4/§5 |
| V6 P2-3 | Abort/expiry purge lost after 202/crash | Durable tombstone + startup/periodic idempotent sweeper — D18/§3/§4/§5 |
| V6 P2-4 | Parent owner/schema and READY-vs-COMPLETED mismatch | Typed scope migration; persisted/API status mapping in D5/D16 and DTR gate — §4/§5/§6 |
| V6 P2-5 | A1 decorator mislabels StoryPhoto evidence | Optional server-controlled evidence kind, default canvas remains legacy; regression — D3/§5 |
| V6 P2-6 | Decoder acceptance overclaims decompression protection | Process-isolated bounded decode, hard kill/resource caps for both assets — D4/§5 |
| V6 P2-7 | API deviates from SRS and omits envelope/poll/rate schemas | Confirmation 202, error envelope, state version/stage, SRS §10.4 limits — D10/§4/§5 |
| V6 P2-8 | Core receipt expires before idempotent replay contract | No receipt TTL in pilot; storage cleanup does not delete replay tombstones — D14/D16/D18 |
| V6 P2-9 | Crosswalk counted only four of five V3 P1 | V3’s five P1 findings are split into five explicit rows — §7 |
| V6 P3 | Historical V4/V5 reports missing | Exact V3/V6 archived; V4/V5 originals remain unavailable and are never represented as exact sources — §7; seek source before claiming full archive closure |

## 8. Ngoài phạm vi

- Không sửa/đóng A2, B1, B2 canvas; không sửa SRS/Data Table Register trong lúc soạn M0.
- Không triển khai code, không chạy test, không truy cập PostgreSQL, không gọi Modal/GPU/provider/mạng ngoài.
- Không stage/commit/push/merge, không sửa approval record.
- Không triển khai UI, Teacher auth/assignment thật, story/storyboard, ASR, video/TTS, billing/quota production, consent dữ liệu thật hoặc orchestration đa stage.
- Không tuyên bố M0 đã được owner chấp nhận, goal đã được duyệt, hay A1 đã chạy Modal thật.
