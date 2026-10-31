# Lộ trình BE Parent/Teacher và demo Vision

- Ngày ghi nhận: 2026-11-02, Asia/Ho_Chi_Minh.
- Trạng thái: **GHI CHÚ ĐIỀU PHỐI / DRAFT**. Đây không phải approval triển khai, không thay thế SRS, plan task hay review độc lập.
- Ưu tiên hiện tại: nhanh chóng có BE demo nhận ảnh synthetic, gọi Vision thật trên Modal và trả kết quả qua API để người phụ trách UI ghép demo. Người thực hiện BE không triển khai UI.
- Phạm vi SRS: Parent/Teacher mới dùng ảnh tranh giấy; tài liệu SRS v2.3 vẫn là draft. Demo là một lát cắt, không chứng minh toàn bộ luồng Parent/Teacher hoặc sẵn sàng cho dữ liệu trẻ thật.

## Sáu mốc BE

| Mốc | Kết quả cần hướng tới | B0–B13 đưa vào mốc | Tiêu chí hoàn thành ở mức kế hoạch |
|---|---|---|---|
| 1. Vision demo | Hoàn thành đúng Goal StoryRun-lite S1→S2: ảnh synthetic → API BE → admission → Vision giả rồi bridge A1 qua HTTP loopback → API trả trạng thái/kết quả. | Không gắn task B0–B13 vào mốc này. | S1→S2 offline/loopback acceptance đạt, được review và bàn giao OpenAPI/Bruno cho UI. Đây chưa phải bằng chứng Modal live; lượt Modal live được ghi riêng nếu owner yêu cầu. |
| 2. Nền Parent/Teacher | Identity và quyền theo vai trò, hồ sơ, StoryRun, nguồn ảnh, kết quả, job và lifecycle bền vững. | B3 (lập manifest mới, owner/sign-off thật); B4b (consent thật khi mở dữ liệu thật); B6/B7 (chỉ phần Rev36 còn phù hợp, phải re-plan); phần nền của B10; B5 nếu còn phải giữ receipt Parent Group. | Kiểm đúng owner/scope, một trẻ/run, cạnh tranh, restart, hủy/xóa và tích hợp AI Jobs theo plan mới đã duyệt. Không dùng manifest B3 cũ như approval. |
| 3. Đầu vào hoàn chỉnh | Text/voice, transcript, Vision và bước người lớn xác nhận chủ thể/context. | Phần input của B9; phần Parent line-sketch của B13 chỉ khi còn được chọn trong SRS. | API lưu đúng revision, cho xem/xác nhận, từ chối dữ liệu sai scope hoặc cũ; chính sách sửa chủ thể thống nhất với SRS/quyết định mới. |
| 4. Story/storyboard | Tạo story có cấu trúc, quản lý revision, viết lại và người lớn xác nhận. | Phần story/script/rewrite còn lại của B9. | Có bằng chứng API, giới hạn viết lại và không tạo video trước xác nhận script. |
| 5. Video | Reference → scene generation → consistency → ghép → TTS/phụ đề → safety → playback riêng tư. | B11. | POC model/GPU/chi phí và kiểm tra từng stage; flow tổng có evidence, lỗi và điều kiện playback rõ ràng. |
| 6. Hoàn thiện sản phẩm | Teacher lesson/occurrence, quota, lịch sử, lifecycle, quan sát/vận hành, billing và tích hợp. | Phần còn lại của B6/B7/B10; B12 là cổng test xuyên mốc 2–6; phần tổ chức/roster/capacity, billing và Teacher sketch của B13; B5 chỉ nếu còn tương thích legacy cần nghiệm thu. | Các yêu cầu SRS đã chọn được review, test tích hợp và có quyết định riêng cho dữ liệu thật/production. |

**Cách hiểu ID cũ:** B0a/B1/B2 là hồ sơ đối chiếu/quyết định đã có, không chạy lại như goal; B0b còn thiếu bằng chứng lịch sử nhưng không chặn; B4a thuộc eligibility canvas cũ, không lặp vào demo ảnh; B8 là smoke route demo cũ, không phải gate của StoryRun S1→S2. B9–B13 là nhóm yêu cầu để phân lại vào các mốc nêu trên, không còn là plan sẵn sàng chạy. B6/B7 “Rev36 S1/S2/S3” không phải Goal StoryRun-lite S1→S2 hiện tại.

## Kế hoạch hiện tại: Mốc 1

1. **M0/Vision contract:** Goal S1→S2 hiện dùng `STORYRUN_LITE_VISION_M0_V12_FINAL_DRAFT_20261102.md` cùng các nguồn ghim trong master goal. Không tuyên bố V12 đã được reviewer ACCEPTED.
2. **Goal gộp S1 + S2 — đang chạy:** tạo run synthetic, nhận ảnh/admission, quản lý trạng thái/kết quả và contract API; sau đó nối guard/ledger/transport A1 phù hợp. Acceptance hiện tại là fake + HTTP loopback và regression; không gọi provider thật.
3. **Kết quả Mốc 1:** khi S1→S2 acceptance đạt và được review, bàn giao OpenAPI/Bruno cho người phụ trách UI. Có thể coi phần BE demo của Mốc 1 hoàn tất theo yêu cầu owner; điều này không tự chứng minh Modal live. Lượt Modal thật, nếu cần để xác nhận kết nối, được ghi evidence riêng và không phải task B0–B13.
4. **Mở rộng:** sau khi UI ghép theo contract, tiếp tục Mốc 2–6 theo plan/review riêng. Không nối lại các goal canvas cũ chỉ vì chúng có số B/T trùng.

### Điều kiện cần chốt trong M0

- Binding riêng cho ảnh chụp; không giả provenance checkpoint canvas hoặc làm thay đổi hành vi canvas đã chấp nhận.
- Truy vết thứ tự worker/guard/transport/bridge/ledger để tránh claim hoặc mark SENT hai lần; thiết kế crash/restart, worker còn sống, phản hồi muộn và reconcile giữa Story/ledger. Không tự gửi lại khi UNKNOWN.
- Chốt admission/chuẩn hóa, phân biệt hash ảnh gốc với hash ảnh gửi VLM, asset storage và scope truy cập. Quyết định tạm thời phải ghi nợ kỹ thuật.
- Chốt việc tạm chưa dùng `AiJobService` nếu được chọn; ghi rõ sai lệch SRS và cách chuyển về sau. Chốt lựa chọn xử lý sửa chủ thể và sai lệch SRS nếu có.
- Demo dùng identity giả lập giới hạn local/test và synthetic; identity/consent thật để mốc sau. Chốt API contract đủ cho frontend, không triển khai UI.
- `/health` chỉ kiểm tra riêng app Modal trả lời; không chứng minh model, token hoặc transport A1. Smoke FEAT-061 ngày 29/10 dùng luồng demo cũ; ghi chép ngày 01/11 không có log thô và không chứng minh A1 live.
- Chọn cách bảo vệ working tree A2 và mốc HEAD trước S1/S2; không tự đưa thay đổi ngoài scope vào commit.

## Trạng thái và phần tạm gác

- **A1: COMPLETE** theo sổ FEAT-064 sau review độc lập; commit local `a88de875ff92e9b4d4fa5cc2f5f8d5fc1f626f58` là mốc đã quan sát, cần kiểm lại trước goal mới.
- **A2: TẠM DỪNG / XONG-CHƯA REVIEW**, không được nhận là ACCEPTED. Báo cáo: `features/FEAT-064-current-flow-modal-vision-dev/evidence/A2_REVIEW_FIX_PAUSE_REPORT_GA2_20261102.md`. Snapshot local: `.claude/handoff/snapshots/GA2_REVIEWFIX_PAUSE_20261102T121026/` và bản bảo vệ `.claude/handoff/snapshots/CLAUDE_A2_PAUSE_20261102T121212/` theo bàn giao.
- Test PG A2 có teardown lỗi FK; **có thể còn hàng synthetic** vì cleanup rollback. Chưa kiểm tra hay dọn lại. Trước khi dùng DB, kiểm tra theo thủ tục đã duyệt, chỉ xử lý đúng dữ liệu test thuộc phạm vi; không giả định database sạch.
- **B1/B2 canvas và T13 canvas: tạm gác**, không xóa. Không tự đưa code A2 chưa review vào nền demo như đã được chấp nhận.
- `origin/dev` từng được kiểm tra ở `c98701b1e500906f396e773c79ec3bba55db2542`; mô phỏng merge giữa các commit có conflict và working tree có file chồng lấp. Đây là quan sát tại thời điểm kiểm, cần kiểm lại; chưa merge. Không stage/commit/push/merge trong lúc goal khác đang dùng chung working tree.

## Kiểm tra môi trường ban đầu

Quan sát ngày 2026-11-02: `backend/.venv` dùng Python 3.12.10; FastAPI TestClient thử app tối thiểu trả OpenAPI 200; Pillow xử lý PNG synthetic trong bộ nhớ; A1 transport/ledger import được. PostgreSQL 17/18 đang chạy và TCP loopback 5432 mở, nhưng chưa xác minh database/schema/cleanup. Docker client có nhưng engine không kết nối được. Modal CLI không có trên PATH hoặc trong `backend/.venv`; môi trường khác chưa kiểm. Một số dependency backend khai báo còn thiếu; cần đối chiếu phạm vi goal trước khi cài. Chưa test app Sketch2Life thật hay gọi Modal trong lượt kiểm này.

## Nguồn và cách cập nhật

- SRS draft: `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` §§5–7, 19, 22, 31; `DATA_TABLE_REGISTER.md` §5.6.
- Quyết định pilot: `.claude/handoff/OWNER_DECISIONS_G3G4_V4_20261101.md`; sổ `features/FEAT-064-current-flow-modal-vision-dev/status/PILOT_GOAL_LEDGER_20261101.md`.
- Evidence smoke BE demo cũ: `features/FEAT-061-modal-qwen-vl-endpoint/evidence/BACKEND_DEMO_MODAL_SMOKE_20261029.md`; không phải bằng chứng cho flow mới hay A1 live.
- Cập nhật kế hoạch/trạng thái có dẫn nguồn sau từng quyết định hoặc review; không sửa hồ sơ approval lịch sử. Khi thông tin mới mâu thuẫn, ghi rõ thời điểm và nguồn mới thay vì âm thầm tuyên bố hoàn tất.

## Disposition B0–B13

Chi tiết trạng thái từng ID và lý do không chạy lại theo kế hoạch cũ được ghi tại `plan/BACKLOG_API_REV37_SRS23_MODAL_20261030.md` phần “Disposition sau khi chuyển sang StoryRun-lite”. Bảng ở đầu roadmap là cách phân bổ hiện hành. SRS vẫn là draft; việc đổi cách lập kế hoạch không xóa yêu cầu SRS hay tự cấp approval triển khai cho Mốc 2–6.
