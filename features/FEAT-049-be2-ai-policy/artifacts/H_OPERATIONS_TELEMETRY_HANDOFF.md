# H-OPERATIONS health/queue producer — candidate local contract, runtime unbound

C6b, parenta561128. BE2-14 owns projection/contract, actual telemetry/job/queue
source supplied/adopted by owning backend/integration workstream, not arbitrary
job-table writes or a new monitoring platform. No live adapter is supplied here.

## Explicit composition

AiPolicyOperations keeps existing store/boundary/optional ledger arguments and adds
keyword-only telemetry=OperationsTelemetryReader, telemetry_source=PolicyDefinitionRef,
clock=aware trusted clock. Reader/profile must be supplied together; malformed
source configuration fails. Source profile exact ref/version/hash comes from
adopted backend composition, never request JSON or opaque credential/endpoint.
Omit both to obtain truthful unavailable telemetry, not fake healthy/empty queue.
No default source/profile/health threshold/expiry TTL/queue topology selected.

snapshot(org,feature) called only after current OPERATIONS_READ and outside own
policy SQL transaction, under held owner/registry guard. Return None for no source
observation, or strict OperationsTelemetryObservation. Bound aggregate collection
latency at adapter level using approved policy; no hidden retry/default timeout.
Guarded caller rechecks rights before DB access and result; real revocation fencing
must still be adopted, synthetic guards are not that proof.

## Observation meaning / disclosure

- organization_id/feature_scope/source_ref exact echo; mismatched source/version/
  hash/scope is error, no alias repinning. Producer validates allowed current source.
- observed_at/expires_at aware timestamps; expiry must follow observation. Producer
  adopts approved freshness/expiry semantics; this code invents no TTL. Future
  observations rejected, exact expiry boundary stale. No clock-skew grace invented.
- health_state optionally healthy/degraded/unavailable, classified by adopted source
  health definition; None if unsupported. Fresh availability is observation freshness,
  not policy enablement/provider permission. health_state=unavailable can be a fresh
  producer report, distinct from missing observation availability=unavailable.
- queued_jobs/running_jobs optional nonnegative actual integers (not bool/coerced
  strings). Count nonterminal foundation queued/running job states in exact org/
  feature, same observation; never pending audit side effects, retry policy ceilings,
  capacity, money or an unscoped broker-wide gauge. Mapping/aggregation/privacy
  suppression rules require owner adoption, no guessed feature-to-job mapping.
- evidence_kind fixture/runtime is explicit source provenance. Synthetic runtime-
  kind tests only exercise classification. Never present fixture samples as live
  health or measured runtime queue/cost. No actual-cost computation supplied.
- No raw logs, prompt/media, child/session/actor identifiers, provider URLs, tokens,
  dynamic labels or arbitrary dictionary fields. Producer enforces safe aggregate
  disclosure/privacy/access/retention policy before returning even small counts.

Empty observation with no health/count value rejected; use None. Partial supported
metrics retain remaining None, measured0 remains0. Producer exceptions/malformed
bindings are errors, not successful unavailable/zero reports. Return only aggregate
metadata; interface must not accept caller claimed runtime proof/verified boolean.

## Projection / consumer behavior

PolicyOperationsView.telemetry defaults unavailable with all provenance/values null
for backward-compatible missing source. Fresh observation carries exact provenance/
times/values. Stale observation carries provenance/times but all values null.
Freshness checked after own read transaction exit and rights before response; these
are snapshots, not a distributed atomic metric/policy grant. Consumer must honor
expires_at at display time, preserve fixture/stale/unavailable labels and not treat
received fresh as indefinitely current. Scope enabled/healthy/zero queue never
substitutes current consent/source/Teacher review/budget/dispatch authorization.

## Adoption / required runtime proof (NOT_RUN)

Adopt producer source profile and semantic/privacy/expiry policy first; then test
cross-org/feature/definition denial, same-snapshot counts, zero vs no observation,
stale/future timestamps, revocation during collection, timeout/error/redaction,
fixture labels and no job/provider side effects. No broker or provider connection
created by local runner. Exact current local command/receipt in consolidated
handoff; actual PG104 does not validate this source or replace runtime conformance.
No new public route/default app or full-card/goal DONE. Original BE1/P4 wiring
remains delegated to teammates per owner, not silently adopted by this document.
