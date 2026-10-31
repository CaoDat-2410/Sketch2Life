# T2 — Child canvas reconnect implementation plan

- Status: prepared for bounded G1 execution; implementation approval is appended separately and pins this file's SHA-256.
- Feature: FEAT-064 current-flow Modal Vision development pilot.
- Owner directive: `CODEX_GOAL_PILOT_T2C_TO_T12_20261101.md`, 2026-11-01, §D G1 and §E; this exact G1 behavior supersedes earlier reconnect alternatives in T3 draft plans.
- Baselines: `PLAN.md` revision 6 (`CD7B3236A55E280D4722166C73AF462835DEC8503BCE882CE0CFF9D5601F9665`); T0 manifest (`3E5BC377117092D0872C97B922B95C3F464BD1C2F12ADC49D5604FFF83E51605`); T2 plan (`T2_ACTOR_AUTHORITY_STATUS_READ_PLAN_20261031.md`).

## Scope and layers

Change the existing read-only `GET /organizations/{organization_id}/sessions/{session_id}/reconnect` to authorize through `get_verified_device_status`, then run the existing typed `_require_group_eligibility` for the admitted Child's current group canvas. Support session `active` and `paused`; do not require an active Child turn. Session `finished`, a missing/revoked grant, rotated/incorrect key, foreign path, non-admitted membership, missing group, or current ineligibility remains denied. Do not call or weaken the write guard. Preserve the existing response shape except `turn_id` becomes nullable when no current turn exists. A paused session with an active turn may return that exact Child turn; no active turn returns `null`.

Layers: **L1/L2** reuse the existing typed status-read and eligibility decisions without changing their policy; **L5** changes the route and response schema. There is no persistence or migration change. The status-read helper may record its existing denied-eligibility audit entry; successful reconnect does not mutate session/canvas state.

## Exact allowlist

- `backend/src/sketch2life/interfaces/http/be1_runtime.py` (only broaden `VerifiedDeviceStatusContext` documentation from status-only to own read authority; do not change its authorization logic)
- `backend/src/sketch2life/contracts/schemas/be1_runtime.py`
- `backend/src/sketch2life/interfaces/http/routers/be1_canvas.py`
- `backend/tests/contract/test_be1_synthetic_pilot.py`
- `backend/tests/integration/test_be1_synthetic_pilot_postgres.py`
- `features/FEAT-064-current-flow-modal-vision-dev/plan/T2_CHILD_CANVAS_RECONNECT_IMPLEMENTATION_PLAN_20261101.md`
- `features/FEAT-064-current-flow-modal-vision-dev/approvals/TASK_APPROVAL.md` (append only)
- `features/FEAT-064-current-flow-modal-vision-dev/evidence/T2_CHILD_CANVAS_RECONNECT_REPORT_20261101.md`
- `features/FEAT-064-current-flow-modal-vision-dev/status/PILOT_GOAL_LEDGER_20261101.md` (G1 progress only)

No other path is permitted by this task plan.

## Contract and test matrix

Request: existing GET route, optional `after_revision` (0..500000 or current documented range), headers `X-Be1-Grant` and `X-Be1-Device-Key`; no turn id is required in the request. Response `Be1CanvasReconnectV1` has `canvas_id`, nullable `turn_id`, current `document_epoch`, `current_revision`, optional checkpoint, and operations after the requested revision. With no aggregate revision yet, report revision 0; an empty new canvas uses epoch 1.

1. L5 contract test: route uses status guard and typed eligibility, does not call `get_verified_device` or `_require_group_consent`, while all other legal-only canvas sites remain unchanged.
2. PostgreSQL cases: admitted synthetic Child reconnects in active and paused states with no active turn; current-turn id is returned only when present; operations/checkpoint remain scoped to the membership's group canvas; foreign session, revoked grant/key, finished session, and revoked/expired proof are denied without canvas disclosure.
3. Regression: selected 5 CI files, T1 tests, and the existing synthetic-pilot PostgreSQL module. No new mock of authorization.

Write and run red tests before changing the route. Run Ruff with `--config backend/pyproject.toml`, strict mypy on changed/new files (new errors only), all three repository validators, and `git diff --check`.

## UI contract (implementation deferred by owner)

Call the same GET route with the admitted device headers and optional `after_revision`; call works in `active` or `paused` with no active turn. `turn_id` is either a string or `null`; the UI must not treat null as failure. `401 INVALID_DEVICE_CREDENTIAL`, `403 DEVICE_SCOPE_INACTIVE` / `DEVICE_MEMBERSHIP_INACTIVE`, `404` for missing scoped resources, and `409 CONSENT_NOT_EFFECTIVE` all mean do not show cached canvas as freshly restored and do not resend queued writes. Example synthetic response:

```json
{"contract":"Be1CanvasReconnectV1","canvas_id":"synthetic-group-001","turn_id":null,"document_epoch":1,"current_revision":0,"checkpoint":null,"operations":[]}
```

Visual AC20 is deferred and not run.

## Exclusions and risks

Exclude `get_verified_device` changes, write routes, new authorization modes, Teacher routes, UI, migration, artifact/rendering, provider/Modal, and any change to legal consent behavior. The canvas is the existing group-scoped canvas; the typed eligibility helper continues to check every current member and past contributor for that group before returning it. A caller cannot supply a group id in this endpoint; the group is derived from the authenticated admitted membership.
