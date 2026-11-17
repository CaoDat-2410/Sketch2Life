# Task approval

- Status: APPROVED
- Approver: repository owner, direct instruction in this Codex conversation
- Approved scope: Create `feature/be2-01-14-integration` from `feature/be2-01-07`, combine the task 8–14 branch, and begin offline integration/testing. The user separately clarified that the requested task-7 PR target is `feature/be2-01-07`; that PR is empty because both refs already point to the same commit.
- Plan revision: 1 (`plan/PLAN.md`)
- Approved at: 2026-10-20 (Asia/Saigon)
- Notes: Offline integration and checks are authorized. Live testing is deferred until Lightning is operating normally again. No `dev`/`main` merge, deployment, full-card acceptance, or runtime adoption is granted by this record.

## Verbatim user instruction

> V thì g làm gì tiếp ? tạo PR đẩy lên nhánh gộp cho tôi đi sau đó check lại nếu ok thì gom của nhánh task 8 tới 14 vào 1 nhánh để bắt đầu ghép và test offline và live sau khi có lighing hoạt động bth trở lại

Clarification for the task-7 PR target:

> task 7 → feature/be2-01-07

## Branch rename addendum — 2026-10-20

The owner instructed: “Đổi tên nhánh này đi nó là be gộp r thì bỏ từ 1 tới 14 đi”.
The approved local candidate branch is now `feature/be2-backend-ai-integration`;
the rename does not expand the integration or acceptance scope.

## Runtime-readiness analysis addendum — 2026-10-20

- Status: APPROVED
- Approver: repository owner, direct instruction in this Codex conversation
- Approved scope: analyze BE2 tasks 01–14 and prepare a source-traced, staged
  command/readiness runbook for use after Lightning is operating normally again.
- Plan: `plan/BE2_01_14_RUNTIME_READINESS_PLAN.md`, revision 1.
- This authorizes analysis and documentation only in this step. It does not
  authorize starting Lightning now, installing packages, provisioning/migrating
  a database, calling providers, implementing missing adapters, or accepting any
  card. Future commands remain gated by the owning feature approvals and the
  actual environment/source prerequisites.

## Verbatim user instruction

> Ok gộp r thì bây giờ đầu tiên cần phân tích toàn bộ từ task 1 tới task 14 để sau khi phần lighing hoạt động trở lại thì đưa lệnh vào mà chạy lun á

## Cross-lane test scaffold sub-scope — 2026-10-20

- Status: APPROVED — scaffold only
- Approver: repository owner, direct instruction in this Codex conversation
- Plan: `plan/CROSS_LANE_INTEGRATION_PLAN_DRAFT_20261020.md`, revision 1;
  approved portion is the test-only scaffold defined in §11.
- Scope: add a FEAT-057-owned offline edge registry, its test-only integration
  scaffold documentation, and tests that validate registry completeness and
  prevent an edge from being labeled PASS without an evidence reference. Record
  the focused test and validator results in feature-local evidence.
- Excluded: wiring any producer to a consumer, changing production code or
  card-owned contracts, shared SQL/migrations, runtime/provider/Lightning,
  route mounting, changing card acceptance/status, commit, push, or merge.
- This approval does not approve the full X01–X09 implementation plan; each
  card-owned edge still requires G0 contract confirmation and any needed owner
  approval before behavior changes.

## Verbatim user instruction

> OK làm cho tôi trước đi sai sửa sau ra cái khung trước đi

## Offline cross-lane implementation addendum — 2026-10-20

- Status: APPROVED — integration-owned offline composition/adapters/tests only
- Approver: repository owner, direct instruction in this Codex conversation
- Plan: `plan/CROSS_LANE_INTEGRATION_PLAN_REV2_20261020.md`, revision 2.
- Authorized worktree/branch: existing `feature/be2-backend-ai-integration` at
  candidate HEAD `1649b72978877d82b4d7662040ff3555dee0a3a7`; preserve its
  pre-existing uncommitted scaffold and evidence changes.
- Allowed: FEAT-057-owned service composition and adapters under
  `backend/src/sketch2life/infrastructure/cross_lane/`, behavior tests under
  `backend/tests/integration/be2_cross_lane/`, and the matching FEAT-057 plan,
  approval, decision, status, context, source-register, and evidence records.
- Required: use actual BE2 producer/consumer services and their existing public
  candidate contracts; producer-created values; consumer state/lineage
  assertions; deterministic fakes only for unavailable external systems.
- Stop condition: do not modify card-owned source/contracts or migrations. If
  an edge needs a missing or unadopted card contract, leave it
  `NOT_IMPLEMENTED` and record the exact owner decision needed.
- Excluded: shared SQL/database provisioning, HTTP route mounting, live service,
  provider/Lightning, changes to card acceptance/status, `dev`/`main` merge,
  commit, push, and deploy.

## Verbatim user instruction

> V thì bạn hãy check và review sau đó nối lại luồng giữa 2 phần cho tôi đi

## Supplemental BE2-VIDEO-LIFECYCLE/1 persisted seam approval — 2026-10-22

- Status: APPROVED — exact FEAT-057 composition manifest below, offline only.
- Card: FEAT-057 / cross-lane composition.
- Scope: `plan/BE2_01_07_08_PERSISTED_VIDEO_SEAM_SCOPE_REV2_DRAFT_20261022.md`
- Scope SHA256: `F170809FCBB71D1B588960466350D6086568EFB6384232AB0F178DF7D350C052`
- Previous exact approval target: `1C199CF6CD1E7C2F2D5981D253256278079D840197CB1B05D304E2620FD2E90D`; the original owner approval quote below is retained verbatim.
- Owner-authorized metadata-only amendment: the machine-specific Worktree locator was removed; contract terms, §2 boundaries, §3 environment limits, and §4 owner manifest are unchanged. Owner instruction: “sửa theo đề xuất” in the current Codex conversation on 2026-10-22 (Asia/Saigon). No scope expansion is authorized.
- CR08-01 adopted as `BE2-VIDEO-LIFECYCLE/1`, covering A/S/B and identity-failure exactly as defined in §2 of that hash-pinned scope. BE2-01 owns each transaction's begin/commit/rollback; BE2-08 participates through the typed transaction-bound contract and writes only BE2-08 rows. No SQL connection is exposed through an application port.
- This approval freezes only the following FEAT-057 composition test path:
  - `backend/tests/integration/be2_cross_lane/test_persisted_video_worker_flow.py` (NEW)
- Source/test work and database creation may begin only after all three FEAT-044/050/057 approval records contain this scope hash and their exact §4 owner manifests, and that state is verified.
- Local database permission is limited to §3: a dedicated, newly created loopback PostgreSQL 17 database with a random `be2_xlane_...` name and synthetic data, used only for offline transaction/persistence verification. No shared, staging, or production database; no provider, Modal, Lightning, HTTP server, deployed service, or runtime. Existing approved schema only; no schema or migration additions or edits.
- This addendum narrowly amends the 2026-10-20 exclusion of shared SQL/database provisioning: only the test-owned local database described in §3 is permitted. It does not approve shared SQL/database use, schema or migration changes, or paths outside the manifest above.
- Excludes BE2-09, BE2-14, D4, BE1 implementation, route/envelope changes, card acceptance/status changes, and durable BE2-07 source-fence implementation. The fence remains a separate gate and X01 remains `PARTIAL` until a fence held through finalization is proven.
- Approver: project owner, direct instruction in this Codex conversation; recorded 2026-10-22, Asia/Saigon (exact wall-clock time not asserted).

### Verbatim owner approval

> Chốt adopt contract `BE2-VIDEO-LIFECYCLE/1` gồm A/S/B và identity-failure theo §2 của Rev2, SHA256 `1C199CF6CD1E7C2F2D5981D253256278079D840197CB1B05D304E2620FD2E90D`. Cho phép cập nhật ba approval record FEAT-044, FEAT-050, FEAT-057 với scope hash và file list chính xác theo §4. Cho phép PostgreSQL cục bộ cô lập, dữ liệu tổng hợp, chỉ để kiểm thử offline theo §3. Chưa sửa source/test hoặc tạo database cho tới khi các approval được ghi và xác minh. Giữ durable source fence ngoài scope và X01 ở PARTIAL.
