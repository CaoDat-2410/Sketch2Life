All 81 manifest hashes match and the index is empty; I've reviewed the packet, rereview 3, and the Rev6 scope. Next I'll go through the three CRs, the BE2-08 and BE2-14 scopes, and the plan, then verify them against source.

I've reviewed all drafts and the main lifecycle source in `ai_jobs.py`. Next, I'll check `TEMPORARY_VERDICTS`, `jobs.cancel`, the codec/SQL guards, the retry policy, and the fence code.

Still verifying source facts: the video model, SQL `save`, codec, `_receipt`, the media key formula and the contract test.

Status: source checks are done and match the drafts. Last pass: scan the drafts and state documents for overclaims, mixed-up terms and internal conflicts before I write the verdict.

# Review độc lập: scope/CR sau D3 (BE2-01..14)

## 0. Xác minh đầu vào

- Worktree truy cập được. Branch là `feature/be2-backend-ai-integration`, HEAD là `1649b729…`, index trống. Worktree dirty (nhiều file `M` và `??`), nên tôi dựa vào hash từng file.
- Hash gói review (`F51FDAD2…`) và manifest (`3010C8F5…`) khớp.
- **81/81 entry của manifest khớp hash và số byte.** Gồm 31 source/test, 3 snapshot, 9 current, 18 historical, 19 current-state và manifest Rev4. Không file nào thiếu hay lệch. 31 hash source trong D3 trùng hoàn toàn với manifest Rev4.
- Đường dẫn receipt D3 trong prompt ghi `FEAT-057-be2-01-14-integration`. Đường dẫn thật (theo manifest) là `FEAT-057-be2-01-14-offline-integration`. Hash khớp ở đường dẫn thật, nên đây chỉ là lỗi gõ trong prompt.

Nhãn dùng bên dưới: **[SF]** source fact, **[DR]** design requirement, **[GATE]** gate adoption/approval, **[IMPL]** hành vi đã chạy. Không có phát biểu nào ở đây đạt mức [IMPL].

## 1. Verdict: DOCUMENT/SCOPE CONSISTENCY = CHANGES_REQUIRED (hẹp)

Cả hai P2 cũ đều đóng trong draft. Còn **một P2 mới**, nhỏ và chỉ cần thêm chữ, ở nhánh completion-time (NEW-1). Ngoài ra có 5 P3 sửa chữ.

## 2. Disposition từng finding của rereview 3

| ID | Kết quả | File/section và bằng chứng |
|---|---|---|
| F-01 / N-04 retry policy | CLOSED_IN_DRAFT + [GATE] BE2-01/10 hợp lệ | Rev6 §2, §7 và Rev7 §4 ghi `JobRetryPolicy` chỉ có `policy_id`/`status`, không có version/hash. Khớp `model.py:103-112` và `ai_jobs.py:91,328`. `VideoPin.retry_policy` là ExactRef riêng (`knowledge_video_create.py:49`). A bị chặn đúng. |
| F-02 writer inventory | PASS giữ nguyên | Đủ 10 vị trí `cas_job` (`ai_jobs.py:488,530,582,651,683,701,764,853,912,918`). Rev6 §4 phủ cả mười. |
| F-03 attempt_id | CLOSED_IN_DRAFT + [GATE] | BE2-08 Rev2 §4.2. Hiện `model.py:210` chỉ buộc `attempt_id` ở RUNNING/SUCCEEDED, chưa buộc rỗng ở QUEUED. |
| F-04 completion_key | CLOSED_IN_DRAFT + [GATE] journal | Manifest D3 đã pin `knowledge_video_media.py` (`media_operation_key`, dòng 97) và `contracts/schemas/knowledge_video.py`. Công thức `worker.py:63-83` tái dựng được cho accepted từ dữ liệu đã lưu. Adapter không được echo key: Rev6 §9, Stale CR §6, BE2-08 §4.9. Non-accepted cần journal stage bền, nên thiếu thì thành gate, không cho rerender. |
| F-05 event_id/reason/audit | CLOSED_IN_DRAFT + [GATE] schema journal; xem NEW-4, NEW-5 | Fingerprint tạo trước normalise: `ai_jobs.py:715` so với `:726`. Rev6 §2 và Stale CR §4 ghi đúng. Event_id/reason bất biến sau lần commit đầu: Rev6 §6, §9. Intent-only không chiếm slot receipt: Stale CR §2, §6. Audit-only incident được giữ: `ai_jobs.py:766-768` so với Rev6 §3 và Stale CR §2. |
| F-06 notice + fence | CLOSED_IN_DRAFT | Rev6 §8 yêu cầu recheck `notice_matches` (tenant, CANCELLABLE_STATES, OR predicate) và revision của cặp run sau khi khóa. Fence union khóa một lần, fence tới muộn thì restart. Khớp `repository.py:881-908` (khóa tất cả match trước khi đọc lại). |
| F-07 owner fence | PASS giữ nguyên | Phát biểu caller-order được giới hạn đúng ở wrapper `SqlAiJobUnitOfWork` (`repository.py:544-545` chuyển tiếp nguyên thứ tự). Fixture tự sort (`owner_fence_fixture.py:139`) và tự khai ASSUMED_CONTRACT. |
| F-08 mapping | CLOSED_IN_DRAFT | Rev6 §7 có job → run → pin, `job_type`, session null fail-closed, các trường không có counterpart. Nguồn: `create_job` ở `ai_jobs.py:364-375`. |
| F-09 / N-05 divergence | CLOSED_IN_DRAFT | `cross_lane/knowledge_video.py` không tồn tại. Thư mục chỉ có `knowledge_script_video.py`, là source reader (đã đọc). Cả Rev6 §2 lẫn Rev7 §7 đều ghi vậy. Rev7 §8 và BE2-08 Rev2 §1-2 ghi rõ khác biệt giữa scope A/B cũ với D1/D2/D3. |
| F-10 read model | CLOSED_IN_DRAFT + [GATE] provenance | BE2-08 Rev2 §7: AR01/AR05 loại stale-không-artifact và tách khỏi historical accepted bị đổi eligibility sau này. Contract test dòng 91 đang từ chối `"stale"` nên cần schema versioned. |
| F-11 participant errors | CLOSED_IN_DRAFT | Bảng ở Rev6 §9 và BE2-08 §6 đủ mã lỗi (đối chiếu `sql.py` và `model.py:230-249`). Lỗi thoát UoW, rollback trước lookup, corrupt không bao giờ replay. |
| N-01 wording | PASS | Mọi draft ghi pending review, không có bản nào nói "đã đóng". |
| **N-02 budget (P2)** | **CLOSED_IN_DRAFT** + [GATE]; xem NEW-1 | Budget CR §3 bao ba nhánh với held pair QUEUED: `_dispatch_one` (`:557`), `start_attempt` (`:657`), `retry_job` (`:892`). Retry là requeue đúng một lần kèm hold. Claim/ack/recover/watchdog được phủ ở §5. Nguồn: claim tăng `publish_attempts` (`repository.py:721`), ack tăng `dispatch_count` (`:769`), `_recover_unstarted` (`:626`). Consent/kill vẫn cancel. Không gọi provider khi đang hoãn. Điểm kết thúc là RESUMED hoặc CLOSED (§4). Max duration giữ PENDING, không bịa số. |
| **N-03 stale (P2)** | **CLOSED_IN_DRAFT** + [GATE] BE1 | Rev6 §3 có bảng outcome → boundary và bảng cặp (job state, disposition, receipt, run). Đối chiếu từng hàng với `_decide_completion` (`:952-1008`) và `model.py` (`block_unsafe`/`succeed`) đều đúng. Guard-STALE (`completion.py:80-86`) được tách khỏi stale authoritative: receipt không lưu vì `authoritative=False` (`ai_jobs.py:761-768`). Stale hiện không ghi quarantine (`:1000-1005`), nên Stale CR đúng khi coi nhánh này là thay đổi mới của BE2-01. |
| N-06 model | CLOSED_IN_DRAFT | BE2-08 Rev2 §4 (state type, transitions, codec `_Run.generation_state`, `TERMINAL_STATES` ở `sql.py:17,104`, `_receipt`). Phù hợp điều kiện 5 của owner. |

Hai cách diễn giải owner được kiểm riêng:

- "Tạm thời → không commit" trong draft nghĩa là không commit lifecycle hay outcome authoritative. Incident audit-only vẫn được lưu. Đúng với source: `TEMPORARY_VERDICTS` = INVALID_STATE và INPUT_MISMATCH (`ai_jobs.py:160`), job không đổi và incident vẫn ghi.
- Câu cuối của owner dừng ở "event_id". Draft không suy diễn thêm chỉ thị nào, và dùng report rereview 3 để rà P3. Cách xử lý này đúng.

## 3. Finding mới

**NEW-1 (P2): Hợp đồng deny/defer của budget chưa nói gì về nhánh completion-time.**
- [SF] `_decide_completion` (`ai_jobs.py:974-979`) khi `eligibility.eligible` là false sẽ `jobs.cancel` rồi quarantine output. `eligibility` đến từ `_check(job)` (`:727`), dùng chung từ vựng với `ELIGIBILITY_ERRORS`, trong đó có `BUDGET_EXCEEDED`.
- [DR] Rev6 §3 viết "*Genuine* eligibility denial" nhưng không định nghĩa "genuine" theo reason code. Stale CR §2 lại viết "Current eligibility denied" (không có chữ genuine). Budget CR và BE2-14 Rev2 không có chữ nào về completion.
- Hậu quả nếu chỉ sửa ba nhánh như D3 liệt kê: output đã sinh xong có thể bị cancel và quarantine vì budget, trong khi provider đã chạy.
- Cần thêm một hàng hoặc câu: kết quả resource tại completion không bao giờ cancel hay quarantine. Settlement/accounting thuộc hợp đồng riêng. Hoặc ghi rõ đây là quyết định còn mở của card-owner.

**NEW-2 (P3): thứ tự kiểm descriptor và stale chưa được nói rõ.** Stale CR §4 và Rev6 §6 nói descriptor không map được thì "fail-closed/pending". Source (`:992-999`) thì validate output *trước* nhánh stale: output không validate sẽ thành `OUTPUT_MALFORMED` (FAILED_EXHAUSTED, F-reject) trước khi tới stale. Cần ghi thứ tự, và ghi rằng "unavailable" khác "absent" (BA07). Hiện `describe()` trả None cho cả hai.

**NEW-3 (P3): danh sách path ứng viên của BE2-14 bị đảo giữa hai tài liệu.** Budget CR §7 coi `ai_policy_accounting` (port/schema) là chính và `ai_policy_use.py` là có điều kiện. BE2-14 Rev2 §5 làm ngược lại và thêm `application/ai_policy_use.py`. Cần thống nhất trước khi đóng exact manifest.

**NEW-4 (P3): định danh "operation" của F-reject/intent-only chưa có công thức.** Stale CR §6 phân biệt ba loại (replay, xung đột khi input đổi, incident mới) nhưng không nói khóa nào phân biệt chúng. Reason của guard thay đổi theo verdict, và reason nằm trong công thức event_id (`:1191-1200`). Đây là gate hợp lệ của journal CR, nhưng journal CR phải được yêu cầu định nghĩa khóa này.

**NEW-5 (P3): nhãn "cách diễn giải" chỉ nằm ở gói review.** Packet §3 mục 4 có nhãn này, còn Rev6 §3 và Rev7 §3 mô tả như phép áp dụng đã chốt. Receipt D3 không ghi gì về điểm này. Nên thêm một câu vào Rev6 §3: "diễn giải bảo thủ, owner có thể xác nhận".

**Ghi chú nhỏ:** trong STATUS/CONTEXT của FEAT-044/050/057, mục cũ "Current checkpoint: Claude rereview 3" vẫn nói C1/C2 "still awaiting the owner". Dòng 11 đã nói các mục dưới là lịch sử, nên chỉ là vệ sinh tài liệu.

## 4. Implementation readiness (riêng, không suy ra từ PASS tài liệu)

- **Chưa có approval nào.** Tất cả [GATE]:
  - BE1 artifacts adoption BA01-BA09. Packet vẫn NOT_SENT.
  - CR chung BE2-01/14, CR schema riêng và migration mới (path hiện UNASSIGNED), CR stale-finalization.
  - CR lifecycle/state/codec/receipt/projection versioned của BE2-08, API get-by-job có khóa (không tồn tại trong `VideoRunRows`), journal stage/reject.
  - Mapping retry-policy (BE2-01/10), các trường request thiếu, `job_type` route.
  - Phase của accounting chỉ có create/dispatch/retry, chưa có phase cho S.
  - Source-fence owner cho X01 bền (giữ PARTIAL). Provenance receipt cho read model.
  - Exact manifest source/test từng card và supplemental approval S/F/schema.
- File composition adapter chưa tồn tại. X01 PARTIAL, X05d BLOCKED, X05c/CR09-02 OPEN, X09-08 NOT_IMPLEMENTED.

## 5. Quyết định owner thật sự còn thiếu (không hỏi lại C1-A/C2-A)

1. Thời gian hoãn tối đa: con số, đếm cái gì, và hành động khi chạm ngưỡng.
2. Đơn vị và hạn mức budget. Điều khoản expiry/renewal của reservation (BE2-14).
3. NEW-1: xử lý kết quả resource ở completion-time (card-owner BE2-01/14). Gợi ý: không cancel/quarantine.
4. Tùy chọn: xác nhận cách diễn giải "tạm thời" ở NEW-5.
5. Câu bị cắt "event_id" của D3: nếu owner có điều kiện cụ thể thì cần bổ sung. Tôi không suy diễn.

## 6. Xác nhận phạm vi

Tôi chỉ đọc file, tính hash và xem trạng thái branch (`git status` dùng `--no-optional-locks`). Tôi không sửa file nào, kể cả repo, memory, scope, hash manifest và approval. Không chạy test, SQL, provider, server, Modal hay Lightning. Không fetch, stage, commit, push, merge hay đổi branch. Không gửi tin ra ngoài.