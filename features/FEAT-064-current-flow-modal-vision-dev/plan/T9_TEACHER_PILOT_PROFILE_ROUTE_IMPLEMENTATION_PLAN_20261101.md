# T9 — Teacher session-scoped synthetic pilot profile route plan

- Status: prepared for bounded G1 execution; implementation approval is appended separately and pins this file's SHA-256.
- Feature: FEAT-064 current-flow Modal Vision development pilot.
- Owner directive: `CODEX_GOAL_PILOT_T2C_TO_T12_20261101.md`, 2026-11-01, §D G1 and §E; this exact route contract supersedes earlier T3 draft alternatives.
- Baselines: `PLAN.md` revision 6 (`CD7B3236A55E280D4722166C73AF462835DEC8503BCE882CE0CFF9D5601F9665`); T0 manifest (`3E5BC377117092D0872C97B922B95C3F464BD1C2F12ADC49D5604FFF83E51605`); owner T3 decisions (`53F588785258FDBC43ED53FE9A45A72D58209916F7E63627CBFE1C7E2136AB64`).

## Scope and layers

Add `GET /organizations/{organization_id}/sessions/{session_id}/pilot-profiles` to the existing BE1 registry router for a local/test pilot lobby. Require an assigned `teacher` or `school_admin`, session state `lobby`, `env in {local,test}`, and `synthetic_pilot_enabled=true`. Return only active `SYNTHETIC_DEV` profiles having at least one currently valid proof with exact organization/class/child/purpose/session scope, expected proof schema/data origin, `issued_at <= now < expires_at`, and `revoked_at is null`. Do not use `pilot_run_ref` as a trust boundary. Do not return age, consent fields, proof ids, run refs, evidence, or eligibility rationale. Keep the class-wide legal-only profile route unchanged.

Layers: **L1** typed response contract in the existing `be1_runtime.py` schema module; **L5** route and PostgreSQL contract cases. No migration or composition change.

## Exact allowlist

- `backend/src/sketch2life/contracts/schemas/be1_runtime.py`
- `backend/src/sketch2life/interfaces/http/routers/be1_registry.py`
- `backend/tests/integration/test_be1_synthetic_pilot_postgres.py`
- `backend/tests/contract/test_app_composition.py` (allow only the new exact route in the reviewed route-surface assertion)
- `features/FEAT-064-current-flow-modal-vision-dev/plan/T9_TEACHER_PILOT_PROFILE_ROUTE_IMPLEMENTATION_PLAN_20261101.md`
- `features/FEAT-064-current-flow-modal-vision-dev/approvals/TASK_APPROVAL.md` (append only)
- `features/FEAT-064-current-flow-modal-vision-dev/evidence/T9_TEACHER_PILOT_PROFILE_ROUTE_REPORT_20261101.md`
- `features/FEAT-064-current-flow-modal-vision-dev/status/PILOT_GOAL_LEDGER_20261101.md` (G1 progress only)

No other path is permitted by this task plan.

## Contract and test matrix

Success response is a typed `Be1PilotProfileListV1` envelope with `items: [{child_id, display_name}]` only. A lobby with no matching active valid profile returns an empty list. Reject disabled pilot/non-local environment and non-lobby session; assignment and route organization/session mismatch must not disclose candidates. The server query must bind `proof.session_id == session_id` and current proof validity, and must never use the session's `pilot_run_ref` to authorize disclosure.

1. L1 contract test: response model rejects extra profile fields.
2. PostgreSQL cases: exact valid synthetic profile appears with exactly the allowed fields; proof unbound to session, wrong session, expired, not-yet-valid, revoked, wrong origin/schema, inactive profile, wrong purpose/class/org are absent; flag disabled/non-local/non-lobby and unassigned adult are denied.
3. Regression: existing class-wide profile listing remains legal-only and is not broadened for synthetic rows.
4. Route surface: update the frozen compatibility-app route set to allow exactly this new GET path, with no other route addition.

Write and run red tests before changing the route. Run Ruff with `--config backend/pyproject.toml`, strict mypy for changed/new files (new errors only), all three repository validators, and `git diff --check`.

## UI contract (implementation deferred by owner)

Teacher calls `GET /api/be1/v1/organizations/{org}/sessions/{session}/pilot-profiles` with adult authentication. Success example:

```json
{"contract":"Be1PilotProfileListV1","items":[{"child_id":"synthetic-child-001","display_name":"Synthetic Profile"}]}
```

The client can use `child_id` to request admission; it must not infer age, consent, eligibility proof, or run identity. On `403` assignment failure, `404` scoped-resource failure, or `409 PILOT_PROFILE_LOOKUP_UNAVAILABLE` / `SESSION_NOT_IN_LOBBY`, do not fall back to the class-wide profile route for synthetic candidates. No UI changes are in this group; visual AC20 is deferred and not run.

## Exclusions and risks

Exclude the existing class-wide `list_profiles` behavior, proof issuance/revocation, consent state, profile creation, membership/admission changes, UI, migration, router composition, provider calls, and Modal/GPU. The new route is candidate discovery only and grants no Child admission or drawing authority.
