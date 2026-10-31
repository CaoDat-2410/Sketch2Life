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
