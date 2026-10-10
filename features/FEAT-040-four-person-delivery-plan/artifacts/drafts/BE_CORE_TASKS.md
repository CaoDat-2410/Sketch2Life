# P2 — Backend lõi, lớp học, cộng tác và dữ liệu

P2 là người BE thứ nhất, chịu trách nhiệm domain/application/contracts và adapters thuộc lớp học, authorization, session, canvas, gallery, assessment/portfolio và data lifecycle. P2 giữ FastAPI; DB, queue, object storage, canvas sync mechanism và thuật toán chi tiết chỉ được adopt qua ADR/feature approval tương ứng. Các task dưới đây là backlog triển khai đề xuất, không phải bằng chứng tính năng đã hoạt động.

Không có ngày, deadline, giờ hay thời lượng sprint trong phân công này. Bắt đầu bằng **BE1-01** với fixtures độc lập; sau đó kéo task theo dependency và gate quyết định. P2 không đợi service thật của P3 để viết domain/contract tests. Khi ghép runtime, P4 nối composition và kiểm thử luồng xuyên module; P2 vẫn tự chịu trách nhiệm module, durable adapters, migrations và kiểm thử của mình.

Baseline đã chốt: một trường pilot, một lớp chạy đồng thời tối đa 40 trẻ; độ tuổi 36–155 completed months inclusive; hồ sơ do Teacher quản lý, QR/mã phiên không phải tài khoản trẻ; school-mediated consent; mỗi AI Sketch phải Teacher duyệt trước cho pilot; tablet chung chọn contributor theo lượt; session/artwork giữ mặc định 90 ngày sau khi end. Đây là yêu cầu, chưa phải năng lực tải, độ tin cậy hay purge đã được chứng minh.

## Ranh giới và bàn giao

- P2 sở hữu DATA-01–DATA-20, DATA-30, DATA-31, DATA-32, DATA-34, DATA-35. P3 sở hữu DATA-21–DATA-29 và DATA-33; migrations/repositories của domain nào do người sở hữu domain đó viết và tự kiểm thử. P4 ghép migration/runtime dependency order đã review.
- P2 sở hữu generic transaction/unit-of-work, idempotency receipts, durable outbox/operation/checkpoint/asset repository ports và core storage adapters. P3 sở hữu AI/content/video job state, dispatch/completion application rules và provider adapters; P2 cung cấp persistence/authorization/asset contracts cần dùng, không được sửa thẳng job DB của P3.
- Bàn giao H-IDENTITY, H-CLASS-CONSENT, H-SESSION-ADMISSION, H-CANVAS-SYNC, H-SESSION-CONTROL, H-GALLERY, H-ASSESSMENT-PORTFOLIO, H-DATA-REQUEST; phần core của H-ADMIN-POLICY/H-OPERATIONS. Consumer là P1/P3/P4 tùy luồng. H-AI-REVIEW, H-KNOWLEDGE-VIDEO, H-ACTIVITY, H-CONTENT-PRESET do P3 cung cấp versioned interface cho P2.
- CMD-59 là gateway allowlist read models do P2 sở hữu: projection AI/content/job/catalog/preset do P3 cung cấp qua versioned query port. CMD-60 do P2 sở hữu admission/authorization và mediated delivery: P3 cung cấp exact artifact eligibility/review/version port. Không để cả hai người cùng viết route hoặc join trực tiếp database xuyên module.
- Code hiện tại có FastAPI/Pydantic/ports, nhưng source audit cho thấy in-memory demo và auth verifier protocol, chưa chứng minh durable DB/auth production. Có thể tái sử dụng patterns; không gọi scaffolding là phần đã hoàn thành. Guard tuổi cũ phải thay qua feature mới được duyệt, không giữ <9 trong target mới.

Quy ước dependencies: ID BE1 là dependency nội bộ; H-* là contract bàn giao bên ngoài. Dependency contract có thể được đáp ứng bằng fixture version đã review để chạy độc lập; kết luận runtime end-to-end phải có adapter thật và allocation/approval tích hợp. Mỗi task triển khai mở/cập nhật feature riêng, có plan/approval/evidence; evidence của FEAT-040 chỉ xác nhận chất lượng tài liệu phân công.

## BE1-01 — Đặc tả domain và bộ fixture backend lõi độc lập

- **Đầu ra:** domain model/ports và schema fixtures cho authorization, lớp/hồ sơ/consent, session/group/admission, turn/canvas, gallery/portfolio/data request; closed command envelopes, errors/CAS/idempotency conventions và standalone runner. Manifest ghi exact contract version và owner; initial fixtures dùng synthetic data, in-memory test adapters.
- **Phụ thuộc/gate:** không phụ thuộc live service, không DB/provider thật. Đọc SRS v3.1 B19–B26; chốt những chi tiết PROPOSED cần áp dụng trong feature approval. Không tự khóa cả stack hoặc biến TBD thành default.
- **Truy vết:** M01–M05/M07/M10/M12–M14; FR001–018, FR021, FR031–033, FR045–050, FR055, FR057–060, FR063–066; UC-001–016, UC-022, UC-029–034, UC-037–038; DATA ownership ở trên, API-CS-01–03.
- **Nghiệm thu:** positive: runner độc lập tải fixture request/state/result của các handoff core và kiểm tra pass bằng domain/application, không cần service khác. Negative: unknown fields/invalid scope, forged role, age 35/156, stale revision và duplicate key khác payload trả đúng typed failures; không reset state để test pass.
- **Evidence/reviewer:** schema/fixture manifest, runner command+output, contract review và source-vs-target gaps trong feature evidence; P4 review contract, P3 review AI/content boundary, P1 review child-facing projections.

## BE1-02 — Durable core adapters, migrations và transaction/outbox

- **Đầu ra:** approved storage adapter cho core repositories, unit-of-work/CAS/idempotency, durable canvas operation/checkpoint metadata, asset metadata/lineage, audit append và outbox; migrations core có forward/restore strategy, synthetic seed fixture không credentials. Tách durable authoritative truth khỏi optional cache/presence/pub-sub. Không triển khai AI model/job rules trong task này.
- **Phụ thuộc/gate:** BE1-01; ADR chọn DB/object store/runtime mechanism trước adapter thật. Backend-only object access; Firebase Authentication-only, cấm Firebase Storage/Firestore/Realtime Database. Credential đi qua ignored runtime secrets.
- **Truy vết:** FR011, FR017, FR047, FR059–060, FR064; B19.3/B19.8/B22.3; DATA-07, DATA-17–DATA-20, DATA-31, DATA-34–DATA-35; P-NFR-04/11/13.
- **Nghiệm thu:** positive: restart process sau durable commit giữ accepted operation/receipt/audit và outbox replay không nhân đôi side effect. Negative: transaction thất bại không phát durable ack hoặc Completed; duplicate delivery không tạo record mới, logging sentinel không lộ child data/token.
- **Evidence/reviewer:** migration matrix, actual adapter integration results, crash-point receipts/checksums và redacted logs; P3 review generic ports/outbox use, P4 review composition/migration contract. Chỉ simulated/in-memory pass chưa hoàn thành adapter thật.

## BE1-03 — Adult authentication, assignments và device-grant lifecycle

- **Đầu ra:** backend adult-token verifier adapter, local scoped role/capability resolver, account commands, Teacher assignment/revoke và admitted-device grant refresh/revoke. Không dùng X-Actor-Ref/demo actor làm production authorization; Child không có login riêng. Có fixture verifier để test độc lập.
- **Phụ thuộc/gate:** BE1-01; adapter persisted cần BE1-02. Policy account provisioning/last Admin/device proof/key store phải được adopt, không hardcode user/credential. H-IDENTITY cho FE và P3.
- **Truy vết:** FR001, FR005, FR055, FR058–059; UC-001/034; DATA-01, DATA-04, DATA-12, DATA-35; **CMD-07, CMD-17, CMD-18, CMD-51, CMD-52, CMD-53**.
- **Nghiệm thu:** positive: Teacher assigned đúng lớp có context tối thiểu; grant refresh còn hợp lệ tạo replacement và revoke làm future reads/writes/subscriptions bị deny. Negative: giả role/header, expired token, self-elevation, revoke assignment rồi refresh, Admin chỉ monitoring xin raw child data đều bị chặn; lịch sử contribution không bị xóa.
- **Evidence/reviewer:** permission matrix, verifier/expiry/revoke race tests, redacted request/result và audit; P4 review auth wiring, P1 review login/revoke UX, P3 review worker/completion authorization.

## BE1-04 — Class, managed child profiles và enrollment

- **Đầu ra:** class create/list/edit/archive; roster/profile create/update theo assignment, atomic profile+enrollment và enrollment end; versioned age computation context, minimized roster projections. Android nhận label/tool policy cần thiết, không mặc định nhận DOB/evidence riêng tư.
- **Phụ thuộc/gate:** BE1-01/03; persisted cần BE1-02. Age endpoints đã chốt 36–155; chốt age-date calculation/mixed-age details trước eligibility implementation liên quan. Một trường có organization scope server-derived, chuẩn bị mở rộng không claim multi-school ready.
- **Truy vết:** FR004, FR012, FR055, FR059; UC-002/012/034; DATA-02–DATA-04; **CMD-01, CMD-02, CMD-03, CMD-04, CMD-05, CMD-06, CMD-56**.
- **Nghiệm thu:** positive: tuổi 36/155 eligible đúng ngày tham chiếu đã adopt, edit tăng age-context revision và enrollment end chặn participation mới nhưng giữ lịch sử. Negative: tuổi 35/156 hoặc unknown age không join protected session; age sources conflict, stale profile patch, class khác scope và duplicate active enrollment bị reject; không suy tuổi từ tranh/AI.
- **Evidence/reviewer:** age boundary/date fixtures, CRUD/assignment/minimization tests, enrollment invalidation history; P1 review roster DTO/labels, P4 review scope migration, P3 review age-context pinning.

## BE1-05 — School-mediated consent và purpose enforcement

- **Đầu ra:** consent record/evidence reference, verification riêng, amendment/revoke theo purpose; eligibility query port cho drawing/AI/sharing/portfolio và invalidation event. Consent authority workflow không đồng nhất với Teacher role/enrollment; evidence không gửi provider tùy tiện.
- **Phụ thuộc/gate:** BE1-03/04; BE1-02 cho persistence. Purpose taxonomy, authority verification và permissions cần privacy decision; school collection đã chốt, không hỏi lại hoặc tạo Parent portal. H-CLASS-CONSENT có verified/non-effective/revoked fixtures.
- **Truy vết:** FR006, FR029, FR059, FR064; UC-003/038; DATA-05, DATA-35; **CMD-08, CMD-09, CMD-54, CMD-55**; FIX-PRIV-01/02.
- **Nghiệm thu:** positive: recorder tạo pending, delegated verifier xác minh evidence/purpose đúng thẩm quyền rồi effective; revoke một purpose chặn work/access tương ứng và giữ history. Negative: create với verified=true/self-approval, role/enrollment-only, expired consent, AI completion sau revoke không phát artifact; purpose mới qua amendment chưa verified không effective.
- **Evidence/reviewer:** record→verify→amend→revoke transition tests, purpose denial và revoke race receipts; P3 review AI completion contract, P4 review privacy scope, P1 review safe consent status display.

## BE1-06 — Session configuration, preset snapshot, lobby và explicit Start

- **Đầu ra:** create draft, validate/edit effective config, pinned preset/policy versions, open lobby và Teacher Start. Validate topic/roster/age/tools/groups/consent theo approved policy; giới hạn pilot một lớp tối đa 40 trẻ, phân biệt count trẻ và count thiết bị.
- **Phụ thuộc/gate:** BE1-03/04/05; BE1-02 persistence. H-CONTENT-PRESET cho preset/policy resolve từ P3, fixture thay service thật ở standalone. Chốt tools/mixed-age/phase policy liên quan; preset không preapprove Sketch/video.
- **Truy vết:** FR007, FR010, FR015, FR052–053; UC-004/033; DATA-06, DATA-07, tham chiếu DATA-33 của P3; **CMD-10, CMD-12, CMD-13, CMD-19**.
- **Nghiệm thu:** positive: draft resolve preset thành immutable effective config; Teacher đúng scope explicit Start khi ready, preset update sau đó không sửa active session. Negative: 41 trẻ, lớp đồng thời thứ hai trong pilot policy, unresolved tool/mixed-age hoặc thiếu consent, stale config/start đều blocked; một group ready không Start/advance lớp tự động.
- **Evidence/reviewer:** ready/not-ready fixture matrix, pinned refs/CAS/idempotency results và capacity policy checks; P1 review T03/T04, P3 review preset eligibility, P4 review session lifecycle handoff. Guard count không chứng minh load 40 đã đạt.

## BE1-07 — QR/mã phiên, pending device và Teacher admission

- **Đầu ra:** possession-bound pending join bootstrap, own pending status, Teacher review/admit/deny; admission transaction bind đúng participants/group/grant/context. QR short-lived locator không chứa identity roster, adult token hoặc durable device grant.
- **Phụ thuộc/gate:** BE1-03/04/05/06; device proof/bootstrap policy adopt qua ADR. H-SESSION-ADMISSION fixture chứa pending/admitted/denied/expired/scope-change.
- **Truy vết:** FR001–003, FR005–006; UC-007/008; DATA-09–DATA-13; **CMD-14, CMD-15, CMD-16**; CS-007/008, FIX-UX-01.
- **Nghiệm thu:** positive: join code hợp lệ chỉ tạo pending; Teacher chọn profiles được phép và admit rồi grant scope mới mở đúng canvas. Negative: pending query roster/canvas/artifact, expired/rate-limited code, stale admission hoặc thiếu consent bị deny; request không chứa child_id/role để tự bind quyền.
- **Evidence/reviewer:** bootstrap/admission/expiry/replay tests, scoped response specimens và audit; P1 review waiting/admission UX, P4 review proof/grant plumbing, P3 review admitted context for AI requests.

## BE1-08 — Manual groups, progress/help, move và leave

- **Đầu ra:** manual group creation, per-group progress/help updates, transactional participant move/leave; replace/revoke membership/turn grants đúng ảnh hưởng, giữ artwork/contribution lịch sử và quyền những trẻ còn dùng chung thiết bị. Participant leave khác enrollment end.
- **Phụ thuộc/gate:** BE1-06/07/03; future canvas interface H-CANVAS-SYNC fixture cho invalidation; tích hợp canvas thật sau BE1-09/10. Quy tắc move disposition và group limits được adopt trong feature.
- **Truy vết:** FR008–009, FR012, FR016, FR066; UC-005/009/012/014; DATA-08, DATA-12–DATA-14; **CMD-24, CMD-25, CMD-26, CMD-66**.
- **Nghiệm thu:** positive: move tăng membership/grant revisions, nét cũ giữ tác giả; leave một trẻ không revoke toàn tablet làm mất quyền peers; group ready chỉ đổi progress. Negative: source/target stale revision, foreign group/participant, Child advance class hoặc access canvas nhóm cũ sau move bị chặn.
- **Evidence/reviewer:** membership atomicity/race fixtures, before/after grant+contribution set và help/progress state; P1 review T06/C05, P4 review session/group invariants.

## BE1-09 — Turn attribution và authorized canvas operation log

- **Đầu ra:** canvas metadata, age/Teacher tool policy, active-turn binding, bounded operation validation, dedup/sequence/durable receipts, region locks và append-only attribution correction. Selected contributor không trở thành security principal; own undo/hide dùng compensating operations bảo toàn peer strokes. Các erase/redo/layer/import extensions chưa có closed payload không được enable chỉ bằng tool flag.
- **Phụ thuộc/gate:** BE1-01/02/03/05/08; H-CANVAS-SYNC thống nhất với P1; ADR canvas/sync và closed operation union/undo/region policy cần adopt. Không ép mọi nét phải If-Match document head; control aggregate/turn CAS và operation IDs/epochs riêng.
- **Truy vết:** FR003, FR014–016, FR018–021, FR028, FR066; UC-008/013/014/015/017; DATA-14–DATA-18, DATA-20; **CMD-27, CMD-29, CMD-30, CMD-61**; AT-CS-001–006.
- **Nghiệm thu:** positive: hai valid authors append không mất nét; identical operation retry trả cùng receipt/sequence, đổi lượt chỉ ảnh hưởng nét mới; correction append giữ original source. Negative: foreign contributor/region, old grant/turn/policy epoch, duplicate ID khác payload, points NaN/out-of-range, undo peer hoặc unsafe chunk bị reject mà không ack_saved; AI overlay không biến thành child stroke.
- **Evidence/reviewer:** operation boundary/duplicate/concurrency/turn-switch tests, accepted sequence/hash and immutable lineage, rejected batch receipt; P1 review canvas serialization/render integration, P4 review consistency, P3 review snapshot vs child-layer semantics.

## BE1-10 — Canvas sync, checkpoints, restore và reconnect recovery

- **Đầu ra:** authorized checkpoint+delta sync, durable checkpoint/snapshot references, controlled restore sang epoch mới giữ provenance, gap replay/dedup và realtime transport adapter nếu ADR chọn. Local unaccepted drafts khác accepted state; presence không thay participant truth.
- **Phụ thuộc/gate:** BE1-02/03/09; H-CANVAS-SYNC version chốt với P1. Offline duration/Teacher-offline và transport details còn gate; standalone dùng clock/network/crash fixtures, runtime phải có persisted adapter.
- **Truy vết:** FR017, FR021, FR060, FR063; UC-014/015/016; DATA-17–DATA-20; **CMD-28, CMD-31**; B19.8/9, API-CS-02; P-NFR-04/05/06.
- **Nghiệm thu:** positive: reconnect fetch checkpoint+delta khôi phục accepted set/hash, gap/delivery duplicate không vẽ thêm; restore tạo epoch mới và preserved lineage. Negative: old-epoch queued ops không auto merge, revoked reader/subscriber không lấy canvas/presence, history-window expiry yêu cầu snapshot; process crash không mất op đã durable ack và không nói pending local đã saved.
- **Evidence/reviewer:** disconnected/out-of-order/gap/restart logs, watermark+checksum before/after và scope-denial matrix; P1 review recovery statuses/transport, P4 review durable/realtime wiring. Đo latency/device profile riêng sau integration, không kết luận SLO từ fixture.

## BE1-11 — Teacher control, phase transitions và durable finish

- **Đầu ra:** pause/resume/advance/finish handlers với checkpoints, group dispositions, approval refs và truthful saving/recovery_required/completed/ended_early outcomes; manual override thắng stale automation. Kết thúc pin ended_at và retention anchor, không báo completed trước durable save.
- **Session clock application contract:** P2 giao monotonic elapsed-time clock port, durable accumulated intervals/checkpoints và pause/resume/stage accounting theo approved policy/version. Tách session elapsed, stage elapsed và screen-time accounting theo policy; session duration không tự là thời gian từng trẻ nhìn màn hình. UTC started_at/ended_at phục vụ timeline/retention, không lấy client wall clock làm nguồn authoritative cho elapsed. Monotonic clock trong một process kết hợp persisted accumulators khi restart; khoảng thời gian chưa biết do crash/offline phải có explicit uncertainty/recovery disposition theo policy, không reset về 0 hoặc bịa exposure. Emit versioned warning/threshold/Teacher override events và safe clock state qua H-SESSION-CONTROL, dùng projection CMD-11/CMD-59 và existing control routes, không thêm CMD. Proposed clock payload/extension DATA-07 phải adopt trong contract registry, không tự sửa SRS/schema trong task planning này. Consumer là FE-05 và INTG-04/INTG-11.
- **Phụ thuộc/gate:** BE1-06/08/10; H-AI-REVIEW/H-KNOWLEDGE-VIDEO/H-ACTIVITY/H-CONTENT-PRESET cung cấp eligibility/decision refs qua P3 fixtures, runtime sau modules P3 được nối. Return-stage/Teacher-offline/co-teacher details cần gate, không mở ngầm bằng UI back.
- **Clock policy gate:** NFR12 xác nhận screen time phù hợp tuổi và có off-screen; số phút theo band, thời gian pause có tính vào budget nào, visibility/exposure signals, warning cadence và hard-stop đều phải chốt OD11/adopted policy. Clock fixtures dùng named synthetic policies riêng, không hardcode 10 phút hoặc thời lượng video cũ; chưa chốt limit không mặc định vô hạn, tự fail trẻ hoặc auto kết thúc phiên.
- **Truy vết:** FR009–013, FR038–039, FR044, FR052, FR060, FR063; UC-009–011/025–026/028/033; DATA-07, DATA-08, DATA-19; **CMD-20, CMD-21, CMD-22, CMD-23**; AT-CS-005/011/014.
- **Truy vết clock:** NFR12/P-NFR-17, B23.6, OD11; UC-010/028/033; shared DATA-07 effective policy/state và API-CS-03 warning/control events; H-SESSION-CONTROL consumer FE-05, INTG-04, INTG-11.
- **Nghiệm thu:** positive: pause/resume giữ current stage/art, explicit advance cần group dispositions/review; finish retry idempotent tạo terminal durable outcome và anchor end+90 ngày. Negative: video đang generating không auto fallback/skip, unapproved media không advance/play, unfinished group không giả completed; checkpoint failure giữ recovery_required và stale automation không ghi đè Teacher decision.
- **Nghiệm thu clock:** positive: deterministic clock fixture qua draw→pause→resume→video→off-screen tính elapsed/budget đúng named policy, warning có exact policy/version và duplicate delivery không double-count; restart giữ durable elapsed/checkpoint và Teacher override traceable. Negative: chỉnh client UTC/ngày giờ, repeat pause/resume, stale policy/event hoặc process monotonic reset không giảm/tăng sai accumulator; unknown crash/offline exposure hiện unresolved/uncertain; threshold warning không auto stop/fail hoặc đổi stage khi OD11 chưa authorise hành vi đó. Video skip vẫn dẫn tới off-screen nếu phiên tiếp tục hoặc recorded early-end theo P-NFR-17.
- **Evidence/reviewer:** transition/failure/idempotency/automation race tests, terminal save receipts và phase timeline; P3 review media/activity handoffs, P1 review controls/save UX, P4 review cross-module orchestration. Failure disposition endpoint do P3 sở hữu; P2 chỉ consume authorized outcome.
- **Evidence/reviewer clock:** fake-clock transition table, accumulated interval/checkpoint receipts, restart/wall-clock-jump/duplicate-warning traces và consumer payload fixtures; P1 review FE-05 clock/warning/uncertainty display, P4 review INTG-04/INTG-11 measurement/wiring, P3 review media/off-screen accounting boundaries. Không suy màn hình thực tế của trẻ hoặc compliance từ fixture clock.

## BE1-12 — Scoped read models và mediated artifact delivery

- **Đầu ra:** role-minimized session view, allowlisted read-model gateway, artifact access-ticket application/adapter với exact version/hash/purpose/audience/review/consent revalidation; dashboard/gallery/audit metadata có unavailable/freshness rõ. P3 cung cấp read/eligibility ports cho pending AI/video/jobs/content/catalog/preset; không expose arbitrary queries hoặc raw DB joins.
- **Phụ thuộc/gate:** BE1-03/05/06/02; H-OPERATIONS/H-ADMIN-POLICY và relevant P3 handoff contract fixtures. Runtime media delivery sau actual P3 exact-review port được nối; ticket lifetime/storage delivery mechanism cần ADR/policy.
- **Truy vết:** FR001, FR009, FR019, FR026, FR033, FR036, FR051, FR054, FR057–059, FR063; UC-017/020/024/032/034/037; DATA-01, DATA-07, DATA-20, DATA-35 + delegated P3 data; **CMD-11, CMD-59, CMD-60**; P-NFR-06/07/08/13/16.
- **Nghiệm thu:** positive: Teacher đúng scope có dashboard/group/help/review metadata; admitted Child chỉ lấy eligible approved exact artifact qua backend-mediated handle. Negative: unknown query/filter, pending device roster, Admin monitoring raw content, revoked grant/consent, stale/recalled/unapproved artifact và alternate thumbnail/download bypass đều denied; response/logs không chứa provider/bucket secrets.
- **Evidence/reviewer:** read/subscribe/thumbnail/artifact scope matrix, revoke-between-ticket-and-delivery race, projection contract and redaction tests; P3 review producer eligibility ports, P1 review query states, P4 review gateway composition. P2 là sole owner route; P3 own source projections.

## BE1-13 — Gallery snapshots, trình bày và chú thích

- **Đầu ra:** gallery publish/order/annotation/present/unpublish trên immutable snapshots, contributor refs và AI-overlay marker; class/session sharing/audience checks cho item, thumbnail và delivery. Child explanation format theo approved policy, không tự bật mic/camera.
- **Phụ thuộc/gate:** BE1-05/09/10/12; H-GALLERY cho P1/P3. Chốt sharing/minimization/age explanation policy; activity/video không thuộc gallery module.
- **Truy vết:** FR019, FR031–033, FR047, FR059; UC-017/022/030; DATA-20, DATA-32; **CMD-37, CMD-65**; FIX-PRIV-03, FIX-UX-07.
- **Nghiệm thu:** positive: Teacher chọn snapshot exact revision, reorder atomic giữ unique published sequence; annotation không sửa art gốc, history cho biết có AI layer. Negative: sharing consent bị revoke, foreign snapshot/audience, stale gallery revision hoặc muốn presenting chưa authorized bị chặn; no private peer data leak.
- **Evidence/reviewer:** snapshot/hash/order/version fixtures và sharing access/consent tests; P1 review C06/T08, P3 review gallery snapshot consumption cho knowledge, P4 review mediated presentation.

## BE1-14 — Observation, reflection, assessment và portfolio

- **Đầu ra:** Teacher observation/Child own reflection, append corrections/withdrawals, descriptive assessment policy adapter, portfolio compose/annotation/redaction và scoped longitudinal read. Evidence type phân biệt child contribution/direct evidence, Teacher judgement và AI inference; group artifact không tự chứng minh năng lực cá nhân. No ranking/psychology/intelligence inference.
- **Phụ thuộc/gate:** BE1-03/05/10/11/13; H-ACTIVITY/H-AI-REVIEW source refs từ P3; rubric/portfolio retention/source-expiry policy cần adopt. H-ASSESSMENT-PORTFOLIO cho FE; export bundle do BE1-15.
- **Truy vết:** FR011, FR044–050, FR058–060; UC-011/028–031; DATA-19, DATA-20, DATA-30, DATA-31; **CMD-46, CMD-47, CMD-62, CMD-64**; FIX-UX-06, FIX-PRIV-03.
- **Nghiệm thu:** positive: portfolio nối session/process/art/activity/reflection/observation refs có provenance và own-child progress; correction giữ original + reason, chưa quan sát là explicit trạng thái. Negative: Child ghi judgement Teacher/peer reflection, AI tự confirmed assessment, foreign portfolio và report rank peers bị từ chối; source expiry không silently giữ raw copy vô hạn hoặc tạo broken ref mà không disposition.
- **Evidence/reviewer:** evidence taxonomy/permission/correction/source-expiry fixtures, sample synthetic within-child report and cross-child denial; P1 review T11/T12/C09, P3 review AI/activity evidence boundary, P4 review portfolio session-completion wiring.

## BE1-15 — Retention 90 ngày, export/delete và copy-purge workflow

- **Đầu ra:** lifecycle-request create/status/review actions, authority/scope verification, discovery manifest/lineage, export minimization, inaccessible expiry→purge workflow và per-copy receipts/exceptions. Session/artwork anchor end+90 ngày; portfolio/profile/audit/device/provider/backups có policy riêng. P3 cung cấp provider-copy discovery/purge and stale-job cancel ports; P2 own lifecycle application and core storage purge.
- **Subtask có ranh giới — policy quản trị ngoài AI:** P2 giao domain/application adapter cho organization/purpose/retention policy draft→review→activate/disable/rollback, effective-version query và append-only change audit. H-ADMIN-POLICY core gồm proposed `CorePrivacyPolicyChangeV1Candidate`/policy snapshot, positive/negative fixtures và safe metadata cho A10. Map vào typed policy branch DATA-33/CMD-48: P3 giữ sole router/schema dispatcher, gọi P2 versioned policy port; P3 không ghi policy DB của P2, P2 không tạo route CMD mới. Non-AI policy activation cần đúng capability và review, rollback tạo effective-version decision mới, không sửa provenance hoặc reset ended_at/retention anchor. Default raw session/artwork 90 ngày đã owner-confirmed, không tự rollback thành vô hạn hoặc đổi default; thay quyết định owner cần approval riêng. Portfolio/profile/audit/copy TTL mở chỉ effective sau policy decision, không default theo 90 ngày.
- **Phụ thuộc/gate:** BE1-02/03/05/10/13/14; H-DATA-REQUEST cùng P3/P4. Shared-art deletion, backup/copy retention, authority/exception/request delivery policies phải adopt trước actual purge/pilot; chưa chốt thì policy_review/blocked scope, không xóa peers theo tiện lợi. Test synthetic destructive fixture riêng.
- **Truy vết:** FR006, FR048, FR057–059, FR064; UC-003/031/037/038; DATA-05, DATA-20, DATA-31–DATA-32, DATA-34–DATA-35; **CMD-49, CMD-50, CMD-63**; FIX-PRIV-01–05, P-NFR-12/13.
- **Truy vết policy subtask:** B23 A10, B24, FR059/064; UC-038; shared DATA-33 governance envelope và DATA-35 audit; CMD-48 typed dispatch do P3 primary; H-ADMIN-POLICY core. Cấu hình ngoài AI là phần refinement PROPOSED cần adopt, không mở rộng route catalogue hoặc giao AI policy của BE2-14 cho P2.
- **Nghiệm thu:** positive: verified request chỉ export/delete subject scope, due_at giữ đúng end+90 sau restart; manifest truy tới copies, completed chỉ theo receipts và approved policy. Negative: thiếu authority, peer-owned shared strokes, provider/backup purge pending không báo all-copies-deleted; consent/grant revoke trong export job chặn download; restore không làm dữ liệu đã purge xuất hiện lại.
- **Nghiệm thu policy subtask:** positive: authorized draft/review/activate pin effective version và runtime resolver nhận bản đó; approved rollback giữ prior versions/audit và không reset raw retention anchor. Negative: monitoring-only Admin, author self-activate, unreviewed/unknown policy fields, unresolved copy TTL hoặc version stale bị reject; AI policy branch không được P2 port xử lý và raw90 default không bị client payload tự ghi đè.
- **Evidence/reviewer:** clock-boundary fixtures, authorized export manifest, shared-canvas policy cases, per-store/provider stub+actual receipts được phân biệt, no-resurrection tests; P3 review provider-copy ports, P4 review retention/restore integration, P1 review authority/pending/exception UI. Fake provider purge chỉ chứng minh contract, không completion thật.
- **Evidence/reviewer cho policy:** change/version/activate/rollback fixture traces và CMD-48 dispatch-to-core consumer checks; P3 review typed dispatcher/schema compatibility, P1 review A10 policy states, P4 review effective runtime policy wiring.

## BE1-16 — Automatic grouping proposal và Teacher commit (Phase 2)

- **Đầu ra:** approved grouping criteria/version, immutable proposal/job result, Teacher review/overrides và atomic commit memberships/current revisions. Thuật toán có explainable bounded inputs được duyệt; không suy tâm lý/năng lực từ tranh và không tự đổi nhóm lúc chưa Teacher commit.
- **Phụ thuộc/gate:** BE1-06/08/03; decision OD18 trước algorithm selection/implementation. Có fixture deterministic ngay khi independent stream; actual automatic grouping là Phase 2 confirmed capability, không gắn status done vào manual grouping pilot.
- **Truy vết:** FR008, FR065; UC-006; DATA-06, DATA-08, DATA-13; **CMD-57, CMD-58**; AT-UC-006-P/N.
- **Nghiệm thu:** positive: proposal dùng pinned roster/criteria, Teacher sửa rồi commit atomic, scopes/grants cập nhật giống manual membership semantics. Negative: child absent/duplicate, stale roster/group revision, unauthorized actor hoặc proposal tự commit bị reject; failed commit không nửa lớp ở nhóm mới/nửa ở nhóm cũ.
- **Evidence/reviewer:** proposal/override/criteria provenance fixtures, stale+atomicity tests và manual parity comparison; P1 review T03/T06, P4 review grouping allocation, P3 review job interface nếu asynchronous.

## Index primary route ownership — 52/66 CMD

Route primary owner là P2; bảng gắn mỗi CMD một task duy nhất. Các CMD còn lại thuộc P3, không được đặt thêm primary owner ở P2. Typed actions trên một route giữ closed union và exact revision checks theo SRS, không mở arbitrary CRUD.

| Contract | Primary task |
|---|---|
| CMD-01 | BE1-04 |
| CMD-02 | BE1-04 |
| CMD-03 | BE1-04 |
| CMD-04 | BE1-04 |
| CMD-05 | BE1-04 |
| CMD-06 | BE1-04 |
| CMD-07 | BE1-03 |
| CMD-08 | BE1-05 |
| CMD-09 | BE1-05 |
| CMD-10 | BE1-06 |
| CMD-11 | BE1-12 |
| CMD-12 | BE1-06 |
| CMD-13 | BE1-06 |
| CMD-14 | BE1-07 |
| CMD-15 | BE1-07 |
| CMD-16 | BE1-07 |
| CMD-17 | BE1-03 |
| CMD-18 | BE1-03 |
| CMD-19 | BE1-06 |
| CMD-20 | BE1-11 |
| CMD-21 | BE1-11 |
| CMD-22 | BE1-11 |
| CMD-23 | BE1-11 |
| CMD-24 | BE1-08 |
| CMD-25 | BE1-08 |
| CMD-26 | BE1-08 |
| CMD-27 | BE1-09 |
| CMD-28 | BE1-10 |
| CMD-29 | BE1-09 |
| CMD-30 | BE1-09 |
| CMD-31 | BE1-10 |
| CMD-37 | BE1-13 |
| CMD-46 | BE1-14 |
| CMD-47 | BE1-14 |
| CMD-49 | BE1-15 |
| CMD-50 | BE1-15 |
| CMD-51 | BE1-03 |
| CMD-52 | BE1-03 |
| CMD-53 | BE1-03 |
| CMD-54 | BE1-05 |
| CMD-55 | BE1-05 |
| CMD-56 | BE1-04 |
| CMD-57 | BE1-16 |
| CMD-58 | BE1-16 |
| CMD-59 | BE1-12 |
| CMD-60 | BE1-12 |
| CMD-61 | BE1-09 |
| CMD-62 | BE1-14 |
| CMD-63 | BE1-15 |
| CMD-64 | BE1-14 |
| CMD-65 | BE1-13 |
| CMD-66 | BE1-08 |

## Index primary logical-data ownership — 25/35 DATA

| Contract | Primary task duy trì schema/semantics |
|---|---|
| DATA-01 | BE1-03 |
| DATA-02 | BE1-04 |
| DATA-03 | BE1-04 |
| DATA-04 | BE1-04; Teacher-assignment behavior BE1-03 |
| DATA-05 | BE1-05 |
| DATA-06 | BE1-06 |
| DATA-07 | BE1-06; lifecycle handlers BE1-11 |
| DATA-08 | BE1-08 |
| DATA-09 | BE1-07 |
| DATA-10 | BE1-07 |
| DATA-11 | BE1-07 |
| DATA-12 | BE1-03; admission producer BE1-07 |
| DATA-13 | BE1-08 |
| DATA-14 | BE1-09 |
| DATA-15 | BE1-09 |
| DATA-16 | BE1-09 |
| DATA-17 | BE1-09 |
| DATA-18 | BE1-09 |
| DATA-19 | BE1-10 |
| DATA-20 | BE1-10; asset repository adapters BE1-02 |
| DATA-30 | BE1-14 |
| DATA-31 | BE1-14 |
| DATA-32 | BE1-13 |
| DATA-34 | BE1-15 |
| DATA-35 | BE1-03; durable audit adapter BE1-02 |

Mỗi DATA có một schema maintainer P2. Các task behavior khác consume/review versioned schema, không fork DTO riêng. DATA-20 cũng chứa artifact refs từ P3; provenance/eligibility của derived AI/media do P3 producer bảo đảm, P2 không sửa content để vượt review.

## Rủi ro cần giữ trên bảng công việc

1. P2 có 52 route nhưng route count không phản ánh độ khó: canvas consistency/durability/privacy có khối lượng lớn; P3 có ít route hơn nhưng model/video/content pipelines khó. Chia theo ownership này cần pull từng bounded slice, không coi số route là phân công cân bằng đã chứng minh.
2. FE chỉ có một người cho Child Android + Teacher/Admin; backend deliver contract/error/recovery fixtures sớm qua BE1-01 để FE chạy độc lập. P4 không nhận viết lại canvas/backend chỉ để bù deadline chưa có.
3. Bản v3.1 là baseline đầy đủ nhưng payload/sync/tool/retention-copy/provider details có PROPOSED/TBD. Task tương ứng chỉ triển khai phần đã adopt; unresolved gate có ID và ảnh hưởng rõ, không silent default.
4. DONE của từng module cần code + own tests + evidence + review; whole-class pilot cần actual integrated adapters/device/load/privacy evidence do cả đội cung cấp. Fixtures, demo login, placeholder video hoặc scaffold compose không được báo full system done.
