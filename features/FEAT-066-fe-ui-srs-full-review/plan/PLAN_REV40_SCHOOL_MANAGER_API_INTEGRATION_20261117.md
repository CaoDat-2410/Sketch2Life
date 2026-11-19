# FEAT-066 Plan Rev40 — School Manager API integration

- Status: DRAFT — planning only; implementation requires owner approval recorded in `approvals/TASK_APPROVAL.md`.
- Owner request: prepare the API integration plan for the School Manager web portal, including authentication and the number of available backend APIs.
- Worktree/branch: `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`; `codex/fe-ui-web-remediation` at `b72f9e46`.
- API source: `origin/dev` commit `1c9148e88600a101887e477541c4c4893ba1c7df`.
- Product authority: FEAT-063 SRS v2.7-draft Rev60 via `docs/context/SRS_AUTHORITY.md`; draft is unsigned. SRS sections 2.3, 3 and 31 govern role/tenant scope and lesson visibility; quota-purchase policy Q193 remains open.
- This plan does not authorize application source changes. Preserve all existing dirty worktree files. Do not change approval records as part of planning.

## Count and baseline

Count unique backend HTTP method + path pairs. Query filters/cursor pages do not create new APIs.

- **18 distinct BE routes are relevant to the current Manager portal scope:** 17 Manager business routes from Plan Rev39 plus shared `GET /api/auth/v1/me`.
- **Firebase `signInWithEmailAndPassword` is an SDK authentication call, not a BE API.** The web flow then calls `GET /api/auth/v1/me` with the Firebase ID token to resolve the account role. There is no dedicated Manager `/login` route. `POST /api/auth/v1/registrations` is registration, not login.
- **Six Manager business routes are already called by the FE:**
  1. `GET /api/be1/v1/organizations/{organization_id}/me` — active organization assignments.
  2. `GET /api/be1/v1/organizations/{organization_id}/classes` — scoped class list.
  3. `POST /api/be1/v1/organizations/{organization_id}/classes` — create class.
  4. `GET /api/lesson-library/v1/organizations/{organization_id}/access-grants` — access-grant list; current UI filters pending PUBLIC grants and uses cursor pagination.
  5. `GET /api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}` — lesson detail; current response only exposes current version.
  6. `POST /api/lesson-library/v1/organizations/{organization_id}/access-grants/{access_grant_id}/decision` — approve/request changes with revision and idempotency handling.
- **Ten additional BE operations are the proposed integration target, if existing role guards and request/response models meet the SRS:**
  7. `GET /api/be1/v1/organizations/{organization_id}` — organization summary.
  8–9. `GET` and `POST /api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles` — roster read/create.
  10–12. `GET` and `POST /api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents`; `POST /api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents/{consent_id}/revoke` — consent read/record/revoke.
  13–14. `GET` and `POST /api/lesson-library/v1/organizations/{organization_id}/parent-groups` — group read/create.
  15. `POST /api/lesson-library/v1/organizations/{organization_id}/parent-groups/{parent_group_id}/invitations` — invite Parent.
  16. `DELETE /api/lesson-library/v1/organizations/{organization_id}/parent-groups/{parent_group_id}/members/{membership_id}` — revoke membership.
- **One further route exists but is excluded from the integration target:** `POST /api/be1/v1/classes/{class_id}/assignments`. There is no tenant-scoped Teacher candidate-list API, so the FE must not guess an assignee.
- The shared auth route makes the overall count 18; Firebase SDK sign-in is not part of that count. The 10 target routes plus 1 excluded command and 6 existing Manager routes make 17 Manager business routes.

## Proposed work breakdown for 2026-11-18

### 0. Reuse and verify existing authentication and organization scope

- Keep Firebase sign-in in `apps/web/src/modules/school-manager/be1/services/authService.ts`.
- Keep `GET /api/auth/v1/me` role resolution and `GET /api/be1/v1/organizations/{organization_id}/me` assignment check; do not invent a second login service or endpoint.
- Confirm the authenticated account maps to the expected School Manager portal and active organization. BE uses `school_admin` for organization assignment while the product role is named School Manager; preserve this distinction in the adapter and do not infer tenant access from account role alone.

### 1. Organization summary and scoped roster/consent (6 target routes)

- Add the organization summary read.
- Connect profile list/create and consent list/record/revoke to the selected class.
- Use only the fields permitted for School Manager; do not expose child images, generated stories, or media.
- Separate loading, API error, empty, and successful data states; mutations must reflect server-confirmed results.

### 2. Parent-group lifecycle (4 target routes)

- Connect organization-scoped group list/create and invitations.
- Connect membership revoke with explicit confirmation and server-confirmed completion.
- Verify the backend guard and payload scope for each operation before exposing the action.

### 3. Preserve existing lesson review and record blockers

- Keep the current pending PUBLIC grant list and decision actions.
- A decision remains disabled unless the loaded lesson version matches the grant's `version_id`.
- Do not claim complete review support for stale grants: there is no exact immutable-version read route in the reviewed API.
- Do not wire class assignment until a scoped Teacher candidate-list read exists.

### 4. Defer unsupported SRS areas

- Do not add fake quota, purchase/allocation, billing, invoice/reconciliation, or organization feedback views. These Manager contracts were not found in the mounted routers; Q193 remains open.
- Do not broaden role permissions or make client-only authorization decisions.

## Acceptance criteria

- Existing Firebase sign-in and shared `/api/auth/v1/me` behavior are reused; no fictitious Manager login endpoint is added.
- Every organization/class operation remains server-authorized for the active organization; cross-tenant and inactive-assignment access fail closed.
- All ten target operations are connected only if their BE role guard and payload satisfy FEAT-063 Rev60. Otherwise, document the exact blocked route and leave its UI action unavailable.
- Roster and consent views use minimal permitted data; no child media/story is returned or linked by the UI.
- Parent-group membership changes require clear confirmation and show success only after backend confirmation.
- Existing review actions keep revision/idempotency behavior and remain blocked for a stale/mismatched version.
- No fake identities, fixtures, API success states, or unapproved quota/billing policy are introduced.

## Governance and evidence

- This plan is DRAFT and does not constitute approval to implement. Before source changes, the owner must approve a concrete task and the approval register must record it.
- Preserve unrelated local worktree changes. No application code, tests, build, runtime API calls, commit, or push are part of Rev40 planning.
- Crosswalk predecessor: `plan/PLAN_REV39_SCHOOL_MANAGER_API_UI_CROSSWALK_20261117.md`; evidence: `evidence/notes/EV-047_SCHOOL_MANAGER_API_UI_CROSSWALK_REV39_20261117.md`.
