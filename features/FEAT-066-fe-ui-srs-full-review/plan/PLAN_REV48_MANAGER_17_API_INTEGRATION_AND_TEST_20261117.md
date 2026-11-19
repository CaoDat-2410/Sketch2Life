# FEAT-066 Plan Rev48 — Manager 17-route integration and test record

- Date: 2026-11-17 (Asia/Bangkok).
- Status: APPROVED_FOR_EXECUTION for the route audit, focused tests, safe smoke checks, evidence and record-only GitHub push.
- Owner request: plan the integration of all 17 Manager business API routes, test them, record the results and push the record to GitHub.
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- API baseline: origin/dev `1c9148e88600a101887e477541c4c4893ba1c7df` (route baseline recorded by Rev40); current local route declarations are unchanged except the bootstrap ordering fix.
- Product authority: FEAT-063 SRS v2.7-draft Rev60 via docs/context/SRS_AUTHORITY.md; unsigned.

## Goal and definition of done

Produce a verifiable test matrix for all 17 Manager business routes, distinguish currently integrated routes from contract/policy blockers, rerun the Manager FE tests and safe BE checks, record exact results and limitations in FEAT-066, then push only the Rev48 plan/test record to GitHub without staging unrelated dirty application work.

## Current route disposition

- 11 business route paths already have FE integration from the approved Rev41–43 work. Reuse these calls; do not duplicate them.
- Six BE route paths exist but remain unavailable to Manager UI until their request/authorization prerequisites are addressed. Test their current guards/contracts in isolated fixtures or verify the UI does not call them; do not call these writes against the live QA organization.
- Shared `GET /api/auth/v1/me` is a separate role-resolution route and is excluded from the count of 17. Firebase sign-in is an SDK call, not a BE endpoint.

| # | Route | Current status | Test focus |
|---:|---|---|---|
| 1 | GET /api/be1/v1/organizations/{organization_id}/me | FE auth/scope gate; live 200 recorded | role assignment shape, organization-wide school_admin scope, deny wrong role/scope |
| 2 | GET /api/be1/v1/organizations/{organization_id}/classes | FE wired; live 200 empty | tenant scope, empty/error/loading |
| 3 | POST /api/be1/v1/organizations/{organization_id}/classes | FE adapter exists; UI unavailable pending capacity guard | assert no live mutation; verify capacity gate |
| 4 | GET /api/lesson-library/v1/organizations/{organization_id}/access-grants | FE wired | pending PUBLIC filter, cursor, error/empty |
| 5 | GET /api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id} | FE wired; current version only | version matching and stale-version deny |
| 6 | POST /api/lesson-library/v1/organizations/{organization_id}/access-grants/{access_grant_id}/decision | FE wired with revision/idempotency | request shape, stale revision, no live write |
| 7 | GET /api/be1/v1/organizations/{organization_id} | FE wired; live 200 recorded | organization metadata only, tenant scope |
| 8 | GET /api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles | FE wired; no live class available | minimal fields, effective-consent gate, no media/opaque ID rendering |
| 9 | POST /api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles | BE only; not Manager-compatible under current guard | verify Teacher/synthetic-pilot restriction; keep UI unavailable |
| 10 | GET /api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents | FE wired; no live class available | scoped read, state/effective fields only |
| 11 | POST /api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents | BE only; consent actor/evidence policy unresolved | no live write; verify UI unavailable |
| 12 | POST /api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents/{consent_id}/revoke | BE only; consent actor/evidence policy unresolved | no live write; verify UI unavailable |
| 13 | GET /api/lesson-library/v1/organizations/{organization_id}/parent-groups | FE wired; live 200 empty | pagination, tenant scope, empty state |
| 14 | POST /api/lesson-library/v1/organizations/{organization_id}/parent-groups | FE wired with explicit submit/idempotency | adapter/UI success/error tests; no live group creation |
| 15 | POST /api/lesson-library/v1/organizations/{organization_id}/parent-groups/{parent_group_id}/invitations | BE only; no scoped Parent discovery | no live write; verify unavailable until discovery/invitation contract exists |
| 16 | DELETE /api/lesson-library/v1/organizations/{organization_id}/parent-groups/{parent_group_id}/members/{membership_id} | BE only; no Manager membership read/revision source | no live write; verify unavailable pending membership read and revision contract |
| 17 | POST /api/be1/v1/classes/{class_id}/assignments | BE only; no scoped Teacher-candidate read | no live write; verify unavailable pending candidate discovery |

## Work breakdown

| ID | Task | Depends on | Parallel with | Acceptance check | Effort | Risk |
|---|---|---|---|---|---|---|
| R48-1 | Reconcile all 17 paths, current FE callers, BE guards and SRS boundaries | None | None; baseline is the critical path | Route matrix above matches source/evidence; no guessed endpoint or role | Small | Medium: source snapshot can drift |
| R48-2 | Run focused FE auth, Manager route-gate, service and page tests | R48-1 | R48-3 | All selected files pass; record exact counts; no API write to live QA | Small | Low |
| R48-3 | Run BE route-composition/contract checks and isolated PostgreSQL acceptance tests only when the configured DB name is explicitly disposable `*be1_acceptance` | R48-1 | R48-2 | Report pass/skip/block separately; never point test writes at the dev QA database | Medium | Medium: test DB may be unavailable |
| R48-4 | Run read-only local health and unauthenticated protection probes; reuse EV-051 authenticated results unless a safe authenticated session is already available | R48-1 | R48-2/R48-3 | Record status codes without exposing credentials/tokens; no business writes | Small | Medium: no browser automation or token may be available |
| R48-5 | Run production build, targeted lint and diff/security/harness/architecture validators | R48-2/R48-3 | None | Exact command results recorded; pre-push security checks pass | Medium | Medium: existing dirty worktree may affect repo-wide validators |
| R48-6 | Write EV-054 and update FEAT-066 context, decisions, status and indexes | R48-1 through R48-5 | None | Every route has tested/blocked/untested status and evidence link | Small | Low |
| R48-7 | Create a docs-only commit containing only the Rev48 plan, approval and evidence record; push the current task record | R48-6 | None | Commit paths contain no unrelated source, `.env`, credentials or child data; push succeeds | Small | Medium: remote policy/network may reject push |

## Integration prerequisites that remain open

Do not mark the following routes integrated or enable their UI based solely on client-side code:

- Class create: backend must enforce the SRS class-capacity rule (FR-T-03) from an authoritative entitlement source.
- Profile create and consent record/revoke: owner must resolve the adult/Parent consent actor and acceptable source evidence; the current BE pilot guard is Teacher/synthetic-only and current consent write is a staff-origin pending record.
- Parent invitation: add/approve a scoped Parent discovery or invitation contract; do not accept a guessed principal reference.
- Membership revoke: provide a scoped membership read plus the current membership revision/ETag needed for safe revoke.
- Teacher assignment: provide a tenant-scoped Teacher candidate read before selecting a subject.
- Lesson review: an exact immutable-version read is still missing; stale grants remain blocked.
- School quota, billing/invoices/reconciliation, school feedback and inbox are absent from the 17-route inventory and have no current mounted Manager API.

These are API/SRS dependencies, not FE implementation omissions that can be fixed by bypassing current guards. Any backend contract, authorization-policy, schema or open-SRS decision change requires a separate, explicit owner decision and plan revision.

## Safety and scope

- Preserve the existing Manager Firebase role and BE1 organization assignment checks; never infer organization permission from the client role alone.
- No live business mutations, class/profile/consent/group/member seeding, real child data, secret/token output, backend/schema/authorization changes or new dependencies.
- Use the current empty nonproduction QA organization only for safe reads. PostgreSQL acceptance tests may write only to a separately verified disposable `*be1_acceptance` database.
- Preserve all unrelated dirty worktree changes. No application source commit. The requested GitHub commit is limited to the Rev48 plan/approval/test record.
- The user explicitly requested focused tests. Do not run unrelated project test suites.

## Final acceptance

1. The FE auth chain and every one of the 17 business routes have an explicit current status and a test result or precise blocker.
2. Focused FE tests pass, and BE tests are either isolated/pass or accurately marked skipped/blocked.
3. Read-only smoke results are separated from mocked/unit results; no write is reported as live success.
4. Production build, targeted lint and required pre-push validators are recorded.
5. EV-054 and indexes are updated; only the Rev48 record is committed and pushed.
