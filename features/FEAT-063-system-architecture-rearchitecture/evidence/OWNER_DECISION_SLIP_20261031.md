# Phiếu quyết định của owner — FEAT-063 (2026-10-31)

## 1. Nguồn và thời điểm ghi nhận

- Ghi nhận: 2026-10-31 00:58:06 Asia/Saigon (giờ máy).
- Người quyết: owner dự án. Căn cứ: owner xem phiếu đề xuất (mã A1–D2) cùng phần giải thích lý do từng mục, rồi trả lời "ok chốt đi ổn đó" trong cuộc trò chuyện, tức là chấp nhận **tất cả các lựa chọn đề xuất** của phiếu. Dòng trả lời phiếu: `A1:a A2:a B1:a B2:a B3:X B3b:a B4:a B5:b B6:a B7:a B8:a C2:a C3:a C4:a C5:a C6:a C7:a C8:a C9:a C10:a D1:a D2:a`.
- Tài liệu liên quan: [manifest B3](B3_OWNERSHIP_MIGRATION_MANIFEST_20261031.md) mục 9 (8 câu hỏi owner), [bản ghi quyết định B2](B2_OWNER_DECISION_A_20261030.md) và [kế hoạch B2A](../plan/B2A_SRS_REGISTER_AMENDMENT_PLAN_20261030.md).

## 2. Quyết định đã chốt

### A. Đóng B3
| Mã | Quyết định |
|---|---|
| A1 | Commit B3 nguyên bản (hai ghi chú review về cột `shared_file` và 5 file overlap được ghi vào báo cáo, không sửa file kết quả). |
| A2 | Gom thành một commit rồi đẩy một lần. |

### B. Pilot FEAT-064 (tương ứng 8 câu của manifest B3, mục 9)
| Mã | Câu B3 | Quyết định |
|---|---|---|
| B1 | Câu 1 | `AnhKhoaa157` là BE2 theo D-08 như **ngoại lệ chỉ trong phạm vi FEAT-064**; không sửa ADR-0015. |
| B2 | Câu 2 | File BE1 do `CaoDat-2410` ghi; file BE2 do `AnhKhoaa157` ghi; `app.py` và `router_composition.py` do `AnhKhoaa157` ghi (integration owner, D-07) với P4 review. Người review cụ thể cho từng file X01–X18 vẫn cần ghi ở T0. |
| B3 | Câu 3 | Phương án migration **X**: pilot T1 sở hữu migration biểu diễn synthetic, Rev36 S2 tái dùng. Cần so enum/CHECK giữa D-05 và S2 trước khi áp dụng. |
| B3b | Câu 3 | Chủ sở hữu schema `data_origin`/consent là owner BE1 (`CaoDat-2410`). |
| B4 | Câu 4 | `OwnerFenceV1` cần ba chữ ký (owner BE1, owner BE2, integration owner) trước khi bắt đầu T7b. |
| B5 | Câu 5 | Chưa có tên P4. `AnhKhoaa157` giữ composition; P4 review sau khi có người. |
| B6 | Câu 6 | Pilot FEAT-064 đi trước, Rev36 S1/S2/S3 sau. S1 không phải điều kiện của pilot. |
| B7 | Câu 7 | Chưa cho DB tạm; chỉ cho khi có plan T12 và phạm vi ghi bằng văn bản. |
| B8 | Câu 8 | Approval FEAT-064 T0 sau khi chốt B1–B5; T13 (gọi Modal thật) riêng, sau T12, kèm chấp nhận rủi ro. |

### C. Hoạt động của Parent (B2/B2A; Q1 = A đã chốt trước đó)
Các mục C2–C8 tương ứng Q2–Q8 của mục S6 trong crosswalk B2. Từ bản ghi này, Q2–Q8 **không còn là giả định chưa xác nhận** mà là quyết định của owner theo nội dung dưới đây.

| Mã | Quyết định |
|---|---|
| C2 (Q2) | Run của Parent có thể mang tham chiếu lesson-version tùy chọn, kiểu opaque, qua cổng của module Lesson; không có org/class/occurrence của Teacher. Run không có lesson vẫn chạy, không hiện danh sách hoạt động và không thay bằng catalog. Vị trí lưu tham chiếu chưa chốt. |
| C3 (Q3) | Parent không cần `activity_ref` làm tiền điều kiện; Teacher vẫn ghim đúng một hoạt động đã duyệt trước video mẫu. |
| C4 (Q4) | Quyền đọc catalog hoặc xem trước lesson tách khỏi điều kiện tạo video; quyết định này không cấp quyền đọc mới. |
| C5 (Q5) | `VIDEO_READY` sau kiểm tra kỹ thuật và an toàn, Parent không cần xem hết; "hoàn tất" không có nghĩa đã làm hoạt động ngoài trời. |
| C6 (Q6) | Giữ metadata và lineage phiên bản; kiểm quyền hiện hành trước khi trả nội dung; lesson bị thu hồi hoặc gỡ phát hành thì ẩn danh sách, video không bị ảnh hưởng, không rơi về catalog công khai. |
| C7 (Q7) | Đầu vào bước viết kịch bản theo role: Parent không buộc hoạt động, Teacher dùng đúng một hoạt động đã duyệt. Không đưa gợi ý tùy chọn của phương án C vào. |
| C8 (Q8) | Có lập kế hoạch sửa nguồn riêng, cần approval riêng. Giữ Q155 là câu nói về tiếng Việt, dùng Q151 cho thứ tự hoạt động. |
| C9 | Không duyệt riêng ba thao tác chỉ cần Q1 (M002, M011, M018); chờ cả bộ rồi áp một lần. |
| C10 | Chỉ cập nhật B1 (gỡ `B2` khỏi 16 dòng) sau khi nguồn đã được sửa, bằng approval riêng. |

### D. Quy trình
| Mã | Quyết định |
|---|---|
| D1 | Thêm `/.codex/` vào `.gitignore` chung, gộp vào commit này. |
| D2 | Bốn ghi chú local (`S1_DECISION_CARD`, `REV36_DELTA_REVIEW_AND_S1_PREPARATION`, `REMAINING_AI_MODEL_RECOMMENDATIONS`, `VIDEO_FLOW_COMPARISON`) giữ ở local đến khi owner duyệt đẩy. |

## 3. Điều bản ghi này KHÔNG làm

- **Không phải approval** cho FEAT-064 (T0 hay bất kỳ T-N nào), Rev36 S1/S2/S3, B2A hay bất kỳ thao tác sửa nguồn nào. Mỗi mục vẫn cần mục approval riêng pin đúng hash.
- **Không phải chữ ký.** Mọi `cosign_status` trong ma trận B3 vẫn là `CHƯA KÝ`; B4 chỉ xác định ai phải ký. Việc `CaoDat-2410` đồng ý với B3:X, B3b và B4 **chưa được ghi nhận riêng**; cần xác nhận khi ký manifest.
- **B5 chưa có tên P4.**
- **Không sửa** SRS, register, ADR, DECISIONS, B1, manifest/ma trận B3, plan B2A hay bản ghi quyết định B2 (bản ghi B2 cũ vẫn ghi Q2–Q8 là giả định tại thời điểm đó; bản ghi này thay thế trạng thái đó từ 2026-10-31).
- Không cho phép DB tạm, gọi Modal/GPU, dữ liệu trẻ thật hay chạy code.
- 16 dòng B1 vẫn `blocked_by=B2` cho tới khi nguồn được sửa và B1 được cập nhật theo approval riêng.

## 4. Ảnh hưởng tới tài liệu hiện có

| Tài liệu | Ảnh hưởng |
|---|---|
| B2A (45 thao tác M001–M045) | Điều kiện "chờ Q2–Q8" nay có câu trả lời của owner; plan vẫn `DRAFT / AWAITING_APPROVAL` cho tới khi owner ghi approval pin hash của nó (mục 10 của plan). |
| Manifest B3 mục 9 | Tám câu có trả lời ở bảng B trên. Các phương án X/Y/Z, người review từng file và chữ ký vẫn là việc của T0. |
| `.gitignore` | Thêm một dòng `/.codex/` (D1). |
