# Task approval

## Plan Rev52 — reconcile SRS review findings

- **Status:** APPROVED for the exact documentation-only scope in Plan Rev52; the SRS and Data Table Register remain unsigned drafts.
- **Approver:** Project owner, direct request on 2026-11-06: “đọc cái này và fix lại các cái mâu thuẫn, có thể hỏi 1 vài câu nếu cần”.
- **Recorded date:** 2026-11-06, Asia/Saigon.
- **Plan:** `plan/PLAN_REV52_SRS_CONTRADICTION_RECONCILIATION_20261106.md`.
- **Plan SHA-256 at authorization:** `2EEBB0290B6A15C09135F2A7CB40A0D68DDC5CA8DFBE34CFA390F6428B747ABA`.
- **Current reviewed plan SHA-256:** `CFA2214E1F1F4E02DDABA2D4952052D26493E0844CE0487A3108505BA14B06BF`.
- **Scope:** correct only contradictions supported by current FEAT-063 requirements; update the v2.6-draft SRS/Register pair, evidence dispositions, and authority/tracking records. Keep open policy/schema items open unless the owner answers them.
- **Not approved:** product implementation, schema/migration changes, tests/builds, production/provider/runtime operations, SRS sign-off, or commit/push.
- **Approval basis:** direct owner request; this approves the scoped documentation review and does not provide answers to pending product questions.

- Status: APPROVED for documentation-only SRS diagrams and detailed system-flow PDFs under plan revision 22: maintain one editable multi-page `.drawio` source, refresh the full-package PDF, and create a separate flow-only PDF at the owner-requested destination. Product implementation is not approved.
- Approver: Project owner, direct 2026-10-27 request for a complete diagram package/PDF and subsequent direct request for an additional detailed PDF covering all system flows, superseding the earlier wait-for-Markdown-review gate for these outputs. This approves artifact creation only; it does not represent sign-off of the SRS/register content or product implementation.
- Feature: FEAT-063 - Whole-repository architecture redesign.
- Plan revision: 22.
- Approved plan SHA-256: `F8B37EB7160680B64107726E3699EFAEAD609132BC304E6928346164B7C9A0D8`.
- Approved scope: maintain exactly one editable multi-page Draw.io master in `owner-selected local document directory`, refresh the complete matching SRS/architecture PDF, and create a separate detailed flow-only PDF from named pages in the same master. Cover all detailed product, AI/media, teacher/parent, organization, content, billing/quota, notification, lifecycle, operations and migration flows specified by SRS v2.0-draft, including main paths and alternate/failure branches. Keep all output monochrome, legible, unclipped and visually inspected. The master retains Context, Use Case, Parent/Teacher Screen Flow, Conceptual Data Model, complete logical ERD for all 78 active target tables, separate legacy inventory, System Architecture, Package, Class, Sequence, Activity, State, Deployment, Component/Data-Flow and trust-boundary views. Use the supplied project-document references and authoritative SRS/UML/architecture sources. The current data target remains 38 retained/refactored + 40 new = 78 active, plus 48 read-only legacy = 126 projected physical, based on repository declarations only.
- Explicitly not approved: sign-off of SRS/Data Table Register content, product code/schema or database changes, migrations, product tests/builds, provider/payment/Modal calls, deployment or real-child data.
- Excluded scope: product source code, database schema/migrations or live DB access; product tests/builds/benchmarks; provider, payment or Modal execution; deployment; real-child data; destructive changes; Git commit/push.
- Approval basis: direct user requests to produce a complete Draw.io/PDF package and an additional comprehensive operational-flows PDF in the specified folder; prior owner answers through Q144; and the updated documentation-only plan revision 22. The request authorizes only these document artifacts, not Markdown content approval or product implementation.
- Implementation gate: any product source/schema work requires a separate exact-scope plan and approval record.

## Plan revision 23 — Parent text starter and SRS source correction

- Status: APPROVED for this documentation amendment only; the complete SRS and Data Table Register remain drafts and are not owner-signed.
- Approver: Project owner, direct instruction in the 2026-10-28 conversation to correct the source to FEAT-063, update the full SRS, and remove stale duplicates where practical.
- Recorded date: 2026-10-28, Asia/Saigon (the conversation provides no more precise approval timestamp).
- Approved plan: `plan/PLAN_REV23_PARENT_SKETCH_IDEA_AMENDMENT_20261028.md`.
- Plan SHA-256: `1DD143F19BD37C5736865A4CB045F646E58917C979B465C28EA6738B8B594BE8`.
- Approved scope: SRS v2.1 documentation update for Q145's optional Parent text idea starter; keep Teacher's occurrence-wide AI Sketch Deck as a main-flow step; mark the former FEAT-062 Q-01–Q-07 draft as superseded and redirect it to FEAT-063.
- Explicitly not included: Parent AI-generated line-sketch guide from open Q146. It remains a proposal until the owner decides; no product code, provider call, schema change, or implementation is approved.

## Plan revision 24 — optional Parent AI line-sketch guide

- Status: APPROVED for the documentation amendment described below; full SRS/Data Table Register sign-off and product implementation remain unapproved.
- Approver: Project owner, direct clarification on 2026-10-28 that the Parent option is an AI-generated visual line-sketch guide (for example, a butterfly), following the earlier request to add the sketch suggestion as an optional step.
- Recorded date: 2026-10-28, Asia/Saigon.
- Approved plan: `plan/PLAN_REV24_PARENT_AI_LINE_SKETCH_20261028.md`.
- Plan SHA-256: `59B5CBAAC46AAD60C482B633C43324D6E509BE940CDF0904E6E961E5F72CFF27`.
- Approved scope: update FEAT-063's full SRS and Data Table Register to replace the interim text-only Parent starter with an optional AI-generated 3–5-step line-sketch guide; preserve skip/non-blocking behavior, generic topic/difficulty input only, no child profile/voice/photo/artwork to the generator, private temporary output with provenance/cleanup, separate sketch compute/rate caps outside video quota, and Teacher's occurrence-wide deck as a main-flow step. Reconcile architecture/decision/context/status/evidence/source records and retire Q146 as open.
- Explicitly not approved: product source/UI/backend code, database migration/live access, provider/model execution, generated images, tests/builds/benchmarks, deployment, real-child data, SRS/Data Table Register sign-off, exact production cost/rate values or final retention duration, or Git commit/push.
- Supersession: this revision clarifies the Parent guide's visual AI form. Plan revision 23 remains historical for the FEAT-063 source correction and FEAT-062 retirement; its interim text-only Parent starter scope is superseded by revision 24.

## Plan revision 25 — platform lesson library and cross-role sharing

- Status: APPROVED for this documentation-only architecture/SRS amendment; SRS/Data Table Register content sign-off and product implementation remain unapproved.
- Approver: Project owner, direct 2026-10-28 request to extend the system into a platform and the owner's 49 follow-up answers specifying roles, lesson library, sharing, authoring/filtering, Parent feedback, child media, video behavior, quotas and preserved flows.
- Recorded date: 2026-10-28, Asia/Saigon.
- Approved plan: plan/PLAN_REV25_PLATFORM_LESSON_LIBRARY_AND_SHARING_20261028.md.
- Plan SHA-256: 90EDB84AE60864740A64863423F7F9C72052AFE757ED7427360FC6A29D8AB621.
- Approved scope: update FEAT-063's full SRS, Data Table Register and architecture records additively for a Vietnamese-first lesson platform for ages 3–10; distinct platform Admin/school Manager/Teacher/Parent roles; one school per organization; invite-based, scoped and revocable Parent–Teacher child-profile sharing; reusable/versioned lessons with private/school/selected/public visibility and Manager review before Public; structured lesson authoring plus filtered uploads; draft-only AI assistance; optional in-session line-sketch generation; Parent access to delivered/public lessons and school-scoped feedback; quota scopes; and the revised order that places configured outdoor activities after video generation. Preserve existing Parent and Teacher flows, the child-specific image-to-video pipeline and historical records. Add data entities only where required and update cross-document counts/provenance.
- Explicitly not approved: product source/UI/backend code, API implementation, database schema/migrations or live DB access, provider/model execution or selection, generated assets, product tests/builds/benchmarks, deployment, real-child processing, SRS/Data Table Register sign-off, destructive changes, or Git commit/push.
- Approval basis: direct owner request and answers 1–49 in the 2026-10-28 conversation; exact documentation scope and acceptance criteria in plan revision 25. This approval does not decide the plan's listed open questions; those must remain explicit in the draft.

## Plan revision 30 - local Docker, MinIO, and lesson-source storage example

- Status: APPROVED for the exact local infrastructure and storage-example scope below. This does not approve the full Lesson Library API implementation from Rev29.
- Approver: Project owner, direct instruction in the 2026-10-28 conversation: set up Docker for the backend, use MinIO first with an environment path to AWS S3 later, prepare the environment configuration for the owner to edit, and make one example first.
- Recorded timestamp: 2026-10-28 22:21:18 Asia/Saigon.
- Feature: FEAT-063 - whole-repository architecture redesign.
- Approved plan: plan/PLAN_REV30_LOCAL_DOCKER_MINIO_STORAGE_EXAMPLE_20261028.md.
- Approved plan SHA-256: F6BD755CBC543374AC9091BB7603C2A9EB83DC20F2EDCA92B2A10158AB88C794.
- Approved scope: add the backend API to local Docker Compose with private MinIO and local bucket initialization; provide placeholder-only environment templates, a provider-neutral storage port with a Boto3 S3-compatible adapter, and local-only lesson-source upload/read/delete example endpoints; document the local workflow and future AWS S3/IAM configuration. Use generated object IDs, a bounded upload size and backend-mediated reads. Preserve the existing Compose services and volumes.
- Explicitly not approved: full Rev29 Lesson Library CRUD/sharing/review implementation, database schema/migrations, authentication or production authorization work, document parsing/OCR/AI, malware scanning/production retention, AWS account access/credentials, deployment, tests/builds/security validation, real child data, running the Compose stack, commit/push, or changes to actual .env/secret files.
- Approval basis: the direct user instruction above and the exact scope/acceptance criteria in Rev30. Older approval exclusions remain applicable outside this narrow Rev30 scope.
## Plan revision 31 - Lesson Library APIs and system API inventory

- Status: APPROVED for implementation of the exact Rev31 scope below.
- Approver: Project owner, direct instruction on 2026-10-28 to proceed with implementation, provide a complete API inventory, and adapt existing APIs where required for FEAT-063.
- Recorded timestamp: 2026-10-28 22:41:33 Asia/Saigon.
- Feature: FEAT-063 - whole-repository architecture redesign.
- Approved plan: plan/PLAN_REV31_LESSON_LIBRARY_API_IMPLEMENTATION_AND_INVENTORY_20261028.md.
- Approved plan SHA-256: BC948B27F5CFADD05EC6D12B0B7D989241CDEB6FC3CA6CAB1521988C712BBB8C.
- Approved scope: implement the 28 no-AI Lesson Library API operations in the Rev29 contract; add additive migrations and persistence as required by static source inventory; use verified identity and tenant-scoped authorization; implement private resumable source-document upload through the existing S3-compatible port; mount the APIs in the default app; audit existing route declarations and compositions; revise only legacy APIs with a demonstrated FEAT-063 conflict; produce a complete route inventory; update FEAT-063 records and source registers.
- Explicitly excluded: AI generation/parsing/OCR, production AI providers, frontend changes, live database access/migration, actual .env or secrets, AWS account access, Docker execution, tests/builds/security validation, real child data, deployment, commit and push.
- Approval basis: the owner's direct instruction above, applied to the exact scope and acceptance criteria of the approved Rev31 plan.

## Plan revision 31 - addendum A: upload lifecycle and API inventory

- Status: APPROVED as an additive implementation scope under Plan Rev31.
- Approver: Project owner, same 2026-10-28 direct instruction to proceed, provide the full system API list, and revise existing APIs where necessary for FEAT-063.
- Recorded date: 2026-10-28, Asia/Saigon.
- Feature: FEAT-063 - whole-repository architecture redesign.
- Approved plan: `plan/PLAN_REV31_ADDENDUM_A_UPLOAD_LIFECYCLE_AND_API_INVENTORY_20261028.md`.
- Approved plan SHA-256: `570BC65BE74A82261EC2455147EAF33FB0575B166B73EF506084BBF07A62727D`.
- Approved scope: add owner-scoped upload-session GET/resume and DELETE/abort operations; reconcile synchronous upload completion to `READY_FOR_REVIEW`; recalculate derived Lesson visibility from live grants; and document every current backend route declaration and its mounting status.
- Explicitly excluded: tests/builds, Docker execution, database access/migration, repository security validation, live credentials, AWS, deployment, real child data, commit and push.
- Approval basis: direct owner authorization for the parent Rev31 implementation and the exact additive scope/acceptance criteria in this hash-identified addendum.

## Plan revision 32 - complete API purpose catalog

- Status: APPROVED for the documentation-only API purpose catalog below.
- Approver: Project owner, direct instruction on 2026-10-28: "list all APIs currently in the system and what they are used for".
- Recorded timestamp: 2026-10-28 23:22:46 Asia/Saigon.
- Feature: FEAT-063 - whole-repository architecture redesign.
- Approved plan: `plan/PLAN_REV32_API_PURPOSE_CATALOG_20261028.md`.
- Approved plan SHA-256: `FD189D3E2684CE2930624AFD7412C54F9BB53339209790F7B319B534C41E087C`.
- Approved scope: add a distinct purpose and runtime-exposure classification to every declared API method/path in the Rev31 route inventory; retain source handlers; document generated docs routes and broader FEAT-063 API requirements not yet implemented. No runtime API changes.
- Explicitly excluded: code/API/schema/migration changes, tests/builds, Docker/runtime/database/provider/AWS operations, security validation, deployment, real child data, commit and push.
- Approval basis: the owner's direct request above, applied to the exact documentation-only scope and acceptance criteria in Plan Rev32.

## Plan revision 33 - non-AI API workflow tests and local database migration

- Status: APPROVED for the exact local verification scope below.
- Approver: Project owner, direct instruction on 2026-10-29 to run API workflow tests, apply the database migration, and skip AI-related APIs.
- Recorded date: 2026-10-29, Asia/Saigon.
- Feature: FEAT-063 - whole-repository architecture redesign.
- Approved plan: `plan/PLAN_REV33_NON_AI_API_TESTS_AND_LOCAL_MIGRATION_20261029.md`.
- Approved plan SHA-256: `513FEE246CF1DD2B062BE146996C362C7C726667A9529E0E2342962084CF4DE1`.
- Approved scope: verify the local Compose PostgreSQL target; apply the Lesson Library Alembic target and its declared BE1 prerequisite to the local application database; create a disposable `be1_acceptance` database for synthetic HTTP integration tests; exercise local MinIO storage and non-AI Lesson Library CRUD, upload, review/publication, sharing/Parent access, and Platform Admin moderation; record feature-local evidence.
- Explicitly excluded: AI/model/line-sketch/ASR/vision/video endpoints, Modal/GPU/provider calls, external Firebase/AWS access, remote or production databases, actual `.env` edits, real child data, resetting the application database, deployment, commit, and push.
- Supersession: this direct approval supersedes Rev31's test/database-migration exclusion only for the exact local verification above. The existing application database remains persistent and is migrated additively; only the disposable test database created for this run may be dropped.

## Plan revision 34 — legacy non-AI API regression run

- Status: APPROVED for the exact test-only scope below.
- Approver: Project owner, direct instruction on 2026-10-29 to rerun all old APIs except AI-related APIs and report failures.
- Recorded date: 2026-10-29, Asia/Saigon.
- Feature: FEAT-063 - whole-repository architecture redesign.
- Approved plan: `plan/PLAN_REV34_LEGACY_NON_AI_API_REGRESSION_20261029.md`.
- Approved plan SHA-256: `308F4FEA6576BAB08ACCD86B62616FE463C94D099FC27EBF301E855C4756F5B1`.
- Approved scope: rerun existing non-AI HTTP/API regression suites and make safe dispatch-smoke requests to each active pre-Lesson-Library BE1/classroom and Demo/local-flow method/path; use synthetic data and a disposable local `be1_acceptance` database; record pass/fail/excluded/uncovered route coverage in EV-063-27.
- Explicitly excluded: AI-related API/provider/Modal/GPU calls, Lesson Library re-test, real MinIO deployment, persistent application-DB writes/migrations, remote services, real child data, product-code/test-expectation changes, deployment, commit, and push.

## Plan revision 35 — UI screen mockups and motion notes

- Status: APPROVED for generated visual drafts and feature-local documentation only.
- Approver: Project owner, direct request on 2026-10-30 to create images of different UI screens based on the current APIs/SRS, put each screen in a separate folder, and document needed animation.
- Recorded timestamp: 2026-10-30 00:19:19 Asia/Saigon.
- Feature: FEAT-063 - whole-repository architecture redesign.
- Approved plan: `plan/PLAN_REV35_UI_SCREEN_MOCKUPS_AND_MOTION_NOTES_20261030.md`.
- Approved plan SHA-256: `0EBBE2D7E983663F448B167F39FE42AD6C89A2E38EE5390A054673FC2C42723C`.
- Approved scope: generate the 14 Parent, Teacher, School Manager and Platform Admin screen drafts listed in Plan Rev35, each with its own PNG, prompt and motion note under `assets/generated/ui-mockups-rev35-20261030/`; inspect outputs and update feature-local context, source, status and evidence.
- Acceptance criteria: AC1–AC6 in the hash-identified Plan Rev35.
- Explicitly excluded: frontend/product implementation, API/schema/database changes, executable animation, provider/model API calls, tests/builds, deployment, real child data, Git commit/push, and promotion into `assets/approved/` or `assets/applied/` before visual approval.
- Approval basis: the owner's direct request applies to this plan's screen inventory, draft-only output location and acceptance criteria.

## Plan revision 36 — UI component patterns and interaction states

- Status: APPROVED for generated visual drafts and feature-local documentation only.
- Approver: Project owner, direct request on 2026-10-30 to add modal, toast and other SRS-required UI samples in FEAT-063.
- Recorded timestamp: 2026-10-30 02:37:54 Asia/Saigon.
- Feature: FEAT-063 - whole-repository architecture redesign.
- Approved plan: `plan/PLAN_REV36_UI_COMPONENT_PATTERNS_AND_STATES_20261030.md`.
- Approved plan SHA-256: `300104684514C4C6F67614F58DDE402668AAC24AF2204F9B1BCA7A5BBEA2D336`.
- Approved scope: generate nine component/state boards listed in Plan Rev36, each with its own image, prompt brief and motion note under `assets/generated/ui-components-rev36-20261030/`; map each group to SRS/API boundaries and update feature-local context, decisions, status, source register and evidence.
- Acceptance criteria: AC1–AC7 in the hash-identified Plan Rev36.
- Explicitly excluded: frontend/component implementation, API/schema/database changes, executable animation, provider/model calls, tests/builds, deployment, real child data, Git commit/push, and promotion into `assets/approved/` or `assets/applied/` before visual approval.
- Approval basis: the owner's direct request applies to the exact plan scope and acceptance criteria above.

## B1 — API crosswalk (backlog B1) and execution plan

- Status: APPROVED for the documentation-only B1 API crosswalk below.
- Approver: Project owner, direct request on 2026-10-30 to draft a concrete B1 step plan and have it executed, producing the API crosswalk after the B0 baseline.
- Recorded timestamp: 2026-10-30 22:50:19 Asia/Saigon.
- Feature: FEAT-063 - whole-repository architecture redesign.
- Approved plan: `plan/B1_API_CROSSWALK_EXECUTION_PLAN_20261030.md`.
- Approved plan SHA-256: `BFD72FB93866E9847F842FF44EA592A9B6A28A7E004DA3574980EC84F8CB2CDB`.
- Approved scope: produce `evidence/B1_API_CROSSWALK_20261030.md` and `.csv` mapping the 135 Rev37 catalog rows plus the target rows from SRS 2.3 §21.2/§9.6 and the FEAT-064 pilot outline to KEEP / MODIFY / LEGACY_HOLD / FIXTURE / NEW_TARGET proposals, with evidence level E0–E3, S1 draft disposition, pilot relevance and blocked-by markers. All dispositions are proposals for owner review.
- Acceptance criteria: the ten checks in §8 of the hash-identified plan. Result files: Markdown SHA-256 `3B3492D46260D16542BDFF1E5FEAE1E87E2D714AFB56A40B54D6AD09AD9CEFB3`, CSV SHA-256 `6D95F1FC485685BC7D615775F5F45FDBED2C2072AAD07534AC7D8FE915E586A2` (commit `9cca8e47`).
- Explicitly excluded: code, API, schema or migration changes; approval-record changes other than this entry; tests/builds; backend, database, MinIO, Modal or GPU operations; resolving the Parent-activity ordering (B2); S1/S2/S3 implementation; deployment; real child data.
- Approval basis: the owner's direct request above, applied to the exact documentation-only scope and acceptance criteria in the B1 plan. This entry records the approval after the work was done; the B1 plan and result files must not change without a new entry.

## B2 — Parent activity ordering crosswalk (backlog B2) and execution plan

- Status: APPROVED for the documentation-only B2 crosswalk below.
- Approver: Project owner, direct instruction on 2026-10-30 to record this approval in TASK_APPROVAL.md and to run B2 after the B1 crosswalk.
- Recorded timestamp: 2026-10-30 23:28:37 Asia/Saigon.
- Feature: FEAT-063 - whole-repository architecture redesign.
- Approved plan: `plan/B2_PARENT_ACTIVITY_ORDER_PLAN_20261030.md`.
- Approved plan SHA-256: `AAD0459FAA7FE7BF053198FEC41CA13CB713F3D5774AC83546B3793862E47A1F`.
- Approved scope: inventory every SRS 2.3 / Data Table Register / decision passage about when a Parent receives outdoor activities, classify each as POST_VIDEO, PRE_VIDEO, TEACHER_PRE_VIDEO or NEUTRAL, lay out the options with their effects on API, schema, state machine, UI, acceptance criteria and pipeline, and record a proposal plus owner questions in `evidence/B2_PARENT_ACTIVITY_ORDER_CROSSWALK_20261030.md` (optionally with an inventory CSV). Include an appendix stating which of the 16 B1 rows blocked by B2 each option would unblock, without editing the B1 files.
- Acceptance criteria: the six checks in section 6 of the hash-identified plan.
- Explicitly excluded: editing the SRS, Data Table Register, ADRs, DECISIONS, B0/B1 files or any approval record other than this entry; choosing an option on the owner's behalf; code, API, schema or migration changes; tests/builds; backend, database, MinIO, Modal or GPU operations; S1/S2/S3 implementation; deployment; real child data.
- Approval basis: the owner's direct instruction above, applied to the exact documentation-only scope and acceptance criteria in the B2 plan. This entry is recorded before the work; the B2 plan must not change without a new entry.

## B3 — Ownership, shared-file and migration-order manifest (backlog B3) and execution plan

- Status: APPROVED for the documentation-only B3 manifest below.
- Approver: Project owner, direct instruction on 2026-10-31 to plan B3 and have it executed after B2.
- Recorded timestamp: 2026-10-31 00:29:22 Asia/Saigon.
- Feature: FEAT-063 - whole-repository architecture redesign.
- Approved plan: `plan/B3_OWNERSHIP_MANIFEST_PLAN_20261031.md`.
- Approved plan SHA-256: `1523AADBEB8B664D6CE5324B2E5F4D6D4085DF9EC71A4D3C72A9FC827FF26514`.
- Approved scope: produce `evidence/B3_OWNERSHIP_MIGRATION_MANIFEST_20261031.md` and `evidence/B3_OWNER_MATRIX_20261031.csv` covering the 18 boundaries of the FEAT-064 owner path draft, the ADR-0015 versus D-07/D-08 role differences, the files shared by FEAT-064 and Rev36 S1-S3 with one proposed writer each, a read-only Alembic graph with migration-order options, the comparison of the synthetic-origin representations, the approval gate table and up to 8 owner questions. All entries are proposals; every co-signature stays unsigned.
- Acceptance criteria: the seven checks in section 6 of the hash-identified plan.
- Explicitly excluded: code, API, schema or migration changes or creation; applying or merging Alembic heads; editing the SRS, register, ADRs, DECISIONS, approval records other than this entry, or the FEAT-064, Rev36, B0, B1 and B2 files; choosing roles, writers, migration options or signatures on the owner's behalf; tests/builds; backend, database, MinIO, Modal or GPU operations; deployment; real child data.
- Approval basis: the owner's direct instruction above, applied to the exact documentation-only scope and acceptance criteria in the B3 plan. This entry is recorded before the work; the B3 plan must not change without a new entry.

## B0b — chấp nhận giới hạn PARTIAL

- **Status:** APPROVED — chỉ ghi nhận giới hạn của B0b; không xác minh lại nhãn runtime.
- **Approver:** Project owner / Person 2 (AnhKhoaa157).
- **Recorded date:** 2026-10-31, Asia/Saigon.
- **Chỉ thị trực tiếp của owner:** “Owner CHẤP NHẬN B0b ở mức PARTIAL (Pha 0). Owner không chờ hai file EV-063-30.”
- **Kết quả được ghi nhận:** B0a hoàn thành. B0b ở mức PARTIAL vì `EV-063-30_openapi-local-compose-20261030.json` và `EV-063-30_API_CONTRACT_AND_FULL_STACK_VERIFICATION_20261030.md` không tìm thấy. Lượt tìm thứ nhất không tìm thấy chúng trong các vị trí local đã quét, 66 ref Git và lịch sử. Lượt thứ hai, sau fetch/prune, cũng không thấy trong 68 ref, lịch sử, 6 stash, toàn bộ thư mục người dùng và ổ D; GitHub code search không đủ mạnh để kết luận file không tồn tại. Kết luận đúng là không có hai file trong máy/remote đã biết; có thể chúng nằm ở máy hoặc nơi lưu của người tạo catalog, nhưng không kết luận chúng không tồn tại.
- **Giới hạn:** Các nhãn runtime PASS/BLOCKED/NOT RUN trong catalog Rev37 không được coi là đã xác minh. B0b có thể mở lại nếu chủ Rev37 gửi hai file nguồn. Không tạo snapshot runtime mới; việc đó cần scope và approval riêng. B0b ở mức PARTIAL không chặn B1.
- **Nguồn ghim:** `evidence/B0_CLOSEOUT_20261030.md`; SHA-256 `452B5C4C7FEDCF0D43C09DBA157BED6D93CA10AAA2EDEF0F9B251525DDE0026F`.
- **Phạm vi bị loại trừ:** Không sửa B0 closeout, backlog, báo cáo B0 cũ, API, code, test hoặc runtime; không xác nhận chất lượng hay hành vi Rev37.

## B2A — SRS/register amendment, Parent activity order A

- **Status:** APPROVED — áp dụng toàn bộ 45 thao tác M001–M045 loại A hoặc B trong đúng rev2; không có thao tác loại C.
- **Approver:** Project owner / Person 2.
- **Recorded date:** 2026-10-31, Asia/Saigon.
- **Chỉ thị trực tiếp của owner:** “Duyệt B2A rev2 ED75E7B53B03E01B + B1”.
- **Approved plan:** plan/B2A_SRS_REGISTER_AMENDMENT_PLAN_REV2_20261031.md; SHA-256 ED75E7B53B03E01B10CC2391107D1D53173176820585CBE8544E7CBC0A2148A7.
- **Quyết định:** Các đề xuất logic tại §4.1–§4.3 của đúng rev2 được owner chấp nhận và trở thành quyết định cho phạm vi B2A này. Không suy diễn thành tên bảng/cột/FK/migration.
- **Thu hồi phân công:** bản ghi phân công đã được owner thu hồi sau khi rev2 được viết; dòng 77 của rev2 không còn đúng. Bản ghi phân công đã bị xóa khỏi working tree và mục Pha 1 đã được gỡ khỏi approval; không ghi tên người viết/review.
- **Nguồn baseline ghim:** SRS 7EE8CD8511AF722E33DEA08AEE4A324532A8C4A397230D74DD5632387A1B4F8B; DATA_TABLE_REGISTER BE34CF5475550CF3DF0A8A174E66AEB06B664D9E62FD6AE38216374A5F3BCC0A; ADR-0021 BB4310E9EE006D2E9DDBE0FBCE1ADA138AA1010DF32C2141F2A9BF3B77BD58CA; DECISIONS 9E7822A3567EC569747498EDEB4A50F22E340D7F869F191700396DF5FB41FBA7.
- **B2 evidence ghim:** B2 plan AAD0459FAA7FE7BF053198FEC41CA13CB713F3D5774AC83546B3793862E47A1F; B2 crosswalk A17246115412A2413BE646F9DB8F16E8BC21B12950F792851322E913E3308514; B2 inventory F88D11E3F3348B646D7D1C3399A7555A5E64A3B67C71D083E3606C8C819A4A02.
- **File được phép sửa:** artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md, artifacts/DATA_TABLE_REGISTER.md, docs/adr/ADR-0021-single-child-parent-teacher-story-architecture.md (đúng ba clause M042–M044), và DECISIONS.md (append đúng một entry M045).
- **B1 đi kèm:** riêng 16 dòng T018–T031, T046, T047; chỉ gỡ B2 khỏi blocked_by và cập nhật câu đếm tương ứng trong B1 MD theo C10. E0, pilot=N, disposition và mọi cột khác giữ nguyên; C022–C024 giữ nguyên blocker B4a/B4b. B1 có approval riêng bên dưới trước khi sửa.
- **Bị loại trừ:** code, API implementation, schema, migration, runtime, DB, tests/build, MinIO, Modal/GPU, deployment, Rev36, ADR-0022, các file B0/B1/B2 khác ngoài phạm vi B1 nêu trên, mọi file ngoài danh sách được phép, dữ liệu trẻ thật, commit/push/stage.
- **Approval basis:** chỉ thị trực tiếp của owner ở trên, áp dụng cho đúng hash rev2 và phạm vi đã liệt kê; ghi trước khi sửa nguồn.

## B1 — gỡ B2 khỏi 16 dòng

- **Status:** APPROVED — chỉ gỡ blocker B2 khỏi đúng 16 dòng target và cập nhật hai câu tổng hợp tương ứng trong B1 MD.
- **Approver:** Project owner / Person 2.
- **Recorded date:** 2026-10-31, Asia/Saigon.
- **Chỉ thị trực tiếp của owner:** “Duyệt B2A rev2 ED75E7B53B03E01B + B1”.
- **Approval basis:** C10 trong OWNER_DECISION_SLIP_20261031.md và việc B2A đã được áp dụng theo rev2 có SHA-256 ED75E7B53B03E01B10CC2391107D1D53173176820585CBE8544E7CBC0A2148A7.
- **B1 baseline ghim trước sửa:** CSV SHA-256 6D95F1FC485685BC7D615775F5F45FDBED2C2072AAD07534AC7D8FE915E586A2; MD SHA-256 3B3492D46260D16542BDFF1E5FEAE1E87E2D714AFB56A40B54D6AD09AD9CEFB3.
- **Phạm vi duyệt:** Chỉ cột blocked_by của T018–T031, T046, T047 trong CSV và phần diễn giải/count tương ứng trong B1 MD. Xóa B2; nếu còn blocker khác thì chỉ giữ blocker đó; nếu không còn blocker thì dùng none.
- **Bất biến:** Giữ nguyên 192 data rows; E0, pilot=N, disposition, các cột khác và toàn bộ dòng ngoài danh sách không đổi. C022–C024 giữ nguyên blocked_by=B4a,B4b.
- **Bị loại trừ:** Không sửa B1 evidence/disposition/pilot, không sửa target khác, B2 files, code, schema, migration, test/runtime/DB/provider, không stage/commit/push.

## B1 — C022-C024 chỉ còn B4b

- **Status:** APPROVED cho cập nhật tài liệu giới hạn bên dưới.
- **Approver:** Project owner / Person 2.
- **Recorded date:** 2026-11-01, Asia/Saigon.
- **Chỉ thị trực tiếp:** “B1: C022-C024 chỉ còn B4b (tài liệu).”
- **Phạm vi:** Trong B1 CSV, chỉ đổi `blocked_by` của C022, C023, C024 từ `B4a,B4b` thành `B4b`; trong B1 Markdown, đồng bộ đúng ba dòng này và câu tóm tắt consent operations. B4a là phần code đã hoàn thành trong commit `6910b603`; B4b vẫn là phần còn lại.
- **Hash baseline:** CSV `C231967E28BE4CB6CE1AACEE8031BED6E8B5AA5F9F49A9863949AF2D9A50568F`; Markdown `2CBA141B336DF623D42D81949FE0E66D55EF484A1DBE738054B3736C0818F717`.
- **Bất biến:** Chỉ ba giá trị blocker thay đổi trong CSV; 189 dòng còn lại và mọi cột khác giữ nguyên. Không thay disposition, evidence, pilot hay rationale; không tuyên bố B4b hoàn tất.
- **Ngoài phạm vi:** Code, test, DB, migration, runtime, Modal, commit và push.

## B5 — tương thích idempotency receipt Parent Group (phương án A)

- **Status:** APPROVED cho đúng phạm vi B5 dưới đây theo chỉ thị trực tiếp của owner; chỉ thị này cho phép thực hiện P0–P6 và một commit chung theo ca X/Y.
- **Approver:** Project owner / Person 2 (AnhKhoaa157).
- **Recorded date:** 2026-11-01, Asia/Saigon.
- **Chỉ thị trực tiếp:** “thực hiện toàn bộ file prompt sau, một mạch, không chờ tin nhắn thêm.”
- **Approved plan:** `plan/B5_PARENT_GROUP_RECEIPT_COMPATIBILITY_PLAN_20261031.md`; SHA-256 `6E36A982265F00EA53F33B7E5AC0EFD957F433317ED53A03D5C1AED91813DA79`.
- **Quyết định:** Phương án A, nâng cấp receipt lúc replay mà không ghi lại receipt; `revision_source` là trường response tùy chọn mặc định `None`, với hai giá trị đóng `recorded` và `reconstructed_from_current_row`; chỉ hai operation scope Parent Group xác nhận trong §1 của plan; test PostgreSQL được viết nhưng để skip theo `BE1_TEST_DATABASE_URL`; review độc lập nội bộ.
- **Phạm vi được duyệt:** `POST /organizations/{organization_id}/parent-groups/{group_id}/invitations` và `POST /me/parent-group-invitations/{membership_id}/accept`, cùng pure helper, `_replay` read-time path, offline tests, test tích hợp PostgreSQL đang bị skip, và evidence như allowlist tại §4 của plan.
- **Mốc P0:** Bộ test được chọn đạt 273 passed, 4 skipped; mypy strict có 30 lỗi nền có sẵn trên `service.py` và `contracts/schemas/lesson_library.py`. P6 phải so sánh và chỉ báo lỗi mypy mới.
- **Yêu cầu review:** Rà độc lập nội bộ ở P5: allowlist, fingerprint/409 giữ nguyên, không có ghi trên đường replay, đủ hai scope P1, provenance đúng và contract vẫn yêu cầu `revision`.
- **Bị loại trừ:** Không đọc hoặc thao tác DB/Alembic; không sửa dữ liệu receipt; không chạy PostgreSQL replay test, Modal/GPU/mạng ngoài; không sửa FEAT-064 pilot, route/grant/upload semantics, `_idempotent` write path, bảy file local-only hoặc file ngoài allowlist; không push.
- **Cơ sở approval:** Chỉ thị trực tiếp của owner ở trên, áp dụng cho đúng hash plan này và allowlist đã ghim; không yêu cầu chữ ký/xác nhận của người khác.

## Plan revision 38 — contract-aligned Swagger/OpenAPI

- Status: APPROVED for the exact Swagger/OpenAPI documentation and focused verification scope below.
- Approver: Project owner, direct instruction in the current chat on 2026-10-30 to build Swagger from the provided API contract, avoid omissions, and report errors.
- Feature: FEAT-063 — whole-repository architecture redesign.
- Source contract: owner-supplied `API_CONTRACT_CATALOG_FEAT063_REV37_20261030.md`; SHA-256 `56FC8BEA01360E11F73E45B2D43AC1897540B30BC8AE524CDE1ECEFACFBB1B88`.
- Approved plan: `plan/PLAN_REV38_SWAGGER_OPENAPI_CONTRACT_20261030.md`.
- Approved plan SHA-256: `C1E8C74AD57E7F053E0D1E093BAF7F97BE6F12E8EF8887A2C098632B9B863BCF`.
- Portability note: the original approved hash was `34C97B1428E231089AE7F868C78A17FAD023BEF4483A6201BC349453BF360F56`; only the machine-local source path was normalized to the attachment filename. The contract hash, scope and acceptance criteria are unchanged.
- Approved scope: enrich FastAPI `/docs` and `/openapi.json` with Rev37 purpose, surface, exact request-input and authentication metadata for all 124 mounted operations; verify parameters, request-body presence/media/schema/requiredness, security, response codes/media/schemas and descriptions against the contract; keep all 11 candidate/fixture operations unmounted while recording their exact metadata in `x-unmounted-operations`; document both the declared and observed body-limit 413 payload shapes without changing runtime behavior; export the local-Compose OpenAPI 3.1 snapshot; add focused parity checks and feature-local evidence.
- Explicitly excluded: adding or mounting candidate routes, API behavior/auth/schema changes, database or Docker runtime operations, provider calls, deployment, real child data, commit and push.
- Acceptance criteria: AC1–AC7 in the hash-identified Plan Rev38.
- Approval basis: the owner's direct request applies to the exact scope and acceptance criteria in Plan Rev38.

## Plan revision 39 — professional Swagger navigation and role grouping

- Status: APPROVED for the exact Swagger navigation/tag documentation scope below.
- Approver: Project owner, direct follow-up request in the current chat on 2026-10-30 to organize Swagger by role where appropriate or otherwise make it easier and more professional to navigate.
- Feature: FEAT-063 — whole-repository architecture redesign.
- Source contract: owner-supplied `API_CONTRACT_CATALOG_FEAT063_REV37_20261030.md`; SHA-256 `56FC8BEA01360E11F73E45B2D43AC1897540B30BC8AE524CDE1ECEFACFBB1B88`.
- Approved plan: `plan/PLAN_REV39_SWAGGER_NAVIGATION_ROLE_GROUPING_20261030.md`.
- Approved plan SHA-256: `1E0244E9D43F3F3B46361D66711D413293F2B7E50DB30DEE5B353BAA2474834F`.
- Portability note: the original approved hash was `9497CF00234A567D30F7B0E7A43D96AEA750FED2641478A15CDDEF80DF61E032`; only the machine-local source path was normalized to the attachment filename. The contract hash, scope and acceptance criteria are unchanged.
- Approved scope: create role-based Lesson Library tags only where current guards establish the role; use domain/workflow tags for BE1 and Demo routes whose audience is not explicit; describe each tag; preserve all route, auth, schema and behavior parity; regenerate the local snapshot and restart the local Swagger server.
- Explicitly excluded: API behavior or authorization changes, candidate route mounting, database/Docker/provider/deployment operations, commit and push.
- Acceptance criteria: AC1–AC6 in the hash-identified Plan Rev39.
- Approval basis: the owner's direct request applies to the exact scope and acceptance criteria in Plan Rev39.

## Plan revision 40 — local Swagger QA kit and upload error parity

- Status: APPROVED for the exact local QA and upload-error contract scope below.
- Approver: Project owner, direct `duyệt` in the current chat on 2026-10-30 after the recommendation to fix 413 parity, prepare synthetic test material, add Swagger examples, and run the focused workflow.
- Recorded date: 2026-10-30, Asia/Saigon.
- Feature: FEAT-063 — whole-repository architecture redesign.
- Source contract: owner-supplied `API_CONTRACT_CATALOG_FEAT063_REV37_20261030.md`; SHA-256 `56FC8BEA01360E11F73E45B2D43AC1897540B30BC8AE524CDE1ECEFACFBB1B88`.
- Approved plan: `plan/PLAN_REV40_LOCAL_SWAGGER_QA_KIT_20261030.md`.
- Approved plan SHA-256: `701402BC515745FDCBCFF8C8AF8E7630EDF4025D51C330F7E7747AB6D738E1E9`.
- Portability note: the original approved hash was `10AB1CEB7D26B16345712CD4BED22F5229B331029A96000E59EE73C9DB1758D1`; only the machine-local source path was normalized to the attachment filename. The contract hash, scope and acceptance criteria are unchanged.
- Approved scope: align image/audio middleware 413 bodies and OpenAPI schemas with `MobileWorkflowResultV1`; add an inspectable synthetic PNG and accurate session/image Swagger examples; document and exercise the loopback in-memory demo workflow; run focused contract/parity/export verification; and update FEAT-063 records/evidence.
- Explicitly excluded: route/auth changes or fake-token bypasses, creating Firebase users or credentials, persistent application-database reads/writes, real child data, external AI/Firebase/AWS/remote-provider calls, deployment, commit, and push. Existing disposable integration fixtures may be referenced; any protected API still requires a valid Firebase ID token for Swagger `Try it out`.
- Acceptance criteria: AC1–AC6 in the hash-identified Plan Rev40.
- Approval basis: the owner's direct `duyệt` applies to the exact plan scope and acceptance criteria above.

## Plan revision 41 — Swagger overview presentation

- Status: APPROVED for the exact Swagger overview-copy and local snapshot/restart scope below.
- Approver: Project owner, direct `làm cho đẹp` request in the current chat on 2026-10-30, referring to the attached screenshot of the Swagger overview.
- Recorded date: 2026-10-30, Asia/Saigon.
- Feature: FEAT-063 — whole-repository architecture redesign.
- Approved plan: `plan/PLAN_REV41_SWAGGER_INFO_PRESENTATION_20261030.md`.
- Approved plan SHA-256: `8693C3B4165F9413775306260CCC9023404F2AB7F58C967632236951B1FC2BDB`.
- Approved scope: shorten and structure only the top-level Swagger `info.description`; preserve all API routes, operation groups, schemas, examples, authentication and behavior; regenerate the OpenAPI snapshot and restart/check the loopback docs server.
- Explicitly excluded: custom CSS/theme, route/auth/schema changes, candidate route mounting, database/provider work, credentials, commit, push, and deployment.
- Acceptance criteria: AC1–AC4 in the hash-identified Plan Rev41.
- Approval basis: the owner's direct request applies to the screenshot's overview block and the exact scope and acceptance criteria above.

## Plan revision 42 — review and commit the Swagger update

- Status: APPROVED for the exact local review and commit scope below.
- Approver: Project owner, direct `coi và commit cho tui` request in the current chat on 2026-10-30.
- Recorded date: 2026-10-30, Asia/Saigon.
- Feature: FEAT-063 — whole-repository architecture redesign.
- Approved plan: `plan/PLAN_REV42_SWAGGER_REVIEW_AND_COMMIT_20261030.md`.
- Approved plan SHA-256: `E8A809729BDE4B83D0A6FD0AC21336C8F3721F55B7BDFA7431F1125922D026E8`.
- Approved scope: review the pending Swagger/OpenAPI implementation and related FEAT-063 records/artifacts; run the focused contract, style, compilation, export/snapshot, hash, whitespace and required security checks; stage only that reviewed work; create one local commit on `dev`; and verify the resulting branch and worktree.
- Explicitly excluded: push, deployment, unrelated changes, new route/API behavior outside earlier approved scope, credentials, real child data, and database/provider operations.
- Supersession: this approval supersedes earlier commit exclusions only for the exact reviewed local commit in Plan Rev42; push remains excluded.

## T12-lite — database thử PostgreSQL (phạm vi ghi)

- Status: APPROVED for one disposable local PostgreSQL database, only when its database name contains `be1_acceptance` and the connection target is loopback.
- Approver: Project owner / Person 2 (`AnhKhoaa157`), direct instruction in this chat on 2026-11-01.
- Authorized writes: repository Alembic migrations and rows created by the named T12-lite tests using `synthetic-<uuid>` identifiers or test-owned unique data. No DROP/TRUNCATE, no deletion of non-test data, no other database, and no non-loopback connection.
- Connection provenance: the local ignored file created by the owner; its path and value are intentionally omitted.
- Test scope: `tests/integration/test_be1_postgres_api.py`; `tests/integration/lesson_library/test_lesson_library_api.py`; database-gated tests under `tests/integration/`, including `ai_jobs/`; and the new `tests/integration/test_be1_synthetic_pilot_postgres.py` specified by this task.
- Report actual outcomes even if a phase is NOT RUN. No Modal/GPU or real child data is authorized.

## T2B migration — phạm vi DB (chỉ thị owner 2026-11-01)

- Status: APPROVED cho migration `20261101_be1_age_0001` với parent duy nhất `20261031_be1_se_0001` theo T2B rework plan SHA-256 `959C9AB6739826F6C8AB53EB4AC7C49ACAD8DBDF629E5564291A615B86657DE6`.
- Phạm vi chỉ một database local dùng một lần có tên chứa `be1_acceptance`, kết nối loopback; chỉ migration của repo và hàng test synthetic có tiền tố `synthetic-`/dữ liệu riêng của test. Không DROP/TRUNCATE, không xóa dữ liệu không phải test, không truy cập database khác.
- Cột provenance cũ được backfill `age_revision=1`, `age_source='LEGACY_UNKNOWN'`; không suy nguồn từ định danh hoặc thời gian. Không Modal/GPU, provider từ xa hay dữ liệu thật của trẻ.
- Approval basis: chỉ thị trực tiếp của project owner trong phiên này; không phải chữ ký của chủ sở hữu khác.

## T12-partial (G6) — PostgreSQL acceptance evidence

- Status: APPROVED for the bounded T12-partial checks of already completed synthetic BE1/canvas work; this does not unblock T6, T7a–T7c, T2C, T8, T9, or authorize T13.
- Approver: Project owner / Person 2 (`AnhKhoaa157`), direct instruction in this session to run the G2–G6 goal and the referenced T12 PostgreSQL procedure, 2026-11-01.
- Execution plan/spec pinned for this partial run: `.claude/handoff/CODEX_PROMPT_T12_POSTGRES_RUN_20261101.md`; SHA-256 `055F557F7228E6DA1F74B0D5E3B6497972F19B0A24ED9D20047B7357C506365D`.
- Database boundary: one owner-created disposable local `be1_acceptance` database on loopback. Its identity and PostgreSQL 17.11 version were checked without recording the connection value. No other database is in scope.
- Authorized tests: `tests/integration/test_be1_synthetic_pilot_postgres.py`, `tests/integration/test_be1_age_provenance_postgres.py`, `tests/integration/test_be1_postgres_api.py` except its global retention-worker case, and `tests/integration/lesson_library/test_lesson_library_api.py`. Test-created rows must use synthetic/test-owned identities and be cleaned only by exact ownership. No source/test edits are authorized by this entry.
- Migration boundary: repository Alembic migrations only; the checked database was already at all current heads, so a no-op head check is expected. Downgrade is permitted only for the single BE1 head revision after tests clean up and the explicit synthetic-profile/proof emptiness gate passes. No DROP/TRUNCATE or deletion of non-test rows.
- Excluded: `ai_jobs` PostgreSQL migration cases that create/drop a separate `be2_b2_*` database, live provider/Modal/GPU, real child data, B4b, T13, and any change to application source or migration files.

## Đính chính hash thủ tục T12

- Nguồn: chỉ thị trực tiếp của Project owner / Person 2 (`AnhKhoaa157`) trong phiên ngày 2026-11-01; cho phép tiếp tục lượt chỉ-F2.
- Đính chính hash thủ tục trong mục `T12-partial (G6) — PostgreSQL acceptance evidence` (dòng khoảng 333) và các tham chiếu liên quan từ prompt F2/G6. Hash ghi `055F557F7228E6DA1F74B0D5E3B6497972F19B0A24ED9D20047B7357C506365D` là lỗi chép ký tự cuối.
- Hash SHA-256 thật của thủ tục T12: `055F557F7228E6DA1F74B0D5E3B6497972F19B0A24ED9D20047B7357C5063657`; đã đo lại trong lượt này. Owner xác nhận file thủ tục không đổi từ 2026-10-31 23:24. Nội dung thủ tục không đổi; không sửa mục approval cũ.
- Prompt chỉ-F2 giữ SHA-256 `446AF8ADB92885282B7CAE26F8D2561A1E01911BD2E97B5995E21DD2F614271D`; plan F2 giữ SHA-256 `BDE6D64168B6801E023AB305B3F787D46474152C49DB4779A37DE93BB2DF9AF8`. Cổng hash lệch được ghi trong plan nay được đính chính bởi chỉ thị này; dùng hash thật khi kiểm thủ tục.
- Chỉ mở lại phạm vi F2 đã duyệt: kiểm tra pending consent trước hai patch test-local mới, ba alias tổng cộng, trên database local dùng một lần theo thủ tục. Không mở rộng sửa mã sản phẩm, F1/F3/F4 hoặc phạm vi khác; không stage/commit/push.

## StoryRun-lite S1 → S2 implementation — 2026-11-02

- Status: APPROVED / IN_PROGRESS for the continuous S1 then S2 implementation recorded in `plan/STORYRUN_LITE_S1_S2_EXECUTION_PLAN_20261102.md`; plan SHA-256 `225FAAEBD6186130214DF2523D0B4ACABEFCEB94C9C235048750430BBA8F1B09`.
- Approver: Project owner, direct instruction in the current thread `/goal` message dated 2026-11-02. The instruction explicitly approves the full S1 + S2 scope in the pinned master goal, authorizes recording this approval, and directs automatic transition from S1 to S2 without another approval/review pause.
- Launch prompt: `plan/STORYRUN_LITE_S1_S2_LAUNCH_PROMPT_20261102.md`, SHA-256 `13067726F17892EDD4E8A10EF0EF24DE65ED4F8FAB913FE1C7753612177A070C`.
- Master goal: `plan/STORYRUN_LITE_S1_S2_MASTER_GOAL_20261102.md`, SHA-256 `C5E8B15839FA3470596DAC4B964450BD56428D481EA1A78B8AEC70B2E6A02B42`.
- Scope: exact initial path allowlist, tasks SL-0–SL-8, S1/S2 acceptance, DTR/migration, OpenAPI/Bruno, focused tests, loopback and evidence in the approved execution plan. Parent synthetic demo only; JPEG/PNG/WebP, 20 MiB/40 MP original limits, A1 photo bridge via typed binding, guard/ledger/transport and HTTP loopback in S2.
- Boundaries: no Modal/GPU/provider/network inference, no real child data, no A2/B1/B2, no Teacher/UI/story/video implementation, no A2 database or any pre-existing application database, no stage/commit/push/merge/deploy. PostgreSQL tests only on a unique loopback database created in this goal after owner verification; cleanup only that exact goal-owned database. Scanner/worker gates must be reported honestly if not verified.
- Protected baseline: preserve every pre-existing local change in `evidence/STORYRUN_LITE_S1_S2_LOCAL_CHANGE_BASELINE_20261102.md`; no listed A2/FEAT-064 or FEAT-061 file is part of this approval.
- Approval basis: owner's direct current-thread instruction and hashes above. This does not claim that M0 V12 has been independently reviewed or accepted and does not authorize a live provider call.

## B0–B13 disposition across six milestones — documentation-only — 2026-11-02

- Status: **APPROVED** for the documentation-only disposition and roadmap update below.
- Approver: Project owner, direct instruction in this thread: “ok cập nhật vào md tương ứng đi và đợi S1 và S2 tiếp”.
- Approved plan: `plan/B0_B13_SIX_MILESTONE_REDISPOSITION_PLAN_20261102.md`.
- Approved plan SHA-256: `03AEA386B8545624100688B68AA828A84CD154B47857CB5E98FB06354D6BB582`.
- Authorized files: the approved plan, this append-only approval entry, `plan/BACKLOG_API_REV37_SRS23_MODAL_20261030.md`, `plan/BE_PARENT_TEACHER_VISION_DEMO_ROADMAP_20261102.md`, and `evidence/B0_B13_SIX_MILESTONE_REDISPOSITION_REPORT_20261102.md`.
- Scope: preserve B0–B13 history; mark the old backlog inactive as an execution sequence; map remaining relevant work to roadmap milestones 2–6; define milestone 1 as the StoryRun-lite S1→S2 demo acceptance only. This does not authorize implementation or delete SRS requirements.
- Excluded: source/tests/migrations/SRS/DTR changes, A2 or legacy canvas goal execution, database operations, Modal/GPU/provider calls, deployment, staging, commit, push, and merge.


## SL-0/SL-8 roadmap rebaseline exception — 2026-11-02

- Status: **APPROVED** by the owner's explicit reply in this thread: “B — Rebaseline 875”.
- Scope: accept the existing roadmap's exact current bytes, SHA-256 `875E93C59085DA9C38923DB85EEE50D15945CBD38EC27EC0B6389B93B3ECB8D4`, as a new baseline for this single path for the S1→S2 SL-0/SL-8 acceptance gate.
- The original capture `B88188B846C62FF086AB067DB7EC7F9678967847D43BED9598274387E2B93A07` remains unchanged as historical evidence. This approval does not state that those original bytes were preserved and does not authorize modification of the roadmap.
- Authorized records: this append-only approval entry, `plan/STORYRUN_LITE_S1_S2_EXECUTION_PLAN_20261102.md`, the new rebaseline evidence, final S1→S2 evidence/status/context/decision/source records, and the additive rebaseline snapshot under `.claude/handoff/snapshots/STORYRUN_LITE_S1_S2_REBASELINE_20261102/`.
- Excluded: all implementation source, tests, migrations, the roadmap file itself, A2, FEAT-061/FEAT-064 protected content, databases, providers, staging, commit, push, merge and deploy.


## StoryRun-lite S1→S2 independent review fixes — three findings — 2026-11-02

- Status: **APPROVED** for implementation of exactly the two P2 findings (upload/cancel lifecycle; published expiry) and one P3 finding (OpenAPI/runtime response parity) in the scope below.
- Approver/source: Project owner, direct instruction in the current thread's pasted request: “Tiếp tục FEAT-063 StoryRun-lite S1→S2 để sửa đúng ba finding từ review độc lập…” The instruction explicitly requires a narrow plan and this append-only approval before source edits.
- Approved plan: `plan/STORYRUN_LITE_S1_S2_REVIEW_FIX_3_FINDINGS_20261102.md`; SHA-256 `D68FFBC1F251E367797DCAD0C6252D08797EA7ED19CC35DC2033B906C9A09D47`.
- Baseline at approval: branch `feature/feat063-be-foundation`, HEAD `a88de875ff92e9b4d4fa5cc2f5f8d5fc1f626f58`, 0 staged paths. Preserve all existing local changes and the prior snapshots. The owner-approved roadmap rebaseline remains `875E93C59085DA9C38923DB85EEE50D15945CBD38EC27EC0B6389B93B3ECB8D4`; the original B881 capture remains historical and is not represented as preserved bytes.
- Exact source/test allowlist: `backend/src/sketch2life/infrastructure/story_run_lite/repository.py`; `backend/src/sketch2life/application/services/story_run_lite.py`; `backend/src/sketch2life/interfaces/http/routers/story_run_lite.py`; `features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/openapi.json`; `backend/tests/contract/test_story_run_lite_api.py`; `backend/tests/integration/test_story_run_lite_postgres.py`; `backend/tests/integration/test_story_run_lite_loopback.py`; and `backend/tests/unit/test_story_run_lite_domain.py` only if needed.
- Authorized records: this approval entry, the exact plan above, an append-only status entry, new FEAT-063 review-fix evidence and a new additive snapshot under `.claude/handoff/snapshots/STORYRUN_LITE_S1_S2_REVIEW_FIX_20261102/`.
- Constraints: reuse the existing `ABORTED`/`EXPIRED` states; do not edit migrations/schema/domain states, roadmap, README/Bruno, A2 or FEAT-061/FEAT-064. Do not use any existing/default/A2 database; PostgreSQL is allowed only through a newly created, uniquely named loopback `storyrun_lite_*` database after owner verification, otherwise report PostgreSQL tests NOT RUN. No `.env` inspection, external network, Modal/GPU/provider, stage, commit, push, merge, deploy or branch/HEAD change.
- Acceptance is the plan's cancel/upload race and cleanup, UTC expiry/recovery/replay semantics, OpenAPI/runtime status/header parity, focused offline S1→S2 regression and validators. Final label is `FIXED — XONG-CHƯA REVIEW`; this does not claim independent review acceptance or live readiness.

## StoryRun-lite PostgreSQL owner assertion and isolated fixture — 2026-11-03

- Status: **APPROVED / IN_PROGRESS** by the owner's direct instruction in this thread to remove the fixed role from `test_goal_database_owner_accepts_loopback_inet_prefix`, compare with the connected user and actual database owner, and run the full suite on a separately created synthetic-fixture DB.
- Plan: `plan/STORYRUN_LITE_POSTGRES_OWNER_TEST_20261103.md`; SHA-256 `9ECCE04FBD36B83F498F1AD3663DFFF48C2AA8D47D59BE79AC1DC70E05C9DF97`.
- Implementation allowlist: that single function in `backend/tests/integration/test_story_run_lite_postgres.py`. Runtime source and migrations remain unchanged; name, loopback and user/owner safety gates are retained.
- Runtime verification: create a new task-owned loopback PostgreSQL 17 database, seed the synthetic Organization asset before the StoryRun-lite migration, then run the complete PostgreSQL suite with timeout and sanitized output. Existing DBs and services are preserved. If the suite fails or times out, stop before Bruno; otherwise require real ClamAV, worker and loopback stub readiness before Bruno.
- Authorized records: this append-only approval, the plan, feature evidence/status and an additive snapshot. No Modal/provider, external inference, stage, commit, push or merge.
## StoryRun-lite PostgreSQL coordination test-only fix — 2026-11-03

- Status: **APPROVED / IN_PROGRESS** by the owner's direct instruction in this thread to repair test synchronization based on `evidence/STORYRUN_LITE_POSTGRES_5433_DIAGNOSTICS_20261103.md`.
- Plan: `plan/STORYRUN_LITE_POSTGRES_COORDINATION_FIX_20261103.md`, SHA-256 `23EA4FA94242253CAA4CFBC0A8B3490ED05E668964EEFB3D81AF6C1829134906`.
- Implementation scope: only `backend/tests/integration/test_story_run_lite_postgres.py`, preserving all race/expiry/recovery behavior assertions while correcting SQL hook recognition and releasing blocking transactions/events before executor shutdown, including error paths. No runtime source or migration changes.
- Verification: run individual focused cases with per-case timeouts and faulthandler, then the full PostgreSQL suite only if focused cases pass, on the previously verified task-owned loopback DB with pre-migration synthetic fixture. Continue to ClamAV/worker/Bruno only if their prerequisites pass; stop on runtime issues or changes outside scope.
- Authorized records: this append-only entry, plan, evidence/status, and additive snapshot. Preserve existing DBs and local work. No Modal/provider, stage, commit, push or merge.
## StoryRun-lite recovery test isolation — 2026-11-03

- Status: **APPROVED / IN_PROGRESS** by the owner's direct test-only instruction based on `evidence/STORYRUN_LITE_FRESH_RECOVERY_20261103.md`.
- Plan: `plan/STORYRUN_LITE_RECOVERY_TEST_ISOLATION_20261103.md`; SHA-256 `2FC29458F68FE1E7209AD1718522C46AFDCA3AD7BA0B9ED6170D8B1DAFAA6D3F`.
- Implementation: only the two recovery tests in `backend/tests/integration/test_story_run_lite_postgres.py`; preserve exact behavioral assertions, scope injected cleanup failure to the target upload, and account precisely for DB-wide recovery candidates. Runtime source and migrations remain unchanged; no unrelated data deletion.
- Verify two isolated cases, the nine previously failing-order focused cases, then full PostgreSQL suite under the plan's gates on new task-owned PostgreSQL 17 DBs with pre-migration synthetic legacy fixture. ClamAV/worker/Bruno require a passed suite and their own readiness checks.
- Authorized records: this approval, plan, evidence/status, additive snapshot. No Modal/provider, stage, commit, push, merge, reset or use of unrelated DBs.
## StoryRun-lite local flow and new mypy diagnostic — 2026-11-03

- Status: **APPROVED / IN_PROGRESS** by the owner's direct instruction in this thread to recover local scanner and fake Vision stub, run the gated Bruno flow and fix the single new test-only mypy error.
- Plan: `plan/STORYRUN_LITE_LOCAL_FLOW_TYPE_FIX_20261103.md`, SHA-256 `1BB36071CDDEA749B3C30F07E9DDDF334E84B745E70274B629D93CE040303A4F`.
- Code scope: only the annotation on the new `ControlledDateTime.now` in `backend/tests/integration/test_story_run_lite_postgres.py` and required imports; do not edit runtime or migration or expand to the 24 earlier diagnostics. Existing DBs and local work are preserved.
- Local flow requires real ClamAV CLEAN and EICAR INFECTED, verified worker, a temporary fake V2 loopback Vision stub and a separately verified task DB. Stop and record missing gates. No Modal/provider, stage, commit, push, merge or deploy.
- Records: this append-only approval, plan, feature evidence/status and an additive snapshot. This records the direct owner instruction and the owner's existing instruction to record required approvals under the harness.
- Type-fix implementation detail: mypy requires the datetime subclass override to return the subclass type. The owner-authorized test-only fix constructs that subclass at the same instant and timezone; revised plan SHA-256 `B805105906944176DBE64111583E6A1F82E21335A474F0E09B4B22F81AC796DC`. The original approval entry and its earlier plan hash remain historical.
- The owner subsequently authorized setup of real ClamAV and its signature database from official sources for this local flow. This does not authorize Modal or a provider call.
## StoryRun-lite guarded Modal live integration — 2026-11-03

- Status: **APPROVED / IN_PROGRESS** under the owner's direct instruction in this thread to integrate and test one synthetic Parent flow through the real Modal V2 endpoint; plan `plan/STORYRUN_LITE_MODAL_LIVE_20261103.md`, SHA-256 `49E1C7584E69964EE2444E7C2CFE85CB816D1501F8080CAAC2F87045F7B4DAE1`.
- Authorized implementation: `backend/src/sketch2life/infrastructure/story_run_lite/photo_bridge.py`, `backend/src/sketch2life/infrastructure/story_run_lite/composition.py`, `backend/tests/unit/test_story_run_lite_photo_bridge.py`, and if needed `backend/tests/integration/test_story_run_lite_loopback.py`; plus plan, append-only approval, feature evidence/status and additive snapshots. No edits to A2, FEAT-061/064, migrations, deployment or unrelated source.
- Explicit live-only configuration and one-run binding; default loopback/fail-closed; existing A1 guard/ledger/TLS transport, total deadline, no redirect, no automatic retry or resend after SENT/UNKNOWN. Offline gates, task-owned DB, actual ClamAV and worker verification precede at most one HTTP inference request; post-SENT ambiguity is UNKNOWN and terminal.
- Owner chose a simple synthetic image. An active Modal endpoint and local credential path are not yet available. No live request is authorized before prerequisites pass; preserve all previous snapshots and existing DBs. No stage, commit, push, merge or deploy.
## StoryRun-lite temporary Modal serve — 2026-11-03

- **APPROVED / IN PROGRESS** by the owner's direct instruction in this thread: temporarily serve the existing FEAT-061 V2 app and run at most one synthetic Parent inference through the StoryRun-lite backend and A1 ledger, after the established safety gates. The owner explicitly authorizes `modal serve` only; persistent deployment is excluded.
- Supplemental plan: `plan/STORYRUN_LITE_MODAL_TEMP_SERVE_20261103.md`, SHA-256 `E57BBB6BDE5061B390E4A6C5D0D14F3F1A260D53CFDB14549759FD838EC77DCE`. Keep the previous plan and historical evidence intact; use a clean committed archive for remote serving, retain all databases and local changes, and shut down task-owned temporary processes/app. No stage, commit, push or merge.
- Classify or fix the two mypy diagnostics only within the existing source allowlist; if a correction requires a file outside that scope, report it before making that change.
## StoryRun-lite Modal diagnosis and cleanup port contract — 2026-11-03

- **APPROVED / IN PROGRESS** under the owner's direct instruction in this thread. Supplemental plan `plan/STORYRUN_LITE_MODAL_DIAGNOSE_CONTRACT_20261103.md`, SHA-256 `F1E3858129F6592EECE021BA51A93601B945F1D36BE562B5F22F485614CF06A9`.
- Authorized narrow extension: `backend/src/sketch2life/application/ports/story_run_lite.py` and genuinely needed focused tests, to represent and verify the real cleanup success/failure result after examining implementations and callers. Do not alter cleanup behavior or migration to obtain a clean type check.
- Diagnose the previous app and, if the health blocker can be resolved, use a new temporary `modal serve`; one synthetic BE/A1 inference request at most, no resend after SENT/UNKNOWN. Preserve DBs, local changes and historical records; no persistent deploy, stage, commit, push or merge.
## StoryRun-lite main backend integration — 2026-11-03

- **APPROVED / IN PROGRESS** by the owner's direct request in this thread. Plan `plan/STORYRUN_LITE_MAIN_BE_INTEGRATION_20261103.md`, SHA-256 `FD5E5DC2CD53391EC31705C8A0A31725EA2F62B6CE88AB3DAF32382E78FED827`. Preserve earlier plans and evidence.
- Authorizes opt-in local synthetic StoryRun main-app integration, a narrowly justified compatibility path for the two conflicting migration branches, focused source/tests/UI handoff, and read-only inspection of local `sketch2life`. Migration of that exact DB is authorized only after isolated matrix/regression gates pass and its observed state is covered; no existing DB reset/drop/truncate/delete.
- Authorizes one guarded Modal inference HTTP request only after all local and database gates pass. No retry following SENT/UNKNOWN. No A2 changes, stage, commit, push, merge or persistent deployment.
## Historical Swagger approvals — Plans Rev38–44 (detail files retired)

- The owner approved the prior Swagger sequence: Rev38 contract alignment and discrepancy reporting; Rev39 navigation grouping; Rev40 synthetic local QA and upload 413 correction; Rev41 overview copy; Rev42 review and local commit; and Rev44 source-backed response documentation and FE grouping.
- The approved scope preserved protected-route authentication and avoided fake credentials, unmounted routes, and unrelated runtime changes. The scoped upload 413 request-ID sanitization from Rev40/42 remains in the reviewed source.
- Plan hashes: Rev38 C1E8C74AD57E7F053E0D1E093BAF7F97BE6F12E8EF8887A2C098632B9B863BCF; Rev39 1E0244E9D43F3F3B46361D66711D413293F2B7E50DB30DEE5B353BAA2474834F; Rev40 701402BC515745FDCBCFF8C8AF8E7630EDF4025D51C330F7E7747AB6D738E1E9; Rev41 8693C3B4165F9413775306260CCC9023404F2AB7F58C967632236951B1FC2BDB; Rev42 E8A809729BDE4B83D0A6FD0AC21336C8F3721F55B7BDFA7431F1125922D026E8; Rev44 310E7ED12BDE95BCFF3B438DB89D4DB42A0B18DA353510529B5BA38E585E0D75.
- At the owner's request, standalone plan/evidence Markdown files for these superseded revisions are omitted from the current dev tree. Current authorization is recorded under Plans Rev45–48.

## Plan revision 45 — Swagger scope aligned to SRS v2.2

- Status: APPROVED for the exact FE-facing OpenAPI projection and documentation-only scope below.
- Approver: Project owner, direct instruction in the current chat on 2026-11-01: “giờ cập nhật lại swagger trên nhánh dev theo srs 2.2 đi”.
- Recorded date: 2026-11-01, Asia/Saigon.
- Feature: FEAT-063 — whole-repository architecture redesign.
- SRS baseline: `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS_V2.2_PRESERVED_20261028.md` (v2.2-draft; owner-selected for this Swagger task, not thereby signed off as a product specification).
- Approved plan: `plan/PLAN_REV45_SWAGGER_SRS_V22_SCOPE_20261101.md`.
- Approved plan SHA-256: `5D1DBABE161F92F08DE7FE8C1B81B1E5D57CFA3C2B8D57CBA6BE76ACADB0FD06`.
- Approved scope: publish exactly 24 existing SRS-domain-related operations across organization/class/profile/consent and Teacher lesson authoring/library/upload; exclude mounted local/demo, collaborative-classroom, gallery, lesson-sharing, moderation, health, and unmounted candidate operations from the FE-facing spec; retain all runtime routes and behavior; describe missing SRS flows without inventing endpoints; regenerate an OpenAPI snapshot and update FEAT-063 records/evidence.
- Explicitly excluded: route/handler/auth/schema/runtime behavior changes; new or fake API endpoints; test-suite execution; database, Docker, provider, deployment, commit, and push operations.
- Acceptance criteria: AC1–AC6 in the hash-identified Plan Rev45.
- Approval basis: the owner's direct instruction applies to the exact Plan Rev45 scope and acceptance criteria.

## Plan revision 46 — commit Swagger and consolidate two prior commits

- Status: APPROVED for the exact local commit and remote branch-history update below.
- Approver: Project owner, direct request in the current chat on 2026-11-01: “commit cho tui và xóa 2 commit trước được không”.
- Recorded date: 2026-11-01, Asia/Saigon.
- Feature: FEAT-063 — whole-repository architecture redesign.
- Approved plan: `plan/PLAN_REV46_SWAGGER_HISTORY_CONSOLIDATION_20261101.md`.
- Approved plan SHA-256: `4EE5DEF1E5AD7C544BBCF79921E8A7495EDE79C7765AE523D38BFFA1D9938B27`.
- Approved history scope: replace only `6d77d2ad41370f118386d9861fed4cd031ddea67` (`feat(swagger): clarify FE-facing OpenAPI contract`) and `f68ed2b579c89e8fb1ee3dcf7e4c8f109acd31d8` (`feat(api-docs): align Swagger with FEAT-063 contract`) with one consolidated commit based on `111ae547007801d7d171dd12f3ac6f1085d22199`; update `origin/dev` using force-with-lease against expected old tip `6d77d2ad41370f118386d9861fed4cd031ddea67`.
- Explicitly excluded: rewriting any other commit/branch, merging other work, API or runtime behavior changes, backend test execution, database/provider/deployment changes.
- Acceptance criteria: AC1–AC6 in the hash-identified Plan Rev46.
- Approval basis: the owner's direct request applies to the exact two commits and branch update scope in Plan Rev46.

## Plan revision 47 — remove obsolete Swagger artifacts before push

- Status: APPROVED for the exact artifact cleanup and amendment of the not-yet-pushed consolidated commit.
- Approver: Project owner, direct follow-up in the current chat on 2026-11-01 requesting removal of unused files before pushing to avoid file clutter.
- Recorded date: 2026-11-01, Asia/Saigon.
- Feature: FEAT-063 — whole-repository architecture redesign.
- Approved plan: `plan/PLAN_REV47_SWAGGER_COMMIT_ARTIFACT_CLEANUP_20261101.md`.
- Approved plan SHA-256: `485BD6239BB6458853339A6E92CD4A02446C41D130819E827F5FA517C913E535`.
- Approved scope: remove superseded Rev37/Rev44 OpenAPI snapshots, obsolete local Swagger quickstart and synthetic PNG fixture; remove only local Demo request examples from generated OpenAPI documentation/export assertions; retain backend runtime routes, current Rev45 snapshot, API contract source, and historical approval/evidence records; amend the single consolidated local commit before the lease-guarded remote update.
- Explicitly excluded: route/auth/payload/runtime behavior changes, deletion of historical approval/evidence records, unrelated branch/history changes, backend test execution.
- Acceptance criteria: AC1–AC5 in the hash-identified Plan Rev47.
- Approval basis: the owner's direct file-cleanup follow-up applies to this exact pre-push cleanup and commit amendment.

## Plan revision 48 — retire superseded Swagger revision notes

- Status: APPROVED for the exact documentation cleanup and amendment of the not-yet-pushed consolidated commit.
- Approver: Project owner, direct request in the current chat on 2026-11-01: remove the old Swagger Markdown files from the pending commit and keep only the current work.
- Recorded date: 2026-11-01, Asia/Saigon.
- Feature: FEAT-063 — whole-repository architecture redesign.
- Approved plan: plan/PLAN_REV48_SWAGGER_HISTORY_DOC_CLEANUP_20261101.md.
- Approved plan SHA-256: DA706B55D7B1310C9CB87288A1A606604FDA3E9D931BC7FFD386E89E482668E3.
- Approved scope: remove the superseded standalone Swagger plan/evidence notes identified in Plan Rev48; clean current indexes/registers so they do not link to removed documents; retain the current SRS v2.2 Swagger snapshot, current evidence, required approval/status records, source contract metadata, and runtime routes.
- Explicitly excluded: unrelated FEAT-063 history, API route/auth/payload/runtime changes, remote ref changes beyond the already approved lease-guarded consolidation in Plan Rev46, and backend test-suite execution.
- Acceptance criteria: AC1–AC5 in the hash-identified Plan Rev48.
- Approval basis: this owner's direct request applies to the exact cleanup and acceptance criteria in Plan Rev48.

## Milestone 1 independent review fixes — 2026-11-03

- Status: APPROVED / IN PROGRESS. Owner explicitly answered: “Cho phép ghi approval và sửa 6 finding”.
- Plan: `plan/STORYRUN_LITE_MILESTONE1_INDEPENDENT_REVIEW_FIX_20261103.md`, SHA-256 `B054B44289EA9DE32F26878F719E06A1EA34591518BDDF5690EA62AB3BB295C4`.
- Authorizes the six reviewed lifecycle/reconciliation/replay/singleton/Bruno findings and focused regression tests, plus feature-owned documentation/evidence/snapshot. Existing D1 permits cancel after PREPARATION_REVIEW; retain states and migrations.
- Preserve the 55 pre-existing A2/local paths, HEAD/index and existing databases. PostgreSQL tests only on a new task-owned loopback DB; otherwise explicitly NOT RUN. No Modal/provider/GPU, stage, commit, push or merge.
- Final implementation label: FIXED — XONG-CHƯA REVIEW only after required gates pass. Independent review remains a separate user-owned chat.

## Owner approval — full BE Bruno collection — 2026-11-03

- **Status:** APPROVED / IN PROGRESS.
- **Owner instruction:** after Milestone 1 completes, create a complete Bruno collection for the full BE API surface under FEAT-063.
- **Pinned plan:** `plan/BE_FULL_BRUNO_COLLECTION_PLAN_20261103.md`, SHA-256 `4488A7B739FDCC80246AFB590DDFC229B6DCB37FEB9600C5B9501B160E5E80ED`.
- **Authorized scope:** inventory current mounted runtime API contracts; create a separate full-BE runtime OpenAPI artifact, Bruno collection, operation coverage matrix, local validator, README and evidence under `artifacts/be-full/`; update FEAT-063 records and snapshot.
- **Boundaries:** preserve StoryRun-lite collection and all 55 unrelated A2 paths; no BE route/schema/migration changes, no real child data/credentials, no external provider/Modal/GPU calls, no existing DB reset, no stage/commit/push/merge.

## Plan Rev49 — six-milestone roadmap review corrections — 2026-11-03

- **Status:** APPROVED / IN PROGRESS for documentation-only corrections to the six-milestone BE Parent/Teacher roadmap and a written disposition of the cloud review findings.
- **Owner instruction:** “lấy những phần review của claude đúng và sửa và cũng chỉ ra cho nó tại sao chỗ đó của nó lại sai đi”.
- **Plan:** `plan/ROADMAP_REVIEW_FIX_PLAN_20261103.md`.
- **Plan SHA-256:** `BECC69238E5049649204E5F9C32D2CB9660E625B795E131C4A5553599D08901C`.
- **Authorized scope:** update the six-milestone roadmap, FEAT-063 source register/context/decisions/status, and add `evidence/CLAUDE_ROADMAP_REVIEW_DISPOSITION_20261103.md` as detailed in the hash-pinned plan. Clarify SRS traceability and unresolved owner gates; correct stale status and renumber the duplicate OpenAPI decision as D-130; document the plan/report hash provenance discrepancy without rewriting historical claims.
- **Boundaries:** do not edit the SRS, DTR, implementation, tests, migrations, FEAT-064 approval or A2/B1/B2 plans; do not access database, Modal/provider, network or remote refs; do not run test/validator suites, stage, commit, push or merge. Preserve all unrelated local changes byte-for-byte.

## Plan Rev50 — six-milestone roadmap round-2 review corrections — 2026-11-03

- **Status:** APPROVED / IN PROGRESS for the documentation-only corrections described below.
- **Owner instruction:** continuation of the direct instruction to apply valid Claude review findings and explain conclusions that were incorrect or limited by cloud visibility.
- **Plan:** `plan/ROADMAP_REVIEW_FIX_PLAN_REV50_20261103.md`.
- **Plan SHA-256:** `0FFF0D9CAA01036E08A90120FC7067D38B564E80E72E4324B470D1E8E13C66DC`.
- **Authorized scope:** update the six-milestone roadmap, FEAT-063 `DECISIONS.md`, `CONTEXT.md`, `SOURCE_REGISTER.md`, `status/STATUS.md`, and `evidence/CLAUDE_ROADMAP_REVIEW_DISPOSITION_20261103.md`; preserve the distinction between accepted local evidence and unsigned SRS/owner gates.
- **Boundaries:** no SRS, DTR, B0 plan/report, source, test, migration or FEAT-064 file changes; no DB, Modal/provider, network, Git history/index/remote operation; no tests/validator suite, stage, commit, push or merge. Preserve unrelated worktree changes byte-for-byte.

## Plan Rev50A — backlog pointer and B4b/B10/B13 disposition — 2026-11-03

- **Status:** APPROVED / IN PROGRESS for this one-file documentation supplement.
- **Owner instruction:** continuation of the direct request to apply valid findings from Claude's round-2 review.
- **Plan:** `plan/ROADMAP_REVIEW_FIX_PLAN_REV50A_BACKLOG_POINTER_20261103.md`.
- **Plan SHA-256:** `27288634F301B7430C531E17B51EE15D35B0EB3735C26925767111447849661D`.
- **Authorized scope:** only `plan/BACKLOG_API_REV37_SRS23_MODAL_20261030.md`, for the current roadmap pointer and B4b/B10/B13 rows described in the hash-pinned plan.
- **Boundaries:** preserve all other bytes; no SRS/DTR/source/test/migration, database, Modal/provider, network, Git history/index/remote, tests/validators, stage, commit, push or merge.

## Owner acceptance — six-milestone roadmap and SRS v2.3 planning baseline — 2026-11-03

- **Status:** APPROVED FOR PLANNING BASELINE ONLY; no M2–M6 implementation approval.
- **Owner instruction:** the owner confirmed “ok chốt đi” after choosing to use the existing SRS v2.3 for M2–M6 without authoring or editing the SRS.
- **Roadmap:** `plan/BE_PARENT_TEACHER_VISION_DEMO_ROADMAP_20261102.md`, current SHA-256 `A0A485EE421FBB1DA9DEC99DD8EC08279D14EAF27EC548AD6A0A4CE8F234F8FA`; independent review round 3 ACCEPTED the preceding reviewed bytes, then the owner acceptance was recorded in the roadmap.
- **Accepted planning direction:** use the current SRS v2.3-draft unchanged as the planning baseline for milestones 2–6; follow its §8.1 Parent-before-Teacher ordering. The SRS remains unsigned and unmodified.
- **Gates:** each milestone requires its own detailed plan, acceptance criteria, data/migration boundary and explicit implementation approval. Model/version, Parent line-sketch scheduling, optional lesson access, B0 provenance and other unresolved gates remain open until their relevant milestone.
- **Excluded:** SRS sign-off or edits, implementation/goal launch, runtime/source/test/migration changes, database or provider operations, and Git history/index/remote operations.

## Modal AI setup scaffold — 2026-11-03

- Status: COMPLETE for the exact dev-only configuration scaffold below; owner-side Modal environment setup remains separate.
- Approver: Project owner, direct instruction in the current chat on 2026-11-03: “tạo mấy đó cho tôi đi, sau đó tôi sẽ setup env sau”.
- Feature: FEAT-063 — whole-repository architecture redesign.
- Approved plan: `plan/MODAL_AI_SETUP_SCAFFOLD_20261103.md`.
- Approved plan SHA-256: `7FE03A68DF76877457DF5C5F652FCB705669A624B2E07F7B6F317C9FB510E391`.
- Approved scope: create the SRS v2.3 workload registry; versioned path/hash-only Modal worker envelope; dev-only L4 and L40S Modal app skeletons with bounded resources and fail-closed unconfigured handlers; placeholder-only Modal environment example and owner setup guide; additive FEAT-063/global context, decision, status, source-register and evidence updates.
- Explicit exclusions: model selection/benchmark, inference implementation, backend/provider/job/storage integration, edits to the existing Qwen3-VL app, actual `.env`/secrets, SRS/ADR/schema/API/Docker changes, Modal account/resource/deployment/GPU/provider operation, tests, child data, commit or push.
- Acceptance criteria: AC1–AC8 in the hash-identified plan.
- Approval basis: the owner’s direct instruction applies to this exact repository scaffold and does not approve live Modal setup; the owner will configure the Modal environment afterward.

## Modal drawing VLM L4 POC — 2026-11-03

- Status: APPROVED for the exact synthetic-only Modal dev POC below.
- Approver: Project owner, direct instruction in the current chat on 2026-11-03: “tạo môi trường xong r, làm phần việc tiếp theo đi, cần AI nào thì host đó đi”.
- Feature: FEAT-063 — system architecture rearchitecture.
- Approved plan: `plan/MODAL_DRAWING_VLM_L4_POC_20261103.md`.
- Approved plan SHA-256: `F2AF6433EFE812BBD8144CBCD3E4ECFDE09FCF0A9952280BCE814314A7008E72`.
- Approved scope: add a separate private `drawing.analyze` Modal app for Modal `dev`; use the pinned Qwen2.5-VL-7B-Instruct revision and pinned runtime dependencies; create the two named Volume v2 resources only if absent; download weights; stage one generated synthetic butterfly drawing via the scratch Volume; perform exactly one bounded L4 inference; and add the task-specific evidence plus additive FEAT-063/global records listed in the plan.
- Explicit exclusions: real child/media/profile/lesson data, MinIO/S3 access, public endpoint, new secret, backend/API/queue/quota integration, production model selection, other AI workloads, SRS/ADR/schema/Docker changes, broad product tests, commit, push, or merge.
- Acceptance criteria: AC1–AC7 in the hash-identified plan.
- Approval basis: the owner’s current instruction authorizes hosting the required next AI workload; the plan limits this first deployment to the first required vision stage and one synthetic inference, and makes no production-default claim.

## Modal drawing VLM corrective retry A — 2026-11-03

- Status: APPROVED for one corrective synthetic inference after the first call failed before model inference because the image lacked `torchvision`.
- Approver/basis: the owner’s direct instruction in the current chat on 2026-11-03 authorizes continuing with the required AI hosting; this amendment records the single dependency-only correction within that scope.
- Feature: FEAT-063 — system architecture rearchitecture.
- Approved plan: `plan/MODAL_DRAWING_VLM_POC_CORRECTIVE_RETRY_A_20261103.md`.
- Approved plan SHA-256: `E7279EEEEEE2DABDA3119090CCC705052D487EBF0AD4081D9E66910A76AA83BC`.
- Approved scope: add `torchvision==0.22.1` compatible with pinned `torch==2.7.1`; redeploy the same private drawing VLM app to Modal `dev`; run exactly one corrective call against the same synthetic butterfly fixture; preserve the first failure and record the new result.
- Explicit exclusions: any third call, model/GPU/precision/configuration change, alternate environment, new Secret, real child data, public endpoint, backend integration, other AI workload, SRS/ADR change, commit, push, or merge.
- Acceptance criteria: AC1–AC4 in the hash-identified corrective plan.

## Modal AI hosting wave — 2026-11-03

- Status: APPROVED for the exact dev-only model hosting and synthetic proof-of-execution scope below.
- Approver: Project owner, direct instruction in the current chat on 2026-11-03: “môi trường xong r, làm phần việc tiếp theo đi, cần AI nào thì host đó đi”.
- Feature: FEAT-063 — system architecture rearchitecture.
- Approved plan: `plan/MODAL_AI_HOSTING_WAVE_20261103.md`.
- Approved plan SHA-256: `C8FCB03681F2145E727F89E55DDD159AA354814E30B868CD745B930A83FCA5BA`.
- Approved scope: implement and deploy private Modal `dev` candidate workers for Qwen2.5-7B story/storyboard, faster-whisper large-v3, VieNeu-TTS v3 Turbo with its pinned ONNX codec, FLUX.2 Klein 4B, and a non-production Wan2.2 TI2V-5B video alternative benchmark; reuse existing Volume v2 resources; run at most one synthetic call per runnable model; for bounded POC media outputs up to 16 MiB, return bytes to the local runner and verify SHA-256; and record evidence plus additive FEAT-063 records.
- Explicit exclusions: real child data, production/public endpoint, LTX-2.5 gated access/license/token/Secret, production model promotion or SRS amendment, lesson suggestions, SAM2, safety certification, backend/API/storage integration, extra retries after failure, commit, push, or merge.
- Acceptance criteria: AC1–AC8 in the hash-identified plan.
- Approval basis: the owner’s direct current instruction authorizes hosting the required AI candidates; the plan limits work to synthetic-only Modal `dev` experiments and preserves unresolved gates.

## Local API runtime availability smoke - 2026-11-03

- Status: APPROVED / COMPLETE for the exact read-only API smoke scope below.
- Approver: Project owner, direct instruction in this chat: run the APIs.
- Feature: FEAT-063 - system architecture rearchitecture.
- Approved plan: `plan/API_RUNTIME_AVAILABILITY_SMOKE_20261103.md`.
- Approved plan SHA-256: `7DA01D9CF5D5C4E98BA45C88815BBBE3589D0A5E9F94E512DDD9B995D570C5BA`.
- Approved scope: GET the live local API health and OpenAPI documents; make one read-only GET route-availability probe; inspect only whether non-secret provider settings are present; record sanitized results.
- Explicit exclusions: mutating API requests, backend/Modal integration, new routes, provider/model inference, database changes, container restart, credential reads, commit, push, or merge.
- Result: read-only probes completed and evidence recorded in `evidence/API_RUNTIME_AVAILABILITY_SMOKE_20261103.md`; the running API has no StoryRun route or dispatch integration to the new Modal workers.

## Backend API to Modal drawing VLM vertical slice - 2026-11-03

- Status: APPROVED / IN PROGRESS for the isolated synthetic drawing-analysis API slice.
- Approver and basis: the project owner directly authorized proceeding with the backend-to-Modal integration and requested that the APIs be exercised.
- Feature: FEAT-063; canonical requirements remain the latest SRS in FEAT-063.
- Plan: `plan/MODAL_BACKEND_API_DRAWING_VERTICAL_SLICE_20261103.md`.
- Current cumulative plan SHA-256: `855235EA0B209A8B64699074C6D861734A5AC17CBD82B1E56E42F9FA9039D0F5`.
- Approved implementation paths: `backend/pyproject.toml`, `backend/uv.lock` (Modal dependency lock only), `backend/Dockerfile` (existing image-admission extra only), the Modal/StoryRun adapter and composition files listed in the plan, its focused test file, and additive FEAT-063 records.
- Approved verification: isolated API containers on loopback ports 8001/8002; temporary task-owned PostgreSQL databases and migrations; synthetic StoryRun CRUD; and, after the earlier call became terminal, exactly one API-triggered analysis of the generated synthetic butterfly fixture.
- Database fallback: use the EDB PostgreSQL 17.11-4 Windows x64 binaries archive only in OS temp, verify its checksum, initialize an isolated data directory, bind only to 127.0.0.1:5433, and do not install a service or change system PATH.
- Modal dispatch gate: prior call `fc-01M6GN62XVPDBR39205WQ35K9Q` reached terminal `success`; this permitted one API-triggered synthetic inference. If that new call becomes ambiguous, do not retry.
- Linux host-network API limitation: do not bypass the Windows Job Object image-admission worker. The Linux CRUD fallback stays Vision-disabled; use the Windows-host runtime for image upload/admission and API inference.
- Excluded: real child data, public Modal HTTP endpoint, new token/Secret, production auth/model selection, other AI workflow integrations, mutations to existing containers/databases, code outside approved paths, commit, push or merge.

### Plan addendum 6 - owner instruction to stop the drawing app

- Status: APPROVED and executed for the one app-stop action below.
- Approver and basis: the project owner directly instructed that the app be stopped after the run.
- Plan: `plan/MODAL_BACKEND_API_DRAWING_VERTICAL_SLICE_20261103.md`.
- Current cumulative plan SHA-256: `855235EA0B209A8B64699074C6D861734A5AC17CBD82B1E56E42F9FA9039D0F5`.
- Approved action: after the API-triggered call reached terminal success, stop only Modal dev app `sketch2life-srs23-drawing-vlm-dev`; verify it is stopped. Preserve shared Volumes/model files and leave every other Modal app untouched.
- Result: `modal app stop ... --env dev --yes` completed successfully; Modal app info reported `State: stopped`. Redeploy is required before future use.
- Boundary: this does not authorize retrying the call, reconciling or rewriting the API StoryRun, stopping other apps/services, deleting task data, commit, or push. The StoryRun remains `VISION_OUTCOME_UNKNOWN` / `AWAITING_RECONCILIATION` because the API did not persist the late result.

## Parent image-to-script API and AI retest - 2026-11-03

- Status: APPROVED / IN PROGRESS for the exact synthetic Parent API + AI script retest below.
- Approver and basis: direct owner request in the current conversation to retest the Parent flow from one drawing, run AI, generate a sample script, report API failures, and skip video generation.
- Plan: `plan/PARENT_IMAGE_TO_SCRIPT_API_AI_RETEST_20261103.md`.
- Approved plan SHA-256: `4376140CE55FA3E612CEA111D0EA73EC2FAE6839CE3E8AAE584B69EA7E8CD1EB`.
- Approved scope: one generated synthetic butterfly fixture and synthetic Parent profile; isolated new task DB and loopback API; all available upload, image-understanding, and subject-confirmation routes in the Parent path; exactly one direct private Modal `story.generate` call after adult confirmation; route/result inventory and task-local evidence.
- Explicit exclusions: real child data, video/Wan/LTX/FFmpeg, ASR/TTS, FLUX, SAM2, lesson suggestions, Teacher flow, changing or retrying the prior ambiguous StoryRun, product/API implementation, model/workload enablement, existing application DB/containers, commit/push/merge.
- Retry fence: at most one drawing inference and one script inference; an unknown outcome is never retried.
- Cleanup: stop only task-owned local processes and the drawing/language-audio apps used in this retest; retain shared Volumes/model files and leave unused FLUX/video apps and existing project services untouched.

## Parent workflow app shutdown amendment - 2026-11-03

- Status: APPROVED / IN PROGRESS as a direct follow-up to the owner's instruction to run the simulated Parent flow and turn off the apps afterward.
- Plan: `plan/PARENT_IMAGE_TO_SCRIPT_API_AI_RETEST_20261103.md`.
- Current plan SHA-256: `D4FFF231654E81E54966219C15685D709E6859AFAFEE6009F4A08A666FE92DD8`.
- Superseding cleanup authorization: stop each Modal app currently deployed in dev after the test reaches a terminal/unknown outcome and evidence is saved: drawing VLM, language/audio, FLUX image, and video candidate. Do not invoke FLUX/video, delete app records, or delete shared Volumes/model files.

## Parent story-worker fallback after Modal L4 scheduling timeout - 2026-11-03

- Status: APPROVED / IN PROGRESS under the owner's direct instruction to run the full simulated Parent workflow, test AI, generate a sample script, and omit video.
- Plan: `plan/PARENT_IMAGE_TO_SCRIPT_API_AI_RETEST_20261103.md`.
- Current plan SHA-256: `8491CBA56D6A44F60B2980D7A5D92ADD88A20F9CB8E85D40495D33016B7561B7`.
- Authorized exception: after the one API drawing inference returned VISION_OUTCOME_UNKNOWN / AWAITING_RECONCILIATION, preserve it without retry; call the private story.generate worker exactly once with the visually verified synthetic butterfly topic, Vietnamese, and five scenes. Record this only as a detached worker test, not as Parent API end-to-end success. No video call.

## Parent image-to-script API/AI retest - final execution record - 2026-11-03

- Execution status: COMPLETE as a test run; functional acceptance is BLOCKED by Modal L4 scheduling and the missing Parent script API.
- AC1: Partial. The isolated app started and API routes were exercised, but `/health`, `/openapi.json`, and `/` return 404 because they are not registered.
- AC2: Pass. Synthetic image upload, SHA-256 validation, ClamAV, normalization, persistence, and `READY` state passed.
- AC3/AC4: Not achieved. The one drawing dispatch returned `VISION_OUTCOME_UNKNOWN` / `AWAITING_RECONCILIATION`; subject confirmation was not called. No retry.
- AC5: Not achieved. The one detached story worker returned no result during the bounded wait; no Parent API script route exists. No retry.
- AC6: Pass for the zero-video requirement. Video inference count is zero; the report records tested route outcomes and the missing script API boundary.
- AC7: Pass. All four deployed Modal dev apps and task-local API/PostgreSQL were stopped. Shared Volumes/model files remain; only task-specific input prefixes were removed.
- Evidence: `evidence/PARENT_IMAGE_TO_SCRIPT_API_AI_RETEST_20261103.md` and `evidence/assets/parent_image_to_script_retest_20261103/`.
- No product code was changed; no commit, push, or merge was requested or performed.

## Parent generated-image and activity-selection retest — 2026-11-03

- Status: APPROVED / IN PROGRESS for the exact synthetic API/AI retest scope below.
- Approver and basis: direct owner instruction in the current chat to generate a new synthetic image, rerun the Parent workflow including a selectable activity list, record timings, and stop apps afterward.
- Plan: `plan/PARENT_GENERATED_IMAGE_TO_ACTIVITY_SELECTION_RETEST_20261103.md`.
- Approved plan SHA-256: `2510140F46377ABF47E357CFF81C89C0B10936EC1B3AA956A9524EA610AA84E2`.
- Approved scope: one new synthetic ImageGen drawing; the isolated StoryRun-lite image/upload/subject path; at most one Modal drawing inference and one story-generation inference; and one synthetic in-process TestClient session using the existing activity HTTP route plus a deterministic VLM fixture to retrieve and select from the curated activity catalog.
- Explicit exclusions: real child data, video inference, FLUX, SAM2, ASR/TTS, product code/API changes, schema changes, durable data in the existing project API, changing or retrying prior runs, stopping unrelated local project services, commit, push, or merge. The activity harness uses the codebase's test-only image decoder and must not be represented as passing ClamAV or production image normalization.
- Important contract boundary: activity suggestions are currently exposed by a separate legacy demo session route before video; that route is not integrated with StoryRun-lite, the activity list is not AI-generated, and it does not satisfy SRS §31.5 post-video ordering. Evidence must state these limitations.
- Retry fence: at most one drawing inference and one story-generation inference for this run; ambiguous outcomes are not retried.
- Cleanup: stop task-owned API/PostgreSQL processes and every Modal app deployed in `dev`; preserve shared Volumes/models and leave the pre-existing local API on port 8000 and unrelated services running.

## Parent generated-image retest - pre-dispatch recovery amendment - 2026-11-03

- Status: APPROVED / IN PROGRESS under the owner's direct request to run the complete synthetic Parent flow, include selectable activities, record timing, and stop apps afterward.
- Plan: `plan/PARENT_GENERATED_IMAGE_TO_ACTIVITY_SELECTION_RETEST_20261103.md`.
- Amended plan SHA-256: `A28BB8F675EC3F1CFCC9C35EEEEAD86B35DDFAB7B6960F4F4EA37682C48DBC74`.
- Recovery: the first StoryRun failed the local pinned-run-ID guard before any durable provider invocation. Preserve it as a setup failure; do not mutate or retry it. One replacement synthetic StoryRun may be created, and the API may be restarted with that exact generated run ID pinned before the image is attached.
- Provider fence: across the whole task, dispatch at most one real drawing VLM call and at most one story-generation call. If the replacement attempt remains blocked before dispatch, stop without creating another run. No video or product/API/schema change is authorized.

## Parent generated-image retest - final execution record - 2026-11-04

- Execution status: COMPLETE under the direct owner request and approved synthetic-only plan; no video call.
- Final plan SHA-256, including execution record: `9DDB22A054E777A4A5ADF7DB5C161FEF7DAE00646FB43A9DADA62BC3D121083E`.
- Results: one actual Modal drawing inference succeeded with subject `bướm`; adult confirmation was accepted; one Modal story worker succeeded with five scenes; one legacy catalog activity was returned and selected using its deterministic test fixture.
- Limitations: the StoryRun API has no script-generation endpoint; the activity route is a separate pre-video legacy session and returned one non-outdoor catalog item; generated story contains factual butterfly-lifecycle errors; video calls equal zero.
- Cleanup: drawing/language Modal apps stopped, every listed dev app is stopped, task API/PostgreSQL ports 8002/5433 are closed, and pre-existing API 8000 plus shared model Volumes remain.
- Evidence: `evidence/PARENT_GENERATED_IMAGE_TO_ACTIVITY_SELECTION_RETEST_20261103.md`. No commit or push was requested or performed.

## AI flow SRS alignment and Teacher deck POC — 2026-11-04

- Status: APPROVED / IN PROGRESS under the owner's direct instruction in the current conversation.
- Plan: `plan/AI_FLOW_SRS_ALIGNMENT_AND_TEACHER_DECK_POC_20261104.md`.
- Approved plan SHA-256: `20453BA46D206EA84A08970F949098130831AB15E0363E1D02410BBCF77B5A4A`.
- Approved scope: SRS-compatible Parent story-draft contracts, persistence and review API; bounded Modal story generation with factual/schema guards; synthetic Teacher Sketch Deck worker plus one FLUX visual and local HTML preview; relevant API/AI tests and task-local evidence.
- Explicit exclusions: video inference, real child data, real lesson documents, public publishing, production model promotion, SAM2, lesson suggestion, TTS/Whisper, `.env`/secret changes, editing the canonical SRS, commit/push/merge.
- Retry fence: one attempt per AI workload; unknown provider outcomes are not retried. Preserve previous test evidence and unrelated worktree changes.
- Cleanup: stop task-owned local services and all deployed Modal `dev` apps after evidence is complete; retain shared Volumes and model weights; do not delete apps or secrets.

## AI flow plan amendment — include local StoryRun-lite contract snapshot — 2026-11-04

- Status: APPROVED / IN PROGRESS under the same direct owner instruction and scope.
- Reason: repository contract tests also validate `features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/openapi.json`; keeping that published local snapshot aligned is necessary to review the new story APIs and declared errors.
- Amended plan: `plan/AI_FLOW_SRS_ALIGNMENT_AND_TEACHER_DECK_POC_20261104.md`.
- Amended plan SHA-256: `88FB0E23FFC473FFC3E6643A1C21AB87F49F24EBF3851C8CF4AEE7C0EECEC0A3`.

## AI flow plan amendment - Bruno requests for story revision APIs - 2026-11-04

- Status: APPROVED / IN PROGRESS under the owner's direct instruction to fix the existing AI/API flow, align the contract with SRS business rules, test all relevant APIs, and report unavailable operations.
- Reason: the new Parent story-revision API must be runnable and reviewable through the existing StoryRun-lite Bruno collection as well as the published OpenAPI contract.
- Amended plan: `plan/AI_FLOW_SRS_ALIGNMENT_AND_TEACHER_DECK_POC_20261104.md`.
- Amended plan SHA-256: `EFEB1E83E2CCEBDCD4478D9F6AEB0C95D4FA63E18A2B88320F1CB72EC91C5C23`.

## Owner authorization - full non-video AI retest - 2026-11-04

- Status: APPROVED / IN PROGRESS by the owner's direct instruction to authorize fresh inference, test every AI workload except video generation, and fix/retest concrete failures until success or a clear blocker.
- Plan: `plan/AI_NONVIDEO_WORKLOAD_FULL_RETEST_20261104.md`.
- Approved plan SHA-256: `006FBBBADA49E2C37631DCBBDE5980F6809442DB4B70B75110E0943564D95D26`.
- This authorization supersedes the prior POC exclusions for TTS, Whisper, and synthetic SAM2 feasibility only. It does not authorize video generation, production enablement, real child data, or resolving lesson-suggestion role policy by inference.
- Approved run rules: all synthetic data; one initial inference per callable non-video workload and at most one corrective call after a concrete fix; stop after a 10-minute GPU queue wait or any unknown outcome; no GPU/provider fallback; keep workloads disabled; stop all Modal dev apps after evidence is saved and retain Volumes.
- No commit/push/merge authorization.

## Owner authorization - commit and push FEAT-063 worktree - 2026-11-04

- Status: APPROVED by the owner's direct instruction in the current conversation: “commit and push nhánh”.
- Amended plan: `plan/AI_NONVIDEO_WORKLOAD_FULL_RETEST_20261104.md`.
- Amended plan SHA-256: `77B9AF47D2F57C9D4CFCE279CDBFD436C2553EBF616A708EBA4F5483021C6EB0`.
- Approved scope: commit the reviewed, non-sensitive pending changes in the current worktree and push `codex/feat063-modal-backend-completion-20261103` to a same-named `origin` branch.
- Explicit exclusions: push to `dev`, force-push, `.env`/credentials/tokens/keys, real-child data, or edits to the canonical SRS.
- Required check: run `python tools/validate_repository_security.py` before commit.

## Owner authorization - 30-minute non-video AI queue retest - 2026-11-04

- Status: APPROVED by the owner's direct instruction to raise the wait to about 30 minutes and test again.
- Plan: `plan/AI_NONVIDEO_30MIN_QUEUE_RETEST_20261104.md`.
- Approved plan SHA-256: `E1C0B7AE0699635F44201ED816E2E8B39C08BD23E9B39B34D4CEA867C13A6606`.
- Scope: one fresh direct Modal worker dispatch for each previously capacity-blocked non-video workload; client-side result wait is capped at 1,800 seconds. Story generation uses a synthetic adult-confirmed Parent fixture. Existing HTTP/API contract results are not repeated because this retest changes only the worker wait. TTS/ASR are not repeated because they succeeded.
- Exclusions: all video inference, real child data, workload enablement, production configuration changes, canonical SRS changes, commit/push/merge.
- Safeguards: never retry an old or unknown call; each new unknown is cancelled and recorded; stop every Modal `dev` app and verify zero tasks afterward; retain shared Volumes.

## Owner authorization - Modal L4 Qwen story readiness diagnostic - 2026-11-04

- Status: APPROVED / IN PROGRESS by the owner's latest direct instruction to open one additional container, run health/model readiness checks, then test the AI request only after readiness.
- Plan: `plan/MODAL_L4_QWEN_STORY_READINESS_DIAGNOSTIC_20261104.md`.
- Approved amended plan SHA-256: `0D97D81769809F8E68362FF04B950ABC6E2EA67C6A844FEAFE563BAC624CECAB`.
- Amendment reason: Modal CLI confirms interactive `modal shell` is unsupported on Windows; use a temporary `modal run -` diagnostic app with the same dependency pins, L4 resources, model-volume mount, and loader settings. This changes execution mechanics only.
- Scope: one temporary L4 container at a time using the existing synthetic Qwen2.5 story worker specification; validate GPU, checkpoint marker/files, and model load before at most one fresh synthetic story request. Result wait is capped at 1,800 seconds; unknown calls are not retried.
- Exclusions: video, real child data, production changes, persistent scaling changes, code/SRS/API edits, commit/push/merge.
- Cleanup: stop any task-owned Modal `dev` app, verify zero tasks, retain shared Volumes.

### Execution closeout - 2026-11-04

- Status: COMPLETE WITH EXECUTION DEVIATIONS. The readiness diagnostic completed and identified GPU_L4 scheduling capacity as the story blocker. The approved plan allowed at most one fresh story request; two were accidentally dispatched because the first runner did not surface its call ID before a second instrumented request was sent. The first call also remained queued 63 seconds past the approved 1,800-second cap while its runner was interrupted. Both requests used synthetic fixtures, neither reached a worker/container or model inference, cancellation was requested, and the task-owned apps were stopped. No further calls were made.
- The second temporary runner saved its result record and then raised a local logging `TypeError` due to a duplicate `stage` argument. The report distinguishes this local wrapper error from the remote scheduling outcome.
- Evidence: `evidence/MODAL_L4_QWEN_STORY_READINESS_DIAGNOSTIC_20261104.md` and `evidence/assets/modal_l4_qwen_story_readiness_20261104/`.
- No product code, API, SRS, environment, persistent Modal scaling, model selection, or video inference was changed. No commit/push/merge was performed.

## Owner authorization - Modal serverless Parent story latency experiment - 2026-11-05

- Status: APPROVED / IN PROGRESS by the owner's direct instruction to try the serverless latency optimization after reviewing the Modal cold-start findings.
- Plan: `plan/MODAL_SERVERLESS_STORY_LATENCY_EXPERIMENT_20261105.md`, revision 1.
- Approved plan SHA-256: `E18267CD3B9D5AC5F75F3A5F80DAD6958AEFF9EDCFF3A36C2C00BF579F2C8711`.
- Approved scope: one FEAT-063 `dev` story worker experiment with ordered GPU choices L4 → L40S → A10; story-only Transformers parallel shard loading (4 workers); privacy-safe phase/GPU timing logs; 120-second scaledown; exactly one fresh synthetic Parent story call with a 300-second client wait limit; stop the task-owned language/audio app after the run.
- This is a narrowly scoped exception to D-130 and the prior no-fallback retest rule. It changes no production model/profile and does not enable any workload.
- Explicit exclusions: video or other AI workload inference, real child data, API/SRS/business-rule/schema changes, model/runtime pin changes, persistent warm containers, GPU snapshots, retries/duplicate calls, deletion of shared Volumes, commit/push/merge.
- Approval basis: owner's direct “ok, thử phương án đó đi” instruction and follow-up request to verify the screenshot's claims and find a faster serverless option.
- Cleanup: cancel and record the single call if it remains pending at 300 seconds; stop only the task-owned language/audio Modal `dev` app, verify no active task/container, retain shared Volumes.


### Execution closeout - 2026-11-05

- Status: COMPLETE WITH STORY OUTPUT FAILURE; the approved one-call scope was followed. Exactly one fresh synthetic Parent story request was dispatched; no video or other AI workload was called.
- Modal allocated an NVIDIA A10 through the ordered fallback configuration. The request reached model loading and token generation, then failed with the worker's existing `MODAL_MODEL_OUTPUT_INVALID` code. The output was not retried.
- The task-owned language/audio app was stopped; Modal reported zero tasks. Shared Volumes were retained. Full timing, limitations, deployment history, and evidence paths are in `evidence/MODAL_SERVERLESS_STORY_LATENCY_EXPERIMENT_20261105.md`.
- No commit, push, or merge was performed.

## Plan revision 43 — include all mounted Parent AI API routes — 2026-11-05

- Status: APPROVED / IN PROGRESS by the owner's direct clarification: “chạy bằng cả các API gọi AI để test luôn”.
- Feature: FEAT-063 — system architecture rearchitecture.
- Amended plan: `plan/PARENT_STORY_API_RETEST_20261105.md`, amendment revision 2.
  - Approved amended plan SHA-256: `0088A5AEA37D0B44D1A1DA291AF0CEE4CE469D0FEFED0692E8497F74C7B01B27`.
- Execution-closeout plan file SHA-256: `5C6985794D86E6FCCECADE18E9E4860D4B214C2CF8062BD6B5D4ED8AB1B8D46E` (records results/variance only; approved scope baseline above is unchanged).
- Added scope: one real synthetic Modal-backed HTTP attempt for each mounted Parent AI route: `POST /v1/story-runs/{run_ref}/assets` (`drawing.analyze`) and `POST /v1/story-runs/{run_ref}/story-revisions` (combined `story.generate`/`storyboard.generate`). Maximum one dispatch per workload, sequential, 300-second wait cap per call, no retry.
  - If drawing analysis fails, is unknown, or returns an unusable candidate, no VLM retry; the independent story API may be exercised once using a separate synthetic actor/run and deterministic vision fixture. Any such result must be labeled as fixture-backed, not a single uninterrupted AI end-to-end success.
- The other 11 StoryRun-lite operations remain synthetic/no-AI contract checks. Modal workloads without a mounted Parent HTTP API are reported as unavailable API surface and are not invoked. Video remains excluded.
- Execution closed 2026-11-05 with partial AI results: all 13 API operations covered; drawing VLM outcome unknown after the 300-second cap; story worker returned 502 after the factual lifecycle validator rejected output. Full measurements, contract findings, safe evidence, and verified shutdown: `evidence/PARENT_STORY_API_RETEST_20261105.md`.
- Cleanup: stop the task-owned drawing-VLM and language/audio `dev` apps and the disposable PostgreSQL container; verify zero Modal tasks and leave shared Volumes/services untouched.
- No product source, canonical SRS/OpenAPI, environment, secrets, workload enablement, shared database, commit, push, or merge is authorized by this amendment.

## Plan revision 40 — Modal Parent story content/metadata boundary — 2026-11-05

- Status: APPROVED / IN PROGRESS by the owner's direct instruction: “tiếp tục fix, đảm bảo đúng parser”.
- Feature: FEAT-063 — system architecture rearchitecture.
- Approved plan: `plan/MODAL_STORY_CONTENT_BOUNDARY_20261105.md`, revision 1.
- Approved plan SHA-256: `DEEC2263B3148A855AE090D1A513B1D57174CD9800FAC9BA8BC0E3A3F6F23917`.
- Scope: strictly parse a content-only internal Qwen output; deterministically add the five-scene 30-second timeline metadata; validate with the unchanged Parent worker parser, backend `StoryRevisionDraftV1`, and butterfly fact guard; run local focused checks; deploy only the FEAT-063 `dev` language/audio app; dispatch exactly one fresh synthetic Parent story call with a 300-second cap; stop the app and verify zero tasks; record privacy-safe evidence.
- Explicit exclusions: no video or other AI workload, backend/API/domain/SRS/schema or business-rule change, model/dependency change, real child data, raw prompt/output retention, environment/secrets edits, persistent scaling change, GPU snapshot, Volume deletion, retry/duplicate inference, commit, push, or merge.
- Approval basis: the direct owner instruction above authorizes continued fixing; this exact plan hash records the scope and one-call boundary. Plan revision 39's inference allowance was already consumed and is not reused.

### Execution closeout — Plan revision 40 — 2026-11-05

- Status: COMPLETE; one fresh synthetic Parent story call succeeded within the 300-second cap.
- Result: five scenes / 30,000 ms; worker parser, backend `StoryRevisionDraftV1`, and butterfly lifecycle validation passed. No video or other AI workload was called.
- Verification: 46 focused tests passed; Ruff and `py_compile` passed.
- Cleanup: Modal app `ap-WMgksDah3JVJTzQ5OU0cXn` is stopped with zero tasks. Scratch request objects were removed; shared Volumes were retained.
- Evidence: `evidence/MODAL_STORY_CONTENT_BOUNDARY_20261105.md` and `evidence/assets/modal_story_content_boundary_20261105/`.
- No commit, push, or merge was performed.

## Plan revision 41 — Parent StoryRun-lite API regression retest — 2026-11-05

- Status: APPROVED / IN PROGRESS by the owner's direct request to retest the APIs, record per-call timings, and report failures, contract drift, and business-rule mismatches.
- Feature: FEAT-063 — system architecture rearchitecture.
- Approved plan: `plan/PARENT_STORY_API_RETEST_20261105.md`, revision 1.
- Approved plan SHA-256: `E1C4CC11D117845CE00C225FC870EA9A357A722DA8C487D744CB4171D7B2F874`.
- Scope: run focused StoryRun-lite tests; use an isolated disposable PostgreSQL container and database; exercise all 13 mounted HTTP operations and expected negative cases; run one synthetic Parent story flow through HTTP and the actual Modal story adapter with a 300-second cap; record safe per-call timings/statuses; stop only task-owned services and verify shutdown.
- Explicit exclusions: no product/backend/SRS/OpenAPI change, no real-child data, drawing VLM/Teacher/video/other AI inference, no shared database/container shutdown, no `.env`/secret change, no workload enablement, no Modal Volume deletion, commit, push, or merge.
- Test-fixture boundary: subject understanding is supplied by a deterministic synthetic adapter; only the story worker is an actual Modal inference. The plan does not claim drawing-VLM coverage.


## Plan revision 38 ? Modal Parent story parser alignment ? 2026-11-05

- Status: APPROVED for the exact scoped implementation, focused tests, one fresh synthetic Parent story request, and shutdown described below.
- Approver: Project owner, direct 2026-11-05 instruction: ?ti?p t?c fix, ??m b?o ??ng parser?.
- Feature: FEAT-063 ? system architecture rearchitecture.
- Approved plan: `plan/MODAL_STORY_PARSER_ALIGNMENT_20261105.md`.
- Approved plan SHA-256: `171D9250B095495D7CEAA8DE3E019B8DFFBAC36619899D586AEAC2A301EA2F3F`.
- Approved scope: Align only the Parent Modal story worker with the existing FEAT-063/backend story contract; add pinned JSON-schema constrained generation; preserve all parser/business/fact rules; add focused local tests and safe reason-code diagnostics; deploy only the dev language/audio app; dispatch at most one fresh synthetic story request with a 300-second wait cap; stop the task-owned app and verify zero active tasks.
- Explicit exclusions: No video or unrelated AI calls, backend/API/SRS/schema/business-rule/model-pin/product-workload changes, prompt/output retention, real child data, environment/secrets changes, Volume deletion, commit, push, or merge. No retry after an unknown or rejected inference.
- Approval basis: The direct owner request above authorizes continued fixing; this exact hash records the implementation/test/one-call boundary.


## Plan revision 39 ? Modal Parent story parser alignment, plan revision 2 ? 2026-11-05

- Status: APPROVED as a clarification to Plan revision 38; implementation remains in progress.
- Approver: Project owner, direct 2026-11-05 instruction: ?ti?p t?c fix, ??m b?o ??ng parser?.
- Approved plan: `plan/MODAL_STORY_PARSER_ALIGNMENT_20261105.md`, revision 2.
- Approved plan SHA-256: `58C763076FA3310E051BBBC0A2D0F508007463B4C128FE88707DE5AAD06771DE`.
- Clarification: outer-whitespace normalization mirrors the existing backend Pydantic contract's `str_strip_whitespace=True`; no other coercion, truncation, or bypass is permitted. All approved call limits and exclusions in Plan revision 38 remain unchanged.

## Plan revision 44 — AI API coverage and Qwen3.5 Modal alignment — 2026-11-05

- Status: APPROVED / IN PROGRESS by the owner's direct request to align and implement the SRS AI APIs/workloads, use Qwen 3.5 VL, test the AI-backed APIs/models, and report failures; role clarification: “Admin + giáo viên; phụ huynh chỉ sửa bản nháp”.
- Feature: FEAT-063 — system architecture rearchitecture.
- Approved plan: `plan/PLAN_REV44_AI_API_COVERAGE_QWEN35_MODAL_20261105.md`.
- Approved plan SHA-256: `59C1CC86C59C6BDFEE1E87ACF58A634830EC1DA399A758FCD4D1A35682E73157`.
- Canonical SRS source: primary checkout's `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, SHA-256 `7D88057653104A5F3BFD791135DDD22144DEE033FF82928AA6F86775E6FC1AF4`; synchronize this exact v2.3-draft before implementation and preserve all history.
- Approved scope: additive SRS Q159 resolution; complete FEAT-063 AI API/workload mapping; dev-only Qwen/Qwen3.5-9B at immutable revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`; compatible Modal runtime; implement API/worker changes within plan allowlist; run bounded synthetic API and Modal AI verification; stop task-owned apps and record safe evidence.
- Role rule: Platform Admin and Teacher may initiate new lesson/activity/plan AI suggestions; Parent may edit an existing draft/personal copy but may not initiate a new generation job. AI outputs remain private drafts pending human review.
- Explicit exclusions: no production model promotion or workload enabling, real child data, actual `.env`/secret edits, destructive Volume/service actions, unrelated source changes, commit, push, or merge. Wan2.2 may not substitute for LTX-2.5; no video becomes playable unless every SRS gate, including final safety, passes.
- Approval basis: owner's current task instruction plus the direct role clarification returned to the pending Q157/Q159 question; this exact plan hash records the approved scope.

### Execution closeout — Plan revision 44 — 2026-11-05

- Status: COMPLETE WITH PARTIAL AI RESULTS; the exact one-attempt-per-workload and no-video limits were followed.
- Qwen3.5 runtime readiness passed. One Teacher Sketch Deck synthetic generation passed the worker contract. Drawing analysis failed with unusable decoded text. Story and lesson suggestion failed before generation because LMFE's Transformers adapter used a removed Transformers 4 import path; a direct LMFE 0.11.3 adapter now passes 59 focused Modal/parser tests and a Modal CPU import readiness call. Post-fix inference was not retried.
- VieNeu TTS produced a synthetic WAV in 23.501s; paired Whisper completed in 31.564s but changed “bướm” to “đứng”. FLUX.3 remained blocked by HTTP 401/no Modal Hugging Face Secret. SAM2 retained prior `UNKNOWN_NO_RETRY` after 1,800 seconds waiting for GPU_L4. Video was deferred and not called.
- Backend API/contract verification: 79 passed, 6 skipped. Main backend OpenAPI is 24 operations/17 paths with no AI dispatch; StoryRun-lite is a 13-operation fixture API whose AI tasks are process-local/non-durable. All workload flags remain disabled.
- Exact call IDs, timings, API gaps, contract findings, and run evidence: `evidence/AI_API_QWEN35_MODAL_VALIDATION_20261105.md` and `artifacts/AI_API_WORKLOAD_CATALOG_FEAT063_REV44_20261105.md`.
- Cleanup: task-owned drawing and language/audio Modal apps stopped with zero active tasks; shared model/scratch Volumes retained. No `.env`/secret changes, commit, push, or merge.
- Security scan: `tools/validate_repository_security.py` passed across 6,388 publishable files. Post-approval plan edits only removed absolute machine paths and recorded execution status; they did not change scope. Current plan file SHA-256 is `053C74FF5A27EA0A2F719922B5717089AF4B9945787974E73234CF5B5E1D4C50`. Current synchronized SRS copy after the additive Q159/Qwen3.5 amendment has SHA-256 `6BADEBAAD6C28239CA9B759CF17C57A0405D7242B45F3411F40B7E8FEBDC8381`.

## Plan revision 45 — Non-video AI flows end-to-end — 2026-11-05

- Status: APPROVED / IN PROGRESS by the owner's direct instruction: “fix tiếp luồng AI đi, đảm bảo là chạy đc hết, chưa cần làm vid thôi”.
- Feature: FEAT-063 — system architecture rearchitecture.
- Approved plan: `plan/PLAN_REV45_NONVIDEO_AI_END_TO_END_20261105.md`.
- Approved plan SHA-256: `F58C20E8CB82AB5AE1FE9370EDB58BFED2719CFCDCEA29909F0063E06C613A47`.
- Scope: repair and verify all non-video AI workers in the plan, including Qwen3.5 drawing/story/deck/lesson outputs, ASR/TTS, image generation and optional SAM2; fix supported API/job integration using existing authenticated/domain/persistence boundaries; test with synthetic fixtures and terminal Modal results; stop task-owned apps and record evidence.
- Role policy remains the owner-resolved Q159 rule: Platform Admin and Teacher can initiate lesson/activity/plan suggestions; Parent can edit an authorized existing draft/personal copy but cannot initiate new generation.
- Explicit exclusions: all video generation and post-video stages; production workload enablement; real personal/child data; secret-value access or `.env` edits; destructive Volume operations; unrelated changes; commit, push, or merge.
- Approval basis: the owner's direct instruction authorizes implementation and bounded dev inference tests. A model substitution is not authorized implicitly; FLUX.3 remains blocked pending owner choice if its Modal access cannot be configured.


## Plan revision 46 ? Qwen3.5-only active profile and FLUX Secret retest ? 2026-11-05

- Status: APPROVED / COMPLETE by the owner's direct instructions to retire Qwen 2 from active use, use Qwen 3.5, adapt the supplied Modal/Hugging Face Secret sample, test outstanding image workloads once, and stop the app afterward.
- Feature: FEAT-063 ? system architecture rearchitecture.
- Approved plan: `plan/PLAN_REV46_QWEN35_ONLY_FLUX_SECRET_RETEST_20261105.md`.
- Approved plan SHA-256: `4F796831148D134B2EABB1CBF791AE1D41C341C9D0C736BED4ECCDC11632B51F`.
- Scope: update active FEAT-063 SRS model selection to Qwen3.5 only while preserving historical evidence; bind FLUX.3 download to the owner-created Modal `dev` Secret `huggingface-secret` with required key `HF_TOKEN`; one model download and one synthetic inference each for Parent Sketch Guide and lesson visuals; validate outputs, record evidence, and stop the task-owned app.
- The sample's Stable Diffusion 1.5 model is not selected; FLUX.3 remains the SRS image model. No token value will be read or exposed.
- Explicit exclusions: video, optional SAM2 retry, repeated Qwen3.5/TTS/ASR calls, production enablement, real child data, historical-evidence deletion, Volume deletion, commit, push, or merge.


- Execution closeout SHA-256: `9dc252d80ce46aeddb9eca1c10da6ad60e52c11907441cea2a3c426ecd324f8f`.

## Plan revision 46A ? FLUX.3 component staging and failed-flow retest ? 2026-11-05

- Status: APPROVED / COMPLETE by the owner's direct instructions to fix the non-video AI flows, ensure they run, use Qwen3.5, and test the supplied Modal/Hugging Face Secret integration.
- Feature: FEAT-063 ? system architecture rearchitecture.
- Approved plan: `plan/PLAN_REV46A_FLUX_COMPONENT_FILES_AND_FAILED_FLOW_RETEST_20261105.md`.
- Approved plan SHA-256: `334ACE80E495EFD453BED980F78F5F9767ADD98C2F32617BCAD8DB87B74C2AE8`.
- Scope: stage and verify the pinned Diffusers FLUX.3 `transformer/` and `vae/` components omitted from the Rev46 allowlist; one checkpoint-staging call; then one synthetic inference each for the two image workloads that failed terminally in Rev46. No successful workload is repeated.
- The source failure was an incomplete checkpoint causing a missing transformer component, not Secret authorization or GPU scheduling. Use the existing `huggingface-secret` with required `HF_TOKEN`; do not inspect its value.
- No Qwen story/drawing/deck/suggestion, TTS/ASR, SAM2, video, production enablement, real child data, Volume/checkpoint deletion, commit, push, or merge.
- Approval basis: the owner's direct instructions in this conversation; exact scope and attempt cap are pinned by the plan hash above.

- Execution closeout SHA-256: `ab24410c6d4b3bcc69cb9acbaf9d58bf7b7ff5bcd6e6785ddb126b8ce375434e`.


## FEAT-063 Plan Rev50 ? local dev duplicate repair, Modal AI integration, and SRS authority

- **Status:** APPROVED / COMPLETE LOCALLY (not pushed) for the exact scope in Plan Rev50.
- **Approver:** Project owner, direct instruction on 2026-11-06 to fix duplicated `dev` commits without changing commit names; selected the full Modal AI branch and pending AI changes. The owner?s prior instruction to keep the newest FEAT-063 SRS canonical is also preserved.
- **Recorded timestamp:** 2026-11-06 06:13:08 Asia/Saigon.
- **Feature:** FEAT-063 ? system architecture rearchitecture.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV50_DEV_DUPLICATE_REPAIR_AND_MODAL_AI_INTEGRATION_20261106.md`.
- **Approved plan SHA-256 at authorization:** `404B793E8A00438882A8CC0532013EC5CD7BB188577EF35713A73DC5EF696936`.
- **Current plan SHA-256 after execution closeout:** `783E4EA92CED5BDFC041945653D5DC135CAD7E5D2EDF5830DEF627E31DCA473F`.
- **Scope:** retain a backup of the current dirty checkout; reset only the local `dev` ref to `origin/dev` to remove six patch-equivalent local copies; commit the 269 manifested pending Modal changes (excluding retained pytest scratch directories); integrate the full Modal branch and the published FEAT-063 SRS v2.4 branch while preserving all existing commit objects/messages; record evidence and run the required repository security validator.
- **Acceptance criteria:** AC50.1?AC50.7 in the hash-identified plan.
- **Exclusions:** no push, force push, remote history rewrite, rebase, amend, squash, commit-message change, tests or provider calls, cleanup of the scratch directories, or modification of unrelated dirty checkout content.
- **Approval basis:** direct owner instructions in the current and preceding conversation; this record authorizes only the exact plan scope above.

### Execution closeout ? local dev merge

- Local `dev` merge commit: `370cb26d6e8c99c126f4a5a16df132eaa70c8e70`.
- Full Modal and SRS v2.4 histories are present; zero patch-equivalent duplicates remain relative to `origin/dev`.
- Original dirty checkout is preserved on `backup/dev-before-dedup-20261106-575139a5`; the remote branch was not pushed or rewritten.
- Security validation passed; product tests and AI/provider calls were not run.

## Plan revision 43 — align SRS with the system under construction

- Status: `APPROVED` for the exact documentation scope in Plan Rev43.
- Approver: Project owner, direct instruction in this conversation on 2026-11-06: “update lại srs dựa trên hệ thống đang build hiện tại”.
- Recorded timestamp: 2026-11-06 00:48:54 Asia/Saigon.
- Feature: FEAT-063 — whole-repository architecture redesign.
- Approved plan: `plan/PLAN_REV43_AS_BUILT_SRS_ALIGNMENT_20261106.md`.
- Plan SHA-256 at authorization: `000A4D0C22BB92666C60C4597BB5B8AEB126E0D4C1F654B610909CC7BBDED945`. Current reviewed plan SHA-256: `1F10B3F447F7AFB59FAD847E6BE05F0C898B4CE4F6F51B0536258BBD1806F185`. Later edits record lifecycle completion and clarify AC2 with the AI/database boundary from the owner's adjacent table-use request; implementation scope remains documentation-only.
- Scope: update the canonical SRS and data-model companion with separately labeled implementation status; reconcile current model/role decisions; record local API/database and owner-supplied Modal dashboard observations; update canonical authority pointers and FEAT-063 tracking/evidence records.
- Acceptance criteria: AC1–AC7 in the hash-identified Plan Rev43.
- Exclusions: product/runtime/API/schema/data/migration/test/provider/deployment/secret changes; paid GPU calls; SRS sign-off; edits to preserved historical SRS bodies or unrelated work; staging, commit or push.
- Approval basis: the owner's direct request authorizes this documentation scope. It does not constitute formal product sign-off of the SRS.

## Plan Rev44 — publish the as-built SRS alignment

- Status: `APPROVED` for the exact documentation publication scope in Plan Rev44.
- Approver: Project owner, direct instruction in this conversation on 2026-11-06: “commit and push”.
- Recorded timestamp: 2026-11-06 05:29:51 Asia/Saigon.
- Feature: FEAT-063 — whole-repository architecture redesign.
- Approved plan: `plan/PLAN_REV44_PUBLISH_AS_BUILT_SRS_20261106.md`.
- Plan SHA-256: `F54CD43EC4E42BB8B46E698D74688BB161929450793EAB301DC8CDC342EA3E47`.
- Scope: publish only the exact 16 paths listed in Plan Rev44 on a new branch based on the fetched `origin/dev`; preserve unrelated staged/unstaged/untracked work in the original checkout.
- Acceptance criteria: AC1–AC5 in the hash-identified Plan Rev44.
- Exclusions: SRS sign-off; product/runtime/API/schema/database/migration/test/provider/deployment/secret changes; force-push or rewriting `dev`; publication of unrelated work.
- Approval basis: the owner's direct instruction authorizes commit and push of the Rev43 documentation package as scoped in Plan Rev44.


## FEAT-063 Plan Rev50 Addendum ? fast-forward publish repaired dev

- **Status:** APPROVED / COMPLETE (fast-forward pushed) for the exact publication scope in the addendum plan.
- **Approver:** Project owner, direct instruction on 2026-11-06: ?commit n?u c?n v? push.?
- **Recorded timestamp:** 2026-11-06 06:43:00 Asia/Saigon.
- **Feature:** FEAT-063 ? system architecture rearchitecture.
- **Approved addendum:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV50_ADDENDUM_DEV_FAST_FORWARD_PUSH_20261106.md`.
- **Approved plan SHA-256 at authorization:** `B8D2C5D83BD5766080207F1F2F8283713A915BFB9EABB49645B95143AE6F3C25`.
- **Current plan SHA-256 after execution closeout:** `5959C210013C294178BF574A8645E218421DDB63D024D5022C68597D049E5C7C`.
- **Scope:** security-validate and push only the repaired local `dev` to `origin/dev` using a regular fast-forward push; fetch and verify the exact resulting remote HEAD.
- **Acceptance criteria:** AC50A.1?AC50A.5 in the hash-identified addendum.
- **Exclusions:** force push/history rewrite, other refs, tests or provider calls, and unrelated checkout changes. This addendum supersedes only the earlier no-push boundary; all existing commit subjects/objects remain unchanged.


### Execution closeout ? publication

- `origin/dev` was fast-forwarded from `c98701b1e500906f396e773c79ec3bba55db2542` to `0d15b1a0ae6e5373354d7ac35cc163e41b55c42e`.
- Fresh fetch confirmed remote and local `dev` match at `0d15b1a0ae6e5373354d7ac35cc163e41b55c42e`; working tree was clean.
- Security validator passed; existing commit messages/objects were preserved.

## Plan Rev45 — SRS system and code alignment

- Status: `APPROVED` for the exact documentation-only scope in Plan Rev45; not SRS content sign-off.
- Approver: Project owner, direct SRS review/update request on 2026-11-06.
- Recorded timestamp: 2026-11-06 12:28:16 Asia/Saigon.
- Plan: `plan/PLAN_REV45_SRS_SYSTEM_CODE_ALIGNMENT_20261106.md`.
- Plan hashes: authorization `AD0554469128DD3DF13484DD7A78BAB42B99CB026C5D433D61D7D48E26950F1A`; approved scope addenda `E9F11167D6BFD1D9D341559B36C1003943460D48B98E0F88D0BDAFA3A2E0A385`, `3BE2B7AB19C69EB229768376B7BD1D041003C175D57B808BBE1BC2706D7BC453`, `1B8A1AD64F80A70D5BDA553311629787936900571B92BBB94433F83191C43175`; final local review `880EC6A2B3DB0B3FBC23A0386589EE2E1E3863E9295F3F1169D9BE7469752F46`.
- Published-port plan SHA-256: `53102EBB02521BC747DA0E79971B1AA636371C4830D501A173D9D7971930C05C`; Plan Rev51 approves its path reindex as EV-063-55 because EV-063-34 is already assigned on `origin/dev`.
- Scope: update the canonical SRS to v2.5-draft, reconcile existing AI directions and local source/runtime boundaries, and update matching authority/tracking records. The v2.5 SRS remains unsigned.

## Plan Rev51 — publish SRS v2.5 and reconcile latest dev source

- Status: `APPROVED` for the exact publication scope in Plan Rev51.
- Approver: Project owner, direct instruction in this conversation on 2026-11-06: “commit and push”.
- Recorded timestamp: 2026-11-06 17:16:12 Asia/Saigon.
- Approved plan: `plan/PLAN_REV51_PUBLISH_REV45_SRS_20261106.md`.
- Plan SHA-256 at authorization: `919CD35DC42973A5FE06C9D99D56DC851B4FCDB1313E1AF0612CB525D78116A8`.
- Scope: publish the v2.5-draft SRS/document package on a new branch from fetched `origin/dev` `4749451080f49243464d40a464b8f83a03ae77bb`; add a source-only §32.6 review of that tree; preserve newer remote records and exclude unrelated checkout work.
- Acceptance criteria: AC1–AC8 in the hash-identified Plan Rev51.
- Exclusions: code/API/schema/data/migration/test/build/provider/Modal/deployment/secret changes; SRS sign-off; push to `dev`; force-push/history rewrite; PR creation; and publication outside the manifest.
- Approval basis: the owner's direct request authorizes commit and push of this reviewed SRS package under Plan Rev51, not publication of unrelated work.

### Plan Rev51 execution close-out

- Recorded timestamp: 2026-11-06 17:33:39 Asia/Saigon.
- Final reviewed Plan Rev51 SHA-256: `06DC756E35F621F8232E89ABE8CDBFFD7FFEF493D0EF09050F1D25A2E26EE394`.
- Package commit `620386fb227e2d8b76c48e72ad22892e3b0c1c53` was pushed to `origin/docs/feat063-rev45-srs-code-alignment-20261106`; fresh fetch confirmed the remote SHA matched.
- The security validator passed before the package commit and first push, scanning 6,563 publishable files each time. No force push or `dev` update was performed.

## Plan Rev51 — bounded Modal AI and legacy API retest

- **Status:** APPROVED; execution COMPLETE WITH FINDINGS.
- **Approver:** Project owner, direct instruction on 2026-11-06 to continue fixing Modal AI, diagnose and raise only proven execution timeouts, minimize inference usage, test existing APIs, consolidate all results/products in one folder, stop used Modal apps, and commit coherent fixes as completed.
- **Recorded timestamp:** 2026-11-06 07:02:29 Asia/Saigon.
- **Approved plan:** `plan/PLAN_REV51_MODAL_AI_AND_LEGACY_API_RETEST_20261106.md`.
- **Approved plan SHA-256:** `B20103A217D7A9623E02279CE0BD82D5BC61141518D820FA683104057B1A6A2F`.
- **Execution closeout SHA-256:** `1CD7EC57885C20484DD1FBB166C917DABF586C58BEFBE49FF2D2B3FDB1BA953C`.
- **Scope and exclusions:** exactly as stated in Plan Rev51; no video calls, shared-database mutations, secrets, production enablement, unrelated legacy refactors, or push.

## FEAT-063 Plan Rev52 - non-video Modal AI reliability and observability

- **Status:** APPROVED for the exact scope in Plan Rev52.
- **Approver:** Project owner, direct instruction on 2026-11-06 to continue fixing all non-video Modal AI, add worker logs that reveal failure causes, and keep running verification until the non-video work is complete.
- **Recorded timestamp:** 2026-11-06 12:15:20 Asia/Saigon.
- **Feature:** FEAT-063 - system architecture rearchitecture.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV52_NONVIDEO_MODAL_AI_RELIABILITY_20261106.md`.
- **Approved plan SHA-256:** `9703A6CFE3AAF6108A1443B4E7F93805481475A0C60C64C50414106441158938`.
- **Current plan SHA-256 after formatting:** `6B3B1C25CD2A9974860A93551CDAD0FB3363DB38CB00D293ABB4818C9F0782D2`.
- **Scope and exclusions:** exactly as stated in Plan Rev52; all nine registered non-video workloads, safe worker/caller telemetry, current mounted AI API flows, synthetic verification and task-app shutdown; no video, real child data, production enablement, secret-value access, shared database writes or push.
- **Approval basis:** the owner's direct request authorizes the scoped implementation, synthetic Modal tests and local conventional commits after repository security validation.

## Plan Rev53 — one-shot SAM 2.1 gate retest

- **Status:** APPROVED for the exact scope in Plan Rev53.
- **Approver:** Project owner, direct instruction on 2026-11-06: “test lại sam2 đi, cho mở gate”.
- **Recorded timestamp:** 2026-11-06 18:36:29 Asia/Saigon.
- **Approved plan:** `plan/PLAN_REV53_SAM2_GATE_RETEST_20261106.md`.
- **Approved plan SHA-256:** `C2695A200FF15253E88E52CC458DC0DA718A51E2B9F8A4EC37BCED198D1EE8B5`.
- **Scope:** open only the `drawing.segment` envelope allowlist for its dedicated L4 Modal worker, keep `workloads.json` disabled, perform one CPU checkpoint preflight and at most one synthetic SAM2 GPU inference call with the existing 600-second worker timeout and 1,800-second caller wait bound, capture safe evidence and stop the app.
- **Acceptance criteria:** AC53.1–AC53.7 in the approved plan.
- **Exclusions:** production or product API enablement, real child media, repeated GPU calls, timeout increase without evidence, video, secret values, shared database writes, Volume deletion, merge or push.
- **Approval basis:** the owner's direct request authorizes this bounded development-only retest and the narrow allowlist fix; no further approval is needed within this scope.
- **Execution closeout:** COMPLETE WITH FINDINGS. Checkpoint preflight and one synthetic worker inference passed; visual review found only the central butterfly body in the mask. Product workload registry remains disabled. Dedicated Modal app stopped with 0 tasks. See `evidence/sam2_gate_retest_20261106/RESULTS.md`.

## Plan Rev54 - integrate SRS v2.5 and Modal AI into dev

- **Status:** APPROVED for the exact integration scope in Plan Rev54.
- **Approver:** Project owner, direct instruction on 2026-11-06 to merge the SRS-fix and AI branches into `dev`.
- **Recorded timestamp:** 2026-11-06 19:06:22 Asia/Saigon.
- **Approved plan:** `plan/PLAN_REV54_MERGE_SRS_V25_AND_MODAL_AI_TO_DEV_20261106.md`.
- **Approved plan SHA-256:** `C6882123DF3F1671AF7014784651E9F6A37AD799BA3763223BFC10C9E2A9F937`.
- **Inputs:** SRS branch `origin/docs/feat063-rev45-srs-code-alignment-20261106` at `fae180dcf3ea2771b41546aa6925b94636821df1`; AI branch `origin/feature/feat063-modal-ai-reliability-20261106` at `c6818490d0d889ab17dc9f8de3830987eb2a230d`.
- **Scope:** integrate both branches into `dev`, preserve commits and records, resolve only the two approval-register conflicts by keeping entries from both branches, validate security, then push normally to `origin/dev` and verify its tip.
- **Acceptance criteria:** AC54.1-AC54.8 in the approved plan.
- **Boundaries:** SRS v2.5 remains unsigned; SAM2 remains disabled in the product registry; no force push, history rewrite, video inference, additional AI calls, or unrelated branches.
- **Approval basis:** direct owner authorization for this integration and dev publication; this is not formal SRS content sign-off.

### Plan Rev54 local execution checkpoint

- Status: COMPLETE. Fast-forwarded local `dev` and pushed normally to `origin/dev`; the fetched remote matched integration commit `47e5308a5c547df8dab5f3c560f949ee925f441e`. A later closeout documentation commit was pushed normally as well.
- AI merge: `634e0e20f56cbfa6101ece6e67f3e4267a30ae92`; SRS merge: `6bbb375a359fb78f06585963b8ee9f7bfc2246ff`.
- Conflict handling retained both histories. SRS decision IDs D-144/D-145 were reassigned to D-148/D-149 to preserve all four records without duplicate IDs.
- Evidence: `evidence/EV-063-57_SRS_V25_AND_MODAL_AI_DEV_INTEGRATION_20261106.md`.
- Validation: `git diff --check` passed; `python tools/validate_repository_security.py` reported `REPOSITORY_SECURITY_VALID` with 6,731 publishable files scanned before commit and push. No force push or history rewrite.


## M2 S0-doc Task Approval — Draft 7 — 2026-11-06

- **Status:** APPROVED for S0-doc documentation scope only; NOT LAUNCHED. Creating this approval does not launch S0-doc. A separate execution session may create the evidence file only after a separate owner instruction.
- **Owner decision records:** D-142 through D-146 in DECISIONS.md.
- **Plan:** plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT7_20261106.md.
- **Plan SHA-256:** BB3C9F165731B1AEE261265270526B791FEE7BD622CE7D614514F2622DEFD099.
- **Baseline:** branch feature/feat063-be-foundation; HEAD dd70685eae58aaaefea3e567f5c23d09345a8513; parents 1e109b1726f327ac9383457b0dbdd535ef5c6518 and fb834771c24957bb8e289fb95d21410b14181e57. If HEAD changes, reconfirm before use.
- **Pinned inputs:** Draft 7 §§1.1–1.3; all 17 source paths and full SHA-256 values pinned there were rechecked before this approval was recorded.
- **Approved scope:** S0-doc only, as defined in Draft 7 §3: reconcile source requirements, schema mappings, owner decisions, B0 provenance and migration graph by reading source. No application/project commands or database access.
- **Read-only inputs (exactly the S0-doc row in Draft 7 §8):** Mọi tài liệu pin ở §1; features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md; features/FEAT-063-system-architecture-rearchitecture/evidence/COMMIT_WHITESPACE_NORMALIZATION_20261103.md; Draft 1/2/3/4 của plan này; backend/alembic/versions/20261104_story_revisions.py; backend/src/sketch2life/infrastructure/persistence/core_models.py; .claude/handoff/logs/GB2_T12_OFFLINE_20261105A/offline-check.txt (local, git-ignore); hồ sơ governance.
- **Existing files permitted to modify:** none.
- **One new file permitted:** features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S0_DOC_SOURCE_RECONCILIATION_20261106.md. This path was absent when approval was recorded. Record its SHA-256 only after the separate execution session creates it; do not predeclare a hash. No other new file is authorized.
- **Snapshot:** no separate snapshot file is authorized by this record; if the S0-doc evidence task determines a repository-standard manifest is required, stop and obtain a scope update before creating another file.
- **Command ceiling:** read-only file inspection and read-only Git metadata only: rev-parse, status, log, diff --name-status, diff --numstat, diff --shortstat, show, and SHA-256 calculation. No test, validator, mypy, Alembic, database connection, Modal/provider/network, stage/commit/push/merge, or edits to source, tests, migrations, SRS, DTR, roadmap or governance.
- **Exit criteria (copied from Draft 7 §3, S0-doc row):** Requirement có source ID; unknown được gắn nhãn; route/table/owner/M2-AT có crosswalk; B0 provenance được owner disposition hoặc vẫn block; các giới hạn evidence được ghi; không claim implementation approval.
- **Stop gate (copied from Draft 7 §3, S0-doc row):** Hash lệch, owner assumption bị coi là quyết định, hoặc cần DB/file ngoài approval thì dừng.
- Owner decision ảnh hưởng S0-doc: §9.7 B0 provenance đã có disposition (xác nhận tương đương cho file B0 plan, xem Ghi A mục 3), nên tiêu chí thoát S0-doc về B0 được thỏa; §9.5 schema convergence: chỉ lập bản đối chiếu để owner xem, không migrate. Các mục §9.1–9.4, §9.6 không chặn S0-doc.
- **Exclusions:** no S0-owner-run, S1a, S1b, S2, S3, M3–M6, implementation, source/test/migration change, DB work, provider or Modal work.
- **Validity:** this approval is limited to S0-doc and ends after the S0-doc evidence is created and independently reviewed. It does not authorize the separate execution session to start without a separate owner instruction. No later phase is opened.
- **Approval basis:** direct owner instruction in the current conversation, 2026-11-06; Draft 7 SHA-256 above.
## M2 S0-doc Evidence Correction Addendum — 2026-11-06

- **Status:** APPROVED for evidence correction only; NOT LAUNCHED. Creating this addendum does not launch the correction. A separate execution session may start only after a separate owner instruction.
- **Owner decision record:** D-147 in DECISIONS.md.
- **Relates to:** entry "M2 S0-doc Task Approval — Draft 7 — 2026-11-06" and evidence SHA-256 473D132DD8442A131A70AF7103A0346B50AA08A6D41E2562DA5FC4BA95667D9F (must match before any edit; stop if it differs).
- **Baseline:** branch feature/feat063-be-foundation; HEAD dd70685eae58aaaefea3e567f5c23d09345a8513. If HEAD changes, reconfirm before use.
- **Existing file permitted to modify:** features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S0_DOC_SOURCE_RECONCILIATION_20261106.md only.
- **Permitted passages (and nothing else):** (E1) the §1 bullet about the S0-doc Task Approval, to state that the approval's historical status is NOT LAUNCHED, that it does not launch S0-doc by itself, and that execution began from a direct owner instruction in conversation on 2026-11-06 not separately recorded in the repository records read; (E2) the BR-49 row of the §2 crosswalk and the F-01 bullet in §2.2, to list the tables outside the M2 BR-49 slice with DTR owners, attribute the lesson/feedback/quota scope to SRS §31.8.1, state that quota owner scopes remain open per DTR §14.2 item 10, and describe the roadmap listing accurately; (E3) the D-144 §9.7 bullet in §5, to state that the read-only comparison was performed by the coordinator per D-144, that D-144's Basis column also says "owner-supplied comparison", and that S0-doc records this per D-144 without re-verifying the snapshot (outside its allowlist). Optional E4 only if the owner says so in the execution instruction.
- **New files:** none. No other existing file may be modified.
- **Command ceiling:** read-only file inspection, read-only Git metadata and SHA-256 calculation, plus the single text edit of the evidence file. No test, validator, mypy, Alembic, database, Modal/provider/network, stage/commit/push/merge, or edits to source, tests, migrations, SRS, DTR, roadmap, Draft files or governance.
- **After the edit:** compute the new SHA-256 (do not predeclare it); a separate focused independent re-review of the diff and the six S0-doc exit criteria is required before any closure record.
- **Exclusions:** no S0-doc closure, no S0-owner-run, S1a, S1b, S2, S3, M3–M6, no implementation, DB work, migration, provider or Modal work.
- **Validity:** ends after the corrected evidence is independently re-reviewed. No later phase is opened.
- **Approval basis:** direct owner instruction in the current conversation, 2026-11-06 (Phương án A).

## M2 S0-doc Evidence Correction Addendum 2 — 2026-11-06

- **Status:** APPROVED for a second, narrower evidence correction only; NOT LAUNCHED. Creating this addendum does not launch the correction. A separate execution session may start only after a separate owner instruction.
- **Owner decision record:** D-149 in DECISIONS.md.
- **Relates to:** "M2 S0-doc Evidence Correction Addendum — 2026-11-06" and evidence SHA-256 E9048877338C74F123355AF938DBB1C8B2A6915EBC0D824CADF3180E8D44CF79 (must match before any edit; stop if it differs).
- **Baseline:** branch feature/feat063-be-foundation; HEAD dd70685eae58aaaefea3e567f5c23d09345a8513. If HEAD changes, reconfirm before use.
- **Reason:** independent re-review of the corrected evidence returned NEEDS_REVISION (0 P1, 2 P2, 1 P3), all in the E2a cell; E1, E2b and E3 are kept unchanged.
- **Existing file permitted to modify:** features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S0_DOC_SOURCE_RECONCILIATION_20261106.md only.
- **Permitted change (and nothing else):** replace the BR-49 "Logical tables / owners theo DTR" cell (section 2 crosswalk, evidence line 51) by the owner-approved text whose UTF-8 SHA-256 is 794B3DB496EB6F873F446ED1E737223EEAC380B4882783C5BCB0E98B43A33DB1. The text must stay on one line with no pipe character. This replacement supersedes the clause "state that quota owner scopes remain open per DTR section 14.2 item 10" of the first addendum.
- **Expected result:** evidence SHA-256 1BB71300A6A22487311A8D39EECB0EB1CE2664CB471EC2DAF45DA8DE2E244001, 146 lines, LF, no BOM, CR=0 (a deterministic check, not a pre-recorded outcome of review).
- **Must not change:** every other line of the evidence and every other file. No new files.
- **Command ceiling:** read-only file inspection, read-only Git metadata and SHA-256 calculation, plus the single text edit of the evidence file. No test, validator, mypy, Alembic, database, Modal/provider/network, stage/commit/push/merge, or edits to source, tests, migrations, SRS, DTR, roadmap, Draft files or governance.
- **After the edit:** a separate focused independent re-review of this one cell and the six S0-doc exit criteria is required before any closure record.
- **Exclusions:** no S0-doc closure, no S0-owner-run, S1a, S1b, S2, S3, M3–M6, no implementation, DB work, migration, provider or Modal work.
- **Validity:** ends after the corrected evidence is independently re-reviewed. No later phase is opened.
- **Approval basis:** direct owner instruction in the current conversation, 2026-11-06 ("Duyệt, soạn prompt").

## M2 S0-doc Closure Record — 2026-11-06

- **Status:** S0-DOC CLOSED at documentation scope only. No later phase is opened.
- **Owner decision record:** D-150 in DECISIONS.md.
- **Evidence:** features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S0_DOC_SOURCE_RECONCILIATION_20261106.md, SHA-256 1BB71300A6A22487311A8D39EECB0EB1CE2664CB471EC2DAF45DA8DE2E244001.
- **Review:** independent re-review of this exact evidence returned ACCEPT_WITH_CONDITIONS (0 P1, 0 P2, 2 P3); conditions and notes are recorded in D-150.
- **Baseline:** branch feature/feat063-be-foundation; HEAD dd70685eae58aaaefea3e567f5c23d09345a8513.
- **Not opened and not approved:** S0-owner-run (needs its own approval with database name/identity, runner, restore method, synthetic-only proof, read-only script and command), S1a, S1b, S2, S3, M3–M6, any implementation, database work, migration, provider or Modal work. OWNER_MODAL_CALL_APPROVED=NO is unchanged.
- **Carry-forward:** see D-150 (Draft 8 items and open route/code mismatches).
- **Approval basis:** direct owner instruction in the current conversation, 2026-11-06.

## M2 S0-owner-run Task Approval — 2026-11-07

- **Status:** APPROVED for one read-only owner-run only; NOT LAUNCHED. Creating this approval does not launch the run. The owner launches only by a separate instruction. No later phase is opened.
- **Owner decision records:** D-152 and D-153 in DECISIONS.md.
- **Approval spec:** plan/M2_S0_OWNER_RUN_APPROVAL_DRAFT6_20261107.md, SHA-256 6B4978C9B941C371D1EFFA654308C43B605A9823B056F2F89B6808005B82D9DE. This is the S0-owner-run approval spec, not the M2 plan with the same Draft number.
- **Plan:** plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT10_20261106.md, SHA-256 7539D642FFD95A9A21C99A0C17C5095FF1443E19538017A92789F631D633E2B1.
- **Baseline:** branch feature/feat063-be-foundation; HEAD dd70685eae58aaaefea3e567f5c23d09345a8513. If HEAD changes, reconfirm before use.
- **Script:** evidence/scripts/m2_s0_owner_run_readonly_20261107_r4.py, SHA-256 C28527CE531A4C1816B04BB4BA071B3F237CAD0AC7E95794A04CC86A2FABADB5. Any byte change voids this approval.
- **K3 static-AST manifest:** read-only inspection of exactly these 28 revision files; verify every SHA-256 again before launch. This is the owner-approved expansion from the 9 files in Draft 10 §8. Do not import revisions or application modules.

| Revision file | SHA-256 |
|---|---|
| backend/alembic/versions/20261014_0001_core_persistence.py | 55F415847B3E8AB5A96023CFC58C9C229056213AF92690865CF70F728290535C |
| backend/alembic/versions/20261014_0002_be1_runtime.py | 08014F5F5CD8A48FC21102090776128712EDEA1D04703853F9A0CC78CADAC520 |
| backend/alembic/versions/20261014_0003_canvas_payload.py | 194A831C661CA84C796557CCCF762715F6C0CC0E747521D588D1F30E1A5BB9E5 |
| backend/alembic/versions/20261014_0004_be1_constraint_names.py | AB15DFCE0738D994B14B337A03B34F7365BBBC67AFFE3BB01F24901F87BAFFFD |
| backend/alembic/versions/20261015_ai_0001_ai_jobs_schema.py | D86BD759FCB5DC644C94007FCA3650C6315903EC39EE4DA99579C4E23E656714 |
| backend/alembic/versions/20261017_ap_0001_policy_lifecycle.py | 81F84E9B3C4C7929018EB0A82ABED1DC2581811BB178EC6097E3134BBD8D765A |
| backend/alembic/versions/20261017_ap_0002_effective_scope.py | 35DBAA33A4F41EC69A01E03D688AF9B9238145EE0006D54CA67C115D0987CDE7 |
| backend/alembic/versions/20261017_ap_0003_resource_ledger.py | FEE3A90E27691B90B1D45E6DE7D14C3DB77311EBE86414051B55C75D02AB1924 |
| backend/alembic/versions/20261017_ap_0004_copy_inventory.py | 3EC8747A198941C9C4B36C4FDD0E08986355F0B2334589951EEA99BBF20AC2E7 |
| backend/alembic/versions/20261017_ap_0005_copy_evidence.py | 9E364BF938C2D6B6714FDE8C2A2527AAB84D3DD378C1AE16C0578FD86B9B8C12 |
| backend/alembic/versions/20261017_lc_0001_content_publication.py | DA2B372442A7CF234B8C1FC0FC7472B5A068FE8F832B6465C1BC1E4D2FE2F498 |
| backend/alembic/versions/20261018_ap_0006_copy_operations.py | B266744B3792E0E68347FA674B374A54D14CC33E4776106ADE91E2E407C447F7 |
| backend/alembic/versions/20261018_ap_0007_copy_delivery.py | 3BF400A165F5D681017FFE1AADEEAEB724BFFF5992289FB21331F5247C479E52 |
| backend/alembic/versions/20261018_ap_0008_delivery_authority.py | 9D8171F8B00C603FD350E32B6D6412B049A504F47B4D4F92355D654C86B71E05 |
| backend/alembic/versions/20261018_ap_0009_copy_resolution.py | 465A3421BC54895D2969AE95B1E3A9425689D1ED38B1CD6BCD8FE29D9B961A44 |
| backend/alembic/versions/20261018_kv_0001_knowledge_video.py | E7EFE124ECBFC5D1E280529DBA3B05EB2B00DCE04C24BF9EAC11BCE516B15D87 |
| backend/alembic/versions/20261018_vr_0001_video_review.py | 3E489443949C0934B414E4A69C6BD01B09782F4653042803C79291D66B415FC7 |
| backend/alembic/versions/20261019_ae_0001_activity_execution.py | 56993DC8CE1507D471ED3E3052F99A3A05B9D26C64E979822198946CD9EF9C30 |
| backend/alembic/versions/20261019_pa_0001_preset_automation.py | D2A8B958D6BD9411D040E3358F5568E2C728C1095D5395D55532916ACC5182E8 |
| backend/alembic/versions/20261019_vf_0001_video_failure.py | 0520CB0EB850D1BB4A267571F30937677908E505B77E221D1F0C90EE806FD178 |
| backend/alembic/versions/20261024_0005_classroom_srs_contracts.py | E533FC15447222C334A82CD162DC01FEB7B94221B402552D774CBD11E7D7289C |
| backend/alembic/versions/20261028_ll_0001_lesson_library.py | 733836723A95834C721E6CD0CA3527D73EA6EFE089B2F109A956EA484DFE1D83 |
| backend/alembic/versions/20261031_be1_synthetic_eligibility.py | 421F695FE49193C4A2EDCAC66B4461D8AFCB47B825813918E0083B21BC1483FC |
| backend/alembic/versions/20261101_be1_age_provenance.py | 2A634DC4DDF00326AFEF4079F7795A185D458DE2DB65BA6FD3C40291BBA5614E |
| backend/alembic/versions/20261102_pilot_vision.py | 6335AD224708AEC8251447A296458854B663FC7DD763EFB184E4AFF156E86BD9 |
| backend/alembic/versions/20261102_story_run_lite.py | D5E5F85EA3A7545538D6F1DE1E17D3869FD9AA7A543F870EAD54297F70D6E143 |
| backend/alembic/versions/20261103_story_upload_compat.py | F16346F5D0D320B22AF0767F387FE066ED3683D57DDD380804424B5A837CA166 |
| backend/alembic/versions/20261104_story_revisions.py | 3618BEF0ECCB0E01EE61F65E1065F7AE8EA6297FE0781D965588614D0F1C37F8 |

- **Owner-reported target and roles:** PostgreSQL native Windows instance, localhost/127.0.0.1 port 5433, database sketch2life, user postgres; expected major version 17. Dump header was reported as PostgreSQL 17.11. The service-to-port/database relationship has not been verified by this coordinator through a DB connection. Executor: Person 2 / AnhKhoaa157. Restore and database-preservation owner: Person 2 / AnhKhoaa157.
- **Dump and restore evidence (owner-provided):** dump file sketch2life-s0-owner-run-20261107.dump, outside the repository, SHA-256 AAD9B4CDBD0C1B11B017846A6B99449747981A8822443E0DC9BDA6B47740371A. Owner reports pg_restore --list returned a valid header, 583 TOC entries and PostgreSQL 17.11. A restore trial was not performed; the owner accepts this disposition. This listing does not establish that a restore was tested.
- **Mypy decision:** NOT RUN in this approval, by owner choice A. There is no mypy command, version command, mypy output file, or cache authorized here. The D-144 §9.6 baseline remains outstanding for a separate run or approval.
- **Approved scope:** exactly one execution of the r4 read-only inventory script and K1–K6 checks as defined in approval spec Draft 6. No migration, Alembic CLI, write, cleanup of the 58 historical rows, write-phase database, or S1a/S1b/S2/S3/M3–M6.
- **Read-only inputs:** the 28 revision files above for static-AST only; .gitignore; backend/pyproject.toml; backend/alembic/env.py was read in Draft 6's non-executable P2 appendix and is included only as read-only source context. This does not authorize any Alembic CLI or P2 operation. Other approval-spec and plan documents are read only.
- **Existing files permitted to modify:** none.
- **New files permitted only after a separate launch instruction:** inventory.json and inventory.txt in a new run directory under .claude/handoff/logs/M2_S0_OWNER_RUN_20261107/. The directory must not exist before launch; r4 creates it and does not overwrite outputs. No mypy outputs or cache are permitted under choice A. Runtime artifacts are never committed.
- **Command ceiling:** the single command below, at most one run and 1800 seconds. No retry without a new approval. Password is entered only at the script's hidden getpass prompt, never in the command line, environment, file, log, chat or transcript. The owner manually monitors the ceiling and presses Ctrl+C at 1800 seconds; r4 handles KeyboardInterrupt and exits 130. Timeout, interruption, missing output or absent safety verdict is NOT RUN, never PASS. No other command is authorized.

    & .\backend\.venv\Scripts\python.exe .\features\FEAT-063-system-architecture-rearchitecture\evidence\scripts\m2_s0_owner_run_readonly_20261107_r4.py --expect-db sketch2life --out-dir .claude\handoff\logs\M2_S0_OWNER_RUN_20261107 --alembic-method static-ast

- **Owner launch preconditions:** copy all 13 checks below into the separate launch instruction and tick each only after verifying it. Every checkbox remains unticked in this approval; any unticked or unverified item blocks execution.

- [ ] OWNER XÁC NHẬN: dump/restore point ngoài repo; ghi tên file/hash dump và đã thử restore hay chưa.
- [ ] OWNER XÁC NHẬN: PostgreSQL native instance, database và identity manifest khớp target đã duyệt; target dự kiến 127.0.0.1:5433, sketch2life, postgres.
- [ ] OWNER XÁC NHẬN: database chỉ dùng cho inventory read-only, không phải write-phase.
- [ ] OWNER XÁC NHẬN: current identity là postgres trên target đã xác minh. A2 history ghi role postgres là user/owner ngày 2026-11-03; owner chưa kiểm tra privilege hiện tại, nên least-privilege không được tuyên bố đạt. Không tạo role mới; script vẫn chỉ chạy transaction READ ONLY.
- [ ] OWNER XÁC NHẬN: password chỉ nhập tại getpass ẩn; không command line, env, file, log hoặc chat.
- [ ] OWNER XÁC NHẬN: PGHOST, PGPORT, PGUSER trong shell riêng đúng target; không có biến password/service/file/options override.
- [ ] OWNER XÁC NHẬN: script chạy trong shell riêng không chứa biến môi trường nào có ://; chặn rộng là chủ ý và có thể từ chối vì biến không liên quan, khi đó phải dùng shell sạch.
- [ ] OWNER XÁC NHẬN: .claude/handoff/logs/ đang bị ignore; chấp thuận script đọc .gitignore ngoài allowlist Draft 10 §8.
- [ ] OWNER XÁC NHẬN: git status trên backend/alembic/versions sạch trước khi chạy.
- [ ] OWNER XÁC NHẬN: 26-table A2 delta liệt kê trong Draft 6 khớp với tổng +58 rows; checkbox này xác nhận delta/count map, không tự xác nhận nguồn gốc synthetic. Bằng chứng synthetic-only cho application rows và bảng thiếu provenance là mục riêng.
- [ ] OWNER XÁC NHẬN: đã chọn P1 hoặc ghi K3 NOT RUN; không suy ra lựa chọn.
- [ ] OWNER XÁC NHẬN: dùng literal loopback; không bật `--allow-nonlocal-host` và không đổi connection để lách guard.
- [ ] OWNER XÁC NHẬN: mypy = NOT RUN under this approval, per owner choice A; no mypy command, mypy output artifact, or mypy cache is authorized.

- **Known conditions carried from Draft 6 review:** (1) the approved order is r4 only; mypy is NOT RUN under owner choice A; (2) postgres privilege is unverified and least-privilege is not met; (3) K1 checks the database name only, so the owner must independently verify the instance, port 5433, PostgreSQL 17 and user postgres, then compare actual version/table counts with the historical expectation of 117 tables, 82 total rows and 9 public.alembic_version rows as of 2026-11-03; far fewer tables suggests the wrong instance; (4) K5 never PASS; K5 for the 15 baseline application rows is NOT RUN because synthetic-only proof was not provided; (5) exit-code mapping and gate states are as in Draft 6, including LockNotAvailable outside K5 -> exit 6; (6) Docker container and native-service observations are historical, not identity evidence.
- **Review recommendations and amendments:** four independent chat-only reviews of Draft 1–4/r1–r4 and one quick Draft 6 review are recommendations, not approval. The quick review was session local_1d5dc947-6f8a-4602-b786-ce62296f1bd9, ACCEPT_WITH_CONDITIONS, 0 P1/0 P2/6 P3. Its amendments are folded here without editing Draft 6: P3-1 r4 creates the run directory before any authorized follow-up (none under choice A); P3-2 this record distinguishes Approval spec Draft 6 from M2 Plan Draft 10 and labels hashes; P3-3 format only; P3-4 the Draft 6 change inventory omitted the privilege wording change, fixed run-directory ID replacing the old placeholder, the new blocking-conditions section, removal of the age_source warning in K5, and the host-guard sentence; P3-5 POSTGRES_USER=portgres is the value observed in the stopped Docker container configuration, an apparent typo not independently verified, with all other values in that observation historical; P3-6 this record pins Draft 6's hash above. These notes do not change scope or grant authority beyond the single r4 run.
- **Exit criteria:** after the owner-run, compare inventory with the historical expectation and record discrepancies; a separate closure record is required to end this phase. K5 NOT RUN remains NOT RUN and is never reported as PASS.
- **Stop gate:** any pin/hash/manifest mismatch; mismatch in instance, version, port, user or DB identity; K1/K2 failure; any non-synthetic origin bucket; any need to write or migrate; missing safety verdict; or any unticked precondition means stop, report and leave the database untouched. Do not switch shells or rephrase commands to bypass a gate.
- **Exclusions:** no S1a, S1b, S2, S3, M3–M6; no implementation, migration, writes, cleanup of the 58 rows, Modal/provider, or network calls. Do not put password, connection URL, token or row data in chat, logs or Git. OWNER_MODAL_CALL_APPROVED=NO remains unchanged.
- **Validity:** limited to one run of the pinned r4 script. It ends after a closure record or if the script/spec hash changes. Every later phase needs its own Task Approval.
- **Approval basis:** direct owner instruction in the current conversation, 2026-11-07; D-152 and D-153; approval spec Draft 6, r4 and Plan Draft 10 hashes above.

## M2 S0-owner-run Closure Record — 2026-11-07

- **Status:** S0-OWNER-RUN CLOSED at the scope of the single read-only run; no later phase is opened.
- **Owner decision record:** D-154 in DECISIONS.md.
- **Run:** one owner-run execution of script r4 on 2026-11-07 (UTC 10:16:07), owner-reported exit code 0, inventory stop code NONE, under M2 S0-owner-run Task Approval — 2026-11-07.
- **Pins:** approval spec Draft 6 SHA-256 6B4978C9B941C371D1EFFA654308C43B605A9823B056F2F89B6808005B82D9DE; script r4 SHA-256 C28527CE531A4C1816B04BB4BA071B3F237CAD0AC7E95794A04CC86A2FABADB5.
- **Results (local, git-ignored, not committed):** inventory.json SHA-256 E4529F541002D840C3F2E1D25F24D00E7B92A65720E3036EB59BA71FD04DB64F; inventory.txt SHA-256 E37B07E82DB8E22B53F93D12F9400912271AD25135EB4103A99DFA2EDAB51025.
- **Observed inventory:** database sketch2life, PostgreSQL 17.11; 12 schemas, 117 tables, 986 columns, 460 constraints, 205 indexes, 231 CHECK constraints, 82 total rows across 37 populated tables, including 9 rows in public.alembic_version. The 117-table per-table count map matches the A2 post-failed-teardown snapshot exactly.
- **Gate outcomes:** K1 PASS (database name only), K2 PASS, K3 FAIL, K4 COLLECTED (source comparison NOT RUN), K5 NOT RUN, K6 COLLECTED (definitions only), K7 NOT RUN. These are the recorded gate states; they do not establish synthetic-only proof, schema equivalence or mypy.
- **K3 discrepancy:** database revision 20261103_story_upload_compat differs from static source head 20261104_story_revisions; no migration was run. Schema story has only command_receipts, review_decisions, run_inputs, runs and understanding_revisions.
- **K5 limitation:** only public.be1_managed_profiles and public.be1_synthetic_eligibility_proofs have data_origin (one SYNTHETIC_DEV row each, no non-synthetic bucket); 115 tables lack data_origin. Owner proof for 15 baseline application rows was not supplied, so K5 remains NOT RUN for that scope. The inventory k5_not_run_tables list is empty, which is not proof.
- **K6 collected definitions (not interpreted):** ck_be1_profile_age_months: CHECK (age_months >= 36 AND age_months <= 155); ck_be1_profile_origin_consent_refs: CHECK (data_origin::text = 'REAL'::text AND consent_id IS NOT NULL AND consent_purpose_ref IS NOT NULL OR data_origin::text = 'SYNTHETIC_DEV'::text AND consent_id IS NULL AND consent_purpose_ref IS NULL OR data_origin::text = 'LEGACY_UNCLASSIFIED'::text). F-6 remains open for owner decision.
- **Not opened and not approved:** S1a, S1b, S2, S3, M3–M6, implementation, migration, any write, cleanup of the 58 rows, mypy run, provider or Modal work. OWNER_MODAL_CALL_APPROVED=NO is unchanged.
- **Carry-forward:** K4 source comparison and F-1, F-2, F-4, F-6, C5 and age source to the S1a Task Approval; D-144 §9.6 mypy baseline remains outstanding; schema-only copy database for S1a/S2 is not created; dump remains outside the repository. See D-154.
- **Approval basis:** direct owner instruction in the current conversation, 2026-11-07; D-152 and D-153; approval spec Draft 6 and script r4 hashes above.


## M2 Baseline Run Approval — 2026-11-08

- **Status:** APPROVED / NOT LAUNCHED. This approval is limited to the single owner-run baseline procedure pinned below; it does not establish that the baseline was run or accepted.
- **Owner decision record:** D-159, B7.
- **Specification:** `plan/M2_BASELINE_RUN_APPROVAL_FINAL_20261107.md` — SHA-256 `A671DBD85B9622CB754C5CECB807BBBBA2C920CD76F0A22ABBA44F4A12DC1A18`.
- **Launch instruction:** `plan/M2_BASELINE_LAUNCH_INSTRUCTION_20261107_R2.md` — SHA-256 `C132EF91AD7C06A82EB27D09D82B0662E77CDD795B9BC2F935B281822EAA9178`.
- **Independent review:** cold, read-only review returned READY (0 P1, 0 P2, 1 P3) in session `01a1b996-cc5d-7f80-8cb6-69a7fa3c0b1c`. The reviewer verified the pinned specification, launch instruction and 17 source pins. The non-blocking P3 records that Git `--quiet` emitted non-fatal stderr warnings in the review workspace while both commands returned 0, whereas the launch instruction describes Boolean-only output. This observation is recorded here; the pinned instruction was not changed.
- **Execution boundary:** owner-run only, NOT LAUNCHED. The owner must satisfy and tick every run-time precondition at launch and follow the pinned command, capture, timeout and stop gates. This entry does not approve S1a-T, write a Baseline Closure Record, or open any later phase. `OWNER_MODAL_CALL_APPROVED=NO` remains unchanged.
- **Approval basis:** direct owner goal message, 2026-11-08; no owner name or signature recorded.

## M2 Baseline Closure Acceptance — 2026-11-08

- **Status:** ACCEPTED by the owner for the exact baseline closure record only: `plan/M2_BASELINE_CLOSURE_RECORD_20261108.md`, SHA-256 `65588C6876F653F3A0B17E227B8845E63EA2F6C77FB78756A91925DEBA9626D6`. The record itself is unchanged; this append-only entry records the subsequent owner acceptance and the provenance correction below.
- **Independent review:** round 3 returned `READY_FOR_OWNER_REVIEW` (0 P1, 0 P2, 2 P3). The two P3 notes are retained without editing the Closure Record: the phrase “log directory above” at line 17 could be more explicit; and the static evidence could mention that `test_synthetic_eligibility.py` directly exercises `PostgresCoreStore.create_synthetic_profile` with inputs rejected by the synthetic-identity guard before its session block. These are review notes, not implementation approval.
- **Required provenance correction (this entry only):** the reading/scanning attributed to the owner in Closure Record lines 96, 98 and 108 was performed read-only by the Claude coordinator: inspection of `backend/tests/unit/test_be1_fact_reader.py` lines 252–272, the 24 baseline logs, and the 25 files under `tmp/M2_BASELINE_RUN_20261107/`. The owner read the reported results and accepted the listed narrow exemptions as owner decisions; the owner did not perform those scans. No URI, credential or token values are reproduced here.
- **Accepted test and static-check limits:** for acceptance, pytest is `NOT RUN / NO VERDICT` because `pytest.stdout.txt` has no official aggregate summary; its exit code 1 is raw data only, and no passed-test count is inferred. Strict mypy reported 255 errors across 50 files and Ruff reported 202 findings; both are baseline data, not PASS. `git diff --check` exited 2.
- **Accepted sequence deviation:** the three validators and `git diff --check` were run after pytest ended without an official summary, despite the stop condition in the baseline specification. This deviation is disclosed and accepted as part of this closure; it does not change pytest to PASS or provide a pytest verdict.
- **Accepted timing/provenance deviation:** `DECISIONS.md` was written at 13:29:01 before the owner-run baseline interval (13:34:40–13:44:28). The R3 launch instruction, approval specification and launcher were written at 13:38:49, 13:42:48 and 13:43:01 during that interval. All 17 pinned source hashes still matched after the run. This is a disclosed timing overlap, not a pin mismatch.
- **Phase boundary:** this acceptance closes only the baseline closure record. It does not launch or approve S1a-T, S1a-P, S1b, S2, S3 or M3–M6; no implementation, database write, migration, provider or Modal work is authorized. A separate Task Approval and launch instruction remain required for any later phase. `OWNER_MODAL_CALL_APPROVED=NO` remains unchanged.
- **Approval basis:** direct owner instruction in the current conversation, 2026-11-08, accepting the exact reviewed Closure Record with the provenance correction above.

## M2 S1a-T Approval — 2026-11-08

- **Status:** APPROVED / NOT LAUNCHED. This entry records approval of the S1a-T task defined by the pinned R5 specification. No S1a-T launch was performed by the coordinator.
- **Owner decision record:** D-159 B7 and D-162. This entry is recorded only after the independent R5 round-3 review returned READY with 0 P1 and 0 P2.
- **Approval specification:** `plan/M2_S1A_T_APPROVAL_SPEC_FINAL_20261107_R5.md` — SHA-256 `934D2E69DAEA293CC68BDD55EED8713CE59E0EAB0E1CA758FB9420B34EAC9345`.
- **Launch instruction:** `plan/M2_S1A_T_LAUNCH_INSTRUCTION_20261107_R5.md` — SHA-256 `9CBCE84B4AB579D0857AC153DC2FC59DAFB255468E1AFC29D338566B9EDAFAAC`.
- **Guarded owner launcher:** `evidence/scripts/m2_s1a_t_owner_run_20261107_r5.py` — SHA-256 `DA7F4A4D6502F927C7EC1F29F112A283E7960F831F2183CD07C09E61EE488FA0`.
- **Baseline prerequisite:** The owner-accepted `M2 Baseline Closure Acceptance — 2026-11-08` at line 909 above satisfies the S1a-T baseline-closure prerequisite. It accepts only `plan/M2_BASELINE_CLOSURE_RECORD_20261108.md`, SHA-256 `65588C6876F653F3A0B17E227B8845E63EA2F6C77FB78756A91925DEBA9626D6`.
- **Independent review:** Fresh cold read-only review, round 3 (final), returned READY (0 P1 / 0 P2 / 1 P3), session `01a1badf-4d36-7c02-8a4c-e7ab2ae6c998`. The non-blocking P3 notes inherited R2/R4 launcher-version wording at specification lines 64 and 79; the reviewed behavior is present in R5 and this note does not change the approved scope.
- **Execution boundary:** APPROVED / NOT LAUNCHED. This entry records no execution. Any owner-run must follow the exact pinned R5 launch instruction, including its launch-time gates and stop conditions. `OWNER_MODAL_CALL_APPROVED=NO` remains unchanged. S1a-P, S1b, S2, S3 and M3–M6 remain closed.
- **Approval basis:** direct owner instruction in the current conversation, 2026-11-08, conditional on the independent R5 review returning READY with 0 P1 and 0 P2; D-159 B7 and D-162.

## M2 S1a-T Approval Addendum — 2026-11-08

- **Status:** APPROVED / NOT LAUNCHED. This addendum resolves the route and age-validation wording conflict for the already approved S1a-T scope. No implementation, test, database, Alembic, or launcher execution had occurred when this addendum was recorded.
- **Owner decision record:** D-163 in `DECISIONS.md`.
- **Route resolution:** The sole existing `POST /api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles` handler is the R5 Teacher synthetic profile/enrollment operation. It will implement the R5 contract; the former consent-bound `ADULT_DECLARED` create behavior is removed from this method/path. Consumers outside the repository (frontend and Bruno) are NOT VERIFIED. `ADULT_DECLARED` remains a valid model/check/reader value.
- **Age compatibility:** Keep `validate_age_months` default at 36–155 for existing callers; apply an explicit maximum of 120 only to new Teacher input and `CreateProfileRequest`. Preserve existing values and the database CHECK; no clamp, `child_age.py`, or migration.
- **R5 artifacts (unchanged):** specification `plan/M2_S1A_T_APPROVAL_SPEC_FINAL_20261107_R5.md` SHA-256 `934D2E69DAEA293CC68BDD55EED8713CE59E0EAB0E1CA758FB9420B34EAC9345`; launch instruction `plan/M2_S1A_T_LAUNCH_INSTRUCTION_20261107_R5.md` SHA-256 `9CBCE84B4AB579D0857AC153DC2FC59DAFB255468E1AFC29D338566B9EDAFAAC`; guarded launcher `evidence/scripts/m2_s1a_t_owner_run_20261107_r5.py` SHA-256 `DA7F4A4D6502F927C7EC1F29F112A283E7960F831F2183CD07C09E61EE488FA0`.
- **DECISIONS pin supersession:** Current `DECISIONS.md` SHA-256 is `$decisionHash`. By owner decision D-163, this current hash supersedes only the old `DECISIONS.md` hash stated in R5 §1/§5 and the R5 launch instruction. Those R5 files remain unchanged; their other pins and the three artifact hashes above are unchanged. The R5 launcher does not validate a `DECISIONS.md` hash.
- **Execution boundary:** This addendum preserves APPROVED / NOT LAUNCHED. Continue implementation only after an independent cold review of D-163 and this addendum returns READY with 0 P1 and 0 P2, then within the existing S1a-T scope. It does not approve the owner PostgreSQL launcher; that remains owner-only and is not to be run by the implementation session. `OWNER_MODAL_CALL_APPROVED=NO` remains unchanged. S1a-P, S1b, S2, S3 and M3–M6 remain closed.
- **Approval basis:** direct owner instruction in the current conversation, 2026-11-08; D-163; existing S1a-T Approval entry.

## M2 S1a-T Approval Addendum 2 — 2026-11-08

- **Status:** APPROVED / NOT LAUNCHED. This addendum records owner dispositions only; no implementation, test, database, Alembic, or launcher execution occurred as part of recording it.
- **Owner decision record:** D-164 in `DECISIONS.md`; D-164 corrects D-163's provenance wording without modifying D-163.
- **Bruno 013 disposition:** Bruno 013 is an in-repository historical artifact, treated like Bruno 004/005 under R5 §5. It remains unchanged and outside the S1a-T edit allowlist. Its old request body is documented debt, not PASS; no R6 is created.
- **Consumer provenance correction:** the Teacher UI profile service calls GET list only; Bruno 013 is in this repository. Actual POST consumers outside the repository remain NOT VERIFIED.
- **Prior pin correction:** the DECISIONS pin in the preceding Addendum 1 at line 939 contains a literal dollar-prefixed `decisionHash` placeholder caused by string interpolation; it is not a SHA-256 value. This addendum records the actual DECISIONS.md SHA-256 after D-164 as `E1F5A5ACCFF412302CE1A543F2FB597D38AC8A0D6E4CCF7E1FC4C3F4B9AA5180`. By owner decision, that hash supersedes only the old DECISIONS.md pin in R5 §1/§5 and the R5 launch instruction. The R5 files remain unchanged; no other pin is superseded. The R5 launcher does not validate a DECISIONS.md hash.
- **R5 artifacts unchanged:** specification `plan/M2_S1A_T_APPROVAL_SPEC_FINAL_20261107_R5.md` — SHA-256 `934D2E69DAEA293CC68BDD55EED8713CE59E0EAB0E1CA758FB9420B34EAC9345`; launch instruction `plan/M2_S1A_T_LAUNCH_INSTRUCTION_20261107_R5.md` — SHA-256 `9CBCE84B4AB579D0857AC153DC2FC59DAFB255468E1AFC29D338566B9EDAFAAC`; guarded launcher `evidence/scripts/m2_s1a_t_owner_run_20261107_r5.py` — SHA-256 `DA7F4A4D6502F927C7EC1F29F112A283E7960F831F2183CD07C09E61EE488FA0`.
- **Execution boundary:** APPROVED / NOT LAUNCHED remains unchanged. Continue only if a new independent cold review of D-164 and this addendum returns READY with 0 P1 and 0 P2, then within the existing S1a-T scope. The owner launcher remains owner-only and must not be run by the implementation session. `OWNER_MODAL_CALL_APPROVED=NO`; S1a-P, S1b, S2, S3 and M3–M6 remain closed.
- **Approval basis:** direct owner instruction in the current conversation, 2026-11-08; D-164; existing S1a-T approval entry.

## M2 S1a-T Approval R6 — 2026-11-08

- **Status:** APPROVED / NOT LAUNCHED. This entry records the R6 approval and does not launch S1a-T.
- **Owner decision record:** D-165 authorizes the narrow R6 revision. D-163 and D-164 continue to govern the sole Teacher profile handler and Bruno 013; no new product rule is introduced here.
- **R6 approval specification:** `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S1A_T_APPROVAL_SPEC_FINAL_20261107_R6.md` — SHA-256 `664E300F5CAA01DA41E17F5E48025F58D2681F6A676E2CAD1973859F19E04479`.
- **R6 launch instruction:** `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S1A_T_LAUNCH_INSTRUCTION_20261107_R6.md` — SHA-256 `F8E2DB8463AC6511C9D0EFC716A1E9076A390EBBC5DF1043125EBB8B989023D9`.
- **R6 guarded launcher:** `features/FEAT-063-system-architecture-rearchitecture/evidence/scripts/m2_s1a_t_owner_run_20261107_r6.py` — SHA-256 `F3D7992FABFEB848085C5BBD55780EE158894BA197DBA054CD205487219B7A55`.
- **Decision pin:** `DECISIONS.md` through D-165 — SHA-256 `08581083E65E2EF5FF3D74EBE419517098FD5D6020C9F68D90E432FECE308F0F`; this replaces the R5 decision pin for R6 execution.
- **Historical records:** the R5 approval and its two addenda remain historical. R6 artifact pins supersede R5 for execution; all other approved R5 scope, allowlist, business rules, ceilings and stop gates remain in force, with D-163 and D-164 continuing to govern.
- **Baseline prerequisite:** the `M2 Baseline Closure Acceptance` entry at line 909 remains ACCEPTED and its closure record SHA-256 is `65588C6876F653F3A0B17E227B8845E63EA2F6C77FB78756A91925DEBA9626D6`.
- **Independent review:** fresh cold read-only R6 review, round 1, session `01a1bc07-9363-7a80-917f-44f1124382ad`: READY, 0 P1, 0 P2, 1 P3. The non-blocking P3 at `backend/tests/contract/test_be1_synthetic_pilot.py:326` notes the `secrets.token_hex(12)` AST assertion does not explicitly reject keyword arguments; reviewer suggested `assert not token_hex_calls[0].keywords`. This note records the finding; it does not modify source or tests.
- **Prior offline attempt:** NOT RUN / NO VERDICT because its official pytest summary was suppressed by the redundant quiet flag; preserve the existing logs. The stdout SHA-256 is `424952E38FEA88EAA90959CEF7C7F65DE9563B9B25C45160B423190BD38127D5`.
- **Execution state:** no R6 test rerun, launcher, database, Alembic, validator, mypy, Ruff, Docker, Modal or provider operation occurred. The two existing output base directories remain a launcher stop gate and must be resolved by the owner before any future launch. A corrected pytest rerun still requires a separate owner instruction.
- **Not opened:** S1a-P, S1b, S2, S3 and M3-M6. `OWNER_MODAL_CALL_APPROVED=NO` remains unchanged.
- **Approval basis:** owner authorization D-165 and the round-1 independent R6 review recommendation; approval is limited to S1a-T and remains NOT LAUNCHED.

## M2 S1a-T Approval Addendum 3 — 2026-11-08

- **Status:** APPROVED / NOT LAUNCHED. This addendum approves only the post-code verification continuation described here; it does not launch S1a-T or the PostgreSQL launcher.
- **Owner decision record:** D-166 in `DECISIONS.md`.
- **Decision pin supersession:** the new `DECISIONS.md` SHA-256 is `758A76E4C949B6EFD6107E66A2283D1AB0E3C95B318F4B52C29E2EB0EEEEBB29`. It supersedes the prior D-165 decision pin for the DECISIONS rows in R6 section 1 and section 5 and the DECISIONS row in the R6 launch instruction. The R6 specification, launch instruction and launcher artifact hashes are unchanged; the R6 files themselves are not edited by this addendum. The R6 launcher does not check the DECISIONS hash directly.
- **R6 artifacts unchanged:** specification SHA-256 `664E300F5CAA01DA41E17F5E48025F58D2681F6A676E2CAD1973859F19E04479`; launch instruction SHA-256 `F8E2DB8463AC6511C9D0EFC716A1E9076A390EBBC5DF1043125EBB8B989023D9`; launcher SHA-256 `F3D7992FABFEB848085C5BBD55780EE158894BA197DBA054CD205487219B7A55`.
- **Authorized offline verification:** one corrected offline pytest invocation using the R6 command without a redundant explicit `-q`; the previous attempt remains invalid NOT RUN / NO VERDICT, with its logs preserved. Each remaining post-code command in R6 section 3 may run once. Only a genuine code failure with an official result or an independent review request permits an in-allowlist fix and one additional run of affected commands (two total per command). No retry to obtain a pass, flag/shell/test-selection change, or further retry is authorized.
- **Output preservation:** new logs and caches may be placed under the two existing ignored S1a-T output bases using unique new names only. Existing files must not be overwritten, removed or edited. The owner will rename both output bases before any PostgreSQL launcher use.
- **Review:** independent cold code review must use a new session, up to three rounds under D-166. A round 3 result with P1/P2 requires stopping and returning to the owner.
- **Execution state:** no post-code command has been run under D-166 at the time of this addendum. PostgreSQL tests, the owner launcher, DB/Alembic, Modal/provider are not authorized here. `OWNER_MODAL_CALL_APPROVED=NO` remains unchanged.
- **Not opened:** S1a-P, S1b, S2, S3 and M3-M6 remain closed. The S1a-T PostgreSQL launcher remains owner-only.
- **Approval basis:** direct owner authorization after R6 approval, current conversation; D-166.
## M2 S1a-T Approval Addendum 4 — 2026-11-09

- **Status:** APPROVED / NOT LAUNCHED. This addendum authorizes only the bounded offline correction and checks recorded below; it does not launch S1a-T or the PostgreSQL launcher.
- **Owner decision record:** D-167 in `DECISIONS.md`.
- **Decision pin supersession:** DECISIONS.md SHA-256 after D-167 is `040FB22E7BA2B63A3EC9492216FB97FD73C0183F33547FD366229A59A8822A11`. It replaces the preceding DECISIONS pin for R6 sections 1 and 5 and the DECISIONS row in the R6 launch instruction. The R6 files remain unchanged.
- **Static root-cause record:** `tmp/m2-s1a-t-impl/S1A_T_STATIC_ROOT_CAUSE_20261109.md`, SHA-256 `C894DF2B076D5F6F9D12A2DE3351A3CD7B23AE41F84F00EE29375001B039F075`.
- **R6 artifact pins unchanged:** specification `664E300F5CAA01DA41E17F5E48025F58D2681F6A676E2CAD1973859F19E04479`; launch instruction `F8E2DB8463AC6511C9D0EFC716A1E9076A390EBBC5DF1043125EBB8B989023D9`; guarded launcher `F3D7992FABFEB848085C5BBD55780EE158894BA197DBA054CD205487219B7A55`.
- **Permitted test edit:** exactly the three D-167 locations in `backend/tests/contract/test_app_composition.py`; each reads `application.state.runtime_openapi_schema["paths"]` after exactly one `application.openapi()` call. Expected sets, assertions and exact-delta checks remain unchanged.
- **Composition/OpenAPI:** exactly one final third invocation under the R6 section 3 command, with new run id and basetemp/log names. FAIL, absent official summary, timeout, PermissionError, or missing safety verdict is a stop; no further composition invocation is authorized.
- **Mypy:** accepted only by R6 section 6 normalized baseline comparison: 255 diagnostics / 50 files; 0 new / 0 vanished. Mypy is not rerun. Exit 1 is NO PASS, never PASS; 8 allowlisted diagnostics remain untouched baseline debt.
- **Remaining post-code checks:** run Ruff on the R6-approved Python paths, `validate_harness.py`, `validate_repository_security.py`, `validate_architecture.py`, and `git diff --check` once each, using the R6 commands and ceilings. A genuine code failure with an official result or independent-review request may authorize one in-allowlist fix and one additional invocation of the affected non-composition command only; no shell/flag/selection changes and no retry to obtain a pass.
- **Output and review:** preserve all existing logs. Write new outputs under the two existing approved output bases with unique names only. After the required commands return official results, use a new cold read-only independent review session, under D-166 limits (maximum three rounds and existing stop gates).
- **Execution state at approval:** no command has yet run under D-167. No PostgreSQL, launcher, database, Alembic, Docker, Modal, provider or network operation is authorized. `OWNER_MODAL_CALL_APPROVED=NO`; S1a-P, S1b, S2, S3 and M3-M6 remain closed.
- **Approval basis:** direct owner instruction in this conversation, 2026-11-09; D-167 and D-166.
## M2 S1a-T Approval Addendum 5 — 2026-11-09

- **Status:** APPROVED / NOT LAUNCHED. This addendum authorizes only the narrow exact-delta correction and one final composition/OpenAPI invocation; it does not launch S1a-T or the PostgreSQL launcher.
- **Owner decision record:** D-168 in `DECISIONS.md`.
- **Decision pin supersession:** DECISIONS.md SHA-256 after D-168 is `FF2220AD57CA2A265C05E2FD849A581AE443D753CF7D2EF6844B3453FC2511CB`. It supersedes the prior decision pin for R6 sections 1 and 5 and the DECISIONS row in the R6 launch instruction. R6 artifacts remain unchanged.
- **R6 artifacts unchanged:** specification `664E300F5CAA01DA41E17F5E48025F58D2681F6A676E2CAD1973859F19E04479`; launch instruction `F8E2DB8463AC6511C9D0EFC716A1E9076A390EBBC5DF1043125EBB8B989023D9`; guarded launcher `F3D7992FABFEB848085C5BBD55780EE158894BA197DBA054CD205487219B7A55`.
- **Prior composition result:** owner disposition of run `r6retry_2ea7b5600e98466d93f4ed7906ae1bdd`, stdout SHA-256 `79A18B44B05185BAC09D72D1675437991093953231966A1DA21BE19362C3E7B6`: official summary `1 failed, 7 passed, 1 error in 22.44s`, exit 1. Setup `FileNotFoundError [WinError 3]` was caused by the missing basetemp parent; the exact-delta failure consisted of the four unchanged pilot-assistance routes listed in D-168.
- **Permitted test edit:** add only the four D-168 route strings to the exact-delta expected set in `backend/tests/contract/test_app_composition.py`. All other assertions, expected sets, ordering, and test structure remain unchanged.
- **Final composition/OpenAPI invocation:** exactly one, using R6 section 3, cwd `backend`, the R6 executable/selection/flags, run id `r6run4_4d8327e54db74ccfab1a0ee9d6f6a84b`, and basetemp `..\tmp\M2_S1A_T_20261107\r6run4_4d8327e54db74ccfab1a0ee9d6f6a84b\composition-openapi`. The run parent must already exist and be empty; do not create it, change permissions, or reuse any old log name. This is the last composition invocation regardless of result.
- **Remaining post-code commands:** only after an official composition PASS, run Ruff on approved Python paths, `validate_harness.py`, `validate_repository_security.py`, `validate_architecture.py`, and `git diff --check` once each per R6/D-167. A missing safety verdict is NOT RUN and stops the sequence. Mypy is not rerun; exit 1 remains NO PASS under D-167.
- **Review/output:** after the required commands have official results, use a fresh cold read-only independent review session, maximum three rounds under D-166; preserve old logs and use only unique new output names. No further composition run is allowed even if review requests a composition-affecting change.
- **Execution state at approval:** no command has yet run under D-168. No PostgreSQL, owner launcher, database, Alembic, Docker, Modal, provider or network action is authorized. `OWNER_MODAL_CALL_APPROVED=NO`; S1a-P, S1b, S2, S3 and M3-M6 remain closed.
- **Approval basis:** direct owner instruction in the current conversation, 2026-11-09; D-168 and D-167.

## M2 S1a-T Approval Addendum 6 — 2026-11-09

- **Status:** APPROVED / NOT LAUNCHED. This addendum records only the accepted owner-run composition/OpenAPI result and the continuation to the remaining post-code commands; it does not launch S1a-T or the PostgreSQL launcher.
- **Owner decision record:** D-169 in `DECISIONS.md`.
- **Decision pin supersession:** DECISIONS.md SHA-256 after D-169 is `A4FEE34E345EE4E325377523240CB46072434F745570E4681B8E056FBB891BD4`. It supersedes the prior decision pin for R6 sections 1 and 5 and the DECISIONS row in the R6 launch instruction. R6 artifacts remain unchanged.
- **R6 artifacts unchanged:** specification `664E300F5CAA01DA41E17F5E48025F58D2681F6A676E2CAD1973859F19E04479`; launch instruction `F8E2DB8463AC6511C9D0EFC716A1E9076A390EBBC5DF1043125EBB8B989023D9`; guarded launcher `F3D7992FABFEB848085C5BBD55780EE158894BA197DBA054CD205487219B7A55`.
- **Composition/OpenAPI result:** owner-run `r6owner_d5281b1e47fe4f71a736a2ffdde9e6df`, exit 0, `9 passed in 34.20s`; stdout SHA-256 `21BB5CD7E56DCB165321D85CEBCB03BA59251CBA5B81CF9873E74772FF40ECAA`, stderr SHA-256 `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`, exit-file SHA-256 `13BF7B3039C63BF5A50491FA3CFD8EB4E699D1BA1436315AEF9CBE5711530354`. History: Codex runs `r6retry_2ea7b5600e98466d93f4ed7906ae1bdd` (`1 failed, 7 passed, 1 error`) and `r6run4_4d8327e54db74ccfab1a0ee9d6f6a84b` (`8 passed, 1 error`, sandbox `PermissionError` at tmp_path setup) are preserved and unedited. No further composition run is authorized.
- **Remaining post-code commands:** Ruff on approved Python paths, `validate_harness.py`, `validate_repository_security.py`, `validate_architecture.py` and `git diff --check`, once each per R6/D-167. A missing safety verdict is NOT RUN. Mypy is not rerun (exit 1 = NO PASS, 0 new diagnostics versus baseline).
- **Review/output:** after the required commands have official results, a fresh cold read-only independent review session, maximum three rounds under D-166; unique new output names only.
- **Execution state at approval:** none of the remaining post-code commands has run under D-169. No PostgreSQL, owner launcher, database, Alembic, Docker, Modal, provider or network action is authorized. `OWNER_MODAL_CALL_APPROVED=NO`; S1a-P, S1b, S2, S3 and M3-M6 remain closed.
- **Approval basis:** direct owner instruction in the current conversation, 2026-11-09; D-169, D-168 and D-167.

## M2 S1a-T Approval Addendum 7 — 2026-11-09

- **Status:** APPROVED / NOT LAUNCHED. This addendum authorizes only R7 artifact preparation, the named offline test edits, the explicitly bounded offline checks, and independent review. It does not launch S1a-T.
- **Owner decision record:** D-170 in `DECISIONS.md`.
- **Decision pin:** `DECISIONS.md` after D-170: SHA-256 `5BBFF2927B53B9EA7CF00DF195B7828B3F9CD7E54D41FC765FD19646AE6F1EFC`; this supersedes the prior D-169 pin where R7 records current governance.
- **R6 history:** R6 specification SHA-256 `664E300F5CAA01DA41E17F5E48025F58D2681F6A676E2CAD1973859F19E04479`; launch instruction `F8E2DB8463AC6511C9D0EFC716A1E9076A390EBBC5DF1043125EBB8B989023D9`; launcher `F3D7992FABFEB848085C5BBD55780EE158894BA197DBA054CD205487219B7A55`. R6 files remain unchanged. R7 is to be created as new files and independently reviewed.
- **Permitted R7 launcher change:** use `host(inet_server_addr())` at each server-address query, preserving loopback validation with `ipaddress.ip_address(...).is_loopback`; synchronize required artifact and decision pins. No other guard, business, allowlist, ceiling or stop-gate change.
- **Permitted PostgreSQL-test changes:** in the new-path `test_m2_s1a_teacher_postgres.py`, fix loopback identity parsing, seed a marker-formatted class directly through the ORM, set `SKETCH2LIFE_BE1_ARTIFACT_ROOT` to `tmp_path`, and add the R6 §4 Teacher-scope/age/persistence/race cases listed in D-170. Use only existing markers for every written table; if an action writes an unmarked or unlisted table, stop without changing launcher markers. PostgreSQL execution remains owner-only and is not authorized by this addendum.
- **Permitted synthetic-pilot test edit:** add only `assert not token_hex_calls[0].keywords` beside the existing token-hex assertions in `test_be1_synthetic_pilot.py`.
- **Explicit exclusions:** no `backend/src`, no composition/OpenAPI test edits or reruns, no changes to R6 files, no scope/allowlist or business-rule changes. P3-5 through P3-9 and mypy P3-10 remain report-only debt.
- **Authorized offline commands:** one third Ruff run on the same 14 approved Python paths; one third offline pytest run for the changed suite selection; one each of `validate_harness.py`, `validate_repository_security.py`, `validate_architecture.py`, and `git diff --check`, using R6 commands and ceilings with new unique logs. No mypy or composition rerun. Missing safety verdict is NOT RUN. Any official failure/error stops the sequence and is recorded verbatim; no retries or command substitutions.
- **Review gate:** a new cold read-only independent reviewer, not a subagent, reviews R7 pins/diffs, P2-1/2/3 and P3-4/12 closure, marker and data-ceiling accounting, race determinism, report/log agreement, and R7 launcher approval selection. R7 entry may be appended only after READY or READY WITH NOTES with 0 P1/0 P2, within D-166 round limits.
- **Open owner decisions:** acceptance of the six baseline Ruff I001 findings, and confirmation of who ran the second offline pytest after the B009 edit, remain OPEN and must be reported as waiting.
- **Execution state at approval:** no command has run under D-170. `OWNER_MODAL_CALL_APPROVED=NO`; no PostgreSQL, owner launcher, DB, Alembic, Docker, Modal, provider or network action; S1a-P, S1b, S2, S3 and M3-M6 remain closed.
- **Approval basis:** direct owner instruction in the current conversation, 2026-11-09; D-170 and D-163 through D-169.

## M2 S1a-T Approval R7 — 2026-11-09

- **Status:** APPROVED / NOT LAUNCHED. This entry records the R7 approval for the owner-run PostgreSQL acceptance of S1a-T and does not launch it. The owner launches the R7 launcher once, after renaming both output directories.
- **Owner decision record:** D-170 and D-171 in `DECISIONS.md`. D-163 and D-164 continue to govern the Teacher profile handler and Bruno 013; no new product rule is introduced here.
- **R7 approval specification:** `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S1A_T_APPROVAL_SPEC_FINAL_20261107_R7.md` — SHA-256 `D79EB097CBFC775F0FD411F94A743B8E2074EAE289BC60316E10CF263DC16E59`.
- **R7 launch instruction:** `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S1A_T_LAUNCH_INSTRUCTION_20261107_R7.md` — SHA-256 `395D43DE5C14559D8E6333CCCA853A0BDAA9D5954EB5332BD74AA2B1B415F200`.
- **R7 guarded launcher:** `features/FEAT-063-system-architecture-rearchitecture/evidence/scripts/m2_s1a_t_owner_run_20261107_r7.py` — SHA-256 `D4016330DA42D38035F1ED14C95A51026C81AEFF31F9F72F1FA364028370DFB3`.
- **Decision pin:** `DECISIONS.md` through D-171 — SHA-256 `CAD56F5754C823B813AF49B0CA438E8332B9C3CE354CEB5513D4F73A134CB151`. The DECISIONS row in section 5 of the R7 specification still carries the earlier post-D-170 value; section 1 of the specification and the launch instruction carry this value, and this value governs. The launcher does not read it.
- **Historical records:** the R5 approval, the R6 approval and Approval Addenda 1 to 7 remain historical. R7 artifact pins supersede R6 for the launcher run; all other approved scope, allowlist, business rules, ceilings and stop gates remain in force, with D-163, D-164, D-170 and D-171 governing.
- **Baseline prerequisite:** the `M2 Baseline Closure Acceptance` entry remains ACCEPTED and its closure record SHA-256 is `65588C6876F653F3A0B17E227B8845E63EA2F6C77FB78756A91925DEBA9626D6`.
- **Independent reviews (fresh, cold, read-only, Claude sessions):** code round 1 READY WITH NOTES (0 P1, 3 P2, 10 P3); round 2 of the R7 package and code BLOCKED (1 P1, 2 P2, 6 P3), fixed by D-171 item 12; final round (R7 package round 2, code round 3) READY WITH NOTES (0 P1, 0 P2, 5 P3), session `local_e5f8f4a6-b6e3-487b-9301-3a107cbd6065`. Carried P3 notes: the section 5 DECISIONS pin is stale and superseded as stated above; the specification's list of secret-scan patterns omits the URL-scheme pattern the launcher also applies; Ruff, `validate_repository_security.py` and `git diff --check` have not been re-run on the final PostgreSQL test file (NOT VERIFIED); the earlier P3 items 5 to 9 remain recorded debt.
- **Execution state:** nothing has run under R7 against PostgreSQL. The launcher has never been executed end to end and the PostgreSQL test has never run on a database. Owner-run composition/OpenAPI result: 9 passed, exit 0. The output directories `.claude/handoff/logs/M2_S1A_T_20261107` and `tmp/M2_S1A_T_20261107` still exist and are a launcher stop gate until the owner renames them.
- **Not opened:** S1a-P, S1b, S2, S3 and M3-M6. `OWNER_MODAL_CALL_APPROVED=NO` remains unchanged. Acceptance of the six residual Ruff I001 diagnostics, confirmation of the coordinator-run offline pytest runs, and ACCEPTED for S1a-T remain owner decisions.
- **Approval basis:** direct owner instruction in the current conversation, 2026-11-09 (choice "record the R7 entry"); D-170 and D-171; the final independent review report.

## M2 S1a-T Closure Acceptance — 2026-11-09

- **Status:** ACCEPTED by the owner for S1a-T on the exact evidence in `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_T_CLOSURE_RECORD_20261109.md`, SHA-256 `D2ACD33F03E28C961F30270F310F27913257D39A28CEC8281D29ADAE5D285FDE`. The record is unchanged; this append-only entry records the owner's acceptance. Owner words: "ACCEPTED".
- **Evidence accepted:** the R7 owner-run PostgreSQL acceptance (run `f7fe88273c7f4dd89b3913efeac6f8fb`: pytest `1 passed in 5.81s`, exit 0, pre-run inventory `PASS_EMPTY`, post-run inventory `MARKER_COUNTS_MATCH` with 29 marker rows); the owner-run composition/OpenAPI result (9 passed, exit 0); offline pytest (574 passed, 1 deselected); strict mypy by baseline comparison under D-167 (exit 1 stays NO PASS); the independent reviews recorded in the R7 approval entry.
- **Provenance disclosed:** the closure record itself was written by the Claude coordinator and was not independently reviewed; the underlying R7 package and code received three independent review rounds. Several post-code commands (Ruff, three validators, `git diff --check`, offline pytest reruns) were run by the coordinator at the owner's instruction after the Codex sandbox could not write its cache and temporary directories; the composition result and the PostgreSQL result were run by the owner.
- **Not decided by this entry and still open:** acceptance of the six residual Ruff I001 diagnostics (already present at HEAD) as lint debt, with Ruff exit 1 still NO PASS; confirmation of the coordinator-run offline pytest reruns; authorisation to commit S1a-T. Ruff, `validate_repository_security.py` and `git diff --check` have not been re-run on the final PostgreSQL test file (NOT VERIFIED).
- **Phase boundary:** this acceptance closes S1a-T only. It does not approve or launch S1a-P, S1b, S2, S3 or M3-M6; each needs its own Task Approval. The task database `sketch2life_m2_s1a` now holds 29 synthetic marker rows that no phase may clean up without a decision. No Modal, provider or network action is authorised. `OWNER_MODAL_CALL_APPROVED=NO` remains unchanged.
- **Approval basis:** direct owner instruction in the current conversation, 2026-11-09 ("ACCEPTED"), after the closure record and the launcher log were presented.

## FEAT-063 Plan Rev52 addendum — publish SRS contradiction reconciliation

- **Status:** APPROVED for the exact branch publication scope below; SRS content remains unsigned.
- **Approver:** Project owner, direct instruction on 2026-11-06: “commit and push”.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV52_SRS_CONTRADICTION_RECONCILIATION_20261106.md`.
- **Current reviewed plan SHA-256:** `9B6100D907B27302A90F194ADB20B0D67AE2811987F9A5C82DAC23B03B432D55`. Original documentation-scope authorization hash and history are retained in the Rev52 approval entry above.
- **Scope:** commit only the 15 paths enumerated in the Plan Rev52 Publication addendum with subject `docs(FEAT-063): reconcile v2.5 SRS review findings`, then regular non-force push to `origin/docs/feat063-srs-conflict-remediation-20261106`.
- **Exclusions:** force-push/history rewrite, `dev`, PR, merge, SRS sign-off, and any path outside the approved manifest.
- **Required checks:** `python tools/validate_repository_security.py` before commit and before push; `git diff --check` must pass.
- **Approval basis:** the owner’s latest direct instruction supersedes only Rev52’s former no-commit/no-push boundary; it does not expand product or SRS requirement scope.


### Execution closeout — Plan Rev52 publication

- Package commit `ca3c5dda695dc8d325442921ace684364d0215b1` was pushed to `origin/docs/feat063-srs-conflict-remediation-20261106` with a regular non-force push. Fresh `git ls-remote` returned the same SHA.
- `python tools/validate_repository_security.py` passed before commit and push (`publishable_files_scanned=6565`); `git diff --check` passed.
- No force push, `dev` update, PR, or merge was performed. The SRS and Data Table Register remain v2.6-draft and unsigned.


## FEAT-063 Plan Rev53 — v2.6 checklist SRS reconciliation

- **Status:** APPROVED for the exact documentation scope in Plan Rev53; not SRS content sign-off.
- **Approver:** Project owner, direct request on 2026-11-07 to read the supplied checklist and continue fixing the SRS.
- **Recorded date:** 2026-11-07, Asia/Saigon.
- **Plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV53_SRS_V26_CHECKLIST_RECONCILIATION_20261107.md`.
- **Plan SHA-256 at authorization:** `C35BD75F9C5844FFB9B297F9A3B5BAFC4136436C766639FBB18EE2E59C987AFE`.
- **Current reviewed plan SHA-256:** `3DA78D1630040B78526767A2FD8D4C782EB96D894D63B1D30B6CE06ADC6AB48D`.
- **Scope:** AC1–AC6 in Plan Rev53 and only its 15-path manifest. The earlier direct “commit and push” instruction in this same SRS remediation thread covers the regular push described by AC7; it does not authorize a PR, merge, force-push, or `dev` update.
- **Acceptance criteria:** AC1–AC7 in the hash-identified Plan Rev53.
- **Exclusions:** product code/API/runtime/provider/database/DDL/migration/test/build/diagram changes; new owner decisions not supplied; formal SRS sign-off; paths outside the manifest.
- **Approval basis:** the owner’s direct request authorizes this bounded SRS/Data Table Register review and correction. The checklist itself does not approve requirements.

## FEAT-063 Plan Rev54 — v2.6 checklist audit and diagram readiness

- **Status:** APPROVED for the exact documentation-only scope in Plan Rev54; this is not SRS content sign-off or approval of final diagrams.
- **Approver:** Project owner, direct instruction on 2026-11-07: “check all these points and fix luôn, fix xong thì commit và push”.
- **Recorded timestamp:** 2026-11-07 09:18:46 Asia/Saigon.
- **Plan:** features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV54_DIAGRAM_READINESS_CROSSWALK_20261107.md.
- **Plan SHA-256 at authorization:** FA962EC25E84F4056DA23CB82C181ED1ADE2DFBD7BF6D6C54E6597C5A0648DF0.
- **Current reviewed plan SHA-256:** 8FD7667D8EA13E2D1F1DA92C4E58974A5F514DF11DF6DB7868EEA0B2A8FB8730.
- **Scope:** AC1–AC8 in the hash-identified plan and only its 12-path manifest; audit all supplied M/D/Q/R items, create draft TO-BE diagram inputs and a traceable crosswalk, update FEAT-063/root tracking, then commit and normally push the named documentation branch.
- **Acceptance criteria:** AC1–AC8 in Plan Rev54.
- **Exclusions:** product code/API/runtime/provider/database/DDL/migration/tests/build; final diagrams; new owner decisions; SRS sign-off; PR/merge/dev/force-push; paths outside the manifest.
- **Approval basis:** the owner’s direct task instruction authorizes review, documentation corrections and publication within this bounded scope. The checklist does not approve its own open product decisions.

### Execution close-out — Plan Rev54 publication

- **Recorded timestamp:** 2026-11-07 09:32:04 Asia/Saigon.
- Package commit c5469153600ba8763f14715eb12f5792e8b5afe4 was pushed to origin/docs/feat063-diagram-readiness-20261107 using a normal push. Fresh git ls-remote confirmed the remote SHA matched.
- git diff --cached --check passed for the exact 12-path manifest. python tools/validate_repository_security.py passed before commit and before push; each run scanned 6,571 publishable files.
- No final SRS sign-off, PR, merge, dev push, force-push, product test/build/runtime/provider/database change or as-built verification occurred.

## FEAT-063 Plan Rev55 — independent two-agent diagram readiness assessment

- **Status:** APPROVED for the exact documentation-only scope in Plan Rev55; not SRS sign-off or approval of final diagrams.
- **Approver:** Project owner, direct instruction on 2026-11-07: “up leen github di”, referring to publishing the immediately preceding two-agent SRS diagram-readiness assessment.
- **Recorded date:** 2026-11-07, Asia/Saigon.
- **Plan:** features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV55_TWO_AGENT_DIAGRAM_READINESS_ASSESSMENT_20261107.md.
- **Plan SHA-256 at authorization:** B3EC54830EEDBE1D5C2DAE7391636103D4A28CD01A174C0EE6B090342078CE73.
- **Scope:** AC1–AC8 in the hash-identified plan and only its 10-path manifest; publish the two independent reviews on docs/feat063-diagram-readiness-20261107.
- **Exclusions:** product/SRS/DTR changes, final diagrams, DDL, tests/build/runtime/provider/database changes, PR/merge/dev/force-push, and paths outside the manifest.
- **Approval basis:** the owner’s direct request authorizes recording and normally pushing this bounded assessment. It does not sign off the SRS, resolve open questions, or approve final diagrams.
- **Current reviewed plan SHA-256:** 2F9387D44D4C2C7BA616FF3919BBFFFE43A757CDB9D45E2B3C62E8334A138EE4.

### Execution close-out — Plan Rev55 publication

- **Status:** COMPLETE.
- **Package commit:** 33c40d17ff77f31b1d128ce35c1f641a2fe6de8a was normally pushed to origin/docs/feat063-diagram-readiness-20261107; fresh git ls-remote confirmed the same SHA.
- **Validation:** git diff --cached --check passed for the exact 10-path manifest. Repository security validator passed before package commit and push; each run scanned 6,573 publishable files.
- **Limits:** No SRS sign-off, final diagrams, product tests/build/runtime/provider/database work, PR, merge, dev update, or force push.

## FEAT-063 Plan Rev56 — ten-group diagram readiness alignment

- Status: APPROVED for the exact documentation-only scope in Plan Rev56; not SRS content sign-off or final diagram approval.
- Approver: Project owner, direct request on 2026-11-08: “fix cái này” with the ten-group checklist.
- Recorded date: 2026-11-08, Asia/Saigon.
- Plan: features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV56_TEN_GROUP_DIAGRAM_READINESS_ALIGNMENT_20261108.md.
- Plan SHA-256 at authorization: 4CAFAF01879AB864ECDFAEF872A057F74BFC15B6D809AEA6855414C6574F7447.
- Scope: AC1–AC8 in the hash-identified plan and only its 13-path manifest; align the sample-selection wording and cross-document readiness trace.
- Exclusions: product code/API/schema/DDL/migration/tests/build/runtime/provider/database changes; owner policy closure; final diagrams; SRS sign-off; commit/push/PR/merge/dev update/force-push; paths outside the manifest.
- Approval basis: the owner's direct request authorizes this bounded documentation update. The checklist does not approve its own OPEN decisions.

### Plan Rev56 initial local review checkpoint — before publication request

- Reviewed plan SHA-256: 4CAFAF01879AB864ECDFAEF872A057F74BFC15B6D809AEA6855414C6574F7447.
- git diff --check passed for the documentation-only working tree.
- At this checkpoint, before the owner requested publication, no commit/push or security validation had been run.
- SRS/Register remain v2.7-draft and unsigned; open owner decisions and technical gates remain open.

### Plan Rev56 publication authorization addendum — revision 2

- Status: APPROVED for commit and push of the exact 13-path manifest in Plan Rev56 revision 2.
- Approver: Project owner, direct instruction on 2026-11-08: “commit and push”.
- Plan SHA-256: F17C145F2C3A61CA1983C2FF9B6DF287ABBFEA2E6DFBDDC4F1CD31481794EB45.
- Target: `docs/feat063-diagram-readiness-20261107` to `origin/docs/feat063-diagram-readiness-20261107`, fast-forward only.
- Commit message: `docs(FEAT-063): align ten diagram readiness gates`.
- Limits: No paths outside the manifest, PR, merge, dev update, force-push, tests/builds, SRS sign-off, or final diagrams.

### Plan Rev56 publication execution closeout

- Package commit `09cfc5ca396016cbb7b238a5c744e004f7c7025a` was pushed to `origin/docs/feat063-diagram-readiness-20261107` with a regular fast-forward push; fresh `git ls-remote` confirmed the same SHA.
- `python tools/validate_repository_security.py` passed before commit and push (`publishable_files_scanned=6576`); `git diff --cached --check` passed for the exact 13-path manifest.
- No tests/builds, PR, merge, dev update, force-push, SRS sign-off, or final diagrams were performed.

## FEAT-063 Plan Rev57 — substantive diagram-input remediation

- **Status:** APPROVED for the exact documentation-only scope in Plan Rev57; SRS and Data Table Register remain unsigned v2.7-draft.
- **Approver:** Project owner, direct task request on 2026-11-09 to implement the supplied G01–G10 remediation requirements, followed by direct instruction to commit and push.
- **Recorded date:** 2026-11-09, Asia/Saigon.
- **Approved plan:** features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV57_DIAGRAM_INPUT_DETAIL_REMEDIATION_20261109.md.
- **Plan SHA-256:** 5B5CD090913CE14651E0641AF768F4BB8154543E02E488B2075C65A26E5FADDC.
- **Scope:** exact manifest and acceptance criteria in Plan Rev57; substantive SRS/Data Table Register amendments; Rev57 catalog, decision/trace/physical/state/API/screen/class-package/remediation artifacts; evidence and feature tracking updates. Read-only source verification at baseline ae5707ca188d01d9719ed959b62d768ae927912d.
- **Exclusions:** product code/runtime/API/database/schema/data/migration/provider/secret/permission/cost changes, tests/build/deployment, final diagrams, SRS/DTR sign-off, PR/merge, and force push. Unanswered policy questions remain OPEN-OWNER.
- **Publication:** owner explicitly authorized commit and push; only a normal fast-forward push of the scoped paths to docs/feat063-diagram-readiness-20261107 is authorized.
- **Approval basis:** the direct user request authorizes this exact documentation and publication scope. It does not approve proposed requirements, settle owner decisions, or sign off SRS/DTR.

## Plan Rev59 — align the canonical SRS to the supplied review note

- Status: `APPROVED` for the exact SRS-only documentation scope in Plan Rev59.
- Approver: Project owner, direct request in the current conversation on 2026-11-09: “fix lại srs dựa trên cái này”.
- Plan: `plan/PLAN_REV59_SRS_ALIGNMENT_TO_REVIEW_NOTE_20261109.md`, SHA-256 `199E8F7916848032726AFE5B20C26DA24E91B37115B981BBCFA53FFAFE16579F`.
- Scope: reconcile current data counts and existing Teacher/school-vs-Parent quota and child-media deny-by-default wording; update NFR-16/36 and AC-09/32/42/61/64, Q193 trace and §31.10 cross-references; expand §31.10 to 17 explicit unanswered owner questions; record a Rev59 SRS change row; retain canonical v2.5-draft status; update feature-local traceability records.
- Boundaries: no Rev57 authority promotion, no DTR/diagram/code/API/database/migration/secret/deployment changes, no tests/build, no branch switch, commit or push.
- Approval does not close owner decisions or approve the SRS for final diagrams, physical ERD, implementation, or production.

## Plan Rev60 — rebase the working SRS to v2.7 Rev57

- Status: `APPROVED` for the exact SRS baseline/authority correction and carry-forward scope in Plan Rev60.
- Approver: Project owner, direct correction in the current conversation on 2026-11-09: latest expected SRS is v2.7; check the newest source.
- Plan: `plan/PLAN_REV60_REBASE_SRS_TO_V27_REV57_20261109.md`, SHA-256 `966FA9E4F375E6A33A8C56D21410FFB7D6828E0EEC1A5F3B29A524FDE0021D69`.
- Source baseline: remote read-only branch `docs/feat063-diagram-readiness-20261107`, commit `f21c6f34af1ee045caf9a0621e38376a2bfde390`, SRS v2.7-draft / Rev57. `dev` and `main` remain distinct and are not changed.
- Scope: rebase the canonical SRS to v2.7 Rev57; preserve Rev58 CI/CD and Rev59 corrections; preserve Rev57 §§32.6–32.7 and add the Rev58 source snapshot as §32.8; update authority/source pointers and FEAT-063 evidence records.
- Boundaries: no DTR, diagram, BM04, code, API, database, migration or deployment edits; no test/build/CI run, fetch, branch switch, merge, commit or push. All 17 owner questions remain open and the SRS remains unsigned.

## Plan Rev61 — Single root .env for Firebase Auth and Docker — 2026-11-10

- **Status:** APPROVED for the exact scope and path manifest in Plan Rev61.
- **Approver:** Project owner, direct instruction in this conversation: use only the repository root, do not split setup across checkouts/app-local env files, and make one root .env sufficient for the Firebase/Docker configuration.
- **Plan:** `plan/PLAN_REV61_SINGLE_ROOT_ENV_FIREBASE_AUTH_20261110.md`.
- **Plan SHA-256:** `27D6D8735FF1F23D9B31F0152AD80EEB0A33085CDC5A1C5096AE1E8452950D30`.
- **Scope:** Root .env config for Docker API Firebase Admin verification, existing Teacher Vite Firebase client, and Parent Android client; Parent Firebase Auth adapter and sign-in/sign-up via AuthSessionPort; backend Admin verifier support for local Base64 service-account JSON; focused verification and FEAT-063 tracking.
- **Exclusions:** No sibling checkout/worktree edits, live Firebase account/provider request, database mutation/migration, AI/Modal request, Docker service lifecycle operation, Parent profile/StoryRun API, commit, push, or deployment. .env and credentials remain local and ignored.
- **Approval basis:** Direct owner request authorizes this scope. The backend verifies Firebase ID tokens; Firebase client creates/signs in the identity. No duplicate backend password store is added.

## Plan Rev62 — Parent account registration through backend and Firebase Auth — 2026-11-10

- **Status:** APPROVED for the exact implementation and verification scope in Plan Rev62.
- **Approver:** Project owner, direct request in this conversation: finish backend account registration, run it, and verify the account appears in Firebase. The owner also confirmed the current Firebase project has only the Web app and asked whether Android registration is required; this plan keeps the existing REST-based Android client and does not add an Android SDK app.
- **Plan:** `plan/PLAN_REV62_BACKEND_FIREBASE_ACCOUNT_REGISTRATION_20261110.md`.
- **Plan SHA-256:** `6EF290FAE2F697E4646304DF80E02435CEF964880FF2AD7A1DDA6AA965D5B905`.
- **Scope:** Local-only versioned backend registration API using Firebase Admin; Parent mobile signup through that API followed by Firebase Auth REST sign-in; one-root-env non-secret API base URL; focused automated tests; one live synthetic Firebase Auth creation and Admin lookup; FEAT-063 tracking/evidence per Plan Rev62 manifest.
- **Limits:** No DB identity/Parent role/profile provisioning, verification action link or delivery, full UC-13 onboarding, production availability, distributed throttling, Firebase data products, Android native Firebase SDK, or `google-services.json`. A unique synthetic account remains in the Firebase project for owner inspection; its password and all tokens/credentials are not recorded.
- **Approval basis:** The owner's direct request authorizes implementing and testing this exact backend-to-Firebase account creation slice. It does not authorize commit/push or broader production onboarding.

### Plan Rev62 scope addendum — frozen API route-surface test

- **Status:** APPROVED for adding `backend/tests/contract/test_app_composition.py` to the exact Plan Rev62 manifest.
- **Approver:** Project owner, same direct request to implement and test the backend registration API. The existing composition test freezes the entire mounted API route surface, so it must explicitly account for the new approved registration route.
- **Updated Plan SHA-256:** `4595A9559B32E74883B82F82467C42149ECC3F322C65621227A50E7CECB6E691`.
- **Scope change:** Add only `backend/tests/contract/test_app_composition.py` to the manifest to update the expected route surface. No other Plan Rev62 criteria, exclusions, or paths change.
- **Supersession:** This addendum supersedes the original Plan Rev62 hash `6EF290FAE2F697E4646304DF80E02435CEF964880FF2AD7A1DDA6AA965D5B905` for the exact path addition above.

### Plan Rev62 review outcome and final plan hash

- **Status:** APPROVED for the implementation outcome and evidence recording under the unchanged Plan Rev62 scope.
- **Approver:** Project owner, original direct instruction to implement and test backend Firebase account creation.
- **Final Plan SHA-256:** `688AEACECC6AA1BD5324BA29D81EDE62E79C425C41774D8B50ED972CB31F2991`.
- **Outcome recorded:** Backend account creation and Firebase Admin lookup passed for one retained synthetic account. Focused backend/mobile checks passed. Live Firebase Auth REST sign-in returned `API key not valid`; Plan Rev62 records this as an external configuration blocker and leaves the overall lifecycle in REVIEW.
- **Scope:** Outcome/evidence text only; the path manifest, acceptance criteria, exclusions, and authorization boundary are unchanged.
- **Supersession:** This record supersedes the reviewed Plan Rev62 hash `4595A9559B32E74883B82F82467C42149ECC3F322C65621227A50E7CECB6E691` only as the final lifecycle/outcome hash. The original path-scope addendum remains in force.

### Plan Rev62 final verification update

- **Status:** APPROVED for recording the final focused-test count and Compose configuration check under the unchanged Plan Rev62 scope.
- **Approver:** Project owner, original direct implementation/test request.
- **Final Plan SHA-256:** `1C245F296FDFBBEACDEF3AEC6D1D1C9AF21122A457490F3AE801DEEB11532FDE`.
- **Updated evidence:** Parent auth Jest is 6/6 after adding safe messaging for Firebase's invalid-key response; `docker compose config -q` also passed. Backend focused tests remain 18/18 and mobile TypeScript/Ruff checks passed. No Docker service was started.
- **Supersession:** This record supersedes the prior Plan Rev62 outcome hash `688AEACECC6AA1BD5324BA29D81EDE62E79C425C41774D8B50ED972CB31F2991` only for the final verification count/outcome. Scope and approval boundaries are unchanged.

## Plan Rev63 — Server-managed roles, account administration and Firebase recovery — 2026-11-10

- **Status:** APPROVED for the exact implementation and path manifest in Plan Rev63.
- **Approver:** Project owner, direct request in this conversation: assign Parent role on Parent app registration; restrict Teacher accounts to Teacher Web; seed a Platform Admin account through the project setup; let Platform Admin create accounts and manage roles; and implement Firebase password change/reset flows.
- **Plan:** `plan/PLAN_REV63_ROLE_BASED_AUTH_AND_ACCOUNT_RECOVERY_20261110.md`.
- **Plan SHA-256:** `F8941BE4ED931128CCA0BDBA00E3EA0DCFFF404514B895450688608DC979C257`.
- **Scope:** PostgreSQL-backed product roles, authenticated role resolver, Parent role registration, Platform Admin account CRUD/role/state management, one-time bootstrap command using root `.env`, app role gates, Firebase password reset/change UI, additive migration and FEAT-063 contract/evidence updates.
- **Architecture boundary:** Firebase Authentication remains the identity provider; PostgreSQL resolves application role; no client role claims, password table, Firebase data products, child-media access for Platform Admin, or implicit Teacher class assignment.
- **Limits:** No live Firebase account creation (no bootstrap email supplied; current Firebase Web API key previously returned an invalid-key response), no database migration execution (Docker engine unavailable), no tests added or run, no commit/push. The implementation must not be described as live-verified or production-ready.
- **Approval basis:** The owner's direct implementation request. This approval does not authorize changing unrelated dirty files, adding/running tests, committing, pushing, or publishing credentials.

### Plan Rev63 scope addendum — schema register and assignment-role enforcement

- **Status:** APPROVED for the path-manifest expansion below.
- **Approver:** Project owner, same direct request to implement account roles and admin role management.
- **Updated Plan SHA-256:** `3B8335F4BE0432AA45C22C9CF9D34F98B79AD793DCADF7BB6A0E486FEC2EFCF5`.
- **Added paths:** `artifacts/DATA_TABLE_REGISTER.md` to document the account-role columns on the existing identity record; `backend/src/sketch2life/interfaces/http/routers/be1_registry.py` to prevent School Managers assigning a Firebase subject that has no server-provisioned Teacher role.
- **Scope effect:** No new product role, API operation or external service. No new database table; the additive migration extends `be1_adult_identities`.
- **Supersession:** This addendum supersedes the original Plan Rev63 hash `F8941BE4ED931128CCA0BDBA00E3EA0DCFFF404514B895450688608DC979C257` for the two added paths only.

### Plan Rev63 scope addendum — root environment loading in Admin Web

- **Status:** APPROVED for the path-manifest expansion below.
- **Approver:** Project owner, prior direct instruction that the project must use one root `.env` for all apps.
- **Updated Plan SHA-256:** `715910E003385EBA365F96CCDE6F85AC80B47C9BD93AD3F3B2B3D9D1DBF819E7`.
- **Added path:** `apps/admin-ui/vite.config.ts` so management Web reads Firebase public config and backend base URL from the single repository-root `.env`, matching Teacher Web.
- **Scope effect:** Configuration loading only; no nested `.env`, credentials or service-account file is added.
- **Supersession:** This addendum supersedes the previous Plan Rev63 hash `3B8335F4BE0432AA45C22C9CF9D34F98B79AD793DCADF7BB6A0E486FEC2EFCF5`.

### Plan Rev63 scope clarification — provider-owned profile fields

- **Status:** APPROVED as a privacy constraint within the existing account-management scope.
- **Authority:** Canonical FEAT-063 SRS UC-13 requires the application not to persist raw recipient email/action links in app data or logs. Account list still needs an email label for the authorized Platform Admin UI.
- **Updated Plan SHA-256:** `8489261CD8D5078B1D6D0708193C253069B773F431FD99F554D37B12338E717D`.
- **Decision:** Do not persist email or display name in PostgreSQL, audit, or logs. Resolve those profile fields from Firebase Auth at account-list/read time and return them only to an authorized Platform Admin. The remaining path manifest is unchanged.
- **Supersession:** This clarification supersedes Plan Rev63 hash `715910E003385EBA365F96CCDE6F85AC80B47C9BD93AD3F3B2B3D9D1DBF819E7` for the storage boundary only.

### Plan Rev63 scope addendum — Docker bootstrap environment

- **Status:** APPROVED for the exact `compose.yaml` change below.
- **Approver:** Project owner, prior direct instruction to configure Firebase/auth through Docker with one repository-root `.env`, together with the current request for the Platform Admin seed flow.
- **Updated Plan SHA-256:** `5AB1135E922EA080786909A17CA20492765295386AB8C6231740A33E50D8CE70`.
- **Added path:** root `compose.yaml`.
- **Scope:** Pass `SKETCH2LIFE_PLATFORM_ADMIN_BOOTSTRAP_EMAIL` from the root `.env` to the API container and stop forwarding the retired subject allowlist. No Docker lifecycle operation or live account/bootstrap action is authorized by this addendum.
- **Supersession:** This addendum supersedes the prior Plan Rev63 hash `8489261CD8D5078B1D6D0708193C253069B773F431FD99F554D37B12338E717D` only for the exact Docker environment mapping above.

### Plan Rev63 scope addendum — end-to-end acceptance run

- **Status:** APPROVED for the exact manual E2E acceptance scope in the updated Plan Rev63.
- **Approver:** Project owner, direct request in this conversation on 2026-11-10: “test end to end luồng này cho tôi đi”.
- **Updated Plan SHA-256:** `120FF1994CE81BD6D6A25BD37543B748D5EDDD26A35D57F18903C7E0559DA048`.
- **Scope:** Start only required local Docker services; run the additive role migration on a dedicated disposable `rev63_e2e` database; exercise APIs and role-gated UI/auth flows with synthetic identities in the configured Firebase dev project; attempt reset/change-password verification without using a real email recipient; record evidence and cleanup.
- **Boundaries:** Preserve pre-existing running services/volumes; do not reset the shared database; no child data, secrets in output, test source changes, production-provider operations, deployment, commit or push. Delete only the disposable database and Firebase identities created for this E2E run when safe.
- **Supersession:** This addendum supersedes the prior Plan Rev63 SHA-256 `5AB1135E922EA080786909A17CA20492765295386AB8C6231740A33E50D8CE70` only for the stated E2E test/runtime scope. All earlier implementation paths and constraints remain in force.

## Plan Rev64 — Parent/Teacher Modal AI integration and E2E evidence

- **Status:** APPROVED for the exact integration and synthetic E2E scope in Plan Rev64.
- **Approver:** Project owner, direct request in this conversation on 2026-11-10: start/connect the Parent and Teacher flows to Modal AI, run both workflows, and capture screenshot evidence.
- **Plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV64_PARENT_TEACHER_MODAL_E2E_20261110.md`.
- **Plan SHA-256:** `F0970725FDFB2250EE1B8F8C9041C60A0930B4AB06B66B00F99244674BAF54E6`.
- **Approved scope:** inspect existing Modal dev functions; connect the Parent and Teacher app/API vertical slices to deployed non-video Modal AI functions where the real contract is confirmed; run a bounded synthetic-data E2E using the root `.env`, disposable `rev64_e2e` PostgreSQL and synthetic Firebase identities; capture runtime screenshots/logs inside the feature evidence folder; update FEAT-063 records.
- **Explicit limits:** no video generation, production deployment, Modal app/secret/model changes, real child data, real email, shared DB mutation, commit or push. Preserve pre-existing Docker services and volumes. No Lightning fallback. Call at most once per distinct AI operation in each role flow; stop a provider path after its first contract/provider failure.
- **Owner authorization:** direct request above. The previous owner direction to defer video generation remains in force because this request does not explicitly re-enable video.
- **Scope clarification:** The owner explicitly directed that both real workflows be connected and tested, with no fixture testing. Fixture behavior may remain as historical/dev source, but invoking it or counting a fixture response as pass is excluded from this acceptance run. This clarification supersedes the earlier Plan Rev64 SHA-256 `29CBB696835D7AEF66B780383DBA6E7B3061082832F5C3266C349A1C6DC5C3A6`.
- **UI-driven E2E clarification:** Acceptance requires each role flow to be driven through its actual UI to backend and live Modal inference, with the result displayed in that UI. Backend-only/API-only calls, `/health`, build and typecheck are supporting/preflight checks only and do not count as workflow acceptance. This supersedes the immediately prior Plan Rev64 SHA-256 `735B2C7009E6EB488376FB2DF232A0E8FA2B339E616A5D78788CB65C20212EBA`.
- **Approval-state correction:** Marked the exact approved scope as `APPROVED` in the Plan status field; no scope changed. This supersedes Plan Rev64 SHA-256 `AB58C03BF24B75E25D77929664C5654A9D1993D6F00B9C325C62CDAED3EDEB4C`.
- **Factual-baseline correction:** The plan now records that Modal SDK 1.6.3 is installed in ignored `backend/.venv`, while the authenticated `docaodat24-10` profile has no apps listed in default or `dev`. This corrects an outdated preflight statement only; no scope or authorization changed. Updated Plan SHA-256: `4B2AB48CABCEE45FB61400DA04A8EEE5193DBB2289D64DA25AC351292DB83E5F`.
- **Source/deployment scope correction:** The owner pointed to the existing Modal source on `dev` and requested the two real UI-to-Modal flows. Prior approval already requires running Modal AI and stopping apps after use. The revised plan may therefore restore the exact non-video worker source from `dev`, deploy the three existing non-video apps into `docaodat24-10/dev` for this run, reuse existing Secrets/Volumes without changing them, and stop/verify zero active tasks after testing. This does not authorize video or any Secret/model/Volume changes. Updated Plan SHA-256: `C3C4F807E9A1431711FB3D4A2635250CB78FFD52E6CDDC49C3C62EE9A8907F89`.
- **Plan Rev64 scope addendum — Firebase clock-skew handling for UI acceptance:**
  - **Status:** APPROVED within the owner's direct request to connect and run the real Parent and Teacher UI-to-backend-to-Modal flows.
  - **Observed blocker:** Firebase minted an ID token whose `iat` was 9 seconds ahead of the local backend clock. `iss` and `aud` matched `sketch2life-dev`; `/api/auth/v1/me` returned `401 INVALID_IDENTITY_TOKEN` before role resolution, so no AI request was sent.
  - **Approved change:** Add only `backend/src/sketch2life/infrastructure/identity/firebase_token_verifier.py` to the Rev64 manifest and pass a 10-second `clock_skew_seconds` tolerance to Firebase Admin `verify_id_token`. Signature, issuer, audience, revocation, account role and authorization checks remain unchanged. No token claim is rewritten and no client-side bypass is allowed.
  - **Updated Plan SHA-256:** `E5144F14EF064F189D8269C556EC7243A278C374C8771DA41DF2EBB7C5E906D9`.
  - **Supersession:** This addendum supersedes Plan Rev64 hash `C3C4F807E9A1431711FB3D4A2635250CB78FFD52E6CDDC49C3C62EE9A8907F89` for the exact verifier path and bounded tolerance above; all other scope limits remain in force.
- **Plan Rev64 scope addendum — one recovery call after confirmed Parent UI crash:**
  - **Status:** APPROVED within the owner's direct request to make both real UI-to-Modal workflows run end to end.
  - **Observed failure:** The initial Parent line-sketch call completed on Modal, but the Parent app crashed before rendering the image because React Native rejected `accessibilityRole="status"`. The result was not persisted in app state.
  - **Approved exception:** After replacing the unsupported role with `accessibilityLiveRegion="polite"`, permit exactly one additional `parent.sketch-guide.generate` invocation through the Parent UI to verify rendering. No other operation gets a retry; provider, contract, timeout and safety failures still stop that operation. No video is authorized.
  - **Updated Plan SHA-256:** `C6A217BB2114C7D64621E6B50E3A92F6E7E20063866EF6977667F40581BBF9A3`.
  - **Supersession:** This addendum supersedes Plan Rev64 hash `E5144F14EF064F189D8269C556EC7243A278C374C8771DA41DF2EBB7C5E906D9` only for this single recovery call; other limits remain unchanged.

### Plan Rev64 scope addendum — Parent Auth screen accessibility repair

- **Status:** APPROVED under the owner’s direct request to exercise the real Parent UI through backend and Modal, including necessary UI fixes.
- **Added path:** `apps/mobile/src/features/auth/ParentAuthScreen.tsx`.
- **Change:** Replace an unsupported React Native status accessibility role with `accessibilityLiveRegion="polite"` so the real Parent auth screen can render. No authentication behavior or API contract changed.
- **Plan SHA-256 after execution record:** `B791E6E552FF16A6A99D5758D7A2226FA6DD561AE852A40DF6BC2B87E32015C8`.
- **Supersession:** This addendum supersedes the prior execution-scope plan SHA `C6A217BB2114C7D64621E6B50E3A92F6E7E20063866EF6977667F40581BBF9A3` for the exact additional Parent Auth UI path above. Existing call limits, video exclusion and cleanup boundaries remain in force.

### Plan Rev64 execution outcome — 2026-11-10

- **Lifecycle:** PARTIAL; the plan’s full Parent and Teacher acceptance criteria were not all met.
- **Final plan SHA-256:** `B791E6E552FF16A6A99D5758D7A2226FA6DD561AE852A40DF6BC2B87E32015C8`.
- **Evidence SHA-256:** `13249D065D10271FA112D9EE24AF76E80961AAED767A6437774CA969EE8C06E6` (`evidence/EV-063-74_PARENT_TEACHER_MODAL_E2E_20261110.md`). Sanitized run log SHA-256: `069C5F698A5DF5A6949FD8D6E22B6A6B8C9DA559766C37CCEACB317CEF35D230`.
- **Result:** Parent signup/role resolution and optional FLUX sketch guide passed through Android UI. Parent Qwen drawing-understanding failed strict output parsing after 256 generated tokens; API surfaced 504 `MODAL_OUTCOME_UNKNOWN` before Modal logged terminal `MODAL_MODEL_OUTPUT_INVALID`; no retry or story call was made. Teacher role resolution, Qwen lesson suggestion, Qwen Sketch Deck and FLUX lesson visual passed through Teacher UI. Lesson-file upload/parser and Parent story review remain untested.
- **Cleanup:** Three task-used Modal apps stopped at zero tasks; two synthetic Firebase identities and `rev64_e2e` removed; task-started Postgres/Redis and emulator stopped; existing API/ClamAV services preserved. No video, commit or push.
- **Authorization basis:** The owner’s direct request to connect and run both actual UI flows; this entry records observed outcomes and the narrow UI repair, without changing canonical SRS requirements.

### Plan Rev64 recovery scope clarification — disposable Parent test identity

- **Status:** APPROVED under the owner's direct instructions to make the non-video AI workflows work and exercise the real Parent UI-to-backend-to-Modal path.
- **Observed cleanup state:** The synthetic Firebase identities and `rev64_e2e` database used by the first run were deleted as documented. They cannot be reused for the recovery.
- **Approved scope:** Create one fresh synthetic Parent identity and recreate only the disposable `rev64_e2e` database needed for exactly one drawing-understanding recovery request through the Parent UI; if valid, allow one first story-generation request through that UI. Delete the identity and database afterward. No real child data.
- **Plan SHA-256:** `0117AE6EB5FE0FE65ABC59DCC439EADA485FB3F49B6E0BD1223232D4A52848BF`.
- **Supersession:** This clarification supersedes the Plan Rev64 recovery addendum hash `AA39A1D85D86A5D0B058F3E08876A07D6A0EBA15CBA830B25811DC0340D7491B` only for test identity/database provisioning. The one-call limits, 512-token cap, strict schema/parser, no-video boundary, no other Modal workload, and app-stop requirement remain in force.

## Plan Rev65 — Teacher Sketch Deck presentation UI

- **Status:** APPROVED for the exact UI scope and file manifest in Plan Rev65.
- **Approver:** Project owner, direct instruction on 2026-11-10 to implement the Teacher presentation interface so generated slides and their visuals display in Teacher Web according to the FEAT-063 SRS.
- **Plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV65_TEACHER_PRESENTATION_UI_20261110.md`.
- **Plan SHA-256:** `FA7878EBC92E657B797FCD9A47BF4EA04610E18279351FBF516B52EFF134989C`.
- **Scope:** Render the existing versioned DRAFT deck as an interactive white 16:9 slide viewer, display the existing FLUX composite lesson visual on the drawing-guide slide, and provide ephemeral navigation/step-skip controls. Verify through Teacher Web with live Modal results where available.
- **Known contract boundary:** Existing API returns a single composite guide image; it has no per-slide image refs or single-step regeneration operation. Do not fabricate per-slide assets or silently regenerate the whole deck as a single-step operation. The UI remains DRAFT/review-required and does not add persistence, publication, export, backend/Modal contract or video behavior.

## Rev61–Rev65 scoped publication authorization — 2026-11-10

- **Status:** APPROVED for a normal commit and push of the scoped Rev58–Rev65 FEAT-063 SRS/auth/Parent/Teacher/Modal/presentation changes collected in this branch.
- **Approver:** Project owner, direct instruction: “commit and push”.
- **Branch:** `codex/feat063-parent-teacher-modal-ui`, based on `origin/feature/feat063-be-foundation` at `4b7f07cc`.
- **Publication boundary:** Push this feature branch only. Do not merge to `dev`, force-push, or include `.env`, credentials, seed accounts, real child data, unrelated feature work, or the separate Rev66 diagram-review plan.
- **Supersession:** This direct publication request supersedes earlier plan-specific “no commit/push” exclusions only for publishing the approved implementation/evidence already completed; it does not authorize new runtime/cloud actions or SRS sign-off.

## Plan Rev67 — Parent Android capture-to-AI flow

- **Status:** APPROVED for the bounded implementation and local integration described below.
- **Approver:** Project owner, direct request in this conversation to continue fixing the Parent flow, connect its APIs to UI, and merge to `dev`.
- **Plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV67_PARENT_ANDROID_CAPTURE_AI_FLOW_20261110.md`.
- **Plan SHA-256:** `7003587DFD9709D746F5FB51C8C73533C84EB0962BEBFF91C5930533CB34F975`.
- **Approved scope:** Replace the digital drawing canvas with physical drawing camera/library capture; allow bounded JPEG/PNG upload through the existing Parent drawing API; pass the adult's optional idea to story generation; require explicit subject and context confirmation; render the existing versioned story contract as readable scenes; preserve safe worker failure codes; add scoped implementation/evidence records; review and fast-forward the feature result into local `dev` after history checks.
- **Boundaries:** No video inference, live Modal calls, Firebase/role changes, profile/consent or durable StoryRun implementation, voice/Whisper integration, activity policy decision, Docker lifecycle, force push, or push to `origin/dev`. No automatic retry after timeout/outcome unknown. No secrets, seed accounts, or real child data.
- **Supersession:** This entry supersedes the earlier “do not merge to `dev`” feature-branch publication boundary only for a local, reviewed integration into `dev`. It does not authorize pushing `dev`.

### Plan Rev67 scope expansion — Parent profiles, consent, and StoryRun context

- **Status:** APPROVED for the expanded scope in the updated Plan Rev67.
- **Approver:** Project owner, direct clarification: “Làm luôn profile, consent và migration”; owner confirmed consent was approved and asked to proceed.
- **Updated Plan SHA-256:** `DB1F3E371B59610026980240DF90AEB2D3A510179810C233373F6B08D3489E36`.
- **Added scope:** Parent-owned profile CRUD with immutable revisions; explicit versioned data-authorization acceptance/revoke; additive PostgreSQL migration; authenticated Parent StoryRun creation; DTR-aligned context snapshot and asset lineage persisted in Story/Core records; UI profile selection and saved subject/story confirmation.
- **Consent configuration boundary:** Read policy version/text from the single root `.env`; fail closed if missing. The owner has approved proceeding, but no consent copy/version was supplied in chat or present in the canonical SRS. Do not invent a production/legal policy in source or use real-child data in validation.
- **Supersession:** This addendum supersedes the earlier Rev67 Plan SHA-256 `7003587DFD9709D746F5FB51C8C73533C84EB0962BEBFF91C5930533CB34F975` and expands its approved scope. No other files/actions outside the updated manifest are approved.

### Plan Rev67 manifest clarification — versioned run contract and resume

- **Status:** APPROVED as an implementation-detail clarification under the owner's direct request to finish and connect the Parent workflow.
- **Plan SHA-256:** `0991C06B3052A0E78634AA6CB00FF3015EC7C9A338E8A2A529B7F0696438F0B5`.
- **Manifest additions:** `contracts/schemas/parent_story_runs.py` and a `GET /api/parent/v1/story-runs/active/current` contract so the mobile UI can resume an already persisted active run after reopening.
- **Boundary:** The resumed route returns only the authenticated Parent's own StoryRun; it introduces no cross-account lookup, additional AI workload, video call or remote publication.

## Plan Rev78 and Rev78A — Parent catalog-first suggestions and quality gate

- Status: APPROVED by the project owner through direct instructions on 2026-11-11.
- Rev78 plan: plan/PLAN_REV78_PARENT_CATALOG_FIRST_ACTIVITY_SUGGESTIONS_20261111.md; SHA-256 127E471CD737E0E1C2A4FD33FF49B2A7790A814C1F8FD7B85A1BFEBC2C27E408.
- Rev78A plan: plan/PLAN_REV78A_PARENT_ACTIVITY_GATE_REFINEMENT_20261111.md; SHA-256 03F777103B23A56FDEC398CA940094A62DF26EDE28B35DA56BE4FBA96C077183.
- Rev78 authorizes catalog-first Parent activity selection from Parent-accessible published/shared lesson versions, minimized context to Qwen3.5, and exactly three gated fallback drafts only when no catalog activity is suitable. Rev78A authorizes the limited prose-format relaxation while preserving hard safety/business gates and one synthetic inference attempt.
- Rev78B plan SHA-256: B4FB3B7C9B202B8FE9A95C09751320409FA18B6051A86A61ECACE4F11A288ED0. The owner's direct request on 2026-11-11 authorizes the exact implementation manifest, one feature commit and push, merge into dev, and push dev. Rev78B supersedes only the earlier no-migration assumption and no-publication limits. The canonical Rev60 SRS remains unsigned and unchanged; its no-preset activity question remains open for SRS reconciliation.

## Plan Rev79 — Parent local workflow, seed, and Modal health lifecycle

- **Status:** APPROVED for the exact Rev79 manifest and acceptance criteria.
- **Approver/basis:** Project owner, direct request on 2026-11-12 to continue fixing Parent, provide idempotent local Docker seed data, pass Firebase App ID from the root `.env`, finish the Parent quality-gate/AI work, and start Modal through Docker with `/health` only.
- **Plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV79_PARENT_DOCKER_SEED_MODAL_HEALTH_20261112.md`.
- **Plan SHA-256:** `529D8619B55F27C5B026D79DF5B37336F5125CBD31F5F54A677FD07544E26753`.
- **Approved scope:** Parent activity quality-gate/parser alignment; Parent Expo Firebase App ID and optional Auth Emulator routing; insert-only synthetic Parent/profile/authorization/public lesson seed; local display-only quota summary; Compose migrations/seed/API/Auth Emulator; a dedicated Modal health app that only receives `GET /health` during startup and is stopped with Compose; FEAT-063 evidence/context updates.
- **Boundaries:** No production Firebase identity creation, no real-child data, no committed credentials or changes to the ignored root `.env`, no Firebase Storage/Firestore/Realtime Database, no video inference, no AI worker call during Docker startup, no GPU/model warmup in the health app, no rewrite of the canonical SRS, and no commit/push/merge authorization in Rev79.
- **Completion evidence:** Record Docker configuration/runtime health, seed idempotency, Modal health response and cleanup; distinguish health-app availability from AI model readiness and local demo quota from production Billing.

### Plan Rev79 amendment — local seed credentials, synthetic pilot, and MinIO source build

- **Status:** APPROVED under the project owner's direct request to provide a ready-to-use Docker seed account and complete the Parent local workflow.
- **Updated Plan SHA-256:** `BB16C720A7BAA968114765C0BF774C3F317A4A8467026B5EDC4AC95FABC580C8`.
- **Clarification:** The ignored repository-root `.env` may contain one generated Parent demo email/password for Firebase Auth Emulator only. Keep it untracked and out of screenshots, logs, reports and Git. Compose enables `SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED` only on its local API service so the synthetic profile can exercise authorized local workflows; staging/production remain unchanged. The MinIO service builds the currently pinned upstream release from the official source because the prior public Quay reference returns 401; no third-party mirror is introduced. `.dockerignore` allows only required deployment/workspace files, and the backend Dockerfile builds the renderer from the committed pnpm lockfile so a clean checkout does not depend on ignored local output. The Parent story-context migration no longer lists AI-job, age or pilot revisions already carried by the story-revision dependency chain.
- **All other Rev79 boundaries remain:** no production Firebase account, real-child data, Firebase data stores, video inference, AI worker request during Docker startup, GPU/model warmup in the health app, SRS rewrite, commit, push, or merge.

### Plan Rev79 amendment — Alembic revision identifier compatibility

- **Status:** APPROVED under the owner's direct request on 2026-11-12 to fix the Parent workflow and make the Docker stack complete and runnable.
- **Updated Plan SHA-256:** `35939EBD6E970EB225AF5486A1EF6966043C040CAB01000DEDBCBB0B7D5A6220`.
- **Manifest addition:** `backend/alembic/versions/20261110_parent_lesson_pin.py`.
- **Reason and boundary:** The Docker PostgreSQL run showed that the Parent context revision identifier exceeds Alembic's default 32-character `version_num` column. The approved fix shortens that revision identifier and updates only its dependent lesson-pin revision pointer, preserving the existing schema operations and order. No data reset, destructive migration, or migration of a user database is authorized.

### Plan Rev79 amendment — local Modal API enablement

- **Status:** APPROVED under the owner's direct request on 2026-11-12 to finish Parent AI wiring while keeping Docker startup limited to a Modal health probe.
- **Updated Plan SHA-256:** `5D7D5082AC0D1BB093843B3539F6B4C5E9FA2BEF4A6CB49C7930FD7A285D0257`.
- **Manifest scope:** Update `.env.example` and `compose.yaml`; as local runtime input only, change `SKETCH2LIFE_AI_PROVIDER` in the ignored repository-root `.env` to `modal_dev` and preserve all other values.
- **Boundary:** This enables Modal-backed routes only when explicitly called. Docker startup still sends exactly one health request and zero model inference requests; no video API is called. The root `.env` remains ignored, unstaged and excluded from evidence.

### Plan Rev79 amendment — Parent API host port collision

- **Status:** APPROVED by the project owner's direct 2026-11-12 request to make the Parent Docker/UI workflow runnable.
- **Plan SHA-256:** `5B8375B7DEED983AAB33C69297C3F44C5B35B12985F17D39E7920035555C0380`.
- **Authorized local configuration:** Set only the ignored root `.env` host-port keys for the isolated stack (API 58000, PostgreSQL 55439, Redis 56390, MinIO 59023, MinIO console 59024, ClamAV 53313, Auth Emulator 9099) and `SKETCH2LIFE_MOBILE_API_BASE_URL=http://10.0.2.2:58000`; preserve unrelated settings and all existing containers/volumes.
- **Authorized tracked scope:** Include `backend/src/sketch2life/interfaces/http/router_composition.py` in the Rev79 manifest and update FEAT-063 local setup/evidence records to document the port conflict and resolution.
- **Boundary:** Modal Compose startup still deploys the dedicated health app and sends only one `/health` request; no inference or video call is authorized by this amendment.

### Plan Rev79 amendment — narrow activity text relaxation

- **Status:** APPROVED under the project owner's direct request to fix the Parent activity quality gate and its Modal parser.
- **Plan SHA-256:** `5B8375B7DEED983AAB33C69297C3F44C5B35B12985F17D39E7920035555C0380`.
- **Authorized behavior:** `materials_text` and `observation_notes` may be short fragments without terminal punctuation. `objective`, `preparation_text`, `instructions_text`, and `safety_notes` must remain complete sentences; all age, safety, outdoor, adult-support, PII, language, deduplication and catalog-selection checks remain active.
- **Verification:** Run only the two targeted Parent activity service/worker-contract test modules; no full backend suite or video inference.

## Plan Rev80 — Parent Android AI verification and Teacher progressive sketch guide

- **Status:** SUPERSEDED BEFORE SOURCE IMPLEMENTATION by Plan Rev81 on 2026-11-12, at the owner's explicit request to pause coding and consolidate the scope. No persistent Rev80 source changes are retained from this turn.
- **Approver/basis:** Project owner, direct requests on 2026-11-12 to run the Parent workflow on Android emulator with a non-butterfly image and capture AI results/failures, and to fix the Teacher line-sketch progression shown in the supplied slide 2 screenshot.
- **Plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV80_PARENT_ANDROID_AI_AND_TEACHER_PROGRESSIVE_SKETCH_20261112.md`.
- **Current plan SHA-256:** `22ABAAC59D61042838753D1CB2A3B38A02A26487D391336F8CDD6B3C5A933EF3`.
- **Historical scope:** Bounded synthetic Parent emulator workflow and screenshots; test available Parent AI workloads through the app/API; implement a versioned, validated, cumulative dashed-stroke construction guide for Teacher and render it progressively. These requirements are carried into Rev81, whose exact allowlist and unresolved decisions replace Rev80 for future implementation.
- **Rev81 carry-forward:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV81_CONSOLIDATED_PARENT_TEACHER_DOCKER_AI_20261112.md`.
- **Evidence:** `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-89_PARENT_ANDROID_AI_TEACHER_SKETCH_20261112/`.

## Plan Rev81 — Consolidated Parent, Teacher Presentation, AI and Docker

- **Status:** APPROVED FOR PLAN/DOCUMENTATION ONLY. Source implementation is paused, per the owner's explicit 2026-11-12 instruction “khoan code”.
- **Approver/basis:** Project owner requested one comprehensive plan combining the Parent topic/lesson flow, Teacher media-bearing presentation, progressive line sketch, real Modal AI, and the existing Docker/local setup. The owner supplied task-scoped clarifications recorded in the plan.
- **Plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV81_CONSOLIDATED_PARENT_TEACHER_DOCKER_AI_20261112.md`.
- **Initial Plan SHA-256:** `D2A530016CB2CAA397BA8A6941B01A0A20C65432F2649E386E3BCE6EDE6B5394`.
- **Updated Plan SHA-256 after owner clarifications:** `749D373A2A34EF857692CB104B5153C4ECDC8248958C0C44AF069BA0901DDC9F`.
- **Previous Plan SHA-256 after the post-retake mismatch decision:** `63E8EC420B4602DDD5C7B2ED6EE9A5F629434FB1FF564B3C41BB937C1CF854C7`.
- **Latest Plan SHA-256 after detailed Parent/Teacher workflow and platform support breakdown:** `9292502F57E7038CFDE6CA7885077FFACE10B6B391F2DB5A8BA022410EE993AA`.
- The expanded plan adds Parent auth/profile/share/account/settings/notification/quota/history screens, Teacher occurrence flow, verified current API routes versus proposed contract gaps, logical data ownership/migration sequence, state gates, per-workload AI quality checks, Docker/seed service matrix, work-package dependencies and a real-E2E verification matrix. It remains planning-only.
- **Authorized now:** Consolidate scope, record the owner-confirmed direction, compare it with canonical SRS Rev60, identify conflicts/open decisions, and prepare acceptance criteria and proposed change areas.
- **Not authorized by Rev81:** Source changes, database migration, paid Modal inference, public lesson/media publication, `.env` changes, Docker/Modal service cleanup, commit, push or merge. The existing Rev79 implementation/runtime evidence remains preserved as the baseline.
- **Next gate:** Resolve the open choices in Plan Rev81 §9, prepare any traced SRS/Data Table Register amendments and final exact implementation allowlist, then obtain explicit implementation approval. SRS v2.7-draft Rev60 remains unchanged and unsigned until that separate review/sign-off.

### Rev81 implementation approval amendment — 2026-11-12

- **Status:** APPROVED FOR IMPLEMENTATION under the project owner's direct instruction: “implement plan, make sure no fixture”. This later instruction supersedes the earlier “khoan code” pause recorded above.
- **Approved Plan SHA-256:** `6BE36B78F949177FA87DCED2EA620713BFE8A8EFE092B844AD20EC83B7CF71C6`.
- **Scope detail amendment:** Plan §5.6 now explicitly records durable storage for server-produced activity suggestion revisions and the exactly-one primary activity snapshot/hash on each generated story revision. This is within the already-approved Parent API/persistence/migration families; no new path family or product rule is introduced.
- **Scope:** Frozen path families in Plan Rev81 §8.1. Implement the real Parent Android and Teacher web workflows, backend contracts/persistence, non-video Modal calls, role-scoped presentation/review, and the single-root-env local Compose support described by the plan. Add matching focused tests and evidence only inside the approved paths.
- **No-fixture acceptance:** Product routes and UI must call real app APIs and real services. No hardcoded/mock/fixture response may stand in for workflow output or count as E2E evidence. Local synthetic seed entities and generated non-personal test images are allowed only through the real backend and must remain local. If an API/provider is unavailable, show an explicit unavailable/error state; do not fall back to fixture data.
- **Open decision handling:** Remaining Rev81 §9 items stay open with the safe dispositions written there. The implementation must not present them as SRS decisions or weaken consent, authorization, quality, moderation or safety gates. The canonical Rev60 SRS and Data Table Register are outside the allowlist and remain unchanged/unsigned.
- **Explicit exclusions:** No LTX/video inference, production publication, production Firebase identity/data operation, real-child test data, legal-consent fabrication, `.env` edits, secret/credential edits, destructive migration/data reset, `down -v`, commit, push or merge. Preserve all pre-existing Rev79 work and runtime state.
- **Verification:** Run focused tests/builds needed to verify changed real paths. A bounded real non-video Modal call per not-yet-proven workload is allowed; do not repeat passing paid calls absent a defect. Capture sanitized results in EV-063-90. Stop only task-started Modal apps/processes after verification and preserve shared volumes.

### Rev81 owner-answers and Modal startup addendum — 2026-11-12

- **Status:** APPROVED as an implementation clarification under the owner's replies to the outstanding Rev81 questions and direct correction of the Docker/Modal startup behavior.
- **Updated approved Plan SHA-256:** `E8313747501660C70491FA0A56C029D7DB7773677434AC8132FE2F3CF218560D`.
- **Latest approved Plan SHA-256 after the no-product-request cost clarification and Modal Containers review:** `494F55A33D56CD0E90D6217A29A6719E08DE2C3ED4CB8D251DF2EC2AFA75960F`.
- **Owner answers:** progressive guide uses adaptive 4–8 stages; an approved lesson missing a guide may generate one on explicit request; lesson video embeds allow only HTTPS YouTube/Vimeo URLs.
- **Docker/Modal correction:** Docker reuses the already-deployed drawing-VLM, language/audio and FLUX apps; it does not redeploy/update them on every Compose start. It makes one internal Modal Function call per configured worker using a warmup-only control envelope; that call loads the target model without product inference/output or user/product payload, then Docker calls each app's `/health`. The warmup call and GPU/model-load/idle time are billable. No permanent `min_containers` are set; workers scale down through their existing idle windows. Video and disabled SAM2 remain excluded; Compose shutdown does not stop shared Modal apps.
- **Modal Containers finding:** dashboard Containers are runtime-instance inspection/operation tools, not the app deployment mode. The system stays on existing Apps/Functions; a missing/stopped app or a worker without the warmup contract is reported as `DEGRADED` and does not block the local backend.
- **Manifest clarification:** `deployment/modal/srs_v23/contracts.py` and focused `deployment/modal/srs_v23/tests/**` are added to the existing Modal worker path family to define and verify the no-inference warmup envelope. All other Rev81 scope and boundaries remain as recorded above.
- **SRS boundary:** Rev60's 3–5 guide limit remains unchanged and unsigned; the owner-selected 4–8 behavior is an explicit Rev81 delta that must be reconciled in a later reviewed SRS amendment.
- **No-fixture and exclusions:** no fixture/mock/hardcoded output; no LTX/video inference, product generation during warmup, real-child/production data, root `.env`/secret edits, destructive cleanup, commit/push/merge.

### Plan Rev82 — Parent/Teacher AI gates, API contracts, local Teacher seed and E2E — 2026-11-12

- **Status:** APPROVED FOR IMPLEMENTATION by the project owner’s direct request: “giảm gate bớt lại, fix api schema json, fix các lỗi đó luôn, tự tạo 1 acocunt teacher và test, dùng docker tạo sẵn tất cả cần thiết để test 2 luồng đó đầy đủ luôn, hạn chế crash looping modal, fix các lỗi AI và test lại, hạ quality gate xuống vừa phải, đừng gắt qyas”.
- **Approved plan:** `plan/PLAN_REV82_PARENT_TEACHER_AI_GATES_AND_E2E_20261112.md`.
- **Approved Plan SHA-256:** `F404CE31F3DC6E3281EE9BED7D9FC7B8F61D405BF96685DC7B6D2781614947C6`.
- **Scope:** Exact path families and acceptance criteria in Plan Rev82 §§5–7. Fix observed Parent JSON/API failures; moderately relax subjective AI quality heuristics while retaining contract, age, safety, consent, authorization, privacy, moderation and adult-review gates; add idempotent local synthetic Teacher/Auth Emulator seed and required local organization/class/lesson data; stabilize bounded Modal health/warmup startup; run real Parent Android and Teacher web workflows with real non-video Modal calls; record sanitized evidence.
- **Local configuration authorized:** Add only generated local synthetic Teacher seed email/password keys to the ignored CAPSTONE-root `.env` if absent. Do not display, stage, commit or copy credentials into logs/evidence. `.env.example` remains placeholders only.
- **No-fixture acceptance:** No mock, fixture, canned, hardcoded or previously generated output counts as workflow evidence. Local synthetic seed entities and a generated non-personal test drawing are permitted through the real application path.
- **Explicit exclusions:** No LTX/video inference, production Firebase identity/data operation, real-child data, legal-consent fabrication, Firebase Storage/Firestore/RTDB, destructive database reset, volume deletion, commit, push or merge. Preserve existing changes, Docker volumes and shared Modal Apps. Do not change canonical SRS/DTR.
- **Modal budget/stability:** At most one real call per required workload after fixes; no retries for unknown outcomes and no repeated paid call after pass. Modal warmups are bounded and non-inference; report GPU time/cost where observable. Missing Apps must fail visibly without crash/deploy loops.
- **Verification:** Targeted offline tests, isolated Docker/Auth Emulator seed/idempotency/API checks, followed by actual Parent Android and Teacher presentation workflows. Capture only actual AI artifacts/full Teacher presentation, plus sanitized logs and timings in the approved feature evidence folder.

#### Rev82 narrow manifest amendment — Teacher web root environment lookup

- **Status:** APPROVED as a necessary implementation detail under the same direct Rev82 owner request.
- **Updated approved Plan SHA-256:** `FD1CA18D77F831734B0BD37E8C192F917C440B644202806449FB7F019B2B0348`.
- **Added path:** `apps/teacher-ui/vite.config.ts`, limited to resolving the existing single CAPSTONE-root `.env` while running from this isolated worktree. No app-local env file or second config folder may be added.
- All Rev82 behaviors, verification limits and exclusions remain unchanged.

#### Rev82 evidence-driven amendment — local UI/API CORS

- **Status:** APPROVED under the same owner-directed Rev82 request to fix the Parent/Teacher workflow errors and test both real UIs.
- **Evidence:** The local Teacher UI reached Firebase Auth Emulator, then failed role verification. Backend logs show `OPTIONS /api/auth/v1/me` returned `405 Method Not Allowed`.
- **Updated approved Plan SHA-256:** `05D98FAB63C7116CEC1361FD49260F894AD15407902F8898F33D12636121E375`.
- **Added paths:** `backend/src/sketch2life/interfaces/http/app.py` and one focused CORS contract test under `backend/tests/unit/`.
- **Boundary:** CORS is enabled only for HTTP loopback origins in local/test, with explicit methods and headers including the Parent `Idempotency-Key`; no wildcard origin, no production/staging change, no auth/role relaxation, and no `.env` change. All existing Rev82 limits remain in force.

#### Rev82 evidence-driven API schema visibility amendment

- **Status:** APPROVED under the project owner's same direct Rev82 request to “fix api schema json”.
- **Evidence:** The running API's `/openapi.json` contained 16 paths and omitted the mounted Parent profile/AI/StoryRun and Teacher AI operations; the published description still marked those capabilities unavailable.
- **Updated approved Plan SHA-256:** `B7A57C912A40D43A14CF58F02699E319C7B5926A55B2F0438722CC88BDB10B51`.
- **Added paths:** `backend/src/sketch2life/interfaces/http/openapi_srs_v22.py` and the focused OpenAPI contract test under `backend/tests/contract/`.
- **Scope:** Include currently mounted auth, Parent, Teacher, billing, and lesson-library non-video operations with their FastAPI schemas/security in runtime OpenAPI; retain existing BE1 operations and exclude video-generation routes. Update stale OpenAPI description text and verify representative workflow paths/schema references.
- All Rev82 safety, data, Modal-call, and no-commit/push/merge boundaries remain unchanged. No SRS/DTR product requirement is changed.

#### Rev82 evidence-driven Android Metro dependency amendment

- **Status:** APPROVED as a narrow implementation detail under the owner's direct instruction to run the real Parent flow on the Android emulator.
- **Evidence:** The installed Metro 0.81.5 / Expo Metro config 0.19.12 graph resolved `metro-cache-key` 0.87.0 and failed before rendering with `TypeError: metro_cache_key_1.default is not a function`, which left the Transformer undefined and returned Metro HTTP 500.
- **Updated approved Plan SHA-256:** `D9C44F7D1B0B9ACD40B4D16D2A32C0716A529D3B642B6C51910023D226897317`.
- **Added paths:** `pnpm-workspace.yaml` and `pnpm-lock.yaml`, limited to pinning the Expo SDK 52 cache-key dependency to Metro 0.81.5. No Expo/RN upgrade or sibling app change.
- All Rev82 safety, inference budget, no-fixture, no-video, no-reset, and no-commit/push/merge restrictions remain unchanged.

#### Rev82 evidence-driven local seed credential reconciliation amendment

- **Status:** APPROVED as a narrow implementation detail under the owner's direct request to create local seed accounts and test both real workflows.
- **Evidence:** The Parent seed account existed in Firebase Auth Emulator, but the configured `.env` credentials returned `INVALID_PASSWORD`. The seed reused the UID without reconciling its password after local `.env` updates.
- **Updated approved Plan SHA-256:** `C5BD922D62A3C6C7CD234EC4DB84F5E6E65F9EA8518E516A1BAFDB6D921ED204`.
- **Scope:** The existing local Parent/Teacher seed adapters may set the exact configured synthetic seed account password to the current ignored `.env` value in Auth Emulator. No production Auth, UID changes, database inserts on existing entities, or credential logging.
- All Rev82 safety, data, Modal-call, no-fixture, no-video, and no-commit/push/merge restrictions remain unchanged.

#### Rev82 evidence-driven FLUX progression gate amendment

- **Status:** APPROVED under the project owner's direct instruction to reduce the AI quality gate, fix the observed Modal AI failure, and retest.
- **Evidence:** Two real Parent line-guide calls completed Flux inference but were rejected solely by the per-transition progression heuristic (`MODAL_PROGRESSIVE_GUIDE_NOT_CUMULATIVE`). The second call confirmed the revised per-panel novelty threshold remained too strict for nonuniform AI steps.
- **Updated approved Plan SHA-256:** `C17D129E288CD266881DE7C9E4249DF9911229596E77805081A107767B20D806`.
- **Scope:** Require meaningful added ink in at least half of the transitions while preserving panel/layout, nonblank/dense, retained-structure, schema, draft, and adult-review checks. This authorizes one additional deployment of the existing Flux dev App and one final real inference through Parent UI; do not redeploy other Apps or retry after this final attempt.
- All other Rev82 no-fixture, no-video, no-production-data, no-destructive-reset, no-commit/push/merge, and secret-handling rules remain unchanged.

#### Rev82 evidence-driven Qwen drawing output amendment — 2026-11-12

- **Status:** APPROVED under the project owner's current direct request to lower overly strict quality gates, fix AI/API JSON errors, and test the real Parent and Teacher workflows.
- **Evidence:** The Android Parent synthetic-drawing request reached Qwen3.5-9B and failed at the 512-token ceiling. The constrained decoder reported a completeable JSON parser state and allowed model EOS, but no EOS was produced. Modal's structured terminal failure event arrived after the API had already returned `504 MODAL_OUTCOME_UNKNOWN`; the worker log later identified `MODAL_MODEL_OUTPUT_TOKEN_LIMIT`.
- **Approved Plan SHA-256:** `2F4B86E5378A7F3776F8B33B9B538560340F2D94F2D27383B102A19E935C8E7B`.
- **Scope:** Strictly parse a complete constrained JSON response even when EOS is absent at the output ceiling; keep malformed/truncated JSON rejected. Wait up to 10 seconds for a structured Modal terminal event after a non-timeout failure, classify only an observed allowlisted terminal worker code, and persist confirmed failures as `FAILED` in the invocation ledger. Add focused contract/bridge tests.
- **Added paths:** `backend/src/sketch2life/infrastructure/ai/modal_function_client.py`, `backend/src/sketch2life/infrastructure/story_run_lite/photo_bridge.py`, their focused unit tests, and the existing `deployment/modal/srs_v23/drawing_vlm_app.py`/Modal test paths already in the approved plan.
- **Bounded provider verification:** One update of the existing `sketch2life-srs23-drawing-vlm-dev` Modal App and one new synthetic Parent UI inference after the code fix. This is not a retry of the previous terminally failed call. Do not re-run Parent guide or any already-passing AI workload. No video, fixtures, real-child data, production Firebase, destructive reset, commit, push, or merge.

#### Rev82 evidence-driven Qwen decoder termination amendment — 2026-11-12

- **Status:** APPROVED under the project owner's direct Rev82 instruction to fix AI failures and retest the real Parent/Teacher workflows.
- **Evidence:** The §14 fresh Parent call failed terminally after 512 generated tokens. Modal logs show the schema parser could end and model EOS was allowed, but the token allowlist still permitted continuation; strict JSON parsing found trailing extra data.
- **Approved Plan SHA-256:** `31080CD6A96300ABD40D2CBCB9B54C4A48D586BEEC5D09FE7FF20F0DA69ED57D`.
- **Scope:** Restrict the constrained decoder to EOS when the full JSON schema is complete. Preserve full strict JSON/schema validation and the existing token budget. Add focused offline tests, update only the existing drawing VLM App once, and perform one fresh synthetic Parent drawing-analysis inference. No retry of the failed call, no repeated Flux guide, no video.
- All existing Rev82 limits remain: no fixtures, real-child data, production Firebase, destructive reset/volume deletion, commit/push/merge, or secret exposure.

#### Rev82 evidence-driven Parent activity workload allowlist amendment — 2026-11-12

- **Status:** APPROVED under the project owner's direct Rev82 request to fix AI/API failures and run the real Parent and Teacher workflows.
- **Evidence:** The real Android Parent activity-suggestion call reached Modal, then failed at `input_envelope` with `MODAL_WORKLOAD_NOT_ALLOWED`. Exact FunctionCall logs show `parent.activity.suggest` is missing from the deployed worker's L4 contract allowlist while its function and workload registry are present. No model was loaded and no inference was performed.
- **Updated approved Plan SHA-256:** `299AF9169218205B0E86CCFD30DB8855E1013B9A9FEED39A84CFB0013564EF30`.
- **Scope:** Add only `parent.activity.suggest` to `L4_WORKLOADS`; add a focused acceptance/rejection test; update the existing `sketch2life-srs23-language-audio-dev` app once; verify CPU `/health`; then make one new Parent UI/API activity-suggestion inference after the fix. The failed call is terminal and will not be retried. If the post-fix call fails, preserve logs and stop without another call.
- **Added paths:** `deployment/modal/srs_v23/contracts.py`, a focused Modal worker-contract test, and the approved FEAT-063 evidence/context/status files. No other Modal app may be deployed under this amendment.
- All Rev82 no-fixture, no-video, synthetic-data-only, no-production-Auth, no-destructive-reset/volume-delete, no-commit/push/merge, and secret-handling boundaries remain unchanged.

#### Rev82 Parent activity failure recovery UI amendment — 2026-11-12

- **Status:** APPROVED under the same project-owner request to fix AI workflow errors and test the real Parent flow.
- **Evidence:** After the known terminal activity-worker failure, the Android screen displayed only “Tiếp tục đến kịch bản”. Its controller marks the request attempted and blocks another attempt; returning to subject confirmation sends a duplicate confirmation and is rejected with `PARENT_SUBJECT_REVIEW_NOT_ACTIVE`. The user cannot retry a confirmed terminal failure from the failed activity screen.
- **Updated approved Plan SHA-256:** `AF36F74CACAE8105AF1AE86F6651488059B693C1D9958B6BC1B9E55C26603247`.
- **Scope:** Add a single retry action for `MODAL_WORKER_FAILED_TERMINAL` only, with a maximum of one retry; retain the existing continue/skip action; never offer retry for unknown outcome. No backend or product business-rule change.
- **Added paths:** `apps/ui-mobile/src/parent/presentation/screens/ActivityScreen.tsx` and `apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts`.
- All Rev82 no-fixture, no-video, synthetic-only, no-production-Auth, no-destructive-reset/volume-delete, no-commit/push/merge, and secret-handling boundaries remain unchanged.

#### Rev82 confirmed Parent run-resume amendment — 2026-11-12

- **Status:** APPROVED under the project owner's direct Rev82 request to finish and test the real Parent workflow.
- **Evidence:** The live Parent session was hot-reloaded after the approved retry UI change and returned to sign-in. The existing active run already had an adult-confirmed subject. Reconfirming it was rejected with `PARENT_SUBJECT_REVIEW_NOT_ACTIVE`; the workflow must resume at activity selection rather than repeat subject confirmation.
- **Updated approved Plan SHA-256:** `870CCB436C26AE7A6D29DFA518D67727C39BE7068AE29FACB40034B83A464B93`.
- **Scope:** In `resumeActiveRun`, route a run with a confirmed subject and no generated story to the optional activity step, restore the existing run context, and permit the already-approved single post-fix activity inference. Keep all adult-confirmation, consent, authorization and unknown-outcome protections intact.
- **Added path:** `apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts`.
- All other Rev82 no-fixture, no-video, synthetic-only, no-production-Auth, no-destructive-reset/volume-delete, no-commit/push/merge, and secret-handling boundaries remain unchanged.

#### Rev82 Teacher auth-boundary test harness amendment — 2026-11-12

- **Status:** APPROVED under the project owner's direct request to fix the workflow and retest both roles.
- **Evidence:** Teacher Web production build passed. The focused Vitest suite has two failures because the auth observer test double never emits the authenticated user after sign-in; the app correctly rejects the resulting signed-out state. Four other tests pass.
- **Updated approved Plan SHA-256:** `3524DF162554FE67987D878E8641583A4E0C854BB9C1420E6CBF52D413547110`.
- **Scope:** Correct only `apps/teacher-ui/src/__tests__/app.test.tsx` so it emits the authenticated synthetic test user and mocks Teacher role resolution. Preserve the signed-out denial and explicit `?demo=1` behavior. Re-run the Teacher UI build and tests. No product auth behavior or live credentials are changed.
- All Rev82 no-fixture, no-video, synthetic-only, no-production-Auth, no-destructive-reset/volume-delete, no-commit/push/merge, and secret-handling limits remain unchanged.

#### Rev82 Qwen language JSON termination and bounded activity output amendment — 2026-11-12

- **Status:** APPROVED under the project owner's current direct request to moderate overly strict quality gates, fix JSON/API and AI errors, seed a real local Teacher account, and test Parent and Teacher workflows using Docker and Modal.
- **Evidence:** The one synthetic Parent activity call reached the Qwen3.5 L40S worker, passed model load and decoder setup, then remained in inference for over 24 minutes with GPU at 0%, CPU near 98%, and a Torch Inductor compile-worker pool. The caller's 15-minute socket wait expired; no terminal result was observed. The shared language decoder returns all parser-allowed tokens even after the schema becomes complete, unlike the drawing worker's EOS-only terminal handling.
- **Approved Plan SHA-256:** `0657C114C57943FC0D13729C9D5E07FD9751FEDEB83AE39C912140701748C0B7`.
- **Scope:** Stop only the identified in-flight synthetic activity container; do not retry that call. Add EOS-only decoding after complete schema, retain strict JSON/schema validation, bound catalog selection output and the no-catalog fallback separately, add focused tests, and update only the existing language/audio Modal App once. Then make one fresh Parent activity request and one real Teacher lesson-plan/Sketch Deck workflow, bounded to 30 minutes. No video.
- **Added paths:** `deployment/modal/srs_v23/language_audio_app.py`, focused Modal tests under `deployment/modal/srs_v23/tests/`, and existing FEAT-063 evidence/context/status files.
- Existing synthetic-only, no-fixture, no-production-Auth, no-destructive-reset/volume-delete, no-commit/push/merge, and secret-handling boundaries remain in force.

#### Rev82 moderate Parent activity quality/schema amendment — 2026-11-12

- **Status:** APPROVED under the project owner's direct instruction to lower overly strict quality gates, fix API/JSON schema issues, and complete the local Parent/Teacher test workflows.
- **Evidence:** Parent fallback generation requires short sentence-ending text patterns, exact repeated phrases, and per-activity Montessori/adult/child-agency markers. These checks and narrow output lengths are stricter than the SRS requirements for complete, safe, age-appropriate outdoor activities and make equivalent Vietnamese wording fail. The worker schema and backend constraints also need to remain aligned.
- **Approved Plan SHA-256:** `5C0899B1A8CC61385F44B7BFBA6330C3D6944A638BE78C1A2EC745D66ACFC9EC`.
- **Scope:** Align Modal JSON, backend Pydantic, and service quality checks; remove punctuation/exact-phrase requirements; expand bounded field limits; require child-centered, exploratory and adult-guided markers across the set rather than repeating them in every item; retain safety, PII, outdoor, age, catalog access, exclusions, context, exact-cardinality and adult-review checks. Add focused tests.
- **Added paths:** `backend/src/sketch2life/application/services/parent_activity_suggestions.py`, `backend/src/sketch2life/contracts/schemas/modal_ai.py`, `backend/tests/unit/test_parent_activity_suggestions.py`, and `backend/tests/unit/test_parent_activity_worker_contract.py`.
- No video, fixture-as-success, production Auth, destructive reset/volume delete, commit, push, merge, or secret exposure is authorized.

#### Rev82 Teacher lesson-visual progression gate amendment — 2026-11-12

- **Status:** APPROVED under the owner's direct request to fix AI failures, moderate overly strict quality gates, and retest the real Teacher workflow.
- **Evidence:** A real Teacher lesson-visual request passed auth, organization authorization, contract validation, FLUX GPU preflight, prompt upsampling, model load, and image inference. It failed only at the cumulative-stroke overlap heuristic with terminal `MODAL_PROGRESSIVE_GUIDE_STROKES_CHANGED`; no output image was returned. The failed call is terminal and will not be retried.
- **Approved Plan SHA-256:** `AF77B7298314B7194FA712610DC7128AF938E1DEEED44ED6B6DF48BAE5CE7473`.
- **Scope:** Keep hard layout/ink/progression and adult-review checks; tolerate one low-overlap transition in an 8-step guide if the sequence otherwise remains cumulative, with a 12% retained-stroke floor and sanitized per-transition diagnostics. Add focused offline tests. Deploy only the existing FLUX image App once, then make one fresh authenticated Teacher visual API request after the fix. If it fails or becomes unknown, stop; no loop, no video, no repeated Parent guide or Qwen workloads.
- **Added paths:** Existing `deployment/modal/srs_v23/flux_image_app.py`, focused Modal tests under `deployment/modal/srs_v23/tests/`, and FEAT-063 evidence/context/status records.
- All prior synthetic-only, no-fixture-as-success, no-production-Auth, no-destructive reset/volume-delete, no-commit/push/merge, and secret-handling limits remain unchanged.

#### Rev82 Modal deploy client encoding recovery — 2026-11-12

- **Status:** APPROVED under the owner's direct request to fix AI failures and complete the real Teacher workflow.
- **Evidence:** The single approved FLUX deployment attempt built Modal images but failed before app publication when the local Windows Python client could not encode a Unicode dependency-install log with its legacy `charmap` codec. No inference, GPU allocation, or worker warmup occurred.
- **Updated approved Plan SHA-256:** `884D25460C683122A94978B25265E869BB388DC552D0AD208AECE1E8F9DBE7A2`.
- **Scope:** Retry the same existing FLUX dev app deployment once with `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8`; verify its health route, then make exactly one post-fix authenticated synthetic Teacher lesson-visual API request. If deploy or inference fails/has unknown outcome, stop. No further AI calls, warmups, or app deployments.
- **Added paths:** No additional implementation paths; existing FLUX app and approved FEAT-063 evidence/context/status records only.
- All Rev82 synthetic-only, no-fixture-as-success, no-production-Auth, no-video, no-destructive reset/volume-delete, no-commit/push/merge, and secret-handling boundaries remain unchanged.

#### Rev82 final bounded FLUX and Parent verification — 2026-11-12

- **Status:** APPROVED by the owner selecting “Tiếp tục một lượt giới hạn”.
- **Evidence:** The prior Teacher lesson-visual request completed FLUX inference but was rejected at the 12% retention floor on one transition (9.46%); it was terminal and was not retried.
- **Approved Plan SHA-256:** `B1212DA02AD8C0A41BDA48A0917DF68F5509F547524EA89EB0AD1A3FE1D44137`.
- **Scope:** Set the hard retention floor to 8% only for one transition in an 8-step guide; retain the 20% soft threshold and reject a second low transition, below-floor retention, invalid/blank/dense panels, no progression and full redraw. Run focused tests, deploy the existing FLUX App once, check CPU `/health`, and make one authenticated synthetic Teacher lesson-visual call.
- **Conditional extension:** Only if Teacher visual passes, create one local synthetic Parent through the real registration/Auth Emulator flow and make at most one fresh call each for drawing understanding, catalog-first activities and story revision, sequentially. Stop on any failure/unknown/mismatch. No Parent guide, Teacher plan/deck, video, retries, production Auth, real child data, destructive reset/volume deletion, shared App stop, commit/push/merge, or secret exposure.
- **Evidence paths:** Existing FLUX worker and focused test path; existing EV-063-90 evidence/context/status records.
- All synthetic-only, no-fixture-as-success and secret-handling requirements remain in force.

## Rev83.4 M1/M2 implementation approval — 2026-11-13

- **Status: APPROVED** by the owner selecting “Approve these defaults and M1/M2 (Recommended)” in response to the Rev83.3 M0 decision sheet.
- **Requirements baseline:** FEAT-063 v2.7-draft SRS Rev67, SHA-256 `B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996`; unsigned. The Rev60 SRS copy in this implementation worktree must be replaced with this canonical content before source implementation. Rev68 will record the approved technical decisions without implying formal sign-off.
- **Approved plan:** `plan/PLAN_REV83_4_M1_M2_APPROVED_IMPLEMENTATION_20261113.md`; SHA-256 `736AB5567FA9F2D9F2C824814B600243AF1B66ACCED971E31C4BCD6FAECB618E` (exact manifest also includes the Teacher layout navigation entry point).
- **Scope:** M1 safe SVG catalog, provenance/readiness and deterministic renderer; M2 4–8-stage progressive playback and Teacher manual guide authoring with immutable revisions, 1.5-second autosave and conflict-safe `409` handling. Exact source and documentation manifest is frozen in §4 of the approved plan.
- **M0 defaults:** at least four independent drawable paths; educator approval bound to exact source hash/revision and separate Platform Admin curation; renderer targets ≥30 FPS, p95 first render ≤500 ms after decode, p95 transition ≤150 ms and ≤64 MiB memory growth; independent SVG AI flags OFF by default; M3-B human gate requires 100% hard gates, ≥80% of all cases scoring ≥4/5 on both criteria from two educators, and a third reviewer for a ≥2-point difference.
- **Persistence gate:** use existing immutable lesson versions where their JSONB content and hashes satisfy guide revisions. Add only the minimal Core catalog/review migration if the recorded DTR crosswalk confirms the platform-scope/provenance/review gap. Do not run the migration in this approval.
- **Exclusions:** no fixture/canned product result; no Modal inference/deploy/warmup or AI flag enablement; no FLUX removal; no video, Docker, seeds, Firebase, real child data, generated/approved/applied illustration assets, migration execution, tests, commit, push, merge, or destructive cleanup.
- If implementation requires a path or data change outside the frozen manifest, stop before that change and request a separately recorded amendment. Preserve all pre-existing worktree changes.

## Rev84 real Teacher SVG Modal UI acceptance — 2026-11-13

- **Status: APPROVED** by the owner's direct instruction: test through the UI, connect to real Modal, and do not use fixtures. The owner also confirmed Docker Engine is online and may be used if required.
- **Requirements baseline:** FEAT-063 v2.7-draft Rev69, SHA-256 `AE3ADE230CD97F282C9B1B342B3D48C0513D7E737F0DD7D3B1EABEFDD73E5C3E`; unsigned.
- **Approved plan:** `plan/PLAN_REV84_TEACHER_SVG_MODAL_UI_REAL_20261113.md`; SHA-256 `2A53DE6617C165239C5EE53BAA0DF697A6807C78FC39AD1999A1B5B63B53947A`.
- **Scope:** One real Teacher Web → authenticated backend → pinned Qwen3.5 Modal worker → strict backend SVG sanitation → browser-rendered, non-persisted draft. New workload/API is disabled by default and may be enabled only for this local test. The direct instruction expands Rev83.4 only to the precise paths and one live inference listed in Rev84; all unrelated Rev83.4 boundaries remain in force.
- **Runtime limit:** At most one update of `sketch2life-srs23-language-audio-dev`, one CPU `/health` call, and one UI-triggered GPU inference with no retry; 1,800-second hard cap. No separate GPU warm-up, no dataset download, no FLUX, no video, no shared-app stop, no `.env` edits and no secret display. Stop before deployment/inference if required access, model readiness or cost assumptions cannot be verified.
- **Data and publication:** Use only a non-personal topic typed in the real UI and a local synthetic Teacher identity if needed. No fixture/canned output or mock provider may satisfy live acceptance. Output stays ephemeral `DRAFT`, `review_required=true`, `persisted=false`; no lesson/catalog write, educator approval or public release.
- **Exact file manifest:** Frozen in Rev84 §8. An extra source path requires another written amendment before editing. Preserve all pre-existing worktree changes.

### Rev84 API composition contract test manifest clarification — 2026-11-13

- **Updated approved plan SHA-256:** `A666B7BA4422D935D69EDDEDEA2670C0F4ADF216A2B4618E9DA26F6E8CB4FD9E`.
- **Clarification:** Add only `backend/tests/contract/test_app_composition.py` so the existing exact mounted-route/OpenAPI contract records the newly approved Teacher SVG endpoint and response schema. This is required to keep the repository contract suite accurate; no runtime scope, Modal call count or other boundary changes.

### Rev84 Teacher UI build blocker manifest clarification — 2026-11-13

- **Updated approved plan SHA-256:** `78F5A781FD34F0FEBA7683E3E352A0603245F9F3F79856C55FDF61921CD9A05C`.
- **Clarification:** Add only `apps/teacher-ui/src/services/svgCatalogService.ts` to replace two pre-existing TypeScript parameter properties that fail the requested full UI build with `erasableSyntaxOnly`. This is a compile-only compatibility fix; API behavior and the single-inference cap do not change.

## Rev85 dataset-conditioned Teacher SVG quality — 2026-11-13

- **Status: APPROVED** under the owner's direct request: “nhìn chưa ổn lắm, cần cải thiện thêm, áp dụng dataset vào để cải thiện chất lượng svg của qweb cho ra”. This approves the bounded dataset retrieval integration and one UI-triggered comparison generation described here; it does not authorize broad benchmark claims.
- **Requirements baseline:** FEAT-063 v2.7-draft Rev69, unsigned; current canonical SRS SHA-256 `3534B9AFFD99F71A35426F7F584F941D9EEB3448F4EFC6F0E005C6A1BEF207F4`. SRS §§1–31 remain unchanged; append as-built evidence only to §32.
- **Approved plan:** `plan/PLAN_REV85_TEACHER_SVG_DATASET_QUALITY_20261113.md`; current SHA-256 `F9F9399E197F4D5079D8E27FD32C36C6274626EE0831DE346F32E263FE6AB9C0`. This replaces the immediately preceding hash by recording the dataset's resolved commit, the strict bounded pre-sanitizer normalization allowlist, and the fact that named sample SVGs have no paired source prompt. Source-preservation, no-relaxed-sanitizer, one-inference and file-manifest limits are unchanged.
- **Dataset choice:** `yoavf/svg-animal-illustrations` dataset card (1,416 prompt/SVG pairs, declared CC0 1.0); resolve and record an immutable source commit before import. Curate at most 12 sanitizer-approved references, ≤64 KiB. Treat the synthetic examples as structural references, not as human-rated gold output. Do not bulk-import the 22.3 GB OpenClipart HF mirror, KidDraw, QuickDraw, repository fixtures, or prior generated product SVGs.
- **Scope:** Teacher `teacher.svg-illustration.generate` workload only; deterministic topic-to-reference lookup, one compact retrieved reference maximum, anatomy/layout prompt improvements, source/provenance manifest, and one real authenticated Teacher UI inference with the same deer topic/age/style as Rev84. Existing strict schema/sanitizer, local-only capability gate, pinned Qwen3.5 model, DRAFT/review-required/not-persisted state and `min_containers=0` remain in force.
- **Runtime cap:** At most one public dataset fetch/curation operation, one update of only `sketch2life-srs23-language-audio-dev`, one CPU `/health` call, and one new UI-triggered GPU inference; no GPU warmup, retry, extra topic, other Modal app, or shared-app stop. Keep the 1,800-second hard cap. If source revision/license cannot be pinned, or runtime output fails/has unknown outcome, stop without retry.
- **Exact file manifest:** Frozen in Plan Rev85 §8: one plan/approval, Modal worker/workload metadata, four dataset provenance/reference files, one new evidence folder, FEAT-063 context/decision/source/status/evidence indexes, and SRS §32 only. No additional path without a written amendment and new plan hash.
- **Exclusions:** No fine-tuning/model change, FLUX, line-guide or Parent changes, video, catalog/lesson persistence, publication, production Auth, child data, `.env` edits, destructive cleanup, tests/test-suite execution, commit, push or merge. Preserve all pre-existing worktree changes.

## Rev86 Teacher SVG dataset pack correction and one real comparison — 2026-11-13

- **Status: APPROVED** by the owner replying “ok, đồng ý” to the bounded correction proposal after Rev85 failed before inference.
- **Approved plan:** features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV86_TEACHER_SVG_DATASET_PACK_FIX_20261113.md.
- **Approved plan SHA-256:** 144EA85E3314A9CC86659D749DDFDD9D317C306C5C134BFE6035F975C395696D.
- **Scope:** Exclude the invalid cat reference from the active pack while preserving the raw source snapshot; record the exclusion and refresh dependent hashes; validate every packaged reference with the exact strict worker parser; update only the listed worker/dataset/workload/evidence/FEAT-063 paths; then make at most one deployment of the existing Modal app, one CPU /health call, and one real authenticated Teacher UI inference for the same deer input.
- **Limits:** No parser/schema/quality-gate relaxation, no retry, warmup, extra topic, new dataset fetch, video, FLUX, database reset/migration/seed, .env edit, production Auth, child data, shared Modal App stop, commit, push, or merge. Restore the local capability flag to false. On any preflight, health, or inference failure, stop and preserve diagnostics.
- **Evidence basis:** Rev85 failed during whole-pack validation because cat path path-026 had stroke_width=20 against the existing 1–12 worker range. Full details are in evidence/EV-063-95_TEACHER_SVG_DATASET_QUALITY_20261113/REPORT.md.
- **Exact path manifest:** Frozen in Plan Rev86 §5. Any additional path requires a new approval.

## Rev87 progressive SVG stroke-guide correction — 2026-11-13

- **Status: APPROVED** based on the owner's direct instruction “fix” after reviewing the Rev86 result and its failure as a child-followable drawing guide.
- **Canonical requirements source:** FEAT-063 v2.7-draft SRS Rev69, unsigned; §§1–31 remain unchanged. Rev87 may append environment-specific as-built evidence to §32 only.
- **Approved plan:** `plan/PLAN_REV87_PROGRESSIVE_SVG_STROKE_GUIDE_FIX_20261113.md`.
- **Approved plan SHA-256:** `EAD1F716E2897124061EB3FAB9F43D4DCE9D24176BC7BDB9676907DB9C4FA95F`.
- **Scope:** Add a distinct Qwen3.5 SVG stroke-guide draft workload/contract with strict progression and anatomy gates; replace Parent's raster FLUX guide API path with catalog-first/AI-on-miss SVG output; add authenticated Teacher guide-draft API/UI; keep static illustration separate; perform at most one real UI-triggered inference and no retries.
- **Limits:** One update of the existing language/audio Modal app, one CPU `/health`, one real authenticated inference, no warmup/second topic/new dataset download/test suite/video/FLUX call/real child data/database migration/publication/.env or secret edits/shared app stop/commit/push/merge. Capability defaults off; restore it to false. Exact source manifest is frozen in Rev87 §6; any extra path requires another approval.

## Rev87.1 dataset-backed stroke-guide amendment — 2026-11-13

- **Status: APPROVED** under the owner's direct instruction to improve stroke clarity with a suitable skill or dataset, using the supplied HTML as a visual example. This adds only the curated, attributed dataset source and dataset-first grouping behavior in Rev87.1; all other Rev87 limits remain.
- **Approved plan:** `plan/PLAN_REV87_1_DATASET_STROKE_REFERENCE_AMENDMENT_20261113.md`.
- **Approved plan SHA-256:** `22074E1FABFBE1900425176B82AE5C2D82D1F95D76FF7E57215667FC204C3B45`.
- **Dataset choice:** a small curated subset of the official Google Quick, Draw! cat category, CC BY 4.0. The dataset supplies ordered vector strokes; Qwen groups the source strokes and writes child-facing instructions. The supplied demo's embedded cat paths remain visual reference only and are not copied.
- **Limits:** At most one public cat-category fetch, one existing Modal app update, one CPU `/health`, and one real authenticated Parent UI inference for the cat topic. No full dataset download, retry, extra topic, FLUX, video, test suite, secret/.env edits, real-child data, DB migration, publication, shared-app stop, commit, push or merge. The workload stays disabled by default and is restored to false after testing.
- **Exact cumulative file manifest:** Rev87 §6 plus Rev87.1 §5 only. Any additional path requires another explicit amendment.

## Rev87.2 clean Openclipart SVG source amendment — 2026-11-13

- **Status: APPROVED** by the owner's direct correction rejecting Quick, Draw! as unsuitable source material and instructing replacement with a different SVG source.
- **Supersedes:** Rev87.1's Quick, Draw! source choice and its planned cat inference. No Quick, Draw! data is authorized for repository packaging or product output.
- **Approved plan:** `plan/PLAN_REV87_2_OPENCLIPART_SVG_STROKE_REFERENCE_AMENDMENT_20261113.md`.
- **Approved plan SHA-256:** `B1B37F1D4D2C408C60DE6645E27E65E3490C63C4E4224377CA71FD0E4E8790CC`.
- **Source:** Openclipart item `330236`, “cute simple cat sitting”; the official detail page records its public-domain donation/artist attribution, and the site FAQ states CC0 1.0 for uploaded work. Validate and preserve the exact source SVG and hashes before using it.
- **Behavior:** The engine constructs a line-only SVG from that clean source. Qwen3.5 returns only semantic grouping, progressive stage order, and Vietnamese instructions; it cannot emit or change the source path geometry. An unsuitable source or grouping stops before inference/deployment.
- **Limits:** One Openclipart source fetch, at most one existing Modal app update, one CPU `/health`, and one real authenticated Parent UI inference for the cat topic. No warmup, retry, additional topic, FLUX, video, test suite, `.env`/secret change, real child data, database migration, publication, shared app stop, commit, push, or merge. Capability remains off by default and is restored to false after the single attempt.
- **Exact cumulative manifest:** Rev87 §6 with Rev87.2 §6 replacing Rev87.1 dataset paths. Any additional path requires another explicit amendment.

## Rev87.3 true-stroke Tabler source amendment — 2026-11-13

- **Status: APPROVED** by the owner's direct instruction to replace the rejected child-doodle and filled-shape sources with a suitable true-stroke SVG source.
- **Supersedes:** Rev87.2's Openclipart item choice, which was fetched only for validation and failed the source gate because its paths are filled silhouettes. The failed source was not packaged.
- **Approved plan:** `plan/PLAN_REV87_3_TABLER_STROKE_SOURCE_AMENDMENT_20261113.md`.
- **Approved plan SHA-256:** `8F24E71494B3508FB27E36A161AC11598C143550777484E34BE54353372A1D12`.
- **Source:** official Tabler Icons outline `cat.svg` from `tabler/tabler-icons`, MIT licensed. Validate explicit unfilled stroke geometry, useful independent paths, cat recognizability and 4–8 meaningful stages before packaging or deployment.
- **Behavior:** preserve and normalize the source strokes deterministically. Qwen3.5 may only group/order path IDs and write Vietnamese instructions; it cannot emit or alter SVG geometry.
- **Limits:** one official source fetch; at most one existing Modal app update, one CPU `/health`, one real authenticated Parent UI inference for `mèo`; no warmup, retry, second topic, FLUX/video, test suite, `.env`/secret edit, real child data, DB migration, publication, shared app stop, commit, push or merge. Restore capability to false.
- **Exact cumulative manifest:** Rev87 §6 with Rev87.3 §6 replacing rejected dataset paths. Any additional path requires a separate amendment.

## Rev87.4 curated SVG plus stroke-authoring skill — 2026-11-13

- **Status: APPROVED** by the owner's direct direction to use a professionally curated SVG dataset as the subject reference and install an Agent Skill to author drawable strokes from the reference.
- **Supersedes:** Rev87.3's Tabler cat icon source. No Tabler, Openclipart or Quick, Draw! source may be packaged.
- **Approved plan:** `plan/PLAN_REV87_4_CURATED_SVG_AND_STROKE_SKILL_20261113.md`.
- **Approved plan SHA-256:** `C1531DDC032941E714391AF6F8FD9441D75DAD06EA408D424EB32DD9B49B483B`.
- **Dataset:** Arcadia Science Free Organism Illustration Library v1.0, Zenodo DOI `10.5281/zenodo.17203578`, CC0; use only a selected `Gallus gallus domesticus` SVG from the 71-organism library and record exact hashes/attribution.
- **Skill:** install the MIT-licensed `whiteboard-animation` Agent Skill from `iart-ai/explainer-video-skills` project-locally; adapt its open-path, draw-order, stroke-dash, lift-between-strokes and visual-review rules to the Sketch2Life 4–8-step API/worker contract. The skill is authoring guidance, not a Modal model/service.
- **Runtime:** use the selected SVG rendered in memory as visual reference to the existing pinned Qwen3.5 multimodal worker. Qwen returns actual new line paths, grouping, order and Vietnamese instructions; strict gates and adult review remain mandatory.
- **Limits:** one archive fetch, one skill install, at most one update of the existing Modal app, one CPU `/health`, one authenticated Parent UI inference for `gà`; no warmup/retry/second topic/video/FLUX/test suite/.env or secret edit/production identity/real child data/database migration/publication/shared app stop/commit/push/merge. Restore capability flag to false.
- **Exact cumulative manifest:** Rev87 §6 with Rev87.4 §6. Any additional path requires another explicit amendment.

## Rev87.5 one bounded Modal retry — 2026-11-13

- **Status: APPROVED** by the owner's direct instruction “chạy lại đi” after the Rev87.4 deployment attempt failed before app update.
- **Requirements baseline:** FEAT-063 v2.7-draft Rev69, unsigned; no §§1–31 requirement changes.
- **Approved plan:** `plan/PLAN_REV87_5_CURATED_SVG_MODAL_RETRY_20261113.md`.
- **Approved plan SHA-256:** `BD7CD38EA2CE52B2ED3F833F9555D40EDA7271292BB4EB0F9B9DC0EB36E202FB`.
- **Authorization:** one additional deployment of the existing Modal dev app, one CPU health call, and at most one real authenticated Parent UI inference for the non-personal `gà` topic. This does not authorize any further retry.
- **Limits:** no warmup, video, FLUX, fixtures, tests, DB migration, seed/account creation, production identity, child data, `.env`/secret edits, shared app stop, commit, push, or merge. If preflight prerequisites are missing, stop before deployment/inference; on any runtime failure or unknown outcome, preserve evidence and stop.
- **Exact path manifest:** frozen in Plan Rev87.5 §5. Any further retry or source change requires a new amendment and approval.
### Rev87.5 local runtime preparation clarification — 2026-11-13

- **Approved plan SHA-256:** `F3B03C3B1993B6C36EE24311D4FE77C4BC397B53BC2091B43F25295B3D44B0CE`.
- The owner's “chạy lại đi” authorizes the necessary isolated local preparation for the same one bounded UI inference: start only the existing PostgreSQL/Firebase Auth services on their current volumes, run a temporary current-worktree API container on port 8001 with the guide flag enabled only for that process, and start the real Expo Parent UI using the existing root .env without editing or printing it.
- No migration, seed/account creation, volume reset/removal, existing API replacement, shared Modal app stop, or additional Modal/GPU call is approved. Stop the task-started local services afterward and preserve the existing shared containers and volumes.
### Rev87.5 live-stack selection clarification — 2026-11-13

- **Approved plan SHA-256:** `94547CEC22E0638788358EEEE8DAFBD304D3BF49837DC9CA246CE0DB7D3BF155`.
- Read-only Docker preflight found the default sketch2life Postgres container stopped and its host port occupied, while the existing
ev79-parent-local-20261112 Postgres and Firebase Auth services are already healthy. Use the latter existing stack for the one-off current-worktree API container; do not start/recreate the default stack or stop shared services.
- This is runtime routing for the same owner-authorized single attempt; no DB migration, seed, account creation, or persistent-volume mutation is included.
## Rev87.6 OpenAPI contract and Modal UTF-8 fix — 2026-11-13

- **Status: APPROVED** by the owner's direct instruction “tôi cho phép chạy để fix”.
- **Requirements baseline:** FEAT-063 v2.7-draft Rev69, unsigned; §§1–31 unchanged.
- **Approved plan:** plan/PLAN_REV87_6_OPENAPI_AND_MODAL_UTF8_FIX_20261113.md.
- **Approved plan SHA-256:** `20DABC39EDEF01959FFFF26B72344C8DB2662E9243216005D20F3933718AC8E2`.
- **Owner-authorized scope clarification:** the owner authorized Codex to “run to fix”; runtime inspection showed the mounted SVG catalog was also omitted by the OpenAPI projection. The plan now includes only publishing `/api/svg-catalog/v1/` and a dedicated tag in `openapi_srs_v22.py`, in addition to the concrete response metadata fix. No unrelated projection paths are included.
- **Owner UI steering:** “chạy trên android emu đi” replaces the isolated browser UI check with a real Android emulator run; use only the existing synthetic Parent account and process-local emulator API/Auth URLs. No web login or AI request was made.
- **Scope:** Correct per-route SVG catalog response schemas/statuses; verify OpenAPI; use process-local Python UTF-8 settings for one Modal deploy; one CPU health call and at most one real authenticated Parent UI inference for gà.
- **Limits:** no retry, warmup, test suite, migration, seed/account creation, .env/secret edit, fixture, video, FLUX, existing API replacement, shared service stop, volume deletion, commit, push, or merge. Exact paths and runtime gates are frozen in Plan Rev87.6 §6.

## Rev87.7 real Parent SVG guide draft — 2026-11-13

- **Status: APPROVED** by the owner's direct instruction “tạo svg đi” after Rev87.6 was stopped at the existing incomplete-run UI blocker.
- **Requirements baseline:** FEAT-063 v2.7-draft Rev69, unsigned; §§1–31 unchanged.
- **Approved plan:** `plan/PLAN_REV87_7_REAL_PARENT_SVG_GUIDE_DRAFT_20261113.md`.
- **Approved plan SHA-256:** `661D5DB2D37BBC6B0E5183B8C9BD4422EFD6281FD731C4D6B0F822E39A8C6A5C`.
- **Scope:** at most one authenticated, non-personal `gà` Parent guide request via the existing API/Modal Qwen3.5 path, with the pinned Arcadia reference; no StoryRun/profile/child data, and no fixture. Output must remain a private, review-required, non-persisted draft.
- **Limits:** at most one Modal deployment and one inference; no retries, video, FLUX, account/profile/run mutation, migration, seed, `.env`/secret changes, shared service stop, commit, push or merge. Exact paths and stop rules are frozen in Plan Rev87.7 §5.

## Rev87.8 full Android Parent flow through story confirmation — 2026-11-13

- **Status: APPROVED** by the owner's direct instruction “chạy full flow đi”. This supersedes Rev87.7's standalone guide-only execution scope; Rev87.7 had not started.
- **Requirements baseline:** FEAT-063 v2.7-draft Rev69, unsigned; §§1–31 unchanged.
- **Approved plan:** `plan/PLAN_REV87_8_ANDROID_PARENT_FULL_FLOW_NO_VIDEO_20261113.md`.
- **Approved plan SHA-256:** `A5FD491C1A8C034753A206B18710129B317F122CA28948AB43D3CDADED41A718`.
- **Scope:** real Android UI Parent signup/profile/local synthetic notice, optional SVG guide, synthetic drawing intake, image understanding, catalog-first activity selection, story draft and adult confirmation. Create one new synthetic test identity/profile because the existing Parent account is blocked by its incomplete open run; do not alter that run.
- **Limits:** maximum four UI-triggered GPU inferences, one each for guide/drawing/activity/story; one deployment per required Modal app only if needed; no retries/replacements/video/FLUX/migrations/seeds/production data/.env edits/shared service stop/commit/push/merge. Exact path manifest and stop conditions are in Plan Rev87.8 §5.

## Rev87.9 Android Parent E2E with activity-selection gap — 2026-11-13

- **Status: APPROVED** by the owner's direct instruction “chạy full flow đi”. Rev87.9 supersedes Rev87.8 before runtime after source review found that the current Parent activity screen has no selection action/StoryRun field. Rev87.7 and Rev87.8 were not executed.
- **Requirements baseline:** FEAT-063 v2.7-draft Rev69, unsigned; §§1–31 unchanged.
- **Approved plan:** `plan/PLAN_REV87_9_ANDROID_PARENT_E2E_ACTIVITY_GAP_20261113.md`.
- **Approved plan SHA-256:** `08FB8ACA06AAC49B498310A2B6D62CFBFA03B48287E932B4BDB63CCB045C5026`.
- **Scope:** real Android Parent signup/profile/synthetic authorization, optional SVG guide, synthetic drawing, drawing analysis, catalog-first activity suggestions, and story confirmation through the actual UI. Use one new synthetic identity because the existing one has an incomplete open run.
- **Known SRS deviation:** no activity can currently be selected or attached before story from the inspected UI/API contract. The test may follow the existing visible Continue action to inspect current story behavior, but must report an SRS failure and must never inject an activity manually.
- **Limits:** at most four GPU calls (one guide, drawing analysis, activity suggestion, story), no retries or alternate activity, no video/FLUX, no existing-run mutation/deletion, no migration/reseed/.env edit/shared-service stop/commit/push/merge. Exact paths and stop rules are in Plan Rev87.9 §6.


### Rev87.9 execution outcome — 2026-11-13

- Real Android Parent signup/profile/context/drawing flow reached Modal drawing analysis and catalog-first activity suggestions; both Qwen3.5 inferences returned successfully.
- Optional guide lookup failed because the shared DB lacked the SVG catalog/review tables; no migration was run and the optional step was skipped in UI.
- The current UI cannot select a primary activity. The visible continue action reached story, where the initial request returned HTTP 422 because the required primary activity request/ref pair was absent. No story Modal call, story confirmation, or video occurred. No activity was injected manually.
- Two GPU inferences total; zero retry/timeout. The activity drafts include a small-grain activity with a supervision warning; the result is not content-safety approval. Worker terminal telemetry also omitted the successful terminal event/output hash.
- Task-started API container, Metro and Android emulator were stopped. Shared services/apps/volumes were preserved; no `.env`, code, migration, test, commit or push change was made.
- Evidence: `evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/REPORT.md`, `runtime-attempt-4.json`, `story-generation-http-422-observation.json`, actual model JSON outputs and Android screenshots.


## Rev87.10 bounded Parent activity selection and story test — 2026-11-13

- **Status: APPROVED** by the owner's direct instruction: “cứ làm thêm đi, tạm tắt quality gate mà test”.
- **Requirements baseline:** FEAT-063 SRS v2.7-draft Rev69, unsigned; §§1–31 unchanged.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_10_PARENT_ACTIVITY_SELECTION_STORY_TEST_20261113.md`.
- **Approved plan SHA-256:** `550EFCC7CD3B0D05E9F552CE091FC6E8BCA71C2CDDB98AF7D4782E050936CAA1`.
- **Pre-implementation corrections:** added required Parent application/use-case/UI and Modal client-test paths to §6; specified an explicit story-input v2 contract; allowed one UTF-8 recovery deploy only if the initial build fails before app submission and deployed app state remains unchanged. The authorized inference limit and safety gates are unchanged.
- **Scope:** temporarily add actual UI selection of an activity returned by the current live AI response; validate its request/ref against a short-lived owner/run/revision-bound server snapshot; pass the exact selected activity to Qwen story. The test adapter is process-local and non-persistent, and must be reported as non-production.
- **Gate scope:** bypass only soft activity quality checks in the task-started API container. Schema, age, auth/owner binding, outdoor location, hard safety, PII and story validation stay on. Gate defaults remain strict outside the temporary test container.
- **Runtime limits:** one new synthetic Parent identity via UI, existing shared dev services left running, no migration/reseed/`.env` edit, maximum three real GPU calls (drawing, activity, story), one attempt each, no video/FLUX/retry. Stop only task-started API/Metro/emulator; preserve shared Modal apps/model volumes.
- **No fixture model output or manually injected activity. No commit/push/merge.**

### Rev87.10-A — one Parent SVG guide attempt — 2026-11-13

- **Status: APPROVED** by the owner's direct instruction: “thử tạo svg xem, luồng parent ấy”.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_10_PARENT_ACTIVITY_SELECTION_STORY_TEST_20261113.md`, additive amendment `Rev87.10-A`.
- **Approved plan SHA-256:** `771AF1A0B6FAC59CF11B58A6EB18CE95D8753D25F0880CDE2E1970D03980FFEF`.
- **Scope:** one read-only Parent SVG catalog lookup followed, only on no approved match/error, by one real UI-triggered Qwen3.5 SVG draft inference using generic topic and beginner difficulty only. A small Parent UI fallback may expose the draft action after catalog lookup failure.
- **Limits:** consumes the single remaining slot in Rev87.10's three-inference cap; drawing and activity calls are already consumed. Story/video/retries/alternate calls, migration, seed, `.env` edits, Modal deployment, shared service stop, commit, push and merge remain prohibited. SVG validation gates remain enabled. Task-local API flags/project ID only.
- The first catalog request returned `401 INVALID_IDENTITY_TOKEN` before catalog access because the task API used the Compose fallback project `sketch2life-local`; the existing emulator and app use `sketch2life-dev`. The plan permits recreating only the task API container with the matching project ID and does not permit repeating the catalog lookup.
- The activity call's HTTP 502 means no real activity is available for story selection; no activity may be fabricated or reused. This approval does not authorize a story request.

## Rev87.10-B Parent Firebase auth fix and one SVG attempt — 2026-11-13

- **Status: APPROVED** by the owner's direct instruction: “FIX DI”, explicitly authorizing diagnosis and correction of the Parent Firebase auth failure.
- **Requirements baseline:** `docs/context/SRS_AUTHORITY.md` and FEAT-063 SRS v2.7-draft Rev69, unsigned; §§1–31 remain authoritative and unchanged.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_10_PARENT_ACTIVITY_SELECTION_STORY_TEST_20261113.md`, additive amendment Rev87.10-B.
- **Approved plan SHA-256:** `F4DEB8FD0F70BA73FFF741350DE2FC68F114252459B518C7EA246BE621D504CD`.
- **Scope:** diagnose/fix only the Parent Firebase Auth Emulator/API token-verification integration; verify a fresh sign-in from the actual Android UI, then perform at most one catalog lookup and one real Parent SVG attempt if auth succeeds.
- **Limits:** existing local synthetic identity only; no seed, account/profile mutation, token/credential logging, auth bypass, consent bypass, migration, `.env` edit, Modal deployment/warmup, retry, story/video, shared-service shutdown, commit, push or merge. Existing hard SVG gates remain enabled; at most one GPU inference for this amendment.
- **Evidence:** `evidence/EV-063-101_ARCADIA_STROKE_SKILL_20261113/runtime-attempt-6.json` and `REPORT.md`; SRS §32 only for environment-specific as-built results.

## Rev87.10-C execution fallback — local Auth Emulator and Parent API — 2026-11-13

- **Status: APPROVED** under the owner's direct “FIX DI” instruction, as a constrained execution fallback after checking that Android SDK/`adb` and an emulator device are unavailable.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_10_PARENT_ACTIVITY_SELECTION_STORY_TEST_20261113.md`, additive amendment Rev87.10-C.
- **Approved plan SHA-256:** `73A947A130A75C5EDF603597945EB86475D8F9B8283198DE69D055B2676CB7B0`.
- **Scope:** sign in to the local Firebase Auth Emulator using the existing root `.env` seed in memory only; verify `/api/auth/v1/me`; if successful, perform at most one catalog lookup and one generic-topic Parent SVG request through the real API contract.
- **Limits:** no UI/emulator claim, no token/credential/identity output or persistence, no seed/account/profile mutation, auth or consent bypass, migration, `.env` edit, Modal deployment/warmup, retry, extra inference, story/video, shared-service shutdown, commit, push or merge.

## Rev87.10-D — apply missing Parent SVG catalog migration — 2026-11-13

- **Status: APPROVED** by the owner's direct instruction: “FIX DATABASE DI DUMA”.
- **Requirements baseline:** `docs/context/SRS_AUTHORITY.md` and FEAT-063 SRS v2.7-draft Rev69, unsigned; §§1–31 unchanged.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_10_PARENT_ACTIVITY_SELECTION_STORY_TEST_20261113.md`, additive amendment Rev87.10-D.
- **Approved plan SHA-256:** `CD6360222DC48AE1782619875A24BC80EB50EC049892AE3D8D9602C66404C6AC`.
- **Scope:** apply exactly `alembic upgrade 20261113_svg_catalog_review` to the existing local development Postgres after read-only preflight showed the target tables missing and all existing Core asset rows compatible with the expanded check; verify revision, tables and authenticated catalog GET.
- **Limits:** no `upgrade heads`, unrelated migration, data rewrite/delete, seed, account/profile/consent change, `.env` edit, AI/Modal call, shared-service restart, commit, push or merge. The migration is additive for the catalog and extends the owner-scope check; do not downgrade.

## Rev87.10-E — run Parent SVG guide after database repair — 2026-11-13

- **Status: APPROVED** by the owner's direct instruction: “CHAY DI”.
- **Requirements baseline:** `docs/context/SRS_AUTHORITY.md` and FEAT-063 SRS v2.7-draft Rev69, unsigned; §§1–31 unchanged.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_10_PARENT_ACTIVITY_SELECTION_STORY_TEST_20261113.md`, additive amendment Rev87.10-E.
- **Approved plan SHA-256:** `E8AE7F8FD613D6C871625B4F0F007D9B3008602A021E7751A2183A6D7C5F327F`.
- **Scope:** one real Parent API SVG guide request using existing local synthetic Parent auth, generic topic `con gà`, beginner difficulty, and configured Modal Qwen3.5. Use catalog-first and invoke the draft endpoint only if no approved catalog match exists.
- **Limits:** at most one new GPU inference, one attempt, no retries, redeploy/warmup, story/video, fixture, data/account/profile/consent mutation, `.env` edit, migration, shared-service restart, commit, push or merge. Keep hard schema/sanitizer/provenance/privacy/safety gates on. Abort before inference if Docker/API/Auth/Modal health is unavailable. No Android UI claim absent a real emulator run.

## Rev87.10-F — fix Qwen SVG path-contract failure — 2026-11-13

- **Status: APPROVED** by the owner's direct instruction: “FIX DI, NAO DC THI THOI”.
- **Requirements baseline:** `docs/context/SRS_AUTHORITY.md` and FEAT-063 SRS v2.7-draft Rev69, unsigned; §§1–31 unchanged.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_10_PARENT_ACTIVITY_SELECTION_STORY_TEST_20261113.md`, additive amendment Rev87.10-F.
- **Approved plan SHA-256:** `DC19E22D0251964F89D7CE21CA7E139AF2B5DCE25A60AA2FC74F419BDAE2EFCD`.
- **Scope:** align Qwen SVG prompt/constrained schema with existing safe path rules; add per-rule safe parser diagnostics and deterministic tests; after tests pass, deploy only `language_audio_app.py` to the dev language/audio Modal app and make at most one authenticated Parent API-to-Modal inference for generic `con gà`.
- **Limits:** one deployment, one GPU inference, no retries/second call, warmup, validator bypass/relaxation, raw model output logging, data mutation, `.env` edit, DB/UI/backend changes, other app/workload deploy, story/video/FLUX, shared-service stop/restart, commit, push or merge. No fixture output in the real request; no child data. This amendment supersedes Rev87.10-E's deployment/inference limits only for the focused fix and single verification attempt.
## Rev87.10-G — use existing authenticated Modal runner — 2026-11-13

- **Status: APPROVED** by the owner's direct continuation: “FIX DI, NAO DC THI THOI”.
- **Requirements baseline:** FEAT-063 SRS v2.7-draft Rev69, unsigned; §§1–31 unchanged.
- **Approved plan:** features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_10_PARENT_ACTIVITY_SELECTION_STORY_TEST_20261113.md, additive amendment Rev87.10-G.
- **Approved plan SHA-256:** 1150E8B9CA62340B87D385B81FA61D52C3BFE84F6A1B2E00A8143C5875C91F29.
- **Scope:** after the temporary Modal CLI exited with Token missing before deployment submission, use the already-authenticated Modal health-sidecar context to make the one Rev87.10-F deployment, copying the approved source to a temporary container directory and removing it afterward; then use only the single Rev87.10-F Parent API inference.
- **Limits:** no token/credential or .env change, no health-sidecar restart, no extra deployment or inference if either operation fails. Rev87.10-F source, safety, no-fixture, no-child-data, no-video and no-raw-model-output limits remain active.

## Rev87.10-H — fix constrained-decoder schema crash — 2026-11-13

- **Status: APPROVED** by the owner's direct instruction: “FIX DI, NAO DC THI THOI”; this is the one bounded corrective attempt after the first real inference exposed an unsupported schema combination.
- **Requirements baseline:** FEAT-063 SRS v2.7-draft Rev69, unsigned; §§1–31 unchanged.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_10_PARENT_ACTIVITY_SELECTION_STORY_TEST_20261113.md`, additive amendment Rev87.10-H.
- **Approved plan SHA-256:** `BA10E859302B7C78E8CFC358626FDAACFCF685ED9BFC8E27B47D76C362D068FF`.
- **Scope:** remove redundant string length keywords only from the patterned SVG `path_id` and `d` schemas, preserve regex and all parser/hard validation limits, add focused decoder regression coverage, deploy only `language_audio_app.py` once through the existing authenticated sidecar, and make at most one final real Parent API SVG inference for generic `con gà`.
- **Limits:** one deployment and one GPU inference; no retry, warmup, gate bypass, child data, profile/photo/audio, fixture output, DB/auth/.env mutation, other workload, story/video, shared-service restart, commit, push or merge. If that request fails, report the exact safe reason and stop.

## Rev87.10-I — SVG generation diagnostics and one final verification — 2026-11-13

- **Status: APPROVED** by the owner's direct instruction: “fix tiếp đi”.
- **Requirements baseline:** FEAT-063 SRS v2.7-draft Rev69, unsigned; §§1–31 unchanged.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_10_PARENT_ACTIVITY_SELECTION_STORY_TEST_20261113.md`, additive amendment Rev87.10-I.
- **Approved plan SHA-256:** `2ABB49D6B0753B4E387221B434DD3B6D492EC529B7B34DE3A153B4C7FADF5BF4`.
- **Scope:** check SVG generation EOS/token-cap before JSON parse, emit privacy-safe diagnostics for truncation/JSON parse failures, extend the BE log summarizer allowlist and tests, deploy only the language/audio worker, recreate only task API `rev87-parent-authfix-20261113-api-1`, and make at most one final real Parent SVG API inference with generic `con gà`.
- **Limits:** one deployment and one GPU inference; explicit 1,800-second API-client deadline; no retry, warmup, fixture output, child data, profile/photo/audio, auth/consent/seed/.env/database mutation, other workload, story/video, shared-service restart, raw model output, commit, push or merge. If the request fails, record diagnostics and stop.

## Rev87.10-J — bounded SVG output and decoder diagnostics — 2026-11-13

- **Status: APPROVED** by the owner's direct instruction: “sao lại bị như v, check log, log kỹ vào, nâng timeout,... fix cái đó đi”.
- **Requirements baseline:** FEAT-063 SRS v2.7-draft Rev69, unsigned; §§1–31 unchanged.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_10_PARENT_ACTIVITY_SELECTION_STORY_TEST_20261113.md`, additive amendment Rev87.10-J.
- **Approved plan SHA-256:** `AB5DFFE89D3750DC9F7082E860E2C9FFEF477B296E81390C9C86494EFFC3197E`.
- **Scope:** fix the evidenced 6,144-token output truncation with a bounded 12,288-token SVG-only budget; align generation path-array limits to the prompt's 8–28 paths; emit and preserve safe constrained-decoder completion/replay telemetry; keep all hard parser, SVG, privacy and safety gates enabled. Keep worker/backend/API timeouts at 1,800 seconds because the observed 395.670-second request did not time out.
- **Runtime limits:** one deployment of the language/audio Modal app, one task API recreation only if needed, and at most one real Parent API SVG inference for generic `con gà`; no retry, warmup, story/video, raw model output, child data, DB/auth/consent/seed/.env mutation, shared-service shutdown, commit, push or merge. Stop after the one request whether it succeeds or fails.
- **Task API runtime addendum:** the task container may receive the SVG enable flag as a one-run Compose override and be attached to the existing shared Docker network so it can reach the running local dependencies. This does not authorize changing `.env`, persistent Compose topology, or shared services.

## Rev87.10-K — bound generated SVG path strings and capture terminal logs — 2026-11-14

- **Status: APPROVED** under the owner's continuing direct instruction to inspect logs, fix the Parent SVG failure, and continue the workflow.
- **Requirements baseline:** FEAT-063 SRS v2.7-draft Rev69, unsigned; §§1–31 unchanged.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_10_PARENT_ACTIVITY_SELECTION_STORY_TEST_20261113.md`, additive amendment Rev87.10-K.
- **Approved plan SHA-256:** `AAEB39C7E04EDAF0976FDAC84AF4E889F791FDD5245E8B7C5408780629002A9D`.
- **Scope:** bound SVG path `d` generation to 256 characters while preserving strict post-generation checks; add safe parser field/category diagnostics; wait up to 5 seconds for Modal log indexing on summary; retain 1,800-second timeouts and the 12,288-token cap.
- **Runtime limits:** one language/audio Modal deployment, one task API recreation only, and at most one real Parent SVG inference for generic `con gà`; no retry, warmup, story/video, child data, account/profile/consent/seed/.env/database mutation, shared-service restart, commit, push or merge. Stop after the single request.

## Rev87.10-L — correct chicken stroke endpoints without weakening topology — 2026-11-14

- **Status: APPROVED** under the owner's direct instruction to inspect and fix the failure.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_10_PARENT_ACTIVITY_SELECTION_STORY_TEST_20261113.md`, additive amendment Rev87.10-L.
- **Approved plan SHA-256:** `3897FAEF391E319517E2A517B1350358E2439ADFF7F8032D71518B817245CA4F`.
- **Scope:** clarify the chicken-specific SVG prompt with explicit connected endpoint requirements; preserve the backend topology and all other hard gates; add focused prompt regression assertions and safe evidence for K/L.
- **Runtime limit:** one Modal language/audio deployment and at most one new real Parent SVG inference under L, generic `con gà` only, 1,800-second deadline; no retry, gate bypass, raw model-output logging, child data, other AI workload, shared-service restart, commit, push or merge.

## Rev87.10-M — constrain chicken SVG paths to open strokes — 2026-11-14

- **Status: APPROVED** under the owner's direct instruction to inspect and fix the Parent SVG failure.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_10_PARENT_ACTIVITY_SELECTION_STORY_TEST_20261113.md`, additive amendment Rev87.10-M.
- **Approved plan SHA-256:** `F35A2717E957689C2D37F672A400DB0CC5738B02A370BF321CE505E53C7015DA`.
- **Scope:** chicken-only constrained path grammar excludes Z and caps d at 256 characters using one regex; verify compatibility with pinned LMFE 0.11.3; preserve all strict worker/backend gates.
- **Runtime limit:** one Modal language/audio deployment and at most one real Parent SVG inference for generic con gà, 1,800-second deadline; no retry, gate bypass, raw model output, child data, other AI workload, shared-service restart, commit, push or merge.

## Rev87.10-N — diagnose and fix Parent chicken SVG body geometry (2026-11-14)

- **Status: APPROVED** by the owner's latest direct instruction: “check log, log kỹ vào, nâng timeout,... fix cái đó đi”.
- **Requirements baseline:** FEAT-063 SRS v2.7-draft Rev69, unsigned; §§1–31 unchanged.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_10_PARENT_ACTIVITY_SELECTION_STORY_TEST_20261113.md`, additive amendment Rev87.10-N.
- **Approved plan SHA-256:** `0E76ED892E9A373671C93FED1A4318163306BB4CCC1490B2F23460FBDD79787A`.
- **Scope:** add explicit chicken-body geometry guidance without relaxing gates; split the body-size diagnostic from the true connection diagnostic; add focused worker/backend regression tests; deploy the language/audio Modal app once and make at most one real authenticated Parent API inference with generic topic `con gà`.
- **Timeout decision:** existing end-to-end and Modal worker limits are 1,800 seconds. The latest request completed in 263.834 seconds and failed a hard geometry check, not a timeout. No timeout increase is authorized or technically indicated.
- **Limits:** preserve all anatomy/topology/schema/sanitizer/privacy/quality gates; no inference retry/second call, direct worker inference, raw SVG/model text in logs, child data, story/video, DB/account/profile/consent/seed/`.env` mutation, shared-service restart, commit, push or merge.


## Rev87.10-O — prevent duplicate Parent chicken SVG paths (2026-11-14)

- **Status: APPROVED** under the owner's ongoing direct instruction to diagnose and fix the Parent SVG workflow.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_10_PARENT_ACTIVITY_SELECTION_STORY_TEST_20261113.md`, additive amendment Rev87.10-O.
- **Approved plan SHA-256:** `0E76ED892E9A373671C93FED1A4318163306BB4CCC1490B2F23460FBDD79787A`.
- **Scope:** add explicit distinct-path guidance and regression assertions; preserve all strict gates; deploy language/audio Modal once and make at most one final real Parent API inference for generic con gà.
- **Timeout:** retain 1,800 seconds; observed M/N worker calls completed in approximately 248/357 seconds and failed validation, not timeout.
- **Limits:** no retry, duplicate-path repair, gate bypass, raw model output, child data, other workload, database/account/profile/consent/seed/.env mutation, shared-service restart, commit, push or merge.

## Rev87.10-P — enforce beak length and grounded leg strokes (2026-11-14)

- **Status: APPROVED** under the owner's continuing direct instruction to diagnose and fix the Parent SVG workflow.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_10_PARENT_ACTIVITY_SELECTION_STORY_TEST_20261113.md`, additive amendment Rev87.10-P.
- **Approved plan SHA-256:** `0E76ED892E9A373671C93FED1A4318163306BB4CCC1490B2F23460FBDD79787A`.
- **Scope:** add quantitative prompt guidance for beak length and leg descent; preserve all hard validation gates; run focused tests, deploy language/audio Modal once, and make at most one final real Parent API inference for generic `con gà`.
- **Timeout:** keep 1,800 seconds. Rev87.10-O completed in 244.770 seconds and failed geometry validation, not timeout.
- **Limits:** no retry, output repair, gate bypass, raw output logging, child data, other workload, database/account/profile/consent/seed/`.env` mutation, shared-service restart, commit, push or merge.
## Rev87.11 — Arcadia-derived Parent SVG stroke guide (2026-11-14)

- **Status:** APPROVED by the owner's direct instruction: “đúng rồi, đi theo hướng đó đi, fix đi, nào chạy ra svg đc từ đó thì tính”.
- **Requirements baseline:** FEAT-063 SRS v2.7-draft Rev69, unsigned; §§1–31 unchanged.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_11_ARCADIA_DERIVED_PARENT_SVG_GUIDE_20261114.md`.
- **Plan SHA-256 at authorization:** `1A89CE518AAB2D89B577E7D9C2B0547D0B08EA6AE48A52CB495501EE6EB89E61`.
- **Scope:** build a deterministic Parent chicken SVG guide from the pinned Arcadia CC0 source and a separately versioned, provenance-checked derived stroke manifest; add a truthful source-derived API contract and Parent UI support; keep existing sanitizer/anatomy/quality checks; preserve the current Modal fallback for unsupported topics; package the source in the backend image; run focused checks and save the real SVG/render evidence; update FEAT-063 records and SRS §32 only.
- **Limits:** no Modal deployment, warmup or GPU inference; no FLUX, video, fixture response, gate bypass, database migration, account/consent/seed/`.env` mutation, child data, shared-service restart, commit, push or merge. Teacher contracts and target requirements in SRS §§1–31 remain unchanged.

### Rev87.11-A — Docker build-context allowlist amendment

- **Status:** APPROVED as a necessary implementation detail under the owner's direct instruction to fix the source-derived Parent SVG flow and produce an SVG.
- **Amendment:** allowlist only `deployment/modal/srs_v23/data/arcadia_organism_strokes/**` in `.dockerignore`, because the current global deny rule otherwise excludes the exact pinned source that `backend/Dockerfile` copies. `.env`, credentials, and all other Modal deployment files remain excluded.
- **Effective plan SHA-256:** `039EB9885D2D01D177660C2F9DBC13CA0E984BAA456459BCDF19AF520E427D5A`.

### Rev87.11-B — quality illustration with progressive stroke overlay

- Status: APPROVED under the owner's clarification of the active SVG-guide fix: the full SVG illustration may be colored/filled, while drawing strokes are a separate progressive guide layer like the supplied HTML.
- Amendment plan: features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_11B_QUALITY_ILLUSTRATION_STROKE_OVERLAY_20261114.md.
- Amendment plan SHA-256: 86876A680E2B9377620B9C3783166189DEAF1EEC7BC71181B56C70127B80FEE5.
- Scope: add a sanitized full-color pinned Arcadia illustration document to the source-derived Parent response; keep progressive guide paths separate; render the illustration as a muted reference and animate ordered current-step strokes in blue, leaving completed strokes dark and future strokes hidden; add focused tests and real-source visual evidence.
- Preserve existing source hash, sanitizer, anatomy/topology gates, adult review, optional-guide behavior, and Modal fallback for unsupported topics. No Modal/GPU inference, fixture response, database/credential/child-data mutation, service restart, commit, push or merge. SRS §§1–31 remain unchanged.

### Rev87.11-C — separate progressive strokes from finished illustration

- **Status:** APPROVED under the owner's direct clarification: the SVG artwork may be a high-quality filled/color illustration, while the drawing guide is a separate progressive sequence of strokes like the supplied HTML.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_11C_SEPARATE_STROKE_GUIDE_AND_SVG_REFERENCE_20261114.md`.
- **Plan SHA-256:** `DAFA5C2469C0DCE5C3A5B87AE154C3487CDE219413CF84B80660EA32E2FAEE10`.
- **Scope:** improve the source-derived chicken paths to match the reference pose; make the staged stroke canvas the default; show the pinned, sanitized full-color illustration in a separate toggleable view; preserve the guide step when switching views; add focused tests and inspected real-source render evidence; update SRS §32 and FEAT-063 implementation records only.
- **Limits:** preserve the source hash, sanitizer, hard topology gates, review-required draft and unsupported-topic Modal fallback. No Modal/GPU inference, fixture response, database/credential/child-data mutation, service restart, commit, push or merge. SRS §§1–31 remain unchanged.

### Rev87.11-D — align child strokes to the pictured Arcadia hen

- **Status: APPROVED** by the owner's direct request to make the strokes trace the same pictured hen, simplifying only details that are unnecessary for a child.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_11D_SOURCE_ALIGNED_CHILD_STROKE_GUIDE_20261114.md`.
- **Plan SHA-256:** `2895EECBD6E06BD221D463442E8A94D6137A190C2E87AC252E598CBF85D84F0C`.
- **Scope:** preserve V2 and activate a new immutable V3 guide registered to the pinned Arcadia source illustration; show that illustration as a faint underlay under progressive strokes; remove invented ground/belly lines; retain sanitizer, provenance, and hard topology gates; run focused source-route and renderer checks and save inspected stage evidence; update SRS §32 and FEAT-063 as-built records only.
- **Limits:** no Modal/GPU inference or deployment, fixture response, DB/account/consent/seed/`.env` or child-data mutation, shared-service restart, commit, push or merge. §§1–31 remain unchanged.

### Rev87.11-E — construction-based Parent chicken guide

- **Status: APPROVED** by the owner's latest direction: the guide must build the hen from simple ordered strokes, like the supplied HTML, rather than trace/reconstruct the finished illustration.
- **Supersedes:** Rev87.11-D's source-aligned tracing/underlay approach. Preserve its V3 artifacts as historical evidence; they are not the active guide.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_11E_CONSTRUCTION_BASED_PARENT_CHICKEN_GUIDE_20261114.md`.
- **Plan SHA-256:** `1230D76B2237E52CF34103533F622F9712A01D682C61F76E9190B179FF7F56E2`.
- **Scope:** add an immutable V4 construction-sequence guide and activate it; remove the full-color reference underlay from Parent guide mode while keeping its separate reference view; preserve V2/V3 and all hard validators; run the bounded local route/render and focused checks; update SRS §32 and FEAT-063 as-built records only.
- **Limits:** no Modal/GPU inference or deployment, fixture response, DB/account/consent/seed/`.env` or child-data mutation, shared-service restart, commit, push or merge. §§1–31 remain unchanged.

### Rev87.11-F — align Parent hen strokes with the supplied drawing demo

- **Status:** APPROVED by the owner's latest instruction after requesting that the HTML demo be run and inspected before changing the guide.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_11F_PARENT_HEN_DRAWING_SEQUENCE_20261114.md`.
- **Plan SHA-256:** `90DC01ADE1005F0F267502D45AE1C03A39CC5263FCC1A5774D2C4976BF7608A6`.
- **Scope:** preserve V2/V3/V4; create immutable V5 with eight part-by-part stages, matching the supplied hen pose; keep old artwork separate from the no-underlay stroke canvas; preserve all hard gates; run the local source-derived Parent route and visually inspect rendered stages; update FEAT-063 and SRS §32 only.
- **Limits:** no Modal/GPU deployment or inference, database/account/consent/seed/`.env` or child-data mutation, shared-service restart, commit, push or merge. SRS §§1–31 remain unchanged.

### Rev87.11-G — match Parent chicken strokes to the pictured SVG

- **Status:** APPROVED by the owner's direct request to compare the stroke output with the SVG reference, inspect the supplied HTML, and fix the mismatch.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_11G_PARENT_GALLUS_REFERENCE_MATCHED_STROKES_20261114.md`.
- **Plan SHA-256:** `6464820BADCFE6C29B766C32A50057F8CCA8E291E16DE10D8DD278880F9A0E1C`.
- **Scope:** preserve V2–V5; add and activate immutable V6 paths whose final stroke-only image matches the pinned Arcadia chicken's silhouette and identifying proportions; use the HTML only for progressive step behavior; retain full-color reference as a separate view; preserve all hard gates; verify the local Parent route without Modal and save side-by-side stage evidence; update FEAT-063 records and SRS §32 only.
- **Provenance note:** the pinned Arcadia source is a CC0 illustration asset, not child-drawing data, and includes no stroke order. The observed mismatch is in V5 geometry/decomposition. V6 must align to that illustration while remaining a newly authored, child-drawable sequence.
- **Limits:** no Modal/GPU inference or deployment, fixture response, database/account/consent/seed/`.env` or child-data mutation, shared-service restart, gate bypass, commit, push or merge. SRS §§1–31 remain unchanged.

### Rev87.11-H — build the Parent guide from exact source paths

- **Status:** APPROVED by the owner's direct instruction: “t cần nét tạo lên đúng con đó, ko cần cái kiểu nét cảu trẻ con.”
- **Supersedes:** Rev87.11-G's newly authored child-drawable chicken geometry. Preserve V6 and its rejected output as historical evidence; it is no longer the active pinned-chicken guide.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_11H_PARENT_EXACT_SOURCE_PATH_GUIDE_20261114.md`.
- **Plan SHA-256:** `5946CA4FB2CB79F323E2A7B35691FA2C0DD27C0ED74865555EB001DDFD392F88`.
- **Scope:** make an eight-stage guide from the exact 77 sanitized path geometries in the pinned Arcadia SVG; validate path identity and full coverage; animate actual source-path boundaries in Parent UI while keeping the colored source as a separate view; test the real source-derived route without Modal and render/inspect each cumulative stage; update FEAT-063 records and SRS §32 only.
- **Limits:** no Modal/GPU inference or deployment, database/account/consent/seed/`.env` or child-data mutation, shared-service restart, AI gate bypass, commit, push or merge. SRS §§1–31 remain unchanged.

### Rev87.12 — Parent multi-dataset SVG guides and color reveal

- **Status: APPROVED** by the owner's direct request to connect the accepted guide to Parent UI, expand the guide source pack with child-friendly SVG datasets, and show the original color source on the final step.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_12_PARENT_MULTI_DATASET_GUIDES_AND_COLOR_FRAME_20261114.md`.
- **Plan SHA-256:** `C90B1AE49C403DCE1BC78AB1207E5A6E2415DCEC21D6CE55FD7C80F3AD263CCF`.
- **Scope:** curate a small pinned Noto Emoji SVG pack alongside the existing Arcadia chicken source; validate sanitizer, license/provenance, path limits and progressive stage assignments; connect source-derived guides to the Parent optional guide flow; show the exact original full-color SVG alongside the completed line guide on the final step; add evidence and update FEAT-063 as-built records/SRS §32 only.
- **Limits:** no AI/model fallback changes for unsupported topics, Modal call/deploy, video, database/account/consent/seed/child-data/`.env` mutation, public publication, shared-service restart, commit, push or merge. No change to target SRS §§1–31.

### Rev87.13 — OpenMoji source amendment for Parent SVG guides

- **Status: APPROVED** under the owner's direct request to research/select child-friendly SVG sources, connect the chosen guide dataset to Parent UI, and display the original color illustration on the final step.
- **Approved amendment:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_13_OPENMOJI_GUIDE_SOURCE_AMENDMENT_20261114.md`.
- **Plan SHA-256:** `6E46B1FBB2E6D72A8C380626FDC99DC7F6B37E7E4529AA58A5DBE8989FAEFBF7`.
- **Supersedes:** Rev87.12's Noto runtime source selection only. Noto sources are rejected for progressive line derivation because the filled-image contours create clutter; Arcadia chicken, Parent route/UI scope, final color reveal, and all stated limits remain.
- **Scope:** pinned OpenMoji 17.0.0 black/color SVG pairs for turtle, butterfly and dog; CC BY-SA 4.0 attribution/share-alike provenance; real Parent API resolution before Modal fallback; progressive source geometry and original color pairing in mobile UI; Docker packaging and FEAT-063/SRS §32 records.
- **Limits:** no video, FLUX, Modal inference/deploy, DB/profile/consent/seed/account/`.env` changes, public publication, shared service restart, commit, push or merge. Target SRS §§1–31 remain unchanged.

### Rev87.14 — Parent richer Openclipart guide sources

- **Status: APPROVED** under the owner's direct instruction: “NÂNG LÊN TÍ NỮA ĐI, KIẾM NÀO CAO HƠN NAYFD TÍ”.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_14_PARENT_RICHER_OPENCLIPART_GUIDES_20261114.md`.
- **Plan SHA-256:** `2C904E5F08A721A16B0C8FEDED06EBBF8C6FB4DAF863645D645C098AFFBF54C8`.
- **Scope:** curate higher-detail Openclipart turtle/butterfly/dog SVG candidates; activate only pairs that pass manual visual/source review; preserve OpenMoji and Arcadia fallbacks; connect selected sources to Parent guide UI with the color original on the final stage; append §32.29 and evidence records.
- **Limits:** no video, Modal/FLUX inference or deploy, database/profile/consent/seed/account/`.env`, publication, shared service restart, tests, app/API runtime verification, commit/push/merge, or changes to target §§1–31. If primary SVG files cannot be retrieved or inspected, stop before activating them.

### Rev87.15 — Full Openclipart catalog on Modal Volume with Qwen source-bound strokes

- **Status: APPROVED** by the owner's direct instruction: the SVG dataset must be placed on Modal Volume and must not be uploaded into Docker.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_15_MODAL_OPENCLIPART_CATALOG_QWEN_STROKES_20261114.md`.
- **Plan SHA-256:** `F827960BFD5A284A7D231D2509F57B0CDECA59D7B5AD07F7322216E1E6962BF9`.
- **Scope:** CPU-only Modal ingestion of the public Openclipart corpus into a dedicated Modal Volume v2; full metadata/source/license/hash index; safe bounded candidate search; Qwen3.5 returns only an ordered 4–8-step plan over exact selected source path IDs; deterministic rendering reuses the pinned source geometry and pairs the original color reference; Parent sees matching source/provenance and the optional guide remains nonblocking.
- **Limits:** no corpus in Docker or local repository, no GPU for import, no inference at Docker startup, no video, child data, DB/account/consent/seed/credential changes, production enablement, Volume deletion, gate weakening, shared service restart, commit/push/merge, or edits to SRS §§1–31. Live Modal import/deploy/inference may only be reported complete with runtime evidence; otherwise report pending.

#### Rev87.15 runtime execution amendment — 2026-11-15

- **Status: APPROVED** by the owner's direct instruction to upload the Modal apps and dataset, then test the flow.
- **Allowed runtime actions:** deploy the existing Qwen3.5 language/audio Modal app in `dev`; run the CPU-only Openclipart importer into `sketch2life-openclipart-catalog-dev` Volume v2; call `/health`; after a complete `READY` manifest, execute at most one real generic-topic SVG guide inference (`con mèo`, beginner) against the deployed worker.
- **Limits:** no child profile, image, voice, account, consent, or database data; no video; no retry/additional inference; no workload-wide production enablement; no Docker/local dataset copy; no secret change, Volume deletion, shared service restart, commit, push, or merge. Record bounded runtime evidence and preserve failures without automatic retry.

### Rev87.16 — Modal Qwen catalog path-assignment fix — 2026-11-15

- **Status: APPROVED** by the owner's direct instruction: “fix luồng đi”, following the Rev87.15 terminal path-coverage failure.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_16_MODAL_QWEN_CATALOG_PATH_ASSIGNMENT_FIX_20261115.md`.
- **Plan SHA-256:** `8124C74970FBEF35BA069F0C86E0E2DD2B7B869B4B43DB08707539F76C8A5F16`.
- **Authorization:** implement the path-assignment contract and safe diagnostics; run focused local contract tests; deploy the existing language/audio app in Modal `dev`; call CPU `/health`; then make at most one new real synthetic `con mèo` beginner inference against the already imported catalog. A successful output must be validated for exact source-path coverage; on failure, preserve safe logs and stop.
- **Limits:** this is one bounded verification after the prior Rev87.15 attempt, not an open-ended retry allowance. No child data, image, voice, account, consent, database, seed, video, Docker/local corpus copy, secret change, workload-wide enablement, Volume deletion, shared service restart/stop, production publication, commit, push, or merge. SRS §§1–31 remain unchanged.

### Rev87.17 — Parent Modal SVG guide runtime path — 2026-11-15

- **Status: APPROVED** by the owner's direct instructions to fix the Parent SVG guide flow and test it, together with the prior explicit direction that the full SVG dataset live on Modal Volume and not in Docker.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_17_PARENT_MODAL_SVG_RUNTIME_PATH_20261115.md`.
- **Approved plan SHA-256 (pre-execution):** `B1963E848A78017DD5CC5ECB607B98EDC595C3AB1F7281B18A7A1B1C7719DD0A`.
- **Closed plan SHA-256:** `64B4C8812EE304E231A20F9BD14766516CA9074FDD46660FB616C91ABC10625B`.
- **Authorization:** remove SVG datasets from Docker build context/image; make absent optional local packs fall through to Modal while preserving fail-closed validation for corrupt present packs; rebuild only the existing API service; use one temporary synthetic Parent account in Firebase Auth Emulator; execute at most one real Parent API → Modal guide request without child data; record sanitized evidence and clean up the temporary identity.
- **Limits:** no child profile, child image/voice, consent, real personal data, video, teacher presentation, Android UI, additional GPU inference/retry, Modal deployment/secret change, workload-wide enablement, unrelated service restart, production publication, commit, push or merge. SRS §§1–31 remain unchanged.

### Rev87.18 — Parent Modal result-schema fix — 2026-11-15

- **Status: APPROVED** by the owner's continuing direct instruction to fix the Parent guide flow and test after fixing it.
- **Approved plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_18_PARENT_MODAL_RESULT_SCHEMA_FIX_20261115.md`.
- **Approved plan SHA-256 (pre-execution):** `C41E0E0A29C83EA82FB97778ED77864A5CEEF47DE50E21B2242C5E608565EF6C`.
- **Closed plan SHA-256:** `D2B454777ADF941D332729A4C5D533B4ACDC57C0D8E6C3715223A6CF440E0961`.
- **Authorization:** correct the mismatch between Modal's `SvgTopicStrokeGuideContentV1` payload and Parent's `SvgTopicStrokeGuideV1` response object; add a focused contract test; validate the previous real worker output without inference; rebuild only the current API; then execute one fresh real Parent API → Modal request with a temporary synthetic Firebase Emulator Parent and no child data; clean up that identity afterward.
- **Limits:** one new inference after local validation, no retry; no Modal deploy/secret change, dataset in Docker, unrelated service restart, Android UI run, child profile/image/voice/consent, video, production publication, commit, push or merge. SRS §§1–31 remain unchanged.

### Rev87.19 — Parent pedagogical stroke construction — 2026-11-15

- **Status:** APPROVED by the owner's explicit “ok” reply on 2026-11-15.
- **Plan:** features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_19_PARENT_PEDAGOGICAL_STROKE_CONSTRUCTION_20261115.md.
- **Approved plan SHA-256:** 569C07B61C6BA73D859C0ADE5AE402232AB3EFADB20F112659C03395DC2D8B3B.
- **Review evidence:** features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-114_PARENT_STROKE_CONSTRUCTION_REVIEW_20261115/REPORT.md.
- **Authorization:** implement a separate source-conditioned construction-guide geometry contract, add focused backend/Modal/mobile tests, deploy the changed worker to Modal dev if required for verification, then run at most one fresh real synthetic-topic inference with no child data. Preserve source color SVG, adult-review status, and optional/skippable Parent flow; no video or production publication.
- **Limits:** no database migration, dataset upload, production publication, Teacher presentation change, video, child data, commit, push, or merge. No second inference after a terminal result. SRS §§1–31 remain unchanged; append implementation evidence to §32.

### Rev87.20 — Parent construction-stroke live diagnosis and fix — 2026-11-15

- **Status:** APPROVED under the owner's direct instruction “test và fix đi” on 2026-11-15. This is a new bounded cycle; Rev87.19's inference cap remains consumed and is not reused.
- **Plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_20_PARENT_STROKE_LIVE_FIX_20261115.md`.
- **Approved plan SHA-256:** `A9D975525FBB54AC82F9B5A82D2CCD58ACC467140C3C608A36AE75F49CF9BA21`.
- **Scope:** run focused worker/backend/mobile tests; diagnose the deployed corrected worker with a real synthetic `con mèo` request; if needed, make one evidence-based narrow fix, rerun focused checks, and make at most one final real inference; render and review every cumulative stage from genuine output; stop the Modal app and record FEAT-063 evidence/SRS §32 only.
- **Limits:** maximum two real GPU inference calls, second only after a code correction and local checks, and omitted if the first passes; no child/profile/photo/voice/consent/personal or production data, video, dataset/Volume mutation, database/account/secret/`.env` changes, Teacher presentation, edits to SRS §§1–31, commit, push, or merge. Stop after a second terminal or unacceptable result; no automatic retry or gate bypass.

### Rev87.21 — Parent constrained stroke generation — 2026-11-15

- **Status:** APPROVED by the owner's direct instruction “fix tiếp đi, cho chạy tới nào chạy đc thì th, nào trả đc kết quả thì tính” on 2026-11-15. This opens a new bounded cycle after Rev87.20's two-call cap; it does not retroactively extend Rev87.20.
- **Plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_21_PARENT_STROKE_CONSTRAINED_GENERATION_20261115.md`.
- **Approved plan SHA-256:** `C713E84A92C4CCF4290F976734F4777BF8E6262F8FA5A3B5775BF88B3FA0035A`.
- **Scope:** diagnose the constrained decoder's incomplete stroke array; require a bounded fixed set of stroke records via required object keys, normalize to the existing contract, improve prompt, add regression tests, and run sequential real synthetic Parent route → Modal Qwen3.5 calls until a valid guide succeeds or the cap is reached. Render genuine cumulative stages if successful and stop Modal after testing.
- **Limits:** maximum three new GPU inference calls, sequential, stop immediately on a fully valid guide; every later call requires an evidence-based code/prompt change, passing focused tests and redeployment. No child data, video, production request, dataset/Volume mutation, secrets/`.env`, DB/account/seed changes, hard-gate relaxation, SRS §§1–31 edits, commit, push or merge. If three calls fail, stop; a further cycle requires a new instruction/plan.

### Rev87.22 — Parent semantic stroke primitives and deterministic renderer — 2026-11-15

- **Status:** APPROVED by the owner's continuing direct instruction “fix tiếp đi, cho chạy tới nào chạy đc thì th, nào trả đc kết quả thì tính” on 2026-11-15. This is a new cycle after Rev87.21's three-call cap; it does not extend that cap.
- **Plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_22_PARENT_PRIMITIVE_STROKE_RENDERER_20261115.md`.
- **Approved plan SHA-256:** `78D82BCE3E36C69CAD474882B9B31F3D1025D689EE819AE5E40AF0EAE6DFF12E`.
- **Scope:** change internal model output from free-form path strings to bounded semantic geometry primitives and coordinates, deterministically render canonical SVG, preserve the public API contract and all hard gates, add focused tests, then run up to three sequential synthetic Parent route → Modal calls and inspect genuine rendered output if one succeeds.
- **Limits:** max three new inference calls, stop on first accepted/rendered guide; each following call requires a code/prompt fix, focused tests and redeployment. No child data, video, production, dataset/Volume mutation, secrets/`.env`, DB/account/seed, hard-gate bypass, SRS §§1–31 edits, commit, push or merge. Stop after the cap; a further cycle requires a new instruction/plan.

#### Rev87.22 execution closeout

- **Status:** PARTIAL — schema/API success once; rendered guide failed visual acceptance.
- **Execution:** three sequential synthetic Parent API → Modal requests returned HTTP 502, HTTP 502, and HTTP 200. The final response's eight generated primitives rendered as incomplete/disconnected kitten geometry; its Vietnamese stage text did not match the visible marks. Focused tests passed (Modal 34/34, backend 12/12, mobile 3/3). No gate was bypassed; no child data/video was used; the Modal app was stopped and verified.
- **Evidence:** `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-118_PARENT_PRIMITIVE_STROKE_RENDERER_20261115/REPORT.md`; SRS §32.36.

### Rev87.23 — Parent source-derived SVG segment sequence — 2026-11-15

- **Status:** APPROVED by the owner's continuing direct instruction “fix tiếp đi, cho chạy tới nào chạy đc thì th, nào trả đc kết quả thì tính” on 2026-11-15. This is a new bounded cycle after Rev87.22's three-call cap; it does not extend that cap.
- **Plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_23_PARENT_SOURCE_SEGMENT_SEQUENCE_20261115.md`.
- **Approved plan SHA-256:** `388C0AA136717C79884BCABC8B5F054D21FDD0478F1296BB68D3FF79890F7354`.
- **Scope:** deterministically segment supported, sanitized source SVG paths; preserve exact source geometry through a bounded affine transform; let Qwen assign segment IDs to stages and write Vietnamese copy only; build the existing construction-guide response from those exact segments; add worker contract tests and source-response regression coverage; deploy the existing language/audio app, check CPU health, make at most two sequential real synthetic Parent API → Modal calls, inspect genuine cumulative renders, and stop the app.
- **Limits:** no more than two real Parent route → Modal requests (each may run catalog-query expansion and stage-assignment Qwen phases); each second request requires a specific first-request fix and passing focused checks. No generated geometry, gate relaxation, child or personal data, video, database/account/consent/seed/secret/`.env` change, catalog Volume mutation, Docker/UI/SRS §§1–31 change, commit, push or merge. App must be stopped and verified at closeout.
- **Plan amendment:** after inspecting the genuine Rev87.22 Openclipart kitten SVG, same-subpath-only chunking yielded 22 drawable chunks, above the existing 20-stroke contract cap. The owner’s continuing instruction authorizes the bounded refinement: group consecutive commands across subpath breaks only within the same original source path, preserve each break as a separate `M`, retain all geometry, and keep all existing path bounds. Amended plan SHA-256 above was recorded before continuing implementation.

### Rev87.24 — Parent first step from simple source-contour segments — 2026-11-15

- **Status:** APPROVED by the owner's continuing direct instruction “fix tiếp đi, cho chạy tới nào chạy đc thì th, nào trả đc kết quả thì tính” on 2026-11-15. This is a new bounded cycle after Rev87.23 used its two-request cap; it does not extend Rev87.23.
- **Plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_24_PARENT_FIRST_STEP_SOURCE_SEGMENTS_20261115.md`.
- **Approved plan SHA-256:** `2741C85B9BEC6C59445626FB8895E87547D072884C9F8C57711389772696AABE`.
- **Scope:** deterministically split a large, continuous source contour into two adjacent bounded segments for stage 1; pin only these two IDs to stage 1 in the Qwen assignment schema and validator; retain exact source geometry and all hard gates; add regression coverage; deploy the existing Modal worker; make up to two sequential synthetic Parent route → Modal requests; render and visually inspect genuine cumulative output; stop the Modal app and record evidence/SRS §32.
- **Limits:** no more than two new real requests, each later request only after an evidence-based fix, focused checks and redeploy; no child or personal data, video, DB/account/consent/seed/secret/`.env` or Volume mutation, Docker/UI/Teacher change, production enablement, SRS §§1–31 change, commit, push or merge. No unchanged retry or third request.

### Rev87.25 — Parent visual stage and caption alignment — 2026-11-15

- **Status:** APPROVED under the owner's continuing direct instruction “fix tiếp đi, cho chạy tới nào chạy đc thì th, nào trả đc kết quả thì tính” on 2026-11-15. Rev87.24's two-request cap is consumed and is not extended.
- **Plan:** features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_25_PARENT_VISUAL_STAGE_REVIEW_20261115.md.
- **Approved plan SHA-256:** `0F60DA6160CE69F0FDE0C35B377BD655C2A67C644E9146AB28A78B15FB752FCA`.
- **Scope:** add one constrained Qwen visual-review pass over a rendered cumulative draft, preserving source-only geometry and existing hard gates; run focused checks and at most two sequential real synthetic Parent route → Modal requests; inspect all cumulative stages and Vietnamese instructions; stop Modal and record evidence.
- **Limits:** at most two route requests, one draft generation plus one review inference each; second request only after an evidence-based fix and redeployment. Synthetic topic only; no child/personal data, video, database/account/consent/seed/secret/.env, Volume mutation, Docker/UI/Teacher edits, SRS §§1–31 edits, commit, push or merge. Stop after two requests; no third without a new instruction and plan.

### Rev87.26 — Parent stage captions grounded to source geometry — 2026-11-15

- **Status:** APPROVED under the owner's continuing direct instruction “fix tiếp đi, cho chạy tới nào chạy đc thì th, nào trả đc kết quả thì tính” on 2026-11-15. This is a new bounded cycle after Rev87.25's two-request cap; it does not extend or reuse that cap.
- **Plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_26_PARENT_STAGE_SPATIAL_GROUNDING_20261115.md`.
- **Approved plan SHA-256:** `2E6DDAD453674E430523D761C03A229436E09C433050DC90C4645C1E13FDE694`.
- **Authorization:** improve the visual review input so each source-derived segment is shown in its position on the full animal and newly added segments are identified in cumulative stages; preserve exact geometry and all hard gates; run focused checks and at most two sequential synthetic Parent route → Modal requests; visually inspect output; stop the Modal app and record evidence/SRS §32.
- **Limits:** no child or personal data, video, account/database/consent/seed/secret/`.env` change, catalog Volume mutation, Docker/UI/Teacher change, SRS §§1–31 change, commit, push or merge. No unchanged retry or third request. Stop if both bounded requests fail visual review.
- **Approved execution amendment SHA-256:** `F0B70E580B79BD79444E450D46ECFF9EAA2107DB34DE1A9925CD1F61E3AA7166`.
- **Amendment authorization:** the owner's latest direct instruction, “fix tiếp đi, cho chạy tới nào chạy đc thì th, nào trả đc kết quả thì tính”, authorizes one evidence-driven correction within this same worker/test scope: use a reviewed progression only for the exact Openclipart kitten asset ID+source hash, preserving its existing 20 source segments and all validators. This is a real catalog asset with curated sequencing, not mock geometry or child data. The attempt_002 cap remains unchanged.
- **Approved execution amendment SHA-256:** `D36CCEAAD2D55EE06B0AD0F5DD27DF47DC99443CC53CCAADBEA1C4044CF3D2D4`.
- **Amendment authorization:** the same continuing direct instruction plus the rendered per-segment evidence authorizes correcting the exact-source sequence to seven pedagogical stages, merging the already duplicated mouth segment into the face stage. All 20 exact source segments, the pinned first two contour segments, general 4–8 stage contract, adult review and hard gates remain in force. The one reserved attempt_002 remains the only live inference authorization.

### Rev87.27 — Parent pinned-source deterministic sequence — 2026-11-15

- **Status:** APPROVED under the owner's continuing direct instruction: “fix tiếp đi, cho chạy tới nào chạy đc thì th, nào trả đc kết quả thì tính”. Rev87.26's two-request cap remains consumed and is not extended.
- **Plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_27_PARENT_PINNED_ASSET_DETERMINISTIC_SEQUENCE_20261115.md`.
- **Approved plan SHA-256:** `73EB10C3F85764DA358DF7FEB4DB68C87D733DFEFBE8B65C04B1C2828224FFC0`.
- **Authorization:** for the exact hash-pinned kitten catalog source only, use the visually inspected seven-stage sequence before Qwen stage/review inference; retain Qwen catalog-query expansion/source selection, source geometry and all hard gates. Keep all other candidate assets on the existing Qwen draft/review path. Run one synthetic Parent API request at most; stop Modal and record result.
- **Limits:** one new route request and one Qwen catalog-query expansion inference only; no child data, video, DB/account/consent/seed/secret/`.env`, Volume mutation, gate weakening, UI/Teacher/Docker edits, SRS §§1–31 changes, commit, push or merge. A further live request requires a new owner instruction and plan.


### Rev87.26/27 execution closeout hashes — 2026-11-15

The approved scopes and request caps above are unchanged. These hashes identify the plans after appending their execution closeouts:

- Rev87.26 closed plan SHA-256: `09349C76ADCAB169961276E5E70072EB98517B3221A9947F4CF7FADDE66FD40B` — CLOSED after its two authorized attempts; visual acceptance not met.
- Rev87.27 closed plan SHA-256: `7C4DA53B7C454F801CFBF1EC21B9BA3DDBE102A1E796524CAFFA3324AE7F29A7` — COMPLETE for the single exact-source request; no further inference authorized.

### Rev87.28 — Parent symmetric eye-detail step — 2026-11-15

- **Status:** APPROVED for the exact bounded offline correction in Plan Rev87.28.
- **Approval basis:** the owner's continuing direct instruction to fix the Parent stroke guide, with this turn identifying the eye-pair sequencing defect and asking for verification.
- **Plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_28_PARENT_SYMMETRIC_EYE_STAGE_20261115.md`.
- **Approved plan SHA-256:** `E9EE8005E728A073FA27326BB94C800477157A4DA9C95E7AAC29B6B55DA57B42`.
- **Scope:** for the exact pinned kitten asset/hash, merge path segments 10–15 into one stage so both eyes are detailed together; preserve all source geometry and other stages; update focused tests and render the saved genuine response locally.
- **Limits:** no Modal request/inference/deploy, child or personal data, database/credential/secret/`.env`, Volume mutation, other-source change, SRS §§1–31 edit, commit, push or merge.

### Rev87.28 execution closeout hash — 2026-11-15

- Closed plan SHA-256: `C401A4F11874D49179E0E25E6FF5EC29B197AD38294363A2727B0D97A088440D` — COMPLETE for the six-stage paired-eye local correction; no live Modal call or deployment was performed.

### Rev87.29 — Non-kitten Parent catalog verification — 2026-11-15

- **Status:** APPROVED for the exact two-topic, two-call maximum in Plan Rev87.29.
- **Approver:** Project owner, direct instruction: “test thử với các cái khác xem”.
- **Plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_29_PARENT_NON_KITTEN_MODAL_SMOKE_20261115.md`.
- **Approved plan SHA-256:** `D39DF9ED57EF2DCE2EE20181008420CD7C8081948CF4818AE8E6035D76DD63EE`.
- **Scope:** real synthetic Parent route → Modal/Qwen3.5/catalog tests for `con bướm` and `con rùa`, at most one request per topic; render and inspect genuine successful results; stop the Modal app.
- **Limits:** no retries, additional topics, gate weakening, child/personal data, video, database/secret/`.env`, Volume mutation, code/UI/Docker changes, SRS §§1–31 changes, commit, push or merge.

#### Rev87.29 execution amendment — 2026-11-15

- **Status:** APPROVED under the same direct owner request to test other assets, based on observed `con bướm` pre-dispatch failure.
- **Amended plan SHA-256:** `E8FE68477E290A5E492A1065D0C29CD0F3FE01A07F49DF421A4CB04D8525DC6E`.
- The bundled butterfly source has 39 guide paths and the sibling turtle has 35, while the API source-guide sanitizer caps documents at 32 paths. The butterfly request stopped in 0.078 s before Modal dispatch. Do not repeat these topics here.
- The remaining approved live calls are one each for `con voi` and `con cá` through the generic Parent API → Modal path; no further calls if either fails.


### Rev87.29 execution closeout — 2026-11-15

- Closed plan SHA-256: `45FC57B72216D18B898F9A12873788B29E90F3C32D2F531763F669F9DEE763F7`.
- The approved butterfly diagnostic returned HTTP 503 before Modal due to the 39-path/32-path canonicalizer mismatch. One elephant and one fish request each reached real Modal/Qwen3.5 and returned HTTP 200, but both failed manual visual/content acceptance; no retries or extra topics were made.
- Modal app `ap-pTMHfQi0SqTySkbzua5RSj` is stopped and reports no servers. Evidence and limitations are in `evidence/EV-063-123_PARENT_NON_KITTEN_MODAL_SMOKE_20261115/REPORT.md`.
- Scope is complete with acceptance not met. No additional inference or implementation is authorized by this closeout.


### Rev87.30 — publish all pending FEAT-063 worktree changes — 2026-11-15

- **Status:** APPROVED by the project owner's direct instruction: “commit tat ca feature nay len, ko phai moi cai nay”.
- **Plan:** `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV87_30_PUBLISH_ALL_PENDING_FEAT063_20261115.md`.
- **Plan SHA-256:** `03CA385FAB80F903BC6C9CF3EA26FD8F5397DAC02F5FFC194988732ADCC865F8`.
- **Scope:** publish the remaining Parent/Teacher/SVG/Modal/Docker implementation and its FEAT-063 documentation/evidence in coherent commits. The Rev87.29 evidence commit `513d5c96` is already pushed and is excluded from duplicate staging.
- **Limits:** no merge to `dev`; no `.env`, provider/Firebase credentials, seed accounts, child data, pytest temporary trees, or browser-profile caches. Redact workstation-specific paths before publication.
