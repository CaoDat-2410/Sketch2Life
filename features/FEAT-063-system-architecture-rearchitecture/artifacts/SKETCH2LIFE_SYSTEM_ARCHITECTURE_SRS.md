# Sketch2Life — Đặc tả yêu cầu phần mềm (SRS) và Kiến trúc đích

**Feature:** FEAT-063 — Thiết kế lại kiến trúc toàn repository  
**Trạng thái tài liệu:** Bản nháp v2.7-draft, nền Rev57 và cập nhật tài liệu Rev58–Rev69; §§1–31 là yêu cầu đích, §32 là bằng chứng nguồn/as-built riêng theo baseline; chưa sign-off
**Phiên bản:** 2.7-draft
**Cập nhật:** 2026-11-13
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
| 2.4-draft | 2026-11-06 | Nhóm FEAT-063 (bản tổng hợp) | Bổ sung ảnh chụp as-built từ backend/API/database local và Modal dev dashboard; phân biệt code, runtime, deployment và target; thay AI development direction theo owner (Qwen3.5-VL, FLUX.3, Whisper, SAM 2 tùy chọn); giải quyết Q159. Không xóa hoặc hạ các yêu cầu sản phẩm chưa triển khai. | Bản nháp chờ review; chưa có sign-off |
| 2.5-draft | 2026-11-06 | Nhóm FEAT-063 (bản tổng hợp) | Rà soát lại SRS với hướng sản phẩm và code hiện hành; thống nhất model direction tại §§2, 6, 9, 14 và 31; phân loại rõ target, development direction, candidate, code có mặt, API/runtime được quan sát và gate còn mở; bổ sung source-only crosswalk Rev45 và snapshot source `origin/dev` Rev51; sửa trạng thái local DB trong companion. Không thay quyết định sản phẩm chưa được owner chốt. | Bản nháp chờ owner review/sign-off |
| 2.6-draft | 2026-11-06 | Nhóm FEAT-063 (bản tổng hợp) | Đối chiếu báo cáo rà soát v2.5; thống nhất quyền khởi tạo AI suggestion, vai trò/permission, quyền media mặc định deny, Parent lesson-version pin/activity timing, profile-share invitation, tám AI Job target, video-admission transitions và target count 92 active + 48 legacy. Ghi nhận owner clarifications: Content Admin là permission của Platform Admin; Platform Admin chưa được xem media trẻ mặc định; Teacher chỉ dùng quota school. Các chi tiết còn mở được giữ rõ. | Bản nháp chờ owner review/sign-off |
| 2.7-draft | 2026-11-07 | Nhóm FEAT-063 (bản tổng hợp) | Đối chiếu checklist remediation v2.6; làm rõ pin LessonVersion theo version/hash qua occurrence, plan revision và StoryRun; thống nhất cách diễn đạt quota admission theo saga nhiều owner; chuẩn hóa nhãn School Manager; giữ hợp đồng Parent không preset, plan supersession, role persistence, legacy age và schema/audit chưa chốt ở trạng thái OPEN; sửa nhãn đếm mục lục Data Table Register mà không đổi target 92 + 48. | Bản nháp chờ owner review/sign-off |
| 2.7-draft / Rev56 | 2026-11-08 | Nhóm FEAT-063 (bản tổng hợp) | Đồng bộ checklist mười nhóm readiness với Data Table Register và Diagram Input Catalog; thống nhất UC-05/FR-T-10/FR-PL-20/AC-56 cho hệ thống chọn ngẫu nhiên và Teacher xác nhận theo policy được duyệt; giữ Q-01, các owner decision và technical gates OPEN; không đổi policy đã chốt, target 92 + 48 hoặc sign-off. | Bản nháp chờ owner review/sign-off |
| 2.7-draft / Rev57 | 2026-11-09 | Nhóm FEAT-063 (bản tổng hợp) | Bổ sung đặc tả chi tiết G01–G10, decision register, trace matrix và các hợp đồng đầu vào diagram; sửa UC-14/§21.5 actor về Platform Admin (Content Admin permission); bổ sung package target; phân biệt TO-BE/PROPOSED với AS-BUILT kiểm chứng tại baseline Rev56. Các policy/technical gate chưa được duyệt tiếp tục OPEN; không tạo diagram final, DDL, migration hoặc sign-off. | Bản nháp chờ owner review/sign-off |
| 2.7-draft / Rev58 | 2026-11-09 | Nhóm FEAT-063 (bản tổng hợp) | Ghi rõ GitHub Actions CI hiện có và tách khỏi luồng phát hành CI/CD đích; thêm kịch bản staging/release/rollback ở mức yêu cầu và một giả định test synthetic no-eligible tạm thời. Không ghi nhận CI run, build hoặc deployment. | Bản nháp; chưa sign-off |
| 2.7-draft / Rev59 | 2026-11-09 | Nhóm FEAT-063 (bản tổng hợp) | Phân biệt 86 source mappings trước Rev31, 89 mappings hiện hành, baseline thiết kế lịch sử 89/137, target 92/140 và snapshot local 41; cập nhật trace/count, quota Parent/school, child-media deny-by-default và 17 câu hỏi OPEN-OWNER; sửa Q183/Q192. Không thay DTR hoặc tự chốt policy. | Bản nháp; chưa sign-off |
| 2.7-draft / Rev60 | 2026-11-09 | Nhóm FEAT-063 (bản tổng hợp) | Chọn v2.7-draft Rev57 làm nền theo yêu cầu owner; giữ nguyên §§32.6–32.7 Rev57, chuyển snapshot CI Rev58 sang §32.8, hòa giải §25.5/§28.2, quota-purchase matrix và authority pointers; rà soát note sáu nhóm, không tự đóng câu hỏi hay đánh dấu diagram/Physical ERD hoàn tất. | Bản nháp; chưa sign-off |
| 2.7-draft / Rev61 | 2026-11-10 | Nhóm FEAT-063 (bản tổng hợp) | Ghi nhận các lựa chọn owner đã trả lời về age band, history, quota tạm, Teacher sample, profile sharing, lesson publication, Parent no-preset, legacy profile và audit; giữ Q192 chưa rõ nguồn. Rà soát bảy diagram còn thiếu đầu vào, bổ sung A01–A10/S01–S12 cùng ma trận mười policy case qua bảy view, thêm AC-67 kiểm tra độ phủ/nhất quán, tách readiness khỏi sign-off và giữ các thiếu hụt kỹ thuật/physical schema ở trạng thái mở. Owner xác nhận run đã nhận trước khi hồ sơ vào dải legacy có thể hoàn tất; draft legacy chỉ đọc/xóa, không có quyền sửa/lưu trữ mới. Không sửa DTR, không tạo diagram hoặc khẳng định runtime đã hoàn tất. | Bản nháp; chưa sign-off |
| 2.7-draft / Rev62 | 2026-11-10 | Nhóm FEAT-063 (bản tổng hợp) | Theo owner clarification, chuẩn hóa Parent thành luồng ảnh tranh bắt buộc với topic/lesson preset tùy chọn; bổ sung preview hoạt động advisory sau VLM và xác nhận chủ thể, dùng lesson version đã pin hoặc Qwen3.5 Modal với subject/context tối thiểu. Tách preview trước video khỏi activity list của lesson sau video; no-preset vẫn không query learning_content hoặc catalog fallback sau video. SRS vẫn unsigned; DTR không đổi. | Bản nháp; chưa sign-off |
| 2.7-draft / Rev63 | 2026-11-11 | Nhóm FEAT-063 (bản tổng hợp) | Theo owner clarification, Parent activity preview trở thành catalog-first: backend lọc activities từ lesson versions PUBLIC/SHARED Parent được quyền xem, Qwen3.5 chọn ID và giải thích theo profile, topic, context tranh đã cấu trúc và lời kể đã được xác nhận; chỉ khi không có hoạt động phù hợp mới sinh đúng 3 bản nháp qua quality gate. Không gửi ảnh/âm thanh thô/định danh; fallback không sửa catalog hay lesson pin. Giữ nguyên danh sách hoạt động sau video theo lesson version đã pin và không có post-video fallback khi không pin lesson. SRS vẫn unsigned; DTR không đổi. | Bản nháp; chưa sign-off |
| 2.7-draft / Rev64 | 2026-11-12 | Nhóm FEAT-063 (bản tổng hợp) | Làm rõ đầu vào và hồ sơ truy vết tối thiểu để đánh giá readiness cho D04 Activity, D05 Sequence, D06 Screen Flow, D07 Class, D08 ERD Logical/Physical, D09 State Machine và D11 Package tại §31.10.3; sửa nhãn nguồn Rev61 thành review input dưới authority Rev64; giữ riêng Parent catalog-first preview trước story và activity list sau video theo exact pin. Không tạo diagram, DTR/DDL, route, class, state, API hay bằng chứng runtime; các readiness gate vẫn PARTIAL/BLOCKED và SRS chưa sign-off. | Bản nháp; chưa sign-off |
| 2.7-draft / Rev65 | 2026-11-12 | Nhóm FEAT-063 (bản tổng hợp) | Rà soát nhất quán cuối cho checklist bảy diagram: đồng bộ mục lục/anchor §31.10.3; hòa giải các câu no-preset cũ trong §§7.2/30.3/31.5 với Rev63 catalog-first preview trước story và no-post-video-fallback; làm rõ current-access recheck cho lesson pin Parent, đầy đủ trình tự S02 và các lifecycle thiếu state inventory; đối chiếu lại A01–A10/S01–S12, AC-67 và §§3/5/6/21/31/32.7. Không đổi product policy, không tạo diagram/DTR/DDL/route/class/state/API hoặc bằng chứng runtime; readiness vẫn PARTIAL/BLOCKED và SRS chưa sign-off. | Bản nháp; chưa sign-off |
| 2.7-draft / Rev66 | 2026-11-13 | Nhóm FEAT-063 (bản tổng hợp) | Theo yêu cầu trực tiếp của chủ sở hữu, thay hướng FLUX bằng SVG catalog + engine vector xác định; làm rõ Parent chọn topic/lesson tùy chọn, guide nét tăng dần 4–8 bước, ảnh bắt buộc, đối chiếu chủ đề và chụp lại tối đa một lần; chọn một hoạt động chính trước script và hiển thị hoạt động sau video; mở rộng Teacher lesson thành presentation chỉnh sửa được với ảnh/video/SVG. Giữ nguyên video LTX pipeline. API V2, DTR/DDL, rubric chất lượng và hiệu năng vẫn là technical gates; không ghi nhận implementation/runtime. Bản SRS vẫn unsigned. | Bản nháp; chưa sign-off |
| 2.7-draft / Rev67 | 2026-11-13 | Nhóm FEAT-063 (bản tổng hợp) | Đối chiếu checklist bảy diagram do owner cung cấp (tự ghi Rev65) với authority Rev66 và proposal Rev83.3; ghi kết quả tại §31.18. Sửa A01/A02 và S01/S02 theo flow Rev66: chọn một main activity là điều kiện trước story; no-pin sau video trả activity đã pin vào run, không query catalog hay tạo list bổ sung; lesson pin trả nội dung của exact version. Lỗi/unknown ở lựa chọn không được lách điều kiện selection; chi tiết recovery còn OPEN. Tạo hồ sơ đầu vào có nguồn nhưng PARTIAL/BLOCKED; không tạo diagram, API, DTR/DDL hay runtime evidence. SRS chưa sign-off. | Bản nháp; chưa sign-off |
| 2.7-draft / Rev68 | 2026-11-13 | Nhóm FEAT-063 (bản tổng hợp) | Ghi nhận M0 kỹ thuật đã được owner duyệt và chỉ mở implementation M1/M2 của Rev83.4: guide 4–8 bước; tối thiểu 4 path độc lập là ngưỡng cấu trúc, không phải điểm sư phạm; educator review theo source hash/revision và Platform Admin curation là hai quyết định riêng; copy-on-write guide revision, autosave debounce 1.5 giây và xung đột 409 giữ bản local; mục tiêu renderer ≥30 FPS, p95 first render ≤500 ms sau decode, p95 chuyển bước ≤150 ms, memory growth ≤64 MiB; ba SVG AI flags OFF mặc định; M3-B threshold 100% hard gates, ≥80% toàn bộ case đạt ≥4/5 ở cả recognizability/teachability qua hai educator, chênh ≥2 điểm cần reviewer thứ ba. Đây không phải formal SRS sign-off, không phải runtime/performance result, và không mở M3, Modal, AI activation, video hay FLUX retirement. | Bản nháp; chưa sign-off |

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
   - [Bảy diagram còn thiếu đầu vào — readiness Rev67](#srs-31-10-2)
   - [Minimum records required to close each diagram input gate](#srs-31-10-3)
   - [Owner clarifications from diagram-input review](#srs-31-14)
   - [Owner clarification — SVG guides and editable Teacher presentation](#srs-31-17)
   - [Rev65 checklist response against current authority](#srs-31-18)
   - [Rev65 checklist response against current authority](#srs-31-18)
32. [Trạng thái triển khai hiện tại (as-built snapshot)](#srs-32)
   - [Rà soát code và đối chiếu target](#srs-32-5)
   - [Source review trên origin/dev hiện hành](#srs-32-6)
   - [Rev57 source-only verification tại docs baseline](#srs-32-7)
   - [CI hiện tại và luồng phát hành đích — Rev58](#srs-32-8)

<a id="srs-1"></a>
## 1. Mục đích và quyết định chính

Sketch2Life giữ hai luồng sản phẩm Parent và Teacher, nay được đặt trên một lớp nền tảng giáo án dùng chung:

1. **Phụ huynh:** ứng dụng Android; topic tự nhập/chọn và lesson public/shared là tùy chọn. Nếu chọn lesson, Parent có thể xem presentation kiến thức và guide của lesson; guide tổng quát cũng có thể bật theo topic trước khi vẽ. Ảnh tranh của đúng một trẻ là bắt buộc; sau đó VLM nhận diện tranh và kiểm tra độ phù hợp với topic/lesson, người lớn xác nhận chủ thể, chọn một hoạt động chính trước khi duyệt kịch bản, rồi tạo video mới từ chính tranh của trẻ. Sau video, lesson đã pin hiển thị toàn bộ hoạt động của lesson; không có lesson pin thì hiển thị hoạt động chính đã chọn.
2. **Giáo viên:** ứng dụng web; trường là một tổ chức quản lý lớp và hồ sơ. Teacher tạo lesson/presentation có version, lọc nội dung upload rồi rà soát trước khi dùng; có thể sửa nội dung và thứ tự slide, thêm ảnh đã upload, video nhúng từ YouTube/Vimeo, SVG catalog hoặc hình SVG do AI tạo ở trạng thái nháp. Guide vẽ tiến dần từ các nét cơ bản đến hình đủ nhận biết. Trong buổi học, Teacher điều khiển presentation/guide; luồng chọn trẻ, xác nhận context và tạo video mẫu từ tranh của một trẻ vẫn theo policy hiện hành.

Mỗi story run gắn chính xác với một trẻ. Tài khoản Parent và Teacher vẫn tách biệt; hồ sơ trẻ có thể được chia sẻ qua lời mời và quyền có phạm vi, có thể thu hồi, không hợp nhất hai tài khoản hoặc biến Parent thành thành viên tổ chức. Mỗi trường là một organization/tenant. Không có runtime cộng tác lớp học, canvas vẽ dùng chung, QR/lobby/admission, xử lý nhiều trẻ theo lô hoặc hoạt ảnh tranh bằng PixiJS.

Hướng phát triển AI hiện tại được phân loại rõ ở §§6.3 và 9.3: Qwen3.5-VL cho hiểu tranh, story/storyboard và bản nháp vector có cấu trúc; SVG catalog cùng engine xác định chịu trách nhiệm parse, kiểm tra, lưu dữ liệu vector chuẩn và render SVG cho line-sketch/ảnh minh họa; FLUX không thuộc hướng đích và không được dùng làm fallback. Whisper là hướng ASR; SAM 2.1 là tùy chọn segmentation; Modal là hướng hosting inference trong giai đoạn phát triển. Các tên này không xác nhận checkpoint/runtime/phê duyệt production hay tích hợp end-to-end. Pipeline video LTX-2.5/Modal L40S theo Q144 giữ nguyên.

Cổng duyệt duy nhất trước khi gọi tạo video là người lớn xác nhận revision cuối của kịch bản/storyboard. Transcript, chủ thể, hoạt động, giáo án và context hồ sơ có bước xem xét/xác nhận riêng trước khi tạo story. Video hoàn chỉnh được hiển thị sau khi qua kiểm tra kỹ thuật và safety gate tự động; không có bước duyệt video cuối. Nếu người lớn đánh dấu video không phù hợp, video cũ bị ẩn khỏi playback ngay khi yêu cầu tạo lại được chấp nhận; run quay lại bước duyệt kịch bản. Bản cũ được giữ nội bộ cho đến khi xóa run.

### 1.1 Số lượng bảng đích

Baseline thiết kế v2.3 lịch sử là **89 bảng active + 48 legacy = 137 bảng dự kiến**. Trước Rev31, repository source inventory ghi nhận **86 mappings**; Rev31 bổ sung ba Lesson support mappings, đưa current source crosswalk lên **89 mappings** (38 retained/refactored + 48 legacy/read-only + 3 Lesson support). Đây là số mapping nguồn, không phải số bảng active hiện hành hay database vật lý. Target hiện hành là **92 active** (38 retained/refactored + 54 new) và **48 legacy/read-only**, tổng cộng **140 mapping vật lý dự kiến**. Bốn helper/snapshot table bị loại khỏi active graph; 13 mapping AI Policy provider-copy/resource receipt vẫn legacy/read-only. Năm fixture bị loại. Con số 92/140 là mô hình source-declared, chưa phải DDL cuối hay kiểm kê production database.

| Hạng mục | Số lượng | Ý nghĩa |
|---|---:|---|
| Bảng active trong target hiện hành | 92 | 38 retained/refactored + 54 new; target source-derived, không phải kiểm kê database đang chạy |
| Bảng fixture chỉ dùng cho test | 5 | Không phải bảng production; loại khỏi mọi phép tính |
| Source mappings trong current crosswalk sau Rev31 | 89 | 86 pre-Rev31 + 3 Lesson support; gồm 38 retained/refactored, 48 legacy và 3 Lesson support |
| Bảng hiện có được giữ lại/chuẩn hóa | 38 | Bảng hiện tại vẫn cần cho sản phẩm và nền tảng đích |
| Bảng mới trong mô hình đích hiện hành | 54 | Dữ liệu Parent/profile, lesson library/sharing/feedback, Sketch Deck, Story, quota/billing, notification, upload, asset và AI job |
| Tổng bảng đang hoạt động hiện hành | **92** | 38 + 54; đồng bộ Data Table Register |
| Bảng legacy chỉ đọc | 48 | Gồm 35 workflow cũ và 13 AI Policy deferred; giữ nguyên tại chỗ |
| Bảng production vật lý dự kiến theo target hiện hành | **140** | 92 active + 48 legacy; chưa phải DDL/prod inventory |

Rev31 implementation crosswalk adds three Lesson-owned support tables beyond the historical v2.3 design (89/137). The current companion target and source-derived crosswalk are both 92 active + 48 legacy/read-only = 140 projected physical mappings. Neither count is a live database observation or final physical schema; see Data Table Register §§1 and 14.4. The local 41-table snapshot in §32 remains environment-specific.

DATA_TABLE_REGISTER.md ghi disposition của nguồn, tên bảng đích, chủ sở hữu dữ liệu và ràng buộc. Thiết kế này không drop bảng và không sao chép dữ liệu sang một kho archive thứ hai.

### 1.2 Trạng thái quyết định

Baseline thiết kế v2.3 lịch sử là 89 active + 48 legacy = 137; current source crosswalk là 89 mappings (86 pre-Rev31 + 3 Lesson support); target hiện hành là 92 active + 48 legacy = 140 mapping dự kiến theo Data Table Register. Rev43 kiểm tra read-only database phát triển local và ghi nhận 41 bảng ứng dụng; snapshot này không phải production và không hoàn tất kiểm kê migration. Bốn con số có phạm vi khác nhau, được giải thích tại §32 và DATA_TABLE_REGISTER.md.

<a id="srs-1-document"></a>
### 1.3 Phạm vi và cấu trúc tài liệu

Đây là package Markdown tổng hợp SRS, kiến trúc đích (SAD-level), vận hành và chiến lược xác minh theo yêu cầu owner muốn duyệt một baseline đầy đủ cùng data register. Requirement quy phạm nằm ở BR/FR/NFR; công nghệ, entity, API, job/ops ở các mục tương ứng phải được đọc theo trạng thái `proposed`/`gate`, không phải implementation fact. Sau khi owner duyệt nội dung có thể tách các chương kiến trúc, runbook và test strategy thành file riêng nhưng giữ nguyên ID/traceability; hiện chưa chia file để tránh lệch nhiều bản nguồn.

Tài liệu tham khảo về yêu cầu được đối chiếu theo ISO/IEC/IEEE 29148:2018; IEEE 830-1998 là thực hành cũ đã được thay thế bởi 29148. Bản này dùng cấu trúc và thuộc tính requirement làm hướng dẫn, không tuyên bố chứng nhận tuân thủ đầy đủ chuẩn. Phần visual diagrams chưa có trong Markdown vì owner yêu cầu chỉ tạo sau khi duyệt SRS và register.

<a id="srs-2"></a>
## 2. Phạm vi

### 2.1 Trong phạm vi

- Khôi phục/chuyển luồng Phụ huynh cũ sang nền tảng Android hiện tại.
- Giữ yêu cầu đích cho Parent Android, Teacher web và pipeline tạo ảnh/video; nền tảng lesson, nội dung và phân quyền là phần bổ sung kiến trúc. Điều này không khẳng định các client/API/provider flow đã hoàn tất trong code hiện tại.
- Tách tài khoản Parent và Teacher; hỗ trợ chia sẻ hồ sơ trẻ bằng invitation, phạm vi quyền tối thiểu, consent, audit và revoke.
- Mỗi trường là một organization/tenant; tách quyền platform Admin, school Manager, Teacher và Parent.
- Thư viện lesson tái sử dụng dạng preset, có version và visibility private/school/selected/public; lesson content độc lập với occurrence dạy thực tế.
- Teacher authoring form và template upload chuẩn hóa; giữ file gốc riêng tư, lọc/extract allowlist trước AI, Teacher xem/sửa bản structured trước khi dùng.
- Teacher/Manager có thể tạo hoặc duyệt lesson draft theo quyền được chốt; Parent dùng public/được chia sẻ, có thể sửa personal copy nhưng không sửa nguồn gốc đã publish.
- Parent có thể xem lesson đã dạy cho profile được chia sẻ trong thời hạn lịch sử được cấu hình, tải lesson được cấp quyền và gửi feedback; không có chat, completion toggle hay upload tranh lên feedback.
- Phạm vi tuổi child là 3–10 (36–120 tháng), chia ba age band versioned: 36–71, 72–107 và 108–120 tháng. Profile/run giữ band version đã dùng; không lưu ngày sinh chính xác.
- Một lesson occurrence cho mỗi buổi dạy và tối đa một video mẫu thành công cho occurrence đó; mỗi run chỉ chọn đúng một trẻ.
- Teacher guide và Parent line-sketch guide là tùy chọn; khi tắt thì không tạo guide-generation job. Lesson/presentation Teacher là nội dung có thể chỉnh sửa, còn SVG/guide nguồn giữ provenance và revision riêng.
- Parent guide dùng catalog SVG trước; khi thiếu guide phù hợp, có thể yêu cầu AI tạo bản nháp nếu capability được bật. Guide gồm 4–8 bước adaptive, đi từ nét cơ bản đến hình đủ nhận biết; người lớn có thể bỏ qua. Guide không phải tranh hoàn chỉnh của trẻ và không nhận profile, ảnh, giọng nói hoặc dữ liệu định danh của trẻ.
- Teacher lesson presentation hỗ trợ chỉnh sửa nội dung slide và thứ tự, upload ảnh, video nhúng từ YouTube/Vimeo, SVG catalog và SVG AI draft. Slide/media placement thuộc version nháp; Teacher review trước khi nộp, Manager duyệt phạm vi trường, Platform Admin duyệt public toàn nền tảng theo quyền.
- Video storytelling từ tranh trẻ theo pipeline VLM hiểu ảnh → LLM tạo story có cấu trúc → storyboard → người lớn duyệt/xác nhận script → chuẩn bị Character Bible và ảnh tham chiếu → LTX-2.5 trên Modal theo scene (mục tiêu theo Q144; WAN chỉ là ứng viên thử nghiệm) → kiểm consistency → FFmpeg ghép scene → tạo/đồng bộ TTS và phụ đề → safety tự động → playback riêng trong run. Hướng phát triển cho VLM/story là Qwen3.5-VL; ASR là Whisper; model TTS/checkpoint và các cổng chất lượng/runtime vẫn mở.
- AI line-sketch/ảnh minh họa mới dùng output vector có cấu trúc được SVG engine kiểm tra và serialize; không dùng FLUX.3. Qwen3.5-VL là hướng tạo draft khi catalog không có nguồn phù hợp, subject to POC/quality gates. SAM 2.1 vẫn là tùy chọn segmentation; đây là hướng đích, không phải bằng chứng guide/deck đã được nối API/runtime.
- Chụp bằng camera/tải ảnh lên, ý tưởng bằng chữ/giọng nói, xem và sửa transcript Whisper, nhận diện/chỉnh chủ thể, tạo story cá nhân hóa, duyệt kịch bản, tạo video mới từ ảnh rồi hiển thị các hoạt động ngoài trời đã cấu hình trong lesson.
- Revision hồ sơ, snapshot context được duyệt cho từng run, provenance, lifecycle xóa và ràng buộc chỉ dùng dữ liệu tổng hợp cho demo.
- Kiểm kê bảng nguồn toàn repository và thiết kế dữ liệu đích không phá hủy dữ liệu hiện có.
- Clean architecture, contract có version, mã lỗi chuẩn hóa, monitoring, rate limit, vận hành Docker local và inference model qua Modal.
- Capacity tổ chức gồm 10 slot lớp trong gói cơ bản trả phí; mua thêm theo đơn giá/slot bằng MoMo/VNPAY ở adapter ban đầu.
- Quota video có hai owner scope tách biệt: school organization và Parent account; video của Teacher dùng quota school theo occurrence, không có Teacher-account pool hay cross-scope fallback. Mức review tạm thời là Parent 2 lượt/tháng và top-up 5 lượt/₫249.000; School 30 lượt/tháng và top-up 50 lượt/₫1.990.000. Các con số/giá chỉ là giả định để review, không phải cấu hình thương mại hoặc giá production. Quyền mua/cấp/phân bổ, expiry và các điều khoản thương mại chưa được chốt.

### 2.2 Ngoài phạm vi

- Session cộng tác lớp học, QR, lobby/admission, nhiều trẻ trong một run, canvas nhóm, vẽ dùng chung hoặc tiến trình theo stage cộng tác.
- Hoạt ảnh tranh bằng PixiJS.
- Teacher AI Sketch Deck trong luồng Parent; chọn trước chủ thể của tranh trẻ trước khi chụp. Parent AI line-sketch guide là một tùy chọn riêng, không lấy dữ liệu trẻ làm input và không chặn capture.
- Xuất presentation ra PPTX/PDF hoặc dùng slide như canvas cộng tác trên thiết bị; presentation Teacher được tạo/chỉnh sửa và trình chiếu trong ứng dụng/web.
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
| Platform Admin có permission rà soát nội dung | Lesson library và chính sách an toàn dùng chung | Permission review/publish/moderate, revision, nguồn và lịch sử thu hồi; không phải một role sản phẩm riêng |
| Vận hành/kỹ thuật | Sức khỏe dịch vụ, queue, model/provider, chi phí và phục hồi | Metrics đã redact, correlation ID, runbook, giới hạn/circuit breaker |
| Privacy/legal/commercial reviewer | Dữ liệu trẻ, vai trò controller/processor, transfer, retention, payment/tax | Evidence và quyết định phê duyệt production; chưa được coi là hoàn thành |

**Người dùng mục tiêu và môi trường:** Parent là người lớn dùng điện thoại Android, có thể không quen thuật ngữ AI; Teacher mầm non thao tác trên máy tính/laptop qua trình duyệt trong thời gian chuẩn bị buổi học; School Manager dùng web với quyền billing/roster theo organization. V1 dùng tiếng Việt. Nếu camera/micro bị từ chối hoặc không sẵn sàng, phải có upload ảnh và nhập chữ thay thế. Repo hiện khai báo `minSdk 29` (Android 10), `targetSdk 36`, `compileSdk 37`; browser target là hai phiên bản stable gần nhất của Chrome/Edge desktop và phải được xác minh lại trong release gate.

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
| Platform Admin | Web desktop, quyền quản trị nền tảng | Soạn lesson public; một Platform Admin khác có Content Admin permission review trước khi publish; quản lý role/quota; child-media access mặc định deny |

<a id="srs-3"></a>
## 3. Tác nhân và phân quyền

| Tác nhân | Quyền hạn | Giới hạn |
|---|---|---|
| Platform Admin | Quản trị role/permission toàn nền tảng; author lesson public; publish chỉ sau independent review bởi Platform Admin khác có Content Admin permission; xem/trả lời feedback school-scoped; ẩn hoặc thu hồi nội dung khi cần | Role Platform Admin tự nó không cấp quyền đọc child media. Media access mặc định bị từ chối; không mở quyền cho tới khi owner duyệt một quy trình riêng. Mọi quy trình tương lai phải đáp ứng permission, reason code, privacy/lifecycle và audit. |
| School Manager | Quản lý một organization (một trường), Teacher/Parent groups, quota school, xem và duyệt Teacher lesson trước public; xem và phản hồi feedback thuộc trường | Không được thấy dữ liệu/media của organization khác; role quản lý roster không mặc nhiên cấp media trẻ. |
| Phụ huynh (Parent) | Sở hữu tài khoản và hồ sơ Parent; tạo run; dùng lesson public/được chia sẻ; xem lesson đã dạy cho child profile liên kết; gửi feedback/trả lời trong feedback thread; quản lý và thu hồi grant; xem video | Không vào organization/roster; không xem profile Teacher ngoài field đã share; không có chat, completion toggle, upload tranh feedback hoặc sửa trực tiếp scene AI. |
| Giáo viên phụ trách (Teacher) | Vận hành lớp được giao; author/edit lesson, dùng preset tùy chọn; quản lý profile được giao; upload/review giáo án đã lọc; chuẩn bị occurrence; bật/tắt line-sketch; xem và xác nhận child đại diện do hệ thống chọn ngẫu nhiên theo policy đã duyệt, rồi tạo video mẫu mới; xử lý feedback của lớp | Quyền run/profile theo phân công và grant đang hiệu lực; khi revoke/reassignment, quyền bị thu hồi ngay. Không xử lý nhiều trẻ theo một run. |
| Platform Admin (Content Admin permission) | Content review/publish/moderation là permission capability trong Platform Admin policy, không phải principal/role độc lập. Dùng nhãn actor Platform Admin (Content Admin permission) trong UC/screen khi thao tác đòi quyền này. | Chỉ tác động tới lesson/catalog theo permission; không cấp quyền child profile/media. |
| Vận hành hệ thống | Vận hành dịch vụ local, giám sát sức khỏe, khôi phục backup và cấu hình secret provider | Telemetry vận hành không để lộ nội dung trẻ. Quyền truy cập dịch vụ production cần chính sách được xem xét riêng. |
| Adapter AI provider | Nhận input được cho phép của đúng một run và trả kết quả có kiểu/version | Chỉ chạy ở backend; không nhận danh sách trẻ, trường hồ sơ bị ẩn, credential tài khoản hoặc quyền truy cập storage không giới hạn. |

Xác thực chỉ dùng Firebase Authentication. Backend xác minh ID token và suy ra danh tính actor; mỗi lần đọc/ghi resource phải kiểm tra tiếp role, permission, tổ chức, phân công lớp, quyền sở hữu hồ sơ và actor của run. Content review là permission của Platform Admin, không phải role đăng nhập riêng. Không dùng Firebase Storage, Firestore hoặc Realtime Database.

Tài khoản Parent và Teacher bắt buộc tách biệt, kể cả khi một người lớn đảm nhiệm cả hai vai. Parent có thể mời một Teacher phụ trách/trường chia sẻ các trường hồ sơ được chọn; grant ghi bên cấp/nhận, scope, purpose, status, thời hạn và revoke, và không đổi owner của profile. Mỗi trường là một tenant; mọi lesson, feedback và member group được kiểm tra theo organization. Mỗi hồ sơ Teacher tối đa một enrollment lớp active; profile cross-role resolve chỉ qua contract/grant versioned.



**Hợp đồng resolver quyền đích (TO-BE / PROPOSED):** API/application phải phân quyền phía server theo principal đã xác thực, role/permission assignment có hiệu lực, organization/class scope, resource/action và revision grant đang hiệu lực. Resolver trả allow hoặc deny cùng reason nội bộ và revision dùng để quyết định; thiếu assignment, scope, resource mapping hoặc không kiểm tra được version thì deny. Revoke làm vô hiệu quyết định cache theo revision cũ và chặn read/token mới cùng job chưa được accept. Đây là hợp đồng logic để thiết kế, chưa phải tên bảng, endpoint hay implementation đã kiểm chứng. Parent không đọc roster trường; School Manager chỉ có tenant scope được gán; Platform Admin không đọc child profile/media nhờ role hoặc Content Admin permission. Force-close chỉ giữ nguyên quy tắc BR-41: School Manager của organization sở hữu lớp/run có thể gửi emergency command tường minh, kèm reason và metadata audit, không đọc media và không xóa quota/sample claim. Cách gán, resolver, người được ủy quyền cụ thể, audit fields/retention tiếp tục OPEN tại Q-13 và §31.10(14),(17).

<a id="srs-4"></a>
## 4. Quy tắc nghiệp vụ

BR-01 đến BR-46 ghi lại baseline sản phẩm/an toàn; BR-47 đến BR-60 bổ sung các quy tắc platform v2.3 và các override được chủ sở hữu yêu cầu. Quy tắc lịch sử mâu thuẫn được giữ để truy vết nhưng nhường cho nội dung mới tại §31.

| ID | Quy tắc nghiệp vụ |
|---|---|
| BR-01 | Một story run phải gắn chính xác một hồ sơ trẻ. Request và job contract chỉ lưu một profile ref scalar; từ chối nhiều trẻ, batch và context nhóm. |
| BR-02 | Mỗi tài khoản người lớn có tối đa một story run chưa kết thúc. Khóa gắn với owner hiện hành (`active_owner_parent_account_id` hoặc `active_owner_teacher_id`), tách khỏi `created_by_actor_ref` bất biến. Parent khóa theo tài khoản Parent; Teacher khóa theo giáo viên đang phụ trách. |
| BR-03 | Parent và Teacher có account scope và lịch sử hồ sơ riêng; một Parent có thể mời Teacher/trường chia sẻ profile qua grant có purpose/scope/revoke. Principal và profile không tự hợp nhất; role claim từ client không cấp quyền. |
| BR-04 | Lớp và hồ sơ trẻ Teacher thuộc tổ chức. Mỗi tổ chức có 10 slot lớp trong gói cơ bản trả phí. Capacity bổ sung mua theo một đơn giá/slot cấu hình được, theo tháng hoặc năm; không chia nhiều tier. Giá cụ thể thuộc cấu hình thương mại. |
| BR-05 | School Manager của organization phân công một Teacher phụ trách mỗi lớp. Một Teacher có thể phụ trách nhiều lớp. Mỗi hồ sơ trẻ tối đa một enrollment lớp đang hoạt động. |
| BR-06 | BE1 là nguồn chuẩn phân công hiện tại. Reassignment dùng workflow bền vững hai owner BE1/Story: đưa lớp vào transfer-pending/read-only, fence quyền và token cũ ngay, chuyển active-run owner/lock qua Story port rồi mới finalize Teacher mới; trong lúc pending không mở nội dung cho Teacher nào. `created_by_actor_ref` chỉ là provenance. Nếu Teacher mới có run active, Story từ chối chuyển lock và saga bù BE1 về assignment cũ; nếu bù mơ hồ, transfer giữ pending/read-only để đối soát; không hủy AI job hợp lệ chỉ vì đổi Teacher. Output chỉ được nhận nếu input/script/hash/occurrence và assignment version còn hợp lệ; chỉ Teacher hiện tại được xem. Admin mặc định không xem media. Teacher phụ trách xác nhận có audit trước khi chiếu mẫu cho lớp; người xem không có tài khoản, playback capability dùng lại hoặc quyền export. |
| BR-07 | Teacher tạo/sửa hồ sơ trẻ bằng form nhập nhanh có cấu trúc, có thể nhập lại câu trả lời trên phiếu khảo sát phụ huynh. V1 không OCR hoặc import file phiếu. |
| BR-08 | Lesson version có thể cấu hình một hoặc nhiều hoạt động ngoài trời với vật liệu/cách làm/ghi chú. Sau VLM và xác nhận chủ thể, Parent chọn một hoạt động chính trước khi tạo kịch bản. Backend dựng candidate set catalog-first từ lesson versions PUBLIC/SHARED Parent hiện có quyền xem, lọc theo đúng tuổi, topic, subject/features của tranh và context hợp lệ; nếu run pin lesson thì chỉ dùng activities của exact version/hash đó. Qwen3.5 nhận candidate set cùng profile summary/tags, topic, subject/features và lời kể/transcript đã được người lớn xác nhận (nếu có), rồi trả ID/thứ tự/lý do; backend chỉ hydrate nội dung chuẩn từ nguồn. Không gửi ảnh, audio thô hoặc định danh trẻ. Nếu không có candidate phù hợp, AI có thể tạo đúng 3 hoạt động draft qua quality gate; người lớn chọn một hoạt động. Người lớn có thể yêu cầu bộ gợi ý khác; các hoạt động đã hiển thị/bị từ chối phải được loại khỏi candidate output để tránh trùng. Draft không được ghi vào catalog hoặc thay lesson pin. Hoạt động chính được đưa vào context kịch bản và diễn ra sau video. Sau video, lesson pin hiển thị toàn bộ hoạt động của exact version/hash; nếu không pin lesson thì hiển thị hoạt động chính đã chọn. Teacher occurrence giữ flow riêng theo approved plan. |
| BR-09 | Reusable lesson/version độc lập với occurrence. Parent có thể bỏ qua topic và lesson preset hoặc chọn một lesson đang được phép xem từ Gallery; chọn lesson là tùy chọn, không phải điều kiện chụp ảnh/tạo video. Run pin exact lesson/version/hash đã được backend xác thực. Teacher occurrence pin optional lesson/version; Teacher occurrence không dùng preset vẫn cần approved plan. Video mẫu dùng đúng một trẻ/tranh. |
| BR-10 | Mỗi occurrence Teacher tạo tối đa một video mẫu có thể phát và đã qua kiểm tra an toàn, cho đúng một trẻ. Slot được claim nguyên tử tại video playable đầu tiên. Run lỗi kỹ thuật hoặc bị chặn an toàn trước lần claim đầu không chiếm slot. Sau khi claim, slot không mở lại khi video bị đánh dấu không phù hợp, bị ẩn, tạo lại thất bại/hết lượt, run bị xóa, hủy hoặc chuyển giáo viên; không có recovery run thứ hai cho occurrence đó. |
| BR-11 | Một run có một request tạo video đầy đủ ban đầu và tối đa hai request tạo lại về chất lượng. Mỗi request video đầy đủ được chấp nhận tiêu thụ một slot giới hạn của run và một unit quota, kể cả khi sau đó lỗi kỹ thuật hoặc safety block. Retry scene tự động không tiêu thụ thêm request/unit. Mỗi lần tạo lại vẫn ở cùng run và phải quay lại xác nhận revision kịch bản. |
| BR-12 | Video Teacher hoàn chỉnh, kể cả các lần tạo lại chất lượng, vẫn là video mẫu duy nhất của occurrence; tạo lại không cấp quyền chọn trẻ khác hoặc mở run mẫu độc lập thứ hai. |
| BR-13 | Mỗi story có một bản đầu và tối đa ba lần AI viết lại (tổng bốn revision story/run). Parent gửi gợi ý; Teacher có thể đặt thêm hướng kể từ giáo án/kế hoạch lớp. Người lớn không sửa trực tiếp scene do AI tạo. |
| BR-14 | Mỗi revision story mới phải được xem và xác nhận lại trước khi tạo video. UI hiển thị revision hiện hành; revision cũ giữ nội bộ đến khi xóa run. |
| BR-15 | Transcript, chủ thể, lesson/plan và snapshot context hồ sơ phải được xác nhận ở bước tiền điều kiện tương ứng. Parent phải chọn một hoạt động chính trước khi tạo kịch bản; activity suggestion có thể đổi bằng một yêu cầu mới loại trừ các lựa chọn đã thấy/bị từ chối. Teacher sample vẫn ghim một activity đã duyệt. Cổng cuối trước video là xác nhận script/storyboard; không có duyệt video cuối riêng. |
| BR-16 | Video được hiển thị ngay khi tạo xong và qua kiểm tra kỹ thuật cùng safety gate tự động. Nếu người lớn đánh dấu video không phù hợp rồi yêu cầu tạo lại, ẩn video cũ khỏi playback ngay; giữ media nội bộ đến khi xóa run. Nếu lần tạo thay thế thất bại thì video cũ vẫn không được phát. Run quay lại bước xem script và phải xác nhận script trước lần tạo tiếp theo. |
| BR-17 | Mỗi scene có một lần thử ban đầu và tối đa hai lần retry kỹ thuật tự động. Hết retry thì run dừng và trả mã lỗi an toàn. Chỉ được mở run Teacher mới cho occurrence nếu chưa có video mẫu nào qua safety gate và phát được. Nếu video đầu đã claim slot, sau đó bị ẩn và cả hai lần tạo lại chất lượng thất bại/hết lượt thì run kết thúc lỗi; slot vẫn đã dùng và không có recovery run mới trong occurrence (Q127). |
| BR-18 | Hồ sơ Parent và Teacher dành cho trẻ 36–120 tháng (3–10 tuổi), chia age band versioned 36–71, 72–107 và 108–120 tháng; lưu tuổi theo tháng và pin band version đã dùng, không lưu ngày sinh chính xác. Không gửi tên/tên gọi thân mật cho model. Đây thay giới hạn lịch sử 36–155 tháng. |
| BR-19 | Thông tin cá nhân hóa do người lớn nhập và được revision hóa. Có thể gồm sở thích, quan sát học tập, lịch sử run trong ứng dụng, trải nghiệm/sự kiện ngoài ứng dụng do người lớn nhập, thành tích, nguồn và ngày gần đúng tùy chọn. Lịch sử ứng dụng và trải nghiệm ngoài app là hai nguồn riêng. |
| BR-20 | Thông tin sức khỏe/tâm lý chỉ biểu diễn nhu cầu hỗ trợ do người lớn nhập, không phải chẩn đoán. Trường này giới hạn truy cập, mặc định loại khỏi AI context và hệ thống không tự suy luận. |
| BR-21 | Người lớn duyệt snapshot context tối thiểu, gắn với version cụ thể cho từng run. Chỉ trường được cho phép rõ ràng mới được gửi vào quy trình AI. |
| BR-22 | Giáo án Teacher nhận PDF/PPTX/DOCX có text, tối đa 25 MB và 100 trang/slide. Từ chối file mã hóa/đặt mật khẩu. Không hỗ trợ OCR trang scan. |
| BR-23 | Ý tưởng âm thanh tối đa 2 phút và 20 MB. Whisper ưu tiên tiếng Việt. Giữ audio gốc, transcript thô và transcript đã sửa cho đến khi xóa run. |
| BR-24 | Video cuối là MP4, 720p, tỷ lệ 16:9, dài 30–90 giây do hệ thống quyết định, một giọng người lớn tiếng Việt trung tính, phụ đề tiếng Việt và luôn tắt nhạc nền. Chủ thể dễ nhận ra, hình dáng chính, màu sắc và phong cách của tranh là neo tham chiếu cho scene. |
| BR-25 | Sản phẩm không có chức năng download/export hoặc URL video công khai. Playback cần token ngắn hạn do server cấp quyền. |
| BR-26 | Khi người dùng xóa run ở COMPLETED, FAILED hoặc ABANDONED, hoặc hủy run chưa hoàn tất, lifecycle xóa tranh, audio, transcript, snapshot hồ sơ của run, revision story, media scene/video và nội dung liên kết. Lệnh hủy giải phóng khóa active ngay; lệnh xóa/hủy chỉ giữ audit metadata tối thiểu. Run FAILED hoặc ABANDONED không bị purge tự động; nội dung được giữ đến khi người lớn có quyền yêu cầu xóa. Với occurrence Teacher, giữ trạng thái slot mẫu đã dùng và thời điểm claim; xóa pointer đến run/media nhưng không mở lại slot. Không có thao tác xóa video riêng. Unit quota đã tiêu thụ không được hoàn lại (Q119, Q123). |
| BR-27 | Mọi luồng demo chỉ dùng profile, tranh và audio tổng hợp. Dữ liệu trẻ thật nằm ngoài demo, cần chính sách riêng về mục đích, quyền, phân quyền, chuyển dữ liệu cho provider và lifecycle. |
| BR-28 | Subscription capacity lớp tính theo tháng/năm và tiền VND. MoMo và VNPAY là payment adapter V1. V1 không dùng VietQR. |
| BR-29 | Slot lớp mua thêm được kích hoạt sau khi xác minh thanh toán và tính prorate cho phần thời gian còn lại của kỳ hiện tại; ngày gia hạn tiếp theo không đổi. |
| BR-30 | Có thể tắt auto-renew. Capacity đã trả tiền còn hiệu lực đến hết kỳ. V1 không tự tính hoàn tiền prorate giữa kỳ; ngoại lệ xử lý thủ công ngoài hệ thống. |
| BR-31 | Gia hạn thất bại bắt đầu 7 ngày grace. Hết grace thì hạn chế tạo lớp mới và story run mới; vẫn cho truy cập lớp, roster, lịch sử và quản lý thanh toán hiện có. |
| BR-32 | Hạ capacity cần School Manager chọn lớp sẽ tạm ngưng trước khi xác nhận. Ghi một sự kiện append-only cho từng lớp được chọn, có chung change-group ID và thời điểm hiệu lực. Lớp/roster/lịch sử tạm ngưng được giữ lại ở chế độ chỉ đọc; không xóa dữ liệu. |
| BR-33 | Thông báo billing gửi admin thanh toán trong app và email: nhắc trước hạn 7 ngày và 1 ngày, khi thanh toán thành công/thất bại và khi grace hết hạn. |
| BR-34 | Audit hệ thống chỉ ghi metadata actor, action, resource và kết quả. Không ghi media, transcript, prompt, token, signed URL hoặc tên trẻ trong audit/log/metric label. |
| BR-35 | Xóa hồ sơ trẻ Parent hoặc Teacher bắt đầu lifecycle theo owner scope: thu hồi quyền, chặn run mới, xóa context hồ sơ và nội dung run liên quan; chỉ giữ metadata audit/enrollment cần thiết. Không tác động hồ sơ thuộc scope khác. |
| BR-36 | Giáo án tải lên, gợi ý người lớn và output model đều là nội dung không đáng tin cậy. Áp dụng safety policy có version dành cho trẻ trước khi hiển thị script hoặc tạo video. Trước playback, gate tự động kiểm tra frame được lấy mẫu, toàn bộ transcript lời kể và toàn bộ phụ đề của video đã ghép. Output bị chặn không phát được và quay lại bước xem script; gate này không thêm bước duyệt video cuối bởi người. Nội dung không chẩn đoán trẻ, đưa lời khuyên y tế/tâm lý, tiết lộ dữ liệu hồ sơ hoặc hướng trẻ tới hoạt động nguy hiểm. |
| BR-37 | Teacher chỉ chiếu video mẫu cho lớp sau khi Teacher phụ trách ghi nhận xác nhận riêng có audit cho occurrence. Đây là xác nhận đối tượng/mục đích trình chiếu, không phải duyệt video cuối. Xử lý dữ liệu trẻ thật vẫn cần chính sách quyền riêng tư được xem xét riêng. |
| BR-38 | Quota video theo tháng dương lịch `Asia/Ho_Chi_Minh`, tách riêng: Parent tính vào tài khoản Parent; Teacher tính vào tổ chức sở hữu occurrence, không có Teacher-account pool. Full-video request chỉ được xem là accepted sau khi AI Policy xác nhận compute reservation và Billing xác nhận quota admission bằng cùng idempotency key; Billing ghi đúng một usage unit trong transaction sở hữu riêng trước dispatch. Đây là saga nhiều owner, không phải transaction SQL xuyên module; receipt mơ hồ được đối soát trước dispatch. Mỗi accepted request vẫn tiêu thụ một unit kể cả khi sau đó lỗi provider/kỹ thuật hoặc safety block; không hoàn quota. Scene retry không phải request mới và không tiêu thụ thêm unit. Budget/quota admission bị từ chối không tạo accepted generation/job/usage, không chiếm run request cap và không dispatch. Hết quota thì từ chối request video mới bằng VIDEO_QUOTA_EXCEEDED; vẫn cho xem video/dữ liệu cũ. Request mới chỉ được gửi lại khi scope có grant hợp lệ; quyền mua/cấp thêm quota chưa được quyết định tại Q193. Billing sở hữu grant và immutable usage ledger; AI Policy chỉ hạch toán/reserve tài nguyên nền tảng (GPU/compute), không sở hữu product quota. Không lưu số dư còn lại mutable. Mức included cấu hình riêng cho school và Parent, số lượng chốt sau benchmark synthetic (Q115). Dùng grant included hiện tại trước, sau đó top-up FIFO; included hết hạn cuối tháng, top-up carry-forward (Q117–Q118, Q124–Q126). Bắt đầu giữa tháng nhận đủ included (Q121); xóa run không hoàn unit (Q119); top-up một lần (Q120, Q128, Q132). |
| BR-39 | Tất cả trạng thái chờ thao tác người lớn, kể cả `DRAFT`, bắt đầu adult-wait khi không còn AI job và cần command người lớn. Tại +144 giờ tạo đúng một inbox reminder theo dedupe key; thử push best-effort và email best-effort chỉ tới địa chỉ đã xác minh của owner hiện tại. Inbox là nguồn chuẩn; lỗi gửi email/push không đổi trạng thái run. Ở +168 giờ, `VIDEO_READY` thành `COMPLETED`, trạng thái adult-wait khác thành `ABANDONED`, nhả khóa owner nhưng giữ nội dung đến khi người dùng xóa. `VIDEO_ADMISSION_PENDING` là system work, không có idle timer; nếu admission bị từ chối, StoryRun về `SCRIPT_REVIEW` và bắt đầu adult-wait mới (Q133, Q136). |
| BR-40 | Người lớn có thể hủy run chưa hoàn tất để nhả khóa ngay và xóa content theo lifecycle; xóa run ở COMPLETED, FAILED hoặc ABANDONED xóa linked media/content. Request video accepted không được hoàn quota; Teacher sample claim thành công vẫn giữ. (Q123/Q128/Q133/Q134) |
| BR-41 | School Manager của organization sở hữu lớp/run chỉ được force-close conflicting run trong emergency qua command tường minh có reason và metadata audit. Lệnh không cho phép xem media; quota claim và sample claim được giữ nguyên. Cách gán/lưu permission và actor resolver còn mở tại §31.10. (Q134) |
| BR-42 | Q137/Q141/Q146/Q167/Rev66: Parent line guide và Teacher drawing guide là tùy chọn; lesson presentation có thể cung cấp kiến thức/guide trước khi vẽ. Parent không preselect subject của tranh; review subject sau capture. Teacher guide/deck bám lesson/plan đã duyệt, progressive adaptive 4–8 bước; Teacher presentation hỗ trợ text/ảnh/video/SVG theo slide. | FR-P-02/04/11/12/13; FR-T-18/19/20; FR-AI-14/15/22 | UC-02/17 | Parent guide; lesson presentation/guide revisions; AI jobs; vector assets | AC-33/34/44; AT-14/15/18; Rev66 |
| BR-43 | Teacher guide bao quát lesson/plan đã duyệt và hướng dẫn vẽ tiến dần từ nét cơ bản đến hình đủ nhận biết, với adaptive 4–8 bước; presentation hỗ trợ nội dung/ảnh/video/SVG theo vị trí slide đã sắp xếp. Teacher điều khiển trình chiếu; khi plan hoặc nội dung nguồn đổi, asset/guide phụ thuộc phải được đánh dấu stale theo revision. (Q138–Q140/Q142/Q167; Rev66) |
| BR-44 | SVG catalog, SVG engine và AI guide/visual không tiêu quota video. Dùng giới hạn request và compute cap riêng; mức số cụ thể phải được benchmark/cấu hình. AI guide/visual không nhận profile, ảnh/tranh, giọng nói hoặc định danh trẻ. (Q143/Q146; Rev66) |
| BR-45 | Video theo pipeline VLM image understanding → structured LLM story → storyboard 5–15 scene → adult script confirmation → scene reference/Character Bible → LTX-2.5 image-to-video trên Modal L40S → consistency/technical validation → FFmpeg composition → TTS/subtitles tiếng Việt, không nhạc → automated safety gate → private playback. Mỗi run có một trẻ; không có collaboration, public gallery/download hoặc final human video approval. Video không phù hợp quay lại script review, tối đa hai lần full regeneration sau request đầu; mỗi scene tối đa hai technical retries sau lần đầu. (Q144 và các quyết định pipeline đã chốt) |
| BR-46 | Q146/Rev66 (supersedes text-only Q145): Parent có thể yêu cầu hoặc bỏ qua SVG guide 4–8 bước progressive cho topic chung; catalog đã duyệt ưu tiên, AI draft khi thiếu và capability bật. Không gửi dữ liệu trẻ; output riêng tư/provenance/cleanup, có cap riêng; mọi lỗi không chặn capture bắt buộc và subject review sau capture. | FR-P-11/12; FR-AI-15 | UC-02/16 | ai_jobs; core asset/lineage; ai_policy; không ghi video quota | AC-44/45; AT-18/19 |

<a id="srs-5"></a>
## 5. Luồng người dùng

### 5.1 Phụ huynh

Parent có thể mở thư viện public, lesson được chia sẻ đích danh/nhóm hoặc lesson đã dạy cho child profile đang được share. Lesson được dùng như preset; bản cá nhân hóa không sửa version nguồn. Lesson history có thời hạn 30 ngày tính từ lần delivery/open đầu tiên; revoke/unpublish giữ metadata trung tính nhưng không mở lại lesson content.

1. Đăng nhập bằng tài khoản Parent riêng, chọn hồ sơ trẻ thuộc tài khoản đó và xác nhận quyền xử lý dữ liệu còn hiệu lực.
2. Topic tự nhập/chọn và lesson từ Gallery đều tùy chọn. Nếu Parent mở Gallery, chỉ đọc lesson public/shared mà Parent có quyền; lesson pin phải xác thực access hiện hành và exact version/hash.
3. Nếu chọn lesson, Parent có thể xem presentation kiến thức của lesson trước khi vẽ. Guide của lesson hoặc guide theo topic là tùy chọn: lấy SVG guide đã duyệt từ catalog trước; nếu thiếu thì người lớn có thể yêu cầu AI tạo draft nếu capability được bật, xem trước rồi chấp nhận/bỏ. Guide có 4–8 bước adaptive, không nhận dữ liệu trẻ; thiếu guide/lỗi/disabled/timeout/rejection không chặn capture.
4. Trẻ vẽ trên giấy. Người lớn chụp tranh của đúng một trẻ (camera là hành động chính; thư viện ảnh là lựa chọn khác). Ảnh là bắt buộc; chưa có ảnh thì chưa tạo StoryRun hoặc gọi VLM.
5. VLM phân tích ảnh và, nếu topic/lesson được chọn, kiểm tra độ phù hợp. Nếu có lệch chủ đề, hệ thống báo cho người lớn đổi topic hoặc chụp lại tối đa một lần. Nếu chụp lại, dùng chủ thể do AI nhận diện từ ảnh mới; lesson đã chọn vẫn là nguồn kiến thức/presentation.
6. Nếu có ghi âm, chạy Whisper; hiển thị transcript và yêu cầu người lớn sửa/xác nhận. Hiển thị subject/đặc điểm/độ không chắc chắn của ảnh; người lớn xác nhận hoặc sửa subject theo revision.
7. Người lớn duyệt context snapshot tối thiểu (profile revision, age band, interests allowlist, topic/ý tưởng, consent version và lesson pin nếu có). Backend xác thực profile/consent/lesson access và gắn run với exact lesson version/hash.
8. Sau khi subject được xác nhận, backend dựng catalog candidate set từ lesson versions PUBLIC/SHARED Parent được quyền xem, lọc theo tuổi/topic/subject/features/context; lesson pin giới hạn vào exact version/hash. Qwen3.5 chọn ID và giải thích theo profile summary/tags, topic, subject/features và narration đã xác nhận; nếu không có hoạt động phù hợp, có thể tạo đúng 3 draft qua quality gate. Không gửi ảnh/audio thô/định danh.
9. Parent chọn một hoạt động chính trước khi tạo kịch bản. Người lớn có thể yêu cầu bộ gợi ý thay thế; hệ thống loại các lựa chọn đã hiển thị/bị từ chối để tránh lặp. Hoạt động đã chọn được đưa vào story context và sẽ làm sau video. Lỗi/timeout/disabled/rejection phải có trạng thái dễ hiểu; Parent có thể sửa lựa chọn hoặc tiếp tục theo policy khôi phục, không có retry AI tự động.
10. AI tạo story/storyboard cá nhân hóa từ tranh, context đã duyệt, subject và hoạt động chính. Chỉ áp dụng lesson script direction nếu version cho phép `script_following_allowed`. Parent có thể gợi ý tối đa ba lần viết lại nhưng không sửa trực tiếp scene.
11. Người lớn xem và xác nhận revision script/storyboard cuối trước video.
12. Backend tạo video mới cho đúng trẻ từ ảnh tranh đó theo pipeline §6.2.2; không tái sử dụng video của trẻ khác. Video có thể khác theo artwork/profile nhưng đi theo hướng script khi được phép/bật.
13. Chỉ mở playback sau kiểm tra kỹ thuật và safety. Parent có thể hoàn tất hoặc yêu cầu tạo lại tối đa hai lần; video cũ bị ẩn ngay khi request thay thế được nhận. Accepted video request tiêu thụ quota theo quy tắc Billing, kể cả lỗi kỹ thuật/provider/safety.
14. Sau video, nếu có lesson pin thì hiển thị đầy đủ outdoor activities từ exact pinned version/hash; nếu không có pin thì hiển thị hoạt động chính đã chọn trước script. Giữ reminder 144h, idle close 168h, cancel/delete lifecycle, private playback và feedback theo hồ sơ được share; không có chat, completion toggle hoặc gửi tranh qua feedback.

Trình tự bắt buộc là hồ sơ/consent → (tùy chọn) topic hoặc lesson presentation → (tùy chọn) SVG guide → chụp ảnh bắt buộc → VLM và kiểm tra topic/lesson match → người lớn xác nhận subject/context → chọn một hoạt động chính → tạo và duyệt story → tạo video mới từ tranh → sau video hiển thị hoạt động đã chọn và mọi hoạt động của exact lesson pin nếu có. Topic, lesson và guide là tùy chọn; ảnh và xác nhận hoạt động chính trước script là bắt buộc.

### 5.2 Giáo viên

Teacher có thể tạo lesson reusable của trường hoặc dùng bản public/được share như preset; dùng preset không sửa source version. Occurrence có thể dùng preset hoặc plan tự tạo đã được duyệt; nếu có preset thì occurrence pin đúng lesson/version/plan đã chọn.

1. Đăng nhập bằng tài khoản Teacher web riêng và mở lớp của tổ chức được phân công.
2. Tạo hoặc chọn hồ sơ trẻ được quản lý. Mỗi hồ sơ chỉ thuộc một lớp đang hoạt động tại một thời điểm. Có thể nhập nhanh câu trả lời từ phiếu phụ huynh.
3. Tạo occurrence, chọn dùng hoặc không dùng preset lesson; có thể upload tài liệu theo template/form chuẩn.
4. Parser trích xuất text theo giới hạn hiện hành, không OCR scan. Hệ thống lọc/map allowlist fields vào structured draft; file gốc và raw plan không gửi model. Teacher preview/correct extracted draft trước khi AI hỗ trợ tạo lesson/plan.
5. Lesson draft do AI hỗ trợ luôn ở trạng thái draft. Teacher review/chỉnh sửa, lưu version và gửi School Manager review nếu muốn public; Admin duyệt nếu muốn public toàn nền tảng. Lesson có activity list và một presentation chỉnh sửa được: Teacher sửa nội dung/ thứ tự slide, upload ảnh, thêm video link YouTube/Vimeo, chọn SVG catalog hoặc yêu cầu AI tạo SVG draft nếu capability được bật, rồi đặt media vào slide phù hợp. Hình/video/AI draft phải qua kiểm tra và Teacher review trước khi xuất bản.
6. Guide vẽ là tùy chọn. Teacher có thể lấy guide SVG catalog hoặc guide gắn lesson; khi thiếu, Teacher có thể yêu cầu tạo draft theo đúng chủ thể/kiến thức của lesson. Guide dùng 4–8 bước adaptive và trình bày tiến dần từ nét cơ bản đến hình đủ nhận biết.
7. Trong buổi học, Teacher mở presentation/guide và điều khiển Back/Next/skip/regenerate theo quyền. Trẻ vẽ bằng giấy/bút; không có canvas chung hoặc nhiều trẻ trong một run.
8. Video mẫu vẫn là luồng riêng. Hệ thống chọn đồng xác suất một trẻ trong tập đủ điều kiện; Teacher xác nhận child/context. Candidate stale được chọn lại tối đa một lần; nếu không có candidate thì dừng. Trước xác nhận không tạo/accept StoryRun, AI job, quota usage hay sample claim. Một occurrence có tối đa một video mẫu thành công.
9. Ghim approved plan vào occurrence; nếu có preset thì pin lesson/version và Teacher chọn đúng một activity đã duyệt cho run mẫu. Plan-only occurrence không yêu cầu lesson preset.
10. Teacher chụp tranh giấy của trẻ đó bằng camera trình duyệt hoặc tải ảnh chụp bằng điện thoại. Nhập ý tưởng bằng chữ hoặc ghi âm; Whisper ưu tiên tiếng Việt, Teacher xem/sửa/xác nhận transcript và chủ thể nhận diện. Sửa chủ thể tạo revision VLM mới. Không dùng ảnh của trẻ khác trong cùng run.
11. VLM phân tích tranh và tạo neo nhận diện; LLM tạo story/storyboard 5–15 scene cá nhân hóa theo profile. Teacher có thể đặt hướng kể theo lesson và gợi ý tối đa ba lần viết lại.
12. Teacher xem và xác nhận revision cuối của script/storyboard. Lesson có thể bật/tắt script-following; nếu bật, video đi theo hướng kịch bản nhưng từng video vẫn mới và có thể khác theo tranh/profile. Chỉ sau xác nhận mới chạy pipeline §6.2.2.
13. Backend chuẩn bị ảnh tham chiếu/Character Bible từ duy nhất bức tranh được chọn, tạo clip scene bằng LTX-2.5 trên Modal L40S, kiểm tra consistency/technical quality, ghép bằng FFmpeg, tạo lời kể tiếng Việt và phụ đề, tắt nhạc nền, rồi chạy safety validation tự động trên output đã ghép. Chỉ video qua gate mới phát được; video sẵn sàng được chiếu trong run/occurrence, không có bước duyệt video cuối.
14. Nếu video không phù hợp, Teacher yêu cầu tạo lại; output cũ bị ẩn khỏi playback ngay khi request thay thế được nhận và run quay về duyệt script. Tối đa hai request tạo lại toàn video sau request đầu; mỗi scene có tối đa hai retry kỹ thuật sau lần đầu. Mỗi request video được nhận tính quota dù lỗi kỹ thuật/safety; lỗi trước video mẫu playable đầu không claim slot occurrence. Sau claim đầu, slot không mở lại, kể cả khi các lần tạo lại lỗi (Q127/Q128).
15. Teacher phụ trách xác nhận riêng việc chiếu video cho cả lớp ở occurrence đó. Đây là xác nhận audience/use, không phải duyệt video. Khi không còn AI job và video sẵn sàng, Teacher có thể hoàn tất hoặc tạo lại; adult-wait/nhắc 144h/đóng 168h, hủy run, giữ media đến xóa và quota không hoàn theo các quy tắc chung.

Sau buổi học, Parent được liên kết có thể xem lesson đã dạy trong 30 ngày theo §31.6, tải nội dung còn quyền truy cập và gửi feedback riêng trong tenant đó.


#### Decision table UC-05 — chọn trẻ mẫu (TO-BE)

Hệ thống tính tập ứng viên theo policy version, consent, enrollment và assignment còn hiệu lực rồi chọn đồng xác suất đúng một trẻ; Teacher xem và xác nhận child/context. Candidate stale được chọn lại tối đa một lần; tập rỗng thì dừng. Trước xác nhận không tạo/accept StoryRun, AI job, quota usage hoặc sample claim. Bảng dưới giữ các guard/response kỹ thuật chưa có contract ở trạng thái mở. “State unchanged” nghĩa là không phát minh occurrence/run state mới; transition cụ thể phải dùng state đã có tại §§6/22–23.

| Case | Guard/input | Action | Response and target state | Evidence / decision |
|---|---|---|---|---|
| Tập đủ điều kiện có ít nhất 1 trẻ | Candidate phải thuộc roster/enrollment và Teacher assignment hiện hành, đồng thời thỏa consent/exclusion policy đang có hiệu lực. | Server chọn đồng xác suất một typed child/recipient reference; trả đúng một lựa chọn cho assigned Teacher. | Hiển thị child/context đã lọc để Teacher xem; chỉ sau xác nhận mới tạo/accept StoryRun và tiến hành admission. Occurrence giữ state hiện hành trước xác nhận. | Owner đã chọn đồng xác suất và xác nhận bởi Teacher. Selection evidence/snapshot schema vẫn OPEN; run-input context snapshot sau xác nhận vẫn bắt buộc riêng. |
| Candidate stale trước xác nhận | Candidate hoặc assignment/grant/consent revision không còn hiện hành. | Revalidate; cho chọn lại tối đa một lần. | Nếu candidate mới còn hợp lệ thì trả một lựa chọn mới; nếu không thì dừng an toàn. Không tạo run/job/quota/claim trước confirmation. | Owner đã chọn giới hạn một lần reselect cho candidate stale; error/expiry/idempotency contract còn OPEN. |
| Tập rỗng | Không candidate thỏa policy đã duyệt. | Không fallback sang profile khác, không cho Teacher tự chọn ngoài tập. | Dừng selection; không tạo sample run, AI job, quota usage hoặc claim; giữ occurrence ở state hiện hành và hiển thị thông báo không có lựa chọn hợp lệ, không tiết lộ lý do loại theo từng child. | Owner đã chọn stop/no-fallback. Error code, retry control, audit event và selection-attempt evidence vẫn OPEN. |
| Grant/consent không còn hợp lệ trước khi trả lựa chọn hoặc confirm | Server kiểm tra lại version/hiệu lực trước mỗi lần đọc/command; revoke phải chặn read/token mới và job chưa accepted. | Deny command và không đưa child media/context vào response; không accept job. | Màn hình denied/refresh theo error handling §21.6; outcome cho selection đang chờ (clear, retain hidden hay yêu cầu selection mới) OPEN. | Ghi nhận allow/deny metadata theo policy hiện hành; retention/field schema OPEN §31.10(17). |
| Teacher không xác nhận hoặc đóng màn hình | Chưa có command confirm gắn đúng occurrence/selection/input revision. | Không tạo hoặc accept StoryRun. | Giữ state hiện hành; timeout, expiry của lựa chọn và resume behavior OPEN. | Event/audit cho confirm/decline/timeout và thời gian giữ lựa chọn OPEN. |
| Teacher yêu cầu chọn lại | Candidate trước bị stale trước confirmation; giới hạn một lần chưa dùng. | Re-run selection một lần theo policy hiện hành; không cho reselect tùy ý. | Trả lựa chọn mới hoặc dừng nếu không có candidate; không nhận run/job/quota/claim trước confirmation. | Owner đã chọn tối đa một reselect chỉ cho stale candidate; attempt correlation/evidence OPEN. |
| Hai request đồng thời claim cùng occurrence | Compare-and-set/serialized command phải kiểm tra occurrence revision và one-successful-sample invariant. Cơ chế vật lý chưa duyệt. | Tối đa một command có thể ghi nhận successful sample cho occurrence; request trùng idempotent hoặc conflict theo contract được duyệt. | Winner tiếp tục flow; loser không thể tạo successful sample thứ hai. Run/quota của request đã accepted xử lý theo receipt/quota rules hiện hành; reconciliation contract còn cần review. | Q-01 + D-06; exact claim timing, key/index và audit evidence OPEN; không tạo cross-owner transaction. |
| Revoke xảy ra trong lúc Teacher chờ xác nhận | Grant revision hiện tại khác revision dùng để tạo view hoặc consent hết hiệu lực theo policy. | Re-authorize khi confirm; deny nếu quyền không còn. | Không accept job chưa accepted. Với job đã accepted, không retarget hoặc tự hủy; áp dụng grant/job policy đã duyệt, hiện còn OPEN cho trường hợp này. | Q-04 / D-09; permission revision và correlation cần được trace; retention OPEN. |

Run-input context snapshot bắt buộc chỉ được tạo từ dữ liệu tối thiểu đã duyệt sau xác nhận. Có thể dùng metadata-only selection evidence để đối soát, nhưng field list, retention và cách xử lý concurrent confirmation chưa được chốt. Không lưu seed có thể tái nhận diện hoặc child media trong audit theo suy luận.

### 5.3 Tổ chức và thanh toán

1. School Manager của organization tạo lớp khi còn capacity (10 slot lớp bao gồm trong gói cơ bản cộng slot mua thêm).
2. School Manager phân công một Teacher phụ trách mỗi lớp và quản lý roster/phân lớp hồ sơ.
3. School Manager mua slot lớp bổ sung qua adapter MoMo/VNPAY theo tháng/năm. Chỉ lưu provider reference, không lưu thông tin xác thực thanh toán.
4. Khi xác minh thanh toán thành công, cập nhật kỳ capacity; slot mua giữa kỳ được tính prorate.
5. Gửi nhắc trong app/email trước hạn 7 ngày và 1 ngày; gửi thông báo thanh toán thành công/thất bại và khi grace hết hạn.
6. Gia hạn lỗi có 7 ngày grace. Hết grace thì hạn chế tạo lớp và story run mới, vẫn giữ quyền xem lớp/roster/lịch sử hiện có và quản lý thanh toán.
7. Khi hạ capacity, School Manager chỉ định lớp cần tạm ngưng. Dữ liệu lớp bị ngưng vẫn còn và chỉ đọc.

<a id="srs-6"></a>
## 6. Vòng đời story và video

### 6.1 Các stage logic

| Stage | Kết quả cần có | Hành động người dùng hoặc quy tắc hệ thống |
|---|---|---|
| Draft | Một trẻ và tranh nguồn được gắn với run | Backend bắt buộc chỉ có một profile ref |
| Xem input | Ý tưởng người lớn tồn tại dạng text hoặc transcript để xem | Whisper chuyển giọng nói thành chữ, người lớn xác nhận |
| Xem chủ thể | VLM trả cấu trúc chủ thể/entity/mức không chắc chắn | Người lớn xác nhận hoặc sửa; sửa sẽ chạy lại VLM |
| Xem context | Snapshot profile tối thiểu và lesson/script direction nếu người lớn chọn đã được duyệt | Parent phải chọn một activity chính trước story. Sau video, no-pin trả activity đã lưu trong run; lesson pin trả toàn bộ activity của exact version và đánh dấu activity chính. Teacher run xác nhận approved activity trong plan trước generation. |
| Story draft | Tạo script có version và 5–15 scene | Output LLM phải khớp schema và safety policy |
| Viết lại | Tạo revision story bất biến mới | Tối đa ba request viết lại sau bản đầu; xem xét từng revision |
| Xác nhận script | Có hash revision script/storyboard đã xác nhận | Bắt buộc trước mỗi request tạo video |
| Tạo video | Có clip từng scene, lời kể, phụ đề và MP4 đã ghép | LTX-2.5 qua Modal L40S; mỗi scene tối đa hai retry kỹ thuật tự động |
| Sẵn sàng phát | Có artifact đạt kiểm tra kỹ thuật và safety | Hiển thị ngay; run vẫn active cho đến khi người lớn bấm Hoàn tất hoặc Tạo lại; không có duyệt video |
| Tạo lại chất lượng | Run quay lại bước xem script | Người lớn đánh dấu không phù hợp; video cũ ẩn playback từ lúc chấp nhận request tạo lại; script phải xác nhận; tối đa hai lần tạo lại |
| Hoàn tất, thất bại, abandon hoặc hủy | Run ra khỏi tập active | Hoàn tất do người lớn hoặc idle closeout từ VIDEO_READY; run chờ khác thành ABANDONED sau 168 giờ adult-wait. FAILED/ABANDONED giữ nội dung đến khi xóa; cancel giải phóng khóa rồi xóa theo lifecycle. Run lỗi trước playable claim đầu không chiếm slot mẫu Teacher |
| Đã xóa | Lifecycle đã xóa toàn bộ nội dung liên kết | Chỉ giữ audit metadata tối thiểu; quota đã tiêu thụ và claim mẫu thành công vẫn được giữ |

Kết quả AI bất đồng bộ phải khớp revision run dự kiến, input hash, hash snapshot context hồ sơ, lesson version nếu có pin, activity chính đã chọn, Teacher activity/plan ref nếu áp dụng và contract version. Activity chính của Parent là story context; các hoạt động bổ sung từ lesson chỉ để thực hiện sau video và không làm thay đổi script đã duyệt. Kết quả cũ được ghi nhận là stale, không được ghi đè dữ liệu mới hơn.

### 6.1.1 Mô hình trạng thái đề xuất

Tên trạng thái dưới đây là giá trị đích ở domain. Nhãn UI phải được Việt hóa, không dùng tên nội bộ/provider để hiển thị cho người dùng.

| Aggregate | Trạng thái đề xuất | Tóm tắt chuyển trạng thái được phép |
|---|---|---|
| StoryRun | DRAFT, INPUT_PROCESSING, INPUT_REVIEW, SUBJECT_REVIEW, PREPARATION_REVIEW, STORY_GENERATING, SCRIPT_REVIEW, VIDEO_ADMISSION_PENDING, VIDEO_QUEUED, VIDEO_GENERATING, VIDEO_SAFETY_VALIDATING, VIDEO_READY, SAFETY_BLOCKED, COMPLETED, FAILED, ABANDONED, DELETE_PENDING, DELETED | `run_state` mô tả bước nghiệp vụ nhìn thấy được; `AiJob.job_state` + `job_stage` mô tả xử lý ASR/VLM/story/video chi tiết. DRAFT là adult-wait khi cần người lớn nhập/xác nhận dữ liệu; DRAFT → INPUT_PROCESSING khi input đã nhận và ASR/VLM job được enqueue; input job thành công hoặc lỗi có thể khắc phục → INPUT_REVIEW; người lớn xác nhận transcript → SUBJECT_REVIEW; sửa chủ thể tạo VLM job mới và quay INPUT_PROCESSING → SUBJECT_REVIEW. Xử lý AI đang chạy không phải adult-wait dù màn hình hiển thị stage. SUBJECT_REVIEW/PREPARATION_REVIEW → STORY_GENERATING chỉ khi subject, context và một activity chính đã chọn/xác nhận; Teacher dùng activity đã duyệt, Parent bắt buộc chọn một activity trước script. STORY_GENERATING → SCRIPT_REVIEW; SCRIPT_REVIEW → STORY_GENERATING khi rewrite hợp lệ hoặc VIDEO_ADMISSION_PENDING khi script revision đã xác nhận; chỉ admission accepted mới đưa StoryRun/VideoGeneration sang VIDEO_QUEUED. Queue → generation → safety validation → VIDEO_READY khi đạt. Chỉ state không có job đang xử lý và cần command người lớn mới adult-wait: DRAFT, INPUT_REVIEW, SUBJECT_REVIEW, PREPARATION_REVIEW, SCRIPT_REVIEW, SAFETY_BLOCKED (khi cần người lớn) và VIDEO_READY. VIDEO_ADMISSION_PENDING là system work, không arm idle timer; budget/quota rejection đưa run về SCRIPT_REVIEW và bắt đầu adult-wait mới; receipt mơ hồ giữ pending tới reconcile. `last_meaningful_activity_at` do server ghi UTC khi người lớn gửi command/review/xác nhận có hiệu lực; polling/push receipt/app heartbeat không reset idle. `adult_wait_started_at` bắt đầu khi AI job kết thúc/lỗi và run thực sự cần thao tác người lớn. Sau 144 giờ tạo inbox reminder, push best-effort và email nếu current-owner email đã xác minh; sau 168 giờ VIDEO_READY → COMPLETED, adult-wait state khác kể cả DRAFT → ABANDONED; cả hai nhả khóa và giữ nội dung đến khi user xóa. AI job có deadline độc lập 6 giờ và không bị idle-closeout khi còn QUEUED/RUNNING/RETRY_WAIT/AWAITING_RECONCILIATION. Hủy run chưa kết thúc → DELETE_PENDING, nhả khóa ngay và khởi động purge. COMPLETED, FAILED, ABANDONED, DELETE_PENDING, DELETED không chiếm khóa. Reassignment không đổi state: quyền chuyển sang Teacher hiện được phân công, quyền cũ/token bị thu hồi, audit metadata được ghi. Ngoại lệ có ghi nhận: SCRIPT_GENERATING và SCRIPT_GENERATION_UNKNOWN là hai giá trị mở rộng ngoài danh mục trạng thái này; hai giá trị được giữ trong response và dữ liệu lưu, và run ở hai giá trị này được phép hủy theo UC-11. |
| VideoGeneration | ADMISSION_PENDING, ADMISSION_REJECTED, ACCEPTED, QUEUED, GENERATING, TECHNICAL_VALIDATING, SAFETY_VALIDATING, READY, SAFETY_BLOCKED, FAILED, REJECTED_BY_ADULT, SUPERSEDED | Một hàng generation bền vững trước tiên là intent có idempotency key. Chỉ chuyển từ ADMISSION_PENDING sang ACCEPTED sau khi AI Policy budget reservation và Billing quota receipt cùng xác nhận; chỉ ACCEPTED mới nhận generation_no, chiếm một trong ba request/run, tạo AI job/outbox và tiêu thụ quota. Budget/quota thất bại chuyển intent sang ADMISSION_REJECTED, không tính request/video quota. Kết quả mơ hồ giữ intent pending để reconciler tra receipt theo cùng key trước dispatch. Khi StoryRun SCRIPT_REVIEW nhận request tạo video, chuyển sang VIDEO_ADMISSION_PENDING. Đây là system work, không adult-wait; `ADMISSION_REJECTED` trả StoryRun về SCRIPT_REVIEW và đặt timer mới, không tiêu quota/cap. `ACCEPTED` đặt `deadline_at = accepted_at + 6h`, gồm queue, retry wait và mọi stage. READY yêu cầu đạt kiểm tra kỹ thuật và safety. Khi người lớn từ chối video và yêu cầu tạo lại, video cũ thành REJECTED_BY_ADULT và bị ẩn khỏi playback ngay; nội dung giữ nội bộ đến khi xóa run. Nếu video thay thế lỗi thì video cũ vẫn không phát lại. Kịch bản mới phải xác nhận trước request tiếp theo. |
| LessonOccurrence | DRAFT, DOCUMENT_REVIEW, PLAN_REVIEW, APPROVED, SAMPLE_AVAILABLE, SAMPLE_USED, ARCHIVED | Import/xem tài liệu trước khi duyệt plan; occurrence đã duyệt cho phép tạo video mẫu; output duy nhất qua safety và phát được sẽ claim slot nguyên tử. Run lỗi trước playback giữ slot chưa dùng. Xóa run xóa pointer run nhưng giữ trạng thái/thời điểm claim. Occurrence cũng ghi xác nhận của Teacher phụ trách khi chiếu video cho lớp. |
| SketchDeckRevision | GENERATING, READY, FAILED, STALE, SUPERSEDED | Tạo từ một approved plan revision/hash; READY chỉ khi bao quát mọi activity, mỗi guide có 4–8 ordered progressive drawing steps theo policy adaptive, nội dung/layout/media validation đạt. Mọi output phải có asset/hash/lineage. Plan/source đổi làm guide phụ thuộc STALE; regenerate tạo revision mới. Không có profile/trẻ subject và không tiêu video quota. |
| AiJob | QUEUED, RUNNING, RETRY_WAIT, SUCCEEDED, FAILED, CANCEL_REQUESTED, CANCELLED, STALE, AWAITING_RECONCILIATION | Trạng thái queue/worker được lưu bền vững; retry kỹ thuật giới hạn có RETRY_WAIT; kết quả hợp lệ thì thành công; lệch hash/revision thì stale; hết retry thì lỗi; provider outcome chưa rõ thì dừng để đối soát trước khi gọi GPU tốn phí lần nữa. |
| OrganizationSubscription | PAYMENT_PENDING, ACTIVE, GRACE, RESTRICTED, CANCEL_AT_PERIOD_END, CANCELED | Chỉ event provider đã xác minh mới chuyển trạng thái thanh toán; gia hạn lỗi vào grace 7 ngày rồi bị hạn chế; hủy subscription ngừng kỳ kế tiếp nhưng quyền đã trả tiền còn đến hết kỳ; capacity gắn kỳ hiệu lực. |
| PaymentAttempt | CREATED, PENDING, SUCCEEDED, FAILED, EXPIRED | Browser redirect chỉ mang tính thông tin; chỉ callback/provider event có chữ ký đã xác minh hoặc đã đối soát mới ghi nhận đã trả tiền. Event trùng không áp dụng capacity lần hai. |

Quy tắc chuyển trạng thái:

- Mỗi application command đổi state và ghi event/outbox trong transaction do owner của aggregate đó sở hữu. Client không tự đặt state; một nghiệp vụ đi qua nhiều owner dùng contract, idempotency receipt và saga, không dùng transaction SQL xuyên module.
- Bộ đếm viết lại story và request video tách riêng. Mỗi run có story đầu và tối đa ba lần viết lại; một request video ban đầu và tối đa hai request tạo lại chất lượng. Admission dùng cùng business command/idempotency key nhưng tách các transaction sở hữu: AI Policy tạo compute reservation; Billing kiểm tra quota scope và ghi usage unit/receipt; chỉ sau khi cả hai receipt được xác nhận thì Story ghi nhận accepted state, chiếm request slot và ghi outbox trong transaction Story riêng. Billing reject thì giải phóng reservation; receipt mơ hồ được tra cứu/đối soát bằng cùng key trước dispatch. Mỗi accepted request vẫn tiêu thụ một quota unit kể cả khi request lỗi kỹ thuật/provider hoặc bị safety block sau đó; không hoàn quota. Retry scene tự động có giới hạn riêng và không tạo product-quota usage mới.
- Tạo lại video chất lượng phải quay về xem/xác nhận revision script hiện hành. Người lớn có thể giữ story hiện tại hoặc yêu cầu AI viết lại trong giới hạn trước khi xác nhận.
- Retry scene kỹ thuật không tính thành lần viết lại story hoặc request tạo lại video. Run lỗi trước khi có output an toàn/phát được không chiếm slot video mẫu của occurrence Teacher.
- VIDEO_READY yêu cầu đạt kiểm tra kỹ thuật và output-safety gate có version. Nếu gate không kiểm tra đủ media, thất bại hoặc trả kết quả không xác định thì chặn playback và đưa run về trạng thái chờ người lớn sửa/xác nhận script. Video đạt được phát ngay; người lớn có thể hoàn tất/tạo lại. VIDEO_READY tự COMPLETED sau 168 giờ adult-wait idle; các trạng thái chờ người lớn khác tự ABANDONED ở cùng deadline, sau nhắc tại giờ 144. Hai kết quả đóng run, nhả khóa và giữ nội dung. Không hoàn quota request đã nhận và không mở lại Teacher sample claim đã dùng.

### 6.2 Quy trình AI

1. **Hiểu ảnh:** VLM nhận diện ứng viên chủ thể, nhân vật, vật thể, bối cảnh, neo phong cách hình ảnh và mức không chắc chắn từ tranh gốc.
2. **Hiểu ý tưởng:** Whisper tạo transcript ưu tiên tiếng Việt. Nội dung người lớn sửa được lưu thành revision riêng.
3. **Lọc context:** backend tạo snapshot context có giới hạn, theo schema version và được người lớn duyệt. Tên trẻ và ghi chú hỗ trợ bị loại.
4. **Lập story:** LLM nhận một tranh, snapshot của một trẻ, ý tưởng đã duyệt, một hoạt động chính Parent đã chọn hoặc một hoạt động Teacher đã duyệt và (chỉ với Teacher) giáo án/hướng kể đã duyệt. Output là script có cấu trúc cùng 5–15 scene.
5. **Cổng xác nhận script:** người lớn xác nhận bản cuối. Mỗi lần AI viết lại, kể cả sau khi video bị đánh dấu không phù hợp, tạo revision mới và cần xác nhận lại.
6. **Chuẩn bị ảnh tham chiếu scene:** dùng tranh gốc/frame tham chiếu đã duyệt và character anchor có version để giữ chủ thể, hình dáng, màu sắc, phong cách dễ nhận ra. Không âm thầm thay hoặc sửa tác phẩm nguồn.
7. **Duyệt budget, quota và tạo video:** use case có một idempotency boundary ở application nhưng không có transaction SQL xuyên module. AI Policy trước hết tạo reservation budget GPU/compute có idempotency key, lease/expiry và mức worst-case cho request; Billing sau đó kiểm tra scope/grant và ghi đúng một `billing.video_quota_usage` nguyên tử trong transaction riêng. Nếu Billing từ chối quota, application giải phóng reservation; reservation mồ côi do tiến trình dừng được dọn/reconcile sau lease. Nếu phản hồi admission bị mất hoặc không rõ, application tra cứu cùng idempotency key ở cả hai owner trước khi dispatch, release hoặc trả lỗi; không tạo request/usage thứ hai. Chỉ khi cả hai receipt đã xác nhận mới ghi/dispatch accepted generation qua outbox. Story chỉ giữ reference opaque đến receipt, không sở hữu budget/quota. Request đã nhận vẫn tiêu thụ unit nếu provider, kỹ thuật hoặc safety stage lỗi; scene retry không tạo unit mới. GPU Modal L40S dùng cho LTX; Modal L4 là ứng viên cho stage model nhỏ hơn. Model/runtime/license và quality evidence cần benchmark riêng.
8. **Kiểm tra kỹ thuật và ghép:** xác minh decode từng scene, kích thước frame, tỷ lệ, thứ tự scene và thời lượng; FFmpeg ghép thành MP4 720p với giọng người lớn cố định và phụ đề tiếng Việt, tắt nhạc nền.
9. **Safety tự động trên output đã ghép:** kiểm tra toàn bộ lời kể/phụ đề và lấy mẫu frame cuối video ít nhất một frame mỗi giây, đồng thời lấy frame đầu/giữa/cuối mỗi scene. Dùng policy/model profile có version, taxonomy, model revision, ngưỡng, bằng chứng calibration và đánh giá false-positive/false-negative làm cổng promote model. Nếu kiểm tra thất bại, thiếu coverage hoặc không xác định, đặt SAFETY_BLOCKED, không cấp playback token và đưa người lớn về xem script. Chỉ ghi policy version, kết quả và mã finding an toàn; không đoán threshold từ prompt. Threshold phải là cổng triển khai đến khi đánh giá trên bộ synthetic.
10. **Playback:** API chỉ cấp token ngắn hạn sau khi kiểm tra kỹ thuật và an toàn đều đạt. Media ở object storage riêng tư; ứng dụng không lấy được URL công khai không giới hạn.

Demo live dự kiến chạy Docker local với dữ liệu tổng hợp và inference live qua Modal. MinIO local không thể được Modal truy cập trực tiếp; contract chuyển file được mô tả tại §24.3. Backend SDK chuyển byte trong allowlist vào scratch prefix riêng theo job trên Modal Volume, gửi path ref/hash opaque tới remote function, tải kết quả bằng SDK, xác minh output trước khi lưu MinIO và xóa scratch. Không truyền media thô trong function argument hoặc cấp Modal quyền rộng vào storage local. Theo tài liệu Modal về payload lớn/bất đồng bộ và vùng lưu trữ, luồng này chỉ dùng synthetic cho đến khi review riêng việc chuyển vùng/xử lý dữ liệu thật được duyệt. [Modal local data](https://modal.com/docs/guide/local-data), [Modal data residency](https://modal.com/docs/guide/data-residency), [Modal Volumes](https://modal.com/docs/guide/volumes).

### 6.2.1 SVG drawing guide và Teacher presentation

SVG là định dạng đầu ra cho guide/ảnh minh họa vector trong sản phẩm; FLUX không thuộc target path và không được dùng làm fallback. Catalog SVG đã duyệt là nguồn ưu tiên. Nếu topic/asset phù hợp chưa có guide, Parent hoặc Teacher có thể yêu cầu AI tạo draft khi capability tương ứng được bật. AI trả dữ liệu vector có cấu trúc theo schema; backend xác thực giới hạn path/tọa độ/dependency/provenance rồi deterministic SVG engine serialize và render. Không chấp nhận SVG/HTML/JavaScript tự do từ model hoặc nguồn upload chưa sanitize.

Guide là chuỗi 4–8 bước adaptive theo độ phức tạp của chủ thể, từ nét cơ bản đến hình đủ nhận biết. Những nét ở bước trước hiển thị liền; nét mới của bước hiện tại hiển thị nét đứt/nổi bật; nét tương lai chưa hiện. Guide phải đủ chi tiết để trẻ nhận ra và vẽ được con vật/đồ vật theo từng bước; một số lượng bước cố định đơn giản không thay cho kiểm tra tính dễ nhận biết/khả năng dạy. Các ngưỡng structural metrics, reviewer rubric, adjudication và cổng bật từng AI capability vẫn là technical/product gate cần chốt.

Lesson Teacher là presentation có version, không chỉ là Sketch Deck sinh tự động. Teacher có thể sửa text, thêm/xóa/sắp xếp slide, tải ảnh gốc lên, thêm link YouTube/Vimeo hợp lệ để nhúng, chọn SVG catalog, yêu cầu AI tạo SVG draft khi bật, và đặt từng media vào slide phù hợp. Media phải qua kiểm tra type/sanitization/safety; video ngoài chỉ cho phép HTTPS YouTube/Vimeo embed và client không fetch tùy ý từ backend. Teacher review draft; School Manager duyệt phạm vi trường, Platform Admin duyệt public toàn nền tảng theo quyền. Published revision không bị sửa trực tiếp; thay đổi tạo draft/version mới và giữ provenance/lineage.

Teacher guide/presentation có thể được mở như kiến thức trước lúc trẻ vẽ. Guide theo lesson hoặc topic là tùy chọn; lỗi, thiếu catalog, capability disabled, timeout hoặc quality rejection không chặn Parent capture hay Teacher tiếp tục lesson. Lesson/guide revision thay đổi làm nội dung phụ thuộc stale theo policy; exact dependency granularity và persistence mapping chờ API/DTR contract.

Parent có capability guide tổng quát riêng: topic từ catalog hoặc text người lớn tự nhập; ảnh/tranh, profile, tuổi chính xác, giọng nói, tên và ID trẻ không được gửi cho line-sketch generation. Parent có thể bỏ qua guide. Ảnh tranh sau cùng vẫn bắt buộc và chỉ được phân tích sau capture. Guide tạm thời/private nếu là draft, có provenance/expiry/cleanup, không gắn profile/StoryRun và không tiêu video quota.

Sketch/vector generation không dùng hoặc trừ `video_quota_usage`; có rate/cost controls riêng. Engine/asset output phải kiểm tra schema, source/license, sanitizer, bounds, path references, safety và lineage. DTR mapping, API version, job persistence, review state, stage render/cache lifecycle và exact asset ownership chưa được chốt bởi Rev66; không suy ra chúng từ code/API hiện có.

### 6.2.2 Pipeline story-video theo đề xuất Sketch2Life

Pipeline áp dụng cho Parent và Teacher, mỗi lần chỉ nhận một tranh của một trẻ. Các bước từ bộ pipeline chủ sở hữu cung cấp được điều chỉnh theo các quy tắc hiện hành: không có vẽ cộng tác/nhiều trẻ; script/storyboard là human approval gate duy nhất; output cuối qua safety gate tự động rồi được phát ngay, không chờ duyệt video cuối; playback riêng trong run, không public gallery/download.

| # | Giai đoạn | Đầu vào/đầu ra và kiểm soát | Công nghệ/ranh giới triển khai |
|---:|---|---|---|
| 1 | Tranh và ý tưởng | Một ảnh tranh bất biến của đúng một trẻ; người lớn nhập ý tưởng chữ và/hoặc xác nhận transcript bằng hướng ASR Whisper. Activity list thuộc lesson và hiển thị sau video; không bắt Parent chọn activity trước khi tạo video. | Android camera/library hoặc Teacher browser camera/upload; upload API resumable; Whisper là development direction, checkpoint/runtime/quality tiếng Việt còn cần pin và benchmark. |
| 2 | Hiểu tranh | VLM nhận diện ứng viên nhân vật/đồ vật/bối cảnh; lưu màu, hình dáng, nét vẽ, bố cục, visual anchors và uncertainty gắn với hash tranh. Các anchor chỉ mô tả bức tranh của trẻ được chọn. | Qwen3.5-VL là model phát triển theo hướng dẫn owner; chạy qua Modal. Pinned checkpoint, serving profile và structured-output conformance phải được xác nhận ở deployment manifest/POC. |
| 3 | Xem xét input | Người lớn xem/xác nhận transcript và chủ thể; sửa subject tạo revision VLM mới trên đúng ảnh hash. Người lớn duyệt context tối thiểu và lesson direction nếu có. Teacher xác nhận lesson/activity đã duyệt; Parent chọn một activity chính trước story. Activity chính là story context; các hoạt động còn lại của lesson được hiển thị sau video và không sửa script. | Client Parent/Teacher + FastAPI application; `story.review_decisions`. |
| 4 | Tạo story | Hướng model Qwen3.5-VL tạo/điều phối nội dung story có cấu trúc gồm mở đầu-diễn biến-kết thúc, nhân vật/hành động và lời kể tiếng Việt dựa trên tranh, ý tưởng đã xác nhận, snapshot cá nhân hóa tối thiểu và lesson/script direction nếu có. Parent chọn một activity chính trước khi story; activity đó là story context và sẽ diễn ra sau video. Teacher dùng activity đã duyệt từ plan. | Story Planner port, structured JSON output, activity/version snapshot, prompt/policy version pin; model/checkpoint, safety, license, latency và quality cần POC trước khi promote. |
| 5 | Tạo storyboard | Hướng model Qwen3.5-VL hỗ trợ chia nội dung thành 5–15 scene, tổng thời lượng do hệ thống chọn trong 30–90 giây; mục tiêu khoảng 6 giây/scene nhưng planner có thể điều chỉnh theo tổng thời lượng. Mỗi scene gồm action, image/video prompt có kiểm soát, narration segment, timing và character anchor. | Structured output + versioned prompt template; scene lưu thành các row, không giữ danh sách vô hạn trong một JSON field. |
| 6 | Duyệt script/storyboard | Adult xem bản story hiện hành và xác nhận hash/revision cuối trước khi generation. Có một bản đầu và tối đa ba lần viết lại. Không cho sửa tay từng scene/thứ tự trong V1. | Parent/Teacher web/mobile review + FastAPI; `story.review_decisions`. Teacher có thể định hướng từ plan; Parent gửi gợi ý. |
| 7 | Chuẩn bị reference | Tạo Character Bible cho tranh duy nhất được chọn: identity anchors, màu, hình dáng và phong cách; chuẩn bị ảnh tham chiếu/layout cho từng scene. Không lấy ảnh/profile của trẻ khác. | Python + OpenCV/Pillow; segmentation như SAM2 chỉ là tùy chọn sau POC, không bắt buộc V1. Derived image có asset ID/hash/lineage riêng. |
| 8 | Sinh video từng scene | Image-to-video tạo clip riêng từ reference và action đã duyệt. Scene độc lập có thể chạy song song trong giới hạn GPU; scene cần nối frame thì chạy tuần tự. Mỗi scene có một lượt đầu và tối đa hai automatic retry; hết lượt làm request lỗi, không gọi lặp vô hạn. | LTX-2.5 official-compatible inference workflow, PyTorch/workflow đã pin; Modal GPU L40S là mục tiêu theo Q144. WAN là dev candidate riêng, chưa thay mục tiêu LTX nếu chưa có quyết định owner/ADR cập nhật. Modal L4 không được mặc định đủ cho LTX. |
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
| ASR tiếng Việt | Whisper/faster-whisper theo hướng dẫn owner | Modal; dashboard dev có function `transcribe-vietnamese-audio` trên CPU | Model/checkpoint chưa xác nhận từ dashboard; phải đo tiếng Việt, latency và xác nhận transcript bởi người lớn. |
| VLM + story/storyboard | Qwen3.5-VL theo hướng dẫn owner | Modal; profile GPU theo bộ nhớ và benchmark | Không dùng Qwen2.x cho luồng mới. Schema, safety, độ trễ, license và kết nối backend còn cần kiểm chứng. |
| Sinh guide/ảnh minh họa SVG | SVG catalog + deterministic engine; Qwen3.5-VL tạo draft vector có cấu trúc khi catalog thiếu và capability tương ứng được bật | Modal là hướng hosting inference; local/backend engine parse, validate, canonicalize và serialize | FLUX không thuộc target và không fallback. Topic-to-guide, grouping existing paths và static illustration là khả năng riêng cần POC; schema, safety, license, quality, latency/cost và dispatch còn gate. |
| Vietnamese TTS | Function tổng hợp lời kể tiếng Việt trong Modal dev app | Modal CPU trên dashboard quan sát được | Model/checkpoint, chất lượng giọng và đồng bộ timing chưa được xác nhận. |
| Segmentation ảnh | SAM 2.1 tùy chọn, sau bước xử lý ảnh xác định bằng OpenCV/Pillow | Modal là đích inference; backend hiện có adapter SAM 2.1 từ các slice cũ | Không bắt buộc V1; cần chuyển/kiểm chứng Modal, đo chất lượng mask và bảo toàn ảnh gốc/lineage. |
| Teacher SVG guide/visual draft | SVG catalog là nguồn mặc định; Qwen3.5-VL có thể tạo vector draft khi capability được bật | Modal là hướng hosting development; deterministic SVG engine render | Riêng với story-video; không nhận profile/ảnh trẻ và không trừ video quota. POC, educator/curator review, quality/safety/license, stability và cost vẫn là gate. |
| Structured output | Pydantic v2 + JSON Schema có version | API/worker Python | Bắt buộc cho VLM, story/storyboard, Character Bible, sketch deck và safety result |
| Reference/image preparation | Python + OpenCV + Pillow; SAM 2.1 tùy chọn | Modal worker khi bật segmentation | Tạo derived asset có hash/lineage; segmentation không bắt buộc V1; hiện chưa xác nhận Modal integration end-to-end. |
| Giọng kể tiếng Việt | Ứng viên VieNeu-TTS | Modal L4 | Cần xác minh giọng người lớn trung tính, đồng bộ phụ đề và license |
| Image-to-video | Pipeline self-host chính thức LTX-2.5 theo Q144 | Modal GPU L40S (48 GB) là target cần POC | Chưa kiểm chứng end-to-end; dashboard dev có worker WAN candidate riêng. WAN không phải quyết định thay thế LTX-2.5. Nếu owner muốn đổi model video phải có quyết định/ADR mới và cập nhật requirements, quality, cost, license, GPU, latency, safety và recovery gates. |
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
| FR-C-08 | M | Cho người lớn hủy run chưa hoàn tất hoặc xóa run ở COMPLETED, FAILED hoặc ABANDONED qua lifecycle. Lệnh hủy run chưa hoàn tất phải nhả khóa active ngay; thu hồi upload/playback, hủy job best-effort, xóa nội dung liên kết và báo tiến trình purge. Không hoàn quota request video đã nhận; giữ metadata quota tối thiểu và Teacher sample claim đã thành công. |
| FR-C-09 | S | Mỗi asset có metadata riêng và lineage nguồn/hash/derived bất biến; không lưu binary trong relational row hoặc JSON không giới hạn. |
| FR-C-10 | M | Cho chủ hồ sơ Parent hoặc Teacher/actor được tổ chức phân quyền yêu cầu xóa hồ sơ; thu hồi quyền profile/run ngay và hiển thị trạng thái đến khi purge nội dung liên kết. Chính sách xóa tài khoản và vai trò xóa hồ sơ Teacher phải chốt trước khi dùng dữ liệu thật. |
| FR-C-11 | M | `DRAFT` và mọi state cần người lớn đều là adult-wait khi không có AI job; tại +144 giờ tạo một inbox reminder, thử push best-effort và gửi email best-effort nếu owner hiện tại có địa chỉ đã xác minh; tại +168 giờ `VIDEO_READY` thành COMPLETED, state chờ khác thành ABANDONED. Nhả khóa owner và giữ nội dung đến khi người dùng xóa; lỗi gửi không chặn run closeout và run đóng không resume. `VIDEO_ADMISSION_PENDING` không phải adult-wait; từ chối admission trả run về `SCRIPT_REVIEW` và bắt đầu wait mới. Deadline generation là sáu giờ từ `accepted_at`, gồm queue và mọi stage (Q133, Q136). |
| FR-C-12 | M | Ảnh, audio và file giáo án upload-resume lưu session/receipt bền vững trong `core.upload_sessions` và `core.upload_parts`, không nhồi vào `core_asset_metadata`. Mỗi app chunk tối đa 4 MiB là object riêng qua PutObject; session gắn principal/scope/purpose, expected media/size/hash, idempotency và expiry. Chunk cùng số/hash idempotent; cùng số khác hash trả conflict. Backend xác minh part liên tục, byte tổng và SHA-256 từng part/toàn asset, lắp ráp bounded stream rồi ghi asset cuối bằng một PutObject; không gọi S3 Multipart Upload API. Chỉ asset hoàn chỉnh, media-validated và AV-clean mới dùng được. Rate limit tách control/status/chunk request, số session đồng thời và unique bytes/phút; retry chunk đã nhận không tính lại byte budget. Client không nhận credential/endpoint MinIO. |

### 7.2 Luồng Phụ huynh

| ID | Ưu tiên | Yêu cầu |
|---|---|---|
| FR-P-01 | M | Khôi phục luồng Parent Android trên nền hiện tại apps/mobile; dùng apps/ui-mobile làm nguồn tham khảo hành vi/giao diện. |
| FR-P-02 | M | Cho Parent tạo/chọn hồ sơ thuộc mình; yêu cầu một ảnh tranh làm input bắt buộc trước khi tạo StoryRun/phân tích ảnh (camera là hành động chính, thư viện ảnh là alternate). Topic và lesson preset trong Parent Gallery đều tùy chọn. Nếu Parent chọn lesson, gửi exact lesson/version pin để backend xác thực quyền truy cập và revision. |
| FR-P-03 | M | Nhận ý tưởng dạng chữ, giọng nói tối đa 2 phút/20 MB hoặc cả hai; dùng Whisper chuyển giọng nói thành chữ và yêu cầu người lớn sửa/xác nhận. |
| FR-P-04 | M | Phân tích ảnh tranh và cho người lớn sửa chủ thể; khi sửa, tạo revision diễn giải VLM mới. |
| FR-P-05 | M | Sau khi người lớn xác nhận subject, Parent phải chọn một hoạt động chính trước khi tạo story. Backend lọc candidates catalog-first từ lesson versions PUBLIC/SHARED Parent có quyền xem theo tuổi, profile summary/tags, topic và context tranh; lesson pin giới hạn vào exact version/hash. Qwen3.5 chọn ID/lý do, backend trả nội dung chuẩn. Nếu không candidate phù hợp, có thể tạo đúng 3 draft qua quality gate; yêu cầu bộ mới phải loại các lựa chọn đã hiển thị/bị từ chối để tránh trùng. Không gửi ảnh/audio thô/định danh trẻ. Activity được chọn là story context và diễn ra sau video. Sau video, lesson pin hiển thị toàn bộ activities của exact version; no-pin hiển thị activity chính đã chọn. Draft AI không phải catalog item/lesson draft. |
| FR-P-06 | M | Tạo context run tối thiểu từ revision hồ sơ đã chọn và yêu cầu người lớn xác nhận trước khi AI tạo story. |
| FR-P-07 | M | Cho phép tối đa ba lần AI viết lại story sau bản đầu theo gợi ý của phụ huynh; không có điều khiển sửa trực tiếp scene/script. |
| FR-P-08 | M | Yêu cầu người lớn xác nhận script/storyboard cuối trước khi tạo video. Hiển thị video ở VIDEO_READY ngay sau khi qua kiểm tra; giữ run active đến khi Parent bấm Hoàn tất/Tạo lại hoặc đủ 168 giờ adult-wait idle, khi run tự hoàn tất; không yêu cầu duyệt video cuối. |
| FR-P-09 | M | Cho người lớn đánh dấu video không phù hợp và quay lại xem script; giới hạn hai lần tạo lại chất lượng đầy đủ sau video đầu. Ẩn video bị từ chối khỏi playback ngay khi request tạo lại được chấp nhận; giữ nội bộ đến khi xóa run. |
| FR-P-10 | S | Hiển thị stage và lỗi dễ hiểu, có thể khôi phục; không đưa prompt/diagnostic model vào UI. |
| FR-P-11 | S | Trong drawing session, Parent có thể bật hoặc bỏ qua guide SVG progressive 4–8 bước cho topic chung. Catalog đã duyệt được ưu tiên; khi thiếu, có thể yêu cầu AI tạo draft nếu capability bật. Chỉ gửi topic/độ khó/guide contract; không gửi profile, tuổi cụ thể, giọng nói, ảnh/tranh hay định danh trẻ. Chỉ hiển thị output qua schema/vector/safety/media checks; draft riêng tư có provenance và expiry/cleanup. Không gắn profile/StoryRun, không tiêu video quota và mọi skip/no-source/disabled/unavailable/timeout/quality rejection đều không chặn capture bắt buộc. Chủ thể tranh chỉ được review sau capture. |
| FR-P-12 | M | Khi Parent chọn topic/lesson trước capture, phân tích ảnh phải kiểm tra topic compatibility. Nếu không phù hợp, hiển thị cảnh báo cho người lớn đổi topic hoặc chụp lại tối đa một lần. Sau lần chụp lại, subject do VLM nhận diện từ ảnh mới là chủ thể cho story; lesson đã pin vẫn là nguồn kiến thức/presentation và không tự đổi. |
| FR-P-13 | M | Topic/lesson tùy chọn; ảnh bắt buộc. Lesson presentation/guide chỉ hiện nếu được chọn hoặc bật. Hoạt động chính được chọn trước script; activity thay thế không được trùng lựa chọn đã trình bày/bị từ chối. Sau video, hiển thị activity đã chọn và toàn bộ activities của exact pinned lesson version nếu có. |


#### Nhánh Parent không có Lesson Preset — contract decision (UC-02/FR-P-05)

Parent không pin lesson vẫn phải chọn một activity chính trước khi story. Catalog-first suggestion lấy activity từ published/shared lesson versions mà Parent được phép xem; nếu đang pin lesson, ưu tiên activities của exact version. Người lớn chọn một kết quả. Nếu không có kết quả phù hợp, AI có thể tạo đúng 3 draft qua quality gate. Yêu cầu bộ khác phải loại lựa chọn đã hiển thị/bị từ chối. Selection bắt buộc; exact recovery khi không có kết quả hoặc suggestion lỗi vẫn OPEN-TECHNICAL. Sau video, no-pin trả activity đã pin vào run snapshot; không query catalog mới và không tạo list fallback.

| Moment | Query/response rule | Permission/filter/version requirements | Empty, error and revoke | Status |
|---|---|---|---|---|
| Chọn một activity chính trước story | Backend lọc candidates hiện render được từ activities trong lesson versions PUBLIC/SHARED mà Parent có quyền xem; lesson pin giới hạn vào exact version/hash. Qwen3.5 chọn request-scoped ID/order/reason và backend trả nội dung chuẩn; nếu không có candidate phù hợp, có thể tạo đúng 3 draft tạm qua quality gate để người lớn chọn. | Lọc theo tuổi và metadata có sẵn; dùng allowlist context tại §31.16/31.17, không raw image/audio hoặc định danh. Yêu cầu bộ khác loại các ID đã hiển thị/từ chối. | Chỉ một lựa chọn được chốt vào StoryRun. Candidate bị revoke/unpublish hoặc không còn quyền truy cập không được trả như nội dung hiện hành; exact error/recovery/API vẫn OPEN-TECHNICAL. | Chính sách Rev66 §31.17; contract còn OPEN-TECHNICAL. |
| Sau playback, không có lesson pin | Trả activity chính đã được người lớn chọn và pin vào run context; không query `learning_content` mới, không gợi ý thêm tự động. | Activity ref/revision thuộc snapshot run; không hydrate từ catalog hiện hành nếu làm đổi nội dung đã duyệt. | Nếu ref không còn đọc được, giữ snapshot theo retention/authorization rule; exact response/error vẫn OPEN-TECHNICAL. | Quy tắc Rev66 §31.17; route/snapshot contract còn OPEN-TECHNICAL. |

Khi có lesson pin, sau video trả toàn bộ activities từ exact lesson-version/hash sau current-access recheck, đánh dấu activity chính đã chọn; không dùng latest thay pin.

### 7.3 Luồng Giáo viên và tổ chức

| ID | Ưu tiên | Yêu cầu |
|---|---|---|
| FR-T-01 | M | Cung cấp luồng Teacher trên web hiện có apps/teacher-ui. |
| FR-T-02 | M | Cho School Manager được phân quyền của organization tạo lớp trong capacity, quản lý roster và phân công chính xác một Teacher phụ trách mỗi lớp. Cách lưu/resolver permission còn OPEN tại §31.10. |
| FR-T-03 | M | Cung cấp 10 slot lớp trong subscription cơ bản trả phí của mỗi tổ chức, cộng slot đã mua; ngăn tạo lớp đồng thời vượt capacity đang hiệu lực. |
| FR-T-04 | M | Cho Teacher tạo hồ sơ trẻ bằng form nhanh có cấu trúc; cho phép tên hiển thị trùng nhau và dùng ID nội bộ opaque. |
| FR-T-05 | M | Giới hạn mỗi hồ sơ Teacher ở tối đa một enrollment lớp hoạt động; khi chuyển lớp thì đóng và lưu enrollment trước đó. |
| FR-T-06 | M | Nhận giáo án PDF/PPTX/DOCX tối đa 25 MB và 100 trang/slide; từ chối file mã hóa/password; trả OCR_NOT_SUPPORTED với trang scan. |
| FR-T-07 | M | Giữ file giáo án gốc và provenance của text trích xuất; cho sửa thành revision text bất biến mới; yêu cầu Teacher xem và duyệt trước khi dùng. |
| FR-T-08 | M | Tạo occurrence và plan cho buổi dạy, pin optional typed `LessonVersionRefV1` với version/hash chính xác khi chọn reusable lesson; plan revision và Teacher StoryRun giữ cùng lineage ref/hash đã pin, không resolve `latest`. Một occurrence có thể giữ nhiều activity; Teacher sample ghim một activity và một child/run như baseline. Cách lưu vật lý chờ DDL được duyệt. |
| FR-T-09 | M | Hoạt động Teacher tự nhập chỉ tồn tại trong occurrence đó và cần Teacher phụ trách xác nhận bằng safety checklist. |
| FR-T-10 | M | Hệ thống chọn đồng xác suất một child từ tập eligibility/consent hợp lệ; Teacher xem và xác nhận child/context trước khi tạo run; không có nhánh Teacher tự chọn child tùy ý. Candidate stale được chọn lại tối đa một lần; tập rỗng dừng không fallback; trước confirmation không tạo/accept run/job/quota/claim. Ghim approved activity nếu có preset và snapshot context tối thiểu vào run. Exact eligibility predicate, consent evidence, concurrency and response contract remain OPEN at Q-01. |
| FR-T-11 | M | Cho Teacher chụp bằng camera trình duyệt hoặc tải ảnh chụp bằng điện thoại. |
| FR-T-12 | M | Cho Teacher đặt hướng story theo giáo án/plan lớp đã duyệt và yêu cầu tối đa ba lần AI viết lại; mỗi lần tạo video đều phải xác nhận script. |
| FR-T-13 | M | Thực thi tối đa một video mẫu phát được và đạt safety cho mỗi occurrence. Lỗi kỹ thuật hoặc safety block trước lần playback/claim đầu không chiếm slot. Sau claim đầu, không mở lại slot dù video bị từ chối/ẩn, các lần tạo lại thất bại/hết lượt, run bị xóa/hủy hoặc đổi Teacher. |
| FR-T-14 | M | Quyền run/media theo Teacher phụ trách hiện tại. Reassignment/offboarding là saga idempotent: BE1 fence/revoke quyền và token cũ ngay, lớp thành read-only; Story chuyển `active_owner_teacher_id`/lock trong transaction riêng; BE1 finalize chỉ sau Story receipt. Trong pending không Teacher nào xem content. Nếu Teacher mới có active run, Story trả conflict và saga phục hồi assignment/quyền cũ; nếu compensation mơ hồ, giữ pending/read-only để reconcile. `created_by_actor_ref` chỉ truy vết. Không hủy AI job hợp lệ chỉ vì đổi assignment. Kết quả chỉ được nhận nếu run/input/script/activity/occurrence hashes còn hợp lệ, cùng org/class, không cancel/delete và transfer receipt hiện hành chứng minh owner mới; assignment version cũ/creator không cấp quyền. |
| FR-T-15 | S | Hiển thị trạng thái và kết quả mẫu của từng occurrence; ở VIDEO_READY cho phép Teacher chiếu, Hoàn tất hoặc Tạo lại; sau 168 giờ adult-wait idle tự hoàn tất. Không có hành động chạy theo toàn roster/batch. |
| FR-T-16 | M | Chỉ Teacher phụ trách hiện tại mới có thao tác chiếu cho lớp. Ghi xác nhận occurrence có audit; cấp playback authorization ngắn hạn, không cấp capability dùng lại cho thành viên lớp. Đây không phải duyệt video cuối. |
| FR-T-17 | M | Cho phép School Manager của organization sở hữu lớp/run force-close conflicting Teacher run chỉ qua command emergency tường minh có reason bắt buộc và metadata audit. Đóng run thành ABANDONED, nhả active-owner lock, không xóa run/media hoặc cho School Manager xem nội dung; quota đã nhận và sample claim thành công vẫn còn. Force-close là bước tường minh trước khi retry reassignment, không phải hành vi tự động của ordinary reassignment. Cách gán/lưu permission, scope và resolver còn OPEN tại §31.10. |
| FR-T-18 | M | Teacher có thể mở guide SVG catalog/lesson để trình bày cách vẽ. Guide/AI draft chỉ được tạo khi Teacher yêu cầu; nếu không bật thì không dispatch AI. Guide bám chủ thể/kiến thức lesson, có 4–8 bước adaptive và không nhận roster/profile/tranh trẻ làm input. |
| FR-T-19 | M | Teacher lesson có presentation 16:9 trong ứng dụng, sửa được text từng slide, thêm/xóa/sắp xếp slide và đặt ảnh/video/SVG vào slide được chọn. Hỗ trợ ảnh Teacher upload, link HTTPS YouTube/Vimeo embed, SVG catalog và SVG draft AI. Teacher điều khiển trình chiếu; không yêu cầu xuất PPTX/PDF. Video story của trẻ vẫn theo flow occurrence sau khi pipeline hoàn tất. |
| FR-T-20 | M | Presentation/guide pin lesson/plan revision/hash. Sửa nguồn tạo revision draft; asset/guide phụ thuộc phải stale theo dependency. AI SVG/media draft không được publish trước Teacher review; School Manager duyệt phạm vi trường, Platform Admin duyệt public toàn nền tảng theo role. Sketch/vector AI dùng rate/cost cap riêng, không ghi `billing.video_quota_usage`. |
| FR-T-21 | M | Bảo toàn asset gốc/provenance; upload ảnh qua type/size/malware/safety checks. Video ngoài chỉ nhúng từ YouTube/Vimeo qua HTTPS allowlist; backend không truy xuất URL tùy ý. Slide order/media refs thuộc revision presentation; không sửa published revision trực tiếp. |
| FR-T-22 | S | Teacher có thể yêu cầu AI tạo minh họa SVG draft khi capability bật; backend kiểm schema, bounds, provenance, safety và license rồi deterministic SVG engine render. Teacher preview/accept/discard trước khi gắn hoặc publish. Không gửi raw lesson file hoặc roster/profile trẻ tới model. |

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
| FR-AI-14 | M | Tạo/retrieve/render guide SVG theo versioned structured contract từ catalog hoặc Teacher-selected source. Guide có 4–8 bước adaptive; validate coverage, path references, dependency/order, layout, media, age-safety, lineage và educator/curator approval trước khi hiển thị/AI dispatch. Không gửi roster/profile/tranh trẻ; không tự phát sinh activity ngoài approved lesson. Teacher presentation và guide revisions phải pin version/hash; nguồn đổi thì nội dung phụ thuộc stale. |
| FR-AI-15 | S | Parent guide dùng SVG catalog trước; nếu thiếu, có thể tạo draft AI theo topic/độ khó và capability flag. Guide progressive 4–8 bước; deterministic engine sanitize/validate/serialize. Không gửi profile/tuổi chính xác/photo/audio/artwork/identity; draft private có provenance/lifecycle, không gắn profile/StoryRun, không dùng video quota. Skip/no-source/disabled/unavailable/timeout/quality rejection không chặn capture bắt buộc. Exact job, asset and API persistence remain technical gates. |

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
| FR-B-10 | M | Duy trì quota video theo tháng cho Parent account và school organization; Teacher video dùng organization của occurrence, không có Teacher-account pool. Billing `video_quota_grants` và `video_quota_usage` là nguồn entitlement/tiêu thụ chuẩn. Use case quota-admission của Billing phân bổ idempotent mỗi request được nhận vào một grant. AI Policy chỉ sở hữu metering/reservation tài nguyên nền tảng. Request đã nhận tiêu thụ một unit kể cả lỗi provider/kỹ thuật/safety; không hoàn quota; retry scene không tiêu thụ. Không ghi danh tính trẻ hoặc media vào ledger. |
| FR-B-11 | M | Trước Billing admission, application phải reserve budget GPU tối đa cấu hình được cho request qua AI Policy port bằng idempotency key và lease/expiry. Nếu không đủ budget thì trả `AI_COST_LIMIT_REACHED` trước khi request được nhận, không tiêu quota. Sau budget reservation, Billing kiểm tra quota trong transaction riêng; `VIDEO_QUOTA_EXCEEDED` không dispatch, không tạo usage row và khiến application giải phóng reservation. Nếu tiến trình dừng hoặc phản hồi không rõ, reconciler tra cứu receipt bằng idempotency key, hết hạn reservation chưa gắn với accepted request và không dispatch hai lần. Chỉ dispatch sau khi cả budget reservation và quota admission được xác nhận. Hết quota vẫn cho playback/quản lý dữ liệu đã lưu. Tính quota còn lại trong Billing từ grant hợp lệ trừ usage ledger bất biến; không lưu balance mutable. Ưu tiên included tháng hiện hành rồi top-up FIFO. |
| FR-B-12 | S | Cung cấp quota summary xác thực theo scope backend suy ra từ actor, gồm included tháng hiện tại/thời điểm hết hạn, top-up FIFO, đã cấp/đã tiêu thụ/còn lại và ranh giới kỳ; không làm lộ account hoặc run/trẻ khác. |
| FR-B-13 | S | Nếu owner bật offer quota bổ sung và xác định actor/permission qua Q193, Billing hỗ trợ payment adapter được duyệt; chỉ phát entitlement sau event thanh toán xác minh/idempotent, số lượng/giá do server kiểm tra và invoice/grant bất biến. Top-up là giao dịch mua một lần, không tự gia hạn (Q120). Purchase availability, actor, scope và quyền vẫn OPEN tại §31.10(2),(6). |
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
| NFR-31 | Giới hạn lưu dữ liệu | M | Synthetic demo tuân theo Q66/Q129/Q133: run COMPLETED/FAILED/ABANDONED và media giữ đến khi người dùng chủ động xóa; không có auto-purge theo ngày. Đây là lựa chọn demo, không được áp dụng cho dữ liệu trẻ thật/production. Trước real-data gate phải chốt retention tối đa theo loại dữ liệu, backup expiry, DSR, xóa khỏi backup hoặc crypto-shredding và bằng chứng hoàn tất xóa. |
| NFR-32 | Upload chịu gián đoạn mạng | M | Tải ảnh tối đa 20 MiB, audio tối đa 20 MB/2 phút và lesson tối đa 25 MB phải hỗ trợ tiếp tục sau khi app/browser hoặc kết nối bị gián đoạn. Dùng application chunk tối đa 4 MiB, mỗi chunk là object PutObject độc lập; `core.upload_sessions`/`core.upload_parts` lưu session/receipt bền vững. Resume chỉ gửi phần thiếu; exact retry không cộng unique-byte budget. Backend kiểm tra thứ tự, kích thước, SHA-256 từng phần/toàn file, lắp ráp bounded stream rồi ghi asset hoàn chỉnh bằng một PutObject đã biết kích thước (demo file tối đa 25 MB, dưới ngưỡng single-PUT 128 MiB được nêu trong tài liệu MinIO Go SDK; cần POC trên đúng phiên bản client). Đây không phải S3 Multipart Upload API. |
| NFR-33 | Khả năng trình chiếu Teacher | M | Teacher Sketch Deck hiển thị ổn định trên viewport 16:9 từ 1280×720 trở lên, co giãn theo máy chiếu, giữ line-art tương phản cao trên nền trắng và dùng text ngắn. Control Back/Next/skip/select activity có semantic label/focus; nội dung không phụ thuộc riêng màu sắc; chữ/control đạt contrast WCAG 2.2 AA. Xác minh bằng render review trên viewport 16:9, keyboard-only và kiểm tra chiếu thử. |

### 8.1 Ưu tiên, verification và phân pha

Ưu tiên `M` (Must) và `S` (Should) thể hiện mức cần thiết trong pha đích, không phải trạng thái duyệt. Functional catalogue (§7) và NFR catalogue (§8) ghi mức ưu tiên cho từng ID. Ma trận §30.3 là nguồn truy vết theo ID cho nguồn/lý do, UC/phạm vi, entity owner, phương pháp xác minh, pha và trạng thái. “Verification” là phương pháp nghiệm thu dự kiến, không phải bằng chứng test đã chạy. Trạng thái requirement là `DRAFT` cho đến khi chủ sở hữu duyệt tài liệu; nguồn Q/BR không đồng nghĩa với nghiệm thu triển khai.

| Pha kỹ thuật đề xuất | Kết quả kiểm chứng | Requirement điển hình | Ranh giới |
|---|---|---|---|
| P0 — Nền tảng/contract | Modular monolith, auth/scope, owner schema, outbox/job, Docker, synthetic fixtures, security basics, quota admission, hard cost reservation và resumable upload contract | FR-C, FR-O, NFR-01–18, NFR-24–28, NFR-32 | Không bỏ quota/cost reservation khỏi video flow; upload adapter POC cần trước media integration; provider payments thật chưa cần cho fixture |
| P1 — Parent vertical slice | Parent profile → ảnh/ý tưởng → subject/activity/context review → story review → video Modal → playback/delete, trên dữ liệu tổng hợp | FR-P, FR-AI, subset FR-C/NFR, resumable media upload | Không dùng dữ liệu trẻ thật; quota fixture/config được cấp từ Billing |
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
        learning_content/ ai_jobs/ ai_policy/ (domain owners, proposed)
      application/
        commands/ queries/ services/ ports/ policies/
        learning_content/ ai_jobs/ ai_policy/ (owner use cases and ports, proposed)
      contracts/
        http/v1/ events/v1/ jobs/v1/ schemas/
      interfaces/
        http/routers/ dependencies/ workers/ schedules/
      infrastructure/
        persistence/ object_storage/ queue/ identity/
        learning_content/ ai_jobs/ ai_policy/ (adapters only, proposed)
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
| AI hosting | Modal là hướng hosting inference trong giai đoạn phát triển | Chỉ backend worker/adapter được gọi provider; vùng production, credentials, data transfer, retention và tích hợp end-to-end còn là gate. Code có adapter Lightning từ các slice trước; sự hiện diện đó không đổi target và không chứng minh Modal đã được nối vào API chính. |
| VLM + story/storyboard | Qwen3.5-VL là hướng phát triển owner chọn | Cần pin checkpoint/serving profile và kiểm tra schema, safety, quality, license, latency, cost; không suy rộng NO_GO của Qwen3-VL sang family này. |
| ASR | Whisper là hướng phát triển owner chọn | Cần pin implementation/checkpoint, đo tiếng Việt/latency và chốt retention; người lớn vẫn xác nhận transcript trước khi tạo story. |
| Line-sketch/hình ảnh giáo án | SVG catalog + deterministic vector engine là target; Qwen3.5-VL là hướng tạo bản nháp vector có cấu trúc khi catalog thiếu | Không dùng FLUX. Model không trả SVG/HTML tự do; backend kiểm schema/safety/license/age suitability rồi serialize/render. Từng capability, checkpoint, serving, quality, latency/cost và license cần POC/promotion gate riêng. |
| Image segmentation | SAM 2.1 tùy chọn | Chỉ bật sau benchmark mask/crop fallback bằng dữ liệu tổng hợp; không bắt buộc để tiếp tục luồng nếu segmentation không đạt. |
| Model video | Pipeline self-host chính thức LTX-2.5 theo Q144; Modal L40S là mục tiêu cần POC | Chưa có kiểm chứng end-to-end. WAN worker là ứng viên phát triển riêng; không thay LTX-2.5 nếu chưa có quyết định owner/ADR mới. |
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
| VideoQuotaAdmissionV1 / VideoQuotaSummaryV1 | Duyệt một full-video request và hiển thị quota hiện tại | Scope Parent account hoặc school organization (Teacher dựa trên occurrence) do server suy ra; một unit/request được chấp nhận; có grant ref và idempotency receipt; không chứa dữ liệu trẻ/media |
| ClassProjectionConfirmationV1 | Xác nhận đối tượng/mục đích chiếu video mẫu cho occurrence | Teacher phụ trách hiện tại, occurrence ref, generation ref đã qua safety, timestamp xác nhận và assignment revision; không cấp capability dùng lại cho thành viên lớp |
| AssetRefV1 | Media gốc/dẫn xuất hoặc guide tạm thời | Asset ID opaque, version/hash bất biến, media type, source link, access policy và expiry khi asset có lifecycle tạm |
| AiJobCommandV1 / AiJobStatusV1 | Stage AI bất đồng bộ cho Story/video, lesson extraction, Teacher Deck hoặc Parent guide | Chính xác một cặp target kind/ref: `STORY_RUN`, `VIDEO_GENERATION`, `VIDEO_GENERATION_SCENE`, `LESSON_SOURCE_DOCUMENT`, `LESSON_LIBRARY_VERSION`, `LESSON_VERSION_VISUAL_ASSET`, `LESSON_SKETCH_DECK_REVISION` hoặc `PARENT_SKETCH_GUIDE`; expected target revision/input hash, stage, attempt và safe result/error. StoryRun target resolve đúng một profile từ Story; video scene target resolve scene/generation/run qua Story port; cả hai Lesson target không có profile trẻ; Parent guide chỉ có generic topic/difficulty. `correlation_id` nối các job thuộc cùng generation/run nhưng không thay thế target. |
| StoryRunDetailV1 | Một response tổng hợp cho client | Current run/input/script/video pointers, safe stage, scene/job statuses, authorized asset/playback refs và quota summary qua owner ports. Không trả prompt, raw transcript, hidden story revision, foreign-scope existence hoặc provider error detail. |
| ScriptRevisionV1 | Story/script/storyboard | Revision/hash bất biến, 5–15 scene, mục tiêu dài 30–90 giây |
| SketchDeckV1 / SketchDeckStepV1 | Deck line-sketch theo occurrence plan | Occurrence ID, approved plan revision/hash, target age band, 16:9 template version, activity ref, stable instruction-group key, adaptive 4–8 ordered progressive drawing-step records per guide, bounded layout hint, concise child-facing prompt/explanation, asset ref/hash/lineage, model/schema/template version; không có profile/trẻ hoặc video quota ref |
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
| Parent drawing-guide resources (version/route TBD) | Đọc guide đã duyệt từ SVG catalog; yêu cầu guide draft theo topic khi capability bật; xem preview, accept/discard, đọc stage/render; lỗi catalog/AI được trả rõ và không chặn capture. |
| Teacher lesson presentation/slide/media resources (version/route TBD) | Đọc/sửa draft presentation; tạo/sửa/xóa/sắp xếp slide, text và media placement; upload ảnh hoặc tham chiếu YouTube/Vimeo/SVG; dùng revision/concurrency guard và giữ published version bất biến. |
| Teacher SVG stroke-guide resources (version/route TBD) | Chọn chính xác source asset/version; đọc/classify source; tạo manual hoặc AI draft guide, sửa metadata/order theo giới hạn, preview stage, review/accept; giữ source geometry bất biến và kiểm organization/lesson permission. |
| /v1/activities | Route đề xuất đọc catalog Parent đã published/approved; có expose cho Parent run không preset và response/filter contract còn OPEN tại §31.10; Teacher chọn activity theo quyền |
| /v1/story-runs | Tạo run một trẻ, gửi tranh/ý tưởng, review stage, yêu cầu viết lại, xác nhận script, hoàn tất/xóa |
| /v1/story-runs/{id} | Đọc StoryRunDetailV1 tổng hợp hiện trạng và timeline an toàn; backend compose từ Story, AI Jobs, Core Asset, Lesson/Billing ports tùy run, không có cross-schema SQL hoặc nhiều endpoint bắt frontend phải ghép |
| /v1/jobs/{job_id} | Poll trạng thái AI job/stage có version và lỗi an toàn |
| /v1/story-runs/{id}/playback-token | Cấp quyền playback ngắn hạn sau khi phân quyền |
| /v1/lesson-occurrences/{id}/projection-confirmation | Xác nhận riêng việc chiếu video mẫu cho occurrence |
| `/v1/video-quota` và `/v1/video-quota/purchases` (TO-BE; purchase route gated by Q193) | Đọc quota tổng hợp theo scope; chỉ cho phép purchase khi owner đã bật offer và xác định actor/permission |
| /v1/organizations/{org}/subscription | Đọc/cập nhật gói, capacity, thanh toán/gia hạn và yêu cầu hạ gói |
| /v1/payments/{provider}/callback | Xác minh callback MoMo/VNPAY và loại event trùng |
| /v1/notifications | Đọc inbox trong app, cursor pagination và xác nhận đã đọc |
| /v1/notifications/push-endpoints | Đăng ký endpoint Web Push hoặc Android provider adapter sau xác thực actor/device proof; revoke endpoint của actor hiện tại |
| /health/live, /health/ready, /metrics | Probe/metric vận hành, được bảo vệ phù hợp |

Dùng pagination cho roster/history; xác minh request size/content type; yêu cầu idempotency key với command đổi state hoặc liên quan payment. Không trả storage URL, provider prompt hoặc traceback nội bộ.

Các resource mới ở trên là yêu cầu đích, không phải route đã freeze. Exact API version, path, request/response schema, error enum, idempotency/concurrency contract và persistence owner phải được đối chiếu trong M0 với OpenAPI hiện hành và DTR; không coi API V2 proposal trong plan là API đã triển khai.

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
| Hoạt động Parent đã phát hành | Learning Content | Story/lesson giữ version đã chọn cùng activity snapshot/hash bất biến |
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
| SketchTeachingDeck | Revision deck/step trình chiếu theo occurrence | Pin một plan revision/hash; deck READY chỉ khi bao quát mọi activity và mỗi hướng dẫn có adaptive 4–8 bước; plan đổi thì STALE; không mang hồ sơ trẻ; compute riêng, không dùng video quota |
| StoryRun | Một người lớn, một trẻ; lesson version optional; Parent chọn và pin một activity chính trước story; Teacher run ghim activity đã duyệt | Một run active/người lớn; lesson ref typed/versioned nếu có dùng; activity chính là story context. Sau video, no-pin trả activity run-pinned; lesson pin trả toàn bộ hoạt động exact version và đánh dấu activity chính. `last_meaningful_activity_at` điều khiển idle deadline; VIDEO_READY idle→COMPLETED, các adult-wait state idle→ABANDONED; cả hai nhả khóa, giữ nội dung; cancel chuyển DELETE_PENDING; XOR profile kind; revision bất biến; giới hạn rewrite/video |
| VideoQuotaGrant | Grant quota tháng/mua thêm theo owner scope | Grant bất biến; quota included tháng hiện hành hết hạn cuối tháng; quota mua thêm không hết hạn và FIFO; admission loại bỏ grant expired |
| VideoQuotaUsage | Một immutable usage unit theo grant trong Billing | Idempotent; mỗi accepted full-video request một unit; không refund; không phụ thuộc retry scene; không có balance mutable |
| AiJob | Một target kind/ref được phân loại (`STORY_RUN`, `VIDEO_GENERATION`, `VIDEO_GENERATION_SCENE`, `LESSON_SOURCE_DOCUMENT`, `LESSON_LIBRARY_VERSION`, `LESSON_VERSION_VISUAL_ASSET`, `LESSON_SKETCH_DECK_REVISION` hoặc `PARENT_SKETCH_GUIDE`) và một stage AI | Dispatch idempotent, attempt giới hạn, expected hash/version, completion cuối hoặc stale; hồ sơ Story chỉ resolve qua StoryRun canonical; lesson-sketch/Parent guide không có child subject |
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
2. Story run có một activity và một scalar lesson-occurrence ref nếu là Teacher.
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

OwnerScopeRefV1 hỗ trợ ORGANIZATION, PARENT_ACCOUNT và GLOBAL. GLOBAL chỉ dành cho catalog/policy nền tảng; không làm owner của profile trẻ, run, quota video hoặc media asset. Backend suy ra adult actor để xác thực, không tin giá trị client gửi. Profile Parent và quota Parent dùng scope tài khoản Parent; profile Teacher thuộc organization; video Teacher resolve quota theo organization của occurrence, không có Teacher-account quota riêng. Không biểu diễn Parent bằng organization giả. ID profile Parent/Teacher opaque và không liên quan nhau. Mỗi model payload được dựng từ đúng một hồ sơ có quyền truy cập và snapshot đã duyệt.

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
| Run, tranh/audio, transcript, story revisions, scenes, video của run COMPLETED, FAILED hoặc ABANDONED | Đến khi người dùng chủ động xóa; Q66/Q129/Q133 không đặt auto-purge theo ngày | Xóa qua lifecycle; backup theo chính sách backup demo được duyệt, hiện không có chính sách backup real data | Synthetic demo only; production gate bắt buộc retention max |
| Giáo án gốc và extraction revisions | Đến khi Teacher/admin xóa lesson theo lifecycle | Purge original + derived text/asset, giữ audit tối thiểu | Synthetic lesson only; production schedule TBD |
| Modal scratch/input-output working copy | Xóa sau completion/failure/cancel; orphan scratch được dọn/cảnh báo sau 24 giờ | Job-scoped prefix, checksum và deletion receipt | Không chứa real child data trong demo |
| Billing invoice/payment event và quota grant/usage | Theo retention tài chính/metering sẽ được chốt với legal/accounting; quota usage không chứa nội dung trẻ | Nội dung run xóa độc lập; append-only billing/audit metadata không bị xóa cùng run | Thời hạn production TBD |
| Logs/traces/metrics | Cấu hình retention hữu hạn; chỉ dữ liệu đã redact/opaque IDs | Xóa theo retention vận hành; không chứa payload/media/PII | Thời hạn cụ thể cần điền trong deploy profile trước pilot |
| Backups | Manual local backups chỉ chứa synthetic data | Production phải có expiry, access controls, deletion propagation hoặc cryptographic-erasure design đã review | Production gate; chưa có backup SLA |

Không thể diễn giải “đến khi user xóa” thành retention policy phù hợp cho trẻ thật. Bất kỳ production/pilot có dữ liệu thật nào đều bị khóa cho đến khi OI-05–OI-08 được duyệt, có thời hạn tối đa theo từng loại record, phương án xóa trong backup và owner chịu trách nhiệm.

<a id="srs-12"></a>
## 12. Kiểm kê nguồn, migration và chuyển đổi

### 12.1 Kiểm kê bảng nguồn

Trước Rev31, repository khai báo 86 production source mappings gồm core (8), BE1 (22), AI Jobs bền vững (7), AI Policy (25), Learning Content (6), Knowledge Video (2), Video Review (6), Video Failure (3), Activity Execution (5) và Preset Automation (2). Rev31 thêm ba Lesson support mappings, nên current source crosswalk có 89 mappings; đây không phải kiểm kê database đang chạy. Năm fixture mappings dùng cho test không nằm trong tổng.

### 12.2 Disposition đích

- Giữ/chuẩn hóa 38 mapping hiện có làm owner cho tổ chức, roster, AI Jobs, AI policy/version/activation/resource budget, catalog hoạt động, provenance/audit Core và hạ tầng transaction.
- Thêm 54 bảng target hiện hành: 40 bảng nền tảng ban đầu, 11 logical platform tables và ba bảng hỗ trợ Lesson Rev31; loại bốn helper/snapshot table trùng với aggregate owner.
- Giữ 48 mapping legacy chỉ đọc tại chỗ: 35 mapping lớp học/canvas/video/activity/preset cũ cùng 12 `ai_policy.copy_*` registry và `ai_policy.resource_receipt`. Registry provider-copy đầy đủ bị deferred tới production gate dùng real-child-data. Lệnh resource mới dùng `resource_event` làm event + idempotency/result ledger, không ghi hai bảng.
- Crosswalk hiện hành Rev31: 38 retained/refactored + 54 new = 92 active; +48 legacy/read-only = 140 projected physical. Current source crosswalk là 89 mappings: 86 pre-Rev31 + 3 Lesson support, gồm 38 retained/refactored + 48 legacy + 3 Lesson support. Baseline thiết kế v2.3 lịch sử là 89 active + 48 legacy = 137. Năm fixtures không tính; các mapping/target này chưa phải kiểm kê DB đang chạy.
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
| AC-08 | Parent/Teacher đã xác nhận transcript, subject và context/lesson direction phù hợp vai trò; Teacher có activity đã duyệt | Adult tiếp tục pipeline | Parent chọn và pin một activity chính trước story; activity đó là story context và diễn ra sau video. Teacher pin activity đã duyệt trước video; script revision cuối cần adult confirmation trước admission | BR-14/15/55; FR-P-05/FR-PL-16; Rev66 |
| AC-09 | Crosswalk nguồn hiện hành sau Rev31 có 89 production mappings; có 5 test fixtures | Đối chiếu register với target | Phân biệt 89 nguồn hiện hành = 38 retained/refactored +48 legacy +3 Lesson support với baseline thiết kế v2.3 lịch sử 89 active/137 physical. Target hiện hành là 38 retained/refactored +54 new =92 active; +48 legacy =140 physical dự kiến; fixtures không tính và không tuyên bố live DB count | §1.1; §12; DATA_TABLE_REGISTER §§1/11/14.4 |
| AC-10 | Module sở hữu profile, lesson, story, billing, notification hoặc asset | Kiểm tra write path | Mỗi fact có một owner; projection/reference/event được chỉ rõ; register có dictionary và requirement-based retention | §9.7; DATA_TABLE_REGISTER |
| AC-11 | Domain/use case/adapter được tổ chức | Kiểm tra import/dependency direction | Domain không phụ thuộc framework/provider/storage/queue/UI; giao tiếp module qua port/contract versioned | NFR-01/14 |
| AC-12 | Docker local synthetic stack chạy | Khởi động/quan sát/backup/restore | Readiness, rate-limit, error envelope, redacted monitoring, backup/restore manual có hướng dẫn | NFR-07/08/11/12/27; §25–27 |
| AC-13 | Demo tạo profile/media/run | Seed hoặc upload fixture | Chỉ dùng dữ liệu tổng hợp; real-child data bị chặn cho đến khi privacy/retention/provider gates có evidence | BR-27; NFR-03/18/31 |
| AC-14 | Tổ chức mua/nâng/hạ capacity hoặc gia hạn | Callback MoMo/VNPAY được nhận | Payment/capacity/grace/downgrade/proration/notice nhất quán; redirect không được coi là thanh toán | BR-28–33 |
| AC-15 | Hai tài liệu Markdown đang chờ owner review | Có yêu cầu diagram/PDF | Không tạo artifact cuối trước khi owner duyệt cả SRS và data register | Yêu cầu sequencing của owner |
| AC-16 | Các use case UC-01…UC-17 được review | Soát đặc tả | Mỗi UC có actor, prerequisite, trigger, main/alternate flow, postcondition và data/requirement refs | §19 |
| AC-17 | Parent-account hoặc school-organization quota scope có grant/usage; Teacher dùng organization của occurrence | Xem quota, generate hoặc hết quota; kiểm tra purchase path chỉ khi policy Q193 được owner bật | Billing ledger idempotent; scope tách; included hiện tại trước top-up FIFO; included hết tháng, top-up carry-forward; playback cũ còn mở; không suy quyền mua từ scope | BR-38; FR-B-10–13; Q193 |
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
| AC-32 | Upload file nằm trong limit demo và mạng bị gián đoạn | App resume, server finalize | 4 MiB application chunks là object PUT riêng; tables session/parts lưu receipts; verify contiguous part numbers, size/SHA-256, scan/format; final asset ghi bằng low-level single PutObject; idempotent duplicate không double-count byte. AC này xác minh upload, không quyết định số bảng target; xem §1.1/§12 để biết phép đếm dữ liệu hiện hành | FR-C-12; NFR-09/12/32; AT-13 |
| AC-33 | Parent/Teacher đang ở session vẽ; Parent có thể chọn topic/lesson và bật guide | Người lớn chọn guide hoặc bỏ qua, sau đó trẻ vẽ và Parent chụp ảnh | Guide Parent/Teacher dùng adaptive 4–8 bước tăng dần từ nét cơ bản thành hình nhận biết; guide tùy chọn và lỗi/skip không chặn capture. Parent không chọn subject ảnh trước capture; VLM đề xuất sau capture để người lớn xác nhận/sửa | BR-42/43/46/54; FR-P-02/04/11; FR-T-18; UC-02/17; AC-44/45/53 |
| AC-34 | Teacher duyệt plan revision có nhiều hoạt động | Yêu cầu tạo Teacher Sketch Deck | Một deck revision gắn đúng plan hash, bao quát từng hoạt động và mỗi guide có adaptive 4–8 bước progressive đến hình nhận biết, layout hint và prompt trẻ em; không chứa hồ sơ/tranh của trẻ | BR-43; FR-T-18/20; FR-AI-14; UC-17 |
| AC-35 | Deck/presentation READY trên lesson/plan revision hiện hành | Teacher xem trước, chỉnh sửa slide/media, trình chiếu hoặc bỏ qua guide | Teacher có thể sửa text, thêm/xóa/sắp xếp slide, đặt ảnh upload/SVG/YouTube-Vimeo embed đúng slide và preview; guide có Back/Next/select/skip/regenerate; sửa tạo draft revision, source change làm dependent asset STALE; không có vẽ tự do/PPTX; AI SVG cap riêng, không dùng video quota | BR-43/44/53; FR-T-19/20; FR-AI-14/22; NFR-12/25/33; UC-17; Rev66 |
| AC-36 | Một run có ảnh của đúng một trẻ, ý tưởng đã duyệt và hoạt động hợp lệ | Chạy story/video pipeline đến playback | VLM tạo visual anchors → LLM tạo story có cấu trúc → storyboard 5–15 scene → người lớn xác nhận script → Character Bible/ảnh tham chiếu → LTX-2.5 trên Modal L40S theo scene → kiểm tra consistency → FFmpeg ghép scene → TTS tiếng Việt/phụ đề, không nhạc → safety tự động → playback riêng; output stale/không an toàn/không hợp lệ không được phát | BR-45; FR-AI-01–13; UC-02/05/16 |
| AC-37 | Video output hoàn tất kỹ thuật và safety | Hệ thống phát hoặc người lớn yêu cầu tạo lại | Video playable ngay, không chờ duyệt cuối; unsuitable output bị ẩn khi replacement được accepted, quay lại script review; tối đa 1 initial + 2 video regens, mỗi scene 1 + 2 retries; accepted request tiêu quota kể cả lỗi, không có public gallery/download | BR-10/11/16/17/24/25/45; FR-AI-06/07/09/13; AT-17 |
| AC-38 | Generation G pin story revision R1; scene S thuộc R2 | Writer tạo generation-scene link giữa G và S | Composite FK từ generation+revision và scene+revision từ chối record; `story_revision_id` lặp là immutable constraint key; không cần application-only check hoặc bảng link mới | §11.1 #21; DATA_TABLE_REGISTER §5.6–§7 |
| AC-39 | Có job ASR, VLM, scene LTX, composition hoặc Sketch step | Hệ thống dispatch và nhận kết quả lặp/stale | Mỗi job có đúng một target kind/ref/revision; scene job target đúng generation_scene_id, correlation groups siblings, Story kiểm reciprocal source_job_ref; `ai_jobs.attempt` là retry ledger duy nhất | FR-AI-01/06/13/14; §22; DATA_TABLE_REGISTER §4.1/§6 |
| AC-40 | StoryRun có current input/script/generation pointers và một aggregate revision | Đồng thời command/job hoàn tất cập nhật state/pointer | Story transaction kiểm expected version, ownership chain và hashes; `video_generations.state` canonical, `runs.state` projection đồng thời; stale command bị từ chối và `VIDEO_READY` không thể đứng riêng khi generation/asset/safety chưa READY | §6.1.1; §11.1 #22–23; DATA_TABLE_REGISTER §6.3 |
| AC-41 | Client được phép đọc một StoryRun; một số resource có thể thuộc owner/module khác | Client gọi `GET /v1/story-runs/{id}` | Một StoryRunDetailV1 tổng hợp status, timeline, scene, job-safe error, permitted assets và quota qua owner ports; không cross-schema SQL, không fan-out phía frontend, không rò prompt/transcript/profile support/foreign-scope existence, không có read-model table | §9.5–§9.7; §22.4; NFR-05/10 |
| AC-42 | So sánh data source inventory với target register | Rà soát AI Policy và mọi source table disposition | Crosswalk hiện hành 89 source mappings =38 retained/refactored +48 legacy +3 Lesson support; target =38 retained/refactored +54 new =92 active; +48 legacy =140 projected physical; 5 fixtures bị loại. 12 copy registry và `resource_receipt` read-only; 12 AI Policy active; legacy rows/IDs không bị drop/copy. Baseline 89 active/137 physical là lịch sử v2.3, không phải target Rev31 | §1.1; §12; DATA_TABLE_REGISTER §§1–4/9/11/14.4 |
| AC-43 | Resource command reserve/consume/release được gửi lặp với cùng key và fingerprint | AI Policy xử lý command và phát resource event | Một event ledger row là receipt/idempotency source mới với response snapshot/delivery state; replay trả cùng outcome; uniqueness phân biệt event kind nếu cần; source `resource_receipt` giữ read-only, không mất lịch sử | §11.1 #14; §12.3; DATA_TABLE_REGISTER §4.1/§6 |
| AC-44 | Parent đang ở drawing session khi trẻ vẽ | Người lớn bật line-sketch guide hoặc bỏ qua | Khi bật, request trả guide SVG progressive 4–8 bước từ catalog đã duyệt hoặc draft qua capability được phép; khi tắt/skip không tạo job. Chỉ topic/độ khó/guide contract được gửi model; không child/profile/photo/audio/artwork refs. Output private, temporary, có provenance/expiry; không gắn profile/StoryRun, không dùng video quota. Mọi source/worker/timeout/quality failure đều không chặn capture; sau vẽ Parent chụp rồi VLM subject review | BR-42/46/54; FR-P-02/04/11; FR-AI-15; Q146/Q167/Rev66 |
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
| AT-15 | Teacher duyệt plan có nhiều hoạt động | Tạo Sketch Deck | Deck bao quát mọi activity; mỗi instruction group có adaptive 4–8 bước progressive, age/layout hint; job không có child/profile/tranh ref; deck ghim approved plan hash | BR-43; FR-T-18; FR-AI-14; AC-34 |
| AT-16 | Deck READY; Teacher yêu cầu tạo lại một sketch hoặc plan đổi | Hoàn tất tạo lại và yêu cầu trình chiếu | Tạo lại sinh deck revision bất biến, giữ asset các bước không đổi; plan hash đổi làm deck stale; bucket/cost cap riêng không tạo video quota usage; deck stale bị chặn | BR-43/44; FR-T-20; AC-35 |
| AT-17 | Một run có đúng một trẻ, script đã duyệt và bắt đầu request video | Thực thi toàn pipeline với cả nhánh consistency/safety thất bại và thành công | Mỗi scene có một lần đầu và tối đa hai retry tự động; LTX tạo scene → kiểm tra consistency → FFmpeg ghép → TTS/phụ đề tiếng Việt, không nhạc → safety; output không đạt không được phát, output đạt phát riêng ngay mà không chờ duyệt video cuối; quota và giới hạn request áp dụng cho mỗi request đã được nhận | BR-45; FR-AI-01/06/07/09/13; AC-36/37 |
| AT-18 | Parent sắp cho trẻ vẽ và chưa có ý tưởng | Người lớn chọn topic/độ khó rồi yêu cầu guide hoặc bỏ qua | Guide trả 4–8 progressive SVG steps; catalog-first, AI draft chỉ khi thiếu và capability bật. Chỉ topic/độ khó được gửi; không profile/child/artwork ref. Skip/source/worker/timeout/quality failure không chặn capture; Parent vẫn chụp ảnh rồi VLM subject review | BR-42/46; FR-P-11/FR-AI-15; AC-44; Rev66 |
| AT-19 | Parent guide job đang chạy hoặc vừa hoàn tất | Timeout, limit refusal, unsafe/invalid output, người lớn skip/đóng guide hoặc TTL hết hạn | Capture flow vẫn dùng được; output invalid/unsafe không hiển thị; accepted guide asset bị xóa khi session kết thúc/TTL đến; lineage/expiry receipt không chứa nội dung trẻ; resource event ghi riêng sketch usage, không có video quota usage | BR-36/44/46; FR-AI-12/15; NFR-23/25; AC-45 |

<a id="srs-14"></a>
## 14. Quyết định và cổng triển khai

Q01–Q146 đã được chủ sở hữu trả lời và đối chiếu. Q145 là hình thức text-only tạm thời và được Q146 thay thế cho Parent pre-drawing guide.

### 14.0 Làm rõ đã được trả lời

| ID | Câu hỏi | Khuyến nghị hiện tại | Trạng thái |
|---|---|---|---|
| Q146 | Có nên cho Parent dùng line-sketch gợi ý do AI tạo, ví dụ guide vẽ con bướm 3–5 bước, như một lựa chọn riêng trước khi trẻ tự vẽ? | Historical answer: the optional Parent guide used 3–5 steps at that time. Rev66 §31.17 supersedes its step count with adaptive 4–8 progressive SVG steps and replaces FLUX image generation with SVG catalog + deterministic engine. Generic input/privacy, separate compute and nonblocking mandatory capture remain. | ANSWERED — owner clarification, 2026-10-28; đưa vào SRS v2.2-draft, chưa phải sign-off toàn SRS |

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
| OI-11 | Production PostgreSQL schema/row/index inventory and source-to-target migration rehearsal/restore | Data owner + Backend | Before migration | Rev31 crosswalk 92/140 and v2.3 design 89/137 are source-derived; local DB snapshot in §32 is not production and does not prove target migration | Local development DB was read-only inspected in Rev43; production inventory/rehearsal remains open |
| OI-12 | Google Play Families/target-audience, child safety, privacy listing and app review requirements | Product + Mobile + Legal | Trước Play publication | Có thể cần đổi onboarding/permissions/store listing | Chưa review theo app listing thực tế |
| OI-13 | Teacher invitation/provisioning, account recovery, organization bootstrap and role support runbook | Identity + Product + Support | Trước external pilot | Teacher/admin không thể onboard/khôi phục có hỗ trợ | Requirement exists; detailed UX/ops not approved |
| OI-14 | Quy trình gửi report hỗ trợ riêng khi video bị xem là không phù hợp; phân biệt với in-run reject/regenerate | Product + Privacy + Safety | Trước support operations | Không có kênh operator nhận media; mặc định operator không được xem nội dung | Ngoài luồng V1; quyết định và quyền truy cập chưa chốt |
| OI-15 | Tập AI evaluation có tranh trẻ thật với consent/authorization, access, purpose, transfer và retention được duyệt | AI + Privacy/Legal | Trước claims về chất lượng thực tế | Synthetic benchmark không đại diện chất lượng với tranh thật | Không thuộc demo; chưa tạo |
| OI-16 | Giá trị included quota của Parent account/school organization, giới hạn run/tháng và storage capacity | Product + Billing + AI + Operations | Sau benchmark; trước commercial launch | Không thể phát hành quota price/allowance hoặc forecast storage | Cấu hình để mở; chưa chốt số |
| OI-17 | Wireframe/interaction sign-off cho form profile, lesson extraction, Teacher Sketch Deck, script approval, quota/top-up, projection, delete/cancel và error/loading/accessibility states | Product + Design + Accessibility reviewer | Trước implementation UI | Màn hình kỹ thuật có thể không phù hợp thao tác nhanh của Parent/Teacher hoặc bỏ sót state | Chưa thiết kế wireframe; flow text tại §5/§19/§21 là baseline |
| OI-18 | POC adapter resumable upload trên MinIO/local storage: ghi từng application chunk thành object riêng, receipt/hash/expiry trong `core.upload_sessions` và `core.upload_parts`, replay idempotent, assemble bounded, final single PutObject, abort/TTL cleanup và AV boundary. Không dùng S3 Multipart Upload API; xác minh hành vi SDK MinIO đã pin. | Backend + Mobile + Infra | Trước Parent/Teacher media upload integration | Nếu SDK/storage semantics hoặc POC không đáp ứng checksum, resume và cleanup thì chưa bật media upload | Thiết kế đích đã chốt; POC còn mở |
| OI-19 | Synthetic POC cho SVG catalog/engine và structured-vector draft: coverage activity, 4–8 progressive steps, recognizability, age fit, safety, hash/lineage, license, latency, render performance và compute cost | AI + Teacher/Parent Product/Design | Trước bật AI SVG guide/visual | Guide/illustration khó hiểu, thiếu bước, unsafe hoặc chậm có thể ảnh hưởng dạy học; không gửi dữ liệu trẻ để bù chất lượng | FLUX không còn target; SVG source/catalog, Qwen draft policy, license, quality floor, caps và benchmark protocol còn OPEN |
| OI-20 | Phân loại vòng đời của từng route BE1/classroom/demo đang được mount hiện nay so với single-child Parent/Teacher target: giữ làm compatibility surface, thay thế bằng versioned target contract hay deprecate có kế hoạch | Product + Architecture + Backend | Trước API contract freeze/external pilot | Route presence có thể bị hiểu nhầm là sản phẩm được nghiệm thu hoặc đưa legacy collaboration behavior vào UI/flow mới; cần map từng operation từ API Catalog Rev37 | Mở; SRS target vẫn cấm classroom collaboration/multi-child story run; chưa có deprecation/migration allocation |

Các mục §29.2 là điều kiện triển khai tương ứng với OI-05–OI-16; bảng này là nguồn tổng hợp duy nhất cho owner, milestone, impact và trạng thái. OI-18 là POC kỹ thuật cho upload session/part tables và object-PUT chunk contract; OI-19 là cổng chất lượng/chi phí cho Teacher Sketch. Các chi tiết model/provider/payment payload sẽ được hoàn thiện theo tài liệu chính thức/sandbox trong ADR/implementation contract; không mô phỏng chữ ký hoặc payload của provider trong SRS.

<a id="srs-15"></a>
## 15. Nguồn và mức độ tin cậy

### Nguồn trong repository đã xem xét

- Quy tắc vận hành repository trong AGENTS.md và docs/governance.
- docs/architecture/OVERVIEW.md, PYTHON_BACKEND_ARCHITECTURE.md, DEPENDENCY_RULES.md, CONTRACTS_AND_INTEGRATION.md.
- ADR-0001, ADR-0017, ADR-0018, ADR-0019, ADR-0020, ADR-0021 và ADR-0022 đề xuất.
- Context, decisions, source register, approval, plan FEAT-063; khai báo bảng SQLAlchemy/Core hiện tại; danh sách Alembic revision, manifest và compose.yaml.
- Rev45 source review: `backend/src/sketch2life/main.py`, `interfaces/http/app.py`, `interfaces/http/router_composition.py`, `interfaces/http/routers/images.py`, `interfaces/http/middleware/bounded_image_upload.py`, `apps/mobile/README.md` và package manifests, `apps/ui-mobile/BACKEND_INTEGRATION.md`, Teacher UI package manifest, `backend/Dockerfile` và `compose.yaml`. Đây là source evidence, không thay kết quả runtime/test ở Rev43.
- API contract/catalog Rev31–Rev37 và EV-063-33/EV-063-34 được dùng để phân biệt khai báo route, route mounted, OpenAPI snapshot và chức năng đã được kiểm chứng.
- Các architecture guide trong repository là tài liệu ranh giới/implementation bổ trợ, không thay SRS/ADR cho product direction. Rev45 thấy provider wording Lightning/Runpod trong một số guide cũ; đối chiếu hiện tại phải theo canonical SRS và ADR có thẩm quyền, đồng thời xem adapter Lightning còn trong source là implementation history/demo chứ không tự hiểu là Modal/production decision.
- Bản nháp luồng/kiến trúc FEAT-062 trước đó; giả định PixiJS motion trong tài liệu cũ đã bị thay thế.
- Phiếu quyết định runtime video FEAT-050 và bằng chứng multimodal FEAT-003. NO_GO chỉ áp dụng cho profile Qwen3-VL đã được đánh giá trước đó; không suy rộng sang Qwen3.5-VL. Qwen3.5-VL là hướng phát triển do owner chọn nhưng cần POC riêng.

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
- [Model card Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B) — tham chiếu cho hướng Qwen3.5-VL development; checkpoint/runtime chính xác còn phải pin và kiểm chứng. [VieNeu-TTS](https://huggingface.co/pnnbao-ump/VieNeu-TTS) remains a historical candidate reference, not a selected TTS checkpoint.
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
| Q08–Q20: activity, lesson import, voice, review, GPU và identity | Parent chỉ dùng catalog hoạt động đã duyệt; Teacher activity riêng cần checklist; một plan/occurrence; giới hạn file/no OCR; giới hạn voice/review; sửa chủ thể; giới hạn output/retry; L40S cho LTX; Firebase Auth | §4–7, §9.3, §10 | §4–7 |
| Q21–Q30: profile context, dữ liệu nhạy cảm và revision | Tuổi theo tháng + nhóm tuổi; không gửi tên trẻ AI; nhu cầu hỗ trợ do người lớn nhập, không chẩn đoán; giới hạn truy cập; tách lịch sử app/trải nghiệm ngoài/achievement; revision bất biến và snapshot được duyệt | BR-18–21; FR-C-05–07; §6, §11 | §5.3–5.6 |
| Q31–Q40: UX Parent, activity, story/video | Parent chỉ dùng catalog; hai vai trò có tối đa ba rewrite; không sửa scene trực tiếp; hệ thống quyết định độ dài; revision cũ ẩn; xóa ở cấp run; stage dễ hiểu | BR-08, 13–16, 24–26; FR-P | §5, §5.6, §8 |
| Q41–Q70: Teacher/organization, tài liệu, voice, video và data lifecycle | Teacher có thể phụ trách nhiều lớp; admin xem roster nhưng không mặc định xem media; một enrollment active; một plan/occurrence; lesson revision; giữ audio gốc/transcript thô+đã sửa; subtitle/không nhạc; một script gate/không duyệt video; playback ngắn hạn; giữ đến khi user xóa; audit metadata; backup thủ công; bảng legacy chỉ đọc; snapshot run tối thiểu | §3–12; BR-05–06, 22–26; FR-T/FR-AI/FR-O | §3–10 |
| Q71–Q86: video mẫu, nhập profile, activity và xóa | Một trẻ/một activity được chọn; tối đa một video mẫu phát được/qua safety mỗi occurrence; Teacher nhập profile nhanh; một Teacher phụ trách/lớp; duyệt plan trước run; Parent dùng catalog; xóa run và media liên kết; lỗi trước playback không chiếm slot mẫu | BR-07–17, 26; FR-T; §6.1.1 | §5.4–5.6, §7–9 |
| Q87–Q101: capacity/subscription | 10 slot bao gồm; đơn giá/slot mua thêm tháng/năm; MoMo/VNPAY; grace 7 ngày; notification; chọn lớp khi downgrade, giữ chỉ đọc; prorate slot thêm; tắt auto-renew; không auto refund; video đầu + hai lần tạo lại | BR-28–33; FR-B; §5.3, §6.1.1, §7.5, §9.6–9.8 | §5.7 |
| Q102–Q104: rewrite, run lại và duyệt activity | Cả hai vai trò yêu cầu rewrite; Teacher thêm hướng lesson; run lỗi kỹ thuật có thể tạo run mới; Teacher activity riêng được xác nhận bằng checklist an toàn tại lớp | BR-08–17; FR-P/FR-T/FR-AI | §5.5–5.6 |
| Q105–Q111 (lịch sử; tuổi bị supersede bởi Q147–Q195) | Teacher xác nhận chiếu theo occurrence; xóa không mở lại sample slot; baseline từng ghi tuổi 36–155 tháng; gói cơ bản trả phí gồm 10 slot; mỗi accepted video request tính quota | BR-06, 10–11, 18, 26, 38; FR-T-16, FR-B-10–13 | §1, §4–7, §14; age scope mới ở §31 |
| Q112–Q114: owner quota, hết quota và carry-forward | Parent account/school organization là hai scope; Teacher usage được quy về organization theo occurrence (owner clarification Rev52); quota tháng; hết quota chặn request mới nhưng giữ playback/dữ liệu; top-up carry-forward đến khi dùng | BR-38; FR-B-10–13; Billing grants + immutable usage ledger | §4, §7, §11, §21, §23; §5.7 |
| Q115–Q118: allowance, video bị từ chối, chu kỳ và FIFO | Số unit được cấu hình cho Parent account và school organization, chốt sau benchmark synthetic; owner clarification Rev52 quy định Teacher usage trừ school quota; ẩn video bị từ chối khi nhận request tạo lại; quota tháng dương lịch Asia/Ho_Chi_Minh; dùng included tháng hiện tại trước, rồi top-up FIFO | BR-16, 38; FR-P-09, FR-B-10–13; §11.1 | §5.7, §7–8, §12 |
| Q119–Q121: xóa run và quota | Xóa run không hoàn unit đã tiêu thụ, giữ tối thiểu usage ledger; top-up một lần, không tự gia hạn; bắt đầu giữa tháng nhận đủ allowance included tháng hiện tại | BR-26, 38; FR-B-10–13; §11, §14, §23 | §5.7, §7–8, quota grants |
| Q122–Q123: hoàn tất và hủy run | VIDEO_READY chờ lệnh hoàn tất/tạo lại nhưng có auto-closeout sau 168 giờ idle; hủy run chưa hoàn tất nhả khóa và xóa nội dung qua lifecycle; không hoàn unit hoặc mở lại sample claim | BR-39–40; FR-C-08, FR-T-15; §6, §11, §21–22 | §5, §7–9 |
| Q124–Q126: hết hạn quota | Included quota chưa dùng hết hạn cuối tháng; top-up carry-forward FIFO đến khi dùng | BR-38; FR-B-10–12; Billing grants + usage ledger; lịch sử diễn giải chỉ ở DECISIONS.md | §4.2, §5.7, §7, §12 |
| Q127–Q133: sample recovery, refund, idle closeout, reassignment, push và quota ledger | Sample claim giữ nguyên sau video playable đầu; mọi accepted request không refund; nhắc ở giờ 144 và đóng ở giờ 168 cho mọi trạng thái chờ người lớn; quyền run/media chuyển khi đổi Teacher; push mobile/web không dùng Firebase Messaging; Billing sở hữu grant + usage; AI job state tách run state | BR-10–11, 17, 38–40; FR-C-11, FR-T-13–15, FR-B-14, FR-O-10; AC-22–28, AT-01–09 | §4.2–5.8, §7–8, §11–14 |
| Q134: owner run/offboarding; Q135: upload session/part; Q136: nhắc email | Q134 đặt `DRAFT` vào adult-wait; khóa theo owner hiện tại tách khỏi creator và reassignment qua saga durable, emergency force-close chỉ ghi metadata/audit. Q135 thêm hai bảng Core, chunk object-PUT 4 MiB và final PutObject đơn. Q136 gửi email best-effort ở +144 giờ nếu owner hiện tại có email đã xác minh; inbox vẫn là nguồn chuẩn. | BR-39/41; FR-C-11/12; FR-T-14/17; §11, §21–24 | §2, §5, §7–9 |
| Q137–Q144: Teacher AI Sketch và pipeline video | Historical trace: Teacher guide now uses adaptive 4–8 progressive steps and the editable presentation target from Rev66; Parent lesson/guide path is separate. Keep the existing LTX-2.5 video pipeline unchanged. | BR-42–45; FR-T-18–20; FR-AI-01/13/14; NFR-33; UC-17; AC-33–37; AT-14–17 | §2/5–11/19/21–22/26/30/31.17; DATA_TABLE_REGISTER §4–7 |
| Q145/Q146: Parent optional AI line-sketch | Historical Q146 was 3–5 steps; Rev66 changes the current target to adaptive 4–8 progressive SVG steps. Guide remains optional, generic and nonblocking to mandatory capture; no child data is sent. Q167 session opt-in remains in force. | BR-42/44/46; FR-P-11; FR-AI-15; AC-44/45; AT-18/19 | §1–2/5–7/13–14/31.17; DATA_TABLE_REGISTER §§4–7 |

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
| Catalog hoạt động đã duyệt | Hoạt động ngoài trời có version, được quản trị nội dung duyệt và phát hành để Parent chọn, Teacher tham khảo. |
| Hoạt động Teacher riêng | Hoạt động chỉ áp dụng một occurrence, do Teacher phụ trách nhập và xác nhận qua safety checklist. |
| Snapshot context tối thiểu | Lựa chọn bất biến từ profile/context được phép, người lớn duyệt cho một run; chỉ chứa đúng một trẻ. |
| Asset nguồn | Tranh/audio/lesson gốc người lớn tải lên; luôn phân biệt với output model. |
| Kết quả stale | Kết quả bất đồng bộ có expected run/revision/input hash không khớp state hiện tại; được lưu dấu nhưng không áp dụng. |
| Dữ liệu demo tổng hợp | Tên, fact profile, artwork, lesson text và audio giả lập cho phát triển/demo, không định danh trẻ thật. |

### 18.2 Giả định

- Onboarding Parent/Teacher đã tồn tại hoặc sẽ được xây trên Firebase Authentication hiện tại. Cách mời/kích hoạt Teacher và xác minh người lớn là quyết định triển khai; không suy diễn Teacher role từ client claim.
- Tổ chức có ít nhất một admin; mỗi lớp active có đúng một Teacher phụ trách. Lớp không thể vận hành nếu thiếu phân công.
- Teacher import lesson nguồn trước khi tạo plan occurrence. Occurrence dùng revision nguồn để xem xét và chọn hoạt động.
- Người lớn có đủ thời gian review transcript giọng trẻ, subject ảnh, activity/context và script. Sản phẩm không phát hành video nếu thiếu tương tác người lớn tại cổng xác nhận script.
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
| Điều kiện tiên quyết | Parent có quyền với hồ sơ; người lớn này không có run chưa kết thúc nào khác. Topic và lesson là tùy chọn; ảnh bắt buộc. Một activity chính phải được chọn trước khi story được tạo.
| Kích hoạt | Parent bắt đầu tạo câu chuyện |
| Luồng chính | Parent có thể chọn topic hoặc pin exact lesson/version để xem presentation kiến thức; guide SVG là tùy chọn → chụp/tải một bức vẽ bắt buộc → nhập text và/hoặc ghi âm → ASR và người lớn xác nhận transcript → VLM phân tích ảnh, đối chiếu topic/lesson nếu có → nếu lệch, thông báo để đổi topic hoặc chụp lại tối đa một lần; sau ảnh thứ hai dùng subject VLM nhận diện, lesson vẫn là nguồn kiến thức → người lớn xác nhận subject/context → catalog-first activity suggestions; người lớn chọn đúng một activity chính trước script, yêu cầu bộ khác phải loại lựa chọn đã hiển thị/từ chối → xác nhận context → AI tạo script/storyboard → tối đa ba lần rewrite trong giới hạn và adult review → xác nhận script cuối → video admission và pipeline hiện hành chạy bất đồng bộ → technical/safety validation và private playback → no-pin hiển thị activity chính đã lưu trong run; lesson pin hiển thị toàn bộ activities của exact pinned version và đánh dấu activity chính.
| Luồng thay thế | Từ chối audio quá dài/quá lớn trước inference; chỉnh transcript tạo revision mới; chỉnh chủ thể chạy lại VLM; người dùng có thể yêu cầu tối đa ba lần viết lại story; từ chối output model sai định dạng/cũ; hết retry kỹ thuật thì đánh dấu run thất bại; video sẵn sàng nhưng không phù hợp thì quay lại bước rà soát kịch bản trong giới hạn tạo lại để cải thiện chất lượng |
| Hậu điều kiện | Run gắn một trẻ, snapshot context và activity chính đã xác nhận trước story, lesson version optional đã pin, provenance script/video bất biến; activity chính được trình bày sau video, cùng toàn bộ activities của lesson pin nếu có. Artifact riêng tư có thể phát; không trả URL tải xuống.
| Dữ liệu/yêu cầu | story.*; ai_jobs.*; core.asset_metadata/core.asset_lineage; FR-P và FR-AI |

### UC-03 — Teacher tạo hồ sơ do tổ chức quản lý

| Hạng mục | Đặc tả |
|---|---|
| Actor chính | Teacher phụ trách; School Manager của organization có thể quản lý thành viên roster |
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
| Điều kiện tiên quyết | Plan occurrence đã duyệt; còn slot video mẫu; Teacher vẫn phụ trách; roster và policy eligibility/consent đã được phê duyệt; hệ thống chỉ tạo run sau khi chọn child theo policy đó và Teacher xác nhận selection/context; người lớn không có run khác đang active |
| Kích hoạt | Teacher bắt đầu yêu cầu video mẫu; hệ thống chọn ngẫu nhiên một child từ tập đủ điều kiện theo policy đã duyệt và trình cho Teacher xác nhận |
| Luồng chính | Hệ thống tạo tập đủ điều kiện theo eligibility/consent policy đã được chủ sở hữu duyệt và chọn ngẫu nhiên một child; Teacher xem và xác nhận child/context trước khi bắt đầu run → tạo run gắn với đúng một child/occurrence/plan đã duyệt → ghim một hoạt động đã chọn → duyệt context hồ sơ tối thiểu → chụp bằng browser hoặc tải ảnh điện thoại lên → thêm văn bản/voice → rà soát transcript và chủ thể → AI soạn kịch bản → Teacher có thể yêu cầu viết lại trong giới hạn rồi xác nhận kịch bản → application reserve GPU budget worst-case qua AI Policy, sau đó Billing cấp quota admission atomic/idempotent → chạy video job → video qua kiểm tra an toàn được hiển thị ngay cho Teacher phụ trách → trước khi chiếu cho lớp, Teacher xác nhận đối tượng/mục đích sử dụng cho occurrence này → Teacher kết thúc hoặc đánh dấu không phù hợp → nếu không phù hợp, phải rà soát/xác nhận kịch bản và được cấp quota trước khi tạo lại để cải thiện chất lượng |
| Luồng thay thế | Không có child đủ điều kiện: dừng selection, giữ occurrence ở state hiện hành, không tạo sample run/job/quota/claim, không fallback và chỉ hiển thị thông báo chung không có lựa chọn hợp lệ; không lộ lý do loại theo từng child. Candidate stale được chọn lại tối đa một lần. Teacher chưa xác nhận thì không accept run; selection expiry/resume và audit evidence còn OPEN theo Q-01. Từ chối mọi request có nhiều child ID, trẻ ngoài roster/phân công hiện hành hoặc plan cũ; nếu hết quota, trả VIDEO_QUOTA_EXCEEDED và không dispatch; request đã chấp nhận tiêu thụ quota dù sau đó lỗi kỹ thuật/bị chặn an toàn; lỗi kỹ thuật hoặc chặn an toàn trước playback để slot mẫu occurrence còn trống; sau khi chấp nhận một video mẫu có thể phát và đã qua an toàn, không được bắt đầu run mẫu độc lập khác cho occurrence; chỉ được tạo lại để cải thiện chất lượng trong cùng run; nếu chưa xác nhận trình chiếu thì không cấp token class-projection |
| Hậu điều kiện | Tối đa một video mẫu có thể phát và đã qua kiểm tra an toàn được giữ cho occurrence. Video đó gắn với một trẻ và một hoạt động. |
| Dữ liệu/yêu cầu | lesson.*, story.*, ai_jobs.*, billing.video_quota_grants/video_quota_usage; ai_policy.resource_* chỉ cho GPU/compute metering; notifications.inbox_items/push_endpoints; FR-T-10–16, FR-AI, FR-B-10–14, BR-09–17, BR-38 |

### UC-06 — School Manager quản lý sức chứa và lớp

| Hạng mục | Đặc tả |
|---|---|
| Actor chính | School Manager của organization |
| Điều kiện tiên quyết | School Manager có quyền quản lý lớp và có thể đọc subscription/sức chứa; cách lưu/resolver permission còn mở tại §31.10 |
| Kích hoạt | School Manager tạo lớp, mua slot, phân công Teacher hoặc hạ sức chứa |
| Luồng chính | Backend đọc sức chứa hiệu lực từ Billing → transaction tạo lớp khóa/kiểm tra slot còn trống → tạo lớp → School Manager phân công một Teacher phụ trách → cấp quyền roster |
| Luồng thay thế | Khi hết sức chứa, tạo lớp mới trả CLASS_CAPACITY_REACHED; School Manager có thể chuyển sang luồng billing để mua thêm sức chứa; các thao tác tạo lớp đồng thời được tuần tự hóa; lớp bị tạm ngưng chỉ xem được; khi hạ gói phải chọn lớp sẽ tạm ngưng |
| Hậu điều kiện | Số lớp active không vượt sức chứa hiệu lực; mỗi lớp cho phép ghi có một Teacher phụ trách; quyền xem media được quản lý riêng. |
| Dữ liệu/yêu cầu | be1.classrooms/assignments; billing.capacity_periods; FR-T-02/03, FR-B |

### UC-07 — Người lớn xóa run ở COMPLETED, FAILED hoặc ABANDONED

| Hạng mục | Đặc tả |
|---|---|
| Actor chính | Chủ sở hữu Parent hoặc Teacher hiện đang được phân công phụ trách lớp; creator cũ chỉ còn provenance |
| Điều kiện tiên quyết | Run ở COMPLETED, FAILED hoặc ABANDONED; caller có quyền; run chưa trong quá trình xóa |
| Kích hoạt | Người lớn chọn Xóa session/run |
| Luồng chính | API xác minh Parent owner hoặc Teacher phụ trách hiện tại → ghi lifecycle request → chặn cấp playback token mới → xóa transcript, audio/tranh đầu vào, context snapshot, story revision, asset scene/video được tạo và asset phái sinh riêng tư đủ điều kiện → ghi hoàn tất và audit chỉ có metadata |
| Luồng thay thế | Thất bại xóa object hiện tại được retry idempotent và trạng thái vẫn pending; giữ asset dùng chung đến khi đối soát các tham chiếu được phép khác; Teacher cũ sau reassignment không còn quyền xóa, Teacher phụ trách mới được xử lý theo policy lifecycle |
| Hậu điều kiện | Nội dung run bị xóa theo lifecycle. Invoice Billing và audit metadata tối thiểu không bị ảnh hưởng. Không có thao tác xóa video riêng hoặc thời gian chờ để khôi phục từ thùng rác. |
| Dữ liệu/yêu cầu | be1.data_lifecycle_requests, core.asset_metadata/lineage, story.*; FR-C-08, BR-26 |

### UC-08 — School Manager gia hạn hoặc đổi sức chứa organization

| Hạng mục | Đặc tả |
|---|---|
| Actor chính | School Manager của organization có permission billing |
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

### UC-10 — Người lớn xem quota; mua đơn vị nếu policy được bật

| Hạng mục | Đặc tả |
|---|---|
| Actor chính | Người lớn được xác thực xem quota trong scope của mình; actor có quyền mua (nếu có) chưa được owner chốt tại Q193 |
| Điều kiện tiên quyết | Tài khoản đã xác thực có scope áp dụng. Nhánh mua chỉ dùng sau khi policy offer, actor/permission và giá/gói được owner duyệt theo Q193; nếu chưa duyệt thì chỉ xem quota |
| Kích hoạt | Người lớn xem quota hoặc request generation bị từ chối vì không còn đơn vị; nhánh purchase chỉ bắt đầu khi actor được policy đã duyệt cho phép |
| Luồng chính | Backend suy ra Parent-account hoặc occurrence-school scope từ principal/assignment đã xác minh → Billing trả quota summary từ grant hợp lệ và `video_quota_usage` → nếu có owner-approved offer và actor/permission, purchase command kiểm tra policy, số lượng và price version → tạo invoice/payment attempt → xác minh callback MoMo/VNPAY idempotent → cấp grant → summary phản ánh grant → caller có thể gửi video request mới sau khi grant khả dụng. Nếu chưa có quyết định Q193 thì chỉ dừng ở quota summary, không có nhánh mua |
| Luồng thay thế | Request bị từ chối vì hết quota không tiêu thụ đơn vị và không tạo AI job; actor không có purchase permission hoặc policy chưa được duyệt chỉ xem quota, không được tạo purchase; callback checkout lặp không tạo grant trùng; failed/pending không tạo entitlement; request được chấp nhận khi còn quota tiêu thụ một đơn vị kể cả khi generation sau đó thất bại/bị chặn an toàn; khi hết quota vẫn xem được playback và lịch sử video hiện có |
| Hậu điều kiện | Billing tính quota từ grant append-only trừ usage ledger append-only; không có balance mutable. Grant included chưa dùng hết hạn cuối tháng; nếu top-up được owner bật thì carry-forward đến khi dùng hết. Trong mỗi tháng dùng included trước rồi top-up FIFO (Q117–Q118, Q124–Q126); không có owner purchase decision suy ra từ quy tắc charge order. |
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

### UC-12 — School Manager đổi Teacher phụ trách và offboard

| Hạng mục | Đặc tả |
|---|---|
| Actor chính | School Manager của organization được cấp quyền quản lý lớp |
| Điều kiện tiên quyết | Lớp active có Teacher hiện hành; replacement thuộc tổ chức/provisioned. Normal transfer chỉ nhận nếu không có active-run lock conflict; emergency force-close được School Manager tường minh trước retry. |
| Kích hoạt | School Manager chọn đổi Teacher hoặc offboard Teacher hiện tại |
| Luồng chính | Backend preflight quyền/assignment version → BE1 ghi transfer-pending và revoke old access/token ngay, lớp thành read-only → Story owner-transfer command kiểm tra uniqueness và chuyển `active_owner_teacher_id`/lock trong Story transaction → BE1 finalize current assignment sau receipt → new Teacher được cấp access; giữ creator provenance; ghi audit metadata/inbox. Job hợp lệ tiếp tục, completion chỉ nhận theo input/hash/occurrence/assignment fence hiện hành. |
| Luồng thay thế | Teacher mới có run active thì Story trả conflict; saga bù BE1 về assignment cũ và khôi phục quyền cũ nếu được xác minh. Nếu thao tác bù timeout/mơ hồ, giữ transfer-pending/read-only và reconcile cùng idempotency key; không cấp content cho Teacher cũ/mới trước khi trạng thái nhất quán. School Manager của organization sở hữu lớp có thể force-close run xung đột bằng emergency Story command tường minh có reason/audit metadata; status thành ABANDONED, khóa được nhả, không xóa media hoặc cho School Manager xem. Sau đó School Manager retry reassignment. Quota/sample claim giữ nguyên; authorization persistence/resolver còn mở. |
| Hậu điều kiện | Khi finalize, lớp có đúng một Teacher current; `created_by_actor_ref` không đổi; quyền mới chỉ mở sau lock receipt; admin không xem media. Transfer pending không cho tạo run. |
| Dữ liệu/yêu cầu | be1.organization_assignments/classrooms; story.runs(active owner); core.audit_events; notifications.inbox_items; FR-T-02/14/17, BR-05/06/41; Q130/Q134 |

### UC-13 — School Manager provision Teacher và khôi phục tài khoản người lớn

| Hạng mục | Đặc tả |
|---|---|
| Actor chính | School Manager của organization và người lớn cần kích hoạt/khôi phục tài khoản |
| Điều kiện tiên quyết | Kênh xác minh identity đã cấu hình; School Manager được xác thực; scope Parent/Teacher chưa bị tiết lộ qua public lookup |
| Kích hoạt | School Manager mời Teacher hoặc người lớn khởi tạo khôi phục tài khoản |
| Luồng chính | Backend tạo/đảm bảo Firebase Authentication identity trước, ghi BE1 identity ở trạng thái chờ xác minh và assignment chưa active → Firebase Admin SDK tạo email-verification/password-reset action link → notification email adapter gửi link → người nhận xác minh và hoàn tất sign-in → backend xác minh Firebase ID token cùng `email_verified` rồi kích hoạt scope/assignment theo policy → trả kết quả tổng quát không tiết lộ UID ở scope khác. Firebase quản lý action code; ứng dụng chỉ lưu trạng thái identity/assignment, không thêm invitation-token table. |
| Luồng thay thế | Link hết hạn/đã dùng trả trạng thái tổng quát và cho admin gửi lại; conflict Parent/Teacher account trả `ACCOUNT_SETUP_UNAVAILABLE` chung; email provider lỗi giữ invitation pending và có retry hữu hạn; nếu Firebase Auth không phát/kiểm tra được action link, không kích hoạt account và chuyển yêu cầu sang trạng thái retryable. |
| Hậu điều kiện | Không có role claim do client tự cấp; audit lưu metadata; không lưu action token hoặc raw recipient email trong app database/log; provider-managed activation link được dùng một lần/hết hạn. |
| Dữ liệu/yêu cầu | be1.adult_identities/organization_assignments; core.audit_events; notifications; Firebase Authentication action-link adapter; không có token table; FR-C-01, FR-O-09 |

### UC-14 — Quản trị nội dung phát hành catalog hoạt động

| Hạng mục | Đặc tả |
|---|---|
| Actor chính | Platform Admin (Content Admin permission) |
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
| Luồng chính | Khi Teacher bật guide, backend pin approved plan revision/hash và tạo deck revision → mỗi guide theo activity/chủ thể có adaptive 4–8 bước progressive; dùng SVG catalog trước, AI draft chỉ khi capability được phép → backend kiểm schema/coverage/safety/media/lineage rồi đánh dấu READY → Teacher preview/điều khiển Back/Next/select/skip/regenerate và trình chiếu trên nền trắng 16:9. Teacher có thể sửa text/order/slide và đặt ảnh upload, SVG hoặc link YouTube/Vimeo đã xác thực vào slide trong presentation revision → trẻ vẽ trên giấy → trong luồng video hiện có Teacher chọn một activity và child đại diện ngẫu nhiên đủ điều kiện, chụp tranh và chạy story-video mới; video chỉ xuất hiện sau pipeline/safety gate. |
| Luồng thay thế | Nếu Teacher không bật, occurrence tiếp tục không có deck/job. Nếu plan đổi, deck cũ thành STALE; regenerate tạo revision bất biến mới. Sketch lỗi có thể skip/regenerate; hết cost/rate cap trả lỗi sketch-specific, không tiêu video quota. |
| Hậu điều kiện | Occurrence có một deck revision READY gắn với plan hash hiện hành hoặc vẫn không có deck; trạng thái Back/Next/skip không lưu server. Deck dùng chung, không mang profile/tranh/nhận diện trẻ. Story video mẫu vẫn chỉ có một child và một activity/occurrence. |
| Dữ liệu/yêu cầu | lesson.sketch_deck_revisions/steps; lesson.plan_revisions/activities; core.asset_metadata/asset_lineage; ai_jobs.job/attempt; AI Policy compute metering; FR-T-18–20, FR-AI-14, BR-42–44, NFR-33 |

**Phản hồi hỗ trợ riêng:** V1 đã định nghĩa đánh dấu không phù hợp để ẩn video và quay lại script. Luồng gửi báo cáo hỗ trợ/đính kèm video cho operator chưa được xác định; mặc định không cấp cho operator quyền đọc media, và không thu thập media báo cáo cho đến khi quyền truy cập, consent/authorization và retention được duyệt.

<a id="srs-20"></a>
## 20. Ma trận phân quyền

Các role sản phẩm trong ma trận là Parent, Teacher, School Manager và Platform Admin như §31.3. School Manager là tên thống nhất cho quyền quản lý một organization (tên lịch sử “Admin tổ chức”). Content review/publish/moderation là permission capability trong Platform Admin, không phải một role riêng. System Operator là principal kỹ thuật, không phải role sản phẩm. Teacher được đọc run/media theo lớp đang được phân công; sau reassignment, quyền chuyển sau khi assignment commit và quyền/token của Teacher cũ bị revoke ngay; `created_by` chỉ là provenance. School Manager và Platform Admin không có quyền đọc child media mặc định. Platform Admin child-media access đang deny cho đến khi owner duyệt một quy trình truy cập riêng; reason/audit đơn lẻ không tạo quyền. System Operator chỉ xử lý health/metadata đã redact và lifecycle command, không đọc nội dung.

| Tài nguyên/thao tác | Parent | Teacher phụ trách | School Manager | Platform Admin (có permission cần thiết) | System Operator |
|---|---|---|---|---|---|
| Tạo/đọc/cập nhật hồ sơ Parent của mình | Hồ sơ của mình | Không | Không | Không | Không |
| Đọc/cập nhật ghi chú nhu cầu hỗ trợ Parent | Chỉ hồ sơ của mình | Không | Không | Mặc định deny; child-media/profile access chưa được mở | Không |
| Tạo/đọc hồ sơ Teacher được quản lý | Không | Chỉ lớp được phân công | Roster trong organization của mình | Không | Không |
| Quản lý lớp/phân công Teacher | Không | Không | Organization của mình | Quản lý policy nền tảng, không thay School Manager | Không |
| Quản lý thành viên roster | Không | Lớp được phân công theo policy | Organization của mình | Không | Không |
| Đọc tài liệu/plan giáo án | Không | Teacher phụ trách occurrence | Metadata/review nội dung lesson trong organization theo permission | Lesson public/catalog theo content permission | Không có quyền nội dung |
| Tạo/đọc/trình chiếu/regenerate AI Sketch Deck | Không | Teacher phụ trách occurrence | Metadata, không child/media deck content mặc định | Không | Không có quyền nội dung |
| Chọn hoạt động Parent | Chỉ catalog đã publish | Chỉ catalog đã publish | Chỉ catalog đã publish | Review/publish khi có content permission | Không |
| Tạo hoạt động riêng cho Teacher occurrence | Không | Teacher phụ trách | Không | Không | Không |
| Tạo story run | Hồ sơ Parent của mình | Một trẻ trong lớp được phân công/occurrence đã duyệt | Không | Không | Không |
| Đọc story/kịch bản/transcript/video | Run Parent của mình | Run lớp hiện được phân công, kể cả run tạo trước reassignment | Deny | Deny cho đến khi quy trình owner phê duyệt; role không tự cấp quyền | Không có quyền nội dung |
| Hỗ trợ truy cập child media | Không áp dụng | Chỉ run được phân công | Deny | Deny-by-default; quy trình permission/approval/expiry/break-glass còn mở | Deny |
| Đánh dấu video sẵn sàng không phù hợp/tạo lại | Run Parent của mình | Run của lớp hiện được phân công, nếu run còn cho phép thao tác | Không | Không | Không |
| Xác nhận chiếu video cho lớp trong occurrence | Không | Teacher phụ trách hiện tại; ghi xác nhận theo occurrence | Không | Không | Không |
| Xem tóm tắt quota | Scope tài khoản Parent của mình | Pool school của occurrence được phân công | School pool của organization mình | Chỉ policy/tổng hợp nền tảng | Chỉ metrics vận hành tổng hợp |
| Mua đơn vị quota video | Quyền mua package/top-up OPEN theo Q193 | Không có Teacher-account pool hoặc quyền mua quota riêng | Quyền mua/cấp/phân bổ quota school OPEN theo Q193 | Quản lý policy nền tảng; quyền mua sản phẩm không suy diễn | Chỉ cấu hình provider |
| Xóa nội dung run ở COMPLETED, FAILED hoặc ABANDONED | Run Parent của mình | Run của lớp hiện được phân công, theo lifecycle | Không | Không | Chỉ lifecycle command, không đọc nội dung |
| Hủy run chưa hoàn tất | Run Parent của mình | Run của lớp hiện được phân công, theo lifecycle | Không | Không | Chỉ lifecycle command, không đọc nội dung |
| Quản lý subscription/thanh toán/sức chứa | Không | Không | Có quyền billing trong organization của mình | Policy nền tảng | Không |
| Xem health/metrics hệ thống đã loại thông tin nhạy cảm | Không | Không | Không | Theo quyền quản trị nền tảng | Có |

Backend kiểm tra role và permission ở mọi thao tác đọc/ghi, cấp playback token và hoàn tất bất đồng bộ. Role claim từ UI chỉ là gợi ý; backend tải và xác thực resource scope cùng phân công hiện tại. Content permission không bao hàm child-media permission. Phản hồi từ chối không được làm lộ việc hồ sơ/run của organization khác có tồn tại hay không.

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
| POST /v1/organizations/{org_id}/classes | School Manager của organization | Kiểm tra sức chứa hiệu lực trong transaction | 201 class ref hoặc CLASS_CAPACITY_REACHED |
| POST /v1/classes/{class_id}/assignments | School Manager của organization | Chính xác một Teacher phụ trách active | 200 assignment revision |
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
| POST /v1/story-runs | Parent hoặc Teacher | Chính xác một profile ref có kiểu; scope khớp role; optional typed lesson-version ref; Parent kèm đúng một main activity selection/ref đã chọn trước script; Teacher kèm occurrence/plan và đúng một activity đã duyệt; idempotency key | 201 run resource; không nhận mảng trẻ |
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
| DELETE /v1/story-runs/{id} | Chủ sở hữu Parent hoặc Teacher được phân quyền | Chỉ run ở COMPLETED, FAILED hoặc ABANDONED; lifecycle command idempotent | 202 deletion request/status |
| GET /v1/jobs/{job_id} | Actor của run được phân quyền | Job phải thuộc scope của actor | 200 trạng thái job có version |
| POST /v1/story-runs/{id}/playback-token | Actor của run được phân quyền hiện tại | Artifact hiện tại ở VIDEO_READY, đã qua kiểm tra; kiểm tra assignment/scope hiện tại | 200 playback token thời hạn ngắn, giới hạn vào một asset; run active đến complete, idle closeout hoặc cancel |
| POST /v1/organizations/{org_id}/subscription/checkout | Admin billing | Price version, kỳ billing và sức chứa mong muốn | 202 payment attempt/redirect instruction |
| GET /v1/video-quota | Chủ Parent, Teacher được phân công hoặc admin billing tổ chức | Suy ra scope từ actor đã xác minh; không nhận owner ID từ client | 200 quota được cấp/đã dùng/còn khả dụng và mốc kỳ đã tính |
| POST /v1/video-quota/purchases (TO-BE; Q193 gate) | Actor/permission chỉ được xác định sau owner decision | Offer/scope/actor policy phải được duyệt; số lượng/price version do server xác định; idempotency key | Nếu được bật: 202 invoice/payment attempt; chỉ cấp grant sau khi xác minh thanh toán |
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
| Android Parent | Đăng nhập/khôi phục tài khoản; danh sách/biểu mẫu hồ sơ trẻ; lịch sử run; chụp/chọn tranh; ý tưởng văn bản/audio; rà soát transcript; xác nhận/chỉnh chủ thể; catalog hoạt động; rà soát context snapshot; rà soát script/storyboard; tiến độ job; trình phát video; Hoàn tất/hủy run; tóm tắt quota; package/top-up purchase availability remains OPEN under Q193; xóa run ở COMPLETED, FAILED hoặc ABANDONED | Yêu cầu quyền theo ngữ cảnh; từ chối camera vẫn cho tải ảnh từ thư viện; từ chối microphone vẫn cho nhập ý tưởng; tiếp tục stage sau khi app chạy nền; trạng thái quota lấy từ server; không có batch trẻ/gallery/export |
| Web Teacher | Đăng nhập; chọn tổ chức/lớp; roster; biểu mẫu hồ sơ có cấu trúc; lesson occurrence; upload/trích xuất tài liệu; rà soát/chỉnh revision văn bản trích xuất; plan/objective/hướng truyện/checklist hoạt động; xem/xác nhận child do hệ thống chọn ngẫu nhiên theo policy đã duyệt; camera/upload; rà soát transcript/chủ thể/context; rà soát script; tiến độ job; trình phát video; xác nhận chiếu theo occurrence; Hoàn tất/hủy run; xem quota school của occurrence (không có Teacher-account pool, không có hành động mua quota riêng); lịch sử run/occurrence | Chỉ hiện lớp được phân công; checklist an toàn chặn duyệt plan; occurrence hiển thị trạng thái một video mẫu; chiếu cần xác nhận; không tạo hàng loạt theo roster |
| School Manager | Dashboard organization; xem sức chứa lớp; tạo/archive/tạm ngưng lớp; phân công Teacher phụ trách; quản trị roster; kỳ billing/invoice/trạng thái thanh toán; tự gia hạn/hạ gói lớp; xem quota school; quyền mua/cấp/phân bổ video quota còn OPEN theo Q193; inbox thông báo | Khi tạo lớp kiểm tra sức chứa hiệu lực; hạ gói yêu cầu chọn lớp; màn hình billing không bao giờ để lộ media/story của trẻ |
| Platform Admin — Quản trị nội dung | Nháp/rà soát/xuất bản catalog hoạt động | Version đã xuất bản là bất biến; thay đổi tạo version mới cần rà soát |
| Dashboard operator | Health, queue, trạng thái tổng hợp job, đối soát billing, backlog lifecycle | Chỉ metadata vận hành đã loại thông tin nhạy cảm; không drill-down hồ sơ/story/media |

Màn hình run giải thích thời điểm cần người lớn nhập liệu. Không hiển thị phần trăm bịa đặt. Trẻ hoặc người lớn không thể duyệt chỉ bằng cách đi qua các màn hình; xác nhận phải là command gắn với revision hash chính xác.

### 21.6 Hành vi khôi phục của client theo nhóm lỗi

| Nhóm/mã lỗi | Hành vi client | Chính sách retry |
|---|---|---|
| AUTH_REQUIRED, INVALID_TOKEN, TOKEN_EXPIRED | Làm mới hoặc xác thực lại bằng Firebase; chỉ quay về màn hình ban đầu sau khi token được xác minh | Retry một lần sau khi làm mới thành công; không lặp vô hạn |
| RESOURCE_NOT_FOUND (ID không tồn tại hoặc ngoài scope) | Báo không tìm thấy/không thể truy cập cùng một cách; làm mới danh sách tài nguyên được phép | Không retry cùng command tài nguyên |
| ACTION_NOT_ALLOWED (resource cùng scope nhưng actor không được phép thực hiện action) | Báo thao tác không được phép, không tiết lộ policy nội bộ | Không retry cùng command; chỉ tiếp tục khi role/assignment hợp lệ |
| ACTIVE_RUN_EXISTS | Đề nghị tiếp tục/mở run active hiện tại nếu caller sở hữu, hoặc hủy run chưa hoàn tất; không tạo run thứ hai | Chỉ thử tạo lại sau khi complete, hủy được chấp nhận hoặc run thất bại/kết thúc |
| MULTI_CHILD_NOT_SUPPORTED | Giải thích mỗi story gắn với một child do hệ thống chọn; quay lại bước Teacher xem/xác nhận child/context | Không retry tự động |
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
5. Worker gửi completion command đến application layer. Completion xác minh đúng target kind/ref/revision/hash; StoryRun target kiểm run/input/lesson/activity; generation target kiểm run/script/generation; scene target kiểm scene thuộc đúng generation/revision; Lesson document/deck target kiểm occurrence assignment/plan hash/deck schema; Parent guide target kiểm generic topic contract, safe output, owner scope và expiry policy.
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
- Xóa run ở COMPLETED, FAILED hoặc ABANDONED cũng tạo lifecycle request; lệnh delete không tạo refund hoặc xóa quota ledger/sample claim metadata.
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

- Parent quota thuộc một tài khoản Parent; video do Teacher khởi tạo ghi vào quota của organization sở hữu occurrence. Không có Teacher-account pool. Backend suy ra owner scope từ principal và assignment đã xác thực; client không chọn owner ID/quota.
- Billing sở hữu `billing.video_quota_grants` và `billing.video_quota_usage`. Grant là entitlement append-only; usage là ledger append-only, mỗi accepted full-video request ghi đúng một unit và tham chiếu grant đã dùng. AI Policy `resource_reservation`/`resource_event` chỉ đo platform GPU/compute capacity và chi phí tài nguyên; resource event là idempotency ledger command mới, còn bảng `resource_receipt` lịch sử không ghi thêm và không tham gia quota sản phẩm.
- Grant monthly included được gắn theo Parent-account hoặc school-organization scope; Teacher sử dụng grant school của occurrence, không có grant/pool tài khoản Teacher. Lượng included chốt sau synthetic cost/latency benchmark. Scope bắt đầu giữa tháng nhận đầy đủ included allowance tháng đó, không prorate (Q115, Q121). Included grant hết hạn cuối tháng lịch `Asia/Ho_Chi_Minh`; phần dư không chuyển tháng sau. Nếu top-up được owner bật, đó là giao dịch mua một lần, không tự gia hạn và không hết hạn; dùng grant included hiện tại trước rồi top-up theo FIFO (Q114, Q117–Q120, Q126).
- Quota admission là use case của Billing qua port có version. Story ghi một intent `ADMISSION_PENDING`; application saga lấy compute-reservation receipt từ AI Policy, sau đó gọi Billing để kiểm tra scope/grant và ghi usage trong transaction riêng do Billing sở hữu. Chỉ khi cả hai receipt có trạng thái xác nhận, Story chuyển generation intent sang `ACCEPTED` trong transaction Story và ghi outbox; không có một transaction PostgreSQL bao trùm các module. Nếu budget/quota bị từ chối thì saga ghi intent `ADMISSION_REJECTED`, release reservation nếu có và không dispatch. Nếu outcome không rõ sau crash/timeout, reconcile bằng cùng idempotency key trước dispatch; usage đã commit ở Billing phải được nối lại với Story intent đúng một lần, không được tạo lại hoặc refund. `billing_quota_usage_ref` trong `story.video_generations` là opaque receipt tham chiếu, không phải FK/cột ledger chung. Số dư chỉ được tính trong Billing từ grants trừ usage.
- Chỉ request bị từ chối trước khi admission commit mới không tiêu thụ quota. Một khi accepted request/usage đã commit trước dispatch, unit không được hoàn trong bất kỳ trường hợp nào: queue/provider ambiguity, technical failure, safety block, cancellation hoặc xóa run (Q110, Q119, Q128). Retry cùng idempotency key trả về cùng generation/usage; scene retry kỹ thuật không phải request mới. Mỗi run tối đa một request đầu + hai request tạo lại chất lượng; mỗi request đã nhận tính vào cap này kể cả khi lỗi.
- Nếu scope không còn unit, từ chối bằng 409 `VIDEO_QUOTA_EXCEEDED`, không tạo accepted generation, usage row hoặc AI dispatch. Hết quota không chặn xem video/dữ liệu đã lưu hoặc xóa run. Xóa run purge nội dung theo lifecycle nhưng giữ metadata usage tối thiểu để đối soát; không hoàn grant đã tiêu thụ.
- Nếu owner phê duyệt bán top-up, báo giá theo price version do server kiểm soát, tạo invoice theo owner scope có kiểu và chỉ phát grant sau payment event MoMo/VNPAY đã xác minh, dedupe và ghi nhận idempotent. Actor có quyền mua, cấu hình offer/price và phân bổ grant vẫn OPEN theo Q193/§31.10(2),(6). Không phát grant từ browser redirect/callback pending. Chính sách hoàn tiền thanh toán thương mại xử lý riêng; không sửa/xóa usage ledger.

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

Activity catalog dùng contract có kiểu/version, không thêm bảng. Contract đích ActivityCatalogItemV2 có trường: supported ages/month ranges; subject/objectives; theme; setting/context; season; outdoor location; duration; materials/equipment; accessibility; safety constraints; status/review version. Đây là metadata có cấu trúc, không phải prompt tự do. Contract catalog hiện tại chưa có đủ các trường này; chỉ lọc theo trường được phiên bản hiện tại cung cấp. Chỉ bật lọc dựa trên toàn bộ metadata sau khi nâng cấp đồng bộ contract version, fixtures và client/server adapters. Không thêm bảng: learning_content.record/version hiện hữu tiếp tục là nguồn chuẩn. Moderation không đổi: Parent chọn catalog toàn cục đã duyệt; Teacher chọn catalog hoặc activity riêng trong occurrence đã xác nhận bằng checklist an toàn.

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

CI/CD đã có GitHub Actions CI tại `.github/workflows/ci.yml`, chạy trên `push` và `pull_request`. Workflow hiện có repository-policy checks bằng Python 3.12.14, backend contract/unit/integration jobs, và Child/Teacher/Admin UI checks bằng Node 24.15.0 (`npm ci`, `npm run check`). Đây là mô tả source/configuration, không phải kết quả của một CI run cụ thể. Snapshot source Rev58 tại §32.8 không thấy workflow CD; provider/host/region/registry triển khai chưa được chọn.

**Luồng CI/CD đích (TO-BE):**

1. Mỗi pull request và push chạy các CI jobs hiện có cùng các gate được duyệt. Chỉ trạng thái xanh mới cho phép merge vào `dev`; artifact được gắn với full commit SHA và digest bất biến.
2. Sau khi merge `dev`, pipeline đóng gói một lần rồi triển khai đúng artifact đó lên staging. Staging chỉ dùng fixture/synthetic data, không dùng hồ sơ hoặc media trẻ thật.
3. Staging kiểm tra health/readiness và smoke theo các contract: Parent hoàn tất flow một trẻ khi không gắn Lesson Preset và không thêm hoạt động riêng của Lesson; occurrence Teacher giữ lesson version/hash đã pin khi lesson có revision mới; roster synthetic không có trẻ đủ điều kiện trả `SAMPLE_NOT_AVAILABLE`, không lộ chi tiết trẻ, không tạo story/video job, không tiêu quota và không chiếm sample slot; profile-sharing chỉ cho recipient/profile/version trong allowlist và revoke chặn request mới.
4. Release tag `vX.Y.Z` promote cùng artifact digest đã qua staging, không build một artifact khác; sau promote kiểm tra health, API readiness, safety gates và smoke suite.
5. Nếu deploy hoặc smoke/health thất bại, dừng promotion, giữ hoặc khôi phục digest tốt gần nhất, kiểm tra migration compatibility/rollback, ghi commit, digest, bước lỗi và trạng thái rollback.

Các gate dưới đây là yêu cầu cho pipeline triển khai tương lai; chúng không khẳng định CD đang cấu hình/chạy:

1. Format/lint/type checks cho module đổi và consistency check generated contracts.
2. Unit/domain/contract suites, boundary tests theo feature plan được duyệt.
3. Dependency/secret/container-image scan và repository security validator.
4. Migration trên PostgreSQL disposable từ source baseline; kiểm tra index/constraint, reconciliation, rollback/feature-flag path.
5. Build Android/web; xác minh client bundle không có credential/provider endpoint.
6. Compose smoke/readiness, restart persistence, synthetic local end-to-end khi workstream được duyệt.
7. Feature-flag release; kiểm tra migration parity, rollback, dashboard/cảnh báo trước khi bật traffic.

Đây là luồng phát hành đích dùng để thiết kế và viết kịch bản nghiệm thu. Nó không khẳng định CI run, build, CD, deployment hay migration đã được thực hiện; không chọn production host/region/registry; và không đóng các owner/policy gates.

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
| Teacher confirmation request tham chiếu child không active-enrolled trong lớp được giao | Từ chối authorization; không tạo story run |
| School Manager yêu cầu media của Teacher run | Từ chối, không tiết lộ private run content |
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
| Temporary test assumption — Teacher occurrence có roster tổng hợp nhưng không có trẻ đủ điều kiện | Kịch bản thiết kế tạm dùng `SAMPLE_NOT_AVAILABLE`; không trả chi tiết hồ sơ/trẻ, không tạo story/video job, không tiêu quota hoặc chiếm sample slot. Không chốt quy tắc eligibility/consent, reselection hay evidence chọn trẻ. |
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
| R-19 | Run `COMPLETED`/`FAILED`/`ABANDONED` và media giữ đến khi người dùng xóa có thể lưu lâu vô hạn | H | C | Privacy/legal + Product | Chấp nhận chỉ cho synthetic demo; production bị chặn đến khi có retention tối đa, backup expiry, deletion evidence và DSR policy; idle closeout giữ nội dung theo Q133 |
| R-20 | Android push không hoạt động với đa số thiết bị hoặc cần distributor/provider không phổ biến | H | M | Mobile + Architecture | Inbox/email là fallback chuẩn; provider Android chỉ là POC gate; không dùng FCM theo repo rule; không quảng bá delivery trước khi chứng minh |
| R-21 | Outbox + RQ + poller tự dựng saga dài khó vận hành hơn workflow engine | M | H | Architect + Operations | ADR so sánh Temporal trước khi implementation; đánh giá crash recovery, timers, cancel/compensate, cost và burden |
| R-22 | Cost per accepted video không khớp giá quota/allowance | H | H | Commercial + AI lead | Benchmark GPU seconds/output/storage; configure included/top-up; hard admission reservation và daily circuit breaker trước demo live |
| R-23 | Hóa đơn điện tử, VAT, consumer policy hoặc provider recurring khác giả định | M | H | Commercial + Legal + Billing | Không thu tiền production trước legal/accounting review và merchant sandbox/approval |
| R-24 | Video mẫu một trẻ chiếu cho cả lớp tạo cảm nhận thiên vị hoặc lộ dữ liệu ngoài mục tiêu | M | H | Product + Education reviewer | Xác nhận riêng theo occurrence, không tái dùng cho thành viên, không thêm danh tính vào payload; review kịch bản chiếu trước production |
| R-25 | Upload lớn bị gián đoạn, app retries bị chặn hoặc partial asset bị dùng nhầm | M | M | Mobile + Backend + Infra | Durable `core.upload_sessions`/`core.upload_parts`, 4 MiB object PutObject chunks, byte/request/session caps, checksum/AV gate, final low-level PutObject; OI-18 POC trước tích hợp |
| R-26 | Teacher Deck bỏ sót activity hoặc SVG Guide draft không rõ/không phù hợp độ tuổi, unsafe hay bị giữ lâu hơn dự kiến | M | H | AI lead + Teacher/Parent Product/Design + Privacy | Catalog/structured-vector contract, adaptive 4–8 ordered steps, line-art/media/malware/age-safety checks, adult/Teacher review, automated safety, private temporary asset expiry/cleanup, separate cost/rate caps, synthetic quality/license/render/cost POC OI-19; không dùng child profile/artwork làm input |

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
| FR-P-05 | M | BR-08/55 | UC-02/16 | learning_content.record/version/review/receipt | Parent must choose one catalog-first main activity before story using accessible published/shared lesson activities and exact pinned version where applicable. A replacement request excludes shown/rejected choices. After video, no-pin returns the run-pinned activity without catalog lookup; a lesson pin returns all exact-version activities with the main one marked. API/UI/recovery proof remains a design input. AC-05/52/Rev66. | P1 | DRAFT; target behavior selected; not signed off |
| FR-P-06 | M | BR-19/21 | UC-02/16 | parent.profile_revisions/context_entries; story.run_inputs; story.review_decisions | Snapshot API rejects unapproved context; pins selected profile revision and context hash on the immutable run-input revision. AC-08. | P1 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-P-07 | M | BR-13/14 | UC-02/16 | story.story_revisions; story.story_scenes; story.review_decisions; ai_jobs.job | Three rewrites accepted, fourth denied; no direct scene-edit endpoint. AC-06. | P1 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-P-08 | M | BR-14/15 | UC-02/16 | story.runs; story.story_revisions; story.review_decisions; story.video_generations | Script confirmation gate and playback after safety; verify 168h closeout/no video approval. AC-06/07/22. | P1 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-P-09 | M | BR-16/17 | UC-02/16 | story.runs; story.video_generations; story.review_decisions; core.asset_metadata | Suitability flow hides old output on accepted replacement; enforce 1+2 cap and ledger. AC-07/23. | P1 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-P-10 | S | NFR-13/21 | UC-02/16 | story.runs; ai_jobs.job/job_events; client error-state presentation | Localized walkthrough for stages, safe errors, retryability and no provider diagnostics. AC-20/22. | P1 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-P-11 | S | Q146; BR-46 | UC-02/16 | Parent UI/API; ai_jobs.job; core_asset_metadata/asset_lineage; ai_policy.resource_reservation/resource_event | Verify 4–8-step SVG guide catalog-first/draft policy; request, skip, source/worker/timeout/quality failure all reach mandatory image capture; topic-only input, no child-data egress, private expiry/provenance and no video quota. AC-44/45/Rev66. | P1 | DRAFT; model/license/cost and retention gates remain open |
| FR-T-01 | M | Owner scope for Teacher Web; §16 | UC-05 | apps/teacher-ui; versioned API contract; no persistent table | Web route walkthrough in supported browsers; verify no Parent/collaboration UI coupling. AC-03/30. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-02 | M | BR-04/05 | UC-03/06/12 | be1.organizations/classrooms/enrollments/organization_assignments; billing.capacity_periods | BE1 authorization/concurrency checks for capacity, roster and one responsible Teacher. AC-14/25. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-03 | M | BR-04 | UC-06/08 | billing.price_versions/organization_subscriptions/capacity_periods; be1.classrooms | Billing fixture: ten included slots plus add-ons; concurrent creation cannot exceed capacity. AC-14. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-04 | M | BR-07 | UC-03 | be1.managed_profiles; be1.profile_revisions; be1.profile_context_entries | Profile API: duplicate display names succeed with distinct IDs and immutable revisions. AC-16. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-05 | M | BR-05 | UC-03/06 | be1.managed_profiles; be1.enrollments | Enrollment constraint: one active class/profile; move closes prior enrollment exactly once. AC-03/25. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-06 | M | BR-22 | UC-04 | lesson.source_documents; core.upload_sessions/parts; core.asset_metadata | Parser fixtures for format/size/page/password/scan; assert no OCR call. AC-16/29. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-07 | M | BR-22 | UC-04 | lesson.source_documents; lesson.document_revisions; core.asset_metadata | Original asset immutable; edited extraction creates a new revision and review state. AC-16. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-08 | M | BR-09/10 | UC-04/05 | lesson.occurrences; lesson.plan_revisions; lesson.plan_activities | Occurrence workflow: multi-activity plan supported; child selection blocked before approval. AC-16. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-09 | M | BR-08 | UC-04/05/14 | lesson.plan_revisions; lesson.plan_activities | Custom activity without Teacher safety checklist cannot pass plan or create run. AC-05/16. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-10 | M | BR-01/09/21 | UC-05 | be1.enrollments/managed_profiles/profile_revisions; lesson.plan_activities; story.runs/run_inputs | GWT verifies the system randomly selects from the owner-approved eligible set, Teacher confirms child/context, and the run input pins one activity and context snapshot; policy details remain OPEN under Q-01. AC-02/08. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-11 | M | Q05/Q82 | UC-05 | apps/teacher-ui; core.upload_sessions/parts; core.asset_metadata | Camera permission and phone-upload fallback; both attach one validated artwork. AC-20/29. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-12 | M | BR-13/15 | UC-05/16 | lesson.plan_revisions/plan_activities; story.story_revisions/review_decisions/runs | Plan direction pinned; enforce 1+3 script revisions and script confirmation hash. AC-06/08. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-13 | M | BR-10/17 | UC-05/16 | lesson.occurrences; story.runs; story.video_generations | Occurrence-claim concurrency: playable safe output claims once; pre-claim failure leaves slot open. AC-04; AT-01. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-14 | M | BR-06; Q130 | UC-12 | be1.organization_assignments/classrooms; story.runs; core.audit_events | Saga fault injection: old fence, Story lock receipt, BE1 finalize/compensation, job completion and conflict. AC-25/31; AT-12. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-15 | S | BR-39 | UC-05/11 | lesson.occurrences; story.runs/video_generations; notifications.inbox_items | Occurrence projection walkthrough and fake-clock closeout; confirm one sample/no batch action. AC-18/22. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-16 | M | BR-37 | UC-05/15 | lesson.occurrences projection confirmation; story.video_generations; core.audit_events; ephemeral playback authorization | Playback capability denied before confirmation, after assignment revoke and after token expiry. AC-18. | P2 | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |
| FR-T-17 | M | BR-41; Q134 | UC-12 | be1.organization_assignments; story.runs; core.audit_events; billing.video_quota_usage; lesson.occurrences | Emergency authorization/reason, metadata-only audit, no admin media access, quota/sample retained. AC-25/31. | P2 | DRAFT; quyết định nghiệp vụ đã chốt; chưa sign-off |
| FR-T-18 | M | Q137–Q140; BR-42/43 | UC-17 | lesson.sketch_deck_revisions/steps; lesson.plan_revisions/activities; core.asset_metadata/lineage | Verify all approved activities are covered with adaptive 4–8 progressive drawing steps, age/layout metadata, lineage and no child refs. SVG catalog/engine target remains unimplemented absent source/runtime evidence. AC-34/Rev66. | P2 | DRAFT; model/chất lượng còn là cổng |
| FR-T-19 | M | Q140/Q142; BR-43 | UC-17 | Teacher presentation client; lesson presentation revision/media refs; occurrence video playback API | Verify slide text editing, add/remove/reorder, attach/reposition uploaded image, approved SVG or validated YouTube/Vimeo embed, preview/review/present. Slide CRUD/persistence API and DTR mapping remain open. AC-35/Rev66. | P2 | DRAFT; implementation contract not signed off |
| FR-T-20 | M | Q139/Q142/Q143; BR-43/44 | UC-17 | lesson.presentation_revisions; ai_jobs.job; ai_policy.resource_reservation; không ghi Billing quota | Verify lesson/guide/media revision/hash pinning, dependent STALE behavior, separate sketch/visual caps and no video quota. Exact aggregate ownership and transitions require DTR/API reconciliation. AC-35; AT-16/Rev66. | P2 | DRAFT; ngưỡng số còn chờ benchmark |
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
| FR-AI-15 | S | Q146; BR-36/44/46 | UC-02/16 | ai_jobs.job/attempt/events; core_asset_metadata/asset_lineage; ai_policy.resource_reservation/resource_event | Verify generic topic/difficulty, adaptive 4–8 SVG steps, no child-data egress, deterministic safety/provenance/expiry and separate cap; no-source/disabled/unavailable/timeout/quality-reject stays nonblocking to capture. AC-44/45/AT-18/Rev66. | P1 | DRAFT; model/license/cost and exact retention remain open gates |
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
| FR-B-13 | S | Q120/Q193 | UC-10 | billing.invoices/payment_attempts/provider_event_receipts/video_quota_grants | Nếu owner bật purchase offer: payment callback to invoice/grant GWT; unverified event and duplicate top-up create no second grant. Actor/scope policy remains OPEN. AC-17/14. | P3; quota admission foundation in P0 | DRAFT; purchase policy còn mở; cổng tích hợp còn mở |
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
| NFR-16 | M | Q79/Q84; bảo toàn dữ liệu nguồn và migration theo pha | UC-01–UC-17; migration xuyên hệ thống | 89 source mappings after Rev31; 38 retained/refactored, 54 new, 92 active, 48 legacy, 140 projected physical; 5 fixtures excluded; DATA_TABLE_REGISTER | Migration rehearsal inventory, row parity, source-to-target crosswalk and restore evidence before cutover. Historical v2.3 baseline is 89 active/137 physical; neither count is a live DB inventory. AC-09/12. | P4 | PROPOSED/GATE; chưa sign-off tài liệu |
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
| FR-PL-03 | M | Q152/Q189; BR-50 | §31.2, reuse/remix | lesson.library_items/library_versions; lesson.occurrences; lesson.version_activities | Pin version per use; Parent copy is reusable PRIVATE with lineage and leaves source/old occurrence unchanged. AC-47/59. | P0 platform foundation | DRAFT; editable-field allowlist and post-recovery retention open |
| FR-PL-04 | M | Q155/Q171/Q174/Q177; BR-51 | §31.2, discovery and use | lesson.library_items/library_versions/access_grants | Public search returns only published PUBLIC; authorized school/group/invite scopes work; denied scopes reveal no content. AC-48/59/63. | P0 platform foundation | DRAFT; chưa sign-off |
| FR-PL-05 | M | Q160–Q163/Q172/Q175; BR-51 | §31.2, publication/moderation | lesson.access_grants; lesson.library_versions | School Manager approves Teacher PUBLIC; independent Platform Admin with Content Admin permission approves Platform Admin-authored PUBLIC; hide/unpublish revokes access but preserves metadata. AC-48/60. | P0 platform foundation | DRAFT; technical review/publish evidence open |
| FR-PL-06 | M | Q162/Q163/Q170/Q176; BR-58 | §31.2–31.3, lesson audience | lesson.access_grants; be1.parent_groups/parent_group_members | Group and named invitation grants are limited to accepted members and stop after revocation. AC-46/57/63. | P0 platform foundation | DRAFT; chưa sign-off |
| FR-PL-07 | M | Q150/Q176; BR-48 | §31.3, profile share lifecycle | parent.profile_share_grants; parent.child_profiles; be1.managed_profiles | Pending invitation grants no access; named Teacher acceptance activates a 90-day scoped link; Parent retains ownership and can revoke. AC-49/57. | P0 platform foundation | DRAFT; exact field list/physical owner open |
| FR-PL-08 | M | Q150/Q151/Q176; NFR-34/36 | §31.3, least-privilege share | parent.profile_share_grants; profile revisions; API/token/job authorization | Resolve only granted fields; immediate revoke blocks new reads, tokens/caches and not-yet-accepted jobs; recipient is an occurrence snapshot. AC-49/57/64. | P0 platform foundation | DRAFT; field schema and implementation gates open |
| FR-PL-09 | M | Q157/Q158/Q164; BR-52 | §31.4, Teacher authoring | lesson.source_documents/document_revisions; structured lesson form | Template contract covers topic, age, objectives, drawing, knowledge, activities/materials/steps/safety and optional script. AC-50. | P0 platform foundation | DRAFT; format review pending |
| FR-PL-10 | M | Q157/Q164/Q165; NFR-35 | §31.4, upload filter | lesson.source_documents; core asset hash/lineage; parser/filter version | Verify raw file/full text/images/metadata do not reach model input or telemetry; only allowlisted fields proceed. AC-50. | P0 platform foundation | DRAFT; parser/AV implementation gate |
| FR-PL-11 | M | Q157/Q164; BR-52 | §31.4, human extraction review | lesson.document_revisions; structured draft | Teacher preview/correction is required before AI request; parser uncertainty returns a repairable result. AC-50. | P0 platform foundation | DRAFT; chưa sign-off |
| FR-PL-12 | M | Q158/Q159; BR-53 | §31.4, AI draft boundary | lesson.library_versions; ai_jobs.job; access/review state | Confirm every AI output is DRAFT and cannot publish/show without authorized human review. AC-51. | P0 platform foundation | DRAFT; initiating roles resolved; runtime/persistence gates pending |
| FR-PL-13 | M | Q155/Q156; BR-50 | §31.2, lesson content | lesson.library_versions/version_activities | Validate drawing guidance, subject knowledge and multiple activity records with material/instruction/note fields. AC-47/52. | P0 platform foundation | DRAFT; chưa sign-off |
| FR-PL-14 | M | Q158/Q169; NFR-37 | §31.2/31.4, visuals/slides | lesson.version_visual_assets; core.asset_lineage; ai_jobs.job | Generated activity/topic visuals and slide assets are versioned derived outputs with safety/review/provenance; source lesson and child artwork are not replaced. AC-51/65. | P0 platform foundation | DRAFT; provider/ownership open |
| FR-PL-15 | M | Q167; BR-54 | §31.5, active-session option | lesson.sketch_deck_revisions/steps; ai_jobs.job; Parent temporary asset | Toggle on may create guide; toggle off creates no job, asset or quota event. AC-44/45/53. | P0 platform foundation | DRAFT; model/license/cost open |
| FR-PL-16 | M | Q151/Q155; BR-55/Rev66 | §5.1/31.5/31.17, Parent sequence | story.runs/run_inputs; lesson.version_activities; video generation/playback | Walk through optional topic/lesson/guide, mandatory capture and VLM review, select one main activity before script, then preserve the video/safety pipeline. No-pin playback returns the run-pinned activity; lesson pin returns all activities from the exact version with the selected activity marked. AC-52/Rev66. | P0 platform foundation | DRAFT; API/snapshot/recovery remain open |
| FR-PL-17 | M | Q168/Q186/Q189/Q191; BR-56 | §31.2/31.5, optional script direction | lesson.library_versions; story revisions/review decisions | Parent keeps preset script direction; Teacher keeps approved objective/activity/safety; adult confirms final revision; each output remains a new child-specific video. AC-54/59/65. | P0 platform foundation | DRAFT; default/override limits open |
| FR-PL-18 | M | Q184–Q187/Q191; BR-56 | §31.5, personalized video | story.run_inputs; story.video_generations/scenes; core asset lineage | Assert source drawing/profile belong to the selected child and each generation is new; reject cross-child video reuse. AC-54/56/65. | P0 platform foundation | DRAFT; current pipeline preserved |
| FR-PL-19 | M | Q190; BR-56 | §31.5, subject correction | story.understanding_revisions; story.review_decisions; ai_jobs.job | Wrong subject requires adult confirm/correct; new suggestion pins corrected revision and original image hash. AC-55. | P0 platform foundation | DRAFT; chưa sign-off |
| FR-PL-20 | M | Q185; BR-10/56; Q-01 | §5.2/31.5, Teacher sample | lesson.occurrences; lesson.delivery_recipients; story.runs | Equal-probability selection, Teacher confirmation, one stale-candidate reselect, empty-set stop and no pre-confirmation admission; one successful sample per occurrence. AC-56. | P0 platform foundation | DRAFT; exact eligibility/evidence/concurrency/error contract open |
| FR-PL-21 | M | Q178/Q179/Q183; BR-58 | §31.6, Parent history | lesson.delivery_recipients; parent.profile_share_grants | Parent sees linked child deliveries for 30 days from first delivery/open, subject to active scope; revoke/unpublish retains neutral metadata only. AC-57/60. | P0 platform foundation | DRAFT; storage/access implementation gate open |
| FR-PL-22 | M | Q180–Q182; BR-59 | §31.6, feedback | lesson.delivery_feedback/feedback_replies; organization ref | Parent submits lesson feedback; Teacher/Manager/Admin replies remain in school scope; no chat, completion mark or image attachment. AC-58. | P0 platform foundation | DRAFT; chưa sign-off |
| FR-PL-23 | M | Q162/Q170; BR-58 | §31.2–31.3, groups and recipients | be1.parent_groups/parent_group_members; lesson.access_grants | Group and named-recipient access are invite-based, membership-checked and revocable. AC-46/57/63. | P0 platform foundation | DRAFT; membership invitation policy open |
| FR-PL-24 | M | Q193 clarified by Rev52/D-146; BR-60 | §31.7, product quota | billing.video_quota_grants/video_quota_usage; ai_policy.resource_reservation | Parent and School scopes are separate; Teacher debits occurrence school scope; no Teacher pool/fallback; included then FIFO top-up; included expires end-of-month and top-up carries forward per BR-38; temporary review units/prices are in §31.7. AC-61. | P0 platform foundation | DRAFT; production price, buyer/allocator, payment/exhaustion and terminal top-up expiry open |
| FR-PL-25 | M | Q153/Q154; BR-57; O-16 | §31.1/31.8/31.10(16), age/personalization | parent.profile_revisions; be1.profile_revisions; age-band catalog; story.runs | Accept 36–120 months and use versioned bands 36–71, 72–107 and 108–120. Profiles aged 121–155 months cannot start a new accept/run; a run accepted before age 121 may complete under its accepted eligibility snapshot and existing authorization, safety and lifecycle controls. Legacy draft remains read/delete only; notify once on detection and once on opening. AC-62/65/66. | P0 platform foundation | DRAFT; policy selected; migration mapping and edit/archive policy open |

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
| BR-08 | Q08/Q32/Q85 activity source | FR-P-05; FR-T-09 | UC-05/14 | learning_content.records/versions; lesson.plan_activities | AC-05 |
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
| BR-42 | Q137/Q141/Q146/Q167/Rev66: Parent topic/lesson/guide đều tùy chọn trước capture; ảnh bắt buộc và chủ thể được review sau capture, đối chiếu với topic/lesson đã chọn. Teacher guide/deck gắn với plan đã duyệt; guide chỉ tạo khi được yêu cầu. Cả hai role dùng guide progressive adaptive 4–8 bước. | FR-P-02/04/11/12/13; FR-T-18/20; FR-AI-14/15 | UC-02/17 | Parent guide, Teacher lesson/guide revisions, AI jobs và vector assets; mapping vật lý còn mở | AC-33/44/45; AT-14/15/18/19; Rev66 |
| BR-43 | Q138–Q140/Q142/Q167/Rev66: Teacher điều khiển presentation theo lesson/plan revision; slide có text và media được sắp xếp (ảnh upload, SVG, video YouTube/Vimeo embed). Guide tiến dần từ nét cơ bản đến hình nhận biết trong 4–8 bước; sửa nguồn làm nội dung phụ thuộc stale. | FR-T-18–21; FR-AI-14; NFR-33/37 | UC-17 | Lesson presentation/guide revisions, plan activities, asset metadata/lineage; exact DTR/DDL mapping còn mở | AC-34/35; AT-15/16; Rev66 |
| BR-44 | Q143/Q146/Rev66: Guide/vector visual có rate và compute cap riêng, không dùng video quota; guide không nhận profile, tuổi chính xác, ảnh, giọng nói hoặc định danh trẻ. Mức cap phải qua benchmark/cấu hình. | FR-P-11; FR-T-20/22; FR-AI-14/15; NFR-25 | UC-02/16/17 | AI Policy reservation/events, lesson presentation/guide revisions và vector assets; không ghi billing.video_quota_usage; mapping vật lý còn mở | AC-35/44/45; AT-16/18/19; Rev66 |
| BR-45 | Q144: pipeline VLM → story/storyboard → Character Bible → LTX → consistency → FFmpeg/TTS → safety → playback đã được chủ sở hữu chỉ định; Rev66 giữ nguyên video pipeline cá nhân hóa theo tranh trẻ. | FR-AI-01/04–09/13; NFR-19/23/25 | UC-02/05/16 | story.understanding_revisions/story_revisions/story_scenes/video_generations/video_generation_scenes; ai_jobs; core.asset_metadata/lineage | AC-36/37; AT-17; Rev66 |
| BR-46 | Q146/Rev66 (supersedes text-only Q145): Parent có thể yêu cầu hoặc bỏ qua SVG guide 4–8 bước progressive; ưu tiên catalog SVG đã duyệt, chỉ tạo Qwen structured-vector draft khi thiếu nguồn và capability bật. Không dùng FLUX/fallback; không gửi dữ liệu trẻ; output private có provenance/lifecycle và sketch-only cap. Mọi lỗi/skip không chặn capture bắt buộc. | FR-P-11/FR-AI-15 | UC-02/16 | AI jobs, vector asset lineage, AI Policy reservation/events; không ghi billing.video_quota_usage; mapping vật lý còn mở | AC-44/45; AT-18/19; Rev66 |

| BR-47 | Q147; additive platform layer preserves the existing Parent/Teacher flows and video pipeline | FR-PL-16/18; NFR-34/38 | §31.1/31.5 | Parent/Teacher run and video owners; lesson delivery | AC-52/54/56 |
| BR-48 | Q148/Q150/Q151/Q176; separate accounts with invited, consented, scoped and revocable child-profile grant | FR-PL-07/08; NFR-34/36 | §31.3 | parent.profile_share_grants; Parent and Teacher profile owners | AC-46/49/57/64 |
| BR-49 | Q149; one school per organization and no cross-tenant disclosure | FR-PL-02/23; NFR-34/36 | §31.3 | be1.organizations; lesson.access_grants; feedback/quota scope | AC-46/57/63 |
| BR-50 | Q152/Q155/Q156/Q189; reusable immutable version differs from occurrence; AI reuse edits create draft/copy | FR-PL-03/13; NFR-37 | §31.2 | lesson.library_items/library_versions/version_activities; occurrences | AC-47/52/59 |
| BR-51 | Q155/Q160–Q163/Q171–Q175; visibility and Manager gate before Teacher PUBLIC; Admin moderation; preserve on unpublish | FR-PL-04/05/06; NFR-34/37 | §31.2/31.3 | lesson.library_versions/access_grants; school tenant | AC-48/60/63 |
| BR-52 | Q157/Q164/Q165; filter uploads to reviewed allowlisted fields before AI | FR-PL-09/10/11; NFR-35 | §31.4 | lesson.source_documents/document_revisions; parser/filter; ai_jobs | AC-50 |
| BR-53 | Q158/Q159; AI-authored lesson/activity/visual remains a draft until authorized review | FR-PL-12/14; NFR-35/37 | §31.4 | lesson.library_versions/version_visual_assets; ai_jobs.job | AC-51 |
| BR-54 | Q167/Rev66; Parent/Teacher guide or AI visual generation runs only after an adult explicitly requests it; disabled/skipped guide creates no job. Parent guide is optional within the session and never blocks mandatory capture. | FR-P-11; FR-T-18/22; FR-PL-15; NFR-34 | §31.5/31.17 | Parent temporary guide asset; Teacher lesson/guide revisions; AI jobs | AC-44/45/53; Rev66 |
| BR-55 | Q151/Q155/Rev66; Parent phải chọn một activity chính catalog-first sau khi VLM subject được người lớn xác nhận; lesson pin/source rules giữ nguyên và activity được chọn là story context. Candidate thay thế loại các lựa chọn đã hiển thị/từ chối. Sau video no-pin trả activity chính đã pin vào run; lesson pin trả toàn bộ activities exact version và đánh dấu activity chính. | FR-P-05/FR-P-13/FR-PL-16 | §5.1/31.5/31.17 | story activity snapshot; lesson.version_activities; Parent suggestions | AC-05/52/Rev66 |
| BR-56 | Q168/Q184–Q191; each video is new for the child drawing; script direction is optional; adult confirms subject mismatch | FR-PL-17/18/19; NFR-37/38 | §31.5 | story.run_inputs/understanding_revisions/video_generations; lesson.library_versions | AC-54/55/65 |
| BR-57 | Q153/Q154; age scope is 36–120 months with versioned bands 36–71, 72–107 and 108–120; legacy profiles cannot start new runs, while a run accepted before age 121 may complete under its accepted eligibility snapshot and existing authorization/safety/lifecycle gates | FR-PL-25; NFR-38 | §31.1/31.10(16) | Parent/Teacher profile revisions; age-band catalog; StoryRun | AC-62/65/66 |
| BR-58 | Q162/Q170; lesson grants can target Parent groups or named invitees and can be revoked | FR-PL-06/23; NFR-34 | §31.2/31.3 | be1.parent_groups/parent_group_members; lesson.access_grants | AC-46/57/63 |
| BR-59 | Q178–Q182; Parent feedback has no chat/media upload and stays within the school thread | FR-PL-21/22; NFR-34/36 | §31.6 | lesson.delivery_recipients/delivery_feedback/feedback_replies | AC-57/58 |
| BR-60 | Q193 clarified by Rev52/D-146; Billing owns school organization and Parent account quota; Teacher usage debits school quota, AI Policy owns compute only | FR-PL-24; NFR-34 | §31.7 | billing.video_quota_grants/video_quota_usage; ai_policy.resource_reservation | AC-61 |

<a id="srs-31"></a>
## 31. Nền tảng giáo án, chia sẻ và tích hợp luồng hiện hữu

### 31.1 Thứ tự ưu tiên và phạm vi thay đổi

Đây là lớp nền tảng bổ sung vào baseline sản phẩm Sketch2Life. Các yêu cầu đích Parent Android, Teacher web, chụp tranh, pipeline story/video, quota, safety, lifecycle và vận hành trong §§1–30 tiếp tục áp dụng trừ các điểm được liệt kê rõ dưới đây. Đây là baseline yêu cầu, không khẳng định các flow đã hoàn tất trong code hiện tại. Không thay thế toàn bộ SRS hoặc xóa history.

Phần này là nguồn chuẩn v2.3 cho các điểm đã thay đổi: age scope 36–120 tháng thay cho 36–155 tháng; Teacher Sketch Deck và Parent Guide đều opt-in theo session; reusable lesson tách với occurrence; Parent hiển thị outdoor activities sau video; Parent/Teacher profile vẫn tách owner nhưng có grant chia sẻ; và hệ thống có role Platform Admin/School Manager. Các câu/ma trận v2.2 mâu thuẫn với các điểm này được xem là history và nhường cho yêu cầu có ID tại §31.8–§31.11.

Không khóa stack production, giá, quota thương mại hoặc schema triển khai trong phần này. Theo ghi nhận lịch sử ngày 2026-11-06, FLUX.3 từng là hướng phát triển line-sketch/lesson visuals; chủ sở hữu thay thế hướng này tại Rev66 bằng SVG catalog + deterministic vector engine. Qwen structured vector draft chỉ dùng khi capability được bật. Presenton vẫn là ứng viên lịch sử cho bố cục slide. Checkpoint, license review, safety, chi phí và kết nối backend còn cần xác minh. Toàn bộ phần này vẫn là draft; Plan Rev25 chỉ duyệt sửa tài liệu, không duyệt product code hay migration.

### 31.2 Mô hình lesson reusable và occurrence

Lesson library là nguồn nội dung có version, có thể chứa:

- Chủ đề, mục tiêu học tập, nhóm tuổi mục tiêu và ghi chú Montessori.
- Hướng dẫn trẻ vẽ chủ thể, các nét chính/đặc điểm cần quan sát và thông tin giúp trẻ hiểu con vật/đồ vật/chủ đề đó.
- Một hoặc nhiều outdoor activities; mỗi mục nêu vật liệu, cách chuẩn bị, các bước thực hiện, mục tiêu quan sát và lưu ý an toàn.
- Video script direction có thể bật/tắt theo lesson hoặc lần dùng; khi bật, script là hướng dẫn nội dung, không buộc video hai trẻ giống hệt.
- Nội dung canonical của lesson là chữ có cấu trúc. Visual assets/slide do AI tạo là lựa chọn riêng, có version, provenance và review; chúng minh họa lesson/activity hoặc session, không thay thế văn bản nguồn và không bao giờ thay ảnh tranh trẻ dùng cho video.

Reusable lesson version độc lập với lesson occurrence của một lớp/buổi. Teacher hoặc Parent dùng lesson như preset; occurrence, plan revision và StoryRun dùng cùng optional typed `LessonVersionRefV1` với version và content hash chính xác trong contract/snapshot khi preset được chọn. Teacher StoryRun pin tiếp đúng lesson version/hash và approved plan revision/hash; Parent StoryRun cũng pin version/hash khi dùng preset. Khi không dùng lesson, các ref vắng mặt; không phân giải `latest`, không retarget occurrence/run cũ. Điểm lưu vật lý và constraint cụ thể chờ DDL được duyệt. Platform Admin và Teacher được khởi tạo AI đề xuất chỉnh sửa; Parent chỉ được sửa draft/personal copy đã được cấp quyền, không tự khởi tạo suggestion mới. Mọi chỉnh sửa tạo draft/version/copy có lineage và cần người có quyền review; không sửa ngược source version đã publish hay làm thay đổi occurrence/run cũ. Parent personal copy là reusable và PRIVATE, giữ source-version lineage; request xóa có 30 ngày recovery. Field allowlist, physical owner và retention sau recovery còn mở tại §31.10(12).

Visibility của lesson là PRIVATE, SCHOOL, SELECTED_AUDIENCE hoặc PUBLIC. Teacher lesson mặc định thuộc trường. SCHOOL chỉ xem trong organization sở hữu; SELECTED_AUDIENCE cấp quyền cho nhóm Parent hoặc người được mời; PUBLIC có thể tìm kiếm và dùng trên toàn nền tảng. Teacher lesson chỉ chuyển PUBLIC sau khi School Manager duyệt. Public lesson do Platform Admin author chỉ được publish sau khi một Platform Admin khác có Content Admin permission review độc lập. Platform Admin có thể hide/disable nội dung theo quyền nền tảng. Lesson public có thể được dùng và remix; remix luôn tạo item/version nguồn mới có provenance đến lesson gốc. Khi unpublish/revoke, giữ metadata/history trung tính nhưng thu hồi quyền truy cập thư viện; content chỉ mở lại sau khi public lại hoặc cấp grant mới.

Khi một lesson đã được dùng rồi bị unpublish, giữ lesson version, occurrence và lịch sử sử dụng. Bỏ quyền tìm/tải/mở lesson content từ library; Parent chỉ truy cập lại lesson content khi lesson được public lại hoặc được chia sẻ lại bằng grant hợp lệ. Lịch sử delivery không tự khôi phục quyền thư viện.

### 31.3 Roles, tenant và profile sharing

| Role | Phạm vi |
|---|---|
| Platform Admin | Toàn nền tảng; cấu hình policy/role/quota, tạo nội dung public, moderation/hide theo permission, xem và trả lời feedback thuộc trường theo audit. Public lesson do Platform Admin author cần một Platform Admin khác có Content Admin permission review độc lập trước khi publish. Child-media access mặc định bị từ chối. |
| School Manager | Một organization tương ứng một trường; quản lý Teacher/Parent groups và quota school, duyệt Teacher-authored public lesson, xem/duyệt lesson và feedback trong trường. Teacher-authored PUBLIC cần School Manager approval. Không mặc nhiên có quyền xem ảnh/video trẻ. |
| Teacher | Lớp/profile được phân công trong trường; tạo/sửa lesson; dùng lesson preset; nhập lesson qua template/form; bật/tắt sketch trong session; tạo video mẫu cho một child/run. |
| Parent | Tài khoản Parent riêng; sở hữu child profile; có thể cấp/revoke profile share tới Teacher được nêu tên; dùng lesson PUBLIC/được cấp; xem lesson đã dạy theo profile share; tạo video mới cho con; gửi lesson feedback. Gói quota Parent được ghi là giả định tạm ở §31.7, chưa phải giá production. |

Permission rà soát/publish/moderate nội dung catalog/lesson được quản lý trong policy của Platform Admin; “Admin nội dung” không phải product role hay principal đăng nhập riêng. Permission đó không bao hàm quyền child profile/media. Trong phạm vi SRS hiện tại, nhãn lịch sử “Organization Admin/admin tổ chức” cho quản trị tenant được chuẩn hóa thành School Manager của organization sở hữu resource; đây là thống nhất tên role, không chốt cách lưu identity/assignment, permission grant, scope resolver hoặc revoke/audit mapping.

Mỗi trường là một organization/tenant. Organization boundary bắt buộc cho lesson SCHOOL, SELECTED, occurrence, Parent groups, feedback, quota và audit. Admin toàn nền tảng có thể moderate nhưng vai trò Manager/Teacher/Parent không vượt tenant.

Parent và Teacher không dùng chung account và không chuyển quyền sở hữu profile. Parent profile có thể có 0..n share grants; mỗi grant liên kết đúng một opaque Managed Profile reference, và mỗi Managed Profile có tối đa một Parent link đang active. Parent mời Teacher được nêu tên; grant ở `INVITED` chưa cấp quyền, Teacher invitee phải chấp nhận trước khi grant `ACTIVE`. Grant có thời hạn 90 ngày; Parent revoke có hiệu lực tức thì với lần đọc mới, token/cache/API và job chưa accepted. Delivery Recipient là snapshot của occurrence, không phải một Parent profile/Managed Profile link mới. Story run đã accepted giữ input snapshot đã được người lớn duyệt theo lifecycle hiện có. Cross-owner ref vẫn là typed opaque reference, không dùng name-based matching hoặc SQL FK xuyên owner. Exact field allowlist, physical owner/schema, consent artifact, renewal và xử lý school-wide/class invitation vẫn OPEN.

| Resource/action | Parent | Teacher | School Manager | Platform Admin |
|---|---|---|---|---|
| Profile | Owner; cấp consent, gửi invitation và revoke grant | Chỉ field được grant sau khi Teacher chấp nhận invitation và lớp được phân công | Không đọc profile contents mặc định | Role không cấp quyền đọc profile/media; mặc định deny tới khi có quy trình được owner duyệt |
| School lesson | Dùng khi school/group/invite grant active | Tạo/sửa lesson của trường | Xem/feedback; approve Teacher public publication | Moderation/hide, platform-wide |
| Public lesson | Tìm/dùng/download theo capability | Dùng/remix hoặc tạo own version | Duyệt Teacher publication | Author; independent review before publish; moderate |
| Occurrence and child media | Chỉ child/run của mình | Chỉ assigned child/run, grant còn hiệu lực | Deny | Deny-by-default; chưa có permission workflow được duyệt |
| Emergency force-close conflicting Teacher run | Không được cấp trong SRS hiện tại | Không được cấp trong SRS hiện tại | School Manager của organization sở hữu lớp/run là actor đích cho command tường minh; cách cấp/lưu permission và resolver còn OPEN | Platform Admin (Content Admin permission) không được cấp qua permission nội dung; child media vẫn deny |
| Lesson feedback | Tạo và xem thread của mình | Xem/reply nếu thuộc occurrence/lớp được giao | Xem/reply trong school tenant | Xem/reply; output chỉ thuộc school thread |
| Quota | Xem Parent-account usage; quyền mua package/top-up OPEN | Dùng quota school của occurrence; không có Teacher-account pool | Xem/administrate school usage theo grant; quyền mua/cấp/phân bổ OPEN | Quản lý policy; không được suy từ role policy sang quyền đọc child media |

Permission checks chạy server-side cho mọi resource operation. Mất assignment, revoke share, unpublish/hide hoặc rời organization phải invalidate grant/cache/download/playback capability liên quan; không suy quyền từ UI role claim.


#### Mapping logic và quyết định chia sẻ hồ sơ

| Concept | Canonical owner | Logical reference | Cardinality/optionality | Authorization and history |
|---|---|---|---|---|
| Parent Child Profile | Parent profile domain | Parent-owned profile reference | Một Parent profile có 0..n grants; link sang School Managed Profile là optional. | Parent là owner; không hợp nhất với School Managed Profile. |
| School Managed Profile | BE1/School tenant | Opaque school-managed profile reference trong organization scope | Mỗi Managed Profile có tối đa một Parent link active; enrollment/Teacher assignment theo bất biến BE1 hiện có. | Roster access cần role, organization, class assignment và active link/grant. |
| Delivery Recipient | Lesson delivery domain | Opaque recipient reference kết hợp với tenant/occurrence contract | Recipient là occurrence-level snapshot; không dùng thay Parent/Managed Profile link. | History giữ snapshot metadata; content access vẫn bị giới hạn bởi grant đang hiệu lực. |
| Profile Share Grant / Invitation | Grant owner chưa được xác định physical | Versioned opaque grant reference; sender/recipient/purpose/scope đi qua contract | Mỗi grant trỏ tới đúng một Managed Profile; named Teacher phải accept; term là 90 ngày. | Parent revoke tức thì; revoke chặn read/token mới và job chưa accepted. Physical schema, allowlist, renewal và school-wide/class acceptance còn OPEN. |

Không match theo tên, ngày sinh hoặc thuộc tính gần đúng. Trước khi tạo logical link, application phải kiểm tra invitation/grant version, tenant, recipient principal đã xác thực, purpose, field scope và consent theo policy đã chọn. Màn hình chỉ liệt kê link đã được xác thực. Mọi link liên-owner là opaque typed reference/version qua port; cấm SQL FK xuyên owner. Field allowlist, school-wide/class acceptance, renewal, revoke race, retained-history behavior và physical mapping tiếp tục là cổng technical review tại §31.10/§31.10.2.

### 31.4 Authoring, upload filtering và AI assistance

Teacher authoring có structured form và standardized lesson-document template. Template nêu rõ topic, age band, objectives, drawing steps, subject knowledge, activities, materials, instructions, safety notes và optional script direction. Giữ giới hạn upload v2.2 (PDF/PPTX/DOCX tối đa 25 MB/100 trang, không OCR scan, từ chối file encrypted/password-protected) cho tới khi có quyết định mới.

Upload đi qua quarantine/AV, parser và deterministic field mapper. Raw file gốc cùng hash/provenance được giữ riêng tư trong organization. Chỉ các field allowlist đã parse, validate, Teacher preview và Teacher sửa/xác nhận mới có thể tạo structured input cho AI. Không gửi nguyên giáo án, full extracted text, embedded image, metadata cá nhân hay file gốc sang AI. Parser/filter/validation chưa đạt thì dừng và trả lỗi có thể sửa; không âm thầm gửi raw document.

AI hỗ trợ tạo lesson/activity/plan chỉ tạo draft; một người có quyền phải kiểm tra, sửa và publish. Có thể dùng AI để bổ sung outdoor activity khi catalog chưa đủ; mỗi đề xuất phải kèm mục tiêu, vật liệu, chuẩn bị, hướng dẫn từng bước và safety notes. Visual/slide generation là job riêng, optional, có review/provenance/safety. Theo Q159, Platform Admin và Teacher được khởi tạo AI lesson/activity suggestion; Parent chỉ được chỉnh sửa draft được cấp quyền, không khởi tạo suggestion mới và không publish source version. Quy tắc này áp dụng cả khi reuse lesson: Platform Admin/Teacher khởi tạo đề xuất chỉnh sửa cho draft/personal copy; Parent chỉ sửa output đã được cấp quyền. Source version không bị ghi đè.

### 31.5 Luồng Parent, Teacher và video sau khi thêm platform

Parent: topic hoặc lesson presentation là tùy chọn; SVG guide là tùy chọn; chụp ảnh bắt buộc → VLM nhận diện/đối chiếu topic hoặc lesson → cảnh báo khi lệch để đổi topic hoặc chụp lại tối đa một lần → người lớn xác nhận subject/context → chọn một activity chính qua catalog-first trước story; nếu catalog không phù hợp, người lớn có thể chọn từ tối đa ba draft AI và yêu cầu bộ khác loại lựa chọn đã hiện/từ chối → xác nhận context → story/script review → video mới theo pipeline hiện hành → private playback. No-pin trả activity chính đã pin theo run; lesson pin trả toàn bộ activities của exact version và đánh dấu activity chính. API/error recovery vẫn OPEN-TECHNICAL.

Đoạn Rev65 này được giữ để truy vết nhưng quy tắc thời điểm activity đã được Rev66 §31.17 thay thế: Parent chọn một activity chính trước story; no-pin hiển thị activity run-pinned sau video; lesson pin hiển thị toàn bộ activity exact version và đánh dấu activity chính. Catalog-first source/privacy rule tiếp tục áp dụng. Parent có thể dùng lesson public hoặc lesson được share; reusable personal copy là PRIVATE, giữ source-version lineage và không ghi lên nguồn chung.

Teacher target flow giữ occurrence/video sample. Teacher có thể tạo occurrence từ lesson preset hoặc approved plan tự tạo; lesson preset là tùy chọn. Khi đang dạy, line-sketch chỉ được tạo nếu Teacher bật; tắt nghĩa là không enqueue job và không tính quota sketch. Hệ thống chọn đồng xác suất một trẻ trong tập đủ điều kiện, kiểm tra assignment/consent còn hiệu lực, cho tối đa một reselect nếu candidate stale, rồi dừng khi tập rỗng. Teacher xem và xác nhận child/context trước khi có run/job/quota/claim; một occurrence tối đa một sample video thành công. Exact eligibility evidence, concurrency contract và error/retry schema còn OPEN.

Mọi video là generation mới từ ảnh tranh của đúng trẻ và profile context đã duyệt. Không tái sử dụng video của trẻ khác hoặc cache video dùng chung làm kết quả cá nhân. Lesson script có thể bật/tắt; nếu bật, story/video đi theo hướng đó nhưng hình ảnh/clip được sinh mới, cho phép khác biệt theo tranh/profile. Nếu VLM nhận sai subject, hệ thống yêu cầu người lớn xác nhận trước khi sửa subject và yêu cầu gợi ý lại. Các bước VLM → structured story → storyboard → adult script review → Character Bible/reference → LTX-2.5/Modal per scene → consistency → FFmpeg/TTS/subtitles → output safety → private playback không thay đổi.

### 31.6 Parent lesson history và feedback

Parent được mời/link profile có thể xem lesson/occurrence đã dạy cho trẻ trong 30 ngày tính từ lần delivery/open đầu tiên, cùng lesson public/được share còn được cấp quyền. Parent có thể xem chi tiết theo quyền và tải lesson content được phép; video trẻ vẫn theo quy tắc playback hiện tại, không mở download/export. Revoke/unpublish giữ metadata trung tính nhưng không mở lại lesson content; nội dung chỉ truy cập lại khi lesson được public lại hoặc có grant mới.

Parent có thể gửi feedback gắn với lesson version/delivery và nhận phản hồi từ Teacher, School Manager hoặc Platform Admin. Feedback scope giới hạn trong organization liên quan; organization khác không được thấy. Đây là feedback thread phục vụ trao đổi về lesson, không phải chat tổng quát. Không thêm đánh dấu hoàn thành/checklist, tải ảnh tranh lên feedback hay gửi media trẻ kèm phản hồi. School Manager/Admin có thể xem feedback và trả lời; phản hồi platform admin vẫn chỉ hiển thị trong trường đó.

### 31.7 Quota và billing platform

Nền tảng chi trả chi phí provider. Billing giữ quota grant/usage theo hai scope tách biệt: school organization và Parent account. Teacher dùng quota của school organization sở hữu occurrence; Parent dùng quota account của Parent. Review assumption (chưa phải production price/config): Parent 2 lượt included/tháng và top-up 5 lượt với giá ₫249.000; School 30 lượt included/tháng và top-up 50 lượt với giá ₫1.990.000. Included được dùng trước, top-up theo FIFO; included hết hạn cuối tháng và top-up carry-forward theo BR-38. Không có Teacher sub-pool hoặc cross-scope fallback. Purchaser/allocator authority, payment, exhausted response và terminal expiry của top-up (nếu có) còn OPEN.

Video generation của Teacher sample trừ quota của school organization gắn với occurrence; Parent tạo video mới cho child trừ quota Parent account. Trong từng scope, grant included tháng hiện tại được dùng trước top-up FIFO; hết quota thì từ chối request video mới tới khi có grant hợp lệ. AI Policy theo dõi compute/cost reservation, không thay thế Billing product quota. Quota sketch, image/slide generation và job authoring có accounting/rate limit riêng theo policy. Các số/giá ở đoạn trước chỉ là giá trị tạm cho review; quyền mua/cấp/phân bổ, expiry và commercial terms chưa được chốt theo §31.10.

### 31.8 Yêu cầu chức năng mới (FR-PL)

| ID | Ưu tiên | Yêu cầu |
|---|---|---|
| FR-PL-01 | M | Cung cấp platform Admin, School Manager, Teacher và Parent với permission có scope, server-side authorization, audit và revoke. |
| FR-PL-02 | M | Mỗi trường là một organization/tenant; mọi record của trường có tenant scope và không thể đọc chéo organization. |
| FR-PL-03 | M | Tách reusable lesson item/version khỏi occurrence; version được pin vào lần dạy/lần dùng nếu có lesson. Platform Admin/Teacher có thể yêu cầu AI đề xuất chỉnh sửa khi dùng lại lesson; Parent chỉ được chỉnh sửa draft/personal copy đã cấp quyền và không thể khởi tạo suggestion. Output có lineage, review gate và không sửa source version. |
| FR-PL-04 | M | Hỗ trợ visibility PRIVATE, SCHOOL, SELECTED_AUDIENCE và PUBLIC; hỗ trợ tìm lesson PUBLIC và download nội dung lesson được cấp quyền. |
| FR-PL-05 | M | Teacher-authored lesson chỉ được PUBLIC sau School Manager approval. Public lesson do Platform Admin author cần một Platform Admin khác có Content Admin permission review độc lập. Admin moderation/hide và unpublish thu hồi library access nhưng không xóa version/history metadata. |
| FR-PL-06 | M | Cho phép share lesson cho nhóm Parent hoặc người được chỉ định/invite; mọi grant có trạng thái/revoke và tôn trọng tenant boundary. |
| FR-PL-07 | M | Cho phép Parent mời Teacher được nêu tên và chia sẻ child profile bằng grant có scope, audit, thời hạn 90 ngày và revoke; mỗi Parent profile có 0..n grants, mỗi grant liên kết một opaque Managed Profile ref, mỗi Managed Profile có tối đa một Parent link active. |
| FR-PL-08 | M | Chỉ trả các profile fields được grant và policy cho phép; revoke có hiệu lực ngay, chặn read/token/job mới chưa accepted. Delivery Recipient là occurrence snapshot, không phải profile link. Exact field allowlist và physical owner/schema còn open. |
| FR-PL-09 | M | Teacher có structured authoring form và standardized lesson upload template; giữ giới hạn file hiện hành đến quyết định mới. |
| FR-PL-10 | M | Parser/filter tạo structured allowlist; raw original, toàn văn giáo án, ảnh nhúng và metadata không được gửi model. |
| FR-PL-11 | M | Teacher preview/correct/confirm structured draft trước AI generation; sai template hoặc parse uncertainty trả lỗi và yêu cầu sửa. |
| FR-PL-12 | M | AI-assisted lesson/activity/plan content luôn là draft, cần người có quyền review/edit/publish; không tự public. |
| FR-PL-13 | M | Lesson version hỗ trợ drawing steps, subject-learning notes, age target, một hoặc nhiều activities với materials/instructions/notes và optional script direction. |
| FR-PL-14 | M | Bao gồm khả năng tạo visual activity/topic assets hoặc session slides theo lựa chọn; ghi provenance/version/safety và không chọn provider cố định. Việc tạo asset trong từng lesson/session là tùy chọn. |
| FR-PL-15 | M | Chỉ tạo Parent hoặc Teacher line-sketch khi người lớn bật trong session; disabled thì không có generation job. |
| FR-PL-16 | M | Parent chọn một activity chính trước story; chụp ảnh bắt buộc và video pipeline giữ nguyên; sau video hiển thị activity chính đã chọn, cộng toàn bộ danh sách từ lesson version exact pin nếu có. |
| FR-PL-17 | M | Lesson script-following có thể bật/tắt theo lesson/usage; Parent preset giữ script direction của lesson, Teacher giữ approved objective/activity/safety, và adult xác nhận script revision trước video. Default, override limits và revision-pin contract còn OPEN tại §31.10. |
| FR-PL-18 | M | Không tái sử dụng video giữa trẻ; mỗi video dùng ảnh tranh và profile context được duyệt của đúng child. |
| FR-PL-19 | M | Khi subject mismatch, yêu cầu adult confirm/correct trước khi re-suggest; không tự đổi chủ thể âm thầm. |
| FR-PL-20 | M | Hệ thống chọn đồng xác suất một child trong tập eligibility/consent hợp lệ; Teacher xác nhận child/context; candidate stale được chọn lại tối đa một lần; tập rỗng dừng không fallback. Trước confirmation không tạo/accept run, job, quota usage hoặc claim. Exact predicate, evidence, concurrency and response contracts remain open. |
| FR-PL-21 | M | Parent xem lesson đã dạy cho child được link trong 30 ngày tính từ lần delivery/open đầu tiên; revoke/unpublish chỉ giữ metadata trung tính và không mở lại content. |
| FR-PL-22 | M | Parent tải lesson được phép và gửi lesson feedback; Teacher/Manager/Admin có thể xem/reply trong phạm vi school; không có direct chat, completion toggle hoặc ảnh tranh trong feedback. |
| FR-PL-23 | M | School groups và named recipients được dùng làm audience cho lesson share; membership và grants có thể thu hồi. |
| FR-PL-24 | M | Billing tách quota school và Parent account; Teacher dùng school quota của occurrence, không có Teacher pool/sub-pool hoặc cross-scope fallback; included dùng trước, top-up FIFO; included hết hạn cuối tháng, top-up carry-forward theo BR-38. Review assumption: Parent 2 included/tháng + top-up 5/₫249.000; School 30 included/tháng + top-up 50/₫1.990.000. Giá/units là tạm, không phải production configuration. Người mua/cấp/phân bổ, payment/exhaustion và terminal top-up expiry còn OPEN. AI Policy chỉ sở hữu compute reservation. |
| FR-PL-25 | M | Giới hạn profile/run mới ở 36–120 tháng, chia ba band versioned: 36–71, 72–107 và 108–120 tháng; profile/run giữ age-band version đã dùng. Profile 121–155 tháng không được nhận run mới; run accepted trước khi tuổi đạt 121 tháng có thể hoàn tất dựa trên eligibility snapshot lúc accept và các guard authorization/safety/lifecycle hiện hành. Draft legacy chỉ đọc/xóa; thông báo một lần khi phát hiện và khi mở draft. Không cho sửa/lưu trữ draft theo clarification hiện tại. |

### 31.8.1 Quy tắc nghiệp vụ platform bổ sung

| ID | Quy tắc nghiệp vụ |
|---|---|
| BR-47 | Nền tảng giáo án là phần bổ sung; các luồng Parent/Teacher và pipeline tạo video đã chốt tiếp tục áp dụng, trừ thay đổi được chủ sở hữu ghi rõ trong v2.3. |
| BR-48 | Parent/Teacher accounts và profile owners tách biệt; cross-role profile read chỉ qua invitation, consent, active scope grant và có thể revoke. |
| BR-49 | Một trường tương ứng một organization/tenant; lesson, feedback, quota và group membership không lộ chéo tenant. |
| BR-50 | Reusable lesson version khác occurrence; dùng/reuse/remix không sửa source version, occurrence cũ giữ version đã pin. AI-proposed edits tạo draft/personal copy có lineage và cần human review. |
| BR-51 | Visibility là PRIVATE/SCHOOL/SELECTED/PUBLIC; Teacher-authored PUBLIC cần School Manager approval; Platform Admin-authored PUBLIC cần một Platform Admin khác có Content Admin permission review độc lập; Admin có thể hide. |
| BR-52 | Original teacher lesson upload được giữ riêng; chỉ structured allowlist đã Teacher review được phép đi vào AI. |
| BR-53 | AI lesson/activity/visual outputs mặc định DRAFT; human review/publish bắt buộc trước khi public/show. |
| BR-54 | Parent và Teacher line-sketch chỉ chạy khi người lớn bật trong session; tắt thì không có AI job. |
| BR-55 | Parent phải chọn một activity chính catalog-first sau khi VLM subject được người lớn xác nhận; backend tìm candidates từ lesson versions PUBLIC/SHARED mà Parent được quyền xem; lesson pin ban đầu giới hạn vào exact version/hash. Qwen3.5 chọn candidate IDs/lý do; nếu không có candidate phù hợp, có thể tạo đúng 3 draft qua quality gate để adult chọn. Không gửi ảnh/audio thô/định danh. Activity đã chọn là story context và diễn ra sau video; yêu cầu bộ khác loại lựa chọn đã hiện/từ chối. Sau video no-pin trả activity run-pinned; lesson pin trả full exact-version list và đánh dấu activity chính. API/snapshot/error mapping còn OPEN-TECHNICAL.
| BR-56 | Video luôn mới theo tranh của đúng trẻ; không tái sử dụng video child khác. Lesson script-following là optional direction. |
| BR-57 | Child profile/run mới có age range 36–120 tháng với age bands versioned 36–71, 72–107 và 108–120 tháng. Profile 121–155 tháng không nhận run mới; run accepted trước khi tuổi đạt 121 tháng có thể hoàn tất theo accepted eligibility snapshot và các guard authorization/safety/lifecycle; legacy draft chỉ đọc/xóa. |
| BR-58 | Lesson audience có thể là group Parent hoặc người cụ thể; mỗi audience membership/grant có thể thu hồi. |
| BR-59 | Parent gửi feedback gắn lesson delivery; Teacher/Manager/Admin phản hồi trong school scope; không mở direct chat hoặc media upload. |
| BR-60 | Billing sở hữu quota usage theo school organization và Parent account; Teacher usage tính vào school quota, Parent usage tính vào Parent quota. Không có Teacher sub-pool hoặc cross-scope fallback; dùng included trước, top-up FIFO; included hết hạn cuối tháng và top-up carry-forward theo BR-38. Ví dụ units/giá ở §31.7 chỉ là review assumption, không phải production config. AI Policy sở hữu compute reservation riêng. Mua/cấp/phân bổ, payment/exhaustion và terminal top-up expiry còn mở. |


### 31.8.2 Approved plan supersession — behavior matrix

Invariant in every row: an accepted occurrence/run/job retains the exact approved plan revision and LessonVersionRefV1 version/hash it accepted; it is never silently retargeted to latest. Completion must pass the existing expected-revision/input/context/lesson hash fence before writing to its owning aggregate. Owner-selected behavior is: accepted-not-queued and queued work is cancelled; running work is cancellation-requested and fenced, with late results purged; READY/playable output remains pinned to the immutable old version. No automatic accepted-quota refund or extra sample claim is created. Exact commands, receipts and cleanup timing remain OPEN-TECHNICAL.

| Supersession arrives while old pinned work is… | Technical invariant | StoryRun / AI Job | Sketch Deck / approval / occurrence | Sample claim / quota / projection | Owner choice still required |
|---|---|---|---|---|---|
| Accepted, not yet queued | Preserve accepted plan/hash and admission receipts; idempotent replay resolves to same accepted intent. | Cancel before queueing; do not retarget or create replacement work automatically. | Old deck remains associated with its old hash; approval does not transfer. Exact cleanup event remains technical. | Keep accepted quota receipt; do not create another sample claim. | Cancellation receipt and cleanup timing remain technical. |
| Queued | Fence dequeue/worker start by expected revision; a late queue message must not substitute the new plan. | Cancel queued work; retries/replay cannot restart it against the new plan. | Old output remains linked to old hash; do not transfer approval/deck to new plan. | Keep accepted quota receipt; no automatic refund or extra claim. | Exact cancel command, receipt and replacement-run policy remain technical/product follow-up. |
| Running | Completion compares exact pinned hashes and expected revision; duplicate callback/replay is idempotent. | Request cancellation and fence the old revision; purge late results after reconciliation. | Late result cannot replace current content or transfer approval. | Keep accepted quota receipt; do not create an extra sample claim. Projection must not overwrite new revision. | Provider-outcome reconciliation and purge confirmation remain technical. |
| Ready but not yet played/projected | Preserve exact output provenance and old immutable plan/version pin. | Job terminal result remains on the original job; no rerun/retarget on read. | Keep old READY/playable output pinned to its old plan; new approval does not mutate it. | Do not create another successful sample claim or refund accepted quota. | Any separate removal request follows normal lifecycle; no implicit supersession hide. |
| Failed | Retain failure against the accepted old revision for audit/reconciliation. | Retry only under the existing bounded retry and idempotency policy; no implicit new-plan retry. | New plan may have independent work; old failure does not approve or invalidate it. | No inferred quota refund; pre-playable Teacher failure does not consume the successful sample slot under existing rule. | Whether a new command is allowed and its cost/claim behavior. |
| Cancelled | Keep cancellation receipt and old pin; reject late completion by expected revision/state fence. | Do not restart against the new plan on replay. | No silent approval/deck transfer. | Keep accepted quota; no extra claim. | Reuse/replacement occurrence command remains separate and cannot bypass sample/quota invariants. |

No transition in this table is a newly approved state. Exact stale/cancel events, owner command and audit fields must be closed before state diagrams or DDL are approved. Cross-owner billing and AI Policy receipts remain separate owner transactions joined by idempotent saga/reconciliation, never a shared SQL transaction.

### 31.9 Yêu cầu phi chức năng và acceptance bổ sung

| ID | Ưu tiên | Yêu cầu phi chức năng |
|---|---|---|
| NFR-34 | M | Authorization deny-by-default, tenant isolation và profile/lesson grant revocation phải áp dụng đồng nhất cho API, download, token, cache và job dispatch; thay đổi được audit metadata-only. |
| NFR-35 | M | Document filtering có thể truy vết source hash → parser/filter version → allowlisted field → Teacher correction → AI draft; raw original không lọt vào model request hoặc telemetry. |
| NFR-36 | M | Cross-role profile grants và school feedback phải được giới hạn theo tenant/scope và audit. Child-media access của Manager/Platform Admin mặc định deny trong V1; mọi ngoại lệ tương lai cần owner phê duyệt riêng với permission, purpose/reason, expiry và audit. |
| NFR-37 | M | Lesson version, generated visual, source file và remix giữ lineage; bản dẫn xuất không ghi đè source. |
| NFR-38 | M | Nội dung V1 tiếng Việt; mục tiêu trẻ 3–10 tuổi, Montessori-inspired, child-centered và người lớn là guide/observer/supporter. |

| AC | Given | When | Then |
|---|---|---|---|
| AC-46 | Có Parent, Teacher, Manager và Admin trong hai organization | Actor đọc lesson/profile/feedback/quota | Chỉ quyền được cấp trong tenant/resource scope mới thành công; mọi revoke có audit. |
| AC-47 | Teacher tạo lesson reusable và hai occurrence | Cập nhật lesson thành version mới | Occurrence cũ giữ version đã pin; lesson source không bị sửa ngược. |
| AC-48 | Teacher lesson ở trạng thái SCHOOL hoặc Platform Admin author public lesson | Author yêu cầu PUBLIC | Teacher lesson chỉ publish sau School Manager approval; Platform Admin-authored lesson cần independent Platform Admin reviewer có Content Admin permission; hide/unpublish thu hồi access, history metadata giữ nguyên. |
| AC-49 | Parent cấp consent và mời Teacher được nêu tên chia sẻ child profile | Teacher chấp nhận invitation rồi Parent revoke | Grant chỉ ACTIVE sau acceptance, term 90 ngày; mỗi Parent profile có thể có nhiều grant, mỗi grant link một Managed Profile và mỗi Managed Profile tối đa một Parent link active. Revoke tức thì chặn API/token/job mới; hai account/profile owners vẫn tách biệt. |
| AC-50 | Teacher upload giáo án theo template | Parser/filter hoàn tất | AI chỉ nhận allowlisted structured fields đã qua Teacher preview/correction; raw file/full text không được gửi. |
| AC-51 | AI tạo lesson hoặc activity suggestion | Generation thành công | Trạng thái là draft; không public trước khi người có quyền review/publish. |
| AC-52 | Lesson chứa nhiều outdoor activities hoặc Parent chạy không pin lesson | Parent chọn activity chính trước story và xem kết quả sau video | Activity chính được xác nhận/pin vào run trước script và là story context. Sau video, no-pin trả activity chính từ run snapshot; lesson pin trả toàn bộ activities của exact version và đánh dấu activity chính. Không query catalog mới sau video. |
| AC-53 | Parent/Teacher không bật line-sketch | Session bắt đầu vẽ | Không tạo sketch AI job, asset hoặc quota usage. |
| AC-54 | Parent preset có script direction hoặc Teacher plan có approved objective/activity/safety | Adult xác nhận script revision và yêu cầu video | Parent direction/Teacher approved plan được giữ trong giới hạn nội dung; video mới theo tranh/profile và không reuse video khác. Default/override limit remains OPEN. |
| AC-55 | VLM subject confidence/mapping không hợp với tranh | Adult sửa subject | Hệ thống yêu cầu xác nhận, tạo revision mới và mới sau đó gợi ý lại. |
| AC-56 | Teacher occurrence có tập child đủ điều kiện theo consent/assignment policy hiện hành | Hệ thống yêu cầu video mẫu | Chọn đồng xác suất một child; Teacher xác nhận trước khi run/job/quota/claim; candidate stale được chọn lại tối đa một lần; tập rỗng dừng không fallback, không tạo run/job/quota/claim và không lộ lý do loại từng child; occurrence tối đa một successful sample. Evidence/concurrency/error schema vẫn OPEN. |
| AC-57 | Parent profile có grant với Teacher trường A | Principal organization B đọc profile/feedback | Bị từ chối, không tiết lộ resource tồn tại hoặc nội dung. |
| AC-58 | Teacher/Manager/Admin reply feedback của Parent | Parent thuộc trường A mở feedback | Chỉ người có quyền của trường A thấy thread; không mở chat hoặc media attachment. |
| AC-59 | Platform Admin/Teacher dùng lesson PUBLIC và yêu cầu AI đề xuất chỉnh sửa | Generation hoàn tất; người có quyền review output | Tạo draft/personal copy có lineage; source version và occurrence cũ không đổi. Parent không khởi tạo suggestion; chỉ sửa draft được cấp quyền. |
| AC-60 | Lesson đã được dùng rồi unpublish | Người dùng mở thư viện/history | Giữ version, occurrence và history metadata; thu hồi quyền tìm/tải/mở lesson content. Chỉ mở lại lesson content sau khi public lại hoặc có grant mới. |
| AC-61 | Parent và Teacher yêu cầu generation từ scope hợp lệ | Video job được accepted sau quota admission | Billing ghi Parent usage vào Parent account; Teacher sample usage vào quota school sở hữu occurrence. Included dùng trước, top-up FIFO; các units/giá review tạm ở §31.7 không phải production price. AI Policy compute reservation riêng. |
| AC-62 | Tuổi child ở biên 36, 71, 72, 107, 108 hoặc 120 tháng | Profile/run validation | 36–71, 72–107 và 108–120 tháng lần lượt thuộc ba age bands versioned; ngoài 36–120 tháng không được accept/run mới theo §31.14. |
| AC-63 | Search lesson PUBLIC toàn platform | User không thuộc organization author | Public version có thể tìm/dùng; SCHOOL/PRIVATE/SELECTED không bị lộ. |
| AC-64 | Manager/Platform Admin (kể cả Content Admin permission) gửi request xem child media trong V1 | Có request, dù principal có role/permission nền tảng | Deny mặc định, không trả media hoặc capability. Role/permission không tự tạo ngoại lệ; workflow ngoại lệ tương lai chỉ được kiểm thử sau một quyết định owner riêng. |
| AC-65 | Parent/Teacher dùng profile cá nhân hóa và lesson | AI lập story/video | Tuân thủ age band/context đã duyệt, nội dung tiếng Việt; video được tạo riêng theo tranh trẻ. |
| AC-66 | Profile vào dải 121–155 tháng khi có StoryRun accepted trước khi tuổi đạt 121; người dùng mở draft legacy hoặc thử action sửa/lưu trữ | Attempt run mới; tiếp tục run accepted; đọc/xóa/sửa/lưu trữ draft; detection/open notice | Run cũ có thể hoàn tất theo eligibility snapshot lúc accept và các guard authorization/safety/lifecycle hiện hành; run mới bị từ chối. Draft đọc/xóa được, sửa/lưu trữ bị từ chối. Gửi một notice khi phát hiện và một notice khi mở draft, không lặp lại cho cùng profile/điều kiện. |
| AC-67 | Đối chiếu đủ mười cross-view cases tại §31.10.2 giữa D04, D05, D06, D07, D08 Logical/Physical, D09 và D11 | Review từng case: O-04, O-08, O-14/O-11, O-15, O-13, O-02/O-06, safety/regeneration, adult lifecycle, O-07 và O-16; kiểm O-17 audit/retention cross-cutting | Mỗi case có mapping cụ thể ở cả bảy view hoặc giải thích N/A; không có mâu thuẫn. Chi tiết không có nguồn vẫn OPEN/BLOCKED; không tự khẳng định route, field, class, state, DDL hay runtime. |

### 31.10 Các quyết định còn mở

Danh sách dưới đây giữ nguyên 17 chủ đề để các trace Q-IDs không bị đứt. `RESOLVED` chỉ nghĩa là owner đã chọn chính sách đích; không chứng minh API, schema, UI hoặc runtime đã triển khai. Phần chưa được trả lời cụ thể vẫn là OPEN.

1. **Age bands — RESOLVED.** Ba band versioned là 36–71, 72–107 và 108–120 tháng; lưu tuổi theo tháng, không lưu ngày sinh chính xác, và giữ band version đã dùng. Profile 121–155 tháng không được nhận run mới; run accepted trước khi tuổi đạt 121 tháng có thể hoàn tất theo accepted eligibility snapshot và các guard hiện hành; draft chỉ đọc/xóa. Cách backfill/chuyển band cho profile legacy là technical gate. Ảnh hưởng: FR-PL-25, AC-62/66, O-16.
2. **Quota units/prices — PARTIAL.** Owner giữ tạm Parent 2 lượt included/tháng + top-up 5 lượt ₫249.000; School 30 lượt included/tháng + top-up 50 lượt ₫1.990.000. Đây là giả định review, không phải production price/config. Hai scope tách biệt; included trước, top-up FIFO; included hết hạn cuối tháng, top-up carry-forward theo BR-38. Người mua, quyền cấp/phân bổ, payment terms, exhaustion response và terminal expiry của top-up (nếu có) vẫn OPEN. Ảnh hưởng: FR-PL-24, AC-61, Q193.
3. **Parent lesson history — RESOLVED.** Cửa sổ là 30 ngày kể từ lần delivery/open đầu tiên. Revoke/unpublish chỉ giữ metadata trung tính, không mở lại content. Mapping history/retention vào schema còn là technical gate. Ảnh hưởng: FR-PL-21/22, Q183.
4. **Teacher random-child — PARTIAL.** Chọn đồng xác suất trong tập đủ điều kiện; Teacher phải xác nhận; candidate stale được reselect tối đa một lần; tập rỗng thì dừng; trước confirmation không tạo/accept run, job, quota usage hoặc claim. Không fallback và không lộ lý do loại theo từng child. Eligibility/consent predicate chi tiết, selection evidence, concurrency/idempotency và error contract vẫn OPEN. Ảnh hưởng: UC-05, FR-T-10/FR-PL-20, AC-56.
5. **Script-following — PARTIAL.** Parent giữ script direction của preset; Teacher giữ approved objective/activity/safety; người lớn xác nhận revision cuối trước video. Mặc định bật/tắt, phạm vi override và revision-pin contract vẫn OPEN. Ảnh hưởng: FR-PL-17/18, AC-54/55.
6. **School quota authority/allocation — PARTIAL.** School và Parent quota tách riêng; Teacher dùng quota school; không có Teacher sub-pool/fallback; included trước top-up FIFO; included hết hạn cuối tháng và top-up carry-forward theo BR-38. Buyer/allocator, payment, exhaustion behavior, terminal top-up expiry và role-change effect vẫn OPEN. Ảnh hưởng: FR-PL-24, AC-61.
7. **PUBLIC lesson do Platform Admin tạo — RESOLVED.** Teacher-authored PUBLIC cần School Manager approval; Platform Admin-authored PUBLIC cần một Platform Admin khác có Content Admin permission review độc lập. Review/publish event schema và moderation evidence là technical gates. Ảnh hưởng: FR-PL-05, AC-48/60.
8. **Profile sharing — PARTIAL.** Parent profile có 0..n grants; mỗi grant trỏ một opaque Managed Profile; mỗi Managed Profile tối đa một Parent link active; named Teacher phải accept; term 90 ngày; Parent revoke tức thì; Delivery Recipient là occurrence snapshot; không match tên hoặc dùng cross-owner SQL FK. Exact field allowlist, consent artifact, physical owner/schema, renewal và school/class invite remain OPEN. Ảnh hưởng: FR-PL-07/08, AC-46/49/57/64.
9. **AI visual/slide — PARTIAL.** Output là draft, có provenance và cần reviewer; không xuất deck thành PPTX/PDF. Asset owner, review criteria, reviewer authority cho asset từ public lesson và publish conditions vẫn OPEN. Ảnh hưởng: FR-PL-12/14, AC-51.
10. **Q192 / answer 46 source — OPEN-OWNER.** Owner không nhớ câu hỏi gốc. “Có, cho phép” không cấp permission hoặc mở rộng scope; không có requirement mới cho tới khi câu hỏi và đối tượng/mục đích được khôi phục.
11. **Child-media exception — V1 RESOLVED; future flow OPEN.** Platform Admin/Content Admin/School Manager không được xem child media trong V1. Future exception, nếu cần, phải là quy trình riêng có owner approval; thiếu quy trình không chặn V1 deny-by-default. Ảnh hưởng: NFR-36, AC-64.
12. **Parent personal copy — PARTIAL.** Copy reusable, PRIVATE, giữ source-version lineage và không sửa published source; delete request có 30 ngày recovery window. Exact editable fields, data owner/schema and retention after recovery remain OPEN. Ảnh hưởng: FR-PL-03/17.
13. **Parent không dùng Lesson Preset — RESOLVED; Rev66 clarification.** Parent chọn một activity chính trước story theo catalog-first; no-pin trả run-pinned activity sau video, lesson pin trả toàn bộ activity exact version và đánh dấu lựa chọn chính. API, snapshot and recovery details remain OPEN-TECHNICAL.
14. **Role and permission — PARTIAL.** Server-side authorization theo role/scope/permission version và deny-by-default; Content Admin là permission của Platform Admin; child media bị deny trong V1. Principal/assignment persistence, resolver/cache/revoke implementation, force-close mapping và audit field schema vẫn OPEN-TECHNICAL. Ảnh hưởng: FR-PL-01/08, NFR-34/36.
15. **Approved-plan supersession — RESOLVED at policy level.** Accepted-not-queued/queued work is cancelled; running work is cancellation-requested and fenced, with late results purged; READY/playable output retains its immutable old pin. No automatic quota refund or additional sample claim. Commands/receipts, reconciliation and purge evidence remain OPEN-TECHNICAL. Ảnh hưởng: §31.8.2, FR-T-08/20.
16. **Legacy profile 121–155 months — PARTIAL.** No new accept/run; a run accepted before the profile reaches 121 months may complete using its accepted eligibility snapshot, subject to current authorization, safety and lifecycle controls. An existing draft remains read/delete only, with one notice on detection and one when opened; edit/archive is not approved. Migration/backfill mechanics remain OPEN. Do not clamp or delete source data by inference. Ảnh hưởng: FR-PL-25, AC-66, profile/run admission and migration gates.
17. **Audit metadata/retention — PARTIAL.** Audit is metadata-only and excludes raw child media/content. Retention targets are 180 or 365 days by record type; exact type-to-duration map, field allowlist, audit authorization and physical mapping remain OPEN-TECHNICAL. Ảnh hưởng: NFR-34/36, data dictionary/physical ERD gate.

18. **SVG source-class behavior — OPEN-TECHNICAL.** Map `STROKE_READY`, `REQUIRES_MANUAL_AUTHORING`, `STATIC_ONLY` and `REJECTED` to versioned API/UI outcomes. Candidate safe rule: Parent has no manual authoring tool; rejected SVG is never rendered; unavailable-guide states never block mandatory capture. Classification names and exact fallback are not frozen.
19. **Guide/presentation quality review — OPEN-TECHNICAL.** Reviewer count, score aggregation, disagreement handling and adjudication are undecided. Rev83.3's proposed 4/5 recognizability/teachability floor and 2-point disagreement threshold are suggestions only, not approved requirements.
20. **Authoring/revision semantics — OPEN-TECHNICAL.** Decide supported guide edits, local undo/redo history, server draft revisions, published revision immutability, autosave concurrency/conflict handling and idempotency before API freeze.
21. **Renderer performance — OPEN-TECHNICAL.** Define browser/renderer versions, device classes, path/asset limits, sample size, cold/warm measurements and SLO. Emulator functional behavior and low-end physical Android performance are separate evidence categories; no numeric target is approved.
22. **API and persistence alignment — OPEN-TECHNICAL.** Rev83.3 API V2 routes remain proposals, not mounted contracts. Reconcile version, request/response/job/error lifecycle, guide/presentation revision and asset ownership, DTR, DDL and migration before implementation; do not infer entities/routes.
23. **Failure recovery — OPEN-TECHNICAL.** Distinguish capability disabled, catalog miss, worker unavailable, timeout and quality rejection. Parent capture must remain available and Teacher can continue lesson editing. Exact status codes, retries and recovery UI remain open.
### 31.10.1 Theo dõi mười nhóm readiness cho diagram

Bảng này theo dõi các phụ thuộc cross-cutting; trạng thái là mức đầu vào hiện có, không phải sign-off SRS/diagram. Owner cá nhân chưa được chỉ định trong hồ sơ.

| Nhóm | Trace hiện có | Owner/status theo hồ sơ hiện tại | Việc còn phải đóng |
|---|---|---|---|
| 01 Teacher Random Child | UC-05, FR-T-10, FR-PL-20, AC-56; Q-01; D-06 | Owner policy selected; PARTIAL | Equal probability, Teacher confirmation, max one stale-candidate reselect, empty-set stop/no fallback and no pre-confirmation run/job/quota/claim are set. Exact consent/eligibility predicates, evidence, concurrency and API/UI contracts remain open. |
| 02 Profile Sharing & Identity Matching | M-11/M-15; D-09; Q-04; §§31.3/31.6 | Owner policy selected; PARTIAL | Cardinality, named Teacher acceptance, 90-day grant, immediate revoke and occurrence-level recipient snapshot are set. Field allowlist, physical owner/mapping, renewal and school/class invitation remain open. |
| 03 Role & Permission | M-03/M-04/M-05; D-07; Q-13; D-146 | Policy partly set; PARTIAL / OPEN-TECHNICAL | Content Admin is a Platform Admin permission; child media is denied in V1; target auth is server-side by role/scope/version and deny-by-default. Persistence/resolver/cache/revoke and force-close evidence remain open. |
| 04 Plan Supersession | M-10; FR-T-08/20; DTR §5.5–5.6 | Owner policy selected; PARTIAL / OPEN-TECHNICAL | Accepted/queued cancellation, running fence/purge, immutable READY pin, no automatic refund/extra claim are set. Exact commands, receipts, reconciliation and UI handling remain open. |
| 05 Parent không dùng Lesson Preset | R-04; UC-02/18; FR-P-05; DTR §5.6/14.3 | Owner policy selected; PARTIAL / OPEN-TECHNICAL | Parent must select one main activity before story from accessible published/shared lesson activities; if no candidate fits, exactly three quality-gated drafts may be generated for adult selection. A replacement set excludes already-shown/rejected choices. No-pin playback returns the run-pinned activity without catalog lookup; lesson pin returns all exact-version activities and marks the chosen main activity. API, snapshot and error-recovery evidence remain technical inputs. |
| 06 Các chính sách nghiệp vụ còn mở | Q-02–Q-12; D-04/D-08/D-14; OI-06 | PARTIAL / OPEN-OWNER | Residual items: quota authority/expiry/production pricing, script default/override, AI visual asset ownership/review criteria, copy editable fields, Q192 source, legacy in-flight work and audit category map. See §31.10(2),(5–6),(9–10),(12),(16–17). |
| 07 Physical Database & ERD | M-07/M-13; D-01–D-04/D-16; OI-11; DTR §§4–7/10/14.4–14.6 | BLOCKED / OPEN-TECHNICAL | DTR remains v2.5-draft and is not aligned to SRS Rev66. Logical relationship/cardinality fields and physical dictionary/DDL, constraints, indexes, migration crosswalk and new presentation/guide owners need aligned review; do not infer columns/FKs. |
| 08 State Machine & Activity | M-08–M-10/M-16; D-06/D-10/D-11; SRS §§6/22–23 | PARTIAL / OPEN-TECHNICAL | Inventory exists, but source/event/actor/guard/effect/target/error/timeout/retry/revoke/cancel rows are incomplete across aggregates. Do not add states without an approved source. |
| 09 API & Sequence | R-02; D-18; Q-02; SRS §21; API Rev37 | PARTIAL / OPEN-TECHNICAL | Request/response/error schemas, auth/revision/idempotency, owner receipts, events/callbacks, timeout/reconciliation/compensation and current mounted proof are incomplete. Target routes are not proof of a mounted contract. |
| 10 Screen Flow, Class & Package | D-17/D-19/D-20; OI-17; Catalog §§7–8 | PARTIAL / OPEN-DESIGN/OPEN-TECHNICAL | Screen IDs/routes/edges/UI states/design evidence; class fields/operations/ports/cardinality; exact imports/DI/router wiring and current source-cycle review remain incomplete. Keep TO-BE and AS-BUILT views separate. |

Các trạng thái ở bảng là readiness, không phải phê duyệt SRS hay diagram. Q-IDs và M/D/R-IDs giữ nguyên.

<a id="srs-31-10-2"></a>
### 31.10.2 Bảy diagram còn thiếu đầu vào — readiness, cập nhật theo Rev67

The owner-supplied checklist reviewed for the earlier amendment identifies its source SRS as Rev61; it is review input only. A follow-up assessment supplied on 2026-11-13 labels itself Rev65. Both are review inputs, not product authority or proof of diagram completion. The current product authority remains the canonical FEAT-063 v2.7-draft Rev67 working SRS, based on the owner-selected Rev57 source and local amendments through Rev67; it remains unsigned. The checklist says Context, Use Case, Workflow and System Architecture have sufficient inputs for logical TO-BE completion; that statement is not independently revalidated here and does not sign off those four views. The Rev65 follow-up is reconciled against Rev66/Rev67 at §31.18. No diagram artifact is created or signed off here.

`PARTIAL` means one or more required inputs are not yet traceable to an approved requirement/companion/source. `BLOCKED` means a required same-baseline or physical source is missing. `DONE` for an input document, `READY-TO-DRAW`, and `SIGNED-OFF` are separate milestones. `READY-TO-DRAW` requires all nodes/edges/guards/fields/operations in scope to have an approved or explicitly target-labeled source, with no material TBD. `SIGNED-OFF` is a separate owner/design approval after drawing. A TO-BE view must never be labeled as implemented/as-built without source evidence.

| Diagram | Status | Input required before `READY-TO-DRAW` | Dependency gate |
|---|---|---|---|
| D04 Activity | PARTIAL | Cover the input checklist's A01–A10 families: Parent preset/no-preset, Teacher occurrence and selection exceptions, sharing/revoke, lesson review/publication, video/quota admission, plan supersession, lifecycle and capacity/billing only where V1 scope is confirmed. For each sourced case, record action, actor, precondition, two-way guard, owner write/no-write, event/receipt, safe terminal, timeout/retry/compensation. | B2 state/activity + B3 API/event; B1 for persisted receipts |
| D05 Sequence | PARTIAL | Cover S01–S12 families in the input checklist: Parent preset/no-preset, Teacher selection/claim, sharing, lesson review, admission/worker callbacks, regeneration, supersession, reassignment/force-close, payment callbacks and closeout. Per message, source/receiver/owner, sync/async, request/response/error, auth revision, idempotency, transaction owner, event version, timeout/reconcile/compensation and evidence remain required. Mark `TO-BE`/`PROPOSED` separately from `MOUNTED` proof. | B3 API/event; B2 state; B1 receipt/data keys |
| D06 Screen Flow | PARTIAL | Parent, Teacher, School Manager and Platform Admin screen families; each screen needs an approved ID/role, actual route or explicitly target-labeled route, entry/trigger, authorized data/API, guard, back/cancel/resume, loading/empty/denied/error/conflict states, revoke handling and design evidence. Include no-preset completion, legacy-age notice, selection empty/stale, quota/payment pending, supersession and publication review where applicable. Do not invent screen names/routes. | B4 screen/navigation + B3 contract |
| D07 Class | PARTIAL | Verify candidate class groups in the input checklist against target contracts and source; they are not an approved class inventory. For any included class, record owner/module/layer, typed attributes, operation signatures, interface/port, cardinality/ownership, invariants, version/lineage and BR/FR/AC/decision trace. Do not equate ORM or source class with approved domain model. | B5 class/package + B1 logical data + B3 contracts |
| D08 ERD — Logical | PARTIAL | Same-baseline active mappings, logical identifiers/attributes, owner, tenant scope, cardinality/optionality, lifecycle, typed cross-owner refs and source trace. Keep 48 legacy/read-only mappings distinct. The 92-active/48-legacy counts remain SRS target counts, not a live schema; the conceptual view is outside this missing-input gate. | B1 data register + B5 class alignment |
| D08 ERD — Physical | BLOCKED | Matching reviewed Data Table Register; per-column SQL type/null/default/key/check/index/FK actions; approved DDL source and retained/refactored column migration crosswalk. No schema detail may be invented from diagram prose. | B1 physical dictionary/DDL/migration evidence |
| D09 State Machine | PARTIAL | Start from state names already in §6.1.1 and verify lifecycle aggregates against the same-baseline state matrix. Require full transition rows for source state/event/actor/guard/target/effect/receipt/error/invalid transition/timeout/retry/cancel/revoke; keep StoryRun, AI Job, billing and review states separate. Missing source state names remain a definition gap, not an invitation to invent states. | B2 state matrix + B3 event contract + B1 keys |
| D11 Package | PARTIAL | Separate target package ownership/dependency tree from current-source package/import/DI/router proof tied to an exact commit; include cycle result and composition entrypoints. The Rev57 source-only scan in §32.7 is not proof of the current source tree. | B5 package/dependency scan |

#### Ten-case cross-view coverage

The checklist scenario labels are review-input indexes, not new APIs, route IDs, class names, state names or approved contracts. The checklist contains ten cross-view cases. The matrix below spells out what each case must show in each view; a missing source detail stays open instead of being filled by diagram prose.

| # | Policy case | Cross-view representation required before finalizing the relevant diagrams |
|---:|---|---|
| 1 | O-04 random child, empty set and concurrency | D04: eligible-set branch, stale-candidate reselect at most once, empty-stop/no-fallback, no pre-confirm write and concurrent-confirm path. <br>D05: selection/confirm messages, revalidation, idempotency or compare-and-set claim, and no run/job/quota/claim before confirmation. <br>D06: confirm, stale, empty and safe-stop states; no arbitrary child picker. <br>D07: selection/occurrence/claim owners and one-successful-claim invariant. <br>D08: logical refs and claim uniqueness/evidence; physical enforcement remains B1-blocked. <br>D09: selection and claim transitions without admitting a run before confirmation. <br>D11: Lesson–BE1–Story contracts/ports; no cross-owner database write. |
| 2 | O-08 profile sharing, acceptance and revoke | D04: invite named Teacher, accept/reject, 90-day expiry, renewal if approved, revoke and denial of later reads/new unaccepted jobs. <br>D05: versioned invite/accept/revoke commands and receipts; accepted-run snapshot behavior stays under the existing rule. <br>D06: invite, accept, expired, revoked and denied screens. <br>D07: grant/invitation/recipient responsibilities and ownership. <br>D08: Parent Profile 0..n grants, one Managed Profile per grant, max one active Parent link, opaque refs, 90-day term and occurrence recipient snapshot; exact columns remain open. <br>D09: only sourced invitation/grant lifecycle states; do not invent states. <br>D11: Parent–BE1–Story through contracts, not cross-owner SQL. |
| 3 | O-14 authorization/revoke and O-11 child-media denial | D04: authorize principal, role, scope and permission version before read/write; deny fail-closed. <br>D05: carry authorization revision and conflict/deny outcome; do not leak whether a denied resource exists. <br>D06: denied/expired/revoked UX; no V1 child-media access screen, including for Content Admin. <br>D07: resolver responsibility for principal/resource/action/scope/version; exact signature remains open. <br>D08: keep role/assignment/grant version with its owner and use typed refs; no inferred Firebase role or cross-owner FK. <br>D09: use sourced revoke/assignment transitions and reject invalid commands. <br>D11: Identity/BE1 and resource-owner ports; no direct owner-table mutation. |
| 4 | O-15 approved-plan supersession | D04: separate accepted-not-queued, queued, running and READY/playable branches; cancel/fence late work, preserve old READY pin. <br>D05: cancellation/fence command, late callback, idempotent receipt and reconciliation path. <br>D06: show stale plan/job and old pinned output; require explicit refresh/review, never silently show latest as the old run. <br>D07: plan revision, run pin and job target/version/hash responsibilities. <br>D08: logical version refs and receipt/claim mapping; exact physical fields remain open. <br>D09: keep StoryRun, AI Job and billing state separate; queued work cancels, running work fences, READY retains old pin. <br>D11: Lesson–Story–AI Jobs ports with no cross-owner write. |
| 5 | O-13 Parent without a preset | D04: after adult subject confirmation, select one main activity from accessible published/shared lesson versions; pinned lesson restricts initial candidates to exact version/hash. If none fit, exactly three quality-gated drafts may be produced. <br>D05: trace catalog filter → Qwen3.5 eligible candidate IDs/order/reasons → backend membership validation/canonical hydration; exclude raw artwork/audio and identifiers. A replacement set excludes shown/rejected candidates. <br>D06: activity selection is required before story; suggestion errors leave a recoverable selection state and cannot silently bypass it. After playback, no-pin returns the run-pinned activity without a catalog query; lesson pin returns the full exact-version list and marks the selected activity. <br>D07: lesson/version pin is optional and immutable. <br>D08: persist activity snapshot and presentation/guide revisions only after same-baseline DTR review; do not infer tables. <br>D09: source states/transitions require an approved lifecycle inventory. <br>D11: route through application/lesson/catalog boundaries; mounted status needs source evidence. |
| 6 | O-02/O-06 quota and compute admission | D04: AI Policy compute reservation and Billing video quota admission are separate owner steps; deny before dispatch. <br>D05: correlate both receipts/idempotency keys and ambiguous reconciliation; denied admission creates no accepted job or usage. <br>D06: pending, exhausted, denied and retry-safe states; do not show accepted before both receipts. <br>D07: separate Billing quota and AI Policy compute ports/owners. <br>D08: map grants, usage and receipts to their owners; no cross-owner FK/transaction assumptions. <br>D09: distinguish intent/pending, accepted and denied without merging billing and job states. <br>D11: Billing and AI Policy remain separate modules; no cross-owner SQL transaction. Temporary units/prices are not production configuration. |
| 7 | Safety validation and regeneration | D04: unsafe/failed/review branches, hide old output on accepted replacement, and keep rewrite/scene/video retry counters separate. <br>D05: worker result, safety callback, duplicate/late result and retry correlation; exact schemas remain B3-open. <br>D06: blocked/review/retry/regenerate states without replaying hidden output. <br>D07: validation, generation and asset-lineage responsibilities. <br>D08: map output status and provenance/lineage refs; do not infer physical columns. <br>D09: keep StoryRun, VideoGeneration and AI Job transitions separate; unsafe output cannot become playable. <br>D11: Story–AI Jobs–Core Asset boundaries through ports/events. |
| 8 | Adult idle, cancel and delete lifecycle | D04: 144-hour reminder, 168-hour closeout, cancel/delete, lock release and cleanup terminals. <br>D05: scheduler, notification, purge/cleanup and late-result handling. <br>D06: resume, reminder, closed, delete-pending and safe error states. <br>D07: lifecycle operations and asset references by owner. <br>D08: retain only required lifecycle/retention refs; physical mapping remains open. <br>D09: timer behavior, 144/168-hour outcomes, `DELETE_PENDING` and terminal cleanup according to existing states. <br>D11: Story–Notifications–Core Asset integration through defined ports/events. |
| 9 | O-07 lesson publication review | D04: draft/review/reject/publish branches; Teacher PUBLIC needs School Manager review; Platform Admin-authored PUBLIC needs independent review by another Platform Admin with Content Admin permission. <br>D05: author/reviewer commands and decision/publish receipts; event contract remains B3 input. <br>D06: distinct author and reviewer views, reject/return-to-draft and permission-denied states. <br>D07: lesson-version, review-decision and reviewer-permission ownership. <br>D08: version/visibility/review provenance mapping; physical fields remain open. <br>D09: use sourced draft/public/hidden transitions only. <br>D11: Lesson and Identity permission boundary; no fifth Content Admin role. |
| 10 | O-16 legacy age behavior | D04: reject new accept/run at 121–155 months; allow a run accepted before age 121 to complete under its accepted eligibility snapshot and current authorization/safety/lifecycle gates; draft read/delete only. <br>D05: reject new admission, continue the accepted run without re-accepting, and deduplicate the detection/open notices. <br>D06: legacy notice, read/delete actions and denied new-run/edit/archive actions. <br>D07: age-band policy and accepted-run snapshot responsibilities. <br>D08: preserve source profile and record migration mapping; do not clamp/delete or invent schema. <br>D09: distinguish denied new run from allowed continuation of a pre-age-out accepted run; use existing states. <br>D11: Profile/Identity–Story policy boundary through a contract/port. Migration remains open. |

Across all applicable rows, O-17 audit stays metadata-only, excludes child names/media/content, and uses the selected 180/365-day retention target by record type; exact type-to-duration mapping, fields, authorization and physical mapping remain open. B1=Data/Physical; B2=State/Activity; B3=API/Event/Sequence; B4=Screen/Navigation; B5=Class/Package. The Data Table Register remains separately labeled v2.5-draft and is not aligned to SRS Rev66; this cross-document baseline mismatch blocks physical ERD completion. Logical/physical ERD cannot be marked complete from the supplied checklist alone.

The suggested P0–P7 work order in the review note is a planning aid, not a new product requirement or evidence that its companion artifacts exist. B1 data/physical inputs are prerequisite to finalizing persisted keys/receipts; B2/B3 state and contract detail must reconcile; B4 follows sourced navigation/API boundaries; B5 must align classes with data and contracts. Detailed execution, approval and artifact tracking remain in the feature plan/evidence records.

<a id="srs-31-10-3"></a>
### 31.10.3 Minimum records required to close each diagram input gate

This section defines the minimum trace and evidence needed to assess the seven views in §31.10.2. It does not claim that the catalogs, diagrams, runtime routes, database schema, or source scans already exist. `OPEN` means a decision/source is missing; `OPEN-TECHNICAL` means policy exists but its technical contract/evidence is missing; `NOT VERIFIED` means current-source proof was not collected; `BLOCKED` means a required baseline/source is unavailable. `TO-BE` and `PROPOSED` describe target design only. `SOURCE-PRESENT` and `MOUNTED-OBSERVED` require attributable source evidence; runtime wiring also needs an exact commit and observation date. A complete checklist or template is not evidence of `READY-TO-DRAW`. `SIGNED-OFF` requires a separate authorized review after drawing.

#### D04 — Activity

Maintain an `ACTIVITY_SCENARIO_CATALOG` for A01–A10. These are review aliases, not new use cases or approved diagram names.

| Alias | Scenario coverage |
|---|---|
| A01 | Parent with an exact pinned lesson version: topic/lesson/guide are optional before the mandatory drawing capture; validate current access and pin ref/version/hash; compare VLM subject with selected topic/lesson and allow at most one recapture; after adult subject/context confirmation, select one main activity from the exact pinned version before story; obtain separate compute/quota admissions; pass technical and safety gates before playback; reauthorize before returning activities from the exact pin and deny content/token if access was revoked. |
| A02 | Parent without a lesson pin: optional topic/guide and mandatory capture; mismatch may allow a topic change or one recapture; after adult subject/context confirmation, select one main activity from currently accessible PUBLIC/SHARED lesson activities before story. If none fit, AI may produce exactly three quality-gated drafts; replacements exclude shown/rejected choices. Suggestion failure/unknown cannot bypass selection or proceed to story; exact recovery is OPEN-TECHNICAL. After video return only the run-pinned choice, without a new catalog query or additional activity list. |
| A03 | Teacher occurrence/sample, approved plan, optional deck, eligible-child selection and Teacher confirmation; one child and one successful sample per occurrence. |
| A04 | Empty candidate set, stale candidate with at most one reselect, revoke/assignment change and duplicate/concurrent confirmation; no run/job/quota usage/claim before Teacher confirmation. |
| A05 | Named Teacher profile-share invitation, acceptance/rejection, expiry, renewal only if approved, revoke and denial of later reads or new unaccepted work. |
| A06 | Lesson upload/filter, Teacher preview/correction, review, reject/hide and publication under BR-51 reviewer rules. |
| A07 | Script confirmation and video admission, separate AI Policy and Billing receipts, dispatch, worker/safety outcomes and reconciliation. |
| A08 | Plan supersession at accepted-not-queued, queued, running and READY/playable points; cancel/fence late work and preserve the old immutable pin. |
| A09 | Adult idle reminder/closeout, cancel/delete, lock release and media cleanup under existing lifecycle rules. |
| A10 | School capacity, payment callback, grace/downgrade and read-only behavior only where current SRS confirms V1 scope; otherwise mark `N/A` with a sourced rationale. |

For every action/decision, record scenario/step ID; UC/BR/FR/AC/decision trace; trigger and actor/swimlane; input and typed references with revision/hash; preconditions; action/decision; both true and false guard outcomes; owner write or explicit `NO WRITE`; sourced domain-state change or `NO CHANGE`; event/receipt or `NONE`; next step; failure/deny/empty/stale/timeout/cancel/revoke path; timeout/retry/reconcile/compensation rule; source/evidence and status. Every decision needs both branches and a safe destination. Labels such as `SUCCESS`, `DENY`, `EMPTY`, `STALE`, `TIMEOUT`, `CANCEL`, `REVOKE`, `FAILED`, and `AWAITING_RECONCILIATION` are analysis outcomes, not domain states unless separately defined by a source.

Keep the 144-hour adult reminder, 168-hour adult closeout and six-hour accepted AI-job deadline separate (§§6.1.1, 6.2, BR-39). Keep the counters distinct: at most three story rewrites after the initial story; at most two technical retries per scene after its initial attempt; and at most two full-video regeneration requests after the initial video request (BR-11/13/17/45). Random-child reselect is at most once and only for a stale candidate (§5.2/UC-05/AC-56). Show fork/join only for actual parallel work, with its join condition and partial-failure path. Billing quota and AI Policy compute remain separate owner steps; do not dispatch until both admission receipts are confirmed or reconciled.

#### D05 — Sequence

Maintain a `SEQUENCE_MESSAGE_INDEX` for S01–S12. Include only participating lifelines; a proposed provider/service lifeline is not evidence that it exists or is mounted.

| Alias | Message coverage |
|---|---|
| S01 | Parent with exact lesson pin: capture is mandatory and topic/guide optional; validate current access and resolve/pin exact lesson ref/version/hash; perform subject mismatch handling with at most one recapture; after adult confirmation select one main activity from the pinned version before story; receive separate AI Policy compute and Billing quota receipts; run job/result/technical+safety gates; play video; reauthorize before returning activities from that exact pin, denying content/token if current access was revoked. |
| S02 | Parent without lesson pin: after mandatory capture, VLM and adult subject/context confirmation, required pre-story selection filters currently renderable activities from accessible published/shared lessons. Qwen3.5 receives only the minimized allowlist (age band, allowed interest tags, selected topic, adult-confirmed subject, visible features and confirmed narration when present) and returns eligible IDs/reasons; backend validates membership and hydrates canonical content. No image/audio bytes or identity. If none fit, it may draft exactly three temporary candidates through quality gate; replacement requests exclude shown/rejected IDs. Story waits for adult selection. Suggestion failure/unknown cannot silently bypass the required choice; exact recovery remains OPEN-TECHNICAL. After video return the run-pinned main activity only, with no catalog query or additional list. |
| S03 | Teacher eligibility response, confirmation, stale/empty/reselect handling and one-successful-sample claim. |
| S04 | Named profile-share invitation/accept/revoke, grant revision and effects on later reads or unaccepted jobs. |
| S05 | Lesson upload, extraction/filter, author preview/correction, reviewer decision and publish/hide. |
| S06 | Story intent, separate AI Policy compute reservation and Billing quota receipt, denial/ambiguity reconciliation, then AI Jobs dispatch only after accepted receipts. |
| S07 | Queue/worker/provider result, validation, safety, asset commit, duplicate/late/out-of-order callback and cleanup. |
| S08 | Adult rejection, hide old playback, script reconfirmation and bounded full-video regeneration within the same run. |
| S09 | Plan supersession cancel/fence, immutable old pin, stale callback rejection and reconciliation. |
| S10 | Assignment transfer, Story lock/compensation, authorization cache revocation and distinct explicit emergency force-close command. |
| S11 | Signed payment event verification, provider-event dedupe, payment receipt, entitlement/capacity change and grace handling. |
| S12 | Scheduler/inbox/push best-effort, idle closeout, cancel/delete, object purge, outbox and stuck-work reconciliation. |

For each message, record message ID; sender/receiver and owner; sync/async; command/query/event and version; request fields with types/requiredness only when sourced; response/error envelope and UI handling only when sourced; authorization/scope and expected revision; idempotency/correlation/causal key; owner transaction and receipt; timeout/retry/dedupe/out-of-order/dead-letter/reconciliation behavior; source commit/date and evidence status. For each event/callback also record envelope, source owner, consumer, delivery mode, causal/reference key and handling for duplicate, out-of-order, timeout and dead-letter cases. Mark each edge `TO-BE`, `PROPOSED`, `SOURCE-PRESENT`, `MOUNTED-OBSERVED`, or `NOT VERIFIED`. HTTP status, error code, endpoint, payload and event shape stay `OPEN` if no current source defines them. Cross-owner writes remain separate owner transactions; ambiguous admission receipts use the same idempotency key and do not permit dispatch while unresolved.

#### D06 — Screen Flow

Maintain a `SCREEN_CATALOG`, `SCREEN_NAVIGATION_MAP`, and UI error/state matrix. Cover the role surfaces listed in §21.5: Android Parent, Web Teacher, School Manager, Platform Admin content administration and the operator dashboard where applicable. These are surface families, not approved screen IDs or routes. Record a stable screen ID only if sourced/approved; otherwise mark ID and route `PROPOSED` or `OPEN`. For each screen capture app/surface, role/resource scope, design owner/evidence, entry trigger/preconditions, actual route/deep link or proposed status, authorized data/query/API and revision, visible-data allowlist, primary/secondary action and resulting command, and each guard-controlled outgoing edge. Include Back, Cancel, Resume, Refresh, deep link, background/foreground, token expiry, offline/reload behavior and async progress where applicable. Record loading, ready, empty, denied, expired, stale/conflict, quota exhausted, pending/reconciling, failed, retry and success as presentation outcomes, not domain-state names. Every branch needs a reachable safe exit; client navigation alone is not business confirmation. Do not invent screens/routes or imply design approval.

#### D07 — Class

Maintain a `CLASS_CONTRACTS` inventory and separate `CLASS_RELATIONS` view. A candidate source/ORM class is not automatically an approved domain class. For each included class/interface/port record source status (`TO-BE`/`PROPOSED`/`SOURCE-PRESENT`), owning module/layer, responsibility, typed attributes and nullability only when sourced, operation signatures/errors only when contracted, ports, relation/multiplicity, aggregate/tenant owner, invariants, version/lineage refs, dependency direction and BR/FR/AC/decision/API/data trace. Keep cross-owner references typed and opaque where required; do not infer cross-owner foreign keys or duplicate owner state. Keep missing details `OPEN` with the decision/source owner needed.

#### D08 — ERD Logical and Physical

Keep the two ERDs separate. For Logical ERD record entity/aggregate and owner, logical identifier/reference type, sourced attributes and lifecycle meaning, cardinality/optionality, tenant/resource scope, version/lineage, constraints/invariants and trace to the aligned data register and class/contract views. Keep the SRS target counts of 92 active and 48 legacy mappings distinct from a verified live schema; keep legacy/read-only mappings separate. Cross-owner references are typed contracts, not implicit joins or presumed SQL foreign keys.

For Physical ERD, tie every table/column to a reviewed same-baseline DTR/DDL source and record physical type, nullability, default, PK/FK/unique/check/index definition, delete/update action, owner, migration/backfill/rollback crosswalk and database/source evidence. Do not derive DDL from the logical model, examples, old DTR versions or §32 environment snapshots. The current Data Table Register remains v2.5-draft and is not aligned to SRS Rev66; therefore D08 Physical remains `BLOCKED`. Do not mark columns, constraints or migration behavior complete.

#### D09 — State Machine

Maintain a `STATE_INVENTORY` and `STATE_TRANSITION_MATRIX` per aggregate. Start only from states in current SRS §6.1.1 or a separately approved contract. For each aggregate record state source and initial/terminal role. For each transition record aggregate, source state, command/event and version, actor/owner, authorization and expected-version guard, target state or explicit `NO CHANGE`, owner write/effect, receipt/outbox event, response/error, invalid-transition behavior, timeout/retry/cancel/revoke/supersession behavior, compensation/reconciliation and source/evidence. Demonstrate reachable states with a valid exit or sourced recovery path. Keep StoryRun, VideoGeneration, AiJob, billing/payment and lesson-review lifecycles separate. For aggregates without a sourced inventory in §6.1.1 or another approved contract (for example, ProfileShareGrant, LessonVersion publication/review, deletion/purge artifact lifecycle and quota-admission receipt), leave state names/transitions `OPEN` until a source supplies them. Do not apply LessonOccurrence states to a separate LessonVersion lifecycle or infer enums. A UI outcome or reconciliation label is not a domain state unless defined by a source. Adult timers and AI-job deadline remain independent; late/duplicate callbacks cannot bypass revision fences, authorization, safety or immutable pins.

#### D11 — Package

Maintain separate `TO-BE` package ownership/dependency and `AS-BUILT` source-dependency records. For target packages record path/name as `PROPOSED` if absent, owner/layer, public visibility, import policy, allowed direction and contract. For as-built evidence record exact repository commit, scan date/tool/scope, source/destination package paths, dependency kind (`import`, `port`, `event`, HTTP, adapter/DI), source evidence, purpose, allowed/forbidden result and any cycle; document cycle disposition/resolution and its reviewer/approval where required. Verify composition entrypoints, dependency-injection registrations, mounted routers, queue/worker composition, event consumers and task registrations against that exact revision. Report pass/fail only for checks actually run. §32.7 records a historical static import cycle between `infrastructure.canvas_render` and `infrastructure.canvas_render.renderer` at commit `ae5707ca188d01d9719ed959b62d768ae927912d`; use this only as a lead for a fresh exact-commit scan, not as a current cycle result or proof of closure. §32 is an environment-specific snapshot, not a current exact-commit scan. Do not claim a proposed package/router is present or mounted without source evidence.

#### Cross-view closeout

For AC-67, map each of the ten policy cases in §31.10.2 to applicable D04/D05/D06/D07/D08 Logical/D08 Physical/D09/D11 record IDs, or give a reasoned `N/A`. Record mismatches, resolution/source, approver when a product decision is required, and status. O-17 audit remains metadata-only; exact event-to-retention mapping, field allowlist, access authority and physical schema remain open. A complete catalog or blank template is not evidence of `READY-TO-DRAW`; readiness does not imply `SIGNED-OFF` or production implementation.

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
| Q158 | Historical record: owner had selected FLUX.3 for line-sketch/lesson visuals; Rev66 §31.17 supersedes it with SVG catalog + deterministic vector engine. Production approval and Presenton remain open/historical. | §31.1/31.4; §31.12/31.17; FR-PL-14 |
| Q159 | Owner clarification ngày 2026-11-06: Platform Admin và Teacher được khởi tạo AI suggestion; Parent chỉ chỉnh sửa draft được cấp quyền. | §31.4; §31.12 |
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
| Q183 | Câu trả lời ban đầu nêu 30/60 ngày; owner follow-up chọn 30 ngày từ lần delivery/open đầu tiên. | §31.6; §31.10(3) |
| Q184 | Video source là ảnh tranh bé vẽ. | §31.5; FR-PL-18 |
| Q185 | Teacher chọn ngẫu nhiên một trẻ đại diện; Parent có thể tạo video mới từ lesson cho con. | §31.5; FR-PL-18/20 |
| Q186 | Theo đúng script direction nhưng video khác biệt theo child drawing. | §31.5; FR-PL-17/18 |
| Q187 | Dùng profile để cá nhân hóa. | §31.5; FR-PL-08/18 |
| Q188 | Platform Admin và Teacher tham gia script authoring/review theo quyền. | §31.3/31.5; role matrix |
| Q189 | AI có thể đề xuất sửa lesson/script khi dùng lại; Q159 sau đó giới hạn người khởi tạo là Platform Admin/Teacher. Parent chỉ được sửa draft/copy đã cấp quyền. | §31.2/31.4; FR-PL-03/17; Q159 |
| Q190 | Subject mismatch phải hỏi adult, cho sửa và gợi ý lại. | §31.5; FR-PL-19 |
| Q191 | Không reuse video; tạo video mới cho từng trẻ; script-following optional. | §31.5; FR-PL-17/18 |
| Q192 | Owner trả lời “có/cho phép” nhưng không nhớ câu hỏi gốc; không suy ra permission hoặc phạm vi mới. | §31.10(10); §31.14 |
| Q193 | Câu trả lời ban đầu nêu package school/Teacher/Parent; clarification Rev52 supersedes Teacher-account pool: Teacher usage tính vào quota school, Parent có quota riêng. Rev61 records temporary review units/prices; production price và quyền mua/cấp/phân bổ còn mở. | §31.7/31.13/31.14; BR-38/60; FR-PL-24; D-146 |
| Q194 | Tất cả workstream nêu ra đều nằm trong scope tài liệu. | §31.1–31.9 |
| Q195 | Có thể thay đổi/thêm; không sửa/xóa toàn bộ nếu chưa được phép. | §31.1; plan Rev25; preserved v2.2 snapshot |

Q185 giữ nguyên câu trả lời nguồn. Cách diễn đạt yêu cầu đích tại §31.5/UC-05/FR-T-10/FR-PL-20/AC-56 làm rõ cơ chế: hệ thống chọn ngẫu nhiên theo tập đủ điều kiện, Teacher xem và xác nhận child/context. Rev61 follow-up chọn equal probability, tối đa một reselect khi candidate stale, stop khi candidate set rỗng và không tạo/accept run/job/quota/claim trước confirmation. Q-01 còn OPEN cho exact eligibility/consent predicates, evidence schema, concurrency and API/UI error contracts; xem §§5.2, 31.10(4), 31.10.2.


## Rev31 backend implementation crosswalk (additive; pending SRS content review)

The v2.3 product-design baseline and requirements remain an unsigned draft. Rev31 implementation source adds three Lesson-owned support tables: `lesson.library_source_documents`, `lesson.library_document_revisions`, and `lesson.command_receipts`. They keep reusable-library uploads separate from occurrence-owned source documents and provide durable command idempotency. The current source-derived implementation crosswalk is 38 retained/refactored + 54 new = 92 active, plus 48 legacy/read-only = 140 projected physical mappings. This does not change product requirements, sign off the SRS/Data Table Register, or claim that the migration has run. See Data Table Register section 14.4 and EV-063-24.

### 31.12 Owner clarifications after Q147–Q195 (2026-11-06)

- **Q159 role resolution:** Platform Admin and Teacher may ask AI to draft lesson/activity suggestions. Parent may edit an authorized lesson draft only; Parent cannot start topic-based lesson-plan suggestion generation or publish a source version. Rev62's Parent activity preview is a distinct StoryRun-scoped suggestion from a captured/confirmed drawing subject, is not a lesson draft/catalog entry, does not publish content and does not change that role rule.
- **AI development direction:** Qwen3.5-VL is the current owner-selected model family for drawing understanding and structured story/storyboard development; SVG catalog + deterministic vector engine is the Rev66 target for line-sketch and lesson visuals, with structured Qwen drafts only when enabled and needed; FLUX.3 is superseded and not a fallback. Whisper is the speech-to-text direction; SAM 2.1 is optional for image segmentation. Modal is the inference-hosting direction. Exact checkpoints, runtime revisions, license/safety review, measured quality and costs are not approved by this documentation note.
- These clarifications do not remove Parent/Teacher workflows, relax the filtered-lesson input gate, or claim that Modal is wired end-to-end into the main API. The current build snapshot is §32.

### 31.13 Owner clarifications from Rev52 review (2026-11-06)

- “Admin nội dung” là permission của Platform Admin, không phải product role độc lập. Permission review/publish/moderate không cấp quyền xem profile/media trẻ.
- Platform Admin child-media access mặc định bị từ chối và chờ quy trình riêng được owner phê duyệt. Cho tới lúc đó, mọi request đều bị deny; approver, scope/purpose, expiry, audit detail và break-glass vẫn mở.
- Teacher video generation chỉ tiêu quota của school organization sở hữu occurrence; không có Teacher-account pool hay fallback sang pool riêng của Teacher. Parent account giữ quota riêng. Rev61 ghi các units/giá review tạm; production price và quyền mua/cấp/phân bổ vẫn mở.
- Current SRS/Data Table Register target count là 92 active + 48 legacy = 140 projected mappings; 89 + 48 = 137 là baseline lịch sử v2.3. Con số nào cũng không thay thế production inventory/DDL review.

<a id="srs-31-14"></a>
### 31.14 Owner clarifications from diagram-input review (2026-11-09)

The supplied review note uses O-01–O-17 labels; those labels are trace aliases for the 17 topics in §31.10, not replacements for existing Q/M/D IDs. The owner accepted the recommendations below in the conversation. These are target-policy selections for this unsigned SRS; they do not approve production configuration, physical schema, API contracts, diagram artifacts or implementation.

| Note reference | Owner-selected target | Residual boundary |
|---|---|---|
| O-01 | Age bands are 36–71, 72–107 and 108–120 months, versioned and snapshotted. | Legacy migration/backfill mechanics remain technical gates. |
| O-02 | Temporary review examples: Parent 2 included/month + top-up 5 for ₫249.000; School 30 included/month + top-up 50 for ₫1.990.000. Included expires end-of-month and top-up carries forward under BR-38. | Not production prices/config. Buyer/allocator, payment terms, exhausted response, terminal top-up expiry and commercial approval remain open. |
| O-03 | Parent lesson history is 30 days from first delivery/open; revoke/unpublish retains neutral metadata only and does not reopen content. | Data mapping and access implementation remain technical gates. |
| O-04 | Equal-probability eligible-child selection; Teacher confirmation; one reselect only for stale candidate; empty set stops; no run/job/quota/claim before confirmation. | Exact consent/eligibility rules, evidence, concurrency and response contracts remain open. |
| O-05 | Parent keeps preset script direction; Teacher keeps approved objective/activity/safety; adult confirms script before video. | Default enablement, override limits and revision pin remain open. |
| O-06 | Parent and School quota scopes remain separate; Teacher has no sub-pool/fallback; included usage precedes FIFO top-up; included expires end-of-month and top-up carries forward. | Purchase/allocation authority, payment/exhaustion contract, role-change behavior and terminal top-up expiry remain open. |
| O-07 | Teacher-authored PUBLIC requires School Manager approval; Platform Admin-authored PUBLIC requires independent review by another Platform Admin with Content Admin permission. | Review evidence/event mapping remains a technical gate. |
| O-08 | Parent Profile 0..n share grants; each grant targets one opaque Managed Profile; each Managed Profile has at most one active Parent link; named Teacher accepts; 90-day term; immediate revoke; Delivery Recipient is an occurrence snapshot. | Exact fields, physical ownership, renewal and class/school invitation remain open. |
| O-09 | AI visual/slide output stays DRAFT with provenance and reviewer gate; no PPTX/PDF export. | Asset owner, review criteria and publish authority for derived assets remain open. |
| O-10 | Q192 source question was not remembered. | “Yes/allowed” creates no new permission or scope until the original question is recovered. |
| O-11 | Child-media access remains denied by default for V1; a future exception is a separately approved workflow. | Future exception design remains open and does not block V1 deny behavior. |
| O-12 | Parent personal copy is reusable, PRIVATE, lineage-preserving and does not change published source; delete request has a 30-day recovery window. | Editable-field allowlist and retention after recovery remain open. |
| O-13 | Parent without a lesson preset must select one catalog-first main activity before story. The server filters activities from published/shared lesson versions the Parent may view; Qwen3.5 selects eligible request-scoped IDs using minimized profile/topic/drawing/narration context. If none is suitable, it may draft exactly three activities through the backend quality gate for adult selection. No artwork, raw audio or child/profile/account identifier is sent. After video, no-pin returns the run-pinned activity without catalog lookup; a lesson pin returns all activities from its exact version with the selected main activity marked. This Rev66 timing supersedes the earlier optional-preview rule. | FR-P-05/FR-PL-16; §31.17 |
| O-14 | Authorization is server-side by principal role, scope and permission version, deny-by-default. | Assignment persistence, resolver/cache/revoke mapping and force-close contract remain open. |
| O-15 | Accepted-not-queued/queued work is cancelled; running work is fenced and late results purged; READY/playable output keeps its immutable old pin; no automatic quota refund or extra sample claim. | Commands/receipts, reconciliation and purge evidence remain technical gates. |
| O-16 | Profiles aged 121–155 months cannot start a new accept/run; a run accepted before age 121 may complete using its accepted eligibility snapshot, subject to current authorization, safety and lifecycle controls. Existing draft remains read/delete only; notify once on detection and once when opening the draft. | Legacy draft edit/archive is not approved; migration/backfill mechanics remain open. |
| O-17 | Audit is metadata-only; retention target is 180 or 365 days by record type. | Type-to-duration mapping, field allowlist, audit authorization and physical schema remain open. |

### 31.15 Owner clarification — Parent image-first flow (2026-11-10)

This Rev62 clarification is based on the owner's direct instruction and supersedes only conflicting Parent flow details in Rev61. Topic and Parent Gallery lesson selection are optional; capture/upload of one child's paper drawing is mandatory before StoryRun creation and image analysis. The backend validates access to a selected lesson and pins its immutable version/hash. After VLM understanding and adult subject confirmation, the app may show a skippable activity preview from that exact lesson version or call a dedicated Qwen3.5 Modal workload with confirmed subject, visible features, age band and other allowlisted minimal context. It must not send the artwork, child's name, profile ID or Firebase identity to that workload. Preview failure/skip/unknown outcome cannot block story/video or trigger automatic retry. It is not Parent lesson-plan generation under Q159, does not create a catalog item and does not replace the pinned lesson's post-video activities. A no-preset run still has no post-video `learning_content` lookup or activity fallback. The activity-preview source/selection semantics in this Rev62 note were superseded by Rev63 §31.16; Rev66 §31.17 additionally makes selection of one main activity mandatory before story and defines no-pin playback. Accordingly, the earlier statement that preview skip/failure/unknown cannot block story/video is superseded for the required main-activity choice: an unavailable suggestion must not silently bypass adult selection. The optional line guide remains skippable and non-blocking to capture. Exact activity-selection recovery remains OPEN-TECHNICAL. The SRS remains unsigned; this note is not production/legal approval or runtime evidence.

### 31.16 Historical owner clarification — Parent catalog-first activity preview (2026-11-11; timing superseded by Rev66)

The owner clarified that Parent activity suggestions must use the existing catalog first and selected activities from published/shared lesson versions the Parent can access as the source. The backend retrieves the eligible, currently renderable candidate set using exact profile age and available topic/drawing-context metadata; a pinned lesson restricts candidates to its immutable version/hash. Qwen3.5 on Modal receives the bounded candidate data and minimized context available from the accepted profile and StoryRun: age band, allowed profile interest summary/tags, selected topic, adult-confirmed subject, VLM visible features and adult-confirmed narration/transcript when present. The worker receives no image bytes, raw audio, child name, profile ID or Firebase/account identity. For catalog matches, the model returns only request-scoped candidate IDs, order and short reasons; the backend validates membership and returns canonical activity content from its exact lesson version. If the candidate set is empty or Qwen3.5 judges that none is suitable, it may draft exactly three structured activities. The backend applies hard schema, complete-text, age, safety, outdoor, Montessori and duplicate-content checks; incomplete or otherwise rejected output fails closed and the Parent may skip. Generated proposals remain clearly marked, temporary, adult-reviewable drafts, are not catalog or lesson content, and do not mutate the pinned version or its post-video list. The static ACT demo catalog is not a Parent product source. Catalog-first selection is required before story; it cannot be silently skipped. For no-pin playback, return the run-pinned selected activity without a new catalog query. Rev66 §31.17 supersedes the earlier optional-preview/no-post-video-list policy. This clarification supersedes the conflicting catalog-free preview wording in Rev62. The SRS remains unsigned; catalog quality and measured quality remain open gates, not claims of runtime readiness.

For clarity, the historical phrase “Parent may skip” above means the adult may discard unusable draft suggestions; under Rev66/Rev67 it does not permit proceeding to story without selecting one main activity. The optional line guide remains separately skippable.

B1–B5 mean Data/Physical, State/Activity, API/Event/Sequence, Screen/Navigation and Class/Package readiness gates in §31.10.2. Owner acceptance applies to this review/checklist structure; it is not evidence that companion artifacts or technical contracts have been produced or reviewed.

### 31.17 Owner clarification — SVG guides, Parent activity timing and editable Teacher presentation (2026-11-13)

This amendment records the owner's direct product direction and supersedes only conflicting target statements in §§1–31 and older clarification notes. It does not delete the Rev57 baseline or historical decisions, approve the implementation plan, freeze APIs/schema, or sign off the SRS.

**Resolved product direction**

- **Remove FLUX from the target path.** Parent drawing guides and Teacher lesson illustrations target a curated, licensed SVG catalog plus a deterministic vector engine. The engine validates structured vector data, dependencies, bounds, sanitization, provenance and safety before serialization/rendering. Qwen may produce a structured vector draft only when the relevant capability is enabled and the catalog/source path is insufficient; the model must not return executable/free-form SVG, HTML or JavaScript. No silent FLUX fallback. This target does not prove current FLUX code or deployments were removed.
- **Parent flow:** topic and public/shared lesson are optional; a selected lesson remains the knowledge/presentation source. An optional line guide may precede drawing. Capturing/uploading one child's drawing remains mandatory. VLM checks the image against a selected topic/lesson; mismatch informs the adult and allows changing the topic or recapturing once. After recapture, use the VLM-recognized subject while keeping the pinned lesson as knowledge context. Adult confirms subject/context, then selects one main activity before script generation. Catalog-first suggestions use permitted profile/context and Parent-accessible published/shared lesson activities; a pinned lesson first supplies its exact-version activities. If none fits, AI may produce exactly three quality-gated drafts. A request for another set must exclude choices already shown or rejected. The selected activity is part of story context and is performed after the video. After playback, no-pin returns the run-pinned main activity without a new catalog query; a lesson pin returns every activity from the exact pinned version and marks the selected main activity. No additional activity list is generated automatically.
- **Teacher lesson presentation:** a lesson is an editable presentation, not only a generated sketch deck. Teacher can edit slide text, add/remove/reorder slides, upload image assets, place images/SVG and validated YouTube/Vimeo embeds on chosen slides, and preview/reorder media. AI-generated SVG illustration is optional and remains a draft for Teacher review. Teacher submits the lesson; School Manager reviews school-public scope, and Platform Admin reviews platform-public scope. Published revisions are immutable; editing creates a new draft revision. Story video remains a new child-specific generation and the existing LTX-2.5 pipeline is unchanged.
- **Age remains 36–120 months** with the current versioned age bands. Parent and Teacher guide length is adaptive **4–8 progressive steps** that build from basic strokes toward a recognizable subject. Guide is optional; disabled, skipped, unavailable, timeout, no-source and quality-rejected paths do not block mandatory capture.

**Technical gates retained as OPEN**

| Gate | Unresolved detail |
|---|---|
| Source classification and Parent fallback | Map `STROKE_READY`, `REQUIRES_MANUAL_AUTHORING`, `STATIC_ONLY` and `REJECTED` to versioned API/UI outcomes. Candidate safe rule: Parent has no manual authoring tool; rejected SVG is never rendered; unavailable-guide states never block mandatory capture. Classification names and exact fallback are not frozen. |
| Quality review/adjudication | Reviewer count, score aggregation, disagreement handling and adjudication are undecided. Rev83.3's proposed 4/5 recognizability/teachability floor and 2-point disagreement threshold are suggestions only, not approved requirements. |
| Authoring/revision semantics | Decide supported guide edits, local undo/redo history, server draft revisions, published revision immutability, autosave concurrency/conflict handling and idempotency before API freeze. |
| Renderer/performance evidence | Define browser/renderer versions, device classes, path/asset limits, sample size, cold/warm measurements and SLO. Emulator functional behavior and low-end physical Android performance are separate evidence categories; no numeric target is approved. |
| API and persistence alignment | Rev83.3 API V2 routes remain proposals, not mounted contracts. Reconcile version, request/response/job/error lifecycle, guide/presentation revision and asset ownership, DTR, DDL and migration before implementation; do not infer entities/routes from the plan or current source. |
| Failure recovery | Distinguish capability disabled, catalog miss, worker unavailable, timeout and quality rejection. Parent capture must remain available and Teacher can continue lesson editing. Exact status codes, retries and recovery UI remain open. |

The current root source review found legacy FLUX worker code and v1 direct-Modal API routes, while the Rev83.3 worktree uses an older Rev60 SRS copy. These are recorded only as source observations in the Rev83.3 pre-implementation audit evidence; they do not change this target or prove live Modal deployment status. The companion Data Table Register remains v2.5-draft and is not yet aligned with editable slide structure, SVG guide revisions or this Rev66 target. Physical/logical persistence mapping and API V2 remain blockers. Rev83.3 remains DRAFT for implementation; this documentation update is not implementation approval. The SRS remains unsigned.

<a id="srs-31-18"></a>
### 31.18 Rev65 checklist response against current authority (2026-11-13)

This section records review of the owner-supplied seven-diagram checklist dated 2026-11-13, which labels its own baseline Rev65. The checklist is review input, not the current SRS, a companion contract, proof that a catalog is populated, or diagram sign-off. The current product authority is this v2.7-draft Rev67 SRS, based on owner-selected Rev57 with local amendments through Rev67; it remains unsigned. The related Rev83.3 implementation proposal remains DRAFT and its worktree contains an older Rev60 SRS copy.

#### Resolution of material Rev65/Rev66 differences

| Checklist statement | Current Rev67 interpretation |
|---|---|
| Parent activity “preview” may be skipped or fail without blocking story/video. | Rev66 requires the adult to choose one main activity after subject/context confirmation and before script/story creation. Catalog lookup or draft-generation failure cannot silently skip that required choice. Story cannot advance until a choice is recorded. Exact retry/manual recovery UI and API remain OPEN-TECHNICAL. This does not change the separate optional, skippable line guide. |
| No-preset Parent has no activity result after playback. | No new catalog query or supplemental activity list is allowed after playback. The selected main activity already pinned in the run is returned. This is not a post-video catalog fallback. With an exact lesson pin, return activities from that exact pinned version and mark the selected main activity; recheck current access before protected content is returned. |
| Pinned lesson is the only meaningful Parent activity source. | Before story, a pinned lesson restricts candidates to its exact version/hash. Without a pin, the backend may use currently accessible PUBLIC/SHARED lesson versions. Both paths require the adult to select one main activity before story. |
| Checklist is labeled Rev65. | Retain the label as provenance only. Reconcile conflicts to current §§5.1, 31.10.2–31.10.3 and 31.17, not the review note. |

#### Answers to the checklist’s requested work

| Checklist area | Answer under Rev67 | Readiness/evidence boundary |
|---|---|---|
| §0 baseline and seven gates | Use the owner-selected Rev57 source and canonical Rev67. Keep A01–A10, S01–S12 and AC-67 as review indexes. D04/D05/D06/D07/D09/D11 remain PARTIAL; D08 Logical PARTIAL; D08 Physical BLOCKED. | Scenario names and checklists are not populated diagram-input evidence. The Rev66 source audit is source-only; no diagram is asserted complete. |
| §1 D04 Activity, A01–A10 | Retain all ten scenario families in §31.10.3. A01/A02 follow Rev66: optional topic/lesson/guide, mandatory capture, mismatch handling with at most one recapture, adult subject/context confirmation, one required main activity before story, separate compute/quota admission, safety/playback and current-access checks. Teacher confirmation, sharing, review, admission, supersession, lifecycle and payment branches remain as resolved/open in §§5, 31.10 and 31.10.3. | Policy descriptions exist; detailed step IDs, API/event/receipt, owner writes, full guards, timeout/retry and compensation records are not populated. D04 stays PARTIAL. |
| §2 D05 Sequence, S01–S12 | Retain twelve message-group families. S01/S02 now carry Rev66 ordering and required activity selection; S03–S12 remain as listed in §31.10.3. | Exact message IDs, versioned schemas, endpoint/error envelopes, mounted proof, owner receipts and callback/reconciliation contracts are missing or unverified. D05 stays PARTIAL. |
| §3 D06 Screen Flow | Cover Parent Android, Teacher Web, School Manager, Platform Admin/content administration and operator surfaces only where applicable. Use actual screen IDs/routes only when design/source supplies them. | Screen catalogue, navigation edges, role/data scope and error behavior require design/source review. D06 stays PARTIAL. |
| §4 D07 Class | Any class/port candidate needs owner, layer, types/signatures, invariant, cardinality and source trace. ORM/source classes alone are not approved domain contracts. | Complete `CLASS_CONTRACTS` and `CLASS_RELATIONS` are not established. D07 stays PARTIAL. |
| §5 D08 ERD | Keep logical and physical views separate. 92 active plus 48 legacy/read-only are target mappings, not a verified live table count. | Logical keys/attributes/cardinality need same-baseline alignment. DTR v2.5-draft is not aligned with Rev66; reviewed same-baseline DDL/dictionary/crosswalk is unavailable. D08 Logical PARTIAL; Physical BLOCKED. |
| §6 D09 State Machine | Use only state names sourced in §6.1.1 or an approved contract; keep StoryRun, VideoGeneration, AI Job, billing and review lifecycles separate. | Transition rows for source state/event/guard/owner effect/receipt/error/timer/revoke/cancel/reconcile remain incomplete. Do not invent states. D09 stays PARTIAL. |
| §7 D11 Package | Separate proposed target ownership from exact-commit AS-BUILT imports, DI, routers, workers and event-consumer evidence. Historical `canvas_render` cycle is only a scan lead. | Rev83.3 reviewed selected source surfaces but did not establish a complete current import/cycle scan or every mounted composition. D11 stays PARTIAL. |
| §8 open decisions | Keep unresolved quota/commercial scope, random-child eligibility/concurrency, script-following policy, sharing fields/renewal, AI visual review, Q192 source, personal-copy details, role persistence, legacy migration, audit map and Parent activity-selection recovery open where §31.10 says so. Do not reopen resolved policies. | Owner-policy status and technical readiness differ. `RESOLVED` does not prove implementation. |
| §9 AC-67 | Map ten cases across the seven views, with O-17 audit checks cross-cutting. | The SRS states required case coverage but does not supply detailed record IDs to close AC-67. It remains OPEN until evidence provides real record IDs or a sourced `N/A`. |
| §10 templates | Use requested fields as completeness criteria; populate sourced policy facts and source paths, and mark unsupported values `OPEN`, `OPEN-TECHNICAL`, `NOT VERIFIED` or `BLOCKED`. | A filled template is not a contract/source artifact. Do not invent routes, fields, classes, states or DDL. |
| §11 work order | Freeze SRS/DTR/ADR sources; align data (B1), state/activity (B2), API/event/sequence (B3), screen/navigation (B4), class/package (B5); then close AC-67 and assess readiness. | B1 physical baseline is currently the hard blocker. This SRS note closes no gate. |
| §12 requested deliverables | The accompanying Rev84 evidence directory contains a baseline register, readiness answer, partial scenario/message/state/screen/class/data/package/AC-67 artifacts and open-blocker register. | These are traceable review inputs, not diagrams or sign-offs. Missing technical records remain OPEN/BLOCKED. |

For Parent activities, catalog-first privacy, exact-pin boundaries, the three-draft ceiling and backend validation remain in force. “Skip/no-fit/error/unknown” are distinct: the line guide is optional; a catalog miss may permit exactly three quality-gated drafts; failure/unknown while selecting the required main activity cannot authorize story generation without an adult selection. Recovery details remain OPEN-TECHNICAL.

The Rev83.3 source-only report records selected source observations at its stated root checkout and file hashes. It found legacy FLUX source and current v1 routes in inspected files, but did not prove live Modal state, full package-cycle closure, database contents or production behavior. The proposal worktree’s Rev60 SRS, the v2.5-draft Data Table Register and the environment-specific §32 snapshot do not override Rev67 requirements. No diagrams were drawn or signed off; D04/D05/D06/D07/D09/D11 remain PARTIAL, D08 Logical remains PARTIAL and D08 Physical remains BLOCKED. No formal SRS sign-off is implied. See `evidence/EV-063-92_REV65_CHECKLIST_RESPONSE_REV67_20261113/`.
<a id="srs-31-19"></a>
### 31.19 Rev68 — owner-approved technical defaults and M1/M2 boundary

On 2026-11-13, the owner approved the Rev83.3 M0 defaults and authorized implementation of M1 and M2 only through Plan Rev83.4. This amendment updates technical acceptance defaults and the approved implementation boundary; it does not sign the SRS or declare any implementation, data migration, API, renderer performance, catalog review, or workflow acceptance complete.

- Progressive drawing guides contain 4–8 ordered stages. The minimum of four independent, safely canonicalized drawable elements is a structural eligibility threshold only. It is not a measure of recognizability, teachability, or age fit.
- Educator review is bound to the exact source asset hash and revision. Platform Admin curation/permission to group paths is a separate recorded decision. A model or structural classifier cannot supply either decision.
- Guide editing is copy-on-write and immutable. Local Undo/Redo does not mutate canonical source geometry. Autosave debounce is 1.5 seconds. A stale expected revision returns `409`; the client preserves its edit buffer and offers reload, resolve, or separate draft.
- Pilot renderer acceptance targets are sustained ≥30 FPS, p95 first visible render ≤500 ms after decoded guide data is available, p95 step transition ≤150 ms, and renderer memory growth ≤64 MiB. These remain target thresholds until measured on a named low-end Android emulator and supported Teacher browser; this amendment contains no measurement.
- SVG path grouping, topic-to-guide synthesis, and static SVG illustration each have an independent capability flag, OFF by default. A disabled capability returns `CAPABILITY_DISABLED`, with zero Modal dispatch and no cross-capability or FLUX fallback. Catalog lookup, deterministic rendering, and manual authoring remain independent of these flags.
- A later M3-B quality gate requires 100% of safety/schema/render hard gates and at least 80% of all cases scoring ≥4/5 on both recognizability and teachability from two educator reviews. A disagreement of at least two points on either criterion requires a third reviewer for adjudication. These thresholds do not authorize or execute the M3-B POC.
- Only M1 (safe catalog/source readiness and deterministic renderer) and M2 (manual guide authoring and progressive Parent/Teacher playback) are authorized for source implementation by the owner response and Plan Rev83.4. No Modal inference/deployment/warmup, AI activation, M3-A/M3-B, video work, or FLUX removal is authorized by this decision.
- Persistence must reuse the existing immutable Lesson version and Core Asset ownership where their contracts suffice. Any migration is limited to a gap demonstrated in the Rev68 crosswalk and requires its separately recorded DTR/DDL details. The route/API contract and final physical mapping remain subject to implementation review; no unrecorded table/field is implied by this SRS note.

The FEAT-063 v2.7-draft SRS remains unsigned. See `plan/PLAN_REV83_4_M1_M2_APPROVED_IMPLEMENTATION_20261113.md`, `artifacts/REV68_SVG_CATALOG_PERSISTENCE_CROSSWALK.md`, and `approvals/TASK_APPROVAL.md` for scope and traceability. These records do not close the seven diagram-readiness gates or replace the companion Data Table Register.

<a id="srs-32"></a>
## 32. Trạng thái triển khai hiện tại (as-built snapshot — 2026-11-06)

§§32.1–32.4 ghi quan sát local/runtime/Modal từ Rev43. §32.5 là source review Rev45 trên working tree local; §32.6 là source review `origin/dev` Rev51; §32.7 là source-only verification Rev57 tại commit `ae5707ca188d01d9719ed959b62d768ae927912d`; §32.8 là snapshot CI Rev58. Các snapshot giữ baseline/ngày riêng và không được gộp thành một trạng thái runtime. Phần 32 không thay thế yêu cầu đích tại §§1–31, không đại diện production, và không biến code/config/deployment riêng lẻ thành bằng chứng đã đạt acceptance criteria.

### 32.1 Backend, API và lưu trữ

| Phạm vi | Trạng thái quan sát | Ý nghĩa |
|---|---|---|
| API local đang chạy | OpenAPI đọc từ `http://127.0.0.1:8000/openapi.json`: 111 path / 124 operation. Các nhóm route gồm BE1 runtime, child preferences, session/media/understanding và context/activity suggestion flows, renderer, story-video/whiteboard-video và Lesson Library. | Đây là runtime local tại thời điểm kiểm tra, không phải toàn bộ dedicated Parent APIs theo SRS; chi tiết route và mục đích từng API ở API Contract Catalog Rev37. |
| AI Jobs API | Router implementation tồn tại nhưng chỉ được mount trong fixture app; không xuất hiện trong OpenAPI của main app. | AI job persistence/orchestration target chưa được đưa vào main API runtime. |
| Lesson Library | CRUD lesson, source upload/revision, version, grant/invitation, parent group và moderation routes xuất hiện trong main OpenAPI. | API presence không chứng minh mọi SRS workflow (billing, publication review, lesson execution, feedback) đã hoàn chỉnh. |
| Local PostgreSQL | Alembic revision `20261028_ll_0001`; 41 application tables: 34 trong `public`, 7 trong `lesson`; ngoài ra có `alembic_version`. | Đây là database local được đọc chỉ; không phải production inventory. Tên từng bảng nằm trong Data Table Register §14.5 và EV-063-33. |
| Schema target | Data Table Register vẫn mô tả 92 active + 48 legacy/read-only = 140 bảng vật lý dự kiến. | Target source-derived count và local database count là hai phép đo khác nhau; không suy ra migration đã hoàn tất từ target count. |

### 32.2 AI pipeline và Modal development deployment

Backend code có provider adapters từ các slice trước, gồm Lightning-prefixed vision, ASR, activity-ranking, segmentation và story-video adapters. Trong code composition được rà soát, chưa thấy adapter nối main backend trực tiếp tới ba Modal dev apps dưới đây. Vì vậy, phân biệt “function/app thấy trên dashboard” với “request đi xuyên backend tới kết quả” là bắt buộc.

| Capability | Hướng hiện tại | Bằng chứng/trạng thái tại Rev43 | Còn cần xác minh |
|---|---|---|---|
| Hiểu tranh và tạo structured story/storyboard | Qwen3.5-VL trên Modal | Owner chọn Qwen3.5-VL; Modal dashboard có function tên `generate-story-and-storyboard`. | Model/checkpoint chính xác không hiện trên ảnh dashboard; backend dispatch, schema conformance, safety, latency và end-to-end API chưa được xác nhận bởi Rev43. |
| Parent line-sketch / lesson visual | FLUX.3 trên Modal | Dashboard có app `sketch2life-srs23-flux-image-dev`, function `generate-line-sketch-guide-candidate`, và function tải model đã pin. | Checkpoint/variant, thành công theo contract, safety review và kết nối main backend chưa được chứng minh ở lần tài liệu này. |
| Ý tưởng giọng nói → text | Whisper/faster-whisper trên Modal | Dashboard có `transcribe-vietnamese-audio`. | Model revision/độ chính xác tiếng Việt; người lớn vẫn phải xác nhận transcript trước story generation. |
| Lời kể tiếng Việt | Modal TTS | Dashboard có `synthesize-vietnamese-narration`. | TTS checkpoint, chất lượng/độ trễ và audio/subtitle timing chưa được xác nhận. |
| Tách vùng tranh | SAM 2.1 tùy chọn | Backend có SAM 2.1 runtime/adapter từ các slice trước; chưa xác nhận deployment SAM 2.1 trên Modal. | Modal worker, mask benchmark, crop fallback và preservation/lineage. Không bắt buộc để tiếp tục luồng khi segmentation không đạt. |
| Video | LTX-2.5/Modal L40S vẫn là SRS target riêng | Dashboard screenshot cho thấy app `sketch2life-srs23-video-candidate-dev` với worker `generate-wan-video-candidate`; video được để sau trong đợt kiểm tra hiện tại. | WAN là candidate thử nghiệm, không thay LTX-2.5 thành quyết định cuối; chưa chứng minh video end-to-end, consistency, TTS timing, safety hay playback theo SRS. |

Dashboard observation đến từ ảnh do owner cung cấp. Tên function, trạng thái “live” và nhãn GPU chỉ ghi nhận deployment UI tại ảnh chụp; chúng không xác nhận model card, quyền truy cập, request thành công, độ chính xác, chi phí thực tế hoặc kết nối runtime với API. Rev43 không gọi inference, không khởi động GPU và không kiểm tra secrets.

### 32.3 Phân biệt mức hoàn thành

- **Có code/API:** backend có các route và provider adapters được liệt kê ở trên; OpenAPI xác nhận route được expose, nhưng Rev43 không xác nhận từng flow chạy thành công hay đang dispatch tới Modal.
- **Có local persistence:** BE1/Core và Lesson Library có mặt trong database local với migration head đã nêu.
- **Có Modal dev deployment quan sát được:** ba app dev trong bảng AI; đây chưa phải bằng chứng đã tích hợp vào backend main app.
- **Chưa được xác nhận hoàn chỉnh:** AI Jobs main runtime/persistence, end-to-end route từ backend tới các Modal app, full video pipeline LTX-2.5, SAM 2.1 on Modal, production safety/licensing, billing/quota và mọi target table vắng mặt trong local DB snapshot.

Các mục “chưa xác nhận” là trạng thái triển khai, không phải hủy yêu cầu. Parent và Teacher flow, lesson platform, phân quyền/chia sẻ, quota, kiểm duyệt và video pipeline vẫn là target SRS cho tới khi có quyết định owner mới được ghi rõ.

### 32.4 Database tables và ranh giới truy cập AI

AI worker/Modal function không được kết nối trực tiếp vào PostgreSQL. Theo kiến trúc đích, backend có trách nhiệm kiểm tra quyền/consent, đọc dữ kiện cần thiết, lọc payload và chuyển đúng asset/context đã allowlist cho provider. Database table được dùng bởi domain/backend không đồng nghĩa model trực tiếp đọc bảng đó.

| Nhóm dữ liệu local hiện có | Bảng liên quan | Quan hệ dự kiến với AI | Điều Rev43 xác nhận |
|---|---|---|---|
| Hồ sơ/consent/ngữ cảnh lớp | `public.be1_managed_profiles`, `public.be1_consent_records`, `public.be1_observations` | Backend có thể dùng để kiểm tra eligibility và dựng facts tối thiểu đã duyệt; không gửi toàn bộ hồ sơ hay consent record cho model. | Các bảng tồn tại; không có query trace chứng minh chúng được đọc cho từng AI request. |
| Asset/upload | `public.core_asset_metadata`, `public.core_upload_sessions`, `public.core_upload_parts` | Backend resolve/hash/lineage asset và gửi asset bytes/ref được allowlist; model không nhận DB credentials. | Các bảng tồn tại; không khẳng định mọi ảnh/âm thanh trong demo đã được lưu qua các bảng này. |
| Lesson source và version | `lesson.library_items`, `lesson.library_versions`, `lesson.version_activities`, `lesson.library_source_documents`, `lesson.library_document_revisions`, `lesson.command_receipts` | AI chỉ được nhận trường lesson đã trích xuất, lọc và người lớn rà soát; không nhận nguyên giáo án/file gốc. | Các bảng tồn tại; Lesson Library routes được mount; chưa xác nhận AI lesson-generation đã dùng chúng end-to-end. |
| AI job, policy, story và billing persistence target | `ai_jobs.*`, `ai_policy.*`, `story.*`, `parent.*`, `billing.*`, `notifications.*` | Dự kiến backend quản lý job/attempt, admission/reservation, story revisions/assets, quota và notifications; provider chỉ trả output theo contract. | Các schema/bảng này chưa có trong database local được kiểm tra; không có bằng chứng persisted job/attempt/quota/story record tại DB này. |

Rev43 không quan sát SQL query trace, row-level activity hoặc telemetry theo AI request. Vì vậy, không thể kết luận bảng nào đang được model “sử dụng” trực tiếp. Kết luận chính xác hiện tại: **không có AI-owned persistence tables trong local DB snapshot; một số bảng Core/BE1/Lesson có thể được backend dùng làm nguồn/đích theo kiến trúc, nhưng lượt đọc/ghi thực tế cần instrument/test riêng.** Ma trận owner và chi tiết nằm ở Data Table Register §14.6.

<a id="srs-32-5"></a>
### 32.5 Rà soát mã nguồn và đối chiếu yêu cầu đích (Rev45 — 2026-11-06)

Các hàng dưới đây ghi nhận mã nguồn hiện có tại thời điểm rà soát. Mục `đã có trong source` không đồng nghĩa tính năng đã chạy được, đã qua acceptance, hoặc đã được chọn làm thiết kế production.

| Thành phần | Quan sát mã nguồn hiện tại | Liên hệ với yêu cầu đích trong SRS | Giới hạn bằng chứng |
|---|---|---|---|
| Parent Android | `apps/mobile` pin React Native 0.87/TypeScript; README gọi đây là ranh giới client đang phát triển nhưng `AppRoot` hiện mount luồng chỉ dùng fixture, đề xuất AI xác định sẵn và tranh tổng hợp. | Parent Android vẫn là mục tiêu; luồng Parent gắn API/provider chưa hoàn tất trong client này. | Chỉ đọc package/README; không build hoặc chạy app ở Rev45. |
| Parent demo/tham khảo | `apps/ui-mobile` dùng Expo 52/RN 0.76.9 và tài liệu hóa FEAT-018/030 với session trong tiến trình, media tổng hợp, Lightning demo lane; `apps/parent-web` tự ghi nhận là tham khảo lịch sử không hoạt động. | Không dùng UI/demo hoặc Lightning integration cũ để thay yêu cầu Parent Android/Modal direction trong SRS. | Chỉ đọc tài liệu/package; không kiểm tra thiết bị hoặc provider ở Rev45. |
| Teacher web | `apps/teacher-ui` là React 19/Vite 8.3 web app; README mô tả console Teacher/Guide. | Web là target cho Teacher; SRS workflow Lesson/occurrence/Sketch Deck vẫn cần hoàn thiện và nghiệm thu theo API/domain contracts. | Chỉ package/README/source boundary được rà trong Rev45; không tuyên bố toàn bộ UX/API flow hoàn chỉnh. |
| Ghép route backend | FastAPI composition root mount health + BE1 runtime, demo child/session/media/renderer/story-video routers và Lesson Library. | Các nhóm API này có mức hoàn thiện và phạm vi khác nhau; dùng `API_INVENTORY`/`API_CONTRACT_CATALOG` làm bảng đối chiếu, không coi toàn bộ OpenAPI là yêu cầu đích đã nghiệm thu. | OpenAPI Rev43 ghi nhận 111 path/124 operation. Rev45 không khởi động lại API; các thay đổi mã nguồn sau snapshot có thể làm OpenAPI khác. |
| AI Jobs | Router/domain/application/infrastructure code có mặt; `ai_jobs` router không được mount trong main app composition, chỉ xuất hiện trong fixture composition theo Rev43. | Durable AI Jobs vẫn là architecture target cho retry/admission/reconciliation; route/source presence chưa chứng minh main runtime đã có durable job orchestration. | Source composition + Rev43 evidence; không chạy worker/job. |
| AI/provider adapters | Backend còn adapter demo/lịch sử dùng Lightning và runtime SAM 2.1; Modal dev dashboard đã ghi riêng tại §32.2. Rev43 không thấy adapter nối trực tiếp API chính tới các Modal dev app. | Hướng phát triển sản phẩm là Modal + Qwen3.5-VL/FLUX.3/Whisper, SAM 2.1 tùy chọn. Giữ ranh giới adapter/provider ở backend; không đưa credentials/endpoint vào mobile. | Rev45 không gọi Modal/Lightning, không đọc secret, không chạy benchmark hoặc request tích hợp. |
| Upload media có giới hạn | Diff trong working tree thêm response 413 cho image/audio tại `/v1/sessions/{id}/media/*`; middleware trả `MobileWorkflowResultV1` với `MEDIA.UPLOAD_TOO_LARGE` hoặc `MEDIA.AUDIO_TOO_LARGE`. Storage-example trả `REQUEST_TOO_LARGE`. Router/service demo giới hạn ảnh 5.000.000 bytes và audio 20.000.000 bytes; middleware giới hạn tổng multipart body. | Đây là contract của demo/route tạm thời; không thay yêu cầu upload resumable, bền vững, quarantine/AV-clean của target. Khi tích hợp client phải ánh xạ mã lỗi theo contract của từng API surface. | Patch chưa build/chạy ở Rev45; response chỉ được đọc từ source, không ghi là đã xác minh runtime. |
| Build context của Compose | Diff working tree đổi API/minio-init sang build context từ repository root; Dockerfile copy backend, activity catalog, generated visual files và renderer demo bundle vào image. | Đây là cách đóng gói môi trường phát triển, không phải topology production đã chốt; quy tắc approval/provenance của asset vẫn áp dụng. | Rev45 chưa chạy Docker build/Compose; các thay đổi này mới được quan sát trong working tree. |
| Data persistence | Rev43 read-only local snapshot: Alembic `20261028_ll_0001`, 41 application tables (34 `public`, 7 `lesson`). Rev31 source crosswalk: 92 active + 48 legacy = 140 projected. | Hai số này không thay SRS v2.3 design baseline 89 active + 48 legacy = 137 và không phải production inventory. | Chỉ local DB snapshot ngày 2026-11-06; production inventory/migration rehearsal vẫn là OI-11. |

#### Kết luận hòa giải

1. Yêu cầu đích vẫn là Parent Android + Teacher web, nền tảng lesson Montessori, ownership tài khoản/hồ sơ tách biệt, contract có version, mỗi story/video run chỉ có một trẻ, các cổng privacy/safety và modular monolith trước. Các module BE1/classroom/demo hiện có không tự mở rộng phạm vi sản phẩm.
2. Hướng phát triển AI owner chọn đã được thống nhất trong §§2, 6, 9 và 31. Adapter/deployment riêng lẻ trong mã nguồn không đổi yêu cầu đích; chỉ quyết định owner/ADR cùng bằng chứng phù hợp mới có thể thay model video, production provider hoặc stack.
3. Code/API hiện gồm nền tảng, demo và các feature slice ở mức hoàn thiện khác nhau. Các phần còn thiếu gồm AI Jobs trong main runtime, dispatch Modal end-to-end, hoàn thiện luồng Parent/Teacher, quyết định vòng đời route cũ, và xác minh dữ liệu/privacy/license/cost/video cho production. Đây là khoảng trống triển khai, không phải lý do xóa requirement.
4. Rev45 rà soát working tree local; Rev51 bổ sung source-only đối chiếu fetched `origin/dev`. Không chạy test/build, database query, API runtime, inference/provider hoặc deployment trong các lượt rà soát này. Kết quả test/runtime có trước được dẫn đúng theo evidence riêng và không được coi là nghiệm thu toàn bộ target.

<a id="srs-32-6"></a>
### 32.6 Source review trên `origin/dev` hiện hành (Rev51 — 2026-11-06)

Rev51 đọc source tree tại commit `4749451080f49243464d40a464b8f83a03ae77bb` sau lần fast-forward/merge đã ghi trong EV-063-54. Đây là kiểm tra tĩnh source/config và evidence có sẵn; không tái chạy API, database, test suite, Modal inference hoặc deployment. Mục này bổ sung §32.5 local working-tree review và các quan sát Rev43, không sửa yêu cầu sản phẩm.

| Surface | Quan sát source/evidence tại Rev51 | Ý nghĩa đối với target | Giới hạn |
|---|---|---|---|
| Main FastAPI composition | `backend/src/sketch2life/interfaces/http/router_composition.py` ghép health + BE1, demo child/session/media/renderer/story-video và Lesson Library. `ai_jobs` và StoryRun-lite không được mount trong composition này. | Code sản phẩm main app chưa cung cấp luồng AI target đầy đủ hoặc durable AI Jobs qua API chính. Việc có router/service/provider adapter trong source không chứng minh route được mount. | Chỉ đọc source. Evidence API đã ghi main OpenAPI 24 operations/17 path templates; Rev51 không khởi động API hay tái sinh OpenAPI. |
| StoryRun-lite API riêng | `interfaces/http/story_run_lite_app.py` tạo app riêng và mount `routers/story_run_lite.py`. Source/evidence mô tả 13 operation trên 12 path; upload asset dispatch drawing analysis và tạo story revision dispatch story generation qua FastAPI `BackgroundTasks`. | Đây là fixture/demo integration riêng, không thay Parent API đích, authenticated tenant/consent boundary, shared job polling hoặc durable outbox/AI Jobs target. | Không gọi API trong Rev51. Các operation và hành vi được dẫn từ contract/evidence đã có; không khẳng định trạng thái live. |
| Modal drawing adapter | `infrastructure/ai/modal_function_client.py` dùng Modal SDK `Function.from_name`; `infrastructure/story_run_lite/photo_bridge.py` tạo client và gọi workload `drawing.analyze`. | Có một đường source integration cho drawing trong app StoryRun-lite riêng. Nó không chứng minh main app route, production credentials, durable dispatch hoặc kết quả an toàn/đúng. | Chỉ đọc source. Không đọc secret, gửi request hay gọi Modal ở Rev51. |
| AI Jobs | `routers/ai_jobs.py` và domain/application/infrastructure code có trong repository nhưng không được include bởi `router_composition.py`. | Durable job admission, retry, reconciliation, authorization và polling vẫn là target gap ở main API; không đồng nhất StoryRun-lite background tasks với AI Jobs persistence. | Route/runtime/database không được tái kiểm tra. |
| Development model profile | Source/config pin Qwen `Qwen/Qwen3.5-9B` revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a` với Transformers 5.22.1; FLUX.3 Image Klein/PUP IDs và revisions được ghi trong Modal worker/workload registry. Registry nói đây là dev profiles và mọi workload vẫn disabled. | Các chi tiết này ghi nhận development implementation, không khóa checkpoint/product stack hoặc production model. SRS vẫn giữ Qwen3.5-VL, FLUX.3, Whisper và SAM 2.1 tùy chọn ở đúng vai trò đã chốt; các gate license/quality/cost/safety/serving còn mở. | Không tải model hoặc gọi worker trong Rev51. Existing Rev44–46 evidence có kết quả tổng hợp nhưng không xác nhận product API end-to-end. |
| Speech, visual và video workers | `deployment/modal/srs_v23/` chứa Qwen/language-audio, FLUX.3 và WAN candidate apps. Evidence Rev44–46 ghi ASR/TTS/story/Teacher Deck thử nghiệm; FLUX từng bị chặn bởi HF Secret; video chưa được gọi. LTX-2.5 vẫn là SRS video target theo Q144, WAN vẫn là candidate. | Synthetic worker success hoặc module file không đồng nghĩa luồng Parent/Teacher production đã hoàn thiện; không thay LTX target bằng WAN. | Chỉ dùng source và evidence có sẵn; không kiểm tra credential, GPU, inference hoặc kết quả mới trong Rev51. |
| API và database snapshots | Evidence hiện hành của AI API coverage ghi main OpenAPI 24/17 và StoryRun-lite 13/12; local DB 41 bảng vẫn là snapshot Rev43 riêng. | Đây là các mốc theo môi trường/evidence khác nhau, không phải target count, migration completion hay production inventory. | Rev51 không tái chạy OpenAPI, query DB hoặc migration. |

Source/evidence được đối chiếu: `router_composition.py`, `story_run_lite_app.py`, `routers/story_run_lite.py`, `infrastructure/ai/modal_function_client.py`, `infrastructure/story_run_lite/photo_bridge.py`, `routers/ai_jobs.py`, `deployment/modal/srs_v23/workloads.json`, `AI_API_QWEN35_MODAL_VALIDATION_20261105.md`, `AI_NONVIDEO_AI_END_TO_END_20261105.md`, `AI_QWEN35_FLUX_REV46A_COMPLETION_20261105.md`, và `EV-063-54_DEV_HISTORY_AND_SRS_MERGE_20261106.md`. EV-063-56 ghi commit nguồn, đường dẫn, phân loại, giới hạn và việc không chạy lại runtime.

<a id="srs-32-7"></a>
### 32.7 Rev57 source-only verification at docs baseline

On 2026-11-09, a read-only source review was performed at repository commit ae5707ca188d01d9719ed959b62d768ae927912d, the fetched Rev56 baseline. The main FastAPI composition includes the configured health, BE1, demo/story and Lesson Library routers in router_composition.py; routers/ai_jobs.py exists in source but is not included by that composition. This is source-level mount inspection only, not a live route/OpenAPI check. Source trees for learning_content, ai_jobs and ai_policy are present; their existence does not prove every target port or workflow is integrated.

A static Python AST import scan covered 559 modules under backend/src/sketch2life. It found no outward-layer import edges under the checked domain/application rule and one import cycle between infrastructure.canvas_render and infrastructure.canvas_render.renderer. The cycle is a source finding for G10, not a product decision or evidence of runtime failure; package readiness stays blocked until reviewed. The scan did not evaluate dynamic imports, dependency-injection wiring or cross-language package graphs.

No live database, production schema, migration, API process, provider, test suite or deployment was inspected or run in Rev57. Section 32.7 supplements but does not replace the historical, environment-specific observations in §§32.1–32.6. §§1–31 remain the v2.7-draft target; no SRS/DTR sign-off is implied.


<a id="srs-32-8"></a>
### 32.8 CI hiện tại và luồng phát hành đích (source-only snapshot — Rev58, 2026-11-09)

- `.github/workflows/ci.yml` khai báo GitHub Actions triggers cho `push` và `pull_request`, với các job repository policy, backend contract/unit tests và active UI checks.
- Repository policy job dùng Python 3.12.14 để gọi `validate_harness.py`, `validate_skeleton.py`, `validate_architecture.py`, `validate_repository_security.py` và `validate_team_allocation.py`.
- Backend job cài dependencies theo lockfile và khai báo contract tests `test_app_composition.py`, `test_session_http_api.py`; unit tests `test_classroom_stage_policy.py`, `test_session_lock_pool.py`; và integration test `test_be1_postgres_api.py`.
- Active UI matrix gồm Child UI, Teacher UI và Admin UI; mỗi entry dùng Node 24.15.0, `npm ci` và `npm run check`.
- Commit `18150aa5` ghi nhận sửa CI để pin Node 24.15.0 và khôi phục repository checks; commit `fa890ef4` ghi nhận tài liệu hóa validation sau sửa chữa. Hai commit là lịch sử source, không chứng minh một run cụ thể thành công trong lần rà soát này.
- Không thấy workflow CD trong `.github/workflows` tại snapshot được đọc. Luồng staging, tag promotion và rollback tại §25.5 là target SRS, không phải as-built deployment evidence.
- Rev58 chỉ đọc source/configuration và cập nhật tài liệu; không chạy CI/application tests, build, truy cập secret/provider/database, hoặc triển khai môi trường.

<a id="srs-32-9"></a>
### 32.9 Rev69 — SVG engine M1/M2 source implementation snapshot (2026-11-13)

This records source edits made under the owner-approved Plan Rev83.4 manifest in local worktree branch `codex/feat063-parent-docker-modal-seed-20261111`, based on `1f5bb0b5b1ab501a7120598a7e6e0de75217ddb3`. The implementation is uncommitted, and the worktree also contains pre-existing changes outside this amendment. This is a static source observation; it does not replace §§1–31 or establish runtime behavior.

| Surface | Source state at Rev69 | Evidence limit |
|---|---|---|
| SVG source intake and persistence | Added a bounded SVG allowlist sanitizer, canonical structured `SvgDocumentV1`, geometry/path checks, source/canonical hashes, lineage and object-storage writes through the existing adapter. Added Core catalog/source/license/readiness metadata, reusable source-bound guide revisions, append-only exact-hash review records, and additive migration `20261113_svg_catalog_review.py`. Reusable catalog guides are distinct from immutable guide snapshots inside lesson versions; curator approval gates platform visibility while `grouping_allowed` is reserved for future automatic grouping. | Migration was not run; object storage, schema constraints, immutable-row triggers, downgrade guard, and repository authorization were not exercised. No external dataset or sample SVG was imported. |
| API | Mounted authenticated `/api/svg-catalog/v1` routes for Parent approved-guide lookup, Teacher source intake/listing, immutable guide revisions, educator source/guide reviews, and Platform Admin curation. Added versioned request/response schemas and static OpenAPI descriptions. | Routes/OpenAPI were not generated, started, or called. Role, organization, hash and storage behavior are source-only observations. |
| Lesson Library | Input presentation schema accepts versioned `SketchStrokeGuideV3` references. Lesson write validates source hash and existing canonical path IDs; Parent lesson-detail hydration resolves the referenced canonical SVG after lesson access succeeds. | No lesson create/update/read was executed; private/shared/public access behavior and `If-Match` conflict handling remain unverified. |
| Parent Android | `SketchGuideScreen` reads approved catalog or selected lesson guide data and renders progressive source paths with prior strokes solid and current strokes dashed through native SVG elements. An empty catalog remains an unavailable/skip state; no AI or fixture fallback was added. | Expo app, Android emulator, catalog response and stage transition were not run. No approved platform guide exists as evidence in this snapshot. |
| Teacher Web | Added an authenticated SVG source and lesson editor route; it assigns existing path IDs to semantic parts and 4–8 stages, authors Vietnamese instructions, previews/presents the guide, keeps local undo/redo, stores browser-local recovery drafts, debounces autosave by 1.5 seconds, uses `If-Match`, and retains local edits on `409`. Added exact-hash review controls for independent educators. | Teacher browser, API, revision history, concurrent edit, recovery and presentation were not exercised. Platform curation is API-only in this amendment; no Admin UI was added. |
| AI/provider behavior | The new SVG path is catalog/manual only. No Modal call, model flag activation, warmup, FLUX removal, video work or AI fallback was added by this amendment. | Zero inference is recorded for this implementation task; previous provider evidence is not revalidated here. |

No test, build, emulator/browser session, database migration, API request, renderer benchmark, catalog approval or deployment was run for Rev69. Therefore the 4–8-step logic, sanitizer properties, access control, write immutability, `409` recovery, empty-state UX, ≥30 FPS, p95 render/transition targets, memory target, and end-to-end Parent/Teacher behavior remain **NOT VERIFIED**. The companion Data Table Register remains older and unsigned; the Rev68 crosswalk is implementation-local and does not sign off the physical ERD. The SRS remains unsigned. See Plan Rev83.4 and `evidence/EV-063-93_SVG_ENGINE_M1_M2_20261113/IMPLEMENTATION_REPORT.md`.

### 32.10 Rev84 — one real Teacher SVG Modal UI verification (2026-11-13)

One local synthetic Teacher account completed an authenticated Teacher Web request to generate a presentation illustration draft through the backend and the deployed Modal teacher.svg-illustration.generate workload. The pinned model was Qwen/Qwen3.5-9B revision c202236235762e1c871ad0ccb60c8ee5ba337b9a. One request returned HTTP 200 in 221.684 seconds; the backend validated and sanitized an 18-path SVG and the Teacher page rendered it. The response remained DRAFT, review_required=true, and persisted=false; no catalog/lesson insertion or publication occurred. This single non-personal synthetic sample is an environment-specific as-built observation, not evidence of quality across topics, a change to §§1–31, or formal SRS approval.

Before inference, the CPU-only Modal /health reported the pinned Qwen checkpoint ready without GPU allocation or inference. After the one request, Modal logs recorded worker_succeeded; the immediate API log summary had missed that terminal event because Modal log indexing lagged. The app remains deployed with min_containers=0; the final Modal running-container query was empty. The local capability flag was returned to false, and the isolated Docker/UI/browser processes were stopped.

During this verification, GET /openapi.json returned HTTP 500 because runtime OpenAPI generation could not find the existing Rev37 SVG catalog contract response schema in components. The authenticated SVG endpoint itself returned HTTP 200. This OpenAPI issue is an as-built contract/documentation defect and remains unresolved. Full timing, output hash, call identifiers, visual review and limits are recorded in evidence/EV-063-94_TEACHER_SVG_MODAL_UI_20261113/REPORT.md.
### 32.11 Rev85 — dataset-conditioned Teacher SVG attempt (2026-11-13)

One authenticated local synthetic Teacher UI request exercised the dataset-conditioned teacher.svg-illustration.generate path using the non-personal topic con hươu sao, target age 60 months, and warm_storybook. The pinned dataset was yoavf/svg-animal-illustrations revision d7ab3149308746a4b17e7cbee30f1f054f6c49df; its card declares CC0-1.0, not independently legally audited. The deployed reference pack contained dog/quadruped, cat/feline and rabbit/lagomorph structural examples. The API returned HTTP 502 MODAL_WORKER_FAILED_TERMINAL (request ID 37bdb1ee-24a1-4de2-866b-8051acf77143) during dataset-reference selection. Whole-pack validation rejected prompet-sample-cat/path-026, whose stroke_width=20 exceeded the unchanged worker contract of 1–12. The Qwen model was not loaded for this request and no inference, SVG response, rendered image or quality comparison was produced. Therefore Rev85 establishes a data-validation defect, not a quality improvement or successful dataset-conditioned generation. The one-request plan limit was consumed; no retry was made. Local generation was disabled after the attempt. The shared Modal app remained deployed; the post-run container-list check timed out, so live-container scale-to-zero was not verified. This environment-specific observation does not change §§1–31 or constitute SRS approval. Detailed evidence: evidence/EV-063-95_TEACHER_SVG_DATASET_QUALITY_20261113/REPORT.md.


### 32.12 Rev86 — dataset-conditioned Teacher SVG comparison (2026-11-13)

Rev86 preserved the pinned `yoavf/svg-animal-illustrations` source snapshot byte-for-byte and removed only the invalid cat example from the active preview pack. The excluded source record remains in the raw snapshot and the manifest records that `path-026` has `stroke_width=20`, beyond the unchanged worker limit of 12. The active dog/quadruped and rabbit/lagomorph pack passed the exact worker parser (22 and 18 paths respectively); its 9,716-byte pack SHA-256 is `319d25932c8d4bc8c362b6af19ecded75cb1015d7f8cc19387c9685a74349af0`.

One authenticated local synthetic Teacher UI request for `con hươu sao`, 60 months, `warm_storybook` reached the existing Qwen/Qwen3.5-9B Modal worker. The existing shared app was updated once; CPU `/health` returned HTTP 200 in 4.749 seconds with the pinned checkpoint ready, no GPU allocation and no inference. The one UI POST returned HTTP 200 after 225.822 seconds (worker wait 223.907 seconds). Request ID: `a371d8a9-2de0-485e-a844-a58328ce29b8`; Modal call ID: `fc-01M799DWAHN9XGNRRTX4NFE2X4`. The result was a sanitized 19-path `TeacherSvgIllustrationDraftV1`, `DRAFT`, `review_required=true`, `persisted=false`, with document SHA-256 `9de4dc5936682e79b3e288229256f84f9564025ec14f3d1bed17b4caebcc8ac7`. The actual JSON, SVG and browser render are in `evidence/EV-063-96_TEACHER_SVG_DATASET_QUALITY_FIX_20261113/`.

The selected dog/quadruped structural reference did not ensure species fidelity: the rendered deer has long unbranched upright forms that read as rabbit ears. Connected, grounded limbs and removal of detached props improved over Rev84, while the deer-recognition criterion failed and body details remain imperfect. The five-criterion comparison is therefore mixed and **does not pass** the requested deer illustration quality objective. One sample does not establish general dataset benefit. API/worker logging also reported no terminal event despite all worker phases completing and HTTP 200. After the request, the Rev86 API container configuration had the local SVG flag set to false, but it remained `Created` because port 8000 was occupied by a separate healthy API container; that existing service was not modified. Modal's `min_containers=0` configuration is present, but post-run live-container scale-to-zero was not verified. This dated, environment-specific evidence is append-only under §32 and does not change §§1–31, the unsigned requirements baseline, or approval status. See `evidence/EV-063-96_TEACHER_SVG_DATASET_QUALITY_FIX_20261113/REPORT.md`.


### 32.13 Rev87.4 — curated SVG reference and stroke-authoring skill (2026-11-13)

Rev87.4 packages one Arcadia Science Free Organism Illustration Library v1.0 `Gallus gallus` tricolor-stroke SVG (Zenodo DOI `10.5281/zenodo.17203578`, CC0-1.0) as a visual reference, not as pre-authored stroke order. The 41,184,246-byte archive matched published MD5 `a845bf16730238334f39c7cfbc1d4703`; the selected 24,251-byte SVG SHA-256 is `4f6397d5d32ff7ea58451cb5e5725c87501be155c0eb64f85c5821dfe99cb1ed`. The upstream MIT `whiteboard-animation` skill v0.1.0 is installed locally as authoring guidance; its rules are ported to the Qwen3.5 prompt and the backend chicken-topology gate. The skill is not a Modal runtime service.

Local source code now packages and verifies the reference, rasterizes it in memory for matching chicken topics, returns source provenance, and keeps the generated SVG as an unpersisted private draft requiring adult review. Static Python/JSON checks and the Teacher UI production build passed. Parent typecheck remains blocked by existing missing Expo public-environment type declarations. One Modal deploy command failed before app update when Windows `Path` conversion produced a non-POSIX remote path; the local path was corrected, but no redeploy was attempted because the approved plan's single-attempt stop condition was reached. No Modal `/health`, GPU inference, Parent AI request or generated guide was produced. The running Docker API returned HTTP 200 health but its image does not expose the current Parent sketch-guide route; no migration, account creation or `.env` change was made. Therefore visual quality and live integration are **not verified**. This dated local implementation evidence does not modify §§1–31 or sign the SRS. See `evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/REPORT.md`.

### 32.14 Rev87.5 — one bounded Modal redeployment attempt (2026-11-13)

The owner authorized one additional deployment attempt after Rev87.4's Windows remote-path failure. A current-worktree temporary API container built and served the mounted Parent guide route on port 8001; its local Docker health returned HTTP 200, an unauthenticated GET to the guide route returned 405, and `/openapi.json` returned HTTP 500 because the `SVG catalog contract` component is missing. No authenticated API call was sent. The existing Rev79 PostgreSQL/Firebase Auth stack was left untouched; its database revision was `20261110_parent_lesson_pin`.

The single Modal deploy command exited 1 after image-build output with a Windows console encoding error (`charmap` cannot encode characters). The deployment state is unknown because no follow-up Modal health/status request was made after the stop condition. No Modal health call, GPU inference, Parent UI login, sketch-guide POST, generated SVG/render, or screenshot was produced. The temporary API container was stopped/removed; the pre-existing API remained unchanged. A failed attempt to start the default Compose PostgreSQL/Firebase services encountered the already-occupied host port 55439; the newly created Firebase container was removed without deleting volumes, and the recreated default Postgres container remains inactive with its volume preserved. No migration, seed/account creation, `.env` edit, test suite, video, FLUX or real child data was used. This is dated as-built evidence only; §§1–31 remain unchanged and the SRS remains unsigned. See `evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/REPORT.md` and `runtime-attempt-2.json`.

### 32.15 Rev87.6 — Android Parent UI attempt (2026-11-13)

The two changed OpenAPI modules compiled in the temporary API container. Runtime `/health` and `/openapi.json` returned HTTP 200; the projection contained the Parent sketch-guide endpoint and 12 SVG catalog operations with concrete response schemas and the declared 200/201 statuses. The real Expo Android app bundled in 11.777 seconds and ran on Pixel_10. The existing synthetic Parent account authenticated through Firebase Auth Emulator; its profile loaded with current authorization/consent.

The profile already had an open run. The UI resume action reported that the open run lacked enough data to restore the next screen, while the app prevented starting another run. The approved stop gate was applied: no run/profile/consent was created, deleted or changed, and the topic/guide screen was not reached. No Modal deployment, Modal health call, GPU inference, generated guide JSON/SVG or renderer result exists for Rev87.6. Actual Android auth, home and resume-blocked screenshots plus cleanup/timing details are recorded in `evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/` (`runtime-attempt-3.json`). The temporary API, Metro and emulator were stopped; shared PostgreSQL/Firebase Auth and `.env` were left untouched. This is environment-specific as-built evidence only; §§1–31 remain unchanged and the SRS remains unsigned.


### 32.16 Rev87.9 — real Android Parent E2E with Modal (2026-11-13)

One real Android Parent flow used a newly registered synthetic account/profile, Firebase Auth Emulator, the current-worktree API in a temporary Docker container, a generated non-personal chicken drawing, and deployed Qwen/Qwen3.5-9B revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`. Signup, synthetic profile creation, drawing upload, context confirmation, drawing analysis, adult subject confirmation, and activity suggestion were exercised through the actual Android UI. Drawing analysis returned HTTP 200 in 38.191 seconds (Modal call `fc-01M7A527SPGTG5XWAVG6SZ4KRH`), identifying `con gà` with 0.90 confidence. Activity suggestion returned HTTP 200 in 121.894 seconds (Modal call `fc-01M7A575511AWPH7B6ERCQC66J`); the catalog supplied two butterfly candidates for a chicken subject, so the model returned `NO_MATCH` and three fallback drafts.

The optional SVG guide lookup failed twice with `DATABASE_UNAVAILABLE`. Read-only inspection found the database at Alembic revision `20261110_parent_lesson_pin` without `core_svg_catalog_assets`, `core_svg_catalog_guide_revisions`, and `core_svg_catalog_reviews`. No migration was run; the guide was skipped as optional. No generated guide SVG or render exists for this run.

The activity screen exposed no primary-activity selection control. The real UI's continue action sent one initial story request and received HTTP 422 before route/provider dispatch. The versioned request schema requires `primary_activity_request_id` and `primary_activity_ref` together; the current Parent adapter sends only `expected_understanding_revision`. No activity was injected, and no story, story confirmation or video was generated. One fallback draft proposes small grains/beans with a supervision warning; the current technical gate allowed it, so technical schema acceptance must not be treated as child-safety content approval.

The API worker wait summaries reported `worker_started_without_terminal_event` and omitted output hashes for both successful inference results; outputs were retrieved by their Modal call IDs. The drawing worker was deployed once (101.473 seconds) and received one CPU-only `/health` call (HTTP 200, no GPU allocation/inference). Exactly two authenticated GPU inferences occurred; there were no retries or timeouts. The task API/Metro/emulator were stopped, while shared PostgreSQL/Firebase/Redis/MinIO/ClamAV, Modal apps and model volume were preserved. No migration, source change, `.env` edit, video or real-child data was used. This is dated environment evidence only: it does not modify §§1–31, establish full-flow acceptance, or imply SRS sign-off. Full actual outputs, IDs, hashes and screenshots: `evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/REPORT.md` and `runtime-attempt-4.json`.

### 32.17 Rev87.10-A — Parent optional SVG guide runtime attempt (2026-11-13)

The actual Parent Android UI reached the optional guide using generic topic `Con ga`. The task API `/health` and OpenAPI route check passed. One catalog lookup returned HTTP 401 `INVALID_IDENTITY_TOKEN` before database access because the task API initially used fallback project `sketch2life-local`, while the existing app/Auth Emulator use `sketch2life-dev`. The task API alone was recreated with the matching project ID and the Parent SVG capability flag enabled; no `.env`, shared service, database or Modal app changed. The single AI-draft POST still returned HTTP 401 `INVALID_IDENTITY_TOKEN`; the API verifier suppresses provider details, so the exact token-validation cause remains unknown. The worker was not dispatched, no GPU inference occurred for SVG, and no SVG response or render exists. The Parent UI now exposes the AI-draft fallback after lookup failure while retaining the error; its focused mobile test passed 4/4. No catalog retry, migration, seed, story or video ran. The task API, Metro and emulator were stopped; shared services remained running. This is environment-specific as-built evidence only: §§1–31 and unsigned SRS requirements remain unchanged. See `evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/runtime-attempt-5.json` and `REPORT.md`.


### 32.18 Rev87.10-B/C — Parent Auth Emulator integration and SVG attempt (2026-11-13)

A fresh local Auth Emulator sign-in and authenticated Parent `/api/auth/v1/me` returned HTTP 200 (`parent`, `active`) when the task API used the current Compose configuration: Firebase project `sketch2life-dev`, `FIREBASE_AUTH_EMULATOR_HOST=firebase-auth:9099`, and revoked-token checking enabled. Read-only inspection found the stale API container `s2l-parent-e2e-20261111-api-1` had the correct project ID but no emulator-host setting; no auth bypass or verifier code change was needed. Current `compose.yaml` already sets the emulator host. The existing shared services and `.env` were not changed.

The one read-only Parent SVG catalog request returned HTTP 503 `DATABASE_UNAVAILABLE`; the shared DB still lacks SVG catalog/review tables, and no migration was run. One generic-topic Parent SVG draft API request then reached Modal and returned HTTP 502 after 820.282 seconds. Qwen/Qwen3.5-9B revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a` ran 766.801 seconds of inference and failed at `output_parse_and_contract_validation` with `SVG_TOPIC_GUIDE_PATH_INVALID` (`RuntimeError`); the worker duration was 805.853 seconds. Modal call: `fc-01M7AGHYQ0DH0Q65V3EW079BRB`. No validated SVG output or render exists. The API's initial worker-log summary missed the terminal event; a later read-only call-log query found it, exposing a log-indexing/terminal-reconciliation gap.

Android UI was not run because Android SDK/`adb` and an emulator device were unavailable. The authenticated API path is verified, but Parent Android UI integration and SVG output remain unverified/failed respectively. No story, video, migration, seed/account/profile change, `.env` edit, Modal deploy/warmup, retry or real-child data was used. This dated environment-specific evidence does not change §§1–31 or sign the SRS. See `evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/runtime-attempt-6.json` and `REPORT.md`.


### 32.19 Rev87.10-D — Parent SVG catalog database migration (2026-11-13)

The owner authorized fixing the local development database after the Parent SVG catalog returned HTTP 503 `DATABASE_UNAVAILABLE`. Read-only preflight found Alembic revision `20261110_parent_lesson_pin`, all three SVG catalog tables absent, and 14 existing `core_asset_metadata` rows; all 14 were compatible with the migration's expanded owner-scope check. The exact revision `20261113_svg_catalog_review` was applied transactionally with `alembic upgrade 20261113_svg_catalog_review`; other Alembic heads were not upgraded.

After migration, the database reports `20261113_svg_catalog_review`, all three catalog/revision/review tables exist, the owner-scope check is validated, two immutable triggers exist, and the existing asset-row count remains 14. API health returned 200. An authenticated Parent catalog GET returned HTTP 200 with `SvgGuideCatalogPageV1` and zero items. No fixture/seed, existing-row mutation, Modal/AI request, `.env` edit or service restart occurred. This is environment-specific as-built evidence only; §§1–31 are unchanged and the SRS remains unsigned. See `evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/runtime-attempt-7.json` and `REPORT.md`.


### 32.20 Rev87.10-E — real Parent SVG generation attempt (2026-11-13)

After the targeted database migration, the authenticated Parent catalog GET returned HTTP 200 with zero approved guide items. One real Parent SVG draft request for generic topic `con gà` reached the deployed Qwen/Qwen3.5-9B Modal worker and returned HTTP 502 after 223 seconds. Modal call `fc-01M7AKKGC21Z4HFMGX8KYRCJ10` failed at `output_parse_and_contract_validation` with `SVG_TOPIC_GUIDE_PATH_INVALID` (`RuntimeError`); worker duration was 212,954 ms. The strict worker parser rejected an SVG path field, but raw model output is not retained, so the specific field is unknown. No validated SVG or rendering was produced. Auth and database succeeded; this was not a timeout. No retry, fixture, child data, video, deployment, or additional inference occurred. Environment-specific evidence only; §§1–31 are unchanged and the SRS remains unsigned. See `evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/runtime-attempt-8.json` and `REPORT.md`.


### 32.21 Rev87.10-F/G/H — Parent SVG constrained-decoder correction and runtime result (2026-11-13)

This environment-only verification fixed a Modal worker crash caused by `lm-format-enforcer==0.11.3` rejecting string schemas that combine `pattern` with `minLength`/`maxLength`. The first call (`fc-01M7AP59BDGMX83146DPZQM6F1`) failed in `model_inference` after 38,044 ms of inference and 60,136 ms total worker duration. Removing only the redundant length keywords from the patterned `path_id` and `d` fields allowed `constrained_decoder_setup` to pass; regex and worker-side length checks remain. Focused tests passed 4/4, worker compilation passed, and the language/audio Modal app was deployed once from the authenticated sidecar.

One authenticated Parent API request passed API health, Auth Emulator sign-in, `/api/auth/v1/me`, and the empty catalog lookup, then reached Qwen/Qwen3.5-9B revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`. Modal call `fc-01M7AQ14QMS06Z00GR5P8X17AH` completed model inference in 364,985 ms and failed at `output_parse_and_contract_validation` with `SVG_TOPIC_GUIDE_JSON_INVALID`; total worker duration was 388,003 ms. The API logged HTTP 502 `MODAL_WORKER_FAILED_TERMINAL` for request `cda21ec2-0531-4025-b637-bd7228e193fc`. No validated SVG or rendering was produced; raw model output was not logged. The client surfaced a `TypeError` after 307.345 seconds before receiving the server terminal response; exact transport cause was not captured.

Source review shows JSON parsing occurs before the EOS/`max_new_tokens=6144` truncation check, so current evidence cannot distinguish malformed JSON from truncated output. No additional inference was authorized or sent; the one Rev87.10-H final attempt is consumed. No fixture, child data, retry, story, video, quality-gate bypass, `.env`/database mutation, or commit/push occurred. This is environment-specific as-built evidence only; §§1–31 are unchanged and the SRS remains unsigned. See `evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/runtime-attempt-10.json` and `REPORT.md`.

### 32.22 Rev87.10-I — SVG truncation diagnostics and one final Parent request (2026-11-13)

The worker now checks EOS and the output-token ceiling before attempting JSON parsing. It emits allowlisted token/EOS counters and JSON error positions without logging model text; the backend Modal log summarizer accepts only those diagnostics for the SVG workload. Focused worker checks passed 6/6, worker compilation passed, and the backend safe-log-summary check passed. One deploy of `language_audio_app.py` completed; Modal applied the language/audio file's full function set, while no other function was invoked and the drawing/VLM and video/FLUX apps were not deployed. The task API alone was rebuilt and returned health HTTP 200. Five project-scoped Compose volume objects were materialized during API recreation despite `--no-deps`; no running container uses them, and they were left untouched. The task API, shared services and database remained operational.

One authenticated Parent request used only the generic topic `con gà` and beginner difficulty. API health, Firebase Auth Emulator sign-in, Parent `/me`, and catalog lookup all returned HTTP 200; the catalog contained no approved matching guide. Qwen/Qwen3.5-9B revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a` reached model inference. Modal call `fc-01M7AVABJR7AVEJS9F89B19ZDM` generated 6,144/6,144 output tokens without model EOS (final token 220; model EOS 248044; tokenizer EOS 248046), then failed the post-generation completion check with `MODAL_SVG_TOPIC_GUIDE_OUTPUT_TRUNCATED`. Inference time was 361.621 seconds, total worker time 384.513 seconds, and Parent API time 395.670 seconds; API returned HTTP 502 `MODAL_WORKER_FAILED_TERMINAL` for request `5a6b5e49-bfb0-4b23-a03e-2e29295247d0`. The terminal event records the configured GPU class `L40S|L4|A10`; it does not identify the actual allocated GPU.

No validated SVG or response was returned. The evidence identifies token-cap truncation, rather than a cold-start timeout or JSON-parse ambiguity; raw generated content remains intentionally unavailable, so output quality and whether a larger budget would yield valid JSON remain unverified. The one inference allowance is consumed; another model/prompt/token-budget change and request require a new bounded plan and approval. No retry, story/video, child data, fixture, account/profile/consent/database mutation, `.env` edit, or product-target change occurred. §§1–31 remain unchanged and the SRS remains unsigned. See `evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/runtime-attempt-11.json` and `REPORT.md`.
### 32.23 Rev87.10-M/N/O/P — Parent SVG anatomy prompt corrections and runtime result (2026-11-14)

The chicken-specific Qwen prompt was incrementally constrained to produce a large horizontal body, distinct part geometry, a visible beak, and grounded legs. The backend now distinguishes an undersized body from disconnected anatomy. Focused worker/LMFE tests passed 10/10; worker compilation passed; focused backend topology tests passed 2/2; scoped `git diff --check` passed. One language/audio Modal deployment completed. The API/auth/catalog preflight was healthy, with zero approved catalog entries for `con-ga`.

One final authenticated Parent API request reached Qwen/Qwen3.5-9B revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`. Modal call `fc-01M7B5C1W8JNVY4061Z2Y7ZKKQ` completed worker parsing successfully with 9 paths, 9 parts, and 8 stages. Inference took 212.486 seconds; total worker time was 240.556 seconds; API wait was 247.307 seconds. API request `353fcb85-1fae-4b41-b584-3a2ef468b6fe` returned HTTP 502 `MODAL_SVG_TOPIC_GUIDE_OUTPUT_REJECTED`, reason `SVG_CHICKEN_ANATOMY_ENDPOINT_DISCONNECTED`. Safe in-memory checks found the neck endpoint still outside the head bounds; the beak remained below its 12-unit minimum and both legs below the required descent. Other body/part overlaps and listed endpoints passed. No validated SVG or render was returned.

The 1,800-second deadline was retained: the request completed in about 253 seconds and failed a hard backend geometry gate, not a timeout. The one Rev87.10-P inference was consumed; no further inference, retry, output repair, or quality-gate bypass occurred. No child data, fixture, story/video, secret, or raw SVG/model text was used or retained. This is environment-specific as-built evidence only; §§1–31 are unchanged and the SRS remains unsigned. Details: `evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/runtime-attempt-20.json` and `REPORT.md`.

### 32.24 Rev87.11 — Arcadia-derived Parent SVG guide (2026-11-14)

The approved Rev87.11 implementation adds a deterministic source-derived Parent guide for supported chicken topic aliases. The backend image packages the pinned Arcadia Science Free Organism Illustration Library v1.0 Gallus gallus CC0 reference and provenance, then builds a separate versioned set of 19 new open paths arranged into six progressive Vietnamese drawing stages. The derivation records source path lineage and verifies the pinned source hash; it does not reuse source illustration paths as child strokes. Existing SVG sanitization and chicken anatomy/topology checks remain active.

One POST to /api/parent/v1/ai/sketch-guides for con gà returned HTTP 200 with SvgTopicStrokeGuideSourceDraftV1 in 0.027 seconds. The response document hash is 325ff5edcdf9de4c71f503bc52e385bcb1f32349099de1f149d0e60362771831; it contains 19 paths and six stages. Modal was not dispatched. An SVG and 1024×1024 raster rendering were saved in EV-063-102. The route verification used a focused FastAPI TestClient with identity and database dependencies overridden; it does not establish Firebase-authenticated production or Android end-to-end behavior.

This source covers chicken only and is a private draft, not an educator-reviewed or published catalog guide. Unsupported topics continue through the existing Modal path. No Modal/GPU request, fixture response, child data, database mutation, shared-service restart, or target-requirement change occurred. §§1–31 remain unchanged; the SRS remains unsigned. See evidence/EV-063-102_ARCADIA_PARENT_SOURCE_DERIVED_GUIDE_20261114/REPORT.md.

### 32.25 Rev87.11-B/C — separate Parent stroke guide and finished SVG reference (2026-11-14)

Visual inspection found that rendering the completed Arcadia illustration as a faint underlay conflicted with the authored guide's pose and obscured its blue step strokes. Rev87.11-C corrected the Parent screen to show the progressive drawing on a plain canvas by default, with a separate toggle to the full-color illustration; toggling back preserves the selected step. The source-derived chicken guide was revised to 20 open paths across six stages facing the same direction as the reference. It includes connected body/head/beak/comb, wing and tail attachments, and two grounded legs; existing sanitizer and hard anatomy/topology checks remain enabled.

The actual packaged-source Parent route returned `SvgTopicStrokeGuideSourceDraftV1`, HTTP 200 in 0.045 seconds, with a 20-path guide and the separate 77-path filled SVG reference. Guide document SHA-256: `27bed3626dada9ce68094d7697896d14fa7b7e399ea3b0c34a05f32eed4c5fc7`; source hash unchanged at `4f6397d5d32ff7ea58451cb5e5725c87501be155c0eb64f85c5821dfe99cb1ed`. Modal was not dispatched. Focused backend derivation/route/topology checks passed 9/9; mobile contract/renderer checks passed 5/5. Eight actual SVG artifacts were rasterized at 1024×1024 and visually inspected.

The route test used FastAPI TestClient with identity/database dependencies overridden and does not prove Firebase-authenticated or Android end-to-end rendering. A standalone TypeScript check for the changed guide domain, screen and renderer passed. Full mobile TypeScript checking still reports missing `EXPO_PUBLIC_*` type declarations in three existing configuration files. The guide is a private chicken-only draft requiring educator review; unsupported topics retain the existing Qwen/Modal path. No database or child-data mutation, Modal call, service restart, commit/push, or target requirement change occurred. §§1–31 remain unchanged; the SRS remains unsigned. See `evidence/EV-063-102_ARCADIA_PARENT_SOURCE_DERIVED_GUIDE_20261114/REPORT.md`.

### 32.26 Rev87.11-F — Parent hen drawing sequence checked against the supplied HTML (2026-11-14)

The supplied HTML demo was run in headless Edge and inspected at all seven drawing steps. It adds one part or a small related group per step; completed paths remain dark while the current paths animate in blue with a 950 ms dash animation and 220 ms stagger. The previous six-step V4 Parent guide did not follow that progression and its final body/wing/tail geometry did not read like the supplied hen. V4 remains preserved as a historical version (manifest SHA-256 `e901533285ef887507e9c6e6623d919e7eb3b6bb499582af0007da3d95ea8665`).

The active local draft is now a separate V5 manifest (SHA-256 `ef05700d09ea5569373fe4746da78b36dd5e0fcbdd34536dd01707f6b9df46b9`) with 16 authored paths in eight Vietnamese stages: head, comb, beak/eye/wattle, connected neck/body, wing, raised tail, legs, and feet with a few feather marks. The pinned Arcadia CC0 illustration provides pose/feature placement only; it is not traced or drawn beneath the guide. Parent guide mode stays stroke-only on white; the complete color illustration remains a separate optional view. Existing sanitizer and chicken anatomy/topology gates remain enabled.

The actual local Parent route for `gà mái` returned `SvgTopicStrokeGuideSourceDraftV1`, HTTP 200 in 0.082 seconds, with 16 paths and eight stages. The guide document SHA-256 is `f88713263264585418b4fe5f58c87f4f2f5071dc0c2db9d24dafc10fb063ead0`; the pinned source hash remains `4f6397d5d32ff7ea58451cb5e5725c87501be155c0eb64f85c5821dfe99cb1ed`. Modal was not dispatched. The eight stage SVGs, final guide and separate reference were rendered at 1024×1024 and visually inspected. Focused backend tests passed 12/12 and Parent UI guide contract tests passed 3/3.

The route check used FastAPI TestClient with Parent identity and database dependencies overridden; it is not Firebase-authenticated, Android E2E or educator approval. This remains a private chicken-only draft. No child data, database mutation, Modal/GPU request, shared-service restart or target-requirement change occurred. §§1–31 remain unchanged and the SRS is unsigned. Evidence: `evidence/EV-063-105_PARENT_HEN_HTML_ALIGNED_DRAWING_SEQUENCE_20261114/REPORT.md`.

### 32.27 Rev87.11-H — Parent chicken guide from exact pinned source paths (2026-11-14)

The owner rejected Rev87.11-G's hand-authored, childlike V6 geometry and clarified that the strokes must form the same pictured animal. V6 remains preserved as historical evidence; active pinned-chicken guide generation now uses V7. The source is the pinned Arcadia Science Free Organism Illustration Library v1.0 `Gallus gallus` CC0 SVG (SHA-256 `4f6397d5d32ff7ea58451cb5e5725c87501be155c0eb64f85c5821dfe99cb1ed`). V7 uses the exact `d` geometry from all 77 sanitized source paths; its manifest stores source provenance, path identity, eight stage assignments and Vietnamese teaching copy, not replacement geometry. Manifest SHA-256: `22eb7e077416b64db52b65ede1a45b584e1315a96d1b7e1ac110118510e532c6`. The guide is unfilled line art on white; the original colored illustration remains a separate reference view.

The local Parent route request for `gà mái` returned HTTP 200 in 0.090 seconds with `SvgTopicStrokeGuideSourceDraftV1`, engine 7.0.0, 77/77 exact source-path matches, and all paths assigned exactly once across eight stages. Modal dispatch was guarded and did not occur. All eight cumulative stages were rendered at 1024×1024 and visually inspected; the final outline depicts the same chicken silhouette and identifying features as the reference. The mobile path-length parser was expanded for the relative curve, arc and other commands used by the actual source, and its test covers all 77 paths.

Focused backend tests passed 9/9, focused Parent mobile guide tests passed 8/8, and backend compilation passed. The route check used FastAPI TestClient with identity/database dependencies overridden; it is not Firebase-authenticated or Android end-to-end evidence. The full mobile typecheck remains blocked by existing missing `EXPO_PUBLIC_*` declarations in three configuration files; the package script also encountered a worktree `realpath` permission error. This is a private chicken-topic draft requiring adult/educator review, not a published catalog guide. Unsupported topics retain their existing Qwen/Modal flow. No database, account, consent, seed, `.env`, GPU, or shared-service mutation occurred. §§1–31 remain unchanged and the SRS remains unsigned. See `evidence/EV-063-107_PARENT_EXACT_SOURCE_PATH_GUIDE_20261114/REPORT.md`.

### 32.28 Rev87.13 — Parent multi-dataset progressive SVG guides and color reveal (2026-11-14)

The Parent optional sketch-guide route now has a pinned local OpenMoji source path before the existing Arcadia chicken path and Modal fallback. OpenMoji 17.0.0 revision `f9fc506a3f913be9897ab0181d611d4c910a4104` supplies paired black/color SVG assets for turtle (`U+1F422`), butterfly (`U+1F98B`) and dog (`U+1F415`). The selected figures were manually reviewed for simple, recognizable silhouettes and enough distinct source elements for 4–8 cumulative stages. Noto Emoji candidates were rejected after preview because deriving strokes from their filled illustrations created excessive internal contours; Noto is not in the runtime asset pack. The existing Arcadia chicken guide remains unchanged.

The API resolves only topic aliases from the hash-pinned local manifest, validates source/license hashes and safe SVG structure, normalizes source primitives to paths without changing geometry, checks black/color line-pair geometry and complete one-time stage coverage, and returns the paired original color SVG with source provenance. It uses only the selected topic; no child photo/profile/voice is sent to a provider for this local source path. Parent mobile displays cumulative lines and, on the last stage, the finished line guide beside the exact original color illustration with linked source/license attribution. The following photo capture remains the existing flow. Docker is configured to include this selected OpenMoji pack while keeping the Arcadia pack.

Source pack and manual stage/color previews are recorded in `evidence/EV-063-108_PARENT_MULTI_DATASET_SVG_GUIDES_20261114/REPORT.md`; OpenMoji source/license/hash metadata is in `deployment/modal/srs_v23/data/openmoji/`. This entry documents the code/source snapshot and manual artwork inspection only: no automated tests, app build, API request, Android run, Modal call/deployment, or production end-to-end check was performed for Rev87.13. Parent runtime behavior and draft-quality/educator approval remain unverified. This is environment-specific as-built evidence; target §§1–31 are unchanged and the SRS remains unsigned.

### 32.29 Rev87.14 — Parent moderately detailed Openclipart SVG guides (2026-11-14)

Rev87.14 adds a hash-pinned local Openclipart source pack before the existing Parent guide fallbacks. It selects matching butterfly color/line assets 352665/352671 by teck5 and crawling turtle assets 325115/325116 by hund. The source pages declare CC0 1.0; URLs, attribution, license notice and per-file SHA-256 values are retained in `deployment/modal/srs_v23/data/openclipart/`. Dog assets 213982/213981 were inspected but excluded because the fur contours are too dense for the intended drawing guide. An alternate turtle outline was excluded because it does not match the selected color asset's pose.

The two active guides use only source line-art paths, assigned exactly once across six progressive stages (39 butterfly paths and 35 turtle paths). Each has a separate matching color illustration (70 butterfly paths and 8 turtle paths) for the final reference view. The added artwork is a moderate-detail option compared with the prior emoji-style figures; it is not evidence of educator/child validation or age-band suitability. Existing OpenMoji and Arcadia sources remain available. The local resolver uses the topic only and does not call Modal for these selected assets. The Docker image copy and `.dockerignore` allowlist include the curated pack.

Manual previews and source review are recorded in `evidence/EV-063-109_PARENT_RICHER_OPENCLIPART_GUIDES_20261114/REPORT.md`. No automated tests, build, API request, app/Android run, Modal inference/deployment or educator/child evaluation was performed for Rev87.14; application behavior and actual device presentation therefore remain unverified. This is append-only environment-specific as-built evidence, does not alter target §§1–31, and does not sign off the SRS.

### 32.30 Rev87.15 — broad Parent Openclipart corpus on Modal Volume (2026-11-14)

Rev87.15 adds source code for an explicit CPU-only importer of `kawwaaa/openclipart`. The intended persistent location is a dedicated Modal Volume v2 named `sketch2life-openclipart-catalog-dev` in environment `dev`. The importer retains the original compressed source shards and, for CC0 records, extracts source SVG assets into a searchable SQLite/FTS catalog with source URLs, dataset revision, shard and asset hashes, license, and eligibility metadata. Docker images and local tracked assets do not contain this full dataset or index.

The Qwen3.5 guide worker has a read-only catalog mount. Its intended flow expands a generic adult-selected Vietnamese topic into bounded search terms, selects a catalog source, and uses the source illustration/path atlas to order exact source path IDs into 4–8 progressive stages. It returns no replacement path geometry; the renderer uses the original path data and pairs the same color source. Backend code checks the source-path list, guide geometry, provenance, and stage contract. The workload remains disabled by default and failures remain optional to the Parent drawing flow.

**As-built runtime evidence (2026-11-15):** the CPU importer completed all 18 shards and returned `READY` for immutable revision `df38e5ef633be067d397df7da19a9f009e69b3bd`. The dedicated Modal Volume v2 contains 178,561 source rows, 178,134 unique CC0 source rows, 1,923 guide-eligible SVGs, 22,340,611,707 bytes of original compressed shards, 87,741,484,027 bytes of extracted SVGs, and a 202,518,528-byte SQLite catalog (110,284,614,262 bytes total). One repeated source ID was collapsed by the SQLite primary key. The language/audio app is deployed; CPU `/health` reports the pinned Qwen3.5-9B checkpoint and catalog `ready`, with no GPU allocation or inference in the health request. One synthetic topic worker inference (`con mèo`, no child data, no video) ran on Modal but terminated at `output_parse_and_source_identity_validation` with `SVG_CATALOG_STROKE_PLAN_PATH_COVERAGE_INVALID`; no SVG guide was returned and no retry was performed. This was not a timeout. Parent HTTP/UI/Android and Teacher presentation runtime were not tested; the workload remains disabled by default. Full evidence is in `evidence/EV-063-110_OPENCLIPART_MODAL_VOLUME_CATALOG_20261114/REPORT.md` and its attached runtime/log files. This section is environment-specific as-built evidence only; target §§1–31 remain unchanged and the SRS remains unsigned.

### 32.31 Rev87.16 — Qwen source-path assignment fix and Modal worker verification (2026-11-15)

The Rev87.15 worker failure was caused by an output shape that expressed source path assignments as several arrays. Its schema constrained each array item to a known ID but could not enforce that their union covered every ID exactly once. The worker now uses an internal `SvgOpenclipartSourceStrokePlanV2`: every selected source path ID is a required property in `path_stage_assignments`, unknown properties are forbidden, duplicate JSON object keys are rejected, and each stage assignment is validated against the actual 4–8 stage count. Stage groups are derived in source order after validation. Qwen supplies only stage ordering/copy; the renderer continues to reuse exact sanitized source `d` geometry, with the paired color source kept separate. Safe diagnostics report counts/reason codes and do not log raw model output.

Focused worker contract checks passed 16 tests with two skips because the local Python environment lacks `lm-format-enforcer`; the pinned Modal worker image has it. Ruff on the contract-test file and the changed worker `SIM102` rule passed, as did Python compilation. The updated language/audio app deployed in Modal `dev` in 13.974 seconds. CPU `/health` returned `ok`, with Qwen3.5-9B at pinned revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a` and the Openclipart Volume v2 catalog `ready`, without GPU allocation or inference by health.

One real synthetic worker request for `con mèo` / beginner completed in 86.088 seconds (Modal call `fc-01M7DW7AGGFFQRV4QPG70ZVEH5`). The source is Openclipart `openclipart-friendly-kitten-icon`, CC0-1.0, dataset revision `df38e5ef633be067d397df7da19a9f009e69b3bd`, source SHA-256 `a5b74eed392104ff9baa2a335b5e8dde9aef40ca7775949a7fbc4a29b7f36594`. Qwen returned 11 source paths across six Vietnamese stages; each path appears exactly once, the line guide and color reference share the same path IDs/geometry, and all eight worker-runner quality checks passed. The constrained decoder setup succeeded and generation ended with EOS. No retry was performed.

This verifies the deployed Modal catalog-to-Qwen worker only. Parent HTTP/API/UI/Android, Teacher presentation, video, educator review, and child testing were not run. The product workload remains disabled by default. The request used no child profile/image/voice or account/consent/database data, and the corpus remains only on Modal Volume v2. Evidence and cumulative SVG previews: `evidence/EV-063-111_MODAL_QWEN_CATALOG_PATH_ASSIGNMENT_FIX_20261115/REPORT.md`. This dated §32 entry is as-built evidence only; target §§1–31 remain unchanged and the SRS remains unsigned.

### 32.32 Rev87.17/18 — Parent Modal SVG guide API integration and schema correction (2026-11-15)

The Parent SVG guide runtime path now keeps the full Openclipart/OpenMoji/Arcadia source packs out of the Docker API build context and image. The complete Openclipart catalog remains on Modal Volume v2; when optional local curated packs are absent, the Parent API continues to the Modal catalog worker. The feature remains disabled by default; the ignored local development .env enabled it only for this bounded verification.

The first authenticated synthetic Parent API request reached Qwen3.5 successfully but returned HTTP 502 because the API compared the worker payload schema (SvgTopicStrokeGuideContentV1) against the assembled API guide schema (SvgTopicStrokeGuideV1). This was a boundary validation defect, not a model timeout or invalid SVG. Rev87.18 introduced and used the separate worker-content schema constant while retaining the API entity schema for its own layer.

One fresh real request then returned HTTP 200 in 102.946 seconds (Modal call fc-01M7E0Z2386EH7TP37PRGEMKWS; worker duration 87.860 seconds). The authenticated Parent request used no child profile, image, voice, consent, or real personal data. Qwen3.5-9B at revision c202236235762e1c871ad0ccb60c8ee5ba337b9a returned a private, non-persisted SvgTopicStrokeGuideSourceDraftV1 for con mèo: 11/11 exact Openclipart CC0 source paths assigned once across six ordered stages, with a separate matching color reference. All eight source/provenance, safe SVG, exact geometry/path coverage, stage, color-match, and review-only gates passed. Seven saved SVGs parsed as XML. The ephemeral Firebase Auth Emulator identity and one backend identity row were deleted.

The focused pytest test was added but could not be collected in the host Python environment because sqlalchemy is absent; it is not reported as a passing unit test. API-container compilation and the real API → Modal → API request passed. No Android UI, Teacher presentation, video, child testing, or additional inference was performed. Full evidence and artifacts are under evidence/EV-063-112_PARENT_MODAL_API_GUIDE_RUNTIME_20261115/ and evidence/EV-063-113_PARENT_MODAL_API_GUIDE_SCHEMA_FIX_20261115/. This is environment-specific as-built evidence only; target §§1–31 are unchanged and the SRS remains unsigned.

### 32.33 Rev87.19 — Parent construction-guide worker rejection and local gate correction (2026-11-15)

Focused local contract tests passed before runtime verification: backend 12/12, Modal worker 25 passed with two asyncio deprecation warnings, and mobile 3/3. These checks validate contracts and render behavior; they do not establish model output quality.

The first HTTP TestClient preflight returned 500 after 3.335 seconds before any Modal worker invocation. Read-only Modal logs contained no worker call for that preflight. One bounded direct invocation of the Parent route handler then used only the generic synthetic topic `con mèo`; auth/database dependency wrappers were bypassed for this harness. No child profile, image, voice, consent, personal data, or video was supplied. Qwen/Qwen3.5-9B revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a` ran on Modal call `fc-01M7E7RJSYRAPJ9HR0XD0NYSSG`. The catalog selected a reference with 11 source paths. Model inference completed in 146.733 seconds; catalog query expansion took 45.720 seconds; total worker time was 216.720 seconds; the handler returned HTTP 502 after 234.273 seconds with request `13cdae7d-15b4-44cd-b47f-84fe983d0fd4` and `MODAL_WORKER_FAILED_TERMINAL`.

The terminal worker stage was `output_parse_and_source_identity_validation`, with `SVG_CONSTRUCTION_GUIDE_GEOMETRY_COMPLEXITY_INVALID`. The detailed worker log records zero parsed strokes/stages. The prior combined geometry gate did not preserve the raw model response or distinguish whether aggregate path characters or duplicate stroke geometry triggered the failure, so the precise subreason cannot be recovered. This was a parser/validation failure, not an inference timeout. No SVG API response, rendered guide, or visual quality result exists. The API-side wait log initially showed no terminal worker event, while the worker log did record the terminal rejection; both sanitized logs are preserved in EV-063-115.

After that terminal attempt, the local implementation aligned the total-geometry limit with the versioned schema maximum (16,384 characters), aligned the prompt to the 8–20 stroke contract, and added safe diagnostics separating duplicate geometry from aggregate-size rejection. Focused tests passed as listed above. The updated language/audio Modal app was deployed to `dev` without another inference and was then stopped; the app was confirmed stopped. Because the single approved inference allowance was consumed by the pre-correction failure, the effect of these changes on live Qwen output remains unverified. No second inference, gate bypass, child-data test, Android UI run, or video run occurred.

This section is environment-specific as-built evidence only. It does not establish successful Parent construction-guide generation or acceptance of the guide as child-readable. Target requirements §§1–31 remain unchanged, and the SRS remains unsigned. Evidence: `evidence/EV-063-115_PARENT_CONSTRUCTION_MODAL_TEST_20261115/REPORT.md` and its request, response, sanitized handler/worker logs, preflight record, and focused test summary.

### 32.34 Rev87.20 — Parent construction-guide live correction and remaining failure (2026-11-15)

Rev87.20 added an explicit final-stage feature requirement to the source-conditioned construction-guide prompt and safe diagnostics for feature-role distribution. Focused post-correction checks passed: Modal worker 27/27, backend 12/12, and Parent mobile 3/3. A real synthetic Parent route → Modal Qwen3.5 request first failed because its final stage omitted a feature stroke. After the prompt/diagnostic correction and deployment v2, the one final authorized request completed model inference but returned only two duplicate strokes for eight stages (70 total geometry characters). The worker rejected it at `output_parse_and_source_identity_validation` with `SVG_CONSTRUCTION_GUIDE_GEOMETRY_COMPLEXITY_INVALID` / `DUPLICATE_STROKE_GEOMETRY`; the Parent handler returned HTTP 502 after 189.152 seconds. This was not a timeout or aggregate geometry-size failure. No valid SVG guide or render was produced; no retry/third inference, child data, video, or Android UI run occurred. Modal CPU `/health` reported the pinned checkpoint/catalog ready without GPU allocation or inference; the Modal app was stopped and verified stopped. Evidence, sanitized worker logs and test results are in `evidence/EV-063-116_PARENT_STROKE_LIVE_FIX_20261115/REPORT.md`. This is environment-specific as-built evidence only; target §§1–31 remain unchanged and the SRS remains unsigned.

### 32.35 Rev87.21 — constrained Parent stroke-generation experiment (2026-11-15)

Rev87.21 replaced the model's variable `strokes` array with an internal fixed-key stroke map and normalized it to the existing construction-guide content contract. Focused tests passed (Modal 30/30, backend 12/12, Parent mobile 3/3). Three sequential real synthetic Parent route → Modal Qwen3.5 inferences were executed with topic `con mèo`, no child data and no video. Call 1 failed duplicate-geometry validation at stroke 5 after four unique geometries (HTTP 502, 193.140 s). Call 2 failed at stroke 9 after eight unique geometries, with a repeated feature label also diagnosed (HTTP 502, 211.341 s). Call 3 failed `SVG_CONSTRUCTION_GUIDE_STROKE_COMPLEXITY_INVALID` on the first 768-character path (HTTP 502, 446.930 s); the safe log did not include command count, so the exact subcondition is unknown. Model inference completed in every call; these were output-validation failures, not timeouts. No valid guide or render was produced. No gate was weakened, no retry/video/child data was used. Modal health remained CPU-only/no inference; the app was stopped and verified stopped. See `evidence/EV-063-117_PARENT_STROKE_CONSTRAINED_GENERATION_20261115/REPORT.md` and call-specific worker logs. This is environment-specific as-built evidence only; target §§1–31 are unchanged and the SRS remains unsigned.

### 32.36 Rev87.22 — Parent primitive renderer API success, visual rejection (2026-11-15)

Rev87.22 replaced model-authored SVG path strings with bounded ellipse/cubic/polyline primitives and deterministic SVG serialization. Focused tests passed (Modal 34/34, backend 12/12, Parent mobile 3/3). Three sequential real synthetic Parent route → Modal calls used only topic `con mèo`; no child data, video, account, or consent data was used. Calls 1 and 2 returned HTTP 502 for duplicate geometry and invalid stage metadata respectively (170.536 s and 151.828 s). Call 3 returned HTTP 200 after 152.067 s with eight paths/four stages, but visual inspection of the genuine render found disconnected/incomplete geometry that did not depict the selected kitten; the Vietnamese directions also disagreed with the visible strokes. The API/schema pass therefore failed visual acceptance. This was not a timeout. The Qwen/catalog health preflights did not allocate GPU or run inference. The language/audio Modal app was stopped and verified stopped; the Volume was not changed. No gate was bypassed and no child data or video was used. See `evidence/EV-063-118_PARENT_PRIMITIVE_STROKE_RENDERER_20261115/REPORT.md`. This is environment-specific as-built evidence only; target §§1–31 are unchanged and the SRS remains unsigned.

### 32.37 Rev87.26/27 — Parent pinned Openclipart source stage sequence (2026-11-15)

Rev87.26 attempt_001 returned HTTP 200 in 180.881 seconds with 20 paths in eight stages, but visual review rejected captions that described the wrong visible marks. Attempt_002 returned HTTP 502 in 172.675 seconds after Qwen draft and visual-review inference completed; the parser rejected one empty stage (`SVG_CATALOG_STROKE_PLAN_EMPTY_STAGE`). This was a hard output-validation failure, not a timeout. After inspecting the spatial atlas and cumulative render, Rev87.27 added an exact asset-ID and raw-source-hash scoped seven-stage sequence for the pinned CC0 Openclipart kitten. The single authorized synthetic Parent route request returned HTTP 200 in 73.116 seconds with all 20 unchanged source paths exactly once; the response remained a private, non-persisted draft requiring adult review. The cumulative render showed a recognizable kitten by stage 3, and subsequent eye, tail and paw directions matched the newly visible marks. Qwen3.5 catalog-query expansion and real catalog source selection remained active; Qwen stage-assignment and visual-review inference were skipped only for this exact pinned source, while nonmatching assets retain the existing Qwen flow. Focused checks passed (Modal worker 49/49; backend 12/12), as did compilation, focused Ruff, local rendering and exact-geometry validation. Full worker-file Ruff retains 16 findings in the existing broad file. The source illustration is monochrome. The route harness used a synthetic Parent principal and bypassed the auth guard; this does not establish Firebase-authenticated or Android end-to-end behavior. No child data, video, production request or Volume mutation was used. Modal `sketch2life-srs23-language-audio-dev` was stopped and verified stopped with zero tasks. This is environment-specific as-built evidence only; target §§1–31 are unchanged and the SRS remains unsigned. See `evidence/EV-063-121_PARENT_STAGE_SPATIAL_GROUNDING_20261115/REPORT.md`.

### 32.38 Rev87.28 — Parent kitten paired-eye stage correction (2026-11-15)

Review of the genuine Rev87.27 render confirmed an asymmetry: the right-eye inner ring was added in step 4, with the remaining eye details added in step 5. For the same exact hash-pinned monochrome kitten source only, worker code now groups source segments 10–15 (inner ears and both eyes) into one step; the curated guide has six stages and retains all 20 original source geometries exactly once. The focused Modal worker contract suite passed 50 tests, Python compilation passed, and the saved Rev87.27 response was re-sequenced and rendered locally. The stage-4 image visibly adds details to both eyes together. This is an offline preview from a saved genuine response, not a new API/Modal result. No deployment or inference was performed; the last live API response remains the seven-stage Rev87.27 response. No child/personal data was used. This is environment-specific as-built evidence only; target §§1–31 are unchanged and the SRS remains unsigned. See `evidence/EV-063-122_PARENT_SYMMETRIC_EYE_STAGE_20261115/REPORT.md`.


### 32.39 Rev87.29 — Parent non-kitten Modal catalog guide verification (2026-11-15)

One synthetic `con bướm` Parent route attempt returned HTTP 503 in 0.078 s before Modal dispatch because its bundled 39-path SVG guide exceeded the API canonicalizer's 32-path limit. The sibling turtle guide declares 35 paths and was not called. One real Parent route → Modal/Qwen3.5/catalog request each for `con voi` and `con cá` returned HTTP 200 in 147.959 s and 131.538 s respectively. The elephant response used 20 CC0 Openclipart paths in eight stages but manual review found a crude silhouette, disconnected first-stage marks, and repeated unrelated rear-leg ridge directions in captions. The fish response used nine paths in four stages, but the selected CC0 source was a kitchen scale, not a fish; its instructions repeated/truncated text and included Chinese characters. Thus both API responses passed their existing contracts/hard gates but failed manual visual/content acceptance. Worker logs show model/catalog/draft/review phases completed; the fish wait diagnostic lacked a worker terminal event despite API completion, indicating an observability inconsistency. No retries, gate weakening, child data, fixture, video, database write, or Android/Firebase E2E occurred. The app was stopped; `app info` reports lifecycle `stopped` and no servers. These results show generic non-kitten catalog selection and guide quality are not reliable; they do not change product targets in §§1–31 and do not generalize the exact pinned-kitten result. The SRS remains unsigned. Evidence: `evidence/EV-063-123_PARENT_NON_KITTEN_MODAL_SMOKE_20261115/REPORT.md` and per-topic request/response, logs, health preflight and rendered stages.
