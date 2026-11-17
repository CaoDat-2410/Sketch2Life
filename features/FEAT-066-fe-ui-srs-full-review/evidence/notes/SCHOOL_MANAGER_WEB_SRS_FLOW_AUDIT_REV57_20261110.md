# FEAT-066-EV-009 — School Manager web SRS Rev57 flow audit (pre-redesign)

Date: 2026-11-10 (Asia/Bangkok)
Worktree: `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`
Branch: `codex/fe-ui-web-remediation`
Plan: revision 8, SHA-256 `C71F0824DC4A7E4901912BB2D8883B954BA6F2ED438BAB9F9C0871CBE3B54D7C`; feature-local approval ledger contains the same hash.

## Product source

Read `docs/context/SRS_AUTHORITY.md` first. It points to FEAT-063 `SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`. SHA-256 verified as `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`. This is v2.7-draft Rev57 and remains awaiting owner sign-off. This audit uses §§1–31 only; §32 is environment-specific as-built evidence.

## Flow coverage matrix

| SRS target | Current School Manager surface / checked API | Result and missing dependency |
| --- | --- | --- |
| Organization dashboard (§21.5, §31.3) | `/m02-organization-management`, fixture KPIs, quick links | Route exists, but summary is not server-backed. No organization dashboard summary API was found; figures are not evidence of live state. |
| Class capacity/create/archive/suspend (UC-06, FR-T-02/03, §5.3) | `?section=classes`; `GET /organizations/{organization_id}/classes` and `GET .../classes/{class_id}/profiles`. `POST .../classes` exists, but `CreateClassRequest` has no capacity input/enforcement. | List/roster read can be wired. Capacity-safe creation is blocked; there is no class archive/suspend endpoint. Keep mutations unavailable until the server contract enforces slots and supports lifecycle states. |
| Teacher provisioning, directory, assignment, transfer/offboard (UC-12/13, FR-T-02/14/17) | `GET .../organizations/{id}/me`, assignment create/revoke endpoints exist. | No Manager teacher directory/search/provision/invite or selection UI/API; no safe transfer/offboard saga contract. Low-level assignment mutation is insufficient to expose an end-to-end UI. |
| Class roster and managed profile (UC-03, FR-T-02/04/05) | `GET .../classes/{class_id}/profiles`; current Manager display is read-only and shows names. | Read-only roster is partially supported. Enrollment add/edit/transfer lifecycle is not an established Manager flow. FE should not fetch or reveal child story/media. |
| Billing, invoice, payment, subscription, renewal/grace/downgrade (UC-08, FR-B-01–09, §5.3/§23) | Settings route exists and shows unavailable state. Search of checked HTTP routers and `apps/shared/backendApi.tsx` found no compatible Manager billing/invoice/payment/subscription surface. | Blocked by backend/API/contracts. No checkout, transaction, invoice state, renewal behavior, policy or price may be fabricated. |
| Organization quota and top-up (UC-10/16, FR-B-10–13) | `?section=quota` currently contains preview values and disabled actions. | No organization quota summary, usage ledger, top-up or verified payment grant API in the checked surface. Preview values are not live balance. |
| Inbox/notification (UC-15, FR-B-08/09/14) | Header has static `Hộp thư chưa khả dụng`; no click affordance or unread dot. | No inbox API/route was found. Keep status non-interactive; a push signal is not a substitute for the SRS inbox source of truth. |
| Teacher lesson public review (§21.5, FR-PL-05) | `/m01-publication-review`; `accessGrants` and `decideAccessGrant` wrappers call the Lesson Library grant list/decision endpoints. | Contract-backed API mode exists; local preview is non-persistent and does not prove an API decision. Do not expose media. The four-item approval rubric remains unstated in FR-PL-05 and owner-open. |
| School feedback reply (§31.6, FR-PL-22) | No School Manager feedback route. The only feedback route found in checked HTTP routers is the unrelated supervised-flow feedback endpoint. | Blocked by missing school-scoped feedback list/reply API and UI route. Do not substitute inbox or direct chat. |
| Privacy and tenant boundary (§20, §31.3/31.6, FR-PL-01/02/08) | M01/M02 contain organization metadata and roster names, no child story/media route. | FE can check absence/presentation only. Tenant enforcement and privacy authorization require backend contract/security evidence; the Manager must not receive default media access. |
| Logout (user-reported defect) | Sidebar action uses existing `TeacherContext.logout`; prior EV-005 records manual route/session checks. | UI action is present and previously manually verified. It is retained; auth provider sign-out was not tested because no provider session was configured. |

### Overall completeness

The School Manager UI is not complete against the SRS target flows. It has route-level coverage for dashboard, teachers, classes, quota, settings and M01, but the dashboard/quota summary is fixture-only; only class listing/read-only roster and M01 grant review have relevant API support. Teacher lifecycle, capacity-safe class lifecycle, billing/subscription/payment, quota/top-up, inbox and school feedback reply remain blocked by missing APIs/contracts. The UI must report those limits clearly and must not simulate success.

### Source cross-check

- `backend/src/sketch2life/interfaces/http/routers/be1_registry.py`: organization assignment/list/create/revoke, class list/create, profile list.
- `backend/src/sketch2life/interfaces/http/routers/lesson_library.py`: access-grant decision/list routes.
- `apps/shared/backendApi.tsx`: wrappers for assignments/classes/profiles and `accessGrants`/`decideAccessGrant`; no manager billing/inbox/quota/reply wrapper.
- Broad route search for billing, invoice, subscription, quota, inbox, notification, school feedback reply, class archive/suspend and transfer found no matching manager API in the checked router/API surface. The supervised session feedback endpoint is not school-scoped feedback reply.

## Worktree preservation

The authorized worktree is `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`, branch `codex/fe-ui-web-remediation`. At this checkpoint its unrelated existing dirty paths remain `approvals/TASK_APPROVAL.md`, two `apps/parent-ui` files and untracked FEAT-070. They are outside scope and remain untouched. Recursive inventory comparison found 29 FEAT-066 paths in the root checkout and 108 in this worktree; there were no root-only paths. The root FEAT-066 subset is older/different on shared paths, so no files were copied or overwritten. Root checkout changes remain untouched.

## UI implementation boundary

Revision 8 authorizes an adult-facing, welcoming school-office style for preschool/primary school management screens. Keep unavailable flows, M01 count/tab semantics, logout, privacy and existing route/API behavior. The implementation has not started at the time of this audit record.
