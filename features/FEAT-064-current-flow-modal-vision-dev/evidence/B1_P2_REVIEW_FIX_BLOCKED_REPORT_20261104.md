# B1 P2 review-fix — BLOCKED report

Date: 2026-11-04 (Asia/Saigon)  
State: **BLOCKED — XONG-CHƯA REVIEW**. Finding 1 has focused composition evidence; Finding 2 is not fixed because the real acceptance path reaches a write-order defect outside the approved source allowlist. No independent review has accepted this correction.

## Checkout and authorization

- Branch: `feature/feat063-be-foundation`
- HEAD: `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9`
- Index: empty; no staged paths.
- B1 P2 addendum: SHA-256 `9E6F7A9DDF22A43EA95E99774C55F99EC7C7833142509BABE0F6122DE4F14AB`.
- B1 implementation report: SHA-256 `4BCBBDFE3AF11D751904FC13E836905665B5499ACBAD89787C579C9D9CFECDF1`.
- The approved P2 scope remains limited to minimal app wiring, pilot composition/runtime, and the named composition/PostgreSQL tests. Service/repository, schema, migration, AI Jobs, routes, and provider code were not changed.

## Finding 1 — runtime composition

The real `create_app()` composition path now passes the default pilot factory to `build_be1_runtime()`. The runtime constructs `pilot_vision` only when an engine exists, the factory is present, the environment is `local` or `test`, and the synthetic-pilot flag is enabled. The focused app test exercises enabled, disabled, staging, non-PostgreSQL, and missing-database cases.

Focused evidence: `test_real_app_composes_pilot_only_for_valid_local_synthetic_gate` — **1 passed, 4 deselected**, exit 0. The queue/composition unit module — **8 passed**, exit 0. A broader run of the app composition contract plus queue module ended **10 passed, 3 failed**, exit 1. The three failures were route-surface expectations in `test_compatibility_app_preserves_baseline_route_surface`, `test_classroom_profile_excludes_process_local_demo_routes`, and `test_demo_profile_excludes_durable_classroom_routes`. This run did not establish whether those route expectations predate this correction; no route code was changed.

## Finding 2 — guarded acceptance with task-owned PostgreSQL

Owner authorized a one-statement connection to the maintenance database solely to create a random task-owned database. No application data was read or changed through the maintenance connection. Created database: `s2l_b1_review_20261104T050646Z_dbbaefa3`. Its own connection verified user `postgres` and PostgreSQL `17.11`; `python -m alembic upgrade heads` completed with exit 0 on this new database. The database is retained. No manual cleanup of prior-run residue was performed.

The initial five-test PostgreSQL acceptance run failed before provider invocation because real BE1 authorization returned `FORBIDDEN_SCOPE`. The allowlisted pilot authorization query was corrected to read named Core columns through a mapping instead of treating a scalar result as an ORM entity. After that correction, a successful-provider acceptance case reached the loopback stub, but the job ended `failed_exhausted`; the invocation ledger recorded `SUCCEEDED`, while no accepted analysis result was created. The test raised:

```text
ValueError: provider result does not match the immutable observation evidence
```

Confirmed write-order mismatch: `application/services/vision_analysis.py` inserts the provider result at line 568 before inserting the observation at line 569. `infrastructure/vision_analysis/repository.py` lines 147–151 validates `insert_provider_result()` by loading that observation and raises when it is not yet present. Correcting this requires changing the service transaction order or repository behavior, outside the approved source allowlist. No such change was made. Consequently, the complete guarded acceptance criteria (durable accepted result, UNKNOWN/HOLD, stale fence, duplicate/replay) are **not demonstrated**. The other four cases were not rerun after the authorization correction.

## Verification results

| Check | Actual result |
|---|---|
| App pilot gate test | 1 passed, 4 deselected; exit 0 |
| Queue/composition unit module | 8 passed; exit 0 |
| Broader app composition + queue tests | 10 passed, 3 failed; exit 1 (three route-surface assertions listed above) |
| PostgreSQL/Alembic | New task DB created; `upgrade heads` exit 0. Acceptance remains blocked by the observation/provider-result write-order error. No complete PostgreSQL module pass. |
| Offline regression runner | NOT RUN after the focused acceptance failure. |
| Ruff check | Exit 1; 12 findings across the five scoped source/test files (import ordering/unused imports/redefinitions and one E501). No auto-fix applied. |
| Ruff format check | Exit 1; 4 files would be reformatted and 1 was already formatted. No formatter was applied. |
| Strict mypy | Exit 1; 75 errors in 4 files (5 checked): `pilot_composition.py`, `app.py`, `test_app_composition.py`, and `test_be1_synthetic_pilot_postgres.py`. Baseline equivalence was not checked. |
| `python tools/validate_harness.py` | `HARNESS_VALID`, exit 0 |
| `python tools/validate_repository_security.py` | `REPOSITORY_SECURITY_VALID`, 6404 publishable files scanned, exit 0 |
| `python tools/validate_architecture.py` | `ARCHITECTURE_VALID`, exit 0 |
| `git diff --check` | Exit 0; only line-ending notices for existing dirty documentation files. |

Commands for successful non-DB tests were run from `backend/` with its project virtualenv and `-o addopts= -q`. Static checks used the backend `pyproject.toml` Ruff configuration and strict mypy. No Modal, GPU, provider, or external-network call occurred. No stage, commit, push, merge, reset, stash, or cleanup operation occurred.

## Required next decision

Keep B1 P2 **BLOCKED** until owner approves a narrow source-scope addendum for the observation/provider-result transaction ordering (likely `backend/src/sketch2life/infrastructure/vision_analysis/repository.py` or the service operation order). Then rerun the guarded PostgreSQL acceptance from a clean task-owned database or otherwise account for the retained task-owned database and any exact fixture-owned rows. Do not claim Finding 2 fixed or move to B2 from this report.
