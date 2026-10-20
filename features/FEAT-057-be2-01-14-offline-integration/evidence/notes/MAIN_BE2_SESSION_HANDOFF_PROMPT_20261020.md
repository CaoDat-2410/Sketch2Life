# Prompt to update the primary BE2 session handoff

Copy the text between PROMPT START and PROMPT END into the primary BE2
integration session.

--- PROMPT START ---

Bạn đang tiếp tục phiên chính BE2-01–14 trên nhánh integration. Hãy cập nhật
bàn giao từ evidence mới nhất và tiếp tục phần offline còn được phê duyệt. Đây
là tiếp tục phạm vi FEAT-057 đã duyệt, không phải phê duyệt mới cho runtime,
provider, database, cài package, hay nghiệm thu.

## Mục tiêu

Đưa trạng thái BE2-01–14 trong handoff chính về đúng evidence hiện tại; xác định
việc offline nào còn làm được trong môi trường này; chuẩn bị chính xác các bước
còn lại khi dependency hoặc Lightning sẵn sàng.

## Nguồn cần đọc

Đọc AGENTS.md, docs/context/SOURCE_REGISTER.md, và các hồ sơ hiện hành:

- features/FEAT-057-be2-01-14-offline-integration/CONTEXT.md
- features/FEAT-057-be2-01-14-offline-integration/plan/PLAN.md
- features/FEAT-057-be2-01-14-offline-integration/plan/BE2_01_14_RUNTIME_READINESS_PLAN.md
- features/FEAT-057-be2-01-14-offline-integration/approvals/TASK_APPROVAL.md
- features/FEAT-057-be2-01-14-offline-integration/status/STATUS.md
- features/FEAT-057-be2-01-14-offline-integration/evidence/notes/BE2_01_14_RUNTIME_READINESS_20261020.md
- features/FEAT-057-be2-01-14-offline-integration/evidence/metrics/BE2_01_14_RUNTIME_READINESS_20261020.json
- features/FEAT-057-be2-01-14-offline-integration/evidence/notes/LOCAL_OFFLINE_RECHECK_20261020.md
- features/FEAT-057-be2-01-14-offline-integration/evidence/metrics/LOCAL_OFFLINE_RECHECK_20261020.json
- features/FEAT-057-be2-01-14-offline-integration/evidence/notes/OFFLINE_INTEGRATION_RESULTS_20261020.md
- Mỗi task 08–14: đọc note LOCAL_OFFLINE_RECHECK_20261020.md, evidence/raw/LOCAL_OFFLINE_RECHECK_20261020.summary.json, approval, status và handoff riêng của card đó.

Xác minh lại worktree, branch, HEAD, index và diff trước khi sửa. Snapshot ghi
nhận gần nhất là worktree be2-01-14-integration-linked, branch
feature/be2-backend-ai-integration, HEAD
d35f035f87fddfc87b0d72d8929f5b1b843fce0e. Worktree đã có thay đổi docs/evidence
chưa commit; giữ nguyên các thay đổi này, không reset, checkout đè, clean hoặc
ghi lại evidence cũ.

## Trạng thái mới nhất cần giữ đúng

Lượt offline recheck ngày 2026-10-20 chạy trên integration candidate, dùng
Python environment có sẵn. Môi trường thiếu Pillow (PIL) và module multipart;
skip quan sát được ở task 12 là do thiếu Pillow. Không cài package.

| Task | Kết quả recheck mới nhất |
|---|---|
| 08 | Runner FAIL do owned suite lỗi import PIL khi collection; inventory 446 case, không có pass count owned. Regression 1.435 PASS. SQL 11 case chỉ collection, không execute. |
| 09 | Owned 458 PASS. Regression collection bị chặn bởi PIL, inventory 1.881 case. SQL 21 case chỉ collection. |
| 10 | Owned 253 PASS. Regression collection bị chặn bởi PIL, inventory 2.339 case. SQL 14 case chỉ collection. |
| 11 | Owned 219 và legacy 25 PASS. Regression collection bị chặn bởi PIL, inventory 2.592 case. SQL 17 case chỉ collection. |
| 12 | Runner NOT_RUN: 476 PASS, 1 trong 477 test skip vì route test cần Pillow. Không tính là PASS trọn bộ. |
| 13 | Owned 194 PASS. Regression collection bị chặn bởi PIL, inventory 2.836 case. SQL 11 case chỉ collection. |
| 14 | Owned 1.061 và foundation 114 PASS. Regression phụ thuộc task 12 nên NOT_RUN. |

Runner 08/09/10/11/13/14 báo các kiểm tra Ruff, mypy, architecture, harness,
repository security và whitespace đạt; tất cả summary ghi source_unchanged=true.
Không có product source/test nào được sửa trong lượt chạy này. Đây là lỗi môi
trường/collection, không được kết luận là lỗi sản phẩm. Các actual PostgreSQL
receipts riêng trước đó vẫn là evidence riêng; lượt này không chạy SQL, không
được thay thế hoặc gộp nhầm với chúng. Repository validators hiện đạt:
validate_harness, validate_repository_security, validate_architecture,
validate_skeleton và git diff --check.

Lightning chưa truy cập được trong phiên; không có Lightning CLI/connector, các
Studio tool hiện ra là Roblox Studio. Hash ZIP và runner A17 của task 01 đã
khớp README, nhưng named-Studio inventory và A17 runtime vẫn NOT_RUN. Task 01
A17 là checkpoint Lightning/Studio duy nhất được duyệt; task 02–14 hiện không
có Lightning entrypoint được duyệt. Không tồn tại lệnh one-shot an toàn cho
toàn BE2-01–14. Task 07 chỉ được chấp nhận ở phạm vi
KNOWLEDGE_SCRIPT_COMPONENT_OFFLINE; không suy rộng thành runtime hoặc full-card
acceptance.

## Cập nhật sau khi soạn handoff — 2026-10-20

BE2-07 cleanup hiện đã được đẩy lên cả ba remote branch refs:

- `feature/be2-07-knowledge-script` và nhánh gộp task 01–07
  `feature/be2-01-07` cùng ở `a3c5b1c078a0772873f23468b3b064c8014532ae`.
- Nhánh gộp BE2-01–14 `feature/be2-backend-ai-integration` ở
  `38b7b4f1593a209c8302c5baf5a30c5198ece757`, cleanup-only cherry-pick trên
  `d35f035f87fddfc87b0d72d8929f5b1b843fce0e`.

Cả ba remote snapshot đều không còn `features/FEAT-056-be2-knowledge-script/evidence/cloud-review/`.
Archive đã kiểm lại (83/83 và 78/78 output khớp SHA256); report PASS còn trong Git history tại
`0d07386eb7b6a17755eaa5ed03a127466194debf`.

Worktree tích hợp hiện có trong phiên này vẫn ở local HEAD `d35f035f87fddfc87b0d72d8929f5b1b843fce0e`,
đang behind remote cleanup commit và giữ nguyên 41 thay đổi local chưa commit (index rỗng).
Không reset, clean, checkout đè hoặc đồng bộ remote vào worktree này khi chưa bảo toàn các thay đổi.

## Việc cần làm

1. Đối chiếu trạng thái cũ trong OFFLINE_INTEGRATION_RESULTS_20261020.md và
   offline-test-matrix.json với recheck mới. Giữ receipts cũ dưới nhãn lịch sử;
   cập nhật handoff chính để người đọc thấy kết quả mới nhất và nguyên nhân
   môi trường, không xóa hoặc viết lại lịch sử.
2. Chỉ chạy các offline checks còn được approval cho phép, chưa có evidence
   tương đương, và có đủ dependency. Trước hết kiểm tra có sẵn environment phù
   hợp hay không. Nếu không có, ghi NOT_RUN/blocked và tiếp tục các việc đọc
   source, contract, dependency order, migration graph hoặc chuẩn bị lệnh không
   cần dependency đó. Không cài package nếu chưa có approval riêng.
3. Nếu một test chỉ lỗi vì dependency, không sửa product code, không bỏ test,
   không đổi expected case count và không báo PASS. Chỉ sửa source nếu phát
   hiện được lỗi offline có thể tái hiện, nằm trong phạm vi đã duyệt; khi đó
   ghi rõ test thất bại trước sửa và rerun đúng suite bị ảnh hưởng.
4. Cập nhật feature-local handoff/context/status khi cần, giữ nguyên trạng thái
   IN_PROGRESS/IN_PROGRESS_PENDING_EXTERNAL và mọi acceptance decision của
   từng card. Lưu evidence trong evidence/ của đúng feature, không ghi absolute
   machine path, secret, credential hoặc dữ liệu trẻ em.
5. Chạy lại các validator phù hợp, kiểm git diff --check và xác nhận diff chỉ
   gồm nội dung đã được duyệt. Báo rõ phần nào PASS, FAIL, NOT_RUN,
   NOT_IMPLEMENTED hoặc bị chặn bởi môi trường.

## Ranh giới

Không gọi Lightning, Studio, model/provider, service, HTTP endpoint, PostgreSQL
hoặc Redis trong phiên hiện tại. Không cài package, provision/migrate DB, tạo
credential, tự nghiệm thu card, đổi approval, commit, push, tạo PR hoặc merge
dev/main. Khi Lightning hoạt động lại, vẫn phải xác minh đúng named Studio,
source pin, package hash, environment và approval trước checkpoint A17; không
tự suy ra task 02–14 được phép chạy live.

## Kết quả bàn giao

Trả lời bằng tiếng Việt, nêu branch/HEAD đã xác minh, file handoff/evidence đã
cập nhật, kết quả mới nhất theo task, validator đã chạy, blocker còn lại và
lệnh offline tiếp theo có thể chạy an toàn. Không gọi integration candidate
hay bất kỳ card nào là accepted/DONE nếu hồ sơ owner chưa ghi rõ.

--- PROMPT END ---
