# GOAL A2 Rev3 main-BE database — independent review

Date: 2026-11-03
Disposition: **NEEDS_REVISION** — one P2 finding remains.

## Review scope and method

Read-only review of the A2 Rev3 report, approved main-BE DB addendum, exact test diff against the pre-test snapshot, current test source, saved test outputs, row-count manifests, and final snapshot hash. No tests were run and no database was queried. The results below distinguish the implementation report from this review's own observations.

Verified pins:

- V4: `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6`.
- A2 Rev3 plan: `0F384549BE15D3BF38AF73287F9C6487D2D5B7AEAA1BFB08D71E18BE7CD2BA91`.
- Main-BE DB addendum: `4AFA521E50A91FB6B06D4BB33303AEC3A39021BECEB2A26907964B99EDF15BB7`.
- Sequential goal: `D7DEE2977C5AA28B26FCB117281DE8B23E4D4AA85A42922B8B37752FBDA8752A`.
- A2 report: `3A8BDC49BEBB6FF768E1A441A551A275A115CE675E95FDF3D1550DBF8D469511`.
- Final snapshot: `.claude/handoff/snapshots/GA2_A2_FINAL_20261103T181341/snapshot_manifest.json`; the current test file hash matches its manifest entry.

Checkout observed during review: branch `feature/feat063-be-foundation`, HEAD `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9`, index empty. The snapshot records 71 status paths; unrelated local changes were not reviewed or modified.

## Finding

### P2 — the shared-DB URL guard does not pin the approved PostgreSQL instance

File: `backend/tests/integration/test_be1_synthetic_pilot_postgres.py:145-150`.

For `sketch2life`, `_is_safe_acceptance_database_url()` checks the database name, loopback host and service/hostaddr routing, but accepts any port and username. The approved A2 target is the existing PostgreSQL 17 instance at `127.0.0.1:5433`, authenticated as `postgres`; this machine has more than one local PostgreSQL service. A URL for a different local server/port with a database also named `sketch2life` therefore passes the fixture guard and can receive the suite's synthetic writes. The test at line 170 proves only the intended `:5433` URL is accepted; it does not reject another port or user.

The implementation report says a separate read-only preflight verified the intended server immediately before this run. That supports the recorded run, but the reusable test guard itself does not fail closed if `BE1_TEST_DATABASE_URL` later points at the wrong local instance.

**Fix direction:** for the exact `sketch2life` exception, require URL port `5433` and explicit username `postgres`; retain the existing loopback/hostaddr/service checks. Add negative guard cases for another port (including default port) and another/missing username. Keep owner and PostgreSQL-major verification in the documented read-only preflight. Do not change the `be1_acceptance` behavior or any runtime code.

## Items reviewed without blocking this finding

- The test-only teardown diff against the fresh pre-test copy is scoped to the A2 integration-test file. It records the exact test-created job/attempt IDs, deletes attempts by both IDs before deleting that job, checks exact row counts, and leaves the existing behavioral assertions unchanged.
- The saved first-run traceback matches the reported FK failure. The saved final focused output is `1 passed`; the full PostgreSQL module output is `77 passed`; T2C/T7b output is `89 passed`; the pinned offline runner output is `401 passed`. These are reported/snapshotted outcomes, not tests rerun by this reviewer.
- The row-count map changed from 24 to 82 after the first failed teardown (58 additional synthetic rows). The report says no further count changes occurred after the exact-ID fix and no prior-run rows were manually removed. This residue is disclosed and should remain untouched unless separately authorized.
- The DB's physical schema includes the expected tables, while its recorded Alembic revisions do not include the synthetic-eligibility source revision. No migration was run. The current evidence therefore does not verify migration history or deployment alignment; the review makes no such claim.
- Strict mypy still exits non-zero with the same protocol incompatibility in the saved baseline and current harness. No new A2 mypy error was reported, but strict mypy is not green.

## Review disposition

The reported A2 tests and exact-ID cleanup correction look sound within their stated scope, but the URL guard is part of the approved shared-database safety boundary and remains too broad. A2 is **NEEDS_REVISION / not accepted** until the P2 is fixed in the same test-only allowlist, focused URL-guard tests are run and recorded, and this independent review is repeated. Keep B1/B2 unopened.

