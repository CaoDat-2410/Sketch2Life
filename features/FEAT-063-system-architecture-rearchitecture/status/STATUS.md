# Status

## BA handoff — 2026-10-30

- Use `plan/PLAN_REV36_BACKEND_SRS23_ALIGNMENT_20261029.md` as the latest backend foundation draft and `plan/REV36_S1_EXECUTION_SCOPE_DRAFT_20261029.md` for the S1 candidate inventory. Rev35 passed independent plan review; Rev36 addresses its three P3 notes but has not yet received an independent final review.
- S1–S3 are proposed foundations only. StoryRun, actual provider integration, voice, video and other end-to-end work need later plans. The SRS/register remain drafts, S1 dispositions and applicable OD decisions remain open, and implementation is AWAITING_APPROVAL. Sharing this material with BA is not approval to implement.

## Rev36 response to Rev35 review — 2026-10-29

- `plan/PLAN_REV36_BACKEND_SRS23_ALIGNMENT_20261029.md` is the current draft for review, superseding Rev35; implementation approval remains pending.
- Clarifies existing/new guards, adds OD-8–OD-14, and records P4 composition ownership alongside FEAT-064 coordination. See `evidence/notes/REV36_REVIEW_RESPONSE_20261029.md`.
- Documentation only; no product code, approvals, DB/provider execution or publication.

## Historical: Rev35 response to independent review — 2026-10-29

- `plan/PLAN_REV35_BACKEND_SRS23_ALIGNMENT_20261029.md` supersedes Rev34 for future review and remains AWAITING_APPROVAL. `plan/REV35_S1_EXECUTION_SCOPE_DRAFT_20261029.md` retains the candidate inventory; exact dispositions remain open.
- Addresses the reviewed migration graph, legacy/typed job compatibility, identity onboarding safety, CI and disposable-DB acceptance gates, and FEAT-064 coordination. See `evidence/notes/REV35_REVIEW_RESPONSE_20261029.md`.
- Documentation only: no product implementation, approval edit, DB/provider execution or publication.

## Historical: SRS 2.3 plan alignment — 2026-10-29

- `plan/PLAN_REV34_BACKEND_SRS23_ALIGNMENT_20261029.md` supersedes Rev33 for future planning; AWAITING_APPROVAL, no implementation approved. S1 inventory remains a subordinate draft with individual operation dispositions pending.
- Records the Parent-after-video and Teacher-before-video distinction, unresolved SRS/register contradictions, eight AI target kinds, consent fail-closed requirements, Teacher age migration gap and SRS cutover gates. Qwen3 smoke is not a quality acceptance.
- See `evidence/notes/REV34_SRS23_PLAN_ALIGNMENT_20261029.md`. No SRS content, historical approvals, runtime source, DB or provider changed.

## Historical: backend-foundation preparation — 2026-10-29

- Branch: `feature/feat063-be-foundation`, baseline `4f071242`; contains Modal and CI repair through the merged history.
- Rev33 remains AWAITING_APPROVAL; S1/S2/S3 source implementation not started. All earlier approvals retain their scope.
- First-slice preparation: `plan/REV33_S1_EXECUTION_SCOPE_DRAFT_20261029.md`, DRAFT. Static command inventory and exceptions prepared; owner disposition/error choice and exact subset approval remain pending.
- Checkpoint: `evidence/notes/BE_FOUNDATION_MERGED_BRANCH_CHECKPOINT_20261029.md`.
- No runtime source, schema/migration, approval, service/DB/Modal execution or Git publication in this preparation step.

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
