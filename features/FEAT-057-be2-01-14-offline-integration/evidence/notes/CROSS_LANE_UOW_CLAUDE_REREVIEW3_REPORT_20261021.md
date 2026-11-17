All 19 manifest entries and all listed documents match. Now the candidates and the owner decision D2.

Hashes and source facts are verified. I'm recording this review in memory before the write-up.

# Rereview 3: scope FEAT-044 Rev5 và plan FEAT-057 Rev6

## 1. Verdict

**CHANGES_REQUIRED.** Không có P1. Hầu hết finding của rereview 2 đã được xử lý đúng, nhưng còn hai P2 (một về STALE, một về budget). **S và F chưa nên gửi đi supplemental approval.**

Tôi đánh dấu các tầng của từng điều khoản như sau:
- **[SF]** là source fact.
- **[DR]** là design requirement.
- **[IMPL]** là hành vi đang chạy.
- **[GATE]** là gate card-owner/CR còn mở.

Mọi hợp đồng ở Rev5/Rev6 đều chỉ là candidate, chưa được adopt hay implement.

## 2. Bảng finding

| ID | Kết quả | Bằng chứng source, clause, và việc còn lại |
|---|---|---|
| **F-01** state mapping | **CHANGES_REQUIRED** (P2) | **Đã sửa đúng.** Rev5 §3 có đủ dispatch loss còn và hết retry, started failure/timeout ở attempt cuối, và foundation là bên quyết định exhaustion. Khớp `domain/ai_jobs/model.py`: `record_dispatch_loss` và `record_failure`. [SF] Foundation lưu `policy_snapshot_id` và `policy_snapshot` (JSON) trên bảng `job`, nhưng `JobRetryPolicy` chỉ có `policy_id`, `status="PROPOSED"`, không có version hay hash. Chính sách do `AiJobDependencies.retry_policy` cấp (mặc định `FIXTURE_RETRY_POLICY`), không theo từng request. `VideoPin.retry_policy` là `ExactRef` riêng. Vì vậy Rev5 §3 đúng khi chặn A; A hiện không thể qua. [GATE] cần CR của BE2-01 và BE2-10 (xem N-04). **Còn lỗi:** SUCCEEDED+STALE chưa có boundary (xem N-03). Hiện `VideoRun.generation_state` kiểu `JobState`, `codec._Run` ép `JobState`, và `save()` dùng `TERMINAL_STATES` của job. State stale mới sẽ lọt guard terminal nếu CR BE2-08 không đổi cả ba chỗ. |
| **F-02** writer inventory | **PASS** | Mười lệnh gọi `cas_job` đều nằm trong `application/services/ai_jobs.py`: `cancel_job`, `apply_cancellation_notice`, `_dispatch_one`, `_recover_unstarted`, `start_attempt`, `report_progress`, `accept_completion`, `_expire_overdue`, và hai nhánh của `retry_job`. Rev5 §4 phủ cả mười, gồm hai nhánh từ chối eligibility. Chỉ claim/ack/publish/delivery bị miễn, đúng với `_publish` và `ack_dispatch`. [IMPL] `VideoRunRows` chưa có caller production nào (chỉ có test), nên phía participant chưa tồn tại. |
| **F-03** attempt identity | **PASS** | Khớp D2. A, retry, và dispatch loss đều để run không có `attempt_id` (Rev5 §3, §5, §7). Chỉ S bind. `attempt_number` thuộc foundation. Lost-ack của S: cùng attempt đang running là duplicate, còn lệch cặp thì fail-closed. [IMPL] `VideoRun.__post_init__` hiện chỉ buộc `attempt_id` khi RUNNING/SUCCEEDED, chưa buộc rỗng ở QUEUED, và domain chưa có transition retry/fail. [GATE] CR BE2-08 phải thêm invariant này. |
| **F-04** receipt và recovery | **OPEN** (P3) | Rev5 §9 đúng khi tách accepted khỏi stale/rejected/intent-only. Tôi kiểm được `completion_key` tái tính được cho accepted từ dữ liệu persisted: `staging_key` và `completion_key` ở `application/knowledge_video_worker.py` cộng `media_operation_key` (pin digest, job, attempt, strategy), hash blob và `artifact.material()`, tất cả đều nằm trong run row. **Nhưng** `media_operation_key` nằm ở `application/knowledge_video_media.py`, file **không có trong manifest**. [DR] đưa file đó vào manifest. [DR] adapter không được trả lại `completion_key` do caller đưa vào: `_receipt` kiểm `result.completion_key`, và với non-accepted không có artifact để buộc khóa, chỉ còn fingerprint. |
| **F-05** reject | **OPEN** (P3 + một phần N-03) | Rev5 §5 đúng. B không mutate khi quyết định dưới lock là non-accepted, F-reject khóa lại và quyết định lại, và intent-only dùng `side_effect_recorded(event_id)`. Crash trước khi có identity bền vẫn chặn. Còn ba điểm. (a) Rev5 gọi `event_id` là "deterministic từ persisted … claim fingerprint", nhưng fingerprint của claim chưa persisted trước commit reject (`_quarantine_intent` trong `ai_jobs.py`). `reason` do quyết định tạo ra và có thể đổi giữa hai lần đánh giá, sinh `event_id` khác. Cần nói rõ đó là xung đột hay intent thứ hai. (b) Đầu vào đánh giá lại (moderation, claim) không bền, nên reject chỉ chạy được khi worker còn sống; Rev5 đã thừa nhận bằng gate crash. (c) `accept_completion` hiện ghi audit incident bền cho verdict tạm thời (`_commit_incident`). "B không ghi gì" phải nói rõ có kể incident này không. |
| **F-06** lock order | **OPEN** (P3) | Rev5 §6 gọi tên đúng ba path: `jobs_for_notice` (khóa mọi job khớp trong một câu lệnh rồi khóa lại từng job), `create_job` giữ fence trước khi insert, và `hold_owner_fences` theo thứ tự của caller. Nó cũng nói fixture sắp xếp và là ASSUMED_CONTRACT, và không khẳng định deadlock chưa chứng minh. Tôi đồng ý: mọi writer đều theo job → run, nên không có chu trình nếu không có writer khóa run trước. Hai điều còn thiếu. (a) Rev5 thay bằng "khám phá ID rồi khóa từng cặp", nhưng không yêu cầu kiểm lại predicate và state sau mỗi lần khóa, trong khi hiện tại dựa vào việc lock kiểm lại hàng (`notice_matches`, `CANCELLABLE_STATES`). (b) Fence từ participant được thêm sau một `_hold` đầu có thể có key nhỏ hơn fence đã giữ, phá thứ tự đã sắp xếp. [DR] mỗi UoW chỉ gọi hold một lần với tập đầy đủ, hoặc từ chối fence thêm muộn. |
| **F-07** fence ownership | **PASS** | `ArtifactDescriptor.fence` đến từ `artifacts` port của BE1 (`ai_jobs.py`, `ports/ai_jobs.py`). `editorial_revision` có dòng riêng trong `VideoPin`. `owner_fence_fixture.py` (sắp xếp và `FOR SHARE` một câu lệnh) tự khai là ASSUMED_CONTRACT. X01 giữ PARTIAL. Rev5 §2 viết "foundation's hold follows caller order", chỉ đúng với wrapper `SqlAiJobUnitOfWork`; port có thể sắp xếp, như fixture. |
| **F-08** field mapping | **PASS** | Bảng Rev5 §7 có đủ cặp trường. `request_id`, `request_revision`, `input_hash`, `target_id`, `purpose_code`, `subject_refs` không có đối ứng nên cần CR hoặc fail-closed. `session_id` null fail-closed (`job.session_id` nullable, `VideoPin.session_id` bắt buộc). Chỉ thiếu `job_type` (admission đã kiểm `_job_type`), mức P3. |
| **F-09** divergence | **PASS** | Rev6 §7 liệt kê đủ chín điều khoản, trùng danh sách của tôi lần trước. Con số 296 passed / 0 failed / 0 skipped đúng với `CROSS_LANE_X01_MODAL_20261020.json`. Còn thiếu hai mục ghi sổ (xem N-05). |
| **F-10** read model | **PASS** | Rev5 §11 và Rev6 §5, §7.6 nguồn receipt provenance từ supplement, giữ supplement nguyên trạng tới khi scope qua review, và nêu hệ quả của opaque ref lên `FinalArtifact`, `VideoRun`, codec, và phép so khớp `completed_run != expected` trong `_receipt`. Chỉ thiếu: state stale mới của D2 ảnh hưởng thế nào lên AR05 của read model (P3). |
| **F-11** lỗi participant | **PASS** | [SF] `VideoRunRows.insert`/`put_receipt` ném `VIDEO_WRITE_CONFLICT`; `save` ném `VIDEO_STALE_RUN`, `VIDEO_IMMUTABLE_LINEAGE`, `VIDEO_IMMUTABLE_ARTIFACT`, `VIDEO_TERMINAL_RUN`. Rev5 §10 yêu cầu rollback toàn UoW trước khi đọc lại và phân biệt replay với conflict. Vòng retry foundation chỉ bắt `UniqueConflict`, nên adapter bắt buộc phải dịch (Rev5 đã nêu). P3: nên có bảng phân loại đầy đủ, gồm `VIDEO_IMMUTABLE_ARTIFACT`, `VIDEO_INVALID_TRANSITION`, `VIDEO_ATTEMPT_NOT_CURRENT`, `VIDEO_STORAGE_CORRUPT`. Lỗi corrupt không bao giờ là replay. Lỗi của participant phải truyền ra ngoài, không được nuốt bên trong UoW. |
| **N-01** wording | **PASS** | Cả hai bản ghi `CHANGES_ADDRESSED_PENDING_INDEPENDENT_REREVIEW`. Không bản nào nói mọi finding đã đóng. |
| **N-02** BUDGET_EXCEEDED | **OPEN** (P2) | [SF] `ELIGIBILITY_ERRORS` có `BUDGET_EXCEEDED`, và ba nhánh cancel khi eligibility bị từ chối (`_dispatch_one`, `start_attempt`, `retry_job`) nằm trong **code của BE2-01**. Rev5 §11 chỉ yêu cầu BE2-14 chấp nhận một hợp đồng không-terminal. Nó chưa nói BE2-01 phải đổi ba nhánh đó và thuộc supplemental S/F nào. Cũng chưa định nghĩa trạng thái kết thúc của defer: nếu S bị hoãn thì job vẫn queued, và `_recover_unstarted` sẽ republish rồi `record_dispatch_loss`, tiêu hao retry budget và cuối cùng đi tới failed_exhausted. Gate: BE2-01 (ba nhánh) + BE2-14 (hợp đồng), cùng một CR. |

## 3. Xác minh manifest

- Worktree ở HEAD `1649b729…`, branch `feature/be2-backend-ai-integration`, dirty (95 mục); tôi chỉ dựa vào hash từng file.
- Manifest Rev3 (`8BC0998D…`) khớp; **19/19** file nguồn khớp, không có file thiếu hay lệch. Gồm `codec.py` và `owner_fence_fixture.py`, hai file lần trước chưa pin.
- Mọi tài liệu có hash đều khớp: Rev5, Rev6, D1, D2, rereview 1 và 2, Rev4 scope, Rev5 plan, Rev4 plan, erratum, BE2-08 scope, supplement, manifest Rev2.
- Tôi đọc nhưng manifest **không pin**: `application/knowledge_video_media.py` (`media_operation_key`) và `contracts/schemas/knowledge_video.py` (mà codec import). Kết luận về việc tái tính `completion_key` dựa vào file đầu chưa được xác minh theo hash.
- Hash chỉ chứng minh bytes. Chúng không chứng minh các file này đã được tích hợp với nhau.

## 4. Vấn đề mới (chưa có trong danh sách)

- **N-03 (P2), boundary cho STALE chưa được gán.** [SF] `_decide_completion` xử lý STALE bằng `jobs.succeed(..., ResultDisposition.STALE)`: đó là một commit authoritative với receipt, kèm `result_refs`, không thêm quarantine intent. Nó không phải reject. Rev5 §5 lại chuyển mọi kết quả non-accepted sang F-reject, mà F-reject được mô tả là reject cộng intent. Thiếu hai thứ: (a) bảng phân loại đầu ra của `_decide_completion` sang boundary (accepted → B, failure claim → F, rejection → F-reject, stale → ?, tạm thời → không commit); (b) bảng cặp hợp lệ giữa (JobState, disposition) của job và state của run, vì khi run là stale terminal thì nguyên tắc "run phản chiếu job" không còn đúng. [DR] gán stale cho một boundary kiểu B (receipt STALE, run sang stale terminal, không artifact). [GATE] owner BE2-01 (commit) cùng CR BE2-08 (state). Dọn dẹp stage private của stale cũng chưa được định nghĩa: foundation không ghi intent nào cho stale, còn `_quarantine` của worker bị nuốt exception.
- **N-04 (P3), retry-policy.** Xem F-01: nên ghi rõ nguồn foundation và việc A hiện không qua được.
- **N-05 (P3), ghi sổ divergence.** Rev4 scope viết rằng `infrastructure/cross_lane/knowledge_video.py` hiện có trong worktree; tôi kiểm thì file này **không tồn tại** (thư mục chỉ có `knowledge_script_video.py`). Rev5 lặng lẽ bỏ câu đó và Rev6 §7 không ghi. Ngoài ra BE2-08 scope addendum (`6A195B6F…`) vẫn dựa vào plan Rev4, chỉ có boundary A/B, loại `domain/knowledge_video/model.py` và `codec.py` khỏi danh sách file, và để trống hash. Cần cập nhật trước khi S/F sang approval, vì D2 buộc phải đổi domain và codec.
- **N-06 (P3), model.** `VideoRun` hiện chưa có transition retry, fail, block, timeout; CR BE2-08 phải thêm cùng với invariant của D2.

## 5. Kiểm lại các P1/P2 trước

| Finding cũ | Trạng thái |
|---|---|
| Boundary inventory | PASS (F-02). Phần còn lại là N-03. |
| Source-fence invalidators | Đúng thiết kế: X01 giữ PARTIAL. Cần owner, khóa, writer cho từng input trước khi claim fence bền. |
| Mapping job → run → pin | PASS với gate (F-08, N-04). |
| Composition adapter ownership | PASS (Rev5 §10). Chưa có file adapter nào tồn tại (N-05). |
| Artifact read model | PASS, chờ supplement (F-10). |
| BE2-14 separation | Tách đúng, nhưng N-02 mở. |
| Rev4/erratum divergence | PASS (F-09). |

## 6. Điều cần sửa trước khi sang supplemental approval

1. Thêm bảng phân loại đầu ra `_decide_completion` sang boundary và bảng cặp trạng thái job/run cho stale (N-03).
2. Chỉ định BE2-01 sở hữu việc đổi ba nhánh cancel-on-denial, định nghĩa trạng thái kết thúc của defer, và nêu CR chung với BE2-14 (N-02).
3. Sửa các điểm P3: `event_id`/reason và audit incident (F-05), kiểm lại predicate và tập fence một lần (F-06), manifest bổ sung và adapter không echo `completion_key` (F-04), bảng lỗi participant (F-11), ghi sổ N-05.

## 7. Phạm vi của review

Đây chỉ là review tài liệu và scope, kèm đọc source. Nó không phải adoption hợp đồng, không phải implementation approval, không phải card acceptance, và không phải bằng chứng runtime. Tôi không sửa repo, không stage hay commit, không chạy test, database, provider, server, Modal, Lightning hay runtime. S và F vẫn cần review độc lập và supplemental approval riêng. X01 giữ PARTIAL, X05d BLOCKED, X05c/CR09-02 OPEN, X09-08 NOT_IMPLEMENTED. Budget unit/limit chưa có. Review hiện chỉ nằm trong chat; ngoài repo tôi chỉ cập nhật memory note.