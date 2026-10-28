# Sketch2Life — Danh mục bảng dữ liệu

**Tính năng:** FEAT-063 — Thiết kế lại kiến trúc toàn repository  
**Trạng thái tài liệu:** Bản nháp v2.2 đồng bộ SRS; Q01–Q146 đã được ghi nhận cho baseline V1; Parent guide dùng AI Job/Core Asset/AI Policy hiện có, không thêm bảng; còn các gate kỹ thuật/pháp lý/commercial cần evidence
**Phiên bản:** 2.2-draft
**Cập nhật:** 2026-10-28  
**SRS đi kèm:** [SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md](SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md)  
**Điều kiện tạo diagram/PDF:** Chỉ tạo diagram khái niệm, logic và PDF sau khi chủ sở hữu phê duyệt cả hai tài liệu Markdown.

## Mục lục

1. [Quy tắc đếm và tổng số đích](#1-quy-tắc-đếm-và-tổng-số-đích)
2. [Quy ước schema và quyền sở hữu](#2-quy-ước-schema-và-quyền-sở-hữu)
3. [Kiểm kê nguồn và cách xử lý](#3-kiểm-kê-86-bảng-nguồn-và-cách-xử-lý)
4. [Các bảng hiện có được giữ hoạt động](#4-trách-nhiệm-của-38-bảng-hiện-có-được-giữ-và-tái-cấu-trúc)
5. [Từ điển bảng đích mới](#5-từ-điển-bảng-đích-mới-40)
6. [Quy tắc quan hệ và quyền sở hữu đích](#6-quy-tắc-quan-hệ-và-quyền-sở-hữu-đích)
7. [Bất biến cơ sở dữ liệu và chỉ mục](#7-bất-biến-cơ-sở-dữ-liệu-và-kế-hoạch-chỉ-mục)
8. [Xóa dữ liệu và kiểm toán](#8-ranh-giới-xóa-lưu-giữ-và-kiểm-toán)
9. [Chính sách legacy chỉ đọc](#9-chính-sách-legacy-chỉ-đọc)
10. [Đối soát migration](#10-danh-sách-đối-soát-migration)
11. [Truy vết số lượng bảng](#11-truy-vết-số-lượng-bảng)
12. [Quyết định đã chốt và cổng kỹ thuật còn mở](#12-quyết-định-đã-chốt-và-cổng-kỹ-thuật-còn-mở)
13. [Nguồn liên quan](#13-nguồn-liên-quan)

## 1. Quy tắc đếm và tổng số đích

Danh mục này đếm các mapping SQLAlchemy/Core production đã khai báo và các bảng logic đích được đề xuất. Danh mục không khẳng định cơ sở dữ liệu đã triển khai hiện có đủ mọi mapping đã khai báo. Chưa kiểm tra trực tiếp cơ sở dữ liệu đang chạy. Năm bảng fixture dùng để kiểm tra ranh giới quyền sở hữu chỉ phục vụ kiểm thử và được loại khỏi phép đếm.

| Phân loại | Số lượng | Cách xử lý |
|---|---:|---|
| Bảng production hiện tại đã khai báo | 86 | Đối chiếu từ danh mục mapping hiện có trong repository |
| Bảng fixture chỉ dùng cho kiểm thử hiện tại | 5 | Loại khỏi số lượng production và bảng đích |
| Bảng hiện tại được giữ/tái cấu trúc để tiếp tục hoạt động | 38 | Giữ chủ sở hữu module hiện tại; tối giản các ledger/registry trùng vòng đời |
| Bảng đích chuẩn hóa mới | 40 | Gồm các bảng Parent/profile, Lesson/Sketch Deck, Story, Billing/quota, Notifications, Core asset/upload và AI job cần vòng đời riêng |
| Tổng số bảng đích active | **78** | 38 + 40 |
| Bảng hiện tại được đánh dấu legacy/chỉ đọc | 48 | Giữ nguyên bảng vật lý và các hàng; không đưa vào ERD đích |
| Tổng số bảng production vật lý sau chuyển đổi schema đích | **126** | 78 bảng active + 48 bảng legacy được giữ lại |

Kiểm tra phép tính: số bảng nguồn hiện tại = 38 bảng giữ/tái cấu trúc + 48 bảng legacy = 86. Số bảng active đích = 38 + 40 = 78. Tổng số bảng vật lý sau chuyển đổi = 78 + 48 = 126. Không cộng 5 bảng fixture vào các phép tính này.

**Tinh gọn AI Policy:** 12 bảng registry bản sao provider được chuyển sang legacy/read-only; flow synthetic V1 theo dõi transfer và dọn scratch trên `ai_jobs.attempt`/`ai_jobs.job_events` cùng provenance của Core Asset. `ai_policy.resource_receipt` cũng trở thành legacy/read-only; với lệnh mới, `ai_policy.resource_event` mang idempotency key, fingerprint và snapshot kết quả cùng event/outbox metadata. Như vậy không có bảng ghi kép receipt/event và không có registry 12 bảng chỉ cần khi xử lý dữ liệu thật. Kích hoạt real-child-data/provider transfer vẫn bị chặn cho tới khi có review riêng về retention/ủy quyền; trước gate này phải duyệt lại việc cần tái lập registry provider.

**Thiết kế này không bao gồm thao tác phá hủy dữ liệu:** không drop, truncate, sao chép bảng sang một kho lưu trữ trùng lặp hoặc âm thầm diễn giải lại dữ liệu. Các bảng ngừng dùng bị loại khỏi ERD logic mới và sẽ chuyển sang chỉ đọc theo kế hoạch triển khai/cutover được duyệt sau này. Số lượng bảng hiện là đề xuất cho đến khi kiểm kê migration và kiểm tra trực tiếp cơ sở dữ liệu trong một nhiệm vụ triển khai được phê duyệt.

## 2. Quy ước schema và quyền sở hữu

### 2.1 Chủ sở hữu

| Chủ sở hữu/schema | Trách nhiệm | Số bảng sau khi áp dụng mô hình đích |
|---|---|---:|
| core | Metadata/lineage asset dùng chung, revision aggregate, audit/outbox và upload session/part receipts | 8 |
| be1 | Tổ chức, danh tính người lớn, phân công, lớp, hồ sơ/enrollment Teacher, consent và lifecycle | 11 |
| ai_jobs | AI job bền vững, attempt/receipt/outbox và event tiến trình có quan hệ với job | 8 |
| ai_policy | Policy AI có version, kích hoạt và hạch toán compute/budget nền tảng | 12 |
| learning_content | Danh mục hoạt động Parent có version và được duyệt | 6 |
| parent | Hồ sơ do Parent sở hữu, revision/context/nhu cầu hỗ trợ và ủy quyền | 5 |
| lesson | Tài liệu giáo án, occurrence plan và deck AI Sketch theo lesson | 7 |
| story | Story run cho một trẻ cùng input/context snapshot, revision/review/video bất biến | 9 |
| billing | Thuê bao tổ chức, billing sức chứa lớp và quota video grants/usage | 9 |
| notifications | Hộp thư trong ứng dụng, push endpoint và các lần gửi thông báo | 3 |
| **Tổng active** |  | **78** |
| Bảng nguồn legacy/chỉ đọc | Canvas/cộng tác/video/activity/preset cũ và provider-copy registry/receipt được deferred | **48** |

### 2.2 Quy ước áp dụng xuyên suốt

- Dùng ID chính UUID/ULID không mang ý nghĩa nghiệp vụ, timestamp UTC, giá trị state tường minh và version của schema/contract.
- Dữ liệu quan hệ phải được lưu theo mô hình quan hệ. Chỉ dùng JSONB cho snapshot có giới hạn, được kiểm tra và có version; không lưu hồ sơ, scene, danh sách trẻ hoặc asset không giới hạn trong JSON.
- Nội dung nhị phân như ảnh, âm thanh, giáo án và video được lưu trong object storage riêng tư. Hàng quan hệ lưu tham chiếu asset không mang ý nghĩa nghiệp vụ, hash, metadata media và lineage.
- Mỗi hàng dùng xuyên vai trò, nếu đại diện cho dữ liệu do người dùng sở hữu, phải có `owner_scope_kind` và `owner_scope_ref` có kiểu rõ ràng. `organization_id` tiếp tục là khóa tổ chức cho dữ liệu Teacher hiện có; dữ liệu Parent dùng scope tài khoản Parent, tuyệt đối không tạo tổ chức giả. Giữ nguyên các cột organization legacy cho đến khi có migration tương thích được phê duyệt riêng.
- Mỗi module sở hữu các bảng và thao tác ghi của mình. Cho phép khóa ngoại nội bộ trong một module/schema. Tham chiếu liên module là tham chiếu opaque có version, được kiểm tra qua application port; không tạo khóa ngoại chéo chủ sở hữu hoặc coupling SQL trực tiếp giữa các module.
- Scope tài khoản Parent là PARENT_ACCOUNT; scope dữ liệu Teacher là ORGANIZATION. ID actor người lớn được suy ra ở server từ danh tính đã xác minh. Không bao giờ biểu diễn Parent thành một tổ chức giả.
- Revision hồ sơ và snapshot run là bất biến. Cập nhật đối tượng đã duyệt tạo revision mới và làm mất hiệu lực các job dựa trên revision cũ.
- Chỉ thu thập telemetry metadata không chứa nội dung. Không ghi prompt model, tên trẻ, transcript, byte media, URL ký số hoặc nội dung nhu cầu hỗ trợ vào log/sự kiện audit.
- Xóa asset tuân theo lifecycle. Không xóa bản gốc được giữ lại hoặc tham chiếu dùng chung chỉ vì xóa một tham chiếu run; dịch vụ lifecycle sở hữu dữ liệu phải đối soát các tham chiếu trước khi purge.

## 3. Kiểm kê 86 bảng nguồn và cách xử lý

Hai giá trị trong cột trạng thái:

- **Retain/refactor:** tiếp tục hoạt động trong mô hình đích. Giữ dữ liệu hiện có và quyền sở hữu bảng; mọi thay đổi schema/contract theo hướng bổ sung và phải qua cổng migration.
- **Legacy/read-only:** loại bảng khỏi ERD đích và luồng mới. Giữ nguyên bảng vật lý và bản ghi, dừng các thao tác ghi mới của sản phẩm sau cutover được duyệt, và tuyệt đối không diễn giải ID cũ thành ID story/lesson mới.

| # | Nhóm chủ sở hữu hiện tại | Bảng/mapping hiện tại | Trạng thái đích | Chủ sở hữu/thao tác đích |
|---:|---|---|---|---|
| 1 | Lưu trữ Core | core_aggregate_revisions | Retain/refactor | core; giữ revision aggregate và provenance cho các aggregate hiện có |
| 2 | Lưu trữ Core | core_canvas_operations | Legacy/read-only | giữ lịch sử thao tác vẽ; không ghi lên canvas dùng chung |
| 3 | Lưu trữ Core | core_idempotency_receipts | Legacy/read-only | giữ receipt của thao tác canvas; idempotency story/payment mới dùng receipt do module tương ứng sở hữu |
| 4 | Lưu trữ Core | core_canvas_checkpoints | Legacy/read-only | giữ checkpoint canvas cũ; mô hình đích không có canvas cộng tác |
| 5 | Lưu trữ Core | core_asset_metadata | Retain/refactor | core; metadata hash/loại/kích thước byte canonical cho asset riêng tư; scope mở rộng bằng owner scope Parent có kiểu; Parent Sketch Guide dùng asset tạm có expiry/cleanup |
| 6 | Lưu trữ Core | core_audit_entries | Retain/refactor | core; audit đã loại nội dung nhạy cảm gồm actor/action/resource/outcome |
| 7 | Lưu trữ Core | core_outbox_events | Retain/refactor | core; transactional outbox cho event do Core sở hữu |
| 8 | Lưu trữ Core | core_outbox_consumer_receipts | Retain/refactor | core; idempotency của consumer event |
| 9 | BE1 danh tính/tổ chức | be1_organizations | Retain/refactor | be1; danh tính tổ chức; Billing là nguồn chuẩn về sức chứa lớp và được truy vấn qua entitlement port |
| 10 | BE1 danh tính/tổ chức | be1_adult_identities | Retain/refactor | be1; projection principal Firebase đã xác minh; bổ sung `account_scope` loại trừ lẫn nhau cho Parent/Teacher, do server gán |
| 11 | BE1 danh tính/tổ chức | be1_organization_assignments | Retain/refactor | be1; phân quyền/vai trò trong tổ chức |
| 12 | BE1 danh sách lớp | be1_classrooms | Retain/refactor | be1; lớp đơn giản thuộc tổ chức, không mang ngữ nghĩa phòng/session trực tiếp |
| 13 | BE1 danh sách lớp | be1_managed_profiles | Retain/refactor | be1; bản ghi đầu hồ sơ Teacher thuộc tổ chức; schema hiện yêu cầu `class_id`, tuổi 36–155 tháng, `consent_id` và `consent_purpose_ref`; mô hình đích xem `class_id` là projection enrollment và các trường consent là tùy theo `data_origin` |
| 14 | BE1 danh sách lớp | be1_enrollments | Retain/refactor | be1; lịch sử roster lớp canonical; mô hình đích bổ sung ràng buộc mỗi hồ sơ có tối đa một enrollment active (khai báo hiện tại chưa thực thi bất biến này) |
| 15 | BE1 quyền riêng tư | be1_consent_records | Retain/refactor | be1; chỉ lưu bằng chứng mục đích/ủy quyền dùng dữ liệu thật; constraint state hiện tại chỉ có pending/revoked, chưa đủ cho xử lý dữ liệu thật sau này; demo dữ liệu tổng hợp không tạo consent record |
| 16 | BE1 lifecycle | be1_data_lifecycle_requests | Retain/refactor | be1; điều phối lifecycle hồ sơ/run và receipt xóa |
| 17 | BE1 runtime cộng tác | be1_device_grants | Legacy/read-only | không có luồng cho thiết bị người tham gia vào |
| 18 | BE1 runtime cộng tác | be1_sessions | Legacy/read-only | tuyệt đối không chuyển ID session nhiều trẻ thành story run |
| 19 | BE1 runtime cộng tác | be1_session_room_codes | Legacy/read-only | không có luồng QR/mã phòng |
| 20 | BE1 runtime cộng tác | be1_room_code_rate_limits | Legacy/read-only | rate limit API đích dùng khóa Redis/tài khoản/IP |
| 21 | BE1 runtime cộng tác | be1_session_learning_stages | Legacy/read-only | không có tiến trình stage theo session |
| 22 | BE1 runtime cộng tác | be1_session_learning_stage_events | Legacy/read-only | chỉ giữ event lịch sử |
| 23 | BE1 runtime cộng tác | be1_session_command_receipts | Legacy/read-only | giữ receipt command session cũ |
| 24 | BE1 runtime cộng tác | be1_group_drafts | Legacy/read-only | không có bản nháp nhóm |
| 25 | BE1 runtime cộng tác | be1_session_outcomes | Legacy/read-only | giữ nguyên ý nghĩa lịch sử của completed/ended-early |
| 26 | BE1 runtime cộng tác | be1_session_memberships | Legacy/read-only | không có membership/admission theo session |
| 27 | BE1 runtime cộng tác | be1_session_groups | Legacy/read-only | không có nhóm cộng tác |
| 28 | BE1 runtime cộng tác | be1_child_turns | Legacy/read-only | không có lượt thao tác canvas của trẻ |
| 29 | BE1 runtime cộng tác | be1_gallery_snapshots | Legacy/read-only | chỉ giữ gallery lịch sử; không tạo gallery nhóm mới |
| 30 | BE1 runtime cộng tác | be1_observations | Legacy/read-only | giữ quan sát session cũ làm lịch sử; context người lớn mới dùng revision context hồ sơ BE1 |
| 31 | AI job bền vững | ai_jobs.job | Retain/refactor | ai_jobs; bổ sung owner scope có kiểu, discriminator/target ref cho đúng một StoryRun, Teacher Sketch Deck hoặc Parent Sketch Guide và `story_run_ref` nullable theo target; Parent guide chỉ nhận generic topic/difficulty, không child/profile ref; `session_id` cũ và JSON nhiều subject/result/history giữ nguyên ý nghĩa legacy |
| 32 | AI job bền vững | ai_jobs.attempt | Retain/refactor | ai_jobs; bản ghi attempt theo provider/stage có giới hạn |
| 33 | AI job bền vững | ai_jobs.command_receipt | Retain/refactor | ai_jobs; idempotency command cho thao tác run/job |
| 34 | AI job bền vững | ai_jobs.semantic_request | Retain/refactor | ai_jobs; loại request trùng theo một run, một input và revision context |
| 35 | AI job bền vững | ai_jobs.completion_receipt | Retain/refactor | ai_jobs; xử lý idempotent kết quả accepted/stale/rejected |
| 36 | AI job bền vững | ai_jobs.cancellation_notice | Retain/refactor | ai_jobs; khóa hủy theo job/run, không theo batch trẻ |
| 37 | AI job bền vững | ai_jobs.outbox | Retain/refactor | ai_jobs; outbox bền vững cho dispatch queue/event |
| 38 | Chính sách AI | ai_policy.record | Retain/refactor | ai_policy; bản ghi nguồn của policy |
| 39 | Chính sách AI | ai_policy.version | Retain/refactor | ai_policy; các version policy bất biến |
| 40 | Chính sách AI | ai_policy.review | Retain/refactor | ai_policy; bằng chứng rà soát/phê duyệt policy |
| 41 | Chính sách AI | ai_policy.receipt | Retain/refactor | ai_policy; idempotency command policy |
| 42 | Chính sách AI | ai_policy.event | Retain/refactor | ai_policy; lịch sử event policy |
| 43 | Chính sách AI | ai_policy.outbox | Retain/refactor | ai_policy; chuyển phát event policy |
| 44 | Kích hoạt policy AI | effective_scope | Retain/refactor | ai_policy; scope policy đã kích hoạt |
| 45 | Kích hoạt policy AI | scope_transition | Retain/refactor | ai_policy; lịch sử chuyển trạng thái kích hoạt |
| 46 | Sổ tài nguyên policy AI | resource_scope | Retain/refactor | ai_policy; scope hạch toán provider/tài nguyên |
| 47 | Sổ tài nguyên policy AI | budget_bucket | Retain/refactor | ai_policy; bucket sổ usage; không mặc định có trần chi AI cứng do chủ sở hữu cấu hình |
| 48 | Sổ tài nguyên policy AI | resource_reservation | Retain/refactor | ai_policy; reserve/capture/release usage của provider |
| 49 | Sổ tài nguyên policy AI | resource_event | Retain/refactor | ai_policy; event usage tài nguyên |
| 50 | Sổ tài nguyên policy AI | resource_receipt | Legacy/read-only | Receipt lịch sử giữ nguyên; idempotency của command mới nằm trên `resource_event` |
| 51 | Registry bản sao AI policy | copy_scope | Legacy/read-only | Scope lịch sử provider; registry đầy đủ hoãn tới gate dữ liệu thật |
| 52 | Registry bản sao AI policy | copy_registration | Legacy/read-only | Định danh bản sao lịch sử giữ nguyên; flow synthetic mới dùng job-attempt scope |
| 53 | Registry bản sao AI policy | copy_coverage | Legacy/read-only | Bằng chứng coverage lịch sử, không cần trong flow synthetic V1 |
| 54 | Registry bản sao AI policy | copy_registry_event | Legacy/read-only | Event lịch sử chỉ đọc; job/asset events theo contract cho flow synthetic mới |
| 55 | Registry bản sao AI policy | copy_inventory_evidence | Legacy/read-only | Bằng chứng inventory lịch sử; real-data provider inventory là production gate |
| 56 | Registry bản sao AI policy | copy_operation | Legacy/read-only | Provider-copy operations lịch sử; không ghi operation mới cho scratch synthetic |
| 57 | Registry bản sao AI policy | copy_operation_authority | Legacy/read-only | Bằng chứng authority lịch sử; không dùng thay cho review dữ liệu thật |
| 58 | Registry bản sao AI policy | copy_delivery | Legacy/read-only | Projection delivery lịch sử; transfer demo được ghi theo AI job attempt |
| 59 | Registry bản sao AI policy | copy_delivery_history | Legacy/read-only | Revision delivery lịch sử được giữ nguyên, không active-write |
| 60 | Registry bản sao AI policy | copy_delivery_authority | Legacy/read-only | Authority transfer lịch sử; gate dữ liệu thật yêu cầu thiết kế/duyệt mới |
| 61 | Registry bản sao AI policy | copy_lifecycle | Legacy/read-only | Lifecycle bản sao cũ; Modal scratch cleanup demo thuộc job attempt |
| 62 | Registry bản sao AI policy | copy_resolution | Legacy/read-only | Resolution lịch sử; không active-write trong flow đích synthetic |
| 63 | Nội dung học tập | learning_content.record | Retain/refactor | learning_content; đầu mục nội dung catalog |
| 64 | Nội dung học tập | learning_content.version | Retain/refactor | learning_content; version hoạt động/catalog bất biến |
| 65 | Nội dung học tập | learning_content.review | Retain/refactor | learning_content; rà soát an toàn của quản trị nội dung |
| 66 | Nội dung học tập | learning_content.receipt | Retain/refactor | learning_content; command nội dung idempotent |
| 67 | Nội dung học tập | learning_content.event | Retain/refactor | learning_content; event catalog |
| 68 | Nội dung học tập | learning_content.outbox | Retain/refactor | learning_content; chuyển phát event |
| 69 | Video kiến thức | knowledge_video.run | Legacy/read-only | vòng đời video đơn trẻ do story run mới quản lý |
| 70 | Video kiến thức | knowledge_video.receipt | Legacy/read-only | giữ receipt idempotency của luồng video kiến thức cũ |
| 71 | Rà soát video | video_review.head | Legacy/read-only | mô hình đích không có head phê duyệt video cuối |
| 72 | Rà soát video | video_review.receipt | Legacy/read-only | giữ receipt command rà soát video cũ |
| 73 | Rà soát video | video_review.history | Legacy/read-only | mô hình đích không có lịch sử duyệt/rà soát video cuối |
| 74 | Rà soát video | video_review.playback | Legacy/read-only | playback đích được API cấp quyền; audit lượt xem chỉ lưu metadata trong Core |
| 75 | Rà soát video | video_review.playback_history | Legacy/read-only | giữ lịch sử playback cũ; audit mới dùng audit Core đã loại nội dung |
| 76 | Rà soát video | video_review.event | Legacy/read-only | giữ event rà soát video lịch sử |
| 77 | Lỗi video | video_failure.intent | Legacy/read-only | trạng thái job/run bền vững mới là nguồn chuẩn cho ý định lỗi |
| 78 | Lỗi video | video_failure.history | Legacy/read-only | attempt/event trong ai_jobs mới và trạng thái story run thay thế luồng ghi này |
| 79 | Lỗi video | video_failure.event | Legacy/read-only | giữ event lỗi lịch sử |
| 80 | Thực thi hoạt động | activity_execution.assignment | Legacy/read-only | không có assignment hoạt động riêng cho nhóm/session; một hoạt động chọn được ghim trên story run |
| 81 | Thực thi hoạt động | activity_execution.history | Legacy/read-only | V1 không có lịch sử thực thi hoạt động sau riêng biệt |
| 82 | Thực thi hoạt động | activity_execution.receipt | Legacy/read-only | giữ receipt command hoạt động cũ |
| 83 | Thực thi hoạt động | activity_execution.event | Legacy/read-only | giữ event hoạt động lịch sử |
| 84 | Thực thi hoạt động | activity_execution.ack | Legacy/read-only | luồng story mới không có quy trình xác nhận hoạt động |
| 85 | Tự động hóa preset | preset_automation.head | Legacy/read-only | occurrence giáo án/kế hoạch đã duyệt quản lý việc chuẩn bị của Teacher |
| 86 | Tự động hóa preset | preset_automation.history | Legacy/read-only | giữ revision preset cũ |

### 3.1 Số lượng kiểm kê theo chủ sở hữu

| Nhóm chủ sở hữu hiện tại | Bảng đã khai báo | Retain/refactor | Legacy/read-only |
|---|---:|---:|---:|
| Lưu trữ Core | 8 | 5 | 3 |
| BE1 danh tính/roster/quyền riêng tư/cộng tác | 22 | 8 | 14 |
| AI job bền vững | 7 | 7 | 0 |
| AI policy/kích hoạt/tài nguyên/registry bản sao | 25 | 12 | 13 |
| Nội dung học tập | 6 | 6 | 0 |
| Video kiến thức | 2 | 0 | 2 |
| Rà soát video | 6 | 0 | 6 |
| Lỗi video | 3 | 0 | 3 |
| Thực thi hoạt động | 5 | 0 | 5 |
| Tự động hóa preset | 2 | 0 | 2 |
| **Total** | **86** | **38** | **48** |

## 4. Trách nhiệm của 38 bảng hiện có được giữ và tái cấu trúc

Các tên bảng sau tiếp tục hoạt động trong mô hình đích. Các hàng hiện có và ranh giới chủ sở hữu được giữ lại. Cột nguồn ở cấp trường và thao tác đích được liệt kê tại §4.1. Migration theo giai đoạn có thể bổ sung trường scope và điều chỉnh khóa/khả năng nhận NULL/check sau khi backfill và đối soát tương đương; phải giữ mọi hàng/ID hiện có, không được drop bảng hoặc cột legacy nếu chưa có phê duyệt riêng.

| Chủ sở hữu | Bảng active | Trách nhiệm và ràng buộc đích |
|---|---|---|
| core (5) | core_aggregate_revisions; core_asset_metadata; core_audit_entries; core_outbox_events; core_outbox_consumer_receipts | Revision aggregate hiện có; metadata asset cho bản gốc/phái sinh; audit chỉ gồm metadata; transactional outbox; idempotency consumer event. Bổ sung OwnerScopeRefV1 khi cần, không diễn giải lại hàng cũ. |
| be1 (8) | be1_organizations; be1_adult_identities; be1_organization_assignments; be1_classrooms; be1_managed_profiles; be1_enrollments; be1_consent_records; be1_data_lifecycle_requests | Tổ chức, projection danh tính người lớn, vai trò, lớp/roster đơn giản, đầu hồ sơ Teacher, lịch sử enrollment, record consent/mục đích cho dữ liệu thật trong tương lai và yêu cầu lifecycle. Thực thi mỗi lớp chỉ có một Teacher phụ trách active và mỗi hồ sơ chỉ có một enrollment lớp active. |
| ai_jobs (7) | ai_jobs.job; ai_jobs.attempt; ai_jobs.command_receipt; ai_jobs.semantic_request; ai_jobs.completion_receipt; ai_jobs.cancellation_notice; ai_jobs.outbox | Job bền vững và sổ dispatch. Mỗi job mới có đúng một target discriminator/ref: `STORY_RUN`, `VIDEO_GENERATION`, `VIDEO_GENERATION_SCENE`, `LESSON_SOURCE_DOCUMENT`, `LESSON_SKETCH_DECK_REVISION` hoặc `PARENT_SKETCH_GUIDE`. Story/video target resolve đúng một profile từ StoryRun canonical; không lưu subject ref trùng lặp. Lesson extraction/sketch và Parent guide không có profile subject; Parent guide chỉ có generic topic/difficulty. `ai_jobs.attempt` ghi provider attempt, bounded transfer/cleanup metadata, correlation ID và retry duy nhất; session_id cũ không đổi. Lesson deck do Lesson aggregate sở hữu output refs; Parent guide trả private Core Asset ref tạm có expiry/lineage, không profile/StoryRun attachment. |
| ai_policy (12) | record; version; review; receipt; event; outbox; effective_scope; scope_transition; resource_scope; budget_bucket; resource_reservation; resource_event | Governance/version, activation và platform compute budget/reservation. `resource_event` là ledger append-only đồng thời lưu operation/idempotency key, fingerprint, reservation, outcome snapshot và delivery state; lệnh retry đọc lại đúng event. Không giữ bảng receipt riêng cho cùng một lệnh. 13 bảng provider-copy/`resource_receipt` cũ chỉ đọc, ngoài ERD đích. Chi tiết nguồn và migration ở §4.1, §9–§10. |
| learning_content (6) | learning_content.record; learning_content.version; learning_content.review; learning_content.receipt; learning_content.event; learning_content.outbox | Catalog hoạt động và content version được duyệt toàn cục. Parent chỉ chọn version đã xuất bản và được duyệt. Quản trị nội dung sở hữu việc rà soát và xuất bản. |

Các trường xuyên module được bổ sung/hoàn thiện khi triển khai có thể gồm owner_scope_kind/ref, contract_version, aggregate_version, created_at/updated_at, idempotency request, source hash và trạng thái xóa. Thao tác đích chính xác cho các trường hiện có cùng quy tắc canonical/projection nằm tại §4.1–§4.2. Kiểu SQL và bước migration chính xác cần được chủ sở hữu phê duyệt riêng và đối soát với schema đang chạy.

### 4.1 Bảng đối chiếu trường nguồn sang đích

Các danh sách cột nguồn dưới đây được trích từ khai báo SQLAlchemy/Core trong repository ngày 2026-10-27, không phải từ database đang chạy. Với mỗi cột được liệt kê, ý nghĩa đích cùng tên được giữ nguyên trừ khi ô thao tác đích nêu rõ migration hoặc thay đổi chủ sở hữu canonical. Quy tắc tại §4.2 được ưu tiên hơn phần tóm tắt theo nhóm trước đó nếu có mâu thuẫn. Không backfill trường từ dữ liệu trẻ suy đoán; hàng legacy không rõ nghĩa phải được đánh dấu để rà soát.

| Bảng đích | Khai báo nguồn | Các cột hiện được khai báo | Thao tác đích / lý do theo yêu cầu |
|---|---|---|---|
| `ai_jobs.attempt` | `backend/src/sketch2life/infrastructure/ai_jobs/sql/tables.py` | `attempt_id`; `job_id`; `attempt_number`; `request_ref`; `dispatch_count`; `outcome` | Là sổ lần gọi/retry provider duy nhất. Đích bổ sung metadata có giới hạn: correlation ID, hash manifest input/output, opaque provider workspace/attempt ref, trạng thái và thời điểm cleanup; không lưu media/prompt/PII thô. Một hàng scene trỏ về đúng job; không sao chép bộ đếm retry vào Story. |
| `ai_jobs.cancellation_notice` | `backend/src/sketch2life/infrastructure/ai_jobs/sql/tables.py` | `notice_id`; `organization_id`; `reason_code`; `session_id`; `job_type`; `subject_ref`; `status`; `applied_count` | Bổ sung owner scope và story_run_ref để hủy cho Parent/Teacher. Chỉ giữ session_id cho luồng cộng tác đã ngừng dùng. |
| `ai_jobs.command_receipt` | `backend/src/sketch2life/infrastructure/ai_jobs/sql/tables.py` | `organization_id`; `principal_id`; `contract_name`; `target_id`; `idempotency_key`; `fingerprint`; `job_id`; `outcome`; `job_revision_at_commit` | Bổ sung owner scope có kiểu và receipt_id thay thế; giữ khóa tổng hợp organization cũ làm quy tắc unique tương thích cho đến khi chuyển khóa được duyệt. Không được dùng ID tổ chức giả cho idempotency của Parent. |
| `ai_jobs.completion_receipt` | `backend/src/sketch2life/infrastructure/ai_jobs/sql/tables.py` | `job_id`; `attempt_id`; `receipt_id`; `fingerprint`; `disposition`; `reason_code`; `job_revision_after` | Hàng rào canonical idempotent cho kết quả accepted/stale/rejected của từng job attempt; event job và trạng thái hiện tại của job là projection/lịch sử, không phải nguồn chuẩn cạnh tranh. |
| `ai_jobs.job` | `backend/src/sketch2life/infrastructure/ai_jobs/sql/tables.py` | `job_id`; `organization_id`; `job_type`; `job_revision`; `state`; `session_id`; `subject_refs`; `purpose_code`; `target_id`; `request_ref`; `correlation_id`; `policy_snapshot_id`; `policy_snapshot`; `progress`; `result_disposition`; `result_refs`; `failure`; `lineage_note`; `history`; `accepted_fences` | Bổ sung owner scope, `target_kind`, một `target_ref`, expected target revision và input hash. Target mới là đúng một trong `STORY_RUN`, `VIDEO_GENERATION`, `VIDEO_GENERATION_SCENE`, `LESSON_SOURCE_DOCUMENT`, `LESSON_SKETCH_DECK_REVISION`; không dùng các nullable target-ref song song. Story resolve đúng một profile từ StoryRun; sketch không có profile. Job mới dùng `session_id=NULL`, JSON legacy arrays/history rỗng; `job_events` là nguồn tiến độ, completion receipt chỉ giữ disposition/hash. Giữ nguyên nghĩa cột cũ cho hàng lịch sử. |
| `ai_jobs.outbox` | `backend/src/sketch2life/infrastructure/ai_jobs/sql/tables.py` | `message_id`; `kind`; `event_id`; `organization_id`; `job_id`; `attempt_id`; `payload`; `lease_owner`; `lease_generation`; `publish_attempts`; `last_error_code` | Chỉ chứa message dispatch AI, tách biệt với domain event Core. Bổ sung owner scope có kiểu và envelope payload có version; payload không chứa quyền worker hay nội dung. |
| `ai_jobs.semantic_request` | `backend/src/sketch2life/infrastructure/ai_jobs/sql/tables.py` | `semantic_key_sha256`; `organization_id`; `job_type`; `request_id`; `request_revision`; `input_hash`; `context_revision`; `target_id`; `purpose_code`; `session_id`; `subject_refs`; `job_id` | Bổ sung owner scope có kiểu; đưa scope, input hash, context revision và purpose vào digest semantic canonical. Legacy session/subject_refs chỉ dùng cho lịch sử. |
| `ai_policy.budget_bucket` | `backend/src/sketch2life/infrastructure/ai_policy/accounting_tables.py` | `organization_id`; `bucket_id`; `feature_scope`; `key`; `held_units`; `spent_units` | Bucket usage có giới hạn và tổng reservation; dùng để cảnh báo/hạch toán, không phải trần chi cứng trừ khi được cấu hình riêng. |
| `ai_policy.copy_coverage` | `backend/src/sketch2life/infrastructure/ai_policy/copy_registry_tables.py` | `organization_id`; `scope_ref`; `applied_revision`; `observation` | Legacy/read-only. Không ghi coverage mới trong synthetic V1; provider inventory là gate trước real-child-data. |
| `ai_policy.copy_delivery` | `backend/src/sketch2life/infrastructure/ai_policy/copy_registry_tables.py` | `organization_id`; `scope_ref`; `operation_key`; `revision`; `status`; `snapshot` | Legacy/read-only. Transfer synthetic được truy vết theo AI job attempt và opaque attempt ref. |
| `ai_policy.copy_delivery_authority` | `backend/src/sketch2life/infrastructure/ai_policy/copy_registry_tables.py` | `organization_id`; `evidence_id`; `scope_ref`; `operation_key`; `evidence` | Legacy/read-only; không được coi là phê duyệt thẩm quyền cho luồng real-data mới. |
| `ai_policy.copy_delivery_history` | `backend/src/sketch2life/infrastructure/ai_policy/copy_registry_tables.py` | `organization_id`; `scope_ref`; `operation_key`; `revision`; `snapshot` | Legacy/read-only; giữ nguyên revision lịch sử, không là nguồn chuẩn cho flow mới. |
| `ai_policy.copy_inventory_evidence` | `backend/src/sketch2life/infrastructure/ai_policy/copy_registry_tables.py` | `organization_id`; `evidence_id`; `scope_ref`; `principal_id`; `inventory_revision`; `observed_at`; `record` | Legacy/read-only; real-data provider inventory cần được thiết kế và phê duyệt trước khi bật. |
| `ai_policy.copy_lifecycle` | `backend/src/sketch2life/infrastructure/ai_policy/copy_registry_tables.py` | `organization_id`; `scope_ref`; `copy_id`; `revision`; `snapshot` | Legacy/read-only; scratch Modal synthetic được cleanup và đối soát từ job attempt/event, không có provider-copy registry riêng. |
| `ai_policy.copy_operation` | `backend/src/sketch2life/infrastructure/ai_policy/copy_registry_tables.py` | `organization_id`; `scope_ref`; `operation_key`; `copy_id`; `envelope` | Legacy/read-only; không ghi lệnh provider-copy mới trong synthetic V1. |
| `ai_policy.copy_operation_authority` | `backend/src/sketch2life/infrastructure/ai_policy/copy_registry_tables.py` | `organization_id`; `observation_id`; `scope_ref`; `operation_key`; `observation` | Legacy/read-only; dữ liệu lịch sử không cấp authority cho job mới. |
| `ai_policy.copy_registration` | `backend/src/sketch2life/infrastructure/ai_policy/copy_registry_tables.py` | `organization_id`; `scope_ref`; `copy_id`; `kind`; `original_profile_ref`; `initially_quarantined` | Legacy/read-only; identity/scratch scope của synthetic job thuộc attempt hiện hành, không tạo một registry aggregate thứ hai. |
| `ai_policy.copy_registry_event` | `backend/src/sketch2life/infrastructure/ai_policy/copy_registry_tables.py` | `organization_id`; `event_id`; `scope_ref`; `revision`; `principal_id`; `occurred_at`; `payload`; `delivered_at` | Legacy/read-only; sự kiện synthetic mới thuộc job events có correlation/version. |
| `ai_policy.copy_resolution` | `backend/src/sketch2life/infrastructure/ai_policy/copy_registry_tables.py` | `organization_id`; `scope_ref`; `resolution_key`; `copy_id`; `operation_key`; `revision`; `before_state`; `after_state`; `observation` | Legacy/read-only; xử lý sai lệch provider-copy cho real data là gate thiết kế riêng. |
| `ai_policy.copy_scope` | `backend/src/sketch2life/infrastructure/ai_policy/copy_registry_tables.py` | `organization_id`; `scope_ref`; `revision`; `purging` | Legacy/read-only; V1 chỉ sử dụng prefix attempt cô lập và cleanup job-scoped trên Modal synthetic. |
| `ai_policy.effective_scope` | `backend/src/sketch2life/infrastructure/ai_policy/activation_tables.py` | `organization_id`; `feature_scope`; `epoch`; `record_id`; `version`; `hash`; `disabled` | Projection kích hoạt policy hiện tại theo scope global/org tường minh; mỗi AI job phải ghim version kích hoạt. |
| `ai_policy.event` | `backend/src/sketch2life/infrastructure/ai_policy/tables.py` | `organization_id`; `event_id`; `record_id`; `version`; `revision`; `kind`; `principal_id`; `occurred_at`; `payload` | Event lifecycle policy chỉ ghi nối tiếp; không chứa prompt model hoặc nội dung trẻ. |
| `ai_policy.outbox` | `backend/src/sketch2life/infrastructure/ai_policy/tables.py` | `organization_id`; `event_id`; `payload`; `delivered_at` | Chỉ chuyển phát event policy có version; không dùng để dispatch tác vụ AI. |
| `ai_policy.receipt` | `backend/src/sketch2life/infrastructure/ai_policy/tables.py` | `organization_id`; `principal_id`; `request_id`; `fingerprint`; `result_json` | Idempotency command policy; ngăn sửa policy trùng lặp. |
| `ai_policy.record` | `backend/src/sketch2life/infrastructure/ai_policy/tables.py` | `current_version`; `revision` | Bản ghi quản trị nền tảng: head version hiện tại của policy an toàn AI/nội dung; không phải story hoặc hồ sơ trẻ. |
| `ai_policy.resource_event` | `backend/src/sketch2life/infrastructure/ai_policy/accounting_tables.py` | `organization_id`; `event_id`; `feature_scope`; `reservation_id`; `principal_id`; `occurred_at`; `payload`; `delivered_at` | Đích giữ event bất biến, thêm `client_request_id`, fingerprint, operation và response snapshot có giới hạn với unique idempotency key. Một transaction cập nhật reservation/bucket và append đúng một event; retry trả lại event đã ghi. Không chứa nội dung người dùng. |
| `ai_policy.resource_receipt` | `backend/src/sketch2life/infrastructure/ai_policy/accounting_tables.py` | `organization_id`; `principal_id`; `client_request_id`; `feature_scope`; `fingerprint`; `reservation_id`; `operation` | Legacy/read-only; idempotency history cũ được giữ, receipt cho command mới gộp vào `resource_event` để không có hai ledger song song. |
| `ai_policy.resource_reservation` | `backend/src/sketch2life/infrastructure/ai_policy/accounting_tables.py` | `organization_id`; `reservation_id`; `feature_scope`; `bucket_id`; `request_digest`; `attempt_id`; `state`; `payload` | Reserve/capture/release idempotent cho compute/GPU capacity và giới hạn tài nguyên nền tảng. Không lưu hoặc phân bổ product video quota; không thêm `FULL_VIDEO_REQUEST` vào scope resource. |
| `ai_policy.resource_scope` | `backend/src/sketch2life/infrastructure/ai_policy/accounting_tables.py` | `organization_id`; `feature_scope`; `occupied_slots` | Sở hữu giới hạn đồng thời/backpressure của platform cho global/account/org; chỉ GPU/compute capacity, không sở hữu hoặc phân bổ product video quota đã mua/cấp. Quota được cấp và tiêu thụ trong Billing `video_quota_grants` + `video_quota_usage`. |
| `ai_policy.review` | `backend/src/sketch2life/infrastructure/ai_policy/tables.py` | `organization_id`; `review_id`; `record_id`; `version`; `context_revision`; `review_revision`; `dimension`; `proof` | Bằng chứng người rà soát cho việc xuất bản policy; giữ provenance actor/revision. |
| `ai_policy.scope_transition` | `backend/src/sketch2life/infrastructure/ai_policy/activation_tables.py` | `organization_id`; `feature_scope`; `epoch`; `event_id`; `principal_id`; `occurred_at`; `payload`; `delivered_at` | Chuyển trạng thái kích hoạt chỉ ghi nối tiếp; kiểm toán rollout và rollback policy. |
| `ai_policy.version` | `backend/src/sketch2life/infrastructure/ai_policy/tables.py` | `version`; `body_json`; `hash`; `state`; `authored_by`; `created_at`; `context_revision`; `review_revision`; `publication_review_ids`; `publication_policy_version`; `recalled_at`; `recall_reason` | Body/hash policy và revision xuất bản bất biến; là nguồn chuẩn policy để kiểm tra story/input/output. |
| `be1_adult_identities` | `backend/src/sketch2life/infrastructure/persistence/be1_models.py` | `subject`; `issuer`; `state`; `created_at` | Bổ sung account_scope=PARENT hoặc TEACHER loại trừ lẫn nhau, khóa theo issuer/UID đã xác minh. Một UID không thể đăng ký cả hai scope; claim từ client không bao giờ được gán trường này. |
| `be1_classrooms` | `backend/src/sketch2life/infrastructure/persistence/be1_models.py` | `class_id`; `organization_id`; `display_name`; `state`; `created_by`; `created_at` | Danh tính lớp/roster container canonical; state là projection vận hành từ event sức chứa/tạm ngưng của Billing. Không tự định nghĩa giới hạn sức chứa ở đây. |
| `be1_consent_records` | `backend/src/sketch2life/infrastructure/persistence/be1_models.py` | `consent_id`; `organization_id`; `class_id`; `child_id`; `purpose_ref`; `evidence_ref`; `state`; `recorded_by`; `recorded_at`; `verification_note` | Chỉ lưu bằng chứng ủy quyền xử lý dữ liệu thật. Hàng dữ liệu tổng hợp không tạo consent. Giữ các hàng pending/revoked hiện có; check state hiện tại chưa đủ cho xử lý dữ liệu thật trong tương lai. |
| `be1_data_lifecycle_requests` | `backend/src/sketch2life/infrastructure/persistence/be1_models.py` | `request_id`; `organization_id`; `request_type`; `target_ref`; `state`; `unresolved_items`; `result_ref`; `requested_by`; `created_at`; `completed_at` | Workflow và trạng thái lifecycle BE1 canonical; không chứa byte media hoặc nội dung hồ sơ tự do. |
| `be1_enrollments` | `backend/src/sketch2life/infrastructure/persistence/be1_models.py` | `enrollment_id`; `organization_id`; `class_id`; `child_id`; `state`; `created_by`; `created_at` | Membership roster hiện tại/lịch sử canonical. Bổ sung partial unique constraint đã kiểm chứng để mỗi trẻ chỉ có một enrollment active; cập nhật projection class_id một cách nguyên tử. |
| `be1_managed_profiles` | `backend/src/sketch2life/infrastructure/persistence/be1_models.py` | `child_id`; `organization_id`; `class_id`; `display_name`; `age_months`; `consent_id`; `consent_purpose_ref`; `state`; `created_by`; `created_at` | Projection head hồ sơ. class_id được suy ra từ enrollment active duy nhất; bổ sung current_profile_revision_ref và data_origin. Consent ref trở thành tùy chọn theo nguồn; hồ sơ tổng hợp không có consent. Giữ khoảng tuổi đã xác nhận 36–155 tháng cho profile Parent và Teacher V1. |
| `be1_organization_assignments` | `backend/src/sketch2life/infrastructure/persistence/be1_models.py` | `assignment_id`; `organization_id`; `subject`; `class_id`; `role`; `active`; `created_at` | Phân quyền vai trò Teacher/admin theo tổ chức/lớp canonical. Bổ sung assignment_version làm hàng rào thu hồi; luồng mới chỉ cấp media lớp cho Teacher đang phụ trách. |
| `be1_organizations` | `backend/src/sketch2life/infrastructure/persistence/be1_models.py` | `organization_id`; `display_name`; `state`; `created_at` | Danh tính và trạng thái tổ chức canonical; entitlement billing được truy vấn qua Billing port, không sao chép vào đây. |
| `core_aggregate_revisions` | `backend/src/sketch2life/infrastructure/persistence/core_models.py` | `aggregate_id`; `organization_id`; `revision`; `updated_at` | Chỉ giữ cho aggregate tổ chức hiện có. Story sở hữu revision story/profile/lesson; không dùng hàng này làm bộ đếm revision story trùng lặp. |
| `core_asset_metadata` | `backend/src/sketch2life/infrastructure/persistence/core_models.py` | `asset_ref`; `asset_version`; `organization_id`; `content_sha256`; `media_type`; `source_refs`; `derived_from_ref`; `created_at` | Metadata canonical về version/hash/loại media/kích thước byte/scope chủ sở hữu của asset. Bổ sung owner_scope_kind/ref có kiểu; organization_id legacy ánh xạ sang ORGANIZATION. Asset Parent mới dùng PARENT_ACCOUNT, tuyệt đối không dùng tổ chức giả. Cạnh lineage mới dùng core.asset_lineage; source_refs legacy chỉ đọc với hàng cũ. Asset metadata ghi state kiểm định/quarantine/ready/deletion cho asset đã được final hóa; Parent Sketch Guide bổ sung lifecycle/`expires_at` cho output tạm và xóa idempotent; session/chunk/expiry/receipt upload vẫn thuộc `core.upload_sessions`/`core.upload_parts`. Asset READY sau schema/media/safety validation mới được hiển thị; Story/Lesson chỉ tham chiếu asset thuộc aggregate của mình. |
| `core_audit_entries` | `backend/src/sketch2life/infrastructure/persistence/core_models.py` | `audit_id`; `organization_id`; `actor_ref`; `action`; `resource_type`; `resource_id`; `decision`; `created_at` | Chỉ lưu metadata. Bổ sung owner scope có kiểu cho event Parent; ID actor/resource vẫn opaque và audit không chứa nội dung. |
| `core_outbox_consumer_receipts` | `backend/src/sketch2life/infrastructure/persistence/core_models.py` | `consumer_name`; `event_id`; `processed_at` | Giữ nguyên idempotency consumer/event; không tạo trạng thái nghiệp vụ trùng lặp. |
| `core_outbox_events` | `backend/src/sketch2life/infrastructure/persistence/core_models.py` | `event_id`; `event_type`; `organization_id`; `aggregate_id`; `aggregate_revision`; `payload`; `status`; `attempt_count`; `available_at`; `lease_owner`; `lease_until`; `delivered_at`; `created_at` | Chỉ relay domain event Core, tách biệt với ai_jobs.outbox. Bổ sung contract_version và owner scope có kiểu; payload event có giới hạn và không chứa nội dung. |
| `learning_content.event` | `backend/src/sketch2life/infrastructure/learning_content/tables.py` | `event_id`; `organization_id`; `record_id`; `version`; `revision`; `kind`; `principal_id`; `occurred_at`; `payload` | Event lifecycle catalog chỉ ghi nối tiếp. |
| `learning_content.outbox` | `backend/src/sketch2life/infrastructure/learning_content/tables.py` | `event_id`; `organization_id`; `payload`; `delivered_at` | Chuyển phát event catalog; không phải thực thi Story hoặc trạng thái job. |
| `learning_content.receipt` | `backend/src/sketch2life/infrastructure/learning_content/tables.py` | `organization_id`; `principal_id`; `request_id`; `fingerprint`; `result_json` | Idempotency cho thay đổi catalog. |
| `learning_content.record` | `backend/src/sketch2life/infrastructure/learning_content/tables.py` | `current_version`; `revision` | Danh tính hoạt động trong catalog toàn cục; không có dữ liệu story thuộc tổ chức hoặc gắn riêng với trẻ. |
| `learning_content.review` | `backend/src/sketch2life/infrastructure/learning_content/tables.py` | `organization_id`; `review_id`; `record_id`; `version`; `context_revision`; `review_revision`; `dimension`; `proof` | Provenance rà soát an toàn/nội dung của catalog toàn cục; mô hình đích bổ sung owner scope GLOBAL có kiểu và xem organization_id legacy là trường tương thích, không phải ranh giới tenant mới. |
| `learning_content.version` | `backend/src/sketch2life/infrastructure/learning_content/tables.py` | `version`; `body_json`; `hash`; `state`; `authored_by`; `created_at`; `context_revision`; `review_revision`; `publication_review_ids`; `publication_policy_version`; `recalled_at`; `recall_reason` | Nội dung/version hoạt động đã duyệt là bất biến; Parent ghim chính xác version đã xuất bản. |

Metadata lọc catalog hoạt động được lưu trong `learning_content.version.body_json` theo activity schema có version; không tạo bảng/cột quan hệ mới. Bộ trường nghiệp vụ đã chốt gồm độ tuổi, môn/chủ đề học tập, chủ đề, bối cảnh, thời lượng, mùa, địa điểm, thiết bị/vật liệu, khả năng tiếp cận và an toàn. Schema hiện có đã biểu diễn tuổi bằng `age_band`/`age_months`, môn/chủ đề học qua `area`/`objective_ids`, thời lượng bằng `duration_minutes`, thiết bị/vật liệu bằng `material_groups` hoặc `material_group_ids`, bối cảnh bằng `prepared_environment_vi` trong golden activity và an toàn bằng `safety`. Schema hiện chưa có trường rõ ràng cho theme, season, location hoặc accessibility; cần bổ sung các thuộc tính có kiểu vào một version mới của contract activity trước khi dựa vào chúng để lọc catalog. Giữ nguyên provenance và review của version; không coi văn bản tự do trong `body_json` là taxonomy đã chuẩn hóa.

### 4.2 Chủ sở hữu canonical, projection và quy tắc chống trùng trạng thái

| Dữ kiện/trạng thái | Chủ sở hữu ghi canonical | Projection/tham chiếu được phép | Quy tắc đối soát |
|---|---|---|---|
| Danh tính Firebase và scope tài khoản ứng dụng loại trừ lẫn nhau | BE1 `be1_adult_identities` khóa theo issuer + UID đã xác minh, có `account_scope` | `be1_organization_assignments` lưu vai trò Teacher/admin trong tổ chức; bảng Parent lưu tham chiếu principal Parent opaque | Unique issuer/UID và một giá trị scope ngăn principal vừa là Parent vừa là Teacher. Chỉ server cấp scope khi provision; không tin claim từ client. Danh tính hiện có vẫn được xem là legacy/Teacher đến khi xác minh rõ ràng. |
| Hồ sơ Parent và revision | Parent `child_profiles` + `profile_revisions` bất biến | Story lưu tham chiếu hồ sơ/revision và snapshot context được người lớn duyệt | Sửa hồ sơ thêm revision và cập nhật con trỏ head hiện tại trong cùng transaction. Không có liên kết giáo viên/tổ chức. |
| Revision hồ sơ Teacher | Các hàng BE1 `profile_revisions` | Trường display/age/revision hiện tại trong `be1_managed_profiles` là projection head | Revision là nguồn chuẩn cho giá trị cá nhân hóa. Cập nhật trường head trong cùng transaction; story/run không lưu thêm hồ sơ mutable thứ hai. |
| Membership lớp Teacher hiện tại | Hàng active trong BE1 `be1_enrollments` | `be1_managed_profiles.class_id` là projection lớp hiện tại; giao diện roster có thể cache giá trị này | Quy tắc partial unique cho phép mỗi trẻ có tối đa một enrollment active. Tạo/chuyển lớp/đối soát cập nhật cả hai trong một application transaction. |
| Nguồn dữ liệu trẻ và ủy quyền xử lý dữ liệu thật | `data_origin` cùng record ủy quyền Parent/BE1 cho dữ liệu thật | Trường `consent_id`/purpose trên hồ sơ quản lý là projection tương thích tùy chọn | `SYNTHETIC_TEST` không có consent record hoặc tham chiếu giả. `LEGACY_UNCLASSIFIED` không bao giờ được xem là đã consent. Chặn xử lý dữ liệu thật cho đến khi có policy riêng được duyệt. |
| Trẻ trong Story, actor và lifecycle run | Actor có kiểu và đúng một tham chiếu hồ sơ trong `story.runs` | `ai_jobs.job` chỉ lưu target-kind/ref có discriminator; không có bảng subject-ref lặp lại StoryRun | Khi tạo/hoàn tất story job, resolve một profile từ StoryRun canonical và đối chiếu revision/hash. Từ chối target lạ, lệch hoặc batch. Sketch job chỉ mang occurrence/plan/deck target refs và không có child subject. |
| Teacher Sketch Deck revision và nội dung trình chiếu | Lesson `sketch_deck_revisions` + `sketch_deck_steps` | Core Asset metadata/lineage giữ byte/hash; `ai_jobs.job` chỉ giữ target ref/revision | Deck pin một approved plan hash và bao quát mọi activity. Mỗi hướng dẫn nhóm line-sketch 3–5 bước. Regenerate tạo revision mới; plan edit làm deck stale. Không gắn hồ sơ trẻ, tranh trẻ hoặc video quota. |
| Nhận diện tranh và Character Bible | `story.understanding_revisions.visual_anchors` là bộ neo nhận diện có version gắn với đúng một tranh/run | `story.story_scenes.character_anchor_ref` chọn neo dùng ở scene; Core Asset metadata/lineage giữ ảnh tham chiếu đã chuẩn bị | Character Bible trong V1 là cấu trúc neo nhận diện thuộc revision VLM đã kiểm schema, không phải bảng vật lý riêng. Ảnh dẫn xuất có asset ref/hash/lineage riêng; không thay tranh gốc hoặc trộn tranh/trẻ khác. |
| Revision Story và số lần viết lại | `story.story_revisions` bất biến | `story.runs.current_story_revision_ref` là con trỏ head; `aggregate_revision` của run chỉ dùng concurrency | Suy ra số lần viết lại từ revision Story bất biến và giới hạn trong transaction ở một bản đầu + ba lần viết lại. Không lưu thêm `rewrite_count`. |
| Request tạo video đầy đủ, giới hạn request và kết quả hiện có thể phát | Các hàng intent/admission/result bất biến `story.video_generations` | `story.runs.current_video_generation_ref` trỏ đến kết quả mới nhất đã qua kiểm tra an toàn và có thể phát | Tạo intent có idempotency key trước admission. Chỉ khi compute budget receipt của AI Policy và quota usage receipt của Billing đã xác nhận thì chuyển `ADMISSION_PENDING` → `ACCEPTED`, cấp generation number, chiếm một trong ba request/run và ghi outbox trước dispatch. Admission bị từ chối giữ metadata trạng thái `ADMISSION_REJECTED`, không tạo AI job/quota usage và không tiêu request cap. Receipt mơ hồ được reconcile bằng cùng request key; không dispatch hai lần. Mỗi accepted request vẫn tính nếu sau đó thất bại hoặc bị chặn an toàn. Retry scene không tiêu thụ đơn vị khác. Không tạo trường `video_generation_count` trùng lặp. |
| Trạng thái scene và lịch sử retry provider | Scene job trong `ai_jobs.job` cùng `ai_jobs.attempt`/`job_events` | `story.video_generation_scenes` lưu một hàng scene, tham chiếu job và trạng thái scene | Bảng attempt là sổ retry duy nhất. Hàng scene không lưu `attempt_no` hoặc `technical_retry_no`. Mỗi scene tối đa một lần inference ban đầu + hai retry tự động. |
| Tiến độ job, kết quả và asset đầu ra | Lịch sử ghi nối tiếp `ai_jobs.job_events`; projection trạng thái hiện tại `ai_jobs.job`; receipt completion giữ disposition/hash | Trạng thái phát Redis/RQ là tạm thời; trường JSON legacy giữ cho job cũ | Story/Sketch job mới để `history`, `result_refs` và `subject_refs` legacy rỗng; event rows ghi tiến độ, aggregate đích nhận kết quả bằng completion command. Target-kind phân biệt StoryRun với Lesson Sketch Deck. |
| Asset, byte, upload-session receipt và lineage | Core `core_asset_metadata` là metadata canonical cho asset hoàn tất/đang kiểm định; `core.upload_sessions` và `core.upload_parts` sở hữu session/receipt/expiry; `core.asset_lineage` sở hữu cạnh nguồn-phái sinh; MinIO riêng tư giữ byte theo object | Story/Lesson aggregate chỉ giữ asset ref/version; AI Job giữ completion disposition, không sở hữu output assets | Không sao chép hash/type/byte vào Story/Lesson/job. Mỗi application chunk 4 MiB là object PutObject riêng, không phải S3 multipart. Finalize sau assemble, aggregate hash, media validation và AV CLEAN; exact client-version semantics là OI-18 POC. |
| Domain event Core và dispatch AI | `core_outbox_events` cho domain event do Core sở hữu; `ai_jobs.outbox` cho envelope dispatch AI | Redis/RQ nhận bản sao để chuyển phát | Mỗi event chỉ có một outbox sở hữu. Consumer có version và idempotent ghi receipt; không ghi độc lập cùng event vào cả hai outbox. |
| Slot video mẫu của occurrence Teacher và xác nhận projection lớp | Lesson `occurrences.sample_slot_state`, `sample_claimed_at` và các trường xác nhận projection theo occurrence | `successful_sample_run_ref` là con trỏ tiện ích khi run còn tồn tại; Story lưu tham chiếu occurrence | Lesson giữ slot nguyên tử khi video playable đầu tiên của run được chấp nhận. Tạo lại chất lượng vẫn thuộc cùng run. Run lỗi trước claim đầu thì slot còn trống. Sau claim đầu, slot không mở lại dù video bị từ chối/ẩn, regeneration thất bại/hết lượt, run bị xóa/hủy hay Teacher đổi; không có recovery run. Khi xóa, xóa con trỏ run/media nhưng giữ claim đã dùng. Xác nhận projection lớp của Teacher phụ trách được ghi riêng theo occurrence; đây không phải duyệt video và không cấp quyền truy cập thành viên lớp dài hạn. |
| Entitlement và product quota usage | Billing `video_quota_grants` + `video_quota_usage` | Story request giữ opaque quota-admission/usage ref; AI Policy resource tables chỉ giữ GPU/compute reservation/metering | Scope Parent là Parent account; Teacher là organization. Orchestration dùng một idempotency boundary nhưng không có transaction SQL cross-module: AI Policy tạo compute reservation có lease/expiry theo request key, sau đó Billing kiểm tra grant và ghi một usage unit trong transaction của Billing trước dispatch. Nếu Billing từ chối, reservation được release; nếu timeout/crash làm admission mơ hồ, reconciler đọc receipt ở hai owner bằng cùng key, dọn reservation mồ côi sau lease và không dispatch trùng. Chỉ sau khi cả hai admission được xác nhận mới tạo/dispatch accepted generation. Không SQL cross-module/join private table. Mọi request đã nhận kể cả technical/provider/safety failure không hoàn; request bị từ chối trước admission không tiêu thụ; scene retry không phải request mới. Included tháng hiện tại trước top-up FIFO; included hết hạn cuối tháng, top-up carry-forward; giữa tháng nhận đủ included. Ledger không có child/run/media content; xóa run vẫn giữ metadata ledger. Không có mutable balance. |
| Phân quyền Teacher theo lớp | Assignment BE1 và `story.runs.active_owner_teacher_id`/owner epoch của Story | Transfer saga có versioned BE1/Story receipts; `created_by_actor_ref` giữ nguyên provenance | BE1 fence Teacher cũ khi vào pending; Story chuyển owner/unique lock trong transaction riêng; BE1 finalize sau receipt. Conflict mục tiêu gây compensation hoặc pending reconciliation. Không hủy job hợp lệ chỉ vì đổi Teacher; completion kiểm tra cùng org/class/occurrence/profile và hash input/script hiện hành, không dựa vào creator. Playback luôn tái phân quyền theo assignment/owner hiện tại. |
| Lifecycle scratch Modal synthetic | `ai_jobs.attempt` + `ai_jobs.job_events`; asset provenance ở `core.asset_lineage` | Attempt giữ opaque scratch/attempt ref, manifest hashes, cleanup state/receipt | Mỗi prefix Modal gắn với đúng một attempt, được xác minh SHA-256 và purge khi kết thúc; orphan sweeper xóa scratch không còn tham chiếu sau 24 giờ. Không tạo copy registry song song; real-data transfer yêu cầu gate/thiết kế riêng. |
| Sức chứa tổ chức và các lớp được chọn để tạm ngưng | Subscription/capacity period Billing và `subscription_events` ghi nối tiếp | `be1_classrooms.state` là projection các event tạm ngưng có lịch/đã hiệu lực theo lớp | Mỗi lớp được chọn có một event riêng, chung change-group ID và thời điểm hiệu lực chính xác. Projection BE1 được xử lý idempotent và đối soát với nhóm event. Không lưu danh sách lớp không giới hạn trong một trường JSON. |
| Nội dung catalog và policy AI | `ai_policy.version` và `learning_content.version` | Job/run ghim ID/hash version | Sổ review và activation nội dung/policy là nguồn chuẩn; snapshot job là tham chiếu bất biến, không phải bản sao có thể sửa. |
| Trạng thái thanh toán và chuyển phát thông báo | Event payment/invoice/subscription của Billing; inbox/lần gửi của Notifications | Redirect từ provider chỉ có tính thông tin | Xác minh chữ ký event provider và loại trùng trước khi đổi sức chứa. Retry gửi notification không được thay đổi trạng thái invoice hoặc subscription. |

#### Mở rộng scope cho hàng Parent trong các bảng nền tảng được giữ lại

Các khai báo persistence BE1/AI Job/Core hiện lấy tổ chức làm trung tâm. Dữ liệu Parent mới tuyệt đối không dùng ID tổ chức giả. Với bản ghi dùng xuyên vai trò trong `core_asset_metadata`, `core_audit_entries`, `core_outbox_events`, cả bảy bảng `ai_jobs` có ngữ cảnh owner/dispatch và các sổ tài nguyên/bản sao AI Policy liên quan, mô hình đích bổ sung `owner_scope_kind` và `owner_scope_ref` có kiểu; `organization_id` legacy vẫn có giá trị cho hàng cũ/Teacher và chỉ trở thành nullable ở nơi cần cho dữ liệu Parent sở hữu. Scope Parent định danh tài khoản Parent đã xác minh; scope organization định danh tổ chức. Sổ event/bản sao dùng chung cũng có thể dùng scope GLOBAL tường minh nếu contract sở hữu cho phép.

Khóa chính tổng hợp hiện tại của `ai_jobs.command_receipt` cần chuyển đổi tương thích trước khi hỗ trợ idempotency cho Parent: bổ sung receipt ID thay thế và unique theo owner scope có kiểu, backfill các hàng cũ sang scope ORGANIZATION, dual-read/write khi caller cũ còn hoạt động, rồi chuyển khóa ứng dụng sau khi đối soát tương đương. Giữ các cột/ràng buộc unique cũ cho đến khi chủ sở hữu phê duyệt dọn dẹp sau này. Cách làm này giữ hàng hiện có nhưng không có nghĩa migration chỉ bổ sung.

`ai_jobs.job.session_id`, `subject_refs`, `result_refs` và `history`, cùng `core_asset_metadata.source_refs`, giữ nguyên ý nghĩa đối với bản ghi legacy. Job mới dùng target-kind/ref có version để gắn đúng một StoryRun, Lesson Sketch Deck hoặc Parent Sketch Guide; Story job có target StoryRun đơn trị và resolve một profile từ run, Teacher Sketch job gắn occurrence/plan/deck refs, Parent guide target chỉ giữ generic topic/difficulty và không có child subject. `ai_jobs.job_events` là nguồn chuẩn cho tiến độ; Teacher deck output refs thuộc Lesson aggregate; Parent guide trả private Core Asset tạm có expiry/lineage, được purge theo lifecycle và không thuộc profile/StoryRun. Completion receipt chỉ giữ disposition/hash. Mảng JSON legacy mới để rỗng. Không bao giờ diễn giải lại mảng cũ như thể chúng mô tả run mới chỉ có một trẻ.

## 5. Từ điển bảng đích mới (40)

Phần sau là từ điển dữ liệu logic đích. Từ điển nêu chủ sở hữu bảng, kiểu khóa/tham chiếu, dữ liệu chính, ràng buộc và lifecycle. Tên trường là tên thiết kế logic, không phải DDL có thể thực thi. Mọi ID đều opaque. Mỗi revision bất biến ghi nhận actor và timestamp. Mọi bảng chứa nội dung nằm trong lifecycle xóa của module sở hữu bảng đó.

### 5.1 Asset lineage và upload-resume Core (3)

| Bảng | Khóa và tham chiếu | Trường logic | Ràng buộc và mục đích |
|---|---|---|---|
| core.asset_lineage | PK lineage_id; composite FK source_asset_ref/version và derived_asset_ref/version tới `core_asset_metadata`; story_run_ref/job_ref tùy chọn là opaque | transform_kind, transform_version, model_profile_ref, config_hash, actor_ref, reason_code, created_at | Ghi provenance từ bản gốc đến bản phái sinh mà không lưu dữ liệu nhị phân. Hash/loại media/kích thước byte vẫn canonical trong `core_asset_metadata`, không sao chép tại đây. Cạnh version nguồn/phái sinh unique. `derived_from_ref`/`source_refs` cũ trong metadata chỉ đọc sau chuyển đổi; ghi mới chỉ vào lineage để không có hai nguồn chuẩn. |
| core.upload_sessions | PK upload_session_id; owner principal/scope ref có kiểu; target ref opaque; idempotency key hash; finalized asset composite FK tùy chọn tới `core_asset_metadata` | purpose (PROFILE_IMAGE, RUN_ARTWORK, RUN_AUDIO, LESSON_SOURCE), expected_media_type, expected_size_bytes, expected_sha256, chunk_size_bytes=4194304, state, expires_at, finalized_asset_ref/version_optional, created_at, completed_at, aborted_at | Nguồn chuẩn bền vững cho phiên upload-resume. Ràng buộc actor/scope/purpose bất biến; max 3 session active/principal theo cấu hình; unique idempotency per actor/scope. Không lưu binary, credential hoặc URL storage. Chỉ `COMPLETED` session mới trả asset ref dùng được; expiry/abort chuyển lifecycle purge các chunk objects idempotent. |
| core.upload_parts | PK upload_part_id; FK nội bộ upload_session_id | part_number, byte_size, sha256, storage_object_ref, state, received_at | Mỗi application chunk ≤4 MiB là object riêng qua PutObject; unique `(upload_session_id, part_number)`. Cùng số/hash là idempotent; cùng số/hash khác trả conflict. Lưu receipt/hash/size/ref, không lưu byte. Backend chỉ finalize khi part number liên tục từ 1, tổng bytes/hash khớp expected và media/AV validation đạt. Đây không phải S3 Multipart Upload API. |

### 5.2 Tiến trình AI job bền vững (1)

| Bảng | Khóa và tham chiếu | Trường logic | Ràng buộc và mục đích |
|---|---|---|---|
| ai_jobs.job_events | PK event_id; FK nội bộ job_id; unique `(job_id, event_sequence)` | event_sequence, event_type, from_state, to_state, stage, attempt_no, safe_error_code, retryable, contract_version, expected_revision, occurred_at | Luồng trạng thái/audit append-only gắn với đúng một AI job. Không chứa request body, prompt, transcript hoặc credential provider. Bảng `ai_jobs.job` sở hữu target-kind/ref có discriminator; chỉ StoryRun target có một hồ sơ trẻ, Lesson Sketch target không có profile. Không có bảng subject riêng vì nó lặp lại quan hệ target. Kết quả được lưu tại aggregate Story/Lesson; `ai_jobs.completion_receipt` chỉ lưu disposition/hash để xử lý idempotent, không sao chép danh sách asset. |

### 5.3 Quyền sở hữu và context hồ sơ Parent (5)

| Bảng | Khóa và tham chiếu | Trường logic | Ràng buộc và mục đích |
|---|---|---|---|
| parent.child_profiles | PK parent_profile_id; chủ sở hữu người lớn là tham chiếu principal Firebase đã xác minh | state, created_at, updated_at, deleted_at, current_revision_ref | Tài khoản Parent là chủ sở hữu duy nhất. Bảng gốc chỉ giữ identity/lifecycle và con trỏ revision hiện hành; không lặp tên/tuổi/sở thích đã thuộc profile revision. Không có FK/liên kết đến hồ sơ Teacher và không chia sẻ trong gia đình. |
| parent.profile_revisions | PK profile_revision_id; FK nội bộ parent_profile_id | revision_no, age_months, age_band, display_name, interests_summary, authored_by, created_at, revision_hash | Snapshot hồ sơ bất biến; không có trường ngày sinh chính xác. Cặp profile/revision phải unique. Sửa hồ sơ tạo revision mới. |
| parent.profile_context_entries | PK context_entry_id; FK nội bộ parent_profile_id | entry_kind (OUTSIDE_EXPERIENCE, ACHIEVEMENT, OBSERVATION), short_text, source_kind, source_ref_optional, approximate_date, created_by, created_at | Các sự kiện/quan sát do người lớn nhập gắn với hồ sơ ổn định, không gắn vào từng revision profile. Lịch sử app được truy vấn từ Story và chỉ chọn vào snapshot run khi cần; không nhập lại như context thủ công. Văn bản có giới hạn và loại nhạy cảm bị chặn. |
| parent.profile_support_needs | PK support_need_id; FK nội bộ parent_profile_id | support_category, encrypted_note, visibility_scope, authored_by, created_at, updated_at | Nhu cầu hỗ trợ do người lớn nhập, quyền truy cập bị giới hạn; không phải chẩn đoán và mặc định loại khỏi AI context. Tách riêng để áp dụng quyền/mã hóa hẹp; chỉ truy cập qua phân quyền hồ sơ. |
| parent.data_authorizations | PK authorization_id; FK nội bộ parent_profile_id; actor người lớn là principal ref | purpose_code, policy_version, state, source_kind, recorded_at, revoked_at, evidence_ref, synthetic_demo_flag | Lifecycle mục đích/ủy quyền dùng dữ liệu thật. Demo tổng hợp không cần UI consent thật và không được coi là bằng chứng xử lý dữ liệu trẻ thật. Chặn run dữ liệu thật mới đến khi có policy riêng được duyệt. |

### 5.4 Mở rộng revision/context hồ sơ Teacher (3)

| Bảng | Khóa và tham chiếu | Trường logic | Ràng buộc và mục đích |
|---|---|---|---|
| be1.profile_revisions | PK profile_revision_id; FK nội bộ managed_profile_id | revision_no, age_months, age_band, display_name, structured_interests, authored_by, created_at, revision_hash | Version bất biến canonical của thuộc tính hồ sơ Teacher do tổ chức sở hữu; ID hồ sơ unique và tên hiển thị được phép trùng. Quan sát/thành tích có ngày thuộc context entries, không lặp ở đây. Không lưu ngày sinh chính xác; tuổi 36–155 tháng. |
| be1.profile_context_entries | PK context_entry_id; FK nội bộ managed_profile_id | entry_kind (OUTSIDE_EXPERIENCE, ACHIEVEMENT, OBSERVATION), short_text, source_kind, source_ref_optional, approximate_date, authored_by, created_at | Dữ liệu có ngày do người lớn nhập, gắn với hồ sơ ổn định thay vì revision; lịch sử app được truy vấn từ Story và không nhập trùng. Giữ nguồn và nhóm; không suy luận chẩn đoán. |
| be1.profile_support_needs | PK support_need_id; FK nội bộ managed_profile_id | support_category, encrypted_note, visibility_scope, authored_by, created_at, updated_at | Ghi chú nhu cầu hỗ trợ hạn chế quyền truy cập do người lớn nhập; không chẩn đoán, mặc định loại khỏi AI context. Vai trò roster của admin tổ chức không cấp quyền xem nội dung này. |

Parent và Teacher dùng các chủ sở hữu vật lý riêng để giữ ranh giới truy cập. Có thể tái sử dụng khái niệm chung và hình dạng API dưới dạng contract có version, nhưng không tạo khóa ngoại/liên kết hồ sơ chéo chủ sở hữu.

### 5.5 Nguồn giáo án, occurrence, kế hoạch và deck AI Sketch (7)

| Bảng | Khóa và tham chiếu | Trường logic | Ràng buộc và mục đích |
|---|---|---|---|
| lesson.occurrences | PK occurrence_id; organization_ref, class_ref và responsible_teacher_ref opaque | title, scheduled_date_optional, state, created_by, created_at, approved_plan_revision_ref, sample_slot_state, successful_sample_run_ref_optional, sample_claimed_at, class_projection_confirmed_by_ref_optional, class_projection_confirmed_at_optional | Một occurrence dạy học, không phải runtime session cộng tác. Có một plan revision đã duyệt. `sample_slot_state` và thời điểm claim là canonical; run lỗi trước playable claim đầu không dùng slot. Sau claim đầu, slot giữ nguyên kể cả video bị từ chối/ẩn, mọi lần tạo lại thất bại/hết lượt, run bị xóa/hủy hoặc Teacher đổi; không tạo sample run phục hồi. Xóa chỉ xóa con trỏ run/media, giữ claim metadata. Teacher phụ trách hiện tại ghi xác nhận projection riêng theo occurrence; admin không có quyền media mặc định. |
| lesson.source_documents | PK source_document_id; FK nội bộ `occurrence_id`; `asset_ref/version` và `upload_session_ref` là typed cross-owner refs | safe_file_name, file_extension, document_state, page_or_slide_count, uploaded_by, uploaded_at, deleted_at | Chỉ nhận PDF/PPTX/DOCX; giới hạn 25 MB và 100 trang/slide; từ chối file mã hóa/có password; file gốc bất biến cho đến khi lifecycle xóa. Media type, byte size và SHA-256 chỉ thuộc Core Asset; upload state/part receipt thuộc Core Upload Session. |
| lesson.document_revisions | PK document_revision_id; FK nội bộ source_document_id | revision_no, extracted_text, extracted_text_hash, parser_name/version, extraction_warnings, page_coverage, review_state, reviewed_by, reviewed_at | Văn bản trích xuất/đã chỉnh sửa là bất biến. Không OCR trang scan. Teacher sửa tạo revision mới; plan tham chiếu chính xác một revision. |
| lesson.plan_revisions | PK plan_revision_id; FK nội bộ `occurrence_id`; FK nội bộ tùy chọn `source_document_revision_id` | revision_no, objective, teacher_direction, safety_notes, state, created_by, created_at, approved_by, approved_at, content_hash | Mỗi occurrence có một aggregate plan với các revision bất biến. Phải duyệt plan trước khi chọn trẻ/bắt đầu tạo story. |
| lesson.plan_activities | PK plan_activity_id; FK nội bộ plan_revision_id; catalog_activity_ref opaque tùy chọn | activity_kind, activity_version, custom_title, custom_description, safety_checklist_version, checklist_result, confirmed_by, confirmed_at, activity_snapshot_hash | Một plan có thể chứa nhiều hoạt động. Hoạt động riêng chỉ dùng cho occurrence đó và cần Teacher phụ trách hoàn tất checklist an toàn. Mỗi Teacher run ghim một hoạt động. Hoạt động Parent tự tạo không dùng bảng này; catalog Parent vẫn phải được duyệt toàn cục. |
| lesson.sketch_deck_revisions | PK sketch_deck_revision_id; FK nội bộ `occurrence_id` và `plan_revision_id` | revision_no, plan_content_hash, target_age_band, deck_schema_version, state, model_profile_ref/version, prompt_template_version, config_hash, compute_reservation_ref opaque, content_hash, created_by, created_at, ready_at, superseded_at | Một deck revision bất biến cho occurrence, dùng chung cho lớp và pin chính xác plan revision/hash đã duyệt. Không có child/profile/tranh trẻ reference. State gồm GENERATING, READY, FAILED, STALE, SUPERSEDED. Plan đổi làm deck STALE; chỉ deck READY trên hash hiện hành được trình chiếu. Regenerate tạo revision mới, không sửa revision cũ. AI compute/cost ghi qua AI Policy receipt; không tạo video quota usage. |
| lesson.sketch_deck_steps | PK sketch_deck_step_id; FK nội bộ sketch_deck_revision_id và plan_activity_id tùy chọn; line_sketch_asset_ref/version opaque tới Core; source_job_ref opaque | `instruction_group_key`, `step_index`, `step_kind`, `subject_key`, `short_title`, `child_facing_prompt`, `teacher_explanation`, `bounded_layout_hints`, `state`, `created_at` | Một hàng là một nội dung/bước trình chiếu; các line-sketch được nhóm bằng `instruction_group_key`, thứ tự `step_index`, mỗi nhóm hướng dẫn READY phải có 3–5 bước tăng dần. Mỗi hoạt động trong plan phải được bao quát; activity ref phải thuộc plan revision đã pin. Core Asset sở hữu hash/type/size và lineage; không lặp hash trên bước. Regenerate tạo deck revision mới; Next/Back/skip không persist. Không lưu slide binary, profile trẻ hay prompt/provider raw trong bảng. |

### 5.6 Story run, input/context, rà soát và video (9)

| Bảng | Khóa và tham chiếu | Trường logic | Ràng buộc và mục đích |
|---|---|---|---|
| story.runs | PK story_run_id; creator/actor ref; đúng một tham chiếu hồ sơ Parent hoặc Teacher opaque; occurrence/class refs tùy chọn | actor_role, owner_scope_kind/ref, profile_kind/ref, current_run_input_ref, activity_ref/version, lesson_plan_revision_ref, state, aggregate_revision, current_story_revision_ref, current_video_generation_ref, run_kind, `created_by_actor_ref`, `active_owner_parent_account_id` XOR `active_owner_teacher_id`, `owner_epoch`, `assignment_version`, started_at, last_meaningful_activity_at, adult_wait_started_at, finished_at, deleted_at | Thực thi XOR giữa hồ sơ Parent/Teacher. Parent không có tham chiếu org/class/lesson; Teacher cần lớp được phân quyền, occurrence, plan đã duyệt và đúng một trẻ. Chỉ một activity scalar. Profile revision và snapshot nằm trong input revision hiện hành, không lặp ở run. Partial unique index khóa run chưa đóng theo current owner field, không theo creator; DRAFT và admission pending vẫn giữ khóa. AI job đang hoạt động không phải adult-wait; `adult_wait_started_at` bắt đầu khi job kết thúc/lỗi và cần thao tác người lớn. Tại +144 giờ gửi inbox/push/email best-effort; tại +168 giờ VIDEO_READY→COMPLETED, adult-wait khác→ABANDONED; cả hai nhả khóa nhưng giữ nội dung đến khi người dùng xóa. Reassignment chuyển owner qua saga BE1/Story và thu hồi quyền creator cũ; `created_by_actor_ref` chỉ là provenance. Hủy người dùng chuyển DELETE_PENDING và xóa nội dung theo lifecycle. |
| story.run_inputs | PK run_input_id; FK nội bộ story_run_id; unique `(story_run_id, input_revision)` | input_revision, drawing_asset_ref/version, typed_idea, voice_asset_ref/version, idea_source, source_profile_revision_ref, context_schema_version, approved_context_snapshot_jsonb_bounded, context_snapshot_hash, input_confirmed_by, input_confirmed_at, created_at | Một revision bất biến gom các đầu vào được gắn với cùng lần lập story: tranh, ý tưởng/transcript đã xác nhận, profile revision và context tối thiểu đã được người lớn duyệt. JSONB chỉ chứa danh sách nhỏ đã validate, allowlist, có version/hash/giới hạn; không phải kho profile hay run history. App history được đọc từ Story; context nhập tay vẫn thuộc Parent/BE1 profile-context entries. Hash/loại media/kích thước byte canonical trong Core Asset. Audio tối đa 2 phút/20 MB; không batch. |
| story.transcript_revisions | PK transcript_revision_id; FK nội bộ run_input_id | revision_no, raw_transcript, adult_corrected_text, language, ASR_profile_ref, model_revision, config_hash, segment_timing_optional, state, reviewed_by, reviewed_at | Lưu Whisper gốc và bản người lớn sửa theo revision của đúng input. Bắt buộc người lớn xác nhận trước khi lập story. Xóa cùng lifecycle run. |
| story.understanding_revisions | PK understanding_revision_id; FK nội bộ run_input_id | revision_no, source_asset_ref/version, VLM_profile_ref, model_revision, config_hash, structured_subjects, entities, setting, visual_anchors, uncertainty, state, created_at, confirmed_by, confirmed_at | Kết quả VLM được kiểm tra schema và gắn với chính xác version asset input bất biến. Hash asset canonical trong Core Asset. Người dùng sửa thì tạo revision VLM mới; không sửa kết quả cũ. |
| story.story_revisions | PK story_revision_id; FK nội bộ run_input_id | revision_no, rewrite_index, story_title, story_arc_json, target_duration_seconds, locale, prompt_template_version, model_profile_ref, model_revision, content_hash, state, created_at | Một story ban đầu và tối đa ba lần viết lại. Scene count/nội dung canonical trong `story_scenes`; không sao chép mảng scene hoặc số lượng tại đây. Kiểm tra 5–15 scene và thời lượng hệ thống 30–90 giây. Bất biến; revision cũ ẩn khỏi UI thông thường. |
| story.story_scenes | PK scene_id; FK nội bộ story_revision_id; unique `(story_revision_id, scene_id)` | scene_index, duration_seconds, action_summary, validated_generation_prompt_ref, narration_segment, character_anchor_ref, state, created_at | Các hàng scene/storyboard canonical, unique theo revision/scene_index và composite key revision/scene. Lưu cấu trúc scene có giới hạn; không sao chép payload prompt gửi provider vào log. Hồ sơ trẻ vẫn là tham chiếu scalar trên run. |
| story.review_decisions | PK decision_id; FK nội bộ `story_run_id`; XOR FK nội bộ `target_run_input_id`/`target_story_revision_id` | stage, decision, actor_ref, actor_role, target_run_input_id_optional, target_story_revision_id_optional, target_hash, safe_reason_code, suggestion_ref_optional, created_at, idempotency_key | Stage gồm transcript, subject, hoạt động/context và xác nhận kịch bản. Xác nhận kịch bản là cổng duyệt rõ ràng duy nhất trước khi tạo video. Không có trạng thái video-approved. Mỗi quyết định trỏ đúng revision input/story và hash đã được xem. |
| story.video_generations | PK video_generation_id; FK nội bộ story_run_id và story_revision_id; unique `(video_generation_id, story_revision_id)` | generation_no (null until accepted), generation_kind (INITIAL or QUALITY_REGEN), state (ADMISSION_PENDING, ADMISSION_REJECTED, ACCEPTED, QUEUED, GENERATING, TECHNICAL_VALIDATING, SAFETY_VALIDATING, READY, SAFETY_BLOCKED, FAILED, REJECTED_BY_ADULT, SUPERSEDED), request_idempotency_key_hash, target_script_hash, compute_reservation_ref opaque, billing_quota_usage_ref opaque, output_asset_ref/version, video_profile_ref, model_revision, config_hash, technical_validation_state, consistency_validation_state, safety_validation_state, safety_policy_version, safety_finding_codes, admission_started_at/accepted_at/rejected_at, started_at, completed_at, safe_failure_code | Mỗi hàng là intent/request. Chỉ ADMISSION_PENDING sau cả hai receipt compute-budget AI Policy và quota Billing mới thành ACCEPTED; chỉ accepted rows chiếm một trong ba request/run, có generation number, AI jobs/outbox và đúng một Billing usage row. Budget/quota rejection để lại ADMISSION_REJECTED metadata nhưng không chiếm request cap/quota và không dispatch. Admission mơ hồ được đối soát bằng request idempotency key; reservation chưa gắn với Billing usage được release/expire, reservation accepted được giữ đến settle/job completion. Mỗi accepted request tiêu thụ quota kể cả lỗi kỹ thuật/provider/an toàn. Mỗi request cần kịch bản đã xác nhận trước dispatch. Retry scene không tạo usage mới. Hash/metadata media output nằm trong Core Asset. Chỉ output đầu tiên qua kiểm tra an toàn và có thể phát mới claim slot occurrence; claim không mở lại khi quality regeneration lỗi/hết lượt. Không duyệt video cuối bởi người. |
| story.video_generation_scenes | PK generation_scene_id; FK `(video_generation_id, story_revision_id)` tới `(video_generation_id, story_revision_id)` của `video_generations`; FK `(story_revision_id, story_scene_id)` tới `(story_revision_id, scene_id)` của `story_scenes`; unique (video_generation_id, story_scene_id) | story_revision_id (constraint key, immutable), state, clip_asset_ref/version, source_job_ref, consistency_result_code_optional, safe_failure_code, started_at, completed_at | Hai composite FK buộc storyboard scene thuộc đúng revision đã pin trên generation. `story_revision_id` lặp có chủ đích làm khóa integrity, không phải source có thể sửa độc lập. `source_job_ref` trỏ job target `VIDEO_GENERATION_SCENE` theo contract, và job output về scene được Story owner xác minh. Không tạo asset-result/helper table, bộ đếm attempt hoặc metadata media trùng; `ai_jobs.attempt` là retry ledger duy nhất, Core Asset sở hữu hash/type/byte. |

### 5.7 Billing sức chứa tổ chức và quota video (9)

| Bảng | Khóa và tham chiếu | Trường logic | Ràng buộc và mục đích |
|---|---|---|---|
| billing.price_versions | PK price_version_id | currency=VND, included_class_slots=10, base_monthly_amount, base_annual_amount, extra_slot_monthly_amount, extra_slot_annual_amount, parent_monthly_video_units_config, teacher_monthly_video_units_config, video_quota_add_on_price_config, effective_from/to, version, approved_by, created_at | Version thương mại/policy bất biến. Gói cơ bản trả phí gồm 10 slot lớp; slot thêm dùng một mức giá cấu hình theo kỳ. Số quota video và giá được cấu hình, chốt sau benchmark chi phí; thiết kế này không tự đặt bậc gói hoặc mức giá. |
| billing.organization_subscriptions | PK subscription_id; organization_ref và billing_admin_ref opaque; FK nội bộ price_version_id | provider, provider_customer_ref, provider_subscription_ref, billing_period, status, auto_renew, started_at, current_period_start/end, grace_until, cancellation_effective_at | Mỗi tổ chức chỉ có một subscription hiện hành tại một thời điểm. Subscription nối tới đúng version giá đã áp dụng. Adapter provider là MoMo hoặc VNPAY. Không lưu credential provider hoặc secret của phương thức thanh toán. |
| billing.capacity_periods | PK capacity_period_id; FK nội bộ subscription_id | period_start/end, included_slots, paid_extra_slots, prorated_amount, state, created_at | Snapshot các đầu vào của kỳ đã thanh toán. Sức chứa hiệu lực được suy ra từ slot bao gồm + slot mua thêm trừ event tạm ngưng từng lớp đã chọn; không lưu thêm số sức chứa hiệu lực hoặc danh sách lớp ở hàng này. Add-on có hiệu lực sau khi xác minh thanh toán và tính prorate phần còn lại mà không đổi ngày gia hạn. |
| billing.invoices | PK invoice_id; owner_scope_kind/ref có kiểu; FK nội bộ subscription_id tùy chọn | invoice_number, period_start/end, currency, subtotal, prorated_adjustment, total, status, due_at, paid_at, invoice_snapshot, created_at | Hỗ trợ invoice subscription tổ chức và giao dịch mua thêm quota video theo scope tài khoản Parent hoặc tổ chức. Lưu snapshot số tiền/kỳ/giá bất biến. Tiền tệ VND. V1 không tự hoàn phí slot lớp giữa kỳ. |
| billing.payment_attempts | PK payment_attempt_id; invoice_id FK nội bộ | provider, merchant_order_ref, provider_transaction_ref, request_id, amount, currency, status, idempotency_key, initiated_at, completed_at, safe_failure_code | Chỉ lưu metadata request/response provider; phải xác minh callback trước khi chuyển sang trạng thái paid. Unique request/merchant ref khi provider yêu cầu. |
| billing.provider_event_receipts | PK event_receipt_id; provider event unique; 0 hoặc 1 FK nội bộ trong `payment_attempt_id`/`subscription_id` | provider, provider_event_ref, signature_valid, payment_attempt_id_optional, subscription_id_optional, received_at, processed_at, processing_status, safe_error_code, payload_hash | Callback chưa xác minh hoặc chưa resolve target được lưu với cả hai FK rỗng; callback đã xác minh/xử lý phải nối đúng một attempt thanh toán hoặc subscription. Invoice resolve qua payment attempt. Không lưu secret thô/dữ liệu thẻ. Khử trùng callback trong transaction Billing. |
| billing.subscription_events | PK subscription_event_id; FK nội bộ subscription_id và invoice_id tùy chọn | event_type, from_state, to_state, capacity_change_group_ref_optional, affected_class_ref_optional, class_from_state_optional, class_to_state_optional, effective_at, actor_ref, safe_reason_code, created_at | Lịch sử subscription và sức chứa từng lớp chỉ ghi nối tiếp. Mỗi lớp bị tạm ngưng có một hàng, dùng chung change-group ref và thời điểm hiệu lực; các hàng theo lớp là nguồn chuẩn cho lựa chọn. Không lưu danh sách lớp JSON không giới hạn. |
| billing.video_quota_grants | PK quota_grant_id; owner_scope_kind/ref có kiểu; FK nội bộ price_version_id và invoice_id optional; source_event_receipt_id optional FK | grant_kind (MONTHLY_INCLUDED or PURCHASE), units_granted, quota_period_start/end_optional, expires_at_optional, source_event_receipt_id, granted_at, granted_by_optional | Các khoản entitlement quota video cấp cho tài khoản Parent hoặc tổ chức Teacher, chỉ ghi nối tiếp. Cấp đủ grant included tháng hiện tại cho scope đủ điều kiện bắt đầu giữa tháng, không prorate (Q121); grant included có `expires_at` ở cuối tháng dương lịch `Asia/Ho_Chi_Minh`. Top-up là one-time, không tự gia hạn, `expires_at` là null và carry-forward đến khi dùng hết (Q114, Q120, Q126). Admission bỏ grant included hết hạn, dùng grant included tháng hiện tại trước rồi top-up FIFO. `invoice_id` là nguồn invoice duy nhất; idempotency source event ngăn cấp trùng. Không lưu số dư còn lại mutable. |
| billing.video_quota_usage | PK usage_id; FK nội bộ quota_grant_id; request/generation ref opaque (không FK sang Story) | owner_scope_kind/ref, request_ref, idempotency_key_hash, units=1, accepted_at, source_contract_version | Ledger append-only: unique owner scope + full-video request/idempotency ref; insert idempotent trong transaction riêng do Billing sở hữu sau compute-reservation receipt và trước Story acceptance/dispatch. Đây không phải transaction với Story; application saga/reconciler nối các receipt. Mỗi accepted request tiêu thụ một unit, không hoàn/reverse khi technical/provider/safety fail, hủy hoặc xóa run. Request bị từ chối trước Billing commit không tạo row; retry scene không tạo row mới. Không lưu child/profile/run content, prompt hoặc media; vẫn giữ metadata sau khi run bị xóa. Số còn lại tính trong Billing từ grant hợp lệ trừ usage; không lưu mutable balance. |

Quy tắc Billing: subscription tổ chức trả phí có 10 slot lớp cơ bản; sức chứa bổ sung dùng một mức giá cấu hình cho mỗi slot theo tháng hoặc năm. Gia hạn thất bại có 7 ngày ân hạn, sau đó chặn tạo lớp và story run mới nhưng vẫn cho truy cập dữ liệu hiện có. Khi hạ gói phải chọn lớp tạm ngưng trước khi sức chứa mới có hiệu lực; dữ liệu lớp tạm ngưng ở chế độ chỉ đọc. Có thể tắt tự gia hạn; quyền đã trả tiền còn hiệu lực đến hết kỳ. Quota video tính theo tháng dương lịch `Asia/Ho_Chi_Minh`, tách biệt theo tài khoản Parent/tổ chức Teacher; cấp đủ grant included của tháng hiện tại khi bắt đầu giữa tháng. Grant included còn dư hết hạn cuối tháng; top-up FIFO carry-forward đến khi dùng hết. Billing sở hữu grants và usage ledger; mọi accepted request tiêu thụ unit không hoàn lại, request bị từ chối trước admission không tiêu thụ. Retry scene không tạo usage. Số included quota riêng theo Parent/Teacher và giá top-up được cấu hình sau synthetic cost benchmark.

### 5.8 Thông báo (3)

| Bảng | Khóa và tham chiếu | Trường logic | Ràng buộc và mục đích |
|---|---|---|---|
| notifications.inbox_items | PK inbox_item_id; tham chiếu người nhận người lớn opaque và organization ref tùy chọn | notification_type, template_version, safe_parameters, trigger_dedupe_key, created_at, read_at, expires_at_optional | Thông báo billing và thông điệp hệ thống trong ứng dụng. Không có nội dung trẻ. Khử trùng theo lịch/event thanh toán và người nhận. |
| notifications.delivery_attempts | PK delivery_attempt_id; FK nội bộ `inbox_item_id`; FK nội bộ tùy chọn `push_endpoint_id` | channel (EMAIL, IN_APP, WEB_PUSH, ANDROID_PUSH), push_endpoint_id_optional, destination_ref_optional, provider, attempt_no, state, safe_error_code, attempted_at, delivered_at, provider_message_ref | Retry có giới hạn; push/email là best-effort, inbox là nguồn chuẩn. Web dùng Web Push; Android dùng non-Firebase provider adapter sau POC. `destination_ref` là opaque ref tới notification identity adapter, không phải địa chỉ/email/token thô. Không lưu credential/raw endpoint trong log. |
| notifications.push_endpoints | PK push_endpoint_id; recipient actor ref opaque | platform_kind (WEB or ANDROID), provider_kind (WEB_PUSH or ANDROID_PROVIDER_TBD), endpoint_ciphertext, endpoint_fingerprint, state, registered_at, last_seen_at, revoked_at, app_version_optional | Một actor có thể có nhiều endpoint; unique fingerprint theo provider; endpoint/token mã hóa at rest, chỉ trả raw endpoint khi đăng ký, không log/telemetry. Thu hồi khi người dùng logout/unregister, provider báo invalid hoặc actor mất scope. Android provider chưa được chọn và chỉ quyết định sau synthetic POC; không dùng FCM/Firebase messaging theo quy tắc Firebase-Authentication-only. |

## 6. Quan hệ, liên kết và quyền sở hữu dữ liệu

Relationship catalogue này bao phủ toàn bộ 78 bảng active đích. FK/unique được dùng cho quan hệ trong cùng owner/schema; tham chiếu liên owner dùng typed ref có contract version và application port. Không dùng opaque ref để né một quan hệ cùng schema có thể được kiểm tra bằng FK. Mọi bảng active phải nối vào aggregate, ledger hoặc operational root của owner.

### 6.1 Quan hệ của 40 bảng mới

| Entity | Quan hệ trong cùng owner | Ref liên owner và lý do tồn tại |
|---|---|---|
| core.asset_lineage | Hai composite FK tới source và derived asset version trong core_asset_metadata; unique theo cặp asset-version và transform | Job/run ref tùy chọn có kiểu; giữ provenance nhiều nguồn mà derived_from_ref đơn không biểu diễn được |
| core.upload_sessions | Finalized asset tùy chọn FK tới core_asset_metadata | Target ref tới Parent/Story/Lesson qua upload purpose contract; giữ resume/expiry bền vững |
| core.upload_parts | FK upload_session_id; unique (upload_session_id, part_number) | Object ref qua storage adapter; từng phần có hash/size để retry idempotent |
| ai_jobs.job_events | FK job_id tới ai_jobs.job; sequence unique trong mỗi job | Stage/progress/error an toàn; không lặp attempts, result assets hoặc subject của aggregate đích |
| parent.child_profiles | Gốc hồ sơ; unique owner/profile key | Chủ sở hữu Parent là principal đã xác minh; độc lập với BE1/organization |
| parent.profile_revisions | FK parent_profile_id; unique (parent_profile_id, revision_no); profile trỏ revision hiện hành | Snapshot bất biến của tuổi, nhóm tuổi, tên hiển thị và sở thích |
| parent.profile_context_entries | FK parent_profile_id; index theo profile/date/kind | Sự kiện/quan sát người lớn nhập; app-run history đọc từ Story, không ghi lặp |
| parent.profile_support_needs | FK parent_profile_id; index theo profile/visibility | Tách riêng vì mã hóa/quyền xem nhạy cảm; loại khỏi AI mặc định |
| parent.data_authorizations | FK parent_profile_id; unique theo profile/purpose/policy/state lifecycle | Actor/evidence ref có kiểu; giữ bằng chứng ủy quyền đúng hồ sơ |
| be1.profile_revisions | FK managed_profile_id; unique (managed_profile_id, revision_no); profile trỏ revision hiện hành | Hồ sơ Teacher thuộc organization; Parent và Teacher không chia sẻ profile |
| be1.profile_context_entries | FK managed_profile_id; index theo profile/date/kind | Sự kiện/quan sát Teacher nhập; app-run history đọc từ Story |
| be1.profile_support_needs | FK managed_profile_id; index theo profile/visibility | Vùng quyền và mã hóa riêng; admin roster không mặc nhiên được xem |
| lesson.occurrences | Gốc một buổi; unique sample claim; current plan/deck pointers có ràng buộc version | Typed ref tới organization/class/Teacher BE1; assignment resolve qua BE1 port |
| lesson.source_documents | FK occurrence_id; unique asset version trong occurrence | Asset/upload refs tới Core; hash/type/size chỉ lấy từ Core Asset |
| lesson.document_revisions | FK source_document_id; unique (source_document_id, revision_no) | Văn bản trích xuất đã chỉnh tách khỏi file gốc bất biến |
| lesson.plan_revisions | FK occurrence_id và source_document_revision_id tùy chọn; unique (occurrence_id, revision_no) | Plan bất biến được duyệt; mọi ref thuộc Lesson owner |
| lesson.plan_activities | FK plan_revision_id; unique (plan_revision_id, activity_key) | Catalog activity là versioned ref tới Learning Content; custom activity thuộc plan |
| lesson.sketch_deck_revisions | FK occurrence_id và plan_revision_id; unique (occurrence_id, revision_no) | Compute reservation ref tới AI Policy; deck ghim plan hash được duyệt |
| lesson.sketch_deck_steps | FK sketch_deck_revision_id và FK plan_activity_id tùy chọn; unique group/index | Activity được kiểm tra trong Lesson transaction để thuộc đúng plan revision đã được deck ghim. Không lặp `plan_revision_id` ở từng step. Line-art asset/source-job refs tới Core/AI Jobs; step rows là output chuẩn, không có bảng result trung gian. |
| story.runs | Gốc run; current input/story/video pointers là projection có xác minh version; partial unique theo active owner | Chính xác một typed Parent/Teacher profile ref; Teacher occurrence/activity/plan refs qua Lesson contract; pointer chỉ được đổi trong aggregate transaction sau kiểm tra ownership |
| story.run_inputs | FK story_run_id; unique (story_run_id, input_revision); run trỏ current input | Core artwork/audio refs và Parent/BE1 profile revision ref; bounded context snapshot nằm cùng input revision |
| story.transcript_revisions | FK run_input_id; unique (run_input_id, revision_no) | ASR profile/model version là typed model registry ref; transcript thuộc Story lifecycle |
| story.understanding_revisions | FK run_input_id; unique (run_input_id, revision_no) | Source image tới Core Asset; VLM profile có version; không lặp media hash |
| story.story_revisions | FK run_input_id; unique (run_input_id, revision_no); run trỏ current story | Model/prompt version là typed registry ref; input/context hash gắn đúng revision |
| story.story_scenes | FK story_revision_id; unique (story_revision_id, scene_index) và (story_revision_id, story_scene_id) | 5–15 scene là danh sách canonical; character anchor/prompt refs thuộc revision |
| story.review_decisions | FK story_run_id; target XOR FK run_input_id hoặc story_revision_id; idempotency unique theo run | Actor principal có kiểu; quyết định gắn revision/hash cụ thể đã xem |
| story.video_generations | FK story_run_id và story_revision_id; unique (video_generation_id, story_revision_id) và generation number khi accepted | Compute reservation/Billing usage/AI job/Core asset là typed refs qua contract; generation state canonical, run state là projection; không FK chéo schema |
| story.video_generation_scenes | Composite FK generation+revision và scene+revision; unique (video_generation_id, story_scene_id) | Bất biến cùng revision; source job ref target `VIDEO_GENERATION_SCENE`; clip asset ref tới Core; Story aggregate giữ output scene |
| billing.price_versions | Gốc immutable; unique version/effective interval | Được subscription/grant ghim; không tham chiếu business data khác |
| billing.organization_subscriptions | FK price_version_id; unique partial một subscription hiện hành/organization | Organization và billing-admin refs được BE1 resolve qua port |
| billing.capacity_periods | FK subscription_id; unique (subscription_id, period_start) | Lựa chọn lớp tạm ngưng là từng subscription_event; không nhúng list lớp |
| billing.invoices | FK subscription_id tùy chọn; unique invoice number | Owner scope Parent/org có kiểu; invoice là snapshot số tiền/kỳ bất biến |
| billing.payment_attempts | FK invoice_id; unique provider request/merchant refs | Provider transaction ref là external ID, không là paid proof nếu callback chưa xác minh |
| billing.provider_event_receipts | 0 hoặc 1 FK đích trong `payment_attempt_id`/`subscription_id`; unique (provider, provider_event_ref) | Callback chưa xác minh hoặc chưa resolve được target được ghi nhận với cả hai FK rỗng; receipt đã xác minh/xử lý phải có đúng một FK. Payload chỉ giữ hash/safe outcome; invoice resolve qua payment attempt. |
| billing.subscription_events | FK subscription_id và invoice_id tùy chọn; unique event/change-group | Affected class ref có kiểu tới BE1; mỗi lớp đổi trạng thái có một hàng |
| billing.video_quota_grants | FK price_version_id, invoice_id tùy chọn và source provider receipt tùy chọn; source event unique | Owner scope là Parent account hoặc organization; không mutable balance |
| billing.video_quota_usage | FK quota_grant_id; unique owner-scope/request idempotency | Request ref tới Story generation qua application saga; không FK chéo schema |
| notifications.inbox_items | Gốc thông báo; unique recipient/dedupe key | Billing/Story event ref có kiểu; recipient là Parent/Teacher/admin principal |
| notifications.delivery_attempts | FK inbox_item_id; FK push_endpoint_id tùy chọn; unique (inbox_item_id, channel, attempt_no) | Email destination là opaque identity-adapter ref; push endpoint nối về `notifications.push_endpoints`; retry không đổi inbox |
| notifications.push_endpoints | Unique endpoint fingerprint theo provider/principal; index principal/state | Principal ref tới identity adapter; raw token mã hóa, không FK cross-owner |

### 6.2 Quan hệ của 38 bảng nguồn active được giữ

| Owner group | Chuỗi quan hệ chuẩn | Kiểm soát liên kết |
|---|---|---|
| Core (5 nguồn) | core_aggregate_revisions → core_outbox_events → core_outbox_consumer_receipts; core_asset_metadata là gốc asset; core_audit_entries ghi metadata với typed resource ref | Canvas operation/checkpoint/idempotency thuộc 35 bảng legacy. Asset refs dùng composite (asset_ref, version); audit/outbox resource refs có contract. |
| BE1 (8 nguồn) | Organization → assignments/classrooms/profiles/consent/lifecycle; adult identity → assignments; profile → enrollment/consent. Bổ sung profile → revision/context/support | Bổ sung composite FK tenant-aware theo organization/class/profile; enrollment là nguồn chuẩn lớp/lịch sử; class assignment phải cùng organization. |
| AI Jobs (7 nguồn + 1 mới) | Job → attempt/command receipt/semantic request/completion receipt/cancellation notice/outbox/job event | Một target discriminator/ref duy nhất: StoryRun, VideoGeneration, GenerationScene, LessonSourceDocument hoặc SketchDeckRevision. `video_generation_scenes.source_job_ref` nối lại đến job cụ thể qua contract; không tạo bảng subject/result helper. |
| AI Policy (12 nguồn active) | Policy record → version → review/event; version → receipt/outbox; effective_scope → scope_transition; resource_scope → budget_bucket → resource_reservation → resource_event | Policy/activation/compute budget có quan hệ cùng owner. Resource event mang idempotency key/fingerprint và kết quả command, thay cho bảng receipt song song. 12 bảng copy registry cùng `resource_receipt` là legacy/read-only, không xuất hiện trong target graph. |
| Learning Content (6 nguồn) | Catalog record → version → review/event; receipt idempotency và outbox nối command/event | Parent story ghim catalog version được duyệt; Teacher plan dùng versioned ref; không sao chép catalog vào hồ sơ. |

### 6.3 Quy tắc integrity và canonical fields

1. Quan hệ trong cùng schema dùng FK, unique và check constraint. Khi có tenant scope, dùng composite key/FK để ngăn nối nhầm organization. Quan hệ giữa owners dùng typed ref có contract version, owner scope, API/port kiểm tra quyền và receipt idempotency; không tạo FK cross-owner.
2. Parent/Teacher profile lưu riêng. Profile root sở hữu identity/state/current-revision pointer; tuổi, nhóm tuổi, tên hiển thị và sở thích chỉ canonical trong profile revision. Context entry có ngày và support need gắn profile root. App-run history truy vấn từ Story, không thêm APP_RUN context row.
3. story.run_inputs là nguồn canonical theo revision cho tranh/ý tưởng, profile revision và context snapshot đã duyệt. Snapshot JSONB phải schema-versioned, hashed, allowlisted và giới hạn kích thước/số item; không dùng JSONB làm hồ sơ đầy đủ hay lịch sử vô hạn.
4. Core Asset là nguồn chuẩn duy nhất cho hash, media type, byte size, version và storage/quarantine state. Lesson/Story chỉ giữ asset ref. Loại hash/type/size trùng khỏi bảng feature. derived_from_ref/source_refs cũ chỉ đọc; lineage mới chỉ ghi ở core.asset_lineage.
5. Story/Lesson aggregate sở hữu output asset refs: Story giữ clip/video; Lesson giữ line-sketch. ai_jobs.completion_receipt ghi disposition/hash/idempotency, không dựng bảng generic job_result_assets.
6. Billing sở hữu price, invoice/payment, capacity period, quota grant và usage. video_quota_grants.invoice_id là liên kết invoice duy nhất; grant/usage append-only, không duplicate source_invoice_ref hoặc balance mutable.
7. Admin chỉ đọc metadata roster/billing theo role; không mặc nhiên được đọc support note, story, ảnh/audio/video. Notification endpoint và audit không chứa media/nội dung.
8. Bốn mươi tám bảng legacy giữ liên kết lịch sử nội bộ nhưng nằm ngoài active target graph; gồm 35 bảng collaboration/canvas/video/activity cũ và 13 bảng AI Policy deferred. Không tạo ref mới từ Story/Lesson sang collaborative session, canvas, video-review, activity-execution hoặc copy-registry legacy.
9. `story.video_generations` có unique `(video_generation_id, story_revision_id)`. `story.story_scenes` có unique `(story_revision_id, story_scene_id)`. `story.video_generation_scenes` lưu `story_revision_id` như khóa constraint bất biến và dùng hai composite FK để buộc generation và scene thuộc cùng revision; không chấp nhận hai FK rời có thể nối chéo revision.
10. Các con trỏ `story.runs.current_run_input_ref`, `current_story_revision_ref` và `current_video_generation_ref` chỉ là head projection. Story command khóa/version-check run, xác minh mọi target ref thuộc cùng run và quan hệ input/script/generation, rồi cập nhật pointer, `aggregate_revision` và trạng thái run trong cùng transaction. Command stale bị từ chối.
11. `story.video_generations.state` là lifecycle canonical cho một generation. `story.runs.state` là projection nghiệp vụ/UI; chỉ Story transaction idempotent mới cập nhật cả hai. `VIDEO_READY` yêu cầu generation hiện hành READY và mọi technical/consistency/safety/output checks đạt. `ai_jobs.job.state` chỉ mô tả thực thi.
12. Mỗi cross-owner reference có owner/resource kind, opaque ID, contract version, scope và revision/hash ghim khi cần. Owner đích xác minh qua port ở admission, completion và reconciliation; không thêm bảng registry tham chiếu chung hoặc SQL join xuyên schema.

### 6.4 Đường đi dữ liệu xuyên hệ thống

| Luồng | Đường đi chính | Cách nối qua ranh giới owner |
|---|---|---|
| Phụ huynh tạo video | Adult identity → `parent.child_profiles` → profile revision/context → `story.runs` → `story.run_inputs` → transcript/understanding/story revisions → scenes/video generations → Core assets; AI Jobs điều phối; Billing ghi quota | StoryRun giữ đúng một profile ref; `run_inputs` ghim profile revision và context đã duyệt. Story, AI Jobs, Core và Billing nối bằng typed opaque refs, versioned port và idempotency receipt; không có profile dùng chung Parent/Teacher. |
| Giáo viên tạo video mẫu | Organization/class/assignment → `be1.managed_profiles`/enrollment → `lesson.occurrences` → source document/extraction/approved plan/activity → đúng một `story.runs` với một profile và một activity → story/video/Core assets | Lesson occurrence/plan là nguồn chuẩn của buổi; StoryRun ghim occurrence/plan/activity và current responsible Teacher. Assignment được xác thực qua BE1 port; sample claim nằm ở Lesson; video/quota nằm ở Story/Billing. |
| Giáo viên tạo deck AI Sketch | Approved Lesson plan/activity → `lesson.sketch_deck_revisions` → `lesson.sketch_deck_steps` → Core line-art assets; AI Jobs dispatch target là deck | Deck revision ghim plan revision/hash; mỗi step FK tới deck và activity, Lesson xác minh activity thuộc plan đã ghim. Sketch job không có child/profile subject và không ghi Billing video quota. |
| Thanh toán và hạn mức | Billing price → subscription/capacity period/invoice → payment attempt/provider receipt → quota grant → quota usage → Story video-generation intent | Billing là nguồn chuẩn về entitlement/usage; callback receipt chỉ gắn attempt/subscription sau khi có target hợp lệ. AI Policy compute reservation và Story admission dùng versioned ports/receipt, không SQL ghi chéo. |
| AI policy và Modal synthetic scratch | AI policy record/version/review/event; resource scope/budget/reservation/event; job attempt/job event/asset lineage | Compute receipt gắn với reservation qua versioned port; resource event là ledger idempotent duy nhất. Modal scratch ref/hash/cleanup nối về attempt và asset lineage. Registry copy provider bị deferred khỏi graph active cho đến gate dữ liệu thật. |
| Thông báo và audit | Story/Billing/Lesson event → Core/owner outbox → `notifications.inbox_items` → `delivery_attempts`/`push_endpoints`; audit ghi actor/action/resource/result | Event contract có version và idempotent consumer receipt. Inbox là nguồn chuẩn; endpoint và recipient là typed principal refs. Audit không sao chép media/story/profile content. |

Các aggregate gốc như tổ chức, hồ sơ, occurrence, run, policy version, catalog record, invoice và inbox là điểm bắt đầu hợp lệ của từng vòng đời; chúng không phải bảng mồ côi. Ranh giới Parent/Teacher được giữ tách có chủ đích vì khác owner/authorization. “Có liên kết” nghĩa là mọi quan hệ nghiệp vụ đều được biểu diễn bằng FK trong owner hoặc typed contract ref qua owner; không tạo FK chéo module để làm sơ đồ trông liền mạch nhưng phá quyền sở hữu.


## 7. Bất biến cơ sở dữ liệu và kế hoạch chỉ mục

Các ràng buộc này phải được thực thi bền vững bằng check/unique constraint/partial index của PostgreSQL khi phù hợp và bằng validation ở cấp application transaction đối với quy tắc liên module.

| Bất biến | Cách thực thi đề xuất |
|---|---|
| Mỗi Firebase principal chỉ có một scope tài khoản ứng dụng | Hàng issuer/UID đã xác minh trong `be1_adult_identities` là unique, có một `account_scope` do server quản lý; vai trò tổ chức nằm ở các hàng assignment riêng |
| Mỗi story run có đúng một hồ sơ Parent hoặc Teacher | Check constraint: chỉ một trong hai tham chiếu hồ sơ có kiểu được điền; kiểm tra quan hệ role/scope khi tạo aggregate |
| Mỗi người lớn chỉ có một run active | Partial unique index trên `story.runs.active_owner_parent_account_id` hoặc `active_owner_teacher_id`, không trên creator; lock tách khỏi `created_by_actor_ref`. DRAFT, VIDEO_ADMISSION_PENDING và mọi state chưa đóng giữ khóa; COMPLETED/FAILED/ABANDONED/DELETE_PENDING/DELETED nhả khóa. Reassignment đổi owner qua saga versioned; idle/cancel release trong transaction Story. |
| Mỗi story run/job chỉ có đúng một trẻ | StoryRun có đúng một profile ref scalar; Story/video job có đúng một StoryRun target và resolve profile từ run đó. Teacher Sketch job không có profile. Từ chối batch/list child ref trong contract; không tạo bảng subject-ref riêng. |
| Upload session/part nhất quán và một lần | `core.upload_sessions`/`core.upload_parts` có unique session+part; exact retry cùng digest idempotent, digest conflict bị từ chối; finalization chỉ sau continuity/bytes/SHA-256/AV/media check; session expiry/abort purge idempotent. |
| Mỗi hồ sơ quản lý chỉ thuộc một lớp active | Partial unique index trên enrollment BE1 active theo hồ sơ quản lý |
| Mỗi lớp chỉ có một Teacher phụ trách | Partial unique index trên assignment phụ trách active theo lớp |
| Mỗi occurrence chỉ có một slot mẫu Teacher | Claim sample occurrence unique tại output đầu tiên được chấp nhận sau kiểm tra an toàn; tạo lại để cải thiện chất lượng vẫn ở cùng run. Tombstone chỉ có metadata giữ claim khi media run bị xóa; chủ sở hữu đã xác nhận slot vẫn được tính là đã dùng. |
| Chỉ có một nguồn chuẩn về sức chứa lớp | Snapshot capacity period là nguồn chuẩn trong một khoảng hiệu lực; transaction tạo lớp kiểm tra số lớp active so với giới hạn |
| Mỗi lần tạm ngưng lớp có thời điểm hiệu lực kiểm toán được | Một hàng `subscription_events` Billing ghi nối tiếp cho mỗi lớp được chọn trong cùng group ID; trạng thái lớp BE1 là projection idempotent |
| Tối đa bốn revision story | Suy ra từ `story.story_revisions` bất biến; command an toàn trong transaction cho phép một bản đầu + ba lần viết lại, không có trường đếm thứ hai |
| Tối đa ba request tạo video | Tạo intent `story.video_generations` trước admission; chỉ chuyển sang `ACCEPTED` sau compute reservation + quota receipt. Accepted rows được giới hạn một lần đầu + hai lần tạo lại. Admission rejected không chiếm cap/quota; mọi accepted request đều tính vào giới hạn và tiêu thụ một quota tháng, kể cả lỗi kỹ thuật/an toàn. |
| Mỗi scene retry tối đa hai lần sau lần đầu | Hàng `ai_jobs.attempt` và phép tăng có điều kiện với tối đa hai retry; không có bộ đếm retry trong bảng scene |
| Không playback trước khi output qua đầy đủ kiểm tra an toàn | Chuyển sang `VIDEO_READY` cần xác minh kỹ thuật và an toàn thành công, đúng policy version và đủ độ bao phủ; không cấp quyền playback nếu lỗi/không xác định |
| Assignment Teacher cũ không thể phát hành kết quả | Khi class reassignment commit, Teacher cũ/token playback cũ mất quyền ngay; Teacher mới được phân quyền qua assignment BE1 hiện tại. Audit metadata ghi transfer; late AI completion/playback phải đối chiếu assignment version hiện tại. Reassignment bị từ chối nếu Teacher mới đã có active run. Admin vẫn không có media access mặc định. |
| Khử trùng callback thanh toán | Tham chiếu provider/event unique và cập nhật receipt cùng chuyển trạng thái invoice/subscription trong một transaction |
| Hoàn tất/hủy/idle run không kẹt khóa | VIDEO_READY thành COMPLETED qua lệnh người lớn hoặc idle deadline 168 giờ; các trạng thái adult-wait khác thành ABANDONED cùng deadline. Nhắc ở giờ 144; AI job active/đối soát không tính adult-wait và giữ deadline riêng 6 giờ. Cả hai state nhả khóa, giữ content đến khi người dùng xóa. Cancel chưa hoàn tất chuyển DELETE_PENDING và purge async. Quota request đã nhận không hoàn; sample claim Teacher thành công không mở lại. |
| Reminder/auto-close idempotent | Story lưu `last_meaningful_activity_at` và `adult_wait_started_at`; adult-wait bắt đầu khi không có AI job active và cần thao tác người lớn. Reminder tại +144 giờ; closeout tại +168 giờ tính theo UTC/server clock. Inbox dedupe key gắn run + expected deadline/state version; command hợp lệ reset deadline. Polling/push receipt không reset idle. Scheduler chỉ chuyển state nếu state/deadline/version vẫn đúng; AI job có deadline riêng 6 giờ. |
| Không ghi đè bất đồng bộ bằng dữ liệu cũ | Job lưu run/revision/hash dự kiến; command hoàn tất đối chiếu mọi revision trước khi ghi |
| Revision bất biến | Chỉ insert hàng revision; con trỏ head hiện tại chỉ được chuyển sang revision mới tạo |
| Chọn catalog theo version đã duyệt | Run ghim activity ID/version/hash của catalog; module content xác minh trạng thái đã xuất bản/được duyệt |
| Mặc định loại context nhạy cảm | Application layer kiểm tra allowlist item snapshot; schema có cờ model_allowed chỉ được bật theo policy trường an toàn tường minh |

Cú pháp partial index, tập giá trị state và khả năng tương thích migration phải được kiểm tra theo schema cuối cùng. Không dựa riêng vào validation UI cho bất kỳ bất biến nào.

## 8. Ranh giới xóa, lưu giữ và kiểm toán

| Dữ liệu | Chủ sở hữu lifecycle | Quy tắc |
|---|---|---|
| Hồ sơ Parent và revision | Module hồ sơ Parent qua lifecycle port | Khi chủ sở hữu yêu cầu xóa, khởi chạy lifecycle context/run liên quan theo policy; audit chỉ giữ metadata |
| Hồ sơ Teacher được quản lý | Lifecycle BE1 | Yêu cầu lifecycle tổ chức có phân quyền; giữ lịch sử enrollment lớp theo policy lifecycle và thu hồi quyền nội dung |
| Tranh, voice, transcript, kết quả VLM, context snapshot, story, scene và video | Module Story + lifecycle asset Core | Xóa cùng nhau khi hủy run chưa hoàn tất hoặc xóa run đã hoàn tất; giữ receipt xóa và audit tối thiểu |
| Tài liệu giáo án gốc và revision văn bản | Module Lesson | Giữ đến khi lifecycle xóa; riêng việc xóa run không được âm thầm xóa nguồn giáo án được occurrence dùng chung |
| Modal scratch synthetic | AI Jobs + Core Asset | Lưu opaque attempt/workspace ref, input/output manifest hash, cleanup state/receipt và asset lineage; không lưu raw payload. Registry provider-copy đầy đủ bị deferred tới gate real-child-data. |
| Invoice/subscription/audit thanh toán | Billing | Giữ riêng metadata tài chính bắt buộc, không phụ thuộc vào việc xóa story/media. Tài liệu này không khẳng định thời hạn luật định cụ thể. |
| Bảng classroom/canvas/video/activity legacy | Chủ sở hữu legacy | Giữ nguyên vật lý ở chế độ chỉ đọc; gỡ/offload cần kế hoạch riêng được rà soát |
| Upload session/part chưa hoàn tất | Core Upload Session + object lifecycle | Khi abort/TTL hết hạn, thu hồi session, xóa chunk objects và giữ receipt/audit metadata tối thiểu theo lifecycle. Upload đã hoàn tất chuyển sang asset lifecycle và không bị session TTL xóa. |
| Audit entry | core | Chỉ actor/action/loại resource/thời gian/outcome; không lưu tên trẻ/media/transcript/prompt/ghi chú hỗ trợ |

Khi người lớn hủy run chưa hoàn tất hoặc xóa run đã hoàn tất, hệ thống thu hồi access, giải phóng khóa active, hủy job best-effort và xóa byte tranh/audio/transcript/context/story/video cùng các hàng nội dung chi tiết liên kết. Đây không phải thao tác “xóa video” riêng. Lệnh hủy commit trạng thái DELETE_PENDING và nhả khóa trước khi purge bất đồng bộ. Run `ABANDONED` và `COMPLETED` vì idle không bị xóa tự động; nội dung giữ đến khi người dùng xóa. Payment, quota usage ledger và audit tối thiểu độc lập với việc xóa run. Với Teacher occurrence, chỉ giữ claim slot mẫu đã dùng dưới dạng metadata; hủy/xóa/idle closeout không mở lại slot đã claim. Quota đã tiêu thụ không được hoàn (Q119, Q123, Q128). Top-up grant độc lập với việc xóa run. Thời hạn lưu giữ theo luật và policy xóa dữ liệu trẻ thật là cổng triển khai riêng, không suy diễn từ danh mục demo dữ liệu tổng hợp này.

## 9. Chính sách legacy chỉ đọc

48 bảng được phân loại Legacy/read-only bị loại khỏi ERD đích và contract đọc/ghi mới của sản phẩm. Ngoài 35 bảng classroom/canvas/video/activity/preset cũ, nhóm này có `ai_policy.resource_receipt` và 12 bảng `ai_policy.copy_*`. Sau cutover được phê duyệt riêng:

- Dừng thao tác ghi của ứng dụng từ các route classroom/canvas/video/activity/preset đã ngừng dùng.
- Giữ nguyên bảng database, hàng, ID gốc và ý nghĩa khóa ngoại.
- Không sao chép hàng vào một bảng archive tổng quát mới.
- Không hiển thị nội dung lịch sử nhiều trẻ như thể đó là story một trẻ.
- Chỉ cấp quyền truy cập cho migration/operator được ủy quyền rõ ràng, phục vụ đối soát hoặc phục hồi.
- Không tạo write mới vào bảng AI Policy deferred. Dữ liệu provider-copy trước đây vẫn được bảo toàn và chỉ đọc; job transfer synthetic mới ghi lifecycle metadata trên AI Job attempt/event và Core asset lineage.
- Giữ quyền và dữ liệu cũ đến khi chủ sở hữu duyệt kế hoạch lưu giữ/offload/drop sau khi có bằng chứng backup và restore.

“Chỉ đọc” ở đây là trạng thái vận hành mục tiêu; nhiệm vụ tài liệu này chưa thay đổi quyền database, route hay dữ liệu bảng.

## 10. Danh sách đối soát migration

Kế hoạch migration khi triển khai phải cung cấp bằng chứng cho từng mục dưới đây trước khi bật ghi mới:

1. Liệt kê schema đang chạy, định nghĩa table/column/index và số lượng hàng thực tế; đối chiếu với mốc 86 bảng khai báo nguồn.
2. Ghi riêng năm mapping fixture; không xem fixture là production.
3. Backup PostgreSQL và MinIO, sau đó kiểm thử restore trước mọi cutover.
4. Mở rộng bằng bảng đích/trường scope có version mới, đồng thời giữ cột, khóa và hàng hiện có; thiết kế này không drop/rename bảng hoặc cột nguồn.
5. Tái sử dụng quyền sở hữu tổ chức/lớp/hồ sơ qua contract repository BE1 hiện có; giữ ID opaque của hồ sơ và enrollment. Chỉ backfill enrollment active khi trạng thái nguồn rõ ràng; cách ly trường hợp không khớp.
6. Bổ sung/xác minh revision hồ sơ và context với provenance xác định được. Đánh dấu nguồn là `LEGACY_UNCLASSIFIED` nếu chưa xác minh. Không gửi tên khi backfill; không tạo consent tổng hợp hoặc consent thật giả.
7. Giữ nguyên ID session cũ; không điền story_run_id bằng cách chuyển đổi ID session cộng tác.
8. Đối soát số lượng, quyền sở hữu, quan hệ hồ sơ-lớp, hash asset và tham chiếu audit. Lưu tóm tắt đối soát đã ký duyệt trong evidence FEAT.
9. Chỉ sau khi chủ sở hữu phê duyệt, chuyển các ngữ nghĩa key/nullability/check không tương thích trên bảng active theo các bước expand/backfill/dual-read/write/validate. Bổ sung quy tắc một enrollment active, hỗ trợ owner scope Parent và constraint consent/data-origin mà không mất hàng hiện có.
10. Chỉ tắt ghi cũ sau feature flag khi route/contract mới được chấp nhận; xác nhận bảng legacy vẫn hiện diện vật lý.
11. Xác minh xóa story run mới không xóa chéo nguồn lesson/activity hoặc bản ghi legacy; giữ claim sample Teacher đã dùng ở dạng metadata.
12. Xác minh rollback dựa trên feature flag/tương thích và không đòi xóa dữ liệu đã migration.
13. Xem việc gỡ bảng, xuất archive, đổi retention hoặc migration dữ liệu thật là công việc riêng cần phê duyệt.

## 11. Truy vết số lượng bảng

| Hạng mục đếm | Nguồn / phép tính |
|---|---|
| 86 mapping production hiện tại | Source Register và danh mục table factory/module hiện tại; không phải số lượng database đang chạy |
| 5 mapping fixture được loại trừ | Danh mục fixture kiểm thử owner_fence_fixture.py |
| 38 mapping active hiện có | Core 5 + BE1 8 + AI jobs 7 + AI policy 12 + Learning Content 6 |
| 40 mapping mới | Core 3 + AI jobs 1 + Parent 5 + BE1 3 + Lesson 7 + Story 9 + Billing 9 + Notifications 3 |
| 78 mapping active đích | 38 + 40 |
| 48 mapping legacy chỉ đọc | Core 3 + BE1 14 + AI Policy 13 + Knowledge Video 2 + Video Review 6 + Video Failure 3 + Activity Execution 5 + Preset Automation 2 |
| 126 mapping vật lý ở trạng thái đích | 78 active + 48 legacy được giữ lại |
| Đối soát | 86 = 38 active-hiện-có + 48 legacy; 126 = 86 + 40 bảng mới |

## 12. Quyết định đã chốt và cổng kỹ thuật còn mở

Q01–Q146 đã được chủ sở hữu trả lời. Q145 text-only là hình thức trung gian và đã được Q146 thay thế; Parent AI guide dùng AI Job/Core Asset/AI Policy hiện có, không thêm bảng mới. SRS/Data Table Register vẫn là draft; gate model/license/cost và thời hạn expiry chính xác còn chờ evidence.

| Quyết định | Quy tắc đã chốt | Ánh xạ dữ liệu đích |
|---|---|---|
| Q134 | `DRAFT` thuộc adult-wait; active owner/lock tách khỏi creator bất biến; reassignment chuyển quyền qua BE1/Story; emergency force-close chỉ metadata/audit và không cấp admin quyền media, không trả quota hay mở lại sample claim. | `story.runs.active_owner_parent_account_id`, `active_owner_teacher_id`, `created_by_actor_ref`, `owner_epoch`; transfer/audit metadata; không thêm bảng riêng cho force-close. |
| Q135 | Thêm `core.upload_sessions` và `core.upload_parts`; mỗi application chunk tối đa 4 MiB là một object `PutObject`; backend kiểm tra liên tục/hash rồi bounded-assemble và ghi asset cuối bằng một `PutObject`; không dùng S3 Multipart Upload API. | Hai bảng Core chứa session/expiry và receipt/hash/size/object ref; `core_asset_metadata` chỉ mô tả asset hoàn tất. Các bảng này vẫn thuộc baseline sau khi gỡ các helper/snapshot trùng lặp; số đích hiện hành được D-83 chốt tại 40 new, 78 active, 126 physical. |
| Q136 | Tại +144 giờ tạo inbox reminder, push best-effort và email best-effort nếu owner Parent/Teacher hiện tại có email đã xác minh; inbox là nguồn chuẩn. | `notifications.inbox_items` giữ notice/dedupe; `notifications.delivery_attempts` giữ trạng thái kênh, không lưu nội dung trẻ hay raw recipient email. |
| Q137 | AI Sketch Deck chỉ phục vụ Teacher; Parent không dùng deck hoặc chọn trước chủ thể. Q146 bổ sung Parent AI line-sketch guide riêng, hoàn toàn tùy chọn. | Lesson deck sinh từ occurrence; Parent guide dùng `ai_jobs.job` target `PARENT_SKETCH_GUIDE`, private temporary Core Asset và AI Policy resource accounting; capture/VLM review flow vẫn giữ nguyên. |
| Q138 | Mỗi hướng dẫn vẽ có chuỗi 3–5 line-sketch bước tăng dần, gợi ý bố cục/vị trí và nội dung ngắn phù hợp tuổi. | `lesson.sketch_deck_steps` và Core line-art assets; target age band thuộc occurrence/deck, không lấy từ một hồ sơ trẻ cụ thể. |
| Q139 | Một deck dùng chung cho một occurrence và bao quát tất cả hoạt động của plan đã duyệt. | `lesson.sketch_deck_revisions` pin plan hash; `lesson.sketch_deck_steps` liên kết từng activity. Video mẫu vẫn chọn một activity và một trẻ riêng. |
| Q140 | Teacher dùng màn hình trình chiếu nền trắng, ít chữ, có line-sketch, hướng dẫn và giải thích nhiều activity; video story của trẻ xuất hiện khi pipeline hoàn tất. | Deck hiển thị trong Teacher web; video phát trong cùng occurrence/run, không xuất PPTX. |
| Q141 | Parent chỉ xác nhận/sửa chủ thể sau khi đã chụp ảnh; không preselect subject. | Không thêm deck/entity API cho Parent; giữ `story.understanding_revisions` và `story.review_decisions`. |
| Q142 | Teacher điều khiển Back/Next, chọn activity/chủ thể, skip và yêu cầu AI tạo lại từng sketch; không sửa freehand/layout hoặc export PPTX. | Điều hướng là client state tạm; sketch regeneration tạo deck revision bất biến mới và giữ provenance. |
| Q143 | Sketch generation không tiêu video quota; có rate-limit và cost cap độc lập. | AI Policy compute reservation/metering và sketch-specific limit; không có `billing.video_quota_usage` entry. |
| Q144 | Story-video theo pipeline người dùng cung cấp: VLM → LLM story → storyboard 5–15 scene → người lớn duyệt/xác nhận kịch bản → Character Bible/ảnh tham chiếu → LTX-2.5/Modal theo scene → kiểm tra consistency → FFmpeg ghép → TTS/phụ đề tiếng Việt → safety tự động → playback riêng. | Mỗi run chỉ dùng một trẻ và một tranh; không có cộng tác, gallery công khai, download hoặc duyệt video cuối. Video 30–90 giây, MP4 720p 16:9, giọng trung tính, không nhạc; retry/quota theo các quyết định đã chốt. Character Bible là cấu trúc neo trong `story.understanding_revisions`, không phải bảng riêng. |
| Q145 | Hình thức text-only được ghi nhận tạm thời trước khi làm rõ yêu cầu line-sketch. | SUPERSEDED bởi Q146; không tạo text-only starter riêng trong baseline hiện tại. |
| Q146 | Parent có thể chọn topic chung/độ khó để yêu cầu AI line-sketch guide 3–5 bước hoặc bỏ qua; không gửi hồ sơ/tuổi cụ thể/voice/photo/artwork; output private, tạm thời, có provenance/expiry-cleanup; lỗi không chặn capture; compute/rate riêng, không dùng video quota. Teacher Deck vẫn là bước chính trong Teacher flow. | Đã trả lời ở SRS v2.2-draft; dùng `ai_jobs.job`, `core_asset_metadata`/`core.asset_lineage`, `ai_policy.resource_reservation`/`resource_event`; chưa thêm bảng. |

**Ghi chú provisioning:** UC-13 dùng trường `state` hiện có của `be1_adult_identities` và `active` hiện có của `be1_organization_assignments` để biểu diễn chờ xác minh/chưa kích hoạt. Firebase Authentication sở hữu action code; email adapter chỉ gửi action link. Không thêm bảng invitation/token riêng.

### Cổng kỹ thuật

| Cổng | Lý do còn chờ |
|---|---|
| Kiểm tra schema/hàng database đang chạy | Bản nháp tài liệu này chưa truy cập database nào |
| Kiểu SQL chính xác, chuyển trạng thái check, khóa receipt thay thế và predicate partial index | Phải ánh xạ mô hình đích sang quy ước SQLAlchemy/Alembic hiện tại và được duyệt trước migration |
| Transfer từ Modal sang MinIO local | Cần POC staging/kết quả qua Volume có xác thực và giới hạn; giới hạn/path dữ liệu tổng hợp được ghi ở SRS §24.3 |
| Migration consent/data-origin BE1 hiện tại | Hồ sơ đang yêu cầu trường consent và state consent hiện tại chưa đầy đủ; chỉ cho phép hàng demo tổng hợp đến khi duyệt schema đích an toàn |
| Runtime/image/model revision LTX chính xác | Đã chọn L40S nhưng pipeline và version model cụ thể chưa được benchmark |
| Android push provider | Q131 yêu cầu mobile/web push; provider Android chưa chọn và không được mặc định UnifiedPush/FCM; POC phải kiểm tra distributor, app/device reach, opt-in, invalidation và background delivery. Inbox/email vẫn là fallback; Firebase Messaging bị loại theo repository rule. |
| Workflow orchestration | So sánh PostgreSQL outbox + RQ + Modal FunctionCall poller với Temporal (recovery, timers, cancellation, operational cost) trước implementation; không giữ RQ worker trong lúc Modal inference chạy |
| AI evaluation set | Synthetic evaluation hiện tại đủ cho demo gate; real-child evaluation set cần purpose/authorization/consent/provider/retention review và quy trình riêng được duyệt |
| Revision AI nhỏ hơn và rà soát license chính xác | Tên model mới là ứng viên; nhiệm vụ này chưa tải model hoặc benchmark chất lượng |
| Giá production, cấu hình merchant thanh toán và quota video | Tiền tệ/provider/quy tắc billing đã cố định; số tiền thương mại, giá trị quota và credential chưa chốt |
| Giá trị included quota Parent/Teacher | Chủ sở hữu quyết định hai mức cấu hình riêng; chốt số ban đầu sau benchmark GPU/chi phí/độ trễ bằng dữ liệu tổng hợp (Q115) |
| Host/region production, nhà cung cấp email, kênh cảnh báo và lịch retention | Chỉ chọn Docker local + Modal cho demo; chưa chọn vận hành production |
| Xử lý dữ liệu trẻ thật | Chỉ demo dữ liệu tổng hợp; ủy quyền dữ liệu thật, transfer, quyền truy cập, retention và policy xóa cần được rà soát riêng |

## 13. Nguồn liên quan

- SRS FEAT-063: [SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md](SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md)
- Source register, context, quyết định và plan FEAT-063.
- Khai báo hiện tại trong backend/src/sketch2life/infrastructure và danh mục Alembic trong backend/alembic/versions.
- docs/architecture/OVERVIEW.md, PYTHON_BACKEND_ARCHITECTURE.md, DEPENDENCY_RULES.md và CONTRACTS_AND_INTEGRATION.md.
- docs/adr/ADR-0016, ADR-0017, ADR-0018, ADR-0019, ADR-0020 và ADR-0021 đang đề xuất.
- [Amazon S3 multipart upload limits](https://docs.aws.amazon.com/AmazonS3/latest/userguide/qfacts.html) — multipart part tối thiểu 5 MiB trừ part cuối; application chunk objects trong thiết kế này không dùng API đó.
- [MinIO Go Client API: PutObject](https://docs.min.io/aistor/developers/sdk/go/api/) — tài liệu hiện hành mô tả object dưới 128 MiB được gửi bằng single PUT; exact MinIO SDK/version trong repository vẫn cần POC trước khi implementation.
