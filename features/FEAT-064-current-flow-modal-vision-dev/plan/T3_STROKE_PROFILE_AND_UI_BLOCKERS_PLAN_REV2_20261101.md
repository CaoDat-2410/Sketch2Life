# T3 REV2 — Stroke profile and Child/Teacher UI blockers

- **Status:** DECISIONS RECORDED; CODE NOT APPROVED.
- **Feature:** FEAT-064 — current-flow Modal Vision dev pilot.
- **Parent plan:** `plan/PLAN.md` revision 6, SHA-256 `CD7B3236A55E280D4722166C73AF462835DEC8503BCE882CE0CFF9D5601F9665`.
- **Source freeze:** FEAT-064 T0 contract freeze `476D48398A6F5A6834D42BE9408BBF445A02200005BDFC59CE8FE4467491041B`; execution manifest `3E5BC377117092D0872C97B922B95C3F464BD1C2F12ADC49D5604FFF83E51605`; guard dispositions `B02543FF2591BF4EF3B422E08E64865CF407299B6CE3FBBC88C8863BBD268F69`.
- **Decision authority:** owner decisions B1–B8 in the direct instruction on 2026-11-01. These settle product values for planning only. They do not authorize implementation.

## 1. Recorded decisions

| ID | Owner decision | T3 planning consequence |
|---|---|---|
| B1 — Canvas profile | Fixed 1:1 canvas; exported image is 1024×1024, RGB, white background; stroke width is a pure ratio independent of an assumed 400-unit logical canvas; pilot UI sets `aspectRatio: 1`. | T3 uses a square normalized coordinate surface. T4/T5 may later export accepted server operations; this decision does not make T3 an exporter. |
| B2 — Widths | Existing UI choices 5/9/14 map to ratios 5/400 = 0.0125, 9/400 = 0.0225 and 14/400 = 0.035. UI currently uses absolute dp, so it must render `ratio × measured canvas width`; review AC20 again. Wire payload carries only integer token 5, 9 or 14. | Implementation must keep wire tokens and rendering ratios distinct and test compact/wide layouts. |
| B3 — Degenerate strokes | A one-point stroke produces no dot. Client drops strokes with fewer than two points; server rejects strokes with fewer than two points. | No optimistic one-point mark can become an accepted operation. |
| B4 — Profile binding | Server owns `CanvasOperationProfileV1`; the profile key is server-only, including `pilot_run_ref`. Apply it from current `SYNTHETIC_DEV` eligibility at append time, not from client/session configuration; persist profile id with each accepted operation. | Existing client-supplied configuration cannot grant or select the profile. Retention may remove configuration, so operation provenance is stored with each operation. |
| B5 — Child canvas read | Choose option A: a separate read-only route for `active` and `paused`; return only the current canvas for the exact group when every current member and every past contributor passes current eligibility. Define the response for paused sessions without a turn. | Separate task before or parallel with T3. It does not weaken the append/write turn guard. |
| B6 — Teacher pilot roster | Choose option B: a new session-scoped route for lobby candidates. Filter proof by exact `proof.session_id`, validity window, non-revocation, pilot enabled and `local`/`test` environment; do not filter by `pilot_run_ref`. Return only `child_id` and `display_name`. | Separate task before or parallel with T3. It must support pre-admission candidate selection without using the class-wide legal-only profile list. |
| B7 — Dependency | B5 and B6 are separate tasks scheduled before or in parallel with T3. T3 acceptance includes tests and offline drawing. | T3 must not claim a complete Child/Teacher flow until these blockers have outcomes. |
| B8 — Files | Exact T3 implementation files are not approved. `be1_sessions.py` and `be1_common.py` may be needed because of B4/B5/B6. | A future implementation approval must pin exact files and tests; this plan assigns no writer or reviewer. |

## 2. Current implementation facts and blockers

### Child read/reconnect

The Child client obtains authoritative canvas state through `/reconnect` (`apps/child-ui/src/services/sessionClient.ts:95-99`). The current BE1 reconnect route uses `get_verified_device` and the legal-only `_require_group_consent` (`backend/src/sketch2life/interfaces/http/routers/be1_canvas.py:648-666`); the T1 synthetic typed eligibility helper is used for the append path, not reconnect. The current device verifier also depends on active session/group/turn (`backend/src/sketch2life/interfaces/http/be1_runtime.py:152-202`). Therefore the selected B5 route is a new read-only path; it must not be described as an existing synthetic-capable reconnect.

### Teacher lobby candidate list

The Teacher lobby calls the class profile-list endpoint before admission (`apps/teacher-ui/src/services/profileService.ts:10-17`). That endpoint checks `consent_is_effective` for every active profile and returns `409 CONSENT_NOT_EFFECTIVE` if any row fails (`backend/src/sketch2life/interfaces/http/routers/be1_registry.py:258-291`). Synthetic profiles intentionally have no consent references (`backend/src/sketch2life/infrastructure/persistence/be1_models.py:98-138`), while the consent table CHECK allows only `pending`/`revoked` and the existing lookup searches for `effective` (`be1_models.py:213-232`; `be1_common.py:234-255`). Do not fix this by making synthetic consent effective. B6's session-scoped roster is the selected planning direction.

### Session configuration is not an eligibility/profile authority

`create_session` accepts caller-supplied configuration keys except reserved `purpose_ref` and `join_code_sha256`, then stores them (`backend/src/sketch2life/interfaces/http/routers/be1_sessions.py:190-220`). No current session operation binds a trusted synthetic profile merely because a profile identifier or pilot profile key appears in this generic configuration. Under B4, the server must bind `CanvasOperationProfileV1` from the current eligibility decision on append; configuration values supplied by the Teacher cannot select or override it.

## 3. T3 scope, sequencing, and open implementation contract

T3 remains the bounded stroke DTO/profile and square Child drawing surface. It does not export an image, create an admission receipt, call Vision, change provider wiring, or make a Modal request. T4 owns authoritative operation export pinned to canvas epoch/revision; T5 owns rendering/admission. B5 and B6 are separate route tasks, prioritized before or parallel to T3 as recorded in B7.

Known source boundaries remain proposals only: the request schema under `backend/src/sketch2life/contracts/schemas/be1_runtime.py`, server validation at `backend/src/sketch2life/interfaces/http/routers/be1_canvas.py` (and possibly a small domain validator), and Child UI in `apps/child-ui/app/index.tsx` plus its session client. Existing test starting points are the BE1 session HTTP contract and Child UI canvas/session-client tests. B8 means this list is not an approved code allowlist.

Still OPEN for a future code approval:

1. Maximum accepted point count and coordinate precision must fit the existing 32 KiB payload ceiling and retain reliable geometry.
2. Client behavior after a server rejection must be explicit (for example, discard/reconcile the optimistic operation); never claim the operation was accepted.
3. No T3 migration is currently identified: B1–B4 require per-operation server profile provenance, but physical persistence placement must be determined against the approved T3 file/schema scope. Do not pre-decide or apply a migration in this plan.
4. B5 must define paused read response without a current turn, group membership changes, and how every current member/past contributor eligibility is evaluated.
5. B6 must specify the minimum session-scoped lobby lookup behavior for a candidate before membership exists; response fields remain limited to `child_id` and `display_name`.

## 4. Proposed acceptance for a later, separately approved T3 implementation

- White, strokes-only, square 1:1 pilot surface; no gallery artwork or suggestion overlay.
- Normalized finite coordinates and widths encoded by integer tokens 5/9/14; rendering uses the corresponding width ratio times measured canvas width.
- Only the five existing palette colors and `kind='stroke'`; unsupported values, fewer than two points and malformed/oversized payloads reject before persistence.
- Server assigns `CanvasOperationProfileV1` using current synthetic eligibility and records the profile id with each accepted operation. Client input cannot choose/downgrade it.
- Existing scope, turn, epoch, expected revision, idempotency, append-only and typed eligibility guards remain in force.
- Offline contract/UI tests cover acceptance, rejection, compact/wide layout, two-point minimum, serialization tokens, optimistic rejection behavior and the B5/B6 route outcomes once those tasks are separately approved.
- AC20 visual review remains required. No code, visual asset, runtime route, Modal/GPU call or end-to-end flow is approved by this document.

## 5. Explicit non-approval

This revision records owner decisions and verified blockers only. It does not approve T3 code, any route, DTO or schema migration, the B5/B6 implementations, a visual asset, production provider wiring, Modal/GPU execution, use of real child data, or a production-readiness claim. A later approval must include exact paths, tests, ownership, migration decision if applicable, and operational constraints.
