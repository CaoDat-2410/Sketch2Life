# BE2-05 — Implementation plan (approval candidate R2): moderation và Teacher duyệt từng Sketch

```text
Status:    AWAITING_OWNER_APPROVAL   (chưa APPROVED; chưa có OD nào được owner chọn)
Ngày:      2026-10-19
Soạn:      Claude, theo yêu cầu trực tiếp của Person 2
Loại:      Plan tự đầy đủ, hợp nhất từ draft gốc + Rev2 + Rev3 (Rev3 = Codex PLAN_REVIEW_PASS)
Thay cho:  BE205_IMPLEMENTATION_PLAN_APPROVAL_CANDIDATE_20261019.md
           (SHA256 1fe9c19990c81c946fab465e922b52ee4339696f2d6dc2539fa166b4d9d9a1b4; giữ nguyên byte)
Sửa theo:  BE205_APPROVAL_CANDIDATE_CHECK_20261019.md (AC-PR01, P2) — chỉ sửa tập trung (§0.3 D-3)
Quyết định: BE205_OWNER_DECISION_PACKAGE_R2_20261019.md (cùng thư mục)
Baseline:  feature/be2-01-07 @ 58293f1a29ec630e2603c2860b6a2337fadfa713 (= upstream lúc đọc; sạch; staged 0)
Consumer:  local tracking ref origin/feature/be2-08-14 = 76959abf8c9938e96f32ff8141141bab4b85f05e
           (chỉ đọc; không fetch; KHÔNG khẳng định là remote tip hiện tại)
```

Vị trí lưu hiện tại: `features/FEAT-050-be2-sketch-generation/evidence/local/be205-preparation/`
(bị Git ignore, `.gitignore:136`). Đây là **ứng viên** để freeze vào feature folder của BE2-05 sau
khi owner duyệt; không chuyển quyền sở hữu BE2-05 sang FEAT-050. Tài liệu này được viết để tự đầy
đủ: không phần nào còn dẫn "như bản gốc", nên file local bị ignore không phải nơi duy nhất chứa
đặc tả khi plan được freeze.

Nhãn: **[SRS]/[CARD]** yêu cầu có nguồn; **[SRC]** đã xác minh trong source tại baseline; **[DP]**
thiết kế đề xuất, chưa adopt; **[FX]** named fixture/candidate; **[OD-xx]** quyết định owner
(xem gói quyết định); **[CR-xx]** yêu cầu tới seam khác.

## 0. Nguồn hợp nhất, ánh xạ và khác biệt

### 0.1 Hash input (đều giữ nguyên byte)

| Input | SHA256 | Bytes | Vai trò |
|---|---|---|---|
| `BE205_COMPONENT_PLAN_DRAFT_20261019.md` | `998dc0f5cb5d3369abf4b883dc8b6fbfd5b49fed24dc633e835b271da150ce0e` | 49723 | Draft gốc (nguồn các phần "như bản gốc") |
| `BE205_COMPONENT_PLAN_REV2_20261019.md` | `f21ab9272ba726d5061933a6ce12c0c542e63bbb82104b77953a31d19fbf6b76` | 42827 | Rev2 (coordinator, token, ReviewTarget, N15) |
| `BE205_COMPONENT_PLAN_REV3_20261019.md` | `799607e0c3b4723587a5168cc70bab92dba440b278b0a438bbf198beb21dc2d2` | 51101 | Rev3 đã PASS (marker terminal, N15b) |
| `BE205_CODEX_PLAN_REVIEW_20261019.md` / `.json` | `9d692cb2…` / `185b08a2…` | 10466 / 4421 | Review 1 (RV-PR01..04) |
| `BE205_CODEX_PLAN_REREVIEW_REV2_20261019.md` / `.json` | `ae691e8e…` / `bc59dc9c…` | 7573 / 5440 | Review 2 (RV-PR03-F1, RV-N01) |
| `BE205_CODEX_PLAN_FINAL_REVIEW_REV3_20261019.md` | `71749ad85cae7c53fe6952d4f0cf27bd77ff578ff647d65991e8749d150ff478` | 5270 | Review 3: PLAN_REVIEW_PASS, 2 lưu ý không chặn |
| `BE205_IMPLEMENTATION_PLAN_APPROVAL_CANDIDATE_20261019.md` | `1fe9c19990c81c946fab465e922b52ee4339696f2d6dc2539fa166b4d9d9a1b4` | 63684 | Candidate trước (giữ nguyên byte) |
| `BE205_APPROVAL_CANDIDATE_CHECK_20261019.md` | `c7b89f8342bb520d911cf7a459ab56d857a299ae0cf049639f4f5d36a5827d09` | 3880 | Kiểm candidate: 0 P1 / 1 P2 (AC-PR01) |

(Hash đầy đủ của mọi input nằm ở báo cáo kèm gói quyết định; bảng trên rút gọn các review.)

### 0.2 Ánh xạ nội dung hợp nhất

| Mục plan này | Lấy từ | Thay đổi khi hợp nhất |
|---|---|---|
| §1 Mục tiêu/phạm vi/exclusions | Gốc §1.1–1.3; Rev2 §1.2–1.3 | Rev2 thay Gốc ở phạm vi (coordinator, adapter); exclusions gộp |
| §2 Nguồn S-01..S-43 | Gốc §2 (S-06 sửa thành 829–830 ở lần tự kiểm gốc) | Chép nguyên |
| §2 Nguồn S-50..S-61 | Rev2 §2; Rev3 S-61 | Chép nguyên |
| §3 Dependency DI-01..DI-18 | Rev2 §3 (thay Gốc §3) | Chép nguyên |
| §4.1 Store/projection/revision authority | Gốc §4.1 + Rev2 §4.1 | Gộp; **D-3** (projection theo entry hiện hành) |
| §4.2 Khoá exact | Gốc §4.2 + Rev3 §4.2 | Gộp |
| §4.3 Decision/terminal | Rev3 §4.3 (+ Gốc §4.3 cho semantic duplicate) | **D-1, D-2** (§0.3) |
| §4.4 Moderation/quarantine | Rev2 §4.4 (thay Gốc §4.4) | Chép nguyên |
| §4.5 ReviewTarget | Rev2 §4.5 | Chép nguyên |
| §4.6 Giao thức | Rev2 §4.6 + Rev3 bước 3/4b/4c | Chép nguyên; D-1 bổ sung bước 4c |
| §4.7 ETag | Gốc §4.7 + Rev2 §4.7 | Gộp |
| §4.8 Authority/device | Gốc §4.8 + Rev2 §4.8 | Gộp |
| §4.9 Stale/mutation 04 | Gốc §4.5 + Rev2 §4.9 | Gộp |
| §4.10 Eligibility | Gốc §4.9 + Rev2 §4.10 | **D-1** thêm điều kiện marker |
| §5 Contracts | Gốc §5.1–5.5 + Rev2 §5 | Gộp; guard order theo Rev2/Rev3 |
| §6 Ports | Rev2 §6 + Rev3 (marker trong UoW) | Chép nguyên |
| §7 Adapter/đồng bộ/HTTP/persistence | Gốc §7 + Rev2 §7 | Gộp |
| §8 Handoff/seam/mismatch | Gốc §8.1–8.2 + Rev2 §8.3 | Gộp; CR-02 đóng |
| §9 File/thứ tự | Gốc §9 + Rev2 §9 | Gộp |
| §10 Acceptance | Gốc §10 + Rev2 §10 + Rev3 §10 | Gộp; **thêm RV-N22, sửa RV-R12** (D-1, D-2) |
| §11 Regression/evidence | Gốc §11 + Rev2 §11 | Gộp |
| §12 OD | Rev3 §12 | Chuyển chi tiết 7 OD chặn sang gói quyết định |
| §13 Gate | Gốc §13 + Rev2 §13 | Gộp |
| §14 Trình tự sau duyệt | Mới (theo yêu cầu owner + merge plan) | Mới |

### 0.3 Khác biệt so với Rev3 đã PASS (để review tập trung)

Không đổi kiến trúc. Hai điểm dưới đây là hai lưu ý không chặn của Review 3, được ghi thành
đặc tả và acceptance; không thay thiết kế đã PASS.

- **D-1 — Terminal áp cho approval cũ của mọi audience.** Rev3 đã tuyên bố terminal "cho exact
  version, áp cho mọi audience", nhưng câu "approve → reject: approve cũ thành `revoked`" có thể
  bị hiểu là chỉ áp cho cùng khoá review. Bản này nói rõ:
  - Khi marker được insert (bước 4c), **mọi** entry approve `effective` của cùng
    `(proposal_id, proposal_version, content_sha256)`, ở **bất kỳ** khoá audience/policy/context
    nào, chuyển `revoked` trong cùng UoW, kèm intent `SketchReviewEligibilityChanged` cho từng
    entry.
  - Eligibility (§4.10) kiểm thêm "không có marker cho exact version", để fail closed kể cả khi
    một entry approve nào đó chưa được chuyển trạng thái.
  - Acceptance mới RV-N22: approve audience A → reject/request_changes audience B (cùng version)
    → Child A bị chặn qua eligibility, cache và ticket.
- **D-2 — Trình tự ETag trong race cùng ETag (RV-R12).** Nếu approve thắng CAS, reject gửi cùng
  ETag ban đầu **phải thua** do precondition cũ (412). Reject thành công sau đó cần ETag mới và
  một command attempt mới (Idempotency-Key mới). Không chấp nhận ETag cũ trong bất kỳ trường hợp nào.

- **D-3 — Sửa AC-PR01 (candidate R2).** Candidate trước lấy trạng thái Teacher từ
  `marker.first_decision`, trong khi marker giữ quyết định đầu tiên mãi mãi; vì vậy
  request_changes → reject vẫn hiện pending/request_changes. Rev3 (§4.1 Rev2/Rev3) dùng quyết định
  hiệu lực; lỗi phát sinh khi hợp nhất. Bản này **khôi phục ngữ nghĩa Rev3**, không đổi kiến trúc:
  - Projection và `review_decision` lấy từ **entry hiện hành** của exact version, qua con trỏ
    `current_entry` trong head (§4.1, §4.6 bước 4c).
  - Marker chỉ giữ lịch sử terminal và chặn approve/access; `first_decision` vẫn bất biến, chỉ là
    provenance.
  - Khi không còn entry hiện hành (mọi entry đã `stale`/`revoked`), version terminal vẫn không
    mở lại quyền (§4.1 bảng precedence, §4.3).
  - Acceptance mới RV-N23, RV-N24.

Nếu owner chọn OD-07-B (reconsider), D-1 bỏ cùng marker; D-2 vẫn giữ; D-3 vẫn áp (projection lấy
entry hiện hành).

## 1. Mục tiêu, phạm vi, exclusions

### 1.1 Mục tiêu

Theo card BE2-05 [CARD S-02, S-04]:
- **Deliver:** DATA-24 primary schema và ExactContentReview port; CMD-35; moderation, queue,
  eligibility; quyết định trên exact item/version/hash/audience/context; invalidation khi edit hay
  đổi version; safe projection cho access gateway của BE1.
- **Exit:** approve/reject/request_changes; stale If-Match, conflict, revoke, edit; item
  pending/rejected/unsafe/stale không được fetch, cache, ticket hay exposure cho Child.
- **Nghiệm thu dương:** item an toàn được Teacher đúng scope approve, chỉ audience đã duyệt nhận
  được; approve trùng chỉ tạo một semantic review.
- **Nghiệm thu âm:** proposal pending/rejected/blocked/edited/stale không có nội dung cho Child;
  preset hay system admin không tự approve; Teacher không bypass unsafe; If-Match cũ bị conflict.
- **Evidence:** test exact-hash review dương/âm; leakage qua fetch/cache/subscription/ticket port;
  race invalidation; mẫu audit review.

### 1.2 Trong phạm vi (component offline)

1. Domain thuần: review entry/head, moderation record, khoá exact, marker terminal, ETag kết hợp,
   ReviewTarget projection, token identity.
2. Contract: binder Sketch cho DATA-24 V1; response CMD-35; Teacher queue view; Child payload
   chỉ-khi-approved; bảng lỗi → HTTP (chỉ dữ liệu, không route).
3. Ports + fakes; composition 05 trên **coordinator dùng chung** của chain harness SK1.
4. Service: moderate, CMD-35, queue, eligibility, child payload, xử lý notice, giao quarantine
   intent sau commit.
5. Adapter đọc 04 qua API public của `SketchGenerationService` (`revalidate`; `get_record` cho
   Teacher queue); `CoordinatedSketchArtifactPort.describe/quarantine`.
6. Fakes, harness, fixtures synthetic; chuỗi 04 → 05 dùng chính harness SK1.
7. Tests và evidence theo card, gồm race có handshake xác định.

### 1.3 Exclusions

- Media generator/player; đường media thay thế; render.
- Admin/preset approve thay Teacher; mọi "AI enabled" hay auto-approve [CARD S-02].
- Generic library publication review (BE2-12) và video review (BE2-09). DATA-24 dùng chung,
  purpose tách riêng.
- Sửa source/test/fixture SK1, BE2-01, nhánh người bạn. Thay đổi cần thiết ghi thành CR.
- Đổi bytes `ExactContentReviewCommandV1`/`ExactContentReviewRecordV1` hay phần
  `ProviderCopyLifecycle` (owner BE2-14) trong `ai_contract_candidates.py`.
- Moderation model/provider thật; policy moderation/reviewer thật (BE2-14 chưa adopt).
- Access ticket thật (CMD-60, BE1); production routes; mobile/FE-06/T07 UI.
- SQL, migration, fence/lock trên database thật, outbox delivery thật.
- Child response (CMD-36, BE2-06).
- Task 07 (PARKED).

## 2. Nguồn

Viết tắt (tương đối với worktree): `SRS` = `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md`;
`ROADMAP` = `features/FEAT-044-be2-ai-job-foundation/plan/BE2_ROADMAP.md`;
`TTB` = `features/FEAT-040-four-person-delivery-plan/artifacts/TEAM_TASK_BREAKDOWN.md`;
`SK1PLAN` = `features/FEAT-050-be2-sketch-generation/plan/PLAN_REV5_APPROVED.md`;
`B/` = `backend/src/sketch2life/`. Số dòng tại baseline 58293f1; S-40..S-43 tại 76959ab.

| ID | Nguồn | Nội dung dùng |
|---|---|---|
| S-01 | `AGENTS.md` | Quy trình feature/approval; bảo mật; không dữ liệu trẻ thật; integration cần allocation riêng |
| S-02 | ROADMAP:99; :132–133; :143; :177–181; :292 | Q07; dependency 05←01+04, 06←05; DATA-24 do 05 sở hữu, 12/09 không chờ 04/05 live; card BE2-05; 05 sở hữu CMD-35/DATA-24 |
| S-03 | `features/FEAT-044-be2-ai-job-foundation/plan/BE2_EXECUTION_TRACKER.md` | Không có ACTIVE slot |
| S-04 | TTB:558–568; :137; :151; :611; :647; :870; :1010; :1013; :1045 | Card (reviewer P2/P1/P4, deliverables, handoff, nghiệm thu, evidence); H-AI-REVIEW; 09/12 chỉ cần contract DATA-24; FR026/029/061 |
| S-05 | SRS:1287–1296 | UC-020 và AT-UC-020-P/N |
| S-06 | SRS:829–830; :955–957 | State Sketch pipeline / Child response; CreateSketchProposal / ReviewSketch / ChildView |
| S-07 | SRS:1007 | AT-CS-009 (Child đoán artifact ref của Sketch chờ review → không truy cập) |
| S-08 | SRS:1652 | DATA-23 SketchProposal (approval_ref; projection pending không có nội dung; sửa level tạo version mới) |
| S-09 | SRS:1654; :1656 | DATA-24 (If-Match là target review_revision; reason bắt buộc; edit cần invalidation); review_context session vs generic |
| S-10 | SRS:1646 | DATA-20 (moderation_state, review_ref; hash không chứng minh an toàn/consent) |
| S-11 | SRS:1682–1703 | B21.5 (review uniqueness theo exact tuple; async acceptance; consent hiện hành) |
| S-12 | SRS:1706–1736 (bảng lỗi 1718–1731) | B22.1 envelope, idempotency, If-Match, mã lỗi |
| S-13 | SRS:1779; :1780; :1804; :1825 | CMD-35 (T K M V); CMD-36; CMD-60 / ArtifactAccessTicket (review_ref bắt buộc cho Sketch AI) |
| S-14 | SRS:1527; :1530; :1562; :2355; :2358; :2390 | Truy vết FR026/029/061 |
| S-15 | SRS:2143; :2039; :2059 | Purpose candidate `ai_sketch`; màn C04; màn T07 AI Review Queue |
| S-16 | SRS:813; :815 | CS-002 (multi-aggregate cần transaction/saga rõ); CS-003 (audit review bền) |
| S-20 | `B/contracts/schemas/ai_contract_candidates.py`:1–9; :19–21; :28–110; :113–160; :272 | DATA-24 V1 (owner BE2-05), ShortText ≤200, ProviderCopyLifecycle (owner BE2-14), FULL_SCHEMA_IDS |
| S-21 | `backend/tests/contract/test_ai_job_contracts.py`:27–68; :154–166 | Manifest hash, fixture dương/âm DATA-24, record/owner metadata |
| S-22 | `features/FEAT-044-be2-ai-job-foundation/fixtures/data24/{positive,negative}/` | 2 dương (session_sketch_approve, library_request_changes), 7 âm |
| S-23 | `B/domain/sketch_proposal.py`:42–59; :62–69; :92–117; :245–331; :334–354; :458–512; :515–554; :581–606; :698–757 | PipelineState; REVIEW_OWNED_STATES; ModerationState; StatusReason; HandoffBinding/CurrentFacts/current_verdict; DecisionToken; PromotedOutput/ProposalVersion (cấm approved/rejected/passed); SketchProposal + etag; content_sha256; terminate/promote/revise_level/device_status |
| S-24 | `B/application/services/sketch_generation.py`:403–435; :437–452; :747–774; :804–853; :855–875; :877–902; :905–918; :1009–1059 | `_decide`; `_current_reason`/`_invalidate`; `revalidate`; `revise_level`; `apply_owner_notice`; `get_record`/`device_view`; `_authorized`; `record_view` |
| S-25 | `B/application/ports/sketch_generation.py`:81–89; :254–273; :276–296; :309–360 | SketchDecisionPort/PolicyPort; SketchAction/Scope/AuthorityPort; Receipt/Event; UnitOfWork |
| S-26 | `B/infrastructure/sketch_generation/fakes.py`:58–62; :102–117; :145–148; :237–275 | Store SK1 bump `eligibility:{org}` sau commit invalidation; CounterDecisionPort |
| S-27 | `B/infrastructure/sketch_generation/harness.py`:222–330; :420–533; :569; :735 | Unit harness, chain harness, `owner_quarantine`, `build_sketch_examples` |
| S-28 | `B/application/ports/ai_jobs.py`:42–55; :57–64; :260–268; :358–360; :472–479; :516–521 | OwnerFence/FenceResult; Principal; ArtifactDescriptor; hold fences trong UoW; OwnerFencePort; ArtifactPort |
| S-29 | `B/infrastructure/ai_jobs/fakes.py`:79–110 | FakeOwnerFences; fence scope (eligibility, grant, artifact) |
| S-30 | `B/application/ports/core_foundation.py`:110–190 | Port BE1 (identity, consent, membership, receipt, scope) |
| S-31 | SK1PLAN:90; :273; :283; :286; :290; :388; :406; :701; :752; :1039 | 05 quyết `passed`; "05 sẽ tăng review_revision (ASSUMED_CONTRACT, G-05)"; approval_ref do 05 ghi; audience subset; 05 phải revalidate trước review; revision sau approve cần contract 05 |
| S-40 | `B/application/video_review_contract.py`:1–60 (76959ab) | 09 binder `bind_video_review` trên DATA-24 V1, không fork |
| S-41 | `B/application/ports/video_review_write.py`; `B/application/video_review_write.py` (76959ab) | 09 dùng Command/Record V1 |
| S-42 | `B/application/learning_content_commands.py`:215–252 (76959ab) | 12 dùng GenericLibrary context và tạo Record V1 |
| S-43 | `git diff 58293f1 76959ab` trên `ai_contract_candidates.py`, `test_ai_job_contracts.py` | Không khác: hai lane dùng cùng bytes DATA-24 V1 |
| S-50 | `B/infrastructure/assistance/fakes.py`:52; :66–182 | `_UNIT_KINDS`; `AssistanceCommitCoordinator`: RLock dùng chung; unit foundation/vision/assistance; cấm mở foundation/vision trong assistance (:111–113, :128–136); `read` re-entrant (:151); `request_publication` defer trong unit, chạy sau khi thoát unit ngoài cùng, **cả khi commit lẫn rollback** (:157–174); lỗi deferred vào `deferred_failures` (:176–182) |
| S-51 | `B/infrastructure/assistance/fakes.py`:184–196 | `HookedOwnerFences.after_successful_hold`: seam post-hold/pre-commit |
| S-52 | `B/infrastructure/sketch_generation/adapters.py`:94; :476–491; :494–514; :530–571 | `sketch_policy_fence_scope`; `CoordinatedSketchRepository`; `FenceDecisionPort.token` (eligibility, analysis, sketch-policy, artifact theo ref); `CoordinatedSketchArtifactPort` |
| S-53 | `B/infrastructure/sketch_generation/adapters.py`:220–245 | `AssistanceHandoffReader.current` đọc assistance store + Vision → không gọi được trong unit `assistance` |
| S-54 | `B/infrastructure/assistance/adapters.py`:161; :174–183 | `CoordinatedAnalysisRepository`: bump `analysis:{org}` sau inner commit; rollback không bump |
| S-55 | `B/infrastructure/sketch_generation/harness.py`:512–523; :578–587 | `publish_policy`, `owner_quarantine` qua coordinator; composition chain: một coordinator, một `HookedOwnerFences` |
| S-56 | `B/infrastructure/assistance/harness.py`:128; :314–322 | `READER` (Teacher reader inject, có scope); `publish_owner_change` = đổi fact + bump `eligibility:{org}` trong một publication |
| S-57 | `B/infrastructure/ai_jobs/fakes.py`:79–110; :604; :634–649 | `FakeOwnerFences.hold` chỉ so sánh; `grant_fence_scope`, `artifact_fence_scope`; `FakeArtifacts.quarantine` idempotent theo `applied_events`; `owner_quarantine` bump artifact epoch |
| S-58 | `B/application/services/sketch_generation.py`:403–435; :446–453; :730–745; :747–766; :839 | `_decide` trả snapshot/updated; `_invalidate`; `deliver_cleanup` (mẫu giao sink sau commit); `revalidate` trả `SketchProposal \| None`; `revise_level` publish invalidation |
| S-59 | `B/domain/sketch_proposal.py`:433–473; :581–606 (:589 có `proposal_version`) | `AssetRef` (ref, sha256, media_type, byte_size); `PromotedOutput.refs()`; `content_sha256` public, có số version |
| S-60 | `B/infrastructure/sketch_generation/fakes.py`:223–225; :237–275 | `request_revalidation` chỉ thêm cờ; store SK1 bump `eligibility:{org}` sau inner commit trong unit coordinator |
| S-61 | `B/application/services/sketch_generation.py`:437–444; `B/domain/sketch_proposal.py`:698–717 | Reason hiện hành của 04 chỉ gồm fact owner + policy 04; `terminate()` thay field lifecycle của version hiện tại, giữ `promoted` |

## 3. Dependency inventory

Trạng thái: **EXISTS** (code trên nhánh), **CANDIDATE** (có code, contract chưa adopt),
**FIXTURE** (plan thêm named fixture), **MISSING**, **CONSUMER** (phía người bạn, chỉ đọc).

| ID | Cần cho 05 | Trạng thái | Bằng chứng | Hành động |
|---|---|---|---|---|
| DI-01 | DATA-24 command/record | EXISTS (0.1-candidate, owner 05) | S-20..S-22 | Giữ V1; binder Sketch |
| DI-02 | Output 04 có version/hash/refs/AssetRef | EXISTS qua `revalidate()` public | S-58, S-59 | ReviewTarget projection do 05 sở hữu |
| DI-03 | Quyền ghi `review_revision` của 04 | MISSING (G-05) | S-31, S-23 | ETag kết hợp (OD-04) hoặc CR-01 |
| DI-04 | approved/rejected/passed/approval_ref trong DATA-23 | MISSING (domain 04 cấm) | S-23:458–512 | Store 05 + projection (OD-03) |
| DI-05 | Khoá giữ applicability tới commit | EXISTS trong fake: `AssistanceCommitCoordinator` | S-50, S-52 | Unit 05 trong coordinator dùng chung; DB thật là gate |
| DI-06 | Epoch của mọi input | EXISTS: eligibility, analysis, sketch-policy, artifact/ref, grant | S-52, S-54, S-55, S-57 | Token 05 superset + scope 05 (§4.6) |
| DI-07 | Moderation/reviewer policy | MISSING (BE2-14 chưa adopt) | S-02, S-04 | [FX] + scope `review-policy:{org}` |
| DI-08 | Teaching/review authority | CANDIDATE (`SketchAuthorityPort` không có REVIEW) | S-25 | `ReviewAuthorityPort` [FX]; epoch `grant_fence_scope` |
| DI-09 | Audience/consent revision cho review_context | CANDIDATE (04 có `consent_ok`, `roster_revision`) | S-23, S-53 | `ReviewContextPort` [FX] + scope `review-context:{org}:{session}`; mapping OD-09 |
| DI-10 | Purpose `ai_sketch` | SRS candidate | S-15 | [FX]; OD-09 |
| DI-11 | Ticket CMD-60 | MISSING (BE1) | S-13 | Fake ticket gọi eligibility |
| DI-12 | Dispatcher/cache/subscription | MISSING | — | Fake + intent |
| DI-13 | Consumer BE2-09 | CONSUMER @76959ab, cùng bytes V1 | S-40, S-41, S-43 | Không đổi V1 |
| DI-14 | Consumer BE2-12 | CONSUMER @76959ab, cùng bytes V1 | S-42, S-43 | Không đổi V1 |
| DI-15 | Consumer BE2-06 | Backlog cùng lane | S-02 | Handoff |
| DI-16 | Runtime 01/04 | OPEN (01 WAITING_STUDIO; 04 live chưa có) | S-03 | Gate |
| DI-17 | Bất biến SK1: mọi commit 04 làm đổi proposal pending đều bump `eligibility:{org}` | EXISTS (`_invalidate`, `revise_level`; `request_revalidation` chỉ thêm cờ) | S-58, S-60 | 05 dựa vào; RV-R07 kiểm |
| DI-18 | Fact owner đổi không qua publication có bump (vd. `set_render` không notice) | Residual SK1 đã nghiệm thu | S-56 | Không bị bắt tại commit; bị bắt ở lần đọc pull sau |

## 4. Thiết kế

### 4.1 Store review riêng, projection kết hợp, authority của revision [SRC S-23, S-31; DP; OD-03, OD-04]

`ProposalVersion.__post_init__` từ chối `approved`, `rejected` và moderation `passed`
[SRC S-23:458–512]. Sửa điều đó là thay code đã nghiệm thu của 04, nên 05 giữ store riêng:

- **`SketchReviewHead`** (một cho mỗi proposal): proposal_id, organization_id,
  `decision_revision` (≥0), moderation outcome mới nhất theo version, và **`current_entry`** theo
  exact version `(proposal_version, content_sha256)`: review_id của entry `effective` có
  `decision_revision` lớn nhất, hoặc null nếu không còn entry `effective` nào (D-3).
- **`SketchReviewEntry`** (append-only): review_id, `review_revision` DATA-24 (= `decision_revision`
  sau quyết định), decision, reason, reviewer principal, reviewed_at, exact target (kind, id,
  version, hash), `source_context_revision`, review_context, audience_scope, policy refs,
  `producer_review_revision` lúc quyết định, state.
- **`ModerationRecord`** (append-only): proposal_id, version, content_sha256, refs+sha256, outcome
  (`passed` | `blocked`), policy ref, decided_at. Không chứa nội dung.
- **`VersionTerminalMarker`** (§4.3).
- **Projection DATA-23 kết hợp** (chỉ đọc, dựng từ ReviewTarget + head 05). `review_decision`
  và trạng thái Teacher lấy từ **`current_entry`** của exact version, **không** lấy từ
  `marker.first_decision` (D-3). Thứ tự ưu tiên, dừng ở dòng đầu tiên khớp:

  | # | Điều kiện | `pipeline_state` | `review_decision` / ghi chú |
  |---|---|---|---|
  | 1 | Moderation 05 `blocked` cho đúng hash | `blocked_unsafe` | moderation `blocked` |
  | 2 | `current_entry.decision = reject` | `rejected` | `reject` |
  | 3 | `current_entry.decision = request_changes` | `pending_teacher_review` (của 04) | `request_changes` |
  | 4 | `current_entry.decision = approve`, entry hiện hành theo §4.10, **không có marker** | `approved` | `approve`; `approval_ref`, moderation `passed` |
  | 5 | Không có `current_entry` nhưng **có marker** | `rejected` nếu entry terminal mới nhất trong lịch sử (mọi state) là reject; ngược lại `pending_teacher_review` của 04 | `null`; `decision_applicable=false`; `version_terminal=true`; `approve_allowed=false` |
  | 6 | Còn lại | trạng thái 04 | `null` hoặc theo entry nếu có |

  - Dòng 4 không bao giờ khớp khi có marker (D-1 đã revoke mọi approve; kiểm thêm để fail closed).
  - Dòng 5 dùng **lịch sử entry** (bất biến, mọi state), không dùng `first_decision`; nó chỉ để
    hiển thị. Quyền luôn bị chặn bởi marker (§4.3, §4.10), dù hiển thị thế nào.
- Không cần transaction ghi qua hai feature (CS-002, S-16).

| Revision | Ai sở hữu / ai tăng | Dùng để |
|---|---|---|
| `record_version` (04) | 04, mọi commit 04 | Identity snapshot trong token |
| `review_revision` (DATA-23, 04) | 04, khi invalidation/revise; **05 không tăng** | Thành phần ETag kết hợp; projection hiển thị |
| `decision_revision` (05) | 05, mỗi quyết định được chấp nhận | Thành phần ETag kết hợp; = `review_revision` của Record V1 |

SRS (S-09) nói If-Match của teaching review là "target review_revision". ETag kết hợp là
**deviation có chủ đích**, chờ owner (OD-04); nếu owner muốn đúng câu chữ SRS thì cần CR-01 cho 04.

### 4.2 Khoá exact và trạng thái áp dụng [SRS S-11; DP]

- Khoá: `(target_kind, target_id, target_version, target_hash, audience digest, context_revision,
  policy_version)`.
  - `policy_version` = id/version review policy [FX], kèm policy ref của version 04.
  - `audience digest` = strict canonical hash của session/group/participant đã sắp xếp cộng
    `consent_revision_refs`.
- Mỗi khoá một review hiệu lực; quyết định mới trên cùng khoá làm entry cũ `revoked`.
- Cùng content hash khác audience/consent **không** dùng lại review.
- State áp dụng `effective | revoked | stale` (khớp enum Record V1). Reject hiệu lực không phải approval.
- State áp dụng **không** quyết định tính terminal; tính terminal (OD-07-A) là thuộc tính exact
  version, lưu ở marker. Entry không bao giờ bị xoá.

### 4.3 Decision semantics và tính terminal [SRS S-05, S-09; DP; OD-07]

**Đề xuất OD-07-A (chưa được owner chọn): reject và request_changes là terminal cho exact version,
áp cho mọi audience.** Lý do: nội dung version không đổi giữa các audience; UC-020 coi rejected là
kết cục của item; muốn nội dung khác thì 04 tạo version mới (`revise_level`).

| Quyết định | Điều kiện | Hệ quả |
|---|---|---|
| `approve` | Moderation `passed`; target pending, hiện hành; audience ⊆ binding; **không có marker** | Review effective; Child trong audience nhận qua eligibility |
| `reject` | `reason` không rỗng | Ghi entry; insert marker nếu chưa có; revoke mọi approve của version (D-1) |
| `request_changes` | `reason` không rỗng | Như reject; **không** tự gọi `revise_level` của 04 (OD-07 phụ: không ghép) |

**Marker terminal.**
- `VersionTerminalMarker{proposal_id, proposal_version, content_sha256, first_decision (reject |
  request_changes), review_id, recorded_at}`, khoá `(proposal_id, proposal_version, content_sha256)`.
- **Vai trò (D-3):** marker chỉ (1) ghi nhận version đã terminal và (2) chặn approve/access.
  `first_decision` là provenance lịch sử bất biến; **không** dùng cho projection hay
  `review_decision` (lấy từ `current_entry`, §4.1).
- Ghi **nguyên tử trong cùng UoW** với entry reject/request_changes đầu tiên của exact version
  (§4.6 bước 4c). Quyết định terminal sau đó không ghi đè marker.
- **Bất biến:** không bị xoá hay đổi khi entry chuyển `stale` (đổi policy/context/audience/consent
  của 05 hoặc invalidation của 04) hay `revoked`.
- Tương đương "có ít nhất một entry reject/request_changes cho exact version ở **bất kỳ** state
  nào"; RV-N21 kiểm hai dạng luôn khớp.
- **D-1:** khi insert marker, mọi approve `effective` của exact version ở mọi khoá chuyển `revoked`
  trong cùng UoW, kèm intent eligibility cho từng entry.

**Guard** dưới CAS của head 05, trong coordinated final unit (§4.6 bước 4b): có marker → approve
409 `INVALID_STATE`, bất kể audience, review policy, context revision hay consent revision. Guard
dùng state 05, không dùng state thô của 04 (04 vẫn pending). Bước 3 đọc marker để trả lỗi sớm;
bước 4b đọc lại dưới CAS mới là quyết định.

**Hệ quả:**
- Approve → reject (bất kỳ audience) cùng version: cho phép; mọi approve của version `revoked`.
  Đây là cách rút approval (OD-08).
- Reject/request_changes → approve cùng version: không cho phép.
- Reject → reject cùng khoá: semantic duplicate; request_changes → reject (cùng hoặc khác khoá):
  ghi được; entry request_changes cùng khoá chuyển `revoked`; `current_entry` = reject → projection
  `rejected`; marker giữ nguyên, `first_decision` vẫn là request_changes (D-3, RV-N23).
- **Không còn entry hiện hành** (mọi entry của version đã `stale`/`revoked`, ví dụ do đổi policy/
  context của 05): `current_entry = null`, marker vẫn còn → approve vẫn 409, eligibility vẫn chặn,
  projection theo dòng 5 bảng §4.1. Teacher có thể ghi một reject/request_changes mới theo policy/
  context hiện hành; entry đó thành `current_entry`, marker không đổi (RV-N24).
- Version mới (04 `revise_level`) có `proposal_version` và `content_sha256` khác (hash gồm số
  version, S-59:589) → không trùng marker → moderate và review lại từ đầu.
- Đổi policy/context/audience của 05 làm entry cũ `stale` **không** mở lại version đã terminal.

**Approve trùng:** cùng Idempotency-Key + payload → replay; khác key + ETag hiện hành + cùng khoá +
cùng decision → trả review hiệu lực sẵn có, `semantic_duplicate=true`, không tăng revision; ETag
cũ → 412.

**Race cùng ETag (D-2):** hai lệnh gửi cùng ETag; lệnh thắng CAS tăng `decision_revision`, lệnh
kia luôn 412 `STALE_AGGREGATE`. Nếu approve thắng, reject ban đầu thua; muốn reject phải đọc ETag
mới và gửi command mới (key mới), khi đó D-1 áp dụng.

**Phương án OD-07-B (owner có thể chọn):** Teacher được reconsider. Khi đó bỏ marker và guard,
reject chỉ đóng quyền cho tới khi có approve hiệu lực mới; mọi câu "không bao giờ tới Child" đổi
thành "không tới Child khi chưa có approve hiệu lực mới"; RV-N16, N18..N22 đổi thành ca dương
tương ứng (với ETag/moderation/context hiện hành); RV-R12 chỉ còn yêu cầu không mất cập nhật.

### 4.4 Moderation và quarantine [SRC S-23, S-52, S-57, S-59; DP; OD-06]

- 04 chỉ ghi `not_applicable`/`pending`/`blocked`; `passed` do 05 [SRC; S-31:90]. 04 không lưu tín
  hiệu an toàn của generator trong proposal (PromotedOutput không có field safety).
- **Input tin cậy** (không dùng `record_view`):
  - text của `PromotedOutput`;
  - `AssetRef` của asset (nếu có) và result document: `artifact_ref`, `sha256`, `media_type`,
    `byte_size` — metadata 04 đã ghim khi promote (S-59);
  - `ArtifactDescriptor` qua `describe(ref)` của `CoordinatedSketchArtifactPort` (quarantine,
    producer job/attempt; đọc qua `coordinator.read`, S-52).
- Moderation record ghim `(proposal_id, version, content_sha256, refs+sha256, policy ref)`.
  Adapter kiểm `content_sha256` bằng hàm public `content_sha256(...)` của 04 trên chính các field
  đã đọc.
- v0 `FixtureSketchModeration` deterministic [FX]: part đóng, text giới hạn, token cấm synthetic,
  `media_type`/`byte_size` theo policy fixture. Không đọc bytes ảnh; moderation ảnh thật là gate.
- Moderation chạy khi Teacher mở queue item hoặc khi CMD-35 approve tới mà chưa có kết quả cho
  đúng hash; cả hai trong giao thức §4.6.
- `blocked`:
  - Ghi `ModerationRecord(blocked)` và `QuarantineIntent` (event_id deterministic) **trong cùng UoW
    05**, nguyên tử với head.
  - **Sau commit, ngoài unit**, deliverer 05 (mẫu `deliver_cleanup`, S-58:730–745) gọi
    `CoordinatedSketchArtifactPort.quarantine(intent, caller="be2-05")`. Port tự đi qua
    `request_publication`; sink idempotent theo event_id (S-57:634–640). Sink lỗi → intent còn
    pending, giao lại; không ảnh hưởng quyết định đã commit.
  - Không bao giờ gọi sink trong unit 05. Không có field/flag nào cho Teacher bypass; approve →
    409 `INVALID_STATE`. Teacher chỉ thấy mã lý do an toàn; Child chỉ thấy "không khả dụng".

### 4.5 ReviewTarget projection từ API public [SRC S-58, S-59; DP]

Adapter `SketchServiceReviewTargetReader`:
- Gọi `revalidate(proposal_id)` → `SketchProposal | None` (API public, mức hệ thống, không
  principal). **Không** đọc `peek`, repository, UoW hay store của 04.
- Map sang `SketchReviewTargetV1` (05 sở hữu, 0.1-candidate):

| Nhóm | Field |
|---|---|
| Identity | proposal_id, organization_id, `record_version`, `review_revision`, `proposal_version` |
| Trạng thái | `pipeline_state`, `moderation_state`, `status_reason` |
| Nội dung | level, display_mode, text, asset `AssetRef \| None`, result_document `AssetRef`, `content_sha256`, producer canonical, job/attempt |
| Binding | session/class/canvas/group, audience, contributor, purpose, `context_revision`, `roster_revision`, analysis id/revision, meaning digest, source snapshot ref + input hash |
| Policy | policy id/version/status của version |

- `ref_set` = `sorted(promoted.refs())`: result document luôn có; asset nếu có (text-only vẫn
  fence được result document).
- `target_identity` = `strict_canonical_sha256` của `{proposal_id, record_version, review_revision,
  proposal_version, content_sha256, ref_set (ref+sha256)}`.
- Chỉ hợp lệ để review khi `pipeline_state == pending_teacher_review` và có `promoted`. Text là dữ
  liệu hạn chế: chỉ ra queue Teacher sau authority 05, hoặc child payload khi eligible.
- `get_record(teacher, …)` dùng cho queue Teacher (defense in depth, principal Teacher thật);
  không dùng cho đường device. `get_record` có thể tự gửi `request_revalidation` trong
  transaction riêng của 04 (S-24:877–888); coi là tác dụng phụ đã biết.

### 4.6 Giao thức ghim và giữ applicability tới commit [SRC S-50..S-58; DP; OD-05]

**Composition.** Một `AssistanceCommitCoordinator` và một `HookedOwnerFences` dùng chung với chain
harness SK1 (S-55). Repository 05 là `CoordinatedSketchReviewRepository`:
`with coordinator.assistance(), inner.transaction()` — cùng mẫu `CoordinatedSketchRepository`.
Unit 05 loại trừ lẫn nhau với mọi unit foundation/Vision/assistance/04 và mọi owner publication
của mọi thread. Không dùng khoá riêng của store 05 thay cho coordinator.

**Scope của `ReviewDecisionToken`:**
1. `eligibility:{org}`, `analysis:{org}`, `sketch-policy:{org}` (như `FenceDecisionPort.token`).
2. `artifact:{ref}` cho mọi ref trong `ref_set`.
3. `grant:{org}:{principal}` (authority review; `grant_fence_scope` có sẵn).
4. `review-policy:{org}` [FX]: policy moderation/review của 05.
5. `review-context:{org}:{session}` [FX]: audience/consent revision của review_context.
- Kèm `target_identity`. Epoch đọc bằng `coordinator.read` (re-entrant, được phép trong unit).
- Publication fixture của policy/context/authority 05 đi qua `coordinator.request_publication` và
  bump đúng scope (mẫu `publish_policy`).

**Các bước:**
1. **Snapshot** (ngoài unit): `revalidate()` → T1. Không pending → dừng.
2. **Token** (ngoài unit): K1 = epochs (ref_set từ T1) + `target_identity(T1)`.
3. **Read** (ngoài unit): `revalidate()` lần hai → T2; đọc authority/context/policy 05;
   moderation (nếu chưa có cho đúng hash). `target_identity(T2) ≠ target_identity(T1)` hoặc ref_set
   đổi → quay lại bước 1. Decide trên T2: pending; hash/version/context khớp command; audience ⊆
   binding; moderation `passed`; consent/context khớp; marker đọc trước.
4. **Final unit** (trong `coordinator.assistance()`):
   a. `fences.hold(K1)` và so `target_identity`; epoch lệch → rollback, quay lại bước 1.
   b. Đọc head 05; kiểm lại **marker** và semantic duplicate **dưới CAS**.
   c. CAS head (`decision_revision`); insert entry; nếu là reject/request_changes đầu tiên của exact
      version thì insert marker (unique) **và revoke mọi approve effective của version (D-1)**;
      chuyển entry cùng khoá cũ sang `revoked`; **cập nhật `current_entry` của exact version** (D-3);
      receipt; audit; intents (`SketchReviewEligibilityChanged`, `QuarantineIntent` nếu có).
      Đường đánh dấu `stale` (notice/policy/context) cũng cập nhật `current_entry` trong cùng UoW.
   d. Inner commit; sau inner commit, vẫn trong unit, bump `sketch-review:{org}:{proposal_id}`
      (mẫu `CoordinatedAnalysisRepository`, S-54): rollback không bump.
   e. Thoát unit → coordinator release.
5. Quá `DECISION_ROUNDS` [FX = 2] → 503 `DEPENDENCY_UNAVAILABLE`, không ghi.

**Vì sao đủ trong fake.** DI-17: mọi commit 04 đổi proposal pending đều bump `eligibility:{org}`
dưới cùng lock; mọi đổi policy/analysis/artifact/owner fact qua publication có bump cũng dưới lock
đó. Final unit giữ lock từ 4a tới 4e nên không writer/publication nào của thread khác chen được
giữa check và commit; thay đổi trước 4a làm lệch epoch → bước 1.

**Lock order và luật lồng unit.**
- Coordinator RLock (ngoài) → lock store 05 (trong); không lấy coordinator khi đang giữ riêng lock
  store 05.
- Trong unit 05 chỉ được: `coordinator.read`, `fences.hold`, UoW 05. **Cấm** `revalidate`,
  `get_record` (mở unit Vision/assistance-store, S-53), job service, sink artifact.
- Writer/publication được bảo vệ: unit 04, Vision (bump analysis), foundation jobs, assistance
  store, `publish_owner_change`, `publish_policy`, `owner_quarantine`/`quarantine` của artifact
  port, publication fixture của 05.

**Publication cùng thread, rollback, exception.**
- 05 không gọi `request_publication` trong unit; bump scope 05 làm trực tiếp sau inner commit.
- Publication cùng thread yêu cầu trong unit (qua hook/test) bị defer, chạy sau khi thoát unit,
  **cả khi unit rollback** (S-50:157–174) — hành vi đã biết; eligibility pull và notice xử lý stale.
- Exception trong unit → inner rollback, không bump, lock nhả; deferred chạy; lỗi deferred vào
  `deferred_failures`. Exception ở bước 1–3 không giữ lock.

**Giới hạn.** Fence `eligibility:{org}` toàn tổ chức → retry thừa (CR-04 tuỳ chọn). DI-18 không bị
bắt tại commit. Bảo đảm chỉ trong một process với coordinator fake; database thật cần fence
`FOR SHARE` trên cùng connection và ADR transaction boundary (G-11 SK1) → gate integration.

### 4.7 ETag và If-Match [SRS S-09, S-12; SRC S-23:549–554; DP; OD-04]

- ETag do 05 phát:
  `"sketch-review:{proposal_id}:{proposal_version}:{review_revision_04}:{decision_revision_05}"`.
- Thiếu → 428 `PRECONDITION_REQUIRED`; lệch bất kỳ phần nào → 412 `STALE_AGGREGATE` kèm
  `current_revisions`. Teacher lấy ETag từ queue view 05, không dùng ETag `sketch-proposal:` của 04.
- Record V1 `review_revision` = `decision_revision` sau quyết định.
- Phương án CR-01: 04 thêm lệnh cho 05 tăng `review_revision` (phải sửa SK1 đã nghiệm thu).

### 4.8 Authority, audience, consent; đường device [SRS S-05, S-09, S-13; DP]

- CMD-35/queue: chỉ Teacher có review scope hiện hành (`ReviewAuthorityPort` [FX], epoch
  `grant:{org}:{p}`). Admin/system role → 403 `FORBIDDEN_SCOPE`; device → 404; khác lớp/org → 404;
  không có đường preset/automation nào gọi approve.
- Audience: `audience_scope.session_id` = session của binding; participants ⊆ audience đã ghim;
  group_ids ⊆ group của binding.
- `review_context` (session_content, `review_purpose=teaching_delivery`):
  `audience_context_revision` và `consent_revision_refs` phải bằng giá trị hiện hành từ
  `ReviewContextPort` (subject = contributor, OD-09).
- Generic library context cho `sketch_proposal` đã bị V1 từ chối [SRC S-20].
- **Đường device** (child payload, fake ticket, dispatcher):
  - 05 kiểm device binding/audience qua `ReviewAuthorityPort.decide(principal, CHILD_VIEW, scope)`.
  - Đọc 04 bằng `revalidate()` (mức hệ thống). Nếu composition cần đọc có principal, dùng reader
    Teacher được inject, có scope đúng lớp (mẫu `READER`, S-56:128), cấu hình ở composition.
  - Không bao giờ truyền device principal vào `get_record` (04 từ chối, S-24:907–908); không dựng
    principal Teacher từ request device.

### 4.9 Stale/revoke và mutation hợp lệ của 04 [SRS S-05, S-09, S-11; SRC S-24, S-58; DP]

| Thay đổi | Ai phát hiện | Kết quả ở 05 |
|---|---|---|
| Context/consent/session/audience/source/meaning/policy của 04 | 04 (`revalidate`/`apply_owner_notice` → stale + `review_revision` +1) | Identity lệch → review `stale` |
| Artifact bị quarantine | 04 (`_quarantined` trong `revalidate`) | như trên |
| Teacher sửa level (04 `revise_level`) | 04 tạo version mới | Version/hash lệch → `stale`; version mới moderate + review lại |
| Audience/consent revision của review_context | `ReviewContextPort` | `stale` |
| Moderation/review policy version | `ReviewPolicyPort` | `stale` |
| Teacher mất review scope | `ReviewAuthorityPort` | Không ghi được; eligibility không đổi trừ khi policy yêu cầu (OD-10) |

- Pull là nguồn sự thật: eligibility gọi `revalidate()` và so với entry review.
- **Mutation hợp lệ do API public của 04** (05 gây ra gián tiếp khi gọi `revalidate`):
  `pending_teacher_review → stale` với reason trong tập của 04 (CONSENT_REVOKED, SESSION_ENDED,
  CONTEXT_CHANGED, SOURCE_CHANGED, MEANING_CHANGED, AUDIENCE_CHANGED, ANALYSIS_NOT_APPLICABLE,
  POLICY_CHANGED, ARTIFACT_QUARANTINED…), `review_revision` +1, `record_version` +1, event, bump
  `eligibility:{org}`, cleanup staged; `terminate()` thay field lifecycle của version hiện tại
  (S-61). Kiểm riêng ở RV-N15c.
- 05 **không** gọi `revise_level`, `cancel`, `apply_owner_notice` hay ghi nào khác của 04.
- Notice handler `apply_target_notice` idempotent theo notice_id: đánh dấu stale + intent. Stale
  không tự quay lại effective; marker không bị ảnh hưởng.

### 4.10 Eligibility cho Child và artifact access [SRS S-07, S-13; CARD S-02, S-04; DP]

`SketchAccessEligibilityPort.decide(request)`; request gồm org, principal (device/participant),
proposal_id hoặc asset ref + version + hash, purpose, review_ref (nếu có). Eligible chỉ khi đủ:
- Có review approve `effective` cho đúng proposal/version/hash; `review_ref` (nếu gửi) khớp.
- **Không có marker terminal cho exact version (D-1).**
- `revalidate()` hiện hành vẫn pending, cùng `target_identity`.
- Participant ∈ `audience_scope`; authority/membership/session/consent hiện hành đạt.
- Moderation `passed` cho đúng hash; policy resolve được.

Không đủ → một kết quả "không khả dụng" chung (không phân biệt pending/rejected/blocked/stale).

Bên dùng (đều là fake; **không** claim đã nối gateway BE1 hay read model thật):
- `child_payload(principal, assistance_id)`: nội dung chỉ khi eligible; ngược lại chỉ status.
- Fake ticket adapter (thay CMD-60): gọi eligibility trước khi phát handle giả.
- Fake dispatcher/subscription: nhận intent `SketchReviewEligibilityChanged`, luôn hỏi lại
  eligibility trước khi đẩy nội dung.
- Fake cache: khoá `(proposal_id, version, hash, eligibility epoch)`; epoch đổi → cache cũ không dùng.

## 5. Contracts

### 5.1 DATA-24 V1 giữ nguyên + binder Sketch [SRC S-20, S-40, S-43; DP; OD-02]

- Không đổi bytes `ExactContentReviewCommandV1`/`RecordV1`, fixtures FEAT-044 và phần owner 14.
- `bind_sketch_review(command, target)` trong module 05 (mẫu `bind_video_review` của 09):
  `target_kind == "sketch_proposal"`; session_content; `review_dimension` và
  `expected_review_revision` null; target id/version/hash/source_context_revision khớp target đã
  resolve; audience theo §4.8; reason không rỗng sau trim.
- Mismatch: V1 `ShortText` ≤200, SRS `LIMIT_TEXT_SHORT` = 128 (PROPOSED). Binder siết ≤128 + NFC +
  cấm control chars (OD-02 khuyến nghị; không chặn).
- Sửa V1 (nếu cần) chỉ bằng version mới + kiểm tương thích consumer, có owner 09/12 cùng review.

### 5.2 CMD-35 `POST /sketch-proposals/{proposal_id}/reviews` (T K M V)

- Body `ExactContentReviewCommandV1`; header `If-Match` (§4.7), `Idempotency-Key`.
- Path `proposal_id` ≠ `target_id` → 422 `FIELD_VALIDATION_FAILED`.
- Response 201 (mới) / 200 (semantic duplicate), envelope API-CS-01, `data` =
  `SketchReviewResultV0` (0.1-candidate): `record` (Record V1), `decision`, `target{kind,id,
  version,hash}`, `review_etag`, `semantic_duplicate`, `replayed`. Wrapper cần vì Record V1 không có
  decision/target (M-02); không thay DATA-24.

### 5.3 Read views (0.1-candidate)

- `SketchReviewQueueItemV0` (Teacher, T07): proposal/version/hash, source snapshot ref,
  context/audience, level, display mode, safe preview (chỉ khi 04 không withheld và moderation
  không blocked), moderation outcome, `current_decision` (từ `current_entry`, D-3),
  `decision_applicable`, `version_terminal`, `approve_allowed`, lịch sử quyết định (gồm marker và
  `first_decision` làm provenance), tuổi request, `review_etag`.
- `SketchChildPayloadV0` (Child, C04): approved + eligible → text/asset ref + `review_ref`; còn lại
  `status: pending | unavailable`.
- Projection DATA-23 kết hợp (§4.1): thoả ShapeSpec DATA-23 hiện có.

### 5.4 Thứ tự guard CMD-35

1. Parse V1 strict (422); Idempotency-Key (400).
2. Fingerprint = `strict_canonical_sha256` của command chuẩn hoá + contract + proposal_id.
3. Resolve proposal (ReviewTarget) trong org; không thấy/không được phép → 404.
4. Authority hiện hành **trước** replay.
5. Receipt `(org, principal, contract, proposal_id, key)`: trùng → replay; khác → 409
   `IDEMPOTENCY_PAYLOAD_MISMATCH`.
6. Policy 05 → 409 `POLICY_UNRESOLVED`.
7. If-Match → 428/412.
8. Binder + target (§4.6 bước 1–3): lệch → 409 `STALE_CONTEXT`; không pending → 409
   `INVALID_STATE`; consent → 403 `CONSENT_REQUIRED`.
9. Moderation blocked + approve → 409; marker + approve → 409 (đọc sớm).
10. Final unit (§4.6 bước 4): hold + marker/duplicate dưới CAS + commit.

### 5.5 Bảng lỗi (mọi mã có trong SRS:1718–1731)

| HTTP | Mã | Trường hợp |
|---|---|---|
| 400 | MALFORMED_REQUEST | Thiếu/sai Idempotency-Key; cú pháp |
| 403 | FORBIDDEN_SCOPE, CONSENT_REQUIRED, GRANT_REVOKED | Admin/không có review scope; consent |
| 404 | RESOURCE_NOT_FOUND | Không tồn tại; khác org/lớp; device đọc queue |
| 409 | INVALID_STATE, STALE_CONTEXT, POLICY_UNRESOLVED, IDEMPOTENCY_PAYLOAD_MISMATCH, IDEMPOTENCY_CONFLICT | §5.4 |
| 412/428 | STALE_AGGREGATE / PRECONDITION_REQUIRED | ETag |
| 422 | FIELD_VALIDATION_FAILED, FIELD_NOT_ALLOWED | Binder; path ≠ target_id; thiếu reason |
| 503 | DEPENDENCY_UNAVAILABLE | Token không ổn định sau DECISION_ROUNDS; storage |

## 6. Ports (`B/application/ports/sketch_review.py`, candidate)

| Port | Ghi chú |
|---|---|
| `SketchReviewTargetReader.read(proposal_id) -> SketchReviewTargetV1 \| None` | Adapter thật trên `revalidate()` |
| `SketchReviewQueueSource.record(teacher, proposal_id)` | `get_record` với Teacher thật |
| `SketchModerationPort.moderate(target)` | [FX] deterministic |
| `ReviewAuthorityPort`, `ReviewContextPort`, `ReviewPolicyPort` | [FX]; publication fixture bump scope §4.6 |
| `ReviewDecisionTokenPort.token(target) / hold(token)` | Fake: `coordinator.read` + `HookedOwnerFences.hold` |
| `SketchReviewRepository.transaction()` | `CoordinatedSketchReviewRepository`; UoW: get/cas head (gồm `current_entry` theo exact version, D-3), insert/get entry, cập nhật state entry, list entry theo exact version, put moderation, get/put receipt, add intent, add audit, `get_terminal_marker` / `insert_terminal_marker` (unique, không update/delete), notice_seen/record_notice |
| `QuarantineSink.quarantine(intent)` | Bọc `CoordinatedSketchArtifactPort.quarantine(caller="be2-05")`, chỉ gọi sau commit |
| `SketchAccessEligibilityPort.decide(request)` | 05 cung cấp cho BE1/06/dispatcher |

Không có port model/provider/job.

## 7. Adapter, đồng bộ, HTTP, persistence

- Adapter đọc 04 dùng đúng các điểm public: `revalidate`, `get_record` (Teacher thật),
  `CoordinatedSketchArtifactPort.describe/quarantine` (quarantine chỉ sau commit). Không import
  repository/UoW/store/`peek` của 04. Spy allowlist trong test (RV-N15a).
- Đồng bộ [OD-12]: không model; moderation fixture tức thời.
- Không route [OD-13]; contract test ở mức DTO/service/bảng lỗi.
- Persistence in-memory [OD-14]: commit atomic, CAS, unique, fault injection.

## 8. Handoff, seam, mismatch

### 8.1 Handoff H-AI-REVIEW

| Bên nhận | 05 cung cấp | Ghi chú |
|---|---|---|
| BE2-06 | `SketchAccessEligibilityPort`, `review_ref`, `SketchChildPayloadV0`, intent `SketchReviewEligibilityChanged` | CMD-36 cần item approved hiện hành (`REVIEW_REQUIRED`, S-13:1780) |
| BE2-09 / BE2-12 | DATA-24 V1 không đổi; fixtures hiện có; ghi chú binder | Không đổi lane bạn, không merge code bạn |
| BE1 (gateway, CMD-60) | Eligibility + `review_ref`; projection an toàn | Ticket thật thuộc BE1 |
| P1 (FE-06/T07/C04) | Queue view, child payload | Fixture, chưa route |
| BE2-04 | Không ghi gì vào 04; đọc qua API public | CR-01 chỉ khi owner bác OD-04 |

### 8.2 Seam owners

| Seam | Cung cấp | Dùng | Trạng thái |
|---|---|---|---|
| Output/currency proposal | 04 | 05 | EXISTS (API public) |
| `review_revision` DATA-23 | 04 | 05 | OPEN — G-05, OD-04 |
| Khoá giữ liên 04/05 | foundation/integration | 05 | Fake dùng chung coordinator; thật OPEN |
| Moderation/review policy | BE2-14 | 05 | FIXTURE |
| Authority/consent/membership | BE1 | 05 | FIXTURE |
| Ticket/gateway | BE1 | Child | MISSING; fake |
| Child response | 06 | — | Backlog |

### 8.3 Mismatch và CR

- **M-01 / CR-01 — `review_revision` (G-05):** mở; CR-01 chỉ cần nếu owner bác ETag kết hợp.
- **M-02 — Record V1 tối giản:** wrapper; không CR.
- **M-03 — DATA-23 approved/rejected/passed:** projection; không CR trừ khi owner muốn ghi vào 04.
- **M-04 / CR-02 — result document ref:** **đóng**; `revalidate()` trả `promoted.refs()` + `AssetRef`.
- **M-05 — ShortText:** OD-02.
- **M-06 / CR-03 — audience revision** (`roster_revision` nullable): OD-09.
- **M-07 / CR-04 — fence thô:** tuỳ chọn, không chặn.
- **M-08 / CR-05 — tín hiệu an toàn generator** không lưu ở 04: moderation 05 tự đánh giá; tuỳ chọn.
- **M-09 — trùng số FEAT:** OD-01.
- **M-10 — DI-18:** residual kế thừa SK1; không CR.

## 9. File/module và thứ tự implementation

File mới (dưới `backend/`, trừ fixtures):
- `src/sketch2life/domain/sketch_review.py`
- `src/sketch2life/contracts/schemas/sketch_reviews.py` (binder, result, views; không phải schema DATA-24 song song)
- `src/sketch2life/application/ports/sketch_review.py`
- `src/sketch2life/application/services/sketch_review.py`
- `src/sketch2life/infrastructure/sketch_review/__init__.py`, `adapters.py`, `coordination.py`
  (`CoordinatedSketchReviewRepository`, token port fake, quarantine deliverer), `fakes.py`, `harness.py`
- Tests unit: `tests/unit/test_sketch_review_domain.py`, `test_sketch_review_service.py`,
  `test_sketch_review_races.py`, `test_sketch_review_eligibility.py`, `test_sketch_review_chain.py`
- Test contract: `tests/contract/test_sketch_review_contracts.py`
- Fixtures (sau OD-01): `features/<FEAT-BE2-05>/fixtures/h_ai_review/sketch_review_examples.json`,
  sinh từ builder, LF.

**Không sửa:** `ai_contract_candidates.py`, `test_ai_job_contracts.py`, fixtures FEAT-044, toàn bộ
code/test/fixture SK1, nhánh người bạn. Cần sửa file dùng chung → dừng và xin quyết định (bảng §5
của merge plan). Kiểm tên module với `tools/validate_architecture.py`; tránh hằng viết hoa
`*TOKEN*`/`SECRET`/`PASSWORD` (gate security).

| Bước | Việc |
|---|---|
| K0 | Governance (§14 bước 1–3) |
| K1 | Domain: entry/head/moderation, khoá exact, marker, ETag, target identity |
| K2 | Contract: binder, result, views, bảng lỗi |
| K3 | Ports, fakes, `coordination.py` trên coordinator chain SK1 |
| K4 | Adapter ReviewTarget trên `revalidate()`; kiểm `content_sha256` |
| K5 | Service CMD-35 + moderate + queue + final unit; replay/race |
| K6 | Eligibility, child payload, fake ticket/dispatcher/cache; notice; quarantine deliverer |
| K7 | Chuỗi 04 → 05; evidence; regression; gói review Codex (READY_FOR_CODEX_REVIEW) |

## 10. Acceptance

"Output thật của 04" = proposal do `SketchGenerationService` tạo trong `build_sketch_chain_harness`
(một coordinator, một `HookedOwnerFences`). Race dùng handshake xác định (Event có timeout, hook
`after_successful_hold`, wrapper `request_publication` ghi `publication_attempted` như R31 của SK1),
không sleep. Mọi ID dưới đây là **acceptance dự kiến**, chưa chạy.

### 10.1 Dương

| ID | Kịch bản | Nguồn |
|---|---|---|
| RV-P01 | 04 → 05: v1 pending; moderate `passed`; Teacher approve đúng ETag/hash → 201, effective, `review_revision=1`; projection `approved` + `approval_ref` | AT-UC-020-P (SRS:1295) |
| RV-P02 | Chỉ participant trong audience nhận payload; participant khác → `unavailable` | AT-UC-020-P; S-13:1825 |
| RV-P03 | Replay cùng key/payload → body gốc, `replayed=true`; semantic duplicate không tăng revision | S-04; S-12 |
| RV-P04 | Reject / request_changes có reason ghi đúng; Child không nhận; queue hiển thị quyết định trước | UC-020; S-09 |
| RV-P05 | Approve → reject cùng khoá: approve `revoked`, eligibility tắt ngay | S-11 |
| RV-P06 | Reject v1 → `revise_level` (04) → v2 → moderate + approve v2 thành công; v1 không chặn v2 | SRS:1652; §4.3 |
| RV-P07 | Contract views; projection thoả ShapeSpec DATA-23; fixtures FEAT-044 qua V1 + binder | S-20; S-22 |
| RV-P08 | Audit mẫu cho mỗi quyết định, không chứa nội dung | CS-003 (SRS:815) |
| RV-P09 | Text-only level: `ref_set` có result document; token có `artifact:{result_doc}` | §4.5 |
| RV-P10 | Reject v1 → đổi policy review 05 (entry stale) → `revise_level` → v2 → moderate theo policy mới + approve v2 thành công; marker v1 còn | §4.3 |

### 10.2 Âm

| ID | Kịch bản | Nguồn |
|---|---|---|
| RV-N01 | Device ở mọi trạng thái không approved (pending/rejected/blocked/stale/request_changes/edited) → chỉ status | AT-UC-020-N; FR061 |
| RV-N02 | Đoán asset ref → fake ticket từ chối | AT-CS-009 (SRS:1007) |
| RV-N03 | Moderation blocked → approve 409; `QuarantineIntent` trong UoW đã commit; sink chỉ gọi sau commit; sink lỗi → intent pending, giao lại idempotent; projection `blocked_unsafe` | UC-020; §4.4 |
| RV-N04 | Admin 403; device 404; không có đường preset approve (kiểm tĩnh) | UC-020; S-04 |
| RV-N05 | Teacher khác lớp/org → 404, body giống không tồn tại | S-12 |
| RV-N06 | Thiếu If-Match 428; ETag cũ (04 hoặc 05 bump) 412 + `current_revisions` | S-09 |
| RV-N07 | hash/version/context lệch → 409; path ≠ target_id → 422 | S-09; S-12 |
| RV-N08 | Thiếu reason; generic context cho Sketch → 422 | S-20; S-22 |
| RV-N09 | Audience ngoài binding/session khác; consent revision lệch → 409; consent revoked → 403 | S-09; S-11 |
| RV-N10 | Target không pending hoặc 04 withheld → 409 | SRS:955; S-24 |
| RV-N11 | Sau approve: consent revoked / session ended / source changed / artifact quarantined → `unavailable`, review stale; không tự hồi phục | AT-UC-020-N; S-11 |
| RV-N12 | Cùng key khác payload → 409; replay sau mất scope → 403/404 | S-12 |
| RV-N13 | Policy 05 không resolve → 409; policy 05 đổi → stale | S-04 |
| RV-N14 | Fake cache/subscription không đẩy nội dung sau stale/revoke | S-04 |
| RV-N15a | 05 không ghi trực tiếp 04: spy chỉ thấy call trong allowlist; module 05 không import repository/UoW/store/`peek` của 04 | §4.5; §7 |
| RV-N15b | Bất biến nội dung/source/provenance: hash source/checkpoint/render; binding; `PromotedOutput` + `content_sha256` mọi version; các version trước giữ nguyên toàn bộ. Không yêu cầu field lifecycle/revision của version hiện tại giữ nguyên (thuộc N15c) | §4.9; S-61 |
| RV-N15c | Mutation hợp lệ của 04 khi 05 gọi `revalidate`: chỉ `pending → stale` + reason hợp lệ, `review_revision`/`record_version` +1, event, bump eligibility; không thay đổi khác | §4.9; S-58 |
| RV-N16 | OD-07-A: reject v1 → ETag hiện hành → approve v1 → 409; tương tự request_changes; cả khi audience khác | §4.3 |
| RV-N17 | Device không bao giờ được truyền vào `get_record` | §4.8 |
| RV-N18 | OD-07-A: reject v1/H theo policy P1 → đổi policy 05 sang P2 → entry stale; 04 vẫn pending v1/H → moderate theo P2, ETag mới → approve v1/H → 409; eligibility tắt; không có entry approve mới | §4.3 |
| RV-N19 | Như RV-N18 với request_changes | §4.3 |
| RV-N20 | Khoá review khác, 04 không đổi: (a) approve v1/H cho audience khác ⊆ binding; (b) sau khi `review-context` đổi `audience_context_revision` → approve v1/H; cả hai → 409 | §4.3 |
| RV-N21 | Marker ⇔ có entry reject/request_changes ở bất kỳ state; marker không bị xoá | §4.3 |
| RV-N22 | **D-1:** approve audience A (effective, Child A nhận được) → reject (và biến thể request_changes) audience B ⊆ binding cùng version → trong cùng commit approve A `revoked`; Child A bị chặn qua eligibility, fake cache (entry cũ không dùng được) và fake ticket; queue hiển thị marker | Review 3 lưu ý 2; §4.3; §4.10 |
| RV-N23 | **D-3:** request_changes v1 → reject v1 **cùng exact review key** (ETag mới, key mới) → `current_decision = reject`, projection `rejected`, entry request_changes `revoked`; marker giữ nguyên byte (`first_decision = request_changes`, review_id cũ); Child bị chặn qua eligibility/cache/ticket; approve v1 → 409. Biến thể: reject khác khoá trong binding cho cùng kết quả | AC-PR01; §4.1; §4.3 |
| RV-N24 | **D-3, không còn entry hiện hành:** reject (và biến thể request_changes) v1 → đổi policy review 05 (entry thành `stale`, `current_entry = null`) → projection không bao giờ `approved` (dòng 5 bảng §4.1, `version_terminal=true`, `approve_allowed=false`); approve v1 → 409; Child bị chặn; ghi reject mới theo policy mới → thành `current_entry`, marker không đổi | AC-PR01; §4.1; §4.3 |

### 10.3 Race / replay / rollback

| ID | Kịch bản | Kỳ vọng | Nguồn |
|---|---|---|---|
| RV-R01 | Sau hold thành công, trước commit: hook khởi động thread gọi `owner_quarantine(asset)`; wrapper báo `publication_attempted` | Thứ tự `[hold_ok, publication_attempted, review_commit, quarantine_applied]`; sau đó eligibility `unavailable`, review stale | RV-PR01 |
| RV-R02 | Như R01 với `publish_owner_change` (consent revoked) | Như R01 | RV-PR01 |
| RV-R03 | Policy Sketch tắt giữa bước 3 và 4a | `sketch-policy` lệch → vòng mới → stale POLICY_CHANGED → không có review effective | RV-PR02 |
| RV-R04 | Vision write giữa bước 3 và 4a | `analysis` lệch → vòng mới → theo verdict 04 | RV-PR02 |
| RV-R05 | Quarantine result document giữa bước 3 và 4a | `artifact:{result_doc}` lệch → vòng mới → stale ARTIFACT_QUARANTINED | RV-PR02 |
| RV-R06 | Authority/policy/context của 05 đổi giữa bước 3 và 4a | Vòng mới; quyết định theo giá trị mới | RV-PR02 |
| RV-R07 | Mọi đường mutation 04 trên proposal pending (revalidate stale, owner notice, revise_level) | Mỗi đường bump `eligibility:{org}` | DI-17 |
| RV-R08 | `target_identity`/`ref_set` đổi giữa bước 1 và 3 | Lấy token mới; không commit trên identity cũ | RV-PR02 |
| RV-R09 | Publication cùng thread yêu cầu trong unit, unit commit | Defer, chạy sau khi thoát unit | RV-PR01 |
| RV-R10 | Như R09, unit rollback | Không ghi gì của 05, không bump scope 05; deferred vẫn chạy sau | RV-PR01; S-50 |
| RV-R11 | Exception trong unit | Lock nhả; không bump; lần sau thành công hoặc 412 đúng | RV-PR01 |
| RV-R12 | **D-2:** reject v1 và approve v1 song song cùng ETag (hai Teacher, hai key) | Đúng một thắng CAS, lệnh kia 412. Nếu reject thắng: approve thua, marker có. Nếu approve thắng: reject ban đầu 412; reject gửi lại với **ETag mới và key mới** → ghi được, revoke approve, tạo marker. Không bao giờ chấp nhận ETag cũ; không bao giờ có approve effective sau marker | RV-PR03; Review 3 lưu ý 1 |
| RV-R13 | Hai approve song song khác key cùng ETag | Một review; lệnh kia 412 (hoặc semantic duplicate nếu đọc ETag mới) | S-12 |
| RV-R14 | Cùng key song song | Một commit, lệnh kia replay | S-12 |
| RV-R15 | Token lệch quá DECISION_ROUNDS | 503, không ghi | §4.6 |
| RV-R16 | Notice trùng notice_id | Không đổi thêm | §4.9 |
| RV-R17 | Reject v1 song song với đổi policy review 05; rồi approve v1 | Bất kể thứ tự commit, marker có và approve → 409 | RV-PR03-F1 |

### 10.4 Contract

| ID | Kiểm | Nguồn |
|---|---|---|
| RV-C01 | Binder chấp nhận `session_sketch_approve` khi target khớp; từ chối các fixture âm | S-22 |
| RV-C02 | Bytes `ai_contract_candidates.py` / fixtures FEAT-044 không đổi (hash trước/sau) | S-43 |
| RV-C03 | Bảng mã → HTTP chỉ dùng mã SRS:1718–1731 | S-12 |
| RV-C04 | Examples JSON tái tạo từ builder; LF; ID synthetic; không đường dẫn tuyệt đối | S-01 |

### 10.5 Truy vết

| Yêu cầu | Acceptance |
|---|---|
| FR026 / UC-020-P | RV-P01..P06, P09, P10 |
| FR029 | RV-N03, N13 |
| FR061 / UC-020-N | RV-N01, N02, N11, N14, N22 |
| AT-CS-009 | RV-N02 |
| DATA-24 | RV-P03, C01, C02 |
| B21.5 review uniqueness | RV-P03, P05, R12, R13 |
| Review 1 counterexamples | RV-R01 (after-hold), R03 (policy), R05 (result document) |
| Review 2 | RV-N18..N21, R17, P10 (RV-PR03-F1); N15b/N15c (RV-N01) |
| Review 3 lưu ý | RV-R12 (D-2); RV-N22 (D-1) |
| AC-PR01 | RV-N23, RV-N24 (D-3) |

Chứng minh trên fake (coordinator, ticket, dispatcher, cache) không phải chứng minh nối database,
gateway BE1 hay read model thật.

## 11. Regression, môi trường, evidence

- Windows, `backend/.venv`; offline; không network/provider/Docker/PostgreSQL. Trong worktree 05 pin
  `PYTHONPATH`/`MYPYPATH` vào `backend/src` của worktree (venv `.pth` trỏ checkout gốc); test
  security chạy từ repo root.
- Focused: các file test mới.
- X01: bộ focused SK1/BE2-04 (175 lúc nghiệm thu) — chuỗi 04 → 05 dùng harness SK1.
- X02: `tests/contract/test_ai_job_contracts.py` và toàn bộ `tests/contract`.
- X03: unit BE2-02/BE2-03 (chain harness SK1 dựng lại A1).
- X04: toàn bộ backend unit offline (`--basetemp` trong scratch); ghi đúng pass/skip.
- Ruff, mypy trên file mới; `validate_harness`, `validate_repository_security`,
  `validate_architecture` (+ `validate_skeleton` nếu đổi cấu trúc); `git diff --check`.
- Evidence: exact-hash review report; leakage report qua fetch/cache/subscription/ticket (ghi rõ là
  fake); race report có log thứ tự handshake; allowlist report RV-N15a; audit sample; metrics JSON
  (LF); evidence note; Codex review; owner component acceptance.

## 12. Quyết định owner

Bảy OD chặn implementation có chi tiết, phương án và khuyến nghị trong
`BE205_OWNER_DECISION_PACKAGE_R2_20261019.md`: **OD-01, OD-03, OD-04, OD-05, OD-06, OD-07, OD-16**. Tất cả
PROPOSED / AWAITING_OWNER_SELECTION.

OD không chặn (có mặc định khuyến nghị, chốt trước nghiệm thu):

| ID | Quyết định | Khuyến nghị |
|---|---|---|
| OD-02 | V1 + binder; ShortText ≤128/NFC | Giữ V1; binder siết |
| OD-08 | Revoke = reject sau approve | Đồng ý |
| OD-09 | Purpose `ai_sketch`; subject consent; mapping audience revision | Fixture; contributor; port context |
| OD-10 | Teacher mất scope sau approve | Không tự thu hồi trong v0 |
| OD-11 | Fence DB thật/ADR | Gate integration riêng |
| OD-12/13/14 | Đồng bộ; không route; in-memory | Đồng ý |
| OD-15 | CR-01/03/04/05 | Không gửi trong checkpoint này |

## 13. Gate

**Offline** (component acceptance có thể phủ): K1–K7 PASS; acceptance §10 có receipt; Codex review
PASS; owner nghiệm thu component.

**Không phủ:** runtime 01/04; moderation/reviewer policy thật và moderation model; BE1 authority,
consent, ticket, read model; fence/transaction liên owner trên database thật; SQL; event delivery;
HTTP; UI FE-06/T07/C04; INTG-05; CR nếu owner chọn. Card DONE cần thêm review P2 (eligibility/
consent/asset access), P1 (queue, payload approved-only), P4 (gate/invalidation races) [S-04].

## 14. Trình tự sau khi owner duyệt

Mọi bước Git dưới đây là bước tương lai; chạy security trước mọi commit/push; không force/rebase/
cherry-pick lịch sử đã publish.

1. **Chốt base và mở nhánh task 05.** Kiểm worktree chung sạch; fetch ref chung, đối chiếu local và
   remote; ghi full SHA B của tip chung mới nhất đã xác minh. Tạo đúng một nhánh/worktree:
   `git worktree add -b feature/be2-05-sketch-review <…>/.worktrees/be2-05-sketch-review <B_SHA>`.
   Nếu tên/path đã tồn tại thì đối chiếu, không ghi đè.
2. **Owning feature và approval thật** (trong worktree 05): tạo feature folder theo OD-01; ghi
   `approvals/TASK_APPROVAL.md` với nguyên văn chỉ thị owner, các OD đã chọn, hash plan; freeze plan
   này (đã áp lựa chọn OD) vào `plan/` của feature, ghi hash snapshot; ghi substitution/ACTIVE slot
   (OD-16) trong tracker, PROJECT_CONTEXT, SOURCE_REGISTER, DECISIONS. Routing "code trực tiếp trên
   nhánh chung" cũ được thay bằng workflow mỗi task một nhánh.
3. **Triển khai K1–K7** trong worktree 05, theo đúng phạm vi đã duyệt; mọi thay đổi ngoài phạm vi
   (file dùng chung, sửa SK1, đổi V1) → dừng, xin quyết định.
4. **Kiểm thử và evidence** theo §10–§11; ghi đúng pass/skip/NOT_RUN.
5. **Dừng ở READY_FOR_CODEX_REVIEW.** Không tự nghiệm thu.
6. **Sau nghiệm thu:** commit/push nhánh task theo publication plan riêng; nhập vào
   `feature/be2-01-07` chỉ theo quyết định Git riêng của owner (tip chung phải là ancestor của tip
   task; `merge --no-ff --no-commit`, security trước merge commit và push). Task 06 tạo từ tip chung
   sau khi đã nhập 05; task 07 vẫn PARKED tới lượt.

## 15. Giới hạn

- Thông tin lane bạn chỉ từ 76959ab. Số dòng tại 58293f1.
- Hành vi coordinator/hook/token đọc trong source; chưa có probe hay code 05.
- Không chạy test; không sửa tracked file/source/test/approval; không thao tác Git mutation.
