# Kết luận: **NEEDS_REVISION**

**Không có P0; có 1 P1, 3 P2 và 1 P3 còn mở.** P1 chặn việc owner chấp thuận M0 và mở goal S1+S2. P3 là khoảng trống lưu trữ lịch sử, không phải blocker triển khai nếu vẫn ghi rõ là chưa archive đầy đủ.

Baseline khớp: hash V7, report V6/V3, các draft V2–V6, HEAD `a88de875ff92e9b4d4fa5cc2f5f8d5fc1f626f58` và branch `feature/feat063-be-foundation`. Tôi đọc source implementation bằng `git show HEAD:<path>`; không dùng thay đổi local làm chứng cứ. Working tree A2 và các draft được giữ nguyên.

## Findings

### P1 — Receipt chưa định nghĩa được idempotency cho endpoint tạo resource

**Vị trí:** [V7 D14/D16 và luồng create](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V7_DRAFT_20261102.md:45>), [V7 contract](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V7_DRAFT_20261102.md:96>), DTR upload session [§5.1](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md:307>).

`story.command_receipts` và `core.upload_command_receipts` dùng unique key có `resource_scope_ref`, nhưng `POST /story-runs` và `POST /upload-sessions` tạo resource nên chưa có `resource_scope_ref` trước khi receipt được ghi. V7 không định nghĩa giá trị collection scope ổn định để phân xử lần gọi lại. DTR còn mô tả idempotency trên `core.upload_sessions`; V7 thêm bảng receipt riêng nhưng chưa chốt bảng nào là nguồn chuẩn.

Ngoài ra, fingerprint Core nêu purpose/size/hash nhưng không nêu `media_type`, dù đó là input bắt buộc của upload. Dùng lại key với media type khác có thể bị xem như cùng fingerprint.

**Tình huống/tác động:** response tạo session bị mất; client retry cùng key nhưng server không tìm được receipt theo khóa đã nêu, có thể tạo session thứ hai hoặc trả `ACTIVE_RUN_EXISTS` thay vì replay đúng snapshot. Điều này làm yếu cam kết durable receipt và có thể tiêu thêm session/asset.

**Cần sửa:** định nghĩa scope idempotency cho collection create trước khi biết resource ID; yêu cầu `Idempotency-Key` rõ ràng trên mọi command có receipt; fingerprint phải bao gồm toàn bộ input có ý nghĩa, gồm media type và target. Chốt một nguồn receipt canonical cho upload và cập nhật DTR tương ứng.

### P2 — Wire contract còn lệch SRS và thiếu một số hành vi poll

**Vị trí:** [V7 contract/error/poll](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V7_DRAFT_20261102.md:97>), [V7 error codes](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V7_DRAFT_20261102.md:120>); [SRS error contract](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:760>), [SRS status fields](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1717>).

V7 đặt `INVALID_FILE_CONTENT` ở 422, trong khi SRS §9.8 đặt mã này ở 400. `IMAGE_SAFETY_REJECTED` cũng xuất hiện nhưng chưa được liệt kê như pilot extension có version. Story poll chưa nêu rõ `job_state`, target revision và thời điểm bắt đầu mà SRS yêu cầu. Với upload hết hạn, V7 nói `GET` có thể trả 410 nhưng chưa định nghĩa response nào cho biết tombstone và `purge_state`, dù phần cleanup yêu cầu GET thể hiện trạng thái purge.

**Tình huống/tác động:** UI có thể xử lý sai lỗi file hoặc không biết Vision job đang ở trạng thái nào; client poll session hết hạn không biết cleanup đã hoàn tất chưa.

**Cần sửa:** thống nhất 400/422 theo SRS hoặc ghi rõ deviation có version; version hóa mọi pilot error mới; chốt poll DTO gồm các trường SRS cần; định nghĩa response 410 có trạng thái purge/tombstone hoặc một cách poll tương đương. Acceptance OpenAPI ở §5 là gate đúng, nhưng cần chỉ rõ các schema và hành vi này trong contract trước khi handoff UI.

### P2 — Retry validation sau `QUARANTINED` chưa có transition cụ thể

**Vị trí:** [V7 D12/D16/D18](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V7_DRAFT_20261102.md:43>), [V7 transition và mapping](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V7_DRAFT_20261102.md:55>).

V7 nói scanner/validation ở `QUARANTINED` có thể retry bằng key mới, nhưng transition được mô tả cụ thể chỉ là `OPEN → VALIDATION_PENDING`. Chưa có quy tắc CAS cho `OPEN/QUARANTINED → OPEN/PENDING`, hoặc định nghĩa receipt/response của lần retry.

**Tình huống/tác động:** scanner timeout để session ở `QUARANTINED`; request complete bằng key mới có thể bị xem là invalid transition, khiến resource được mô tả là retryable nhưng không thể retry.

**Cần sửa:** ghi rõ transition, điều kiện version/lifecycle, receipt mới và hành vi duplicate cho lần scan retry; thêm acceptance case timeout rồi retry.

### P2 — Core upload DTO và schema chưa được đối chiếu đầy đủ với DTR

**Vị trí:** [V7 upload request](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V7_DRAFT_20261102.md:108>), [V7 schema/migration gate](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V7_DRAFT_20261102.md:137>); [DTR upload session](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md:307>).

DTR hiện liệt kê `target_ref` và các purpose `PROFILE_IMAGE`, `RUN_ARTWORK`, `RUN_AUDIO`, `LESSON_SOURCE`. V7 thêm `RUN_ARTWORK_ORIGINAL` nhưng không đưa `target_ref` vào request upload. Acceptance yêu cầu sửa DTR trước migration, nhưng chưa nêu các mục này hoặc cách hòa giải idempotency giữa session và bảng receipt.

**Tình huống/tác động:** trước migration, người triển khai/UI chưa biết session phải bind với run thế nào, purpose ảnh gốc được lưu ra sao, và schema nào giữ idempotency canonical.

**Cần sửa:** đưa purpose ảnh gốc, target/scope, receipt ownership và các ràng buộc owner vào DTR/OpenAPI amendment trước migration. Phần `organization_id` nullable, backfill org legacy và typed Parent scope **phù hợp về hướng** với DTR §4.2/§5.1; cần chốt check constraint/FK cụ thể trong amendment.

### P3 — Report V4/V5 gốc vẫn chưa được archive

**Vị trí:** [V7 traceability note](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V7_DRAFT_20261102.md:165>).

Checkout có report nguyên văn V3/V6 và các draft V4/V5, nhưng không có report review gốc V4/V5. V7 đánh dấu crosswalk V4/V5 là tái dựng, không tuyên bố đã lưu report nguyên văn. Đây là **archive gap còn mở**, nhưng không chặn triển khai nếu không gọi crosswalk là archive đầy đủ.

## Đối chiếu toàn bộ finding V6

| Finding V6 | Đánh giá nội dung V7 |
|---|---|
| P1-1: sync worker chặn polling | Đã xử lý ở mức thiết kế: executor riêng, capacity gồm queued + running = 1, control path riêng, 503 trước receipt. |
| P1-2: race part/complete/abort và PENDING | Row lock/CAS, một dispatcher và recovery hold đã nêu. Retry từ `QUARANTINED` còn thiếu transition cụ thể (P2 ở trên). |
| P2-1: mất lock không fence worker cũ | Epoch kiểm tra ở claim/mark_sent, CAS run head và không resend sau SENT đã được quy định. |
| P2-2: upload thiếu part thành terminal | 422 không consume key, giữ resumable/RECEIVING và test resume đã có. |
| P2-3: purge mất sau crash | Tombstone bền và startup/periodic sweeper idempotent đã có. |
| P2-4: Parent scope và READY/COMPLETED | Typed scope, backfill legacy và `COMPLETED/CLEAN → READY` rõ; DTR purpose/target cần được hoàn thiện. |
| P2-5: StoryPhoto bị gắn LIVE | Optional server-controlled evidence kind và regression canvas đã có. |
| P2-6: decoder overclaim | V7 không tuyên bố decoder hiện tại đã sandbox; yêu cầu subprocess có timeout/memory cap cho normalized và original, fail readiness nếu không enforce. Acceptance phù hợp. |
| P2-7: API lệch SRS/thiếu poll schema | Một phần đã sửa, nhưng còn các lệch và trường poll nêu ở P2. |
| P2-8: receipt hết hạn trước replay | No TTL cho receipt pilot; tombstone/replay được giữ qua expiry/purge. Còn phụ thuộc sửa scope idempotency của create. |
| P2-9: thiếu V3 P1 trong crosswalk | Đã liệt kê đủ 5 P1/4 P2 V3. |
| P3: archive report lịch sử | V4/V5 vẫn chưa có report gốc; V7 ghi đúng đây là limitation. |

Crosswalk V7 cũng có đủ các số lượng được ghi nhận: V3 **5 P1/4 P2**, V4 **2/2**, V5 **1 P1/2 P2/1 P3**, V6 **2 P1/9 P2/1 P3**. V4/V5 vẫn là tái dựng từ draft và crosswalk, không thể coi là nguồn review nguyên văn.

## Các điểm bắt buộc khác

Worker topology, epoch fence, StoryPhoto dùng đúng kiểu wire V2 qua A1 transport/guard, hook lỗi sau SENT thành UNKNOWN, hai loại hash tách biệt, và AV CLEAN ràng buộc digest của từng asset đều được nêu đủ rõ ở mức acceptance. Source HEAD xác nhận guard hiện finalize trước khi trả outcome và ép evidence LIVE; V7 đã đề xuất hook/evidence override cho StoryPhoto. Decoder HEAD hiện chạy trong tiến trình, nên subprocess/kill/resource-cap là điều kiện nghiệm thu tương lai, chưa phải chứng cứ đã có.

S1+S2 chỉ mở sau owner approval riêng; dùng fake/HTTP loopback, Modal thật là readiness/approval gate riêng; A2 bị loại khỏi DB test và acceptance yêu cầu DB disposable mới kèm bằng chứng tạo/xóa. Các ranh giới này rõ. Các owner decisions và deviations vẫn được ghi là chờ duyệt.

Không chạy test/validator, không truy cập DB/provider/network và không sửa file hay approval/status.
