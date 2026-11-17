# Plan revision 31 — Lesson Library API implementation and system API inventory

- Feature: FEAT-063 — whole-repository architecture redesign.
- Plan status at authoring: AWAITING_APPROVAL. This immutable revision becomes actionable only when `approvals/TASK_APPROVAL.md` records the owner's approval for its exact SHA-256.
- Scope authority: owner's 2026-10-28 instruction to proceed, list every API in the system when finished, and adapt existing APIs where needed for FEAT-063.
- Prerequisite baseline: Rev30 local Docker/MinIO storage example and its Boto3 adapter. Rev29 is the Lesson Library contract draft this revision implements and reconciles.

## Goal

Implement the no-AI Lesson Library backend described by the 28-operation Rev29 contract, connect its source-document upload flow to private MinIO through the replaceable S3-compatible adapter, audit the existing route surface for FEAT-063 compatibility, and publish a complete route inventory showing active, profile-specific, fixture-only and new endpoints.

## Scope

1. Implement the 28 Lesson Library operations in `artifacts/LESSON_LIBRARY_API_CONTRACT_DRAFT_REV29_20261028.md`: Teacher CRUD/versioning/upload, Manager Public review, school/named/group grants and revocation, Parent invitations/read/download, Parent groups, and Platform Admin moderation. Keep all lesson and upload behavior deterministic; do not call AI.
2. Keep the domain model distinct: `Lesson` aggregate root, immutable `LessonVersion`, ordered `LessonActivity`, `LessonSourceDocument`, `LessonDocumentRevision`, `LessonAccessGrant`, and BE1-owned `ParentGroup`/`ParentGroupMembership`. A Public review request remains a pending PUBLIC `LessonAccessGrant`; do not add a duplicate PublicationRequest entity/table.
3. Add only the required Alembic branches/tables/columns if the repository inventory confirms they are missing. Use the established PostgreSQL schema ownership pattern, stable constraints/indexes, optimistic revisions, idempotent command receipts, and opaque cross-owner references. Reuse BE1 organizations/assignments, Core asset metadata and the Rev30 S3-compatible object-storage port. Do not inspect or migrate any live user database.
4. Implement resumable source-document upload with application chunks capped at 4 MiB, checksum/idempotency receipts, expiry/abort behavior, private quarantine/final objects, bounded assembly, safe type/size validation, immutable originals and deterministic allowlisted text extraction/coverage metadata. No S3 Multipart Upload API, OCR, AI parsing or full raw-text forwarding is introduced.
5. Implement authorization from verified server identity and database organization assignments. Teachers are author-scoped; Managers are organization-scoped and cannot approve their own authored lesson; Parents resolve only their verified principal and active grants; Platform Admin moderation uses a verified platform-admin authority. Do not trust caller-supplied role, principal, organization ownership or author fields.
6. Audit every existing backend route declaration and the default/classroom/demo composition graph. Update an existing route only when evidence shows a direct FEAT-063 conflict; preserve existing Parent/Teacher behavior and old paths where compatibility is required. Record any changed route and compatibility behavior in the inventory.
7. Produce `artifacts/API_INVENTORY_FEAT063_REV31_20261028.md` with all route method/path pairs categorized as active in the default app, classroom-only, demo-only, fixture/unmounted candidate, Rev30 local storage example, or newly implemented Lesson Library API. Include route owner/module and compatibility notes.
8. Update the Rev29 API contract only where implementation review finds a specific ambiguity or mismatch; record each amendment and its reason. Update FEAT-063 context, decisions, status, evidence and both source registers.

## Acceptance criteria

- AC1: The default API exposes the 28 Lesson Library method/path contracts under `/api/lesson-library/v1`; request/response DTOs retain versioned names, `contract` discriminators, snake_case JSON, safe errors, authorization scope and required headers.
- AC2: Lesson edits create immutable versions; stale `If-Match` fails; retries with the same idempotency key and request fingerprint return the original receipt; conflicting reuse fails safely.
- AC3: Original upload bytes remain private and immutable in S3-compatible storage. Upload session/part metadata is durable; parts are at most 4 MiB, retries are digest-checked, finalization verifies continuity and checksums, and source text extraction is deterministic and reviewable.
- AC4: No extracted text is sent to AI. OCR, AI lesson suggestions, line-sketch generation, video/Story integration, frontend changes and quota/billing work are absent.
- AC5: Only an authorized Manager may approve a Teacher PUBLIC grant, never for their own authored lesson. Public Parent discovery/read requires an active approved grant and a visible lesson; named/group grants are effective only after the applicable Parent acceptance and remain immediately revocable.
- AC6: Parent list/detail/download responses reveal only approved structured content authorized for the verified principal. The original Teacher upload is never exposed by Parent download.
- AC7: Parent groups and lesson grants remain tenant-scoped; cross-organization reads/decisions return safe denials; Platform Admin moderation is separately authorized and audited.
- AC8: The API inventory documents every route in the actual composition plus unmounted/fixture candidates, clearly distinguishing declaration from runtime exposure. All legacy route edits, if any, have explicit compatibility notes.
- AC9: The route inventory reports totals by surface and identifies any unresolved runtime verification gap. It does not claim fixture/unmounted routes are production APIs.
- AC10: No actual `.env`, secret, Firebase credential, AWS credential, live database, provider account, real child data, commit or push is accessed or changed.

## Implementation sequence

1. Record the exact plan hash and the owner's direct authorization in `approvals/TASK_APPROVAL.md`.
2. Complete static route composition and persistence ownership inventory; record the baseline before code changes.
3. Implement the Lesson domain/application/contract boundaries, migrations/repositories and identity/authorization adapters.
4. Implement source upload sessions over the Rev30 object-storage port and deterministic extraction.
5. Implement the HTTP routes and mount them in the default app; resolve legacy compatibility only where the audit requires it.
6. Produce the complete API inventory; reconcile the contract, FEAT-063 records and evidence.

## Risks and controls

- Rev29 and SRS v2.3 are design drafts, not a live database specification. Map each table to current Alembic conventions and preserve existing tables; additive migrations only.
- Current BE1 identity/assignment roles may not yet encode Parent and Platform Admin clearly. Map only verified Firebase claims plus server-owned assignments; fail closed when role authority is absent.
- A parser extraction result is a review draft, not a validated lesson. Preserve the original, record parser/version/coverage/warnings, and require Teacher confirmation before creating a new LessonVersion.
- Route inventory includes several routers that are not mounted by the default app. Label them as fixture/candidate routes and do not silently expose them.
- MinIO Community upstream is archived/source-only. Keep MinIO local-only, use the generic storage port, and do not choose a production provider in this revision.

## Verification limits

- Do not add or run tests, builds, Docker pulls, Compose startup, security validation, live DB inspection/migration, AWS calls, or deployment in this revision unless the owner separately requests verification.
- Perform static source/contract review and record which runtime, database and authorization behaviors remain unverified.
- No commit or push is included.

## References

- `artifacts/LESSON_LIBRARY_API_CONTRACT_DRAFT_REV29_20261028.md`
- `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` §31
- `artifacts/DATA_TABLE_REGISTER.md` §14 and relationship catalogue
- `docs/architecture/PYTHON_BACKEND_ARCHITECTURE.md`
- `docs/architecture/DEPENDENCY_RULES.md`
- `docs/adr/ADR-0020-parent-teacher-modal-local-architecture.md`
- `docs/adr/ADR-0021-single-child-parent-teacher-story-architecture.md`
