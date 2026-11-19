# FEAT-081 Wave 2 API Wiring Plan — Draft R2

**Status:** DRAFT for owner review only. No implementation, runtime, test, backend, or publication approval is granted.
**Date:** 2026-11-12
**Target:** `apps/ui-mobile` on `feature/fe-mobile-remediation`
**Goal:** Wire the existing Parent flow to the pending M2/S1a-P2 routes in two separately gated checkpoints. Wave 2 changes existing UI only in 2B and adds no screen.

## Authority, sources, and snapshots

FEAT-081 D-008 and the Wave 1 approval put backend route wiring outside launched Wave 1. FEAT-081 Revision 2 keeps `apps/ui-mobile` as this feature's location, but every follow-on wave still needs separate approval. This draft changes no pinned Wave 1 record and does not amend the unsigned FEAT-063 Rev60 SRS.

Read-only sources:

- Mobile worktree: `feature/fe-mobile-remediation` at `1f5bb0b5b1ab501a7120598a7e6e0de75217ddb3`. Its current working tree includes uncommitted Wave 1 code and records; Wave 1 remains awaiting owner acceptance. All app E/H pins below are current working-tree bytes, not assumed HEAD blobs.
- M2 integration worktree: `integration/dev-on-s1ap` at `8bf5f0afacedc1e1d406c272279fcfe3a7fd44a9`. The comparison plan is `.worktrees/dev-on-s1ap/features/FEAT-063-system-architecture-rearchitecture/plan/M2_INTEGRATION_DEV_ON_S1AP_CHANGES_VS_DEV_20261112.md`; the apps/mobile migration guide is `.worktrees/dev-on-s1ap/tmp/dev-on-s1ap/FE_API_MIGRATION_GUIDE_apps-mobile.md` (the requested root-level guide path was absent). The guide is a route crosswalk only; this plan follows the inspected `apps/ui-mobile` callers.
- Pending S1a-P2 profile proposal: the three requested files were read at the root checkout paths `backend/src/sketch2life/interfaces/http/routers/parent_profiles.py`, `backend/src/sketch2life/contracts/schemas/parent_profiles.py`, and `backend/src/sketch2life/domain/parent_profiles.py`. They are modified in the root checkout on `feature/feat063-m2-parent-teacher-foundation` at `c32d0b060e9625854dbdb781d7f8b11467bdca34`; they are not yet accepted or present in the inspected integration-worktree commit. Treat their added list/delete contract as **PENDING ACCEPTANCE and subject to change** until S1a-P2 lands and is accepted on the integration branch.
- Product routing: `docs/context/SRS_AUTHORITY.md`, `docs/context/SOURCE_REGISTER.md`, `docs/context/PROJECT_CONTEXT.md`, and FEAT-063 Rev60 SRS §9.8.
- Client sources read: `ParentApi.ts`, ports/module/error types, domain types, profile/learning use cases, controller, `ParentExpoApp.tsx`, `workflowTypes.ts`, and the existing Parent screens.

The M2 comparison says StoryRun routes are mounted only when `story_demo_enabled` is off. It records one failure and 91 passes in a selected backend test set, an interrupted broader test run, and no request-level tests for six new StoryRun routes. It reports that migration `20261112_parent_story_context` has not been run against a database. These source notes do not establish a running service's configuration or readiness.

## Owner decisions adopted for this draft

These are settled for tomorrow's bounded owner-run scenario and are not reopened here:

1. The scenario requires a lesson pin. Do not create a StoryRun without a selected `lesson_version` pin for tomorrow's test. This scenario constraint does not amend Rev60 or claim a broader product decision beyond the owner's instruction.
2. `drawing-understandings` remains unchanged. Do not add `Idempotency-Key` to that request.
3. Consent and data-authorization calls/fields stay removed for this integration. This plan does not design a consent-return path.
4. `activity-suggestions` is not mounted. The owner-run flow uses the existing Activity screen skip action; it does not call that route.
5. Use synthetic profiles only. Restore an existing synthetic profile through the new profile list route; create a synthetic profile if the list has none.
6. `OWNER_MODAL_CALL_APPROVED=NO` remains. The first Modal-touching request is `drawing-understandings`, followed later by `story-revisions`. The owner-run acceptance flow stops before `drawing-understandings` unless the owner separately records bounded Modal approval.

## Route-by-route mapping

All JSON requests retain the current Firebase bearer token, `Accept: application/json`, `X-Request-ID`, and `Content-Type: application/json` when they have a body. Profile create, patch, and deletion request use `Idempotency-Key` (one key per user action; 1–128 printable ASCII characters). StoryRun create and context/subject/script confirmations use their I2 key contract (1–256 characters). Legacy story-revision commands use 1–200 characters. The unchanged drawing-understanding request has no added idempotency key.

| Current `ui-mobile` call | Proposed route/body/response | Client treatment |
|---|---|---|
| `getConsentPolicy`: `GET /api/parent/v1/consent-policy` | Removed for this integration; no replacement. | Do not request consent policy or send consent fields. No consent-return design is part of Wave 2. |
| `listProfiles`: `GET /api/parent/v1/child-profiles` | `GET /v1/parent/profiles?limit={limit}&cursor={cursor}`. `limit` is optional, default 25, valid 1–100; `cursor` is optional and opaque. Unknown query keys and duplicate `limit`/`cursor` are invalid. Response is `{items: ParentProfileView[], next_cursor: string | null, request_id}`. | Use `items` for the current page. Read the next-page token from `next_cursor`; if non-null, URL-encode it into the next `cursor` query value and keep the chosen `limit`. Stop when it is null. On sign-in, restore an existing synthetic profile from this list and read its detail by ID when needed. This route is in the pending, unaccepted S1a-P2 working tree. |
| `createProfile`: `POST /api/parent/v1/child-profiles` with consent fields | `POST /v1/parent/profiles`, body `{display_name, age_months, interests_summary?}`; `interests_summary` may be omitted or null. Header `Idempotency-Key`. Response model `ParentProfileReference`: `{profile_id, revision_no, revision_hash}`. | Do not send consent fields. For a fresh synthetic profile, use `profile_id` to call GET-by-ID and hydrate the view before continuing. This route is covered by pending S1a-P2. |
| No current single-profile read method | `GET /v1/parent/profiles/{profile_id}`. Response is `ParentProfileView` `{profile_id, revision_no, revision_hash, display_name, age_months, age_band_ref, age_band_version, interests_summary, state, data_origin}`; the pending schema also allows `ParentProfileDeletePendingView` for a deletion-pending resource. | Add a typed get-by-ID method. Existing profiles are selected from list results and restored with this route as needed. |
| `updateProfile`: `PATCH /api/parent/v1/child-profiles/{id}` | `PATCH /v1/parent/profiles/{profile_id}` with `{expected_revision, display_name, age_months, interests_summary}` and `Idempotency-Key`; response is the direct `ParentProfileView`. | Show field errors safely. For `409 STALE_REVISION`, refresh the view and require adult review before a new write; do not blindly retry. Pending S1a-P2. |
| `grantAuthorization`: `POST /api/parent/v1/child-profiles/{id}/data-authorizations`; `revokeAuthorization`: `DELETE` on that route | Removed; no replacement. | Remove controller and screen actions that call these routes. |
| `archiveProfile`: `DELETE /api/parent/v1/child-profiles/{id}` | `DELETE /v1/parent/profiles/{profile_id}` with required `Idempotency-Key` (1–128 printable ASCII); returns HTTP `202 Accepted`, body `ParentProfileDeletePendingView`: `{profile_id, state: "DELETE_PENDING", request_id}`. | Treat the response as a deletion request, not completed deletion. Keep/render the profile as **deletion pending**, disable a duplicate delete action, and do not show it as fully deleted or discard its local pending state. Reconcile through a later read/list. The exact eventual transition/list visibility is not established by these three files. Pending S1a-P2. |
| `getActiveStoryRun`: `GET /api/parent/v1/story-runs/active/current` | `GET /v1/story-runs/active/current`, response `{request_id, story_run}` where `story_run` may be null. | Change the path and preserve active-run recovery. |
| `getStoryRun`: `GET /api/parent/v1/story-runs/{run_id}` | `GET /v1/story-runs/{run_id}`. | Change the path and align to the accepted response contract. |
| `listStoryRuns`: old `GET /api/parent/v1/story-runs?...`; `cancelStoryRun`: `POST .../{id}/cancel`; `deleteStoryRun`: `DELETE .../{id}` | No list/cancel/delete StoryRun route appears in the M2 route inventory; these remain later work. | Exclude Parent history/cancel/delete surfaces from tomorrow's acceptance. Do not claim those routes work on the integration service. |
| `createStoryRun`: `POST /api/parent/v1/story-runs` with old consent/profile-revision/context fields and split lesson IDs | `POST /v1/story-runs`; body `{parent_profile_id, topic?, adult_confirmed_idea?, lesson_version?: {lesson_id, version_id, content_sha256}}` plus `Idempotency-Key`. Remove `expected_profile_revision_id`, consent, and `context_confirmed`. Response `{request_id, story_run}` contains server context and optional lesson-pin snapshot. | For tomorrow's scenario require a real selected lesson version pin and include all three pin fields. The owner-run flow must not omit it. `409 ACTIVE_RUN_EXISTS` is the active-run conflict. Exact StoryRun/snapshot schemas remain subject to contract confirmation. |
| No current context-confirmation method | `POST /v1/story-runs/{run_id}/context-confirmation`, body `{expected_context_revision, context_snapshot_sha256, confirmed: true}` plus `Idempotency-Key`. | Present the server-created context and obtain adult confirmation. Creation's old `context_confirmed` field is not a substitute. For tomorrow, this is the last API command before the flow stops ahead of the Modal-touching drawing-understanding call. |
| `generateSketchGuide`: `POST /api/parent/v1/ai/sketch-guides` | Same path; M2 lists it as unchanged. | Outside tomorrow's pre-Modal acceptance path. |
| `analyzeDrawing`: `POST /api/parent/v1/ai/drawing-understandings`, body `{story_run_id, image_base64, media_type}` | Same route, body, and response. No `Idempotency-Key` is added by owner decision. | First Modal-touching flow step. Do not call during the approved owner-run test while `OWNER_MODAL_CALL_APPROVED=NO`. |
| `confirmSubject`: `POST /api/parent/v1/story-runs/{id}/subject-confirmations` | `POST /v1/story-runs/{run_id}/subject-confirmation`, current body `{expected_understanding_revision, confirmed_subject}`, plus `Idempotency-Key`. | Update prefix/singular suffix. Outside tomorrow's pre-Modal acceptance. |
| `suggestActivities`: `POST /api/parent/v1/ai/story-runs/{id}/activity-suggestions` | Not mounted on the integration branch according to M2 §2. | Do not call it. The owner directs the E2E path to the existing skip action on `ActivityScreen`; no change to that screen is in this allowlist. |
| `generateStory`: `POST /api/parent/v1/ai/story-runs/{id}/story-revisions`, body `{expected_understanding_revision, rewrite_instruction?}` | Same legacy path/body, with `Idempotency-Key` (1–200 characters). Replay may be indicated by `Idempotency-Replayed`; errors use the I2 envelope. | Later Modal-touching step. Not part of tomorrow's test without separate bounded approval; never automatically retry an unknown Modal outcome. |
| `confirmStory`: `POST /api/parent/v1/story-runs/{id}/story-revision-confirmations` | `POST /v1/story-runs/{run_id}/script-confirmation`, same body `{expected_revision, story_sha256}`, plus `Idempotency-Key`. | Update path. Outside tomorrow's pre-Modal acceptance. |
| `transcribeAudio`: `POST /api/parent/v1/story-runs/{id}/audio-transcriptions`; `confirmTranscript`: `POST .../{id}/transcript-confirmations` | No route mapping appears in the M2 route notes or apps/mobile migration guide. | Runtime availability is NOT VERIFIED. Audio is outside tomorrow's acceptance path. |
| Profile-sharing, lesson library/invitations, delivery/feedback, notifications, quota | Existing routes outside the profile and StoryRun route changes are not mapped by the M2 notes. | Do not infer their runtime status or claim them in this wave's acceptance. A valid lesson pin is required, but the lesson route/data path for the scratch service must be verified before the test. |

### Parent role gate, errors, and field validation

The pending profile router calls an active-Parent role check for create/list/read/update/delete. A denied role returns HTTP `403 ACTION_NOT_ALLOWED`; a role-store exception fails closed with HTTP `503 PARENT_STORE_UNAVAILABLE`. The client must not bypass either check or reveal profile existence/role details. Proposed safe localized message meanings:

- `403 ACTION_NOT_ALLOWED`: “This action is not available for this account.” Do not say which role or resource is missing.
- `503 PARENT_STORE_UNAVAILABLE`: “Profiles are temporarily unavailable. Try again later.” Do not continue as if the user were authorized and do not automatically retry a mutation.
- `401` authentication errors: request sign-in again using the existing auth flow.

The pending `ParentErrorResponse` schema declares `code`, `message`, `correlation_id`, `retryable`, `request_id`, optional `retry_after_seconds`, optional `current_version`, and optional `field_errors`. Field errors are non-echoing `{field, code}` pairs. The pending schema maps validation conditions to safe codes such as `REQUIRED`, `EMPTY`, `TOO_LONG`, `OUT_OF_RANGE`, `INVALID_TYPE`, `INVALID_FORMAT`, and `UNKNOWN_FIELD`; profile inputs include display name, age months, interests summary, expected revision, cursor/limit, profile ID, and `Idempotency-Key`.

Map known profile field errors to localized inline guidance: display name required/empty/too long; age must be a whole number in the supported 36–120 month range; optional interests may be cleared or shortened; stale revision requests a refresh; invalid cursor/limit requests a profile-list refresh. Missing/invalid idempotency keys and unknown fields receive a generic retry/edit message. Never echo submitted child data or raw backend details.

The pending router raises some FastAPI `HTTPException(detail={...})` bodies, while the declared error model is the top-level `ParentErrorResponse`; the global error serialization was not inspected. Until the accepted contract resolves that discrepancy, the adapter proposal parses both top-level fields and a nested `detail` object, and maps by HTTP status/code even when optional correlation/retry fields are absent. Preserve the request ID from `X-Request-ID` as fallback. The exact wire shape is an R2 unknown, not a reason to leak `detail.message` directly.

`409 ACTIVE_RUN_EXISTS` refreshes `GET /v1/story-runs/active/current` and restores a returned run; it does not repeat create. `409 STALE_REVISION` refreshes the affected profile or lesson and asks the adult to review. Do not auto-replay a mutation with a newly generated key.

### Per-file edit map

The route table above is implemented only through the following paths; no additional UI or helper file is implied.

**2A E/N files:**

- `ParentApi.ts`: add typed V1 profile list/read/create/patch/delete calls with cursor encoding, request IDs, idempotency headers, and robust error-envelope parsing; update StoryRun and confirmation paths/bodies to the I2 contracts.
- `ParentPorts.ts`: add source-compatible typed profile pagination/deletion and lesson-pin/context-confirmation operations to the ports.
- `ParentApplicationModule.ts`: expose the new API operations/use cases while retaining old exports needed by the still-unmigrated screens until 2B.
- `ParentApplicationError.ts`: represent status, code, request/correlation IDs, retry metadata, and safe field errors without surfacing raw backend details.
- `domain/types.ts`: add list cursor/page, delete-pending, V1 profile and lesson-pin/context contract types; preserve types still imported by current UI at the 2A boundary.
- `ParentProfileUseCases.ts`: add list-page/read/create/update/delete-request flows; retain DELETE_PENDING as a pending state and refresh on stale revision.
- `ParentLearningUseCases.ts`: require the selected lesson pin for tomorrow's StoryRun flow, map server context confirmation explicitly, recover ACTIVE_RUN_EXISTS via active-run read, and leave drawing-understanding without an added idempotency key.
- `parentApiI2Contract.test.ts`: fake-fetch contract tests for routes, query/body/header encoding, envelopes, and synthetic profile pagination/deletion; no network.
- `parentLearningI2.test.ts`: fake-port tests for required lesson pin, active-run/stale-revision handling, context confirmation, and the unchanged drawing-understanding header behavior.

**2B E files:**

- `useParentController.ts`: restore profiles through list/read, paginate, create synthetic profiles, request deletion, require a lesson pin, drive context confirmation, and use the existing Activity skip; remove consent/data-authorization calls.
- `ParentExpoApp.tsx`: wire the new controller state/actions and pass the selected profile explicitly to HomeScreen.
- `ContextScreen.tsx`: show the returned server context and collect explicit adult confirmation.
- `ProfileFormScreen.tsx`: submit profile create/edit through the new contracts and render safe field-level guidance.
- `ProfileScreen.tsx`: show restored/listed profiles and render DELETE_PENDING distinctly after the 202 response; do not imply completed deletion.
- `ProfileSharingScreen.tsx`: remove consent/data-authorization integration actions while preserving any separately supported sharing UI in this screen.
- `HomeScreen.tsx`: render the active-child label only from the explicit selected-profile prop, never by deriving a selection from the profiles array.

Profile-list and deletion-request UI are contained in `useParentController.ts`, `ProfileScreen.tsx`, and `ProfileFormScreen.tsx`; no new path or screen is added.

## Checkpoint 2A — API/domain/application contract, no UI

2A edits only the seven E paths and two N tests in the exact manifest below. It adds the new I2 profile and learning contracts, API operations, safe errors, and fake-based tests. It performs no screen/controller migration. Since the existing UI call sites remain untouched at this checkpoint, keep their types source-compatible until 2B; expose the new V1 types/operations additively and do not send removed consent/data-authorization fields or old routes from the new I2 API methods. The 2A state is not runtime-ready or owner-testable. 2A passes only on offline tests and typecheck; no UI/runtime acceptance is claimed.

**2A acceptance criteria**

- **2A-AC1:** Fake-fetch tests prove list query encoding and `items`/`next_cursor` pagination, create/read/patch/delete methods and response shapes, required idempotency headers, and no network access.
- **2A-AC2:** Fake-response tests cover pending deletion, `ACTIVE_RUN_EXISTS`, `STALE_REVISION`, role-denied `ACTION_NOT_ALLOWED`, `PARENT_STORE_UNAVAILABLE`, and field errors in supported top-level/nested forms; safe error metadata is retained where present.
- **2A-AC3:** Fake-port tests verify the tomorrow scenario requires a selected lesson pin, maps its IDs/hash exactly, omits legacy consent/profile-revision/context fields, and delegates explicit context confirmation. Drawing-understanding has no added idempotency header.
- **2A-AC4:** `pnpm run test` and `pnpm run typecheck` pass at the post-2A checkpoint. These are the only 2A acceptance checks.
- **2A-AC5:** Only 2A E/N paths change; all common H pins remain byte-identical.

## Checkpoint 2B — controller and existing UI

2B starts only after 2A-AC1–AC5 pass. It edits only the seven 2B E paths and uses the 2A API/domain operations. Bootstrap restores synthetic profiles from the paginated list; a fresh flow creates a synthetic profile and reads it by ID. The selected profile is passed explicitly from `ParentExpoApp` to `HomeScreen` for the active-child label; `HomeScreen` never derives it from the profiles array. `ProfileScreen` handles pending deletion as a pending state, not a completed delete. `ContextScreen` presents the server snapshot and confirmation. The flow is configured to require a lesson pin for tomorrow's run and uses the existing activity skip action without calling `activity-suggestions`.

**2B acceptance criteria**

- **2B-AC1:** Parent list pages restore existing synthetic profiles through `next_cursor`; fresh synthetic profile creation is followed by GET-by-ID before the profile is used.
- **2B-AC2:** Profile create/edit/delete UI shows safe field/role/store errors; a 202 deletion request remains visibly pending and is not represented as completed.
- **2B-AC3:** Home receives the selected profile via an explicit prop from `ParentExpoApp`; it does not infer selection from `profiles`.
- **2B-AC4:** The selected lesson pin is required for tomorrow's StoryRun create; the server context is presented and explicitly confirmed. The existing Activity skip is used; `activity-suggestions` is never called.
- **2B-AC5:** `pnpm run test` and `pnpm run typecheck` pass after the UI migration; H pins remain byte-identical; repository validators and `git diff --check` stay within their separate ceilings.
- **2B-AC6 — owner-run pre-Modal acceptance:** Using the scratch/integration service and synthetic profile data, run only these steps: authenticate Parent; list synthetic profiles; restore/read a listed profile or create a synthetic profile and GET it by ID; select a lesson pin; create the StoryRun with that pin; display and confirm the returned context. Stop immediately after successful context confirmation and before `POST /api/parent/v1/ai/drawing-understandings`. No drawing upload/analysis or story revision is allowed while `OWNER_MODAL_CALL_APPROVED=NO`. This is a pre-Modal contract acceptance, not a full Parent story completion.
- **2B-AC7:** No path outside the 2B E paths changes; shared H pins remain byte-identical; no code is staged or published under this plan.

## Runtime prerequisites for tomorrow's owner-run test

1. The Parent StoryRun router is mounted only when `story_demo_enabled` is off. The owner/coordinator must verify that the scratch/integration service has this setting before testing; otherwise the expected StoryRun routes are absent.
2. The BE1 Parent-role adapter depends on account columns in `public.be1_adult_identities`. The owner reports those columns may be missing; this is **NOT VERIFIED**. If the role reader cannot use them, profile operations fail closed with `503 PARENT_STORE_UNAVAILABLE`; do not bypass the gate.
3. The M2 branch report says migration `20261112_parent_story_context` has never run against a database. Gate A on a scratch database is an owner gate before route/runtime use. No shared or production database is in scope.
4. Configure `apps/ui-mobile` to point only at the approved scratch/integration service. Do not point the FE at production or another shared environment. The live profile/test data must be synthetic.
5. A valid lesson preset/version/hash must be available to satisfy the required `lesson_version` pin. The lesson-library route/data path on the scratch service is not established by the M2 profile sources and must be confirmed before the owner-run flow.
6. No Modal call is approved. Stop before drawing-understanding; do not proceed to story revisions without a separate bounded owner approval.

## Proposed exact allowlists and refreshed working-tree pins

All 23 E/H paths from R1 were rehashed from the mobile working tree while preparing R2. The byte counts and SHA-256 values below are the refreshed 2026-11-12 pins; they match R1's values. They pin the current bytes and must be rechecked against the then-current worktree before any later approval/launch. `HomeScreen.tsx` contains uncommitted Wave 1 work. The two N paths were absent at inspection.

**2A allowlist:** the seven 2A E paths, two 2A N paths, and every common H path below. **2B allowlist:** the seven 2B E paths and every common H path below. R paths are read-only only; all unlisted paths are outside both allowlists.

| Checkpoint | Mode | Exact path | Current bytes | Current SHA-256 |
|---|---|---|---:|---|
| 2A | E | `apps/ui-mobile/src/parent/infrastructure/http/ParentApi.ts` | 16,805 | `B448B9F13A153D2F90E1BAD6A284488117B4458223C1239FC2865F850438B918` |
| 2A | E | `apps/ui-mobile/src/parent/application/ports/ParentPorts.ts` | 6,318 | `52041644201401DB3CEDCBC7E9C34B7954B715FA80505990ACCB9897CC87D284` |
| 2A | E | `apps/ui-mobile/src/parent/application/ports/ParentApplicationModule.ts` | 1,766 | `0635F3E3C3278C8582C071A57E18C0ACB3EA3A766BD6A89167C5DA6D36E6F73B` |
| 2A | E | `apps/ui-mobile/src/parent/application/ParentApplicationError.ts` | 252 | `B62AC222CF5CDE6915ED23EE7052A82AA636BD1F1B7603E5D3E4413D0E7E4165` |
| 2A | E | `apps/ui-mobile/src/parent/domain/types.ts` | 7,338 | `76293E25E2F3157A7EC4053703CED9F25D9213DB0347FF2B59DDE44FFD18AD24` |
| 2A | E | `apps/ui-mobile/src/parent/application/use-cases/ParentProfileUseCases.ts` | 1,472 | `9035F49E23B8077131B1EC6AB8386FF8833CB5E6908AD7C595E79219C2E8DED1` |
| 2A | E | `apps/ui-mobile/src/parent/application/use-cases/ParentLearningUseCases.ts` | 3,563 | `F24500EF6F17C105F723B9B6EAC83924A66056C3F9608E418EB546BE4050E464` |
| 2A | N | `apps/ui-mobile/tests/parentApiI2Contract.test.ts` | absent | n/a |
| 2A | N | `apps/ui-mobile/tests/parentLearningI2.test.ts` | absent | n/a |
| Both | H | `apps/ui-mobile/package.json` | 2,081 | `AC8C5AB17D61B4DD126D28D9918CB4E4EB5C40EEFD3B4C965D9597294B9CD9FF` |
| Both | H | `pnpm-lock.yaml` | 470,780 | `5D778524730134CAFE360564408CBF45030B476C99A69CCD32897BAB55559A72` |
| Both | H | `apps/ui-mobile/app.json` | 1,560 | `9489E92A02306F6F0C1F575F3FF1C1FB9331BCB58ED2FD52E49880781F2D0651` |
| Both | H | `apps/ui-mobile/app.config.js` | 1,578 | `8D78BFAE71EF705299603BD4F6FBE74388756BBEEE93A1C6F1C4D99341ED1F43` |
| Both | H | `apps/ui-mobile/metro.config.js` | 2,145 | `068C704CC6F14F15178424B584DF4FD36169C221A57C534FD39D59C209E7B5A1` |
| Both | H | `apps/ui-mobile/tsconfig.json` | 147 | `B16D29C183DA613864125B17F2C6EC4E19419EF3E47E7C207FD8E7622F941130` |
| Both | H | `apps/ui-mobile/src/parent/presentation/components/ui.tsx` | 11,444 | `722636038EE8CBDFA36A90F6D102ABB4F69A43DC5B6848978EEC8795DFFDB773` |
| Both | H | `apps/ui-mobile/src/parent/infrastructure/config.ts` | 1,049 | `F0C1E0198460E9A432E81D9E8724BCC35CD030CA8C411F2050503F1C87C0FF07` |
| Both | H | `apps/ui-mobile/src/parent/infrastructure/auth/ParentAuth.ts` | 10,305 | `BBFEEF77C3CABD2632AFE7EE96D6996509C809BB8521FBD80326223961DD6077` |
| 2B | E | `apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts` | 26,476 | `E9626384DC22C9F8A2F74E9F5683D9F53DACE6596DF8FE16A80CE49CCDC3ABEF` |
| 2B | E | `apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx` | 15,960 | `7319EFF269ED8C714E7AC1AD5F5BB91277E4F3ECB022E59473169C20F9D84C12` |
| 2B | E | `apps/ui-mobile/src/parent/presentation/screens/ContextScreen.tsx` | 2,499 | `B1E96B75C4E2396CDE249A4D7B191D22F50F673A6490A3CDDF0C6F5B715758B2` |
| 2B | E | `apps/ui-mobile/src/parent/presentation/screens/ProfileFormScreen.tsx` | 4,780 | `99EC05ABBE0C0460668CEE8418B3CF071945580ADC28311EE72A54EC12BA59E6` |
| 2B | E | `apps/ui-mobile/src/parent/presentation/screens/ProfileScreen.tsx` | 3,928 | `36C7C0732AF25DFAC7911C9B44E55253C2A358EB05CC1BDB03CCF5A869139773` |
| 2B | E | `apps/ui-mobile/src/parent/presentation/screens/ProfileSharingScreen.tsx` | 3,771 | `F0BA4F7FA51E887161CFBF88DC1A553540596616B7DAFBE35990FA75E494C1C4` |
| 2B | E | `apps/ui-mobile/src/parent/presentation/screens/HomeScreen.tsx` | 4,349 | `A09E8BC37C30DCFB293B68172119DB62C06DF93D1201C068BCC79958433B28E3` |

**R (read-only, never edited by either checkpoint):** `apps/ui-mobile/src/parent/presentation/navigation/workflowTypes.ts` (reuse existing context step); `apps/ui-mobile/src/parent/presentation/screens/ActivityScreen.tsx` (use its existing skip); `apps/ui-mobile/src/parent/application/use-cases/ParentLessonUseCases.ts`, `ParentPlatformUseCases.ts`, `apps/ui-mobile/src/parent/presentation/navigation/useParentPlatformController.ts`, `apps/ui-mobile/src/parent/ParentModule.ts`, and existing `mainFlowSafety.test.mjs`, `storyDraft.test.ts`, `apiRetryIdentity.test.mjs` (integration references only); the M2 route comparison, apps/mobile guide, and three pending S1a-P2 files (read-only, pending acceptance). The Wave 1 `PLAN.md`, `PLAN_REVISION_2.md`, `DECISIONS.md`, ADR, approval, status, and context remain outside this draft's write scope.

## Command ceilings proposed for the split

These are new proposed Wave 2 ceilings requiring separate approval. No command below was run for R2.

| Command | Ceiling | Planned invocations and reason |
|---|---:|---|
| From `apps/ui-mobile`: `pnpm run test` | 3 total | Baseline before 2A, post-2A, and post-2B. Three source checkpoints are needed to identify whether an API-contract failure appears in 2A or a regression is introduced by the UI wiring in 2B. |
| From `apps/ui-mobile`: `pnpm run typecheck` | 3 total | Baseline before 2A, post-2A, and post-2B, for the same checkpoint isolation. |
| From repository root: `python tools/validate_harness.py` | 2 total | One baseline snapshot and one final post-2B validation; not part of 2A acceptance. |
| From repository root: `python tools/validate_repository_security.py` | 2 total | One baseline and one final post-2B validation; required before any later commit/push by repository rules. |
| From repository root: `python tools/validate_architecture.py` | 2 total | One baseline and one final post-2B validation; not part of 2A acceptance. |
| From repository root: `git diff --check` | 2 total | One baseline and one final post-2B whitespace check; not part of 2A acceptance. |

2A's acceptance remains only offline tests plus typecheck as requested. Validators and `git diff --check` are budgeted for baseline/final governance snapshots, not as a hidden 2A gate. The tests use fake `fetch`, fake `AuthTokenPort` and fake `ParentApiPort` with synthetic data only. The package script is `vitest run tests` followed by `node scripts/validate-ui-copy.mjs`; no focused test command is required. If pnpm would install or modify dependency state, stop for owner disposition; no install is included here.

## Known unknowns after these decisions

1. The exact accepted StoryRun create response, `context_snapshot`/lesson-pin snapshot fields, and context-confirmation response schema are not established by the inspected profile files and migration handoff.
2. The migration guide requires context confirmation before story generation, but the required order relative to drawing analysis is not established by the files read. Tomorrow's flow stops before drawing analysis regardless.
3. The three requested S1a-P2 files were readable, but the accepted integration version, service implementation, global FastAPI error wrapper, BE1 role-adapter schema, database state, and runtime flags were not verified. The pending router's `HTTPException(detail=...)` shape and `ParentErrorResponse` schema need reconciliation.
4. The availability of lesson-list/detail routes and a valid pin on the scratch service is not established by the M2 profile sources. No database or service was contacted.
5. The exact post-`DELETE_PENDING` transition and whether a pending row remains in subsequent list pages are not specified by the three requested files.

## Risks and sequence after review

- **Pending backend contract:** The list/delete routes and role gate were read from modified, unaccepted files in the root M2 worktree. Do not treat them as deployable or accepted until S1a-P2 lands and the accepted integration diff is reviewed; their contract may change.
- **CaoDat collision risk — in-flight ownership NOT VERIFIED:** FEAT-081 CONTEXT records CaoDat built the existing `ui-mobile` base and may edit the same Parent paths on `dev`. All app E files overlap that base. `HomeScreen.tsx` also contains uncommitted Wave 1 work. Reconcile ownership and preserve current bytes before any later launch.
- **Checkpoint boundary:** 2A must remain source-compatible with unchanged UI call sites so offline typecheck can pass. Its API/domain additions are not runtime-ready. 2B starts only after 2A tests/typecheck pass and switches the controller/screens to those contracts.
- **Backend evidence gap:** The integration report has no request-level tests for six new StoryRun routes, a selected backend test failure, and an interrupted broader run. Fake tests prove client serialization only; the owner pre-Modal run proves only profile and context routes.
- **Provider limit:** `OWNER_MODAL_CALL_APPROVED=NO` prevents the actual drawing analysis and story generation steps. The owner-run acceptance is deliberately partial and must not be reported as full Parent end-to-end completion.
- **Contract-safe errors:** Map role/store/field errors to generic localized copy; never reveal another profile's existence, role assignment, raw child data, or unfiltered server messages.

| Order | Work | Depends on | Checkpoint |
|---|---|---|---|
| 1 | Owner accepts the pending S1a-P2 list/delete/role contract and confirms scratch-service prerequisites and a valid lesson pin. | Owner/backend gates. | No source change until accepted contract and runtime target are known. |
| 2 | Implement the 2A API/domain/application additions and two fake-based tests. | 1 | Run full test and typecheck; pass 2A ACs before UI edits. |
| 3 | Implement 2B controller and existing-screen integration, including profile pagination/deletion-pending UI, context review, active-child prop, required lesson pin, and activity skip. | 2A passes. | Run full test and typecheck; review exact 2B allowlist. |
| 4 | Run final validators/diff check within ceilings, then owner/coordinator performs only the approved pre-Modal scratch-service flow. | 3 | Record result through context confirmation; stop before drawing-understanding. |

**End state:** R2 is a planning draft only. No Wave 2 launch or runtime operation is authorized.
