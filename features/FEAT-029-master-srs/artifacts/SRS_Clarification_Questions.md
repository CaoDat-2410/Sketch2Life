# Câu hỏi làm rõ SRS Sketch2Life theo phiếu đăng ký

- Dùng cùng với: `artifacts/Sketch2Life_Master_SRS.md`
- Nguồn scope cần đối chiếu: `Phieu_FA26SE225.docx`
- Mục đích: chốt yêu cầu còn thiếu trước khi mở rộng SRS; không phải spec đã được phê duyệt.
- Cách trả lời: ghi theo ID, có thể trả lời `giữ theo phiếu`, `giữ theo repo`, `chọn ...`, hoặc `chưa biết — để TBD`. Không cần bịa giá trị nếu chưa có quyết định.

## Các điều đã được xác nhận trước đó

Không cần trả lời lại trừ khi muốn thay đổi:

1. Dùng workflow trong hình làm workflow mục tiêu.
2. Parent và Guide là người lớn giám hộ, quan sát và tham gia cùng trẻ; có thêm Admin.
3. Cho phép người lớn sửa narration hoặc ghi lại nếu không nghe rõ.
4. Thời lượng số mục tiêu khoảng tối đa 10 phút, không tính hoạt động ngoài trời/thể chất.
5. Parent chọn hạn lưu 30, 60 hoặc 90 ngày.
6. Tuổi mục tiêu sản phẩm là 0–12; catalog hiện có các dải tháng 0–35, 36–71, 72–107 và 108–155. Tuổi tuyển nghiên cứu chưa được xác nhận.
7. Giữ riêng các contract cùng tên nhưng khác schema cho tới khi có quyết định adoption.

## A. Ranh giới scope và ưu tiên

**Q-001.** SRS tổng cần mô tả cả sản phẩm mục tiêu và thiết kế nghiên cứu của capstone, hay phần nghiên cứu (protocol, tuyển người tham gia, chỉ số, phân tích) nên nằm ở phụ lục/phần tham chiếu riêng?

**Q-002.** Hãy phân loại từng deliverable theo `MVP bắt buộc`, `mở rộng nếu đủ thời gian`, `nghiên cứu/đầu ra học thuật`, hoặc `không làm`: Parent/Child Mobile App; Guide Console; Montessori Knowledge Base; multimodal understanding; recommender; artwork-preserving animation; narrated story; micro-video trong hình workflow; activity handoff; annotated dataset; evaluation report.

**Q-003.** Phiếu gọi animation, generated story và dataset release là extended scope, còn minimum scope là KB, multimodal understanding + adult confirmation, constrained recommender, activity delivery và Guide Console. Đây có phải thứ tự ưu tiên chính thức không? Nếu workflow hình mới là scope cuối cùng, phần nào được nâng lên MVP?

### Giải thích Q-002/Q-003 trước khi phân loại

- **MVP bắt buộc**: phần tối thiểu phải có trong bản capstone có thể demo/use end-to-end. Nếu thiếu phần này thì sản phẩm không đạt workflow tối thiểu đã chọn.
- **Mở rộng nếu đủ thời gian (extended)**: vẫn là năng lực thuộc sản phẩm, nhưng có thể làm sau hoặc dùng bản fallback; không được coi là bắt buộc cho mốc MVP.
- **Nghiên cứu/đầu ra học thuật**: kết quả phục vụ đánh giá, dataset hoặc báo cáo nghiên cứu; không nhất thiết là chức năng người dùng phải chạy trong mọi session.
- **Không làm**: loại khỏi scope giao hàng hiện tại, dù có thể ghi lại như hướng tương lai.

Phiếu đăng ký đang ghi minimum scope gồm knowledge base, multimodal understanding + adult confirmation, constrained recommender, activity delivery và Guide Console; animation, generated story và dataset release được ghi là extended. Workflow hình mà owner chọn lại có animation, story kể và micro-video 5–10 giây. Vì vậy cần chọn một cách xử lý: **(A)** giữ phân loại theo phiếu; **(B)** nâng các phần trong workflow hình lên MVP; hoặc **(C)** coi toàn bộ workflow là target, nhưng MVP chỉ giao phần lõi và các media nâng cao là module extended. SRS hiện chưa tự chọn A/B/C.

**Q-004.** Phiếu nói early childhood nhưng catalog hiện bao phủ 0–12 tuổi. Đối tượng sản phẩm/nghiên cứu là 0–6, 0–12, hay nhóm tuổi khác? Có giữ đủ bốn band hiện tại hay chỉ dùng một số band cho MVP/trial?

**Q-005.** Sáu curriculum area trong phiếu (`Practical Life`, `Sensorial`, `Language`, `Mathematics`, `Cultural`, `Science`) có phải taxonomy chuẩn cần khóa trong SRS? Có gộp/tách mục nào theo catalog hiện tại không?

**Q-006.** Guide Console là deliverable bắt buộc của MVP chứ? Nếu có, đó là web app, chức năng trong Android app, hay nền tảng khác? Những nền tảng khác ngoài Android có nằm trong scope không?

## B. Actor, authentication và authorization

Repository hiện ghi Firebase Authentication, Google Sign-In/email-password cho người lớn, backend tự xác thực ID token và quyết định quyền; trẻ không có credential riêng. Firebase Storage/Firestore/Realtime Database bị cấm.

**Q-007.** Giữ nguyên các ràng buộc auth này cho SRS chứ? Nếu thay đổi, nêu đúng phần muốn đổi.

**Q-008.** Người lớn tự đăng ký hay chỉ được mời? Ai tạo/duyệt tài khoản Parent, Guide và Admin? Có yêu cầu xác minh email, khôi phục mật khẩu, MFA/reauth cho thao tác nhạy cảm, khóa tài khoản hoặc xóa tài khoản không?

**Q-009.** Parent, Guide và Admin là role loại trừ nhau hay một account có thể mang nhiều role? Guide có thể đồng thời là guardian của trẻ đó không?

**Q-010.** Trước đây owner xác nhận Guide cũng là người giám hộ tham gia cùng trẻ; phiếu lại cấp cho Guide quyền xem hồ sơ lớp, quản lý curriculum và override recommendation. Guide được phép truy cập một trẻ vì là guardian, vì được phân công lớp, hay phải có cả hai? Quyền classroom có cần consent/ủy quyền riêng?

**Q-011.** Ai tạo child profile, liên kết guardian, gia đình và classroom; ai gửi/nhận invite; ai xác nhận hoặc thu hồi quan hệ? Khi Guardian rời family hoặc Guide rời class thì session, history và artifact cũ được xử lý ra sao?

**Q-012.** Xin chốt ma trận quyền cho từng actor `Child trong supervised mode`, `Parent/Guardian`, `Guide`, `System Admin`, `AI/service account`. Với mỗi năng lực sau, ghi `xem`, `tạo`, `sửa`, `duyệt`, `xóa`, hoặc `không được`: child profile; consent; capture/narration; Gate A; Gate B; recommendation; feedback/history; classroom roster; curriculum/catalog; mappings; templates; recommendation override; retention/deletion; account/role/family/class links; model/safety/screen-time configuration; job/health monitoring; audit log; raw drawing/audio/transcript access.

**Q-013.** Với Admin, phiếu liệt kê account/role/family-classroom, model/safety/screen-time config, retention/consent/deletion, job/model/platform monitoring. Admin có được mở nội dung tranh, audio, narration hoặc observation để support không? Nếu được, cần reason, thời hạn quyền, user notice, phê duyệt kép hay audit nào? Nếu không, support qua metadata nào?

**Q-014.** Ai được gán Admin, đổi role, khôi phục tài khoản, unlink guardian/child và phê duyệt các thao tác quản trị? Có yêu cầu tách người cấu hình khỏi người duyệt (four-eyes) không?

**Q-015.** Có giới hạn phiên đăng nhập, logout từ xa, thu hồi token, kiểm tra revocation sau role/relationship change hoặc xác thực lại trước export/xóa dữ liệu không? Nếu chưa có chính sách, ghi TBD.

**Q-016.** Trẻ không có account; trong child mode có cần PIN/parent gate để rời màn hình trẻ, sửa profile, mở link ngoài, đổi account hoặc xem lịch sử không?

## C. Child profile, consent, privacy và retention

**Q-017.** Child profile cần lưu chính xác những trường nào: ngày sinh hay chỉ age band, tên hiển thị, ngôn ngữ, readiness, interests, materials/previous work? Trường nào tuyệt đối không thu thập? Ai được xem/sửa mỗi trường?

**Q-018.** Consent cần tách theo mục đích nào: tạo phiên, ảnh/âm thanh, gửi AI provider, lưu transcript/derived media, analytics, annotated dataset, household trial, phỏng vấn, phát hành dataset? Có opt-in riêng cho nghiên cứu và phát hành dữ liệu ngoài hệ thống không?

**Q-019.** Nếu consent bị rút giữa một job/session, dừng phần nào ngay, artifact/job đã tạo được xóa thế nào, và có thể tiếp tục bằng offline activity card không?

**Q-020.** Lựa chọn 30/60/90 ngày áp dụng theo từng child profile hay từng Parent/account? Mốc bắt đầu tính là lúc capture, lúc kết thúc session, lần sử dụng cuối hay thời điểm khác? Nếu guardian đổi lựa chọn, dữ liệu cũ áp dụng policy mới hay giữ expiry ban đầu?

**Q-021.** Hạn retention áp dụng riêng cho original drawing, raw audio, transcript, proposal/model output, animation/story/video, feedback/observation, history, cache/object copies, analytics và audit như thế nào? Có data class nào giữ lâu hơn 90 ngày không?

**Q-022.** Ai có quyền xóa một artifact, một session, toàn bộ child profile hoặc account? Xóa ngay hay theo SLA? Backup, cache, search index, provider copies và legal/audit receipt được xóa/giữ bao lâu?

**Q-023.** Dataset ghi trong phiếu chỉ dùng nội bộ cho evaluation/training, hay sẽ phát hành bên ngoài? Có bao gồm ảnh/tranh, raw voice, transcript, age, child ID/pseudonym, guide mapping không? Yêu cầu consent riêng, de-identification, license, access review và withdrawal xử lý thế nào?

**Q-024.** Trên Guide Console, Guide được xem dữ liệu nhận dạng cá nhân nào; Parent có thể ẩn tên/tranh khỏi lớp; class view cần aggregate hay từng hồ sơ? Có giới hạn xuất/tải xuống không?

## D. Luồng sử dụng, màn hình và trạng thái

**Q-025.** Narration có bắt buộc mỗi phiên không? Khi trẻ không nói/không muốn nói, hỗ trợ description do adult nhập, image-only, bỏ qua phiên, hay yêu cầu ghi lại? Ngôn ngữ và cách xác nhận transcript nào thuộc MVP?

**Q-026.** Phiếu nói child's own description được ưu tiên nếu mâu thuẫn với ảnh. Nếu narration không rõ hoặc người lớn hiểu khác trẻ, ai quyết định meaning cuối? Có lưu song song lời trẻ, transcript ASR và correction của người lớn không?

**Q-027.** Gate A và Gate B do Parent/Guardian, Guide, hay một trong hai được quyền quyết định? Có cần cả Parent và Guide đồng ý khi ở lớp? Ai giải quyết bất đồng? Trẻ có thể xác nhận bằng lời nhưng không có account không?

**Q-028.** Parent/Guide thấy một đề xuất duy nhất hay top-N kèm alternatives/reasons? Guide override recommendation nghĩa là chọn một activity khác trong tập hợp vẫn đủ tuổi/readiness/prerequisite/safety, hay phiếu kỳ vọng bỏ qua rule nào? Repository hiện yêu cầu hard safety/prerequisite không bị ranking/override làm yếu.

**Q-029.** “Mỗi session kết thúc bằng off-screen activity” có là hard requirement không? Nếu trẻ từ chối, phụ huynh dừng, không có vật liệu, safety fail, app crash hoặc mất mạng thì session đóng trạng thái gì; có thể bỏ qua/để thực hiện sau không?

**Q-030.** Mốc ~10 phút đã xác nhận là hard stop hay mục tiêu mặc định có thể cấu hình? Ai cấu hình (Admin/Parent/Guide), có giới hạn thấp hơn theo tuổi không, và timer tính capture, chờ xử lý, review, story, animation/video hay toàn bộ thời gian app foreground? Hãy xác nhận pause/background và màn hình báo cáo per-session.

**Q-031.** Activity card cần chính xác trường nào: mục tiêu, materials, home substitutes, setup photo, chuẩn bị, bước, thời gian, safety hazards, supervision, lỗi cần tránh, câu hỏi cho trẻ? Ảnh setup do Guide upload/review hay nguồn nào khác?

**Q-032.** Feedback gồm completed/partial/not attempted, interest, independence, observation note, ảnh hoạt động, mastered materials hay trạng thái khác? Ai ghi và ai có thể sửa? Completion có đồng nghĩa “mastered” không, hay mastery cần Guide đánh giá riêng?

## E. Knowledge Base, recommender và Montessori safety

**Q-033.** Mỗi Curriculum Area/Material/Activity/Objective/Prerequisite/Template cần những field nào? Xác nhận có cần age bounds, readiness, sequence, required materials, substitute, steps, estimated time, safety hazards, supervision, source citation, reviewer và version không.

**Q-034.** Guide KB workflow: ai tạo draft, ai review pedagogy/safety, ai publish/archive/version; có cần double approval; sửa catalog có ảnh hưởng session đang chạy/history cũ thế nào?

**Q-035.** Ai được review/correct mapping từ theme sang area/activity; mapping correction áp dụng cho session hiện tại, một Guide/class hay toàn hệ thống? Có cần lưu lý do và dùng feedback đó để retrain không?

**Q-036.** Prerequisite được thỏa bởi activity đã completed, Guide-confirmed mastery, Parent report hay bất kỳ activity history nào? Partial/not attempted ảnh hưởng ra sao? Làm thế nào đánh dấu placement/previous work của trẻ trước khi dùng app?

**Q-037.** Safety screening của activity cần catalog các hazard small parts, sharp tools, heat, choking, allergens, chemicals, water, outdoor/traffic hay loại nào khác? Ai đặt ngưỡng theo age/supervision và kiểm duyệt safety source?

**Q-038.** Khi Guide override, hard rules nào tuyệt đối không thể vượt qua? Cách xử lý nếu không có ứng viên hợp lệ: dừng, hỏi Guide chọn từ catalog chưa đủ dữ liệu, hay dùng activity thủ công ngoài hệ thống?

**Q-039.** Ranking cần tối ưu/hiển thị tiêu chí nào ngoài eligibility: curriculum sequence, interests, novelty/repetition, materials available, session history? Có trọng số/giải thích nào owner muốn khóa, hay chỉ yêu cầu giải thích reason mà chưa đặt weights?

## F. AI, story, animation và content safety

**Q-040.** Hiểu tranh cần đầu ra nào: subject, entities, actions, spatial relations, theme, line segments/regions, story anchors, confidence/uncertainty? Thuật ngữ nào phải được Guide/Parent xác nhận trước mapping?

**Q-041.** Trên workflow mục tiêu, cần đồng thời cả (a) animation từ nét tranh gốc, (b) narrated story và (c) micro-video giáo dục 5–10 giây, hay micro-video thay thế story/animation ở phase khác? Hãy xác định thứ tự, thời lượng, actor xem và nhóm tuổi.

**Q-042.** Nội dung dưới 6 tuổi phải reality-grounded; độ tuổi nào được phép dùng fantasy? Có cấm sự kiện bạo lực, sợ hãi, tình dục, định kiến, chẩn đoán, nhận định tính cách/phát triển, nhắc tên/địa chỉ từ tranh hay loại nội dung nào khác?

**Q-043.** Phiếu nói screen text và imagery phải safety-screen. Image nào sẽ được sinh/hiển thị ngoài tranh gốc (asset Montessori, setup photo, video frames)? Ai đánh giá filter version/false negatives; nếu screen không kết luận chắc chắn thì block, human review hay fallback?

**Q-044.** Animation thất bại phải chuyển sang still image như phiếu mô tả. Story/video/provider/content safety thất bại thì tắt riêng phase tương ứng, dùng template đã duyệt, hay chặn toàn bộ session? Cần hiển thị lỗi nào cho child/adult?

**Q-045.** Có provider/model nào được phép dùng với dữ liệu thật của trẻ không? Dữ liệu nào được gửi, ở môi trường nào, có giữ lại/training hay human review từ provider không? Nếu chưa phê duyệt provider thực, xác nhận chỉ dùng synthetic data/fixture cho capstone.

## G. Platform, offline, integration và NFR

**Q-046.** Phiếu yêu cầu capture/activity instructions dùng được khi mạng kém và generation xếp hàng tới khi có mạng. Offline cụ thể hỗ trợ xem catalog, tạo profile, capture, lưu audio, review session, xem activity card, feedback, hay phần nào? Có cho upload lại khi consent đã đổi không?

**Q-047.** Offline artifact lưu local bao lâu, mã hóa/khóa bằng gì, ai được mở, cách resume/cancel/retry/sync conflict ra sao, và xóa thế nào khi người dùng logout hoặc xóa profile?

**Q-048.** Responsiveness “nhanh đủ giữ sự chú ý trong một sitting” cần ngưỡng đo nào cho upload, ASR/understanding, recommendation, animation/story/video? Nếu chưa đo, giữ mục tiêu định tính hay đặt benchmark sau?

**Q-049.** Target platform chính xác: Android version/device range, Guide Console browser/OS, hỗ trợ tablet/phone, ngôn ngữ UI/ASR/story và accessibility cần đáp ứng mức nào?

**Q-050.** Có SLO/scale/deployment targets đã được chốt không: concurrent sessions, availability, backup, recovery time, data region, incident response, support hours? Nếu chưa có, đánh dấu TBD thay vì tự đặt số.

## H. Research protocol và acceptance criteria

**Q-051.** Đối tượng tuyển: độ tuổi, số trẻ/gia đình/lớp, địa điểm home/classroom, tiêu chuẩn chọn/loại, thời lượng trial vài tuần cụ thể? Ai là Guide được xem là “trained” và cần bao nhiêu reviewer?

**Q-052.** Dataset dự kiến có bao nhiêu tranh/child descriptions/guide labels? Ai annotates, rubric/adjudication ra sao, tách train/validation/test thế nào để tránh cùng trẻ xuất hiện ở nhiều split? Có public release hay chỉ kèm evaluation nội bộ?

**Q-053.** So sánh understanding xác nhận đúng ba điều kiện image-only, description-only, image+description chứ? Metric là exact subject accuracy, entity F1, top-k, calibration/uncertainty hay bộ nào; report phân nhóm age band và curriculum area như phiếu yêu cầu?

**Q-054.** Recommendation study so sánh constrained recommender với topical-similarity baseline. Blind rating rubric gồm developmental appropriateness, sequence correctness, safety, relevance hay gì? Đo inter-rater agreement bằng phương pháp nào; có ngưỡng đạt không?

**Q-055.** Household trial “full flow vs same activity without animation” randomize theo session, child hay family; crossover hay parallel groups; ai assign condition; bao lâu để tránh carry-over/learning effects?

**Q-056.** Primary endpoint chính xác là off-screen completion rate, screen time/session hay một chỉ số khác? Định nghĩa denominator, partial/not attempted, adult report, telemetry, missing sessions và interview coding ra sao?

**Q-057.** Có threshold thành công tối thiểu cho accuracy, sequence violation, guide rating, correction recovery, completion rate, screen time hoặc latency không? Nếu chưa có số được duyệt, giữ threshold OPEN_TBD.

**Q-058.** Trước collection có yêu cầu ethics/IRB/approval của trường, parental consent, child assent, incident response, compensation và quyền rút nghiên cứu không? Ai chịu trách nhiệm/phê duyệt?

## I. Ưu tiên quyết định

Nếu muốn trả lời nhanh, ưu tiên các mục còn mở: **Q-002–003 (sau phần giải thích ở trên), Q-008–016, Q-018–023, Q-027–030, Q-033–038, Q-041–050, Q-051–058**. Q-004, Q-007 và một phần Q-010/Q-012 đã có câu trả lời; xem bảng “Owner responses recorded” ở cuối tài liệu. Những điểm chưa quyết định có thể trả lời `TBD`; mình sẽ ghi đúng là chưa chốt thay vì tự đưa mặc định.



## Owner responses recorded — 2026-09-18

| Topic | Owner answer | SRS treatment |
|---|---|---|
| Workflow/story | Dùng workflow trong hình và có story kể. | Workflow mục tiêu gồm luồng hình và story kể; phân loại MVP/extended còn mở tại các điểm khác phiếu đăng ký. |
| Tuổi sản phẩm | 0–12. | Ghi là dải tuổi mục tiêu của sản phẩm; giữ các band catalog và điều kiện từng activity. Không suy ra đây là dải tuổi tuyển nghiên cứu. |
| Authentication | “dựa trên phiếu” / đồng ý giữ cách hiện có trong repository. | Giữ Firebase Auth và ranh giới adult identity/backend authorization hiện tại. Account lifecycle còn mở. |
| Role | Admin có quyền cao nhất; Parent/Guide giới hạn trong phạm vi trẻ của mình. | Admin là role hệ thống cao nhất. Quyền Parent/Guide theo quan hệ với trẻ; quyền lớp của Guide cần quy tắc phân công riêng vì phiếu có chức năng theo lớp. |
| Phạm vi retention | Chưa tính. | Giữ lựa chọn 30/60/90 ngày; data class, mốc tính hạn và chi tiết xóa vẫn OPEN_TBD. |
| Guide class assignment | Guide được truy cập trẻ trong lớp khi Admin cấp; nếu trẻ đã có Parent thì gửi thông báo cho Parent; Parent có thể kiến nghị đổi. | Ghi assignment server-side, notification và petition path là yêu cầu đã xác nhận; trạng thái xử lý petition, thu hồi assignment và có cần Parent consent/acknowledgement vẫn OPEN_TBD. |
| Admin raw content | Có; Admin được xem drawing, raw audio, transcript và observation khi cần; auth dùng Firebase. | Ghi raw-content visibility là OWNER_CONFIRMED; reason, user notice, break-glass, time limit, dual approval, audit detail, retention và provisioning vẫn OPEN_TBD. |
| Chi tiết nghiên cứu | Chưa rõ. | Giữ câu hỏi/phương pháp nghiên cứu trong phạm vi đăng ký; cỡ mẫu, ngưỡng, protocol và quyết định phát hành dữ liệu vẫn OPEN_TBD. |

## Owner responses recorded — 2026-09-19 (superseding earlier open items)

| Topic | Owner answer | SRS treatment |
|---|---|---|
| Release scope | MVP includes animation, narrated story and micro-video. | B20 marks all three as MVP target scope. |
| Owner/child cardinality | One Owner Caregiver per ChildProfile; one owner may create many ChildProfiles; no child account. | B22/B24 replace the prior multi-parent ambiguity. |
| Guide cardinality | A ChildProfile may have multiple Guides; active assignments may overlap. | B22 permits multiple assignments. |
| Guide duration | Share duration is 3/7/15/30 days, effective immediately. | B22 assignment model and expiry rules. |
| Parent revoke | Parent may revoke any time; during an active session the session stops immediately and UI shows a message. | B23 immediate revoke state and event. |
| Guide rights | Guide has Parent-like rights for the entire valid share period, below Owner. | B22 records the baseline; exact raw/history field-level permission remains TBD. |
| Live monitoring | Parent sees all necessary live information with metadata minimized. | B23 defines the redacted live projection. |
| Parent Web | Phase 2; management, monitoring, child information updates and feedback; not implicitly a session runner. | B21 product surface and API boundary. |
| Retention | 30/60/90 applies to all child/session data classes; expired data becomes inaccessible archive before purge. | B26 data-class and archive lifecycle. |
| Audit | Audit retention is separate from child-data retention. | B25/B26 separate policy. |
| Notifications | Combined channels. | Channel matrix and retry remain OPEN_TBD. |
| Concurrent sessions | One Guide runs one session at a time. | B23 invariant. |
| Admin raw access | Break-glass. | B25 safeguards; dual approval/time window/notice remain OPEN_TBD. |


