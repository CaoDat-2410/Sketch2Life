# BE2-04 — Sketch proposal component offline (FEAT-050), working plan

- Status: APPROVED
- Implementation status: SK1 ACCEPTED (offline component, 2026-10-18,
  `../approvals/SK1_COMPONENT_ACCEPTANCE.md`); card BE2-04 IN_PROGRESS / NOT_DONE
- Approval: owner Person 2, 2026-10-18 (verbatim `../approvals/TASK_APPROVAL.md`). Approved bytes
  `PLAN_REV5_APPROVED.md`, 108 220 B, SHA256
  `461d06849899ea41f2c93432ed8b88c5a64428cf17bce5d2959a6d26ef4fa819`; Q1–Q6 as recommended.
- This working copy differs from the approved bytes only in this header block. The approved
  file is immutable; if they ever disagree, `PLAN_REV5_APPROVED.md` governs.
- Owning feature: `features/FEAT-050-be2-sketch-generation` (card BE2-04), branch
  `feature/be2-04-sketch-generation`, worktree `.worktrees/be2-04-sketch-generation`, base
  `113cdf956a09336a0abf5561bd939f5e13b31ea0`. Paths in the body that point at FEAT-049 local
  planning files are historical inputs; the plan is owned here.
- Acceptance → test mapping: §9 (test files) plus `../evidence/notes/SK1_IMPLEMENTATION_EVIDENCE_20261018.md`.

Original approved header (verbatim, kept for traceability):


- Ngày: 18/10/2026, Asia/Saigon. Người viết: Claude (Opus 5.5), theo yêu cầu trực tiếp của
  người dùng: sửa revision 4 thành revision 5 theo focused re-review của Codex.
> - Status: **DRAFT_REV5_FOR_CODEX_FOCUSED_REREVIEW**. Implementation NOT_STARTED. Tài liệu này
>   không phải approval; BE2-04 chưa có TASK_APPROVAL.
- Revision 5 so với revision 4: chỉ sửa theo SK-PR01-F2 (bảng §0c), cùng các chỗ phải đồng bộ
  theo (§6.3 actor set, §6.5 wiring/builder, §7.1 C9, §7.2a, §9, §10, §11, §13). Mọi phần đã đóng
  giữ nguyên: SK-PR02-F1, SK-PR03, N01 (CLOSED_AT_PLAN_LEVEL); token, router, ref-set.
- Input của revision 5:
  - plan revision 4 `BE204_COMPONENT_PLAN_REV4.md`, 98 328 B, SHA256
    `92569d9bbe6911c9c914d98cbfcc60ebb8a210382cf6f7485f3e1dfb42d81394` (giữ nguyên byte);
  - Codex re-review `BE204_PLAN_CODEX_REREVIEW_REV4_20261018.md`, 7 549 B, SHA256
    `c612db3502f12cd1f511a61725606788b6494ffa6398aa386a6a18917d4039c6` (NEEDS_REVISION,
    0 P1 / 1 P2); probe `codex-rev4-probes/shared_outbox_probe.py` (+ `.json`).
- Revision 4 so với revision 3: chỉ sửa theo SK-PR01-F1 và SK-PR02-F1 (bảng §0b), cùng các chỗ
  phải đồng bộ theo (§5.2 reason, §6.3–6.5, §7.1 C9, §7.2a, §7.2b, §9, §11, §13). Các phần khác
  giữ nguyên lời của revision 3. SK-PR03 và N01 đã được Codex ghi CLOSED_AT_PLAN_LEVEL.
- Input của revision 4:
  - plan revision 3 `BE204_COMPONENT_PLAN_REV3.md`, 85 326 B, SHA256
    `380247fbd11c9775d6d0da5676cd4e851e01a00f09b51ae156c03bc46eac0d53` (giữ nguyên byte);
  - Codex re-review `BE204_PLAN_CODEX_REREVIEW_REV3_20261018.md`, 8 723 B, SHA256
    `217eeb84e999fb8e902b20c32f949ea8d7fd27814a0499f9c499d1027d9ff437` (NEEDS_REVISION,
    1 P1 / 1 P2 còn lại).
- Revision 3 so với revision 2: chỉ sửa theo SK-PR01, SK-PR02, SK-PR03 và N01 (bảng §0a), cùng
  các chỗ phải đồng bộ theo (§3.2, §4.1, §6, §7, §9, §10, §11, §13). Phần còn lại giữ nguyên lời
  của revision 2.
- Input của revision 3:
  - plan revision 2 `BE204_COMPONENT_PLAN_REV2.md`, 61 816 B, SHA256
    `d80982b2f3e938ca9c90f663f3a25a302c1fabcac4aa5112bc031279b6ccdd90` (giữ nguyên byte);
  - Codex review `BE204_PLAN_CODEX_REVIEW_REV2_20261018.md`, 10 201 B, SHA256
    `f0998bb581c50367894435a578b64e08baea9fd58369b8b8c0a3ddaa5ebbd6f9` (NEEDS_REVISION,
    1 P1 / 2 P2 + N01).
- Checkpoint đề xuất: `SKETCH_COMPONENT_OFFLINE` (SK1) của card BE2-04, không phải business task
  mới. Sau SK1, full card BE2-04 vẫn NOT_DONE.
- Mức: **candidate-only** (roadmap §3.1 bước 2–3, dòng 115–116). Taxonomy, output shape, model
  và profile mà card yêu cầu "quyết định qua ADR/feature approval" (FEAT-040 dòng 551) chỉ dùng
  fixture có nhãn trong SK1.
- Nơi lưu tạm: `features/FEAT-049-be2-assistance-orchestration/evidence/local/be204-preparation/`
  (Git ignore). FEAT-049 không trở thành owner của BE2-04. Chưa cấp FEAT ID, chưa tạo folder
  hay branch.
- Candidate base: `113cdf956a09336a0abf5561bd939f5e13b31ea0`. Đây là tip BE2-03, đã chứa
  01 `6dcc57e` và 02 `f120c4f`.
- Input: draft revision 1 `BE204_COMPONENT_PLAN_DRAFT.md`, 17 349 B, SHA256
  `8daf1f4382ac8804f1e97b5cc00aa19bb8d2cd8917af567c9b5a6911212c5d0a`. Giữ nguyên byte.
- Chỉ thị điều phối: người dùng làm tiếp phần mình độc lập, không chờ người bạn về FEAT ID,
  policy port, copy hooks hay allocation tích hợp. Phần chưa nối được ghi thành handoff/gate.
- Đường dẫn Python tương đối với `backend/src/sketch2life/`; số dòng tại 113cdf9.
- Nhãn:
  - **S** = field/nghĩa vụ từ SRS hoặc FEAT-040.
  - **E** = code/contract đang có.
  - **P** = đề xuất của plan này, cần review.
  - **TC-nn** = lựa chọn kỹ thuật, sẽ ghi vào DECISIONS khi có owning feature.

## 0a. Xử lý Codex review revision 2

Cả ba finding và N01 đều được chấp nhận; không phản bác finding nào. Source đã đối chiếu lại tại
113cdf9, dòng ghi bên dưới.

| Finding | Kết luận | Bằng chứng source | Sửa trong revision 3 | Acceptance mới / sửa |
|---|---|---|---|---|
| SK-PR01 (P1) — read hiện hành của C8 không được giữ tới lúc commit | **Chấp nhận.** Câu "04 không cần coordinator của A1" ở revision 2 là sai. CAS của 04 chỉ thấy thay đổi trên record 04 | `AssistanceService.read` đóng transaction trước khi trả (services/assistance.py 994–1003). `analysis_record` và `downstream_meaning` là hai lần đọc riêng (services/vision_analysis.py 828–855). Thay đổi owner trong chain đi qua `publish_owner_change`, cùng lúc bump `eligibility:<org>` (infrastructure/assistance/harness.py 314–322). Mọi lần ghi Vision có điều phối đều bump `analysis:<org>` (adapters.py 161–183). A1 dùng `decision_epoch` (fakes.py 221–226) và kiểm lại trong commit (services/assistance.py 870–878) | Thêm **decision token** (§7.2a): token = epoch owner, analysis, policy 04 và fence của artifact được tham chiếu. Lấy token *trước* mọi lần đọc; kiểm lại token *bên trong* unit commit của 04. Unit này chạy trong `coordinator.assistance()` của A1 qua decorator `CoordinatedSketchRepository` (§6.3), không sửa A1. Token lệch thì đọc lại và quyết định lại (tối đa 2 vòng, như A1); vẫn lệch thì trả `DECISION_UNRESOLVED`, không ghi gì. Áp dụng cho C1, C5, C8, `revise_level`, `revalidate`. Hook nằm trong unit foundation/vision phải request publication (deferred). `get_record` có nội dung phải kiểm applicability hiện hành; không đạt thì giữ lại nội dung và không mutate. Định nghĩa rõ thay đổi trước và sau commit (§7.2b) | SK-R13 tới SK-R21, SK-N23; sửa SK-R06 |
| SK-PR02 (P2) — queue dùng chung chưa route theo job_type trước start | **Chấp nhận.** Câu "nếu instance A1 có chạm vào sketch job thì start vẫn bị instance sketch chặn" ở revision 2 là sai | `FakeQueue.receive` pop FIFO bất kỳ envelope (infrastructure/ai_jobs/fakes.py 499–504). `FakeWorker` gọi `start_attempt` trước provider, không lọc type (713–722). A1 `start_next` pop bất kỳ envelope và start qua `h.jobs` (infrastructure/assistance/harness.py 257–264) | Thêm `JobTypeRouter` (§6.5). Đây là consumer duy nhất của queue trong test 04: đọc `message.job_type` **trước** start, route Vision về đường A1 (`h.jobs.start_attempt` + `finish_vision` với chính envelope đó), route Sketch về instance sketch (`start_attempt` qua SketchEligibility → provider adapter → `accept_completion`). Giữ nguyên capability gốc, không bỏ envelope; type lạ → redeliver và fail test. Test 04 không gọi `h.start_next()`/`h.run_vision()` khi queue có thể chứa Sketch | SK-R22, SK-R23, SK-C08 |
| SK-PR03 (P2) — ràng buộc level bằng 03 trên mọi version mâu thuẫn với `revise_level` | **Chấp nhận** | Revision 2 §4.1 ghi `assistance_level = requested_level của 03`, trong khi §7.4 và SK-P08 tạo v2 với level khác | Equality với 03 chỉ áp cho v1. Từ v2, level lấy từ lệnh revision đã kiểm quyền; lưu `level_source` theo version (`request` hoặc `revision{receipt_ref}`). Output rule, `generation_digest`, semantic key của job và `content_sha256` đều dùng level hiệu lực của version. Request 03 và provenance của v1 giữ nguyên (§4.1, §5.1, §7.4) | Sửa SK-P08, SK-N20; thêm SK-P11, SK-N24, SK-C03b |
| N01 — khai báo consumer projection có version | **Chấp nhận** | Revision 2 để resolver trả `SketchHandoff` chưa version; adapter dùng domain type của 03 | Thêm `SketchHandoffV1`: value object có version thuộc application ports của 04. Chỉ adapter (infrastructure) import domain/port type của 03; domain và application của 04 không import (§3.2, §6.1) | SK-C09 |

## 0c. Xử lý Codex focused re-review revision 4

| Finding | Kết luận | Bằng chứng source / probe | Sửa trong revision 5 | Acceptance mới / sửa |
|---|---|---|---|---|
| SK-PR01-F2 (P2) — outbox side-effect dùng chung có thể giao quarantine Sketch qua instance A1 với sink thô | **Chấp nhận.** Câu ở revision 4 "`h.jobs` không bao giờ quarantine ref 04" chỉ đúng lúc *tạo* intent (`_owned_descriptors`), không đúng lúc *giao lại* intent đã commit trong repository dùng chung | `deliver_side_effects` đếm và claim **mọi** side effect đang pending, không lọc job type/producer (application/services/ai_jobs.py 789–829). `claim_side_effects` chỉ lọc trạng thái giao, lease và cursor; `owner` là lease holder (infrastructure/ai_jobs/fakes.py 254–284). `_apply_side_effect` gọi `self._d.artifacts.quarantine` của instance đang giao (ai_jobs.py 1225–1229). Sink được gọi sau khi transaction claim đóng và trước transaction mark. Builder A1 truyền `FakeArtifacts` thô cho `h.jobs` (infrastructure/assistance/harness.py 382–388). Probe `shared_outbox_probe`: A1 giao 3 effect, gồm quarantine Sketch qua sink thô (epoch 0→1); mutation xảy ra trong lúc thread khác giữ `coordinator.assistance()` | **Chọn phương án 1: mọi service có thể drain outbox dùng cùng một coordinated sink.** 04 có builder chain riêng `build_sketch_chain_harness()`, dựng lại composition của A1 từ các class/hằng/helper public của A1 (không sửa và không gọi `build_assistance_harness`). Khác biệt duy nhất: **cả hai** instance `AiJobService` (`h.jobs` hướng A1 và `sketch_jobs`) nhận `artifacts = CoordinatedSketchArtifactPort` — cùng một instance, bọc cùng `FakeArtifacts`. `AssistanceHarness.artifacts` vẫn là `FakeArtifacts` thô, chỉ dùng cho `put` (harness A1 chỉ gọi `artifacts.put`, harness.py 288). Actor set viết lại: mọi đường quarantine/cleanup — completion và drain outbox của **cả hai** instance, C9, owner hook — đều đi qua port này (§6.3, §6.5). Phương án 2 (một dispatcher duy nhất + chặn đường A1) không chọn: không sửa A1 thì chỉ có thể chặn bằng monkeypatch method trên instance A1 hoặc bằng quy ước "không gọi" — đúng loại wiring mà review không chấp nhận | SK-R30–R33, SK-C11; sửa SK-C10 |

## 0b. Xử lý Codex focused re-review revision 3

Hai finding còn lại đều được chấp nhận. Source đã đối chiếu tại 113cdf9.

| Finding | Kết luận | Bằng chứng source | Sửa trong revision 4 | Acceptance mới / sửa |
|---|---|---|---|---|
| SK-PR01-F1 (P1) — epoch artifact chưa nằm cùng publication boundary với C8 | **Chấp nhận.** Revision 3 đưa `artifact:<ref>` vào token nhưng chưa có đường ghi được điều phối, nên câu "không writer có điều phối nào lọt vào giữa" chưa đúng với artifact | `FakeArtifacts.quarantine` gọi thẳng `owner_quarantine`; method này cập nhật map và bump fence mà không lấy coordinator (infrastructure/ai_jobs/fakes.py 634–649). Foundation giao quarantine intent qua `self._d.artifacts.quarantine` trong `_deliver_now`/`deliver_side_effects` (application/services/ai_jobs.py 1215–1229). Probe của Codex: gọi trực tiếp thì đổi được artifact trong lúc unit đang giữ lock; bọc trong `request_publication` thì chỉ đổi sau khi unit nhả lock | Thêm `CoordinatedSketchArtifactPort` (§6.3). Mọi quarantine/cleanup ref 04 đi qua `coordinator.request_publication`, cùng backing `FakeArtifacts`, gồm: (1) `deps.artifacts` của instance `sketch_jobs` (side-effect của foundation); (2) C9 `deliver_cleanup`; (3) owner quarantine trong test (`h04.owner_quarantine(...)`). Chỉ có ba actor hợp lệ này; mọi gọi thẳng `FakeArtifacts` trên ref 04 bị bắt bằng kiểm toán (SK-C10). Ref-set được chốt từ snapshot đã commit **trước** `t0`, ghim bằng ref-set identity; đọc sau đó chọn tập khác → bỏ quyết định, lấy token mới (§7.2a). Thêm reason `ARTIFACT_QUARANTINED` | SK-R24–R27, SK-C10 |
| SK-PR02-F1 (P2) — nhánh Vision của router không dừng khi start bị từ chối | **Chấp nhận** | `finish_vision` không tự kiểm start, chạy thẳng observation/claim/completion (infrastructure/assistance/harness.py 266–297). `run_vision` của A1 kiểm `started.started` trước khi gọi `finish_vision` (302–305). `start_attempt` trả `started=False` cho DUPLICATE_DELIVERY / JOB_NOT_QUEUED / bị eligibility từ chối (application/services/ai_jobs.py 657–689) | Cả hai nhánh router kiểm `StartResult` trước. `started=False` → trả `RouteResult(job_type, started=False, reason)`; **không** gọi `finish_vision`, observation, provider hay `accept_completion`; không redeliver envelope (start đã quyết định xong). Chỉ khi `started=True` mới đi tiếp đường của owner (§6.5) | SK-R28, SK-R29; sửa SK-C08 |

## 0. Thay đổi so với draft 1

| # | Draft 1 | Revision 2 | Căn cứ |
|---|---|---|---|
| 1 | Hướng A "ưu tiên khảo sát", chưa chỉ method/field | A cụ thể. Đọc `AssistanceService.read`: trả domain `AssistanceRequest`, có `handoff`, `cache_hit_of`, `facts.source`. Đọc thêm `VisionAnalysisService.analysis_record` và `downstream_meaning` qua reader Teacher được inject. DTO `AssistanceRequestRecordV1` (`teacher_view`) **không** có handoff ref và snapshot ref, nên không đủ nếu dùng riêng | services/assistance.py 994–1004, 1118–1170; domain/assistance.py 395–440 |
| 2 | Coi SketchIntent là đường vào | Callback chỉ là hint best-effort: gọi sau commit, không retry. Request cache-hit không phát intent. Vì vậy thêm open theo `assistance_id`; tự phát hiện request cần mở ghi là NOT_IMPLEMENTED; B delta được nêu cụ thể | services/assistance.py 556–593, 870–911 |
| 3 | Q4 "phải chọn protocol trước code" | Protocol cụ thể: staging theo `(job_id, attempt_id)`; chỉ cho hiển thị sau khi job SUCCEEDED/ACCEPTED; reconcile idempotent. Đây là mẫu 02/03 đang dùng trong chain A1. Có ma trận crash/recovery. Claim chỉ dừng ở fault injection trong một process | services/vision_analysis.py 304–486; infrastructure/assistance/harness.py 266–297; services/ai_jobs.py 704–1030 |
| 4 | "Sketch job/attempt adapter: cần source-audit" | Đã audit: `job_type` là chuỗi tự do; `DispatchMessage` không có body; completion bắt buộc có output artifact do đúng job/attempt sinh; FAILURE claim không được kèm output; retry policy của service được đóng dấu vào job lúc tạo | ports/ai_jobs.py 169–178; services/ai_jobs.py 425, 1010–1030, 1297–1324 |
| 5 | moderation_state "định nghĩa bằng fixture policy" | 04 chỉ ghi `not_applicable`, `pending`, `blocked` (enum DATA-20). Tín hiệu an toàn lúc tạo đi vào claim. Quyết định `passed` thuộc 05 | SRS 1646, 1652, 955; UC-020 |
| 6 | review_revision "bằng fixture policy" | Counter kỹ thuật, Revision ≥1 (B21.1), tăng đơn điệu qua mọi version. 04 tăng khi có version mới hoặc invalidation | SRS 1594; DATA-24 1654 (If-Match) |
| 7 | Field mới chỉ ghi chung "ĐỀ XUẤT" | Mỗi field có nhãn S/E/P và nguồn. Thêm `content_sha256` (target_hash của DATA-24; registry ghi "proposal version/hash"), audience, ref analysis/job/producer. `editable_bounds` để null | SRS 804, 1652, 1654, 1695 |
| 8 | Budget: "named fixture policy, quota semantics rõ" | Không lập ledger 04. Dùng quyết định eligibility/policy (fixture) và giới hạn số attempt. Kế toán cho stage Sketch là gate | A1 D6/D8; infrastructure/ai_jobs/fakes.py 564–597 |
| 9 | Copy lifecycle "fixture seam" chung | Dùng fake support có sẵn trong stack: `ProviderCopyLifecycleService`, `InMemoryProviderCopyRegistry`, `FakeProviderCopyAdapter`, `ProviderCopyLifecycleReportV1`. Không cần code nhánh người bạn | services/provider_copy_lifecycle.py; fakes.py 725–800 |
| 10 | Chưa nói provider nhận gì | Tối thiểu hóa: không gửi child_intent, ID, tuổi hay model candidates. Concept chỉ gửi khi Teacher đã xác nhận (`confirmed`) | C2 plan Q2 dòng 61; services/vision_analysis.py 828–851 |
| 11 | Chưa có rule stale khi có correction | Chỉ stale khi "meaning basis" chiếu sang generator thay đổi. Correction kiểu child proposal không gây stale | domain/vision_analysis.py 944–969 |
| 12 | Cancel/control chưa rõ | Control nội bộ cho Teacher. Sau `pending_teacher_review` trả `INVALID_STATE`. Không có route public. Đường cancel public và cancel từ Child là gate | Roadmap 291; A1 D11 |
| 13 | Chưa có revision theo level | Có `revise_level` nội bộ, chỉ từ `pending_teacher_review` (card yêu cầu "support-level revision"). Có phương án hoãn | FEAT-040 550; SRS 1652 |
| 14 | Chưa nói route | Không có HTTP route, kể cả fixture app (khác A1) | Roadmap §6.1 dòng 291 |
| 15 | Q6 publication | Hard gate: tạo owning feature, ghi approval và tạo branch trước khi code (AGENTS bước 2–5) | AGENTS.md |
| 16 | Acceptance SC-01…17 | Tổ chức lại thành nhóm P/N/R/C/X, có file test; ánh xạ SC cũ ở §9.6. Fault injection chỉ được tính PASS cho protocol một process; durable crash vẫn NOT_IMPLEMENTED | — |
| 17 | Admission "reuse validators khi phù hợp" | `ArtifactPort` không có thao tác ghi. `session_storage.ArtifactStore` là demo storage. 04 định nghĩa consumer port cho `ArtifactReferenceV1` (của P2) kèm fake. Decode NOT_RUN: venv gốc không có Pillow; có `av` 18.1.0 (tùy chọn) | ports/ai_jobs.py 516–522; ports/session_storage.py; FEAT-040 552 |

## 1. Mục tiêu và phạm vi

### 1.1 Kết quả của SK1

Đầu vào là một request BE2-03 đã `analysis_ready`, qua đường handoff hoặc cache-hit. 04 làm
các việc sau:

1. Đọc và ghim handoff, kiểm quyền hiện hành (hướng A).
2. Tạo DATA-23 SketchProposal version 1 ở trạng thái `requested`, rồi tạo một BE2-01 job loại
   `sketch_generation`.
3. Worker gọi fake generator ngoài transaction, kiểm output, staging derivative riêng tư mang
   lineage của job/attempt, và đăng ký provider copies (fixture).
4. Foundation chấp nhận completion. 04 reconcile; chỉ khi mọi cổng hiện hành đạt mới chuyển
   sang `pending_teacher_review` với `moderation_state=pending`.
5. Xử lý cancel nội bộ, owner notices, output unsafe/malformed, timeout/retry, revision theo
   level, idempotency, CAS và rollback.
6. Phát event candidates và record H-AI-REVIEW cho 05. Child chỉ thấy trạng thái chờ.

### 1.2 Không thuộc SK1

- Model/provider/inference thật; quality, latency, cost thật.
- Taxonomy level/support mode được adopt.
- SQL, migration, Redis/RQ mới, outbox durable, recovery đa process.
- BE1 artifact admission/storage/mediated delivery thật (`ArtifactReferenceV1`, DATA-20);
  decoding và safety classifier thật.
- Moderation và Teacher review (05, CMD-35); Child response (06, CMD-36).
- HTTP route, auth, live app; composition P4 (INTG-02/05); UI của P1.
- Merge hoặc sửa nhánh người bạn; adopt policy/budget/copy hooks của BE2-14.
- Xác nhận xóa thật ở provider.
- Sửa A1/C1/C2/foundation hoặc package A17.

### 1.3 Claim được phép khi SK1 PASS

Được claim: "Component BE2-04 đúng contract trên các fake/adapter đã ghi; chain offline
01→02→03→04 chạy trong một process; fault injection protocol trong một process."

Không được claim: Sketch generation thật, runtime/durable, an toàn nội dung thật, tích hợp với
05/06/BE1/P4, full card DONE.

## 2. Nguồn và seams đã kiểm tại 113cdf9

### 2.1 Nghĩa vụ nguồn

| Nguồn (dòng) | Nghĩa vụ | SK1 xử lý |
|---|---|---|
| SRS DATA-23 (1652) | Danh sách field. Ít nhất có text hoặc reference asset đúng output shape. Không có command vẽ. Child ở trạng thái pending chỉ thấy status. Sửa level/output tạo version mới và phải review lại | §4 field map; §5 invariants |
| SRS DATA-20 (1646) | `origin ai_derived`, `source_refs`, `producer_ref`, enum `moderation_state` | Metadata của derivative (P, ASSUMED_CONTRACT với BE1) |
| SRS B19.10 CreateSketchProposal (955), SourceChangesDuringAI (958) | Purpose/age/tools/source đã duyệt, safety validator, geometry bounds → `pending_teacher_review`. Child không fetch trước cổng review. Source đổi → stale, hoặc giữ reference view theo policy | Cổng §7; geometry bounds = gate G-08 |
| SRS UC-017 (1254–1263), UC-019 (1276–1285) | AI tách khỏi nét trẻ. Callback chỉ tạo proposal/result ref. Worker tạo proposal có provenance rồi revalidate cancel/scope/stale. Kết quả về sau khi đã cancel không được available | §5, §7 |
| SRS FR025 và ghi chú (401, 408) | Mức 0–4 là taxonomy PROPOSED | Level opaque + fixture rules (Q2) |
| SRS B19.2 (752–790) | Không có key timeout/retry riêng cho Sketch. LIMIT_TEXT_LONG 4000 và LIMIT_ASSET_BYTES 10 MiB là PROPOSED. Giá trị TBD không được đọc thành 0 hay vô hạn | Dùng lại retry fixture của foundation; bound fixture trích từ giá trị PROPOSED của SRS |
| SRS B21.1 (1581–1594), B21.5 (1695, 1696, 1699) | DTO đóng; Revision ≥1. Completion thuộc attempt hiện hành. Kết quả cancel/stale giữ ở diagnostic disposition hạn chế. Review unique theo target_version/hash. Consent phải còn hiệu lực lúc dispatch và lúc chấp nhận completion | §4, §7 |
| SRS P-NFR-08 (2248), FIX-UX-04 (2270), events (549 `SketchProposalReady`) | Pending/stale/unsafe không deliver cho Child. Không mutate nét | §9 N-cases; event `sketch.proposal_ready` |
| FEAT-040 BE2-04 (546–557) | DATA-23 producer, SketchGenerator port, fake/real, worker/timeout/cancel, admission/provenance, support-level revision, provider-copy hooks. Handoff H-AI-REVIEW + H-DATA-REQUEST. Reviewer P2/P1/P4 | Toàn plan; phần real và cross-owner là gate |
| FEAT-040 owner ledger (870, 897) | DATA-23 schema owner là BE2-04. DATA-20 schema thuộc BE1-10; P3 giữ provenance/eligibility của derivative | §4 |
| Roadmap §3.1 bước 3 (116), §4 BE2-04 (170–175), §6.1 (291) | 04-component chỉ gồm fake port và output admission. Không có route public | §1, §6 |
| FEAT-049 A1 D8/D9/D11, §9.2 (553–556, 425–436) | Intent ở mức SIMULATED. Không map level. Sau handoff, việc rút lại thuộc 04/05. Với cache-hit, "mọi Sketch downstream vẫn cần review từng item" | §3 |
| FEAT-048 C2 plan Q2 (dòng 61) | Không gửi free text của Child cho provider | TC-06 |
| AGENTS.md | Phải có feature folder, plan và approval trước code. Domain không import framework. Application không import outer layer | Q6; §10 |

### 2.2 Seams thực tế

Chỉ dùng public service/port. Không sửa code nào ở 01/02/03.

| Owner | Seam | Sự thật đã kiểm | SK1 dùng thế nào |
|---|---|---|---|
| 03 | `AssistanceService.read(principal, id)` (994–1004) | Kiểm org và `authority.disclose`, trả domain `AssistanceRequest` | Resolver A |
| 03 | `AssistanceRequest` (domain 413–440) | Có `status`; `handoff: HandoffRef(analysis_id, analysis_revision, job_id, attempt_id)`; `cache_hit_of`; `facts` (scope, audience, roster_revision, purpose, policy, context_revision, `source: SourcePin` với snapshot_ref/checkpoint/render/input_hash); `requested_level`; `requester`; `assistance_context_digest` | Ghim binding. Không đọc `child_intent` |
| 03 | `teacher_view` (1118–1170) → `AssistanceRequestRecordV1` | Không có handoff ref, không có snapshot ref/render | Không đủ nếu dùng riêng (lý do cần B) |
| 03 | Handoff commit (870–911) | Intent được ghi trong UoW. `request_sketch(intent)` gọi sau khi ra khỏi `with` (910–911), không có try/except, không retry | Adapter callback không được ném lỗi |
| 03 | Cache hit (`_new_request` 556–593) | Tạo request thẳng ở `analysis_ready`, `handoff=None`, `cache_hit_of=…`, không phát intent | Resolver hỗ trợ đường này; cần open theo id |
| 03 | `SketchIntent`/`SketchStagePort` (ports 77–86, 303–304) | Gồm intent_id, assistance_id, request_revision, analysis_id/revision, `SIMULATED_NO_PRODUCER` | 04 implement adapter (chỉ là hint) |
| 03 | Scheduler (631–699) | Dựng lại `Principal` từ `ScheduleIdentity` đã đóng băng để tạo job (TC-10 của A1) | Mẫu cho principal tạo sketch job |
| 02 | `analysis_record`, `downstream_meaning` (828–855), `_teacher_read` (878–892) | Chỉ Teacher có disclosure gọi được. `downstream_meaning` trả NOT_APPLICABLE khi consent/purpose/session/tuổi/context/source không còn hiện hành | Cổng hiện hành chính |
| 02 | `analysis_record_view` (1077–1137) | Có lineage của candidate; `source_binding` (snapshot ref, checkpoint, render ref/sha/media, `admission_receipt_id`); `current_meaning_ref` | Đối chiếu với pin của 03; input cho generator |
| 02 | `apply_correction` (domain 944–969) | Mọi correction đều tăng `analysis_revision`; chỉ Teacher confirmation đổi meaning | TC-07 meaning basis |
| 02/03 | `VisionAnalysisOutcomes` (adapters 316–358) | Reader Teacher được inject, không suy ra từ request (A1 rev3) | Tiền lệ cho reader của 04 |
| 01 | `create_job` (342–446) | `job_type` là chuỗi tự do; dedup theo semantic key; retry policy của instance đóng dấu vào job (425) | Job `sketch_generation` |
| 01 | `start_attempt` (657–689), `accept_completion` (704–787), `_decide_completion` (952–1008) | Kiểm eligibility trước khi start/complete; ineligible → cancel. FAILURE → `record_failure`. UNSAFE → quarantine + blocked. Context đổi → succeeded/STALE | Worker seam |
| 01 | `_validated_outputs` (1010–1030), `_normalise_claim` (1297–1324), `_produced_by` (1420–1425) | Success cần ≥1 output do đúng org/job/attempt sinh, đúng sha, chưa bị quarantine. FAILURE không được kèm output. Mã lỗi ngoài 4 mã worker → PROVIDER_ERROR | Luôn có result document artifact |
| 01 | `DispatchMessage` (169–178) | Chỉ có job/attempt/type/request_ref, không có body | Worker đọc input từ store 04 |
| 01 | `ArtifactPort` (516–522) | Chỉ có describe/quarantine, không có thao tác ghi | 04 cần admission port riêng |
| 01 | `Principal` (57–69) | Role: teacher/admin/device; không có service role | Q4 |
| 01 | `find_semantic` (UoW 350; SQL 481) | Lookup theo semantic key đã index | Tìm job mồ côi khi mất reply |
| 01 | `ProviderCopyLifecycleService`, fake registry/adapter | Receipt fixture không bao giờ được coi là đã xóa thật | Copy hooks của SK1 |
| 01 | `FakeWorker`/`FakeProvider` (692–722) | queue → start → `provider.run(message)` → completion; nhận envelope bất kỳ, không lọc theo type | Chỉ dùng trong unit test có queue riêng của 04. Chain dùng `JobTypeRouter` (§6.5, SK-PR02) |
| 01 | `FIXTURE_RETRY_POLICY` (91–98) | 3 attempts, timeout 30 s, PROPOSED | Dùng lại, không thêm số mới |
| — | `ArtifactReferenceV1` | Không có code trong stack (đã grep) | ASSUMED_CONTRACT |

## 3. Handoff 03→04: chọn A hay B

### 3.1 So sánh

| Tiêu chí | A — resolver phía 04, dùng public reads của 03/02 | B — checkpoint 03 mới phát hành handoff có version |
|---|---|---|
| Đủ dữ kiện để ghim | Đủ. `read` trả domain aggregate có handoff/cache_hit_of/facts.source/level/policy/requester/digest; 02 cho source binding, lineage, meaning | Đủ, qua contract có version |
| Quyền hiện hành | Mỗi lần đọc đều kiểm disclosure (03) và Teacher disclosure (02) | Như A, cộng với publication |
| Phát hiện request cần mở | Chỉ khi callback hint đến hoặc có caller đưa `assistance_id`. Cache-hit không có hint → không tự phát hiện | Có: listing/outbox các handoff đang chờ, cho cả hai đường |
| Delivery bền vững/ack | Không | Có, nếu checkpoint B làm |
| Coupling | Phụ thuộc domain type chưa version của 03 | Contract `AssistanceHandoffV1` có version |
| Atomic xuyên feature | Không | Không |
| Ảnh hưởng tới A1 đã nghiệm thu | Không sửa A1 | Cần checkpoint 03 mới có approval riêng; byte của A1 giữ nguyên |
| Chặn SK1? | Không | Có — phải chờ checkpoint 03 |

### 3.2 Khuyến nghị: A cho SK1; B là gate trước runtime integration

Thiết kế của A:

1. **Hint.** `SketchStageAdapter` implement `SketchStagePort`. `request_sketch(intent)` chỉ ghi
   hint vào inbox của 04, idempotent theo `intent_id`. Adapter nuốt mọi lỗi phía 04 (ghi audit
   candidate) và không bao giờ ném lỗi vào 03, vì callback chạy sau commit 03, ngay trong call
   stack `reconcile` của 03, mà ở đó không có try/except.
2. **Mở proposal.** `open_from_handoff(organization_id, assistance_id, hint=None)` luôn đọc nguồn
   chuẩn qua `AssistanceService.read(reader, …)`. Hint chỉ dùng để đối chiếu; nếu lệch → refuse
   `HANDOFF_MISMATCH`.
3. **Hai đường input.**
   - Handoff: `status=analysis_ready` và `handoff` có giá trị.
   - Cache-hit: `status=analysis_ready`, `handoff is None`, `cache_hit_of` có giá trị. Lineage
     của analysis thuộc request gốc; proposal vẫn mang `assistance_id`/`request_revision` của
     request mới.
   - Mọi trường hợp khác → `HANDOFF_NOT_READY`.
4. **Đọc 02** bằng cùng reader: `analysis_record` và `downstream_meaning`. Đối chiếu:
   - lineage của candidate (assistance_id gốc, request_revision, job_id, attempt_id) với
     handoff/cache_hit_of;
   - `source_binding` với `facts.source` (snapshot_ref, checkpoint id/checksum, render ref/sha);
   - context_revision.
5. **Reader.** Principal role TEACHER, giới hạn trong class, inject từ composition (giống
   `READER` của A1). Không suy ra từ request, không dùng principal của Child. Identity cho
   production là gate G-12.
6. **Recovery/discovery.** Nếu callback bị lỡ (crash) hoặc là request cache-hit, cần một caller
   gọi `open_from_handoff` theo id. Trong SK1, harness/test đóng vai caller. Tự phát hiện là
   NOT_IMPLEMENTED (G-02).
7. **Consumer projection có version (N01).** Adapter chiếu kết quả đọc 03/02 thành
   `SketchHandoffV1`: một value object bất biến thuộc `application/ports/sketch_generation.py`,
   có `contract_version = "sketch-handoff-v1"`. Field gồm:
   - assistance_id, request_revision, handoff_kind, cache_source_assistance_id;
   - analysis_id/analysis_revision, vision job_id/attempt_id;
   - organization/class/session/canvas/group, target, audience, roster_revision,
     contributor_participant_id, purpose_code;
   - source pin (snapshot_ref, checkpoint id/epoch/sequence/checksum, render ref/sha/media type,
     admission_receipt_id, input_hash), context_revision;
   - requested_level, 03 policy ref (id/version), requester đã đóng băng (principal_id + kind),
     assistance_context_digest;
   - meaning basis (state, confirmation_ref, confirmed concepts).

   `SketchCurrentState` cũng là value object riêng của 04. Chỉ `infrastructure/sketch_generation/
   adapters.py` import `domain.assistance`, `application.ports.assistance` hoặc types của 02.
   Domain và application của 04 không import type producer nào của 03. Không cần sửa producer 03
   để có DTO này; checkpoint B sau này có thể thay adapter mà không đổi phía 04.

Delta tối thiểu cho B (chỉ ghi lại, chưa làm):

- Contract `AssistanceHandoffV1` gồm: assistance_id, request_revision,
  `handoff_kind ∈ {analysis, cache_hit}`, analysis ref, vision job ref, source pin đầy đủ,
  context_revision, requested_level, policy ref, purpose, scope/audience/roster_revision/region,
  requester đã đóng băng, digest, `handoff_id` tất định.
- Phát contract này trong cùng commit `analysis_ready`, cho cả hai đường.
- Listing `pending_handoffs(org, after, limit)`, hoặc outbox kèm receipt của consumer.
- Tùy chọn: `AssistanceHandoffWithdrawnV1` (phương án thay thế của D11).
- Không sửa DTO cũ rồi vẫn giữ claim của A1.

## 4. DATA-23 và provenance

### 4.1 `SketchProposalRecordV1` (Teacher/internal; 0.1-candidate; strict, `extra="forbid"`)

| Field | Nhãn | Quy tắc |
|---|---|---|
| `proposal_id` | S | OpaqueId do server cấp. Unique theo `(organization_id, assistance_id)`: một request có đúng một proposal (TC-01) |
| `proposal_version` | S | Revision ≥1. v1 lúc mở; tăng khi có revision theo level (P) |
| `review_revision` | S | Revision ≥1 (B21.1). Khởi tạo 1, tăng đơn điệu qua mọi version. 04 tăng khi có version mới hoặc invalidation (stale/cancel). 05 sẽ tăng khi review (ASSUMED_CONTRACT, G-05) |
| `assistance_id`, `request_revision` | S | Lấy từ `read` của 03; không dùng "latest" |
| `source_snapshot_ref` | S | `facts.source.snapshot_ref`, bằng `input_snapshot_ref` của 02 |
| `context_revision` | S | Ghim từ facts của 03; phải bằng giá trị trong candidate của 02 |
| `assistance_level` | S | Level **hiệu lực của version hiện hành** (opaque); phải có rule trong fixture policy của 04 (Q2). v1: bắt buộc bằng `requested_level` của 03 lúc mở. Từ v2: lấy từ lệnh `revise_level` đã kiểm quyền; request 03 không đổi (SK-PR03) |
| `level_source` (theo version, Teacher/internal) | P | `request` cho v1; `revision{receipt_ref}` cho version tạo từ `revise_level`. Lịch sử version giữ level và nguồn của từng version, nên provenance của v1 và request 03 vẫn truy được |
| `display_mode` | S | `side_reference` hoặc `overlay`; suy từ rule của level. Không có input từ client vì DATA-21 không có field mode (TC-03) |
| `overlay_asset_ref` | S N/S | Ref derivative duy nhất cho cả hai display mode (P, dựa trên `sketchArtifactRef` trong domain model, SRS 255). Null khi rule chỉ có text |
| `text_or_question` | S N/S | Text thuần, NFC, cấm control char, ≤ bound fixture (4000 = LIMIT_TEXT_LONG PROPOSED). Không có HTML thực thi; không cắt im lặng |
| `editable_bounds` | S N/S | Luôn null trong SK1: shape chưa được định nghĩa; geometry là G-08 |
| `moderation_state` | S (enum DATA-20) | 04 chỉ ghi `not_applicable` (chưa có output), `pending` (output chờ 05), `blocked` (unsafe). Không bao giờ ghi `passed` |
| `pipeline_state` | S | Đúng 9 giá trị của SRS. 04 không bao giờ ghi `approved`/`rejected` |
| `created_at` | S | Lấy từ fake clock |
| `approval_ref` | S N/S | Luôn null phía 04 (05 ghi) |
| `child_response` | S N/S | Có schema `{action: available\|viewed\|hidden\|declined, participant_id, turn_id, responded_at}` vì 04 là schema owner; luôn null phía 04 (06 ghi) |
| `content_sha256` | P | target_hash cho DATA-24, theo registry "proposal version/hash" (SRS 804, 1654, 1695). Chỉ có khi đã có output |
| `organization_id`, `session_id`, `canvas_id`, `group_id` | P | Server suy ra từ facts của 03; cần cho phạm vi review |
| `audience_participant_ids` | P | Audience đã ghim. 05 validate audience của review là tập con (DATA-24) |
| `analysis_ref{analysis_id, analysis_revision}` | P | Provenance (UC-019 bước 4) |
| `handoff_kind` | P | `analysis` hoặc `cache_hit`; cache-hit kèm `cache_source_assistance_id` |
| `generation_job_ref{job_id, attempt_id}` | P | Attempt được promote; null trước đó |
| `producer_ref{adapter_id, model_profile_version, configuration_version}` | P (DATA-20) | Profile fixture trong SK1 |
| `generation_evidence_kind` | P | `fixture` hoặc `provider`; SK1 luôn là `fixture` |
| `policy_ref{policy_id, version, status}` | P | Ghim policy của 04 lúc mở |
| `status_reason` | TC-02 | Token đóng (§5.2). Bắt buộc với stale/cancelled/failed/blocked_unsafe |
| `updated_at` | P | Lấy từ fake clock |

Không đưa vào record: child_intent, tuổi/tháng, consent record, model candidates, raw provider
log, URL/ticket, key/endpoint.

Teacher chỉ thấy `text_or_question` và `overlay_asset_ref` khi proposal đang
`pending_teacher_review` **và** lần kiểm hiện hành lúc đọc đạt: `current(binding)`, policy còn
rule cho level, artifact chưa bị quarantine (SK-PR01). Không đạt thì record trả nội dung là null,
kèm `content_withheld_reason` (P, Teacher/internal), và yêu cầu revalidate qua inbox. Read không
mutate proposal. Với `blocked_unsafe`, Teacher chỉ thấy reason, không thấy nội dung bị chặn
(DATA-20: "exact moderation evidence restricted").

### 4.2 `SketchProposalDeviceViewV1` (Child)

Chỉ gồm `assistance_id` và `status ∈ {pending, unavailable}`. Không có proposal_id, text, asset,
audience hay lý do kỹ thuật. Mọi pipeline_state của 04, kể cả `pending_teacher_review`, đều chiếu
thành `pending` hoặc `unavailable`. Hiển thị nội dung đã duyệt thuộc 05/06 và BE1.

### 4.3 Events và hash

- **`SketchProposalEventV1`**: event_id tất định; `event_type` thuộc tập đóng:
  `sketch.proposal_requested`, `sketch.scheduled`, `sketch.proposal_ready` (SRS
  `SketchProposalReady`), `sketch.blocked_unsafe`, `sketch.failed`, `sketch.cancelled`,
  `sketch.stale`, `sketch.superseded`, `sketch.open_refused`, `sketch.cleanup_requested`.
  Kèm organization_id, proposal_id/version, assistance_id, reason, occurred_at. Không có nội
  dung hay child text. Delivery NOT_RUN, như A1.
- **`content_sha256`** (TC-04): strict canonical SHA256 của
  `{rules: "sketch-proposal-content-v1", proposal_id, proposal_version, assistance_id,
  request_revision, source_snapshot_ref, source_input_hash, context_revision, assistance_level,
  display_mode, text_or_question, asset{ref, sha256, media_type, byte_size}|null,
  editable_bounds: null, analysis_ref, producer_ref, policy_ref}`. Không gồm timestamps,
  pipeline_state, moderation_state, review_revision. Có golden vector.
- **`generation_digest`** (TC-05), dùng làm `RequestRef.input_hash` của sketch job: canonical
  SHA256 của projection gửi generator và các pin
  `{rules: "sketch-generation-input-v1", proposal_id, proposal_version, source_input_hash,
  render_sha256, assistance_level, display_mode, output_rule, meaning_basis_digest, policy_ref,
  generator_profile_ref}`.
- Trong cả hai hash, `assistance_level` và `display_mode`/`output_rule` là giá trị **hiệu lực
  của version** đang xét (SK-PR03). Không bao giờ thay bằng `requested_level` của 03 khi
  version ≥2. Vì `proposal_version` và `generation_digest` nằm trong `RequestRef`, semantic key
  của job theo từng version cũng khác nhau.
- **ETag nội bộ** (TC-06): `"sketch-proposal:<id>:<version>:<review_revision>"`.

### 4.4 Tương thích

- ShapeSpec DATA-23 (ai_contract_candidates.py 225–237) giữ nguyên; record mới phải qua
  `check_shape("DATA-23", …)`.
- Copy report dùng `ProviderCopyLifecycleReportV1` có sẵn (dòng 146), với `fixture_marker=true`.
- Không thêm field vào DATA-24 hay DATA-21.

## 5. Domain (`domain/sketch_proposal.py`, thuần, không framework)

### 5.1 Aggregate

- `SketchProposal`: `record_version` cho CAS; version hiện hành và lịch sử version bất biến.
  Mỗi version có:
  - level hiệu lực và `level_source` (§4.1);
  - output rule đã ghim, `generation_digest`;
  - `GenerationStage` (job_id, schedule identity đã đóng băng, cleanup job ids).
- `DecisionToken` (value object): epoch của owner, analysis, policy 04 và fence của artifact
  được tham chiếu, cho một org (§7.2a). So sánh bằng nhau tuyệt đối; domain không tự đọc epoch.
- `StagedGeneration`, key `(job_id, attempt_id)`: các part đã validate, artifact ref/sha, result
  document ref/sha, producer, evidence_kind, copy ids, claim fingerprint, trạng thái
  `staged|promoted|superseded|discarded`.
- Value objects:
  - `HandoffBinding`: mọi pin ở §3.2.
  - `MeaningBasis{state, confirmation_ref, concepts}` và digest.
  - `LevelOutputRule{display_mode, text: required|optional|forbidden,
    asset: required|optional|forbidden}`.
  - `OutputPart`, tập đóng: `text_or_question` | `reference_image{bytes_sha256, media_type,
    byte_size}`.

### 5.2 Máy trạng thái (pipeline_state của version hiện hành)

| Từ | Sự kiện | Đến | Reason |
|---|---|---|---|
| — | Open hợp lệ, cổng đạt | requested | — |
| — | Handoff hợp lệ nhưng analysis không còn áp dụng, hoặc owner facts đã đổi | stale | ANALYSIS_NOT_APPLICABLE / CONSENT_REVOKED / … |
| — | Handoff hợp lệ nhưng policy thiếu/tắt, hoặc level không có rule | failed | POLICY_UNRESOLVED / POLICY_DISABLED / LEVEL_NOT_ALLOWED |
| requested | Create bị từ chối và job tìm được (nếu có) chưa link | stale | SCHEDULE_REFUSED (+ code), giống A1 |
| requested | Attempt đã start và pre-gate đạt (trong `record_generation`) | analyzing | — |
| requested/analyzing | Cancel nội bộ | cancelled | CANCELLED_BY_TEACHER |
| requested/analyzing/pending_teacher_review | Owner notice, hoặc cổng hiện hành không đạt | stale | CONSENT_REVOKED, SESSION_ENDED, TURN_REVOKED, CANVAS_RESTORED, CONTEXT_CHANGED, SOURCE_CHANGED, MEANING_CHANGED, AUDIENCE_CHANGED, ANALYSIS_NOT_APPLICABLE, POLICY_CHANGED, ARTIFACT_QUARANTINED (thêm ở revision 4) |
| analyzing | Job SUCCEEDED/ACCEPTED, staged khớp, cổng đạt | pending_teacher_review | — |
| analyzing | Job SUCCEEDED/STALE | stale | CONTEXT_CHANGED |
| analyzing | Job BLOCKED_UNSAFE | blocked_unsafe | UNSAFE_CONTENT |
| requested/analyzing | Job FAILED_EXHAUSTED | failed | PROVIDER_TIMEOUT / PROVIDER_UNAVAILABLE / PROVIDER_ERROR / OUTPUT_MALFORMED |
| requested/analyzing | Job CANCELLED không do 04 cancel | stale | JOB_CANCELLED (+ code) |
| pending_teacher_review | `revise_level` | Version mới ở requested; version cũ vào lịch sử với SUPERSEDED_BY_REVISION | — |
| pending_teacher_review | Cancel | Không đổi; trả `INVALID_STATE` | — |
| approved/rejected | — | Chỉ 05 được ghi | — |

Mapping moderation:

- requested/analyzing → `not_applicable`;
- pending_teacher_review → `pending`;
- blocked_unsafe → `blocked`;
- cancelled/stale/failed: giữ giá trị trước đó.

Gọi giai đoạn đang generation là "analyzing" là cách hiểu P, vì enum SRS không có "generating".

### 5.3 Invariant

- **Source bất biến.** 04 không có port ghi canvas/source; test so hash source/checkpoint/render
  trước và sau. Output chỉ là text và asset; part nằm ngoài tập đóng (ví dụ `canvas_operations`)
  → OUTPUT_MALFORMED. Derivative mang `origin ai_derived`, `source_refs` trỏ tới render ref/sha,
  và `producer_ref` của adapter. Không ghi đóng góp nào cho Child.
- **Không tự duyệt.** Không có transition hay command nào dẫn tới `approved`, `rejected` hay
  `passed`. `approval_ref` và `child_response` luôn null.
- **Mỗi version promote đúng một attempt.** Điều kiện promote: `job.active_attempt ==
  staged.attempt`; `job.result_refs` (ref+sha) đúng bằng tập staged; artifact chưa bị quarantine
  và đúng producer.
- **Output không được trùng source.** Asset có sha bằng sha của render → OUTPUT_MALFORMED (TC-15).

## 6. Ports, service, adapters, fakes

### 6.1 Ports (`application/ports/sketch_generation.py`)

| Port | Method | Ghi chú |
|---|---|---|
| `SketchHandoffReader` | `resolve(org, assistance_id) -> SketchHandoffV1 \| HandoffRefusal`; `current(binding) -> SketchCurrentState` | Adapter A (§3.2). `SketchHandoffV1` và `SketchCurrentState` là type của 04 (N01). `current` trả applicability của 02, meaning basis, audience/roster hiện hành, trạng thái 03 |
| `SketchDecisionPort` | `token(org, artifact_refs=()) -> DecisionToken` | Đọc epoch đã commit (§7.2a). Chain: đọc `FakeOwnerFences` bên trong `coordinator.read`. Unit test: counter fake |
| `SketchPolicyPort` | `current(org, session) -> SketchPolicySnapshot \| None` | Đề xuất phía consumer gửi BE2-14 (như A1 D10); FIXTURE_ONLY |
| `SketchGenerator` | `generate(request) -> Succeeded \| Failed` | Chạy ngoài mọi transaction; domain không import SDK |
| `DerivedArtifactAdmissionPort` | `stage(org, job_id, attempt_id, part_key, body, media_type, provenance) -> StagedArtifact \| AdmissionRefusal` | ASSUMED_CONTRACT cho `ArtifactReferenceV1` của P2. Idempotent theo `(job, attempt, part_key)`. Foundation phải `describe` được artifact kèm producer lineage |
| `SketchProposalRepository` | `transaction() -> SketchUnitOfWork` | CAS theo record_version; unique handoff key; staged theo attempt; receipts; inbox hint; events; cleanup intents; notices. UoW có `require_token(token)`: kiểm lại token bên trong boundary commit, lệch → `StaleDecision` và rollback toàn bộ unit |
| `SketchJobPort` | `create(...)`, `cancel(principal, job_id, expected_revision)` | Đi qua `AiJobService` |
| `SketchJobReader` | `get(job_id)`, `find_semantic(key)` | Read-only qua `AiJobRepository`; không scan `list_jobs` |
| `SketchCopyPort` | `register(copy)` | Qua `ProviderCopyLifecycleService.register_copy` |
| `SketchAuthorityPort` | `decide(principal, scope, action)`, `disclose(principal, scope)` | Teacher theo class; Child chỉ có device view |
| `ClockPort`, `IdGeneratorPort` | — | Dùng lại của foundation |

### 6.2 Service (`application/services/sketch_generation.py`)

Các method:

- Mở và lên lịch: `open_from_handoff`, `process_inbox(org)`, `schedule(proposal_id)`.
- Worker và reconcile: `record_generation(job_id, attempt_id, correlation_id) -> GenerationClaim`,
  `reconcile(proposal_id)`.
- Control: `cancel(cmd)`, `revise_level(cmd)`, `apply_owner_notice(notice)`, `deliver_cleanup()`.
- Đọc: `get_record(principal, proposal_id)`, `device_view(principal, assistance_id)`.
  `get_record` kiểm applicability hiện hành trước khi trả nội dung (§4.1). Read không bao giờ
  commit. Khi thấy không còn hiện hành, read chỉ ghi hint revalidate vào inbox bằng một unit
  riêng sau khi read xong; read vẫn trả kết quả đã giữ lại nội dung dù unit đó có lỗi.
- `revalidate(proposal_id)`: chạy lại cổng C8 cho proposal đang `pending_teacher_review`, có
  token, và stale nếu không còn hiện hành. Đây là đường xử lý thay đổi xảy ra sau commit (§7.2b).
- Các quyết định phụ thuộc lần đọc bên ngoài (C1, C5, C8, `revise_level`, `revalidate`) chạy
  vòng `token → đọc → quyết định → commit có require_token`, tối đa `DECISION_ROUNDS = 2` (như
  A1). Hết vòng mà token vẫn đổi → `DECISION_UNRESOLVED`, không ghi gì; caller thử lại sau.

Code ở tầng application không được chứa chuỗi `sketch2life.infrastructure`. Validator kiến trúc
(dòng 31–34) so khớp theo chuỗi, kể cả trong docstring.

### 6.3 Adapters (`infrastructure/sketch_generation/adapters.py`)

- **`AssistanceHandoffReader`**: như §3.2. Kiểm audience bằng `AssistanceOwnerPort.roster/canvas`
  của A1; roster revision hoặc members khác pin → AUDIENCE_CHANGED (cùng facts mà A1 đưa vào
  digest).
- **`SketchEligibility`**: decorator cho `EligibilityPort` của foundation.
  - Với job type `sketch_generation`, yêu cầu: proposal tồn tại, cùng org,
    `version == request_ref.request_revision`, `generation_digest == request_ref.input_hash`,
    state ∈ {requested, analyzing}. Không đạt → ineligible kèm reason.
  - Sau đó gọi inner (owner), trả fence/context_revision của inner.
  - Job type khác đi thẳng xuống inner.
  - Trong chain, đọc state đã commit của 04 bên trong `coordinator.read(...)`, giống
    `AssistanceEligibility` của A1 (adapters.py 186–223).
- **`CoordinatedSketchRepository`** (chỉ dùng trong chain; SK-PR01): decorator quanh
  `InMemorySketchStore`. Mỗi unit của 04 chạy trong `coordinator.assistance()` — API public đã
  có của A1, A1 không phải sửa.
  - Unit này loại trừ lẫn nhau với các unit foundation/vision và với owner publication; mọi
    publication đều chạy dưới lock của coordinator (fakes.py 97–176).
  - Nếu unit được mở bên trong một unit foundation/vision, coordinator đã ném
    `CoordinationError` → hook phải `request_publication` (deferred), không publish lén.
  - `require_token` đọc lại epoch ngay trong unit trước inner commit.
  - Khi có transition invalidating, bump `eligibility:<org>` sau inner commit và trước khi nhả
    unit (giống `InMemoryAssistanceStore`, fakes.py 318–345).
  - Tên kind "assistance" là của A1; 04 chỉ dùng lại, không thêm kind mới.
- **`FenceDecisionPort`** (chain): `token` = `(epochs["eligibility:<org>"],
  epochs["analysis:<org>"], epochs["sketch-policy:<org>"], epochs["artifact:<ref>"]…)` đọc
  trong `coordinator.read`. Hai scope đầu chính là `decision_epoch` của A1 (fakes.py 221–226).
- **`CoordinatedSketchArtifactPort`** (chain; SK-PR01-F1): implement `ArtifactPort` trên cùng
  backing `h.artifacts` (`FakeArtifacts`).
  - `describe(ref)` đọc trong `coordinator.read`.
  - `quarantine(intent)` và `owner_quarantine(refs, reason)` gọi backing qua
    `coordinator.request_publication(...)`:
    - Ngoài mọi unit: chạy ngay, đồng bộ, dưới lock của coordinator; lỗi được ném lại cho caller.
      Foundation khi đó giữ intent pending để `deliver_side_effects` giao lại (services/ai_jobs.py
      1215–1229).
    - Trong một unit (chỉ xảy ra với hook của test): deferred tới khi unit ngoài cùng nhả lock,
      dù unit commit hay rollback. Lỗi deferred nằm trong `coordinator.deferred_failures`; test
      phải kiểm danh sách này.
  - Log kiểm toán: mỗi lần giao (kể cả giao lại) ghi
    `(caller, event_id hoặc reason, ref, epoch_before, epoch_after, bumped)`. Đọc epoch trước/sau
    ngay trong publication. `bumped` chỉ đúng khi epoch thực sự tăng; dùng cho SK-C10.
  - Có `fail_next_quarantine` cho test: ném lỗi **trước khi** gọi backing, nên không có gì được áp
    dụng. Đây là đường "sink lỗi lần đầu" mà foundation xử lý bằng release lease
    (ai_jobs.py 815–819).
  - **Actor set (revision 5, SK-PR01-F2).** Chỉ có một instance port trong chain; mọi đường làm
    đổi trạng thái quarantine của artifact đều đi qua nó:
    1. `h.jobs` (instance hướng A1): quarantine side effect từ completion (`_deliver_now`) **và**
       drain outbox dùng chung (`deliver_side_effects`), gồm cả intent do Sketch tạo;
    2. `sketch_jobs`: tương tự, cho completion Sketch và drain outbox dùng chung;
    3. C9 `deliver_cleanup` của 04;
    4. owner quarantine trong test qua `h04.owner_quarantine(refs, reason)`.

    Không còn service nào trong chain giữ `FakeArtifacts` thô làm `ArtifactPort`. Bản thô chỉ còn
    được dùng cho `put` (admission 04 và `AssistanceHarness.finish_vision`, harness.py 288) và cho
    assertion chỉ đọc trong test. Drain outbox của bất kỳ instance nào — kể cả intent do instance
    kia tạo — đều áp dụng dưới publication lock.
  - Revision 4 viết "`h.jobs` vẫn dùng `h.artifacts` thô, không bao giờ quarantine ref 04" là sai.
    `_owned_descriptors` (ai_jobs.py 1281–1295) chỉ bảo vệ lúc *tạo* intent; `deliver_side_effects`
    (789–829) giao mọi intent pending trong repository dùng chung (SK-PR01-F2).
  - Vision ref cũng đi qua cùng port. Thứ tự và kết quả không đổi so với sink thô khi caller ở
    ngoài mọi unit (`request_publication` chạy ngay, đồng bộ). Khác biệt duy nhất là phải chờ lock
    nếu đang có unit của 04/03 giữ lock.
  - Không sửa `FakeArtifacts` hay source foundation/A1.
- **`AiJobSketchPort`, `AiJobSketchReader`**: `get_job`; `find_semantic` bằng một
  `SemanticRequestKey` dựng lại.
- **`SketchProviderAdapter`**: implement `AiProviderPort`. `run(message)` gọi `record_generation`
  rồi dựng `CompletionClaim`:
  - SUCCESS kèm outputs, moderation PASSED hoặc UNSAFE;
  - FAILURE không kèm output, mã thuộc 4 mã worker.
- **`SketchStageAdapter`**: implement `SketchStagePort`; chỉ ghi hint, không ném lỗi.
- **`SketchCopyRegistrar`**: bọc `ProviderCopyLifecycleService`.

### 6.4 Fakes (`infrastructure/sketch_generation/fakes.py`)

- **`InMemorySketchStore`**: commit staged all-or-nothing; có `fail_next_commit` và hook trước
  commit. Khi có transition invalidating, bump fence `eligibility:<org>` trên `FakeOwnerFences`
  dùng chung, như A1. Khi chạy độc lập (unit test), có lock riêng và kiểm token qua
  `CounterDecisionPort`.
- **`CounterDecisionPort`**: counter epoch cho unit test; test có thể bump giữa "lần đọc cuối"
  và commit bằng hook.
- **`FixtureSketchPolicy`** có version. Mọi thay đổi policy trong chain đi qua
  `coordinator.request_publication` và bump `sketch-policy:<org>`.
- **`ScriptedSketchGenerator`**: script theo attempt, đếm số lần gọi theo proposal. Sinh text và
  byte có PNG signature — chỉ là chữ ký cấu trúc, không decode được.
- **`FixtureDerivedArtifactAdmission`**:
  - allowlist `image/png` (ảnh) và `application/json` (result document);
  - giới hạn ≤ 10 485 760 B; kiểm PNG signature; tính lại sha;
  - ghi qua `FakeArtifacts.put(job_id, attempt_id)`;
  - giữ map key → ref để idempotent, vì `put` của fake tạo ref mới mỗi lần gọi.
- **`FixtureSketchPolicy`**, **`FakeSketchAuthority`**, **`ScriptedHandoffReader`** (cho unit test
  của service).

### 6.5 Chain harness (`infrastructure/sketch_generation/harness.py`)

- **Builder riêng `build_sketch_chain_harness()`** (revision 5, SK-PR01-F2). Không gọi
  `build_assistance_harness()`, vì builder đó truyền `FakeArtifacts` thô cho `h.jobs` và không nhận
  injection (harness.py 370–388).
  - Builder 04 dựng lại cùng composition chỉ từ các thành phần public của A1, không sửa file A1:
    `AssistanceCommitCoordinator`, `HookedOwnerFences`, `InMemoryAiJobStore`,
    `CoordinatedAiJobRepository`, `FakeEligibility`, `InMemoryAssistanceStore`,
    `AssistanceEligibility`, `FakeAuthorization`, `FakeArtifacts`, `FakeQueue`,
    `FakeWorkerCapability`, các fake owner/authority/source/policy của A1, Vision service + fakes,
    `VisionAnalysisOutcomes`, `AiJobServicePort`, `AiJobRepositoryReader`,
    `RecordingSketchStage`, `AssistanceService`; dùng cùng hằng fixture và helper (`make_source`,
    `fixture_policy`, …).
  - Builder trả về một `AssistanceHarness` (dataclass public, harness.py 155) chứa các object vừa
    dựng, cùng với phần 04. Các method A1 (`submit`, `finish_vision`, `publish_owner_change`, …) vì
    vậy chạy trên composition này.
  - Khác biệt duy nhất so với builder A1: `artifact_port = CoordinatedSketchArtifactPort(
    raw_artifacts, coordinator)` được dựng **một lần** và truyền làm `artifacts` cho **cả hai**
    `AiJobService`:
    - `h.jobs` (hướng A1, eligibility `AssistanceEligibility` như A1);
    - `sketch_jobs` (eligibility `SketchEligibility(inner=h.eligibility)`, `FIXTURE_RETRY_POLICY`).
  - `AssistanceHarness.artifacts` = `raw_artifacts`, chỉ dùng cho `put`.
  - SK-C11 kiểm builder 04 cho cùng hành vi A1 với builder A1, để bản dựng lại không lệch khỏi A1.
- Cấp `READER` trong `h.authority.teachers` (cấu hình fixture).
- Admission 04 vẫn ghi qua `FakeArtifacts.put` (tạo artifact mới, chưa ai tham chiếu, không bump
  fence của ref đã có), nên không cần điều phối.
- `AiJobService` chỉ giữ deps (dòng 337–339), nên hai instance nhất quán với nhau. Sweeps và
  dispatch của sketch job chạy qua instance sketch. (Revision 2 viết "nếu instance A1 chạm vào
  sketch job thì start vẫn bị chặn" — sai, xem SK-PR02; thay bằng router bên dưới.)
- Store 04 trong chain được bọc bằng `CoordinatedSketchRepository`, dùng chung coordinator và
  fences của composition do builder 04 dựng (`h.coordinator`, `h.fences`).
- Harness chuyển `h.sketch.intents` (RecordingSketchStage) vào inbox của 04 để mô phỏng hint.
  Test có thể bỏ hint để mô phỏng callback bị lỡ.
- **`JobTypeRouter`** (SK-PR02) là **consumer duy nhất** của `h.queue` trong mọi test chain/race
  của 04. `run_next()` lấy envelope ở đầu queue, đọc `envelope.message.job_type` **trước** mọi
  `start_attempt`, rồi route:
  - `vision_analysis` → `started = h.jobs.start_attempt(envelope.capability, …)`. **Chỉ khi
    `started.started` là True** mới đặt `h.last_envelope = envelope` rồi gọi
    `h.finish_vision(job_id, attempt_id)`. Đây là đúng guard mà A1 `run_vision` dùng
    (harness.py 302–305), vì `finish_vision` (266–297) không tự kiểm (SK-PR02-F1);
  - `sketch_generation` → `started = sketch_jobs.start_attempt(envelope.capability, …)` (qua
    SketchEligibility). **Chỉ khi `started.started` là True** mới gọi `adapter.run(message)` rồi
    `sketch_jobs.accept_completion(envelope.capability, claim)`;
  - `started.started` False ở bất kỳ nhánh nào (DUPLICATE_DELIVERY, ATTEMPT_NOT_ACTIVE,
    JOB_NOT_QUEUED, eligibility từ chối, STALE_CONTEXT) → trả
    `RouteResult(job_type, job_id, started=False, reason)`. Không gọi observation, provider,
    `finish_vision` hay `accept_completion`, không đặt `h.last_envelope`, không redeliver (start đã
    quyết định xong envelope này). Lần `run_next()` sau xử lý envelope kế tiếp;
  - type khác → `h.queue.redeliver(envelope)` và raise trong test.

  Capability gốc được chuyển nguyên; không envelope nào bị bỏ. Test 04 không gọi `h.start_next()`,
  `h.run_vision()` hay `FakeWorker` trên queue dùng chung khi queue có thể chứa Sketch.
  `FakeWorker` chỉ còn dùng trong unit test có queue riêng của 04.

## 7. Luồng, commit protocol và recovery

### 7.1 Các commit

Mỗi bước là một transaction cục bộ; không có atomic xuyên feature.

| # | Chủ | Commit |
|---|---|---|
| C0 | 03 | Handoff `analysis_ready` (bất biến, D11). Nằm ngoài 04 |
| C1 | 04 | Open (có token, §7.2a): insert proposal v1 `requested` (hoặc `stale`/`failed`), unique handoff key, schedule identity đóng băng (`create_key = "sketch:<id>:<v>:generate"`, requester đã đóng băng), event |
| C2 | 01 | `create_job` (receipt + semantic key) |
| C3 | 04 | Link job (CAS). Nếu mất reply: gửi lại đúng lệnh cũ → replay → link. Nếu bị từ chối: `find_semantic`; job đã link thì giữ nguyên; job chưa link thì đưa vào cleanup và chuyển stale(SCHEDULE_REFUSED) (tương đương A1-R14) |
| C4 | 01 | `start_attempt` (qua SketchEligibility) |
| C5 | 04 | `record_generation` chạy pre-gate rồi CAS requested→analyzing **có token**: thay đổi commit giữa pre-gate và C5 sẽ bị bắt, nên không gọi provider theo quyết định cũ. Nếu job chưa link mà request_ref khớp thì link luôn |
| — | — | Đăng ký copy INPUT/JOB (ghi claim trước khi gọi), gọi generator (ngoài tx), validate (domain), chạy post-gate với trạng thái hiện hành |
| C6 | ngoài/04 | Stage artifact (result document + asset) qua admission; đăng ký copy OUTPUT/CACHE; insert-once `StagedGeneration` theo `(job, attempt)`. **Không cần token**: C6 không làm gì có thể nhìn thấy; C7 (eligibility của foundation) và C8 (token) đều kiểm lại |
| C7 | 01 | `accept_completion` |
| C8 | 04 | `reconcile` (có token): promote → `pending_teacher_review`, tính `content_sha256`, event `sketch.proposal_ready`; hoặc map theo trạng thái job. Staged không khớp → superseded + cleanup intent |
| C9 | 04/01 | `deliver_cleanup`: gọi `CoordinatedSketchArtifactPort.quarantine(QuarantineIntent)` với event_id tất định (FakeArtifacts dedup), chạy ngoài mọi unit nên publication đồng bộ dưới lock. Lỗi → intent vẫn pending và giao lại ở lần sau (SK-PR01-F1) |

### 7.2 Cổng hiển thị

Chỉ C8 mới biến một version thành reviewable, và chỉ khi đủ tất cả các điều kiện:

- Job SUCCEEDED với disposition ACCEPTED, đúng `request_revision == proposal_version` và
  `input_hash == generation_digest`.
- Staged của active attempt khớp `result_refs`; artifact chưa bị quarantine.
- `current(binding)` đạt: 03 vẫn `analysis_ready` với cùng handoff; 02 còn applicable; meaning
  basis không đổi; audience không đổi.
- Policy vẫn có rule cho level.
- Proposal chưa bị cancel hay stale.

Child không bao giờ nhận nội dung. Fence/eligibility của foundation chỉ giúp giảm việc thừa.
Tính đúng của exposure do C8 quyết định, **với điều kiện các lần đọc của C8 được giữ tới commit
bằng decision token (§7.2a)**. Revision 2 viết "04 không cần coordinator của A1" là sai: CAS của
04 không thấy thay đổi ở 02/owner/policy (SK-PR01).

### 7.2a Decision token

Thành phần token của một org:

| Thành phần | Do ai bump | Bao phủ |
|---|---|---|
| `eligibility:<org>` | Owner publication (`publish_owner_change`, harness.py 314–322); request fence của 03 (fakes.py 310–338); transition invalidating của 04 | Consent, session, tuổi, roster/audience, context revision, render/source, turn, canvas restore |
| `analysis:<org>` | `CoordinatedAnalysisRepository` sau mỗi lần ghi Vision đã commit (adapters.py 161–183) | Teacher confirmation, correction, invalidation của analysis |
| `sketch-policy:<org>` | Publication của fixture policy 04 | Rule level, policy tắt |
| `artifact:<ref>` cho từng ref trong ref-set đã chốt (bên dưới) | `FakeArtifacts.owner_quarantine` (fakes.py 643–649), **chỉ khi được gọi qua `CoordinatedSketchArtifactPort`**, tức là trong `request_publication` dưới lock của coordinator (SK-PR01-F1) | Quarantine artifact do foundation side effect từ **cả hai** instance (completion và drain outbox dùng chung; revision 5, SK-PR01-F2), do C9 cleanup, hoặc do owner |

**Ref-set của token (SK-PR01-F1).** Trước khi lấy `t0`, đọc snapshot đã commit của 04 trong
`coordinator.read`: record proposal (record_version, version hiện hành) và staged generation
liên quan. Từ đó chốt:

- `ref_set` = tập ref artifact mà quyết định sẽ dựa vào:
  - C8: ref của staged generation ứng với `generation_job_ref` hoặc active attempt đọc được lúc
    snapshot (result document + asset);
  - `revalidate` và `get_record`: ref của version đã promote;
  - C1, C5 và `revise_level`: tập rỗng có chủ đích. Các quyết định này không phụ thuộc trạng thái
    artifact: C1/C5 diễn ra trước khi có output; `revise_level` tạo version mới mà không dùng
    nội dung của version cũ.
- `ref_set_id = sha256(proposal_id, record_version, version, staged_key, sorted(ref_set))`.

Token = `(epochs owner/analysis/policy, {ref: epochs["artifact:<ref>"] for ref in ref_set},
ref_set_id)`.

Sau đó, nếu lần đọc job evidence chọn một staged/attempt khác (ví dụ attempt bị thay hoặc
`result_refs` khác) tức ref-set khác `ref_set` → **bỏ quyết định**, không commit, đọc snapshot
mới và lấy token mới. Việc này tính vào cùng giới hạn 2 vòng. `require_token` trong unit kiểm
lại cả epoch lẫn `ref_set_id`: record_version/staged trong unit phải khớp snapshot. Vì vậy
không thể lấy token cho một ref-set rồi commit promote với ref khác.

Vòng quyết định (C1, C5, C8, `revise_level`, `revalidate`):

1. Đọc snapshot đã commit của 04 → chốt `ref_set`. `t0 = decision.token(org, ref_set)`, đọc
   trong `coordinator.read`.
2. Đọc `resolve/current` (03 + hai lần đọc 02 + owner roster), policy, job evidence. Nếu ref-set
   suy ra từ job evidence khác `ref_set` → quay lại bước 1.
3. Quyết định bằng hàm domain thuần.
4. Mở unit 04 (`coordinator.assistance()`), `require_token(t0)` (epoch + `ref_set_id`), CAS
   record_version, ghi state + event (+ bump khi invalidating), commit.
5. `StaleDecision` → quay lại bước 1. Tối đa 2 vòng; vẫn lệch → `DECISION_UNRESOLVED`, không
   ghi gì.

Vì sao đủ trong scope fake một process: mọi lần ghi có điều phối đều chạy dưới lock của
coordinator và bump epoch trước khi nhả lock. Các lần ghi đó gồm: owner publication, Vision
write, policy publication, unit 03/04 và — từ revision 4 — mọi quarantine/cleanup ref 04 qua
`CoordinatedSketchArtifactPort`. Bước 4 giữ chính lock đó trong lúc kiểm token và commit, nên
không thay đổi nào có điều phối lọt vào giữa "kiểm token" và "commit 04". Hai lần đọc tách nhau
của 02 được bao phủ vì cả hai nằm sau `t0`. Đường gọi thẳng `FakeArtifacts.quarantine` hoặc
`owner_quarantine` trên ref 04 không phải actor hợp lệ; SK-C10 bắt nếu có.

Giới hạn ghi rõ:

- Token dựa trên giả định owner bump fence cho mọi thay đổi quyết định (OwnerFence
  ASSUMED_CONTRACT, Δ1). Thay đổi fake không đi qua publication thì token không bắt được; đó là
  vi phạm của fixture, không phải trường hợp hợp lệ.
- Token khác nhau không đồng nghĩa với stale theo nghĩa nghiệp vụ. Ví dụ: child correction bump
  `analysis:<org>` → vòng sau đọc lại, meaning basis không đổi → vẫn promote (TC-07).
- Không claim PostgreSQL isolation hay đảm bảo phân tán (G-11).

### 7.2b Thay đổi trước và sau commit

| Thời điểm thay đổi (theo thứ tự commit thực tế) | Kết quả |
|---|---|
| Commit trước bước 4 của C8 | Token lệch → quyết định lại → stale đúng reason (hoặc promote nếu không đổi về nghiệp vụ); không phát `proposal_ready` theo quyết định cũ |
| Commit sau C8 | Tại thời điểm C8, proposal hợp lệ là `pending_teacher_review`. Sau thay đổi: mọi `get_record` kiểm hiện hành và giữ lại nội dung; owner notice hoặc `revalidate` chuyển `stale` + review_revision +1; 05 phải revalidate trước khi review (G-05). Không claim "proposal không bao giờ đổi" |
| Thay đổi trong lúc đang chạy unit 04 | Không xảy ra: publication (kể cả quarantine ref 04) bị chặn tới khi unit nhả lock. Hook nằm trong unit foundation/vision/04 chỉ có thể request publication (deferred) |
| Quarantine ref 04 commit trước bước 4 của C8 | Token lệch (`artifact:<ref>`) → vòng sau: artifact bị quarantine → không promote; `stale` (ARTIFACT_QUARANTINED) |
| Quarantine ref 04 được yêu cầu trong lúc unit C8 đang chạy | Chờ tới khi unit commit; promote đã commit trước, rồi quarantine áp dụng. Sau đó `get_record` giữ lại nội dung (artifact bị quarantine) và `revalidate` → `stale` (ARTIFACT_QUARANTINED) + review_revision +1 |

### 7.3 Crash và recovery (fault injection trong một process)

| Điểm hỏng | Kết quả bắt buộc |
|---|---|
| Callback bị lỡ / request cache-hit | Không có proposal cho tới khi có lệnh open theo id; open sau đó chạy đúng (discovery: G-02) |
| Sau C2, trước C3 | `schedule` lặp lại → replay ra cùng job → link |
| Sau C4, trước khi gọi generator | Attempt hết hạn (`expire_overdue_attempts`) → retry → attempt mới |
| Sau generator, trước C6 | Như dòng trên. Copy INPUT/JOB đã được đăng ký. Artifact chưa ghi, hoặc đã ghi mà không ai tham chiếu, không bao giờ được hiển thị (cleanup artifact mồ côi: G-10) |
| Sau C6, trước C7 | Retry bằng attempt mới. Staged cũ không bao giờ được promote; reconcile đánh dấu superseded và quarantine |
| Sau C7, trước C8 | Reconcile chạy sau sẽ promote đúng một lần; gọi lại không có tác dụng |
| Commit 04 hỏng (open/link/stage/finalize/cancel/notice) | Không để lại trạng thái dở; thử lại thành công; không deadlock |
| Worker giao trùng | Start trả DUPLICATE_DELIVERY; `record_generation` replay trả đúng claim đã lưu (cùng fingerprint) |

Không claim: crash đa process, PostgreSQL isolation, outbox durable, exactly-once với provider.
Theo CS-023, store chỉ nằm trong bộ nhớ không đạt yêu cầu recovery.

### 7.4 Cancel, owner notices, revision

**Cancel** (nội bộ, Teacher có disclosure):

- Receipt theo `(org, principal, "SketchGenerationCancelV1", proposal_id, key)`; fingerprint là
  `{proposal_id, if_match, reason}`.
- Thiếu key → MALFORMED. Thiếu If-Match → PRECONDITION_REQUIRED. If-Match cũ →
  PRECONDITION_FAILED. Cùng key khác payload → IDEMPOTENCY_PAYLOAD_MISMATCH.
- Từ requested/analyzing → `cancelled`, bump fence; sau commit, cancel job theo best-effort bằng
  principal của người cancel.
- Từ `pending_teacher_review` → INVALID_STATE. Principal của Child → FORBIDDEN_SCOPE. Đường cancel
  từ Child hoặc qua route public là G-04.

**Owner notices** (consent_revoked / session_ended / turn_revoked / canvas_restored):

- Idempotent theo notice_id.
- Áp cho các proposal khớp đang requested/analyzing/pending_teacher_review → `stale`, tăng
  review_revision, cleanup job (giống A1 §8.5; TC-08).

**`revise_level`** (caller tin cậy đại diện 05, Teacher có disclosure):

- Chỉ từ `pending_teacher_review`. If-Match là ETag. Level mới phải có rule.
- Có decision token (policy có thể đổi giữa lúc đọc và lúc commit).
- Tạo version N+1 ở `requested` với schedule mới; review_revision +1; event `sketch.superseded`.
  Version N được giữ trong lịch sử và không còn reviewable.
- Level của version N+1 lấy từ lệnh revision (SK-PR03); `level_source = revision{receipt_ref}`.
  Output rule, `generation_digest`, `RequestRef` (nên cả semantic key của job) và về sau
  `content_sha256` của N+1 đều tính bằng level mới. Request 03, `requested_level` và level/nguồn
  của v1 không đổi. Equality với `requested_level` của 03 chỉ kiểm khi mở v1.
- Receipt/idempotency giống cancel.
- Revision sau khi đã approve cần contract của 05 (G-05).

## 8. Policy, budget, copy và seams nối sau

- **Fixture policy** `fixture.sketch_generation.v0` (FIXTURE_ONLY_NOT_ADOPTED):
  - `level_fx_1` → side_reference, bắt buộc text, cấm asset.
  - `level_fx_2` → overlay, bắt buộc asset, text tùy chọn.
  - Asset `image/png` ≤ 10 485 760 B; text ≤ 4000 ký tự.
  - `generator_profile_ref = fixture-sketch-profile-v0`; purpose `ai_drawing_assistance`.
  - Đây là gán fixture cho các token opaque của A1, không phải taxonomy.
- **Budget.** 04 không có ledger. Kill switch, budget và consent đi qua quyết định eligibility
  của owner (fake; `BUDGET_EXCEEDED` và `KILL_SWITCH` đã có sẵn). Số lần gọi provider bị giới hạn
  bởi retry fixture của foundation. Kế toán cho stage Sketch chưa có owner (A1 D8 không reserve)
  → G-07.
- **Copy.**
  - Đăng ký INPUT/JOB trước khi gọi provider; OUTPUT/CACHE sau khi có kết quả.
  - `scope_ref = sketch_proposal:<id>` (TC-11); dùng profile fixture của
    `FakeProviderCopyAdapter`.
  - Discover/cancel/purge qua `ProviderCopyLifecycleService`. Report có `fixture_marker=true`,
    `actual_deletion_proven=false`.
  - Authority theo session/subject của BE1-15 là G-09.
- **Seams với BE2-14 của người bạn.** Chỉ đối chiếu theo snapshot local `be64b999…`; không merge,
  không copy code.
  - `PolicyUseAccess` (pin/phase) ↔ các phase create/start/complete/finalize của 04.
  - `ResourceAccountingAccess` (quote/settlement theo attempt) ↔ usage theo attempt của 04.
  - `ProviderCopyOperationHook` (original profile, `operation_key` ổn định, chạy ngoài
    transaction) ↔ adapter copy thật của 04.
  - Người dùng sẽ tự nối sau (G-07, G-09).

## 9. Acceptance

"Chain" nghĩa là 01/02/03 thật chạy trên fakes qua harness của A1, cộng 04. "Races" nghĩa là
interleaving tất định hoặc fault injection.

File test (dưới `backend/`):

| Viết tắt | File |
|---|---|
| dom | `tests/unit/test_sketch_proposal_domain.py` |
| svc | `tests/unit/test_sketch_generation_service.py` |
| adp | `tests/unit/test_sketch_generation_adapters.py` |
| chain | `tests/unit/test_sketch_generation_chain.py` |
| races | `tests/unit/test_sketch_generation_races.py` |
| contract | `tests/contract/test_sketch_proposal_contracts.py` |
| ex | `tests/contract/test_sketch_proposal_examples.py` |

### 9.1 Positive

| ID | Given / when | Expected | Test |
|---|---|---|---|
| SK-P01 | Child gửi request trên personal canvas → A1 `analysis_ready` → hint → open → job → generation (level_fx_2) → completion → reconcile | v1 `pending_teacher_review`, moderation `pending`, có `content_sha256`. Derivative ai_derived, có source_refs. Hash source/checkpoint/render không đổi. Device view `pending`, không có nội dung | chain |
| SK-P02 | level_fx_1 | Chỉ có `text_or_question`; `overlay_asset_ref` null; display side_reference; result document artifact có mặt | svc, chain |
| SK-P03 | Teacher gửi request cho nhóm có tuổi khác nhau | `audience_participant_ids` bằng audience đã ghim; job subject_refs bằng audience | chain |
| SK-P04 | Request cache-hit của A1 (không có hint), open theo id | Có proposal riêng; analysis_ref thuộc request gốc; `handoff_kind=cache_hit`; có job mới | chain |
| SK-P05 | Adapter callback | Hint vào inbox; `process_inbox` mở proposal; adapter không ném lỗi kể cả khi store 04 hỏng | adp |
| SK-P06 | Open lặp lại (hint + id, gọi nhiều lần) | Cùng một proposal; một job; generator chỉ được gọi một lần | svc, chain |
| SK-P07 | Attempt 1 lỗi retryable, attempt 2 thành công | Chỉ staged của attempt 2 được promote | chain |
| SK-P08 | `revise_level` từ pending (request 03 ở level_fx_1; v1 level_fx_1 → v2 level_fx_2) | v2 `requested` rồi `pending`; review_revision tăng; v1 vào lịch sử, không reviewable; có job mới. Record v2 có `assistance_level=level_fx_2`, `level_source=revision`; request 03 (`requested_level`, `request_revision`) không đổi (SK-PR03) | svc, chain |
| SK-P11 | Sau SK-P08, kiểm tính đồng nhất của v2 | Output rule của v2 (overlay, bắt buộc asset), `generation_digest`, `RequestRef` của job v2 và `content_sha256` đều tính bằng level_fx_2; job v2 khác semantic key với job v1; v1 giữ level_fx_1 + `level_source=request` trong lịch sử | dom, chain |
| SK-P09 | Teacher có disclosure đọc record | Record đủ field ở §4.1; device view tối thiểu ở mọi trạng thái | svc, contract |
| SK-P10 | Đăng ký copy rồi purge theo scope | Outcome fixture; `actual_deletion_proven=false`; purge cùng key thì replay | svc |

### 9.2 Negative

| ID | Given / when | Expected | Test |
|---|---|---|---|
| SK-N01 | Status của 03 là scheduling/scheduled/cancelled/stale/failed | `HANDOFF_NOT_READY`, không tạo record, audit `sketch.open_refused` | svc |
| SK-N02 | Hint lệch với read (analysis/revision/request_revision) | `HANDOFF_MISMATCH`, không tạo record | svc |
| SK-N03 | Reader khác org, mất disclosure, hoặc không phải Teacher | `HANDOFF_UNREADABLE`; không lộ việc resource có tồn tại | svc, adp |
| SK-N04 | Analysis không accepted, meaning not_applicable, hoặc lineage/source của 02 khác pin của 03 | Record `stale` (ANALYSIS_NOT_APPLICABLE) hoặc refuse MISMATCH; không job, không gọi provider | svc, chain |
| SK-N05 | Policy thiếu/tắt, level không có rule, purpose lệch | Record `failed` với reason tương ứng; không job | svc |
| SK-N06 | Lúc open: consent đã thu hồi, session đã kết thúc, tuổi ngoài phạm vi, hoặc roster đã đổi | `stale` kèm reason; không job | chain |
| SK-N07 | `create_job` bị từ chối (requester mất quyền, BUDGET_EXCEEDED, KILL_SWITCH) | `stale` (SCHEDULE_REFUSED + code); không gọi provider | chain |
| SK-N08 | `record_generation` với job type sai, attempt không active, job không running, request_revision hoặc digest lệch, version lệch | Refuse trước khi gọi provider; không có staged | svc, chain |
| SK-N09 | Context, correction (Teacher confirm), consent, source hoặc audience đổi sau open, trước khi gọi provider | Pre-gate → `stale`; không gọi provider; foundation cancel job qua eligibility | chain |
| SK-N10 | Như N09 nhưng xảy ra trong lúc provider đang chạy | Post-gate → `stale`; không stage, không promote; copy đã đăng ký vẫn còn | chain |
| SK-N11 | Output hỏng: thiếu part bắt buộc; có part bị cấm; text rỗng, quá dài hoặc có control char; media type ngoài allowlist; vượt giới hạn byte; thiếu PNG signature; sha lệch; trùng render; part kind lạ | FAILURE OUTPUT_MALFORMED, không retry → `failed`; không có staged | dom, svc, chain |
| SK-N12 | Generator báo unsafe (fixture) | Claim UNSAFE → job blocked_unsafe, foundation quarantine → `blocked_unsafe`, moderation `blocked`. Teacher chỉ thấy reason; có event; Child thấy `unavailable` | chain |
| SK-N13 | Tín hiệu timeout, hoặc attempt quá hạn | Retry tới khi hết `FIXTURE_RETRY_POLICY` → `failed` (PROVIDER_TIMEOUT). Completion đến muộn của attempt đã hết hạn → disposition STALE, output bị quarantine, không promote | chain |
| SK-N14 | Provider unavailable/error cho tới khi hết retry | `failed` với reason đúng | chain |
| SK-N15 | Cancel trước start; cancel trùng key; cùng key khác payload; If-Match cũ; thiếu key | Lần lượt: `cancelled` + job cancelled + start bị từ chối, không gọi provider / replay / 409 / 412 / 400 | svc, chain |
| SK-N16 | Cancel sau khi đã pending; principal Child cancel | INVALID_STATE / FORBIDDEN_SCOPE | svc |
| SK-N17 | Child đọc proposal ở mọi trạng thái; Teacher lớp khác đọc | Chỉ có status / NOT_FOUND; không text, asset hay ticket | svc |
| SK-N18 | Tìm đường ghi canvas/stroke | Không có dependency ghi canvas; hash source không đổi; part `canvas_operations` bị từ chối | dom, chain |
| SK-N19 | Record do 04 tạo có approved/rejected, approval_ref hoặc child_response | Producer không bao giờ tạo; schema từ chối field thừa | dom, contract |
| SK-N20 | `revise_level` từ requested/analyzing/blocked/cancelled; level không có rule; If-Match cũ (kể cả ETag của v1 sau khi đã có v2); replay; cùng key khác payload | Lần lượt: INVALID_STATE / 422 / 412 / trả kết quả gốc (không tạo v3) / 409 | svc |
| SK-N23 | Proposal đang `pending_teacher_review`; publish thay đổi consent / Teacher confirmation / render / policy sau C8; Teacher đọc record trước khi có notice hay revalidate | Nội dung null + `content_withheld_reason`; read không mutate; có hint revalidate; `revalidate` sau đó → `stale` + review_revision +1. Không có thay đổi → read trả đủ nội dung | svc, chain |
| SK-N24 | (a) Mở v1: level của v1 phải bằng `requested_level` trong `SketchHandoffV1` (open không nhận level từ caller; SketchIntent không mang level). (b) `requested_level` của 03 không có rule. (c) Mở lại cùng request sau khi đã có v2 | (a) v1 ghi đúng `requested_level`, `level_source=request`. (b) `failed` (LEVEL_NOT_ALLOWED). (c) Trả proposal hiện có (đang ở v2), không tạo version, không đổi level về `requested_level` | svc |
| SK-N21 | Owner notice khớp; không khớp; gửi lặp | `stale` + review_revision tăng + cleanup / không đổi / bỏ qua | svc, chain |
| SK-N22 | Child correction (không phải Teacher confirmation) sau open | Không stale vì meaning basis không đổi; `analysis_revision` mới chỉ ghi vào provenance | chain |

### 9.3 Races và recovery

| ID | Given / when | Expected | Test |
|---|---|---|---|
| SK-R01 | Open đồng thời (hint + id) | Một proposal | races |
| SK-R02 | Mất reply sau khi create commit; schedule gửi lại | Cùng job; link | races |
| SK-R03 | Requester mất quyền trước khi gửi lại sau mất reply | `find_semantic` tìm thấy job mồ côi → cleanup; `stale` (SCHEDULE_REFUSED); start bị từ chối; không có job thứ hai | races |
| SK-R04 | Cancel commit trước create / giữa create và link | Create bị eligibility từ chối / CAS link thua → cleanup cancel; start bị từ chối | races |
| SK-R05 | Cancel giữa start và generator | Pre-gate từ chối; không gọi provider | races |
| SK-R06 | Hook nằm trong cửa sổ post-hold/pre-commit của completion (unit foundation) muốn cancel | Mở unit 04 bên trong unit foundation → `CoordinationError`; đường đúng là hook `request_publication(cancel)` → cancel được deferred và commit sau khi completion commit. Job SUCCEEDED; reconcile thấy cancelled → không promote, quarantine; ghi lại thứ tự commit thực tế "completion trước, cancel sau" | races |
| SK-R07 | Reconcile và cancel tranh CAS | Bên nào commit trước thắng. Promote trước → cancel trả INVALID_STATE. Cancel trước → reconcile không làm gì và cleanup | races |
| SK-R08 | Crash sau C6, trước C7 | Attempt hết hạn → retry → attempt mới được promote; staged cũ superseded + quarantine; một proposal | races |
| SK-R09 | Crash sau C7, trước C8 | Reconcile chạy muộn promote đúng một lần | races |
| SK-R10 | Worker giao trùng | DUPLICATE_DELIVERY; provider chỉ được gọi một lần; claim replay | races |
| SK-R11 | Commit 04 hỏng ở từng bước | Không để lại proposal/receipt/event/staged dở; thử lại thành công | races |
| SK-R12 | Bỏ hint (callback bị lỡ) | Không có proposal cho tới khi open theo id | races |
| SK-R13 | C8: sau lần đọc hiện hành cuối, trước unit commit, hook `publish_owner_change(revoke_consent)` | `require_token` lệch → vòng 2 đọc lại → `stale` (CONSENT_REVOKED); không có `proposal_ready`, không có `content_sha256` | races |
| SK-R14 | C8: Teacher confirmation commit **giữa** `analysis_record` và `downstream_meaning` (hai lần đọc tách nhau) | Token lệch → vòng 2 → `stale` (MEANING_CHANGED); không promote theo record cũ + meaning mới | races |
| SK-R15 | C8: publish render mới (`set_render` qua publication) trong cửa sổ | Vòng 2 → `stale` (SOURCE_CHANGED) | races |
| SK-R16 | C8 và `revise_level`: publish policy bỏ rule của level trong cửa sổ | Vòng 2 → `stale` (POLICY_CHANGED) / `revise_level` → 422; không có version mới | races |
| SK-R17 | C8: child correction (bump `analysis:<org>`, meaning basis không đổi) trong cửa sổ | Vòng 2 đọc lại → promote đúng một lần; không stale (TC-07) | races |
| SK-R18 | Epoch đổi ở cả hai vòng | `DECISION_UNRESOLVED`, không ghi gì; reconcile sau đó (không còn thay đổi) promote/stale đúng | races |
| SK-R19 | C1 và C5 với thay đổi trong cửa sổ (consent revoke / roster đổi) | C1: không tạo `requested` theo quyết định cũ (vòng 2 → `stale`). C5: không chuyển `analyzing`, không gọi provider | races |
| SK-R20 | `fail_next_commit` sau khi `require_token` đạt | Rollback toàn bộ: không state/event/bump epoch; coordinator rảnh (không deadlock); thử lại thành công | races |
| SK-R21 | Đối chứng: không có thay đổi nào trong cửa sổ | Promote đúng một lần ngay vòng 1 | races |
| SK-R22 | Queue dùng chung: Vision của request B và Sketch của request A xen kẽ theo cả hai thứ tự; xử lý bằng `JobTypeRouter.run_next()` | Mỗi job start qua đúng service (Vision qua `h.jobs`, Sketch qua `sketch_jobs`), tới đúng provider đúng một lần, dùng capability gốc; không envelope nào mất; không attempt nào RUNNING chờ timeout | races |
| SK-R23 | Như R22 nhưng Sketch đã bị cancel trước khi tới lượt | Router đưa Sketch tới `sketch_jobs.start_attempt` → SketchEligibility từ chối, job cancelled, không gọi provider; Vision vẫn chạy bình thường | races |
| SK-R24 | `h04.owner_quarantine(ref staged)` (qua publication) commit **trước** bước 4 của C8 | Token lệch ở `artifact:<ref>` → vòng 2: artifact bị quarantine → không promote, không `proposal_ready`; `stale` (ARTIFACT_QUARANTINED) | races |
| SK-R25 | Thread khác yêu cầu quarantine ref staged trong lúc thread C8 đang giữ unit 04 | Quarantine chờ tới khi unit commit; thứ tự commit thực tế là "promote rồi quarantine". Sau đó `get_record` trả nội dung null + `content_withheld_reason`; `revalidate` → `stale` (ARTIFACT_QUARANTINED) + review_revision +1 | races |
| SK-R26 | Hook cùng thread yêu cầu quarantine **bên trong** unit 04, rồi unit lỗi (`fail_next_commit`) | Quarantine deferred; unit rollback (không state/event/bump của 04); publication deferred vẫn chạy sau khi nhả lock (rollback cũng drain); `coordinator.deferred_failures` rỗng; vòng quyết định sau dùng token mới và không promote | races |
| SK-R27 | Ref-set đổi giữa snapshot và quyết định: attempt 1 timeout/superseded, attempt 2 staged ref khác; C8 snapshot thấy attempt 1 nhưng job evidence chỉ attempt 2 | Bỏ quyết định, lấy snapshot + token mới (trong giới hạn 2 vòng); chỉ promote ref của attempt 2; không bao giờ commit promote với `ref_set_id` không khớp | races |
| SK-R28 | Queue dùng chung: envelope Vision bị giao trùng (redeliver khi job đang RUNNING) đứng trước một Sketch | Router: `h.jobs.start_attempt` → `started=False` (DUPLICATE_DELIVERY) → `RouteResult(started=False)`; không gọi `finish_vision`, observation hay `accept_completion`; `h.last_envelope` không đổi. `run_next()` kế tiếp xử lý Sketch đúng một lần | races |
| SK-R29 | Queue dùng chung: Vision của request đã cancel (eligibility từ chối khi start) đứng trước một Sketch | Router: `started=False` (lý do eligibility) → không `finish_vision`/observation/completion; job Vision cancelled bởi foundation. Sketch sau đó được xử lý bình thường. Đảo thứ tự (Sketch trước) cho cùng kết quả | races |
| SK-R30 | Completion Sketch UNSAFE qua `sketch_jobs` khi `fail_next_quarantine` đang bật: `_deliver_now` lỗi, intent quarantine còn pending. Sau đó gọi `h.jobs.deliver_side_effects()` (lối hướng A1) | Intent Sketch được claim bởi `h.jobs` và áp dụng **qua cùng port** (log có `caller=h.jobs`, `bumped=True`); artifact bị quarantine đúng một lần; intent được mark delivered; không mất intent. Proposal → `blocked_unsafe`, không `proposal_ready`. SK-C10 đạt | races |
| SK-R31 | Như R30, nhưng `h.jobs.deliver_side_effects()` chạy ở thread B và dừng ở cửa sổ sau claim, trước sink; thread A đang giữ unit C8 của 04 (hook giữ lock) | Sink trong thread B chờ tới khi thread A nhả lock; không có mutation artifact và không có bump epoch trong lúc unit giữ lock. Thứ tự commit thực tế: "unit 04 commit → quarantine → mark delivered". Nếu unit C8 dùng ref-set chứa ref đó thì quyết định của C8 dựa trên epoch trước quarantine; quarantine áp sau đó, `get_record` giữ lại nội dung, `revalidate` → `stale` (ARTIFACT_QUARANTINED) | races |
| SK-R32 | Giao lại cùng event_id: (a) sink áp dụng xong, nhưng lease bị coi là stale nên mark là no-op, rồi lần drain sau claim lại; (b) C9 và drain outbox cùng mang một event_id | `FakeArtifacts` dedup theo event_id → không bump fence lần hai; log có thêm entry `bumped=False`; epoch không đổi; kiểm toán SK-C10 vẫn đạt (đúng một `bumped=True` cho ref) | races |
| SK-R33 | Drain outbox bằng cả hai instance xen kẽ (`h.jobs` rồi `sketch_jobs` và ngược lại) với hỗn hợp intent Vision và Sketch | Mỗi intent được áp dụng đúng một lần qua cùng port, bất kể instance nào claim; không intent nào mất; tổng bump bằng số ref bị quarantine; SK-C10 đạt | races |

`SK-NI01` — crash/restart đa process và outbox durable: **NOT_IMPLEMENTED**, không tính vào tổng.

### 9.4 Contract và kiến trúc

| ID | Expected | Test |
|---|---|---|
| SK-C01 | Record, device view, event round-trip; field thừa bị từ chối; enum đúng SRS | contract |
| SK-C02 | Record qua `check_shape("DATA-23")`; ShapeSpec không đổi | contract |
| SK-C03 | Golden vector cho `content_sha256` và `generation_digest`; hash đổi khi content/level/display/version đổi; không phụ thuộc timestamps | dom, contract |
| SK-C04 | Event không chứa nội dung, child text hay thông tin nội bộ của provider | contract |
| SK-C05 | `ProviderCopyLifecycleReportV1` từ registry 04: `fixture_marker=true`, không có nhãn deleted từ fixture | contract |
| SK-C06 | Example fixtures H-AI-REVIEW được ghim: record pending, notice blocked, device view, copy report | ex |
| SK-C03b | Golden vector theo version: v1 (level_fx_1) và v2 (level_fx_2) của cùng proposal cho `generation_digest`/`content_sha256` khác nhau; tính lại từ lịch sử cho đúng giá trị đã lưu | dom, contract |
| SK-C07 | Domain không import framework; application không chứa chuỗi outer-layer; live app không có route sketch | contract + `tools/validate_architecture.py` |
| SK-C08 | `JobTypeRouter`: bảng route chỉ có `vision_analysis` và `sketch_generation`; type lạ → redeliver + raise; router không bao giờ gọi `start_attempt` trước khi chọn service; **ở cả hai nhánh**, provider/`finish_vision`/`accept_completion` chỉ được gọi khi `started=True` (spy: số lần gọi bằng 0 với mọi `started=False`) | adp |
| SK-C10 | Kiểm toán artifact (fixture teardown của mọi test chain/race). Mọi lần bump `artifact:<ref>` (ref 04 và cả ref Vision) đều có đúng một entry `bumped=True` trong log của `CoordinatedSketchArtifactPort`. Giao lại cùng event_id chỉ tạo entry `bumped=False`. `deps.artifacts` của **cả** `h.jobs` và `sketch_jobs`, cùng C9 và `h04.owner_quarantine`, là **cùng một** instance port (kiểm bằng identity). Test cố ý gọi thẳng `raw_artifacts.owner_quarantine(ref 04)` thì kiểm toán phát hiện | adp, races |
| SK-C11 | Builder parity: chạy cùng kịch bản A1 trên builder A1 gốc và trên `build_sketch_chain_harness()` — gồm A1-P01 (submit → schedule), A1-P07 (run Vision → handoff, qua router), A1-P08 (cache hit), A1-N15 (revoke consent sau schedule) và một completion Vision UNSAFE. So sánh trạng thái request/job/analysis, event và tập artifact bị quarantine: phải bằng nhau. Khác biệt duy nhất được phép là log kiểm toán của port. Suite A1 (SK-X03) vẫn chạy trên builder A1 gốc, không đổi | chain |
| SK-C09 | `SketchHandoffV1`: adapter chiếu đúng mọi field từ fixture 03/02 (cả hai đường analysis và cache_hit); `contract_version` cố định; domain/application của 04 không import `domain.assistance`, `application.ports.assistance` hay type của 02 (kiểm bằng AST trong test) | adp, contract |

### 9.5 Regression và static

- **SK-X01, BE2-01**: `tests/unit/test_ai_job_*.py`, `tests/contract/test_ai_job_contracts.py`,
  `test_ai_job_polling.py`. Integration PG trong `tests/integration/ai_jobs/` không có env →
  NOT_RUN.
- **SK-X02, BE2-02**: `test_vision_analysis_*.py`, `test_vision_context_*.py`,
  `tests/contract/test_analysis_*`, `test_vision_context_contracts.py`,
  `test_h_ai_review_handoff_examples.py`. Test bị skip do thiếu Pillow → NOT_RUN kèm lý do.
- **SK-X03, BE2-03**: `test_assistance_*.py`, `tests/contract/test_assistance_*`. Suite này gồm
  các test race và coordinator của A1 (`test_assistance_races.py`,
  `test_assistance_cr03_followup.py`). Mục đích: chứng minh việc 04 dùng chung coordinator và
  fences trong chain 04 không đổi hành vi của A1. Source của A1 vẫn không bị sửa.
- **SK-X04**: ruff và strict mypy trên các path mới; validators; `git diff --check`.
- Không hard-code tổng 878. Thu collected identities và JUnit cho từng suite.

### 9.6 Ánh xạ SC của draft 1

| SC | ID mới |
|---|---|
| SC-01 | C01, C02 |
| SC-02 | P01, P02 |
| SC-03 | P01, P02, N18 |
| SC-04 | P06, R01, R10 |
| SC-05 | N03, N06 |
| SC-06 | N08 |
| SC-07 | N09, N10, N22 |
| SC-08 | N11, N12 |
| SC-09 | N15, R04, R05 |
| SC-10 | N07, N13, N14 |
| SC-11 | R07, R11 |
| SC-12 | N11 (trùng source), N18 |
| SC-13 | N17 |
| SC-14 | P08, N20 |
| SC-15 | P10, C05 |
| SC-16 | R08, R09, R11, NI01 |
| SC-17 | X01–X04 |

Acceptance mới của revision 3 (không có SC tương ứng):

| Finding | Acceptance |
|---|---|
| SK-PR01 | SK-R13–R21, SK-N23, sửa SK-R06 |
| SK-PR02 | SK-R22, SK-R23, SK-C08 |
| SK-PR03 | sửa SK-P08 và SK-N20; SK-P11, SK-N24, SK-C03b |
| N01 | SK-C09 |

Acceptance mới của revision 4:

| Finding | Acceptance |
|---|---|
| SK-PR01-F1 | SK-R24, SK-R25, SK-R26, SK-R27, SK-C10 |
| SK-PR02-F1 | SK-R28, SK-R29; sửa SK-C08. Giữ nguyên SK-R22, SK-R23 |

Acceptance mới của revision 5:

| Finding | Acceptance |
|---|---|
| SK-PR01-F2 | SK-R30 (sink Sketch lỗi rồi giao lại qua A1), SK-R31 (thứ tự publication khi C8 giữ lock), SK-R32 (giao lại cùng event_id không bump lần hai), SK-R33 (drain xen kẽ hai instance), SK-C11 (builder parity); sửa SK-C10 (cùng instance port cho mọi actor, entry `bumped`) |

## 10. Batches, file, kiểm tra, evidence

| Batch | Phạm vi | File (đều mới) |
|---|---|---|
| SK1.1 | Domain + contracts | `domain/sketch_proposal.py`; `contracts/schemas/sketch_proposals.py`; test dom + contract |
| SK1.2 | Ports (gồm `SketchHandoffV1`, `SketchDecisionPort`) + service (vòng token, read có kiểm hiện hành, `revalidate`) + fakes cho unit test (`CounterDecisionPort`) | `application/ports/sketch_generation.py`; `application/services/sketch_generation.py`; `infrastructure/sketch_generation/{__init__,fakes}.py`; test svc |
| SK1.3 | Adapters (gồm `CoordinatedSketchRepository`, `FenceDecisionPort` với ref-set, `CoordinatedSketchArtifactPort` + log kiểm toán, chiếu `SketchHandoffV1`) | `infrastructure/sketch_generation/adapters.py`; test adp |
| SK1.4 | Chain harness: `build_sketch_chain_harness()` dựng lại composition A1 từ thành phần public, có một `CoordinatedSketchArtifactPort` dùng chung cho cả hai `AiJobService`; `JobTypeRouter` có guard `started` ở cả hai nhánh; `h04.owner_quarantine`; fixture teardown kiểm toán SK-C10 + chain/races + parity SK-C11 | `infrastructure/sketch_generation/harness.py`; test chain + races |
| SK1.5 | Examples, evidence, regression, dừng để review | `features/<feature BE2-04>/fixtures/h_ai_review/sketch_proposal_examples.json`; test ex; evidence |

Không sửa file nào của 01/02/03, A17 hay migration. Nếu phải sửa → đó là scope change, dừng lại.

Kiểm tra:

- Mỗi batch chạy test mới của batch đó.
- Trước khi review, chạy regression ở §9.5:
  - dùng venv gốc, ghim PYTHONPATH/MYPYPATH vào `backend/src` của worktree mới (tránh bẫy
    editable install);
  - chạy security test từ repo root.
- Chạy `tools/validate_harness.py`, `validate_repository_security.py`,
  `validate_architecture.py`, `validate_skeleton.py` (vì có thư mục mới) và `git diff --check`.
- Tránh tên hằng viết hoa chứa TOKEN/SECRET/PASSWORD (security gate).
- Không cài dependency, không chạy provider/Studio/DB.

Evidence (đặt trong owning feature):

- `evidence/notes/SK1_IMPLEMENTATION_EVIDENCE_<date>.md`: case → test, lệnh đã chạy, kết quả thật,
  NOT_RUN/NOT_IMPLEMENTED kèm lý do.
- `evidence/metrics/SK1_CHECKS_<date>.json`: hash source trước/sau, JUnit theo suite, identities.
- Raw logs đặt ở `evidence/local/`.

## 11. Quyết định Q1–Q6 (khuyến nghị đặt trước)

| Q | Khuyến nghị | Phương án thay thế / đánh đổi | Còn lại |
|---|---|---|---|
| Q1 Handoff | A (§3.2): resolver 04 qua `read` + `analysis_record`/`downstream_meaning`, reader Teacher được inject. Hint không phải nguồn chuẩn. Hỗ trợ cache-hit. Có open theo id. Kết quả chiếu vào `SketchHandoffV1` của 04; coupling với domain 03 chỉ nằm trong adapter (N01) | Làm B trước: gọn hơn về version và discovery, nhưng 04 phải chờ checkpoint 03 | G-01 B delta; G-02 discovery; G-03 trigger cho cache-hit |
| Q2 Level, input, output, version | Level opaque + fixture rule; display suy từ rule; `overlay_asset_ref` là ref derivative duy nhất; `editable_bounds` null; moderation chỉ not_applicable/pending/blocked; review_revision ≥1, tăng đơn điệu; `revise_level` chỉ từ pending. Level hiệu lực ghim theo version: v1 bằng `requested_level` của 03; version sau lấy từ lệnh revision; request 03 không đổi (SK-PR03). Provider nhận: render ref/sha, admission id, level, display, rule, và concept đã xác nhận (chỉ khi `confirmed`). Không child text, ID, tuổi hay model candidates. Meaning basis chỉ gây stale khi projection đổi | (a) Hoãn `revise_level` sang plan 05. (b) Sửa DATA-23 để có field asset riêng cho side_reference (scope change). (c) Gửi thêm candidates/tuổi (cần quyết định về privacy) | G-05; G-06 taxonomy; G-08 geometry |
| Q3 Admission | Consumer port `DerivedArtifactAdmissionPort` + fake chạy trên FakeArtifacts. Chỉ kiểm cấu trúc. Mọi output đều có result document artifact. Decode NOT_RUN | Dùng lại `ImageDecoderPort` + `AvImageDecoder` (`av` 18.1.0 có trong venv gốc) để decode ảnh synthetic; đổi lại bị coupling vào kiểu tín hiệu của FEAT-018 | G-10: artifact/decode/safety thật của BE1 |
| Q4 Worker/commit seam | Staging theo attempt + cổng hiển thị C8 + reconcile. C1/C5/C8/`revise_level`/`revalidate` dùng decision token được kiểm trong unit 04, chạy trong `coordinator.assistance()` của A1 (SK-PR01). Ref-set của token được chốt trước `t0`; mọi quarantine/cleanup ref 04 đi qua `CoordinatedSketchArtifactPort` (SK-PR01-F1). Builder chain riêng truyền **cùng** port đó cho cả hai `AiJobService`, nên drain outbox dùng chung từ bất kỳ instance nào cũng đi qua publication lock (SK-PR01-F2). Router chỉ đi tiếp khi `started=True` (SK-PR02-F1). Worker qua `AiProviderPort`; trong chain, `JobTypeRouter` là consumer duy nhất của queue và route theo job_type trước khi start (SK-PR02). Instance `AiJobService` thứ hai trong harness, dùng `FIXTURE_RETRY_POLICY`. Principal tạo job là requester đã đóng băng (tiền lệ TC-10 của A1). Dùng `find_semantic` để tìm job mồ côi. Không gọi provider trong transaction | (a) Retry policy riêng cho Sketch (cần số mới, cần owner duyệt). (b) Principal kiểu service (phải đổi role trong foundation; gate BE1) | G-11 durable/ADR; G-12 service identity |
| Q5 Policy/budget/copy | Không có ledger 04. Budget/kill switch qua eligibility fixture + giới hạn attempt. Copy qua fake support của foundation. Ghi lại seams với BE2-14 | Quota stage riêng của 04 theo mẫu A1 D6; có thể trùng ledger với BE2-14 | G-07, G-09 |
| Q6 Publication/ownership | Plan nằm ở local tới khi người dùng quyết định. Trước khi code: chọn ID khi tạo owning feature (ghi mapping), copy plan và approval vào đó, tạo branch/worktree từ base đã duyệt. FEAT-049 không làm owner | Code tạm trong FEAT-049: sai AGENTS và sai quyền sở hữu | Điều kiện bắt đầu ở §13 |

TC (ghi vào DECISIONS khi có owning feature):

| TC | Nội dung |
|---|---|
| TC-01 | Uniqueness: một proposal cho một assistance request |
| TC-02 | Tập reason token đóng |
| TC-03 | display_mode suy từ rule |
| TC-04 | content hash |
| TC-05 | generation digest dùng làm input_hash của job |
| TC-06 | ETag |
| TC-07 | Meaning basis |
| TC-08 | Owner notices giống A1 |
| TC-09 | Cancel chỉ cho Teacher |
| TC-10 | job_type `sketch_generation`, target = proposal_id |
| TC-11 | Copy scope |
| TC-12 | Tên event |
| TC-13 | Thời điểm đăng ký copy |
| TC-14 | Fixture policy |
| TC-15 | Output trùng source là malformed |
| TC-16 | Thành phần của decision token, `DECISION_ROUNDS = 2`, `DECISION_UNRESOLVED` |
| TC-17 | Store 04 trong chain dùng unit kind `assistance` của coordinator A1 |
| TC-18 | `JobTypeRouter` là consumer duy nhất của queue dùng chung trong test 04 |
| TC-19 | Level hiệu lực và `level_source` theo version |
| TC-20 | `SketchHandoffV1` (`contract_version = "sketch-handoff-v1"`) |
| TC-21 | `CoordinatedSketchArtifactPort` là đường duy nhất cập nhật ref 04; ba actor hợp lệ; log kiểm toán |
| TC-22 | Ref-set và `ref_set_id` chốt trước `t0`; ref-set đổi → bỏ quyết định |
| TC-23 | Reason `ARTIFACT_QUARANTINED` → `stale` |
| TC-24 | Router chỉ đi tiếp khi `started=True`, ở cả hai nhánh; `RouteResult` |
| TC-25 | Builder chain riêng của 04 dựng lại composition A1; một port artifact dùng chung cho mọi `AiJobService`; không dùng phương án dispatcher duy nhất |

## 12. Gates còn lại và handoff

| Gate | Nội dung | Owner / cần gì |
|---|---|---|
| G-01 | Handoff có version (B) | 03, checkpoint riêng |
| G-02 | Discovery/delivery bền vững cho handoff bị lỡ | Runtime 03/04 |
| G-03 | Trigger Sketch cho request cache-hit (A1 không phát intent) | 03 |
| G-04 | Đường cancel public hoặc từ Child sau handoff | Checkpoint 03 hoặc route P4, kèm quyết định owner |
| G-05 | Contract ghi review/approval/child_response; quyền ghi review_revision; revision sau khi approve | 05/06 |
| G-06 | Taxonomy level/support mode được adopt (FR025 đang PROPOSED) | Quyết định owner |
| G-07 | Policy/budget/kế toán stage Sketch được adopt; nối với `PolicyUse`/`ResourceAccounting` của BE2-14 | BE2-14 + người dùng |
| G-08 | Geometry bounds/editable_bounds, kích thước render, region | BE1 render + quyết định |
| G-09 | Provider copy hooks thật + authority/scope của BE1-15; nối với `ProviderCopyOperationHook` | 04 real + BE2-14/BE1-15 |
| G-10 | Admission theo `ArtifactReferenceV1`/DATA-20, lưu trữ, delivery qua mediation, retention và cleanup artifact mồ côi; decode/safety thật | BE1 + 04 real |
| G-11 | Persistence/outbox/fencing cho 04 (cùng 02/03); ADR về transaction boundary | Plan runtime riêng |
| G-12 | Service identity cho reader và cho việc tạo job (thay vì principal Teacher cố định) | BE1/P4 |
| G-13 | Model/profile/license/cost/quality/timeout thật; cơ chế kill worker thật | 04-live; LightningAI env + approval |
| G-14 | Review của P2/P1/P4 theo card; INTG-02/05; UI của P1 | Cross-owner |

Handoff H-AI-REVIEW cho 05: record §4.1, `content_sha256`, version, review_revision, audience,
event stale/superseded, example fixtures.

Handoff H-DATA-REQUEST: copy refs và report fixture.

## 13. Điều kiện bắt đầu code và điểm chưa xác minh

Điều kiện trước khi code:

1. Người dùng duyệt đúng revision/hash này và các lựa chọn Q1–Q6.
2. Đã tạo owning feature cho BE2-04, có plan và approval (AGENTS bước 2–5).
3. Đã tạo branch/worktree từ base đã duyệt.
4. Đã ghi ACTIVE slot = BE2-04 SK1 (roadmap §3.1 bước 3). BE2-03 giữ IN_PROGRESS (A1 đã nghiệm
   thu), BE2-02 PARKED, BE2-01 WAITING_STUDIO. Khi Studio có lại, R0/A17 được ưu tiên sau khi
   park rõ ràng.

Điểm chưa xác minh:

- Chưa chạy test nào; mọi hành vi mô tả ở trên là đọc code tại 113cdf9.
- Chưa chạy thử hai instance `AiJobService` trong cùng một harness.
- Code BE2-14 chỉ được nêu từ snapshot local `be64b999…`, chưa đối chiếu sâu.
- Cách hiểu "analyzing" và `overlay_asset_ref` là P.
- Hướng A phụ thuộc domain type chưa có version của 03. Coupling này chỉ nằm trong adapter (N01).
- Byte PNG trong fake chỉ có chữ ký cấu trúc, không decode được.
- Decision token mới được kiểm bằng đọc code coordinator/fences của A1, chưa chạy. Token chỉ bao
  phủ các thay đổi có điều phối và có bump fence (giả định OwnerFence). Không có bảo đảm
  PostgreSQL hay đa process.
- Việc dùng kind `assistance` của coordinator cho unit 04 mới dựa trên đọc code: kind này chặn
  việc mở unit lồng trong unit foundation/vision và chạy dưới cùng lock. Chưa chạy thử với ma
  trận coordinator của A1.
- `JobTypeRouter` dùng `h.last_envelope` và `h.finish_vision` của harness A1 (các field/method
  public của dataclass harness); chưa chạy thử với queue có cả hai loại job, hay với envelope
  bị giao trùng hoặc bị cancel.
- `CoordinatedSketchArtifactPort` dựa trên probe boundary của Codex (`codex-rev3-probes/`, chỉ
  dùng fake hiện có) và đọc code `request_publication`. Kiểm toán SK-C10 phát hiện được vi phạm
  trong test, nhưng không ngăn được ở mức ngôn ngữ việc gọi thẳng `FakeArtifacts`. Không có bảo
  đảm PostgreSQL/đa process cho artifact (G-10, G-11).
- Revision 5 dựa trên probe `codex-rev4-probes/shared_outbox_probe` và đọc code
  `deliver_side_effects`/`claim_side_effects`. Builder chain riêng chưa được viết. Composition A1
  dựng lại có thể lệch nếu builder A1 thay đổi sau này; SK-C11 là chốt chặn, chưa chạy. Outbox vẫn
  dùng chung, nên bất kỳ composition nào khác (ngoài chain 04) có nhiều instance với sink khác
  nhau thì không được bảo vệ; ghi lại cho G-11/P4 composition.
