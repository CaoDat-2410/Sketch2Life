# Kế hoạch chỉnh roadmap sau review độc lập — 2026-11-03

## Mục tiêu

Áp dụng các finding có căn cứ trong review cloud cho roadmap BE Parent/Teacher sáu mốc; ghi rõ finding nào không đúng với checkout local hiện tại vì reviewer không thấy tài liệu chưa được publish. Đây là cập nhật kế hoạch và provenance, không triển khai sản phẩm.

## Nguồn và baseline đã đối chiếu

- Roadmap hiện tại: `plan/BE_PARENT_TEACHER_VISION_DEMO_ROADMAP_20261102.md`, SHA-256 `875E93C59085DA9C38923DB85EEE50D15945CBD38EC27EC0B6389B93B3ECB8D4`.
- SRS v2.3-draft: `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, SHA-256 `DCBF9786FF8983E34F2D3B4EBAB76301D0C52A6C9DE72CD08D0816BBD0D983FC`.
- DTR v2.3-draft: `artifacts/DATA_TABLE_REGISTER.md`, SHA-256 `3E793BB2C62C9E6C50780DE636EDDE442D382C62B4643552F2298AF374171E22`.
- B0–B13 plan: `plan/B0_B13_SIX_MILESTONE_REDISPOSITION_PLAN_20261102.md`, current SHA-256 `773C4A8340C8E33AE39764D920B042AC19BACBAF6DC561FE9D5D3DFFCC4B5A5A`.
- B0–B13 report: `evidence/B0_B13_SIX_MILESTONE_REDISPOSITION_REPORT_20261102.md`, SHA-256 `8061DE7447A5C1A319D318290EE529BCF78A36C8DB013A53C2C34F35691B5645`.
- Local-only A2 closeout: `features/FEAT-064-current-flow-modal-vision-dev/evidence/A2_REV3_INDEPENDENT_REVIEW_CLOSEOUT_20261103.md`, SHA-256 `10B12F4417A5E29DF0ED1697F33A8FAA08D692E71015998CCC8DE297328A1C36`.
- Local-only sequential A2→B1→B2 plan: `features/FEAT-064-current-flow-modal-vision-dev/plan/FEAT064_A2_B1_B2_SEQUENTIAL_GOAL_20261103.md`, SHA-256 `D7DEE2977C5AA28B26FCB117281DE8B23E4D4AA85A42922B8B37752FBDA8752A`.

## Phạm vi tài liệu

1. Cập nhật roadmap: bổ sung các cổng quota/compute trước video; ánh xạ FR-PL/BR/NFR có liên quan vào sáu mốc; làm rõ lifecycle, schema convergence, safety/privacy/observability; thu hẹp tiêu chí và làm rõ ID B0–B13; ghi Parent-first/Teacher sequencing là đề xuất cần owner xác nhận vì SRS còn draft.
2. Sửa phần trạng thái roadmap đã cũ theo bằng chứng local: Mốc 1 được review ACCEPTED trong phạm vi demo synthetic; A2 được review ACCEPTED/COMPLETE theo closeout local. Không nhập Goal A2/B1/B2 legacy vào sáu mốc; không tuyên bố B1/B2 hay Mốc 2–6 đã hoàn thành/được phê duyệt.
3. Tạo evidence `CLAUDE_ROADMAP_REVIEW_DISPOSITION_20261103.md`: phân loại từng finding thành ACCEPT, ACCEPT-WITH-NUANCE hoặc NOT-REPRODUCED-LOCALLY; giải thích giới hạn quan sát của reviewer cloud và đưa lời phản hồi có thể gửi lại.
4. Bổ sung nguồn roadmap/B0–B13 vào FEAT-063 `SOURCE_REGISTER.md`, cập nhật `CONTEXT.md` và `status/STATUS.md`, và đổi bản ghi OpenAPI đang trùng D-120 thành ID còn trống D-130 trong `DECISIONS.md` mà không thay đổi nội dung quyết định.
5. Ghi rõ sai khác hash plan/report là sai khác provenance cần đính chính; giữ nguyên số liệu hash lịch sử, thêm hash hiện tại và không giả định bytes lịch sử nào đã được reviewer dùng.

## Ngoài phạm vi

- Không sửa SRS hoặc DTR; không tự chốt các câu hỏi sản phẩm còn mở.
- Không sửa source, test, migration, schema, API, approval/plan của FEAT-064; không thao tác DB, Modal, provider, mạng, Git history, index hay remote.
- Không thực hiện test/validator suite; chỉ dùng `git diff --check` và kiểm tra nội dung/hash tài liệu sau sửa.
- Không gửi tin nhắn ra Claude/Codex thread; evidence sẽ chứa phần phản hồi để owner chuyển tiếp.

## Tiêu chí chấp nhận

- Roadmap nêu rõ từng finding áp dụng được và điều kiện owner-gated; không biến draft SRS thành quyết định đã duyệt.
- Mỗi nhóm yêu cầu FR-PL/BR/NFR được gắn mốc hoặc ghi rõ là cross-cutting / pending owner decision.
- Trạng thái Mốc 1/A2 khớp evidence local và ghi cảnh báo tài liệu A2 chưa có trên remote; không suy diễn tiến độ B1/B2.
- Evidence trả lời trực tiếp finding cloud, chỉ ra finding nào sai hoặc chưa thể kết luận và lý do cụ thể.
- Context, source register, decisions và status dẫn tới đúng hồ sơ mới; không đổi các file FEAT-061/FEAT-064 khác.
- `git diff --check` sạch; branch, HEAD và index giữ nguyên; các đường dẫn ngoài allowlist giữ nguyên bytes.

## Trạng thái

**APPROVED / IN PROGRESS** theo yêu cầu trực tiếp của owner: “lấy những phần review của claude đúng và sửa và cũng chỉ ra cho nó tại sao chỗ đó của nó lại sai đi”. Approval cụ thể và hash plan được ghi trong `approvals/TASK_APPROVAL.md` trước khi sửa các tài liệu còn lại.
