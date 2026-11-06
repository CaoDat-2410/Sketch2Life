# Task approval

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
