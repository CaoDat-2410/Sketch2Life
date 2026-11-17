<!-- Captured from Codex thread 01a19b0d-5746-79e3-8dfa-81f622647d09, turn 01a19b0d-5d27-7531-af00-8c18629f4c40; read-only independent review. -->

# Kết luận: **NEEDS_REVISION**

Không có P0. Có hai P1 cần sửa trước khi chấp nhận M0: worker có thể chặn API polling và luồng Core upload chưa khóa các cuộc đua trạng thái. Các P2 bên dưới cần được chốt trong M0 hoặc plan S1+S2 trước khi xem contract là đủ để triển khai.

Đã xác minh hash V2–V6 đều khớp. HEAD và nhánh đúng `a88de875ff92e9b4d4fa5cc2f5f8d5fc1f626f58` / `feature/feat063-be-foundation`. Các dẫn chiếu source bên dưới dùng `git show HEAD:<path>`; thay đổi A2 trong working tree không được dùng làm bằng chứng. Đây là review chỉ đọc; không chạy test, validator, PostgreSQL, Modal, provider hay mạng ngoài.

## Findings

### P1 — Worker đồng bộ có thể làm mất tính bất đồng bộ của API

**Vị trí:** [V6 §2 D12](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V6_DRAFT_20261102.md:42), [V6 §3](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V6_DRAFT_20261102.md:51); source HEAD [transport.py](D:/GitHub/Sketch2Life/backend/src/sketch2life/infrastructure/vision_analysis/transport.py:231), [legacy_v2.py](D:/GitHub/Sketch2Life/backend/src/sketch2life/infrastructure/vision_analysis/legacy_v2.py:157).

`HttpJsonTransport.post_json()` và `observe()` hiện là hàm đồng bộ. Nếu worker chạy chúng trực tiếp trong coroutine của `asyncio.Queue`, một lần gọi Vision có thể giữ event loop đến hết timeout 160 giây; trong thời gian đó FastAPI không phục vụ được `GET` để poll trạng thái. `202` khi ấy không đảm bảo UI có thể đọc trạng thái đang chạy.

**Cần sửa:** quy định worker chạy A1 qua thread/executor hoặc worker thread riêng, giữ concurrency bằng một. Acceptance phải kiểm tra `GET` vẫn trả trạng thái trong lúc loopback call bị giữ chậm và queue đầy trả `503 QUEUE_UNAVAILABLE` mà không ghi receipt.

### P1 — Core upload chưa định nghĩa phân xử nguyên tử cho các lệnh cạnh tranh

**Vị trí:** [V6 §3.2–3.4](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V6_DRAFT_20261102.md:51), [D16](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V6_DRAFT_20261102.md:46); source HEAD [service.py](D:/GitHub/Sketch2Life/backend/src/sketch2life/infrastructure/lesson_library/service.py:698), [tables.py](D:/GitHub/Sketch2Life/backend/src/sketch2life/infrastructure/lesson_library/tables.py:58).

V6 có cơ chế PENDING/queue ack/FINAL rõ cho Story attach, nhưng không định nghĩa xử lý duplicate khi Core receipt còn PENDING. Cũng chưa yêu cầu khóa/CAS theo session version cho `PUT part`, `POST complete` và `DELETE`.

Ví dụ: hai lệnh complete với key khác có thể cùng thấy session đang nhận upload; hoặc `PUT part` có thể đua với complete/abort. Kết quả có thể là validation bị queue hai lần, part được ghi sau khi validation bắt đầu, hoặc purge đua với assemble. Source hiện có cũng chưa đủ làm bằng chứng an toàn: `PUT part` đọc session không khóa, trong khi complete khóa session và kiểm tra part ở luồng riêng.

**Cần sửa:** quy định row lock hoặc CAS có version cho mọi chuyển trạng thái session; chỉ nhận part ở state cho phép; complete và abort phải thắng loại trừ lẫn nhau. Core duplicate cùng key/fingerprint khi PENDING phải chờ cùng dispatcher hoặc được recovery chốt hold, không được tạo validation thứ hai.

### P2 — Mất advisory lock chưa fence worker đang sống

**Vị trí:** [V6 D12](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V6_DRAFT_20261102.md:42), [V6 crash matrix](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V6_DRAFT_20261102.md:69); source HEAD [InvocationGuardedVisionObservationPort](D:/GitHub/Sketch2Life/backend/src/sketch2life/infrastructure/vision_analysis/invocation_guard.py:204), [InvocationLedger](D:/GitHub/Sketch2Life/backend/src/sketch2life/infrastructure/vision_analysis/ledger.py:64).

Sau hard crash, thiết kế không tự enqueue lại; ledger cũng ghi `SENT` trước HTTP và khóa run bằng `run_id`, nên không có lần gửi lại tự động. Rủi ro khác là kết nối giữ session advisory lock mất khi process cũ vẫn còn chạy. PostgreSQL nhả lock; process mới có thể lấy lock và chốt run thành hold, trong khi worker cũ chưa claim ledger vẫn có thể tiếp tục nếu queue gate đã mở. Readiness fail không tự dừng worker đang chạy.

**Cần sửa:** yêu cầu worker kiểm tra/fence quyền sở hữu lock trước `claim` và trước `mark_sent`; result sink phải CAS theo run revision hoặc worker epoch để kết quả từ process cũ không ghi đè recovery. Thêm acceptance mô phỏng mất kết nối lock khi process cũ vẫn sống. Ledger hiện ngăn gửi trùng cùng run, nhưng chưa chứng minh fail-closed trước worker cũ.

### P2 — `UPLOAD_INCOMPLETE` có thể biến session resumable thành terminal

**Vị trí:** [V6 §3.2](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V6_DRAFT_20261102.md:51), [V6 error contract](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V6_DRAFT_20261102.md:105); [SRS §24.2](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1843).

V6 cho phép thử lại bằng key mới khi session `QUARANTINED`, nhưng lỗi nội dung như `UPLOAD_INCOMPLETE` đưa session sang `REJECTED`. Không nói rõ `PUT part` hoặc complete mới có được tiếp tục trên session đó hay không. Một client gửi complete trước khi part cuối được ghi có thể nhận 202, rồi nhận `UPLOAD_INCOMPLETE` trên resource và mất khả năng resume cùng session. V6 cũng chưa nêu rõ yêu cầu part liên tục từ 1, dù SRS yêu cầu assemble theo part liên tục.

**Cần sửa:** nếu thiếu part, giữ session ở `RECEIVING` và trả 422 không consume key, hoặc định nghĩa state retryable rõ ràng cho complete bằng key mới. Acceptance cần kiểm tra part trùng cùng digest, digest khác, part thiếu/thứ tự sai, resume sau restart, aggregate hash và byte count.

### P2 — Abort và expiry có thể mất việc purge sau crash

**Vị trí:** [V6 DELETE upload](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V6_DRAFT_20261102.md:52), [V6 D12](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V6_DRAFT_20261102.md:42); [SRS §24.2](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1843).

DELETE ghi `ABORTED` và trả 202 sau queue ack, nhưng queue nằm trong RAM. Crash sau FINAL 202 có thể làm mất purge command; startup recovery được mô tả cho validation, không thấy đường phục hồi purge. Expiry cũng có state `EXPIRED` và retention grace, nhưng chưa có sweeper/lifecycle đảm bảo xóa chunk objects. SRS yêu cầu purge idempotent cho session expired/aborted.

**Cần sửa:** thêm durable tombstone/outbox hoặc sweeper/storage TTL có thể khôi phục sau restart. Acceptance cần crash sau abort 202 và kiểm chứng purge; kiểm tra expiry không chỉ qua GET mà cả cleanup.

### P2 — Core Parent scope và trạng thái upload chưa khớp source/schema hiện tại

**Vị trí:** [V6 D5](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V6_DRAFT_20261102.md:35), [V6 D16](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V6_DRAFT_20261102.md:46); [DATA_TABLE_REGISTER Core asset](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md:251), [upload session](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md:307).

V6 đúng khi cấm organization giả và yêu cầu lineage riêng. Tuy nhiên HEAD hiện có `CoreAssetMetadataModel.organization_id NOT NULL`; port Core cũng truy vấn theo organization. Upload table hiện dùng `OPEN/COMPLETED/ABORTED/EXPIRED/FAILED`, còn V6 đưa ra `RECEIVING/VALIDATION_PENDING/READY/QUARANTINED/REJECTED`. DATA_TABLE_REGISTER nói chỉ session `COMPLETED` mới trả asset ref, trong khi API V6 trả asset ref ở state `READY`. Luồng Lesson Library hiện có cũng là upload tổ chức và complete đồng bộ, không phải Parent async 202.

**Cần sửa:** trước migration, xác định rõ schema/adapter dùng chung hay bảng mới; thêm owner scope có kiểu và giữ tương thích `organization_id` legacy; xác định `READY` là trạng thái API hay persistence và cập nhật register nếu cần. Không ghi lineage mới vào `source_refs`. A1 ledger yêu cầu PostgreSQL ở source HEAD; đổi acceptance “PostgreSQL nếu cần” thành bắt buộc dùng DB mới disposable và chứng minh cleanup, không đụng DB A2.

### P2 — Wrapper A1 hiện tại sẽ gắn sai loại evidence cho Photo adapter

**Vị trí:** [V6 D3](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V6_DRAFT_20261102.md:33); source HEAD [guard identity check](D:/GitHub/Sketch2Life/backend/src/sketch2life/infrastructure/vision_analysis/invocation_guard.py:183), [evidence rewrite](D:/GitHub/Sketch2Life/backend/src/sketch2life/infrastructure/vision_analysis/invocation_guard.py:253), [legacy bridge](D:/GitHub/Sketch2Life/backend/src/sketch2life/infrastructure/vision_analysis/legacy_v2.py:233).

Photo path riêng có thể dùng normalized bytes qua A1 transport/guard mà không giả `RenderBinding`, không sửa canvas codec và không truyền `processing_image_ref`: `legacy_v2` hiện từ chối trường đó. Guard decorator kiểm tra đúng cùng instance và finalize sau khi inner adapter trả về; vì thế Story sink có thể ghi bền trước finalize như V6 đề xuất.

Nhưng decorator hiện gán `EvidenceKind.LIVE_LEGACY_BRIDGE` cho mọi success. Nếu StoryPhoto adapter dùng wrapper này, evidence sẽ mô tả sai adapter; loopback success cũng có thể mang nhãn live legacy.

**Cần sửa:** định nghĩa wrapper/hook StoryPhoto giữ identity guard và thứ tự finalize nhưng phát evidence kind StoryPhoto/loopback đúng nghĩa. Thêm A1 regression bảo đảm canvas giữ default behavior.

### P2 — FEAT-018 deviation đã nêu, nhưng acceptance đòi bảo vệ decoder chưa có

**Vị trí:** [V6 D4](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V6_DRAFT_20261102.md:34), [V6 acceptance ảnh](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V6_DRAFT_20261102.md:126); [SRS §24.2](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1850).

V6 minh bạch rằng chọn FEAT-018: 5 MB, 4 MP, cạnh 4096, PNG/JPEG và client normalization thay cho SRS 20 MiB, 40 MP, WebP, server normalization. Đây là deviation chờ owner, không phải tuân thủ SRS. Tuy nhiên acceptance còn yêu cầu kiểm decompression limit. Decoder FEAT-018 hiện chạy PyAV trong process; port ghi rõ `ImageDecodeTimeoutError` chỉ có từ test stub và decoder thật không có cơ chế timeout/kill. Ảnh gốc tùy chọn tối đa 15 MB cũng chưa có decoded-dimension policy riêng.

**Cần sửa:** thêm decoder worker có thể giới hạn tài nguyên và bị kill, hoặc thu hẹp claim acceptance/deviation cho đúng phạm vi synthetic loopback. Định nghĩa giới hạn media/dimensions cho source image và kiểm scanner CLEAN cho đúng hash của cả source lẫn normalized trước READY.

### P2 — API còn vài khác biệt với SRS và chưa là wire contract hoàn chỉnh

**Vị trí:** [V6 §4](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V6_DRAFT_20261102.md:89); [SRS subject confirmation](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1574), [error envelope](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:762), [status/job fields](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1717), [rate limits](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:890).

Các status/error chính khác nhìn chung đúng SRS: 400 idempotency, 409 active/stale/state conflicts, 410 expired, 413 size, 415 media type, 429 rate limit, 503 queue unavailable. Điểm lệch cụ thể: V6 đặt subject confirmation là 200; SRS route ghi 202. `PROVIDER_OUTCOME_UNKNOWN` và `SAFETY_SCANNER_UNAVAILABLE` chưa được đánh dấu là pilot extensions; SRS hiện có `AWAITING_RECONCILIATION` cho job. V6 cũng chưa nêu envelope fields `correlation_id`, `retryable`, `retry_after_seconds`, `field_errors`, hoặc `job_stage`/timestamps/version trong status polling. Mục §4 còn thiếu schema request/response cụ thể cho upload create/part.

V6 chỉ nêu 429 `RATE_LIMITED`, chưa áp dụng các giới hạn SRS cho upload: tối đa ba session hoạt động, rate/budget cho chunk và status. Queue `maxsize=1` không giới hạn các session/partial bytes đã tạo.

**Cần sửa:** đổi subject confirmation sang 202 hoặc ghi rõ deviation; đánh dấu mọi mã mới là extension có version; đưa error envelope và poll fields vào OpenAPI. Chốt rate/session caps theo SRS hoặc ghi deviation có giới hạn. OpenAPI/schema test trong S1+S2 là gate đúng, nhưng UI chưa thể ghép trước khi gate đó hoàn tất.

### P2 — Core idempotency receipt có thời hạn replay chưa khớp cam kết chung

**Vị trí:** [V6 D16](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V6_DRAFT_20261102.md:46), [V6 Core idempotency](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V6_DRAFT_20261102.md:111); [SRS §21.4](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1605).

Story receipt được giữ suốt vòng đời run, nhưng Core receipt chỉ giữ đến `expires_at + 24h`. Nếu receipt bị purge rồi client gửi lại cùng create key, Core có thể tạo upload session mới thay vì replay response 201 cũ. SRS yêu cầu cùng key/payload trả kết quả ban đầu nhưng chưa có ngoại lệ thời hạn.

**Cần sửa:** giữ tombstone/receipt đủ lâu để replay, hoặc công bố rõ cửa sổ idempotency trong SRS/OpenAPI và cho client biết khi nào phải tạo key mới.

### P2 — Crosswalk thiếu một V3 P1

**Vị trí:** [V4 ghi tổng V3 review](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V4_DRAFT_20261102.md:5), [V6 crosswalk](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V6_DRAFT_20261102.md:148).

V4 ghi review V3 có 5 P1 và 4 P2. V6 liệt kê 4 V3 P1 và 4 V3 P2. V4/V5 đều được liệt kê đủ theo số finding đã công bố. Mình không thể suy ra finding P1 còn thiếu và không gán ID lịch sử.

**Cần sửa:** đối chiếu báo cáo V3 gốc để bổ sung đúng mô tả/disposition của P1 còn thiếu trước khi gọi crosswalk là đầy đủ.

### P3 — Báo cáo review lịch sử chưa có traceability bền vững

[V6 §7](D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V6_DRAFT_20261102.md:144) thừa nhận báo cáo V4 chưa được lưu trong evidence và đề nghị lưu liên kết/bản sao sau. Trong checkout này không có report V3/V4/V5 dưới FEAT-063; crosswalk cũng không dẫn link hoặc hash nguồn. Vì vậy không thể kiểm chứng độc lập nội dung các hàng từ report gốc. Đây là P3 riêng với lỗi thiếu P1 ở trên: cần lưu báo cáo và cập nhật trỏ nguồn trước khi coi finding V5 về traceability đã đóng.

## Những điểm V6 xử lý đúng

- Story receipt có scope unique, key hash, fingerprint, snapshot bounded; cùng key/payload replay snapshot, khác payload trả 400 `INVALID_IDEMPOTENCY_KEY`. `ACTIVE_RUN_EXISTS` và `STALE_REVISION` dùng 409 và được lưu FINAL; client dùng key mới sau khi sửa state. Đây là thiết kế phù hợp §21.4.
- Story queue gate chỉ mở sau queue ack và receipt FINAL 202. Crash sau SENT không redispatch. Story result sink nằm trước guard finalize; raw HTTP body hash khác canonical result hash; reconcile result bền khi ledger UNKNOWN mà không đổi ledger. Source A1 hỗ trợ thứ tự này nếu StoryPhoto adapter ghi sink bên trong inner adapter.
- UUIDv4 run/public ref/ledger run ID và UUIDv5 job/attempt phù hợp source A1: guard parse `run_id` thành UUID; ledger lưu các ID và `organization_id` dạng string, không có FK organization. Namespace kỹ thuật Parent không phải organization row và không cấp quyền.
- StoryPhoto adapter riêng có đường thực hiện qua A1 mà không dùng `processing_image_ref` hay giả checkpoint. Cần xử lý nhãn evidence của decorator như finding ở trên.
- S1+S2 chỉ mở sau owner approval; fake/loopback là phạm vi kiểm chứng; Modal thật là cổng readiness/approval riêng. §23 billing/quota không áp dụng cho goal một Vision subject không tạo video. V6 không tuyên bố fake là bằng chứng Modal live.

Không có test hoặc validator nào được chạy theo ràng buộc của bạn; không có DB hay dịch vụ ngoài nào được truy cập.