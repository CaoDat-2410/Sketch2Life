# Sketch2Life backend API reference

- **Tree and commit:** branch `feature/backend-srs-api-and-fe-integration`, commit `297f2849` (goal v4 Phases A, B and C merged)
- **Date:** 2026-11-25
- **Generator note:** Generated from code by agy and checked by Claude (route paths were compared with the router code; rows that could not be proven are marked `UNVERIFIED`)

## Files

| File | Content |
|---|---|
| [PARENT_API.md](PARENT_API.md) | Parent routes: auth, profiles, support needs, the `/v1/story-runs` family, uploads, notifications and push, lesson library reads, Parent groups, personal video quota. |
| [TEACHER_API.md](TEACHER_API.md) | Teacher routes: class roster and profiles, lesson library authoring and versions, lesson occurrences and plan revisions, Teacher story runs, projection, Teacher AI routes, notifications. |
| [SCHOOL_MANAGER_API.md](SCHOOL_MANAGER_API.md) | School Manager routes: organizations and classes, assignments, roster counts, library review and sharing, parent groups, feedback, notifications, school capacity. |
| [PLATFORM_ADMIN_API.md](PLATFORM_ADMIN_API.md) | Platform Admin routes under `/api/platform-admin/v1`: organizations, accounts, audit, inbox, moderation, operations, e-mail deliveries, runtime settings. |
| [ERRORS_AND_CONVENTIONS.md](ERRORS_AND_CONVENTIONS.md) | Error envelope, wire error code catalogue, `Idempotency-Key`, `If-Match` and ETag, cursor paging, correlation id, auth and the uniform 404. |
| [ARCHITECTURE_AND_STATE_MACHINES.md](ARCHITECTURE_AND_STATE_MACHINES.md) | Backend layers, persistence, Alembic counts, and the state machines for StoryRun, Lesson occurrence, and class and subscription. |

## How to read the route tables

Each row has: method, path, purpose, request, response, error codes, idempotency, SRS ids, status.

Status values:

- `MERGED`: found in the code at the commit above.
- `PENDING-MERGE`: implemented in the Phase D/E working trees (`v4d`, `v4d2`, `v4e`), not in the code at the commit above.
- `pending merge (Phase D, planned)`: planned only (Teacher invitation, offboarding, force-close, suggestions); not in the code. Do not call these.
- `owner: Billing/Capacity (not documented in detail here)`: billing, capacity and subscription routes belong to another owner; only method and path are listed.
- `UNVERIFIED: ...`: the generator could not prove the item in the code. Treat it as unknown.

Where a route serves two roles, the full row is in one role file and the other role file holds a cross-reference row.

## Limits

- The code decides. If a row and the code differ, the code is right; report the row.
- Examples use placeholders (`<id>`, `{{name}}`); no tokens, keys or personal data are in these files.
- The files are generated, so wording may be uneven; they have been checked by path comparison with the code and by spot checks, not by running the API against a live backend.
