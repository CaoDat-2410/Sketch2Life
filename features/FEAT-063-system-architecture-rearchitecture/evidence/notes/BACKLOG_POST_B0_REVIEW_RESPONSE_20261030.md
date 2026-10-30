# Xử lý review kế hoạch sau B0 — 2026-10-30

## Phạm vi và nguồn

Chủ task gửi bản review Claude với verdict `NEEDS_REVISION` về thứ tự, đồng thời xác nhận B1 bắt đầu được. SHA-256 bản review được gửi: `6095597F282F27D600BCD1DC197513D52D553479DE31D261EDB4272796CCF7B2`. Đã đối chiếu read-only với source và hồ sơ FEAT-064, sau đó sửa [backlog điều phối](../../plan/BACKLOG_API_REV37_SRS23_MODAL_20261030.md) cùng hai báo cáo B0. Đây là sửa tài liệu; không triển khai B1, pilot, code, migration hay provider.

## Xử lý finding

| Finding | Xử lý và giới hạn |
|---|---|
| F1 — mâu thuẫn Parent chặn nhầm pilot | B2 chạy song song B1/B3/T0 và pilot; chỉ chặn contract StoryRun/Parent phụ thuộc. |
| F2 — gộp consent synthetic và legal | B4a trỏ đúng FEAT-064 T1 theo D-05; B4b giữ vòng đời/chính sách dữ liệu thật trong scope sau. Không thêm `effective`, giả consent hoặc mở guard REAL để làm pilot. B5, S1/S2/S3 không là prerequisite pilot. |
| F3 — thiếu nhánh FEAT-064, hỏi lại lựa chọn | Ghi lại D-01 đã chọn pilot trước flow mới, tham chiếu T0–T14 thay vì tạo task trùng. B8 được ghi là optional demo-route regression. Giữ 14 ID cấp trên B0–B13. |
| F4 — ownership chưa đủ | B3/T0 cùng tạo manifest file, thứ tự migration và contract data_origin; named owners không đồng nghĩa đồng ký. Phải có đồng ký thực tế theo scope trước code phụ thuộc, phối hợp composition theo ADR-0015 và ghi lệch mapping vai trò. Không bắt B3 hoàn chỉnh trước T0 docs để tạo vòng phụ thuộc. |
| F5 — B0 chưa đủ tiêu chí lịch sử | Tách B0a đạt baseline offline `combined`, B0b blocked lịch sử. B1 có cột profile/evidence/pilot-needed/blocked-by. Snapshot classroom chưa có. Thời điểm publication B0 được bổ sung bằng hai commit đã push. |
| F6 — wording cũ của plan, decisions đã chọn | Backlog yêu cầu T0 đối chiếu D-04–D-09 với §8 và các tham chiếu Rev33 cũ, pin đúng plan rev6 cùng DECISIONS/hồ sơ T0 có version/hash/scope khi xin approval. Không sửa PLAN hoặc tự cấp precedence cho văn bản mới. Exact profile/contract, đồng ký và manifests còn mở. |
| F7 — replay Parent Group | Giữ B5 độc lập, hiện là rủi ro từ source; chưa tái hiện hoặc biết DB có receipt cũ. Không là blocker classroom pilot. |

## Điểm cần làm rõ trong review

- Bảng so sánh của Claude nói cần thêm `/v1/vision/context` cho pilot. [FEAT-064 PLAN](../../../FEAT-064-current-flow-modal-vision-dev/plan/PLAN.md) §6 và [DECISIONS](../../../FEAT-064-current-flow-modal-vision-dev/DECISIONS.md) P-05 giữ `image_only` qua `/v2/vision` khi policy cho phép; typed context bắt buộc C2 thì phải từ chối hoặc có scope riêng. Không thêm endpoint hay nới guard C1/C2 trong backlog này.
- Câu “S1 first” của Rev36 là thứ tự nhánh nền tảng mới; cùng plan ghi S1 không là prerequisite pilot. Backlog ghi rõ pilot trước theo D-01 và manifest/approval phải chốt thứ tự thực tế, không sửa hash Rev36 hoặc tự phê duyệt ngoại lệ.
- Bản catalog được gửi dùng CRLF, bản trong Git dùng LF. Đã đối chiếu bytes và ghi hai SHA-256 riêng tại báo cáo B0; trùng nội dung sau chuẩn hóa xuống dòng, không trùng hash nguyên bản.

## Bước tiếp theo

1. B1 crosswalk 135 operation catalog và thêm các NEW_TARGET SRS, dùng B0a; B0b giữ blocked.
2. B3/T0 chuẩn bị manifest và quyết định contract còn mở, B2 song song. Không hỏi lại việc đã chọn pilot; chưa có approval code/DB/live cho FEAT-064.
3. Chỉ sau approval đúng scope và gates theo FEAT-064 mới làm task phụ thuộc; live T13 sau T12 và approval/chấp nhận rủi ro riêng. B8 không thay pilot.

## Kiểm tra bảo toàn

Các hash trước sửa tài liệu để đối chiếu sau:

- FEAT-064 PLAN rev6: `CD7B3236A55E280D4722166C73AF462835DEC8503BCE882CE0CFF9D5601F9665`.
- FEAT-064 TASK_APPROVAL: `71514E7F2BDA2AAE96374135FE6DE450F15816567191DBBF74B4F23EAA0B5A8B`.
- FEAT-063 plan backend Rev36: `8DD1989926DCA4E0312ABD79032EE4AF862A9FE1AAAB786A6BC4BC6DB5389751`.
- FEAT-063 TASK_APPROVAL: `E27F1D385F2430E32782C2F2471E6E4368D0F64131341EA18641E866CC9AD35A`.

Các kết quả B0 cũ giữ đúng phạm vi offline; không có test runtime mới, DB/MinIO/Modal/GPU hoặc child data. Các thay đổi local ngoài phần review này được giữ nguyên.

Đã đối chiếu sau sửa: bốn hash ở trên giữ nguyên. Link nội bộ hợp lệ, có đúng 14 ID B0–B13; `git diff --check`, harness, architecture và repository-security validators đạt. Rà delta độc lập không còn finding bắt buộc trong phần sửa backlog; đây không phải approval thực thi hoặc reviewer PASS cho toàn bộ plan FEAT-064/Rev36.
