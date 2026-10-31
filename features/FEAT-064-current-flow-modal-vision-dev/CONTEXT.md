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
