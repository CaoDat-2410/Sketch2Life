# L5 Authenticated Run Readiness — Draft 1

Status: DRAFT / PREPARATION ONLY. This note does not decide O-BRU-AUTH, issue tokens, approve a seed, or authorize an authenticated run.

## Authority and evidence boundary

Use the canonical FEAT-063 v2.7-draft SRS selected by `docs/context/SRS_AUTHORITY.md` (701,810 bytes; SHA-256 `443A3CA37272D2FE96127564BAF400461F394E098724A6BD999D723A4E504021`). It remains unsigned. The requests below reflect current router contracts. A source route does not by itself make an SRS target path final, a provider safe to call, or a runtime verified.

Source composition is in `backend/src/sketch2life/interfaces/http/router_composition.py`: the combined profile mounts Parent profiles, Parent StoryRuns, Parent AI, Teacher AI and auth registration. The Parent StoryRun router is omitted when StoryRun-lite demo mode is enabled. The current local collection run must therefore use the combined profile with demo mode off.

## Preconditions before any authenticated run

1. Resolve the SD-5 prerequisite in D-066-72 (SEED-1 section, `features/FEAT-066-fe-ui-srs-full-review/DECISIONS.md:544`; SD-5 at `features/FEAT-066-fe-ui-srs-full-review/DECISIONS.md:563`): adult sign-in is deferred until before the FE slices, FE-screen acceptance is deferred with it, and the seeded issuer depends on the selected sign-in. Before an authenticated run, the chosen adult sign-in and identity-verifier path must be implemented and configured for the isolated local environment. A placeholder bearer currently cannot authenticate.
2. The owner must resolve O-BRU-AUTH: the permitted source and lifecycle for test tokens, the issuing authority, allowed roles, and safe storage/rotation. This task does not create or supply tokens.
3. The owner must identify an approved seed stage using synthetic-only data and document which disposable database it targets. No seed or real child data is included here.
4. That seed must provide distinct active principals for Platform Admin, Manager assignments, assigned/unassigned/no-organization Teachers, and Parent P1/P2/P3 where each scenario needs them. Organization, class, profile, run and revision identifiers must come from those fixtures or from preceding responses.
5. Provider-backed routes require a separate explicit local-provider gate and owner-approved fixtures. Requests 153–159 were removed from the coordinating session's run copy and were not sent or parsed by the Bruno CLI; CLI parsing is NOT VERIFIED. Do not treat a valid bearer as permission to call an identity provider or model provider.
6. Confirm the application worktree, mounted profile, loopback base URL, database identity, request collection pin and active loopback guard before a future run. No configured or shared environment is a valid target for this readiness note.

## Provisional role variables and candidate request paths

The following names come from `requests/l5/README.md`. They are names only; no values are recorded. Folder paths are relative to the Bruno collection root and identify candidate requests only. Run by request, not by folder.

| Role | Provisional variables | Candidate request paths for later role-scoped review |
|---|---|---|
| Platform Admin | `TOKEN_PLATFORM_ADMIN` | `requests/portal-auth` (request 141, current-account read only), `requests/platform-admin-accounts`, `requests/platform-admin-moderation` |
| School Manager | `TOKEN_MANAGER_ORG_A`, `TOKEN_MANAGER_ORG_B` | `requests/portal-auth`, `requests/organizations-classes`, `requests/school-manager-sharing`, `requests/parent-group-membership`, `requests/records-gallery`, `requests/sessions-devices`, `requests/session-artifacts` |
| Teacher | `TOKEN_TEACHER_ASSIGNED`, `TOKEN_TEACHER_UNASSIGNED`, `TOKEN_TEACHER_NO_ORG` | `requests/portal-auth`, `requests/organizations-classes`, `requests/teacher-lesson-authoring`, `requests/staff-lesson-library`, `requests/lesson-library-upload-sessions`, `requests/collaborative-canvas`, `requests/sessions-devices`, `requests/session-artifacts`, `requests/records-gallery` |
| Parent | `TOKEN_PARENT_P1`, `TOKEN_PARENT_P2`, `TOKEN_PARENT_P3` | `requests/portal-auth`, `requests/parent-mobile-read-routes`, `requests/l5/parent-mobile-lifecycle`, `requests/parent-lesson-library` |

The paths above are only a way to find candidate requests; there is no folder-level authorization. Run by request, not by folder. These paths are excluded from any role-scoped run until separately authorized: `requests/l5/parent-ai`, `requests/l5/teacher-ai`, and `requests/l5/portal-auth`. The last is distinct from `requests/portal-auth`, which contains request 141; request 153 is the separate public registration route. SD-5 and owner-approved seeds must establish the actual role/scope for each request before using these variables.

## Safe order and revision dependencies

For an eventual authenticated rehearsal, perform read-only discovery and health checks first. Then create only synthetic test resources, read back their server-issued IDs/revisions, perform updates or confirmations, read back the resulting state, and place deletion/cleanup commands last. Do not run an entire folder blindly when it mixes reads and writes.

For the newly added Parent requests:

1. Read Parent profiles and the active/specific StoryRun with requests 137–140 first. Record IDs and current revisions only in the approved local test notes.
2. If testing profile creation, run 147 against the disposable database, read the created profile, then run 148 with the returned `revision_no` as `expected_revision`. Request 149 is optional cleanup and runs last for that synthetic profile.
3. Context confirmation 151 requires a seeded/current run and the `context_revision` plus `context_snapshot_sha256` from its current response. Script confirmation 152 requires the generated story revision and its `story_sha256`; do not send either command with guessed revisions or hashes.
4. Run deletion 150 is cleanup only, after the run is in an SRS-eligible terminal state. The canonical SRS §21.2 line 1674 limits DELETE to `COMPLETED`, `FAILED` or `ABANDONED`; it returns 202. The current route does not accept `If-Match` or a body for DELETE.
5. None of the 13 new requests uses an `If-Match` header. Revision checks are JSON body fields for 148, 151 and 152. Request 156 also needs the current `understanding_revision` from the StoryRun response. These requests carry `Idempotency-Key` only where the router declares/parses it.
6. Registration and all six AI requests (153–159) remain excluded from the authenticated collection run and from every role-scoped run until separately authorized. They were not parsed by the Bruno CLI; parsing is NOT VERIFIED. If separately authorized in the future, first review their provider/identity effects and test data with the owner.

## Expected results once identity and fixtures work

These are source-level expectations, not observed authenticated results.

| Request class | Expected success and relevant failures |
|---|---|
| Parent profile create (147) | Router returns 201 with a profile reference and revision. Source declares 400 invalid request, 401, 403, 404, 409 conflict and 503 dependency errors. SRS §21.2 line 1647 requires 201 and no organization ID. |
| Parent profile update (148) | Router returns 200 with the current profile projection/revision. A stale `expected_revision` conflicts; malformed fields use 400. SRS §21.2 line 1648 requires expected revision and immutable revision creation. |
| Parent profile deletion (149) | Router returns 202 with `DELETE_PENDING`; errors use the Parent profile envelope. SRS lifecycle semantics remain subject to its current deletion sections. |
| Parent StoryRun deletion (150) | Router returns 202 with a lifecycle envelope for an eligible terminal run. The source requires one 1–128 visible-ASCII idempotency key via its parser; invalid/missing keys are 400. SRS §21.2 line 1674 defines the eligible states and 202 response. |
| Context/script confirmation (151–152) | Router returns 200 on accepted confirmation. Missing/invalid key or malformed body is 400; stale context/story revision is 409; auth/scope and unavailable-service errors use the route error envelope. SRS §21.2 lines 1667 and 1669 require snapshot/version confirmation and exact script/storyboard revision/hash. |
| Parent registration (153) | Public router returns 201 `IDENTITY_CREATED`; source also declares 409 `ACCOUNT_SETUP_UNAVAILABLE`, 422 invalid request, 429 `RATE_LIMITED`, and 503 `IDENTITY_PROVIDER_UNAVAILABLE` or account setup unavailable. Never include this request in a configured-environment run. SRS §29.2 line 2272 leaves registration and role UX to be defined. |
| Parent AI (154–156) | Parent AI router requires active Parent identity and `ai_provider=modal_dev` in local/test. Request 154 requires a StoryRun without artwork already attached; if artwork is already attached it returns 409 `PARENT_STORY_ARTWORK_ALREADY_ATTACHED`. Missing scanner or storage returns 503 `PARENT_ARTWORK_STORAGE_UNAVAILABLE`; an unavailable scanner returns 503 `PARENT_ARTWORK_SCAN_UNAVAILABLE`. Invalid base64 bytes return 422 `DRAWING_IMAGE_INVALID`, and disallowed image signatures return 415 `DRAWING_IMAGE_TYPE_NOT_ALLOWED` (`backend/src/sketch2life/interfaces/http/routers/parent_ai.py:254-278`). With AI disabled it returns 503 `MODAL_AI_NOT_ENABLED`; provider/output failures may return 502/504. Request 156 requires `Idempotency-Key` length 1–200 and current understanding revision. Exact API path is current-source evidence; SRS §9.6 line 800 leaves Parent drawing-guide route/version TBD. |
| Teacher AI (157–159) | Teacher AI router requires an active Teacher assignment for the organization and local/test `modal_dev`. With AI disabled it returns 503 `MODAL_AI_NOT_ENABLED`; provider/output failures may return 502/504. These routes are source contracts; do not infer an SRS-stable path from them. |

Bearer-authenticated adult routes depend on a working identity verifier. The B2 and follow-up run records show identity-provider unavailability for the placeholder bearer; see `evidence/notes/B2_BRUNO_FULL_COLLECTION_RUN_20261119.md` and `evidence/notes/BRUNO_POST_B2_FOLLOWUP_RUN_20261119.md`. This is a blocked prerequisite, not proof of authenticated success or failure of the contract.

## Owner questions still open

- O-BRU-AUTH: who/what issues local test tokens, which token type and roles are permitted, how tokens are stored/rotated, and who approves the process?
- Which SD-5 milestone and isolated local configuration count as ready for an authenticated run?
- Which seed stage supplies the required synthetic principals and Parent profile/StoryRun revisions, and how is its target database pinned without recording a connection string?
- SRS §21.4 (line 1697) requires idempotency keys for state-changing commands, but the current routers for requests 154, 155 and 157–159 accept no key while the Bruno requests follow those routers (`backend/src/sketch2life/interfaces/http/routers/parent_ai.py:182-226, 232-250`; `teacher_ai.py:125-131, 178-184, 256-262`). Should BE add key handling, or should the SRS define an exception? This remains OPEN; no request-side key is invented.
- Will the owner separately authorize registration or AI-provider requests for any future local test, and what provider/offline constraints apply?
- Which request folders and individual scenarios are approved for each role once SD-5 and seeds exist?

Until these questions are answered and the prerequisites are evidenced, authenticated runs remain NOT READY. This note makes no decision for the owner.
