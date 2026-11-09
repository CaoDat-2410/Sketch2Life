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
