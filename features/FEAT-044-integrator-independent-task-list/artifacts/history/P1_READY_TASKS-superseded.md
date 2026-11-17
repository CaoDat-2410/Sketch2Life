# Task Người 1 có thể làm mà không chờ BE/P4

Người 1 là FE theo [phân công hiện tại](../../FEAT-040-four-person-delivery-plan/artifacts/TEAM_TASK_BREAKDOWN.md). **Bắt đầu bằng FE-01, rồi làm các phần UI/state với dữ liệu mẫu. Không cần BE, DB, GPU hay người tổng hợp chạy xong.** Các phần sau có thể cần nền tảng do chính P1 làm trước; đó là phụ thuộc nội bộ, không phải chờ người khác.

Các nhãn `/a…/f` dưới đây là checklist con của FE-01, không thêm task ID toàn hệ thống hoặc đổi tổng57 card. Danh sách này là kế hoạch công việc; chưa triển khai runtime trong yêu cầu hiện tại.

## 1. Nhận trước: nền tảng hoàn toàn độc lập

| Task | Việc làm cụ thể | Đầu ra đủ để bàn giao |
| --- | --- | --- |
| FE-01/a — Bộ component chung | Tái dùng theme hiện tại; chuẩn hóa button, input, card, dialog, tab, badge, alias/avatar, thông báo và trạng thái loading/empty/error/disabled. | Component showcase RN mở được không có backend, có màn ví dụ cho từng trạng thái. |
| FE-01/b — Điều hướng và trạng thái Child | Tách navigation/view state khỏi API; dựng các route/workspace cần cho Child. Teacher/Admin làm sơ đồ route, wireframe và view model trước khi chốt web framework. | Bấm qua luồng Child bằng fake data; reset về từng scenario; không kéo lại Parent/payment/credit flow cũ. |
| FE-01/c — Fake ports và fixture mới | Viết interface FE cần consume, fake adapter và synthetic fixture có version; mô phỏng độ trễ, typed errors, stale/revoked/unsupported-version. Lấy B19–B23 và các H-* làm đầu vào, ghi payload candidate còn cần review. | Một lệnh chạy demo khi BE tắt; đổi fixture được; manifest ghi revision/hash và payload/error examples. Không tự chốt contract của cả nhóm. |
| FE-01/d — Prototype canvas Android | Vẽ nét, chọn màu/độ dày, thử own-undo trên nét của mình; hiển thị active child và trạng thái on-device/sending/accepted/rejected bằng receipt giả. Đánh giá candidate trên stack hiện hữu, không khóa editor production. | Canvas local thao tác được; draft chưa gửi không hiện là server-saved; không undo nét synthetic của bạn khác. |
| FE-01/e — Bộ scenario lỗi/recovery | Tạo case mất mạng, request chậm/trùng, đổi lượt khi còn draft, vùng bị khóa, revoke và reconnect/checkpoint. Đây là simulator, chưa phải sync/offline persistence thật. | State matrix và component/state checks cho các guard quan trọng; bước tái hiện và kết quả mong đợi rõ. |
| FE-01/f — Hồ sơ bàn giao độc lập | Ghi cách chạy, fixture manifest, ảnh state synthetic, adapter seams và danh sách contract gap; đề xuất bài đo canvas nếu cần. | P2/P4 có thể đọc/chạy lại demo mà không cần service. Review của họ là checkpoint sau đầu ra, không chặn P1 tạo fixture trước. Chưa đo thì ghi chưa đo. |

Thứ tự nội bộ gợi ý: `/a + /b + /c → /d + /e → /f`. Sau `/c`, P1 đã có thể tự cấp dữ liệu cho các màn bên dưới. Không cần mở cả15 card FE cùng lúc.

## 2. Các phần UI có thể làm tiếp bằng dữ liệu mẫu

Đây là **slice UI/fixture** của các task gốc, không phải nghiệm thu đầy đủ runtime. Có thể dùng fixture đầu vào thay cho task FE upstream chưa hoàn tất; muốn nghiệm thu luồng thật phải quay lại các dependency và handoff của FEAT-040.

| Task gốc / màn | Phần không cần chờ người khác | Kết quả kiểm tra tại FE |
| --- | --- | --- |
| FE-02 · C01/C02 | Nhập mã phiên, QR qua fake scanner port, chờ GV duyệt, Lobby và chọn active child theo lượt; mã hết hạn/sai, bị từ chối/revoke. | Child join demo; không có child login; chưa được admit thì không hiện roster/canvas. Camera QR thật là phần thử riêng sau approval phù hợp. |
| FE-03 · T01–T04/T14 | Teacher home, danh sách lớp/hồ sơ, form tạo phiên, chọn topic/công cụ/nhóm, Lobby và preset. Fake Start pending/accepted/rejected. | Teacher setup prototype; enrollment khác consent; Teacher bấm Start rõ ràng; auto grouping chỉ là extension chưa chốt. |
| FE-04 · C03/C05/C10 | Dựng workspace cá nhân/nhóm trên prototype canvas; thanh công cụ, active contributor, khóa vùng, checkpoint/draft/reconnect presentation. | UI giữ tác giả nét cũ khi đổi lượt, trạng thái lưu đúng, own-undo không xóa nét peer. Đồng bộ nhiều máy/persist thật vẫn chờ H-CANVAS-SYNC. |
| FE-05 · T05/T06 | Dashboard lớp, thẻ nhóm, help queue, thumbnails synthetic, pause/resume/advance/end confirmation và clock/error state. | Hai nhóm có tiến độ khác nhau; nút pending không hiện thành công trước receipt; đồng hồ phiên không được gắn nhãn thời gian từng trẻ thực sự nhìn màn hình. |
| FE-06 · C04/T07 | Hàng đợi từng sketch, review approve/reject/correction; Child xem/ẩn/từ chối gợi ý. Mock pending/unsafe/stale/revoked. | Pending/unsafe/stale không hiện cho Child; AI overlay tách tranh gốc. Không cần model chạy. |
| FE-07 · C06/T08 | Thẻ tranh, preview, sắp xếp/chọn/present, empty/withdrawn/unauthorized; tách original và AI overlay. | Gallery demo bằng tranh synthetic; không thêm public share; không gán cả tranh nhóm cho một trẻ. |
| FE-08 · C07/T09 | Knowledge/script form, review video, generating/waiting, exhausted failure và playback error. Dùng placeholder hoặc media synthetic được phép để kiểm tra player. | Generating phải chờ; chỉ Teacher chọn retry/skip/end sau exhausted failure; script/video đổi sau review thì yêu cầu duyệt lại. Không claim đã sinh video thật. |
| FE-09 · C08/T10 | Activity card, vật liệu/an toàn/chỉ dẫn, phân cho nhóm, Teacher chuẩn bị/xác nhận, off-screen help/done signals. | Chỉ nhóm được chỉ định nhận nội dung; Child báo xong không tự chuyển cả lớp hoặc thành assessment. Nội dung fixture chưa là catalog đã duyệt. |
| FE-10 · C09/T11 | Reflection theo tuổi, Teacher observation/evidence form, draft/submit/correction và NOT_OBSERVED. | Child reflection, Teacher result và AI draft tách loại; double-submit giả không trùng; không ranking hoặc suy tính cách. Rubric chưa chốt giữ candidate. |
| FE-11 · T12/A07 | Portfolio timeline, bộ lọc, report layout và export pending/partial/ready/revoked. | Hiển thị nguồn/bằng chứng và giới hạn quyền bằng fixture; không báo export partial là complete; không tự áp90 ngày cho portfolio/profile/audit. |
| FE-12 · T13/A04 | Form soạn nội dung, validation, lịch sử phiên bản, yêu cầu review/publish/recall. | Teacher author không tự publish toàn trường; draft/review/published/withdrawn tách trạng thái. Chính sách reviewer/recall cần chốt trước nối thật. |
| FE-13 · A01/A02/A03 | Admin overview, bảng adult users/roles, lớp và Teacher assignment bằng synthetic metadata. | Loading/empty/stale/denied demo; không tạo child accounts, không coi Admin role là quyền xem raw child content. |
| FE-14 · A05/A06/A09 | Form policy candidate, job/incident status, redacted audit table và filter. | Không hiện token/QR/prompt/media nhạy cảm; stale khác zero; audit không sửa/xóa event cũ; không có config bypass Teacher review. |
| FE-15 · A08/A10 | Consent purpose matrix, evidence metadata, export/delete workflow, per-copy pending/partial/exception; policy draft/diff/validation. | Unverified khác verified; partial purge không thành completed;90 ngày chỉ session/artwork sau kết thúc; chính sách lớp dữ liệu khác giữ riêng. Không thực hiện xóa thật. |

## 3. Nên giao trước phần nào

**Lô đầu:** FE-01/a–f → FE-02 UI → FE-03 UI → FE-04 prototype. Đầu ra mong đợi là Child join/lobby/drawing và Teacher setup chạy với fake adapters, kèm những case pending/rejected/reconnect.

**Lô tiếp:** FE-05 → FE-06/07 → FE-08 → FE-09/10 → FE-11. FE-12–15 là nhóm form/table/state có thể nhận thêm khi nền tảng đã ổn; phần Teacher/Admin giữ wireframe/view-model nếu ADR web chưa được adopt. Không có ngày hoặc ước lượng thời lượng trong cách chia này.

## 4. Phần cần chờ trước khi nối thật

- BE/P4 review và adopt versioned contract: auth/admission/grants, canvas receipt/checkpoint/sync, session controls, AI review/job/media, content/policy và data lifecycle. P1 có thể đề xuất candidate ngay; không tự biến fixture thành contract chung.
- Backend mới chứng minh permissions, persistence, retry idempotency, consent/revocation và scope thực tế. Ẩn nút hoặc fake success không chứng minh các điều đó.
- ADR còn mở cho web framework Teacher/Admin, production editor/sync, advanced tools, offline-local retention, model/retry/media và các policy TBD. Không cần đợi những quyết định này để viết wireframe/state model, nhưng không tự chốt bằng demo.
- [43 ảnh FEAT-043](../../FEAT-043-srs-ui-screen-set/artifacts/SCREEN_INDEX.md) là nguồn tham khảo REVIEW_PENDING. Chưa copy chúng vào approved/applied hoặc dùng như assets đã duyệt. Theme/component đã có có thể tái sử dụng; schema/mockData Parent/story cũ phải rà lại theo SRS mới.
- Các task implementation cần owning feature plan/acceptance/task approval như [workflow](../../../docs/governance/WORKFLOW.md). Yêu cầu hiện tại chỉ lập danh sách; không áp dụng thay đổi app.

## 5. Bàn giao mỗi phần UI

Giao component/view model + fake adapter + fixture/version manifest + lệnh chạy + state matrix/evidence. Tối thiểu phân biệt loading, empty, pending, accepted, denied, stale, revoked và lỗi/retry phù hợp với từng màn. Dùng synthetic data; giữ secrets/provider endpoints/real child data ngoài FE. Người tổng hợp sẽ thay adapter và nối runtime sau, còn P1 giữ ownership logic UI và sửa lỗi của mình.

## Nguồn và giới hạn

Nguồn: [Master SRS v3.1](../../FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md), [57 task/15 FE cards](../../FEAT-040-four-person-delivery-plan/artifacts/TEAM_TASK_BREAKDOWN.md), [ADR-0006](../../../docs/adr/ADR-0006-parallel-sprint-1-delivery.md), [ADR-0015](../../../docs/adr/ADR-0015-four-person-role-and-integration-allocation.md), theme và fixture-runner hiện có trong apps/ui-mobile và apps/mobile. ADR-0006 giữ độc lập của runner; vai trò mới theo ADR-0015. Đây là checklist có thể bắt đầu, không phải xác nhận implementation đã tồn tại hoặc đã được nghiệm thu.
