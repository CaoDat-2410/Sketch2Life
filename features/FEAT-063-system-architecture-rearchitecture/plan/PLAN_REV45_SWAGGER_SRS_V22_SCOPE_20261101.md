# Plan Rev45 — FE Swagger scope aligned to SRS v2.2

## Status

- Lifecycle: PLANNED; direct owner instruction recorded for approval before implementation.
- Feature: FEAT-063 — whole-repository architecture redesign.
- Branch: `dev`.
- Date: 2026-11-01, Asia/Saigon.

## Goal

Make the FE-facing `/docs` and `/openapi.json` show the currently implemented API operations that map to the Parent/Teacher/organization domains in the owner-selected SRS v2.2. Make missing SRS flows visible as implementation gaps without inventing routes or claiming the draft SRS route proposals are implemented contracts.

## Source baseline

- Owner-selected SRS: `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS_V2.2_PRESERVED_20261028.md`, version 2.2-draft, especially §§2–4 and §9.6. §9.6 explicitly describes logical route groups as proposals, not the final OpenAPI contract.
- Current implementation: mounted FastAPI handlers, route guards, DTOs, and `MOUNTED_OPERATIONS` metadata.
- Current published baseline before this plan: `artifacts/OPENAPI_FEAT063_REV44_20261031.json` (124 operations / 111 paths / 18 tags).
- Owner request: “giờ cập nhật lại swagger trên nhánh dev theo srs 2.2 đi”.

## Scope

1. Publish an explicit allowlist of 24 existing operations in four SRS-related groups:
   - `BE1 — Organizations & Classes`: 11 organization, assignment, class, profile, and consent operations.
   - `Teacher — Lesson Authoring`: 6 lesson create/update, source-document read/revision, upload-session creation, and lesson-version operations; exclude lesson access-grant creation.
   - `Teacher & School Manager — Lesson Library`: 3 lesson list/read/archive operations; exclude access-grant revocation.
   - `Lesson Library — Upload Session Owner`: 4 upload-session read/abort/part/complete operations.
2. Treat Swagger as a FE-facing projection. Preserve current handlers, route methods, authentication/authorization, request and response behavior, and the separate full mounted-operation inventory used for source parity.
3. Remove the `BE1` acronym from the FE-visible organization tag and use concise descriptions that say tags are navigation labels while each operation's guard remains authoritative.
4. Exclude from the FE document the existing classroom-session/device/canvas/artifact operations; gallery and local demo, renderer, whiteboard/video and storage-example routes; lesson-sharing/invitation routes; moderation; health endpoints; and unmounted candidate operations. Do not unmount or change these backend routes.
5. Add concise Swagger overview text identifying the included implemented scope and the major SRS v2.2 gaps: Parent profile/story/activity/job/playback APIs; Teacher lesson-occurrence/Sketch Deck/sample-video/projection APIs; activity catalog, quota/payment/subscription and notifications. Do not present these as available endpoints.
6. Export a feature-local OpenAPI snapshot and evidence recording the exact included/excluded operation inventory and verification limits.
7. Update FEAT-063 context, source register, decisions, status, and approval/evidence records for this revision.

## Acceptance criteria

- AC1: `/docs` and `/openapi.json` publish only the allowlisted implementation-backed operations and no local/demo, collaborative-classroom, gallery, lesson-sharing, health, or unmounted-candidate operations.
- AC2: The operation inventory contains exactly 24 operations across 17 paths and four tags; the full runtime route inventory remains separately available internally for parity review.
- AC3: Every published operation retains its current path, method, security, request/response schemas, examples, and operation ID; no product/API behavior changes.
- AC4: Swagger explains the current scope, role authorization boundary, SRS proposal status, and missing API flows without custom `x-` extensions or fake endpoints.
- AC5: The Rev45 snapshot is regenerated and a deterministic exporter verifies exact allowlist equality, tags, path/method uniqueness, schema-reference integrity, and absence of custom extensions.
- AC6: Feature-local evidence and governance records report the SRS draft status, excluded APIs, and verification not performed. No commit or push is made in this task.

## Explicit exclusions

- No new backend route, handler, DTO, auth rule, runtime validation, or persistence behavior.
- No changes to routes solely to match the SRS proposal paths.
- No fake Parent/video/Sketch Deck/quota/payment/notification operations or Try it out workarounds.
- No backend test suite, database, Docker, provider, deployment, commit, or push operation.

## Implementation and verification steps

1. Add a separate SRS v2.2 OpenAPI projection over the current full OpenAPI schema and keep the full schema available for internal contract inventory.
2. Assign the four public tags and SRS scope notes; prune unrelated public paths while preserving referenced component schemas.
3. Update the existing OpenAPI exporter and snapshot path to validate the exact projection inventory.
4. Update existing contract-test fixtures/expectations only as needed to distinguish the full runtime inventory from the FE-facing projection; do not run tests.
5. Run the OpenAPI exporter to generate the snapshot; statically inspect the JSON inventory and referenced schemas; inspect `git diff --check` and final branch/worktree.
6. Record commands, counts, hashes, findings, and not-run checks in feature-local evidence and status.

## Risks and limits

- SRS v2.2 is marked draft/pending owner sign-off. The owner selected it as the documentation baseline for this task; this does not sign off the SRS itself.
- SRS §9.6 provides logical target groups, not final route definitions. Published paths and schemas remain those of the current backend.
- The FE document will intentionally omit real mounted legacy/demo APIs. The full mounted inventory remains available in repository contract metadata and historical artifacts; this projection is not a claim that those backend routes were removed.
- Exposing only currently implemented operations makes SRS implementation gaps more visible; it does not complete those backend flows.
