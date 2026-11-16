# Three-role web FE remediation and local review — Rev57 — 2026-11-11

Evidence ID: FEAT-066-EV-018
Plan: revision 15, SHA-256 86c6a13185797c8b5912ca3b6adb54b63f58d8ff87f1bebb16a6652434eb331e
Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation
Source commit at review: 3c1caf479eb6d6757d84890f73c07f185e32a9f9 (remediation remains uncommitted)

## Authority and scope

Used only the authority-selected FEAT-063 system architecture SRS v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5. It remains unsigned and awaiting owner sign-off. Sections 1–31 are the working target requirements; §32 is source evidence only. Plan revision 15 and the user’s direct authorization were recorded before application source changes.

Scope was limited to Teacher, School Manager, Platform Admin, directly shared web API client code, and FEAT-066 governance/evidence. No backend, Parent, other Admin app, mobile/native, package/lockfile, credential, or production-data changes were made.

## Implemented

- Shared API client: added an upload-session status read and caller-supplied idempotency keys for existing key-capable mutations. A logical retry retains its key; contracts without an idempotency header remain unchanged.
- School Manager M01: loads the lesson for the selected PUBLIC grant and enables review only when the returned current immutable version matches the grant version and contains structured lesson content. A mismatched/unknown version leaves decisions disabled because the current API has no GET-by-version contract. Added opaque-cursor grant pagination and stable idempotency keys for retries. Review content contains no child media/story.
- Teacher T05: consent is displayed per child and purpose from API consent records; missing or failed records are not called effective. Removed local child-profile CRUD and cross-class fallback from the preview route. The current BE1 profile POST is synthetic-pilot-only, not a product roster flow.
- Teacher T02/T03: added cursor pagination and retry-stable keys for supported mutations. T03 persists only upload metadata in tab session storage (no filename, file bytes, credential, or child data); it verifies the reselected file by SHA-256, queries the existing upload-status API, sends only missing parts for OPEN sessions, and replays completion with the same key to recover a completed upload result.
- Teacher unsupported routes: T04 session sketch deck, T06 Story Run, T07 video/projection confirmation, and T08 profile/settings now state the missing product API without local success behavior. T03 extraction editing/final immutable-revision confirmation remains unavailable where the contract is absent.
- Platform Admin: removed local fixture moderation/catalog/operations mutations and success signals. A01 reports the missing authenticated role discovery, queue/list/detail and exact-revision dependencies. A02 uses only the existing health endpoint and identifies missing organization, queue/job, billing reconciliation, quota, catalog lifecycle, and audit APIs.

## Local review

A loopback-only Edge preview was used with isolated browser storage. HTTP(S) requests outside the three Vite ports (127.0.0.1:5172, :5173, :5174) were blocked. No real account, Firebase ID token, backend production, provider, or user/child data was used.

The capture helper saved 34 route-state screenshots for 17 routes at 1440×900 and 390×844, plus one post-action M01 screenshot (35 PNG files total):
- School Manager: M01 and M02 dashboard, teachers, classes, quota, and settings.
- Teacher: T01, T02, T03, T04, T05 list/detail, T06, and T07.
- Platform Admin: A01 and A02 including the catalog panel.
- interaction-observations.json records route, heading, viewport/document width, visible state, and checks.

All 34 captures report zero horizontal overflow and no Vite error overlay. M01 local preview interaction after “Yêu cầu chỉnh sửa” reports “Chờ duyệt: 2”, “Đã duyệt: 0”, and “Yêu cầu chỉnh sửa: 1”; the visible preview notice explicitly says it changed local state only and was not sent to the API. This is not an authenticated backend decision test. M01 tab/panel keyboard semantics were previously recorded in EV-007; the current change did not alter those tabs. The source retains role=tab, aria-controls, aria-selected, roving tabIndex, arrow-key handling, and labelled tabpanels. No physical screen-reader run was performed.

The T03 screenshot shows the no-token preview state. Authenticated upload, pagination, grant decisions, and health response could not be verified: no Firebase token/backend was configured, and the browser policy intentionally blocked network requests outside loopback. A02's captured health failure is therefore not evidence of backend health.

## Remaining API and owner blockers

- Teacher: product profile create/update/lifecycle; extraction edit and confirmation into an immutable revision; occurrence/session and lesson-plan flows; product sample selection/StoryRun; video playback token and projection confirmation; Teacher profile/settings APIs. Existing T02/T03 APIs still need an authorized authenticated integration review.
- School Manager: class capacity enforcement and create/archive/suspend lifecycle; Teacher directory/provisioning and safe assignment management; product roster lifecycle; billing/invoice/payment/subscription; quota/top-up; notification inbox; feedback reply. When a grant references a non-current lesson version, the current API cannot retrieve that exact version, so M01 remains read-only for that item.
- Platform Admin: product role discovery/authorization; moderation queue, lesson detail and exact revision; catalog lifecycle/publish; organization/operations aggregates, billing reconciliation, quota and audit feed.
- The four M01 approval criteria and Admin/operator permission separation remain owner-open in EV-016. No pricing, quota policy, eligibility, auth policy, or other open SRS decision was invented or closed.

## Validation limits and result

No automated tests or builds were added or run, as instructed. The Vite dev previews reloaded the changed source and the browser review completed without Vite overlays. No security validator was run because there is no commit or push. All FE changes and evidence remain uncommitted and unpushed for user review.
