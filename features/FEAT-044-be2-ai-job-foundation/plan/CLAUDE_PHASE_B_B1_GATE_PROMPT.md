# Claude — chuẩn bị/chốt hồ sơ B1 sau plan review PASS, chưa code

Mục tiêu: gom các quyết định còn thiếu vào **một** record reviewable để owner chốt. Phase B plan rev3 review PASS; PB-R01–R06/PB-C01/C02 closed ở mức thiết kế. Không sửa lại plan hoặc mở thêm card nếu scope/decisions không thay đổi.

Trong worktree `.worktrees/be2-01-ai-job-foundation`, branch `feature/be2-01-ai-job-foundation`: kiểm tra status và đọc AGENTS.md, project context/source register, FEAT-044 context/decisions/status/approval/tracker. Đọc plan/PHASE_B_PLAN.md rev3, PHASE_B_ADR_PROPOSAL.md rev3, PHASE_B_PORT_REVIEW.md rev3, evidence/notes/PHASE_B_PLAN_FINAL_REVIEW_20261015.md, PHASE_A_ACCEPTANCE_GATE_RECORD.md.

## Đầu ra duy nhất cần chuẩn bị

Tạo `plan/PHASE_B_DECISION_RECORD.md` với status PENDING_OWNER_DECISION nếu chưa có actual inputs. Mỗi hàng có: nhóm gate, đề xuất hiện có/source, exact câu owner cần chốt, owner, quyết định thực tế + nguồn/ngày hoặc PENDING, ảnh hưởng/điều kiện code.

Gom thành các nhóm:
1. **G1 Phase A:** tìm genuine P1/P2/P4/task-owner decisions và test/disposition đã có; dùng lại, không hỏi lại. Thiếu thì dẫn gate record hiện tại, không tự ký hay ghi deviation. Candidate acceptance/production adoption deferred phải đúng phạm vi; live test skip vẫn NOT_RUN.
2. **G3 ADR D1–D7:** đề xuất ưu tiên từ companion ADR. Owner chốt protocol/store/queue/migration/identity và vị trí ADR. Nếu chọn D3/D7 fallback, nêu exact scope/acceptance delta để amendment/review; không quietly adopt alternate.
3. **G4 P2/P4 Q1–Q8:** ghi đúng tám câu hỏi hiện có, loại trùng; đặc biệt Q8 owner-fence scope/epoch/connection ownership, Q4 QuarantineIntent/event_id, Q5 audit dedup, Q6 process/secret wiring. Không đòi P2 triển khai toàn BE1 trong B1, không coi assumed fixture là actual adapter.
4. **G5 môi trường và profile:** environment có thật, được phép dùng, PostgreSQL17/Redis/dependency inventory; nguồn actual secret không đưa vào record. Các giá trị DISPATCH_START_TIMEOUT/MAX, NOTICE_ATOMIC_MAX, capability slack và existing attempt policy vẫn named PROPOSED nếu chưa được chốt; đề xuất fixture profile riêng khi phù hợp, không tự freeze production.
5. **G2 approval Phase B:** chỉ chuẩn bị lời duyệt mẫu tham chiếu đúng rev3 + ADR/port/env record, ghi rõ mẫu không là approval. Không sửa approvals/TASK_APPROVAL.md Phase A. Chỉ ghi một approval B riêng khi user thực sự gửi lệnh duyệt đúng scope và các preconditions hợp lệ; không suy từ prompt này.

Tìm quyết định đã có trong repo/session trước; nếu owner cung cấp actual inputs thì ghi nguyên văn/phạm vi/ngày/source và phân biệt record role-owning với project-owner directive. Chưa có câu trả lời, để PENDING và hoàn tất đề xuất reviewable, không giả sign-off hoặc gửi tin cho ai.

## Giới hạn và cập nhật

B1 là docs/decisions; B2–B6 code cần G1–G5 đúng như plan. Review PASS không là approval/adoption hay runtime PASS. ACTIVE Q00 chưa đổi nếu disposition vẫn pending; WIP implementation1, roadmap14 cards.

Giữ .gitignore publication triage và61 local diagnostics; preservesource/tests/runners/fixtures/approved Phase A plan/approval. Không install/start PostgreSQL/Redis/container/cloud/provider/upload/commit/push/deploy hoặc sửa backend.

Update CONTEXT/DECISIONS/status/tracker/index với actual decision state. Dùng existing harness/security/git diff --check cho docs và hash snapshot24; lưu repeated receipts trong feature evidence/local/ để không làm Git status phình do log.

Báo cáo tiếng Việt: link decision record, nhóm nào có quyết định thật, exact input còn thiếu và conditions trước code. Kết thúc ở pending gate hoặc records hợp lệ; không bắt đầu implementation bằng lời duyệt mẫu.
