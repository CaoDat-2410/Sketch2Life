# T3 — BE1 canvas operation profile implementation plan

- Status: prepared for bounded G1 execution; implementation approval is appended separately and pins this file's SHA-256.
- Feature: FEAT-064 current-flow Modal Vision development pilot.
- Owner directive: `CODEX_GOAL_PILOT_T2C_TO_T12_20261101.md`, 2026-11-01, §D G1 and §E.
- Baselines: `PLAN.md` revision 6 (`CD7B3236A55E280D4722166C73AF462835DEC8503BCE882CE0CFF9D5601F9665`); T0 contract freeze (`476D48398A6F5A6834D42BE9408BBF445A02200005BDFC59CE8FE4467491041B`); T0 manifest (`3E5BC377117092D0872C97B922B95C3F464BD1C2F12ADC49D5604FFF83E51605`); owner T3 decisions in `OWNER_DECISIONS_T2B_T3_20261101.md` (`53F588785258FDBC43ED53FE9A45A72D58209916F7E63627CBFE1C7E2136AB64`).

## Scope and layer order

Implement the BE1 server contract for a versioned `CanvasOperationProfileV1` on new pilot-enabled local/test sessions and validate accepted stroke operations before persistence. Preserve independent typed eligibility, identity, current-turn, epoch, revision, idempotency, and append-only guards. The active pilot profile is attached by the server at session creation when both `env in {local,test}` and `synthetic_pilot_enabled` are true. The profile key is reserved against caller configuration. This is a profile selector only; it grants no eligibility and does not replace the typed proof/legal gate. Previously created sessions without the key keep their legacy payload interpretation.

Profile: 1:1 normalized white surface; logical geometry 400 × 400; strokes-only and append-only; colors `#FFD21F`, `#FF596C`, `#1685F8`, `#31C978`, `#9250E8`; width tokens 5/9/14 map to ratios 0.0125/0.0225/0.035; at least 2 and at most 512 points; finite normalized coordinates in [0,1] with at most 6 decimal places; `operation_payload` remains subject to the existing 32 KiB serialized-size cap. One-point strokes are rejected, never stored as dots. The future 1024 × 1024 RGB export belongs to T4/T5 and is not implemented here.

Layers: **L1** pure domain profile and request/response contract first; run unit tests, Ruff, strict mypy on changed/new L1 files, and architecture validation before moving upward. **L5** session binding and HTTP acceptance/rejection next; test contract and PostgreSQL persistence behavior. L3 persistence schema/migration is not touched: `ClassroomSessionModel.configuration` and `CoreCanvasOperationModel.operation_payload` already provide JSON storage.

## Exact allowlist

- `backend/src/sketch2life/domain/core_foundation.py`
- `backend/src/sketch2life/contracts/schemas/be1_runtime.py`
- `backend/src/sketch2life/interfaces/http/routers/be1_sessions.py`
- `backend/src/sketch2life/interfaces/http/routers/be1_canvas.py`
- `backend/tests/unit/test_canvas_operation_profile.py` (new, listed and pinned in this plan)
- `backend/tests/integration/test_be1_synthetic_pilot_postgres.py`
- `features/FEAT-064-current-flow-modal-vision-dev/plan/T3_BE1_CANVAS_PROFILE_IMPLEMENTATION_PLAN_20261101.md`
- `features/FEAT-064-current-flow-modal-vision-dev/approvals/TASK_APPROVAL.md` (append only)
- `features/FEAT-064-current-flow-modal-vision-dev/evidence/T3_CANVAS_PROFILE_IMPLEMENTATION_REPORT_20261101.md`
- `features/FEAT-064-current-flow-modal-vision-dev/status/PILOT_GOAL_LEDGER_20261101.md` (G1 progress only)

No other path is permitted by this task plan.

## Test matrix

1. L1 unit: exact profile constants; accepted two-point/multi-point examples; each palette and width; reject one point, empty/excessive points, extra fields, wrong operation kind, unknown palette/width, bool/non-numeric, NaN/infinity, out-of-range coordinates, and precision over six decimal places.
2. L5 contract: profile is present only on sessions created under explicit local/test pilot settings; caller cannot supply/override reserved profile keys; client must echo the exact version; mismatch, missing version, downgrade, or invalid stroke rejects before persistence; legacy sessions without a server profile retain the old generic payload behavior and reject client opt-in.
3. PostgreSQL acceptance: update the existing synthetic-pilot stroke case to send the contract payload, assert the server profile in session configuration, and assert stored accepted payload has the server profile id. Assert invalid profile input leaves operation count and revision unchanged.
4. Regression: selected 5 CI test files plus the T1 tests and the updated synthetic-pilot PostgreSQL module; preserve all existing legal and synthetic eligibility checks.

Red tests are written/run before implementation. Report actual red and green results. Run Ruff with `--config backend/pyproject.toml`, strict mypy only on changed/new files (report new errors only), the three repository validators, and `git diff --check`. No provider or UI test.

## UI contract (implementation deferred by owner)

The client reads `configuration.canvas_operation_profile.version` from the session response and echoes `profile_version` in each append request. Example request:

```json
{
  "operation_id": "synthetic-op-001",
  "turn_id": "synthetic-turn-001",
  "document_epoch": 1,
  "expected_revision": 1,
  "profile_version": "CanvasOperationProfileV1",
  "operation_payload": {
    "kind": "stroke",
    "points": [{"x": 0.1, "y": 0.2}, {"x": 0.3, "y": 0.4}],
    "color": "#FFD21F",
    "size": 5
  }
}
```

On success the server returns `Be1CanvasOperationReceiptV1` with `status`, `canvas_id`, `resulting_revision`, and `operation_id`. `409 CANVAS_PROFILE_MISMATCH` means the server session profile and echoed version differ; `422 CANVAS_PROFILE_INVALID` means the stroke is outside the pinned profile. Rejection means no operation was accepted: the UI must mark/remove that queued stroke, show a recoverable error, reconcile from the server revision, and must not leave it spinning or retry it blindly. Request payload stays within 32 KiB. The current child UI is not changed; visual AC20 is deferred and not run.

## Exclusions and risks

Exclude image rendering/export/admission, migration/schema changes, checkpoint semantics, provider/BE2 wiring, Modal/GPU, production configuration, and `apps/**`. A session created while the explicit local/test synthetic-pilot flag is enabled receives the versioned stroke rules even when its later eligibility is legal; eligibility remains independently enforced. Session profile configuration has no update path in this scope; any later profile change needs a new version/task. Old sessions are not backfilled or reinterpreted.

Primary risk: existing callers in a test process that explicitly enables synthetic pilot may need to echo the profile version on new sessions. Mitigation: regression-test legacy unprofiled sessions separately and update only the existing approved synthetic-pilot integration case.
