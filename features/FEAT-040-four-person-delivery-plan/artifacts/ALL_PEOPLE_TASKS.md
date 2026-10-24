# Task cho cả 4 người — bản xem nhanh

Giữ phân công 1 FE / 2 BE / 1 người tổng hợp. **57 task: Người 1 có 15, Người 2 có 16, Người 3 có 14, Người 4 có 12.** Đây là bảng xem nhanh của backlog hiện có, không đổi ID hoặc phân việc.

★ = task foundation có thể bắt đầu độc lập bằng synthetic fixtures/fake adapters, không cần output của ba người còn lại. Task khác giữ dependency/gate trong [bản chi tiết](TEAM_TASK_BREAKDOWN.md); có thể chuẩn bị UI/domain/schema/test scenarios trước, nhưng không coi đó là nghiệm thu toàn card.

## Giao ngay cho cả 4 người

| Người | Task độc lập | Đầu ra đầu tiên |
| --- | --- | --- |
| Người 1 — FE | FE-01 | Theme/component/navigation, fake API ports, UI state fixtures và prototype canvas Android; runner khi BE tắt. |
| Người 2 — BE lõi | BE1-01 | Domain/application rules, ports và command/result/error/permission/age fixtures; runner với in-memory test adapters. |
| Người 3 — BE AI | BE2-01, chặng foundation | Job/attempt/review state machine, fake provider/queue/clock/store, polling/error/cancel/stale và provider-copy receipts; runner không GPU/live BE. |
| Người 4 — Tổng hợp | INTG-01 | Handoff/contract candidate registry, synthetic fixture pack, fake-boundary runner, fault cases và compatibility map. |

Bốn foundation chạy song song; registry của P4 không chặn ba người còn lại tạo foundation riêng. Sau đó cross-review payload/version/error/hash, adopt contract cho phạm vi cần nối. P3 vẫn sở hữu durable job repository/migrations/outbox của AI ở chặng runtime riêng.

## Người 1 — FE — 15 task

React Native Android cho Child; UI Teacher/Admin; canvas/input và logic UI.

| ID | Task |
| --- | --- |
| FE-01 ★ | Nền tảng UI chạy độc lập và prototype canvas Android |
| FE-02 | Child join, admission, Lobby và chọn lượt |
| FE-03 | Teacher lớp, tạo phiên, Lobby và preset |
| FE-04 | Canvas, cộng tác, turn attribution và recovery |
| FE-05 | Teacher live dashboard và group workspace |
| FE-06 | AI request, Teacher review queue và Child agency |
| FE-07 | Gallery và trình bày tác phẩm |
| FE-08 | Knowledge/video review, wait và failure disposition |
| FE-09 | Activity assignment và off-screen handoff |
| FE-10 | Reflection, observations và assessment |
| FE-11 | Portfolio, learning reports và scoped exports |
| FE-12 | Teacher authoring và Admin content governance |
| FE-13 | Admin overview, adult accounts và school/class configuration |
| FE-14 | Admin AI policy, monitoring/incident và audit |
| FE-15 | Admin consent/data requests và lifecycle policy |

## Người 2 — BE lõi — 16 task

Auth/scope, lớp/hồ sơ/consent, session/group/canvas, lưu dữ liệu, portfolio và privacy.

| ID | Task |
| --- | --- |
| BE1-01 ★ | Đặc tả domain và bộ fixture backend lõi độc lập |
| BE1-02 | Durable core adapters, migrations và transaction/outbox |
| BE1-03 | Adult authentication, assignments và device-grant lifecycle |
| BE1-04 | Class, managed child profiles và enrollment |
| BE1-05 | School-mediated consent và purpose enforcement |
| BE1-06 | Session configuration, preset snapshot, lobby và explicit Start |
| BE1-07 | QR/mã phiên, pending device và Teacher admission |
| BE1-08 | Manual groups, progress/help, move và leave |
| BE1-09 | Turn attribution và authorized canvas operation log |
| BE1-10 | Canvas sync, checkpoints, restore và reconnect recovery |
| BE1-11 | Teacher control, phase transitions và durable finish |
| BE1-12 | Scoped read models và mediated artifact delivery |
| BE1-13 | Gallery snapshots, trình bày và chú thích |
| BE1-14 | Observation, reflection, assessment và portfolio |
| BE1-15 | Retention 90 ngày, export/delete và copy-purge workflow |
| BE1-16 | Automatic grouping proposal và Teacher commit (Phase 2) |

## Người 3 — BE AI/nội dung — 14 task

AI/jobs/review, knowledge/video, activities/content/preset, provider và dữ liệu job riêng.

| ID | Task |
| --- | --- |
| BE2-01 ★ | AI/job contract foundation và harness độc lập |
| BE2-02 | Tái sử dụng Vision và correction có provenance |
| BE2-03 | Assistance request, cancel, dedup và budget orchestration |
| BE2-04 | Pipeline tạo Sketch thật và output tách tranh gốc |
| BE2-05 | Moderation và Teacher duyệt từng Sketch |
| BE2-06 | Child view/hide/decline và tiếp tục vẽ |
| BE2-07 | Knowledge có nguồn và script versioning |
| BE2-08 | Library resolution và pipeline video generation thật |
| BE2-09 | Final video review và authorized playback |
| BE2-10 | Video exhausted failure: Teacher retry/skip/end |
| BE2-11 | Activity discovery, adaptation và execution |
| BE2-12 | Content authoring, publication review và recall |
| BE2-13 | Preset versioning, conditional automation và Teacher override |
| BE2-14 | System AI configuration, limits và kill switch |

## Người 4 — Tổng hợp kỹ thuật — 12 task

Composition, connectors FE–BE, nối luồng, môi trường chung và kiểm tra/bàn giao tích hợp.

| ID | Task |
| --- | --- |
| INTG-01 ★ | Bộ fixture tích hợp và sổ contract dùng chung |
| INTG-02 | Composition root và điểm vào backend/worker |
| INTG-03 | Kết nối Child Android, Teacher và Admin với API |
| INTG-04 | Nối canvas realtime, lượt vẽ và recovery |
| INTG-05 | Nối snapshot → Vision → Sketch → Teacher review → Child |
| INTG-06 | Nối gallery → knowledge → video → playback và failure controls |
| INTG-07 | Nối hoạt động, reflection, assessment, portfolio và kết thúc phiên |
| INTG-08 | Nối Admin, consent, content recall và data lifecycle xuyên hệ thống |
| INTG-09 | Bộ kiểm thử tích hợp chín bước và quản lý lỗi theo owner |
| INTG-10 | Môi trường chạy chung, config và quan sát hệ thống |
| INTG-11 | Xác nhận hệ thống ở tải pilot và tổng hợp device/model evidence |
| INTG-12 | Bàn giao hệ thống, demo và hồ sơ kỹ thuật |

## Cách nối và ranh giới

- P1 làm UI/state; P2 core/classroom/canvas/privacy; P3 AI/content/media; P4 nối qua versioned ports/contracts. Component owner vẫn giữ tests và sửa lỗi phần mình.
- P4 nối ngay từng luồng khi đủ output: lớp/consent/join → canvas/control/recovery → gallery/knowledge/video → off-screen/reflection/portfolio. Không cần chờ cả 57 task.
- Sketch là nhánh tùy chọn; gallery/video có path không yêu cầu Sketch. Knowledge/video không buộc chờ model Sketch chạy.
- BE1-16 automatic grouping thuộc Phase 2; manual grouping của pilot chạy trước, không lấy extension làm blocker toàn pilot.
- FastAPI và React Native/Android đã chốt; web Teacher/Admin, DB/queue/editor/model và policies còn mở giữ ADR/feature gate. Bộ ảnh FEAT-043 vẫn REVIEW_PENDING.
- Đây là kế hoạch, không phải bảng chứng minh code đã xong. Từng implementation cần owning feature plan/approval; mock success không là auth/persistence/generation/load evidence. Không có lịch/ngày/ước lượng thời lượng cho công việc.

## Nguồn

- [Task cards, dependencies, handoffs, SRS trace và acceptance](TEAM_TASK_BREAKDOWN.md).
- [Master SRS v3.1](../../FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md).
- [Checklist độc lập người tổng hợp/P4](../../FEAT-044-integrator-independent-task-list/artifacts/INTEGRATOR_READY_TASKS.md).
- [ADR-0015 — phân vai hiện tại](../../../docs/adr/ADR-0015-four-person-role-and-integration-allocation.md).
