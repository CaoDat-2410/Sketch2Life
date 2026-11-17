# Người 3 — Backend AI, knowledge, video, activity và content

Tài liệu chia việc dựa trên Master SRS v3.1, B19–B26 và audit FEAT-039. **P3 là người BE thứ hai**; đây là backlog đề xuất, chưa là approval triển khai runtime. Không gán ngày, tuần hoặc giờ. Mỗi card triển khai sau này có feature plan/approval và evidence riêng.

P3 giữ domain/application độc lập FastAPI, model SDK, queue và storage. P3 tự xây adapter/job/media worker của module mình; P4 ghép composition root, cấu hình runtime và luồng tích hợp. P4 không phải người làm thay toàn backend, infrastructure hoặc test. P3 phải giao tests và fault evidence cho phần mình.

## Ranh giới và handoff chung

- **Nhận:** `H-IDENTITY`, `H-CLASS-CONSENT`, `H-SESSION-CONTROL`, `H-CANVAS-SYNC` từ P2 qua versioned contracts/ports. Payload tối thiểu gồm verified principal/grant, authorized audience, age 36–155 tháng, purpose/consent revisions, session/config epochs, immutable checkpoint/version/hash và current cancellation/revocation decision. Không đọc bảng classroom/canvas/consent trực tiếp để nối module.
- **Phát:** `H-AI-REVIEW`, `H-KNOWLEDGE-VIDEO`, `H-ACTIVITY`, `H-CONTENT-PRESET`, `H-ADMIN-POLICY`, `H-OPERATIONS`, cùng phần provider-copy lifecycle của `H-DATA-REQUEST`. Mỗi package có schema version, synthetic positive/negative fixtures, error catalogue, executable contract checks, metadata migration note và consumer example cho P1/P2/P4.
- **Tên typed contract candidate:** `LearningContextV1`, `ArtifactReferenceV1`, `AuthorizationDecisionV1`, `JobStatusV1`, `CancellationNoticeV1`. Chúng phải map đúng DATA/B22 và được adopt trong registry chung; không dùng tên mới để tạo schema cạnh tranh với SRS.
- P2 là primary owner route `CMD-59` read-model dispatcher và `CMD-60` artifact access-ticket; P3 giao scoped projection providers và artifact/review eligibility qua port. P3 không tạo một đường đọc media khác bypass gate. Read, poll, cache hit và worker completion đều recheck quyền/purpose/version hiện hành.
- `DATA-20` provenance/artifact access và `DATA-35` audit là hợp đồng dùng chung do P2 quản lý; P3 phát metadata/audit events đúng version. Tranh gốc, recognition, correction, AI derivative và Teacher review giữ nguồn riêng.
- Chặng đầu là **BE2-01 fixture/contract stream độc lập**, chạy với fake authorization/session/artifact/provider/queue; không chờ backend P2 đang chạy, cloud hoặc app P1. Model thật, persistent adapter, queue runtime và live wiring chỉ được nghiệm thu trong feature/integration đã được duyệt.

## Danh mục primary ownership

| Card | Primary route contracts | Primary DTO / shared DTO | Handoff |
|---|---|---|---|
| BE2-01 | CMD-44 | DATA-25 | H-OPERATIONS |
| BE2-02 | CMD-34 | DATA-22 | H-AI-REVIEW |
| BE2-03 | CMD-32, CMD-33 | DATA-21 | H-AI-REVIEW, H-OPERATIONS |
| BE2-04 | Không thêm route; backend worker port | DATA-23 | H-AI-REVIEW |
| BE2-05 | CMD-35 | DATA-24; shared DATA-23 | H-AI-REVIEW |
| BE2-06 | CMD-36 | Shared DATA-23/24 | H-AI-REVIEW |
| BE2-07 | CMD-38, CMD-39 | DATA-26 | H-KNOWLEDGE-VIDEO |
| BE2-08 | CMD-40 | DATA-27 | H-KNOWLEDGE-VIDEO, H-OPERATIONS |
| BE2-09 | CMD-41, CMD-42 | Shared DATA-24/27 | H-KNOWLEDGE-VIDEO |
| BE2-10 | CMD-43 | DATA-28 | H-KNOWLEDGE-VIDEO |
| BE2-11 | CMD-45 | DATA-29 | H-ACTIVITY |
| BE2-12 | CMD-48 | DATA-33 | H-CONTENT-PRESET |
| BE2-13 | Typed preset branch của CMD-48 qua BE2-12; không primary router thứ hai | Shared DATA-33 | H-CONTENT-PRESET |
| BE2-14 | Typed AI-policy branch của CMD-48 qua BE2-12; không primary router thứ hai | Shared DATA-33 | H-ADMIN-POLICY, H-OPERATIONS |

Các route P3 primary là đúng 14 route: CMD-32–36, CMD-38–45, CMD-48. Không gán primary ownership CMD-37 gallery, CMD-46/47 observation/portfolio, CMD-49/50 lifecycle hoặc routes P2 khác cho P3. P3 chịu **10 DTO primary**: DATA-21–29 và DATA-33; DATA-24 chỉ có một primary schema owner tại BE2-05 dù review được nhiều module sử dụng.

## BE2-01 — AI/job contract foundation và harness độc lập

- **Reviewer:** P2 review authorization/persistence/outbox boundaries; P1 review job status/error payload; P4 review composition và completion wiring.
- **Phạm vi:** dựng domain job lifecycle và standalone runner cho AI/media; fake clock/provider/queue/artifact/authorization để chạy thành công, lỗi, timeout, cancel và stale result. Đây là đầu ra độc lập đầu tiên của P3, không cần live P2.
- **Giao:** chặng độc lập đầu tiên có schema/payload fixtures DATA-21–29/33, DATA-25 validator, bounded job/attempt state machine, scoped polling handler CMD-44, backend-only completion port, queue/job repository ports và fake adapters; fake provider-copy discovery/purge/receipt fixtures cùng repository port cho BE2-14. **Chặng runtime riêng sau approval** do P3 giao durable DATA-25 job repositories/migrations, attempt/request CAS, dispatch/completion receipts và transactional outbox/queue adapter; job state của P3 không chuyển sang P2/P4 làm thay. Chặng này cần runtime/storage decision và core generic persistence contracts được adopt, không chặn runner độc lập ban đầu hoặc coi fake store là persistent store.
- **Điều kiện trước:** SRS/feature approval; không có dependency live. Numeric retry/budget/progress policy chưa adopt dùng named fixture policy và ghi rõ PROPOSED.
- **Handoff:** `H-OPERATIONS` gồm `JobStatusV1`, typed failure/public message, polling hints, cancellation/completion fixtures; `H-DATA-REQUEST` có provider-copy fake receipt/unsupported/Pending/Exception cases từ contract BE2-14. P4 nhận composition contract; P1 nhận queued/running/retryable/exhausted/cancelled/unknown-progress states.
- **Truy vết:** FR029, FR030, FR037, FR051, FR054; UC-019/025/032; DATA-25; CMD-44; B19.10, B22.3, P-NFR-16.
- **Nghiệm thu dương:** retry cùng semantic request trả một job; job success có exact result refs nhưng không tự thành Teacher approval hoặc session complete; unknown progress giữ unknown. Chặng durable riêng restart sau commit vẫn giữ job/attempt/receipt, outbox dispatch retry không tạo semantic attempt mới và CAS chặn concurrent completion.
- **Nghiệm thu âm:** completion sai attempt/request/context hoặc sau revoke bị stale/rejected; job ngoài scope không lộ artifact/provider internals; cancel không bị late success mở lại.
- **Evidence:** runner command/result, schema fixture report, state-transition table, duplicate/cancellation fault traces đã redaction, adapter contract test. Chặng durable riêng có migration report, actual restart/attempt-CAS/outbox/dispatch fault receipts và adapter tests; fake provider purge chỉ chứng minh contract, chưa chứng minh actual copy deletion.

## BE2-02 — Tái sử dụng Vision và correction có provenance

- **Reviewer:** P2 review snapshot/consent/version; P1 review meaning/correction projections; P4 review adapter/provider wiring.
- **Phạm vi:** bọc Vision/Qwen transport hiện có vào canvas snapshot + topic + age/context contract mới; nhận object candidates/uncertainty, lưu Teacher/Child correction riêng. Không coi SAM/animation là Sketch generator.
- **Giao:** Vision application port/adapter mapping; source snapshot/version/hash validation; DATA-22 persistence port; CMD-34 correction use case và handler; fake provider cases wrong recognition/low confidence/malformed response.
- **Điều kiện trước:** BE2-01; snapshot/context và authority fixtures từ `H-CANVAS-SYNC`/`H-CLASS-CONSENT`. Adapter thật cần model/profile/serving/license/budget decision và feature approval; chất lượng adapter cũ phải đo lại trên context mới.
- **Handoff:** `H-AI-REVIEW` analysis/correction refs, uncertainty nullable confidence, source revisions và invalidation notice. P1 có projection đúng tuổi; P4 nối provider credentials backend-only.
- **Truy vết:** FR022, FR023, FR061; UC-018; DATA-22; CMD-34; AT-CS-008.
- **Nghiệm thu dương:** snapshot hợp lệ sinh candidate; Teacher/Child đúng scope sửa ý định, original inference và correction/author/reason đều truy vết được.
- **Nghiệm thu âm:** đổi context/snapshot làm result cũ không được authoritative; model không suy tuổi hoặc psychology/intelligence; malformed output thành typed failure, không bịa confidence.
- **Evidence:** synthetic snapshot-to-result/correction fixtures, revision-conflict tests, sanitized provider mapping; real inference report có model revision/profile/input hash khi được duyệt.

## BE2-03 — Assistance request, cancel, dedup và budget orchestration

- **Reviewer:** P2 review target/turn/purpose scope; P1 review request/cancel/rate feedback; P4 review scheduling/status/completion boundaries.
- **Phạm vi:** Child/Teacher yêu cầu trợ giúp cho cá nhân/nhóm/vùng; current turn và audience validation; queue Vision/Sketch job, debounce/cache/budget, cancel và stale completion.
- **Giao:** DATA-21 command/application service; CMD-32/33 handlers; request repository/idempotency ports; bounded scheduling/budget policy adapter do P3 sở hữu; audit/cancellation events. Idempotency khác payload phải conflict.
- **Điều kiện trước:** BE2-01/02; `H-CLASS-CONSENT`, `H-SESSION-CONTROL`, `H-CANVAS-SYNC` schemas. Real budget/rate/retry parameters phải được adopt; fixture không khóa giá trị production.
- **Handoff:** `H-AI-REVIEW` request status/context/target; `H-OPERATIONS` job/queue/budget status. Nhóm mixed-age kiểm từng audience member, không lấy tuổi trung bình.
- **Truy vết:** FR024, FR025, FR028, FR029, FR030, FR054; UC-019/032; DATA-21/25; CMD-32/33; FIX-UX-04, FIX-NFR-02.
- **Nghiệm thu dương:** request đúng grant/purpose/context tạo một job và Child tiếp tục vẽ; cancel đúng actor lưu outcome, retry duplicate không tăng chi phí semantic.
- **Nghiệm thu âm:** idle riêng lẻ không tạo kết luận thiếu kiến thức/request tự động; request vượt scope/budget hoặc consent thiếu không gọi provider; cache hit/cancel late result không bypass Teacher review.
- **Evidence:** request/cancel/duplicate/cache/stale tests, bounded queue fixture và budget accounting traces; scoped read-model examples cho CMD-59 owner.

## BE2-04 — Pipeline tạo Sketch thật và output tách tranh gốc

- **Reviewer:** P2 review artifact/source/consent lineage; P1 review output shape/overlay separation; P4 review worker/provider activation and lifecycle hooks.
- **Phạm vi:** năng lực mới tạo reference/question/line-sketch/overlay theo support policy đã chọn. Giữ port độc lập model; fake provider phục vụ contract first, nhưng fake hoặc Vision classifier không đủ nghiệm thu generation thật.
- **Giao:** DATA-23 producer; SketchGenerator port, fake/real adapters, own worker/timeout/cancel handling; output media admission/provenance; separate AI overlay reference và support-level revision. Vision/Sketch provider adapters implement BE2-14 `ProviderCopyLifecycle` hooks: discover input/output/job/cached copies được biết, scoped cancel/purge request, verify receipt/status và unsupported/pending/exception outcome. Output không là command sửa child strokes.
- **Điều kiện trước:** BE2-01/02/03; taxonomy/support modes/output shape và model/profile/license/cost/quality gate được quyết định qua ADR/feature approval. BE2-14 policy ref có thể dùng fixture trước live; không chọn model hoặc SAM bắt buộc trong card.
- **Handoff:** `H-AI-REVIEW` proposal/version/hash/source/context/producer; asset admission dùng `ArtifactReferenceV1` port của P2. `H-DATA-REQUEST` có scoped provider-copy refs và actual/fake-marked lifecycle receipts; P1 chỉ nhận asset/text khi review gate cho phép.
- **Truy vết:** FR019, FR025, FR028, FR029, FR030; UC-017/019; DATA-23, shared DATA-20; backend-only worker port; FIX-UX-04, P-NFR-08.
- **Nghiệm thu dương:** approved real profile tạo được Sketch asset đúng shape từ synthetic source, có provenance và immutable source; result chờ moderation/Teacher review.
- **Nghiệm thu âm:** không thay nét/gán contribution AI cho trẻ; stale/unsafe/malformed/cancelled output không child exposure; quá timeout/budget ghi typed outcome, không loop vô hạn.
- **Evidence:** fake contract report riêng; sau approval có actual generated asset/hash, sanitized provider request/result metadata, decoding/safety/quality review và latency/cost/memory profile; provider-copy lifecycle tests/actual receipt hoặc explicit Unsupported/Pending/Exception. Không đánh dấu real generation hoặc actual purge DONE bằng fixture pass.

## BE2-05 — Moderation và Teacher duyệt từng Sketch

- **Reviewer:** P2 review eligibility/consent/asset access; P1 review Teacher queue và approved-only Child payload; P4 review gate/invalidation races.
- **Phạm vi:** moderation trước phát nội dung, review queue eligibility; Teacher approve/reject/request_changes đúng từng item/version/hash/audience. Sửa output/support level tạo version mới.
- **Giao:** DATA-24 primary schema/ExactContentReview port; CMD-35; review repository/current-eligibility service; approved-only child projection; review invalidation events; metadata cho P2 artifact-ticket và read-model dispatchers.
- **Điều kiện trước:** BE2-01/04; teaching authority/context fixtures; approved moderation/reviewer policy (BE2-14 cung cấp versioned config). Không đòi live P2 cho fixture tests.
- **Handoff:** `H-AI-REVIEW` review queue item, safe preview cho Teacher, exact approval/ref/state và availability. Các video/library reviews dùng shared DATA-24, không tạo schema khác.
- **Truy vết:** FR026, FR029, FR061; UC-020; DATA-23/24; CMD-35; AT-CS-009.
- **Nghiệm thu dương:** safe exact item được Teacher đúng scope approve, chỉ approved audience nhận được; duplicate approve có một semantic review.
- **Nghiệm thu âm:** pending/rejected/blocked/edited/stale proposal không có child content; preset/system admin không tự approve; Teacher không bypass unsafe gate; If-Match cũ conflict.
- **Evidence:** positive/negative exact-hash review tests, pending-content leakage test qua fetch/cache/subscription/ticket port, invalidation race fixtures, review audit sample.

## BE2-06 — Child view/hide/decline và tiếp tục vẽ

- **Reviewer:** P2 review bound turn/attribution/revoke; P1 review child agency; P4 review response/artifact integration.
- **Phạm vi:** ghi response theo participant/turn cho approved Sketch; hỗ trợ hide/decline mà giữ child drawing và review history.
- **Giao:** CMD-36 command handler; DATA-23 child-response projection; response idempotency/attribution port; Teacher response event. P1 thực hiện UX/overlay display; P3 chịu authority/domain invariants.
- **Điều kiện trước:** BE2-05; current turn/grant fixtures từ P2. Chính sách xem lại item đã decline nếu muốn cần refinement riêng, không tự refresh gợi ý.
- **Handoff:** `H-AI-REVIEW` available/viewed/hidden/declined payload và projection; explicit overlay visibility state tách canvas operations.
- **Truy vết:** FR019, FR027, FR028; UC-017/021; shared DATA-23/24; CMD-36; P-NFR-08.
- **Nghiệm thu dương:** Child đúng lượt xem rồi hide/decline, response lưu đúng version/author; vẽ tiếp không bị đổi stroke hoặc trừ đánh giá.
- **Nghiệm thu âm:** review/grant bị revoke chặn URL/ref cũ; child response không approve AI sửa tranh; retry không nhân records, decline không ép gọi lại model.
- **Evidence:** turn/revocation/idempotency tests, before/after source hash, UI-facing response fixtures và Teacher event contract checks.

## BE2-07 — Knowledge có nguồn và script versioning

- **Reviewer:** P2 review audience/source/context refs; P1 review Teacher script/source UI; P4 review downstream version invalidation.
- **Phạm vi:** resolve confirmed topic/meaning, tìm reviewed knowledge, gắn factual claims với nguồn; tách yếu tố tưởng tượng và Teacher corrections; edit script invalidates downstream exact review/results.
- **Giao:** DATA-26; CMD-38/39 handlers; knowledge-source/library ports; bundle version/hash/provenance; source-validation fixtures, script edit and downstream invalidation events.
- **Điều kiện trước:** BE2-01; confirmed context fixtures từ BE2-02/P2; source/content policy refs. Pre-render script approval là proposal cần adopt nếu dùng, không thay mandatory final video approval.
- **Handoff:** `H-KNOWLEDGE-VIDEO` bundle/version/hash/audience/claims/source refs và generation-ready or needs-content-action outcome.
- **Truy vết:** FR034, FR035, FR040; UC-023; DATA-26; CMD-38/39; FIX-GOV-01, AT-CS-010.
- **Nghiệm thu dương:** concept hợp lệ tạo bundle có claim/source/version; Teacher correction tạo phiên bản mới và downstream cũ mất eligibility đúng contract.
- **Nghiệm thu âm:** fantasy không thành science fact; thiếu nguồn trả Teacher content action, không model self-verification; generic content không bị ép fabricated child consent và child-derived content không né purpose checks.
- **Evidence:** claim-source mapping/review report trên synthetic cases, edit/stale tests, imagined/factual separation fixtures, bounded-text validation.

## BE2-08 — Library resolution và pipeline video generation thật

- **Reviewer:** P2 review artifact storage/consent/source version; P1 review waiting/progress/media shape; P4 review queue/worker/provider/lifecycle wiring.
- **Phạm vi:** reviewed_library/generate/compose_library strategies, exact bundle/audience/profile refs; job/media validation và immutable final artifact. Path generate thật phải có trong backlog, không chỉ DeferredVideo/placeholder.
- **Giao:** DATA-27 producer; CMD-40; VideoGenerator/LibraryResolver/MediaValidator ports; P3 queue/worker/backend provider adapters, cancellation/progress/attempt handling; storage/artifact integration qua P2 port; safe final asset chờ review. Video và optional TTS/media provider adapters implement BE2-14 `ProviderCopyLifecycle` hooks cho input/script/output/cache/job copies, scoped cancel/purge dispatch và actual receipt/verification hoặc explicit Unsupported/Pending/Exception. Narration/TTS chỉ conditional nếu được chọn.
- **Điều kiện trước:** BE2-01/07; adopt policy/rights/content/profile/encoding/audience và final Teacher review cho strategy đã chọn. Model/provider/license/budget/render timeout/retry gates chỉ áp dụng generate hoặc composition có gọi generation/provider. Path reviewed_library không phải chờ generation model decision, vẫn kiểm publication/usage rights, content/profile/encoding/audience và Teacher duyệt exact video trong phiên. Done của toàn card vẫn cần evidence library và real-generation path đã chọn trong scope; fake/placeholder hoặc riêng library pass không hoàn tất nghĩa vụ real generation. Không mặc định Wan, 40–60 giây, L4, narration hoặc một cloud từ lịch sử.
- **Handoff:** `H-KNOWLEDGE-VIDEO` independent generation/review/playback axes; `H-OPERATIONS` truthful progress/job/attempts/public errors; `H-DATA-REQUEST` provider copy refs, scoped cancellation/purge and per-copy receipt/status. P4 nối worker/service config; P3 giao adapters và runner thực hiện.
- **Truy vết:** FR034, FR037, FR038, FR040; UC-023/025; DATA-25/27, shared DATA-20; CMD-40; FIX-UX-05, AT-CS-011.
- **Nghiệm thu dương:** valid generation request tạo actual decodable video có source/profile/hash; library hit cũng chờ per-session Teacher review; queued/running vẫn ở waiting stage.
- **Nghiệm thu âm:** placeholder hoặc fixture không được báo generated; unsafe/stale/recalled result bị chặn; timeout không auto fallback/skip/play; progress unknown không bịa percentage.
- **Evidence:** fake path tests riêng; sau approval có sanitized actual render/decoder/quality record và cost/latency/profile; worker retry/cancel/restart evidence khi durable adapters đã implement; lifecycle per-copy actual receipt/verification hoặc outstanding status. Stub deletion không được coi actual provider purge complete.

## BE2-09 — Final video review và authorized playback

- **Reviewer:** P2 review session/audience/mediated asset authority; P1 review review/playback states; P4 review exact-hash delivery chain.
- **Phạm vi:** Teacher kiểm/chỉnh/reject final artifact đúng exact version/hash và audience; playback chỉ với effective review + current session/grant/consent/content eligibility.
- **Giao:** CMD-41/42; DATA-24 session_content review integration; DATA-27 playback lifecycle, capability validation và metadata cho mediated access port. Library publication review không thay Teacher approval trong phiên.
- **Điều kiện trước:** BE2-08 và **shared DATA-24 exact-content review contract/schema fixtures của BE2-05**, không cần real Sketch generation hoặc live Sketch-review service. Reviewed-library video có thể được triển khai/verify độc lập path Sketch. Session advance/access port contract của P2; video content/profile review policy. Chỉnh script/media tạo version mới và render/review lại theo scope.
- **Handoff:** `H-KNOWLEDGE-VIDEO` ready_for_review/approved/playing/rejected/stale fixtures, playback intent/result và exact review refs. Không phát bucket/provider credentials hoặc raw permanent URL.
- **Truy vết:** FR035, FR036, FR040; UC-024; DATA-24/27; CMD-41/42; AT-CS-010.
- **Nghiệm thu dương:** Teacher approve final exact artifact rồi start playback cho authorized audience; review revision khác run/job/session revisions được kiểm đúng.
- **Nghiệm thu âm:** generic published video vẫn không play khi chưa session Teacher review; edit/audience/context/revoke làm review không còn hiệu lực; stale ETag hoặc URL cũ không bypass gate.
- **Evidence:** final-hash/review-axis tests, library-vs-session review fixtures, unauthorized/stale playback tests qua access port, public playback error samples.

## BE2-10 — Video exhausted failure: Teacher retry/skip/end

- **Reviewer:** P2 review stage/finish/checkpoint outcomes; P1 review Teacher disposition UI; P4 review cross-module receipts/atomicity.
- **Phạm vi:** sau các automatic retries được phép thất bại, Teacher explicit disposition; history giữ prior failure và budget decision. Khi còn queued/running vẫn chờ.
- **Giao:** DATA-28; CMD-43; disposition repository/service; retry-new-run command và session-end/skip port invocation cho P2, durable outcome events; bounded manual-retry authorization.
- **Điều kiện trước:** BE2-01/08; adopted retry/budget policy và versioned session command port. Không gọi trực tiếp session DB; orchestration phối hợp receipt/outbox/idempotency theo integration decision.
- **Handoff:** `H-KNOWLEDGE-VIDEO` failed_exhausted + permitted Teacher actions; `H-SESSION-CONTROL` explicit skipped_by_teacher/session_ended_early intent/result, không giả stage success.
- **Truy vết:** FR038, FR039; UC-025/026; DATA-25/27/28; CMD-43; AT-CS-011.
- **Nghiệm thu dương:** Teacher chọn retry tạo bounded new attempt/run, skip ghi disposition, end ghi early outcome và đòi checkpoint receipt; duplicate action không lặp side effect.
- **Nghiệm thu âm:** Child không disposition; running job trả VIDEO_NOT_EXHAUSTED; skip không generated/succeeded; retry không tạo human approval hoặc vô hạn budget.
- **Evidence:** all-three-actions tests, lifecycle/race/duplicate fixtures, cross-module failure-compensation receipt tests và disposition audit record.

## BE2-11 — Activity discovery, adaptation và execution

- **Reviewer:** P2 review session/portfolio/source handoff; P1 review activity preparation/instructions; P4 review off-screen assignment/result wiring.
- **Phạm vi:** reviewed activity library/recommendation candidate, Teacher select/adapt cho lớp/nhóm; age/safety/preparation trước execution; select/confirm_ready/start/finish/skip/interrupt lifecycle.
- **Giao:** DATA-29; CMD-45; catalog/recommendation adapter mapping reuse existing full topic/exact-age discovery as **candidate**; immutable effective assignment snapshot; objective/source versions, reason and evidence refs; event để P2 nối reflection/portfolio.
- **Điều kiện trước:** BE2-01; catalog/content fixtures và publication lifecycle BE2-12; adopt age-compatibility/safety/material/prerequisite policy khi triển khai. Existing preference-ranking/no-readiness-filter policy không tự trở thành confirmed new scope.
- **Handoff:** `H-ACTIVITY` scoped catalog/recommendation projection provider cho CMD-59, assignment/actions/feasibility state và off-screen outcome refs. P2 primary CMD-46/47 giữ observation/reflection/portfolio; P3 không tự ghi các tables đó.
- **Truy vết:** FR041, FR042, FR043; shared FR044; UC-027/028; DATA-29, shared DATA-33; CMD-45; FIX-UX-06.
- **Nghiệm thu dương:** Teacher chọn rồi chỉnh local assignment, xác nhận khả thi/an toàn theo policy, start/finish đúng version và gửi result refs; không sửa master catalog ngầm.
- **Nghiệm thu âm:** mixed-age eligibility kiểm từng audience theo approved policy, hazardous/unprepared assignment không start; discovery không thêm readiness/history/material hard filters chưa adopt; reflected result không giả Teacher observation.
- **Evidence:** catalog parity/adaptation/age/safety/preparation tests, action-state matrix và immutable-source hashes; cross-module observation handoff fixture.

## BE2-12 — Content authoring, publication review và recall

- **Reviewer:** P2 review authority/consent/recall eligibility; P1 review author/reviewer/publisher states; P4 review dispatcher/publication/consumer boundaries.
- **Phạm vi:** generic library content/activity/video draft→submit→changes/review→publish→recall/archive. P3 primary CMD-48 closed-union dispatcher và DATA-33 shared schema; preset/policy branches do BE2-13/14 giao use case adapters.
- **Giao:** content version repository/port, CMD-48 router/typed action validator; exact safety/pedagogical generic_library review integration DATA-24; independent author/reviewer/publisher authority checks; recall eligibility event/cancellation notice và consumer fixtures.
- **Điều kiện trước:** BE2-01/05 schema contracts; publication/reviewer separation/recall policy phải adopt trước runtime. BE2-05 implementation không phụ thuộc BE2-12 live; sử dụng DATA-24 fixture để tránh integration cycle.
- **Handoff:** `H-CONTENT-PRESET` immutable published record/ref/hash/review set/recall event; `H-CLASS-CONSENT` eligibility query khi child-derived content; new-session resolver blocking cho P2/P3.
- **Truy vết:** FR056, FR062; UC-035; DATA-33, shared DATA-24/35; CMD-48; FIX-GOV-01.
- **Nghiệm thu dương:** generic authored content có safety/pedagogical approvals đúng exact version và publisher capability mới publish; recall chặn phiên mới, history còn provenance.
- **Nghiệm thu âm:** author không tự publish, edit không giữ approval cũ; generic library review không yêu cầu fabricated session/child consent, child-derived classification không né policy. Active-copy deletion/replacement không tự invent khi OD05 còn mở.
- **Evidence:** full action union tests, author/reviewer/publisher separation fixtures, generic-vs-session review cases, recall/new-session tests và version/audit history.

## BE2-13 — Preset versioning, conditional automation và Teacher override

- **Reviewer:** P2 review current session/config command guards; P1 review preset/override UI; P4 review automation intent/receipt wiring.
- **Phạm vi:** preset library versions và pinned session config; conditional automation suggestions/commands revalidated trước effect; Teacher override wins trong authority hợp lệ. P2 owns effective session/config mutation; P3 không có session DB access.
- **Giao:** preset branch use cases cho CMD-48 dispatcher BE2-12; DATA-33 preset validation; automation evaluator/scheduler port, versioned command intents/receipt/stale outcomes, queue priority policy adapter nếu được adopt.
- **Điều kiện trước:** BE2-01/12; `H-SESSION-CONTROL` command/config contract; adopt preset field/condition/priority/override rules. Fixture stream dùng fake command handler, không chờ live orchestration.
- **Handoff:** `H-CONTENT-PRESET` pinned preset snapshots và automation/override records; `H-SESSION-CONTROL` scoped intent có observed config/stage versions; `H-OPERATIONS` deferral/overload/public status.
- **Truy vết:** FR052, FR053, FR054; UC-032/033; DATA-33, shared DATA-06/35; CMD-48 typed preset branch; P2 CMD-12/59 integration; FIX-GOV-01, P-NFR-16.
- **Nghiệm thu dương:** draft session dùng pinned preset; Teacher override/disable thay effective config qua P2 port và queued old-version action bị stale, có reason/audit.
- **Nghiệm thu âm:** edit preset library không đổi active session; automation không bỏ per-Sketch/final video approval, consent/safety hoặc auto-complete/purge; queue overflow không autoapprove/drop silent.
- **Evidence:** policy-condition fixtures, override/cancellation race tests, command receipt/dedup checks, config-pin hash và consumer contract examples.

## BE2-14 — System AI configuration, limits và kill switch

- **Reviewer:** P2 review data-lifecycle authority/copy manifest; P1 review scoped Admin/exception status; P4 review policy/provider-copy wiring and receipts.
- **Phạm vi:** authorized Super Admin draft/validate/publish/disable allowlisted policy/model-profile refs, moderation/retry/budget/concurrency; pinned request/attempt provenance; emergency block/cancel/revalidate.
- **Giao:** AI-policy branch adapter cho CMD-48/BE2-12; DATA-33 policy validation/version repository; policy eligibility/budget port; backend-only provider profile resolution, kill-switch cancellation events; redacted health/queue/cost projections qua H-OPERATIONS. P3 primary owner versioned **`ProviderCopyLifecycle`** contract/registry: scoped discovery, cancel, purge dispatch, receipt verification, per-copy status và Unsupported/Pending/Exception reasons; request/receipt idempotency, current authority/source-expiry checks và no-late-result exposure. BE2-01 giao fake/repository support; BE2-04/08 giao provider-specific hooks. P2 giữ lifecycle application/request authority và core-storage purge; P4 nối ports, không làm thay provider adapters.
- **Điều kiện trước:** BE2-01/12; Admin capability contract; provider/model/queue/deployment/config values phải có ADR/evidence và approved feature trước activation. Card không nâng dependencies/cloud hoặc chọn provider tự động.
- **Handoff:** `H-ADMIN-POLICY` allowlisted effective version/config metadata; `H-OPERATIONS` safe metrics/log/trace contract cho P4 wiring/CMD-59 projection; **`H-DATA-REQUEST`** copy discovery manifest/cancel-purge command/receipt/status/exception cho BE1-15 và INTG-08. Tokens, keys, endpoint secrets ở runtime backend, không policy DTO/mobile/logs.
- **Truy vết:** FR029, FR030, FR054, FR056; UC-036/037; DATA-33/25, shared DATA-35; CMD-48 typed policy branch; FIX-GOV-01, P-NFR-13.
- **Nghiệm thu dương:** publish policy v2 làm new requests pin phiên bản mới; prior requests giữ source version và check current eligibility; disable chặn work mới và disposition pending jobs traceable. Authorized lifecycle request discover được known provider copies, dispatch cancel/purge idempotent và trả exact per-copy receipts để P2 cập nhật manifest.
- **Nghiệm thu âm:** config bypass mandatory Teacher review/consent/unsafe gates bị reject; secret hoặc unallowlisted profile không vào public payload; role Admin không tự teaching approval/raw-child access. Provider không hỗ trợ purge/receipt chưa verify/ongoing copies phải Unsupported/Pending/Exception, không fake Deleted/complete; late completion sau revoke/expiry không resurrect artifact.
- **Evidence:** policy compatibility/allowlist/kill-switch tests, redaction samples, request-version/cancellation faults; ProviderCopyLifecycle conformance/discovery/duplicate/cancel/purge/unsupported/exception/no-resurrection fixtures; actual provider receipts tách riêng fake results. Real cost/load/provider reports chỉ khi approved measurement profile đã chạy; fake purge pass chưa là actual deletion completion.

## Trình tự nội bộ và ranh giới Done

Chặng độc lập đầu tiên giao BE2-01 cùng representative Vision/Sketch/video/activity/governance fixtures. Có thể xây producer/consumer contract fragments của các cards khác bằng fake ports song song với P1/P2/P4; không gọi live service để tuyên bố harness độc lập.

Dependency nội bộ triển khai: BE2-01 → BE2-02 → BE2-03 → BE2-04 → BE2-05 Sketch-review runtime → BE2-06; BE2-01 → BE2-07 → BE2-08 → BE2-09/10; BE2-01 + BE2-05 shared-schema output → BE2-12 → BE2-11/13/14. **Shared DATA-24 contract/schema fixtures của BE2-05 được thiết kế từ foundation, độc lập BE2-04**; BE2-09/12 chỉ consume phần shared contract này, không phải chờ real Sketch generator/review runtime. ProviderCopyLifecycle foundation từ BE2-14 và fake support BE2-01 cũng có thể review độc lập trước live config/purge activation. Chính sách fixture cho BE2-04/05/07/08 không đòi BE2-14 runtime trước; adopted policy/config là gate trước live activation. Generic publication và teaching review là purposes khác nhau.

Mỗi card có hai mức evidence riêng: **component/contract ready** và **runtime/integrated verified**. Real Sketch/video generation bổ sung provider evidence sau approval; media placeholder/fake, catalog fixture pass hoặc successful job không chứng minh trải nghiệm classroom/pilot đã đạt. P3 tham gia tích hợp/fix defect của modules mình và chạy component/consumer/security tests; P4 chịu ghép luồng và tổ chức E2E, các owners vẫn chịu sửa và cung cấp evidence.

Toàn bộ development dùng synthetic fixtures, không commit real child data/credentials. Parent portal, billing, social/chat/marketplace, segmentation, narration và art animation không được thêm thành mandatory prerequisite. Giá trị còn PROPOSED/TBD giữ decision gate, không giảm scope bằng cách loại generation/video để bỏ khó.
