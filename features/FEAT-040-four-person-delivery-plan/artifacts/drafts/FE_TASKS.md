# Phân việc frontend — P1

Đây là backlog đề xuất triển khai từ SRS v3.1, không cấp approval cho runtime. P1 chịu trách nhiệm UI Android cho Child và Teacher/Admin desktop; P4 chịu trách nhiệm nối các phần sau khi contract/handoff đã được duyệt. P1 vẫn phải tự kiểm tra component/UI của mình; P4 không nhận thay mọi test. Giữ React Native; runtime/version Android, canvas engine/sync và công nghệ Teacher/Admin web phải chốt bằng ADR trước phần triển khai phụ thuộc. Không có ngày, giờ, sprint duration hoặc deadline trong phân việc này.

## Cách nhận task và bàn giao

- FE-01 là một stream fixture/contract độc lập: runner không cần API sống, DB, tài khoản thật, GPU hoặc kết quả từ người khác. P1 dùng synthetic fixtures, không có dữ liệu trẻ thật. Bốn stream nền tảng và integration allocation được xem riêng theo ADR-0006.
- FE-02–FE-05 ưu tiên bộ điều phối lớp tối thiểu: join/admission, chuẩn bị phiên, vẽ/recovery và Teacher control. Đây là thứ tự phụ thuộc/ưu tiên, không bỏ các màn hình còn lại. FE-06–FE-12 hoàn thiện vòng học; FE-13–FE-15 hoàn thiện vận hành Admin. Một FE có 34 UI responsibilities, vì vậy không mở tất cả task cùng lúc.
- Prerequisite dạng `H-*` là handoff contract/version + fixtures + conformance evidence; P4 nối ID này với task BE/INT trong bảng tổng. UI có thể phát triển state từ fixture trước handoff, nhưng acceptance kết nối thật chỉ đạt sau handoff và integration task approval.
- Mỗi card cần feature implementation plan/approval riêng, review contract và evidence trong feature đó. Khi visual mới cần asset: sinh vào `assets/generated/`, ghi provenance, lấy visual approval, rồi mới đưa vào `assets/approved/` và `assets/applied/` theo AGENTS. Wireframe/fixture prototype chưa duyệt không được gắn production visual đã approved.
- DoD chung: code/UI state review; command/query dùng adapter/versioned contract; lỗi loading/empty/stale/pending/failed/revoked thể hiện đúng; không lưu token/QR/child media vào telemetry; evidence là synthetic screen states, positive/negative test outcome và exact source/contract revision. Không đưa S3/Lightning/Runpod credentials/endpoints vào mobile. Fixture pass không chứng minh inference, video generation, tải 40 trẻ hoặc classroom pilot.

## FE-01 — Nền tảng UI chạy độc lập và prototype canvas Android

- **Chủ trì / review:** P1; P2 review command/operation shape, P4 review runner/handoff. Đầu ra nền tảng độc lập, chưa nối API thật.
- **Phạm vi / bàn giao:** RN fixture runner với navigation/state adapter, component status/alias/help và command/result envelopes; một canvas prototype dùng nét synthetic có local tentative/accepted/rejected state. So sánh các candidate editor/runtime trong ADR OD15 bằng thao tác input/render, own-undo, turn context và interrupted-draft fixtures; chọn candidate thử nghiệm không tự freeze stack. Teacher/Admin UI wireframes/state fixtures không khóa web framework. Bàn giao manifest fixture/version, runner instructions, operation examples và benchmark plan/raw evidence nếu benchmark được duyệt.
- **Prerequisites / gate:** không phụ thuộc live service hoặc task BE/INT; đọc B19–B23 và reuse audit. Benchmark on-device/package additions theo feature approval; OD08/OD15 trước production editor. H-CANVAS-SYNC là handoff sẽ consume, không prerequisite chạy fixture.
- **SRS:** UC-013/015/016; FR014–021, FR060/063/066; NFR01/05/06/10; UI IDs là cross-cutting, primary ownership ở các card sau; P-NFR-01/14, GATE-02.
- **Nghiệm thu dương:** Given fixture contract hợp lệ và backend không chạy, When mở runner, join state và vẽ synthetic stroke, Then UI hoạt động độc lập, cho thấy đúng tentative/accepted states và xuất manifest không cần secret/provider.
- **Nghiệm thu âm:** Given fixture event version unsupported hoặc stroke bị reject, When runner nhận outcome, Then hiện typed error/recovery draft, không đổi thành saved và không sửa nét accepted của peer.
- **Evidence / DoD riêng:** runner execution log, screenshot các state synthetic, input/render trace được gắn device manifest nếu đã đo, comparison/decision note; số đo chưa có ghi chưa đo. P2/P4 đọc được contract fixtures và chạy lại được cùng kịch bản.

## FE-02 — Child join, admission, Lobby và chọn lượt

- **Chủ trì / review:** P1; P2 review admission/grant/turn, P4 review integration seams.
- **Phạm vi / bàn giao:** C01/C02, QR scan + nhập mã fallback, pending admission, hiển thị nhóm/alias chỉ sau authorization; chọn active contributor theo lượt trên thiết bị chung; không tạo child login account. UI và adapter không coi QR/code là quyền đọc roster/canvas. Gate đổi lượt cuối cùng được nối với canvas trong FE-04.
- **Prerequisites / gate:** FE-01; H-IDENTITY và H-SESSION-ADMISSION; camera permission chỉ cho QR scan, không xin camera để chụp evidence lớp mặc định.
- **SRS:** FR002/003/005/066; UC-007/008; C01/C02; CMD-13–18/27; FIX-UX-01/02.
- **Nghiệm thu dương:** Given mã hợp lệ và Teacher đã admit device/profile, When trẻ chọn contributor trong tập được bind, Then hiện đúng group/turn policy; rejoin/retry không tạo participant trùng.
- **Nghiệm thu âm:** Given camera permission bị từ chối hoặc mã expired/chưa admit, When scan/join hay mở canvas, Then nhập mã còn dùng được, chưa có quyền thì không hiện roster/artwork và UI giữ safe pending/error state.
- **Evidence / DoD riêng:** fixture screen states và test kết nối admitted/pending/revoked; sanitize QR/token trước lưu evidence; adapter mapping admission/device grant/turn được P2 review.

## FE-03 — Teacher lớp, tạo phiên, Lobby và preset

- **Chủ trì / review:** P1; P2 review classroom/session, P3 review preset semantics; P4 nối acceptance.
- **Phạm vi / bàn giao:** T01/T02/T03/T04/T14: lớp được assignment, profiles/enrollment/consent summary, builder topic/tuổi/tools/canvas/groups, Lobby admit/reject/device binding, explicit Start, preset version/overrides. Consent evidence thao tác sâu ở FE-15, không tự suy consent từ enrollment. Manual grouping là core; auto-grouping UI giữ extension backlog/feature gate OD18.
- **Prerequisites / gate:** FE-01; H-IDENTITY, H-CLASS-CONSENT, H-SESSION-ADMISSION, H-CONTENT-PRESET. Desktop web framework và auth adapter cần ADR; feature branch fixture có thể chạy riêng. OD07/11/14/18 áp dụng cho controls còn chưa chốt.
- **SRS:** FR004/006–008/010/015/052/053/065; UC-002–006/007/033; T01/T02/T03/T04/T14; CMD-01–06/10/12–16/19/24/48/57/58; FIX-GOV-01.
- **Nghiệm thu dương:** Given roster đủ tuổi/consent trong một lớp ≤40 trẻ, When Teacher lưu config/preset pinned version, admit và explicit Start, Then hiển thị Active chỉ sau server acceptance và retry không start lần hai.
- **Nghiệm thu âm:** Given tuổi 35/156 tháng, thiếu consent, preset stale hoặc roster vượt40, When mở/start phiên, Then hiện từng safe validation finding, giữ trạng thái hợp lệ cũ; preset không bypass per-Sketch/video review.
- **Evidence / DoD riêng:** core setup click path, state/conflict fixture outcomes, field validation/role checks, manual grouping và planned auto-grouping extension label. Các 36–155 tháng/40 trẻ là policy/target, không load-test claim.

## FE-04 — Canvas, cộng tác, turn attribution và recovery

- **Chủ trì / review:** P1; P2 review operations/auth/recovery; P4 review reconnect handoff.
- **Phạm vi / bàn giao:** C03/C05/C10: editor cá nhân/nhóm, tool/region theo participant, active child rõ, scoped own-undo và process replay khi operation extension adopted; status on-device/sending/accepted/rejected; pending draft queue/checkpoint watermark, resync/dedupe/gap/permission conflicts. AI overlay chỉ renderer slot riêng, dataflow ở FE-06. Shapes/layers/transform/import/text là extension task con của card này sau contract/tool gates, không biến flag thành support giả.
- **Prerequisites / gate:** FE-01/FE-02; H-CANVAS-SYNC, H-SESSION-ADMISSION, H-SESSION-CONTROL. OD08/09/14/15 và local retention policy trước editor production/offline authoring; advanced tools giữ backlog đến có payload/permission/causality/replay contracts.
- **SRS:** FR014–021/060/063/066; UC-008/013–017; C03/C05/C10; CMD-27–31/61; AT-CS-001–007, FIX-UX-02/03, P-NFR-01/02/04/05.
- **Nghiệm thu dương:** Given hai authorized devices cùng group và A→B turn switch đã ack, When vẽ, duplicate delivery rồi reconnect, Then mỗi accepted stroke hiện một lần, nét mới gắn B, nét cũ vẫn A; accepted checkpoint/hash phục hồi đúng.
- **Nghiệm thu âm:** Given teacher lock/revoke/group move sau local draft, When reconnect/replay hoặc own-undo cố tác động nét peer, Then adapter nhận reject, hiện draft/disposition cần hỗ trợ, không replay trái quyền hoặc báo saved.
- **Evidence / DoD riêng:** synthetic two-device operation set/hash, reconnect/turn/undo outcomes, save-state screenshots và approved-device input/render traces khi đã chạy. Chưa có benchmark thì không báo đạt 40 children/touch responsiveness.

## FE-05 — Teacher live dashboard và group workspace

- **Chủ trì / review:** P1; P2 review state machine, region/group operations; P4 review combined view.
- **Phạm vi / bàn giao:** T05/T06, group progress độc lập, help queue, admitted device/turn status, authorized thumbnails, pause/resume/advance/draft/end, move member/lock/restore/contribution correction. Controller command được confirm bằng current server version; restore/correction giữ provenance. Consume H-SESSION-CONTROL từ BE1-11 cho clock/elapsed, pause/resume, policy version và warning/Teacher override events; hiển thị cảnh báo theo config đã adopt. Session elapsed không được gắn nhãn thời gian từng trẻ thực sự nhìn màn hình.
- **Prerequisites / gate:** FE-03/FE-04; H-SESSION-CONTROL, H-CANVAS-SYNC. OD07/11/14 trước rewind/hard timer/co-teacher/teacher-offline controls; không thêm các quyền này bằng UI.
- **SRS:** FR008–013/016–018/051/054/060/063/066; UC-009–012/014–016/032; NFR12; T05/T06; CMD-19–31/61/66; AT-CS-005/006/007/014, P-NFR-16/17.
- **Nghiệm thu dương:** Given group A ready còn B đang vẽ, When Teacher pause rồi resume bằng current revision, Then cả lớp giữ stage đến explicit advance, pending/accepted control rõ; progress A/B vẫn độc lập. Given adopted warning config, When backend phát warning/elapsed rồi Teacher override có receipt, Then UI hiển thị đúng policy version, clock/pause state và override outcome; không suy individual screen exposure từ session clock.
- **Nghiệm thu âm:** Given session revision stale hoặc child đã chuyển group, When controller/membership command conflict, Then UI reload safe context, không optimistic success/mất history, binding cũ không được vẽ tiếp. Given threshold/hard-stop OD11 chưa adopt hoặc warning version stale, When UI nhận clock/warning, Then không hardcode phút, tự end hay phạt trẻ; stale status được reload/đánh dấu, không áp policy cũ ngầm.
- **Evidence / DoD riêng:** control conflict/independent-group test outputs, visible pending/error/health states và review confirmation UX cho restore/end; fake-clock pause/resume/warning/override traces gắn effective policy version và labels phân biệt session elapsed với individual exposure; P2 đối chiếu state-machine outcomes.

## FE-06 — AI request, Teacher review queue và Child agency

- **Chủ trì / review:** P1; P3 review understanding/Sketch/moderation, P2 review source/scope; P4 review end-to-end seam.
- **Phạm vi / bàn giao:** C04/T07: Vision meaning correction, request/debounce/rate feedback, source snapshot/hash/support level, per-item approve/reject/regenerate, Child view/hide/decline, overlay tách strokes; queue/status tuổi request. Không preview/download raw pending proposal cho Child.
- **Prerequisites / gate:** FE-04/FE-05; H-AI-REVIEW, H-CANVAS-SYNC. OD16 model/output và applicable consent/limits trước provider execution; fixture queue trước không cần GPU.
- **SRS:** FR019/022–030/051/054/061; UC-017–021/032; C04/T07; CMD-32–36/44; FIX-UX-04, AT-CS-008/009, P-NFR-08/09/16.
- **Nghiệm thu dương:** Given proposal đúng context/version đã Teacher approve, When Child mở rồi hide/decline, Then chỉ overlay thay visibility/agency state, original strokes không đổi và proposal đó không bị automation bật lại.
- **Nghiệm thu âm:** Given unsafe/pending/stale proposal hoặc consent revoke giữa job, When Child mở trợ giúp/Teacher approve bản cũ, Then không deliver artifact, queue giữ typed outcome và không có preset approve-all bypass.
- **Evidence / DoD riêng:** source/review/version/visibility fixtures, delayed/duplicate completion probes, safe queue screenshots; xác minh không model prompt/credentials xuất hiện trong mobile/UI logs.

## FE-07 — Gallery và trình bày tác phẩm

- **Chủ trì / review:** P1; P2 review snapshot/gallery scope, P3 review derivative/provenance; P4 review display.
- **Phạm vi / bàn giao:** C06/T08, preview immutable artwork, original vs AI overlay, Teacher select/order/annotate/publish/present/withdraw; declared group contributions hiển thị khi evidence đủ. Không public social/share link mặc định, không tự thêm recording mic/camera.
- **Prerequisites / gate:** FE-04/FE-05; H-GALLERY. OD09/16 trước audio/text explanation collection; versioned media authorization.
- **SRS:** FR019/021/031–033; UC-017/022; C06/T08; CMD-37/65; FIX-PRIV-03, FIX-UX-07, P-NFR-11.
- **Nghiệm thu dương:** Given snapshots cùng phiên đã được phép chia sẻ, When Teacher chọn/sắp xếp/annotate rồi present, Then gallery đúng thứ tự, annotation riêng và source hashes không đổi.
- **Nghiệm thu âm:** Given revoke/cross-class snapshot hoặc group artwork chưa có individual attribution, When preview/publish, Then media unauthorized không mở; UI không gán tranh nhóm cho một trẻ hoặc public share.
- **Evidence / DoD riêng:** empty/gallery/display/source split screenshots, authorize/revoke test outcomes và snapshot checksum provenance.

## FE-08 — Knowledge/video review, wait và failure disposition

- **Chủ trì / review:** P1; P3 review jobs/script/artifact/approval, P2 review session stages; P4 review playback chain.
- **Phạm vi / bàn giao:** C07/T09, Teacher knowledge/script source editing, library select/generate, attempts/status, exact video version/hash review/playback. Generating phải chờ; exhausted failure cho Teacher explicit retry/skip/end; playback error khác render failure. Caption/TTS/audio language còn gate, không nhập thời lượng cũ.
- **Prerequisites / gate:** FE-05/FE-07; H-KNOWLEDGE-VIDEO, H-SESSION-CONTROL. OD16 retry/model/encoding/library profile trước real generation/playback acceptance; fixture states không claim generated video.
- **SRS:** FR034–040; UC-023–026; C07/T09; CMD-38–44; FIX-UX-05, AT-CS-010/011, P-NFR-10.
- **Nghiệm thu dương:** Given exact artifact Teacher đã approve, When Teacher phát cho audience được grant, Then Child xem đúng approved hash; exhausted-failure fixture cho Teacher chọn disposition và lưu outcome đó.
- **Nghiệm thu âm:** Given đang Generating hoặc script/artifact đã đổi sau review, When Child/automation cố skip/play, Then không tự skip/fallback/play bản stale; Teacher UI yêu cầu review mới, không gọi skipped là successfully generated.
- **Evidence / DoD riêng:** generating/review/failure/playback state matrix, request retry/idempotency results và approved hash; actual codec/device playback evidence tách stub generation evidence.

## FE-09 — Activity assignment và off-screen handoff

- **Chủ trì / review:** P1; P3 review catalog/activity versions, P2 review class/group assignment; P4 review stage handoff.
- **Phạm vi / bàn giao:** C08/T10, discovery/library recommendation, nguyên bản/Teacher edits, material/safety/preparation, assignment theo class/group, off-screen instructions/help/ready signals; Child done signal tách Teacher observation. Hoạt động reviewed assets được dùng theo visual/provenance rules.
- **Prerequisites / gate:** FE-05/FE-08; H-ACTIVITY, H-SESSION-CONTROL. Adopt catalog discovery semantics/pedagogical/material policy trước production selection; OD10/11 phần liên quan.
- **SRS:** FR041–044; UC-027/028; C08/T10; CMD-45/48/59; FIX-UX-06, P-NFR-17.
- **Nghiệm thu dương:** Given activity version được phép và Teacher xác nhận chuẩn bị, When assign cho một group và start off-screen, Then chỉ đúng nhóm nhận chỉ dẫn, Teacher edit có lineage và help/xong là signal riêng.
- **Nghiệm thu âm:** Given thiếu vật liệu/safety hoặc Child tự mark done, When start/advance, Then UI dẫn về Teacher chuẩn bị/chọn lại; không tự xác nhận assessment hoặc chuyển cả lớp.
- **Evidence / DoD riêng:** assignment/preparation fixtures, original/edit diff, Child instructions/help screenshots; không thu camera evidence mặc định.

## FE-10 — Reflection, observations và assessment

- **Chủ trì / review:** P1; P2 review evidence/assessment, P3 review AI suggestion separation; P4 review learning-result assembly.
- **Phạm vi / bàn giao:** C09/T11, reflection tương tác theo tuổi, save draft/submit duplicate-safe, Teacher evidence/NOT_OBSERVED/descriptive observation, AI draft riêng, confirm/correction version. Không peer ranking/psychological inference; không thu mic/text chưa duyệt.
- **Prerequisites / gate:** FE-09; H-ASSESSMENT-PORTFOLIO. OD10 rubric/OD09 input and relevant purpose policy trước final form; reviewed synthetic rubric fixtures được label candidate.
- **SRS:** FR044/045/049/050; UC-028/029; C09/T11; CMD-46/62; FIX-UX-06, GATE-05.
- **Nghiệm thu dương:** Given evidence đủ và rubric version adopted, When Teacher lưu/chốt observation rồi correction, Then child reflection/Teacher result/AI draft tách loại, correction append revision và retry không duplicate.
- **Nghiệm thu âm:** Given chưa quan sát hoặc thiếu individual attribution, When form confirm, Then lưu NOT_OBSERVED/group context phù hợp; AI suggestion không tự thành Teacher-confirmed assessment và partial save không hiện completed.
- **Evidence / DoD riêng:** evidence association/draft/confirmation/correction fixtures, age UI states và consent/output minimization checks.

## FE-11 — Portfolio, learning reports và scoped exports

- **Chủ trì / review:** P1; P2 review portfolio/report/export authorization, P4 review report assembly.
- **Phạm vi / bàn giao:** T12/A07, timeline/evidence/contribution quality, own progress/descriptive reports, export request/status/download có permission revalidation; separate school aggregate operational reports với learning report purposes. Không leaderboard.
- **Prerequisites / gate:** FE-07/FE-10; H-ASSESSMENT-PORTFOLIO, H-DATA-REQUEST. Portfolio/profile/audit TTL và aggregate suppression policy chưa chốt không tự lấy TTL90 cho mọi thứ.
- **SRS:** FR011/046–050/057–059; UC-011/030/031/038; T12/A07; CMD-23/47/49/50/64; FIX-PRIV-03, P-NFR-12.
- **Nghiệm thu dương:** Given Teacher đang có assignment/purpose và own-progress entries hợp lệ, When filter report/export, Then hiện đúng evidence provenance và download chỉ sau artifact authorized/current status.
- **Nghiệm thu âm:** Given assignment revoke giữa export hoặc group artwork chứa peer data, When xem/download, Then không trả peer raw media trái phép/không dùng role Admin như raw-read grant; partial export không báo complete.
- **Evidence / DoD riêng:** report definitions/state screenshots, privilege/revoke/peer-data fixtures và export result/hash liên kết request.

## FE-12 — Teacher authoring và Admin content governance

- **Chủ trì / review:** P1; P3 review content/publish/recall/version, P4 review usage impact view.
- **Phạm vi / bàn giao:** T13/A04, draft author/source/topic/age/material/safety, request review/change/publish/recall, version history và affected usage summaries; Teacher author không tự có global publish grant. Preset UI đã ở FE-03/T14.
- **Prerequisites / gate:** FE-01; H-CONTENT-PRESET. Content reviewer/recall active-playback policy refinement và reviewed assets/visual approval trước apply.
- **SRS:** FR040–042/052/056/062; UC-027/033/035; T13/A04; CMD-48; FIX-GOV-01, GATE-05.
- **Nghiệm thu dương:** Given draft đủ source/audience/review và publisher scope, When publish version mới, Then active content pin version/hash và published version cũ không bị sửa trực tiếp.
- **Nghiệm thu âm:** Given Teacher chỉ là author hoặc source/review thiếu, When publish/recall trái grant, Then UI báo denied/findings, không phát nội dung chưa duyệt; library edit không tự đổi active session.
- **Evidence / DoD riêng:** draft/review/recall state transitions, role/policy negative probes và lineage display examples.

## FE-13 — Admin overview, adult accounts và school/class configuration

- **Chủ trì / review:** P1; P2 review identity/assignment/class scope, P4 review bootstrap integration.
- **Phạm vi / bàn giao:** A01/A02/A03, operational metadata overview có freshness, adult account/status/roles/grants, class/archive/Teacher assignment. Chuẩn bị organization keys cho mở rộng nhưng pilot một trường; không tạo child accounts và không thêm production multi-tenant UX chưa yêu cầu.
- **Prerequisites / gate:** FE-01; H-IDENTITY, H-CLASS-CONSENT, H-ADMIN-POLICY. Bootstrap/provisioning/recovery/dual approval cần policy trước thao tác quyền production.
- **SRS:** FR001/004/005/055/058; UC-001/002/034; A01/A02/A03; CMD-01/07/18/51–53/56; P-NFR-06/07.
- **Nghiệm thu dương:** Given authorized Admin grant đúng trường, When archive class hoặc revoke Teacher assignment, Then metadata/version được cập nhật, history giữ nguyên và access revocation hiển thị rõ.
- **Nghiệm thu âm:** Given caller tự đề nghị nâng scope/role hoặc Admin không có raw-art grant, When sửa quyền/xem media, Then denied, không lộ child artwork/guardian evidence và không sửa identity claims từ UI.
- **Evidence / DoD riêng:** loading/empty/stale/revoked screens, assignment/account fixtures và scoped history; không seed account/credentials thật.

## FE-14 — Admin AI policy, monitoring/incident và audit

- **Chủ trì / review:** P1; P3 review AI/job/policy, P2 review durable audit/access, P4 review telemetry contract.
- **Phạm vi / bàn giao:** A05/A06/A09, candidate policy draft/activate/revoke, job aggregate status/queue controls theo grant, redacted incidents/metrics/audit filters/history. Không sửa DB row/job trực tiếp hoặc hiển thị credentials/provider internals cho Child; metrics timestamp phân biệt stale/zero.
- **Prerequisites / gate:** FE-01; H-OPERATIONS, H-ADMIN-POLICY, H-AI-REVIEW. AI policy/model activation cần OD16 evaluation/ADR; audit retention và exceptional access vẫn gated.
- **SRS:** FR029/030/054/056–059/064; UC-036/037/038; A05/A06/A09; CMD-11/44/48/50/59/60/63; FIX-NFR-02/03, P-NFR-13/16.
- **Nghiệm thu dương:** Given redacted operational data và scoped operator, When xem lag/status/incident và gửi permitted queue command, Then có freshness/correlation và outcome/history qua versioned application command.
- **Nghiệm thu âm:** Given log chứa synthetic sensitive sentinel hoặc policy muốn bypass Teacher review, When render/activate, Then không hiện raw child/token/prompt/QR; config bị reject, audit không cho UI sửa/xóa event cũ.
- **Evidence / DoD riêng:** redaction sentinel probes, incident/status fixtures và stale/retry command outcomes; không lấy screenshot chứa token/signed URL.

## FE-15 — Admin consent/data requests và lifecycle policy

- **Chủ trì / review:** P1; P2 review purposes/data lifecycle/revocation, P3 review provider/artifact copy states; P4 review shared-work purge results.
- **Phạm vi / bàn giao:** A08/A10, evidence metadata theo quyền, consent verify/revoke/correct, export/delete authority/scope review, per-store pending/exception/results; policy draft/diff/validate/activate/version với confirmed session/artwork TTL90 và data classes khác riêng. Evidence bytes cần grant riêng; không nút purge bỏ authority/shared-work/backups review.
- **Prerequisites / gate:** FE-01; H-CLASS-CONSENT, H-DATA-REQUEST, H-ADMIN-POLICY. OD04/05/17/legal authority/verification/other data TTL cần policy adoption; UI không declare legal compliance.
- **SRS:** FR006/055–059/064; UC-003/034/038; A08/A10; CMD-08/09/49/50/54/55/63; FIX-PRIV-01–05, P-NFR-07/12.
- **Nghiệm thu dương:** Given school evidence đã được authorized verifier kiểm tra đúng purpose, When ghi/thu hồi và theo dõi data request, Then status/scope/version thể hiện riêng với enrollment, policy raw-session TTL90 tính từ session end và per-copy results được hiển thị.
- **Nghiệm thu âm:** Given evidence chưa xác minh, quyền guardian request chưa kiểm hoặc purge còn external/backup exception, When bật purpose/complete request/activate TTL chung, Then không tự grant consent/không báo completed, portfolio/profile/audit không thừa hưởng90 ngày vô điều kiện.
- **Evidence / DoD riêng:** consent purpose matrix, data-request incomplete/exception state screenshots, policy diff/validation results và role/evidence isolation probes; chỉ dùng synthetic evidence metadata.

## UI primary ownership — đủ 34 responsibilities

Mỗi UI-ID dưới đây có một task primary. Một task khác có thể hiển thị link/widget tới màn hình đó nhưng không có ownership thứ hai. C03/C05/C10 là workspace state liên quan, không bắt buộc ba routes; tương tự Teacher/Admin workspace có thể gom theo layout đã review.

| UI-ID | Primary task | Trách nhiệm |
|---|---|---|
| C01 | FE-02 | Welcome/QR/code join |
| C02 | FE-02 | Lobby/active child |
| C03 | FE-04 | Drawing/tools/save state |
| C04 | FE-06 | AI assistance/agency |
| C05 | FE-04 | Collaboration/turn/regions |
| C06 | FE-07 | Artwork preview |
| C07 | FE-08 | Knowledge/wait/playback |
| C08 | FE-09 | Off-screen instructions/help |
| C09 | FE-10 | Reflection |
| C10 | FE-04 | Recovery/resync |
| T01 | FE-03 | Teacher home |
| T02 | FE-03 | Class/student management |
| T03 | FE-03 | Session builder |
| T04 | FE-03 | Teacher Lobby/admission |
| T05 | FE-05 | Live dashboard |
| T06 | FE-05 | Group workspace |
| T07 | FE-06 | Per-item AI review |
| T08 | FE-07 | Gallery/presentation |
| T09 | FE-08 | Knowledge/video review |
| T10 | FE-09 | Activity assignment |
| T11 | FE-10 | Reflection/assessment |
| T12 | FE-11 | Portfolio/report |
| T13 | FE-12 | Content authoring |
| T14 | FE-03 | Presets/automation |
| A01 | FE-13 | Admin overview |
| A02 | FE-13 | Adult users/roles |
| A03 | FE-13 | School/class organization |
| A04 | FE-12 | Content governance |
| A05 | FE-14 | AI governance |
| A06 | FE-14 | Monitoring/incidents |
| A07 | FE-11 | Scoped reports |
| A08 | FE-15 | Consent/data requests |
| A09 | FE-14 | Audit |
| A10 | FE-15 | Lifecycle/system configuration |

## UI backlog extensions và release gates còn mở

- FE-03/FE-05: stage rewind FR013, screen-time values, co-teacher/teacher-offline policy và automatic grouping FR065 cần OD07/11/14/18; giữ trong backlog nhưng không hardcode hành vi.
- FE-04: advanced age-appropriate UX FR021 có obligation review/process; exact layer/object/eraser/redo payloads chưa đầy đủ, cần OD08/15 adopted extension. Import/sticker/text FR020 là TBD OD09, chưa xin permission/collect input.
- FE-06/FE-08: AI/model/output/retry budget/voice/duration/codec chất lượng cần OD16 và measured evidence; library preview/stub transitions không là model success.
- FE-10/FE-11/FE-15: age rubric/longitudinal retention/legal verification/aggregate suppression cần OD10/05/17. Confirmed 90 ngày session/artwork không giữ raw session source qua portfolio vô thời hạn.
- Mỗi FE task bàn giao fixture và component evidence cho P4; acceptance E2E là giao điểm FE + BE + INT, không coi việc build UI hoặc hide button là authorization đã kiểm chứng.
