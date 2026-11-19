# EV-054 — Manager 17 API integration and test record

- Date: 2026-11-17 (Asia/Bangkok).
- Plan: plan/PLAN_REV48_MANAGER_17_API_INTEGRATION_AND_TEST_20261117.md.
- Approval: Rev48 is recorded in approvals/TASK_APPROVAL.md.
- Product authority: docs/context/SRS_AUTHORITY.md points to the FEAT-063 system architecture SRS v2.7-draft, Rev60. It remains unsigned.
- Scope: assess the 17 Manager business routes previously inventoried, test current FE/UI wiring and mounted backend contract, perform read-only local smoke checks, and preserve all application changes outside this record.

## Result summary

- All 17 method/path pairs are mounted in the current backend app composition: 17/17. This is a route-composition check, not a claim that all 17 were authenticated or functionally invoked.
- Current FE status remains 11 routes wired or adapter-backed; six routes blocked from Manager UI by policy or missing supporting reads. Class creation is adapter-backed but its UI action remains disabled until the BE enforces the SRS capacity rule.
- Focused FE checks: 4 files, 18 tests passed.
- Isolated BE contract/unit checks: 90 passed. The first run inherited SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED=true and produced 7 environment-related failures; rerunning with it explicitly false passed all selected checks.
- Production build passed. Oxlint exited 0 with 28 React warnings.
- Repository harness, architecture, security, and git diff --check validators passed.
- Read-only local probes: API health 200; FE /login?role=manager 200; unauthenticated /api/auth/v1/me and BE1 organization-assignment reads 401.
- A previously authenticated QA run on 2026-11-17 returned 200 for organization assignment, organization, classes, and Parent-group list; classes and groups were empty. Those authenticated requests were not repeated in this run.
- No live business write was sent. PostgreSQL-backed API acceptance tests were not run because BE1_TEST_DATABASE_URL is unset; no disposable acceptance database was provisioned.
- Browser-based Firebase sign-in was not automated in this verification. No credential or token was recorded.

## Test commands and environment

FE focused suite:

    npm run test -- --pool=threads --maxWorkers=1 --fileParallelism=false src/app/__tests__/PortalEntryPage.auth.test.tsx src/modules/school-manager/be1/__tests__/app.test.tsx src/modules/school-manager/be1/__tests__/managerBusinessService.test.ts src/modules/school-manager/be1/__tests__/managerBusinessPages.test.tsx

Result: 4 files passed, 18 tests passed.

BE selected contract/unit suite ran in the API container with SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED=false:

    tests/contract/test_app_composition.py
    tests/contract/test_be1_synthetic_pilot.py
    tests/unit/test_member_fact_consent_rules.py
    tests/unit/test_lesson_library_receipt_compatibility.py

Result: 90 passed.

The route-composition probe instantiated the application in test configuration with a closed loopback database URL and compared each expected Manager method/path against application.openapi(fe_projected=False). It found 17/17, missing=[]. It did not call request handlers or touch the QA database.

The live /openapi.json projection lists 11/17 of these operations. It omits the six Lesson Library operations at rows 4, 6, 13, 14, 15, and 16 below. The backend's full mounted route-composition check contains them; the public SRS projection omission must not be interpreted as proof those routes are unmounted.

## Per-route record

| # | Method and path | FE status | Verification / limitation |
|---:|---|---|---|
| 1 | GET /api/be1/v1/organizations/{organization_id}/me | Wired as Manager assignment gate | Prior authenticated QA read returned 200 with organization-wide school_admin; current unauthenticated probe returned 401; FE auth-gate tests passed. |
| 2 | GET /api/be1/v1/organizations/{organization_id}/classes | Wired | Prior authenticated read returned 200 with an empty list; full route composition confirms mounted. No class was seeded. |
| 3 | POST /api/be1/v1/organizations/{organization_id}/classes | Adapter exists; UI action disabled | FE capacity guard test passed. No live POST; BE still lacks authoritative enforcement for SRS FR-T-03. |
| 4 | GET /api/lesson-library/v1/organizations/{organization_id}/access-grants | Wired | Mounted by route-composition check; omitted from public OpenAPI projection. No authenticated call or focused FE test in this run. |
| 5 | GET /api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id} | Wired with current-version limitation | Mounted. It cannot prove/retrieve an exact immutable historical version; no authenticated call in this run. |
| 6 | POST /api/lesson-library/v1/organizations/{organization_id}/access-grants/{access_grant_id}/decision | Wired with revision/idempotency | Mounted; omitted from public OpenAPI projection. No live write or focused FE test in this run. |
| 7 | GET /api/be1/v1/organizations/{organization_id} | Wired | Prior authenticated QA read returned 200; full route composition confirms mounted. |
| 8 | GET /api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles | Wired as minimal roster read | FE Manager service/page checks passed. No live read because QA organization has no class. |
| 9 | POST /api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles | Not wired for Manager | BE route is constrained to Teacher/synthetic-pilot flow; the focused BE contract suite passed. No live write or Manager UI bypass. |
| 10 | GET /api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents | Wired as read-only status | FE Manager service/page checks passed. No live read because QA organization has no class. |
| 11 | POST /api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents | Not wired | Consent actor/evidence policy is unresolved; consent-rule unit checks passed. No live write. |
| 12 | POST /api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents/{consent_id}/revoke | Not wired | Consent actor/policy is unresolved; consent-rule unit checks passed. No live write. |
| 13 | GET /api/lesson-library/v1/organizations/{organization_id}/parent-groups | Wired | Prior authenticated QA read returned 200 with an empty list; FE service/page checks passed. Omitted from public OpenAPI projection. |
| 14 | POST /api/lesson-library/v1/organizations/{organization_id}/parent-groups | Wired with explicit submit/idempotency | FE service/page checks passed. No live group creation. Omitted from public OpenAPI projection. |
| 15 | POST /api/lesson-library/v1/organizations/{organization_id}/parent-groups/{parent_group_id}/invitations | Not wired | No organization-scoped Parent discovery contract; do not guess a principal ID. Route is mounted but omitted from public OpenAPI projection. No live write. |
| 16 | DELETE /api/lesson-library/v1/organizations/{organization_id}/parent-groups/{parent_group_id}/members/{membership_id} | Not wired | No scoped membership read/revision source for safe revoke. Route is mounted but omitted from public OpenAPI projection. No live delete. |
| 17 | POST /api/be1/v1/classes/{class_id}/assignments | Not wired | No organization-scoped Teacher-candidate read. Route is mounted; no live assignment write. |

## Remaining integration prerequisites

Keep these Manager actions unavailable until the backend contract or policy is resolved:

1. Class creation requires an authoritative capacity/entitlement check in BE1 (SRS FR-T-03).
2. Manager profile creation and consent record/revoke require an approved Parent/adult actor and evidence contract.
3. Parent invitations require scoped Parent discovery.
4. Membership revoke requires a scoped membership read and current revision/ETag.
5. Teacher assignment requires a scoped Teacher-candidate read.
6. Lesson review of an old grant requires an exact immutable-version read.
7. Quota, billing/invoices/reconciliation, school feedback, and inbox have no corresponding mounted Manager APIs in this inventory.

No BE contract, schema, authorization policy, SRS, database, or UI source was changed in Rev48. The next integration phase must resolve the listed prerequisites before enabling writes.
