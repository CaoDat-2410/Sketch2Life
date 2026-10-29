# Plan review và static checks — 2026-10-29

## Trạng thái

Đây là record review/checks của **rev1 tại thời điểm viết**, được giữ làm lịch sử. Rev1 đã được thay bằng rev2 sau Claude NEEDS_REVISION; xem `CLAUDE_PLAN_REVIEW_REV2_20261029.md` và `../../status/STATUS.md` cho trạng thái hiện tại. Không dùng hash rev1 dưới đây để duyệt rev2.

Tại checkpoint này plan revision 1 vẫn DRAFT, implementation NOT_STARTED. Approval template vẫn AWAITING_APPROVAL, không có approver/scope. Đây không phải owner approval hoặc runtime acceptance.

Plan SHA-256 sau các sửa draft:

`B563BEB6552AADB4B2658BE8DE3806CE1DF401DAF5BF96D38D413DF56246155A`

## Review độc lập

Hai reviewer đọc source và draft, không sửa file hoặc chạy test/dịch vụ/provider. Các điểm material đã được giải quyết ở mức kế hoạch:

1. Canvas đang thấy phải cùng white/strokes-only profile với nguồn export/preview; không âm thầm bỏ gallery hoặc suggestion layer.
2. Success của BE2-03 vốn tạo SketchIntent/call. Đã yêu cầu explicit analysis-only continuation và zero Sketch intent/event/outbox/call, kể cả replay/restart; không dùng no-op fake.
3. Synthetic eligibility phải có evidence riêng xuyên BE1/BE2; không forge legal consent hoặc consent_effective booleans. Sửa riêng device guard không đủ.
4. Giới hạn một call phải ở durable backend run ledger, commit trước send và áp dụng mọi ID/worker/restart; helper marker không đủ. FEAT-061 allowance đã dùng.
5. Quyền AI riêng, source freshness/revision thay đổi và accepted/worker/poll vì Child API timeout 12 giây được ghi rõ.

Sau follow-up, cả hai reviewer không còn material finding từ phạm vi đã review. Các exact contracts, ADR, owner decisions/manifests và implementation vẫn chưa hoàn tất. Không diễn giải review kỹ thuật này thành task approval.

Sau review còn làm rõ lifecycle join/admit trước Start, runtime đích classroom và việc client mock preparation không thay dependency integration. Không mở thêm scope hoặc sửa source.

## Kết quả command thực sự đã chạy

Các command chạy từ dev-based worktree bằng venv Python đã có; không cài thêm dependency, import backend app hoặc truy cập DB/provider.

| Command | Kết quả |
| --- | --- |
| `python tools/validate_harness.py --feature features/FEAT-064-current-flow-modal-vision-dev` | Exit 1, HARNESS_INVALID do paths của feature khác bên dưới; không báo lỗi FEAT-064 |
| `python tools/validate_skeleton.py` | Exit 0, SKELETON_VALID |
| `python tools/validate_repository_security.py` | Exit 0, REPOSITORY_SECURITY_VALID, 5699 publishable files ở snapshot kiểm tra |
| `git diff --check` | Không báo lỗi |

`--feature` không cô lập vòng quét chung của validator hiện tại. Lỗi thực tế:

- FEAT-043-srs-ui-screen-set thiếu `evidence/screenshots`.
- FEAT-063-system-architecture-rearchitecture thiếu `evidence/raw`, `evidence/screenshots`, `evidence/metrics`, `evidence/notes`.

Không sửa các feature đó hoặc harness để làm xanh. Không ghi HARNESS_VALID cho toàn repo. Source/runtime chưa đổi; không chạy application/DB/UI/model test và không dùng kết quả static thay runtime evidence.

Ghi chú kết quả này được viết sau command; số file scan là số ở lần chạy được ghi nhận, không phải live count sau mọi cập nhật tài liệu tiếp theo. Không commit/push trong nhiệm vụ planning.

Sau khi thêm record review và làm rõ draft, security validator được chạy lại và vẫn `REPOSITORY_SECURITY_VALID`, 5700 publishable files. Final plan hash khớp status; approval file vẫn giống template AWAITING_APPROVAL. Git diff dưới `backend/src` và `apps` không có thay đổi. Các draft/CONTEXT FEAT-063 ngoài nhiệm vụ được giữ nguyên, không được xem là thay đổi của FEAT-064.
