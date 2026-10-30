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

## Plan revision 38 — UI mockup remediation and workflow coverage

- Status: APPROVED for generated visual drafts and the single AC-33 consistency correction described below. Visual approval, product implementation and promotion of assets remain separate gates.
- Approver: Project owner, direct reply on 2026-10-30 (“Ok, ấy lại dfi”) to the recommendation to revise the UI mockups against the current FEAT-063 source, reconcile the Parent line-sketch contradiction, and add missing workflow screens.
- Recorded timestamp: 2026-10-30 15:21:02 Asia/Saigon.
- Feature: FEAT-063 - whole-repository architecture redesign.
- Approved plan: `plan/PLAN_REV38_UI_MOCKUP_REMEDIATION_20261030.md`.
- Approved plan SHA-256: `ADB45B054C5E4872629AFDAF52037053AB97470EEEAC6F225D007ED0B62ADB27`.
- Approved scope: correct the contradictory Parent-guide wording in draft SRS AC-33; preserve Rev35/Rev36 originals; produce 23 screen drafts and nine component boards with prompt/motion notes and API-boundary labels under new `assets/generated/` directories; use consistent proposed visual styling and synthetic examples; inspect and record provenance, hashes and limitations; update FEAT-063 context, decisions, source register, evidence and status.
- Acceptance criteria: AC1–AC8 in the hash-identified Plan Rev38.
- Explicitly excluded: app/source implementation, product API/schema/database changes, executable animation, age-policy decision or SRS sign-off, provider calls, tests/builds, deployment, real child data, Git commit/push, and promotion to `assets/approved/` or `assets/applied/` before separate owner visual approval.
- Approval basis: the owner's direct instruction applies to the exact scope and acceptance criteria in Plan Rev38; it does not constitute visual approval of generated assets.

## Plan revision 40 — publish Rev38 on a branch based on current origin/dev

- Status: APPROVED for a new-branch publish of the Rev38 package; do not rewrite `origin/dev`.
- Approver: Project owner, direct instruction on 2026-10-30: “commit and push lên”.
- Recorded date: 2026-10-30.
- Feature: FEAT-063 — whole-repository architecture redesign.
- Approved plan: `plan/PLAN_REV40_PUBLISH_REV38_BRANCH_20261030.md`.
- Approved plan SHA-256: `B8B6B143F2032AD53C2B8A9A3A8E5D2632FE06FD55B0FEF5248CFB7191B78174`.
- Approved scope: publish Rev38 visuals and associated FEAT-063 records on `codex/feat063-rev38-ui-mockups-20261030`, rooted at fetched `origin/dev`; run repository security validation before commit and push.
- Acceptance criteria: AC1–AC5 in the hash-identified Plan Rev40.
- Explicit exclusions: force-push or change to `origin/dev`, Rev37 pending outputs, unrelated staged/worktree changes, other features, secrets, `.env`, and visual asset promotion.
- Approval basis: the owner's direct commit/push instruction authorizes publishing this package on a new branch because the local and remote `dev` histories diverged. It is not visual approval of the generated UI assets.

## Plan revision 41 — publish Rev38 with its API source on a branch

- Status: APPROVED for the exact path-scoped commit and new-branch push below.
- Approver: Project owner, direct instruction on 2026-10-30: “commit and push lên”.
- Recorded date: 2026-10-30.
- Feature: FEAT-063 — whole-repository architecture redesign.
- Approved plan: `plan/PLAN_REV41_PUBLISH_REV38_WITH_API_SOURCE_20261030.md`.
- Approved plan SHA-256: `BDA32999FED7D34B3F94939F9836F9073A4BD624A7CEC3A20071D9C65D0636BD`.
- Approved scope: publish Rev38 visuals and associated FEAT-063 records on `codex/feat063-rev38-ui-mockups-20261030`, rooted at fetched `origin/dev`; include the cited Rev37 API contract catalog as a read-only source dependency; run repository security validation before commit and push.
- Acceptance criteria: AC1–AC5 in the hash-identified Plan Rev41.
- Explicit exclusions: force-push or change to `origin/dev`, Rev37 execution reports/scripts/logs, unrelated staged/worktree changes, other features, secrets, `.env`, product-code changes and visual asset promotion.
- Supersession: Rev41 supersedes Plan Rev40 only to include the Rev37 API contract catalog required by Rev38 provenance. It is not visual approval of generated UI assets.
- Approval basis: the owner's direct commit/push instruction authorizes publishing this reviewable package on a new branch because local and remote `dev` histories diverged.
