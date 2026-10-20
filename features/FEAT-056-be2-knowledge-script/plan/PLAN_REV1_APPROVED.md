# BE2-07 — Knowledge có nguồn và script versioning, offline

- Status: DRAFT / READY_FOR_OWNER_PLAN_APPROVAL
- Plan revision: 1
- Implementation status: NOT_STARTED
- Checkpoint: KNOWLEDGE_SCRIPT_COMPONENT_OFFLINE
- Owner feature: FEAT-056-be2-knowledge-script
- Branch: feature/be2-07-knowledge-script
- Base: 23acf9e83e181305edfeb345be9a8e7eb9dbef88, nhánh gộp sau merge PR15.
- Approval: AWAITING_PLAN_APPROVAL; chưa code, stage, commit hay push.

## 1. Mục tiêu và authority

Phần component offline cuối của lane01–07: Teacher tạo knowledge bundle từ topic/meaning
đã xác nhận; factual claims có nguồn reviewed; tưởng tượng tách riêng; script/correction
có version bất biến; downstream cũ mất eligibility khi nội dung đổi. Card vẫn NOT_DONE
cho đến runtime/integration. Yêu cầu nguyên văn nằm trong approvals/TASK_APPROVAL.md.

Hướng offline trước, gom campaign Lightning01–07 sau đã được user yêu cầu. Các lựa chọn
contract/readiness mới ở §11 đang được đề xuất để duyệt cùng plan, chưa là implementation
approval. Một task một nhánh; không merge/cherry-pick lại01–06. FEAT056 được cấp hành chính
sau fetch/48ref inventory, không phải nguyên văn user chọn056 hay teammate confirmation.

## 2. Nguồn và disposition draft cũ

- FEAT040 artifacts/TEAM_TASK_BREAKDOWN.md:582–592 và FEAT044 plan/BE2_ROADMAP.md:191–196:
  DATA26/CMD38/39, reviewed sources, corrections/invalidation; không crawler/RAG/self-verification.
- FEAT039 artifacts/Collaborative_Learning_SRS_v3.1.md: UC023, DATA26, B22.1, CMD38/39.
- contracts/schemas/ai_contract_candidates.py: DATA26 ShapeSpec không reject extra fields;
  shape conformance không phải adoption của SRS/consumer.
- application/services/vision_analysis.py: DownstreamMeaning241–251 thiếu scope/contributor;
  downstream_meaning828–850 kiểm current applicability, analysis_record là read riêng.
- FEAT055 evidence/notes/BE206_DEFERRED_RUNTIME_BATCH_20261019.md: runtime01–06/A17 profile.
- Draft cũ FEAT050 evidence/local/be207-preparation, SHA256
  e64d25b713fdc8c2208958024852ec84637c7c2b69475119ddfbcce3146ee7ea, giữ nguyên byte.
- Consumer08 đọc tại origin/feature/be2-08-14 sau fetch:
  2d5d9256bcbdb8c2465d720ab989a94fbb8ab6e7. Đây là pin lúc audit, không remote tip vĩnh viễn.

| Review cũ | Thiết kế successor | Acceptance dự kiến |
|---|---|---|
| KB-PR01 P2: arbitrary fact text gắn claim_ref hợp lệ | Fact text derive từ claims; sửa câu factual ở claim-level có source/attestation | N01/P04/C03 |
| Q1: historical/current basis | Recheck exact basis revision/confirmation/applicability lúc command và resolve | N04/R02 |
| Q2: thiếu trusted scope/contributors | Enriched KnowledgeBasisV1 fixture; real Vision/BE1 adapter là gate riêng | N05/C04 |
| Q3: mutable guards trước commit | Shared fake coordinator/UoW và generation guard cho nested commit | R01–R07 |

Đây là disposition thiết kế, chưa có test07 nào chạy.

## 3. Scope và exclusions

Own pure domain, strict DTO, ports, synchronous service CMD38/39, in-memory store, source/
basis/audience/policy/Teacher/disclosure fixtures, current exact resolver/export, immutable
receipts/corrections/atomic invalidation intents, producer examples và unit/contract/race tests.

Không job/model cho bounded catalog lookup, HTTP route, SQL/migration/Redis, UI, TTS/video,
crawler/vector DB/RAG, nguồn thật/download hoặc dependency install. Không sửa source01–06
hay08–14. Không mandatory pre-render approval; final exact-video approval thuộc08/09.
Fixture pass không chứng minh real source quality, role-owner concurrence hoặc production adoption.

## 4. Domain và provenance

### 4.1 Versions/hash

BundleHead có bundle_id, org/session, current_version, editorial_revision; version là immutable.
Create v1/revision1; edit có thay đổi thực tăng cả hai đúng1, correction reason/principal/ref
và cumulative correction refs. No-op trả NO_CONTENT_CHANGE, không CAS/version/receipt/event mới.
Editorial state chỉ phát draft; readiness độc lập editorial state và không là approval.

Canonical document chứa rules/contract version, bundle identity/version, scope/basis/source/
audience pins, sticky origin/contributors, claims, structured script/flat projection, correction
refs và policy refs. Không đưa bundle_hash tự tham chiếu hoặc mutable current eligibility/token
vào document. Content metadata/timestamps nếu hash phải được đóng băng trong version.

NFC strings, JSON native types, sort keys, compact UTF8; reject floats/nonfinite/unsupported
types/key trùng sau NFC. Arrays giữ thứ tự; tập exact refs có canonical sort/uniqueness rõ.
Dùng strict_canonical_sha256 hiện có ở domain/vision_context.py, không sửa foundation.
Lưu canonical bytes/SHA256, kiểm lại khi export. Bundle hash khác namespace VideoPin.digest08.

Helper hiện tại normalize string values nhưng không normalize object keys hoặc phát hiện
NFC-key collision. Own07 canonical builder phải normalize cả keys/values, reject key collision
trước khi gọi helper, rồi serialize sorted/compact UTF8 và kiểm SHA256 của bytes bằng helper
result. Decode request JSON có duplicate raw keys phải reject tại boundary; typed DTO không
được tự claim phát hiện duplicate keys đã mất khi upstream parser tạo dict. HTTP chưa có nên
wire-parser conformance là gate; own canonical vectors vẫn kiểm NFC-key collision trực tiếp.

### 4.2 Trusted basis và scope

Create nhận refs, không nhận actor/org/topic text/contributor identity từ client:

- teacher_topic: exact ref/revision từ scoped Teacher authority fixture, generic.
- confirmed_meaning: exact analysis revision/confirmation từ trusted KnowledgeBasisV1 fixture;
  có org/session/source snapshot refs, exact contributors và approved imagined selections.
- AudienceContextV1 giữ record ref, context_revision và audience_revision riêng; roster/age
  bands/provenance có nguồn, kiểm từng participant, không lấy tuổi trung bình.

Server derive content_origin. Có child-derived basis/imagined input thì origin child_derived;
xóa imagined sau đó không xóa contributor provenance hoặc downgrade thành generic.
Generic Teacher topic không gọi child consent hoặc bịa child IDs. Child-derived kiểm từng
contributor đúng purpose/membership/scope. knowledge_media và các age/source limits là named
fixture policies, chưa adopt production taxonomy.

Fixture enriched không giả là real02 adapter: DownstreamMeaning không cung cấp đủ scope.
Real path cần authorized public reads + trusted coherent enriched pin dưới owning boundary,
được review riêng; không suy contributor từ Teacher principal/client hay đọc private producer DB.

### 4.3 Sources, claims và script — đóng KB-PR01

ReviewedSourceV1: id/revision/hash/title/fixture locator/review date/age bands/state/recall.
ReviewedClaimV1: exact source ref, claim id/revision/text. Source phải reviewed, current exact
revision/hash/topic, không recalled và đúng audience policy. Bundle claims có exact source
id/revision/hash và verification_state catalog_reviewed hoặc teacher_attested.

- catalog_reviewed: text khớp exact reviewed catalog claim.
- teacher_attested: Teacher sửa câu tại claim-level, chọn reviewed source, server ghi author,
  correction/reason. Đây là accountable attestation, không semantic machine verification.
  Gói OD03 đề xuất chúng ready theo named fixture policy; phương án chặt hơn ở §11.

FactSection command chỉ có section_id + ordered unique claim_refs, không arbitrary text.
Server derive text bằng nối chính xác claim.text theo separator đã version hóa. Response có
text phải validate bằng projection đó. Câu khác gắn claim_ref cũ bị reject; sửa câu phải sửa
claim/source/attestation rõ. Không chỉ kiểm claim_ref tồn tại rồi coi fact text có nguồn.

StorySection có refs tới trusted imagined elements cùng version, text derive từ chúng;
không claim_refs hoặc unrestricted factual prose ẩn sau nhãn story. Imagined không được
promote thành catalog fact. Literal NFC/casefold leakage vào facts bị chặn; không claim
phát hiện mọi paraphrase hay chứng minh sự thật. Final video/content review vẫn là gate.

### 4.4 Readiness/current eligibility

generation_ready cần >=1 sourced claim và >=1 fact section hợp lệ; mọi exact source/basis/
audience/policy còn current. Missing-source create vẫn tạo draft0claims, needs_content_action
với NO_ELIGIBLE_SOURCE; không provider call hoặc fake approval. Edit explicit source sai/recalled
bị reject nguyên khối. Historical readiness trong version không thay current eligibility.

resolve_exact recheck basis ref/revision/confirmation/applicability, source revision/hash/
recall, policy/audience, purpose/membership và exact version/hash. Superseded, revoked/not
applicable hoặc đổi pin thì withhold script/export, trả reason/action an toàn. Read không ghi
version hoặc silently re-pin nội dung. Edit không đổi basis/audience pin; tạo bundle mới nếu cần.

## 5. Candidate DTO/command và replay

Own version0.1-candidate, strict extra=forbid/literals/bounds; không sửa DATA24/V2/ShapeSpec01.

| Contract | Fields chính |
|---|---|
| CreateKnowledgeBundleV1 | session_id, basis_ref union, expected_context_revision, expected_audience_revision, bounded catalog_claim_ids/imagined_refs |
| EditKnowledgeBundleV1 | expected_context_revision, expected_audience_revision, correction_reason; optional claim edits/structured sections/imagined refs, >=1change |
| KnowledgeBundleRecordV1 | DATA26 required fields + exact sources/provenance, bundle_hash, sticky origin, readiness/policy refs |
| KnowledgeBundleExportV1 | exact bundle id/version/hash + canonical bytes identity, structured/flat script, separate editorial/context/audience revisions, exact source/basis refs, current decision |
| KnowledgeSupersededV1 | stable event_id, org/session, exact old/new bundle refs/hashes, correction_ref, causal operation_id |

OpaqueIDs; context revision>=0, content/editorial revisions>=1. Fixture bounds claims24,
sources12, sections32, imagined8, claim text400, audience32; scalar/body lengths finite and
consistent across DTO/domain. Các số là fixture settings, không production policy.

Named fixture limits bổ sung: opaque id120, topic/title/locator/reason200 Unicode characters,
imagined element200, total projected script16000 characters và canonical/request-document
196608 UTF8 bytes. Fact projection hoặc correction-history document vượt giới hạn thì reject
nguyên khối, không truncate hoặc xóa provenance. Named settings và overflow tests đi cùng DTO.

CMD38: scoped Teacher + Idempotency-Key, create không If-Match. CMD39: scoped Teacher +
Idempotency-Key + editorial ETag/If-Match + correction reason. Server cấp org/author/hash/
origin/verification attribution; client không override. Family-qualified ETag của head.

Order: parse/bounds → current principal/disclosure auth → accepted receipt lookup và canonical
payload match → replay original committed status/body → unseen mutation mới kiểm current
context/purpose/lifecycle/policy/If-Match → atomic commit. Same key khác payload409; wrong
If-Match412; missing precondition typed428; failed guards/storage không giữ success receipt.

Accepted replay giữ original version dù head lênv2, pause hoặc If-Match cũ. Không dùng new
mutation guards để đổi accepted result thành failure. Withdrawn read scope deny receipt;
consent revoke có thu hồi disclosure phải deny. Mutation-only pause không xóa receipt.
Receipt replay không cấp generation eligibility; consumer luôn resolve_exact lại trước dùng.

Receipt uniqueness scope là (organization_id, authenticated principal_id, contract_name,
target_id, Idempotency-Key). Create target_id là collection knowledge-bundles; edit là exact
bundle_id. Canonical semantic payload gồm body có session/basis/context pins, không gồm
transient If-Match/correlation header; replay cùng body với original If-Match cũ vẫn nguyên
kết quả. Scope/operation target không nhận override từ client; cross-principal keys độc lập.

## 6. Atomicity và race protocol — single-process fixtures

KnowledgeCommitCoordinator infrastructure07 dùng chung cho own repository và mọi fake
basis/audience/authority/disclosure/consent/catalog/policy publication. Không mutable dict
leak/bypass; test audit mọi mutation. Không sửa composition/transactions của01–06.

Command đọc receipt/state/current facts trong coordinated unit; final guards/CAS giữ lock
qua publish. Stage head/version/correction/receipt/audit/outbox cùng một commit; exception
rollback tất cả. Lock order coordinator trước store; finally luôn release.

Other-thread fact publication chờ unit kết thúc. Same-thread external publication từ hook
được queue, chưa coi là applied; drain sau outer commit hoặc rollback. Subsequent resolve
thấy epoch mới và fail closed. Đây là local ordering, không distributed fence.

Nested own07 command có thể commit trong reentrant hook: local generation chụp khi stage,
kiểm lại sau hook trước publish. Inner accepted commit làm outer stale snapshot bị reject;
inner receipt/version/event giữ nguyên. Same-operation loser reread winning receipt sau
rollback và reauthorize disclosure; không false success hoặc retry side effect vô hạn.

Create uniqueness/edit CAS cùng UoW. Superseded event names exact old bundle id/version/hash,
stable identity khi replay. Resolver deny old version ngay sau v2 commit, không đợi delivery.
Recording consumer fake chỉ chứng minh projection/idempotent apply; không real08/09 delivery.

## 7. Public07→08 handoff

Public resolve_exact/export cung cấp immutable canonical content và current decision. Consumer
không tự ráp facts bỏ provenance. Export tách editorial/context/audience revisions và exact
source refs như VideoPin08; script_text derive từ structured sections. Consumer pin digest
không thay producer bundle hash. Candidate conformance vectors kiểm normalized native JSON,
không claim general equivalence với consumer canonical_digest không NFC.

Own DTO/fixture không import08 code chưa có trên nhánh. Real VideoCreationResolver.hold /
assert_current phải giữ producer validity qua commit08; cross-owner lease/fence là integration
gate. Không merge08–14 ở checkpoint này; FEAT collisions/migration reconciliation giữ backlog.

## 8. Implementation sau duyệt

| Slice | Output/check |
|---|---|
| K0 | Freeze plan/approval/OD; record ACTIVE07/WIP1 trước source |
| K1 | domain/knowledge_bundle.py + domain/hash vector tests |
| K2 | contracts/schemas/knowledge_bundles.py, application/ports/knowledge_bundle.py + strict tests |
| K3 | infrastructure/knowledge_bundle/coordination.py/fakes.py + rollback/CAS/publication tests |
| K4 | application/services/knowledge_bundle.py create/edit/read/resolve/receipts + service tests |
| K5 | infrastructure/knowledge_bundle/adapters.py/harness.py/examples.py + producer/consumer candidate fixtures |
| K6 | Races/fail injection/assertion map, no provider/canvas/source01–06-change invariants |
| K7 | One final offline01–07 batch, lint/type/validators; independent review/fixes |
| K8 | Owner offline acceptance rồi inventory/publication plan riêng trên task07 |

Test files: unit/test_knowledge_bundle_{domain,service,adapters,races,chain}.py và
contract/test_knowledge_bundles.py; producer artifact KNOWLEDGE_BUNDLE_EXAMPLES.json.
Publication commit count/path groups chốt sau review/acceptance; không tạo commits để đủ số.

## 9. Acceptance — planned, mọi test07 hiện NOT_RUN

| ID | Assertion |
|---|---|
| P01 | Generic topic/catalog → sourced v1; không child consent call |
| P02 | Child basis ghi exact contributors/purpose/snapshot provenance |
| P03 | Missing sources → needs_content_action; zero model/job/provider calls |
| P04 | Teacher claim-level correction → sourced/attested v2 và derived fact text |
| P05 | v1 canonical bytes immutable; v2/correction/exact supersession event atomic |
| P06 | Current exact export đủ script/source/context/audience separate revisions |
| P07 | Accepted replay original version/status/body sau headchange/pause/stale IfMatch |
| P08 | Imagined/story separation; sticky child-derived khi bỏ selections |
| P09 | Deterministic producer example → JSON value equality |
| P10 | Consumer fake apply event một lần, unrelated exact bundle không bị invalidate |
| N01 | Arbitrary unrelated fact text với valid claim_ref bị reject, KB-PR01 closed |
| N02 | Imagined-as-fact/literal leakage, unknown claim/imagined refs bị reject |
| N03 | Source missing/notreviewed/recalled/wrong revision/hash/topic/age → đúng reason |
| N04 | Basis revision/confirmation/applicability đổi → không disclose ready content |
| N05 | Client scope/actor/contributor/text/origin override hoặc thiếu trusted scope bị reject |
| N06 | Per-contributor purpose/membership; một người revoke → child-derived deny |
| N07 | Admin/device/foreign Teacher/cross-session không được read/write; safe existence handling |
| N08 | Unseen key kiểm current guards/IfMatch; stale/missing precondition typed |
| N09 | Same key khác payload409; failed attempt không giữ accepted receipt |
| N10 | Withdrawn disclosure deny replay; mutation-only pause không rewrite receipt |
| N11 | No-op edit không CAS/version/correction/event mới |
| N12 | Floats/nonfinite/unsupported/NFCduplicate keys và bounded overflow bị reject |
| N13 | Old version/hash tamper/source/policy/audience change không ready; read không ghi |
| N14 | Không invent pre-render/final-video approval hoặc automatic model call |
| R01 | Source recall commit trước finalunit → command/resolve deny |
| R02 | Basis/context/audience/consent/policy change trước commit được finalguard bắt |
| R03 | Request publication trong unit → chờ commit/rollback xong mới apply; resolve sau deny |
| R04 | Fail stage version/correction/receipt/audit/outbox → rollback tất cả, retry được |
| R05 | Two edits sameETag → một version accepted, loser không partial publish |
| R06 | Nested inner commit accepted → outer generation conflict, inner data nguyên vẹn |
| R07 | Same-operation nested winner reread receipt dưới disclosure, không overwrite/false success |
| R08 | Lost ack/replay không duplicate correction/version/event; disclosure vẫn checked |
| R09 | Resolve versus edit linearized; old version deny ngay kể cả chưa drain event |
| R10 | Deferred publication còn chạy sau rollback; lock release/no deadlock, stable event identity |
| C01 | DATA26 shape + own strict extension + canonical/hash vectors |
| C02 | CMD38/39 key/ETag/guardorder/errors/server attribution |
| C03 | Fact projection/structured-flat script và examples equality |
| C04 | Enriched projection không giả DownstreamMeaning có scope/contributor |
| C05 | Exact bundle/source revisions, hash namespaces, consumer candidate fixture |
| X01 | Existing required01–06 + new07 trong same final offline batch |
| X02 | Source/canvas/original modules/approvals/reviews/metrics immutable |
| X03 | Audit mọi fake guard publication và receipt/current-read bypass |

42case IDs. Assertion map cần test::node thực và PASS/PARTIAL/NOT_RUN; không claim pass vì
có tên test hoặc tautological assertion. Không dự đoán số pytest cases trước execution.

## 10. Verification/evidence

Venv sẵn của repository; PYTHONPATH/MYPYPATH trỏ worktree07/backend/src; không install.
Focused development checks chạy trong quá trình code. Final snapshot pin filelist/profile/
hashes, chạy required01–07 offline batch một đợt: reuse50file selection06, thêm07, kiểm
collection/JUnit/exit và reasons cho skips/exclusions. Không chờ Lightning mới unit test.
Pillow live-app skips và V2server module exclusion được ghi thật, không biến thành pass.

Ruff changed source/tests, mypy strict source, harness/security/architecture/skeleton,
diffcheck và before/after source/EOL/hash invariants. Code/contract/config đổi sau final batch
thì refresh snapshot/rerun required batch; docs-only không repeat regression vô ích.
Independent review fact provenance, scope/receipt/concurrency và runtime claims trước owner acceptance.

Publishable note/metrics/review/assertion map/generated examples thuộc feature056; raw logs,
JUnit/env/probes/inputcopies trong ignored evidence/local. Giữ LF/frozen hashes, failed attempts
không xóa. Runtime campaign: [BE2_01_07_RUNTIME_CAMPAIGN_PLAN.md](BE2_01_07_RUNTIME_CAMPAIGN_PLAN.md),
chỉ gate inventory, không executed receipt hoặc authority tự dựng service/provider.

## 11. Gói owner decisions đề xuất

| OD | Khuyến nghị |
|---|---|
| 01 | FEAT056/ownbranch từ23acf9e, ACTIVE07/WIP1 chỉ sau plan approval |
| 02 | Hai trusted basis fixtures + currentbasis; real02/BE1 adapter deferred |
| 03 | Catalog-reviewed và explicitly sourced Teacher-attested claims ready theo named fixture policy |
| 04 | Fact/story text derive từ refs; claim-level edit, immutable version/hash/correction |
| 05 | Own coordinated UoW/fakepublications/CAS/generationguard/publicexactresolver |
| 06 | Strict own0.1candidate extensions/export; actual08heldfence/adoption deferred |
| 07 | Synchronous deterministic/memory/noHTTP/noLLM/noinstall, missing-source draft, fixture bounds |
| 08 | Offline07 trước; source-pinned runtime01–07 sau prerequisites/approval; A17 profile riêng |

OD03 tradeoff: Teacher chịu trách nhiệm correction có source nhưng hệ thống không xác minh
ngữ nghĩa. Phương án chặt hơn là teacher_attested chỉ draft/needs_content_action đến catalog
review; nếu chọn phải sửa readiness/tests trước freeze. Không ghi owner đã chọn lựa chọn nào.

## 12. Điểm dừng

Planning deliverable: self-contained plan, independent focused review, decision package và
runtime campaign; approval vẫn AWAITING_APPROVAL, source/tests07 chưa có. Sau owner duyệt
revision/hash/gói OD mới freeze và ghi APPROVED trước K1. Offline acceptance không đóng
runtime/P1-P2-P4 adoption/integration hay toàn card DONE.
