# T3 — Stroke profile and Child/Teacher UI blockers

- **Status:** DRAFT / AWAITING_APPROVAL. This file is a plan only; it authorizes no code.
- **Feature:** FEAT-064 — current-flow Modal Vision dev pilot.
- **Plan baseline:** `plan/PLAN.md` revision 6, SHA-256 `CD7B3236A55E280D4722166C73AF462835DEC8503BCE882CE0CFF9D5601F9665`.
- **T0 source pins:** `evidence/T0_CONTRACT_FREEZE_20261031.md` `476D48398A6F5A6834D42BE9408BBF445A02200005BDFC59CE8FE4467491041B`; `evidence/T0_EXECUTION_MANIFEST_20261031.csv` `3E5BC377117092D0872C97B922B95C3F464BD1C2F12ADC49D5604FFF83E51605`; `evidence/T0_GUARD_DISPOSITIONS_20261031.csv` `B02543FF2591BF4EF3B422E08E64865CF407299B6CE3FBBC88C8863BBD268F69`.
- **Execution:** no UI/backend code, tests, database, Alembic, Modal or GPU operation was performed for T3. T3 implementation requires its own approval with exact paths and frozen profile values.

## 1. Task placement and boundaries

`PLAN.md:90-91` defines T3 as “Stroke DTO/profile, geometry/width và canvas dev trắng tương ứng”, dependent on T0, parallelizable with T1 and selected T6/T7a work, with acceptance requiring strokes-only, matching logical viewport/aspect/width, rejection outside the profile, reuse of existing components/styles, and visual gate AC20. T4 follows T3 and is responsible for an authoritative export pinned to epoch/revision; T3 must not claim a PNG export, rendering receipt, admission receipt, or Vision request.

T0 manifest O01 assigns the BE1 wire schema/profile boundary to `backend/src/sketch2life/contracts/schemas/be1_runtime.py`; O05 assigns the canvas implementation boundary to `backend/src/sketch2life/interfaces/http/routers/be1_canvas.py`; O17 identifies Child UI in `apps/child-ui/app/index.tsx` and its session client. All manifest rows remain proposals with `approval_state=T0 documentation-only`; they do not assign a final writer or reviewer. The following list is therefore a **proposed T3 allowlist**, to be pinned by a separate approval:

| Boundary | Proposed paths | Existing test starting points | Notes |
|---|---|---|---|
| Request DTO and bounded operation payload | `backend/src/sketch2life/contracts/schemas/be1_runtime.py` | `backend/tests/contract/test_session_http_api.py` | Current request payload is a generic JSON dictionary with a 32 KiB bound (`be1_runtime.py:172-185`). |
| Server-side accepted-operation profile check | `backend/src/sketch2life/interfaces/http/routers/be1_canvas.py`; if domain validation is required, `backend/src/sketch2life/domain/core_foundation.py` | `backend/tests/contract/test_session_http_api.py` and a new focused BE1 contract test, if approved | Route currently persists a generic operation payload; `CanvasOperation` only carries operation/session/turn/canvas/revision identity (`core_foundation.py:263-270`). Owner must pin whether validation belongs in DTO, domain, route or a small combination. |
| Child pilot canvas geometry/presentation and client payload | `apps/child-ui/app/index.tsx`; `apps/child-ui/src/services/sessionClient.ts` | `apps/child-ui/src/__tests__/useDrawingCanvas.test.ts`, `sessionClient.test.ts`, `DrawScreen.test.tsx` | Reuse existing native views and styles; no new visual assets in the current proposal. |

No router composition, runtime, BE2 service, export/render, artifact storage, AI provider or production deployment change belongs in T3. The exact candidate paths and test files require owner approval; the plan does not claim they have been assigned.

## 2. Current stroke and canvas behavior

Verified source observations:

- `apps/child-ui/app/index.tsx:31-36` stores a stroke as points/color/size and defines the five current palette values: `#FFD21F`, `#FF596C`, `#1685F8`, `#31C978`, `#9250E8`.
- `apps/child-ui/app/index.tsx:280-291` normalizes pointer coordinates independently by the measured canvas width and height. The container is responsive and does not establish a fixed aspect ratio (`index.tsx:363`, styles at `:629`).
- `apps/child-ui/app/index.tsx:351-366` renders segments from `points.slice(1)`, uses the selected size and rounded rectangles, and overlays gallery artwork plus an optional suggestion. A one-point stroke has no visible segment. The collaborative eraser, undo and redo paths are not persisted as accepted operations (`index.tsx:281-289,320-351`).
- Brush choices are currently 5, 9 and 14 UI units (`apps/child-ui/app/index.tsx:421-423`). The client sends `{kind:'stroke', points, color, size}` to BE1 with turn, epoch and expected revision (`apps/child-ui/src/services/sessionClient.ts:185-207`).
- `CanvasOperationRequest.operation_payload` is currently `dict[str, Any]` with a 32 KiB JSON-size limit (`backend/src/sketch2life/contracts/schemas/be1_runtime.py:172-185`). The append route validates the authenticated turn and typed group eligibility, then passes the payload to the existing canvas storage path (`backend/src/sketch2life/interfaces/http/routers/be1_canvas.py:103-168`). The payload has no strict stroke-profile validation here.
- Current UI is not a source export: it renders gallery art/suggestion layers and local optimistic strokes. T4 must later export only accepted server operations at a consistent epoch/revision; T3 must not treat local optimistic strokes as authoritative.

## 3. Proposed T3 contract to freeze before implementation

The owner’s previously recorded direction is: fixed-ratio dev canvas, white background, strokes-only, append-only accepted operations, width normalized to canvas width, the existing five palette colors, and server rejection for values outside the chosen profile. T0 S4 gives a concrete proposal, but the exact aspect ratio, logical geometry, size mapping and one-point behavior remain values to pin in the T3 implementation approval; this plan does not turn a proposal into a decision.

| Contract area | Proposed acceptance | Open value / source |
|---|---|---|
| Profile identity | Versioned `CanvasOperationProfileV1`; unknown/missing profile for the pilot path is rejected. Bind it server-side or in an approved session contract; do not trust a client to downgrade the profile. | T0 S4; owner must choose where the profile is bound. |
| Presentation | Separate plain white drawing surface, strokes-only, fixed aspect ratio, using existing UI components/styles. No gallery background, suggestion overlay, annotations, or hidden history in the pilot surface. | Owner direction; T0 S4 proposes aspect 1:1 but requires owner confirmation before code. |
| Coordinates | Finite normalized `x`/`y` in `[0,1]`; reject NaN/infinity, wrong types, out-of-range values, unsupported point counts and oversized payloads. No server-side clamping. | T0 S4; exact point-count ceiling must be pinned against the existing 32 KiB request limit. |
| Color and operation kind | Only the five current palette colors and `kind='stroke'`; reject unknown kind/color. Accepted history is append-only and ordered by server revision. | Palette is directly present in `index.tsx:36`; eraser/undo/redo are not server-persisted in the connected path. |
| Width | Normalize UI sizes to the logical canvas width; reject widths outside the approved finite set/profile. | T0 S4 proposes logical width 400 with ratios `0.0125`, `0.0225`, `0.035` for UI sizes 5/9/14, yielding 12.8/23.04/35.84 px at 1024 px. The responsive UI does not prove a 400-unit logical width; owner must freeze this mapping or provide a sourced replacement. |
| Line geometry | Deterministic coordinates and caps/joins shared by UI and later renderer; accepted operation order must use BE1 revisions. | T0 S4 proposes rounded endpoints/joins and circular caps/joins. Current segment renderer does not define a raster parity contract. |
| Single-point stroke | Explicitly decide whether a one-point stroke is invisible or a dot; reject or render consistently in UI and later CPU renderer. | Current `points.slice(1)` renders no segment. T0 proposes no dot to match; owner approval required. |
| Canvas size / export | T3 pins logical geometry, not an export image. | T0 S4 proposes 1024×1024 RGB white PNG for later T5, under admission limits; keep rendering out of T3. |

### Server acceptance rules

1. Validate the entire operation payload before persistence; unsupported profile/version, kind, color, width, coordinate, geometry or size is rejected without storing a partial operation.
2. Preserve current identity, scope, current-turn, document-epoch, expected-revision, idempotency and typed-eligibility checks. T3 does not weaken the active turn requirement for writes.
3. Accepted operations remain append-only with the server-assigned resulting revision; client images, checkpoints, restore JSON and optimistic UI state are not evidence that an operation was accepted.
4. Keep existing non-pilot behavior compatible or explicitly reject only requests entering the new versioned pilot profile. Do not silently reinterpret historic arbitrary payloads.
5. The future exporter/renderer must use exactly the accepted server operation sequence. That is T4/T5, not acceptance for this task.

## 4. Child UI blocker: `/reconnect` is not synthetic-ready

`apps/child-ui/src/services/sessionClient.ts:95-99` calls `/organizations/{organization}/sessions/{session}/reconnect` when loading the complete canvas. `be1_canvas.py:648-666` authorizes it through `get_verified_device` and then `_require_group_consent`; the latter is the old legal-consent-only helper (`be1_canvas.py:212-269`). T1 added the separate typed synthetic eligibility helper for the append-stroke route only; the file explicitly says sync/checkpoint/restore/reconnect remain on the legal-only helper (`be1_canvas.py:271-284`). `get_verified_device` also currently requires an active session, an active group and an active Child turn (`be1_runtime.py:152-202`). Thus a synthetic Child may append under the selected pilot path but cannot fetch authoritative canvas state through the current reconnect path; pause/turn closure also prevents the existing guard from serving as a general read guard.

| Option | Change shape | Benefit | Cost / risk |
|---|---|---|---|
| A — Add a dedicated read-only reconnect authorization path | Resolve the Child’s own canvas under the exact device grant, membership, org/session/group and current typed proof; define active/paused semantics explicitly. Do not call the write guard or relax append/write checks. | Allows reload/reconnect of the same scoped pilot canvas while keeping legal behavior for other routes. | Requires a new read contract and scope-specific tests; the T2 own-status guard does not itself return a canvas/turn, so it cannot be assumed to be a drop-in. Pause, group membership and checkpoint disclosure must be specified. |
| B — Keep reconnect legal-only and limit the pilot UI to a no-reload session | No BE1 reconnect change. UI exposes a clear unavailable state and does not pretend a recovered canvas is current. | Smallest backend surface. | Refresh/crash loses local current state; cannot satisfy robust child flow or claim reliable server-authoritative preview. This is only a deliberately limited manual pilot, not a complete flow. |
| C — Add a separate session-scoped synthetic reconnect route | New route returns only the proof-authorized Child’s accepted operation projection, with exact current session/run/scope checks. | Keeps the existing legal route unchanged and makes the synthetic exception explicit. | Adds route/DTO/security surface and likely duplicates projection logic; requires separate route approval and response-disclosure review. |

**Owner decision required:** select A/B/C, specify whether reconnect is allowed while `paused`, whether only the exact current Child/group canvas is returned, and whether a separate endpoint is acceptable. No option is selected here.

## 5. Teacher UI blocker: class profile list returns 409 for synthetic rows

`apps/teacher-ui/src/services/profileService.ts:10-17` calls BE1 `GET /organizations/{org}/classes/{class}/profiles`; `SessionLobbyRuntime.tsx:41,105-126,297` uses that list to show candidate profiles for admission. `be1_registry.py:258-291` loads active class profiles and returns 409 `CONSENT_NOT_EFFECTIVE` if `consent_is_effective` is false for **any** row. A `SYNTHETIC_DEV` profile intentionally has null consent references (`be1_models.py:98-138`), so it cannot pass this legal-only class list. One synthetic row also makes the endpoint reject the whole class response. This behavior must not be “fixed” by making synthetic consent effective.

The existing session roster route (`be1_sessions.py:288-370`) is session-scoped and lists admitted memberships/groups/turns; it does not provide the pre-admission profile choices required by the lobby, so it is not by itself a replacement for `list_profiles`.

| Option | Change shape | Benefit | Cost / risk |
|---|---|---|---|
| A — Extend class list with typed synthetic handling | Existing route remains; provide session/run context and prove the exact synthetic profile is eligible before disclosure. Preserve REAL/legacy legal guard. | Reuses current Teacher API/UI integration. | Current route is class-scoped, not session-scoped; changing its contract and class-wide “any invalid row => 409” behavior risks disclosing profiles across sessions or changing legal behavior. Needs owner-approved typed filter semantics. |
| B — Add a session-scoped pilot profile/roster projection | New Teacher route binds to assigned org/class/session and only returns the allowed candidate/member projection after current proof and session checks. | Exact session/run scope; does not overload the legal-only profile endpoint. | New endpoint/schema/test and disclosure review; must decide whether a lobby profile can be listed before Child membership exists and what minimum fields are returned. |
| C — Use a bounded operator-seeded pilot mapping in Teacher UI | Keep production class list unchanged; pilot-specific Child identity is supplied through a reviewed local/test setup path. UI does not enumerate arbitrary synthetic profiles. | Avoids broad profile-list changes for a one-child synthetic pilot. | Requires a safe operator setup path and explicit UX; likely not representative of the normal Teacher lifecycle and should not be mistaken for production behavior. |

**Owner decision required:** choose A/B/C; if B or C, state how the lobby gets the exact synthetic Child identifier before admission and which profile fields the Teacher may see. Preserve the current legal-only class profile route unless an explicit decision changes it.

## 6. Dependency and sequence

1. T0 is complete as documentation; its concrete profile values are still proposals that must be pinned in the T3 implementation approval.
2. Resolve the profile values in §3 and the Child/Teacher choices in §§4–5. Resolve T2B’s missing BE1→BE2 provenance/revision facts separately; T3 must not create substitutes for that adapter.
3. Approve the exact T3 code allowlist, named owners/reviewers where required, DTO/profile binding, server reject behavior, and test matrix.
4. Implement T3 and validate client rendering/profile plus server operation rejection. Verify AC20 visual approval requirements. Do not claim complete AI flow.
5. T4 may begin after T3 acceptance; T4 creates the authoritative epoch/revision export. T5 then renders/admission-binds. T9/T10 are needed for request/status UI. T11 is the separate Teacher analysis-only panel.
6. T3 may not issue a provider request or use Modal. A future live call remains behind T12 and its own T13 approval.

## 7. Tests and acceptance criteria (proposed; not run)

### Backend

- Contract accept: exact frozen profile, each of the five colors, each allowed width, finite normalized boundary coordinates and valid stroke payload size.
- Contract reject: missing/unknown profile, unsupported operation kind/color/width, malformed/wrong-type/NaN/infinite/out-of-range coordinates, empty/excessive point list, malformed stroke and oversized payload; rejection must leave no accepted operation/revision.
- Preserve identity/scope/current turn, eligibility, idempotency, expected revision, epoch and append-only behavior; stale or duplicate requests must not create extra operations.
- Historical/unprofiled payload behavior is explicitly covered and not silently reinterpreted.

### Child UI

- Canvas remains the chosen aspect ratio at compact and wide viewport sizes, white and strokes-only; no artwork/overlay appears in the pilot surface.
- Palette and width selection serialize the pinned profile; render and payload geometry agree for horizontal, vertical, diagonal and boundary strokes.
- One-point, interrupted stroke and unsupported tool behavior match the frozen contract; only acknowledged operations are eligible for later export.
- Reconnect outcome follows the owner-selected option; failure or denial never claims server state was restored.

### Visual gate

AC20 (`plan/PLAN.md:154`) requires existing components/styles and no new asset in the current proposal; if a new visual asset becomes necessary, AGENTS §6 generated provenance → visual approval → approved/applied remains required. A synthetic screenshot can be test evidence but is not visual approval. Review at compact and wide layouts for clipping, scaling, point/line geometry, white background, hidden layers and status clarity.

### Completion

T3 completes only when the owner-approved path/profile is implemented, backend accepts/rejects exactly the frozen operation profile, Child UI and server geometry match, relevant backend/frontend checks are run, reconnect blocker has an explicit outcome, AC20 is reviewed, and evidence records exact code/test results. T3 does not complete T4/T5/T9/T10/T11/T12/T13 and does not establish Modal or production readiness.

## 8. Risks and open owner questions

1. **Profile freeze:** confirm aspect ratio and logical viewport. T0’s 1:1, 1024×1024 and logical width 400 are sourced proposals, not an approval to implement them.
2. **Width geometry:** confirm whether UI sizes 5/9/14 map to T0 ratios 0.0125/0.0225/0.035 or supply another width basis; ensure compact and wide layouts preserve equal logical width.
3. **Single-point stroke:** confirm no dot (matching current UI/T0 proposal) or specify an alternate behavior shared by UI and renderer.
4. **Profile binding:** confirm how profile version is bound so the Child cannot submit a downgrade and how historical operations without the profile are treated.
5. **Reconnect:** choose A/B/C in §4 and define pause/session/turn/group and projection scope.
6. **Teacher lobby:** choose A/B/C in §5 and define pre-admission lookup, session/run binding and minimum disclosed fields.
7. **Exact T3 allowlist/ownership:** approve the proposed paths/tests in §1 and resolve any required domain path before code; T0 manifest roles are proposals, not assignments or signatures.
8. **T2B blocker:** decide how BE1 facts gain authoritative age/consent/context/roster revisions and how synthetic facts represent the absence of legal consent; do not use T3 as an implicit resolution.

## 9. Not approved / not implied

This DRAFT does not approve any code, route, schema, migration, BE2 adapter, UI implementation, visual asset, database, MinIO, Modal/GPU call, production provider, use of real child data, or live pilot. It records current behavior and options for owner review only.
