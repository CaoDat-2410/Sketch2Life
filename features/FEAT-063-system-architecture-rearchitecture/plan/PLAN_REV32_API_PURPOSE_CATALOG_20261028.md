# Plan revision 32 - complete API purpose catalog

- Feature: FEAT-063 - whole-repository architecture redesign.
- Plan status at authoring: AWAITING_APPROVAL. This documentation-only scope becomes actionable when the owner's direct request to list every current API and its purpose is recorded against this exact plan hash in `approvals/TASK_APPROVAL.md`.
- Authority: direct owner request on 2026-10-28: "list all APIs currently in the system and what they are used for".
- Baseline: approved Rev31 API inventory with 135 declared route operations, including mounted, conditional-local, and unmounted candidate/fixture routes.

## Goal

Publish one complete API catalog with each declared HTTP method/path, concise purpose, owning handler, and runtime exposure status. Make clear which endpoints are active in the combined application, local-only, profile-specific, or unmounted candidates.

## Scope

1. Add a per-endpoint purpose to every route declaration in the Rev31 inventory without changing any method, path, router, or runtime behavior.
2. Retain handler/source attribution and classify runtime exposure from the existing route composition: combined, classroom/demo profile, conditional local example, or candidate/fixture/unmounted.
3. Keep FastAPI-generated OpenAPI/docs endpoints and the conditional `/renderer` static mount separately identified.
4. Link the purpose catalog from the existing FEAT-063 API inventory, evidence index, current context/status and source registers.
5. Record broader FEAT-063 requirements that have no implemented API in this slice.

## Acceptance criteria

- AC1: Every one of the 135 declared method/path operations has a distinct catalog row with method, path and concise purpose.
- AC2: Each row retains its source handler and route exposure category; unmounted fixture/candidate routes are not described as active APIs.
- AC3: Totals remain reconcilable: 56 BE1/classroom, 35 demo/local-flow, 30 Lesson Library, 3 conditional local-storage examples and 11 candidate/fixture/unmounted declarations.
- AC4: The catalog distinguishes 121 unconditional combined-app operations and 3 additional local-only routes; generated docs endpoints are outside the 135 router-operation count.
- AC5: This is documentation only. No API, code, schema, migration, credentials, runtime, tests, Docker, provider or deployment changes are made.

## Verification limits

Use the existing static route inventory and composition review. Do not run tests/builds, start Docker, inspect/migrate a live database, call providers, deploy, or commit/push.
