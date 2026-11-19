# FR-C-08 owner questions and D-214 dispositions — Revision 5

**Status:** Planning reconciliation only. D-214 records the owner selections below; this document does not approve implementation.
**Authority:** D-209 canonical unsigned SRS, read together with D-214. D-214 amends nothing in the SRS; its item 1 directs a separate documentation-only SRS revision.

Each question retains the relevant verbatim canonical SRS line. Governance questions with no SRS rule say so explicitly. D-214 resolves the selected option for eleven questions; Q-OWNERS records the selected assignment policy but remains open for names and record location.

## Q-A — Explicit DELETE eligibility

**Question:** Does the approved user-triggered DELETE set include only COMPLETED, or also FAILED and ABANDONED?

**Canonical SRS basis:**
> SRS line 270:
> | BR-26 | Khi người dùng xóa run đã hoàn tất hoặc hủy run chưa hoàn tất, lifecycle xóa tranh, audio, transcript, snapshot hồ sơ của run, revision story, media scene/video và nội dung liên kết. Lệnh hủy giải phóng khóa active ngay; lệnh xóa/hủy chỉ giữ audit metadata tối thiểu. Với occurrence Teacher, giữ trạng thái slot mẫu đã dùng và thời điểm claim; xóa pointer đến run/media nhưng không mở lại slot. Không có thao tác xóa video riêng. Unit quota đã tiêu thụ không được hoàn lại (Q119, Q123). |

> SRS line 383:
> | Hoàn tất, thất bại, abandon hoặc hủy | Run ra khỏi tập active | Hoàn tất do người lớn hoặc idle closeout từ VIDEO_READY; run chờ khác thành ABANDONED sau 168 giờ adult-wait. FAILED/ABANDONED giữ nội dung đến khi xóa; cancel giải phóng khóa rồi xóa theo lifecycle. Run lỗi trước playable claim đầu không chiếm slot mẫu Teacher |

> SRS line 1470:
> | Điều kiện tiên quyết | Run đã hoàn tất; caller có quyền; run chưa trong quá trình xóa |

> SRS line 1674:
> | DELETE /v1/story-runs/{id} | Chủ sở hữu Parent hoặc Teacher được phân quyền | Chỉ run đã hoàn tất; lifecycle command idempotent | 202 deletion request/status |

**D-214 disposition:** Option B. Permit user-triggered DELETE for COMPLETED, FAILED, and ABANDONED. Never automatically purge FAILED or ABANDONED.
**Effect:** This answers the eligibility ambiguity for planning and requires a separate documentation-only SRS alignment of UC-07, §21.2, and BR-26 before implementation.
**Remaining open point:** The SRS wording revision and its independent review are still required; no implementation approval exists.
**Status:** ANSWERED BY D-214.

## Q-STATES — Cancel-eligible state set and response schema

**Question:** How should the cancel command handle the SRS state set and the two source-only values without expanding the public state inventory?

**Canonical SRS basis:**
> SRS line 394:
> | StoryRun | DRAFT, INPUT_PROCESSING, INPUT_REVIEW, SUBJECT_REVIEW, PREPARATION_REVIEW, STORY_GENERATING, SCRIPT_REVIEW, VIDEO_ADMISSION_PENDING, VIDEO_QUEUED, VIDEO_GENERATING, VIDEO_SAFETY_VALIDATING, VIDEO_READY, SAFETY_BLOCKED, COMPLETED, FAILED, ABANDONED, DELETE_PENDING, DELETED | `run_state` mô tả bước nghiệp vụ nhìn thấy được; `AiJob.job_state` + `job_stage` mô tả xử lý ASR/VLM/story/video chi tiết. DRAFT là adult-wait khi cần người lớn nhập/xác nhận dữ liệu; DRAFT → INPUT_PROCESSING khi input đã nhận và ASR/VLM job được enqueue; input job thành công hoặc lỗi có thể khắc phục → INPUT_REVIEW; người lớn xác nhận transcript → SUBJECT_REVIEW; sửa chủ thể tạo VLM job mới và quay INPUT_PROCESSING → SUBJECT_REVIEW. Xử lý AI đang chạy không phải adult-wait dù màn hình hiển thị stage. SUBJECT_REVIEW/PREPARATION_REVIEW → STORY_GENERATING chỉ khi subject, context và một activity chính đã chọn/xác nhận; Teacher dùng activity đã duyệt, Parent bắt buộc chọn một activity trước script. STORY_GENERATING → SCRIPT_REVIEW; SCRIPT_REVIEW → STORY_GENERATING khi rewrite hợp lệ hoặc VIDEO_ADMISSION_PENDING khi script revision đã xác nhận; chỉ admission accepted mới đưa StoryRun/VideoGeneration sang VIDEO_QUEUED. Queue → generation → safety validation → VIDEO_READY khi đạt. Chỉ state không có job đang xử lý và cần command người lớn mới adult-wait: DRAFT, INPUT_REVIEW, SUBJECT_REVIEW, PREPARATION_REVIEW, SCRIPT_REVIEW, SAFETY_BLOCKED (khi cần người lớn) và VIDEO_READY. VIDEO_ADMISSION_PENDING là system work, không arm idle timer; budget/quota rejection đưa run về SCRIPT_REVIEW và bắt đầu adult-wait mới; receipt mơ hồ giữ pending tới reconcile. `last_meaningful_activity_at` do server ghi UTC khi người lớn gửi command/review/xác nhận có hiệu lực; polling/push receipt/app heartbeat không reset idle. `adult_wait_started_at` bắt đầu khi AI job kết thúc/lỗi và run thực sự cần thao tác người lớn. Sau 144 giờ tạo inbox reminder, push best-effort và email nếu current-owner email đã xác minh; sau 168 giờ VIDEO_READY → COMPLETED, adult-wait state khác kể cả DRAFT → ABANDONED; cả hai nhả khóa và giữ nội dung đến khi user xóa. AI job có deadline độc lập 6 giờ và không bị idle-closeout khi còn QUEUED/RUNNING/RETRY_WAIT/AWAITING_RECONCILIATION. Hủy run chưa kết thúc → DELETE_PENDING, nhả khóa ngay và khởi động purge. COMPLETED, FAILED, ABANDONED, DELETE_PENDING, DELETED không chiếm khóa. Reassignment không đổi state: quyền chuyển sang Teacher hiện được phân công, quyền cũ/token bị thu hồi, audit metadata được ghi. |

> SRS line 1518:
> | Điều kiện tiên quyết | Run chưa ở COMPLETED/FAILED/ABANDONED/DELETE_PENDING/DELETED; caller còn quyền theo assignment hiện tại; run revision hiện tại được biết |

**D-214 disposition:** Option A. Use the 13 SRS cancel-eligible states; explicitly map or remove SCRIPT_GENERATING and SCRIPT_GENERATION_UNKNOWN without adding a public state.
**Effect:** The cancel contract cannot be represented as SRS-compatible until the compatibility map and a response-schema decision are reviewed.
**Remaining open point:** The current response schema omits ABANDONED and DELETED; the exact compatible response contract remains open.
**Status:** ANSWERED BY D-214.

## Q-PARENT — Parent scope and durable receipt

**Question:** Which reviewed contract carries PARENT_ACCOUNT scope and owns the durable lifecycle receipt?

**Canonical SRS basis:**
> SRS line 771:
> | OwnerScopeRefV1 | Resource có owner scope | kind là ORGANIZATION, PARENT_ACCOUNT hoặc GLOBAL; GLOBAL chỉ dùng cho catalog/policy nền tảng; ID opaque; backend suy ra actor để xác thực |

> SRS line 1475:
> | Dữ liệu/yêu cầu | be1.data_lifecycle_requests, core.asset_metadata/lineage, story.*; FR-C-08, BR-26 |

> SRS line 1523:
> | Dữ liệu/yêu cầu | story.runs; be1.data_lifecycle_requests; ai_jobs.cancellation_notice; core.asset_metadata/lineage; FR-C-08, BR-26, BR-40 |

**D-214 disposition:** Option B. Prepare a separately reviewed DTR/schema and contract proposal as a delta to the SRS-named be1.data_lifecycle_requests; never fabricate organization_id.
**Effect:** The existing mapped request requires organization_id, so Parent scope needs an approved typed representation and durable receipt ownership.
**Remaining open point:** The DTR/schema delta, receipt ownership, physical mapping, and cross-module contract are not yet approved.
**Status:** ANSWERED BY D-214.

## Q-TEACHER — Teacher authorization boundary

**Question:** Which Teacher assignment/version contract authorizes lifecycle commands, reads, and content access?

**Canonical SRS basis:**
> SRS line 667:
> | P1 — Parent vertical slice | Parent profile → ảnh/ý tưởng → subject/activity/context review → story review → video Modal → playback/delete, trên dữ liệu tổng hợp | FR-P, FR-AI, subset FR-C/NFR, resumable media upload | Không dùng dữ liệu trẻ thật; quota fixture/config được cấp từ Billing |

> SRS line 668:
> | P2 — Teacher vertical slice | Organization/class/roster → profile → lesson import/review → occurrence/one child sample → script confirmation → video/chiếu/reassignment | FR-T, shared FR-AI/FR-C | Một child/activity/run; không classroom collaboration/batch |

> SRS line 1469:
> | Actor chính | Chủ sở hữu Parent hoặc Teacher hiện đang được phân công phụ trách lớp; creator cũ chỉ còn provenance |

> SRS line 2339:
> | FR-C-08 | M | BR-26/40 | UC-07/11 | story.runs; story.video_generations; be1.data_lifecycle_requests; core.asset_metadata; billing.video_quota_usage; lesson.occurrences | Cancel/delete GWT: lock release, asset purge, quota ledger and sample tombstone retained. AC-13/23. | P0; lifecycle as shared Parent/Teacher slice | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |

> SRS line 2341:
> | FR-C-10 | M | BR-35 | UC-09 | parent.child_profiles/data_authorizations; be1.managed_profiles/data_lifecycle_requests; story.runs | Deletion review: owner authorization, immediate revoke, lifecycle receipt and cross-scope isolation. AC-13. | P0; lifecycle as shared Parent/Teacher slice | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |

**D-214 disposition:** Option C. The first implementation scope is Parent only. Keep lifecycle design shared; defer the Teacher authorization adapter to a separately versioned current-assignment contract.
**Effect:** This is a scope limit against FR-C-08 and UC-07 wording that also names Teacher; the SRS phase plan places Parent in P1 and Teacher in P2.
**Remaining open point:** Teacher is not in the first implementation scope; its authorization contract remains a separate future gate.
**Status:** ANSWERED BY D-214.

## Q-READ — Lifecycle progress read

**Question:** How should a client read purge progress and verified terminal deletion?

**Canonical SRS basis:**
> SRS line 780:
> | StoryRunDetailV1 | Một response tổng hợp cho client | Current run/input/script/video pointers, safe stage, scene/job statuses, authorized asset/playback refs và quota summary qua owner ports. Không trả prompt, raw transcript, hidden story revision, foreign-scope existence hoặc provider error detail. |

> SRS line 805:
> | /v1/story-runs/{id} | Đọc StoryRunDetailV1 tổng hợp hiện trạng và timeline an toàn; backend compose từ Story, AI Jobs, Core Asset, Lesson/Billing ports tùy run, không có cross-schema SQL hoặc nhiều endpoint bắt frontend phải ghép |

> SRS line 1164:
> | AC-41 | Client được phép đọc một StoryRun; một số resource có thể thuộc owner/module khác | Client gọi `GET /v1/story-runs/{id}` | Một StoryRunDetailV1 tổng hợp status, timeline, scene, job-safe error, permitted assets và quota qua owner ports; không cross-schema SQL, không fan-out phía frontend, không rò prompt/transcript/profile support/foreign-scope existence, không có read-model table | §9.5–§9.7; §22.4; NFR-05/10 |

> SRS line 1811:
> `GET /v1/story-runs/{id}` trả StoryRunDetailV1 tổng hợp để frontend không gọi nhiều endpoint theo từng module. Application read composer đọc Story làm gốc, gọi AI Jobs lấy stage/job status theo target, Core lấy asset/playback readiness, Lesson kiểm occurrence/assignment khi Teacher, và Billing trả quota summary khi được phép. Response có scene/generation status, current input/script/generation refs, error code an toàn, current authorization và playback ref ngắn hạn nếu đủ quyền. Không trả prompt/provider payload, transcript thô, profile support note, revision ẩn, hay tồn tại resource ngoài scope. Không lưu read-model table hay duplicate mutable state; endpoint dùng cursor/version để cache an toàn và ETag.

**D-214 disposition:** Option A. Extend the existing owner-scoped GET /v1/story-runs/{id} with only an owner-approved lifecycle projection; add no second read route.
**Effect:** Only fields and evidence that meet the existing aggregated StoryRunDetailV1 contract may be exposed.
**Remaining open point:** Exact fields, authorization, completion predicate, and response-schema compatibility remain open. Never report DELETED from access denial.
**Status:** ANSWERED BY D-214.

## Q-FENCE — Acceptance-time access and worker fence

**Question:** Which mechanism prevents access, dispatch, and late results after lifecycle acceptance?

**Canonical SRS basis:**
> SRS line 1676:
> | POST /v1/story-runs/{id}/playback-token | Actor của run được phân quyền hiện tại | Artifact hiện tại ở VIDEO_READY, đã qua kiểm tra; kiểm tra assignment/scope hiện tại | 200 playback token thời hạn ngắn, giới hạn vào một asset; run active đến complete, idle closeout hoặc cancel |

> SRS line 1797:
> - Hủy run chưa hoàn tất chuyển run sang DELETE_PENDING và giải phóng khóa active trong transaction ghi nhận lệnh. Ghi `StoryRunCancellationRequestedV1`, tạo lifecycle request, thu hồi playback/upload và yêu cầu hủy job đang chờ/chạy. Worker kiểm tra cancellation trước stage tốn tài nguyên và trước khi nhận kết quả; nếu không ngắt được provider, output đến muộn là stale, không playable và bị xóa qua lifecycle. Giữ quota usage đã nhận và sample claim Teacher thành công.

**D-214 disposition:** Option A. Owner modules validate a shared lifecycle version/fence at each access and worker boundary.
**Effect:** Race evidence is required at every API, download, playback, cache/stream, in-flight upload, job dispatch, and late-result boundary; provider cancellation is best-effort.
**Remaining open point:** The versioned cross-module fence, owner evidence, and race contract remain to be designed and reviewed.
**Status:** ANSWERED BY D-214.

## Q-PURGE — Owner acknowledgements and shared-reference closure

**Question:** What proves run-owned purge and safe retention of shared assets?

**Canonical SRS basis:**
> SRS line 1473:
> | Luồng thay thế | Thất bại xóa object hiện tại được retry idempotent và trạng thái vẫn pending; giữ asset dùng chung đến khi đối soát các tham chiếu được phép khác; Teacher cũ sau reassignment không còn quyền xóa, Teacher phụ trách mới được xử lý theo policy lifecycle |

> SRS line 2144:
> 3. Giữ deletion request pending đến khi đối soát object refs bắt buộc; retry idempotent.

> SRS line 2146:
> 5. Đưa trường hợp reference dùng chung chưa rõ lên owner review; không purge source có thể vẫn được lưu giữ.

**D-214 disposition:** Option A. Use owner-module acknowledgements, reference closure, and idempotent retry.
**Effect:** Core reference-closure and storage-ownership contracts are missing and block implementation. Preserve an asset until an independent valid reference is positively reconciled.
**Remaining open point:** Core must supply a reviewed ownership/reference contract and positive completion evidence; provider/backup copies remain unverified.
**Status:** ANSWERED BY D-214.

## Q-WORKFLOW — Durable lifecycle workflow records

**Question:** Which records represent request acceptance, owner work, retry, reconciliation, and verified completion?

**Canonical SRS basis:**
> SRS line 1523:
> | Dữ liệu/yêu cầu | story.runs; be1.data_lifecycle_requests; ai_jobs.cancellation_notice; core.asset_metadata/lineage; FR-C-08, BR-26, BR-40 |

**D-214 disposition:** Option B, narrowed to a DTR delta. Start from the tables already named by the SRS and add only missing Parent scope, per-owner acknowledgements, retry, and verified-completion evidence.
**Effect:** Do not add a public StoryRun state and do not reuse AiJob state as purge state.
**Remaining open point:** The DTR/schema delta and phase-to-record map require a separate review and approval.
**Status:** ANSWERED BY D-214.

## Q-AUDIT — Audit fields, readers, and retention

**Question:** Which audit fields, readers, Parent scope, and record-specific retention durations are allowed?

**Canonical SRS basis:**
> SRS line 2758:
> 17. **Audit metadata/retention — PARTIAL.** Audit is metadata-only and excludes raw child media/content. Retention targets are 180 or 365 days by record type; exact type-to-duration map, field allowlist, audit authorization and physical mapping remain OPEN-TECHNICAL. Ảnh hưởng: NFR-34/36, data dictionary/physical ERD gate.

> SRS line 2996:
> | O-17 | Audit is metadata-only; retention target is 180 or 365 days by record type. | Type-to-duration mapping, field allowlist, audit authorization and physical schema remain open. |

**D-214 disposition:** Option A. Approve a field, reader, scope, and retention matrix in the DTR before any dependent audit write or read.
**Effect:** The audit remains metadata-only; raw child content is excluded.
**Remaining open point:** The 180/365-day type map, field allowlist, reader authorization, and physical mapping remain OPEN-TECHNICAL.
**Status:** ANSWERED BY D-214.

## Q-BASE — Implementation base and CONV-1 sequence

**Question:** Which exact branch and commit should be the implementation base after CONV-1 is confirmed?

**Canonical SRS basis:**
The SRS defines the product phase sequence below but does not select a repository branch, commit, or merge base.
> SRS line 667:
> | P1 — Parent vertical slice | Parent profile → ảnh/ý tưởng → subject/activity/context review → story review → video Modal → playback/delete, trên dữ liệu tổng hợp | FR-P, FR-AI, subset FR-C/NFR, resumable media upload | Không dùng dữ liệu trẻ thật; quota fixture/config được cấp từ Billing |

> SRS line 668:
> | P2 — Teacher vertical slice | Organization/class/roster → profile → lesson import/review → occurrence/one child sample → script confirmation → video/chiếu/reassignment | FR-T, shared FR-AI/FR-C | Một child/activity/run; không classroom collaboration/batch |

**D-214 disposition:** Option B. FR-C-08 code is cut from the tip of the local, never-pushed branch feature/feat066-conv1 (commit 2dddc607 or later, parent 08439b22), after the owner confirms CONV-1, and the shared paths are re-pinned at that base. The exact commit is named when the base is fixed.
**Effect:** D-214 records the CONV-1 decision, approval entry, and implementation evidence on the local branch, not in the root checkout.
**Remaining open point:** The exact commit and the relationship of the uncommitted D-214 working-tree record to that base must be pinned before any implementation approval.
**Status:** ANSWERED BY D-214.

## Q-M2-GATE — M2 closure coordination gate

**Question:** Does the accepted M2 closure satisfy D-208 item 8's separate baseline-reconciliation gate?

**Canonical SRS basis:**
The SRS does not define the D-208 M2 baseline-reconciliation gate. The following line identifies FR-C-08 as a product requirement only.
> SRS line 2339:
> | FR-C-08 | M | BR-26/40 | UC-07/11 | story.runs; story.video_generations; be1.data_lifecycle_requests; core.asset_metadata; billing.video_quota_usage; lesson.occurrences | Cancel/delete GWT: lock release, asset purge, quota ledger and sample tombstone retained. AC-13/23. | P0; lifecycle as shared Parent/Teacher slice | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |

**D-214 disposition:** Option A. The owner-accepted M2 closure and limitation ledger (approvals/TASK_APPROVAL.md lines 3243-3247; status/STATUS.md line 876) satisfy D-208 item 8. Line 873 of the status file is a stale snapshot that predates the owner acceptance.
**Effect:** M2 approvals, allowlists, command ceilings, and evidence do not transfer to FR-C-08. Re-pin the FR-C-08 baseline at the selected base.
**Remaining open point:** Only the exact FR-C-08 base pins remain to be established; no M2 authority transfers.
**Status:** ANSWERED BY D-214.

## Q-OWNERS — Named accountable module owners

**Question:** Which named people accept each module's launch accountability, and where is the assignment recorded?

**Canonical SRS basis:**
The SRS identifies the authorized actor and product scope; named-person accountability is a D-208 governance gate, not an SRS field.
> SRS line 1469:
> | Actor chính | Chủ sở hữu Parent hoặc Teacher hiện đang được phân công phụ trách lớp; creator cũ chỉ còn provenance |

> SRS line 2339:
> | FR-C-08 | M | BR-26/40 | UC-07/11 | story.runs; story.video_generations; be1.data_lifecycle_requests; core.asset_metadata; billing.video_quota_usage; lesson.occurrences | Cancel/delete GWT: lock release, asset purge, quota ledger and sample tombstone retained. AC-13/23. | P0; lifecycle as shared Parent/Teacher slice | DRAFT; nguồn Q/BR là quyết định đã chốt khi có dẫn chiếu; chưa sign-off |

**D-214 disposition:** Option A selected. Assign named owners for BE1 coordination, Story state/event, Core Asset reference/deletion, AI Jobs, Lesson claim preservation, and HTTP/evidence.
**Effect:** The selected requirement is to assign names, but none have been supplied. Launch remains blocked until every responsibility has a named owner.
**Remaining open point:** OPEN: names and the record location are still missing.
**Status:** OPEN — selected option recorded; names and record location remain outstanding.

## Non-transfer and approval boundary

These dispositions are planning inputs. The SRS remains unsigned. The separate SRS wording revision, DTR/schema review, Core reference-closure contract, exact implementation base, owner names, implementation allowlist review, formal Task Approval, and direct launch instruction remain separate gates. No approval or launch is recorded here.
