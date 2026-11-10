# Rà soát luồng Web của ba role theo SRS v2.7-draft Rev57

- Ngày rà: 2026-11-10 (Asia/Bangkok)
- Trạng thái: hoàn tất rà soát source và contract; chỉ audit, chưa sửa source/UI/API.
- Worktree: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation
- Branch: codex/fe-ui-web-remediation
- SRS authority: F:/Github/Sketch2Life/docs/context/SRS_AUTHORITY.md
- SRS chuẩn: features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md
- Baseline: v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; draft vẫn chờ owner sign-off.
- Ranh giới yêu cầu: chỉ §§1–31 là target requirements; §32 là source/as-built evidence, không dùng làm yêu cầu.
- Roles: Teacher (teacher), School Manager (school_manager), Platform Admin (platform_admin) theo §3; không audit Parent hoặc apps/admin-ui.

## Cách rà và giới hạn bằng chứng

Đã đọc SRS authority và xác minh hash trên đúng file canonical; rà route, API adapter, màn hình và router/contracts backend liên quan trong worktree. So sánh route mục tiêu theo §§3, 5, 7, 19–21, 23, 28, 30–31. Các evidence FEAT-066 trước đó được dùng như lịch sử triển khai; các gap được kiểm tra lại trên source hiện tại.

Đây là source/contract review, không phải xác nhận end-to-end bằng tài khoản thật. Không dùng credential, backend production, dữ liệu người dùng/trẻ thật hay provider ngoài; không chạy automated test/build và không thay đổi mã ứng dụng. Không chạy local browser capture mới trong lượt audit này. Worktree root và branch xác minh đúng; git status --short --branch hiện trả fatal: this operation must be run in a work tree, do đó trạng thái dirty hiện tại không thể đối soát bằng Git status trong lượt này. Không checkout, dọn hoặc sửa checkout gốc.

Mức độ:
- P1: luồng bắt buộc không thể hoàn tất ở chế độ sản phẩm, hoặc UI có thể báo thành công khi chưa có thay đổi bền vững.
- P2: luồng một phần, gây hiểu sai quyết định/quyền, mất khả năng phục hồi, hoặc không thể xem đủ danh sách.

## Kết quả tổng quan

| Role | Trạng thái luồng hiện tại |
|---|---|
| Teacher | Có đăng nhập/local preview, workspace, danh sách lớp, lesson CRUD/review request và upload API. Chưa thể hoàn tất chuỗi occurrence → chọn trẻ do hệ thống → run/video → xác nhận chiếu bằng product API; các màn import/review và roster còn khoảng trống. |
| School Manager | M01 có API cho access grant review/decision; M02 ở backend mode mới đọc class list/roster. Capacity/lifecycle/Teacher management, billing/quota, inbox và feedback chưa hoàn chỉnh hoặc chưa có API. M01 còn có thể duyệt mà không xem nội dung đúng version. |
| Platform Admin | Backend sign-in dừng với ROLE_DISCOVERY_UNAVAILABLE (501). A01 moderation queue, catalog publish và phần lớn A02 operations không có luồng API product hoàn chỉnh; preview có thao tác cục bộ trông như đã hoàn tất. |

## Teacher — findings

### T-01 — P1 — Chuỗi occurrence → sample run → video → projection không chạy được trong backend mode

**SRS:** FR-T-08, FR-T-10–16, FR-T-18–19; §5.2 UC-05/17; §21.2/21.5/21.6.

**Hiện trạng:** apps/teacher-ui/src/App.tsx chuyển T04, T06 và T07 sang ApiUnavailableView ngoài local preview. T01 backend mode chỉ tải assignment/class/lesson; T05 có class/profile reads. FE adapter hiện không gọi product API cho occurrence/plan revision, random sample selection, StoryRun, job state, script confirm, video playback/regeneration, projection confirmation, quota admission hay completion/cancel.

**Contract boundary:** backend có StoryRun-lite routes riêng, nhưng composition ghi rõ đây là demo tổng hợp, unauthenticated và loopback-only; không phải product API để mở các luồng đó trong FE production. Không tính contract này là hỗ trợ sản phẩm.

**Ảnh hưởng:** Teacher không thể thực hiện các màn bắt buộc của §21.5 sau khi chuẩn bị lesson/lớp; các màn xem thử không thể dùng để xác nhận trạng thái API/SRS.

**Hướng sửa sau:** chỉ nối FE vào product contracts có auth/scope/version/state hợp lệ; triển khai từng stage cùng hành vi lỗi §21.6. Nếu contract chưa sẵn sàng, giữ trạng thái unavailable rõ ràng, không biến demo StoryRun-lite thành product flow.

### T-02 — P1 — Không tạo được hồ sơ Teacher và occurrence từ luồng backend của UI

**SRS:** FR-T-04/05/08; §19 UC-03/04/05; §21.2/21.5.

**Hiện trạng:** T05 ở backend mode chỉ tải class/profile/consent và render danh sách chỉ đọc. FE không có form POST profile; không có route/adapter tạo occurrence hoặc plan. BE1 có endpoint tạo profile, nhưng FE không gọi; API class hiện tại cũng chưa cung cấp luồng occurrence/plan sản phẩm. Phần thêm hồ sơ trong preview chỉ cập nhật fixture.

**Ảnh hưởng:** Teacher không thể bắt đầu luồng từ hồ sơ/lớp tới buổi dạy qua product UI. Dữ liệu preview không tạo enrollment hoặc lineage bền vững.

**Hướng sửa sau:** bổ sung form và API adapter theo typed request/consent/scope rules; nối occurrence và plan với expected revision/hash. Không dùng profile fixture làm dữ liệu server.

### T-03 — P1 — Upload tài liệu dừng trước bước sửa và xác nhận structured draft

**SRS:** FR-T-06/07; FR-PL-09/10/11; §21.2.

**Hiện trạng:** T03 backend mode tải tệp, đọc extraction revision rồi chỉ hiện extracted_fields dạng JSON/preformatted content. Màn hình thông báo cần rà/sửa structured content nhưng không có editor/confirm action gắn với source revision; shared API adapter không có method tạo LessonVersion với source_document_revision_id. T02 tạo lesson riêng từ content nhập tay, không nối lại provenance của bản extraction.

**Ảnh hưởng:** Không thể hoàn tất yêu cầu giữ original/provenance, sửa thành revision mới và xác nhận draft trích xuất trước khi dùng. Trang upload kết thúc ở trạng thái “đã xử lý” chứ chưa đạt “Teacher reviewed/confirmed”.

**Hướng sửa sau:** hiển thị structured fields có thể sửa, lưu revision bất biến và confirm đúng source hash/revision; chỉ cho dùng sau xác nhận. Tôn trọng lỗi template/parser và allowlist, không gửi original hoặc toàn văn chưa lọc cho AI.

### T-04 — P2 — Preview cho Teacher tự chọn trẻ và có fallback ra roster lớp khác

**SRS:** FR-T-10, FR-PL-20; §5.2 decision table UC-05; Q-01.

**Hiện trạng:** T06 có dropdown “Chọn 1 học sinh”; khi roster lớp đang chọn rỗng, eligible fallback sang toàn bộ active roster của Teacher. Route này chỉ dùng local preview nên đây không phải bằng chứng rò rỉ dữ liệu production, nhưng flow minh họa trái invariant random selection.

**Ảnh hưởng:** Người rà/test có thể học sai rằng Teacher tự chọn trẻ hoặc có thể lấy trẻ từ lớp khác. Quy tắc hệ thống chọn ngẫu nhiên vẫn đã chốt; Q-01 chỉ để mở cách tính eligibility, consent, reselection và empty-set.

**Hướng sửa sau:** trong product flow nhận đúng một lựa chọn từ server theo policy đã được owner duyệt, hiển thị để Teacher xác nhận; không fallback sang lớp khác. Chưa tự chọn policy cho các case Q-01.

### T-05 — P2 — Nhãn consent trên roster không được liên kết với consent record cụ thể

**SRS:** §3, §5.2 UC-05, §10, §20; FR-T-10/FR-PL-08/20.

**Hiện trạng:** T05 tải profile và consent độc lập bằng Promise.allSettled; mỗi profile sau đó luôn nhận chip “Consent effective”. Chip không được tính từ child_id + purpose_ref + effective/revision của consent response, và profile vẫn render nếu consent request riêng thất bại. API profile hiện cũng kiểm tra consent phía server và có thể từ chối toàn bộ list, nên finding này không khẳng định backend cấp quyền sai; nó nói UI không thể giải thích/đối chiếu consent đúng trạng thái.

**Ảnh hưởng:** Teacher/tester có thể đọc nhầm một badge chung là consent cho mục đích hiện tại đã được xác nhận, kể cả khi response consent không có hoặc lỗi.

**Hướng sửa sau:** derive state từ consent record cùng child/purpose hiện hành; nếu không đối chiếu được thì ghi “không xác định/chưa tải được”, không khẳng định effective.

### T-06 — P2 — Upload session không phục hồi sau reload dù contract có GET status

**SRS:** §21.2 upload-session GET/status/accepted-parts; §21.6; FR-C-12.

**Hiện trạng:** session id, file và part progress chỉ nằm trong React component state. API adapter có create/part/complete/abort nhưng không expose GET /upload-sessions/{upload_id}; sau reload không còn session id để hỏi server và tiếp tục đúng tệp.

**Ảnh hưởng:** Một phiên đã nhận part có thể bị bỏ dở; retry upload sau timeout có thể mở phiên khác thay vì resume.

**Hướng sửa sau:** giữ opaque session ref và file hash an toàn qua reload, gọi GET status, bắt người dùng chọn lại tệp và xác minh hash trước khi gửi các part còn thiếu.

### T-07 — P2 — Lesson list không theo next_cursor

**SRS:** §21.1 yêu cầu cursor pagination cho list API; §21.5 Teacher lesson workspace.

**Hiện trạng:** response type LessonPage có next_cursor, adapter nhận cursor nhưng TeacherApiLessonPage chỉ lấy page.items; không có gọi tiếp hoặc thao tác “xem thêm”.

**Ảnh hưởng:** Nếu danh sách vượt một page, Teacher không thể tìm/chọn lesson cũ hơn trong UI.

**Hướng sửa sau:** dùng cursor opaque, thứ tự server, loading/error/empty states và nạp thêm page; không tự dựng cursor từ item id.

## School Manager — findings

### M-01 — P1 — M01 có thể quyết định PUBLIC mà không xem nội dung đúng version được gửi duyệt

**SRS:** FR-PL-05; §3/§20; §21.5 School Manager; §31.2 version/approval gate.

**Hiện trạng:** backend M01 tải access grants và LessonSummary, sau đó cho phép approve khi đủ bốn checkbox. Panel chỉ hiện title/topic/current version number/activity count và grant metadata; không fetch/render lesson content hoặc compare. Nhãn version ưu tiên LessonSummary.current_version_no, trong khi grant chỉ đích danh version_id; vì vậy UI không chứng minh checklist đang áp dụng cho đúng version được duyệt. API có GET lesson detail cho Manager, nhưng trang M01 hiện không gọi detail endpoint. Không tải media/story trẻ, phù hợp ranh giới privacy.

**Ảnh hưởng:** Manager có thể xác nhận và publish một request mà không nhìn thấy structured content của version đó. Đây là lỗi luồng review, dù API quyết định access grant có hoạt động.

**Hướng sửa sau:** tải đúng immutable version được grant chỉ ra, hiển thị nội dung lesson/diff metadata cần review, gắn decision với revision/version được xem; giữ nguyên privacy boundary, không tải child media. Cần xác định contract GET-by-version nếu GET detail hiện chỉ trả current version.

### M-02 — P1 — Capacity, class lifecycle và Teacher assignment không hoàn tất được ở backend mode

**SRS:** FR-T-02/03/05; FR-B-07; §19 UC-06/12/13; §21.5.

**Hiện trạng:** M02 backend mode chỉ list class và roster read-only; không tạo/archive/suspend lớp, không phân công/chuyển/offboard Teacher, không provision Teacher hoặc recovery account. BE1 có POST class và assignment cơ bản, nhưng class-create contract hiện không kiểm capacity trong transaction và chưa có teacher directory/lifecycle saga; FE vì vậy tắt create action.

**Ảnh hưởng:** School Manager chưa thể quản lý capacity-safe class roster/lifecycle theo organization. Đây là dependency FE + backend/contract, không thể hoàn tất bằng UX-only.

**Hướng sửa sau:** cần capacity summary/atomic guard, class archive/suspend, teacher directory/provisioning/transfer/offboard contracts trước; sau đó mới nối UI và xử lý retry/pending/compensation theo UC-12/13. Không đưa slot/class ra khỏi capacity để giả lập.

### M-03 — P1 — Billing, invoice, payment, subscription và quota chưa có flow sử dụng được

**SRS:** FR-B-01–12, FR-PL-24; §19 UC-08/10; §21.5.

**Hiện trạng:** backend M02 hiển thị các mục này là unavailable; dashboard/quota fixture chỉ là số xem thử. Client không có API invoice/payment/subscription/renewal/downgrade, organization quota summary/top-up. Capacity downgrade chọn lớp và suspension cũng chưa có contract hoàn chỉnh.

**Ảnh hưởng:** Manager không thể xem invoice/payment state, quản lý subscription hay mua quota/slot từ sản phẩm.

**Hướng sửa sau:** cần billing contracts và server-owned price version, invoice/payment attempt/status, subscription events, capacity/quota summary và downgrade suspension. Không tự điền giá, chu kỳ/proration/refund hoặc chính sách thương mại còn OPEN; không tạo giao dịch/toast thành công giả.

### M-04 — P1 — Inbox billing notices và phản hồi feedback theo trường chưa có luồng

**SRS:** FR-B-08/09, FR-PL-22; §21.5 School Manager.

**Hiện trạng:** chuông đã là trạng thái “Hộp thư thông báo chưa khả dụng”, không còn chấm unread gây hiểu nhầm. Tuy vậy UI chưa đọc inbox; cũng chưa có màn reply feedback trong tenant.

**Ảnh hưởng:** Manager không thể xem nhắc billing/notice hoặc phản hồi feedback được gửi về trường. Đây là flow bị thiếu do API, không phải lỗi tín hiệu unread hiện tại.

**Hướng sửa sau:** nối inbox khi có notification contract, và feedback thread/reply API có scope tenant + audit. Giữ payload tối thiểu, không trả child media/story.

### M-05 — P2 — M01 không nạp page tiếp theo của access-grant queue

**SRS:** §21.1 cursor pagination; §21.5 review queue.

**Hiện trạng:** FE dùng grantPage.items và lessonPage.items, bỏ qua next_cursor ở cả hai response.

**Ảnh hưởng:** Khi queue/list vượt một trang, Manager không thể review đủ yêu cầu.

**Hướng sửa sau:** thêm cursor navigation/load-more cho grant queue và metadata lessons; giữ stable order và hiển thị lỗi page tiếp theo.

### M-06 — Owner clarification — Bốn tiêu chí duyệt M01 chưa được SRS chốt

**SRS:** FR-PL-05 xác định Manager approval gate nhưng không định nghĩa bốn tiêu chí; §14.1 OI-17 yêu cầu product/design sign-off cho review workflow.

**Hiện trạng:** cả API-mode lẫn local preview yêu cầu bốn checklist để approve. Đây là rule đang có trong UI, nhưng chưa đủ căn cứ gọi là yêu cầu SRS đã duyệt.

**Hướng xử lý:** xin owner xác định rubric và liệu checkbox có phải hard gate; đến lúc đó ghi là OPEN, không tự gỡ hoặc nâng thành policy chuẩn trong audit này.

## Platform Admin — findings

### A-01 — P1 — Không đăng nhập được Platform Admin bằng backend mode

**SRS:** §3, §20; FR-PL-01; §21.5 Platform Admin/Admin permission surfaces.

**Hiện trạng:** signInAndResolveRole("platform_admin", …) sign-out và trả ROLE_DISCOVERY_UNAVAILABLE (501) vì backend chưa có API đọc assignment/permission Platform Admin. Login UI/route tồn tại nhưng không thể xác nhận role và vào phiên sản phẩm.

**Ảnh hưởng:** mọi flow Platform Admin có backend đều bị chặn trước khi mở màn hình.

**Hướng sửa sau:** cần server-side role/capability discovery có permission scope/audit/revoke theo FR-PL-01; không tin role tự chọn từ UI.

### A-02 — P1 — Moderation queue không có product list/detail; preview hide/unhide chỉ đổi state cục bộ

**SRS:** FR-PL-05; §3/§20; §21.5 Platform Admin content surface.

**Hiện trạng:** backend A01 trả unavailable vì API hiện chỉ có PATCH .../platform/lessons/{lesson_id}/moderation; chưa có API liệt kê queue hoặc lấy revision/content có thể review. Trong local preview, ẩn/hiện đổi React state rồi toast “đã ẩn/hiện”, không tạo server result bền vững.

**Ảnh hưởng:** moderation/hide/unpublish không chạy ở product mode; preview có thể khiến tester tưởng dữ liệu hệ thống đã đổi.

**Hướng sửa sau:** thêm authorized queue/detail contract cùng exact version/revision và reason/audit, rồi gọi moderation endpoint; local preview toast phải ghi rõ kết quả chỉ cục bộ hoặc action bị disable.

### A-03 — P1 — Tạo/publish hoạt động catalog chỉ là thao tác mảng local

**SRS:** UC-14; FR-PL-12/14; §21.5 Platform Admin content surface.

**Hiện trạng:** preview A02 thêm chuỗi vào state activities và báo “Đã phát hành hoạt động mới vào danh mục chuẩn”. Không có version bất biến, trạng thái draft/review/publish, provenance hoặc API catalog. Backend mode A02 chỉ mở health view và thông báo các mục này chưa kết nối.

**Ảnh hưởng:** UI tuyên bố xuất bản một hoạt động nhưng chỉ thay local state; flow không thể test acceptance/provenance của catalog.

**Hướng sửa sau:** cần catalog item/version + draft/review/publish API có permission và audit; giữ AI-produced activity ở draft đến khi authorized review theo FR-PL-12.

### A-04 — P1 — A02 chỉ kiểm tra /health; các flow operations khác là unavailable/fixture

**SRS:** §21.5 Dashboard operator; FR-O-07; §3/§20 permission boundary.

**Hiện trạng:** API screen có health check, nhưng không có queue/job aggregates, billing reconciliation, lifecycle backlog hoặc audit feed. Organization/catalog/quota/audit trên preview là fixture và stat buttons chỉ toast thông tin; backend mode nói rõ các nguồn này chưa tải được.

**Ảnh hưởng:** operator không có dashboard vận hành theo inventory SRS. Màn hiện tại kết hợp số liệu mock trong preview và một health probe trong backend mode.

**Hướng sửa sau:** cần các aggregate endpoints đã redact và scope truy cập tách bạch; không nối màn operator vào child profile/story/media.

### A-05 — P2 / cần chốt capability — Admin UI chưa tách Platform Admin permission với operator principal

**SRS:** §3 và §20 xác định Content Admin là permission capability trong Platform Admin; §21.5 tách “Platform Admin — Quản trị nội dung” khỏi “Dashboard operator”, operator là technical principal chứ không phải role sản phẩm.

**Hiện trạng:** app gộp content moderation, catalog/policy, tổ chức và health/operations dưới cùng cổng ADMIN; chưa có API capability discovery nên không thể chứng minh một tài khoản chỉ thấy đúng hành động được cấp.

**Ảnh hưởng:** ranh giới role/permission trong UI chưa truy vết được. Không kết luận có authorization bypass vì backend action thật hiện không khả dụng và backend vẫn phải là nguồn kiểm tra quyền.

**Hướng sửa sau:** làm rõ capability matrix/actor routing với owner và expose permission-aware API; UI chỉ hiển thị/enable action theo capability đã xác minh, backend tiếp tục authorize mỗi request.

## Cross-cutting — findings

### X-01 — P2 — Idempotency key chưa được giữ cho lần retry cùng một command

**SRS:** §21.1/21.4: client phải giữ cùng key khi retry lại cùng command logic.

**Hiện trạng:** shared API helper tạo Idempotency-Key mới bên trong mỗi method invocation; caller không truyền operation key vào. createClass hiện không gửi Idempotency-Key. Với timeout không rõ server đã nhận hay chưa, bấm lại có thể gửi key khác (ví dụ lesson create, upload session, access-grant decision).

**Ảnh hưởng:** không bảo đảm dedupe/replay kết quả gốc; có nguy cơ duplicate create/session hoặc state retry không thể đối soát.

**Hướng sửa sau:** tạo key một lần theo logical command, giữ qua retry, bỏ key khi người dùng bắt đầu command mới; kiểm tra tất cả mutation, gồm class creation, với contract tương ứng.

### X-02 — P2 — Error recovery của list/mutation chưa được đánh giá end-to-end

Source review xác nhận API pages hiện có error labels, nhưng chưa chạy authenticated session để kiểm tra token refresh, stale revision, timeout ambiguity, Retry-After, RATE_LIMITED hoặc resume/reconciliation flow giữa FE và backend. Đây là giới hạn xác minh, chưa được tính là lỗi runtime độc lập trong audit này.

## Các điểm đã đúng hoặc đã được ghi nhận riêng

- Đăng xuất có nút trên cả Teacher, School Manager và Platform Admin; EV-015 đã ghi nhận manual local activation/clear-session behavior. Không tính thiếu logout là lỗi hiện tại.
- M01 preview đã tách approvedIds và changeRequestedIds; request chỉnh sửa không còn tăng approved counter. Đây là remediation trước đó, không phải lỗi còn mở.
- Inbox School Manager hiện báo unavailable và không tạo unread dot giả. Thiếu inbox API vẫn là flow blocker ở M-04.
- Manager roster chỉ render tên và không request/hiển thị media/story trẻ; privacy boundary được giữ.
- Local preview counters và trạng thái fixture cần hiểu là dữ liệu minh họa; không đối chiếu chúng với quota, billing hoặc org production.
- Giá VND, policy renewal/proration/refund, một số eligibility/reselection/no-eligible behaviors và no-preset Parent catalog behavior còn OPEN trong SRS; không coi thiếu quyết định mở là lỗi đã chốt, không suy ra giá/chính sách.

## Kết luận và thứ tự xử lý đề xuất

1. Chốt product API/permission dependencies cho Platform Admin sign-in/content operations và Teacher occurrence/StoryRun/Sketch Deck.
2. Hoàn thiện School Manager review đúng immutable version, rồi capacity/Teacher lifecycle/billing/inbox/feedback contracts.
3. Hoàn thiện Teacher extraction review, profile/occurrence entry, random sample confirmation, recovery và list pagination.
4. Giải quyết X-01 idempotency end-to-end và xác nhận các OPEN owner decisions trước khi thay đổi UX/flows.
5. Sau khi owner chọn implementation scope, mới lập plan/acceptance cho remediation. Audit này không phê duyệt sửa product code.
