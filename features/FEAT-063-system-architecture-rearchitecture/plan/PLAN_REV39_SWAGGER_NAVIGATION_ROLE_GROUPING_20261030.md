# Plan Rev39 — professional Swagger navigation and role grouping

- Feature: FEAT-063 — whole-repository architecture redesign.
- Status: APPROVED for the exact documentation/navigation scope below, based on the project owner's direct request on 2026-10-30 to make Swagger easier to navigate by role or another professional grouping.
- Authority: continue the Rev37 contract-alignment work from approved Plan Rev38 while improving only OpenAPI tags and descriptions.
- Source contract: owner-supplied `API_CONTRACT_CATALOG_FEAT063_REV37_20261030.md`; SHA-256 `56FC8BEA01360E11F73E45B2D43AC1897540B30BC8AE524CDE1ECEFACFBB1B88`.
- Approval record: `approvals/TASK_APPROVAL.md` (this plan's SHA-256 is recorded there).

## Goal

Make Swagger's collapsed tag groups useful to developers by grouping APIs under their actual role where source guards establish one, and by API domain/workflow where role access is not explicit.

## Scope

1. Inspect current route guards and handler families; create role-oriented groups only for explicitly enforced Lesson Library actors (Teacher, School Manager, Parent, Platform Admin, or shared/owner scope).
2. Group the remaining BE1 and Demo APIs by their handler/domain families; label health and local storage examples separately.
3. Add a concise description for every tag and state that tags organize navigation rather than replace actual authorization. Keep the current Rev37 operation descriptions, request/response schemas, authentication declarations, metadata and route exposure intact.
4. Preserve exactly 124 mounted operations across 111 local-profile paths and all 11 unmounted candidate records.
5. Regenerate the OpenAPI snapshot, update parity assertions for the new tag taxonomy, and record the result in FEAT-063 context/status/source/evidence.
6. Restart the already-running local Swagger server so the owner can inspect the updated UI at the same URL.

## Acceptance criteria

- AC1: Every mounted operation belongs to one descriptive tag; all tags have human-readable descriptions.
- AC2: Lesson Library tags reflect explicit source-level role guards; upload-session owner routes are not mislabeled as a staff role.
- AC3: BE1/Demo, health and local storage routes are grouped by domain/workflow when the owner role is not explicit.
- AC4: No route, handler, authorization behavior, request/response schema or API behavior changes.
- AC5: Rev37 method/path, request, authentication, response and mounted/unmounted parity remains intact.
- AC6: `/docs` and `/openapi.json` continue to serve the latest local profile; the snapshot reflects the same tags.

## Verification

- Run focused Swagger parity checks and the snapshot exporter with local storage examples enabled.
- Confirm all route tags resolve to exactly one defined tag group, operation counts remain 124/111/11, and the local Swagger endpoints return HTTP 200 after restart.

## Explicitly excluded

Changing route behavior or authorization, mounting candidate APIs, modifying product flows or schemas, database/Docker/provider operations, deployment, commit and push.
