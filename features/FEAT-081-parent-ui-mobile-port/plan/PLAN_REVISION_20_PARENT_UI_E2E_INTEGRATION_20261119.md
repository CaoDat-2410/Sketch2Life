# FEAT-081 — Plan Revision 20: nối end-to-end Parent Expo UI với API thật

- Trạng thái: APPROVED / IMPLEMENTATION IN PROGRESS (Addendum 35)
- Implementation: NOT STARTED
- Ngày: 2026-11-19, Asia/Saigon
- Nhánh: feature/fe-mobile-remediation
- Baseline code: f90226f37b265a8a35b02c95da5daa74146ad0a9
- Baseline UI evidence: 5aa9443a772462d247a6018a62aab4e37d2092ae

## 1. Mục tiêu

Nối các màn Parent Expo mới với API/backend và AI service thật theo luồng SRS; xác định rõ những API đã có, những API chỉ có khung code, những API thiếu và các phụ thuộc chưa sẵn sàng. Không coi màn preview hay dữ liệu mô phỏng là kiểm thử end-to-end.

Phạm vi chính:

1. Đăng nhập Parent, hồ sơ trẻ, chọn chủ đề hoặc bài học.
2. Hướng dẫn vẽ SVG tùy chọn.
3. Chụp/chọn ảnh bắt buộc, phân tích tranh, kiểm tra lệch chủ đề và xác nhận chủ thể.
4. Gợi ý hoạt động catalog-first, lưu lựa chọn hoạt động chính vào StoryRun.
5. Sinh/xem/sửa bằng gợi ý AI/xác nhận kịch bản.
6. Tạo video từ đúng ảnh và kịch bản, xem kết quả và các hoạt động sau video.
7. Nối các màn phụ trợ được SRS yêu cầu, trừ quota và payment.

Quota, mua lượt, subscription, giá và payment thuộc phạm vi của người đang làm phần đó. Plan này không sửa các contract/bảng của họ, không gọi API quota, không giả lập quota và không bỏ qua admission. Video chỉ được test qua admission thật sau khi contract/quyền tích hợp của phần quota được bàn giao.

## 2. Nguồn chuẩn và bằng chứng giao diện

- SRS sản phẩm: bản v2.7-draft được D-209 chỉ định trong docs/context/SRS_AUTHORITY.md; vẫn là bản unsigned. Dùng §§1–31 làm yêu cầu mục tiêu, §32 chỉ làm bằng chứng as-built theo môi trường.
- UI reference: thư mục PARENT_UI_API_ANNOTATED_EMULATOR_20261118, gồm 32 ảnh raw, 32 ảnh chú thích, bảng API_BUTTON_MAP.md, accessibility XML và capture log. Bản này được chụp từ commit 5aa9443a bằng EXPO_PUBLIC_FEAT081_VISUAL_PREVIEW=true.
- Preview hiển thị nhãn dữ liệu mô phỏng; các handler no-op và không gửi Firebase, backend hoặc Modal request. Các dòng CLIENT trong API_BUTTON_MAP chỉ nói source có client call, không chứng minh API đã chạy.
- Worktree hiện tại ở f90226f3 sau khi merge dev. Chín commit sau 5aa9443a có thay đổi backend/SRS/OpenAPI và hồ sơ quản trị; không có thay đổi apps/ui-mobile. Vì vậy giữ nguyên 32 màn làm bản đồ UI, nhưng đánh giá API theo code hiện tại sau merge.
- Bằng chứng Parent cũ trong EV-063-87 và ảnh Teacher EV-063-75 chỉ dùng để hiểu lịch sử, không coi là pass cho UI/API hiện tại.

## 3. Ranh giới phạm vi

### Trong plan

- UI Parent Expo trong apps/ui-mobile.
- Firebase Authentication và API backend cho Parent.
- Modal AI thật ở các bước được SRS cho phép, sau khi có durable request/job contract.
- Data synthetic được tạo qua luồng ứng dụng/API thật; tranh kiểm thử được tạo riêng, không lấy dữ liệu trẻ thật.
- Nối lesson public/shared có quyền truy cập và pin chính xác lesson/version/hash.

### Ngoài plan

- Quota summary, quota reservation/consumption, mua thêm lượt, subscription, thanh toán MoMo/VNPAY và điều chỉnh giới hạn trường/tài khoản.
- Sửa UI hoặc API Teacher/Manager/Admin. Các luồng này chỉ là nguồn tạo lesson đã duyệt để Parent đọc.
- Bypass consent, bypass video admission, mock response, preview harness, fixture thành công, dữ liệu child thật.
- Triển khai/đổi model hay provider ngoài lựa chọn trong SRS.

## 4. Quy ước trạng thái

- READY-SOURCE: route và client cùng tồn tại trong source; vẫn cần kiểm tra contract/runtime sau merge.
- PARTIAL-LEGACY: có route/client nhưng đang dùng flow hoặc schema cũ, không đạt target SRS.
- FE-STUB: màn hình/use case có khung nhưng trả unavailable hoặc không gửi request.
- BE-ONLY: backend có route, nhưng Parent UI/client chưa gọi.
- MISSING: không thấy route/contract hoặc persistence cần cho workflow.
- EXTERNAL-GATE: chờ phần quota/payment hoặc dữ liệu lesson được duyệt từ luồng khác.
- PREVIEW-ONLY: có ảnh/layout nhưng không phải bằng chứng request thật.

“Có route” không đồng nghĩa route đã được kiểm tra bằng HTTP ở baseline hiện tại.

## 5. Kiểm kê hiện trạng theo capability

| Capability | Đã có trong source hiện tại | Trạng thái và thiếu gì |
|---|---|---|
| Đăng nhập/đăng ký | ParentAuth có Firebase email/password, Google, reset/change password; backend có registration và current-user/role resolution. | READY-SOURCE. Chưa có bằng chứng chạy end-to-end từ bản UI mới sau merge; cần xác nhận app config, Firebase provider và role Parent thật. |
| Hồ sơ Parent | FE gọi GET/POST/PATCH/DELETE /v1/parent/profiles; backend router tương ứng đã mount. Patch/delete có revision/idempotency ở client. | READY-SOURCE cho CRUD cơ bản. Phải xác nhận DTO/error và response delete-pending trên API hiện tại. Dữ liệu thật vẫn bị chặn khi chưa có consent hợp lệ. |
| Consent | UI thể hiện trạng thái consent; các method consent hiện unavailable. Không thấy Parent policy/grant/revoke route trong router hiện hành. | MISSING cho dữ liệu trẻ thật. E2E đầu tiên chỉ dùng profile synthetic với data_origin được backend xác nhận là synthetic. Không tạo consent giả. |
| Hồ sơ đang chọn/run đang mở | FE có active/current, đọc run detail và tạo StoryRun; backend có các route này. | READY-SOURCE, chưa runtime-verified. Resume/error khi active run đã tồn tại cần chạy bằng state server thật. |
| Lesson Gallery | FE gọi danh sách, chi tiết, lời mời lesson/parent-group và accept/decline; backend Lesson Library có các route. | READY-SOURCE một phần. FE chưa dùng cursor đầy đủ ở một số list và kiểu lỗi/DTO cần đối chiếu. Cần một lesson public/shared thật, có quyền Parent và version/hash hiện hành; EV-063-87 trước đây từng có 0 lesson đủ điều kiện, nên dữ liệu hiện tại chưa được chứng minh. |
| Presentation của lesson trong Parent | Parent có màn thư viện/chọn bài và giữ pin lesson. | PARTIAL. Ảnh preview không chứng minh media presentation hiển thị được. Xác nhận API detail trả slide/media refs và Parent có renderer đúng thứ tự/version; nếu thiếu thì bổ sung trong nhánh lesson-read, không tái tạo lesson bằng fixture. |
| Entry theo chủ đề/bài học | Có gallery và màn chủ đề; topic cards hiện là nhóm chủ đề cố định/local. Run create use case hỗ trợ lesson pin nullable. | PARTIAL. Cần hai entry lựa chọn rõ “Theo chủ đề” và “Theo bài học”, hỗ trợ bỏ qua cả hai theo SRS. Trước khi tạo run cần đảm bảo ảnh đã được chọn/chụp. |
| Ba thẻ gợi ý chủ đề + ô nhập riêng | Màn topic hiện có 6 nhóm chủ đề tĩnh; chưa có 3 thẻ topic được đổi ngẫu nhiên theo lượt mới và ô nhập topic riêng. | OWNER-REQUESTED / NOT IMPLEMENTED. Chọn 3 topic khác nhau từ taxonomy được duyệt; giữ nguyên bộ thẻ trong cùng một draft/session để không đổi lựa chọn khi back/resume. Đây chưa có trong SRS v2.7-draft. |
| Ba gợi ý đối tượng thuộc topic + ô nhập riêng | Chưa có bước gợi ý ba con vật/đồ vật cụ thể sau khi Parent chọn topic; chưa có kiểm tra custom subject có thuộc topic hay không. | OWNER-REQUESTED / NOT IMPLEMENTED. Catalog topic-to-subject trước; Qwen chỉ tạo draft khi catalog không đủ và capability bật. Cần amendment SRS vì subject gợi ý trước ảnh khác với câu hiện tại rằng Parent không preselect subject. |
| Voice idea / Whisper | UI có chỗ ghi âm nhưng ParentApi transcribeAudio và confirmTranscript unavailable; không có Parent route /idea hiện hành. | MISSING. Cần upload/audio contract, job status, transcript revision và xác nhận người lớn; không gửi âm thanh trước khi có contract. |
| SVG guide Parent | Backend có POST /api/parent/v1/ai/sketch-guides nhưng gọi FLUX và trả PNG; FE controller createGuide hiện báo chưa khả dụng, ParentApi cũ gửi 3 bước. | PARTIAL-LEGACY, không đạt SRS. Target là SVG catalog-first, 4–8 bước progressive, AI draft khi capability bật, không gửi profile/ảnh/giọng nói trẻ. Guide lỗi/bỏ qua không chặn capture. Không dùng FLUX cho guide. |
| Camera/photo picker | UI có camera/gallery native và bước bắt buộc chọn ảnh. | READY-UI, nhưng preview harness chỉ mô phỏng thao tác. Cần kiểm tra trên app Android thật và quyền camera/photo picker. |
| Đính kèm ảnh và phân tích VLM | Có POST /api/parent/v1/ai/drawing-understandings, nhận base64 JSON, lưu original/derived asset và gọi Modal đồng bộ. FE gọi route này sau khi tạo run. | PARTIAL-LEGACY. SRS target cần asset upload/attach có kiểm soát và AI Job bền vững; route hiện tại gộp ingest+analysis, chưa dùng upload-session/chunk contract. Request dài đồng bộ không phải bằng chứng job durable. |
| Kiểm tra topic/lesson lệch ảnh và chụp lại một lần | VLM trả candidate/subject; chưa thấy response/UI state để thông báo incompatibility với topic/lesson và giới hạn một lần retake. | MISSING. Cần thêm kết quả compatibility, hành động đổi topic hoặc chụp lại đúng một lần; sau retake dùng subject ảnh mới và giữ exact lesson pin làm kiến thức. |
| Xác nhận chủ thể/ngữ cảnh | FE và backend có subject-confirmation, context-confirmation; create-run response có snapshot/hash. | READY-SOURCE, nhưng một số OpenAPI summary còn gắn [PROPOSAL]. Cần đóng contract, idempotency, stale revision và error mapping trước khi gọi runtime. |
| Gợi ý hoạt động | Có ParentActivitySuggestionService ở application layer. Không thấy Parent HTTP route được mount; ParentApi.suggestActivities trả unavailable. | MISSING-ROUTE. SRS yêu cầu catalog-first từ lesson public/shared Parent có quyền; exact route/request/response còn OPEN-TECHNICAL, không tự coi endpoint cũ hoặc DemoApi là contract. |
| Lưu hoạt động chính | UI chặn story bằng activitySelectionPersisted=false. Chưa có API/persistence lưu ID/version/content snapshot của lựa chọn vào StoryRun. | HARD BLOCKER. Phải lưu đúng một hoạt động, nguồn/version/hash và danh sách đã hiện/từ chối để tránh lặp; nếu không có candidate, chỉ cho đúng 3 draft có quality gate rồi Parent chọn. |
| Tạo/viết lại story | Có POST /api/parent/v1/ai/story-runs/{run_id}/story-revisions ở FE và BE; xác nhận script có route /v1/story-runs/{id}/script-confirmation. | PARTIAL. UI chặn do chưa lưu activity. Story revision hiện gọi Modal đồng bộ với timeout rất dài; thiếu GET /v1/jobs/{job_id} để theo dõi job bền vững như SRS. Cần kết quả có schema/revision/hash, tối đa 3 lần viết lại, không sửa scene trực tiếp. |
| Video Parent | Parent UI platform controller trả unavailable. Có route video legacy theo /v1/sessions/{session_id}/story-video-jobs, nằm trong session/demo flow, không phải StoryRun Parent. | MISSING cho Parent StoryRun. Cần API video-generation/status/safety/playback/unsuitable/regenerate/complete gắn với StoryRun và Modal LTX-2.5 theo SRS. Không nối Parent UI sang session/Lightning route cũ. |
| Video quota/payment | Có màn quota trong 32 ảnh; getVideoQuota trả unavailable. | DEFERRED theo yêu cầu. Không nối, không tạo API giả, không thao tác mua/thanh toán. Video E2E phụ thuộc contract admission của người đang làm quota; tuyệt đối không bỏ qua gate. |
| Run lifecycle/history | GET active/detail và create hiện có; backend sau merge đã có POST /v1/story-runs/{id}/cancel, nhưng mobile cancelStoryRun vẫn unavailable. Không có list history hoặc completed-run delete/complete route được nối. | PARTIAL/BE-ONLY. Nối cancel theo contract; history/delete/complete cần contract SRS và backend trước khi nối. |
| Hoạt động sau video | Run pin có thể giữ lesson pin; Parent UI/API hiện chưa có response view chứng minh trả toàn bộ activities của exact lesson version hoặc activity đã chọn khi không pin. | MISSING. Cần view trạng thái VIDEO_READY/hoạt động, lấy exact pinned content; no-pin phải dùng activity snapshot đã chọn, không query catalog mới. |
| Chia sẻ hồ sơ, bài đã dạy, feedback | UI có màn share/delivery/feedback; controller và ParentApi trả unavailable. Không thấy route Parent tương ứng; một số path chưa được SRS chốt. | MISSING/OPEN API CONTRACT. Không tự tạo path. Chốt scope, quyền, retention và API riêng rồi mới nối. |
| Notifications | UI có inbox/đánh dấu đã đọc; controller trả unavailable, không có route Parent inbox trong router hiện hành. | MISSING. Cần list cursor, unread/read mutation, error/loading/empty states. |
| Bottom bar/settings/local filters | Điều hướng, filter và tùy chọn cục bộ hiện là local state. | Không cần API trừ khi SRS yêu cầu lưu setting giữa thiết bị. Xác nhận sign-out/settings cần gọi Auth; các filter không giả làm server data. |

## 6. Bản đồ 32 màn và dự kiến nối

| Màn trong evidence | Nối/điều chỉnh |
|---|---|
| 01 Đăng nhập | Firebase sign-in → backend GET /api/auth/v1/me; chặn sai role. |
| 02 Tài khoản | Firebase đổi mật khẩu/reset, sign-out và refresh session; không gọi API profile trẻ. |
| 03 Cài đặt | Guide setting giữ local; bật guide chỉ cho phép yêu cầu ở session sau, không tự gọi AI. |
| 04–05 Trang chủ | GET profiles + GET active run; entry rõ “Theo chủ đề”/“Theo bài học” và action chụp ảnh. Notification badge chỉ hiện khi API inbox có thật. |
| 06–10 Gia đình/hồ sơ/chia sẻ | GET/POST/PATCH/DELETE profile; consent gate synthetic/legal; share giữ disabled cho tới khi API/permission contract có. |
| 11–12 Thư viện/chọn bài | Lesson list/detail + invitations; xác thực quyền hiện hành, pin exact version/hash; hiển thị presentation/media nếu detail contract có. |
| 13 Chủ đề | Tách thành hai trạng thái: chọn topic (3 thẻ topic đổi theo draft mới + ô nhập topic) rồi chọn đối tượng trong topic (3 thẻ đối tượng + ô nhập riêng). Off-topic/ambiguous input phải dừng để sửa topic hoặc đối tượng; không tự đổi ý nghĩa. Cần SRS amendment trước khi code vì có xung đột với rule không preselect subject. |
| 14 Ý tưởng | Gửi text qua StoryRun context; ghi âm chỉ bật khi Whisper upload/job/transcript confirmation có API. |
| 15 Gợi ý vẽ | Catalog SVG trước; render step theo thứ tự, nút bỏ qua; lỗi/no-source/timeout vẫn đi tới chụp ảnh. |
| 16–18 Chụp tranh | Android camera/photo picker; chọn ảnh là bắt buộc trước network create/analyze; upload bằng contract được chốt. |
| 19 Bản ghi | Giữ preview transcript và yêu cầu người lớn sửa/xác nhận sau khi Whisper route có. |
| 20 Chủ thể | Hiển thị VLM output/confidence và cho người lớn xác nhận/sửa; nếu lệch topic/lesson thì đổi hoặc retake một lần. |
| 21–22 Ngữ cảnh | Đọc snapshot từ run, xác minh profile/consent/lesson pin và context hash; POST xác nhận idempotent. |
| 23 Hoạt động | Catalog-first suggestions, chọn một hoạt động; lưu server-side trước khi mở story. Nếu API/job lỗi thì ở lại đây, không đi tắt. |
| 24 Kịch bản | Sinh qua durable job, hiển thị trạng thái, rewrite tối đa 3, xác nhận revision/hash trước khi video. |
| 25 Trạng thái | Poll run/job; sau này hiển thị video state. Video call chỉ sau khi quota admission API đang được làm bàn giao contract. |
| 26 Lịch sử | Nối khi có StoryRun list/pagination; cancel route hiện có ở BE cần thêm client; delete/complete chờ contract. |
| 27 Bài đã học | Nối lesson delivery history/feedback khi backend contract và Parent authorization có. |
| 28 Lượt dùng | Để nguyên ở trạng thái chờ phần quota; không nối API trong plan này. |
| 29–31 Thông báo | Nối inbox/cursor/read khi backend route có. Không dùng preview items làm dữ liệu. |
| 32 Thanh điều hướng | Local navigation; tab Câu chuyện chỉ hiển thị lịch sử thật khi route list đã có. |

## 7. Trình tự triển khai đề xuất

### M0 — Contract freeze và baseline sau merge

1. Xuất inventory từ OpenAPI đang được phục vụ và router hiện tại; so với ParentApi, ParentAuth, application use cases và 32 dòng mapping UI.
2. Với mỗi request ghi rõ method/path, role/scope, request/response schema, idempotency, expected revision, status/error contract, pagination, timeout/job semantics và data owner.
3. Đánh dấu route có [PROPOSAL] là chưa freeze. Đặc biệt chốt activity suggestion/selection, asset upload, AI job polling, topic compatibility/retake, Parent consent, post-video activities và run history.
4. Ghi amendment cho cả hai tầng: ba thẻ topic thay đổi theo draft mới + ô nhập topic; sau khi chọn topic, ba gợi ý đối tượng thuộc topic + ô nhập đối tượng. Chốt rule off-topic, random-set stability và nguồn catalog/Qwen. SRS hiện hành nói Parent không preselect subject, nên không triển khai gợi ý đối tượng trước capture cho tới khi owner amendment được ghi vào SRS.
5. Xác nhận data source: một tài khoản Parent thật trên Firebase dev, hồ sơ synthetic do backend tạo, một lesson version đã public/shared và có quyền truy cập; không nhập fixture thành công vào UI.

### M1 — Chạy thật app shell, Firebase, profile

1. Tắt visual preview flag; chạy app Expo Android thật.
2. Đăng ký/đăng nhập Parent bằng Firebase dev và xác minh role qua backend; thử sign-out, Google nếu provider đã cấu hình, reset/change password.
3. Tạo/list/edit/request-delete hồ sơ synthetic bằng UI và API; xác minh idempotency, revision, pending receipt, quyền chỉ thấy profile của Parent.
4. Với profile thật/unknown origin, chặn học cho tới khi consent API và văn bản/purpose/version hợp lệ tồn tại.

### M2 — Hai cách bắt đầu và lesson/topic/guide tùy chọn

1. Trang chủ đưa ra hai entry rõ: theo chủ đề và theo bài học. Theo SRS, topic và lesson vẫn có thể bỏ qua; ảnh vẫn bắt buộc.
2. Nhánh theo chủ đề có hai tầng: ba thẻ topic được xáo/chọn lại ở mỗi draft mới, kèm ô nhập topic riêng; sau khi chốt topic, hiện đúng ba gợi ý đối tượng thuộc topic đó, kèm ô nhập đối tượng riêng.
3. Gợi ý lấy từ taxonomy/topic-to-subject catalog đã duyệt trước; chỉ gọi Qwen để tạo draft khi catalog không đủ và capability bật. Không gọi AI chỉ để xáo thẻ. Giữ nguyên set ID và thứ tự khi quay lại/resume cùng draft; set mới chỉ khi Parent chủ động bắt đầu draft mới hoặc đổi topic.
4. Custom topic/đối tượng phải được chuẩn hóa và kiểm tra liên quan. Nếu đối tượng ngoài topic hoặc không chắc, dừng ở bước chọn; cho sửa đối tượng, chọn một trong ba gợi ý hoặc đổi topic. Không âm thầm đổi topic/subject và không gửi giá trị chưa xác nhận vào guide/story.
5. Đối tượng đã chọn là gợi ý vẽ, không thay VLM: guide SVG có thể dùng topic + đối tượng generic; sau capture VLM vẫn nhận diện tranh và kiểm tra topic/lesson compatibility. Ảnh lệch theo FR-P-12 thì cho đổi topic hoặc chụp lại tối đa một lần.
6. Nhánh theo bài học dùng exact public/shared lesson version/hash, presentation, guide và activities của lesson đó; không trộn ngẫu nhiên đối tượng từ topic catalog vào bài học.
7. Thư viện xử lý invitation, access revoke và không tự thay lesson pin sang latest. Hiển thị presentation/media nếu API detail hỗ trợ; nếu thiếu thì ghi API gap, không dựng content tĩnh.
8. Thay line guide raster/FLUX bằng SVG catalog-first và deterministic renderer; AI draft chỉ khi capability bật. Chỉ gửi topic/đối tượng generic và guide contract, không gửi profile, tuổi chính xác, ảnh/audio hay ID trẻ. Skip/fail/timeout vẫn tiếp tục capture.

### M3 — Ảnh, upload và VLM

1. Camera/gallery trả file thật của thiết bị; kiểm mime/size, preview, thay ảnh và retry chọn ảnh trước khi gửi.
2. Thay request base64 gộp cũ bằng asset-upload/attach contract theo SRS, giữ original/hash/provenance và kiểm tra storage/safety.
3. Gọi VLM qua durable job; app poll job/status, không giữ HTTP request treo hàng chục phút.
4. Trả candidate, confidence, revision và topic/lesson compatibility. Người lớn sửa/xác nhận subject nhận diện.
5. Với nhánh topic đã được amendment duyệt, xác thực custom subject trước guide; sau ảnh vẫn so VLM subject với topic/lesson. Nếu ảnh mismatch, cho đổi topic hoặc chụp lại tối đa một lần. Sau retake dùng subject của ảnh mới, lesson pin vẫn là nguồn kiến thức.

### M4 — Catalog-first activity, selection và persistence

1. Backend dựng activity candidates từ lesson versions PUBLIC/SHARED Parent được xem; lesson pin giới hạn exact version/hash. Với nhánh topic, truyền subject suggestion đã được Parent xác nhận như context text đã cấu trúc, không truyền dữ liệu trẻ.
2. Qwen3.5 chỉ chọn request-scoped IDs/lý do; backend hydrate canonical activity. Không gửi raw image/audio/child identifiers.
3. Nếu không candidate nào phù hợp, có thể trả đúng 3 draft qua schema/safety/age/Montessori/outdoor/duplicate quality gates; draft không ghi vào catalog.
4. “Gợi ý bộ khác” phải loại choices đã hiện/bị từ chối.
5. Parent chọn một hoạt động; API lưu activity ref/version/content snapshot vào StoryRun với revision/idempotency. Story generation vẫn bị khóa cho tới khi đọc lại xác nhận selection đã persisted.
6. Chốt recovery cho empty/error/unknown result theo SRS open technical gate; không cho qua story nếu chưa có hoạt động được người lớn chọn.

### M5 — Story và xác nhận

1. Nối story revision với persisted activity, confirmed subject/context, pinned artwork, optional topic/lesson và transcript đã xác nhận.
2. Chuyển AI call dài thành job bền vững có job ID, stage, retry policy và safe error; có API poll được.
3. Validate response schema, revision/hash; hiển thị cảnh báo/loading/failure/retry từ backend.
4. Cho gợi ý viết lại tối đa 3 lần; không cho sửa trực tiếp scene.
5. Bắt buộc xác nhận story/storyboard revision hash trước khi mở video.

### M6 — Video và sau video

1. Tạo API Parent video generation gắn StoryRun, không dùng legacy session route.
2. Modal LTX-2.5 worker chạy pipeline theo SRS: ảnh trẻ làm reference, storyboard/script đúng revision, job bền vững, consistency/safety, playback authorization.
3. Thêm status/polling, safety-blocked/error/recovery, mark-unsuitable, tối đa hai full-video regeneration, complete/cancel lifecycle và video player.
4. Nối điểm admission tới quota API do contributor khác bàn giao. Không code billing/quota tại FEAT-081, không bỏ qua admission. Nếu chưa có contract, video E2E dừng rõ tại gate và được báo BLOCKED, không đánh dấu complete.
5. Sau VIDEO_READY: lesson pin hiển thị mọi activity của exact version/hash và đánh dấu activity chính; no-pin hiển thị activity snapshot đã chọn. Không query activity mới sau video.

### M7 — Màn phụ trợ

1. Nối cancel đang có ở backend; chốt API list/history và delete/complete theo SRS trước khi kết nối.
2. Chốt API sharing/revoke, lesson delivery/feedback và notification inbox/read; không tự đặt path chưa có trong OpenAPI.
3. Quota screen và purchase/payment tiếp tục thuộc người khác; không thay đổi.
4. Duyệt lại mọi empty/error/unavailable state để chúng không thể hiện nhầm là dữ liệu rỗng hoặc thành công.

### M8 — E2E thật và evidence

Chỉ bắt đầu sau khi M0–M6 có API/permission/Modal worker ổn định và amendment topic được chấp thuận:

- Luồng topic: nhận ba topic cards mới, chọn một; nhận ba đối tượng thuộc topic; thử custom subject hợp lệ và một subject lệch topic; xác nhận trường hợp lệ tiếp tục, trường hợp lệch bị giữ lại để sửa. Kiểm tra back/resume không xáo lại set của cùng draft.
- Luồng no-preset: topic có hoặc không, ảnh thật được tạo riêng để kiểm thử, subject, context, activity catalog/draft, story, xác nhận, admission thật, video và post-video activity.
- Luồng lesson-pinned: chọn lesson public/shared thật, pin exact hash, xem presentation/guide, ảnh, kiểm tra lệch chủ đề, activity theo đúng version, story/video, toàn bộ hoạt động sau video.
- Kịch bản lỗi: activity empty/timeout, ảnh không phù hợp, recapture một lần, Modal job pending/fail, resume app, mất lesson access, active run conflict, safety block.
- Mọi bước chạy qua UI Android thật, API thật và Modal thật. Tắt preview harness. Không dùng fixtures/mock response/“success” cài sẵn.
- Evidence lưu dưới FEAT-081/evidence: ảnh màn thật, request ID/job ID, status/error codes, thời lượng từng stage và redacted logs. Không lưu token, .env, credential hay dữ liệu child thật.
- Mỗi luồng phải chứng minh dữ liệu server được đọc lại sau mutation; không chỉ dựa trên state trong React.

## 8. Cổng chấp nhận

1. 32 màn được phân loại rõ: API thật, local-only, unavailable có chủ đích hoặc ngoài phạm vi; không còn preview content xuất hiện trong build/test thật.
2. Firebase login và backend role resolution hoạt động; Parent chỉ đọc/sửa hồ sơ thuộc mình.
3. Run không thể bắt đầu nếu chưa có ảnh; không gửi ảnh/audio trẻ vào SVG guide.
4. Topic path có ba topic cards thay đổi theo draft mới và ô nhập riêng; sau chọn topic có ba đối tượng thuộc topic và ô nhập riêng. Set không đổi khi quay lại/resume cùng draft.
5. Custom topic/subject lệch hoặc mơ hồ không đi tiếp cho tới khi người lớn sửa subject, chọn gợi ý phù hợp hoặc đổi topic; không tự diễn giải thay.
6. Kiểm tra đủ nhánh topic/no-preset và exact lesson pin. Lesson path giữ đúng version/hash.
7. Subject/context được người lớn xác nhận; sau ảnh, mismatch xử lý tối đa một lần chụp lại.
8. Main activity được persisted trước story; không thể vượt gate bằng thao tác UI hoặc request retry.
9. Story revision đúng schema, tối đa ba rewrite và được xác nhận trước video.
10. Video luôn gắn đúng StoryRun/artwork/script, qua admission thật, automated safety và authorized playback.
11. Sau video trả đúng activity snapshot/version; cancel/history/notification/share không báo thành công nếu route chưa có.
12. Quota/payment không bị sửa hoặc bypass; nếu chưa được bàn giao thì video E2E được báo blocked tại admission.

## 9. Rủi ro và điểm chặn

- **P0:** Parent activity route và selection persistence chưa có; đây là chặn trực tiếp từ màn 23 sang màn 24.
- **P0:** Parent video API/worker linkage thiếu; session video route cũ không thay thế được.
- **P0:** Video E2E phụ thuộc quota admission đang do người khác làm. Không thể hứa full video pass trước khi có handoff contract.
- **P1:** Capture hiện dùng base64 + VLM đồng bộ; cần chuyển đúng upload/job lifecycle để tránh request treo và mất khả năng resume.
- **P1:** Guide hiện sai công nghệ/format mục tiêu: FLUX raster 3 bước; controller đã chặn UI, nên phải thay bằng SVG route trước khi bật.
- **P1:** Lesson public/shared thật chưa được chứng minh có trong database hiện tại; cần tạo qua luồng Teacher/Manager thật.
- **P1:** Consent cho real child data và consent API chưa có; chỉ dùng synthetic trong E2E trước.
- **P1:** Ba thẻ topic random rồi ba gợi ý đối tượng trong topic chưa có trong SRS; còn mâu thuẫn với rule “không preselect subject”. Cần amendment rõ nguồn gợi ý, validation off-topic và cách gắn subject với SVG guide trước khi bật.
- Các API status từ bản chú thích 5aa là source annotation, còn report runtime cũ không đại diện cho code sau merge.

## 10. Điều kiện và giới hạn triển khai

- Owner đã duyệt plan Rev20 bằng Addendum 35 trong approvals/TASK_APPROVAL.md; implementation bắt đầu theo các phase và cổng trong tài liệu này.
- M0 phải đóng contract/API gaps trước khi bật luồng tương ứng, nhất là activity persistence, asset upload/job polling và Parent video boundary.
- Ghi amendment/decision cho ba thẻ topic và ba gợi ý đối tượng thuộc topic; giải quyết mâu thuẫn “không preselect subject” trước khi bật UI/API gợi ý đối tượng.
- E2E dùng Parent account/profile synthetic do Firebase/backend thật tạo và lesson public/shared được cấp quyền qua luồng thật. Không dùng fixture/mock success, preview harness hay dữ liệu trẻ thật.
- Quota/payment là workstream loại trừ. Chỉ dùng admission contract thật sau khi contributor bàn giao; nếu chưa có, dừng video tại gate và báo BLOCKED.
- Addendum 35 cho phép kiểm tra frontend/backend/API, Android emulator và các Modal inference cần thiết cho flow không-video trong giới hạn được ghi ở approval. Không triển khai warm-loop, không chạy tải GPU lặp.
- Không commit hoặc push nếu chưa có yêu cầu riêng.
