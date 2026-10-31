# T6 — invocation guard and bounded HTTP transport (GOAL A1)

**Status: XONG-CHƯA REVIEW**
**Timestamp:** 2026-11-01 20:53 Asia/Saigon
**Plan SHA-256:** `E339DE53582C60DA2BAFF65236333ABEFEC0E087D6D42D0F1340F73C69B8668B`

## Scope and authority

Implemented the approved T6/V4 D3 boundary only. V4 SHA-256 is `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6`; Goal A1 SHA-256 is `90B546430E1E1E2E8B40078EBD7FF2CA108D0F785C054C06620F2EBBF6902949`. The append-only T6 approval pins the same plan and authorizes the allowlist.

No changes were made to `ObservationRequest`, `application/services/vision_analysis.py`, AI-job services/policies, routes, workers, app composition, schema/migrations, BE1, or Modal deployment. No approval entry was edited during implementation.

## Implementation by layer

| Layer | Result |
| --- | --- |
| L1 — application/domain/contracts | Added the invocation guard protocol and closed failure codes; added `LIVE_LEGACY_BRIDGE` provenance with the existing image-only/full-identity constraints. |
| L4 — infrastructure | Added the T7a-ledger-backed single-use guard, bounded one-request HTTP JSON transport, guarded observation decorator, strict identity validation for typed V2 failures, and the fixed single-attempt pilot policy. |
| L7 — tests/evidence | Added 19 loopback/in-memory T6 test cases, this report, an append-only progress entry, and the T6 snapshot. |
| L2/L3/L5 | No changes in T6. |
| L6 — UI | Deferred by owner. |

The guard binds `run_id`, `job_id`, `attempt_id`, and `organization_id`; persists `SENT` before issuing the HTTP request; sends at most one request; follows no redirects; applies a 160-second monotonic total deadline and a 1,000,000-byte response cap. A complete HTTP 200 JSON object becomes terminal only after the existing V2 bridge validates its identity and outcome. Any ambiguous post-SENT result is `PROVIDER_OUTCOME_UNKNOWN`; only an accepted successful live outcome receives `LIVE_LEGACY_BRIDGE`. The pilot policy remains one attempt with a 180,000 ms attempt timeout; fixture policy is unchanged.

## Test-first and regression results

- Test-first red: before implementation, focused collection failed because `InvocationGuardState` had not yet been added. This was an expected import-level red, not an assertion failure.
- After the first implementation, a broader focused run found six offline bridge failures because failure validation had been applied to fixture transports. The check was narrowed to the guarded live transport; final bridge/domain regression is green.
- Focused T6 file: 19 test cases passed. The copied offline runner reported 609 passed / 4 skipped with the T6 file added to its base list; runner exit 0.
- Focused T6 + legacy bridge + vision domain: 653 passed / 4 skipped in 18.09 s; runner exit 0.
- Established A1 offline regression (618-test cleared baseline plus M1/T7a unit add-ons and T6): **637 passed / 4 skipped / 0 failed** in 18.72 s; runner exit 0. The copied runner cleared database/provider environment settings, blocked non-loopback sockets, and kept pytest temporary data outside the repository. Logs are in the T6 snapshot.
- No PostgreSQL/Alembic, Modal/GPU/provider, external network, or real-child data was used.

## Static checks

- Ruff check on all eight T6 Python paths: `All checks passed!`.
- Ruff format check on the four new Python files: `4 files already formatted`.
- Mypy on seven T6 source files, using a temporary cache outside the repository: `Success: no issues found in 7 source files`.
- `validate_harness.py`: `HARNESS_VALID`.
- `validate_repository_security.py`: `REPOSITORY_SECURITY_VALID`; 6,063 publishable files scanned; no absolute machine paths.
- `validate_architecture.py`: `ARCHITECTURE_VALID`.
- `git diff --check`: exit 0, no output.
- New-file UTF-8/whitespace inspection is recorded in the snapshot. The first mypy attempt hit an internal cache error; rerunning with an external temporary cache produced the successful result above. Ruff’s two import-order findings were fixed before the final successful Ruff run.

## Files in T6 scope

- `backend/src/sketch2life/application/ports/vision_analysis.py`
- `backend/src/sketch2life/domain/vision_analysis.py`
- `backend/src/sketch2life/contracts/schemas/analysis_results.py`
- `backend/src/sketch2life/infrastructure/vision_analysis/invocation_guard.py`
- `backend/src/sketch2life/infrastructure/vision_analysis/transport.py`
- `backend/src/sketch2life/infrastructure/vision_analysis/pilot_policy.py`
- `backend/src/sketch2life/infrastructure/vision_analysis/legacy_v2.py`
- `backend/tests/unit/test_invocation_guard_transport_ga1.py`
- `features/FEAT-064-current-flow-modal-vision-dev/plan/T6_INVOCATION_GUARD_IMPLEMENTATION_PLAN_GA1_20261101.md`
- `features/FEAT-064-current-flow-modal-vision-dev/approvals/TASK_APPROVAL.md` (approval was already appended before implementation)
- `features/FEAT-064-current-flow-modal-vision-dev/status/PILOT_GOAL_LEDGER_20261101.md` (append-only progress)
- `features/FEAT-064-current-flow-modal-vision-dev/evidence/T6_INVOCATION_GUARD_IMPLEMENTATION_REPORT_GA1_20261101.md`

## Residual limits

T6 supplies the guarded invocation components but does not wire a caller or worker. Durable host witness/rollback protection remains deferred. No live provider behavior or model quality is established. Independent review remains outstanding. `OWNER_MODAL_CALL_APPROVED: NO`.

Snapshot: `.claude/handoff/snapshots/GA1_T6_20261101T205305/`. No stage, commit, push, or publication action was performed.
