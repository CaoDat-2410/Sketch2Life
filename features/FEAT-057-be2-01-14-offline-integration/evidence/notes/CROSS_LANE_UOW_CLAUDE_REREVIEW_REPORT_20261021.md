Now hash verification of all manifest files and the other named documents.

All pinned hashes match so far. I'll now review the foundation service, completion path, dispatch worker, BE2-07 resolver, and BE2-14 accounting source to verify lock order and the mapping claims.

I've verified the source claims for the lifecycle, locking, and read-model points. Now checking the untracked adapter directory, diffs to approval/status files, and the scope index for any divergence from the slice plan.

# Review độc lập: scope Rev3 và quyết định D1

**Verdict: CHANGES_REQUIRED.**

Rev3 giữ đúng các điều kiện owner chốt:
- BE2-01 sở hữu UoW, còn BE2-08 chỉ là participant.
- Có bảng A/S/B/F.
- Thứ tự khoá job → run → fence được nêu.
- Không mở rộng enum (không có `REJECTED` JobState).
- CR08-01 được nêu rõ.
- X01 vẫn PARTIAL, X05d BLOCKED, X05c/CR09-02 mở.
- Không có giá trị budget được tự điền.

Tuy nhiên nhiều dòng của bảng boundary mô tả thao tác, row hoặc thứ tự khoá mà source hiện tại không cho phép hoặc không có. Đây là lõi của D1 nên chưa nên chuyển sang supplemental approval. Không có P1 mới. P1-1 và P1-2 mới đóng một phần.

## Xác minh source

- HEAD là `1649b729…`, khớp manifest.
- Manifest `88368265…` khớp.
- Cả 14 file nguồn trong manifest đều khớp SHA256.
- Rev3 (`507EF557…`), D1 (`3EECF89A…`), slice plan Rev4 (`6AF69E07…`), erratum (`7530294B…`), supplement BE2-08 (`F24823A1…`) và scope Rev2 (`39B0FD59…`) đều khớp.
- Các file tôi đọc nhưng manifest không pin, nên các kết luận dựa vào chúng là **chưa xác minh theo hash**. Hash quan sát được, không phải hash pin:
  - `application/services/ai_jobs.py`: `DF6AC4FD…`
  - `domain/ai_jobs/model.py`: `512B6046…`
  - `infrastructure/knowledge_video/codec.py`: `3E6AFFAE…`
  - `infrastructure/ai_jobs/sql/tables.py`: `12F6CE1E…`
- Hai file `knowledge_video_media.py` và `infrastructure/ai_jobs/fakes.py` tôi không dùng làm bằng chứng.

## Findings

| ID | Mức | Section / source | Bằng chứng | Sửa cần thiết |
|---|---|---|---|---|
| F-01 | P2 | Matrix dòng F | Domain video chỉ có `start`, `finalize`, `cancel` (`domain/knowledge_video/model.py:226-251`). Không có fail, timeout, retry hay block. Docstring dòng 5 ghi "BE2-10 owns exhausted dispositions", nhưng dòng F buộc run CAS sang `failed_exhausted`. Reject hiện có cho ra `BLOCKED_UNSAFE` (`services/ai_jobs.py:985-989`), `CANCELLED` (`:974-979`) và `FAILED_*` (`:994-999`), mà run không đi tới được. Danh sách file BE2-08 trong Rev3 không có `domain/knowledge_video/model.py` và `codec.py`. | Thêm bảng "lý do → JobState → run state". Đưa file domain và codec vào danh sách BE2-08 candidate. Quyết định bằng CR xem BE2-08 hay BE2-10 sở hữu `failed_exhausted`. |
| F-02 | P2 | Matrix F và đoạn "Reconciler…" | Rev3 chỉ liệt kê chung "fail/cancel/timeout/retry/reject". Các đường ghi job thực tế: `cancel_job` (`:448`), `apply_cancellation_notice` (`:505`, khoá toàn bộ job khớp trong một UoW, `repository.py:881-908`), cancel khi bị từ chối ở dispatch (`:577-583`), start (`:673-679`), retry (`:908-912`) và completion (`:974-979`), overdue (`:849`), dispatch-lost (`:647`), requeue (`:915`) và `report_progress` (`:699`). | Thêm bảng writer → boundary. Nêu rõ notice cancel enlist N run sau khi đã khoá hết job. Nêu `report_progress` là job-only và được miễn (hoặc enlist). Nêu nhánh cancel trong S. |
| F-03 | P2 | Dòng S và dòng A | Dòng S ghi caller là "worker, reconciler, dispatcher", nhưng reconciler và dispatcher không start. Route video (`worker.py:74-80`) bỏ qua `AiJobService.start_attempt` (kiểm tra capability và eligibility fence). `VideoWorkerAdmission.begin` (`ports/knowledge_video_worker.py:49-59`) chưa có entry UoW của BE2-01. Dòng A ghi run "bound to … initial attempt", nhưng run chỉ có `attempt_id` và chỉ gán khi `start()` (`model.py:226-232`). Run không lưu attempt number. | Đặt tên API start của BE2-01 (kèm participant) và vị trí kiểm tra capability. Nêu nhánh bị từ chối eligibility và kết quả `DUPLICATE_DELIVERY` / `ATTEMPT_NOT_ACTIVE`. Sửa "attempt ID/number" thành ID. |
| F-04 | P2 | Dòng A và B, cột rows enlisted | Dòng A thiếu `put_semantic` (`:429`) và audit intent (`:435`). Hai index dedup độc lập: `SemanticRequestKey` của foundation và `find_semantic(session_id, pin_digest)` của video (`knowledge_video/sql.py:69-76`). Dòng B ghi "immutable artifact row" và receipt, nhưng `tables.py` chỉ có `RUN` và `RECEIPT` (receipt tạo). Artifact nằm trong `run_json`. Không có chỗ lưu `completion_key`, trong khi `AtomicVideoFinalizer.lookup` cần nó. | Liệt kê đủ row. Thêm quy tắc đối chiếu hai index dedup: lệch thì fail-closed. Nêu cách phục hồi `completion_key` từ `completion_receipt(job_id, attempt_id)` cộng `run.artifact`. Nếu cần bảng mới thì dùng CR (đang bị loại trừ). |
| F-05 | P2 | Reject boundary | Rev3 chưa nói rõ quan hệ giữa việc phát hiện reject trong B và reject UoW. Source cho thấy foundation đã commit CAS, receipt và intent cùng nhau (`:758-767`). Với job không đổi, nó commit intent riêng như incident (`:745-768`, `_write_side_effects :1204-1213`). Đường reject trước finalize của BE2-08 chỉ gọi `request_quarantine`, nuốt exception (`knowledge_video_worker.py:236-243,272-276`), không có intent foundation. Port finalizer chỉ có `lookup` và `finish` (`ports/knowledge_video_worker.py:91-117`). | Ghi rõ trình tự: B không ghi gì → reject UoW lấy lại khoá job rồi run theo đúng thứ tự → đọc lại trạng thái → hoặc CAS ghép cặp kèm intent (attempt còn hiệu lực), hoặc chỉ intent (đã terminal/cancelled/superseded). Dùng `event_id` xác định sẵn. Nêu port nào gọi reject, cách ánh xạ `ExactRef` sang `artifact_refs`, và quan hệ với `request_quarantine` của BE2-08. Đường recovery khi B rollback hiện có là `recover_stage`/`reconcile` rồi sweep timeout; cần nêu rõ lỗ hổng "worker chết thì rerender". |
| F-06 | P2 | Lock order | `_hold` chạy trước mọi mutation (`:406,481,576,672,763,907`). Nếu run chưa bị khoá trước đó thì thứ tự thành job → fence → run. `hold_owner_fences` giữ fence theo thứ tự caller, không sắp xếp (`repository.py:544-548`, `:763` truyền `fence, *artifact_fences`). Creation lease bọc `submit` bên ngoài UoW (`knowledge_video_create.py:98-107`), nên "lease sau fence rows" là bất khả. Transaction của invalidator hay notice không được khoá job/run khi đang giữ fence FOR UPDATE. Ledger BE2-14 dùng `engine.begin()` riêng, khoá scope row (`accounting_sql.py:107,336`). Câu "outbox lease không được giữ" nhầm lease logic với row lock (`_dispatch_one` giữ lease qua lúc publish, `:595-611`). | Quy tắc: participant khoá run ngay sau khi khoá job và trước `_hold`. BE2-01 sắp xếp fence theo canonical key. A: lease là guard tách rời, không atomic. Mở rộng quy tắc thứ tự sang transaction của invalidator. Cấm mở giao dịch accounting lồng trong UoW. Viết lại câu về outbox: chỉ row lock mới tính. |
| F-07 | P2 | Fence protocol, mục 1 | Danh sách input khớp `_current` của BE2-07 (`knowledge_bundle.py:256-276`). Nhưng thiếu các input mà finalizer cần theo `finish` (`ports/knowledge_video_worker.py:108-116`): policy epoch, kill, rights, encoding, profile, library asset, model profile (`model.py:96-111`), eligibility fence và artifact descriptor fence. `OwnerFencePort` chưa có binding production (`repository.py:952-955`). | Bổ sung các input và owner tương ứng. Tách rõ "OwnerFence foundation (có hold, FOR SHARE, cùng connection)" với "fence nguồn BE2-07 (chưa có)". X01 giữ PARTIAL. |
| F-08 | P3 | Mapping job → run | `run_one_job` (org, job_id) tồn tại (`tables.py:28`), nhưng `VideoRunRows`/`VideoRunParticipant` không có `get_by_job` (`sql.py:59-76`, `ports/knowledge_video.py:125-144`). Không thể khoá run sau job nếu thiếu accessor. `session_id` của job nullable, của run thì không. Chỉ `context_revision` chung giữa `request_ref` và pin. Key idempotency của foundation (org, principal, contract, target, key) khác receipt video (org, session, principal, key). | Thêm `get_by_job(…, for_update)` vào candidate. Ghi bảng cặp trường cần so khớp. Giữ fail-closed và X09-08 NOT_IMPLEMENTED. |
| F-09 | P2 | Slice plan Rev4 và erratum | Xem mục dưới. | Rev5 của FEAT-057. |
| F-10 | P3 | Supplement BE2-08 read-model | Dòng 9 vẫn trỏ Rev2 (`39B0FD59…`). "Finalization receipt identity" nằm ở schema foundation, trong khi `tables.py` ghi "No FK or write into foundation". `VideoRun` không có trạng thái superseded. | Làm mới tham chiếu sang Rev3 (`507EF557…`) sau khi PASS. Bổ sung cách BE2-08 đọc receipt foundation. |
| F-11 | P3 | Adapter và evidence | Lỗi unique của video là `VideoError("VIDEO_WRITE_CONFLICT")` (`sql.py:83-87,141-142`), còn foundation raise `UniqueConflict`, và vòng retry chỉ bắt `UniqueConflict` (`ai_jobs.py:438`). `SqlAiJobUnitOfWork.connection` là thuộc tính public (`repository.py:344-348`). U01–U11 không có test thứ tự khoá job/run cho F, và không có test participant không begin/commit/rollback. | Adapter phải dịch `VIDEO_WRITE_CONFLICT` thành rollback toàn UoW rồi replay trong transaction mới. BE2-01 phải công bố API enlist thay vì để adapter đọc `.connection`. Thêm U12 (lock-order/deadlock cho F) và test negative cho participant. |

## Các finding P1/P2 trước

| Finding cũ | Trạng thái | Lý do |
|---|---|---|
| P1-1 (thiếu S/F) | **PARTIALLY_CLOSED** | Đã có dòng S/F, nhưng F-01 đến F-05 cho thấy các dòng chưa khớp source. |
| P1-2 (source fence) | **PARTIALLY_CLOSED** | X01 PARTIAL trung thực, yêu cầu hai thứ tự thắng trên PostgreSQL và fail-closed đều có. Còn F-06 và F-07. Không coi `resolve_exact` hay coordinator process-local là fence đang giữ. |
| P2-1 (mapping) | **CLOSED** | Hướng đúng: lookup `job_id` → run, không đánh đồng các ID, envelope giữ nguyên, thiếu/sai thì fail-closed. Còn F-08 là P3. |
| P2-2 (adapter / lease) | **PARTIALLY_CLOSED** | Phân chia ownership đúng, có unique-conflict rollback rồi replay trong transaction mới, có lost-ack. Còn vị trí creation lease (F-06) và F-11. |
| P2-3 (read model) | **CLOSED** (với Rev3) | Đã tách thành supplement BE2-08, BE2-09 không ghi row BE2-08. Phần còn lại thuộc supplement (F-10). |
| P2-4 (BE2-14) | **CLOSED** | Xác minh trong source: ledger dùng transaction riêng (`accounting_sql.py:336`), `Reservation` không có expiry (`accounting.py:133-147`; grep "expir/ttl/renew" trong `ai_policy` cũng không có). Tách ba gate, nêu expiry/renewal qua CR, giá trị synthetic. Còn việc cấm lồng giao dịch (F-06). |
| P2-5 (Rev4 quá lời) | **CLOSED** bằng erratum 1 | Đã sửa hai điểm cũ. Nhưng erratum cũng lỗi thời sau D1 (F-09). |
| P2-6 (case / test / nhãn) | **PARTIALLY_CLOSED** | Có U01–U11, 3 tên test và quy tắc gắn nhãn fake/SQL. Còn thiếu F-11. |
| P3 (pin source) | **CLOSED** cho manifest | Đủ 14/14 khớp. Còn các file ngoài manifest ở trên. |

## Lệch giữa Rev4 / erratum và D1

Khuyến nghị: tạo **FEAT-057 plan revision 5**, không thêm erratum 2. Lý do là chuỗi Rev4 + erratum 1 + erratum 2 khó đọc, trong khi nhiều gate phải đổi cùng lúc.

Các điều khoản cần cập nhật:
- **Rev4 §4 OD-X05a và §4A hàng X05a:** chỉ nói hai commit A và B. Cần thêm S, F và reject, cùng quy tắc "participant không begin/commit/rollback".
- **§5 G0 bước 4:** thêm bảng boundary, thứ tự khoá, reject commit và cặp CAS.
- **G1:** thêm gate "S/F cần review và supplemental approval riêng".
- **G2:** thêm S vào route typed (hiện bỏ qua `start_attempt`). Làm rõ mapping job → run.
- **G3 bước 2–4:** thêm F/reject/retry/timeout vào các case cần chứng minh. Câu "Hold or atomically revalidate" (dòng 247) đã bị erratum 1 sửa, Rev5 cần viết lại hẳn.
- **§6 A4:** mở rộng sang fail/cancel/timeout/retry/reject và thứ tự khoá.
- **Erratum 1:** các dòng S/F ghi "Pending owner disposition", mục "Recommended direction … not adopted", và status `OWNER_SCOPE_DECISIONS_PENDING` đã lỗi thời. Cách mô tả "intent lưu ở boundary riêng khi completion rollback" cũng chưa khớp D1 ("commit reject riêng, không dựa vào rollback").
- **Số dòng trích dẫn:** `ai_jobs.py:337` nay là `:342` (create_job).
- **`STATUS.md` của FEAT-057** dòng 13 vẫn liệt kê UoW Rev2 là bản sẵn sàng review.
- **Scope index:** đã ghi D1, nên không cần sửa ở bước này.

## Xác nhận

- Đây chỉ là review tài liệu/scope. Tôi không sửa file, không chạy test, DB, provider, Modal, Lightning hay runtime.
- Rev3 không cấp implementation approval và không đổi approval/status của card. Các thay đổi chưa commit trong approval/status của worktree đã có từ trước và không chứa nội dung Rev3. Rev3 không đổi X01/X05c/X05d và không thêm giá trị budget.
- PASS sau khi sửa chỉ có nghĩa scope đủ rõ để sang bước supplemental approval riêng cho từng card (đặc biệt S và F). Nó không cho phép bắt đầu code.

Review này mới chỉ nằm trong chat, chưa ghi vào repo.