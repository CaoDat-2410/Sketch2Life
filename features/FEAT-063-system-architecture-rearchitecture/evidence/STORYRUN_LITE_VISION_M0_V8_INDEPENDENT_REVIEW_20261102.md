# NEEDS_REVISION

**Baseline khớp:** các hash được ghim, HEAD `a88de875ff92e9b4d4fa5cc2f5f8d5fc1f626f58` và branch `feature/feat063-be-foundation` đều đúng. Không có P0/P1. Có **4 finding P2** cần xử lý trước khi chấp nhận V8 và mở goal S1+S2.

V7 P1 về collection-scoped idempotency, P2 về status/poll DTO và transition retry từ `QUARANTINED` đã được xử lý ở mức thiết kế. V7 P2 về DTR mới được giải quyết một phần; các vấn đề còn lại nằm dưới đây.

## Findings

### P2 — Số đếm DTR chưa bao gồm Rev31, và tên cột part không thống nhất

**Vị trí:** [V8 §5](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V8_DRAFT_20261102.md:140>); [DTR §1](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md:33>), [§5.1](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md:308>), [§14.4](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md:692>).

**Tình huống/tác động:** Phép tính `51/89/137 → 53/91/139` đúng cho baseline v2.3 ở §14.1. Nhưng DTR hiện đã tính thêm ba bảng hỗ trợ Rev31, nên crosswalk hiện hành là `54/92/140`; sau hai bảng receipt phải là `56/94/142`. Nếu chỉ áp dụng số V8, các tổng hiện hành và tổng v2.3 sẽ mâu thuẫn. Cùng amendment đó, V8 dùng `part_no` trong D16/luồng upload, nhưng DTR và tiêu chí acceptance dùng `part_number`.

**Sửa chính xác:** Giữ riêng hai lớp số đếm: baseline sau amendment `53/91/139`, crosswalk sau Rev31 `56/94/142`. Cập nhật các tổng và owner counts tại §1, §2.1, §5, §6, §11, §14.1 và §14.4; Core thành 9 bảng, Story thành 10. Dùng `part_number` nhất quán cho cột DB và nêu rõ `part_no` chỉ là tham số route, hoặc ghi rõ migration đổi tên cột và cập nhật mọi chỗ liên quan.

### P2 — Story review decision còn unique idempotency riêng

**Vị trí:** [V8 D14](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V8_DRAFT_20261102.md:46>); [DTR `story.review_decisions`](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md:375>) và [§6 relationship](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md:450>).

**Tình huống/tác động:** D14 phân biệt receipt theo `operation`, còn DTR vẫn yêu cầu `review_decisions` unique theo run và `idempotency_key`. Hai loại review operation trên cùng run có thể được phép theo identity của receipt nhưng bị unique constraint thứ hai từ chối.

**Sửa chính xác:** Để `story.command_receipts` làm nguồn chuẩn cho replay và key conflict. Bỏ unique idempotency riêng khỏi `review_decisions`, hoặc thay trường đó bằng `receipt_id` không có quyền replay độc lập; cập nhật §5.6, §6 và §7.

### P2 — Recovery Core không chốt receipt `PENDING` bị bỏ lại

**Vị trí:** [V8 D16/D18](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V8_DRAFT_20261102.md:48>), [§3 bước complete](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V8_DRAFT_20261102.md:58>) và [bước startup recovery](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V8_DRAFT_20261102.md:62>).

**Tình huống/tác động:** Process chết sau khi commit session/receipt `PENDING` nhưng trước queue ack hoặc trước khi chốt `FINAL`. Startup chuyển session sang `QUARANTINED` và giữ receipt, nhưng không quy định chốt receipt cũ. Retry đúng key có thể chờ dispatcher đã mất mãi; key đó cũng không dùng lại được.

**Sửa chính xác:** Recovery phải chốt receipt mồ côi thành một response snapshot ổn định, chẳng hạn `409 UPLOAD_SESSION_STATE_CONFLICT` kèm state version hiện tại. Retry đúng key chỉ replay snapshot đó, không dispatch; retry validation tiếp theo dùng key mới và `If-Match` hiện hành. Thêm acceptance cho crash giữa commit PENDING và finalize.

### P2 — Acceptance chưa kiểm tra bước người lớn `CONFIRM`

**Vị trí:** [V8 API contract](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V8_DRAFT_20261102.md:108>) và [§5 acceptance](</D:/GitHub/Sketch2Life/features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V8_DRAFT_20261102.md:132>).

**Tình huống/tác động:** Contract mô tả `subject-confirmation` trả 202 và GET sau đó hiện `PREPARATION_REVIEW`, nhưng acceptance không yêu cầu chạy lệnh này. Goal có thể qua các gate OpenAPI/AV/Vision mà chưa chứng minh được flow kết thúc bằng xác nhận của người lớn.

**Sửa chính xác:** Thêm kịch bản acceptance/Bruno chạy flow synthetic đến kết quả, gửi `CONFIRM` với understanding revision hiện hành, kiểm tra 202 và GET trả `PREPARATION_REVIEW`. Retry cùng key phải replay snapshot, không tạo decision hay Vision attempt thứ hai; revision cũ phải trả `409 STALE_REVISION`.

## Giới hạn archive và bằng chứng

Khoảng trống report V4/V5 là **không chặn**: V8 công khai đây là bản tái dựng từ draft/crosswalk. Các số V3 `5/4`, V6 `2/9/1` và V7 `1/3/1` khớp report gốc; số V4 `2/2` và V5 `1/2/1` chỉ đối chiếu được với bản tóm tắt tái dựng, không thể xác minh từ report gốc đang thiếu.

Tại HEAD, guard hiện vẫn finalize trước khi trả kết quả và gắn evidence `LIVE_LEGACY_BRIDGE`; `ObservationRequest` vẫn yêu cầu `render`; decoder hiện gọi PyAV trong tiến trình. V8 nêu rõ các thay đổi/gates tương lai cho hook, StoryPhoto evidence và decoder cô lập, nên tôi không xem chúng là đã triển khai. Chỉ dùng `git show HEAD:<path>` để xem implementation; không dùng thay đổi A2 cục bộ làm bằng chứng.

Không chạy test/validator, không truy cập DB/provider/network và không sửa file. Goal S1+S2 vẫn cần approval riêng; Modal thật vẫn là readiness và approval gate riêng.
