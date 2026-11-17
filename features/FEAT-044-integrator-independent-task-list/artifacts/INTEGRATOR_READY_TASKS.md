# Các task người tổng hợp có thể làm ngay

**Đây là người nối FE với hai BE — P4 trong [bảng phân công hiện tại](../../FEAT-040-four-person-delivery-plan/artifacts/TEAM_TASK_BREAKDOWN.md).** Chủ đề đã được owner đính chính, không phải P1 FE. Không thay đổi phân công gốc.

P4 không cần chờ người khác viết xong code để chuẩn bị đường nối. **INTG-01 là foundation độc lập chính thức**; các card sau có thể chuẩn bị sơ đồ, fixture, fake wiring và mẫu kiểm tra trước. Nghiệm thu nối runtime thật vẫn giữ các dependency trong FEAT-040. Danh sách này là kế hoạch; yêu cầu hiện tại không triển khai code.

## A. Task độc lập, có đầu ra ngay

Các nhãn `/a…/g` là checklist con của INTG-01, không thêm task ID toàn hệ thống hay endpoint mới.

| Task | Việc làm cụ thể | Đầu ra / tiêu chí xong phần độc lập |
| --- | --- | --- |
| INTG-01/a — Bản đồ các điểm nối | Đọc SRS và14 handoff H-* hiện có; liệt kê module, producer, consumer, dữ liệu/lỗi và owner. Phân biệt nhánh Sketch tùy chọn với luồng gallery/video. | Handoff map: mỗi seam có owner và consumer; không phải chờ code hoặc dựng backend thật. |
| INTG-01/b — Sổ contract candidate | Tập hợp request/result/event/schema examples; ghi version, IDs/scope, expected revision, idempotency, source/artifact/hash và typed error theo từng handoff. Phân biệt đang đề xuất, đã adopt và gap. | Registry + payload mẫu để P1/P2/P3 review sau. Không tự chốt domain contract, transport, trường dữ liệu hay route của toàn nhóm. |
| INTG-01/c — Bộ dữ liệu mẫu dùng nối | Tạo synthetic school/class/session/group/participant/device/turn/canvas/checkpoint/AI review/video/consent/activity/result. Ghi input, expected outcome, version, hash và lineage. | Fixture pack có success/fault cases, không cần DB, Firebase, GPU, FE screens hoặc API của hai BE. Không chứa credentials/real child data. |
| INTG-01/d — Fake adapters | Dựng fake port cho core, AI/jobs/media và client consumer; cho phép chọn delayed/error/stale/revoked outcome. Giữ fake mode rõ và tách khỏi production adapter. | Adapter fixtures tự chạy local; một module fake có thể thay bằng output thật sau khi contract được adopt. Đây không phải viết thay adapter backend/provider của P2/P3. |
| INTG-01/e — Runner nối giả lập | Nối fake boundaries theo request → result/event → consumer. Đầu tiên lớp/join/admission; sau đó canvas receipt, gallery/video/off-screen; nhánh Sketch review riêng. Có thể dùng headless consumer, không cần UI thật. | Một lệnh chạy demo/suite khi toàn bộ BE/FE/provider tắt; kiểm tra IDs/version/hash và expected state qua từng seam. |
| INTG-01/f — Case lỗi tại boundary | Unknown field/version, mất ack và gửi trùng, stale snapshot/review, wrong scope/revoke, delayed completion, AI pending/unsafe, video generating/exhausted failure, partial finish/purge. | Case matrix và kết quả expected/pass/fail của fake runner; không biến pending/partial thành success. Không chứng minh permission, persistence hay inference thật bằng stub. |
| INTG-01/g — Traceability và compatibility | Map SRS → task → H-* → fixture/check → evidence; lập diff/gap và phần cần owner xác nhận. Định nghĩa format handoff component: revision, manifest, lệnh chạy, error examples và giới hạn. | Bảng trace/gap + checklist nhận code. Khi ba người bàn giao mới chạy cross-review compatibility; không bắt họ chờ registry để làm foundation riêng. |

Thứ tự hữu ích: **handoff map → registry candidate → fixture pack → fake adapters/runner → fault cases → compatibility/handoff checklist**. Có thể bổ sung fixture dần theo từng seam; không cần mô phỏng hết toàn sản phẩm trước đầu ra đầu tiên.

## B. Phần chuẩn bị của các card tiếp theo cũng không cần chờ

| Card gốc | Chuẩn bị ngay | Cần có trước khi nghiệm thu toàn card |
| --- | --- | --- |
| INTG-02 — Composition | Sơ đồ composition root, inventory ports/adapters/entrypoints; thiết kế injection; sau foundation có thể dựng skeleton với fake ports và startup error scenarios. | Foundation packs đã review, adapters thật từ P2/P3, feature approval và ADR liên quan. Thiếu durable adapter phải ghi rõ chưa ready. |
| INTG-03 — FE–API connector | Fake-client examples cho request/result/error mapping, loading/cancel/retry và identity/admission lifecycle. | UI tương ứng của P1, API/adopted contracts và auth/scope của P2; fake actor header không phải authentication thật. |
| INTG-04–08 — Đường nối từng luồng | Sequence diagrams và fault-fixtures cho canvas/recovery, AI review, gallery/video, activity/portfolio, Admin/revoke/recall/delete. Dùng H-* có sẵn, không truy DB module khác. | Các module, UI, domain policies và storage/provider outcomes tương ứng được bàn giao. Chỉ nối những seam đã đủ đầu ra, không đợi xong cả 57 task. |
| INTG-09 — Test plan và quản lý lỗi | Đặc tả nine-step learning loop và SRS INT-01–12; expected results, setup/cleanup, evidence fields, defect template có owner. | Integrated flows và component tests thực tế; P1/P2/P3 vẫn sửa lỗi phần mình. INTG task IDs khác SRS INT scenario IDs. |
| INTG-10 — Config/runbook | Config schema với placeholders, bảng dependency/readiness, redaction sentinels, startup/shutdown/runbook skeleton cho fixture mode. | Stack decisions/adapters đã adopt và runtime environment được cấp cấu hình. Không tự chốt DB/queue/cloud/model/web để lấp chỗ chưa quyết định. |
| INTG-11 — Kế hoạch đo tải | Thiết kế profile một lớp tối đa 40 trẻ; tách participant/connections/group/operations/job load; mẫu run/device/model/network manifest và kết quả đo. | Hệ thống nối thật, ngưỡng được adopt và benchmark component. Chưa chạy thì chưa có số đo;40 idle logins không chứng minh tải lớp học. |
| INTG-12 — Mẫu hồ sơ bàn giao | Template architecture/API/contract list, checklist demo/build/run, evidence index và verified/deferred/TBD matrix. | Code và evidence thực tế để đồng bộ tài liệu cuối; release/visual/content/security approvals liên quan. Không ghi module VERIFIED chỉ vì có checklist. |

## C. Giao việc trước cho người tổng hợp

Giao **INTG-01/a–g trước**. Bộ bàn giao đầu tiên: handoff/contract registry candidate, synthetic fixture pack, fake-boundary runner, fault-case outcomes, lệnh chạy và compatibility gaps. Tất cả có thể tạo mà không cần implementation của P1/P2/P3.

Trong lúc đó làm mẫu composition/config/test/handover; chưa cần nối API, realtime canvas hoặc provider thật. Khi một luồng đủ component đầu vào, P4 chuyển sang card INTG tương ứng. Không giao P4 viết toàn bộ backend, renderer hay provider adapter thay các owner.

## Nguồn, khả năng tái sử dụng và giới hạn

- [SRS v3.1](../../FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md), [INTG cards và 14 handoffs](../../FEAT-040-four-person-delivery-plan/artifacts/TEAM_TASK_BREAKDOWN.md), [ADR-0006](../../../docs/adr/ADR-0006-parallel-sprint-allocation.md), [ADR-0015](../../../docs/adr/ADR-0015-four-person-role-and-integration-allocation.md), [contract/integration rules](../../../docs/architecture/CONTRACTS_AND_INTEGRATION.md).
- Tái dùng cơ chế fixture/version/hash/local-transport từ source hiện có sau khi rà semantics. Workflow Gate A/B, Parent/story/media fallback cũ không tự thành contract scope mới. `packages/contracts` là nơi boundary/schema, không chứng minh pack replacement-scope đã được adopt.
- Đây là khả năng bắt đầu độc lập, không xác nhận runner/connector mới đã tồn tại. Từng implementation vẫn cần feature plan/acceptance/task approval theo [workflow](../../../docs/governance/WORKFLOW.md). Không có lịch/ngày/ước lượng thời lượng, code change, messaging, Git push hoặc deployment trong task này.
