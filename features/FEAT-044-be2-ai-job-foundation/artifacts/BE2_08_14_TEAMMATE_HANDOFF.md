# Bàn giao BE2-08–14 cho người thực hiện thứ hai

Ngày: 2026-10-16, Asia/Saigon. Tài liệu bàn giao công việc trên repository;
nguồn yêu cầu vẫn là SRS/FEAT-040 và plan/approval đúng card.

## Phân công đã chốt

| Người thực hiện | Card | Số lượng |
|---|---|---|
| Người gửi / executor hiện tại | BE2-01–BE2-07 | 7 |
| Người nhận tài liệu này | BE2-08–BE2-14 | 7 |

BE2-07 là knowledge/script của người gửi. Người nhận dùng contract của07 để làm video,
không implement lại07. Chia đều số card không đồng nghĩa mọi card bằng nhau về khối lượng.
Không chuyển trách nhiệm identity/session/artifact authority của BE1 hay composition của P4
sang người nhận. Tổng backlog giữ14 card.

## Bối cảnh và nguồn cần đọc

Sketch2Life hỗ trợ học sáng tạo cộng tác: Teacher quản lý lớp/nhóm, AI hỗ trợ có kiểm soát,
video được Teacher duyệt đúng final version/hash/audience trước playback. Giữ original artwork
và provenance. Baseline là Master SRS v3.1, Android/React Native và FastAPI; các model/provider/
profile hoặc numeric policy chưa adopt không được suy từ code lịch sử.

Mọi đường dẫn dưới đây tính từ root checkout của người nhận:

1. `AGENTS.md`; `docs/context/PROJECT_CONTEXT.md`; `docs/context/SOURCE_REGISTER.md`.
2. `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md`.
3. `features/FEAT-040-four-person-delivery-plan/artifacts/TEAM_TASK_BREAKDOWN.md`, cards08–14
   và07 như input contract bên ngoài; FR/UC/DATA/CMD registry liên quan.
4. `features/FEAT-044-be2-ai-job-foundation/plan/BE2_ROADMAP.md` và `BE2_EXECUTION_TRACKER.md`
   trong cùng thư mục plan, ưu tiên amendment hiện tại trên đầu file.
5. `docs/adr/ADR-0015-four-person-role-and-integration-allocation.md` và
   `docs/adr/ADR-0018-be2-durable-ai-job-runtime.md`.
6. FEAT-044 `evidence/notes/PHASE_A_HANDOFF.md`, `PHASE_B_B6_HANDOFF_20261016.md` và
   `PHASE_B_B6_A17FIX01_CLOUD_RECEIPT_REVIEW_20261016.md` trong cùng thư mục notes.

Đọc source cho card đang lập plan, không cần nạp toàn lịch sử mọi feature. CONFIRMED,
PROPOSED/TBD, candidate, adopted và actual runtime proof là các trạng thái khác nhau.

## Foundation đang ở đâu?

- Branch nguồn bàn giao: `feature/be2-01-ai-job-foundation`.
- A17-fix01 sửa scenario thứ tự dispatch, giữ đủ negative capability checks và real RQ path;
  không phải bằng chứng một lỗi bypass authorization của code sản phẩm.
- Raw cloud archive được Codex nhận/kiểm tra:221 B2–B6 +224 Phase A PASS,0 failure/error/skip;
  durable43/43 required PASS. Source manifest5b76868d/46files.
- Local B6 units25 PASS; focused ruff/mypy và validator PASS. Xem note/metrics để lấy hash đầy đủ.
- **Studio A17-fix01 NOT_RUN; B6-CR01 open; BE2-01 IN_PROGRESS; B-12 HANDOFF.**
- OwnerFence/audit/artifact component fixtures vẫn ASSUMED_CONTRACT. Production key provisioning,
  real owner adapters, live route/provider, actual purge, deployment và cross-owner sign-off
  không được coi đã có từ checkpoint này.
- Cloud test-role adjustment không phải production requirement hoặc lệnh đổi quyền DB bên nhận.

Foundation cung cấp job/attempt/state/retry/cancel, idempotency/dedup, SQL repository/UoW/CAS,
transactional outbox, Redis/RQ lease/recovery và attempt capability. Provider trong proof là fake.
`ai_jobs` có7 bảng; migration foundation đã publish không được sửa ngược để làm card mới.

Các vùng source để tra khi cần nối:

```text
backend/src/sketch2life/domain/ai_jobs/
backend/src/sketch2life/application/ports/ai_jobs.py
backend/src/sketch2life/application/services/ai_jobs.py
backend/src/sketch2life/contracts/schemas/ai_jobs.py
backend/src/sketch2life/contracts/schemas/ai_contract_candidates.py
backend/src/sketch2life/infrastructure/ai_jobs/
```

Contract shape tồn tại không có nghĩa business card đó đã implement hoặc schema đã adopt.

## Thứ tự của người nhận

Ưu tiên **12 → 14 → 08 → 09 → 10 → 11 → 13**. Việc đầu tiên là **lập plan BE2-12**.
Nếu07 chưa sẵn cho08, có thể làm11 rồi13 khi01/12 và các external port/policy của chúng đủ;
sau đó trở lại08–10. Không bắt activity/preset chờ full video và không tự nhận07 để bỏ chờ.
08 có thể làm component trên pinned fixture port theo plan/approval, nhưng chưa được báo
integrated/runtime-ready với07 hoặc full08 DONE.

| Card | Đầu ra chính | Dependency và điều kiện nghiệm thu cốt lõi |
|---|---|---|
| **08** | CMD-40; DATA-27; LibraryResolver/VideoGenerator/MediaValidator; worker/provider và copy hooks |01+07; exact bundle/audience/profile/rights; library cũng chờ final Teacher review; actual generate path phải có video decode được và evidence theo profile đã duyệt |
| **09** | CMD-41/42; shared DATA-24; DATA-27 review/playback refs và intents |08+shared review contract05; Teacher duyệt exact final version/hash/audience; current consent/grant/session eligibility; stale URL/ETag/review không bypass |
| **10** | CMD-43; DATA-28; retry-new-run/skip/end intents, receipts |01+08+BE1 session port; chỉ exhausted, Teacher explicit; cả3 actions có positive/negative/race tests; không auto-skip/end hoặc reset terminal job |
| **11** | CMD-45; DATA-29; activity assignment/adaptation/execution và outcome refs |01+12; published source, mỗi-child age/safety/preparation theo policy đã adopt; adaptation không sửa master; outcome qua BE1 port |
| **12** | DATA-33 content versions; sole CMD-48 dispatcher; publication/review/recall |01+shared DATA-24; capability/separation rules; edit tạo version mới; exact review trước publish; recall chặn resolver mới nhưng giữ provenance |
| **13** | CMD-48 preset delegate; pinned config; bounded automation/override intents |01+12+BE1 session/config port; library edit không đổi session pin; Teacher override làm old intents stale/cancel; không bypass mandatory review/consent |
| **14** | CMD-48 AI-policy delegate; limits/kill switch; ProviderCopyLifecycle registry/receipts |01+12; adopted policy/profile trước activation; disable chặn/new work và xử lý in-flight; chỉ báo Deleted khi đủ actual verification; explicit Pending/Unsupported/Exception khi thiếu |

Truy vết card gốc:

- BE2-08: FR034/037/038/040, UC-023/025, DATA-25/27/shared20, FIX-UX-05, AT-CS-011.
- BE2-09: FR035/036/040, UC-024, DATA-24/27, AT-CS-010.
- BE2-10: FR038/039, UC-025/026, DATA-25/27/28, AT-CS-011.
- BE2-11: FR041/042/043/shared044, UC-027/028, DATA-29/shared33, FIX-UX-06.
- BE2-12: FR056/062, UC-035, DATA-33/shared24/35, FIX-GOV-01.
- BE2-13: FR052/053/054, UC-032/033, DATA-33/shared06/35, FIX-GOV-01, P-NFR-16.
- BE2-14: FR029/030/054/056, UC-036/037, DATA-33/25/shared35, FIX-GOV-01, P-NFR-13.

Đối chiếu trạng thái FR/UC trong SRS trước code; bảng này không tự adopt PROPOSED/TBD.
08 không mặc định Wan/L4/40–60s/narration từ lịch sử. Library-only/fake không hoàn tất
nghĩa vụ actual generation. 11 không làm reflection/portfolio CMD-46/47 của BE1.
13 không xây workflow/rule engine tổng quát;14 không tự chọn production budgets/TTL/provider.

## Contract giao nhau: giữ đúng owner

| Contract | Owner | Cách phối hợp |
|---|---|---|
| DATA-25, job repository/lifecycle | Người gửi01 | Consume ports, không shortcut bằng SQL direct |
| DATA-24 exact review | Người gửi05 |09/12 dùng chung, purpose/audience rõ; không tạo schema khác |
| DATA-26, CMD-38/39 | **Người gửi07** |08 nhận bundle/script version/hash/audience, context/source revisions và eligibility;09/10 giữ lineage/invalidation |
| DATA-33, CMD-48 dispatcher | Người nhận12 | Một closed typed dispatcher;13/14 là delegates, core non-AI policy về BE1-15 |
| ProviderCopyLifecycle | Người nhận14 | Shared registry/contract; người gửi04 và người nhận08 implement provider-specific hooks |
| Artifact/access/audit/session/config/lifecycle authority | BE1 | Versioned ports/receipts; không viết trực tiếp bảng BE1 hoặc tạo duplicate gateways |
| Composition, deployment và combined integration coordination | P4 | Giao component adapters/tests/config requirements rõ version; P4 nối, owner sửa component |

07 bàn giao grounded claim-source map, immutable bundle/script refs, fantasy/factual separation,
Teacher corrections và generation-ready/needs-content-action outcome. Script/source edit tạo
version mới làm downstream cũ mất eligibility theo contract. Retry10 revalidate current context/
policy, giữ prior failure/source lineage và không hồi sinh approval cũ. Không chờ live Sketch
để làm library09/12; shared DATA-24 schema/fixture có thể dùng ở candidate scope ghi rõ.

Mỗi handoff ghi version/owner, DTO/errors, source/version/hash/audience/purpose refs, examples,
synthetic positive/negative fixtures, conformance command và phần ASSUMED/NOT_RUN.
Field/schema mới phải map nguồn/invariant/producer/consumer/constraint/test; không thêm field
"để dành". Technical field cần lý do thực tế. Persistence mới dùng forward Alembic revision;
không sửa migration foundation hoặc tự thêm foreign key sang BE1.

## Lấy checkpoint và tạo nhánh riêng

DECISIONS125 cho phép bàn giao sớm một **candidate planning branch**, vì dev chưa có checkpoint
foundation tại publication preflight. Không merge BE2-01 vào dev trong lượt này.

Trong clone/worktree riêng và sạch của người nhận, xác nhận repo/remote/status trước:

```bash
git status --short
git remote -v
git fetch origin
git log -1 --oneline origin/feature/be2-01-ai-job-foundation
git switch --no-track -c feature/be2-12-content-publication origin/feature/be2-01-ai-job-foundation
git branch --show-current
git rev-parse HEAD
```

Ghi HEAD vừa nhận làm base trong plan card12. `--no-track` tránh nhánh12 tracking nhánh01;
khi owner authorize publication card12, push đúng tên nhánh12 và đặt upstream cho nó.
Nếu working tree có thay đổi hoặc tên nhánh đã tồn tại, giữ nguyên và kiểm tra trước;
không reset/clean/overwrite để ép chạy lệnh trên.

Mặc định về sau vẫn **mỗi card một nhánh → review → merge dev → card tiếp theo từ dev đã cập nhật**.
Nhánh planning sớm này phải đồng bộ foundation đã review trước integration. Không rebase/reset
nhánh đã chia sẻ khi chưa phối hợp owner. Không mở sẵn7 nhánh hoặc gom7 card vào nhánh12.

BE2-12 là backlog ID, không đồng nghĩa FEAT-012. Tìm feature mapping hiện có; nếu thiếu,
chọn FEAT ID còn trống theo template/harness và ghi mapping. Không dùng FEAT-044 chứa code
toàn bộ08–14. Lập plan/acceptance trước code; lưu approval thật đúng card. Nếu approval đã
hợp lệ thì dùng lại, không hỏi lại chỉ vì đổi AI session. Phân công/card planning không phải
blanket approval implementation. Code WIP hiện giữ1; ghi phối hợp trước khi bật luồng code thứ hai.

Không sửa checkout Studio của người gửi bằng git pull; package Studio vẫn pin base993a26c.
Nếu sau này chạy trên checkout có HEAD mới vừa publish, phải có package revision riêng hỗ trợ
base đó; manifest source không đổi không làm mất hiệu lực guard HEAD của wrapper hiện có.
Máy người nhận không cần credential, database, local ZIP hoặc folder cá nhân của người gửi
để đọc source và lập plan. Bản AI prompt/handover cá nhân và raw evidence giữ local theo
publication policy; tài liệu này đủ entrypoint cho clone mới.

## Kiểm thử và điểm bắt đầu

Mỗi card có owning feature context/plan/decisions/approval/status/evidence. Component fake,
actual adapter/provider runtime và integrated/device proof được báo riêng. Required skip =
NOT_RUN, không PASS; fake purge không actual Deleted; fixture video không actual generated.
Giữ cả FAIL/before và PASS/after cùng exact source/environment/time/command/input hash.

Trước commit/push chạy security và các validator theo AGENTS/harness; test/ruff/mypy đúng
phần đổi. Không đổi validator để vượt gate. Domain độc lập framework/provider/storage;
dependencies hướng vào trong. Không commit `.env`, credentials/keys, seed accounts hay child
data. Firebase chỉ Authentication; không Storage/Firestore/Realtime Database. Không mang
S3/Lightning/Runpod credential/endpoint vào mobile; không sửa môi trường FEAT-018/Wan.

**Việc làm ngay:** xác nhận checkout/base; đọc nguồn card12; kiểm kê DATA-24/DATA-33/CMD-48;
lập plan12 với outputs/modules, publication/capability/recall rules, field rationale,
positive/negative tests, dependency/decision labels và owning feature mapping. Dừng trước
implementation nếu card12 chưa có approval thật. Người gửi tiếp tục gate Studio/closure của01.
