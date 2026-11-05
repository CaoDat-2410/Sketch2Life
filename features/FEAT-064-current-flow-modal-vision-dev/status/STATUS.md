# FEAT-064 status

## GOAL A2 — database BE tổng (2026-11-03)

- Owner đã chọn dùng database BE tổng hiện có `sketch2life`, không tạo DB riêng. Quyết định và giới hạn: `DECISIONS.md` D-13; plan addendum `plan/CHAIN_A2_MAIN_BE_DB_ADDENDUM_20261103.md`.
- PostgreSQL test hiện chưa thể nhận tên DB này vì safety predicate chỉ cho `be1_acceptance`; addendum cho phép đúng thay đổi test-only để chấp nhận exact `sketch2life` trên loopback và thêm regression guard.
- Cấm migration, reset/drop/truncate/broad cleanup và thay đổi hàng BE hiện có. Chỉ được ghi synthetic IDs mới và cleanup đúng những ID do fixture lượt hiện tại tạo; phải xác minh database/user/owner/host/port/version chỉ đọc trước khi test.
- A2 đã chạy lại theo addendum và fresh launch; các P2 của review độc lập về URL, database override và libpq environment routing đã được sửa và rereview. Kết luận độc lập mới nhất: **A2 Rev3 overall ACCEPTED / complete** trong phạm vi các plan/addendum đã duyệt. Các giới hạn còn lại và trạng thái B1/B2 được ghi ở `evidence/A2_REV3_INDEPENDENT_REVIEW_CLOSEOUT_20261103.md`.

Evidence quyết định: `evidence/A2_MAIN_BE_DATABASE_SCOPE_DECISION_20261103.md`.

## A2 Rev3 independent review — NEEDS_REVISION (initial review; superseded 2026-11-03)

- Review found one P2 in `backend/tests/integration/test_be1_synthetic_pilot_postgres.py`: the `sketch2life` guard accepts any loopback port and username, although the approved target is PG17 / `127.0.0.1:5433` / user `postgres`.
- The implementation report's preflight supports the completed run, but the reusable test guard does not fail closed on a wrong local instance. Require exact port/user for the `sketch2life` exception and add negative predicate cases, then request another independent review.
- Recorded PostgreSQL residue: 58 additional synthetic rows remained after the first failed teardown; the report says later runs added no further rows. Do not clean them without separate authorization.
- Initial verdict was **NEEDS_REVISION / not accepted**. This historical finding was subsequently fixed and accepted; see the independent review closeout below. B1 and B2 remain unopened.

## Current decision checkpoint — 2026-11-01

- The T2B/T3 ballot outcomes are recorded in D-10–D-12 with design-only plans and a documentation-only approval. See `evidence/OWNER_DECISIONS_T2B_T3_20261101.md`.
- T2B and T3 implementation: **NOT_STARTED; separate task approval required**. Parent plan revision 6 remains `DRAFT / NOT_STARTED`.
- A3 uses an explicit versioned context digest alongside the existing integer `context_revision`; the latter is not retyped or treated as an ordered whole-context version.
- T3 B8 remains blocked: the original §1 path allowlist referenced by the ballot is not present in reachable history, so this plan authorizes no T3 source/test path. B5 reconnect and B6 Teacher profile routes remain separate later tasks.
- T12 PostgreSQL is waiting for a disposable database and local-only `BE1_TEST_DATABASE_URL`; B4b remains deferred. Hiếu has not been contacted.
- Branch publication is to `feature/feat063-be-foundation` from remote base `3ca9c159`. The reported `578f3e5e` is unavailable locally and from origin; no force-push is authorized.
- No code, test, migration, DB, Docker, provider or Modal operation was performed in this checkpoint.

- Status: DRAFT
- Plan revision: 6
- Implementation status: NOT_STARTED
- Updated: 2026-10-29, Asia/Saigon.

## Đã làm

- Chủ task chọn kiểm chứng Child UI/BE1 hiện tại với Modal trước khi làm luồng mới.
- Đọc baseline `529cbef9`, source/approvals liên quan; viết plan và hồ sơ draft.
- Approval template giữ AWAITING_APPROVAL; chưa có approver/scope.
- Hai review độc lập đã kiểm tra draft ban đầu; Claude sau đó review rev1 với NEEDS_REVISION (0 P1, 3 P2, 4 P3). Rev2 xử lý F1–F7: inventory/required fields, retry/run/DB authority, T7a/b/c, status-read, UI và composition boundaries. Scoped re-review không còn material F1–F5; sửa thêm nhãn list_profiles, không gọi là enrollment. Chưa phải approval hoặc Claude PASS cho rev2.
- Rev1 nguyên bytes/hash được giữ trong `../evidence/notes/PLAN_REV1_REVIEWED_20261029.md`.
- Static checks rev1 ở `../evidence/notes/PLAN_REVIEW_AND_CHECKS_20261029.md`; kết quả rev2 ghi riêng tại `../evidence/notes/CLAUDE_PLAN_REVIEW_REV2_20261029.md`.
- Claude review rev2 NEEDS_REVISION: 1 P2 và sáu finding P3 được liệt kê. Rev3 bổ sung witness độc lập DB, deadline wall-clock, UNKNOWN projection, guard outbound, guard inventory và method-level UoW, status-read lifetime. Chưa có Claude PASS cho rev3.
- Claude review rev3 NEEDS_REVISION (1 P2 / 2 P3); rev4 đồng bộ AC18 với witness, tách T0 thiết kế khỏi T7c/T12 tests, UNUSED phải hiện hữu, làm rõ kết quả transport và guard loser.
- Claude review đúng rev4: `PLAN_REVIEW_PASS`, có P3-C. Chủ task chọn OD-3=B; rev5 gộp lựa chọn và P3-C, chưa có review rev5, vẫn DRAFT/NOT_STARTED. Review rev4 không phải approval thực thi.
- Claude review rev5 PLAN_REVIEW_PASS kèm P3 về acceptance bị rút ngắn. Rev6 khôi phục tiêu chí T0/T6/T8/T13, giữ phần mới rev5 và làm rõ bằng chứng restore; Claude review delta rev6 PLAN_REVIEW_PASS, không còn finding bắt buộc. Review plan không phải approval.
- Plan revision 6 SHA-256: `CD7B3236A55E280D4722166C73AF462835DEC8503BCE882CE0CFF9D5601F9665`. Rev5 nguyên bytes tại `../evidence/notes/PLAN_REV5_REVIEWED_20261029.md`.
- Chủ task chọn OD-1 theo D-04: fixed aspect, trắng/strokes-only/append-only, width theo chiều rộng, palette năm màu, Pillow PNG RGB và provenance version. Exact aspect/palette/pixel size còn chốt trong T0; không cấp implementation approval.
- Chủ task chọn OD-2 theo D-05: operator tạo server-managed synthetic proof cho local/test pilot, quyết định eligibility có kiểu, profile nullable/CHECK theo origin, legacy bị từ chối và BE2 dùng eligibility_basis version riêng; contract/migration/call sites chốt T0, chưa được phép triển khai.
- Chủ task chọn OD-3 status-read theo D-06: Child đọc request chính mình trong active/paused với device key, admitted grant/membership, đúng Child/canvas và eligibility; finished/revoked/rotated key từ chối, không TTL mới hay auto resubmit. Hiệu lực request đang chạy khi paused còn chốt T0; đề xuất giữ request đang chạy, không cho request mới.
- Chủ task chọn OD-4 theo D-07: Person 2 là integration owner và operator live; Person 2 ký OwnerFenceV1 cùng owner BE1/BE2 có tên ở T0; thiếu đồng ký thì dừng phần phụ thuộc. Phiên AI không là owner; review độc lập tại T0, T7a/b/c và trước T13.
- Chủ task nêu owner BE1 GitHub `CaoDat-2410` và owner BE2 là Person 2, GitHub `AnhKhoaa157` (D-08). Chưa ghi nhận hai owner đồng ký OwnerFenceV1; không suy tên owner thành đồng ký.
- Chủ task chọn khi session `paused` tiếp tục xử lý request AI đang chạy, không nhận request mới (D-09); T0 cần đặc tả/test và giữ eligibility/freshness.

## Chưa làm

- Chưa chốt exact profile OD-1, contract/migration OD-2, đặc tả/test paused OD-3, đồng ký thực tế BE1/BE2 và method UoW/phân công task OD-4, ADR/hợp đồng/version và execution manifests; đã chọn behavior paused và nêu tên owner.
- Chưa có implementation/DB/GPU approval; chưa sửa source hoặc thêm migration.
- Chưa cài package, chạy application test, service, DB, renderer, worker hay provider.
- Chưa merge, commit hoặc push. Không sửa original approvals FEAT-061 hoặc FEAT-063 Rev33.

## Trước triển khai

Review plan, chốt owner scope và ghi approval đúng revision/hash/selected tasks. M0 đóng các điểm chặn; yêu cầu lập plan không cấp quyền implementation.

Bước tiếp theo: hoàn thiện đặc tả paused/profile/eligibility, chuẩn bị hợp đồng để BE1/BE2 đồng ký và phân công/owner/manifests M0; record approval đúng phạm vi trước implementation. Bản chấp nhận rủi ro dư cần được soạn/ghi đúng approval M3 sau này; DB restore có thể làm mất ledger sau khi đã gửi nên absence không tự chứng minh NOT_SENT. Modal giữ ở checkpoint đã dừng.

## GOAL A2 Rev3 — URL guard review 2 fix (2026-11-03)

- Finding P2: query `dbname`/`database` could override a loopback `be1_acceptance` URL path and target another database. Fixed in the existing PostgreSQL test guard by requiring every database override to match the URL path name; matching acceptance URLs remain accepted.
- Verification: focused guard **26 passed, 65 deselected**; Ruff and `git diff --check` passed. No PostgreSQL, Alembic, full offline suite, Modal, or provider run.
- Evidence: `evidence/A2_URL_GUARD_REVIEW2_FIX_REPORT_20261103.md`; plan SHA-256 `C1DD0313D0D5398F836EE4F38AA625F82A394ECC138A894B19AC35DAE0F5A590`.
- State: **FIXED — XONG-CHƯA REVIEW**; A2 is not accepted pending independent rereview. B1/B2 remain unopened.

## GOAL A2 Rev3 — libpq environment routing guard fix (2026-11-03)

- Independent rereview confirmed the `dbname`/`database` override fix and found a new P2: libpq environment variables can change the actual connection target.
- The fixture now fails before engine creation if any target-routing variable is present: `PGHOST`, `PGHOSTADDR`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGSERVICE`, or `PGSERVICEFILE`. It reports names only and does not read or print values.
- Focused URL/environment guard: **35 passed, 65 deselected**; Ruff and `git diff --check` passed. PostgreSQL, full offline GA2, mypy, validators, Modal/provider were not run for this correction.
- Evidence: `evidence/A2_URL_GUARD_REVIEW3_FIX_REPORT_20261103.md`; plan SHA-256 `A147E9199D5391DAD3A86762C1C4B23D8454C80E06A69589546E34FCFF5354F6`.
- State: **FIXED — XONG-CHƯA REVIEW**; wait for independent rereview. B1/B2 remain unopened.

## GOAL A2 Rev3 — independent review closeout (2026-11-03)

- Independent reviewer thread `01a1a16f-ac73-7d32-8964-37f1428787cf` returned **A2 Rev3 overall ACCEPTED / complete** within the approved plans and addenda. The URL target, `dbname`/`database` override, and libpq environment-routing P2 findings were fixed and rereviewed; no blocking finding or missing A2 evidence gate was identified in scope.
- Acceptance is based on source, tests, approvals, reports, snapshots, and saved test outputs. Reviewer did not rerun tests, validators, PostgreSQL, or providers.
- Limits remain disclosed: one strict-mypy protocol error matching baseline; 58 synthetic rows left from the earlier failed teardown and not cleaned; Alembic history was not reconciled with the physical schema; T7b does not guarantee prevention of a phantom insert after `hold()`.
- Historical implementation evidence remains: PostgreSQL module 77 passed, T2C/T7b caller regressions 89 passed, offline GA2 401 passed; final focused URL/environment guard 35 passed / 65 deselected. Full suites were not rerun after the last guard-only change.
- **A2 is complete and independently accepted. B1/B2 are not started and require a separate owner launch.** No source, database, provider, or Git-index operation was performed for this documentation closeout.

## GOAL B1 — implementation checkpoint (2026-11-04)

- State: XONG-CHƯA REVIEW; independent review is pending. B1 implements analysis-only/zero-Sketch plus the default-off in-process T8 pilot under the pinned Rev2 plan.
- Evidence: evidence/B1_IMPLEMENTATION_REPORT_20261104.md; final local snapshot: .claude/handoff/snapshots/GB1_20261104T003700/.
- Focused tests: 3 + 8 + 1 passed. Pinned offline regression: 460 passed. Ruff lint, focused formatting, strict mypy, three repository validators, and git diff --check completed; see the report for exact commands/results and the inherited contract-file format note.
- PostgreSQL/Alembic and Modal/GPU/provider/live calls were not run. B2 remains unopened and requires independent ACCEPTED plus a separate owner launch.

## GOAL B1 — P2 review correction checkpoint (2026-11-04)

- State: **BLOCKED — XONG-CHƯA REVIEW**. The real app composition gate test passes, but the guarded acceptance success path is blocked by a confirmed observation/provider-result insertion-order mismatch between `application/services/vision_analysis.py` and `infrastructure/vision_analysis/repository.py`.
- The mismatch requires source outside the approved B1 P2 allowlist. No service/repository change was made; request a narrow owner-approved scope addendum before proceeding.
- Task-owned database `s2l_b1_review_20261104T050646Z_dbbaefa3` was created under the approved maintenance-connection exception, verified as PostgreSQL 17.11 / user `postgres`, and migrated with `alembic upgrade heads` (exit 0). It is retained. Do not clean historical/synthetic rows without scope.
- Focused results and current Ruff/mypy/validator outcomes are in `evidence/B1_P2_REVIEW_FIX_BLOCKED_REPORT_20261104.md`. Offline regression was NOT RUN after the PostgreSQL acceptance failed. No B2, Modal/provider, stage, commit, push, or merge.

### B1 P2 addendum 2 — ordering correction (2026-11-04)

- Disposition: **BLOCKED — XONG-CHƯA REVIEW**. Service insertion order is corrected and the test-local ordering assertions pass.
- Real PG acceptance still returns `STALE_CONTEXT` after one loopback stub call, with invocation `SUCCEEDED` and analysis head persisted but no accepted job result. Further runtime diagnosis needs a separately approved scope.
- Remaining PG scenarios and pinned offline regression: NOT RUN. See `evidence/B1_P2_ADDENDUM2_ORDERING_FIX_REPORT_20261104.md` and snapshot `.claude/handoff/snapshots/GB1_P2_ORDERING_BLOCKED_20261104T130416/`.

## GOAL B1 P2 — independent review closeout (2026-11-04; cập nhật hồ sơ 2026-11-05)

- Disposition mới nhất: B1 P2 CLOSED — ACCEPTED_WITH_CONDITIONS trong phạm vi local/test synthetic, default-off, loopback stub. Mục BLOCKED trước đó được giữ làm lịch sử; điều kiện stale-owner vẫn phải xử lý trước dữ liệu không synthetic hoặc provider. B2 không được đọc hoặc công bố analysis orphan như kết quả được chấp nhận.

## GOAL B2 — trạng thái sau independent review vòng ba (2026-11-05)

- B2 được launch riêng theo plan đã duyệt sau khi B1 P2 đóng. T12 gồm assertion fix test-only, các bước PostgreSQL owner-run, đối soát chỉ đọc, kiểm tra đồ thị ngoại tuyến và round-trip nhánh pilot trên database mới. Database round-trip chỉ chứng minh nhánh pilot_vision ở trạng thái trung gian với bảng pilot rỗng: 48 → 39 → 48 bảng; không chứng minh round-trip toàn đồ thị hoặc với dữ liệu. Đối soát ngoại tuyến ghi nhận 117 bảng metadata khớp 117 bảng DB và 9 hàng revision khớp 9 head thật. Phần DB của test_migrations.py NOT RUN. Mọi dữ kiện DB là owner-run.
- Lượt rerun bốn suite PostgreSQL trên database giữ lại là owner-run: lần lượt 4, 118, 5 và 1 test passed theo summary pytest chính thức; nguồn: bảng T12 trong evidence/B2_IMPLEMENTATION_REPORT_20261104.md và log .claude/handoff/logs/GB2_T12_RERUN_20261105T013143/.
- Database giữ lại s2l_b2_be1_acceptance_20261104 nguyên vẹn; database mới s2l_b2_be1_roundtrip_20261105 để nguyên sau lần nâng lại cuối với 48 bảng. Giữ hay xóa các database là quyết định riêng của owner và chưa được đưa ra.
- Review độc lập vòng ba khuyến nghị ACCEPTED_WITH_CONDITIONS, không có P1. Đây là khuyến nghị từ tóm tắt owner chuyển lại, không phải quyết định owner. B2 vẫn NEEDS_REVISION cho tới khi owner quyết định riêng.
- Điều kiện còn ghi nhận: đóng OpenAPI P3 trước frontend/client; xử lý orphan stale-owner B1 trước dữ liệu không synthetic/provider; giữ giới hạn T13 là timeout của hàm script-local với stub; ghi T12 đúng phạm vi pilot-only; giữ mypy test_be1_postgres_api.py ở trạng thái NO VERDICT; hoàn thành test PostgreSQL mức route cho POST request/cancel trước D9 hoặc trước frontend.
- N-3: lần rerun PostgreSQL là owner-run bằng runner không có hash pin trong approval. Runner đối soát PowerShell từng được pin không còn trong thư mục script cục bộ khi review; nguyên nhân chưa biết. N-4: chưa có baseline mypy của file test trước B2. OWNER_MODAL_CALL_APPROVED=NO.

## GOAL B2 — owner acceptance with conditions (2026-11-05)

- Owner chấp nhận Goal B2 ở trạng thái ACCEPTED_WITH_CONDITIONS theo chỉ thị "Chấp nhận B2"; review độc lập vòng ba khuyến nghị cùng trạng thái và không có P1. Đây là quyết định của owner, không phải review chấp nhận thay owner.
- Phạm vi gồm T9, T13 và T12 cho pilot local/test synthetic, default-off, loopback stub. T12 đóng có điều kiện: round-trip chỉ nhánh pilot_vision ở trạng thái trung gian với bảng pilot rỗng; không dữ liệu, không story_run_lite, không toàn đồ thị. DB của test_migrations.py NOT RUN; mypy test_be1_postgres_api.py NO VERDICT, chưa có baseline trước B2. Mọi dữ kiện DB là owner-run.
- Điều kiện còn giữ: OpenAPI P3 trước frontend/client; orphan stale-owner B1 trước dữ liệu không synthetic/provider; T13 chỉ chứng minh timeout của hàm script-local với stub; N-1 cần test PostgreSQL mức route child request → job → status trước D9/frontend; N-3 rerun dùng runner không ghim hash và runner đối soát không còn trong thư mục script cục bộ, nguyên nhân chưa biết.
- Chấp nhận B2 không cho phép Modal/GPU/provider/live (`OWNER_MODAL_CALL_APPROVED=NO`), commit/push/merge/stage, xóa/dọn hai DB, gộp nhánh origin/codex/feat063-modal-backend-completion-20261103, bắt đầu goal sau B2, dùng dữ liệu không synthetic/provider thật hoặc tuyên bố production readiness. B1 và B2 vẫn chưa commit.
