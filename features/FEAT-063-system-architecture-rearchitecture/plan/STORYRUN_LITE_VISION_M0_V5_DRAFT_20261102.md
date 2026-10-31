# M0 V5 — Đề xuất chốt StoryRun-lite Vision cho BE demo

Ngày: 2026-11-02. Trạng thái: **DRAFT / CHỜ OWNER DUYỆT / CHỜ REVIEW ĐỘC LẬP**. Đây là đề xuất kiến trúc và contract, không phải approval triển khai. Không được coi các lựa chọn bên dưới là owner đã duyệt.

V5 giữ nguyên V2, V3 và V4. Nó xử lý bốn finding còn lại từ review độc lập V4: reconcile kết quả khi ledger là UNKNOWN; ID invocation A1 ổn định; contract trạng thái/API đủ cho UI; adapter ảnh dẫn xuất riêng.

## 1. Mục tiêu, ranh giới và baseline

Mục tiêu đề xuất là một flow BE demo Parent, chỉ dùng dữ liệu tổng hợp: tạo một run → nhận ảnh tranh giấy → validate và chuẩn hóa ảnh → gọi Vision đúng một lần → API cho frontend đọc trạng thái/kết quả → người lớn xác nhận chủ thể. Bruno và OpenAPI dùng để kiểm tra/ghép API; UI do người khác phụ trách.

Goal gộp S1+S2 chỉ được viết sau khi owner chấp nhận M0 và có plan cùng approval riêng. Goal dùng fake/loopback để chứng minh API, persistence, guard, recovery và contract. Gọi Modal thật là cổng riêng, chỉ sau review readiness và approval live.

Baseline:

- M0 V4: SHA-256 **96D40096E7D57DFBBBF270D80AD7BE2C24555D69935156CBBEA5A648C170BC7E**; review độc lập kết luận CHƯA ACCEPTED, 2 P1 và 2 P2.
- M0 V3: SHA-256 **2223310837BD1B42757CE818BF932FF5F98D1AE9EB7FB5552904F3AF9A51FCEE**.
- M0 V2: SHA-256 **06346124F6851DD401148CE25EC2541B29C2738E0D67A77FE3258666F81CB71B**.
- HEAD: **a88de875ff92e9b4d4fa5cc2f5f8d5fc1f626f58**, nhánh **feature/feat063-be-foundation**.
- Working tree có A2 review-fix và thay đổi khác chưa commit. V5 chỉ là file mới; không sửa/dọn/commit A2. Future goal dùng worktree/snapshot riêng ghim HEAD để tách baseline.
- A2 pause report ghi PostgreSQL cleanup teardown lỗi FK; database cục bộ có thể còn synthetic rows. Không dùng/dọn database đó. Test PostgreSQL chỉ trên disposable database mới, tạo và xóa có kiểm chứng.
- SRS FEAT-063 v2.3 và DATA_TABLE_REGISTER là draft. Rev37 vẫn là catalog baseline; operation pilot được đếm riêng.
- FEAT-061 smoke chứng minh đường demo Modal cũ với ảnh synthetic, không chứng minh A1 guard/ledger/transport chạy với Modal thật.

## 2. Các lựa chọn owner đề xuất

Mọi D dưới đây vẫn **CHỜ OWNER**. Bản nháp không tự duyệt deviation hoặc migration.

| ID | Đề xuất | Giới hạn/trách nhiệm |
|---|---|---|
| D1 — Scope | Parent synthetic; một run, một ảnh, một Vision attempt; trả chủ thể đề xuất/độ không chắc chắn và cho người lớn xác nhận. Chưa hỗ trợ correction/rerun, Teacher auth/assignment thật, story/video/audio, quota production hay UI. | Ghi deviation với SRS AT-14: correction không được thực hiện trong demo. Không tuyên bố AT-14 hoàn tất. |
| D2 — Identity | Một actor/profile synthetic cố định do server cấu hình; chỉ local/test, synthetic gate bật, API bind loopback. Không nhận X-Actor-Ref hoặc owner ID để phân quyền. | Đây không phải Parent Authentication, BOLA protection hay authorization cho dữ liệu thật. Startup fail-closed ngoài chế độ demo. |
| D3 — Binding ảnh | Thêm PhotoInputV1/StoryPhotoBindingV1 và StoryPhotoVisionAdapterV1. Không giả RenderBinding/CheckpointBinding, không đổi payload codec canvas. Adapter đọc đúng asset đã normalize, kiểm hash, dựng VLM request từ byte ảnh dẫn xuất và gửi qua A1 HttpJsonTransport + InvocationGuard. | Không truyền processing_image_ref vào legacy_v2: bridge hiện tại từ chối trường này. Không khẳng định đang tái dùng toàn bộ legacy bridge. Giữ adapter/call sites canvas hiện tại nguyên vẹn; nếu cần extension shared guard phải nằm trong allowlist và có A1 regression. |
| D4 — Admission | Để giữ demo hẹp, dùng đúng policy FEAT-018 hiện có cho bytes normalized gửi Vision: PNG/JPEG, tối đa 5.000.000 byte, 4 MP và cạnh dài 4096; không thêm WebP hay server-side normalization trong mốc này. Client/Bruno gửi image đã chuẩn hóa theo normalization_policy hiện có; có thể kèm source_image gốc tối đa 15.000.000 byte. | Đây là deviation tạm của demo so với SRS §24.2 (20 MiB/40 MP/WebP/server normalization). Contract phải công khai giới hạn và yêu cầu normalize phía client. Không tuyên bố ảnh điện thoại 12 MP được hỗ trợ trực tiếp; mở rộng sau demo cần quyết định và test riêng. |
| D5 — Asset/scope | Asset Parent gắn owner_scope_kind/ref = PARENT_ACCOUNT; original và derived là hai asset riêng, lineage mới ghi qua core.asset_lineage; không ghi lineage mới trong source_refs. Dùng adapter lưu byte local/private chỉ trong local demo. | Không tạo organization giả, không chọn storage production. Migration/Core metadata phải được ghi trong plan/approval của goal. |
| D6 — Identity invocation | story.runs dùng internal story_run_id là UUID ổn định; public story_run_ref là opaque API ref được server ánh xạ. Ledger run_id dùng internal UUID, không dùng chuỗi public tùy ý. | Guard A1 parse run_id bằng UUID và yêu cầu đủ job_id, attempt_id, organization_id. |
| D7 — Job/attempt và ledger namespace | Vì demo chỉ có stage VISION_SUBJECT_V1 và đúng một attempt/run, đề xuất job_id = UUIDv5(NAMESPACE_URL, “sketch2life:story-vision:v1:{story_run_id}:job”), attempt_id = UUIDv5(NAMESPACE_URL, “sketch2life:story-vision:v1:{story_run_id}:attempt:1”). organization_id của ledger dùng hằng kỹ thuật “storyrun-lite-parent-demo-v1”; đây chỉ là namespace khóa/phân vùng invocation, không phải Parent scope, không tạo organization row và không cấp quyền. | Tuple/derivation version được lưu hoặc suy ra ổn định từ StoryRun UUID; exact replay/restart phải tạo lại đúng tuple. Invocation ledger hiện dùng String cho các ID và organization_id, không có FK trên invocation. Nếu code/schema/runtime thực tế có ràng buộc khác, dừng trước provider call và xin owner chọn mapping; không tạo organization giả. |
| D8 — Kết quả bền vững | Story understanding revision là nguồn chuẩn cho kết quả UI. Ghi các trường structured result hiện có cùng invocation receipt trong một Story UoW trước khi finalize ledger SUCCEEDED; cùng transaction cập nhật story.runs.current_understanding_revision_ref và state=SUBJECT_REVIEW. Đề xuất bổ sung vào story.understanding_revisions: invocation_job_id, invocation_attempt_id, transport_response_body_sha256, canonical_result_sha256 và result_contract_version; unique theo job/attempt. StoryRun ID suy ra qua run_input_id và là UUID ledger.run_id. | Cần cập nhật DATA_TABLE_REGISTER trước migration; không tạo job projection thứ hai. Cần optional durable-result sink/hook trong đường Story invocation nằm trước finalize; path canvas cũ giữ default behavior. Sink phải idempotent theo attempt tuple. |
| D9 — UNKNOWN và reconcile | Ledger là hàng rào chống gửi trùng, không phải nguồn duy nhất để đọc kết quả Story. Nếu receipt/revision đã bền vững nhưng guard trả PROVIDER_OUTCOME_UNKNOWN hoặc ledger đã UNKNOWN, Story GET vẫn trả revision đã lưu ở SUBJECT_REVIEW; ledger UNKNOWN được giữ nguyên và khóa mọi lần gửi tiếp. Reconciler cập nhật/đọc projection Story từ receipt, không cố chuyển ledger UNKNOWN→SUCCEEDED. Nếu không có receipt/revision và ledger là CLAIMED/SENT/UNKNOWN, API trả hold/INPUT_REVIEW với retry_allowed=false và action_required=OPERATOR_REVIEW; tuyệt đối không redispatch. | Một thời điểm có thể có Story result sẵn sàng nhưng ledger UNKNOWN. API phân biệt rõ hai nguồn trạng thái; không báo “provider outcome unknown” cho người dùng khi Story có response hợp lệ đã lưu. Mọi tình huống UNKNOWN không được retry tự động hoặc bằng cooldown. |
| D10 — API/OpenAPI | Giữ route SRS: story-runs, assets, subject-confirmation; không dùng /drawing hay /subject-review. OpenAPI pilot versioned và contract test là điều kiện trước handoff UI. | Quy định cụ thể DTO, status, state, error, polling, idempotency và ví dụ ở mục 4. Rev37 catalog không bị âm thầm đổi. |
| D11 — AiJobService | Hoãn full AiJobService/outbox/multi-stage retry cho demo một bước. StoryRun/revision giữ nghiệp vụ; invocation ledger giữ trạng thái gửi. Không có endpoint reanalyze. | Process crash có thể để run ở hold/input review, cần owner xử lý; không tự dispatch lại. Đây là nợ demo, không phải lifecycle production. |
| D12 — Worker topology | Enforce đúng một backend process và một worker bằng exclusive process lock; startup fail nếu lock đã có chủ hoặc cấu hình nhiều worker/replica. Lưu worker_instance_id với attempt. Trong process đang giữ lock, attempt đang chạy hiển thị INPUT_PROCESSING. Khi process mới giữ được lock, mọi CLAIMED/SENT chưa có Story result từ instance cũ được chiếu thành INPUT_REVIEW/hold; không sửa trạng thái ledger và không dispatch lại. | Một attempt đã claim không được release/reclaim bằng tuổi hoặc thiếu heartbeat. Cùng run không mở attempt thứ hai; request đồng thời nhận cùng resource hoặc 409. Test phải chứng minh process thứ hai fail-closed và startup sau crash không gửi lại. |
| D13 — Test baseline | Dùng worktree/snapshot riêng ghim HEAD; PostgreSQL chỉ trên disposable DB mới, cleanup được chứng minh. | Không dùng/dọn DB A2 hoặc BE1 cục bộ chưa xác định sạch. |

## 3. Luồng invocation và phục hồi bắt buộc

1. Tạo StoryRun nội bộ UUID cùng input revision; server trả public opaque ref. ID invocation cho stage VISION_SUBJECT_V1 được xác định ổn định trước lần gửi đầu. Cùng idempotency key và fingerprint không sinh run/tuple mới.
2. Upload session kiểm bytes/hash/media theo FEAT-018. Nếu có source_image, backend giữ original bytes đó; image là bytes normalized từ client. Nếu không có source_image, image là cả original lẫn model input theo IDENTITY_V1. Lưu mỗi asset/hash và normalization_policy, nối original → normalized bằng lineage. StoryPhotoVisionAdapter chỉ đọc image đã READY, xác minh owner PARENT_ACCOUNT và kiểm hash đúng receipt.
3. Guard claim tuple; ledger CLAIMED phải bền trước khi tiếp tục. Ghi SENT bền trước ranh giới gửi HTTP. Chỉ một attempt/run; không có stale reclaim hay reanalyze.
4. Khi adapter nhận response hợp lệ, nó đưa outcome đã validate tới durable-result sink trước bước guard finalize. Sink ghi các trường structured result hiện có của story.understanding_revisions cùng invocation_job_id, invocation_attempt_id, transport_response_body_sha256, canonical_result_sha256 và result_contract_version; cùng transaction cập nhật story.runs.current_understanding_revision_ref/state=SUBJECT_REVIEW. run_input_id nối revision tới StoryRun UUID, không tạo FK chéo module. Nếu sink không ghi được, không được coi Story/ledger là thành công và không gửi lại provider.
5. Sau khi Story result đã đọc lại được, guard finalize ledger. Nếu finalize thành công, StoryRun chuyển SUBJECT_REVIEW. Nếu finalize trả UNKNOWN nhưng receipt tồn tại, application tra receipt theo cùng attempt tuple, giữ nguyên ledger state, trả Story result ở SUBJECT_REVIEW và không tạo invocation khác. Đây là reconcile Story projection, không phải đổi ledger UNKNOWN thành SUCCEEDED.
6. Nếu worker hiện tại còn hoạt động, Story GET trả INPUT_PROCESSING, không cho retry và có thể trả Retry-After=2. Nếu không có Story receipt/revision và attempt không còn active trong process giữ exclusive lock (bao gồm attempt mồ côi phát hiện khi startup), GET trả INPUT_REVIEW với code an toàn phù hợp, retry_allowed=false và action_required=OPERATOR_REVIEW. Không có attempt mới cạnh tranh; ledger không bị reset.
7. Nếu phát hiện ledger SUCCEEDED nhưng không tìm thấy Story result receipt, đây là invariant breach: API không trả thành công, run bị hold, không gọi lại provider và cần owner xử lý.

### Hai hash kết quả không được gộp

- transport_response_body_sha256: SHA-256 của đúng raw HTTP response body; A1 transport đưa hash này vào InvocationGuard/Ledger field hiện có result_sha256.
- canonical_result_sha256: SHA-256 của canonical JSON result sau khi bridge/model validation hoàn tất; đây là hash result document/evidence và Story revision.
- original_image_sha256 và model_input_sha256 là hai hash khác của ảnh gốc và ảnh dẫn xuất thực gửi VLM.

Story receipt phải ghi tên/ý nghĩa/version của từng hash. Không so sánh raw HTTP body hash với canonical JSON hash như thể chúng cùng bytes. Nếu mapping/version không khớp, receipt không đủ điều kiện reconcile.

## 4. Contract API cụ thể cho UI

Đây là contract pilot đề xuất để owner/reviewer duyệt; OpenAPI thực tế vẫn phải được sinh và contract-test trong goal.

| Thao tác | Thành công | Response/ý nghĩa |
|---|---:|---|
| POST /v1/story-runs | 201 Created | Trả run_ref, state=DRAFT, revision/version. Idempotency-Key bắt buộc. |
| POST /v1/upload-sessions | 201 Created | Trả upload_ref/progress/expiry; không có storage URL/credential. |
| GET /v1/upload-sessions/{upload_id} | 200 OK | Trạng thái và phần đã nhận; chỉ actor/scope server-resolved sở hữu mới đọc được. |
| PUT /v1/upload-sessions/{upload_id}/parts/{part_no} | 200 OK | Exact same part/hash retry idempotent; part cùng index khác hash trả 409. |
| POST /v1/upload-sessions/{upload_id}/complete | 202 Accepted | Bắt đầu final validation; Location trỏ upload resource; trả Retry-After khi còn xử lý. |
| POST /v1/story-runs/{id}/assets | 202 Accepted | Gắn asset READY cùng owner scope và bắt đầu Vision; Location=/v1/story-runs/{id}, Retry-After=2. |
| GET /v1/story-runs/{id} | 200 OK | Luôn trả resource hiện hành. Attempt còn active trong process đang giữ lock: state=INPUT_PROCESSING, Retry-After=2, retry_allowed=false. Có revision bền vững: state=SUBJECT_REVIEW và result, kể cả khi ledger UNKNOWN. Không có result và attempt CLAIMED/SENT/UNKNOWN đã orphan/terminal: state=INPUT_REVIEW, error.code=VISION_ATTEMPT_HOLD hoặc PROVIDER_OUTCOME_UNKNOWN, retry_allowed=false, action_required=OPERATOR_REVIEW. |
| POST /v1/story-runs/{id}/subject-confirmation | 200 OK | Chỉ decision=CONFIRM, expected_understanding_revision bắt buộc, Idempotency-Key; trả review receipt/state=PREPARATION_REVIEW. Correction/rerun không nằm trong pilot. |

Error/status tối thiểu:

- 400 VALIDATION_ERROR cho JSON/field sai.
- 404 RUN_NOT_FOUND cho resource không tồn tại hoặc không thuộc scope; không tiết lộ resource chéo owner.
- 409 IDEMPOTENCY_CONFLICT, REVISION_CONFLICT hoặc ATTEMPT_ALREADY_CLAIMED; body có safe code/version.
- 413 IMAGE_TOO_LARGE; 415 UNSUPPORTED_MEDIA_TYPE; 422 IMAGE_RECAPTURE chỉ khi lỗi thực sự do ảnh cần chụp lại.
- 429 RATE_LIMITED.
- Khi provider result mơ hồ, GET run vẫn là 200 resource với INPUT_REVIEW và retry_allowed=false; không dùng 202/503 để ám chỉ client nên retry.

Idempotency scope là server-resolved actor scope + method/operation + key. Fingerprint canonical hóa request body và gồm ref/version/hash asset hoặc expected revision tương ứng. Cùng key/cùng fingerprint replay resource/kết quả cũ; cùng key/khác fingerprint trả 409. Upload part exact retry dùng part number + content SHA-256.

## 5. Điều kiện acceptance cho goal sau M0

Goal S1+S2 sau khi được duyệt cần chứng minh tối thiểu:

- Story photo adapter gửi đúng model_input_sha256 qua A1 HttpJsonTransport/InvocationGuard; request trước ranh giới SENT hoặc mọi guard/admission/scope/ledger denial không gửi HTTP.
- Không thay đổi canvas RenderBinding/CheckpointBinding/codec semantics; regression A1 canvas chạy với default sink.
- Hai request đồng thời cùng run tạo tối đa một provider send; process topology >1 bị từ chối hoặc bị cấu hình không thể chạy.
- Fault injection ở các điểm: provider trả hợp lệ trước Story write; Story write xong trước ledger finalize; finalize thành UNKNOWN; restart sau SENT; result receipt thiếu/không đọc được. Không có ca nào tự gọi lại.
- Nếu receipt có sẵn nhưng ledger UNKNOWN, GET trả đúng Story result, không mutate ledger và không gửi thêm. Nếu receipt thiếu, GET trả đúng hold/error với retry_allowed=false.
- Unit/integration tests kiểm tuple UUID ổn định qua replay/restart; không tạo ID mới và không gắn owner scope Parent vào ledger organization namespace.
- OpenAPI method/path/schema/status/error và ví dụ khớp app; test idempotency cùng key/cùng fingerprint và key khác fingerprint.
- Test ảnh synthetic theo FEAT-018: giới hạn 5.000.000 byte/4 MP/cạnh 4096, PNG/JPEG, source_image tối đa 15.000.000 byte và từng normalization_policy; kiểm corrupt/decompression limit, original-vs-normalized lineage và exact model_input_sha256. Mọi admission fail phải zero provider send.
- PostgreSQL (nếu cần) chỉ ở disposable DB mới; không truy cập/dọn DB A2.
- Fake/loopback không được tuyên bố là bằng chứng Modal thật. Goal dừng XONG-CHƯA REVIEW; live Modal chỉ mở ở approval riêng.

## 6. Vẫn chờ owner chấp thuận

1. Demo chỉ CONFIRM, chưa correction/rerun theo AT-14.
2. Demo dùng policy FEAT-018 và client-side normalization thay vì SRS §24.2 đề xuất 20 MiB/40 MP/WebP/server normalization; client phải tuân giới hạn 5 MB/4 MP/4096; không tuyên bố nhận trực tiếp ảnh điện thoại 12 MP.
3. ID tuple UUIDv5 cố định và technical ledger namespace nêu ở D6–D7; namespace đó không đại diện organization/Parent.
4. Durable result sink trước finalize, Story là nguồn chuẩn nội dung; ledger UNKNOWN được giữ làm anti-resend barrier dù API có thể đọc result từ receipt.
5. Hoãn AiJobService, một process duy nhất, không tự retry UNKNOWN; lỗi mơ hồ có thể cần operator xử lý.
6. Dùng local/private artifact adapter và disposable PostgreSQL riêng cho synthetic demo; chưa chọn storage production.

Review độc lập V5 phải kiểm tra các quyết định này với mã hiện tại và chỉ ra nếu còn blocker. Sau review, owner mới duyệt/revise M0 và mở goal S1+S2.

## 7. Ngoài phạm vi

- Không sửa/đóng A2, B1, B2 canvas; không sửa SRS/Data Table Register trong lúc soạn M0.
- Không triển khai code, không chạy test, không truy cập PostgreSQL, không gọi Modal/GPU/provider/mạng ngoài.
- Không stage/commit/push/merge, không sửa approval record.
- Không triển khai UI, Teacher auth/assignment thật, story/storyboard, ASR, video/TTS, billing/quota production, consent dữ liệu thật hoặc orchestration đa stage.
- Không tuyên bố M0 đã được owner chấp nhận, goal đã được duyệt, hay A1 đã chạy Modal thật.
