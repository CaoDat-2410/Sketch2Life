# FR-C-08 owner questions — 2026-11-18

**Status: OPEN.** These questions are not decisions or implementation approval. Recommendations are coordinator proposals only. The quotations below are verbatim from the adopted D-209 SRS; line numbers refer to the pinned canonical file in the current checkout.

## Q-A — Does “completed” deletion include FAILED and ABANDONED?

**SRS, line 500:** “Cho người lớn hủy run chưa hoàn tất hoặc xóa run đã hoàn tất qua lifecycle.”  
**SRS, line 1674:** “| DELETE /v1/story-runs/{id} | Chủ sở hữu Parent hoặc Teacher được phân quyền | Chỉ run đã hoàn tất; lifecycle command idempotent | 202 deletion request/status |”  
**SRS, line 1470:** “| Điều kiện tiên quyết | Run đã hoàn tất; caller có quyền; run chưa trong quá trình xóa |”  
**SRS, line 1518:** “| Điều kiện tiên quyết | Run chưa ở COMPLETED/FAILED/ABANDONED/DELETE_PENDING/DELETED; caller còn quyền theo assignment hiện tại; run revision hiện tại được biết |”

**Question:** Does explicit DELETE eligibility cover only COMPLETED, or also FAILED and ABANDONED?  
**Options:** A. COMPLETED only; B. COMPLETED, FAILED, and ABANDONED; C. another explicitly listed state set.  
**Recommendation:** A until the owner clarifies. UC-07 and §21.2 say completed, and D-209 expressly leaves the broader interpretation open. Do not auto-purge FAILED or ABANDONED.

## Q-PARENT — Who owns the typed Parent lifecycle request and durable receipt?

**SRS, line 771:** “| OwnerScopeRefV1 | Resource có owner scope | kind là ORGANIZATION, PARENT_ACCOUNT hoặc GLOBAL; GLOBAL chỉ dùng cho catalog/policy nền tảng; ID opaque; backend suy ra actor để xác thực |”  
**SRS, line 1475:** “| Dữ liệu/yêu cầu | be1.data_lifecycle_requests, core.asset_metadata/lineage, story.*; FR-C-08, BR-26 |”  
**SRS, line 1523:** “| Dữ liệu/yêu cầu | story.runs; be1.data_lifecycle_requests; ai_jobs.cancellation_notice; core.asset_metadata/lineage; FR-C-08, BR-26, BR-40 |”

**Question:** Which versioned cross-module request carries `PARENT_ACCOUNT`, which module owns the durable request and receipt, and what already-approved physical mapping supports it?  
**Options:** A. use an existing typed contract and mapped storage after proof; B. prepare a separate DTR/schema proposal for owner review; C. another typed design with explicit ownership.  
**Recommendation:** A only if the existing contract can be demonstrated end to end. Otherwise stop for B. Never synthesize an `organization_id` for a Parent.

## Q-TEACHER — What proves current Teacher authority?

**SRS, line 1469:** “| Actor chính | Chủ sở hữu Parent hoặc Teacher hiện đang được phân công phụ trách lớp; creator cũ chỉ còn provenance |”  
**SRS, line 1518:** “| Điều kiện tiên quyết | Run chưa ở COMPLETED/FAILED/ABANDONED/DELETE_PENDING/DELETED; caller còn quyền theo assignment hiện tại; run revision hiện tại được biết |”

**Question:** Which BE1 assignment/version source and adapter authorize each lifecycle command, read, playback/download, upload, and dispatch check, and where must authorization be rechecked?  
**Options:** A. current versioned BE1 assignment source with checks at every owner boundary; B. another approved versioned source; C. deny the Teacher path until one is available.  
**Recommendation:** A, with fail-closed denial on missing/stale assignment and former-Teacher denial after reassignment. Creator provenance alone grants no authority.

## Q-READ — What read proves purge progress and DELETED?

**SRS, line 500:** “Lệnh hủy run chưa hoàn tất phải nhả khóa active ngay; thu hồi upload/playback, hủy job best-effort, xóa nội dung liên kết và báo tiến trình purge.”  
**SRS, line 1472:** “| Luồng chính | API xác minh Parent owner hoặc Teacher phụ trách hiện tại → ghi lifecycle request → chặn cấp playback token mới → xóa transcript, audio/tranh đầu vào, context snapshot, story revision, asset scene/video được tạo và asset phái sinh riêng tư đủ điều kiện → ghi hoàn tất và audit chỉ có metadata |”

**Question:** Is owner-scoped `GET /v1/story-runs/{id}` sufficient to expose an approved progress state and prove that DELETED follows verified purge, or is a separately reviewed read contract needed?  
**Options:** A. existing GET, with DELETE_PENDING until owner evidence proves completion; B. review an exact read-contract change; C. another owner-scoped read already in the approved contract.  
**Recommendation:** A if it can represent the predicate without a new public state; do not invent percentages. Otherwise choose B before implementation.

## Q-FENCE — What fences access and late work at acceptance?

**SRS, line 1520:** “| Luồng chính | Application command kiểm tra actor/state/revision và idempotency → trong một transaction chuyển run sang DELETE_PENDING và giải phóng khóa active → thu hồi playback/upload → ghi cancellation notice và lifecycle request → gửi hủy best-effort tới job/provider → lifecycle xóa nội dung liên kết → ghi DELETED và audit metadata tối thiểu |”  
**SRS, line 1797:** “Hủy run chưa hoàn tất chuyển run sang DELETE_PENDING và giải phóng khóa active trong transaction ghi nhận lệnh. Ghi `StoryRunCancellationRequestedV1`, tạo lifecycle request, thu hồi playback/upload và yêu cầu hủy job đang chờ/chạy. Worker kiểm tra cancellation trước stage tốn tài nguyên và trước khi nhận kết quả; nếu không ngắt được provider, output đến muộn là stale, không playable và bị xóa qua lifecycle. Giữ quota usage đã nhận và sample claim Teacher thành công.”

**Question:** Which owner-owned version/fence blocks new API, download, playback, cache/stream, upload/partial upload, and dispatch access on accepted request, and what happens if an owner is delayed or unavailable?  
**Options:** A. durable shared fence checked by each owning module; B. separate owner fences with an explicit transaction/receipt protocol; C. another fail-closed design.  
**Recommendation:** A if existing boundaries support it; otherwise B with a versioned acceptance protocol. Provider interruption remains best-effort and is never treated as purge proof.

## Q-PURGE — Who proves owner-module purge and shared-reference safety?

**SRS, line 1472:** “| Luồng chính | API xác minh Parent owner hoặc Teacher phụ trách hiện tại → ghi lifecycle request → chặn cấp playback token mới → xóa transcript, audio/tranh đầu vào, context snapshot, story revision, asset scene/video được tạo và asset phái sinh riêng tư đủ điều kiện → ghi hoàn tất và audit chỉ có metadata |”  
**SRS, line 1473:** “| Luồng thay thế | Thất bại xóa object hiện tại được retry idempotent và trạng thái vẫn pending; giữ asset dùng chung đến khi đối soát các tham chiếu được phép khác; Teacher cũ sau reassignment không còn quyền xóa, Teacher phụ trách mới được xử lý theo policy lifecycle |”

**Question:** Which exact Story, BE1, AI Jobs, Core Asset, storage, and Lesson owner contracts enumerate/remove run references, retry deletion, verify independent shared references, clear occurrence pointers, and report closure?  
**Options:** A. existing owner ports plus durable evidence; B. separate DTR/schema work where a contract is missing; C. split the lifecycle into separately approved slices.  
**Recommendation:** A where proven; B or C for any missing schema/owner proof. Keep shared assets until positive reference reconciliation; do not claim provider-copy or backup deletion without evidence.

## Q-WORKFLOW — What internal retry/reconciliation record is approved?

**SRS, line 1520:** “| Luồng chính | Application command kiểm tra actor/state/revision và idempotency → trong một transaction chuyển run sang DELETE_PENDING và giải phóng khóa active → thu hồi playback/upload → ghi cancellation notice và lifecycle request → gửi hủy best-effort tới job/provider → lifecycle xóa nội dung liên kết → ghi DELETED và audit metadata tối thiểu |”

**Question:** Which existing owner-owned records/statuses represent request acceptance, per-owner work, retryable failure, ambiguous provider outcome, reconciliation, and verified completion without adding public StoryRun states?  
**Options:** A. reuse existing mapped internal records after proving they cover every phase; B. prepare a separate DTR/schema proposal; C. split work by owner with a versioned receipt protocol.  
**Recommendation:** A only after a phase-to-record mapping is reviewed. If any required durable phase is unmapped, stop for B or C; do not infer that AiJob state is a purge state.

## Q-AUDIT — What metadata and retention map is approved?

**SRS, line 2758:** “17. **Audit metadata/retention — PARTIAL.** Audit is metadata-only and excludes raw child media/content. Retention targets are 180 or 365 days by record type; exact type-to-duration map, field allowlist, audit authorization and physical mapping remain OPEN-TECHNICAL. Ảnh hưởng: NFR-34/36, data dictionary/physical ERD gate.”

**Question:** Which metadata fields and readers are allowed, which typed Parent scope/module stores them, and which record types use 180 versus 365 days?  
**Options:** A. owner approves one field/reader/scope/retention matrix and records it in the DTR; B. defer audit-dependent implementation until that matrix exists; C. another explicit mapping.  
**Recommendation:** A before dependent audit writes/reads or full lifecycle acceptance. No raw child content or guessed physical fields.

## Q-BASE — What branch is the future implementation base?

**SRS, line 1674:** “| DELETE /v1/story-runs/{id} | Chủ sở hữu Parent hoặc Teacher được phân quyền | Chỉ run đã hoàn tất; lifecycle command idempotent | 202 deletion request/status |”  
This SRS sentence specifies the API behavior; it does not prescribe a Git branch. `feature/feat066-conv1` is a local-only branch observed at the current base. The latest CONV-1 plan is an unreviewed draft and is not a dependency.

**Question:** Should a future FR-C-08 task start from the accepted root feature branch, or from a later base only after a separately reviewed and authorized CONV-1 commit is integrated?  
**Options:** A. use the approved root implementation base and re-pin all files; B. wait for CONV-1 review/approval and an explicitly selected integrated commit; C. another named commit/branch.  
**Recommendation:** B only if the owner explicitly approves CONV-1 and its integration first; otherwise A at a newly pinned base. Do not rely on a local-only branch or unreviewed draft.

## Q-OWNERS — Which named people accept launch accountability?

**SRS, line 1472:** “| Luồng chính | API xác minh Parent owner hoặc Teacher phụ trách hiện tại → ghi lifecycle request → chặn cấp playback token mới → xóa transcript, audio/tranh đầu vào, context snapshot, story revision, asset scene/video được tạo và asset phái sinh riêng tư đủ điều kiện → ghi hoàn tất và audit chỉ có metadata |”

The adopted SRS does not name individual owners; this functional sentence identifies the work areas only. Named-person assignment is a governance/launch question carried from the prior lifecycle planning record where consistent with D-209, not a product requirement inferred from this quotation.

**Question:** Which named person accepts each responsibility area for BE1 request coordination, Story transition/event, Core Asset references/deletion, AI Jobs, Lesson claim, and HTTP/integration evidence, and where is the assignment recorded before launch?  
**Options:** A. record names against module responsibilities; B. narrow the launch scope to modules with named owners; C. defer launch.  
**Recommendation:** A before launch. Named-person accountability is a launch gate and does not replace technical contract resolution.

## Owner disposition record

No answers have been recorded in this draft. Keep all questions open until the owner provides explicit dispositions. Any answer that implies a new state, physical schema, migration, route, or file outside the allowlist requires a separately reviewed change before implementation.
