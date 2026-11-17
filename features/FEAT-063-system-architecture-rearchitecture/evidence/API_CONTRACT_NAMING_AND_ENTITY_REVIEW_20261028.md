# API contract, naming and entity review — EV-063-22

- Date: 2026-10-28 (Asia/Saigon).
- Purpose: document the repository contract conventions and prepare the Rev29 Lesson Library API contract.
- Sources: FEAT-047 `API_CONTRACT.md`; BE1 contracts/routes; SRS §9.6 and §31; Data Table Register §2, §14; backend architecture and contracts/integration guides; Rev28 implementation plan.

## Findings applied

- Existing BE1 API uses a feature-scoped versioned base path (`/api/be1/v1`), `X-Request-ID`, strict request schemas, `contract` response discriminators and error bodies `{code,message,request_id}`. The SRS lists `/v1/lessons` as a proposed resource group, not a final OpenAPI contract.
- Domain entities must not be confused with persistence rows or API DTOs. Rev29 defines `Lesson`/`LessonVersion`/`LessonActivity`/`LessonAccessGrant` separately from table names and `*RequestV1`/`*V1` DTO names.
- A Public publication request can use the existing proposed `lesson.access_grants` model as a Public audience grant in pending-review state; no duplicate publication entity/table is proposed.
- `ParentGroup` is BE1-owned, Core owns upload sessions/assets, and Lesson owns its library-specific source-document lifecycle. Occurrence-owned documents are not reused for reusable library items.

## Limits

This review produced a draft contract, not a signed API implementation contract. No code, test, database, runtime, upload, external service, AI or child data was used.
