# Plan revision 27 — backend manual lesson-draft CRUD vertical slice

- Feature: FEAT-063 — whole-repository architecture redesign.
- Status: DRAFT. The recommended scope is concrete, but two owner choices below are still open. No implementation approval is recorded.
- Requested outcome: start backend implementation with a small, manually authored CRUD flow so the basic platform path can be exercised before AI work.
- Authority: the current product baseline is the FEAT-063 SRS and Data Table Register v2.3-draft. Plan Rev25 approved a documentation amendment only. Plan Rev26 is an independent AI/Modal research amendment awaiting approval; neither plan authorizes backend implementation.

## Repository baseline reviewed

- The backend is a Python modular monolith with FastAPI interfaces, domain/application/contracts/infrastructure layers, PostgreSQL and Alembic patterns. FEAT-047 already provides Firebase-verified adult identity, organization membership and Teacher/school-administrator assignments.
- `learning_content` has a domain, application commands, SQL adapter, contracts, migration and extensive candidate tests. Its HTTP router is explicitly a candidate, has no read/list routes and is not mounted by the default router composition. Its generic knowledge/activity/video payload is not the structured Montessori Lesson contract.
- The SRS describes a separate reusable Lesson aggregate. The v2.3 Data Table Register proposes `lesson.library_items`, `lesson.library_versions` and `lesson.version_activities` for the manual text-and-activity core; these are design targets, not verified live database tables.
- No live database was inspected. No implementation, migration, test, build, provider call or AI inference was performed for this plan.

## Recommended first slice

Implement a versioned, text-only Teacher lesson draft API. A Teacher creates and manages their own private draft under the verified school organization. The API supports create, list, detail, update and archive. A lesson version contains the fields needed for a basic Montessori lesson: title, topic, target age range within 36–120 months, drawing guidance, subject-learning notes and an ordered list of activities with materials, preparation, instructions, observation notes and safety notes.

Use the existing verified identity and organization-assignment boundary. Derive principal, role and organization from server-side verification; never accept them as authority from request payloads. Use the proposed Lesson tables and existing backend migration conventions after confirming their exact mapping. Preserve immutable lesson versions: an edit creates a new version and advances the current-version pointer with a revision precondition. Archive is soft and preserves versions and provenance.

This plan recommends a dedicated `lesson` domain slice, while reusing established authentication, HTTP, database and audit patterns. Do not mount or repurpose the generic `learning_content` candidate as a shortcut. If a repository review identifies a safe shared component, reuse it only through an explicit mapping that does not weaken either domain's invariants.

## Scope

- Teacher-authored structured text only; no file upload or document parser in this first slice.
- Create, list, read, update and archive private lesson drafts, including their ordered activity list.
- School tenant isolation and author ownership checks on every read and write.
- Server-generated identifiers/timestamps, actor provenance, safe error responses, and optimistic concurrency for edits.
- Additive Lesson persistence for the minimum library item/version/activity records; no live-database migration or schema inspection.
- Versioned API contract and OpenAPI description, following current backend conventions.
- Unit, HTTP contract and disposable-PostgreSQL integration verification as implementation acceptance work after the plan is approved.

## Explicitly out of scope

- AI lesson suggestions, AI-generated activities, line sketches, images, slides, VLM/LLM, Modal, AI jobs, model configuration or provider calls.
- Upload, extraction, filtering, OCR, or handing any lesson material to a model.
- Manager review, Public/Selected visibility, publication, hide/unpublish, Parent browsing/downloading, sharing grants or feedback.
- Lesson occurrences, class delivery, child profiles, Parent/Teacher profile sharing, video generation, quota/billing, notifications or frontend work.
- Changes to the Parent or Teacher runtime flows, existing video pipeline, current SRS baseline, unrelated schemas or legacy records.
- Hard deletion of lesson drafts or versions.

## Implementation sequence after approval

1. **Scope and contract lock:** incorporate owner answers; map the structured fields and version lifecycle to SRS §31 and Data Table Register §14. Confirm the existing Teacher role and organization assignment contract. If implementation needs a material architecture/schema deviation, record and review an ADR before coding.
2. **Domain and contracts:** define Lesson, immutable LessonVersion and ordered Activity values; validate Vietnamese text fields, age range, activity ordering, draft/archive transitions and version preconditions without framework or database imports.
3. **Persistence:** add only the Lesson tables needed for this slice through an additive Alembic migration. Enforce organization-scoped identifiers/queries, unique version numbers, activity ordering, current-version integrity and safe archive behavior. Keep activity data attached to the exact version.
4. **Application use cases:** implement create/list/get/update/archive through ports and transactions. All reads filter by verified organization and author; edits use compare-and-swap so a stale version cannot overwrite a newer one. Record actor/time and metadata-only audit events.
5. **HTTP boundary:** add thin versioned endpoints with strict request/response contracts, authentication through the established verified identity path, role/scope checks, correlation IDs, pagination for lists and safe 401/403/404/409/422 responses. Do not expose database or model-provider details.
6. **Verification:** add focused unit and HTTP contract cases, then run the Lesson migration/CRUD/isolation suite only against a dedicated disposable PostgreSQL test database. Exercise the API with synthetic test identities; do not use real child data or production credentials.

## Proposed API behavior

The exact route prefix is to be confirmed against the current API composition before implementation. The resource operations are:

| Operation | Behavior |
|---|---|
| Create | Create a private `DRAFT` lesson and version 1 with its ordered activities. |
| List | Return only the authenticated Teacher's active drafts in the authenticated organization; support bounded page size and cursor/continuation token. |
| Read | Return the lesson head and its exact current version/activities only when the caller owns it in the same organization. |
| Update | Require the current revision (`If-Match` or the existing project equivalent); create a new immutable version and atomically advance the head. |
| Archive | Soft-archive the lesson, omit it from the default active list, and preserve all versions and audit history. |

## Acceptance criteria

- **AC-BE-01 Create:** an authenticated Teacher with an active school assignment can create a valid text-only draft; the response includes the opaque lesson ID, organization scope, author, state, revision/version and activities.
- **AC-BE-02 Read/list:** list and detail return only the caller's own lessons for the verified organization; another Teacher cannot read a private draft by guessing its ID.
- **AC-BE-03 Update/version:** a valid update with the current revision creates the next immutable version and updates the head in one transaction; previous version content remains unchanged.
- **AC-BE-04 Concurrency:** an update with a stale revision is rejected with a stable conflict response and does not alter the lesson, activities, version pointer or audit record.
- **AC-BE-05 Activities:** activities are stored and returned in declared order under the lesson version, with materials, preparation, instructions, observation notes and safety notes.
- **AC-BE-06 Archive:** archive is reversible only through a separately approved future lifecycle; it does not hard-delete the lesson, versions or provenance and removes the item from the default active list.
- **AC-BE-07 Authorization:** missing/invalid authentication is rejected; non-Teacher or inactive assignment is denied; organization and role claims supplied by the client cannot grant access.
- **AC-BE-08 Tenant isolation:** a principal from School B cannot list, read, update or archive School A's lesson, even when the resource ID is known; no cross-tenant payload or existence detail is returned.
- **AC-BE-09 Input validation:** blank required text, invalid age bounds, malformed activity order, unknown fields and oversized payloads are rejected with safe contract errors and no input echo.
- **AC-BE-10 Persistence:** migration upgrade/downgrade affects only the Lesson schema owned by this feature; restart against the disposable test database preserves lesson/version/activity data.
- **AC-BE-11 No AI path:** this slice creates no AI job, provider request, generated asset, quota usage or child-profile reference. The implementation contains no AI suggestion endpoint or hidden AI fallback.
- **AC-BE-12 Contract and architecture:** OpenAPI matches the implemented requests/responses/errors; routes remain thin, domain rules remain framework-independent, and database access stays behind application ports.

## Risks and mitigations

- **Generic content overlap:** the existing `learning_content` candidate may look reusable but represents a different contract. Map fields and ownership first; do not force Lesson data into it.
- **Identity mapping:** FEAT-047 uses existing school roles and assignments while the new SRS names School Manager. This slice requires only the existing Teacher assignment; Manager mapping remains for a later approval/publication slice.
- **Versioning adds structure to CRUD:** immutable versions are required by the platform design. Keep the API edit operation simple while implementing it as an atomic new version.
- **Draft privacy vs organization ownership:** store the organization owner for tenant continuity, but limit this slice's read/write capability to the author. Manager and successor access require an explicit later policy.
- **Unapproved baseline:** SRS/Data Table Register remain drafts. This plan approval, if later granted, should authorize only this bounded CRUD slice and its required migration; it must not be treated as sign-off of the full SRS or AI pipeline.

## Owner choices to close

1. **First-slice access:** confirm Teacher-only private draft CRUD as proposed, or include School Manager review/Public publication and Parent read/share now. Recommended: Teacher-only CRUD first.
2. **Teacher input:** confirm manually entered structured fields only, with upload/template parsing deferred. Recommended: defer uploads and parsing; keep this slice text-only and AI-free.

## Approval boundary

This file is a draft plan, not task approval. No implementation, schema migration, tests/builds, live database access, AI/provider/Modal operation or deployment may start until the owner resolves the two choices, approves the final plan revision/hash in `approvals/TASK_APPROVAL.md`, and the feature status advances under the repository workflow.
