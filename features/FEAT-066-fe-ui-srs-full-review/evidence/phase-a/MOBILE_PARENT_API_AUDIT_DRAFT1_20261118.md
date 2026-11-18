# Parent Mobile FE API Audit — Phase A Draft 1

Date: 2026-11-18  
Status: Read-only source audit; no runtime requests or tests performed.

## Scope and verified pins

| Source | Verified snapshot |
|---|---|
| Adopted SRS | Downloaded file and repository canonical copy both measure 701,157 bytes, SHA-256 B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5. It is v2.7-draft and unsigned. |
| Mobile worktree | .worktrees\mobile, branch feature/fe-mobile-remediation, HEAD 73fe001e3677ed30d8cdb33cefc1f66eb82d4966; 10 ahead / 45 behind origin/dev. Cached diff stat: 21 files changed, 1,665 insertions, 1,330 deletions. The unmerged apps/ui-mobile/tests/parentSrsBehavior.test.ts was not opened or touched. |
| Dev BE worktree | .worktrees\manager-api, branch feature/feat066-manager-api-contracts, HEAD 1c9148e88600a101887e477541c4c4893ba1c7df, tracking origin/dev. It has local modifications; effects of the modified lesson-library service on runtime responses are NOT VERIFIED. |
| M2 BE ref | origin/feature/feat063-m2-parent-teacher-foundation at 833df67789b9594ed41f83d672962ad99f1d2abd. |
| M2 frozen contract and inventory | Repository frozen OpenAPI: 847,426 bytes, SHA-256 E9C2D7C8E95225F3D1F8B708C50C9ACC19CF822508ABEFD4F85298AD2E6B3A0C. Inventory evidence: 56,475 bytes, SHA-256 B72228CE918DE75A6531ED6A01C9E2A1C9643D26BC69442505D87591414AE351. |
| Existing Bruno checks | Four Parent GET request files (profile list/detail and active/detail StoryRun) were read. They were not run. |

The frozen M2 inventory allows eight operations for client integration: five Parent profile operations, StoryRun create, active StoryRun read, and StoryRun-by-ID read. M2 adds StoryRun cancel and run_revision; cancel is not allowed for client integration. The three Parent AI assistance operations remain blocked.

## Audit conventions

Mobile paths and line references below describe the mobile working tree, including staged edits. ParentApi sends Authorization: Bearer, Accept, and X-Request-ID on its requests; it adds JSON content type when a body exists. It does not add Idempotency-Key by default.

The ParentApi error parser reads code, request_id, correlation_id, retryable, retry_after_seconds, field_errors, and current_version from a top-level object or FastAPI detail. It maps errors to local messages instead of using the server message, and does not parse the Retry-After response header. The M2 Parent profile/StoryRun error schemas align with SRS §9.8, with profile-specific extra fields. The inspected auth and Lesson Library routes return detail objects containing code and message, without the full §9.8 envelope.

“Status” below means statically documented by route code/OpenAPI, not observed through a live request.

## Product Parent and auth calls

| # | Method and path | Mobile caller, working-tree lines | Dev / M2 route and DTO comparison | Headers, errors, pagination and status | M2 8 | Classification |
|---:|---|---|---|---|---|---|
| 1 | GET /api/parent/v1/consent-policy | ParentApi.ts:69; use case/controller: ParentProfileUseCases.ts:23,76, useParentController.ts:220 | No matching route found in either snapshot. No BE DTO to compare. | ParentApi headers; no cursor. Status/response NOT VERIFIED. | No | OWNER-DECISION — the client requires a current consent-policy contract, but this path and DTO are not established by the frozen contract. |
| 2 | GET /v1/parent/profiles | ParentApi.ts:77; useParentController.ts:146 | Exists in dev and M2. List response request_id/items/next_cursor and FE envelope match. | ParentApi headers; no limit or cursor sent, and caller uses only the returned first page. 200; errors 400,401,403,409,422,503. | Yes, C2 | FIX-FE — support cursor continuation per SRS §21.1. |
| 3 | GET /v1/parent/profiles/{profile_id} | ParentApi.ts:81; ParentProfileUseCases.ts:34 | Exists in dev and M2. BE returns a flat profile view or delete-pending view; FE expects {request_id, profile} and reads envelope.profile. | ParentApi headers; no pagination. 200; errors 400,401,403,404,409,422,503. | Yes, C3 | FIX-FE — map the flat response and represent the delete-pending variant. |
| 4 | POST /api/parent/v1/child-profiles | ParentApi.ts:85,125; active use case/controller: ParentProfileUseCases.ts:40, useParentController.ts:280 | Exact path absent. M2 target counterpart is POST /v1/parent/profiles (C1). FE sends consent fields absent from frozen CreateParentProfileRequest; it expects a nested profile envelope instead of the flat ParentProfileReference. | ParentApi headers; Idempotency-Key missing. Target status 201; target errors 400,401,403,409,422,503. | No exact path; counterpart C1 allowed | FIX-FE — target path, DTO, response mapping, and required idempotency header must align. |
| 5 | PATCH /api/parent/v1/child-profiles/{profile_id} | ParentApi.ts:89,137; ParentProfileUseCases.ts:46, controller: useParentController.ts:330 | Exact path absent. M2 counterpart is PATCH /v1/parent/profiles/{profile_id} (C4). expected_revision, display name, age, and interests align; response wrapper does not. | ParentApi headers; Idempotency-Key missing. Target status 200; errors 400,401,403,404,409,422,503. | No exact path; counterpart C4 allowed | FIX-FE |
| 6 | POST /api/parent/v1/child-profiles/{profile_id}/data-authorizations | ParentApi.ts:97,146; use case/controller: ParentProfileUseCases.ts:58, useParentController.ts:385 | No matching route in dev or M2. Consent request/response DTO and status are NOT VERIFIED. | ParentApi headers; Idempotency-Key missing for this state change. | No | OWNER-DECISION — SRS requires consent handling, but no corresponding operation contract is established here. |
| 7 | DELETE /api/parent/v1/child-profiles/{profile_id}/data-authorizations | ParentApi.ts:105,153; use case/controller: ParentProfileUseCases.ts:63, useParentController.ts:406 | No matching route in dev or M2. DTO and status NOT VERIFIED. | ParentApi headers; Idempotency-Key missing for this state change. | No | OWNER-DECISION |
| 8 | DELETE /api/parent/v1/child-profiles/{profile_id} | ParentApi.ts:112,159; use case/controller: ParentProfileUseCases.ts:68, useParentController.ts:424 | Exact path absent. M2 counterpart is DELETE /v1/parent/profiles/{profile_id} (C5). M2 returns a flat delete-pending receipt; FE expects a profile envelope. | ParentApi headers; Idempotency-Key missing. Target status 202; errors 400,401,403,404,409,422,503. | No exact path; counterpart C5 allowed | FIX-FE |
| 9 | GET /v1/story-runs/active/current | ParentApi.ts:164,172; ParentLearningUseCases.ts:25,27; useParentController.ts:155 | Exists in dev and M2. Envelope matches; FE response type omits M2’s run_revision. M2 inventory notes the route summary remains marked [PROPOSAL]. | ParentApi headers; no pagination. 200; errors 400,401,403,404,409,422,500,503. | Yes, C7 | FIX-FE for the incomplete response type; the proposal marker remains an open contract note. |
| 10 | GET /v1/story-runs/{run_id} | ParentApi.ts:168,176; use cases: ParentLearningUseCases.ts:26,28; useParentController.ts:700 | Exists in dev and M2. Envelope matches, but FE type omits M2 run_revision. SRS uses {id} while frozen runtime uses {run_id}; inventory records the parameter spelling as open, not a wire-path difference. | ParentApi headers; no pagination. 200; errors 400,401,403,404,409,422,500,503. | Yes, C8 | FIX-FE for the incomplete response type. |
| 11 | POST /api/parent/v1/story-runs | ParentApi.ts:179; no active HTTP caller found; the V1 use case rejects before transport. | Exact path absent. M2 counterpart is POST /v1/story-runs (C6). FE body includes profile revision and consent fields not in the frozen create request; FE lacks the required response run_revision. | ParentApi headers; Idempotency-Key missing. Target status 201; errors 400,401,403,404,409,422,500,503. | No exact path; counterpart C6 allowed | FIX-FE |
| 12 | POST /api/parent/v1/story-runs/{run_id}/subject-confirmations | ParentApi.ts:183–186,321–326; active controller: ParentLearningUseCases.ts:80, useParentController.ts:907 | Exact path absent. Dev/M2 counterpart is /v1/story-runs/{run_id}/subject-confirmation (singular). Body fields align with that route. Counterpart is outside the eight allowed operations. | ParentApi headers; no Idempotency-Key. Counterpart success 200; complete error statuses NOT VERIFIED. | No | FIX-FE — path mismatch; integration also needs the M2 allowlist closed. |
| 13 | POST /api/parent/v1/story-runs/{run_id}/story-revision-confirmations | ParentApi.ts:191–196,351–355; use-case method exists, but no presentation caller was found. | Exact path absent. Dev/M2 counterpart is /v1/story-runs/{run_id}/script-confirmation. Body fields expected_revision and story_sha256 align. | ParentApi headers; no Idempotency-Key. Counterpart success 200; remaining errors NOT VERIFIED. | No | FIX-FE — path mismatch; the operation is outside the eight allowed operations. |
| 14 | POST /api/parent/v1/ai/story-runs/{run_id}/story-revisions | ParentApi.ts:206–214,338–349; use-case methods exist; no presentation caller was found. | Route exists in dev and M2. V1 request fields align with route schema. Frozen response is generic object, so exact FE response DTO is NOT VERIFIED. Legacy generateStory caller omits Idempotency-Key. | ParentApi headers; key present only on V1 method. Frozen responses 200,422. | No; assistance integration blocked | OWNER-DECISION — M2 explicitly blocks client integration for this assistance operation. |
| 15 | GET /api/lesson-library/v1/me/lessons?source=ALL&limit=50 | ParentApi.ts:234–238; useParentController.ts:487 | Exists in dev and M2. Page and summary fields substantially match; FE does not pass/consume cursor. | ParentApi headers; requests 50, no continuation. Frozen OpenAPI documents 200,422; runtime error statuses NOT VERIFIED. Lesson error bodies lack §9.8 fields. | No | FIX-FE for cursor continuation. |
| 16 | GET /api/lesson-library/v1/me/lesson-invitations?limit=50 | ParentApi.ts:240–244; useParentController.ts:488 | Exists in dev and M2. Page matches; FE invitation item type is a subset of BE LessonAccessGrantV1. No cursor continuation. | ParentApi headers; frozen 200,422; runtime errors NOT VERIFIED; error body is not §9.8. | No | FIX-FE for pagination/type completeness. |
| 17 | POST /api/lesson-library/v1/me/lesson-invitations/{access_grant_id}/accept | ParentApi.ts:247–254; useParentController.ts:554 | Exists in dev and M2. No request body; response typed unknown. | ParentApi headers plus required Idempotency-Key (present). Frozen 200,422; runtime errors NOT VERIFIED. BE errors use detail:{code,message}, not §9.8. | No | FIX-BE — error-envelope gap. |
| 18 | POST /api/lesson-library/v1/me/lesson-invitations/{access_grant_id}/decline | ParentApi.ts:257–264; useParentController.ts:560 | Exists in dev and M2. No request body; response typed unknown. | ParentApi headers plus required Idempotency-Key (present). Frozen 200,422; runtime errors NOT VERIFIED. BE errors are not §9.8. | No | FIX-BE |
| 19 | GET /api/lesson-library/v1/me/parent-group-invitations?limit=50 | ParentApi.ts:267–271; useParentController.ts:489 | Exists in dev and M2. Page matches; FE membership type omits some BE fields. No cursor continuation. | ParentApi headers; frozen 200,422; runtime errors NOT VERIFIED. BE errors are not §9.8. | No | FIX-FE |
| 20 | POST /api/lesson-library/v1/me/parent-group-invitations/{membership_id}/accept | ParentApi.ts:274–281; useParentController.ts:566 | Exists in dev and M2. No request body; response typed unknown. | ParentApi headers plus required Idempotency-Key (present). Frozen 200,422; runtime errors NOT VERIFIED. BE errors are not §9.8. | No | FIX-BE |
| 21 | GET /api/lesson-library/v1/me/lessons/{lesson_id} | ParentApi.ts:284–286; use case/controller: ParentLessonUseCases.ts:8, useParentController.ts:535 | Exists in dev and M2. FE LessonDetail omits required locale. | ParentApi headers; no pagination. Frozen 200,422; runtime errors NOT VERIFIED. BE errors are not §9.8. | No | FIX-FE |
| 22 | GET /api/lesson-library/v1/me/lessons/{lesson_id}/download | ParentApi.ts:288–293; export method exists; presentation caller NOT VERIFIED | Exists in dev and M2. LessonExportV1 shape matches. | ParentApi headers; no pagination. Frozen 200,422; runtime errors NOT VERIFIED. BE errors are not §9.8. | No | FIX-BE |
| 23 | POST /api/parent/v1/ai/sketch-guides | ParentApi.ts:295–305; use-case method exists; presentation caller NOT VERIFIED | Route exists in dev and M2. FE sends step_count:3; BE accepts 3–5, while SRS FR-P-11 requires 4–8 progressive steps. FE expects an image response; SRS target is a validated SVG guide. | ParentApi headers; frozen 200,422; error shape not §9.8. | No; assistance integration blocked | FIX-FE |
| 24 | POST /api/parent/v1/ai/drawing-understandings | ParentApi.ts:307–319; active controller: useParentController.ts:794 | Route exists in dev and M2; request matches the legacy BE DTO. FE posts image_base64 in JSON, contrary to SRS §21.1’s upload-session/chunk rule. | ParentApi headers; frozen 200,422; error shape not §9.8. | No; assistance integration blocked | FIX-FE — current route is a legacy artwork-ingestion flow. |
| 25 | POST /api/parent/v1/ai/story-runs/{run_id}/activity-suggestions | ParentApi.ts:329–335; active controller: useParentController.ts:975 | No matching route in dev or M2. Exact endpoint/request/response contract is not stated in adopted SRS. | ParentApi headers; status/DTO NOT VERIFIED. | No | OWNER-DECISION — do not treat the FE path as an approved BE contract. |
| 26 | POST /api/auth/v1/registrations | ParentAuth.ts:65–71; sign-up flow | Exists in dev and M2. FE reads status and role; BE returns those plus email_verified. | No bearer, X-Request-ID, or idempotency key. 201; errors 409,422,429,503. Error body is detail:{code,message}, not §9.8. | No | FIX-BE — standard error/correlation contract gap. |
| 27 | GET /api/auth/v1/me | ParentAuth.ts:170–173; sign-in role resolution | Exists in dev and M2. FE reads role/state; BE also returns role_revision. | Bearer present; X-Request-ID absent. Success 200; auth/scope errors include 401/403. Error envelope is not §9.8. | No | FIX-BE |

## Staged mobile changes relative to HEAD

The audit uses staged working-tree contents, not just HEAD. The staged ParentApi.ts changes move several methods away from the M2 route surface:

- Profile create/patch/delete were changed from /v1/parent/profiles... to /api/parent/v1/child-profiles...; idempotency headers were dropped.
- StoryRun create changed from /v1/story-runs with an idempotency key to /api/parent/v1/story-runs without one.
- Subject/script confirmation paths changed from singular /v1/story-runs/{id}/...-confirmation forms to plural /api/parent/v1/...-confirmations paths; their keys were dropped.
- listProfilesV1 lost its limit/cursor parameters.

These are visible in the staged diff. The unmerged test path remains untouched.

## SRS Parent capability gaps: no target caller and no BE route

Paths below are those stated by the adopted SRS. “No target caller” means no matching HTTP operation in the Parent client; legacy substitute calls are called out where relevant. No route is proposed for capabilities whose path is unspecified.

| SRS capability / stated route | Mobile caller | Dev / M2 BE route | Gap |
|---|---|---|---|
| Attach validated artwork: POST /v1/story-runs/{id}/assets (§21.2) | No matching attach call. Client instead sends base64 to legacy drawing-understandings route. | Absent in inspected dev/M2 Parent routers. | GAP; legacy analysis call is not the SRS upload/attach contract. |
| Text/audio idea: POST /v1/story-runs/{id}/idea (§21.2) | transcribeAudio returns unavailable; no HTTP caller. | Absent. | GAP |
| Job polling: GET /v1/jobs/{job_id} (§9.6/21.2) | No job-by-ID call; StoryRun reads only expose embedded job state. | Absent. | GAP |
| Video admission: POST /v1/story-runs/{id}/video-generations (§21.2) | No caller. | Absent. | GAP |
| Mark video unsuitable: POST /v1/story-runs/{id}/video-unsuitable (§21.2) | No caller. | Absent. | GAP |
| Complete run: POST /v1/story-runs/{id}/complete (§21.2) | No caller. | Absent. | GAP |
| Delete completed run: DELETE /v1/story-runs/{id} (§21.2) | deleteStoryRun returns unavailable; no HTTP call. | Absent. | GAP |
| Playback authorization: POST /v1/story-runs/{id}/playback-token (§9.6/21.2) | No caller. | Absent. | GAP |
| Parent quota summary: GET /v1/video-quota (§9.6/21.2; §23.5) | getVideoQuota returns unavailable. | Absent. | GAP |
| Notifications inbox: GET /v1/notifications (§9.6/21.2) | Notification methods return unavailable; no HTTP call. | Absent. | GAP |
| Push registration/revoke: POST /v1/notifications/push-endpoints, DELETE /v1/notifications/push-endpoints/{endpoint_id} (§9.6/21.2) | No caller. | Absent. | GAP |
| StoryRun history screen (§21.5) | listStoryRuns returns unavailable. | No list route found. | GAP, but SRS does not define the list method/path. Do not invent one. |
| Parent lesson delivery history and feedback (FR-PL-21/22) | History/feedback methods return unavailable; no HTTP calls. | No matching routes in inspected BE sources. | GAP; exact API paths are not stated in SRS. |
| Parent child-profile sharing/revoke (FR-PL-07) | Share methods return unavailable; no HTTP calls. | No child-profile share route in inspected BE sources. Lesson group invitations are separate. | GAP; exact API paths are not stated in SRS. |
| Quota purchase: POST /v1/video-quota/purchases (§9.6/21.2; Q193) | No caller. | Absent. | EXCLUDED-PAYMENT — SRS gates purchase on owner decisions. |

The M2 POST /v1/story-runs/{run_id}/cancel route exists, but the mobile adapter returns unavailable and the operation is not among the eight allowed. It is not a “no BE route” gap. Context confirmation is also present in BE code but was not found as a Parent HTTP call.

## Demo and fixture surfaces, kept separate

src/demo/api.ts is a legacy/demo workflow client used by DemoWorkflowScreen, AppContext, and Flow2Screens. It uses WorkflowResult, a custom error parser, synthetic actor/session-version metadata, and optional auth. Its calls are not M2-allowed Parent operations; per-route DTO/status parity was NOT VERIFIED in this Parent product audit.

| Methods and paths declared by DemoApi | Source lines |
|---|---|
| POST /v1/sessions | demo/api.ts:290 |
| POST /v1/sessions/{session_id}/media/image | :318–348 |
| POST /v1/sessions/{session_id}/media/audio | :363–374 |
| POST /v1/sessions/{session_id}/understanding | :380–415 (run, requery, select subject) |
| GET /v1/sessions/{session_id}/understanding/progress | :417–426 |
| POST /v1/sessions/{session_id}/gate-a/confirm | :429–450 |
| POST /v1/sessions/{session_id}/p1/context-options/finalize | :458–481 |
| GET /v1/sessions/{session_id}/p1/context-options | :458–491 |
| GET /v1/sessions/{session_id}/p1/context-candidates | :494–503 |
| POST /v1/sessions/{session_id}/p1/activity-suggestions | :506–532 |
| POST /v1/sessions/{session_id}/p1/activity-suggestions/rank | :536–563 |
| POST /v1/profile/preferences/classify | :566–583 |
| PUT /v1/sessions/{session_id}/p1-context | :587–596 |
| POST /v1/sessions/{session_id}/p1-filter | :599–603 |
| POST /v1/sessions/{session_id}/experience/prepare | :606–610 |
| POST /v1/sessions/{session_id}/gate-b/approve | :613–618 |
| POST /v1/sessions/{session_id}/renderer/launch | :621–625 |
| POST /v1/sessions/{session_id}/handoff | :628–632 |
| GET /v1/sessions/{session_id}/story-video-jobs | :635–640 |
| POST /v1/sessions/{session_id}/media/retake | :643–647 |
| POST /v1/sessions/{session_id}/feedback | :650–667 |
| GET /v1/sessions/{session_id}/gallery | :670–680 |
| GET /v1/sessions/{session_id} | :682–692 |

src/services/api.ts is a dormant mock facade, not an emitted product-call surface: it has no internal call sites and API_CONFIG.USE_MOCK_API is true. Its eight declared fallback endpoints are GET /api/children, POST /api/drawings/upload, POST /api/voice/transcribe, GET /api/story/scene-understanding, GET /api/story/video, GET /api/activities/recommend, GET /api/activities/{id}, and POST /api/activities/{id}/feedback. api.types.ts supplies these mock DTOs.

ParentAuth also calls Firebase Authentication provider endpoints (accounts:signInWithPassword, accounts:signInWithIdp, accounts:sendOobCode, accounts:update, and Secure Token refresh). These are provider calls, not BE routes; no keys or live credentials were inspected.

## Summary and verification limits

- Exact paths for the eight M2-allowed operations are used only by the profile list/detail and StoryRun active/detail reads; the detail/profile response DTOs still need alignment. The create/patch/delete profile and create StoryRun methods use non-M2 paths and omit required idempotency keys.
- Consent-policy and data-authorization calls have no matching BE route. Activity suggestions also has a FE call with no matching route or SRS path contract.
- Lesson Library paths and mutation idempotency headers match, but FE list callers do not continue pages and BE errors do not use the §9.8 envelope.
- SRS capabilities still lacking both target callers and BE routes are listed above; quota purchase is excluded pending Q193.
- No HTTP calls, tests, Bruno checks, builds, app starts, database, or Docker operations were performed. Runtime route mounting, actual response bodies, unspecified error statuses, modified BE service effects, Firebase provider responses, and request emission for declaration-only methods remain NOT VERIFIED.
