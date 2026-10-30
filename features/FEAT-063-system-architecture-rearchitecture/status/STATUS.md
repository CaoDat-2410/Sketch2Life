# Status

## Swagger review and local commit — Plan Rev42 (2026-10-30)

- Lifecycle: REVIEW and verification complete for the approved single local commit scope; push is excluded.
- Approved Plan Rev42 SHA-256: `E8A809729BDE4B83D0A6FD0AC21336C8F3721F55B7BDFA7431F1125922D026E8`.
- Review confirmed the 124-operation/111-path/18-tag local OpenAPI snapshot matches the served API and records 11 unmounted candidates. A middleware review finding was fixed: invalid request IDs are now sanitized before being echoed in typed 413 responses, media-route matching is exact, and oversized version values are capped.
- Focused Swagger/upload suite: 5 passed; Ruff, compile, exporter, live snapshot parity, plan hash checks, `git diff --check` and repository security validation passed.
- Evidence: `evidence/EV-063-34_SWAGGER_REVIEW_AND_COMMIT_20261030.md`.

## Swagger overview presentation — Plan Rev41 (2026-10-30)

- Lifecycle: COMPLETE for the approved overview-copy change.
- Approved Plan Rev41 SHA-256: `8693C3B4165F9413775306260CCC9023404F2AB7F58C967632236951B1FC2BDB`.
- Replaced the dense info paragraph with a concise intro and labeled coverage, authorization/Try it out and unmounted-route notes. No API routes, tags, schemas or behavior changed.
- Snapshot SHA-256: `C1F2B453E5D893AF5328C9091A51B183CB2D67FED2587411C0D45598F47A9466`; it matches the live OpenAPI (124 operations, 111 paths, 18 tags). `/docs` and `/openapi.json` return 200.
- Evidence: `evidence/EV-063-33_SWAGGER_INFO_PRESENTATION_20261030.md`.

## Local Swagger QA kit — Plan Rev40 (2026-10-30)

- Lifecycle: COMPLETE for the approved local synthetic workflow and 413 parity scope.
- Approved Plan Rev40 SHA-256: `701402BC515745FDCBCFF8C8AF8E7630EDF4025D51C330F7E7747AB6D738E1E9`.
- Oversized image/audio requests now return HTTP 413 with `MobileWorkflowResultV1` / `UPLOAD_TOO_LARGE`; OpenAPI 413 schemas match. Focused tests: 4 passed; exporter, Ruff, compile and `git diff --check` passed.
- The documented synthetic session/image flow passed in memory: 201/version 0, then 200/`ADMITTED`/version 1. Snapshot SHA-256: `70BDA49D2E122C4CE0370211DCEF8EA03BEC477CFDE2C60673501EB2CCDF8208`.
- The loopback API was restarted; `/docs` and `/openapi.json` return 200 with 124 operations, 111 paths, 18 tags and two Try it out examples. The synthetic Demo workflow is ready for interactive testing. Protected routes still require Firebase ID tokens and their persistence services; no Auth Emulator, test DB URL, or fake credential path is configured. Evidence: `evidence/EV-063-32_LOCAL_SWAGGER_QA_KIT_20261030.md`.

## Professional Swagger navigation — Plan Rev39 (2026-10-30)

- Lifecycle: COMPLETE for the approved tag/navigation scope.
- Approved Plan Rev39 SHA-256: `1E0244E9D43F3F3B46361D66711D413293F2B7E50DB30DEE5B353BAA2474834F`.
- Swagger has 18 descriptive groups. Explicit Lesson Library roles are shown where source guards establish them; other routes are grouped by BE1/Demo domain and workflow.
- Contract parity remains 124 mounted operations across 111 paths and 11 unmounted candidates. Focused Swagger test: 2 passed; exporter passed.
- Snapshot SHA-256: `27BB19AC8A5938D239A300DB4BFC5028AA205A675AE9B09EE00CCD35CB3D3453`. Local server restarted at `/docs`; existing upload 413 mismatch remains documented under EV-063-30.
- Evidence: `evidence/EV-063-31_SWAGGER_NAVIGATION_ROLE_GROUPING_20261030.md`.

## Contract-aligned Swagger/OpenAPI — Plan Rev38 (2026-10-30)

- Lifecycle: COMPLETE for the approved documentation scope; one existing upload body-limit API/test mismatch is reported in EV-063-30 and remains outside this behavior-preserving change.
- Approved Plan Rev38 SHA-256: `C1E8C74AD57E7F053E0D1E093BAF7F97BE6F12E8EF8887A2C098632B9B863BCF`.
- `/docs` and `/openapi.json` returned HTTP 200. Local profile OpenAPI 3.1.0 contains all 124 mounted operations across 111 paths and records all 11 unmounted candidates. Request, authentication, response and schema parity checks passed.
- Snapshot `artifacts/OPENAPI_FEAT063_REV37_20261030.json`; SHA-256 `A45748B8715F1934BED86F89795F71C3559CD0E2122140EC3D346194E9B2F9F5`.
- Focused Swagger checks: 2 passed; exporter validation and targeted Ruff/compile checks passed. The existing upload body-cap test fails because its expected `failure.code=UPLOAD_TOO_LARGE` payload differs from the middleware's generic `REQUEST_TOO_LARGE` body. No route behavior, database, Docker, provider, commit, or push changes were made.
- Evidence: `evidence/EV-063-30_SWAGGER_OPENAPI_FEAT063_REV37_20261030.md`.

## UI component patterns and interaction states — Plan Rev36 (2026-10-30)

- Lifecycle: REVIEW; nine component/state images and all per-group prompt/motion/index/evidence records are complete.
- Approved Plan Rev36 SHA-256: `300104684514C4C6F67614F58DDE402668AAC24AF2204F9B1BCA7A5BBEA2D336`.
- Output: nine 1,586 × 992 PNG boards, nine `PROMPT.md` files and nine `MOTION.md` files under `assets/generated/ui-components-rev36-20261030/`.
- Includes modal/bottom-sheet, decision dialog, toast/snackbar, error/empty/auth states, upload/extraction, quota/video-job, sharing/revoke, and feedback/notification patterns.
- Current-versus-SRS-target API boundary is documented in the index. Visual approval remains pending; no app code/API/database change or test/build was performed.
- Evidence: EV-063-29; index: `assets/generated/ui-components-rev36-20261030/COMPONENT_INDEX.md`.

## UI screen mockups and motion notes — Plan Rev35 (2026-10-30)

- Lifecycle: REVIEW; generation, per-screen organization, prompt/motion notes and feature-local provenance are complete.
- Approved Plan Rev35 SHA-256: `0EBBE2D7E983663F448B167F39FE42AD6C89A2E38EE5390A054673FC2C42723C`.
- Output: 14 valid PNG screens, each in its role/screen folder with `PROMPT.md` and `MOTION.md`; dimensions are portrait Android (approximately 790–864 × 1,821–1,989) or desktop web (1,586 × 992).
- Detailed motion suggestions cover explicit guide reveal, capture feedback, backend-confirmed job stages, video/activity transitions, filtered-upload stages, classroom Deck opt-in, publication decisions and moderation. Reduced-motion behavior is documented.
- All assets remain generated drafts pending owner visual approval. No code, API, database, migration, test/build, provider call or deployment was performed.
- Evidence: EV-063-28; index: `assets/generated/ui-mockups-rev35-20261030/SCREEN_INDEX.md`.

## Legacy non-AI API regression - Plan Rev34 (2026-10-29)

- Lifecycle: REVIEW; execution and feature-local evidence EV-063-27 are complete, with two test failures recorded.
- Approved Plan Rev34 SHA-256: `308F4FEA6576BAB08ACCD86B62616FE463C94D099FC27EBF301E855C4756F5B1`.
- Safe dispatch smoke: 77 active legacy non-AI routes returned HTTP responses; 52 returned 401, 23 returned 422, 2 health endpoints returned 200, and none returned 5xx. This does not replace success-path coverage.
- Existing API suites: non-PostgreSQL batch 109 passed / 1 failed; BE1 PostgreSQL suite 3 passed / 1 failed. Failures are an outdated route-composition baseline and the BE1 unrepresentable `effective` consent state, detailed in EV-063-27.
- AI-dependent routes were excluded. Newer Lesson Library/storage routes and unmounted candidates are separated in EV-063-27. The disposable test DB was dropped; the persistent DB remains unchanged at the Rev33 target.
- No product-code or existing test-expectation change was made. No AI/provider call, real child data, `.env` edit, commit, or push.

## Current non-AI API workflow verification - Plan Rev33 (2026-10-29)

- Lifecycle: REVIEW; execution is complete and evidence EV-063-26 records the partial verification and remaining limits.
- Approved Plan Rev33 SHA-256: `513FEE246CF1DD2B062BE146996C362C7C726667A9529E0E2342962084CF4DE1`.
- Applied `20261028_ll_0001` to the existing local Compose database `sketch2life`; Alembic also applied prerequisite `20261024_0005`. Main DB revision is verified and its named volume/data were retained.
- Lesson Library HTTP integration suite: 5/5 passed against PostgreSQL with synthetic data. Existing BE1 suite: 3 passed, 1 failed; the run exposed that BE1 authorization requires consent state `effective`, while the database constraint only permits `pending`/`revoked`. The successful consent path cannot be represented; details are in EV-063-26.
- A disposable `sketch2life_be1_acceptance` database was migrated, used for the tests, and dropped afterward. ClamAV was healthy. MinIO image pulls failed (Quay 401; Docker Hub access denied), so storage-example routes used an in-memory object-store test adapter; MinIO adapter/bucket behavior remains unverified.
- Targeted Ruff and compile checks passed. AI APIs, remote databases, real child data, actual `.env` edits and deployment were excluded. No commit or push was performed.

## Current API purpose catalog - Plan Rev32 (2026-10-28)

- Lifecycle: COMPLETE; documentation-only catalog generated and reconciled against the 135-route Rev31 inventory.
- Approved Plan Rev32 SHA-256: `FD189D3E2684CE2930624AFD7412C54F9BB53339209790F7B319B534C41E087C`.
- Artifact: `artifacts/API_PURPOSE_CATALOG_FEAT063_REV32_20261028.md` (SHA-256 `E65582C197FCF9DC134294D140B5289C44B82E6A81AC6DB6C23C0AFE3800A881`).
- No endpoint, code, schema, migration, or runtime behavior changed. Static route inventory only; no tests, Docker, database, provider, or deployment operation was performed.

## Current Lesson Library backend and API inventory - Plan Rev31 (2026-10-28)

- Lifecycle: IMPLEMENTED; static source review complete. Runtime validation and database migration are pending and were outside this approved slice.
- Approved Plan Rev31 SHA-256: `BC948B27F5CFADD05EC6D12B0B7D989241CDEB6FC3CA6CAB1521988C712BBB8C`; Addendum A SHA-256: `570BC65BE74A82261EC2455147EAF33FB0575B166B73EF506084BBF07A62727D`.
- Scope delivered: 30 Lesson Library operations, additive persistence/migration source, owner-scoped resumable uploads, deterministic PDF/DOCX/PPTX extraction and ClamAV scan boundary, Manager moderation, Parent read/share, default-router mounting, and the complete static API inventory.
- Existing Parent, Teacher, BE1 and demo route paths were preserved. Evidence: EV-063-24 at `evidence/REV31_LESSON_LIBRARY_IMPLEMENTATION_AND_API_INVENTORY_20261028.md`.
- Inventory: 135 route declarations total; 121 unconditional routes in the combined app, 3 conditional local storage-example routes, and 11 candidate/fixture/unmounted declarations. FastAPI docs endpoints are noted separately in the inventory.
- No tests/builds, security validation, Docker pulls/start, live database or migration, AWS operation, provider call, deployment, or actual `.env`/secret edit was performed. The Alembic migration is present but unrun. SRS and Data Table Register v2.3 remain unsigned drafts; Rev31's 92/140 count is an implementation crosswalk, not a database observation.

## Historical local Docker and storage example - Plan Rev30 (incorporated in Rev31)

- Lifecycle: IN_PROGRESS. Owner approval for this exact slice is recorded in `approvals/TASK_APPROVAL.md`.
- Approved plan SHA-256: `F6BD755CBC543374AC9091BB7603C2A9EB83DC20F2EDCA92B2A10158AB88C794`.
- Scope: backend Compose service, local MinIO/private bucket initialization, placeholder env templates, Boto3 S3-compatible adapter, and local-only source-document upload/read/delete example.
- No tests, builds, security validation, Docker pulls, Compose service startup, database changes, or AWS operations have been run.
- Rev29 was a contract-only draft at the time. Rev31 and Addendum A later approve and implement the API; see the current status above.

## Historical backend API contract plan - Plan Rev29 (implemented under Rev31)

- Lifecycle: AWAITING_APPROVAL. Plan Rev29 SHA-256: `B63B5BEC21C71BFD154EEA08741C167B3B144AF1133A17695D4C63E6760BCD6A`.
- Rev29 pre-reconciliation API contract SHA-256: `81405D5BB6FC5FBAE50E8E73796FFABBC7C2E5B898C8BA7CEEF99AA3176407A2`; current Rev31-reconciled contract SHA-256: `78D4F99C4EBD51C460CF02863FD2C595AA5AE3D01E7433B7637DB416B765C085`.
- Rev29 clarifies domain entities vs tables vs DTOs and lists routes, actors, purposes, schemas and errors. Scope continues to include Teacher CRUD/upload, deterministic no-AI extraction, Manager Public review, Parent read/share and Admin hide.
- Evidence: EV-063-22, `evidence/API_CONTRACT_NAMING_AND_ENTITY_REVIEW_20261028.md`.
- Rev29 was a contract-only draft at the time. Rev31 and Addendum A later authorize and implement the API; their current status is recorded above.

## Historical backend implementation plan — Plan Rev28 (superseded by Rev29)

- Lifecycle: superseded by Plan Rev29; implementation approval was not recorded. Plan Rev28 SHA-256: `22CBC9E4360B39BDD995B683B5B9681D962D3D1C54355F929F0B1C3BE2387FE6`.
- Scope: Teacher lesson CRUD and upload, deterministic no-AI extraction with Teacher review, Manager approval for Teacher Public content, selected/group sharing, Parent read-only access to Public/active shares, and Platform Admin hide.
- Schema gap: current occurrence-owned document records cannot own reusable library uploads. Rev28 proposes library-scoped source-document/revision records and an additive Data Table Register update before migration.
- Evidence: EV-063-21, `evidence/BACKEND_LESSON_LIBRARY_SCOPE_AND_UPLOAD_REVIEW_20261028.md`.
- No code, migrations, tests/builds, live database or provider operation was performed. `approvals/TASK_APPROVAL.md` remains unchanged.

## Historical initial recommendation — Plan Rev27 (superseded by Rev28)

## Draft backend implementation plan — Plan Rev27 (2026-10-28)

- Lifecycle: superseded initial narrow recommendation; no implementation approval was recorded. Plan Rev27 SHA-256: `984B54DE505A4C86B9334079D6FC9086A0E5ABC9E1736C21BC0734096454E3BD`.
- Proposed slice: Teacher-only private lesson draft CRUD, manually entered structured text and activities, immutable versioned edits, soft archive, verified school/author scope.
- The owner subsequently chose to include Manager publication, Parent read/share and lesson upload; those choices are incorporated into Rev28.
- Evidence: EV-063-20, `evidence/BACKEND_BASIC_LESSON_CRUD_REPOSITORY_REVIEW_20261028.md`.
- `approvals/TASK_APPROVAL.md` is unchanged. No source code, migration, test/build, live database, AI/Modal or deployment work was done.

## Pending amendment — Plan Rev26 (2026-10-28)

- Lifecycle: AWAITING_APPROVAL for a documentation-only AI model/Modal flow reassessment. Plan Rev26 SHA-256: `ECD0A0A6435193A903313409B699574FE9DB30BAAB8498A714A3FC54C75EEABC`.
- Research evidence: EV-063-19, `evidence/MODAL_HOSTED_AI_PIPELINE_REASSESSMENT_20261028.md`.
- Historical Rev26 status: the v2.3 draft carried a stale 91/126 note, later corrected. Current SRS distinguishes v2.3 baseline 89/137 from the Rev31 92/140 implementation crosswalk; neither describes a live database.
- Recommendations are not owner decisions. No model/provider/checkpoint is selected; Q11/Q13, quota-refund behavior and Teacher sample recovery remain open.
- No SRS/register/ADR content change, product implementation, database inspection, Modal operation, provider call, benchmark, GPU spend, test/build, deployment or real-child processing was performed.

## Historical product-design state - Plan Rev25 (extended by later records)

- Lifecycle: DOCUMENTATION_ONLY. Plan Rev25 is approved for updating SRS, Data Table Register and architecture records. Product implementation, schema/migration work, providers, tests/builds and deployment remain unapproved.
- Authority: owner answers Q147–Q195. They extend Q01–Q146 and preserve the earlier Parent/Teacher flows, image-to-video pipeline and historical records.
- SRS: v2.3-draft, Vietnamese, age 36–120 months. The platform adds Platform Admin, School Manager, scoped/revocable access, one-school-per-organization tenancy, reusable lesson versions, filtered authoring, lesson visibility/publication, Parent history/feedback and multi-scope quota.
- Runtime order: Parent child draws; an adult may enable line-sketch during drawing; after drawing capture artwork, generate a new video through the existing child-specific pipeline, then show lesson activities. Teacher flow and one-child sample remain, with line-sketch generated only when enabled in-session.
- Requirements: 107 FR, 60 BR, 38 NFR, 65 Given/When/Then acceptance criteria and 19 edge scenarios. This amendment adds FR-PL-01–25, BR-47–60, NFR-34–38 and AC-46–65.
- Data Table Register: v2.3-draft; 11 logical platform tables added. Target is 38 retained/refactored + 51 new = 89 active, plus 48 legacy/read-only = 137 projected physical. Counts are repository-derived and are not a live database inspection.
- Proposed architecture record: ADR-0022, additive platform lesson library and sharing; no final stack/provider is selected.
- Current sources: SRS §31, Data Table Register §14, ADR-0022, Plan Rev25 and `approvals/TASK_APPROVAL.md`. The SRS and register remain unsigned drafts.
- Open decisions remain explicit in SRS §31.10 and Data Table Register §14.3, including exact age bands, AI lesson suggestion roles, 30/60-day history, share fields/expiry, sample eligibility, script defaults, visual approval, quota precedence and answer 46.
- Evidence: EV-063-18 records document-only scope, preserved v2.2 snapshots and static reconciliation. No product tests/builds, database, provider, Modal, payment, migration, deployment or real-child data was used.
- Diagram/PDF outputs are historical snapshots based on an earlier SRS. They were not refreshed by this Markdown amendment and are not evidence for the v2.3 content.

## Historical snapshot through Plan Rev24 (superseded by the current state above)

- Lifecycle: DOCUMENTATION_ONLY. Plan revision 22's Draw.io/PDF request is complete. Revision 23 corrected the SRS source; revision 24 is approved for the Parent AI line-sketch documentation amendment. The SRS and Data Table Register remain drafts; product implementation remains unapproved.
- Plan: revision 22; the approved scope is documentation-only under `approvals/TASK_APPROVAL.md`. The approval hash matches this plan revision.
- Follow-up amendment: plan revision 23 corrected the SRS source and retired FEAT-062's stale question list. Plan revision 24 is approved for documentation-only scope: Q146 records the Parent AI line-sketch as an optional feature; Q145's text-only interpretation is superseded.
- Owner decisions: Q01–Q146 are represented in the SRS, data-table register, ADR and feature decision/context records. Parent/Teacher flows remain separate; Parent can request or skip a generic 3–5-step AI line-sketch guide and confirms the child's artwork subject only after capture; Teacher AI Sketch remains an occurrence-wide main-flow deck; every story/video run has exactly one child.
- SRS: revision 2.2-draft, Vietnamese, with 46 BR, 82 FR and 33 NFR IDs; 45 Given/When/Then acceptance criteria and 19 edge scenarios. It includes the full VLM → structured story/storyboard → script review → Character Bible/reference → per-scene LTX-2.5 on Modal L40S → consistency → FFmpeg/TTS/subtitles → automated safety → private playback pipeline. Final video approval and public gallery/download are excluded. SRS content remains unsigned.
- Data-table register: revision 2.2-draft. Parent Sketch Guide uses existing AI Job/Core Asset/AI Policy owners, with target kind `PARENT_SKETCH_GUIDE`, private temporary asset provenance/expiry/cleanup and independent resource accounting; no new table is currently proposed. All 86 repository-declared production mappings are dispositioned and five fixtures are excluded. The target is 38 retained/refactored + 40 new = 78 active, plus 48 read-only legacy = 126 projected physical. Each of the 40 new tables has a matching relationship entry. This is a logical target, not a live database count.
- AI job architecture baseline: one discriminated target per StoryRun, Teacher Sketch Deck, or Parent Sketch Guide. Story/video jobs resolve one child from StoryRun; neither sketch target contains child/profile refs.
- Architecture record: proposed ADR-0021 reconciles target counts, Teacher Sketch Deck, optional Parent AI guide, video pipeline, current-owner transfer, upload lifecycle and async job boundaries. D-73–D-79 record Q137–Q144; D-91 is the historical text-only interpretation and D-92 records the owner clarification for Q146. D-80 records the target-discriminated AI Job contract; D-83 records the current full data-model audit and supersedes D-82's count. D-84–D-85 record relationship integrity and the composed read contract.
- Evidence: EV-063-13 records all-source/target table disposition, relation and canonical-field checks, the 78 active/48 legacy/126 projected physical arithmetic, and static cross-document consistency review. No product tests/builds, database, provider, Modal, payment, migration or benchmark was run.
- Parent guide amendment: EV-063-17 records the Q146 SRS/Data Table Register/ADR/source reconciliation, Plan Rev24 scope and static checks; exact model/license/cost/rate/retention gates remain open.
- Markdown language: Vietnamese with technical identifiers retained. Both files remain drafts and have not received content sign-off.
- Diagrams/PDF: the existing monochrome 69-page Draw.io master and matching full-package PDF, plus 24-page flow-only PDF, are revision 2.0 outputs and predate the Parent AI guide. They are historical snapshots; refresh only if the owner requests a new diagram/PDF package. EV-063-15 records their original hashes and QA. All 78 active target tables appear once; 48 legacy mappings remain separate.
- Product code/schema changes, database access, tests/builds, provider/payment/Modal calls, deployment and real-child data: not performed or approved.
- Working tree: documentation changes are limited to FEAT-063, the FEAT-062 retirement redirect/records, ADR-0021 and the global source-register pointer; unrelated existing changes were not modified.
