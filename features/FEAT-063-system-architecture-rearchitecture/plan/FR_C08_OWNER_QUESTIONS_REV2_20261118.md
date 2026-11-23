# FR-C-08 owner questions — revision 2

**Status: OPEN.** These questions are not decisions or implementation approval. Recommendations are coordinator proposals only. SRS line numbers refer to the D-209 canonical unsigned working SRS in this checkout. D-208 is carried forward only where consistent with D-209.

## Q-A — Does explicit DELETE include FAILED and ABANDONED?

**D-209, item 4:** D-208 dispositions stand only where consistent with the adopted SRS; whether UC-07 and §21.2 deletion of a run that “đã hoàn tất” includes FAILED and ABANDONED as well as COMPLETED remains OPEN-OWNER.

**Historical D-208 item 6, quoted from `DECISIONS.md`:**

> 6. Cancel is limited to the 13 unfinished states permitted by Rev67 UC-11. Explicit DELETE is permitted for COMPLETED, FAILED, and ABANDONED. FAILED and ABANDONED are never purged automatically; their content remains until an authorized user requests deletion. Direct the next SRS revision to align UC-07 and Section 21.2 with this eligibility while preserving the UC-11 cancel exclusions. DELETE_PENDING and DELETED accept no new user delete/cancel command. No implementation may begin until the SRS wording and corresponding contract are updated and independently reviewed.

The adopted SRS contains these relevant statements:

- **SRS line 283, BR-39:** “| BR-39 | Tất cả trạng thái chờ thao tác người lớn, kể cả `DRAFT`, bắt đầu adult-wait khi không còn AI job và cần command người lớn. Tại +144 giờ tạo đúng một inbox reminder theo dedupe key; thử push best-effort và email best-effort chỉ tới địa chỉ đã xác minh của owner hiện tại. Inbox là nguồn chuẩn; lỗi gửi email/push không đổi trạng thái run. Ở +168 giờ, `VIDEO_READY` thành `COMPLETED`, trạng thái adult-wait khác thành `ABANDONED`, nhả khóa owner nhưng giữ nội dung đến khi người dùng xóa. `VIDEO_ADMISSION_PENDING` là system work, không có idle timer; nếu admission bị từ chối, StoryRun về `SCRIPT_REVIEW` và bắt đầu adult-wait mới (Q133, Q136).”
- **SRS line 383:** “| Hoàn tất, thất bại, abandon hoặc hủy | Run ra khỏi tập active | Hoàn tất do người lớn hoặc idle closeout từ VIDEO_READY; run chờ khác thành ABANDONED sau 168 giờ adult-wait. FAILED/ABANDONED giữ nội dung đến khi xóa; cancel giải phóng khóa rồi xóa theo lifecycle. Run lỗi trước playable claim đầu không chiếm slot mẫu Teacher |”
- **SRS line 500, FR-C-08:** “| FR-C-08 | M | Cho người lớn hủy run chưa hoàn tất hoặc xóa run đã hoàn tất qua lifecycle. Lệnh hủy run chưa hoàn tất phải nhả khóa active ngay; thu hồi upload/playback, hủy job best-effort, xóa nội dung liên kết và báo tiến trình purge. Không hoàn quota request video đã nhận; giữ metadata quota tối thiểu và Teacher sample claim đã thành công. |”
- **SRS line 656, NFR-31:** “| NFR-31 | Giới hạn lưu dữ liệu | M | Synthetic demo tuân theo Q66/Q129/Q133: run hoàn tất/abandoned và media giữ đến khi người dùng chủ động xóa; không có auto-purge theo ngày. Đây là lựa chọn demo, không được áp dụng cho dữ liệu trẻ thật/production. Trước real-data gate phải chốt retention tối đa theo loại dữ liệu, backup expiry, DSR, xóa khỏi backup hoặc crypto-shredding và bằng chứng hoàn tất xóa. |”
- **SRS line 1064:** “| Run, tranh/audio, transcript, story revisions, scenes, video hoàn tất hoặc ABANDONED | Đến khi người dùng chủ động xóa; Q66/Q129/Q133 không đặt auto-purge theo ngày | Xóa qua lifecycle; backup theo chính sách backup demo được duyệt, hiện không có chính sách backup real data | Synthetic demo only; production gate bắt buộc retention max |”
- **SRS line 1350:** “| Adult-wait / `ABANDONED` | State không có AI job đang chạy và cần thao tác người lớn. Reminder ở +144 giờ; ở +168 giờ `VIDEO_READY` thành `COMPLETED`, state adult-wait khác thành `ABANDONED`; nội dung giữ đến khi người dùng xóa. |”
- **SRS line 1372:** “- Parent/Teacher có thể kết thúc run sau khi xem video sẵn sàng. Nếu không có thao tác có ý nghĩa ở mọi adult-wait state (kể cả DRAFT), hệ thống nhắc tại +144 giờ và đóng tại +168 giờ; `VIDEO_READY` thành COMPLETED, state khác thành ABANDONED. Nội dung giữ đến khi người dùng xóa; email reminder chỉ gửi best-effort nếu current owner có email đã xác minh.”
- **SRS line 1470, UC-07:** “| Điều kiện tiên quyết | Run đã hoàn tất; caller có quyền; run chưa trong quá trình xóa |”
- **SRS line 1674, §21.2:** “| DELETE /v1/story-runs/{id} | Chủ sở hữu Parent hoặc Teacher được phân quyền | Chỉ run đã hoàn tất; lifecycle command idempotent | 202 deletion request/status |”

**Question:** For the user-triggered DELETE route, does “đã hoàn tất” mean COMPLETED only, or also FAILED and ABANDONED?

**Options:** A. COMPLETED only; B. COMPLETED, FAILED, and ABANDONED; C. define another explicit set and reconcile the relevant SRS sections.

**Recommendation:** Keep this open until the owner selects and the SRS/contract are reconciled. A provisional COMPLETED-only recommendation is weak: if ABANDONED remains ineligible, its retained content would have no user-triggered lifecycle DELETE route under that policy. FAILED and ABANDONED must never be purged automatically.

## Q-STATES — How should the M2 cancel state set be reconciled with UC-11?

**SRS line 1518:** “| Điều kiện tiên quyết | Run chưa ở COMPLETED/FAILED/ABANDONED/DELETE_PENDING/DELETED; caller còn quyền theo assignment hiện tại; run revision hiện tại được biết |”

Static source currently accepts seven run-state literals in the cancel repository. Five intersect the SRS's 13 cancel-eligible states. Eight SRS-eligible states are rejected with 409 `INVALID_STATE_TRANSITION`: `DRAFT`, `INPUT_REVIEW`, `STORY_GENERATING`, `VIDEO_QUEUED`, `VIDEO_GENERATING`, `VIDEO_SAFETY_VALIDATING`, `VIDEO_READY`, and `SAFETY_BLOCKED`. Two source-only values, `SCRIPT_GENERATING` and `SCRIPT_GENERATION_UNKNOWN`, are outside the SRS 18-state inventory. The response schema also omits `ABANDONED` and `DELETED`.

**Question:** Which compatibility disposition should govern before changing the cancel route or response contract?

**Options:** A. implement the 13 SRS-eligible states after separately mapping or removing source-only values without adding a public state; B. retain the seven source values under an explicit SRS deviation; C. another owner-defined mapping with its own reviewed contract.

**Recommendation:** A only after an explicit compatibility map for the two source-only values and a response-schema decision. Do not infer a new public state or silently preserve the partial set.

## Q-PARENT — Which typed Parent-scope request and durable receipt contract applies?

**SRS line 771:** “| OwnerScopeRefV1 | Resource có owner scope | kind là ORGANIZATION, PARENT_ACCOUNT hoặc GLOBAL; GLOBAL chỉ dùng cho catalog/policy nền tảng; ID opaque; backend suy ra actor để xác thực |”

**Question:** Which existing or separately approved contract carries `PARENT_ACCOUNT` scope across BE1, Story, AI Jobs, and Core Asset, and which module owns its durable lifecycle receipt?

**Options:** A. prove an existing typed contract and receipt owner; B. prepare a separately reviewed DTR/schema and contract proposal; C. split ownership across versioned module receipts with an agreed reconciliation contract.

**Recommendation:** A only if source proves it. Otherwise stop for B or C. Never fabricate `organization_id` for a Parent request.

## Q-TEACHER — Which current assignment/version authorizes Teacher lifecycle actions?

**SRS line 1469:** “| Actor chính | Chủ sở hữu Parent hoặc Teacher hiện đang được phân công phụ trách lớp; creator cũ chỉ còn provenance |”

Current source inspection found no Teacher lifecycle route and no current Teacher-assignment resolver for this flow. `be1_parent_role_adapter.py` reads whether a verified identity has an active Parent role; it does not resolve the current Teacher assignment.

**Question:** Which BE1 assignment/version source and cross-module adapter must each command, read, and content-access boundary use?

**Options:** A. use an existing authoritative versioned assignment resolver after proving its contract; B. define a versioned BE1 authorization contract and owner-owned adapter; C. restrict the first approved scope to Parent only.

**Recommendation:** A only with source evidence; otherwise B or C requires owner selection. Fail closed on stale or missing assignment evidence.

## Q-READ — Can the existing StoryRun GET prove safe progress and verified deletion?

**SRS line 780:** “| StoryRunDetailV1 | Một response tổng hợp cho client | Current run/input/script/video pointers, safe stage, scene/job statuses, authorized asset/playback refs và quota summary qua owner ports. Không trả prompt, raw transcript, hidden story revision, foreign-scope existence hoặc provider error detail. |”

**SRS line 805:** “| /v1/story-runs/{id} | Đọc StoryRunDetailV1 tổng hợp hiện trạng và timeline an toàn; backend compose từ Story, AI Jobs, Core Asset, Lesson/Billing ports tùy run, không có cross-schema SQL hoặc nhiều endpoint bắt frontend phải ghép |”

**SRS line 1164:** “| AC-41 | Client được phép đọc một StoryRun; một số resource có thể thuộc owner/module khác | Client gọi `GET /v1/story-runs/{id}` | Một StoryRunDetailV1 tổng hợp status, timeline, scene, job-safe error, permitted assets và quota qua owner ports; không cross-schema SQL, không fan-out phía frontend, không rò prompt/transcript/profile support/foreign-scope existence, không có read-model table | §9.5–§9.7; §22.4; NFR-05/10 |”

**SRS line 1811:** “`GET /v1/story-runs/{id}` trả StoryRunDetailV1 tổng hợp để frontend không gọi nhiều endpoint theo từng module. Application read composer đọc Story làm gốc, gọi AI Jobs lấy stage/job status theo target, Core lấy asset/playback readiness, Lesson kiểm occurrence/assignment khi Teacher, và Billing trả quota summary khi được phép. Response có scene/generation status, current input/script/generation refs, error code an toàn, current authorization và playback ref ngắn hạn nếu đủ quyền. Không trả prompt/provider payload, transcript thô, profile support note, revision ẩn, hay tồn tại resource ngoài scope. Không lưu read-model table hay duplicate mutable state; endpoint dùng cursor/version để cache an toàn và ETag.”

**M2 owner disposition, `approvals/TASK_APPROVAL.md` line 3250:** “5. **`GET /v1/story-runs/{run_id}`** (SRS section 9.6: "Đọc StoryRunDetailV1 tổng hợp hiện trạng và timeline an toàn"): "Không chặn" — the response-content difference (no `StoryRunDetailV1` timeline) is recorded OPEN-OWNER and does not block client integration.” This is an M2 disposition, not lifecycle-purge proof.

**Question:** Does the existing owner-scoped GET provide enough lifecycle progress and terminal proof, or is an additional read contract required? D-208 proposed the existing GET as the default, and D-209 permits D-208 only where consistent. Q-READ and Q-PARENT both remain open; D-209 requires a StoryRunDetailV1 safe timeline but does not define purge percentage or the exact owner evidence predicate.

**Options:** A. extend the existing GET with only an owner-approved lifecycle projection; B. use existing detail as-is and keep pending until owner evidence can be represented; C. propose a separate read route only if the current GET cannot meet the SRS.

**Recommendation:** B as the baseline; select A or C only after an exact field, authorization, and evidence contract is reviewed. Never report `DELETED` from access denial alone.

## Q-FENCE — What acceptance-time fence blocks access and late dispatch/results?

**SRS line 1797:** “- Hủy run chưa hoàn tất chuyển run sang DELETE_PENDING và giải phóng khóa active trong transaction ghi nhận lệnh. Ghi `StoryRunCancellationRequestedV1`, tạo lifecycle request, thu hồi playback/upload và yêu cầu hủy job đang chờ/chạy. Worker kiểm tra cancellation trước stage tốn tài nguyên và trước khi nhận kết quả; nếu không ngắt được provider, output đến muộn là stale, không playable và bị xóa qua lifecycle. Giữ quota usage đã nhận và sample claim Teacher thành công.”

**Question:** Which durable versioned fence covers API reads, downloads, playback tokens, cache/stream, in-flight uploads, dispatch, and late-result acceptance when cancellation is accepted?

**Options:** A. owner modules validate a shared lifecycle version/fence at each access and worker boundary; B. define a separate reviewed revocation protocol; C. another explicit owner-approved contract.

**Recommendation:** A only if every owner boundary and race is evidenced; provider interruption is best-effort and is not purge proof.

## Q-PURGE — Which owner contracts prove purge and shared-reference safety?

**SRS line 1473:** “| Luồng thay thế | Thất bại xóa object hiện tại được retry idempotent và trạng thái vẫn pending; giữ asset dùng chung đến khi đối soát các tham chiếu được phép khác; Teacher cũ sau reassignment không còn quyền xóa, Teacher phụ trách mới được xử lý theo policy lifecycle |”

**Question:** Which module contracts enumerate and remove run-owned references, clean incomplete uploads, verify independent shared references, and provide durable completion evidence?

**Options:** A. owner-module acknowledgements plus reference closure and idempotent retry; B. defer terminal deletion until each owner supplies a contract; C. another reviewed ownership model.

**Recommendation:** A only after the Core reference-closure and storage ownership contracts exist. Preserve shared assets until an independent valid reference is positively reconciled.

## Q-WORKFLOW — Which durable records represent retry and reconciliation?

**SRS line 1520:** “| Luồng chính | Application command kiểm tra actor/state/revision và idempotency → trong một transaction chuyển run sang DELETE_PENDING và giải phóng khóa active → thu hồi playback/upload → ghi cancellation notice và lifecycle request → gửi hủy best-effort tới job/provider → lifecycle xóa nội dung liên kết → ghi DELETED và audit metadata tối thiểu |”

**Question:** Which existing records represent request acceptance, owner work, retries, reconciliation, and verified completion without adding public StoryRun states?

**Options:** A. map every durable phase to existing approved records; B. propose a separate DTR/schema change; C. use versioned owner-module receipts with a reviewed coordinator.

**Recommendation:** A only with a complete phase-to-record map; if any required durable phase is unmapped, stop for B or C. Do not reuse `AiJob` state as purge state by analogy.

## Q-AUDIT — Which metadata, readers, and retention map are approved?

**SRS line 2758:** “17. **Audit metadata/retention — PARTIAL.** Audit is metadata-only and excludes raw child media/content. Retention targets are 180 or 365 days by record type; exact type-to-duration map, field allowlist, audit authorization and physical mapping remain OPEN-TECHNICAL. Ảnh hưởng: NFR-34/36, data dictionary/physical ERD gate.”

**Question:** Which metadata fields and readers are permitted, where is Parent scope represented, and which record types use 180 versus 365 days?

**Options:** A. approve a field/reader/scope/retention matrix in the DTR; B. defer audit-dependent implementation until the mapping exists; C. another explicit mapping.

**Recommendation:** A before dependent audit writes or reads. Exclude raw child content and do not guess physical fields.

## Q-BASE — What is the FR-C-08 implementation base and sequence relative to CONV-1?

**Current root-checkout evidence:** `DECISIONS.md` contains D-066-68 through line 405, which says CONV-1 still needs its own Task Approval. The inspected `TASK_APPROVAL.md` contains a MGR-7 approval entry at lines 366–374 but no CONV-1-specific approval entry. D-066-71, the CONV-1 package Draft 5, and the named implementation evidence file were not found at their expected root paths during this observation. The two governance files are tracked and clean in this checkout. This does not establish the state in another worktree or prove whether implementation work happened.

**Question:** Given that the CONV-1 approval, implementation status, and exact approved file set cannot be verified from the current root checkout, which exact branch and commit should FR-C-08 use, and should it wait for a separately evidenced CONV-1 commit and integration before re-pinning shared paths?

**Options:** A. select and re-pin the current root feature branch, leaving any CONV-1 overlap outside scope; B. first provide and verify the missing CONV-1 approval, implementation evidence, and exact file set, then select an owner-authorized integrated commit and re-pin; C. name another exact branch and commit with its evidence.

**Recommendation:** B only after the missing CONV-1 records and exact file set are supplied and verified; otherwise choose A or C explicitly. No approval, implementation state, base, or sequence is selected here.

## Q-M2-GATE — Does the accepted M2 closure satisfy D-208 item 8?

**D-208 item 8:** “Reconcile and pin the partial, dirty M2 baseline as a separate coordination gate before FR-C-08 implementation. M2 approvals, allowlists, and command ceilings do not transfer to FR-C-08.” The owner later accepted S3 and closed M2 with recorded debt and deviations (`approvals/TASK_APPROVAL.md` lines 3243–3247; `status/STATUS.md` line 876).

**Question:** Does that owner-accepted M2 closure satisfy D-208 item 8's separate baseline reconciliation and pinning gate, or is any additional reconciliation required before FR-C-08 implementation?

**Options:** A. accept the recorded M2 closure and limitation ledger as meeting that gate; B. require a separate pinned M2 baseline reconciliation; C. another exact evidence threshold.

**Recommendation:** Keep open. The existence of an M2 closure does not by itself answer the specific gate unless the owner confirms the evidence threshold.

## Q-OWNERS — Which named people accept launch accountability?

**D-208 item 4:** “Authorize the current Parent owner or the Teacher currently assigned to the class, validated against the current BE1 assignment/version. Former Teacher status and creator provenance do not grant authority. The owner must assign named accountable module owners before launch.” D-209 carries this direction only where consistent with the adopted SRS. This is a governance/launch question, not a SRS quote naming individuals.

**Question:** Which named person accepts each responsibility for BE1 coordination, Story state/event, Core Asset reference/deletion, AI Jobs, Lesson claim preservation, and HTTP/evidence, and where will each assignment be recorded?

**Options:** A. assign named owners by module; B. narrow launch scope to modules with named owners; C. defer launch.

**Recommendation:** A before launch. Named accountability does not replace technical contract resolution.

## Owner disposition record

No answers are recorded in this revision. Preserve all questions as OPEN until the owner provides explicit dispositions. Any answer requiring a new route, public state, DTR row, table, column, constraint, migration, or path outside a reviewed allowlist requires separate review and approval.
