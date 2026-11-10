# Hướng dẫn test tuần tự toàn bộ luồng School Manager Web — SRS v2.7-draft Rev57

## Baseline và cách dùng

- Nguồn yêu cầu duy nhất: SRS FEAT-063 v2.7-draft Rev57, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`. Authority hiện tại xác nhận bản này vẫn chờ owner sign-off. Chỉ §§1–31 là yêu cầu đích; §32 là snapshot as-built và không dùng làm yêu cầu.
- Màn hình School Manager bắt buộc trong §21.5: dashboard organization; sức chứa lớp; tạo/archive/tạm ngưng lớp; phân công Teacher; roster; billing/invoice/payment; tự gia hạn/hạ gói; quota organization/top-up; inbox thông báo. Các flow liên quan: UC-03, UC-06, UC-08, UC-10, UC-12, UC-13, UC-15; FR-T-02–05, FR-B-01–14, FR-PL-05, FR-PL-22, §31.2/31.6/31.7, AC-58.
- Bản guide này tách **yêu cầu đích** khỏi **khả năng đang có trong FE/API đã kiểm tra**. SRS v2.7 là draft; nội dung này không phải sign-off.
- Chỉ dùng preview local `http://127.0.0.1:5173/` với dữ liệu fixture tổng hợp. Không dùng tài khoản thật, trẻ thật, backend production hay provider thanh toán/email/push. Không gửi mutation đến backend khi chưa có hợp đồng phù hợp.
- Trạng thái trong guide: **Có thể rà FE local** = kiểm tra layout/nhãn/tương tác fixture, không chứng minh dữ liệu được lưu; **Có API đọc/duyệt** = hợp đồng đã được rà source nhưng không gọi API trong lần kiểm tra này; **Bị chặn** = API/contract hoặc UI cần thiết chưa có; kiểm tra phải dừng ở thông báo unavailable, không mô phỏng thành công.

## Route map hiện tại

| Khu vực | Route hiện tại | Ghi chú |
|---|---|---|
| Đăng nhập | `/login` | Có chế độ xem thử local; không xác thực production. |
| Dashboard organization | `/m02-organization-management` | Các số tổng quan hiện là fixture, không phải API summary. |
| Teacher/nhóm | `/m02-organization-management?section=teachers` | Chưa có Teacher directory/invite hợp đồng đầy đủ cho Manager. |
| Lớp/sức chứa/roster | `/m02-organization-management?section=classes` | API đọc danh sách lớp và roster đã có; tạo an toàn theo capacity và archive/suspend chưa có đủ contract. |
| Quota organization | `/m02-organization-management?section=quota` | Chưa có API quota summary/top-up của organization. |
| Settings/billing | `/m02-organization-management?section=settings` | Chưa có billing/invoice/payment/subscription API. Không có giá/chính sách để test. |
| Duyệt Teacher lesson PUBLIC | `/m01-publication-review` | Có API access-grant list/decision; preview local không lưu. Manager không xem child media/story. |
| Inbox | Không có route | Không có inbox API; UI hiển thị `Hộp thư chưa khả dụng`, không có unread dot/click giả. |
| Feedback reply | Không có route | Không có School Manager reply API/contract. |
| Logout | Nút sidebar trên route đã đăng nhập | Dùng `TeacherContext.logout`; được bổ sung theo phát hiện trực tiếp của user, không phải screen requirement riêng của §21.5. |

## Trình tự kiểm tra

### SM-01 — Vào cổng School Manager và kiểm tra tenant context

**Tham chiếu:** §21.5, §31.3, FR-PL-01/02, AC-46/63.

1. Mở `/login`, chọn chế độ xem thử local.
2. Xác nhận cổng hiển thị vai trò Quản lý trường và điều hướng tới M02.
3. Kiểm tra mọi trang M02 giữ ngữ cảnh organization; không xuất hiện bộ chọn organization nếu không có luồng tương ứng.
4. Quan sát banner `Xem thử · Dữ liệu minh họa, không lưu`.

**Kỳ vọng:** route vào được ở preview và organization context là thông tin tĩnh. Fixture không chứng minh xác thực, permission resolver hay tenant isolation thực. Cross-organization authorization chỉ được xác nhận bằng API integration test của backend; không dùng tổ chức thật tại đây.

**Trạng thái:** Có thể rà FE local; xác thực/tenant isolation production cần backend/auth test.

### SM-02 — Dashboard organization

**Tham chiếu:** §21.5; phạm vi organization tại §31.3/FR-PL-02.

1. Mở `/m02-organization-management`.
2. Đọc các thẻ tổng quan giáo viên, lớp/sức chứa và quota.
3. Dùng từng quick link để mở Teacher, Lớp, Quota và Settings.
4. Quan sát cảnh báo billing/feedback unavailable nếu có.

**Kỳ vọng:** quick link dẫn đúng section; dashboard phải được hiểu là fixture, không phải báo cáo được server tính. SRS yêu cầu dashboard organization nhưng không định nghĩa chính xác KPI/biểu đồ; không dùng con số fixture làm tiêu chí nghiệp vụ.

**Trạng thái:** Có thể rà FE local; API dashboard summary chưa có.

### SM-03 — Xem capacity và quản lý vòng đời lớp

**Tham chiếu:** UC-06; §21.5; FR-T-02/03; FR-B-07; BR-04/32; AC-14.

1. Mở `?section=classes`, kiểm tra danh sách lớp và thông tin capacity đang hiển thị.
2. Xác định action tạo lớp. Với preview hiện tại, xác nhận action được ghi rõ unavailable/disabled; không gửi request tạo lớp.
3. Kiểm tra có thao tác archive/tạm ngưng và trạng thái read-only hay không; preview phải nêu unavailable nếu thiếu endpoint.
4. Ghi nhận các expected server behavior để test khi API sẵn sàng: capacity được đọc từ Billing; tạo đồng thời không vượt slot; hết slot trả `CLASS_CAPACITY_REACHED`; downgrade bắt buộc chọn lớp trước; lớp bị suspend giữ dữ liệu và chỉ đọc.

**Kỳ vọng đích:** capacity enforcement phải ở server/transaction, không thể kết luận chỉ từ việc nút có hiện hay không. API create class hiện chỉ nhận display name và không enforce capacity; chưa thấy endpoint archive/suspend. Không tạo lớp thật hoặc giả lập toast thành công.

**Trạng thái:** Có thể xem danh sách lớp; create-with-capacity, archive/suspend và downgrade projection bị chặn bởi API/backend.

### SM-04 — Provision Teacher, phân công, đổi Teacher và offboard

**Tham chiếu:** UC-06/12/13; §21.5; FR-T-02/14/17; BR-05/06/41; Q-13/Q-134.

1. Mở `?section=teachers`, kiểm tra danh sách/action và thông báo trạng thái.
2. Không gửi lời mời/email và không nhập danh tính thật.
3. Khi tích hợp thật, kiểm tra chuỗi: Manager tìm Teacher thuộc đúng organization → chọn Teacher → gán đúng một Teacher current cho lớp → chuyển Teacher/offboard → xác minh quyền Teacher cũ bị thu hồi trước khi cấp quyền mới.
4. Tạo fixture conflict active-run để backend test riêng: transfer thường phải conflict/reconcile; emergency force-close cần command tường minh, reason và audit metadata, không cho Manager xem media.
5. Provision Teacher phải tạo trạng thái chờ xác minh; chỉ kích hoạt sau email verification và server xác minh Firebase ID token.

**Kỳ vọng đích:** scope một organization; transfer pending giữ lớp read-only; active run conflict không tạo trạng thái nửa chừng; không cấp quyền dựa trên client role.

**Trạng thái:** Bị chặn cho luồng UI end-to-end. Có create/revoke assignment contract mức thấp nhưng chưa có Manager Teacher directory/selection và không đủ saga transfer; chưa có Manager provisioning/invitation API. Không suy ra Teacher từ ID tự nhập.

### SM-05 — Roster lớp và hồ sơ do tổ chức quản lý

**Tham chiếu:** UC-03; §21.5; FR-T-02/04/05; FR-PL-08; AC-63/64.

1. Ở `?section=classes`, chọn lớp và mở roster nếu local state cung cấp.
2. Chỉ rà tên hiển thị/trạng thái enrollment cần thiết; không tìm ảnh, video, story, transcript hoặc playback.
3. Khi API test được phê duyệt, dùng dữ liệu tổng hợp để xác nhận `GET .../classes/{class_id}/profiles` chỉ trả hồ sơ trong assignment/consent scope; tên hiển thị trùng nhau vẫn phân biệt bằng ID opaque.
4. Chuyển enrollment cần đóng enrollment cũ trước, không để một hồ sơ có hai lớp active.

**Kỳ vọng đích:** roster theo đúng organization/class và profile grants; School Manager không mặc định có quyền media. FE đã có đường đọc roster qua API profiles; trang hiện là read-only, hiển thị tên. Preview dùng fixture. Thêm/sửa/chuyển enrollment đầy đủ chưa được xác nhận là luồng Manager end-to-end.

**Trạng thái:** API đọc roster có sẵn nhưng chưa được gọi bằng session tích hợp trong lần rà này; fixture local có thể rà hình thức. Lifecycle mutation cần xác minh contract/backend trước khi test.

### SM-06 — Invoice, payment, subscription, renewal và grace period

**Tham chiếu:** UC-08; §21.5; FR-B-01–09; BR-28–33; AC-14/26.

1. Mở `?section=settings`.
2. Ghi lại invoice, trạng thái payment, kỳ subscription, renewal/downgrade actions nào đang được nêu unavailable.
3. Không nhập giá, khởi tạo checkout hoặc dùng provider.
4. Khi contract/backend sẵn sàng, kiểm lần lượt: invoice snapshot → payment pending → callback được xác minh và dedupe → trạng thái subscription/capacity đổi; browser redirect đơn thuần không chứng minh thanh toán.
5. Dùng fixture clock ở backend để xác minh nhắc trước hạn 7 ngày/1 ngày, failed payment/grace 7 ngày, phục hồi trong grace, hết grace chỉ chặn tạo lớp/run mới; vẫn đọc roster/lịch sử và quản lý payment.
6. Tắt auto-renew phải giữ quyền tới hết kỳ đã trả. Hạ capacity yêu cầu chọn lớp và chỉ áp dụng suspension tại effective time.

**Kỳ vọng đích:** không tự gia hạn sau khi tắt; invoice/payment audit được; không lộ provider secrets. Giá VND/package và một số policy còn mở trong SRS nên không điền giá hoặc suy diễn policy.

**Trạng thái:** Bị chặn bởi billing/invoice/payment/subscription API/backend chưa có trong surface đã kiểm tra. Settings hiện chỉ hiển thị unavailable. Không có giao dịch giả.

### SM-07 — Quota video của organization và top-up

**Tham chiếu:** UC-10/16; §21.5; FR-B-10–13; BR-11/38; AC-17/23/24.

1. Mở `?section=quota`, kiểm tra phân biệt organization quota với quota Parent; Teacher generation phải trừ organization của occurrence, không có Teacher-account pool.
2. Kiểm tra unavailable state và không bấm action mua/top-up nếu UI báo chưa khả dụng.
3. Khi API được triển khai, xác nhận summary lấy từ grant/usage ledger, kỳ included, expiry và top-up FIFO; số dư không phải trường mutable.
4. Kiểm callback payment pending/failed/duplicate không tạo grant; chỉ payment event đã verify mới cấp top-up. Hết quota chặn generation mới nhưng playback/history cũ vẫn truy cập được.

**Kỳ vọng đích:** included kỳ hiện tại dùng trước top-up FIFO; accepted generation tiêu thụ một unit theo policy SRS kể cả lỗi sau admission; không hoàn quota. Số included unit/giá và chi tiết gói còn mở, không tự ghi ra giá/chính sách.

**Trạng thái:** Bị chặn bởi organization quota-summary/top-up/payment APIs. Số quota đang thấy trong dashboard/quota là fixture.

### SM-08 — Inbox và thông báo billing

**Tham chiếu:** §21.5; UC-08/15; FR-B-08/09/14; NFR-26; AC-26.

1. Quan sát header ở M01/M02.
2. Xác nhận `Hộp thư chưa khả dụng` là status tĩnh, không phải nút; không có unread dot.
3. Không dùng browser push hoặc cấp notification permission cho preview.
4. Khi API có, kiểm inbox nhận notice billing trước push/email; kiểm dedupe/retry và payload chỉ có loại thông báo + opaque route/ref, không có tên trẻ/media/playback URL.

**Kỳ vọng đích:** inbox là nguồn chuẩn; push/email best-effort; provider failure không xóa notice. UC-15 đăng ký/revoke push chủ yếu cho Parent/Teacher; không mở rộng thành flow opt-in của School Manager khi SRS không yêu cầu.

**Trạng thái:** Bị chặn do không có inbox API/route; FE hiển thị unavailable.

### SM-09 — Duyệt Teacher lesson trước khi PUBLIC

**Tham chiếu:** `/m01-publication-review`; §21.5 role scope; §31.2; FR-PL-05; BR-51; AC-48/60.

1. Mở `/m01-publication-review`; xác nhận danh sách chờ chỉ có Teacher lesson/access-grant trong organization được phép.
2. Xem metadata/text cần cho quyết định; không mở media/story của trẻ.
3. Ở preview local, nhập reason và chọn `Yêu cầu chỉnh sửa`; xác nhận `Đã duyệt` không tăng và bộ đếm yêu cầu chỉnh sửa tăng riêng. Nhãn phải nói đây là state local, không được gửi API.
4. Có thể reload preview để thấy fixture không lưu. Không xem kết quả đó là decision backend.
5. Khi API integration test được phê duyệt, kiểm queue access-grant thật, approve/change-request command, revision/version, trạng thái pending và lỗi; chỉ approve mới mở cổng PUBLIC. SCHOOL visibility vẫn chỉ trong tenant.

**Kỳ vọng đích:** public bị chặn cho tới Manager approval; unpublish/hide giữ lịch sử nhưng revoke quyền truy cập thư viện. M01 hiện có access-grant list/decision API; lần rà hiện tại chỉ test fixture local, không gửi quyết định thật.

**Trạng thái:** Có API đọc/duyệt trong source và FE có API mode; preview interaction có thể test local, không persistent.

### SM-10 — Xem và trả lời feedback trong phạm vi trường

**Tham chiếu:** §31.6; FR-PL-22; Q180–Q182; AC-58/63.

1. Kiểm tra M02 có route/tab feedback reply hay không.
2. Hiện chưa có route; không dùng inbox unavailable thay cho feedback.
3. Khi API/UI được triển khai, test thread gắn lesson version/delivery; chỉ member có quyền của organization liên quan xem/trả lời; reply không mở direct chat.
4. Xác nhận không có completion toggle, checklist hoặc upload ảnh/media trẻ trong feedback.

**Kỳ vọng đích:** reply của Manager vẫn chỉ hiển thị trong school scope; tổ chức khác không thấy thread.

**Trạng thái:** Bị chặn do thiếu School Manager feedback list/reply API và UI route.

### SM-11 — Quyền riêng tư và tenant boundary (checkpoint xuyên suốt)

**Tham chiếu:** §31.3/31.6; FR-PL-01/02/08/22; NFR-36; AC-46/57/63/64.

1. Trong từng flow, rà organization/class context và role trước khi xem resource.
2. Xác nhận không có link/preview vào ảnh tranh, video, story, transcript hoặc playback của trẻ cho School Manager.
3. Khi backend có test fixtures, thử scope mismatch và confirm response không tiết lộ resource tồn tại ở organization khác; kiểm revoke chặn read/token/job mới.

**Kỳ vọng:** deny-by-default với child media; permission nội dung không cấp quyền media. FE preview không đủ để chứng minh server authorization.

**Trạng thái:** FE có thể rà sự vắng mặt của media; quyền server và cross-tenant isolation cần backend security/contract tests.

### SM-12 — Logout và bảo vệ route sau logout

**Tham chiếu:** phát hiện trực tiếp của user; không coi là screen requirement riêng trong §21.5. Handler hiện tại được tái sử dụng.

1. Từ M02 dashboard hoặc settings, Tab/focus tới `Đăng xuất` và nhấn Enter.
2. Xác nhận về `/login`, xóa `s2l-web-role` và `s2l-web-authenticated`.
3. Nhập trực tiếp route M02 đã bảo vệ sau logout; xác nhận vẫn ở `/login`.
4. Ở 390px, xác nhận nút icon sidebar có accessible name và vùng bấm tối thiểu 44×44px.

**Kỳ vọng/hiện trạng:** đã rà đạt trên dashboard/settings ở 1440×900 và 390×844. Ảnh + route/session observation tại EV-005.

## Dependency/API chưa có — không thể hoàn tất end-to-end trong FE-only

- Billing price/period/invoice/payment/recurring subscription/callback, grace, downgrade và capacity projection (UC-06/08; FR-B-01–09).
- Enforcement capacity tại transaction, class archive/suspend, Teacher directory/provision/assignment transfer saga (UC-06/12/13; FR-T-02/03/14/17).
- Organization quota summary/top-up/payment grant (UC-10/16; FR-B-10–13).
- Notification inbox and delivery records (FR-B-08/09/14; UC-15).
- School Manager feedback list/reply (FR-PL-22; AC-58).

Các phần này phải giữ unavailable tới khi API/contract và UI states tương ứng có thật. Không dùng fixture/toast như bằng chứng backend đã chạy.

## Evidence liên quan

- Route screenshot sau remediation: `../screenshots/remediation-after/`.
- Logout desktop/narrow, dashboard/settings: `../screenshots/logout-check/` và `SCHOOL_MANAGER_WEB_LOGOUT_QA_REV57_20261110.md`.
- API inventory chi tiết: `SCHOOL_MANAGER_WEB_REMEDIATION_REV57_20261110.md`.
- Plan/acceptance: `../../plan/PLAN.md` AC14; approval: `../../approvals/TASK_APPROVAL.md`.
