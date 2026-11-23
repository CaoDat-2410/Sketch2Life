# FEAT-066 Plan Rev39 — School Manager API/UI crosswalk

- Status: DRAFT — planning only; awaiting owner approval before implementation.
- Owner request: finish the Platform Admin API availability check, then prepare the next web role (School Manager) if no more SRS-ready Admin feature API can be integrated.
- Worktree/branch: `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`; `codex/fe-ui-web-remediation` at `b72f9e46`.
- API source baseline: `origin/dev` at `1c9148e88600a101887e477541c4c4893ba1c7df`.
- Product requirements: canonical FEAT-063 SRS v2.7-draft Rev60, unsigned, via `docs/context/SRS_AUTHORITY.md`. Treat §32 as environment-specific as-built evidence; preserve open questions.
- Scope: read-only API/UI crosswalk and proposed Manager sequence. No app/backend/API calls, source edits, tests, build, commit, or push in this revision. Do not edit `approvals/TASK_APPROVAL.md`.

## Admin closeout finding

The account list/create/update routes under `/api/platform-admin/v1/accounts` are already typed and used by the Platform Admin account UI. The general `GET /health` probe is also wired, but it reports only the API health endpoint and does not establish queue, billing, or platform-wide health.

One additional command exists: `PATCH /api/lesson-library/v1/platform/lessons/{lesson_id}/moderation`, and the typed web client has a `moderateLesson` method. It is not wired into a usable Admin moderation flow: there is no platform moderation queue/list or exact immutable-version detail read. The route guard checks the `platform_admin` role, while the SRS reserves content moderation for the Platform Admin Content Admin permission. Keep the page blocked and do not invoke this command with guessed IDs/revisions. Therefore there is no additional end-to-end, SRS-ready Admin feature API to integrate before moving to Manager planning.

## Manager API/UI crosswalk on origin/dev

| Flow | Backend contract | Web status | Readiness |
|---|---|---|---|
| Resolve active organization assignment | `GET /api/be1/v1/organizations/{organization_id}/me` | Called by the public lesson review flow and the BE1 manager shell | Available; preserve server-side organization scope |
| Read classes | `GET /api/be1/v1/organizations/{organization_id}/classes` | Used by the Manager classes page | Available and wired |
| Create class | `POST /api/be1/v1/organizations/{organization_id}/classes` | Used by the Manager classes page | Available and wired; server requires active School Manager assignment |
| List pending public lesson grants | `GET /api/lesson-library/v1/organizations/{organization_id}/access-grants?state=PENDING_REVIEW&audience_kind=PUBLIC&cursor=...` | Used by Manager review page, including cursor pagination | Available and wired |
| Read lesson for review | `GET /api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}` | Used by Manager review page | Partial: response exposes current version; UI correctly blocks when its version differs from the grant version. No exact immutable-version read was found, so stale grants cannot be reviewed safely yet |
| Decide public grant | `POST /api/lesson-library/v1/organizations/{organization_id}/access-grants/{access_grant_id}/decision` with revision and idempotency key | Used by Manager review page; reason required for request-changes and approval requires explicit review confirmation | Available and wired, gated on matching reviewed version |
| Assign Teacher to class | `POST /api/be1/v1/classes/{class_id}/assignments` | No assignment command UI found | Backend command exists; no scoped Teacher candidate-list contract was found, so a picker cannot be built without guessing identities |
| Read/manage class roster and consent | Organization/class profile and consent GET/POST/revoke routes in BE1 registry | No Manager roster/consent UI wiring found in the reviewed module | Backend routes exist; expose only fields required by SRS and keep child media/story inaccessible |
| Manage Parent groups/invitations | Organization-scoped parent-group and invitation routes in Lesson Library | No Manager UI wiring found in the reviewed module | Routes exist; validate role guards and intended group capability before implementation |
| School quota/billing and organization feedback | No School Manager quota/billing/invoice/reconciliation or feedback-thread read/reply routes found in the mounted API routers | Not integrated | Backend/API contract required; quota-purchase/allocation policy remains open in SRS Q193 |

## SRS boundaries

- School Manager is scoped to one assigned organization: groups, school quota, Teacher public-lesson review, and feedback within that organization.
- Teacher lesson becomes public only after School Manager approval. Review must use the exact version referenced by the pending grant.
- School Manager must not see another organization or child media/story by default. Roster UI must use only the minimum permitted profile fields.
- Do not invent billing, quota purchase/allocation, feedback, or permission behavior while the related contract or owner decision is absent. The SRS remains a draft, and open questions stay open.

## Proposed implementation order after owner approval

1. Recheck the current dirty-worktree baseline and approvals; preserve unrelated local changes.
2. Complete the existing public-lesson review flow only after the backend supplies an exact-version read and its authorization/revision contract is confirmed. Until then, keep stale-version actions disabled with an explanatory state.
3. Extend Manager class operations with Teacher assignment only after a tenant-scoped candidate-list/read contract exists. Reuse the existing list/create class API and show authoritative loading, error, empty, and success states.
4. Assess scoped roster/profile/consent and Parent-group flows against the SRS data-minimization and role guards; implement only flows whose API contract is sufficient.
5. Defer school quota/billing and feedback-thread UI until their APIs and open owner decisions are resolved.

## Acceptance criteria for any later implementation

- Every read and mutation is bound to the authenticated principal and assigned organization by the backend; cross-organization requests fail closed.
- Public approval is possible only after the exact `version_id` in the pending grant has been loaded and visibly reviewed. Stale/missing version, permission, or revision keeps the action disabled.
- State-changing actions use the API revision/ETag and idempotency contract; request-changes includes a non-empty reason.
- Class/roster/group UI never fabricates candidates or data and never exposes child media/story. Errors are not presented as empty successful results.
- Quota/billing/feedback remain unavailable until their backend contracts and any SRS owner decisions are recorded.
- Before implementation, write/approve the concrete plan in `approvals/TASK_APPROVAL.md`; no approval is implied by this crosswalk.

## Review limits

This is a static source crosswalk against the named `origin/dev` commit plus the existing web worktree. No live API response, authenticated mutation, browser review, test, or build was performed for Rev39.

## 2026-11-18 work plan and API count

Count unique HTTP method + route pairs once; query variants and cursor pages do not count as separate APIs.

- **17 Manager-relevant operations exist on `origin/dev`.** Six are already called by the web UI: GET organization assignment (`/organizations/{org}/me`), GET/POST classes, GET access grants, GET lesson detail, and POST access-grant decision.
- **11 additional operations are present in backend routes but are not wired in the reviewed Manager UI:**
  1. GET `/api/be1/v1/organizations/{org}`.
  2. POST `/api/be1/v1/classes/{class_id}/assignments`.
  3–4. GET/POST `/api/be1/v1/organizations/{org}/classes/{class_id}/profiles`.
  5–7. GET/POST `/api/be1/v1/organizations/{org}/classes/{class_id}/consents` and POST `/api/be1/v1/organizations/{org}/classes/{class_id}/consents/{consent_id}/revoke`.
  8–9. GET/POST `/api/lesson-library/v1/organizations/{org}/parent-groups`.
  10. POST `/api/lesson-library/v1/organizations/{org}/parent-groups/{parent_group_id}/invitations`.
  11. DELETE `/api/lesson-library/v1/organizations/{org}/parent-groups/{parent_group_id}/members/{membership_id}`.
- **Tomorrow's target: wire up to 10 of those 11**, grouped as organization overview (1), roster/consent (5), and Parent-group management (4). The class-assignment command is excluded from UI work until there is a tenant-scoped Teacher candidate-list API; do not guess a Teacher identity.
- Existing lesson review remains in place. Exact-version reads are still a backend gap; keep the current mismatch blocker and do not claim stale-grant review is complete.

### Suggested sequence for 2026-11-18

1. **Preflight (about 1 hour):** check the worktree diff and Manager route guards/request/response models for the ten target operations. If any role/scope contract does not meet the SRS, stop that slice and report the backend gap.
2. **Organization + roster/consent (about 3 hours):** add typed FE methods for organization read, profile list/create, consent list/create/revoke; connect them to an organization-scoped Manager view with truthful loading/error/empty/success states.
3. **Parent groups (about 2–3 hours):** connect group list/create, Parent invitation, and member revoke; keep organization and membership scope visible and require confirmation for revoke.
4. **Integration pass (about 1–2 hours):** reconcile API response/error handling with the existing authenticated Manager shell and preserve the six wired operations. Do not add fake rows, default identities, or cross-tenant shortcuts.
5. **Closeout:** record any blocked operations and evidence. Do not claim quota/billing, feedback, Teacher assignment, or exact-version lesson review is complete; those still need backend/API work. Source implementation starts only after the owner records approval for this scope.

The 10-operation target is conditional on the existing endpoint guards and payloads being sufficient for FEAT-063 Rev60. If inspection finds a mismatch, report the exact endpoint and leave it out rather than broadening permissions or inventing a contract.
