# FEAT-064 T0 — Kế hoạch chốt hợp đồng, guard và manifest thực thi (DRAFT)

- Trạng thái: **DRAFT** — kế hoạch làm tài liệu, không phải approval triển khai. T0 **chỉ là tài liệu** (theo bảng T0 của `PLAN.md` §5): không sửa code, không migration, không chạy backend/DB/MinIO/Modal/GPU/test, không đổi approval, không ký thay ai.
- Ngày: 2026-10-31. Plan cha: `plan/PLAN.md` rev6 (SHA-256 `CD7B3236A55E280D4722166C73AF462835DEC8503BCE882CE0CFF9D5601F9665`, DRAFT / NOT_STARTED). Mục T0: M0 trong §4 và dòng T0 trong §5.
- Mục đích: sau T0, owner có đủ hồ sơ để **ghi approval cho T1 (sửa code BE1 để chạy được đường hợp lệ)** và các task sau, đi tới một lần gọi Modal thật có kiểm soát (T13). T0 là cổng cuối trước khi có dòng code đầu tiên.
- Người đọc: owner, owner BE1, owner BE2/integration, người review độc lập.

## 1. Đầu vào phải ghim (ghi hash vào đầu tài liệu kết quả)

| Đầu vào | Dùng để |
|---|---|
| `plan/PLAN.md` rev6 (§3 điểm chặn, §4 mốc, §5 T0–T14, §6 hợp đồng, §7 AC01–AC20, §8 OD, §12–§13 witness/UNKNOWN) | Phạm vi và tiêu chí |
| `DECISIONS.md` D-01…D-09 và P-01…P-11 | Quyết định đã chọn và đề xuất |
| `plan/CONTRACT_OUTLINE_DRAFT.md` (A–F), `plan/ELIGIBILITY_GUARD_INVENTORY_DRAFT.md` (14 dòng), `plan/OWNER_PATH_MANIFEST_DRAFT.md` (18 ranh giới) | Điểm xuất phát, đều là bản nháp |
| `../FEAT-063-system-architecture-rearchitecture/evidence/OWNER_DECISION_SLIP_20261031.md`, `B3_OWNERSHIP_MIGRATION_MANIFEST_20261031.md`, `B3_OWNER_MATRIX_20261031.csv` | Quyết định owner (B1–B8) và ma trận ownership; chữ ký còn `CHƯA KÝ` |
| `../FEAT-063-.../plan/PLAN_REV36_BACKEND_SRS23_ALIGNMENT_20261029.md` (S2, OD-2/OD-7/OD-13) | Chồng lấn schema synthetic |
| `evidence/notes/SOURCE_REVIEW_20261029.md` | Dòng mã gốc đã rà |
| `deployment/modal/qwen_vision_v2.py`, `backend/src/.../infrastructure/ai/lightning_vision_v2.py`, `application/ports/*.py`, `interfaces/http/routers/be1_*.py`, `be1_runtime.py`, `infrastructure/persistence/be1_models.py`, `backend/alembic/versions/` | Đọc tĩnh để xác minh mọi dòng mã trích dẫn tại HEAD hiện tại |

## 2. Quyết định owner đã có (không hỏi lại)

Theo phiếu quyết định 2026-10-31: BE2 là Person 2 như ngoại lệ trong phạm vi FEAT-064; phương án migration **X** (pilot T1 sở hữu migration biểu diễn synthetic, Rev36 S2 tái dùng), chủ schema là owner BE1; `OwnerFenceV1` cần ba chữ ký (BE1, BE2, integration) trước T7b; pilot đi trước Rev36; chưa cho DB tạm; T13 (Modal thật) xin approval riêng sau T12 kèm chấp nhận rủi ro dư. Cùng D-03 (witness file local, OD-3=B), D-04…D-09. **Chưa có:** tên P4, chữ ký thật, người review từng file, xác nhận riêng của owner BE1.

## 3. Nguyên tắc

1. **Mỗi khẳng định về code có dẫn nguồn `đường dẫn:dòng` đã mở lại tại HEAD hiện tại.** Dòng trong bản nháp (baseline `529cbef9`) có thể đã lệch; không chép.
2. **Không ký, không chọn thay owner.** Chỗ chưa có quyết định → `NEEDS_OWNER` + câu hỏi cụ thể (tối đa 10).
3. **Không đổi nghĩa legal consent.** Proof synthetic là loại bằng chứng riêng; không tạo `effective` giả, không nới ràng buộc dữ liệu thật; REAL/LEGACY_UNCLASSIFIED vẫn bị từ chối.
4. **Không mô tả như đã chạy.** Mọi test/hành vi là "dự kiến"; không ghi pass.
5. **Một đề xuất cụ thể mỗi hợp đồng**, kèm lý do ngược lại; không để T1 phải tự quyết khi code.

## 4. Các bước

| Bước | Việc | Đầu ra | Xong khi |
|---|---|---|---|
| S0 | Preflight: đọc `AGENTS.md`, `.codex/sketch2life-harness.md`; `git status`/`git log`; hash đầu vào; kiểm mục approval T0 trong `approvals/TASK_APPROVAL.md` của FEAT-064 khớp hash plan này; kiểm 8 file local owner giữ | Khối preflight | Khớp; nếu thiếu approval thì dừng |
| S1 | **Mang quyết định vào:** bảng nối từng quyết định trong phiếu (B1–B8, C…) tới điều khoản T0 bị ảnh hưởng; liệt kê điều kiện B3 còn mở (P4, chữ ký, người review, xác nhận owner BE1) thành **cổng chặn** có trạng thái | Bảng quyết định → T0 và bảng cổng | Mỗi cổng có người chịu trách nhiệm hoặc `NEEDS_OWNER` |
| S2 | **Guard eligibility (14 điểm):** mở lại từng điểm trong inventory và mọi caller của `consent_is_effective`, `deny_pending_consent`, `ConsentRecordModel.state == "effective"`; ghi hành vi hiện tại, bước lifecycle (create profile → join → admit → Start → group → turn → draw → export), disposition đề xuất (**nhận proof synthetic riêng** / **giữ nguyên** / **ngoài lifecycle, vẫn từ chối**), test dự kiến (dương và âm), owner ghi | `T0_GUARD_DISPOSITIONS_20261031.csv` + bảng trong md | 14 dòng gốc đều có disposition; mọi caller thêm vào được báo cáo; không điểm nào "blanket bypass" |
| S3 | **Hợp đồng proof synthetic và biểu diễn schema (phương án X):** viết `SyntheticDevEligibilityEvidenceV1` (trường, ai tạo, ai đọc, hết hạn, thu hồi, phiên bản), cột/CHECK đề xuất cho `be1_managed_profiles` (consent ref nullable theo origin, `data_origin`), so từng thuộc tính với Rev36 S2 và nêu chỗ khác enum/CHECK; nêu revision cha Alembic (đọc tĩnh), backfill `LEGACY_UNCLASSIFIED`, downgrade, và rằng không có DB tạm thì T1 nghiệm thu bị BLOCKED | Mục hợp đồng + DDL dạng văn bản (chưa phải migration) | Mọi khác biệt với S2 có kết luận; không ghi migration thật |
| S4 | **Nguồn → render → admission:** chốt `CanvasOperationProfileV1`, `CanvasSourceExportV1`, `RenderDerivationReceiptV1`, `VisionAdmissionBindingV1`; đưa **giá trị cụ thể** cho OD-1 (D-04): tỉ lệ, kích thước pixel, bảng 5 màu, quy đổi độ dày, cap/join/dot, mã hóa xác định (Pillow RGB PNG), giới hạn kích thước theo admission; mô tả export nhất quán tại epoch/revision | Mục hợp đồng | Mỗi trường có kiểu và giới hạn; nêu rõ cái gì bị từ chối (history, overlay, gallery) |
| S5 | **Gateway và projection:** đặt tên đường dẫn, phương thức, xác thực, mã lỗi (export, request Vision, cancel own, status-own, Teacher pending list/read); trả "accepted" sớm (timeout Child API 12s); status-own theo D-06/D-09 (active hoặc paused; khóa thiết bị, grant, membership, Child, canvas, eligibility; finished/revoked/rotated bị từ chối); projection UNKNOWN và NOT_SENT_* theo §13 | Mục hợp đồng | Mỗi capability có ma trận quyền và mã lỗi |
| S6 | **Quan sát runtime, guard gọi ngoài, retry/deadline:** định nghĩa `InvocationGuardPort`; chính sách pilot `max_attempts=1`; công thức `attempt_deadline > elapsed_pre_send + enforced_HTTP_wall_deadline + completion_margin`; liệt kê các giới hạn **đo được từ nguồn** (Modal `timeout=150`, `startup_timeout=300`, `scaledown_window=30`, `max_containers=1`; client Child 12s) và một mẫu đo 23,938 s; ghi cái **chưa chứng minh** (wall deadline của `urlopen`), đề xuất cách enforce hoặc chính sách late-response | Mục chính sách | Mỗi con số có nguồn; không suy từ một mẫu |
| S7 | **Trạng thái bền tối thiểu (T7a):** kiểm kê từng method của cổng assistance/analysis/UoW thật sự được đường chọn gọi (đọc `application/ports/*.py` và store hiện có); mỗi method: cần bền, nguyên tử, chỉ đọc, hoặc fail-closed; test | `T0_METHOD_INVENTORY_20261031.csv` | Không method nào "silent no-op"; phạm vi không phình thành toàn bộ BE2 |
| S8 | **`OwnerFenceV1` và analysis-only (T7b):** phiên bản đề xuất, ranh giới owner, linearization/UoW tại điểm commit, zero SketchIntent/event/outbox/SketchStage kể cả replay/restart; ghi ba chữ ký cần có (BE1, BE2, integration) ở trạng thái chưa ký | Mục hợp đồng | Acceptance atomic nêu rõ; không giữ transaction DB qua GPU |
| S9 | **Run manifest, witness (T7c) và rủi ro dư:** đặc tả witness file trên Windows (tạo độc quyền, chuyển trạng thái nguyên tử, flush file và xử lý thư mục), ma trận cửa sổ lỗi (§13), kế hoạch thử throwaway ở T12, và **văn bản chấp nhận rủi ro dư** soạn sẵn để owner ghi vào approval M3 | Mục đặc tả + văn bản rủi ro | Mỗi cửa sổ lỗi có kết quả bảo thủ; M3 bị BLOCKED nếu thiếu T12 |
| S10 | **Manifest thực thi T1–T12:** mỗi task: file, hunk, hash baseline tại HEAD, writer/reviewer (từ B3), test được phép, phạm vi DB tạm (chỉ DB `*_be1_acceptance` sau approval), phạm vi provider (không có trước T13), thứ tự migration, điều kiện bắt đầu | `T0_EXECUTION_MANIFEST_20261031.csv` | Mọi file trong 18 ranh giới B3 có hàng; không wildcard |
| S11 | **Gói approval soạn sẵn:** văn bản đề nghị approval cho T1 (code), T12 (DB tạm, test) và T13 (Modal thật, một lần gọi, chấp nhận rủi ro dư) kèm chỗ pin hash; chưa ghi vào approval | Mục gói approval | Mỗi gói nêu scope, loại trừ, hash cần pin |
| S12 | **Lệch trong plan rev6:** liệt kê chỗ plan còn nhắc Rev33 thay vì Rev36, bảng OD §8 vs D-04…D-09, tham chiếu stale; đề xuất nội dung rev7 (chỉ liệt kê, không sửa plan) | Mục lệch | Mỗi lệch có dòng nguồn |
| S13 | **Câu hỏi cho owner** (tối đa 10) và tự kiểm (§6); chạy `validate_harness`, `validate_repository_security`, `validate_architecture`, `git diff --check` | Bảng câu hỏi + bảng kiểm | Cả bốn exit 0 |

## 5. Sản phẩm

Trong `features/FEAT-064-current-flow-modal-vision-dev/evidence/`:
- `T0_CONTRACT_FREEZE_20261031.md`: giới hạn, hash đầu vào, S1–S13.
- `T0_GUARD_DISPOSITIONS_20261031.csv` (S2), `T0_METHOD_INVENTORY_20261031.csv` (S7), `T0_EXECUTION_MANIFEST_20261031.csv` (S10); UTF-8.

## 6. Kiểm tra bắt buộc

1. 14/14 điểm guard gốc có disposition; caller mới tìm thấy được ghi.
2. Mọi trích dẫn `path:line` mở lại được tại HEAD; không dòng nào chép từ baseline `529cbef9` mà chưa kiểm.
3. Không chỗ nào ghi pass, ký hoặc approved cho thứ chưa có (FEAT-064, Rev36, T-N, chữ ký).
4. Proof synthetic không bị mô tả như consent hiệu lực; REAL/LEGACY vẫn từ chối.
5. Mỗi con số thời gian có nguồn; một mẫu 23,938 s không được dùng làm deadline.
6. Hàng nào cần quyết định chưa có là `NEEDS_OWNER` kèm câu hỏi.
7. Không file nguồn nào bị sửa; không đường dẫn tuyệt đối local, token, dữ liệu trẻ.

## 7. Ranh giới

- Không sửa: `backend/`, `apps/`, `deployment/`, migration, SRS, register, ADR, DECISIONS (cả FEAT-063 và FEAT-064), plan FEAT-064/Rev36, mọi file approval (kể cả FEAT-064), B0–B3 và phiếu quyết định, 8 file local owner giữ.
- Không chạy dịch vụ/test/DB/Alembic, không gọi Modal hay GPU, không đọc token hay `.env`.
- Commit theo quy tắc owner: một task một commit, chỉ khi owner yêu cầu; không tự đẩy.

## 8. Điều T0 KHÔNG làm

T0 không cho phép sửa code, không là approval T1…T13, không chạy thử Modal, không thay thế chữ ký `OwnerFenceV1`. Sau T0, **mỗi** bước code/DB/live vẫn cần mục approval riêng pin đúng hash.

## 9. Thứ tự sau T0 (tham chiếu, không tạo task mới)

T0 → approval T1 → T1 (BE1 eligibility, đường hợp lệ) cùng T3/T6/T7a theo manifest → T2/T4/T5 → T7b/T7c → T8 → T9 → T10/T11 → T12 (CPU + DB tạm, cần approval) → approval live → T13 (một lần gọi Modal) → T14.

## 10. Câu hỏi dự kiến cho owner sau T0

Người review từng file; tên P4; xác nhận của owner BE1 cho phương án X; ba chữ ký `OwnerFenceV1` khi nào; giá trị OD-1 cụ thể (tỉ lệ, màu, pixel); chính sách late-response của HTTP; phạm vi DB tạm cho T12; nội dung rủi ro dư; có sửa plan rev6 thành rev7 không.
