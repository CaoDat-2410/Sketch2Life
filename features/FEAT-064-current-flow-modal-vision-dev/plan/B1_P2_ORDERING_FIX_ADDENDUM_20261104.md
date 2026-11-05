# B1 P2 Addendum 2 — observation/provider-result write order

Status: owner-approved narrow correction from the direct launch prompt accompanying this addendum. This authorizes only the listed service-order correction, local order-enforcing test, and PostgreSQL acceptance on the new task-owned database below. The original B1 P2 boundaries otherwise remain in force.

## Pinned context

- Prior blocked report: `evidence/B1_P2_REVIEW_FIX_BLOCKED_REPORT_20261104.md`, SHA-256 `073D7EB129FBCD1432717EF6684B2A2298EB8AE50FCE481A5763FF3DF6EABCB8`.
- Branch: `feature/feat063-be-foundation`.
- Expected HEAD: `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9`.
- Target service change: `backend/src/sketch2life/application/services/vision_analysis.py`, only reorder the three inserts in the existing transaction.
- Test-only change: `backend/tests/integration/test_be1_synthetic_pilot_postgres.py`, add a local transaction wrapper that rejects provider-result insertion before head and observation insertion. No shared fake is changed.

## Source evidence and required order

Static source inspection found:

- `infrastructure/vision_analysis/tables.py` defines the analysis head primary key; both `observation` and `provider_result` use `_analysis_fk(...)` to reference `analysis_head`.
- `infrastructure/vision_analysis/repository.py` `insert_provider_result()` requires `get_observation(record.analysis_id)` to return an observation before accepting the provider result.
- At current HEAD, `application/services/vision_analysis.py` calls provider-result, observation, then head inserts. The verified order from `test_pilot_vision_persistence_ga1_postgres.py` is head, observation, provider result.

The sole authorized service change is to call `insert_head(created)`, `insert_observation(observation)`, then `insert_provider_result(result_record)` in the same transaction. The repository invariant, schema, migrations, result contract, and other service logic stay unchanged.

## Test-target guard compatibility

The PostgreSQL fixture already restricts task-owned databases to a canonical random-name pattern plus exact loopback host, port, and role. The owner-approved target generated for this run uses the same `s2l_b1_review_` prefix and exact host/port/role but a date-plus-random-suffix name. To keep the fixture fail-closed without creating a second database or changing target rules, the test-only URL predicate may add this one exact task database name and negative cases for a one-character name mismatch. All existing host, port, role, query-override, hostaddr, and service checks remain unchanged.

## Order regression test

In the already-approved PostgreSQL integration test file, wrap only the analysis repository transaction for the successful B1 acceptance scenario. The test-local wrapper delegates to the real SQL repository and records/enforces the order: a head must be inserted before an observation, and an observation must be present before a provider result. Run the wrapper against the current service before editing the service; it must fail on the old ordering. After the service-only reorder, the same test must pass and the real SQL repository must persist the accepted result.

## PostgreSQL acceptance plan

- New database: `s2l_b1_review_20261104_6a1af65b`.
- Purpose: isolated, disposable-for-testing PostgreSQL 17 target for reproducing the ordering defect and running all five B1 P2 guarded-acceptance scenarios. It is separate from existing databases and the earlier retained task DB `s2l_b1_review_20261104T050646Z_dbbaefa3`.
- Target: local loopback PostgreSQL 17 at `127.0.0.1:5433`, role `postgres`. Load the password/URL only from the existing ignored local configuration into the child process environment; never print or persist it.
- Creation: exactly one connection to the maintenance database, executing only `CREATE DATABASE s2l_b1_review_20261104_6a1af65b`. Do not query application data through that connection. If creation reports a collision or any target mismatch, stop; do not inspect or reuse an existing database.
- Migration: target only the new database and run `python -m alembic upgrade heads`.
- Acceptance: run the five existing B1 P2 scenarios on this new database: durable SUCCEEDED before accepted result; UNKNOWN/HOLD; stale owner fence; duplicate/concurrent delivery; replay/restart after SENT. Use only the existing loopback vision stub. No Modal, GPU, real provider, or external network.
- Cleanup: test fixtures may remove only exact synthetic rows created and tracked by that same fixture run. Close/dispose test engines. Do not reset, truncate, or drop any database; retain this task-created database for independent review. Do not clean the earlier retained task database or its historical rows.

## Acceptance and stop conditions

1. The local order-enforcing regression fails before the service edit and passes after it, with the observed call sequence head → observation → provider result.
2. The successful PostgreSQL scenario commits invocation state `SUCCEEDED` and the analysis result; verify through a fresh connection after commit.
3. The remaining four scenarios pass individually with their required no-resend/no-invalid-acceptance assertions.
4. If the service reorder exposes any additional FK/invariant failure, if another DB is needed, or if a change outside this addendum is required, stop and write a new BLOCKED report. Do not edit approval records or broaden scope.
5. After acceptance, run the pinned offline regression and repository checks from the owner addendum; record actual outputs and snapshot hashes. The state remains `XONG-CHƯA REVIEW` until independent review.

## Explicit exclusions

No changes to `repository.py`, shared fakes, schema, migrations, AI Jobs, routes, provider code, approvals, or any files outside the original B1 P2 allowlist and the two paths named above. No B2, stage, commit, push, merge, reset, stash, or broad cleanup.
