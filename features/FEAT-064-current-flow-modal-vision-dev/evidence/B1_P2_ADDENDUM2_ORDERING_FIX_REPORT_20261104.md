# B1 P2 Addendum 2 — execution report

**Disposition: BLOCKED — XONG-CHƯA REVIEW.** The insert-order regression is corrected, but the real PostgreSQL acceptance still returns `STALE_CONTEXT` after the provider result and invocation ledger were persisted. Do not start B2.

## Scope and checkout

- Approved plan: `plan/B1_P2_ORDERING_FIX_ADDENDUM_20261104.md`, SHA-256 `EEC39B82F918379E1E9795582BD42C3A3D2FC9952555D43B20941850423B8459`.
- Prior blocked report: `evidence/B1_P2_REVIEW_FIX_BLOCKED_REPORT_20261104.md`, SHA-256 `073D7EB129FBCD1432717EF6684B2A2298EB8AE50FCE481A5763FF3DF6EABCB8`.
- Branch `feature/feat063-be-foundation`; HEAD `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9`; index empty. The worktree contains other pre-existing changes; they were preserved.
- This correction only changed the insert order in `backend/src/sketch2life/application/services/vision_analysis.py` and added the local order-enforcing wrapper/diagnostic to `backend/tests/integration/test_be1_synthetic_pilot_postgres.py`. No repository, schema, migration, AI Jobs, route, provider, or approval file was changed for this correction.
- Current SHA-256: service `1BCFB18F07613EF3377D34EE85091FD349EB502178F0A04F8B511A2A969E48C1`; PostgreSQL test `4D81FDD3B4F73FF56027DB632EAB2AF0AF7C102CFEFB53990FAEC83A0D6FD0E6`.

## PostgreSQL execution

- Used only the task-owned database `s2l_b1_review_20261104_6a1af65b` (PostgreSQL 17.11, local loopback, role `postgres`). It was created for this task and migrated with `alembic upgrade heads` (exit 0); it remains retained. The older task database was not used. No database was dropped, reset, truncated, or broadly cleaned.
- Before the service edit, the order-enforcing test failed on the expected violation: provider result was attempted before the observation.
- After the service edit, the same focused test ran with effective pytest arguments:
  `-o addopts= -q --tb=short tests/integration/test_be1_synthetic_pilot_postgres.py::test_b1_succeeded_is_durable_before_real_app_result_acceptance`
- Result: **1 failed in 4.47s**, exit 1. The wrapper's order assertions passed and confirmed `head → observation → provider_result`. The subsequent real acceptance assertion failed with `reason=STALE_CONTEXT`; observed persisted summary was `job_state=running`, `result_disposition=None`, zero result refs, one attempt with no outcome, one analysis head, invocation state `SUCCEEDED`, and `stub_calls=1`.
- This is a distinct post-provider completion/freshness blocker. Its exact originating predicate has not been isolated. The narrow addendum authorizes the insert-order correction and test guard, not a broader change to worker/current-facts/AI Jobs behavior. No assertion was weakened and no additional PG scenarios were run.
- The other four guarded-acceptance scenarios and the full offline regression are **NOT RUN** because the success acceptance failed. The database is retained for review.

## Other checks

| Check / command | Actual result |
|---|---|
| PostgreSQL URL guard tests (preceding run; exact invocation not retained in this report) | 37 passed, 79 deselected; exit 0. No connection was made by these guard tests. |
| Previous broad app-composition + queue selection | 10 passed, 3 route-surface failures; unchanged from prior blocked report. No route code changed in this correction. A clean HEAD-baseline rerun was not established, so whether those failures predate B1 remains **NOT DETERMINED**. |
| `backend\.venv\Scripts\python.exe -m ruff check --no-cache --config backend/pyproject.toml backend/src/sketch2life/application/services/vision_analysis.py backend/tests/integration/test_be1_synthetic_pilot_postgres.py` | Exit 1; one `I001` import-order finding in the PostgreSQL test. No auto-fix applied. |
| `backend\.venv\Scripts\python.exe -m mypy --config-file backend/pyproject.toml --strict --no-incremental --cache-dir backend/.mypy_cache_b1p2_addendum2 backend/src/sketch2life/application/services/vision_analysis.py backend/tests/integration/test_be1_synthetic_pilot_postgres.py` | Exit 1; 66 errors in the PostgreSQL test file. The earlier B1 strict-mypy success covered seven different paths and is not a comparable baseline; baseline equivalence is **NOT DETERMINED**. |
| `python tools/validate_harness.py` | `HARNESS_VALID`, exit 0. |
| `python tools/validate_repository_security.py` | `REPOSITORY_SECURITY_VALID`, 6406 publishable files scanned, exit 0. |
| `python tools/validate_architecture.py` | `ARCHITECTURE_VALID`, exit 0. |
| `git diff --check` | Exit 0; Git printed only existing CRLF-to-LF working-copy notices for dirty documentation. |
| PostgreSQL scenarios beyond the focused success case / offline regression | NOT RUN. |

Snapshot: `.claude/handoff/snapshots/GB1_P2_ORDERING_BLOCKED_20261104T130416/`. It records the checkout, complete worktree hashes, this report/status/ledger, and copies the scoped service/test/plan/report/status files. The task DB remains retained; its URL and credential are not recorded.

No Modal, GPU, real provider, external network, stage, commit, push, merge, reset, stash, or cleanup was performed. B2 remains closed. The remaining blocker requires an owner-approved follow-up scope after independent review of this report.
