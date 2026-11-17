# G1 review fixes — T2 / T3 / T9

- Status: APPROVED only for the bounded G1 review fixes in this plan.
- Feature: FEAT-064 current-flow Modal Vision development pilot.
- Baseline: `1e93bc3f3ac645cf4baecbbc09c73afe48719c92`; G1 snapshot `G1_20261101T115654`.
- Owner instruction: `CODEX_PROMPT_G1_REVIEW_FIXES_20261101.md`, 2026-11-01; scope is G1 review corrections only. G2 and later groups are excluded.
- Mode: TREO KHÔNG COMMIT. Do not stage, commit, push, reset, checkout, clean, or stash.

## Purpose

Address the independent review findings F1–F4 and the permitted portions of F5–F6 while preserving the approved T2/T3/T9 security and legacy-session behavior. This is a post-review additive scope. It does not replace or rewrite the earlier T2, T3, or T9 approvals.

## Findings and bounded changes

| Finding | Planned change | Acceptance evidence |
|---|---|---|
| F1 — pilot route changes generated Rev37 operation totals | Keep the generated `openapi_contract.py` untouched. In `test_openapi_contract_catalog.py`, declare the single session-scoped pilot-only GET route explicitly, exclude it from Rev37 catalog counts/set equality, and assert the catalog remains 111 paths / 124 operations and the pilot-only set contains exactly that route. Confirm the OpenAPI builder handles a route with no catalog extension. | Contract test passes; generated contract source and its pinned hash are unchanged. |
| F2 — unhashable or unusual stroke values can escape as a server error | Make profile validation reject non-string colors before palette membership and audit all payload-derived checks in that function for JSON values. Add table-driven unit cases for list/dict/null/bool/string/numeric and large values across color, width, point list and coordinates. Add an HTTP contract case for typed 422, safe response detail, and no persisted operation. | Rejections are `CANVAS_PROFILE_INVALID`; no uncaught exception or persistence on invalid payload. |
| F3 — Child reconnect omits the server-owned profile version | Add nullable `profile_version` to `CanvasReconnectResponse`; populate it from the session configuration returned by `_require_group_eligibility`. A legacy unprofiled session returns null. Cover active and paused reconnect, including a profile-bearing response followed by append with the returned version. Correct the stale T3 UI-contract statement and add complete reconnect/UI contract examples to the T2/T3 reports. | Schema remains `extra="forbid"`; profile version is present for a profiled session and null for a legacy session; existing legal behavior is unchanged. |
| F4 — legacy idempotency fingerprint includes a new null field | Omit `profile_version` from the fingerprint payload when it is null; retain it for profiled requests. Independently compute the historical six-key digest in a test. | Unprofiled digest matches the pre-G1 canonical fingerprint; profiled digest differs. |
| F5 — PostgreSQL fixture checks DB name but not connection host | Parse the connection URL in memory and allow only loopback hostnames/IPs; reject query overrides that can select a non-loopback host. Never print the URL. Report that Python socket patches do not protect libpq/psycopg connections. | Fixture rejects non-loopback host settings and accepts the authorized local URL without displaying it. |
| F6 — missing reconnect and Teacher-route regressions | Extend the existing PostgreSQL module for legal reconnect compatibility, eligibility/membership/group/state denials, Teacher assignment to a different class and foreign organization, pilot-disabled/staging profile attachment, and reconnect read-back of the accepted operation profile id. Use existing test paths only. | Relevant PostgreSQL module passes on the authorized loopback acceptance database; each negative case asserts non-disclosure. |

## Exact allowlist

Modify only the described sections in:

- `backend/src/sketch2life/domain/core_foundation.py` — the canvas profile payload validator only.
- `backend/src/sketch2life/contracts/schemas/be1_runtime.py` — `CanvasReconnectResponse` only.
- `backend/src/sketch2life/interfaces/http/routers/be1_canvas.py` — reconnect response profile version and null-safe append fingerprint only; preserve the three pre-existing Ruff-format-only hunks.
- `backend/tests/unit/test_canvas_operation_profile.py`.
- `backend/tests/contract/test_be1_synthetic_pilot.py`.
- `backend/tests/contract/test_openapi_contract_catalog.py`.
- `backend/tests/integration/test_be1_synthetic_pilot_postgres.py`.
- `features/FEAT-064-current-flow-modal-vision-dev/evidence/T2_CHILD_CANVAS_RECONNECT_REPORT_20261101.md`.
- `features/FEAT-064-current-flow-modal-vision-dev/evidence/T3_CANVAS_PROFILE_IMPLEMENTATION_REPORT_20261101.md`.
- `features/FEAT-064-current-flow-modal-vision-dev/evidence/T9_TEACHER_PILOT_PROFILE_ROUTE_REPORT_20261101.md`.
- `features/FEAT-064-current-flow-modal-vision-dev/status/PILOT_GOAL_LEDGER_20261101.md` — prepend the review-fix report and update G1 only.
- Append one G1 review-fix approval section to `features/FEAT-064-current-flow-modal-vision-dev/approvals/TASK_APPROVAL.md`.
- New: this plan and `features/FEAT-064-current-flow-modal-vision-dev/evidence/G1_REVIEW_FIXES_REPORT_20261101.md`.

No new test file is planned. The OpenAPI catalog test is explicitly in scope for F1.

## Verification plan

1. Add regression tests before implementation and record actual red results for F1–F4. If a test cannot be made red without expanding this allowlist, record NOT DONE and continue independent items.
2. Run focused unit/contract tests after each fix, then the R0 CPU/offline set, `tests/contract` excluding `test_live_image_demo_api.py`, `tests/unit`, and the PostgreSQL synthetic-pilot module.
3. Compare the full contract and unit outcomes against the HEAD archive baseline. The known `test_sketch_review_contracts.py` archive failure is due to that archive not containing `.git`; missing `imageio`/`imageio_ffmpeg` collection errors are environment blockers and will not be fixed by installing packages.
4. Run Ruff lint and format with `--config backend/pyproject.toml` on changed Python files. Run strict mypy on changed files and compare only new diagnostics against HEAD. Run `validate_harness.py`, `validate_repository_security.py`, `validate_architecture.py`, and `git diff --check`; separately scan newly created files for trailing whitespace, CR, and BOM.
5. Run PostgreSQL tests only through the owner-provided loopback `be1_acceptance` URL, kept in memory and never printed. Construct all `Settings` with `_env_file=None`; create and delete only unique synthetic test rows owned by the fixture. Do not run Alembic or use any non-loopback service.
6. Recheck the 18-file G1 snapshot boundary and seven owner-local hashes. Report any baseline or unsupported-suite limitation without claiming a pass.

## Exclusions and unresolved owner questions

- No G2 or later work, UI, npm, Modal/GPU/provider, external network, real child data, migration, schema changes, generated OpenAPI edits, or changes to the write/eligibility guards.
- Preserve acceptance of two identical points; the current profile only forbids fewer than two points. Ask whether identical two-point strokes should remain accepted.
- Do not set export size 1024 or renderer parameters in this task. Ask whether those belong to profile v1 or a later T4/T5 version.
- Checkpoint snapshots remain arbitrary dictionaries and are not validated as profile strokes. T4 must derive authoritative export from accepted operations rather than trust a checkpoint snapshot.
- UI source remains untouched; record the current nullable-turn/profile-version gap in the UI contract.

## Risk and rollback

The main risks are adding a public response field, preserving exact legacy idempotency hashes, and accidentally widening pilot route/catalog scope. Tests pin the route set, response schema, legacy hash, typed rejection, and persistence boundary. If review identifies a defect, revert only the G1 review-fix edits from the resulting snapshot; do not alter the original G1 baseline snapshot or owner-local files.
