# Roadmap BE2 — phạm vi và thứ tự thực hiện

> Latest progress (2026-10-14, final Q00 code review): original R01–R11 and follow-ups R03a/R04a/A18a CLOSED; code review PASS at fake/contract scope. ACTIVE Q00 waits for adoption/Pillow disposition, with no remaining correction from this review. Tracker and evidence/notes/PHASE_A_Q00_FINAL_CODE_REVIEW_20261014.md hold current status; dated readiness snapshots below retain the state when roadmap revision2 was authored. Queue, 14-card scope and approvals are unchanged.

- Roadmap revision: 2
- Date: 2026-10-14, Asia/Saigon
- Status: ACTIVE_FOR_PLANNING_AND_ROUTING
- Source baseline: Master SRS v3.1, FEAT-040, ADR-0015
- Executor: Claude; owner workstream: P3 / BE2; Codex review và điều phối kế hoạch
- Current branch: feature/be2-01-ai-job-foundation
- Current authorized implementation: BE2-01 Phase A revision 1 only
- Current slot: Q00 — nghiệm thu Phase A; code review PASS, còn gate adoption/Pillow
- Progress register: BE2_EXECUTION_TRACKER.md

## 1. Cách dùng và authority

Người dùng yêu cầu: “G hãy phân tích lại toàn bộ task cho BE2 này và sau đó làm 1 roadmap lộ trình làm và sẽ bám sát theo lộ trình đó để tránh phát sinh phình to task ra”.

Từ revision này, đây là **điểm vào duy nhất để chọn việc BE2 tiếp theo**. Tracker chỉ ghi tiến độ, blockers và việc đang làm; không tạo scope riêng. Nội dung task/requirements vẫn do FEAT-040 và SRS quản lý; implementation do plan + approval đúng owning feature quản lý. Roadmap không sửa scope Phase A đã duyệt, không duyệt Phase B/các card khác, không adopt stack/model/schema/numeric policy.

Các gợi ý “next step” trong tài liệu cũ chỉ còn giá trị tham khảo; chọn việc theo roadmap này. Bản revision 1 được giữ ở evidence/notes/BE2_ROADMAP_REV1_ARCHIVE_20261014.md. Không thêm lịch/ngày giao hàng/thời lượng.

**Giữ đúng 14 card BE2.** 01-A/01-B, library/generation và component/runtime là các checkpoint của card gốc, không là business task mới. R01–R11 là lỗi của Phase A, sửa tại chính Phase A. Không sinh thêm framework hoặc feature để “hỗ trợ” lỗi này.

## 2. Phân tích lại workstream

### 2.1 Phạm vi BE2

BE2 có năm nhóm công việc:

| Nhóm | Cards | Kết quả phải bàn giao |
|---|---|---|
| Job foundation | BE2-01 | Contract/job/attempt/status; durable jobs và outbox ở chặng riêng |
| AI assistance | BE2-02–06 | Snapshot/meaning → request → real Sketch derivative → exact Teacher review → Child response |
| Knowledge/video | BE2-07–10 | Sources/script → library/real generation → final review/playback → failure disposition |
| Activity/content | BE2-11/12 | Published content và scoped activity assignment/execution |
| Configuration/automation | BE2-13/14 | Pinned preset, bounded automation/override; versioned AI policy/limits/copy lifecycle |

Không đưa identity/class/session/canvas/portfolio/core privacy sang BE2. BE2 cung cấp projection/eligibility/command intents qua ports; không viết bảng của BE1. P4 ghép luồng, không làm thay job/provider adapters của BE2. FE giữ UI/player/device behavior.

### 2.2 Hiện trạng có evidence

- BE2-01 Phase A đã có code/approval, nhưng review NEEDS_REVISION: R01–R11 chưa có closure. Test hiện có 172 passed/1 skipped và runner 171 checks pass chỉ chứng minh những cases đã chạy.
- A-20 candidate cross-review/adoption và live-app route check thiếu Pillow còn pending.
- BE2-01 Phase B và BE2-02–14 chưa có approval trong feature này, chưa được đánh dấu implemented bởi representative fixtures.
- Legacy Vision/media/catalog có thể reuse theo audit; không chứng minh sản phẩm v3.1 hoặc new generation đã đạt.

Kết luận: việc đang làm là **hoàn thiện foundation đã duyệt**. Không bắt đầu thêm card runtime khi đang sửa R01–R11.

### 2.3 Điểm dễ phình cần chặn

| Điểm dễ phình | Ranh giới phải giữ |
|---|---|
| “Foundation cho tất cả AI” | Chỉ job lifecycle/contracts/ports phục vụ 14 card; representative schemas không kéo cả business logic vào 01 |
| “Có queue thì làm luôn infra” | 01-B chỉ durable AI jobs/receipts/outbox/queue adapter; core persistence BE1, deployment/composition P4 theo scope riêng |
| “Cần review nên viết workflow engine” | Exact-content schema dùng chung, purpose branches rõ; chỉ lifecycle trong card, không custom workflow builder |
| “Tạo Sketch cần SAM/rigging/animation” | Chỉ output/support modes/profile được adopt; SAM/animation không mandatory prerequisite |
| “Video cần cả TTS/scene library/cloud mới” | Chỉ strategy/profile được duyệt; TTS/narration/composition bổ sung nếu scope quyết định yêu cầu |
| “Knowledge cần RAG platform” | Claim-source map và bounded library/source ports; không crawler/vector DB/search framework tự phát |
| “Policy cần admin backend tổng quát” | AI allowlist/profile/limits/kill switch; core policy/account/privacy vẫn BE1 |
| “Test pass nên optimize/refactor thêm” | Đạt acceptance thì review/handoff; optimization chỉ khi có measured problem liên quan và scope riêng |

## 3. Hàng đợi mặc định — một card/chặng đang code

Đây là **thứ tự ưu tiên cho executor**, không thay dependency DAG và không thay phân công team. Thứ tự id không phải độ ưu tiên. Các checkpoint tích hợp nối khi output đủ; không chờ cả 14 card.

| Slot | Card/chặng | Kết quả của lượt | Gate để chuyển slot |
|---|---|---|---|
| Q00 | BE2-01 Phase A closure | Sửa R01–R11; A-01–A-20 + candidate handoff đúng phạm vi | Regression/repro closure + independent review; thiếu check/adoption ghi rõ, không giấu skip |
| Q01 | BE2-01 Phase B | Durable job repository/migrations/CAS/receipts/outbox/queue | Approved Phase B + persistence/queue ADR + actual restart/concurrency/fault evidence |
| Q02 | BE2-12 | Content lifecycle + sole CMD-48 dispatcher + DATA-33 | Exact publication/capabilities/recall tests; shared DATA-24 contract đúng owner |
| Q03 | BE2-14 | Versioned AI configuration/limits/kill switch/copy lifecycle | Policy/copy conformance; activation values/profile adopted trước live; hook obligations giữ rõ |
| Q04 | BE2-02 | Vision reuse và provenance correction | Snapshot/hash/uncertainty/correction/stale cases; real profile evidence khi activated |
| Q05 | BE2-03 | Request/cancel/dedup/cache/budget | Scope/turn/purpose + duplicate/conflict/bounded/cancel tests |
| Q06 | BE2-04 | Real Sketch derivative và worker/provider hooks | Actual selected-profile output/safety/quality/copy evidence; fake chưa full DONE |
| Q07 | BE2-05 | Moderation và per-Sketch Teacher review | Exact version/hash/audience; edit/revoke/stale và Child access denied trước gate |
| Q08 | BE2-06 | Child view/hide/decline | Exact authorized item/turn/response, idempotency, original hash bất biến |
| Q09 | BE2-07 | Grounded knowledge và script versions | Claims có nguồn, fantasy tách facts, edits invalidate downstream |
| Q10 | BE2-08 | Reviewed-library + actual video generation | Media/rights/scope + actual generation; unknown progress, bounded waiting; no placeholder success |
| Q11 | BE2-09 | Final session video review/playback | Exact approved artifact mới play; old bytes/audience/URL không bypass |
| Q12 | BE2-10 | Explicit Teacher retry/skip/end | All-three actions, exhausted guards, duplicate/race/BE1 receipts |
| Q13 | BE2-11 | Activity assignment/adaptation/execution | Published source, each-child compatibility/preparation/safety, outcome handoff |
| Q14 | BE2-13 | Preset/conditional automation/Teacher override | Config pinning, bounded adopted conditions, old intents stale sau override |

Mỗi slot có component và runtime checkpoints theo phần 4; chuyển sang **component** tiếp theo không được báo full card trước đã DONE. Runtime consumer không được dùng một prerequisite mới chỉ candidate như thể đã adopt.

### 3.1 Nếu Q01/real-model gate chưa sẵn sàng

Không giữ toàn workstream chờ quyết định xa; cũng không tự đổi thứ tự trong im lặng:

1. Ghi slot/chặng bị chặn, gate thiếu cụ thể, owner cần trả lời, remaining acceptance và checkpoint quay lại vào tracker. Thiếu approval là approval gate, thiếu môi trường là environment gate; không gom thành “khó nên hoãn”.
2. Q00 implementation corrections phải đóng trước. Cross-review/adoption còn thiếu chỉ cho phép downstream **candidate-only** work nếu plan của downstream ghi rõ mức này; không pretend registry accepted.
3. Nếu 01-B thiếu ADR/approval, có thể làm theo thứ tự **12-component → 14-component → 02-component → 03-component → 04-component** trong scope đã được duyệt, giữ durable/live remainder trong tracker. 04-component chỉ fake port/output admission, chưa real Sketch.
4. Nếu selected Sketch provider/model của 04-live chưa có decision, có thể chuyển sang **07 → 08-reviewed_library → 09-library → 10-component → 11**, sau khi ghi substitution và có approval đúng scope. Shared DATA-24 đủ cho video/publication; không cần 04/05 live.
5. Nếu video generation decision chưa sẵn, chỉ làm library/review/disposition đã nằm trong plan; 08-generate vẫn pending. Không dùng library-only/fake để kết luận full08 DONE.
6. Chỉ chọn **một** slot thay thế có dependencies sẵn. Trước lượt code tiếp theo, ghi ACTIVE slot mới; slot trước WAITING_GATE, không có hai implementation đang chạy. Scope người dùng đã duyệt cho thay thế không cần xin lại.
7. Khi gate quay lại, xử lý waiting slot ưu tiên cao nhất trong hàng đợi mặc định sau khi lượt đang làm đã review/handoff hoặc được park rõ. Không mất dấu việc real generation/durable đã hứa.

Các đường thay thế là phương án có kiểm soát, không tự cấp implementation approval. Ngoài các đường này, thay thứ tự/scope phải ghi change entry có quyết định owner. Việc hiện tại vẫn Q00.

### 3.2 Dependency DAG gốc phải giữ

| Card | Runtime nội bộ cần trước |
|---|---|
| BE2-01 | Không live dependency cho foundation; durable cần adopted external persistence/runtime decisions |
| BE2-02 | BE2-01 |
| BE2-03 | BE2-01, BE2-02 |
| BE2-04 | BE2-01, BE2-02, BE2-03 |
| BE2-05 | BE2-01, BE2-04 |
| BE2-06 | BE2-05 |
| BE2-07 | BE2-01 |
| BE2-08 | BE2-01, BE2-07 |
| BE2-09 | BE2-08 + DATA-24 schema fixtures |
| BE2-10 | BE2-01, BE2-08 |
| BE2-11 | BE2-01, BE2-12 |
| BE2-12 | BE2-01 + DATA-24 schema fixtures |
| BE2-13 | BE2-01, BE2-12 |
| BE2-14 | BE2-01, BE2-12 |

**Schema-only và implementation khác nhau:** DATA-24 do BE2-05 sở hữu, candidate có từ foundation; 12/09 không chờ real04/live05. ProviderCopyLifecycle do14 sở hữu, fake support từ01 và provider-specific hooks ở04/08. Chính sách fixture không đòi live14; real activation cần adopted policy. 07 nhận confirmed context từ02 **hoặc BE1/Teacher fixture**, không cần Vision mới để làm library video.

## 4. Phạm vi khóa của từng card

Các bullets sau là phân tích/bounded checklist từ card gốc. Không giảm nghĩa vụ CONFIRMED hoặc tự adopt PROPOSED/TBD. Plan của từng card phải triển khai đủ source acceptance tương ứng; nếu tách checkpoint, ghi phần còn lại.

### BE2-01 — Job foundation

- Deliver: Phase A job/attempt/state/disposition, DATA-25/CMD-44, scopes/receipts/ports/fakes, shape pack/runner. Phase B durable AI job repositories/migrations, attempt/request CAS, dispatch/completion receipts, outbox và queue adapter.
- Scope stop: không domain nghiệp vụ 02–14, platform orchestration chung, provider thật hoặc toàn core persistence. Shape fixtures không là implementation card khác.
- Exit A: R01–R11 đóng, A-01–A-20 evidence, consumer examples/version/owner, skipped checks/adoption remaining rõ. Exit B: actual migration/restart, broker-down/outbox replay, same-attempt redelivery, concurrent winner, revoke/cancel races.
- Decision gates: Phase B plan/approval + DB/queue/transaction/recovery/service-identity ADR, BE1 generic persistence port. A không chờ live service.

### BE2-02 — Vision/correction

- Deliver: DATA-22, CMD-34, Vision port/legacy adapter map; immutable snapshot/version/hash/topic/age/context; original inference riêng, author/reason/version của corrections riêng.
- Scope stop: không Sketch generation, segmentation/SAM/rigging, age/psychology/intelligence inference, model tuning project.
- Exit: valid/low-confidence/malformed/correction/conflict/stale fixtures; uncertainty nullable và không bịa. Nếu activate real profile, có measured quality/revision/profile/hash report của context mới.
- Gates: 01; H-CANVAS-SYNC/H-CLASS-CONSENT/H-IDENTITY contracts; real profile/model/license/budget decision.

### BE2-03 — Assistance request

- Deliver: DATA-21, CMD-32/33; target/group/region/current-turn/purpose/audience guards; semantic dedup/debounce/cache/budget scheduling; cancel/events.
- Scope stop: không session/canvas engine, UI, generic scheduling platform, automatic request suy từ idle.
- Exit: same semantic scope một job; changed payload conflict; wrong scope/consent/budget không provider; mixed-age mỗi member; cache/cancel/stale không bypass review.
- Gates: 01/02 và session/canvas/consent contracts; numeric rate/retry/budget policy adopt trước real activation.

### BE2-04 — Real Sketch

- Deliver: DATA-23, SketchGenerator/worker/fake + real selected adapter, separate derivative/overlay, output admission/provenance; known-copy lifecycle hooks.
- Scope stop: không sửa original strokes, attribution AI thành child contribution; không mandatory SAM/animation, thêm models/support modes chưa quyết định.
- Exit: actual generated asset/hash/decoding/safety/quality/profile từ synthetic input; original hash giữ nguyên; pending moderation/Teacher review; stale/unsafe/cancel/timeout không expose.
- Gates: 01/02/03; selected support taxonomy/output/profile/model/license/cost/quality/timeout policy và approval. Fake không đóng real requirement; provider purge còn Pending/Unsupported/Exception phải ghi thật.

### BE2-05 — Sketch review / shared exact review

- Deliver: DATA-24 primary schema/ExactContentReview port, CMD-35; moderation/queue/eligibility, exact item/version/hash/audience/context decisions; edit/version invalidation, safe projection cho BE1 access gateway.
- Scope stop: không media generator/player, alternate media route, Admin/preset approval thay Teacher; generic publication và session review giữ purposes riêng.
- Exit: approve/reject/request_changes, stale If-Match/conflict/revoke/edit; pending/rejected/unsafe/stale item không fetch/cache/ticket/exposure cho Child.
- Gates: runtime01/04 + teaching authority/adopted moderation policy. Shared schema từfoundation cung cấp cho12/09 độc lập realSketch.

### BE2-06 — Child agency

- Deliver: CMD-36; viewed/hidden/declined response đúng participant/turn/version, idempotency/attribution và Teacher event.
- Scope stop: không UI rendering, regeneration tự động, original edits hoặc tự chọn policy xem lại declined.
- Exit: view→hide/decline giữ original hash; revoked/duplicate/late response không mở quyền hoặc gọi model mới.
- Gates:05/current grant/turn contracts; refinements ngoài agreed action cần separate decision.

### BE2-07 — Knowledge/script

- Deliver: DATA-26, CMD-38/39; confirmed concept/context→reviewed sources; factual claim-source map; imagined story elements riêng; script/bundle versions/hash; correction/invalidation.
- Scope stop: không crawler/vector DB/RAG platform, self-verification bằng model, tự thêm mandatory pre-render approval/TTS.
- Exit: mỗi fact có source; missing source trả Teacher content action; edits invalidate downstream exact version; fantasy không science fact.
- Gates:01; confirmed meaning/context từ02 hoặc BE1/Teacher fixtures; bounded source/content policy.

### BE2-08 — Library + actual video

- Deliver: DATA-27, CMD-40; library resolver/generator/media validator/own worker/adapters; strategy contract reviewed_library/generate/compose_library, policy-selected implementations; immutable final artifact và provider-copy hooks.
- Scope stop: không player UI, tự cố định Wan/L4/video duration/cloud/narration; không auto-fallback/skip/play khi generating; không mở thêm render engines trước approved profile.
- Exit library: publication/usage rights/profile/encoding/audience/admission và exact session Teacher-review handoff. Exit generation: actual decodable video/hash/quality/cost/latency/profile, retry/cancel/stale và known-copy outcomes. Whole08 cần selected actual generation, không chỉ library.
- Gates:01/07; library không chờ generation-model decision. Generate hoặc provider-using compose cần model/license/cost/quality/deadline/retry approval/ADR và durable runtime gates liên quan.

### BE2-09 — Final video review/playback

- Deliver: CMD-41/42; shared DATA-24 session review, DATA-27 playback state; exact final bytes/script/audience/review version; access/play intent/receipt qua BE1 ports.
- Scope stop: không player frontend, bucket/provider/permanent URL, library publication thay Teacher approval trong phiên.
- Exit: exact approved version mới play; edited bytes/script/audience/context/revoke chặn old approval/URL; library video vẫn có per-session review.
- Gates:08 path tương ứng + shared DATA-24; session/access contracts. Không dependency realSketch/liveSketch-review.

### BE2-10 — Exhausted video disposition

- Deliver: DATA-28, CMD-43; Teacher retry/skip/end; prior failure history, bounded new run và versioned BE1 stage/end/checkpoint receipts, compensation/idempotency.
- Scope stop: không session DB write, generic terminal reset, automatic skip/end hoặc silent “success”.
- Exit: cả ba action + duplicate/race/failed remote receipt; running→VIDEO_NOT_EXHAUSTED; skip không generated; end đòi checkpoint receipt; retry không bypass unsafe/review/budget.
- Gates:01/08; adopted retry/budget + session command/atomicity integration decision. Fixtures không thay durable end receipt.

### BE2-11 — Activity

- Deliver: DATA-29, CMD-45; published catalog/recommendation candidate, Teacher select/adapt local assignment, immutable objective/source refs; confirm_ready/start/finish/skip/interrupt; outcome handoff.
- Scope stop: không portfolio/observation engine CMD-46/47; không mở rộng catalog vô hạn, silent master edits hoặc hard discovery filters chưa adopt.
- Exit: catalog parity + từng trẻ compatibility/safety/preparation/material/prerequisite theo adopted policy; hazardous/unprepared không start; assignment edits giữ provenance; no fabricated Teacher observation.
- Gates:01/12 + pedagogical/publication/safety policy và BE1 session/result ports. Existing ranking/no-readiness-filter rules chỉ là candidate, không tự thành target mới.

### BE2-12 — Content publication

- Deliver: DATA-33 shared envelope; **sole CMD-48 closed dispatcher**; content draft/edit/submit/review/changes/publish/recall/archive, exact safety/pedagogical reviews và author/reviewer/publisher capabilities.
- Scope stop: không preset/AI policy/core policy logic thay owner; dispatcher gọi typed delegated ports. Không biến generic content thành fake child/session record hoặc invent active-copy deletion policy.
- Exit: exact reviewed version mới publish; author không self-publish; edit invalidate approvals; recall chặn new-session resolution; source/history/audit giữ riêng.
- Gates:01/shared DATA-24; adopted publication/reviewer/recall policy, lifecycle scope liên quan. Core non-AI branch delegate BE1-15; schema-only không chờ05 live.

### BE2-13 — Preset/automation

- Deliver: preset typed branch qua CMD-48, pinned snapshots/config hash; conditional evaluator/scheduler cho fields/conditions đã adopt; scoped intents/receipts; Teacher override qua BE1 session port.
- Scope stop: không workflow builder/rule engine vô hạn, session state engine thứ hai, autoapprove/autocomplete/purge hay mutable library affecting active sessions.
- Exit: library edit không đổi active session; override/disable làm queued old-version actions stale; receipts/dedup/race/priority behavior đúng adopted policy.
- Gates:01/12; H-SESSION-CONTROL; preset condition/priority/override decisions. Không tự invent rules để đủ demo.

### BE2-14 — AI configuration/lifecycle

- Deliver: AI typed branch qua CMD-48; allowlisted policy/model-profile refs, version pinning/limits/kill switch và redacted projections; ProviderCopyLifecycle primary registry/discovery/cancel/purge/verify/idempotency.
- Scope stop: không secrets vào DTO/log/mobile, cloud/package upgrade, BE1 lifecycle authority/core storage purge; Admin không thay teaching approval hoặc tự có raw-child access.
- Exit component: new requests pin new version, prior provenance giữ riêng; current eligibility/disable chặn new/inflight publication; exact per-copy receipt semantics/concurrent replay/no-resurrection. Exit real: provider-specific hooks của04/08 có actual verified receipt hoặc explicit Pending/Unsupported/Exception; không fake actual Deleted.
- Gates:01/12, Admin capability; profile/runtime/config values adopted trước activation; BE1 scoped lifecycle authority. Contract completion không đòi invent provider capability; genuine unsupported outcomes là explicit exception, không báo purge complete.

## 5. Exit, scope change và cách giao Claude

### 5.1 Ba mức kết quả, không nhập làm một

| Mức | Đủ evidence gì | Chưa được claim |
|---|---|---|
| Component accepted | Plan/approval đúng scope; domain/contracts/adapters fakes và negative tests; applicable checks + independent review; contract pack/handoff | Durable restart, actual model quality/purge, integrated classroom |
| Runtime accepted | Adopted contracts/policies/runtime decisions; actual adapter/migration/restart/provider evidence theo card; review | UI/device/full pilot hoặc cross-module E2E chưa chạy |
| Integration accepted | P4 nối luồng cùng owners; current auth/review/consent/cancel/recall/fault chain có actual combined receipts | Production/legal compliance/load vượt measured profile |

Full card DONE chỉ khi **nghĩa vụ source của card** và acceptance/architecture/evidence/review trong approved plan đều được đáp ứng; dùng plan chỉ-cover-fixtures không được silently loại full-card obligations. P4 integration có owner riêng, không biến toàn system E2E thành exit của mỗi component độc lập. Nếu UI/integration còn pending, tracker ghi rõ mà không tự nói product ready.

Skipped required check là NOT_RUN và có owner/command/reason. Muốn chấp nhận checkpoint với deviation cần quyết định đúng scope ghi lại; không đổi skip thành PASS. Policy/schema chưa adopt giữ candidate dù tests pass.

### 5.2 Quy tắc không làm task phình

1. **Một card/chặng đang code.** Trước mỗi lượt ghi ACTIVE slot, approved feature/plan revision và exact outputs; những card khác chỉ review/documentation liên quan hoặc WAITING_GATE.
2. **Scope trước code:** write allowed behavior/output/module areas, exclusions, source mapping, acceptance và dependencies. Không dùng prompt “làm luôn cả BE2”.
3. **Sửa lỗi tại card:** lỗi vi phạm accepted source/criteria là correction cùng scope; không tạo business task mới để che lỗi. Re-review tập trung repro/acceptance affected; phát hiện mới phải concrete/reproducible, không sở thích refactor.
4. **Việc “hay hơn/tiện sau này” đưa Later:** record riêng, không code trong task hiện tại; không blanket “cleanup backend” hoặc thêm abstraction chưa có caller trong acceptance.
5. **Scope mới cần change entry:** FR/UC/DATA/CMD affected, owner, lý do, compatibility/privacy/dependency impact, acceptance delta; owner quyết định + new approval nếu scope/architecture thay đổi rồi mới làm. Không sửa source để hợp thức hóa code đã mở rộng.
6. **Còn TBD thì fixture hoặc bounded decision:** dùng named candidate policy; chỉ nghiên cứu quyết định đang chặn slot. Không benchmark/model shopping/provider migration vô hạn trong một card.
7. **Giữ registry owner:** 14 primary CMD và 10 primary DATA bên dưới. New endpoints/entities/model/support mode/media strategy là scope change; child/adult projections/helpers trực tiếp cần cho current schema không là business card mới.
8. **Đạt gate thì đóng checkpoint:** evidence/review/handoff xong thì chọn slot tiếp; không thêm optimization/polish tự phát. Không chạy rộng/repeat tests khi không có change/failure/unresolved concern.
9. **Blocker không mở nhiều task:** explicit waiting gate + một substitution được ghi nhận; giữ return checkpoint/remaining obligations.
10. **Code executor vẫn Claude:** Codex plan/review; không tự làm thay backend hoặc tự gửi lệnh thực thi/provider/cloud khi user chưa yêu cầu.

### 5.3 Prompt dispatch dùng cho mọi slot

Chỉ điền một slot có approval hợp lệ; không xem template là approval:

> Claude đọc BE2_ROADMAP.md revision 2 và BE2_EXECUTION_TRACKER.md. Lượt này chỉ làm [slot/card/checkpoint], owning feature [path], approved plan [revision/scope]. Deliver [exact outputs], acceptance [IDs], exclude [list]. Preserve unrelated changes. Nếu không có approval đúng scope, chuẩn bị reviewable plan; không code. Nếu đã có approval, tiếp tục tự chủ trong phạm vi đó. Không kéo card khác/framework/provider/profile mới vào task. Việc phát sinh ghi tracker/change entry và tiếp tục phần độc lập đã authorized. Kết thúc bằng actual commands/results, remaining acceptance, candidate/runtime/integration levels và handoff. Chưa tự mark full card DONE hoặc next card approved.

Các prompt sửa Q00 được giữ làm lịch sử; code review cuối đã đóng các findings. Việc hiện tại là acceptance gates theo tracker, không dispatch lại prompt sửa cũ. Những prompt trước có wording “next step” phải resolve qua active tracker; Phase A approval không đổi.

## 6. Handoffs, decisions và integration

### 6.1 Primary contract ownership giữ nguyên

| Card | Primary CMD | Primary DATA |
|---|---|---|
| BE2-01 | CMD-44 | DATA-25 |
| BE2-02 | CMD-34 | DATA-22 |
| BE2-03 | CMD-32, CMD-33 | DATA-21 |
| BE2-04 | Internal worker port; no new public route | DATA-23 |
| BE2-05 | CMD-35 | DATA-24 |
| BE2-06 | CMD-36 | Shared DATA-23/24 |
| BE2-07 | CMD-38, CMD-39 | DATA-26 |
| BE2-08 | CMD-40 | DATA-27 |
| BE2-09 | CMD-41, CMD-42 | Shared DATA-24/27 |
| BE2-10 | CMD-43 | DATA-28 |
| BE2-11 | CMD-45 | DATA-29 |
| BE2-12 | CMD-48 sole dispatcher | DATA-33 |
| BE2-13 | Typed preset delegate via CMD-48 | Shared DATA-33 |
| BE2-14 | Typed AI-policy delegate via CMD-48 | Shared DATA-33 |

CMD-59/60 và DATA-20/35 primary ở BE1. CMD-48 non-AI organization/purpose/retention branch delegates BE1-15. DATA-34 lifecycle authority/core purge ở BE1; provider-copy semantics/registry ở BE2-14, specific adapters04/08, fake support01. Không direct cross-module DB integration.

Inputs: H-IDENTITY, H-CLASS-CONSENT, H-SESSION-CONTROL, H-CANVAS-SYNC, H-GALLERY khi cần, generic artifact/audit/lifecycle ports. Outputs: H-AI-REVIEW, H-KNOWLEDGE-VIDEO, H-ACTIVITY, H-CONTENT-PRESET, AI H-ADMIN-POLICY, H-OPERATIONS, provider-copy H-DATA-REQUEST. Pack tối thiểu version/schema/owner, synthetic fixtures/hash/errors/example, conformance/report/remaining gates.

### 6.2 Decision gates theo nơi giải quyết

| Gate | Trước phần nào | Phần cần chốt; không đưa vào task khác |
|---|---|---|
| Persistence/queue/transaction/service identity | 01-B + live job wiring | ADR và BE1 generic ports; P3 AI adapters, P4 composition |
| Contract/error/role projections | Runtime route adoption | DATA/B22 versioning, owner review; source guards không chỉ UI |
| Publication/recall/reviewer policy | 12 runtime + library use | Exact review/publisher capabilities, source rights và recall behavior |
| AI profiles/limits/moderation/retry | Live02/04/08, policy14 activation | Selected profile/license/support modes/quality/cost/deadline + candidate measurements |
| Video library/media encoding/audience | 08 library/09 | Không cần generation model decision cho library; session review vẫn mandatory |
| Activity/automation policies | 11/13 runtime | Age/preparation/safety và bounded preset fields/conditions/override |
| Provider-copy/data lifecycle | 14/04/08 real hooks | Scoped authority, known copy discovery, verified receipts hoặc outstanding exception; BE1 lifecycle owns request |

Windows chỉ code/lightweight checks và existing environment; không cài model/GPU dependencies. Model/integration measurements theo separate Sketch2Life LightningAI environment và approval; không sửa Wan2.2 env. Synthetic-only; Firebase Authentication-only; originals/provenance và current auth/consent/review vẫn bắt buộc.

### 6.3 Integration checkpoints không là card BE2 mới

- Assistance ready → P4 INTG-05 với FE/BE1, đúng snapshot/request/Sketch/review/Child chain.
- Knowledge/video ready → INTG-06 độc lập Sketch; generation/library/review/play/failure states đúng.
- Activity ready → INTG-07; BE1 reflection/observation/portfolio/finish, không BE2 tự làm thay.
- Policy/recall/copy/durable operations → INTG-08/10; pilot/load/device/model evidence phối hợp INTG-11 theo approved profiles.
- Các owners sửa component defects của mình. Không thêm deployment/pilot targets hoặc toàn E2E backend vào scope một card để “xong luôn”.

## 7. Trạng thái và việc tiếp theo

**Đang làm: Q00 BE2-01 Phase A acceptance gates.** Code review cuối PASS: R01–R11 và R03a/R04a/A18a đã đóng. Còn consumer adoption và test live-app cần Pillow hoặc checkpoint deviation được ghi nhận. Giữ original approved Phase A revision1; không có runtime code/approval nào được thay bởi cập nhật review/routing này.

Sau closure chọn Q01 nếu decisions/approval đủ; nếu chưa, ghi rõ candidate-only substitution theo 3.1. Lượt tiếp theo sẽ bám ACTIVE slot trong tracker; việc phát sinh ngoài card không tự thêm vào implementation.

Evidence của lần lập roadmap: evidence/notes/BE2_ROADMAP_REV2_VALIDATION_20261014.md. Source requirements và task counts không đổi.
