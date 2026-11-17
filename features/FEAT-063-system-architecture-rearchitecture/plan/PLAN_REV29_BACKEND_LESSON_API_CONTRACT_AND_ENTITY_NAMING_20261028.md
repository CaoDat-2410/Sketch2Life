# Plan revision 29 — backend API contract and entity naming

- Feature: FEAT-063 — whole-repository architecture redesign.
- Status: AWAITING_APPROVAL. This successor makes the owner-selected scope from Rev28 reviewable at the domain/entity and HTTP contract level; implementation approval is still absent.
- Scope authority: owner selected Teacher lesson upload, Manager review/Public publication, and Parent read/share. The implementation scope is unchanged from Rev28.
- Supersedes as the current proposal: Plan Rev28 `PLAN_REV28_BACKEND_LESSON_LIBRARY_UPLOAD_REVIEW_PARENT_READ_20261028.md` (SHA-256 `22CBC9E4360B39BDD995B683B5B9681D962D3D1C54355F929F0B1C3BE2387FE6`). Rev28 remains preserved.

## Included implementation scope

Use Rev28's full implementation scope and acceptance criteria, including Teacher CRUD/upload, deterministic non-AI extraction and Teacher confirmation, Manager approval for Teacher Public access, selected/group sharing, Parent read-only access and Platform Admin hide. Preserve existing Parent/Teacher drawing, occurrence and video flows. Do not add AI, frontend work or production storage-provider choice.

The formal API contract and entity/storage mapping are in [LESSON_LIBRARY_API_CONTRACT_DRAFT_REV29_20261028.md](../artifacts/LESSON_LIBRARY_API_CONTRACT_DRAFT_REV29_20261028.md). It defines base path, naming rules, authorization, entities, endpoint purposes, request/response DTOs, state transitions and error codes. The API artifact is part of the exact plan approval scope (SHA-256 `81405D5BB6FC5FBAE50E8E73796FFABBC7C2E5B898C8BA7CEEF99AA3176407A2`).

## Naming and architecture decisions captured by this revision

- `Lesson` is the reusable-library aggregate root. A `LessonOccurrence` is a different entity and is not introduced as a synonym for Lesson.
- `LessonVersion` is immutable; `LessonActivity` is an ordered child of one version, distinct from a catalog `Activity`.
- `LessonSourceDocument` and `LessonDocumentRevision` are library-owned; they must not point to occurrence-owned source-document rows.
- `LessonAccessGrant` represents one exact audience/capability edge. A Public publication request is the grant to the `PUBLIC` audience in `PENDING_REVIEW` state; do not create a duplicate publication table/entity.
- `ParentGroup`/`ParentGroupMembership` stay owned by BE1. `UploadSession`/`Asset` stay owned by Core. Lesson stores typed opaque references and calls owner ports rather than writing cross-owner tables.
- HTTP resource names are plural nouns under `/api/lesson-library/v1`; actor role is resolved from verified context, not encoded into a role-specific resource or accepted from the request body.

## Updated review/approval package

- Plan Rev29 SHA-256: recorded in FEAT-063 `status/STATUS.md` and source registers after the contract artifact is frozen.
- Contract artifact SHA-256: recorded beside the plan hash in the same records.
- Implementation remains blocked until the owner approves this exact Rev29 plan and linked contract revision in `approvals/TASK_APPROVAL.md`, as required by repository `AGENTS.md`.

No code, database migration, test/build, live database, file upload, AI/provider/Modal operation or deployment was performed for this contract clarification.
