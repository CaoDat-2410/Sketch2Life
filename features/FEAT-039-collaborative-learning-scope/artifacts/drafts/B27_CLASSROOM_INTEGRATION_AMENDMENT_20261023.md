## B27. Phụ lục sửa đổi tích hợp lớp — 2026-10-23

Phụ lục này bổ sung cách đọc yêu cầu lớp học và ghi rõ contract gaps phát hiện trong rà soát FEAT-060. Nó không viết lại các baseline B5/B19/B22, không chứng nhận source hiện tại, và không adopt API hay schema. SRS v3.1 trước thay đổi được bảo toàn nguyên trạng. Phụ lục được version hóa thành v3.2 để người đọc truy vết được phần bổ sung.

### B27.1 Mã phòng sáu chữ số — OWNER_CONFIRMED

Owner xác nhận mã sáu chữ số là **mã phòng dùng chung** theo kiểu Quizizz/Kahoot: nhiều trẻ trong cùng lớp có thể nhập cùng mã. Đây không phải OTP, không phải mã dùng một lần, và không nhận diện một hồ sơ trẻ. Khi Teacher bắt đầu lớp thành công, **cả QR/deep-link lẫn mã sáu chữ số đều ngừng nhận yêu cầu tham gia mới**; không nhận trẻ vào muộn qua hai đường này sau thời điểm đó. Trẻ đã được admit trước lúc bắt đầu tiếp tục dùng grant hiện có. Không có thời hạn OTP cố định được xác nhận.

Mã phòng chỉ định tuyến yêu cầu vào phiên. Mã hợp lệ không tự admit trẻ và không thay thế các bước backend tạo yêu cầu chờ, Teacher chọn hồ sơ trẻ được quản lý, kiểm tra consent có hiệu lực và admit thiết bị. Không trả roster, hồ sơ, nội dung lớp hay tranh chỉ dựa vào mã.

**Giới hạn của quyết định:** quy tắc đóng QR và mã 6 số sau khi start đã được xác nhận ở mức sản phẩm. Server contract vẫn phải định nghĩa cách trả lỗi cho lời mời cũ, cách xử lý pending request đang chờ tại thời điểm start, và phân biệt admission mới với thiết bị đã admitted; các chi tiết này chưa tự quyết định trong SRS.

### B27.2 Stage học, lifecycle phiên và tiến độ nhóm — đề xuất contract

SRS B5/B19 đã xác định chín chặng học: `preparation`, `join`, `explore_draw`, `assistance`, `sharing`, `knowledge`, `off_screen`, `reflection`, `completion`. Chặng học trả lời **“lớp đang làm phần học nào?”**; lifecycle (`lobby`, `active`, `paused`, `finished`...) trả lời **“phiên đang vận hành ra sao?”**. Tiến độ riêng của từng nhóm/trẻ là chiều thứ ba. Một phiên `active` chưa cho biết lớp đang ở chặng nào.

Để UI Teacher và Child theo cùng một trạng thái sau refresh/reconnect, đề xuất BE lưu chặng dùng chung và trả về giá trị authoritative cùng revision; Teacher chuyển chặng bằng command có kiểm tra revision/điều kiện và receipt bền vững. Không cho màn hình tự đổi stage ở client, không suy stage từ `active`, và không tự advance khi nhóm báo ready. Hoạt động hỗ trợ AI có thể xen kẽ theo B19; việc gọi help không nhất thiết chuyển lớp sang stage mới. Đây là refinement cho các nguyên tắc hiện có, không phải quyết định thêm enum/product flow.

Stage endpoint, revision/CAS, idempotency, transition guards, event history và bảng lưu là `PROPOSED_UNADOPTED`. Cần BE1 owner review, phê duyệt contract/migration, và feature approval trước khi implement. API mapping và các gaps hiện tại được ghi tại [FEAT-060 API traceability](../../../FEAT-060-classroom-integration-and-review-remediation/evidence/notes/SRS_STAGE_API_TRACEABILITY_20261023.md) và [đề xuất shared-stage BE1](../../../FEAT-060-classroom-integration-and-review-remediation/artifacts/BE1_SHARED_STAGE_CONTRACT_PROPOSAL.md). FEAT-060 Plan Rev3 vẫn DRAFT.

### B27.3 Kết quả kết thúc phiên — OWNER_CONFIRMED semantics; contract details proposed

Owner xác nhận hệ thống phải phân biệt: (a) lớp hoàn tất các bước/kết quả bắt buộc (`completed`) và (b) Teacher dừng buổi trước khi hoàn tất (`ended_early`). Nói đơn giản, đây là cách tránh hiển thị buổi bị dừng giữa chừng như đã hoàn thành đầy đủ. Source `/finish` hiện chỉ lưu lifecycle `finished`; bản thân giá trị đó không chứng minh trường hợp nào đã xảy ra.

Hai ý nghĩa kết quả là **OWNER_CONFIRMED**. Tên field, completion receipt, điều kiện bắt buộc cho `completed`, lý do dừng sớm, dữ liệu đã lưu và nhóm chưa hoàn thành vẫn cần contract/guard cụ thể; những chi tiết kỹ thuật này chưa được adopt. Cho đến khi có contract, không map lifecycle `finished` sang `completed` hoặc `ended_early`, không tuyên bố quy trình hoàn tất từ một lệnh finish.

### B27.4 Bảng thay đổi và trạng thái

| Chủ đề | Cập nhật B27 | Trạng thái / evidence |
|---|---|---|
| Mã phòng 6 số | Dùng chung; đóng mã khi Teacher bắt đầu lớp; giữ Teacher profile/admission và consent | OWNER_CONFIRMED; API còn chưa implement |
| QR/code late admission | QR/deep-link và mã 6 số đều đóng nhận admission mới sau khi start thành công | OWNER_CONFIRMED; pending-request/response semantics vẫn cần contract |
| Chín chặng SRS | Backend cần trạng thái chặng dùng chung, tách lifecycle và tiến độ nhóm/trẻ | Requirement principles đã có ở B19; API/schema refinement PROPOSED_UNADOPTED |
| Hoàn tất hay dừng sớm | Phân biệt đủ quy trình (`completed`) và Teacher dừng trước đó (`ended_early`); không suy từ `finished` | OWNER_CONFIRMED semantics; API/schema/guards PROPOSED_UNADOPTED |
| Implementation | Chỉ thay yêu cầu và đường dẫn composer/checker tài liệu; product source/DB/runtime không đổi | FEAT-060 Plan Rev3 DRAFT; approval và BE1 migration/contract review là gate |

## Change log — SRS v3.2

2026-10-23: Add B27 from owner-confirmed classroom integration direction and FEAT-060 source/API review. Preserve v3.1 exactly. Close all new QR/deep-link and six-digit-code admission when start succeeds; retain existing admitted grants; distinguish full completion from Teacher early stop. Endpoint/schema/revision/guard/pending-request semantics, stage persistence implementation and migration remain PROPOSED_UNADOPTED. No product code, database, API, migration, application test, provider, or deployment change is implied; documentation composer/checker paths target v3.2.
