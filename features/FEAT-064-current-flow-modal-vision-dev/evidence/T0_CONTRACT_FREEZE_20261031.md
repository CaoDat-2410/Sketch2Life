# FEAT-064 T0 — Hợp đồng, guard và manifest thực thi

> **Giới hạn:** Chỉ là tài liệu T0. Approval T0 chỉ cho phép tạo bộ tài liệu này; không phê duyệt sửa code, schema/migration, chạy backend, DB, MinIO, Modal/GPU, hay bất kỳ test nào. Các lựa chọn dưới đây là hợp đồng đề xuất để owner chốt, không phải bằng chứng đã chạy. Không có API nào được ghi là đạt; mọi ca runtime bên dưới là kế hoạch. Không ký thay; chữ ký `OwnerFenceV1` vẫn `CHƯA KÝ`.

- Feature: FEAT-064, `feature/feat063-be-foundation`, snapshot 2026-10-31.
- Kế hoạch tác vụ T0: `plan/T0_CONTRACT_FREEZE_EXECUTION_PLAN_20261031.md`, SHA-256 `9C62504CD2AD018B47F7D36B8B64D47016FAE19D3D8C3FADD4C911C98925945E`.
- Kế hoạch cha rev6: `plan/PLAN.md`, SHA-256 `CD7B3236A55E280D4722166C73AF462835DEC8503BCE882CE0CFF9D5601F9665`; `DRAFT / NOT_STARTED`.
- Approval T0 hiện có trong FEAT-064 `approvals/TASK_APPROVAL.md`; chỉ cho phép tài liệu T0. Approval file không được sửa trong công việc này.

## 1. Preflight và hash đầu vào

Hash SHA-256 của bytes trong working tree tại thời điểm đọc:

| Đầu vào | SHA-256 |
|---|---|
| T0 execution plan | `9C62504CD2AD018B47F7D36B8B64D47016FAE19D3D8C3FADD4C911C98925945E` |
| FEAT-064 `PLAN.md` rev6 | `CD7B3236A55E280D4722166C73AF462835DEC8503BCE882CE0CFF9D5601F9665` |
| FEAT-064 `DECISIONS.md` | `FD7B9ED0943509B31C07284B2B42EA9FBA26EE203D68BAA09E512D5CD8230644` |
| `CONTRACT_OUTLINE_DRAFT.md` | `63937D10EA9513AC74FFB4049E29FE91072E33B8CAE246409137CE46F740496E` |
| `ELIGIBILITY_GUARD_INVENTORY_DRAFT.md` | `D3F109F99824F2CF085DD528A4BB85888AA7E3F17A335D406F6B3F5282134615` |
| `OWNER_PATH_MANIFEST_DRAFT.md` | `F5AFC985357CD0610D8A31CF4954C6F28C0A8B7B2E81D111560ACDE72F8A9EEE` |
| FEAT-064 `approvals/TASK_APPROVAL.md` (read only) | `6538E2161E0C98B5E8BFB0C7A4544969080A3F2F04AEB432F31BAED8A4C4BFD9` |
| FEAT-063 `OWNER_DECISION_SLIP_20261031.md` | `DEBD034D269E4EC3D3026BEA02A1E9C43855F4064AE91A1FE4E189FBEB95FEA8` |
| FEAT-063 B3 ownership manifest | `EA0326EA7ABAA1637BD57AFA7B5318DF98B8178CEE1BF6F925678E226F68802E` |
| FEAT-063 B3 owner matrix | `747891D220467198A7C2867FF5D78C61065AA81D621BA534C42757B0223A70F1` |
| FEAT-063 Rev36 plan | `8DD1989926DCA4E0312ABD79032EE4AF862A9FE1AAAB786A6BC4BC6DB5389751` |
| FEAT-064 `SOURCE_REVIEW_20261029.md` | `ADA2428ED3CE6D1CDF9413BE603CB5471FEB4A293FFDF91027DF5675FBF139E9` |
| `application/ports/assistance.py` | `5E205659F2ABBE3F3AD5E5459F05A64139D51DCE8A7DB19B60FD3426BD90E338` |
| `application/ports/vision_analysis.py` | `2F36D096127930A25B60057B48F47DF726EB77E132808A20B2E5B15E7E5584AE` |
| `application/services/be1_runtime.py` | `BD1D57B2E69ABB71F6FB933BF66CC499F36CA8F79D1FE03F6CE99FFD6AEBC3E4` |
| `domain/core_foundation.py` | `E5AE89B8AEB3471C1DDE10788F91995623949EF7701FAB672EE1A32A89FB8F3C` |
| `application/services/core_foundation.py` | `FB1B6B0466AEF9EEEDE0803DAAD9B118A51619BE3F6D5D75850AF10A9F584E7E` |
| `contracts/schemas/video_review.py` | `96787057F1631D6597DB266338582F6C0D76EB0D2EBE6487376CE727BE43AE2F` |
| `domain/understanding/image_admission.py` | `34480DA59FD2436DB6A4FC92380FC0AD9284E8F4EB4C46B61CD2578AAB349DF5` |
| `application/services/image_admission.py` | `6EB7C081DF8D738AA03F5FF4BA284647F3C89606BAD81758DF9BF45AC193BD91` |
| `backend/pyproject.toml` | `26436E10897FD8B13D5F23E9B28E088EA9E7D332053E1E39D5847ED9ADC0DA2E` |
| `backend/uv.lock` | `219C81CAAE5DB3054417B755F220277CAEF50B4F34FEF953A9FA484298388BA9` |
| Modal endpoint recipe `deployment/modal/qwen_vision_v2.py` | `8163EDB6431394BA9A1C9A1105D3B18ECEAB60F90AC7A3801E42FA2C36DD4792` |
| Vision V2 schema `contracts/schemas/vision_v2.py` | `BEA0511C400B452B86FF32A90CB5F65DF4C191A72A857B1024C30A65628CD0D8` |
| Child canvas `apps/child-ui/app/index.tsx` | `57B5ACE6E94D69655E80A74ED3E99BC0AE5F6B06C19D942D865B3206C65FAE3C` |
| Child `sessionClient.ts` | `B0D5C9CD89ADF29BF7A3D900BD31C9B7CCD08553A9059A1280493C54B3675830` |
| Child `apiClient.ts` | `16A14A65D05C400AF9AA0E11DDDCFBFF4F212A077859B183F90036C1FF36CB66` |
| Lightning transport `lightning_client.py` | `A8F0FE7BFC0B5770D5AB335B787353C42633C639DB6E0A0A9600DF3707AA4DA1` |
| Runtime settings | `C2AC5064EC9FEA4B8E3F591CE4B923C72A804DBC4F3EC5E50CFE218A905DBFB6` |
| Synthetic smoke sample `backend-demo-smoke-20261029-v1/results.jsonl` | `003DFC99811F6C0F831E137F1EA01C3F37F2031D6E53880015152C887BFF9C44` |

Preflight `git status --short` khớp các thay đổi local owner đã được nêu trước T0 cộng với plan T0; không có file đầu ra nào trong bốn tên mục tiêu tồn tại trước khi tạo. Các thay đổi đó được giữ nguyên. Source review tĩnh chỉ; không chạy Alembic CLI, backend, DB, dịch vụ hay test.

## 2. S1 — Quyết định owner và cổng còn mở

| Quyết định | Áp vào hợp đồng T0 | Tình trạng / cổng |
|---|---|---|
| B1 | `AnhKhoaa157` là owner BE2 riêng FEAT-064; không sửa ADR-0015 | Ghi nhận phân công, không phải chữ ký |
| B2 | BE1 paths do `CaoDat-2410`; BE2 paths do `AnhKhoaa157`; `app.py`/`router_composition.py` do integration owner `AnhKhoaa157`, P4 review | Người review X01–X18 và P4 chưa nêu tên: `NEEDS_OWNER` |
| B3 + B3b | Phương án migration X: FEAT-064 T1 sở hữu biểu diễn synthetic một lần; Rev36 S2 tái dùng; chủ schema `data_origin`/consent là BE1 | Owner BE1 chưa xác nhận riêng B3:X/B3b; không bắt đầu migration nếu thiếu xác nhận |
| B4 | `OwnerFenceV1` cần ba role signatures: BE1, BE2, integration | Tất cả `CHƯA KÝ`; thiếu đồng ký thì T7b dừng |
| B5 | P2 giữ composition; P4 review | Tên P4 chưa có: `NEEDS_OWNER` |
| B6 | FEAT-064 pilot trước Rev36; S1 không phải điều kiện pilot; nếu S1 chạy trong pilot thì classroom flag giữ bật | Ranh giới ghi vào manifest; không áp Rev36 |
| B7 | Chưa cho DB tạm; chỉ sau plan T12 và phạm vi bằng văn bản | T12 DB `BLOCKED` đến khi có approval/phạm vi riêng |
| B8 | T0 documentation-only; T13 Modal gọi riêng sau T12 với chấp nhận rủi ro | T0 không mở T1–T13; T13 approval chưa có |
| D-03 | Witness local single-host; chấp nhận rủi ro dư bằng văn bản sau T12 | M3 approval phải có text risk; không tuyên bố chống OS rollback |
| D-04 | Canvas trắng, strokes-only, fixed aspect, append-only, Pillow RGB PNG | Chốt contract đề xuất tại §4; pixel geometry/proof còn cần owner xác nhận |
| D-05 | Synthetic proof riêng; typed decision LEGAL_CONSENT/SYNTHETIC_DEV/DENIED; không fake effective | Schema đề xuất §3; exact owner confirmation/call-site approval còn mở |
| D-06 + D-09 | Child own-status active/paused với scope hiện hành; request tiếp tục khi paused nhưng không nhận mới | Được ghi trong §5; triển khai vẫn cần T1+API approval |
| D-07 + D-08 | P2 integration/live operator; BE1=`CaoDat-2410`, BE2=`AnhKhoaa157` | Hai role của cùng người cần xác nhận cách ký; chưa ký |

## 3. S2–S3 — Eligibility dispositions và synthetic proof

CSV `T0_GUARD_DISPOSITIONS_20261031.csv` liệt kê 17 dòng: 15 dòng nguồn inventory hiện tại và hai caller được phát hiện khi quét lại (`VisionAnalysisService` và `video_review.py`). **Lệch plan:** inventory ghi “14 điểm” nhưng bảng hiện có 15 dòng dữ liệu. Vì vậy tiêu chí literal 14/14 không thể được xácה minh như viết; bảng này xử lý đủ 15 nguồn gốc và 2 caller thêm vào, cần sửa số ở plan trước T1.

| Disposition đề xuất | Số | Nội dung |
|---|---:|---|
| `SYNTHETIC_TYPED_ONLY` | 10 | Model/profile representation, lifecycle Start/admit/group/turn, scoped device write, private canvas export, BE1 application transition, BE2 member/service gates. Mỗi lần đánh giá phải trả typed outcome; không đổi boolean legal consent. |
| `KEEP_LEGAL_GATE` | 3 | Registry legal consent operations, shared legal helper semantics, record/gallery/legal data routes. Giữ nguyên hành vi hiện tại; synthetic operator issuance là boundary riêng, không gọi “effective”. |
| `OUTSIDE_PILOT_DENY` | 4 | Progress/help, generic artifact upload/download, core-foundation legal-only path, video-review projection. Ngoài selected path: giữ deny/current behavior, không blanket bypass. |

`be1_sessions.py` hiện có legal-effective checks ở Start `:746–756`, device admit `:1307–1314`, group assign `:1586–1593`, progress/help `:1750–1757` và `:1815–1822`, turn `:1946–1953`. Chỉ các selected lifecycle operations được disposition typed synthetic; progress/help không được mở. `be1_runtime.py:143–227` là verified shared-device write authority, không được dùng làm status-own guard: status-read cần policy riêng và không đòi turn/group active theo D-06.

### Hợp đồng đề xuất `SyntheticDevEligibilityEvidenceV1`

1. **Issuance:** operator command chỉ hoạt động khi `environment in {local,test}` và explicit `pilot_enabled=true`; không có public Child endpoint để cấp proof. Record do server tạo, versioned, append-only, revocation bằng event/sequence chứ không sửa lịch sử issuance.
2. **Binding:** `evidence_id`, `schema_version`, `data_origin=SYNTHETIC_DEV`, `organization_id`, `class_id`, `child_profile_id`, `purpose_ref`, `run_id`, `issued_by`, `issued_at`, `expires_at`, `revoked_at/revocation_revision`, `pilot_enabled`, `policy_version`. Mọi yêu cầu phải match scope đầy đủ và thời gian hiện hành; thiếu/mismatch/expired/revoked => `DENIED`.
3. **Typed decision:** `EligibilityDecisionV1 = LEGAL_CONSENT | SYNTHETIC_DEV | DENIED`, kèm `basis_version`, subject/scope, decision time và reason code kín. LEGAL path chỉ dựa trên consent pháp lý hợp lệ; synthetic path chỉ dựa trên proof này; không gán `consent_effective=true` cho BE1/BE2.
4. **Profile schema (đề xuất X, chưa phải DDL):** thêm `data_origin` với `REAL`, `SYNTHETIC_DEV`, `LEGACY_UNCLASSIFIED`; `consent_id` và `consent_purpose_ref` nullable có điều kiện. CHECK: `REAL` yêu cầu hai tham chiếu consent; `SYNTHETIC_DEV` không chứa tham chiếu legal và phải có proof scope hợp lệ; `LEGACY_UNCLASSIFIED` không cấp eligibility, giữ nguyên dữ liệu tham chiếu để audit. Các ràng buộc cross-row phải qua FK/lookup service, không thể giả định CHECK SQL đọc bảng proof. Hàng hiện có backfill `LEGACY_UNCLASSIFIED` trừ khi migration được owner thiết kế khác.
5. **BE2:** `MemberFact.consent_effective`/`ContextDecision.consent_effective` vẫn `false` với synthetic; thêm `eligibility_basis` có version. Gate mới chấp nhận `SYNTHETIC_DEV` chỉ ở pilot contract đã duyệt; REAL đi legal path; legacy/pending/revoked deny. Không điều phối một profile synthetic bằng consent row giả.

### So sánh với Rev36 S2

| Thuộc tính | D-05 / T0 đề xuất | Rev36 S2 | Kết luận |
|---|---|---|---|
| Synthetic origin | `SYNTHETIC_DEV`, proof gắn org/class/child/purpose/run/expiry/revocation và pilot flag | Draft nêu `SYNTHETIC_TEST`, `REAL`, `LEGACY_UNCLASSIFIED` | Khác enum; theo phương án X cần một tên canonical do BE1 owner xác nhận, không tạo hai enum |
| Consent refs | Nullable có CHECK theo origin; synthetic không có legal refs | S2 cũng đề xuất nullable/cross-origin CHECK | Cùng hướng, chi tiết CHECK khác cần chốt theo model hiện tại |
| Existing guards | Chỉ selected FEAT-064 callsites có typed branch riêng sau approval | Rev36 S2 ghi existing BE1 guards không đổi; code mới mới đọc origin | Phải giữ nguyên behavior ngoài pilot; FEAT-064 selected branches là scope riêng có approval, không phải blanket S2 relaxation |
| Legacy | `LEGACY_UNCLASSIFIED` luôn deny; không suy legal status từ non-null refs | Backfill legacy/unclassified; không cấp eligibility | Cùng hướng; phải giữ refs cũ để audit |
| BE2 | synthetic `consent_effective=false`, basis version riêng | Rev36 S2 không định nghĩa runtime basis | T0 bổ sung cho pilot; không gán thành S2 behavior |
| Ownership/migration | BE1 sở hữu schema; T1 tạo một lần; Rev36 S2 tái dùng | S2 dự kiến có migration riêng | Phương án X owner đã chọn nhưng BE1 chưa xác nhận riêng; không tạo duplicate revision |

Static Alembic metadata review (không chạy Alembic): repository snapshot có 22 revision scripts. Đếm literal `down_revision` leaves cho 10; tính `depends_on` dependency tạo effective frontier 9. Candidate BE1 parent được ghi ở B3 là `20261024_0005`; lesson-library revision khai `depends_on=20261024_0005`. Đây là phân tích graph text, không xác nhận DB state/head và không áp migration. Không có DB tạm được phê duyệt nên T1 schema acceptance/T12 DB rehearsal bị `BLOCKED` đến khi có plan, DB scope và approval riêng; downgrade/backfill thực tế chưa xác minh.

## 4. S4 — Canvas source, render, admission

Đây là profile pilot đề xuất, dựa D-04 và source hiện tại; mọi giá trị phải được pin bởi owner trước code.

| Contract | Giá trị đề xuất |
|---|---|
| `CanvasOperationProfileV1` | Aspect 1:1; logical coordinates finite `[0,1]`; accepted operations append-only, monotonic revision; only current five palette colors `#FFD21F`, `#FF596C`, `#1685F8`, `#31C978`, `#9250E8`; unsupported operation/color/width/point rejected server-side. |
| Width mapping | UI exposes brush sizes 5/9/14 (`apps/child-ui/app/index.tsx:421–423`). Proposal normalizes each to logical viewport width 400: ratios `0.0125`, `0.0225`, `0.035`; at 1024 px canvas these become 12.8/23.04/35.84 px. Responsive UI currently does not prove 400-unit geometry; owner must freeze this mapping or substitute a sourced canonical width. |
| `CanvasSourceExportV1` | `organization/session/group/canvas`, source epoch, revision, ordered accepted operation IDs, canonical operation digest, export ID, immutable source reference. Do not accept client-supplied image or silently omit rejected history. |
| `RenderDerivationReceiptV1` | `renderer_id=sketch2life-strokes-only-pillow-v1`, Pillow version, renderer version, source epoch/revision/digest, dimensions, `image/png`, `RGB`, derivation digest and creation time. |
| Renderer | Pillow rasterizes only accepted operations, in revision order; 1024×1024 RGB, white background, no gallery image, no suggestion overlay, no hidden history. Deterministic normalized-coordinate mapping; rounded line endpoints/joins; circular caps/joins. UI code currently renders segments from `points.slice(1)` (`index.tsx:351–360`), so one-point stroke has no visible segment; proposed renderer emits no dot for one point to match that behavior. Owner must confirm before code. |
| `VisionAdmissionBindingV1` | PNG; encoded bytes ≤5,000,000; pixels ≤4,000,000; longest edge ≤4096; frames=1. 1024² is 1,048,576 px and edge 1024, within current domain limits, but encoded byte limit still enforced. Include actual admission policy/version, source/render hashes and receipt ID. |

Current child canvas includes existing artwork/suggestion overlay (`index.tsx:363–366`), so pilot must use a separate strokes-only white presentation. `sessionClient.ts:185–207` currently appends strokes with idempotency key/revision; it does not establish that a PNG export exists. Current UI brush geometry and one-point rendering are references only, not an implemented renderer contract. `backend/uv.lock:1499–1502` pins Pillow 12.3.0 while `pyproject.toml` allows `Pillow>=11,<13`; propose receipt records exact installed Pillow version and deployment pins it. No production stack decision is made.

## 5. S5 — Gateway, auth and projections

All routes below are **proposed contract names**, not existing endpoints. Exact router path and DTOs require T1 approval. Child client must persist request ref and never automatically resubmit after timeout/unavailable.

| Capability | Caller / authorization | Result and failure behavior |
|---|---|---|
| Create canvas export | Child device key + verified grant, admitted membership, active session/group/turn and current source authority; synthetic eligibility only for pilot | Server creates immutable source/render/admission receipts from accepted operations. Reject unsupported profile/history/overlay, stale epoch/revision, proof failure, size or admission failure. |
| Request Vision | Child device; exact own `org/class/session/group/child/canvas/source_ref`; source and eligibility current; pilot enabled | Return `202` + stable `request_ref/status_ref` before provider work, within Child API 12-second client bound. No candidates/raw payload to Child. No auto retry. Provider remains existing `/v2/vision`, `IMAGE_ONLY`, same selected profile only after T13 approval. |
| Cancel own | Same device grant and own request scope; cancellation only before possible-send | Idempotent cancel receipt. After possible-send, report current state/UNKNOWN; do not claim cancel prevented provider billing. Generic unavailable for foreign/unknown request. |
| Status-own GET | Device key matches; grant + membership remain `admitted`; request belongs to same Child/canvas; current eligibility; session `active` or `paused`. No active turn/group requirement. | Read-only allowed statuses only; generic `REQUEST_UNAVAILABLE` for unknown, foreign, expired, revoked, rotated or finished. Keep request ref on UI, no resubmit. Paused request already in progress continues; paused admits no new request. |
| Teacher pending list/read | Verified Teacher identity, current assignment to org/class/session, request’s exact scope and current disclosure/eligibility | Read-only analysis-only projection; status `pending/unconfirmed`; no approve/confirm/correct action, no Sketch generation/stage. Hidden when current authority is lost. |

The 12s client bound comes from `apps/child-ui/src/services/apiClient.ts:79–85`. It is an HTTP UI timeout, not a provider completion deadline. No status-own route is evidenced in current UI/backend. `video_review.py:45–60` still enforces legal-effective consent and stays outside this pilot path.

## 6. S6 — Invocation guard, deadlines and late response

### `InvocationGuardPort` proposal

- Before outbound: verify approval/run/host/DB identity, current request/source/eligibility, unused witness, and `attempt_count=0`; make durable invocation claim and policy pin before any provider byte can leave.
- Pilot `max_attempts=1`. Missing/invalid proof, capability refusal, transport setup error before possible send, or failed claim must produce zero outbound requests. If send may have happened and authenticated complete response/provenance is absent, use `UNKNOWN/HOLD`; do not retry, refund, re-arm or create another attempt.
- A completed response is applicable only to the same request/attempt and still-current source/eligibility/fence. Late, stale, mismatched or partial evidence => `UNKNOWN/HOLD`, not another call. Do not equate HTTP 401/403/404/422 or client exception with “no GPU cost” unless transport evidence proves no request was sent.
- Keep invocation ledger separate from existing A1 quota/reservation accounting. Do not change default retry policy for nonpilot jobs.

### Measured source limits and unresolved wall deadline

| Bound | Current source | Meaning |
|---|---|---|
| Child HTTP client `12_000 ms` | `apps/child-ui/src/services/apiClient.ts:79–85` | Client abort bound only |
| Backend `ai_request_timeout_seconds=120.0` | `settings.py:74–76`; transport default `120.0`, `urlopen(timeout=...)` at `lightning_client.py:79–105` | Socket/request timeout argument; not evidence of enforced total wall-clock bound across DNS, connect, retries, body or response processing |
| Modal web function `timeout=150`, `startup_timeout=300`, `scaledown_window=30`, `max_containers=1` | `deployment/modal/qwen_vision_v2.py:77–92` | Modal configuration values; separate startup and web execution limits |
| One observed sample `23.938 s` | `features/FEAT-061-modal-qwen-vl-endpoint/evidence/backend-demo-smoke-20261029-v1/results.jsonl:3` | Single sample only; not a deadline or percentile |

No enforceable total HTTP wall-clock deadline or completion margin is established by these sources. Proposed relation remains `attempt_deadline > elapsed_pre_send + enforced_HTTP_wall_deadline + completion_margin`; the HTTP wall value and margin are `NEEDS_OWNER`. Proposal: use a monotonic deadline around the entire transport call and response processing, test cold/warm/deadline/cancel behavior after approvals; do not treat `urlopen(timeout=120)` as proof. Modal's 150s execution cap can exceed the current backend request setting; resolution/late-response policy must be frozen before T6/T13. Until then, possible-send followed by timeout => `UNKNOWN/HOLD` and cap remains closed.

## 7. S7 — Unit-of-work method inventory

`T0_METHOD_INVENTORY_20261031.csv` has all 36 protocol members: 18 `AssistanceUnitOfWork` methods + transaction and 16 `AnalysisUnitOfWork` methods + transaction. The category is the selected pilot contract disposition, not a claim that the method is already durable or used at runtime.

| Disposition | Count | Pilot rule |
|---|---:|---|
| `ATOMIC_DURABLE` | 13 | Selected acceptance mutations and repository transaction must commit atomically; semantics require a database-backed implementation and tests. |
| `READ_ONLY` | 12 | Pure read in the selected contract; must read current owner fence/eligibility consistently; it does not imply persistence exists. |
| `FAIL_CLOSED` | 11 | Cache, corrections/invalidation and Sketch intent are outside selected analysis-only path. If invoked, reject/rollback visibly; never silent no-op. `add_sketch_intent` is forbidden. |
| `DURABLE_ONLY` | 0 | No method is classified as merely durable without an atomicity requirement in the selected path. |

At source, current assistance/analysis repositories are in-memory fakes (`infrastructure/assistance/fakes.py`, `infrastructure/vision_analysis/fakes.py`); `owner_fence_fixture.py` is a fixture, not runtime persistence. No live SQL runtime adapter was verified. Planned tests are listed row-by-row in CSV and remain unrun.

## 8. S8 — `OwnerFenceV1` and analysis-only invariant

Proposed versioned fence binds `organization_id`, `session_id`, `group_id`, `canvas_id`, source epoch/revision/digest, eligibility basis/version, verified actor/grant identity, request/result IDs, and monotonic fence revision. BE1 owns source/eligibility fact updates; BE2 owns request/analysis; P2 coordinates composition/integration. Every mutation that changes source or eligibility advances the fence atomically with its owner fact.

Acceptance commit re-reads source authority, proof/current eligibility and fence inside one transaction, then atomically stores analysis observation/provider result, current pending review pointer and reservation settlement/receipt. No DB transaction spans a provider call. Conflict or stale fence creates no Teacher-current pending pointer; result remains non-applicable and is handled as conflict/UNKNOWN according to whether send may have happened. Concrete UoW methods and exact transaction boundary are enumerated in §7/CSV.

Three role signatures required before T7b: BE1 `CaoDat-2410`, BE2 `AnhKhoaa157`, integration owner `AnhKhoaa157`; each currently `CHƯA KÝ`. Owner decision assigns P2 both BE2 and integration roles, so whether this is one person signing two distinct roles or requires a separate signer is `NEEDS_OWNER`. No production fixture fence may be wired into runtime.

**Zero-Sketch invariant:** selected pilot returns only a pending/unconfirmed analysis projection. It must not create a `SketchIntent`, `assistance.sketch_intent_simulated` event, outbox entry, Sketch stage call, renderer/generation job, or auto-approval—on initial completion, replay, recovery or restart. Existing nonpilot A1 continuation remains unchanged. Any accidental selected-path call to `add_sketch_intent` fails the transaction.

## 9. S9 — Run manifest, witness and residual risk

Run manifest fields proposed: `manifest_version`, `run_id`, task/approval/plan hashes, host identity, DB identity/generation, environment/pilot flag, scope, model/profile/revision, source/export/admission hashes, invocation ID, `max_attempts=1`, witness ID, created/expiry times, operator, restore declaration/evidence reference and outcome. Run IDs are server/operator-created, never client-selected.

### Windows witness proposal (not verified on a filesystem)

Use a host-pinned local witness directory outside the DB volume, cloud sync and DB backup/restore set. Require an existing immutable `UNUSED` record bound to host/run/DB/manifest. Consume by exclusive OS create of a sibling `CONSUMED` claim on the same volume; flush record contents and file handle, and flush directory metadata where the chosen filesystem/API supports it. Never overwrite or delete/recreate the `UNUSED` file. If exclusive creation, durability, identity or directory flush semantics cannot be demonstrated for the selected filesystem, fail closed as `NOT_SENT_CAP_UNAVAILABLE`; do not assume NTFS or exFAT semantics.

Order proposed: validate manifest and current unused witness → exclusive consume claim → commit durable invocation ledger → record possible-send immediately before HTTP → outbound call. Only one winner can send. Crash after possible-send or any uncertain persistence/send point is `UNKNOWN/HOLD`, cap closed, no retry. Missing/mismatched/unreadable/quarantined token => unavailable/closed. Concurrent loser with proven consumed token => closed. DB restore where ledger row disappears but host witness is consumed => `UNKNOWN`, never infer `NOT_SENT`. A full host restore can roll back both DB and witness; this design does not prove OS anti-rollback. T12 fault-injection requires its own scoped approval and throwaway identities; no primitive has been tested here.

**Residual-risk text prepared for owner to paste in a future M3/T13 approval:** “The pilot witness is local to one host and is not protected against full-host rollback. Restoring the host may restore an UNUSED witness and allow a later request to make another paid provider call; repeated restores may incur repeated charges. Only synthetic data may be used. Any host/DB restore invalidates the run authority; the operator must stop the prior run and obtain a new manifest and approval. This process reduces accidental duplicate calls but does not guarantee OS-level rollback prevention.” This is draft text, not approval or acceptance of a live call.

## 10. S10 — T1–T12 execution manifest

`T0_EXECUTION_MANIFEST_20261031.csv` expands B3 O01–O18 into exact file rows; it records current source hash, task/hunk proposal, writer/reviewer from the owner matrix, planned tests, DB/provider scope and approval gate. It includes `NEEDS_OWNER` rows for absent runtime store/migration/fence/witness paths and absent Teacher pending panel path; no wildcard is used. All implementation approvals remain separate; T13 provider scope is zero until T13 approval. The CSV is a proposed execution boundary, not an authorization.

### Proposed order / gates

| Order | Work | Entry condition / boundary |
|---|---|---|
| T1 | BE1 typed synthetic eligibility/profile + selected guards, coordinate T3/T6/T7a | Separate code/schema approval pins T0 hashes; BE1 confirms migration X; no DB apply unless later T12 approval |
| T2 | Lifecycle/data representation compatibility | T1 contract and legal/legacy denies; no blanket bypass |
| T3–T5 | Child canvas profile, export/render/admission, request/read API and projections | Exact files/writers; use 1024² pilot proposal only after owner freeze |
| T6 | Invocation guard/provenance and `max_attempts=1` | Wall deadline and late-response policy must be decided; no provider call before T13 |
| T7a | Minimum durable selected assistance/analysis state | Migration owner/order and schema review; no DB until T12 approval |
| T7b | `OwnerFenceV1` and atomic UoW | All three role signatures and independent review; absent signature blocks |
| T7c | Run ledger + Windows witness | Exact FS/host/DB identity and risk text; throwaway-only tests after approval |
| T8–T11 | Runtime/UI/read-only Teacher pending path and recovery | No Sketch side effect; existing A1 path preserved |
| T12 | CPU validation + isolated `*_be1_acceptance` DB rehearsal | Separate approval with explicit DB/data scope; until then BLOCKED |
| T13 | One live Modal request | Separate live approval after T12; one synthetic call; operator owns start/stop; residual risk accepted in approval |

Owner and reviewer per exact path are in the CSV. P4 identity and per-file independent reviewers remain `NEEDS_OWNER`; no implicit assignment is made.

## 11. S11 — Future approval blocks (draft only)

- **T1 code/schema approval:** pin final T0 plan + four output hashes; exact files/hunks from execution manifest; allowlisted tests; migration owner and dependency; explicit no DB apply, no provider call, no real data; BE1 confirms option X. Do not write approval here.
- **T12 test/DB approval:** pin T12 plan, test inventory, throwaway database identity and network/credential scope; synthetic-only rows; explicit create/restore/drop/recovery operations and rollback evidence; provider disabled. Current status: no DB approval, so blocked.
- **T13 live approval:** separately pin one-run manifest/approval/model profile/source hash/host+DB identity/witness proof and one-call cap; synthetic fixture only; name live operator; include risk text in §9; specify timeout/UNKNOWN reconciliation and stop condition. Current status: not approved.

## 12. S12 — Plan rev6 stale references; proposed rev7 wording only

No plan edit is made in T0. Current `plan/PLAN.md` still mentions FEAT-063 Rev33 at `:30`, `:34`, `:56`, `:148`, `:173–174`, `:184`, while current coordination baseline is FEAT-063 Rev36/B3. It also shows OD-1–OD-4 as open at `:171–174`, although D-04–D-09 and the owner slip resolve the high-level choices; exact contract freeze, test evidence, cosignatures, deadlines and API scopes remain open.

Proposed rev7 clarification: replace Rev33 references in FEAT-064 coordination with the current FEAT-063 Rev36/B3 artifacts; state pilot FEAT-064 precedes Rev36 and that Rev36 S1 is not a pilot prerequisite, while its classroom flag remains on if S1 is present. Change OD-1/OD-2/OD-3/OD-4 from “owner choice pending” to “high-level owner decision recorded; exact typed contract, values, per-file owner/reviewer, signatures and test/DB/live gates still need T0/T-N evidence.” Keep Parent/Teacher foundation, SRS revisions and production policy outside FEAT-064.

## 13. S13 — Owner questions (10 max) and self-check

### Questions requiring an owner answer

1. BE1 owner `CaoDat-2410`: confirm option X, canonical `SYNTHETIC_DEV` enum/CHECK, one-time migration ownership and Rev36 S2 reuse; confirm selected registry/session/canvas boundaries without changing other legal gates.
2. Name independent reviewers for each X01–X18/manifest path and identify P4 for composition review.
3. Confirm whether `AnhKhoaa157` can sign both BE2 and integration roles on `OwnerFenceV1`, or provide a separate integration signer.
4. Freeze canvas geometry: 1:1 1024², 400-unit width basis, ratios, one-point no-dot behavior and exact RGB/PNG determinism; if not, provide alternative sourced geometry.
5. Decide a measured HTTP total wall deadline and completion margin; specify cold-start handling and late complete response behavior. Current sources do not prove a total deadline.
6. Pin exact request/export/cancel/status-own/Teacher pending route paths, DTOs and error/status codes; confirm active/paused behavior follows D-06/D-09.
7. Name the T12 DB owner and approve isolated `*_be1_acceptance` scope only after its plan exists; otherwise keep T12 blocked.
8. Confirm exact Windows filesystem/API/host pin and durability mechanism for witness, and approve the residual-risk wording in a future M3/T13 approval.
9. Name writer/reviewer for new durable store, migration, owner-fence and witness paths (O16) and Teacher pending panel route/UI (O18).
10. Decide whether to issue a separately approved PLAN rev7 update for stale Rev33/OD wording.

### Required checks §6

| # | Check | Result |
|---:|---|---|
| 1 | Guard rows | 15 source inventory rows plus 2 newly found direct caller rows are represented in the CSV. Plan’s “14” count is a documented mismatch, so literal `14/14` is **BLOCKED pending plan correction**. |
| 2 | Citation re-open | Relevant `path:line` references were re-opened from current source during T0; implementation hashes are listed in execution manifest. Static documentation check only. |
| 3 | No false runtime/API pass, approval or signature | Met in artifact wording; no runtime/test claim and all fence signatures `CHƯA KÝ`. |
| 4 | Synthetic != consent | Met in proposed contract; BE1/BE2 legal consent booleans remain false for synthetic; REAL/LEGACY/pending/revoked deny. |
| 5 | Time bounds sourced | Child 12s, backend 120s, Modal 150/300/30/1 values have repository references; 23.938s is labeled one sample only. Total HTTP deadline remains unresolved. |
| 6 | Unresolved items marked | `NEEDS_OWNER` questions and TBD manifest rows are explicit. |
| 7 | Boundary / secret / child-data check | Only the four requested evidence files are created; they contain no absolute local path, token, `.env` value or real-child data. Existing local owner changes preserved. |

### Validator record

Commands were run from the repository root after preparing these artifacts. They are repository validators only and do not execute backend/API/DB/Modal or establish runtime behavior.

| Command | Exit / actual verdict |
|---|---|
| `python tools/validate_harness.py` | Exit 0; `HARNESS_VALID`; `approval_gate=enabled`; `frontend_asset_gate=enabled` |
| `python tools/validate_repository_security.py` | Exit 0; `REPOSITORY_SECURITY_VALID`; `publishable_files_scanned=5938`; environment files, seed accounts, credentials/signing keys, external reference documents excluded; `absolute_machine_paths=absent` |
| `python tools/validate_architecture.py` | Exit 0; `ARCHITECTURE_VALID`; Python dependency direction, mobile feature isolation, frontend asset gate, mobile AI boundary valid; Firebase data products absent |
| `git diff --check` | Exit 0; no output. Git does not include untracked files in this check. |
| Separate trailing-whitespace scan of the four new files | 0 lines with trailing spaces/tabs. |
| PowerShell CSV parse + manifest source-hash recheck | Guard 17 rows/14 columns; method 36 rows/10 columns; manifest 48 rows/15 columns; zero row-width errors and zero existing-file baseline-hash mismatches. |

No unit/integration test, backend, DB, MinIO, Modal, GPU or Alembic command was run. No runtime behavior is verified by these checks.
