# Task approval

- Status: APPROVED
- Approver: user (Person 2 / BE2 task owner), direct instruction in the Claude session
- Approved scope: FEAT-048 / BE2-02 checkpoint C1_COMPONENT_OFFLINE only, per `plan/PLAN.md` revision 1, decisions D01–D11 and acceptance V01–V17; batches C1.1–C1.5 (strict DATA-22/CMD-34 candidate contracts; pure domain/application; source/authority/admission/lineage/repository ports with fake transaction/CAS; offline bridge reusing Vision V2 via injected transport; isolated CMD-34 fixture handler; tests, evidence and consumer handoff).
- Plan revision: 1
- Approved plan SHA256: `f4733c88797edbcce225ecd63700634f929ca75789362c7f3a58a2b57f19df30` (14657 bytes); byte-identical snapshot `plan/PLAN_REV1_APPROVED.md`, saved before the status update of `plan/PLAN.md`.
- Approved at: 2026-10-16, Asia/Saigon; recorded 2026-10-16 19:18 +07:00 (12:18Z) before implementation
- Worktree/branch: `.worktrees/be2-02-vision-correction`, `feature/be2-02-vision-correction`
- Baseline: `6dcc57ee0b3d053f071c8c92e72aaaee2e98d899` (HEAD equals base at approval time)
- Executor: Claude; reviewer: Codex
- Excluded: real provider/network/model calls, weights, dependency installation, services; SQL migrations, Redis/RQ, production router mount; BE2-01 and FEAT-018 worktrees, other cards; commit/push/merge/deploy; production adoption and BE1/P1/P4 sign-off.
- Missing-dependency rule: a missing dependency or skipped check is `NOT_RUN` with the exact reason, never PASS.
- Notes: component-candidate approval only. Routine choices inside D01–D11 proceed without re-confirmation; scope/authority changes or genuinely missing facts require a question. C1 PASS does not mean BE2-02 DONE; BE2-01 remains WAITING_STUDIO. Pre-existing uncommitted planning files in the worktree are preserved as valid preparation.

## Approval evidence (verbatim)

```text
Đây là yêu cầu trực tiếp của tôi. Tiếp nhận và triển khai BE2-02 — Vision và correction có provenance.

GOAL
Hoàn thành checkpoint C1_COMPONENT_OFFLINE của BE2-02:
snapshot/context hợp lệ → Vision observation có provenance → Child ghi ý định/correction → Teacher xác nhận meaning, đồng thời giữ nguyên inference gốc và toàn bộ lịch sử.

WORKSPACE
- Worktree: D:\GitHub\Sketch2Life\.worktrees\be2-02-vision-correction
- Branch: feature/be2-02-vision-correction
- Base: 6dcc57ee0b3d053f071c8c92e72aaaee2e98d899
- Feature: features/FEAT-048-be2-vision-correction

Xác nhận workspace trước khi sửa. Các file planning chưa commit trong worktree là phần chuẩn bị hợp lệ; giữ nguyên thay đổi ngoài phạm vi.

APPROVAL
Tôi duyệt FEAT-048 / BE2-02 theo plan/PLAN.md revision 1,
phạm vi C1_COMPONENT_OFFLINE, các quyết định D01–D11 và acceptance V01–V17.

SHA256 plan:
f4733c88797edbcce225ecd63700634f929ca75789362c7f3a58a2b57f19df30

Ghi nguyên văn yêu cầu này vào approvals/TASK_APPROVAL.md trước khi code.
Lưu bản plan đã duyệt cùng hash trước khi cập nhật trạng thái triển khai.
Approval này áp dụng cho component candidate, không phải production adoption hoặc sign-off BE1/P1/P4.

NGUỒN CẦN ĐỌC
Đọc AGENTS.md, sau đó trong FEAT-048:
- CONTEXT.md
- plan/PLAN.md
- DECISIONS.md
- evidence/notes/SOURCE_AUDIT.md
- evidence/notes/PLAN_REVIEW.md

Nguồn đã được audit. Đối chiếu các đoạn SRS/card được chỉ rõ khi cần, rồi triển khai theo plan; tập trung vào code và bằng chứng.

KẾT QUẢ PHẢI CÓ
1. DATA-22 contracts chặt chẽ; observation gốc và correction tách riêng, có ref/version/author/context.
2. Domain/application và các port source, authority, admission, lineage, repository; fake transaction/CAS cho component.
3. Bridge tái sử dụng Vision V2 hiện có bằng injected transport, chạy offline.
4. CMD-34 correction handler trong fixture app riêng.
5. Tests và evidence ánh xạ đủ V01–V17, consumer handoff và danh sách runtime/adoption còn thiếu.

CÁC GUARANTEE CẦN GIỮ
- Child chỉ ghi proposal/ý định trong scope và current turn; Teacher đúng quyền mới xác nhận authoritative meaning.
- Correction không overwrite inference gốc hoặc tự tạo Teacher review.
- Snapshot/context đổi, consent/grant bị revoke hoặc job/attempt sai thì result không được authoritative.
- Checkpoint JSON checksum, rendered-image hash và admission receipt phải được phân biệt và kiểm tra.
- Confidence nullable; không bịa score, tuổi, tâm lý hoặc ý định.
- Idempotency, If-Match, CAS và rollback đúng plan; replay không làm lộ dữ liệu sau revoke.
- Legacy bridge ghi rõ image_only; không nhét Child intent vào adult narration_context rồi tuyên bố đã hỗ trợ typed context.
- Unsafe/pending/raw model content không được lộ cho Child.

CÁCH THỰC HIỆN
Tự tổ chức và hoàn thành C1.1–C1.5 trong plan.
Các lựa chọn chi tiết trong D01–D11 được ghi rõ trước khi code, không cần hỏi lại cho từng lựa chọn thông thường.
Chỉ hỏi khi gặp quyết định làm đổi scope/authority hoặc thực sự thiếu dữ kiện; tiếp tục phần độc lập có thể làm.

Sử dụng Python venv hiện có, xác minh import trỏ đúng worktree BE2-02.
Chạy test phù hợp, legacy regression liên quan, focused ruff/mypy và validator.
Ghi kết quả thật; missing dependency/skip là NOT_RUN.

GIỚI HẠN
- Không gọi provider/network/model thật, tải weights, cài dependency hoặc dựng service.
- Không thêm SQL migration/Redis/RQ hoặc mount router vào production app.
- Không sửa worktree BE2-01, FEAT-018 hay implement card khác.
- Không commit, push, merge hoặc deploy.
- BE2-01 vẫn chờ Studio; C1 PASS không đồng nghĩa toàn BE2-02 DONE.

ĐIỂM DỪNG
Dừng khi C1 review-ready để Codex review.
Báo bằng tiếng Việt: đã làm gì, file thay đổi, kết quả test/check,
mapping V01–V17, giới hạn còn lại và bước tiếp theo.
```
