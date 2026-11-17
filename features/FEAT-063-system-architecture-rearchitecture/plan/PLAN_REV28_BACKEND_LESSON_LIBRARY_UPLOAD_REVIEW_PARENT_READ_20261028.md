# Plan revision 28 — backend Lesson library, upload, publication and Parent read

- Feature: FEAT-063 — whole-repository architecture redesign.
- Status: AWAITING_APPROVAL. The owner has selected the broader first-scope features below; implementation approval is not yet recorded.
- Owner scope choices (2026-10-28): include Teacher lesson upload; include School Manager review/Public publication and Parent read/share in the first backend plan.
- Supersedes as the current proposal: Plan Rev27 `PLAN_REV27_BACKEND_BASIC_LESSON_CRUD_DRAFT_20261028.md` (SHA-256 `984B54DE505A4C86B9334079D6FC9086A0E5ABC9E1736C21BC0734096454E3BD`). Rev27 remains preserved as the initial narrow recommendation.
- Product authority: FEAT-063 SRS and Data Table Register v2.3-draft. The scope uses requirements already described there; this plan does not sign off the complete SRS or select an AI model/provider.

## Repository baseline and material gaps

- BE1 currently provides Firebase-verified adult identity, school/organization assignment and Teacher/school-administrator operations. It does not provide a Parent lesson-library read API or Manager lesson-review API.
- The reusable Lesson tables in Data Table Register §14 are proposals, not verified live database tables. Existing `lesson.source_documents` and `lesson.document_revisions` are owned by a teaching occurrence; they must not be attached to reusable library lessons through an untyped or cross-owner reference.
- The existing `learning_content` module is a different generic catalog candidate. Its command router is not mounted in the default app and lacks lesson-library reads. Reuse its generic payload as a Lesson would lose the structured lesson/document ownership model.
- BE1 artifact upload is session/consent scoped. This repository review found no general reusable-library upload route or Parent library role boundary. Use backend-owned ports and verified identity; do not send mobile clients storage credentials or direct object-store endpoints.
- No live database, migration, runtime, test, upload, provider or AI operation was performed while preparing this plan.

## Goal and implementation slices

Deliver one backend-only vertical path from Teacher authoring to authorized Parent read, with the work split into small increments:

1. **Author and upload:** Teacher creates/edits a private school-owned lesson draft manually or from an uploaded text-based template; Teacher reviews/corrects extracted fields before saving the structured version.
2. **Review and publication:** Teacher requests Public visibility; the School Manager for that organization approves or requests changes. A Teacher version is never Public before approval.
3. **Share and Parent read:** after the required approval, authorized Teacher/Manager shares to a named Parent or Parent group, or the item is Public. Parent can list and read Public or currently shared lesson content. Revocation blocks future reads.

The API is backend-only. Parent/Teacher mobile and Teacher web UI changes, lesson-to-occurrence/Story wiring, child-profile sharing/history and the existing child-specific video pipeline are later integration work.

## Scope

### Teacher authoring and lesson lifecycle

- CRUD for a reusable lesson draft scoped to one school organization: create, list, detail, update and soft archive.
- Structured Vietnamese text fields: title, topic, target age range within 36–120 months, objectives/learning notes, drawing subject/steps and an ordered list of activities with materials, preparation, instructions, observation notes and safety notes.
- Teacher may start with the manual form or attach a source document. Store immutable versions; edits create a new version. The currently published version stays readable while a newer draft is being reviewed.
- Default new Teacher lesson to `PRIVATE`. Support `PRIVATE`, `SCHOOL`, `SELECTED_AUDIENCE` and `PUBLIC` visibility, enforcing the publication gate for Teacher Public content.

### Upload and deterministic extraction (no AI)

- Accept PDF, PPTX and DOCX text-based lesson templates, preserving the original as a private immutable Core Asset with provenance.
- Use the existing documented limits: maximum 25 MB and 100 pages/slides; reject encrypted/password-protected, malformed, unsupported and over-limit inputs. Do not OCR scanned pages.
- Validate extension, media signature, archive safety, size and page/slide count; run the configured file safety scan before attaching the asset. Return bounded, safe error codes.
- Use backend-owned upload sessions/chunks and a storage port. Local/test storage may support development. Production object storage remains unselected and requires its own reviewed ADR/configuration before deployment. Mobile clients receive opaque refs/progress only, never storage credentials or endpoints.
- Extract text deterministically with parser/version and coverage/warning provenance. Map only the approved structured fields into a draft. Teacher must preview, edit and confirm the extracted content. Uncertain/unsupported extraction remains a manual-edit path.
- Do not send the file, extracted full text, structured lesson or any child data to an AI/model. No AI suggestions, AI parser, OCR model or hidden fallback.

### Manager review, sharing and Parent read

- A Teacher requests Public publication for a specific immutable lesson version. A Manager with active authority in the same school may approve or request changes; the author cannot approve their own Teacher publication.
- Approval pins the exact version/hash and policy revision. Editing creates a new draft version; it does not silently change the currently approved version. A new version needs a new approval before replacing the Public version.
- Support school-only access and, after approval, selected-audience access to a named Parent or active Parent group. Grants have explicit capability, target/version scope, state, expiry where configured, audit and revoke behavior. Manager group membership and invite acceptance must be verified server-side.
- Public lesson list/detail and active-grant list/detail are read-only for Parent. Parent receives only structured lesson content and permitted lesson assets; original Teacher upload and raw extracted text remain private to the authoring school.
- Unpublish/revoke removes future library read access while preserving source/version/history metadata. Parent lesson use in a StoryRun, past-delivery history and feedback are excluded from this backend slice.
- Add the narrow Platform Admin hide/unpublish action needed to remove a Public lesson; it must be server-authorized, audited and must not expose child media.

## Data and architecture plan

- Use a dedicated `lesson` domain/application/contracts/ports/infrastructure slice; reuse established Firebase verification, BE1 assignment lookup, request/error conventions and database transaction patterns.
- Implement the proposed `lesson.library_items`, `lesson.library_versions`, `lesson.version_activities` and `lesson.access_grants`, plus `be1.parent_groups` / `be1.parent_group_members` where required by the access matrix.
- Add library-owned source records rather than linking to occurrence-owned uploads: proposed `lesson.library_source_documents` and `lesson.library_document_revisions`. A lesson version references the exact reviewed document revision. Core remains owner of bytes/hash/media validation; Lesson owns document lifecycle, extraction provenance and review state.
- Add/use Core upload-session and upload-part contracts through a storage port; do not couple Lesson directly to an object-storage implementation. Any new table/relationship is additive and tenant-scoped.
- The proposed two library-document tables would change the repository target from 89 to 91 active tables (48 legacy/read-only, 139 projected physical) if accepted. This is a design count only; update the Data Table Register and derived counts before migration. No live database count is asserted.
- Before implementation, reconcile the Parent verified-principal/role mapping and map existing BE1 `school_admin` authority to the SRS School Manager permission set. Record any new role/contract or storage choice in an ADR; do not trust caller-provided roles.

## Implementation sequence after approval

1. **Lock contracts and records:** update the SRS/Data Table Register with library-owned source-document ownership and revised table counts; document role mappings, visibility/access matrix, version transitions and upload contract. Preserve the occurrence document flow and both Parent/Teacher runtime flows. Record any architecture choice in the appropriate ADR.
2. **Lesson draft CRUD:** implement domain rules/contracts, additive migration, tenant-scoped persistence, create/list/get/versioned update/archive, audit and stale-revision handling.
3. **Upload and extraction:** implement backend-owned upload session lifecycle and a non-AI deterministic extraction worker/service. Preserve originals and parser provenance; make review/correction create immutable revisions. Expose progress/status and attach only a Teacher-confirmed structured revision to a lesson version.
4. **Manager review/publication:** add organization-scoped pending review queue, approve/request-changes commands and exact-version publication. Keep the previous approved version active while a new draft is reviewed.
5. **Sharing and Parent read:** add Parent groups/named invitations and revocable grants; add read-only public/shared queries that re-evaluate access on every request. Never return raw source document or extracted full text to Parent.
6. **Admin moderation and verification:** add audited Platform Admin hide/unpublish command. Complete unit, HTTP contract and disposable-PostgreSQL integration verification for upload safety, role/tenant boundaries, publication, grant/revoke and migration recovery. Use synthetic documents/accounts only.

## API operations to contract

Exact prefixes and DTO names are set in the implementation contract. The backend must cover these operations:

| Actor | Operation |
|---|---|
| Teacher | Create/list/read/update/archive own school lesson drafts; create/review/confirm an uploaded document extraction; request Public publication; create eligible named/group share grants after approval; revoke grants they own where policy permits. |
| School Manager | List pending review items for their organization; approve or request changes for a Teacher's exact version; manage school Parent groups/membership; inspect school lesson metadata and revoke school-scoped grants. |
| Parent | List/read Public lessons and lessons with an active named/group grant; accept/revoke invitation membership; download permitted structured lesson content, never original Teacher files. |
| Platform Admin | Hide/unpublish a Public lesson through an audited moderation command; read only the metadata needed for moderation. |

## Acceptance criteria

- **AC-BE-01 CRUD:** Teacher can create/list/read/update/archive a school-scoped lesson draft; update creates an immutable version and stale revisions conflict without partial writes.
- **AC-BE-02 Upload admission:** only PDF/PPTX/DOCX within the existing byte/page limits are accepted; encrypted/password files, malformed archives, unsupported media, invalid signatures and scanned pages needing OCR fail safely.
- **AC-BE-03 Source integrity:** original bytes remain private, immutable, integrity-checked and provenance-linked. Parent responses never reveal source files, extracted full text, internal storage references or credentials.
- **AC-BE-04 Extraction:** parser output carries parser/version, coverage and warnings; only allowlisted lesson fields are exposed for Teacher review. Teacher correction creates a new revision; unconfirmed extraction cannot be attached to a usable lesson version.
- **AC-BE-05 No AI:** file admission, extraction, lesson CRUD and review create no AI job, model/provider call, generated asset, AI quota usage or child-profile reference.
- **AC-BE-06 Tenant and role enforcement:** Teacher writes only own organization lessons; Manager review/group actions are limited to their organization; Parent access requires Public visibility or an effective grant; Platform Admin moderation requires the platform permission. Client-supplied actor/org/role fields cannot grant access.
- **AC-BE-07 Publication gate:** Teacher Public request is not visible to Parents before Manager approval. Approval records reviewer, exact version/hash, time and policy. Self-approval is rejected; request-changes returns the item to Teacher draft without publication.
- **AC-BE-08 Version safety:** editing an approved Public version creates a new non-public draft. Existing Public content stays pinned until the new version is approved; previous versions and provenance remain immutable.
- **AC-BE-09 Audience matrix:** PRIVATE is author-only; SCHOOL is limited to authorized members of the same school; SELECTED requires a valid named/group grant; PUBLIC is searchable/readable across organizations. Every read rechecks current publication, membership and grant state.
- **AC-BE-10 Revocation:** revoking a grant, removing a Parent from a group, unpublishing or hiding a lesson blocks the next read/download; historical versions remain stored and do not silently restore access.
- **AC-BE-11 Parent projection:** Parent can list/read the authorized structured lesson/activity content and permitted published assets, but cannot edit source lessons or view raw uploads, teacher-only notes outside the approved projection, another school's SCHOOL lesson or revoked content.
- **AC-BE-12 Persistence and contracts:** additive migrations, unique tenant/version/order constraints, API/OpenAPI schemas, safe error envelopes and audit events match the approved contract; migration tests run only on a dedicated disposable PostgreSQL database.
- **AC-BE-13 Preserved flows:** no change to existing Parent drawing→capture→child-specific video→activity order, Teacher occurrence/sample flow, sketch opt-in behavior or image/video AI pipeline.

## Risks, dependencies and boundaries

- **Broader than CRUD:** upload sessions, Parent grants and Manager publication are multiple vertical slices. Implement in the order above; each phase must meet its acceptance criteria before the next is integrated.
- **Source-document ownership mismatch:** occurrence uploads cannot serve as reusable library sources. Add library-owned source/document revision records; do not create cross-owner database coupling.
- **Parent identity boundary:** Parent library reads need a verified principal and active Parent/group/invite scope. Define that server-side using Firebase verification and the approved account contract; no synthetic identity fallback in runtime.
- **Storage provider not chosen:** local/test adapter supports development only. Production deployment is blocked until an object-storage adapter and secrets path are approved in an ADR; Firebase Storage remains forbidden.
- **Parser risk:** PDF/Office parsing is deterministic and may have incomplete text coverage. Report uncertainty and require Teacher correction; no OCR or model fallback.
- **Architecture authority:** SRS/Data Table Register remain drafts until their required additive amendment is reviewed. Approval of this plan must explicitly cover the stated SRS/Register changes and this bounded backend scope only.

## Verification plan

- Domain/unit cases for version transitions, permissions, visibility, publication and grant revocation.
- HTTP contract cases with synthetic Firebase principals for Teacher, Manager, Parent and Platform Admin; test missing role, revoked assignment/grant and cross-school identifiers.
- Synthetic PDF/DOCX/PPTX fixtures for size/signature/encryption/page-limit, parser coverage, teacher correction, upload resume/integrity and no-source-leak checks.
- Dedicated disposable PostgreSQL migration/integration cases for tenant isolation, immutable versions, review/share transactions, audit/outbox and restart persistence.
- OpenAPI/manual API walkthrough for Teacher upload→review→draft→Manager approve→Parent read/revoke. Do not use real child data, production credentials or AI providers.

## Approval boundary

This is the exact implementation proposal awaiting review. It does not authorize code, migrations, tests/builds, database access, AI/provider/Modal calls or deployment. Under the repository AGENTS.md workflow, implementation starts only after the owner approves this exact Plan Rev28 revision/hash in `approvals/TASK_APPROVAL.md` and the feature status is advanced. Plan Rev27 and Plan Rev26 remain preserved history; Rev26's AI research approval is independent.
