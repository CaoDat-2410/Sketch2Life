# Claude — hoàn tất gate bàn giao/kiểm tra Q00 Phase A

Lượt này chỉ chuẩn bị và xử lý các gate nghiệm thu BE2-01 Phase A, không sửa backend. Code review cuối PASS; R01–R11 và R03a/R04a/A18a đã đóng. Claude tiếp tục là executor; không mở thêm card.

## Nguồn và phạm vi

Làm trong worktree `.worktrees/be2-01-ai-job-foundation`. Kiểm tra branch thực tế là `feature/be2-01-ai-job-foundation`, đọc git status và giữ thay đổi ngoài task.

Đọc AGENTS.md, docs/context/PROJECT_CONTEXT.md, SOURCE_REGISTER.md, rồi các file trong `features/FEAT-044-be2-ai-job-foundation/`:
- CONTEXT.md, DECISIONS.md, approvals/TASK_APPROVAL.md.
- plan/PLAN.md revision1 (acceptance ở mục5), BE2_ROADMAP.md revision2, BE2_EXECUTION_TRACKER.md.
- plan/PHASE_A_CANDIDATE_SPEC.md.
- evidence/notes/PHASE_A_HANDOFF.md và PHASE_A_Q00_FINAL_CODE_REVIEW_20261014.md.
- metrics/code/test receipts được final review dẫn chiếu.

Approval hiện có chỉ Phase A A1–A9. Prompt này không duyệt Phase B, cài dependency, stack/policy/schema production hoặc thay approved plan/approval.

## Bước 1 — gói cross-review nhỏ, dùng lại evidence

Đồng bộ PHASE_A_HANDOFF.md với final review và source hiện tại: review corrections đã đóng; code provider là string không nhận diện → PROVIDER_ERROR, nonstring → non-authoritative MALFORMED_CLAIM; artifact foreign/unowned không bị mutate; temporary guard không quarantine; cancel/register/purge cùng scope lock. Chỉ chỉnh mô tả bàn giao có liên quan.

Tạo `evidence/notes/PHASE_A_ACCEPTANCE_GATE_RECORD.md`, một bảng:
`consumer | contract/port + candidate/version | điểm cần review | compatibility delta | evidence path/hash | quyết định + nguồn/ngày | trạng thái`.

- P1: DATA-25/full/Child projection, progress, refs, error, poll hint, ETag/304; succeeded không tự là Teacher approval.
- P2: auth/eligibility/notice, artifact organization/producer lineage/quarantine_reason, immutable receipts và copy scope-lock. Persistence chỉ xác nhận boundary/requirements, không triển khai adapter.
- P4: contract name/version/namespace compatibility, dependency/composition pack, fixture tách live app. Không mount router hoặc ghi adoption vào registry khi chưa có quyết định.

Dẫn schema/fixture/error/example/runner receipts đã có để đáp ứng A9/A-20. Giữ DATA-24 owner BE2-05 và ProviderCopyLifecycle owner BE2-14; không triển khai hai card này.

Tìm và dùng quyết định đã có trước. Thiếu thì ghi PENDING_OWNER_DECISION, đúng owner và câu hỏi cần trả lời. Chuẩn bị nội dung để owner review; không tự gửi tin, giả chữ ký hoặc coi reviewer agent là owner có quyền adopt.

A9/A-20 yêu cầu cross-review/handoff candidate/fixture. Owner có thể chấp nhận checkpoint candidate và giữ production adoption DEFERRED. Không đòi implement FE/BE1/P4, live registry hoặc chốt các số retry/poll production để giao gói này. Phân biệt quyết định chấp nhận Phase A với adoption cần cho Phase B/runtime.

## Bước 2 — đúng một test còn thiếu

Kiểm tra môi trường hiện hữu được phép truy cập, có dependency sẵn; không cài package hoặc chạy setup. Nếu dùng LightningAI, dùng môi trường Sketch2Life riêng theo policy; giữ Wan2.2 environment.

Chạy từ đúng checkout chứa reviewed source, pin PYTHONPATH vào `backend/src`, xác nhận module origin/interpreter và hash của test/app source. Bật PYTHONDONTWRITEBYTECODE=1, tắt pytest cache.

```text
python -B -m pytest backend/tests/contract/test_ai_job_polling.py::test_live_app_routes_have_no_candidate_job_route -p no:cacheprovider -rs
```

PASS chỉ khi test thực thi với **1 passed, 0 skipped**, exit0. Test dùng importorskip("PIL"): exit0 kèm 1 skipped vẫn chưa đóng gate. Không dùng runner HTTP hoặc AST check để thay test này.

Lưu command, environment/interpreter/module origin, thời gian, source hashes và output đã loại đường dẫn máy/secret vào feature evidence/raw + metrics. Không chạy lại toàn suite khi chỉ sửa docs và không có concern mới.

Thiếu môi trường/dependency: giữ REQUIRES_LIGHTNINGAI_TEST và ghi lệnh chưa chạy. Chỉ ghi checkpoint deviation nếu có quyết định owner thật, nêu phạm vi/rủi ro/owner và điều kiện chạy lại. Test vẫn NOT_RUN, không đổi thành PASS.

## Bước 3 — chốt trạng thái theo evidence

Cập nhật gate record, handoff, CONTEXT/DECISIONS/status/STATUS.md, tracker và evidence index theo kết quả thực tế. Không sửa approved PLAN.md hoặc TASK_APPROVAL.md.

Nếu thiếu owner review/disposition hoặc test evidence: ACTIVE Q00, acceptance PENDING; báo chính xác người/quyết định/môi trường còn thiếu. Nếu đủ và có quyết định nghiệm thu đúng scope, ghi Phase A accepted ở candidate/fixture checkpoint. Whole BE2-01 vẫn IN_PROGRESS vì Phase B durable còn lại.

Chạy harness --feature, repository security và git diff --check cho thay đổi docs. Giữ review gốc và receipts cũ.

## Đầu ra và điểm dừng

Báo cáo tiếng Việt: gate nào đã đóng, link record/receipts, kết quả test thực tế hoặc NOT_RUN, quyết định còn thiếu và trạng thái Q00. Việc độc lập đã làm xong thì giao cụ thể để owner review.

Đề xuất lượt sau là plan Phase B Q01 với durable repository/migrations/CAS/receipts/outbox/queue và acceptance restart/concurrency/fault recovery. Lượt này không viết plan/code Phase B, không chuyển ACTIVE sang Q01 hoặc đánh dấu full BE2-01 DONE. Implementation Phase B cần plan/approval riêng, ADR và BE1 port adoption.
