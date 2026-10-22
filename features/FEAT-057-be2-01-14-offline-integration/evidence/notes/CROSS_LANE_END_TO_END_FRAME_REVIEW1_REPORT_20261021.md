# FEAT-057 end-to-end execution frame — independent review 1 report — 2026-10-21

- Status: PRESERVED_REVIEW_INPUT. Verdict as delivered: CHANGES_REQUIRED (0 P1 / 5 P2 / 8 P3).
- Reviewed plan: `plan/CROSS_LANE_END_TO_END_EXECUTION_FRAME_DRAFT_20261021.md`, SHA256 `1B17056637542C78342076C050E46C55666DE21F2AC562CCCBD2D7F48406C2FD`, 21,759 bytes.
- Reviewed manifest: `evidence/metrics/CROSS_LANE_END_TO_END_FRAME_INPUTS_20261021.json`, SHA256 `9B6DECC3D37A9183333A5F7F731D5DE01EBF0BA4B235AF774A8C3E1E9129746A`.
- Provenance: independent read-only review by Claude in a chat session on 2026-10-21, at the owner's request. The report was delivered in chat only; this file reproduces its findings so the successor and re-review can cite exact text. The wording below is the delivered report with formatting kept; no finding was added, removed or softened. One edit for repository security: the local absolute worktree path in the input-verification table is written in its repository-relative form.
- Authority: review evidence only. It is not owner adoption, implementation approval, card acceptance or runtime authorization.

---

# Review độc lập: CROSS_LANE_END_TO_END_EXECUTION_FRAME_DRAFT_20261021

**Verdict: CHANGES_REQUIRED.** Không có P1. Có 5 P2 và 8 P3. Plan giữ đúng các trạng thái bắt buộc: X01 PARTIAL, X05d BLOCKED, X05c/CR09-02 OPEN, D4 pending, runtime hoãn. Plan cũng không tự nhận là implementation approval. Tuy vậy, plan bỏ sót hoặc rút gọn sai một số ràng buộc đã có trong Rev7, Budget CR Rev2, Rev8 và các owner disposition, nên chưa đủ chính xác để chuyển sang bước chuẩn bị implementation.

## 1. Xác minh đầu vào

| Mục | Kết quả |
|---|---|
| Worktree | `.worktrees/be2-01-14-integration-linked` ✔ |
| Branch / HEAD | `feature/be2-backend-ai-integration` / `1649b72978877d82b4d7662040ff3555dee0a3a7` ✔ |
| Plan | SHA256 `1B170566…C2FD`, 21,759 byte ✔ |
| Manifest | SHA256 `9B6DECC3…746A` ✔ |
| Nguồn được manifest pin | **39/39 khớp cả hash lẫn kích thước**, không thiếu file nào |
| Staged | Trống |
| Dirty | 147 path. Gồm 145 path lúc snapshot, cộng plan và manifest (cả hai untracked). Khớp ghi chú trong manifest. Có cả source thuộc card khác đã sửa sẵn: `worker.py`, `typed_dispatch.py`, test BE2-01. |

Số liệu evidence trong plan khớp với metrics: 14 test X01, 282 test adjacent, Modal 296/296.

## 2. Verdict: **CHANGES_REQUIRED**

## 3. Findings

### P2-1: Thứ tự khoá ở §4 (dòng 79) không đầy đủ và lệch với Rev7 §8 / Budget CR Rev2 §6
- **Bằng chứng:** Plan chỉ ghi "one lock order for all paired paths: job → run → fence union". Các tài liệu nguồn nói chi tiết hơn:
  - Rev7 §8 yêu cầu khoá *tất cả* cặp job/run theo thứ tự job ổn định, rồi mới khoá union fence *một lần*. Cấm kiểu pair1/fences → pair2. Fence phát hiện muộn thì phải restart.
  - `create_job` giữ fence trước khi insert. Đây là ngoại lệ chỉ dành cho A.
  - Invalidator đã commit fence trước thì phải mở UoW lifecycle mới.
  - Accounting không được lồng dưới lifecycle lock.
  - Budget CR dòng 62 đặt hold/dispatch bookkeeping nằm giữa run và fence. CR này còn ghi rõ thứ tự khoá cho multi-job và ngoại lệ outbox claim *vẫn cần review*.
  - Source hiện tại: `jobs_for_notice` khoá mọi job theo thứ tự id (`repository.py:881-905`). `ack_dispatch` đọc outbox trước rồi mới khoá job (`repository.py:747-772`).
- **Tác động:** Dòng 18 viết "agreed lock order" như thể đã chốt. Trong khi đó D1 #4 yêu cầu đối chiếu với mọi lock path thực tế. Người làm G2 có thể bỏ qua đường notice, đường invalidator và ngoại lệ của A, dẫn tới rủi ro deadlock.
- **Sửa:** Thay dòng 79 bằng tham chiếu chính xác tới Rev7 §8 và Budget CR §6 kèm SHA. Liệt kê các ngoại lệ và mục còn mở: multi-pair, A-only, invalidator, outbox claim, late fence. Đổi chữ "agreed" ở dòng 18 thành "selected, pending lock-path review".

### P2-2: Bảng boundary §4 thiếu các bảng mà D3 C2-A #4 bắt buộc, và định nghĩa "I" bị lệch
- **Bằng chứng:**
  - Plan không có bảng ánh xạ đầu ra của `_decide_completion` sang boundary, cũng không có bảng cặp hợp lệ (JobState, disposition, receipt, run). Rev7 §3 có cả hai.
  - Thiếu dòng guard JOB_CANCELLED/JOB_TERMINAL/ATTEMPT_SUPERSEDED. Trường hợp này không phải authoritative nhưng *vẫn commit* quarantine intent và audit, và không chiếm completion slot (`ai_jobs.py:966-972`, `761-768`).
  - Thiếu dòng H (hold/resume).
  - Dòng I trong plan là "infrastructure incident… recover from stage journal". Theo source và Rev7, I là incident chỉ ghi audit cho INVALID_STATE/INPUT_MISMATCH/lỗi normalise (`ai_jobs.py:160`, `738-740`). Plan cũng không ghi rằng cách diễn giải bảo thủ ở NEW-5 vẫn chờ owner xác nhận.
- **Tác động:** G2 yêu cầu "Implement A/S/B-accepted/B-stale/F/F-reject/I" dựa trên một bảng thiếu dòng và sai nghĩa của I.
- **Sửa:** Đưa vào (hoặc tham chiếu chính xác kèm SHA) hai bảng ở Rev7 §3. Thêm dòng guard intent-only và dòng H. Sửa I theo đúng source. Ghi NEW-5 là pending owner confirmation.

### P2-3: Chưa tách budget khỏi current-use eligibility ở mọi call site
- **Bằng chứng:** `_check()` dùng chung một bộ reason, trong đó có BUDGET_EXCEEDED, ở 6 chỗ: `create_job` (`ai_jobs.py:389-393`, trả 429), `_dispatch_one`, `start_attempt`, `accept_completion` (D4), `retry_job`, và **đường đọc `get_job_status`** (`ai_jobs.py:935-940`, dùng `_check(job).eligible` để quyết định có hiện kết quả hay không). Plan §5 và cả bộ CR chỉ xử lý 3 nhánh cộng D4. Không tài liệu nào nhắc tới A hay `get_job_status`. Ngoài ra dòng S (dòng 72) chỉ ghi "policy/reservation", thiếu execution authorization. Rev7 §4 có đủ ba gate.
- **Tác động:** Kết quả ACCEPTED có thể bị ẩn chỉ vì hết budget, tức budget bị coi như thu hồi quyền dùng. Hành vi ở A so với hold cũng chưa được định nghĩa.
- **Sửa:** Thêm bảng kê đủ 6 call site, quy định BE2-14 phải trả kiểu resource và current-use tách biệt, và ghi rule cho A và đường đọc (giữ nguyên hoặc là owner gate). Dòng S cần ghi đủ eligibility, execution và reservation, và fail-closed khi một gate unknown/unavailable.

### P2-4: Ranh giới X05d / X02 chưa rõ, có nguy cơ dùng X02 để lấp X05d
- **Bằng chứng:**
  - OD-X05d và G0 B6 định nghĩa X05d là resolver/fence current-source *đã được adopt sẵn* của BE2-07/09. Nó phải bao cả *review commit* lẫn playback intent. Nếu chưa có thì "không kéo X02 vào". Receiver X02 mới cần quyết định và approval riêng.
  - BE2-09 scope R05/R07 quy định: không được ghi review thành công khi X05d chưa có.
  - Plan G1 (dòng 94) không liệt kê resolver/fence của X05d. G5 và branch 6 gộp X02/X04/X05 kèm câu "resolve X05c/X05d gates". Exit G5 ghi "stale/recalled content cannot be reviewed or played", điều này có thể đạt được qua invalidation X02.
- **Sửa:** Định nghĩa X05d ngay trong dòng X05. Ghi rõ review commit cũng bị chặn khi thiếu X05d. Ghi rõ X02 không thay thế được X05d và cần approval riêng. Thêm X05d vào G1. Tách X05d khỏi branch 6 hoặc ghi rõ owner là BE2-07. Bổ sung câu: playback intent không chứng minh quyền session/access.

### P2-5: Thiếu điều kiện tiên quyết của A và ràng buộc giữ nguyên envelope
- **Bằng chứng:**
  - Rev7 §2/§7 và Rev8 §4 ghi "A currently remains blocked" cho tới khi BE2-01/10 adopt mapping retry-policy có version. Lý do: `JobRetryPolicy` không có version/hash, còn `VideoPin.retry_policy` là ExactRef.
  - Các trường request_id/revision/input_hash và target_id/purpose_code/subject_refs chưa có counterpart. Session null phải fail-closed.
  - Rev7/Rev8 và approval BE2-01 đều yêu cầu `WorkerDispatchEnvelope` giữ nguyên.
  - Plan không nhắc tới retry policy, BE2-10 (với vai trò này) hay envelope. G2 vẫn ghi "Implement A".
- **Sửa:** Thêm vào G1 và điều kiện vào G2: mapping retry-policy BE2-01/10 (`FEAT-052-be2-video-failure-disposition`), mapping các trường request, null session fail-closed. Thêm bất biến "WorkerDispatchEnvelope unchanged; mapping chỉ lấy từ dữ liệu đã persist".

### P3
1. **X09-08:** Ghi nguyên văn "X09-08 NOT_IMPLEMENTED" như STATUS và Rev8, thay cho "route-level partial evidence". Router hiện chọn route theo `message.job_type` (`typed_dispatch.py:60-67`), và `VideoWorkerAdmission.begin` chưa có implementation phía foundation. Cũng cần ghi hệ quả lifecycle với job type lạ: job vẫn QUEUED, bị republish, rồi thành dispatch-loss. "Không có side effect" mới chỉ đúng với phía provider.
2. **FEAT id mơ hồ:** G2/G4/G6 ghi "FEAT-049", "FEAT-050". Theo collision map, các số này trùng với BE2-03/04, trong khi G6 lại động tới đúng BE2-03/04. Cần ghi đủ tên thư mục.
3. **Manifest thiếu nguồn chi phối:** `OWNER_DISPOSITION_X01_X05_20261021.md`, G0 ballot/contract review (nơi ghi B6/X05d), các approval file của card, BE2-03/04 consumer records, Budget schema CR. Ngoài ra BE2-14 Rev3 còn tham chiếu bản Budget CR cũ, không phải REV2.
4. **Source của card khác đang nằm trong worktree tích hợp:** Typed route BE2-01 đã được approve và sửa ngay trong worktree FEAT-057. Điều này mâu thuẫn với quy tắc ở dòng 121. G0 cần nêu rõ disposition: commit theo owner tại đây hay chuyển sang worktree của owner.
5. **Năm scope card đã approve theo hash:** AD1BA…, CA531…, 6A195…, 12169…, 417A7…. Cần ghi đây là historical và không bao các path mở rộng trong Rev3 (theo Rev8 dòng 36). Cũng cần nói rõ S/F cần supplemental approval riêng theo D1.
6. **§5 thiếu một số đường so với Budget CR:** `claim_outbox`, `ack_dispatch`, `queued_dispatched_not_started`, `run_due_retries`, đóng hold khi cancel/notice, việc re-dispatch sau resume. Cũng thiếu "không reserve/settle dưới lock". Chỉ cần tham chiếu Budget CR Rev2 §3/§5.
7. **B-stale:** Nêu tên các CR cụ thể (BE2-01 stale CR Rev2, BE2-08 Rev3) và trạng thái packet BE1 là NOT_SENT. Cần thêm: output phải validate trước khi xét stale, descriptor FOUND/ABSENT/UNAVAILABLE là ba trạng thái riêng, và không có commit một phần nếu không map được (NEW-2).
8. **X05b:** Ghi rõ BE2-09 sở hữu review head và projection DATA-27, khoá theo đúng artifact hash/version, và không được ghi vào row/migration của BE2-08. Read-after-commit phải chạy trên cùng store với finalization.

## 4. Đã kiểm tra, không có vấn đề trọng yếu
- Có hai atomic boundary A và B riêng, provider chạy ở giữa, không transaction nào bao trùm.
- BE2-08 là participant, không được begin/commit/rollback. Không cho phép half-pair.
- D1/D2/D3 được tóm tắt đúng. D4 không bị suy diễn (dòng 23, 87). G2 chặn completion handling cho tới khi D4 đóng.
- C1-A: job và run đều QUEUED, không thêm state mới, `attempt_id` null tới S, retry chỉ requeue một lần, recovery không tính thời gian hoãn, số liệu để pending.
- BE2-14 chỉ được deny/defer, không tự cấp budget hay execution.
- X01 giữ PARTIAL nếu chưa có fence cùng store. Fixture không được dùng để giả lập fence. Modal và process-local test không nâng được trạng thái X01.
- Tiêu chí hoàn tất (§7) chặt và đúng với Rev2 A11. Không có chỗ nào nói quá kiểu "đã nối", "adopted" hay "approved".
- BE1, Git publication, DB conformance, Modal và Lightning đều được đặt sau gate riêng.

## 5. Các gate còn pending hoặc blocked
- **Candidate design (chưa adopt):** Rev7, Budget CR Rev2, schema CR, Stale CR Rev2, BE2-08 Rev3 và read-model, BE2-14 Rev3, BE2-09 scope, Rev8, chính plan này.
- **Owner design direction (không phải approval):** D1, D2, D3 C1-A/C2-A, OD-X01/X05a/X05b/X09-08/POLICY-08, G0 B1–B5/B7.
- **Đang mở hoặc blocked:** D4. Đơn vị, hạn mức budget, thời gian hoãn tối đa và deadline action. Phase S và expiry/renewal của reservation. Adoption BE1 (packet NOT_SENT). Fence cùng store cho X01. X05d BLOCKED. X05c/CR09-02 OPEN. Mapping retry-policy BE2-01/10. X02–X09 NOT_IMPLEMENTED.
- **Implementation approval:** chỉ có subset typed route BE2-01, đã implement nhưng chưa commit. Chưa có approval S/F/schema nào.
- **Implementation:** chưa có boundary lifecycle nào được implement.

## 6. Xác nhận phạm vi
Tôi chỉ đọc file, tính hash và chạy `git status/diff/rev-parse`. Không sửa, tạo, xoá, stage hay format file nào, kể cả memory. Không chạy pytest, Modal, Lightning, server, DB hay provider. Không fetch, commit, push, merge hay đổi branch. Sau review, HEAD, branch, 147 dirty path, index trống và hai hash plan/manifest đều giữ nguyên. Verdict này không phải approval triển khai.
