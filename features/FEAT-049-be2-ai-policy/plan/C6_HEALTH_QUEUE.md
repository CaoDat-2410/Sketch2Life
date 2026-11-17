# C6b — remaining health/queue projection (approved P5/AC11)

Parenta561128. Resolve the own local projection gap found by C6a, not activate
actual telemetry/provider/queue source. Add typed trusted producer observation and
internal read-only port; explicitly bind source profile from backend composition,
not caller body. No source means unavailable/null, never healthy/zero. Source
observation binds org/feature/exact source/version/hash, observed_at/expires_at and
fixture/runtime provenance. No raw logs/identities/endpoints/provider payloads.

Fields: health_state producer-classified healthy/degraded/unavailable; queued_jobs
and running_jobs are scoped counts of foundation queued/running states at the
observation, not side-effect count/capacity/cost. Each may be null if not supported;
nonempty typed observation required. No health thresholds, production TTL, provider
selection or numeric limits invented. Actual adapter must adopt measured meanings
and expiry policy before runtime use; fixture label remains mandatory.

Current operations-read guard before collector; collector runs outside own DB
transaction, no job-table scan or external I/O under policy lock. Strict native
scope/source/enum/count/time validation; unknown configured-source errors fail
closed, not unavailable success. Return stale metadata but suppress stale values;
future/malformed observation rejected. Re-evaluate freshness after own policy/ledger
read and rights before response; metadata never authorizes new use/dispatch.

Tests absent/null vs actual0, partial sources, runtime-kind synthetic classifier,
stale/boundary/future dates, native flags/forged source/private fields, scope/access/
revocation, collector transaction ordering and sanitized failures. Refresh exact
component node/hash/source count after collection, rerun consolidated pack and
acceptance audit/handoff. No new SQL cases/schema, actual PG104 still NOT_RUN.
