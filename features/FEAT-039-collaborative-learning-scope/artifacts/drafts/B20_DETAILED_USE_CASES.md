## B20. Use case chi tiết và tiêu chí nghiệm thu theo luồng

### B20.1 Thẩm quyền, quy ước và điều kiện chung

Các bước, tên lệnh/trạng thái và tiêu chí kiểm thử chi tiết trong B20 là **PROPOSED**: tầng refinement để review và làm nền tảng cho feature plan, không chứng nhận runtime đã triển khai. Nhãn của FR gốc không đổi. Các quyết định **OWNER_CONFIRMED** được nhắc rõ tại use case liên quan: pilot một trường và chuẩn bị mở rộng; hồ sơ trẻ do giáo viên quản lý, vào phiên bằng QR/mã, không tài khoản riêng; nhà trường thu consent, Teacher/Admin được cấp quyền ghi nhận bằng chứng/phạm vi; duyệt từng Sketch; chọn trẻ đang vẽ theo lượt trên tablet chung; Teacher quyết định retry/skip/end khi video thất bại hết retries. Owner xác nhận thêm tuổi **36–155 completed months inclusive**, pilot **một lớp với tối đa 40 trẻ**, lưu **session/artwork 90 ngày sau khi phiên kết thúc**; portfolio/profile/audit có lifecycle riêng chưa chốt. Capacity là mục tiêu pilot, không chứng minh tải đã đạt. Mixed-age/curriculum mapping, công cụ, quay lại stage, offline authoring, retention exceptions/shared copies/backups, rubric và giới hạn AI vẫn cần decision gate B17.

Điều kiện chung `UC-COMMON` áp dụng cho mọi luồng:

1. Actor phải có quyền hiện hành theo tổ chức, lớp, phiên, nhóm, resource và action; kiểm tra tại lúc đọc/lệnh được chấp nhận, không chỉ lúc mở màn hình. Thiết kế có organization scope để chuẩn bị mở rộng, nhưng pilot chỉ vận hành một trường theo quyết định owner.
2. Dữ liệu trẻ và tác vụ AI phải đáp ứng purpose/consent policy hiện hành. QR/mã chỉ dẫn vào admission, không thay consent hoặc quyền lớp. Thiết bị được cấp quyền và contributor do UI lựa chọn là hai khái niệm riêng.
3. Lệnh ghi cần expected version và khóa idempotency/operation ID theo contract tương ứng. Cùng khóa và cùng nội dung trả lại kết quả đã ghi; cùng khóa khác nội dung bị từ chối. State, review và đóng góp không nhân đôi khi retry.
4. Đổi quyền, consent, content policy hoặc aggregate version khi tác vụ đang chạy yêu cầu kiểm tra lại trước commit/phát kết quả. Từ chối có mã an toàn, hành động sửa phù hợp và audit; không lộ token, provider endpoint hay raw dữ liệu ngoài scope.
5. Postcondition bền vững chỉ tính khi backend xác nhận đã ghi qua persistence port. Local draft, job đang chờ, thumbnail và presence không đủ để báo “đã lưu” hoặc “hoàn tất”. Original/accepted snapshot giữ bất biến; correction/derivative có version và provenance riêng.
6. Tiêu chí `AT-UC-xxx-P/N` là Given/When/Then đề xuất, dùng fixture tổng hợp. Ngoài age endpoint, pilot capacity và session/artwork retention đã được owner xác nhận ở trên, B20 không tự đặt số latency, timeout, payload hay chất lượng model; áp dụng profile/contract được duyệt ở phần tương ứng. Tối đa 40 tính theo unique admitted children, không theo số tablet/connections.

### B20.2 Danh mục use case

| Use case | Nội dung | Actor chính | FR được làm rõ |
|---|---|---|---|
| UC-001 | Đăng nhập người lớn và phân quyền theo scope | Teacher / Super Admin | FR001, FR005 |
| UC-002 | Quản lý lớp, hồ sơ trẻ và enrollment | Teacher | FR004 |
| UC-003 | Ghi nhận, kiểm tra và thu hồi consent | Teacher / Admin được cấp quyền | FR006 |
| UC-004 | Chuẩn bị cấu hình, mở Lobby và explicit Start | Teacher | FR007, làm rõ Teacher control FR010 |
| UC-005 | Tạo và chỉnh nhóm thủ công | Teacher | FR008 |
| UC-006 | Đề xuất chia nhóm tự động Phase 2 | Teacher | FR065 |
| UC-007 | Join và Teacher admission | Child / Teacher | FR002 |
| UC-008 | Tablet chung và chọn contributor theo lượt | Child / Teacher | FR003, FR066 |
| UC-009 | Tiến độ độc lập của nhóm | Child / Teacher | FR009 |
| UC-010 | Pause, resume, advance và kết thúc sớm | Teacher | FR010, FR013 |
| UC-011 | Đóng phiên và lưu kết quả | Teacher | FR011 |
| UC-012 | Di chuyển hoặc cho trẻ rời nhóm | Teacher | FR012 |
| UC-013 | Mở canvas và vẽ theo công cụ được phép | Child | FR014, FR015, FR020 |
| UC-014 | Xin hỗ trợ, bảo vệ và khôi phục vùng vẽ | Child / Teacher | FR016 |
| UC-015 | Scoped undo và xem lại quá trình | Child / Teacher | FR018, FR021 |
| UC-016 | Mất kết nối, resync và recovery | Child / Teacher | FR017, FR060, FR063 |
| UC-017 | Tách AI overlay khỏi nét trẻ | Child / Teacher | FR019, FR028 |
| UC-018 | Vision và xác nhận/correction ý nghĩa | Child / Teacher | FR022, FR023 |
| UC-019 | Yêu cầu và chuẩn bị Sketch proposal | Child / Teacher | FR024, FR025, FR030 |
| UC-020 | Moderation và Teacher duyệt từng Sketch | Teacher | FR026, FR029, FR061 |
| UC-021 | Child xem, ẩn hoặc từ chối Sketch | Child | FR027 |
| UC-022 | Gallery, trình bày và chia sẻ đúng scope | Teacher / Child | FR031, FR032, FR033 |
| UC-023 | Chuẩn bị knowledge/script và chọn/tạo video | Teacher | FR034, FR035, FR040 |
| UC-024 | Review đúng version video trước chiếu | Teacher | FR036 |
| UC-025 | Theo dõi video đang tạo và chờ | Teacher / Child | FR037, FR038 |
| UC-026 | Quyết định sau video thất bại | Teacher | FR039 |
| UC-027 | Chọn/chỉnh hoạt động và xác nhận an toàn | Teacher | FR041, FR042, FR043 |
| UC-028 | Ghi nhận off-screen và reflection | Child / Teacher | FR044 |
| UC-029 | Quan sát và assessment theo tuổi | Teacher | FR045, FR049, FR050 |
| UC-030 | Lưu lịch sử và portfolio | Teacher | FR047 |
| UC-031 | Báo cáo tiến bộ và export theo quyền | Teacher | FR046, FR048 |
| UC-032 | Dashboard lớp và hàng đợi hỗ trợ | Teacher | FR051, FR054 |
| UC-033 | Preset, automation và Teacher override | Teacher | FR052, FR053 |
| UC-034 | Cấp quyền, đình chỉ và vận hành tài khoản | Super Admin | FR055, FR058 |
| UC-035 | Author/review/publish/recall nội dung | Teacher / Super Admin | FR056, FR062 |
| UC-036 | Version và thay đổi AI policy | Super Admin | Làm rõ phần AI policy của FR056 |
| UC-037 | Monitoring, audit và xử lý incident | Super Admin được cấp quyền | FR057 |
| UC-038 | Retention, yêu cầu xuất/xóa và kiểm chứng purge | Actor có thẩm quyền / Admin | FR059, FR064 |

FR056 được triển khai thành hai luồng nghiệp vụ UC-035/036; bảng traceability cuối có một dòng duy nhất cho FR056 và chỉ ra cả hai. Mọi use case dưới đây thừa hưởng `UC-COMMON` và không mở quyền chỉ bằng actor role.

### UC-001 — Đăng nhập người lớn và phân quyền theo scope

- **Actor / FR:** Teacher, Super Admin; FR001, FR005. Firebase dùng Authentication-only theo `REPO_CONSTRAINT`; provisioning và token/capability contract là `PROPOSED`.
- **Preconditions:** adult account được provision hoặc có quy trình chờ provision; assignment/policy có version. Không dùng Child profile làm adult credential.
- **Trigger/input:** người lớn đăng nhập; backend nhận bằng chứng identity và context resource được yêu cầu.
- **Main flow:** (1) Backend xác minh identity qua auth port. (2) Resolve account/status/assignment hiện hành, không tin role do client gửi. (3) Trả authorized context và các action của từng lớp. (4) Mỗi query/command/subscription tiếp tục kiểm tra scope/action. (5) Ghi decision bảo mật có correlation, không ghi token.
- **Alternatives/errors:** identity không hợp lệ/hết hạn yêu cầu reauthenticate; chưa provision không tự trở thành Teacher; suspended/revoked assignment chặn truy cập mới và subscription. Yêu cầu resource khác lớp bị từ chối dù user vẫn đăng nhập.
- **Persistent postconditions:** account mapping và decision audit hợp lệ; không có child account được tạo. Chỉ grant được policy cho phép mới có hiệu lực; không thay đổi assignment bởi đăng nhập.
- **AT-UC-001-P:** Given Teacher hoạt động và được giao lớp A, When đăng nhập rồi đọc lớp A, Then trả projection theo quyền và ghi actor identity đã xác minh.
- **AT-UC-001-N:** Given Teacher chỉ được giao A, When client giả role Admin hoặc đọc canvas lớp B, Then backend từ chối, không trả thumbnail/raw media và audit không chứa token.

### UC-002 — Quản lý lớp, hồ sơ trẻ và enrollment

- **Actor / FR:** Teacher trong scope được cấp; FR004. **OWNER_CONFIRMED:** Teacher quản lý hồ sơ, trẻ không có tài khoản đăng nhập riêng.
- **Preconditions:** class/teacher assignment hợp lệ; age policy được version theo tuổi owner đã chốt 36–155 completed months inclusive; cách tính tuổi tại ngày phiên và trường tối thiểu phải được contract duyệt. Consent được quản lý riêng ở UC-003.
- **Trigger/input:** tạo/chỉnh lớp, tạo/chỉnh hồ sơ bằng alias và tuổi do người lớn xác nhận, thêm/ngừng enrollment; ID/version hiện hành.
- **Main flow:** (1) Kiểm tra quyền class và danh mục trường tối thiểu. (2) Tạo hoặc chọn profile qua ID, không lấy alias làm identity. (3) Ghi adult-confirmed age/context với policy reference. (4) Ghi enrollment và thời điểm có hiệu lực. (5) Hiển thị trạng thái hồ sơ/enrollment/consent độc lập để Teacher chuẩn bị phiên.
- **Alternatives/errors:** cùng retry không tạo profile/enrollment trùng; cùng alias không tự merge hai trẻ. Không biết tuổi hoặc ngoài 36–155 completed months chặn session eligibility theo policy, không suy tuổi từ ảnh; tạo/sửa hồ sơ lịch sử không tự là admission. Ngừng enrollment không tự xóa portfolio hay đứt history.
- **Persistent postconditions:** class, profile version và enrollment history có actor/provenance; không sinh credential trẻ hoặc consent tự động. Profile correction giữ dấu vết giá trị trước.
- **AT-UC-002-P:** Given Teacher lớp A, When tạo profile rồi enroll vào A và sửa alias, Then identity/profile history giữ nguyên và không có child login account.
- **AT-UC-002-N:** Given hai profile cùng alias/request retry hoặc profile có tuổi 35/156 completed months tại ngày phiên, When Teacher enroll/xác nhận session eligibility, Then không merge nhầm/nhân đôi enrollment, tuổi ngoài biên không được admit và enrollment không tự tạo consent.

### UC-003 — Ghi nhận và thu hồi consent theo purpose

- **Actor / FR:** Teacher/Admin có authority ghi consent; FR006. **OWNER_CONFIRMED:** nhà trường thu consent của người đại diện hợp pháp; actor được cấp quyền ghi bằng chứng và phạm vi, không thay guardian chỉ vì có role.
- **Preconditions:** có subject profile và privacy policy version; quy trình kiểm tra thẩm quyền/guardian evidence được duyệt trước thu dữ liệu thực. Không đưa bằng chứng consent thật vào repo.
- **Trigger/input:** grant/correction/revoke consent; subject, representative/evidence reference, purposes, policy version và thời điểm hiệu lực theo contract.
- **Main flow:** (1) Xác minh actor có authority và evidence theo quy trình trường. (2) Ghi consent record version cùng purposes cụ thể. (3) Evaluate quyền thu thập, lưu, dùng AI và chia sẻ của các lệnh tiếp theo. (4) Khi revoke/thu hẹp, invalidate grants/tác vụ bị ảnh hưởng theo policy. (5) Hiển thị Teacher hành động được phép và việc đang chờ xử lý.
- **Alternatives/errors:** thiếu evidence/scope không tự chuyển thành grant; enrollment hoặc Teacher tick chung không đủ. Completion AI chạy trước revoke phải được kiểm tra lại, không phát nếu purpose hiện hành không cho phép. Revoke không báo mọi bản sao đã xóa; xóa theo UC-038.
- **Persistent postconditions:** consent history và audit có người ghi, bằng chứng reference/policy/purposes; derived decision có version. Không sửa original record hoặc đồng nhất consent với school enrollment.
- **AT-UC-003-P:** Given evidence đã kiểm tra chỉ cho phép lưu tranh, When Teacher ghi consent, Then lưu record và cho phép đúng purpose đã cấp.
- **AT-UC-003-N:** Given AI purpose chưa có hoặc đã revoke trong khi job chạy, When yêu cầu/nhận kết quả AI, Then không gửi/phát kết quả trái scope; lưu typed decision và Teacher thấy cách giải quyết.

### UC-004 — Chuẩn bị, mở Lobby và bắt đầu phiên

- **Actor / FR:** Teacher; FR007 và Teacher control FR010. Topic/age/tools/group/preset là `CONFIRMED`; field/validation/Start guards chi tiết `PROPOSED` trong phạm vi pilot owner đã chốt.
- **Preconditions:** lớp hoạt động, assignment đúng; thư viện/preset và age policy có version dùng được. Pilot một lớp, tối đa 40 unique admitted children; readiness/consent guards phải hợp lệ khi Start. Chưa phát QR hoặc mở drawing nếu cấu hình chưa hợp lệ.
- **Trigger/input:** tạo Draft từ mới/preset, OpenLobby hoặc explicit StartSession; topic, age context, canvas/tool/AI policy, nhóm, content references và expected session/configuration version.
- **Main flow:** (1) Teacher chọn lớp/topic/preset version. (2) Hệ thống hiển thị effective config và các thiếu sót. (3) Teacher chỉnh tools/canvas/groups và review riêng các approval policy. (4) Validate compatibility/consent/age/content policy. (5) Lưu Draft có config version; Teacher explicit mở Lobby khi sẵn sàng; admission thực hiện UC-007. (6) Sau admission, controlling Teacher explicit StartSession bằng current version; backend recheck config/roster/tuổi 36–155/consent/capacity tối đa 40, pilot một lớp hoạt động và current scope. (7) Commit Lobby→Active, effective stage/control epoch rồi phát authorized drawing/resync policy; không start chỉ vì Child đã join.
- **Alternatives/errors:** preset stale/recalled phải chọn lại hoặc tạo phiên bản hợp lệ; thiếu required policy/config làm Draft chưa mở được theo validation đã duyệt. Roster vượt 40, tuổi ngoài biên, thiếu consent hoặc Start stale bị từ chối; giữ Lobby/validation errors, không half-start. Retry cùng lệnh không tạo hai phiên/start events. Sửa cấu hình sau Lobby cần UC-033/state contract, không âm thầm thay expected config của trẻ.
- **Persistent postconditions:** session Draft/Lobby hoặc Active sau explicit Start, effective configuration/control epoch/preset source và Teacher decision được ghi; không tự admit participants/approve Sketch/video. Admission/start là records riêng và capacity target không bị mô tả là benchmark pass.
- **AT-UC-004-P:** Given preset/config hợp lệ và roster tối đa 40 trẻ đủ tuổi/consent trong pilot một lớp, When Teacher chỉnh tool, lưu/mở Lobby, admit roster qua UC-007 rồi explicit Start bằng current version, Then config/override/start lưu bền vững, phiên Active và retry không tạo start event thứ hai.
- **AT-UC-004-N:** Given preset muốn bypass review/recalled content hoặc roster vượt 40/Start version stale, When mở/bắt đầu phiên pilot, Then không bypass per-item review/content gate, Start không hợp lệ giữ Lobby và Child join không tự kích hoạt phiên.

### UC-005 — Tạo và chỉnh nhóm thủ công

- **Actor / FR:** Teacher; FR008.
- **Preconditions:** session thuộc lớp được giao; membership/session version còn hiện hành; quy tắc số nhóm/canvas/age mix đã được policy định nghĩa trước thực thi.
- **Trigger/input:** thêm/đổi tên nhóm, phân participants, chọn personal/shared/region canvas mode, expected group/session version.
- **Main flow:** (1) Teacher xem roster đủ điều kiện và các nhóm. (2) Tạo nhóm hoặc phân membership. (3) Backend kiểm tra participant cùng session và ràng buộc membership hiệu lực. (4) Ghi group/canvas scope và membership history theo transaction/contract được duyệt. (5) Cập nhật dashboard/device projections đúng scope.
- **Alternatives/errors:** cùng participant được phân trái ràng buộc hiện hành bị từ chối, không “last write wins” âm thầm. Roster stale yêu cầu reload. Chuyển nhóm khi đang vẽ đi UC-012, giữ lịch sử; xóa nhóm có artwork không tự xóa sản phẩm.
- **Persistent postconditions:** group/version, membership effective intervals và canvas references; chỉ quyền hiện hành thay đổi, history trước được giữ.
- **AT-UC-005-P:** Given roster cùng phiên, When Teacher chia thành nhóm A/B, Then mỗi participant có membership và canvas quyền tương ứng, nhóm có progress độc lập.
- **AT-UC-005-N:** Given participant thuộc phiên khác hoặc roster đã đổi, When gửi phân nhóm, Then từ chối toàn bộ thay đổi không hợp lệ, không cấp canvas quyền ngoài phiên.

### UC-006 — Đề xuất chia nhóm tự động Phase 2

- **Actor / FR:** Teacher; FR065. Khả năng thuộc `CONFIRMED` Phase 2; thuật toán, input/constraints và preview/commit là `PROPOSED/TBD` OD18.
- **Preconditions:** Phase 2 capability được mở; criteria policy đã được duyệt; roster eligible có version. Không dùng AI suy psychology/intelligence hoặc thu thông tin mới để chia nhóm.
- **Trigger/input:** Teacher chọn criteria được cho phép và yêu cầu grouping proposal cho roster hiện hành.
- **Main flow:** (1) Chụp roster/criteria version. (2) Tạo proposal kèm lý do theo tiêu chí được phép và cảnh báo constraint chưa đạt. (3) Teacher preview, đổi từng membership hoặc hủy. (4) Teacher explicit commit kết quả cuối. (5) Backend revalidate roster và ghi membership history như UC-005/012.
- **Alternatives/errors:** roster đổi trong lúc tạo thì proposal stale, không tự áp; không tìm được grouping hợp lệ thì báo constraint và cho manual grouping. Thuật toán không tự di chuyển trẻ đang vẽ hoặc điều khiển stage.
- **Persistent postconditions:** proposal/source criteria và Teacher final decision có audit; chỉ commit hợp lệ mới tạo membership phiên bản mới.
- **AT-UC-006-P:** Given roster/criteria hợp lệ, When Teacher sửa proposal rồi commit, Then nhóm đúng bản Teacher chốt, proposal và override được lưu.
- **AT-UC-006-N:** Given participant đã rời roster sau proposal, When commit cũ, Then chặn stale result, membership đang chạy và canvas cũ không bị đổi.

### UC-007 — Join bằng QR/mã và Teacher admission

- **Actor / FR:** Child tham gia với Teacher xác nhận; FR002. **OWNER_CONFIRMED:** hồ sơ + QR/mã phiên, không child login riêng.
- **Preconditions:** Lobby mở hoặc late-join policy đã được duyệt; managed profile/enrollment/consent đủ cho purpose hiện hành, tuổi 36–155 completed months tại ngày phiên và còn quota admission tối đa 40 trẻ; device chưa bị revoke.
- **Trigger/input:** quét QR/nhập mã, chọn profile qua flow được phép và yêu cầu join; join reference và device binding, không gửi quyền tự khai.
- **Main flow:** (1) Resolve join reference, chỉ trả context tối thiểu. (2) Teacher kiểm tra/chọn đúng profile, session/group. (3) Backend validate eligibility và admission. (4) Ghi participant/device binding, cấp scoped grant theo contract. (5) Trả authorized lobby/canvas config; reconnect dùng participant đã admit.
- **Alternatives/errors:** mã sai/hết hạn/đóng admission cho thông báo an toàn, không lộ roster cả lớp. Duplicate join trả binding hiện có hoặc yêu cầu Teacher xử lý rebind theo policy. Late join chưa có policy không tự admit. Grant bị revoke không thể dùng QR cũ để lấy quyền lại.
- **Persistent postconditions:** admitted participant gắn profile/session và grant/device scope; không tạo Firebase child account. Từ chối admission không tạo participant đầy quyền.
- **AT-UC-007-P:** Given Lobby và profile đủ điều kiện, When Teacher xác nhận join, Then trẻ nhận đúng canvas/group và retry không nhân đôi participant.
- **AT-UC-007-N:** Given chỉ biết mã phiên hoặc consent thiếu, When gọi canvas API trực tiếp, Then không đọc/sửa được artwork và admission không bỏ qua Teacher/consent gate.

### UC-008 — Tablet chung và contributor theo lượt

- **Actor / FR:** Child/Teacher; FR003, FR066. **OWNER_CONFIRMED:** chọn trẻ đang vẽ theo lượt; không đổi tác giả nét cũ. Chi tiết switching/correction là `PROPOSED`.
- **Preconditions:** device có grant cho danh sách participant đã admit; canvas/policy hợp lệ. Attribution là lựa chọn có khai báo, không chứng minh ai đang cầm bút.
- **Trigger/input:** chọn active child và mở/chuyển lượt; participant/turn context và expected binding version.
- **Main flow:** (1) Hiển thị các participant device được phép chọn. (2) Kết thúc input đang diễn ra trước switch theo policy được duyệt. (3) Ghi active-child/turn context mới. (4) Mỗi nét mới ghi verified device principal riêng với selected contributor/turn. (5) Teacher có thể xem history attribution và thực hiện correction có log nếu quy trình được duyệt.
- **Alternatives/errors:** chưa chọn active child thì không tự đoán contributor; chặn input hoặc lưu unknown/group attribution chỉ theo policy được duyệt. Chọn trẻ khác nhóm/scope bị từ chối. Buffered nét từ lượt trước giữ context lúc tạo và revalidate quyền lúc nhận; không đổi sang người mới.
- **Persistent postconditions:** turn/binding history và operation contributor không bị rewrite khi switch; attribution correction là record mới, giữ original attribution.
- **AT-UC-008-P:** Given A rồi B dùng cùng tablet, When switch lượt sau nét A đã nhận, Then nét mới gắn B, nét A giữ A và cả hai có verified device principal.
- **AT-UC-008-N:** Given client sửa contributor thành trẻ chưa được bind, When gửi nét, Then backend từ chối; không suy identity từ pointer/touch hoặc gán lại nét đã nhận.

### UC-009 — Theo dõi tiến độ nhóm độc lập

- **Actor / FR:** Child theo action được cho phép, Teacher điều phối; FR009.
- **Preconditions:** session Active, group membership hiện hành; group progress contract phân biệt shared stage và local state.
- **Trigger/input:** group báo hoàn thành/need help/ready; Teacher xem hoặc sửa progress; group expected version.
- **Main flow:** (1) Ghi progress group từ action được phép. (2) Dashboard cập nhật trạng thái/last accepted change. (3) Nhóm sẵn sàng có thể chờ/chia sẻ theo Teacher policy, nhóm khác vẫn tiếp tục. (4) Teacher quyết định mốc lớp qua UC-010. (5) History ghi readiness và stage quyết định riêng.
- **Alternatives/errors:** Child không thể gọi class advance qua progress update; stale group event không kéo trạng thái về cũ. Mất presence không tự đánh dấu hoàn tất/không hợp tác; Teacher thấy disconnected riêng với progress.
- **Persistent postconditions:** progress từng group và Teacher intervention history; class stage không thay đổi nếu không có command có thẩm quyền.
- **AT-UC-009-P:** Given A ready, B đang vẽ, When ghi readiness A, Then B tiếp tục được phép và shared stage giữ nguyên cho tới Teacher command.
- **AT-UC-009-N:** Given Child chỉ có group grant, When gửi stage advance hoặc event stale, Then class không chuyển, progress mới không bị ghi đè.

### UC-010 — Pause, resume, advance và kết thúc sớm

- **Actor / FR:** Teacher; FR010, FR013. Quyền control là `CONFIRMED`; quay lại stage cũ FR013 vẫn `TBD` OD07.
- **Preconditions:** Teacher assignment hiện hành; expected session version; stage guards/review/save policy đã được duyệt.
- **Trigger/input:** pause/resume/advance/save draft/end early; target stage, reason/confirmation khi policy yêu cầu.
- **Main flow:** (1) Validate command và current lifecycle. (2) Persist control event/policy version và yêu cầu checkpoint phù hợp. (3) Broadcast effective action tới groups/devices. (4) Resume giữ products/progress; advance ghi Teacher disposition đối với nhóm chưa xong. (5) End early lưu phần đã có/incomplete stages, không báo full journey hoàn tất.
- **Alternatives/errors:** network retry không tạo hai stage events; concurrent control stale phải reload. Advance Knowledge không tự play video chưa duyệt. Pause editing behavior theo state policy, không mặc định mất nét. ReturnToEarlierStage chỉ được bật sau OD07; UI back không là domain stage command.
- **Persistent postconditions:** lifecycle/stage/teacher reason/version bền vững; accepted artwork giữ. EndedEarly khác Completed, thiếu video/activity không bị ghi thành thành công.
- **AT-UC-010-P:** Given hai nhóm tiến độ khác nhau, When Teacher pause/resume rồi end early, Then products được checkpoint/giữ, quyết định có actor và phiên ghi EndedEarly.
- **AT-UC-010-N:** Given quay lại stage chưa có policy hoặc video chưa approved, When UI gửi back/advance-play, Then không tạo transition trái policy hoặc autoplay.

### UC-011 — Đóng phiên và lưu kết quả bền vững

- **Actor / FR:** Teacher; FR011.
- **Preconditions:** có accepted canvas/process/observations/reflections phù hợp; Teacher có quyền complete; save/retention policy hiện hành.
- **Trigger/input:** CompleteSession hoặc lưu draft cuối phiên, expected version và disposition các bước chưa hoàn tất.
- **Main flow:** (1) Chốt operation watermarks và products thuộc snapshot hợp lệ. (2) Ghi Completing cùng outcome từng giai đoạn. (3) Lưu session products/process/comments, tạo/đối chiếu portfolio entries theo UC-030. (4) Hiển thị lỗi và tài nguyên chưa lưu nếu bước persistence thất bại. (5) Chỉ xác nhận Completed khi bộ lưu yêu cầu đã bền vững theo contract.
- **Alternatives/errors:** một phần lưu lỗi giữ Completing/recoverable state, không báo Completed; retry dùng cùng command và entry identity để tránh duplicate. Late canvas events sau cutoff xử lý theo contract, không lặng lẽ bỏ contribution được acknowledge.
- **Persistent postconditions:** session outcome, snapshot refs/watermarks, process/comments và portfolio references; completion evidence có save status thật. End timestamp làm anchor lưu session/artwork 90 ngày theo owner policy; portfolio/profile/audit và copy exceptions có lifecycle riêng. Originals không bị thay bằng thumbnail/AI summary.
- **AT-UC-011-P:** Given bộ evidence hợp lệ, When Teacher complete và persistence xác nhận, Then session Completed, entry không trùng khi retry, watermark khớp các nét đã acknowledge.
- **AT-UC-011-N:** Given storage lỗi lúc lưu portfolio, When complete, Then UI báo phần chưa lưu và recovery action; không có tuyên bố Completed giả hoặc silent loss.

### UC-012 — Chuyển nhóm hoặc cho trẻ rời phiên

- **Actor / FR:** Teacher; FR012.
- **Preconditions:** participant/session/group versions hiện hành; Teacher có scope cả nguồn và đích trong cùng phiên; relocation policy được duyệt.
- **Trigger/input:** MoveParticipant/RemoveParticipant; participant, target group hoặc leave disposition và expected membership version.
- **Main flow:** (1) Kiểm tra source/target và xử lý input đang gửi theo cutoff. (2) Ghi kết thúc membership cũ và membership mới hoặc removed state. (3) Revoke scope canvas cũ, issue/rebind grant đúng group khi cần. (4) Cập nhật device/Teacher projections. (5) Giữ artwork/contribution của participant dưới group lịch sử; không tự chép sang canvas đích.
- **Alternatives/errors:** client không có quyền tự chuyển; queued nét gửi sau revoke bị reject/recoverable draft. Mất mạng trong lúc chuyển phải resync binding; retry không tạo nhiều memberships. Group đích thuộc phiên khác bị từ chối.
- **Persistent postconditions:** membership/grant history và contributions đã nhận còn đầy đủ; quyền mới không sửa attribution của operations trước.
- **AT-UC-012-P:** Given A có nét ở group X, When Teacher chuyển sang Y, Then A có quyền Y, mất quyền ghi X và nét cũ vẫn nằm ở X với A attribution.
- **AT-UC-012-N:** Given grant cũ bị thu hồi, When device replay nét mới vào X, Then backend không nhận nét trái quyền và không xóa các nét lịch sử đã acknowledge.

### UC-013 — Mở canvas và vẽ bằng công cụ được phép

- **Actor / FR:** Child; FR014, FR015, FR020. Import ảnh/sticker/text/mẫu vẫn `TBD` OD09, không là input core của use case này.
- **Preconditions:** admitted participant/device binding, effective age/tool/canvas policy và current region permissions; lifecycle cho phép vẽ theo B19.
- **Trigger/input:** mở personal/shared/region canvas, chọn công cụ được cho phép và gửi stroke operation cùng source context/version.
- **Main flow:** (1) Fetch checkpoint và policy đúng scope. (2) Render canvas với công cụ Teacher đã bật theo UX tuổi. (3) Child tạo local stroke; UI hiển thị pending rõ. (4) Backend validate grant, contributor/turn, tool, geometry/region và version theo contract B22. (5) Ghi accepted operation rồi acknowledge/fanout; UI đổi sang đã lưu khi có durable ack.
- **Alternatives/errors:** gửi tool hidden bằng API vẫn bị policy từ chối; region/version/operation shape sai không được nhận. Hai thiết bị cùng vẽ phải giữ cả accepted contributions theo thuật toán đã duyệt. Nhập sticker/text/image khi capability chưa được duyệt trả unsupported, không mở camera/import tự động.
- **Persistent postconditions:** accepted operation log gắn principal/contributor/provenance, canvas revision/watermark tiến lên; pending/rejected không bị tuyên bố durable.
- **AT-UC-013-P:** Given hai thiết bị cùng shared canvas, When gửi nét hợp lệ đồng thời, Then cả hai contribution có trong checkpoint và mỗi thiết bị nhận ack đúng operation.
- **AT-UC-013-N:** Given Teacher tắt công cụ hoặc import chưa approved, When client gọi trực tiếp operation đó, Then backend reject và snapshot không thay đổi do lệnh trái policy.

### UC-014 — Xin hỗ trợ, khóa và khôi phục vùng vẽ

- **Actor / FR:** Child gửi help; Teacher được cấp quyền can thiệp; FR016.
- **Preconditions:** participant/canvas đúng scope; region policy có version; Teacher intervention/restore policy ở B19 đã được duyệt.
- **Trigger/input:** help request hoặc Teacher lock/unlock/restore region; target region/checkpoint, expected policy/document version và reason phù hợp.
- **Main flow:** (1) Help request xuất hiện trong queue/dashboard, không suy ra diagnosis. (2) Teacher xem scope và có thể đặt region permission/lock. (3) Backend ghi effective lock/version rồi thông báo thiết bị. (4) Operations mới kiểm tra vùng bị khóa ở server. (5) Restore theo policy tạo revision/correction event trỏ checkpoint và phạm vi, giữ history đã nhận.
- **Alternatives/errors:** presence của bạn không cấp quyền vùng; operation vượt biên/mixed vùng bị khóa xử lý theo validation đã duyệt, không dùng UI mask làm authorization. Restore checkpoint stale yêu cầu Teacher review tác động; unlock không hồi sinh các nét đã reject tự động. Help duplicate không tạo hàng chờ vô hạn.
- **Persistent postconditions:** region policy/help/Teacher intervention history và revision restore; accepted originals/operations trước vẫn có provenance, current view thể hiện đúng quyết định.
- **AT-UC-014-P:** Given vùng của A bị khóa, When Teacher unlock rồi Child gửi nét hợp lệ, Then nét được nhận theo lock version mới và intervention có log.
- **AT-UC-014-N:** Given lock hiệu lực, When client che UI lock hoặc replay nét trái quyền, Then server reject; restore không âm thầm xóa history contribution của bạn.

### UC-015 — Scoped undo, lịch sử và xem lại quá trình

- **Actor / FR:** Child theo contribution scope; Teacher can thiệp có quyền; FR018, FR021. Scoped undo/layer behavior chi tiết là `PROPOSED` và phụ thuộc B19/OD08.
- **Preconditions:** operation history bền vững có authorship/attribution; undo scope/tool/layer policy hiện hành; UX nâng cao cho nhóm 9–12 theo scope, thao tác layer cụ thể chỉ mở khi policy đã được duyệt cho phép.
- **Trigger/input:** undo/redo, yêu cầu replay accepted history hoặc thao tác layer được bật; target operation IDs và expected revision.
- **Main flow:** (1) Xác định operations thuộc contributor/turn được phép undo. (2) Hiển thị tác động, cảnh báo/xin Teacher action nếu liên quan nội dung người khác theo policy. (3) Backend validate target và ghi compensation operation thay vì xóa original log. (4) Replay dùng ordered accepted events/checkpoints và phân biệt AI layer. (5) Teacher review quá trình theo scope, không coi tốc độ vẽ là năng lực.
- **Alternatives/errors:** target operation của peer không thể bị undo chỉ vì cùng device/canvas; group/unknown attribution cần quy tắc đã duyệt. Redo không được bypass lock/consent hiện hành. Thiếu history thì báo phạm vi replay có dữ liệu, không dựng lại bằng AI như chứng cứ thật.
- **Persistent postconditions:** undo/redo compensation và attribution/Teacher intervention history; current canvas khác old snapshot nhưng old snapshot/log không bị thay.
- **AT-UC-015-P:** Given A/B cùng canvas có nét được nhận, When A undo nét A theo policy, Then chỉ tác động hợp lệ được ghi, nét B giữ và replay cho thấy cả nét gốc/undo.
- **AT-UC-015-N:** Given A chọn operation B, When gọi undo trực tiếp, Then server từ chối hoặc yêu cầu Teacher intervention theo policy; không xóa attribution/historical evidence.

### UC-016 — Disconnect, resync và phục hồi phiên/canvas

- **Actor / FR:** Child/device và Teacher; FR017, FR060, FR063. Offline authoring và Teacher-offline continuation chi tiết `PROPOSED`, chưa được mặc định là quyền vẽ vô hạn.
- **Preconditions:** có checkpoint/ack watermark, device binding và connection state; contract gap/replay/policy ở B19/B22 đã được duyệt.
- **Trigger/input:** mất mạng/app restart/backend recovery rồi reconnect; last accepted watermark và local draft operation IDs/context.
- **Main flow:** (1) Hiển thị disconnected/local draft khác durable state. (2) Reconnect xác minh grant hiện hành. (3) Fetch checkpoint+delta từ watermark và detect gaps. (4) Reconcile accepted IDs trước replay drafts. (5) Validate từng pending operation với membership/lock/consent/turn hiện hành; giữ rejected draft cho recovery UX. (6) Teacher-offline actions cần approval tiếp tục đợi; drawing chỉ tiếp tục trong scope policy cho phép.
- **Alternatives/errors:** grant hết hạn/revoked phải rebind qua Teacher, không replay trước auth. Đồng bộ gap không thể chỉ áp event sau cùng; checkpoint fallback không mất acknowledged nét. Storage restart restore accepted log; pending chưa nhận không bị báo đã lưu. Offline quyền chưa duyệt không tự bật.
- **Persistent postconditions:** checkpoint/watermark và accepted operations khôi phục chính xác; không duplicate contribution/participant. Recovery decisions và lỗi lưu được truy vết.
- **AT-UC-016-P:** Given vài nét đã ack và vài nét local pending, When restart/reconnect, Then acked nét restore đủ, replay không duplicate và UI phân biệt các trạng thái còn chờ.
- **AT-UC-016-N:** Given Teacher khóa vùng hoặc revoke binding trong lúc offline, When replay pending nét, Then nét trái policy không được commit, local draft được giải thích/khôi phục theo policy và không bypass review.

### UC-017 — Tách gợi ý AI và giữ quyền vẽ của trẻ

- **Actor / FR:** Child/Teacher; FR019, FR028. Tách AI khỏi nét trẻ là `CONFIRMED`; view không AI và cơ chế layer cụ thể `PROPOSED`.
- **Preconditions:** canvas có child accepted operations và có thể có proposal đã approved ở đúng scope; overlay adapter không sở hữu child source operations.
- **Trigger/input:** bật/tắt reference/overlay view, tiếp tục vẽ khi AI phân tích hoặc đang chờ review; assistance policy version.
- **Main flow:** (1) Render child strokes từ document riêng với suggestion layer. (2) Hiển thị nhãn AI/reference khi suggestion được phép xuất hiện. (3) Child chuyển view không AI theo capability được duyệt. (4) Input của trẻ luôn ghi operation child bình thường. (5) Các AI callbacks chỉ tạo proposal/result reference, không sửa child strokes.
- **Alternatives/errors:** AI result không được phát dưới dạng replacement stroke; overlay API gửi mutation trực tiếp bị từ chối. Dừng vẽ, idle hoặc ít nét chỉ là signal được policy cho phép, không là kết luận thiếu kiến thức; không tự tạo report deficit/forced intervention.
- **Persistent postconditions:** child source unchanged khi chỉ toggling AI view; proposal/provenance và child response có history riêng. Chỉ thao tác vẽ thực của trẻ tạo contribution trẻ.
- **AT-UC-017-P:** Given approved overlay cùng child strokes, When ẩn overlay rồi tiếp tục vẽ, Then child snapshot giữ đúng nét gốc và nét mới, AI layer có thể truy vết riêng.
- **AT-UC-017-N:** Given trẻ dừng vẽ hoặc AI đề xuất stroke replacement, When callback chạy, Then không thay tranh/đánh giá thiếu năng lực/tự ép hỗ trợ chỉ từ idle.

### UC-018 — Vision và xác nhận/correction ý nghĩa

- **Actor / FR:** Child giải thích theo format đã được duyệt; Teacher xác nhận; FR022, FR023. Không tự thêm microphone/camera vào format giải thích.
- **Preconditions:** snapshot/vùng chốt có hash/revision, topic/age/context version và AI purpose được cấp; Vision policy/model config có version.
- **Trigger/input:** explicit analysis request hoặc signal được policy duyệt; snapshot/vùng, topic/age/context version, request/action summary theo policy, child statement nếu có và Teacher feedback. Không gọi Vision trên từng pointer event.
- **Main flow:** (1) Validate nguồn/purpose và capture context version. (2) Worker nhận snapshot qua backend port. (3) Lưu object candidates/context/uncertainty kèm provenance, không coi top label là ground truth. (4) Child/Teacher confirm/correct intended concept. (5) Ghi MeaningConfirmation version và dùng context đã xác nhận cho downstream phù hợp.
- **Alternatives/errors:** low confidence cho chọn/correction, không bịa intent. Canvas/context đổi làm result stale theo B19/B22; Teacher không “approve tất cả phiên” bằng correction cũ. Raw observation giữ nguyên khi correction khác; không tự infer tuổi/mental state.
- **Persistent postconditions:** VisionObservation source refs và MeaningConfirmation riêng, có actor/version. Downstream biết đâu là model candidate, đâu là child intent/Teacher correction.
- **AT-UC-018-P:** Given Vision gọi hình là mèo nhưng trẻ muốn hổ, When Teacher xác nhận correction, Then downstream dùng concept đã chốt và observation mèo vẫn giữ provenance.
- **AT-UC-018-N:** Given snapshot/context đã đổi hoặc AI đoán tuổi, When worker trả result, Then không dùng suy tuổi/cũ làm authoritative context, không silently thay meaning đã chốt.

### UC-019 — Yêu cầu và chuẩn bị Sketch proposal

- **Actor / FR:** Child yêu cầu, Teacher kích hoạt/hủy; FR024, FR025, FR030. Taxonomy level/cache/debounce/budget là `PROPOSED`, không chốt model/output shape.
- **Preconditions:** assistance enabled trong scope, consent AI purpose, valid snapshot/context và current request limits; required per-item review vẫn bật.
- **Trigger/input:** help/request sketch hoặc Teacher manual trigger; requested support mode/level, target region và idempotent request ID.
- **Main flow:** (1) Resolve current snapshot/confirmed meaning và quyền. (2) Dedup request, apply budget/debounce/cache theo policy B19/B22. (3) Schedule backend job và hiển thị pending. (4) Worker tạo reference/overlay proposal với source/config/model provenance. (5) Revalidate cancellation/scope/staleness, lưu proposal chờ moderation/review UC-020.
- **Alternatives/errors:** hết budget/rate limit trả cách tiếp tục vẽ hoặc Teacher action, không gửi provider request vô hạn. Cache hit vẫn kiểm tra age/topic/consent/version và phải Teacher review từng item trước trẻ. Teacher cancel thì late result không tự available; stale result không rebase ngầm.
- **Persistent postconditions:** request/job/proposal hoặc failure/cancellation typed outcome có traceability; chưa có child exposure hoặc mutation tranh.
- **AT-UC-019-P:** Given request hợp lệ, When retry cùng key trong lúc job chạy, Then có một semantic request/job/result và proposal đi vào review, trẻ tiếp tục vẽ được.
- **AT-UC-019-N:** Given request đã cancel hoặc context đổi, When result/cache hit về, Then không tự phát overlay/đổi source; ngân sách/dedup không thay Teacher approval.

### UC-020 — Moderation và Teacher duyệt từng Sketch

- **Actor / FR:** Teacher; FR026, FR029, FR061. **OWNER_CONFIRMED:** mỗi gợi ý được Teacher duyệt trước phát cho trẻ trong pilot.
- **Preconditions:** proposal/source/audience/config versions còn hợp lệ; moderation outcome được policy cho phép review; Teacher có teaching/review scope.
- **Trigger/input:** approve/reject hoặc chỉnh support level/content; content ID/version/hash và expected review context.
- **Main flow:** (1) Moderation chặn unsafe hoặc trả typed failure và safe Teacher notice. (2) Queue hiển thị proposal/context cho Teacher đúng quyền. (3) Teacher xem, chỉnh hoặc reject. (4) Chỉnh tạo phiên bản mới và chạy lại checks cần thiết; approve gắn exact version/hash/audience/policy. (5) Application revalidate trước ghi review và trước phát approved item.
- **Alternatives/errors:** unsafe output không có nút bypass bằng preset; failure không đưa provider internals vào Child UI. Source/audience thay đổi làm review stale. Duplicate approve không nhân đôi; Admin chỉ có system role không tự là reviewer. Pending/Rejected/Blocked/edited-unreviewed không vào child payload/subscription.
- **Persistent postconditions:** moderation/review history, approved exact item hoặc rejected/blocked outcome; original proposal và edits đều có provenance. Child access chỉ mở cho review còn hiệu lực.
- **AT-UC-020-P:** Given safe proposal đúng snapshot/audience, When Teacher approve item, Then review exact hash lưu và chỉ participants được cấp scope nhận item.
- **AT-UC-020-N:** Given pending/unsafe/stale hoặc item đã chỉnh sau review, When child fetch/subscription yêu cầu artifact, Then không trả content; preset “AI enabled” không bypass gate.

### UC-021 — Child xem, ẩn và từ chối gợi ý

- **Actor / FR:** Child trong scope; FR027.
- **Preconditions:** proposal đã qua UC-020, còn available/current và grant được phép xem/đáp; format view phù hợp tuổi theo B23.
- **Trigger/input:** request/view/hide/decline proposal; proposal version và participant/turn context khi cần attribution response.
- **Main flow:** (1) Child thấy có trợ giúp được phép. (2) Chọn xem reference/overlay. (3) Child có thể ẩn hoặc từ chối bằng action phù hợp tuổi. (4) Ghi response riêng với canvas; trở lại vẽ tự do. (5) Teacher projection thấy response để điều chỉnh hỗ trợ theo policy, không tự coi decline là lỗi học tập.
- **Alternatives/errors:** review bị revoke trước fetch thì unavailable; decline retry không sinh nhiều records semantic. Decline không tự xóa nét trẻ/đánh trừ điểm/tự gọi lại model để ép nhận. Việc muốn xem lại item đã decline cần policy rõ, không tự refresh proposal mới.
- **Persistent postconditions:** response actor/proposal/version/time có history, canvas child source giữ nguyên; item review và child choice là records khác nhau.
- **AT-UC-021-P:** Given approved suggestion, When Child xem rồi hide/decline, Then overlay biến mất theo lựa chọn, response lưu và vẽ vẫn tiếp tục.
- **AT-UC-021-N:** Given proposal pending hoặc đã revoked, When client dùng URL/ref cũ, Then không nhận content; decline không tạo deficit assessment hoặc tự cưỡng ép gợi ý mới.

### UC-022 — Gallery và trình bày ý tưởng trong lớp

- **Actor / FR:** Teacher điều phối, Child preview/trình bày; FR031, FR032, FR033. Format giải thích, annotations và snapshot sharing chi tiết `PROPOSED`.
- **Preconditions:** accepted snapshot và share scope hợp lệ, purpose cho phép; Teacher có class/session access. Audio/image explanation chưa được chọn không tự thu thập.
- **Trigger/input:** chọn/order/share snapshot, annotate/present; Child giải thích bằng format đã được duyệt; version/scope/audience references.
- **Main flow:** (1) Teacher chọn snapshot thay vì mutable live pointer. (2) Preview với attribution và nhãn AI/child source. (3) Chọn thứ tự/chú thích và authorized audience. (4) Child trình bày/giải thích theo format phù hợp tuổi; Teacher hỗ trợ khi cần. (5) Lưu share/presentation/annotation version và kết nối reflection/knowledge.
- **Alternatives/errors:** cross-class share/subscription denied; unauthorized raw original không đi cùng thumbnail. Canvas thay đổi sau chọn không tự thay ảnh đang trình chiếu; Teacher chọn snapshot mới để cập nhật. Peer/group artwork không gắn sở hữu cá nhân nếu attribution không đủ. Recalled/unsafe AI content không được gallery bypass gate.
- **Persistent postconditions:** ArtworkShare snapshot/order/annotations/audience và presentation evidence; canvas originals không thay đổi; không tạo public gallery.
- **AT-UC-022-P:** Given hai group snapshots, When Teacher chọn/order và Child giải thích, Then trình chiếu đúng versions/scope và lưu author/source labels.
- **AT-UC-022-N:** Given viewer thuộc lớp khác hoặc share trỏ mutable/stale item, When truy cập, Then không nhận content ngoài quyền hoặc version thay âm thầm; không tự bật mic/camera.

### UC-023 — Knowledge có nguồn và chọn/tạo video

- **Actor / FR:** Teacher, backend worker là technical actor; FR034, FR035, FR040. Source-grounded script/pre-render workflow và TTS nếu chọn là `PROPOSED`; không chốt model/voice/duration.
- **Preconditions:** concept/context được xác nhận; library/source content đủ review status; policy tuổi/purpose/provider hợp lệ.
- **Trigger/input:** Teacher yêu cầu knowledge cho lớp hoặc child scope được phép; concept, audience, source refs, library selection hoặc render request.
- **Main flow:** (1) Resolve topic/confirmed concepts và audience. (2) Tìm source/library phù hợp, kiểm tra version/recall. (3) Soạn knowledge/script gắn factual statements với nguồn, tách chi tiết tưởng tượng. (4) Teacher chỉnh script nếu workflow được duyệt. (5) Chọn video library hoặc tạo render job từ script/config version; media/TTS nếu có giữ provenance riêng. (6) Result đi UC-024, không auto play.
- **Alternatives/errors:** thiếu nguồn đáng tin thì báo cần Teacher content action, không biến hình tưởng tượng thành khoa học. Script edit tạo version mới; downstream old render không tự hợp lệ. Library hit vẫn cần Teacher approve đúng video cho audience; provider/cache không là approval.
- **Persistent postconditions:** KnowledgeBundle/script/source refs và video job/library reference, audience/policy versions; chưa có playback authorization.
- **AT-UC-023-P:** Given confirmed concept và library hợp lệ, When Teacher chọn hoặc render knowledge, Then script/source/audience provenance đầy đủ và media chờ exact-version review.
- **AT-UC-023-N:** Given tranh có động vật tưởng tượng hoặc thiếu nguồn, When tạo kiến thức, Then không trình bày imagined details là facts hoặc dùng recalled asset cho phiên mới.

### UC-024 — Teacher review video và bắt đầu trình chiếu

- **Actor / FR:** Teacher; FR036.
- **Preconditions:** media artifact ready, moderation hợp lệ, bundle/script/audience versions phù hợp; Teacher có quyền review/playback.
- **Trigger/input:** preview/approve/reject/edit video hoặc script liên quan; exact artifact ID/hash/version/audience; explicit StartPlayback.
- **Main flow:** (1) Teacher xem artifact thực và nguồn/context. (2) Approve hoặc reject; chỉnh sửa tạo version mới và quay lại checks/render khi cần. (3) Ghi review exact content và audience. (4) Khi Teacher start, backend kiểm tra review/consent/publication hiện hành. (5) Phát authorized playback reference và ghi playback state, không auto-start từ job ready.
- **Alternatives/errors:** sửa script/audio/video sau approve làm bản mới chưa approved; đổi audience cần review applicability check theo policy. Ready không có review là không playable; old artifact reference không được vượt scope. Provider result tới sau cancel không tự play.
- **Persistent postconditions:** review history và explicit playback authorization/events; review cũ vẫn chứng minh bản cũ nhưng không approve mọi phiên bản.
- **AT-UC-024-P:** Given exact video v1/h1 safe, When Teacher approve rồi start đúng audience, Then chỉ v1/h1 được playback và review/play command lưu.
- **AT-UC-024-N:** Given script/media chuyển v2 sau review v1 hoặc viewer khác scope, When start/fetch v2, Then không phát cho đến review hợp lệ; job Ready không tự autoplay.

### UC-025 — Video đang tạo: trạng thái thật và chờ

- **Actor / FR:** Teacher, Child xem trạng thái được phép; FR037, FR038. Chờ khi Generating là `CONFIRMED`; activity trong lúc chờ là proposal, không tự đổi stage.
- **Preconditions:** có video job/request version, session chưa kết thúc/cancel, authorized viewers; progress contract phân biệt trạng thái và phần trăm thực.
- **Trigger/input:** job accepted/progress/ready/failure update hoặc query status; job/version/correlation refs.
- **Main flow:** (1) Hiển thị Generating và thông tin status có thật. (2) Poll/subscribe theo contract, không tạo job mới mỗi refresh. (3) Teacher có thể trao đổi về tranh trong lúc chờ nếu policy cho phép. (4) ReadyForReview chuyển vào UC-024. (5) Failed đi UC-026 khi hết retries được policy cho phép; lớp chỉ đổi shared stage bằng Teacher action.
- **Alternatives/errors:** provider chỉ có status thì không dựng percent giả; temporary transport loss báo chưa xác định, không tự Failed/Success. Chậm quá timeout dùng typed policy outcome, không auto fallback video hoặc skip. Cancel/end early xử lý version để late update không hồi sinh stage.
- **Persistent postconditions:** job/status/attempt history và session disposition hợp lệ; waiting không là video completion hoặc off-screen completion.
- **AT-UC-025-P:** Given job đang Generating, When nhiều refresh/progress updates rồi Ready, Then chỉ có một job semantic, UI chờ rồi vào review, không tự play.
- **AT-UC-025-N:** Given job vẫn Generating lâu hoặc transport mất, When timeout/status query lỗi, Then không tự chiếu fallback/skip Knowledge hoặc báo Completed giả.

### UC-026 — Teacher quyết định sau video thất bại

- **Actor / FR:** Teacher; FR039. **OWNER_CONFIRMED:** sau hết retries được phép, Teacher chọn thử lại, bỏ qua hoặc kết thúc; retry budget/timeouts vẫn policy/TBD.
- **Preconditions:** Failed final outcome theo policy có attempt history, session chưa terminal; Teacher có scope/control và current version.
- **Trigger/input:** RetryVideo, SkipVideoByTeacher hoặc EndSessionByTeacher; failed request ref, reason/disposition và idempotency key.
- **Main flow:** (1) Hiển thị lỗi an toàn, attempts và ba lựa chọn. (2) Teacher explicit chọn action. (3) Retry tạo attempt/request lifecycle theo budget authorization, giữ nguồn context và revalidate. (4) Skip ghi disposition và Teacher quyết định tiến tới bước được phép. (5) End lưu EndedEarly cùng evidence đã có theo UC-010/011.
- **Alternatives/errors:** hết budget mới không tự grant retry vô hạn; báo Teacher cần authorization/config phù hợp. Duplicate skip/end không tạo nhiều transitions. Job cũ tới sau quyết định không auto rollback/chiếu; skip không bị ghi video success.
- **Persistent postconditions:** failed history, Teacher choice/reason và request/transition version; retained outcomes phân biệt success, skipped, ended early.
- **AT-UC-026-P:** Given Failed exhausted, When Teacher chọn skip, Then lưu explicit disposition/actor, stage chỉ chuyển theo lệnh và video không được báo đã hoàn thành.
- **AT-UC-026-N:** Given Teacher chưa chọn hoặc retry không được budget policy cho phép, When scheduler xử lý failure, Then không tự skip/end/retry vô hạn hoặc phát late result của request cũ.

### UC-027 — Chọn/chỉnh hoạt động và xác nhận khả thi/an toàn

- **Actor / FR:** Teacher; FR041, FR042, FR043. Library/recommendation và Teacher chọn/chỉnh là `CONFIRMED`; trường activity/material confirmation chi tiết `PROPOSED`.
- **Preconditions:** topic/age context được xác nhận; activity version đủ publication status; safety/material policy được duyệt trước cho trẻ thực hiện.
- **Trigger/input:** discover/recommend activities, chọn/chỉnh assignment lớp/nhóm, xác nhận materials và bắt đầu; activity/objective/version refs.
- **Main flow:** (1) Teacher xem library và AI recommendations có lý do/nguồn. (2) Chọn lớp hoặc nhóm; xem mục tiêu, độ tuổi, vật liệu, bước làm, dự kiến thời lượng, safety/observation theo schema B21. (3) Chỉnh cho điều kiện lớp, tạo assignment version giữ source. (4) Teacher kiểm tra vật liệu thực và xác nhận an toàn/khả thi. (5) Start chỉ khi guards hợp lệ; phát hướng dẫn theo nhóm/audience.
- **Alternatives/errors:** discovery rộng không bị tự hard-filter readiness chưa được duyệt; execution safety checks vẫn bắt buộc theo policy. Thiếu vật liệu/rủi ro chưa xử lý thì chọn/chỉnh hoạt động khác, không start vì AI đã chọn. Edit safety-critical cần review lại; recalled version không assignment cho phiên mới.
- **Persistent postconditions:** assignment/source/version, Teacher edits/material-safety decision và started state; recommendation không thay Teacher approval.
- **AT-UC-027-P:** Given hoạt động phù hợp và vật liệu có thật, When Teacher chỉnh cho nhóm B rồi xác nhận/start, Then assignment B lưu source+edits và child nhận đúng instructions.
- **AT-UC-027-N:** Given vật liệu nguy hiểm/thiếu hoặc activity đã recalled, When AI/client gọi start, Then guard từ chối; Teacher phải xử lý/đổi hoạt động, không bỏ safety gate.

### UC-028 — Off-screen evidence và reflection

- **Actor / FR:** Child với Teacher hỗ trợ, Teacher ghi nhận; FR044. Format reflection/evidence `PROPOSED/TBD`, không tự bật mic/camera.
- **Preconditions:** activity assignment hợp lệ hoặc session cần lưu outcome đã thực hiện; reflection formats/purposes đã duyệt; participant/group attribution rõ hoặc ghi group/unknown.
- **Trigger/input:** Teacher đánh dấu thực hiện/kết thúc activity; Child phản hồi bằng format được bật; Teacher thêm evidence reference/notes.
- **Main flow:** (1) Hiển thị instructions và chuyển sang off-screen theo Teacher control. (2) Teacher ghi trạng thái thực hiện và observation/evidence phù hợp. (3) Child reflection theo format tuổi đã duyệt, có quyền bỏ qua theo policy. (4) Tách child statement, Teacher note và evidence về nhóm/cá nhân. (5) Lưu records vào session và portfolio processing UC-030.
- **Alternatives/errors:** chưa có reflection không suy thiếu năng lực; audio/image chưa consent/capability không được thu. Group activity không tự chứng minh mỗi trẻ làm tất cả bước. Save failed giữ draft/status để retry; kết thúc sớm không báo activity hoàn thành nếu chưa làm.
- **Persistent postconditions:** ActivityOutcome/ReflectionRecord/evidence refs có author/source/attribution/save status; không chép peer evidence thành cá nhân.
- **AT-UC-028-P:** Given nhóm thực hiện activity, When Teacher ghi outcome và Child reflection hợp lệ, Then session giữ cả hai nguồn riêng và portfolio dùng đúng scope/attribution.
- **AT-UC-028-N:** Given reflection chưa được ghi hoặc format mic chưa approved, When submit/complete, Then không tự thu audio hoặc tạo negative assessment; incomplete khác successful outcome.

### UC-029 — Teacher observation và assessment theo tuổi

- **Actor / FR:** Teacher; FR045, FR049, FR050. Assessment tuổi/quá trình `CONFIRMED`; rubric/descriptive levels `PROPOSED` OD10, inference bị cấm theo repo.
- **Preconditions:** Teacher có assessment scope; age/context/rubric version đã được duyệt cho audience; evidence thuộc session/child/group hợp lệ.
- **Trigger/input:** ghi observation, nhận AI suggestion nếu purpose/capability được phép, confirm/edit assessment; criterion/evidence/version refs.
- **Main flow:** (1) Teacher xem evidence/process với attribution/source. (2) Ghi mô tả khám phá/hợp tác/diễn đạt hoặc criterion đã duyệt. (3) Nếu có AI, tách suggestion từ Teacher judgment, kèm nguồn và uncertainty. (4) Teacher confirm/chỉnh/reject; tiêu chí chưa có evidence ghi “chưa quan sát”. (5) Lưu observation confirmed và link portfolio/report, so tiến bộ của chính trẻ.
- **Alternatives/errors:** rubric chưa duyệt không tự triển khai mặc định như scale chính thức. Evidence của peer hoặc AI inference không được đánh dấu direct evidence của trẻ. Không infer intelligence/personality/psychology/diagnosis; thiếu quan sát không tự lowest level.
- **Persistent postconditions:** versioned ObservationRecord, criterion/evidence source, AI suggestion riêng và Teacher decision; no ranking/diagnostic label.
- **AT-UC-029-P:** Given evidence đúng trẻ và một criterion chưa quan sát, When Teacher confirm nhận xét, Then report giữ judgment/evidence tách biệt và ghi chưa quan sát cho criterion thiếu.
- **AT-UC-029-N:** Given chỉ có AI label hoặc group art không xác định contribution, When generate assessment, Then không suy diagnosis/deficit hoặc gán evidence cá nhân sai; không publish unconfirmed AI judgment.

### UC-030 — Session history và portfolio bền vững

- **Actor / FR:** Teacher; FR047.
- **Preconditions:** session/products/process/review/outcome refs có save status; purpose và portfolio scope hợp lệ; attribution policy được duyệt. Session/artwork nguồn lưu 90 ngày sau end; portfolio duration/retained-derivative disposition riêng chưa chốt, không giữ raw source vô hạn vì entry có link.
- **Trigger/input:** tạo/cập nhật entry từ session hoàn tất/draft outcome được phép; evidence bundle refs, source versions và Teacher approved summary.
- **Main flow:** (1) Thu thập artwork/contribution/process/AI usage/content/comments/activity/reflection refs theo scope. (2) Phân biệt direct individual evidence với group participation/unknown attribution. (3) Teacher review summary, không tự coi AI content là nét trẻ. (4) Ghi entry identity theo source session+student để retry idempotent. (5) History/read model hiển thị entry và các versions/sources được phép truy cập.
- **Alternatives/errors:** evidence thiếu hoặc artifact chưa durable giữ pending/partial trạng thái rõ. Group canvas không copy toàn bộ contribution vào mọi portfolio như tác phẩm riêng. Retention/consent thay đổi làm evidence unavailable cần giữ disposition theo policy, không broken link được coi là bằng chứng còn xem được.
- **Persistent postconditions:** PortfolioEntry/history/source lineage bền vững; summary edits giữ version; không thay original artwork/process bằng AI summary.
- **AT-UC-030-P:** Given shared canvas có nét A/B và activity outcome, When tạo portfolio A rồi retry, Then một entry có contribution A và group context đúng, không nhân đôi.
- **AT-UC-030-N:** Given contribution unknown hoặc storage chưa xác nhận, When tạo entry, Then không tuyên bố tranh cả nhóm của A hoặc báo complete evidence giả.

### UC-031 — Báo cáo tiến bộ và export theo quyền

- **Actor / FR:** Teacher hoặc actor được cấp reporting scope; FR046, FR048. Evidence taxonomy `PROPOSED`; no child-to-child ranking `CONFIRMED`.
- **Preconditions:** portfolio entries/observations được Teacher confirm; reporting/export purpose hợp lệ; actor chỉ có phạm vi học sinh được cấp.
- **Trigger/input:** chọn học sinh/time range/criteria/report format được duyệt; export request ID nếu cần artifact đầu ra.
- **Main flow:** (1) Resolve authorized entries và policy. (2) So các mốc của chính học sinh, chỉ mô tả thay đổi có evidence. (3) Tách direct evidence, Teacher observation và AI suggestion; hiển thị gaps/chưa quan sát. (4) Teacher review báo cáo trước share theo policy. (5) Export tạo artifact minimised theo scope, ghi actor/purpose/status và access expiry theo B24/B22.
- **Alternatives/errors:** cross-class export bị chặn cả nội dung lẫn aggregate dễ tái định danh. Không tạo rank/percentile so bạn, “điểm sáng tạo” hoặc diagnosis từ tranh. Nếu quyền bị revoke trong job thì recheck trước phát/download; export lỗi không cung cấp file partial như hoàn tất.
- **Persistent postconditions:** report/source versions, review/export request/audit và authorized artifact; export không tự mở public link.
- **AT-UC-031-P:** Given cùng trẻ có hai mốc confirmed, When Teacher tạo report, Then mô tả tiến bộ riêng với source labels, chưa quan sát hiện rõ và export đúng quyền.
- **AT-UC-031-N:** Given user yêu cầu bảng xếp hạng hoặc export trẻ ngoài scope, When generate/download, Then không tạo ranking/tiết lộ data; role Teacher không đủ mở mọi portfolio.

### UC-032 — Dashboard toàn lớp và queue hỗ trợ

- **Actor / FR:** Teacher; FR051, FR054. Queue priority/overload limits `PROPOSED`, workload targets ở B25.
- **Preconditions:** Teacher session access; projections/presence/help/review records phân biệt durable/ephemeral và timestamp freshness.
- **Trigger/input:** mở live dashboard, filter groups/help/review, ưu tiên item hoặc nhận overload indication; session/group scope.
- **Main flow:** (1) Load authorized groups/status/previews và class control state. (2) Hiển thị connection freshness riêng progress. (3) Queue gom help/review requests và policy-based priority có lý do. (4) Teacher mở context item/approve/intervene qua use case có quyền tương ứng. (5) Khi quá tải, ưu tiên/cancel/defer theo policy nhưng ghi automated action và Teacher override.
- **Alternatives/errors:** stale preview không báo live; mất Teacher connection chuyển trạng thái và recovery UC-016. Queue overflow không tự approve/drop requests không ghi dấu; chưa có priority policy dùng thứ tự rõ đã duyệt, không suy weak child từ idle. Subscriber lớp khác denied.
- **Persistent postconditions:** durable help/review decisions/automation actions và audit; projection/presence không thay nguồn state.
- **AT-UC-032-P:** Given nhóm có help và pending Sketch, When Teacher mở dashboard xử lý item, Then context đúng scope, item lifecycle lưu và queue refresh phản ánh decision.
- **AT-UC-032-N:** Given overload/stale preview hoặc unauthorized subscriber, When dashboard updates, Then không autoapprove/giả live/tiết lộ thumbnail; automation có traceable disposition.

### UC-033 — Preset, automation và Teacher override

- **Actor / FR:** Teacher; FR052, FR053. Preset fields/automation conditions `PROPOSED`; quyền Teacher override `CONFIRMED`.
- **Preconditions:** Teacher preset/session scope; preset schema/conditions/version và mandatory gates B19 được duyệt. System safety/consent/review guards không bị Teacher preference vô hiệu hóa.
- **Trigger/input:** tạo/version preset, áp vào draft, enable conditional automation hoặc override effective setting đang chạy; expected config/session version.
- **Main flow:** (1) Teacher chọn/edit topic/age/tools/canvas/AI/stage/notifications/video/activity/assessment settings được phép. (2) Lưu immutable preset version và effective config riêng cho phiên. (3) Evaluate automation trên state/condition version hiện hành. (4) Trước action recheck scope/guards và ghi decision. (5) Teacher override/disable bất kỳ lúc có quyền; ghi override version và reconcile scheduled work bị ảnh hưởng.
- **Alternatives/errors:** sửa preset library không retroactively đổi active session. Preset không bỏ per-Sketch/video approval, consent hoặc tự completion/xóa sản phẩm. Job/automation đang chạy sau override phải kiểm tra version, không chạy lệnh cũ. Invalid config trả field-level errors, không half-apply.
- **Persistent postconditions:** preset history, session effective config, automation/override reason/actor/version; bắt buộc gates vẫn có hiệu lực.
- **AT-UC-033-P:** Given automation đúng policy, When Teacher override tool/disable hỗ trợ, Then config mới effective có audit và scheduled stale action không được commit.
- **AT-UC-033-N:** Given preset chứa bypass review hoặc mutable update, When apply vào phiên, Then reject bypass và active session không bị đổi bởi sửa preset bên ngoài.

### UC-034 — Provision, phân quyền và đình chỉ tài khoản

- **Actor / FR:** Super Admin có administrative scope; FR055, FR058. Quyền admin raw-data access chi tiết `PROPOSED`, không mặc định theo role.
- **Preconditions:** Admin identity verified và policy cấp/đổi quyền đã được duyệt; nguồn xác thực vẫn Firebase Authentication-only.
- **Trigger/input:** provision/assign/revoke/suspend adult account, class scope hoặc request purpose-scoped data access; target/version/reason.
- **Main flow:** (1) Admin xem user/class/session operational overview được phép. (2) Kiểm tra target/actions tránh role từ client và privilege escalation. (3) Ghi account/status/assignments và scope hữu hiệu. (4) Suspend/revoke invalidates ongoing access/capabilities theo contract; impacted session xử lý recovery/control policy đã duyệt. (5) Raw-child-data access, nếu được policy cho phép, đi qua specific purpose/scope approval và audit riêng.
- **Alternatives/errors:** system admin account không tự teaching/review quyền mọi lớp. Suspended Teacher không tiếp tục approve bằng tab cũ. Không còn Teacher control cho active session dùng policy đã duyệt, không tự giao Admin đọc raw media/kết thúc/xóa. Revoke không delete lịch sử reviewer/contribution.
- **Persistent postconditions:** account/assignment/access-grant history có actor/reason và effective timestamps; original audit identities vẫn tham chiếu được với minimization policy.
- **AT-UC-034-P:** Given account Teacher có assignment A, When Admin suspend, Then các request/subscriptions mới bị chặn và lịch sử review/phiên còn provenance.
- **AT-UC-034-N:** Given Admin chỉ có user-management scope, When mở raw artwork hoặc approve Sketch lớp A, Then authorization từ chối dù role là Super Admin, không cấp global media access.

### UC-035 — Content authoring, review, publication và recall

- **Actor / FR:** Teacher author trong scope, Super Admin/publisher có quyền; FR056, FR062. Content lifecycle fields/reviewer separation `PROPOSED`.
- **Preconditions:** content type/schema/sources/version và publication/recall policy được duyệt; material không chứa raw child data ngoài purpose được phép.
- **Trigger/input:** tạo/edit/submit/review/publish/recall activity/knowledge/preset/library content; exact version/hash và reason.
- **Main flow:** (1) Author tạo draft giữ nguồn/provenance. (2) Edit tạo version mới, review scope có source/safety/age checks. (3) Authorized reviewer ghi decision exact version. (4) Publisher explicit publish version; catalog chỉ expose versions phù hợp. (5) Recall ghi reason/version/effective status; không cho phiên mới resolve recalled version và thông báo impacted references theo policy.
- **Alternatives/errors:** Teacher author không tự global publish nếu không quyền; edit không giữ approve cho bytes mới. Phiên đang chạy/portfolio dùng recalled content có policy riêng OD05/state phần liên quan, không tự silent delete/change history. Unsafe recall incident ưu tiên chặn access theo approved safety policy, giữ provenance.
- **Persistent postconditions:** content version/review/publication/recall history; new-session eligibility cập nhật; original references không bị rewrite thành version khác.
- **AT-UC-035-P:** Given published activity v1, When publisher recall, Then phiên mới không dùng v1 và audit lưu reason/version, lịch sử nguồn cũ còn traceable.
- **AT-UC-035-N:** Given author chỉnh v1 thành v2 hoặc Teacher chưa có publisher scope, When publish/use new session, Then không dựa approval v1 hoặc role author để bỏ publication gate.

### UC-036 — AI policy/configuration có version

- **Actor / FR:** Super Admin có AI-policy scope; làm rõ phần system AI policies/limits của FR056.
- **Preconditions:** policy schema/allowed operations và technical decision gate đã được duyệt; không chốt provider/model qua use case này. Provider secrets ở backend runtime secret mechanism.
- **Trigger/input:** tạo/validate/publish/disable AI configuration version; permitted model profile refs, moderation/review/limit/budget settings và effective scope.
- **Main flow:** (1) Admin xem configuration metadata/redacted operational status. (2) Draft policy và validate compatibility/mandatory safety gates. (3) Review/publish theo governance policy, ghi effective version/scope. (4) Request mới pin version; worker completion kiểm tra current eligibility trước phát. (5) Disable/emergency stop ngăn work mới và xử lý work đang chạy theo cancellation/stale contract.
- **Alternatives/errors:** secret/endpoint không trả mobile hoặc logs; thử tăng limit không tự bypass budget authorization. Policy không vô hiệu hóa per-item Teacher review của pilot/consent/safety guard. Version cũ không silently biến thành config mới; nguồn model/source provenance giữ.
- **Persistent postconditions:** policy/config version, admin change/audit và job/request pinned references; không upgrade library/cloud hoặc đưa credentials vào source.
- **AT-UC-036-P:** Given published policy P1, When Admin publish P2 rồi tạo request mới, Then request mới pin P2, request cũ giữ provenance P1 và revalidate trước exposure.
- **AT-UC-036-N:** Given config chứa secret hoặc bypass mandatory review, When validate/publish/read từ Child, Then bypass bị reject và credentials không được hiển thị/phát xuống client.

### UC-037 — Monitoring, audit và incident theo scope

- **Actor / FR:** Super Admin/operator có operational/audit/report scope; FR057.
- **Preconditions:** domain history, security audit và technical telemetry được tách; redaction/retention/access policies đã được duyệt; purpose của investigation rõ.
- **Trigger/input:** xem health/session/review/save metrics, query audit hoặc mở incident; time range/scope/action/correlation refs và reason khi policy yêu cầu.
- **Main flow:** (1) Load metrics/projections được phép, chỉ metadata tối thiểu. (2) Tìm correlation nối command/job/control/save decisions mà không lộ raw media. (3) Khi cần điều tra, mở incident và access dữ liệu riêng theo specific grant UC-034. (4) Ghi operational action, evidence refs và disposition. (5) Theo dõi recovery/consent/data-request status nhưng không đổi state bằng sửa log.
- **Alternatives/errors:** audit viewer không mặc định raw-content viewer; exported telemetry không chứa tên trẻ/token/prompt/signed URL. Missing metrics báo unavailable, không coi zero. Unauthorized audit query/incident access bị chặn; audit log không được edit để xóa dấu vết lỗi.
- **Persistent postconditions:** query/access/action audit và incident record có purpose/actor; technical metric không thay domain truth hoặc portfolio evidence.
- **AT-UC-037-P:** Given video failure và save error có correlation, When operator có quyền mở incident, Then nối đúng decisions và recovery status bằng metadata redacted.
- **AT-UC-037-N:** Given chỉ monitoring scope, When query raw canvas/prompt/child identity hoặc sửa audit, Then từ chối; telemetry không chứa secrets/raw child media.

### UC-038 — Retention, yêu cầu xuất/xóa và kiểm chứng purge

- **Actor / FR:** người được trường xác minh có thẩm quyền yêu cầu, Teacher/Admin ghi/xử lý trong scope; FR059, FR064. Không cần Parent portal; không tự coi Teacher là legal representative. Retention/shared deletion/provider-backup policy `PROPOSED/TBD` OD05/17.
- **Preconditions:** requester authority được kiểm tra theo quy trình; current data policy/subject/scope rõ. **OWNER_CONFIRMED:** session/artwork lưu 90 ngày sau end; portfolio/profile/audit không dùng TTL này mặc định. Các TTL riêng, copies/backups/shared-work/legal exceptions cần được duyệt trước vận hành thực.
- **Trigger/input:** export/delete request hoặc retention expiry; subject/data classes/purpose, evidence authority, request ID và policy/version.
- **Main flow:** (1) Trường/authorized actor ghi request và verify authority, không công bố data trước verify. (2) Resolve identity/session/artwork/derivatives/AI/cache/portfolio/copies lineage, tách shared peer data. (3) Export chỉ nội dung được phép; delete/expiry restrict access và hủy future work phù hợp. (4) Execute purge qua storage/provider/backup ports theo policy, ghi receipts/exceptions/pending states. (5) Review shared-canvas impact theo policy đã duyệt, giữ peer rights và audit minimization. (6) Chỉ báo Completed khi tiêu chí scope/copies/exceptions được đáp ứng; requester nhận outcome theo kênh đã được duyệt riêng.
- **Alternatives/errors:** mixed attribution/shared artwork hoặc authority chưa rõ chuyển policy review, không tự xóa cả canvas/giao peer raw data. Provider/backup chưa purge không báo all-copies-deleted; retry idempotent và giữ pending exception. Audit retained có policy/purpose/minimization riêng, không retention vô hạn do tiện vận hành. Revoke lúc export chạy yêu cầu revalidate trước download.
- **Persistent postconditions:** verified request/status, inventory/lineage, authorized export hoặc deletion receipts/exception refs, minimized audit; no orphan accessible derivative được bỏ sót ngoài scope.
- **AT-UC-038-P:** Given request hợp lệ và lineage đầy đủ, When export/delete hoàn tất theo policy, Then chỉ subject scope được xuất/xóa, shared peers được bảo vệ và receipts/status đúng bản sao đã xử lý.
- **AT-UC-038-N:** Given requester thiếu authority, shared ownership chưa rõ hoặc provider backup còn pending, When xử lý, Then không lộ peer data/xóa toàn canvas/báo purge hoàn tất giả; ghi review/exception và safe next action.

### B20.3 Traceability đầy đủ FR001–FR066

Bảng có một dòng cho mỗi FR gốc. Một dòng có thể dẫn nhiều use case/AT khi requirement xuyên luồng; không tạo FR mới bằng các chi tiết `PROPOSED`. Phần B19/B21–B25 bổ sung state/field/contract/UI/privacy/NFR verification cho cùng case.

| Requirement | Detailed use case | Acceptance scenario chính | Điểm kiểm chứng |
|---|---|---|---|
| `FR001` | UC-001, UC-007, UC-034 | AT-UC-001-P, AT-UC-001-N, AT-UC-007-N, AT-UC-034-N | Verified principal và scope isolation, không tin role client |
| `FR002` | UC-007 | AT-UC-007-P, AT-UC-007-N | QR/mã + Teacher admission; duplicate/revoke denied |
| `FR003` | UC-008 | AT-UC-008-P, AT-UC-008-N | One/many participants trên device, context được bind |
| `FR004` | UC-002 | AT-UC-002-P, AT-UC-002-N | Class/profile/enrollment history và minimal identity |
| `FR005` | UC-001, UC-007, UC-034 | AT-UC-001-P, AT-UC-001-N, AT-UC-034-P | Adult verification, scoped grants/provision/revoke |
| `FR006` | UC-003 | AT-UC-003-P, AT-UC-003-N | Purpose grant/evidence; AI completion kiểm tra revoke |
| `FR007` | UC-004 | AT-UC-004-P, AT-UC-004-N | Session config/version, explicit Teacher Start, age/capacity guards |
| `FR008` | UC-005 | AT-UC-005-P, AT-UC-005-N | Membership/canvas scopes và stale grouping rejected |
| `FR009` | UC-009 | AT-UC-009-P, AT-UC-009-N | Group readiness không tự chuyển shared stage |
| `FR010` | UC-004, UC-010 | AT-UC-004-P, AT-UC-004-N, AT-UC-010-P, AT-UC-010-N | Teacher Start/control, checkpoint và truthful outcome |
| `FR011` | UC-011 | AT-UC-011-P, AT-UC-011-N | Completed chỉ sau durable save; recovery/idempotency |
| `FR012` | UC-012 | AT-UC-012-P, AT-UC-012-N | Move/leave giữ contribution, revoke old grant |
| `FR013` | UC-010 | AT-UC-010-N | TBD return-stage gate; UI back không tự transition |
| `FR014` | UC-013 | AT-UC-013-P, AT-UC-013-N | Personal/shared/region canvas và accepted operations |
| `FR015` | UC-013 | AT-UC-013-P, AT-UC-013-N | Age/Teacher tool policy enforced server-side |
| `FR016` | UC-014 | AT-UC-014-P, AT-UC-014-N | Help/region locks/restore có quyền và history |
| `FR017` | UC-016 | AT-UC-016-P, AT-UC-016-N | Reconnect/gap/replay giữ accepted contribution |
| `FR018` | UC-015 | AT-UC-015-P, AT-UC-015-N | Scoped compensation, không undo peer tùy tiện |
| `FR019` | UC-017 | AT-UC-017-P, AT-UC-017-N | AI overlay riêng, child-only view khi approved capability |
| `FR020` | UC-013 | AT-UC-013-N | TBD import extensions không tự trở thành core |
| `FR021` | UC-015 | AT-UC-015-P, AT-UC-015-N | Replay và advanced tools theo age policy đã duyệt |
| `FR022` | UC-018 | AT-UC-018-P, AT-UC-018-N | Snapshot/context/topic/age/source pinned |
| `FR023` | UC-018 | AT-UC-018-P, AT-UC-018-N | Candidate/uncertainty riêng confirmed meaning |
| `FR024` | UC-019 | AT-UC-019-P, AT-UC-019-N | Explicit/manual request và cancellation |
| `FR025` | UC-019, UC-021 | AT-UC-019-P, AT-UC-021-P | Support mode/level theo approved policy |
| `FR026` | UC-020 | AT-UC-020-P, AT-UC-020-N | Per-item Teacher review exact version cho pilot |
| `FR027` | UC-021 | AT-UC-021-P, AT-UC-021-N | Child view/hide/decline và quyền tiếp tục vẽ |
| `FR028` | UC-017 | AT-UC-017-P, AT-UC-017-N | AI không replace strokes/diagnose từ idle |
| `FR029` | UC-020 | AT-UC-020-P, AT-UC-020-N | Moderation blocking/typed failures/redacted notice |
| `FR030` | UC-019 | AT-UC-019-P, AT-UC-019-N | Dedup/budget/cache/stale không bypass approval |
| `FR031` | UC-022 | AT-UC-022-P, AT-UC-022-N | Teacher gallery/order/annotate/present snapshots |
| `FR032` | UC-022 | AT-UC-022-P, AT-UC-022-N | Child explanation theo approved format, không tự thu mic |
| `FR033` | UC-022 | AT-UC-022-P, AT-UC-022-N | Versioned share đúng class/session/audience |
| `FR034` | UC-023 | AT-UC-023-P, AT-UC-023-N | Library/render scope lớp/child và provenance |
| `FR035` | UC-023 | AT-UC-023-P, AT-UC-023-N | Knowledge factual sources, không imagined facts |
| `FR036` | UC-024 | AT-UC-024-P, AT-UC-024-N | Exact-video approval và explicit playback |
| `FR037` | UC-025, UC-024, UC-026 | AT-UC-025-P, AT-UC-025-N, AT-UC-024-P, AT-UC-026-P | Status/readiness/review/play/failure rõ |
| `FR038` | UC-025 | AT-UC-025-P, AT-UC-025-N | Generating waits, no auto fallback/skip |
| `FR039` | UC-026 | AT-UC-026-P, AT-UC-026-N | Teacher explicit retry/skip/end exhausted failure |
| `FR040` | UC-023, UC-024 | AT-UC-023-P, AT-UC-023-N, AT-UC-024-N | Script/source/media versions, edit invalidates review |
| `FR041` | UC-027 | AT-UC-027-P, AT-UC-027-N | Teacher chọn/chỉnh class/group recommendation |
| `FR042` | UC-027 | AT-UC-027-P | Activity fields/source/version theo dictionary B21 |
| `FR043` | UC-027 | AT-UC-027-P, AT-UC-027-N | Material/safety confirmation trước start |
| `FR044` | UC-028 | AT-UC-028-P, AT-UC-028-N | Off-screen/reflection evidence và truthful outcomes |
| `FR045` | UC-029 | AT-UC-029-P, AT-UC-029-N | Age/process/evidence và Teacher judgement |
| `FR046` | UC-031 | AT-UC-031-P, AT-UC-031-N | Within-child progress, không rank peers |
| `FR047` | UC-030 | AT-UC-030-P, AT-UC-030-N | Session/process/AI/content/reflection portfolio lineage |
| `FR048` | UC-031 | AT-UC-031-P, AT-UC-031-N | Authorized reports/export, evidence taxonomy |
| `FR049` | UC-029 | AT-UC-029-P, AT-UC-029-N | Proposed rubric descriptive, OD10 gate |
| `FR050` | UC-029 | AT-UC-029-P, AT-UC-029-N | Chưa quan sát khác thiếu năng lực, prohibited inference |
| `FR051` | UC-032 | AT-UC-032-P, AT-UC-032-N | Authorized class live projections/control/queue |
| `FR052` | UC-033 | AT-UC-033-P, AT-UC-033-N | Preset reuse và Teacher override automation |
| `FR053` | UC-033 | AT-UC-033-P, AT-UC-033-N | Immutable preset/effective config version |
| `FR054` | UC-032, UC-033 | AT-UC-032-P, AT-UC-032-N, AT-UC-033-P | Queue priority/overload/action audit |
| `FR055` | UC-034 | AT-UC-034-P, AT-UC-034-N | Accounts/roles/classes/session metadata administration |
| `FR056` | UC-035, UC-036 | AT-UC-035-P, AT-UC-035-N, AT-UC-036-P, AT-UC-036-N | Content lifecycle và AI config governed versions |
| `FR057` | UC-037 | AT-UC-037-P, AT-UC-037-N | Monitoring/reports/consent/audit/incidents scoped |
| `FR058` | UC-034, UC-037 | AT-UC-034-N, AT-UC-037-N | Admin raw data cần specific purpose/grant |
| `FR059` | UC-038, UC-003, UC-001 | AT-UC-038-P, AT-UC-038-N, AT-UC-003-N, AT-UC-001-N | Access/consent/retention/export/delete/audit lifecycle |
| `FR060` | UC-016, UC-011 | AT-UC-016-P, AT-UC-016-N, AT-UC-011-N | Durable checkpoint/draft/recovery/save failure |
| `FR061` | UC-020, UC-018 | AT-UC-020-P, AT-UC-020-N, AT-UC-018-P | Correction, unsafe block và pending content gate |
| `FR062` | UC-035 | AT-UC-035-P, AT-UC-035-N | Recalled version bị loại khỏi new session |
| `FR063` | UC-016 | AT-UC-016-P, AT-UC-016-N | Proposed Teacher-offline rules; approval actions wait |
| `FR064` | UC-038 | AT-UC-038-P, AT-UC-038-N | Copies/backups/shared peer deletion/retained audit |
| `FR065` | UC-006 | AT-UC-006-P, AT-UC-006-N | Phase 2 grouping proposal và Teacher final commit |
| `FR066` | UC-008 | AT-UC-008-P, AT-UC-008-N | Selected contributor/turn riêng verified principal |

### B20.4 Cách sử dụng để lập feature và nghiệm thu

Use case là hợp đồng hành vi để tách feature, không gán mỗi use case một service hoặc một người. Một vertical slice phải chứng minh đường thành công và đường từ chối/recovery có liên quan qua domain/contract/adapters và thiết bị. AT trong B20 cần kết hợp negative/concurrency/state fixtures ở B19/B22 và profile đo ở B25; không dùng ảnh chụp UI thay bằng chứng authorization/persistence. Trước triển khai case có TBD, owner cần chốt decision liên quan và cập nhật FR/policy/version; trước phần có PROPOSED, feature plan/approval phải ghi rõ chi tiết nào được adopt. UC01–UC13 ở B14 là luồng tóm tắt; UC-001–UC-038 ở B20 là danh mục chi tiết riêng, không tự thay ID cũ trong evidence.
