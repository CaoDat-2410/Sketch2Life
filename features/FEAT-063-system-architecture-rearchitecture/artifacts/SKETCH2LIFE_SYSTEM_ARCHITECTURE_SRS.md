# Sketch2Life — Đặc tả yêu cầu phần mềm (SRS) và Kiến trúc đích

**Feature:** FEAT-063 — Thiết kế lại kiến trúc toàn repository  
**Trạng thái tài liệu:** Bản nháp v2.3 để chủ sở hữu rà soát; giữ baseline Parent/Teacher và pipeline video, bổ sung lesson platform, school tenancy, profile sharing có thể thu hồi, quản trị nội dung và quota đa scope (Q147–Q195)  
**Phiên bản:** 2.3-draft  
**Cập nhật:** 2026-10-28  
**Tài liệu kèm theo:** [DATA_TABLE_REGISTER.md](DATA_TABLE_REGISTER.md)  
**Cổng rà soát:** Đây là bản Markdown để xem xét. Chỉ tạo diagram conceptual/logical cuối và PDF sau khi chủ sở hữu duyệt cả hai tài liệu Markdown.

### Kiểm soát tài liệu

| Phiên bản | Ngày | Người biên soạn | Thay đổi | Trạng thái/phê duyệt |
|---|---|---|---|---|
| 1.5-draft | 2026-10-27 | Nhóm FEAT-063 (bản tổng hợp) | Baseline trước vòng phản biện này; các quyết định Q01–Q133 đã được ghi nhận. | Bản nháp; chưa có chữ ký duyệt |
| 1.6-draft | 2026-10-27 | Nhóm FEAT-063 (bản tổng hợp) | Hòa giải quyền Teacher khi đổi phân công, ownership quota và cost-cap, run idle/retention, push, upload-resume, truy vết từng ID, persona, yêu cầu đo được và cổng tuân thủ theo phản biện v1.5. | Bản nháp trước review v1.6 |
| 1.7-draft | 2026-10-27 | Nhóm FEAT-063 (bản tổng hợp) | Chốt current owner/force-close, DRAFT/admission state, verified-email reminder, upload session/part tables, 4 MiB PutObject chunks, deadline/rate limit, error mapping và traceability theo ID. | Chờ chủ sở hữu duyệt Markdown; chưa có sign-off |
| 1.8-draft | 2026-10-27 | Nhóm FEAT-063 (bản tổng hợp) | Bổ sung AI Sketch chỉ cho Teacher, deck trình chiếu theo occurrence và chuẩn hóa pipeline story-video theo đề xuất LTX-2.5/Modal của chủ sở hữu; bổ sung Lesson deck revision/step entities. | Bản nháp đang chờ chủ sở hữu rà soát; chưa có sign-off |
| 1.9-draft | 2026-10-27 | Nhóm FEAT-063 (bản tổng hợp) | Mở rộng pipeline video theo đầy đủ giai đoạn VLM, story/storyboard, Character Bible, LTX-2.5 theo scene, consistency, ghép hình, lời kể/phụ đề và safety; làm rõ AI job đa mục tiêu cho lesson sketch và story run; thống nhất số bảng cuối cùng và truy vết. | Bản nháp đang chờ chủ sở hữu rà soát; chưa có sign-off |
| 2.0-draft | 2026-10-27 | Nhóm FEAT-063 (bản tổng hợp) | Kiểm toán lại 86 source mappings và data graph; gỡ bốn bảng helper/snapshot bị trùng, gộp context snapshot có giới hạn vào run input, chuyển output asset refs về Story/Lesson aggregate, chuẩn hóa profile context và media field ownership, bổ sung relationship catalogue cùng phép đếm mới. | Bản nháp đang chờ chủ sở hữu rà soát; chưa có sign-off |
| 2.1-draft | 2026-10-28 | Nhóm FEAT-063 (bản tổng hợp) | Bổ sung gợi ý ý tưởng sketch dạng chữ, tùy chọn cho Parent trước khi vẽ; làm rõ đây không phải Teacher AI Sketch Deck, không tạo tranh mẫu và không đổi thứ tự chụp-trước/xác nhận-chủ-thể-sau. Ghi nhận Q145; đề xuất khả năng AI tạo line-sketch được để mở ở Q146. | Bản nháp đang chờ chủ sở hữu rà soát; chưa có sign-off |
| 2.2-draft | 2026-10-28 | Nhóm FEAT-063 (bản tổng hợp) | Theo làm rõ Q146, thay gợi ý chữ tĩnh tạm thời bằng line-sketch AI 3–5 bước tùy chọn cho Parent; thêm target/job, asset provenance/expiry, output safety và compute/rate accounting riêng. Teacher AI Sketch Deck vẫn là bước chính trong luồng Teacher. | Bản nháp đang chờ chủ sở hữu rà soát; chưa có sign-off |
| 2.3-draft | 2026-10-28 | Nhóm FEAT-063 (bản tổng hợp) | Bổ sung lớp nền tảng lesson dùng lại, tổ chức trường, quyền Admin/Manager/Teacher/Parent, profile share có invitation/revoke, upload giáo án qua bộ lọc, Parent lesson history/feedback, quota theo scope và giới hạn tuổi 3–10. Giữ luồng Parent/Teacher và pipeline video; line-sketch chỉ sinh trong session khi người lớn bật. Bản v2.2 được lưu nguyên trạng để tra cứu lịch sử. | Bản nháp đang chờ chủ sở hữu rà soát; chưa có sign-off |

| Vai trò sign-off | Người ký | Trạng thái |
|---|---|---|
| Chủ sở hữu sản phẩm | Chưa ghi nhận | Chờ duyệt SRS và DATA_TABLE_REGISTER.md |
| Kiến trúc/engineering | Chưa chỉ định | Cần review trước implementation plan |
| Privacy/legal/commercial | Chưa chỉ định | Cần review trước dữ liệu trẻ thật hoặc thu phí production |

## Mục lục

1. [Mục đích và quyết định chính](#srs-1)
   - [Phạm vi và cấu trúc tài liệu](#srs-1-document)
2. [Phạm vi](#srs-2)
   - [Stakeholder, bối cảnh hệ thống và người dùng](#srs-2-context)
3. [Tác nhân và phân quyền](#srs-3)
4. [Quy tắc nghiệp vụ](#srs-4)
5. [Luồng người dùng](#srs-5)
6. [Vòng đời story và video](#srs-6)
7. [Yêu cầu chức năng](#srs-7)
8. [Yêu cầu phi chức năng](#srs-8)
   - [Ưu tiên, verification và phân pha](#srs-8-delivery)
9. [Kiến trúc phần mềm đích](#srs-9)
10. [Bảo mật, giám sát và giới hạn tốc độ](#srs-10)
11. [Kiến trúc dữ liệu và bất biến](#srs-11)
12. [Kiểm kê nguồn, migration và chuyển đổi](#srs-12)
13. [Tiêu chí chấp nhận kiến trúc](#srs-13)
14. [Quyết định và cổng triển khai](#srs-14)
15. [Nguồn và mức độ tin cậy](#srs-15)
16. [Truy vết quyết định của chủ sở hữu](#srs-16)
17. [Truy vết yêu cầu tới kiến trúc](#srs-17)
18. [Thuật ngữ, giả định và ràng buộc hệ thống](#srs-18)
19. [Ca sử dụng chi tiết và các luồng thay thế](#srs-19)
20. [Ma trận phân quyền](#srs-20)
21. [API và tương tác client](#srs-21)
22. [Job bất đồng bộ và xử lý event](#srs-22)
23. [Chi tiết vòng đời billing](#srs-23)
24. [Phân loại dữ liệu và xử lý media](#srs-24)
25. [Yêu cầu môi trường và triển khai](#srs-25)
26. [Monitoring, cảnh báo và mục tiêu vận hành](#srs-26)
27. [Runbook vận hành](#srs-27)
28. [Chiến lược xác minh và kịch bản rà soát](#srs-28)
29. [Danh mục rủi ro và cổng triển khai](#srs-29)
30. [Truy vết mở rộng](#srs-30)
   - [Ánh xạ use case tới requirement](#srs-30-1)
   - [Ánh xạ requirement tới entity đích](#srs-30-2)
   - [Ma trận truy vết FR/NFR theo từng ID](#srs-30-3)
   - [Ma trận truy vết BR theo từng ID](#srs-30-4)
31. [Nền tảng giáo án, chia sẻ và tích hợp luồng hiện hữu](#srs-31)

<a id="srs-1"></a>
## 1. Mục đích và quyết định chính

Sketch2Life giữ hai luồng sản phẩm Parent và Teacher, nay được đặt trên một lớp nền tảng giáo án dùng chung:

1. **Phụ huynh:** ứng dụng Android; người lớn dùng giáo án public hoặc giáo án được chia sẻ hợp lệ, có thể bật/tắt line-sketch gợi ý trong lúc vẽ, chụp tranh, xác nhận/sửa chủ thể sau VLM, duyệt kịch bản và tạo video mới từ chính tranh của con. Sau video, ứng dụng hiển thị một hoặc nhiều hoạt động ngoài trời đã cấu hình trong giáo án.
2. **Giáo viên:** ứng dụng web; trường là một tổ chức quản lý lớp và hồ sơ. Teacher có thể tạo giáo án dạng preset hoặc dùng giáo án được chia sẻ; khi upload, nội dung được lọc thành trường dữ liệu cho phép và Teacher xem/sửa trước khi AI hỗ trợ. Trong buổi học, Teacher chỉ sinh line-sketch nếu bật tùy chọn; luồng video mẫu hiện có vẫn chọn một trẻ đại diện ngẫu nhiên đủ điều kiện và tạo video mới từ tranh của trẻ đó.

Mỗi story run gắn chính xác với một trẻ. Tài khoản Parent và Teacher vẫn tách biệt; hồ sơ trẻ có thể được chia sẻ qua lời mời và quyền có phạm vi, có thể thu hồi, không hợp nhất hai tài khoản hoặc biến Parent thành thành viên tổ chức. Mỗi trường là một organization/tenant. Không có runtime cộng tác lớp học, canvas vẽ dùng chung, QR/lobby/admission, xử lý nhiều trẻ theo lô hoặc hoạt ảnh tranh bằng PixiJS.

Cổng duyệt duy nhất trước khi gọi tạo video là người lớn xác nhận revision cuối của kịch bản/storyboard. Transcript, chủ thể và context hồ sơ được xem xét/xác nhận theo role trước story. Parent không chọn hoặc xác nhận activity làm tiền điều kiện story/video. Teacher sample vẫn ghim đúng một activity đã duyệt; lesson/plan được duyệt theo luồng Teacher. Video hoàn chỉnh được hiển thị sau khi qua kiểm tra kỹ thuật và safety gate tự động; không có bước duyệt video cuối. Nếu người lớn đánh dấu video không phù hợp, video cũ bị ẩn khỏi playback ngay khi yêu cầu tạo lại được chấp nhận; run quay lại bước duyệt kịch bản. Bản cũ được giữ nội bộ cho đến khi xóa run.

### 1.1 Số lượng bảng đích

Mô hình đích v2.3 đề xuất có **89 bảng đang hoạt động**: giữ/tái cấu trúc 38 bảng nguồn và thêm 51 bảng mới. Bốn helper/snapshot table bị loại khỏi mô hình active vì dữ liệu đã có owner chuẩn; 13 mapping AI Policy provider-copy/resource receipt vẫn được giữ vật lý ở trạng thái legacy/read-only. Có **48 bảng nguồn legacy/read-only**; tổng physical dự kiến là **137** theo 86 mapping repository. Năm fixture bị loại khỏi phép tính. Đây là phép tính source-declared, không phải introspection database.

| Hạng mục | Số lượng | Ý nghĩa |
|---|---:|---|
| Bảng production khai báo trong nguồn hiện tại | 86 | Mapping SQLAlchemy/Core trong danh mục module hiện tại |
| Bảng fixture chỉ dùng cho test | 5 | Không phải bảng production; loại khỏi mọi phép tính |
| Bảng hiện có được giữ lại/chuẩn hóa | 38 | Bảng hiện tại vẫn cần cho sản phẩm và nền tảng đích |
| Bảng mới trong mô hình đích | 51 | Dữ liệu Parent/profile, lesson library/sharing/feedback, Sketch Deck, Story, quota/billing, notification, upload, asset và AI job |
| Tổng bảng đang hoạt động | **89** | 38 + 51 |
| Bảng legacy chỉ đọc | 48 | Gồm 35 workflow cũ và 13 AI Policy deferred; giữ nguyên tại chỗ |
| Bảng production vật lý sau chuyển đổi schema đích | **137** | 89 active + 48 legacy |

Rev31 implementation crosswalk: the backend adds three Lesson-owned support tables beyond the v2.3 draft. The current source-derived implementation target is 92 active + 48 legacy/read-only = 140 projected physical mappings. Neither count is a live database observation; this note does not sign off the SRS. See Data Table Register section 14.4.

DATA_TABLE_REGISTER.md ghi disposition của nguồn, tên bảng đích, chủ sở hữu dữ liệu và ràng buộc. Thiết kế này không drop bảng và không sao chép dữ liệu sang một kho archive thứ hai.

### 1.2 Trạng thái quyết định

The v2.3-draft model contains 89 active tables (38 retained/refactored + 51 new) and 137 projected physical tables (plus 48 legacy); no live database was inspected. Rev31 adds three Lesson support tables, making the current source-derived implementation crosswalk 92 active + 48 legacy/read-only = 140 projected physical. Neither count is a database result.

<a id="srs-1-document"></a>
### 1.3 Phạm vi và cấu trúc tài liệu

Đây là package Markdown tổng hợp SRS, kiến trúc đích (SAD-level), vận hành và chiến lược xác minh theo yêu cầu owner muốn duyệt một baseline đầy đủ cùng data register. Requirement quy phạm nằm ở BR/FR/NFR; công nghệ, entity, API, job/ops ở các mục tương ứng phải được đọc theo trạng thái `proposed`/`gate`, không phải implementation fact. Sau khi owner duyệt nội dung có thể tách các chương kiến trúc, runbook và test strategy thành file riêng nhưng giữ nguyên ID/traceability; hiện chưa chia file để tránh lệch nhiều bản nguồn.

Tài liệu tham khảo về yêu cầu được đối chiếu theo ISO/IEC/IEEE 29148:2018; IEEE 830-1998 là thực hành cũ đã được thay thế bởi 29148. Bản này dùng cấu trúc và thuộc tính requirement làm hướng dẫn, không tuyên bố chứng nhận tuân thủ đầy đủ chuẩn. Phần visual diagrams chưa có trong Markdown vì owner yêu cầu chỉ tạo sau khi duyệt SRS và register.

<a id="srs-2"></a>
## 2. Phạm vi

### 2.1 Trong phạm vi

- Khôi phục/chuyển luồng Phụ huynh cũ sang nền tảng Android hiện tại.
- Giữ luồng Phụ huynh Android, luồng Giáo viên web và pipeline tạo ảnh/video đã có; lớp nền tảng lesson, nội dung và phân quyền là phần bổ sung kiến trúc.
- Tách tài khoản Parent và Teacher; hỗ trợ chia sẻ hồ sơ trẻ bằng invitation, phạm vi quyền tối thiểu, consent, audit và revoke.
- Mỗi trường là một organization/tenant; tách quyền platform Admin, school Manager, Teacher và Parent.
- Thư viện lesson tái sử dụng dạng preset, có version và visibility private/school/selected/public; lesson content độc lập với occurrence dạy thực tế.
- Teacher authoring form và template upload chuẩn hóa; giữ file gốc riêng tư, lọc/extract allowlist trước AI, Teacher xem/sửa bản structured trước khi dùng.
- Teacher/Manager có thể tạo hoặc duyệt lesson draft theo quyền được chốt; Parent dùng public/được chia sẻ, có thể sửa personal copy nhưng không sửa nguồn gốc đã publish.
- Parent có thể xem lesson đã dạy cho profile được chia sẻ trong thời hạn lịch sử được cấu hình, tải lesson được cấp quyền và gửi feedback; không có chat, completion toggle hay upload tranh lên feedback.
- Phạm vi tuổi child là 3–10 (36–120 tháng); age-band con cụ thể cần cấu hình/version và đang để mở.
- Một lesson occurrence cho mỗi buổi dạy và tối đa một video mẫu thành công cho occurrence đó; mỗi run chỉ chọn đúng một trẻ.
- Teacher AI Sketch Deck và Parent line-sketch guide chỉ sinh trong session khi người lớn bật; nếu tắt thì không tạo job. Deck vẫn là bề mặt trình chiếu nền trắng; trẻ vẽ bằng giấy/bút.
- Parent có thể tùy chọn bật line-sketch AI 3–5 bước cho topic chung/độ khó đơn giản trong drawing session; có thể bỏ qua mà không đổi luồng chính. Guide không phải tranh hoàn chỉnh của trẻ, không dùng dữ liệu trẻ làm input, và không phải Teacher AI Sketch Deck.
- Video storytelling từ tranh trẻ theo pipeline VLM hiểu ảnh → LLM tạo story có cấu trúc → storyboard → người lớn duyệt/xác nhận script → chuẩn bị Character Bible và ảnh tham chiếu → LTX-2.5 trên Modal theo scene → kiểm consistency → FFmpeg ghép scene → tạo/đồng bộ TTS và phụ đề → safety tự động → playback riêng trong run.
- Chụp bằng camera/tải ảnh lên, ý tưởng bằng chữ/giọng nói, xem và sửa transcript Whisper, nhận diện/chỉnh chủ thể, tạo story cá nhân hóa, duyệt kịch bản, tạo video mới từ ảnh rồi hiển thị các hoạt động ngoài trời đã cấu hình trong lesson.
- Revision hồ sơ, snapshot context được duyệt cho từng run, provenance, lifecycle xóa và ràng buộc chỉ dùng dữ liệu tổng hợp cho demo.
- Kiểm kê bảng nguồn toàn repository và thiết kế dữ liệu đích không phá hủy dữ liệu hiện có.
- Clean architecture, contract có version, mã lỗi chuẩn hóa, monitoring, rate limit, vận hành Docker local và inference model qua Modal.
- Capacity tổ chức gồm 10 slot lớp trong gói cơ bản trả phí; mua thêm theo đơn giá/slot bằng MoMo/VNPAY ở adapter ban đầu.
- Quota video theo gói cho school organization, Teacher account và Parent account; Billing sở hữu grant/usage. Manager có thể mua/đặt quota school; Parent có gói và add-on riêng.

### 2.2 Ngoài phạm vi

- Session cộng tác lớp học, QR, lobby/admission, nhiều trẻ trong một run, canvas nhóm, vẽ dùng chung hoặc tiến trình theo stage cộng tác.
- Hoạt ảnh tranh bằng PixiJS.
- Teacher AI Sketch Deck trong luồng Parent; chọn trước chủ thể của tranh trẻ trước khi chụp. Parent AI line-sketch guide là một tùy chọn riêng, không lấy dữ liệu trẻ làm input và không chặn capture.
- Xuất deck ra PPTX/PDF hoặc dùng slide như công cụ vẽ cộng tác trên thiết bị; deck Teacher chỉ là bề mặt trình chiếu trong ứng dụng/web.
- Hợp nhất danh tính Parent/Teacher thành một tài khoản; chia sẻ hồ sơ trong gia đình ngoài luồng grant được định nghĩa; dùng chung tài khoản Parent/Teacher.
- OCR trang scan giáo án, trích ảnh thành nội dung lesson, Phụ huynh gửi hoạt động riêng hoặc sửa trực tiếp từng scene do AI tạo.
- Duyệt video cuối, tải/xuất file từ sản phẩm, chia sẻ video, gallery công khai, xếp hạng/so sánh trẻ.
- Chốt host/region production, email provider production, SLO/địa chỉ cảnh báo production, mức giá thương mại cụ thể, revision model/weights AI cụ thể hoặc thông tin thanh toán đang hoạt động.
- Dọn schema phá hủy, chạy migration, triển khai code, chạy build/test sản phẩm, dùng dữ liệu trẻ thật, thanh toán bên ngoài đang hoạt động hoặc gọi provider/Modal thật.

<a id="srs-2-context"></a>
### 2.3 Stakeholder, bối cảnh hệ thống và người dùng

| Stakeholder | Mối quan tâm/chịu trách nhiệm | Thông tin cần được cung cấp |
|---|---|---|
| Chủ sở hữu sản phẩm | Phạm vi, trải nghiệm, quy tắc một trẻ/một run, nội dung được duyệt | Luồng Parent/Teacher, quota, trạng thái, acceptance criteria |
| Admin nền tảng | Platform-wide roles, public lesson library, moderation/hide và quota policy | Audit, provenance, review/publish state và quyền truy cập rõ ràng |
| School Manager | Một organization/trường, member groups, quota, review public lesson và feedback trong trường | Quyền theo tenant, lịch sử duyệt và phản hồi; media không mặc định |
| Phụ huynh/người giám hộ | Hồ sơ trẻ, consent chia sẻ, lesson dùng với con, video cá nhân và feedback | Trạng thái/revoke grant, quota, lịch sử lesson có giới hạn và thông báo |
| Giáo viên phụ trách | Reusable lesson, occurrence, một trẻ mẫu, sketch tùy chọn và feedback Parent | Upload đã lọc, profile scope được share và quyền lớp hiện hành |
| Quản trị nội dung | Lesson library và chính sách an toàn dùng chung | Revision, nguồn, trạng thái review/publish/hide và lịch sử thu hồi |
| Vận hành/kỹ thuật | Sức khỏe dịch vụ, queue, model/provider, chi phí và phục hồi | Metrics đã redact, correlation ID, runbook, giới hạn/circuit breaker |
| Privacy/legal/commercial reviewer | Dữ liệu trẻ, vai trò controller/processor, transfer, retention, payment/tax | Evidence và quyết định phê duyệt production; chưa được coi là hoàn thành |

**Người dùng mục tiêu và môi trường:** Parent là người lớn dùng điện thoại Android, có thể không quen thuật ngữ AI; Teacher mầm non thao tác trên máy tính/laptop qua trình duyệt trong thời gian chuẩn bị buổi học; Admin tổ chức dùng web với quyền billing/roster tách biệt. V1 dùng tiếng Việt. Nếu camera/micro bị từ chối hoặc không sẵn sàng, phải có upload ảnh và nhập chữ thay thế. Repo hiện khai báo `minSdk 29` (Android 10), `targetSdk 36`, `compileSdk 37`; browser target là hai phiên bản stable gần nhất của Chrome/Edge desktop và phải được xác minh lại trong release gate.

**Bối cảnh tích hợp bằng văn bản** (diagram vẫn để sau khi duyệt Markdown):

| Thành phần/hệ thống ngoài | Giao tiếp | Dữ liệu và ranh giới | Điều kiện |
|---|---|---|---|
| Parent Android và Teacher Web | HTTPS tới API versioned `/v1`; Firebase ID token | Chỉ command/asset upload/trạng thái; không có credential DB, MinIO, payment hoặc Modal | Backend xác minh token và quyền từng resource |
| Firebase Authentication | Client/backend xác thực identity | Issuer/UID; không lưu profile, media, notification hoặc dữ liệu sản phẩm | Repository chỉ cho phép Firebase Authentication |
| Modal | Backend worker gọi bất đồng bộ; reference nhỏ và file qua scratch cô lập | Input/output giới hạn theo job, checksum, xóa scratch sau xử lý | Synthetic-only; review region/transfer trước dữ liệu thật |
| MoMo/VNPAY | Callback provider về backend; redirect client chỉ hiển thị trạng thái | Payload ký, provider event ID, invoice/payment refs | Signature, replay protection, dedupe và reconciliation qua sandbox |
| Notifications | Inbox, email, Web Push, Android adapter | Payload tối thiểu/opaque reference; không có child name/media/story | Android delivery là POC gate; không dùng Firebase Messaging |
| PostgreSQL/Redis-RQ/MinIO | Internal Docker network | DB nguồn chuẩn; Redis dispatch/rate-limit; object storage riêng tư | Local synthetic; backup/restore thủ công |
| OTel/Prometheus/Grafana/Mailpit | Internal telemetry/development | Log/metrics đã redact; Mailpit local | Production destinations và retention chưa chọn |

| Nhóm người dùng | Thiết bị/kỹ năng giả định | Nhu cầu và accessibility |
|---|---|---|
| Parent | Android, cảm ứng, kỹ năng số cơ bản | Chọn lesson, bật/tắt guide, vẽ/chụp, xác nhận subject/script, xem video rồi hoạt động; lỗi có hành động kế tiếp |
| Teacher | Chrome/Edge desktop, bàn phím/chuột, thao tác nhanh | Import/review lesson, chọn profile/activity, chụp hoặc nhận ảnh upload, chiếu mẫu sau xác nhận |
| School Manager | Web desktop, kỹ năng tổ chức/quota | Quản lý nhóm, phân công, duyệt public và quota; không xem media mặc định |
| Platform Admin | Web desktop, quyền vận hành nền tảng | Soạn/duyệt/public/hide lesson, quản lý permission và quota; media access có audit |

<a id="srs-3"></a>
## 3. Tác nhân và phân quyền

| Tác nhân | Quyền hạn | Giới hạn |
|---|---|---|
| Platform Admin | Quản trị role/permission toàn nền tảng; author/review/publish lesson public; xem, trả lời feedback school-scoped; ẩn hoặc thu hồi nội dung khi cần; có thể truy cập media trẻ theo quyền nền tảng đã audit | Không được bỏ qua audit, privacy policy hoặc lifecycle; không cấp quyền chéo organization cho Manager/Teacher/Parent. |
| School Manager | Quản lý một organization (một trường), Teacher/Parent groups, quota school, xem và duyệt Teacher lesson trước public; xem và phản hồi feedback thuộc trường | Không được thấy dữ liệu/media của organization khác; role quản lý roster không mặc nhiên cấp media trẻ. |
| Phụ huynh (Parent) | Sở hữu tài khoản và hồ sơ Parent; tạo run; dùng lesson public/được chia sẻ; xem lesson đã dạy cho child profile liên kết; gửi feedback/trả lời trong feedback thread; quản lý và thu hồi grant; xem video | Không vào organization/roster; không xem profile Teacher ngoài field đã share; không có chat, completion toggle, upload tranh feedback hoặc sửa trực tiếp scene AI. |
| Giáo viên phụ trách (Teacher) | Vận hành lớp được giao; author/edit lesson, dùng preset tùy chọn; quản lý profile được giao; upload/review giáo án đã lọc; chuẩn bị occurrence; bật/tắt line-sketch; chọn một trẻ đại diện và tạo video mẫu mới; xử lý feedback của lớp | Quyền run/profile theo phân công và grant đang hiệu lực; khi revoke/reassignment, quyền bị thu hồi ngay. Không xử lý nhiều trẻ theo một run. |
| Quản trị nội dung | Review nội dung/catalog theo permission được cấp | Không có quyền nhận media riêng tư nếu không có role/grant riêng. |
| Vận hành hệ thống | Vận hành dịch vụ local, giám sát sức khỏe, khôi phục backup và cấu hình secret provider | Telemetry vận hành không để lộ nội dung trẻ. Quyền truy cập dịch vụ production cần chính sách được xem xét riêng. |
| Adapter AI provider | Nhận input được cho phép của đúng một run và trả kết quả có kiểu/version | Chỉ chạy ở backend; không nhận danh sách trẻ, trường hồ sơ bị ẩn, credential tài khoản hoặc quyền truy cập storage không giới hạn. |

Xác thực chỉ dùng Firebase Authentication. Backend xác minh ID token và suy ra danh tính actor; mỗi lần đọc/ghi resource phải kiểm tra tiếp role, tổ chức, phân công lớp, quyền sở hữu hồ sơ và actor của run. Không dùng Firebase Storage, Firestore hoặc Realtime Database.

Tài khoản Parent và Teacher bắt buộc tách biệt, kể cả khi một người lớn đảm nhiệm cả hai vai. Parent có thể mời một Teacher phụ trách/trường chia sẻ các trường hồ sơ được chọn; grant ghi bên cấp/nhận, scope, purpose, status, thời hạn và revoke, và không đổi owner của profile. Mỗi trường là một tenant; mọi lesson, feedback và member group được kiểm tra theo organization. Mỗi hồ sơ Teacher tối đa một enrollment lớp active; profile cross-role resolve chỉ qua contract/grant versioned.

<a id="srs-4"></a>
## 4. Quy tắc nghiệp vụ

BR-01 đến BR-46 ghi lại baseline sản phẩm/an toàn; BR-47 đến BR-60 bổ sung các quy tắc platform v2.3 và các override được chủ sở hữu yêu cầu. Quy tắc lịch sử mâu thuẫn được giữ để truy vết nhưng nhường cho nội dung mới tại §31.

| ID | Quy tắc nghiệp vụ |
|---|---|
| BR-01 | Một story run phải gắn chính xác một hồ sơ trẻ. Request và job contract chỉ lưu một profile ref scalar; từ chối nhiều trẻ, batch và context nhóm. |
| BR-02 | Mỗi tài khoản người lớn có tối đa một story run chưa kết thúc. Khóa gắn với owner hiện hành (`active_owner_parent_account_id` hoặc `active_owner_teacher_id`), tách khỏi `created_by_actor_ref` bất biến. Parent khóa theo tài khoản Parent; Teacher khóa theo giáo viên đang phụ trách. |
| BR-03 | Parent và Teacher có account scope và lịch sử hồ sơ riêng; một Parent có thể mời Teacher/trường chia sẻ profile qua grant có purpose/scope/revoke. Principal và profile không tự hợp nhất; role claim từ client không cấp quyền. |
| BR-04 | Lớp và hồ sơ trẻ Teacher thuộc tổ chức. Mỗi tổ chức có 10 slot lớp trong gói cơ bản trả phí. Capacity bổ sung mua theo một đơn giá/slot cấu hình được, theo tháng hoặc năm; không chia nhiều tier. Giá cụ thể thuộc cấu hình thương mại. |
| BR-05 | Admin tổ chức phân công một Teacher phụ trách mỗi lớp. Một Teacher có thể phụ trách nhiều lớp. Mỗi hồ sơ trẻ tối đa một enrollment lớp đang hoạt động. |
| BR-06 | BE1 là nguồn chuẩn phân công hiện tại. Reassignment dùng workflow bền vững hai owner BE1/Story: đưa lớp vào transfer-pending/read-only, fence quyền và token cũ ngay, chuyển active-run owner/lock qua Story port rồi mới finalize Teacher mới; trong lúc pending không mở nội dung cho Teacher nào. `created_by_actor_ref` chỉ là provenance. Nếu Teacher mới có run active, Story từ chối chuyển lock và saga bù BE1 về assignment cũ; nếu bù mơ hồ, transfer giữ pending/read-only để đối soát; không hủy AI job hợp lệ chỉ vì đổi Teacher. Output chỉ được nhận nếu input/script/hash/occurrence và assignment version còn hợp lệ; chỉ Teacher hiện tại được xem. Admin mặc định không xem media. Teacher phụ trách xác nhận có audit trước khi chiếu mẫu cho lớp; người xem không có tài khoản, playback capability dùng lại hoặc quyền export. |
| BR-07 | Teacher tạo/sửa hồ sơ trẻ bằng form nhập nhanh có cấu trúc, có thể nhập lại câu trả lời trên phiếu khảo sát phụ huynh. V1 không OCR hoặc import file phiếu. |
| BR-08 | Lesson version có thể cấu hình một hoặc nhiều hoạt động ngoài trời với vật liệu/cách làm/ghi chú. Parent xem activity list sau khi video sẵn sàng; Teacher occurrence giữ flow hoạt động riêng theo lesson. |
| BR-09 | Reusable lesson/version độc lập với occurrence. Occurrence pin lesson/version; video mẫu dùng đúng một trẻ/tranh; lesson activities hiển thị sau video, không phải điều kiện chọn trước cho Parent video. |
| BR-10 | Mỗi occurrence Teacher tạo tối đa một video mẫu có thể phát và đã qua kiểm tra an toàn, cho đúng một trẻ. Slot được claim nguyên tử tại video playable đầu tiên. Run lỗi kỹ thuật hoặc bị chặn an toàn trước lần claim đầu không chiếm slot. Sau khi claim, slot không mở lại khi video bị đánh dấu không phù hợp, bị ẩn, tạo lại thất bại/hết lượt, run bị xóa, hủy hoặc chuyển giáo viên; không có recovery run thứ hai cho occurrence đó. |
| BR-11 | Một run có một request tạo video đầy đủ ban đầu và tối đa hai request tạo lại về chất lượng. Mỗi request video đầy đủ được chấp nhận tiêu thụ một slot giới hạn của run và một unit quota, kể cả khi sau đó lỗi kỹ thuật hoặc safety block. Retry scene tự động không tiêu thụ thêm request/unit. Mỗi lần tạo lại vẫn ở cùng run và phải quay lại xác nhận revision kịch bản. |
| BR-12 | Video Teacher hoàn chỉnh, kể cả các lần tạo lại chất lượng, vẫn là video mẫu duy nhất của occurrence; tạo lại không cấp quyền chọn trẻ khác hoặc mở run mẫu độc lập thứ hai. |
| BR-13 | Mỗi story có một bản đầu và tối đa ba lần AI viết lại (tổng bốn revision story/run). Parent gửi gợi ý; Teacher có thể đặt thêm hướng kể từ giáo án/kế hoạch lớp. Người lớn không sửa trực tiếp scene do AI tạo. |
| BR-14 | Mỗi revision story mới phải được xem và xác nhận lại trước khi tạo video. UI hiển thị revision hiện hành; revision cũ giữ nội bộ đến khi xóa run. |
| BR-15 | Transcript, chủ thể, lesson/plan và snapshot context hồ sơ phải được xác nhận ở bước tiền điều kiện tương ứng. Parent không chọn activity trước video; Teacher sample vẫn ghim một activity đã duyệt. Cổng cuối trước video là xác nhận script/storyboard; không có duyệt video cuối riêng. |
| BR-16 | Video được hiển thị ngay khi tạo xong và qua kiểm tra kỹ thuật cùng safety gate tự động. Nếu người lớn đánh dấu video không phù hợp rồi yêu cầu tạo lại, ẩn video cũ khỏi playback ngay; giữ media nội bộ đến khi xóa run. Nếu lần tạo thay thế thất bại thì video cũ vẫn không được phát. Run quay lại bước xem script và phải xác nhận script trước lần tạo tiếp theo. |
| BR-17 | Mỗi scene có một lần thử ban đầu và tối đa hai lần retry kỹ thuật tự động. Hết retry thì run dừng và trả mã lỗi an toàn. Chỉ được mở run Teacher mới cho occurrence nếu chưa có video mẫu nào qua safety gate và phát được. Nếu video đầu đã claim slot, sau đó bị ẩn và cả hai lần tạo lại chất lượng thất bại/hết lượt thì run kết thúc lỗi; slot vẫn đã dùng và không có recovery run mới trong occurrence (Q127). |
| BR-18 | Hồ sơ Parent và Teacher dành cho trẻ 36–120 tháng (3–10 tuổi); lưu tuổi theo tháng và age band versioned, không lưu ngày sinh chính xác. Không gửi tên/tên gọi thân mật cho model. Đây thay giới hạn lịch sử 36–155 tháng. |
| BR-19 | Thông tin cá nhân hóa do người lớn nhập và được revision hóa. Có thể gồm sở thích, quan sát học tập, lịch sử run trong ứng dụng, trải nghiệm/sự kiện ngoài ứng dụng do người lớn nhập, thành tích, nguồn và ngày gần đúng tùy chọn. Lịch sử ứng dụng và trải nghiệm ngoài app là hai nguồn riêng. |
| BR-20 | Thông tin sức khỏe/tâm lý chỉ biểu diễn nhu cầu hỗ trợ do người lớn nhập, không phải chẩn đoán. Trường này giới hạn truy cập, mặc định loại khỏi AI context và hệ thống không tự suy luận. |
| BR-21 | Người lớn duyệt snapshot context tối thiểu, gắn với version cụ thể cho từng run. Chỉ trường được cho phép rõ ràng mới được gửi vào quy trình AI. |
| BR-22 | Giáo án Teacher nhận PDF/PPTX/DOCX có text, tối đa 25 MB và 100 trang/slide. Từ chối file mã hóa/đặt mật khẩu. Không hỗ trợ OCR trang scan. |
| BR-23 | Ý tưởng âm thanh tối đa 2 phút và 20 MB. Whisper ưu tiên tiếng Việt. Giữ audio gốc, transcript thô và transcript đã sửa cho đến khi xóa run. |
| BR-24 | Video cuối là MP4, 720p, tỷ lệ 16:9, dài 30–90 giây do hệ thống quyết định, một giọng người lớn tiếng Việt trung tính, phụ đề tiếng Việt và luôn tắt nhạc nền. Chủ thể dễ nhận ra, hình dáng chính, màu sắc và phong cách của tranh là neo tham chiếu cho scene. |
| BR-25 | Sản phẩm không có chức năng download/export hoặc URL video công khai. Playback cần token ngắn hạn do server cấp quyền. |
| BR-26 | Khi người dùng xóa run đã hoàn tất hoặc hủy run chưa hoàn tất, lifecycle xóa tranh, audio, transcript, snapshot hồ sơ của run, revision story, media scene/video và nội dung liên kết. Lệnh hủy giải phóng khóa active ngay; lệnh xóa/hủy chỉ giữ audit metadata tối thiểu. Với occurrence Teacher, giữ trạng thái slot mẫu đã dùng và thời điểm claim; xóa pointer đến run/media nhưng không mở lại slot. Không có thao tác xóa video riêng. Unit quota đã tiêu thụ không được hoàn lại (Q119, Q123). |
| BR-27 | Mọi luồng demo chỉ dùng profile, tranh và audio tổng hợp. Dữ liệu trẻ thật nằm ngoài demo, cần chính sách riêng về mục đích, quyền, phân quyền, chuyển dữ liệu cho provider và lifecycle. |
| BR-28 | Subscription capacity lớp tính theo tháng/năm và tiền VND. MoMo và VNPAY là payment adapter V1. V1 không dùng VietQR. |
| BR-29 | Slot lớp mua thêm được kích hoạt sau khi xác minh thanh toán và tính prorate cho phần thời gian còn lại của kỳ hiện tại; ngày gia hạn tiếp theo không đổi. |
| BR-30 | Có thể tắt auto-renew. Capacity đã trả tiền còn hiệu lực đến hết kỳ. V1 không tự tính hoàn tiền prorate giữa kỳ; ngoại lệ xử lý thủ công ngoài hệ thống. |
| BR-31 | Gia hạn thất bại bắt đầu 7 ngày grace. Hết grace thì hạn chế tạo lớp mới và story run mới; vẫn cho truy cập lớp, roster, lịch sử và quản lý thanh toán hiện có. |
| BR-32 | Hạ capacity cần admin tổ chức chọn lớp sẽ tạm ngưng trước khi xác nhận. Ghi một sự kiện append-only cho từng lớp được chọn, có chung change-group ID và thời điểm hiệu lực. Lớp/roster/lịch sử tạm ngưng được giữ lại ở chế độ chỉ đọc; không xóa dữ liệu. |
| BR-33 | Thông báo billing gửi admin thanh toán trong app và email: nhắc trước hạn 7 ngày và 1 ngày, khi thanh toán thành công/thất bại và khi grace hết hạn. |
| BR-34 | Audit hệ thống chỉ ghi metadata actor, action, resource và kết quả. Không ghi media, transcript, prompt, token, signed URL hoặc tên trẻ trong audit/log/metric label. |
| BR-35 | Xóa hồ sơ trẻ Parent hoặc Teacher bắt đầu lifecycle theo owner scope: thu hồi quyền, chặn run mới, xóa context hồ sơ và nội dung run liên quan; chỉ giữ metadata audit/enrollment cần thiết. Không tác động hồ sơ thuộc scope khác. |
| BR-36 | Giáo án tải lên, gợi ý người lớn và output model đều là nội dung không đáng tin cậy. Áp dụng safety policy có version dành cho trẻ trước khi hiển thị script hoặc tạo video. Trước playback, gate tự động kiểm tra frame được lấy mẫu, toàn bộ transcript lời kể và toàn bộ phụ đề của video đã ghép. Output bị chặn không phát được và quay lại bước xem script; gate này không thêm bước duyệt video cuối bởi người. Nội dung không chẩn đoán trẻ, đưa lời khuyên y tế/tâm lý, tiết lộ dữ liệu hồ sơ hoặc hướng trẻ tới hoạt động nguy hiểm. |
| BR-37 | Teacher chỉ chiếu video mẫu cho lớp sau khi Teacher phụ trách ghi nhận xác nhận riêng có audit cho occurrence. Đây là xác nhận đối tượng/mục đích trình chiếu, không phải duyệt video cuối. Xử lý dữ liệu trẻ thật vẫn cần chính sách quyền riêng tư được xem xét riêng. |
| BR-38 | Quota video theo tháng dương lịch `Asia/Ho_Chi_Minh`, tách riêng: Parent tính vào tài khoản Parent; Teacher tính vào tổ chức. Full-video request chỉ được xem là accepted sau khi AI Policy xác nhận compute reservation và Billing xác nhận quota admission bằng cùng idempotency key; Billing ghi đúng một usage unit trong transaction sở hữu riêng trước dispatch. Đây là saga nhiều owner, không phải transaction SQL xuyên module; receipt mơ hồ được đối soát trước dispatch. Mỗi accepted request vẫn tiêu thụ một unit kể cả khi sau đó lỗi provider/kỹ thuật hoặc safety block; không hoàn quota. Scene retry không phải request mới và không tiêu thụ thêm unit. Budget/quota admission bị từ chối không tạo accepted generation/job/usage, không chiếm run request cap và không dispatch. Hết quota thì từ chối request video mới bằng VIDEO_QUOTA_EXCEEDED, nhưng vẫn cho xem video/dữ liệu cũ và mua quota bổ sung. Billing sở hữu grant và immutable usage ledger; AI Policy chỉ hạch toán/reserve tài nguyên nền tảng (GPU/compute), không sở hữu product quota. Không lưu số dư còn lại mutable. Mức included cấu hình riêng cho Parent/Teacher và chốt sau benchmark synthetic (Q115). Dùng grant included hiện tại trước, sau đó top-up FIFO; included hết hạn cuối tháng, top-up carry-forward (Q117–Q118, Q124–Q126). Bắt đầu giữa tháng nhận đủ included (Q121); xóa run không hoàn unit (Q119); top-up một lần (Q120, Q128, Q132). |
| BR-39 | Tất cả trạng thái chờ thao tác người lớn, kể cả `DRAFT`, bắt đầu adult-wait khi không còn AI job và cần command người lớn. Tại +144 giờ tạo đúng một inbox reminder theo dedupe key; thử push best-effort và email best-effort chỉ tới địa chỉ đã xác minh của owner hiện tại. Inbox là nguồn chuẩn; lỗi gửi email/push không đổi trạng thái run. Ở +168 giờ, `VIDEO_READY` thành `COMPLETED`, trạng thái adult-wait khác thành `ABANDONED`, nhả khóa owner nhưng giữ nội dung đến khi người dùng xóa. `VIDEO_ADMISSION_PENDING` là system work, không có idle timer; nếu admission bị từ chối, StoryRun về `SCRIPT_REVIEW` và bắt đầu adult-wait mới (Q133, Q136). |
| BR-40 | Người lớn có thể hủy run chưa hoàn tất để nhả khóa ngay và xóa content theo lifecycle; xóa run hoàn tất xóa linked media/content. Request video accepted không được hoàn quota; Teacher sample claim thành công vẫn giữ. (Q123/Q128/Q133/Q134) |
| BR-41 | Organization admin chỉ được force-close conflicting run trong emergency qua command có reason và metadata audit; admin không xem media, quota claim và sample claim được giữ nguyên. (Q134) |
| BR-42 | Teacher AI Sketch Deck chỉ có trong Teacher web. Cả Teacher deck và Parent line-sketch guide đều tùy chọn trong session, chỉ được tạo khi người lớn bật; disabled nghĩa là không có job. Parent chụp trước khi VLM review subject và không dùng Teacher deck. (Q137/Q141/Q146/Q167) |
| BR-43 | Nếu Teacher bật deck, một occurrence dùng một deck revision chung cho plan đã duyệt, bao quát activities; giữ nền trắng, 3–5 bước, gợi ý bố cục và hướng dẫn ngắn. Deck chỉ được sinh sau toggle; khi plan đổi, deck stale và cần revision mới. (Q138–Q140/Q142/Q167) |
| BR-44 | Teacher Deck và Parent Sketch Guide không tiêu quota video. Dùng giới hạn request và compute cost cap riêng; mức số cụ thể phải được benchmark/cấu hình. Cả hai sketch job không nhận profile/tranh trẻ làm context; Parent guide chỉ nhận topic chung/độ khó. (Q143/Q146) |
| BR-45 | Video theo pipeline VLM image understanding → structured LLM story → storyboard 5–15 scene → adult script confirmation → scene reference/Character Bible → LTX-2.5 image-to-video trên Modal L40S → consistency/technical validation → FFmpeg composition → TTS/subtitles tiếng Việt, không nhạc → automated safety gate → private playback. Mỗi run có một trẻ; không có collaboration, public gallery/download hoặc final human video approval. Video không phù hợp quay lại script review, tối đa hai lần full regeneration sau request đầu; mỗi scene tối đa hai technical retries sau lần đầu. (Q144 và các quyết định pipeline đã chốt) |
| BR-46 | Trong drawing session, người lớn có thể bật line-sketch AI 3–5 bước cho một chủ đề chung đã chọn (ví dụ: con bướm) hoặc bỏ qua. Guide là hình hướng dẫn tổng quát, không phải tranh hoàn chỉnh của trẻ; chỉ topic/độ khó và guide contract được gửi đến sketch model, tuyệt đối không gửi hồ sơ, tuổi cụ thể, giọng nói, ảnh hay tranh trẻ. Guide tạm thời, riêng tư, có provenance và cleanup; không gắn profile/StoryRun, không dùng video quota, có compute/rate cap riêng. Skip, lỗi, timeout, limit refusal hoặc output bị chặn đều tiếp tục luồng vẽ/chụp; chủ thể tranh trẻ chỉ được xác nhận sau capture/VLM. (Q146; thay thế hình thức text-only Q145) |

<a id="srs-5"></a>
## 5. Luồng người dùng

### 5.1 Phụ huynh

Parent có thể mở thư viện public, lesson được chia sẻ đích danh/nhóm hoặc lesson đã dạy cho child profile đang được share. Lesson được dùng như preset; bản cá nhân hóa không sửa version nguồn. Thời hạn lesson history 30/60 ngày là câu hỏi mở tại §31.

1. Đăng nhập bằng tài khoản Parent riêng và chọn hồ sơ trẻ thuộc tài khoản đó.
2. Tạo run; backend kiểm tra người lớn chưa có run khác đang hoạt động.
   - Trẻ bắt đầu vẽ trên giấy. Trong lúc trẻ đang vẽ, người lớn có thể bật line-sketch AI 3–5 bước cho topic chung hoặc bỏ qua. Tắt thì không tạo AI job. Guide không dùng profile/ảnh/voice/artwork của trẻ và không chọn chủ thể thay cho bước VLM sau capture.
3. Sau khi trẻ vẽ xong, người lớn chụp ảnh tranh của đúng một trẻ. Giữ ảnh gốc và hash.
4. Nhập ý tưởng bằng chữ, ghi âm tối đa 2 phút hoặc dùng cả hai.
5. Nếu có ghi âm, chạy Whisper; hiển thị transcript thô và yêu cầu người lớn sửa/xác nhận. Lưu hai revision transcript riêng.
6. Chạy image understanding trên tranh. Hiển thị chủ thể/nhân vật dự kiến và mức không chắc chắn; người lớn có thể sửa chủ thể, thao tác này tạo revision diễn giải VLM mới cho ảnh đó.
7. Xem và duyệt snapshot context tối thiểu cho run này; chỉ gửi trường đã allowlist và được người lớn duyệt. Tên, tên gọi thân mật và support-needs bị loại mặc định.
8. AI tạo story/storyboard cá nhân hóa từ tranh, profile snapshot và lesson direction. Nếu script-following được bật cho lesson/run, dùng script làm hướng dẫn; nếu tắt thì tạo theo pipeline story hiện có. Parent có thể gợi ý tối đa ba lần viết lại, nhưng không chỉnh trực tiếp scene.
9. Người lớn xem và xác nhận revision script/storyboard cuối. Nếu chủ thể không đúng, xác nhận người lớn trước khi sửa subject và yêu cầu AI gợi ý lại.
10. Backend tạo video mới cho đúng child từ ảnh tranh đó theo pipeline §6.2.2; không tái sử dụng video của trẻ khác. Video có thể khác nhau theo artwork/profile nhưng theo hướng script nếu tùy chọn đó bật.
11. Khi video đã playable, mới hiển thị danh sách một hoặc nhiều hoạt động ngoài trời trong lesson, gồm vật liệu, cách làm và ghi chú. Parent có thể dùng lesson để làm hoạt động với con.
12. Chỉ mở playback sau kiểm tra kỹ thuật và safety. Parent có thể hoàn tất hoặc yêu cầu tạo lại tối đa hai lần; video cũ bị ẩn ngay khi request thay thế được nhận. Accepted video request tiêu thụ quota theo quy tắc Billing, kể cả lỗi kỹ thuật/provider/safety.
13. Giữ reminder 144h, idle close 168h, cancel/delete lifecycle và private playback như baseline. Parent có thể xem feedback/reply lesson theo child profile share; đây không phải chat, không có completion toggle hoặc gửi tranh qua feedback.

Trình tự bắt buộc là vẽ (line-sketch chỉ khi bật) → chụp tranh → tạo video từ tranh theo pipeline → hiển thị outdoor activities đã đặt trong lesson.

### 5.2 Giáo viên

Teacher có thể tạo lesson reusable của trường hoặc dùng bản public/được share như preset; dùng preset không sửa source version. Mỗi occurrence pin đúng lesson/version và plan đã chọn.

1. Đăng nhập bằng tài khoản Teacher web riêng và mở lớp của tổ chức được phân công.
2. Tạo hoặc chọn hồ sơ trẻ được quản lý. Mỗi hồ sơ chỉ thuộc một lớp đang hoạt động tại một thời điểm. Có thể nhập nhanh câu trả lời từ phiếu phụ huynh.
3. Tạo occurrence, chọn dùng hoặc không dùng preset lesson; có thể upload tài liệu theo template/form chuẩn.
4. Parser trích xuất text theo giới hạn hiện hành, không OCR scan. Hệ thống lọc và map chỉ allowlist fields vào structured draft; file gốc và toàn bộ raw plan không được gửi model. Teacher preview/correct extracted structured draft trước khi AI hỗ trợ tạo lesson/plan.
5. Lesson draft do AI hỗ trợ luôn ở trạng thái draft; Teacher review/chỉnh sửa, lưu version và gửi Manager review nếu muốn public. Lesson có activity list một hoặc nhiều mục với vật liệu, cách làm và ghi chú.
6. Khi đang chạy buổi học, Teacher bật line-sketch guide nếu muốn trẻ vẽ theo. Chỉ lúc bật mới tạo Sketch Deck/job cho plan/occurrence; nếu tắt thì không tạo, và không chặn luồng vẽ/chụp/video.
7. Nếu bật, Teacher xem preview line-sketch deck dùng chung cho occurrence trên bề mặt trình chiếu nền trắng, điều khiển Back/Next/skip/regenerate. Trẻ vẽ bằng giấy/bút; không có canvas chung hoặc nhiều trẻ trong một run.
8. Video mẫu vẫn là luồng riêng. Hệ thống chọn ngẫu nhiên một trẻ đại diện đủ điều kiện trong roster đã được phép; Teacher xác nhận selection/context. Một occurrence có tối đa một video mẫu thành công.
9. Ghim lesson/plan version vào occurrence; Teacher chọn đúng một activity đã duyệt cho run mẫu. Các activities khác có thể được hiển thị sau video theo lesson.
10. Teacher chụp tranh giấy của trẻ đó bằng camera trình duyệt hoặc tải ảnh chụp bằng điện thoại. Nhập ý tưởng bằng chữ hoặc ghi âm; Whisper ưu tiên tiếng Việt, Teacher xem/sửa/xác nhận transcript và chủ thể nhận diện. Sửa chủ thể tạo revision VLM mới. Không dùng ảnh của trẻ khác trong cùng run.
11. VLM phân tích tranh và tạo neo nhận diện; LLM tạo story/storyboard 5–15 scene cá nhân hóa theo profile. Teacher có thể đặt hướng kể theo lesson và gợi ý tối đa ba lần viết lại.
12. Teacher xem và xác nhận revision cuối của script/storyboard. Lesson có thể bật/tắt script-following; nếu bật, video đi theo hướng kịch bản nhưng từng video vẫn mới và có thể khác theo tranh/profile. Chỉ sau xác nhận mới chạy pipeline §6.2.2.
13. Backend chuẩn bị ảnh tham chiếu/Character Bible từ duy nhất bức tranh được chọn, tạo clip scene bằng LTX-2.5 trên Modal L40S, kiểm tra consistency/technical quality, ghép bằng FFmpeg, tạo lời kể tiếng Việt và phụ đề, tắt nhạc nền, rồi chạy safety validation tự động trên output đã ghép. Chỉ video qua gate mới phát được; video sẵn sàng được chiếu trong run/occurrence, không có bước duyệt video cuối.
14. Nếu video không phù hợp, Teacher yêu cầu tạo lại; output cũ bị ẩn khỏi playback ngay khi request thay thế được nhận và run quay về duyệt script. Tối đa hai request tạo lại toàn video sau request đầu; mỗi scene có tối đa hai retry kỹ thuật sau lần đầu. Mỗi request video được nhận tính quota dù lỗi kỹ thuật/safety; lỗi trước video mẫu playable đầu không claim slot occurrence. Sau claim đầu, slot không mở lại, kể cả khi các lần tạo lại lỗi (Q127/Q128).
15. Teacher phụ trách xác nhận riêng việc chiếu video cho cả lớp ở occurrence đó. Đây là xác nhận audience/use, không phải duyệt video. Khi không còn AI job và video sẵn sàng, Teacher có thể hoàn tất hoặc tạo lại; adult-wait/nhắc 144h/đóng 168h, hủy run, giữ media đến xóa và quota không hoàn theo các quy tắc chung.

Sau buổi học, Parent được liên kết có thể xem lesson đã dạy trong cửa sổ history đang được quyết định, tải nội dung còn quyền truy cập và gửi feedback riêng trong tenant đó.

### 5.3 Tổ chức và thanh toán

1. Admin tổ chức tạo lớp khi còn capacity (10 slot lớp bao gồm trong gói cơ bản cộng slot mua thêm).
2. Admin phân công một Teacher phụ trách mỗi lớp và quản lý roster/phân lớp hồ sơ.
3. Admin mua slot lớp bổ sung qua adapter MoMo/VNPAY theo tháng/năm. Chỉ lưu provider reference, không lưu thông tin xác thực thanh toán.
4. Khi xác minh thanh toán thành công, cập nhật kỳ capacity; slot mua giữa kỳ được tính prorate.
5. Gửi nhắc trong app/email trước hạn 7 ngày và 1 ngày; gửi thông báo thanh toán thành công/thất bại và khi grace hết hạn.
6. Gia hạn lỗi có 7 ngày grace. Hết grace thì hạn chế tạo lớp và story run mới, vẫn giữ quyền xem lớp/roster/lịch sử hiện có và quản lý thanh toán.
7. Khi hạ capacity, admin chỉ định lớp cần tạm ngưng. Dữ liệu lớp bị ngưng vẫn còn và chỉ đọc.

<a id="srs-6"></a>
## 6. Vòng đời story và video

### 6.1 Các stage logic

| Stage | Kết quả cần có | Hành động người dùng hoặc quy tắc hệ thống |
|---|---|---|
| Draft | Một trẻ và tranh nguồn được gắn với run | Backend bắt buộc chỉ có một profile ref |
| Xem input | Ý tưởng người lớn tồn tại dạng text hoặc transcript để xem | Whisper chuyển giọng nói thành chữ, người lớn xác nhận |
| Xem chủ thể | VLM trả cấu trúc chủ thể/entity/mức không chắc chắn | Người lớn xác nhận hoặc sửa; sửa sẽ chạy lại VLM |
| Xem context | Snapshot context tối thiểu đã được người lớn duyệt | Lesson activity list hiển thị sau khi video hoàn tất |
| Story draft | Tạo script có version và 5–15 scene | Output LLM phải khớp schema và safety policy |
| Viết lại | Tạo revision story bất biến mới | Tối đa ba request viết lại sau bản đầu; xem xét từng revision |
| Xác nhận script | Có hash revision script/storyboard đã xác nhận | Bắt buộc trước mỗi request tạo video |
| Tạo video | Có clip từng scene, lời kể, phụ đề và MP4 đã ghép | LTX-2.5 qua Modal L40S; mỗi scene tối đa hai retry kỹ thuật tự động |
| Sẵn sàng phát | Có artifact đạt kiểm tra kỹ thuật và safety | Hiển thị ngay; run vẫn active cho đến khi người lớn bấm Hoàn tất hoặc Tạo lại; không có duyệt video |
| Tạo lại chất lượng | Run quay lại bước xem script | Người lớn đánh dấu không phù hợp; video cũ ẩn playback từ lúc chấp nhận request tạo lại; script phải xác nhận; tối đa hai lần tạo lại |
| Hoàn tất, thất bại, abandon hoặc hủy | Run ra khỏi tập active | Hoàn tất do người lớn hoặc idle closeout từ VIDEO_READY; run chờ khác thành ABANDONED sau 168 giờ adult-wait. FAILED/ABANDONED giữ nội dung đến khi xóa; cancel giải phóng khóa rồi xóa theo lifecycle. Run lỗi trước playable claim đầu không chiếm slot mẫu Teacher |
| Đã xóa | Lifecycle đã xóa toàn bộ nội dung liên kết | Chỉ giữ audit metadata tối thiểu; quota đã tiêu thụ và claim mẫu thành công vẫn được giữ |

Kết quả AI bất đồng bộ phải khớp revision run dự kiến, input hash, hash snapshot context hồ sơ, các revision lesson/activity áp dụng cho role và input đã pin, cùng contract version; Parent không bị coi là stale chỉ vì thiếu lựa chọn activity trước video, còn tập ref/hash cụ thể (tham chiếu lesson-version opaque tùy chọn qua cổng module Lesson; không gắn org/class/occurrence của Teacher; Parent không cần activity_ref làm tiền điều kiện; Teacher sample vẫn ghim đúng một activity đã duyệt) [Còn mở cho thiết kế vật lý: vị trí lưu vật lý tham chiếu lesson-version; biểu diễn contract/schema theo role]. Kết quả cũ được ghi nhận là stale, không được ghi đè dữ liệu mới hơn.

### 6.1.1 Mô hình trạng thái đề xuất

Tên trạng thái dưới đây là giá trị đích ở domain. Nhãn UI phải được Việt hóa, không dùng tên nội bộ/provider để hiển thị cho người dùng.

| Aggregate | Trạng thái đề xuất | Tóm tắt chuyển trạng thái được phép |
|---|---|---|
| StoryRun | DRAFT, INPUT_PROCESSING, INPUT_REVIEW, SUBJECT_REVIEW, PREPARATION_REVIEW, STORY_GENERATING, SCRIPT_REVIEW, VIDEO_ADMISSION_PENDING, VIDEO_QUEUED, VIDEO_GENERATING, VIDEO_SAFETY_VALIDATING, VIDEO_READY, SAFETY_BLOCKED, COMPLETED, FAILED, ABANDONED, DELETE_PENDING, DELETED | `run_state` mô tả bước nghiệp vụ nhìn thấy được; `AiJob.job_state` + `job_stage` mô tả xử lý ASR/VLM/story/video chi tiết. DRAFT là adult-wait khi cần người lớn nhập/xác nhận dữ liệu; DRAFT → INPUT_PROCESSING khi input đã nhận và ASR/VLM job được enqueue; input job thành công hoặc lỗi có thể khắc phục → INPUT_REVIEW; người lớn xác nhận transcript → SUBJECT_REVIEW; sửa chủ thể tạo VLM job mới và quay INPUT_PROCESSING → SUBJECT_REVIEW. Xử lý AI đang chạy không phải adult-wait dù màn hình hiển thị stage. SUBJECT_REVIEW/PREPARATION_REVIEW → STORY_GENERATING khi subject và snapshot context đã xác nhận; Parent không có điều kiện activity đã chọn/xác nhận, Teacher sample còn cần đúng một activity đã duyệt; STORY_GENERATING → SCRIPT_REVIEW; SCRIPT_REVIEW → STORY_GENERATING khi rewrite hợp lệ hoặc VIDEO_QUEUED khi script revision đã xác nhận; queue → generation → safety validation → VIDEO_READY khi đạt. Chỉ state không có job đang xử lý và cần command người lớn mới adult-wait: DRAFT, INPUT_REVIEW, SUBJECT_REVIEW, PREPARATION_REVIEW, SCRIPT_REVIEW, SAFETY_BLOCKED (khi cần người lớn) và VIDEO_READY. VIDEO_ADMISSION_PENDING là system work, không arm idle timer; ADMISSION_REJECTED đưa run về SCRIPT_REVIEW và bắt đầu adult-wait mới. `last_meaningful_activity_at` do server ghi UTC khi người lớn gửi command/review/xác nhận có hiệu lực; polling/push receipt/app heartbeat không reset idle. `adult_wait_started_at` bắt đầu khi AI job kết thúc/lỗi và run thực sự cần thao tác người lớn. Sau 144 giờ tạo inbox reminder, push best-effort và email nếu current-owner email đã xác minh; sau 168 giờ VIDEO_READY → COMPLETED, adult-wait state khác kể cả DRAFT → ABANDONED; cả hai nhả khóa và giữ nội dung đến khi user xóa. AI job có deadline độc lập 6 giờ và không bị idle-closeout khi còn QUEUED/RUNNING/RETRY_WAIT/AWAITING_RECONCILIATION. Hủy run chưa kết thúc → DELETE_PENDING, nhả khóa ngay và khởi động purge. COMPLETED, FAILED, ABANDONED, DELETE_PENDING, DELETED không chiếm khóa. Reassignment không đổi state: quyền chuyển sang Teacher hiện được phân công, quyền cũ/token bị thu hồi, audit metadata được ghi. |
| VideoGeneration | ADMISSION_PENDING, ADMISSION_REJECTED, ACCEPTED, QUEUED, GENERATING, TECHNICAL_VALIDATING, SAFETY_VALIDATING, READY, SAFETY_BLOCKED, FAILED, REJECTED_BY_ADULT, SUPERSEDED | Một hàng generation bền vững trước tiên là intent có idempotency key. Chỉ chuyển từ ADMISSION_PENDING sang ACCEPTED sau khi AI Policy budget reservation và Billing quota receipt cùng xác nhận; chỉ ACCEPTED mới nhận generation_no, chiếm một trong ba request/run, tạo AI job/outbox và tiêu thụ quota. Budget/quota thất bại chuyển intent sang ADMISSION_REJECTED, không tính request/video quota. Kết quả mơ hồ giữ intent pending để reconciler tra receipt theo cùng key trước dispatch. Khi StoryRun SCRIPT_REVIEW nhận request tạo video, chuyển sang VIDEO_ADMISSION_PENDING. Đây là system work, không adult-wait; `ADMISSION_REJECTED` trả StoryRun về SCRIPT_REVIEW và đặt timer mới, không tiêu quota/cap. `ACCEPTED` đặt `deadline_at = accepted_at + 6h`, gồm queue, retry wait và mọi stage. READY yêu cầu đạt kiểm tra kỹ thuật và safety. Khi người lớn từ chối video và yêu cầu tạo lại, video cũ thành REJECTED_BY_ADULT và bị ẩn khỏi playback ngay; nội dung giữ nội bộ đến khi xóa run. Nếu video thay thế lỗi thì video cũ vẫn không phát lại. Kịch bản mới phải xác nhận trước request tiếp theo. |
| LessonOccurrence | DRAFT, DOCUMENT_REVIEW, PLAN_REVIEW, APPROVED, SAMPLE_AVAILABLE, SAMPLE_USED, ARCHIVED | Import/xem tài liệu trước khi duyệt plan; occurrence đã duyệt cho phép tạo video mẫu; output duy nhất qua safety và phát được sẽ claim slot nguyên tử. Run lỗi trước playback giữ slot chưa dùng. Xóa run xóa pointer run nhưng giữ trạng thái/thời điểm claim. Occurrence cũng ghi xác nhận của Teacher phụ trách khi chiếu video cho lớp. |
| SketchDeckRevision | GENERATING, READY, FAILED, STALE, SUPERSEDED | Tạo từ một approved plan revision/hash; READY chỉ khi bao quát mọi activity, mỗi hướng dẫn có đúng 3–5 ordered line-sketch step, age band/layout/content/media validation đạt. Mọi output phải có asset/hash/lineage. Plan đổi làm deck hiện hành STALE; regenerate tạo revision mới. Không có profile/trẻ subject và không tiêu video quota. |
| AiJob | QUEUED, RUNNING, RETRY_WAIT, SUCCEEDED, FAILED, CANCEL_REQUESTED, CANCELLED, STALE, AWAITING_RECONCILIATION | Trạng thái queue/worker được lưu bền vững; retry kỹ thuật giới hạn có RETRY_WAIT; kết quả hợp lệ thì thành công; lệch hash/revision thì stale; hết retry thì lỗi; provider outcome chưa rõ thì dừng để đối soát trước khi gọi GPU tốn phí lần nữa. |
| OrganizationSubscription | PAYMENT_PENDING, ACTIVE, GRACE, RESTRICTED, CANCEL_AT_PERIOD_END, CANCELED | Chỉ event provider đã xác minh mới chuyển trạng thái thanh toán; gia hạn lỗi vào grace 7 ngày rồi bị hạn chế; hủy subscription ngừng kỳ kế tiếp nhưng quyền đã trả tiền còn đến hết kỳ; capacity gắn kỳ hiệu lực. |
| PaymentAttempt | CREATED, PENDING, SUCCEEDED, FAILED, EXPIRED | Browser redirect chỉ mang tính thông tin; chỉ callback/provider event có chữ ký đã xác minh hoặc đã đối soát mới ghi nhận đã trả tiền. Event trùng không áp dụng capacity lần hai. |

Quy tắc chuyển trạng thái:

- Application command thực hiện chuyển trạng thái và lưu event/outbox trong transaction. Client không tự đặt state.
- Bộ đếm viết lại story và request video tách riêng. Mỗi run có story đầu và tối đa ba lần viết lại; một request video ban đầu và tối đa hai request tạo lại chất lượng. Khi chấp nhận full-video request, transaction đồng thời tiêu thụ một request slot và một unit quota qua Billing ledger, kể cả khi request lỗi kỹ thuật/provider hoặc bị safety block sau đó; không hoàn quota. Retry scene tự động có giới hạn riêng và không tạo product-quota usage mới.
- Tạo lại video chất lượng phải quay về xem/xác nhận revision script hiện hành. Người lớn có thể giữ story hiện tại hoặc yêu cầu AI viết lại trong giới hạn trước khi xác nhận.
- Retry scene kỹ thuật không tính thành lần viết lại story hoặc request tạo lại video. Run lỗi trước khi có output an toàn/phát được không chiếm slot video mẫu của occurrence Teacher.
- VIDEO_READY yêu cầu đạt kiểm tra kỹ thuật và output-safety gate có version. Nếu gate không kiểm tra đủ media, thất bại hoặc trả kết quả không xác định thì chặn playback và đưa run về trạng thái chờ người lớn sửa/xác nhận script. Video đạt được phát ngay; người lớn có thể hoàn tất/tạo lại. VIDEO_READY tự COMPLETED sau 168 giờ adult-wait idle; các trạng thái chờ người lớn khác tự ABANDONED ở cùng deadline, sau nhắc tại giờ 144. Hai kết quả đóng run, nhả khóa và giữ nội dung. Không hoàn quota request đã nhận và không mở lại Teacher sample claim đã dùng.

### 6.2 Quy trình AI

1. **Hiểu ảnh:** VLM nhận diện ứng viên chủ thể, nhân vật, vật thể, bối cảnh, neo phong cách hình ảnh và mức không chắc chắn từ tranh gốc.
2. **Hiểu ý tưởng:** Whisper tạo transcript ưu tiên tiếng Việt. Nội dung người lớn sửa được lưu thành revision riêng.
3. **Lọc context:** backend tạo snapshot context có giới hạn, theo schema version và được người lớn duyệt. Tên trẻ và ghi chú hỗ trợ bị loại.
4. **Lập story:** LLM nhận tranh, snapshot tối thiểu và ý tưởng đã duyệt. Parent không có bước chọn hoặc xác nhận activity trước story/video. Teacher sample bổ sung đúng một activity đã duyệt và giáo án/hướng kể theo contract. Input/prompt cụ thể và lesson direction của Parent (tham chiếu lesson-version opaque tùy chọn qua cổng module Lesson; không gắn org/class/occurrence của Teacher; đầu vào theo role; Parent story prompt không đưa activity, lesson hoặc gợi ý catalog; Teacher prompt dùng đúng một activity đã duyệt. Nếu lesson-version ref không còn hợp lệ thì không đưa ref đó vào planner prompt; list hậu video tuân quy tắc C6.); không tự lấy activity đầu tiên làm fallback. Output vẫn là script có cấu trúc cùng 5–15 scene. [Còn mở cho thiết kế vật lý: vị trí lưu vật lý tham chiếu lesson-version].
5. **Cổng xác nhận script:** người lớn xác nhận bản cuối. Mỗi lần AI viết lại, kể cả sau khi video bị đánh dấu không phù hợp, tạo revision mới và cần xác nhận lại.
6. **Chuẩn bị ảnh tham chiếu scene:** dùng tranh gốc/frame tham chiếu đã duyệt và character anchor có version để giữ chủ thể, hình dáng, màu sắc, phong cách dễ nhận ra. Không âm thầm thay hoặc sửa tác phẩm nguồn.
7. **Duyệt budget, quota và tạo video:** use case có một idempotency boundary ở application nhưng không có transaction SQL xuyên module. AI Policy trước hết tạo reservation budget GPU/compute có idempotency key, lease/expiry và mức worst-case cho request; Billing sau đó kiểm tra scope/grant và ghi đúng một `billing.video_quota_usage` nguyên tử trong transaction riêng. Nếu Billing từ chối quota, application giải phóng reservation; reservation mồ côi do tiến trình dừng được dọn/reconcile sau lease. Nếu phản hồi admission bị mất hoặc không rõ, application tra cứu cùng idempotency key ở cả hai owner trước khi dispatch, release hoặc trả lỗi; không tạo request/usage thứ hai. Chỉ khi cả hai receipt đã xác nhận mới ghi/dispatch accepted generation qua outbox. Story chỉ giữ reference opaque đến receipt, không sở hữu budget/quota. Request đã nhận vẫn tiêu thụ unit nếu provider, kỹ thuật hoặc safety stage lỗi; scene retry không tạo unit mới. GPU Modal L40S dùng cho LTX; Modal L4 là ứng viên cho stage model nhỏ hơn. Model/runtime/license và quality evidence cần benchmark riêng.
8. **Kiểm tra kỹ thuật và ghép:** xác minh decode từng scene, kích thước frame, tỷ lệ, thứ tự scene và thời lượng; FFmpeg ghép thành MP4 720p với giọng người lớn cố định và phụ đề tiếng Việt, tắt nhạc nền.
9. **Safety tự động trên output đã ghép:** kiểm tra toàn bộ lời kể/phụ đề và lấy mẫu frame cuối video ít nhất một frame mỗi giây, đồng thời lấy frame đầu/giữa/cuối mỗi scene. Dùng policy/model profile có version, taxonomy, model revision, ngưỡng, bằng chứng calibration và đánh giá false-positive/false-negative làm cổng promote model. Nếu kiểm tra thất bại, thiếu coverage hoặc không xác định, đặt SAFETY_BLOCKED, không cấp playback token và đưa người lớn về xem script. Chỉ ghi policy version, kết quả và mã finding an toàn; không đoán threshold từ prompt. Threshold phải là cổng triển khai đến khi đánh giá trên bộ synthetic.
10. **Playback:** API chỉ cấp token ngắn hạn sau khi kiểm tra kỹ thuật và an toàn đều đạt. Media ở object storage riêng tư; ứng dụng không lấy được URL công khai không giới hạn.

Demo live dự kiến chạy Docker local với dữ liệu tổng hợp và inference live qua Modal. MinIO local không thể được Modal truy cập trực tiếp; contract chuyển file được mô tả tại §24.3. Backend SDK chuyển byte trong allowlist vào scratch prefix riêng theo job trên Modal Volume, gửi path ref/hash opaque tới remote function, tải kết quả bằng SDK, xác minh output trước khi lưu MinIO và xóa scratch. Không truyền media thô trong function argument hoặc cấp Modal quyền rộng vào storage local. Theo tài liệu Modal về payload lớn/bất đồng bộ và vùng lưu trữ, luồng này chỉ dùng synthetic cho đến khi review riêng việc chuyển vùng/xử lý dữ liệu thật được duyệt. [Modal local data](https://modal.com/docs/guide/local-data), [Modal data residency](https://modal.com/docs/guide/data-residency), [Modal Volumes](https://modal.com/docs/guide/volumes).

### 6.2.1 AI Sketch và deck trình chiếu Teacher

AI Sketch là pipeline riêng với story/video. Lesson application chỉ tạo deck request khi Teacher bật line-sketch trong session; nếu tắt thì không enqueue job hoặc asset. Khi bật, request pin chính xác `approved_plan_revision_ref` và `content_hash`. Pipeline đọc mục tiêu, chủ thể, vật liệu và activities đã duyệt; không gửi roster, tên trẻ, profile cá nhân hóa hoặc tranh mẫu. Deck là tùy chọn và không chặn Teacher tiếp tục buổi học.

Một occurrence có một deck revision hiện hành dùng chung cho cả buổi, bao quát mọi activity trong plan đã duyệt. Deck là bề mặt trình chiếu web 16:9 nền trắng, ít chữ, phù hợp để chiếu; với mỗi chủ thể/hướng dẫn vẽ, deck có chuỗi 3–5 line-sketch bước tăng dần, chỉ dẫn bố cục/vị trí (ví dụ chủ thể ở giữa, hoa bên phải), và câu ngắn giúp Teacher giải thích activity ngoài trời cho trẻ. Deck giải thích từng activity theo dữ liệu đã duyệt, không tự thêm hoạt động nguy hiểm hoặc không có trong plan. Nó không phải bộ slide PowerPoint để xuất file và không phải canvas vẽ số: Teacher điều khiển trình chiếu; trẻ vẽ bằng giấy/bút.

Teacher điều khiển Back/Next, chọn activity/chủ thể trong plan, skip bước không cần và yêu cầu AI tạo lại từng sketch. Next/Back/skip và vị trí đang xem chỉ là trạng thái giao diện tạm thời, không cần persistence. Regenerate không sửa revision hiện có: tạo deck revision mới gắn cùng plan hash, giữ nguyên tham chiếu asset của các bước không đổi và thay asset/lineage của bước được tạo lại. Nếu plan được sửa hoặc duyệt lại, deck cũ chuyển STALE và không được dùng để trình chiếu cho occurrence đến khi deck mới READY. Story video không nằm trong slide text/ảnh AI Sketch; khi video mẫu của đúng một trẻ hoàn tất pipeline §6.2.2, Teacher có thể mở playback trong cùng màn hình trình chiếu ở phần kết thúc hoạt động/occurrence.

Sketch generation không dùng hoặc trừ `video_quota_usage`. Nó có bucket rate-limit, compute reservation/cost cap và telemetry riêng theo owner/occurrence, với giá trị được benchmark bằng dữ liệu tổng hợp. Dùng AI Policy để reserve/settle compute, nhưng không tạo product video quota usage. Output phải kiểm schema, aspect/dimensions, file type, malware/safety policy và provenance; asset được ghi qua Core và liên kết bằng lineage. Model tạo line-art chưa được chọn; dùng provider port và POC synthetic để so sánh khả năng tạo nét đơn giản, tính ổn định theo bước, tuổi phù hợp, độ trễ, license và cost trước khi promote.

Parent có một capability riêng, hoàn toàn tùy chọn trong lúc trẻ đang vẽ: người lớn chọn topic chung từ danh mục đã duyệt (ví dụ con bướm) và độ khó đơn giản, rồi có thể yêu cầu guide line-art 3–5 bước hoặc bỏ qua. Target của job là `PARENT_SKETCH_GUIDE`; model chỉ nhận topic/độ khó và phiên bản guide contract, không nhận hồ sơ, tuổi cụ thể, tên, giọng nói, ảnh hay tranh trẻ. Output minh họa cách vẽ một chủ thể chung chứ không phải tranh hoàn chỉnh của trẻ; nó phải qua schema, media, nét line-art và kiểm tra an toàn trước khi hiển thị. Asset riêng tư có provenance, gắn expiry/cleanup và không thuộc profile hay StoryRun. Compute/rate cap riêng, không ghi video quota. Skip, lỗi, timeout, limit refusal hoặc output không đạt đều trả Parent về luồng vẽ/chụp hiện tại; subject review vẫn diễn ra sau capture. Q146 thay thế hình thức text-only tạm thời ghi ở Q145. Parent guide không phải Teacher Deck và không biến thành bước chính của Parent.

### 6.2.2 Pipeline story-video theo đề xuất Sketch2Life

Pipeline áp dụng cho Parent và Teacher, mỗi lần chỉ nhận một tranh của một trẻ. Các bước từ bộ pipeline chủ sở hữu cung cấp được điều chỉnh theo các quy tắc hiện hành: không có vẽ cộng tác/nhiều trẻ; script/storyboard là human approval gate duy nhất; output cuối qua safety gate tự động rồi được phát ngay, không chờ duyệt video cuối; playback riêng trong run, không public gallery/download.

| # | Giai đoạn | Đầu vào/đầu ra và kiểm soát | Công nghệ/ranh giới triển khai |
|---:|---|---|---|
| 1 | Tranh và ý tưởng | Một ảnh tranh bất biến của đúng một trẻ; người lớn nhập ý tưởng chữ và/hoặc xác nhận transcript Whisper. Activity list thuộc lesson và hiển thị sau video; không bắt Parent chọn activity trước khi tạo video. | Android camera/library hoặc Teacher browser camera/upload; upload API resumable; Whisper ASR adapter ưu tiên tiếng Việt. |
| 2 | Hiểu tranh | VLM nhận diện ứng viên nhân vật/đồ vật/bối cảnh; lưu màu, hình dáng, nét vẽ, bố cục, visual anchors và uncertainty gắn với hash tranh. Các anchor chỉ mô tả bức tranh của trẻ được chọn. | VLM adapter; candidate Qwen2.5-VL-7B trên Modal L4 sau POC, không coi là đã benchmark. Pydantic/JSON Schema validation. |
| 3 | Xem xét input | Người lớn xem/xác nhận transcript và chủ thể; sửa subject tạo revision VLM mới trên đúng ảnh hash. Người lớn duyệt context tối thiểu. Teacher xác nhận lesson/activity đã duyệt; Parent activity list chỉ hiện sau khi video sẵn sàng. | Client Parent/Teacher + FastAPI application; `story.review_decisions`. |
| 4 | Tạo story | LLM tạo mở đầu-diễn biến-kết thúc, nhân vật/hành động và lời kể tiếng Việt dựa trên tranh, ý tưởng và snapshot cá nhân hóa tối thiểu đã xác nhận; Parent không có bước chọn activity trước story/video, Teacher bổ sung đúng một activity đã duyệt và hướng kể từ plan. Input/prompt và lesson direction Parent (tham chiếu lesson-version opaque tùy chọn qua cổng module Lesson; không gắn org/class/occurrence của Teacher; đầu vào theo role; Parent story prompt không đưa activity, lesson hoặc gợi ý catalog; Teacher prompt dùng đúng một activity đã duyệt. Nếu lesson-version ref không còn hợp lệ thì không đưa ref đó vào planner prompt; list hậu video tuân quy tắc C6.). [Còn mở cho thiết kế vật lý: vị trí lưu vật lý tham chiếu lesson-version]. | Story Planner port, structured JSON output, prompt/policy version pin. |
| 5 | Tạo storyboard | Chia nội dung thành 5–15 scene, tổng thời lượng do hệ thống chọn trong 30–90 giây; mục tiêu khoảng 6 giây/scene nhưng planner có thể điều chỉnh theo tổng thời lượng. Mỗi scene gồm action, image/video prompt có kiểm soát, narration segment, timing và character anchor. | LLM + versioned prompt template; scene lưu thành các row, không giữ danh sách vô hạn trong một JSON field. |
| 6 | Duyệt script/storyboard | Adult xem bản story hiện hành và xác nhận hash/revision cuối trước khi generation. Có một bản đầu và tối đa ba lần viết lại. Không cho sửa tay từng scene/thứ tự trong V1. | Parent/Teacher web/mobile review + FastAPI; `story.review_decisions`. Teacher có thể định hướng từ plan; Parent gửi gợi ý. |
| 7 | Chuẩn bị reference | Tạo Character Bible cho tranh duy nhất được chọn: identity anchors, màu, hình dáng và phong cách; chuẩn bị ảnh tham chiếu/layout cho từng scene. Không lấy ảnh/profile của trẻ khác. | Python + OpenCV/Pillow; segmentation như SAM2 chỉ là tùy chọn sau POC, không bắt buộc V1. Derived image có asset ID/hash/lineage riêng. |
| 8 | Sinh video từng scene | Image-to-video tạo clip riêng từ reference và action đã duyệt. Scene độc lập có thể chạy song song trong giới hạn GPU; scene cần nối frame thì chạy tuần tự. Mỗi scene có một lượt đầu và tối đa hai automatic retry; hết lượt làm request lỗi, không gọi lặp vô hạn. | LTX-2.5 official-compatible inference workflow, PyTorch/workflow đã pin; Modal GPU L40S. Modal L4 không được mặc định đủ cho LTX. |
| 9 | Kiểm consistency | Kiểm tra subject/character anchor, màu, hình dáng/phong cách, biến dạng, chi tiết không mong muốn và mức phù hợp action. Retry scene không đạt trong giới hạn bước 8; không đạt tiếp thì dừng request và báo lỗi an toàn. | OpenCV metrics + VLM/vision validation adapter; ngưỡng, model revision và calibration là benchmark/promotion gate, không giả định prompt bảo đảm consistency. |
| 10 | Ghép các scene | Kiểm tra khả năng giải mã, kích thước khung hình, tỷ lệ và thứ tự; ghép clip theo storyboard, căn thời lượng/chuyển cảnh cần thiết để tạo bản video tổng. | FFmpeg worker/container; scene được sắp xếp theo `scene_index`, không đổi thứ tự storyboard đã duyệt. |
| 11 | Tạo lời kể và âm thanh | Tạo lời kể bằng một giọng người lớn tiếng Việt trung tính, căn lời kể với scene; tạo phụ đề tiếng Việt đồng bộ. V1 luôn tắt nhạc nền và hiệu ứng âm thanh. | Vietnamese TTS adapter (VieNeu-TTS chỉ là ứng viên), kiểm tra timing phụ đề và FFmpeg để mux lời kể/phụ đề vào video tổng. |
| 12 | Safety và kiểm tra đầu ra | Sau khi ghép/mux, kiểm tra toàn bộ lời kể/phụ đề và frame video theo policy/model profile có version. Thiếu coverage, lỗi hoặc kết quả không xác định đều chặn playback. Đây là kiểm tra tự động, không phải bước người lớn duyệt video cuối. | OpenCV + safety/VLM adapter; lưu policy revision, kết quả và mã lý do an toàn; không ghi media/prompt vào telemetry. |
| 13 | Phát video và tạo lại | Sau khi kiểm tra kỹ thuật và safety đều đạt, cấp playback token ngắn hạn và phát video trong run. Nếu người lớn đánh dấu không phù hợp, ẩn bản cũ khi request thay thế được nhận, quay lại duyệt script rồi xác nhận trước khi tạo lại; tối đa hai lần tạo lại toàn video sau lần đầu. | API phân quyền + object storage riêng tư; không có gallery công khai, download/export hoặc URL dài hạn. Teacher xác nhận audience riêng nếu chiếu cho lớp. |
| 14 | Vòng đời dữ liệu | Lưu output riêng tư cùng provenance đến khi người lớn xóa run; khi xóa, xóa tranh, audio, transcript, story, scene và video theo lifecycle; chỉ giữ quota/sample claim và audit metadata đã quy định. | Core private object storage + PostgreSQL; quota/slot ledger do module sở hữu tương ứng quản lý. |

**Giới hạn vận hành:** một full-video request có tối đa 15 scene × 3 inference attempts = 45 lần thử scene. Mỗi request được nhận đã tiêu thụ quota, kể cả provider/technical/safety failure; cost-cap/circuit-breaker đóng admission cho request mới, không dừng giữa chừng công việc đã reserve bình thường. Trần GPU-second/request và quota mức included phải được benchmark synthetic và cấu hình trước khi bật live demo. AI job có deadline 6 giờ từ accepted admission, tính cả queue. Video output mục tiêu 30–90 giây không bảo đảm đạt mọi quality case; consistency gate phải chặn output lỗi thay vì lặng lẽ thay tranh gốc.

### 6.3 Ứng viên AI và cổng triển khai

| Stage | Ứng viên | Hosting đề xuất | Trạng thái |
|---|---|---|---|
| ASR | Adapter faster-whisper hiện có | Modal L4 ứng viên | Chỉ dùng sau khi chốt version và đo chất lượng/độ trễ tiếng Việt |
| VLM | Ứng viên Qwen2.5-VL-7B | Modal L4; chỉ dùng GPU lớn hơn nếu benchmark yêu cầu | Chưa là mặc định; bằng chứng hiện có của Qwen3-VL là NO_GO |
| Story LLM | Ứng viên Qwen2.5-7B | Modal L4 | Cần xác minh schema story, safety, độ trễ và license |
| Teacher Sketch line-art generator | Provider port cho sinh ảnh line-art từng bước; model/checkpoint chưa chọn | Modal L4 là ứng viên; hosting chỉ chốt sau POC synthetic | Riêng với story-video; không nhận profile/ảnh trẻ và không trừ video quota |
| Structured output | Pydantic v2 + JSON Schema có version | API/worker Python | Bắt buộc cho VLM, story/storyboard, Character Bible, sketch deck và safety result |
| Reference/image preparation | Python + OpenCV + Pillow; SAM/SAM2 tùy chọn | Worker CPU/GPU theo benchmark | Tạo derived asset có hash/lineage; segmentation không bắt buộc V1 |
| Giọng kể tiếng Việt | Ứng viên VieNeu-TTS | Modal L4 | Cần xác minh giọng người lớn trung tính, đồng bộ phụ đề và license |
| Image-to-video | Pipeline self-host chính thức LTX-2.5 | Modal GPU L40S (48 GB) | Chủ sở hữu chọn loại GPU; model/runtime cụ thể và chi phí/độ trễ chưa benchmark |
| Kiểm tra consistency scene | OpenCV metrics + VLM/vision adapter có version | Modal L4 ứng viên hoặc worker CPU cho bước không cần GPU | Kiểm tra identity/color/style/action anchor sau khi sinh scene; chặn nếu sai ngưỡng hoặc kết quả không xác định |
| Safety trên video hoàn chỉnh | Safety policy/model có version + kiểm tra frame, narration và phụ đề | Modal L4 ứng viên hoặc worker CPU theo POC | Chạy sau composition/TTS/subtitles; fail closed nếu coverage thiếu, có vi phạm hoặc kết quả không xác định; không cấp playback token |
| Ghép video | FFmpeg | Container worker local | Pin binary và kiểm tra output |

Tài liệu LTX chính thức nêu yêu cầu tối thiểu từ 32 GB VRAM; Modal liệt kê L40S với 48 GB GPU RAM và L4 là lựa chọn GPU nhỏ hơn. Đây là cơ sở chọn L40S cho LTX, nhưng không chứng minh pipeline LTX đã deploy/benchmark thành công. [Yêu cầu LTX](https://docs.ltx.io/open-source-model/getting-started/system-requirements), [hướng dẫn GPU Modal](https://modal.com/docs/guide/gpu).

<a id="srs-7"></a>
## 7. Yêu cầu chức năng

Mức ưu tiên: **M** = bắt buộc trong baseline sản phẩm; **S** = cần thiết để chạy demo end-to-end; **G** = cổng triển khai chưa hoàn tất.

Danh mục hiện có 80 FR riêng theo ID. AI Sketch cho Teacher là một luồng yêu cầu/job riêng với StoryRun; không mở rộng actor/subject story thành nhiều trẻ.

### 7.1 Danh tính và hồ sơ dùng chung

| ID | Ưu tiên | Yêu cầu |
|---|---|---|
| FR-C-01 | M | Xác thực Parent và Teacher bằng tài khoản Firebase Authentication tách biệt; backend xác minh ID token và xác định account scope độc quyền theo issuer/UID. Từ chối yêu cầu role/setup không hợp lệ bằng phản hồi tổng quát `ACCOUNT_SETUP_UNAVAILABLE`, không tiết lộ UID đã đăng ký ở scope nào; client không thể tự cấp hoặc đổi role claim. |
| FR-C-02 | M | Từ chối run request không có profile trẻ hoặc có nhiều hơn một profile. Không nhận danh sách profile, group hoặc lớp làm subject của run. |
| FR-C-03 | M | Thực thi tối đa một run đang hoạt động trên mỗi owner hiện hành bằng unique constraint/concurrency ở database. Khóa dùng Parent account hoặc Teacher hiện hành qua `active_owner_parent_account_id`/`active_owner_teacher_id`; tách khỏi creator provenance. `DRAFT` và `VIDEO_ADMISSION_PENDING` chiếm khóa; state hoàn tất/hủy/abandon nhả khóa. |
| FR-C-04 | M | Tách owner scope hồ sơ Parent khỏi hồ sơ Teacher thuộc tổ chức. Không tạo chức năng liên kết hoặc tra cứu chéo scope. |
| FR-C-05 | M | Lưu thay đổi hồ sơ thành revision bất biến; giữ tuổi theo tháng/nhóm tuổi, sở thích, quan sát, thành tích, trải nghiệm ngoài app và nguồn thông tin nếu có. |
| FR-C-06 | M | Lưu riêng lịch sử run do app tạo và trải nghiệm ngoài app do người lớn nhập. Cho phép người lớn duyệt giá trị tối thiểu đưa vào snapshot từng run. |
| FR-C-07 | M | Giới hạn dữ liệu nhu cầu hỗ trợ theo quyền hồ sơ, mặc định loại khỏi AI context; không suy diễn chẩn đoán. |
| FR-C-08 | M | Cho người lớn hủy run chưa hoàn tất hoặc xóa run đã hoàn tất qua lifecycle. Lệnh hủy run chưa hoàn tất phải nhả khóa active ngay; thu hồi upload/playback, hủy job best-effort, xóa nội dung liên kết và báo tiến trình purge. Không hoàn quota request video đã nhận; giữ metadata quota tối thiểu và Teacher sample claim đã thành công. |
| FR-C-09 | S | Mỗi asset có metadata riêng và lineage nguồn/hash/derived bất biến; không lưu binary trong relational row hoặc JSON không giới hạn. |
| FR-C-10 | M | Cho chủ hồ sơ Parent hoặc Teacher/actor được tổ chức phân quyền yêu cầu xóa hồ sơ; thu hồi quyền profile/run ngay và hiển thị trạng thái đến khi purge nội dung liên kết. Chính sách xóa tài khoản và vai trò xóa hồ sơ Teacher phải chốt trước khi dùng dữ liệu thật. |
| FR-C-11 | M | `DRAFT` và mọi state cần người lớn đều là adult-wait khi không có AI job; tại +144 giờ tạo một inbox reminder, thử push best-effort và gửi email best-effort nếu owner hiện tại có địa chỉ đã xác minh; tại +168 giờ `VIDEO_READY` thành COMPLETED, state chờ khác thành ABANDONED. Nhả khóa owner và giữ nội dung đến khi người dùng xóa; lỗi gửi không chặn run closeout và run đóng không resume. `VIDEO_ADMISSION_PENDING` không phải adult-wait; từ chối admission trả run về `SCRIPT_REVIEW` và bắt đầu wait mới. Deadline generation là sáu giờ từ `accepted_at`, gồm queue và mọi stage (Q133, Q136). |
| FR-C-12 | M | Ảnh, audio và file giáo án upload-resume lưu session/receipt bền vững trong `core.upload_sessions` và `core.upload_parts`, không nhồi vào `core_asset_metadata`. Mỗi app chunk tối đa 4 MiB là object riêng qua PutObject; session gắn principal/scope/purpose, expected media/size/hash, idempotency và expiry. Chunk cùng số/hash idempotent; cùng số khác hash trả conflict. Backend xác minh part liên tục, byte tổng và SHA-256 từng part/toàn asset, lắp ráp bounded stream rồi ghi asset cuối bằng một PutObject; không gọi S3 Multipart Upload API. Chỉ asset hoàn chỉnh, media-validated và AV-clean mới dùng được. Rate limit tách control/status/chunk request, số session đồng thời và unique bytes/phút; retry chunk đã nhận không tính lại byte budget. Client không nhận credential/endpoint MinIO. |

### 7.2 Luồng Phụ huynh

| ID | Ưu tiên | Yêu cầu |
|---|---|---|
| FR-P-01 | M | Khôi phục luồng Parent Android trên nền hiện tại apps/mobile; dùng apps/ui-mobile làm nguồn tham khảo hành vi/giao diện. |
| FR-P-02 | M | Cho Parent tạo/chọn hồ sơ thuộc mình và gửi một ảnh tranh từ camera hoặc thư viện. |
| FR-P-03 | M | Nhận ý tưởng dạng chữ, giọng nói tối đa 2 phút/20 MB hoặc cả hai; dùng Whisper chuyển giọng nói thành chữ và yêu cầu người lớn sửa/xác nhận. |
| FR-P-04 | M | Phân tích ảnh tranh và cho người lớn sửa chủ thể; khi sửa, tạo revision diễn giải VLM mới. |
| FR-P-05 | M | Sau video, hiển thị một hoặc nhiều hoạt động ngoài trời gắn với lesson version, gồm vật liệu/cách làm/ghi chú; activity catalog thêm có thể được đề xuất bởi AI nhưng cần review. Không yêu cầu Parent chọn activity trước khi tạo video. |
| FR-P-06 | M | Tạo context run tối thiểu từ revision hồ sơ đã chọn và yêu cầu người lớn xác nhận trước khi AI tạo story. |
| FR-P-07 | M | Cho phép tối đa ba lần AI viết lại story sau bản đầu theo gợi ý của phụ huynh; không có điều khiển sửa trực tiếp scene/script. |
| FR-P-08 | M | Yêu cầu người lớn xác nhận script/storyboard cuối trước khi tạo video. Hiển thị video ở VIDEO_READY ngay sau khi qua kiểm tra; giữ run active đến khi Parent bấm Hoàn tất/Tạo lại hoặc đủ 168 giờ adult-wait idle, khi run tự hoàn tất; không yêu cầu duyệt video cuối. |
| FR-P-09 | M | Cho người lớn đánh dấu video không phù hợp và quay lại xem script; giới hạn hai lần tạo lại chất lượng đầy đủ sau video đầu. Ẩn video bị từ chối khỏi playback ngay khi request tạo lại được chấp nhận; giữ nội bộ đến khi xóa run. |
| FR-P-10 | S | Hiển thị stage và lỗi dễ hiểu, có thể khôi phục; không đưa prompt/diagnostic model vào UI. |
| FR-P-11 | S | Trong drawing session, Parent có thể bật hoặc bỏ qua một AI line-sketch guide 3–5 bước cho chủ đề chung và độ khó đơn giản. Chỉ gửi topic/độ khó cùng phiên bản hợp đồng guide; không gửi dữ liệu hồ sơ, tuổi cụ thể, giọng nói, ảnh hay tranh trẻ. Chỉ hiển thị output đã qua kiểm tra schema, line-art, an toàn, media và malware/AV; output chỉ người yêu cầu được xem, có provenance và là asset tạm với expiry/cleanup. Không gắn với profile/StoryRun, không tiêu video quota và không chặn capture khi skip/lỗi/timeout/limit/output rejection. Chủ thể tranh trẻ tiếp tục được review sau capture. |

### 7.3 Luồng Giáo viên và tổ chức

| ID | Ưu tiên | Yêu cầu |
|---|---|---|
| FR-T-01 | M | Cung cấp luồng Teacher trên web hiện có apps/teacher-ui. |
| FR-T-02 | M | Cho admin tổ chức được phân quyền tạo lớp trong capacity, quản lý roster và phân công chính xác một Teacher phụ trách mỗi lớp. |
| FR-T-03 | M | Cung cấp 10 slot lớp trong subscription cơ bản trả phí của mỗi tổ chức, cộng slot đã mua; ngăn tạo lớp đồng thời vượt capacity đang hiệu lực. |
| FR-T-04 | M | Cho Teacher tạo hồ sơ trẻ bằng form nhanh có cấu trúc; cho phép tên hiển thị trùng nhau và dùng ID nội bộ opaque. |
| FR-T-05 | M | Giới hạn mỗi hồ sơ Teacher ở tối đa một enrollment lớp hoạt động; khi chuyển lớp thì đóng và lưu enrollment trước đó. |
| FR-T-06 | M | Nhận giáo án PDF/PPTX/DOCX tối đa 25 MB và 100 trang/slide; từ chối file mã hóa/password; trả OCR_NOT_SUPPORTED với trang scan. |
| FR-T-07 | M | Giữ file giáo án gốc và provenance của text trích xuất; cho sửa thành revision text bất biến mới; yêu cầu Teacher xem và duyệt trước khi dùng. |
| FR-T-08 | M | Tạo occurrence và plan cho buổi dạy, pin reusable lesson/version nếu được chọn; lesson dùng như preset. Một occurrence có thể giữ nhiều activity; Teacher sample ghim một activity và một child/run như baseline. |
| FR-T-09 | M | Hoạt động Teacher tự nhập chỉ tồn tại trong occurrence đó và cần Teacher phụ trách xác nhận bằng safety checklist. |
| FR-T-10 | M | Cho Teacher dùng child đại diện được chọn ngẫu nhiên từ roster đủ điều kiện, xác nhận một activity đã duyệt và snapshot context tối thiểu cho run. |
| FR-T-11 | M | Cho Teacher chụp bằng camera trình duyệt hoặc tải ảnh chụp bằng điện thoại. |
| FR-T-12 | M | Cho Teacher đặt hướng story theo giáo án/plan lớp đã duyệt và yêu cầu tối đa ba lần AI viết lại; mỗi lần tạo video đều phải xác nhận script. |
| FR-T-13 | M | Thực thi tối đa một video mẫu phát được và đạt safety cho mỗi occurrence. Lỗi kỹ thuật hoặc safety block trước lần playback/claim đầu không chiếm slot. Sau claim đầu, không mở lại slot dù video bị từ chối/ẩn, các lần tạo lại thất bại/hết lượt, run bị xóa/hủy hoặc đổi Teacher. |
| FR-T-14 | M | Quyền run/media theo Teacher phụ trách hiện tại. Reassignment/offboarding là saga idempotent: BE1 fence/revoke quyền và token cũ ngay, lớp thành read-only; Story chuyển `active_owner_teacher_id`/lock trong transaction riêng; BE1 finalize chỉ sau Story receipt. Trong pending không Teacher nào xem content. Nếu Teacher mới có active run, Story trả conflict và saga phục hồi assignment/quyền cũ; nếu compensation mơ hồ, giữ pending/read-only để reconcile. `created_by_actor_ref` chỉ truy vết. Không hủy AI job hợp lệ chỉ vì đổi assignment. Kết quả chỉ được nhận nếu run/input/script/activity/occurrence hashes còn hợp lệ, cùng org/class, không cancel/delete và transfer receipt hiện hành chứng minh owner mới; assignment version cũ/creator không cấp quyền. |
| FR-T-15 | S | Hiển thị trạng thái và kết quả mẫu của từng occurrence; ở VIDEO_READY cho phép Teacher chiếu, Hoàn tất hoặc Tạo lại; sau 168 giờ adult-wait idle tự hoàn tất. Không có hành động chạy theo toàn roster/batch. |
| FR-T-16 | M | Chỉ Teacher phụ trách hiện tại mới có thao tác chiếu cho lớp. Ghi xác nhận occurrence có audit; cấp playback authorization ngắn hạn, không cấp capability dùng lại cho thành viên lớp. Đây không phải duyệt video cuối. |
| FR-T-17 | M | Cho phép admin tổ chức force-close conflicting Teacher run chỉ qua command emergency có reason bắt buộc và metadata audit. Đóng run thành ABANDONED, nhả active-owner lock, không xóa run/media hoặc cho admin xem nội dung; quota đã nhận và sample claim thành công vẫn còn. Force-close là bước tường minh trước khi retry reassignment, không phải hành vi tự động của ordinary reassignment. |
| FR-T-18 | M | Chỉ tạo Teacher Sketch Deck khi Teacher bật line-sketch guide trong session; nếu tắt thì không tạo job. Khi bật, deck revision dùng chung cho occurrence/plan đã duyệt, bao quát activity list và không nhận roster, profile hoặc tranh trẻ làm input. |
| FR-T-19 | M | Hiển thị deck trong Teacher web như bề mặt trình chiếu 16:9 nền trắng, ít chữ. Teacher điều khiển Back/Next, chọn activity/chủ thể trong plan, skip hướng dẫn và yêu cầu tạo lại một sketch. Không yêu cầu sửa text/layout/freehand hoặc xuất PPTX. Trẻ vẽ bằng giấy; video story của trẻ được mở/phát trong cùng occurrence sau khi pipeline video hoàn tất. |
| FR-T-20 | M | Pin deck vào plan revision/hash đã duyệt; khi plan thay đổi, đánh dấu deck cũ STALE và chặn trình chiếu cho đến khi có deck READY mới. Regenerate tạo revision bất biến mới và chỉ thay asset của sketch được chọn. Sketch AI dùng rate limit/cost cap riêng, không trừ hoặc ghi `billing.video_quota_usage`. |

### 7.4 AI story, video và playback

| ID | Ưu tiên | Yêu cầu |
|---|---|---|
| FR-AI-01 | M | Tạo job có kiểu/version cho lesson extraction/library-version draft/activity suggestion/visual asset/plan-to-deck/sketch-step regeneration, Parent line-sketch guide và cho story ASR, VLM image understanding, story/rewrite, storyboard, scene reference, video scene, consistency/safety validation, TTS, subtitle và composition. Mỗi job gắn đúng một target kind/ref/revision; Story/video target resolve đúng một trẻ từ StoryRun canonical, Lesson Sketch target không có child/profile subject, Parent guide target chỉ có generic topic/difficulty và không có profile/child/artwork refs. Không lưu subject ref lặp trong AI Job. |
| FR-AI-02 | M | Xác thực mọi model response bằng schema có version trước khi lưu/hiển thị. Từ chối output sai cấu trúc hoặc stale. |
| FR-AI-03 | M | Giữ tranh/audio/giáo án gốc và ghi source hash, model/profile revision, config hash, lý do và actor cho artifact dẫn xuất. |
| FR-AI-04 | M | Tạo storyboard 5–15 scene và video mục tiêu 30–90 giây do hệ thống chọn. |
| FR-AI-05 | M | Tạo story image-to-video cho một trẻ, dùng tranh đã chọn làm tham chiếu; giữ chủ thể dễ nhận biết cùng neo hình dáng/màu/phong cách theo mục tiêu chất lượng; không dùng hoạt ảnh tranh PixiJS. |
| FR-AI-06 | M | Kiểm tra decode/output từng scene và tiêu chí consistency nhân vật đã cấu hình. Scene lỗi tối đa hai retry kỹ thuật/validation tự động sau lần đầu. Hết retry thì báo lỗi an toàn và dừng run. |
| FR-AI-07 | M | Giới hạn hai full-video request tạo lại chất lượng sau request đầu trong cùng run; mỗi lần quay lại xem script và xác nhận. Mỗi request được chấp nhận tiêu thụ slot giới hạn và một unit quota, kể cả lỗi kỹ thuật/safety; retry scene không tiêu thụ thêm. |
| FR-AI-08 | M | Output MP4, 720p, 16:9, một giọng kể người lớn trung tính tiếng Việt, phụ đề tiếng Việt và không nhạc. |
| FR-AI-09 | M | Mở playback ngay khi qua kiểm tra kỹ thuật và safety gate tự động của video đã ghép; không yêu cầu người duyệt video cuối và không có download/export. Khi video bị đánh dấu không phù hợp và tạo lại được chấp nhận, ẩn output cũ khỏi playback. |
| FR-AI-10 | S | Cấp playback authorization ngắn hạn và kiểm tra lại quyền run ở mỗi lần playback. |
| FR-AI-11 | S | Theo dõi stage attempt, thời lượng, lỗi, GPU seconds và artifact ID nhưng không log nội dung người dùng. |
| FR-AI-12 | M | Áp dụng safety check có version cho transcript chữ/giọng nói, context giáo án trích xuất, script/storyboard, prompt scene, frame video đã ghép, toàn bộ transcript lời kể và text phụ đề. Xử lý instruction như dữ liệu, không phải quyền điều khiển. Chặn output không an toàn/không xác định khỏi review hoặc playback và trả mã lý do an toàn; không để lộ prompt nội bộ. |
| FR-AI-13 | M | Thực thi pipeline story-video theo BR-45: Character Bible/reference preparation từ một tranh, image-to-video LTX-2.5 qua Modal L40S cho từng scene, consistency validation, FFmpeg composition, TTS/subtitle generation và automated safety validation trước playback. Mỗi scene và mỗi full-video request tuân theo giới hạn retry/quota đã định; mọi stage là job bền vững, idempotent và kiểm stale theo hash/revision. |
| FR-AI-14 | M | Tạo deck/line-sketch theo versioned structured contract dựa trên toàn bộ plan/activity đã duyệt; validate schema, coverage, 3–5 bước mỗi hướng dẫn, layout hints, media type/size, age-safety và lineage trước khi hiển thị. Output phải chỉ dẫn theo lesson, không tự phát sinh activity không được duyệt; job không nhận profile/context/tranh trẻ; lỗi/stale/rejected output không được trình chiếu. Dùng provider adapter cho sketch generation, không ghim model chưa benchmark. |
| FR-AI-15 | S | Sinh Parent guide theo contract line-art có version từ generic topic/difficulty; xác thực topic allowlist, 3–5 bước tăng dần, nét rõ, schema, media bounds, malware/AV, age-safety và provenance trước khi hiển thị. Dùng target `PARENT_SKETCH_GUIDE`, trong đó request ID thuộc AI Job nên không cần aggregate/table Parent riêng; không có child/profile/photo/audio/artwork ref. Kết quả chỉ người yêu cầu được xem, là asset tạm, không gắn profile/StoryRun, có expiry/cleanup, rate/compute cap riêng; skip/failure/timeout/unsafe output không chặn luồng vẽ và không ghi video quota. |

### 7.5 Billing và thông báo

| ID | Ưu tiên | Yêu cầu |
|---|---|---|
| FR-B-01 | M | Lưu giá VND có version cho capacity tổ chức theo tháng/năm, gồm gói cơ bản trả phí có 10 slot và một đơn giá cho mỗi slot tăng thêm. Giá gói cơ bản/slot bổ sung là cấu hình thương mại, chưa chốt trong SRS. |
| FR-B-02 | M | Hỗ trợ vòng đời subscription tổ chức và adapter thanh toán định kỳ MoMo/VNPAY; loại VietQR khỏi V1. |
| FR-B-03 | M | Xác minh chữ ký callback provider, deduplicate provider event và đối soát invoice/subscription trong transaction. Không xem browser redirect là chứng từ thanh toán. |
| FR-B-04 | M | Kích hoạt capacity mua thêm sau xác minh thanh toán và tính phí prorate cho phần kỳ còn lại, không đổi ngày gia hạn. |
| FR-B-05 | M | Hỗ trợ tắt auto-renew, giữ quyền đến hết kỳ đã trả; V1 không tự tính hoàn tiền prorate. |
| FR-B-06 | M | Áp dụng grace gia hạn 7 ngày, sau đó hạn chế tạo lớp/run mới; vẫn cho truy cập lớp/roster/lịch sử và quản lý thanh toán hiện có. |
| FR-B-07 | M | Khi hạ capacity, bắt buộc chọn lớp; ghi sự kiện suspension có version/thời điểm cho từng lớp được chọn và chiếu trạng thái sang BE1 đúng kỳ hiệu lực. Lớp tạm ngưng chỉ đọc, mọi dữ liệu vẫn được giữ. |
| FR-B-08 | M | Gửi nhắc billing admin trong app/email trước hạn 7 ngày và 1 ngày; gửi thông báo khi thanh toán thành công/thất bại và khi hết grace. |
| FR-B-09 | S | Dùng notification outbox và retry giới hạn; deduplicate theo lịch/provider event. Hộp thư trong app là nguồn chuẩn; push/email là kênh giao best-effort. |
| FR-B-10 | M | Duy trì quota video theo tháng tách biệt giữa Parent account và Teacher organization. Billing `video_quota_grants` và `video_quota_usage` là nguồn entitlement/tiêu thụ chuẩn. Use case quota-admission của Billing phân bổ idempotent mỗi request được nhận vào một grant. AI Policy chỉ sở hữu metering/reservation tài nguyên nền tảng. Request đã nhận tiêu thụ một unit kể cả lỗi provider/kỹ thuật/safety; không hoàn quota; retry scene không tiêu thụ. Không ghi danh tính trẻ hoặc media vào ledger. |
| FR-B-11 | M | Trước Billing admission, application phải reserve budget GPU tối đa cấu hình được cho request qua AI Policy port bằng idempotency key và lease/expiry. Nếu không đủ budget thì trả `AI_COST_LIMIT_REACHED` trước khi request được nhận, không tiêu quota. Sau budget reservation, Billing kiểm tra quota trong transaction riêng; `VIDEO_QUOTA_EXCEEDED` không dispatch, không tạo usage row và khiến application giải phóng reservation. Nếu tiến trình dừng hoặc phản hồi không rõ, reconciler tra cứu receipt bằng idempotency key, hết hạn reservation chưa gắn với accepted request và không dispatch hai lần. Chỉ dispatch sau khi cả budget reservation và quota admission được xác nhận. Hết quota vẫn cho playback/quản lý dữ liệu đã lưu. Tính quota còn lại trong Billing từ grant hợp lệ trừ usage ledger bất biến; không lưu balance mutable. Ưu tiên included tháng hiện hành rồi top-up FIFO. |
| FR-B-12 | S | Cung cấp quota summary xác thực theo scope backend suy ra từ actor, gồm included tháng hiện tại/thời điểm hết hạn, top-up FIFO, đã cấp/đã tiêu thụ/còn lại và ranh giới kỳ; không làm lộ account hoặc run/trẻ khác. |
| FR-B-13 | S | Cho chủ tài khoản Parent và admin billing tổ chức mua unit quota bổ sung theo cấu hình qua payment adapter được duyệt. Chỉ phát entitlement sau event thanh toán xác minh/idempotent; số lượng/giá do server kiểm tra, invoice/grant bất biến. Top-up là giao dịch mua một lần, không tự gia hạn (Q120). |
| FR-B-14 | M | Gửi reminder hết hạn run, cập nhật job và billing qua hộp thư trong app, push web/mobile và email. Run reminder chỉ gửi email tới địa chỉ đã xác minh của owner hiện tại (Q136); billing notice gửi tới admin thanh toán theo cấu hình. Web dùng Web Push. Android push provider chưa được chọn; chỉ bật một adapter sau khi synthetic POC chứng minh provider, distributor, cài đặt/phân phối ứng dụng, opt-in, thu hồi token và trải nghiệm nền trên thiết bị mục tiêu. Không mặc định UnifiedPush hay Firebase Messaging; Firebase Messaging bị loại theo repository rule. Payload push chỉ có loại thông báo và opaque route/ref; không có tên trẻ, story, transcript, media hay playback URL. Email/delivery record không ghi raw recipient address vào nội dung notice hoặc log. Push không thay thế inbox/polling; inbox luôn nhận notice dù push không khả dụng. |

### 7.6 Nền tảng và vận hành

| ID | Ưu tiên | Yêu cầu |
|---|---|---|
| FR-O-01 | M | Dùng modular monolith với domain module có owner rõ và dependency theo clean architecture. |
| FR-O-02 | M | Version hóa API, queue, event, asset và profile-scope contract. Từ chối major version không được hỗ trợ. |
| FR-O-03 | M | Dùng PostgreSQL làm nguồn dữ liệu nghiệp vụ/job; Redis/RQ làm kênh dispatch/backpressure/rate limit; MinIO làm object storage riêng tư local. |
| FR-O-04 | M | Chỉ cấu hình provider credential trong backend worker/runtime secret. Mobile và Teacher browser không nhận secret/endpoint Modal, payment, object storage hoặc database. |
| FR-O-05 | M | Trả error envelope an toàn, ổn định, có correlation ID, retryability và thời gian chờ lại tùy chọn. |
| FR-O-06 | M | Áp dụng giới hạn server-side theo account/IP/API, đồng thời giới hạn queue/GPU AI và deadline provider hữu hạn cho từng stage/toàn run. Thông số demo đầu tiên ở §10.4, cần benchmark. |
| FR-O-07 | S | Cung cấp health/readiness probe, queue visibility, dashboard và log đã redact để operator đọc trong Docker Compose. |
| FR-O-08 | S | Tài liệu hóa backup/restore PostgreSQL và MinIO thủ công với dữ liệu tổng hợp; restore phải giữ lineage và metadata liên kết. |
| FR-O-09 | M | Cấp role Parent/Teacher từ server. Teacher role và tổ chức cần quy trình provision/phân công được phép; client không tự gắn claim Teacher/admin. Trước launch cần mô tả khôi phục tài khoản, mời/kích hoạt Teacher và bootstrap tổ chức. |
| FR-O-10 | M | Tách `run_state` nghiệp vụ khỏi `job_state`/`job_stage` của ASR, VLM, story và video, đồng thời trả trạng thái VideoGeneration admission riêng. Status API trả cả trạng thái cùng revision/version, deadline, timestamp cập nhật, safe error code, retryability và human action required để UI phân biệt admission/AI đang chạy, chờ người lớn hay đã kết thúc; admission reconciliation không phải adult-wait. AI job deadline là 6 giờ, adult-wait idle deadline là 168 giờ. |

<a id="srs-8"></a>
## 8. Yêu cầu phi chức năng

Danh mục baseline có 33 NFR; bổ sung NFR-34–NFR-38 cho platform v2.3, tổng cộng 38 NFR riêng theo ID; các mục đánh giá AI, chi phí và hiệu năng là cổng benchmark, không phải kết quả đã đo.

Các yêu cầu này là mục tiêu cho demo local bằng dữ liệu tổng hợp, không phải cam kết đã đo hoặc SLA production. Chỉ xác nhận giá trị tải/độ trễ sau khi có kế hoạch triển khai được duyệt và benchmark synthetic.

| ID | Nhóm | Ưu tiên | Yêu cầu/mục tiêu |
|---|---|---|
| NFR-01 | Kiến trúc | M | Domain code không import FastAPI, SQLAlchemy, Redis, S3/MinIO, Firebase Admin, Modal SDK, payment SDK hoặc UI package. Use case phụ thuộc port; adapter phụ thuộc hướng vào trong. |
| NFR-02 | Phân quyền | M | Mọi truy cập profile/class/run/asset/playback được server phân quyền theo actor và scope/assignment hiện hành. Mặc định từ chối. |
| NFR-03 | Riêng tư | M | Demo chỉ dùng dữ liệu tổng hợp. Redact payload khỏi log/trace/metric. Loại tên, byte ảnh/audio, transcript, prompt, signed URL và ghi chú hỗ trợ. |
| NFR-04 | Tách dữ liệu | M | Owner hồ sơ Parent tách khỏi owner tổ chức Teacher; không dùng polymorphic FK có thể nối nhầm hai loại profile. |
| NFR-05 | Toàn vẹn dữ liệu | M | Constraint database thực thi một trẻ/run và một run/current-owner. Khóa theo active-owner field riêng khỏi creator; reassignment BE1/Story dùng durable idempotent transfer phases thay cho cross-module atomic transaction, fence quyền cũ ngay, không cấp quyền mới trước lock-transfer receipt; conflict trả 409, emergency admin force-close cần audit. Enrollment, assignment, sample, rewrite/video cap, quota và payment callback vẫn có invariant/idempotency riêng. |
| NFR-06 | Nhất quán bất đồng bộ | M | Mỗi job idempotent, có version và gắn hash input bất biến. Kết quả stale không ghi đè run/script/profile/lesson revision mới. |
| NFR-07 | Khả năng phục hồi | M | Restart local Compose vẫn giữ PostgreSQL/MinIO volume. Có hướng dẫn backup/restore thủ công. Không tuyên bố cloud uptime. |
| NFR-08 | Hiệu năng | S | Mục tiêu đầu: request đọc có xác thực, không gọi AI, p95 ≤ 500 ms; command/job enqueue được chấp nhận p95 ≤ 2 giây, không tính upload/inference. Benchmark bằng tải tổng hợp trước triển khai. Chưa cam kết độ trễ AI trước benchmark model/GPU. |
| NFR-09 | Media | M | Kiểm tra MIME theo nội dung, extension, kích thước, số trang, decode và checksum; giữ bản gốc riêng tư cùng bản dẫn xuất có provenance. |
| NFR-10 | Playback | M | Yêu cầu playback authorization ngắn hạn và đúng scope. Không phát hành object URL vĩnh viễn hoặc endpoint liệt kê/tải file. |
| NFR-11 | Observability | M | Phát structured log, trace và metric đã redact cho API, queue, job, stage, provider latency/failure, GPU, storage, billing notice và rate-limit event. |
| NFR-12 | Rate limit | M | Trả HTTP 429 cùng Retry-After khi vượt giới hạn; khóa rate theo account/IP/operation, không theo ID trẻ hoặc content. |
| NFR-13 | UX dễ hiểu | M | Stage và lỗi dễ hiểu với người lớn không chuyên, bằng tiếng Việt ở luồng V1; gom xác nhận tiền quyết liên quan vào ít màn hình dễ tiếp cận nhưng không bỏ review bắt buộc; không hiển thị stack trace model. |
| NFR-14 | Bảo trì | M | Contract có version kiểm tra được kiểu; state domain tường minh; repository chuyển row thành domain object; route/worker adapter mỏng; tránh shared model khổng lồ và SQL ghi chéo module. |
| NFR-15 | Bảo mật | M | Secret chỉ từ file local bị ignore hoặc runtime secret manager; .env.example chỉ có placeholder. Firebase chỉ dùng Authentication. |
| NFR-16 | An toàn migration | M | Bắt đầu bằng expand/backfill không phá hủy; sau migration được duyệt riêng mới chuyển key/nullability/check bằng dual-read/write và bằng chứng parity. Giữ row/ID và tương thích đến khi chứng minh được; baseline này không drop bảng/row legacy hay đổi nghĩa ID. Không tuyên bố mọi thay đổi đều additive. |
| NFR-17 | Chịu lỗi provider | M | Timeout/provider unavailable/response sai cấu trúc/hết retry thành job state có kiểu; không tự động chuyển sang model/provider khác. |
| NFR-18 | Riêng tư backup | M | Backup chỉ chứa dữ liệu demo tổng hợp đến khi có chính sách dữ liệu thật và thiết kế backup an toàn được duyệt riêng. |
| NFR-19 | Chất lượng/an toàn media sinh | M | Bộ đánh giá synthetic đo mức nhận ra chủ thể, neo màu/hình, mạch scene, đồng bộ lời kể/phụ đề, format output và độ phủ safety gate trước khi nâng model. Chạy kiểm tra kỹ thuật/an toàn trước playback; người lớn vẫn có thể đánh dấu video đạt kỹ thuật nhưng không phù hợp. Không cam kết giữ nhận diện hoàn hảo hoặc classifier hoàn hảo. |
| NFR-20 | Khả năng tiếp cận | M | Luồng chính Parent/Teacher hỗ trợ screen reader/semantic label, thao tác bàn phím trên web, focus nhìn thấy được, tương phản đủ, tóm tắt lỗi bằng text và caption/phụ đề. Nếu từ chối quyền camera/mic vẫn có upload/nhập chữ thay thế. |
| NFR-21 | Ngôn ngữ | M | Luồng người lớn, nhãn trạng thái, validation và lỗi an toàn V1 bằng tiếng Việt. API code ổn định, không phụ thuộc ngôn ngữ; format ngày/tiền theo locale/timezone nhưng giá trị lưu theo UTC/VND. |
| NFR-22 | Tải demo | S | Cấu hình benchmark synthetic đầu tiên dự kiến: 10 client xác thực đồng thời, mỗi client tối đa một run; một run video LTX chạy đồng thời và tối đa năm video chờ toàn cục. Scheduler chọn luân phiên (round-robin) các owner scope đủ điều kiện, FIFO trong từng scope, giới hạn số việc chờ mỗi scope theo cấu hình để một Parent account/tổ chức không chiếm cả hàng đợi. Hiển thị trạng thái/thời gian chờ; queue đầy thì từ chối khởi chạy an toàn. Đây là kích thước demo local đề xuất, không phải SLA production. |
| NFR-23 | An toàn nội dung trẻ em | M | Safety policy có version và thực thi server-side cho input/output. Không chỉ dựa vào prompt model hoặc UI; review người lớn bổ sung nhưng không thay thế validation tự động. |
| NFR-24 | Bảo mật nhiều lớp | M | Có threat model STRIDE cho client/API, DB, queue, object store, Modal, payment và notification boundary. Bắt buộc MFA cho org/billing admin; Android Play Integrity qua backend (không dùng Firebase App Check); quét antivirus file ở quarantine trước parser/model; PostgreSQL RLS và role least-privilege là defense-in-depth. Runtime DB role không sở hữu bảng, không có BYPASSRLS. |
| NFR-25 | Kiểm soát chi phí AI | M | Trước khi nhận full-video request, application phải reserve đủ GPU-second theo mức trần per-request đã benchmark và mức daily/owner budget còn lại qua AI Policy port. Nếu không reserve được thì từ chối trước Billing admission, không tiêu quota. Sau khi request được nhận, reservation bảo vệ request khỏi ordinary daily-cap exhaustion; circuit breaker đóng admission mới, không cắt các request đã reserve. Chỉ emergency safety/operator abort mới có thể dừng request giữa chừng; theo Q128 unit đã nhận không được hoàn. Giới hạn scene/attempt/byte/concurrency/queue là bắt buộc; alert không thay hard cap. |
| NFR-26 | Push notification | S | Inbox là trạng thái chuẩn; push là best-effort, payload tối thiểu và có dedupe. Mất/quyền push bị từ chối không ngăn polling/foreground refresh; không dựa vào notification delivery để đổi business state. |
| NFR-27 | Availability, SLO và phục hồi | S | Baseline demo local: container cần báo readiness trong 10 phút sau `docker compose up`; PostgreSQL/MinIO backup thủ công có RPO mục tiêu ≤24 giờ và RTO mục tiêu ≤4 giờ trong diễn tập local. Đây là mục tiêu đề xuất, chưa được đo. Production availability mục tiêu đề xuất 99.5%/tháng cho API control-plane, không gồm provider/Modal; RPO/RTO production chưa chốt và bắt buộc có ADR/owner approval trước deploy. SLO AI end-to-end chỉ được chốt sau benchmark L40S; deadline cứng hiện là 6 giờ/job. |
| NFR-28 | Dung lượng và capacity | M | File MP4 đầu ra ≤256 MiB; input/run caps theo §10.4/§24.2. Capacity phải được lập bằng công thức `monthly_object_bytes = accepted_runs × (source_assets + retained_intermediates + final_outputs)` và `monthly_gpu_seconds = accepted_video_requests × measured_p95_gpu_seconds/request`; phải đưa số lượt và concurrency vào benchmark/cap trước demo live. Số quota included và số run/tháng chưa chốt nên chưa có dự toán storage/GPU production. |
| NFR-29 | Accessibility | S | Teacher Web hướng tới WCAG 2.2 AA; Android đánh giá theo WCAG2ICT/platform accessibility guidance. Verification gồm automated accessibility scan và manual keyboard/screen reader/contrast/focus checks cho luồng chính; đây là mục tiêu thiết kế, chưa phải chứng nhận độc lập. |
| NFR-30 | Tương thích client | M | Android support floor là API 29 (Android 10) theo cấu hình repository; target/compile SDK hiện tại phải tiếp tục theo Gradle pin đã kiểm kê. Teacher Web hỗ trợ hai phiên bản stable gần nhất của Chrome và Edge desktop. Release checklist ghi OS/browser version và thực hiện smoke verification trước demo. |
| NFR-31 | Giới hạn lưu dữ liệu | M | Synthetic demo tuân theo Q66/Q129/Q133: run hoàn tất/abandoned và media giữ đến khi người dùng chủ động xóa; không có auto-purge theo ngày. Đây là lựa chọn demo, không được áp dụng cho dữ liệu trẻ thật/production. Trước real-data gate phải chốt retention tối đa theo loại dữ liệu, backup expiry, DSR, xóa khỏi backup hoặc crypto-shredding và bằng chứng hoàn tất xóa. |
| NFR-32 | Upload chịu gián đoạn mạng | M | Tải ảnh tối đa 20 MiB, audio tối đa 20 MB/2 phút và lesson tối đa 25 MB phải hỗ trợ tiếp tục sau khi app/browser hoặc kết nối bị gián đoạn. Dùng application chunk tối đa 4 MiB, mỗi chunk là object PutObject độc lập; `core.upload_sessions`/`core.upload_parts` lưu session/receipt bền vững. Resume chỉ gửi phần thiếu; exact retry không cộng unique-byte budget. Backend kiểm tra thứ tự, kích thước, SHA-256 từng phần/toàn file, lắp ráp bounded stream rồi ghi asset hoàn chỉnh bằng một PutObject đã biết kích thước (demo file tối đa 25 MB, dưới ngưỡng single-PUT 128 MiB được nêu trong tài liệu MinIO Go SDK; cần POC trên đúng phiên bản client). Đây không phải S3 Multipart Upload API. |
| NFR-33 | Khả năng trình chiếu Teacher | M | Teacher Sketch Deck hiển thị ổn định trên viewport 16:9 từ 1280×720 trở lên, co giãn theo máy chiếu, giữ line-art tương phản cao trên nền trắng và dùng text ngắn. Control Back/Next/skip/select activity có semantic label/focus; nội dung không phụ thuộc riêng màu sắc; chữ/control đạt contrast WCAG 2.2 AA. Xác minh bằng render review trên viewport 16:9, keyboard-only và kiểm tra chiếu thử. |

### 8.1 Ưu tiên, verification và phân pha

Ưu tiên `M` (Must) và `S` (Should) thể hiện mức cần thiết trong pha đích, không phải trạng thái duyệt. Functional catalogue (§7) và NFR catalogue (§8) ghi mức ưu tiên cho từng ID. Ma trận §30.3 là nguồn truy vết theo ID cho nguồn/lý do, UC/phạm vi, entity owner, phương pháp xác minh, pha và trạng thái. “Verification” là phương pháp nghiệm thu dự kiến, không phải bằng chứng test đã chạy. Trạng thái requirement là `DRAFT` cho đến khi chủ sở hữu duyệt tài liệu; nguồn Q/BR không đồng nghĩa với nghiệm thu triển khai.

| Pha kỹ thuật đề xuất | Kết quả kiểm chứng | Requirement điển hình | Ranh giới |
|---|---|---|---|
| P0 — Nền tảng/contract | Modular monolith, auth/scope, owner schema, outbox/job, Docker, synthetic fixtures, security basics, quota admission, hard cost reservation và resumable upload contract | FR-C, FR-O, NFR-01–18, NFR-24–28, NFR-32 | Không bỏ quota/cost reservation khỏi video flow; upload adapter POC cần trước media integration; provider payments thật chưa cần cho fixture |
| P1 — Parent vertical slice | Parent profile → ảnh/ý tưởng → subject/context review → story review → video Modal → playback → lesson activity list theo quyền → delete, trên dữ liệu tổng hợp; Parent có thể mang tham chiếu lesson-version opaque tùy chọn qua cổng module Lesson; nếu không có lesson thì run vẫn chạy, không có lesson activity list và không fallback. VIDEO_READY sau kiểm tra kỹ thuật/an toàn, không cần xem hết; kiểm quyền hiện hành, lesson bị thu hồi/gỡ phát hành thì ẩn list, không ảnh hưởng video và không fallback. Vị trí lưu vật lý tham chiếu còn mở. [Còn mở cho thiết kế vật lý: vị trí lưu vật lý tham chiếu lesson-version]. | FR-P, FR-AI, subset FR-C/NFR, resumable media upload | Không dùng dữ liệu trẻ thật; quota fixture/config được cấp từ Billing |
| P2 — Teacher vertical slice | Organization/class/roster → profile → lesson import/review → occurrence/one child sample → script confirmation → video/chiếu/reassignment | FR-T, shared FR-AI/FR-C | Một child/activity/run; không classroom collaboration/batch |
| P3 — Billing và notification | MoMo/VNPAY sandbox, class capacity, recurring/subscription state, quota top-up, inbox/email/Web Push, Android provider POC | FR-B, FR-O-09, FR-B-14 | Sandbox trước merchant production; Android push chỉ promote sau delivery POC |
| P4 — Production readiness | Hosting/region, SLO/RPO/RTO, legal/retention/DSR/DPIA, billing/tax, threat model evidence, migration rehearsal | NFR-24–32; §29.2 | Dữ liệu trẻ thật/production bị chặn đến khi từng gate có owner và bằng chứng |

Toàn bộ luồng Parent và Teacher, quota sản phẩm, video pipeline và các business rules đã xác nhận vẫn thuộc target V1. Bảng pha là thứ tự build/verification được đề xuất, không xóa requirement hoặc tuyên bố người dùng đã duyệt một kế hoạch release.

<a id="srs-9"></a>
## 9. Kiến trúc phần mềm đích

### 9.1 Clean architecture và ranh giới module

Giữ modular monolith cho đến khi số liệu runtime chứng minh cần tách dịch vụ deploy độc lập. Dependency hướng vào trong:

| Layer | Trách nhiệm | Không phụ thuộc vào |
|---|---|---|
| Domain | Hồ sơ Parent, roster/capacity tổ chức, lesson occurrence, story run, review, billing policy và state machine | Framework, ORM/database, queue, cloud provider, model SDK, HTTP/UI |
| Application | Command/query, transaction, điều phối use case, phân quyền, port, idempotency và xử lý stale result | Hạ tầng client cụ thể |
| Contracts | Schema có version cho HTTP/event/job/asset/provider request/response; validation tại ranh giới | ORM row hoặc provider payload chưa xác thực |
| Interfaces | FastAPI route mỏng, queue consumer, adapter command thông báo theo lịch | Rẽ nhánh nghiệp vụ, SQL trực tiếp, gọi thẳng AI/payment SDK |
| Infrastructure | SQLAlchemy/Alembic, PostgreSQL, Redis/RQ, MinIO, Firebase token verification, Modal, MoMo/VNPAY, email, OTel | Sở hữu business rule của Domain |
| Apps | Parent React Native, Teacher React web, adapter camera/audio thiết bị, screen và generated contract type | Database/provider credentials hoặc truy cập thẳng provider/storage |

Mỗi module sở hữu bảng và quyền ghi của mình. Giao tiếp module dùng command/event có version với opaque reference qua application port. Module không truy vấn bảng riêng module khác để tự suy ra quyền hoặc sửa state.

### 9.2 Cấu trúc code đề xuất

    apps/
      mobile/                         Parent Android (React Native + TypeScript)
      teacher-ui/                     Teacher và tổ chức (React + Vite)
    backend/src/sketch2life/
      domain/
        identity/ organization/ roster/ parent_profiles/ profile_context/
        lesson/ story/ billing/ notifications/ assets/
      application/
        commands/ queries/ services/ ports/ policies/
      contracts/
        http/v1/ events/v1/ jobs/v1/ schemas/
      interfaces/
        http/routers/ dependencies/ workers/ schedules/
      infrastructure/
        persistence/ object_storage/ queue/ identity/
        ai/modal/ payments/momo/ payments/vnpay/ email/ telemetry/
    backend/alembic/                   Migration có version, nhóm theo owner bảng
    infra/                             Docker Compose profile và monitoring config

Đây là cấu trúc đích đề xuất, không khẳng định package hiện đã tồn tại. Mỗi khái niệm nghiệp vụ thuộc đúng một domain module. SQLAlchemy row không phải domain entity; mapping thực hiện tại ranh giới repository. Worker completion là application command, xác minh expected revision trước khi lưu.

### 9.3 Baseline công nghệ

| Phạm vi | Baseline/đích đề xuất | Lý do/trạng thái |
|---|---|---|
| Parent Android | React Native 0.87 + TypeScript đang pin trong apps/mobile | Giữ baseline repository; khôi phục hành vi tham khảo apps/ui-mobile. Không mô tả 0.87 là bản upstream mới nhất. |
| Teacher web | React 19 + Vite 8.3 đang pin trong apps/teacher-ui | Giữ app hiện tại, đổi luồng sản phẩm cộng tác sang luồng Teacher riêng. |
| Backend | Mục tiêu Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic | Python 3.13 cần bug-fix support và tương thích giới hạn <3.14 của repo; đánh giá Python 3.14 sau dependency/Modal runtime review. Giữ baseline 3.12 cho workload cũ đến khi migration được duyệt và xác minh 3.13. |
| Database | PostgreSQL 17 trong Compose/local demo | Khớp baseline repo/migration và được hỗ trợ. PostgreSQL 18 là major upstream hiện hành; cần đánh giá migration/extension trước nâng cấp, nhất là production. |
| Queue/cache/limits | Redis 8 + RQ | PostgreSQL/outbox giữ việc bền vững; Redis/RQ dùng dispatch, backpressure và rate limit. |
| Object store local | MinIO, S3-compatible riêng tư | Lưu media/lesson gốc và dẫn xuất local; không lưu binary trong PostgreSQL. |
| Xác thực | Chỉ Firebase Authentication | Backend xác minh ID token và phân quyền; cấm dịch vụ Firebase lưu dữ liệu sản phẩm. |
| AI hosting | Modal | Provider adapter chỉ ở backend; không dùng Lightning AI. |
| Model video | Pipeline self-host chính thức LTX-2.5 trên Modal L40S | Chủ sở hữu chọn L40S sau xem xét VRAM; image/config model cần POC. |
| Stage AI nhỏ hơn | Modal L4 là ứng viên | Dùng cho ASR/VLM/LLM/TTS nhẹ hơn nếu benchmark phù hợp. |
| Media | FFmpeg | Ghép scene, lời kể/phụ đề và kiểm tra kỹ thuật MP4. |
| Monitoring | JSON structlog, OpenTelemetry SDK/Collector, Prometheus, Grafana | Đề xuất cho Docker Compose local; chưa chọn nơi nhận alert production. |
| Email local | Mailpit | Bắt email nhắc thanh toán local, không gửi ra ngoài. |
| Container | Docker Compose | API, worker, dependency stateful/monitoring local; mobile emulator chạy trên host; Teacher web dùng dev server hoặc Compose profile. |

React Native 0.88 upstream phát hành ngày 2026-10-19. Đây là ứng viên nâng cấp, không tự đổi baseline: trước hết review compatibility của apps/mobile, React/Metro, native modules và Android/iOS tooling. Vite 8.3 là pin hiện hành trong teacher-ui. Compose pin PostgreSQL 17 để tương thích repository; PostgreSQL 18 được đánh giá tại cổng migration/deployment. Nguồn chính thức và trạng thái phiên bản chi tiết ghi tại §25.6.

**Hiện trạng nền tảng trong repository:** apps/mobile hiện chủ yếu là fixture/contract foundation; apps/ui-mobile là nguồn tham khảo hành vi, chưa phải luồng Parent production để khôi phục. Chụp camera, ghi âm và upload voice cần triển khai cùng xử lý quyền thiết bị. SRS không giả định đã có đủ screen/tích hợp. Khi lập kế hoạch Parent cần kiểm tra cả hai app và ánh xạ hành vi sang API React Native được hỗ trợ trước khi đóng luồng.

Các phiên bản nêu trên phản ánh baseline repository hoặc đích đề xuất. Cần pin patch version, model revision, CUDA/runtime image và license trong implementation plan được duyệt. Provider docs/năng lực GPU có thể thay đổi; kiểm tra lại trước deploy.

### 9.4 Deploy local và secret

Các service Docker Compose mục tiêu:

- api: HTTP interface FastAPI.
- worker: RQ worker cùng adapter Modal/payment/email.
- PostgreSQL: persistent volume và health check.
- Redis: queue/rate-limit state.
- MinIO: object store local riêng tư và persistent volume.
- OTel Collector: nhận trace/metric/log ứng dụng và export local.
- Prometheus/Grafana: scrape và hiển thị metric local.
- Mailpit: SMTP sink local cho thông báo billing.
- Teacher web profile tùy chọn: build/dev server.

Android chạy bằng công cụ phát triển/emulator local và gọi API; Android production build không chứa private key/endpoint. Compose dùng named volume, readiness check và health endpoint. File .env/provider credential thật phải ở local và được ignore; .env.example chỉ có placeholder. Không in secret trong terminal evidence.

Modal không truy cập trực tiếp MinIO local. Demo synthetic dùng backend SDK chuyển file vào scratch prefix riêng theo attempt trên Modal Volume, chỉ truyền path/hash ref, tải output bằng SDK để kiểm tra, lưu vào MinIO nếu an toàn/phát được rồi purge scratch. Giới hạn/cleanup chi tiết ở §24.3; cần POC truyền file synthetic trước tích hợp video.

Kiến trúc demo local chưa chọn host/region production, object storage production, email delivery, nơi nhận alert, mục tiêu disaster recovery hoặc quy mô production.

### 9.5 Contract ranh giới có version

| Contract | Mục đích | Bất biến bắt buộc |
|---|---|---|
| OwnerScopeRefV1 | Resource có owner scope | kind là ORGANIZATION, PARENT_ACCOUNT hoặc GLOBAL; GLOBAL chỉ dùng cho catalog/policy nền tảng; ID opaque; backend suy ra actor để xác thực |
| OwnerResourceRefV1 | Tham chiếu giữa hai module | `owner_module`, `resource_kind`, opaque `resource_id`, `owner_scope`, `contract_version`; thêm revision/hash pin khi resource bất biến. Owner đích xác minh ref qua port ở admission/completion/reconciliation; không tạo bảng reference registry hoặc FK chéo schema. |
| ProfileRefV1 | Tham chiếu hồ sơ trẻ Parent/Teacher | Loại profile khớp owner; cross-role read cần active ShareGrantRefV1, purpose/field scope/version check và revoke |
| StoryRunCommandV1 | Tạo/cập nhật một run | Chính xác một scalar profile ref, adult actor và input revision; từ chối array/group ref |
| LessonOccurrenceRefV1 | Một buổi dạy Teacher | Class, Teacher phụ trách hiện tại và một plan revision đã duyệt |
| VideoQuotaAdmissionV1 / VideoQuotaSummaryV1 | Duyệt một full-video request và hiển thị quota hiện tại | Scope Parent account/Teacher organization do server suy ra; một unit/request được chấp nhận; có grant ref và idempotency receipt; không chứa dữ liệu trẻ/media |
| ClassProjectionConfirmationV1 | Xác nhận đối tượng/mục đích chiếu video mẫu cho occurrence | Teacher phụ trách hiện tại, occurrence ref, generation ref đã qua safety, timestamp xác nhận và assignment revision; không cấp capability dùng lại cho thành viên lớp |
| AssetRefV1 | Media gốc/dẫn xuất hoặc guide tạm thời | Asset ID opaque, version/hash bất biến, media type, source link, access policy và expiry khi asset có lifecycle tạm |
| AiJobCommandV1 / AiJobStatusV1 | Stage AI bất đồng bộ cho Story/video, lesson extraction, Teacher Deck hoặc Parent guide | Chính xác một cặp target kind/ref: `STORY_RUN`, `VIDEO_GENERATION`, `VIDEO_GENERATION_SCENE`, `LESSON_SOURCE_DOCUMENT`, `LESSON_LIBRARY_VERSION`, `LESSON_VERSION_VISUAL_ASSET`, `LESSON_SKETCH_DECK_REVISION` hoặc `PARENT_SKETCH_GUIDE`; expected target revision/input hash, stage, attempt và safe result/error. StoryRun target resolve đúng một profile từ Story; video scene target resolve scene/generation/run qua Story port; cả hai Lesson target không có profile trẻ; Parent guide chỉ có generic topic/difficulty. `correlation_id` nối các job thuộc cùng generation/run nhưng không thay thế target. |
| StoryRunDetailV1 | Một response tổng hợp cho client | Current run/input/script/video pointers, safe stage, scene/job statuses, authorized asset/playback refs và quota summary qua owner ports. Không trả prompt, raw transcript, hidden story revision, foreign-scope existence hoặc provider error detail. |
| ScriptRevisionV1 | Story/script/storyboard | Revision/hash bất biến, 5–15 scene, mục tiêu dài 30–90 giây |
| SketchDeckV1 / SketchDeckStepV1 | Deck line-sketch theo occurrence plan | Occurrence ID, approved plan revision/hash, target age band, 16:9 template version, activity ref, stable instruction-group key, 3–5 ordered sketch-step records per guide, bounded layout hint, concise child-facing prompt/explanation, asset ref/hash/lineage, model/schema/template version; không có profile/trẻ hoặc video quota ref |
| PaymentEventV1 | Callback provider | Provider/event/order ref, kết quả xác minh signature, idempotency key, amount/currency |
| NotificationCommandV1 | Thông báo theo lịch/sự kiện | Vai trò người nhận, template/version, trigger ID, dedupe key; không chứa nội dung trẻ |

Client poll job status có version, bắt đầu mỗi 2 giây và exponential backoff đến 10 giây; dừng ở trạng thái kết thúc, giảm/tạm dừng khi app chạy nền. ETag/job version tránh fetch thừa. Chỉ thêm SSE/WebSocket nếu dữ liệu chứng minh cần và có ADR riêng. Contract là nguồn chuẩn; type mobile/web được generate hoặc derive từ contract.

### 9.6 API đích đề xuất

Các route dưới đây là nhóm resource, chưa phải OpenAPI cuối. Ngoài local development, mọi route dùng HTTPS và phân quyền, trừ auth bootstrap/health và provider callback.

| Nhóm route | Thao tác chính |
|---|---|
| /v1/me | Giải quyết danh tính đã xác minh, role và scope được cấp |
| /v1/parent/profiles | Liệt kê/tạo/tạo revision/xóa hồ sơ Parent của mình |
| /v1/organizations/{org}/classes | Liệt kê/tạo lớp, phân công Teacher, quản lý roster trong entitlement |
| /v1/teacher/profiles | Tạo/sửa hồ sơ qua form và profile context |
| /v1/lessons và /v1/lesson-occurrences | Import, extraction status, revision chỉnh sửa, plan occurrence và phê duyệt |
| /v1/lesson-occurrences/{id}/sketch-decks | Sinh deck từ approved plan revision, đọc trạng thái/revision hiện hành, lấy step/asset refs và regenerate đúng một sketch step. Mỗi command kiểm occurrence assignment, plan hash, idempotency key và sketch-specific rate/cost admission. |
| /v1/activities | Đọc catalog đã phát hành theo quyền hiện hành; đây không phải bước chọn activity làm điều kiện Parent story/video. Teacher vẫn chọn activity theo quyền. Quyền đọc/preview Parent trước video và projection của lesson list hậu video (tham chiếu lesson-version opaque tùy chọn qua cổng module Lesson; không gắn org/class/occurrence của Teacher; quyền đọc catalog/xem trước lesson tách khỏi điều kiện tạo video; không cấp quyền đọc mới; kiểm quyền hiện hành trước khi trả nội dung; lesson bị thu hồi/gỡ phát hành thì ẩn danh sách, video không bị ảnh hưởng và không fallback sang catalog công khai). [Còn mở cho thiết kế vật lý: vị trí lưu vật lý tham chiếu lesson-version]. |
| /v1/story-runs | Tạo run một trẻ, gửi tranh/ý tưởng, review stage, yêu cầu viết lại, xác nhận script, hoàn tất/xóa |
| /v1/story-runs/{id} | Đọc StoryRunDetailV1 tổng hợp hiện trạng và timeline an toàn; backend compose từ Story, AI Jobs, Core Asset, Lesson/Billing ports tùy run, không có cross-schema SQL hoặc nhiều endpoint bắt frontend phải ghép |
| /v1/jobs/{job_id} | Poll trạng thái AI job/stage có version và lỗi an toàn |
| /v1/story-runs/{id}/playback-token | Cấp quyền playback ngắn hạn sau khi phân quyền |
| /v1/lesson-occurrences/{id}/projection-confirmation | Xác nhận riêng việc chiếu video mẫu cho occurrence |
| /v1/video-quota và /v1/video-quota/purchases | Đọc quota tổng hợp theo scope và mua quota bổ sung |
| /v1/organizations/{org}/subscription | Đọc/cập nhật gói, capacity, thanh toán/gia hạn và yêu cầu hạ gói |
| /v1/payments/{provider}/callback | Xác minh callback MoMo/VNPAY và loại event trùng |
| /v1/notifications | Đọc inbox trong app, cursor pagination và xác nhận đã đọc |
| /v1/notifications/push-endpoints | Đăng ký endpoint Web Push hoặc Android provider adapter sau xác thực actor/device proof; revoke endpoint của actor hiện tại |
| /health/live, /health/ready, /metrics | Probe/metric vận hành, được bảo vệ phù hợp |

Dùng pagination cho roster/history; xác minh request size/content type; yêu cầu idempotency key với command đổi state hoặc liên quan payment. Không trả storage URL, provider prompt hoặc traceback nội bộ.

### 9.7 Nguồn dữ liệu có thẩm quyền

Mỗi khái niệm nghiệp vụ có một owner dữ liệu chuẩn. Module khác chỉ giữ reference/event có version, không duy trì bản mutable cạnh tranh.

| Fact nghiệp vụ | Nguồn chuẩn | Module khác được giữ |
|---|---|---|
| Danh tính người lớn đăng nhập và Parent/Teacher scope độc quyền | Firebase Authentication chứng minh issuer/UID; BE1 identity registry sở hữu phân công account scope độc quyền | Actor/scope reference có kiểu, opaque và assignment version; Firebase claim không phải thẩm quyền phân quyền duy nhất |
| Tổ chức, lớp, phân công và roster Teacher | BE1 | Reference opaque và assignment version trong lesson/story contract |
| Hồ sơ trẻ Parent | Parent profile module | Parent profile ref opaque và run snapshot đã duyệt |
| Revision hồ sơ Teacher | be1.profile_revisions; be1_managed_profiles là projection head hiện tại | Story giữ revision ref/hash bất biến và giá trị đã duyệt |
| Membership lớp hiện tại | Enrollment row của BE1 | be1_managed_profiles.class_id chỉ là projection lớp hiện tại; cập nhật cùng transaction application với enrollment |
| Revision hồ sơ/context người lớn nhập | Owner profile (Parent hoặc BE1) | Story giữ snapshot ref/hash tối thiểu, bất biến và item đã duyệt; lịch sử app và trải nghiệm ngoài app vẫn là hai nguồn riêng |
| Quyền/consent xử lý dữ liệu thật | Authorization record BE1/Parent, chỉ cho scope dữ liệu thật | Profile synthetic có data_origin=SYNTHETIC_TEST, không giả consent; legacy không rõ nguồn không được coi là có consent |
| Hoạt động Parent đã phát hành | Learning Content | Learning Content giữ catalog/version được duyệt; Teacher sample ghim đúng activity version/snapshot được phép. Parent không cần ghim catalog activity trước story/video. Nguồn immutable lesson/version và ref/snapshot phục vụ list hậu video (tham chiếu lesson-version opaque tùy chọn qua cổng module Lesson; không gắn org/class/occurrence của Teacher; Parent không cần activity_ref làm tiền điều kiện; Teacher sample vẫn ghim đúng một activity đã duyệt); không đổi owner hoặc sao chép catalog. [Còn mở cho thiết kế vật lý: vị trí lưu vật lý tham chiếu lesson-version; biểu diễn contract/schema theo role]. |
| Giáo án Teacher và occurrence plan | Lesson | Story giữ đúng plan revision/hash đã duyệt và snapshot một hoạt động |
| Teacher Sketch Deck revision và thứ tự nội dung trình chiếu | Lesson | Sketch job chỉ giữ occurrence/plan/deck revision refs có version; Core giữ asset/lineage; deck không giữ child/profile ref |
| Entitlement/grant và usage quota video | Billing `video_quota_grants` + `video_quota_usage` | Story chỉ giữ opaque admission/usage ref qua versioned contract; AI Policy không nhận product-quota ref hoặc balance |
| Sức chứa/chi phí GPU và compute nền tảng | AI Policy `resource_scope`, `budget_bucket`, `resource_reservation`, `resource_event` | Một resource event append-only giữ idempotency/fingerprint/result snapshot và delivery state; `resource_receipt` nguồn được giữ legacy/read-only. Billing không dùng AI Policy để cấp grant, trừ quota sản phẩm hoặc tính balance |
| Vòng đời story/run, trẻ, script và giới hạn request | Story; revision/generation row là chuẩn, pointer run-head chỉ là projection | Story command xác minh owner-local targets rồi đổi pointer, aggregate version và run-state projection cùng transaction; generation lifecycle state vẫn là chuẩn |
| Dispatch job, attempt và provider completion | AI Jobs; attempt row là retry/transfer ledger duy nhất, job row là trạng thái hiện hành | Một job có một target kind/ref; scene ghi source job ref về đúng generation scene. Không giữ bộ đếm retry riêng; job events append-only; không ghi JSON history/result-array legacy mới |
| Model policy/profile và bằng chứng provider copy | AI Policy sở hữu policy/model profile; provider-copy registry cũ là legacy/read-only | Job giữ profile/version ref/hash; synthetic Modal workspace/cleanup metadata nằm ở attempt/event. Provider-copy registry mới chỉ sau real-data gate |
| Byte asset, hash, media type và byte count | Object store riêng qua Core Asset port; core_asset_metadata là metadata chuẩn, core.asset_lineage sở hữu provenance edge | Story/job chỉ giữ asset ref/version, không copy hash/output metadata |
| Subscription, invoice, payment và class capacity tổ chức | Billing; subscription_events sở hữu thay đổi capacity từng lớp append-only | BE1 class state là projection đọc nhanh của capacity/suspension event hiệu lực; tạo lớp/run hỏi entitlement port có version |
| Inbox, push endpoint và trạng thái gửi in-app/email/push | Notifications | Producer phát notification request có kiểu và dedupe key; inbox là nguồn chuẩn, push best-effort |

Nguồn dữ liệu có thẩm quyền tránh trùng owner và một fact nằm hai nơi. `core_outbox_events` phát domain event do Core sở hữu; `ai_jobs.outbox` phát lệnh dispatch AI; chúng không cùng trách nhiệm. Data-table register ghi write model của từng owner và các cột nguồn được giữ. API StoryRun detail là application-level read composition qua các owner port; không ghi bản sao mutable vào bảng cache/read-model riêng.

### 9.8 Error contract chuẩn

Mọi API error trả envelope an toàn, ổn định:

| Field | Ý nghĩa |
|---|---|
| code | Mã domain/error ổn định, máy đọc được |
| message | Giải thích an toàn, đã Việt hóa; không tiết lộ provider nội bộ hoặc resource ở scope khác |
| correlation_id | ID nối request/job với trace |
| retryable | Client/operator có thể thử lại hay không |
| retry_after_seconds | Tùy chọn; trả khi rate/backpressure limit có thể xác định thời gian |
| field_errors | Mã lỗi field để kiểm tra; không echo nội dung upload |

| HTTP | Mã lỗi/ví dụ |
|---|---|
| 400 | INVALID_REQUEST, INVALID_FILE_CONTENT, INVALID_IDEMPOTENCY_KEY |
| 401 | AUTH_REQUIRED, INVALID_TOKEN, TOKEN_EXPIRED |
| 403 | ACTION_NOT_ALLOWED (chỉ khi resource đã được xác định là cùng scope nhưng actor không có quyền thực hiện action) |
| 404 | RESOURCE_NOT_FOUND (cùng một shape cho ID không tồn tại và resource ngoài scope; không tiết lộ membership, phân công hay existence) |
| 409 | ACTIVE_RUN_EXISTS, TEACHER_ACTIVE_RUN_CONFLICT, TEACHER_ASSIGNMENT_REQUIRED, ACCOUNT_SETUP_UNAVAILABLE, CLASS_CAPACITY_REACHED, INVALID_STATE_TRANSITION, STALE_REVISION, SKETCH_DECK_STALE, SKETCH_DECK_NOT_READY, SAMPLE_VIDEO_ALREADY_EXISTS, STORY_REWRITE_LIMIT_REACHED, VIDEO_REGENERATION_LIMIT_REACHED, SUBSCRIPTION_RESTRICTED, VIDEO_QUOTA_EXCEEDED |
| 409 | UPLOAD_PART_CONFLICT, UPLOAD_SESSION_STATE_CONFLICT (same part number/state with a different digest or invalid lifecycle transition) |
| 410 | UPLOAD_SESSION_EXPIRED |
| 413 | LESSON_FILE_TOO_LARGE, AUDIO_TOO_LARGE, MEDIA_TOO_LARGE (byte limit) |
| 415 | UNSUPPORTED_LESSON_TYPE, UNSUPPORTED_MEDIA_TYPE |
| 422 | IMAGE_DIMENSIONS_EXCEEDED, MULTI_CHILD_NOT_SUPPORTED, OCR_NOT_SUPPORTED, TRANSCRIPT_NOT_CONFIRMED, LESSON_PLAN_NOT_APPROVED, SUBJECT_NOT_CONFIRMED, PROFILE_CONTEXT_NOT_CONFIRMED, UPLOAD_INCOMPLETE, UPLOAD_CHECKSUM_MISMATCH, UPLOAD_CONTENT_MISMATCH |
| 429 | RATE_LIMITED cùng Retry-After; áp dụng bucket riêng cho Teacher Sketch và không trừ video quota |
| 502/503 | PROVIDER_BAD_RESPONSE, PROVIDER_UNAVAILABLE, STORAGE_UNAVAILABLE, QUEUE_UNAVAILABLE, AI_CAPACITY_BUSY, AI_COST_LIMIT_REACHED, MODAL_TRANSFER_FAILED, MODAL_RESULT_INVALID, SKETCH_OUTPUT_INVALID |

Lỗi AI bất đồng bộ cũng xuất hiện trên job resource có version, gồm mã an toàn, stage, retryability và trạng thái kết thúc/chưa kết thúc. VIDEO_SAFETY_BLOCKED và AUTHORIZATION_REVOKED là outcome cuối, an toàn cho job/run; outcome đầu không bao giờ cấp playback. Không trả stack trace, filesystem path local, Modal secret, model prompt hoặc text upload.

### 9.9 Entity, aggregate và quy ước code

Dùng domain entity/aggregate cho khái niệm có chuyển trạng thái và bất biến nghiệp vụ; không tạo một god entity cho toàn ứng dụng.

| Aggregate/entity | Sở hữu | Chuyển trạng thái/bất biến chính |
|---|---|---|
| ParentChildProfile | Profile head Parent và revision hồ sơ bất biến | Chỉ owner sửa; thay đổi tạo revision mới; không có reference Teacher/tổ chức |
| ManagedChildProfile | Danh tính hồ sơ Teacher và quyền enrollment qua BE1 port | Thuộc tổ chức; tối đa một enrollment hoạt động; chuyển lớp đóng enrollment cũ |
| OrganizationCapacity | Entitlement slot lớp và quyền tạo lớp | Capacity = 10 slot bao gồm + slot mua; transaction ngăn vượt mức |
| LessonOccurrence | Revision tài liệu nguồn, plan đã duyệt, hoạt động occurrence và con trỏ deck hiện hành | Plan phải duyệt; có thể có nhiều hoạt động; deck bao quát hoạt động đã duyệt; run chọn một activity; tối đa một sample phát được/qua safety |
| SketchTeachingDeck | Revision deck/step trình chiếu theo occurrence | Pin một plan revision/hash; deck READY chỉ khi bao quát mọi activity và mỗi hướng dẫn có 3–5 bước; plan đổi thì STALE; không mang hồ sơ trẻ; compute riêng, không dùng video quota |
| StoryRun | Một người lớn, một trẻ, input và revision context/script đã duyệt; Teacher sample ghim đúng một activity đã duyệt. Parent không có bước chọn activity trước video; ý nghĩa prerequisite theo role đã chốt ở C3; biểu diễn theo role (Parent không cần activity_ref làm tiền điều kiện; Teacher sample vẫn ghim đúng một activity đã duyệt) [Còn mở cho thiết kế vật lý: biểu diễn contract/schema theo role]. | Một run active/người lớn; `last_meaningful_activity_at` điều khiển idle deadline; VIDEO_READY idle→COMPLETED, các adult-wait state idle→ABANDONED; cả hai nhả khóa, giữ nội dung; cancel chuyển DELETE_PENDING; XOR profile kind; revision bất biến; giới hạn rewrite/video |
| VideoQuotaGrant | Grant quota tháng/mua thêm theo owner scope | Grant bất biến; quota included tháng hiện hành hết hạn cuối tháng; quota mua thêm không hết hạn và FIFO; admission loại bỏ grant expired |
| VideoQuotaUsage | Một immutable usage unit theo grant trong Billing | Idempotent; mỗi accepted full-video request một unit; không refund; không phụ thuộc retry scene; không có balance mutable |
| AiJob | Một target kind/ref được phân loại (StoryRun, VideoGeneration, GenerationScene, LessonSourceDocument hoặc SketchDeckRevision) và một stage AI | Dispatch idempotent, attempt giới hạn, expected hash/version, completion cuối hoặc stale; hồ sơ Story chỉ resolve qua StoryRun canonical; lesson-sketch không có child subject |
| OrganizationSubscription | State billing, kỳ, grace, auto-renew và class capacity | Chỉ callback xác minh đổi trạng thái thanh toán; downgrade chọn lớp; grace 7 ngày |
| Notification | Lifecycle gửi một notice/người nhận/trigger/channel | Dedupe theo trigger; retry giới hạn; không chứa nội dung trẻ |

Value object gồm OwnerScopeRef, ProfileRef, AssetRef, ActivitySnapshot, RevisionHash, MoneyVnd, BillingPeriod, QuotaGrantRef, QuotaDecision và SafeError. Dùng enum tường minh cho state/reason code; không dùng status text tự do. Domain entity tự xác thực chuyển trạng thái; không mở setter tùy ý cho state, owner, approval hoặc revision.

Quy tắc code:

1. Route/worker parse và xác thực transport data, tạo command có version, gọi một application use case và ánh xạ typed result thành HTTP/job output.
2. Application use case đọc aggregate qua repository port, phân quyền actor/resource, mở transaction, gọi domain behavior, ghi outbox/job command và trả typed result.
3. Domain sở hữu bất biến/chuyển trạng thái, không import framework, ORM, provider hoặc UI.
4. Infrastructure repository ánh xạ SQLAlchemy row sang domain object. Provider adapter xác thực JSON/media không đáng tin cậy trước khi trả contract có kiểu. Không để provider response hoặc ORM model lọt vào domain/API contract.
5. Worker không sửa trực tiếp story row sau inference. Gọi completion command với job ID, expected run revision, input/context/lesson hash và contract version. Application nhận kết quả hoặc ghi stale.
6. Mỗi command đổi state có idempotency/dedupe. Payment callback dùng provider event identity. AI dùng job/semantic request receipt. Outbox event commit cùng transaction aggregate.
7. Schema change thuộc Alembic migration của owner. Dùng expand/backfill tương thích, reconcile, sau đó bật feature flag/cutover. Không rename/drop bảng để đi đường tắt; chuyển key/cấu trúc có thể cần migration tương thích riêng.
8. UI state chỉ là projection từ API/job contract. Screen không tự suy ra quyền, duyệt, billing capacity hoặc job hoàn tất từ local state.
9. Asset gốc và dẫn xuất có danh tính riêng. Mỗi transform tạo asset version/lineage mới; không ghi đè tranh/giáo án nguồn.

### 9.10 Trình tự triển khai theo quản trị repository

Mỗi implementation task sau này cần tuân thủ workflow governance:

1. Tạo/cập nhật feature folder; đọc context và source register liên quan.
2. Ghi scope, dependency, acceptance criteria, owner module và rollback plan cụ thể.
3. Giải quyết câu hỏi sản phẩm; ghi quyết định kiến trúc vào ADR trước khi chốt stack/schema.
4. Định nghĩa domain entity và contract có version trước; bổ sung fixture/contract review trước tích hợp UI/backend.
5. Triển khai domain behavior, application use case/port, infrastructure adapter, route/worker mỏng, rồi client screen theo hướng dependency.
6. Dùng Alembic thay đổi không phá hủy theo giai đoạn; lưu migration evidence, row/hash reconciliation và rollback behavior.
7. Lưu evidence trong feature sở hữu; cập nhật context/decision/status sau mỗi bước triển khai đáng kể.
8. Cần phê duyệt rõ cho từng implementation plan trước khi sửa code/data sản phẩm. Phê duyệt tài liệu này không cho phép sửa runtime.
9. Trước commit/push, chạy repository security validator. Không commit secret, credential hoặc dữ liệu trẻ thật.

Sprint 1 vẫn là bốn workstream fixture/contract độc lập theo ADR-0006. Roadmap theo dependency và phân công làm song song là hai góc nhìn riêng; tích hợp cần allocation được duyệt riêng. Mặc định không giao backend/infra/E2E cho Person 4 hoặc toàn bộ Android app cho Person 3.

<a id="srs-10"></a>
## 10. Bảo mật, giám sát và giới hạn tốc độ

### 10.1 Kiểm soát bảo mật và quyền riêng tư

- Firebase Authentication xác minh danh tính người lớn; backend phân quyền riêng theo owner hồ sơ, membership tổ chức, phân công lớp, actor của run và trạng thái subscription. Firebase không lưu dữ liệu sản phẩm.
- Tài khoản Parent và Teacher tách biệt; profile có thể liên kết qua grant consented, scoped và revocable. Không hợp nhất account/profile owner; mọi cross-role access được backend xác minh.
- Tên/tên gọi thân mật và thông tin nhu cầu hỗ trợ bị loại khỏi context prompt AI. Snapshot mỗi run tường minh, tối thiểu, bất biến và được người lớn duyệt.
- Xem file lesson, ý tưởng nhập chữ/giọng nói và response model là dữ liệu không đáng tin cậy. Tách text lesson trích xuất khỏi system policy; không để nội dung thay system instruction, gọi tool hoặc vượt plan/safety policy đã duyệt.
- Xác thực story/script/scene/lời kể theo child-safety policy đang kích hoạt trước khi hiển thị hoặc tạo video. Output không an toàn bị chặn, trả lối khôi phục an toàn và chỉ ghi audit metadata.
- Dùng object storage riêng tư, mã hóa at-rest nếu dịch vụ hỗ trợ, playback scope ngắn hạn, kiểm tra content-type/kích thước phía server, hash/provenance cho asset gốc và dẫn xuất.
- Browser/mobile không nhận credential Modal, MoMo, VNPAY, PostgreSQL, Redis hoặc MinIO. Provider adapter chỉ chạy trong backend worker.
- Xác minh chữ ký payment callback; provider-event ref duy nhất và receipt trong transaction giúp webhook lặp idempotent.
- Bật MFA cho organization admin và billing admin. Android client gửi Play Integrity token qua backend adapter; đây không phải identity proof thay Firebase Auth và không dùng Firebase App Check.
- Database triển khai PostgreSQL RLS theo owner/org scope như defense-in-depth; runtime DB roles không phải table owner, không có `BYPASSRLS`, chỉ được cấp quyền tối thiểu. Use case vẫn kiểm tra owner/assignment explicit; RLS không thay thế authorization application.
- File upload đi vào quarantine. ClamAV hoặc scanner tương thích phải trả `CLEAN` trước parser, ASR, VLM hoặc model; scanner timeout/unavailable/error giữ file quarantine và fail closed. Scan không ghi nội dung file vào log.
- Tranh có thể chứa chữ nhận dạng như tên/trường/địa chỉ: cảnh báo/preview cho người lớn trước provider transfer, kiểm tra chữ có giới hạn, yêu cầu crop/mask nếu phát hiện PII và chỉ gửi derived masked asset. Original luôn riêng tư, lineage được ghi; đây là lớp giảm rủi ro, không đảm bảo nhận diện mọi chữ viết tay.
- Không log request body, Authorization header, audio, tranh, transcript, story text, prompt, signed URL, payment credential hoặc tên trẻ.
- Demo fixture chỉ dùng dữ liệu tổng hợp. Loại dữ liệu trẻ thật khỏi demo đến khi được duyệt riêng mục đích, quyền, consent, transfer provider, lưu giữ/xóa, truy cập và privacy.
- Không commit .env, provider token, service-account key, signing key, seed account credential hoặc dữ liệu trẻ thật.

### 10.2 Monitoring

Dùng JSON log có cấu trúc và correlation ID cùng opaque resource ID. Metric dạng tổng hợp, không có identifier trẻ/profile hoặc free text.

| Tín hiệu | Ví dụ số liệu |
|---|---|
| API | Số request/độ trễ theo route template/status, lỗi auth, 4xx/5xx |
| Queue | Độ sâu queue, tuổi job lâu nhất, enqueue/start/finish, worker heartbeat |
| AI job | Độ trễ/lỗi theo stage/type (kể riêng story-video và Teacher Sketch), số attempt, stale result, provider timeout, GPU seconds/concurrency Modal |
| Teacher Sketch | Deck/step generation, coverage/schema/safety rejection, stale/regeneration, latency và compute usage theo scope tổng hợp; không child/profile label, không video quota usage |
| Video/quota | Scene attempt, kết quả kiểm tra decode/format/safety, generation/regeneration, grant/admission/consumption/exhaustion theo loại owner scope tổng quát, top-up/đối soát callback; không dùng label child/profile |
| Storage | Số byte/object theo loại asset tổng quát, upload/download errors, deletion lifecycle backlog |
| Billing | Callback signature errors, duplicate callbacks, invoice reconciliation latency, renewal result, notification delivery |
| Security | Rate-limit event, authorization denial, authentication failure bất thường |
| Runtime | Container health, DB connection pool saturation, Redis/MinIO/OTel collector status |

Grafana có dashboard cho API/job/service health, Modal usage theo stage, video retry, storage lifecycle, payment reconciliation và notification. Nơi nhận alert là quyết định production; demo local chỉ hiển thị dashboard/log.

### 10.3 Telemetry an toàn dữ liệu

Field telemetry được phép: route template, status, duration, stage, retry number, provider/model profile ID không bí mật, GPU class, số liệu tổng hợp, correlation ID và opaque run/job ID với retention được kiểm soát. Cấm ghi tên trẻ, context hồ sơ chi tiết, byte ảnh/audio, transcript/story/prompt, credential, signed playback URL và thông tin sức khỏe/nhu cầu hỗ trợ. Sampling không được bỏ qua bước redact.

### 10.4 Giới hạn khởi đầu cho demo local

| Phạm vi | Giới hạn khởi đầu | Phản hồi |
|---|---:|---|
| API đã xác thực | 60 request/phút/account | 429 + Retry-After |
| Endpoint chưa xác thực | 20 request/phút/IP | 429 + Retry-After |
| Tạo story run | 2 request/phút/account | 429 + Retry-After; giới hạn một run hoạt động được kiểm tra riêng |
| Full-video admission attempt | 2 request/phút/account | 429 + Retry-After; giới hạn tính cả admission bị từ chối để chống spam intent; retry cùng idempotency key trả cùng kết quả và không tạo intent mới |
| Upload session control (create/complete/abort) | 10 request/phút/account | 429 + Retry-After; rate bucket riêng với chunk/status |
| Upload chunk PUT | 60 request/phút/account; tối đa 40 MiB byte mới/phút/account; tối đa 3 session đang hoạt động/account | 429 + Retry-After; chunk tối đa 4 MiB; exact-digest retry vẫn tính request nhưng không tính lại unique-byte budget |
| Upload status/list-parts | 30 request/phút/session | 429 + Retry-After; chỉ trả state/receipt trong owner scope |
| Teacher AI Sketch | Rate-limit và compute cost cap độc lập theo organization/current responsible Teacher/occurrence; giá trị cụ thể sau synthetic benchmark | 429 `RATE_LIMITED` hoặc 503 `AI_COST_LIMIT_REACHED`; không ghi Billing video quota |
| Run story hoạt động | 1 trên mỗi tài khoản người lớn | 409 ACTIVE_RUN_EXISTS |
| Quota video tháng | Tổng grant của Parent account hoặc Teacher organization | 409 VIDEO_QUOTA_EXCEEDED; playback/lịch sử cũ vẫn truy cập được |
| Audio | 2 phút và 20 MB | 413 khi vượt size/thời lượng |
| Ảnh tranh | Tối đa 20 MiB encoded, 40 megapixel decoded; chỉ JPEG/PNG/WebP | 413 khi vượt byte; 422 IMAGE_DIMENSIONS_EXCEEDED hoặc UNSUPPORTED_MEDIA_TYPE |
| File lesson | 25 MB và 100 trang/slide | 413/422 với mã lỗi an toàn |
| Scene AI | 1 lần đầu + 2 retry tự động | Hết retry thì job lỗi an toàn ở trạng thái cuối |
| Số inference scene tối đa | 15 scene × 3 attempt = 45 attempt/request; tối đa 3 accepted request/run = 135 attempt/run về mặt cấu trúc | Hard GPU-second/request và daily caps dừng trước giới hạn lý thuyết nếu benchmark/cost ceiling thấp hơn |
| Video LTX trên Modal | 1 run đang chạy; tối đa 5 video chờ | 503 AI_CAPACITY_BUSY + Retry-After khi queue đầy |
| Timeout stage scene Modal | 900 giây mỗi attempt; hard generation deadline `accepted_at + 6 giờ`, gồm queue, retry wait, model stages, composition, validation và reconciliation | Dừng tại deadline, trả timeout an toàn; quota đã nhận vẫn tiêu thụ; deadline không phải completion SLO |
| GPU cost cap | Hard cap GPU-seconds cho mỗi accepted request và mỗi ngày, cùng circuit breaker | Cấu hình bắt buộc trước khi mở live video; giá trị đặt sau benchmark synthetic, không chỉ dùng cảnh báo |
| Fair queue | Round-robin theo owner scope; FIFO trong Parent account/Teacher organization; bounded waiting per scope | Một scope không chiếm hết hàng đợi; queue đầy từ chối mới bằng AI_CAPACITY_BUSY |
| Công tắc dừng Modal | AI_VIDEO_ENABLED=false ngừng nhận video mới; gửi yêu cầu hủy work đang chạy | Từ chối request mới an toàn; không publish output stale/muộn |

Giới hạn được cấu hình phía server và là điểm khởi đầu cho synthetic POC; upload buckets tách khỏi generic API bucket để resume không tự bị 10 request/phút chặn. Ngưỡng upload/ảnh/timeout/queue chưa phải capacity đã đo hoặc production SLO. Mức 15 scene × 3 attempt × 900 giây tương ứng tối đa 11,25 GPU-giờ aggregate nếu chạy tuần tự; scene độc lập được chạy song song trong concurrency giới hạn. Trước quota admission phải xác nhận GPU-second reservation và deadline/capacity envelope khả thi; nếu không, từ chối trước Billing usage. Benchmark phải xác nhận 6 giờ wall-clock từ accepted_at, gồm queue và mọi stage; 6 giờ là hard timeout, không phải p95 claim. Hard GPU caps là cấu hình release bắt buộc; giá trị cụ thể chỉ chốt sau benchmark tổng hợp. Cần giữ mọi giới hạn hữu hạn, khác 0. Không khóa rate theo ID trẻ/content.

Payment callback có policy chống abuse/replay riêng theo provider, xác minh chữ ký và receipt idempotent; không từ chối retry callback hợp lệ chỉ vì generic unauthenticated-browser bucket đầy. Health probe và metrics scrape phải được bảo vệ nội bộ, tách khỏi throttle public.

<a id="srs-11"></a>
## 11. Kiến trúc dữ liệu và bất biến

Danh sách chuẩn về owner, key, field chính, quan hệ, constraint, retention và disposition nguồn/đích nằm trong [DATA_TABLE_REGISTER.md](DATA_TABLE_REGISTER.md). Mô hình đích phân trách nhiệm như sau:

| Owner/schema | Trách nhiệm dữ liệu |
|---|---|
| core | Audit dùng chung, aggregate revision, outbox, asset metadata/lineage, upload sessions và part receipts |
| be1 | Tổ chức, identity projection người lớn, assignment tổ chức/lớp, lớp, hồ sơ Teacher và enrollment |
| parent | Hồ sơ trẻ Parent, revision, context, nhu cầu hỗ trợ và authorization dữ liệu |
| ai_jobs | Provider job bền vững, stage attempt/event và command/completion receipt; Story/Lesson aggregates sở hữu output refs |
| ai_policy | Policy/model governance, activation và platform compute/resource reservation ledger; provider-copy registry nguồn được giữ read-only ngoài target graph |
| learning_content | Catalog hoạt động Parent toàn cục, được duyệt và có version |
| lesson | File nguồn, revision text trích xuất, occurrence, plan đã duyệt và các hoạt động |
| story | Run một trẻ; `run_inputs` giữ revision tranh/ý tưởng, revision hồ sơ được ghim và snapshot context đã duyệt; transcript/understanding, story/review revision, scene và video generation |
| billing | Rate có version, subscription tổ chức, capacity, invoice/payment, provider receipts/events, video-quota grants và immutable usage ledger |
| notifications | In-app item, delivery attempt và push endpoint |
| Schema legacy | Bảng lịch sử collaboration/canvas/video/activity/preset cùng 13 AI Policy deferred giữ read-only; không nằm trong ERD đích |

### 11.1 Constraint database bắt buộc

1. Story run mang đúng một profile ref Parent hoặc Teacher (exclusive-or check); role/scope phải khớp.
2. Story run có đúng một profile ref có kiểu. Teacher sample có đúng một activity đã duyệt và scalar lesson-occurrence ref; Parent không cần activity đã chọn trước story/video. Nguồn lesson/version Parent và biểu diễn ref theo role (tham chiếu lesson-version opaque tùy chọn qua cổng module Lesson; không gắn org/class/occurrence của Teacher; Parent không cần activity_ref làm tiền điều kiện; Teacher sample vẫn ghim đúng một activity đã duyệt), không suy ra schema/FK/NULL policy mới. [Còn mở cho thiết kế vật lý: vị trí lưu vật lý tham chiếu lesson-version; biểu diễn contract/schema theo role].
3. Partial unique constraint cho tối đa một run chưa đóng trên mỗi owner hiện hành: Parent account hoặc Teacher hiện được phân công, qua `active_owner_parent_account_id`/`active_owner_teacher_id`. Các trường này tách khỏi `created_by_actor_ref` bất biến. `DRAFT`, `VIDEO_ADMISSION_PENDING` và mọi run chưa đóng giữ khóa; `COMPLETED`, `FAILED`, `ABANDONED`, `DELETE_PENDING`, `DELETED` không. Reassignment cập nhật owner/lock qua Story command idempotent có version; BE1 và Story dùng transaction/receipt riêng trong saga, không SQL/transaction xuyên module. Hủy và idle-closeout giải phóng khóa trong transaction Story; timer không đóng run khi AI job/admission reconciliation còn hoạt động.
4. Partial unique constraint cho tối đa một enrollment lớp hoạt động trên mỗi managed profile.
5. Partial unique constraint cho tối đa một Teacher phụ trách hoạt động trên mỗi lớp.
6. Unique partial constraint giới hạn một video mẫu phát được/đạt safety cho mỗi occurrence. Run lỗi/safety-block trước claim đầu không tính. Sau claim, slot không mở lại do từ chối video, regeneration lỗi/hết lượt, delete/cancel hay Teacher reassignment.
7. Một run nhận một full-video request đầu và tối đa hai request tạo lại chất lượng. Mỗi request được chấp nhận tiêu thụ một request cap và một unit quota. ai_jobs.attempt giới hạn hai retry kỹ thuật sau lần gọi đầu của từng scene và không trừ thêm quota.
8. Story revision cho phép bản đầu và tối đa ba lần viết lại/run. Revision bất biến; job stale không thể duyệt revision mới hơn.
9. Mỗi AI job có đúng một target kind/ref/revision. `STORY_RUN` resolve đúng một child qua Story; `VIDEO_GENERATION` resolve đúng generation/run; `VIDEO_GENERATION_SCENE` resolve đúng scene/generation/run; `LESSON_SOURCE_DOCUMENT` resolve tài liệu qua Lesson; `LESSON_LIBRARY_VERSION` resolve lesson draft; `LESSON_VERSION_VISUAL_ASSET` resolve visual asset; `LESSON_SKETCH_DECK_REVISION` resolve Teacher deck; `PARENT_SKETCH_GUIDE` chỉ nhận generic topic/difficulty và trả temporary guide asset. Cả hai sketch target đều không có child/profile. Không tạo subject-ref hoặc job-scene helper table.
10. Số lớp hoạt động không vượt capacity hiệu lực của tổ chức. Thay đổi capacity/tạo lớp chạy transaction với lock hoặc serializable enforcement.
11. Provider event key duy nhất theo provider; webhook receipt và cập nhật invoice/subscription idempotent trong transaction.
12. Revision hồ sơ/context snapshot là opaque ref có version giữa các module. Cross-module validation dùng contract/port; không tạo FK xuyên module.
13. Chỉ owner hồ sơ/Teacher phụ trách được đọc nội dung profile; admin quản lý roster không mặc nhiên xem media.
14. Billing là nguồn entitlement và immutable usage ledger cho quota video. Parent scope là Parent account; Teacher scope là organization. Trước admission/dispatch, application reserve compute budget qua AI Policy port rồi Billing kiểm tra scope/grant và ghi usage idempotent; nếu không có budget/quota thì request chưa được nhận và không ghi usage. Khi đã nhận, unit không hoàn dù provider/safety/emergency abort fail hoặc run bị xóa. AI Policy resource ledger chỉ đo/reserve tài nguyên nền tảng; Story giữ opaque usage ref. Không tạo balance mutable thứ hai và không SQL/join cross-module.
15. Mỗi full-video request được chấp nhận tiêu thụ một unit quota và một trong ba request slot/run, kể cả lỗi kỹ thuật/provider/safety. Billing ghi usage trước dispatch; retry scene không tạo row mới; không refund. Kỳ tháng dương lịch `Asia/Ho_Chi_Minh`; dùng grant included tháng hiện tại trước rồi top-up FIFO. Grant included còn dư hết hạn cuối tháng; quota mua thêm carry-forward (Q117–Q118, Q124–Q126, Q128, Q132).
16. Xóa run không hoàn unit quota đã tiêu thụ (Q119); giữ tối thiểu usage ledger để audit/metering và xóa nội dung liên kết theo lifecycle.
17. Top-up là giao dịch mua một lần, không tự gia hạn (Q120). Event thanh toán đã xác minh/idempotent mới phát grant.
18. Account/tổ chức bắt đầu giữa tháng nhận đầy đủ allowance included tháng dương lịch hiện tại, không prorate (Q121).
19. Mỗi lần chiếu video mẫu cho lớp cần xác nhận theo occurrence của Teacher phụ trách trước khi cấp playback token chiếu. Ghi riêng với review script/video; không tạo playback capability dùng lại cho thành viên lớp.
20. `VIDEO_READY` được người lớn hoàn tất/tạo lại hoặc tự chuyển `COMPLETED` sau 168 giờ adult-wait idle. Adult-wait states khác chuyển `ABANDONED` cùng deadline; nhắc ở giờ 144. Hai state đóng run và nhả khóa nhưng giữ nội dung đến khi xóa. Hủy run chưa hoàn tất chuyển `DELETE_PENDING`, giải phóng khóa ngay, hủy job và xóa theo lifecycle. Giữ quota đã tiêu thụ và sample claim đã thành công (Q122–Q123, Q129, Q133).
21. Generation-scene không thể gắn scene từ revision khác: `story.video_generations` có unique `(video_generation_id, story_revision_id)`; `story.story_scenes` có unique `(story_revision_id, scene_id)`; `story.video_generation_scenes` mang `story_revision_id` bất biến và có composite FK tới cả generation lẫn scene.
22. Current pointer thuộc đúng run: Story command khóa/version-check run, validate input/story/video pointer ownership và parent revision, rồi cập nhật pointer + aggregate revision + run state trong một Story transaction; stale expected revision bị từ chối.
23. Run/video state không tự lệch: `video_generations.state` là generation lifecycle canonical; `runs.state` là business projection. Completion idempotent của Story cập nhật đồng thời; `VIDEO_READY` yêu cầu current generation READY, asset hoàn chỉnh và technical/consistency/safety đều pass.
24. AI Job nối đúng target: job có đúng một target kind/ref/revision — `STORY_RUN`, `VIDEO_GENERATION`, `VIDEO_GENERATION_SCENE`, `LESSON_SOURCE_DOCUMENT`, `LESSON_LIBRARY_VERSION`, `LESSON_VERSION_VISUAL_ASSET`, `LESSON_SKETCH_DECK_REVISION` hoặc `PARENT_SKETCH_GUIDE`. Scene giữ reciprocal source job ref được Story owner xác minh; attempt là retry/transfer ledger duy nhất.
25. Tham chiếu xuyên module có contract: ref mang owner/resource kind, opaque ID, scope, contract version và revision/hash pin nếu cần; owner đích validate ở admission/completion/reconciliation. Không dùng FK xuyên schema hoặc bảng registry ref chung.

PostgreSQL partial unique index được đề xuất cho uniqueness phụ thuộc state; cần xác minh trên schema/state thực ở giai đoạn triển khai. [Tài liệu index PostgreSQL 17](https://www.postgresql.org/docs/17/indexes.html).

### 11.2 Owner scope

OwnerScopeRefV1 hỗ trợ ORGANIZATION, PARENT_ACCOUNT và GLOBAL. GLOBAL chỉ dành cho catalog/policy nền tảng; không làm owner của profile trẻ, run, quota video hoặc media asset. Backend suy ra adult actor để xác thực, không tin giá trị client gửi. Profile Parent và quota Parent dùng scope tài khoản Parent; profile Teacher và quota Teacher dùng scope tổ chức cùng authorization tổ chức. Không biểu diễn Parent bằng organization giả. ID profile Parent/Teacher opaque và không liên quan nhau. Mỗi model payload được dựng từ đúng một hồ sơ có quyền truy cập và snapshot đã duyệt.

### 11.3 Lưu giữ và xóa

- Tranh/audio/lesson gốc và từng artifact dẫn xuất có asset identity bất biến cùng source lineage khi cần.
- Hủy một run chưa hoàn tất dùng cùng lifecycle purge với xóa nội dung: thu hồi access và nhả khóa active ngay khi ghi nhận lệnh, hủy job best-effort, xóa mọi object/metadata đủ điều kiện; giữ quota usage tối thiểu và Teacher sample-slot claim đã tiêu thụ.
- Xóa run tạo lifecycle request cho từng nội dung riêng tư và artifact sinh ra của run. Nếu asset còn được object hợp lệ khác tham chiếu, chỉ xóa khi không còn reference được lưu hợp lệ theo owner lifecycle.
- Với video mẫu Teacher, sau khi xóa run chỉ giữ sample_slot_state và thời điểm claim của occurrence; xóa pointer run/profile/media. Slot đã tiêu thụ vẫn dùng theo xác nhận của chủ sở hữu. Metadata này không định danh trẻ và không cấp playback.
- Audit giữ actor/action/loại resource/thời gian/kết quả và deletion receipt; không giữ media, transcript, prompt hoặc chi tiết profile.
- Xóa profile theo lifecycle của owner và xóa/ẩn context/lịch sử phụ thuộc theo policy. Thời hạn lưu theo luật chưa chốt trong SRS demo; cần policy dữ liệu thật trước khi bật dữ liệu trẻ thật.
- Không áp dụng ngầm retention mới cho dữ liệu legacy chỉ đọc. Archive migration/purge cần mapping, backup và restore plan được duyệt riêng.
- Q119 đã chốt: xóa run/content không hoàn quota đã tiêu thụ; giữ tối thiểu quota-usage ledger metadata.

| Loại dữ liệu | Retention trong demo tổng hợp | Xóa/backup | Trạng thái áp dụng |
|---|---|---|---|
| Profile và revision Parent/Teacher | Đến khi chủ thể có quyền yêu cầu xóa theo lifecycle; không auto-expire | Thu hồi quyền ngay, purge nội dung phụ thuộc; giữ audit/roster/legal metadata tối thiểu đã phân loại | Synthetic demo; thời hạn tối đa cho real data chưa chốt |
| Run, tranh/audio, transcript, story revisions, scenes, video hoàn tất hoặc ABANDONED | Đến khi người dùng chủ động xóa; Q66/Q129/Q133 không đặt auto-purge theo ngày | Xóa qua lifecycle; backup theo chính sách backup demo được duyệt, hiện không có chính sách backup real data | Synthetic demo only; production gate bắt buộc retention max |
| Giáo án gốc và extraction revisions | Đến khi Teacher/admin xóa lesson theo lifecycle | Purge original + derived text/asset, giữ audit tối thiểu | Synthetic lesson only; production schedule TBD |
| Modal scratch/input-output working copy | Xóa sau completion/failure/cancel; orphan scratch được dọn/cảnh báo sau 24 giờ | Job-scoped prefix, checksum và deletion receipt | Không chứa real child data trong demo |
| Billing invoice/payment event và quota grant/usage | Theo retention tài chính/metering sẽ được chốt với legal/accounting; quota usage không chứa nội dung trẻ | Nội dung run xóa độc lập; append-only billing/audit metadata không bị xóa cùng run | Thời hạn production TBD |
| Logs/traces/metrics | Cấu hình retention hữu hạn; chỉ dữ liệu đã redact/opaque IDs | Xóa theo retention vận hành; không chứa payload/media/PII | Thời hạn cụ thể cần điền trong deploy profile trước pilot |
| Backups | Manual local backups chỉ chứa synthetic data | Production phải có expiry, access controls, deletion propagation hoặc cryptographic-erasure design đã review | Production gate; chưa có backup SLA |

Không thể diễn giải “đến khi user xóa” thành retention policy phù hợp cho trẻ thật. Bất kỳ production/pilot có dữ liệu thật nào đều bị khóa cho đến khi OI-05–OI-08 được duyệt, có thời hạn tối đa theo từng loại record, phương án xóa trong backup và owner chịu trách nhiệm.

<a id="srs-12"></a>
## 12. Kiểm kê nguồn, migration và chuyển đổi

### 12.1 Kiểm kê bảng nguồn

Repository hiện khai báo 86 production mapping gồm core (8), BE1 (22), AI Jobs bền vững (7), AI Policy (25), Learning Content (6), Knowledge Video (2), Video Review (6), Video Failure (3), Activity Execution (5) và Preset Automation (2). Năm fixture mapping dùng cho test không nằm trong tổng. Chưa đối chiếu các con số với database đang chạy.

### 12.2 Disposition đích

- Giữ/chuẩn hóa 38 mapping hiện có làm owner cho tổ chức, roster, AI Jobs, AI policy/version/activation/resource budget, catalog hoạt động, provenance/audit Core và hạ tầng transaction.
- Thêm 40 bảng đích để chuẩn hóa owner Parent, revision/context hồ sơ, lesson và Teacher Sketch Deck, story, quota, billing, notification, asset và job; loại bốn helper/snapshot table trùng với aggregate owner.
- Giữ 48 mapping legacy chỉ đọc tại chỗ: 35 mapping lớp học/canvas/video/activity/preset cũ cùng 12 `ai_policy.copy_*` registry và `ai_policy.resource_receipt`. Registry provider-copy đầy đủ bị deferred tới production gate dùng real-child-data. Lệnh resource mới dùng `resource_event` làm event + idempotency/result ledger, không ghi hai bảng.
- Phép tính đích: 38 retained/refactored + 51 new = 89 active; +48 legacy/read-only = 137 physical. Source inventory là 86 mapping; năm fixtures không tính. Đây là proposal theo source declaration, chưa đối chiếu DB đang chạy.
- Thiết kế này không copy bảng sang schema archive, không drop/truncate bảng. Giữ row/ID hiện có; một số key/nullability/check của bảng đang hoạt động chỉ đổi sau expand/backfill/reconcile và migration plan được duyệt riêng.
- Không diễn giải session ID cộng tác cũ thành story run một trẻ. Giữ nguyên session ID và ý nghĩa lịch sử.

#### Ràng buộc BE1 hiện có cần mô hình đích xử lý

Khai báo trong backend/src/sketch2life/infrastructure/persistence/be1_models.py chặt hơn đích đề xuất; không giả định luồng mới đã tương thích sẵn:

- be1_managed_profiles.class_id hiện NOT NULL và tham chiếu class. Trong đích, be1_enrollments là nguồn membership hiện tại/lịch sử chuẩn; managed_profiles.class_id chỉ là projection lớp hiện tại đã chuẩn hóa. Tạo/chuyển profile và enrollment atomically, đối soát projection. Profile thiếu enrollment hoặc enrollment không rõ phải quarantine xem xét, không tự ghi danh.
- V2.3 nhận tuổi 36–120 tháng cho profile Parent và Teacher; schema/validation nguồn hiện khai báo khoảng cũ cần được đổi trong một migration được duyệt. Age-band ranh giới cụ thể vẫn mở.
- consent_id, consent_purpose_ref hiện NOT NULL. Đích thêm data_origin (SYNTHETIC_TEST, REAL, LEGACY_UNCLASSIFIED) và chỉ bắt buộc consent theo nguồn: fixture synthetic không cần consent row/ID giả; row dữ liệu thật cần authorization hợp lệ đã xác minh; row thiếu bằng chứng giữ LEGACY_UNCLASSIFIED, backfill không tự nâng thành đủ điều kiện dữ liệu thật.
- be1_consent_records.state hiện chỉ nhận pending và revoked, chưa đủ lifecycle authorization. Demo không có dữ liệu trẻ thật. Xử lý dữ liệu thật phải định nghĩa state valid/granted/expired/withdrawn và xác minh bằng chứng trước khi bật provider transfer.
- Unique hiện tại của be1_enrollments chỉ đảm bảo bộ ba organization/class/child, chưa đảm bảo trẻ chỉ ở một lớp active. Thêm partial unique constraint một enrollment active và reconciliation idempotent trước khi bật write.
- be1_adult_identities hiện có subject key và issuer, chưa có account scope Parent/Teacher độc quyền. Thêm scope do server quản lý và uniqueness; giữ identity cũ ở Teacher/legacy đến khi xác minh riêng, không suy ra đủ điều kiện Parent chỉ vì thiếu assignment tổ chức.

### 12.3 Trình tự migration đề xuất

1. **Chụp baseline và backup:** đếm bảng/cột/index/row ở mỗi môi trường triển khai; xác minh backup/restore PostgreSQL/MinIO bằng dữ liệu tổng hợp.
2. **Mở rộng schema:** tạo schema/bảng/index đích và thêm field scope/revision/origin có version qua Alembic. Giữ nguyên cột, key và row hiện tại trong bước mở rộng ban đầu.
3. **Mapping tương thích:** tái dùng record organization/class/profile qua repository của module sở hữu. Thêm backfill idempotent cho enrollment/identity scope/data origin để xác minh; dùng LEGACY_UNCLASSIFIED nếu thiếu chứng cứ; ghi count/hash. Không tạo consent giả hoặc organization synthetic.
4. **Đối soát:** so row count nguồn/đích, opaque ID, owner profile/class, enrollment state, asset hash và audit reference. Dừng cutover nếu lệch.
5. **Tắt luồng cũ:** dùng feature flag tắt ghi classroom/canvas legacy; giữ quyền bảng/owner và read-only history cho migration/operator có quyền. Không hiển thị dữ liệu cũ trong run một trẻ mới nếu chưa có mapping được duyệt.
6. **Cutover luồng đích:** bật Parent/Teacher phía đích sau khi fixture/contract/integration đạt tiêu chí. Xác minh role assignment hiện hành và không có child/run ref rỗng.
7. **Chuyển constraint:** sau parity và chủ sở hữu duyệt, thêm/validate partial uniqueness và chuyển receipt key/nullable owner scope bằng bước dual-read/write tương thích. Giữ giá trị cột/row gốc và đường tương thích đến khi chứng minh reader mới.
8. **Theo dõi và rollback:** giám sát error, đối soát, queue và data parity. Rollback bằng feature flag và reader tương thích; không xóa dữ liệu đã chuyển hoặc cột legacy để rollback.
9. **Dọn hợp đồng về sau:** xóa bảng cũ, chuyển archive hoặc đổi retention cần plan được duyệt riêng, restore test và review owner dữ liệu/pháp lý.
10. **Chuyển provider-copy tables sang legacy:** trước cutover chứng minh synthetic Modal path có attempt-scoped workspace ref, manifest hash, cleanup receipt và orphan sweep; sau đối soát lịch sử, khóa quyền ghi `resource_receipt` và 12 bảng `copy_*`. Không drop/copy; giữ nguyên rows/IDs read-only.
11. **Gộp resource command ledger:** trước new writes, đảm bảo `resource_event` có unique idempotency key, fingerprint, operation/result snapshot và delivery state; đối soát receipts cũ. Nếu một command có thể sinh nhiều event, dùng event-kind trong khóa hoặc giữ receipt table đến khi chứng minh mapping an toàn; không bật migration mơ hồ.
12. **Validate Story composite constraints:** backfill `story_revision_id` cho generation-scene links từ generation parent; quarantine scene không thuộc revision đó; đối soát mismatch/orphan rồi mới validate composite FK. Không tự gán scene.
13. **AI Job target migration:** backfill một target kind/ref/revision từ mapping aggregate đã xác minh; map scene job tới `generation_scene_id` và kiểm tra reciprocal `source_job_ref`. Không suy diễn job target một trẻ từ session ID cộng tác.
14. **Read-model parity:** so StoryRun detail response với từng owner source và ma trận quyền; không tạo bảng projection thứ hai hoặc trả prompt/transcript/profile nhạy cảm.

Phần này chỉ mô tả trình tự an toàn đề xuất. Không thực hiện migration hoặc truy cập database khi soạn tài liệu.

<a id="srs-13"></a>
## 13. Tiêu chí chấp nhận kiến trúc nền

| ID | Given | When | Then | Nguồn |
|---|---|---|---|---|
| AC-01 | Parent và Teacher có account/scope độc lập | Actor thử truy cập profile ở scope còn lại | Backend từ chối mà không lộ account/profile tồn tại; không có liên kết chéo | BR-03; FR-C-01/04 |
| AC-02 | Người lớn đã có run active gắn đúng một profile | Gửi run thứ hai hoặc nhiều profile | Database/API từ chối; VIDEO_READY vẫn giữ khóa đến complete/cancel/idle closeout hợp lệ | BR-01/02; FR-C-02/03 |
| AC-03 | Teacher đã có lớp, roster và occurrence | Tìm canvas/QR/lobby/batch action | Không có runtime collaboration, shared canvas, QR, lobby hoặc nhiều trẻ/run | BR-01/05; FR-T-01–10 |
| AC-04 | Occurrence chưa có sample claim | Video qua safety và được playable, sau đó bị từ chối và các lần tạo lại lỗi | Claim được giữ vĩnh viễn; không có recovery run cho occurrence | BR-10/17; Q127 |
| AC-05 | Parent dùng lesson có activity list hoặc Teacher chuẩn bị occurrence | Video Parent hoàn tất hoặc Teacher tạo sample | Parent activities hiển thị sau video; Teacher sample vẫn pin một activity đã duyệt; custom activity chỉ trong occurrence và cần checklist | BR-08/09; FR-PL-16 |
| AC-06 | Story/video run đang hoạt động | Gọi rewrite hoặc full-video request | Story tối đa 1 đầu + 3 rewrite; video tối đa 1 đầu + 2 tạo lại; mỗi video request cần xác nhận script | BR-11/13–15 |
| AC-07 | Video đã qua safety tự động | Hệ thống phát video | Không có duyệt video cuối, PixiJS motion, download/export hoặc public URL | BR-16/25/36 |
| AC-08 | Có transcript nếu có voice, subject, context và script revision được duyệt theo role; Teacher bổ sung lesson/plan/activity đã duyệt. Parent không chọn/xác nhận activity trước story/video; stage/input chi tiết (đầu vào theo role; Parent story prompt không đưa activity, lesson hoặc gợi ý catalog; Teacher prompt dùng đúng một activity đã duyệt. Nếu lesson-version ref không còn hợp lệ thì không đưa ref đó vào planner prompt; list hậu video tuân quy tắc C6.) | Adult tiếp tục pipeline | Mỗi dữ liệu cần xác nhận ở bước quy định; script cuối là cổng human approval trước video | BR-14/15 |
| AC-09 | Source inventory khai báo 86 bảng production và 5 test fixtures | Đối chiếu register với target | Có 38 retained/refactored + 51 new = 89 active; +48 legacy = 137 physical; fixtures không tính; không tuyên bố live DB count | §1.1; DATA_TABLE_REGISTER |
| AC-10 | Module sở hữu profile, lesson, story, billing, notification hoặc asset | Kiểm tra write path | Mỗi fact có một owner; projection/reference/event được chỉ rõ; register có dictionary và requirement-based retention | §9.7; DATA_TABLE_REGISTER |
| AC-11 | Domain/use case/adapter được tổ chức | Kiểm tra import/dependency direction | Domain không phụ thuộc framework/provider/storage/queue/UI; giao tiếp module qua port/contract versioned | NFR-01/14 |
| AC-12 | Docker local synthetic stack chạy | Khởi động/quan sát/backup/restore | Readiness, rate-limit, error envelope, redacted monitoring, backup/restore manual có hướng dẫn | NFR-07/08/11/12/27; §25–27 |
| AC-13 | Demo tạo profile/media/run | Seed hoặc upload fixture | Chỉ dùng dữ liệu tổng hợp; real-child data bị chặn cho đến khi privacy/retention/provider gates có evidence | BR-27; NFR-03/18/31 |
| AC-14 | Tổ chức mua/nâng/hạ capacity hoặc gia hạn | Callback MoMo/VNPAY được nhận | Payment/capacity/grace/downgrade/proration/notice nhất quán; redirect không được coi là thanh toán | BR-28–33 |
| AC-15 | Hai tài liệu Markdown đang chờ owner review | Có yêu cầu diagram/PDF | Không tạo artifact cuối trước khi owner duyệt cả SRS và data register | Yêu cầu sequencing của owner |
| AC-16 | Các use case UC-01…UC-17 được review | Soát đặc tả | Mỗi UC có actor, prerequisite, trigger, main/alternate flow, postcondition và data/requirement refs | §19 |
| AC-17 | Scope quota Parent hoặc Teacher có grant/usage | Xem quota/mua/generate/hết quota | Billing ledger idempotent; scope tách; included hiện tại trước top-up FIFO; included hết tháng, top-up carry-forward; playback cũ còn mở | BR-38; FR-B-10–13 |
| AC-18 | Video Teacher đã sẵn sàng | Teacher muốn chiếu cho lớp | Teacher phụ trách xác nhận đúng occurrence; playback token ngắn hạn; không cấp account/capability dùng lại cho học sinh | BR-37; FR-T-16 |
| AC-19 | Upload, callback, job async hoặc playback được gọi | Gửi command trùng/stale hoặc provider outcome chưa rõ | Contract có auth/idempotency/version; stale result không ghi đè; trạng thái unknown vào reconciliation; lỗi có error envelope | FR-O-02/05/10; §21–22 |
| AC-20 | Người dùng chạy luồng Parent/Teacher chính | Chỉ dùng bàn phím/screen reader hoặc từ chối camera/mic | Luồng có semantic labels, focus, text error/caption; upload/text fallback dùng được; UI tiếng Việt | NFR-13/20/21/29 |
| AC-21 | Lesson, adult input, model output hoặc media được xử lý | Safety policy chạy | Nội dung untrusted; versioned validation chặn unsafe/private/medical claims trước script display hoặc playback | BR-36; FR-AI-12; NFR-23 |
| AC-22 | DRAFT hoặc run đang chờ thao tác người lớn, không có AI job/admission xử lý | Đến 144h/168h idle | Inbox tạo một reminder; push best-effort; email chỉ thử nếu current owner có email verified; +168h VIDEO_READY→COMPLETED, state chờ khác kể cả DRAFT→ABANDONED; nhả owner lock nhưng giữ content; AI deadline 6h từ accepted_at riêng | BR-39/40; FR-C-11; AT-11 |
| AC-23 | Video request vượt admission | Provider/safety/technical failure hoặc run deletion xảy ra sau đó | Mọi accepted request đã consume quota không được refund; request bị từ chối trước admission không consume | BR-11/38; Q128 |
| AC-24 | Story yêu cầu quota admission | Application phối hợp module | Billing duy nhất sở hữu grants/usage; AI Policy chỉ GPU/compute; Story giữ opaque ref; không join/ghi chéo private table | Q132; §9.7 |
| AC-25 | Admin yêu cầu reassignment; StoryRun thuộc lớp và có active owner | Transfer saga bắt đầu/hoàn tất hoặc gặp conflict | Old access/token bị fence ngay; pending state không cấp content; Story lock chuyển trước khi BE1 finalize; valid AI job tiếp tục; normal conflict 409; emergency force-close có metadata audit, không xem/xóa media, quota/sample claim giữ nguyên | BR-06/41; FR-T-14/17; AT-12 |
| AC-26 | Actor bật push hoặc endpoint invalid | Worker gửi notice | Inbox luôn authoritative; Web Push best effort; Android adapter chỉ bật sau POC; payload không chứa child data; Firebase Messaging không dùng | FR-B-14; NFR-26; Q131 |
| AC-27 | ID lạ/ngoài scope hoặc actor thiếu action | API phân quyền | ID lạ và ngoài scope cùng 404; 403 chỉ cho resource đã biết cùng scope nhưng action không được phép; account-scope conflict không lộ UID | §9.8; FR-O-05 |
| AC-28 | Hệ thống nhận nhiều upload/job/provider requests | Tải vượt rate/cost/queue hoặc threat boundary | Hard caps, fair queue, quarantine AV, RLS/least-privilege/MFA/Play Integrity là release gate; cap không được vượt | NFR-12/24/25; §10/26 |
| AC-29 | Người lớn upload ảnh/audio/lesson qua mạng không ổn định | Mất mạng rồi resume session | `core.upload_sessions`/`core.upload_parts` giữ state/receipt; app chunk 4 MiB qua object PutObject riêng; backend xác minh contiguous parts + per-part/whole SHA-256 + bytes, bounded assemble và final PutObject; không gọi S3 Multipart Upload API; exact retry không tính lại byte budget; limits cho phép resume hợp lệ | FR-C-12; NFR-32; AT-13 |
| AC-30 | Run `DRAFT`, review state hoặc `VIDEO_ADMISSION_PENDING` không có kết quả còn mơ hồ | Idle scheduler/admission callback chạy | DRAFT và các review state bắt đầu timer adult-wait; +144h có inbox, push best-effort, email nếu verified; +168h closeout và nhả khóa. Admission pending không idle-close; rejected quay về SCRIPT_REVIEW và bắt đầu timer mới | BR-39/40; FR-C-11; FR-O-10; AT-11 |
| AC-31 | Teacher assignment chuyển trong khi run/job active hoặc Teacher mới đã có run | Chạy normal transfer hoặc emergency force-close | Transfer có durable BE1/Story receipts; old authorization bị revoke, no-content trong pending, new authorization chỉ sau finalize; output valid không bị hủy; conflict ordinary trả 409; force-close chỉ metadata và không cấp media cho admin | BR-06/41; FR-T-14/17; NFR-05; AT-12 |
| AC-32 | Upload file nằm trong limit demo và mạng bị gián đoạn | App resume, server finalize | 4 MiB application chunks là object PUT riêng; tables session/parts lưu receipts; verify contiguous part numbers, size/SHA-256, scan/format; final asset ghi bằng low-level single PutObject; idempotent duplicate không double-count byte; bảng đích 40/78/126 | FR-C-12; NFR-09/12/32; AT-13 |
| AC-33 | Parent bắt đầu run; Teacher đã có tranh của đúng một trẻ | Người lớn mở bước xác nhận chủ thể hoặc AI Sketch | Parent không có bước chọn trước chủ thể hay AI Sketch; sau khi chụp, VLM đề xuất chủ thể để người lớn xác nhận/sửa. AI Sketch chỉ xuất hiện trong luồng occurrence của Teacher | BR-42; FR-P-02/04; FR-T-18; UC-02/17 |
| AC-34 | Teacher duyệt plan revision có nhiều hoạt động | Yêu cầu tạo Teacher Sketch Deck | Một deck revision gắn đúng plan hash, bao quát từng hoạt động và mỗi hướng dẫn có 3–5 bước line-sketch, gợi ý bố cục và prompt dành cho trẻ; không chứa hồ sơ/tranh của trẻ | BR-43; FR-T-18/20; FR-AI-14; UC-17 |
| AC-35 | Deck READY trên plan hash hiện hành | Teacher trình chiếu, bỏ qua hoặc yêu cầu tạo lại một bước | Back/Next/chọn/bỏ qua dùng được; tạo lại sinh revision bất biến, plan đổi làm deck cũ STALE; không có vẽ tự do/PPTX; rate/cost cap của Sketch riêng và không phát sinh video quota usage | BR-43/44; FR-T-19/20; FR-AI-14; NFR-12/25/33; UC-17 |
| AC-36 | Một run có ảnh của đúng một trẻ và ý tưởng đã duyệt; Teacher sample bổ sung đúng một activity hợp lệ đã duyệt, Parent không có pre-video activity-selection gate | Chạy story/video pipeline đến playback | VLM tạo visual anchors → LLM tạo story có cấu trúc → storyboard 5–15 scene → người lớn xác nhận script → Character Bible/ảnh tham chiếu → LTX-2.5 trên Modal L40S theo scene → kiểm tra consistency → FFmpeg ghép scene → TTS tiếng Việt/phụ đề, không nhạc → safety tự động → playback riêng; output stale/không an toàn/không hợp lệ không được phát | BR-45; FR-AI-01–13; UC-02/05/16 |
| AC-37 | Video output hoàn tất kỹ thuật và safety | Hệ thống phát hoặc người lớn yêu cầu tạo lại | Video playable ngay, không chờ duyệt cuối; unsuitable output bị ẩn khi replacement được accepted, quay lại script review; tối đa 1 initial + 2 video regens, mỗi scene 1 + 2 retries; accepted request tiêu quota kể cả lỗi, không có public gallery/download | BR-10/11/16/17/24/25/45; FR-AI-06/07/09/13; AT-17 |
| AC-38 | Generation G pin story revision R1; scene S thuộc R2 | Writer tạo generation-scene link giữa G và S | Composite FK từ generation+revision và scene+revision từ chối record; `story_revision_id` lặp là immutable constraint key; không cần application-only check hoặc bảng link mới | §11.1 #21; DATA_TABLE_REGISTER §5.6–§7 |
| AC-39 | Có job ASR, VLM, scene LTX, composition hoặc Sketch step | Hệ thống dispatch và nhận kết quả lặp/stale | Mỗi job có đúng một target kind/ref/revision; scene job target đúng generation_scene_id, correlation groups siblings, Story kiểm reciprocal source_job_ref; `ai_jobs.attempt` là retry ledger duy nhất | FR-AI-01/06/13/14; §22; DATA_TABLE_REGISTER §4.1/§6 |
| AC-40 | StoryRun có current input/script/generation pointers và một aggregate revision | Đồng thời command/job hoàn tất cập nhật state/pointer | Story transaction kiểm expected version, ownership chain và hashes; `video_generations.state` canonical, `runs.state` projection đồng thời; stale command bị từ chối và `VIDEO_READY` không thể đứng riêng khi generation/asset/safety chưa READY | §6.1.1; §11.1 #22–23; DATA_TABLE_REGISTER §6.3 |
| AC-41 | Client được phép đọc một StoryRun; một số resource có thể thuộc owner/module khác | Client gọi `GET /v1/story-runs/{id}` | Một StoryRunDetailV1 tổng hợp status, timeline, scene, job-safe error, permitted assets và quota qua owner ports; không cross-schema SQL, không fan-out phía frontend, không rò prompt/transcript/profile support/foreign-scope existence, không có read-model table | §9.5–§9.7; §22.4; NFR-05/10 |
| AC-42 | So sánh data source inventory với target register | Rà soát AI Policy và mọi source table disposition | 86 source = 38 retained/refactored + 48 legacy; 38 + 51 new = 89 active; 89 + 48 = 137 physical. 12 copy registry và resource_receipt read-only; 12 AI Policy active; legacy rows/IDs không bị drop/copy | §1.1; §12; DATA_TABLE_REGISTER §§1–4/9/11 |
| AC-43 | Resource command reserve/consume/release được gửi lặp với cùng key và fingerprint | AI Policy xử lý command và phát resource event | Một event ledger row là receipt/idempotency source mới với response snapshot/delivery state; replay trả cùng outcome; uniqueness phân biệt event kind nếu cần; source `resource_receipt` giữ read-only, không mất lịch sử | §11.1 #14; §12.3; DATA_TABLE_REGISTER §4.1/§6 |
| AC-44 | Parent đang ở drawing session khi trẻ vẽ | Người lớn bật line-sketch guide hoặc bỏ qua | Khi bật, request trả guide line-art 3–5 bước; khi tắt/skip không tạo job. Chỉ topic/độ khó được gửi model; guide không có child/profile/photo/audio/artwork refs; output private, temporary, có provenance/expiry, không gắn profile/StoryRun và không dùng video quota; sau vẽ người lớn chụp rồi VLM subject review | BR-42/46/54; FR-P-02/04/11; FR-AI-15; Q146/Q167 |
| AC-45 | Parent guide request bị timeout/limit từ chối hoặc output invalid/unsafe | Parent chọn tiếp tục, thử lại theo cap, hoặc thoát guide | Không có output chưa kiểm định nào được hiển thị; lỗi an toàn không lộ provider detail; guide bị dọn/không được gắn profile/run; người lớn vẫn tới luồng vẽ/chụp; resource accounting dùng sketch cap riêng và không ghi video quota | BR-36/44/46; FR-P-11; FR-AI-12/15; NFR-23/25; Q146 |

### 13.1 Ví dụ acceptance Given/When/Then

| ID | Given | When | Then | Requirement |
|---|---|---|---|---|
| AT-01 | Teacher occurrence chưa có sample claim; video đầu đã phát được và đã claim | Teacher đánh dấu video không phù hợp; các request tạo lại còn lại đều lỗi hoặc hết | Video cũ không playback; occurrence vẫn `SAMPLE_USED`; API không cho mở run thứ hai; run kết thúc lỗi và slot không trả lại | BR-10, BR-16–17, Q127 |
| AT-02 | Một request tạo video vượt qua admission và đã được Billing ghi usage | Provider, kỹ thuật hoặc safety gate thất bại; sau đó người lớn xóa run | Usage unit vẫn tồn tại, không refund; asset/run content xóa theo lifecycle; scene retry không tạo unit khác | BR-11, BR-26, BR-38, Q128 |
| AT-03 | Run ở `INPUT_REVIEW`, `SCRIPT_REVIEW` hoặc `VIDEO_READY`, không có AI job hoạt động và adult-wait đã đủ 144 giờ/168 giờ | Scheduler tới reminder deadline rồi idle deadline | Có inbox notice và push best-effort ở giờ 144; giờ 168 `VIDEO_READY` thành `COMPLETED`, review state khác thành `ABANDONED`; khóa được nhả; content không bị xóa tự động | FR-C-11, BR-39–40, Q129/Q133 |
| AT-04 | Lớp có run/media; admin chọn Teacher mới; Teacher mới chưa có run active | Assignment transaction commit | Teacher cũ mất quyền và token playback cũ hết hiệu lực; Teacher mới có quyền theo assignment; actor creator không bị viết lại; audit metadata ghi transfer; admin vẫn không xem media | FR-T-14, BR-06, Q130 |
| AT-05 | Actor đã đăng ký endpoint push hợp lệ | Có idle/billing/job notice hoặc provider báo endpoint invalid | Notice vào inbox bất kể push; push best-effort chỉ chứa opaque reference; endpoint invalid bị revoke; raw token/subscription không xuất hiện trong log | FR-B-09, FR-B-14, NFR-26, Q131 |
| AT-06 | Parent/Teacher scope có grant hợp lệ, chưa có usage cho idempotency key | Story yêu cầu admission qua Billing port | Billing chọn grant theo FIFO, ghi một usage row trong transaction trước dispatch; retry key trả cùng receipt; AI Policy không giữ product-quota balance | FR-B-10–12, BR-38, Q132 |
| AT-07 | Run đã nhận ảnh/ý tưởng; ASR và VLM jobs đang chạy hoặc retry | Parent/Teacher tải trạng thái run | `StoryRun=INPUT_PROCESSING`; API trả stage/job state/deadline/time updated; không đặt adult-wait timer khi còn job; job terminal mới chuyển sang review state | FR-O-10, FR-AI-01, NFR-06, Q133 |
| AT-08 | Budget reservation hoặc quota admission chưa đủ trước full-video request | Người lớn xác nhận yêu cầu tạo video | Không có accepted generation/job/quota usage; trả `AI_COST_LIMIT_REACHED` hoặc `VIDEO_QUOTA_EXCEEDED` phù hợp; nếu cả hai admission thành công thì reservation cover request cap trước dispatch | FR-B-10/11, NFR-25, BR-38 |
| AT-09 | Owner scope còn đúng một quota unit; hai request khác nhau đồng thời thử admission | Billing xử lý các request cạnh tranh | Tối đa một request được ACCEPTED và có một usage row; request còn lại bị từ chối không có usage/job/dispatch; retry của request thắng với cùng idempotency key trả receipt cũ | FR-B-10/11; BR-38; NFR-02 |
| AT-10 | Upload session đã nhận một số app chunk; app/browser mất mạng rồi mở lại | Actor resume cùng session, gửi exact-digest duplicate rồi complete; sau đó thử sai hash/state hoặc session hết hạn | Mỗi app chunk 4 MiB được lưu thành object riêng bằng PutObject; exact duplicate idempotent; part/hash conflict bị từ chối; partial asset không đến parser/model; backend assemble bounded stream, xác minh tổng size + per-part/whole SHA-256 + format + AV rồi single PutObject final asset; limit byte/request/session cho phép retry đúng mà không double-count unique bytes; expiry purge cả temp object/metadata | FR-C-12; NFR-32; AT-13 |
| AT-11 | `DRAFT` run chưa có AI job; một video request vừa bị admission reject | Scheduler chạy ở 144h/168h hoặc Billing trả rejected receipt | DRAFT/review state được nhắc và closeout đúng hạn; ADMISSION_PENDING không có timer; rejection quay về SCRIPT_REVIEW, không consume quota/cap và bắt đầu wait mới; email chỉ gửi khi email của active owner verified | FR-C-11; FR-O-10; BR-39/40; AC-30 |
| AT-12 | Teacher A có run active của lớp; Teacher B là replacement và có/không có active run riêng | Admin reassignment hoặc emergency force-close + retry | Access/token A bị fence ngay; pending không lộ content; Story owner lock chuyển trước BE1 finalize; normal conflict trả 409; emergency close chỉ metadata, không cấp quyền media cho admin; valid AI job tiếp tục và quota/sample claim được giữ | FR-T-14/17; BR-06/41; AC-31 |
| AT-13 | Upload session có 4 MiB app chunks đã ghi nhận một phần | Client retry chunk hợp lệ, hoàn tất, và gửi sai hash | Session/part tables có receipts; mỗi chunk là PutObject riêng; backend verifies continuous part IDs, bytes, per-part + whole SHA-256, AV/format; final low-level PutObject; no S3 Multipart API; unique-byte bucket không tăng khi exact retry; 429 limits không block configured maximum file flow | FR-C-12; NFR-09/12/32; AC-32 |
| AT-14 | Parent đã chụp tranh; không chọn trước chủ thể | VLM đề xuất chủ thể để người lớn xác nhận hoặc sửa | Sửa chủ thể tạo revision/VLM job mới trên cùng image hash; Parent không chọn trước subject của tranh trẻ; optional generic guide không thay thế capture-first; run vẫn gắn một trẻ | BR-42; FR-P-02/04; AC-33 |
| AT-15 | Teacher duyệt plan có nhiều hoạt động | Tạo Sketch Deck | Deck bao quát mọi activity; mỗi instruction group có 3–5 bước line-sketch theo thứ tự, có hướng dẫn age/layout; job không có child/profile/tranh ref; deck ghim approved plan hash | BR-43; FR-T-18; FR-AI-14; AC-34 |
| AT-16 | Deck READY; Teacher yêu cầu tạo lại một sketch hoặc plan đổi | Hoàn tất tạo lại và yêu cầu trình chiếu | Tạo lại sinh deck revision bất biến, giữ asset các bước không đổi; plan hash đổi làm deck stale; bucket/cost cap riêng không tạo video quota usage; deck stale bị chặn | BR-43/44; FR-T-20; AC-35 |
| AT-17 | Một run có đúng một trẻ, script đã duyệt và bắt đầu request video | Thực thi toàn pipeline với cả nhánh consistency/safety thất bại và thành công | Mỗi scene có một lần đầu và tối đa hai retry tự động; LTX tạo scene → kiểm tra consistency → FFmpeg ghép → TTS/phụ đề tiếng Việt, không nhạc → safety; output không đạt không được phát, output đạt phát riêng ngay mà không chờ duyệt video cuối; quota và giới hạn request áp dụng cho mỗi request đã được nhận | BR-45; FR-AI-01/06/07/09/13; AC-36/37 |
| AT-18 | Parent sắp cho trẻ vẽ và chưa có ý tưởng | Người lớn chọn topic/độ khó rồi yêu cầu guide hoặc bỏ qua | Guide trả 3–5 line-art steps theo generic topic; chỉ topic/độ khó được gửi model; không có profile/child/artwork ref; skip path không tạo AI job; guide không chọn chủ thể tranh trẻ và sau đó vẫn capture rồi VLM subject review | BR-42/46; FR-P-11/FR-AI-15; AC-44 |
| AT-19 | Parent guide job đang chạy hoặc vừa hoàn tất | Timeout, limit refusal, unsafe/invalid output, người lớn skip/đóng guide hoặc TTL hết hạn | Capture flow vẫn dùng được; output invalid/unsafe không hiển thị; accepted guide asset bị xóa khi session kết thúc/TTL đến; lineage/expiry receipt không chứa nội dung trẻ; resource event ghi riêng sketch usage, không có video quota usage | BR-36/44/46; FR-AI-12/15; NFR-23/25; AC-45 |

<a id="srs-14"></a>
## 14. Quyết định và cổng triển khai

Q01–Q146 đã được chủ sở hữu trả lời và đối chiếu. Q145 là hình thức text-only tạm thời và được Q146 thay thế cho Parent pre-drawing guide.

### 14.0 Làm rõ đã được trả lời

| ID | Câu hỏi | Khuyến nghị hiện tại | Trạng thái |
|---|---|---|---|
| Q146 | Có nên cho Parent dùng line-sketch gợi ý do AI tạo, ví dụ guide vẽ con bướm 3–5 bước, như một lựa chọn riêng trước khi trẻ tự vẽ? | Có; đây là tùy chọn không bắt buộc. Dùng topic chung/độ khó đơn giản; không gửi child profile, tuổi cụ thể, voice, photo hay artwork; output riêng tư, có provenance và expiry/cleanup; skip/failure/timeout/limit không chặn capture; compute/rate cap sketch riêng, không dùng video quota. Q146 thay thế phần text-only tạm thời ở Q145. | ANSWERED — owner clarification, 2026-10-28; đưa vào SRS v2.2-draft, chưa phải sign-off toàn SRS |

Danh mục sau đây tổng hợp các gate kỹ thuật/vận hành/thương mại đã có owner/evidence cần đóng. Các quyết định sản phẩm Q01–Q146 đã được ghi nhận; chúng không tự đóng các gate triển khai bên dưới:

### 14.1 Danh mục issue/gate đang mở

Q01–Q146 giải quyết các quyết định sản phẩm nền. Bảng sau gom các quyết định kỹ thuật, pháp lý, thương mại và rollout còn phải có owner/evidence; nội dung SRS/Data Table Register vẫn là draft và các gate này chưa được đóng. `Mốc` là điều kiện milestone, không phải ngày lịch vì chưa có kế hoạch release được duyệt.

| ID | Issue/gate | Owner vai trò | Mốc cần đóng | Tác động nếu chưa đóng | Trạng thái |
|---|---|---|---|---|---|
| OI-01 | Android push provider ngoài Firebase; kiểm distributor, opt-in, invalidation, battery/background behavior | Mobile + Architecture | Trước P3/mobile push demo | Inbox/email vẫn chạy; Android push chưa thể cam kết, Q131 chưa đủ evidence vận hành | Mở POC; FCM bị repo rule loại |
| OI-02 | Benchmark chi phí video theo L40S, GPU seconds, 45 scene attempts/request, storage/output và giá quota | AI + Commercial + Billing | Trước bật full-video request live | Chưa chốt allowance mặc định, top-up price hoặc đơn vị kinh tế | Chưa benchmark |
| OI-03 | Hard cost reservation per request/day; xác nhận đủ budget trước Billing admission; ưu tiên hoàn tất request đã nhận | AI + Billing + Operations | Trước P1 video live | Cost cap giữa job có thể làm mất quota mà không có video; theo Q128 không hoàn | Thiết kế bắt buộc, giá trị cần benchmark |
| OI-04 | So sánh PostgreSQL outbox/RQ/Modal poller với Temporal cho saga dài | Architecture + Operations | Trước implementation workflow | Crash recovery/timer/cancellation có thể phức tạp hoặc tăng vận hành | Chưa có ADR so sánh |
| OI-05 | Controller/processor, DPA, authorization/consent, privacy notice, DSR, DPIA/assessment và escalation breach | Privacy/Legal + Product | Trước bất kỳ dữ liệu trẻ thật | Cấm real-child data/provider use và production launch | Chờ chuyên gia |
| OI-06 | Max retention theo profile/run/media/transcript/log/audit/payment; backup expiry và deletion proof | Privacy/Legal + Data owner | Trước real-data gate | Q66/Q129/Q133 chỉ phù hợp synthetic demo; lưu vô hạn không được đem sang production | Chưa chốt; demo giữ đến user-delete |
| OI-07 | Modal/provider region, cross-border transfer, object storage/hosting region và scratch deletion evidence | Privacy/Legal + Infra | Trước real-child data/provider transfer | Chỉ synthetic được phép gửi | Chưa review |
| OI-08 | Production host/network/region, availability SLO, RPO/RTO, alert destination, offsite backup/restore | Operations + Architecture | Trước production deployment | Không có SLA/recovery commitment; local target chỉ là mục tiêu draft | Chưa chọn |
| OI-09 | Merchant MoMo/VNPAY sandbox, recurring contract, callback signature/freshness, cancel/retry and failure reconciliation | Billing + Legal/Commercial | Trước P3 payment integration | Không thể bật payment; không dùng browser redirect làm bằng chứng | Adapter contract draft; sandbox chưa chạy |
| OI-10 | Hóa đơn điện tử/VAT, rounding/proration, consumer refund/support policy | Legal/Accounting + Commercial | Trước thu phí production | Rủi ro sai hóa đơn/giá và nghĩa vụ khách hàng | Chưa review; không chốt giá |
| OI-11 | Live PostgreSQL schema/row/index inventory and source-to-target migration rehearsal/restore | Data owner + Backend | Before migration | Rev31 crosswalk 92/140 and v2.3 baseline 89/137 are source-derived, not live DB state | Not inspected |
| OI-12 | Google Play Families/target-audience, child safety, privacy listing and app review requirements | Product + Mobile + Legal | Trước Play publication | Có thể cần đổi onboarding/permissions/store listing | Chưa review theo app listing thực tế |
| OI-13 | Teacher invitation/provisioning, account recovery, organization bootstrap and role support runbook | Identity + Product + Support | Trước external pilot | Teacher/admin không thể onboard/khôi phục có hỗ trợ | Requirement exists; detailed UX/ops not approved |
| OI-14 | Quy trình gửi report hỗ trợ riêng khi video bị xem là không phù hợp; phân biệt với in-run reject/regenerate | Product + Privacy + Safety | Trước support operations | Không có kênh operator nhận media; mặc định operator không được xem nội dung | Ngoài luồng V1; quyết định và quyền truy cập chưa chốt |
| OI-15 | Tập AI evaluation có tranh trẻ thật với consent/authorization, access, purpose, transfer và retention được duyệt | AI + Privacy/Legal | Trước claims về chất lượng thực tế | Synthetic benchmark không đại diện chất lượng với tranh thật | Không thuộc demo; chưa tạo |
| OI-16 | Giá trị mặc định quota included Parent/Teacher và giới hạn run/tháng/storage capacity | Product + Billing + AI + Operations | Sau benchmark; trước commercial launch | Không thể phát hành quota price/allowance hoặc forecast storage | Cấu hình để mở; chưa chốt số |
| OI-17 | Wireframe/interaction sign-off cho form profile, lesson extraction, Teacher Sketch Deck, script approval, quota/top-up, projection, delete/cancel và error/loading/accessibility states | Product + Design + Accessibility reviewer | Trước implementation UI | Màn hình kỹ thuật có thể không phù hợp thao tác nhanh của Parent/Teacher hoặc bỏ sót state | Chưa thiết kế wireframe; flow text tại §5/§19/§21 là baseline |
| OI-18 | POC adapter resumable upload trên MinIO/local storage: ghi từng application chunk thành object riêng, receipt/hash/expiry trong `core.upload_sessions` và `core.upload_parts`, replay idempotent, assemble bounded, final single PutObject, abort/TTL cleanup và AV boundary. Không dùng S3 Multipart Upload API; xác minh hành vi SDK MinIO đã pin. | Backend + Mobile + Infra | Trước Parent/Teacher media upload integration | Nếu SDK/storage semantics hoặc POC không đáp ứng checksum, resume và cleanup thì chưa bật media upload | Thiết kế đích đã chốt; POC còn mở |
| OI-19 | Synthetic POC cho Teacher Sketch provider/model: coverage toàn bộ activity, 3–5 nét tăng dần mỗi guide, độ rõ bố cục, phù hợp age band, safety, hash/lineage, license, latency và compute cost | AI + Teacher Product/Design | Trước bật AI Sketch cho occurrence | Sketch mơ hồ, thiếu hoạt động hoặc không ổn định có thể làm sai hướng dẫn lớp; không được gửi dữ liệu trẻ để bù chất lượng | Provider/model chưa chọn; cap riêng, chưa benchmark |

Các mục §29.2 là điều kiện triển khai tương ứng với OI-05–OI-16; bảng này là nguồn tổng hợp duy nhất cho owner, milestone, impact và trạng thái. OI-18 là POC kỹ thuật cho upload session/part tables và object-PUT chunk contract; OI-19 là cổng chất lượng/chi phí cho Teacher Sketch. Các chi tiết model/provider/payment payload sẽ được hoàn thiện theo tài liệu chính thức/sandbox trong ADR/implementation contract; không mô phỏng chữ ký hoặc payload của provider trong SRS.

<a id="srs-15"></a>
## 15. Nguồn và mức độ tin cậy

### Nguồn trong repository đã xem xét

- Quy tắc vận hành repository trong AGENTS.md và docs/governance.
- docs/architecture/OVERVIEW.md, PYTHON_BACKEND_ARCHITECTURE.md, DEPENDENCY_RULES.md, CONTRACTS_AND_INTEGRATION.md.
- ADR-0001, ADR-0017, ADR-0018, ADR-0019, ADR-0020, ADR-0021 và ADR-0022 đề xuất.
- Context, decisions, source register, approval, plan FEAT-063; khai báo bảng SQLAlchemy/Core hiện tại; danh sách Alembic revision, manifest và compose.yaml.
- Bản nháp luồng/kiến trúc FEAT-062 trước đó; giả định PixiJS motion trong tài liệu cũ đã bị thay thế.
- Phiếu quyết định runtime video FEAT-050 và bằng chứng multimodal FEAT-003. Bằng chứng hiện có của Qwen3-VL là NO_GO nên không chọn làm mặc định.

### Nguồn kỹ thuật/pháp lý chính thức được đối chiếu ngày 2026-10-27
- [Amazon S3 multipart upload limits](https://docs.aws.amazon.com/AmazonS3/latest/userguide/qfacts.html): multipart part tối thiểu 5 MiB (trừ part cuối); thiết kế application chunk này dùng object PUT riêng, không dùng S3 Multipart Upload API.
- [MinIO Go Client API: PutObject](https://docs.min.io/aistor/developers/sdk/go/api/): tài liệu hiện hành mô tả object dưới 128 MiB được gửi bằng single PUT; phiên bản SDK chính xác của dự án chưa được xác minh và vẫn cần POC trước implementation.

- [Yêu cầu hệ thống LTX-2.5](https://docs.ltx.io/open-source-model/getting-started/system-requirements) — nêu VRAM GPU tối thiểu từ 32 GB và yêu cầu Python/CUDA.
- [Hướng dẫn GPU Modal](https://modal.com/docs/guide/gpu) — liệt kê L4/L40S, L40S 48 GB GPU RAM; giá có thể thay đổi.
- [Modal local data](https://modal.com/docs/guide/local-data), [data residency](https://modal.com/docs/guide/data-residency), [Volumes](https://modal.com/docs/guide/volumes), [cloud bucket mounts](https://modal.com/docs/guide/cloud-bucket-mounts) — giới hạn cách demo MinIO local stage file và lý do chưa gửi media trẻ thật.
- [Phiên bản Python được hỗ trợ](https://devguide.python.org/versions/) — Python 3.13 là runtime đích đề xuất; xác minh tương thích runtime/library trước khi nâng repository.
- [Các bản phát hành PostgreSQL](https://www.postgresql.org/docs/current/release.html) và [chính sách version](https://www.postgresql.org/support/versioning/) — PostgreSQL 17 là baseline repo/demo; PostgreSQL 18 cần đánh giá trước migration/deployment.
- [Firebase xác minh ID token](https://firebase.google.com/docs/auth/admin/verify-id-tokens) — backend xác minh client ID token và lấy UID.
- [Firebase Authentication email action links](https://firebase.google.com/docs/auth/admin/email-action-links) — Firebase Admin SDK tạo link xác minh email/đặt lại mật khẩu để gửi qua email adapter; action code thuộc Firebase Authentication, không cần bảng token nội bộ.
- [Modal function invocation methods](https://modal.com/docs/guide/function-invocation-methods), [Modal FunctionCall SDK](https://modal.com/docs/sdk/py/latest/FunctionCall) — long-running call có thể submit bất đồng bộ, lưu call ref rồi poll; không giữ RQ worker chờ GPU.
- [PostgreSQL 17 Row Security](https://www.postgresql.org/docs/17/ddl-rowsecurity.html) — RLS policy và cảnh báo table owner/BYPASSRLS; app runtime roles không được sở hữu bảng.
- [Android Play Integrity](https://developer.android.com/google/play/integrity) — Android app/device integrity signal do backend xác minh; không thay user authentication.
- [Web Push API](https://developer.mozilla.org/en-US/docs/Web/API/Push_API), [UnifiedPush distributors](https://unifiedpush.org/users/distributors/), [UnifiedPush Android specification](https://unifiedpush.org/developers/spec/android/) — browser/Android push options. Android provider remains a synthetic POC gate; Firebase messaging is excluded by repository's Firebase-Authentication-only rule.
- [ClamAV scanning usage](https://docs.clamav.net/manual/Usage) — scanner/quarantine workflow candidate; verdict fail-closed trước parser/model.
- [RQ worker types](https://python-rq.org/docs/workers/) — worker scheduling/fairness reference; verify RQ/Redis license and deployment fit before adoption.
- [Temporal workflow execution](https://docs.temporal.io/workflow-execution), [Temporal tasks and timers](https://docs.temporal.io/tasks) — reference for durable workflow state, human-wait timers and recovery; Temporal is an alternative to evaluate, not a selected dependency.
- [Redis license terms](https://redis.io/legal/licenses/) — license review is a deployment gate for the proposed Redis version.
- [Index PostgreSQL 17](https://www.postgresql.org/docs/17/indexes.html) — tham chiếu index/partial index cho uniqueness phụ thuộc state.
- [MoMo Subscription](https://developers.momo.vn/v3/docs/payment/api/wallet/subscription/) — luồng subscription định kỳ, tần suất, request ID và lịch thanh toán.
- [Đặc tả kỹ thuật VNPAY Recurring Payment](https://sandbox.vnpayment.vn/apis/files/VNPAYGW_RecurringPayment_Techspec2.1.0-VN.pdf) — luồng recurring cho merchant. Phê duyệt merchant và hợp đồng cụ thể vẫn là cổng tích hợp.
- [Model card Qwen2.5-VL-7B](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct), [Qwen2.5-7B](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct), [VieNeu-TTS](https://huggingface.co/pnnbao-ump/VieNeu-TTS) — chỉ là ứng viên, chưa xác nhận mặc định.
- [Luật số 91/2025/QH15 về Bảo vệ dữ liệu cá nhân](https://chinhphu.vn/?classid=1&docid=214590&orggroupid=1&pageid=27160) — hồ sơ văn bản Chính phủ; SRS không kết luận tuân thủ pháp luật; cần chuyên gia pháp lý/quyền riêng tư xem xét trước xử lý dữ liệu trẻ thật hoặc chuyển dữ liệu cho AI provider.
- [Văn bản hợp nhất Luật Trẻ em số 108/VBHN-VPQH](https://vanban.chinhphu.vn/?classid=2629&docid=215227&pageid=27160) — văn bản hợp nhất chính thức làm bối cảnh an toàn trẻ em; dự án cần review pháp lý chuyên môn, không tự suy ra tuân thủ từ tài liệu kiến trúc.
- [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/) — chuẩn accessibility cho nội dung web; target Level AA là yêu cầu thiết kế, chưa phải chứng nhận.
- [W3C WCAG2ICT](https://www.w3.org/TR/wcag2ict/) — hướng dẫn áp dụng WCAG cho non-web software như Android; informative guidance, không tự tạo conformance claim.
- [Google Play Families Policy Requirements](https://support.google.com/googleplay/android-developer/answer/9893335) — yêu cầu cần rà trước khi xác định target audience/phát hành app.
- [ISO/IEC/IEEE 29148:2018](https://www.iso.org/standard/72089.html) và [IEEE 830-1998 status](https://standards.ieee.org/ieee/830/1222/) — 29148 là tham chiếu hiện hành cho requirements engineering; 830-1998 đã bị supersede. Không phải claim compliance của bản SRS này.

### Giới hạn độ tin cậy

- Con số 86 là mapping khai báo trong source, không phải kết quả introspection database đang chạy. Kiểm kê cột 51 bảng trong register trích từ repository và vẫn cần đối chiếu migration/schema thực tế.
- Ứng viên model, chi phí, hiệu năng và độ nhất quán nhân vật chưa benchmark trong tài liệu này.
- Field bảng mới và target action trong register là thiết kế logic đề xuất, không phải DDL đã chạy. Danh sách cột hiện tại là khai báo nguồn, không chứng minh database đã deploy khớp.
- SRS này là baseline sản phẩm/kiến trúc để xem xét, không thay tư vấn pháp lý hoặc bằng chứng hành vi deploy.
- Chủ sở hữu chọn review tài liệu bằng tiếng Việt, giữ nguyên tên kỹ thuật để dùng thống nhất. SRS và data-table register cần được duyệt trước khi bắt đầu diagram/PDF.

<a id="srs-16"></a>
## 16. Truy vết quyết định của chủ sở hữu

Bảng này nhóm các câu trả lời đã nhận thành cụm yêu cầu. SRS/register ghi baseline đã chốt; không giữ đề xuất cũ như thể chủ sở hữu đã chấp thuận.

| Cụm quyết định | Hướng đã chốt | Vị trí SRS | Vị trí register |
|---|---|---|---|
| Q01–Q07: ranh giới account/profile/organization | Parent và Teacher là hai account/scope; Parent chỉ chủ tài khoản truy cập; tổ chức quản lý roster; ID nội bộ phân biệt hồ sơ; một Teacher phụ trách mỗi lớp | §3–5; BR-02–07; FR-C/FR-T | §2–5 |
| Q08–Q20: activity, lesson import, voice, review, GPU và identity | Trace lịch sử Q08–Q20: Parent chỉ dùng catalog hoạt động đã duyệt; annotation thứ tự hiện hành B2 Q1=A: Parent không chọn activity trước video, lesson activity list hiện sau video xem được; quyền đọc và binding (tham chiếu lesson-version opaque tùy chọn qua cổng module Lesson; không gắn org/class/occurrence của Teacher; quyền đọc catalog/xem trước lesson tách khỏi điều kiện tạo video; không cấp quyền đọc mới) [Còn mở cho thiết kế vật lý: vị trí lưu vật lý tham chiếu lesson-version]. Teacher activity riêng cần checklist; một plan/occurrence; giới hạn file/no OCR; giới hạn voice/review; sửa chủ thể; giới hạn output/retry; L40S cho LTX; Firebase Auth | §4–7, §9.3, §10 | §4–7 |
| Q21–Q30: profile context, dữ liệu nhạy cảm và revision | Tuổi theo tháng + nhóm tuổi; không gửi tên trẻ AI; nhu cầu hỗ trợ do người lớn nhập, không chẩn đoán; giới hạn truy cập; tách lịch sử app/trải nghiệm ngoài/achievement; revision bất biến và snapshot được duyệt | BR-18–21; FR-C-05–07; §6, §11 | §5.3–5.6 |
| Q31–Q40: UX Parent, activity, story/video | Trace lịch sử Q31–Q40: Parent chỉ dùng catalog; annotation B2 Q1=A bỏ selection làm điều kiện trước video và đặt lesson list hậu video; quyền đọc (quyền đọc catalog/xem trước lesson tách khỏi điều kiện tạo video; không cấp quyền đọc mới); hai vai trò có tối đa ba rewrite; không sửa scene trực tiếp; hệ thống quyết định độ dài; revision cũ ẩn; xóa ở cấp run; stage dễ hiểu | BR-08, 13–16, 24–26; FR-P | §5, §5.6, §8 |
| Q41–Q70: Teacher/organization, tài liệu, voice, video và data lifecycle | Teacher có thể phụ trách nhiều lớp; admin xem roster nhưng không mặc định xem media; một enrollment active; một plan/occurrence; lesson revision; giữ audio gốc/transcript thô+đã sửa; subtitle/không nhạc; một script gate/không duyệt video; playback ngắn hạn; giữ đến khi user xóa; audit metadata; backup thủ công; bảng legacy chỉ đọc; snapshot run tối thiểu | §3–12; BR-05–06, 22–26; FR-T/FR-AI/FR-O | §3–10 |
| Q71–Q86: video mẫu, nhập profile, activity và xóa | Một trẻ/một activity được chọn; tối đa một video mẫu phát được/qua safety mỗi occurrence; Teacher nhập profile nhanh; một Teacher phụ trách/lớp; duyệt plan trước run; Trace lịch sử: Parent dùng catalog; theo B2 Q1=A, Parent không chọn activity trước video, Teacher sample vẫn pin một activity đã duyệt; binding/quyền đọc (tham chiếu lesson-version opaque tùy chọn qua cổng module Lesson; không gắn org/class/occurrence của Teacher; quyền đọc catalog/xem trước lesson tách khỏi điều kiện tạo video; không cấp quyền đọc mới) [Còn mở cho thiết kế vật lý: vị trí lưu vật lý tham chiếu lesson-version]. xóa run và media liên kết; lỗi trước playback không chiếm slot mẫu | BR-07–17, 26; FR-T; §6.1.1 | §5.4–5.6, §7–9 |
| Q87–Q101: capacity/subscription | 10 slot bao gồm; đơn giá/slot mua thêm tháng/năm; MoMo/VNPAY; grace 7 ngày; notification; chọn lớp khi downgrade, giữ chỉ đọc; prorate slot thêm; tắt auto-renew; không auto refund; video đầu + hai lần tạo lại | BR-28–33; FR-B; §5.3, §6.1.1, §7.5, §9.6–9.8 | §5.7 |
| Q102–Q104: rewrite, run lại và duyệt activity | Cả hai vai trò yêu cầu rewrite; Teacher thêm hướng lesson; run lỗi kỹ thuật có thể tạo run mới; Teacher activity riêng được xác nhận bằng checklist an toàn tại lớp | BR-08–17; FR-P/FR-T/FR-AI | §5.5–5.6 |
| Q105–Q111 (lịch sử; tuổi bị supersede bởi Q147–Q195) | Teacher xác nhận chiếu theo occurrence; xóa không mở lại sample slot; baseline từng ghi tuổi 36–155 tháng; gói cơ bản trả phí gồm 10 slot; mỗi accepted video request tính quota | BR-06, 10–11, 18, 26, 38; FR-T-16, FR-B-10–13 | §1, §4–7, §14; age scope mới ở §31 |
| Q112–Q114: owner quota, hết quota và carry-forward | Parent account/Teacher organization tách scope; quota tháng; hết quota chặn request mới nhưng giữ playback/dữ liệu; top-up carry-forward đến khi dùng | BR-38; FR-B-10–13; Billing grants + immutable usage ledger | §4, §7, §11, §21, §23; §5.7 |
| Q115–Q118: allowance, video bị từ chối, chu kỳ và FIFO | Số unit cấu hình riêng theo Parent/Teacher, chốt sau benchmark synthetic; ẩn video bị từ chối khi nhận request tạo lại; quota tháng dương lịch Asia/Ho_Chi_Minh; dùng included tháng hiện tại trước, rồi top-up FIFO | BR-16, 38; FR-P-09, FR-B-10–13; §11.1 | §5.7, §7–8, §12 |
| Q119–Q121: xóa run và quota | Xóa run không hoàn unit đã tiêu thụ, giữ tối thiểu usage ledger; top-up một lần, không tự gia hạn; bắt đầu giữa tháng nhận đủ allowance included tháng hiện tại | BR-26, 38; FR-B-10–13; §11, §14, §23 | §5.7, §7–8, quota grants |
| Q122–Q123: hoàn tất và hủy run | VIDEO_READY chờ lệnh hoàn tất/tạo lại nhưng có auto-closeout sau 168 giờ idle; hủy run chưa hoàn tất nhả khóa và xóa nội dung qua lifecycle; không hoàn unit hoặc mở lại sample claim | BR-39–40; FR-C-08, FR-T-15; §6, §11, §21–22 | §5, §7–9 |
| Q124–Q126: hết hạn quota | Included quota chưa dùng hết hạn cuối tháng; top-up carry-forward FIFO đến khi dùng | BR-38; FR-B-10–12; Billing grants + usage ledger; lịch sử diễn giải chỉ ở DECISIONS.md | §4.2, §5.7, §7, §12 |
| Q127–Q133: sample recovery, refund, idle closeout, reassignment, push và quota ledger | Sample claim giữ nguyên sau video playable đầu; mọi accepted request không refund; nhắc ở giờ 144 và đóng ở giờ 168 cho mọi trạng thái chờ người lớn; quyền run/media chuyển khi đổi Teacher; push mobile/web không dùng Firebase Messaging; Billing sở hữu grant + usage; AI job state tách run state | BR-10–11, 17, 38–40; FR-C-11, FR-T-13–15, FR-B-14, FR-O-10; AC-22–28, AT-01–09 | §4.2–5.8, §7–8, §11–14 |
| Q134: owner run/offboarding; Q135: upload session/part; Q136: nhắc email | Q134 đặt `DRAFT` vào adult-wait; khóa theo owner hiện tại tách khỏi creator và reassignment qua saga durable, emergency force-close chỉ ghi metadata/audit. Q135 thêm hai bảng Core, chunk object-PUT 4 MiB và final PutObject đơn. Q136 gửi email best-effort ở +144 giờ nếu owner hiện tại có email đã xác minh; inbox vẫn là nguồn chuẩn. | BR-39/41; FR-C-11/12; FR-T-14/17; §11, §21–24 | §2, §5, §7–9 |
| Q137–Q144: Teacher AI Sketch và pipeline video | AI Sketch Deck chỉ dành cho Teacher, dùng chung toàn occurrence, bao quát mọi activity trong plan và có 3–5 bước line-sketch cùng điều khiển Back/Next/select/skip/regenerate; Parent không có Teacher Deck và không preselect subject. Deck không có child context, không export PPTX và dùng compute/rate cap tách video quota. Video theo pipeline VLM → structured story/storyboard 5–15 scene → adult script review → Character Bible/reference → LTX-2.5/Modal L40S từng scene → consistency → FFmpeg + Vietnamese TTS/subtitles/no music → automated safety → private playback; không human final-video approval/public gallery/download. | BR-42–45; FR-T-18–20; FR-AI-01/13/14; NFR-33; UC-17; AC-33–37; AT-14–17 | §2, §5–11, §19, §21–22, §26, §30; DATA_TABLE_REGISTER §4–7 |
| Q145/Q146: Parent optional AI line-sketch | Q145 text-only là phương án trung gian đã bị thay thế. Q146 xác nhận Parent có thể chọn topic/độ khó chung để nhận AI guide 3–5 bước hoặc bỏ qua; không gửi dữ liệu trẻ, output tạm/private có provenance-cleanup, không tiêu video quota và không chặn capture. Q167 sau đó xác định Teacher Deck chỉ sinh khi được bật trong session. | BR-42/44/46; FR-P-11; FR-AI-15; AC-44/45; AT-18/19 | §1–2, §5–7, §13–14; DATA_TABLE_REGISTER §§4–7 |

<a id="srs-17"></a>
## 17. Truy vết yêu cầu tới kiến trúc

| Nhóm yêu cầu | Owner domain/data | Contract/thao tác | Bằng chứng chấp nhận cần có ở implementation sau |
|---|---|---|---|
| Tách role/account/profile | Parent, BE1 | OwnerScopeRefV1, ProfileRefV1 | Fixture contract phân quyền và bằng chứng chặn truy cập chéo scope |
| Một trẻ/một run hoạt động | Story, AI Jobs | StoryRunCommandV1, AiJobCommandV1 | Constraint database và evidence tạo trùng/đồng thời |
| Lớp/roster/capacity tổ chức | BE1, Billing | Entitlement port, organization command | Test ranh giới capacity/concurrency và authorization assignment |
| Import lesson và plan | Lesson, Learning Content | LessonOccurrenceRefV1, AssetRefV1 | Contract format/size/OCR/revision/approval |
| Story/context/review | Profile owner, Story | Profile snapshot và ScriptRevisionV1 | Allowlist snapshot, revision hash, rewrite/approval state |
| Upload ảnh/audio/lesson tiếp tục sau gián đoạn | Core Upload Session + Core Asset | UploadSessionV1, UploadPartReceiptV1, AssetRefV1 | Resume/chunk conflict/hash/TTL/AV POC; session/part tables là nguồn chuẩn của upload state |
| Tạo video/playback | Story, AI Jobs, Core Assets | AiJobStatusV1, AssetRefV1 | Retry, stale result, media validation và playback đúng scope |
| Billing và notice | Billing, Notifications | PaymentEventV1, NotificationCommandV1 | Signature/idempotency, grace/capacity và notification dedupe |
| Quota entitlement/usage | Billing (sole write owner) | VideoQuotaAdmissionV1, VideoQuotaSummaryV1; AI Policy compute reservation port riêng; Story giữ opaque refs | Grant, FIFO, exhaustion/top-up idempotent; không ghi/join SQL xuyên module |
| Chiếu cho lớp | Lesson, Story/Core Asset | ClassProjectionConfirmationV1 | Xác nhận occurrence, assignment revoke và token ngắn hạn |
| Security/vận hành | Core, interfaces/infrastructure | Error envelope, telemetry convention, rate-limit policy | Redaction, 429, dashboard, backup/restore, secret scan |
| Giữ legacy | Owner module hiện có | Alembic không phá hủy theo giai đoạn, compatibility và feature flag | Inventory trước/sau, đối soát và restore test |

Tài liệu draft này không khẳng định đã có implementation evidence.

<a id="srs-18"></a>
## 18. Thuật ngữ, giả định và ràng buộc hệ thống

### 18.1 Thuật ngữ

| Thuật ngữ | Định nghĩa |
|---|---|
| Tài khoản người lớn | Danh tính người lớn đã xác thực trong một role scope sản phẩm. Parent và Teacher là hai tài khoản tách biệt dù một người có thể đảm nhiệm hai vai. |
| Hồ sơ Parent | Hồ sơ trẻ do một tài khoản Parent sở hữu; tách biệt profile Teacher quản lý. |
| Hồ sơ được quản lý | Hồ sơ trẻ thuộc tổ chức và quản trị qua BE1. Mỗi thời điểm profile thuộc một roster lớp active. |
| Lớp | Container roster thuộc tổ chức, có đúng một Teacher phụ trách active. Không tạo runtime cộng tác. |
| Occurrence dạy | Một buổi/đợt dạy theo ngày hoặc tên của một lớp, có một lesson được import/review và một plan được duyệt. Đây là đơn vị của một video mẫu. |
| Lesson plan | Cấu trúc diễn giải lesson nguồn của một occurrence do Teacher xem xét; có mục tiêu học tập, hướng kể story và một/nhiều hoạt động lựa chọn. |
| Story run | Một record xử lý end-to-end cho một trẻ, từ tranh/ý tưởng đến script/video; active-owner lock thuộc Parent account hoặc Teacher phụ trách hiện tại, không thuộc creator.
| Active owner/current owner | Parent account sở hữu run Parent hoặc Teacher đang được BE1 phân công phụ trách lớp của run Teacher. `created_by_actor_ref` chỉ là provenance và không cấp quyền sau transfer. |
| Adult-wait / `ABANDONED` | State không có AI job đang chạy và cần thao tác người lớn. Reminder ở +144 giờ; ở +168 giờ `VIDEO_READY` thành `COMPLETED`, state adult-wait khác thành `ABANDONED`; nội dung giữ đến khi người dùng xóa. |
| Upload session / application chunk | Session bền vững có actor/scope/purpose, expiry và receipt; một chunk ≤4 MiB là object PutObject độc lập. Đây không phải part của S3 Multipart Upload API. |
| Video mẫu | Output đại diện cho một occurrence Teacher. Video ban đầu và các lần tạo lại chất lượng vẫn là một run mẫu cho một trẻ. |
| Story revision | Phiên bản script/storyboard sinh ra, bất biến. Mỗi run có bản đầu và tối đa ba lần AI viết lại. |
| Tạo lại video chất lượng | Full-video request sau khi người lớn thấy output không phù hợp và quay lại xem script. Tối đa hai lần sau request đầu; request được nhận tiêu thụ một quota unit kể cả lỗi kỹ thuật/safety block. |
| Grant quota video | Một lô entitlement bất biến do Billing cấp cho owner scope. Grant included được cấp theo tháng, hết hạn cuối tháng; top-up không hết hạn và carry-forward đến khi dùng. |
| Quota admission | Quyết định idempotent nhận một full-video request và phân bổ một unit khả dụng từ grant hợp lệ trước khi dispatch provider. Tách biệt rate limit và GPU concurrency. |
| Chiếu cho lớp | Teacher điều khiển hiển thị video mẫu duy nhất của occurrence cho cả lớp sau khi Teacher phụ trách xác nhận đối tượng/mục đích. Không cấp login lớp hoặc playback capability dùng lại. |
| Retry kỹ thuật | Tự thử lại tạo scene do lỗi hạ tầng/output. Tối đa hai lần retry sau lần đầu cho mỗi scene. |
| Catalog hoạt động đã duyệt | Hoạt động ngoài trời có version, được quản trị nội dung duyệt/phát hành. Không dùng định nghĩa catalog để đặt precondition Parent chọn trước story/video. Teacher sample ghim đúng một activity đã duyệt; quyền read/preview Parent và list lesson hậu video (tham chiếu lesson-version opaque tùy chọn qua cổng module Lesson; không gắn org/class/occurrence của Teacher; quyền đọc catalog/xem trước lesson tách khỏi điều kiện tạo video; không cấp quyền đọc mới). [Còn mở cho thiết kế vật lý: vị trí lưu vật lý tham chiếu lesson-version]. |
| Hoạt động Teacher riêng | Hoạt động chỉ áp dụng một occurrence, do Teacher phụ trách nhập và xác nhận qua safety checklist. |
| Snapshot context tối thiểu | Lựa chọn bất biến từ profile/context được phép, người lớn duyệt cho một run; chỉ chứa đúng một trẻ. |
| Asset nguồn | Tranh/audio/lesson gốc người lớn tải lên; luôn phân biệt với output model. |
| Kết quả stale | Kết quả bất đồng bộ có expected run/revision/input hash không khớp state hiện tại; được lưu dấu nhưng không áp dụng. |
| Dữ liệu demo tổng hợp | Tên, fact profile, artwork, lesson text và audio giả lập cho phát triển/demo, không định danh trẻ thật. |

### 18.2 Giả định

- Onboarding Parent/Teacher đã tồn tại hoặc sẽ được xây trên Firebase Authentication hiện tại. Cách mời/kích hoạt Teacher và xác minh người lớn là quyết định triển khai; không suy diễn Teacher role từ client claim.
- Tổ chức có ít nhất một admin; mỗi lớp active có đúng một Teacher phụ trách. Lớp không thể vận hành nếu thiếu phân công.
- Teacher import lesson nguồn trước khi tạo plan occurrence. Occurrence dùng revision nguồn để xem xét và chọn hoạt động.
- Người lớn có đủ thời gian review transcript giọng trẻ, subject ảnh, context và script theo role; Teacher sample còn duyệt lesson/plan/activity. Parent không có activity-selection gate trước story/video; biểu diễn stage/input (đầu vào theo role; Parent story prompt không đưa activity, lesson hoặc gợi ý catalog; Teacher prompt dùng đúng một activity đã duyệt. Nếu lesson-version ref không còn hợp lệ thì không đưa ref đó vào planner prompt; list hậu video tuân quy tắc C6.). Sản phẩm không phát hành video nếu thiếu tương tác người lớn tại cổng xác nhận script.
- Parent/Teacher có thể kết thúc run sau khi xem video sẵn sàng. Nếu không có thao tác có ý nghĩa ở mọi adult-wait state (kể cả DRAFT), hệ thống nhắc tại +144 giờ và đóng tại +168 giờ; `VIDEO_READY` thành COMPLETED, state khác thành ABANDONED. Nội dung giữ đến khi người dùng xóa; email reminder chỉ gửi best-effort nếu current owner có email đã xác minh.
- Demo local dùng nội dung tổng hợp. Nội dung trẻ thật không phải fixture hoặc cách vận hành tạm.
- Backend worker kết nối Modal qua provider transport được xác thực. MinIO local không được Modal truy cập trực tiếp.
- Chủ sở hữu cấu hình riêng giá subscription và merchant account thật. SRS không tự đặt giá VND.

### 18.3 Ràng buộc

- Một trẻ/run là invariant ở database, API, job, storage-lineage và UI, không chỉ là quy ước luồng.
- Identity/profile Parent và Teacher không dùng chung primary key, owner scope hoặc authorization path.
- Legacy session ID giữ ý nghĩa collaboration trước đây, không phải alias của story_run_id.
- Cần pin GPU image/model/library revision, parser library, email vendor, host/region production và storage endpoint ở giai đoạn sau.
- Không đảm bảo tuyệt đối giữ nguyên nhận diện trong video; đây là mục tiêu chất lượng được đo trên tranh synthetic và người lớn đánh giá.
- Không cho URL video công khai, download endpoint hoặc credential storage nằm trong client.

<a id="srs-19"></a>
## 19. Ca sử dụng chi tiết và các luồng thay thế

Các ca sử dụng không phụ thuộc vào cách triển khai cụ thể. Tên route và ánh xạ lưu trữ là đề xuất trong §9 và danh mục bảng. Mọi thao tác ghi đều yêu cầu principal đã xác minh, quyền hiện hành, idempotency khi áp dụng và chuyển trạng thái ở server.

### UC-01 — Parent đăng nhập và tạo hồ sơ trẻ

| Hạng mục | Đặc tả |
|---|---|
| Actor chính | Parent |
| Điều kiện tiên quyết | Firebase Authentication thành công; backend phân giải được tài khoản có vai trò Parent; scope hồ sơ thuộc tài khoản này |
| Kích hoạt | Parent chọn Thêm trẻ |
| Luồng chính | Backend kiểm tra các trường hồ sơ có giới hạn → tạo head hồ sơ Parent → tạo revision bất biến gồm tuổi theo tháng/nhóm tuổi và context do người lớn nhập → trả về profile ID và revision opaque |
| Luồng thay thế | Tuổi/nhóm không hợp lệ trả lỗi tại trường; cho phép trùng display name; từ chối vai trò không hỗ trợ hoặc thiếu Parent scope |
| Hậu điều kiện | Chỉ chủ sở hữu xem được hồ sơ. Không tạo liên kết đến hồ sơ Teacher, lớp hoặc tổ chức. |
| Dữ liệu/yêu cầu | parent.child_profiles, parent.profile_revisions, parent.profile_context_entries; FR-C-01/04/05 |

Việc tiếp nhận hồ sơ Teacher phục vụ cùng mục đích người dùng nhưng dùng aggregate hồ sơ do tổ chức quản lý, biểu mẫu có cấu trúc và quyền roster lớp hiện tại. Phiếu phụ huynh là nguồn thông tin do người lớn cung cấp; không nhập bằng OCR.

### UC-02 — Parent tạo và xem video câu chuyện

| Hạng mục | Đặc tả |
|---|---|
| Actor chính | Parent |
| Điều kiện tiên quyết | Parent có quyền với hồ sơ; người lớn này không có run chưa kết thúc nào khác; Parent không chọn/xác nhận activity trước story/video; catalog/lesson readiness và quyền đọc trước video (tham chiếu lesson-version opaque tùy chọn qua cổng module Lesson; không gắn org/class/occurrence của Teacher; quyền đọc catalog/xem trước lesson tách khỏi điều kiện tạo video; không cấp quyền đọc mới) [Còn mở cho thiết kế vật lý: vị trí lưu vật lý tham chiếu lesson-version]. |
| Kích hoạt | Parent bắt đầu tạo câu chuyện |
| Luồng chính | Tạo run gắn một hồ sơ → chụp/chọn một bức vẽ → nhập văn bản và/hoặc ghi âm → tải asset gốc lên → nếu có voice thì chuyển thành transcript → người lớn xác nhận/chỉnh transcript → VLM đề xuất chủ thể → người lớn xác nhận/chỉnh chủ thể → duyệt context snapshot tối thiểu → AI tạo kịch bản/storyboard → Parent có thể yêu cầu viết lại trong giới hạn → Parent xác nhận kịch bản/storyboard cuối → pipeline video chạy bất đồng bộ → API đánh dấu artifact sẵn sàng và cấp playback token → Khi video đã xem được, ứng dụng trình bày lesson activity list theo quyền; nguồn lesson/version và behavior READY/complete/hide/revoke (tham chiếu lesson-version opaque tùy chọn qua cổng module Lesson; không gắn org/class/occurrence của Teacher; VIDEO_READY sau kiểm tra kỹ thuật và an toàn; Parent không cần xem hết video; hoàn tất không có nghĩa đã làm hoạt động; kiểm quyền hiện hành trước khi trả nội dung; lesson bị thu hồi/gỡ phát hành thì ẩn danh sách, video không bị ảnh hưởng và không fallback sang catalog công khai); Parent có thể xem và kết thúc [Còn mở cho thiết kế vật lý: vị trí lưu vật lý tham chiếu lesson-version]. |
| Luồng thay thế | Từ chối audio quá dài/quá lớn trước inference; chỉnh transcript tạo revision mới; chỉnh chủ thể chạy lại VLM; người dùng có thể yêu cầu tối đa ba lần viết lại story; từ chối output model sai định dạng/cũ; hết retry kỹ thuật thì đánh dấu run thất bại; video sẵn sàng nhưng không phù hợp thì quay lại bước rà soát kịch bản trong giới hạn tạo lại để cải thiện chất lượng |
| Hậu điều kiện | Run Parent hoàn tất gắn một trẻ và context hồ sơ đã ghim, không đòi scalar activity như điều kiện trước video; liên kết lesson/activity-list hậu video và ref theo role (tham chiếu lesson-version opaque tùy chọn qua cổng module Lesson; không gắn org/class/occurrence của Teacher; Parent không cần activity_ref làm tiền điều kiện; Teacher sample vẫn ghim đúng một activity đã duyệt) [Còn mở cho thiết kế vật lý: vị trí lưu vật lý tham chiếu lesson-version; biểu diễn contract/schema theo role]. provenance kịch bản/video bất biến và artifact riêng tư có thể phát. Không trả URL tải xuống. |
| Dữ liệu/yêu cầu | story.*; ai_jobs.*; core.asset_metadata/core.asset_lineage; FR-P và FR-AI |

### UC-03 — Teacher tạo hồ sơ do tổ chức quản lý

| Hạng mục | Đặc tả |
|---|---|
| Actor chính | Teacher phụ trách; admin tổ chức có thể quản lý thành viên roster |
| Điều kiện tiên quyết | Teacher có phân công tổ chức và lớp đang active; lớp còn trong giới hạn sức chứa |
| Kích hoạt | Teacher chọn Thêm trẻ |
| Luồng chính | Teacher nhập các trường có cấu trúc → backend xác minh trách nhiệm lớp và scope tổ chức → tạo head hồ sơ và revision bất biến → tạo enrollment active cho lớp đã chọn → hồ sơ xuất hiện trong roster lớp đó |
| Luồng thay thế | Cho phép hồ sơ trùng display name; nếu hồ sơ đã enrollment active ở lớp khác thì phải chuyển/đóng enrollment trước; lớp bị tạm ngưng ở chế độ chỉ đọc; giới hạn sức chứa chặn tạo lớp mới, không chặn thay đổi hồ sơ trong lớp hiện có |
| Hậu điều kiện | Hồ sơ thuộc một tổ chức có tối đa một enrollment lớp active và không liên kết tài khoản Parent. |
| Dữ liệu/yêu cầu | be1.managed_profiles, be1.enrollments, be1.profile_revisions/context; FR-T-02/04/05 |

### UC-04 — Teacher nhập và duyệt occurrence giáo án

| Hạng mục | Đặc tả |
|---|---|
| Actor chính | Teacher phụ trách |
| Điều kiện tiên quyết | Teacher được phân công vào lớp đã chọn; occurrence cho phép ghi; file nguồn thuộc loại được hỗ trợ và nằm trong giới hạn |
| Kích hoạt | Teacher nhập giáo án cho một occurrence dạy học |
| Luồng chính | Tải file gốc lên → kiểm tra phần mở rộng, chữ ký nội dung, mã hóa và kích thước → trích xuất văn bản không OCR → lưu provenance trích xuất → Teacher rà soát và chỉnh văn bản nếu cần → tạo revision chỉnh sửa bất biến → xác định mục tiêu/hướng truyện/danh sách hoạt động → xác nhận checklist an toàn cho hoạt động riêng → duyệt plan revision |
| Luồng thay thế | Định dạng không hỗ trợ, file mã hóa, >25 MB, >100 trang/slide, archive lỗi hoặc không trích xuất được văn bản trả mã lỗi an toàn cụ thể; trang scan được đánh dấu OCR_NOT_SUPPORTED và không OCR; Teacher có thể thay file hoặc tự sửa văn bản trích xuất thành revision mới |
| Hậu điều kiện | Một occurrence có plan đã duyệt tham chiếu đến một revision văn bản cụ thể của tài liệu. Plan có thể liệt kê nhiều hoạt động; chưa có child run nào. |
| Dữ liệu/yêu cầu | lesson.occurrences, source_documents, document_revisions, plan_revisions, plan_activities; FR-T-06–09 |

### UC-05 — Teacher tạo video mẫu một trẻ cho occurrence

| Hạng mục | Đặc tả |
|---|---|
| Actor chính | Teacher phụ trách |
| Điều kiện tiên quyết | Plan occurrence đã duyệt; còn slot video mẫu; Teacher vẫn phụ trách; trẻ được chọn đang enrollment active trong lớp này; người lớn không có run khác đang active |
| Kích hoạt | Teacher chọn một trẻ và bắt đầu tạo video mẫu |
| Luồng chính | Tạo run gắn với một trẻ/occurrence/plan đã duyệt → ghim một hoạt động đã chọn → duyệt context hồ sơ tối thiểu → chụp bằng browser hoặc tải ảnh điện thoại lên → thêm văn bản/voice → rà soát transcript và chủ thể → AI soạn kịch bản → Teacher có thể yêu cầu viết lại trong giới hạn rồi xác nhận kịch bản → application reserve GPU budget worst-case qua AI Policy, sau đó Billing cấp quota admission atomic/idempotent → chạy video job → video qua kiểm tra an toàn được hiển thị ngay cho Teacher phụ trách → trước khi chiếu cho lớp, Teacher xác nhận đối tượng/mục đích sử dụng cho occurrence này → Teacher kết thúc hoặc đánh dấu không phù hợp → nếu không phù hợp, phải rà soát/xác nhận kịch bản và được cấp quota trước khi tạo lại để cải thiện chất lượng |
| Luồng thay thế | Từ chối mọi request có nhiều child ID; từ chối trẻ chưa được phân công hoặc plan cũ; nếu hết quota, trả VIDEO_QUOTA_EXCEEDED và không dispatch; request đã chấp nhận tiêu thụ quota dù sau đó lỗi kỹ thuật/bị chặn an toàn; lỗi kỹ thuật hoặc chặn an toàn trước playback để slot mẫu occurrence còn trống; sau khi chấp nhận một video mẫu có thể phát và đã qua an toàn, không được bắt đầu run mẫu độc lập khác cho occurrence; chỉ được tạo lại để cải thiện chất lượng trong cùng run; nếu chưa xác nhận trình chiếu thì không cấp token class-projection |
| Hậu điều kiện | Tối đa một video mẫu có thể phát và đã qua kiểm tra an toàn được giữ cho occurrence. Video đó gắn với một trẻ và một hoạt động. |
| Dữ liệu/yêu cầu | lesson.*, story.*, ai_jobs.*, billing.video_quota_grants/video_quota_usage; ai_policy.resource_* chỉ cho GPU/compute metering; notifications.inbox_items/push_endpoints; FR-T-10–16, FR-AI, FR-B-10–14, BR-09–17, BR-38 |

### UC-06 — Admin tổ chức quản lý sức chứa và lớp

| Hạng mục | Đặc tả |
|---|---|
| Actor chính | Admin tổ chức |
| Điều kiện tiên quyết | Admin có quyền admin tổ chức; có thể đọc subscription/sức chứa |
| Kích hoạt | Admin tạo lớp, mua slot, phân công Teacher hoặc hạ sức chứa |
| Luồng chính | Backend đọc sức chứa hiệu lực từ Billing → transaction tạo lớp khóa/kiểm tra slot còn trống → tạo lớp → admin phân công một Teacher phụ trách → cấp quyền roster |
| Luồng thay thế | Khi hết sức chứa, tạo lớp mới trả CLASS_CAPACITY_REACHED; admin có thể chuyển sang luồng billing để mua thêm sức chứa; các thao tác tạo lớp đồng thời được tuần tự hóa; lớp bị tạm ngưng chỉ xem được; khi hạ gói phải chọn lớp sẽ tạm ngưng |
| Hậu điều kiện | Số lớp active không vượt sức chứa hiệu lực; mỗi lớp cho phép ghi có một Teacher phụ trách; quyền xem media được quản lý riêng. |
| Dữ liệu/yêu cầu | be1.classrooms/assignments; billing.capacity_periods; FR-T-02/03, FR-B |

### UC-07 — Người lớn xóa run đã hoàn tất

| Hạng mục | Đặc tả |
|---|---|
| Actor chính | Chủ sở hữu Parent hoặc Teacher hiện đang được phân công phụ trách lớp; creator cũ chỉ còn provenance |
| Điều kiện tiên quyết | Run đã hoàn tất; caller có quyền; run chưa trong quá trình xóa |
| Kích hoạt | Người lớn chọn Xóa session/run |
| Luồng chính | API xác minh Parent owner hoặc Teacher phụ trách hiện tại → ghi lifecycle request → chặn cấp playback token mới → xóa transcript, audio/tranh đầu vào, context snapshot, story revision, asset scene/video được tạo và asset phái sinh riêng tư đủ điều kiện → ghi hoàn tất và audit chỉ có metadata |
| Luồng thay thế | Thất bại xóa object hiện tại được retry idempotent và trạng thái vẫn pending; giữ asset dùng chung đến khi đối soát các tham chiếu được phép khác; Teacher cũ sau reassignment không còn quyền xóa, Teacher phụ trách mới được xử lý theo policy lifecycle |
| Hậu điều kiện | Nội dung run bị xóa theo lifecycle. Invoice Billing và audit metadata tối thiểu không bị ảnh hưởng. Không có thao tác xóa video riêng hoặc thời gian chờ để khôi phục từ thùng rác. |
| Dữ liệu/yêu cầu | be1.data_lifecycle_requests, core.asset_metadata/lineage, story.*; FR-C-08, BR-26 |

### UC-08 — Admin billing của tổ chức gia hạn hoặc đổi sức chứa

| Hạng mục | Đặc tả |
|---|---|
| Actor chính | Admin tổ chức có quyền billing |
| Điều kiện tiên quyết | Tổ chức có liên hệ billing, kỳ billing được chọn và price version đã cấu hình |
| Kích hoạt | Mua/nâng gói, đổi thiết lập tự gia hạn, đến hạn gia hạn, thanh toán thất bại hoặc hạ gói |
| Luồng chính | Tạo snapshot invoice → bắt đầu thao tác subscription/thanh toán MoMo/VNPAY → xác minh callback provider → ghi event unique và payment attempt theo transaction → cập nhật subscription/sức chứa → đưa thông báo vào hàng đợi |
| Luồng thay thế | Quay về từ trình duyệt khi chưa xác minh callback thì invoice vẫn pending; callback trùng được xác nhận idempotent; thanh toán thất bại bắt đầu thời gian ân hạn; khôi phục trong thời gian ân hạn đưa subscription về active; hết ân hạn thì hạn chế tạo lớp/run mới; hạ gói lên lịch tạm ngưng lớp đã chọn tại mốc hiệu lực |
| Hậu điều kiện | Trạng thái sức chứa/thanh toán kiểm toán được và thông báo được khử trùng. Không lưu credential provider hoặc secret thẻ/phương tiện thanh toán. |
| Dữ liệu/yêu cầu | billing.*, notifications.*; FR-B-01–09, FR-B-13 |

### UC-09 — Người lớn yêu cầu xóa hồ sơ trẻ

| Hạng mục | Đặc tả |
|---|---|
| Actor chính | Chủ sở hữu hồ sơ Parent; với hồ sơ Teacher, Teacher được phân quyền hoặc actor lifecycle tổ chức theo policy vai trò cuối cùng |
| Điều kiện tiên quyết | Caller có quyền với hồ sơ; chưa có yêu cầu xóa nào đang active |
| Kích hoạt | Caller chọn Xóa hồ sơ trẻ |
| Luồng chính | Backend xác minh owner scope → đánh dấu hồ sơ không khả dụng cho run mới → thu hồi quyền hồ sơ/run/playback → tạo lifecycle request → lên lịch xóa run/context/media liên kết → đóng enrollment active nếu có → đối soát tham chiếu asset → ghi hoàn tất và audit tối thiểu |
| Luồng thay thế | Nếu job đang chạy thì yêu cầu hủy và loại bỏ output đến muộn; lỗi xóa object giữ lifecycle ở pending và retry; không tác động hồ sơ thuộc owner scope khác; yêu cầu audit pháp lý/tài chính hiện hành tiếp tục được quản lý riêng |
| Hậu điều kiện | Nội dung hồ sơ và media run liên kết bị xóa theo lifecycle; không tạo liên kết ẩn sang scope hồ sơ còn lại; lịch sử enrollment tổ chức có thể giữ metadata không chứa nội dung để giải thích lịch sử roster |
| Dữ liệu/yêu cầu | parent.child_profiles/data_authorizations; be1.managed_profiles/enrollments/data_lifecycle_requests; lifecycle asset Core; FR-C-10, BR-35 |

### UC-10 — Người lớn xem quota và mua đơn vị video

| Hạng mục | Đặc tả |
|---|---|
| Actor chính | Chủ tài khoản Parent hoặc admin billing tổ chức |
| Điều kiện tiên quyết | Tài khoản đã xác thực có scope áp dụng; caller có quyền mua; cấu hình giá/gói do server quản lý đang hiệu lực |
| Kích hoạt | Người lớn xem quota hoặc request generation bị từ chối vì không còn đơn vị |
| Luồng chính | Backend suy ra scope tài khoản Parent hoặc tổ chức Teacher từ principal đã xác minh → Billing trả tóm tắt tính từ grant hợp lệ và `video_quota_usage` → nếu caller chọn mua thêm thì server kiểm tra số lượng và price version → tạo invoice/payment attempt → xác minh callback MoMo/VNPAY idempotent → thêm quota grant Billing → tóm tắt mới phản ánh grant → caller có thể thử lại quy trình trước đó bằng request video mới sau khi grant khả dụng |
| Luồng thay thế | Request bị từ chối vì hết quota không tiêu thụ đơn vị và không tạo AI job; callback checkout lặp không tạo grant trùng; thanh toán failed/pending không tạo entitlement; request được chấp nhận khi còn quota tiêu thụ một đơn vị kể cả khi generation sau đó thất bại/bị chặn an toàn; khi hết quota vẫn xem được playback và lịch sử video hiện có |
| Hậu điều kiện | Billing tính quota từ grant append-only trừ usage ledger append-only; không có trường số dư còn lại mutable. Grant included chưa dùng hết hạn cuối tháng; top-up được chuyển tiếp đến khi dùng hết. Trong mỗi tháng dùng included trước rồi top-up FIFO (Q117–Q118, Q124–Q126). |
| Dữ liệu/yêu cầu | billing.video_quota_grants/video_quota_usage/invoices/payment_attempts/provider_event_receipts; ai_policy.resource_reservation/resource_event chỉ cho hạch toán GPU/compute; FR-B-10–13, BR-38 |

### UC-11 — Người lớn hủy run chưa hoàn tất

| Hạng mục | Đặc tả |
|---|---|
| Actor chính | Chủ sở hữu Parent hoặc Teacher hiện được phân công phụ trách lớp; creator cũ chỉ còn provenance |
| Điều kiện tiên quyết | Run chưa ở COMPLETED/FAILED/ABANDONED/DELETE_PENDING/DELETED; caller còn quyền theo assignment hiện tại; run revision hiện tại được biết |
| Kích hoạt | Người lớn xác nhận Hủy run |
| Luồng chính | Application command kiểm tra actor/state/revision và idempotency → trong một transaction chuyển run sang DELETE_PENDING và giải phóng khóa active → thu hồi playback/upload → ghi cancellation notice và lifecycle request → gửi hủy best-effort tới job/provider → lifecycle xóa nội dung liên kết → ghi DELETED và audit metadata tối thiểu |
| Luồng thay thế | Nếu provider đang chạy thì không chờ interrupt thành công để nhả khóa; kết quả muộn bị stale, không playable và được purge. Request video đã được nhận vẫn giữ quota usage. Teacher sample claim đã thành công vẫn còn ở occurrence kể cả khi media bị xóa. Gọi lặp cùng idempotency key trả cùng kết quả. |
| Hậu điều kiện | Run không còn chiếm khóa active ngay khi lệnh được chấp nhận; media/private content được xóa theo lifecycle; quota đã tiêu thụ và Teacher sample claim không được hoàn lại. |
| Dữ liệu/yêu cầu | story.runs; be1.data_lifecycle_requests; ai_jobs.cancellation_notice; core.asset_metadata/lineage; FR-C-08, BR-26, BR-40 |

### UC-12 — Admin tổ chức đổi Teacher phụ trách và offboard

| Hạng mục | Đặc tả |
|---|---|
| Actor chính | Admin tổ chức được cấp quyền quản lý lớp |
| Điều kiện tiên quyết | Lớp active có Teacher hiện hành; replacement thuộc tổ chức/provisioned. Normal transfer chỉ nhận nếu không có active-run lock conflict; emergency force-close được admin tổ chức tường minh trước retry. |
| Kích hoạt | Admin chọn đổi Teacher hoặc offboard Teacher hiện tại |
| Luồng chính | Backend preflight quyền/assignment version → BE1 ghi transfer-pending và revoke old access/token ngay, lớp thành read-only → Story owner-transfer command kiểm tra uniqueness và chuyển `active_owner_teacher_id`/lock trong Story transaction → BE1 finalize current assignment sau receipt → new Teacher được cấp access; giữ creator provenance; ghi audit metadata/inbox. Job hợp lệ tiếp tục, completion chỉ nhận theo input/hash/occurrence/assignment fence hiện hành. |
| Luồng thay thế | Teacher mới có run active thì Story trả conflict; saga bù BE1 về assignment cũ và khôi phục quyền cũ nếu được xác minh. Nếu thao tác bù timeout/mơ hồ, giữ transfer-pending/read-only và reconcile cùng idempotency key; không cấp content cho Teacher cũ/mới trước khi trạng thái nhất quán. Admin có thể force-close run xung đột bằng emergency Story command có reason/audit metadata; status thành ABANDONED, khóa được nhả, không xóa media hoặc cho admin xem. Sau đó admin retry reassignment. Quota/sample claim giữ nguyên. |
| Hậu điều kiện | Khi finalize, lớp có đúng một Teacher current; `created_by_actor_ref` không đổi; quyền mới chỉ mở sau lock receipt; admin không xem media. Transfer pending không cho tạo run. |
| Dữ liệu/yêu cầu | be1.organization_assignments/classrooms; story.runs(active owner); core.audit_events; notifications.inbox_items; FR-T-02/14/17, BR-05/06/41; Q130/Q134 |

### UC-13 — Provision Teacher và khôi phục tài khoản người lớn

| Hạng mục | Đặc tả |
|---|---|
| Actor chính | Admin tổ chức và người lớn cần kích hoạt/khôi phục tài khoản |
| Điều kiện tiên quyết | Kênh xác minh identity đã cấu hình; admin được xác thực; scope Parent/Teacher chưa bị tiết lộ qua public lookup |
| Kích hoạt | Admin mời Teacher hoặc người lớn khởi tạo khôi phục tài khoản |
| Luồng chính | Backend tạo/đảm bảo Firebase Authentication identity trước, ghi BE1 identity ở trạng thái chờ xác minh và assignment chưa active → Firebase Admin SDK tạo email-verification/password-reset action link → notification email adapter gửi link → người nhận xác minh và hoàn tất sign-in → backend xác minh Firebase ID token cùng `email_verified` rồi kích hoạt scope/assignment theo policy → trả kết quả tổng quát không tiết lộ UID ở scope khác. Firebase quản lý action code; ứng dụng chỉ lưu trạng thái identity/assignment, không thêm invitation-token table. |
| Luồng thay thế | Link hết hạn/đã dùng trả trạng thái tổng quát và cho admin gửi lại; conflict Parent/Teacher account trả `ACCOUNT_SETUP_UNAVAILABLE` chung; email provider lỗi giữ invitation pending và có retry hữu hạn; nếu Firebase Auth không phát/kiểm tra được action link, không kích hoạt account và chuyển yêu cầu sang trạng thái retryable. |
| Hậu điều kiện | Không có role claim do client tự cấp; audit lưu metadata; không lưu action token hoặc raw recipient email trong app database/log; provider-managed activation link được dùng một lần/hết hạn. |
| Dữ liệu/yêu cầu | be1.adult_identities/organization_assignments; core.audit_events; notifications; Firebase Authentication action-link adapter; không có token table; FR-C-01, FR-O-09 |

### UC-14 — Quản trị nội dung phát hành catalog hoạt động

| Hạng mục | Đặc tả |
|---|---|
| Actor chính | Quản trị nội dung |
| Điều kiện tiên quyết | Actor có quyền catalog; safety/content checklist và catalog schema version đang hiệu lực |
| Kích hoạt | Tạo, duyệt, phát hành, sửa hoặc retire một hoạt động ngoài trời |
| Luồng chính | Tạo immutable catalog revision → validate age/context/accessibility/safety metadata → reviewer khác hoặc quyền review độc lập phê duyệt → publish có effective time → Parent chỉ nhận version đã published; Teacher activity snapshot ghim đúng version |
| Luồng thay thế | Validation/safety thất bại thì revision ở draft/rejected, không thấy trong Parent catalog; sửa tạo revision mới; retire không đổi snapshot của run đã tạo |
| Hậu điều kiện | Catalog có provenance, revision và audit; hoạt động riêng Teacher vẫn chỉ trong occurrence và không tự trở thành global activity |
| Dữ liệu/yêu cầu | learning_content.records/versions/reviews/events/outbox; FR-P-05, FR-T-09, BR-08, BR-36 |

### UC-15 — Đăng ký, thu hồi và giao thông báo push

| Hạng mục | Đặc tả |
|---|---|
| Actor chính | Parent/Teacher đăng ký endpoint trên client; Notifications worker gửi |
| Điều kiện tiên quyết | Actor đã xác thực; notification permission được người dùng cấp; endpoint/provider được hỗ trợ trên client |
| Kích hoạt | Đăng nhập/bật thông báo, logout, thu hồi permission hoặc provider báo endpoint invalid |
| Luồng chính | Client gửi endpoint tới API qua TLS → backend kiểm tra actor/platform/provider và mã hóa endpoint → lưu fingerprint chống trùng → tạo inbox notice trước → dispatch push best-effort với payload tối thiểu → ghi delivery attempt/status |
| Luồng thay thế | Push bị từ chối, endpoint invalid, Android provider chưa hỗ trợ hoặc delivery lỗi thì vẫn lưu inbox; revoke endpoint và không lặp vô hạn; không gửi tên trẻ/media/playback URL |
| Hậu điều kiện | Inbox là nguồn chuẩn, push không thay đổi trạng thái nghiệp vụ; endpoint có thể revoke được và không lộ token trong log |
| Dữ liệu/yêu cầu | notifications.push_endpoints, inbox_items, delivery_attempts; FR-B-09/14, NFR-26, Q131 |

### UC-16 — Hết quota, mua top-up và gửi phản hồi video không phù hợp

| Hạng mục | Đặc tả |
|---|---|
| Actor chính | Parent hoặc Teacher phụ trách hiện tại |
| Điều kiện tiên quyết | Actor có quyền run; video generation chưa vượt giới hạn; quota scope được xác định từ identity/organization |
| Kích hoạt | Người dùng bắt đầu/tạo lại video, quota hết hoặc đánh dấu video không phù hợp |
| Luồng chính | UI hiển thị quota estimate/số request còn lại trước khi nhận full-video request → Billing admission idempotent ghi một usage unit trước dispatch → khi hết quota, hiển thị lý do/kỳ và nút mua nếu actor có quyền → sau thanh toán xác minh, người dùng chủ động bấm thử lại; khi đánh dấu không phù hợp, video hiện tại bị ẩn và run quay về script review trước lần tạo mới |
| Luồng thay thế | Bị từ chối trước admission thì không tiêu quota; đã nhận request rồi lỗi technical/provider/safety thì không hoàn unit theo Q128; playback cũ giữ nguyên khi quota hết nhưng video bị người dùng từ chối vẫn bị ẩn; không tự retry sau khi quota được cấp |
| Hậu điều kiện | Không có generation dispatch nếu hết quota; quota usage ledger không chứa nội dung trẻ; phản hồi chất lượng không tự cấp quyền operator xem video |
| Dữ liệu/yêu cầu | billing.video_quota_grants/video_quota_usage; story.video_generations/review_decisions; notifications; FR-B-10–14, FR-P-09, FR-T-12–16, BR-11/16/38 |

### UC-17 — Teacher tạo và trình chiếu AI Sketch Deck theo giáo án

| Hạng mục | Đặc tả |
|---|---|
| Actor chính | Teacher phụ trách occurrence |
| Điều kiện tiên quyết | Occurrence thuộc lớp được phân công; plan/activity đã được duyệt. Teacher bật line-sketch guide trong session mới tạo job; không bật thì use case không chạy. Age band có trong plan hoặc Teacher xác nhận; sketch rate/cost budget còn khả dụng. |
| Kích hoạt | Teacher bật line-sketch guide, mở deck READY để trình chiếu, hoặc yêu cầu tạo lại một sketch. Disabled/skip trước generation không tạo job/deck/asset. |
| Luồng chính | Khi đã bật, backend pin plan revision/hash và tạo `SketchDeckRevision=GENERATING` → AI phân tích activity/chủ thể của plan, tạo deck schema chuẩn → mỗi guide có 3–5 line-sketch bước → backend kiểm schema/coverage/safety/media/lineage và lưu asset qua Core → đánh dấu deck READY → Teacher xem preview, Back/Next/skip và trình chiếu trên nền trắng 16:9 → trẻ vẽ trên giấy → trong luồng video hiện có Teacher chọn một activity và child đại diện ngẫu nhiên đủ điều kiện, chụp tranh và chạy story-video mới; video chỉ xuất hiện sau pipeline/safety gate. |
| Luồng thay thế | Nếu Teacher không bật, occurrence tiếp tục không có deck/job. Nếu plan đổi, deck cũ thành STALE; regenerate tạo revision bất biến mới. Sketch lỗi có thể skip/regenerate; hết cost/rate cap trả lỗi sketch-specific, không tiêu video quota. |
| Hậu điều kiện | Occurrence có một deck revision READY gắn với plan hash hiện hành hoặc vẫn không có deck; trạng thái Back/Next/skip không lưu server. Deck dùng chung, không mang profile/tranh/nhận diện trẻ. Story video mẫu vẫn chỉ có một child và một activity/occurrence. |
| Dữ liệu/yêu cầu | lesson.sketch_deck_revisions/steps; lesson.plan_revisions/activities; core.asset_metadata/asset_lineage; ai_jobs.job/attempt; AI Policy compute metering; FR-T-18–20, FR-AI-14, BR-42–44, NFR-33 |

**Phản hồi hỗ trợ riêng:** V1 đã định nghĩa đánh dấu không phù hợp để ẩn video và quay lại script. Luồng gửi báo cáo hỗ trợ/đính kèm video cho operator chưa được xác định; mặc định không cấp cho operator quyền đọc media, và không thu thập media báo cáo cho đến khi quyền truy cập, consent/authorization và retention được duyệt.

<a id="srs-20"></a>
## 20. Ma trận phân quyền

Teacher được quyền đọc run/media theo lớp đang được phân công. Sau reassignment, quyền chuyển sang Teacher mới sau khi assignment commit, Teacher cũ và playback token cũ bị revoke ngay; `created_by` chỉ là provenance. Admin tổ chức không có quyền media mặc định. Trong demo, operator chỉ được truy cập metadata vận hành; quyền khẩn cấp đọc nội dung không thuộc baseline này.

| Tài nguyên/thao tác | Chủ hồ sơ Parent | Teacher phụ trách | Admin tổ chức | Admin nội dung | Operator hệ thống |
|---|---|---|---|---|---|
| Tạo/đọc/cập nhật hồ sơ Parent của mình | Có | Không | Không | Không | Không có quyền sản phẩm |
| Đọc/cập nhật ghi chú nhu cầu hỗ trợ Parent | Chỉ hồ sơ của mình | Không | Không | Không | Không có quyền sản phẩm |
| Tạo/đọc hồ sơ Teacher được quản lý | Không | Chỉ lớp được phân công | Chỉ trường roster/admin | Không | Không có quyền sản phẩm |
| Quản lý lớp/phân công Teacher | Không | Không | Tổ chức của mình | Không | Không |
| Quản lý thành viên roster | Không | Lớp được phân công theo policy | Tổ chức của mình | Không | Không |
| Đọc tài liệu/plan giáo án | Không | Teacher phụ trách occurrence | Mặc định chỉ metadata | Không | Không có quyền nội dung |
| Tạo/đọc/trình chiếu/regenerate AI Sketch Deck | Không | Teacher phụ trách occurrence | Mặc định không xem nội dung deck/media | Không | Không có quyền nội dung |
| Đọc catalog theo quyền hiện hành; không là lựa chọn activity bắt buộc trước Parent video (quyền preview/projection cụ thể (quyền đọc catalog/xem trước lesson tách khỏi điều kiện tạo video; không cấp quyền đọc mới)) | Chỉ catalog đã xuất bản | Chỉ catalog đã xuất bản | Chỉ catalog đã xuất bản | Rà soát/xuất bản | Không |
| Tạo hoạt động riêng cho Teacher occurrence | Không | Teacher phụ trách | Không | Không | Không |
| Tạo story run | Hồ sơ Parent của mình | Một trẻ trong lớp được phân công/occurrence đã duyệt | Không | Không | Không |
| Đọc story/kịch bản/transcript/video | Run Parent của mình | Run của lớp hiện được phân công, bao gồm run tạo trước khi phân công đổi | Mặc định không | Không | Không có quyền nội dung |
| Đánh dấu video sẵn sàng không phù hợp/tạo lại | Run Parent của mình | Run của lớp hiện được phân công, nếu run còn cho phép thao tác | Không | Không | Không |
| Xác nhận chiếu video cho lớp trong occurrence | Không | Teacher phụ trách hiện tại; ghi xác nhận tường minh theo occurrence | Không | Không | Không |
| Xem tóm tắt quota | Scope tài khoản Parent của mình | Scope tổ chức của Teacher được phân công | Có quyền billing trong tổ chức của mình | Không | Chỉ metrics vận hành tổng hợp |
| Mua đơn vị quota video | Chủ tài khoản Parent | Không | Có quyền billing trong tổ chức của mình | Không | Chỉ cấu hình provider |
| Xóa nội dung run đã hoàn tất | Run Parent của mình | Run của lớp hiện được phân công, theo lifecycle | Mặc định không | Không | Chỉ thao tác lifecycle |
| Hủy run chưa hoàn tất | Run Parent của mình | Run của lớp hiện được phân công, theo lifecycle | Không | Không | Chỉ thao tác lifecycle |
| Quản lý subscription/thanh toán/sức chứa | Không | Không | Có quyền billing trong tổ chức của mình | Không | Chỉ cấu hình provider |
| Xem health/metrics hệ thống đã loại thông tin nhạy cảm | Không | Không | Không | Không | Có |

Backend kiểm tra phân quyền ở mọi thao tác đọc/ghi, cấp playback token và hoàn tất bất đồng bộ. Role claim từ UI chỉ là gợi ý; backend tải và xác thực resource scope cùng phân công hiện tại. Phản hồi từ chối không được làm lộ việc hồ sơ/run của tổ chức khác có tồn tại hay không.

<a id="srs-21"></a>
## 21. Chi tiết API và tương tác client

### 21.1 Quy tắc HTTP dùng chung

- Mọi request production dùng HTTPS. Local Compose chỉ được dùng HTTP trên loopback/mạng phát triển.
- Base path có version, bắt đầu từ /v1. Thay đổi contract không tương thích cần path/schema version major mới và thời gian tương thích; có thể phát hành trường tùy chọn bổ sung trong version hiện hành.
- Backend trả correlation ID cho request trong mọi response. Client gửi idempotency key cho command đổi trạng thái và giữ nguyên key khi retry cùng một command logic.
- Firebase ID token được gửi trong header Authorization. Backend xác minh issuer, audience, expiry và signature rồi mới suy ra principal. Không tin role, owner ID, organization ID hoặc trường quyền hạn do request body cung cấp.
- Request body JSON có giới hạn. Binary upload dùng session/chunk API có kiểm tra media type, byte size và checksum; không gửi byte lớn trong command JSON, không cấp MinIO/S3 credential hoặc endpoint cho client. Từ chối trường lạ với command nhạy cảm về bảo mật hoặc chỉ bỏ qua khi contract có version cho phép rõ việc mở rộng tương thích về sau.
- Timestamp server theo UTC ISO-8601. Ngày hiển thị theo timezone cấu hình của tổ chức/người dùng; timezone mặc định được đề xuất cho giao diện billing là Asia/Ho_Chi_Minh và phải cấu hình được.
- API danh sách dùng cursor pagination với cursor opaque ổn định, page size mặc định 25 và tối đa 100. Thứ tự sắp xếp phải tường minh, xác định được; không dùng tên trường SQL do client gửi.
- Mọi response là resource/kết quả command có version hoặc error envelope chuẩn tại §9.8. Không serialize ORM entity hoặc response provider thô.

### 21.2 Khung contract tài nguyên

| Method và path | Actor | Cấu trúc request/bất biến | Response thành công |
|---|---|---|---|
| POST /v1/parent/profiles | Parent | Trường hồ sơ có giới hạn; không có organization ID | 201 profile ref + revision |
| GET/PATCH /v1/parent/profiles/{profile_id} | Parent sở hữu | PATCH có expected revision; tạo revision bất biến mới | 200 profile projection/revision hiện tại |
| POST /v1/organizations/{org_id}/classes | Admin tổ chức | Kiểm tra sức chứa hiệu lực trong transaction | 201 class ref hoặc CLASS_CAPACITY_REACHED |
| POST /v1/classes/{class_id}/assignments | Admin tổ chức | Chính xác một Teacher phụ trách active | 200 assignment revision |
| POST /v1/classes/{class_id}/profiles | Teacher được phân công | Trường hồ sơ có cấu trúc và expected class revision; một enrollment active | 201 profile/enrollment ref |
| POST /v1/lesson-occurrences | Teacher được phân công | Class ref, nhãn/ngày occurrence; xác minh sức chứa/phân công | 201 occurrence ref |
| POST /v1/lesson-occurrences/{id}/documents | Teacher được phân công | Attach asset ref từ upload session đã hoàn tất; chỉ PDF/PPTX/DOCX ≤25 MB/100 trang/slide; source hash do server xác minh | 202 extraction job + source ref |
| POST /v1/upload-sessions | Parent hoặc Teacher được phân quyền | Purpose, media type, expected byte size/hash, scoped target ref và idempotency key; server suy ra actor/scope | 201 upload session ref, chunk size (≤4 MiB), accepted-part set, expiry; không trả MinIO URL/credential; Core tables `upload_sessions`/`upload_parts` sở hữu resume state |
| GET /v1/upload-sessions/{upload_id} | Actor sở hữu session | Chỉ cùng actor/scope và session còn hiệu lực | 200 state, chunk receipts/bitmap, byte count và expiry |
| PUT /v1/upload-sessions/{upload_id}/parts/{part_no} | Actor sở hữu session | Raw chunk ≤4 MiB cấu hình, part number, SHA-256; same part/hash retry idempotent | 200 part receipt và tiến độ; part number trùng nhưng hash khác trả 409 |
| POST /v1/upload-sessions/{upload_id}/complete | Actor sở hữu session | Expected aggregate size/hash; không thể sửa purpose/scope | 202 complete/validation state; asset ref chỉ dùng được khi hash, media validation và AV scan đạt |
| DELETE /v1/upload-sessions/{upload_id} | Actor sở hữu session | Expected state/version; idempotent | 202 abort/purge state; partial bytes không được dùng |
| POST /v1/lesson-occurrences/{id}/plan-revisions | Teacher phụ trách | Document revision, objectives, hướng truyện và danh sách hoạt động | 201 plan revision nháp bất biến |
| POST /v1/lesson-occurrences/{id}/plan-revisions/{revision}/confirm | Teacher phụ trách | Expected plan hash và checklist an toàn của hoạt động riêng | 200 revision đã duyệt |
| POST /v1/lesson-occurrences/{id}/projection-confirmation | Teacher phụ trách | Occurrence đã duyệt và sample hiện tại đã qua kiểm tra an toàn; xác nhận tường minh audience/use; idempotency key | 200 confirmation receipt theo occurrence |
| POST /v1/lesson-occurrences/{id}/projection-playback-token | Teacher phụ trách | Xác nhận occurrence hiện tại, sample đã chọn, assignment version hiện tại | 200 token thời hạn ngắn để Teacher điều khiển chiếu cho lớp |
| POST /v1/story-runs | Parent hoặc Teacher | Chính xác một profile ref có kiểu; scope khớp role; Parent không có bước chọn/xác nhận activity trước story/video; Teacher dùng ref occurrence/plan/đúng một activity đã duyệt; schema field/nullable và lesson-version Parent (tham chiếu lesson-version opaque tùy chọn qua cổng module Lesson; không gắn org/class/occurrence của Teacher; Parent không cần activity_ref làm tiền điều kiện; Teacher sample vẫn ghim đúng một activity đã duyệt) [Còn mở cho thiết kế vật lý: vị trí lưu vật lý tham chiếu lesson-version; biểu diễn contract/schema theo role]. idempotency key | 201 run resource; không nhận mảng trẻ |
| POST /v1/story-runs/{id}/assets | Actor của run | Attach một asset tranh/audio đã qua upload validation; owner asset phải trùng run | 201/202 asset ref và trạng thái validation |
| POST /v1/story-runs/{id}/idea | Actor của run | Văn bản, audio ref hoặc cả hai; giới hạn audio; expected run revision | 202 input/ASR job refs |
| POST /v1/story-runs/{id}/subject-confirmation | Actor của run | Ứng viên đã xác nhận hoặc phần chỉnh sửa có giới hạn; expected VLM revision | 202 xác nhận được chấp nhận hoặc VLM rerun job |
| POST /v1/story-runs/{id}/context-confirmation | Actor của run | Snapshot version/hash và xác nhận tường minh của người lớn | 200 snapshot ref đã ghim |
| POST /v1/story-runs/{id}/story-rewrites | Actor của run | Gợi ý tùy chọn có giới hạn và được sàng lọc; expected story revision | 202 rewrite job hoặc 409 quá giới hạn viết lại |
| POST /v1/story-runs/{id}/script-confirmation | Actor của run | Chính xác script/storyboard revision/hash | 200 confirmation receipt; revision cũ trả 409 |
| POST /v1/story-runs/{id}/video-generations | Actor của run | Hash kịch bản hiện tại đã xác nhận; quality-reason code khi tạo lại; idempotency key | 202 intent ref; state `ADMISSION_PENDING` cho đến khi hai receipt rõ. Khi được nhận, state `ACCEPTED`/job ref chỉ sau budget reservation + quota admission. Quota denial trả 409 `VIDEO_QUOTA_EXCEEDED`; cost denial trả 503 `AI_COST_LIMIT_REACHED`; rejected intent không tạo usage/job/dispatch/cap |
| POST /v1/story-runs/{id}/video-unsuitable | Actor của run | Generation ID hiện tại và safe reason code | 200 run quay lại rà soát kịch bản hoặc lỗi giới hạn |
| POST /v1/story-runs/{id}/complete | Actor của run | Chỉ hợp lệ ở VIDEO_READY; run revision hiện tại; idempotency key | 200 trạng thái COMPLETED kết thúc run và nhả khóa active; không phải video approval |
| POST /v1/story-runs/{id}/cancel | Actor của run | Run chưa hoàn tất; run revision hiện tại; idempotency key | 202 trạng thái DELETE_PENDING; nhả khóa active trong transaction và bắt đầu hủy job/purge lifecycle |
| DELETE /v1/story-runs/{id} | Chủ sở hữu Parent hoặc Teacher được phân quyền | Chỉ run đã hoàn tất; lifecycle command idempotent | 202 deletion request/status |
| GET /v1/jobs/{job_id} | Actor của run được phân quyền | Job phải thuộc scope của actor | 200 trạng thái job có version |
| POST /v1/story-runs/{id}/playback-token | Actor của run được phân quyền hiện tại | Artifact hiện tại ở VIDEO_READY, đã qua kiểm tra; kiểm tra assignment/scope hiện tại | 200 playback token thời hạn ngắn, giới hạn vào một asset; run active đến complete, idle closeout hoặc cancel |
| POST /v1/organizations/{org_id}/subscription/checkout | Admin billing | Price version, kỳ billing và sức chứa mong muốn | 202 payment attempt/redirect instruction |
| GET /v1/video-quota | Chủ Parent, Teacher được phân công hoặc admin billing tổ chức | Suy ra scope từ actor đã xác minh; không nhận owner ID từ client | 200 quota được cấp/đã dùng/còn khả dụng và mốc kỳ đã tính |
| POST /v1/video-quota/purchases | Chủ Parent hoặc admin billing tổ chức | Số lượng/price version do server xác định; scope có kiểu suy ra từ phân quyền; idempotency key | 202 invoice/payment attempt; chỉ cấp grant sau khi xác minh thanh toán |
| POST /v1/payments/{provider}/callback | Provider | Payload provider đã ký; xác minh replay/idempotency | Acknowledgement riêng của provider; không dùng browser auth |
| GET /v1/notifications | Người lớn nhận thông báo | Cursor pagination | 200 inbox item không chứa media/story của trẻ |
| POST /v1/notifications/push-endpoints | Người lớn đã xác thực | Platform/provider type, encrypted endpoint registration proof, idempotency key | 201 endpoint ref; raw endpoint không log |
| DELETE /v1/notifications/push-endpoints/{endpoint_id} | Chủ endpoint | Actor scope, expected endpoint version | 204 revoked; không ảnh hưởng inbox |

Hình dạng route là contract sẽ chốt trong OpenAPI. Đặc biệt, body tạo story run phải biểu diễn một trường hồ sơ duy nhất; tuyệt đối không dùng children[], profiles[], participant_ids[] hoặc trường lớp làm subject.

### 21.3 Bảo mật upload và playback

- Upload trong demo local có thể đi qua API hoặc dùng upload grant một object có scope hẹp và thời hạn hết hạn. Grant chỉ trỏ đúng một asset key opaque, content type kỳ vọng và byte size tối đa. Đây không phải credential MinIO dùng chung.
- Sau upload, server xác minh hash, kích thước và chữ ký nội dung của object; asset chưa hoàn tất/chưa xác minh không được dùng trong AI job.
- Playback token có thời hạn ngắn, giới hạn cho một video ready và actor/run, đồng thời được kiểm tra lại theo quyền sở hữu Parent hoặc phân công Teacher hiện tại. Thu hồi phân công Teacher lập tức ngăn cấp token mới.
- Không để lộ tên bucket, object key, URL vĩnh viễn hoặc API liệt kê cho client. Không cung cấp chức năng export/download. Chỉ stream video qua route/token playback đã phân quyền.
- Ngăn dùng lại token ngoài thời hạn/tài nguyên được phép. Tránh ghi token vào app log, analytics, clipboard hoặc báo cáo lỗi.

### 21.4 Idempotency, concurrency và optimistic concurrency

- Command đổi trạng thái phải có idempotency key theo principal, operation và tài nguyên đích. Gửi lại cùng key/payload trả kết quả ban đầu; dùng lại key với payload khác trả INVALID_IDEMPOTENCY_KEY.
- Tạo run dùng quy tắc unique bền vững và transaction. Hai yêu cầu đồng thời từ cùng người lớn tạo một run; yêu cầu còn lại nhận ACTIVE_RUN_EXISTS.
- Thay đổi hồ sơ, lesson plan, story và script phải gửi expected revision/hash. Request cũ nhận STALE_REVISION cùng version hiện tại, không ghi đè head hiện tại.
- Callback provider dùng provider/event ID và xác minh signature, không dùng token idempotency của client.
- Tính lại số tiền/tiền tệ thanh toán và sức chứa mong muốn từ price version bất biến do server quản lý. Không bao giờ coi tổng tiền do client gửi là nguồn chuẩn.

### 21.5 Danh mục màn hình client

| App/khu vực | Màn hình hoặc surface bắt buộc | Hành vi chính |
|---|---|---|
| Android Parent | Đăng nhập/khôi phục tài khoản; danh sách/biểu mẫu hồ sơ trẻ; lịch sử run; chụp/chọn tranh; ý tưởng văn bản/audio; rà soát transcript; xác nhận/chỉnh chủ thể; rà soát context snapshot; catalog read/preview nếu Q4 được xác nhận là bề mặt độc lập, không phải selector activity trước story/video; rà soát script/storyboard; tiến độ job; trình phát video; lesson activity list sau video xem được (binding/quyền/projection (tham chiếu lesson-version opaque tùy chọn qua cổng module Lesson; không gắn org/class/occurrence của Teacher; quyền đọc catalog/xem trước lesson tách khỏi điều kiện tạo video; không cấp quyền đọc mới; VIDEO_READY sau kiểm tra kỹ thuật và an toàn; Parent không cần xem hết video; hoàn tất không có nghĩa đã làm hoạt động; kiểm quyền hiện hành trước khi trả nội dung; lesson bị thu hồi/gỡ phát hành thì ẩn danh sách, video không bị ảnh hưởng và không fallback sang catalog công khai)); Hoàn tất/hủy run [Còn mở cho thiết kế vật lý: vị trí lưu vật lý tham chiếu lesson-version]. tóm tắt quota/mua thêm; xóa run đã hoàn tất | Yêu cầu quyền theo ngữ cảnh; từ chối camera vẫn cho tải ảnh từ thư viện; từ chối microphone vẫn cho nhập ý tưởng; tiếp tục stage sau khi app chạy nền; trạng thái quota lấy từ server; không có batch trẻ/gallery/export |
| Web Teacher | Đăng nhập; chọn tổ chức/lớp; roster; biểu mẫu hồ sơ có cấu trúc; lesson occurrence; upload/trích xuất tài liệu; rà soát/chỉnh revision văn bản trích xuất; plan/objective/hướng truyện/checklist hoạt động; chọn trẻ; camera/upload; rà soát transcript/chủ thể/context; rà soát script; tiến độ job; trình phát video; xác nhận chiếu theo occurrence; Hoàn tất/hủy run; tóm tắt quota tổ chức/mua thêm; lịch sử run/occurrence | Chỉ hiện lớp được phân công; checklist an toàn chặn duyệt plan; occurrence hiển thị trạng thái một video mẫu; chiếu cần xác nhận; không tạo hàng loạt theo roster |
| Admin tổ chức | Dashboard tổ chức; xem sức chứa lớp; tạo/archive/tạm ngưng lớp; phân công Teacher phụ trách; quản trị roster; kỳ billing/invoice/trạng thái thanh toán; tự gia hạn/hạ gói; quota tổ chức/mua thêm; inbox thông báo | Khi tạo lớp kiểm tra sức chứa hiệu lực; hạ gói yêu cầu chọn lớp; màn hình billing không bao giờ để lộ media/story của trẻ |
| Quản trị nội dung | Nháp/rà soát/xuất bản catalog hoạt động | Version đã xuất bản là bất biến; thay đổi tạo version mới cần rà soát |
| Dashboard operator | Health, queue, trạng thái tổng hợp job, đối soát billing, backlog lifecycle | Chỉ metadata vận hành đã loại thông tin nhạy cảm; không drill-down hồ sơ/story/media |

Màn hình run giải thích thời điểm cần người lớn nhập liệu. Không hiển thị phần trăm bịa đặt. Trẻ hoặc người lớn không thể duyệt chỉ bằng cách đi qua các màn hình; xác nhận phải là command gắn với revision hash chính xác.

### 21.6 Hành vi khôi phục của client theo nhóm lỗi

| Nhóm/mã lỗi | Hành vi client | Chính sách retry |
|---|---|---|
| AUTH_REQUIRED, INVALID_TOKEN, TOKEN_EXPIRED | Làm mới hoặc xác thực lại bằng Firebase; chỉ quay về màn hình ban đầu sau khi token được xác minh | Retry một lần sau khi làm mới thành công; không lặp vô hạn |
| RESOURCE_NOT_FOUND (ID không tồn tại hoặc ngoài scope) | Báo không tìm thấy/không thể truy cập cùng một cách; làm mới danh sách tài nguyên được phép | Không retry cùng command tài nguyên |
| ACTION_NOT_ALLOWED (resource cùng scope nhưng actor không được phép thực hiện action) | Báo thao tác không được phép, không tiết lộ policy nội bộ | Không retry cùng command; chỉ tiếp tục khi role/assignment hợp lệ |
| ACTIVE_RUN_EXISTS | Đề nghị tiếp tục/mở run active hiện tại nếu caller sở hữu, hoặc hủy run chưa hoàn tất; không tạo run thứ hai | Chỉ thử tạo lại sau khi complete, hủy được chấp nhận hoặc run thất bại/kết thúc |
| MULTI_CHILD_NOT_SUPPORTED | Giải thích mỗi story chỉ chọn một trẻ; quay lại chọn trẻ | Không retry tự động |
| STALE_REVISION | Tải lại revision hiện tại và yêu cầu người lớn rà soát/xác nhận lại | Chỉ retry với expected revision mới |
| OCR_NOT_SUPPORTED, UNSUPPORTED_LESSON_TYPE, LESSON_FILE_TOO_LARGE | Giải thích hỗ trợ văn bản PDF/PPTX/DOCX và giới hạn; cho thay file hoặc sửa văn bản thủ công nếu được hỗ trợ | Không retry mù |
| TRANSCRIPT_NOT_CONFIRMED, SUBJECT_NOT_CONFIRMED, PROFILE_CONTEXT_NOT_CONFIRMED | Quay về màn hình rà soát tương ứng và giữ trạng thái đang sửa | Chỉ tiếp tục sau xác nhận tường minh |
| LESSON_PLAN_NOT_APPROVED | Đưa Teacher về bước rà soát plan occurrence | Không bắt đầu child run/job |
| STORY_REWRITE_LIMIT_REACHED | Giữ story hiện tại; cho người lớn xác nhận story hoặc dừng run | Không tự tạo story job mới |
| VIDEO_REGENERATION_LIMIT_REACHED | Báo đã hết lượt tạo lại để cải thiện chất lượng; playback tuân theo trạng thái generation hiện tại; output bị đánh dấu không phù hợp vẫn bị ẩn khỏi playback | Không tự retry |
| VIDEO_QUOTA_EXCEEDED | Hiển thị tóm tắt quota còn lại/kỳ và lựa chọn mua thêm được phép; giữ playback/lịch sử hiện tại | Không retry generation; chỉ thử lại sau khi grant được xác minh |
| AI_COST_LIMIT_REACHED trước admission | Giải thích hệ thống tạm thời chưa thể nhận request; không hiển thị như lỗi provider/model và xác nhận không tiêu quota | Cùng idempotency key trả cùng rejection; sau khi budget/circuit breaker cho phép, người lớn chủ động bấm lại để tạo command mới với key mới |
| PROVIDER_UNAVAILABLE | Hiển thị lỗi tạm thời an toàn kèm correlation ID và hướng dẫn retry | Chỉ retry nếu trạng thái job cho phép; giữ idempotency key |
| AWAITING_RECONCILIATION | Hiển thị “Đang kiểm tra trạng thái tạo”; không tạo video job khác | Poll trạng thái job đến khi có kết quả |
| SUBSCRIPTION_RESTRICTED / CLASS_CAPACITY_REACHED | Liên kết đến thao tác billing/sức chứa được phép; giữ dữ liệu hiện tại | Retry sau khi xác minh thay đổi thanh toán/sức chứa |
| RATE_LIMITED | Hiển thị hướng dẫn chờ ngắn | Chờ theo Retry-After; không lặp request liên tục |
| Trạng thái lifecycle DELETE_PENDING | Hiển thị đang xóa và chặn playback/run mới trên hồ sơ đã xóa | Poll trạng thái lifecycle; server retry xóa object |

Client không bao giờ hiển thị mã provider thô, lỗi SQL, stack trace, đường dẫn filesystem hoặc nội dung exception.

### 21.7 Hợp đồng giao tiếp với provider ngoài

Các cấu trúc sau là logical adapter contract để kiểm tra ranh giới và idempotency; chưa phải payload wire-format của MoMo/VNPAY hoặc Modal. Payload/headers/chữ ký chi tiết chỉ được hoàn thiện từ tài liệu chính thức và sandbox của đúng merchant/account.

| Adapter contract | Request tối thiểu | Response/event tối thiểu | Kiểm soát bắt buộc |
|---|---|---|---|
| `PaymentCallbackV1` | Provider kind, raw-body digest, provider event ID, merchant/payment ref, amount/currency, provider status, event time, received time, signature verification outcome | Acknowledge theo provider format sau durable receipt; canonical payment state/event ref | Xác minh chữ ký trên đúng bytes/algorithm theo provider; freshness/replay; unique event ID; kiểm amount/currency/order; callback idempotent; browser redirect không authoritative; secret chỉ backend |
| `ModalVideoJobRequestV1` | Opaque job/run ref, idempotency key, model/profile revision, config/policy version, one-child source manifest refs + hashes, output scratch prefix, media/output bounds, deadline, cancellation ref | Durable `FunctionCall` ref; state/result metadata; output refs/checksum/media type/byte size; provider error class | Không truyền secret hoặc payload trẻ tự do lớn qua function args; private job scratch; worker thoát sau spawn; poll/reconcile không giữ RQ worker; verify hash/schema/format; timeout/cancel/stale cleanup |
| `ModalStageResultV1` | FunctionCall ref, expected job/input/config hashes | `SUCCEEDED/FAILED/CANCELLED/UNKNOWN`, output manifest, checksum, duration/GPU seconds, provider version | UNKNOWN vào reconciliation, không gọi GPU lặp mù; output đến muộn là stale; chỉ ingestion backend cấp quyền playback |
| `NotificationDeliveryV1` | Recipient actor ref, endpoint ref, notice type, dedupe key, expiry | Accepted/delivered/failed/invalid endpoint; provider receipt ref | Inbox ghi trước; retry hữu hạn; payload tối thiểu; raw endpoint encrypted; revoke invalid endpoint; push fail không rollback business state |

**Wireframe/UI contract:** Không tạo wireframe đồ họa trong giai đoạn Markdown này. Màn hình và interaction state được mô tả trong §5, §19, §21.5–21.6; trước implementation cần product/design sign-off cho form profile, lesson extraction/review, story approval, quota exhaustion/top-up, class projection, cancellation/deletion, empty/error/loading states và accessibility flows. Đây là OI-17 trong §14.1.

<a id="srs-22"></a>
## 22. Job bất đồng bộ và xử lý event

### 22.1 Job envelope

Mỗi AI job bền vững mang theo:

| Trường | Mục đích |
|---|---|
| contract_name / contract_version | Ranh giới request/response có kiểu và version |
| job_id / idempotency_key | Định danh bền vững và khử trùng command |
| stage | LESSON_EXTRACT, SKETCH_DECK_PLAN, SKETCH_STEP_GENERATION, ASR, VLM_IMAGE_UNDERSTANDING, STORY_PLAN, STORY_REWRITE, STORYBOARD, SCENE_REFERENCE, VIDEO_SCENE, CONSISTENCY_VALIDATION, TTS, SUBTITLE, COMPOSITION, OUTPUT_SAFETY hoặc VALIDATION |
| owner_scope_ref / actor_role | Quyền sở hữu được server cấp và context policy |
| target_kind / target_ref / expected_target_revision | Chính xác một cặp target kind/ref trong mỗi job: `STORY_RUN`, `VIDEO_GENERATION`, `VIDEO_GENERATION_SCENE`, `LESSON_SOURCE_DOCUMENT`, `LESSON_LIBRARY_VERSION`, `LESSON_VERSION_VISUAL_ASSET`, `LESSON_SKETCH_DECK_REVISION` hoặc `PARENT_SKETCH_GUIDE`; optimistic concurrency theo target |
| correlation_id / input_hash | Nối stage/jobs trong cùng run/generation và ghim đúng tập input; correlation không thay thế target hoặc FK owner-local |
| source_asset_refs / source_hashes | Chỉ ref/hash tối thiểu cho artifact input; không copy binary, prompt hoặc profile fields vào job |
| pinned_lesson/activity/context refs | Chỉ khi stage cần; lesson/story owner xác minh scope và revision qua port, không lưu lại profile/context snapshot mutable trong job |
| model_profile_ref / config_hash | Lựa chọn runtime có thể tái lập, không chứa secret |
| attempt / deadline / cancellation_state | Xử lý có giới hạn; attempt lưu opaque workspace ref, manifest hash và cleanup state/receipt cho Modal synthetic |
| result_refs or safe_error | Output có kiểu hoặc lỗi an toàn; không có stack trace thô |

Contract job từ chối danh sách child ref và yêu cầu đúng một target kind/ref. ASR/VLM/story planning/rewrite target `STORY_RUN`; reference preparation, consistency, TTS, subtitle, composition và safety target `VIDEO_GENERATION`; mỗi inference LTX target đúng một `VIDEO_GENERATION_SCENE`; lesson extraction target `LESSON_SOURCE_DOCUMENT`; Teacher deck target `LESSON_SKETCH_DECK_REVISION`; Parent guide target `PARENT_SKETCH_GUIDE`, với request ID chỉ tồn tại trên AI Job, không có aggregate/table Parent riêng. Video scene row nối ngược đến job qua typed versioned ref, Story owner xác minh scene và generation khớp. StoryRun target resolve đúng một child từ Story canonical, không lặp profile ref trong AI Jobs. Cả hai sketch target không có child/profile/tranh trẻ; Parent guide chỉ chứa topic/difficulty và output-ref/lifecycle metadata. Tất cả loại job dùng chung dispatch/attempt/outbox; không ghi lịch sử mới vào JSON legacy arrays.

### 22.2 Dispatch và hoàn tất

1. Application command xác minh domain state và ghi aggregate revision cùng outbox event trong một PostgreSQL transaction.
2. Outbox dispatcher gửi job ref tối thiểu đến Redis/RQ. Queue chỉ dùng để chuyển phát; PostgreSQL vẫn là nguồn chuẩn cho job record.
3. Worker nhận job bằng lease/heartbeat, tải input có version và được phân quyền, xác minh hash rồi chỉ gọi provider port của mình.
4. Provider adapter ánh xạ response/lỗi riêng của provider thành kết quả nội bộ có kiểu. Adapter không sửa bảng story.
5. Worker gửi completion command đến application layer. Completion xác minh đúng target kind/ref/revision/hash; StoryRun target kiểm run/input và các lesson/activity ref áp dụng theo role/contract đã pin; không buộc Parent có pre-video activity selection; tập ref và hash theo role (tham chiếu lesson-version opaque tùy chọn qua cổng module Lesson; không gắn org/class/occurrence của Teacher; Parent không cần activity_ref làm tiền điều kiện; Teacher sample vẫn ghim đúng một activity đã duyệt) [Còn mở cho thiết kế vật lý: vị trí lưu vật lý tham chiếu lesson-version; biểu diễn contract/schema theo role]. generation target kiểm run/script/generation; scene target kiểm scene thuộc đúng generation/revision; Lesson document/deck target kiểm occurrence assignment/plan hash/deck schema; Parent guide target kiểm generic topic contract, safe output, owner scope và expiry policy.
6. Kết quả hợp lệ được ghi bởi owner tương ứng. Story scene job completion updates scene state/output ref; overall generation completion updates canonical `video_generations.state`, then the same Story transaction projects `story.runs.state` and current pointers. `VIDEO_READY` only after current generation READY, validation gates, and output asset exist. Lesson owner handles deck outputs; Parent guide returns a private temporary Core Asset ref with provenance/expiry and no profile/StoryRun attachment. AI job event/completion receipt stores execution disposition/hash only. Stale/rejected/expired outputs are cleaned through Core asset lifecycle. No worker writes across owner tables.
7. Lỗi kết thúc lưu safe code và correlation ID cho operator. Client nhận trạng thái stage đã nội địa hóa, không thấy stack trace.

Modal inference dài không chiếm một RQ worker trong lúc GPU chạy. Adapter gọi `Function.spawn()`, persist Modal FunctionCall `object_id` cùng attempt trước khi kết thúc worker; poller tải lại bằng `FunctionCall.from_id()` và kiểm tra kết quả không blocking. Nếu submit timeout nhưng không rõ Modal đã nhận job hay chưa, giữ `AWAITING_RECONCILIATION`, đối soát FunctionCall/outbox rồi mới quyết định; không tự submit job GPU trùng. Cancellation là best-effort, không thay đổi quota đã nhận.

### 22.3 Retry, hủy và khôi phục queue

- `ai_jobs.attempt` là sổ provider-attempt/retry duy nhất. Tạo scene cho phép đúng một lần inference ban đầu cộng hai retry kỹ thuật tự động; `story.video_generation_scenes` lưu trạng thái scene/job hiện tại và asset pointer, không lưu bộ đếm retry thứ hai. Ghi attempt trước khi gọi provider lần kế tiếp.
- Lệnh xác nhận script tạo một intent `VideoGeneration=ADMISSION_PENDING` có idempotency key bền vững trước mọi external admission. Orchestrator reserve compute budget ở AI Policy trước, rồi Billing ghi usage trong transaction riêng theo cùng request key. Chỉ sau hai receipt đã xác nhận, Story đổi intent thành `ACCEPTED`, gán generation number trong transaction Story và ghi outbox cho dispatch; request cap/run và quota chỉ tính từ trạng thái `ACCEPTED`. Nếu budget/quota bị từ chối, intent thành `ADMISSION_REJECTED`, quota usage và AI job không được tạo. Nếu tiến trình chết giữa bước hoặc timeout làm kết quả mơ hồ, reconciler đọc hai receipt theo cùng key; reservation chưa được gắn với Billing usage được release/expire, còn Billing usage đã ghi được hoàn tất idempotently thành accepted intent rồi dispatch đúng một lần. Reservation gắn với request accepted được giữ/settle theo job thực tế, không hết hạn khi inference còn trong thời hạn. Không có transaction SQL xuyên module; retry cùng key không tạo request/usage/inference thứ hai.
- Mỗi request tạo video đầy đủ được chấp nhận tiêu thụ nguyên tử một request-cap và một đơn vị quota Billing trước khi dispatch inference. Request vẫn được tính nếu sau đó lỗi kỹ thuật hoặc bị chặn an toàn. Chỉ lỗi kỹ thuật/safety trước khi có bất kỳ video playable nào claim occurrence mới để slot mẫu còn trống và cho phép run thay thế; sau khi sample claim đã commit thì không có recovery run khác cho occurrence, kể cả khi mọi quality regeneration đều thất bại. Nếu hết quota tháng của owner scope thì từ chối request và không tiêu thụ quota.
- Lỗi truyền tải tạm thời có thể được chuyển phát lại theo backoff cấu hình có giới hạn; idempotency ngăn chuyển trạng thái trùng. Retry chuyển phát này không tăng bộ đếm attempt scene trừ khi inference thực sự được gọi lại.
- Khi provider hỗ trợ, dùng provider request key xác định được từ job ID và stage attempt. Nếu timeout khiến kết quả inference không rõ và provider không đảm bảo truy vấn trạng thái/idempotency, đánh dấu cần đối soát; không tự khởi chạy job GPU trùng lặp không giới hạn.
- Không retry input không hợp lệ, từ chối phân quyền, file không hỗ trợ, OCR_NOT_SUPPORTED, dữ liệu người lớn lỗi định dạng hoặc bị policy từ chối.
- Các AI stage khác dùng retry policy vận hành có giới hạn, được định nghĩa theo từng adapter lúc triển khai; không âm thầm biến lỗi provider thành viết lại story hoặc đổi provider model.
- Hủy run chưa hoàn tất chuyển run sang DELETE_PENDING và giải phóng khóa active trong transaction ghi nhận lệnh. Ghi `StoryRunCancellationRequestedV1`, tạo lifecycle request, thu hồi playback/upload và yêu cầu hủy job đang chờ/chạy. Worker kiểm tra cancellation trước stage tốn tài nguyên và trước khi nhận kết quả; nếu không ngắt được provider, output đến muộn là stale, không playable và bị xóa qua lifecycle. Giữ quota usage đã nhận và sample claim Teacher thành công.
- Xóa run đã hoàn tất cũng tạo lifecycle request; lệnh delete không tạo refund hoặc xóa quota ledger/sample claim metadata.
- Scheduler bền vững đặt `adult_wait_started_at` khi không còn AI job hoạt động và run cần người lớn, phát reminder tại mốc +144 giờ rồi đóng tại +168 giờ. Inbox dùng dedupe key có run/state/deadline version; command hợp lệ của người lớn reset mốc và làm lịch cũ stale. Polling nền, push receipt và app heartbeat không reset idle. Closeout xác minh expected state/deadline/version trong transaction; VIDEO_READY→COMPLETED, adult-wait review state→ABANDONED, giữ nội dung và nhả khóa. AI job có deadline độc lập 6 giờ; timestamp lưu UTC, không dựa đồng hồ thiết bị.
- Khi lớp được phân công lại, BE1 assignment hiện tại là nguồn chuẩn quyền: workflow là saga bền vững, mỗi owner ghi trong transaction riêng và trao receipt có version. BE1 chuyển lớp sang transfer-pending/read-only và fence token/quyền Teacher cũ; Story command kiểm tra uniqueness, chuyển `active_owner_teacher_id`/active lock và tăng owner epoch; BE1 chỉ finalize assignment mới sau receipt Story. Nếu Story từ chối do Teacher mới có run active, saga bù trạng thái BE1 về assignment cũ; nếu kết quả bù mơ hồ, giữ transfer-pending/read-only và reconcile, không cấp content cho ai. Emergency force-close là command metadata-only riêng trước lần thử lại. Job hợp lệ không bị hủy chỉ vì transfer: completion kiểm tra run/input/script/activity/occurrence hashes, tổ chức/lớp còn hợp lệ, không bị cancel/delete và transfer receipt hiện hành; original creator/assignment version không cấp quyền. Nếu input/occurrence/class binding đã đổi, kết quả stale. Chỉ current owner có quyền xem/playback.
- Mất Redis không được xóa record job đang chờ. Khi khôi phục, dispatcher quét outbox/job state chưa tiêu thụ trong PostgreSQL rồi publish lại idempotent.
- Job không thể xử lý sau nhiều lần vẫn ở trạng thái FAILED kết thúc trong PostgreSQL. Operator có thể xem metadata an toàn và bắt đầu run mới được phép; không retry thủ công scene video trong run đã lỗi vượt quá giới hạn cấu hình.
- Có thể cấu hình riêng concurrency worker và concurrency Modal. Không chạy song song các run của trẻ; scene trong cùng run chỉ được chạy song song trong giới hạn GPU/tài nguyên đã cấu hình và được ghép theo thứ tự storyboard.

### 22.4 Trạng thái và tiến độ trên client

Client nhận stage code và nhãn dễ hiểu, ví dụ: “Đang nhận nội dung”, “Đang đọc tranh”, “Đang tạo kịch bản”, “Đang tạo từng cảnh”, “Đang ghép video”, “Đang kiểm tra video”, “Sẵn sàng phát”, “Cần chỉnh lại kịch bản”, “Không tạo được lần này”. Artifact bị chặn an toàn không bao giờ được cấp quyền playback.

StoryRun status gồm `run_state` riêng với `job_state`/`job_stage` cho ASR, VLM, story và video; SketchDeck status là resource Lesson riêng với job stage cho extraction/deck/step generation. Mỗi status trả target revision, version, tiến độ chỉ khi đo được, thời gian bắt đầu/cập nhật, retryability và safe error code. Điều này phân biệt xử lý model với người lớn đang review và tránh run/deck trông như bị treo. Không bịa phần trăm chính xác cho tác vụ model opaque. Client polling theo backoff tại §9.5, dừng ở trạng thái kết thúc và giảm tần suất khi chạy nền; push chỉ báo có cập nhật, client fetch trạng thái mới bằng authenticated API.

`GET /v1/story-runs/{id}` trả StoryRunDetailV1 tổng hợp để frontend không gọi nhiều endpoint theo từng module. Application read composer đọc Story làm gốc, gọi AI Jobs lấy stage/job status theo target, Core lấy asset/playback readiness, Lesson kiểm occurrence/assignment khi Teacher, và Billing trả quota summary khi được phép. Response có scene/generation status, current input/script/generation refs, error code an toàn, current authorization và playback ref ngắn hạn nếu đủ quyền. Không trả prompt/provider payload, transcript thô, profile support note, revision ẩn, hay tồn tại resource ngoài scope. Không lưu read-model table hay duplicate mutable state; endpoint dùng cursor/version để cache an toàn và ETag.

### 22.5 Danh mục domain event

Đây là các tên event nội bộ có version được đề xuất. Chúng là envelope metadata, không phải cơ chế chia sẻ nội dung hồ sơ/media thô giữa các module.

| Event | Chủ sở hữu | Consumer/mục đích | Payload tối thiểu |
|---|---|---|---|
| OrganizationCreatedV1 | BE1 | Khởi tạo Billing/tra cứu entitlement | organization ref, actor ref, version |
| ClassCreatedV1 | BE1 | Đối soát/kiểm toán sổ sức chứa | organization/class refs, assignment revision |
| ManagedProfileRevisionCreatedV1 | BE1 | Xác định điều kiện tạo snapshot context Story | profile ref, revision ref/hash, scope |
| LessonDocumentAcceptedV1 | Lesson | Dispatch worker trích xuất | occurrence/document refs, asset hash, parser contract |
| LessonPlanApprovedV1 | Lesson | Xác định điều kiện tạo Teacher run và Sketch Deck | occurrence/class/teacher refs, plan revision/hash |
| SketchDeckRequestedV1 | Lesson | Điều phối AI Job tạo deck cho occurrence | occurrence/plan revision/hash, target age band, assignment version, idempotency ref; không có child/profile ref hoặc tranh trẻ |
| SketchDeckReadyV1 | Lesson | Cho phép trình chiếu deck đã kiểm định | occurrence/deck revision ref, current plan hash, step count, schema version; không có nội dung nhạy cảm |
| SketchDeckGenerationFailedV1 | Lesson | Hiển thị lỗi an toàn và cho Teacher thử lại theo giới hạn | occurrence/deck revision ref, safe error code, retryable, correlation ref |
| StoryRunCreatedV1 | Story | Điều phối job/kiểm toán | run ref, actor role, một profile ref, run revision |
| StoryInputAcceptedV1 | Story | Lập kế hoạch job ASR/VLM | run/input refs, source hash; không có binary/text |
| TranscriptConfirmedV1 | Story | Điều kiện trước cho Story planner | run/transcript revision/hash |
| SubjectConfirmedV1 | Story | Điều kiện trước cho Story planner | run/understanding revision/hash |
| ContextSnapshotApprovedV1 | Story | Điều kiện trước cho Story planner | run/snapshot ref/hash và allowlist version |
| StoryRevisionCreatedV1 | Story | Rà soát UI/sẵn sàng cho job | run/story revision/hash, rewrite index |
| ScriptConfirmedV1 | Story | Xác định điều kiện tạo video job | run/revision/hash, ref người lớn xác nhận |
| VideoGenerationRequestedV1 | Story | Dispatch AI Jobs | run/generation ref, hash story đã xác nhận |
| VideoOutputSafetyPassedV1 | Story | Cho phép chuyển sang playback | run/generation refs, policy version, safe decision code, tóm tắt độ bao phủ |
| VideoOutputSafetyBlockedV1 | Story | Chặn playback và quay lại rà soát kịch bản | run/generation refs, policy version, safe finding codes |
| VideoGenerationCompletedV1 | Story | Sẵn sàng playback/đảm bảo duy nhất sample | run/generation/artifact refs; output hash vẫn canonical trong metadata Core Asset |
| VideoGenerationFailedV1 | Story | Trạng thái run an toàn/metrics lỗi | run/job ref, safe failure code |
| VideoQuotaGrantIssuedV1 | Billing | Cập nhật quota khả dụng sau khi xác minh giao dịch mua hoặc cấp quota tháng | owner-scope ref, quota-grant ref, units, period/expiry và event ref; không có dữ liệu trẻ/run/media |
| VideoQuotaUnitConsumedV1 | Billing | Ghi nhận bất biến một unit cho accepted full-video request trước dispatch | owner-scope ref, grant ref, usage ref, idempotency fingerprint và units=1; không có dữ liệu trẻ/run/media hoặc outcome chưa biết |
| ClassProjectionConfirmedV1 | Lesson | Cấp token thời hạn ngắn để Teacher điều khiển trình chiếu | occurrence ref, generation ref, responsible-Teacher ref, assignment revision và thời điểm xác nhận |
| TeacherAssignmentChangedV1 | BE1 | Chuyển run/media access sang Teacher hiện được phân công; revoke quyền cũ và fence stale jobs/tokens | class ref, old/new Teacher refs opaque, assignment version, thời điểm hiệu lực; metadata only |
| StoryRunIdleReminderRequestedV1 | Story | Gửi in-app/push reminder một ngày trước closeout | run ref opaque, expected state/deadline version, dedupe key; không có content |
| StoryRunIdleClosedV1 | Story | Đóng run theo 7-day inactivity rule và nhả active lock | run ref opaque, prior state, COMPLETED/ABANDONED result, expected version, occurred_at |
| StoryRunCancellationRequestedV1 | Story | Giải phóng khóa active và bắt đầu lifecycle hủy/xóa run chưa hoàn tất | run ref, actor ref, expected revision, lifecycle request ref, safe reason code; không có media/content |
| StoryRunDeletedV1 | Story | Xóa lifecycle/object | run ref, lifecycle request ref, scope |
| PaymentVerifiedV1 | Billing | Kích hoạt sức chứa/thông báo | invoice/subscription ref, amount/currency, provider event ref |
| SubscriptionRestrictedV1 | Billing | Chặn command tạo lớp/run mới | organization ref, capacity period hiệu lực, state |
| CapacityClassSuspensionScheduledV1 | Billing | Đưa trạng thái chỉ đọc vào BE1 tại thời điểm hiệu lực | change-group ref, một class ref, thời điểm hiệu lực, capacity period |
| BillingNoticeRequestedV1 | Billing | Outbox thông báo | organization/billing recipient ref, notice template và dedupe key |

Mỗi event envelope có event ID, event name/version, occurred-at UTC, producer module, aggregate ref/version, correlation ID và tham chiếu idempotency/dedupe. Consumer lưu receipt trước khi tạo side effect. Event được retry theo cơ chế at-least-once; handler phải idempotent. Không đưa display name, transcript, story text, secret provider hoặc byte media vào event.

<a id="srs-23"></a>
## 23. Chi tiết vòng đời billing

### 23.1 Mô hình capacity và giá

- Mỗi tổ chức có 10 slot lớp trong gói cơ bản; phí gói cơ bản và phí mỗi slot bổ sung được cấu hình, version hóa; chu kỳ billing tháng hoặc năm, không chia tier.
- Giá được lưu thành phiên bản bất biến bằng VND. Giá mới áp dụng cho báo giá/kỳ mới theo ngày hiệu lực; invoice đã phát hành giữ snapshot giá/số tiền.
- Capacity lớp hiệu lực bằng 10 slot cơ bản cộng slot add-on đã thanh toán trong kỳ, trừ lớp được chọn tạm ngưng khi downgrade có hiệu lực. Chỉ lớp active trong capacity mới được ghi; lớp tạm ngưng vẫn được đọc/quản lý ở trạng thái chỉ đọc.

### 23.2 Nâng capacity và prorate

Khi admin mua thêm slot giữa kỳ:

1. Backend lập quote/invoice snapshot từ phiên bản giá, phần thời gian còn lại và số slot tăng.
2. Checkout MoMo/VNPAY bắt đầu qua payment adapter. Browser redirect không phải bằng chứng thanh toán.
3. Event thanh toán thành công đã xác minh được deduplicate; trong transaction, cập nhật payment attempt/invoice và tạo capacity period/add-on hiệu lực.
4. Slot kích hoạt ngay sau khi xác minh thành công.
5. Phí prorate dựa trên thời gian còn lại của kỳ provider, không đổi ngày gia hạn. Invoice lưu giá cơ bản, số lượng tăng, đầu/cuối kỳ, tỷ lệ thời gian còn lại, số tiền VND làm tròn và phiên bản giá. Công thức sau là quy tắc xác định được đề xuất, phải hiện trong quote trước thanh toán.

Công thức đề xuất: phí add-on prorate = số slot tăng × giá/slot cả kỳ × (số giây còn lại / tổng số giây kỳ provider hiện tại), làm tròn đến VND nguyên gần nhất theo half-up. Dùng timestamp UTC; lưu tỷ lệ và số tiền làm tròn trong invoice snapshot. Thuế/giảm giá là cấu hình thương mại riêng.

Callback bị trễ thì UI báo đang chờ; không kích hoạt slot trước xác minh. Thanh toán thất bại không đổi capacity. Callback trùng/sai thứ tự không tính phí hoặc kích hoạt hai lần.

### 23.3 Gia hạn, ân hạn và hạn chế

| Sự kiện | Kết quả subscription/capacity | Quyền người dùng |
|---|---|---|
| Còn 7 ngày đến hạn | Lên lịch nhắc | Quyền hiện tại |
| Còn 1 ngày đến hạn | Lên lịch nhắc | Quyền hiện tại |
| Gia hạn thành công đã xác minh | Bắt đầu kỳ mới đã thanh toán | Đủ capacity |
| Gia hạn thất bại | GRACE 7 ngày; thông báo trong app/email | Lớp, roster, lịch sử, playback và cập nhật thanh toán hiện có vẫn dùng được; vẫn tạo lớp/run mới trong ân hạn |
| Khôi phục thanh toán trong ân hạn | ACTIVE, đối soát invoice | Khôi phục đầy đủ |
| Hết ân hạn chưa trả | RESTRICTED; gửi thông báo | Không tạo lớp/run mới; vẫn đọc/quản lý lớp, roster, lịch sử và thanh toán hiện có |
| Tắt auto-renew | CANCEL_AT_PERIOD_END | Dùng tính năng đã trả đến hết kỳ |
| Hết kỳ không gia hạn | RESTRICTED hoặc CANCELED theo provider | Giữ dữ liệu; hạn chế tạo mới |

Hạn chế chỉ bắt đầu sau đủ 7 ngày ân hạn, theo quyết định của chủ sở hữu.

### 23.4 Hạ capacity, hủy và thông báo

- Admin giảm số slot add-on và chọn lớp tạm ngưng trước khi xác nhận.
- Billing ghi một subscription_events row cho mỗi lớp được chọn, với chung capacity_change_group_ref, class ref, capacity trước/sau, kỳ capacity và timestamp hiệu lực. Commit toàn bộ lựa chọn nguyên tử trước xác nhận downgrade.
- Capacity đã trả giữ đến ranh giới kỳ. Kỳ sau, event CapacityClassSuspensionScheduledV1 version hóa chiếu lớp đã chọn thành chỉ đọc trong BE1; retry idempotent, đối soát event group với class refs. Không xóa lớp/roster/run history. Chuyển lớp/kích hoạt lại cần capacity.
- Tắt auto-renew ngăn lần thu tiền tiếp; không tự hoàn tiền phần kỳ đã dùng. Ngoại lệ V1 xử lý thủ công ngoài billing tự động.
- Khóa dedupe thông báo trong app/email là organization + trigger/event + period + recipient. Nhắc trước hạn 7 ngày và 1 ngày; thông báo thành công/thất bại/hết ân hạn theo event.
- Lỗi gửi retry với backoff giới hạn và được ghi nhận; không đảo payment/capacity đã xác minh. Admin xem trạng thái gửi, không xem nội dung trẻ.

### 23.5 Grant, usage và top-up quota video

- Parent quota thuộc một tài khoản Parent; Teacher quota thuộc tổ chức. Backend suy ra owner scope từ principal và assignment đã xác thực; client không chọn owner ID/quota.
- Billing sở hữu `billing.video_quota_grants` và `billing.video_quota_usage`. Grant là entitlement append-only; usage là ledger append-only, mỗi accepted full-video request ghi đúng một unit và tham chiếu grant đã dùng. AI Policy `resource_reservation`/`resource_event` chỉ đo platform GPU/compute capacity và chi phí tài nguyên; resource event là idempotency ledger command mới, còn bảng `resource_receipt` lịch sử không ghi thêm và không tham gia quota sản phẩm.
- Grant monthly included cấp riêng theo Parent/Teacher, số lượng chốt sau synthetic cost/latency benchmark. Scope bắt đầu giữa tháng nhận đầy đủ included allowance tháng đó, không prorate (Q115, Q121). Included grant hết hạn cuối tháng lịch `Asia/Ho_Chi_Minh`; phần dư không chuyển tháng sau. Top-up là giao dịch mua một lần, không tự gia hạn và không hết hạn; dùng grant included hiện tại trước rồi top-up theo FIFO (Q114, Q117–Q120, Q126).
- Quota admission là use case của Billing qua port có version. Story ghi một intent `ADMISSION_PENDING`; application saga lấy compute-reservation receipt từ AI Policy, sau đó gọi Billing để kiểm tra scope/grant và ghi usage trong transaction riêng do Billing sở hữu. Chỉ khi cả hai receipt có trạng thái xác nhận, Story chuyển generation intent sang `ACCEPTED` trong transaction Story và ghi outbox; không có một transaction PostgreSQL bao trùm các module. Nếu budget/quota bị từ chối thì saga ghi intent `ADMISSION_REJECTED`, release reservation nếu có và không dispatch. Nếu outcome không rõ sau crash/timeout, reconcile bằng cùng idempotency key trước dispatch; usage đã commit ở Billing phải được nối lại với Story intent đúng một lần, không được tạo lại hoặc refund. `billing_quota_usage_ref` trong `story.video_generations` là opaque receipt tham chiếu, không phải FK/cột ledger chung. Số dư chỉ được tính trong Billing từ grants trừ usage.
- Chỉ request bị từ chối trước khi admission commit mới không tiêu thụ quota. Một khi accepted request/usage đã commit trước dispatch, unit không được hoàn trong bất kỳ trường hợp nào: queue/provider ambiguity, technical failure, safety block, cancellation hoặc xóa run (Q110, Q119, Q128). Retry cùng idempotency key trả về cùng generation/usage; scene retry kỹ thuật không phải request mới. Mỗi run tối đa một request đầu + hai request tạo lại chất lượng; mỗi request đã nhận tính vào cap này kể cả khi lỗi.
- Nếu scope không còn unit, từ chối bằng 409 `VIDEO_QUOTA_EXCEEDED`, không tạo accepted generation, usage row hoặc AI dispatch. Hết quota không chặn xem video/dữ liệu đã lưu hoặc xóa run. Xóa run purge nội dung theo lifecycle nhưng giữ metadata usage tối thiểu để đối soát; không hoàn grant đã tiêu thụ.
- Top-up báo giá theo price version do server kiểm soát, tạo invoice theo owner scope có kiểu và chỉ phát grant sau payment event MoMo/VNPAY đã xác minh, dedupe và ghi nhận idempotent. Không phát grant từ browser redirect/callback pending. Chính sách hoàn tiền thanh toán thương mại xử lý riêng; không sửa/xóa usage ledger.

Quota sản phẩm và rate limit, GPU concurrency, cost cap là ba cơ chế riêng: quota giới hạn entitlement của khách hàng; rate limit chống lạm dụng API; capacity/circuit breaker chặn quá tải hoặc vượt trần chi phí vận hành.
<a id="srs-24"></a>
## 24. Phân loại dữ liệu và xử lý media

### 24.1 Phân loại dữ liệu

| Loại | Ví dụ | Cách xử lý |
|---|---|---|
| Công khai | Mô tả activity đã phát hành, nhóm tuổi catalog | Version hóa, duyệt; không có run ref riêng tư |
| Tài khoản/tổ chức | Firebase UID ref, organization/class ID, role assignment, billing contact | Authorization server-side, quyền tối thiểu, không công khai |
| Hồ sơ trẻ | Display name, tuổi tháng/nhóm, sở thích, quan sát, thành tích | Người lớn nhập; theo owner scope; không gửi tên cho model |
| Hỗ trợ nhạy cảm | Nhóm nhu cầu hỗ trợ, note mã hóa | Quyền hồ sơ hẹp; mặc định loại khỏi AI context; không chẩn đoán |
| Media trẻ tạo | Tranh, voice idea, story, video | Object storage private; demo chỉ dữ liệu tổng hợp; không log/link công khai |
| Lesson | PDF/PPTX/DOCX gốc và text trích xuất/chỉnh sửa | Teacher phụ trách; giữ source/revision; không OCR trang scan |
| Thanh toán | Provider refs, invoice, event IDs, amounts | Chỉ lưu merchant refs cần thiết; không lưu bí mật thẻ/ngân hàng |
| Vận hành | Correlation ID, run/job ID, status, thời lượng stage | Redact, retention giới hạn, opaque IDs; không free text/nội dung |
| Secrets | Firebase verifier config, Modal key, payment signing secrets, SMTP | File ignore/runtime secret manager; không source control/client |

Activity catalog dùng contract có kiểu/version, không thêm bảng. Contract đích ActivityCatalogItemV2 có trường: supported ages/month ranges; subject/objectives; theme; setting/context; season; outdoor location; duration; materials/equipment; accessibility; safety constraints; status/review version. Đây là metadata có cấu trúc, không phải prompt tự do. Contract catalog hiện tại chưa có đủ các trường này; chỉ lọc theo trường được phiên bản hiện tại cung cấp. Chỉ bật lọc dựa trên toàn bộ metadata sau khi nâng cấp đồng bộ contract version, fixtures và client/server adapters. Không thêm bảng: learning_content.record/version hiện hữu tiếp tục là nguồn chuẩn. Moderation không đổi: Catalog toàn cục đã duyệt không tạo precondition chọn activity cho Parent story/video theo A; quyền đọc/preview và projection hậu video (tham chiếu lesson-version opaque tùy chọn qua cổng module Lesson; không gắn org/class/occurrence của Teacher; quyền đọc catalog/xem trước lesson tách khỏi điều kiện tạo video; không cấp quyền đọc mới; kiểm quyền hiện hành trước khi trả nội dung; lesson bị thu hồi/gỡ phát hành thì ẩn danh sách, video không bị ảnh hưởng và không fallback sang catalog công khai) [Còn mở cho thiết kế vật lý: vị trí lưu vật lý tham chiếu lesson-version]. Teacher chọn catalog hoặc activity riêng trong occurrence đã xác nhận bằng checklist an toàn.

### 24.2 Kiểm tra upload và phân tích tài liệu

- Đối chiếu extension, MIME khai báo và file signature; không tin extension đơn lẻ.
- Quarantine upload đến khi ClamAV/scanner-compatible verdict `CLEAN`; file chưa được quét không vào ASR/VLM/parser/model job. `INFECTED`, `ERROR` hoặc timeout bị fail closed; giữ quarantine hoặc từ chối theo policy.
- Binary được gửi qua API upload session backend có thể resume; `core.upload_sessions` giữ principal/scope/purpose, expected media/size/hash, expiry và trạng thái session; `core.upload_parts` giữ part number, size/hash và opaque object ref cho từng application chunk. Mỗi chunk (tối đa 4 MiB) là object riêng qua PutObject, không dùng S3 Multipart Upload API. Backend chỉ assemble theo part number liên tục, xác minh per-part/whole SHA-256 và tổng bytes, chạy media validation/AV, rồi tạo final asset bằng PutObject có kích thước đã biết. Partial bytes không thể attach hoặc đưa vào model; expired/aborted session và chunk objects được purge idempotent theo TTL. Client chỉ nhận opaque ref/progress, không nhận endpoint/credential storage.
- Lưu verdict, scanner/version, checksum và thời điểm quét trong asset-validation metadata/event; không log file bytes, tên hiển thị hoặc signature nội dung.
- Giới hạn lesson 25 MB và 100 trang/slide trước extraction. Từ chối PDF/Office mã hóa hoặc có password. Đánh dấu trang scan không hỗ trợ; không fallback OCR.
- PPTX/DOCX là ZIP container: giới hạn kích thước giải nén, entry count, nesting và processing time để giảm archive-bomb risk. Không chạy macro, embedded script hoặc external links.
- Parser chạy trong worker giới hạn tài nguyên, không arbitrary outbound network. Chỉ trích text; không execute/render embedded objects.
- Từ chối file lỗi bằng safe code ổn định; lưu parser name/version, page coverage, warnings và source hash.
- Audio tối đa 20 MB/2 phút. Danh sách MIME/container/codec chấp nhận là implementation gate; validate bằng decode, không dựa tên file.
- Giới hạn ảnh demo tổng hợp đề xuất: 20 MiB encoded, 40 megapixels decoded, JPEG/PNG/WebP. Decode trong worker cô lập, giới hạn tài nguyên; chuẩn hóa EXIF orientation/color thành derived asset, giữ nguyên original. Ảnh quá kích thước trả IMAGE_DIMENSIONS_EXCEEDED; không resize trước khi ghi source hash/provenance.
- Giới hạn decompression và decoded pixels để ngăn image bomb. Tính SHA-256 khi stream upload; không tin MIME, filename hoặc dimensions do client khai báo.

### 24.3 Lưu trữ, lineage và lifecycle

- PostgreSQL lưu metadata nghiệp vụ/references; MinIO/private object store lưu binary.
- Object key là opaque ID ngẫu nhiên, không chứa tên, trường, ngày sinh hoặc tên file gốc.
- Mỗi source/derived object ghi owner scope, media type, byte size, checksum, upload/transform time, source ref, model/config revision và deletion state.
- Original bất biến. Crop, reference frame, scene clips, narration, subtitle file và MP4 cuối là asset riêng.
- Lifecycle xóa thu hồi playback/upload authorization, cancel jobs, rồi xóa objects/metadata đủ điều kiện theo batch idempotent. Lỗi giữ deletion-pending để retry; chưa đánh dấu hoàn tất đến khi đối soát đủ object.
- Chia sẻ asset giữa run không phải tính năng V1. Chỉ xóa asset được tham chiếu khi lifecycle xác nhận không còn reference hợp lệ.

#### Contract chuyển dữ liệu tổng hợp từ Docker local sang Modal

MinIO local là kho chuẩn của original/derived media. Modal chỉ nhận working copy theo job trong scratch prefix cô lập; không có MinIO credentials, Docker-network route hoặc URL lâu dài tới local store.

1. Backend validate, stream và hash upload vào private MinIO key. Chỉ assets đã validate và text/context được allowlist, giới hạn mới stage sang inference.
2. Worker tạo prefix riêng sketch2life/{environment}/{job_id}/{generation_id}/{attempt_id}/ trong Modal Volume, upload qua Modal SDK local-to-volume batch interface. Mỗi prefix single-writer; jobs không dùng chung filename/scratch path mutable.
3. Remote function chỉ nhận opaque job/generation ID, versioned contract, allowlisted path refs, SHA-256 và metadata nhỏ; không nhận raw image/audio bytes, local MinIO endpoint, child name, Firebase token hoặc payment data làm arguments.
4. Input transfer tối đa 48 MiB/job: một drawing tối đa 20 MiB, voice tùy chọn tối đa 20 MiB, và tối đa 1 MiB extracted lesson/story/context text cộng manifest overhead. Không stage lesson document gốc; chỉ text đã review. Deadline 300 giây, tối đa hai transport retries idempotent.
5. Output chỉ ghi trong output prefix của attempt. Worker lấy qua SDK và kiểm tra path containment, manifest, SHA-256, byte cap, codec, dimensions, duration; application kiểm tra đủ narration/subtitle coverage và automated output-safety gate. Chỉ output qua cả hai cổng mới trở thành playable private MinIO asset; xác minh hash đã lưu. Safety-blocked candidate không publish/cấp playback token; xóa scratch copy, chỉ giữ safe decision metadata.
6. MP4 cuối tối đa 256 MiB. Hash mismatch, unexpected/missing output, traversal path hoặc invalid media trả MODAL_RESULT_INVALID; transfer exhaustion trả MODAL_TRANSFER_FAILED. Không kết quả nào playable.
7. Sau verified return hoặc terminal failure, xóa attempt prefix. Orphan sweeper idempotent xóa prefix không tham chiếu sau 24 giờ. Xóa run cũng lên lịch scratch cleanup; MinIO lifecycle không phụ thuộc Modal cleanup thành công.
8. Truyền job_id/storage-path refs thay vì function arguments lớn. Modal khuyến nghị external object storage cho arguments lớn/async và dùng default centralized storage region; Volume staging vẫn là external processing. Các giới hạn này chỉ cho synthetic demo. Real data cần review provider region, transfer, retention và deletion trước activation.

48 MiB/256 MiB/timeout là synthetic-demo caps đề xuất, chưa đo. Xác minh limits và SDK/Volume support trước khi bật video live. [Modal local data](https://modal.com/docs/guide/local-data), [Modal data residency](https://modal.com/docs/guide/data-residency), [Modal Volumes](https://modal.com/docs/guide/volumes), [Modal cloud bucket mounts](https://modal.com/docs/guide/cloud-bucket-mounts).

<a id="srs-25"></a>
## 25. Yêu cầu môi trường và triển khai

### 25.1 Tách biệt môi trường

| Môi trường | Mục đích | Chính sách dữ liệu/provider |
|---|---|---|
| Local developer | Phát triển cá nhân | Chỉ synthetic fixtures; Docker Compose; Mailpit; Modal dev environment chỉ khi implementation cấu hình rõ |
| Shared demo | Walkthrough tái lập được | Profile/media tổng hợp; test organization cô lập; payment sandbox; không dùng dữ liệu trẻ thật |
| Staging | Xác minh tích hợp | Dữ liệu tổng hợp; provider sandbox; secrets/storage cô lập; không dùng payment production |
| Production | Tổ chức thật | SRS chưa chốt; hosting, privacy, security, operations, budget và rollout cần duyệt riêng |

Ủy quyền hiện tại chỉ dành cho tài liệu; không tạo/cấu hình các môi trường này trong công việc này.

### 25.2 Yêu cầu dịch vụ Compose

| Service | Vai trò | Persistence/health |
|---|---|---|
| api | FastAPI routes, command/query adapters | Stateless; readiness kiểm tra DB, queue và object-store client |
| worker | RQ jobs và scheduled tasks | Stateless process; heartbeat; graceful shutdown/cancel check |
| postgres | PostgreSQL 17, nguồn chuẩn local demo | Named volume; readiness probe; tài liệu backup/restore |
| redis | Queue transport, rate-limit counters | Named volume tùy chọn demo; jobs có thể tái dựng từ PostgreSQL |
| minio | Private S3-compatible object store | Named volume; liveness/readiness; chỉ synthetic content |
| otel-collector | Nhận traces/metrics/logs | Config-mounted; collector health |
| prometheus | Scrape metrics | Named volume tùy chọn; scrape health |
| grafana | Dashboard local | Demo admin secret từ ignored config; không có production credential mặc định |
| mailpit | Local SMTP sink | Web UI/SMTP local; không gửi email ngoài |
| teacher-ui (optional profile) | Teacher web app | Dev server/build container; không chứa backend secrets |

Android chạy trên host/emulator hoặc simulator được duyệt, không chạy như privileged container. Compose chỉ expose host ports cần thiết. Database, Redis và MinIO mặc định không public ra external network. Persistent volumes tách biệt/có tên; xóa volume không thuộc stop/start thông thường.

PostgreSQL 17 là baseline tương thích Compose/local demo hiện tại, không phải tuyên bố là upstream mới nhất. PostgreSQL 18 là major hiện hành tại ngày rà soát; đánh giá 18 là cổng migration/deployment riêng, kiểm tra extension, driver, migration, backup/restore và tương thích dữ liệu.

### 25.3 Cấu hình và secret

Tên cấu hình sau là ví dụ để chuẩn hóa; không commit giá trị thật:

- Database URL, pool sizing.
- Redis URL, queue names, worker concurrency.
- MinIO internal endpoint, bucket names, runtime credentials.
- Firebase project/audience và server-side ID-token verifier.
- Modal workspace/environment, function IDs, timeout/concurrency, provider secret reference.
- Model profile IDs/revisions, prompt-template versions, content-policy versions, inference limits.
- MoMo/VNPAY merchant IDs, callback URLs, signing/verification secret references.
- SMTP adapter endpoint; local dùng Mailpit.
- OTel collector endpoint, sampling/redaction flags, service name.
- Upload byte/page/duration limits, rate-limit policy, playback token lifetime, retention config.

Secrets lấy từ ignored local files hoặc runtime secret management; .env.example chỉ có placeholder. Startup validator fail closed nếu thiếu production-mode secrets hoặc callback verification. Không log environment dumps.

### 25.4 Topology production là ADR riêng

Production region, API/database host, object storage, network path đến Modal, key management, email vendor, alert destination, backup frequency, recovery objectives, scale và SLA chưa được chọn. Không suy diễn Docker Compose local là production design.

### 25.5 CI, release và rollback gates

CI vendor chưa chọn. Pipeline triển khai sau này phải có cổng tương đương:

1. Format/lint/type checks cho module đổi và consistency check generated contracts.
2. Unit/domain/contract suites, boundary tests theo feature plan được duyệt.
3. Dependency/secret/container-image scan và repository security validator.
4. Migration trên PostgreSQL disposable từ source baseline; kiểm tra index/constraint, reconciliation, rollback/feature-flag path.
5. Build Android/web; xác minh client bundle không có credential/provider endpoint.
6. Compose smoke/readiness, restart persistence, synthetic local end-to-end khi workstream được duyệt.
7. Feature-flag release; kiểm tra migration parity, rollback, dashboard/cảnh báo trước khi bật traffic.

Đây là yêu cầu tương lai, không phải bằng chứng test/build đã chạy trong task tài liệu.

### 25.6 Baseline phiên bản client/runtime cần đánh giá

- apps/mobile pin React Native 0.87: baseline repository, không phải bản upstream mới nhất.
- React Native 0.88 upstream release ngày 2026-10-19. Nâng từ 0.87 cần compatibility review riêng cho apps/mobile, React/Metro, native modules, Android/iOS tooling và CI; không tự đổi pin.
- apps/teacher-ui pin Vite 8.3: baseline hiện có; nâng cấp cần compatibility/security review theo lockfile và dependency set.
- Compose dùng PostgreSQL 17 làm local baseline; PostgreSQL 18 cần được đánh giá tại cổng migration/deployment, không tự đổi major trong tài liệu này.

Nguồn upstream chính thức: [React Native 0.88 release (2026-10-19)](https://reactnative.dev/blog/2026/10/19/react-native-0.88), [React Native release overview](https://reactnative.dev/releases/), [PostgreSQL supported versions](https://www.postgresql.org/support/versioning/), [PostgreSQL current release notes](https://www.postgresql.org/docs/current/release.html), [Vite releases](https://vite.dev/releases). Các nguồn xác nhận upstream tại thời điểm rà soát; repository pin tiếp tục là baseline đến khi có review nâng cấp riêng.

<a id="srs-26"></a>
## 26. Monitoring, cảnh báo và mục tiêu vận hành

### 26.1 Danh mục metric bắt buộc

| Tên metric | Ví dụ chỉ số |
|---|---|
| API | Số request/độ trễ theo route template/status, lỗi xác thực, tỷ lệ 4xx/5xx |
| Queue | Độ sâu queue, tuổi job lâu nhất, enqueue/start/finish, worker heartbeat |
| AI job | Độ trễ/lỗi theo stage, số attempt, stale result, provider timeout, GPU seconds/concurrency của Modal |
| Teacher Sketch | Số deck/step job, độ trễ, coverage/schema/safety rejection, stale/regeneration và compute usage tổng hợp; không label child/profile và không cộng vào video quota |
| Video/quota | Số scene attempt, kết quả kiểm tra decode/format/safety, generation/regeneration, grant/admission/consumption/exhaustion theo loại owner scope tổng quát, top-up và đối soát callback; không dùng child/profile làm label |
| Storage | Số byte/object theo loại asset tổng quát, lỗi upload/download, deletion lifecycle backlog |
| Billing | Lỗi xác minh callback, callback trùng, độ trễ đối soát invoice, kết quả gia hạn, trạng thái giao notification |
| Security | Rate-limit event, từ chối phân quyền, authentication failure bất thường |
| Runtime | Health container, mức sử dụng DB connection pool, trạng thái Redis/MinIO/OTel collector |

Grafana cung cấp dashboard riêng cho sức khỏe API/job/service, mức sử dụng Modal theo stage, video retry, Sketch deck/step cost-cap, storage lifecycle, đối soát payment và notification. Sketch usage và video quota có metric/dashboard tách biệt; không cho dashboard billing/media drill-down theo hồ sơ trẻ.

### 26.2 Trường log và trace

Chỉ ghi structured JSON log với correlation ID và opaque resource IDs. Trace/metric dùng giá trị tổng hợp, không có child/profile identifier hoặc free text. Trường telemetry được phép gồm route template, status, duration, stage, retry number, provider/model profile ID không bí mật, GPU class, giá trị tổng hợp, correlation ID và opaque run/job ID theo thời hạn lưu có kiểm soát. Không log tên trẻ, chi tiết context hồ sơ, image/audio bytes, transcript/story/prompt, credential, signed playback URL hoặc ghi chú sức khỏe/nhu cầu hỗ trợ. Sampling không được bỏ qua bước redact.

### 26.3 Điều kiện cảnh báo cho local demo

| Điều kiện | Hành động |
|---|---|
| API readiness thất bại hoặc lỗi 5xx vượt ngưỡng cấu hình | Dừng tạo traffic demo mới, kiểm tra health dependency và correlation ID |
| Worker heartbeat mất hoặc job cũ hơn deadline cảnh báo | Kiểm tra worker/Redis/outbox; không tự sửa row nghiệp vụ |
| LTX queue/concurrency vượt maximum cấu hình, queue đầy hoặc job video lâu hơn deadline cảnh báo | Dừng nhận việc mới khi bão hòa; hiển thị AI_CAPACITY_BUSY an toàn |
| Vượt ngưỡng sử dụng Modal cấu hình theo GPU seconds/bytes staged/số run mỗi ngày | Hard cap ngăn nhận/dispatch thêm việc; dừng scene chưa chạy, ghi safe error và cảnh báo aggregate; không vượt budget, giữ quota đã nhận |
| Safety gate trả indeterminate hoặc thiếu coverage frame/audio/subtitle | Chặn playback; đưa về bước rà soát script; phát operator event đã redact |
| Có Modal scratch prefix không được tham chiếu quá 24 giờ | Chạy cleanup idempotent; cảnh báo nếu backlog tăng |
| Tỷ lệ stale result tăng đột ngột so với baseline | Kiểm tra duplicate dispatch/version churn, không xem user content |
| Callback payment có signature sai | Ghi security event; callback hợp lệ chưa đối soát trong 5 phút là warning |
| Lifecycle deletion pending vượt retry horizon cấu hình | Hiển thị số lượng queue cho operator, không hiển thị nội dung |
| Local storage volume vượt warning threshold cấu hình | Chặn upload mới trước khi hết dung lượng |
| Rate-limit event tăng đột biến kéo dài | Báo cáo tổng hợp theo route/bucket class |

Các ngưỡng cảnh báo và nơi nhận paging cần tune sau benchmark synthetic; hard GPU-second cap/request và cap/day là cấu hình bắt buộc trước live video. Trước khi Billing nhận request, application reserve đủ budget tối đa cho request qua AI Policy port; thiếu reservation thì trả `AI_COST_LIMIT_REACHED` trước admission, không ghi quota usage. Sau khi đã nhận, reservation phải bảo vệ request khỏi daily cap bình thường; circuit breaker đóng admission mới và worker không tiêu vượt reservation. Emergency safety/operator abort có thể dừng request đang chạy; theo Q128 quota đã nhận vẫn không hoàn, đây là rủi ro còn lại được chấp nhận và phải được giải thích trước khi xác nhận. Worst-case structural bound là 15 scene × 3 attempts = 45 scene attempts/full-video request, tối đa 135 scene attempts/run; reservation và cap phải tính theo đúng bound, không nhầm với retry scene ngoài request cap. Circuit breaker global/owner-scope từ chối request mới khi ngân sách đã reserve hết. Chưa chốt số GPU-second/USD đến benchmark synthetic.

### 26.4 Dashboard vận hành

Grafana cần các panel riêng cho service readiness, API latency/errors, auth denials, rate limiting, queue depth/age, job theo stage, model/GPU seconds, scene retries, output validation, storage/lifecycle, payment reconciliation và email/in-app delivery. Tách dashboard billing khỏi dashboard child media; không dashboard nào có drill-down theo hồ sơ trẻ.

<a id="srs-27"></a>
## 27. Runbook vận hành

Các quy trình này là mục tiêu tài liệu hóa; không cho phép deploy hoặc thao tác provider trong task này.

### 27.1 Khởi động local và kiểm tra health

1. Xác nhận Docker Engine sẵn sàng và không nạp production provider secrets.
2. Khởi động dependency có state và application services bằng Compose profile đã tài liệu hóa.
3. Chờ PostgreSQL/Redis/MinIO readiness trước khi khởi động API/worker; không chỉ dựa trạng thái container “running”.
4. Chạy Alembic head check và khởi tạo synthetic demo fixture trong implementation task được duyệt riêng.
5. Mở API health/readiness, Prometheus targets và Grafana dashboard. Xác nhận Mailpit chỉ nhận billing notice tổng hợp.
6. Chỉ kết nối Android emulator và Teacher web đến local API; kiểm tra client không gọi trực tiếp Modal hoặc MinIO.

### 27.2 AI job bị kẹt hoặc thất bại

1. Tra cứu bằng correlation ID/job ID và stage; không tra theo tên trẻ hoặc prompt.
2. Kiểm tra trạng thái durable của ai_jobs, attempt count, outbox, worker heartbeat, Redis connectivity và Modal provider health.
3. Dựa safe error code xác định lỗi retry được, người dùng sửa được hay terminal.
4. Không sửa thủ công story/job database rows. Dùng application repair command có idempotency và audit.
5. Nếu scene retries đã hết, giữ run FAILED và giải thích bước kế tiếp an toàn. Teacher chỉ được tạo run mới cho occurrence nếu chưa có sample playable nào qua safety gate.
6. Nếu accepted video request thất bại hoặc bị safety block, tuân theo bounded request-cap và quay lại script review. Nếu đã có video playable nhưng không phù hợp, không reset counter hoặc gọi scene retry ngoài luồng.

### 27.3 Modal/provider outage

1. Dừng hoặc trì hoãn job mới theo cấu hình queue backpressure; giữ durable jobs/outbox trong PostgreSQL.
2. Nếu usage/safety/transfer/queue alarm yêu cầu, bật operator kill switch để dừng nhận video job mới; không xóa durable job state.
3. Hiển thị trạng thái provider unavailable an toàn và hướng dẫn retry dự kiến.
4. Không tự đổi model/provider, âm thầm giảm chất lượng hoặc lộ credential cho client.
5. Khi phục hồi, resume idempotent và kiểm tra input hashes cùng authorization/assignment version hiện hành trước khi nhận kết quả.
6. Đối soát và purge Modal scratch prefix theo attempt; ghi duration/failure/GPU class tổng hợp, không ghi payload nội dung.

### 27.4 Sai lệch payment callback

1. Xác minh callback signature và provider event ID trước state transition.
2. Kiểm tra provider, event receipt, payment attempt và invoice bằng opaque refs.
3. Signature sai thì từ chối và ghi safe security event; không kích hoạt capacity.
4. Callback signature đúng nhưng trùng thì trả provider acknowledgement mà không cập nhật invoice/capacity lần nữa.
5. Nếu provider status và internal invoice lệch nhau, giữ nguyên capacity và reconcile qua adapter đã duyệt; không đánh dấu paid dựa redirect hoặc ảnh chụp màn hình người dùng.
6. Chỉ gửi notice thành công/thất bại từ trạng thái đã đối soát.

### 27.5 Storage hoặc deletion backlog

1. Kiểm tra MinIO health, dung lượng volume, lifecycle queue và safe failure code theo object.
2. Ngừng nhận upload mới khi storage degraded hoặc disk sắp đạt ngưỡng cấu hình.
3. Giữ deletion request pending đến khi đối soát object refs bắt buộc; retry idempotent.
4. Không trả internal object key trong lỗi client.
5. Đưa trường hợp reference dùng chung chưa rõ lên owner review; không purge source có thể vẫn được lưu giữ.

### 27.6 Backup và restore

1. Backup PostgreSQL bằng phương thức nhất quán và backup MinIO object data/metadata như một bộ khớp nhau.
2. Ghi timestamp backup, schema revision, object-store inventory/checksum summary và synthetic-demo marker.
3. Restore vào môi trường local cô lập; kiểm tra table counts, migration head, object hashes và asset lineage.
4. Chỉ chạy synthetic read/playback và job-status checks; không tự gửi media đã restore sang Modal.
5. Ghi thời gian restore và sai lệch vào evidence riêng của feature.
6. Production recovery point/recovery time objectives, encryption keys, offsite copies và retention schedule cần operations plan riêng.

<a id="srs-28"></a>
## 28. Chiến lược xác minh và kịch bản rà soát

Phần này quy định evidence cần tạo trong tương lai; không khẳng định task tài liệu này đã viết/chạy tests.

### 28.1 Các tầng xác minh

| Tầng | Evidence cần có sau này |
|---|---|
| Domain | Coverage state transition/invariant cho một trẻ, serialization active-run, class enrollment, sample uniqueness, rewrite/video caps, billing grace và deletion |
| Contract | Fixture round-trip hợp lệ/không hợp lệ cho OwnerScopeRefV1, StoryRunCommandV1, AiJobStatusV1, ScriptRevisionV1, PaymentEventV1 và error envelope |
| Application | Fake-port tests cho authorization, transaction/idempotency, stale job completion, deletion orchestration và provider failure |
| Repository/migration | PostgreSQL tạm từ source baseline; kiểm partial indexes, row/hash reconciliation và rollback bằng feature flag |
| Adapter integration | MinIO upload/hash/delete, Redis/RQ redelivery, Firebase token verification, Modal sandbox/synthetic flow, MoMo/VNPAY sandbox callbacks |
| API | Role/resource access matrix, request limits, stable error mapping, pagination, idempotency và không rò rỉ nội dung |
| Client | Parent Android permissions/return flow; Teacher browser camera/upload, status polling, safe errors, accessibility và không có batch action |
| Synthetic end-to-end | Parent one-child run và Teacher occurrence sample từ input đến MP4 phát được, gồm script review và adult confirmation |
| AI evaluation | Chất lượng Whisper tiếng Việt, độ chính xác/uncertainty của VLM subject, story schema/safety, character/color/style anchors, subtitle sync, video decode/format, Teacher Sketch activity coverage/line steps/age fit và GPU/latency/cost |
| Security/privacy | Secret scan, log/trace redaction, cross-scope denial, signed playback expiry, upload/archive parser bounds và provider payload allowlist |
| Operations | Compose health/restart persistence, queue recovery, backup/restore, payment event replay và lifecycle deletion recovery |

### 28.2 Kịch bản nghiệm thu tối thiểu

| Kịch bản | Kết quả kỳ vọng |
|---|---|
| Parent gửi hai profile ID trong một run | 422 MULTI_CHILD_NOT_SUPPORTED; không tạo run/job/media |
| Parent mở hai run đồng thời | Một run thành công; run còn lại nhận 409 ACTIVE_RUN_EXISTS |
| Teacher chọn trẻ không active-enrolled trong lớp được giao | Từ chối authorization; không tạo story run |
| Organization admin yêu cầu media của Teacher run | Từ chối, không tiết lộ private run content |
| Teacher assignment bị thu hồi sau khi tạo run | Các lần xem profile/story/playback tiếp theo bị thu hồi; metadata audit ghi sự kiện |
| Teacher import lesson mã hóa hoặc PDF chỉ có scan | File mã hóa bị từ chối; scan trả OCR_NOT_SUPPORTED; không gọi OCR provider |
| Teacher sửa extraction | Tạo text revision bất biến mới; plan/run hash cũ không đổi |
| Teacher chọn custom outdoor activity nhưng thiếu safety checklist | Không duyệt plan, không chạy được run |
| AI trả output cho profile/context/script hash cũ | Job thành stale; current story head không đổi |
| Parent dùng hết ba lần rewrite | Lần rewrite thứ tư trả STORY_REWRITE_LIMIT_REACHED |
| Người lớn xác nhận script revision A rồi tạo revision B | Video request dùng revision A bị từ chối là stale |
| Một video hoàn tất và người lớn đánh dấu không phù hợp | Cùng run quay về script review; cần revision đã xác nhận mới trước regeneration |
| Scene lỗi lần đầu và cả hai retry | Run dừng an toàn; không retry âm thầm vượt giới hạn |
| Lesson có chỉ dẫn nhúng yêu cầu lộ secret hoặc đổi safety policy | Xem như lesson content; không lộ system/provider secret, safety policy vẫn ưu tiên |
| Story output chứa chẩn đoán, chỉ dẫn gây hại hoặc dữ liệu hồ sơ riêng | Chặn trước khi hiển thị script/video job; chỉ ghi safe policy reason |
| Video ghép có frame/audio/subtitle không an toàn hoặc validator chưa đủ | Không cấp playback token/final asset lưu bền; set safety blocked, quay lại script review, chỉ ghi safe policy metadata |
| Provider timeout sau khi nhận LTX request nhưng chưa rõ kết quả | Job vào AWAITING_RECONCILIATION; không tạo generation trùng trước khi kiểm tra status/operator xử lý |
| Teacher run lỗi trước khi có playable video qua safety | Run lỗi terminal; run mới cho cùng occurrence được dùng sample slot còn trống |
| Teacher occurrence có sample playable đã qua safety | Từ chối run độc lập khác; regeneration chất lượng phải cùng run |
| Teacher assignment được thay thế khi Modal scene đang chạy | Không hủy job hợp lệ chỉ vì đổi owner; completion đối chiếu run/input/script/occurrence hash và transfer receipt hiện hành. Kết quả không còn khớp bị đánh dấu stale và scratch được purge |
| Provider callback hợp lệ đến trùng | Acknowledge idempotent; invoice/capacity chỉ đổi một lần |
| Payment callback signature không hợp lệ | Payment pending/failed; không tăng capacity |
| Renewal grace hết hạn | Hạn chế tạo class/run mới; dữ liệu hiện có vẫn giữ và truy cập được |
| Đang xóa run khi video job chạy | Gửi yêu cầu hủy; late result bị bỏ/xóa; run thể hiện lifecycle status |
| Parent xóa profile | Ẩn profile ngay; lifecycle bắt đầu cho run/context/media liên quan; profile Teacher scope khác không bị ảnh hưởng |
| Rà log sau synthetic run | Không thấy tên trẻ, transcript, ảnh, prompt, support note, token hoặc signed URL |

### 28.3 Trách nhiệm xác minh yêu cầu

Feature triển khai mỗi module lưu evidence trong feature folder của mình. Evidence tích hợp cross-feature ghi contract version và fixture hash; không gom vào kho evidence chung không truy vết được. Không suy ra product acceptance từ việc PDF render thành công hoặc architecture review.

<a id="srs-29"></a>
## 29. Danh mục rủi ro và cổng triển khai

**Thang đánh giá định tính:** Xác suất `L/M/H` = thấp/trung bình/cao; tác động `M/H/C` = trung bình/cao/nghiêm trọng. Đây là đánh giá ban đầu của nhóm tài liệu, cần owner chức năng xác nhận trước implementation; không phải xác suất thống kê.

| ID | Rủi ro | Xác suất | Tác động | Owner vai trò | Giảm thiểu / trạng thái |
|---|---|---|---|---|---|
| R-01 | LTX không giữ nhất quán nhân vật qua nhiều scene | M | H | AI lead | POC synthetic với bộ đánh giá cố định, neo nhân vật, giới hạn retry; người lớn có thể quay lại duyệt script |
| R-02 | Modal không truy cập MinIO local hoặc transfer/region không phù hợp | M | H | Infra + Privacy reviewer | Transfer bounded qua backend/scratch cô lập, checksum, cleanup; chỉ synthetic cho đến khi review region |
| R-03 | LTX runtime/model revision/license thay đổi hoặc không tương thích | M | H | AI lead | Pin model/runtime/CUDA/license và provenance trước promote |
| R-04 | Model ASR/VLM/LLM/TTS không đạt chất lượng tiếng Việt | M | H | AI lead | Benchmark synthetic theo rubric; provider ports; không fallback âm thầm |
| R-05 | Snapshot chứa note nhạy cảm bị gửi cho model ngoài | M | C | Privacy + Data owner | Allowlist tối thiểu, mặc định loại support-needs, preflight/redaction evidence |
| R-06 | Reassignment đua với run/job đang chạy, current-owner lock và quyền cũ | M | H | Backend/BE1/Story owner | Durable two-owner transfer state, immediate old-access fence, no-content during pending, Story lock receipt trước finalize; không hủy job hợp lệ; admin emergency force-close metadata-only nếu conflict; reconcile transfer idempotently |
| R-07 | Hai request tạo lớp cùng lúc vượt capacity | L | H | Billing + BE1 owner | Entitlement transaction, lock/serializable constraint, idempotency |
| R-08 | Payment callback trùng, giả mạo hoặc sai thứ tự | M | H | Billing owner | Verify signature/freshness, unique provider event, state machine, reconciliation; redirect không phải bằng chứng |
| R-09 | File lesson/parser bị zip bomb/malware/resource exhaustion | M | H | Security + Backend | Quarantine AV, parser sandbox, byte/page/entry/ratio/time limits, fail closed |
| R-10 | Legacy ID bị hiểu nhầm thành run/profile mới | L | H | Data owner | Legacy read-only; không map legacy session ID thành story run; migration crosswalk |
| R-11 | Source-derived table target count is mistaken for the live database table count | M | H | Data owner | Distinguish v2.3 baseline 89/137 from Rev31 implementation crosswalk 92/140; both are source-declared; inventory the live schema before migration |
| R-12 | Dữ liệu trẻ thật vào demo/provider khi chưa có policy | L (do gate) | C | Product + Privacy/legal | Synthetic-only; chặn release thật đến khi purpose/authorization/transfer/retention/DSR được duyệt |
| R-13 | Email/push provider outage làm chậm billing/run notices | M | M | Operations | Inbox authoritative, outbox + retry bounded, dashboard; payment/run state không phụ thuộc delivery |
| R-14 | Schema/table ownership drift khi implementation | M | H | Data owner + Architect | Mọi thay đổi cập nhật SRS/register/ADR và migration plan trước merge |
| R-15 | Chi phí, availability hoặc SLA production bị suy ra từ local demo | H | H | Product + Commercial + Operations | Không cam kết giá/SLA từ demo; benchmark, chọn host, ADR và approval riêng |
| R-16 | Lesson/output model gây nội dung nguy hiểm hoặc lộ thông tin | M | C | Safety/AI lead | Untrusted input, versioned safety gate, structured output, script confirmation, synthetic adversarial corpus |
| R-17 | Q127 giữ sample slot sau video đầu nhưng mọi lần tạo lại lỗi, không còn video dùng được cho occurrence | M | H | Product owner + Teacher workflow owner | Quyết định Q127 đã chốt; cảnh báo trước khi claim, cho thấy chính sách không phục hồi, theo dõi tỷ lệ; không mở slot tự động |
| R-18 | Quota đã mua/được cấp bị mất dù provider/safety/cost cap không tạo được video (Q128) | M | H | Product + Billing + AI lead | Quyết định no-refund được giữ; trước admission phải reserve đủ GPU budget worst-case; hiển thị unit được tính trước khi xác nhận; emergency abort vẫn là rủi ro được chấp nhận |
| R-19 | Run `COMPLETED`/`ABANDONED` và media giữ đến khi người dùng xóa có thể lưu lâu vô hạn | H | C | Privacy/legal + Product | Chấp nhận chỉ cho synthetic demo; production bị chặn đến khi có retention tối đa, backup expiry, deletion evidence và DSR policy; idle closeout giữ nội dung theo Q133 |
| R-20 | Android push không hoạt động với đa số thiết bị hoặc cần distributor/provider không phổ biến | H | M | Mobile + Architecture | Inbox/email là fallback chuẩn; provider Android chỉ là POC gate; không dùng FCM theo repo rule; không quảng bá delivery trước khi chứng minh |
| R-21 | Outbox + RQ + poller tự dựng saga dài khó vận hành hơn workflow engine | M | H | Architect + Operations | ADR so sánh Temporal trước khi implementation; đánh giá crash recovery, timers, cancel/compensate, cost và burden |
| R-22 | Cost per accepted video không khớp giá quota/allowance | H | H | Commercial + AI lead | Benchmark GPU seconds/output/storage; configure included/top-up; hard admission reservation và daily circuit breaker trước demo live |
| R-23 | Hóa đơn điện tử, VAT, consumer policy hoặc provider recurring khác giả định | M | H | Commercial + Legal + Billing | Không thu tiền production trước legal/accounting review và merchant sandbox/approval |
| R-24 | Video mẫu một trẻ chiếu cho cả lớp tạo cảm nhận thiên vị hoặc lộ dữ liệu ngoài mục tiêu | M | H | Product + Education reviewer | Xác nhận riêng theo occurrence, không tái dùng cho thành viên, không thêm danh tính vào payload; review kịch bản chiếu trước production |
| R-25 | Upload lớn bị gián đoạn, app retries bị chặn hoặc partial asset bị dùng nhầm | M | M | Mobile + Backend + Infra | Durable `core.upload_sessions`/`core.upload_parts`, 4 MiB object PutObject chunks, byte/request/session caps, checksum/AV gate, final low-level PutObject; OI-18 POC trước tích hợp |
| R-26 | Teacher Deck bỏ sót activity hoặc Parent Guide tạo line-art khó hiểu/không phù hợp độ tuổi, unsafe hay bị giữ lâu hơn dự kiến | M | H | AI lead + Teacher/Parent Product/Design + Privacy | Contract/topic allowlist, 3–5 ordered steps, line-art/media/malware/age-safety checks, adult preview/skip, automated safety, private temporary asset expiry/cleanup, separate cost/rate caps, synthetic quality/license/cost POC OI-19; không dùng child profile/artwork làm input |

### 29.1 Cổng trước synthetic end-to-end live

- Pin LTX inference workflow tương thích, GPU image và dependency versions hiện hành.
- Benchmark Modal L40S video job và các stage model nhỏ trên L4 bằng asset tự tạo/test-only.
- Benchmark Teacher Sketch provider/model trên lesson/activity fixtures tổng hợp; kiểm coverage, line-step quality, age fit, safety, license, latency và compute cost trước khi bật deck generation.
- Xác minh bounded upload/result transfer giữa local backend và Modal.
- Tạo profile, image, audio và lesson fixture chỉ dùng synthetic.
- Xác minh không có provider/API credential trong client bundle hoặc source control.
- Xác minh domain constraints, run state machine, script approval gate và sample uniqueness trước khi bật UI flow.

### 29.2 Cổng trước khi dùng dữ liệu thật hoặc production

- Xác định bằng văn bản trường/tổ chức và nền tảng giữ vai trò nào đối với từng mục đích; ký thỏa thuận xử lý dữ liệu phù hợp, xác định lawful purpose/authorization/guardian role, privacy notices và ai tiếp nhận yêu cầu chủ thể dữ liệu (DSR).
- Thiết kế quy trình tiếp nhận, xác minh, theo dõi và thực hiện quyền truy cập/sửa/xóa/nhận bản sao khi áp dụng; không suy diễn thời hạn luật định trong SRS, để legal owner chốt theo pháp luật hiện hành và vai trò controller/processor.
- Có incident/breach runbook gồm phát hiện, cô lập, evidence, escalation, communications và mốc notification do counsel xác nhận; không hard-code thời hạn pháp lý nếu chưa được review.
- Lập data-flow/processing inventory cho Firebase Auth, Modal, payment, email, push, object store, logs/backups; đánh giá chuyển dữ liệu xuyên biên giới, vùng xử lý, hợp đồng provider và cơ chế xóa bản sao trước khi truyền dữ liệu thật.
- Chốt retention tối đa theo từng record class (profile, media, transcript, lesson, run, billing, audit/log, backup); xác định backup expiry, purge/crypto-shredding, deletion receipt và exception/legal hold trước real-data enablement.
- Thực hiện DPIA/đánh giá tác động/quy trình hồ sơ theo yêu cầu pháp luật áp dụng và quyết định counsel; SRS không tự kết luận loại tổ chức được miễn hoặc phải thực hiện.
- Rà soát Luật số 91/2025/QH15, văn bản liên quan bảo vệ trẻ em và các văn bản hướng dẫn mới nhất với chuyên gia pháp lý. Nguồn chính thức được liệt kê tại §15; links chỉ là nguồn kiểm tra, không phải ý kiến pháp lý.
- Rà Google Play Families/target-audience, privacy disclosures, child-safety content, permissions, SDK/provider policy và listing trước Play publication; phê duyệt store-specific implementation riêng.
- Chọn production hosting/region/network/object store, secret manager, observability/alert path, email provider và backup/restore objective.
- Có merchant sandbox/production approval và xác minh hợp đồng callback/signature recurring MoMo/VNPAY chính xác.
- Chốt commercial prices, hóa đơn điện tử/VAT, xử lý thuế/invoice, quy tắc rounding/day-count proration, cancellation/recovery/refund disclosures và customer support operations với legal/accounting.
- Review công thức prorate VND half-up đề xuất trước thu phí thật; cấu hình thuế/discount riêng nếu áp dụng.
- Định nghĩa Parent registration/account recovery, Teacher invitation/activation, organization bootstrap và UX cấp role chính xác.
- Thực hiện live DB schema/row inventory, staged migration rehearsal, backup/restore, reconciliation và rollback evidence.
- Phê duyệt implementation plan riêng, có người phụ trách và integration allocation rõ ràng.

<a id="srs-30"></a>
## 30. Truy vết mở rộng

<a id="srs-30-1"></a>
### 30.1 Ánh xạ use case tới requirement

| Use case | Requirement được bao phủ |
|---|---|
| UC-01 Parent profile | FR-C-01, FR-C-04, FR-C-05; BR-03, BR-18–21 |
| UC-02 Parent story/video | FR-C-12, FR-P-01–10, FR-AI-01–12; BR-01–03, BR-08, BR-13–27, BR-36 |
| UC-03 Teacher profile | FR-T-02–05; BR-04–07 |
| UC-04 Lesson import/approval | FR-C-12, FR-T-06–09; BR-09, BR-22 |
| UC-05 Teacher sample | FR-C-12, FR-T-10–15, FR-AI-01–12; BR-01–02, BR-09–17, BR-36 |
| UC-06 Class/billing admin | FR-T-02/03, FR-B-01–09; BR-04/05, BR-28–33 |
| UC-07 Delete run | FR-C-08, FR-O-03; BR-26 |
| UC-08 Subscription | FR-B-01–09, FR-B-13; BR-28–34, BR-38 |
| UC-09 Delete profile | FR-C-10; BR-35 |
| UC-10 Quota view/purchase/consumption | FR-B-10–13; BR-11, BR-38 |
| UC-11 Cancel unfinished run | FR-C-03, FR-C-08; BR-02, BR-26, BR-40 |
| UC-12 Teacher reassignment/offboarding | FR-T-02/14; BR-05/06; Q130 |
| UC-13 Teacher provisioning/account recovery | FR-C-01, FR-O-09 |
| UC-14 Catalog publish/retire | FR-P-05, FR-T-09; BR-08/36 |
| UC-15 Push registration/revocation | FR-B-09/14; NFR-26; Q131 |
| UC-16 Quota exhaustion/top-up and in-run unsuitable-video action | FR-P-09, FR-T-12–16, FR-B-10–14; BR-11/16/38 |
| UC-17 Tạo và trình chiếu Teacher AI Sketch Deck | FR-T-18–20, FR-AI-01/14, NFR-33; BR-42–44 |

<a id="srs-30-2"></a>
### 30.2 Ánh xạ requirement tới entity đích

| Nhóm requirement | Entity đích chính |
|---|---|
| Quyền sở hữu và revision hồ sơ Parent | parent.child_profiles, parent.profile_revisions, parent.profile_context_entries, parent.profile_support_needs, parent.data_authorizations |
| Tổ chức, lớp và roster Teacher | be1.organizations, be1.classrooms, be1.managed_profiles, be1.enrollments, be1.organization_assignments, be1.profile_revisions/context/support |
| Giáo án, kế hoạch và Teacher Sketch Deck | lesson.occurrences, lesson.source_documents, lesson.document_revisions, lesson.plan_revisions, lesson.plan_activities, lesson.sketch_deck_revisions, lesson.sketch_deck_steps |
| Run một trẻ, input/context và story | story.runs, story.run_inputs (bao gồm snapshot context giới hạn), story.transcript_revisions, story.understanding_revisions, story.story_revisions, story.story_scenes, story.review_decisions |
| Tạo scene/video và output | story.video_generations, story.video_generation_scenes, ai_jobs.job/attempt/events/completion_receipt, core.asset_metadata/asset_lineage |
| Catalog hoạt động đã duyệt | learning_content.record/version/review/receipt/event/outbox |
| Billing tổ chức | billing.price_versions, organization_subscriptions, capacity_periods, invoices, payment_attempts, provider_event_receipts, subscription_events |
| Grant quota và usage video đã nhận | billing.video_quota_grants, **billing.video_quota_usage**; usage không FK tới run/media và AI Policy không sở hữu quota sản phẩm |
| Thông báo và push endpoint | notifications.inbox_items, notifications.delivery_attempts, **notifications.push_endpoints** |
| Audit, AI job và AI policy | Core audit/outbox/consumer receipts; ai_jobs; toàn bộ ai_policy ledgers |
| Reusable lesson library và nội dung lesson | lesson.library_items/library_versions/version_activities/version_visual_assets; lesson.occurrences/plan_revisions/plan_activities |
| Lesson visibility, approval và sharing | lesson.access_grants; be1.parent_groups/parent_group_members |
| Parent–Teacher profile sharing | parent.profile_share_grants; parent.child_profiles; be1.managed_profiles; identity/assignment owner ports |
| Lesson delivery, Parent history và feedback | lesson.delivery_recipients/delivery_feedback/feedback_replies; active profile-share grants |
| Lesson upload filtering và AI draft/visual jobs | lesson.source_documents/document_revisions/library_versions/version_visual_assets; ai_jobs.job; core.asset_lineage |

Tổng target v2.3 như §1.1 và DATA_TABLE_REGISTER.md là 89 bảng active (38 retained/refactored + 51 new) và 48 source table legacy/read-only, tổng vật lý dự kiến 137 theo source declarations. Sáu bảng nghiệp vụ baseline được giữ gồm `billing.video_quota_usage`, `notifications.push_endpoints`, `core.upload_sessions`, `core.upload_parts`, `lesson.sketch_deck_revisions` và `lesson.sketch_deck_steps`; 11 logical entity của lớp nền tảng được bổ sung tại §14.1 của DATA_TABLE_REGISTER.md. 13 AI Policy source table bị deferred: 12 provider-copy registry và `resource_receipt`; resource event chứa idempotency receipt cho new writes. Bốn helper/snapshot table bị loại: job subject refs đã có target StoryRun; job result refs thuộc aggregate Story/Lesson; snapshot context/item được lưu gọn, có schema/hash/giới hạn trong `story.run_inputs`. Không đưa diagram hoặc PDF vào bản mở rộng này.

<a id="srs-30-3"></a>
### 30.3 Ma trận truy vết FR/NFR theo từng ID

Mỗi requirement được liệt kê riêng để giữ đường truy vết hai chiều. Ma trận có tám cột cố định; `M`/`S` là ưu tiên và khớp danh mục FR/NFR ở §§7–8. `M` là điều kiện bắt buộc trong pha được ghi, kể cả khi pha đó là production gate; `S` là mục tiêu ưu tiên nhưng có thể hoãn bằng quyết định rủi ro. UC/phạm vi nêu các use case áp dụng hoặc phạm vi cross-cutting. Cột xác minh là phương pháp dự kiến, chưa phải test report. `DRAFT` nghĩa là chưa có sign-off cho tài liệu; nguồn Q/BR chỉ cho biết nội dung nghiệp vụ đã chốt, không chứng minh requirement đã được triển khai.

| ID | Ưu tiên | Nguồn/lý do (BR/Q) | UC/phạm vi | Owner/entity đích | Verification dự kiến | Pha | Trạng thái duyệt |
|---|---|---|---|---|---|---|---|
| FR-C-01 | M | BR-03 | UC-01/13 | be1.adult_identities; Firebase Authentication verifier | API auth cases: valid Parent/Teacher, cross-scope setup, generic error; confirm no UID enumeration. AC-01. | P0; lifecycle as shared Parent/Teacher slice | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-C-02 | M | BR-01 | UC-02/05 | story.runs.profile_ref; ai_jobs.job.target_kind/target_ref | Run has exactly one scalar profile; Story job resolves it from canonical StoryRun, without a batch or subject-ref table. AC-02/03. | P0; lifecycle as shared Parent/Teacher slice | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-C-03 | M | BR-02 | UC-02/05/11 | story.runs.active_owner_parent_account_id / active_owner_teacher_id | Concurrent create commands for same current owner; assert DB uniqueness and lock transfer. AC-02/31. | P0; lifecycle as shared Parent/Teacher slice | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-C-04 | M | BR-03 | UC-01/03 | be1.adult_identities; parent.child_profiles; be1.managed_profiles | Negative API/DB matrix: Parent cannot resolve Teacher profile and vice versa. AC-01. | P0; lifecycle as shared Parent/Teacher slice | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-C-05 | M | BR-18/19 | UC-01/03 | parent.profile_revisions/context_entries; be1.profile_revisions/context_entries | Edit profile twice; prove append-only history and age/context schema bounds. AC-08/16. | P0; lifecycle as shared Parent/Teacher slice | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-C-06 | M | BR-19/21 | UC-01/03 | parent.profile_context_entries; be1.profile_context_entries; story.run_inputs | Provenance check: app history vs external experience stays distinct; only approved selected context enters the bounded snapshot on the exact input revision. AC-08. | P0; lifecycle as shared Parent/Teacher slice | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-C-07 | M | BR-20 | UC-01/03 | parent.profile_support_needs; be1.profile_support_needs; story.run_inputs | Role-denial for support notes; verify support values remain excluded from run-input snapshot by default. AC-21. | P0; lifecycle as shared Parent/Teacher slice | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-C-08 | M | BR-26/40 | UC-07/11 | story.runs; story.video_generations; be1.data_lifecycle_requests; core.asset_metadata; billing.video_quota_usage; lesson.occurrences | Cancel/delete GWT: lock release, asset purge, quota ledger and sample tombstone retained. AC-13/23. | P0; lifecycle as shared Parent/Teacher slice | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-C-09 | S | BR-25/26 | UC-07 | core.asset_metadata; core.asset_lineage | Compare source/derived hashes and lineage; assert no binary or duplicated media metadata in rows. AC-10/29. | P0; lifecycle as shared Parent/Teacher slice | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-C-10 | M | BR-35 | UC-09 | parent.child_profiles/data_authorizations; be1.managed_profiles/data_lifecycle_requests; story.runs | Deletion review: owner authorization, immediate revoke, lifecycle receipt and cross-scope isolation. AC-13. | P0; lifecycle as shared Parent/Teacher slice | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-C-11 | M | BR-39/40 | UC-02/05/11 | story.runs; ai_jobs.job; notifications.inbox_items/delivery_attempts/push_endpoints | Fake-clock reminder/closeout at 144h/168h, verified-email gate, admission exclusion, 6h job deadline. AC-22/30; AT-11. | P0; lifecycle as shared Parent/Teacher slice | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-C-12 | M | NFR-32; upload reliability on mobile networks | UC-02/04/05 | core.upload_sessions; core.upload_parts; core.asset_metadata; ai_jobs.job | Upload POC: restart/resume, exact/conflicting chunk, order/hash/AV/TTL, final PutObject and rates. AC-29/32; AT-10/13. | P0/P1 before real Parent/Teacher media | DRAFT/đề xuất kỹ thuật; chưa sign-off |
| FR-P-01 | M | Owner scope/legacy Parent flow; §16 | UC-02/16 | apps/mobile; apps/ui-mobile (reference only); no persistent table | Walkthrough apps/mobile contract; map reference behavior without restoring collaboration runtime. AC-03/20. | P1 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-P-02 | M | BR-01/18/27 | UC-02/16 | parent.child_profiles; parent.profile_revisions; core.upload_sessions; core.asset_metadata | Android API walkthrough: owned profile, camera/library asset and ownership-mismatch cases. AC-02/13. | P1 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-P-03 | M | BR-23 | UC-02/16 | story.run_inputs; story.transcript_revisions; ai_jobs.job; core.asset_metadata | ASR fixtures: ≤2m accepted, over-limit rejected, corrected transcript required before story. AC-08/21. | P1 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-P-04 | M | BR-15/16 | UC-02/16 | story.understanding_revisions; story.run_inputs; story.review_decisions; core.asset_lineage | VLM fixtures: detection, correction and new interpretation revision pinned to asset hash. AC-08/19. | P1 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-P-05 | M | BR-08 | UC-02/16 | learning_content.record/version/review/receipt | Catalog query: published versions only; deterministic filtering/order plus age/safety boundaries. AC-05. In addition, verify the Parent flow has no pre-video activity-selection step and presents the lesson activity list after video is viewable; lesson binding, read authorization and projection/revocation cases (tham chiếu lesson-version opaque tùy chọn qua cổng module Lesson; không gắn org/class/occurrence của Teacher; quyền đọc catalog/xem trước lesson tách khỏi điều kiện tạo video; không cấp quyền đọc mới; VIDEO_READY sau kiểm tra kỹ thuật và an toàn; Parent không cần xem hết video; hoàn tất không có nghĩa đã làm hoạt động; kiểm quyền hiện hành trước khi trả nội dung; lesson bị thu hồi/gỡ phát hành thì ẩn danh sách, video không bị ảnh hưởng và không fallback sang catalog công khai). AC-52; B2 Q1=A. [Còn mở cho thiết kế vật lý: vị trí lưu vật lý tham chiếu lesson-version]. | P1 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-P-06 | M | BR-19/21 | UC-02/16 | parent.profile_revisions/context_entries; story.run_inputs; story.review_decisions | Snapshot API rejects unapproved context; pins selected profile revision and context hash on the immutable run-input revision. AC-08. | P1 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-P-07 | M | BR-13/14 | UC-02/16 | story.story_revisions; story.story_scenes; story.review_decisions; ai_jobs.job | Three rewrites accepted, fourth denied; no direct scene-edit endpoint. AC-06. | P1 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-P-08 | M | BR-14/15 | UC-02/16 | story.runs; story.story_revisions; story.review_decisions; story.video_generations | Script confirmation gate and playback after safety; verify 168h closeout/no video approval. AC-06/07/22. | P1 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-P-09 | M | BR-16/17 | UC-02/16 | story.runs; story.video_generations; story.review_decisions; core.asset_metadata | Suitability flow hides old output on accepted replacement; enforce 1+2 cap and ledger. AC-07/23. | P1 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-P-10 | S | NFR-13/21 | UC-02/16 | story.runs; ai_jobs.job/job_events; client error-state presentation | Localized walkthrough for stages, safe errors, retryability and no provider diagnostics. AC-20/22. | P1 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-P-11 | S | Q146; BR-46 | UC-02/16 | Parent UI/API; ai_jobs.job; core_asset_metadata/asset_lineage; ai_policy.resource_reservation/resource_event | Synthetic contract fixtures: request/skip/failure reach capture; verify topic-only input, no child-data egress, 3–5-step output validation, private expiry/cleanup, provenance and no video-quota entry. AC-44/45; AT-18/19. | P1 | DRAFT; model/license/cost and retention gates remain open |
| FR-T-01 | M | Owner scope for Teacher Web; §16 | UC-05 | apps/teacher-ui; versioned API contract; no persistent table | Web route walkthrough in supported browsers; verify no Parent/collaboration UI coupling. AC-03/30. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-02 | M | BR-04/05 | UC-03/06/12 | be1.organizations/classrooms/enrollments/organization_assignments; billing.capacity_periods | BE1 authorization/concurrency checks for capacity, roster and one responsible Teacher. AC-14/25. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-03 | M | BR-04 | UC-06/08 | billing.price_versions/organization_subscriptions/capacity_periods; be1.classrooms | Billing fixture: ten included slots plus add-ons; concurrent creation cannot exceed capacity. AC-14. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-04 | M | BR-07 | UC-03 | be1.managed_profiles; be1.profile_revisions; be1.profile_context_entries | Profile API: duplicate display names succeed with distinct IDs and immutable revisions. AC-16. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-05 | M | BR-05 | UC-03/06 | be1.managed_profiles; be1.enrollments | Enrollment constraint: one active class/profile; move closes prior enrollment exactly once. AC-03/25. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-06 | M | BR-22 | UC-04 | lesson.source_documents; core.upload_sessions/parts; core.asset_metadata | Parser fixtures for format/size/page/password/scan; assert no OCR call. AC-16/29. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-07 | M | BR-22 | UC-04 | lesson.source_documents; lesson.document_revisions; core.asset_metadata | Original asset immutable; edited extraction creates a new revision and review state. AC-16. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-08 | M | BR-09/10 | UC-04/05 | lesson.occurrences; lesson.plan_revisions; lesson.plan_activities | Occurrence workflow: multi-activity plan supported; child selection blocked before approval. AC-16. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-09 | M | BR-08 | UC-04/05/14 | lesson.plan_revisions; lesson.plan_activities | Custom activity without Teacher safety checklist cannot pass plan or create run. AC-05/16. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-10 | M | BR-01/09/21 | UC-05 | be1.enrollments/managed_profiles/profile_revisions; lesson.plan_activities; story.runs/run_inputs | Authorization GWT selects one roster profile, one activity and a context snapshot pinned to the run input. AC-02/08. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-11 | M | Q05/Q82 | UC-05 | apps/teacher-ui; core.upload_sessions/parts; core.asset_metadata | Camera permission and phone-upload fallback; both attach one validated artwork. AC-20/29. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-12 | M | BR-13/15 | UC-05/16 | lesson.plan_revisions/plan_activities; story.story_revisions/review_decisions/runs | Plan direction pinned; enforce 1+3 script revisions and script confirmation hash. AC-06/08. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-13 | M | BR-10/17 | UC-05/16 | lesson.occurrences; story.runs; story.video_generations | Occurrence-claim concurrency: playable safe output claims once; pre-claim failure leaves slot open. AC-04; AT-01. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-14 | M | BR-06; Q130 | UC-12 | be1.organization_assignments/classrooms; story.runs; core.audit_events | Saga fault injection: old fence, Story lock receipt, BE1 finalize/compensation, job completion and conflict. AC-25/31; AT-12. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-15 | S | BR-39 | UC-05/11 | lesson.occurrences; story.runs/video_generations; notifications.inbox_items | Occurrence projection walkthrough and fake-clock closeout; confirm one sample/no batch action. AC-18/22. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-16 | M | BR-37 | UC-05/15 | lesson.occurrences projection confirmation; story.video_generations; core.audit_events; ephemeral playback authorization | Playback capability denied before confirmation, after assignment revoke and after token expiry. AC-18. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-17 | M | BR-41; Q134 | UC-12 | be1.organization_assignments; story.runs; core.audit_events; billing.video_quota_usage; lesson.occurrences | Emergency authorization/reason, metadata-only audit, no admin media access, quota/sample retained. AC-25/31. | P2 | DRAFT; quyết định nghiệp vụ đã chốt; chưa sign-off |
| FR-T-18 | M | Q137–Q140; BR-42/43 | UC-17 | lesson.sketch_deck_revisions/steps; lesson.plan_revisions/activities; core.asset_metadata/lineage | Fixture plan-to-deck xác minh mọi hoạt động được bao quát, mỗi hướng dẫn vẽ có 3–5 bước theo thứ tự, có age band và không có tham chiếu trẻ/hồ sơ. AC-34. | P2 | DRAFT; quyết định đã chốt; model/chất lượng còn là cổng |
| FR-T-19 | M | Q140/Q142; BR-43 | UC-17 | Teacher presentation client; lesson.sketch_deck_steps; occurrence video playback API | Walkthrough xác minh trình chiếu trắng 16:9, điều khiển Back/Next/activity/subject/skip/regenerate, không vẽ tự do/PPTX và video truy cập được sau khi sẵn sàng. AC-35; NFR-33. | P2 | DRAFT; chưa sign-off tài liệu |
| FR-T-20 | M | Q139/Q142/Q143; BR-43/44 | UC-17 | lesson.sketch_deck_revisions/steps; ai_jobs.job; ai_policy.resource_reservation; không ghi Billing quota | Đổi plan hash và tạo lại một bước; xác minh chặn dữ liệu stale, revision deck mới bất biến, admission compute/rate riêng và không ghi video quota. AC-35; AT-16. | P2 | DRAFT; quyết định đã chốt; ngưỡng số còn chờ benchmark |
| FR-AI-01 | M | BR-23/36/43/45 | UC-02/05/16/17 | ai_jobs.job/attempt/job_events; story.runs; lesson.sketch_deck_revisions/steps; core.asset_metadata | Fixture contract cho target story/video và lesson-sketch; xác minh mỗi job có đúng một target, chỉ Story có subject trẻ, cùng stage/version/hash và attempt bền vững. AT-07/15/17. | P1 + P2 | DRAFT/đề xuất kỹ thuật; chưa sign-off |
| FR-AI-02 | M | BR-14/36 | UC-02/05/16 | ai_jobs.job/job_events; story.understanding_revisions/story_revisions; story.video_generations | Schema-negative fixtures for missing/extra/wrong-version fields; assert invalid/stale outputs are not persisted. AC-19/21. | P1 + P2 | DRAFT/đề xuất kỹ thuật; chưa sign-off |
| FR-AI-03 | M | BR-26/34 | UC-02/05/16 | core.asset_metadata/asset_lineage; Story/Lesson aggregate output refs; story.run_inputs | Lineage inspection for original vs derived media, source hash and model/config provenance. AC-10/29. | P1 + P2 | DRAFT/đề xuất kỹ thuật; chưa sign-off |
| FR-AI-04 | M | BR-24 | UC-02/05/16 | story.story_revisions; story.story_scenes; story.video_generations | Planner contract verifies 5–15 scenes and system-selected 30–90s duration within output schema. AC-06. | P1 + P2 | DRAFT/đề xuất kỹ thuật; chưa sign-off |
| FR-AI-05 | M | BR-01/24 | UC-02/05/16 | story.runs/run_inputs/understanding_revisions; ai_jobs.job.target_kind/target_ref; story.video_generations | Synthetic prompt/output rubric checks one child subject, anchor preservation and no PixiJS path. AC-02/07/19. | P1 + P2 | DRAFT/đề xuất kỹ thuật; chưa sign-off |
| FR-AI-06 | M | BR-17 | UC-02/05/16 | story.video_generation_scenes; ai_jobs.attempt/job_events; core.asset_metadata | Fault-inject each scene attempt; assert one initial + two retries then safe terminal failure. AC-04; AT-01. | P1 + P2 | DRAFT/đề xuất kỹ thuật; chưa sign-off |
| FR-AI-07 | M | BR-11/38 | UC-02/05/16 | billing.video_quota_usage; story.video_generations; ai_policy.resource_reservation/resource_event | Billing-ledger concurrency test: request cap and one quota unit per accepted request, no charge for scene retries. AC-17/23; AT-06/09. | P1 + P2 | DRAFT/đề xuất kỹ thuật; chưa sign-off |
| FR-AI-08 | M | BR-24 | UC-02/05/16 | story.video_generations/story_scenes; Story/Lesson aggregate output refs; core.asset_metadata | Media contract checks MP4/720p/16:9/Vietnamese narration/subtitles/no music. AC-07. | P1 + P2 | DRAFT/đề xuất kỹ thuật; chưa sign-off |
| FR-AI-09 | M | BR-16/25/36 | UC-02/05/16 | story.video_generations/review_decisions; core.asset_metadata; playback API authorization | Gate test blocks playback on missing/unknown safety validation and hides rejected output on accepted replacement. AC-07/21. | P1 + P2 | DRAFT/đề xuất kỹ thuật; chưa sign-off |
| FR-AI-10 | S | BR-25 | UC-02/05/16 | story.runs/video_generations; core.audit_events; ephemeral playback authorization | Playback-token negative test for wrong scope, revoked assignment, expiry and asset substitution. AC-18. | P1 + P2 | DRAFT/đề xuất kỹ thuật; chưa sign-off |
| FR-AI-11 | S | BR-34 | UC-02/05/16 | ai_jobs.job/attempt/job_events; ai_policy.resource_event; redacted telemetry | Synthetic run review of metrics/log fields; prove stage/GPU telemetry present and content absent. AC-12/28. | P1 + P2 | DRAFT/đề xuất kỹ thuật; chưa sign-off |
| FR-AI-12 | M | BR-36 | UC-02/05/16 | ai_policy.version/review; story.story_revisions/story_scenes; ai_jobs.job_events; core.asset_metadata | Adversarial synthetic corpus across transcript, lesson, story, frames and subtitles; fail-closed gate review. AC-21. | P1 + P2 | DRAFT/đề xuất kỹ thuật; chưa sign-off |
| FR-AI-13 | M | Q144; BR-45 | UC-02/05/16 | story.understanding_revisions/story_revisions/story_scenes/video_generations/video_generation_scenes; ai_jobs.attempt/completion_receipt; core.asset_metadata/lineage | Hợp đồng end-to-end với dữ liệu tổng hợp bao phủ neo Character Bible/reference, LTX theo scene, consistency, FFmpeg, TTS/phụ đề và safety trước playback; xác minh giới hạn retry/request. AC-36/37; AT-17. | P1 + P2 | DRAFT; LTX runtime/model và chất lượng chưa benchmark |
| FR-AI-14 | M | Q137–Q143; BR-42–44 | UC-17 | lesson.sketch_deck_revisions/steps; lesson.plan_activities; ai_jobs.job/attempt; core.asset_metadata/lineage; ai_policy compute ledger | Fixture output có cấu trúc xác minh coverage plan/hoạt động, schema line-art, chặn stale, media an toàn và compute metering riêng, không ghi video usage cho Billing. AC-34/35; AT-15/16. | P2 | DRAFT; POC model/chất lượng/license của Sketch còn mở |
| FR-AI-15 | S | Q146; BR-36/44/46 | UC-02/16 | ai_jobs.job/attempt/events; core_asset_metadata/asset_lineage; ai_policy.resource_reservation/resource_event | Synthetic contract fixtures verify generic topic/difficulty only, 3–5 progressive steps, no child-data egress, safety/media/provenance, temporary expiry/cleanup, separate resource caps and no video quota; skip/failure remains non-blocking. AC-44/45; AT-18/19. | P1 | DRAFT; model/license/cost and exact retention remain open gates |
| FR-B-01 | M | BR-28 | UC-06/08 | billing.price_versions | Inspect price-version fixtures for VND, 10 included slots and one add-on unit price by term. AC-14. | P3; quota admission foundation in P0 | DRAFT; quyết định nghiệp vụ đã chốt; cổng tích hợp còn mở |
| FR-B-02 | M | BR-28/30 | UC-08 | billing.organization_subscriptions; billing.payment_attempts; billing.provider_event_receipts; billing.subscription_events | Sandbox contract review for MoMo/VNPAY recurring lifecycle; VietQR route must be absent. AC-14. | P3; quota admission foundation in P0 | DRAFT; quyết định nghiệp vụ đã chốt; cổng tích hợp còn mở |
| FR-B-03 | M | BR-28/30 | UC-08 | billing.provider_event_receipts; billing.payment_attempts; billing.invoices; billing.subscription_events | Signed/unsigned, duplicate and out-of-order callback fixtures; verify invoice/subscription transaction idempotency. AC-14. | P3; quota admission foundation in P0 | DRAFT; quyết định nghiệp vụ đã chốt; cổng tích hợp còn mở |
| FR-B-04 | M | BR-29 | UC-06/08 | billing.capacity_periods; billing.invoices; billing.payment_attempts; billing.subscription_events; be1.classrooms | Proration arithmetic cases for mid-cycle slot purchase without shifting renewal date. AC-14. | P3; quota admission foundation in P0 | DRAFT; quyết định nghiệp vụ đã chốt; cổng tích hợp còn mở |
| FR-B-05 | M | BR-30 | UC-08 | billing.organization_subscriptions; billing.subscription_events; billing.invoices | Renewal-off command GWT: paid-through access remains; no automatic prorated refund event. AC-14. | P3; quota admission foundation in P0 | DRAFT; quyết định nghiệp vụ đã chốt; cổng tích hợp còn mở |
| FR-B-06 | M | BR-31 | UC-08 | billing.organization_subscriptions; billing.subscription_events; billing.capacity_periods; be1.classrooms | Fake-clock renewal test at 7-day grace boundary; creation blocked while existing roster remains readable. AC-14. | P3; quota admission foundation in P0 | DRAFT; quyết định nghiệp vụ đã chốt; cổng tích hợp còn mở |
| FR-B-07 | M | BR-32 | UC-06/08 | billing.subscription_events; be1.classrooms; billing.capacity_periods | Downgrade fixture selects classes; event history and read-only projection match effective time. AC-14. | P3; quota admission foundation in P0 | DRAFT; quyết định nghiệp vụ đã chốt; cổng tích hợp còn mở |
| FR-B-08 | M | BR-33 | UC-08/15 | billing.invoices; billing.organization_subscriptions; notifications.inbox_items/delivery_attempts | Schedule tests at -7d/-1d plus paid/failed/grace events; verify admin recipient only. AC-26. | P3; quota admission foundation in P0 | DRAFT; quyết định nghiệp vụ đã chốt; cổng tích hợp còn mở |
| FR-B-09 | S | BR-33 | UC-15 | core.outbox_events; notifications.inbox_items/delivery_attempts/push_endpoints; billing.provider_event_receipts | Outbox duplicate/retry/provider-failure fixture; inbox remains canonical and delivery retries are bounded. AC-26. | P3; quota admission foundation in P0 | DRAFT; quyết định nghiệp vụ đã chốt; cổng tích hợp còn mở |
| FR-B-10 | M | BR-38; Q132 | UC-10/16 | billing.video_quota_grants; billing.video_quota_usage | Grant/usage ledger tests across Parent and org scopes, monthly reset, expiry and top-up FIFO. AC-17/23. | P3; quota admission foundation in P0 | DRAFT; quyết định nghiệp vụ đã chốt; cổng tích hợp còn mở |
| FR-B-11 | M | BR-38; Q128 | UC-10/16 | ai_policy.budget_bucket/resource_reservation/resource_event; billing.video_quota_grants/video_quota_usage; story.video_generations | Saga fault-injection across reservation, Billing usage and Story acceptance; reconcile by one key without cross-owner SQL. AC-17/24; AT-06/08/09. | P3; cost-reservation foundation in P0 | DRAFT; quyết định nghiệp vụ đã chốt; cổng tích hợp còn mở |
| FR-B-12 | S | Q115/Q117–Q126 | UC-10 | billing.video_quota_grants/video_quota_usage; scoped quota-summary API | Quota-summary API scope and arithmetic checks; verify no account/run enumeration. AC-17. | P3; quota admission foundation in P0 | DRAFT; quyết định nghiệp vụ đã chốt; cổng tích hợp còn mở |
| FR-B-13 | S | Q120 | UC-10 | billing.invoices/payment_attempts/provider_event_receipts/video_quota_grants | Payment callback to invoice/grant GWT; unverified event and duplicate top-up create no second grant. AC-17/14. | P3; quota admission foundation in P0 | DRAFT; quyết định nghiệp vụ đã chốt; cổng tích hợp còn mở |
| FR-B-14 | M | Q129/Q131/Q133/Q136 | UC-15/16 | notifications.inbox_items/delivery_attempts/push_endpoints; story.runs; billing.organization_subscriptions | Fake-clock run reminder plus billing notice checks; email only for verified current-owner address; inbox authoritative; push best effort. AC-22/26; AT-05/11. | P3; quota admission foundation in P0 | DRAFT; quyết định nghiệp vụ đã chốt; cổng tích hợp còn mở |
| FR-O-01 | M | NFR-01; clean-architecture rule | UC-01–UC-16; cross-cutting | Domain/application/infrastructure package boundaries; no product table | Static dependency/import review confirms domain direction and framework/provider isolation. AC-11. | P0; deployment gates in P4 | DRAFT/đề xuất kỹ thuật hoặc cổng |
| FR-O-02 | M | FR-O-02; contract version rule | UC-01–UC-16; cross-cutting | Versioned API/event/queue/asset/profile contracts; core.outbox_events; ai_jobs.outbox | Contract compatibility fixtures verify supported version, rejected major version and idempotent event replay. AC-19. | P0; deployment gates in P4 | DRAFT/đề xuất kỹ thuật hoặc cổng |
| FR-O-03 | M | Docker/local deployment rule | UC-01–UC-16; cross-cutting | Docker Compose services; PostgreSQL; Redis/RQ; MinIO; no product table | Docker Compose inspection and readiness walkthrough confirm DB/queue/storage topology. AC-12. | P0; deployment gates in P4 | DRAFT/đề xuất kỹ thuật hoặc cổng |
| FR-O-04 | M | Repository security rules | UC-01–UC-16; cross-cutting | Backend runtime secret configuration; client package boundary; no product table | Secret/config inspection confirms no provider credential or endpoint in mobile/browser artifacts. AC-28. | P0; deployment gates in P4 | DRAFT/đề xuất kỹ thuật hoặc cổng |
| FR-O-05 | M | NFR-02/24 | UC-01–UC-16; cross-cutting | API error envelope; core.audit_events; structured logs/metrics | API contract review for safe code, correlation ID, retryability and 404/403 disclosure rules. AC-27. | P0; deployment gates in P4 | DRAFT/đề xuất kỹ thuật hoặc cổng |
| FR-O-06 | M | NFR-12/22/25 | UC-01–UC-16; cross-cutting | Rate-limit configuration; ai_jobs.job; ai_policy.resource_scope/budget_bucket/resource_reservation | Load fixtures verify account/IP/operation caps, queue/GPU bounds, 429 Retry-After and fairness. AC-28. | P0; deployment gates in P4 | DRAFT/đề xuất kỹ thuật hoặc cổng |
| FR-O-07 | S | NFR-11/27 | UC-01–UC-16; cross-cutting | Health/readiness endpoints; OTel/Prometheus/Grafana configuration | Compose walkthrough checks health/readiness, dashboard inputs and redacted operator logs. AC-12. | P0; deployment gates in P4 | DRAFT/đề xuất kỹ thuật hoặc cổng |
| FR-O-08 | S | Q68; NFR-07 | UC-01–UC-16; cross-cutting | PostgreSQL/MinIO volume and backup/restore procedures | Documented synthetic PostgreSQL/MinIO backup restore drill checks object hash and lineage parity. AC-12. | P0; deployment gates in P4 | DRAFT/đề xuất kỹ thuật hoặc cổng |
| FR-O-09 | M | Q20; identity provisioning gate | UC-01–UC-16; cross-cutting | be1.adult_identities; be1.organization_assignments; core.audit_events; Firebase Authentication | Provision/recovery walkthrough: verified Firebase identity only; server-controlled role/assignment and no UID scope disclosure. AC-01/27. | P0; deployment gates in P4 | DRAFT/đề xuất kỹ thuật hoặc cổng |
| FR-O-10 | M | Q129/Q133 | UC-01–UC-16; cross-cutting | story.runs; story.video_generations; ai_jobs.job/job_events; notifications.inbox_items | State-machine contract tests cover INPUT_PROCESSING, admission, adult-wait, safe errors and independent 6h/168h deadlines. AC-22; AT-07/11. | P0; deployment gates in P4 | DRAFT/đề xuất kỹ thuật hoặc cổng |
| NFR-01 | M | Quy tắc kiến trúc sạch và chiều phụ thuộc của repository | UC-01–UC-16; áp dụng xuyên kiến trúc | Python package/import graph; no persistence entity | Static import/dependency review: domain imports no framework/provider/storage/queue/UI. AC-11. | P0 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-02 | M | BR-01–06/10/38; quy tắc phân quyền từ chối mặc định và quy tắc repository | UC-01–UC-16; mọi thao tác có xác thực | be1.adult_identities/organization_assignments; parent.child_profiles; story.runs; core.asset_metadata; billing scopes | Negative API/DB scope matrix across Parent, Teacher, admin, run and playback resources. AC-01/27. | P0/P4 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-03 | M | Demo chỉ dùng dữ liệu tổng hợp; Q66/Q129/Q133; yêu cầu riêng tư và redact telemetry | UC-01–UC-16; mọi luồng dữ liệu cá nhân | Parent/BE1 profile revisions; story.runs/context snapshots; core.asset_metadata/asset_lineage; backup volumes | Synthetic data-flow and log inspection; confirm prohibited content absent and source class labelled. AC-13/28. | P0/P4 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-04 | M | BR-03; Q01; tách quyền sở hữu dữ liệu Parent và Teacher | UC-01/03/05/06/09/12/13 | be1.adult_identities; parent.child_profiles; be1.managed_profiles | Try cross-linking Parent and Teacher IDs through API and DB checks; all attempts fail closed. AC-01. | P0/P4 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-05 | M | BR-01–06/10/11/17/26/38/40; invariant được ép ở database | UC-01–UC-16; mọi luồng đổi trạng thái | story.runs/video_generations; be1.enrollments/organization_assignments; lesson.occurrences; Billing ledgers | DB concurrency review for one child/run, active owner, enrollment, sample, cap, quota and callback constraints. AC-02/04/17/25. | P0/P4 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-06 | M | FR-AI-01–12; quy tắc job bất đồng bộ và input bất biến | UC-02/04/05/10/16 | story revisions/runs; ai_jobs.job/attempt/job_events/outbox; core.outbox_events | Inject stale revision/hash and duplicate job event; current aggregate head must not change. AC-19; AT-07. | P0–P4 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-07 | M | Q68; mục tiêu phục hồi local bằng Docker | UC-01–UC-16; vận hành khôi phục | PostgreSQL; MinIO; Docker Compose volumes and backup metadata | Compose restart plus documented backup/restore drill; compare PostgreSQL and MinIO lineage/object hashes. AC-12. | P0/P4 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-08 | S | Mục tiêu độ phản hồi API; cổng benchmark OI-02/OI-03/OI-08 | UC-01–UC-16; API/queue | API metrics; ai_jobs.job; ai_policy.resource_reservation; core.asset_metadata | Synthetic load benchmark reports p95 read/control-plane targets separately from inference. AC-12/28. | P0/P4 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-09 | M | Q04/Q05/Q10/Q51/Q54; quy tắc tiếp nhận và xác thực media/tệp | UC-02/04/05 | core.upload_sessions/upload_parts/asset_metadata; lesson.source_documents; ai_jobs.job | Upload/parser integration fixtures for MIME, size, decode, pages, checksum and AV fail-closed cases. AC-29/32. | P1/P2 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-10 | M | BR-25; phân quyền playback bằng token ngắn hạn | UC-02/05/07/16 | story.video_generations; lesson.occurrences; playback authorization API | Token tests for wrong actor, revoked assignment, expired token and asset substitution. AC-18. | P1/P2 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-11 | M | Yêu cầu monitoring của repository; chính sách redact telemetry | UC-01–UC-16; monitoring xuyên hệ thống | OTel logs/traces/metrics; no content entity | Inspect structured logs/traces/metrics after synthetic run; verify redact before sampling/export. AC-12/28. | P0 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-12 | M | Yêu cầu rate limit và fairness tại §9/§25 | UC-01–UC-16; các thao tác API | Redis/runtime rate-limit configuration; core.upload_sessions/upload_parts; ai_jobs.job | Load each configured bucket; verify 429/Retry-After, independent chunk budget and tenant fairness. AC-28/32. | P0 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-13 | M | Yêu cầu usability của persona Parent/Teacher và giao diện tiếng Việt | UC-01–UC-16; màn hình dành cho người lớn | Parent Android and Teacher Web client; no persistence entity | Parent/Teacher moderated walkthrough for task completion, plain-language errors and confirmation burden. AC-20. | P1/P2 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-14 | M | Quy tắc kiến trúc sạch, version contract và quyền sở hữu module của repository | UC-01–UC-16; kiến trúc xuyên hệ thống | Domain/application/adapter dependency graph and versioned contracts; no table | Architecture import rule and contract type review; verify no cross-module SQL write path. AC-11/24. | P0 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-15 | M | Quy tắc quản lý secret của repository; Firebase chỉ dùng Authentication | UC-01–UC-16; cấu hình runtime | Runtime secret configuration; Firebase Authentication only; no product table | Secret scanning/config review: placeholders only, no provider key in app; Firebase SDK uses Auth only. AC-28. | P0 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-16 | M | Q79/Q84; bảo toàn dữ liệu nguồn và migration theo pha | UC-01–UC-17; migration xuyên hệ thống | 86 source mappings, 38 retained/refactored, 51 new, 89 active, 48 legacy; DATA_TABLE_REGISTER | Migration rehearsal inventory, row parity, source-to-target crosswalk and restore evidence before cutover. AC-09/12. | P4 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-17 | M | Ranh giới lỗi provider và chính sách retry có giới hạn tại §12/§22 | UC-02/04/05/16 | ai_jobs.job/attempt/job_events; provider adapter contracts | Stub provider timeout, malformed response, unavailable and retry-exhaustion fixtures; no silent fallback. AC-19/21. | P1/P2 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-18 | M | Q66/Q129/Q133; backup chỉ có dữ liệu tổng hợp; cổng riêng tư dữ liệu thật | UC-01–UC-16; backup/lifecycle operations | Profile revisions; story.runs/context/media; core.asset_metadata/lineage; backup lifecycle | Retention/delete drill over profile, story media, backups; verify only synthetic backup data before gate. AC-13. | P0/P4 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-19 | M | Q03/Q75/Q83; cổng đánh giá chất lượng AI/an toàn bằng dữ liệu tổng hợp | UC-02/05/16 | story.video_generations/scenes; core.asset_lineage/asset_metadata; synthetic evaluation corpus | Synthetic rubric for subject anchors, scenes, narration/subtitle and safety coverage; report no real-data claim. AC-21. | P1/P2 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-20 | M | Yêu cầu accessibility cho Parent/Teacher | UC-01–UC-16; luồng giao diện người dùng | Android/Web interaction and accessibility semantics; no persistence entity | Automated scan plus manual keyboard/screen-reader/contrast/focus review of critical flows. AC-20. | P1/P2 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-21 | M | Ngôn ngữ do chủ sở hữu chọn; API không phụ thuộc ngôn ngữ; quy tắc VND/UTC | UC-01–UC-16; nội dung giao diện | billing.price_versions/invoices; UTC timestamps and locale formatting adapters | API/UI checks for Vietnamese labels, UTC storage, Asia/Ho_Chi_Minh quota period and VND rendering. AC-17/26. | P0–P4 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-22 | S | Đề xuất queue/concurrency demo; cổng benchmark OI-02/OI-03/OI-08 | UC-02/05/10/16 | ai_jobs.job/outbox; ai_policy.resource_scope/budget_bucket/resource_reservation; queue metrics | Synthetic queue benchmark at stated concurrency; prove round-robin fairness, bounded wait and full-queue refusal. AC-28. | P0/P4 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-23 | M | BR-36; chính sách an toàn nội dung trẻ em và cổng safety đầu ra | UC-02/05/14/16 | ai_policy.version/review; learning_content.version/review; story revisions/scenes; job validation | Adversarial synthetic policy cases; fail-closed on unknown output-safety result before playback. AC-21. | P0/P4 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-24 | M | Quy tắc bảo mật repository; STRIDE và phòng vệ nhiều lớp | UC-01–UC-16; mọi trust boundary | be1 identity/assignment; core upload/audit; Billing callbacks; Modal/payment/notification adapters | STRIDE review and negative tests for MFA, RLS/DB role, Play Integrity, AV, upload, payment and Modal boundaries. AC-28. | P0/P4 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-25 | M | Q128; kiểm soát chi phí AI; cổng benchmark OI-02/OI-03/OI-08 | UC-02/05/10/16 | ai_policy.budget_bucket/resource_reservation/resource_event; billing.video_quota_usage; story.video_generations | Cost-reservation fault injection at request/day caps; reject before quota and never overspend accepted reservation. AT-08/09. | P0/P4 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-26 | S | Q97/Q131; thiết kế inbox và push best-effort | UC-15/16 | notifications.inbox_items/delivery_attempts/push_endpoints | Inbox fallback test when push/email fails; verify dedupe, endpoint revoke and payload minimization. AC-22/26; AT-05. | P3 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-27 | S | Q68; đề xuất phục hồi/SLO và cổng vận hành production | UC-01–UC-16; vận hành xuyên hệ thống | PostgreSQL/MinIO Compose services; backup/restore records and operational metrics | Measure local readiness, then execute manual RPO/RTO restore drill; production target stays marked unverified. AC-12. | P0/P4 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-28 | M | Giới hạn input/output tại §10.4/§24.2; cổng capacity lưu trữ/GPU | UC-02/04/05/10/16 | core.asset_metadata/asset_lineage; ai_jobs.attempt; ai_policy budget; billing.video_quota_usage | Capacity calculation from synthetic sizes and measured GPU seconds; assert output/file caps. AC-28. | P0/P4 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-29 | S | Mục tiêu accessibility; nguồn WCAG/WCAG2ICT tại §15 | UC-01–UC-16; luồng giao diện người dùng | Teacher Web accessibility; Android platform accessibility; no persistence entity | Automated accessibility scan and manual keyboard/screen-reader/contrast/focus checklist for Teacher Web. AC-20. | P1/P2 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-30 | M | Nền tảng Android Gradle trong repository và mục tiêu hỗ trợ trình duyệt | UC-01–UC-16; luồng client | apps/mobile Gradle/Android target; Teacher browser matrix; no product table | Record tested Android API/device and Chrome/Edge stable versions; run release smoke matrix. AC-20. | P1 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-31 | M | Q66/Q129/Q133; lựa chọn retention cho demo tổng hợp và cổng retention production | UC-07/09/11/12/16 | parent/be1 lifecycle entities; story.runs; core assets; billing retention exceptions; backup policy | Deletion and backup-expiry tabletop; verify production gate blocks real data absent approved retention. AC-13. | P0/P4 | PROPOSED/GATE; chưa sign-off tài liệu |
| NFR-32 | M | Q05/Q10/Q54; độ bền mạng di động và giới hạn upload tại §10.4/§24.2 | UC-02/04/05 | core.upload_sessions; core.upload_parts; core.asset_metadata; lesson.source_documents | Network interruption POC: resume session after restart; verify chunks, hashes, byte rate, TTL, AV and final PutObject. AC-29/32; AT-10/13. | P0/P1 | PROPOSED; POC năng lực adapter lưu trữ còn mở |
| NFR-33 | M | Q138/Q140/Q142; khả năng chiếu và điều khiển deck Teacher | UC-17; màn hình trình chiếu Teacher | lesson.sketch_deck_revisions/steps; ngữ nghĩa truy cập của Teacher Web; không có bảng trẻ/hồ sơ | Xác minh viewport 16:9 tối thiểu 1280×720, line-art tương phản trên nền trắng, chữ ngắn, focus/nhãn bàn phím, không phụ thuộc riêng màu và độ tương phản WCAG 2.2 AA. AC-35. | P2 | PROPOSED; cần review giao diện/chiếu thử |
| FR-PL-01 | M | Q148; NFR-34 | §31.3, mọi resource operation | Platform Admin/School Manager/Teacher/Parent; identity refs; core audit | Authorization matrix: allow only scoped role grants; verify revoke and metadata audit across reads/tokens/jobs. AC-46/64. | P0 platform foundation | DRAFT; chưa sign-off |
| FR-PL-02 | M | Q149; BR-49 | §31.3, tenant boundary | be1.organizations; all school-owned lesson/feedback/quota entities | Cross-organization negative checks disclose neither resource existence nor content. AC-46/57/63. | P0 platform foundation | DRAFT; chưa sign-off |
| FR-PL-03 | M | Q152/Q189; BR-50 | §31.2, reuse/remix | lesson.library_items/library_versions; lesson.occurrences; lesson.version_activities | Pin version per use; AI edit request yields draft/personal copy with lineage and leaves source/old occurrence unchanged. AC-47/59. | P0 platform foundation | DRAFT; exact Parent editable fields open |
| FR-PL-04 | M | Q155/Q171/Q174/Q177; BR-51 | §31.2, discovery and use | lesson.library_items/library_versions/access_grants | Public search returns only published PUBLIC; authorized school/group/invite scopes work; denied scopes reveal no content. AC-48/59/63. | P0 platform foundation | DRAFT; chưa sign-off |
| FR-PL-05 | M | Q160–Q163/Q172/Q175; BR-51 | §31.2, publication/moderation | lesson.access_grants; lesson.library_versions | Manager approval gates Teacher PUBLIC; SCHOOL-only remains tenant-scoped; Admin hide/unpublish revokes library access but preserves history. AC-48/60. | P0 platform foundation | DRAFT; Admin-authored review policy open |
| FR-PL-06 | M | Q162/Q163/Q170/Q176; BR-58 | §31.2–31.3, lesson audience | lesson.access_grants; be1.parent_groups/parent_group_members | Group and named invitation grants are limited to accepted members and stop after revocation. AC-46/57/63. | P0 platform foundation | DRAFT; chưa sign-off |
| FR-PL-07 | M | Q150/Q176; BR-48 | §31.3, profile share lifecycle | parent.profile_share_grants; parent.child_profiles; be1.managed_profiles | Pending invitation grants no access; accepted scope works; Parent retains ownership and can revoke. AC-49/57. | P0 platform foundation | DRAFT; exact field list open |
| FR-PL-08 | M | Q150/Q151/Q176; NFR-34/36 | §31.3, least-privilege share | parent.profile_share_grants; profile revisions; API/token/job authorization | Verify only granted fields resolve; revoke blocks new reads, downloads, tokens, caches and not-yet-accepted jobs. AC-49/57/64. | P0 platform foundation | DRAFT; expiry policy open |
| FR-PL-09 | M | Q157/Q158/Q164; BR-52 | §31.4, Teacher authoring | lesson.source_documents/document_revisions; structured lesson form | Template contract covers topic, age, objectives, drawing, knowledge, activities/materials/steps/safety and optional script. AC-50. | P0 platform foundation | DRAFT; format review pending |
| FR-PL-10 | M | Q157/Q164/Q165; NFR-35 | §31.4, upload filter | lesson.source_documents; core asset hash/lineage; parser/filter version | Verify raw file/full text/images/metadata do not reach model input or telemetry; only allowlisted fields proceed. AC-50. | P0 platform foundation | DRAFT; parser/AV implementation gate |
| FR-PL-11 | M | Q157/Q164; BR-52 | §31.4, human extraction review | lesson.document_revisions; structured draft | Teacher preview/correction is required before AI request; parser uncertainty returns a repairable result. AC-50. | P0 platform foundation | DRAFT; chưa sign-off |
| FR-PL-12 | M | Q158/Q159; BR-53 | §31.4, AI draft boundary | lesson.library_versions; ai_jobs.job; access/review state | Confirm every AI output is DRAFT and cannot publish/show without authorized human review. AC-51. | P0 platform foundation | DRAFT; initiating roles open |
| FR-PL-13 | M | Q155/Q156; BR-50 | §31.2, lesson content | lesson.library_versions/version_activities | Validate drawing guidance, subject knowledge and multiple activity records with material/instruction/note fields. AC-47/52. | P0 platform foundation | DRAFT; chưa sign-off |
| FR-PL-14 | M | Q158/Q169; NFR-37 | §31.2/31.4, visuals/slides | lesson.version_visual_assets; core.asset_lineage; ai_jobs.job | Generated activity/topic visuals and slide assets are versioned derived outputs with safety/review/provenance; source lesson and child artwork are not replaced. AC-51/65. | P0 platform foundation | DRAFT; provider/ownership open |
| FR-PL-15 | M | Q167; BR-54 | §31.5, active-session option | lesson.sketch_deck_revisions/steps; ai_jobs.job; Parent temporary asset | Toggle on may create guide; toggle off creates no job, asset or quota event. AC-44/45/53. | P0 platform foundation | DRAFT; model/license/cost open |
| FR-PL-16 | M | Q151 + B2 Q1=A; BR-55 | §5.1/31.5, Parent sequence | story.runs/run_inputs; lesson.version_activities; video generation/playback | Walk through draw, optional active-session guide, capture, existing video/safety pipeline, then activity list. AC-52. | P0 platform foundation | DRAFT; preserves existing pipeline |
| FR-PL-17 | M | Q168/Q186/Q189/Q191; BR-56 | §31.2/31.5, optional script direction | lesson.library_versions; story revisions/review decisions | Follow direction only when enabled; adult can request draft edits; every output remains a new child-specific video. AC-54/59/65. | P0 platform foundation | DRAFT; default/deviation open |
| FR-PL-18 | M | Q184–Q187/Q191; BR-56 | §31.5, personalized video | story.run_inputs; story.video_generations/scenes; core asset lineage | Assert source drawing/profile belong to the selected child and each generation is new; reject cross-child video reuse. AC-54/56/65. | P0 platform foundation | DRAFT; current pipeline preserved |
| FR-PL-19 | M | Q190; BR-56 | §31.5, subject correction | story.understanding_revisions; story.review_decisions; ai_jobs.job | Wrong subject requires adult confirm/correct; new suggestion pins corrected revision and original image hash. AC-55. | P0 platform foundation | DRAFT; chưa sign-off |
| FR-PL-20 | M | Q185; BR-10/56 | §5.2/31.5, Teacher sample | lesson.occurrences; lesson.delivery_recipients; story.runs | Select one eligible child randomly, pin one approved activity and enforce one successful sample per occurrence. AC-56. | P0 platform foundation | DRAFT; eligibility/consent open |
| FR-PL-21 | M | Q178/Q179/Q183; BR-58 | §31.6, Parent history | lesson.delivery_recipients; parent.profile_share_grants | Parent sees only linked child deliveries within configured 30/60-day window and active share scope. AC-57/60. | P0 platform foundation | DRAFT; exact window open |
| FR-PL-22 | M | Q180–Q182; BR-59 | §31.6, feedback | lesson.delivery_feedback/feedback_replies; organization ref | Parent submits lesson feedback; Teacher/Manager/Admin replies remain in school scope; no chat, completion mark or image attachment. AC-58. | P0 platform foundation | DRAFT; chưa sign-off |
| FR-PL-23 | M | Q162/Q170; BR-58 | §31.2–31.3, groups and recipients | be1.parent_groups/parent_group_members; lesson.access_grants | Group and named-recipient access are invite-based, membership-checked and revocable. AC-46/57/63. | P0 platform foundation | DRAFT; membership invitation policy open |
| FR-PL-24 | M | Q193; BR-60 | §31.7, product quota | billing.video_quota_grants/video_quota_usage; ai_policy.resource_reservation | Exercise school, Teacher and Parent scope attribution; Manager school allocation/purchase; Parent package/top-up; keep compute separate. AC-61. | P0 platform foundation | DRAFT; package/charge order open |
| FR-PL-25 | M | Q153/Q154; BR-57 | §31.1/31.8, age/personalization | parent.profile_revisions; be1.profile_revisions; age-band catalog | Accept 36 and 120 months, reject outside scope under transition policy and resolve versioned age-band personalization. AC-62/65. | P0 platform foundation | DRAFT; band boundaries open |

<a id="srs-30-4"></a>
### 30.4 Ma trận truy vết BR theo từng ID

BR là quy tắc nghiệp vụ; nguồn owner cụ thể được phân cụm tại §16. Requirement/UC/entity/acceptance dưới đây nối từng BR tới implementation surface và phương pháp xác minh. BR-36 là control đề xuất về an toàn, không phải phê duyệt pháp lý.

| BR | Nguồn quyết định | FR/NFR liên quan | UC | Entity/owner đích | Acceptance/verification |
|---|---|---|---|---|---|
| BR-01 | Owner decisions về single-child, Q71–Q86 | FR-C-02; FR-T-10; FR-AI-05 | UC-02/05 | story.runs; ai_jobs.job.target_ref; parent/be1 profiles | AC-02/03 |
| BR-02 | Owner decision one-active-run/adult | FR-C-03/08; FR-O-10 | UC-02/05/11 | story.runs; ai_jobs.jobs | AC-02/22 |
| BR-03 | Q01/Q03/Q20 account scope and auth | FR-C-01/04; FR-O-09 | UC-01/13 | identity scope refs; parent.child_profiles; be1 identity | AC-01 |
| BR-04 | Q87–Q96/Q105 billing class slots | FR-T-02/03; FR-B-01/04 | UC-06/08 | be1.classrooms; billing.capacity_periods/subscriptions | AC-14 |
| BR-05 | Q05/Q41/Q44/Q73/Q74 organization/class | FR-T-02/05/14 | UC-03/06/12 | be1.classrooms/enrollments/organization_assignments | AC-03/25 |
| BR-06 | Q13/Q42/Q43/Q74/Q130 access transfer | FR-T-14/16; FR-C-08 | UC-05/12 | be1.organization_assignments; story.runs; lesson projection records | AC-18/25; AT-04 |
| BR-07 | Q03/Q44/Q73/Q82 profile entry | FR-T-04/05; FR-C-05 | UC-03 | be1.managed_profiles/profile_revisions | AC-16 |
| BR-08 | Q08/Q32/Q85: historical catalog eligibility; Q151 + B2 Q1=A: Parent post-video ordering | FR-P-05; FR-T-09 | UC-02/05/14; §31.5 \| learning_content.record/version; lesson.plan_activities/version_activities; Parent lesson linkage (tham chiếu lesson-version opaque tùy chọn qua cổng module Lesson; không gắn org/class/occurrence của Teacher) [Còn mở cho thiết kế vật lý: vị trí lưu vật lý tham chiếu lesson-version]. | AC-05 |
| BR-09 | Q09/Q47/Q48/Q52/Q53 lesson per occurrence | FR-T-06–08 | UC-04/05 | lesson.occurrences/source_documents/document_revisions/plan_revisions | AC-16 |
| BR-10 | Q71–Q80/Q83/Q103/Q127 sample-slot semantics | FR-T-13; FR-AI-09 | UC-05/16 | lesson.occurrences; story.video_generations | AC-04; AT-01 |
| BR-11 | Q110/Q113/Q119/Q128 quota unit/no-refund | FR-B-10/11; FR-AI-07 | UC-10/16 | billing.video_quota_grants/video_quota_usage | AC-17/23; AT-02 |
| BR-12 | Q80/Q91/Q95 one sample per occurrence | FR-T-13/15 | UC-05 | lesson.occurrences; story.video_generations | AC-04 |
| BR-13 | Q33/Q35/Q75/Q76/Q102 story rewrite | FR-P-07; FR-T-12; FR-AI-07 | UC-02/05/16 | story.story_revisions/review_decisions | AC-06 |
| BR-14 | Q60/Q75 script revision approval | FR-P-08; FR-T-12; FR-AI-02 | UC-02/05 | story.story_revisions/review_decisions | AC-06/08 |
| BR-15 | Q75/Q83 script-only approval gate | FR-P-08; FR-T-12/16 | UC-02/05 | story.review_decisions; video_generations | AC-07/08 |
| BR-16 | Q116 rejection/hide behavior | FR-P-09; FR-T-12/15; FR-AI-09 | UC-02/05/16 | story.video_generations/review_decisions | AC-07; AT-01 |
| BR-17 | Q18/Q63/Q78 scene retry | FR-AI-06; FR-T-13 | UC-05/16 | ai_jobs.attempts; story.video_generation_scenes | AC-04 |
| BR-18 | Q21/Q22 age/name minimization | FR-C-05; FR-P-06; FR-T-10 | UC-01/05 | parent/be1 profile revisions/context snapshots | AC-08 |
| BR-19 | Q26–Q30/Q77 profile context sources | FR-C-05/06; FR-P-06 | UC-01/02/03/05 | profile_context_entries; story.run_inputs bounded snapshot | AC-08 |
| BR-20 | Q23–Q25 support-needs boundary | FR-C-07; FR-AI-12 | UC-01/02/05 | parent/be1.profile_support_needs; snapshot exclusion rule | AC-21 |
| BR-21 | Q29/Q30/Q70 approved immutable snapshot | FR-C-05/06; FR-P-06; FR-T-10 | UC-01/02/05 | profile_revisions/story.run_inputs snapshot/hash | AC-08 |
| BR-22 | Q04/Q10/Q51/Q52 lesson format/limits | FR-T-06/07 | UC-04 | lesson.source_documents/document_revisions; core.asset_metadata | AC-16 |
| BR-23 | Q11/Q12/Q54–Q56 audio/transcript handling | FR-P-03; FR-AI-01/03 | UC-02/05 | story.run_inputs/transcript_revisions; core.asset_metadata | AC-08 |
| BR-24 | Q16/Q17/Q57/Q58/Q62 video format/voice/subtitle | FR-AI-04/08; FR-P-08 | UC-02/05 | story.video_generations/scenes; ai_jobs.result_assets | AC-06/07 |
| BR-25 | Q65 playback token/no export | FR-P-08; FR-AI-09/10 | UC-02/05 | story.video_generations; playback authorization | AC-07/18 |
| BR-26 | Q37–Q39/Q66/Q86/Q119/Q123/Q127 deletion | FR-C-08/10; FR-O-03 | UC-07/09/11 | be1.data_lifecycle_requests; core.asset_metadata/lineage; story.runs; billing.video_quota_usage | AC-13/23; AT-02 |
| BR-27 | Q06/Q27 synthetic-only until review | FR-C-10; FR-O-04 | UC-01–UC-16 | data_origin/authorization refs; provider-copy registry nguồn legacy/read-only; synthetic Modal scratch theo ai_jobs.attempt | AC-13 |
| BR-28 | Q89/Q93 MoMo/VNPAY VND scope | FR-B-01/02/03 | UC-08/10 | billing.price_versions/invoices/payment_attempts/provider_event_receipts | AC-14 |
| BR-29 | Q99 proration | FR-B-04 | UC-06/08 | billing.capacity_periods/invoices/subscription_events | AC-14 |
| BR-30 | Q100/Q101 renewal cancellation | FR-B-05 | UC-08 | billing.organization_subscriptions/subscription_events | AC-14 |
| BR-31 | Q90/Q94 grace window | FR-B-06 | UC-08 | billing.organization_subscriptions/subscription_events | AC-14 |
| BR-32 | Q98 capacity downgrade class selection | FR-B-07 | UC-06/08 | billing.subscription_events; be1.classrooms | AC-14 |
| BR-33 | Q97 billing notice schedule | FR-B-08/09/14 | UC-08/15 | notifications.inbox_items/delivery_attempts/push_endpoints | AC-26 |
| BR-34 | Q67 audit metadata-only | FR-C-08; FR-O-05/07 | UC-07/09/11/12 | core.audit_events; telemetry pipeline | AC-12/27 |
| BR-35 | Q04/Q86 profile lifecycle delete | FR-C-10; FR-C-08 | UC-09 | parent.child_profiles; be1.managed_profiles/data_lifecycle_requests | AC-13 |
| BR-36 | Safety policy derived from child-targeted use; not legal sign-off | FR-AI-12; NFR-23 | UC-02/05/14/16 | learning_content; story; policy versions; ai_jobs | AC-21 |
| BR-37 | Q111 class projection confirmation | FR-T-16 | UC-05 | lesson.occurrences/projection confirmation; playback authorization | AC-18 |
| BR-38 | Q110–Q126/Q128/Q132 quota ownership and lifecycle | FR-B-10–13; FR-AI-07 | UC-10/16 | billing.video_quota_grants/video_quota_usage; ai_policy.resource_reservation for compute only | AC-17/23/24; AT-06/08/09 |
| BR-39 | Q122/Q129/Q133/Q136 wait closeout and verified email reminder | FR-C-11; FR-T-15; FR-B-14 | UC-02/05/11/15 | story.runs; notifications.inbox_items/delivery_attempts/push_endpoints | AC-22/30; AT-03/11 |
| BR-40 | Q123/Q128/Q133/Q134: hủy run và idle closeout | FR-C-08/11; FR-T-15/17; FR-O-10 | UC-11/12 | story.runs; be1.data_lifecycle_requests; ai_jobs.job; core.asset_metadata; billing.video_quota_usage; lesson.occurrences | AC-22/23/31; AT-02/03/11/12 |
| BR-41 | Q134: emergency force-close, metadata-only | FR-C-03; FR-T-14/17 | UC-12 | be1.organization_assignments; story.runs; core.audit_events; billing.video_quota_usage; lesson.occurrences | AC-25/31; AT-12 |
| BR-42 | Q137/Q141/Q146: Teacher Deck chỉ dành cho Teacher; câu Q137/Q141/Q146 ban đầu xem đây là bước chính, nhưng Q167 cập nhật thành opt-in trong session. Parent có AI guide riêng, không preselect subject của tranh trẻ và chỉ review subject sau capture | FR-P-02/04/11; FR-T-18; FR-AI-14/15 | UC-02/17 | story.understanding_revisions; lesson.sketch_deck_revisions/steps; ai_jobs.job target kind/ref | AC-33/44/45; AT-14/15/18/19 |
| BR-43 | Q138–Q140/Q142: deck chung toàn occurrence, line-sketch theo bước và điều khiển trình chiếu nền trắng | FR-T-18–20; FR-AI-14; NFR-33 | UC-17 | lesson.occurrences/plan_revisions/plan_activities/sketch_deck_revisions/sketch_deck_steps; core.asset_metadata/lineage | AC-34/35; AT-15/16 |
| BR-44 | Q143/Q146: giới hạn compute/rate cho cả Teacher Deck và Parent Guide, tách biệt video quota | FR-T-20; FR-AI-14/15; NFR-25 | UC-02/16/17 | ai_policy.resource_reservation/resource_event; lesson.sketch_deck_revisions; Parent temporary Core Asset; không ghi billing.video_quota_usage | AC-35/45; AT-16/19 |
| BR-45 | Q144: pipeline VLM → story/storyboard → Character Bible → LTX → consistency → FFmpeg/TTS → safety → playback đã được chủ sở hữu chỉ định | FR-AI-01/04–09/13; NFR-19/23/25 | UC-02/05/16 | story.understanding_revisions/story_revisions/story_scenes/video_generations/video_generation_scenes; ai_jobs; core.asset_metadata/lineage | AC-36/37; AT-17 |
| BR-46 | Q146 (supersedes text-only Q145): Parent có thể yêu cầu hoặc bỏ qua AI line-sketch guide 3–5 bước cho topic chung; input không có dữ liệu trẻ; guide riêng tư/tạm thời, có provenance/cleanup và sketch-only resource cap; lỗi không chặn vẽ/capture, subject review vẫn sau capture. | FR-P-11; FR-AI-15 | UC-02/16 | ai_jobs.job; core_asset_metadata/asset_lineage; ai_policy.resource_reservation/resource_event; không ghi billing.video_quota_usage | AC-44/45; AT-18/19 |

| BR-47 | Q147; additive platform layer preserves the existing Parent/Teacher flows and video pipeline | FR-PL-16/18; NFR-34/38 | §31.1/31.5 | Parent/Teacher run and video owners; lesson delivery | AC-52/54/56 |
| BR-48 | Q148/Q150/Q151/Q176; separate accounts with invited, consented, scoped and revocable child-profile grant | FR-PL-07/08; NFR-34/36 | §31.3 | parent.profile_share_grants; Parent and Teacher profile owners | AC-46/49/57/64 |
| BR-49 | Q149; one school per organization and no cross-tenant disclosure | FR-PL-02/23; NFR-34/36 | §31.3 | be1.organizations; lesson.access_grants; feedback/quota scope | AC-46/57/63 |
| BR-50 | Q152/Q155/Q156/Q189; reusable immutable version differs from occurrence; AI reuse edits create draft/copy | FR-PL-03/13; NFR-37 | §31.2 | lesson.library_items/library_versions/version_activities; occurrences | AC-47/52/59 |
| BR-51 | Q155/Q160–Q163/Q171–Q175; visibility and Manager gate before Teacher PUBLIC; Admin moderation; preserve on unpublish | FR-PL-04/05/06; NFR-34/37 | §31.2/31.3 | lesson.library_versions/access_grants; school tenant | AC-48/60/63 |
| BR-52 | Q157/Q164/Q165; filter uploads to reviewed allowlisted fields before AI | FR-PL-09/10/11; NFR-35 | §31.4 | lesson.source_documents/document_revisions; parser/filter; ai_jobs | AC-50 |
| BR-53 | Q158/Q159; AI-authored lesson/activity/visual remains a draft until authorized review | FR-PL-12/14; NFR-35/37 | §31.4 | lesson.library_versions/version_visual_assets; ai_jobs.job | AC-51 |
| BR-54 | Q167; Parent and Teacher line-sketch is created only after adult enables it in-session | FR-PL-15; NFR-34 | §31.5 | lesson.sketch_deck_revisions/steps; Parent temporary guide asset; ai_jobs.job | AC-44/45/53 |
| BR-55 | Q151 + B2 Q1=A; Parent activities are presented after video, never selected as video precondition | FR-PL-16 | §5.1/31.5 | story.video_generations; lesson.version_activities | AC-52 |
| BR-56 | Q168/Q184–Q191; each video is new for the child drawing; script direction is optional; adult confirms subject mismatch | FR-PL-17/18/19; NFR-37/38 | §31.5 | story.run_inputs/understanding_revisions/video_generations; lesson.library_versions | AC-54/55/65 |
| BR-57 | Q153/Q154; age scope is 36–120 months with versioned but not yet fixed bands | FR-PL-25; NFR-38 | §31.1 | Parent/Teacher profile revisions; age-band catalog | AC-62/65 |
| BR-58 | Q162/Q170; lesson grants can target Parent groups or named invitees and can be revoked | FR-PL-06/23; NFR-34 | §31.2/31.3 | be1.parent_groups/parent_group_members; lesson.access_grants | AC-46/57/63 |
| BR-59 | Q178–Q182; Parent feedback has no chat/media upload and stays within the school thread | FR-PL-21/22; NFR-34/36 | §31.6 | lesson.delivery_recipients/delivery_feedback/feedback_replies | AC-57/58 |
| BR-60 | Q193; Billing owns school/Teacher/Parent quota while AI Policy owns compute reservation | FR-PL-24; NFR-34 | §31.7 | billing.video_quota_grants/video_quota_usage; ai_policy.resource_reservation | AC-61 |Phương pháp verify trong hai ma trận là kế hoạch; không có product test/build/database inspection nào được chạy trong vòng sửa tài liệu này. AC-01–AC-45 được viết theo Given/When/Then ở §13; AT-01–AT-19 là các kịch bản edge bổ sung. Sơ đồ context, conceptual/logical ERD, state, sequence và diagram vận hành vẫn chờ owner duyệt cả hai Markdown baselines.

<a id="srs-31"></a>
## 31. Nền tảng giáo án, chia sẻ và tích hợp luồng hiện hữu

### 31.1 Thứ tự ưu tiên và phạm vi thay đổi

Đây là lớp nền tảng bổ sung lên hệ thống Sketch2Life hiện có. Các luồng Parent Android, Teacher web, luồng chụp tranh, pipeline story/video, quota hiện hành, cơ chế safety, lifecycle và vận hành đã ghi ở §1–§30 tiếp tục áp dụng trừ các điểm được liệt kê rõ dưới đây. Không thay thế toàn bộ SRS hoặc xóa history.

Phần này là nguồn chuẩn v2.3 cho các điểm đã thay đổi: age scope 36–120 tháng thay cho 36–155 tháng; Teacher Sketch Deck và Parent Guide đều opt-in theo session; reusable lesson tách với occurrence; Parent hiển thị outdoor activities sau video; Parent/Teacher profile vẫn tách owner nhưng có grant chia sẻ; và hệ thống có role Platform Admin/School Manager. Các câu/ma trận v2.2 mâu thuẫn với các điểm này được xem là history và nhường cho yêu cầu có ID tại §31.8–§31.11.

Không có quyết định công nghệ/provider mới ở phần này. Presenton, FLUX.3 và các công cụ khác chỉ là ứng viên; không khóa model, host, chi phí, giá bán hoặc schema triển khai. Toàn bộ phần này vẫn là draft; plan Rev25 chỉ duyệt sửa tài liệu, không duyệt product code hay migration.

### 31.2 Mô hình lesson reusable và occurrence

Lesson library là nguồn nội dung có version, có thể chứa:

- Chủ đề, mục tiêu học tập, nhóm tuổi mục tiêu và ghi chú Montessori.
- Hướng dẫn trẻ vẽ chủ thể, các nét chính/đặc điểm cần quan sát và thông tin giúp trẻ hiểu con vật/đồ vật/chủ đề đó.
- Một hoặc nhiều outdoor activities; mỗi mục nêu vật liệu, cách chuẩn bị, các bước thực hiện, mục tiêu quan sát và lưu ý an toàn.
- Video script direction có thể bật/tắt theo lesson hoặc lần dùng; khi bật, script là hướng dẫn nội dung, không buộc video hai trẻ giống hệt.
- Nội dung canonical của lesson là chữ có cấu trúc. Visual assets/slide do AI tạo là lựa chọn riêng, có version, provenance và review; chúng minh họa lesson/activity hoặc session, không thay thế văn bản nguồn và không bao giờ thay ảnh tranh trẻ dùng cho video.

Reusable lesson version độc lập với lesson occurrence của một lớp/buổi. Teacher hoặc Parent dùng lesson như preset; occurrence/story run pin đúng lesson version. Người lớn có thể yêu cầu AI đề xuất chỉnh sửa khi dùng lại lesson; kết quả là draft hoặc personal copy có lineage và cần người lớn review. Mọi chỉnh sửa tạo version mới hoặc personal copy; không sửa ngược version đã publish hay làm thay đổi occurrence cũ.

Visibility của lesson là PRIVATE, SCHOOL, SELECTED_AUDIENCE hoặc PUBLIC. Teacher lesson mặc định thuộc trường. SCHOOL chỉ xem trong organization sở hữu; SELECTED_AUDIENCE cấp quyền cho nhóm Parent hoặc người được mời; PUBLIC có thể tìm kiếm và dùng trên toàn nền tảng. Teacher lesson chỉ chuyển PUBLIC sau khi School Manager duyệt. Platform Admin có thể duyệt/hide/disable nội dung theo quyền nền tảng. Lesson public có thể được dùng và remix; remix luôn tạo item/version nguồn mới có provenance đến lesson gốc. Khi unpublish/revoke, giữ nội dung và lịch sử đã dùng nhưng thu hồi quyền truy cập thư viện. Lesson content chỉ mở lại sau khi public lại hoặc cấp grant mới.

Khi một lesson đã được dùng rồi bị unpublish, giữ lesson version, occurrence và lịch sử sử dụng. Bỏ quyền tìm/tải/mở lesson content từ library; Parent chỉ truy cập lại lesson content khi lesson được public lại hoặc được chia sẻ lại bằng grant hợp lệ. Lịch sử delivery không tự khôi phục quyền thư viện.

### 31.3 Roles, tenant và profile sharing

| Role | Phạm vi |
|---|---|
| Platform Admin | Toàn nền tảng; cấu hình policy/role/quota, tạo nội dung public, moderation/hide, xem và trả lời feedback thuộc trường theo audit. Có thể xem child media theo quyền nền tảng do chủ sở hữu xác nhận; mọi truy cập cần reason code và audit. |
| School Manager | Một organization tương ứng một trường; quản lý Teacher/Parent groups và quota school, duyệt Teacher content trước PUBLIC, xem/duyệt lesson và feedback trong trường. Không mặc nhiên có quyền xem ảnh/video trẻ. |
| Teacher | Lớp/profile được phân công trong trường; tạo/sửa lesson; dùng lesson preset; nhập lesson qua template/form; bật/tắt sketch trong session; tạo video mẫu cho một child/run. |
| Parent | Tài khoản Parent riêng; sở hữu child profile; có thể cấp/revoke profile share; dùng lesson PUBLIC/được cấp; xem lesson đã dạy theo profile share; tạo video mới cho con; gửi lesson feedback. |

Mỗi trường là một organization/tenant. Organization boundary bắt buộc cho lesson SCHOOL, SELECTED, occurrence, Parent groups, feedback, quota và audit. Admin toàn nền tảng có thể moderate nhưng vai trò Manager/Teacher/Parent không vượt tenant.

Parent và Teacher không dùng chung account và không chuyển quyền sở hữu profile. Parent mời Teacher phụ trách hoặc trường qua invitation. Sau khi Parent chấp thuận, profile share grant ghi inviter, recipient/organization/class, child profile opaque ref, purpose, field scope, status, created/expiry/revoked timestamps và actor. Grant có thể thu hồi; revoke có hiệu lực tức thì với lần đọc mới, token/cache/API và các lần gọi AI chưa accepted. Story run đã accepted giữ input snapshot đã được người lớn duyệt theo lifecycle hiện có. Chia sẻ chỉ mở các field được cho phép; mặc định loại tên pháp lý, support-needs, ảnh/tranh, voice và lịch sử không liên quan. Bộ field chính xác còn mở.

| Resource/action | Parent | Teacher | School Manager | Platform Admin |
|---|---|---|---|---|
| Profile | Owner; tạo/revoke share grant | Chỉ field được grant và lớp được phân công | Không đọc profile contents mặc định | Có quyền nền tảng; child-media/profile access phải audit |
| School lesson | Dùng khi school/group/invite grant active | Tạo/sửa lesson của trường | Xem/feedback; approve Teacher public publication | Moderation/hide, platform-wide |
| Public lesson | Tìm/dùng/download theo capability | Dùng/remix hoặc tạo own version | Duyệt Teacher publication | Tạo/publish/moderate |
| Occurrence and child media | Chỉ child/run của mình | Chỉ assigned child/run, grant còn hiệu lực | Không media mặc định | Có thể xem theo platform permission, reason và audit |
| Lesson feedback | Tạo và xem thread của mình | Xem/reply nếu thuộc occurrence/lớp được giao | Xem/reply trong school tenant | Xem/reply; output chỉ thuộc school thread |
| Quota | Xem/mua Parent scope | Dùng Teacher/school scope theo package | Mua/allocate school quota | Quản lý platform policy/quota |

Permission checks chạy server-side cho mọi resource operation. Mất assignment, revoke share, unpublish/hide hoặc rời organization phải invalidate grant/cache/download/playback capability liên quan; không suy quyền từ UI role claim.

### 31.4 Authoring, upload filtering và AI assistance

Teacher authoring có structured form và standardized lesson-document template. Template nêu rõ topic, age band, objectives, drawing steps, subject knowledge, activities, materials, instructions, safety notes và optional script direction. Giữ giới hạn upload v2.2 (PDF/PPTX/DOCX tối đa 25 MB/100 trang, không OCR scan, từ chối file encrypted/password-protected) cho tới khi có quyết định mới.

Upload đi qua quarantine/AV, parser và deterministic field mapper. Raw file gốc cùng hash/provenance được giữ riêng tư trong organization. Chỉ các field allowlist đã parse, validate, Teacher preview và Teacher sửa/xác nhận mới có thể tạo structured input cho AI. Không gửi nguyên giáo án, full extracted text, embedded image, metadata cá nhân hay file gốc sang AI. Parser/filter/validation chưa đạt thì dừng và trả lỗi có thể sửa; không âm thầm gửi raw document.

AI hỗ trợ tạo lesson/activity/plan chỉ tạo draft; một người có quyền phải kiểm tra, sửa và publish. Có thể dùng AI để bổ sung outdoor activity khi catalog chưa đủ; mỗi đề xuất phải kèm mục tiêu, vật liệu, chuẩn bị, hướng dẫn từng bước và safety notes. Visual/slide generation là job riêng, optional, có review/provenance/safety. Parent không khởi tạo lesson/activity suggestions mới theo chủ đề trong baseline; quyền role cụ thể của Teacher/Admin cho loại suggestion này đang chờ làm rõ vì Q157/Q159. Phân biệt với việc reuse lesson đã có: Parent/Teacher có thể yêu cầu AI đề xuất chỉnh sửa cho draft/personal copy theo FR-PL-03; không sửa source version.

### 31.5 Luồng Parent, Teacher và video sau khi thêm platform

Parent: chọn lesson được phép hoặc bắt đầu theo flow hiện có → trẻ bắt đầu vẽ → trong lúc vẽ, người lớn có thể bật line-sketch guide hoặc bỏ qua → vẽ xong thì chụp ảnh tranh → VLM đề xuất chủ thể → người lớn xác nhận hoặc sửa subject → duyệt profile context tối thiểu và script nếu dùng lesson direction → chạy pipeline video hiện hành từ tranh trẻ → video qua technical/safety gates và playback private → hiển thị một hoặc nhiều outdoor activities đã định nghĩa trong lesson.

Các hoạt động không được yêu cầu chọn trước khi video tạo. Activity list có materials/instructions/notes; activity catalog bổ sung do AI gợi ý cần human review. Parent có thể dùng lesson public hoặc lesson được share; chỉnh sửa chỉ áp dụng cho bản cá nhân, không ghi lên nguồn chung.

Teacher giữ flow occurrence/video sample hiện tại. Teacher có thể tạo occurrence từ lesson preset hoặc plan tự tạo. Khi đang dạy, line-sketch chỉ được tạo nếu Teacher bật; disabled nghĩa là không enqueue job, không tính quota sketch. Một trẻ đại diện được chọn ngẫu nhiên từ roster đủ điều kiện và Teacher kiểm tra selection; cơ chế chọn và consent cụ thể là open item. Mỗi occurrence tối đa một sample video thành công như baseline.

Mọi video là generation mới từ ảnh tranh của đúng trẻ và profile context đã duyệt. Không tái sử dụng video của trẻ khác hoặc cache video dùng chung làm kết quả cá nhân. Lesson script có thể bật/tắt; nếu bật, story/video đi theo hướng đó nhưng hình ảnh/clip được sinh mới, cho phép khác biệt theo tranh/profile. Nếu VLM nhận sai subject, hệ thống yêu cầu người lớn xác nhận trước khi sửa subject và yêu cầu gợi ý lại. Các bước VLM → structured story → storyboard → adult script review → Character Bible/reference → LTX-2.5/Modal per scene → consistency → FFmpeg/TTS/subtitles → output safety → private playback không thay đổi.

### 31.6 Parent lesson history và feedback

Parent được mời/link profile có thể xem lesson/occurrence đã dạy cho trẻ và lesson public/được share, trong một khoảng lịch sử 30 hoặc 60 ngày đang mở. Parent có thể xem chi tiết theo quyền và tải lesson content được phép; video trẻ vẫn theo quy tắc playback hiện tại, không mở download/export. Nếu source lesson đã unpublish, occurrence/history metadata vẫn giữ nhưng lesson content chỉ mở lại khi public lại hoặc grant được cấp lại.

Parent có thể gửi feedback gắn với lesson version/delivery và nhận phản hồi từ Teacher, School Manager hoặc Platform Admin. Feedback scope giới hạn trong organization liên quan; organization khác không được thấy. Đây là feedback thread phục vụ trao đổi về lesson, không phải chat tổng quát. Không thêm đánh dấu hoàn thành/checklist, tải ảnh tranh lên feedback hay gửi media trẻ kèm phản hồi. School Manager/Admin có thể xem feedback và trả lời; phản hồi platform admin vẫn chỉ hiển thị trong trường đó.

### 31.7 Quota và billing platform

Nền tảng chi trả chi phí provider. Billing giữ các quota grant/usage theo scope tách biệt: school organization, Teacher account và Parent account. School Manager có thể mua quota hoặc đặt allocation cho trường; Parent có subscription/quota riêng và có thể mua top-up. Gói/giá/số lượng chưa chốt.

Video generation của Teacher sample dùng quota school/Teacher theo policy; Parent tạo video mới cho child dùng Parent quota. AI Policy tiếp tục theo dõi compute/cost reservation, không thay thế Billing product quota. Quota sketch, image/slide generation và các job authoring có accounting/rate limit riêng theo policy. Thứ tự charge/fallback giữa các pool, phần quota Teacher thuộc school hay tài khoản riêng và cách xử lý hết quota là open item.

### 31.8 Yêu cầu chức năng mới (FR-PL)

| ID | Ưu tiên | Yêu cầu |
|---|---|---|
| FR-PL-01 | M | Cung cấp platform Admin, School Manager, Teacher và Parent với permission có scope, server-side authorization, audit và revoke. |
| FR-PL-02 | M | Mỗi trường là một organization/tenant; mọi record của trường có tenant scope và không thể đọc chéo organization. |
| FR-PL-03 | M | Tách reusable lesson item/version khỏi occurrence; version được pin vào lần dạy/lần dùng. Teacher/Parent có thể yêu cầu AI đề xuất chỉnh sửa khi dùng lại lesson; output phải là draft/personal copy có lineage và không sửa source version. |
| FR-PL-04 | M | Hỗ trợ visibility PRIVATE, SCHOOL, SELECTED_AUDIENCE và PUBLIC; hỗ trợ tìm lesson PUBLIC và download nội dung lesson được cấp quyền. |
| FR-PL-05 | M | Teacher lesson chỉ được PUBLIC sau Manager approval; Admin có quyền moderation/hide; unpublish không xóa version/historical usage nhưng revoke library access. |
| FR-PL-06 | M | Cho phép share lesson cho nhóm Parent hoặc người được chỉ định/invite; mọi grant có trạng thái/revoke và tôn trọng tenant boundary. |
| FR-PL-07 | M | Cho phép Parent mời và chia sẻ child profile với Teacher/trường qua consented, scoped, audited, revocable grant; account/profile owner vẫn tách biệt. |
| FR-PL-08 | M | Chỉ trả các profile fields được grant và policy cho phép; revoke ngăn mọi lần truy cập mới và ngăn job chưa accepted dùng grant cũ. |
| FR-PL-09 | M | Teacher có structured authoring form và standardized lesson upload template; giữ giới hạn file hiện hành đến quyết định mới. |
| FR-PL-10 | M | Parser/filter tạo structured allowlist; raw original, toàn văn giáo án, ảnh nhúng và metadata không được gửi model. |
| FR-PL-11 | M | Teacher preview/correct/confirm structured draft trước AI generation; sai template hoặc parse uncertainty trả lỗi và yêu cầu sửa. |
| FR-PL-12 | M | AI-assisted lesson/activity/plan content luôn là draft, cần người có quyền review/edit/publish; không tự public. |
| FR-PL-13 | M | Lesson version hỗ trợ drawing steps, subject-learning notes, age target, một hoặc nhiều activities với materials/instructions/notes và optional script direction. |
| FR-PL-14 | M | Bao gồm khả năng tạo visual activity/topic assets hoặc session slides theo lựa chọn; ghi provenance/version/safety và không chọn provider cố định. Việc tạo asset trong từng lesson/session là tùy chọn. |
| FR-PL-15 | M | Chỉ tạo Parent hoặc Teacher line-sketch khi người lớn bật trong session; disabled thì không có generation job. |
| FR-PL-16 | M | Giữ thứ tự Parent draw → capture → video pipeline → lesson activity list; không yêu cầu chọn outdoor activity trước video. |
| FR-PL-17 | M | Lesson script-following bật/tắt theo lesson/usage; nếu bật thì giữ story direction nhưng video vẫn generation mới theo child drawing/profile. |
| FR-PL-18 | M | Không tái sử dụng video giữa trẻ; mỗi video dùng ảnh tranh và profile context được duyệt của đúng child. |
| FR-PL-19 | M | Khi subject mismatch, yêu cầu adult confirm/correct trước khi re-suggest; không tự đổi chủ thể âm thầm. |
| FR-PL-20 | M | Teacher sample chọn một child đại diện ngẫu nhiên đủ điều kiện; giữ tối đa một successful sample mỗi occurrence. |
| FR-PL-21 | M | Parent xem lesson đã dạy cho child liên kết và lesson public/được share, theo history window có cấu hình; 30/60 ngày đang mở. |
| FR-PL-22 | M | Parent tải lesson được phép và gửi lesson feedback; Teacher/Manager/Admin có thể xem/reply trong phạm vi school; không có direct chat, completion toggle hoặc ảnh tranh trong feedback. |
| FR-PL-23 | M | School groups và named recipients được dùng làm audience cho lesson share; membership và grants có thể thu hồi. |
| FR-PL-24 | M | Billing hỗ trợ quota scopes school, Teacher và Parent; Manager có thể mua/allocate school quota; Parent có thể mua gói/top-up riêng. |
| FR-PL-25 | M | Giới hạn profile/run ở 36–120 tháng; cá nhân hóa theo tuổi chính xác và age-band versioned; nhóm tuổi cụ thể được cấu hình sau. |

### 31.8.1 Quy tắc nghiệp vụ platform bổ sung

| ID | Quy tắc nghiệp vụ |
|---|---|
| BR-47 | Nền tảng giáo án là phần bổ sung; các luồng Parent/Teacher và pipeline tạo video đã chốt tiếp tục áp dụng, trừ thay đổi được chủ sở hữu ghi rõ trong v2.3. |
| BR-48 | Parent/Teacher accounts và profile owners tách biệt; cross-role profile read chỉ qua invitation, consent, active scope grant và có thể revoke. |
| BR-49 | Một trường tương ứng một organization/tenant; lesson, feedback, quota và group membership không lộ chéo tenant. |
| BR-50 | Reusable lesson version khác occurrence; dùng/reuse/remix không sửa source version, occurrence cũ giữ version đã pin. AI-proposed edits tạo draft/personal copy có lineage và cần human review. |
| BR-51 | Visibility là PRIVATE/SCHOOL/SELECTED/PUBLIC; Teacher content cần School Manager approval trước PUBLIC; Admin có thể hide. |
| BR-52 | Original teacher lesson upload được giữ riêng; chỉ structured allowlist đã Teacher review được phép đi vào AI. |
| BR-53 | AI lesson/activity/visual outputs mặc định DRAFT; human review/publish bắt buộc trước khi public/show. |
| BR-54 | Parent và Teacher line-sketch chỉ chạy khi người lớn bật trong session; tắt thì không có AI job. |
| BR-55 | Parent flow đặt lesson activities sau khi video hoàn tất; activity selection không là điều kiện tạo video. |
| BR-56 | Video luôn mới theo tranh của đúng trẻ; không tái sử dụng video child khác. Lesson script-following là optional direction. |
| BR-57 | Child profile/run age range là 36–120 tháng; age bands bên trong range có version và boundary còn mở. |
| BR-58 | Lesson audience có thể là group Parent hoặc người cụ thể; mỗi audience membership/grant có thể thu hồi. |
| BR-59 | Parent gửi feedback gắn lesson delivery; Teacher/Manager/Admin phản hồi trong school scope; không mở direct chat hoặc media upload. |
| BR-60 | Billing sở hữu quota usage theo Parent/Teacher/school scope; AI Policy tiếp tục sở hữu compute reservation. Gói, allocation và charge order còn mở. |

### 31.9 Yêu cầu phi chức năng và acceptance bổ sung

| ID | Ưu tiên | Yêu cầu phi chức năng |
|---|---|---|
| NFR-34 | M | Authorization deny-by-default, tenant isolation và profile/lesson grant revocation phải áp dụng đồng nhất cho API, download, token, cache và job dispatch; thay đổi được audit metadata-only. |
| NFR-35 | M | Document filtering có thể truy vết source hash → parser/filter version → allowlisted field → Teacher correction → AI draft; raw original không lọt vào model request hoặc telemetry. |
| NFR-36 | M | Admin access vào child media, profile data và cross-role grant được giới hạn theo permission, reason code và audit; school feedback không lộ organization khác. |
| NFR-37 | M | Lesson version, generated visual, source file và remix giữ lineage; bản dẫn xuất không ghi đè source. |
| NFR-38 | M | Nội dung V1 tiếng Việt; mục tiêu trẻ 3–10 tuổi, Montessori-inspired, child-centered và người lớn là guide/observer/supporter. |

| AC | Given | When | Then |
|---|---|---|---|
| AC-46 | Có Parent, Teacher, Manager và Admin trong hai organization | Actor đọc lesson/profile/feedback/quota | Chỉ quyền được cấp trong tenant/resource scope mới thành công; mọi revoke có audit. |
| AC-47 | Teacher tạo lesson reusable và hai occurrence | Cập nhật lesson thành version mới | Occurrence cũ giữ version đã pin; lesson source không bị sửa ngược. |
| AC-48 | Teacher lesson ở trạng thái SCHOOL | Teacher yêu cầu PUBLIC | Chỉ publish sau Manager approval; khi bị Admin hide, search/access bị thu hồi và history giữ nguyên. |
| AC-49 | Parent mời Teacher chia sẻ child profile | Teacher chấp nhận rồi Parent revoke | Chỉ field scope được mở; revoke chặn API/token/job mới; hai account/profile owners vẫn tách biệt. |
| AC-50 | Teacher upload giáo án theo template | Parser/filter hoàn tất | AI chỉ nhận allowlisted structured fields đã qua Teacher preview/correction; raw file/full text không được gửi. |
| AC-51 | AI tạo lesson hoặc activity suggestion | Generation thành công | Trạng thái là draft; không public trước khi người có quyền review/publish. |
| AC-52 | Lesson chứa nhiều outdoor activities | Parent dùng lesson | Story/video chạy trước; activity list có materials/instructions/notes chỉ hiện sau video. |
| AC-53 | Parent/Teacher không bật line-sketch | Session bắt đầu vẽ | Không tạo sketch AI job, asset hoặc quota usage. |
| AC-54 | Parent hoặc Teacher bật script-following | Adult xác nhận script và yêu cầu video | Video mới được tạo từ tranh trẻ; direction được theo nhưng hình ảnh/clip được cá nhân hóa và không reuse video khác. |
| AC-55 | VLM subject confidence/mapping không hợp với tranh | Adult sửa subject | Hệ thống yêu cầu xác nhận, tạo revision mới và mới sau đó gợi ý lại. |
| AC-56 | Teacher occurrence có roster đủ điều kiện | Tạo video mẫu | Chọn một child đại diện ngẫu nhiên theo eligibility policy; occurrence vẫn tối đa một successful sample. |
| AC-57 | Parent profile có grant với Teacher trường A | Principal organization B đọc profile/feedback | Bị từ chối, không tiết lộ resource tồn tại hoặc nội dung. |
| AC-58 | Teacher/Manager/Admin reply feedback của Parent | Parent thuộc trường A mở feedback | Chỉ người có quyền của trường A thấy thread; không mở chat hoặc media attachment. |
| AC-59 | Parent/Teacher dùng lesson PUBLIC và yêu cầu AI đề xuất chỉnh sửa | Người lớn review output | Tạo draft/personal copy có lineage; source version và occurrence cũ không đổi. |
| AC-60 | Lesson đã được dùng rồi unpublish | Người dùng mở thư viện/history | Giữ version, occurrence và history metadata; thu hồi quyền tìm/tải/mở lesson content. Chỉ mở lại lesson content sau khi public lại hoặc có grant mới. |
| AC-61 | Parent yêu cầu generation trong quota scope riêng | Video job được accepted | Billing ghi đúng Parent scope; phí provider do platform xử lý theo package/policy. |
| AC-62 | Tuổi child ở biên 36 hoặc 120 tháng | Profile/run validation | Được chấp nhận; tuổi ngoài khoảng 36–120 bị từ chối hoặc cần policy transition rõ ràng. |
| AC-63 | Search lesson PUBLIC toàn platform | User không thuộc organization author | Public version có thể tìm/dùng; SCHOOL/PRIVATE/SELECTED không bị lộ. |
| AC-64 | Manager/Admin xem child media | Request thiếu permission/reason/audit | Deny; request có quyền hợp lệ được audit và vẫn chịu privacy/lifecycle policy. |
| AC-65 | Parent/Teacher dùng profile cá nhân hóa và lesson | AI lập story/video | Tuân thủ age band/context đã duyệt, nội dung tiếng Việt; video được tạo riêng theo tranh trẻ. |

### 31.10 Các quyết định còn mở

1. Nhóm tuổi Montessori cụ thể bên trong 3–10.
2. Role nào được bấm tạo AI lesson suggestion; câu trả lời về Admin/Teacher/Parent edit-vs-suggest cần được hòa giải. Baseline tạm thời: Parent không tạo suggestion.
3. Parent được sửa trường nào trong personal copy.
4. Parent lesson history là 30 hay 60 ngày; có thay theo plan/quota không.
5. Cách chọn random child đại diện, eligibility, consent/guardian notification và cơ chế loại trừ.
6. Default của script-following, chỗ được phép biến thể và cách Teacher/Parent override.
7. Quota pool Teacher riêng hay nằm trong school, fallback/charge order khi có nhiều pool, quota/price của từng package và hành vi hết quota.
8. Quyền publish public lesson do Platform Admin tạo và record review/moderation tương ứng; Teacher lesson cần Manager approval trước PUBLIC, SCHOOL-only không cần public approval.
9. Field list chính xác của profile share và cách invitation được thu hồi/hết hạn.
10. Visual asset/slide review, quyền sở hữu và approval khi AI tạo từ public lesson.
11. Nội dung chính xác của câu trả lời ngắn “có, cho phép” tại answer 46; không mở rộng quyền ngoài phạm vi chắc chắn cho đến khi gắn lại câu hỏi tương ứng.

### 31.11 Trace câu trả lời owner 1–49

Các số Q147–Q195 dưới đây là trace index cho 49 câu trả lời owner trong đợt làm rõ platform ngày 2026-10-28; chúng không sửa hoặc xóa Q01–Q146. Nội dung chưa rõ được nêu lại ở §31.10, không tự chuyển thành quyết định.

| Trace | Quyết định/ý owner | Ánh xạ trong SRS |
|---|---|---|
| Q147 | Platform là lớp kiến trúc bổ sung; giữ các phần phù hợp, Parent/Teacher flows và image/video pipeline; không tự ý bỏ baseline. | §31.1; BR-47 |
| Q148 | Tách role và permission đầy đủ; quyền có thể revoke. | §31.3; FR-PL-01; NFR-34 |
| Q149 | Mỗi trường là một organization. | §31.3; FR-PL-02 |
| Q150 | Parent/Teacher accounts tách biệt; cho phép share profile trẻ. | §31.3; FR-PL-07 |
| Q151 | Vẽ, sketch optional khi bật, chụp, video theo pipeline, rồi activities. | §31.5; FR-PL-15–16 |
| Q152 | Lesson dùng lại như preset, Teacher có thể dùng hoặc bỏ qua. | §31.2; FR-PL-03 |
| Q153 | Tuổi 3–10; có thể chia band để cá nhân hóa. | BR-18; FR-PL-25; AC-62 |
| Q154 | Child-centered, mixed-age, adult guide/observer/supporter, cá nhân hóa đúng tuổi. | §31.2; NFR-38; AC-65 |
| Q155 | Tiếng Việt trước; chưa thêm ngôn ngữ khác. | NFR-38 |
| Q156 | Giữ các yêu cầu nền hiện có theo lưu ý đã ghi trong SRS. | §31.1 |
| Q157 | Có AI-assisted lesson từ bước vẽ, kiến thức chủ đề, video và hoạt động; có thể gợi ý activity/visual/slide. | §31.2/31.4; FR-PL-12–14 |
| Q158 | Tạo draft; Presenton/FLUX.3 chỉ là ứng viên. | §31.1/31.4; FR-PL-14 |
| Q159 | Nêu quyền edit/suggest nhưng câu trả lời mâu thuẫn; chưa khóa role AI generation. | §31.4; §31.10(2) |
| Q160 | Lesson chữ; video mới dựa trên tranh trẻ, script có thể biên theo. | §31.2/31.5; FR-PL-17–18 |
| Q161 | Giữ lesson đã dùng; revoke access trừ khi public lại. | §31.2; FR-PL-05; AC-60 |
| Q162 | Hỗ trợ cả structured form lẫn template upload. | §31.4; FR-PL-09 |
| Q163 | AI hỗ trợ lên kế hoạch khi cần. | §31.4; FR-PL-12 |
| Q164 | Áp dụng luồng lọc nội dung theo ví dụ đã nêu. | §31.4; FR-PL-10–11 |
| Q165 | Giữ file gốc riêng; AI chỉ nhận dữ liệu đã lọc và Teacher review. | §31.4; NFR-35; AC-50 |
| Q166 | Dùng format/template mới. | §31.4; FR-PL-09 |
| Q167 | Teacher bật line-sketch trong session mới được sinh; tắt thì không tạo. | §31.5; FR-PL-15; AC-53 |
| Q168 | Cần School Manager duyệt trước PUBLIC. | §31.2/31.3; FR-PL-05 |
| Q169 | Sau duyệt mới chia sẻ theo visibility đã cấp. | §31.2; FR-PL-04–06 |
| Q170 | Share được cho nhóm Parent hoặc mời người cụ thể. | §31.2/31.3; FR-PL-06/23 |
| Q171 | Lesson PUBLIC tìm được toàn nền tảng; Teacher upload cần Manager duyệt trước public. | §31.2; FR-PL-04/05 |
| Q172 | Manager xem, duyệt và feedback. | §31.3/31.6 |
| Q173 | Trường giữ lesson của Teacher khi Teacher rời trường. | §31.2; FR-PL-03 |
| Q174 | Cho phép dùng/remix public lesson. | §31.2; FR-PL-04; AC-59 |
| Q175 | Manager duyệt theo trường; Platform Admin có quyền toàn nền tảng và ẩn nội dung. | §31.3; FR-PL-05 |
| Q176 | Parent profile link với Teacher bằng invitation. | §31.3; FR-PL-07 |
| Q177 | Parent dùng lesson PUBLIC để học với con. | §31.5; FR-PL-04 |
| Q178 | Parent thấy lesson đã dạy cho con. | §31.6; FR-PL-21 |
| Q179 | Parent xem thông tin lesson theo phương án đề xuất. | §31.6; FR-PL-21/22 |
| Q180 | Feedback, bỏ completion mark và upload tranh. | §31.6; FR-PL-22 |
| Q181 | Admin có thể xem/trả lời; feedback vẫn chỉ thuộc trường đó. | §31.3/31.6; NFR-36 |
| Q182 | Feedback, không mở direct chat. | §31.6; FR-PL-22 |
| Q183 | Parent xem lịch sử 30/60 ngày; exact window còn mở. | §31.6; §31.10(4) |
| Q184 | Video source là ảnh tranh bé vẽ. | §31.5; FR-PL-18 |
| Q185 | Teacher chọn ngẫu nhiên một trẻ đại diện; Parent có thể tạo video mới từ lesson cho con. | §31.5; FR-PL-18/20 |
| Q186 | Theo đúng script direction nhưng video khác biệt theo child drawing. | §31.5; FR-PL-17/18 |
| Q187 | Dùng profile để cá nhân hóa. | §31.5; FR-PL-08/18 |
| Q188 | Platform Admin và Teacher tham gia script authoring/review theo quyền. | §31.3/31.5; role matrix |
| Q189 | Có thể gợi ý AI sửa lesson/script khi dùng lại; output là bản nháp/copy riêng. | §31.2/31.5; FR-PL-03/17 |
| Q190 | Subject mismatch phải hỏi adult, cho sửa và gợi ý lại. | §31.5; FR-PL-19 |
| Q191 | Không reuse video; tạo video mới cho từng trẻ; script-following optional. | §31.5; FR-PL-17/18 |
| Q192 | Owner cho phép lựa chọn được hỏi ở answer 46; chi tiết đang cần gắn lại câu hỏi gốc. | §31.10(12) |
| Q193 | Platform chi phí provider; quota theo school/Teacher/Parent packages; Manager/Parent có thể mua/thêm quota. | §31.7; FR-PL-24 |
| Q194 | Tất cả workstream nêu ra đều nằm trong scope tài liệu. | §31.1–31.9 |
| Q195 | Có thể thay đổi/thêm; không sửa/xóa toàn bộ nếu chưa được phép. | §31.1; plan Rev25; preserved v2.2 snapshot |


## Rev31 backend implementation crosswalk (additive; pending SRS content review)

The v2.3 product-design baseline and requirements remain an unsigned draft. Rev31 implementation source adds three Lesson-owned support tables: `lesson.library_source_documents`, `lesson.library_document_revisions`, and `lesson.command_receipts`. They keep reusable-library uploads separate from occurrence-owned source documents and provide durable command idempotency. The current source-derived implementation crosswalk is 38 retained/refactored + 54 new = 92 active, plus 48 legacy/read-only = 140 projected physical mappings. This does not change product requirements, sign off the SRS/Data Table Register, or claim that the migration has run. See Data Table Register section 14.4 and EV-063-24.
