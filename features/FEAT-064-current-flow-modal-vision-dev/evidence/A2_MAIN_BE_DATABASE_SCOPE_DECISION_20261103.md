# GOAL A2 database-scope decision — existing full BE database

Date: 2026-11-03

## Decision

The owner directed the A2 PostgreSQL verification to use the existing full BE database instead of a separate task database. This applies only to A2 and only to the current local `sketch2life` database under the exact identity and no-migration safeguards in `plan/CHAIN_A2_MAIN_BE_DB_ADDENDUM_20261103.md`.

The new addendum SHA-256 is `4AFA521E50A91FB6B06D4BB33303AEC3A39021BECEB2A26907964B99EDF15BB7`. The sequential A2→B1→B2 goal now pins the addendum and has SHA-256 `D7DEE2977C5AA28B26FCB117281DE8B23E4D4AA85A42922B8B37752FBDA8752A`. The original A2 Rev3 plan remains unchanged at SHA-256 `0F384549BE15D3BF38AF73287F9C6487D2D5B7AEAA1BFB08D71E18BE7CD2BA91`.

## Test review informing the boundary

`backend/tests/integration/test_be1_synthetic_pilot_postgres.py` currently accepts only loopback database names containing `be1_acceptance`; it rejects `sketch2life` before connecting. Its fixture creates a fresh randomly generated synthetic organization and adult identity, while teardown discovers tables and deletes rows filtered to that fixture's generated organization ID, plus its generated adult subjects. The existing FK teardown issue concerns deleting an exact test-created AI-job attempt/job pair in the wrong order.

Therefore a fresh A2 launch must authorize the narrow test-only safety-predicate change and its regression tests before the main BE DB can be used. The exact fixture-owned cleanup must remain scoped; no database-wide, prefix-based, or historical-row cleanup is allowed.

## State of work

- This session did not connect to PostgreSQL or inspect live database contents.
- No test, migration, database write, service, or provider was run.
- The DB identity values in the addendum are expected values from prior local observations and must be reverified read-only in the fresh implementation launch.
- A2 remains **BLOCKED / NOT ACCEPTED** until a fresh launch uses this addendum, completes the required PostgreSQL and offline/static gates, and receives independent review. B1 and B2 remain unopened.

