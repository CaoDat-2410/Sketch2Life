# C2 task approval

- Status: APPROVED (C2_TYPED_CONTEXT_OFFLINE only)
- Approver: user (Person 2 / BE2 task owner), direct instruction in the Claude session
- Approved scope: FEAT-048 / BE2-02 checkpoint C2_TYPED_CONTEXT_OFFLINE, batches C2.1–C2.5 and
  acceptance C2-A01–C2-A14 of `plan/C2_TYPED_CONTEXT_PLAN.md` revision 2.
- Plan revision: 2
- Approved plan SHA256: `4b339514d3d5bf01b9a8c23f0a15ea5e71b4d2f1389db9e141e31aa322cd57c2` (19655 bytes);
  byte-identical snapshot `plan/C2_TYPED_CONTEXT_PLAN_REV2_APPROVED.md`, saved before any status update.
- Owner choices: Q1–Q5 all selected as recommended in revision 2 (Q1 anonymous per-member age bands,
  exact months internal, `fixture-completed-years-v1` test-only and not pedagogically adopted; Q2 no
  Child text, Teacher topic + trusted request enums only; Q3 Teacher feedback/confirmed meaning/action
  summaries deferred as provider inputs; Q4 new client contract + injected offline transport, no
  server/prompt/endpoint call; Q5 coherent fixture snapshot/revision/digest, real owner adapter handoff).
- Approved at: 2026-10-17, Asia/Saigon; recorded 2026-10-17 11:20 +07:00 (04:20Z) before implementation
- Worktree/branch: `.worktrees/be2-02-vision-correction`, `feature/be2-02-vision-correction`
- Baseline: HEAD `98876fe762a61e64b61980cd0634415e6f5e1dfb`, staged paths 0 at approval time
- Executor: Claude; code/acceptance reviewer: Codex; owner acceptance: user
- Excluded: real provider/network/model calls, weights, dependency installation, services; SQL,
  migrations, Redis/RQ, lifecycle/budget; Lightning server/prompt and production router; BE1/BE2-01/
  BE2-03/FEAT-018 code and other worktrees; stage/commit/push/merge/amend/rebase/deploy; production
  adoption, BE1/P1/P4 sign-off, full-card acceptance and Git publication.
- Unchanged: C1 approval `approvals/TASK_APPROVAL.md` (SHA256 ebe826ce…), approved C1 plan
  `plan/PLAN_REV1_APPROVED.md` (SHA256 f4733c88…) and `approvals/C1_COMPONENT_ACCEPTANCE.md`.
- Stop: C2_CODE_COMPLETE_PENDING_CODEX_REVIEW.

## Approval evidence (verbatim)

```text
Đây là yêu cầu trực tiếp của tôi. Hãy tiếp nhận và triển khai BE2-02 checkpoint C2_TYPED_CONTEXT_OFFLINE theo phạm vi được duyệt dưới đây.

Bạn tự truy cập các file local bằng công cụ của mình. Không cần tôi dán lại lịch sử hay nội dung tài liệu đã có trên máy.

1. WORKSPACE BẮT BUỘC

Worktree:
D:\GitHub\Sketch2Life\.worktrees\be2-02-vision-correction

Branch:
feature/be2-02-vision-correction

Expected HEAD:
98876fe762a61e64b61980cd0634415e6f5e1dfb

Feature:
D:\GitHub\Sketch2Life\.worktrees\be2-02-vision-correction\features\FEAT-048-be2-vision-correction

Nếu phiên mở ở root D:\GitHub\Sketch2Life, hãy tự chuyển working directory của các lệnh sang worktree trên. Không dùng git checkout để đổi nhánh của root.

Trước khi sửa:
- Xác nhận đường dẫn, branch, HEAD, git status và staged paths.
- Staged hiện được kỳ vọng là 0.
- Có sẵn thay đổi tài liệu/planning chưa commit; giữ nguyên chúng.
- Không reset, clean, pull, checkout hoặc cherry-pick để ép workspace khớp.
- Nếu Git báo dubious ownership, có thể dùng safe.directory ở phạm vi từng lệnh cho đúng worktree; không sửa global config.
- Nếu đường dẫn không truy cập được hoặc identity/hash khác, báo rõ khác biệt; không tự clone một bản khác vì các file local chưa được publish đầy đủ.

2. APPROVAL C2

Tôi duyệt BE2-02 checkpoint C2_TYPED_CONTEXT_OFFLINE theo:

D:\GitHub\Sketch2Life\.worktrees\be2-02-vision-correction\features\FEAT-048-be2-vision-correction\plan\C2_TYPED_CONTEXT_PLAN.md

Revision: 2
Phạm vi: C2.1–C2.5
Acceptance: C2-A01–C2-A14

SHA256 plan:
4b339514d3d5bf01b9a8c23f0a15ea5e71b4d2f1389db9e141e31aa322cd57c2

Tôi chọn toàn bộ phương án đề xuất Q1–Q5 trong revision này:

- Q1: provider nhận age-band từng thành viên, không kèm identity; exact completed months giữ nội bộ. Policy fixture-completed-years-v1 chỉ dùng kiểm thử, không phải policy sư phạm đã adopt.
- Q2: không gửi Child intent/explanation/free text; chỉ dùng Teacher topic và request enums được phép từ trusted ports.
- Q3: hoãn Teacher feedback, confirmed meaning và action summaries làm provider input trong C2; giữ nguyên lịch sử correction nội bộ.
- Q4: contract client và injected offline transport mới; chưa sửa server, prompt hay gọi endpoint thật.
- Q5: coherent fixture context snapshot, revision và digest; adapter owner thật tiếp tục là handoff.

Approval này dành cho component candidate offline. Không phải production adoption, sign-off BE1/P1/P4, acceptance toàn card hay quyền Git publication.

Sau khi đối chiếu đúng hash:
- Lưu bản byte-identical của plan đã duyệt trước khi cập nhật trạng thái.
- Ghi nguyên văn tin nhắn thực này vào approvals/C2_TASK_APPROVAL.md trong FEAT-048.
- Liên kết approval C2 từ CONTEXT/status.
- Giữ nguyên approval và approved plan của C1.
- Sau đó triển khai; không hỏi lại approval đã ghi rõ trong tin nhắn này.

3. FILE HƯỚNG DẪN CHÍNH — PHẢI TỰ MỞ ĐỌC

D:\GitHub\Sketch2Life\.worktrees\be2-02-vision-correction\features\FEAT-048-be2-vision-correction\evidence\local\claude\prompts\CLAUDE_C2_IMPLEMENTATION_PROMPT_20261017.md

Đọc đầy đủ file trên và thực hiện cùng với tin nhắn này.

File đó là procedure/template được Codex chuẩn bị, không tự cấp quyền. Approval thực là tin nhắn trực tiếp này. Nếu có xung đột, ưu tiên chỉ thị trực tiếp của tôi và plan có hash đã duyệt; báo rõ xung đột làm thay đổi phạm vi.

Đọc tiếp các nguồn được procedure chỉ định, trước hết:
- AGENTS.md của worktree.
- docs/context/PROJECT_CONTEXT.md.
- docs/context/SOURCE_REGISTER.md.
- FEAT-048 CONTEXT.md, DECISIONS.md, status/STATUS.md.
- Plan C2 revision 2.
- evidence/notes/C2_PLAN_REVIEW_20261017.md.
- evidence/notes/SOURCE_AUDIT.md.
- evidence/notes/H_AI_REVIEW_HANDOFF.md.
- Approval và acceptance C1 để phân biệt phạm vi.

Các đường dẫn tương đối trên đều tính từ worktree hoặc FEAT-048 tương ứng. Tự mở file; không yêu cầu tôi upload lại file local đang đọc được.

4. NGỮ CẢNH CẦN GIỮ

- BE2-02 là FEAT-048, không phải FEAT-002.
- C1_COMPONENT_OFFLINE đã được owner nghiệm thu, các finding C1 đã đóng trong component scope.
- 8 commit C1 đã push, checkpoint là HEAD 98876fe.
- Toàn card BE2-02 vẫn IN_PROGRESS / NOT_DONE.
- Các kết quả test C1 ghi trong evidence là lịch sử, không được dùng làm kết quả test C2 mới.
- BE2-01 nằm trong worktree khác, vẫn WAITING_STUDIO; CR01 còn mở, B-12 HANDOFF và OwnerFence ASSUMED_CONTRACT.
- Lightning đang không dùng được theo checkpoint hiện tại; không tự xác nhận đã khôi phục.
- Lượt này làm C2 offline, không dựng môi trường thay thế hay chạy thêm cloud probe.
- Nếu tôi yêu cầu chuyển sang Studio sau khi khôi phục, checkpoint C2 rồi chuyển theo chỉ thị. Không tự chạy song song hai task.
- FR022 còn yêu cầu feedback/actions và các đầu vào được hoãn. C2 không hoàn tất toàn FR022 hay chứng minh model thật hiểu context.

5. GOAL VÀ CÁC PHẦN TRIỂN KHAI

Hoàn thành:
trusted source/request/context
→ context có kiểu và kiểm quyền từng member/field
→ provider payload tối thiểu
→ adapter injected offline
→ original result có binding/digest/provenance
→ context đổi hoặc quyền bị revoke không tạo authority sai.

Triển khai C2.1–C2.5:
1. Pure domain context snapshot/projection/binding và canonical digest.
2. Strict versioned contracts cho typed context/result.
3. Nối application service, fake UoW/repository/harness và current checks.
4. Adapter context dùng injected offline transport.
5. Tests, evidence, acceptance mapping và consumer handoff.

Đọc code hiện có theo từng lớp trước khi sửa. Tự giải quyết chi tiết kỹ thuật thông thường trong phạm vi plan và ghi DECISIONS; chỉ hỏi khi thiếu dữ kiện thực sự làm thay đổi scope hoặc authority.

6. GUARANTEE QUAN TRỌNG

- Domain/application không phụ thuộc Pydantic, HTTP, DB hoặc provider implementation.
- Trusted snapshot phải bind đúng request/source/scope/audience/purpose và thống nhất với context port hiện có.
- Reject audience thiếu/thừa/trùng trước khi chuyển sang dict/set.
- Kiểm từng thành viên; không suy tuổi từ tranh, không lấy tuổi trung bình.
- Tách internal snapshot khỏi provider projection. Không dump internal object ra payload.
- Exact months, identity, consent evidence và internal authority records không được gửi làm context provider.
- payload_digest và context_digest có tập dữ liệu hash khác nhau, canonical rõ ràng; không tự hash chính mình hay transient execution time.
- Tuổi đổi trong cùng age-band vẫn phải làm đổi internal digest.
- Không thêm digest hay sửa lifecycle của BE2-01.
- Lightning V2 forbid extras: không nhét context vào /v2/vision hoặc narration_context.
- Capability không hỗ trợ phải refuse trước image load/call; không fallback image_only.
- New wrapper phải kiểm echo lẫn nested V2 result và retain/hash toàn bộ response.
- Typed output dùng provenance truthful offline_context_adapter; không giả là legacy image_only hay inference thật.
- Giữ image_only 0.1 contracts/golden bytes; typed records dùng sibling 0.2 candidate theo plan.
- Recheck current consent/purpose/transfer permission/eligibility sau provider.
- Revocation/ineligibility: reject, không lưu output dở.
- Context revision hoặc digest đổi: stale/non-authoritative theo plan, không rebind.
- Kiểm cả observation replay, current reads, downstream applicability và correction mới.
- Receipt correction đã accepted vẫn replay như lịch sử sau current disclosure checks; replay không làm meaning cũ có hiệu lực trở lại.
- Sequential replay không gọi provider mới. Concurrent first submissions có thể mỗi bên gọi một lần trước khi một atomic winner thắng; không claim exactly-once.
- Giữ C1 privacy/bounds/rollback/idempotency/CAS guarantees; không bỏ assertion chỉ để test xanh.

7. KIỂM THỬ VÀ HỒ SƠ

Python venv hiện có:
D:\GitHub\Sketch2Life\backend\.venv\Scripts\python.exe

Pin PYTHONPATH/MYPYPATH tới:
D:\GitHub\Sketch2Life\.worktrees\be2-02-vision-correction\backend\src

Xác minh sketch2life.__file__ trỏ đúng worktree trước khi test. Editable install mặc định có thể trỏ root checkout khác.

Không cài dependency hoặc sửa shared venv. Có thể dùng dependency đã tồn tại theo cách process-local trong procedure. Thiếu check/dependency thì ghi NOT_RUN và lý do, không báo PASS.

Chạy:
- Focused C2 và toàn focused C1.
- Relevant legacy Vision/V2/Qwen regressions.
- Relevant BE2-01 non-service regressions.
- Focused ruff và strict mypy.
- Harness, repository security, architecture, skeleton và git diff --check.

Không chạy PostgreSQL/Redis/Studio/model thật.

Old local C1 wrapper có pin HEAD/source cũ: không chạy lại nguyên xi sau khi đổi code hoặc overwrite receipt lịch sử. Tạo run directory/wrapper C2 riêng trong ignored evidence/local/.

Map đủ C2-A01–A14 tới test IDs và kết quả thực. Báo riêng collected/pass/fail/error/skip.

Giữ evidence gọn: một implementation note và một metrics JSON, cập nhật current CONTEXT/DECISIONS/STATUS, evidence index, handoff và tracker. Raw logs/JUnit/prompts/scratch ở evidence/local/ bị ignore. Không ghi secret, real child data hoặc absolute machine paths vào tài liệu publish.

8. GIỚI HẠN VÀ ĐIỂM DỪNG

Không:
- Stage, commit, push, merge, amend, rebase hoặc deploy.
- Gọi provider/network/model thật, tải weights, cài dependency hoặc dựng service.
- Sửa BE1/BE2-01/BE2-03/FEAT-018 code hay worktree khác.
- Thêm SQL/migration/Redis/RQ/lifecycle/budget.
- Sửa Lightning server/prompt hoặc mount production router.
- Sửa harness/SRS để làm validator pass.
- Tự nghiệm thu C2, đóng toàn card hoặc mở chặng tiếp.

Hoàn thành đến C2_CODE_COMPLETE_PENDING_CODEX_REVIEW rồi DỪNG.

Báo bằng tiếng Việt:
- Đã thay đổi gì và vì sao.
- File chính.
- Test/check thực và acceptance mapping.
- Hash approval/approved plan.
- Remaining gates.
- Link evidence và các điểm Codex cần review.

Không dump toàn bộ lịch sử/log vào chat; giữ đủ thông tin để kiểm chứng.
```
