# FEAT-064 — Kiểm chứng luồng hiện tại với Modal Vision ở dev

## T2B/T3 decision checkpoint — 2026-11-01

- Owner requested commit/push after the T2B/T3 decision ballot. The selected options and caveats are recorded in `DECISIONS.md` D-10–D-12 and `evidence/OWNER_DECISIONS_T2B_T3_20261101.md`.
- Added design plans: `plan/T2B_BE1_TO_BE2_FACT_ADAPTER_PLAN_20261101.md` and `plan/T3_STROKE_PROFILE_AND_UI_BLOCKERS_PLAN_20261101.md`. Both are design-only; the FEAT-064 parent plan remains `DRAFT`, implementation remains `NOT_STARTED`, and code/migration/runtime work still needs separate task approval.
- A3 was refined after inspecting the current BE2 types: `ContextDecision.context_revision` is `int`; consumers compare equality. The full-context digest will be a separate versioned field, compared by equality, rather than being coerced into the integer revision.
- T3 B8 remains blocked because the owner-referenced original §1 allowlist is missing from the reachable branch/worktrees. No T3 source/test path is authorized by the new plan. Child reconnect (B5) and Teacher synthetic-profile lookup (B6) remain separate future tasks.
- Publication branch: `feature/feat063-be-foundation`. Current remote tip was `3ca9c159`; owner-reported `578f3e5e` was not available in this checkout or fetchable from origin, so the approved action is a new forward docs-only commit from the remote tip.
- No implementation, tests, migration, database operation, Docker/MinIO/Modal call, real-child data or outreach to Hiếu is part of this checkpoint.

- Status: DRAFT
- Owner: Person 2 / chủ task; phân công BE1, BE2, frontend và integration cần chốt trước triển khai.
- Requested at: 2026-10-29, Asia/Saigon.
- Goal: tranh vẽ giả lập từ Child UI hiện tại đi qua BE1/BE2 tới Qwen, tạo kết quả nhận diện chưa xác nhận mà Teacher có quyền đọc ở trạng thái chờ duyệt.
- Scope: lát cắt Vision của luồng lớp học hiện có, môi trường dev cô lập, synthetic-only; lập kế hoạch trước, chưa triển khai.
- Non-goals: Parent/Teacher mới của FEAT-063, StoryRun, ASR, SAM, video, recommendation/ranking, Pixi, duyệt/sửa nghĩa và phát kết quả cho Child, production hoặc chất lượng model.
- Baseline: `origin/dev` / worktree `feature/modal-vision-dev` tại `529cbef9c71c0b225dca0d6a88f50f099e05176e`; chưa tạo hoặc đổi tên nhánh khác.
- Dependencies: hợp đồng nguồn ảnh, eligibility/consent, capability/policy và phạm vi owner được duyệt; runtime BE1/BE2 và migration riêng được kiểm chứng.
- Risks: dữ liệu canvas generic, snapshot từ client chưa được chứng minh đúng, consent runtime/schema không khớp xuyên registry/session/shared guards, adapter BE2 chỉ offline, assistance/analysis chỉ in-memory và owner fence chỉ fixture.

## Chỉ đạo hiện tại của chủ task

> Test luồng hiện tại chạy ok trên modal đi r mới làm luồng mới được nha :))) luồng mới hơi nhìu

Đây là quyết định hướng ưu tiên và yêu cầu lập plan, không phải phê duyệt source/migration/GPU. FEAT-063 Rev33 vẫn AWAITING_APPROVAL; FEAT-064 không tự triển khai S1/S2/S3 hoặc đổi kiến trúc sản phẩm.

## Bằng chứng nền

FEAT-061 đã chạy một ảnh giả lập qua demo backend → Modal: `SUCCEEDED`, 23.938 s, bốn entity, attempt 1 và Gate A ready. Cả Modal lẫn backend đã dừng. Đây không phải Child UI/BE1 runtime pass; ngân sách một request của lượt đó đã dùng hết.

BE2-02/03 và nhánh integration đã nằm trong lịch sử baseline dev. Có logic service/adapter tái sử dụng, nhưng chưa có cầu nối runtime sẵn để chỉ merge. Code source hiện tại và giới hạn của phép đọc được ghi tại `evidence/notes/SOURCE_REVIEW_20261029.md`.

## Trạng thái và giới hạn

Chỉ có hồ sơ kế hoạch được tạo trong feature này. Không sửa source, thực thi migration, chạy dịch vụ, test ứng dụng hoặc gọi provider. Approval template còn `AWAITING_APPROVAL`; không được bắt đầu implementation khi plan này còn DRAFT.

Claude review rev1 kết luận NEEDS_REVISION (0 P1, 3 P2, 4 P3). Rev2 bổ sung guard/required-profile inventory, pin pilot retry policy và run/DB authority, tách T7a/b/c, status-read sau turn, visual/Teacher-panel boundary và classroom composition terminology. Đây là xử lý finding ở mức tài liệu, chưa có Claude PASS cho rev2; OD-1–OD-4 còn mở và approval không thay đổi. Rev1 nguyên bản được giữ trong evidence để đối chiếu.

Claude review rev2 kết luận NEEDS_REVISION, đặc biệt ledger cùng DB không tự phát hiện restore về trạng thái cũ. Rev3 đề xuất witness độc lập claim trước DB/send, fail-closed khi crash/mismatch; thêm deadline wall-clock, UNKNOWN projection, outbound guard và inventories. Đây là thiết kế cần T0 chốt và kiểm thử, chưa phải cơ chế đã tồn tại. Plan DRAFT, OD-1–OD-4 mở, approval vẫn AWAITING_APPROVAL; rev2 được giữ trong evidence.

Claude review rev3 NEEDS_REVISION (1 P2 / 2 P3). Rev4 đưa witness vào tiêu chí chính, yêu cầu UNUSED có mặt/xác minh, tách đặc tả T0 và thử nghiệm sau approval, phân biệt lỗi transport không chắc. Claude sau đó review đúng rev4 và trả PLAN_REVIEW_PASS; P3-C còn cần disposition ở T0. Witness là đề xuất chưa tồn tại hoặc được chứng minh; PASS không cấp implementation approval.

Nguồn: mục `owner-feat064-current-flow-modal-vision-plan-20261029` trong `docs/context/SOURCE_REGISTER.md`, các record FEAT-060/063 và hồ sơ FEAT-061 được pin trong source review.

Rev5: chủ task chọn OD-3=B, witness file cục bộ single-host, chấp nhận rủi ro dư host rollback bằng văn bản khi duyệt M3; restore DB vẫn phải fail-closed. Plan xử lý P3-C có điều kiện không rollback để tránh suy nhầm ledger vắng sau restore. Rev5 DRAFT/NOT_STARTED, chưa review; chưa sửa approval hoặc triển khai.

Claude review rev5 trả PLAN_REVIEW_PASS kèm P3: các cột acceptance T0/T6/T8/T13 cần khôi phục tiêu chí rev4 bị rút ngắn. Rev6 khôi phục và giữ bổ sung của rev5; operator statement không tự chứng minh DB chưa rollback, thiếu chứng cứ thì UNKNOWN. Rev6 DRAFT/NOT_STARTED, chưa review hoặc approval.

Claude review rev6 trả PLAN_REVIEW_PASS, không có finding bắt buộc; đây là kết quả review plan, không phải approval. OD-1/OD-2/OD-4 và thời hạn status-read ở OD-3 còn cần chốt. Plan và approval giữ nguyên hash đã review.

Chủ task đã chọn hướng OD-1 tại `DECISIONS.md` D-04: fixed-aspect white strokes-only append-only, width theo canvas width, năm màu và Pillow PNG RGB từ operations được chấp nhận; receipt pin phiên bản. Exact aspect/palette/pixel size còn chốt tại T0. Quyết định này không là approval thực thi.

Chủ task đã chọn hướng OD-2 tại `DECISIONS.md` D-05: synthetic proof server-managed/operator, scoped và revocable; typed eligibility decision, nullable consent với origin CHECK, legacy fail-closed, BE2 consent_effective=false và eligibility_basis version riêng. Exact bảng/field/CHECK/migration/call sites còn chốt tại T0; không tạo legal consent giả hoặc nới gate dữ liệu thật. Đây không là approval thực thi.

Chủ task chọn OD-3 status-read tại `DECISIONS.md` D-06: request của chính Child, session active/paused, kiểm device key, admitted grant/membership, Child/canvas và eligibility; finished/revoked/rotated key deny, không TTL grant mới hoặc auto resubmit. Hiệu lực request đang chạy khi paused vẫn để T0 chốt; đề xuất giữ request đang chạy nhưng không cho request mới. Không cấp approval thực thi.

Chủ task chọn OD-4 tại `DECISIONS.md` D-07: Person 2 là integration owner/operator live; OwnerFenceV1 cần Person 2 và owner BE1/BE2 có tên đồng ký, phần phụ thuộc dừng nếu thiếu đồng ký. Phiên AI không là owner. Method UoW và phân công task chốt ở T0; review độc lập tại T0, T7a/b/c và trước T13. Không cấp approval thực thi.

Chủ task nêu tên owner BE1 GitHub `CaoDat-2410` và owner BE2 là Person 2 / GitHub `AnhKhoaa157` (D-08). Đây là phân công được cung cấp trong chat; chưa ghi nhận đồng ký hợp đồng của họ.

Chủ task chốt paused behavior (D-09): request AI đang chạy tiếp tục, không nhận request mới; T0 đặc tả/test và giữ các kiểm tra eligibility/freshness.

## GOAL A2 — cập nhật gate PostgreSQL (2026-11-03)

Goal A2 Rev3 ban đầu dừng vì không có database task-owned; chủ task sau đó chọn DB BE tổng `sketch2life`. Sau test-only safety-predicate changes, A2 chạy lại trên PostgreSQL 17 / `127.0.0.1:5433` theo report `evidence/A2_REV3_MAIN_DB_TEARDOWN_FIX_20261103.md`. Các finding độc lập về target URL, query override và libpq environment routing đã được sửa. Review độc lập cuối cùng kết luận **A2 Rev3 overall ACCEPTED / complete** trong phạm vi plan/addendum đã duyệt; chi tiết và giới hạn còn lại ở `evidence/A2_REV3_INDEPENDENT_REVIEW_CLOSEOUT_20261103.md`. B1/B2 chưa mở.

Rereview vòng sau xác nhận fix query `dbname`/`database`, rồi tìm finding mới: biến môi trường định tuyến libpq có thể đổi đích dù URL là loopback. Fixture hiện fail-closed trước khi tạo engine nếu `PGHOST`, `PGHOSTADDR`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGSERVICE` hoặc `PGSERVICEFILE` hiện diện; lỗi chỉ nêu tên biến. Focused guard đạt 35 passed, 65 deselected; Ruff và diff-check đạt. A2 vẫn **FIXED — XONG-CHƯA REVIEW**, chờ independent rereview. Evidence mới: `evidence/A2_URL_GUARD_REVIEW3_FIX_REPORT_20261103.md`.

## GOAL A1 — closeout sau review T7a (2026-11-01)

Finding P2 về organization scope của `CommandReceipt` đã được sửa: `put_receipt()` từ chối snapshot có organization khác repository trước khi gọi SQL; regression unit xác nhận storage không bị gọi. Focused T7a đạt 18 passed; offline GA1 đạt 649 passed, 4 skipped; Ruff, mypy, ba validator và diff-check đạt. Báo cáo sửa: `evidence/T7A_TENANT_SCOPE_REVIEW_FIX_REPORT_GA1_20261101.md`; snapshot: `GA1_T7A_TENANT_SCOPE_FIX_20261101T233641`.

Claude review độc lập kết luận ACCEPTED; T7a P2 đã đóng. M1 và T6 đã được chấp nhận ở các review trước. **Trạng thái GOAL A1: COMPLETE.** Review record: `evidence/T7A_TENANT_SCOPE_INDEPENDENT_REVIEW_GA1_20261101.md`. Việc dispatch review Codex trước đó không xác nhận được; sau đó owner cung cấp kết quả Claude review độc lập.

Chưa khởi chạy A2. Goal A2 hiện vẫn ghim HEAD cũ `1e93bc3f…`; cần owner quyết định cập nhật mốc sau khi commit A1 được amend, rồi review/ghim lại goal trước khi chạy. Trạng thái DRAFT của kế hoạch cha FEAT-064 ở phần trên vẫn là trạng thái của kế hoạch nền, không phải trạng thái Goal A1.

## GOAL A2 Rev3 — sửa finding URL guard vòng 2 (2026-11-03)

Reviewer độc lập mới phát hiện query `dbname`/`database` có thể chuyển URL path `be1_acceptance` sang database khác. Đã siết test guard để mọi override database phải khớp tên trong URL path; các URL acceptance hợp lệ được giữ lại. Focused URL guard đạt 26 passed, 65 deselected; Ruff và `git diff --check` đạt. Không chạy PostgreSQL hoặc full offline suite. A2 đang **FIXED — XONG-CHƯA REVIEW**, chờ reviewer kiểm tra lại; B1/B2 chưa mở. Evidence: `evidence/A2_URL_GUARD_REVIEW2_FIX_REPORT_20261103.md`.

## GOAL A2 Rev3 — independent review closeout (2026-11-03)

Independent review thread `01a1a16f-ac73-7d32-8964-37f1428787cf` returned **overall ACCEPTED / complete** for A2 Rev3. No source or DB operation was performed while recording the verdict. Reviewer acceptance does not start B1/B2; each needs a separate owner launch. The strict-mypy baseline error, 58 retained synthetic rows, Alembic-history mismatch, and T7b phantom-insert limitation remain documented rather than being treated as resolved.

## GOAL B1 — analysis-only and T8 pilot (2026-11-04)

The owner launched B1 Rev2 after A2 reached independent ACCEPTED / COMPLETE. B1 now has an implementation checkpoint for the analysis-only zero-Sketch path and a separate default-off in-process T8 pilot. The pilot reuses A2's canvas source adapter without editing it; audit/artifact/capability/ID adapters are explicitly labelled PILOT_FAKE_* and remain process-local, non-durable dependencies.

Focused tests and the pinned offline regression completed successfully; exact results, hashes, and limitations are in evidence/B1_IMPLEMENTATION_REPORT_20261104.md. The state is XONG-CHƯA REVIEW, not independently accepted. PostgreSQL/Alembic, Modal/GPU/provider/live calls, T9/T12/T13, and B2 were not run or started. B2 requires an independent ACCEPTED verdict and a separate owner launch.

## GOAL B1 P2 và GOAL B2 — cập nhật sau review độc lập vòng ba (2026-11-05)

Review độc lập đã đóng B1 P2 với ACCEPTED_WITH_CONDITIONS, giới hạn ở pilot local/test synthetic, default-off và loopback stub. Trước khi dùng dữ liệu không synthetic hoặc provider, vẫn cần cleanup/invalidation/reconciliation cho stale-owner analysis, review readers, regression và owner approval. Các checkpoint BLOCKED trước đó được giữ làm lịch sử.

B2 được launch riêng theo plan CHAIN_B2_REV2. Sau lần PostgreSQL đầu gặp assertion contract, owner duyệt sửa test-only cho hai assertion tại test_be1_postgres_api.py; các kết quả PostgreSQL và migration tiếp theo đều là owner-run, điều phối/reviewer chỉ đọc log. T12 còn có read-only reconciliation, đối chiếu offline và một round-trip giới hạn ở nhánh pilot_vision trên database mới. Đối chiếu offline ghi nhận 117 bảng metadata bằng 117 bảng DB và 9 hàng revision bằng 9 head thật. Round-trip đạt 48 → 39 → 48 bảng khi các bảng pilot rỗng; không kiểm tra dữ liệu, chuỗi story_run_lite hay toàn đồ thị. Phần DB của test_migrations.py chưa chạy.

Lượt rerun bốn suite PostgreSQL trên database giữ lại là owner-run: lần lượt 4, 118, 5 và 1 test passed theo summary pytest chính thức; nguồn: bảng T12 trong evidence/B2_IMPLEMENTATION_REPORT_20261104.md và log .claude/handoff/logs/GB2_T12_RERUN_20261105T013143/.

Review B2 vòng ba khuyến nghị ACCEPTED_WITH_CONDITIONS, không có P1; B2 vẫn NEEDS_REVISION cho tới khi owner quyết định riêng. T13 chỉ chứng minh timeout của hàm script-local với stub; không chứng minh job thật chuyển UNKNOWN qua worker/provider lifecycle. Mypy cho test_be1_postgres_api.py không có verdict; owner chấp nhận ghi nhận đây là giới hạn, không phải PASS. OpenAPI P3 phải xử lý trước frontend/client integration. Finding N-1 yêu cầu test PostgreSQL mức route cho POST request/cancel trước D9 hoặc frontend. Điều kiện orphan stale-owner B1 vẫn giữ nguyên. OWNER_MODAL_CALL_APPROVED=NO.

Lần rerun bốn suite dùng runner không được pin hash trong approval. Runner PowerShell đối soát từng được pin hiện không còn trong thư mục script cục bộ; nguyên nhân chưa xác định. Chưa có baseline mypy của file test trước B2, nên chưa thể quy lỗi INTERNAL ERROR cho trước hay sau B2.

## GOAL B2 — owner acceptance with conditions (2026-11-05)

Owner chấp nhận Goal B2 ở trạng thái ACCEPTED_WITH_CONDITIONS theo chỉ thị trực tiếp "Chấp nhận B2". Review độc lập vòng ba khuyến nghị ACCEPTED_WITH_CONDITIONS, không có P1; quyết định chấp nhận là của owner. Phạm vi gồm T9, T13 và T12 theo plan B2 cho pilot local/test synthetic, default-off, loopback stub.

T12 đóng có điều kiện trong phạm vi đã duyệt: round-trip chỉ nhánh pilot_vision ở trạng thái trung gian với bảng pilot rỗng; không dữ liệu, không chuỗi story_run_lite, không toàn đồ thị. Phần DB của test_migrations.py NOT RUN; mypy cho test_be1_postgres_api.py NO VERDICT và chưa có baseline trước B2. Mọi kết quả PostgreSQL là owner-run, chưa được reviewer xác minh bằng kết nối DB độc lập.

Các điều kiện tiếp tục ràng buộc: đóng OpenAPI P3 trước frontend/client; xử lý orphan stale-owner B1 trước dữ liệu không synthetic/provider; giới hạn claim T13 ở timeout của hàm script-local với stub; chạy test PostgreSQL mức route child request → job → status trước D9 hoặc frontend; ghi nhận runner rerun bốn suite không được pin hash và runner đối soát không còn trong thư mục script cục bộ, nguyên nhân chưa biết.

Quyết định này không cho phép gọi Modal/GPU/provider/live, commit/push/merge/stage, xóa hoặc dọn hai DB, gộp nhánh origin/codex/feat063-modal-backend-completion-20261103, bắt đầu goal sau B2, dùng dữ liệu không synthetic/provider thật hoặc tuyên bố production readiness. OWNER_MODAL_CALL_APPROVED=NO; B1 và B2 vẫn chưa commit.
