# StoryRun-lite M0 — xử lý review V11

Ngày 2026-11-02. Owner yêu cầu xử lý finding một lần, không mở thêm vòng review M0, rồi chuẩn bị Goal 1. Reviewer độc lập kết luận V11 **NEEDS_REVISION**, 7 P2 và 2 P3; báo cáo nguyên văn được lưu tại `STORYRUN_LITE_VISION_M0_V11_INDEPENDENT_REVIEW_20261102.md`, SHA-256 `755FF00669104900B1F728C35107ABEE123BC31B65D258900508A7CA3C51F1A5`.

V11 được review SHA-256 `31217D7C1870D4DEA132B472B917890ABA86CCAE92970BD1EE8AB3CCE506883F`; giữ nguyên V11. Bản kế tiếp `plan/STORYRUN_LITE_VISION_M0_V12_FINAL_DRAFT_20261102.md` bổ sung mục 9 là điều khoản hiện hành khi mâu thuẫn với lịch sử V11. Các xử lý dưới đây là của phiên lập kế hoạch; **không khẳng định reviewer đã chấp nhận V12**.

| Finding | Xử lý trong V12 |
|---|---|
| P2-1 | §9.1: B+ có thể chồng lấn hai invocation khác run cả khi claimant cũ chưa SENT và khi invocation cũ SENT/UNKNOWN; capacity là theo process; Q3-C không dừng request đã gửi. |
| P2-2 | §9.2: pin fixture/provenance/hash trước admission; hash, scan, decode trên cùng snapshot bất biến; hai cách test 1/2 part theo contract, test 5 MB ở tầng upload không nới allowlist. |
| P2-3 | §9.3: SQL CHECK ba nhánh có NULL rõ, trigger ngăn tạo legacy shape mới, phạm vi tương thích writer cũ/mới, fallback/index, acceptance disposable PostgreSQL. |
| P2-4 | §9.4: Core và Story chốt PENDING mồ côi, giữ FINAL 202, bump version/CAS chặn worker cũ; crash-injection acceptance cho cả hai cửa sổ. |
| P2-5 | §9.5: kịch bản Bruno/CONFIRM 202 → GET PREPARATION_REVIEW → exact replay, không trùng decision/attempt, stale revision 409; receipt + decision cùng Story UoW. |
| P2-6 | §9.6: bổ sung các mục DTR tổng/ownership/relationship/invariant và số đếm hai baseline, trường/unique/CHECK/FK hai receipt; giữ Q135 lịch sử. |
| P2-7 | §9.7: hai receipt authority, identity/scopes, fingerprint từng command, key conflict đúng phạm vi và PUT part natural key/digest. |
| P3-1 | Mở đầu ghi hai goal tuần tự, approval riêng; không thêm vòng review M0. |
| P3-2 | Ghi rõ mốc smoke là lịch sử V10; V12 không nâng mức chứng cứ. |

## Tự kiểm tiền đề của prompt V11

1. **Một phần:** `application/services/image_admission.py:65` đọc metadata rồi đánh giá giới hạn trước `decode_one_frame`; `domain/understanding/image_admission.py:76` nêu 5.000.000 byte/4.000.000 pixel/4096 edge. `infrastructure/media_validation/av_image_decoder.py:32` đọc metadata PyAV, `:52` demux packet, `:70` decode frame trong process. Không thấy subprocess timeout 3 giây/hard memory cap ở adapter đó; header limit không chứng minh hard bound đối với header sai. V12 thêm snapshot bất biến/exact fixture và yêu cầu isolation trước input tùy ý. Đây là đọc tĩnh, không chạy decoder.
2. **Đúng:** 5.000.000 byte = 4.194.304 + 805.696, cần tối đa 2 part cỡ không quá 4 MiB. `DATA_TABLE_REGISTER.md:307` và `:308` mô tả part liên tục, per-part hash và tổng/hash; aggregate là SHA của bytes nối đúng thứ tự. Test 2 part phụ thuộc quy tắc kích thước part và fixture tương ứng, không mặc định fixture có đủ 4 MiB.
3. **INPUT_PROCESSING: đúng; UNKNOWN: suy luận:** SRS `SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:339` phân biệt StoryRun và `:343` AiJob; UC-11 `:1422`–`:1432` cho hủy run chưa thuộc các trạng thái loại trừ. `AWAITING_RECONCILIATION` là job state và không được UC-11 gọi tên riêng; có thể cancel nếu run vẫn chưa terminal. `infrastructure/documents/clamav_scanner.py:22` nhận `BinaryIO` stream, có thể cần adapter như `BytesIO`, không nhận raw bytes trực tiếp; chưa chạy/dò service.

## Sổ độ lệch và các điểm owner cần biết

V12 §6.1/§9 ghi đủ lý do, rủi ro, điều kiện đảo và hardening: ảnh synthetic exact fixture, giới hạn 5 MB/4 MP/PNG-JPEG, PyAV không hard limit, attestation không phải AV CLEAN, scanner fail → session mới, purge best-effort, AiJobService hoãn và B+ có thể overlap provider giữa các run. Các điểm lựa chọn về fixture, scanner và migration/owner scope không thể coi là đã được owner phê duyệt chỉ từ yêu cầu sửa tài liệu. Goal 1 chuẩn bị công việc và plan hẹp cho các cổng đó; live Modal là phê duyệt riêng.

**Cập nhật sau đó theo owner:** owner làm rõ demo phải cho người dùng chọn các ảnh synthetic khác nhau mỗi lần và chọn JPEG/PNG/WebP. Vì vậy phạm vi fixture-only và 5 MB/4 MP trong đoạn lịch sử trên đã được thay thế bởi V12 §10: input có thể thay đổi, mục tiêu SRS 20 MiB/40 MP, scanner thật trước parser, decoder/normalizer trong worker có OS limits, bảo toàn original/derived. Fixture hash chỉ dùng cho test. Không tự suy ra được phép dùng dữ liệu trẻ thật hoặc gọi Modal live. V12 được cập nhật sau khi owner sửa yêu cầu; hash cũ trong bản Goal 1 cũ và prompt cũ không còn hợp lệ và đã được thay bằng hash mới.

## Giới hạn lượt này

Không chạy test/validator, không kiểm trạng thái ClamAV/port, Docker, PostgreSQL, Modal/provider hay môi trường triển khai; không xác minh fixture cụ thể, hash fixture, UI consumer hoặc evidence runtime mới. A2 vẫn tạm dừng và database A2 không được đụng. Chưa stage/commit/push/merge; báo cáo V11 không phải approval triển khai và V12 không được gắn nhãn independent-review accepted.
