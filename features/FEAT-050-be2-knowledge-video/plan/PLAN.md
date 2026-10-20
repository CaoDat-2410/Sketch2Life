# BE2-08 — Library resolution và pipeline video generation thật

- Status: AWAITING_APPROVAL
- Plan revision: 1
- Implementation status: NOT_STARTED
- Date: 2026-10-18, Asia/Saigon
- Branch: feature/be2-08-14
- Planning baseline: be64b99
- Owner: receiver BE2-08–14; BE2-07 vẫn thuộc sender BE2-01–07.

## 1. Goal và nguồn

Implement CMD-40 và DATA-27: nhận exact knowledge bundle, chọn strategy được
phép, tạo run/job, resolve hoặc generate media, validate immutable final artifact
và đưa vào ready_for_review. Đây không phải playback hoặc Teacher approval.

Nguồn yêu cầu: canonical SRS v3.1 tại FEAT-029 artifacts/Sketch2Life_Master_SRS.md,
FR034/037/038/040, UC-023/025, DATA-25/26/27/shared20, CMD-40, FIX-UX-05,
AT-CS-011; FEAT-040 TEAM_TASK_BREAKDOWN card BE2-08; FEAT-044
BE2_08_14_TEAMMATE_HANDOFF.md và BE2_ROADMAP.md; ADR-0015/0018;
FEAT-048 publication và FEAT-049 current policy/provider-copy handoffs.
Các nguồn này không tự cấp approval implementation hoặc provider activation.

Checkout baseline có DATA-26/27 ShapeSpec candidate; chưa thấy dedicated BE2-07
service/port implementation khi rà backend source. Không tuyên bố upstream đã
ready. Legacy story/whiteboard pipelines và Wan scripts không phải BE2-08 đã đạt.
BE2-12/14 component/owned SQL evidence không tính thành BE2-08 PASS.

## 2. Scope và boundaries

- Pure domain; strict versioned DTOs; application ports/services; own repository,
  forward migrations; CMD-40 thin HTTP adapter; foundation worker integration
  adapter; provider adapter boundary; deterministic fixtures và evidence runners.
- Strategy union giữ reviewed_library/generate/compose_library. Không silent
  fallback giữa strategies. Strategy chưa có adopted implementation trả explicit
  unsupported/not-configured, không giả thành video generated.
- Consume BE2-01 job/UoW/attempt/cancellation/outbox contracts, không direct-write
  foundation hoặc BE1 tables, không sửa ngược published migration/shared schema.
- BE2-07 bundle/current eligibility và BE1 identity/consent/session/artifact authority
  qua typed ports. Fixture bindings nhãn ASSUMED_CONTRACT, không runtime-ready.
- BE2-09 owns exact final Teacher review/playback; BE2-10 owns exhausted retry/
  skip/end. Card này không implement thay hoặc tự advance stage/play/skip.
- BE2-14 owns ProviderCopyLifecycle registry/verification. Card này owns video/
  optional media-provider-specific hooks và inventory production khi profile được
  chọn. Không coi hook fixture là actual deletion.
- Real BE1/P4 composition để đồng đội nối theo owner; giao wiring examples,
  conformance fixtures và open-contract list, không tự nhận integration sign-off.

## 3. P1 — Contract, eligibility và run domain

1. Lập dependency inventory/CR cho exact bundle snapshot/current eligibility,
   session/audience authority, artifact storage và foundation interfaces. DATA-26
   candidate thiếu semantics nào thì ghi candidate addition/owner decision;
   không tự publish contract thay sender.
2. Strict CMD-40 input theo DATA-27: exact bundle id/version/hash, audience revision,
   strategy; conditional library/profile refs; extra/secret/endpoint fields rejected.
3. Server-derived principal/org/session scope; immutable request pin gồm source,
   bundle/editorial/context/audience, policy/profile/rights/encoding refs. Hash
   canonicalization có test vectors, không tin hash client mà không resolve bytes.
4. Tách video content version, run revision, review revision, generation/review/
   playback axes. Generated/library media ban đầu chỉ pending exact-session review;
   approval generic library không cấp playback.
5. Scoped semantic dedup và idempotency: duplicate compatible một run/job;
   conflicting body/key bị reject, replay vẫn check current authority/eligibility.

## 4. P2 — Orchestration, own persistence và CMD-40

1. Implement LibraryResolver, VideoGenerator, MediaValidator, bundle/current-owner,
   storage/finalization ports và use cases; boundaries versioned, fail closed nếu
   thiếu adopted definitions hoặc current authority.
2. reviewed_library kiểm publication/recall, usage rights, exact source/profile/
   encoding/audience; không cần generation model decision nhưng vẫn cần final
   session review. generate/compose chỉ dispatch với approved profile/rights/gates.
3. Own SQL repository/CAS/forward migration cho run, immutable source/artifact
   lineage và idempotency/outbox nếu cần. Atomic run/job submission phải dùng
   compatible foundation UoW bridge; không giả atomic bằng hai commit nối tiếp.
   Nếu chưa có bridge, ghi CR và giữ durable submission gated; fixture không
   được dùng làm bằng chứng actual atomicity.
4. POST /knowledge-videos trả 202 run/job projection, không raw storage/provider
   URL, secret, prompt/child data. HTTP tests dùng explicitly composed fixture app;
   production routes chỉ wired khi adopted identity/session bindings có thật.

## 5. P3 — Worker, finalization và provider-copy hooks

1. Adapter consume BE2-01 attempt capability/lease/retry/cancel/restart, progress
   có nguồn; unknown vẫn unknown, không bịa percent hoặc tự reset terminal job.
2. External provider work ngoài DB transaction; stable original request/attempt/
   operation keys, exact original profile, explicit timeout/ambiguous outcomes.
   Completion giữ current owner/source/consent/audience/policy fences đến commit;
   stale/revoked/cancelled/expired result không expose hoặc resurrect artifact.
3. MediaValidator kiểm actual bytes/hash, container/codec/decode, dimensions/
   duration và profile constraints. Không tin MIME/extension hoặc provider success
   đơn thuần. Preserve originals, derived output có immutable provenance.
4. Copy hooks cover input/script/output/cache/job copies mà selected provider
   thực sự tạo. Scoped inventory, cancel/purge idempotency, receipts/source proof;
   unsupported/ongoing/unknown trả Unsupported/Pending/Exception, không Deleted giả.
5. Respect BE2-14 original policy-generation stop fence. Broad cancellation không
   thay generation-safe notice; contract gap ghi CR và không bật unsafe delivery.

## 6. P4 — Consolidated local verification và handoff

1. Một local runner source-pinned gom unit/contract/application/HTTP/adapter
   fixtures, regression của BE2-01/12/14, Ruff/Mypy, architecture/harness/security.
   Kiểm source trước/sau, ghi exit/status rõ và không biến skipped thành PASS.
2. Own PostgreSQL integration suite: migration/rollback, CAS/dedup races, run/job
   atomicity khi bridge adopted, immutable finalization và stale/late completion.
   Chuẩn bị runner không tự provision DB; chạy trên isolated test DB sau approval
   môi trường riêng, không dùng quyền provisioning cũ của BE2-14 cho card này.
3. Decoder fixture pack có media synthetic/rights record, positive/corrupt/wrong
   codec/hash/duration/dimensions; adapter thực dùng executable/runtime explicit.
   Nếu runtime thiếu thì báo NOT_RUN, không tự cài dependency.
4. Bàn giao payload/error examples, owner matrix, unresolved CR, one-batch runtime
   instructions, acceptance audit và honest component-vs-integrated status.

## 7. P5 — Actual generation gate / Lightning batch

Không approval ngầm provider/model/license/encoding/duration/TTS/GPU/budget/timeout/
retry hoặc stack từ lịch sử. Không mặc định Wan, L4, 35–40s hay narration.

Trước runtime: inventory chỉ read-only; trình một decision sheet với exact model/
provider revision, license/rights, profile/encoding/duration, machine/VRAM/disk,
approved dependencies và quota/timeout/retry. Nếu dùng TTS thêm decision/rights và
copy inventory. Owner duyệt sheet và provisioning/test budget riêng trước tải
weights/cài packages/start GPU/provider calls. Plan revision1 chỉ duyệt chuẩn bị
P5, chưa duyệt các giá trị còn thiếu hoặc actual render.

Batch sau gate gồm actual generation video decode được, source/profile/hash,
latency/cost hoặc explicit unknown, peak memory nếu đo được; success/error/cancel/
restart/late-completion cases theo adopted runtime; actual per-copy lifecycle
receipts hoặc outstanding statuses. Sanitize evidence, không real child data.
Library pass hoặc fake generator pass không hoàn tất nghĩa vụ generation thật.

## 8. Acceptance criteria

| ID | Điều kiện |
|---|---|
| A1 | Strict request, scope/current permissions, exact resolved bundle/source/audience/profile; stale/unsafe/recalled/unauthorized rejected |
| A2 | Compatible duplicate một run/job; conflicting duplicate rejected; race/CAS và failure rollback chứng minh không orphan/partial submission |
| A3 | Valid reviewed-library path giữ rights/provenance và pending final-session review, không playback URL/auto stage advance |
| A4 | Actual selected generation path tạo bytes decode được, validated profile/hash/lineage; fixture/placeholder không được coi generated |
| A5 | Cancel/revoke/expiry/kill/stale/restart/timeout không expose late result, không tự fallback/skip/approve; progress truthful |
| A6 | Provider copy inventory/hooks exact scoped, dedup/receipt verification hoặc outstanding reason; không giả actual purge |
| A7 | Local suites, actual owned SQL và chosen runtime evidence tách biệt, reproducible, source-pinned; unknown/NOT_RUN/assumed ghi rõ |
| A8 | BE1/P4/07 dependency contracts và CR bàn giao; full DONE chỉ khi required adopted integrations/reviews và A1–A7 đủ evidence |

Component handoff có thể đạt trước A4/runtime và external adoption, nhưng status
toàn card vẫn IN_PROGRESS. Không dùng owner deferral làm waiver full acceptance.

## 9. Commit / review / execution order

Đề xuất các checkpoint có thể review độc lập: C0 plan; C1 P1 contracts/domain;
C2 P2 service/storage/HTTP; C3 P3 worker/finalization/hooks; C4 P4 consolidated
tests/handoff; C5 P5 actual runtime evidence sau gate riêng. Một phase có thể cần
nhiều focused fix/test commits; không mỗi function một commit và không gom cả card
thành một commit khổng lồ. Security/diff checks trước mỗi checkpoint commit.
Không push/merge/deploy. Sau approval revision1 mới implement P1–P4/prepare P5;
nếu scope/shared contracts/architecture đổi đáng kể phải revise và xin duyệt lại.

## 10. Risks / mitigations

- Upstream07 và owner adapters chưa adopted: typed fixtures + CR; không tự làm07.
- Atomic foundation bridge/cancellation generation thiếu: fail closed, owner CR,
  không sửa foundation contract/migration ngầm.
- Provider activation/VRAM/dependency unknown: decision sheet trước actual batch,
  không lặp cài từng dependency hoặc retry runtime không giới hạn.
- Legacy video code có thể không cùng consent/provenance semantics: chỉ reuse
  sau compatibility review và tests, không route legacy bypass current gates.
- Decoder success không chứng minh nội dung đúng/đẹp: actual quality review riêng,
  không tuyên bố Teacher approval từ automated validation.

Implementation blocked until exact revision1 approval recorded separately.
