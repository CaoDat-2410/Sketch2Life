# FEAT-064 status

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
