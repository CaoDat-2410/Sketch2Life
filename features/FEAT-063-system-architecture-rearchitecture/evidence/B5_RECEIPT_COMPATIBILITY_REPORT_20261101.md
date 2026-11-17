# B5 — Tương thích idempotency receipt Parent Group

Ngày thực hiện: 2026-11-01 (Asia/Saigon)
Phạm vi: đọc và sửa code/test cục bộ theo approval B5; không đọc `.env` hoặc token, không đọc/ghi database, không chạy Alembic, Modal, GPU hay mạng ngoài.

## P0 — Mốc và ca gộp

- Nhánh: `feature/feat063-be-foundation`.
- HEAD trước B5: `b111916ef4089b5ca1273de520cbeb9c1d47ae90`; parent: `6910b603daac4f7f75bd090467d57f7ed7ea8ec3`.
- HEAD là hậu duệ của `6910b603`; nhánh remote có ahead/behind `0 1`; index ban đầu rỗng. Đây là **Ca X**.
- Bộ test mốc P0: 273 passed, 4 skipped.
- Mypy `--strict` trên `service.py` và `contracts/schemas/lesson_library.py`: 30 lỗi nền đã có trước B5.

## P1 — Kiểm kê receipt mang `revision`

Receipt được khóa bởi `(organization_id, principal_ref, operation_scope, idempotency_key)` và mang `request_fingerprint`. Commit `08459372` thêm trường `revision` vào response của hai thao tác membership dưới đây. Receipt đã lưu trước thay đổi đó không có trường bắt buộc này nên không còn khớp response contract hiện tại. Chưa có bằng chứng cho biết database thật nào có receipt cũ; đây là rủi ro tương thích suy ra từ source, không phải sự cố đã quan sát.

| Operation scope | Route / response model | Receipt trước `08459372` | Sau `08459372` | Cách đọc để dựng revision hiện tại |
|---|---|---|---|---|
| `POST /organizations/{organization_id}/parent-groups/{group_id}/invitations` | `POST /organizations/{organization_id}/parent-groups/{parent_group_id}/invitations`; `ParentGroupInvitationV1` | `contract`, `membership_id`, `parent_group_id`, `state`, `invited_at`, `expires_at`, `accepted_at` | Các trường cũ + `revision` | Tìm membership bằng `membership_id` và `parent_group_id` trong receipt; join Parent Group để ràng buộc `organization_id`. |
| `POST /me/parent-group-invitations/{membership_id}/accept` | `POST /me/parent-group-invitations/{membership_id}/accept`; `ParentGroupMembershipV1` | `contract`, `membership_id`, `parent_group_id`, `state`, `invited_at`, `expires_at`, `accepted_at` | Các trường cũ + `revision` | Tìm theo `membership_id`, join Parent Group để ràng buộc `organization_id`, đồng thời ràng buộc `parent_principal_ref` bằng principal của receipt/actor hiện tại. |

Hai lookup chỉ đọc bảng membership hiện tại. Nếu không còn hàng khớp, receipt không được replay thành công giả; trả lỗi tương thích typed qua HTTP 409 `IDEMPOTENCY_RECEIPT_INCOMPATIBLE`. Revision trả về có thể mới hơn revision tại thời điểm phát hành receipt; `revision_source` làm rõ provenance này.

Các operation receipt khác có response revision-bearing nhưng không bị `08459372` đổi hình response: `POST /organizations/{organization_id}/lessons` (`LessonDetailV1`); `POST /organizations/{organization_id}/lessons/{lesson_id}/access-grants` (`LessonAccessGrantV1`); `POST /organizations/{organization_id}/access-grants/{grant_id}/decision` (response quyết định access grant, replay trực tiếp); `POST /me/lesson-invitations/{access_grant_id}/{action}` (`LessonAccessGrantV1`); và `PATCH /platform/lessons/{lesson_id}/moderation` (`LessonModerationV1`). Parent Group creation (`ParentGroupV1`), upload-session và upload-complete receipts không chứa revision membership bị thêm trong commit đó. Các list/revoke membership không dùng command receipt.

## Quyết định và thay đổi

- Áp dụng phương án A: nâng cấp tại thời điểm `_replay`, không ghi lại `response_json`.
- `revision_source` là trường tùy chọn đóng trong `ParentGroupMembershipV1` và `ParentGroupInvitationV1`, mặc định `None`; giá trị provenance khi nâng receipt cũ là `reconstructed_from_current_row`. Response hiện hành không được gán provenance hồi tố.
- Pure helper `receipt_compat.py` chỉ nhận diện chính xác hai operation scope đã duyệt, kiểm tra hình receipt, xác định lookup key và dựng response mới từ receipt cùng revision của hàng hiện tại; helper không truy cập DB, router hay đồng hồ.
- `_replay` vẫn kiểm tra fingerprint trước; key dùng lại với fingerprint khác giữ nguyên lỗi 409 `IDEMPOTENCY_KEY_REUSED`. Lookup được lọc theo membership/group/organization, và với accept còn theo principal. Lỗi receipt hỏng hoặc thiếu membership được ánh xạ thành lỗi typed 409.
- Không sửa `_idempotent` write path, không ghi lại receipt, không tạo membership/audit/outbox. Response đúng hình hiện tại được helper trả nguyên trạng.

## P3 — Test đỏ trước implementation

Chạy test offline mới trên HEAD trước khi triển khai: **5 failed, 2 passed**. Các ca đỏ xác nhận thiếu đường tương thích receipt cũ, lỗi khi membership không còn, và lỗi receipt hỏng chưa được chuyển thành lỗi tương thích có kiểm soát; các ca fingerprint và cô lập identity đã có hành vi đúng.

## P6 — Kiểm chứng sau implementation

| Kiểm tra | Kết quả thật |
|---|---|
| 5 test file CI, test unit B5 mới, và toàn bộ test integration Lesson Library (không cấu hình `BE1_TEST_DATABASE_URL`) | **34 passed, 10 skipped**. Bốn test PostgreSQL BE1 và sáu test PostgreSQL Lesson Library bị skip theo fixture hiện có; test replay receipt B5 cũng nằm trong sáu test bị skip. |
| Ruff check 5 file sửa/tạo, `--config backend/pyproject.toml` | Lệnh có exit 1 do **42 diagnostic** hiện có. So sánh baseline `HEAD` trên ba file đã tồn tại: baseline 44, hiện tại 42, **0 diagnostic mới, 2 đã hết**. Hai file Python mới không có diagnostic Ruff. |
| Ruff format check trên 2 file Python mới | **2 files already formatted**. |
| Mypy strict trên 5 file | 40 lỗi trong 3 file đã tồn tại: 30 lỗi ở `service.py`/contract, bằng mốc P0; 10 lỗi cũ trong integration test. Không có lỗi trong helper/unit test mới hoặc phần test B5 được thêm. |
| Mypy strict riêng helper và unit test mới | **Success: no issues found in 2 source files**. |
| `validate_harness.py` | `HARNESS_VALID` (approval gate và frontend asset gate enabled). |
| `validate_repository_security.py` | `REPOSITORY_SECURITY_VALID`; quét 5,955 file publishable, không phát hiện absolute machine paths. |
| `validate_architecture.py` | `ARCHITECTURE_VALID`; các kiểm tra hướng phụ thuộc và ranh giới hiện có đều valid. |
| `git diff --check` | Không có output; exit 0. |

## P5 — Review độc lập

Một subagent chỉ đọc đã rà allowlist, giữ nguyên kiểm tra fingerprint/409, đường replay không ghi DB, độ phủ hai scope, provenance, contract và test đỏ/xanh. **Không có finding chặn**. Review không truy cập DB và không thay thế xác nhận của owner/BE1.

## File B5 và SHA-256

| File | SHA-256 |
|---|---|
| `backend/src/sketch2life/infrastructure/lesson_library/service.py` | `FB03E0077BD03B0672C5F40242E6848A8521B76AEF58F56A6AE08447ABE52A70` |
| `backend/src/sketch2life/contracts/schemas/lesson_library.py` | `DABD7F1AC9C8E171ECBDC658921D00178B785833D53FE577BC04B30A27D5585F` |
| `backend/src/sketch2life/infrastructure/lesson_library/receipt_compat.py` | `BC22DC7982D601397997FECA223A61A1392B4392EE24D7F21B9F756ED1F60A47` |
| `backend/tests/unit/test_lesson_library_receipt_compatibility.py` | `F32708D26500A49AF55D072984378CCD745BF384037B38DFEB1A730DD5B73A50` |
| `backend/tests/integration/lesson_library/test_lesson_library_api.py` | `ECBFCB03A1E73EBE4D7F213C3F7788C1F0A083C37C96EA0C636D4DDBCF7A90DE` |
| `features/FEAT-063-system-architecture-rearchitecture/plan/B5_PARENT_GROUP_RECEIPT_COMPATIBILITY_PLAN_20261031.md` | `6E36A982265F00EA53F33B7E5AC0EFD957F433317ED53A03D5C1AED91813DA79` |
| `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md` | `DA2B2C0C6C7E4E8085A07683B425D310B2910098EF416E67EB0C48A1FDD8819D` |

The hash of this report is recorded in the final task response because it cannot contain its own final hash.

## Giới hạn

Không đọc database thật nên chưa biết có receipt cũ nào đang được lưu. Không chạy test PostgreSQL replay B5; test đó chỉ chạy khi `BE1_TEST_DATABASE_URL` trỏ tới database acceptance dùng riêng. Không chạy Alembic, Modal/GPU, không push. Bảy file local-only của owner được giữ nguyên.
