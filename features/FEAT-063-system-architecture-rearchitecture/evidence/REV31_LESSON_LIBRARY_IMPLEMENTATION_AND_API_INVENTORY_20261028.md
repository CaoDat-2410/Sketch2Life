# EV-063-24 - Rev31 Lesson Library backend implementation and complete API inventory

Date: 2026-10-28
Plan: Rev31 (`BC948B27F5CFADD05EC6D12B0B7D989241CDEB6FC3CA6CAB1521988C712BBB8C`) and Addendum A (`570BC65BE74A82261EC2455147EAF33FB0575B166B73EF506084BBF07A62727D`), approved in `approvals/TASK_APPROVAL.md`.

## Delivered

- Added the Lesson Library domain contracts, request/response schemas, persistence tables, service and HTTP router; mounted the router in the combined application.
- Implemented 30 operations for lesson CRUD/versioning, resumable private source upload, deterministic document filtering/extraction, moderation/publication, access grants, Parent reading/download/invitations and Platform Admin moderation.
- Kept upload sources private and separate from occurrence-owned documents. Upload completion is synchronous and returns `READY_FOR_REVIEW`; owner-scoped GET and DELETE upload-session operations support status/resume and abort.
- Added an additive Alembic migration source and three Lesson-owned support tables: `lesson.library_source_documents`, `lesson.library_document_revisions`, and `lesson.command_receipts`.
- Preserved existing Parent, Teacher, BE1 and demo method/path declarations. The route inventory records all declarations and their mount status.
- Updated the API contract with the Rev31 reconciliation; updated the SRS and Data Table Register implementation crosswalk, current FEAT-063 context/status/source registers, and project-wide source register.
- Current reconciled API contract SHA-256: `78D4F99C4EBD51C460CF02863FD2C595AA5AE3D01E7433B7637DB416B765C085`.
- Added local ClamAV service wiring for fail-closed document scanning. No AI generation, OCR, generated lesson content or frontend work was added.
- Broader FEAT-063 requirements for Parent-Teacher child-profile grants, LessonOccurrence history/feedback, AI suggestion/sketch generation, billing/quota endpoints and new Story/video endpoints remain outside Rev31 and are called out in the API inventory.

## API inventory findings

The static source inventory lists 135 router declarations: 56 BE1/classroom, 35 demo/local-flow, 30 Lesson Library, 3 conditional local-storage examples and 11 candidate/fixture/unmounted declarations. The combined app exposes 121 unconditional router operations; enabling the local storage example adds 3. Framework OpenAPI/docs routes are described separately and excluded from the router count. See `../artifacts/API_INVENTORY_FEAT063_REV31_20261028.md`.

The 3 upload-support tables make the source-derived target crosswalk 92 active plus 48 legacy/read-only, or 140 projected physical mappings. This is a target-model reconciliation, not a live database inventory. SRS v2.3 remains unsigned.

## Evidence limits

Static source and documentation review only. No tests/builds, application startup, OpenAPI runtime export, Docker pull/start, security validation, database inspection or migration, AWS/provider call, deployment or real-child-data processing was performed. The Alembic migration is present but unrun. Runtime authorization, scanner availability, storage integration and migration behavior remain unverified.
