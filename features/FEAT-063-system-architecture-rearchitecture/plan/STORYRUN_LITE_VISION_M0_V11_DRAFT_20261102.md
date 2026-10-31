# M0 V11 — Đề xuất StoryRun-lite Vision cho BE demo

Ngày: 2026-11-02. Trạng thái: **DRAFT / CHỜ OWNER DUYỆT / CHỜ REVIEW ĐỘC LẬP**. V11 cập nhật các hướng đề xuất Q1–Q5 từ phần tư vấn trước; chưa phải lựa chọn hay phê duyệt của owner. Mục tiêu: BE demo Parent bằng dữ liệu synthetic, API kiểm qua Bruno/OpenAPI, rồi mới mở cổng gọi Modal thật; UI do người khác làm.

Nguồn trực tiếp: M0 V10 SHA-256 DB0024A4A489BE1CD7413544DF6D20BE6E78312E4C47687994624707A4F78594; file handling đúng trong repo là evidence/STORYRUN_LITE_VISION_M0_V10_FINDINGS_HANDLING_20261102.md, SHA-256 A25C1409868022373614023194989B571163F6041DD61BD434E42C71D6740F40. Tên file trong prompt V11 thiếu chữ FINDINGS, hash ghim khớp file có tên trên. Không sửa V1–V10, SRS, DATA_TABLE_REGISTER, approval, code hay baseline A2. A2 vẫn TẠM DỪNG. Không tạo goal, migration, commit/stage/push/merge, gọi Modal/provider, dò dịch vụ/cổng, đọc hay dùng database.

**Điều chỉnh bắt buộc sau tự kiểm chứng:** decoder FEAT-018 chạy PyAV trong process; không có subprocess timeout 3 giây hoặc hard memory cap. V11 không tuyên bố các bảo đảm đó. Demo chỉ nhận đúng fixture synthetic có SHA-256 ghim ở server trước decoder; bytes không khớp bị chặn trước decode. Ảnh tùy ý cần decoder process có thể kill và OS resource limit đã kiểm chứng trước.

## 1. Mục tiêu, ranh giới và baseline

Mục tiêu đề xuất là một flow BE demo Parent, chỉ dùng dữ liệu tổng hợp: tạo một run → nhận ảnh tranh giấy → validate và chuẩn hóa ảnh → gọi Vision đúng một lần → API cho frontend đọc trạng thái/kết quả → người lớn xác nhận chủ thể. Bruno và OpenAPI dùng để kiểm tra/ghép API; UI do người khác phụ trách.

Goal gộp S1+S2 chỉ được viết sau khi owner chấp nhận M0 và có plan cùng approval riêng. Goal dùng fake/loopback để chứng minh API, persistence, guard, recovery và contract. Gọi Modal thật là cổng riêng, chỉ sau review readiness và approval live.

Baseline:

- M0 V7: SHA-256 **23EF3BBB5E8E51BA27221091C5AC16D42B8B87F3FB9DBEE975E6955F90346EA7**; review độc lập NEEDS_REVISION (1 P1, 3 P2, 1 P3), report nguyên văn tại `evidence/STORYRUN_LITE_VISION_M0_V7_INDEPENDENT_REVIEW_20261102.md`, SHA-256 **FBB06C848CF3E2EF41FB7037A7F5CCBFD45E7D3A730C00A76407BC1B1BCB24B8**.
- M0 V8: SHA-256 **75F7C0312E7683EA24BBC079BECF7FC7CF364F107B3AE89552F5546C5DE6A0D3**; review độc lập NEEDS_REVISION (4 P2, không P0/P1), report nguyên văn tại `evidence/STORYRUN_LITE_VISION_M0_V8_INDEPENDENT_REVIEW_20261102.md`, SHA-256 **B88F014CBF34DBAE879DE63BA2E6D15254BB10F99BDBC8E799BFD4BC5AFF5A8E**.
- M0 V9: hash được prompt V10 ghim **F922C7AEBFBA5A6DACAC5315952C33B94A1B06097719C9B50A7485A83CA5979C**; hash hiện tính từ file **C2364A72D4C8E11EDFEE015C2E4F6C2B40F5813A1230EC4265EC363890FD6C9D**. V10 dùng bytes hiện tại để đối chiếu, nêu mismatch thay vì sửa V9. V9 chưa được review độc lập chấp nhận.
- M0 V5: SHA-256 **FE532FB2EEC71DAE4A407428C23A1F54267698C3B9CA8262C971F410F1590262**; review độc lập kết luận CHƯA ACCEPTED, 1 P1, 2 P2 và 1 P3.
- M0 V6: SHA-256 **8240A3FA208C9B41D157A5254F520CD3E9F460DAC13DFE82D21E33911E573018**; review V6 kết luận NEEDS_REVISION (2 P1, 9 P2, 1 P3), report nguyên văn tại `evidence/STORYRUN_LITE_VISION_M0_V6_INDEPENDENT_REVIEW_20261102.md`, SHA-256 **E80C77E1614093137744FFDBC84B03E61FE2F61AB86E710D0D991DD2EFD0ABC3**.
- M0 V4: SHA-256 **96D40096E7D57DFBBBF270D80AD7BE2C24555D69935156CBBEA5A648C170BC7E**; review độc lập kết luận CHƯA ACCEPTED, 2 P1 và 2 P2.
- M0 V3: SHA-256 **2223310837BD1B42757CE818BF932FF5F98D1AE9EB7FB5552904F3AF9A51FCEE**.
- M0 V2: SHA-256 **06346124F6851DD401148CE25EC2541B29C2738E0D67A77FE3258666F81CB71B**.
- HEAD: **a88de875ff92e9b4d4fa5cc2f5f8d5fc1f626f58**, nhánh **feature/feat063-be-foundation**.
- Working tree có nhiều thay đổi A2 chưa commit cùng các draft M0/roadmap local. Giữ nguyên các thay đổi có sẵn; V10 là draft mới, không cập nhật status/approval hay source implementation. Goal tương lai dùng worktree/snapshot riêng ghim HEAD để tách baseline.
- A2 pause report ghi PostgreSQL cleanup teardown lỗi FK; database cục bộ có thể còn synthetic rows. Không dùng/dọn database đó. Test PostgreSQL chỉ trên disposable database mới, tạo và xóa có kiểm chứng.
- SRS FEAT-063 v2.3 và DATA_TABLE_REGISTER là draft. DTR §14.1 là baseline v2.3 trước Rev31; §14.4 là crosswalk hiện hành sau Rev31. Sau bổ sung hai receipt, số mục tiêu hai lớp là baseline **53 new / 91 active / 139 physical** và crosswalk Rev31 **56 new / 94 active / 142 physical**. Source-declared mapping hiện tại vẫn 89 cho tới khi triển khai; operation pilot Rev37 được đếm riêng.
- FEAT-061 smoke chứng minh đường demo Modal cũ với ảnh synthetic, không chứng minh A1 guard/ledger/transport chạy với Modal thật.

### 1.1 Bằng chứng Modal/Vision theo mức

| Khẳng định | Nguồn được ghi nhận | Mức chứng cứ / điều được phép kết luận |
|---|---|---|
| Vision V2 qua app Modal chạy được ngày 29/10 (backend `demo_main` trên `dev`, ảnh crayon, một lần gọi) | FEAT-061 `BACKEND_DEMO_MODAL_SMOKE_20261029.md`, kết quả thô và `MODAL_HISTORY_METRICS_20261029.md` | Có báo cáo và dữ liệu thô trong repo; lượt lập V10 này không mở lại từng file thô. Không chứng minh StoryRun hoặc A1 transport/guard/ledger. |
| 01/11: nóng 200 `SUCCEEDED` 2,9 s, “mặt trời” 0,99; cold 120,6 s bị ngắt; nạp 4 shard 47 s; app dừng 17:07 | `SESSION_LOG_20261101.md`, bàn giao và V1–V4 | Chỉ là tự thuật của Claude từ cùng một nguồn. `serve.log`/thư mục chạy đã bị xóa; còn script `be_modal_smoke.py`. Không xác minh độc lập offline; 120 s khớp client timeout 120 s nhưng nguyên nhân “model chưa nạp” chưa chứng minh. |
| Đường gọi ngày 01/11 | `be_modal_smoke.py` | `create_app()` + `UrllibJsonTransport` + `LightningVisionV2Adapter`, route demo `/v1/sessions/{id}/understanding`, ảnh fixture synthetic nhỏ. Không đi qua A1 guard/ledger/transport. |
| `/health` | `deployment/modal/qwen_vision_v2.py` và A1 transport chỉ gửi POST | Kiểm tra riêng: chỉ xác nhận app trả lời; không chứng minh model đã nạp, token hợp lệ, hoặc A1 live hoạt động. |
| A1 transport/guard/ledger/bridge đã gọi Modal thật | Chưa có bằng chứng; A1 chỉ có stub loopback theo hồ sơ hiện có | Chưa từng được chứng minh. Lần gọi thật chỉ sau review readiness và owner approval riêng. |

### 1.2 Phân loại phạm vi

| Phân loại | Nội dung đề xuất | Ghi chú |
|---|---|---|
| Bắt buộc cho demo BE | Một Parent/run/ảnh synthetic; contract API/OpenAPI; intake + admission; một Vision attempt có receipt/revision bền; GET status/result; người lớn CONFIRM; Bruno flow; không auto-resend khi UNKNOWN; có đường an toàn để giải phóng run/active lock trước run tiếp theo. | Q2 phải được owner chọn trước goal; UI không thuộc phần triển khai của owner. |
| Hoàn thiện sau theo SRS | Authentication thật/BOLA đầy đủ, Teacher/assignment, subject correction + rerun, full AiJobService/outbox/retry lifecycle, upload resume đầy đủ, cancellation/purge lifecycle, production observability/retention/quota, UI. | Không được mô tả như đã hoàn tất trong demo. |
| Độ lệch SRS còn mở | 5 MB/4 MP/4096 PNG/JPEG thay cho §24.2 20 MiB/40 MP/WebP/server normalization; không dùng AiJobService; synthetic identity; cách scanner/decode nếu chọn shortcut; có thể rút gọn upload. | Mỗi lệch cần owner chấp thuận và phải ghi tác động contract/migration; không tự coi hash fixture là scanner CLEAN. |

## 2. Các lựa chọn owner đề xuất

Tất cả D1–D18/Q1–Q5 vẫn **CHỜ OWNER DUYỆT**. Đây là cấu hình draft, không phải approval.

| ID | Đề xuất | Giới hạn / điều kiện |
|---|---|---|
| D1 Scope | Parent synthetic, một actor, một run, một ảnh RUN_ARTWORK, một Vision attempt; người lớn CONFIRM. PREPARATION_REVIEW giữ active-owner lock đến khi hoàn tất hoặc cancel. | Correction/rerun, Teacher thật, story/video/audio, quota và UI ngoài scope. Cancel là lối thoát; không chứng minh provider dừng. |
| D2 Identity | Actor synthetic seed phía server, local/loopback; không lấy authority từ X-Actor-Ref client. | Không chứng minh auth Parent/BOLA/production tenant. Không tạo org giả. |
| D3 Photo/A1 seam | Binding/adapter ảnh riêng; shared A1 chỉ thêm before_finalize và success_evidence_kind; canvas default không đổi; cùng guard/ledger/transport. | Không đổi ObservationRequest, application/services/vision_analysis.py, codec, canvas call sites hay Modal server; không hook fence. Receipt bền trước finalize; lỗi sau SENT giữ UNKNOWN, không resend. |
| D4 Admission/decode/scanner | Chỉ fixture synthetic exact SHA-256 allowlist phía server; kiểm hash/size trước FEAT-018 decoder. Giữ FEAT-018: 5.000.000 byte, 4.000.000 pixel, cạnh 4096, PNG/JPEG. Thêm ImageSafetyScannerPort. Attestation riêng không phải CLEAN; ClamAV chỉ nếu owner tự xác nhận khả dụng. | Decoder là PyAV in-process, không hard timeout/memory cap. Không nhận bytes tùy ý hay tuyên bố bảo vệ decompression bomb. Input ngoài fixture cần process isolation + OS limits. Scanner lỗi → FAILED, session mới. |
| D5 Core owner scope | Thêm owner_scope_kind NOT NULL DEFAULT ORGANIZATION và owner_scope_ref nullable, không runtime backfill. Legacy org row ref NULL đọc fallback organization_id. New org row ref phải khớp organization_id; Parent row dùng PARENT_ACCOUNT/ref, organization_id NULL. | organization_id hiện NOT NULL: migration phải cho phép NULL cho Parent, thêm CHECK/index và rule legacy tạm; không org giả. |
| D6 Run ID | UUIDv4 ổn định là story_run_id, public opaque run_ref và ledger run_id. | Replay cùng key/fingerprint giữ run_ref. |
| D7 Job/attempt | Một VISION_SUBJECT_V1, tối đa một attempt/run; job/attempt UUIDv5 deterministic từ run ID và versioned name. Ledger organization_id chỉ là technical namespace, không phải tenant. | Công thức ổn định; không tạo organization row. |
| D8 Result | Immutable Story result receipt/revision commit trước ledger finalize; run head update bằng CAS expected revision. Raw body hash tách canonical result hash. | Chỉ response V2 hợp lệ mới project SUBJECT_REVIEW. Canvas default giữ nguyên. |
| D9 UNKNOWN | Không chuyển UNKNOWN thành FAILED, không auto-retry. Cancel là run-level exit từ INPUT_PROCESSING, kể cả job_state AWAITING_RECONCILIATION; ledger UNKNOWN giữ nguyên. | UC-11 hủy run chưa kết thúc; AWAITING_RECONCILIATION là AiJob state, không phải StoryRun state. Late output bị run/head CAS loại. Không bảo đảm GPU đã dừng. |
| D10 Contract | Giữ SRS routes/DTO; 5 upload-session operations và cancel; OpenAPI StoryRunLite-v1 trước để UI ghép. | /assets vẫn attach ref, không multipart; không thêm StoryRun state; expired upload 410 envelope cơ bản, chưa có purge snapshot. |
| D11 AiJobService | Hoãn full AiJobService/outbox/retry; Story sở hữu run/result, A1 ledger chống resend. | Poll UNKNOWN chiếu AWAITING_RECONCILIATION; đây không phải AiJob persistence SRS §22. Không reanalyze/auto-retry. |
| D12 Worker | Một API process giữ PostgreSQL session advisory lock từ startup; instance hai fail-fast. Executor/worker capacity=1; readiness fail và command mới bị từ chối khi mất lock. | Không worker_epoch/queue bền/multi-process; residual risk tại D17. |
| D13 Baseline | Mỗi goal có snapshot/worktree ghim commit và approval; PG chỉ trên disposable DB mới với bằng chứng cleanup. | Không dùng/kiểm/dọn DB A2. |
| D14 Story receipts | story.command_receipts là nguồn replay duy nhất cho create/attach/confirm/cancel; typed scope, operation, key hash, fingerprint, PENDING/FINAL, status/version/snapshot giới hạn và resource ref. | review_decisions chỉ FK command_receipt_id, không có idempotency authority riêng. |
| D15 Scanner | ImageSafetyScannerPort có exact-fixture attestation hoặc ClamAV. Attestation xác nhận fixture được phép trong synthetic demo, KHÔNG phải AV/CLEAN; client không tự gửi verdict. | Không mở live Modal bằng attestation nếu owner chưa chấp nhận rõ không có antivirus. Không dò ClamAV/3310. |
| D16 Core upload | core.upload_command_receipts canonical cho create/complete/abort; PUT part natural key session+part_number+digest. Tổng ≤5.000.000 byte, part ≤4.194.304, tối đa 2 part liên tục; aggregate SHA trên bytes nối theo thứ tự. | Scanner fail → FAILED, session mới. Không idempotency uniqueness song song trong upload_sessions. API quảng bá max_total_bytes/part_size_bytes/max_parts, UI không hard-code 2. |
| D17 Single instance + CAS | Session advisory lock + Story run-head CAS; không lease row, worker_epoch hoặc hook claim/mark_sent. | Worker đã CLAIMED có thể tới SENT một lần sau lock loss; call có thể bị phí. UNIQUE ngăn lần claim thứ hai cùng tuple nhưng không fence claimant cũ. Chuyển Q3-C trước multi-process, dữ liệu thật hoặc zero-send requirement. |
| D18 Upload concurrency/cleanup | PUT/complete/abort dùng row lock/CAS state_version; part chỉ thêm khi OPEN; complete xác minh 1..N, tổng bytes và hash; thiếu part 422, session còn RECEIVING/key chưa tiêu. Abort/expiry đổi state rồi xóa staged bytes đồng bộ best-effort. | Không purge worker/purge_state/410 tombstone snapshot ở milestone đầu. Crash/error có thể để sót bytes synthetic; không dùng dữ liệu thật trước hardening

## 3. Luồng command, invocation và phục hồi

1. POST /v1/story-runs resolve actor synthetic server-side; collection receipt canonical được reserve trước active-owner check. Same key/fingerprint replay snapshot; key khác fingerprint trả 400. Một transaction tạo run/input và FINAL 201.
2. POST /v1/upload-sessions nhận STORY_RUN target, RUN_ARTWORK, media_type, expected size/hash và Idempotency-Key. Core receipt canonical bảo đảm replay không tạo session hai; response quảng bá giới hạn upload.
3. PUT part là bytes thô ≤4 MiB; part number bắt đầu 1, liên tục không gap. Cùng session/part/digest replay; cùng part khác digest 409. Mọi part/complete/abort khóa session và CAS state_version.
4. Complete kiểm part liên tục, tổng ≤5.000.000 byte và SHA-256 của bytes nối theo part_number. Tối đa 2 part; 5.000.000 = 4.194.304 + 805.696 byte. Không hash các hash-part. Thiếu part trả 422 UPLOAD_INCOMPLETE, session RECEIVING, key chưa tiêu.
5. Trước decoder, exact file SHA phải có trong server allowlist fixture; mismatch bị chặn. Fixture hợp lệ đi qua giới hạn FEAT-018 (PNG/JPEG, byte/pixel/cạnh, metadata/frame/decode). Decoder in-process không có hard timeout/OS memory cap; không nhận ảnh tùy ý. ClamAV phải trả CLEAN đúng bytes mới gọi là scanner-clean; attestation trả SYNTHETIC_FIXTURE_ATTESTED, không giả CLEAN. Admission/scanner lỗi → FAILED, upload-session mới, không asset/không Vision.
6. Goal 1 chạy fake Vision; Goal 2 chỉ HTTP loopback qua A1 guard/ledger/transport. Story receipt/revision bền trước finalize. Hook lỗi sau SENT hoặc phản hồi mơ hồ → PROVIDER_OUTCOME_UNKNOWN; không resend; reconcile cùng tuple, không sửa ledger UNKNOWN.
7. POST cancel nhận expected revision + Idempotency-Key. UC-11 cho hủy run chưa kết thúc, gồm INPUT_PROCESSING; job UNKNOWN vẫn là AiJob state trong run chưa kết thúc. Một transaction ghi DELETE_PENDING, FINAL receipt và nhả active-owner lock. Demo không có AiJobService/provider cancel. Staged bytes được xóa đồng bộ best-effort; ledger UNKNOWN không đổi.
8. Late result sau cancel bị loại vì run DELETE_PENDING/revision mới làm head CAS thất bại; không được cập nhật run mới. Cancel không chứng minh Modal/GPU đã dừng.
9. GET run UNKNOWN trả HTTP 200, run_state hợp lệ chưa kết thúc (thường INPUT_PROCESSING), job_state AWAITING_RECONCILIATION, PROVIDER_OUTCOME_UNKNOWN, retryable=false, action_required=OPERATOR_REVIEW. Cancel trả DELETE_PENDING. Không thêm StoryRun state UNKNOWN.
10. Abort/expiry/cancel ghi state trước, rồi xóa bytes best-effort. Không có durable sweeper/tombstone; crash/storage error có thể để sót bytes synthetic, phải harden trước dữ liệu thật.

### Crash/race acceptance

| Tình huống | Kết quả |
|---|---|
| Queue full | 503 trước mutation/receipt/key use. |
| Part thiếu/gap | 422, RECEIVING giữ nguyên, bổ sung part rồi complete lại. |
| PUT cùng part/hash so với hash khác | Exact replay; hash khác 409, không overwrite. |
| PUT đua complete/abort hoặc hai complete | Row lock/CAS chỉ một winner; loser conflict, tối đa một validation dispatch. |
| Scanner/admission lỗi | FAILED, không asset/vision; retry bằng session mới. |
| Crash sau abort/expiry/cancel trước byte delete | State đã chốt, bytes có thể còn; không durable purge ở demo. |
| Cancel INPUT_PROCESSING hoặc UNKNOWN | DELETE_PENDING, lock nhả, ledger UNKNOWN không đổi; late result bị CAS loại. |
| Lock mất sau CLAIMED trước SENT | Readiness fail; worker cũ vẫn có thể SENT một lần, call có thể phí. |
| SENT rồi timeout/reset/3xx/5xx/401/invalid V2 | UNKNOWN, không auto-resend. |
| Result receipt bền nhưng ledger finalize UNKNOWN | Reconcile cùng tuple; ledger giữ UNKNOWN; Story head chỉ update nếu CAS còn hợp lệ. |

### Hash không được gộp

transport_response_body_sha256 là raw HTTP body; canonical_result_sha256 là canonical validated JSON; original_image_sha256 và model_input_sha256 chỉ tách khi có hai asset; fixture attestation hash chỉ nhận diện fixture, không phải verdict malware hay result hash.

## 4. Contract API cụ thể cho UI

OpenAPI StoryRunLite-v1 là nguồn chuẩn. Goal 1 xuất OpenAPI và Bruno skeleton/examples làm bước đầu để UI ghép song song. Route, envelope, headers và ý nghĩa operation được giữ khi hardening; limit do server quảng bá.

| # | Operation | Thành công | Contract chính |
|---:|---|---:|---|
| 1 | POST /v1/story-runs | 201 | profile_ref synthetic + Idempotency-Key; trả run_ref/state/revision/version/time. |
| 2 | POST /v1/upload-sessions | 201 | STORY_RUN target, RUN_ARTWORK, media/size/SHA; trả upload_ref, RECEIVING/version, part_size_bytes=4194304, max_total_bytes=5000000, max_parts=2, expiry. |
| 3 | GET /v1/upload-sessions/{upload_id} | 200; 410 expired | state/version/parts/limits/error/expiry; 410 chỉ envelope SRS cơ bản, không purge snapshot. |
| 4 | PUT /v1/upload-sessions/{upload_id}/parts/{part_no} | 200 | raw bytes ≤4 MiB, Content-Length + Content-SHA256, part từ 1 liên tục; exact replay idempotent, digest khác 409. |
| 5 | POST /v1/upload-sessions/{upload_id}/complete | 202 | aggregate size/SHA, If-Match, Idempotency-Key; Location + Retry-After. Thiếu part 422 không consume key. |
| 6 | DELETE /v1/upload-sessions/{upload_id} | 202 | If-Match + Idempotency-Key; chốt ABORTED rồi xóa bytes best-effort, không purge poll. |
| 7 | POST /v1/story-runs/{id}/assets | 202 | attach asset ref, expected run revision, Idempotency-Key; không multipart. |
| 8 | GET /v1/story-runs/{id} | 200 | SRS run_state, revision/version, target revision/timestamps, job fields, retry/action/error; result chỉ ở SUBJECT_REVIEW. |
| 9 | POST /v1/story-runs/{id}/subject-confirmation | 202 | chỉ CONFIRM; expected understanding revision + Idempotency-Key; sau đó PREPARATION_REVIEW. |
| 10 | POST /v1/story-runs/{id}/cancel | 202 | expected run revision + Idempotency-Key; DELETE_PENDING và nhả active lock cùng transaction; không khẳng định provider dừng. |

### Request/response, states và errors

- Error envelope SRS: code, message, correlation_id, retryable, retry_after_seconds? và field_errors?; không echo bytes, key, token, storage URL hay provider detail.
- Idempotency: canonical receipt gồm actor scope, operation, server-defined scope, key hash và RFC 8785 fingerprint; exact replay nguyên status/body; key/fingerprint khác trả 400 INVALID_IDEMPOTENCY_KEY. PUT part idempotent theo session/part/digest.
- UI dùng max_total_bytes, part_size_bytes, max_parts từ API, không hard-code hai part. Khi mở lên 20 MiB, server có thể quảng bá 5 part mà không đổi routes/DTO.
- Upload pilot states: RECEIVING, VALIDATION_PENDING, READY, FAILED, ABORTED, EXPIRED. Scanner error là FAILED + session mới. QUARANTINED/retry chỉ thêm sau hardening; UI phải xử lý state chưa biết fail-closed.
- UNKNOWN không phải StoryRun state: run giữ state SRS chưa kết thúc, thường INPUT_PROCESSING; job_state chiếu AWAITING_RECONCILIATION, code PROVIDER_OUTCOME_UNKNOWN, retryable=false, action_required=OPERATOR_REVIEW. Cancel thành DELETE_PENDING.
- GET dùng ETag/If-None-Match và backoff theo SRS; không progress giả, prompt, provider payload.
- Giữ mapping: INVALID_FILE_CONTENT=400; STALE_REVISION=409; UPLOAD_INCOMPLETE/UPLOAD_CHECKSUM_MISMATCH/UPLOAD_CONTENT_MISMATCH/IMAGE_DIMENSIONS_EXCEEDED=422; QUEUE_UNAVAILABLE=503; UPLOAD_SESSION_EXPIRED=410; RATE_LIMITED=429. Pilot extensions versioned: PROVIDER_OUTCOME_UNKNOWN, VISION_ATTEMPT_HOLD, IMAGE_SAFETY_REJECTED, SAFETY_SCANNER_UNAVAILABLE. Scanner failure ở pilot thành FAILED, không retry cùng session.
- 404 RESOURCE_NOT_FOUND đồng nhất cho absent/out-of-scope. 409 gồm ACTIVE_RUN_EXISTS, INVALID_STATE_TRANSITION, UPLOAD_PART_CONFLICT, UPLOAD_SESSION_STATE_CONFLICT. Không đổi HTTP status mã SRS.
- Giữ rate limits SRS §10.4: API 60/min/account, local IP 20/min, create run 2/min/account, upload create/complete/abort 10/min, part PUT 60/min và 40 MiB bytes mới/min/account, tối đa 3 active sessions/account, status 30/min/session. Exact digest retry tính request, không tính byte mới.
- Expired GET trả 410 envelope cơ bản; v1 không hứa purge_state, purge poll hay tombstone snapshot. Future fields/states additive và client forward-compatible; không đổi semantics route.
- /health không chứng minh model loaded hoặc A1 live.

## 5. Acceptance cho hai goal tương lai

Acceptance chung: server pin đúng synthetic fixture hash; attestation không gọi CLEAN; không có ảnh ngoài allowlist; không auto-resend; cancel INPUT_PROCESSING và UNKNOWN/AWAITING_RECONCILIATION; late result bị CAS loại; upload tối đa 2 part; scanner fail → FAILED + session mới; stale revision conflict; canvas default không đổi.

### Goal 1 — OpenAPI trước + synthetic API/fake Vision

- Bước đầu xuất OpenAPI StoryRunLite-v1 và Bruno skeleton/examples để UI bắt đầu song song. Sau review/freeze contract mới làm API, persistence, intake/admission, Story state, fake Vision, CONFIRM/cancel.
- Đủ 10 operations; contract tests khớp DTO/status/headers/errors/idempotency/rate limits. Bruno chạy happy/error path.
- Kiểm 1-part và 2-part, tổng ≤5.000.000 byte; max part 4.194.304; SHA là bytes nối theo thứ tự; gap thiếu 422, key chưa consume.
- Exact create/complete/abort replay nguyên snapshot; khác fingerprint 400; exact part replay không ghi lại; digest khác 409; complete/abort race một winner.
- Scanner/admission fail → FAILED, không asset/Vision; retry session mới.
- Cancel cả INPUT_PROCESSING và UNKNOWN/AWAITING_RECONCILIATION trả 202/DELETE_PENDING, nhả lock, không đổi ledger UNKNOWN; fake late result bị CAS loại. Hủy không biểu diễn là provider đã dừng.
- UNKNOWN không retry/attempt mới/FAILED. Run mới chỉ sau accepted cancel.
- External network/provider bị chặn; PG chỉ disposable database có bằng chứng tạo/cleanup, không DB A2. Independent review trước Goal 2.

### Goal 2 — A1 photo bridge/readiness offline

- Photo bridge dùng guard/ledger/transport A1; shared change chỉ before_finalize + success_evidence_kind. Không sửa ObservationRequest, application/services/vision_analysis.py hoặc canvas codec/call sites.
- Loopback: success đúng một send; guard/ledger denial zero; race tối đa một; crash sau SENT không resend; timeout/reset/3xx/5xx/401/invalid V2 → UNKNOWN; test deadline rút ngắn.
- Story receipt trước finalize; raw/canonical hashes riêng; UNKNOWN reconcile cùng tuple, ledger UNKNOWN không đổi; cancel/stale revision bỏ late result.
- Canvas default/evidence giữ nguyên; loopback không gắn nhãn live.
- Không Modal/GPU/provider; readiness report và independent review xong rồi mới xin owner approval riêng cho live Modal.

## 6. Vẫn chờ owner chấp thuận

V11 chưa duyệt D3, migration/domain, lưu ảnh, owner scope, scanner, AiJobService hay Modal. Mọi quyết định vẫn cần owner duyệt sau independent review.

### 6.1 Q1–Q5 và deviation có thời hạn

Ước lượng thô cho một backend engineer quen repo; độ tin cậy thấp. Thêm 30–100% review/fix; không gồm chờ owner/UI/live Modal hoặc lỗi ngoài dự kiến.

| Q | Hướng draft | Phương án còn mở / chốt owner |
|---|---|---|
| Q1 Upload | **B:** 5 route/DTO SRS, receipt canonical, row lock/CAS, tối đa 2 part. Scanner fail → FAILED + session mới. Hoãn purge worker, QUARANTINED retry, purge_state, 410 snapshot. | A: full SRS resume/retry/purge. C: multipart. Duyệt deviation 5 MB/4 MP/PNG-JPEG và best-effort cleanup. |
| Q2 Reset | **A tối thiểu:** SRS POST cancel, expected revision/key, DELETE_PENDING + nhả lock trong transaction; staged bytes xóa đồng bộ best-effort. | B: script chỉ gọi route. C: nhiều actor. Duyệt cancel INPUT_PROCESSING và UNKNOWN; không DB direct. |
| Q3 Worker | **B+:** một process/session advisory lock, capacity 1, readiness fail/reject command khi mất lock, run-head CAS; không epoch/hook. | A: full fence. B: UNIQUE + CAS. C: fence mark_sent. Duyệt residual B+ hoặc chọn C trước multi-process, real data, zero-send. |
| Q4 Decode/scanner | Decode điều chỉnh thành **B-fixture-only** do decoder in-process, không 3s timeout/cap; exact hash gate trước decode. Chọn ClamAV nếu owner tự xác nhận, nếu không attestation synthetic không CLEAN. | A: Windows Job Object; C: container OS limits đã xác minh. Owner chốt ClamAV hay attestation; không dò cổng 3310. |
| Q5 Milestone | **B:** hai goal tuần tự; G1 OpenAPI/Bruno đầu tiên, rồi fake-Vision API slice; G2 A1 bridge/loopback/readiness. | A: một goal. C: ba mốc. Không song song vì shared contract/A1. Live Modal approval riêng. |

#### Sổ độ lệch

| Độ lệch | Lý do | Rủi ro | Điều kiện đảo | Hardening |
|---|---|---|---|---|
| 5 MB/4 MP/4096 PNG/JPEG thay SRS 20 MiB/40 MP/WebP | FEAT-018 có policy nhỏ, scope synthetic. | Không hỗ trợ ảnh phone thật/12 MP, chưa phải SRS. | Trước ảnh người dùng/lớn hơn. | SRS normalization/size policy, hash/lineage, test ảnh lớn. |
| Exact fixture + decoder in-process, không timeout/cap | Mã PyAV hiện tại không có killable subprocess/resource cap. | Header limit không hard-bound allocation. | Trước bất kỳ ảnh nào ngoài fixture. | Process killable, OS CPU/RAM cap đã kiểm chứng, bomb/corrupt/timeout tests. |
| Attestation thay antivirus nếu được chọn | Availability ClamAV chưa xác minh; chỉ synthetic. | Không phát hiện malware; không được gọi CLEAN. | Input không synthetic hoặc live gate cần AV. | ClamAV/production scanner với digest/version/time, fail-closed; owner duyệt live nếu còn attestation. |
| Scanner error → FAILED/session mới | Hoãn QUARANTINED recovery. | Tốn UX/session; bytes cũ có thể còn. | Cần resume/retry hoặc dữ liệu thật. | Durable QUARANTINED, fresh-key/If-Match CAS, recovery tests. |
| Không purge worker/state/410 snapshot; delete đồng bộ best-effort | Rút ngắn demo synthetic. | Crash/storage failure để lại staged bytes; không poll cleanup. | Trước chạy dài/dữ liệu thật. | Durable tombstone, idempotent sweeper, purge poll/410 snapshot, cleanup evidence. |
| Không AiJobService/outbox/retry | Một stage/attempt, fake/loopback. | Không durable lifecycle/recovery SRS §22; UNKNOWN cần operator cancel. | Multi-stage/worker/retry. | AiJobService/outbox/reconciler; không resend UNKNOWN. |
| Q3-B+ no fence at SENT | Tái dùng A1, không sửa claim/mark_sent. | CLAIMED cũ có thể gửi một lần sau lock loss; phí call/không zero-send. | Multi-process, real data hoặc zero-send. | Q3-C tại mark_sent hoặc lease/epoch fence đầy đủ + race review. |
| Synthetic identity, API only | BE contract demo cho UI khác. | Không chứng minh auth/BOLA/privacy. | Trước dữ liệu/tài khoản thật. | Auth/tenant/privacy/consent/retention review. |

#### DTR amendment tối thiểu (không sửa register)

| Lớp đếm | Hiện tại | Sau thêm hai receipt table | Thay đổi |
|---|---:|---:|---|
| §14.1 baseline SRS v2.3 | 51 new / 89 active / 137 physical | 53 new / 91 active / 139 physical | +core.upload_command_receipts, +story.command_receipts. |
| §14.4 Rev31 crosswalk | 54 new / 92 active / 140 physical | 56 new / 94 active / 142 physical | Cùng thêm hai bảng. |
| Source-declared mappings | 89 | Giữ 89 tới implementation | Không tuyên bố đây là DB live count. |

Amend §5.1 Core 3→4, §5.6 Story 9→10, §14.1 và §14.4; thêm hai receipt tables; Core upload_sessions bỏ key/hash/unique replay riêng; upload_parts dùng cột part_number; Story run target/purpose/state/version fields; review_decisions FK command_receipt_id, không unique replay; core_asset_metadata thêm owner_scope_kind/ref, nullable organization_id cho Parent, CHECK/index và legacy read fallback. Không runtime backfill; cột mới không đổi table count.

### 6.2 Milestone đề xuất, chưa phải goal

| Goal | Phạm vi/điều kiện | Effort thô |
|---|---|---:|
| 1 — API contract + synthetic Parent slice | Bước đầu OpenAPI + Bruno examples cho UI. Sau freeze: DTR/migration approval, upload, Story UoW, fixture gate, scanner choice, fake Vision, CONFIRM/cancel; không provider. | 2–4 ngày |
| 2 — A1 photo bridge + offline readiness | Chỉ sau G1 review/accept; before_finalize/evidence kind, photo bridge, loopback/crash/race/UNKNOWN, canvas regression; không live provider. | 2–4 ngày |
| Tổng cơ sở | Tuần tự, shared contract/A1. | 4–8 ngày |
| Cộng review/fix | 30–100%; khoảng tính toán, độ tin cậy thấp. | 5,2–16 ngày |

Tạo goal từng bước sau independent review M0, owner duyệt lựa chọn/deviation, plan hash và approval. Không mở Goal 2 trước review Goal 1.

## 7. Crosswalk các finding review trước

### Nguồn và giới hạn traceability

- V9 source: `plan/STORYRUN_LITE_VISION_M0_V9_DRAFT_20261102.md`; expected hash trong prompt V10 **F922C7AEBFBA5A6DACAC5315952C33B94A1B06097719C9B50A7485A83CA5979C**, actual hash khi soạn V10 **C2364A72D4C8E11EDFEE015C2E4F6C2B40F5813A1230EC4265EC363890FD6C9D**. V10 dựa trên bản actual và không khẳng định review V9 đã hoàn tất.
- Review V3: report nguyên văn lưu tại `evidence/STORYRUN_LITE_VISION_M0_V3_INDEPENDENT_REVIEW_20261102.md`, Codex thread `01a19ace-ea77-7cd2-a630-ca55fdb2b5f7`, SHA-256 **47772B37E91A57C11ACD32664ADAEC511574B7685699FC9F118835E55D29FD4B**.
- Review V6: report nguyên văn lưu tại `evidence/STORYRUN_LITE_VISION_M0_V6_INDEPENDENT_REVIEW_20261102.md`, Codex thread `01a19b0d-5746-79e3-8dfa-81f622647d09`, SHA-256 **E80C77E1614093137744FFDBC84B03E61FE2F61AB86E710D0D991DD2EFD0ABC3**.
- Review V7: report nguyên văn lưu tại `evidence/STORYRUN_LITE_VISION_M0_V7_INDEPENDENT_REVIEW_20261102.md`, Codex thread `01a19b29-138f-78f2-8f46-765ca55ed506`; NEEDS_REVISION (1 P1, 3 P2, 1 P3). Report SHA-256 **FBB06C848CF3E2EF41FB7037A7F5CCBFD45E7D3A730C00A76407BC1B1BCB24B8**; V7 SHA-256 **23EF3BBB5E8E51BA27221091C5AC16D42B8B87F3FB9DBEE975E6955F90346EA7**.
- Review V8: report nguyên văn lưu tại `evidence/STORYRUN_LITE_VISION_M0_V8_INDEPENDENT_REVIEW_20261102.md`, Codex thread `01a19b3b-5bfe-7181-aae2-8cba92c08493`; NEEDS_REVISION (4 P2, không P0/P1). Report SHA-256 **B88F014CBF34DBAE879DE63BA2E6D15254BB10F99BDBC8E799BFD4BC5AFF5A8E**; V8 SHA-256 **75F7C0312E7683EA24BBC079BECF7FC7CF364F107B3AE89552F5546C5DE6A0D3**.
- Report gốc V4/V5 chưa tìm thấy trong checkout hoặc các thread Codex liên quan đã truy vấn. V4 draft hash **96D40096E7D57DFBBBF270D80AD7BE2C24555D69935156CBBEA5A648C170BC7E** và V5 draft hash **FE532FB2EEC71DAE4A407428C23A1F54267698C3B9CA8262C971F410F1590262** chỉ ghi tóm tắt kết quả/finding; các hàng V4/V5 dưới đây được khôi phục từ chúng và crosswalk V6, không phải report nguyên văn. Không tự tạo finding ID.

| Nguồn / mức | Finding được ghi nhận | Disposition V10 (draft, chưa review) |
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
| V5 P3 | Review traceability absent | V3/V6/V7 exact reports archived; V4/V5 originals explicitly unavailable and reconstruction labeled — §7 (archive limitation remains explicit) |
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
| V6 P3 | Historical V4/V5 reports missing | Exact V3/V6/V7 archived; V4/V5 originals remain unavailable and are never represented as exact sources — §7; seek source before claiming full archive closure |
| V7 P1 | Collection create lacked a scope before resource ID; Core receipt authority and `media_type` fingerprint were ambiguous | Server-defined collection scopes for run/upload creates; unique actor+operation+scope+key identity; complete semantic fingerprints; `core.upload_command_receipts` canonical with DTR amendment — D14/D16/§3/§4/§5 |
| V7 P2-1 | SRS error mapping and poll/tombstone DTO incomplete | `INVALID_FILE_CONTENT=400`; new pilot codes versioned; Story poll includes job state/target revision/start time; expired upload 410 includes versioned purge snapshot — D10/§4/§5 |
| V7 P2-2 | QUARANTINED validation retry had no transition | Explicit `OPEN/QUARANTINED→OPEN/PENDING` CAS with fresh key + current If-Match; replay/restart semantics and acceptance tests — D16/D18/§3/§5 |
| V7 P2-3 | DTR target/purpose/receipt schema differed from upload API | Typed STORY_RUN target, `RUN_ARTWORK_ORIGINAL`, exact session/receipt fields and constraints in DTR before migration — D5/D16/§3/§4/§5/§6 |
| V7 P3 | Original V4/V5 review reports unavailable | Remains a disclosed historical archive gap; reconstructed summaries are not called original reports. Nonblocking for implementation only while this limitation remains explicit — §7 |
| V8 P2-1 | DTR totals omitted current Rev31 crosswalk and DB column used `part_no` | V10 records two count views `53/91/139` and `56/94/142`, precise DTR sections and DB `part_number` / route `{part_no}` mapping; migration amendment remains unimplemented and owner-gated — §1/§5/§6.1 |
| V8 P2-2 | `story.review_decisions` still had its own per-run idempotency unique | V10 keeps `story.command_receipts` as sole replay/key-conflict source; decision links `command_receipt_id`; acceptance requires same Story UoW — D14/§5 |
| V8 P2-3 | Crash recovery could leave Core PENDING receipt orphaned or change a FINAL response implicitly | V10 retains atomic quarantine/version + orphan PENDING→FINAL 409, immutable FINAL 202, stale-worker CAS, and both crash-injection cases — D18/§3/§5 |
| V8 P2-4 | Acceptance did not execute adult subject confirmation | V10 retains full flow to CONFIRM/PREPARATION_REVIEW, exact replay/no duplicate decision or Vision attempt, stale revision 409, Bruno; adds cancel/reset acceptance only if Q2 selects cancel — §4/§5 |

### C1–C8 fact-check summary

`STORYRUN_LITE_VISION_M0_V10_FINDINGS_HANDLING_20261102.md` contains the per-finding verdicts and source line references. C1/C4/C7 are confirmed; C2/C3/C5 are partially confirmed; C6 is a real shared-boundary change whose exact seam depends on D3/Q3; C8 verifies the four V8 fixes in V9 text, not independent review acceptance. No source/test/runtime result is implied.

### V11 delta và disposition cập nhật

Crosswalk V3–V8 phía trên được giữ như lịch sử disposition V10; bảng dưới ghi thay đổi draft, không xóa finding hoặc xác nhận reviewer đã accept.

| Finding | V11 draft |
|---|---|
| V8 P2-1 DTR/count/part_number | Giữ hai lớp đếm, thêm đúng hai receipts, Core column part_number, typed owner scope với legacy exception/no runtime backfill. |
| V8 P2-2 replay authority | story.command_receipts là nguồn duy nhất; review_decisions chỉ FK command_receipt_id, cùng Story UoW. |
| V8 P2-3 orphan PENDING/immutable FINAL | Giữ receipts, row lock/CAS/exact replay; hoãn durable quarantine recovery. Scanner lỗi FAILED + session mới; không tuyên bố recovery V10 đầy đủ trong pilot. |
| V8 P2-4 confirm | Goal 1 vẫn tới CONFIRM/PREPARATION_REVIEW; thêm cancel từ INPUT_PROCESSING/UNKNOWN. |
| C1 | SRS cancel giải phóng lock; UNKNOWN là AiJob state, ledger giữ UNKNOWN. |
| C2 | Q3-B+ residual minh bạch; nâng Q3-C trước multi-process/real data/zero-send. |
| C3 | Q1-B giữ 5 route/DTO, tối đa 2 part, receipts/CAS; hoãn purge/quarantine retry/tombstone. |
| C4 | Decoder là in-process PyAV; không subprocess 3s/hard cap. Exact fixture hash gate; arbitrary input bị chặn tới khi decoder isolation. |
| C5 | Không dò ClamAV; attestation không CLEAN; owner chọn/duyệt adapter. |
| C6 | Chỉ before_finalize + success_evidence_kind; không ledger fence hook, không đổi request/service/canvas. |
| C7 | Hai goal tuần tự; Goal 1 OpenAPI/Bruno trước + fake Vision; Goal 2 bridge/loopback. Modal approval riêng. |
| C8 | Giữ crosswalk DTR/receipt/crash/CONFIRM; không suy ra V9/V10/V11 review accepted. |

**V11 chưa được review độc lập.** Reviewer kiểm đặc biệt: Q3-B+ residual; cancel từ UNKNOWN và INPUT_PROCESSING theo UC-11; 2-part aggregate hash; contract ổn định UI; DTR amendment/legacy owner scope; decoder in-process/exact fixture; attestation không CLEAN; cleanup best-effort; deviation và effort.

## 8. Ngoài phạm vi và trạng thái review

- Không sửa A2/B1/B2; A2 vẫn TẠM DỪNG, snapshot .claude/handoff/snapshots/CLAUDE_A2_PAUSE_20261102T121212 được giữ nguyên.
- Không sửa SRS, DATA_TABLE_REGISTER, approval, V1–V10, source code hoặc migration. V11 chỉ ghi amendment cần thiết.
- Không triển khai UI, Teacher thật, correction/rerun, story/video/audio, quota production, consent/retention dữ liệu thật hoặc orchestration đa stage.
- Không gọi Modal/GPU/provider/mạng ngoài, không dò port/service, không dùng DB A2.
- Không stage/commit/push/merge hoặc tạo goal. V11 vẫn DRAFT, chưa owner-approved và chưa independent-review accepted.