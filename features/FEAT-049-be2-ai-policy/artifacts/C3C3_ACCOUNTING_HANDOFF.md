# Guarded resource accounting — backend integration handoff

ResourceAccountingService is backend-only application code, not a mounted route
or dispatcher action. It composes own ResourceLedgerStore, ResourceAccountingBoundary
and PolicyUseLeases. No permissive production adapter supplied; real BE1/P4 wiring
remains deferred to teammates. Scope and identity come from verified backend
context, not role strings or principal/org fields in client JSON.

## Calls and fields

- `reserve(principal_id, organization_id, ResourceReservationRequest)`: exact stored
  request/pin/attempt, phase create/dispatch/retry, client idempotency key. Initial
  consumer must already persist the original pin through its authorized lifecycle;
  service create-phase rechecks same pin rather than silently repinning.
- `settle(principal_id, organization_id, feature_scope, ResourceSettlementRequest)`:
  explicit backend routing feature selects lock scope before lookup; not a permission
  assertion. Command contains reservation id, operation consume/release/reconcile,
  evidence ref/hash and client key. No caller units/window/verified/allowed override.
- Return is immutable AccountingChange with reservation/counters/replayed metadata.
  It is NOT a dispatch grant, provider token, external cancellation receipt or real
  cost measurement. Fixture evidence never becomes actual_usage_proven.

Reserve holds current-use fence, current accounting guard/quote, then ledger UoW.
Quote must resolve exact adopted definitions/unit/window/ceilings/estimate and
current selected profile/request/attempt eligibility. Same original pin/attempt
maps to one reservation regardless of new caller key. Receipt fingerprint includes
actor/org/feature/full command. Replay still rechecks current authority and quote;
changed terms/window conflict, terminal reservation cannot resume.

Settlement holds accounting guard then ledger UoW; verifier rechecks current rights,
authenticated exact immutable terminal evidence and original reservation binding.
Native proof/key types rebuilt, not coerced. Consume/release disposition must match;
reconcile accepts either verified outcome. Unknown/ongoing work never auto-refunded.
Original unit/window/terms retained after policy/stop/window change. Same terminal
proof replays without delta; different proof cannot charge or refund again.

## Owner fence / failure obligations

Real accounting guard must pre-acquire relevant owner fences and hold them to
ledger commit. Verifier under ledger lock must not acquire outer owner/policy locks
or call a provider over network. Do not create lock inversion or substitute stale
cache for current authority. No provider network work under resource lock.

Dispatch/retry/completion/exposure still require their own current-use/worker gates
and original pin. Cleanup after stop does not invoke a use lease or resurrect work.
No foreign job/session tables written; owner persists consumer provenance separately.

Ledger counters/reservation/receipt/audit intent atomic inside own UoW; no 2PC with
external owners. Guard-exit/network response failure after ledger commit cannot be
called rollback/refund. Surface safe dependency failure, inspect exact committed
receipt on authorized retry, never blindly allocate with a new attempt/key. Audit
intent/delivery marker is not actual provider verification.

## Verification

49 new service component cases, 488 own total PASS; MEMORY ledger and ASSUMED
authority/evidence. SQL pack has 19 ledger cases including two service composition
checks; all 44 actual PG cases NOT_RUN. Commands/preconditions/impact/log-return:
artifacts/C2_SQL_RUNTIME.md. Production adoption, runtime races, provider cost,
ProviderCopyLifecycle, C5 projections/binding and full-card acceptance remain open.
